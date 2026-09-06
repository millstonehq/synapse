# Context MCP Server

Lightweight file reading and context selection for MCP clients.

## Available tools

- `get_file_tree`: list files and directories, respecting `.gitignore`.
- `read_file`: read a file or a line range.
- `manage_selection`: select full files or line slices; preview content and token counts.
- `workspace_context`: combine selection, file contents, file tree, and token counts.

## Run

```sh
npm install
npm run build
WORKSPACE_DIR=/absolute/path/to/project node dist/index.js
```

The server uses stdio. `WORKSPACE_DIR` defaults to the current directory.
`WORKSPACE_DIRS` remains accepted for existing configurations; file-tree and
selection operations use its first directory.

```json
{
  "mcpServers": {
    "context": {
      "command": "node",
      "args": ["/absolute/path/to/context-mcp/dist/index.js"],
      "env": {"WORKSPACE_DIR": "/absolute/path/to/project"}
    }
  }
}
```

## Continue removal

The unused Continue integration has been removed. This removes `file_search`,
`semantic_search`, `get_code_structure`, and `index_code`, along with their
SQLite/LanceDB indexes, embedding runtime, worker shims, and bundled Tree-sitter
assets. Selection supports `full` and `slices`; the unimplemented `codemap_only`,
`promote`, `demote`, and workspace `code` options are no longer advertised.

Use your client's file/text search or a separate tool such as Serena for code
navigation. Serena's symbol navigation is not a replacement for embedding-based
prose retrieval. No replacement embedding service is installed by this package.
Existing user caches are left on disk; this server no longer reads or writes them.

## Development

```sh
npm run check:types
npm run build
npm test
```

The build is plain TypeScript and fails on type errors. No bundling or native
indexing dependencies are required. Historical discovery evaluations remain in
`evals/`; their old Continue search scenarios do not describe the current tools.
