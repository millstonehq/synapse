---
description: Sync vault documentation with current code changes
---

# Sync Docs

Find and update any Synapse vault documentation that has become stale relative to the current code changes.

## Overview

This command detects code changes via `git diff`, uses the context-helper-synapse MCP server to find all vault documents referencing the affected code, and updates stale sections to reflect the current state. It covers ALL document types: PRDs, TDDs, ADRs, SOPs, system docs, runbooks, etc.

**Performance target**: < 3 minutes for a typical change affecting 2-3 docs.

## Instructions

### Phase 1: Detect Code Changes

1. **Get the current diff**:
   ```bash
   git diff
   ```
   This shows unstaged changes. If the diff is empty, inform the user and stop.

2. **Parse the diff** to extract:
   - Changed file paths
   - Nature of changes (new functions, modified interfaces, config changes, etc.)
   - Key identifiers (function names, class names, config keys, API routes)

3. **Summarize the changes** internally — you'll use this summary to search for related docs.

### Phase 2: Search Vault for Relevant Documents

Use the **context-helper-synapse MCP tools** to search the vault efficiently. Do NOT use Glob or Grep to scan docs — use the indexed search tools instead.

**CRITICAL**: You MUST run multiple searches with different query strategies. A single search will miss docs that use different vocabulary (e.g., a TDD describes "architecture" while a PRD describes "requirements" — both may be stale from the same code change). Do NOT stop searching after finding the first relevant doc.

#### Step 1: Build search queries

From the code changes, identify:
- **Domain keywords**: The business domain (e.g., "payments", "authentication", "deployment")
- **Identifiers**: Function names, class names, file paths, API routes, config keys
- **Concepts**: What the change does at a high level (e.g., "multi-provider payment processing")

#### Step 2: Run semantic searches (minimum 3 queries)

Run AT LEAST 3 semantic searches targeting different document types and vocabulary:

```
# Query 1: Domain + technical terms (finds system docs, TDDs)
mcp__context-helper-synapse__semantic_search({
  query: "technical design architecture of [domain]",
  filter: { extensions: ["md"] }, include_content: true, max_results: 20
})

# Query 2: Domain + product terms (finds PRDs, capability docs)
mcp__context-helper-synapse__semantic_search({
  query: "[domain] product requirements features scope",
  filter: { extensions: ["md"] }, include_content: true, max_results: 20
})

# Query 3: Specific to what changed (finds directly referencing docs)
mcp__context-helper-synapse__semantic_search({
  query: "[specific description of the code change]",
  filter: { extensions: ["md"] }, include_content: true, max_results: 20
})
```

Fire all 3+ queries in parallel. Collect the union of all results — do not deduplicate until after reading.

#### Step 3: Run file searches for direct references

Search for specific identifiers from the diff that might appear in documentation:
```
mcp__context-helper-synapse__file_search({
  pattern: "changed-function-name",
  mode: "content",
  filter: { extensions: ["md"] }, include_content: true, max_results: 20
})
```

Also search for the domain keyword broadly across all content:
```
mcp__context-helper-synapse__file_search({
  pattern: "[domain-keyword]",
  mode: "content",
  filter: { extensions: ["md"] }, include_content: true, max_results: 20
})
```

#### Step 4: Completeness check with file tree

After collecting search results, verify you haven't missed anything:
```
mcp__context-helper-synapse__get_file_tree({ type: "files", path: "content", max_depth: 4 })
```

Scan the file tree for any docs whose **path or filename** contains domain keywords but that didn't appear in your search results. Read these docs to check relevance — search results can miss docs that use different vocabulary.

#### Step 5: Read ALL candidate docs

For every unique doc surfaced by steps 2-4, read the full content:
```
mcp__context-helper-synapse__read_file({
  path: "content/90_Architecture/TDDs/some-tdd.md"
})
```

Parse frontmatter to extract `type`, `tags`, `related_*` fields, and `summary`.

#### Step 6: Follow cross-references

For each doc you read, check its `related_tdds`, `related_adrs`, `related_standards`, and other `related_*` frontmatter fields. If any referenced doc hasn't been read yet, read it — cross-referenced docs are likely affected by the same changes.

#### Step 7: Score relevance and filter

Score each document against the code changes:
- **Direct reference**: Doc mentions a changed file path, function, class, or API route → HIGH
- **Cross-reference**: Doc has `related_*` fields pointing to affected docs → MEDIUM
- **Domain overlap**: Doc tags, title, or content overlap with the domain of the changes → MEDIUM
- **No match**: Skip entirely

Keep all HIGH and MEDIUM docs. If no docs are relevant, inform the user and stop.

### Phase 3: Analyze Staleness

For each relevant document:

1. **Compare doc content against code changes**:
   - Does the doc describe behavior that the code change modifies?
   - Does the doc reference APIs, interfaces, or configurations that changed?
   - Does the doc contain outdated examples or code snippets?
   - Are there section-level inaccuracies introduced by the code change?

2. **Classify each doc**:
   - **STALE**: Contains content that is now incorrect or outdated due to the code changes
   - **CURRENT**: Content is still accurate despite the code changes
   - **NEEDS_REVIEW**: Uncertain — content may be affected but requires judgment

3. **For STALE docs, identify specific sections** that need updating. Reference section headers (## headings) and describe what needs to change.

### Phase 4: Propose and Confirm Updates

1. **Present a summary** to the user showing:
   - Total docs found by search
   - Docs identified as relevant (with relevance level)
   - Docs classified as STALE (with specific sections)
   - Docs classified as NEEDS_REVIEW

   Format:
   ```
   ## Sync Docs Summary

   **Code Changes**: [brief description of what changed]
   **Docs Searched**: N found via MCP search
   **Relevant Docs**: M

   ### Stale Documents (will update)

   1. **[doc title]** (`content/path/to/doc.md`)
      - Type: [tdd/prd/adr/etc]
      - Stale sections: [section names]
      - Reason: [why it's stale]

   2. ...

   ### Needs Review

   1. **[doc title]** — [why it needs review]

   ### Current (no changes needed)

   1. **[doc title]** — still accurate
   ```

2. **Ask the user for confirmation** before making any edits:
   - "Should I proceed with updating the N stale documents listed above? You can also specify specific docs to skip or include from the Needs Review list."
   - Wait for the user's response before proceeding

### Phase 5: Update Documents

For each confirmed stale document:

1. **Read the full document** content using the Read tool (for editing, use the standard Read/Edit tools — MCP tools are for search, Read/Edit are for modification)

2. **Update stale sections** using the Edit tool:
   - Preserve all frontmatter fields EXCEPT `updated` (set to current ISO 8601 timestamp)
   - Preserve document structure and section ordering
   - Update only the specific content that is stale — do NOT rewrite entire documents
   - Match the existing writing style and level of detail
   - Preserve any wikilinks (`[[...]]`) and cross-references

3. **Key editing rules**:
   - Only edit sections identified as stale — leave everything else untouched
   - When updating code examples or snippets, match them to the new code
   - When updating behavioral descriptions, reflect the new behavior accurately
   - When updating API documentation, match the new signatures/routes
   - Do NOT add new sections unless the code change introduces entirely new functionality that an existing section should cover
   - Do NOT remove sections unless the code change removes the feature they describe

4. **Update the `updated` frontmatter field** to the current timestamp

### Phase 6: Validate

1. **Run validation** on each updated document:
   ```bash
   npx synapse validate content/path/to/updated-doc.md
   ```

2. **If validation fails**, fix the issues and re-validate. Common issues:
   - Missing required frontmatter fields
   - Invalid frontmatter values
   - Missing required sections for the doc type

3. **Report results**:
   ```
   ## Sync Complete

   **Updated**: N documents
   **Validated**: All passing

   ### Changes Made

   1. **[doc title]** (`content/path/to/doc.md`)
      - Updated sections: [section names]
      - Validation: passing

   2. ...

   ### Skipped

   - [any docs that were skipped and why]
   ```

## Command Flags

Parse these from the arguments:

- `--dry-run`: Show what would be updated without making changes. Still performs Phase 1-4 but skips Phase 5-6.
- `--include-review`: Also update docs classified as NEEDS_REVIEW (default: skip them)
- `--type <doctype>`: Only check documents of a specific type (e.g., `--type tdd`, `--type prd`)
- `--verbose`: Show detailed matching reasoning for each document

## MCP Tool Usage

Use these context-helper-synapse MCP tools for **searching and reading** vault docs:

| Tool | Use For |
|------|---------|
| `mcp__context-helper-synapse__semantic_search` | Find docs by concept/topic (e.g., "authentication flow") |
| `mcp__context-helper-synapse__file_search` | Find docs containing specific identifiers (function names, paths) |
| `mcp__context-helper-synapse__read_file` | Read full content of a candidate doc |
| `mcp__context-helper-synapse__get_file_tree` | Get vault structure overview if needed |

Use standard tools for **modifying** docs:

| Tool | Use For |
|------|---------|
| `Read` | Re-read a doc before editing (required by Edit tool) |
| `Edit` | Make targeted edits to stale sections |
| `Bash` | Run `git diff` and `npx synapse validate` |

## Document Type Reference

The vault uses these content directories (from TEMPLATE_REGISTRY):

| Type | Folder | Description |
|------|--------|-------------|
| `adr` | `content/90_Architecture/ADRs/` | Architecture Decision Records |
| `tdd` | `content/90_Architecture/TDDs/` | Technical Design Documents |
| `prd` | `content/100_Products/PRDs/` | Product Requirements Documents |
| `system` | `content/70_Systems/` | System documentation |
| `sop` | `content/40_SOPs/` | Standard Operating Procedures |
| `runbook` | `content/50_Runbooks/` | Runbooks |
| `process` | `content/30_Processes/` | Process docs |
| `policy` | `content/10_Policies/` | Policy documents |
| `standard` | `content/20_Standards/` | Standards |
| `capability` | `content/110_Capabilities/` | Capability docs |
| `reference` | `content/200_References/` | External references |
| `scorecard` | `content/80_Scorecards/` | Scorecards |
| `meeting` | `content/60_Meetings/` | Meeting notes |

## Important Rules

- **DO** use `git diff` (unstaged changes) as the source of code changes
- **DO** use MCP semantic_search and file_search to find relevant docs — do NOT manually Glob through all content directories
- **DO** parse frontmatter to understand doc type and cross-references
- **DO** preserve document structure — only edit stale sections
- **DO** update the `updated` frontmatter timestamp on every edited doc
- **DO** run `npx synapse validate` on every edited doc
- **DO** ask for user confirmation before making edits
- **DO** handle errors gracefully — if one doc fails, continue with others
- **DO NOT** rewrite entire documents — make targeted, minimal edits
- **DO NOT** change document `id`, `type`, `created`, or `owner` fields
- **DO NOT** add or remove sections unless clearly warranted by the code change
- **DO NOT** skip the confirmation step (Phase 4) unless `--dry-run` is set
- **DO NOT** modify reference docs (`type: reference`) — those are synced from upstream URLs
- **DO NOT** modify meeting notes (`type: meeting`) — those are historical records
- **DO NOT** modify documents with `status: deprecated` — they are intentionally archived

## Efficiency Tips

To meet the < 3 minute performance target:

1. **Search, don't scan**: Use semantic_search and file_search with targeted queries instead of reading every doc in the vault
2. **Run multiple searches in parallel**: Fire off several MCP search queries at once covering different aspects of the change
3. **Read frontmatter first**: For candidate docs, check the first ~20 lines to extract frontmatter before reading the full body — skip `example: true`, `type: reference`, `type: meeting`, and `status: deprecated` docs early
4. **Minimize edit passes**: Collect all edits for a single doc and apply them in one pass
5. **Skip references and meetings**: These doc types are never updated by sync-docs
