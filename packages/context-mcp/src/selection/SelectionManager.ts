import * as fs from 'fs/promises';
import * as path from 'path';
import { TokenCounter } from '../utils/token-counter.js';

export type SelectionMode = 'full' | 'slices' | 'codemap_only';

export interface Slice {
  startLine: number;
  endLine: number;
  description?: string;
}

export interface SelectedFile {
  path: string;
  mode: SelectionMode;
  slices?: Slice[];
}

export interface SelectionSummary {
  files: SelectedFile[];
  totalFiles: number;
  totalTokens: number;
}

/**
 * Manages which files/slices are currently in context
 */
export class SelectionManager {
  private selection: Map<string, SelectedFile> = new Map();
  private tokenCounter: TokenCounter;

  constructor(private workspaceDir: string) {
    this.tokenCounter = new TokenCounter();
  }

  /**
   * Add file to selection
   */
  async add(path: string, mode: SelectionMode = 'full'): Promise<void> {
    this.selection.set(path, { path, mode });
  }

  /**
   * Add file with specific slices
   * If the file already has slices, new slices are appended
   */
  async addSlices(path: string, slices: Slice[]): Promise<void> {
    const existing = this.selection.get(path);

    if (existing && existing.mode === 'slices' && existing.slices) {
      // Merge new slices with existing ones
      const mergedSlices = [...existing.slices, ...slices];
      this.selection.set(path, { path, mode: 'slices', slices: mergedSlices });
    } else {
      // No existing slices, just set the new ones
      this.selection.set(path, { path, mode: 'slices', slices });
    }
  }

  /**
   * Remove file from selection
   */
  remove(path: string): void {
    this.selection.delete(path);
  }

  /**
   * Remove multiple files from selection
   */
  removeMultiple(paths: string[]): void {
    paths.forEach(path => this.selection.delete(path));
  }

  /**
   * Clear all selections
   */
  clear(): void {
    this.selection.clear();
  }

  /**
   * Replace entire selection
   */
  async set(files: SelectedFile[]): Promise<void> {
    this.selection.clear();
    for (const file of files) {
      this.selection.set(file.path, file);
    }
  }

  /**
   * Check if file is selected
   */
  has(path: string): boolean {
    return this.selection.has(path);
  }

  /**
   * Get selection for a specific file
   */
  get(path: string): SelectedFile | undefined {
    return this.selection.get(path);
  }

  /**
   * Get all selected files
   */
  getAll(): SelectedFile[] {
    return Array.from(this.selection.values());
  }

  /**
   * Get current selection summary
   */
  async getSummary(): Promise<SelectionSummary> {
    const files = this.getAll();
    const content = await this.getContent();
    const totalTokens = this.tokenCounter.count(content);

    return {
      files,
      totalFiles: files.length,
      totalTokens,
    };
  }

  /**
   * Get full content for LLM context
   */
  async getContent(): Promise<string> {
    const parts: string[] = [];

    for (const selected of this.selection.values()) {
      try {
        // Resolve path relative to workspace directory
        const resolvedPath = path.resolve(this.workspaceDir, selected.path);

        switch (selected.mode) {
          case 'full':
            const fullContent = await fs.readFile(resolvedPath, 'utf-8');
            parts.push(`\`\`\`${selected.path}\n${fullContent}\n\`\`\``);
            break;

          case 'slices':
            const fileContent = await fs.readFile(resolvedPath, 'utf-8');
            const lines = fileContent.split('\n');

            for (const slice of selected.slices || []) {
              const sliceLines = lines.slice(slice.startLine, slice.endLine + 1);
              const content = sliceLines.join('\n');
              const desc = slice.description ? ` (${slice.description})` : '';
              parts.push(
                `\`\`\`${selected.path}:${slice.startLine}-${slice.endLine}${desc}\n${content}\n\`\`\``
              );
            }
            break;

          case 'codemap_only':
            // For codemap_only, we'll just show the file path
            // TODO: Add actual code structure extraction in V2
            parts.push(`\`\`\`${selected.path} (structure only)\n// Code structure extraction not yet implemented\n\`\`\``);
            break;
        }
      } catch (error) {
        console.error(`Error reading file ${selected.path}:`, error);
      }
    }

    return parts.join('\n\n');
  }

  /**
   * Preview what would be sent to LLM
   */
  async preview(): Promise<{ content: string; tokens: number }> {
    const content = await this.getContent();
    const tokens = this.tokenCounter.count(content);
    return { content, tokens };
  }

  /**
   * Promote codemap_only to full content
   */
  async promote(path: string): Promise<void> {
    const selected = this.selection.get(path);
    if (selected && selected.mode === 'codemap_only') {
      selected.mode = 'full';
      this.selection.set(path, selected);
    }
  }

  /**
   * Demote full content to codemap_only
   */
  async demote(path: string): Promise<void> {
    const selected = this.selection.get(path);
    if (selected && selected.mode === 'full') {
      selected.mode = 'codemap_only';
      this.selection.set(path, selected);
    }
  }

  /**
   * Clean up resources
   */
  dispose(): void {
    this.tokenCounter.free();
  }
}
