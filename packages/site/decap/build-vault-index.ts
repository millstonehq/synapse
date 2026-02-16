#!/usr/bin/env npx ts-node
/**
 * Build-time script to generate vault-index.json
 *
 * This script scans the content directory and creates an index of all
 * valid wikilink targets for browser-side validation.
 *
 * Usage: npx ts-node packages/site/decap/build-vault-index.ts
 */

import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import glob from 'fast-glob';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

interface VaultIndex {
  /** Generated timestamp */
  generatedAt: string;
  /** Total file count */
  fileCount: number;
  /** All valid wikilink targets (basenames without .md) */
  targets: string[];
  /** Full relative paths for folder validation */
  paths: string[];
}

async function buildVaultIndex(contentDir: string, outputPath: string): Promise<void> {
  console.log(`Scanning content directory: ${contentDir}`);

  // Find all markdown files
  const files = await glob('**/*.md', {
    cwd: contentDir,
    absolute: false,
    ignore: [
      '**/node_modules/**',
      '**/.git/**',
      '**/templates/**',
      'index.md'
    ]
  });

  console.log(`Found ${files.length} markdown files`);

  // Extract unique targets
  const targets = new Set<string>();
  const paths: string[] = [];

  for (const file of files) {
    // Add full relative path
    paths.push(file);

    // Add basename without extension
    const basename = path.basename(file, '.md');
    targets.add(basename);

    // Also add normalized version (lowercase, dashes)
    const normalized = basename.toLowerCase().replace(/\s+/g, '-');
    targets.add(normalized);
  }

  const index: VaultIndex = {
    generatedAt: new Date().toISOString(),
    fileCount: files.length,
    targets: Array.from(targets).sort(),
    paths: paths.sort()
  };

  // Ensure output directory exists
  const outputDir = path.dirname(outputPath);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // Write index
  fs.writeFileSync(outputPath, JSON.stringify(index, null, 2));
  console.log(`Wrote vault index to: ${outputPath}`);
  console.log(`  - ${index.targets.length} unique targets`);
  console.log(`  - ${index.paths.length} file paths`);
}

async function copySchemas(schemasDir: string, outputDir: string): Promise<void> {
  console.log(`\nCopying schemas from: ${schemasDir}`);

  // Copy frontmatter schemas
  const frontmatterDir = path.join(schemasDir, 'frontmatter');
  const frontmatterOutput = path.join(outputDir, 'schemas');

  if (!fs.existsSync(frontmatterOutput)) {
    fs.mkdirSync(frontmatterOutput, { recursive: true });
  }

  const schemaFiles = await glob('*.schema.json', { cwd: frontmatterDir });
  const schemas: Record<string, any> = {};

  for (const file of schemaFiles) {
    const content = fs.readFileSync(path.join(frontmatterDir, file), 'utf-8');
    const schema = JSON.parse(content);
    const type = file.replace('.schema.json', '');

    // Resolve base schema references
    if (schema.allOf && Array.isArray(schema.allOf)) {
      const basePath = path.join(frontmatterDir, 'base.schema.json');
      const baseContent = fs.readFileSync(basePath, 'utf-8');
      const baseSchema = JSON.parse(baseContent);

      // Merge base with type-specific
      schemas[type] = {
        ...schema,
        properties: {
          ...baseSchema.properties,
          ...schema.properties
        },
        required: [
          ...(baseSchema.required || []),
          ...(schema.required || [])
        ].filter((v, i, a) => a.indexOf(v) === i)
      };
      delete schemas[type].allOf;
    } else if (type !== 'base') {
      schemas[type] = schema;
    }
  }

  fs.writeFileSync(
    path.join(frontmatterOutput, 'index.json'),
    JSON.stringify(schemas, null, 2)
  );
  console.log(`  Wrote ${Object.keys(schemas).length} schemas to schemas/index.json`);

  // Copy body grammars
  const grammarsDir = path.join(schemasDir, 'body-grammars');
  const grammarsOutput = path.join(outputDir, 'body-grammars');

  if (!fs.existsSync(grammarsOutput)) {
    fs.mkdirSync(grammarsOutput, { recursive: true });
  }

  const grammarFiles = await glob('*.body-grammar.json', { cwd: grammarsDir });
  const grammars: Record<string, any> = {};

  for (const file of grammarFiles) {
    const content = fs.readFileSync(path.join(grammarsDir, file), 'utf-8');
    const grammar = JSON.parse(content);
    grammars[grammar.type] = grammar;
  }

  fs.writeFileSync(
    path.join(grammarsOutput, 'index.json'),
    JSON.stringify(grammars, null, 2)
  );
  console.log(`  Wrote ${Object.keys(grammars).length} grammars to body-grammars/index.json`);
}

async function main(): Promise<void> {
  // Determine paths
  const projectRoot = path.resolve(__dirname, '../../..');
  const contentDir = path.join(projectRoot, 'content');
  const schemasDir = path.join(projectRoot, 'schemas');
  const outputDir = path.join(__dirname, '../static/edit');

  console.log('=== Building Decap CMS Validation Assets ===\n');

  // Build vault index
  await buildVaultIndex(contentDir, path.join(outputDir, 'vault-index.json'));

  // Copy and process schemas
  await copySchemas(schemasDir, outputDir);

  console.log('\n=== Build Complete ===');
}

main().catch(error => {
  console.error('Build failed:', error);
  process.exit(1);
});
