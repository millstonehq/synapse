#!/usr/bin/env node

/**
 * Test bundled Continue tree-sitter code structure extraction
 */

import { getCodeStructureToolV2 } from './dist/bundled/code-structure-v2.js';

async function testTreeSitter() {
  console.log('🧪 Testing bundled tree-sitter code structure extraction\n');

  const workspaceDir = process.cwd();
  const tsFiles = [
    workspaceDir + '/src/server-v2.ts',
    workspaceDir + '/src/continue/ContinueIDE.ts',
  ];

  try {
    console.log('Test: Extracting code structure with tree-sitter...');
    const result = await getCodeStructureToolV2({
      paths: tsFiles,
      scope: 'paths',
    });

    console.log(`✅ Extraction completed!`);
    console.log(`   Files processed: ${result.performance.filesProcessed}`);
    console.log(`   Extraction time: ${result.performance.extractionTime}ms`);

    for (const struct of result.structures) {
      const fileName = struct.path.split('/').pop();
      console.log(`\n   ${fileName}:`);
      console.log(`   - Signatures found: ${struct.count}`);
      if (struct.signatures.length > 0) {
        console.log(`   - Examples:`);
        struct.signatures.slice(0, 3).forEach(sig => {
          console.log(`     • ${sig.substring(0, 80)}${sig.length > 80 ? '...' : ''}`);
        });
      }
    }

    console.log('\n🎉 Tree-sitter code structure extraction works!');

  } catch (error) {
    console.error('❌ Test failed:', error);
    console.error(error.stack);
    process.exit(1);
  }
}

testTreeSitter();
