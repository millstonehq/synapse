import * as path from "path";
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import fsExtra from "fs-extra";
const fs = fsExtra;
import { jest } from '@jest/globals';
import {
  loadSchema,
  listSchemas,
} from "../../src/lib/schemas.js";
import {
  loadBodyRules,
} from "../../src/lib/bodyRules.js";

// ESM __dirname replacement
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

describe("schema resolution cascade", () => {
  const originalConsoleError = console.error;
  beforeAll(() => {
    console.error = jest.fn();
  });
  afterAll(() => {
    console.error = originalConsoleError;
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.restoreAllMocks();
    jest.clearAllMocks();
  });

  describe("frontmatter schema resolution", () => {
    it("should resolve schemas from local project directory", async () => {
      // The test setup sets cwd to packages/cli, which has ../schemas/frontmatter
      const schemas = await listSchemas();
      expect(schemas.length).toBeGreaterThan(0);
      expect(schemas).toContain("adr");
    });

    it("should load schema from explicit local directory (priority 1 override)", async () => {
      const tempDir = path.join("/tmp", "test-schema-cascade-local-" + Date.now());
      await fs.ensureDir(tempDir);

      // Create a local override schema
      const overrideSchema = {
        $id: "adr.schema.json",
        $schema: "https://json-schema.org/draft/2020-12/schema",
        type: "object",
        properties: {
          type: { const: "adr" },
          customField: { type: "string" },
        },
        required: ["type"],
      };
      await fs.writeJson(path.join(tempDir, "adr.schema.json"), overrideSchema);

      // Load from explicit dir should use local override
      const schema = await loadSchema("adr", tempDir);
      expect(schema).toBeDefined();
      expect(schema.properties.customField).toBeDefined();
      expect(schema.properties.customField.type).toBe("string");

      await fs.remove(tempDir);
    });

    it("should fall back gracefully when no schemas found at given path", async () => {
      const nonExistentDir = "/tmp/nonexistent-schema-dir-" + Date.now();
      await expect(loadSchema("adr", nonExistentDir)).rejects.toThrow();
    });

    it("should list schemas from explicit directory", async () => {
      const tempDir = path.join("/tmp", "test-schema-cascade-list-" + Date.now());
      await fs.ensureDir(tempDir);

      await fs.writeJson(path.join(tempDir, "custom.schema.json"), {
        $id: "custom.schema.json",
        type: "object",
        properties: {},
      });

      const schemas = await listSchemas(tempDir);
      expect(schemas).toContain("custom");

      await fs.remove(tempDir);
    });
  });

  describe("body grammar resolution", () => {
    it("should resolve body rules from local project directory", async () => {
      // The test setup sets cwd to packages/cli, which has ../schemas/body-grammars
      const rules = await loadBodyRules();
      expect(rules).toBeDefined();
      expect(rules.documentTypes).toBeDefined();
      expect(rules.documentTypes.adr).toBeDefined();
    });

    it("should load body rules from explicit root directory (priority 1 override)", async () => {
      const tempDir = path.join("/tmp", "test-grammar-cascade-local-" + Date.now());
      const grammarsDir = path.join(tempDir, "schemas/body-grammars");
      await fs.ensureDir(grammarsDir);

      // Create a local override grammar
      const overrideGrammar = {
        type: "custom",
        displayName: "Custom Document",
        sections: [
          {
            id: "overview",
            title: "Overview",
            required: true,
            order: 1,
            shape: { type: "paragraphs" },
          },
        ],
      };
      await fs.writeJson(
        path.join(grammarsDir, "custom.body-grammar.json"),
        overrideGrammar
      );

      const rules = await loadBodyRules(tempDir);
      expect(rules.documentTypes.custom).toBeDefined();
      expect(rules.documentTypes.custom.displayName).toBe("Custom Document");
      expect(rules.documentTypes.custom.sections).toHaveLength(1);

      await fs.remove(tempDir);
    });

    it("should throw when grammars directory does not exist", async () => {
      const nonExistentDir = "/tmp/nonexistent-grammar-dir-" + Date.now();
      await expect(loadBodyRules(nonExistentDir)).rejects.toThrow(
        "Body grammars directory not found"
      );
    });
  });

  describe("cascade priority behavior", () => {
    it("should prefer local schemas over package schemas when both exist", async () => {
      // When running from the project root (or packages/cli with ../schemas available),
      // the local schemas should be found first, before checking @millstone/synapse-schemas package
      const schemas = await listSchemas();
      expect(schemas).toContain("adr");

      const schema = await loadSchema("adr");
      expect(schema).toBeDefined();
      expect(schema.$id).toBe("adr.schema.json");
    });

    it("should prefer local body grammars over package grammars", async () => {
      const rules = await loadBodyRules();
      expect(rules.documentTypes.adr).toBeDefined();
      expect(rules.documentTypes.adr.displayName).toBe("Architecture Decision Record");
    });
  });
});
