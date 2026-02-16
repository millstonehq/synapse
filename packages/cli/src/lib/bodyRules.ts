/**
 * Body validation rules for Synapse document types
 * Implements AST-based validation of Markdown body structure
 */

import fsExtra from 'fs-extra';
import * as path from 'path';
import { createRequire } from 'module';
import type { Root, Content, List, Heading, Paragraph, Table, ListItem, BlockContent, PhrasingContent } from 'mdast';
import { parseMarkdown, findSections, stringifyMarkdown, type SectionNode } from './markdown.js';

const fs = fsExtra;

// ============================================================================
// Type Definitions
// ============================================================================

export interface ValidationIssue {
  notePath: string;
  type: 'error';
  code: string;
  message: string;
  sectionId?: string;
  line?: number;
  column?: number;
}

export interface SectionRule {
  id: string;
  title: string;
  alternativeTitles?: string[];
  required: boolean;
  order: number;
  shape: SectionShape;
}

export type SectionShape =
  | { type: 'paragraphs' }
  | { type: 'list'; ordered?: boolean; maxDepth?: number; minItems?: number }
  | { type: 'flow'; allowedNodes: string[] }
  | { type: 'table'; requiredHeaders?: string[]; minRows?: number }
  | {
      type: 'milestoneList';
      requireH3: boolean;
      requiredSubsections: string[];
      requiredFields?: string[];
    };

export interface BodyRules {
  documentTypes: Record<
    string,
    {
      displayName: string;
      sections: SectionRule[];
    }
  >;
}

// ============================================================================
// Rule Loading
// ============================================================================

/**
 * Loads body rules from the body-grammars directory
 */
export async function loadBodyRules(root?: string): Promise<BodyRules> {
  const grammarsDir = root
    ? path.resolve(root, 'schemas/body-grammars')
    : getDefaultGrammarsDir();

  if (!(await fs.pathExists(grammarsDir))) {
    throw new Error(`Body grammars directory not found at ${grammarsDir}`);
  }

  // Read all .body-grammar.json files
  const files = await fs.readdir(grammarsDir);
  const grammarFiles = files.filter(f => f.endsWith('.body-grammar.json'));

  if (grammarFiles.length === 0) {
    throw new Error(`No body grammar files found in ${grammarsDir}`);
  }

  // Load each grammar file and construct BodyRules
  const documentTypes: Record<string, { displayName: string; sections: SectionRule[] }> = {};

  for (const file of grammarFiles) {
    const grammarPath = path.join(grammarsDir, file);
    const grammarContent = await fs.readFile(grammarPath, 'utf-8');
    const grammar = JSON.parse(grammarContent);

    // Extract the type from the grammar
    const type = grammar.type;
    if (!type) {
      throw new Error(`Body grammar file ${file} is missing 'type' field`);
    }

    // Convert sections to SectionRule format
    const sections: SectionRule[] = grammar.sections.map((section: any) => ({
      id: section.id,
      title: section.title,
      alternativeTitles: section.alternativeTitles,
      required: section.required,
      order: section.order,
      shape: section.shape
    }));

    documentTypes[type] = {
      displayName: grammar.displayName || type,
      sections
    };
  }

  return { documentTypes };
}

// ============================================================================
// Formatting
// ============================================================================

/**
 * Formats a document body according to grammar rules
 * - Inserts missing required sections in canonical order
 * - Normalizes section titles to match grammar
 * - Normalizes heading levels (H2 for sections)
 * - Normalizes list markers
 * - Preserves existing content
 * @param body - The original markdown body
 * @param rules - Body grammar rules
 * @param type - Document type
 * @returns Formatted markdown body
 */
export function formatBody(
  body: string,
  rules: BodyRules,
  type: string
): string {
  const typeRules = rules.documentTypes[type];
  if (!typeRules) {
    // No rules for this type, return body as-is
    return body;
  }

  // Parse existing body
  const ast = parseMarkdown(body);
  const existingSections = findSections(ast);

  // Build a map of existing sections by normalized ID
  const sectionMap = new Map<string, SectionNode>();
  for (const section of existingSections) {
    sectionMap.set(section.id, section);
  }

  // Build new AST with sections in canonical order
  const newChildren: Content[] = [];

  for (const rule of typeRules.sections) {
    const existingSection = sectionMap.get(rule.id);

    if (existingSection) {
      // Use existing section but normalize the title
      const normalizedHeading: Heading = {
        type: 'heading',
        depth: 2, // Always use H2 for sections
        children: [{ type: 'text', value: rule.title }],
      };

      // Add normalized heading
      newChildren.push(normalizedHeading);

      // Add existing content, normalizing lists
      for (const node of existingSection.content) {
        if (node.type === 'list') {
          newChildren.push(normalizeList(node, rule.shape));
        } else if (node.type === 'heading' && node.depth > 2) {
          // Preserve subsection headings (H3, H4, etc.)
          newChildren.push(node);
        } else if (node.type !== 'heading') {
          // Preserve non-heading content
          newChildren.push(node);
        }
      }
    } else if (rule.required) {
      // Insert missing required section with placeholder
      const heading: Heading = {
        type: 'heading',
        depth: 2,
        children: [{ type: 'text', value: rule.title }],
      };

      const placeholder: Paragraph = {
        type: 'paragraph',
        children: [{ type: 'text', value: '[TODO: Complete this section]' }],
      };

      newChildren.push(heading, placeholder);
    }

    // Add blank line after each section for readability
    // (This is handled by the stringifier)
  }

  // Build new AST
  const formattedAst: Root = {
    type: 'root',
    children: newChildren,
  };

  return stringifyMarkdown(formattedAst);
}

/**
 * Normalizes a list node according to shape rules
 * - Converts to correct list type (ordered/unordered)
 * - Uses canonical markers (- for unordered, 1. for ordered)
 * - Flattens lists that exceed maxDepth
 */
function normalizeList(list: List, shape: SectionShape): List {
  const normalizedList: List = {
    type: 'list',
    ordered: false,
    spread: false,
    children: list.children.map((item) => ({ ...item })),
  };

  // Determine target ordered state
  if (shape.type === 'list' && shape.ordered !== undefined) {
    normalizedList.ordered = shape.ordered;
  } else {
    // Preserve original ordering if not specified
    normalizedList.ordered = list.ordered;
  }

  // Flatten if maxDepth is specified and exceeded
  if (shape.type === 'list' && shape.maxDepth !== undefined) {
    const currentDepth = getListDepth(list);
    if (currentDepth > shape.maxDepth) {
      normalizedList.children = flattenList(list, shape.maxDepth);
    }
  }

  return normalizedList;
}

/**
 * Flattens a nested list to a maximum depth
 */
function flattenList(list: List, maxDepth: number, currentDepth: number = 1): ListItem[] {
  const flattened: ListItem[] = [];

  for (const item of list.children) {
    if (currentDepth >= maxDepth) {
      // At max depth, flatten any nested lists
      const flatItemChildren: BlockContent[] = [];
      for (const child of item.children) {
        if (child.type === 'list') {
          // Extract items from nested list and add as top-level items
          for (const nestedItem of child.children) {
            flattened.push(nestedItem);
          }
        } else {
          flatItemChildren.push(child as BlockContent);
        }
      }
      if (flatItemChildren.length > 0) {
        const flatItem: ListItem = {
          type: 'listItem',
          children: flatItemChildren,
        };
        flattened.push(flatItem);
      }
    } else {
      // Below max depth, recursively process children
      const newItemChildren: BlockContent[] = [];
      for (const child of item.children) {
        if (child.type === 'list') {
          const flattenedChildren = flattenList(child, maxDepth, currentDepth + 1);
          newItemChildren.push({
            ...child,
            children: flattenedChildren,
          });
        } else {
          newItemChildren.push(child as BlockContent);
        }
      }
      const newItem: ListItem = {
        type: 'listItem',
        children: newItemChildren,
      };
      flattened.push(newItem);
    }
  }

  return flattened;
}

/**
 * Resolve the body grammars directory using a cascade:
 * 1. Local project override: {projectRoot}/schemas/body-grammars/
 * 2. @millstone/synapse-schemas npm package
 * 3. Error with helpful message
 */
function getDefaultGrammarsDir(): string {
  // Priority 1: Local project override
  const localPaths = [
    path.resolve(process.cwd(), 'schemas/body-grammars'),
    path.resolve(process.cwd(), '../schemas/body-grammars'),
    path.resolve(process.cwd(), '../../schemas/body-grammars'),
  ];

  for (const p of localPaths) {
    if (fs.existsSync(p)) {
      try {
        const files = fs.readdirSync(p);
        const hasGrammars = files.some(f => f.endsWith('.body-grammar.json'));
        if (hasGrammars) {
          return p;
        }
      } catch {
        continue;
      }
    }
  }

  // Priority 2: @millstone/synapse-schemas package
  try {
    const require = createRequire(import.meta.url);
    const pkgPath = require.resolve('@millstone/synapse-schemas/package.json');
    const pkgDir = path.dirname(pkgPath);
    const grammarsDir = path.join(pkgDir, 'body-grammars');
    if (fs.existsSync(grammarsDir)) {
      return grammarsDir;
    }
  } catch {
    // Package not installed
  }

  // Priority 3: Error with helpful message
  throw new Error(
    'Could not find body grammar schemas. Either place schemas in {projectRoot}/schemas/body-grammars/ ' +
    'or install the @millstone/synapse-schemas package: npm install @millstone/synapse-schemas'
  );
}

// ============================================================================
// Body Validation
// ============================================================================

/**
 * Validates markdown body against rules for a given document type
 */
export function validateBody(
  body: string,
  rules: BodyRules,
  type: string,
  notePath: string
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];

  // Get rules for this document type
  const typeRules = rules.documentTypes[type];
  if (!typeRules) {
    issues.push({
      notePath,
      type: 'error',
      code: 'unknown-type',
      message: `No body rules defined for document type '${type}'`,
    });
    return issues;
  }

  // Parse the markdown body
  const ast = parseMarkdown(body);
  const sections = findSections(ast);

  // Build a map of found sections by ID
  const foundSections = new Map<string, SectionNode[]>();
  for (const section of sections) {
    if (!foundSections.has(section.id)) {
      foundSections.set(section.id, []);
    }
    foundSections.get(section.id)!.push(section);
  }

  // Check each rule
  for (const rule of typeRules.sections) {
    const matchingSection = findMatchingSection(sections, rule);

    // Check required sections
    if (rule.required && !matchingSection) {
      issues.push({
        notePath,
        type: 'error',
        code: 'missing-required-section',
        message: `Missing required section "${rule.title}"`,
        sectionId: rule.id,
      });
      continue;
    }

    if (!matchingSection) {
      continue; // Optional section not present
    }

    // Check uniqueness
    const allMatches = findAllMatchingSections(sections, rule);
    if (allMatches.length > 1) {
      for (const duplicate of allMatches.slice(1)) {
        issues.push({
          notePath,
          type: 'error',
          code: 'duplicate-section',
          message: `Duplicate section "${rule.title}" (appears ${allMatches.length} times)`,
          sectionId: rule.id,
          line: duplicate.line,
          column: duplicate.column,
        });
      }
    }

    // Check shape
    const shapeIssues = validateSectionShape(
      matchingSection,
      rule,
      notePath
    );
    issues.push(...shapeIssues);
  }

  // Check section order
  const orderIssues = validateSectionOrder(sections, typeRules.sections, notePath);
  issues.push(...orderIssues);

  return issues;
}

/**
 * Finds a section that matches the rule (by ID or alternative titles)
 */
function findMatchingSection(
  sections: SectionNode[],
  rule: SectionRule
): SectionNode | undefined {
  return sections.find((section) => {
    // Match by normalized ID
    if (section.id === rule.id) {
      return true;
    }

    // Match by title (case-insensitive)
    const normalizedTitle = section.title.toLowerCase().trim();
    const ruleTitle = rule.title.toLowerCase().trim();

    if (normalizedTitle === ruleTitle) {
      return true;
    }

    // Match by alternative titles
    if (rule.alternativeTitles) {
      for (const altTitle of rule.alternativeTitles) {
        if (normalizedTitle === altTitle.toLowerCase().trim()) {
          return true;
        }
      }
    }

    return false;
  });
}

/**
 * Finds all sections that match the rule
 */
function findAllMatchingSections(
  sections: SectionNode[],
  rule: SectionRule
): SectionNode[] {
  return sections.filter((section) => {
    const normalizedTitle = section.title.toLowerCase().trim();
    const ruleTitle = rule.title.toLowerCase().trim();

    if (section.id === rule.id || normalizedTitle === ruleTitle) {
      return true;
    }

    if (rule.alternativeTitles) {
      for (const altTitle of rule.alternativeTitles) {
        if (normalizedTitle === altTitle.toLowerCase().trim()) {
          return true;
        }
      }
    }

    return false;
  });
}

/**
 * Validates that sections appear in the canonical order
 */
function validateSectionOrder(
  sections: SectionNode[],
  rules: SectionRule[],
  notePath: string
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];

  // Build a map of section IDs to their expected order
  const expectedOrder = new Map<string, number>();
  for (const rule of rules) {
    expectedOrder.set(rule.id, rule.order);

    // Also map alternative titles
    if (rule.alternativeTitles) {
      for (const altTitle of rule.alternativeTitles) {
        const altId = altTitle.toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]/g, '');
        expectedOrder.set(altId, rule.order);
      }
    }
  }

  // Check the order of found sections
  let lastOrder = 0;
  for (const section of sections) {
    const order = expectedOrder.get(section.id);

    if (order !== undefined) {
      if (order < lastOrder) {
        issues.push({
          notePath,
          type: 'error',
          code: 'section-out-of-order',
          message: `Section "${section.title}" appears out of order (expected order: ${order}, follows: ${lastOrder})`,
          sectionId: section.id,
          line: section.line,
          column: section.column,
        });
      }
      lastOrder = order;
    }
  }

  return issues;
}

/**
 * Validates the shape of a section's content
 */
function validateSectionShape(
  section: SectionNode,
  rule: SectionRule,
  notePath: string
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const shape = rule.shape;

  switch (shape.type) {
    case 'paragraphs':
      return validateParagraphsShape(section, rule, notePath);

    case 'list':
      return validateListShape(section, rule, shape, notePath);

    case 'flow':
      return validateFlowShape(section, rule, shape, notePath);

    case 'table':
      return validateTableShape(section, rule, shape, notePath);

    case 'milestoneList':
      return validateMilestoneListShape(section, rule, shape, notePath);

    default:
      issues.push({
        notePath,
        type: 'error',
        code: 'unknown-shape',
        message: `Unknown shape type for section "${rule.title}"`,
        sectionId: rule.id,
        line: section.line,
      });
  }

  return issues;
}

/**
 * Validates paragraphs shape
 */
function validateParagraphsShape(
  section: SectionNode,
  rule: SectionRule,
  notePath: string
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];

  for (const node of section.content) {
    if (node.type !== 'paragraph') {
      issues.push({
        notePath,
        type: 'error',
        code: 'invalid-section-content',
        message: `Section "${rule.title}" should only contain paragraphs, found ${node.type}`,
        sectionId: rule.id,
        line: node.position?.start.line,
        column: node.position?.start.column,
      });
    }
  }

  return issues;
}

/**
 * Validates list shape
 */
function validateListShape(
  section: SectionNode,
  rule: SectionRule,
  shape: Extract<SectionShape, { type: 'list' }>,
  notePath: string
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];

  // Find lists in the content
  const lists = section.content.filter((node) => node.type === 'list') as List[];

  if (lists.length === 0 && shape.minItems && shape.minItems > 0) {
    issues.push({
      notePath,
      type: 'error',
      code: 'missing-list',
      message: `Section "${rule.title}" should contain a list`,
      sectionId: rule.id,
      line: section.line,
    });
    return issues;
  }

  // Only check the first list for ordered/unordered requirement
  // (subsequent lists may be nested details with different formatting)
  const firstList = lists[0];
  if (firstList && shape.ordered !== undefined && firstList.ordered !== shape.ordered) {
    const expectedType = shape.ordered ? 'numbered (1. 2. 3.)' : 'bulleted (-)';
    const actualType = firstList.ordered ? 'numbered' : 'bulleted';
    const lineNum = firstList.position?.start.line || section.line;
    issues.push({
      notePath,
      type: 'error',
      code: 'wrong-list-type',
      message: `Section "## ${rule.title}" at line ${lineNum}: expected ${expectedType} list but found ${actualType}. The first list in this section must be ${shape.ordered ? 'numbered' : 'bulleted'}.`,
      sectionId: rule.id,
      line: lineNum,
    });
  }

  for (const list of lists) {

    // Check minimum items
    if (shape.minItems && list.children.length < shape.minItems) {
      issues.push({
        notePath,
        type: 'error',
        code: 'insufficient-list-items',
        message: `Section "${rule.title}" list should have at least ${shape.minItems} items, found ${list.children.length}`,
        sectionId: rule.id,
        line: list.position?.start.line,
      });
    }

    // Check max depth
    if (shape.maxDepth !== undefined) {
      const depth = getListDepth(list);
      if (depth > shape.maxDepth) {
        issues.push({
          notePath,
          type: 'error',
          code: 'list-too-deep',
          message: `Section "${rule.title}" list exceeds maximum depth of ${shape.maxDepth} (found depth: ${depth})`,
          sectionId: rule.id,
          line: list.position?.start.line,
        });
      }
    }
  }

  return issues;
}

/**
 * Gets the maximum nesting depth of a list
 */
function getListDepth(list: List, currentDepth: number = 1): number {
  let maxDepth = currentDepth;

  for (const item of list.children) {
    for (const child of item.children) {
      if (child.type === 'list') {
        const childDepth = getListDepth(child, currentDepth + 1);
        maxDepth = Math.max(maxDepth, childDepth);
      }
    }
  }

  return maxDepth;
}

/**
 * Validates flow shape (mixed content)
 */
function validateFlowShape(
  section: SectionNode,
  rule: SectionRule,
  shape: Extract<SectionShape, { type: 'flow' }>,
  notePath: string
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];

  for (const node of section.content) {
    if (!shape.allowedNodes.includes(node.type)) {
      issues.push({
        notePath,
        type: 'error',
        code: 'disallowed-node-type',
        message: `Section "${rule.title}" does not allow ${node.type} nodes (allowed: ${shape.allowedNodes.join(', ')})`,
        sectionId: rule.id,
        line: node.position?.start.line,
        column: node.position?.start.column,
      });
    }
  }

  return issues;
}

/**
 * Validates table shape
 */
function validateTableShape(
  section: SectionNode,
  rule: SectionRule,
  shape: Extract<SectionShape, { type: 'table' }>,
  notePath: string
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];

  // Filter for tables, ignoring blank lines (paragraph nodes with no content)
  const tables = section.content.filter((node) => {
    if (node.type === 'table') return true;
    // Allow blank paragraphs (they don't break table validation)
    if (node.type === 'paragraph' && 'children' in node) {
      const hasContent = node.children.some((child: any) =>
        child.type === 'text' && child.value.trim().length > 0
      );
      return false; // Don't count paragraphs as tables, even if blank
    }
    return false;
  }) as Table[];

  if (tables.length === 0) {
    issues.push({
      notePath,
      type: 'error',
      code: 'missing-table',
      message: `Section "${rule.title}" should contain a table`,
      sectionId: rule.id,
      line: section.line,
    });
    return issues;
  }

  for (const table of tables) {
    // Check required headers
    if (shape.requiredHeaders && table.children.length > 0) {
      const headerRow = table.children[0];
      const headers = headerRow.children.map((cell) => {
        // Extract text from cell
        return cell.children
          .map((child) => (child.type === 'text' ? child.value : ''))
          .join('')
          .trim();
      });

      for (const requiredHeader of shape.requiredHeaders) {
        if (!headers.includes(requiredHeader)) {
          issues.push({
            notePath,
            type: 'error',
            code: 'missing-table-header',
            message: `Table in "${rule.title}" missing required header: ${requiredHeader}`,
            sectionId: rule.id,
            line: table.position?.start.line,
          });
        }
      }
    }

    // Check minimum rows (excluding header)
    if (shape.minRows !== undefined) {
      const dataRows = table.children.length - 1;
      if (dataRows < shape.minRows) {
        issues.push({
          notePath,
          type: 'error',
          code: 'insufficient-table-rows',
          message: `Table in "${rule.title}" should have at least ${shape.minRows} data rows, found ${dataRows}`,
          sectionId: rule.id,
          line: table.position?.start.line,
        });
      }
    }
  }

  return issues;
}

/**
 * Validates milestone list shape (SOW/PRD specific)
 */
function validateMilestoneListShape(
  section: SectionNode,
  rule: SectionRule,
  shape: Extract<SectionShape, { type: 'milestoneList' }>,
  notePath: string
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];

  // Look for H3 headings in the content
  const milestones = section.content.filter(
    (node) => node.type === 'heading' && node.depth === 3
  ) as Heading[];

  if (shape.requireH3 && milestones.length === 0) {
    issues.push({
      notePath,
      type: 'error',
      code: 'no-milestones',
      message: `Section "${rule.title}" should contain milestone blocks (H3 headings)`,
      sectionId: rule.id,
      line: section.line,
    });
  }

  // For each milestone, check for required subsections (H4)
  if (shape.requiredSubsections && shape.requiredSubsections.length > 0 && milestones.length > 0) {
    // Build a map of milestone positions to their content
    const milestoneGroups: Map<Heading, Content[]> = new Map();

    // Group content by milestone
    let currentMilestone: Heading | null = null;
    let currentContent: Content[] = [];

    for (const node of section.content) {
      if (node.type === 'heading' && node.depth === 3) {
        // Save previous milestone's content if any
        if (currentMilestone) {
          milestoneGroups.set(currentMilestone, currentContent);
        }
        // Start new milestone
        currentMilestone = node;
        currentContent = [];
      } else if (currentMilestone) {
        // Add to current milestone's content
        currentContent.push(node);
      }
    }

    // Save the last milestone's content
    if (currentMilestone) {
      milestoneGroups.set(currentMilestone, currentContent);
    }

    // Validate each milestone's subsections
    for (const [milestone, content] of milestoneGroups.entries()) {
      // Extract milestone title for error messages
      const milestoneTitle = milestone.children
        .filter((child) => child.type === 'text')
        .map((child: any) => child.value)
        .join('');

      // Find all H4 headings in this milestone's content
      const h4Headings = content
        .filter((node) => node.type === 'heading' && node.depth === 4)
        .map((heading: any) => {
          return heading.children
            .filter((child: any) => child.type === 'text')
            .map((child: any) => child.value)
            .join('')
            .trim();
        });

      // Check for each required subsection
      for (const requiredSubsection of shape.requiredSubsections) {
        const found = h4Headings.some(
          (h4Title) => h4Title.toLowerCase() === requiredSubsection.toLowerCase()
        );

        if (!found) {
          issues.push({
            notePath,
            type: 'error',
            code: 'missing-milestone-subsection',
            message: `Milestone "${milestoneTitle}" is missing required subsection "${requiredSubsection}"`,
            sectionId: rule.id,
            line: milestone.position?.start.line,
            column: milestone.position?.start.column,
          });
        }
      }
    }
  }

  return issues;
}
