#!/usr/bin/env node

import { ContextMCPServer } from './server.js';

/**
 * Entry point for Context MCP Server
 *
 * Uses Continue's FTS5 search and tree-sitter for fast, accurate code analysis.
 *
 * Environment Variables:
 * - WORKSPACE_DIRS: Comma-separated list of directories to index (e.g., "/path/to/repoA,/path/to/synapse")
 * - WORKSPACE_DIR: Single directory (legacy, used if WORKSPACE_DIRS not set)
 *
 * Falls back to process.cwd() if neither is set.
 */

function parseWorkspaceDirs(): string[] {
  // Check for multi-directory config first
  const workspaceDirs = process.env.WORKSPACE_DIRS;
  if (workspaceDirs) {
    return workspaceDirs
      .split(',')
      .map(dir => dir.trim())
      .filter(dir => dir.length > 0);
  }

  // Fall back to single directory (legacy)
  const workspaceDir = process.env.WORKSPACE_DIR || process.cwd();
  return [workspaceDir];
}

async function main() {
  const workspaceDirs = parseWorkspaceDirs();

  console.error(`Starting Context MCP Server for ${workspaceDirs.length} workspace(s):`);
  workspaceDirs.forEach(dir => console.error(`  - ${dir}`));
  console.error('Features: FTS5 search (BM25), Tree-sitter code structure');

  try {
    const server = new ContextMCPServer(workspaceDirs);

    // Handle cleanup on exit
    process.on('SIGINT', () => {
      console.error('Shutting down...');
      server.dispose();
      process.exit(0);
    });

    process.on('SIGTERM', () => {
      console.error('Shutting down...');
      server.dispose();
      process.exit(0);
    });

    await server.run();
  } catch (error) {
    console.error('Fatal error:', error);
    process.exit(1);
  }
}

main();
