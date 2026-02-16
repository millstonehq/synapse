/**
 * Vitest Global Setup
 *
 * Sets up tree-sitter WASM and query files for Continue compatibility.
 *
 * Continue's treeSitter.ts expects:
 * - WASMs at: <util-dir>/node_modules/tree-sitter-wasms/out/ (when NODE_ENV=test)
 * - Queries at: <core-root>/extensions/vscode/tree-sitter/code-snippet-queries/ (when NODE_ENV=test)
 *
 * We symlink our local files to those locations.
 */

import { createRequire } from 'node:module';
import * as fs from 'node:fs';
import * as path from 'node:path';

const require = createRequire(import.meta.url);

function ensureSymlink(sourceDir: string, targetDir: string, name: string) {
  if (fs.existsSync(targetDir)) {
    const stats = fs.lstatSync(targetDir);
    if (stats.isSymbolicLink()) {
      const linkTarget = fs.readlinkSync(targetDir);
      if (linkTarget === sourceDir) {
        console.log(`[setup] ${name} symlink already exists`);
        return;
      }
      // Remove stale symlink
      fs.unlinkSync(targetDir);
    } else {
      // It's a real directory, leave it alone
      console.log(`[setup] ${name} directory exists (not symlink)`);
      return;
    }
  }

  // Create parent directories
  fs.mkdirSync(path.dirname(targetDir), { recursive: true });

  // Create symlink
  fs.symlinkSync(sourceDir, targetDir, 'dir');
  console.log(`[setup] Created ${name} symlink: ${targetDir} -> ${sourceDir}`);
}

export function setup() {
  const continueCorePath = path.dirname(
    require.resolve('@continuedev/core/package.json')
  );

  // 1. WASM files: <util>/node_modules/tree-sitter-wasms/out/
  const wasmSourceDir = path.resolve(__dirname, '..', 'src', 'tree-sitter', 'wasms');
  const wasmTargetDir = path.join(
    continueCorePath,
    'util',
    'node_modules',
    'tree-sitter-wasms',
    'out'
  );
  ensureSymlink(wasmSourceDir, wasmTargetDir, 'Tree-sitter WASM');

  // 2. Query files: <core>/extensions/vscode/tree-sitter/code-snippet-queries/
  // Continue's getQueryForFile looks for:
  //   __dirname/../extensions/vscode/tree-sitter/code-snippet-queries/<lang>.scm (when NODE_ENV=test)
  const querySourceDir = path.resolve(__dirname, '..', 'src', 'tree-sitter', 'code-snippet-queries');
  const queryTargetDir = path.join(
    continueCorePath,
    'extensions',
    'vscode',
    'tree-sitter',
    'code-snippet-queries'
  );
  ensureSymlink(querySourceDir, queryTargetDir, 'Tree-sitter query');
}

export function teardown() {
  // Leave symlinks in place for faster subsequent runs
}
