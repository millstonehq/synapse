/**
 * Shared utilities for parsing and processing markdown documents
 */

import * as yaml from 'js-yaml';
import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkGfm from 'remark-gfm';
import remarkStringify from 'remark-stringify';
// @ts-ignore - no types available
import remarkHtml from 'remark-html';
import { visitParents } from 'unist-util-visit-parents';
import type { Root, Heading, Content, PhrasingContent, Image, Parent } from 'mdast';
import * as path from 'node:path';
import * as fs from 'node:fs/promises';

/**
 * Extracts raw frontmatter and body from markdown content
 * @param content - The markdown content to parse
 * @returns Object with raw frontmatter string, body, and line numbers
 */
export function extractFrontmatter(content: string): {
  frontmatter: string;
  body: string;
  startLine: number;
  endLine: number;
} {
  const lines = content.split('\n');
  let startLine = -1;
  let endLine = -1;
  
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim() === '---') {
      if (startLine === -1) {
        startLine = i;
      } else {
        endLine = i;
        break;
      }
    }
  }
  
  if (startLine === -1 || endLine === -1) {
    return {
      frontmatter: '',
      body: content,
      startLine: 0,
      endLine: 0
    };
  }
  
  const frontmatter = lines.slice(startLine + 1, endLine).join('\n');
  const body = lines.slice(endLine + 1).join('\n');
  
  return {
    frontmatter,
    body,
    startLine: startLine + 1,
    endLine
  };
}

/**
 * Parses markdown content into frontmatter data and body
 * @param content - The markdown content to parse
 * @returns Object with parsed frontmatter data and body
 */
export function parseDocument(content: string): {
  frontmatter: any;
  body: string;
  raw: {
    frontmatter: string;
    startLine: number;
    endLine: number;
  };
  error?: string;
} {
  const extracted = extractFrontmatter(content);
  
  let frontmatterData = {};
  let parseError: string | undefined;
  
  if (extracted.frontmatter) {
    try {
      frontmatterData = yaml.load(extracted.frontmatter) || {};
    } catch (error) {
      // Capture the error but still return empty frontmatter
      parseError = error instanceof Error ? error.message : String(error);
      console.warn('Failed to parse frontmatter YAML:', error);
    }
  }
  
  return {
    frontmatter: frontmatterData,
    body: extracted.body,
    raw: {
      frontmatter: extracted.frontmatter,
      startLine: extracted.startLine,
      endLine: extracted.endLine
    },
    error: parseError
  };
}

/**
 * Extracts wikilinks from markdown content
 * @param content - The markdown content to parse
 * @returns Array of wikilink targets (without the brackets)
 */
export function extractWikilinks(content: string): string[] {
  const wikilinks: string[] = [];
  
  // Match [[Link]] and [[Link|Display Text]] patterns
  const wikilinkRegex = /\[\[([^\]|]+)(?:\|[^\]]+)?\]\]/g;
  
  let match;
  while ((match = wikilinkRegex.exec(content)) !== null) {
    const linkTarget = match[1].trim();
    if (linkTarget && !wikilinks.includes(linkTarget)) {
      wikilinks.push(linkTarget);
    }
  }
  
  return wikilinks;
}

/**
 * Validates that a wikilink target exists in the vault
 * @param linkTarget - The target of the wikilink (without brackets)
 * @param existingFiles - Set of existing file paths in the vault
 * @returns true if the target exists, false otherwise
 */
export function validateWikilinkExists(
  linkTarget: string,
  existingFiles: Set<string>
): boolean {
  // Normalize the link target to handle various cases
  const normalizedTarget = linkTarget.toLowerCase().replace(/\s+/g, '-');
  
  // Check if any file matches the link target
  for (const file of existingFiles) {
    const normalizedFile = file.toLowerCase();
    const fileBasename = normalizedFile.split('/').pop() || '';
    const fileWithoutExt = fileBasename.replace(/\.md$/, '');
    
    // Check various matching patterns
    if (normalizedFile.endsWith(`/${normalizedTarget}.md`) || 
        normalizedFile.endsWith(`-${normalizedTarget}.md`) ||
        normalizedFile.endsWith(`/${normalizedTarget}`) ||
        normalizedFile.endsWith(`-${normalizedTarget}`) ||
        fileWithoutExt === normalizedTarget ||
        fileWithoutExt.endsWith(`-${normalizedTarget}`) ||
        normalizedFile === `${normalizedTarget}.md` ||
        normalizedFile === normalizedTarget) {
      return true;
    }
  }
  
  return false;
}

/**
 * Extracts all {{placeholder}} references from template text
 * Used primarily for template linting
 */
export function extractPlaceholders(text: string): Set<string> {
  const placeholders = new Set<string>();
  // Match {{variable}} or {{#helper variable}} or {{/helper}}
  const regex = /\{\{(?:#|\/)?([^}#/\s]+)(?:\s+([^}]+))?\}\}/g;
  let match;
  
  while ((match = regex.exec(text)) !== null) {
    const [fullMatch, helper, args] = match;
    
    // Skip closing tags
    if (fullMatch.startsWith('{{/')) {
      continue;
    }
    
    // For block helpers like {{#each}}, extract the variable being iterated
    if (fullMatch.startsWith('{{#')) {
      if (args) {
        // Extract the variable name from the arguments
        const varName = args.trim().split(/\s+/)[0];
        if (varName && !varName.includes('}')) {
          placeholders.add(varName);
        }
      }
    } else {
      // Regular placeholder - skip default helpers
      if (!isDefaultHelper(helper)) {
        placeholders.add(helper);
      }
    }
  }
  
  return placeholders;
}

/**
 * Parses frontmatter keys from raw frontmatter string
 * Used for template analysis without full YAML parsing
 */
export function parseFrontmatterKeys(frontmatter: string): Set<string> {
  const keys = new Set<string>();
  const lines = frontmatter.split('\n');
  
  for (const line of lines) {
    // Match 'key: value' pattern at the start of a line
    const match = line.match(/^(\w+):/);
    if (match) {
      keys.add(match[1]);
    }
  }
  
  return keys;
}

// Helper function for placeholder extraction
/**
 * Checks if a string value needs YAML quoting
 * Returns true if the string contains characters that could cause YAML parsing issues
 */
export function needsYamlQuoting(value: string): boolean {
  if (typeof value !== 'string') return false;
  
  // Check for problematic patterns
  const problematicPatterns = [
    /:/,        // Colons can be interpreted as key-value separator
    /\n/,       // Newlines need proper handling
    /^['"]/,    // Starting quotes
    /^[!&*]/,   // YAML special characters
    /^-\s/,     // Looks like a list item
    /^\s/,      // Leading whitespace
    /\s$/,      // Trailing whitespace
    /^(true|false|null|yes|no|on|off)$/i, // YAML keywords
    /^\d+$/,    // Pure numbers
  ];
  
  return problematicPatterns.some(pattern => pattern.test(value));
}

/**
 * Checks if a helper name is a default Handlebars helper
 */
function isDefaultHelper(name: string): boolean {
  const DEFAULT_HELPERS = ['now', 'each', 'unless', 'if', 'with'];
  return DEFAULT_HELPERS.includes(name);
}

// ============================================================================
// AST-based Markdown parsing (Phase 1)
// ============================================================================

/**
 * Represents a section node extracted from the AST
 */
export interface SectionNode {
  /** Section ID (normalized from title) */
  id: string;
  /** Original heading text */
  title: string;
  /** Heading depth (2 for H2, 3 for H3, etc.) */
  depth: number;
  /** Line number where the heading appears */
  line: number;
  /** Column number where the heading starts */
  column: number;
  /** AST nodes that are children of this section */
  content: Content[];
  /** Start position in the document */
  position?: {
    start: { line: number; column: number; offset?: number };
    end: { line: number; column: number; offset?: number };
  };
}

/**
 * Parses markdown body text into an AST
 * @param body - The markdown body content (without frontmatter)
 * @returns The parsed AST root node
 */
export function parseMarkdown(body: string): Root {
  const processor = unified().use(remarkParse).use(remarkGfm);
  const ast = processor.parse(body);
  return ast as Root;
}

/**
 * Extracts heading text from a heading node, stripping HTML anchors
 * @param heading - The heading node from the AST
 * @returns The clean heading text
 */
function extractHeadingText(heading: Heading): string {
  let text = '';

  for (const child of heading.children) {
    if (child.type === 'text') {
      text += child.value;
    } else if (child.type === 'html') {
      // Skip HTML anchor tags like <a id="summary"/>
      continue;
    } else if ('children' in child) {
      // Handle nested inline elements (emphasis, strong, etc.)
      text += extractInlineText(child.children as PhrasingContent[]);
    }
  }

  return text.trim();
}

/**
 * Extracts text from phrasing content (inline elements)
 */
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
 * Normalizes a section title to an ID
 * @param title - The section title
 * @returns The normalized section ID
 */
function normalizeSectionId(title: string): string {
  return title
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '') // Remove special characters
    .replace(/\s+/g, '-')     // Replace spaces with dashes
    .replace(/-+/g, '-')      // Replace multiple dashes with single dash
    .replace(/^-+|-+$/g, ''); // Remove leading/trailing dashes
}

/**
 * Finds all H2 sections in the AST and extracts their content
 * @param ast - The parsed markdown AST
 * @returns Array of section nodes with their content
 */
export function findSections(ast: Root): SectionNode[] {
  const sections: SectionNode[] = [];
  const children = ast.children;

  let currentSection: SectionNode | null = null;

  for (let i = 0; i < children.length; i++) {
    const node = children[i];

    // Check if this is an H2 heading
    if (node.type === 'heading' && node.depth === 2) {
      // Save the previous section if it exists
      if (currentSection) {
        sections.push(currentSection);
      }

      // Start a new section
      const title = extractHeadingText(node);
      const id = normalizeSectionId(title);

      currentSection = {
        id,
        title,
        depth: node.depth,
        line: node.position?.start.line || 0,
        column: node.position?.start.column || 0,
        content: [],
        position: node.position
      };
    } else if (currentSection) {
      // Add content to the current section
      currentSection.content.push(node);
    }
    // Ignore content before the first H2 section
  }

  // Add the last section
  if (currentSection) {
    sections.push(currentSection);
  }

  return sections;
}

/**
 * Stringifies an AST back to markdown
 * @param ast - The AST to stringify
 * @returns The markdown string
 */
export function stringifyMarkdown(ast: Root): string {
  const processor = unified().use(remarkStringify, {
    bullet: '-',
    emphasis: '_',
    fences: true,
    incrementListMarker: true,
  });
  return processor.stringify(ast);
}

// ============================================================================
// Include resolution and HTML conversion
// ============================================================================

/**
 * Remark plugin to resolve ![include](path.md) directives.
 * Replaces image nodes with alt="include" with the parsed contents
 * of the target file.
 */
function remarkIncludePlugin(options: { cwd: string }) {
  return async (tree: Root) => {
    type IncludeTarget = {
      node: Image;
      parent: Parent;
      index: number;
      ancestors: Parent[];
    };

    const targets: IncludeTarget[] = [];

    visitParents(tree, 'image', (node: Image, ancestors: Parent[]) => {
      const parent = ancestors[ancestors.length - 1] as Parent;
      const idx = (parent.children as Content[]).indexOf(node as unknown as Content);
      if (node.alt === 'include' && idx !== -1) {
        targets.push({ node, parent, index: idx, ancestors });
      }
    });

    for (const { node, parent, index, ancestors } of targets) {
      const absTarget = path.resolve(options.cwd, node.url);
      const basePath = path.resolve(options.cwd);
      const withinBase = absTarget === basePath || absTarget.startsWith(basePath + path.sep);

      if (!withinBase) {
        (parent.children as Content[])[index] = {
          type: 'html',
          value: `<!-- include blocked (outside base): ${node.url} -->`,
        } as any;
        continue;
      }

      let includedChildren: Content[] = [];
      try {
        const content = await fs.readFile(absTarget, 'utf-8');
        const includedAst = parseMarkdown(content);
        includedChildren = (includedAst.children as Content[]).filter(
          (n: any) => n.type !== 'yaml',
        );
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        (parent.children as Content[])[index] = {
          type: 'html',
          value: `<!-- include failed: ${node.url} (${msg}) -->`,
        } as any;
        continue;
      }

      if (parent.type === 'paragraph') {
        const grandparent = ancestors[ancestors.length - 2] as Parent | undefined;
        if (!grandparent) {
          (parent.children as Content[]).splice(index, 1, ...includedChildren);
          continue;
        }
        const parentIndex = (grandparent.children as Content[]).indexOf(parent as unknown as Content);
        const beforeInline = (parent.children as Content[]).slice(0, index);
        const afterInline = (parent.children as Content[]).slice(index + 1);
        const replacement: Content[] = [];

        if (beforeInline.length > 0) {
          replacement.push({ type: 'paragraph', children: beforeInline as any } as any);
        }
        if (includedChildren.length > 0) {
          replacement.push(...includedChildren);
        }
        if (afterInline.length > 0) {
          replacement.push({ type: 'paragraph', children: afterInline as any } as any);
        }
        (grandparent.children as Content[]).splice(parentIndex, 1, ...replacement);
      } else {
        (parent.children as Content[]).splice(index, 1, ...includedChildren);
      }
    }
  };
}

/**
 * Converts markdown to HTML with GFM support and ![include]() resolution.
 * @param body - The markdown body content (without frontmatter)
 * @param basePath - Base path for resolving includes (defaults to process.cwd())
 * @returns Promise resolving to the HTML string
 */
export async function markdownToHtml(body: string, basePath?: string): Promise<string> {
  const cwd = basePath || process.cwd();
  const processor = unified()
    .use(remarkParse)
    .use(remarkGfm)
    .use(remarkIncludePlugin, { cwd })
    .use(remarkHtml);

  const file = await processor.process(body);
  return String(file);
}

/**
 * Parses markdown body with ![include]() directives resolved.
 * @param body - The markdown body content (without frontmatter)
 * @param basePath - Base path for resolving includes (defaults to process.cwd())
 * @returns Promise resolving to the parsed AST with includes resolved
 */
export async function parseMarkdownWithIncludes(body: string, basePath?: string): Promise<Root> {
  const cwd = basePath || process.cwd();
  const ast = parseMarkdown(body);
  const transformer = remarkIncludePlugin({ cwd });
  await transformer(ast);
  return ast;
}