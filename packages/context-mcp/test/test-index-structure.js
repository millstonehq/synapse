#!/usr/bin/env node

/**
 * Test indexing and code structure extraction
 */

import { indexCodeTool, getCodeStructureTool } from './dist/bundled/code-structure.js';

async function test() {
  console.log('🧪 Testing code indexing and structure extraction\n');

  const workspaceDir = process.cwd();
  const filesToIndex = [
    workspaceDir + '/src/server.ts',
    workspaceDir + '/src/tools/code-structure.ts',
    workspaceDir + '/src/tools/file-search.ts',
  ];

  try {
    // Step 1: Index files
    console.log('Step 1: Indexing files...');
    const indexResult = await indexCodeTool({ paths: filesToIndex });
    console.log('✅ Indexing completed!');
    console.log(`   Files indexed: ${indexResult.indexed}`);
    console.log(`   Files failed: ${indexResult.failed}`);
    console.log(`   Total snippets: ${indexResult.totalSnippets}`);
    console.log(`   Indexing time: ${indexResult.performance.indexingTime}ms\n`);

    // Step 2: Extract code structure
    console.log('Step 2: Extracting code structure...');
    const structureResult = await getCodeStructureTool({
      paths: filesToIndex,
      scope: 'paths'
    });

    console.log('✅ Extraction completed!');
    console.log(`   Files processed: ${structureResult.performance.filesProcessed}`);
    console.log(`   Extraction time: ${structureResult.performance.extractionTime}ms\n`);

    // Display results
    for (const struct of structureResult.structures) {
      const fileName = struct.path.split('/').pop();
      console.log(`\n📄 ${fileName}:`);
      console.log(`   Signatures found: ${struct.count}`);
      if (struct.signatures.length > 0) {
        console.log(`   Examples:`);
        struct.signatures.slice(0, 5).forEach(sig => {
          console.log(`     • ${sig.substring(0, 100)}${sig.length > 100 ? '...' : ''}`);
        });
      }
    }

    console.log('\n🎉 Code indexing and structure extraction works!');

  } catch (error) {
    console.error('❌ Test failed:', error);
    console.error(error.stack);
    process.exit(1);
  }
}

test();
