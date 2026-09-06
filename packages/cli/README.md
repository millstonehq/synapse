# @millstone/synapse-cli

CLI for the Synapse documentation framework. Provides validation, formatting, scaffolding, and PDF generation for structured documentation.

## Installation

```bash
npm install @millstone/synapse-cli
```

Or use directly with npx:

```bash
npx @millstone/synapse-cli validate
```

## Commands

### validate

Validate documentation files against JSON schemas and body grammar rules.

```bash
synapse validate [options]

Options:
  --dir <path>        Content directory to validate (default: content/)
  --schema <path>     Schema directory override
  --pattern <glob>    Glob pattern to match files (default: **/*.md)
  --format <format>   Output format: pretty, json, compact (default: pretty)
  --strict            Enable strict naming validation (default: true)
  --no-strict         Disable strict naming validation
```

### format

Format documentation files according to body grammar rules.

```bash
synapse format [options]

Options:
  --dir <path>        Content directory to format (default: content/)
  --write             Write changes to files (default: dry-run)
  --pattern <glob>    Glob pattern to match files (default: **/*.md)
  --verbose           Show all files, including unchanged
```

### scaffold

Create a new document from a template.

```bash
synapse scaffold [options]

Options:
  --type <type>       Document type (required)
  --title <title>     Document title (required)
  --owner <owner>     Document owner (optional)
  --id <id>           Custom document ID (default: auto-generated)
  --target-dir <path> Output directory (default: content/{type folder})
  --force             Overwrite existing files
```

Available document types: adr, agreement, capability, meeting, policy, prd, process, reference, runbook, scorecard, sop, sow, standard, system, tdd.

### generate-pdf

Generate a PDF from Markdown with YAML frontmatter. Local images are embedded relative to the input file. Mermaid diagrams render using the installed package, with no CDN or global Mermaid CLI. Invalid diagrams and unreadable images fail the command instead of producing an incomplete PDF.

```bash
synapse generate-pdf [options]

Options:
  --input <path>      Input Markdown file (required)
  --output <path>     Output PDF file path (required)
  --logo <path>       Logo image path (optional)
  --company <name>    Company name for letterhead (optional)
  --url <url>         Company URL for letterhead (optional)
  --no-validate       Skip schema validation
```

### fetch-reference

Fetch external documentation and convert to markdown.

```bash
synapse fetch-reference <url>
```

### index

Generate the homepage index.md with navigation.

```bash
synapse index [options]

Options:
  --dir <path>        Content directory (default: content/)
  --output <path>     Output file path (default: content/index.md)
```

## Schema Resolution

The CLI resolves schemas using a cascade:

1. **Local override**: `{projectRoot}/schemas/frontmatter/{name}.schema.json`
2. **@millstone/synapse-schemas package**: Standard schemas from the npm package
3. **Error**: With a message explaining how to install schemas

This allows projects to customize individual schemas while using the standard set as a base. The same cascade applies to body grammar rules in `schemas/body-grammars/`.

## License

MIT
