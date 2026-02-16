import fsExtra from 'fs-extra';
import * as path from 'path';
import * as readline from 'readline/promises';
import { createRequire } from 'module';
import { getDocTypes, getTypeRegistry } from '../lib/type-registry.js';

const fs = fsExtra;
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
        cyan: (str: string) => str,
      };
    }
  }
  return chalk;
}

export interface InitOptions {
  siteName?: string;
  baseUrl?: string;
  force?: boolean;
  interactive?: boolean;
  cwd?: string;
}

/**
 * Resolve the @millstone/synapse-schemas package directory
 */
function resolveSchemasPackage(cwd: string): string {
  try {
    const require = createRequire(path.join(cwd, 'package.json'));
    const pkgPath = require.resolve('@millstone/synapse-schemas/package.json');
    return path.dirname(pkgPath);
  } catch {
    throw new Error(
      '@millstone/synapse-schemas package not found.\n' +
      'Install it first: npm install @millstone/synapse-cli'
    );
  }
}

/**
 * Prompt user for input with optional default
 */
async function prompt(rl: readline.Interface, question: string, defaultValue?: string): Promise<string> {
  const suffix = defaultValue ? ` (${defaultValue})` : '';
  const answer = await rl.question(`${question}${suffix}: `);
  return answer.trim() || defaultValue || '';
}

/**
 * Bootstrap a new Synapse documentation project.
 *
 * Copies schemas from @millstone/synapse-schemas into local schemas/ directory,
 * creates the content folder structure, and generates synapse.config.json.
 */
export async function init(options: InitOptions = {}): Promise<void> {
  const c = await getChalk();
  const rootDir = options.cwd ?? process.cwd();

  console.log(c.bold('\n🧬 Synapse Project Bootstrap\n'));

  // Check if already initialized
  const schemasDir = path.join(rootDir, 'schemas', 'frontmatter');
  if (await fs.pathExists(schemasDir)) {
    const files = await fs.readdir(schemasDir);
    const hasSchemas = files.some((f: string) => f.endsWith('.schema.json'));
    if (hasSchemas && !options.force) {
      console.log(c.yellow('⚠️  schemas/frontmatter/ already exists with schema files.'));
      console.log(c.gray('Use --force to re-bootstrap from the package.\n'));
      return;
    }
  }

  // Resolve schemas package
  console.log(c.blue('📦 Resolving @millstone/synapse-schemas...'));
  const schemasPkgDir = resolveSchemasPackage(rootDir);

  const pkgJson = JSON.parse(await fs.readFile(path.join(schemasPkgDir, 'package.json'), 'utf-8'));
  console.log(c.green(`   ✓ Found v${pkgJson.version}`));

  // Gather config via prompts if interactive
  let siteName = options.siteName;
  let baseUrl = options.baseUrl;

  if (options.interactive !== false && (!siteName || !baseUrl)) {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
    });

    try {
      console.log(c.gray('\nConfigure your project:\n'));

      if (!siteName) {
        const dirName = path.basename(rootDir);
        siteName = await prompt(rl, 'Site name', dirName);
      }

      if (!baseUrl) {
        baseUrl = await prompt(rl, 'Base URL (for Quartz site)', `${siteName}.local`);
      }

      console.log();
    } finally {
      rl.close();
    }
  }

  siteName = siteName || path.basename(rootDir);
  baseUrl = baseUrl || `${siteName}.local`;

  // 1. Copy schemas
  console.log(c.blue('📋 Copying schemas to local project...'));

  const frontmatterSrc = path.join(schemasPkgDir, 'frontmatter');
  const bodyGrammarsSrc = path.join(schemasPkgDir, 'body-grammars');
  const frontmatterDest = path.join(rootDir, 'schemas', 'frontmatter');
  const bodyGrammarsDest = path.join(rootDir, 'schemas', 'body-grammars');

  await fs.ensureDir(frontmatterDest);
  await fs.ensureDir(bodyGrammarsDest);

  // Copy frontmatter schemas
  if (await fs.pathExists(frontmatterSrc)) {
    const files = await fs.readdir(frontmatterSrc);
    let count = 0;
    for (const file of files) {
      if (!file.endsWith('.schema.json')) continue;
      await fs.copy(path.join(frontmatterSrc, file), path.join(frontmatterDest, file), { overwrite: options.force });
      count++;
    }
    console.log(c.green(`   ✓ ${count} frontmatter schemas`));
  }

  // Copy body grammars
  if (await fs.pathExists(bodyGrammarsSrc)) {
    const files = await fs.readdir(bodyGrammarsSrc);
    let count = 0;
    for (const file of files) {
      if (!file.endsWith('.body-grammar.json')) continue;
      await fs.copy(path.join(bodyGrammarsSrc, file), path.join(bodyGrammarsDest, file), { overwrite: options.force });
      count++;
    }
    console.log(c.green(`   ✓ ${count} body grammars`));
  }

  // 2. Create content directory structure
  console.log(c.blue('\n📁 Creating content directories...'));

  const registry = getTypeRegistry();
  const createdDirs = new Set<string>();

  for (const type of getDocTypes()) {
    const folder = registry[type].folder;
    const dirPath = path.join(rootDir, 'content', folder);
    await fs.ensureDir(dirPath);

    // Track unique top-level dirs for display
    const topLevel = folder.split('/')[0];
    createdDirs.add(topLevel);

    // Add .gitkeep if empty
    const files = await fs.readdir(dirPath);
    if (files.length === 0) {
      await fs.writeFile(path.join(dirPath, '.gitkeep'), '', 'utf-8');
    }
  }

  console.log(c.green(`   ✓ ${createdDirs.size} content directories`));

  // 3. Create synapse.config.json
  const configPath = path.join(rootDir, 'synapse.config.json');
  if (!(await fs.pathExists(configPath)) || options.force) {
    console.log(c.blue('\n⚙️  Creating synapse.config.json...'));

    const config = {
      branding: {
        siteName,
        displayName: siteName,
        baseUrl,
      },
    };

    await fs.writeFile(configPath, JSON.stringify(config, null, 2) + '\n', 'utf-8');
    console.log(c.green('   ✓ Created synapse.config.json'));
  } else {
    console.log(c.gray('\n   synapse.config.json already exists, skipping'));
  }

  // 4. Create .gitignore if it doesn't exist
  const gitignorePath = path.join(rootDir, '.gitignore');
  if (!(await fs.pathExists(gitignorePath))) {
    console.log(c.blue('\n📄 Creating .gitignore...'));
    await fs.writeFile(gitignorePath, 'node_modules/\n.DS_Store\n', 'utf-8');
    console.log(c.green('   ✓ Created .gitignore'));
  }

  // Summary
  console.log(c.bold(c.green('\n✅ Project bootstrapped!\n')));
  console.log(c.gray('Project structure:'));
  console.log(c.gray('  schemas/frontmatter/   — Frontmatter JSON schemas (customize per project)'));
  console.log(c.gray('  schemas/body-grammars/ — Body grammar rules'));
  console.log(c.gray('  content/               — Your documentation'));
  console.log(c.gray('  synapse.config.json    — Project configuration'));
  console.log(c.gray('\nNext steps:'));
  console.log(c.gray('  1. Create a document:  npx synapse scaffold --type adr --title "My Decision"'));
  console.log(c.gray('  2. Validate:           npx synapse validate'));
  console.log(c.gray('  3. Generate homepage:  npx synapse index'));
  console.log();
}

/**
 * CLI command handler for init
 */
export async function initCommand(args: {
  siteName?: string;
  baseUrl?: string;
  force?: boolean;
  yes?: boolean;
}): Promise<void> {
  const c = await getChalk();

  try {
    await init({
      siteName: args.siteName,
      baseUrl: args.baseUrl,
      force: args.force,
      interactive: !args.yes,
    });
  } catch (error) {
    console.error(c.red('\nError:'), error instanceof Error ? error.message : error);
    process.exit(1);
  }
}
