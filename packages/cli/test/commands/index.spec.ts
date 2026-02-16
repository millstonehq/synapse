import { describe, it, expect, beforeEach, afterEach } from '@jest/globals';
import fsExtra from 'fs-extra';
const fs = fsExtra;
import * as path from 'path';
import { index, indexCommand } from '../../src/commands/index';

describe('index command', () => {
  const testDir = path.join(process.cwd(), 'test-index-command');
  const contentDir = path.join(testDir, 'content');
  const originalCwd = process.cwd();

  afterAll(() => {
    try {
      process.chdir(originalCwd);
    } catch {}
  });

  beforeEach(async () => {
    // Create test directory structure
    await fs.ensureDir(contentDir);
  });

  afterEach(async () => {
    await fs.remove(testDir);
  });

  describe('index function', () => {
    it('should generate homepage with default output path', async () => {
      // Create some test documents
      await fs.ensureDir(path.join(contentDir, '10_Policies'));
      await fs.writeFile(path.join(contentDir, '10_Policies', 'policy1.md'), '# Policy 1');
      await fs.writeFile(path.join(contentDir, '10_Policies', 'policy2.md'), '# Policy 2');

      await fs.ensureDir(path.join(contentDir, '20_Standards'));
      await fs.writeFile(path.join(contentDir, '20_Standards', 'standard1.md'), '# Standard 1');

      // Create empty directories for other required types
      await fs.ensureDir(path.join(contentDir, '30_Processes'));
      await fs.ensureDir(path.join(contentDir, '40_SOPs'));
      await fs.ensureDir(path.join(contentDir, '50_Runbooks'));
      await fs.ensureDir(path.join(contentDir, '70_Systems'));
      await fs.ensureDir(path.join(contentDir, '90_Architecture', 'ADRs'));
      await fs.ensureDir(path.join(contentDir, '90_Architecture', 'TDDs'));
      await fs.ensureDir(path.join(contentDir, '100_Products', 'PRDs'));
      await fs.ensureDir(path.join(contentDir, '110_Capabilities'));

      await index({ contentDir });

      // Check that index.md was created in the content directory
      const indexPath = path.join(contentDir, 'index.md');
      expect(await fs.pathExists(indexPath)).toBe(true);

      const content = await fs.readFile(indexPath, 'utf-8');
      expect(content).toContain('# Synapse Documentation Framework');
      expect(content).toContain('- **Policies** (2):');
      expect(content).toContain('- **Standards** (1):')
    });

    it('should use custom output path when specified', async () => {
      // Create minimal structure
      await fs.ensureDir(path.join(contentDir, '10_Policies'));
      await fs.ensureDir(path.join(contentDir, '20_Standards'));
      await fs.ensureDir(path.join(contentDir, '30_Processes'));
      await fs.ensureDir(path.join(contentDir, '40_SOPs'));
      await fs.ensureDir(path.join(contentDir, '50_Runbooks'));
      await fs.ensureDir(path.join(contentDir, '70_Systems'));
      await fs.ensureDir(path.join(contentDir, '90_Architecture', 'ADRs'));
      await fs.ensureDir(path.join(contentDir, '90_Architecture', 'TDDs'));
      await fs.ensureDir(path.join(contentDir, '100_Products', 'PRDs'));
      await fs.ensureDir(path.join(contentDir, '110_Capabilities'));

      const customOutput = path.join(testDir, 'custom-index.md');
      await index({
        contentDir,
        output: customOutput
      });

      // Check that custom path was used
      expect(await fs.pathExists(customOutput)).toBe(true);

      // Default path should not exist
      const defaultPath = path.join(contentDir, 'index.md');
      expect(await fs.pathExists(defaultPath)).toBe(false);

      const content = await fs.readFile(customOutput, 'utf-8');
      expect(content).toContain('# Synapse Documentation Framework');
    });

    it('should generate correct navigation links for all document types', async () => {
      // Create documents in various folders
      await fs.ensureDir(path.join(contentDir, '10_Policies'));
      await fs.writeFile(path.join(contentDir, '10_Policies', 'p1.md'), '# P1');

      await fs.ensureDir(path.join(contentDir, '90_Architecture', 'ADRs'));
      await fs.writeFile(path.join(contentDir, '90_Architecture', 'ADRs', 'adr1.md'), '# ADR1');

      await fs.ensureDir(path.join(contentDir, '90_Architecture', 'TDDs'));
      await fs.writeFile(path.join(contentDir, '90_Architecture', 'TDDs', 'tdd1.md'), '# TDD1');

      await fs.ensureDir(path.join(contentDir, '100_Products', 'PRDs'));
      await fs.writeFile(path.join(contentDir, '100_Products', 'PRDs', 'prd1.md'), '# PRD1');

      // Create empty directories for other required types
      await fs.ensureDir(path.join(contentDir, '20_Standards'));
      await fs.ensureDir(path.join(contentDir, '30_Processes'));
      await fs.ensureDir(path.join(contentDir, '40_SOPs'));
      await fs.ensureDir(path.join(contentDir, '50_Runbooks'));
      await fs.ensureDir(path.join(contentDir, '60_Systems'));
      await fs.ensureDir(path.join(contentDir, '90_Capabilities'));

      await index({ contentDir });

      const content = await fs.readFile(path.join(contentDir, 'index.md'), 'utf-8');

      // Check navigation links in new format
      expect(content).toContain('[[content/10_Policies]]');
      expect(content).toContain('[[content/20_Standards]]');
      expect(content).toContain('[[content/30_Processes]]');
      expect(content).toContain('[[content/40_SOPs]]');
      expect(content).toContain('[[content/50_Runbooks]]');
      expect(content).toContain('[[content/70_Systems]]');
      expect(content).toContain('[[content/90_Architecture/ADRs]]');
      expect(content).toContain('[[content/90_Architecture/TDDs]]');
      expect(content).toContain('[[content/100_Products/PRDs]]');
      expect(content).toContain('[[content/110_Capabilities]]');
    });

    it('should include correct frontmatter', async () => {
      // Create minimal structure
      await fs.ensureDir(path.join(contentDir, '10_Policies'));
      await fs.ensureDir(path.join(contentDir, '20_Standards'));
      await fs.ensureDir(path.join(contentDir, '30_Processes'));
      await fs.ensureDir(path.join(contentDir, '40_SOPs'));
      await fs.ensureDir(path.join(contentDir, '50_Runbooks'));
      await fs.ensureDir(path.join(contentDir, '70_Systems'));
      await fs.ensureDir(path.join(contentDir, '90_Architecture', 'ADRs'));
      await fs.ensureDir(path.join(contentDir, '90_Architecture', 'TDDs'));
      await fs.ensureDir(path.join(contentDir, '100_Products', 'PRDs'));
      await fs.ensureDir(path.join(contentDir, '110_Capabilities'));

      await index({ contentDir });

      const content = await fs.readFile(path.join(contentDir, 'index.md'), 'utf-8');

      // Check title and content
      expect(content).toContain('# Synapse Documentation Framework');
      expect(content).toContain('Welcome to your centralized documentation hub');
    });

    it('should include timestamp', async () => {
      // Create minimal structure
      await fs.ensureDir(path.join(contentDir, '10_Policies'));
      await fs.ensureDir(path.join(contentDir, '20_Standards'));
      await fs.ensureDir(path.join(contentDir, '30_Processes'));
      await fs.ensureDir(path.join(contentDir, '40_SOPs'));
      await fs.ensureDir(path.join(contentDir, '50_Runbooks'));
      await fs.ensureDir(path.join(contentDir, '70_Systems'));
      await fs.ensureDir(path.join(contentDir, '90_Architecture', 'ADRs'));
      await fs.ensureDir(path.join(contentDir, '90_Architecture', 'TDDs'));
      await fs.ensureDir(path.join(contentDir, '100_Products', 'PRDs'));
      await fs.ensureDir(path.join(contentDir, '110_Capabilities'));

      await index({ contentDir });

      const content = await fs.readFile(path.join(contentDir, 'index.md'), 'utf-8');

      // Check for timestamp in expected format
      expect(content).toMatch(/Last updated: \d{4}-\d{2}-\d{2}/)
    });
  });

  describe('indexCommand', () => {
    it('should handle command line arguments', async () => {
      // Create minimal structure
      await fs.ensureDir(path.join(contentDir, '10_Policies'));
      await fs.ensureDir(path.join(contentDir, '20_Standards'));
      await fs.ensureDir(path.join(contentDir, '30_Processes'));
      await fs.ensureDir(path.join(contentDir, '40_SOPs'));
      await fs.ensureDir(path.join(contentDir, '50_Runbooks'));
      await fs.ensureDir(path.join(contentDir, '70_Systems'));
      await fs.ensureDir(path.join(contentDir, '90_Architecture', 'ADRs'));
      await fs.ensureDir(path.join(contentDir, '90_Architecture', 'TDDs'));
      await fs.ensureDir(path.join(contentDir, '100_Products', 'PRDs'));
      await fs.ensureDir(path.join(contentDir, '110_Capabilities'));

      // Call with custom directory
      await indexCommand({ dir: contentDir });

      const indexPath = path.join(contentDir, 'index.md');
      expect(await fs.pathExists(indexPath)).toBe(true);

      const content = await fs.readFile(indexPath, 'utf-8');
      expect(content).toContain('# Synapse Documentation Framework');
    });

    it('should handle command with output option', async () => {
      // Create minimal structure
      await fs.ensureDir(path.join(contentDir, '10_Policies'));
      await fs.ensureDir(path.join(contentDir, '20_Standards'));
      await fs.ensureDir(path.join(contentDir, '30_Processes'));
      await fs.ensureDir(path.join(contentDir, '40_SOPs'));
      await fs.ensureDir(path.join(contentDir, '50_Runbooks'));
      await fs.ensureDir(path.join(contentDir, '70_Systems'));
      await fs.ensureDir(path.join(contentDir, '90_Architecture', 'ADRs'));
      await fs.ensureDir(path.join(contentDir, '90_Architecture', 'TDDs'));
      await fs.ensureDir(path.join(contentDir, '100_Products', 'PRDs'));
      await fs.ensureDir(path.join(contentDir, '110_Capabilities'));

      const customOutput = path.join(testDir, 'command-output.md');

      // Call with both dir and output options
      await indexCommand({
        dir: contentDir,
        output: customOutput
      });

      expect(await fs.pathExists(customOutput)).toBe(true);

      const content = await fs.readFile(customOutput, 'utf-8');
      expect(content).toContain('# Synapse Documentation Framework');
    });

    it('should use current directory when dir not specified', async () => {
      const originalCwd = process.cwd();

      try {
        // Create a test content directory in a temporary location
        const tempTestDir = path.join(testDir, 'temp-cwd');
        await fs.ensureDir(tempTestDir);

        // Change to temp directory
        process.chdir(tempTestDir);

        // Create content structure in current directory
        const localContentDir = path.join(tempTestDir, 'content');
        await fs.ensureDir(path.join(localContentDir, '10_Policies'));
        await fs.ensureDir(path.join(localContentDir, '20_Standards'));
        await fs.ensureDir(path.join(localContentDir, '30_Processes'));
        await fs.ensureDir(path.join(localContentDir, '40_SOPs'));
        await fs.ensureDir(path.join(localContentDir, '50_Runbooks'));
        await fs.ensureDir(path.join(localContentDir, '60_Systems'));
        await fs.ensureDir(path.join(localContentDir, '70_Architecture', 'ADRs'));
        await fs.ensureDir(path.join(localContentDir, '70_Architecture', 'TDDs'));
        await fs.ensureDir(path.join(localContentDir, '80_Products', 'PRDs'));
        await fs.ensureDir(path.join(localContentDir, '90_Capabilities'));

        await fs.writeFile(path.join(localContentDir, '10_Policies', 'test.md'), '# Test');

        // Call without dir argument - should use current directory
        await indexCommand({});

        const indexPath = path.join(localContentDir, 'index.md');
        expect(await fs.pathExists(indexPath)).toBe(true);

        const content = await fs.readFile(indexPath, 'utf-8');
        expect(content).toContain('# Synapse Documentation Framework');
        expect(content).toContain('- **Policies** (1):');
      } finally {
        // Restore original directory
        process.chdir(originalCwd);
      }
    });
  });
});
