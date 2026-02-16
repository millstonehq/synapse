import { CodeSnippetsCodebaseIndex } from '@continuedev/core/dist/indexing/CodeSnippetsIndex.js';
import { SqliteDb } from '@continuedev/core/dist/indexing/refreshIndex.js';
import * as fs from 'fs';

export interface CodeStructureArgs {
  paths: string[];
  scope?: 'paths' | 'selected';
}

export interface CodeStructureResult {
  scope: string;
  structures: Array<{
    path: string;
    signatures: string[];
    count: number;
  }>;
  performance?: {
    extractionTime: number;
    filesProcessed: number;
  };
}

export interface IndexCodeArgs {
  paths: string[];
}

export interface IndexCodeResult {
  indexed: number;
  failed: number;
  totalSnippets: number;
  performance: {
    indexingTime: number;
  };
}

/**
 * Extract code structure using Continue's tree-sitter parser
 */
export async function getCodeStructureTool(
  args: CodeStructureArgs,
  selectedPaths?: string[]
): Promise<CodeStructureResult> {
  const startTime = Date.now();

  // Determine which paths to analyze
  const paths = args.scope === 'selected'
    ? (selectedPaths || [])
    : args.paths;

  if (paths.length === 0) {
    return {
      scope: args.scope || 'paths',
      structures: [],
      performance: {
        extractionTime: 0,
        filesProcessed: 0,
      },
    };
  }

  try {
    // Use Continue's CodeSnippetsIndex to extract signatures
    const { groupedByUri } = await CodeSnippetsCodebaseIndex.getPathsAndSignatures(
      paths,
      0,                // uriOffset
      paths.length,     // uriBatchSize - process all paths
      0,                // snippetOffset
      1000              // snippetBatchSize - max snippets per file
    );

    // Format results
    const structures = Object.entries(groupedByUri).map(([path, signatures]) => ({
      path,
      signatures: signatures as string[],
      count: (signatures as string[]).length,
    }));

    const extractionTime = Date.now() - startTime;

    return {
      scope: args.scope || 'paths',
      structures,
      performance: {
        extractionTime,
        filesProcessed: paths.length,
      },
    };
  } catch (error) {
    console.error('Code structure extraction error:', error);

    // Return placeholder results on error
    return {
      scope: args.scope || 'paths',
      structures: paths.map(path => ({
        path,
        signatures: [],
        count: 0,
      })),
      performance: {
        extractionTime: Date.now() - startTime,
        filesProcessed: 0,
      },
    };
  }
}

/**
 * Index code files into the database for structure extraction
 */
export async function indexCodeTool(args: IndexCodeArgs): Promise<IndexCodeResult> {
  const startTime = Date.now();
  let indexed = 0;
  let failed = 0;
  let totalSnippets = 0;

  try {
    const db = await SqliteDb.get();

    // Create tables if they don't exist
    await db.exec(`CREATE TABLE IF NOT EXISTS code_snippets (
        id INTEGER PRIMARY KEY,
        path TEXT NOT NULL,
        cacheKey TEXT NOT NULL,
        content TEXT NOT NULL,
        title TEXT NOT NULL,
        signature TEXT,
        startLine INTEGER NOT NULL,
        endLine INTEGER NOT NULL
    )`);

    // Create a minimal IDE interface
    const fakeIde = {
      readFile: async (filepath: string) => {
        return fs.readFileSync(filepath, 'utf-8');
      }
    };

    const indexer = new CodeSnippetsCodebaseIndex(fakeIde as any);

    // Process each file
    for (const filepath of args.paths) {
      try {
        const contents = fs.readFileSync(filepath, 'utf-8');
        const snippets = await indexer.getSnippetsInFile(filepath, contents);

        // Store snippets in database
        for (const snippet of snippets) {
          await db.run(
            'INSERT OR REPLACE INTO code_snippets (path, cacheKey, content, title, signature, startLine, endLine) VALUES (?, ?, ?, ?, ?, ?, ?)',
            [
              filepath,
              'default', // Simple cache key
              snippet.content,
              snippet.title,
              snippet.signature,
              snippet.startLine,
              snippet.endLine
            ]
          );
          totalSnippets++;
        }

        indexed++;
      } catch (error) {
        console.error(`Failed to index ${filepath}:`, error);
        failed++;
      }
    }

    const indexingTime = Date.now() - startTime;

    return {
      indexed,
      failed,
      totalSnippets,
      performance: {
        indexingTime
      }
    };
  } catch (error) {
    console.error('Indexing error:', error);
    throw error;
  }
}
