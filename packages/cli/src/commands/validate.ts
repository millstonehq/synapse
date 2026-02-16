import fsExtra from "fs-extra";
const fs = fsExtra;
import * as path from "path";
import glob from "fast-glob";
import { loadSchema, validateFrontmatter, isKnownDocType } from "../lib/schemas.js";
import { validateNaming } from "../lib/naming.js";
import {
  parseDocument,
  extractWikilinks,
  validateWikilinkExists,
} from "../lib/markdown.js";

import { loadBodyRules, validateBody } from "../lib/bodyRules.js";
import { validatePluginMarketplace } from "../lib/validate-plugins.js";

export interface ValidationIssue {
  type: "error" | "warning";
  code: string;
  message: string;
  file?: string;
  line?: number;
  column?: number;
  field?: string;
  sectionId?: string;
}

export interface ValidationResult {
  success: boolean;
  issues: ValidationIssue[];
  filesValidated: number;
}

/**
 * Validates that content directories don't have duplicate numeric prefixes
 */
async function validateDirectoryPrefixes(
  contentDir: string,
): Promise<ValidationIssue[]> {
  const issues: ValidationIssue[] = [];

  try {
    const entries = await fs.readdir(contentDir, { withFileTypes: true });
    const directories = entries.filter((e) => e.isDirectory());

    // Extract numeric prefixes from directory names
    const prefixMap = new Map<string, string[]>();

    for (const dir of directories) {
      const match = dir.name.match(/^(\d+)_/);
      if (match) {
        const prefix = match[1];
        if (!prefixMap.has(prefix)) {
          prefixMap.set(prefix, []);
        }
        prefixMap.get(prefix)!.push(dir.name);
      }
    }

    // Check for duplicates
    for (const [prefix, dirs] of prefixMap.entries()) {
      if (dirs.length > 1) {
        issues.push({
          type: "error",
          code: "DUPLICATE_PREFIX",
          message: `Multiple directories with prefix ${prefix}_: ${dirs.join(", ")}. Each directory must have a unique numeric prefix.`,
        });
      }
    }
  } catch (error) {
    // Ignore errors reading directory
  }

  return issues;
}

/**
 * Validates cross-link rules for different document types
 */
function validateCrossLinks(
  frontmatter: any,
  body: string,
  filePath: string,
  existingFiles: Set<string>,
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const docType = frontmatter.type as string;

  if (!docType || !isKnownDocType(docType)) {
    return issues;
  }

  // Extract wikilinks from body
  const wikilinks = extractWikilinks(body);

  // Validate that all wikilinks point to existing documents
  for (const link of wikilinks) {
    if (!validateWikilinkExists(link, existingFiles)) {
      issues.push({
        type: "error",
        code: "BROKEN_LINK",
        message: `Referenced document does not exist: [[${link}]]`,
        file: filePath,
      });
    }
  }

  // Validate cross-link rules based on document type
  switch (docType) {
    case "process":
      // Process documents must reference at least one standard
      if (
        !frontmatter.related_standards ||
        !Array.isArray(frontmatter.related_standards) ||
        frontmatter.related_standards.length === 0
      ) {
        issues.push({
          type: "error",
          code: "MISSING_REQUIRED_LINK",
          message: "Process documents must reference at least one standard",
          file: filePath,
          field: "related_standards",
        });
      } else {
        // Validate that referenced standards exist
        for (const standard of frontmatter.related_standards) {
          const standardLink = extractWikilinks(standard)[0];
          if (
            standardLink &&
            !validateWikilinkExists(standardLink, existingFiles)
          ) {
            issues.push({
              type: "error",
              code: "BROKEN_LINK",
              message: `Referenced standard does not exist: ${standard}`,
              file: filePath,
              field: "related_standards",
            });
          }
        }
      }
      break;

    case "sop":
      // SOP must reference a parent process
      if (
        !frontmatter.related_process ||
        typeof frontmatter.related_process !== "string" ||
        frontmatter.related_process.trim() === ""
      ) {
        issues.push({
          type: "error",
          code: "MISSING_REQUIRED_LINK",
          message: "SOP must reference a parent process",
          file: filePath,
          field: "related_process",
        });
      } else {
        // Validate that referenced process exists
        const processLink = extractWikilinks(frontmatter.related_process)[0];
        if (
          processLink &&
          !validateWikilinkExists(processLink, existingFiles)
        ) {
          issues.push({
            type: "error",
            code: "BROKEN_LINK",
            message: `Referenced process does not exist: ${frontmatter.related_process}`,
            file: filePath,
            field: "related_process",
          });
        }
      }
      break;

    case "runbook":
      // Runbook must reference a system/service (in body under ## Service section)
      const serviceMatch = body.match(/##\s+Service\s*\n+([^\n#]+)/);
      const serviceContent = serviceMatch ? serviceMatch[1].trim() : "";
      const serviceLinks = extractWikilinks(serviceContent);

      if (!serviceContent || serviceLinks.length === 0) {
        issues.push({
          type: "error",
          code: "MISSING_REQUIRED_LINK",
          message: "Runbook must reference a system/service",
          file: filePath,
          field: "service",
        });
      } else {
        // Validate that referenced service exists
        for (const serviceLink of serviceLinks) {
          if (!validateWikilinkExists(serviceLink, existingFiles)) {
            issues.push({
              type: "error",
              code: "BROKEN_LINK",
              message: `Referenced service does not exist: [[${serviceLink}]]`,
              file: filePath,
              field: "service",
            });
          }
        }
      }
      break;
  }

  return issues;
}

/**
 * Validates a single document
 */
async function validateDocument(
  filePath: string,
  contentDir: string,
  schemaDir: string,
  existingFiles: Set<string>,
  bodyRules: any, // BodyRules type from bodyRules.ts
  strict: boolean = true,
): Promise<ValidationIssue[]> {
  const issues: ValidationIssue[] = [];

  try {
    // Read file content
    const content = await fs.readFile(filePath, "utf-8");
    const parsed = parseDocument(content);

    // Check for YAML parse errors
    if (parsed.error) {
      issues.push({
        type: "error",
        code: "YAML_PARSE_ERROR",
        message: `Invalid YAML in frontmatter: ${parsed.error}`,
        file: filePath,
      });
      return issues; // Can't continue validation without valid frontmatter
    }

    const { frontmatter, body } = parsed;

    // Get document type (supports both base types and custom types with local schemas)
    const docType = frontmatter.type;
    if (!docType || !isKnownDocType(docType)) {
      issues.push({
        type: "error",
        code: "INVALID_DOC_TYPE",
        message: `Invalid or missing document type: ${docType}`,
        file: filePath,
        field: "type",
      });
      return issues;
    }

    // Load and validate against schema
    const schema = await loadSchema(docType, schemaDir);
    const schemaValidation = validateFrontmatter(frontmatter, schema);

    if (!schemaValidation.valid && schemaValidation.errors) {
      for (const error of schemaValidation.errors) {
        issues.push({
          type: "error",
          code: "SCHEMA_VALIDATION_ERROR",
          message: `Schema validation: ${error.path} ${error.message}`,
          file: filePath,
          field: error.path || undefined,
        });
      }
    }

    // Validate body structure (AST-based validation)
    if (bodyRules) {
      const relativePath = path.relative(contentDir, filePath);
      const bodyIssues = validateBody(body, bodyRules, docType, relativePath);

      // Map body validation issues to include file path
      issues.push(
        ...bodyIssues.map((issue) => ({
          ...issue,
          file: filePath,
        }))
      );
    }

    // Validate naming conventions
    const relativePath = path.relative(contentDir, filePath);
    const projectRoot = path.resolve(contentDir, '..');
    const namingIssues = validateNaming(relativePath, frontmatter, strict, projectRoot);
    issues.push(
      ...namingIssues.map((issue) => ({
        ...issue,
        file: filePath,
      })),
    );

    // Validate cross-links
    const crossLinkIssues = validateCrossLinks(
      frontmatter,
      body,
      filePath,
      existingFiles,
    );
    issues.push(...crossLinkIssues);
  } catch (error) {
    issues.push({
      type: "error",
      code: "VALIDATION_FAILED",
      message: `Failed to validate file: ${error}`,
      file: filePath,
    });
  }

  return issues;
}

/**
 * Main validation function
 */
export async function validate(options: {
  contentDir?: string;
  schemaDir?: string;
  pattern?: string;
  strict?: boolean;
}): Promise<ValidationResult> {
  // Better directory resolution that works from any location
  let contentDir = options.contentDir;
  if (!contentDir) {
    // Try to find content directory relative to cwd
    const cwdContent = path.resolve(process.cwd(), "content");
    const parentContent = path.resolve(process.cwd(), "../content");
    const grandparentContent = path.resolve(process.cwd(), "../../content");

    if (await fs.pathExists(cwdContent)) {
      contentDir = cwdContent;
    } else if (await fs.pathExists(parentContent)) {
      contentDir = parentContent;
    } else if (await fs.pathExists(grandparentContent)) {
      contentDir = grandparentContent;
    } else {
      // Default fallback
      contentDir = cwdContent;
    }
  } else {
    // Resolve the provided path
    contentDir = path.resolve(process.cwd(), contentDir);
  }

  // Schema dir should be at project root, not inside content
  const projectRoot = path.resolve(contentDir, '..');
  const schemaDir = options.schemaDir || path.resolve(projectRoot, "schemas/frontmatter");
  const pattern = options.pattern || "**/*.md";
  const strict = options.strict !== undefined ? options.strict : true; // Default to strict mode

  const allIssues: ValidationIssue[] = [];
  let filesValidated = 0;

  try {
    // Load body validation rules
    let bodyRules = null;
    try {
      bodyRules = await loadBodyRules();
    } catch (error) {
      // Body rules are optional - if they don't exist, skip body validation
      console.warn('Warning: Body rules not found, skipping body validation');
    }

    // Validate directory structure first
    const directoryIssues = await validateDirectoryPrefixes(contentDir);
    allIssues.push(...directoryIssues);

    // Get all markdown files to validate
    const files = await glob(pattern, {
      cwd: contentDir,
      absolute: true,
      ignore: [
        "**/node_modules/**",
        "**/.git/**",
        "**/templates/**",
        "index.md",
      ],
    });

    // Build set of ALL existing files in the vault for cross-reference validation
    // This needs to include files from the entire content root, not just the validation directory
    const existingFiles = new Set<string>();

    // Find the root content directory (go up from contentDir until we find the base)
    let rootContentDir = contentDir;
    const pathParts = contentDir.split(path.sep);
    for (let i = pathParts.length - 1; i >= 0; i--) {
      if (pathParts[i] === "content") {
        rootContentDir = pathParts.slice(0, i + 1).join(path.sep);
        break;
      }
    }

    // Get ALL markdown files from the root for link validation
    const allVaultFiles = await glob("**/*.md", {
      cwd: rootContentDir,
      absolute: true,
      ignore: [
        "**/node_modules/**",
        "**/.git/**",
        "**/templates/**",
        "index.md",
      ],
    });

    // Add all vault files to the set for cross-reference checking
    for (const file of allVaultFiles) {
      const relativePath = path.relative(rootContentDir, file);
      existingFiles.add(relativePath);
      existingFiles.add(path.basename(file));
      existingFiles.add(path.basename(file, ".md"));
    }

    // Validate each file
    for (const file of files) {
      const issues = await validateDocument(
        file,
        rootContentDir, // Use root content dir for proper relative paths
        schemaDir,
        existingFiles,
        bodyRules,
        strict,
      );
      allIssues.push(...issues);
      filesValidated++;
    }

    // Check for duplicate titles across all documents
    const titleMap = new Map<string, string[]>();

    for (const file of files) {
      try {
        const content = await fs.readFile(file, "utf-8");
        const { frontmatter } = parseDocument(content);

        if (frontmatter.title && frontmatter.type) {
          // Create a normalized key for comparison
          const normalizedTitle = frontmatter.title
            .toLowerCase()
            .replace(/[^\w\s-]/g, "")
            .replace(/\s+/g, "-")
            .replace(/-+/g, "-")
            .trim();

          // Group by type and normalized title
          // For wiki documents, include parent directory to avoid false positives
          // across different wiki subdirectories (e.g., project-overview.md in each repo)
          const relPath = path.relative(contentDir, file);
          const parentDir = frontmatter.type === 'wiki' ? path.dirname(relPath) : '';
          const key = parentDir
            ? `${frontmatter.type}:${parentDir}:${normalizedTitle}`
            : `${frontmatter.type}:${normalizedTitle}`;
          if (!titleMap.has(key)) {
            titleMap.set(key, []);
          }
          titleMap.get(key)!.push(path.relative(contentDir, file));
        }
      } catch (error) {
        // Skip files that can't be parsed for duplicate detection
      }
    }

    // Report duplicates (excluding examples as they're expected to have similar titles)
    for (const [key, paths] of titleMap.entries()) {
      const nonExamplePaths = paths.filter(
        (p) => !p.includes("00_Guides/Examples/"),
      );
      if (nonExamplePaths.length > 1) {
        const [type, title] = key.split(":", 2);
        allIssues.push({
          type: "warning",
          code: "DUPLICATE_TITLE",
          message: `Multiple ${type} documents with similar title may cause confusion: ${nonExamplePaths.join(", ")}`,
          file: "", // No specific file, it's a cross-file issue
        });
      }
    }

    // Validate plugins if marketplace manifest exists
    const marketplacePath = path.join(projectRoot, '.claude-plugin/marketplace.json');
    if (await fs.pathExists(marketplacePath)) {
      try {
        const pluginSchemaDir = path.join(projectRoot, 'schemas/plugins');
        const pluginResult = await validatePluginMarketplace(projectRoot, pluginSchemaDir);
        
        // Merge plugin issues into main validation
        allIssues.push(...pluginResult.issues);
      } catch (error) {
        allIssues.push({
          type: "error",
          code: "PLUGIN_VALIDATION_FAILED",
          message: `Plugin validation failed: ${error}`,
        });
      }
    }

    return {
      success: allIssues.filter((i) => i.type === "error").length === 0,
      issues: allIssues,
      filesValidated,
    };
  } catch (error) {
    return {
      success: false,
      issues: [
        {
          type: "error",
          code: "VALIDATION_FAILED",
          message: `Validation failed: ${error}`,
        },
      ],
      filesValidated,
    };
  }
}

/**
 * CLI handler for validate command
 */
export async function validateCommand(args: {
  dir?: string;
  schema?: string;
  pattern?: string;
  strict?: boolean;
  quiet?: boolean;
  format?: string;
  examples?: boolean; // False when --no-examples is used
}): Promise<void> {
  // Handle special case where dir is '.' - treat as current directory
  let contentDir = args.dir;
  if (contentDir === ".") {
    contentDir = process.cwd();
  }

  // Determine project root for plugin validation
  let projectRoot = process.cwd();
  if (contentDir) {
    projectRoot = path.resolve(contentDir, '..');
  }

  const result = await validate({
    contentDir: contentDir,
    schemaDir: args.schema, // Updated to use args.schema
    pattern: args.pattern,
    strict: args.strict, // Will default to true if not specified
  });

  // Get plugin validation results if marketplace exists
  let pluginResult: any = null;
  const marketplacePath = path.join(projectRoot, '.claude-plugin/marketplace.json');
  if (await fs.pathExists(marketplacePath)) {
    try {
      const pluginSchemaDir = path.join(projectRoot, 'schemas/plugins');
      pluginResult = await validatePluginMarketplace(projectRoot, pluginSchemaDir);
    } catch (error) {
      // Error already captured in main validation
    }
  }

  const errors = result.issues.filter((i) => i.type === "error");
  const warnings = result.issues.filter((i) => i.type === "warning");

  // Handle different output formats
  if (args.format === "json") {
    // Count files with errors (not total errors)
    const filesWithErrors = new Set(errors.map((e) => e.file).filter((f) => f))
      .size;
    const validFiles = result.filesValidated - filesWithErrors;

    // Output JSON format
    const jsonOutput = {
      errors: errors,
      warnings: warnings,
      summary: {
        total: result.filesValidated,
        valid: validFiles,
        errors: errors.length,
        warnings: warnings.length,
      },
    };
    console.log(JSON.stringify(jsonOutput, null, 2));
  } else if (args.format === "compact") {
    // Compact format - one line per issue
    for (const error of errors) {
      console.log(`[E] ${error.file || "global"}: ${error.message}`);
    }
    for (const warning of warnings) {
      console.log(`[W] ${warning.file || "global"}: ${warning.message}`);
    }
  } else if (!args.quiet) {
    // Default pretty format
    console.log(`\nValidated ${result.filesValidated} files\n`);

    // Show plugin validation summary if plugins were validated
    if (pluginResult) {
      console.log('Plugin validation:');
      console.log(`  Plugins validated: ${pluginResult.pluginsValidated}`);
      const { componentsValidated } = pluginResult;
      if (componentsValidated.commands > 0) {
        console.log(`  Commands: ${componentsValidated.commands}`);
      }
      if (componentsValidated.agents > 0) {
        console.log(`  Agents: ${componentsValidated.agents}`);
      }
      if (componentsValidated.skills > 0) {
        console.log(`  Skills: ${componentsValidated.skills}`);
      }
      if (componentsValidated.hooks > 0) {
        console.log(`  Hooks: ${componentsValidated.hooks}`);
      }
      if (componentsValidated.mcpServers > 0) {
        console.log(`  MCP servers: ${componentsValidated.mcpServers}`);
      }
      console.log();
    }

    if (errors.length > 0) {
      console.log(`❌ ${errors.length} errors:`);
      for (const error of errors) {
        console.log(
          `  - ${error.file ? path.basename(error.file) + ": " : ""}${error.message}`,
        );
      }
      console.log();
    }

    if (warnings.length > 0) {
      console.log(`⚠️  ${warnings.length} warnings:`);
      for (const warning of warnings) {
        console.log(
          `  - ${warning.file ? path.basename(warning.file) + ": " : ""}${warning.message}`,
        );
      }
      console.log();
    }

    if (result.success) {
      console.log("✅ All validations passed!");
    } else {
      console.log("❌ Validation failed");
    }
  }

  // Exit with error code if validation failed
  if (!result.success) {
    process.exit(1);
  }
}
