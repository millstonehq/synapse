#!/usr/bin/env tsx
/**
 * Script to convert frontmatter content to body sections for process files
 * Replaces TODO placeholders with actual content from frontmatter
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

interface ProcessFrontmatter {
  id: string;
  type: string;
  title: string;
  purpose?: string;
  scope?: string;
  roles?: string[];
  triggers?: string;
  inputs?: string[];
  outputs?: string[];
  steps?: string[];
  controls?: string[];
  [key: string]: any;
}

async function fixProcessFile(filePath: string): Promise<void> {
  const content = await fs.readFile(filePath, 'utf-8');

  // Extract frontmatter and body
  const match = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!match) {
    console.log(`⚠️  Skipping ${path.basename(filePath)}: No frontmatter found`);
    return;
  }

  const [, frontmatterStr, body] = match;
  const frontmatter = yaml.load(frontmatterStr) as ProcessFrontmatter;

  // Skip if not a process type
  if (frontmatter.type !== 'process') {
    console.log(`⚠️  Skipping ${path.basename(filePath)}: Not a process document`);
    return;
  }

  // Check if body has TODOs that need replacing
  const hasTodos = body.includes('_[TODO: Complete this section]_') ||
                   body.includes('\\_\\[TODO: Complete this section]\\_');

  if (!hasTodos) {
    console.log(`✓  Skipping ${path.basename(filePath)}: Already has content`);
    return;
  }

  // Build new body sections
  const sections: string[] = [];

  // Purpose section
  if (frontmatter.purpose) {
    sections.push('## Purpose\n');
    sections.push(`${frontmatter.purpose}\n`);
  }

  // Scope section
  if (frontmatter.scope) {
    sections.push('## Scope\n');
    sections.push(`${frontmatter.scope}\n`);
  }

  // Roles and Responsibilities section
  if (frontmatter.roles && frontmatter.roles.length > 0) {
    sections.push('## Roles and Responsibilities\n');
    for (const role of frontmatter.roles) {
      sections.push(`- **${role}**\n`);
    }
    sections.push('');
  }

  // Triggers section
  if (frontmatter.triggers) {
    sections.push('## Triggers\n');
    sections.push(`${frontmatter.triggers}\n`);
  }

  // Inputs section
  if (frontmatter.inputs && frontmatter.inputs.length > 0) {
    sections.push('## Inputs\n');
    for (const input of frontmatter.inputs) {
      sections.push(`- ${input}\n`);
    }
    sections.push('');
  }

  // Outputs section
  if (frontmatter.outputs && frontmatter.outputs.length > 0) {
    sections.push('## Outputs\n');
    for (const output of frontmatter.outputs) {
      sections.push(`- ${output}\n`);
    }
    sections.push('');
  }

  // Steps section (ordered list)
  if (frontmatter.steps && frontmatter.steps.length > 0) {
    sections.push('## Steps\n');
    for (const step of frontmatter.steps) {
      sections.push(`1. ${step}\n`);
    }
    sections.push('');
  }

  // Controls section
  if (frontmatter.controls && frontmatter.controls.length > 0) {
    sections.push('## Controls\n');
    for (const control of frontmatter.controls) {
      sections.push(`- ${control}\n`);
    }
    sections.push('');
  }

  // Reconstruct the file
  const newContent = `---\n${frontmatterStr}\n---\n${sections.join('\n')}`;

  await fs.writeFile(filePath, newContent, 'utf-8');
  console.log(`✅ Fixed ${path.basename(filePath)}`);
}

async function main() {
  const contentDir = path.resolve(__dirname, '../../../content');
  const processFiles = await glob('30_Processes/*.md', {
    cwd: contentDir,
    absolute: true,
  });

  console.log(`Found ${processFiles.length} process files\n`);

  let fixed = 0;
  let skipped = 0;
  let errors = 0;

  for (const file of processFiles) {
    try {
      const beforeContent = await fs.readFile(file, 'utf-8');
      const hasTodos = beforeContent.includes('_[TODO: Complete this section]_') ||
                       beforeContent.includes('\\_\\[TODO: Complete this section]\\_');

      await fixProcessFile(file);

      const afterContent = await fs.readFile(file, 'utf-8');
      const stillHasTodos = afterContent.includes('_[TODO: Complete this section]_') ||
                            afterContent.includes('\\_\\[TODO: Complete this section]\\_');

      if (hasTodos && !stillHasTodos) {
        fixed++;
      } else if (!hasTodos) {
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
