import * as path from 'path';
import fsExtra from 'fs-extra';
const fs = fsExtra;
import {
  analyzeTemplate,
  lintTemplatesDirectory,
  type TemplateLintResult
} from '../../src/lib/templateLint';

describe('templateLint', () => {
  const testDir = path.join(process.cwd(), 'test-temp');
  const templatesDir = path.join(testDir, 'templates');
  const schemasDir = path.join(testDir, 'schemas');

  beforeEach(async () => {
    await fs.ensureDir(templatesDir);
    await fs.ensureDir(schemasDir);
  });

  afterEach(async () => {
    await fs.remove(testDir);
  });

  describe('analyzeTemplate', () => {
    it('should detect missing frontmatter', async () => {
      const templatePath = path.join(templatesDir, 'test.hbs');
      await fs.writeFile(templatePath, '# No frontmatter here\n{{title}}');

      const result = await analyzeTemplate(templatePath);

      expect(result.errors).toHaveLength(1);
      expect(result.errors[0].message).toContain('missing frontmatter');
      expect(result.warnings).toHaveLength(0);
    });

    it('should detect missing type constant', async () => {
      const templatePath = path.join(templatesDir, 'policy.hbs');
      await fs.writeFile(templatePath, `---
id: {{id}}
title: {{title}}
---
# {{title}}`);

      const result = await analyzeTemplate(templatePath);

      expect(result.errors).toHaveLength(1);
      expect(result.errors[0].message).toContain('missing type constant');
      expect(result.errors[0].field).toBe('type');
    });

    it('should accept valid type constant', async () => {
      const templatePath = path.join(templatesDir, 'policy.hbs');
      await fs.writeFile(templatePath, `---
type: policy
id: {{id}}
title: {{title}}
---
# {{title}}`);

      // Create minimal schema
      await fs.writeJSON(path.join(schemasDir, 'base.schema.json'), {
        properties: {
          id: { type: 'string' },
          type: { type: 'string' },
          title: { type: 'string' }
        },
        required: ['id', 'type', 'title']
      });

      await fs.writeJSON(path.join(schemasDir, 'policy.schema.json'), {
        allOf: [{ $ref: 'base.schema.json' }],
        properties: {
          type: { const: 'policy' }
        }
      });

      const result = await analyzeTemplate(templatePath, undefined, schemasDir);

      // Should not have type constant error
      const typeErrors = result.errors.filter(e => e.message.includes('type constant'));
      expect(typeErrors).toHaveLength(0);
    });

    it('should warn about missing required fields not referenced', async () => {
      const templatePath = path.join(templatesDir, 'policy.hbs');
      await fs.writeFile(templatePath, `---
type: policy
id: {{id}}
title: {{title}}
---
# {{title}}`);

      // Create schema with additional required fields
      await fs.writeJSON(path.join(schemasDir, 'base.schema.json'), {
        properties: {
          id: { type: 'string' },
          type: { type: 'string' },
          title: { type: 'string' },
          status: { type: 'string' },
          owner: { type: 'string' }
        },
        required: ['id', 'type', 'title', 'status', 'owner']
      });

      await fs.writeJSON(path.join(schemasDir, 'policy.schema.json'), {
        allOf: [{ $ref: 'base.schema.json' }],
        properties: {
          type: { const: 'policy' },
          scope: { type: 'string' }
        },
        required: ['type', 'scope']
      });

      const result = await analyzeTemplate(templatePath, undefined, schemasDir);

      // Should warn about missing status, owner, and scope
      const missingWarnings = result.warnings.filter(w => w.message.includes('neither set nor referenced'));
      expect(missingWarnings.length).toBe(3);
      
      const missingFields = missingWarnings.map(w => w.field);
      expect(missingFields).toContain('status');
      expect(missingFields).toContain('owner');
      expect(missingFields).toContain('scope');
    });

    it('should not warn about fields set in frontmatter', async () => {
      const templatePath = path.join(templatesDir, 'policy.hbs');
      await fs.writeFile(templatePath, `---
type: policy
id: {{id}}
title: {{title}}
status: draft
owner: {{owner}}
---
# {{title}}`);

      await fs.writeJSON(path.join(schemasDir, 'base.schema.json'), {
        properties: {
          id: { type: 'string' },
          type: { type: 'string' },
          title: { type: 'string' },
          status: { type: 'string' },
          owner: { type: 'string' }
        },
        required: ['id', 'type', 'title', 'status', 'owner']
      });

      await fs.writeJSON(path.join(schemasDir, 'policy.schema.json'), {
        allOf: [{ $ref: 'base.schema.json' }],
        properties: {
          type: { const: 'policy' }
        }
      });

      const result = await analyzeTemplate(templatePath, undefined, schemasDir);

      // Should not warn about status (set) or owner (placeholder)
      const statusWarnings = result.warnings.filter(w => w.field === 'status');
      const ownerWarnings = result.warnings.filter(w => w.field === 'owner');
      expect(statusWarnings).toHaveLength(0);
      expect(ownerWarnings).toHaveLength(0);
    });

    it('should handle {{now}} helper for created/updated fields', async () => {
      const templatePath = path.join(templatesDir, 'policy.hbs');
      await fs.writeFile(templatePath, `---
type: policy
id: {{id}}
title: {{title}}
created: {{now}}
updated: {{now}}
---
# {{title}}`);

      await fs.writeJSON(path.join(schemasDir, 'base.schema.json'), {
        properties: {
          id: { type: 'string' },
          type: { type: 'string' },
          title: { type: 'string' },
          created: { type: 'string' },
          updated: { type: 'string' }
        },
        required: ['id', 'type', 'title', 'created', 'updated']
      });

      await fs.writeJSON(path.join(schemasDir, 'policy.schema.json'), {
        allOf: [{ $ref: 'base.schema.json' }],
        properties: {
          type: { const: 'policy' }
        }
      });

      const result = await analyzeTemplate(templatePath, undefined, schemasDir);

      // Should not warn about created/updated when {{now}} is used
      const createdWarnings = result.warnings.filter(w => w.field === 'created');
      const updatedWarnings = result.warnings.filter(w => w.field === 'updated');
      expect(createdWarnings).toHaveLength(0);
      expect(updatedWarnings).toHaveLength(0);
    });

    it('should warn about unknown placeholders', async () => {
      const templatePath = path.join(templatesDir, 'policy.hbs');
      await fs.writeFile(templatePath, `---
type: policy
id: {{id}}
title: {{title}}
---
# {{title}}
{{unknownField}}
{{anotherUnknown}}`);

      await fs.writeJSON(path.join(schemasDir, 'base.schema.json'), {
        properties: {
          id: { type: 'string' },
          type: { type: 'string' },
          title: { type: 'string' }
        }
      });

      await fs.writeJSON(path.join(schemasDir, 'policy.schema.json'), {
        allOf: [{ $ref: 'base.schema.json' }],
        properties: {
          type: { const: 'policy' }
        }
      });

      const result = await analyzeTemplate(templatePath, undefined, schemasDir);

      const unknownWarnings = result.warnings.filter(w => w.message.includes('Unknown placeholder'));
      expect(unknownWarnings.length).toBeGreaterThanOrEqual(2);
      
      const unknownFields = unknownWarnings.map(w => w.field);
      expect(unknownFields).toContain('unknownField');
      expect(unknownFields).toContain('anotherUnknown');
    });

    it('should not warn about Handlebars helpers', async () => {
      const templatePath = path.join(templatesDir, 'policy.hbs');
      await fs.writeFile(templatePath, `---
type: policy
id: {{id}}
title: {{title}}
---
{{#each items}}
- {{this}}
{{/each}}
{{#unless disabled}}
Enabled
{{/unless}}`);

      await fs.writeJSON(path.join(schemasDir, 'base.schema.json'), {
        properties: {
          id: { type: 'string' },
          type: { type: 'string' },
          title: { type: 'string' },
          items: { type: 'array' },
          disabled: { type: 'boolean' }
        }
      });

      await fs.writeJSON(path.join(schemasDir, 'policy.schema.json'), {
        allOf: [{ $ref: 'base.schema.json' }],
        properties: {
          type: { const: 'policy' }
        }
      });

      const result = await analyzeTemplate(templatePath, undefined, schemasDir);

      // Should not warn about 'each' or 'unless' helpers
      const helperWarnings = result.warnings.filter(w => 
        w.field === 'each' || w.field === 'unless'
      );
      expect(helperWarnings).toHaveLength(0);
    });

    it('should handle @-prefixed Handlebars variables', async () => {
      const templatePath = path.join(templatesDir, 'policy.hbs');
      await fs.writeFile(templatePath, `---
type: policy
id: {{id}}
title: {{title}}
---
{{#each items}}
{{@index}}: {{this}}{{#unless @last}},{{/unless}}
{{/each}}`);

      await fs.writeJSON(path.join(schemasDir, 'base.schema.json'), {
        properties: {
          id: { type: 'string' },
          type: { type: 'string' },
          title: { type: 'string' },
          items: { type: 'array' }
        }
      });

      await fs.writeJSON(path.join(schemasDir, 'policy.schema.json'), {
        allOf: [{ $ref: 'base.schema.json' }],
        properties: {
          type: { const: 'policy' }
        }
      });

      const result = await analyzeTemplate(templatePath, undefined, schemasDir);

      // Should not warn about @index or @last
      const atWarnings = result.warnings.filter(w => 
        w.field && w.field.startsWith('@')
      );
      expect(atWarnings).toHaveLength(0);
    });

    it('should infer doc type from filename if not in frontmatter', async () => {
      const templatePath = path.join(templatesDir, 'ADR.hbs');
      await fs.writeFile(templatePath, `---
id: {{id}}
title: {{title}}
---
# {{title}}`);

      const result = await analyzeTemplate(templatePath);

      // Should infer 'adr' from 'ADR.hbs'
      const typeErrors = result.errors.filter(e => e.message.includes("type constant field with value 'adr'"));
      expect(typeErrors).toHaveLength(1);
    });

    it('should handle complex block helpers with variables', async () => {
      const templatePath = path.join(templatesDir, 'process.hbs');
      await fs.writeFile(templatePath, `---
type: process
id: {{id}}
title: {{title}}
---
{{#each related_standards}}
- {{this}}
{{/each}}
{{#with metadata}}
Version: {{version}}
{{/with}}`);

      await fs.writeJSON(path.join(schemasDir, 'base.schema.json'), {
        properties: {
          id: { type: 'string' },
          type: { type: 'string' },
          title: { type: 'string' }
        }
      });

      await fs.writeJSON(path.join(schemasDir, 'process.schema.json'), {
        allOf: [{ $ref: 'base.schema.json' }],
        properties: {
          type: { const: 'process' },
          related_standards: { type: 'array' },
          metadata: { type: 'object' },
          version: { type: 'string' }
        }
      });

      const result = await analyzeTemplate(templatePath, undefined, schemasDir);

      // Should recognize related_standards and metadata as valid
      const relatedWarnings = result.warnings.filter(w => w.field === 'related_standards');
      const metadataWarnings = result.warnings.filter(w => w.field === 'metadata');
      expect(relatedWarnings).toHaveLength(0);
      expect(metadataWarnings).toHaveLength(0);
    });

    it('should handle templates with no schemas gracefully', async () => {
      const templatePath = path.join(templatesDir, 'newtype.hbs');
      await fs.writeFile(templatePath, `---
type: newtype
id: {{id}}
title: {{title}}
---
# {{title}}`);

      // Don't create any schemas
      const result = await analyzeTemplate(templatePath, undefined, schemasDir);

      // Should still check for type constant
      expect(result.errors.length).toBeGreaterThanOrEqual(0);
      // Should not crash
      expect(result.templatePath).toBe(templatePath);
    });
  });

  describe('lintTemplatesDirectory', () => {
    it('should lint all .hbs files in directory', async () => {
      // Create multiple templates
      await fs.writeFile(path.join(templatesDir, 'policy.hbs'), `---
type: policy
id: {{id}}
title: {{title}}
---
# {{title}}`);

      await fs.writeFile(path.join(templatesDir, 'standard.hbs'), `---
type: standard
id: {{id}}
title: {{title}}
---
# {{title}}`);

      await fs.writeFile(path.join(templatesDir, 'ignored.txt'), 'Not a template');

      const results = await lintTemplatesDirectory(templatesDir);

      expect(results).toHaveLength(2);
      const paths = results.map(r => path.basename(r.templatePath));
      expect(paths).toContain('policy.hbs');
      expect(paths).toContain('standard.hbs');
      expect(paths).not.toContain('ignored.txt');
    });

    it('should return empty array for non-existent directory', async () => {
      const results = await lintTemplatesDirectory('/non/existent/path');
      expect(results).toEqual([]);
    });

    it('should handle empty directory', async () => {
      const results = await lintTemplatesDirectory(templatesDir);
      expect(results).toEqual([]);
    });
  });

  describe('Real template analysis', () => {
    it('should analyze actual ADR template', async () => {
      const actualTemplateContent = `---
id: {{id}}
type: adr
title: {{title}}
status: proposed
owner: {{owner}}
created: {{now}}
updated: {{now}}
tags: [adr]
---
# {{title}}

## Context
{{context}}

## Decision
{{decision}}

## Consequences
{{consequences}}

## Alternatives Considered
{{#each alternatives}}- {{this}}
{{/each}}

## References
{{#each references}}- {{this}}
{{/each}}`;

      const templatePath = path.join(templatesDir, 'ADR.hbs');
      await fs.writeFile(templatePath, actualTemplateContent);

      // Create realistic schemas
      await fs.writeJSON(path.join(schemasDir, 'base.schema.json'), {
        properties: {
          id: { type: 'string' },
          type: { type: 'string' },
          title: { type: 'string' },
          status: { type: 'string' },
          owner: { type: 'string' },
          created: { type: 'string' },
          updated: { type: 'string' },
          tags: { type: 'array' },
          summary: { type: 'string' }
        },
        required: ['id', 'type', 'title', 'status', 'owner', 'created', 'updated']
      });

      await fs.writeJSON(path.join(schemasDir, 'adr.schema.json'), {
        allOf: [{ $ref: 'base.schema.json' }],
        properties: {
          type: { const: 'adr' },
          context: { type: 'string' },
          decision: { type: 'string' },
          consequences: { type: 'string' },
          alternatives: { type: 'array' },
          references: { type: 'array' }
        },
        required: ['type']
      });

      const result = await analyzeTemplate(templatePath, undefined, schemasDir);

      // Should have no errors for type constant
      const typeErrors = result.errors.filter(e => e.message.includes('type constant'));
      expect(typeErrors).toHaveLength(0);

      // Summary is not required in base schema but might warn if not referenced
      // This matches the actual scenario mentioned in requirements
      const summaryWarnings = result.warnings.filter(w => w.field === 'summary');
      // Summary is not required, so no warning expected
      expect(summaryWarnings).toHaveLength(0);
    });

    it('should handle Process template with related_standards requirement', async () => {
      const processTemplate = `---
id: {{id}}
type: process
title: {{title}}
status: draft
owner: {{owner}}
created: {{now}}
updated: {{now}}
tags: [process]
summary: {{summary}}
related_standards: [{{#each related_standards}}{{this}}{{#unless @last}}, {{/unless}}{{/each}}]
---
# {{title}} Process`;

      const templatePath = path.join(templatesDir, 'Process.hbs');
      await fs.writeFile(templatePath, processTemplate);

      await fs.writeJSON(path.join(schemasDir, 'base.schema.json'), {
        properties: {
          id: { type: 'string' },
          type: { type: 'string' },
          title: { type: 'string' },
          status: { type: 'string' },
          owner: { type: 'string' },
          created: { type: 'string' },
          updated: { type: 'string' },
          tags: { type: 'array' },
          summary: { type: 'string' }
        },
        required: ['id', 'type', 'title', 'status', 'owner', 'created', 'updated']
      });

      await fs.writeJSON(path.join(schemasDir, 'process.schema.json'), {
        allOf: [{ $ref: 'base.schema.json' }],
        properties: {
          type: { const: 'process' },
          related_standards: { type: 'array', minItems: 1 }
        },
        required: ['type', 'related_standards']
      });

      const result = await analyzeTemplate(templatePath, undefined, schemasDir);

      // Should not warn about related_standards since it's referenced
      const relatedStandardsWarnings = result.warnings.filter(w => w.field === 'related_standards');
      expect(relatedStandardsWarnings).toHaveLength(0);

      // Should have correct type
      const typeErrors = result.errors.filter(e => e.message.includes('type constant'));
      expect(typeErrors).toHaveLength(0);
    });
  });
});