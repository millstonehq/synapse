import fsExtra from 'fs-extra';
const fs = fsExtra;
import * as path from 'path';
import { loadSchema, type JSONSchema } from './schemas.js';
import { isKnownDocType } from './type-registry.js';
import { extractFrontmatter, extractPlaceholders, parseFrontmatterKeys } from './markdown.js';

// Default Handlebars helpers that are always available
const DEFAULT_HELPERS = ['now', 'each', 'unless', 'if', 'with'];

export interface TemplateLintIssue {
  type: 'error' | 'warning';
  message: string;
  field?: string;
  line?: number;
}

export interface TemplateLintResult {
  templatePath: string;
  errors: TemplateLintIssue[];
  warnings: TemplateLintIssue[];
}

// Default Handlebars helpers that are always available




/**
 * Gets the document type from the template path or frontmatter
 */
function getDocTypeFromTemplate(templatePath: string, frontmatter: string): string | null {
  // Try to extract from frontmatter first
  const typeMatch = frontmatter.match(/^type:\s*([a-zA-Z_]+)/m);
  if (typeMatch && isKnownDocType(typeMatch[1])) {
    return typeMatch[1];
  }

  // Try to infer from filename
  const basename = path.basename(templatePath, '.hbs').toLowerCase();
  if (isKnownDocType(basename)) {
    return basename;
  }

  return null;
}

/**
 * Gets required fields from the merged schema
 */
async function getRequiredFields(
  type: string,
  schemaDir?: string
): Promise<Set<string>> {
  const requiredFields = new Set<string>();
  
  // For custom schema directories (like in tests), bypass loadSchema to avoid caching issues
  if (schemaDir && !schemaDir.includes('content/schemas')) {
    try {
      // Load base schema
      const baseSchemaPath = path.join(schemaDir, 'base.schema.json');
      if (await fs.pathExists(baseSchemaPath)) {
        const baseSchema = await fs.readJSON(baseSchemaPath);
        if (baseSchema.required && Array.isArray(baseSchema.required)) {
          baseSchema.required.forEach((field: string) => requiredFields.add(field));
        }
      }
      
      // Load type-specific schema
      const typeSchemaPath = path.join(schemaDir, `${type}.schema.json`);
      if (await fs.pathExists(typeSchemaPath)) {
        const typeSchema = await fs.readJSON(typeSchemaPath);
        if (typeSchema.required && Array.isArray(typeSchema.required)) {
          typeSchema.required.forEach((field: string) => requiredFields.add(field));
        }
      }
    } catch (error) {
      // Schema loading failed
    }
    return requiredFields;
  }
  
  // For production schemas, use the cached loadSchema function
  try {
    const schema = await loadSchema(type, schemaDir);
    
    if (schema.required && Array.isArray(schema.required)) {
      schema.required.forEach((field: string) => requiredFields.add(field));
    }
  } catch (error) {
    // Schema might not exist yet
  }
  
  return requiredFields;
}

/**
 * Gets all valid properties from the merged schema
 */
async function getAllSchemaProperties(
  type: string,
  schemaDir?: string
): Promise<Set<string>> {
  const allProperties = new Set<string>();
  
  // For custom schema directories (like in tests), bypass loadSchema to avoid caching issues
  if (schemaDir && !schemaDir.includes('content/schemas')) {
    try {
      // Load base schema properties
      const baseSchemaPath = path.join(schemaDir, 'base.schema.json');
      if (await fs.pathExists(baseSchemaPath)) {
        const baseSchema = await fs.readJSON(baseSchemaPath);
        if (baseSchema.properties) {
          Object.keys(baseSchema.properties).forEach(prop => allProperties.add(prop));
        }
      }
      
      // Load type-specific schema properties
      const typeSchemaPath = path.join(schemaDir, `${type}.schema.json`);
      if (await fs.pathExists(typeSchemaPath)) {
        const typeSchema = await fs.readJSON(typeSchemaPath);
        if (typeSchema.properties) {
          Object.keys(typeSchema.properties).forEach(prop => allProperties.add(prop));
        }
      }
    } catch (error) {
      // Schema loading failed
    }
    return allProperties;
  }
  
  // For production schemas, use the cached loadSchema function
  try {
    const schema = await loadSchema(type, schemaDir);
    
    if (schema.properties) {
      Object.keys(schema.properties).forEach(prop => allProperties.add(prop));
    }
  } catch (error) {
    // Schema might not exist yet
  }
  
  return allProperties;
}

/**
 * Analyzes a template file and checks it against its schema
 */
export async function analyzeTemplate(
  templatePath: string,
  schema?: JSONSchema,
  schemaDir?: string
): Promise<TemplateLintResult> {
  const errors: TemplateLintIssue[] = [];
  const warnings: TemplateLintIssue[] = [];
  
  try {
    // Read template content
    const templateContent = await fs.readFile(templatePath, 'utf-8');
    
    // Extract frontmatter
    const { frontmatter, body, startLine } = extractFrontmatter(templateContent);
    
    if (!frontmatter) {
      errors.push({
        type: 'error',
        message: 'Template missing frontmatter block'
      });
      return { templatePath, errors, warnings };
    }
    
    // Get document type
    const docType = getDocTypeFromTemplate(templatePath, frontmatter);
    
    if (!docType) {
      errors.push({
        type: 'error',
        message: 'Unable to determine document type from template'
      });
      return { templatePath, errors, warnings };
    }
    
    // Check for type const in frontmatter
    const typePattern = new RegExp(`^type:\\s*${docType}\\s*$`, 'm');
    if (!typePattern.test(frontmatter)) {
      errors.push({
        type: 'error',
        message: `Frontmatter missing type constant field with value '${docType}'`,
        field: 'type',
        line: startLine
      });
    }
    
    // Parse frontmatter keys
    const frontmatterKeys = parseFrontmatterKeys(frontmatter);
    
    // Extract all placeholders from entire template
    const allPlaceholders = new Set<string>([
      ...extractPlaceholders(frontmatter),
      ...extractPlaceholders(body)
    ]);
    
    // Get required fields from schema
    const requiredFields = await getRequiredFields(docType, schemaDir);
    
    // Check for missing required fields
    for (const requiredField of requiredFields) {
      // Skip 'type' as it should be a constant
      if (requiredField === 'type') continue;
      
      // Check if field is in frontmatter or referenced as placeholder
      if (!frontmatterKeys.has(requiredField) && !allPlaceholders.has(requiredField)) {
        // Special case: 'now' helper can satisfy created/updated fields
        if ((requiredField === 'created' || requiredField === 'updated') && 
            allPlaceholders.has('now')) {
          continue;
        }
        
        warnings.push({
          type: 'warning',
          message: `Required schema property '${requiredField}' is neither set nor referenced in template`,
          field: requiredField
        });
      }
    }
    
    // Get all valid schema properties
    const allSchemaProperties = await getAllSchemaProperties(docType, schemaDir);
    
    // Check for unknown placeholders
    for (const placeholder of allPlaceholders) {
      // Skip if it's a known helper
      if (DEFAULT_HELPERS.includes(placeholder)) continue;
      
      // Skip @-prefixed variables (Handlebars built-ins like @last, @index)
      if (placeholder.startsWith('@')) continue;
      
      // Skip 'this' keyword
      if (placeholder === 'this') continue;
      
      // Check if it's a valid schema property
      if (!allSchemaProperties.has(placeholder)) {
        warnings.push({
          type: 'warning',
          message: `Unknown placeholder '${placeholder}' not found in schema properties or registered helpers`,
          field: placeholder
        });
      }
    }
    
  } catch (error) {
    errors.push({
      type: 'error',
      message: `Failed to analyze template: ${error instanceof Error ? error.message : String(error)}`
    });
  }
  
  return {
    templatePath,
    errors,
    warnings
  };
}

/**
 * Lint all templates in a directory
 */
export async function lintTemplatesDirectory(
  templatesDir: string,
  schemaDir?: string
): Promise<TemplateLintResult[]> {
  const results: TemplateLintResult[] = [];
  
  try {
    const templateFiles = await fs.readdir(templatesDir);
    
    for (const file of templateFiles) {
      if (file.endsWith('.hbs')) {
        const templatePath = path.join(templatesDir, file);
        const result = await analyzeTemplate(templatePath, undefined, schemaDir);
        results.push(result);
      }
    }
  } catch (error) {
    // Directory might not exist
  }
  
  return results;
}