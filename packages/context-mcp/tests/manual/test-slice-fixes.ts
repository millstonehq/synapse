#!/usr/bin/env tsx
/**
 * Manual integration test for slice management fixes
 *
 * This script tests the fixes for:
 * 1. op="add" now works with slices
 * 2. Slices are merged when adding to existing file
 * 3. Error messages for invalid operations
 */

import { SelectionManager } from '../../src/selection/SelectionManager.js';
import { manageSelectionTool } from '../../src/tools/manage-selection.js';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as os from 'os';

async function createTestFiles(dir: string) {
  const files = {
    'a.ts': path.join(dir, 'a.ts'),
    'b.ts': path.join(dir, 'b.ts'),
  };

  await fs.writeFile(
    files['a.ts'],
    `// File A
function one() { return 1; }
function two() { return 2; }
function three() { return 3; }
function four() { return 4; }
function five() { return 5; }
function six() { return 6; }
function seven() { return 7; }
function eight() { return 8; }
function nine() { return 9; }
function ten() { return 10; }
`
  );

  await fs.writeFile(
    files['b.ts'],
    `// File B
function alpha() { return 'a'; }
function beta() { return 'b'; }
function gamma() { return 'g'; }
function delta() { return 'd'; }
function epsilon() { return 'e'; }
function zeta() { return 'z'; }
function eta() { return 'h'; }
function theta() { return 't'; }
function iota() { return 'i'; }
function kappa() { return 'k'; }
`
  );

  return files;
}

async function runTests() {
  console.log('🧪 Testing context-helper MCP Server Slice Fixes\n');

  const testDir = await fs.mkdtemp(path.join(os.tmpdir(), 'slice-test-'));
  const testFiles = await createTestFiles(testDir);
  const manager = new SelectionManager(testDir);

  try {
    // Test 1: Add slices incrementally
    console.log('✓ Test 1: Add slices incrementally from different files');

    // Clear selection
    await manageSelectionTool({ op: 'clear' }, manager);

    // Add first slice
    console.log('  Adding slice from a.ts...');
    await manageSelectionTool({
      op: 'add',
      slices: [{
        path: testFiles['a.ts'],
        ranges: [{ startLine: 1, endLine: 10, description: 'functions 1-10' }]
      }]
    }, manager);

    let summary = await manager.getSummary();
    console.log(`  ✓ Selection has ${summary.totalFiles} file(s)`);
    if (summary.totalFiles !== 1) throw new Error('Expected 1 file after first add');

    // Add second slice from different file
    console.log('  Adding slice from b.ts...');
    await manageSelectionTool({
      op: 'add',
      slices: [{
        path: testFiles['b.ts'],
        ranges: [{ startLine: 1, endLine: 10, description: 'greek functions' }]
      }]
    }, manager);

    summary = await manager.getSummary();
    console.log(`  ✓ Selection has ${summary.totalFiles} file(s)`);
    if (summary.totalFiles !== 2) throw new Error('Expected 2 files after second add');

    console.log('  ✅ Test 1 PASSED: Both a.ts and b.ts in selection\n');

    // Test 2: Add ranges to existing file
    console.log('✓ Test 2: Add multiple ranges to same file (auto-merge)');

    await manageSelectionTool({ op: 'clear' }, manager);

    // Add first range
    console.log('  Adding first range to a.ts...');
    await manageSelectionTool({
      op: 'add',
      slices: [{
        path: testFiles['a.ts'],
        ranges: [{ startLine: 1, endLine: 5, description: 'first chunk' }]
      }]
    }, manager);

    let file = manager.get(testFiles['a.ts']);
    console.log(`  ✓ a.ts has ${file?.slices?.length} slice(s)`);
    if (file?.slices?.length !== 1) throw new Error('Expected 1 slice after first add');

    // Add second range to same file
    console.log('  Adding second range to a.ts...');
    await manageSelectionTool({
      op: 'add',
      slices: [{
        path: testFiles['a.ts'],
        ranges: [{ startLine: 6, endLine: 10, description: 'second chunk' }]
      }]
    }, manager);

    file = manager.get(testFiles['a.ts']);
    console.log(`  ✓ a.ts now has ${file?.slices?.length} slice(s)`);
    if (file?.slices?.length !== 2) throw new Error('Expected 2 slices after second add');

    console.log(`  ✓ First slice: lines ${file?.slices?.[0].startLine}-${file?.slices?.[0].endLine} (${file?.slices?.[0].description})`);
    console.log(`  ✓ Second slice: lines ${file?.slices?.[1].startLine}-${file?.slices?.[1].endLine} (${file?.slices?.[1].description})`);

    console.log('  ✅ Test 2 PASSED: Ranges auto-merged for same file\n');

    // Test 3: Error handling
    console.log('✓ Test 3: Error handling for invalid operations');

    // Test invalid operation
    console.log('  Testing invalid operation name...');
    let result = await manageSelectionTool({
      op: 'invalid_op' as any,
      slices: [{
        path: testFiles['a.ts'],
        ranges: [{ startLine: 1, endLine: 5 }]
      }]
    }, manager);

    if (!result.error) throw new Error('Expected error for invalid operation');
    console.log(`  ✓ Got error: "${result.error}"`);

    // Test missing parameters
    console.log('  Testing add with no paths or slices...');
    result = await manageSelectionTool({
      op: 'add'
    }, manager);

    if (!result.error) throw new Error('Expected error for missing parameters');
    console.log(`  ✓ Got error: "${result.error}"`);

    console.log('  ✅ Test 3 PASSED: Clear error messages\n');

    console.log('🎉 All tests PASSED!\n');
    console.log('Summary:');
    console.log('  ✅ op="add" works with slices (incremental addition)');
    console.log('  ✅ Slices auto-merge when adding to existing file');
    console.log('  ✅ Clear error messages for invalid operations');
    console.log('  ✅ Natural incremental workflow now supported');

  } catch (error) {
    console.error('\n❌ Test FAILED:', error);
    throw error;
  } finally {
    manager.dispose();
    await fs.rm(testDir, { recursive: true, force: true });
  }
}

runTests().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
