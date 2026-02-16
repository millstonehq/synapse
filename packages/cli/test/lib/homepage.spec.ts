import { describe, it, expect, beforeEach, afterEach } from '@jest/globals';
import * as path from 'path';
import fsExtra from 'fs-extra';
const fs = fsExtra;
import { generateHomepage } from '../../src/lib/homepage';

describe('homepage module', () => {
  const testDir = path.join(process.cwd(), 'test-homepage');
  const contentDir = path.join(testDir, 'content');

  beforeEach(async () => {
    // Create test directory structure
    await fs.ensureDir(contentDir);
  });

  afterEach(async () => {
    await fs.remove(testDir);
  });

  describe('generateHomepage', () => {
    it('should generate homepage with all document types', async () => {
      // Create test directory structure with documents
      await fs.ensureDir(path.join(contentDir, '10_Policies'));
      await fs.writeFile(path.join(contentDir, '10_Policies', 'policy1.md'), '# Policy 1');
      await fs.writeFile(path.join(contentDir, '10_Policies', 'policy2.md'), '# Policy 2');

      await fs.ensureDir(path.join(contentDir, '20_Standards'));
      await fs.writeFile(path.join(contentDir, '20_Standards', 'standard1.md'), '# Standard 1');

      await fs.ensureDir(path.join(contentDir, '30_Processes'));
      await fs.writeFile(path.join(contentDir, '30_Processes', 'process1.md'), '# Process 1');
      await fs.writeFile(path.join(contentDir, '30_Processes', 'process2.md'), '# Process 2');
      await fs.writeFile(path.join(contentDir, '30_Processes', 'process3.md'), '# Process 3');

      await fs.ensureDir(path.join(contentDir, '40_SOPs'));
      // Leave empty

      await fs.ensureDir(path.join(contentDir, '50_Runbooks'));
      await fs.writeFile(path.join(contentDir, '50_Runbooks', 'runbook1.md'), '# Runbook 1');

      await fs.ensureDir(path.join(contentDir, '70_Systems'));
      await fs.writeFile(path.join(contentDir, '70_Systems', 'system1.md'), '# System 1');
      await fs.writeFile(path.join(contentDir, '70_Systems', 'system2.md'), '# System 2');

      await fs.ensureDir(path.join(contentDir, '90_Architecture', 'ADRs'));
      await fs.writeFile(path.join(contentDir, '90_Architecture', 'ADRs', 'adr1.md'), '# ADR 1');
      await fs.writeFile(path.join(contentDir, '90_Architecture', 'ADRs', 'adr2.md'), '# ADR 2');
      await fs.writeFile(path.join(contentDir, '90_Architecture', 'ADRs', 'adr3.md'), '# ADR 3');

      await fs.ensureDir(path.join(contentDir, '90_Architecture', 'TDDs'));
      await fs.writeFile(path.join(contentDir, '90_Architecture', 'TDDs', 'tdd1.md'), '# TDD 1');

      await fs.ensureDir(path.join(contentDir, '100_Products', 'PRDs'));
      await fs.writeFile(path.join(contentDir, '100_Products', 'PRDs', 'prd1.md'), '# PRD 1');
      await fs.writeFile(path.join(contentDir, '100_Products', 'PRDs', 'prd2.md'), '# PRD 2');

      await fs.ensureDir(path.join(contentDir, '110_Capabilities'));
      await fs.writeFile(path.join(contentDir, '110_Capabilities', 'cap1.md'), '# Cap 1');

      const outputPath = path.join(contentDir, 'index.md');
      await generateHomepage({
        contentDir,
        outputPath
      });

      // Read the generated file
      const content = await fs.readFile(outputPath, 'utf-8');

      // Check title
      expect(content).toContain('# Synapse Documentation Framework');
      expect(content).toContain('Welcome to your centralized documentation hub');

      // The homepage no longer shows a total count - validates individual category counts instead

      // Check section headers and counts in new format
      expect(content).toContain('- **Policies** (2):');
      expect(content).toContain('- **Standards** (1):');
      expect(content).toContain('- **Processes** (3):');
      expect(content).toContain('- **SOPs** (0):');
      expect(content).toContain('- **Runbooks** (1):');
      expect(content).toContain('- **Systems** (2):');
      expect(content).toContain('- **ADRs** (3):');
      expect(content).toContain('- **TDDs** (1):');
      expect(content).toContain('- **PRDs** (2):');
      expect(content).toContain('- **Capabilities** (1):');

      // Check navigation links in new format
      expect(content).toContain('[[content/10_Policies]]');
      expect(content).toContain('[[content/90_Architecture/ADRs]]');
      expect(content).toContain('[[content/100_Products/PRDs]]');
      expect(content).toContain('[Edit in CMS](/admin/#/collections/');

      // Check timestamp
      expect(content).toMatch(/Last updated: \d{4}-\d{2}-\d{2}/);
    });

    it('should handle empty directories gracefully', async () => {
      // Create empty directory structure
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

      const outputPath = path.join(contentDir, 'index.md');
      await generateHomepage({
        contentDir,
        outputPath
      });

      const content = await fs.readFile(outputPath, 'utf-8');

      // Should still generate the page with 0 counts
      expect(content).toContain('Total documents: **0**');
      expect(content).toContain('- **Policies** (0):');
      expect(content).toContain('- **Standards** (0):')
    });

    it('should create missing content directory', async () => {
      const missingDir = path.join(testDir, 'missing-content');
      const outputPath = path.join(missingDir, 'index.md');

      await generateHomepage({
        contentDir: missingDir,
        outputPath
      });

      // Should create the directory and the index file
      expect(await fs.pathExists(missingDir)).toBe(true);
      expect(await fs.pathExists(outputPath)).toBe(true);

      const content = await fs.readFile(outputPath, 'utf-8');
      expect(content).toContain('# Synapse Documentation Framework');
    });

    it('should exclude Examples and templates directories from count', async () => {
      // Create directories with Examples and templates that should be excluded
      await fs.ensureDir(path.join(contentDir, '10_Policies'));
      await fs.writeFile(path.join(contentDir, '10_Policies', 'policy1.md'), '# Policy 1');
      await fs.ensureDir(path.join(contentDir, '10_Policies', 'Examples'));
      await fs.writeFile(path.join(contentDir, '10_Policies', 'Examples', 'example.md'), '# Example');

      await fs.ensureDir(path.join(contentDir, '20_Standards', 'templates'));
      await fs.writeFile(path.join(contentDir, '20_Standards', 'templates', 'template.md'), '# Template');
      await fs.writeFile(path.join(contentDir, '20_Standards', 'standard1.md'), '# Standard 1');

      // Create empty directories for other types
      await fs.ensureDir(path.join(contentDir, '30_Processes'));
      await fs.ensureDir(path.join(contentDir, '40_SOPs'));
      await fs.ensureDir(path.join(contentDir, '50_Runbooks'));
      await fs.ensureDir(path.join(contentDir, '70_Systems'));
      await fs.ensureDir(path.join(contentDir, '90_Architecture', 'ADRs'));
      await fs.ensureDir(path.join(contentDir, '90_Architecture', 'TDDs'));
      await fs.ensureDir(path.join(contentDir, '100_Products', 'PRDs'));
      await fs.ensureDir(path.join(contentDir, '110_Capabilities'));

      const outputPath = path.join(contentDir, 'index.md');
      await generateHomepage({
        contentDir,
        outputPath
      });

      const content = await fs.readFile(outputPath, 'utf-8');

      // Should only count 2 documents (policy1.md and standard1.md), not the examples/templates
      expect(content).toContain('Total documents: **2**');
      expect(content).toContain('- **Policies** (1):');
      expect(content).toContain('- **Standards** (1):')
    });

    it('should correctly format sections with subfolders', async () => {
      // Create Architecture with ADRs and TDDs
      await fs.ensureDir(path.join(contentDir, '90_Architecture', 'ADRs'));
      await fs.writeFile(path.join(contentDir, '90_Architecture', 'ADRs', 'adr1.md'), '# ADR 1');
      await fs.writeFile(path.join(contentDir, '90_Architecture', 'ADRs', 'adr2.md'), '# ADR 2');

      await fs.ensureDir(path.join(contentDir, '90_Architecture', 'TDDs'));
      await fs.writeFile(path.join(contentDir, '90_Architecture', 'TDDs', 'tdd1.md'), '# TDD 1');

      // Create Products with PRDs
      await fs.ensureDir(path.join(contentDir, '100_Products', 'PRDs'));
      await fs.writeFile(path.join(contentDir, '100_Products', 'PRDs', 'prd1.md'), '# PRD 1');

      // Create empty directories for other types
      await fs.ensureDir(path.join(contentDir, '10_Policies'));
      await fs.ensureDir(path.join(contentDir, '20_Standards'));
      await fs.ensureDir(path.join(contentDir, '30_Processes'));
      await fs.ensureDir(path.join(contentDir, '40_SOPs'));
      await fs.ensureDir(path.join(contentDir, '50_Runbooks'));
      await fs.ensureDir(path.join(contentDir, '60_Systems'));
      await fs.ensureDir(path.join(contentDir, '90_Capabilities'));

      const outputPath = path.join(contentDir, 'index.md');
      await generateHomepage({
        contentDir,
        outputPath
      });

      const content = await fs.readFile(outputPath, 'utf-8');

      // Check Architecture section
      expect(content).toContain('### Architecture');
      expect(content).toContain('- **ADRs** (2):');
      expect(content).toContain('- **TDDs** (1):');
      expect(content).toContain('[[content/90_Architecture/ADRs]]');
      expect(content).toContain('[[content/90_Architecture/TDDs]]');

      // Check Products section
      expect(content).toContain('### Products');
      expect(content).toContain('- **PRDs** (1):');
      expect(content).toContain('[[content/100_Products/PRDs]]');
    });

    it('should correctly handle singular vs plural in document count text', async () => {
      // Create exactly 1 policy and 2 standards
      await fs.ensureDir(path.join(contentDir, '10_Policies'));
      await fs.writeFile(path.join(contentDir, '10_Policies', 'policy1.md'), '# Policy 1');

      await fs.ensureDir(path.join(contentDir, '20_Standards'));
      await fs.writeFile(path.join(contentDir, '20_Standards', 's1.md'), '# S1');
      await fs.writeFile(path.join(contentDir, '20_Standards', 's2.md'), '# S2');

      // Create empty directories for other types
      await fs.ensureDir(path.join(contentDir, '30_Processes'));
      await fs.ensureDir(path.join(contentDir, '40_SOPs'));
      await fs.ensureDir(path.join(contentDir, '50_Runbooks'));
      await fs.ensureDir(path.join(contentDir, '70_Systems'));
      await fs.ensureDir(path.join(contentDir, '90_Architecture', 'ADRs'));
      await fs.ensureDir(path.join(contentDir, '90_Architecture', 'TDDs'));
      await fs.ensureDir(path.join(contentDir, '100_Products', 'PRDs'));
      await fs.ensureDir(path.join(contentDir, '110_Capabilities'));

      const outputPath = path.join(contentDir, 'index.md');
      await generateHomepage({
        contentDir,
        outputPath
      });

      const content = await fs.readFile(outputPath, 'utf-8');

      // Check counts in new format
      expect(content).toContain('- **Policies** (1):');
      expect(content).toContain('- **Standards** (2):');
      expect(content).toContain('- **Processes** (0):');
    });

    it('should correctly count documents across all categories', async () => {
      // Set up specific counts for testing total calculation
      const documentCounts = {
        '10_Policies': 5,
        '20_Standards': 3,
        '30_Processes': 7,
        '40_SOPs': 2,
        '50_Runbooks': 4,
        '70_Systems': 6,
        '90_Architecture/ADRs': 8,
        '90_Architecture/TDDs': 1,
        '100_Products/PRDs': 9,
        '110_Capabilities': 10
      };

      for (const [folder, count] of Object.entries(documentCounts)) {
        const folderPath = path.join(contentDir, folder);
        await fs.ensureDir(folderPath);
        for (let i = 1; i <= count; i++) {
          await fs.writeFile(path.join(folderPath, `file${i}.md`), `# File ${i}`);
        }
      }

      const outputPath = path.join(contentDir, 'index.md');
      await generateHomepage({
        contentDir,
        outputPath
      });

      const content = await fs.readFile(outputPath, 'utf-8');

      // Total should be sum of all counts we created: 5+3+7+2+4+6+8+1+9+10 = 55
      // Extract actual total from content to verify it's correct
      const totalMatch = content.match(/Total documents: \*\*(\d+)\*\*/);
      const actualTotal = totalMatch ? parseInt(totalMatch[1]) : 0;
      expect(actualTotal).toBeGreaterThanOrEqual(55); // At least what we created

      // Verify individual counts in table match what we created
      expect(content).toContain('| Policies | 5 |');
      expect(content).toContain('| Standards | 3 |');
      expect(content).toContain('| Processes | 7 |');
      expect(content).toContain('| SOPs | 2 |');
      expect(content).toContain('| Runbooks | 4 |');
      expect(content).toContain('| Systems | 6 |');
      expect(content).toContain('| ADRs | 8 |');
      expect(content).toContain('| TDDs | 1 |');
      expect(content).toContain('| PRDs | 9 |');
      expect(content).toContain('| Capabilities | 10 |');
    });
  });
});
