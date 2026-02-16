/**
 * Transformers.js Vendor Path Tests
 *
 * Tests that validate the transformers.js vendor module path in @continuedev/core.
 *
 * NOTE: The vendored transformers.js uses __dirname which requires ESM polyfills
 * that are only available when running bundled code. These tests verify the
 * module files exist and have the correct structure, but cannot import them
 * directly in a vitest environment without bundling.
 *
 * These tests will catch breaking changes if:
 * - The vendored transformers.js path changes
 * - Key source files are removed
 */

import { describe, it, expect } from 'vitest';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);

describe('transformers.js vendor module', () => {
  const corePackagePath = require.resolve('@continuedev/core/package.json');
  const coreRoot = path.dirname(corePackagePath);
  const vendorPath = path.join(
    coreRoot,
    'vendor/modules/@xenova/transformers/src'
  );

  it('vendor path exists', () => {
    expect(fs.existsSync(vendorPath)).toBe(true);
  });

  it('transformers.js entry point exists', () => {
    const transformersPath = path.join(vendorPath, 'transformers.js');
    expect(fs.existsSync(transformersPath)).toBe(true);
  });

  it('env.js module exists', () => {
    const envPath = path.join(vendorPath, 'env.js');
    expect(fs.existsSync(envPath)).toBe(true);
  });

  it('transformers.js exports env and pipeline', () => {
    // Read the file and check for expected exports
    const transformersPath = path.join(vendorPath, 'transformers.js');
    const content = fs.readFileSync(transformersPath, 'utf-8');

    // Should re-export env from env.js
    expect(content).toMatch(/env/);
    // Should export pipeline function
    expect(content).toMatch(/pipeline/);
  });

  it('env.js contains configuration properties', () => {
    const envPath = path.join(vendorPath, 'env.js');
    const content = fs.readFileSync(envPath, 'utf-8');

    // These properties are used by embeddings-provider.ts
    expect(content).toMatch(/allowRemoteModels/);
    expect(content).toMatch(/allowLocalModels/);
    expect(content).toMatch(/cacheDir/);
  });
});

describe('transformers.js package structure', () => {
  const corePackagePath = require.resolve('@continuedev/core/package.json');
  const coreRoot = path.dirname(corePackagePath);
  const vendorRoot = path.join(coreRoot, 'vendor/modules/@xenova/transformers');

  it('has package.json', () => {
    const pkgPath = path.join(vendorRoot, 'package.json');
    expect(fs.existsSync(pkgPath)).toBe(true);

    const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf-8'));
    expect(pkg.name).toBe('@xenova/transformers');
  });

  it('is ESM module', () => {
    const pkgPath = path.join(vendorRoot, 'package.json');
    const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf-8'));
    expect(pkg.type).toBe('module');
  });
});
