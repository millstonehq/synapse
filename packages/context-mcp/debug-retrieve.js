#!/usr/bin/env node

import { FullTextSearchCodebaseIndex } from './dist/bundled/file-search-v2.js';

async function debugRetrieve() {
  const workspaceDir = process.cwd();

  const tag = {
    branch: 'main',
    directory: workspaceDir,
    artifactId: 'fts',
  };

  const ftsIndex = new FullTextSearchCodebaseIndex();

  console.log('Calling retrieve with:');
  console.log('- text: buildFTSIndex');
  console.log('- tags:', [tag]);
  console.log('- n: 10');
  console.log('- bm25Threshold: -10.0\n');

  const chunks = await ftsIndex.retrieve({
    n: 10,
    text: 'buildFTSIndex',
    tags: [tag],
    bm25Threshold: -10.0,
  });

  console.log(`Retrieved ${chunks.length} chunks:`);
  console.log(JSON.stringify(chunks, null, 2));
}

debugRetrieve().catch(console.error);
