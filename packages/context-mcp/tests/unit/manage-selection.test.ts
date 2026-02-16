import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { SelectionManager } from '../../src/selection/SelectionManager.js';
import { manageSelectionTool } from '../../src/tools/manage-selection.js';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as os from 'os';

describe('manage-selection', () => {
  let manager: SelectionManager;
  let testDir: string;
  let testFiles: { [key: string]: string };

  beforeEach(async () => {
    // Create a temporary directory for test files
    testDir = await fs.mkdtemp(path.join(os.tmpdir(), 'manage-selection-test-'));

    // Create test files
    testFiles = {
      'file1.ts': path.join(testDir, 'file1.ts'),
      'file2.ts': path.join(testDir, 'file2.ts'),
      'file3.ts': path.join(testDir, 'file3.ts'),
    };

    await fs.writeFile(
      testFiles['file1.ts'],
      `// File 1
function first() {
  console.log('first');
}

function second() {
  console.log('second');
}

function third() {
  console.log('third');
}
`
    );

    await fs.writeFile(
      testFiles['file2.ts'],
      `// File 2
function alpha() {
  console.log('alpha');
}

function beta() {
  console.log('beta');
}
`
    );

    await fs.writeFile(
      testFiles['file3.ts'],
      `// File 3
function gamma() {
  console.log('gamma');
}
`
    );

    manager = new SelectionManager(testDir);
  });

  afterEach(async () => {
    // Clean up
    manager.dispose();
    await fs.rm(testDir, { recursive: true, force: true });
  });

  describe('op="add" with slices', () => {
    it('should add slices from a single file', async () => {
      const result = await manageSelectionTool(
        {
          op: 'add',
          slices: [
            {
              path: testFiles['file1.ts'],
              ranges: [{ startLine: 1, endLine: 4, description: 'first function' }],
            },
          ],
        },
        manager
      );

      expect(result.error).toBeUndefined();
      expect(result.totalFiles).toBe(1);
      const summary = await manager.getSummary();
      expect(summary.files).toHaveLength(1);
      expect(summary.files[0].mode).toBe('slices');
      expect(summary.files[0].slices).toHaveLength(1);
    });

    it('should add slices from multiple files incrementally', async () => {
      // Add first file
      await manageSelectionTool(
        {
          op: 'add',
          slices: [
            {
              path: testFiles['file1.ts'],
              ranges: [{ startLine: 1, endLine: 4, description: 'first function' }],
            },
          ],
        },
        manager
      );

      // Add second file
      const result = await manageSelectionTool(
        {
          op: 'add',
          slices: [
            {
              path: testFiles['file2.ts'],
              ranges: [{ startLine: 1, endLine: 4, description: 'alpha function' }],
            },
          ],
        },
        manager
      );

      expect(result.error).toBeUndefined();
      expect(result.totalFiles).toBe(2);
      const summary = await manager.getSummary();
      expect(summary.files).toHaveLength(2);
    });

    it('should append ranges to existing file slices', async () => {
      // Add first range
      await manageSelectionTool(
        {
          op: 'add',
          slices: [
            {
              path: testFiles['file1.ts'],
              ranges: [{ startLine: 1, endLine: 4, description: 'first function' }],
            },
          ],
        },
        manager
      );

      // Add second range to same file
      const result = await manageSelectionTool(
        {
          op: 'add',
          slices: [
            {
              path: testFiles['file1.ts'],
              ranges: [{ startLine: 6, endLine: 9, description: 'second function' }],
            },
          ],
        },
        manager
      );

      expect(result.error).toBeUndefined();
      expect(result.totalFiles).toBe(1);
      const summary = await manager.getSummary();
      expect(summary.files[0].slices).toHaveLength(2);
      expect(summary.files[0].slices?.[0].description).toBe('first function');
      expect(summary.files[0].slices?.[1].description).toBe('second function');
    });

    it('should work with multiple ranges in a single call', async () => {
      const result = await manageSelectionTool(
        {
          op: 'add',
          slices: [
            {
              path: testFiles['file1.ts'],
              ranges: [
                { startLine: 1, endLine: 4, description: 'first function' },
                { startLine: 6, endLine: 9, description: 'second function' },
              ],
            },
          ],
        },
        manager
      );

      expect(result.error).toBeUndefined();
      const summary = await manager.getSummary();
      expect(summary.files[0].slices).toHaveLength(2);
    });
  });

  describe('op="add" with paths', () => {
    it('should add full files', async () => {
      const result = await manageSelectionTool(
        {
          op: 'add',
          paths: [testFiles['file1.ts']],
        },
        manager
      );

      expect(result.error).toBeUndefined();
      expect(result.totalFiles).toBe(1);
      const summary = await manager.getSummary();
      expect(summary.files[0].mode).toBe('full');
    });

    it('should add multiple full files incrementally', async () => {
      await manageSelectionTool({ op: 'add', paths: [testFiles['file1.ts']] }, manager);
      const result = await manageSelectionTool({ op: 'add', paths: [testFiles['file2.ts']] }, manager);

      expect(result.error).toBeUndefined();
      expect(result.totalFiles).toBe(2);
    });
  });

  describe('op="set" with slices', () => {
    it('should replace entire selection with new slices', async () => {
      // Add some files first
      await manageSelectionTool({ op: 'add', paths: [testFiles['file1.ts']] }, manager);

      // Replace with slices
      const result = await manageSelectionTool(
        {
          op: 'set',
          slices: [
            {
              path: testFiles['file2.ts'],
              ranges: [{ startLine: 1, endLine: 4, description: 'alpha function' }],
            },
          ],
        },
        manager
      );

      expect(result.error).toBeUndefined();
      expect(result.totalFiles).toBe(1);
      const summary = await manager.getSummary();
      expect(summary.files[0].path).toBe(testFiles['file2.ts']);
      expect(summary.files[0].mode).toBe('slices');
    });

    it('should handle multiple files with slices in one call', async () => {
      const result = await manageSelectionTool(
        {
          op: 'set',
          slices: [
            {
              path: testFiles['file1.ts'],
              ranges: [{ startLine: 1, endLine: 4, description: 'first function' }],
            },
            {
              path: testFiles['file2.ts'],
              ranges: [{ startLine: 1, endLine: 4, description: 'alpha function' }],
            },
          ],
        },
        manager
      );

      expect(result.error).toBeUndefined();
      expect(result.totalFiles).toBe(2);
    });
  });

  describe('error handling', () => {
    it('should return error for invalid operation', async () => {
      const result = await manageSelectionTool(
        {
          op: 'invalid_op' as any,
          slices: [
            {
              path: testFiles['file1.ts'],
              ranges: [{ startLine: 1, endLine: 4 }],
            },
          ],
        },
        manager
      );

      expect(result.error).toBeDefined();
      expect(result.error).toContain('Invalid operation');
    });

    it('should return error when add operation has no paths or slices', async () => {
      const result = await manageSelectionTool(
        {
          op: 'add',
        },
        manager
      );

      expect(result.error).toBeDefined();
      expect(result.error).toContain('requires either');
    });
  });

  describe('clear operation', () => {
    it('should clear all selections', async () => {
      await manageSelectionTool(
        {
          op: 'add',
          slices: [
            {
              path: testFiles['file1.ts'],
              ranges: [{ startLine: 1, endLine: 4 }],
            },
          ],
        },
        manager
      );

      const result = await manageSelectionTool({ op: 'clear' }, manager);
      expect(result.error).toBeUndefined();
      expect(result.totalFiles).toBe(0);
    });
  });

  describe('get operation', () => {
    it('should return current selection', async () => {
      await manageSelectionTool(
        {
          op: 'add',
          slices: [
            {
              path: testFiles['file1.ts'],
              ranges: [{ startLine: 1, endLine: 4, description: 'test' }],
            },
          ],
        },
        manager
      );

      const result = await manageSelectionTool({ op: 'get' }, manager);
      expect(result.error).toBeUndefined();
      expect(result.totalFiles).toBe(1);
      expect(result.files?.[0].slices).toHaveLength(1);
    });
  });
});
