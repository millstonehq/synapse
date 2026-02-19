#!/usr/bin/env node

import { validateCommand } from "./commands/validate.js";
import { formatCommand } from "./commands/format.js";
import { indexCommand } from "./commands/index.js";
import { scaffoldCommand } from "./commands/scaffold.js";
import { generatePdfCommand } from "./commands/generate-pdf.js";
import { initCommand } from "./commands/init.js";
import { fetchReferenceCommand } from "./commands/fetch-reference.js";
import { generateCommand } from "./commands/generate.js";
import { getDocTypes } from "./lib/type-registry.js";

// Parse command line arguments
const [, , command, ...args] = process.argv;

// Simple argument parser
function parseArgs(args: string[]): Record<string, any> {
  const parsed: Record<string, any> = {};
  let i = 0;

  // Helper to convert kebab-case to camelCase
  const toCamelCase = (str: string): string => {
    return str.replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
  };

  while (i < args.length) {
    const arg = args[i];

    if (arg.startsWith("--")) {
      const key = arg.slice(2);

      // Handle --no-* flags
      if (key.startsWith("no-")) {
        const actualKey = toCamelCase(key.slice(3));
        parsed[actualKey] = false;
        i++;
      } else {
        const nextArg = args[i + 1];
        const camelKey = toCamelCase(key);

        // Check if this is a boolean flag or has a value
        if (!nextArg || nextArg.startsWith("--")) {
          parsed[camelKey] = true;
          i++;
        } else {
          parsed[camelKey] = nextArg;
          i += 2;
        }
      }
    } else if (arg.startsWith("-")) {
      // Short flags
      const key = arg.slice(1);
      parsed[key] = true;
      i++;
    } else {
      // Positional arguments
      if (!parsed._) {
        parsed._ = [];
      }
      parsed._.push(arg);
      i++;
    }
  }

  return parsed;
}

// Show help message
function showHelp(): void {
  const availableTypes = getDocTypes().join(", ");

  console.log(`
Synapse Documentation Framework CLI

Usage:
  synapse <command> [options]

Commands:
  init            Bootstrap a new Synapse project (schemas, content dirs, config)
  validate        Validate documentation files against schemas
  format          Format documentation files according to body grammar rules
  index           Generate the homepage index.md with navigation
  scaffold        Create a new document from a template
  generate        Generate synthetic example documents from titles.json
  generate-pdf    Generate a PDF from YAML data and template
  fetch-reference Fetch and convert external URL to markdown

Options:
  --help      Show this help message

Init Command:
  synapse init [options]

  Bootstrap a new project by copying schemas from @millstone/synapse-schemas,
  creating content directories, and generating synapse.config.json.

  Options:
    --site-name <name>        Site name (default: directory name)
    --base-url <url>          Base URL for Quartz site
    --force                   Re-bootstrap even if schemas exist
    --yes                     Skip interactive prompts

Validate Command:
  synapse validate [options]

  Options:
    --dir <path>        Content directory to validate (default: content/)
    --schema <path>     Schema directory (default: content/schemas/)
    --pattern <glob>    Glob pattern to match files (default: **/*.md)
    --format <format>   Output format: pretty, json, compact (default: pretty)
    --strict            Enable strict mode for naming validation (default: true)
    --no-strict         Disable strict mode for naming validation

Format Command:
  synapse format [options]

  Options:
    --dir <path>        Content directory to format (default: content/)
    --write             Write changes to files (default: dry-run)
    --pattern <glob>    Glob pattern to match files (default: **/*.md)
    --verbose           Show all files, including unchanged

Index Command:
  synapse index [options]

  Options:
    --dir <path>        Content directory (default: content/)
    --output <path>     Output file path (default: content/index.md)

Scaffold Command:
  synapse scaffold [options]

  Options:
    --type <type>       Document type (required: ${availableTypes})
    --template <type>   Alias for --type (backward compatible)
    --title <title>     Document title (required)
    --owner <owner>     Document owner (optional)
    --id <id>           Custom document ID (default: auto-generated)
    --target-dir <path> Output directory (default: content/{type folder})
    --force             Overwrite existing files

Generate Command:
  synapse generate <titles.json> [options]

  Generate synthetic example documents from a titles manifest.
  Titles.json is an array of { type, title, domain } objects.

  Options:
    --dir <path>        Content root directory (default: cwd)
    --force             Overwrite existing files

Generate PDF Command:
  synapse generate-pdf [options]

  Options:
    --input <path>      Input markdown file (required)
    --output <path>     Output PDF file path (required)
    --theme <name>      Theme name (overrides frontmatter brand_theme)
    --logo <path>       Logo image path (overrides theme logo)
    --company <name>    Company name (overrides frontmatter)
    --draft             Force draft watermark
    --no-validate       Skip schema validation

Fetch Reference Command:
  synapse fetch-reference <url>

  Fetch external documentation and convert to markdown using Mozilla
  Readability + Turndown. Outputs JSON with markdown content, title,
  byline, and excerpt.

Examples:
  synapse init
  synapse init --site-name "Acme Docs" --base-url "docs.acme.com" --yes
  synapse validate
  synapse validate --no-strict
  synapse validate --pattern "**/ADRs/*.md" --format compact
  synapse format --write
  synapse index
  synapse scaffold --type adr --title "Use React for Frontend"
  synapse scaffold --type policy --title "Security Policy" --owner "Security Team"
  synapse generate titles.json --force
  synapse generate-pdf --input data.yaml --output document.pdf
`);
}

// Main CLI handler
async function main(): Promise<void> {
  if (
    !command ||
    command === "--help" ||
    command === "-h" ||
    command === "help"
  ) {
    showHelp();
    process.exit(0);
  }

  const parsedArgs = parseArgs(args);

  try {
    switch (command) {
      case "init":
        await initCommand(parsedArgs);
        break;

      case "validate":
        await validateCommand(parsedArgs);
        break;

      case "format":
        await formatCommand(parsedArgs);
        break;

      case "index":
        await indexCommand(parsedArgs);
        break;

      case "scaffold":
        await scaffoldCommand(parsedArgs);
        break;

      case "generate":
        await generateCommand(parsedArgs);
        break;

      case "generate-pdf":
        await generatePdfCommand(parsedArgs);
        break;

      case "fetch-reference":
        // First positional arg is the URL
        await fetchReferenceCommand({
          url: parsedArgs._?.[0],
          ...parsedArgs,
        });
        break;

      default:
        console.error(`Unknown command: ${command}`);
        console.log('Run "synapse --help" for usage information');
        process.exit(1);
    }
  } catch (error) {
    console.error("Error:", error);
    process.exit(1);
  }
}

// Run the CLI
main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
