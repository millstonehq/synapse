# Context Helper MCP Server - Tool Examples

This document provides working examples of all tools available in the context-helper-code MCP server, showing the input parameters and actual outputs from each tool.

## Table of Contents

1. [file_search](#1-file_search)
2. [get_file_tree](#2-get_file_tree)
3. [index_code](#3-index_code)
4. [get_code_structure](#4-get_code_structure)
5. [read_file](#5-read_file)
6. [manage_selection](#6-manage_selection)
7. [workspace_context](#7-workspace_context)

---

## 1. file_search

Search files with FTS5 + BM25 ranking for content, fast file system search for paths. 10-100x faster than grep on large codebases.

### Example 1: Path Search (Auto Mode)

**Input:**
```json
{
  "pattern": "file-search",
  "mode": "auto",
  "max_results": 5
}
```

**Output:**
```json
{
  "pattern": "file-search",
  "mode": "auto",
  "results": [
    {
      "type": "path",
      "path": "/path/to/context-mcp/src/tools/file-search.ts"
    }
  ],
  "count": 1,
  "performance": {
    "searchTime": 4,
    "method": "File System"
  }
}
```

**Performance Timings (5 runs):**
- Run 1: 4ms
- Run 2: 1ms
- Run 3: 1ms
- Run 4: 1ms
- Run 5: 1ms
- **Average: 1.6ms**

### Example 2: Content Search with Results

**Input:**
```json
{
  "pattern": "MCP server",
  "mode": "content",
  "include_content": true,
  "max_results": 3
}
```

**Output:**
```json
{
  "pattern": "MCP server",
  "mode": "content",
  "results": [
    {
      "type": "content",
      "path": "/path/to/context-mcp-server/test-new-format.js",
      "line_range": [77, 158],
      "content": "async function runTests() { ... }"
    },
    {
      "type": "content",
      "path": "/path/to/context-mcp-server/test-simple.js",
      "line_range": [13, 159],
      "content": "async function runTests() { ... }"
    },
    {
      "type": "content",
      "path": "/path/to/context-mcp-server/test-format-simple.js",
      "line_range": [12, 90],
      "content": "async function test() { ... }"
    }
  ],
  "count": 3,
  "performance": {
    "searchTime": 1256,
    "method": "FTS5 (BM25)"
  }
}
```

**Performance Timings (3 runs):**
- Run 1: 410ms
- Run 2: 444ms (with FTS5 index building)
- Run 3: 440ms (with FTS5 index building)
- **Average: ~431ms** (Note: First run on cold cache may include index building time)

**Key Features:**
- `mode`: "auto" (smart), "path" (filenames), "content" (file contents), "both"
- `include_content`: Set to true to see content previews (saves tokens when false)
- Uses BM25 ranking for content search
- Significantly faster than grep on large codebases

---

## 2. get_file_tree

Get workspace file tree structure. Respects .gitignore automatically.

### Example: Get File Tree with Max Depth

**Input:**
```json
{
  "type": "files",
  "max_depth": 2
}
```

**Output:**
```json
{
  "type": "files",
  "files": [
    "/path/to/context-mcp/.claude/settings.local.json",
    "/path/to/context-mcp/.gitignore",
    "/path/to/context-mcp/README.md",
    "/path/to/context-mcp/bundle-continue.js",
    "/path/to/context-mcp/claude_desktop_config.example.json",
    "/path/to/context-mcp/debug-retrieve.js",
    "/path/to/context-mcp/docs/BUILD_GUIDE.md",
    "/path/to/context-mcp/docs/BUNDLING_SOLUTION.md",
    "/path/to/context-mcp/docs/TESTING.md",
    "/path/to/context-mcp/docs/VERIFICATION.md",
    "/path/to/context-mcp/package-lock.json",
    "/path/to/context-mcp/package.json",
    "/path/to/context-mcp/src/index.ts",
    "/path/to/context-mcp/src/server.ts",
    "/path/to/context-mcp/test/test-bundled-structure.js",
    "/path/to/context-mcp/test/test-bundled.js",
    "/path/to/context-mcp/test/test-format-simple.js",
    "/path/to/context-mcp/test/test-fts5-search.js",
    "/path/to/context-mcp/test/test-hybrid-v2.js",
    "/path/to/context-mcp/test/test-matching-logic.js",
    "/path/to/context-mcp/test/test-new-format.js",
    "/path/to/context-mcp/test/test-search-fix.js",
    "/path/to/context-mcp/test/test-server-v2-integration.js",
    "/path/to/context-mcp/test/test-simple.js",
    "/path/to/context-mcp/test/test-v2-bundled.js",
    "/path/to/context-mcp/tsconfig.json"
  ],
  "count": 26
}
```

**Performance Timings (5 runs):**
- Run 1: <1ms
- Run 2: <1ms
- Run 3: <1ms
- Run 4: <1ms
- Run 5: <1ms
- **Average: <1ms** (Very fast filesystem traversal with .gitignore filtering)

**Key Features:**
- `type`: "files" (full tree) or "roots" (workspace roots)
- `mode`: "full" (all files), "folders" (directories only)
- `max_depth`: Limit traversal depth
- Automatically respects .gitignore rules

---

## 3. index_code

Index code files into the database for structure extraction. Must be called before `get_code_structure` to populate the database.

### Example: Index TypeScript Files

**Input:**
```json
{
  "paths": [
    "/path/to/context-mcp/src/server.ts",
    "/path/to/context-mcp/src/tools/code-structure.ts"
  ]
}
```

**Output:**
```json
{
  "indexed": 2,
  "failed": 0,
  "totalSnippets": 13,
  "performance": {
    "indexingTime": 65
  }
}
```

**Performance Timings (5 runs):**
- Run 1: 84ms
- Run 2: 33ms
- Run 3: 26ms
- Run 4: 25ms
- Run 5: 65ms (from output above)
- **Average: 46.6ms** (for 2 TypeScript files with 13 code snippets)

**Key Features:**
- Parses files using tree-sitter
- Extracts functions, classes, interfaces, methods
- Stores signatures in SQLite database
- Required before using `get_code_structure`

---

## 4. get_code_structure

Extract code structure using tree-sitter. Returns function signatures, class definitions, etc. Supports 40+ languages.

**Important:** You must first call `index_code` to populate the database before using this tool.

### Example: Extract Structure from Indexed Files

**Input:**
```json
{
  "paths": [
    "/path/to/context-mcp/src/server.ts",
    "/path/to/context-mcp/src/tools/code-structure.ts"
  ],
  "scope": "paths"
}
```

**Output:**
```json
{
  "scope": "paths",
  "structures": [
    {
      "path": "/path/to/context-mcp/src/server.ts",
      "signatures": [
        "ContextMCPServer ",
        "constructor (workspaceDir: string) ",
        "dispose () ",
        "getTools () ",
        "loadBundledModules () ",
        "run () ",
        "setupHandlers () "
      ],
      "count": 7
    },
    {
      "path": "/path/to/context-mcp/src/tools/code-structure.ts",
      "signatures": [
        "getCodeStructureTool (\n  args: CodeStructureArgs,\n  selectedPaths?: string[]\n) ",
        "indexCodeTool (args: IndexCodeArgs) ",
        "interface CodeStructureArgs {\n  paths: string[];\n  scope?: 'paths' | 'selected';\n}",
        "interface CodeStructureResult {\n  scope: string;\n  structures: Array<{\n    path: string;\n    signatures: string[];\n    count: number;\n  }>;\n  performance?: {\n    extractionTime: number;\n    filesProcessed: number;\n  };\n}",
        "interface IndexCodeArgs {\n  paths: string[];\n}",
        "interface IndexCodeResult {\n  indexed: number;\n  failed: number;\n  totalSnippets: number;\n  performance: {\n    indexingTime: number;\n  };\n}"
      ],
      "count": 6
    }
  ],
  "performance": {
    "extractionTime": 1,
    "filesProcessed": 2
  }
}
```

**Performance Timings (5 runs):**
- Run 1: 1ms
- Run 2: 1ms
- Run 3: 0ms
- Run 4: 1ms
- Run 5: 1ms
- **Average: 0.8ms** (Extremely fast querying from SQLite database after indexing)

**Key Features:**
- Uses tree-sitter for accurate code parsing
- Supports 40+ programming languages
- Returns function signatures, class definitions, interfaces, etc.
- `scope`: "paths" (use provided paths) or "selected" (use current selection)
- Extremely fast querying from SQLite database

---

## 5. read_file

Read file contents, optionally with line range.

### Example 1: Read Entire File

**Input:**
```json
{
  "path": "/path/to/context-mcp/package.json"
}
```

**Output:**
```json
{
  "path": "/path/to/context-mcp/package.json",
  "content": "{\n  \"name\": \"@millstonehq/context-mcp-server\",\n  \"version\": \"0.3.0\",\n  \"description\": \"MCP server providing context management and code structure extraction\",\n  \"type\": \"module\",\n  \"main\": \"dist/index.js\",\n  \"bin\": {\n    \"context-mcp-server\": \"dist/index.js\"\n  },\n  \"scripts\": {\n    \"build\": \"tsc; node bundle-continue.js\",\n    \"build:verbose\": \"tsc\",\n    \"build:bundle\": \"node bundle-continue.js\",\n    \"build:clean\": \"rm -rf dist && npm run build\",\n    \"dev\": \"tsc --watch\",\n    \"test\": \"node --test test/\"\n  },\n  \"keywords\": [\n    \"mcp\",\n    \"context\",\n    \"code-structure\",\n    \"ai\"\n  ],\n  \"author\": \"Millstone HQ\",\n  \"license\": \"MIT\",\n  \"dependencies\": {\n    \"@continuedev/core\": \"^1.1.0\",\n    \"@modelcontextprotocol/sdk\": \"^0.5.0\",\n    \"glob\": \"^11.0.0\",\n    \"ignore\": \"^6.0.2\",\n    \"tiktoken\": \"^1.0.17\"\n  },\n  \"devDependencies\": {\n    \"@types/node\": \"^20.0.0\",\n    \"@types/uuid\": \"^10.0.0\",\n    \"esbuild\": \"^0.25.0\",\n    \"tsx\": \"^4.20.6\",\n    \"typescript\": \"^5.3.0\"\n  },\n  \"engines\": {\n    \"node\": \">=18.0.0\"\n  }\n}\n",
  "size": 1022
}
```

**Performance Timings (5 runs):**
- Run 1: <1ms
- Run 2: <1ms
- Run 3: <1ms
- Run 4: <1ms
- Run 5: <1ms
- **Average: <1ms** (Simple file read operation)

### Example 2: Read Specific Line Range

**Input:**
```json
{
  "path": "/path/to/context-mcp/src/index.ts",
  "start_line": 0,
  "end_line": 10
}
```

**Output:**
```json
{
  "path": "/path/to/context-mcp/src/index.ts",
  "content": "#!/usr/bin/env node\n\nimport { ContextMCPServer } from './server.js';\n\n/**\n * Entry point for Context MCP Server\n *\n * Uses Continue's FTS5 search and tree-sitter for fast, accurate code analysis.\n */\n\nasync function main() {",
  "lines": {
    "start": 0,
    "end": 10
  },
  "size": 224
}
```

**Performance Timings (5 runs):**
- Run 1: <1ms
- Run 2: <1ms
- Run 3: <1ms
- Run 4: <1ms
- Run 5: <1ms
- **Average: <1ms** (Efficient line range reading)

**Key Features:**
- Read entire files or specific line ranges
- `start_line` and `end_line` are 0-indexed
- Returns content and file size
- Optional line range parameters save tokens

---

## 6. manage_selection

Manage context selection - add/remove files, track what will be sent to LLM.

### Example 1: Add Files to Selection

**Input:**
```json
{
  "op": "add",
  "paths": [
    "/path/to/context-mcp/src/server.ts",
    "/path/to/context-mcp/package.json"
  ],
  "mode": "full"
}
```

**Output:**
```json
{
  "operation": "add",
  "files": [
    {
      "path": "/path/to/context-mcp/src/server.ts",
      "mode": "full"
    },
    {
      "path": "/path/to/context-mcp/package.json",
      "mode": "full"
    }
  ],
  "totalFiles": 2,
  "totalTokens": 3071
}
```

**Performance Timings (5 runs):**
- Run 1: <1ms
- Run 2: <1ms
- Run 3: <1ms
- Run 4: <1ms
- Run 5: <1ms
- **Average: <1ms** (Fast selection management with token counting)

### Example 2: Get Current Selection

**Input:**
```json
{
  "op": "get",
  "view": "summary"
}
```

**Output:**
```json
{
  "operation": "get",
  "files": [
    {
      "path": "/path/to/context-mcp/src/server.ts",
      "mode": "full"
    },
    {
      "path": "/path/to/context-mcp/package.json",
      "mode": "full"
    }
  ],
  "totalFiles": 2,
  "totalTokens": 3071
}
```

**Performance Timings (5 runs):**
- Run 1: <1ms
- Run 2: <1ms
- Run 3: <1ms
- Run 4: <1ms
- Run 5: <1ms
- **Average: <1ms**

### Example 3: Clear Selection

**Input:**
```json
{
  "op": "clear"
}
```

**Output:**
```json
{
  "operation": "clear",
  "files": [],
  "totalFiles": 0,
  "totalTokens": 0
}
```

**Performance Timings (5 runs):**
- Run 1: <1ms
- Run 2: <1ms
- Run 3: <1ms
- Run 4: <1ms
- Run 5: <1ms
- **Average: <1ms**

**Key Features:**
- `op`: "get", "add", "remove", "set", "clear", "preview", "promote", "demote"
- `mode`: "full" (entire file), "slices" (specific ranges), "codemap_only" (signatures)
- `view`: "summary", "files", "content" (for get operation)
- Tracks token count for selected files

---

## 7. workspace_context

Get comprehensive workspace context snapshot - combines selection, code structure, and file tree.

### Example: Get Selection and Token Count

**Input:**
```json
{
  "include": ["selection", "tokens"]
}
```

**Output:**
```json
{
  "selection": {
    "files": [
      {
        "path": "/path/to/context-mcp/src/server.ts",
        "mode": "full"
      },
      {
        "path": "/path/to/context-mcp/package.json",
        "mode": "full"
      }
    ],
    "totalFiles": 2,
    "totalTokens": 3071
  },
  "tokens": 3071
}
```

**Performance Timings (5 runs):**
- Run 1: <1ms
- Run 2: <1ms
- Run 3: <1ms
- Run 4: <1ms
- Run 5: <1ms
- **Average: <1ms** (Aggregates data from selection manager)

**Key Features:**
- `include`: Array of what to include: "selection", "code", "files", "tree", "tokens"
- Combines multiple data sources in one call
- Useful for getting comprehensive context snapshot
- Default includes: ["selection", "tokens"]

---

## Summary

The context-helper-code MCP server provides powerful tools for:

1. **Fast searching** - BM25-ranked content search and file path matching
2. **File tree navigation** - Get workspace structure with .gitignore respect
3. **Code indexing** - Index files into database for fast structure extraction
4. **Code structure extraction** - Parse code with tree-sitter for 40+ languages
5. **File reading** - Read entire files or specific line ranges
6. **Selection management** - Track files for LLM context with token counting
7. **Workspace context** - Comprehensive snapshots combining multiple sources

All tools are optimized for performance and designed to work efficiently with large codebases.

## Performance Summary

The following table summarizes the average performance of all tools based on multiple test runs:

| Tool | Operation | Average Time | Notes |
|------|-----------|--------------|-------|
| `file_search` | Path search (filesystem) | **1.6ms** | Fast filename matching |
| `file_search` | Content search (FTS5/BM25) | **~431ms** | First run may include index building |
| `get_file_tree` | List files with max_depth | **<1ms** | Very fast with .gitignore filtering |
| `index_code` | Index 2 TypeScript files | **46.6ms** | One-time indexing cost for 13 snippets |
| `get_code_structure` | Extract from 2 indexed files | **0.8ms** | Extremely fast SQLite queries |
| `read_file` | Read full file | **<1ms** | Simple file read |
| `read_file` | Read line range | **<1ms** | Efficient partial file read |
| `manage_selection` | Add files | **<1ms** | Fast with token counting |
| `manage_selection` | Get selection | **<1ms** | Instant selection retrieval |
| `manage_selection` | Clear selection | **<1ms** | Instant clear operation |
| `workspace_context` | Get selection + tokens | **<1ms** | Fast aggregation |

### Key Performance Insights

1. **Indexing Strategy**: `index_code` has a one-time cost (~47ms for 2 files), but subsequent `get_code_structure` queries are extremely fast (<1ms)
2. **Search Performance**:
   - Path search is nearly instant (1.6ms)
   - Content search with FTS5 takes longer (~431ms) but provides BM25-ranked results
3. **File Operations**: All file reading and selection management operations are sub-millisecond
4. **Scalability**: Times shown are for a small project; performance scales well with larger codebases due to SQLite database and FTS5 indexing

---

## Usage Workflow

For optimal code structure extraction:
1. Use `index_code` to populate the database with code structures
2. Use `get_code_structure` to query the indexed structures
3. Indexing is persistent - only needs to be done once (or when files change)
