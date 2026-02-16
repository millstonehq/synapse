import fsExtra from 'fs-extra';
import * as path from 'path';
import glob from 'fast-glob';
import { getDocTypes, getTypeRegistry } from './type-registry.js';
import { expectedFolder } from './naming.js';

const fs = fsExtra;

interface HomepageSection {
  type: string;
  label: string;
  folder: string;
  collection: string;
  count: number;
}

interface HomepageOptions {
  contentDir?: string;
  outputPath?: string;
}

/**
 * Count markdown files in a directory
 */
async function countMarkdownFiles(dirPath: string): Promise<number> {
  try {
    const files = await glob(['**/*.md'], {
      cwd: dirPath,
      absolute: false,
      onlyFiles: true,
      ignore: ['**/Examples/*.md', '**/templates/**']
    });
    return files.length;
  } catch (error) {
    // Directory might not exist yet, which is fine
    return 0;
  }
}

/**
 * Generate homepage content with navigation and getting started sections
 */
export async function generateHomepage(options: HomepageOptions = {}): Promise<void> {
  const {
    contentDir = path.resolve(process.cwd(), 'content'),
    outputPath = path.join(contentDir, 'index.md')
  } = options;

  console.log('Generating homepage...');

  // Define the sections based on doc types
  const sections: HomepageSection[] = [];

  // Get type config from registry with proper pluralization
  const typeConfig = Object.entries(getTypeRegistry()).reduce((acc, [type, metadata]) => {
    // Special pluralization rules
    let pluralLabel = metadata.displayLabel;
    if (pluralLabel.endsWith('y') && !pluralLabel.endsWith('ey')) {
      pluralLabel = pluralLabel.slice(0, -1) + 'ies'; // Policy -> Policies
    } else if (pluralLabel.endsWith('s') || pluralLabel.endsWith('x') || pluralLabel.endsWith('ch')) {
      pluralLabel += 'es'; // Process -> Processes
    } else {
      pluralLabel += 's'; // Standard -> Standards
    }
    
    acc[type] = {
      label: pluralLabel,
      collection: metadata.cmsCollection
    };
    return acc;
  }, {} as Record<string, { label: string; collection: string }>);

  // Build sections for each doc type
  for (const docType of getDocTypes()) {
    const folder = expectedFolder(docType);
    const config = typeConfig[docType];

    if (config && folder) {
      // Remove 'content/' prefix since contentDir already contains it
      const relativeFolderPath = folder.replace(/^content\//, '');
      const folderPath = path.join(contentDir, relativeFolderPath);
      const count = await countMarkdownFiles(folderPath);

      // Debug logging
      if (count > 0) {
        console.log(`  ${config.label}: ${count} documents in ${folder}`);
      }

      sections.push({
        type: docType,
        label: config.label,
        folder,
        collection: config.collection,
        count
      });
    }
  }

  // Build homepage content
  let content = `# Synapse Documentation Framework

Welcome to your centralized documentation hub. This framework provides a structured approach to managing technical and operational documentation.

## Quick Navigation

Navigate to documentation by type:

`;

  // Group sections by category for better organization
  const policyGroup = sections.filter(s => ['policy', 'standard'].includes(s.type));
  const processGroup = sections.filter(s => ['process', 'sop', 'runbook'].includes(s.type));
  const meetingGroup = sections.filter(s => ['meeting', 'scorecard'].includes(s.type));
  const architectureGroup = sections.filter(s => ['adr', 'tdd'].includes(s.type));
  const productGroup = sections.filter(s => ['prd'].includes(s.type));
  const systemGroup = sections.filter(s => ['system', 'capability'].includes(s.type));

  // Add Policy & Standards section
  if (policyGroup.length > 0) {
    content += `### Governance & Standards\n\n`;
    for (const section of policyGroup) {
      content += `- **${section.label}** (${section.count}): [[${section.folder}]] • [Edit in CMS](/admin/#/collections/${section.collection})\n`;
    }
    content += '\n';
  }

  // Add Process & Operations section
  if (processGroup.length > 0) {
    content += `### Processes & Operations\n\n`;
    for (const section of processGroup) {
      content += `- **${section.label}** (${section.count}): [[${section.folder}]] • [Edit in CMS](/admin/#/collections/${section.collection})\n`;
    }
    content += '\n';
  }

  // Add Meetings & Assessments section
  if (meetingGroup.length > 0) {
    content += `### Meetings & Assessments\n\n`;
    for (const section of meetingGroup) {
      content += `- **${section.label}** (${section.count}): [[${section.folder}]] • [Edit in CMS](/admin/#/collections/${section.collection})\n`;
    }
    content += '\n';
  }

  // Add Architecture section
  if (architectureGroup.length > 0) {
    content += `### Architecture\n\n`;
    for (const section of architectureGroup) {
      content += `- **${section.label}** (${section.count}): [[${section.folder}]] • [Edit in CMS](/admin/#/collections/${section.collection})\n`;
    }
    content += '\n';
  }

  // Add Products section
  if (productGroup.length > 0) {
    content += `### Products\n\n`;
    for (const section of productGroup) {
      content += `- **${section.label}** (${section.count}): [[${section.folder}]] • [Edit in CMS](/admin/#/collections/${section.collection})\n`;
    }
    content += '\n';
  }

  // Add Systems & Capabilities section
  if (systemGroup.length > 0) {
    content += `### Systems & Capabilities\n\n`;
    for (const section of systemGroup) {
      content += `- **${section.label}** (${section.count}): [[${section.folder}]] • [Edit in CMS](/admin/#/collections/${section.collection})\n`;
    }
    content += '\n';
  }

  // Add Getting Started section
  content += `## Getting Started

New to the framework? Start here:

- **[[00_Guides/Authoring Guide]]**: Learn how to create and maintain documentation
- **[[00_Guides/Examples]]**: Browse example documents for each type

## Recent Activity

_This section will be automatically updated with recent changes._

## Statistics

Total documents: **${sections.reduce((sum, s) => sum + s.count, 0)}**

| Type | Count |
|------|-------|
${sections.map(s => `| ${s.label} | ${s.count} |`).join('\n')}

---

_Last updated: ${new Date().toISOString()}_
`;

  // Ensure the output directory exists
  await fs.ensureDir(path.dirname(outputPath));

  // Write the homepage
  await fs.writeFile(outputPath, content, 'utf-8');
  console.log(`Homepage generated at: ${outputPath}`);

  // Log summary
  const totalDocs = sections.reduce((sum, s) => sum + s.count, 0);
  console.log(`Total documents indexed: ${totalDocs}`);
}
