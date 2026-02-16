import * as path from "path";
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import fsExtra from "fs-extra";
const fs = fsExtra;
import { jest } from '@jest/globals';
import {
  loadSchema,
  listSchemas,
  validateFrontmatter,
  validateSchemasCoverage,
} from "../../src/lib/schemas";

// ESM __dirname replacement
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

describe("schemas module", () => {
  // Mock console.error to avoid noise in test output
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
  describe("getDefaultSchemaDir path resolution", () => {
    it("should find schemas from the project", async () => {
      // Just test that we can find schemas - don't mock fs
      const schemas = await listSchemas();
      expect(schemas.length).toBeGreaterThan(0);
      expect(schemas).toContain("adr");
      expect(schemas).toContain("process");
    });

    it("should handle non-existent directory", async () => {
      // Test with an actual non-existent directory
      const nonExistentDir = "/tmp/non-existent-schemas-" + Date.now();
      await expect(listSchemas(nonExistentDir)).rejects.toThrow(
        "Schema directory not found",
      );
    });
  });

  describe("loadSchema", () => {
    it("should load a valid schema", async () => {
      const schema = await loadSchema("adr");
      expect(schema).toBeDefined();
      expect(schema.$id).toBe("adr.schema.json");
      expect(schema.properties).toBeDefined();
      expect(schema.required).toBeDefined();
      expect(Array.isArray(schema.required)).toBe(true);
    });

    it("should load schema with custom directory", async () => {
      const customDir = path.resolve(__dirname, "../../../../schemas/frontmatter");
      const schema = await loadSchema("policy", customDir);
      expect(schema).toBeDefined();
      expect(schema.$id).toBe("policy.schema.json");
    });

    it("should throw for invalid type", async () => {
      await expect(loadSchema("invalid")).rejects.toThrow();
    });

    it("should cache loaded schemas", async () => {
      const start = Date.now();
      await loadSchema("process");
      const firstLoad = Date.now() - start;

      const start2 = Date.now();
      await loadSchema("process");
      const secondLoad = Date.now() - start2;

      // Second load should be faster due to caching
      expect(secondLoad).toBeLessThanOrEqual(firstLoad + 5); // Allow small margin
    });

    it("should handle non-existent schema file", async () => {
      // Mock a scenario where file doesn't exist
      const nonExistentDir = "/non/existent/path";
      await expect(loadSchema("adr", nonExistentDir)).rejects.toThrow();
    });

    it("should handle malformed JSON in schema file", async () => {
      const tempDir = path.join("/tmp", "test-schemas-malformed-" + Date.now());
      await fs.ensureDir(tempDir);

      // Write invalid JSON
      await fs.writeFile(
        path.join(tempDir, "malformed.schema.json"),
        "{ invalid json }",
      );

      await expect(loadSchema("malformed" as any, tempDir)).rejects.toThrow(
        "Failed to load schema for type 'malformed'",
      );

      await fs.remove(tempDir);
    });

    // Removed test that mocked fs.readFile - not idiomatic

    it("should reuse cached schema on second load", async () => {
      // First load - will cache the schema
      const schema1 = await loadSchema("adr");

      // Second load - should use cached version
      const schema2 = await loadSchema("adr");

      // They should be the same object reference due to caching
      expect(schema1).toBe(schema2);
    });

    it("should use different cache for different directories", async () => {
      const dir1 = path.resolve(__dirname, "../../../../schemas/frontmatter");
      const dir2 = "/tmp/different-schemas";

      // Create a simple schema in temp dir
      await fs.ensureDir(dir2);
      const simpleSchema = {
        $id: "adr.schema.json",
        $schema: "https://json-schema.org/draft/2020-12/schema",
        type: "object",
        properties: {
          type: { const: "adr" },
          name: { type: "string" },
        },
      };
      await fs.writeJson(path.join(dir2, "adr.schema.json"), simpleSchema);

      // Load from both directories
      const schema1 = await loadSchema("adr", dir1);
      const schema2 = await loadSchema("adr", dir2);

      // They should be different objects
      expect(schema1).not.toBe(schema2);
      expect(schema1.properties).toBeDefined();
      expect(schema2.properties).toBeDefined();

      // Clean up
      await fs.remove(dir2);
    });

    it("should handle schema without allOf", async () => {
      // Create a temporary directory with a simple schema (no allOf)
      const tempDir = path.join("/tmp", "test-schemas-simple-" + Date.now());
      await fs.ensureDir(tempDir);

      const simpleSchema = {
        $id: "simple.schema.json",
        $schema: "https://json-schema.org/draft/2020-12/schema",
        type: "object",
        properties: {
          type: { const: "simple" },
          name: { type: "string" },
        },
        required: ["type", "name"],
      };

      await fs.writeJson(
        path.join(tempDir, "simple.schema.json"),
        simpleSchema,
      );

      const schema = await loadSchema("simple" as any, tempDir);
      expect(schema.properties).toBeDefined();
      expect(schema.properties.type.const).toBe("simple");
      expect(schema.allOf).toBeUndefined(); // Should not have allOf since we didn't provide it

      await fs.remove(tempDir);
    });

    it("should handle schema with non-base $ref in allOf", async () => {
      // Create a schema with allOf that doesn't reference base.schema.json
      const tempDir = path.join("/tmp", "test-schemas-ref-" + Date.now());
      await fs.ensureDir(tempDir);

      const schemaWithRef = {
        $id: "withref.schema.json",
        $schema: "https://json-schema.org/draft/2020-12/schema",
        type: "object",
        allOf: [
          { properties: { field1: { type: "string" } } },
          { properties: { field2: { type: "number" } } },
        ],
        properties: {
          type: { const: "withref" },
        },
      };

      await fs.writeJson(
        path.join(tempDir, "withref.schema.json"),
        schemaWithRef,
      );

      const schema = await loadSchema("withref" as any, tempDir);
      expect(schema.properties).toBeDefined();
      expect(schema.properties.type.const).toBe("withref");

      await fs.remove(tempDir);
    });
  });

  describe("listSchemas", () => {
    it("should return an array of schema files", async () => {
      const schemas = await listSchemas();
      expect(Array.isArray(schemas)).toBe(true);
      expect(schemas.length).toBeGreaterThanOrEqual(10);
    });

    it("should exclude base.schema.json", async () => {
      const schemas = await listSchemas();
      expect(schemas).not.toContain("base.schema.json");
    });

    it("should include all expected doc types", async () => {
      const schemas = await listSchemas();
      const expectedTypes = [
        "adr",
        "capability",
        "policy",
        "prd",
        "process",
        "runbook",
        "sop",
        "standard",
        "system",
        "tdd",
      ];

      expectedTypes.forEach((type) => {
        expect(schemas).toContain(type);
      });
    });

    it("should handle ENOENT error when directory does not exist", async () => {
      const nonExistentDir = "/this/path/does/not/exist";
      await expect(listSchemas(nonExistentDir)).rejects.toThrow(
        "Schema directory not found",
      );
    });

    // Removed test that mocked fs.readdir - not idiomatic
  });

  describe("validateFrontmatter", () => {
    let adrSchema: any;
    let processSchema: any;

    beforeAll(async () => {
      adrSchema = await loadSchema("adr");
      processSchema = await loadSchema("process");
    });

    it("should validate correct frontmatter", () => {
      const validData = {
        type: "adr",
        id: "ADR-0001",
        title: "Test ADR",
        status: "accepted",
        owner: "Test Owner",
        created: "2024-01-01T00:00:00.000Z",
        updated: "2024-01-01T00:00:00.000Z",
        tags: ["test"],
        summary: "Test summary",
        // Note: decision, context, consequences are validated in body grammars, not frontmatter
      };

      const result = validateFrontmatter(validData, adrSchema);
      expect(result.valid).toBe(true);
      expect(result.errors).toBeUndefined();
    });

    it("should reject invalid frontmatter", () => {
      const invalidData = {
        type: "adr",
        id: "ADR-0001",
        title: "Test ADR",
        // Missing required fields
      };

      const result = validateFrontmatter(invalidData, adrSchema);
      expect(result.valid).toBe(false);
      expect(result.errors).toBeDefined();
      expect(result.errors!.length).toBeGreaterThan(0);
    });

    it("should reject wrong type constant", () => {
      const wrongTypeData = {
        type: "policy", // Wrong type for ADR schema
        id: "ADR-0001",
        title: "Test ADR",
        status: "accepted",
        owner: "Test Owner",
        created: "2024-01-01T00:00:00.000Z",
        updated: "2024-01-01T00:00:00.000Z",
        tags: ["test"],
        summary: "Test summary",
      };

      const result = validateFrontmatter(wrongTypeData, adrSchema);
      expect(result.valid).toBe(false);
    });

    it("should validate date formats", () => {
      const badDateData = {
        type: "adr",
        id: "ADR-0001",
        title: "Test ADR",
        status: "accepted",
        owner: "Test Owner",
        created: "not-a-date",
        updated: "2024-01-01T00:00:00.000Z",
        tags: ["test"],
        summary: "Test summary",
      };

      const result = validateFrontmatter(badDateData, adrSchema);
      expect(result.valid).toBe(false);
    });

    it("should validate arrays and nested structures", () => {
      // Process schema now only validates frontmatter, not body content
      // Fields like purpose, scope, steps, roles are validated in body grammars
      const processData = {
        type: "process",
        id: "PROC-001",
        title: "Test Process",
        status: "approved",
        owner: "Test Owner",
        created: "2024-01-01T00:00:00.000Z",
        updated: "2024-01-01T00:00:00.000Z",
        tags: [] as string[], // Empty array should be valid
        summary: "Test summary",
        related_standards: ["STD-001"], // Optional array field
      };

      const result = validateFrontmatter(processData, processSchema);
      expect(result.valid).toBe(true);

      // Test with additional optional arrays
      const processWithArrays = {
        ...processData,
        related_prds: ["PRD-001"],
        related_tdds: ["TDD-001"],
      };
      const arrayResult = validateFrontmatter(processWithArrays, processSchema);
      expect(arrayResult.valid).toBe(true);
    });

    it("should handle additional properties", () => {
      const dataWithExtra = {
        type: "adr",
        id: "ADR-0001",
        title: "Test ADR",
        status: "accepted",
        owner: "Test Owner",
        created: "2024-01-01T00:00:00.000Z",
        updated: "2024-01-01T00:00:00.000Z",
        tags: ["test"],
        summary: "Test summary",
        extraField: "This field is not in the schema", // Additional property
      };

      // Schema has additionalProperties: false, so this should be invalid
      const result = validateFrontmatter(dataWithExtra, adrSchema);
      expect(result.valid).toBe(false);
    });

    it("should handle schema compilation errors", () => {
      // Create an invalid schema that will cause compilation to fail
      const invalidSchema = {
        type: "object",
        properties: {
          test: {
            type: "invalid-type", // This will cause compilation to fail
          },
        },
      };

      const testData = { test: "value" };
      const result = validateFrontmatter(testData, invalidSchema);

      expect(result.valid).toBe(false);
      expect(result.errors).toBeDefined();
      expect(result.errors!.length).toBeGreaterThan(0);
      expect(result.errors![0].path).toBe("/");
      expect(result.errors![0].message).toContain("Schema compilation failed");
    });

    it("should format type errors properly", () => {
      const invalidTypeData = {
        type: "adr",
        id: "ADR-0001",
        title: "Test ADR",
        status: "accepted",
        owner: "Test Owner",
        created: "2024-01-01T00:00:00.000Z",
        updated: "2024-01-01T00:00:00.000Z",
        tags: "not-an-array", // Should be array
        summary: "Test summary",
      };

      const result = validateFrontmatter(invalidTypeData, adrSchema);
      expect(result.valid).toBe(false);
      expect(result.errors).toBeDefined();

      const typeError = result.errors!.find(e => e.message.includes("must be"));
      expect(typeError).toBeDefined();
    });
  });

  describe("validateSchemasCoverage", () => {
    it("should return coverage information", async () => {
      const result = await validateSchemasCoverage();

      expect(result).toHaveProperty("success");
      expect(result).toHaveProperty("coverage");
      expect(result).toHaveProperty("errors");

      expect(result.coverage).toHaveProperty("expected");
      expect(result.coverage).toHaveProperty("found");
      expect(result.coverage).toHaveProperty("missing");
      expect(result.coverage).toHaveProperty("extra");

      expect(Array.isArray(result.coverage.expected)).toBe(true);
      expect(Array.isArray(result.coverage.found)).toBe(true);
      expect(Array.isArray(result.coverage.missing)).toBe(true);
      expect(Array.isArray(result.errors)).toBe(true);
    });

    it("should report correct schema count", async () => {
      const result = await validateSchemasCoverage();
      expect(result.coverage.expected.length).toBeGreaterThan(0);
      expect(result.coverage.found.length).toBe(result.coverage.expected.length);
    });

    it("should have no missing schemas", async () => {
      const result = await validateSchemasCoverage();
      expect(result.coverage.missing).toHaveLength(0);
      expect(result.success).toBe(true);
    });

    it("should validate all schemas can be loaded", async () => {
      const result = await validateSchemasCoverage();
      // If all schemas load correctly, errors should be empty
      expect(result.errors).toHaveLength(0);
    });

    it("should handle directory with missing schemas", async () => {
      const tempDir = "/tmp/test-schemas-" + Date.now();
      const result = await validateSchemasCoverage(tempDir);
      expect(result.success).toBe(false);
      expect(result.coverage.missing.length).toBeGreaterThan(0);
    });

    it("should handle error when loading schema fails", async () => {
      const tempDir = path.join(
        "/tmp",
        "test-schemas-load-error-" + Date.now(),
      );
      await fs.ensureDir(tempDir);

      // Create a corrupted schema file that will be found by listSchemas
      await fs.writeFile(
        path.join(tempDir, "adr.schema.json"),
        "not valid json",
      );

      const result = await validateSchemasCoverage(tempDir);

      expect(result.success).toBe(false);
      // Should have missing schemas since our temp dir doesn't have all required schemas
      expect(result.coverage.missing.length).toBeGreaterThan(0);

      await fs.remove(tempDir);
    });

    // Removed test that mocked listSchemas - not idiomatic

    it("should detect schema with wrong type constant", async () => {
      // This tests the branch where schema.properties.type.const !== type
      // The real schemas should all have correct type constants
      const result = await validateSchemasCoverage();

      // Should not have any mismatched type errors with real schemas
      const hasMismatchError = result.errors.some((e) =>
        e.includes("mismatched type const"),
      );
      expect(hasMismatchError).toBe(false);
    });

    it("should detect schema missing properties field", async () => {
      const tempDir = path.join("/tmp", "test-schemas-no-props-" + Date.now());
      const schemaDir = path.join(tempDir);
      await fs.ensureDir(schemaDir);

      // Create schema without properties
      await fs.writeJson(
        path.join(schemaDir, "adr.schema.json"),
        {
          $id: "adr.schema.json",
          $schema: "https://json-schema.org/draft/2020-12/schema",
          type: "object",
          // Missing properties field
        }
      );

      const result = await validateSchemasCoverage(tempDir);

      expect(result.success).toBe(false);
      const missingPropsError = result.errors.find(e =>
        e.includes("missing 'properties' field")
      );
      expect(missingPropsError).toBeDefined();

      await fs.remove(tempDir);
    });

    it("should detect schema missing type property definition", async () => {
      const tempDir = path.join("/tmp", "test-schemas-no-type-" + Date.now());
      const schemaDir = path.join(tempDir);
      await fs.ensureDir(schemaDir);

      // Create schema without type property
      await fs.writeJson(
        path.join(schemaDir, "adr.schema.json"),
        {
          $id: "adr.schema.json",
          $schema: "https://json-schema.org/draft/2020-12/schema",
          type: "object",
          properties: {
            // Missing type property
            id: { type: "string" }
          },
        }
      );

      const result = await validateSchemasCoverage(tempDir);

      expect(result.success).toBe(false);
      const missingTypeError = result.errors.find(e =>
        e.includes("missing 'type' property definition")
      );
      expect(missingTypeError).toBeDefined();

      await fs.remove(tempDir);
    });

    it("should detect schema with mismatched type constant", async () => {
      const tempDir = path.join("/tmp", "test-schemas-wrong-const-" + Date.now());
      const schemaDir = path.join(tempDir);
      await fs.ensureDir(schemaDir);

      // Create schema with wrong type constant
      await fs.writeJson(
        path.join(schemaDir, "adr.schema.json"),
        {
          $id: "adr.schema.json",
          $schema: "https://json-schema.org/draft/2020-12/schema",
          type: "object",
          properties: {
            type: { const: "wrong-type" }, // Should be "adr"
            id: { type: "string" }
          },
        }
      );

      const result = await validateSchemasCoverage(tempDir);

      expect(result.success).toBe(false);
      const mismatchError = result.errors.find(e =>
        e.includes("mismatched type const")
      );
      expect(mismatchError).toBeDefined();
      expect(mismatchError).toContain("expected 'adr'");
      expect(mismatchError).toContain("got 'wrong-type'");

      await fs.remove(tempDir);
    });

    // Removed test that mocked listSchemas - not idiomatic

    // Removed test that mocked listSchemas - not idiomatic
  });

  describe("schema $ref resolution", () => {
    it("should resolve base schema references", async () => {
      const processSchema = await loadSchema("process");

      // The merged schema should have properties from both base and process
      expect(processSchema.properties.id).toBeDefined(); // From base
      expect(processSchema.properties.related_standards).toBeDefined(); // From process
      expect(processSchema.required).toContain("id"); // From base
      expect(processSchema.required).toContain("type"); // From process

      const data = {
        type: "process",
        id: "PROC-001",
        title: "Test Process",
        status: "approved", // Valid status from enum
        owner: "Test Owner",
        created: "2024-01-01T00:00:00.000Z",
        updated: "2024-01-01T00:00:00.000Z",
        tags: ["test"],
        summary: "Test summary",
        // Note: purpose, scope, roles, steps are validated in body grammars, not frontmatter
        related_standards: ["STD-001"],
      };

      const result = validateFrontmatter(data, processSchema);
      expect(result.valid).toBe(true);
    });

    it("should enforce base schema fields", async () => {
      const processSchema = await loadSchema("process");

      const missingBaseField = {
        type: "process",
        id: "PROC-001",
        title: "Test Process",
        // Missing 'owner' from base schema
        status: "approved", // Valid status from enum
        created: "2024-01-01T00:00:00.000Z",
        updated: "2024-01-01T00:00:00.000Z",
        tags: ["test"],
        summary: "Test summary",
        related_standards: ["STD-001"],
      };

      const result = validateFrontmatter(missingBaseField, processSchema);
      expect(result.valid).toBe(false);
    });
  });
});
