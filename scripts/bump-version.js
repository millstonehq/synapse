#!/usr/bin/env node

/**
 * Bump version across all packages in the monorepo.
 * Usage: node scripts/bump-version.js <version>
 * Example: node scripts/bump-version.js 0.2.0
 */

import { readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, '..');

const PACKAGE_PATHS = [
  'package.json',
  'packages/schemas/package.json',
  'packages/cli/package.json',
  'packages/context-mcp/package.json',
  'packages/site/package.json',
];

// Validate semver: X.Y.Z or X.Y.Z-prerelease (e.g. 0.2.0-beta.1)
const SEMVER_RE = /^\d+\.\d+\.\d+(-[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*)?$/;

function main() {
  const version = process.argv[2];

  if (!version) {
    console.error('Usage: node scripts/bump-version.js <version>');
    console.error('Example: node scripts/bump-version.js 0.2.0');
    process.exit(1);
  }

  if (!SEMVER_RE.test(version)) {
    console.error(`Invalid semver version: "${version}"`);
    console.error('Expected format: X.Y.Z or X.Y.Z-prerelease (e.g. 1.2.3, 0.2.0-beta.1)');
    process.exit(1);
  }

  console.log(`Bumping all packages to ${version}\n`);

  for (const rel of PACKAGE_PATHS) {
    const abs = resolve(root, rel);
    const pkg = JSON.parse(readFileSync(abs, 'utf-8'));
    const oldVersion = pkg.version;
    pkg.version = version;
    writeFileSync(abs, JSON.stringify(pkg, null, 2) + '\n');
    console.log(`  ${rel}: ${oldVersion} -> ${version}`);
  }

  console.log(`\nAll packages updated to ${version}`);
  console.log('\nNext steps:');
  console.log(`  git add -A && git commit -m "chore: bump version to ${version}"`);
  console.log(`  git tag v${version}`);
  console.log(`  git push origin main --tags`);
}

main();
