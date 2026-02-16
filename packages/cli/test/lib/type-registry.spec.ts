import * as path from 'path';
import * as os from 'os';
import fsExtra from 'fs-extra';
const fs = fsExtra;

import {
  getTypeRegistry,
  getDocTypes,
  isKnownDocType,
  getExpectedFolder,
  getDisplayLabel,
  getCmsCollection,
  clearTypeRegistryCache,
} from '../../src/lib/type-registry.js';

describe('type-registry', () => {
  let tmpDir: string;
  let originalCwd: string;

  beforeEach(() => {
    tmpDir = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'synapse-typereg-test-')));
    originalCwd = process.cwd();
    clearTypeRegistryCache();
  });

  afterEach(() => {
    process.chdir(originalCwd);
    if (fs.existsSync(tmpDir)) {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
    clearTypeRegistryCache();
  });

  function createSchema(dir: string, filename: string, schema: any) {
    fs.writeFileSync(path.join(dir, filename), JSON.stringify(schema, null, 2));
  }

  describe('schema discovery', () => {
    let schemaDir: string;

    beforeEach(() => {
      schemaDir = path.join(tmpDir, 'schemas/frontmatter');
      fs.mkdirpSync(schemaDir);
      // base.schema.json should be skipped
      createSchema(schemaDir, 'base.schema.json', { type: 'object' });
    });

    it('should discover types from schema files with x-synapse metadata', () => {
      createSchema(schemaDir, 'meeting.schema.json', {
        properties: { type: { const: 'meeting' } },
        'x-synapse': {
          folder: '60_Meetings',
          displayLabel: 'Meeting',
          cmsCollection: 'meetings',
        },
      });

      process.chdir(tmpDir);
      const registry = getTypeRegistry();
      expect(registry).toHaveProperty('meeting');
      expect(registry['meeting'].folder).toBe('60_Meetings');
      expect(registry['meeting'].displayLabel).toBe('Meeting');
    });

    it('should derive defaults when no x-synapse metadata', () => {
      createSchema(schemaDir, 'note.schema.json', {
        properties: { type: { const: 'note' } },
      });

      process.chdir(tmpDir);
      const registry = getTypeRegistry();
      expect(registry).toHaveProperty('note');
      expect(registry['note'].folder).toBe('note');
      expect(registry['note'].displayLabel).toBe('Note');
      expect(registry['note'].cmsCollection).toBe('notes');
    });

    it('should skip base.schema.json', () => {
      createSchema(schemaDir, 'meeting.schema.json', {
        properties: { type: { const: 'meeting' } },
        'x-synapse': { folder: '60_Meetings', displayLabel: 'Meeting', cmsCollection: 'meetings' },
      });

      process.chdir(tmpDir);
      const types = getDocTypes();
      expect(types).not.toContain('object');
      expect(types).toContain('meeting');
    });

    it('should skip schemas without type const', () => {
      createSchema(schemaDir, 'broken.schema.json', {
        properties: { title: { type: 'string' } },
      });

      process.chdir(tmpDir);
      const registry = getTypeRegistry();
      expect(Object.keys(registry)).not.toContain('broken');
    });

    it('should skip schemas with allOf but no type const', () => {
      createSchema(schemaDir, 'allof.schema.json', {
        allOf: [
          { properties: { title: { type: 'string' } } },
        ],
      });

      process.chdir(tmpDir);
      const registry = getTypeRegistry();
      expect(Object.keys(registry)).toHaveLength(0);
    });

    it('should skip unparseable schema files', () => {
      fs.writeFileSync(path.join(schemaDir, 'bad.schema.json'), '{invalid json!!!');

      process.chdir(tmpDir);
      // Should not throw
      const registry = getTypeRegistry();
      expect(registry).toBeDefined();
    });
  });

  describe('public API', () => {
    let schemaDir: string;

    beforeEach(() => {
      schemaDir = path.join(tmpDir, 'schemas/frontmatter');
      fs.mkdirpSync(schemaDir);
      createSchema(schemaDir, 'base.schema.json', { type: 'object' });
      createSchema(schemaDir, 'system.schema.json', {
        properties: { type: { const: 'system' } },
        'x-synapse': { folder: '75_Systems', displayLabel: 'System', cmsCollection: 'systems' },
      });
      process.chdir(tmpDir);
    });

    it('getDocTypes returns sorted list', () => {
      createSchema(schemaDir, 'meeting.schema.json', {
        properties: { type: { const: 'meeting' } },
        'x-synapse': { folder: '60_Meetings', displayLabel: 'Meeting', cmsCollection: 'meetings' },
      });
      clearTypeRegistryCache();

      const types = getDocTypes();
      expect(types).toEqual(['meeting', 'system']);
    });

    it('isKnownDocType returns true for known types', () => {
      expect(isKnownDocType('system')).toBe(true);
    });

    it('isKnownDocType returns false for unknown types', () => {
      expect(isKnownDocType('nonexistent')).toBe(false);
    });

    it('getExpectedFolder returns content path', () => {
      expect(getExpectedFolder('system')).toBe('content/75_Systems');
    });

    it('getExpectedFolder throws for unknown type', () => {
      expect(() => getExpectedFolder('nonexistent')).toThrow('Unknown document type');
    });

    it('getDisplayLabel returns label', () => {
      expect(getDisplayLabel('system')).toBe('System');
    });

    it('getDisplayLabel throws for unknown type', () => {
      expect(() => getDisplayLabel('nonexistent')).toThrow('Unknown document type');
    });

    it('getCmsCollection returns collection name', () => {
      expect(getCmsCollection('system')).toBe('systems');
    });

    it('getCmsCollection throws for unknown type', () => {
      expect(() => getCmsCollection('nonexistent')).toThrow('Unknown document type');
    });

    it('caches results after first call', () => {
      const first = getTypeRegistry();
      const second = getTypeRegistry();
      expect(first).toBe(second);
    });
  });

  describe('schema resolution cascade', () => {
    it('should find schemas in parent directory', () => {
      const schemaDir = path.join(tmpDir, 'schemas/frontmatter');
      fs.mkdirpSync(schemaDir);
      createSchema(schemaDir, 'base.schema.json', { type: 'object' });
      createSchema(schemaDir, 'tdd.schema.json', {
        properties: { type: { const: 'tdd' } },
        'x-synapse': { folder: '90_Architecture/TDDs', displayLabel: 'TDD', cmsCollection: 'tdds' },
      });

      const subDir = path.join(tmpDir, 'content');
      fs.mkdirpSync(subDir);
      process.chdir(subDir);

      expect(isKnownDocType('tdd')).toBe(true);
    });

    it('should fall back to npm package when no local schemas', () => {
      // When chdir to a dir with no schemas/, the registry should still work
      // because it falls back to @millstone/synapse-schemas via createRequire
      const emptyDir = path.join(tmpDir, 'empty');
      fs.mkdirpSync(emptyDir);
      process.chdir(emptyDir);

      // Should not throw — falls back to npm package
      const registry = getTypeRegistry();
      expect(Object.keys(registry).length).toBeGreaterThan(0);
    });
  });
});
