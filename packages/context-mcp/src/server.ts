import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import type { Transport } from '@modelcontextprotocol/sdk/shared/transport.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';

import { SelectionManager } from './selection/SelectionManager.js';

// Tools
import { getFileTreeTool } from './tools/file-tree.js';
import { readFileTool } from './tools/read-file.js';
import { manageSelectionTool } from './tools/manage-selection.js';
import { workspaceContextTool } from './tools/workspace-context.js';

/** File reading and context selection, without an indexing runtime. */
export class ContextMCPServer {
  private server: Server;
  private selectionManager: SelectionManager;
  private workspaceDirs: string[];

  constructor(workspaceDirs: string[]) {
    if (workspaceDirs.length === 0) throw new Error('At least one workspace is required');
    this.workspaceDirs = workspaceDirs;

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
          case 'get_file_tree':
            // For now, use first workspace dir (TODO: support multi-root tree)
            result = await getFileTreeTool(args as any, this.workspaceDirs[0]);
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
                tool: name
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
              enum: ['get', 'add', 'remove', 'set', 'clear', 'preview'],
              description: 'Operation: get (current), add (append), remove (delete), set (replace), clear (empty), preview (show content)',
            },
            paths: {
              type: 'array',
              items: { type: 'string' },
              description: 'File paths for operation',
            },
            mode: {
              type: 'string',
              enum: ['full', 'slices'],
              description: 'Selection mode: full (entire file), slices (specific ranges)',
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
        description: 'Get comprehensive workspace context snapshot - combines selection, file contents, token counts, and file tree.',
        inputSchema: {
          type: 'object',
          properties: {
            include: {
              type: 'array',
              items: {
                type: 'string',
                enum: ['selection', 'files', 'tree', 'tokens'],
              },
              description: 'What to include: selection (summary), files (contents), tree (file tree), tokens (count)',
              default: ['selection', 'tokens'],
            },
          },
        },
      },
    ];
  }

  async run(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.connect(transport);
    console.error('Context MCP Server running on stdio');
  }

  async connect(transport: Transport): Promise<void> {
    await this.server.connect(transport);
  }

  dispose(): void {
    this.selectionManager.dispose();
  }
}
