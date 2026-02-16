---
name: synapse-docs
description: Create, validate, fix, and scaffold Synapse documents. Covers all 15 document types with schema-enforced frontmatter and body-grammar rules. Uses the scaffold command for new docs and validate for compliance checks.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Synapse Document Specialist

Create, validate, and fix documents in a Synapse vault — a structured knowledge management system with strict schema validation across 15 document types.

## When to Use

- Creating new documents (use `synapse scaffold`)
- Fixing validation errors
- Understanding document structure and requirements
- Converting or restructuring document content to comply with body-grammar rules

## Quick Start

### Scaffold a New Document

```bash
synapse scaffold --type <type> --title "Document Title" [--owner "Team"] [--id "CUSTOM-001"]
```

Available types: `adr`, `agreement`, `capability`, `meeting`, `policy`, `prd`, `process`, `reference`, `runbook`, `scorecard`, `sop`, `sow`, `standard`, `system`, `tdd`

The scaffold command:
- Finds the example file in `content/<folder>/examples/`
- Copies it with updated frontmatter (id, title, dates, status: draft)
- Auto-generates sequential IDs (e.g., TDD-001, PRD-003)
- Writes to the correct content folder

### Validate Documents

```bash
synapse validate                          # validate all
synapse validate --dir content --strict   # strict mode
```

Validation checks:
- YAML frontmatter schema compliance
- Required sections present
- Section content restrictions (allowed node types per section)
- Filename slug matches document title
- Reference document prefix conventions

## Document Types and Folders

| Type | Folder | Display |
|------|--------|---------|
| adr | `content/90_Architecture/ADRs` | ADR |
| agreement | `content/120_Legal/agreements` | Agreement |
| capability | `content/110_Capabilities` | Capability |
| meeting | `content/60_Meetings` | Meeting |
| policy | `content/10_Policies` | Policy |
| prd | `content/100_Products/PRDs` | PRD |
| process | `content/30_Processes` | Process |
| reference | `content/200_References` | Reference |
| runbook | `content/50_Runbooks` | Runbook |
| scorecard | `content/80_Scorecards` | Scorecard |
| sop | `content/40_SOPs` | SOP |
| sow | `content/120_Legal/SOWs` | SOW |
| standard | `content/20_Standards` | Standard |
| system | `content/70_Systems` | System |
| tdd | `content/90_Architecture/TDDs` | TDD |

## Schema Cascade

Schemas resolve in priority order:
1. **Local custom** — `schemas/frontmatter/custom/`, `schemas/body-grammars/custom/`
2. **Local base** — `schemas/frontmatter/`, `schemas/body-grammars/` (fork mode only)
3. **@millstone/synapse-schemas package** — from `node_modules/@millstone/synapse-schemas/` (npm mode)

Custom schemas override base schemas. This lets you extend or restrict rules per-project without modifying the upstream package.

## Body-Grammar Rules (Key Document Types)

Body grammars define which markdown AST node types are allowed in each section. Fix the **document content**, never loosen the schema.

### TDD (Technical Design Document)

**Restricted sections (paragraph + list + heading + thematicBreak only):**
- Summary, Overview, Work Plan, Risks and Mitigations

**Sections that also allow code:**
- Architecture (+ code, blockquote), Information Model (+ code), Interfaces (+ code), Files and Layout (+ code), Operations (+ code)

**Appendix allows tables** — move tables here if needed.

Common fix: Convert tables in Overview/Risks to bullet lists.

### Meeting Notes

**Section-specific rules:**
- "Meeting Details": paragraph, list only (no thematicBreak)
- "Observations by Domain": MUST use unordered lists (`-`), NOT ordered (`1. 2. 3.`)
- "Risks and Mitigations": MUST be a table
- "Decisions & Next Steps": paragraph, list, heading only (no blockquotes)

### System Documentation

**Section-specific rules:**
- "Overview": paragraph only — NO lists
- "Architecture": paragraph, list, code only — NO headings, NO tables
- "Repositories": must be a list
- "SLA": paragraph, table only — NO headings, NO lists

### PRD (Product Requirements)

**Section-specific rules:**
- "Requirements": paragraph, list only — NO headings, NO tables, NO code
- "Information Architecture": paragraph, list, code, blockquote — NO headings
- "Data Model": paragraph, list, code, table — NO headings
- "Risks": paragraph, list only — NO tables

## Common Validation Errors and Fixes

### 1. Disallowed Node Types

**Error:** `Section "Overview" does not allow table nodes`

**Fix:** Convert the table to a bullet list:
```markdown
# Before (WRONG — table in a non-table section)
| Feature | Status |
|---------|--------|
| Auth    | Done   |

# After (CORRECT — bullet list)
- **Auth** — Done
- **Search** — In Progress
```

### 2. Filename Slug Mismatch

**Error:** `Filename 'foo-bar' does not match expected slug 'foo-bar-baz'`

**Fix:** Rename file to match the slugified title:
```bash
git mv content/path/foo-bar.md content/path/foo-bar-baz.md
```

Also update the `id` field in frontmatter to match.

### 3. Ordered vs Unordered Lists

**Error:** `expected numbered (1. 2. 3.) list but found bulleted` (or vice versa)

**Fix:** Convert list style to match the section requirement.

### 4. Headings in Restricted Sections

**Error:** `Section "Requirements" does not allow heading nodes`

**Fix:** Convert `###` subheadings to **bold text** labels:
```markdown
# Before
### Functional Requirements
- Requirement 1

# After
**Functional Requirements**
- Requirement 1
```

### 5. YAML Frontmatter Issues

Quote strings containing colons:
```yaml
# Before (WRONG)
summary: This is: a summary

# After (CORRECT)
summary: "This is: a summary"
```

Ensure arrays use list syntax:
```yaml
# Before (WRONG)
related_adrs: "ADR-001: Title"

# After (CORRECT)
related_adrs:
  - "ADR-001: Title"
```

### 6. Missing Required Sections

Add the section with appropriate content matching body-grammar rules. Check the body-grammar JSON for the type to see which nodes are allowed.

## Workflow

### Creating a New Document

1. **Scaffold:** `synapse scaffold --type tdd --title "Feature Name — Technical Design"`
2. **Edit** the generated file — fill in real content per section
3. **Validate:** `synapse validate`
4. **Fix** any errors following the rules above
5. **Iterate** until clean

### Bulk Validation Fix

1. Run `synapse validate` to see all errors
2. Group errors by file and error type
3. Fix each file — respect body-grammar rules (fix content, not schemas)
4. Re-validate after each batch
5. Success: all documents pass

## Critical Rules

1. **Fix the document, not the schema** — When content doesn't match body-grammar rules, restructure the content. Never loosen schema constraints.
2. **Always validate after changes** — Run `synapse validate` to confirm compliance.
3. **Use `git mv` for renames** — Preserve file history when renaming to fix slug mismatches.
4. **Respect section restrictions** — Each section's allowed nodes are defined in the body-grammar JSON. Check `schemas/body-grammars/<type>.body-grammar.json` when unsure.
5. **Tables go in Appendix** — If a TDD section doesn't allow tables, move the table to Appendix or convert to a bullet list.
6. **Quote YAML special characters** — Values with `:`, `#`, `{`, `}`, `[`, `]` need quoting.
