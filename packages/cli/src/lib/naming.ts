import * as path from "path";
import { isKnownDocType } from "./schemas.js";
import { getExpectedFolder, getFolderName } from "./config.js";

/**
 * Extract a source prefix from an upstream URL for reference documents
 * @param upstreamUrl - The upstream URL from frontmatter
 * @returns A source prefix string (e.g., "claude-code", "dora", "mercury")
 */
function extractSourcePrefix(upstreamUrl: string): string {
  try {
    const url = new URL(upstreamUrl);
    const hostname = url.hostname.toLowerCase();
    
    // Domain-based mapping with heuristics
    // Prioritize specific known sources first
    const domainMappings: Record<string, string> = {
      'docs.claude.com': 'claude-code',
      'claude.ai': 'claude',
      'dora.dev': 'dora',
      'docs.mercury.com': 'mercury',
      'api.mercury.com': 'mercury',
      'huggingface.co': 'huggingface',
      'readme.io': 'readme',
    };
    
    // Check exact domain matches first
    if (domainMappings[hostname]) {
      return domainMappings[hostname];
    }
    
    // Handle docs.X.com pattern
    const docsMatch = hostname.match(/^docs\.([a-z0-9-]+)\.[a-z]+$/);
    if (docsMatch) {
      return docsMatch[1];
    }
    
    // Handle api.X.com pattern
    const apiMatch = hostname.match(/^api\.([a-z0-9-]+)\.[a-z]+$/);
    if (apiMatch) {
      return apiMatch[1];
    }
    
    // For other domains, use the primary domain name (without TLD)
    // e.g., "example.com" → "example", "my-site.org" → "my-site"
    const parts = hostname.split('.');
    if (parts.length >= 2) {
      // Get the second-to-last part (domain before TLD)
      const domainName = parts[parts.length - 2];
      // Skip generic domains that aren't meaningful as prefixes
      const genericDomains = ['github', 'stackoverflow', 'medium', 'dev', 'substack'];
      if (!genericDomains.includes(domainName)) {
        return domainName;
      }
      
      // For generic domains, try to extract from path
      const pathSegments = url.pathname.split('/').filter(s => s.length > 0);
      if (pathSegments.length > 0) {
        // Use first path segment as prefix for generic domains
        return toSlugCase(pathSegments[0]);
      }
    }
    
    // Fallback: use domain name without TLD
    return hostname.split('.')[0];
  } catch (error) {
    // If URL parsing fails, return empty string (will trigger validation error)
    return '';
  }
}

/**
 * Validation issue structure for consistent error reporting
 */
export interface ValidationIssue {
  notePath: string;
  type: "error" | "warning";
  code: string;
  message: string;
  field?: string;
}

/**
 * Get the expected folder path for a document type
 * Now delegates to config.ts which handles config-based overrides
 * @param type - The document type
 * @param cwd - Optional working directory for config lookup
 * @returns The expected folder path relative to content directory
 */
export function expectedFolder(type: string, cwd?: string): string {
  // Check if type is valid
  if (!isKnownDocType(type)) {
    throw new Error(`Unknown document type: ${type}`);
  }
  return getExpectedFolder(type, cwd);
}

/**
 * Validate that a file is in the correct folder for its type
 * @param notePath - The path to the note file
 * @param type - The document type
 * @returns Array of validation issues (errors for incorrect placement)
 */
export function validateFolderForType(
  notePath: string,
  type: string,
  cwd?: string,
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const normalizedPath = notePath.replace(/\\/g, "/");
  
  // Get folder configuration (respects config overrides)
  const expectedFolderPath = expectedFolder(type, cwd);
  const expectedFolderName = getFolderName(type, cwd);

  // Check if the file is in the expected folder
  // Accept either the full path (content/10_Policies) or just the folder name (10_Policies)
  if (
    !normalizedPath.includes(expectedFolderPath) &&
    !normalizedPath.includes(expectedFolderName)
  ) {
    issues.push({
      notePath,
      type: "error",
      code: "WRONG_FOLDER",
      message: `Document of type '${type}' must be placed in ${expectedFolderPath}`,
      field: "path",
    });
  }

  return issues;
}

/**
 * Convert a string to slug case
 * @param str - The string to convert
 * @returns The slug-case version
 */
function toSlugCase(str: string): string {
  return str
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, "") // Remove special characters
    .replace(/\s+/g, "-") // Replace spaces with dashes
    .replace(/-+/g, "-") // Replace multiple dashes with single dash
    .replace(/^-+|-+$/g, ""); // Remove leading/trailing dashes
}

/**
 * Validate the filename pattern for a document
 * @param notePath - The path to the note file
 * @param type - The document type
 * @param id - The document ID from frontmatter
 * @param title - The document title from frontmatter
 * @param strict - Whether to use strict mode (default: true - elevates warnings to errors)
 * @returns Array of validation issues
 */
export function validateFilenamePattern(
  notePath: string,
  type: string,
  id: string,
  title: string,
  strict: boolean = true, // Default to strict mode
  frontmatter?: Record<string, any>, // Optional frontmatter for reference type validation
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const filename = path.basename(notePath, ".md");

  if (type === "meeting") {
    // Meeting filenames must start with YYYY-MM-DD- date prefix
    const meetingDate = frontmatter?.meeting_date as string | undefined;

    if (!meetingDate) {
      issues.push({
        notePath,
        type: "error",
        code: "MISSING_MEETING_DATE",
        message: "Meeting documents require 'meeting_date' in frontmatter for filename validation",
        field: "meeting_date",
      });
      return issues;
    }

    // Extract date from meeting_date (handle ISO 8601 format)
    let datePrefix: string;
    try {
      const date = new Date(meetingDate);
      if (isNaN(date.getTime())) {
        throw new Error("Invalid date");
      }
      const year = date.getUTCFullYear();
      const month = String(date.getUTCMonth() + 1).padStart(2, '0');
      const day = String(date.getUTCDate()).padStart(2, '0');
      datePrefix = `${year}-${month}-${day}`;
    } catch (error) {
      issues.push({
        notePath,
        type: "error",
        code: "INVALID_MEETING_DATE",
        message: `Invalid meeting_date format '${meetingDate}'. Must be a valid ISO 8601 date string.`,
        field: "meeting_date",
      });
      return issues;
    }

    // Check if filename starts with date prefix
    const expectedPattern = `${datePrefix}-`;
    if (!filename.startsWith(expectedPattern)) {
      issues.push({
        notePath,
        type: "error",
        code: "MISSING_DATE_PREFIX",
        message: `Meeting filename must start with date prefix '${datePrefix}-' (from meeting_date '${meetingDate}'). Expected pattern: 'YYYY-MM-DD-company-topic.md'`,
        field: "filename",
      });
      return issues;
    }

    // Validate the rest of the filename is slug-case
    const slugPart = filename.substring(datePrefix.length + 1); // +1 for the hyphen
    const isSlugCase = /^[a-z0-9-]+$/.test(slugPart);

    if (!isSlugCase) {
      issues.push({
        notePath,
        type: "error",
        code: "INVALID_FILENAME_FORMAT",
        message: `Meeting filename after date prefix must be in slug-case (lowercase, hyphens only), got '${slugPart}'`,
        field: "filename",
      });
    }
  } else if (type === "adr") {
    // ADR has strict requirements
    // 1. ID must match pattern ADR-####
    const adrIdPattern = /^ADR-\d{4,}$/;
    if (!adrIdPattern.test(id)) {
      issues.push({
        notePath,
        type: "error",
        code: "INVALID_ADR_ID",
        message: `ADR id must match pattern ADR-#### (e.g., ADR-0001), got '${id}'`,
        field: "id",
      });
    }

    // 2. Filename must be ADR-####-slug.md
    const adrFilenamePattern = /^ADR-\d{4,}-[a-z0-9-]+$/;
    if (!adrFilenamePattern.test(filename)) {
      issues.push({
        notePath,
        type: "error",
        code: "INVALID_ADR_FILENAME",
        message: `ADR filename must match pattern ADR-####-slug.md (e.g., ADR-0001-api-design.md), got '${filename}.md'`,
        field: "filename",
      });
    } else {
      // Check that the ADR number in filename matches the ID
      const filenameAdrNumber = filename.match(/^ADR-(\d{4,})/)?.[1];
      const idAdrNumber = id.match(/^ADR-(\d{4,})/)?.[1];

      if (
        filenameAdrNumber &&
        idAdrNumber &&
        filenameAdrNumber !== idAdrNumber
      ) {
        issues.push({
          notePath,
          type: "error",
          code: "ADR_ID_MISMATCH",
          message: `ADR number in filename (${filenameAdrNumber}) does not match id (${idAdrNumber})`,
          field: "filename",
        });
      }
    }
  } else if (type === "reference") {
    // Reference type: enforce source prefix from upstream_url
    const isSlugCase = /^[a-z0-9-]+$/.test(filename);
    
    if (!isSlugCase) {
      issues.push({
        notePath,
        type: "error",
        code: "INVALID_FILENAME_FORMAT",
        message: `Filename must be in slug-case (lowercase, hyphens only), got '${filename}'`,
        field: "filename",
      });
      return issues; // Can't continue with invalid format
    }
    
    // Check for upstream_url in frontmatter
    const upstreamUrl = frontmatter?.upstream_url as string | undefined;
    const manualPrefix = frontmatter?.source_prefix as string | undefined;
    
    if (!upstreamUrl) {
      issues.push({
        notePath,
        type: "error",
        code: "MISSING_UPSTREAM_URL",
        message: "Reference documents require 'upstream_url' in frontmatter for source prefix validation",
        field: "upstream_url",
      });
      return issues; // Can't validate prefix without upstream_url
    }
    
    // Extract or use manual source prefix
    const sourcePrefix = manualPrefix || extractSourcePrefix(upstreamUrl);
    
    if (!sourcePrefix) {
      issues.push({
        notePath,
        type: "error",
        code: "CANNOT_EXTRACT_SOURCE_PREFIX",
        message: `Cannot extract source prefix from upstream_url '${upstreamUrl}'. Add 'source_prefix' field to frontmatter to manually specify the prefix.`,
        field: "upstream_url",
      });
      return issues;
    }
    
    // Validate filename starts with source prefix
    const expectedPattern = `${sourcePrefix}-`;
    if (!filename.startsWith(expectedPattern)) {
      issues.push({
        notePath,
        type: "error",
        code: "MISSING_SOURCE_PREFIX",
        message: `Reference filename must start with source prefix '${sourcePrefix}-' (derived from upstream_url '${upstreamUrl}'). Expected pattern: '${sourcePrefix}-{slug}.md'`,
        field: "filename",
      });
      return issues;
    }
    
    // Extract the slug part (after prefix)
    const slugPart = filename.substring(sourcePrefix.length + 1); // +1 for the hyphen
    
    // Generate expected slug from title, removing the source prefix if it appears in the title
    // e.g., "Claude Code Plugins" -> "plugins" (not "claude-code-plugins")
    // e.g., "DORA 2025 Analysis" -> "2025-analysis" (not "dora-2025-analysis")
    let titleForSlug = title;
    const titleSlug = toSlugCase(title);
    
    // If the title slug starts with the source prefix, remove it
    if (titleSlug.startsWith(sourcePrefix + '-')) {
      titleForSlug = titleSlug.substring(sourcePrefix.length + 1);
    } else {
      titleForSlug = titleSlug;
    }
    
    // Validate the slug part matches the cleaned title slug
    if (slugPart !== titleForSlug) {
      const severity = strict ? "error" : "warning";
      issues.push({
        notePath,
        type: severity,
        code: "FILENAME_TITLE_MISMATCH",
        message: `Filename slug '${slugPart}' does not match expected slug from title '${title}' (expected: '${sourcePrefix}-${titleForSlug}.md')`,
        field: "filename",
      });
    }
  } else if (type === "wiki" && filename === "index") {
    // Wiki index.md files are used for directory-based routing; skip title-slug check
  } else {
    // Other document types: slug-case filename validation
    const expectedSlug = toSlugCase(title);
    const isSlugCase = /^[a-z0-9-]+$/.test(filename);

    if (!isSlugCase) {
      issues.push({
        notePath,
        type: "error",
        code: "INVALID_FILENAME_FORMAT",
        message: `Filename must be in slug-case (lowercase, hyphens only), got '${filename}'`,
        field: "filename",
      });
    } else if (filename !== expectedSlug) {
      // Check if filename matches the title slug
      const severity = strict ? "error" : "warning";
      issues.push({
        notePath,
        type: severity,
        code: "FILENAME_TITLE_MISMATCH",
        message: `Filename '${filename}' does not match expected slug from title '${title}' (expected: '${expectedSlug}')`,
        field: "filename",
      });
    }
  }

  return issues;
}

/**
 * Comprehensive validation of naming and placement rules
 * @param notePath - The path to the note file
 * @param frontmatter - The parsed frontmatter data
 * @param strict - Whether to use strict mode (default: true)
 * @param cwd - Optional working directory for config lookup
 * @returns Array of validation issues
 */
export function validateNaming(
  notePath: string,
  frontmatter: Record<string, any>,
  strict: boolean = true,
  cwd?: string,
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];

  // Skip naming validation for example files
  if (
    notePath.includes("00_Guides/Examples/") ||
    frontmatter.example === true
  ) {
    return issues;
  }

  // Extract required fields
  const type = frontmatter.type as string;
  const id = frontmatter.id as string;
  const title = frontmatter.title as string;

  // Validate type is present and valid
  if (!type) {
    issues.push({
      notePath,
      type: "error",
      code: "MISSING_TYPE",
      message: "Document type is missing from frontmatter",
      field: "type",
    });
    return issues; // Can't continue without type
  }

  if (!isKnownDocType(type)) {
    issues.push({
      notePath,
      type: "error",
      code: "INVALID_TYPE",
      message: `Invalid document type: '${type}'`,
      field: "type",
    });
    return issues; // Can't continue with invalid type
  }

  // Validate required fields for naming checks
  if (!id) {
    issues.push({
      notePath,
      type: "error",
      code: "MISSING_ID",
      message: "Document id is missing from frontmatter",
      field: "id",
    });
  }

  if (!title) {
    issues.push({
      notePath,
      type: "error",
      code: "MISSING_TITLE",
      message: "Document title is missing from frontmatter",
      field: "title",
    });
  }

  // If we have all required fields, perform naming validation
  if (type && id && title) {
    // Validate folder placement
    issues.push(...validateFolderForType(notePath, type, cwd));

    // Validate filename pattern (pass frontmatter for reference type)
    issues.push(...validateFilenamePattern(notePath, type, id, title, strict, frontmatter));
  }

  return issues;
}
