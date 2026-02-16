# Build Guide

## Quick Start

```bash
npm run build
```

That's it! Despite the TypeScript warnings you'll see, **the build succeeds**.

## Understanding Build Output

When you run `npm run build`, you'll see TypeScript errors like:

```
node_modules/@continuedev/core/llm/llms/Anthropic.ts(190,11): error TS18046: 'json' is of type 'unknown'.
node_modules/@continuedev/core/llm/llms/Ollama.ts(165,13): error TS18046: 'body' is of type 'unknown'.
...
```

### ✅ These errors are EXPECTED and SAFE to ignore

**Why?**

1. **These are from Continue's node_modules**, not our code
2. **Our tsconfig has `noEmitOnError: false`**, so TypeScript still compiles successfully
3. **Our tsconfig has `skipLibCheck: true`**, but some errors still show
4. **The bundled code works perfectly** - esbuild handles Continue's code

### How to Verify Build Succeeded

Check for these signs:

1. **Exit code is 0** (or build doesn't stop)
2. **Files are created**:
   ```bash
   ls -lh dist/*.js dist/bundled/*.js
   ```

   You should see:
   ```
   dist/index.js
   dist/server.js
   dist/server-v2.js
   dist/bundled/file-search-v2.js
   dist/bundled/code-structure-v2.js
   ```

3. **Test the built server**:
   ```bash
   node test-server-v2-integration.js
   ```

   Should output:
   ```
   ✅ V2: Loaded bundled Continue modules (FTS5 + tree-sitter)
   🎉 Server V2 integration test passed!
   ```

## Build Process Explained

The build has two steps:

### Step 1: TypeScript Compilation

```bash
tsc
```

- Compiles `src/` → `dist/`
- Shows errors from Continue's node_modules (which we ignore)
- Still generates output due to `noEmitOnError: false`

### Step 2: Bundling Continue Modules

```bash
node bundle-continue.js
```

- Uses esbuild to bundle Continue's FTS5 and tree-sitter
- Creates `dist/bundled/file-search-v2.js`
- Creates `dist/bundled/code-structure-v2.js`
- Resolves all ESM issues (missing `.js` extensions, `__dirname`, etc.)

## Build Commands

| Command | Description |
|---------|-------------|
| `npm run build` | Full build (compile + bundle) |
| `npm run build:verbose` | Just TypeScript compilation (shows all output) |
| `npm run build:bundle` | Just bundling (assumes TS already compiled) |
| `npm run build:clean` | Clean dist/ and rebuild from scratch |
| `npm run dev` | Watch mode for development |

## Troubleshooting

### Build appears to fail but files are created

✅ **This is normal!** TypeScript errors from Continue's node_modules make it look like the build failed, but check if `dist/` files were created. If yes, the build succeeded.

### dist/bundled/ files are missing

Run the full build:
```bash
npm run build:clean
```

### Server fails to load bundled modules

Check console output when running the server:
```bash
VERSION=2 node dist/index.js
```

Should show:
```
✅ V2: Loaded bundled Continue modules (FTS5 + tree-sitter)
```

If it shows:
```
⚠️ V2: Failed to load bundled modules
```

Then run:
```bash
npm run build:bundle
```

### "Cannot find module" errors at runtime

Make sure you ran the full build:
```bash
npm run build
```

## Why Not Suppress the TypeScript Errors?

We could suppress them with `|| true` or `2>/dev/null`, but:

1. **We want to see real errors in OUR code**
2. **TypeScript's `skipLibCheck` should handle this** (and mostly does)
3. **The errors are harmless** - they don't prevent compilation
4. **Seeing them is educational** - shows Continue's package has type issues

## What the Errors Mean

Continue's package (`@continuedev/core`) has TypeScript errors because:

1. **Designed for bundled environments** - Continue is a VS Code extension
2. **Uses TypeScript "Bundler" moduleResolution** - assumes webpack will fix imports
3. **Type safety issues in their code** - `'unknown'` type errors
4. **Missing type declarations** - jsdom, json-schema

**None of this affects our bundled code** - esbuild handles it all!

## Production Build Verification

After building, verify everything works:

```bash
# 1. Build
npm run build

# 2. Test bundled modules
node test-v2-bundled.js

# 3. Test server integration
node test-server-v2-integration.js

# 4. Run server
VERSION=2 WORKSPACE_DIR=$(pwd) node dist/index.js
```

All tests should pass and server should start with:
```
✅ V2: Loaded bundled Continue modules (FTS5 + tree-sitter)
Context MCP Server V2 running on stdio
```

## Summary

✅ **TypeScript errors from Continue's node_modules are expected**
✅ **Build succeeds despite the errors**
✅ **Bundled code works perfectly**
✅ **Server runs with full V2 features**

**Don't worry about the red text - focus on the test results!**

---

**Last Updated:** 2025-10-25
**Version:** 0.3.0
