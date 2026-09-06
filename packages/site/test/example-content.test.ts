import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, symlinkSync, readdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { stageExamples } from '../example-content.js';

test('public staging excludes non-examples, drafts, raw assets, symlinks and stale output', () => {
  const root = mkdtempSync(join(tmpdir(), 'synapse-examples-'));
  const source = join(root, 'vault'), destination = join(root, 'staged');
  const put = (path: string, text: string) => { mkdirSync(dirname(path), { recursive: true }); writeFileSync(path, text); };
  try {
    put(join(source, 'type/examples/approved.md'), '---\nexample: true\n---\nExample');
    put(join(source, 'type/examples/unmarked.md'), 'Private');
    put(join(source, 'type/examples/string.md'), '---\nexample: "true"\n---\nPrivate');
    put(join(source, 'type/examples/draft.md'), '---\nexample: true\ndraft: true\n---\nDraft');
    put(join(source, 'type/private.md'), '---\nexample: true\n---\nPrivate');
    put(join(source, 'type/examples/secret.json'), '{"secret":true}');
    put(join(destination, 'stale.md'), 'Stale');
    symlinkSync(join(source, 'type/private.md'), join(source, 'type/examples/link.md'));
    assert.deepEqual(stageExamples(source, destination), ['type/examples/approved.md']);
    assert.deepEqual(readdirSync(destination).sort(), ['index.md', 'type']);
    assert.deepEqual(readdirSync(join(destination, 'type/examples')), ['approved.md']);
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test('empty example set fails closed', () => {
  const root = mkdtempSync(join(tmpdir(), 'synapse-empty-'));
  try { assert.throws(() => stageExamples(root, join(root, 'output')), /at least one/); }
  finally { rmSync(root, { recursive: true, force: true }); }
});
