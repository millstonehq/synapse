/**
 * Bundle Continue's indexing modules with esbuild
 *
 * This resolves ESM import issues in @continuedev/core and sets up
 * the workerpool shim to handle dynamic worker path resolution.
 *
 * @see docs/BUNDLING_SOLUTION.md for architecture details
 */

import * as esbuild from 'esbuild';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Esbuild plugin to redirect workerpool imports from @continuedev/core
 * to our shim. This allows us to intercept worker path resolution.
 *
 * IMPORTANT: Only redirects imports originating from @continuedev/core.
 * Other imports (including our shim's own import) resolve normally.
 */
function redirectWorkerpoolForContinue() {
  const corePathFragment = `node_modules${path.sep}@continuedev${path.sep}core`;
  // Use relative path from bundled output directory to shims directory
  const shimRelativePath = '../shims/workerpool-shim.js';

  return {
    name: 'redirect-workerpool-for-continue',
    setup(build) {
      build.onResolve({ filter: /^workerpool$/ }, (args) => {
        // Only rewrite imports originating from inside @continuedev/core
        if (args.importer && args.importer.includes(corePathFragment)) {
          console.log(`[esbuild] Redirecting workerpool import from ${args.importer} to shim`);
          // Mark as external with the relative path - don't inline the shim
          return { path: shimRelativePath, external: true };
        }
        // Let all other imports resolve normally (mark as external)
        return { path: 'workerpool', external: true };
      });
    },
  };
}

// First, compile the shims (they need to exist before being referenced)
// Shims are NOT bundled - they import workerpool at runtime
console.log('📦 Building shims...');
await esbuild.build({
  entryPoints: [
    'src/shims/continue-worker-paths.ts',
    'src/shims/workerpool-shim.ts',
  ],
  bundle: false, // Don't bundle - imports resolve at runtime
  platform: 'node',
  format: 'esm',
  outdir: 'dist/shims',
});
console.log('✅ Built shims');

// Build embeddings modules (separate from main bundle due to transformers.js)
console.log('📦 Building embeddings modules...');
await esbuild.build({
  entryPoints: [
    'src/embeddings/embeddings-provider.ts',
    'src/embeddings/vector-index.ts',
  ],
  bundle: false, // Don't bundle - dynamic imports for transformers.js
  platform: 'node',
  format: 'esm',
  outdir: 'dist/embeddings',
});
console.log('✅ Built embeddings modules');

// Now bundle Continue modules with the workerpool redirect plugin
console.log('📦 Bundling Continue modules...');
await esbuild.build({
  entryPoints: [
    'src/tools/file-search.ts',
    'src/tools/code-structure.ts',
    'src/tools/semantic-search.ts',
  ],
  bundle: true,
  platform: 'node',
  format: 'esm',
  outdir: 'dist/bundled',
  plugins: [
    redirectWorkerpoolForContinue(),
  ],
  external: [
    '@modelcontextprotocol/*',
    'tiktoken',
    'glob',
    'ignore',
    'fs',
    'path',
    'child_process',
    'module',
    'url',
    'os',
    'sqlite3',           // Native module - can't bundle
    'better-sqlite3',    // Native module - can't bundle
    'tree-sitter',       // Native module - can't bundle
    '@vscode/sqlite3',   // Native module - can't bundle
    'vectordb',          // LanceDB native module - can't bundle
    'onnxruntime-node',  // ONNX native module for transformers.js
    '../embeddings/*',   // Embeddings modules - resolve at runtime
    // Note: workerpool is handled by the plugin, not listed here
  ],
  banner: {
    js: 'import { createRequire } from "module"; import { fileURLToPath } from "url"; import { dirname } from "path"; const require = createRequire(import.meta.url); const __filename = fileURLToPath(import.meta.url); const __dirname = dirname(__filename);'
  }
});

console.log('✅ Bundled Continue modules with workerpool shim');

// Copy tree-sitter query files
const srcQueriesDir = 'src/tree-sitter/code-snippet-queries';
const destQueriesDir = 'dist/tree-sitter/code-snippet-queries';

fs.mkdirSync(destQueriesDir, { recursive: true });

const queryFiles = fs.readdirSync(srcQueriesDir);
for (const file of queryFiles) {
  if (file.endsWith('.scm')) {
    fs.copyFileSync(
      path.join(srcQueriesDir, file),
      path.join(destQueriesDir, file)
    );
  }
}

console.log(`✅ Copied ${queryFiles.length} tree-sitter query files`);

// Copy tree-sitter WASM files
const srcWasmsDir = 'src/tree-sitter/wasms';
const destWasmsDir = 'dist/bundled/tree-sitter-wasms';

fs.mkdirSync(destWasmsDir, { recursive: true });

const wasmFiles = fs.readdirSync(srcWasmsDir);
for (const file of wasmFiles) {
  if (file.endsWith('.wasm')) {
    fs.copyFileSync(
      path.join(srcWasmsDir, file),
      path.join(destWasmsDir, file)
    );
  }
}

// Also copy main tree-sitter.wasm to dist/bundled/ for Continue's code
fs.copyFileSync(
  path.join(srcWasmsDir, 'tree-sitter.wasm'),
  path.join('dist/bundled', 'tree-sitter.wasm')
);

console.log(`✅ Copied ${wasmFiles.filter(f => f.endsWith('.wasm')).length} tree-sitter WASM files`);
