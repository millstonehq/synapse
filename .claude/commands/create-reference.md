---
description: Create a new reference document by fetching content from an external URL
---

# Create Reference Document

Create a new reference document in `content/200_References/` by fetching full content from an upstream URL and converting it to markdown.

## Instructions

1. **Validate environment** - Check if running in synapse project:
   ```bash
   if [ ! -f "package.json" ] || ! grep -q '"@millstone/synapse-cli"' package.json 2>/dev/null; then
     echo "Error: Must run from synapse project root directory"
     echo "Current directory: $(pwd)"
     exit 1
   fi
   ```

2. **Parse the URL parameter** provided by the user

3. **Fetch and convert content using synapse CLI**:
   ```bash
   npx synapse fetch-reference {url}
   ```
   - This uses Mozilla Readability + Turndown for deterministic conversion
   - Returns JSON with: `{ markdown, title, byline, excerpt, url }`
   - Preserves ALL content from the main article area

4. **Parse the JSON output** to extract:
   - `markdown`: Full converted markdown content
   - `title`: Page title
   - `byline`: Author attribution (if available)
   - `excerpt`: Brief description (if available)

5. **Generate a filename** from the URL with source prefix:
   - Extract source prefix from domain (e.g., `docs.claude.com` → `claude-code-`)
   - Extract the last meaningful path segment from URL path
   - Convert path segment to kebab-case
   - Combine as: `{source-prefix}-{path-slug}.md`
   - Examples:
     - `https://docs.claude.com/en/docs/claude-code/hooks` → `claude-code-hooks.md`
     - `https://dora.dev/research/2025/` → `dora-2025.md`
     - `https://docs.mercury.com/reference` → `mercury-reference.md`
   
   **Source prefix extraction rules**:
   - Known domains: `docs.claude.com` → `claude-code`, `dora.dev` → `dora`, `docs.mercury.com` → `mercury`
   - Pattern `docs.{name}.com` → `{name}`
   - Pattern `api.{name}.com` → `{name}`
   - Generic domains (github.com, etc.) → use first path segment
   - Fallback → use domain name without TLD

6. **Generate frontmatter automatically** (best-effort, no manual input):
   - `id`: Generate from filename without `.md` extension (e.g., "claude-code-hooks")
   - `type`: reference
   - `title`: Use title from JSON output
   - `status`: draft
   - `owner`: automation
   - `created`: Current ISO 8601 timestamp
   - `updated`: Current ISO 8601 timestamp (same as created initially)
   - `summary`: Use excerpt from JSON output (or "External reference document" if not available)
   - `upstream_url`: The fetched URL
   - `last_synced`: Current ISO 8601 timestamp
   - `source_prefix`: (Optional) Only add if extraction from URL failed; allows manual override

7. **Write the file** to `content/200_References/{filename}` with:
   - Auto-generated frontmatter
   - Full converted markdown content from the CLI output

## Important Rules

- **MUST run from synapse project root** - Command validates environment first
- **DO use synapse fetch-reference command** - it uses deterministic conversion
- **DO NOT use WebFetch** - it summarizes content
- **DO preserve full content** - no summarization
- Each reference must have 1:1 relationship with upstream URL
- Set `last_synced` to current ISO 8601 timestamp
- Set `status: draft` initially
- **Fully automated** - no manual questions required

## Example Usage

```
/create-reference https://docs.claude.com/en/docs/claude-code/hooks
```

This will:
1. Validate you're in synapse project root
2. Call `npx synapse fetch-reference https://docs.claude.com/en/docs/claude-code/hooks`
3. Parse the JSON output to extract markdown, title, and metadata
4. Extract source prefix from domain (`docs.claude.com` → `claude-code-`)
5. Generate filename with source prefix: `claude-code-hooks.md`
6. Auto-generate frontmatter from JSON output
7. Create `content/200_References/claude-code-hooks.md` with complete content
8. No manual questions required!

**If run from wrong directory:**
```
Error: Must run from synapse project root directory
Current directory: /Users/you/somewhere-else
```

## Example Frontmatter

```yaml
---
id: claude-code-hooks
type: reference
title: "Using Hooks in Claude Code"
status: draft
owner: automation
created: "2025-01-29T12:00:00.000Z"
updated: "2025-01-29T12:00:00.000Z"
summary: "Documentation on configuring and using hooks in Claude Code for custom workflows."
upstream_url: https://docs.claude.com/en/docs/claude-code/hooks
last_synced: "2025-01-29T12:00:00.000Z"
---
```

**Note**: Filename will be `claude-code-hooks.md` (source prefix `claude-code-` + path slug `hooks`)

**Note**:
- All fields auto-generated from fetch output and context
- Optional fields like `attribution`, `license`, `category`, and `tags` can be added manually later if needed
- `owner: automation` indicates this was auto-created from external source
