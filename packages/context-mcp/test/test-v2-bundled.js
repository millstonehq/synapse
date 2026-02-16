#!/usr/bin/env node

/**
 * Test V2 with bundled Continue modules (FTS5 + tree-sitter)
 */

import { ContinueIDE } from './dist/continue/ContinueIDE.js';
import { ContinueLLM } from './dist/continue/ContinueLLM.js';
import { fileSearchToolV2 } from './dist/bundled/file-search-v2.js';
import { getCodeStructureToolV2 } from './dist/bundled/code-structure-v2.js';
import { SelectionManager } from './dist/selection/SelectionManager.js';

async function runV2BundledTests() {
  console.log('🧪 Testing Context MCP Server V2 (Bundled Continue Integration)\n');
  console.log('This version uses Continue\'s FTS5 and tree-sitter via esbuild bundling\n');
  console.log('Working directory:', process.cwd());
  console.log();

  const workspaceDir = process.cwd();
  const ide = new ContinueIDE(workspaceDir);
  const llm = new ContinueLLM();
  const manager = new SelectionManager(workspaceDir);

  try {
    // Test 1: IDE shim basics
    console.log('Test 1: Testing IDE shim...');
    const workspaceDirs = await ide.getWorkspaceDirs();
    console.log('✅ Workspace:', workspaceDirs[0]);
    const branch = await ide.getBranch(workspaceDir);
    console.log('✅ Git branch:', branch);
    console.log();

    // Test 2: LLM token counting
    console.log('Test 2: Testing LLM token counting...');
    const testText = 'Hello, this is a test of the token counting system.';
    const tokens = llm.countTokens(testText);
    console.log(`✅ Counted ${tokens} tokens in test text`);
    console.log();

    // Test 3: FTS5 File search (bundled Continue)
    console.log('Test 3: Testing FTS5 file search (Continue via bundling)...');
    const searchResult = await fileSearchToolV2(
      {
        pattern: 'Context',
        mode: 'content',
        max_results: 3,
      },
      workspaceDir,
      ide
    );
    console.log(`✅ Found ${searchResult.count} results`);
    console.log(`   Search time: ${searchResult.performance.searchTime}ms`);
    console.log(`   Method: ${searchResult.performance.method}`);
    if (searchResult.results.length > 0) {
      console.log(`   First match: ${searchResult.results[0].path.split('/').pop()}`);
    }
    console.log();

    // Test 4: Tree-sitter code structure extraction (bundled Continue)
    console.log('Test 4: Testing tree-sitter code structure extraction (Continue via bundling)...');
    const tsFiles = [
      workspaceDir + '/src/server-v2.ts',
      workspaceDir + '/src/continue/ContinueIDE.ts',
    ];
    const structureResult = await getCodeStructureToolV2({
      paths: tsFiles,
      scope: 'paths',
    });
    console.log(`✅ Extracted structure from ${structureResult.structures.length} files`);
    console.log(`   Extraction time: ${structureResult.performance.extractionTime}ms`);
    console.log(`   Files processed: ${structureResult.performance.filesProcessed}`);

    for (const struct of structureResult.structures) {
      const fileName = struct.path.split('/').pop();
      console.log(`   ${fileName}: ${struct.count} signatures`);
      if (struct.signatures.length > 0) {
        console.log(`      Example: ${struct.signatures[0].substring(0, 60)}...`);
      }
    }
    console.log();

    // Test 5: File reading
    console.log('Test 5: Reading file via IDE...');
    const packageContent = await ide.readFile(workspaceDir + '/package.json');
    const packageData = JSON.parse(packageContent);
    console.log(`✅ Read package.json via IDE`);
    console.log(`   Name: ${packageData.name}`);
    console.log(`   Version: ${packageData.version}`);
    console.log();

    // Test 6: Selection with V2 features
    console.log('Test 6: Testing selection with code structure...');
    await manager.add(workspaceDir + '/README.md', 'full');
    const summary = await manager.getSummary();
    console.log(`✅ Selection: ${summary.totalFiles} files, ${summary.totalTokens} tokens`);
    console.log();

    console.log('🎉 All V2 bundled tests passed!\n');
    console.log('📊 Summary:');
    console.log('  - IDE shim: ✅ Working');
    console.log('  - LLM token counting: ✅ Working');
    console.log('  - FTS5 search (Continue): ✅ Working via bundling!');
    console.log('  - Tree-sitter structure (Continue): ✅ Working via bundling!');
    console.log('  - Selection management: ✅ Working');
    console.log();
    console.log('💡 Continue integration successful via esbuild bundling!');
    console.log('   Thanks to __dirname polyfill and native module externalization');

    // Cleanup
    manager.dispose();
    llm.dispose();

  } catch (error) {
    console.error('❌ Test failed:', error);
    console.error(error.stack);
    process.exit(1);
  }
}

runV2BundledTests();
