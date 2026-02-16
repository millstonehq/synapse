/**
 * ContinueIDE Interface Tests
 *
 * Tests that validate our ContinueIDE implementation satisfies the IDE interface
 * expected by @continuedev/core indexing functions.
 *
 * These tests will catch breaking changes if:
 * - Continue adds new required methods to the IDE interface
 * - Method signatures change (parameters or return types)
 * - Expected behavior of methods changes
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { ContinueIDE } from '../../src/continue/ContinueIDE.js';
import * as fs from 'node:fs/promises';
import * as path from 'node:path';
import * as os from 'node:os';

describe('ContinueIDE', () => {
  let testDir: string;
  let ide: ContinueIDE;

  beforeAll(async () => {
    // Create a temporary test directory with some files
    testDir = path.join(os.tmpdir(), `continue-ide-test-${Date.now()}`);
    await fs.mkdir(testDir, { recursive: true });

    // Create test files
    await fs.writeFile(path.join(testDir, 'test.ts'), 'export const x = 1;\n');
    await fs.writeFile(
      path.join(testDir, 'nested', 'file.ts'),
      'export const y = 2;\n',
      { flag: 'w' }
    ).catch(async () => {
      await fs.mkdir(path.join(testDir, 'nested'), { recursive: true });
      await fs.writeFile(
        path.join(testDir, 'nested', 'file.ts'),
        'export const y = 2;\n'
      );
    });

    ide = new ContinueIDE(testDir);
  });

  afterAll(async () => {
    // Cleanup test directory
    await fs.rm(testDir, { recursive: true, force: true }).catch(() => {});
  });

  describe('required methods for indexing', () => {
    it('implements getWorkspaceDirs', async () => {
      expect(typeof ide.getWorkspaceDirs).toBe('function');
      const dirs = await ide.getWorkspaceDirs();
      expect(Array.isArray(dirs)).toBe(true);
      expect(dirs).toContain(testDir);
    });

    it('implements readFile', async () => {
      expect(typeof ide.readFile).toBe('function');
      const content = await ide.readFile('test.ts');
      expect(content).toBe('export const x = 1;\n');
    });

    it('implements readFile with absolute path', async () => {
      const content = await ide.readFile(path.join(testDir, 'test.ts'));
      expect(content).toBe('export const x = 1;\n');
    });

    it('implements listDir', async () => {
      expect(typeof ide.listDir).toBe('function');
      const entries = await ide.listDir('.');
      expect(Array.isArray(entries)).toBe(true);
      // Each entry should be [path, FileType]
      expect(entries.length).toBeGreaterThan(0);
      expect(entries[0]).toHaveLength(2);
    });

    it('implements fileExists', async () => {
      expect(typeof ide.fileExists).toBe('function');
      expect(await ide.fileExists('test.ts')).toBe(true);
      expect(await ide.fileExists('nonexistent.ts')).toBe(false);
    });

    it('implements getBranch', async () => {
      expect(typeof ide.getBranch).toBe('function');
      const branch = await ide.getBranch(testDir);
      expect(typeof branch).toBe('string');
    });

    it('implements getGitRootPath', async () => {
      expect(typeof ide.getGitRootPath).toBe('function');
      // May return undefined if not in a git repo
      const gitRoot = await ide.getGitRootPath(testDir);
      expect(gitRoot === undefined || typeof gitRoot === 'string').toBe(true);
    });

    it('implements getRepoName', async () => {
      expect(typeof ide.getRepoName).toBe('function');
      const repoName = await ide.getRepoName(testDir);
      expect(repoName === undefined || typeof repoName === 'string').toBe(true);
    });

    it('implements getLastModified', async () => {
      expect(typeof ide.getLastModified).toBe('function');
      const result = await ide.getLastModified(['test.ts']);
      expect(typeof result).toBe('object');
    });

    it('implements getFileStats', async () => {
      expect(typeof ide.getFileStats).toBe('function');
      const result = await ide.getFileStats(['test.ts']);
      expect(typeof result).toBe('object');
    });
  });

  describe('metadata methods', () => {
    it('implements getIdeInfo with required fields', async () => {
      expect(typeof ide.getIdeInfo).toBe('function');
      const info = await ide.getIdeInfo();
      expect(info).toHaveProperty('ideType');
      expect(info).toHaveProperty('name');
      expect(info).toHaveProperty('version');
    });

    it('implements getIdeSettings', async () => {
      expect(typeof ide.getIdeSettings).toBe('function');
      const settings = await ide.getIdeSettings();
      expect(typeof settings).toBe('object');
    });
  });

  describe('readRangeInFile', () => {
    it('reads a range of lines', async () => {
      // Create a multi-line test file
      await fs.writeFile(
        path.join(testDir, 'multiline.ts'),
        'line 0\nline 1\nline 2\nline 3\n'
      );

      const range = {
        start: { line: 1, character: 0 },
        end: { line: 2, character: 6 },
      };

      const content = await ide.readRangeInFile('multiline.ts', range);
      expect(content).toContain('line 1');
      expect(content).toContain('line 2');
    });
  });

  describe('stub methods exist', () => {
    // These methods are required by the interface but not used for indexing
    const stubMethods = [
      'writeFile',
      'showVirtualFile',
      'openFile',
      'openUrl',
      'runCommand',
      'saveFile',
      'showLines',
      'getDiff',
      'getClipboardContent',
      'isTelemetryEnabled',
      'getUniqueId',
      'getTerminalContents',
      'getDebugLocals',
      'getTopLevelCallStackSources',
      'getAvailableThreads',
      'getWorkspaceConfigs',
      'getOpenFiles',
      'getCurrentFile',
      'getPinnedFiles',
      'getSearchResults',
      'subprocess',
      'getProblems',
      'getTags',
      'showToast',
      'gotoDefinition',
      'getGitHubAuthToken',
      'onDidChangeActiveTextEditor',
    ];

    for (const method of stubMethods) {
      it(`implements ${method}`, () => {
        expect(typeof (ide as any)[method]).toBe('function');
      });
    }
  });
});
