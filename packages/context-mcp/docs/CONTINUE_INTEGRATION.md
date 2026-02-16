# Continue Integration Architecture

## Overview

Context-MCP integrates with `@continuedev/core` to provide code indexing, full-text search, semantic search, and code structure extraction. Continue's codebase was designed for VS Code extension contexts, not standalone Node.js usage, so we use several shims and workarounds to make it work.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              context-mcp                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ file_search │  │semantic_    │  │ code_       │  │ (future tools)      │ │
│  │   (FTS5)    │  │   search    │  │  structure  │  │                     │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────────────────────┘ │
│         │                │                │                                  │
│         ▼                ▼                ▼                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         Shim Layer                                    │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────┐  │   │
│  │  │  workerpool-shim │  │ embeddings-      │  │   ContinueIDE      │  │   │
│  │  │  (worker paths)  │  │   provider       │  │ (IDE interface)    │  │   │
│  │  └────────┬─────────┘  └────────┬─────────┘  └─────────┬──────────┘  │   │
│  └───────────┼─────────────────────┼──────────────────────┼─────────────┘   │
│              │                     │                      │                  │
└──────────────┼─────────────────────┼──────────────────────┼──────────────────┘
               │                     │                      │
               ▼                     ▼                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          @continuedev/core                                    │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  ┌────────────┐  │
│  │ FullTextSearch │  │  LanceDbIndex  │  │  CodeSnippets  │  │ workerpool │  │
│  │ CodebaseIndex  │  │ (vector search)│  │ CodebaseIndex  │  │  (workers) │  │
│  └────────────────┘  └────────────────┘  └────────────────┘  └────────────┘  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                  │
│  │  ChunkCodebase │  │ transformers.js│  │  tree-sitter   │                  │
│  │     Index      │  │   (vendored)   │  │    (WASM)      │                  │
│  └────────────────┘  └────────────────┘  └────────────────┘                  │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Shims Explained

### 1. Workerpool Shim (`src/shims/workerpool-shim.ts`)

**Problem:** Continue uses `workerpool` for CPU-intensive tasks (tokenization). When bundled with esbuild, Continue's `__dirname` points to our `dist/` directory, but worker files remain in `node_modules/@continuedev/core/llm/`.

**Solution:** Intercept `workerpool.pool()` calls and resolve worker paths to their actual locations.

```
┌─────────────────────────────────────────────────────────────────┐
│ Continue calls: workerpool.pool('/dist/bundled/worker.mjs')     │
│                              ↓                                   │
│ workerpool-shim intercepts and resolves:                        │
│   '/dist/bundled/worker.mjs' → '/node_modules/.../worker.mjs'   │
│                              ↓                                   │
│ Real workerpool.pool() called with correct path                 │
└─────────────────────────────────────────────────────────────────┘
```

**Files:**
- `src/shims/workerpool-shim.ts` - Intercepts pool() calls
- `src/shims/continue-worker-paths.ts` - Builds manifest of worker file locations

### 2. Embeddings Provider (`src/embeddings/embeddings-provider.ts`)

**Problem:** Continue's `TransformersJsEmbeddingsProvider` doesn't work standalone because:
- It disables remote model downloads by default
- It expects VS Code extension context for caching

**Solution:** Custom provider that:
- Enables `env.allowRemoteModels = true` for HuggingFace downloads
- Sets a persistent cache directory at `~/.cache/context-mcp/models/`
- Implements minimal `ILLM` interface for `LanceDbIndex`

### 3. ContinueIDE (`src/continue/ContinueIDE.ts`)

**Problem:** Continue's indexing requires an `IDE` interface (designed for VS Code).

**Solution:** Minimal implementation with:
- File system operations (`readFile`, `listDir`, `fileExists`)
- Git operations (`getBranch`, `getGitRootPath`)
- Stub methods for unused VS Code features

### 4. Tree-sitter Setup (Test Environment)

**Problem:** Continue's `treeSitter.ts` expects WASM and query files at hardcoded paths relative to its location in node_modules.

**Solution:** `tests/setup.ts` creates symlinks:
```
src/tree-sitter/wasms/          →  node_modules/@continuedev/core/util/node_modules/tree-sitter-wasms/out/
src/tree-sitter/code-snippet-queries/  →  node_modules/@continuedev/core/extensions/vscode/tree-sitter/code-snippet-queries/
```

### 5. Bundle Configuration (`bundle-continue.js`)

**Problem:** Continue's ESM code has bundling issues:
- Dynamic `require()` for native modules
- Missing `__dirname` in ESM context
- Workerpool imports need redirection

**Solution:** esbuild with:
- Plugin to redirect `workerpool` imports from Continue to our shim
- ESM polyfill banner (`__dirname`, `__filename`, `require`)
- External declarations for native modules (sqlite3, vectordb, onnxruntime-node)

## What We Expect From Continue

These interfaces/behaviors must remain stable:

| Component | Expected Interface | Test Coverage |
|-----------|-------------------|---------------|
| `FullTextSearchCodebaseIndex` | Constructor with no args, `.retrieve()`, `.update()` | `fts5-indexing.test.ts` |
| `ChunkCodebaseIndex` | Constructor(readFile, serverClient, maxChunkSize) | `fts5-indexing.test.ts` |
| `getComputeDeleteAddRemove` | Returns `[results, pathsAndCacheKeys, markComplete]` | `fts5-indexing.test.ts` |
| `LanceDbIndex.create` | Static factory accepting (embeddingsProvider, readFile) | `vector-index.test.ts` |
| `CodeSnippetsCodebaseIndex` | `.getSnippetsInFile()`, `.getPathsAndSignatures()` | `code-structure.test.ts` |
| Worker file naming | `*Worker*.mjs` or `*Worker*.js` in `llm/` directory | `worker-paths.test.ts` |
| Transformers.js vendor | Path at `vendor/modules/@xenova/transformers/src/` | `transformers-vendor.test.ts` |
| IDE interface | Methods used by indexing (readFile, listDir, getBranch, etc.) | `ide-interface.test.ts` |

## Keeping It Updated

### When Bumping `@continuedev/core` Version

```bash
# 1. Update the package
npm install @continuedev/core@X.Y.Z

# 2. Check for compile-time breaks
npm run build

# 3. Run compatibility tests
npm test

# 4. If tests fail, check:
#    - Worker file locations/naming changed?
#    - Constructor signatures changed?
#    - New required IDE methods?
#    - Vendor paths moved?
```

### CI Integration

```yaml
# .github/workflows/continue-compat.yml
name: Continue Compatibility
on:
  push:
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npm run build
      - run: npm test

  test-latest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npm install @continuedev/core@latest
      - run: npm run build
      - run: npm test
```

### Common Failure Scenarios

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Worker pool fails to spawn | Worker paths changed | Update glob patterns in `continue-worker-paths.ts` |
| Tree-sitter returns empty | Query files moved | Update symlink paths in `tests/setup.ts` |
| Embeddings fail to load | Vendor path changed | Update import in `embeddings-provider.ts` |
| Build fails with type errors | Interface changed | Update `ContinueIDE.ts` to match new interface |
| LanceDB returns null | Platform check changed | Update `isSupportedLanceDbCpuTargetForLinux` import |

## File Inventory

```
src/
├── shims/
│   ├── workerpool-shim.ts       # Intercepts workerpool.pool()
│   └── continue-worker-paths.ts # Resolves worker file locations
├── embeddings/
│   ├── embeddings-provider.ts   # Custom ILLM for transformers.js
│   └── vector-index.ts          # LanceDB wrapper
├── continue/
│   └── ContinueIDE.ts           # IDE interface implementation
├── tools/
│   ├── file-search.ts           # FTS5 search tool
│   ├── semantic-search.ts       # Hybrid vector+FTS search
│   └── code-structure.ts        # Tree-sitter extraction
└── tree-sitter/
    ├── wasms/                   # Tree-sitter WASM binaries
    └── code-snippet-queries/    # Language-specific queries

tests/
├── setup.ts                     # Global setup (symlinks)
└── continue-compat/
    ├── worker-paths.test.ts     # Worker resolution tests
    ├── ide-interface.test.ts    # IDE implementation tests
    ├── fts5-indexing.test.ts    # FTS5/Chunk index tests
    ├── vector-index.test.ts     # LanceDB tests
    ├── transformers-vendor.test.ts # Vendor path tests
    └── code-structure.test.ts   # Tree-sitter tests
```
