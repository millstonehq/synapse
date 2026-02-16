/**
 * Workerpool Shim for Continue Integration
 *
 * This shim wraps workerpool to intercept pool() calls and resolve worker paths
 * to their actual locations in node_modules/@continuedev/core.
 *
 * When @continuedev/core is bundled, its __dirname points to the bundle output
 * directory, but worker files remain in node_modules. This shim bridges that gap.
 *
 * IMPORTANT: This file should be used as an alias for 'workerpool' ONLY for
 * imports originating from @continuedev/core. Other imports should use the
 * real workerpool directly.
 *
 * @see docs/BUNDLING_SOLUTION.md for architecture details
 */

import fs from 'node:fs';
import { createRequire } from 'node:module';
import { resolveWorkerPathSync, prewarmManifest } from './continue-worker-paths.js';

// Use permissive types - workerpool doesn't have good TypeScript definitions
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type Pool = any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type PoolOptions = any;

// Load workerpool SYNCHRONOUSLY using require()
// This is necessary because Continue calls pool() during module initialization
const require = createRequire(import.meta.url);
const realWorkerpool = require('workerpool') as typeof import('workerpool');

// Pre-warm the worker manifest in the background (non-blocking)
prewarmManifest().catch((err) => {
  console.error('[workerpool-shim] Failed to prewarm manifest:', err);
});

/**
 * Create a worker pool with path resolution for Continue workers.
 *
 * If the worker path doesn't exist (common when bundled), we resolve it
 * to the actual location in node_modules/@continuedev/core.
 */
export function pool(script?: string, options?: PoolOptions): Pool {
  let resolvedScript = script;

  if (typeof script === 'string' && !fs.existsSync(script)) {
    resolvedScript = resolveWorkerPathSync(script);
    console.error(`[workerpool-shim] Resolved worker path: ${script} -> ${resolvedScript}`);
  }

  return realWorkerpool.pool(resolvedScript, options);
}

/**
 * Create a worker that can be managed by the pool.
 * Passed through to real workerpool without modification.
 */
export function worker(
  methods?: Record<string, (...args: unknown[]) => unknown>,
  options?: { onTerminate?: () => void }
): void {
  return realWorkerpool.worker(methods, options);
}

// Re-export workerpool utilities
export const cpus = realWorkerpool.cpus;
export const isMainThread = realWorkerpool.isMainThread;
export const platform = realWorkerpool.platform;

// Default export mimics workerpool's default export
export default {
  pool,
  worker,
  cpus,
  isMainThread,
  platform,
};
