import * as fs from 'fs/promises';
import * as path from 'path';
import { spawn } from 'child_process';
import type { IDE, IdeInfo, IdeSettings, FileType, ToastType } from '@continuedev/core';

/**
 * Minimal IDE implementation for Continue's indexing
 * Only implements methods actually used by FullTextSearchCodebaseIndex and CodeSnippetsCodebaseIndex
 */
export class ContinueIDE implements IDE {
  constructor(private workspaceDir: string) {}

  // === Core file system methods (REQUIRED) ===

  async getWorkspaceDirs(): Promise<string[]> {
    return [this.workspaceDir];
  }

  async readFile(filepath: string): Promise<string> {
    const fullPath = this.resolveWorkspacePath(filepath);
    return await fs.readFile(fullPath, 'utf-8');
  }

  async fileExists(filepath: string): Promise<boolean> {
    try {
      const fullPath = this.resolveWorkspacePath(filepath);
      await fs.access(fullPath);
      return true;
    } catch {
      return false;
    }
  }

  async listDir(dir: string): Promise<[string, FileType][]> {
    const fullPath = this.resolveWorkspacePath(dir);
    const entries = await fs.readdir(fullPath, { withFileTypes: true });

    return entries.map(entry => {
      const entryPath = path.join(dir, entry.name);
      let type: FileType;

      if (entry.isDirectory()) {
        type = 2 as FileType; // FileType.Directory
      } else if (entry.isSymbolicLink()) {
        type = 64 as FileType; // FileType.SymbolicLink
      } else {
        type = 1 as FileType; // FileType.File
      }

      return [entryPath, type];
    });
  }

  async readRangeInFile(filepath: string, range: { start: { line: number; character: number }; end: { line: number; character: number } }): Promise<string> {
    const content = await this.readFile(filepath);
    const lines = content.split('\n');
    const selectedLines = lines.slice(range.start.line, range.end.line + 1);

    if (selectedLines.length === 0) return '';

    if (selectedLines.length === 1) {
      return selectedLines[0].slice(range.start.character, range.end.character);
    }

    selectedLines[0] = selectedLines[0].slice(range.start.character);
    selectedLines[selectedLines.length - 1] = selectedLines[selectedLines.length - 1].slice(0, range.end.character);

    return selectedLines.join('\n');
  }

  // === Git methods (used by indexing) ===

  async getBranch(dir: string): Promise<string> {
    try {
      const gitDir = await this.getGitRootPath(dir);
      if (!gitDir) return 'main';

      const headPath = path.join(gitDir, '.git', 'HEAD');
      const head = await fs.readFile(headPath, 'utf-8');

      if (head.startsWith('ref: refs/heads/')) {
        return head.slice('ref: refs/heads/'.length).trim();
      }

      return 'main';
    } catch {
      return 'main';
    }
  }

  async getGitRootPath(dir: string): Promise<string | undefined> {
    let currentDir = this.resolveWorkspacePath(dir);

    while (currentDir !== path.parse(currentDir).root) {
      try {
        await fs.access(path.join(currentDir, '.git'));
        return currentDir;
      } catch {
        currentDir = path.dirname(currentDir);
      }
    }

    return undefined;
  }

  async getRepoName(dir: string): Promise<string | undefined> {
    return path.basename(this.workspaceDir);
  }

  // === Metadata methods ===

  async getIdeInfo(): Promise<IdeInfo> {
    return {
      ideType: 'vscode', // Required enum value
      name: 'Context MCP Server',
      version: '0.2.0',
      remoteName: 'local',
      extensionVersion: '0.2.0',
    };
  }

  async getIdeSettings(): Promise<IdeSettings> {
    return {
      remoteConfigServerUrl: undefined,
      remoteConfigSyncPeriod: 60,
      userToken: '',
      enableControlServerBeta: false,
      pauseCodebaseIndexOnStart: false,
      continueTestEnvironment: 'none' as any,
    };
  }

  async getFileStats(files: string[]): Promise<any> {
    const result: Record<string, any> = {};
    for (const file of files) {
      try {
        const fullPath = this.resolveWorkspacePath(file);
        const stats = await fs.stat(fullPath);
        result[file] = {
          size: stats.size,
          lastModified: stats.mtimeMs,
        };
      } catch {
        // Skip files that don't exist
      }
    }
    return result;
  }

  async readSecrets(): Promise<Record<string, string>> {
    return {};
  }

  async writeSecrets(_secrets: Record<string, string>): Promise<void> {}

  async getLastModified(files: string[]): Promise<{ [path: string]: number }> {
    const result: { [path: string]: number } = {};

    for (const file of files) {
      try {
        const fullPath = this.resolveWorkspacePath(file);
        const stats = await fs.stat(fullPath);
        result[file] = stats.mtimeMs;
      } catch {
        // Skip files that don't exist
      }
    }

    return result;
  }

  // === Helper methods ===

  private resolveWorkspacePath(filepath: string): string {
    if (path.isAbsolute(filepath)) {
      return filepath;
    }
    return path.join(this.workspaceDir, filepath);
  }

  // === Stub methods (not used by indexing, but required by interface) ===

  async writeFile(filepath: string, contents: string): Promise<void> {
    const fullPath = this.resolveWorkspacePath(filepath);
    await fs.mkdir(path.dirname(fullPath), { recursive: true });
    await fs.writeFile(fullPath, contents, 'utf-8');
  }

  async showVirtualFile(_title: string, _contents: string): Promise<void> {}
  async openFile(_path: string): Promise<void> {}
  async openUrl(_url: string): Promise<void> {}
  async runCommand(_command: string): Promise<void> {}
  async saveFile(_filepath: string): Promise<void> {}
  async showLines(_filepath: string, _startLine: number, _endLine: number): Promise<void> {}

  async getDiff(_includeUnstaged: boolean): Promise<string[]> {
    return [];
  }

  async getClipboardContent(): Promise<{ text: string; copiedAt: string }> {
    return { text: '', copiedAt: new Date().toISOString() };
  }

  async isTelemetryEnabled(): Promise<boolean> {
    return false;
  }

  async getUniqueId(): Promise<string> {
    return 'context-mcp-server';
  }

  async getTerminalContents(): Promise<string> {
    return '';
  }

  async getDebugLocals(_threadIndex: number): Promise<string> {
    return '';
  }

  async getTopLevelCallStackSources(_threadIndex: number, _stackDepth: number): Promise<string[]> {
    return [];
  }

  async getAvailableThreads(): Promise<any[]> {
    return [];
  }

  async getWorkspaceConfigs(): Promise<any[]> {
    return [];
  }

  async getOpenFiles(): Promise<string[]> {
    return [];
  }

  async getCurrentFile(): Promise<{ isUntitled: boolean; path: string; contents: string } | undefined> {
    return undefined;
  }

  async getPinnedFiles(): Promise<string[]> {
    return [];
  }

  async getSearchResults(_query: string): Promise<string> {
    return '';
  }

  async subprocess(command: string, cwd?: string): Promise<[string, string]> {
    return new Promise((resolve, reject) => {
      const workingDir = cwd || this.workspaceDir;
      const proc = spawn(command, {
        shell: true,
        cwd: workingDir,
      });

      let stdout = '';
      let stderr = '';

      proc.stdout?.on('data', (data) => {
        stdout += data.toString();
      });

      proc.stderr?.on('data', (data) => {
        stderr += data.toString();
      });

      proc.on('close', (code) => {
        if (code === 0) {
          resolve([stdout, stderr]);
        } else {
          reject(new Error(`Command failed with code ${code}: ${stderr}`));
        }
      });

      proc.on('error', (err) => {
        reject(err);
      });
    });
  }

  async getProblems(_filepath?: string): Promise<any[]> {
    return [];
  }

  async getTags(_artifactId: string): Promise<any[]> {
    return [];
  }

  async showToast(_type: ToastType, _message: string): Promise<void> {}

  async gotoDefinition(_location: any): Promise<any[]> {
    return [];
  }

  async getGitHubAuthToken(_args: any): Promise<string | undefined> {
    return undefined;
  }

  onDidChangeActiveTextEditor(_callback: (filepath: string) => void): void {}
}
