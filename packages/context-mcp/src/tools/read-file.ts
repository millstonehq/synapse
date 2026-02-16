import * as fs from 'fs/promises';

export interface ReadFileArgs {
  path: string;
  start_line?: number;
  end_line?: number;
}

export interface ReadFileResult {
  path: string;
  content: string;
  lines?: {
    start: number;
    end: number;
  };
  size: number;
}

/**
 * Read file contents
 */
export async function readFileTool(
  args: ReadFileArgs
): Promise<ReadFileResult> {
  try {
    const fullContent = await fs.readFile(args.path, 'utf-8');

    // Read specific line range if specified
    if (args.start_line !== undefined && args.end_line !== undefined) {
      const lines = fullContent.split('\n');
      const selectedLines = lines.slice(args.start_line, args.end_line + 1);
      const content = selectedLines.join('\n');

      return {
        path: args.path,
        content,
        lines: {
          start: args.start_line,
          end: args.end_line,
        },
        size: content.length,
      };
    } else {
      return {
        path: args.path,
        content: fullContent,
        size: fullContent.length,
      };
    }
  } catch (error) {
    throw new Error(`Failed to read file ${args.path}: ${error}`);
  }
}
