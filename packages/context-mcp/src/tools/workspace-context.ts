import type { SelectionManager } from '../selection/SelectionManager.js';
import { getFileTreeTool } from './file-tree.js';

export interface WorkspaceContextArgs {
  include?: Array<'selection' | 'code' | 'files' | 'tree' | 'tokens'>;
}

export interface WorkspaceContextResult {
  selection?: {
    files: any[];
    totalFiles: number;
    totalTokens: number;
  };
  code_structures?: any;
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
  const result: WorkspaceContextResult = {};

  try {
    if (include.includes('selection')) {
      result.selection = await manager.getSummary();
    }

    if (include.includes('code')) {
      result.code_structures = {
        note: 'Code structure extraction will be added in V2',
      };
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
