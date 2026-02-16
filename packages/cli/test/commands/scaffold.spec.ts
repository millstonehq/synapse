import fsExtra from 'fs-extra';
const fs = fsExtra;
import * as path from 'path';
import * as yaml from 'js-yaml';
import { scaffold, scaffoldCommand, generateFilename, parseTemplateVars } from '../../src/commands/scaffold';
import { describe, it, expect, beforeEach, afterEach } from '@jest/globals';

const TEST_DIR = path.join(process.cwd(), 'test-scaffold-tmp');
const CONTENT_DIR = path.join(TEST_DIR, 'content');

// Helper to create an example file for a given type
async function createExample(folder: string, filename: string, frontmatter: Record<string, any>, body: string) {
  const examplesDir = path.join(CONTENT_DIR, folder, 'examples');
  await fs.ensureDir(examplesDir);
  const fmYaml = yaml.dump(frontmatter, { lineWidth: -1 }).trim();
  await fs.writeFile(
    path.join(examplesDir, filename),
    `---\n${fmYaml}\n---\n${body}`,
    'utf-8'
  );
}

describe('scaffold command', () => {
  beforeEach(async () => {
    await fs.ensureDir(CONTENT_DIR);
    // Create a sample ADR example
    await createExample(
      '90_Architecture/ADRs',
      'example-test-adr.md',
      {
        id: 'ADR-0001',
        type: 'adr',
        title: 'Example ADR Title',
        status: 'proposed',
        owner: 'Tech Lead',
        created: '2025-01-01T00:00:00.000Z',
        updated: '2025-01-01T00:00:00.000Z',
        tags: ['adr'],
        example: true
      },
      '\n# Example ADR Title\n\n## Context\nSome context here.\n\n## Decision\nWe decided X.\n'
    );

    // Create a sample policy example
    await createExample(
      '10_Policies',
      'example-test-policy.md',
      {
        id: 'test-policy',
        type: 'policy',
        title: 'Test Policy',
        status: 'draft',
        owner: 'CTO',
        created: '2025-01-01T00:00:00.000Z',
        updated: '2025-01-01T00:00:00.000Z',
        tags: ['policy'],
        summary: 'A test policy',
        example: true
      },
      '\n## Scope\n\nAll systems.\n\n## Policy Statements\n\n- Statement one.\n'
    );
  });

  afterEach(async () => {
    await fs.remove(TEST_DIR);
  });

  it('should scaffold an ADR document', async () => {
    const result = await scaffold({
      type: 'adr',
      title: 'Use PostgreSQL for Database',
      cwd: TEST_DIR
    });

    expect(result).toContain('ADR-001-use-postgresql-for-database.md');
    expect(await fs.pathExists(result)).toBe(true);

    const content = await fs.readFile(result, 'utf-8');
    const lines = content.split('\n');

    // Check frontmatter exists
    expect(lines[0]).toBe('---');
    const fmEnd = lines.indexOf('---', 1);
    expect(fmEnd).toBeGreaterThan(0);

    const fmYaml = lines.slice(1, fmEnd).join('\n');
    const fm = yaml.load(fmYaml) as Record<string, any>;

    expect(fm.id).toBe('ADR-001');
    expect(fm.type).toBe('adr');
    expect(fm.title).toBe('Use PostgreSQL for Database');
    expect(fm.status).toBe('draft');
    expect(fm.example).toBeUndefined();
  });

  it('should scaffold a policy document', async () => {
    const result = await scaffold({
      type: 'policy',
      title: 'Data Protection Policy',
      owner: 'Security Team',
      cwd: TEST_DIR
    });

    expect(result).toContain('POLICY-001-data-protection-policy.md');
    expect(await fs.pathExists(result)).toBe(true);

    const content = await fs.readFile(result, 'utf-8');
    const lines = content.split('\n');
    const fmEnd = lines.indexOf('---', 1);
    const fmYaml = lines.slice(1, fmEnd).join('\n');
    const fm = yaml.load(fmYaml) as Record<string, any>;

    expect(fm.owner).toBe('Security Team');
    expect(fm.example).toBeUndefined();
  });

  it('should error on missing --type', async () => {
    await expect(scaffold({
      type: '',
      title: 'Test',
      cwd: TEST_DIR
    })).rejects.toThrow('Missing required option: --type');
  });

  it('should error on invalid document type', async () => {
    await expect(scaffold({
      type: 'invalid-type',
      title: 'Test',
      cwd: TEST_DIR
    })).rejects.toThrow('Invalid document type: "invalid-type"');
  });

  it('should error on missing --title', async () => {
    await expect(scaffold({
      type: 'adr',
      title: '',
      cwd: TEST_DIR
    })).rejects.toThrow('Missing required option: --title');
  });

  it('should error when example file is not found', async () => {
    await expect(scaffold({
      type: 'reference',
      title: 'Test Reference',
      cwd: TEST_DIR
    })).rejects.toThrow('No example file found for type "reference"');
  });

  it('should error when file already exists without --force', async () => {
    // First scaffold
    await scaffold({
      type: 'adr',
      title: 'Duplicate Test',
      id: 'ADR-DUP',
      cwd: TEST_DIR
    });

    // Second attempt should fail
    await expect(scaffold({
      type: 'adr',
      title: 'Duplicate Test',
      id: 'ADR-DUP',
      cwd: TEST_DIR
    })).rejects.toThrow('File already exists');
  });

  it('should overwrite when --force is set', async () => {
    // First scaffold
    await scaffold({
      type: 'adr',
      title: 'Force Test',
      id: 'ADR-FORCE',
      cwd: TEST_DIR
    });

    // Second attempt with force should succeed
    const result = await scaffold({
      type: 'adr',
      title: 'Force Test',
      id: 'ADR-FORCE',
      force: true,
      cwd: TEST_DIR
    });

    expect(await fs.pathExists(result)).toBe(true);
  });

  it('should use custom ID when provided', async () => {
    const result = await scaffold({
      type: 'adr',
      title: 'Custom ID Test',
      id: 'MY-CUSTOM-ID',
      cwd: TEST_DIR
    });

    expect(result).toContain('MY-CUSTOM-ID-custom-id-test.md');

    const content = await fs.readFile(result, 'utf-8');
    const lines = content.split('\n');
    const fmEnd = lines.indexOf('---', 1);
    const fmYaml = lines.slice(1, fmEnd).join('\n');
    const fm = yaml.load(fmYaml) as Record<string, any>;

    expect(fm.id).toBe('MY-CUSTOM-ID');
  });

  it('should use custom target directory', async () => {
    const customDir = path.join(TEST_DIR, 'custom-output');
    const result = await scaffold({
      type: 'adr',
      title: 'Custom Dir Test',
      targetDir: customDir,
      cwd: TEST_DIR
    });

    expect(result).toContain('custom-output');
    expect(await fs.pathExists(result)).toBe(true);
  });

  it('should auto-increment ID based on existing files', async () => {
    // Create first document
    await scaffold({
      type: 'adr',
      title: 'First ADR',
      cwd: TEST_DIR
    });

    // Create second document - should get ADR-002
    const result = await scaffold({
      type: 'adr',
      title: 'Second ADR',
      cwd: TEST_DIR
    });

    const content = await fs.readFile(result, 'utf-8');
    const lines = content.split('\n');
    const fmEnd = lines.indexOf('---', 1);
    const fmYaml = lines.slice(1, fmEnd).join('\n');
    const fm = yaml.load(fmYaml) as Record<string, any>;

    expect(fm.id).toBe('ADR-002');
  });

  it('should remove the example flag from frontmatter', async () => {
    const result = await scaffold({
      type: 'adr',
      title: 'No Example Flag',
      cwd: TEST_DIR
    });

    const content = await fs.readFile(result, 'utf-8');
    expect(content).not.toContain('example:');
  });

  it('should preserve body content from the example', async () => {
    const result = await scaffold({
      type: 'adr',
      title: 'Body Preservation Test',
      cwd: TEST_DIR
    });

    const content = await fs.readFile(result, 'utf-8');
    expect(content).toContain('## Context');
    expect(content).toContain('## Decision');
  });

  it('should set status to draft', async () => {
    const result = await scaffold({
      type: 'adr',
      title: 'Draft Status Test',
      cwd: TEST_DIR
    });

    const content = await fs.readFile(result, 'utf-8');
    const lines = content.split('\n');
    const fmEnd = lines.indexOf('---', 1);
    const fmYaml = lines.slice(1, fmEnd).join('\n');
    const fm = yaml.load(fmYaml) as Record<string, any>;

    expect(fm.status).toBe('draft');
  });
});

describe('scaffoldCommand', () => {
  beforeEach(async () => {
    await fs.ensureDir(CONTENT_DIR);
    await createExample(
      '90_Architecture/ADRs',
      'example-test-adr.md',
      {
        id: 'ADR-0001',
        type: 'adr',
        title: 'Example ADR',
        status: 'proposed',
        owner: 'Tech Lead',
        created: '2025-01-01T00:00:00.000Z',
        updated: '2025-01-01T00:00:00.000Z',
        example: true
      },
      '\n# Example\n'
    );
  });

  afterEach(async () => {
    await fs.remove(TEST_DIR);
  });

  it('should support --template as alias for --type', async () => {
    // scaffoldCommand wraps scaffold and maps template -> type
    // We cannot easily test the full flow without cwd, so test indirectly
    await expect(scaffoldCommand({
      template: 'invalid-type',
      title: 'Test'
    })).rejects.toThrow('Invalid document type');
  });
});

describe('generateFilename', () => {
  it('should generate a kebab-case filename', () => {
    expect(generateFilename('adr', 'ADR-001', 'Use React for Frontend'))
      .toBe('ADR-001-use-react-for-frontend.md');
  });

  it('should handle special characters in title', () => {
    expect(generateFilename('policy', 'POL-001', "Data Protection & Privacy"))
      .toBe('POL-001-data-protection-privacy.md');
  });
});

describe('parseTemplateVars', () => {
  it('should parse comma-separated key=value pairs', () => {
    expect(parseTemplateVars('key1=val1,key2=val2')).toEqual({
      key1: 'val1',
      key2: 'val2'
    });
  });

  it('should handle values with equals signs', () => {
    expect(parseTemplateVars('url=https://example.com?q=1')).toEqual({
      url: 'https://example.com?q=1'
    });
  });

  it('should return empty object for undefined input', () => {
    expect(parseTemplateVars()).toEqual({});
  });

  it('should return empty object for empty string', () => {
    expect(parseTemplateVars('')).toEqual({});
  });
});
