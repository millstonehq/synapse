#!/usr/bin/env node

/**
 * Test bundled Continue modules
 */

import { fileSearchToolV2 } from './dist/bundled/file-search-v2.js';
import { ContinueIDE } from './dist/continue/ContinueIDE.js';

async function testBundled() {
  console.log('🧪 Testing bundled Continue modules\n');

  const workspaceDir = process.cwd();
  const ide = new ContinueIDE(workspaceDir);

  try {
    console.log('Test: FTS5 search via bundled module...');
    const result = await fileSearchToolV2(
      {
        pattern: 'Context',
        mode: 'content',
        max_results: 3,
      },
      workspaceDir,
      ide
    );

    console.log(`✅ Search completed!`);
    console.log(`   Found: ${result.count} results`);
    console.log(`   Method: ${result.performance.method}`);
    console.log(`   Time: ${result.performance.searchTime}ms`);

    if (result.results.length > 0) {
      console.log(`   First match: ${result.results[0].path.split('/').pop()}`);
    }

    console.log('\n🎉 Bundled Continue modules work!');

  } catch (error) {
    console.error('❌ Test failed:', error);
    console.error(error.stack);
    process.exit(1);
  }
}

testBundled();
