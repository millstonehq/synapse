---
description: Build a handoff prompt after finding relevant code context
---

## MANDATORY: Read This First

**This command produces a handoff prompt, not direct analysis.**

### Before You Start

1. **Classify the request:**
   - Implementation task (add feature, fix bug, refactor) → Proceed with discovery
   - Analysis/review request ("tell me about", "how can I improve") → **ASK FIRST**
   - Unclear scope → Ask clarifying questions

2. **If the request looks like analysis:**
   Ask the user: "This looks like an analysis request rather than an implementation task. Would you like me to:
   A) Build a handoff prompt with context for future implementation
   B) Provide direct analysis without the handoff format

   /discover is designed for (A). If you want (B), I can do that instead."

### Required Output Format

Your final output MUST be a handoff prompt with these sections:
- `# Task` - Clear restatement
- `# Architecture` - Relevant codebase structure
- `# Selected Code Context` - Actual code inline (not file references)
- `# Relationships` - Dependencies and data flows
- `# Ambiguities` - Factual observations or "None"
- `# Implementation Notes` - Context about selections made

**A validation hook checks this format.** If you skip it, you'll be asked to revise.

### What NOT To Do

- Don't provide direct recommendations or analysis as your final output
- Don't say "here are improvements" without the handoff structure
- Don't skip the inline code in "Selected Code Context"
- Don't assume the user wants analysis when they invoked /discover

---

# Discover - Context Curation for Code Tasks

Curate the perfect file selection and craft a precise handoff prompt for complex coding tasks. Inspired by RepoPrompt's MCP Discover workflow.

## Mission

You are a **context discovery agent**. Your goal is to:
1. **Explore** the codebase to understand the task requirements
2. **Curate** a focused selection of relevant files
3. **Craft** a clear handoff prompt that enables effective implementation

**CRITICAL:** You are NOT solving the problem—you're gathering complete context so a future implementation can explore different approaches.

## Available Tools

Use these MCP tools from `context-helper-synapse`:
- `mcp__context-helper-synapse__workspace_context` - Get current selection and token counts
- `mcp__context-helper-synapse__get_file_tree` - Map directory structure
- `mcp__context-helper-synapse__get_code_structure` - Extract code structure with tree-sitter
- `mcp__context-helper-synapse__file_search` - **Search indexed chunks with FTS5 + BM25 ranking**
- `mcp__context-helper-synapse__read_file` - Read specific file contents
- `mcp__context-helper-synapse__manage_selection` - Add/remove files from context
- `mcp__context-helper-synapse__index_code` - Index files for structure extraction

## How file_search Works

The `file_search` tool searches **pre-indexed chunks** stored in a local SQLite database using FTS5 (full-text search) with BM25 ranking. These chunks are automatically indexed and represent semantically meaningful code sections.

**Key points:**
- Returns **relevant chunks**, not full files
- Each chunk contains focused, contextual code snippets
- Use `include_content: true` to see chunk contents during exploration
- Chunks guide you to the minimal necessary slices

## The Discovery Workflow

### Phase 1: Exploration

**1. Understand existing context**
```
workspace_context with path_display="relative"
```
This shows current selection, tokens, and prompt state.

**2. Map the terrain**
```
get_file_tree with type="files", mode="folders"
```
For focused exploration, add path and max_depth parameters.

**3. Discover relevant code** (use both approaches as needed):

**Option A: Chunk-based search** (optimized grep for finding specific code)
```
file_search with pattern="UserTermOrSymbol", mode="content", include_content=true, max_results=50
```
- Returns **indexed chunks** ranked by relevance (BM25)
- Chunks show you exactly where relevant code lives
- Use this when searching for specific functionality, terms, or patterns
- Chunks directly guide minimal slice creation

**Option B: Architecture-first with codemaps**
```
get_code_structure with scope="paths", paths=["Root/src/services", "Root/src/models"]
```
- Reveals class hierarchies, function signatures, and relationships
- Use this to understand module structure and find related files
- Codemaps guide you to the right files/sections to slice

**Both approaches are valuable** - use whichever fits the task:
- **Search** when you know what to look for (terms, functionality)
- **Codemaps** when you need to understand architecture first
- **Combine both** for comprehensive discovery

**4. Verify and bound slices**
```
read_file with path="Root/src/File.swift", start_line=40, limit=50
```
After finding relevant chunks or codemap symbols:
- Read surrounding context to find natural boundaries
- Verify the chunk/section is self-contained
- Determine if expansion is needed or if chunk is sufficient

### Phase 2: Curation

**5. Build minimal slices from chunks**

**CRITICAL PRINCIPLE: Prefer minimal slices over full files**

When `file_search` returns relevant chunks:
1. **Evaluate the chunk** - Does it contain enough information?
   - ✅ If yes: Create a slice around that chunk (minimal necessary context)
   - ❌ If no: Read surrounding code to find natural boundaries

2. **Determine slice boundaries** using `read_file`:
   - Find the complete function/class/block containing the chunk
   - Include necessary imports/dependencies at file top
   - Ensure slice is self-contained

3. **Add the minimal slice** to selection:

Use the `mcp__context-helper-synapse__manage_selection` tool with:
- `op`: "add" (or "set" to replace entire selection)
- `slices`: Array of slice objects, each containing:
  - `path`: File path
  - `ranges`: Array of range objects with:
    - `startLine`: Start line number (camelCase, not snake_case!)
    - `endLine`: End line number (camelCase, not snake_case!)
    - `description`: What this slice contains and why it's relevant

**Example slice addition:**
```json
{
  "op": "add",
  "slices": [{
    "path": "Root/src/Auth.swift",
    "ranges": [{
      "startLine": 45,
      "endLine": 120,
      "description": "UserAuth.login() method - handles JWT token creation (found via search)"
    }]
  }]
}
```

**Multiple ranges from same file:**
```json
{
  "op": "add",
  "slices": [{
    "path": "Root/src/Auth.swift",
    "ranges": [
      {"startLine": 45, "endLine": 120, "description": "UserAuth.login() method"},
      {"startLine": 200, "endLine": 250, "description": "UserAuth.logout() method"}
    ]
  }]
}
```

**Add slices incrementally from different files:**
```json
// First file
{"op": "add", "slices": [{"path": "Root/src/Auth.swift", "ranges": [...]}]}

// Second file - automatically appends
{"op": "add", "slices": [{"path": "Root/src/User.swift", "ranges": [...]}]}

// Add more ranges to existing file - automatically merges
{"op": "add", "slices": [{"path": "Root/src/Auth.swift", "ranges": [{"startLine": 300, "endLine": 350, "description": "token validation"}]}]}
```

**Other selection operations:**
- Full file: `{"op": "add", "paths": ["Root/src/File.swift"]}`
- Codemap only: `{"op": "add", "mode": "codemap_only", "paths": ["Root/src/Types.swift"]}`
- Clear selection: `{"op": "clear"}`
- View current: `{"op": "get", "view": "summary"}`

**Selection strategy (in priority order):**

1. **Minimal slices** (PREFERRED) - Based on chunks found via search
   - Only include the relevant function/class/section
   - Expand only if chunk lacks critical context
   - Each slice typically 20-150 lines

2. **Expanded slices** - When minimal chunks need more context
   - Include related methods/dependencies
   - Show interconnections within the file
   - Typically 100-300 lines

3. **Full files** - Only when truly necessary:
   - File is small (<200 lines) and entirely relevant
   - File is likely to be heavily edited
   - Slicing would fragment understanding

4. **Codemap-only** - For architectural reference:
   - Type definitions/interfaces used for reference
   - Dependencies where only signatures matter
   - Files providing context but not implementation

**Slicing guidelines:**
- Each slice MUST have a descriptive `description` explaining content and why it's included
- Reference the chunk or search that led to this slice
- Start with smallest necessary slice, expand only if needed
- Target 50-80k tokens total (include more slices rather than full files)

**Workflow for building multi-file selections (natural incremental approach):**
```
1. Search and identify relevant chunk in first file
2. Read file to determine slice boundaries
3. Add slice: op="add" with slices=[first_slice]
4. Find chunk in second file, read, add: op="add" with slices=[second_slice]
5. Find more chunks, continue adding incrementally
6. Add full files if needed: op="add", paths=[...]
7. Verify tokens with workspace_context(include=["tokens"])
```

This incremental workflow is now fully supported! Add slices as you discover them.

**6. Export selection as inline content**

Use `workspace_context` to get the actual file/slice contents:
```json
{
  "include": ["files", "tokens"]
}
```

This returns:
- `file_contents`: All selected files/slices with their actual code
- `tokens`: Total token count

**7. Craft the self-contained handoff prompt**

Build a complete, portable handoff prompt with **inline code content**:

```markdown
# Task

[Clear restatement of the task]

# Architecture

[Key modules and their responsibilities discovered during exploration]

# Selected Code Context

[Paste the file_contents from workspace_context here - includes all slices/files with descriptions]

# Relationships

- LoginView → UserAuth.login() → Token → SessionStore
- UserAuth implements Authenticatable protocol
[Map dependencies and data flows]

# Ambiguities

[Factual observations if genuine ambiguity exists, OR "None"]

# Implementation Notes

[Any important context about why these specific slices were chosen, patterns observed, etc.]
```

**CRITICAL:** The handoff prompt is **self-contained** with all code inline. This makes it:
- ✅ Portable (copy/paste anywhere)
- ✅ Reliable (works even if MCP resets)
- ✅ Inspectable (see exactly what's included)
- ✅ Shareable (can be saved or shared with others)

**8. Verify final token count**

The `workspace_context` response includes total tokens. Ensure you're within ~50–80k tokens.

**9. Output the handoff prompt and halt**

Output the complete handoff prompt as text, then await further instructions. Do not implement unless explicitly requested.

## Core Principles

- **Chunks guide slices** - Use search results to identify minimal necessary context
- **Minimal is better** - Start with the smallest slice that contains relevant code
- **The selection is the universe** - The next model only sees what you select, but prefer precision over bulk
- **Don't assume a solution** - Select context for multiple possible approaches, not just your imagined solution
- **Think like a different model** - The next model may solve this differently than you would
- **Expand only when needed** - If a chunk lacks context, expand to natural boundaries (not the whole file)
- **Resolve ambiguity now** - Clarify task scope during exploration

## Selection Priority (Inverted from Traditional Approach)

1. **Minimal slices** (PREFERRED) - Chunks found via search, bounded to function/class
2. **Expanded slices** - When minimal chunks need dependencies or related methods
3. **Full files** - Only for small files (<200 lines) or when heavily edited
4. **Codemap-only** - Pure type definitions or architectural reference

## Best Practices

✅ Prefer minimal slices over full files when possible
✅ Use chunk-based search (`file_search`) to guide slice selection
✅ Always read actual code before creating slices to verify boundaries
✅ Include descriptive `description` for each slice explaining what and why
✅ Select context for multiple possible approaches, not just one solution
✅ Read enough files during exploration to understand the full context
✅ Verify final token count before outputting handoff prompt
✅ Output handoff prompt with inline code, then halt (don't implement unless requested)

## Example Usage

```
/discover

User task: Add user authentication with JWT tokens
```

The command will:
1. **Search** for "authentication", "JWT", "token", "login" to find relevant chunks
2. **Review chunks** to identify files like AuthService.ts, User.ts, TokenUtils.ts
3. **Read specific sections** to find natural boundaries around the chunks
4. **Create minimal slices**:
   - AuthService.ts lines 45-120 (login/logout methods)
   - TokenUtils.ts lines 15-80 (JWT creation/validation)
   - User.ts lines 30-60 (User model with auth fields)
5. **Add codemaps** for related interfaces/types (SessionStore, AuthConfig)
6. **Build handoff prompt** describing current auth architecture and task
7. **Verify token budget** (~20-30k for this focused selection)
8. **Halt** and await implementation instructions

**Key difference:** Instead of selecting 3 full files (potentially 1000+ lines), you select 3 targeted slices (~200 lines total) plus codemaps, staying well under token budget while including all necessary implementation details.

## Success Criteria

✅ **Chunk-based discovery** used to find relevant code sections
✅ **Minimal slices** created (not full files by default)
✅ Selection executed targeting 50–80k tokens (often much less with slices)
✅ Handoff prompt created with architectural clarity
✅ Complete token count verified
✅ Architecture understood through exploration
✅ All necessary implementation details included in slices

## Notes

- This command focuses on **discovery and curation**, not implementation
- **file_search returns chunks** - use these to guide slice creation
- **Prefer minimal slices** - only expand when chunks lack critical context
- The handoff prompt you create can be used by another model or saved for later
- Think of yourself as a scout mapping territory with laser precision
- Efficient token usage through slicing allows for more comprehensive coverage of relevant code
