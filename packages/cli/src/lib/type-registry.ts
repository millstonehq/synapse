/**
 * Dynamic type registry - discovers document types at runtime from schema files.
 * Replaces the static types.generated.ts with runtime schema discovery.
 */

import fsExtra from 'fs-extra';
import * as path from 'path';
import { createRequire } from 'module';

const fs = fsExtra;

export interface TypeMetadata {
  folder: string;
  displayLabel: string;
  cmsCollection: string;
}

// Cache for discovered types
let _typeRegistry: Record<string, TypeMetadata> | null = null;

/**
 * Resolve the frontmatter schema directory using a cascade:
 * 1. Local project: {cwd}/schemas/frontmatter/
 * 2. @millstone/synapse-schemas npm package
 * 3. Error with helpful message
 */
function getSchemaDir(): string {
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
        const hasSchemas = files.some((f: string) => f.endsWith('.schema.json'));
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
 * Discover all document types by scanning schema files.
 * Reads x-synapse metadata from each schema for folder/displayLabel/cmsCollection.
 */
function discoverTypes(): Record<string, TypeMetadata> {
  const schemaDir = getSchemaDir();
  const files = fs.readdirSync(schemaDir);
  const registry: Record<string, TypeMetadata> = {};

  for (const file of files) {
    if (!file.endsWith('.schema.json') || file === 'base.schema.json') continue;

    const schemaPath = path.join(schemaDir, file);
    try {
      const content = fs.readFileSync(schemaPath, 'utf-8');
      const schema = JSON.parse(content);

      // Extract type from properties.type.const
      const type = schema.properties?.type?.const;
      if (!type) {
        // Also check inside allOf for the const
        const allOfType = schema.allOf?.find((item: any) => item.properties?.type?.const);
        if (!allOfType) continue;
        // Skip - schema doesn't define a type const
        continue;
      }

      // Extract x-synapse metadata
      const xSynapse = schema['x-synapse'];
      if (xSynapse) {
        registry[type] = {
          folder: xSynapse.folder,
          displayLabel: xSynapse.displayLabel,
          cmsCollection: xSynapse.cmsCollection,
        };
      } else {
        // Derive defaults if no x-synapse metadata
        registry[type] = {
          folder: type,
          displayLabel: type.charAt(0).toUpperCase() + type.slice(1),
          cmsCollection: type + 's',
        };
      }
    } catch {
      // Skip files that can't be parsed
      continue;
    }
  }

  return registry;
}

/**
 * Get the full type registry. Cached after first call.
 */
export function getTypeRegistry(): Record<string, TypeMetadata> {
  if (!_typeRegistry) {
    _typeRegistry = discoverTypes();
  }
  return _typeRegistry;
}

/**
 * Get all known document types as a sorted array.
 */
export function getDocTypes(): string[] {
  return Object.keys(getTypeRegistry()).sort();
}

/**
 * Check if a value is a known document type.
 */
export function isKnownDocType(value: string): boolean {
  return value in getTypeRegistry();
}

/**
 * Get the expected content folder for a document type.
 * Returns path like "content/90_Architecture/ADRs"
 */
export function getExpectedFolder(type: string): string {
  const registry = getTypeRegistry();
  const meta = registry[type];
  if (!meta) throw new Error(`Unknown document type: ${type}`);
  return `content/${meta.folder}`;
}

/**
 * Get the display label for a document type.
 */
export function getDisplayLabel(type: string): string {
  const registry = getTypeRegistry();
  const meta = registry[type];
  if (!meta) throw new Error(`Unknown document type: ${type}`);
  return meta.displayLabel;
}

/**
 * Get the CMS collection name for a document type.
 */
export function getCmsCollection(type: string): string {
  const registry = getTypeRegistry();
  const meta = registry[type];
  if (!meta) throw new Error(`Unknown document type: ${type}`);
  return meta.cmsCollection;
}

/**
 * Clear the type registry cache. Useful for testing.
 */
export function clearTypeRegistryCache(): void {
  _typeRegistry = null;
}
