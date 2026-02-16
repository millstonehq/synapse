/**
 * Worker Paths Shim Tests
 *
 * Tests that validate our workerpool shim correctly resolves worker paths
 * to their actual locations in node_modules/@continuedev/core.
 *
 * These tests will catch breaking changes if:
 * - Worker file naming conventions change (e.g., *Worker*.mjs pattern)
 * - Worker file locations change (e.g., moved from llm/ to another dir)
 * - Continue removes or renames worker files
 */

import { describe, it, expect, beforeAll } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import {
  buildWorkerManifest,
  resolveWorkerPath,
  resolveWorkerPathSync,
  resolveCoreRoot,
  prewarmManifest,
} from '../../src/shims/continue-worker-paths.js';

describe('continue-worker-paths', () => {
  describe('resolveCoreRoot', () => {
    it('finds @continuedev/core package root', () => {
      const coreRoot = resolveCoreRoot();
      expect(coreRoot).toBeDefined();
      expect(fs.existsSync(coreRoot)).toBe(true);
      expect(fs.existsSync(path.join(coreRoot, 'package.json'))).toBe(true);
    });

    it('returns a path containing node_modules/@continuedev/core', () => {
      const coreRoot = resolveCoreRoot();
      expect(coreRoot).toContain('@continuedev');
      expect(coreRoot).toContain('core');
    });
  });

  describe('buildWorkerManifest', () => {
    it('finds worker files in @continuedev/core', async () => {
      const manifest = await buildWorkerManifest({ cache: false });
      expect(Object.keys(manifest).length).toBeGreaterThan(0);
    });

    it('finds tokenizer worker (tiktoken or llama)', async () => {
      const manifest = await buildWorkerManifest({ cache: false });
      const workerNames = Object.keys(manifest);

      // Should find at least one tokenizer-related worker
      const hasTokenizerWorker = workerNames.some(
        (k) =>
          k.toLowerCase().includes('tiktoken') ||
          k.toLowerCase().includes('llama') ||
          k.toLowerCase().includes('token')
      );

      expect(hasTokenizerWorker).toBe(true);
    });

    it('manifest entries point to existing files', async () => {
      const manifest = await buildWorkerManifest({ cache: false });

      for (const [basename, absolutePath] of Object.entries(manifest)) {
        expect(fs.existsSync(absolutePath)).toBe(true);
        expect(path.basename(absolutePath)).toBe(basename);
      }
    });

    it('worker files are .mjs or .js files', async () => {
      const manifest = await buildWorkerManifest({ cache: false });

      for (const basename of Object.keys(manifest)) {
        const ext = path.extname(basename);
        expect(['.mjs', '.js']).toContain(ext);
      }
    });
  });

  describe('resolveWorkerPath (async)', () => {
    beforeAll(async () => {
      // Prewarm manifest for resolution tests
      await prewarmManifest();
    });

    it('returns existing paths unchanged', async () => {
      const existingPath = path.join(resolveCoreRoot(), 'package.json');
      const resolved = await resolveWorkerPath(existingPath);
      expect(resolved).toBe(existingPath);
    });

    it('resolves non-existent paths to real worker locations', async () => {
      const manifest = await buildWorkerManifest();
      const workerBasename = Object.keys(manifest)[0];

      if (workerBasename) {
        const fakePath = `/nonexistent/path/${workerBasename}`;
        const resolved = await resolveWorkerPath(fakePath);

        expect(fs.existsSync(resolved)).toBe(true);
        expect(resolved).toContain('@continuedev');
      }
    });
  });

  describe('resolveWorkerPathSync', () => {
    beforeAll(async () => {
      // Prewarm manifest for sync resolution
      await prewarmManifest();
    });

    it('returns existing paths unchanged', () => {
      const existingPath = path.join(resolveCoreRoot(), 'package.json');
      const resolved = resolveWorkerPathSync(existingPath);
      expect(resolved).toBe(existingPath);
    });

    it('resolves worker basename to actual path', async () => {
      const manifest = await buildWorkerManifest();
      const workerBasename = Object.keys(manifest)[0];

      if (workerBasename) {
        const fakePath = `/nonexistent/path/${workerBasename}`;
        const resolved = resolveWorkerPathSync(fakePath);

        expect(fs.existsSync(resolved)).toBe(true);
      }
    });
  });

  describe('prewarmManifest', () => {
    it('completes without error', async () => {
      await expect(prewarmManifest()).resolves.toBeUndefined();
    });
  });
});
