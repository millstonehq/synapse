#!/usr/bin/env tsx
/**
 * Script to remove duplicate sections from markdown files
 * Keeps the last occurrence of each section (which typically has more content)
 */

import fsExtra from 'fs-extra';
import * as path from 'path';
import * as yaml from 'js-yaml';
import glob from 'fast-glob';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const fs = fsExtra;

interface Section {
  title: string;
  normalizedTitle: string;
  content: string[];
  startLine: number;
}

function deduplicateBody(body: string): { deduped: string; duplicatesFound: string[] } {
  const lines = body.split('\n');
  const sections: Section[] = [];
  const duplicates: string[] = [];
  let currentSection: Section | null = null;

  // Parse all sections
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const heading = line.match(/^##\s+(.+)$/);
    
    if (heading) {
      // Save previous section
      if (currentSection) {
        sections.push(currentSection);
      }
      
      // Start new section
      currentSection = {
        title: heading[1].trim(),
        normalizedTitle: heading[1].trim().toLowerCase(),
        content: [line],
        startLine: i,
      };
    } else if (currentSection) {
      currentSection.content.push(line);
    } else {
      // Content before first section - preserve it
      if (!currentSection) {
        sections.push({
          title: '__preamble__',
          normalizedTitle: '__preamble__',
          content: [line],
          startLine: i,
        });
      }
    }
  }
  
  // Save last section
  if (currentSection) {
    sections.push(currentSection);
  }

  // Find and remove duplicates, keeping last occurrence
  const seen = new Map<string, number>();
  const toKeep = new Set<number>();

  for (let i = 0; i < sections.length; i++) {
    const section = sections[i];
    const prevIndex = seen.get(section.normalizedTitle);
    
    if (prevIndex !== undefined && section.normalizedTitle !== '__preamble__') {
      // Mark duplicate found
      if (!duplicates.includes(section.title)) {
        duplicates.push(section.title);
      }
      // Remove previous occurrence, keep this one (last wins)
      toKeep.delete(prevIndex);
    }
    
    toKeep.add(i);
    seen.set(section.normalizedTitle, i);
  }

  // Rebuild body with deduplicated sections
  const dedupedLines: string[] = [];
  for (let i = 0; i < sections.length; i++) {
    if (toKeep.has(i)) {
      dedupedLines.push(...sections[i].content);
    }
  }

  return {
    deduped: dedupedLines.join('\n'),
    duplicatesFound: duplicates,
  };
}

async function deduplicateFile(filePath: string, dryRun: boolean = false): Promise<boolean> {
  const content = await fs.readFile(filePath, 'utf-8');

  // Extract frontmatter and body
  const match = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!match) {
    return false;
  }

  const [, frontmatterStr, body] = match;
  
  const { deduped, duplicatesFound } = deduplicateBody(body);

  if (duplicatesFound.length === 0) {
    return false;
  }

  if (!dryRun) {
    const newContent = `---\n${frontmatterStr}\n---\n${deduped}`;
    await fs.writeFile(filePath, newContent, 'utf-8');
  }

  return true;
}

async function main() {
  const dryRun = process.argv.includes('--dry-run');
  const contentDir = path.resolve(__dirname, '../../../content');

  console.log(dryRun ? '🔍 DRY RUN MODE - No files will be modified\n' : '📝 DEDUPLICATION MODE - Removing duplicates\n');

  const allFiles = await glob('**/*.md', {
    cwd: contentDir,
    absolute: true,
    ignore: ['**/node_modules/**', '**/dist/**'],
  });

  console.log(`Found ${allFiles.length} markdown files\n`);

  let deduplicated = 0;
  let skipped = 0;
  let errors = 0;

  for (const file of allFiles) {
    try {
      const hadDuplicates = await deduplicateFile(file, dryRun);
      if (hadDuplicates) {
        console.log(`✅ ${dryRun ? 'Would deduplicate' : 'Deduplicated'} ${path.relative(contentDir, file)}`);
        deduplicated++;
      } else {
        skipped++;
      }
    } catch (error) {
      console.error(`❌ Error processing ${path.basename(file)}:`, error);
      errors++;
    }
  }

  console.log(`\n📊 Summary:`);
  console.log(`   ${dryRun ? 'Would deduplicate' : 'Deduplicated'}: ${deduplicated}`);
  console.log(`   Skipped (no duplicates): ${skipped}`);
  console.log(`   Errors: ${errors}`);

  if (dryRun) {
    console.log(`\n💡 Run without --dry-run to apply changes`);
  }
}

main().catch(console.error);
