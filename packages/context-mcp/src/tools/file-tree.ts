import { FileWalker } from '../utils/file-walker.js';
import * as path from 'path';

export interface FileTreeArgs {
  type: 'files' | 'roots';
  mode?: 'auto' | 'full' | 'folders';
  path?: string;
  max_depth?: number;
}

export interface FileTreeResult {
  type: string;
  mode?: string;
  roots?: string[];
  files?: string[];
  count?: number;
}

/**
 * Get workspace file tree
 */
export async function getFileTreeTool(
  args: FileTreeArgs,
  workspaceDir: string
): Promise<FileTreeResult> {
  // Return workspace roots
  if (args.type === 'roots') {
    return {
      type: 'roots',
      roots: [workspaceDir],
    };
  }

  // Get files
  try {
    const walker = new FileWalker(workspaceDir);
    const startPath = args.path || workspaceDir;
    const files = await walker.walk(startPath);

    // Filter by depth if specified
    let filteredFiles = files;
    if (args.max_depth !== undefined) {
      filteredFiles = files.filter(file => {
        const relativePath = path.relative(workspaceDir, file);
        const depth = relativePath.split(path.sep).length;
        return depth <= args.max_depth!;
      });
    }

    return {
      type: args.type,
      mode: args.mode,
      files: filteredFiles,
      count: filteredFiles.length,
    };
  } catch (error) {
    console.error('File tree error:', error);
    return {
      type: args.type,
      mode: args.mode,
      files: [],
      count: 0,
    };
  }
}
