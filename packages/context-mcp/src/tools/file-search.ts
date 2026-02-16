import { FileWalker } from '../utils/file-walker.js';
import type { ContinueIDE } from '../continue/ContinueIDE.js';
import { FullTextSearchCodebaseIndex } from '@continuedev/core/dist/indexing/FullTextSearchCodebaseIndex.js';
import { getComputeDeleteAddRemove, SqliteDb } from '@continuedev/core/dist/indexing/refreshIndex.js';
import { ChunkCodebaseIndex } from '@continuedev/core/dist/indexing/chunk/ChunkCodebaseIndex.js';
import type { IndexTag } from '@continuedev/core';
import { promises as fs } from 'fs';

/**
 * Build tag string in Continue's format: "directory::branch::artifactId"
 */
function tagToString(tag: IndexTag): string {
  return `${tag.directory}::${tag.branch}::${tag.artifactId}`;
}

/**
 * Check if a tag already has indexed chunks in the database.
 * This handles the case where a previous indexing run was interrupted:
 * - chunk_tags has entries (INSERT succeeded)
 * - tag_catalog wasn't updated (markComplete didn't run)
 * - Next run would try to re-insert → UNIQUE constraint violation
 */
async function isTagAlreadyIndexed(tag: IndexTag): Promise<boolean> {
  try {
    const db = await SqliteDb.get();
    const tagString = tagToString(tag);
    console.error(`[DEBUG] isTagAlreadyIndexed: checking for tag="${tagString}"`);
    const result = await db.get<{ count: number }>(
      'SELECT COUNT(*) as count FROM chunk_tags WHERE tag = ?',
      [tagString]
    );
    const count = result?.count ?? 0;
    console.error(`[DEBUG] isTagAlreadyIndexed: found ${count} entries`);
    return count > 0;
  } catch (error) {
    // Table might not exist yet on first run
    console.error(`[DEBUG] isTagAlreadyIndexed: error`, error);
    return false;
  }
}

export interface FileSearchArgs {
  pattern: string;
  mode?: 'auto' | 'path' | 'content' | 'both';
  regex?: boolean;
  filter?: {
    extensions?: string[];
    exclude?: string[];
  };
  max_results?: number;
  context_lines?: number;
  include_content?: boolean;
}

export interface FileSearchResult {
  pattern: string;
  mode: string;
  results: Array<{
    type: 'path' | 'content';
    path: string;
    line_range?: [number, number];
    content?: string;
    score?: number;
  }>;
  count: number;
  performance?: {
    searchTime: number;
    method: string;
  };
}

// Track which directories have been indexed (rebuilds on server restart)
const indexedDirs = new Set<string>();

/**
 * Sanitize query text for FTS5 phrase search.
 *
 * FTS5 interprets special characters as operators:
 * - `-` as NOT (e.g., "crossplane-plan" becomes "crossplane NOT plan")
 * - `+` as required term
 * - `*` as prefix wildcard
 * - `OR`, `AND`, `NOT` as boolean operators
 * - `"` for phrase search
 *
 * Continue's upstream code only strips `?` characters, leaving this bug.
 * We fix it by wrapping the entire query in double quotes for phrase search.
 * This matches exact character sequences, which is typically what users want
 * for code identifiers like `context-mcp` or `getUserById`.
 */
function sanitizeFTS5Query(text: string): string {
  // Escape any existing double quotes by doubling them
  const escaped = text.replace(/"/g, '""');
  // Wrap in double quotes for phrase search
  return `"${escaped}"`;
}

/**
 * Build FTS5 index for a single workspace directory
 * This populates the chunks table and FTS5 index tables
 */
async function buildFTSIndexForDir(
  workspaceDir: string,
  ide: ContinueIDE
): Promise<IndexTag> {
  // 1. Create IndexTag - each directory gets its own tag
  const tag: IndexTag = {
    branch: 'main', // TODO: Detect from git
    directory: workspaceDir,
    artifactId: 'chunks', // ChunkCodebaseIndex.artifactId
  };

  // Check if already indexed in chunk_tags (handles interrupted previous runs)
  if (await isTagAlreadyIndexed(tag)) {
    console.error(`FTS5 index already exists for: ${workspaceDir} (skipping)`);
    indexedDirs.add(workspaceDir);
    return tag;
  }

  console.error(`Building FTS5 index for: ${workspaceDir}`);

  // 2. Get all files to index
  const walker = new FileWalker(workspaceDir);
  const allFiles = await walker.walk();

  // Create FileStatsMap
  const fileStats: Record<
    string,
    { size: number; lastModified: number }
  > = {};
  for (const file of allFiles) {
    try {
      const stats = await fs.stat(file);
      fileStats[file] = {
        size: stats.size,
        lastModified: stats.mtimeMs,
      };
    } catch (error) {
      // Skip files we can't stat
      console.error(`Error stating file ${file}:`, error);
    }
  }

  // 3. Use Continue's helper to compute what to index
  const [results, _pathsAndCacheKeys, markComplete] =
    await getComputeDeleteAddRemove(
      tag,
      fileStats,
      async (path: string) => await fs.readFile(path, 'utf-8'),
      undefined // repoName
    );

  console.error(
    `  Indexing ${results.compute.length} files, removing ${results.del.length} files...`
  );

  // 4. Build Chunks index (populates chunks table)
  try {
    // ChunkCodebaseIndex needs (readFile, continueServerClient, maxChunkSize)
    // We don't have a continueServerClient, so pass a mock with connected: false
    const mockServerClient = {
      connected: false,
      url: undefined,
      getUserToken: () => undefined,
      getConfig: async () => ({ configJson: '{}' }),
      getFromIndexCache: async () => ({ files: {} }),
    };
    const maxChunkSize = 512; // Default chunk size
    const chunkIndex = new ChunkCodebaseIndex(
      ide.readFile.bind(ide),
      mockServerClient,
      maxChunkSize
    );

    for await (const progress of chunkIndex.update(
      tag,
      results,
      markComplete,
      undefined
    )) {
      // Log progress
      if (progress.progress % 20 === 0 || progress.progress === 100) {
        console.error(`  Chunks indexing progress: ${progress.progress}%`);
      }
    }
    console.error(`  ✅ Chunks table populated for ${workspaceDir}`);
  } catch (error) {
    console.error(`  ❌ Error building chunks index for ${workspaceDir}:`, error);
    throw error;
  }

  // 5. Build FTS index (indexes the chunks)
  try {
    const ftsIndex = new FullTextSearchCodebaseIndex();

    for await (const progress of ftsIndex.update(
      tag,
      results,
      markComplete,
      undefined
    )) {
      // Log progress
      if (progress.progress % 20 === 0 || progress.progress === 100) {
        console.error(`  FTS indexing progress: ${progress.progress}%`);
      }
    }
    console.error(`  ✅ FTS index populated for ${workspaceDir}`);
  } catch (error) {
    console.error(`  ❌ Error building FTS index for ${workspaceDir}:`, error);
    throw error;
  }

  indexedDirs.add(workspaceDir);
  return tag;
}

/**
 * Build FTS5 index for all workspace directories
 * Returns array of IndexTags for querying
 */
async function buildFTSIndex(
  workspaceDirs: string[],
  ide: ContinueIDE
): Promise<IndexTag[]> {
  const tags: IndexTag[] = [];

  // Check which directories need indexing
  const dirsToIndex = workspaceDirs.filter(dir => !indexedDirs.has(dir));

  if (dirsToIndex.length === 0) {
    console.error('FTS5 index already built for all directories, skipping...');
    // Return tags for all indexed directories
    return workspaceDirs.map(dir => ({
      branch: 'main',
      directory: dir,
      artifactId: 'chunks',
    }));
  }

  console.error(`Building FTS5 index for ${dirsToIndex.length} directory(ies)...`);

  // Index each directory sequentially
  for (const dir of dirsToIndex) {
    const tag = await buildFTSIndexForDir(dir, ide);
    tags.push(tag);
  }

  // Add tags for already-indexed directories
  for (const dir of workspaceDirs) {
    if (!dirsToIndex.includes(dir)) {
      tags.push({
        branch: 'main',
        directory: dir,
        artifactId: 'chunks',
      });
    }
  }

  console.error(`✅ FTS5 index built for ${workspaceDirs.length} directory(ies)`);
  return tags;
}

/**
 * Search files using Continue's FTS5 index with BM25 ranking
 * Supports multiple workspace directories for cross-repository search
 */
export async function fileSearchTool(
  args: FileSearchArgs,
  workspaceDirs: string | string[],
  ide: ContinueIDE
): Promise<FileSearchResult> {
  // Normalize to array and remove trailing slashes for consistent tag matching
  const dirs = (Array.isArray(workspaceDirs) ? workspaceDirs : [workspaceDirs])
    .map(dir => dir.replace(/\/+$/, ''));

  const mode = args.mode || 'auto';
  const maxResults = args.max_results || 50;
  const includeContent = args.include_content ?? false; // Default to false to save tokens
  const results: FileSearchResult['results'] = [];
  const startTime = Date.now();

  // Path search across all directories (still uses V1 walker - fast enough)
  if (mode === 'path' || mode === 'both' || mode === 'auto') {
    try {
      let allPathMatches: string[] = [];

      // Search each directory
      for (const dir of dirs) {
        const walker = new FileWalker(dir);
        const pathMatches = await walker.find(args.pattern, args.regex);
        allPathMatches.push(...pathMatches);
      }

      // Apply filters
      if (args.filter?.extensions && args.filter.extensions.length > 0) {
        allPathMatches = allPathMatches.filter(path => {
          const ext = path.split('.').pop();
          return ext && args.filter!.extensions!.includes(ext);
        });
      }

      if (args.filter?.exclude && args.filter.exclude.length > 0) {
        allPathMatches = allPathMatches.filter(path => {
          return !args.filter!.exclude!.some(exclude =>
            path.includes(exclude)
          );
        });
      }

      results.push(...allPathMatches.slice(0, maxResults).map(path => ({
        type: 'path' as const,
        path,
      })));
    } catch (error) {
      console.error('Path search error:', error);
    }
  }

  // Content search using FTS5
  let searchMethod = 'File System';

  if (
    mode === 'content' ||
    mode === 'both' ||
    (mode === 'auto' && results.length === 0)
  ) {
    try {
      // 1. Build FTS index for all directories if not already built
      const tags = await buildFTSIndex(dirs, ide);

      // 2. Search using FTS5 across all indexed directories
      const ftsIndex = new FullTextSearchCodebaseIndex();

      const chunks = await ftsIndex.retrieve({
        n: maxResults,
        text: sanitizeFTS5Query(args.pattern),
        tags: tags, // Search across all indexed directories
        bm25Threshold: -2.5, // Ranks are negative; filter keeps rank <= threshold
      });

      // 3. Convert chunks to results
      for (const chunk of chunks) {
        // Apply extension filter if specified
        if (args.filter?.extensions && args.filter.extensions.length > 0) {
          const ext = chunk.filepath.split('.').pop();
          if (!ext || !args.filter.extensions.includes(ext)) {
            continue;
          }
        }

        // Apply exclude filter if specified
        if (args.filter?.exclude && args.filter.exclude.length > 0) {
          const shouldExclude = args.filter.exclude.some(exclude =>
            chunk.filepath.includes(exclude)
          );
          if (shouldExclude) {
            continue;
          }
        }

        // Build result with line range and optional content
        const result: FileSearchResult['results'][number] = {
          type: 'content' as const,
          path: chunk.filepath,
          line_range: [chunk.startLine, chunk.endLine],
        };

        // Only include content if requested (saves tokens)
        if (includeContent) {
          result.content = chunk.content.trim();
        }

        results.push(result);
      }

      searchMethod = `FTS5 (BM25, ${dirs.length} dir${dirs.length > 1 ? 's' : ''})`;
    } catch (error) {
      console.error('FTS5 search error:', error);
      throw error; // No fallback - FTS5 failures are hard errors
    }
  }

  const searchTime = Date.now() - startTime;

  // Deduplicate by path
  const uniqueResults = Array.from(
    new Map(results.map(r => [r.path, r])).values()
  ).slice(0, maxResults);

  return {
    pattern: args.pattern,
    mode,
    results: uniqueResults,
    count: uniqueResults.length,
    performance: {
      searchTime,
      method: searchMethod,
    },
  };
}
