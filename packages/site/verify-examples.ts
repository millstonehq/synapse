import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve, join } from 'node:path';
import yaml from 'js-yaml';

const site = resolve(import.meta.dirname);
const content = JSON.parse(readFileSync(join(site, 'quartz/public/static/contentIndex.json'), 'utf8'));
const paths = new Set<string>();
for (const entry of Object.values(content) as { filePath: string }[]) {
  if (entry.filePath === 'index.md') continue;
  assert(entry.filePath.split('/').slice(0, -1).includes('examples'), `Non-example page: ${entry.filePath}`);
  const text = readFileSync(join(site, 'quartz/content', entry.filePath), 'utf8');
  const match = /^---\r?\n([\s\S]*?)\r?\n---/.exec(text);
  const metadata = yaml.load(match![1]) as Record<string, unknown>;
  assert(metadata.example === true && metadata.draft !== true, `Unapproved page: ${entry.filePath}`);
  paths.add(entry.filePath);
}
assert(paths.size > 0, 'No example pages were built');
const vault = JSON.parse(readFileSync(join(site, 'quartz/public/static/edit/vault-index.json'), 'utf8'));
assert.deepEqual(new Set(vault.paths), paths, 'CMS and rendered examples must match');
console.log(`Verified ${paths.size} public examples and matching CMS index`);
