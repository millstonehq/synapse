import * as fs from 'fs';
import * as path from 'path';
import { createRequire } from 'module';

/**
 * Check whether @millstone/synapse-schemas is available.
 * Returns true if the package is resolvable from the given directory.
 */
export function hasSchemasPackage(cwd?: string): boolean {
  const rootDir = cwd ?? process.cwd();

  try {
    const require = createRequire(path.join(rootDir, 'package.json'));
    require.resolve('@millstone/synapse-schemas/package.json');
    return true;
  } catch {
    return false;
  }
}

/**
 * Check whether local schemas exist at the given directory.
 */
export function hasLocalSchemas(cwd?: string): boolean {
  const rootDir = cwd ?? process.cwd();
  const schemaDir = path.join(rootDir, 'schemas', 'frontmatter');

  if (!fs.existsSync(schemaDir)) return false;

  try {
    const files = fs.readdirSync(schemaDir);
    return files.some(f => f.endsWith('.schema.json'));
  } catch {
    return false;
  }
}
