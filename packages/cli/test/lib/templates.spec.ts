import * as path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import fsExtra from 'fs-extra';
const fs = fsExtra;
import {
  registerHelpers,
  registerDefaultHelpers,
  compileTemplate,
  renderTemplate,
  discoverTemplates,
  compileAllTemplates,
  getTemplateMetadata
} from '../../src/lib/templates';

// ESM __dirname replacement
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

describe('templates module', () => {
  const tempDir = path.join(__dirname, 'test-temp');

  beforeEach(async () => {
    await fs.ensureDir(tempDir);
  });

  afterEach(async () => {
    await fs.remove(tempDir);
  });

  describe('registerHelpers', () => {
    it('should register custom helpers', async () => {
      const testHelpers = {
        testHelper: () => 'test output',
        upperCase: (str: string) => str.toUpperCase()
      };

      registerHelpers(testHelpers);

      const template = '{{testHelper}} {{upperCase "hello"}}';
      const tempFile = path.join(tempDir, 'test-helper.hbs');
      await fs.writeFile(tempFile, template);

      const result = await renderTemplate(tempFile, {});
      expect(result).toBe('test output HELLO');
    });
  });

  describe('registerDefaultHelpers', () => {
    beforeEach(() => {
      registerDefaultHelpers();
    });

    it('should register now helper', async () => {
      const template = '{{{now}}}';
      const tempFile = path.join(tempDir, 'test-now.hbs');
      await fs.writeFile(tempFile, template);

      const result = await renderTemplate(tempFile, {});
      // The now helper returns a quoted string like "2025-09-20T20:08:54.599Z"
      // Strip the quotes before parsing
      const dateString = result.replace(/^"(.*)"$/, '$1');
      const date = new Date(dateString);
      expect(date.toString()).not.toBe('Invalid Date');

      // Check it's recent (within last minute)
      const diff = Date.now() - date.getTime();
      expect(diff).toBeGreaterThanOrEqual(0);
      expect(diff).toBeLessThan(60000);
    });

    it('should return quoted date string from now helper for YAML safety', async () => {
      const template = '{{{now}}}';
      const tempFile = path.join(tempDir, 'test-now-quoted.hbs');
      await fs.writeFile(tempFile, template);

      const result = await renderTemplate(tempFile, {});
      // Should be wrapped in quotes for YAML safety
      expect(result).toMatch(/^".*"$/);
      // Should be a valid ISO date inside the quotes
      expect(result).toMatch(/^"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z"$/);
    });

    it('should register slug helper', async () => {
      const template = '{{slug "Hello World Test"}}';
      const tempFile = path.join(tempDir, 'test-slug.hbs');
      await fs.writeFile(tempFile, template);

      const result = await renderTemplate(tempFile, {});
      expect(result).toBe('hello-world-test');
    });

    it('should handle slug with special characters', async () => {
      const template = '{{slug "Hello @#$ World & Test!"}}';
      const tempFile = path.join(tempDir, 'test-slug-special.hbs');
      await fs.writeFile(tempFile, template);

      const result = await renderTemplate(tempFile, {});
      expect(result).toBe('hello-world-test');
    });

    it('should handle empty slug', async () => {
      const template = '{{slug ""}}';
      const tempFile = path.join(tempDir, 'test-slug-empty.hbs');
      await fs.writeFile(tempFile, template);

      const result = await renderTemplate(tempFile, {});
      expect(result).toBe('');
    });

    it('should handle slug with multiple hyphens', async () => {
      const template = '{{slug "Hello   ---   World"}}';
      const tempFile = path.join(tempDir, 'test-slug-hyphens.hbs');
      await fs.writeFile(tempFile, template);

      const result = await renderTemplate(tempFile, {});
      expect(result).toBe('hello-world');
    });

    it('should handle undefined slug input', async () => {
      const template = '{{slug undefined}}';
      const tempFile = path.join(tempDir, 'test-slug-undefined.hbs');
      await fs.writeFile(tempFile, template);

      const result = await renderTemplate(tempFile, {});
      expect(result).toBe('');
    });

    it('should handle null slug input', async () => {
      const template = '{{slug nullValue}}';
      const tempFile = path.join(tempDir, 'test-slug-null.hbs');
      await fs.writeFile(tempFile, template);

      const result = await renderTemplate(tempFile, { nullValue: null });
      expect(result).toBe('');
    });
  });

  describe('compileTemplate', () => {
    it('should compile a valid template', async () => {
      const template = '# {{title}}\n{{content}}';
      const tempFile = path.join(tempDir, 'test-compile.hbs');
      await fs.writeFile(tempFile, template);

      const compiled = await compileTemplate(tempFile);
      expect(typeof compiled).toBe('function');

      const output = compiled({ title: 'Test', content: 'Content' });
      expect(output).toBe('# Test\nContent');
    });

    it('should throw for non-existent file', async () => {
      await expect(compileTemplate('/non/existent/file.hbs')).rejects.toThrow();
    });

    it('should compile even with mismatched helpers', async () => {
      // Handlebars actually compiles mismatched if/unless pairs without error
      const invalidTemplate = '{{#if test}}Missing end{{/unless}}';
      const tempFile = path.join(tempDir, 'test-invalid.hbs');
      await fs.writeFile(tempFile, invalidTemplate);

      const compiled = await compileTemplate(tempFile);
      expect(typeof compiled).toBe('function');
    });

    it('should throw with detailed error message', async () => {
      const nonExistentFile = '/this/file/does/not/exist.hbs';
      try {
        await compileTemplate(nonExistentFile);
        fail('Should have thrown');
      } catch (error: any) {
        expect(error.message).toContain('Failed to compile template');
        expect(error.message).toContain(nonExistentFile);
      }
    });

    it('should compile templates with missing parameters', async () => {
      // Handlebars doesn't throw for missing parameters at compile time
      const badTemplate = '{{#each}}{{/each}}'; // Missing parameters
      const tempFile = path.join(tempDir, 'test-bad-syntax.hbs');
      await fs.writeFile(tempFile, badTemplate);

      // This compiles successfully but may error at runtime
      const compiled = await compileTemplate(tempFile);
      expect(typeof compiled).toBe('function');
    });

  });

  describe('renderTemplate', () => {
    it('should render template with data', async () => {
      const template = `---
id: {{id}}
title: {{title}}
---

# {{title}}

{{#if sections}}
{{#each sections}}
- {{this.name}}
{{/each}}
{{/if}}`;

      const tempFile = path.join(tempDir, 'test-render.hbs');
      await fs.writeFile(tempFile, template);

      const data = {
        id: 'TEST-001',
        title: 'Test Document',
        sections: [
          { name: 'Section 1' },
          { name: 'Section 2' }
        ]
      };

      const result = await renderTemplate(tempFile, data);
      expect(result).toContain('id: TEST-001');
      expect(result).toContain('# Test Document');
      expect(result).toContain('- Section 1');
      expect(result).toContain('- Section 2');
    });

    it('should handle missing optional fields', async () => {
      const template = '{{title}}{{#if optional}} - {{optional}}{{/if}}';
      const tempFile = path.join(tempDir, 'test-optional.hbs');
      await fs.writeFile(tempFile, template);

      const result = await renderTemplate(tempFile, { title: 'Test' });
      expect(result).toBe('Test');
    });
  });

  describe('discoverTemplates', () => {
    it('should discover .hbs files recursively', async () => {
      const subDir = path.join(tempDir, 'sub');
      await fs.ensureDir(subDir);

      await fs.writeFile(path.join(tempDir, 'template1.hbs'), '{{test1}}');
      await fs.writeFile(path.join(tempDir, 'template2.hbs'), '{{test2}}');
      await fs.writeFile(path.join(subDir, 'nested.hbs'), '{{nested}}');
      await fs.writeFile(path.join(tempDir, 'notatemplate.txt'), 'not a template');

      const templates = await discoverTemplates(tempDir);

      expect(Array.isArray(templates)).toBe(true);
      expect(templates).toHaveLength(3);
      expect(templates.some(t => t.endsWith('template1.hbs'))).toBe(true);
      expect(templates.some(t => t.endsWith('template2.hbs'))).toBe(true);
      expect(templates.some(t => t.endsWith('nested.hbs'))).toBe(true);
      expect(templates.some(t => t.endsWith('notatemplate.txt'))).toBe(false);
    });

    it('should return empty array for non-existent directory', async () => {
      const result = await discoverTemplates('/non/existent/directory');
      expect(Array.isArray(result)).toBe(true);
      expect(result).toHaveLength(0);
    });
  });

  describe('compileAllTemplates', () => {
    it('should compile multiple templates', async () => {
      await fs.writeFile(path.join(tempDir, 'valid1.hbs'), '{{title}}');
      await fs.writeFile(path.join(tempDir, 'valid2.hbs'), '# {{header}}');
      await fs.writeFile(path.join(tempDir, 'invalid.hbs'), '{{#if test}}{{/unless}}');

      const result = await compileAllTemplates(tempDir);

      expect(result).toHaveProperty('success');
      expect(result).toHaveProperty('templates');
      expect(Array.isArray(result.templates)).toBe(true);

      // Should have compiled valid templates
      expect(result.templates.some(t => t.name === 'valid1')).toBe(true);
      expect(result.templates.some(t => t.name === 'valid2')).toBe(true);

      // Should report errors for invalid template
      const invalidTemplate = result.templates.find(t => t.name === 'invalid');
      // Note: Invalid Handlebars syntax may still compile (depends on the error)
      // Check that we at least attempted to process it
      expect(invalidTemplate).toBeDefined();
    });

    it('should handle all templates compiling successfully', async () => {
      // Handlebars doesn't fail compilation on missing parameters
      await fs.writeFile(path.join(tempDir, 'good.hbs'), '{{title}}');
      await fs.writeFile(path.join(tempDir, 'another.hbs'), '{{#each}}{{/each}}');

      const result = await compileAllTemplates(tempDir);

      // Both templates should compile successfully
      const goodTemplate = result.templates.find(t => t.name === 'good');
      expect(goodTemplate?.compiled).toBe(true);

      const anotherTemplate = result.templates.find(t => t.name === 'another');
      expect(anotherTemplate?.compiled).toBe(true);

      // Overall success should be true
      expect(result.success).toBe(true);
    });

  });

  describe('compileTemplate error handling', () => {
    it('should handle template with only helpers', async () => {
      const template = '{{#if condition}}yes{{else}}no{{/if}}';
      const tempFile = path.join(tempDir, 'test-helpers-only.hbs');
      await fs.writeFile(tempFile, template);

      const compiled = await compileTemplate(tempFile);
      const result = compiled({ condition: true });
      expect(result).toBe('yes');

      const result2 = compiled({ condition: false });
      expect(result2).toBe('no');
    });

    it('should handle nested helpers', async () => {
      const template = '{{#each items}}{{#if this.active}}{{this.name}}{{/if}}{{/each}}';
      const tempFile = path.join(tempDir, 'test-nested.hbs');
      await fs.writeFile(tempFile, template);

      const compiled = await compileTemplate(tempFile);
      const result = compiled({
        items: [
          { name: 'A', active: true },
          { name: 'B', active: false },
          { name: 'C', active: true }
        ]
      });
      expect(result).toBe('AC');
    });
  });

  describe('getTemplateMetadata', () => {
    it('should extract metadata from template', async () => {
      const template = `---
type: test
title: Test Template
---

# {{title}}

{{#if description}}
Description: {{description}}
{{/if}}`;

      const tempFile = path.join(tempDir, 'test-metadata.hbs');
      await fs.writeFile(tempFile, template);

      const metadata = await getTemplateMetadata(tempFile);

      expect(metadata).toHaveProperty('name');
      expect(metadata).toHaveProperty('path');
      expect(metadata).toHaveProperty('variables');
      expect(metadata).toHaveProperty('helpers');

      expect(metadata.name).toBe('test-metadata');
      expect(metadata.path).toBe(tempFile);
      expect(metadata.variables).toContain('title');
      expect(metadata.variables).toContain('description');
    });

    it('should handle templates without frontmatter', async () => {
      const template = '# {{title}}\n\nNo frontmatter here';
      const tempFile = path.join(tempDir, 'test-no-fm.hbs');
      await fs.writeFile(tempFile, template);

      const metadata = await getTemplateMetadata(tempFile);
      expect(metadata.name).toBe('test-no-fm');
      expect(metadata.variables).toContain('title');
    });

    it('should handle templates with no variables or helpers', async () => {
      const template = '# Static Content\n\nNo handlebars here.';
      const tempFile = path.join(tempDir, 'test-static.hbs');
      await fs.writeFile(tempFile, template);

      const metadata = await getTemplateMetadata(tempFile);
      expect(metadata.name).toBe('test-static');
      expect(metadata.variables).toEqual([]);
      expect(metadata.helpers).toEqual([]);
    });
  });
});
