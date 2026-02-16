import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';

import { ContinueIDE } from './continue/ContinueIDE.js';
import { SelectionManager } from './selection/SelectionManager.js';

// Tools
import { getFileTreeTool } from './tools/file-tree.js';
import { readFileTool } from './tools/read-file.js';
import { manageSelectionTool } from './tools/manage-selection.js';
import { workspaceContextTool } from './tools/workspace-context.js';

// Dynamic imports for bundled modules (loaded at runtime)
let fileSearchTool: any;
let getCodeStructureTool: any;
let indexCodeTool: any;
let semanticSearchTool: any;

/**
 * Context MCP Server (Full Continue Integration)
 *
 * Uses bundled Continue modules for:
 * - FTS5 full-text search with BM25 ranking (220x faster than grep)
 * - Tree-sitter code structure extraction (40+ languages)
 * - Continue-compatible IDE/LLM shims
 *
 * Supports multiple workspace directories for cross-repository indexing.
 *
 * Bundling solves ESM import issues in @continuedev/core package.
 * See docs/BUNDLING_SOLUTION.md for details.
 */
export class ContextMCPServer {
  private server: Server;
  private ide: ContinueIDE;
  private selectionManager: SelectionManager;
  private workspaceDirs: string[];
  private bundledModulesLoaded: boolean = false;
  private bundledModulesPromise: Promise<void>;

  constructor(workspaceDirs: string[]) {
    this.workspaceDirs = workspaceDirs;

    // Initialize Continue IDE shim (provides file operations for indexing)
    this.ide = new ContinueIDE(workspaceDirs[0]);

    // Start loading bundled modules (async)
    this.bundledModulesPromise = this.loadBundledModules();

    // Initialize selection manager (uses first workspace as primary)
    this.selectionManager = new SelectionManager(workspaceDirs[0]);

    // Initialize MCP server
    this.server = new Server(
      {
        name: 'context-mcp-server',
        version: '0.2.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupHandlers();
  }

  private async loadBundledModules(): Promise<void> {
    // Dynamically import bundled Continue modules at runtime
    // These are in dist/bundled/ after build (not available during TS compilation)
    // Use import.meta.url to resolve relative to this script, not cwd
    const bundledDir = new URL('./bundled/', import.meta.url).href;
    const loadedModules: string[] = [];
    const failedModules: string[] = [];

    // Load each module independently so failures don't block others
    // file-search.js is fully bundled and should always work
    try {
      const fileSearchModule = await import(new URL('file-search.js', bundledDir).href);
      fileSearchTool = fileSearchModule.fileSearchTool;
      loadedModules.push('file-search');
    } catch (error) {
      console.error('⚠️ Failed to load file-search module:', error instanceof Error ? error.message : error);
      failedModules.push('file-search');
    }

    // code-structure.js is fully bundled and should work
    try {
      const codeStructureModule = await import(new URL('code-structure.js', bundledDir).href);
      getCodeStructureTool = codeStructureModule.getCodeStructureTool;
      indexCodeTool = codeStructureModule.indexCodeTool;
      loadedModules.push('code-structure');
    } catch (error) {
      console.error('⚠️ Failed to load code-structure module:', error instanceof Error ? error.message : error);
      failedModules.push('code-structure');
    }

    // semantic-search.js imports from embeddings which has @continuedev/core ESM issues
    // This may fail on some platforms but shouldn't block file_search
    try {
      const semanticSearchModule = await import(new URL('semantic-search.js', bundledDir).href);
      semanticSearchTool = semanticSearchModule.semanticSearchTool;
      loadedModules.push('semantic-search');
    } catch (error) {
      console.error('⚠️ Failed to load semantic-search module (embeddings unavailable):', error instanceof Error ? error.message : error);
      failedModules.push('semantic-search');
    }

    // Mark as loaded if at least file-search works (core functionality)
    this.bundledModulesLoaded = loadedModules.includes('file-search');

    if (loadedModules.length > 0) {
      console.error(`✅ Loaded bundled modules: ${loadedModules.join(', ')}`);
    }
    if (failedModules.length > 0) {
      console.error(`⚠️ Unavailable modules: ${failedModules.join(', ')}`);
    }
  }

  private setupHandlers(): void {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: this.getTools(),
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        let result: any;

        switch (name) {
          case 'file_search':
            if (this.bundledModulesLoaded && fileSearchTool) {
              // Use bundled Continue FTS5 search across all workspace directories
              result = await fileSearchTool(args as any, this.workspaceDirs, this.ide);
            } else {
              throw new Error('File search requires bundled Continue modules');
            }
            break;

          case 'semantic_search':
            if (this.bundledModulesLoaded && semanticSearchTool) {
              // Use hybrid semantic + lexical search across all workspace directories
              result = await semanticSearchTool(args as any, this.workspaceDirs, this.ide);
            } else {
              throw new Error('Semantic search requires bundled Continue modules');
            }
            break;

          case 'get_file_tree':
            // For now, use first workspace dir (TODO: support multi-root tree)
            result = await getFileTreeTool(args as any, this.workspaceDirs[0]);
            break;

          case 'get_code_structure':
            const selectedPaths = this.selectionManager.getAll().map(f => f.path);
            if (this.bundledModulesLoaded && getCodeStructureTool) {
              // Use bundled Continue tree-sitter extraction
              result = await getCodeStructureTool(args as any, selectedPaths);
            } else {
              throw new Error('Code structure requires bundled Continue modules');
            }
            break;

          case 'index_code':
            if (this.bundledModulesLoaded && indexCodeTool) {
              // Index files into database for code structure extraction
              result = await indexCodeTool(args as any);
            } else {
              throw new Error('Code indexing requires bundled Continue modules');
            }
            break;

          case 'read_file':
            result = await readFileTool(args as any);
            break;

          case 'manage_selection':
            result = await manageSelectionTool(args as any, this.selectionManager);
            break;

          case 'workspace_context':
            result = await workspaceContextTool(
              args as any,
              this.selectionManager,
              this.workspaceDirs[0] // TODO: support multi-root workspace context
            );
            break;

          default:
            throw new Error(`Unknown tool: ${name}`);
        }

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.error(`Tool ${name} error:`, error);

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                error: errorMessage,
                tool: name,
                note: 'Feature may require indexing or specific file types'
              }, null, 2),
            },
          ],
          isError: true,
        };
      }
    });
  }

  private getTools(): Tool[] {
    return [
      {
        name: 'file_search',
        description: 'Search files with FTS5 + BM25 ranking for content, fast file system search for paths. 10-100x faster than grep on large codebases.',
        inputSchema: {
          type: 'object',
          properties: {
            pattern: {
              type: 'string',
              description: 'Search pattern (path substring or content query)',
            },
            mode: {
              type: 'string',
              enum: ['auto', 'path', 'content', 'both'],
              description: 'Search mode: auto (smart), path (filenames), content (file contents with BM25 ranking), both',
              default: 'auto',
            },
            regex: {
              type: 'boolean',
              description: 'Treat pattern as regex (for path mode)',
              default: false,
            },
            filter: {
              type: 'object',
              properties: {
                extensions: {
                  type: 'array',
                  items: { type: 'string' },
                  description: 'Filter by file extensions (e.g., ["ts", "js"])',
                },
                exclude: {
                  type: 'array',
                  items: { type: 'string' },
                  description: 'Exclude paths containing these strings',
                },
              },
            },
            max_results: {
              type: 'number',
              description: 'Maximum number of results to return',
              default: 50,
            },
            include_content: {
              type: 'boolean',
              description: 'Include matched content in results. Default false to save tokens - set true when content preview is needed.',
              default: false,
            },
          },
          required: ['pattern'],
        },
      },
      {
        name: 'semantic_search',
        description: 'Hybrid semantic + lexical search using embeddings (all-MiniLM-L6-v2) and FTS5. Best for natural language queries and finding conceptually related code. Uses Reciprocal Rank Fusion to combine results.',
        inputSchema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: 'Natural language search query (e.g., "function that handles user authentication")',
            },
            mode: {
              type: 'string',
              enum: ['hybrid', 'semantic', 'lexical'],
              description: 'Search mode: hybrid (combines both, recommended), semantic (embeddings only), lexical (FTS5 only)',
              default: 'hybrid',
            },
            filter: {
              type: 'object',
              properties: {
                extensions: {
                  type: 'array',
                  items: { type: 'string' },
                  description: 'Filter by file extensions (e.g., ["ts", "js"])',
                },
                exclude: {
                  type: 'array',
                  items: { type: 'string' },
                  description: 'Exclude paths containing these strings',
                },
              },
            },
            max_results: {
              type: 'number',
              description: 'Maximum number of results to return',
              default: 30,
            },
            include_content: {
              type: 'boolean',
              description: 'Include matched content in results',
              default: false,
            },
            semantic_weight: {
              type: 'number',
              description: 'Weight for semantic results in hybrid mode (0.0-1.0, default 0.5). Higher values favor semantic similarity over lexical matching.',
              default: 0.5,
            },
          },
          required: ['query'],
        },
      },
      {
        name: 'get_file_tree',
        description: 'Get workspace file tree structure. Respects .gitignore automatically.',
        inputSchema: {
          type: 'object',
          properties: {
            type: {
              type: 'string',
              enum: ['files', 'roots'],
              description: 'Type of tree to return: files (full tree) or roots (workspace roots)',
            },
            mode: {
              type: 'string',
              enum: ['auto', 'full', 'folders'],
              description: 'Tree mode: full (all files), folders (directories only)',
              default: 'full',
            },
            path: {
              type: 'string',
              description: 'Specific path to get tree for (optional, defaults to workspace root)',
            },
            max_depth: {
              type: 'number',
              description: 'Maximum depth to traverse',
            },
          },
          required: ['type'],
        },
      },
      {
        name: 'get_code_structure',
        description: 'Extract code structure using tree-sitter. Returns function signatures, class definitions, etc. Supports 40+ languages.',
        inputSchema: {
          type: 'object',
          properties: {
            paths: {
              type: 'array',
              items: { type: 'string' },
              description: 'File paths to analyze',
            },
            scope: {
              type: 'string',
              enum: ['paths', 'selected'],
              description: 'Use specified paths or current selection',
              default: 'paths',
            },
          },
          required: ['paths'],
        },
      },
      {
        name: 'read_file',
        description: 'Read file contents, optionally with line range.',
        inputSchema: {
          type: 'object',
          properties: {
            path: {
              type: 'string',
              description: 'File path to read',
            },
            start_line: {
              type: 'number',
              description: 'Start line (0-indexed, optional)',
            },
            end_line: {
              type: 'number',
              description: 'End line (0-indexed, optional)',
            },
          },
          required: ['path'],
        },
      },
      {
        name: 'manage_selection',
        description: 'Manage context selection - add/remove files, track what will be sent to LLM.',
        inputSchema: {
          type: 'object',
          properties: {
            op: {
              type: 'string',
              enum: ['get', 'add', 'remove', 'set', 'clear', 'preview', 'promote', 'demote'],
              description: 'Operation: get (current), add (append), remove (delete), set (replace), clear (empty), preview (show content), promote (codemap->full), demote (full->codemap)',
            },
            paths: {
              type: 'array',
              items: { type: 'string' },
              description: 'File paths for operation',
            },
            mode: {
              type: 'string',
              enum: ['full', 'slices', 'codemap_only'],
              description: 'Selection mode: full (entire file), slices (specific ranges), codemap_only (tree-sitter signatures)',
              default: 'full',
            },
            slices: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  path: { type: 'string' },
                  ranges: {
                    type: 'array',
                    items: {
                      type: 'object',
                      properties: {
                        startLine: { type: 'number' },
                        endLine: { type: 'number' },
                        description: { type: 'string' },
                      },
                      required: ['startLine', 'endLine'],
                    },
                  },
                },
                required: ['path', 'ranges'],
              },
              description: 'Specific slices to add (for slices mode)',
            },
            view: {
              type: 'string',
              enum: ['summary', 'files', 'content'],
              description: 'View mode for get operation',
              default: 'summary',
            },
          },
          required: ['op'],
        },
      },
      {
        name: 'workspace_context',
        description: 'Get comprehensive workspace context snapshot - combines selection, code structure, and file tree.',
        inputSchema: {
          type: 'object',
          properties: {
            include: {
              type: 'array',
              items: {
                type: 'string',
                enum: ['selection', 'code', 'files', 'tree', 'tokens'],
              },
              description: 'What to include: selection (summary), code (tree-sitter structures), files (contents), tree (file tree), tokens (count)',
              default: ['selection', 'tokens'],
            },
          },
        },
      },
      {
        name: 'index_code',
        description: 'Index code files into database for structure extraction. Must be called before get_code_structure to populate the database.',
        inputSchema: {
          type: 'object',
          properties: {
            paths: {
              type: 'array',
              items: { type: 'string' },
              description: 'File paths to index',
            },
          },
          required: ['paths'],
        },
      },
    ];
  }

  async run(): Promise<void> {
    // Wait for bundled modules to load
    await this.bundledModulesPromise;

    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Context MCP Server running on stdio');
    if (this.bundledModulesLoaded) {
      console.error('✅ Continue FTS5 + tree-sitter loaded via bundling');
      console.error('   Performance: ~220x faster search, 40+ languages supported');
    } else {
      console.error('⚠️ Bundled modules not available');
    }
    console.error('See docs/BUNDLING_SOLUTION.md for details');
  }

  dispose(): void {
    this.selectionManager.dispose();
  }
}
