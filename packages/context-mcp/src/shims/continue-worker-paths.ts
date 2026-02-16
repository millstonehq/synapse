/**
 * Continue Worker Path Resolution
 *
 * Resolves worker filenames to their actual paths in node_modules/@continuedev/core.
 * This shim enables Continue's worker-based tokenization to work when the main code
 * is bundled to a different location than the worker files.
 *
 * @see docs/BUNDLING_SOLUTION.md for architecture details
 */

import { createRequire } from 'node:module';
import path from 'node:path';
import fs from 'node:fs';
import { glob } from 'glob';

export type WorkerManifest = Record<string, string>;

// Cached manifest - built once per process
let manifest: WorkerManifest | null = null;
let coreRootCache: string | null = null;

/**
 * Locate @continuedev/core's package root in node_modules.
 * Uses Node's standard module resolution - works with npm/yarn/pnpm.
 */
export function resolveCoreRoot(): string {
  if (coreRootCache) return coreRootCache;

  const require = createRequire(import.meta.url);
  const pkgPath = require.resolve('@continuedev/core/package.json');
  coreRootCache = path.dirname(pkgPath);

  return coreRootCache;
}

/**
 * Build a manifest mapping worker basenames to absolute paths.
 * Scans @continuedev/core for files matching worker naming conventions.
 *
 * @param opts.cache - Whether to cache the result (default: true)
 * @param opts.patterns - Glob patterns to match worker files
 */
export async function buildWorkerManifest(opts?: {
  cache?: boolean;
  patterns?: string[];
}): Promise<WorkerManifest> {
  const useCache = opts?.cache ?? true;

  if (useCache && manifest) {
    return manifest;
  }

  const coreRoot = resolveCoreRoot();
  const patterns = opts?.patterns ?? [
    '**/*[Ww]orker*.mjs',
    '**/*[Ww]orker*.js',
  ];

  const result: WorkerManifest = {};

  for (const pattern of patterns) {
    const files = await glob(pattern, {
      cwd: coreRoot,
      ignore: ['**/node_modules/**'],
    });

    for (const file of files) {
      const basename = path.basename(file);
      const absolutePath = path.join(coreRoot, file);

      // Prefer files in 'llm' directory if duplicates exist
      if (!result[basename] || file.includes('/llm/')) {
        result[basename] = absolutePath;
      }
    }
  }

  if (useCache) {
    manifest = result;
  }

  console.error(`[continue-worker-paths] Built manifest with ${Object.keys(result).length} workers:`, Object.keys(result));

  return result;
}

/**
 * Resolve a worker path to its actual location.
 *
 * If the input path exists, returns it unchanged.
 * Otherwise, looks up the basename in the worker manifest.
 *
 * @param input - The worker path (may be invalid due to bundling)
 * @returns The resolved absolute path to the worker file
 */
export async function resolveWorkerPath(input: string): Promise<string> {
  // If the path already exists, no resolution needed
  if (fs.existsSync(input)) {
    return input;
  }

  const basename = path.basename(input);
  const m = await buildWorkerManifest();

  // Try manifest lookup
  if (m[basename] && fs.existsSync(m[basename])) {
    console.error(`[continue-worker-paths] Resolved ${basename} -> ${m[basename]}`);
    return m[basename];
  }

  // Fallback: try common subdirectories
  const coreRoot = resolveCoreRoot();
  const fallbackDirs = ['llm', 'dist/llm', 'codebase', 'indexing'];

  for (const dir of fallbackDirs) {
    const candidate = path.join(coreRoot, dir, basename);
    if (fs.existsSync(candidate)) {
      console.error(`[continue-worker-paths] Resolved ${basename} via fallback -> ${candidate}`);
      return candidate;
    }
  }

  // Give up - return original and let it fail naturally
  console.error(`[continue-worker-paths] Could not resolve ${basename}, returning original path`);
  return input;
}

/**
 * Synchronous version of resolveWorkerPath.
 * Uses cached manifest if available, otherwise builds it synchronously.
 */
export function resolveWorkerPathSync(input: string): string {
  if (fs.existsSync(input)) {
    return input;
  }

  const basename = path.basename(input);

  // If manifest is cached, use it
  if (manifest && manifest[basename] && fs.existsSync(manifest[basename])) {
    return manifest[basename];
  }

  // Fallback: try common subdirectories synchronously
  const coreRoot = resolveCoreRoot();
  const fallbackDirs = ['llm', 'dist/llm', 'codebase', 'indexing'];

  for (const dir of fallbackDirs) {
    const candidate = path.join(coreRoot, dir, basename);
    if (fs.existsSync(candidate)) {
      console.error(`[continue-worker-paths] Resolved ${basename} via sync fallback -> ${candidate}`);
      return candidate;
    }
  }

  return input;
}

/**
 * Pre-warm the manifest cache.
 * Call this at startup to avoid async resolution during first worker spawn.
 */
export async function prewarmManifest(): Promise<void> {
  await buildWorkerManifest();
}
