#!/usr/bin/env node

/**
 * Test Hybrid V2 (Continue architecture + V1 implementations)
 */

import { ContinueIDE } from './dist/continue/ContinueIDE.js';
import { ContinueLLM } from './dist/continue/ContinueLLM.js';
import { fileSearchTool } from './dist/tools/file-search.js';
import { getCodeStructureTool } from './dist/tools/code-structure.js';
import { SelectionManager } from './dist/selection/SelectionManager.js';

async function runHybridV2Tests() {
  console.log('🧪 Testing Context MCP Server V2 (Hybrid)\n');
  console.log('Architecture: Continue-compatible shims');
  console.log('Implementation: V1 tools (until Continue exports are fixed)');
  console.log('Working directory:', process.cwd());
  console.log();

  const workspaceDir = process.cwd();
  const ide = new ContinueIDE(workspaceDir);
  const llm = new ContinueLLM();
  const manager = new SelectionManager(workspaceDir);

  try {
    // Test 1: IDE shim (Continue-compatible)
    console.log('Test 1: Continue IDE shim...');
    const workspaceDirs = await ide.getWorkspaceDirs();
    console.log('✅ Workspace:', workspaceDirs[0]);

    const branch = await ide.getBranch(workspaceDir);
    console.log('✅ Git branch:', branch);

    const ideInfo = await ide.getIdeInfo();
    console.log(`✅ IDE type: ${ideInfo.ideType} (Continue-compatible)`);
    console.log();

    // Test 2: LLM shim (Continue-compatible)
    console.log('Test 2: Continue LLM shim...');
    const testText = 'This is a test of the token counting system using tiktoken.';
    const tokens = llm.countTokens(testText);
    console.log(`✅ Counted ${tokens} tokens`);
    console.log(`✅ Provider: ${llm.providerName}`);
    console.log(`✅ Model: ${llm.model}`);
    console.log();

    // Test 3: File operations via IDE
    console.log('Test 3: File operations via Continue IDE...');
    const packageContent = await ide.readFile(workspaceDir + '/package.json');
    const packageData = JSON.parse(packageContent);
    console.log(`✅ Read package.json via IDE shim`);
    console.log(`   Name: ${packageData.name}`);
    console.log(`   Version: ${packageData.version}`);
    console.log();

    // Test 4: File search (V1 implementation)
    console.log('Test 4: File search (V1 implementation)...');
    const searchResult = await fileSearchTool(
      {
        pattern: 'Context',
        mode: 'content',
        max_results: 3,
      },
      workspaceDir
    );
    console.log(`✅ Found ${searchResult.count} results`);
    if (searchResult.results.length > 0) {
      console.log(`   First match: ${searchResult.results[0].path.split('/').pop()}`);
    }
    console.log();

    // Test 5: Code structure (V1 placeholder)
    console.log('Test 5: Code structure (V1 placeholder)...');
    const structureResult = await getCodeStructureTool({
      paths: [workspaceDir + '/src/server-v2.ts'],
      scope: 'paths',
    });
    console.log(`✅ Structure for ${structureResult.structures.length} files`);
    console.log(`   Note: ${structureResult.structures[0].note}`);
    console.log();

    // Test 6: Selection management
    console.log('Test 6: Selection management...');
    await manager.add(workspaceDir + '/README.md', 'full');
    await manager.add(workspaceDir + '/package.json', 'full');
    const summary = await manager.getSummary();
    console.log(`✅ Selection: ${summary.totalFiles} files, ${summary.totalTokens} tokens`);
    summary.files.forEach(file => {
      console.log(`   - ${file.path.split('/').pop()} (${file.mode})`);
    });
    console.log();

    console.log('🎉 All Hybrid V2 tests passed!\n');
    console.log('📊 Summary:');
    console.log('  ✅ Continue IDE shim: Fully functional');
    console.log('  ✅ Continue LLM shim: Fully functional');
    console.log('  ✅ File operations: Working via IDE');
    console.log('  ✅ Search: V1 implementation (ready for FTS5 upgrade)');
    console.log('  ✅ Code structure: V1 placeholder (ready for tree-sitter upgrade)');
    console.log('  ✅ Selection: Working with token counting');
    console.log();
    console.log('🔄 V2 Status: Architecture complete, waiting on Continue exports');
    console.log('   See V2_STATUS.md for upgrade path');
    console.log();

    // Cleanup
    manager.dispose();
    llm.dispose();

  } catch (error) {
    console.error('❌ Test failed:', error);
    console.error(error.stack);
    process.exit(1);
  }
}

runHybridV2Tests();
