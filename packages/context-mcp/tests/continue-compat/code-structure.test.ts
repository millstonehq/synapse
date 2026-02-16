/**
 * Code Structure Integration Tests
 *
 * Tests that validate our code structure extraction integration with @continuedev/core.
 *
 * These tests will catch breaking changes if:
 * - CodeSnippetsCodebaseIndex constructor signature changes
 * - getPathsAndSignatures static method changes
 * - getSnippetsInFile method changes
 * - SqliteDb.get() return type changes
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { CodeSnippetsCodebaseIndex } from '@continuedev/core/indexing/CodeSnippetsIndex.js';
import { SqliteDb } from '@continuedev/core/indexing/refreshIndex.js';
import * as fs from 'node:fs/promises';
import * as path from 'node:path';
import * as os from 'node:os';

describe('CodeSnippetsCodebaseIndex', () => {
  let testDir: string;
  let testFile: string;

  beforeAll(async () => {
    // Create a temporary test file with recognizable code structure
    testDir = path.join(os.tmpdir(), `code-structure-test-${Date.now()}`);
    await fs.mkdir(testDir, { recursive: true });

    testFile = path.join(testDir, 'test.ts');
    await fs.writeFile(
      testFile,
      `
export function helloWorld(): string {
  return 'Hello, World!';
}

export class TestClass {
  private value: number;

  constructor(value: number) {
    this.value = value;
  }

  getValue(): number {
    return this.value;
  }
}

export interface TestInterface {
  name: string;
  age: number;
}
`.trim()
    );
  });

  afterAll(async () => {
    await fs.rm(testDir, { recursive: true, force: true }).catch(() => {});
  });

  it('can be instantiated with IDE-like object', () => {
    const mockIde = {
      readFile: async (filepath: string) => {
        return fs.readFile(filepath, 'utf-8');
      },
    };

    const indexer = new CodeSnippetsCodebaseIndex(mockIde as any);
    expect(indexer).toBeDefined();
  });

  it('has getSnippetsInFile method', () => {
    const mockIde = {
      readFile: async (filepath: string) => {
        return fs.readFile(filepath, 'utf-8');
      },
    };

    const indexer = new CodeSnippetsCodebaseIndex(mockIde as any);
    expect(typeof indexer.getSnippetsInFile).toBe('function');
  });

  it('extracts snippets from TypeScript file', async () => {
    const mockIde = {
      readFile: async (filepath: string) => {
        return fs.readFile(filepath, 'utf-8');
      },
    };

    const indexer = new CodeSnippetsCodebaseIndex(mockIde as any);
    const content = await fs.readFile(testFile, 'utf-8');
    const snippets = await indexer.getSnippetsInFile(testFile, content);

    // Tree-sitter WASMs and queries are symlinked via vitest globalSetup
    expect(Array.isArray(snippets)).toBe(true);
    expect(snippets.length).toBeGreaterThan(0);

    // Verify snippet structure
    for (const snippet of snippets) {
      expect(snippet).toHaveProperty('content');
      expect(snippet).toHaveProperty('title');
      expect(snippet).toHaveProperty('startLine');
      expect(snippet).toHaveProperty('endLine');
      expect(typeof snippet.startLine).toBe('number');
      expect(typeof snippet.endLine).toBe('number');
    }

    // Should find our test function and class
    const titles = snippets.map((s: any) => s.title);
    expect(titles.some((t: string) => t.includes('helloWorld'))).toBe(true);
    expect(titles.some((t: string) => t.includes('TestClass'))).toBe(true);
  });

  it('has static getPathsAndSignatures method', () => {
    expect(typeof CodeSnippetsCodebaseIndex.getPathsAndSignatures).toBe(
      'function'
    );
  });

  it('getPathsAndSignatures returns expected structure', async () => {
    const result = await CodeSnippetsCodebaseIndex.getPathsAndSignatures(
      [testFile],
      0, // uriOffset
      1, // uriBatchSize
      0, // snippetOffset
      100 // snippetBatchSize
    );

    expect(result).toHaveProperty('groupedByUri');
    expect(typeof result.groupedByUri).toBe('object');

    // Should have extracted signatures from our test file
    const signatures = result.groupedByUri[testFile];
    if (signatures) {
      expect(Array.isArray(signatures)).toBe(true);
    }
  });
});

describe('SqliteDb for code snippets', () => {
  it('returns database with exec method', async () => {
    const db = await SqliteDb.get();
    expect(typeof db.exec).toBe('function');
  });

  it('returns database with run method', async () => {
    const db = await SqliteDb.get();
    expect(typeof db.run).toBe('function');
  });

  it('returns database with all method', async () => {
    const db = await SqliteDb.get();
    expect(typeof db.all).toBe('function');
  });

  it('can create custom tables', async () => {
    const db = await SqliteDb.get();

    // This mimics what code-structure.ts does
    await db.exec(`CREATE TABLE IF NOT EXISTS test_compat_check (
      id INTEGER PRIMARY KEY,
      value TEXT
    )`);

    // Clean up
    await db.exec('DROP TABLE IF EXISTS test_compat_check');
  });
});
