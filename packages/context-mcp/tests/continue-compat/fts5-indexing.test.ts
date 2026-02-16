/**
 * FTS5 Indexing Integration Tests
 *
 * Tests that validate our FTS5 indexing integration with @continuedev/core.
 *
 * These tests will catch breaking changes if:
 * - FullTextSearchCodebaseIndex constructor signature changes
 * - ChunkCodebaseIndex constructor signature changes
 * - getComputeDeleteAddRemove return shape changes
 * - IndexTag interface changes
 * - Chunk interface changes
 */

import { describe, it, expect } from 'vitest';
import { FullTextSearchCodebaseIndex } from '@continuedev/core/indexing/FullTextSearchCodebaseIndex.js';
import { ChunkCodebaseIndex } from '@continuedev/core/indexing/chunk/ChunkCodebaseIndex.js';
import {
  getComputeDeleteAddRemove,
  SqliteDb,
} from '@continuedev/core/indexing/refreshIndex.js';
import type { IndexTag, Chunk } from '@continuedev/core';

describe('FullTextSearchCodebaseIndex', () => {
  it('can be instantiated without arguments', () => {
    const fts = new FullTextSearchCodebaseIndex();
    expect(fts).toBeDefined();
  });

  it('has a retrieve method', () => {
    const fts = new FullTextSearchCodebaseIndex();
    expect(typeof fts.retrieve).toBe('function');
  });

  it('has an update method (generator)', () => {
    const fts = new FullTextSearchCodebaseIndex();
    expect(typeof fts.update).toBe('function');
  });

  it('has an artifactId property', () => {
    const fts = new FullTextSearchCodebaseIndex();
    expect(fts.artifactId).toBeDefined();
    expect(typeof fts.artifactId).toBe('string');
  });
});

describe('ChunkCodebaseIndex', () => {
  it('can be instantiated with expected arguments', () => {
    // ChunkCodebaseIndex needs (readFile, continueServerClient, maxChunkSize)
    const mockReadFile = async (path: string) => 'content';
    const mockServerClient = {
      connected: false,
      url: undefined,
      getUserToken: () => undefined,
      getConfig: async () => ({ configJson: '{}' }),
      getFromIndexCache: async () => ({ files: {} }),
    };

    const chunkIndex = new ChunkCodebaseIndex(
      mockReadFile,
      mockServerClient as any,
      512
    );

    expect(chunkIndex).toBeDefined();
  });

  it('has an update method', () => {
    const mockReadFile = async (path: string) => 'content';
    const mockServerClient = {
      connected: false,
      url: undefined,
      getUserToken: () => undefined,
      getConfig: async () => ({ configJson: '{}' }),
      getFromIndexCache: async () => ({ files: {} }),
    };

    const chunkIndex = new ChunkCodebaseIndex(
      mockReadFile,
      mockServerClient as any,
      512
    );

    expect(typeof chunkIndex.update).toBe('function');
  });

  it('has an artifactId property', () => {
    const mockReadFile = async (path: string) => 'content';
    const mockServerClient = {
      connected: false,
      url: undefined,
      getUserToken: () => undefined,
      getConfig: async () => ({ configJson: '{}' }),
      getFromIndexCache: async () => ({ files: {} }),
    };

    const chunkIndex = new ChunkCodebaseIndex(
      mockReadFile,
      mockServerClient as any,
      512
    );

    expect(chunkIndex.artifactId).toBeDefined();
    expect(typeof chunkIndex.artifactId).toBe('string');
  });
});

describe('getComputeDeleteAddRemove', () => {
  it('is a function', () => {
    expect(typeof getComputeDeleteAddRemove).toBe('function');
  });

  it('returns expected shape', async () => {
    const tag: IndexTag = {
      branch: 'main',
      directory: '/tmp/test-dir',
      artifactId: 'test',
    };

    const fileStats = {};
    const readFile = async (path: string) => '';

    const [results, pathsAndCacheKeys, markComplete] =
      await getComputeDeleteAddRemove(tag, fileStats, readFile, undefined);

    // Verify results structure
    expect(results).toHaveProperty('compute');
    expect(results).toHaveProperty('del');
    expect(results).toHaveProperty('addTag');
    expect(results).toHaveProperty('removeTag');

    // Verify arrays
    expect(Array.isArray(results.compute)).toBe(true);
    expect(Array.isArray(results.del)).toBe(true);
    expect(Array.isArray(results.addTag)).toBe(true);
    expect(Array.isArray(results.removeTag)).toBe(true);

    // Verify markComplete is a function
    expect(typeof markComplete).toBe('function');
  });
});

describe('SqliteDb', () => {
  it('has a static get method', () => {
    expect(typeof SqliteDb.get).toBe('function');
  });

  it('returns a database connection', async () => {
    const db = await SqliteDb.get();
    expect(db).toBeDefined();
    expect(typeof db.exec).toBe('function');
    expect(typeof db.run).toBe('function');
  });
});

describe('IndexTag interface', () => {
  it('accepts expected structure', () => {
    const tag: IndexTag = {
      branch: 'main',
      directory: '/path/to/dir',
      artifactId: 'chunks',
    };

    expect(tag.branch).toBe('main');
    expect(tag.directory).toBe('/path/to/dir');
    expect(tag.artifactId).toBe('chunks');
  });
});

describe('Chunk interface', () => {
  it('type can be constructed with expected properties', () => {
    // This test validates at compile-time that our expected Chunk properties exist
    const chunk: Partial<Chunk> = {
      filepath: '/path/to/file.ts',
      content: 'const x = 1;',
      startLine: 0,
      endLine: 1,
    };

    expect(chunk.filepath).toBeDefined();
    expect(chunk.content).toBeDefined();
    expect(chunk.startLine).toBeDefined();
    expect(chunk.endLine).toBeDefined();
  });
});
