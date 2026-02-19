import { defineConfig } from 'vitest/config';
import path from 'node:path';

// Set NODE_ENV=test for Continue's tree-sitter path resolution
process.env.NODE_ENV = 'test';

export default defineConfig({
  resolve: {
    alias: {
      // Redirect workerpool imports to our shim for worker path resolution
      // This makes Continue's workerpool.pool() calls use resolved paths
      workerpool: path.resolve(__dirname, 'src/shims/workerpool-shim.ts'),
    },
  },
  test: {
    globals: true,
    environment: 'node',
    include: ['tests/**/*.test.ts'],
    testTimeout: 60000, // Some tests need time for indexing
    hookTimeout: 60000,
    globalSetup: './tests/setup.ts',
    server: {
      deps: {
        // @continuedev/core is ESM but uses extensionless relative imports
        // (e.g. "../util/parameters") which Node cannot resolve natively.
        // Inlining lets Vite's resolver handle the missing .js extensions.
        inline: ['@continuedev/core'],
      },
    },
  },
});
