import { describe, it, expect } from '@jest/globals';
import * as path from 'path';
import fsExtra from 'fs-extra';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const fs = fsExtra;
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

describe('Schema Coverage', () => {
  const frontmatterDir = path.resolve(__dirname, '../../../../schemas/frontmatter');
  const bodyDir = path.resolve(__dirname, '../../../../schemas/body-grammars');

  it('should have matching type.const between schema filename and properties.type.const', async () => {
    const frontmatterFiles = (await fs.readdir(frontmatterDir))
      .filter(f => f.endsWith('.schema.json') && f !== 'base.schema.json');

    const mismatches: string[] = [];

    for (const file of frontmatterFiles) {
      const expectedType = file.replace('.schema.json', '');
      const schema = await fs.readJSON(path.join(frontmatterDir, file));
      const actualType = schema.properties?.type?.const;

      if (!actualType) {
        mismatches.push(`${file}: missing properties.type.const`);
      } else if (actualType !== expectedType) {
        mismatches.push(`${file}: properties.type.const is "${actualType}", expected "${expectedType}"`);
      }
    }

    if (mismatches.length > 0) {
      throw new Error(`Schema filename/type mismatches:\n  - ${mismatches.join('\n  - ')}`);
    }

    expect(mismatches).toHaveLength(0);
  });

  it('should have matching type field in body grammar and its filename', async () => {
    const bodyFiles = (await fs.readdir(bodyDir))
      .filter(f => f.endsWith('.body-grammar.json'));

    const mismatches: string[] = [];

    for (const file of bodyFiles) {
      const expectedType = file.replace('.body-grammar.json', '');
      const body = await fs.readJSON(path.join(bodyDir, file));

      if (body.type !== expectedType) {
        mismatches.push(`${file}: type is "${body.type}", expected "${expectedType}"`);
      }
    }

    if (mismatches.length > 0) {
      throw new Error(`Body grammar type mismatches:\n  - ${mismatches.join('\n  - ')}`);
    }

    expect(mismatches).toHaveLength(0);
  });
});
