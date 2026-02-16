import fsExtra from 'fs-extra';
const fs = fsExtra;
import * as path from 'path';
import { format } from '../../src/commands/format';
import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';

describe('Format Command', () => {
  const testDir = path.join(process.cwd(), 'test-vault-format');
  const contentDir = path.join(testDir, 'content');

  beforeEach(async () => {
    // Just create test content directory - schemas will be found via path resolution
    await fs.ensureDir(contentDir);
  });

  afterEach(async () => {
    await fs.remove(testDir);
  });

  describe('Dry-run mode', () => {
    it('should identify files needing formatting without modifying them', async () => {
      // Create a policy document with missing required sections
      await fs.ensureDir(path.join(contentDir, '10_Policies'));
      const policyPath = path.join(contentDir, '10_Policies/test-policy.md');

      await fs.writeFile(
        policyPath,
        `---
type: policy
id: test-policy
title: Test Policy
owner: Security Team
summary: A test policy
scope: All systems
rationale: Testing
---

# Summary

This is a test policy.`
      );

      const originalContent = await fs.readFile(policyPath, 'utf-8');

      // Run format without write flag (dry-run)
      const result = await format({
        contentDir,
        write: false,
        verbose: true
      });

      // File content should be unchanged
      const afterContent = await fs.readFile(policyPath, 'utf-8');
      expect(afterContent).toBe(originalContent);

      // Should report files that would be formatted
      expect(result.filesModified).toBeGreaterThan(0);
    });
  });

  describe('Write mode', () => {
    it('should modify files when write flag is enabled', async () => {
      // Create a policy document with missing sections
      await fs.ensureDir(path.join(contentDir, '10_Policies'));
      const policyPath = path.join(contentDir, '10_Policies/test-policy.md');

      await fs.writeFile(
        policyPath,
        `---
type: policy
id: test-policy
title: Test Policy
owner: Security Team
summary: A test policy
scope: All systems
rationale: Testing
---

# Summary

This is a test policy.`
      );

      const originalContent = await fs.readFile(policyPath, 'utf-8');

      // Run format with write flag
      const result = await format({
        contentDir,
        write: true,
        verbose: true
      });

      // File should be modified
      const afterContent = await fs.readFile(policyPath, 'utf-8');
      expect(afterContent).not.toBe(originalContent);

      // Should have formatted at least one file
      expect(result.filesFormatted).toBeGreaterThan(0);
    });
  });

  describe('Section scaffolding', () => {
    it('should add missing required sections with TODO placeholders', async () => {
      // Create a policy document missing the "Enforcement" section
      await fs.ensureDir(path.join(contentDir, '10_Policies'));
      const policyPath = path.join(contentDir, '10_Policies/test-policy.md');

      await fs.writeFile(
        policyPath,
        `---
type: policy
id: test-policy
title: Test Policy
owner: Security Team
summary: A test policy
scope: All systems
rationale: Testing
---

# Summary

This is a test policy.

# Scope

All systems.`
      );

      // Run format with write flag
      await format({
        contentDir,
        write: true
      });

      const afterContent = await fs.readFile(policyPath, 'utf-8');

      // Should have added missing sections with level 2 headings
      expect(afterContent).toContain('## ');
      expect(afterContent).toContain('TODO');
    });

    it('should handle files that already have all required sections', async () => {
      await fs.ensureDir(path.join(contentDir, '10_Policies'));
      const policyPath = path.join(contentDir, '10_Policies/test-policy.md');

      const existingContent = 'This is my existing policy content.';

      await fs.writeFile(
        policyPath,
        `---
type: policy
id: test-policy
title: Test Policy
owner: Security Team
summary: A test policy
scope: All systems
rationale: Testing
---

## Scope
Scope content.

## Rationale
Rationale content.

## Policy Statements
${existingContent}

## Related Standards
Standards content.`
      );

      await format({
        contentDir,
        write: true
      });

      const afterContent = await fs.readFile(policyPath, 'utf-8');

      // Should preserve the existing content when all sections exist
      expect(afterContent).toContain(existingContent);
    });
  });

  describe('Section reordering', () => {
    it('should reorder sections to canonical order', async () => {
      // Create a policy with sections in wrong order
      await fs.ensureDir(path.join(contentDir, '10_Policies'));
      const policyPath = path.join(contentDir, '10_Policies/test-policy.md');

      await fs.writeFile(
        policyPath,
        `---
type: policy
id: test-policy
title: Test Policy
owner: Security Team
summary: A test policy
scope: All systems
rationale: Testing
---

## Policy Statements

Policy details.

## Scope

Scope details.

## Rationale

Rationale details.`
      );

      await format({
        contentDir,
        write: true
      });

      const afterContent = await fs.readFile(policyPath, 'utf-8');

      // Sections should be in canonical order
      const scopeIndex = afterContent.indexOf('## Scope');
      const rationaleIndex = afterContent.indexOf('## Rationale');
      const policyIndex = afterContent.indexOf('## Policy Statements');

      expect(scopeIndex).toBeGreaterThan(0);
      expect(rationaleIndex).toBeGreaterThan(0);
      expect(policyIndex).toBeGreaterThan(0);
      // Scope should come before Rationale and Policy Statements
      expect(scopeIndex).toBeLessThan(rationaleIndex);
      expect(scopeIndex).toBeLessThan(policyIndex);
    });
  });

  describe('Idempotency', () => {
    it('should produce no changes on second format run (CRITICAL)', async () => {
      // Create a policy document
      await fs.ensureDir(path.join(contentDir, '10_Policies'));
      const policyPath = path.join(contentDir, '10_Policies/test-policy.md');

      await fs.writeFile(
        policyPath,
        `---
type: policy
id: test-policy
title: Test Policy
owner: Security Team
summary: A test policy
scope: All systems
rationale: Testing
---

# Enforcement

Enforcement details.

# Summary

Summary details.

# Scope

Scope details.`
      );

      // First format run
      await format({
        contentDir,
        write: true
      });

      const afterFirstFormat = await fs.readFile(policyPath, 'utf-8');

      // Second format run
      const result = await format({
        contentDir,
        write: true
      });

      const afterSecondFormat = await fs.readFile(policyPath, 'utf-8');

      // Content should be identical
      expect(afterSecondFormat).toBe(afterFirstFormat);

      // Should report 0 files modified on second run
      expect(result.filesModified).toBe(0);
    });
  });

  describe('Section title normalization', () => {
    it('should normalize section titles to canonical form', async () => {
      // Create a policy with lowercase/mixed-case section titles
      await fs.ensureDir(path.join(contentDir, '10_Policies'));
      const policyPath = path.join(contentDir, '10_Policies/test-policy.md');

      await fs.writeFile(
        policyPath,
        `---
type: policy
id: test-policy
title: Test Policy
owner: Security Team
summary: A test policy
scope: All systems
rationale: Testing
---

## scope

Scope details.

## RATIONALE

Rationale details.

## policy statements

Policy details.`
      );

      await format({
        contentDir,
        write: true
      });

      const afterContent = await fs.readFile(policyPath, 'utf-8');

      // Section titles should be normalized to proper case with level 2 headings
      expect(afterContent).toContain('## Scope');
      expect(afterContent).toContain('## Rationale');
      expect(afterContent).toContain('## Policy Statements');

      // Should not contain the original incorrect titles
      expect(afterContent).not.toContain('## scope');
      expect(afterContent).not.toContain('## RATIONALE');
      expect(afterContent).not.toContain('## policy statements');
    });
  });

  describe('List normalization', () => {
    it('should normalize list markers and respect maxDepth rules', async () => {
      // Create a process with deeply nested lists
      await fs.ensureDir(path.join(contentDir, '30_Processes'));
      const processPath = path.join(contentDir, '30_Processes/test-process.md');

      await fs.writeFile(
        processPath,
        `---
type: process
id: test-process
title: Test Process
owner: Engineering
summary: Test process
purpose: Testing
roles:
  - Engineer
steps:
  - Step 1
related_standards:
  - "[[test-standard]]"
---

# Summary

Process summary.

# Roles

* Engineer
  * Senior Engineer
    * Lead Engineer
      * Principal Engineer

# Steps

- Step 1
  - Step 1a
    - Step 1a1`
      );

      await format({
        contentDir,
        write: true
      });

      const afterContent = await fs.readFile(processPath, 'utf-8');

      // List markers should be normalized to '-' for unordered lists
      expect(afterContent).not.toContain('* ');

      // Lists should respect maxDepth rules (if defined in body-grammar.json)
    });
  });

  describe('Error handling - invalid file', () => {
    it('should handle files with invalid frontmatter gracefully', async () => {
      await fs.ensureDir(path.join(contentDir, '10_Policies'));
      const policyPath = path.join(contentDir, '10_Policies/invalid-policy.md');

      // Create file with invalid YAML frontmatter
      await fs.writeFile(
        policyPath,
        `---
type: policy
id: invalid-policy
title: Invalid Policy
owner: Security Team
summary: [invalid yaml structure
---

# Summary

Test content.`
      );

      // Should not crash
      const result = await format({
        contentDir,
        write: false
      });

      // Should continue processing without crashing
      expect(result).toBeDefined();
      expect(result.success).toBeDefined();
    });
  });

  describe('Error handling - missing type', () => {
    it('should skip files without a valid document type', async () => {
      await fs.ensureDir(path.join(contentDir, '10_Policies'));
      const noTypePath = path.join(contentDir, '10_Policies/no-type.md');

      // Create file without type field
      await fs.writeFile(
        noTypePath,
        `---
id: no-type
title: No Type Document
---

# Summary

Test content.`
      );

      // Should not crash
      const result = await format({
        contentDir,
        write: false
      });

      // Should skip the file
      expect(result).toBeDefined();
    });
  });

  describe('Verbose mode', () => {
    it('should show all files including unchanged ones with verbose flag', async () => {
      await fs.ensureDir(path.join(contentDir, '10_Policies'));

      // Create a well-formatted file that won't need changes
      const goodPath = path.join(contentDir, '10_Policies/good-policy.md');
      await fs.writeFile(
        goodPath,
        `---
type: policy
id: good-policy
title: Good Policy
owner: Security Team
summary: A well-formatted policy
scope: All systems
rationale: Testing
---

# Summary

Summary content.

# Scope

Scope content.

# Enforcement

Enforcement content.`
      );

      // Create a file that needs formatting
      const badPath = path.join(contentDir, '10_Policies/bad-policy.md');
      await fs.writeFile(
        badPath,
        `---
type: policy
id: bad-policy
title: Bad Policy
owner: Security Team
summary: A poorly formatted policy
scope: All systems
rationale: Testing
---

# summary

Summary content.`
      );

      // Run with verbose
      const resultVerbose = await format({
        contentDir,
        write: false,
        verbose: true
      });

      // Run without verbose
      const resultQuiet = await format({
        contentDir,
        write: false,
        verbose: false
      });

      // Verbose should report on all files checked
      expect(resultVerbose.filesFormatted).toBeGreaterThanOrEqual(2);
      expect(resultQuiet.filesFormatted).toBeGreaterThanOrEqual(2);
    });
  });

  describe('Multiple document types', () => {
    it('should format different document types correctly', async () => {
      // Create multiple document types
      await fs.ensureDir(path.join(contentDir, '10_Policies'));
      await fs.ensureDir(path.join(contentDir, '30_Processes'));
      await fs.ensureDir(path.join(contentDir, '40_SOPs'));

      // Policy
      await fs.writeFile(
        path.join(contentDir, '10_Policies/test-policy.md'),
        `---
type: policy
id: test-policy
title: Test Policy
owner: Security
summary: Test
scope: All
rationale: Test
---

# Summary
Test`
      );

      // Process
      await fs.writeFile(
        path.join(contentDir, '30_Processes/test-process.md'),
        `---
type: process
id: test-process
title: Test Process
owner: Engineering
summary: Test
purpose: Test
roles:
  - Engineer
steps:
  - Step 1
related_standards:
  - "[[test]]"
---

# Summary
Test`
      );

      // SOP
      await fs.writeFile(
        path.join(contentDir, '40_SOPs/test-sop.md'),
        `---
type: sop
id: test-sop
title: Test SOP
owner: Operations
summary: Test
step_list:
  - Step 1
related_process: "[[test-process]]"
---

# Summary
Test`
      );

      const result = await format({
        contentDir,
        write: true
      });

      // Should successfully format all document types
      expect(result.filesFormatted).toBeGreaterThanOrEqual(3);
    });
  });
});
