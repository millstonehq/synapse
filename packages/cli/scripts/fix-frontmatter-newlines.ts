#!/usr/bin/env tsx
/**
 * Script to fix broken frontmatter by adding missing newline before closing ---
 */

import fsExtra from 'fs-extra';
import * as path from 'path';
import glob from 'fast-glob';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const fs = fsExtra;

async function fixFile(filePath: string): Promise<boolean> {
  const content = await fs.readFile(filePath, 'utf-8');

  // Check if frontmatter is broken (missing newline before closing ---)
  // Pattern: YAML content followed by ---\n with no newline before ---
  const brokenPattern = /^---\n([\s\S]*?[^\n])---\n/;
  const match = content.match(brokenPattern);

  if (!match) {
    return false;
  }

  // Fix by adding newline before closing ---
  const fixed = content.replace(brokenPattern, '---\n$1\n---\n');

  await fs.writeFile(filePath, fixed, 'utf-8');
  return true;
}

async function main() {
  const contentDir = path.resolve(__dirname, '../../../content');

  const allFiles = await glob('**/*.md', {
    cwd: contentDir,
    absolute: true,
    ignore: ['**/node_modules/**', '**/dist/**'],
  });

  console.log(`📝 Fixing frontmatter newlines in ${allFiles.length} files\n`);

  let fixed = 0;
  let skipped = 0;
  let errors = 0;

  for (const file of allFiles) {
    try {
      const wasFixed = await fixFile(file);
      if (wasFixed) {
        console.log(`✅ Fixed ${path.relative(contentDir, file)}`);
        fixed++;
      } else {
        skipped++;
      }
    } catch (error) {
      console.error(`❌ Error processing ${path.basename(file)}:`, error);
      errors++;
    }
  }

  console.log(`\n📊 Summary:`);
  console.log(`   Fixed: ${fixed}`);
  console.log(`   Skipped: ${skipped}`);
  console.log(`   Errors: ${errors}`);
}

main().catch(console.error);
