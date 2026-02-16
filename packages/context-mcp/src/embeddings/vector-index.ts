/**
 * Vector Index Wrapper for Context-MCP
 *
 * This wraps Continue's LanceDbIndex to provide vector-based semantic search
 * for code files. Uses all-MiniLM-L6-v2 embeddings and LanceDB for fast
 * approximate nearest neighbor (ANN) search.
 *
 * The index is built incrementally and persisted to disk at ~/.continue/index/lancedb/
 *
 * @see docs/BUNDLING_SOLUTION.md for architecture details
 */

import { promises as fs } from 'node:fs';
import type { IndexTag, Chunk, BranchAndDir } from '@continuedev/core';
import { LanceDbIndex } from '@continuedev/core/dist/indexing/LanceDbIndex.js';
import { getComputeDeleteAddRemove } from '@continuedev/core/dist/indexing/refreshIndex.js';
import { getEmbeddingsProvider } from './embeddings-provider.js';
import { FileWalker } from '../utils/file-walker.js';
import type { ContinueIDE } from '../continue/ContinueIDE.js';

// Track which directories have been indexed
const indexedDirs = new Set<string>();

// Singleton LanceDbIndex instance
let lanceDbIndex: LanceDbIndex | null = null;
let indexInitPromise: Promise<LanceDbIndex | null> | null = null;

/**
 * Initialize or get the LanceDbIndex singleton.
 * Returns null if LanceDB fails to load (unsupported platform).
 */
export async function getLanceDbIndex(): Promise<LanceDbIndex | null> {
  if (lanceDbIndex !== null) {
    return lanceDbIndex;
  }

  if (indexInitPromise !== null) {
    return indexInitPromise;
  }

  indexInitPromise = (async () => {
    try {
      console.error('[vector-index] Initializing LanceDB...');
      const embeddingsProvider = await getEmbeddingsProvider();

      const readFile = async (filepath: string): Promise<string> => {
        return await fs.readFile(filepath, 'utf-8');
      };

      lanceDbIndex = await LanceDbIndex.create(embeddingsProvider, readFile);

      if (lanceDbIndex) {
        console.error('[vector-index] LanceDB initialized successfully');
      } else {
        console.error('[vector-index] LanceDB not available on this platform');
      }

      return lanceDbIndex;
    } catch (error) {
      console.error('[vector-index] Failed to initialize LanceDB:', error);
      return null;
    }
  })();

  return indexInitPromise;
}

/**
 * Build vector embeddings index for a single workspace directory.
 */
async function buildVectorIndexForDir(
  workspaceDir: string,
  ide: ContinueIDE
): Promise<IndexTag | null> {
  const index = await getLanceDbIndex();
  if (!index) {
    console.error('[vector-index] LanceDB not available, skipping vector indexing');
    return null;
  }

  console.error(`[vector-index] Building embeddings index for: ${workspaceDir}`);

  // Create IndexTag for this directory
  const tag: IndexTag = {
    branch: 'main', // TODO: Detect from git
    directory: workspaceDir,
    artifactId: index.artifactId,
  };

  // Get all files to index
  const walker = new FileWalker(workspaceDir);
  const allFiles = await walker.walk();

  // Create FileStatsMap
  const fileStats: Record<string, { size: number; lastModified: number }> = {};
  for (const file of allFiles) {
    try {
      const stats = await fs.stat(file);
      fileStats[file] = {
        size: stats.size,
        lastModified: stats.mtimeMs,
      };
    } catch (error) {
      // Skip files we can't stat
    }
  }

  // Compute what needs to be indexed
  const [results, _pathsAndCacheKeys, markComplete] = await getComputeDeleteAddRemove(
    tag,
    fileStats,
    async (path: string) => await fs.readFile(path, 'utf-8'),
    undefined // repoName
  );

  console.error(
    `[vector-index] Indexing ${results.compute.length} files, ` +
    `adding tags to ${results.addTag.length}, ` +
    `removing ${results.del.length}...`
  );

  if (results.compute.length === 0 && results.addTag.length === 0) {
    console.error('[vector-index] No files to index, using cached embeddings');
    indexedDirs.add(workspaceDir);
    return tag;
  }

  // Run the vector index update
  try {
    for await (const progress of index.update(tag, results, markComplete, undefined)) {
      if (progress.status === 'indexing') {
        const pct = Math.round(progress.progress * 100);
        if (pct % 20 === 0 || pct >= 95) {
          console.error(`[vector-index] Embeddings progress: ${pct}% - ${progress.desc}`);
        }
      }
    }
    console.error(`[vector-index] ✅ Embeddings index built for ${workspaceDir}`);
    indexedDirs.add(workspaceDir);
    return tag;
  } catch (error) {
    console.error(`[vector-index] ❌ Error building embeddings index:`, error);
    throw error;
  }
}

/**
 * Build vector embeddings index for all workspace directories.
 * Returns array of IndexTags for querying.
 */
export async function buildVectorIndex(
  workspaceDirs: string[],
  ide: ContinueIDE
): Promise<IndexTag[]> {
  const tags: IndexTag[] = [];

  // Check which directories need indexing
  const dirsToIndex = workspaceDirs.filter((dir) => !indexedDirs.has(dir));

  if (dirsToIndex.length === 0) {
    console.error('[vector-index] All directories already indexed');
    const index = await getLanceDbIndex();
    return workspaceDirs.map((dir) => ({
      branch: 'main',
      directory: dir,
      artifactId: index?.artifactId || 'vectordb::transformers.js::all-MiniLM-L6-v2',
    }));
  }

  console.error(`[vector-index] Building embeddings for ${dirsToIndex.length} directory(ies)...`);

  // Index each directory sequentially (embeddings are CPU-intensive)
  for (const dir of dirsToIndex) {
    const tag = await buildVectorIndexForDir(dir, ide);
    if (tag) {
      tags.push(tag);
    }
  }

  // Add tags for already-indexed directories
  const index = await getLanceDbIndex();
  for (const dir of workspaceDirs) {
    if (!dirsToIndex.includes(dir)) {
      tags.push({
        branch: 'main',
        directory: dir,
        artifactId: index?.artifactId || 'vectordb::transformers.js::all-MiniLM-L6-v2',
      });
    }
  }

  return tags;
}

/**
 * Search using vector embeddings for semantic similarity.
 */
export async function vectorSearch(
  query: string,
  workspaceDirs: string[],
  ide: ContinueIDE,
  options: {
    maxResults?: number;
    filterDirectory?: string;
  } = {}
): Promise<Chunk[]> {
  const index = await getLanceDbIndex();
  if (!index) {
    console.error('[vector-index] LanceDB not available, returning empty results');
    return [];
  }

  const maxResults = options.maxResults || 20;

  // Ensure index is built for all directories
  const tags = await buildVectorIndex(workspaceDirs, ide);
  if (tags.length === 0) {
    console.error('[vector-index] No indexed directories, returning empty results');
    return [];
  }

  // Convert IndexTags to BranchAndDir for retrieve()
  const branchAndDirs: BranchAndDir[] = tags.map((tag) => ({
    branch: tag.branch,
    directory: tag.directory,
  }));

  try {
    const startTime = Date.now();
    const results = await index.retrieve(
      query,
      maxResults,
      branchAndDirs,
      options.filterDirectory
    );
    const elapsed = Date.now() - startTime;

    console.error(`[vector-index] Retrieved ${results.length} results in ${elapsed}ms`);
    return results;
  } catch (error) {
    console.error('[vector-index] Search error:', error);
    return [];
  }
}

/**
 * Check if LanceDB is available on this platform.
 */
export async function isVectorSearchAvailable(): Promise<boolean> {
  const index = await getLanceDbIndex();
  return index !== null;
}

export default {
  getLanceDbIndex,
  buildVectorIndex,
  vectorSearch,
  isVectorSearchAvailable,
};
