import { jest } from '@jest/globals';
import {
  extractFrontmatter,
  parseDocument,
  extractWikilinks,
  validateWikilinkExists,
  extractPlaceholders,
  parseFrontmatterKeys,
  needsYamlQuoting,
  parseMarkdown,
  findSections,
  stringifyMarkdown,
  type SectionNode,
} from "../../src/lib/markdown.js";

describe("markdown module", () => {
  const originalConsoleWarn = console.warn;

  beforeAll(() => {
    console.warn = jest.fn();
  });

  afterAll(() => {
    console.warn = originalConsoleWarn;
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("extractFrontmatter", () => {
    it("should extract frontmatter and body", () => {
      const content = `---
title: Test
type: adr
---

Body content here.`;

      const result = extractFrontmatter(content);

      expect(result.frontmatter).toContain("title: Test");
      expect(result.frontmatter).toContain("type: adr");
      expect(result.body).toBe("\nBody content here.");
      expect(result.startLine).toBe(1);
      expect(result.endLine).toBe(3);
    });

    it("should handle content without frontmatter", () => {
      const content = "Just body content.";

      const result = extractFrontmatter(content);

      expect(result.frontmatter).toBe("");
      expect(result.body).toBe(content);
      expect(result.startLine).toBe(0);
      expect(result.endLine).toBe(0);
    });

    it("should handle incomplete frontmatter delimiters", () => {
      const content = `---
title: Test
No closing delimiter

Body content.`;

      const result = extractFrontmatter(content);

      expect(result.frontmatter).toBe("");
      expect(result.body).toBe(content);
    });
  });

  describe("parseDocument", () => {
    it("should parse valid frontmatter and body", () => {
      const content = `---
title: Test Document
type: adr
---

Body content.`;

      const result = parseDocument(content);

      expect(result.frontmatter.title).toBe("Test Document");
      expect(result.frontmatter.type).toBe("adr");
      expect(result.body).toBe("\nBody content.");
      expect(result.error).toBeUndefined();
    });

    it("should handle malformed YAML in frontmatter", () => {
      const content = `---
title: Test
invalid: [unclosed bracket
---

Body.`;

      const result = parseDocument(content);

      expect(result.frontmatter).toEqual({});
      expect(result.error).toBeDefined();
      expect(result.body).toContain("Body.");
    });

    it("should handle empty frontmatter", () => {
      const content = `---
---

Body only.`;

      const result = parseDocument(content);

      expect(result.frontmatter).toEqual({});
      expect(result.body).toBe("\nBody only.");
    });
  });

  describe("extractWikilinks", () => {
    it("should extract simple wikilinks", () => {
      const content = "See [[Link 1]] and [[Link 2]] for details.";

      const links = extractWikilinks(content);

      expect(links).toContain("Link 1");
      expect(links).toContain("Link 2");
      expect(links.length).toBe(2);
    });

    it("should extract wikilinks with display text", () => {
      const content = "See [[Link|Display Text]] for details.";

      const links = extractWikilinks(content);

      expect(links).toContain("Link");
      expect(links).not.toContain("Display Text");
      expect(links.length).toBe(1);
    });

    it("should deduplicate wikilinks", () => {
      const content = "[[Link 1]] and [[Link 1]] appear twice.";

      const links = extractWikilinks(content);

      expect(links.length).toBe(1);
      expect(links[0]).toBe("Link 1");
    });

    it("should handle no wikilinks", () => {
      const content = "No wikilinks here.";

      const links = extractWikilinks(content);

      expect(links.length).toBe(0);
    });
  });

  describe("validateWikilinkExists", () => {
    const existingFiles = new Set([
      "notes/test-document.md",
      "notes/another-doc.md",
      "deep/nested/file.md",
    ]);

    it("should validate existing wikilink", () => {
      expect(validateWikilinkExists("test-document", existingFiles)).toBe(true);
      expect(validateWikilinkExists("another-doc", existingFiles)).toBe(true);
    });

    it("should validate with different casing", () => {
      expect(validateWikilinkExists("Test-Document", existingFiles)).toBe(true);
      expect(validateWikilinkExists("ANOTHER-DOC", existingFiles)).toBe(true);
    });

    it("should return false for non-existent wikilink", () => {
      expect(validateWikilinkExists("non-existent", existingFiles)).toBe(false);
    });

    it("should handle wikilinks with spaces", () => {
      const filesWithSpaces = new Set(["notes/test-document.md"]);
      // validateWikilinkExists normalizes "test document" to "test-document"
      expect(validateWikilinkExists("test document", filesWithSpaces)).toBe(true);
    });
  });

  describe("extractPlaceholders", () => {
    it("should extract simple placeholders", () => {
      const text = "Hello {{name}}, your id is {{id}}.";

      const placeholders = extractPlaceholders(text);

      expect(placeholders.has("name")).toBe(true);
      expect(placeholders.has("id")).toBe(true);
      expect(placeholders.size).toBe(2);
    });

    it("should skip default helpers", () => {
      const text = "{{now}} {{#if condition}}{{id}}{{/if}}";

      const placeholders = extractPlaceholders(text);

      expect(placeholders.has("now")).toBe(false);
      expect(placeholders.has("if")).toBe(false);
      expect(placeholders.has("condition")).toBe(true);
      expect(placeholders.has("id")).toBe(true);
    });

    it("should extract block helper variables", () => {
      const text = "{{#each items}} {{name}} {{/each}}";

      const placeholders = extractPlaceholders(text);

      expect(placeholders.has("items")).toBe(true);
      expect(placeholders.has("name")).toBe(true);
    });

    it("should skip closing tags", () => {
      const text = "{{#if condition}} content {{/if}}";

      const placeholders = extractPlaceholders(text);

      expect(placeholders.has("condition")).toBe(true);
      expect(placeholders.has("if")).toBe(false);
    });
  });

  describe("parseFrontmatterKeys", () => {
    it("should extract frontmatter keys", () => {
      const frontmatter = `title: Test
type: adr
status: draft`;

      const keys = parseFrontmatterKeys(frontmatter);

      expect(keys.has("title")).toBe(true);
      expect(keys.has("type")).toBe(true);
      expect(keys.has("status")).toBe(true);
      expect(keys.size).toBe(3);
    });

    it("should handle nested structures", () => {
      const frontmatter = `title: Test
metadata:
  author: John
  date: 2024-01-01`;

      const keys = parseFrontmatterKeys(frontmatter);

      // parseFrontmatterKeys only extracts top-level keys (those at start of line)
      expect(keys.has("title")).toBe(true);
      expect(keys.has("metadata")).toBe(true);
      // Nested keys are not extracted by this simple parser
      expect(keys.has("author")).toBe(false);
      expect(keys.has("date")).toBe(false);
    });

    it("should handle empty frontmatter", () => {
      const keys = parseFrontmatterKeys("");

      expect(keys.size).toBe(0);
    });
  });

  describe("needsYamlQuoting", () => {
    it("should detect colons", () => {
      expect(needsYamlQuoting("key: value")).toBe(true);
      expect(needsYamlQuoting("http://example.com")).toBe(true);
    });

    it("should detect newlines", () => {
      expect(needsYamlQuoting("line1\nline2")).toBe(true);
    });

    it("should detect starting quotes", () => {
      expect(needsYamlQuoting('"quoted"')).toBe(true);
      expect(needsYamlQuoting("'quoted'")).toBe(true);
    });

    it("should detect YAML special characters", () => {
      expect(needsYamlQuoting("!important")).toBe(true);
      expect(needsYamlQuoting("&reference")).toBe(true);
      expect(needsYamlQuoting("*alias")).toBe(true);
    });

    it("should detect list-like patterns", () => {
      expect(needsYamlQuoting("- item")).toBe(true);
    });

    it("should detect leading/trailing whitespace", () => {
      expect(needsYamlQuoting(" value")).toBe(true);
      expect(needsYamlQuoting("value ")).toBe(true);
    });

    it("should detect YAML keywords", () => {
      expect(needsYamlQuoting("true")).toBe(true);
      expect(needsYamlQuoting("false")).toBe(true);
      expect(needsYamlQuoting("null")).toBe(true);
      expect(needsYamlQuoting("yes")).toBe(true);
      expect(needsYamlQuoting("no")).toBe(true);
      expect(needsYamlQuoting("on")).toBe(true);
      expect(needsYamlQuoting("off")).toBe(true);
      expect(needsYamlQuoting("TRUE")).toBe(true);
      expect(needsYamlQuoting("False")).toBe(true);
    });

    it("should detect pure numbers", () => {
      expect(needsYamlQuoting("123")).toBe(true);
      expect(needsYamlQuoting("456")).toBe(true);
    });

    it("should return false for safe strings", () => {
      expect(needsYamlQuoting("safe_value")).toBe(false);
      expect(needsYamlQuoting("SafeValue")).toBe(false);
      expect(needsYamlQuoting("value123")).toBe(false);
    });

    it("should return false for non-string values", () => {
      expect(needsYamlQuoting(123 as any)).toBe(false);
      expect(needsYamlQuoting(null as any)).toBe(false);
      expect(needsYamlQuoting(undefined as any)).toBe(false);
    });
  });

  describe("parseMarkdown", () => {
    it("should parse markdown to AST", () => {
      const body = "## Heading\n\nParagraph content.";

      const ast = parseMarkdown(body);

      expect(ast.type).toBe("root");
      expect(ast.children.length).toBeGreaterThan(0);
      expect(ast.children[0].type).toBe("heading");
    });

    it("should parse GFM features like tables", () => {
      const body = `| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |`;

      const ast = parseMarkdown(body);

      const table = ast.children.find(node => node.type === "table");
      expect(table).toBeDefined();
    });
  });

  describe("findSections", () => {
    it("should find H2 sections", () => {
      const body = `## Section 1

Content 1.

## Section 2

Content 2.`;

      const ast = parseMarkdown(body);
      const sections = findSections(ast);

      expect(sections.length).toBe(2);
      expect(sections[0].title).toBe("Section 1");
      expect(sections[0].id).toBe("section-1");
      expect(sections[1].title).toBe("Section 2");
      expect(sections[1].id).toBe("section-2");
    });

    it("should include H3 and H4 in section content", () => {
      const body = `## Main Section

### Subsection

Content here.

#### Sub-subsection

More content.`;

      const ast = parseMarkdown(body);
      const sections = findSections(ast);

      expect(sections.length).toBe(1);
      expect(sections[0].title).toBe("Main Section");

      const h3 = sections[0].content.find(node => node.type === "heading" && (node as any).depth === 3);
      const h4 = sections[0].content.find(node => node.type === "heading" && (node as any).depth === 4);

      expect(h3).toBeDefined();
      expect(h4).toBeDefined();
    });

    it("should normalize section IDs", () => {
      const body = `## Context & Background!

Content.

## Decision-Making Process

More content.`;

      const ast = parseMarkdown(body);
      const sections = findSections(ast);

      expect(sections[0].id).toBe("context-background");
      expect(sections[1].id).toBe("decision-making-process");
    });

    it("should ignore content before first H2", () => {
      const body = `Some preamble content.

## First Section

Section content.`;

      const ast = parseMarkdown(body);
      const sections = findSections(ast);

      expect(sections.length).toBe(1);
      expect(sections[0].title).toBe("First Section");
    });

    it("should handle headings with HTML anchors", () => {
      const body = `## <a id="summary"/>Summary

Content here.`;

      const ast = parseMarkdown(body);
      const sections = findSections(ast);

      expect(sections.length).toBe(1);
      expect(sections[0].title).toBe("Summary");
      expect(sections[0].id).toBe("summary");
    });

    it("should handle headings with emphasis and strong", () => {
      const body = `## *Emphasized* and **Strong** Heading

Content.`;

      const ast = parseMarkdown(body);
      const sections = findSections(ast);

      expect(sections.length).toBe(1);
      expect(sections[0].title).toBe("Emphasized and Strong Heading");
    });

    it("should handle headings with nested inline elements", () => {
      const body = `## Complex **bold _and italic_** Heading

Content.`;

      const ast = parseMarkdown(body);
      const sections = findSections(ast);

      expect(sections.length).toBe(1);
      expect(sections[0].title).toBe("Complex bold and italic Heading");
    });

    it("should preserve position information", () => {
      const body = `## First Section

Content.

## Second Section

More content.`;

      const ast = parseMarkdown(body);
      const sections = findSections(ast);

      expect(sections[0].line).toBeGreaterThan(0);
      expect(sections[0].column).toBeGreaterThan(0);
      expect(sections[0].position).toBeDefined();
    });
  });

  describe("stringifyMarkdown", () => {
    it("should stringify AST back to markdown", () => {
      const body = `## Heading

Paragraph content.

- List item 1
- List item 2`;

      const ast = parseMarkdown(body);
      const stringified = stringifyMarkdown(ast);

      expect(stringified).toContain("## Heading");
      expect(stringified).toContain("Paragraph content.");
      expect(stringified).toContain("- List item 1");
      expect(stringified).toContain("- List item 2");
    });

    it("should use canonical list markers", () => {
      const body = `* Item 1
* Item 2`;

      const ast = parseMarkdown(body);
      const stringified = stringifyMarkdown(ast);

      // Should convert to canonical - marker
      expect(stringified).toContain("- Item 1");
      expect(stringified).toContain("- Item 2");
    });

    it("should preserve ordered lists", () => {
      const body = `1. First
2. Second
3. Third`;

      const ast = parseMarkdown(body);
      const stringified = stringifyMarkdown(ast);

      expect(stringified).toMatch(/1\.\s+First/);
      expect(stringified).toMatch(/2\.\s+Second/);
      expect(stringified).toMatch(/3\.\s+Third/);
    });
  });
});
