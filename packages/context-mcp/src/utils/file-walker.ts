import * as fs from 'fs/promises';
import * as path from 'path';
import ignore, { Ignore } from 'ignore';

/**
 * Walk directory tree respecting .gitignore
 */
export class FileWalker {
  private ignoreInstance: Ignore;

  constructor(private workspaceDir: string) {
    this.ignoreInstance = ignore();
    this.loadGitignore();
  }

  private async loadGitignore(): Promise<void> {
    try {
      const gitignorePath = path.join(this.workspaceDir, '.gitignore');
      const content = await fs.readFile(gitignorePath, 'utf-8');
      this.ignoreInstance.add(content);
    } catch {
      // No .gitignore file, that's fine
    }

    // Add default ignores
    this.ignoreInstance.add([
      'node_modules',
      '.git',
      '.DS_Store',
      'dist',
      'build',
      '.continue',
      '*.log',
    ]);
  }

  /**
   * Walk directory and return all file paths
   */
  async walk(rootPath?: string): Promise<string[]> {
    const startPath = rootPath || this.workspaceDir;
    const files: string[] = [];

    await this.walkRecursive(startPath, files);

    return files;
  }

  private async walkRecursive(dir: string, files: string[]): Promise<void> {
    try {
      const entries = await fs.readdir(dir, { withFileTypes: true });

      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        const relativePath = path.relative(this.workspaceDir, fullPath);

        // Check if should be ignored
        if (this.ignoreInstance.ignores(relativePath)) {
          continue;
        }

        if (entry.isDirectory()) {
          await this.walkRecursive(fullPath, files);
        } else if (entry.isFile()) {
          files.push(fullPath);
        }
      }
    } catch (error) {
      // Skip directories we can't read
      console.error(`Error reading directory ${dir}:`, error);
    }
  }

  /**
   * Find files matching a pattern
   */
  async find(pattern: string, regex = false): Promise<string[]> {
    const allFiles = await this.walk();

    if (regex) {
      const re = new RegExp(pattern);
      return allFiles.filter(file => re.test(file));
    } else {
      // Simple substring matching
      return allFiles.filter(file =>
        file.toLowerCase().includes(pattern.toLowerCase())
      );
    }
  }
}
