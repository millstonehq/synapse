import { describe, it, expect } from '@jest/globals';
import {
  expectedFolder,
  validateFolderForType,
  validateFilenamePattern,
  validateNaming,
  type ValidationIssue
} from '../../src/lib/naming';

describe('naming module', () => {
  describe('expectedFolder', () => {
    it('should return correct folder for each document type', () => {
      expect(expectedFolder('policy')).toBe('content/10_Policies');
      expect(expectedFolder('standard')).toBe('content/20_Standards');
      expect(expectedFolder('process')).toBe('content/30_Processes');
      expect(expectedFolder('sop')).toBe('content/40_SOPs');
      expect(expectedFolder('runbook')).toBe('content/50_Runbooks');
      expect(expectedFolder('system')).toBe('content/70_Systems');
      expect(expectedFolder('adr')).toBe('content/90_Architecture/ADRs');
      expect(expectedFolder('prd')).toBe('content/100_Products/PRDs');
      expect(expectedFolder('capability')).toBe('content/110_Capabilities');
      expect(expectedFolder('tdd')).toBe('content/90_Architecture/TDDs');
    });

    it('should throw error for unknown document type', () => {
      expect(() => expectedFolder('invalid')).toThrow('Unknown document type: invalid');
    });
  });

  describe('validateFolderForType', () => {
    it('should return no issues for correct folder placement', () => {
      const issues = validateFolderForType(
        'content/10_Policies/data-retention.md',
        'policy'
      );
      expect(issues).toHaveLength(0);
    });

    it('should return error for incorrect folder placement', () => {
      const issues = validateFolderForType(
        'content/20_Standards/data-retention.md',
        'policy'
      );
      expect(issues).toHaveLength(1);
      expect(issues[0]).toMatchObject({
        type: 'error',
        code: 'WRONG_FOLDER',
        message: expect.stringContaining('must be placed in content/10_Policies')
      });
    });

    it('should handle ADR subfolder correctly', () => {
      const issues = validateFolderForType(
        'content/90_Architecture/ADRs/ADR-0001-api-design.md',
        'adr'
      );
      expect(issues).toHaveLength(0);
    });

    it('should handle TDD subfolder correctly', () => {
      const issues = validateFolderForType(
        'content/90_Architecture/TDDs/synapse-tdd.md',
        'tdd'
      );
      expect(issues).toHaveLength(0);
    });

    it('should handle PRD subfolder correctly', () => {
      const issues = validateFolderForType(
        'content/100_Products/PRDs/synapse-documentation-framework-v1-prd.md',
        'prd'
      );
      expect(issues).toHaveLength(0);
    });

    it('should handle Windows-style paths', () => {
      const issues = validateFolderForType(
        'content\\10_Policies\\data-retention.md',
        'policy'
      );
      expect(issues).toHaveLength(0);
    });
  });

  describe('validateFilenamePattern', () => {
    describe('ADR validation', () => {
      it('should validate correct ADR pattern', () => {
        const issues = validateFilenamePattern(
          'content/90_Architecture/ADRs/ADR-0001-api-design.md',
          'adr',
          'ADR-0001',
          'API Design Decisions',
          true
        );
        expect(issues).toHaveLength(0);
      });

      it('should error on invalid ADR ID pattern', () => {
        const issues = validateFilenamePattern(
          'content/90_Architecture/ADRs/ADR-1-api-design.md',
          'adr',
          'ADR-1',
          'API Design',
          true
        );
        // Should have two errors: invalid ID and invalid filename
        expect(issues).toHaveLength(2);

        const idError = issues.find(i => i.code === 'INVALID_ADR_ID');
        expect(idError).toMatchObject({
          type: 'error',
          code: 'INVALID_ADR_ID',
          message: expect.stringContaining('ADR id must match pattern ADR-####')
        });

        const filenameError = issues.find(i => i.code === 'INVALID_ADR_FILENAME');
        expect(filenameError).toMatchObject({
          type: 'error',
          code: 'INVALID_ADR_FILENAME',
          message: expect.stringContaining('ADR filename must match pattern')
        });
      });

      it('should error on invalid ADR filename pattern', () => {
        const issues = validateFilenamePattern(
          'content/90_Architecture/ADRs/adr_0001_api_design.md',
          'adr',
          'ADR-0001',
          'API Design',
          true
        );
        expect(issues).toHaveLength(1);
        expect(issues[0]).toMatchObject({
          type: 'error',
          code: 'INVALID_ADR_FILENAME',
          message: expect.stringContaining('ADR filename must match pattern')
        });
      });

      it('should error when ADR number in filename does not match ID', () => {
        const issues = validateFilenamePattern(
          'content/90_Architecture/ADRs/ADR-0002-api-design.md',
          'adr',
          'ADR-0001',
          'API Design',
          true
        );
        expect(issues).toHaveLength(1);
        expect(issues[0]).toMatchObject({
          type: 'error',
          code: 'ADR_ID_MISMATCH',
          message: expect.stringContaining('does not match id')
        });
      });

      it('should accept ADR IDs with more than 4 digits', () => {
        const issues = validateFilenamePattern(
          'content/90_Architecture/ADRs/ADR-10001-large-scale-refactor.md',
          'adr',
          'ADR-10001',
          'Large Scale Refactor',
          true
        );
        expect(issues).toHaveLength(0);
      });
    });

    describe('non-ADR validation', () => {
      it('should validate correct slug-case filename', () => {
        const issues = validateFilenamePattern(
          'content/10_Policies/data-retention-policy.md',
          'policy',
          'data-retention-001',
          'Data Retention Policy',
          true
        );
        expect(issues).toHaveLength(0);
      });

      it('should error on non-slug-case filename', () => {
        const issues = validateFilenamePattern(
          'content/10_Policies/Data_Retention_Policy.md',
          'policy',
          'policy-001',
          'Data Retention Policy',
          true
        );
        expect(issues).toHaveLength(1);
        expect(issues[0]).toMatchObject({
          type: 'error',
          code: 'INVALID_FILENAME_FORMAT',
          message: expect.stringContaining('must be in slug-case')
        });
      });

      it('should handle filename/title mismatch based on strict mode', () => {
        // Strict mode (default): error
        const strictIssues = validateFilenamePattern(
          'content/10_Policies/data-policy.md',
          'policy',
          'policy-001',
          'Data Retention Policy',
          true
        );
        expect(strictIssues).toHaveLength(1);
        expect(strictIssues[0]).toMatchObject({
          type: 'error',
          code: 'FILENAME_TITLE_MISMATCH'
        });

        // Non-strict mode: warning
        const nonStrictIssues = validateFilenamePattern(
          'content/10_Policies/data-policy.md',
          'policy',
          'policy-001',
          'Data Retention Policy',
          false
        );
        expect(nonStrictIssues).toHaveLength(1);
        expect(nonStrictIssues[0]).toMatchObject({
          type: 'warning',
          code: 'FILENAME_TITLE_MISMATCH'
        });
      });

      it('should default to strict mode when not specified', () => {
        const issues = validateFilenamePattern(
          'content/10_Policies/data-policy.md',
          'policy',
          'policy-001',
          'Data Retention Policy'
          // strict parameter omitted - should default to true
        );
        expect(issues).toHaveLength(1);
        expect(issues[0]).toMatchObject({
          type: 'error',
          code: 'FILENAME_TITLE_MISMATCH'
        });
      });

      it('should handle special characters in title correctly', () => {
        const issues = validateFilenamePattern(
          'content/20_Standards/api-design-rest.md',
          'standard',
          'std-001',
          'API Design & REST',
          true
        );
        expect(issues).toHaveLength(0);
      });
    });

    describe('reference document validation', () => {
      it('should validate reference with upstream_url', () => {
        const issues = validateFilenamePattern(
          'content/80_References/claude-code-plugins.md',
          'reference',
          'ref-001',
          'Claude Code Plugins',
          true,
          { upstream_url: 'https://docs.claude.com/plugins' }
        );
        expect(issues).toHaveLength(0);
      });

      it('should error when upstream_url is missing', () => {
        const issues = validateFilenamePattern(
          'content/80_References/some-reference.md',
          'reference',
          'ref-001',
          'Some Reference',
          true,
          {}
        );
        expect(issues).toHaveLength(1);
        expect(issues[0]).toMatchObject({
          type: 'error',
          code: 'MISSING_UPSTREAM_URL'
        });
      });

      it('should error when filename is not slug-case', () => {
        const issues = validateFilenamePattern(
          'content/80_References/Claude_Code_Plugins.md',
          'reference',
          'ref-001',
          'Claude Code Plugins',
          true,
          { upstream_url: 'https://docs.claude.com/plugins' }
        );
        expect(issues).toHaveLength(1);
        expect(issues[0]).toMatchObject({
          type: 'error',
          code: 'INVALID_FILENAME_FORMAT'
        });
      });

      it('should error when source prefix is missing', () => {
        const issues = validateFilenamePattern(
          'content/80_References/plugins.md',
          'reference',
          'ref-001',
          'Plugins',
          true,
          { upstream_url: 'https://docs.claude.com/plugins' }
        );
        expect(issues).toHaveLength(1);
        expect(issues[0]).toMatchObject({
          type: 'error',
          code: 'MISSING_SOURCE_PREFIX',
          message: expect.stringContaining('claude-code-')
        });
      });

      it('should accept manual source_prefix override', () => {
        const issues = validateFilenamePattern(
          'content/80_References/custom-prefix-document.md',
          'reference',
          'ref-001',
          'Document',
          true,
          {
            upstream_url: 'https://example.com/docs',
            source_prefix: 'custom-prefix'
          }
        );
        expect(issues).toHaveLength(0);
      });

      it('should validate slug matches title after prefix', () => {
        const issues = validateFilenamePattern(
          'content/80_References/dora-wrong-slug.md',
          'reference',
          'ref-001',
          'DORA 2025 Analysis',
          true,
          { upstream_url: 'https://dora.dev/analysis' }
        );
        expect(issues).toHaveLength(1);
        expect(issues[0]).toMatchObject({
          type: 'error',
          code: 'FILENAME_TITLE_MISMATCH'
        });
      });

      it('should handle titles with source prefix in them', () => {
        const issues = validateFilenamePattern(
          'content/80_References/mercury-api-reference.md',
          'reference',
          'ref-001',
          'Mercury API Reference',
          true,
          { upstream_url: 'https://api.mercury.com/reference' }
        );
        expect(issues).toHaveLength(0);
      });

      it('should handle docs.X.com pattern', () => {
        const issues = validateFilenamePattern(
          'content/80_References/example-guide.md',
          'reference',
          'ref-001',
          'Example Guide',
          true,
          { upstream_url: 'https://docs.example.com/guide' }
        );
        expect(issues).toHaveLength(0);
      });

      it('should handle api.X.com pattern', () => {
        const issues = validateFilenamePattern(
          'content/80_References/stripe-webhooks.md',
          'reference',
          'ref-001',
          'Stripe Webhooks',
          true,
          { upstream_url: 'https://api.stripe.com/webhooks' }
        );
        expect(issues).toHaveLength(0);
      });

      it('should handle huggingface.co', () => {
        const issues = validateFilenamePattern(
          'content/80_References/huggingface-models.md',
          'reference',
          'ref-001',
          'Models',
          true,
          { upstream_url: 'https://huggingface.co/models' }
        );
        expect(issues).toHaveLength(0);
      });

      it('should handle generic domains with path extraction', () => {
        const issues = validateFilenamePattern(
          'content/80_References/anthropic-api.md',
          'reference',
          'ref-001',
          'Anthropic API',
          true,
          { upstream_url: 'https://github.com/anthropic/api' }
        );
        expect(issues).toHaveLength(0);
      });

      it('should error when URL cannot be parsed', () => {
        const issues = validateFilenamePattern(
          'content/80_References/some-doc.md',
          'reference',
          'ref-001',
          'Some Doc',
          true,
          { upstream_url: 'not-a-valid-url' }
        );
        expect(issues).toHaveLength(1);
        expect(issues[0]).toMatchObject({
          type: 'error',
          code: 'CANNOT_EXTRACT_SOURCE_PREFIX'
        });
      });

      it('should use warning in non-strict mode for slug mismatch', () => {
        const issues = validateFilenamePattern(
          'content/80_References/dora-wrong.md',
          'reference',
          'ref-001',
          'DORA Analysis',
          false,
          { upstream_url: 'https://dora.dev/docs' }
        );
        const mismatch = issues.find(i => i.code === 'FILENAME_TITLE_MISMATCH');
        expect(mismatch?.type).toBe('warning');
      });

      it('should handle subdomain extraction', () => {
        const issues = validateFilenamePattern(
          'content/80_References/readme-getting-started.md',
          'reference',
          'ref-001',
          'Getting Started',
          true,
          { upstream_url: 'https://readme.io/getting-started' }
        );
        expect(issues).toHaveLength(0);
      });
    });
  });

  describe('validateNaming', () => {
    it('should skip validation for example files in Examples folder', () => {
      const issues = validateNaming(
        'content/00_Guides/Examples/example-policy.md',
        {
          type: 'policy',
          id: 'example-001',
          title: 'Example Policy'
        },
        true
      );
      expect(issues).toHaveLength(0);
    });

    it('should skip validation for files marked as example in frontmatter', () => {
      const issues = validateNaming(
        'content/10_Policies/wrong-filename.md',
        {
          type: 'policy',
          id: 'policy-001',
          title: 'Example Policy',
          example: true
        },
        true
      );
      expect(issues).toHaveLength(0);
    });

    it('should perform comprehensive validation', () => {
      const issues = validateNaming(
        'content/90_Architecture/ADRs/ADR-0001-api-design.md',
        {
          type: 'adr',
          id: 'ADR-0001',
          title: 'API Design Decisions'
        },
        true
      );
      expect(issues).toHaveLength(0);
    });

    it('should error when type is missing', () => {
      const issues = validateNaming(
        'content/10_Policies/data-retention.md',
        {
          id: 'policy-001',
          title: 'Data Retention'
        },
        true
      );
      expect(issues).toHaveLength(1);
      expect(issues[0]).toMatchObject({
        type: 'error',
        code: 'MISSING_TYPE'
      });
    });

    it('should error when type is invalid', () => {
      const issues = validateNaming(
        'content/10_Policies/data-retention.md',
        {
          type: 'invalid-type',
          id: 'policy-001',
          title: 'Data Retention'
        },
        true
      );
      expect(issues).toHaveLength(1);
      expect(issues[0]).toMatchObject({
        type: 'error',
        code: 'INVALID_TYPE'
      });
    });

    it('should error when id is missing', () => {
      const issues = validateNaming(
        'content/10_Policies/data-retention.md',
        {
          type: 'policy',
          title: 'Data Retention'
        },
        true
      );
      expect(issues).toHaveLength(1);
      expect(issues[0]).toMatchObject({
        type: 'error',
        code: 'MISSING_ID'
      });
    });

    it('should error when title is missing', () => {
      const issues = validateNaming(
        'content/10_Policies/data-retention.md',
        {
          type: 'policy',
          id: 'policy-001'
        },
        true
      );
      expect(issues).toHaveLength(1);
      expect(issues[0]).toMatchObject({
        type: 'error',
        code: 'MISSING_TITLE'
      });
    });

    it('should collect multiple validation errors', () => {
      const issues = validateNaming(
        'content/20_Standards/Policy_001.md', // Wrong folder and wrong filename format
        {
          type: 'policy',
          id: 'policy-001',
          title: 'Data Retention Policy'
        },
        true
      );
      expect(issues.length).toBeGreaterThanOrEqual(2);

      const codes = issues.map(i => i.code);
      expect(codes).toContain('WRONG_FOLDER');
      expect(codes).toContain('INVALID_FILENAME_FORMAT');
    });

    it('should respect strict mode setting', () => {
      // Non-strict mode
      const nonStrictIssues = validateNaming(
        'content/10_Policies/data-policy.md',
        {
          type: 'policy',
          id: 'policy-001',
          title: 'Data Retention Policy'
        },
        false
      );
      const mismatchIssue = nonStrictIssues.find(i => i.code === 'FILENAME_TITLE_MISMATCH');
      expect(mismatchIssue?.type).toBe('warning');

      // Strict mode (default)
      const strictIssues = validateNaming(
        'content/10_Policies/data-policy.md',
        {
          type: 'policy',
          id: 'policy-001',
          title: 'Data Retention Policy'
        }
        // strict parameter omitted - should default to true
      );
      const strictMismatchIssue = strictIssues.find(i => i.code === 'FILENAME_TITLE_MISMATCH');
      expect(strictMismatchIssue?.type).toBe('error');
    });

    it('should validate complex ADR requirements comprehensively', () => {
      const issues = validateNaming(
        'content/90_Architecture/ADRs/ADR-0001-api-design.md',
        {
          type: 'adr',
          id: 'ADR-0002', // ID mismatch
          title: 'API Design'
        },
        true
      );

      const idMismatchIssue = issues.find(i => i.code === 'ADR_ID_MISMATCH');
      expect(idMismatchIssue).toBeDefined();
      expect(idMismatchIssue?.type).toBe('error');
    });
  });
});
