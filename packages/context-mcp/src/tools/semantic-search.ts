/**
 * Semantic Search Tool for Context-MCP
 *
 * Provides hybrid search combining:
 * - FTS5 full-text search with BM25 ranking (lexical matching)
 * - LanceDB vector search with embeddings (semantic similarity)
 *
 * Results are merged using Reciprocal Rank Fusion (RRF) to combine
 * both ranking signals effectively.
 *
 * IMPORTANT: This tool requires LanceDB. If LanceDB is unavailable
 * (unsupported platform), the tool will fail rather than fall back.
 */

import type { Chunk, IndexTag } from '@continuedev/core';
import { FullTextSearchCodebaseIndex } from '@continuedev/core/dist/indexing/FullTextSearchCodebaseIndex.js';
import { getComputeDeleteAddRemove } from '@continuedev/core/dist/indexing/refreshIndex.js';
import { ChunkCodebaseIndex } from '@continuedev/core/dist/indexing/chunk/ChunkCodebaseIndex.js';
import { promises as fs } from 'node:fs';
import { FileWalker } from '../utils/file-walker.js';
import { vectorSearch, buildVectorIndex, isVectorSearchAvailable } from '../embeddings/vector-index.js';
import type { ContinueIDE } from '../continue/ContinueIDE.js';

export interface SemanticSearchArgs {
  query: string;
  mode?: 'hybrid' | 'semantic' | 'lexical';
  filter?: {
    extensions?: string[];
    exclude?: string[];
  };
  max_results?: number;
  include_content?: boolean;
  semantic_weight?: number; // 0.0-1.0, default 0.5
}

export interface SemanticSearchResult {
  query: string;
  mode: string;
  results: Array<{
    path: string;
    line_range: [number, number];
    content?: string;
    score: number;
    source: 'semantic' | 'lexical' | 'hybrid';
  }>;
  count: number;
  performance?: {
    searchTime: number;
    semanticTime?: number;
    lexicalTime?: number;
  };
}

// Track which directories have FTS index built
const ftsIndexedDirs = new Set<string>();

/**
 * Sanitize query for FTS5 phrase search.
 */
function sanitizeFTS5Query(text: string): string {
  const escaped = text.replace(/"/g, '""');
  return `"${escaped}"`;
}

/**
 * Build FTS5 index for a directory (same logic as file-search.ts).
 */
async function ensureFTSIndex(
  workspaceDir: string,
  ide: ContinueIDE
): Promise<IndexTag> {
  if (ftsIndexedDirs.has(workspaceDir)) {
    return {
      branch: 'main',
      directory: workspaceDir,
      artifactId: 'chunks',
    };
  }

  console.error(`[semantic-search] Building FTS index for: ${workspaceDir}`);

  const tag: IndexTag = {
    branch: 'main',
    directory: workspaceDir,
    artifactId: 'chunks',
  };

  const walker = new FileWalker(workspaceDir);
  const allFiles = await walker.walk();

  const fileStats: Record<string, { size: number; lastModified: number }> = {};
  for (const file of allFiles) {
    try {
      const stats = await fs.stat(file);
      fileStats[file] = {
        size: stats.size,
        lastModified: stats.mtimeMs,
      };
    } catch {
      // Skip files we can't stat
    }
  }

  const [results, , markComplete] = await getComputeDeleteAddRemove(
    tag,
    fileStats,
    async (path: string) => await fs.readFile(path, 'utf-8'),
    undefined
  );

  // Build chunks index
  const mockServerClient = {
    connected: false,
    url: undefined,
    getUserToken: () => undefined,
    getConfig: async () => ({ configJson: '{}' }),
    getFromIndexCache: async () => ({ files: {} }),
  };

  const chunkIndex = new ChunkCodebaseIndex(
    ide.readFile.bind(ide),
    mockServerClient,
    512
  );

  for await (const progress of chunkIndex.update(tag, results, markComplete, undefined)) {
    // Progress logging
  }

  // Build FTS index
  const ftsIndex = new FullTextSearchCodebaseIndex();
  for await (const progress of ftsIndex.update(tag, results, markComplete, undefined)) {
    // Progress logging
  }

  ftsIndexedDirs.add(workspaceDir);
  console.error(`[semantic-search] ✅ FTS index built for ${workspaceDir}`);
  return tag;
}

/**
 * Perform FTS5 lexical search.
 */
async function lexicalSearch(
  query: string,
  workspaceDirs: string[],
  ide: ContinueIDE,
  maxResults: number
): Promise<Chunk[]> {
  const tags: IndexTag[] = [];

  for (const dir of workspaceDirs) {
    const tag = await ensureFTSIndex(dir, ide);
    tags.push(tag);
  }

  const ftsIndex = new FullTextSearchCodebaseIndex();
  return await ftsIndex.retrieve({
    n: maxResults,
    text: sanitizeFTS5Query(query),
    tags,
    bm25Threshold: -2.5,
  });
}

/**
 * Reciprocal Rank Fusion (RRF) for combining ranked lists.
 * RRF(d) = Σ 1/(k + rank(d)) for each ranking
 * k=60 is standard constant to prevent high ranks from dominating.
 */
function reciprocalRankFusion(
  semanticResults: Chunk[],
  lexicalResults: Chunk[],
  semanticWeight: number = 0.5,
  k: number = 60
): Map<string, { chunk: Chunk; score: number; sources: Set<string> }> {
  const scores = new Map<string, { chunk: Chunk; score: number; sources: Set<string> }>();

  const lexicalWeight = 1 - semanticWeight;

  // Score semantic results
  semanticResults.forEach((chunk, rank) => {
    const key = `${chunk.filepath}:${chunk.startLine}-${chunk.endLine}`;
    const rrfScore = semanticWeight / (k + rank + 1);

    if (scores.has(key)) {
      const existing = scores.get(key)!;
      existing.score += rrfScore;
      existing.sources.add('semantic');
    } else {
      scores.set(key, {
        chunk,
        score: rrfScore,
        sources: new Set(['semantic']),
      });
    }
  });

  // Score lexical results
  lexicalResults.forEach((chunk, rank) => {
    const key = `${chunk.filepath}:${chunk.startLine}-${chunk.endLine}`;
    const rrfScore = lexicalWeight / (k + rank + 1);

    if (scores.has(key)) {
      const existing = scores.get(key)!;
      existing.score += rrfScore;
      existing.sources.add('lexical');
    } else {
      scores.set(key, {
        chunk,
        score: rrfScore,
        sources: new Set(['lexical']),
      });
    }
  });

  return scores;
}

/**
 * Main semantic search tool.
 *
 * @throws Error if vector search is unavailable (LanceDB not supported)
 */
export async function semanticSearchTool(
  args: SemanticSearchArgs,
  workspaceDirs: string | string[],
  ide: ContinueIDE
): Promise<SemanticSearchResult> {
  const dirs = Array.isArray(workspaceDirs) ? workspaceDirs : [workspaceDirs];
  const mode = args.mode || 'hybrid';
  const maxResults = args.max_results || 30;
  const includeContent = args.include_content ?? false;
  const semanticWeight = args.semantic_weight ?? 0.5;

  const startTime = Date.now();
  let semanticTime: number | undefined;
  let lexicalTime: number | undefined;

  // Check vector search availability - FAIL if unavailable
  if (mode === 'hybrid' || mode === 'semantic') {
    const available = await isVectorSearchAvailable();
    if (!available) {
      throw new Error(
        'Semantic search requires LanceDB which is not available on this platform. ' +
        'Use file_search tool for lexical search instead.'
      );
    }
  }

  let semanticResults: Chunk[] = [];
  let lexicalResults: Chunk[] = [];

  // Perform semantic search
  if (mode === 'hybrid' || mode === 'semantic') {
    const semStart = Date.now();
    semanticResults = await vectorSearch(args.query, dirs, ide, {
      maxResults: maxResults * 2, // Get more to allow for deduplication
    });
    semanticTime = Date.now() - semStart;
  }

  // Perform lexical search
  if (mode === 'hybrid' || mode === 'lexical') {
    const lexStart = Date.now();
    lexicalResults = await lexicalSearch(args.query, dirs, ide, maxResults * 2);
    lexicalTime = Date.now() - lexStart;
  }

  // Merge results
  let finalResults: SemanticSearchResult['results'] = [];

  if (mode === 'hybrid') {
    // Use RRF to combine rankings
    const fusedScores = reciprocalRankFusion(
      semanticResults,
      lexicalResults,
      semanticWeight
    );

    // Sort by fused score and take top results
    const sorted = Array.from(fusedScores.values())
      .sort((a, b) => b.score - a.score)
      .slice(0, maxResults);

    finalResults = sorted.map(({ chunk, score, sources }) => ({
      path: chunk.filepath,
      line_range: [chunk.startLine, chunk.endLine] as [number, number],
      content: includeContent ? chunk.content : undefined,
      score,
      source: sources.size > 1 ? 'hybrid' : (sources.has('semantic') ? 'semantic' : 'lexical'),
    }));
  } else if (mode === 'semantic') {
    finalResults = semanticResults.slice(0, maxResults).map((chunk, idx) => ({
      path: chunk.filepath,
      line_range: [chunk.startLine, chunk.endLine] as [number, number],
      content: includeContent ? chunk.content : undefined,
      score: 1 / (idx + 1), // Normalized rank score
      source: 'semantic' as const,
    }));
  } else {
    finalResults = lexicalResults.slice(0, maxResults).map((chunk, idx) => ({
      path: chunk.filepath,
      line_range: [chunk.startLine, chunk.endLine] as [number, number],
      content: includeContent ? chunk.content : undefined,
      score: 1 / (idx + 1),
      source: 'lexical' as const,
    }));
  }

  // Apply filters
  if (args.filter?.extensions?.length) {
    finalResults = finalResults.filter((r) => {
      const ext = r.path.split('.').pop();
      return ext && args.filter!.extensions!.includes(ext);
    });
  }

  if (args.filter?.exclude?.length) {
    finalResults = finalResults.filter((r) => {
      return !args.filter!.exclude!.some((ex) => r.path.includes(ex));
    });
  }

  const searchTime = Date.now() - startTime;

  return {
    query: args.query,
    mode,
    results: finalResults,
    count: finalResults.length,
    performance: {
      searchTime,
      semanticTime,
      lexicalTime,
    },
  };
}

export default semanticSearchTool;
