import * as path from "path";
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import fsExtra from "fs-extra";
const fs = fsExtra;
import { jest } from '@jest/globals';
import {
  loadBodyRules,
  formatBody,
  validateBody,
  type BodyRules,
  type ValidationIssue,
} from "../../src/lib/bodyRules.js";

// ESM __dirname replacement
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

describe("bodyRules module", () => {
  const originalConsoleError = console.error;
  const originalConsoleWarn = console.warn;

  beforeAll(() => {
    console.error = jest.fn();
    console.warn = jest.fn();
  });

  afterAll(() => {
    console.error = originalConsoleError;
    console.warn = originalConsoleWarn;
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.restoreAllMocks();
    jest.clearAllMocks();
  });

  describe("loadBodyRules", () => {
    it("should load body rules from default directory", async () => {
      const rules = await loadBodyRules();

      expect(rules).toBeDefined();
      expect(rules.documentTypes).toBeDefined();
      expect(Object.keys(rules.documentTypes).length).toBeGreaterThan(0);
      expect(rules.documentTypes.adr).toBeDefined();
      expect(rules.documentTypes.adr.displayName).toBe("Architecture Decision Record");
      expect(rules.documentTypes.adr.sections.length).toBeGreaterThan(0);
    });

    it("should load body rules from custom root directory", async () => {
      const customRoot = path.resolve(__dirname, "../../../../");
      const rules = await loadBodyRules(customRoot);

      expect(rules).toBeDefined();
      expect(rules.documentTypes.process).toBeDefined();
      expect(rules.documentTypes.process.displayName).toBe("Process Document");
    });

    it("should throw error if grammars directory does not exist", async () => {
      const nonExistentDir = "/tmp/non-existent-grammars-" + Date.now();
      await expect(loadBodyRules(nonExistentDir)).rejects.toThrow(
        "Body grammars directory not found"
      );
    });

    it("should throw error if no grammar files found", async () => {
      const emptyDir = path.join("/tmp", "empty-grammars-" + Date.now());
      await fs.ensureDir(path.join(emptyDir, "schemas/body-grammars"));

      await expect(loadBodyRules(emptyDir)).rejects.toThrow(
        "No body grammar files found"
      );

      await fs.remove(emptyDir);
    });

    it("should throw error if grammar file missing type field", async () => {
      const tempDir = path.join("/tmp", "test-grammars-missing-type-" + Date.now());
      const grammarsDir = path.join(tempDir, "schemas/body-grammars");
      await fs.ensureDir(grammarsDir);

      // Create a grammar file without 'type' field
      const invalidGrammar = {
        displayName: "Invalid Type",
        sections: []
      };
      await fs.writeJson(
        path.join(grammarsDir, "invalid.body-grammar.json"),
        invalidGrammar
      );

      await expect(loadBodyRules(tempDir)).rejects.toThrow(
        "missing 'type' field"
      );

      await fs.remove(tempDir);
    });

    it("should load multiple grammar files", async () => {
      const rules = await loadBodyRules();

      expect(rules.documentTypes.adr).toBeDefined();
      expect(rules.documentTypes.process).toBeDefined();
      expect(rules.documentTypes.prd).toBeDefined();
    });

    it("should parse sections with alternativeTitles", async () => {
      const rules = await loadBodyRules();
      const prdSections = rules.documentTypes.prd.sections;

      const goalsSection = prdSections.find(s => s.id === "goals");
      expect(goalsSection).toBeDefined();
      expect(goalsSection!.alternativeTitles).toBeDefined();
      expect(goalsSection!.alternativeTitles).toContain("Objective");
    });
  });

  describe("formatBody", () => {
    let rules: BodyRules;

    beforeAll(async () => {
      rules = await loadBodyRules();
    });

    it("should return body as-is for unknown document type", () => {
      const body = "## Some Section\n\nContent here";
      const formatted = formatBody(body, rules, "unknown" as any);

      expect(formatted).toBe(body);
    });

    it("should format body with all required sections in order", () => {
      const body = "";
      const formatted = formatBody(body, rules, "adr");

      expect(formatted).toContain("## Context");
      expect(formatted).toContain("## Decision");
      expect(formatted).toContain("## Consequences");
      expect(formatted).toMatch(/## Context.*## Decision.*## Consequences/s);
    });

    it("should preserve existing section content", () => {
      const body = `## Context

This is the context section with content.

## Decision

This is the decision.`;

      const formatted = formatBody(body, rules, "adr");

      expect(formatted).toContain("This is the context section with content.");
      expect(formatted).toContain("This is the decision.");
    });

    it("should normalize section headings to canonical titles", () => {
      const body = `## context

Content here.

## DECISION

More content.`;

      const formatted = formatBody(body, rules, "adr");

      expect(formatted).toContain("## Context");
      expect(formatted).toContain("## Decision");
      expect(formatted).not.toContain("## context");
      expect(formatted).not.toContain("## DECISION");
    });

    it("should insert missing required sections with placeholder", () => {
      const body = `## Context

Only context is provided.`;

      const formatted = formatBody(body, rules, "adr");

      expect(formatted).toContain("## Decision");
      expect(formatted).toContain("## Consequences");
      expect(formatted).toContain("[TODO: Complete this section]");
    });

    it("should normalize lists to unordered by default", () => {
      const body = `## Roles and Responsibilities

1. First item
2. Second item
3. Third item`;

      const formatted = formatBody(body, rules, "process");

      // Should convert to unordered list
      expect(formatted).toContain("- First item");
      expect(formatted).toContain("- Second item");
    });

    it("should normalize lists to ordered when specified", () => {
      const body = `## Steps

- Unordered first
- Unordered second`;

      const formatted = formatBody(body, rules, "process");

      // Steps section requires ordered list
      expect(formatted).toMatch(/1\.\s+Unordered first/);
      expect(formatted).toMatch(/2\.\s+Unordered second/);
    });

    it("should flatten deeply nested lists when maxDepth is set", async () => {
      const tempDir = path.join("/tmp", "test-grammars-flatten-" + Date.now());
      const grammarsDir = path.join(tempDir, "schemas/body-grammars");
      await fs.ensureDir(grammarsDir);

      const grammarWithMaxDepth = {
        type: "testdoc",
        displayName: "Test Document",
        sections: [
          {
            id: "test-section",
            title: "Test Section",
            required: true,
            order: 1,
            shape: {
              type: "list",
              ordered: false,
              maxDepth: 1
            }
          }
        ]
      };

      await fs.writeJson(
        path.join(grammarsDir, "testdoc.body-grammar.json"),
        grammarWithMaxDepth
      );

      const testRules = await loadBodyRules(tempDir);

      const body = `## Test Section

- Level 1
  - Level 2 (should be flattened)
    - Level 3 (should be flattened)`;

      const formatted = formatBody(body, testRules, "testdoc" as any);

      // Should flatten nested lists
      expect(formatted).toContain("- Level 1");
      expect(formatted).toContain("- Level 2 (should be flattened)");

      await fs.remove(tempDir);
    });

    it("should preserve subsection headings (H3, H4)", () => {
      const body = `## Context

### Subsection

Content here.

#### Sub-subsection

More content.`;

      const formatted = formatBody(body, rules, "adr");

      expect(formatted).toContain("### Subsection");
      expect(formatted).toContain("#### Sub-subsection");
    });

    it("should not include optional sections if not present", () => {
      const body = `## Context

Context content.

## Decision

Decision content.

## Consequences

Consequences content.`;

      const formatted = formatBody(body, rules, "adr");

      // Should not include "Alternatives Considered" (optional)
      expect(formatted).not.toContain("## Alternatives Considered");
    });
  });

  describe("validateBody", () => {
    let rules: BodyRules;

    beforeAll(async () => {
      rules = await loadBodyRules();
    });

    it("should return error for unknown document type", () => {
      const body = "## Some Section";
      const issues = validateBody(body, rules, "unknown" as any, "test.md");

      expect(issues.length).toBe(1);
      expect(issues[0].code).toBe("unknown-type");
      expect(issues[0].message).toContain("No body rules defined");
    });

    it("should validate body with all required sections", () => {
      const body = `## Context

Context content.

## Decision

Decision content.

## Consequences

Consequences content.`;

      const issues = validateBody(body, rules, "adr", "test.md");

      expect(issues.length).toBe(0);
    });

    it("should report missing required sections", () => {
      const body = `## Context

Only context provided.`;

      const issues = validateBody(body, rules, "adr", "test.md");

      expect(issues.length).toBeGreaterThan(0);
      const missingDecision = issues.find(i => i.code === "missing-required-section" && i.message.includes("Decision"));
      const missingConsequences = issues.find(i => i.code === "missing-required-section" && i.message.includes("Consequences"));

      expect(missingDecision).toBeDefined();
      expect(missingConsequences).toBeDefined();
    });

    it("should detect duplicate sections", () => {
      const body = `## Context

First context.

## Context

Duplicate context.

## Decision

Decision content.

## Consequences

Consequences content.`;

      const issues = validateBody(body, rules, "adr", "test.md");

      const duplicateIssue = issues.find(i => i.code === "duplicate-section");
      expect(duplicateIssue).toBeDefined();
      expect(duplicateIssue!.message).toContain("Duplicate section");
      expect(duplicateIssue!.message).toContain("appears 2 times");
    });

    it("should validate section order", () => {
      const body = `## Decision

Decision first (wrong order).

## Context

Context second (wrong order).

## Consequences

Consequences last.`;

      const issues = validateBody(body, rules, "adr", "test.md");

      const orderIssue = issues.find(i => i.code === "section-out-of-order");
      expect(orderIssue).toBeDefined();
      expect(orderIssue!.message).toContain("out of order");
    });

    it("should match sections by alternative titles", () => {
      const body = `## Summary

Summary content.

## Objective

Using alternative title for Goals.

## In Scope

In scope content.

## Out of Scope

Out of scope content.

## Users and Flows

Users content.

## Functional Requirements

Using alternative title for Requirements.

## KPIs

KPIs content.

## Information Architecture

IA content.

## Data Model

Data model content.

## Non-Functional

Non-functional content.

## Constraints

Constraints content.

## Risks

Risks content.

## Milestones

### Milestone 1

#### Deliverables

Deliverable content.

#### Acceptance Criteria

Criteria content.`;

      const issues = validateBody(body, rules, "prd", "test.md");

      // Should not have missing section errors for "Goals" or "Requirements"
      const missingGoals = issues.find(i => i.message.includes("Goals"));
      const missingRequirements = issues.find(i => i.message.includes("Requirements"));

      expect(missingGoals).toBeUndefined();
      expect(missingRequirements).toBeUndefined();
    });

    it("should validate paragraphs shape", async () => {
      const tempDir = path.join("/tmp", "test-grammars-paragraphs-" + Date.now());
      const grammarsDir = path.join(tempDir, "schemas/body-grammars");
      await fs.ensureDir(grammarsDir);

      const grammarWithParagraphs = {
        type: "testpara",
        displayName: "Test Paragraphs",
        sections: [
          {
            id: "para-section",
            title: "Paragraph Section",
            required: true,
            order: 1,
            shape: {
              type: "paragraphs"
            }
          }
        ]
      };

      await fs.writeJson(
        path.join(grammarsDir, "testpara.body-grammar.json"),
        grammarWithParagraphs
      );

      const testRules = await loadBodyRules(tempDir);

      const bodyWithList = `## Paragraph Section

- This is a list
- Not a paragraph`;

      const issues = validateBody(bodyWithList, testRules, "testpara" as any, "test.md");

      const invalidContent = issues.find(i => i.code === "invalid-section-content");
      expect(invalidContent).toBeDefined();
      expect(invalidContent!.message).toContain("should only contain paragraphs");
      expect(invalidContent!.message).toContain("found list");

      await fs.remove(tempDir);
    });

    it("should validate list shape - ordered vs unordered", () => {
      const body = `## Steps

- Wrong list type (unordered)
- Should be ordered`;

      const issues = validateBody(body, rules, "process", "test.md");

      const wrongListType = issues.find(i => i.code === "wrong-list-type");
      expect(wrongListType).toBeDefined();
      expect(wrongListType!.message).toContain("expected numbered");
      expect(wrongListType!.message).toContain("found bulleted");
    });

    it("should validate list minItems", () => {
      const body = `## Roles and Responsibilities

Empty list section.`;

      const issues = validateBody(body, rules, "process", "test.md");

      const missingList = issues.find(i => i.code === "missing-list");
      expect(missingList).toBeDefined();
      expect(missingList!.message).toContain("should contain a list");
    });

    it("should validate insufficient list items", async () => {
      const tempDir = path.join("/tmp", "test-grammars-minitems-" + Date.now());
      const grammarsDir = path.join(tempDir, "schemas/body-grammars");
      await fs.ensureDir(grammarsDir);

      const grammarWithMinItems = {
        type: "testlist",
        displayName: "Test List",
        sections: [
          {
            id: "list-section",
            title: "List Section",
            required: true,
            order: 1,
            shape: {
              type: "list",
              ordered: false,
              minItems: 3
            }
          }
        ]
      };

      await fs.writeJson(
        path.join(grammarsDir, "testlist.body-grammar.json"),
        grammarWithMinItems
      );

      const testRules = await loadBodyRules(tempDir);

      const bodyWithFewItems = `## List Section

- Only one item
- Only two items`;

      const issues = validateBody(bodyWithFewItems, testRules, "testlist" as any, "test.md");

      const insufficientItems = issues.find(i => i.code === "insufficient-list-items");
      expect(insufficientItems).toBeDefined();
      expect(insufficientItems!.message).toContain("at least 3 items");
      expect(insufficientItems!.message).toContain("found 2");

      await fs.remove(tempDir);
    });

    it("should validate list maxDepth", async () => {
      const tempDir = path.join("/tmp", "test-grammars-maxdepth-" + Date.now());
      const grammarsDir = path.join(tempDir, "schemas/body-grammars");
      await fs.ensureDir(grammarsDir);

      const grammarWithMaxDepth = {
        type: "testdepth",
        displayName: "Test Depth",
        sections: [
          {
            id: "depth-section",
            title: "Depth Section",
            required: true,
            order: 1,
            shape: {
              type: "list",
              ordered: false,
              maxDepth: 1
            }
          }
        ]
      };

      await fs.writeJson(
        path.join(grammarsDir, "testdepth.body-grammar.json"),
        grammarWithMaxDepth
      );

      const testRules = await loadBodyRules(tempDir);

      const bodyWithDeepNesting = `## Depth Section

- Level 1
  - Level 2 (exceeds maxDepth)`;

      const issues = validateBody(bodyWithDeepNesting, testRules, "testdepth" as any, "test.md");

      const tooDeep = issues.find(i => i.code === "list-too-deep");
      expect(tooDeep).toBeDefined();
      expect(tooDeep!.message).toContain("exceeds maximum depth of 1");
      expect(tooDeep!.message).toContain("found depth: 2");

      await fs.remove(tempDir);
    });

    it("should validate flow shape with allowed nodes", () => {
      const body = `## Context

This is a paragraph (allowed).

- This is a list (allowed)

\`\`\`
This is code (not allowed)
\`\`\`

## Decision

Decision content.

## Consequences

Consequences content.`;

      const issues = validateBody(body, rules, "adr", "test.md");

      const disallowedNode = issues.find(i => i.code === "disallowed-node-type");
      expect(disallowedNode).toBeDefined();
      expect(disallowedNode!.message).toContain("does not allow code nodes");
    });

    it("should validate table shape", async () => {
      const tempDir = path.join("/tmp", "test-grammars-table-" + Date.now());
      const grammarsDir = path.join(tempDir, "schemas/body-grammars");
      await fs.ensureDir(grammarsDir);

      const grammarWithTable = {
        type: "testtable",
        displayName: "Test Table",
        sections: [
          {
            id: "table-section",
            title: "Table Section",
            required: true,
            order: 1,
            shape: {
              type: "table",
              requiredHeaders: ["Name", "Value"],
              minRows: 2
            }
          }
        ]
      };

      await fs.writeJson(
        path.join(grammarsDir, "testtable.body-grammar.json"),
        grammarWithTable
      );

      const testRules = await loadBodyRules(tempDir);

      // Test missing table
      const bodyWithoutTable = `## Table Section

Just a paragraph, no table.`;

      let issues = validateBody(bodyWithoutTable, testRules, "testtable" as any, "test.md");

      let missingTable = issues.find(i => i.code === "missing-table");
      expect(missingTable).toBeDefined();

      // Test missing required header
      const bodyWithWrongHeaders = `## Table Section

| Wrong | Headers |
|-------|---------|
| A     | B       |
| C     | D       |`;

      issues = validateBody(bodyWithWrongHeaders, testRules, "testtable" as any, "test.md");

      const missingHeader = issues.find(i => i.code === "missing-table-header");
      expect(missingHeader).toBeDefined();
      expect(missingHeader!.message).toContain("missing required header: Name");

      // Test insufficient rows
      const bodyWithFewRows = `## Table Section

| Name | Value |
|------|-------|
| One  | 1     |`;

      issues = validateBody(bodyWithFewRows, testRules, "testtable" as any, "test.md");

      const insufficientRows = issues.find(i => i.code === "insufficient-table-rows");
      expect(insufficientRows).toBeDefined();
      expect(insufficientRows!.message).toContain("at least 2 data rows");
      expect(insufficientRows!.message).toContain("found 1");

      await fs.remove(tempDir);
    });

    it("should validate milestoneList shape", () => {
      const body = `## Milestones

Just a paragraph, no milestones.`;

      const issues = validateBody(body, rules, "prd", "test.md");

      const noMilestones = issues.find(i => i.code === "no-milestones");
      expect(noMilestones).toBeDefined();
      expect(noMilestones!.message).toContain("should contain milestone blocks");
    });

    it("should validate milestone subsections", () => {
      const body = `## Milestones

### Milestone 1

Some content.

#### Deliverables

Deliverables content.

(Missing Acceptance Criteria subsection)

### Milestone 2

More content.

#### Acceptance Criteria

Criteria content.

(Missing Deliverables subsection)`;

      const issues = validateBody(body, rules, "prd", "test.md");

      const missingSubsections = issues.filter(i => i.code === "missing-milestone-subsection");
      expect(missingSubsections.length).toBe(2);

      const missingAcceptance = missingSubsections.find(i => i.message.includes("Milestone 1") && i.message.includes("Acceptance Criteria"));
      const missingDeliverables = missingSubsections.find(i => i.message.includes("Milestone 2") && i.message.includes("Deliverables"));

      expect(missingAcceptance).toBeDefined();
      expect(missingDeliverables).toBeDefined();
    });

    it("should handle unknown shape type gracefully", async () => {
      const tempDir = path.join("/tmp", "test-grammars-unknown-" + Date.now());
      const grammarsDir = path.join(tempDir, "schemas/body-grammars");
      await fs.ensureDir(grammarsDir);

      const grammarWithUnknownShape = {
        type: "testunknown",
        displayName: "Test Unknown",
        sections: [
          {
            id: "unknown-section",
            title: "Unknown Section",
            required: true,
            order: 1,
            shape: {
              type: "unknownShapeType"
            }
          }
        ]
      };

      await fs.writeJson(
        path.join(grammarsDir, "testunknown.body-grammar.json"),
        grammarWithUnknownShape
      );

      const testRules = await loadBodyRules(tempDir);

      const body = `## Unknown Section

Some content.`;

      const issues = validateBody(body, testRules, "testunknown" as any, "test.md");

      const unknownShape = issues.find(i => i.code === "unknown-shape");
      expect(unknownShape).toBeDefined();
      expect(unknownShape!.message).toContain("Unknown shape type");

      await fs.remove(tempDir);
    });

    it("should pass validation with correct list depth", () => {
      const body = `## Roles and Responsibilities

- Role 1
- Role 2`;

      const issues = validateBody(body, rules, "process", "test.md");

      const depthIssues = issues.filter(i => i.code === "list-too-deep");
      expect(depthIssues.length).toBe(0);
    });

    it("should validate table with blank paragraphs", async () => {
      const tempDir = path.join("/tmp", "test-grammars-table-blank-" + Date.now());
      const grammarsDir = path.join(tempDir, "schemas/body-grammars");
      await fs.ensureDir(grammarsDir);

      const grammarWithTable = {
        type: "testtableblank",
        displayName: "Test Table Blank",
        sections: [
          {
            id: "table-section",
            title: "Table Section",
            required: true,
            order: 1,
            shape: {
              type: "table"
            }
          }
        ]
      };

      await fs.writeJson(
        path.join(grammarsDir, "testtableblank.body-grammar.json"),
        grammarWithTable
      );

      const testRules = await loadBodyRules(tempDir);

      const bodyWithBlankLines = `## Table Section

| Name | Value |
|------|-------|
| A    | 1     |

`;

      const issues = validateBody(bodyWithBlankLines, testRules, "testtableblank" as any, "test.md");

      // Should not complain about blank paragraphs
      const missingTable = issues.find(i => i.code === "missing-table");
      expect(missingTable).toBeUndefined();

      await fs.remove(tempDir);
    });
  });
});
