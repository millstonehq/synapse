import * as path from 'path';
import fsExtra from 'fs-extra';
const fs = fsExtra;
import * as yaml from 'js-yaml';
import { getDocTypes, isKnownDocType, getTypeRegistry, getExpectedFolder, getDisplayLabel } from '../lib/type-registry.js';

let chalk: any;

async function getChalk() {
  if (!chalk) {
    try {
      chalk = (await import('chalk')).default;
    } catch {
      chalk = {
        green: (str: string) => str,
        red: (str: string) => str,
        yellow: (str: string) => str,
        blue: (str: string) => str,
        gray: (str: string) => str,
        bold: (str: string) => str,
        cyan: (str: string) => str
      };
    }
  }
  return chalk;
}

export interface ScaffoldOptions {
  type: string;
  title: string;
  owner?: string;
  id?: string;
  targetDir?: string;
  force?: boolean;
  cwd?: string;
}

/**
 * Convert a title to kebab-case for use in filenames
 */
function toKebabCase(str: string): string {
  return str
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

/**
 * Find the example file for a given document type
 */
async function findExampleFile(type: string, cwd: string): Promise<string | null> {
  const folder = getTypeRegistry()[type].folder;
  const examplesDir = path.join(cwd, 'content', folder, 'examples');

  if (!await fs.pathExists(examplesDir)) {
    return null;
  }

  const files = await fs.readdir(examplesDir);
  const mdFiles = files.filter(f => f.endsWith('.md'));

  if (mdFiles.length === 0) {
    return null;
  }

  return path.join(examplesDir, mdFiles[0]);
}

/**
 * Parse frontmatter and body from markdown content
 */
function parseFrontmatterAndBody(content: string): { frontmatter: Record<string, any>; body: string } {
  const lines = content.split('\n');
  let startLine = -1;
  let endLine = -1;

  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim() === '---') {
      if (startLine === -1) {
        startLine = i;
      } else {
        endLine = i;
        break;
      }
    }
  }

  if (startLine === -1 || endLine === -1) {
    return { frontmatter: {}, body: content };
  }

  const fmString = lines.slice(startLine + 1, endLine).join('\n');
  const body = lines.slice(endLine + 1).join('\n');
  const frontmatter = (yaml.load(fmString) as Record<string, any>) || {};

  return { frontmatter, body };
}

/**
 * Generate the next sequential ID for a document type by scanning existing files
 */
async function generateNextId(type: string, cwd: string): Promise<string> {
  const label = getDisplayLabel(type);
  const prefix = label.toUpperCase().replace(/\s+/g, '-');
  const folder = getExpectedFolder(type);
  const typeDir = path.join(cwd, folder);

  let maxNum = 0;

  if (await fs.pathExists(typeDir)) {
    const files = await fs.readdir(typeDir);
    const pattern = new RegExp(`^${prefix}-(\\d+)`, 'i');

    for (const file of files) {
      const match = file.match(pattern);
      if (match) {
        const num = parseInt(match[1], 10);
        if (num > maxNum) {
          maxNum = num;
        }
      }
    }

    // Also check frontmatter id fields for the pattern
    for (const file of files) {
      if (!file.endsWith('.md')) continue;
      const filePath = path.join(typeDir, file);
      const stat = await fs.stat(filePath);
      if (!stat.isFile()) continue;

      try {
        const content = await fs.readFile(filePath, 'utf-8');
        const { frontmatter } = parseFrontmatterAndBody(content);
        if (frontmatter.id && typeof frontmatter.id === 'string') {
          const match = frontmatter.id.match(new RegExp(`^${prefix}-(\\d+)$`, 'i'));
          if (match) {
            const num = parseInt(match[1], 10);
            if (num > maxNum) {
              maxNum = num;
            }
          }
        }
      } catch {
        // skip files that can't be read
      }
    }
  }

  const nextNum = String(maxNum + 1).padStart(3, '0');
  return `${prefix}-${nextNum}`;
}

/**
 * Scaffold a new document from an example file
 */
export async function scaffold(options: ScaffoldOptions): Promise<string> {
  const c = await getChalk();
  const cwd = options.cwd || process.cwd();

  // 1. Validate document type
  const type = options.type?.toLowerCase();
  if (!type) {
    throw new Error('Missing required option: --type. Available types: ' + getDocTypes().join(', '));
  }
  if (!isKnownDocType(type)) {
    throw new Error(`Invalid document type: "${type}". Available types: ${getDocTypes().join(', ')}`);
  }

  // 2. Validate title
  if (!options.title) {
    throw new Error('Missing required option: --title');
  }

  // 3. Find the example file
  const examplePath = await findExampleFile(type, cwd);
  if (!examplePath) {
    throw new Error(
      `No example file found for type "${type}". Expected examples in: content/${getTypeRegistry()[type].folder}/examples/`
    );
  }

  // 4. Read and parse example
  const exampleContent = await fs.readFile(examplePath, 'utf-8');
  const { frontmatter, body } = parseFrontmatterAndBody(exampleContent);

  // 5. Generate or use provided ID
  const id = options.id || await generateNextId(type, cwd);

  // 6. Update frontmatter fields
  const now = new Date().toISOString();
  frontmatter.id = id;
  frontmatter.title = options.title;
  frontmatter.status = 'draft';
  frontmatter.created = now;
  frontmatter.updated = now;

  if (options.owner) {
    frontmatter.owner = options.owner;
  }

  // Remove example flag
  delete frontmatter.example;

  // Remove tags that are just the type name (auto-populated from example)
  if (Array.isArray(frontmatter.tags)) {
    frontmatter.tags = frontmatter.tags.filter((t: string) => t !== type);
    if (frontmatter.tags.length === 0) {
      delete frontmatter.tags;
    }
  }

  // 7. Generate output filename
  const kebabTitle = toKebabCase(options.title);
  const filename = `${id}-${kebabTitle}.md`;

  // 8. Determine output directory
  const outputDir = options.targetDir || path.join(cwd, getExpectedFolder(type));

  // 9. Build output path and check existence
  const outputPath = path.join(outputDir, filename);

  if (await fs.pathExists(outputPath)) {
    if (!options.force) {
      throw new Error(
        `File already exists: ${outputPath}\nUse --force to overwrite.`
      );
    }
  }

  // 10. Build output content
  const fmYaml = yaml.dump(frontmatter, {
    lineWidth: -1,
    quotingType: '"',
    forceQuotes: false
  }).trim();
  const outputContent = `---\n${fmYaml}\n---\n${body}`;

  // 11. Write file
  await fs.ensureDir(outputDir);
  await fs.writeFile(outputPath, outputContent, 'utf-8');

  // 12. Print success
  const relPath = path.relative(cwd, outputPath);
  console.log(c.green(`\nCreated ${getDisplayLabel(type)} document:`));
  console.log(c.cyan(`  ${relPath}`));
  console.log(c.gray(`  Type:   ${type}`));
  console.log(c.gray(`  ID:     ${id}`));
  console.log(c.gray(`  Title:  ${options.title}`));
  if (options.owner) {
    console.log(c.gray(`  Owner:  ${options.owner}`));
  }
  console.log('');

  return outputPath;
}

export async function scaffoldCommand(args: Record<string, any>): Promise<void> {
  // Support both --type and --template for backward compatibility
  const type = args.type || args.template;
  const title = args.title;

  await scaffold({
    type,
    title,
    owner: args.owner,
    id: args.id,
    targetDir: args.targetDir || args.outdir,
    force: args.force,
  });
}

/**
 * Generate a filename from type, id, and title
 */
export function generateFilename(type: string, id: string, title: string): string {
  const kebabTitle = toKebabCase(title);
  return `${id}-${kebabTitle}.md`;
}

/**
 * Parse template variables from a "key=val,key2=val2" string
 */
export function parseTemplateVars(varsString?: string): Record<string, string> {
  if (!varsString) return {};
  const vars: Record<string, string> = {};
  for (const pair of varsString.split(',')) {
    const [key, ...rest] = pair.split('=');
    if (key && rest.length > 0) {
      vars[key.trim()] = rest.join('=').trim();
    }
  }
  return vars;
}
