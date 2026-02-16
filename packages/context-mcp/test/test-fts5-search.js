#!/usr/bin/env node

/**
 * Test FTS5 search functionality
 */

import { fileSearchToolV2 } from './dist/bundled/file-search-v2.js';
import { ContinueIDE } from './dist/continue/ContinueIDE.js';

async function testFTS5Search() {
  const workspaceDir = process.cwd();
  const ide = new ContinueIDE(workspaceDir);

  console.log('🔍 Testing FTS5 search functionality\n');

  // Test 1: Search for "buildFTSIndex" (should be in file-search-v2.ts)
  console.log('Test 1: Searching for "buildFTSIndex"...');
  const result1 = await fileSearchToolV2(
    {
      pattern: 'buildFTSIndex',
      mode: 'content',
      max_results: 10,
    },
    workspaceDir,
    ide
  );
  console.log(`✅ Found ${result1.count} results`);
  console.log(`   Method: ${result1.performance?.method}`);
  console.log(`   Search time: ${result1.performance?.searchTime}ms`);
  if (result1.results.length > 0) {
    console.log(`   First match: ${result1.results[0].path.replace(workspaceDir + '/', '')}`);
  }

  // Test 2: Search for "ContinueIDE" (should be in multiple files)
  console.log('\nTest 2: Searching for "ContinueIDE"...');
  const result2 = await fileSearchToolV2(
    {
      pattern: 'ContinueIDE',
      mode: 'content',
      max_results: 10,
    },
    workspaceDir,
    ide
  );
  console.log(`✅ Found ${result2.count} results`);
  console.log(`   Method: ${result2.performance?.method}`);
  console.log(`   Search time: ${result2.performance?.searchTime}ms`);

  // Test 3: Search for "FileWalker"
  console.log('\nTest 3: Searching for "FileWalker"...');
  const result3 = await fileSearchToolV2(
    {
      pattern: 'FileWalker',
      mode: 'content',
      max_results: 10,
    },
    workspaceDir,
    ide
  );
  console.log(`✅ Found ${result3.count} results`);
  console.log(`   Method: ${result3.performance?.method}`);
  console.log(`   Search time: ${result3.performance?.searchTime}ms`);

  // Summary
  console.log('\n📊 Summary:');
  console.log(`   All searches used: ${result1.performance?.method}`);
  console.log(`   Average search time: ${((result1.performance?.searchTime + result2.performance?.searchTime + result3.performance?.searchTime) / 3).toFixed(1)}ms`);
}

testFTS5Search().catch(console.error);
