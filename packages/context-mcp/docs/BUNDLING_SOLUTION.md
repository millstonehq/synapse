# Continue Integration via Esbuild Bundling + Workerpool Shim

## Overview

This document describes how context-mcp integrates `@continuedev/core` for:
- **FTS5 full-text search** with BM25 ranking (lexical search)
- **LanceDB vector search** with embeddings (semantic search)
- **Tree-sitter code structure** extraction (40+ languages)

The integration requires workarounds due to issues in Continue's npm package.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         context-mcp server                               │
├─────────────────────────────────────────────────────────────────────────┤
│  dist/bundled/                                                           │
│  ├── file-search.js      (esbuild bundle of Continue's FTS5)            │
│  ├── semantic-search.js  (hybrid search: FTS5 + LanceDB embeddings)     │
│  └── code-structure.js   (esbuild bundle of Continue's tree-sitter)     │
│           │                                                              │
│           ├── import 'workerpool' (redirected by esbuild plugin)        │
│           └── import '../embeddings/*' (external, runtime resolution)   │
│           ▼                                                              │
│  dist/embeddings/                                                        │
│  ├── embeddings-provider.js  (TransformersJS wrapper)                   │
│  └── vector-index.js         (LanceDB wrapper)                          │
│           │                                                              │
│           │ Uses Continue's vendored transformers.js                     │
│           │ Downloads all-MiniLM-L6-v2 (~24MB) from HuggingFace          │
│           ▼                                                              │
│  dist/shims/                                                             │
│  ├── workerpool-shim.js  (intercepts pool() calls)                      │
│  └── continue-worker-paths.js (resolves worker paths)                   │
│           │                                                              │
│  node_modules/                                                           │
│  ├── workerpool/         (real workerpool package)                      │
│  ├── vectordb/           (LanceDB native bindings)                      │
│  └── @continuedev/core/                                                 │
│      ├── llm/            (worker pools for tokenization)                │
│      └── vendor/         (transformers.js for embeddings)               │
└─────────────────────────────────────────────────────────────────────────┘
```

## Semantic Search

### How It Works

The `semantic_search` tool combines two search strategies using **Reciprocal Rank Fusion (RRF)**:

1. **Lexical (FTS5)**: Fast exact-match search with BM25 ranking
2. **Semantic (LanceDB)**: Embedding-based similarity search using all-MiniLM-L6-v2

RRF merges results from both strategies, giving bonus scores to results that appear in both lists.

### Configuration

```typescript
semantic_search({
  query: "function that handles user authentication",
  mode: "hybrid",          // "hybrid" | "semantic" | "lexical"
  semantic_weight: 0.5,    // 0.0 = pure lexical, 1.0 = pure semantic
  max_results: 30,
  include_content: false,  // set true to include matched content
});
```

### First Run

On first use, the embedding model is downloaded from HuggingFace:
- Model: `Xenova/all-MiniLM-L6-v2` (~24MB quantized)
- Cache: `~/.cache/context-mcp/models/`
- Vector DB: `~/.continue/index/lancedb/`

### Dependencies

- **vectordb**: LanceDB native module for vector storage
- **onnxruntime-node**: ONNX runtime for embedding inference
- **@continuedev/core**: Provides transformers.js and LanceDbIndex

## Problems Solved

### Problem 1: Broken ESM Exports

Continue's compiled JavaScript has broken ESM imports:

```javascript
// In @continuedev/core/dist/indexing/FullTextSearchCodebaseIndex.js
import { RETRIEVAL_PARAMS } from "../util/parameters";  // Missing .js extension!
```

Node.js ESM requires explicit `.js` extensions for relative imports. This causes `ERR_MODULE_NOT_FOUND` errors.

**Solution:** Esbuild bundling resolves all imports at build time, eliminating the extension issue.

### Problem 2: `__dirname` Undefined in ESM

Continue uses `__dirname` which is undefined in ES modules:

```javascript
const workerPath = path.join(__dirname, 'worker.js');  // Fails in ESM
```

**Solution:** Esbuild banner injects a polyfill:

```javascript
const __dirname = dirname(fileURLToPath(import.meta.url));
```

### Problem 3: Dynamic Worker Thread Loading

Continue's `ChunkCodebaseIndex` spawns worker threads at runtime:

```javascript
// In asyncEncoder.js
this.workerPool = workerpool.pool(
  workerCodeFilePath("llamaTokenizerWorkerPool.mjs")
);

// workerCodeFilePath() does:
path.join(__dirname, filename)
```

After bundling, `__dirname` resolves to `dist/bundled/`, but worker files remain in `node_modules/@continuedev/core/llm/`. The workers cannot be found.

**Solution:** Workerpool shim intercepts `pool()` calls and rewrites paths:

```
dist/bundled/tiktokenWorkerPool.mjs (doesn't exist)
        ↓ resolveWorkerPath()
node_modules/@continuedev/core/llm/tiktokenWorkerPool.mjs (actual file)
```

## Implementation

### File: `src/shims/continue-worker-paths.ts`

Resolves worker filenames to their actual paths in node_modules:

```typescript
export function resolveCoreRoot(): string {
  // Uses Node's module resolution to find @continuedev/core
  const require = createRequire(import.meta.url);
  const pkgPath = require.resolve('@continuedev/core/package.json');
  return path.dirname(pkgPath);
}

export async function buildWorkerManifest(): Promise<Record<string, string>> {
  // Scans @continuedev/core for *worker*.mjs files
  // Returns: { 'tiktokenWorkerPool.mjs': '/abs/path/to/file.mjs', ... }
}

export function resolveWorkerPathSync(input: string): string {
  // If input path exists, return it
  // Otherwise, look up basename in manifest and return real path
}
```

### File: `src/shims/workerpool-shim.ts`

Drop-in replacement for workerpool that rewrites paths:

```typescript
const realWorkerpool = require('workerpool');

export function pool(script?: string, options?: PoolOptions): Pool {
  let resolvedScript = script;

  if (typeof script === 'string' && !fs.existsSync(script)) {
    resolvedScript = resolveWorkerPathSync(script);
  }

  return realWorkerpool.pool(resolvedScript, options);
}
```

### File: `bundle-continue.js`

Esbuild configuration with workerpool redirect plugin:

```javascript
function redirectWorkerpoolForContinue() {
  return {
    name: 'redirect-workerpool-for-continue',
    setup(build) {
      build.onResolve({ filter: /^workerpool$/ }, (args) => {
        // Only redirect imports from @continuedev/core
        if (args.importer.includes('node_modules/@continuedev/core')) {
          return { path: '../shims/workerpool-shim.js', external: true };
        }
        return { path: 'workerpool', external: true };
      });
    },
  };
}
```

## Build Process

```bash
npm run build
# 1. tsc compiles src/ to dist/
# 2. bundle-continue.js:
#    a. Compiles shims to dist/shims/
#    b. Bundles Continue modules to dist/bundled/ with:
#       - workerpool imports redirected to shim
#       - __dirname polyfill injected
#       - Native modules externalized
```

## Maintenance

### When Continue Updates

The shim is designed to be resilient:

1. **Worker file renames**: Glob pattern `*[Ww]orker*.mjs` catches common conventions
2. **Worker file moves**: Full recursive scan of @continuedev/core
3. **New worker files**: Auto-discovered by manifest scan

### Breaking Changes to Watch For

- Continue stops using `workerpool` library
- Continue changes to native `worker_threads`
- Fundamental changes to tokenization architecture

### Files to Modify

| File | Purpose |
|------|---------|
| `src/shims/continue-worker-paths.ts` | Worker path resolution |
| `src/shims/workerpool-shim.ts` | Workerpool interception |
| `bundle-continue.js` | Esbuild configuration |

## Performance

| Operation | Time | Notes |
|-----------|------|-------|
| First FTS search (cold) | ~9s | Builds FTS5 index for 500+ files |
| Subsequent FTS searches | ~10ms | Index is cached in memory |
| First semantic search (cold) | ~30-60s | Downloads model + builds embeddings |
| Subsequent semantic searches | ~50-200ms | Depends on query complexity |
| Hybrid search | ~100-300ms | Runs both in parallel + RRF merge |
| Worker path resolution | <1ms | Manifest is cached |

## Debugging

### Check if shim is working

Look for these log lines during startup:

```
[workerpool-shim] Resolved worker path: .../dist/bundled/tiktokenWorkerPool.mjs -> .../node_modules/@continuedev/core/llm/tiktokenWorkerPool.mjs
[continue-worker-paths] Built manifest with 3 workers: [...]
```

### If FTS5 fails

1. Check that worker files exist in node_modules
2. Verify the shim is being used (check esbuild output for redirect message)
3. Check that workerpool is installed

### If Semantic Search fails

1. Check that vectordb is installed (native module)
2. Check model cache at `~/.cache/context-mcp/models/`
3. Check vector DB at `~/.continue/index/lancedb/`
4. LanceDB may not be available on all platforms (ARM Linux)

---

**Version:** 0.5.0
**Updated:** 2025-11-27
**New in 0.5.0:** Added semantic search with LanceDB + TransformersJS embeddings
