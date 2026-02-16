---
description: Sync external reference documents from their upstream URLs
---

# Update References

Scan `content/200_References/` for reference documents and sync them with their upstream sources.

## Instructions

1. **Scan for reference documents**:
   - Use Glob to find all markdown files in `content/200_References/`
   - Read each file and parse the frontmatter
   - Filter for files with `type: reference`

2. **Parse command flags**:
   - `--force`: Update all references regardless of staleness
   - `--dry-run`: Show what would be updated without making changes
   - `--max-age <days>`: Custom staleness threshold (default: 30 days)

3. **For each reference document**:
   - Extract `upstream_url` and `last_synced` from frontmatter
   - Calculate age: current time - last_synced
   - Skip if not stale (unless --force is set)
   
4. **Fetch fresh content**:
   ```bash
   npx synapse fetch-reference {upstream_url}
   ```
   - Parse JSON output to get fresh markdown content

5. **Compare content**:
   - Extract body content (everything after frontmatter)
   - Compare old body vs new markdown
   - Show diff using the Edit tool preview if there are changes
   
6. **Update file** (unless --dry-run):
   - Keep existing frontmatter metadata (title, attribution, license, category, summary)
   - Update only the body content with fresh markdown
   - Update `last_synced` to current ISO 8601 timestamp
   - Use Edit tool to replace the body content

7. **Report results**:
   - Show summary of scanned files
   - List updated files with change counts
   - List skipped files (not stale)
   - List failed fetches (with errors)

## Staleness Logic

A reference is considered stale if:
```
(current_time - last_synced) > max_age_days
```

Default max_age: 30 days

## Important Rules

- **DO use synapse fetch-reference** for fetching fresh content
- **DO preserve frontmatter** - only update body content and last_synced
- **DO show diffs** before updating (unless --dry-run)
- **DO handle errors gracefully** - continue with other files if one fails
- Use ISO 8601 format for timestamps

## Example Usage

### Update all stale references (older than 30 days)
```
/update-references
```

### See what would be updated (dry run)
```
/update-references --dry-run
```

### Force update all references regardless of age
```
/update-references --force
```

### Custom staleness threshold (update if older than 7 days)
```
/update-references --max-age 7
```

## Example Output

```
Scanning content/200_References/ for reference documents...

Found 5 reference documents:
  - claude-code-hooks.md (last synced: 25 days ago) ✓ stale
  - claude-code-plugins.md (last synced: 15 days ago) ✓ stale  
  - claude-code-skills.md (last synced: 5 days ago) ✗ fresh
  - readability-api.md (last synced: 45 days ago) ✓ stale
  - turndown-docs.md (last synced: 10 days ago) ✗ fresh

Updating 3 stale references...

[1/3] Updating claude-code-hooks.md
  Fetching from https://docs.claude.com/en/docs/claude-code/hooks
  Changes detected: +15 lines, -3 lines
  ✓ Updated

[2/3] Updating claude-code-plugins.md
  Fetching from https://docs.claude.com/en/docs/claude-code/plugins
  No changes detected
  ✓ Synced timestamp only

[3/3] Updating readability-api.md
  Fetching from https://github.com/mozilla/readability/blob/main/README.md
  ✗ Failed: 404 Not Found

Summary:
  ✓ 2 updated successfully
  ✗ 1 failed
  - 2 skipped (not stale)
```

## Error Handling

If a fetch fails:
- Log the error with URL and status code
- Continue with remaining references
- Include in final summary

Common errors:
- 404 Not Found: URL may have changed
- Network timeout: Retry or skip
- Parse error: HTML structure may have changed
