/**
 * E2E Test for file_search tool
 *
 * Creates a fresh test directory with known content, indexes it,
 * and validates that searches return expected document content.
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { fileSearchTool } from '../../src/tools/file-search.js';
import { ContinueIDE } from '../../src/continue/ContinueIDE.js';
import * as path from 'node:path';
import * as fs from 'node:fs/promises';
import * as os from 'node:os';

describe('file_search e2e', () => {
  let testDir: string;
  let ide: ContinueIDE;

  // Known content for validation
  const testFiles = {
    'src/authentication.ts': `
/**
 * Authentication module for user management
 * Handles JWT token validation and session management
 */

export interface User {
  id: string;
  email: string;
  displayName: string;
}

export class AuthenticationService {
  private readonly secretKey: string;

  constructor(secretKey: string) {
    this.secretKey = secretKey;
  }

  async validateToken(token: string): Promise<User | null> {
    // Token validation logic here
    if (!token) return null;
    return { id: '1', email: 'test@example.com', displayName: 'Test User' };
  }

  async createSession(user: User): Promise<string> {
    // Create JWT session token
    return 'session-token-' + user.id;
  }
}

export const DEFAULT_SESSION_TIMEOUT = 3600;
`.trim(),

    'src/database.ts': `
/**
 * Database connection and query utilities
 * Supports PostgreSQL and SQLite backends
 */

export interface DatabaseConfig {
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
}

export class DatabaseConnection {
  private config: DatabaseConfig;
  private connected = false;

  constructor(config: DatabaseConfig) {
    this.config = config;
  }

  async connect(): Promise<void> {
    console.log('Connecting to database:', this.config.host);
    this.connected = true;
  }

  async query<T>(sql: string, params?: unknown[]): Promise<T[]> {
    if (!this.connected) {
      throw new Error('Not connected to database');
    }
    // Execute query
    return [] as T[];
  }

  async disconnect(): Promise<void> {
    this.connected = false;
  }
}
`.trim(),

    'src/utils/string-helpers.ts': `
/**
 * String manipulation utilities
 * Common functions for text processing
 */

export function capitalizeFirst(text: string): string {
  if (!text) return '';
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

export function truncateWithEllipsis(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}

// Unique identifier for testing: XYZZY_MAGIC_MARKER_12345
export const MAGIC_CONSTANT = 'XYZZY_MAGIC_MARKER_12345';
`.trim(),

    'README.md': `
# Test Project

This is a test project for validating the file_search tool.

## Features

- Authentication with JWT tokens
- Database connectivity
- String utility functions

## Installation

\`\`\`bash
npm install
npm run build
\`\`\`

## Usage

See the documentation for more details.
`.trim(),
  };

  beforeAll(async () => {
    // Create a unique test directory
    testDir = path.join(os.tmpdir(), `file-search-e2e-${Date.now()}`);
    await fs.mkdir(testDir, { recursive: true });

    // Write all test files
    for (const [relativePath, content] of Object.entries(testFiles)) {
      const fullPath = path.join(testDir, relativePath);
      await fs.mkdir(path.dirname(fullPath), { recursive: true });
      await fs.writeFile(fullPath, content, 'utf-8');
    }

    // Initialize IDE for the test directory
    ide = new ContinueIDE(testDir);
  }, 30000);

  afterAll(async () => {
    // Clean up test directory
    await fs.rm(testDir, { recursive: true, force: true }).catch(() => {});
  });

  it('indexes and finds a unique identifier in document content', async () => {
    // Search for the magic marker that only exists in one file
    const result = await fileSearchTool(
      {
        pattern: 'XYZZY_MAGIC_MARKER_12345',
        mode: 'content',
        include_content: true,
        max_results: 10,
      },
      testDir,
      ide
    );

    // Must find results
    expect(result.count).toBeGreaterThan(0);
    expect(result.performance?.method).toContain('FTS5');

    // Must find the specific file
    const match = result.results.find(r =>
      r.path.includes('string-helpers.ts')
    );
    expect(match).toBeDefined();
    expect(match?.type).toBe('content');
    expect(match?.line_range).toBeDefined();

    // Must include the content with our marker
    expect(match?.content).toContain('XYZZY_MAGIC_MARKER_12345');
  }, 60000);

  it('finds class definitions by name', async () => {
    const result = await fileSearchTool(
      {
        pattern: 'AuthenticationService',
        mode: 'content',
        include_content: true,
        max_results: 10,
      },
      testDir,
      ide
    );

    expect(result.count).toBeGreaterThan(0);

    // Should find the class in authentication.ts
    const match = result.results.find(r =>
      r.path.includes('authentication.ts')
    );
    expect(match).toBeDefined();
    expect(match?.content).toContain('class AuthenticationService');
  }, 60000);

  it('finds function definitions by name', async () => {
    const result = await fileSearchTool(
      {
        pattern: 'truncateWithEllipsis',
        mode: 'content',
        include_content: true,
        max_results: 10,
      },
      testDir,
      ide
    );

    expect(result.count).toBeGreaterThan(0);

    const match = result.results.find(r =>
      r.path.includes('string-helpers.ts')
    );
    expect(match).toBeDefined();
    expect(match?.content).toContain('function truncateWithEllipsis');
  }, 60000);

  it('filters results by file extension', async () => {
    const result = await fileSearchTool(
      {
        pattern: 'export',
        mode: 'content',
        filter: {
          extensions: ['ts'],
        },
        max_results: 20,
      },
      testDir,
      ide
    );

    expect(result.count).toBeGreaterThan(0);

    // All results should be TypeScript files
    for (const r of result.results) {
      expect(r.path).toMatch(/\.ts$/);
    }

    // Should not include the README.md
    const hasReadme = result.results.some(r => r.path.includes('README'));
    expect(hasReadme).toBe(false);
  }, 60000);

  it('finds files by path pattern', async () => {
    const result = await fileSearchTool(
      {
        pattern: 'database',
        mode: 'path',
      },
      testDir,
      ide
    );

    expect(result.count).toBeGreaterThan(0);
    expect(result.results.some(r => r.path.includes('database.ts'))).toBe(true);
    expect(result.results.every(r => r.type === 'path')).toBe(true);
  }, 60000);

  it('returns accurate line ranges for matches', async () => {
    const result = await fileSearchTool(
      {
        pattern: 'DatabaseConnection',
        mode: 'content',
        include_content: true,
        max_results: 5,
      },
      testDir,
      ide
    );

    expect(result.count).toBeGreaterThan(0);

    const match = result.results.find(r => r.path.includes('database.ts'));
    expect(match).toBeDefined();
    expect(match?.line_range).toBeDefined();

    // Line range should be valid (0-indexed, start <= end)
    const [startLine, endLine] = match!.line_range!;
    expect(startLine).toBeGreaterThanOrEqual(0);
    expect(endLine).toBeGreaterThanOrEqual(startLine);
  }, 60000);

  it('finds interface definitions', async () => {
    const result = await fileSearchTool(
      {
        pattern: 'DatabaseConfig',
        mode: 'content',
        include_content: true,
        max_results: 10,
      },
      testDir,
      ide
    );

    expect(result.count).toBeGreaterThan(0);

    const match = result.results.find(r => r.path.includes('database.ts'));
    expect(match).toBeDefined();
    expect(match?.content).toContain('interface DatabaseConfig');
  }, 60000);

  it('excludes files matching exclude patterns', async () => {
    const result = await fileSearchTool(
      {
        pattern: 'export',
        mode: 'content',
        filter: {
          exclude: ['utils'],
        },
        max_results: 20,
      },
      testDir,
      ide
    );

    // Should find results in authentication.ts and database.ts
    expect(result.count).toBeGreaterThan(0);

    // Should not include files in utils/
    const hasUtils = result.results.some(r => r.path.includes('utils'));
    expect(hasUtils).toBe(false);
  }, 60000);

  it('handles multi-word searches', async () => {
    const result = await fileSearchTool(
      {
        pattern: 'session management',
        mode: 'content',
        include_content: true,
        max_results: 10,
      },
      testDir,
      ide
    );

    // FTS5 should find documents containing both words
    expect(result.performance?.method).toContain('FTS5');

    // The authentication.ts file has "session management" in the comments
    if (result.count > 0) {
      const match = result.results.find(r =>
        r.path.includes('authentication.ts')
      );
      expect(match).toBeDefined();
    }
  }, 60000);
});
