import Ajv, { ErrorObject, JSONSchemaType } from 'ajv';
import addFormats from 'ajv-formats';
import fsExtra from 'fs-extra';
const fs = fsExtra;
import * as path from 'path';
import { createRequire } from 'module';
import { isKnownDocType, getDocTypes } from './type-registry.js';

// Re-export isKnownDocType for backward compatibility
export { isKnownDocType } from './type-registry.js';

// Type for JSON Schema (using any for flexibility with schema structure)
export type JSONSchema = any;

// Cache for compiled schemas to improve performance
const schemaCache = new Map<string, JSONSchema>();

/**
 * Resolve the frontmatter schema directory using a cascade:
 * 1. Local project override: {projectRoot}/schemas/frontmatter/
 * 2. @millstone/synapse-schemas npm package
 * 3. Error with helpful message
 */
function getDefaultSchemaDir(): string {
  // Priority 1: Local project override
  const localPaths = [
    path.resolve(process.cwd(), 'schemas/frontmatter'),
    path.resolve(process.cwd(), '../schemas/frontmatter'),
    path.resolve(process.cwd(), '../../schemas/frontmatter'),
  ];

  for (const schemaPath of localPaths) {
    if (fs.existsSync(schemaPath)) {
      try {
        const files = fs.readdirSync(schemaPath);
        const hasSchemas = files.some(f => f.endsWith('.schema.json'));
        if (hasSchemas) {
          return schemaPath;
        }
      } catch {
        continue;
      }
    }
  }

  // Priority 2: @millstone/synapse-schemas package
  try {
    const require = createRequire(import.meta.url);
    const pkgPath = require.resolve('@millstone/synapse-schemas/package.json');
    const pkgDir = path.dirname(pkgPath);
    const frontmatterDir = path.join(pkgDir, 'frontmatter');
    if (fs.existsSync(frontmatterDir)) {
      return frontmatterDir;
    }
  } catch {
    // Package not installed
  }

  // Priority 3: Error with helpful message
  throw new Error(
    'Could not find frontmatter schemas. Either place schemas in {projectRoot}/schemas/frontmatter/ ' +
    'or install the @millstone/synapse-schemas package: npm install @millstone/synapse-schemas'
  );
}

/**
 * Load a schema for a specific document type
 * Resolves $ref references to base.schema.json automatically
 */
export async function loadSchema(type: string, dir?: string): Promise<JSONSchema> {
  const schemaDir = dir || getDefaultSchemaDir();
  const schemaPath = path.join(schemaDir, `${type}.schema.json`);
  const cacheKey = `${schemaDir}:${type}`;

  // Return cached schema if available
  if (schemaCache.has(cacheKey)) {
    return schemaCache.get(cacheKey)!;
  }

  try {
    // Read the schema file
    const schemaContent = await fs.readFile(schemaPath, 'utf-8');
    const schema = JSON.parse(schemaContent);

    // If schema has allOf with $ref to base.schema.json, resolve it
    if (schema.allOf && Array.isArray(schema.allOf)) {
      const resolvedAllOf = await Promise.all(
        schema.allOf.map(async (item: any) => {
          if (item.$ref === 'base.schema.json') {
            const basePath = path.join(schemaDir, 'base.schema.json');
            const baseContent = await fs.readFile(basePath, 'utf-8');
            return JSON.parse(baseContent);
          }
          return item;
        })
      );

      // Merge base schema properties with type-specific schema
      const mergedSchema = {
        ...schema,
        properties: {
          ...resolvedAllOf[0]?.properties || {},
          ...schema.properties || {}
        },
        required: [
          ...(resolvedAllOf[0]?.required || []),
          ...(schema.required || [])
        ].filter((v, i, a) => a.indexOf(v) === i) // Remove duplicates
      };

      // Remove allOf since we've resolved it
      delete mergedSchema.allOf;

      schemaCache.set(cacheKey, mergedSchema);
      return mergedSchema;
    }

    // Cache and return schema as-is if no allOf
    schemaCache.set(cacheKey, schema);
    return schema;

  } catch (error) {
    if ((error as any).code === 'ENOENT') {
      throw new Error(`Schema file not found for type '${type}' at path: ${schemaPath}`);
    }
    throw new Error(`Failed to load schema for type '${type}': ${(error as Error).message}`);
  }
}

/**
 * List all available schema types in the schema directory
 */
export async function listSchemas(dir?: string): Promise<string[]> {
  const schemaDir = dir || getDefaultSchemaDir();

  try {
    const files = await fs.readdir(schemaDir);

    // Filter for .schema.json files and extract type names
    const schemaTypes = files
      .filter(file => file.endsWith('.schema.json') && file !== 'base.schema.json')
      .map(file => file.replace('.schema.json', ''))
      .sort();

    return schemaTypes;

  } catch (error) {
    if ((error as any).code === 'ENOENT') {
      throw new Error(`Schema directory not found: ${schemaDir}`);
    }
    throw new Error(`Failed to list schemas: ${(error as Error).message}`);
  }
}

/**
 * Validate frontmatter data against a JSON schema
 */
export function validateFrontmatter(
  data: any,
  schema: JSONSchema
): { valid: boolean; errors?: Array<{ path: string; message: string }> } {
  // Create a temporary Ajv instance for validation
  // Remove the $schema property to avoid draft version conflicts
  const cleanSchema = { ...schema };
  delete cleanSchema.$schema;
  delete cleanSchema.$id;

  const ajv = new Ajv({
    allErrors: true,
    strict: false,
    validateSchema: false // Don't validate the schema itself
  });

  // Add format validation support
  addFormats(ajv);

  try {
    const validate = ajv.compile(cleanSchema);
    const valid = validate(data);

    if (valid) {
      return { valid: true };
    } else {
      // Format errors to be more human-readable
      const formattedErrors = (validate.errors || []).map(error => {
        const path = error.instancePath || '/';
        let message = error.message || 'validation error';

        // Add more context for specific error types
        if (error.keyword === 'required') {
          const missingProp = (error.params as any).missingProperty;
          message = `missing required property '${missingProp}'`;
        } else if (error.keyword === 'type') {
          const expectedType = (error.params as any).type;
          message = `must be ${expectedType}`;
        } else if (error.keyword === 'const') {
          const expectedValue = (error.params as any).allowedValue;
          message = `must be equal to constant '${expectedValue}'`;
        }

        return { path, message };
      });

      return {
        valid: false,
        errors: formattedErrors
      };
    }
  } catch (error) {
    // If compilation fails, return as validation error
    return {
      valid: false,
      errors: [{
        path: '/',
        message: `Schema compilation failed: ${(error as Error).message}`
      }]
    };
  }
}

/**
 * Validate that all expected document types have schemas
 * Returns an object with validation results
 */
export async function validateSchemasCoverage(dir?: string): Promise<{
  success: boolean;
  coverage: {
    expected: string[];
    found: string[];
    missing: string[];
    extra: string[];
  };
  errors: string[];
}> {
  // Use dynamic type registry instead of static DOC_TYPES
  const expectedTypes: string[] = getDocTypes();

  const errors: string[] = [];

  try {
    const foundTypes = await listSchemas(dir);

    // Check for missing schemas
    const missing = expectedTypes.filter(type => !foundTypes.includes(type));

    // Check for extra schemas (not in expected list)
    const extra = foundTypes.filter(type => !expectedTypes.includes(type));

    // Validate each schema can be loaded and compiled
    for (const type of expectedTypes) {
      if (foundTypes.includes(type)) {
        try {
          const schema = await loadSchema(type, dir);

          // Basic validation that schema has required structure
          if (!schema.properties) {
            errors.push(`Schema for '${type}' is missing 'properties' field`);
          }

          if (!schema.properties.type) {
            errors.push(`Schema for '${type}' is missing 'type' property definition`);
          } else if (schema.properties.type.const !== type) {
            errors.push(`Schema for '${type}' has mismatched type const: expected '${type}', got '${schema.properties.type.const}'`);
          }

        } catch (error) {
          errors.push(`Failed to load schema for '${type}': ${(error as Error).message}`);
        }
      }
    }

    return {
      success: missing.length === 0 && errors.length === 0,
      coverage: {
        expected: expectedTypes,
        found: foundTypes,
        missing,
        extra
      },
      errors
    };

  } catch (error) {
    return {
      success: false,
      coverage: {
        expected: expectedTypes,
        found: [],
        missing: expectedTypes,
        extra: []
      },
      errors: [`Failed to validate schema coverage: ${(error as Error).message}`]
    };
  }
}
