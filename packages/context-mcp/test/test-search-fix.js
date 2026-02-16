#!/usr/bin/env node
import { fileSearchToolV2 } from './dist/tools/file-search-v2.js';
import { ContinueIDE } from './dist/continue/ContinueIDE.js';

const workspaceDir = '/path/to/synapse';
const ide = new ContinueIDE(workspaceDir);

console.log('Testing file_search with pattern "standard"...\n');

const results = await fileSearchToolV2(
  {
    pattern: 'standard',
    mode: 'content',
    max_results: 10
  },
  workspaceDir,
  ide
);

console.log(`Found ${results.count} results in ${results.performance.searchTime}ms`);
console.log(`Search method: ${results.performance.method}\n`);

console.log('First 5 results:');
results.results.slice(0, 5).forEach((result, i) => {
  console.log(`\n${i + 1}. ${result.path}`);
  console.log(`   Line ${result.line_number}: ${result.line_content}`);

  // Verify the line contains "standard" (case-insensitive)
  const hasMatch = result.line_content?.toLowerCase().includes('standard');
  console.log(`   ✓ Contains "standard": ${hasMatch ? 'YES' : 'NO ❌'}`);
});
