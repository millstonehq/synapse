import fsExtra from "fs-extra";
const fs = fsExtra;
import * as path from "path";
import glob from "fast-glob";
import { parseDocument, extractFrontmatter } from "../lib/markdown.js";
import { isKnownDocType } from "../lib/schemas.js";
import { loadBodyRules, formatBody } from "../lib/bodyRules.js";

export interface FormatOptions {
  contentDir?: string;
  write?: boolean;
  pattern?: string;
  verbose?: boolean;
}

export interface FormatResult {
  success: boolean;
  filesFormatted: number;
  filesModified: number;
  errors: string[];
}

/**
 * Formats a single document
 */
async function formatDocument(
  filePath: string,
  contentDir: string,
  bodyRules: any,
  writeChanges: boolean,
  verbose: boolean,
): Promise<{ modified: boolean; error?: string }> {
  try {
    const content = await fs.readFile(filePath, "utf-8");
    const { frontmatter, body } = parseDocument(content);

    // Get document type from frontmatter
    const type = frontmatter?.type;
    if (!type || !isKnownDocType(type)) {
      if (verbose) {
        console.log(`  ⏭️  Skipping ${path.relative(contentDir, filePath)} (no valid type)`);
      }
      return { modified: false };
    }

    // Format the body (support compound body grammar keys)
    const subType = frontmatter?.report_type as string | undefined;
    const effectiveType = subType && bodyRules.documentTypes[`${type}-${subType}`]
      ? `${type}-${subType}`
      : type;
    const formattedBody = formatBody(body, bodyRules, effectiveType);

    // Check if body changed
    const modified = formattedBody.trim() !== body.trim();

    if (modified) {
      if (writeChanges) {
        // Reconstruct the document with frontmatter
        const { frontmatter: frontmatterText } = extractFrontmatter(content);
        const newContent = frontmatterText
          ? `---\n${frontmatterText}\n---\n${formattedBody}`
          : formattedBody;

        await fs.writeFile(filePath, newContent, "utf-8");
        console.log(`  ✏️  Formatted ${path.relative(contentDir, filePath)}`);
      } else {
        console.log(`  ℹ️  Would format ${path.relative(contentDir, filePath)}`);
      }
    } else if (verbose) {
      console.log(`  ✓  ${path.relative(contentDir, filePath)} (no changes needed)`);
    }

    return { modified };
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    console.error(`  ❌ Error formatting ${path.relative(contentDir, filePath)}: ${errorMsg}`);
    return { modified: false, error: errorMsg };
  }
}

/**
 * Formats markdown documents according to body grammar rules
 */
export async function format(options: FormatOptions = {}): Promise<FormatResult> {
  const contentDir = options.contentDir || path.resolve(process.cwd(), "content");
  const write = options.write || false;
  const pattern = options.pattern || "**/*.md";
  const verbose = options.verbose || false;

  const result: FormatResult = {
    success: true,
    filesFormatted: 0,
    filesModified: 0,
    errors: [],
  };

  try {
    // Load body rules
    console.log(`📋 Loading body grammar rules...`);
    const bodyRules = await loadBodyRules();

    // Find all markdown files
    console.log(`🔍 Finding markdown files in ${contentDir}...`);
    const files = await glob(pattern, {
      cwd: contentDir,
      absolute: true,
      ignore: ["**/node_modules/**", "**/templates/**"],
    });

    console.log(`📄 Found ${files.length} markdown files`);
    console.log(write ? `✍️  Formatting files (--write mode)...\n` : `👀 Dry-run mode (use --write to save changes)...\n`);

    // Format each file
    for (const file of files) {
      const formatResult = await formatDocument(file, contentDir, bodyRules, write, verbose);
      result.filesFormatted++;

      if (formatResult.error) {
        result.errors.push(formatResult.error);
        result.success = false;
      } else if (formatResult.modified) {
        result.filesModified++;
      }
    }

    // Print summary
    console.log(`\n${"=".repeat(80)}`);
    console.log(`📊 Format Summary`);
    console.log(`${"=".repeat(80)}`);
    console.log(`Files processed: ${result.filesFormatted}`);
    console.log(`Files ${write ? "modified" : "would be modified"}: ${result.filesModified}`);
    if (result.errors.length > 0) {
      console.log(`Errors: ${result.errors.length}`);
    }

    if (!write && result.filesModified > 0) {
      console.log(`\n💡 Run with --write to apply changes`);
    }

  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    console.error(`\n❌ Fatal error: ${errorMsg}`);
    result.success = false;
    result.errors.push(errorMsg);
  }

  return result;
}

/**
 * CLI command handler for format
 */
export async function formatCommand(args: {
  dir?: string;
  write?: boolean;
  pattern?: string;
  verbose?: boolean;
}): Promise<void> {
  const result = await format({
    contentDir: args.dir,
    write: args.write,
    pattern: args.pattern,
    verbose: args.verbose,
  });

  if (!result.success) {
    process.exit(1);
  }
}
