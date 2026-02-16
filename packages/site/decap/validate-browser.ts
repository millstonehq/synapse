/**
 * Browser-compatible validation for Decap CMS
 *
 * This module provides client-side validation that mirrors the server-side
 * `synapse validate` command, running entirely in the browser.
 */

import Ajv from 'ajv';
import addFormats from 'ajv-formats';
import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkGfm from 'remark-gfm';
import type { Root, Heading, Content, List, PhrasingContent } from 'mdast';
import { DOC_TYPES, isDocType, TEMPLATE_REGISTRY, type DocType } from './doc-types.generated.js';

export { DOC_TYPES, isDocType, TEMPLATE_REGISTRY };
export type { DocType };

export interface ValidationIssue {
  type: 'error' | 'warning';
  code: string;
  message: string;
  field?: string;
  sectionId?: string;
  line?: number;
}

export interface ValidationResult {
  success: boolean;
  issues: ValidationIssue[];
}

export interface ValidationContext {
  /** All valid wikilink targets (file basenames without .md) */
  vaultIndex: string[];
  /** JSON schemas keyed by document type */
  schemas: Record<string, any>;
  /** Body grammars keyed by document type */
  bodyGrammars: Record<string, any>;
}

export interface SectionNode {
  id: string;
  title: string;
  depth: number;
  line: number;
  column: number;
  content: Content[];
}

// ============================================================================
// Schema Validation
// ============================================================================

/**
 * Validates frontmatter against a JSON schema
 */
export function validateSchema(
  frontmatter: Record<string, any>,
  schema: any
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];

  // Clean schema for Ajv compatibility
  const cleanSchema = { ...schema };
  delete cleanSchema.$schema;
  delete cleanSchema.$id;

  const ajv = new Ajv({
    allErrors: true,
    strict: false,
    validateSchema: false
  });

  addFormats(ajv);

  try {
    const validate = ajv.compile(cleanSchema);
    const valid = validate(frontmatter);

    if (!valid && validate.errors) {
      for (const error of validate.errors) {
        const path = error.instancePath || '/';
        let message = error.message || 'validation error';

        if (error.keyword === 'required') {
          const missingProp = (error.params as any).missingProperty;
          message = `missing required property '${missingProp}'`;
        } else if (error.keyword === 'type') {
          const expectedType = (error.params as any).type;
          message = `must be ${expectedType}`;
        } else if (error.keyword === 'const') {
          const expectedValue = (error.params as any).allowedValue;
          message = `must be equal to '${expectedValue}'`;
        }

        issues.push({
          type: 'error',
          code: 'SCHEMA_VALIDATION_ERROR',
          message: `${path} ${message}`,
          field: path.replace(/^\//, '') || undefined
        });
      }
    }
  } catch (error) {
    issues.push({
      type: 'error',
      code: 'SCHEMA_COMPILATION_ERROR',
      message: `Schema error: ${(error as Error).message}`
    });
  }

  return issues;
}

// ============================================================================
// Markdown Parsing
// ============================================================================

/**
 * Parses markdown into AST
 */
function parseMarkdown(body: string): Root {
  const processor = unified().use(remarkParse).use(remarkGfm);
  return processor.parse(body) as Root;
}

/**
 * Extracts heading text from AST node
 */
function extractHeadingText(heading: Heading): string {
  let text = '';
  for (const child of heading.children) {
    if (child.type === 'text') {
      text += child.value;
    } else if (child.type === 'html') {
      continue;
    } else if ('children' in child) {
      text += extractInlineText(child.children as PhrasingContent[]);
    }
  }
  return text.trim();
}

function extractInlineText(children: PhrasingContent[]): string {
  let text = '';
  for (const child of children) {
    if (child.type === 'text') {
      text += child.value;
    } else if ('children' in child) {
      text += extractInlineText(child.children as PhrasingContent[]);
    }
  }
  return text;
}

/**
 * Normalizes section title to ID
 */
function normalizeSectionId(title: string): string {
  return title
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '');
}

/**
 * Finds all H2 sections in the AST
 */
function findSections(ast: Root): SectionNode[] {
  const sections: SectionNode[] = [];
  let currentSection: SectionNode | null = null;

  for (const node of ast.children) {
    if (node.type === 'heading' && node.depth === 2) {
      if (currentSection) {
        sections.push(currentSection);
      }
      const title = extractHeadingText(node);
      currentSection = {
        id: normalizeSectionId(title),
        title,
        depth: node.depth,
        line: node.position?.start.line || 0,
        column: node.position?.start.column || 0,
        content: []
      };
    } else if (currentSection) {
      currentSection.content.push(node);
    }
  }

  if (currentSection) {
    sections.push(currentSection);
  }

  return sections;
}

// ============================================================================
// Body Grammar Validation
// ============================================================================

/**
 * Validates body structure against grammar rules
 */
export function validateBodyGrammar(
  body: string,
  grammar: any,
  docType: DocType
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];

  if (!grammar || !grammar.sections) {
    return issues; // No grammar defined, skip
  }

  const ast = parseMarkdown(body);
  const sections = findSections(ast);

  // Check required sections
  for (const rule of grammar.sections) {
    const found = sections.find(s =>
      s.id === rule.id ||
      s.title.toLowerCase() === rule.title.toLowerCase()
    );

    if (rule.required && !found) {
      issues.push({
        type: 'error',
        code: 'MISSING_REQUIRED_SECTION',
        message: `Missing required section. Add this H2 heading to your document:\n\n## ${rule.title}`,
        sectionId: rule.id
      });
    }

    // Validate section shape if present
    if (found && rule.shape) {
      const shapeIssues = validateSectionShape(found, rule);
      issues.push(...shapeIssues);
    }
  }

  // Check section order
  const ruleOrder = new Map(grammar.sections.map((r: any) => [r.id, r.order]));
  const ruleById = new Map(grammar.sections.map((r: any) => [r.id, r]));
  let lastOrder = 0;
  let lastSectionTitle = '';
  for (const section of sections) {
    const order = ruleOrder.get(section.id);
    if (order !== undefined && order < lastOrder) {
      // Find what section should come before this one
      const expectedBefore = grammar.sections
        .filter((r: any) => r.order < order)
        .sort((a: any, b: any) => b.order - a.order)[0];

      issues.push({
        type: 'error',
        code: 'SECTION_OUT_OF_ORDER',
        message: `Section "## ${section.title}" is out of order. It should appear ${expectedBefore ? `after "## ${expectedBefore.title}"` : 'earlier in the document'}, not after "## ${lastSectionTitle}".`,
        sectionId: section.id,
        line: section.line
      });
    }
    if (order !== undefined) {
      lastOrder = order;
      lastSectionTitle = section.title;
    }
  }

  return issues;
}

/**
 * Validates section content shape
 */
function validateSectionShape(section: SectionNode, rule: any): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const shape = rule.shape;

  if (shape.type === 'list') {
    const lists = section.content.filter(n => n.type === 'list') as List[];
    const listTypeExample = shape.ordered
      ? '1. First item\n2. Second item\n3. Third item'
      : '- First item\n- Second item\n- Third item';

    if (lists.length === 0 && shape.minItems && shape.minItems > 0) {
      issues.push({
        type: 'error',
        code: 'MISSING_LIST',
        message: `Section "## ${rule.title}" requires a ${shape.ordered ? 'numbered' : 'bulleted'} list. Add items like:\n\n${listTypeExample}`,
        sectionId: rule.id
      });
    }

    for (const list of lists) {
      if (shape.ordered !== undefined && list.ordered !== shape.ordered) {
        const currentType = list.ordered ? 'numbered (1. 2. 3.)' : 'bulleted (-)';
        const expectedType = shape.ordered ? 'numbered (1. 2. 3.)' : 'bulleted (-)';
        issues.push({
          type: 'error',
          code: 'WRONG_LIST_TYPE',
          message: `Section "## ${rule.title}" has a ${currentType} list but requires a ${expectedType} list. Change to:\n\n${listTypeExample}`,
          sectionId: rule.id
        });
      }
      if (shape.minItems && list.children.length < shape.minItems) {
        issues.push({
          type: 'error',
          code: 'INSUFFICIENT_LIST_ITEMS',
          message: `Section "## ${rule.title}" needs at least ${shape.minItems} list items (currently has ${list.children.length}).`,
          sectionId: rule.id
        });
      }
    }
  }

  if (shape.type === 'table') {
    const tables = section.content.filter(n => n.type === 'table');
    if (tables.length === 0) {
      issues.push({
        type: 'error',
        code: 'MISSING_TABLE',
        message: `Section "## ${rule.title}" requires a table. Add a markdown table like:\n\n| Column 1 | Column 2 |\n|----------|----------|\n| Data     | Data     |`,
        sectionId: rule.id
      });
    }
  }

  if (shape.type === 'flow' && shape.allowedNodes) {
    const nodeTypeNames: Record<string, string> = {
      'paragraph': 'paragraphs',
      'list': 'lists',
      'table': 'tables',
      'code': 'code blocks',
      'blockquote': 'blockquotes',
      'heading': 'headings'
    };
    for (const node of section.content) {
      if (!shape.allowedNodes.includes(node.type)) {
        const nodeName = nodeTypeNames[node.type] || node.type;
        const allowedNames = shape.allowedNodes.map((t: string) => nodeTypeNames[t] || t).join(', ');
        issues.push({
          type: 'error',
          code: 'DISALLOWED_NODE_TYPE',
          message: `Section "## ${rule.title}" does not allow ${nodeName}. Only ${allowedNames} are permitted.`,
          sectionId: rule.id,
          line: node.position?.start.line
        });
      }
    }
  }

  return issues;
}

// ============================================================================
// Wikilink Validation
// ============================================================================

/**
 * Extracts wikilinks from markdown content
 */
export function extractWikilinks(content: string): string[] {
  const wikilinks: string[] = [];
  const regex = /\[\[([^\]|]+)(?:\|[^\]]+)?\]\]/g;
  let match;

  while ((match = regex.exec(content)) !== null) {
    const target = match[1].trim();
    if (target && !wikilinks.includes(target)) {
      wikilinks.push(target);
    }
  }

  return wikilinks;
}

/**
 * Validates that wikilinks exist in the vault
 */
export function validateWikilinks(
  body: string,
  vaultIndex: string[]
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const wikilinks = extractWikilinks(body);

  // Normalize vault index for matching
  const normalizedIndex = new Set(
    vaultIndex.map(f => f.toLowerCase().replace(/\s+/g, '-'))
  );

  for (const link of wikilinks) {
    const normalized = link.toLowerCase().replace(/\s+/g, '-');

    // Check various matching patterns
    const exists = normalizedIndex.has(normalized) ||
      normalizedIndex.has(normalized.replace(/\.md$/, '')) ||
      [...normalizedIndex].some(f =>
        f.endsWith(`/${normalized}`) ||
        f.endsWith(`-${normalized}`) ||
        f === normalized
      );

    if (!exists) {
      issues.push({
        type: 'error',
        code: 'BROKEN_LINK',
        message: `Broken link: [[${link}]] - This document doesn't exist. Check the spelling or create the document first.`
      });
    }
  }

  return issues;
}

// ============================================================================
// Cross-Link Validation (Type-Specific Rules)
// ============================================================================

/**
 * Validates type-specific cross-link requirements
 */
export function validateCrossLinks(
  frontmatter: Record<string, any>,
  body: string,
  vaultIndex: string[]
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const docType = frontmatter.type as DocType;

  if (!docType || !isDocType(docType)) {
    return issues;
  }

  switch (docType) {
    case 'process':
      // Process must reference at least one standard
      if (!frontmatter.related_standards ||
          !Array.isArray(frontmatter.related_standards) ||
          frontmatter.related_standards.length === 0) {
        issues.push({
          type: 'error',
          code: 'MISSING_REQUIRED_LINK',
          message: 'Process documents must reference at least one standard in related_standards',
          field: 'related_standards'
        });
      }
      break;

    case 'sop':
      // SOP must reference a parent process
      if (!frontmatter.related_process ||
          typeof frontmatter.related_process !== 'string' ||
          frontmatter.related_process.trim() === '') {
        issues.push({
          type: 'error',
          code: 'MISSING_REQUIRED_LINK',
          message: 'SOP must reference a parent process in related_process',
          field: 'related_process'
        });
      }
      break;

    case 'runbook':
      // Runbook must reference a system in ## Service section
      const serviceMatch = body.match(/##\s+Service\s*\n+([^\n#]+)/);
      const serviceContent = serviceMatch ? serviceMatch[1].trim() : '';
      const serviceLinks = extractWikilinks(serviceContent);

      if (!serviceContent || serviceLinks.length === 0) {
        issues.push({
          type: 'error',
          code: 'MISSING_REQUIRED_LINK',
          message: 'Runbook must reference a system/service in the ## Service section',
          field: 'service'
        });
      }
      break;
  }

  return issues;
}

// ============================================================================
// Naming Validation
// ============================================================================

/**
 * Validates document is in correct folder
 */
export function validateNaming(
  filePath: string,
  frontmatter: Record<string, any>
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const docType = frontmatter.type as DocType;

  if (!docType || !isDocType(docType)) {
    return issues;
  }

  // Check folder placement
  const expectedFolder = TEMPLATE_REGISTRY[docType].folder;
  if (!filePath.includes(expectedFolder)) {
    issues.push({
      type: 'error',
      code: 'WRONG_FOLDER',
      message: `Document of type '${docType}' should be in ${expectedFolder}`,
      field: 'path'
    });
  }

  // Validate filename for ADRs
  if (docType === 'adr') {
    const filename = filePath.split('/').pop()?.replace('.md', '') || '';
    const adrPattern = /^ADR-\d{4,}-[a-z0-9-]+$/;
    if (!adrPattern.test(filename)) {
      issues.push({
        type: 'error',
        code: 'INVALID_ADR_FILENAME',
        message: 'ADR filename must match pattern ADR-####-slug.md',
        field: 'filename'
      });
    }
  }

  return issues;
}

// ============================================================================
// Main Validation Function
// ============================================================================

/**
 * Validates a document for Decap CMS
 *
 * @param frontmatter - The document frontmatter
 * @param body - The document body (markdown)
 * @param filePath - The file path within the vault
 * @param context - Validation context (vault index, schemas, grammars)
 * @returns Validation result with any issues
 */
export function validateDocument(
  frontmatter: Record<string, any>,
  body: string,
  filePath: string,
  context: ValidationContext
): ValidationResult {
  const issues: ValidationIssue[] = [];

  const docType = frontmatter.type;

  // Validate type is present
  if (!docType) {
    issues.push({
      type: 'error',
      code: 'MISSING_TYPE',
      message: 'Document type is required',
      field: 'type'
    });
    return { success: false, issues };
  }

  if (!isDocType(docType)) {
    issues.push({
      type: 'error',
      code: 'INVALID_TYPE',
      message: `Invalid document type: '${docType}'`,
      field: 'type'
    });
    return { success: false, issues };
  }

  // 1. Schema validation
  const schema = context.schemas[docType];
  if (schema) {
    issues.push(...validateSchema(frontmatter, schema));
  }

  // 2. Body grammar validation
  const grammar = context.bodyGrammars[docType];
  if (grammar) {
    issues.push(...validateBodyGrammar(body, grammar, docType));
  }

  // 3. Wikilink validation
  issues.push(...validateWikilinks(body, context.vaultIndex));

  // 4. Cross-link validation (type-specific rules)
  issues.push(...validateCrossLinks(frontmatter, body, context.vaultIndex));

  // 5. Naming validation
  issues.push(...validateNaming(filePath, frontmatter));

  const errors = issues.filter(i => i.type === 'error');

  return {
    success: errors.length === 0,
    issues
  };
}

export default validateDocument;
