import Handlebars from 'handlebars';
import fsExtra from 'fs-extra';
const fs = fsExtra;
import * as path from 'path';
import glob from 'fast-glob';

// Store the Handlebars instance for helper registration
const handlebars = Handlebars.create();

/**
 * Register custom Handlebars helpers
 */
export function registerHelpers(helpers: Record<string, Handlebars.HelperDelegate>): void {
  Object.entries(helpers).forEach(([name, helper]) => {
    handlebars.registerHelper(name, helper);
  });
}

/**
 * Register default helpers for Synapse templates
 */
export function registerDefaultHelpers(): void {
  // Register 'now' helper for current timestamp
  handlebars.registerHelper('now', () => {
    // Return quoted timestamp for YAML frontmatter
    return `"${new Date().toISOString()}"`;
  });

  // Register 'slug' helper to convert text to slug format
  handlebars.registerHelper('slug', (text: string) => {
    if (!text) return '';
    return text
      .toLowerCase()
      .replace(/[^\w\s-]/g, '') // Remove special characters
      .replace(/\s+/g, '-')      // Replace spaces with hyphens
      .replace(/-+/g, '-')       // Replace multiple hyphens with single
      .trim();
  });

  // Note: {{#each}} and {{#unless}} are Handlebars built-ins
  // Wikilink syntax [[...]] is handled as plain text in templates
}

/**
 * Compile a single Handlebars template from file path
 */
export async function compileTemplate(templatePath: string): Promise<HandlebarsTemplateDelegate> {
  try {
    const templateContent = await fs.readFile(templatePath, 'utf-8');
    return handlebars.compile(templateContent);
  } catch (error) {
    throw new Error(`Failed to compile template ${templatePath}: ${(error as Error).message}`);
  }
}

/**
 * Render a template with provided data
 */
export async function renderTemplate(
  templatePath: string,
  data: Record<string, any>
): Promise<string> {
  const template = await compileTemplate(templatePath);
  return template(data);
}

/**
 * Discover all .hbs template files in a directory
 */
export async function discoverTemplates(baseDir: string): Promise<string[]> {
  const pattern = path.join(baseDir, '**/*.hbs');
  const templates = await glob(pattern, {
    absolute: true,
    onlyFiles: true,
  });
  return templates;
}

/**
 * Compile and validate all templates, returning a report
 */
export async function compileAllTemplates(
  templateDir: string
): Promise<{
  success: boolean;
  templates: Array<{
    path: string;
    name: string;
    compiled: boolean;
    error?: string;
  }>;
}> {
  // Register default helpers before compilation
  registerDefaultHelpers();

  const templates = await discoverTemplates(templateDir);
  const results = await Promise.all(
    templates.map(async (templatePath) => {
      const name = path.basename(templatePath, '.hbs');
      try {
        await compileTemplate(templatePath);
        return {
          path: templatePath,
          name,
          compiled: true,
        };
      } catch (error) {
        return {
          path: templatePath,
          name,
          compiled: false,
          error: (error as Error).message,
        };
      }
    })
  );

  const success = results.every(r => r.compiled);
  return { success, templates: results };
}

/**
 * Get template metadata including required fields from analysis
 */
export async function getTemplateMetadata(templatePath: string): Promise<{
  name: string;
  path: string;
  variables: string[];
  helpers: string[];
}> {
  const content = await fs.readFile(templatePath, 'utf-8');
  const name = path.basename(templatePath, '.hbs');

  // Extract variables (simple regex for {{variable}} patterns)
  const variableMatches = content.match(/\{\{(?!#|\/|else)([^}]+)\}\}/g) || [];
  const variables = [...new Set(
    variableMatches
      .map(m => m.replace(/\{\{|\}\}/g, '').trim())
      .filter(v => !v.startsWith('this') && !v.startsWith('@'))
  )];

  // Extract helpers ({{#helper}} patterns)
  const helperMatches = content.match(/\{\{#([^}\s]+)/g) || [];
  const helpers = [...new Set(
    helperMatches.map(m => m.replace('{{#', ''))
  )];

  return {
    name,
    path: templatePath,
    variables,
    helpers,
  };
}

export default {
  compileTemplate,
  renderTemplate,
  registerHelpers,
  registerDefaultHelpers,
  discoverTemplates,
  compileAllTemplates,
  getTemplateMetadata,
};
