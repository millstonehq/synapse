# Testing Guide

## Running Automated Tests

```bash
npm run test
```

**Expected output:** All 6 tests should pass ✅

```
ℹ tests 6
ℹ pass 6
ℹ fail 0
```

## Test Suite (v0.3.0)

We have 6 automated tests that verify all functionality:

1. **test-simple.js** - V1 core functionality
2. **test-bundled.js** - Bundled Continue FTS5 search
3. **test-bundled-structure.js** - Bundled tree-sitter extraction
4. **test-hybrid-v2.js** - V2 architecture with shims
5. **test-server-v2-integration.js** - V2 server initialization
6. **test-v2-bundled.js** - Complete V2 end-to-end test

All tests verify:
- ✅ File tree navigation
- ✅ File search (FTS5 + BM25 ranking)
- ✅ Tree-sitter code structure extraction
- ✅ File reading
- ✅ Selection management (add, get, preview, clear)
- ✅ Token counting
- ✅ Workspace context
- ✅ Continue IDE/LLM shims
- ✅ Bundled module loading

## Testing with Claude Desktop

### Step 1: Configure Claude Desktop

Edit your Claude Desktop config file:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Add this configuration:

```json
{
  "mcpServers": {
    "context": {
      "command": "node",
      "args": [
        "/path/to/context-mcp-server/dist/index.js"
      ],
      "env": {
        "WORKSPACE_DIR": "/path/to/context-mcp-server"
      }
    }
  }
}
```

**Important:**
- Replace the workspace directory with the actual project you want to analyze
- Paths must be absolute (no `~` or relative paths)

### Step 2: Restart Claude Desktop

Completely quit and reopen Claude Desktop (not just close the window).

### Step 3: Verify Connection

In Claude Desktop, type:
```
Can you list the available MCP tools?
```

You should see 6 tools:
1. `file_search`
2. `get_file_tree`
3. `get_code_structure`
4. `read_file`
5. `manage_selection`
6. `workspace_context`

### Step 4: Test Basic Workflow

Try this conversation with Claude:

```
Let's test the context MCP server:

1. First, search for TypeScript files in the workspace
2. Add README.md and package.json to the selection
3. Show me the selection summary with token count
4. Preview what would be sent to you
```

Claude should be able to:
- ✅ Search files using `file_search`
- ✅ Add them to selection using `manage_selection`
- ✅ Show token counts
- ✅ Preview the content

### Step 5: Advanced Testing

Test more complex scenarios:

**Scenario 1: Code Search**
```
Search for all files containing "SelectionManager" and add the relevant ones to context
```

**Scenario 2: Selective Context**
```
I want to understand the file search implementation. Add only the file-search.ts file
to context, then tell me how it works.
```

**Scenario 3: Token Management**
```
Add all TypeScript files to the selection, then show me the total token count.
If it's over 10000 tokens, remove some files to get under that limit.
```

## Troubleshooting

### Issue: "MCP server not found"

**Solution:**
1. Check that `dist/index.js` exists:
   ```bash
   ls -la /path/to/context-mcp-server/dist/index.js
   ```
2. Verify the path in config is absolute
3. Restart Claude Desktop completely

### Issue: "Permission denied"

**Solution:**
```bash
chmod +x /path/to/context-mcp-server/dist/index.js
```

### Issue: Tools not appearing

**Solution:**
1. Check Claude Desktop logs:
   - macOS: `~/Library/Logs/Claude/mcp*.log`
2. Verify JSON config is valid (use https://jsonlint.com)
3. Check for trailing commas in JSON

### Issue: "Module not found"

**Solution:**
```bash
cd /path/to/context-mcp-server
npm install
npm run build
```

## Manual Testing

You can also run the test suite manually:

```bash
# Run local tests
node test-simple.js

# Test the server process directly
WORKSPACE_DIR=/path/to/your/project node dist/index.js
# (Server will wait for stdio input - use Ctrl+C to exit)
```

## Expected Behavior

### File Search
- Path search should respect `.gitignore`
- Content search should find text within files
- Results should be limited to `max_results`

### Selection Management
- Can add/remove multiple files
- Token counts should be accurate (using GPT-4 tokenizer)
- Preview should show actual content that would be sent

### Performance
- Path search on 1000 files: < 500ms
- Content search on 1000 files: ~2s (grep-based)
- Token counting: ~100ms per file

## Next Steps

Once testing with Claude Desktop is successful:
1. ✅ V1 is working!
2. 📝 Document any issues or desired features
3. 🚀 Move to V2 for Continue integration

## Test Results

Fill in your results:

- [ ] Claude Desktop config updated
- [ ] Server appears in Claude Desktop
- [ ] All 6 tools are available
- [ ] `file_search` works
- [ ] `manage_selection` works
- [ ] Token counting is accurate
- [ ] No errors in logs

## Example Use Cases

### Use Case 1: Understanding a Feature

```
User: I want to understand how the selection management works

Claude should:
1. Use file_search to find SelectionManager files
2. Use manage_selection to add them to context
3. Use read_file to read the implementation
4. Explain how it works
```

### Use Case 2: Code Review

```
User: Review the file-search.ts implementation

Claude should:
1. Add file-search.ts to selection
2. Read the file
3. Analyze the code
4. Provide feedback
```

### Use Case 3: Multi-file Context

```
User: I need context on the MCP server implementation

Claude should:
1. Search for server-related files
2. Add server.ts, tools/*.ts to selection
3. Show token count
4. Summarize the architecture
```

## Logs

Check logs for debugging:

```bash
# macOS
tail -f ~/Library/Logs/Claude/mcp*.log

# Or run server manually to see stderr
WORKSPACE_DIR=/path/to/project node dist/index.js
```

## Success Criteria

V1 testing is successful if:
- ✅ Server starts without errors
- ✅ All tools are accessible in Claude Desktop
- ✅ File search finds files correctly
- ✅ Selection management tracks files and counts tokens
- ✅ No crashes or errors during normal usage
- ✅ Token counts are within 10% of actual (GPT-4 tokenizer)

Ready to move to V2 when all criteria are met!
