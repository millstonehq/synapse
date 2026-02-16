import fsExtra from 'fs-extra';
const fs = fsExtra;
import * as path from 'path';
import { validateCommand } from '../../src/commands/validate';
import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';

describe('Validate Command - Output Formats', () => {
  const testDir = path.join(process.cwd(), 'test-vault-formats');
  const contentDir = path.join(testDir, 'content');
  const schemaDir = path.join(contentDir, 'schemas');

  // Mock console.log to capture output
  const originalConsoleLog = console.log;
  const originalConsoleError = console.error;
  const originalProcessExit = process.exit;
  let consoleOutput: string[] = [];

  beforeEach(async () => {
    // Setup console mocks
    consoleOutput = [];
    console.log = jest.fn((...args) => {
      consoleOutput.push(args.join(' '));
    }) as any;
    console.error = jest.fn((...args) => {
      consoleOutput.push(args.join(' '));
    }) as any;
    process.exit = jest.fn() as any;

    // Create test directory structure
    await fs.ensureDir(path.join(contentDir, '10_Policies'));
    await fs.ensureDir(schemaDir);

    // Copy schemas
    const realSchemaDir = path.resolve(process.cwd(), '../../schemas/frontmatter');
    const schemas = await fs.readdir(realSchemaDir);
    for (const schema of schemas) {
      if (schema.endsWith('.json')) {
        await fs.copy(
          path.join(realSchemaDir, schema),
          path.join(schemaDir, schema)
        );
      }
    }
  });

  afterEach(async () => {
    // Restore console
    console.log = originalConsoleLog;
    console.error = originalConsoleError;
    process.exit = originalProcessExit;

    await fs.remove(testDir);
  });

  describe('JSON format', () => {
    it('should output valid JSON with no errors', async () => {
      // Create a valid policy with all required fields
      await fs.writeFile(
        path.join(contentDir, '10_Policies/test-policy.md'),
        `---
type: policy
id: test-policy
title: Test Policy
status: approved
owner: Security Team
created: "2024-01-01T00:00:00.000Z"
updated: "2024-01-01T00:00:00.000Z"
tags: ["test"]
summary: Test policy for validation
related_standards: ["ISO 27001"]
---

# Test Policy

## Scope

This policy applies to all systems.

## Rationale

Testing validation.

## Policy Statements

- Test statement 1
- Test statement 2

## Related Standards

- ISO 27001
- SOC 2`
      );

      await validateCommand({
        dir: contentDir,
        schema: schemaDir,
        format: 'json',
        strict: true
      });

      // Should output valid JSON
      const output = consoleOutput.join('');
      const json = JSON.parse(output);

      // Debug: show what errors we're getting
      if (json.errors.length > 0) {
        console.log('Unexpected errors found:');
        json.errors.forEach((err: any) => {
          console.log(`  - ${err.code}: ${err.message}`);
        });
      }

      expect(json).toHaveProperty('errors');
      expect(json).toHaveProperty('warnings');
      expect(json).toHaveProperty('summary');
      expect(json.summary).toMatchObject({
        total: 1,
        valid: 1,
        errors: 0,
        warnings: 0
      });
      expect(json.errors).toEqual([]);
      expect(json.warnings).toEqual([]);
    });

    it('should output valid JSON with errors', async () => {
      // Create an invalid policy (missing required fields)
      await fs.writeFile(
        path.join(contentDir, '10_Policies/invalid-policy.md'),
        `---
type: policy
id: invalid-policy
title: Invalid Policy
# Missing required fields: status, owner, created, updated, scope, rationale, related_standards
---

# Invalid Policy`
      );

      await validateCommand({
        dir: contentDir,
        schema: schemaDir,
        format: 'json',
        strict: true
      }).catch(() => {}); // Expect it to fail

      // Should output valid JSON even with errors
      const output = consoleOutput.join('');
      const json = JSON.parse(output);

      expect(json).toHaveProperty('errors');
      expect(json).toHaveProperty('warnings');
      expect(json).toHaveProperty('summary');
      expect(json.errors.length).toBeGreaterThan(0);
      expect(json.summary.errors).toBeGreaterThan(0);
      expect(json.summary.valid).toBe(0);

      // Check that process.exit was called with 1
      expect(process.exit).toHaveBeenCalledWith(1);
    });
  });

  describe('Compact format', () => {
    it('should output compact format with warnings and errors', async () => {
      // Create a policy with issues (uppercase ID, empty related_standards)
      await fs.writeFile(
        path.join(contentDir, '10_Policies/policy-issues.md'),
        `---
type: policy
id: POL001
title: Policy With Issues
status: draft
owner: Security Team
created: "2024-01-01T00:00:00.000Z"
updated: "2024-01-01T00:00:00.000Z"
tags: ["test"]
summary: Test
related_standards: []
---

# Policy

## Scope

All systems

## Rationale

Test`
      );

      await validateCommand({
        dir: contentDir,
        schema: schemaDir,
        format: 'compact',
        strict: true
      }).catch(() => {});

      const output = consoleOutput.join('\n');

      // Should have compact format with [E] or [W] prefixes
      expect(output).toContain('[E]');
      // Check for file path in output
      expect(output).toContain('policy-issues.md');
    });

    it('should output nothing in compact format when no issues', async () => {
      // Create a valid policy
      await fs.writeFile(
        path.join(contentDir, '10_Policies/valid-policy.md'),
        `---
type: policy
id: valid-policy
title: Valid Policy
status: approved
owner: Security Team
created: "2024-01-01T00:00:00.000Z"
updated: "2024-01-01T00:00:00.000Z"
tags: ["test"]
summary: Valid policy
related_standards: ["ISO 27001"]
---

# Valid Policy

## Scope

This policy applies to all systems.

## Rationale

Testing validation.

## Policy Statements

- Valid statement 1
- Valid statement 2

## Related Standards

- ISO 27001
- SOC 2`
      );

      await validateCommand({
        dir: contentDir,
        schema: schemaDir,
        format: 'compact',
        strict: false
      });

      const output = consoleOutput.join('\n');

      // Should have no error or warning output
      expect(output).not.toContain('[E]');
      expect(output).not.toContain('[W]');
    });
  });

  describe('Pretty format (default)', () => {
    it('should output pretty format with emojis', async () => {
      // Create a valid policy
      await fs.writeFile(
        path.join(contentDir, '10_Policies/pretty-policy.md'),
        `---
type: policy
id: pretty-policy
title: Pretty Policy
status: approved
owner: Security Team
created: "2024-01-01T00:00:00.000Z"
updated: "2024-01-01T00:00:00.000Z"
tags: ["test"]
summary: Pretty test
related_standards: ["ISO 27001"]
---

# Pretty Policy

## Scope

This policy applies to all systems.

## Rationale

Testing pretty output.

## Policy Statements

- Pretty statement 1
- Pretty statement 2

## Related Standards

- ISO 27001
- SOC 2`
      );

      await validateCommand({
        dir: contentDir,
        schema: schemaDir,
        // No format specified - should use default pretty
        strict: false
      });

      const output = consoleOutput.join('\n');

      // Should have pretty format with emojis
      expect(output).toContain('✅');
      expect(output).toContain('Validated 1 files');
      expect(output).toContain('All validations passed');
    });

    it('should show errors in pretty format', async () => {
      // Create an invalid policy
      await fs.writeFile(
        path.join(contentDir, '10_Policies/error-policy.md'),
        `---
type: policy
id: error-policy
title: Error Policy
# Missing required fields
---

# Error Policy`
      );

      await validateCommand({
        dir: contentDir,
        schema: schemaDir,
        strict: true
      }).catch(() => {});

      const output = consoleOutput.join('\n');

      // Should have error indicators
      expect(output).toContain('❌');
      expect(output).toContain('errors:');
      expect(output).toContain('Validation failed');
    });
  });

  describe('Quiet mode', () => {
    it('should not output anything in quiet mode', async () => {
      await fs.writeFile(
        path.join(contentDir, '10_Policies/quiet-policy.md'),
        `---
type: policy
id: quiet-policy
title: Quiet Policy
status: approved
owner: Security Team
created: "2024-01-01T00:00:00.000Z"
updated: "2024-01-01T00:00:00.000Z"
tags: ["test"]
summary: Quiet test
related_standards: ["ISO 27001"]
---

# Quiet Policy

## Scope

This policy applies to all systems.

## Rationale

Testing quiet mode.

## Policy Statements

- Quiet statement 1
- Quiet statement 2

## Related Standards

- ISO 27001
- SOC 2`
      );

      await validateCommand({
        dir: contentDir,
        schema: schemaDir,
        quiet: true
      });

      const output = consoleOutput.join('\n');

      // Should have no output at all
      expect(output).toBe('');
    });
  });

  describe('Exit codes', () => {
    it('should not call process.exit when validation passes', async () => {
      await fs.writeFile(
        path.join(contentDir, '10_Policies/pass-policy.md'),
        `---
type: policy
id: pass-policy
title: Pass Policy
status: approved
owner: Security Team
created: "2024-01-01T00:00:00.000Z"
updated: "2024-01-01T00:00:00.000Z"
tags: ["test"]
summary: Pass test
related_standards: ["ISO 27001"]
---

# Pass Policy

## Scope

This policy applies to all systems.

## Rationale

Testing pass.

## Policy Statements

- Pass statement 1
- Pass statement 2

## Related Standards

- ISO 27001
- SOC 2`
      );

      await validateCommand({
        dir: contentDir,
        schema: schemaDir,
        format: 'json'
      });

      expect(process.exit).not.toHaveBeenCalled();
    });

    it('should call process.exit(1) when validation fails', async () => {
      await fs.writeFile(
        path.join(contentDir, '10_Policies/fail-policy.md'),
        `---
type: policy
# Invalid - missing required fields
---

# Fail Policy`
      );

      await validateCommand({
        dir: contentDir,
        schema: schemaDir,
        format: 'json'
      }).catch(() => {});

      expect(process.exit).toHaveBeenCalledWith(1);
    });
  });
});
