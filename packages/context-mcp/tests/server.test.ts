import { afterEach, beforeEach, expect, it } from 'vitest';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { InMemoryTransport } from '@modelcontextprotocol/sdk/inMemory.js';
import { mkdtemp, writeFile, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { ContextMCPServer } from '../src/server.js';

let server: ContextMCPServer;
let client: Client;
let dir: string;
beforeEach(async () => {
  dir = await mkdtemp(path.join(os.tmpdir(), 'context-server-'));
  await writeFile(path.join(dir, 'note.md'), 'A selected document.');
  server = new ContextMCPServer([dir]);
  client = new Client({ name: 'test', version: '1' });
  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
  await server.connect(serverTransport);
  await client.connect(clientTransport);
});
afterEach(async () => {
  await client.close();
  server.dispose();
  await rm(dir, { recursive: true, force: true });
});

it('serves file selection and context without an indexing runtime', async () => {
  const { tools } = await client.listTools();
  expect(tools.map(tool => tool.name).sort()).toEqual(['get_file_tree', 'manage_selection', 'read_file', 'workspace_context']);
  const selected = await client.callTool({ name: 'manage_selection', arguments: { op: 'add', paths: ['note.md'] } });
  expect(selected.isError).not.toBe(true);
  const context = await client.callTool({ name: 'workspace_context', arguments: { include: ['files', 'tokens'] } });
  expect(context.isError).not.toBe(true);
  expect(JSON.stringify(context.content)).toContain('A selected document.');
  const read = await client.callTool({ name: 'read_file', arguments: { path: path.join(dir, 'note.md') } });
  expect(JSON.stringify(read.content)).toContain('A selected document.');
});

it('explicitly rejects removed tools and placeholder code modes', async () => {
  for (const name of ['file_search', 'semantic_search', 'get_code_structure', 'index_code']) {
    expect((await client.callTool({ name, arguments: {} })).isError).toBe(true);
  }
  expect((await client.callTool({ name: 'manage_selection', arguments: { op: 'add', paths: ['note.md'], mode: 'codemap_only' } })).isError).toBe(true);
});
