# Language Support

The Context Helper MCP server supports code structure extraction for **24 programming languages** using tree-sitter parsers.

## Supported Languages

The following languages have full support for extracting code structures (functions, classes, methods, etc.):

### Systems Programming
- **C** - Functions, structs, enums, unions
- **C++** - Functions, classes, structs, namespaces
- **Rust** - Functions, structs, enums, traits, impl blocks
- **Zig** - Functions, container declarations
- **Go** - Functions, methods, type definitions

### Object-Oriented Languages
- **Java** - Classes, interfaces, methods, constructors
- **C#** - Classes, interfaces, structs, methods, constructors
- **Kotlin** - Classes, objects, functions, interfaces
- **Swift** - Functions, classes, structs, protocols, enums
- **Scala** - Classes, objects, traits, functions

### Scripting Languages
- **Python** - Functions, classes
- **Ruby** - Methods, classes, modules
- **PHP** - Functions, methods, classes, interfaces, traits
- **Lua** - Function declarations and definitions
- **Bash** - Function definitions

### Functional Languages
- **OCaml** - Value definitions, type definitions, modules
- **Elixir** - Modules, functions, macros (defmodule, def, defp, defmacro)
- **Elm** - Function declarations, type declarations
- **Elisp** - Functions, macros, variables (defun, defmacro, defvar, etc.)

### Web & Modern Languages
- **JavaScript** - Functions, classes, methods
- **TypeScript** - Functions, classes, methods, interfaces, type aliases
- **TSX** - All TypeScript features plus React components
- **Dart** - Classes, mixins, functions, methods
- **ReScript** - Let bindings, type declarations, modules

### Specialized Languages
- **Solidity** - Contracts, interfaces, libraries, functions

## How It Works

### 1. Indexing Phase
Code must first be indexed using the `index_code` tool:

```typescript
{
  "paths": ["/path/to/your/file.py"]
}
```

This parses the files using tree-sitter and stores code snippets in a SQLite database.

### 2. Retrieval Phase
After indexing, use `get_code_structure` to retrieve signatures:

```typescript
{
  "paths": ["/path/to/your/file.py"]
}
```

**Response:**
```json
{
  "scope": "paths",
  "structures": [
    {
      "path": "/path/to/your/file.py",
      "signatures": [
        "MyClass def __init__(self, value): ...",
        "parse (value, *args, **kwargs) ..."
      ],
      "count": 2
    }
  ],
  "performance": {
    "extractionTime": 1,
    "filesProcessed": 1
  }
}
```

## What Gets Extracted

Each language extracts different code structures based on its syntax:

### Common Extractions
- **Function signatures** with parameters and return types
- **Class definitions** with their bodies
- **Method definitions** within classes
- **Interface/Protocol/Trait definitions**
- **Type definitions** (type aliases, structs, etc.)
- **Documentation comments** preceding definitions

### Language-Specific Features

**Python**: Classes and functions with parameters
**Go**: Functions, methods (with receivers), and type specs
**Rust**: Structs, enums, functions, traits, and impl blocks
**Java/C#**: Classes, interfaces, methods, and constructors
**TypeScript**: Interfaces, type aliases, and arrow functions
**Solidity**: Contracts, interfaces, and libraries

## Performance

The tool is optimized for performance:
- Indexing: Processes files in parallel using tree-sitter's fast parser
- Retrieval: Uses SQLite database with indexed queries
- Typical speed: 1-100ms per file depending on size

## Verified Language Tests

### TypeScript ✅
```
7 signatures extracted from server.ts
Including: ContextMCPServer class, constructor, methods
```

### Python ✅
```
227 snippets indexed from flatted.py
Including: _Known, _String classes, parse/stringify functions
```

### Go ✅
```
1 signature extracted from file1.go
Including: getAddress function with receiver
```

### PHP ✅
```
21 snippets indexed from flatted.php
Including: Flatted/FlattedString classes, parse/stringify methods
```

## Adding New Languages

To add support for a new language:

1. Add the tree-sitter WASM parser to `src/tree-sitter/wasms/`
2. Create a query file at `src/tree-sitter/code-snippet-queries/<language>.scm`
3. Define tree-sitter queries matching the language's AST nodes
4. Run `node bundle-continue.js` to bundle the new files
5. Test with sample code files

### Query File Format

Query files use tree-sitter's S-expression format. Example for a simple language:

```scheme
(
  (comment)? @comment
  (function_declaration
    name: (identifier) @name
    parameters: (parameter_list) @parameters
    body: (_) @body
  ) @definition
)
```

## Known Limitations

1. **Two-step process**: Files must be indexed before structure extraction
2. **Database dependency**: Requires SQLite for storing indexed code
3. **Query file required**: Each language needs a custom `.scm` query file
4. **No on-the-fly parsing**: The original `getPathsAndSignatures` queries a database, not live files

## Future Improvements

- [ ] Add support for more languages (Haskell, F#, etc.)
- [ ] Improve signature formatting for better readability
- [ ] Add filtering to reduce duplicate signatures
- [ ] Support incremental indexing for large codebases
- [ ] Add language-specific metadata (visibility modifiers, decorators, etc.)
