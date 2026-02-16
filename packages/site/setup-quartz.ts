#!/usr/bin/env tsx

import { execSync } from 'child_process';
import { existsSync, copyFileSync, rmSync, symlinkSync, readFileSync, writeFileSync } from 'fs';
import { join, resolve } from 'path';
import chalk from 'chalk';

/**
 * Setup script for Quartz 4 as a git submodule in Synapse Documentation Framework
 * This script handles the initialization and configuration of Quartz for SYN-P1-T02
 */

const SITE_DIR = resolve(import.meta.dirname);
const QUARTZ_DIR = join(SITE_DIR, 'quartz');
const PROJECT_ROOT = resolve(SITE_DIR, '../..');
const CONTENT_DIR = join(PROJECT_ROOT, 'content');

function run(command: string, options: { cwd?: string; silent?: boolean } = {}) {
  const { cwd = SITE_DIR, silent = false } = options;
  
  if (!silent) {
    console.log(chalk.gray(`  $ ${command}`));
  }
  
  try {
    return execSync(command, { 
      cwd, 
      stdio: silent ? 'pipe' : 'inherit',
      encoding: 'utf8'
    });
  } catch (error: any) {
    console.error(chalk.red(`Failed to run: ${command}`));
    console.error(error.message);
    process.exit(1);
  }
}

function setupQuartzSubmodule() {
  console.log(chalk.cyan('🧬 Setting up Quartz 4 for Synapse Documentation...'));

  // Check if submodule already exists
  if (existsSync(QUARTZ_DIR)) {
    console.log(chalk.yellow('⚠️  Quartz submodule already exists'));
    
    // Check if it's initialized
    if (!existsSync(join(QUARTZ_DIR, 'package.json'))) {
      console.log(chalk.blue('📦 Initializing existing submodule...'));
      run('git submodule update --init --recursive', { cwd: PROJECT_ROOT });
    }
  } else {
    // Add Quartz as a submodule
    console.log(chalk.blue('📦 Adding Quartz as a git submodule...'));
    run('git submodule add -b v4 https://github.com/jackyzha0/quartz.git site/quartz', { 
      cwd: PROJECT_ROOT 
    });
  }

  // Install Quartz dependencies
  console.log(chalk.blue('📦 Installing Quartz dependencies...'));
  run('npm install', { cwd: QUARTZ_DIR });

  // Copy our configuration files
  console.log(chalk.blue('⚙️  Applying Synapse configuration...'));
  
  const configFiles = [
    { src: 'quartz.config.ts', dest: 'quartz.config.ts' },
    { src: 'quartz.layout.ts', dest: 'quartz.layout.ts' }
  ];

  for (const { src, dest } of configFiles) {
    const srcPath = join(SITE_DIR, src);
    const destPath = join(QUARTZ_DIR, dest);
    
    if (existsSync(srcPath)) {
      // Backup original if it exists
      if (existsSync(destPath) && !existsSync(`${destPath}.original`)) {
        copyFileSync(destPath, `${destPath}.original`);
        console.log(chalk.gray(`  Backed up original ${dest}`));
      }
      
      copyFileSync(srcPath, destPath);
      console.log(chalk.green(`  ✓ Copied ${src} to quartz/${dest}`));
    } else {
      console.log(chalk.yellow(`  ⚠️  ${src} not found, skipping`));
    }
  }

  // Copy custom plugins directory if it exists
  const pluginsPath = join(SITE_DIR, 'plugins');
  if (existsSync(pluginsPath)) {
    const destPluginsPath = join(QUARTZ_DIR, 'plugins');
    
    // Remove existing plugins directory if it exists
    if (existsSync(destPluginsPath)) {
      rmSync(destPluginsPath, { recursive: true, force: true });
    }
    
    // Copy the plugins directory
    run(`cp -r "${pluginsPath}" "${destPluginsPath}"`);
    console.log(chalk.green('  ✓ Copied custom plugins directory'));
  }

  // Create symlink to content directory
  const quartzContentPath = join(QUARTZ_DIR, 'content');
  
  if (existsSync(quartzContentPath)) {
    if (!existsSync(join(quartzContentPath, '.gitkeep'))) {
      // It's not the default empty content dir, back it up
      if (!existsSync(`${quartzContentPath}.backup`)) {
        console.log(chalk.gray('  Backing up existing content directory...'));
        run(`mv content content.backup`, { cwd: QUARTZ_DIR });
      } else {
        rmSync(quartzContentPath, { recursive: true, force: true });
      }
    } else {
      rmSync(quartzContentPath, { recursive: true, force: true });
    }
  }

  console.log(chalk.blue('🔗 Linking to Synapse content directory...'));
  symlinkSync('../../../content', quartzContentPath);
  console.log(chalk.green('  ✓ Created symlink: quartz/content -> ../../content'));

  // Add custom styles if they exist
  const customStylesPath = join(SITE_DIR, 'custom.scss');
  if (existsSync(customStylesPath)) {
    const quartzStylesDir = join(QUARTZ_DIR, 'quartz', 'styles');
    const destStylesPath = join(quartzStylesDir, 'custom.scss');
    
    if (!existsSync(destStylesPath)) {
      copyFileSync(customStylesPath, destStylesPath);
      console.log(chalk.green('  ✓ Copied custom styles'));
    }
  }

  console.log(chalk.green('\n✅ Quartz setup complete!\n'));
  
  console.log(chalk.cyan('Available commands (run from site/quartz):'));
  console.log('  npx quartz build       - Build the static site');
  console.log('  npx quartz build --serve - Serve with hot reload');
  console.log('  npm run build          - Alternative build command');
  console.log('  npm run serve          - Alternative serve command\n');
  
  console.log(chalk.cyan('To start the development server:'));
  console.log(chalk.white('  cd site/quartz && npx quartz build --serve'));
}

// Run the setup
if (import.meta.filename === process.argv[1]) {
  setupQuartzSubmodule();
}