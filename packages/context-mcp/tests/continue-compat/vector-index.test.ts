/**
 * Vector Index Integration Tests
 *
 * Tests that validate our LanceDB vector index integration with @continuedev/core.
 *
 * These tests will catch breaking changes if:
 * - LanceDbIndex.create factory signature changes
 * - isSupportedLanceDbCpuTargetForLinux export changes
 * - LanceDbIndex retrieve/update method signatures change
 */

import { describe, it, expect } from 'vitest';
import { LanceDbIndex } from '@continuedev/core/indexing/LanceDbIndex.js';

describe('LanceDbIndex', () => {
  it('has a static create factory method', () => {
    expect(typeof LanceDbIndex.create).toBe('function');
  });

  it('create method accepts embeddingsProvider and readFile', async () => {
    // Create a minimal mock embeddings provider
    const mockEmbeddingsProvider = {
      model: 'test-model',
      embeddingId: 'test::model',
      maxEmbeddingChunkSize: 512,
      maxEmbeddingBatchSize: 32,
      embed: async (chunks: string[]) => {
        // Return dummy 384-dimensional embeddings
        return chunks.map(() => new Array(384).fill(0.1));
      },
      providerName: 'test',
      uniqueId: 'test-id',
      contextLength: 512,
    };

    const mockReadFile = async (path: string) => 'content';

    // This tests that the factory method signature hasn't changed
    // It may return null if LanceDB native bindings aren't available
    const index = await LanceDbIndex.create(
      mockEmbeddingsProvider as any,
      mockReadFile
    );

    // Index might be null on unsupported platforms
    expect(index === null || typeof index === 'object').toBe(true);
  });
});

describe('LanceDB platform support check', () => {
  it('isSupportedLanceDbCpuTargetForLinux function exists', async () => {
    // This import path may change - catching it is the point
    const configUtil = await import('@continuedev/core/config/util.js');

    expect(
      typeof configUtil.isSupportedLanceDbCpuTargetForLinux
    ).toBe('function');
  });

  it('isSupportedLanceDbCpuTargetForLinux returns boolean', async () => {
    const { isSupportedLanceDbCpuTargetForLinux } = await import(
      '@continuedev/core/config/util.js'
    );

    const result = isSupportedLanceDbCpuTargetForLinux();
    expect(typeof result).toBe('boolean');
  });
});

describe('BranchAndDir type', () => {
  it('BranchAndDir type is used correctly in our code', async () => {
    // BranchAndDir is a type import, not a runtime value
    // We verify the type exists by ensuring our vector-index.ts compiles
    // This is a compile-time check - if the type changes, TypeScript fails

    // Runtime check: our LanceDbIndex import works
    const { LanceDbIndex } = await import(
      '@continuedev/core/indexing/LanceDbIndex.js'
    );
    expect(LanceDbIndex).toBeDefined();
  });
});
