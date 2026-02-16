#!/usr/bin/env tsx

import { execSync } from 'child_process';
import { existsSync, copyFileSync, lstatSync, unlinkSync, rmSync } from 'fs';
import { join, resolve } from 'path';

/**
 * Lightweight sync script for plugins, config, and content
 * Ensures all assets are up-to-date before each build
 */

const SITE_DIR = resolve(import.meta.dirname);
const PROJECT_ROOT = resolve(SITE_DIR, '../..');
const PLUGINS_DIR = join(SITE_DIR, 'plugins');
const QUARTZ_DIR = join(SITE_DIR, 'quartz');
const QUARTZ_PLUGINS_DIR = join(QUARTZ_DIR, 'plugins');
const QUARTZ_CONTENT_DIR = join(QUARTZ_DIR, 'content');
const QUARTZ_PUBLIC_DIR = join(QUARTZ_DIR, 'public');
const CONTENT_DIR = join(PROJECT_ROOT, 'content');
const STATIC_EDIT_DIR = join(SITE_DIR, 'static/edit');
const CONFIG_FILE = 'quartz.config.ts';

// Only sync if quartz directory exists
if (existsSync(QUARTZ_DIR)) {
  let synced = [];

  // Sync plugins directory
  if (existsSync(PLUGINS_DIR)) {
    try {
      // Use rsync for efficient syncing (only copies changed files)
      execSync(`rsync -a --delete "${PLUGINS_DIR}/" "${QUARTZ_PLUGINS_DIR}/"`, {
        stdio: 'pipe'
      });
      synced.push('plugins');
    } catch (error) {
      // Fallback to cp if rsync isn't available
      try {
        execSync(`rm -rf "${QUARTZ_PLUGINS_DIR}" && cp -r "${PLUGINS_DIR}" "${QUARTZ_PLUGINS_DIR}"`, {
          stdio: 'pipe'
        });
        synced.push('plugins');
      } catch (cpError) {
        console.error('Warning: Could not sync plugins directory');
      }
    }
  }

  // Sync config file
  const sourceConfig = join(SITE_DIR, CONFIG_FILE);
  const destConfig = join(QUARTZ_DIR, CONFIG_FILE);

  if (existsSync(sourceConfig)) {
    try {
      copyFileSync(sourceConfig, destConfig);
      synced.push('config');
    } catch (error) {
      console.error('Warning: Could not sync config file');
    }
  }

  // Sync content directory (remove symlink if exists, then rsync)
  if (existsSync(CONTENT_DIR)) {
    try {
      // Remove symlink if it exists
      if (existsSync(QUARTZ_CONTENT_DIR)) {
        const stats = lstatSync(QUARTZ_CONTENT_DIR);
        if (stats.isSymbolicLink()) {
          unlinkSync(QUARTZ_CONTENT_DIR);
        }
      }

      // Use rsync for efficient syncing
      execSync(`rsync -a --delete "${CONTENT_DIR}/" "${QUARTZ_CONTENT_DIR}/"`, {
        stdio: 'pipe'
      });
      synced.push('content');
    } catch (error) {
      // Fallback to cp if rsync isn't available
      try {
        if (existsSync(QUARTZ_CONTENT_DIR)) {
          rmSync(QUARTZ_CONTENT_DIR, { recursive: true, force: true });
        }
        execSync(`cp -r "${CONTENT_DIR}" "${QUARTZ_CONTENT_DIR}"`, {
          stdio: 'pipe'
        });
        synced.push('content');
      } catch (cpError) {
        console.error('Warning: Could not sync content directory');
      }
    }
  }

  // Sync edit directory to public (for Decap CMS)
  if (existsSync(STATIC_EDIT_DIR)) {
    const editOutputDir = join(QUARTZ_PUBLIC_DIR, 'edit');
    try {
      // Ensure public directory exists
      if (!existsSync(QUARTZ_PUBLIC_DIR)) {
        execSync(`mkdir -p "${QUARTZ_PUBLIC_DIR}"`, { stdio: 'pipe' });
      }

      // Use rsync for efficient syncing
      execSync(`rsync -a --delete "${STATIC_EDIT_DIR}/" "${editOutputDir}/"`, {
        stdio: 'pipe'
      });
      synced.push('edit');
    } catch (error) {
      // Fallback to cp if rsync isn't available
      try {
        if (existsSync(editOutputDir)) {
          rmSync(editOutputDir, { recursive: true, force: true });
        }
        execSync(`cp -r "${STATIC_EDIT_DIR}" "${editOutputDir}"`, {
          stdio: 'pipe'
        });
        synced.push('edit');
      } catch (cpError) {
        console.error('Warning: Could not sync edit directory');
      }
    }
  }

  if (synced.length > 0) {
    console.log(`✓ Synced: ${synced.join(', ')}`);
  }
}
