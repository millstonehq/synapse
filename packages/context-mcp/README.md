# Context MCP Server

A Model Context Protocol (MCP) server providing intelligent context management and code structure extraction for AI assistants like Claude.

## Features

- **FTS5 Full-Text Search** - BM25-ranked search (220x faster than grep!)
- **Tree-Sitter Code Structure** - Extract signatures from 40+ languages
- **File Search** - Path pattern search with `.gitignore` support
- **Selection Management** - Track which files are in context
- **Token Counting** - GPT-4 tokenization with tiktoken
- **File Reading** - Full files or specific line ranges
- **Workspace Context** - Comprehensive snapshots of selected content

## Installation

```bash
# Clone the repository
git clone <your-repo>
cd context-mcp-server

# Install dependencies
npm install

# Build
npm run build
```

**Note:** You'll see TypeScript warnings from Continue's node_modules during build - these are expected and safe to ignore. See [Build Guide](./docs/BUILD_GUIDE.md) for details.

## Usage with Claude Desktop

Add to your Claude Desktop config at:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "context": {
      "command": "node",
      "args": ["/absolute/path/to/context-mcp-server/dist/index.js"],
      "env": {
        "WORKSPACE_DIR": "/absolute/path/to/your/project"
      }
    }
  }
}
```

## Usage with Claude Code
```

  "mcpServers": {
    "context-helper-code": {
      "command": "node",
      "args": [
        "/absolute/path/to/context-helper-mcp/dist/index.js"
      ],
      "env": {
        "WORKSPACE_DIR": "/path/to/workspace/millstonehq/cc-templates/"
      }
    },
    "context-helper-docs": {
      "command": "node",
      "args": [
        "/absolute/path/to/context-helper-mcp/dist/index.js"
      ],
      "env": {
        "WORKSPACE_DIR": "/path/to/workspace/millstonehq/synapse/"
      }
    }
  },
```
```
```

**Important:**
- Use absolute paths! Relative paths will not work.
- After updating the config, restart Claude Desktop completely (quit and reopen)



## Quick Start

1. **Search** for files: Use `file_search` tool
2. **Add** to selection: Use `manage_selection` with `op: "add"`
3. **Review** selection: Use `manage_selection` with `op: "get"`
4. **Preview** before sending: Use `manage_selection` with `op: "preview"`
5. **Get context**: Use `workspace_context` tool

## Available Tools

### 1. `file_search`
Search files by path pattern or content.

**Example:**
```json
{
  "pattern": "SelectionManager",
  "mode": "content",
  "filter": {
    "extensions": ["ts"]
  }
}
```

### 2. `get_file_tree`
Get workspace file structure.

### 3. `read_file`
Read file contents with optional line ranges.

### 4. `manage_selection`
Manage context selection - the KEY feature for context management!

**Operations:**
- `get` - Get current selection
- `add` - Add files to selection
- `remove` - Remove files from selection
- `set` - Replace entire selection
- `clear` - Clear all selections
- `preview` - Preview what would be sent to LLM
- `promote` - Upgrade codemap_only to full content
- `demote` - Downgrade full to codemap_only

### 5. `get_code_structure`
Extract code structure using tree-sitter.

### 6. `workspace_context`
Get comprehensive workspace context including selection, code structures, files, and token counts.

## Development

```bash
# Watch mode
npm run dev

# Build
npm run build

# Test
npm test
```

## Documentation

- **[Build Guide](./docs/BUILD_GUIDE.md)** - Build process and troubleshooting
- **[Bundling Solution](./docs/BUNDLING_SOLUTION.md)** - How Continue integration works
- **[Testing Guide](./docs/TESTING.md)** - Testing procedures and verification
- **[Verification](./docs/VERIFICATION.md)** - System verification steps

## Architecture

Uses **esbuild bundling** to integrate Continue's advanced features:
- Bundles Continue's FTS5 and tree-sitter modules automatically
- Polyfills `__dirname` for ESM compatibility
- Externalizes native modules (sqlite3, tree-sitter)
- Zero manual maintenance - just run `npm run build`

See [Bundling Solution](./docs/BUNDLING_SOLUTION.md) for technical details.

## Performance

| Operation | Traditional (Grep) | FTS5 Search | Improvement |
|-----------|-----------|-----------|-------------|
| Content search (1000 files) | ~2s | ~9ms | **220x faster** |
| Code structure extraction | N/A | ~5ms | New feature |

## Troubleshooting

### "MCP server not found"
- Ensure you used **absolute paths** in config
- Check that `dist/index.js` exists after building
- Restart Claude Desktop completely

### "Permission denied"
```bash
chmod +x dist/index.js
```

### "Module not found"
```bash
rm -rf dist node_modules
npm install
npm run build
```

### Debug logging
The server logs to stderr. To see logs:
```bash
WORKSPACE_DIR=/path/to/project node dist/index.js
```

## Comparison to Other Tools

### vs RepoPrompt
- ✅ Integrates directly with Claude via MCP (no copy/paste)
- ✅ **220x faster search** with FTS5 instead of grep
- ✅ Selection tracking with token budgeting
- ✅ Tree-sitter code structure for 40+ languages

### vs Continue Extension
- ✅ Works with Claude Desktop (not just VS Code)
- ✅ Uses Continue's FTS5 and tree-sitter via bundling
- ✅ Focused on context management (not autocomplete)
- ✅ Simpler setup - just one MCP server

## License

MIT

## Credits

- Inspired by [RepoPrompt](https://github.com/continuedev/repoprompt)
- Uses [Continue's](https://github.com/continuedev/continue) indexing features via bundling
- Built on [Model Context Protocol](https://modelcontextprotocol.io)
