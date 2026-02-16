#!/usr/bin/env node

/**
 * Simple direct test of the MCP server tools
 */

import { fileSearchTool } from './dist/tools/file-search.js';
import { getFileTreeTool } from './dist/tools/file-tree.js';
import { readFileTool } from './dist/tools/read-file.js';
import { manageSelectionTool } from './dist/tools/manage-selection.js';
import { workspaceContextTool } from './dist/tools/workspace-context.js';
import { SelectionManager } from './dist/selection/SelectionManager.js';

async function runTests() {
  console.log('🧪 Testing Context MCP Server Tools\n');
  console.log('Working directory:', process.cwd());
  console.log();

  const workspaceDir = process.cwd();
  const manager = new SelectionManager(workspaceDir);

  try {
    // Test 1: File tree
    console.log('Test 1: Get file tree roots...');
    const treeResult = await getFileTreeTool(
      { type: 'roots' },
      workspaceDir
    );
    console.log('✅ Roots:', treeResult.roots);
    console.log();

    // Test 2: File search (path)
    console.log('Test 2: Search for .ts files...');
    const searchResult = await fileSearchTool(
      {
        pattern: '.ts',
        mode: 'path',
        max_results: 5,
      },
      workspaceDir
    );
    console.log(`✅ Found ${searchResult.count} files`);
    if (searchResult.results.length > 0) {
      console.log('   First result:', searchResult.results[0].path);
    }
    console.log();

    // Test 3: Read file
    console.log('Test 3: Read package.json...');
    const readResult = await readFileTool({
      path: workspaceDir + '/package.json',
    });
    console.log(`✅ Read ${readResult.size} bytes`);
    const packageData = JSON.parse(readResult.content);
    console.log(`   Name: ${packageData.name}`);
    console.log(`   Version: ${packageData.version}`);
    console.log();

    // Test 4: Add to selection
    console.log('Test 4: Add files to selection...');
    await manageSelectionTool(
      {
        op: 'add',
        paths: [
          workspaceDir + '/package.json',
          workspaceDir + '/README.md',
        ],
        mode: 'full',
      },
      manager
    );
    console.log('✅ Added 2 files to selection');
    console.log();

    // Test 5: Get selection
    console.log('Test 5: Get selection summary...');
    const selectionResult = await manageSelectionTool(
      {
        op: 'get',
        view: 'summary',
      },
      manager
    );
    console.log(`✅ Selection: ${selectionResult.totalFiles} files, ${selectionResult.totalTokens} tokens`);
    selectionResult.files.forEach(file => {
      console.log(`   - ${file.path.split('/').pop()} (${file.mode})`);
    });
    console.log();

    // Test 6: Preview
    console.log('Test 6: Preview selection...');
    const previewResult = await manageSelectionTool(
      {
        op: 'preview',
      },
      manager
    );
    console.log(`✅ Preview: ${previewResult.totalTokens} tokens`);
    console.log(`   Content length: ${previewResult.content.length} characters`);
    console.log();

    // Test 7: Workspace context
    console.log('Test 7: Get workspace context...');
    const contextResult = await workspaceContextTool(
      {
        include: ['selection', 'tokens'],
      },
      manager,
      workspaceDir
    );
    console.log(`✅ Context: ${contextResult.selection.totalFiles} files, ${contextResult.tokens} tokens`);
    console.log();

    // Test 8: Clear selection
    console.log('Test 8: Clear selection...');
    await manageSelectionTool(
      {
        op: 'clear',
      },
      manager
    );
    const emptyResult = await manageSelectionTool(
      {
        op: 'get',
      },
      manager
    );
    console.log(`✅ Cleared. Now has ${emptyResult.totalFiles} files`);
    console.log();

    // Test 9: Content search
    console.log('Test 9: Search file contents...');
    const contentSearchResult = await fileSearchTool(
      {
        pattern: 'MCP',
        mode: 'content',
        max_results: 3,
      },
      workspaceDir
    );
    console.log(`✅ Found ${contentSearchResult.count} matches`);
    if (contentSearchResult.results.length > 0) {
      console.log(`   First match: ${contentSearchResult.results[0].path.split('/').pop()}`);
      if (contentSearchResult.results[0].line_content) {
        console.log(`   Line: ${contentSearchResult.results[0].line_content.substring(0, 60)}...`);
      }
    }
    console.log();

    console.log('🎉 All tests passed!\n');

    // Cleanup
    manager.dispose();

  } catch (error) {
    console.error('❌ Test failed:', error);
    console.error(error.stack);
    process.exit(1);
  }
}

runTests();
