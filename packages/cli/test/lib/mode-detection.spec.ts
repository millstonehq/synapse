import * as path from 'path';
import * as os from 'os';
import fsExtra from 'fs-extra';
const fs = fsExtra;

import { hasSchemasPackage, hasLocalSchemas } from '../../src/lib/mode-detection.js';

describe('mode-detection', () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'synapse-mode-test-')));
  });

  afterEach(() => {
    if (fs.existsSync(tmpDir)) {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  });

  describe('hasSchemasPackage', () => {
    it('should return false when package is not installed', () => {
      fs.writeFileSync(path.join(tmpDir, 'package.json'), '{}');
      expect(hasSchemasPackage(tmpDir)).toBe(false);
    });

    it('should return true when synapse-schemas is resolvable', () => {
      fs.writeFileSync(path.join(tmpDir, 'package.json'), '{}');
      const pkgDir = path.join(tmpDir, 'node_modules/@millstone/synapse-schemas');
      fs.mkdirpSync(pkgDir);
      fs.writeFileSync(path.join(pkgDir, 'package.json'), '{"name":"@millstone/synapse-schemas"}');

      expect(hasSchemasPackage(tmpDir)).toBe(true);
    });

    it('should default to process.cwd() when no cwd provided', () => {
      // process.cwd() is the synapse repo which has the schemas workspace package
      const result = hasSchemasPackage();
      expect(typeof result).toBe('boolean');
    });
  });

  describe('hasLocalSchemas', () => {
    it('should return false when no schemas directory exists', () => {
      expect(hasLocalSchemas(tmpDir)).toBe(false);
    });

    it('should return false when schemas directory is empty', () => {
      fs.mkdirpSync(path.join(tmpDir, 'schemas', 'frontmatter'));
      expect(hasLocalSchemas(tmpDir)).toBe(false);
    });

    it('should return true when schema files exist locally', () => {
      const schemaDir = path.join(tmpDir, 'schemas', 'frontmatter');
      fs.mkdirpSync(schemaDir);
      fs.writeFileSync(path.join(schemaDir, 'adr.schema.json'), '{}');
      expect(hasLocalSchemas(tmpDir)).toBe(true);
    });

    it('should default to process.cwd() when no cwd provided', () => {
      // process.cwd() unlikely to have schemas/frontmatter
      expect(hasLocalSchemas()).toBe(false);
    });
  });
});
