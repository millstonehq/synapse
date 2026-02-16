#!/usr/bin/env node

/**
 * Simple direct test of new file_search format
 */

import { fileSearchToolV2 } from './dist/bundled/file-search-v2.js';
import { ContinueIDE } from './dist/continue/ContinueIDE.js';

const workspaceDir = process.cwd();
const ide = new ContinueIDE(workspaceDir);

async function test() {
  console.log('🧪 Testing new file_search response format\n');

  // Test 1: Default (include_content: false)
  console.log('Test 1: Default behavior (include_content not specified)');
  try {
    const result1 = await fileSearchToolV2(
      {
        pattern: 'FileSearchResult',
        mode: 'content',
        max_results: 2
      },
      workspaceDir,
      ide
    );

    console.log('Result count:', result1.count);
    if (result1.results && result1.results.length > 0) {
      const first = result1.results[0];
      console.log('\nFirst result:');
      console.log('  path:', first.path);
      console.log('  line_range:', first.line_range);
      console.log('  content present:', !!first.content);

      if (Array.isArray(first.line_range) && first.line_range.length === 2) {
        console.log('✅ line_range is array [start, end]');
      } else {
        console.log('❌ line_range format incorrect');
      }

      if (!first.content) {
        console.log('✅ content not included by default');
      } else {
        console.log('❌ content included when it should not be');
      }
    }
  } catch (error) {
    console.log('❌ Test 1 failed:', error.message);
  }

  console.log('\n' + '='.repeat(60) + '\n');

  // Test 2: With include_content: true
  console.log('Test 2: With include_content: true');
  try {
    const result2 = await fileSearchToolV2(
      {
        pattern: 'FileSearchResult',
        mode: 'content',
        max_results: 2,
        include_content: true
      },
      workspaceDir,
      ide
    );

    console.log('Result count:', result2.count);
    if (result2.results && result2.results.length > 0) {
      const first = result2.results[0];
      console.log('\nFirst result:');
      console.log('  path:', first.path);
      console.log('  line_range:', first.line_range);
      console.log('  content present:', !!first.content);

      if (first.content) {
        console.log('✅ content field present');
        console.log('  Content preview (first 80 chars):');
        console.log('  ', first.content.substring(0, 80) + '...');
      } else {
        console.log('❌ content missing when include_content: true');
      }
    }
  } catch (error) {
    console.log('❌ Test 2 failed:', error.message);
  }

  console.log('\n✅ Tests complete!\n');
  process.exit(0);
}

test().catch(error => {
  console.error('Test error:', error);
  process.exit(1);
});
