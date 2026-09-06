import type { SelectionManager } from '../selection/SelectionManager.js';
import { getFileTreeTool } from './file-tree.js';

export interface WorkspaceContextArgs {
  include?: Array<'selection' | 'files' | 'tree' | 'tokens'>;
}

export interface WorkspaceContextResult {
  selection?: {
    files: any[];
    totalFiles: number;
    totalTokens: number;
  };
  file_contents?: string;
  tree?: any;
  tokens?: number;
}

/**
 * Get comprehensive workspace context snapshot
 */
export async function workspaceContextTool(
  args: WorkspaceContextArgs,
  manager: SelectionManager,
  workspaceDir: string
): Promise<WorkspaceContextResult> {
  const include = args.include || ['selection', 'tokens'];
  if (include.some(item => !['selection', 'files', 'tree', 'tokens'].includes(item))) {
    throw new Error('Unsupported workspace context include option');
  }
  const result: WorkspaceContextResult = {};

  try {
    if (include.includes('selection')) {
      result.selection = await manager.getSummary();
    }

    if (include.includes('files')) {
      result.file_contents = await manager.getContent();
    }

    if (include.includes('tree')) {
      result.tree = await getFileTreeTool(
        {
          type: 'files',
          mode: 'full',
        },
        workspaceDir
      );
    }

    if (include.includes('tokens')) {
      const preview = await manager.preview();
      result.tokens = preview.tokens;
    }
  } catch (error) {
    console.error('Workspace context error:', error);
  }

  return result;
}
