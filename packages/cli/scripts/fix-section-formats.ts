import fsExtra from 'fs-extra';
import * as path from 'path';
import * as yaml from 'js-yaml';
import glob from 'fast-glob';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const fs = fsExtra;

interface DocFrontmatter {
  id: string;
  type: string;
  title: string;
  [key: string]: any;
}

// Convert paragraph content to unordered list
function convertToList(content: string): string {
  const lines = content.split('\n').filter(line => line.trim() && !line.trim().startsWith('-'));
  if (lines.length === 0) return content;
  return lines.map(line => `- ${line.trim()}`).join('\n');
}

// Check if content is already a list
function isAlreadyList(content: string): boolean {
  const lines = content.split('\n').filter(line => line.trim());
  return lines.length > 0 && lines.every(line => line.trim().startsWith('-') || line.trim().startsWith('*'));
}

// Check if content is already a table
function isAlreadyTable(content: string): boolean {
  return content.includes('|') && content.includes('---');
}

// Convert content to table format for "Risks and Mitigations"
function convertToRisksTable(content: string): string {
  if (isAlreadyTable(content)) return content;

  // Create table header
  const header = '| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |';
  const separator = '|------|----------|------------|-------|------------|----------|';

  // If there's existing content, try to preserve it in a basic row
  const lines = content.split('\n').filter(line => line.trim());
  if (lines.length === 0) {
    return `${header}\n${separator}\n| _[TODO: Add risks]_ | H/M/L | H/M/L | TBD | TBD | TBD |`;
  }

  // Try to convert existing list items to table rows
  const rows = lines.map(line => {
    const text = line.replace(/^[-*]\s*/, '').trim();
    return `| ${text} | TBD | TBD | TBD | TBD | TBD |`;
  });

  return `${header}\n${separator}\n${rows.join('\n')}`;
}

async function fixSectionFormats(filePath: string, dryRun: boolean = false): Promise<boolean> {
  const content = await fs.readFile(filePath, 'utf-8');

  // Extract frontmatter and body
  const match = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!match) {
    console.log(`⚠️  Skipping ${path.basename(filePath)}: No frontmatter found`);
    return false;
  }

  const [, frontmatterStr, body] = match;
  const frontmatter = yaml.load(frontmatterStr) as DocFrontmatter;

  if (!frontmatter.type) {
    console.log(`⚠️  Skipping ${path.basename(filePath)}: No type specified`);
    return false;
  }

  let modified = false;
  let newBody = body;

  // Define sections that should be lists by doc type
  const listSections: Record<string, string[]> = {
    sop: ['Preconditions', 'Materials/Access', 'Materials', 'Access'],
    meeting: ['Observations by Domain', 'Key Metrics & Data Points', 'Key Metrics and Data Points', 'Preliminary Scorecard Hooks'],
    prd: ['In Scope', 'Out of Scope'],
    runbook: ['Service', 'Alerts', 'Dashboards'],
    process: ['Inputs', 'Outputs', 'Roles and Responsibilities'],
  };

  // Define sections that should be tables
  const tableSections: Record<string, string[]> = {
    meeting: ['Risks and Mitigations'],
  };

  const type = frontmatter.type;
  const shouldBeList = listSections[type] || [];
  const shouldBeTable = tableSections[type] || [];

  // Process each section
  const sections: Array<{ title: string; content: string; startIdx: number; endIdx: number }> = [];
  const lines = newBody.split('\n');
  let currentSection: { title: string; startIdx: number; lines: string[] } | null = null;

  lines.forEach((line, idx) => {
    const heading = line.match(/^##\s+(.+)$/);
    if (heading) {
      // Save previous section
      if (currentSection) {
        sections.push({
          title: currentSection.title,
          content: currentSection.lines.join('\n'),
          startIdx: currentSection.startIdx,
          endIdx: idx - 1,
        });
      }
      // Start new section
      currentSection = {
        title: heading[1].trim(),
        startIdx: idx,
        lines: [],
      };
    } else if (currentSection) {
      currentSection.lines.push(line);
    }
  });

  // Save last section
  if (currentSection) {
    sections.push({
      title: currentSection.title,
      content: currentSection.lines.join('\n'),
      startIdx: currentSection.startIdx,
      endIdx: lines.length - 1,
    });
  }

  // Fix sections
  sections.forEach(section => {
    const trimmedContent = section.content.trim();

    // Skip empty sections or placeholder sections
    if (!trimmedContent || trimmedContent.includes('_[TODO: Complete this section]_')) {
      return;
    }

    // Check if section should be a list
    if (shouldBeList.includes(section.title)) {
      if (!isAlreadyList(trimmedContent)) {
        const listContent = convertToList(trimmedContent);
        newBody = newBody.replace(
          `## ${section.title}\n${section.content}`,
          `## ${section.title}\n\n${listContent}\n`
        );
        modified = true;
      }
    }

    // Check if section should be a table
    if (shouldBeTable.includes(section.title)) {
      if (!isAlreadyTable(trimmedContent)) {
        const tableContent = convertToRisksTable(trimmedContent);
        newBody = newBody.replace(
          `## ${section.title}\n${section.content}`,
          `## ${section.title}\n\n${tableContent}\n`
        );
        modified = true;
      }
    }
  });

  if (!modified) {
    return false;
  }

  // Reconstruct file
  const newContent = `---\n${frontmatterStr}\n---\n${newBody}`;

  if (!dryRun) {
    await fs.writeFile(filePath, newContent, 'utf-8');
  }

  return true;
}

async function main() {
  const dryRun = process.argv.includes('--dry-run');

  if (dryRun) {
    console.log('🔍 DRY RUN MODE - No files will be modified\n');
  }

  const contentDir = path.resolve(__dirname, '../../../content');
  const files = await glob('**/*.md', { cwd: contentDir, absolute: true });

  console.log(`Found ${files.length} markdown files\n`);

  let fixed = 0;
  let skipped = 0;
  let errors = 0;

  for (const file of files) {
    try {
      const wasFixed = await fixSectionFormats(file, dryRun);
      if (wasFixed) {
        const relativePath = path.relative(contentDir, file);
        console.log(`${dryRun ? '✅ Would fix' : '✅ Fixed'} ${relativePath}`);
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
  console.log(`   ${dryRun ? 'Would fix' : 'Fixed'}: ${fixed}`);
  console.log(`   Skipped: ${skipped}`);
  console.log(`   Errors: ${errors}`);

  if (dryRun) {
    console.log('\n💡 Run without --dry-run to apply changes');
  }
}

main().catch(console.error);
