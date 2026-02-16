import type { SelectionManager, SelectionMode, Slice } from '../selection/SelectionManager.js';

export interface ManageSelectionArgs {
  op: 'get' | 'add' | 'remove' | 'set' | 'clear' | 'preview' | 'promote' | 'demote';
  paths?: string[];
  mode?: SelectionMode;
  slices?: Array<{
    path: string;
    ranges: Slice[];
  }>;
  view?: 'summary' | 'files' | 'content';
}

export interface ManageSelectionResult {
  operation: string;
  files?: Array<{
    path: string;
    mode: SelectionMode;
    slices?: Slice[];
  }>;
  totalFiles?: number;
  totalTokens?: number;
  content?: string;
  error?: string;
}

/**
 * Manage file selection (add/remove/get/clear)
 */
export async function manageSelectionTool(
  args: ManageSelectionArgs,
  manager: SelectionManager
): Promise<ManageSelectionResult> {
  // Validate operation
  const validOps = ['get', 'add', 'remove', 'set', 'clear', 'preview', 'promote', 'demote'];
  if (!validOps.includes(args.op)) {
    return {
      operation: args.op,
      error: `Invalid operation '${args.op}'. Valid operations: ${validOps.join(', ')}`,
    };
  }

  // Validate that at least one of paths or slices is provided for operations that need them
  if (['add', 'remove', 'set', 'promote', 'demote'].includes(args.op)) {
    if (!args.paths && !args.slices) {
      return {
        operation: args.op,
        error: `Operation '${args.op}' requires either 'paths' or 'slices' parameter`,
      };
    }
  }

  switch (args.op) {
    case 'add':
      // Handle adding full files
      for (const path of args.paths || []) {
        await manager.add(path, args.mode || 'full');
      }

      // Handle adding slices
      if (args.slices) {
        for (const slice of args.slices) {
          await manager.addSlices(slice.path, slice.ranges);
        }
      }
      break;

    case 'remove':
      if (args.paths) {
        manager.removeMultiple(args.paths);
      }
      break;

    case 'set':
      const filesToSet: Array<{ path: string; mode: SelectionMode; slices?: Slice[] }> =
        args.paths?.map(path => ({
          path,
          mode: args.mode || 'full' as SelectionMode,
        })) || [];

      if (args.slices) {
        for (const slice of args.slices) {
          filesToSet.push({
            path: slice.path,
            mode: 'slices' as SelectionMode,
            slices: slice.ranges,
          });
        }
      }

      await manager.set(filesToSet as any);
      break;

    case 'clear':
      manager.clear();
      break;

    case 'preview':
      const preview = await manager.preview();
      return {
        operation: 'preview',
        content: preview.content,
        totalTokens: preview.tokens,
      };

    case 'promote':
      for (const path of args.paths || []) {
        await manager.promote(path);
      }
      break;

    case 'demote':
      for (const path of args.paths || []) {
        await manager.demote(path);
      }
      break;

    case 'get':
    default:
      const summary = await manager.getSummary();

      const result: ManageSelectionResult = {
        operation: 'get',
        files: summary.files,
        totalFiles: summary.totalFiles,
        totalTokens: summary.totalTokens,
      };

      if (args.view === 'content') {
        result.content = await manager.getContent();
      }

      return result;
  }

  const summary = await manager.getSummary();
  return {
    operation: args.op,
    files: summary.files,
    totalFiles: summary.totalFiles,
    totalTokens: summary.totalTokens,
  };
}
