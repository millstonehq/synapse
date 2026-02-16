import { execSync } from 'child_process';

export interface GitRemote {
  name: string;
  url: string;
  type: 'fetch' | 'push';
}

export interface GitCommit {
  hash: string;
  author: string;
  date: string;
  message: string;
}

export interface MergeConflict {
  path: string;
  status: string;
}

/**
 * Check if the current directory is a git repository
 */
export function checkGitRepo(cwd?: string): boolean {
  try {
    execSync('git rev-parse --git-dir', { cwd: cwd ?? process.cwd(), stdio: 'pipe', encoding: 'utf-8' });
    return true;
  } catch {
    return false;
  }
}

/**
 * Check if a remote exists
 */
export function hasRemote(name: string, cwd?: string): boolean {
  try {
    const remotes = execSync('git remote', { cwd: cwd ?? process.cwd(), stdio: 'pipe', encoding: 'utf-8' })
      .trim()
      .split('\n')
      .filter(Boolean);
    return remotes.includes(name);
  } catch {
    return false;
  }
}

/**
 * Get all remotes with their URLs
 */
export function getRemotes(cwd?: string): GitRemote[] {
  try {
    const output = execSync('git remote -v', { cwd: cwd ?? process.cwd(), stdio: 'pipe', encoding: 'utf-8' }).trim();
    if (!output) return [];

    const remotes: GitRemote[] = [];
    const lines = output.split('\n');

    for (const line of lines) {
      const match = line.match(/^(\S+)\s+(\S+)\s+\((\w+)\)$/);
      if (match) {
        remotes.push({
          name: match[1],
          url: match[2],
          type: match[3] as 'fetch' | 'push',
        });
      }
    }

    return remotes;
  } catch {
    return [];
  }
}

/**
 * Add a remote
 */
export function addRemote(name: string, url: string, cwd?: string): void {
  execSync(`git remote add ${name} ${url}`, { cwd: cwd ?? process.cwd(), stdio: 'pipe' });
}

/**
 * Remove a remote
 */
export function removeRemote(name: string, cwd?: string): void {
  execSync(`git remote remove ${name}`, { cwd: cwd ?? process.cwd(), stdio: 'pipe' });
}

/**
 * Fetch from a remote
 */
export function fetchRemote(name: string, cwd?: string): void {
  execSync(`git fetch ${name}`, { cwd: cwd ?? process.cwd(), stdio: 'inherit' });
}

/**
 * Get the current branch name
 */
export function getCurrentBranch(cwd?: string): string {
  try {
    return execSync('git branch --show-current', { cwd: cwd ?? process.cwd(), stdio: 'pipe', encoding: 'utf-8' }).trim();
  } catch (error) {
    throw new Error('Failed to get current branch');
  }
}

/**
 * Get the commit SHA for a branch
 */
export function getBranchHead(branch: string, cwd?: string): string {
  try {
    return execSync(`git rev-parse ${branch}`, { cwd: cwd ?? process.cwd(), stdio: 'pipe', encoding: 'utf-8' }).trim();
  } catch (error) {
    throw new Error(`Failed to get head for branch: ${branch}`);
  }
}

/**
 * Get commits between two refs
 */
export function getCommitsBetween(from: string, to: string, cwd?: string): GitCommit[] {
  try {
    const output = execSync(
      `git log ${from}..${to} --pretty=format:"%H|%an|%ai|%s"`,
      { cwd: cwd ?? process.cwd(), stdio: 'pipe', encoding: 'utf-8' }
    ).trim();

    if (!output) return [];

    const commits: GitCommit[] = [];
    const lines = output.split('\n');

    for (const line of lines) {
      const [hash, author, date, message] = line.split('|');
      if (hash && author && date && message) {
        commits.push({ hash, author, date, message });
      }
    }

    return commits;
  } catch {
    return [];
  }
}

/**
 * Check if there's a merge in progress
 */
export function isMergeInProgress(cwd?: string): boolean {
  try {
    const output = execSync('git status --porcelain=v1', { cwd: cwd ?? process.cwd(), stdio: 'pipe', encoding: 'utf-8' });
    return output.includes('UU ') || output.includes('AA ') || output.includes('DD ');
  } catch {
    return false;
  }
}

/**
 * Get merge conflicts
 */
export function getMergeConflicts(cwd?: string): MergeConflict[] {
  try {
    const output = execSync('git status --porcelain=v1', { cwd: cwd ?? process.cwd(), stdio: 'pipe', encoding: 'utf-8' }).trim();
    if (!output) return [];

    const conflicts: MergeConflict[] = [];
    const lines = output.split('\n');

    for (const line of lines) {
      const match = line.match(/^(UU|AA|DD|AU|UA|DU|UD)\s+(.+)$/);
      if (match) {
        conflicts.push({
          status: match[1],
          path: match[2],
        });
      }
    }

    return conflicts;
  } catch {
    return [];
  }
}

/**
 * Create a backup branch
 */
export function createBackupBranch(name: string, cwd?: string): void {
  execSync(`git branch ${name}`, { cwd: cwd ?? process.cwd(), stdio: 'pipe' });
}

/**
 * Merge a branch
 */
export function merge(branch: string, options: { noCommit?: boolean; noFf?: boolean; cwd?: string; stdio?: any } = {}): {
  success: boolean;
  conflicts: MergeConflict[];
} {
  try {
    let cmd = `git merge ${branch}`;
    if (options.noCommit) cmd += ' --no-commit';
    if (options.noFf) cmd += ' --no-ff';

    console.log('[DEBUG] Executing merge command:', cmd);
    console.log('[DEBUG] Working directory:', options.cwd ?? process.cwd());
    const output = execSync(cmd, { cwd: options.cwd ?? process.cwd(), stdio: options.stdio ?? 'pipe', encoding: 'utf-8' });
    console.log('[DEBUG] Merge output:', output);
    return { success: true, conflicts: [] };
  } catch (error) {
    console.log('[DEBUG] Merge failed:', error);
    // Check for conflicts
    const conflicts = getMergeConflicts(options.cwd);
    return { success: false, conflicts };
  }
}

/**
 * Abort a merge
 */
export function abortMerge(cwd?: string): void {
  execSync('git merge --abort', { cwd: cwd ?? process.cwd(), stdio: 'inherit' });
}

/**
 * Accept all changes from one side during merge
 */
export function acceptMergeStrategy(strategy: 'ours' | 'theirs', files?: string[], cwd?: string): void {
  const dir = cwd ?? process.cwd();
  if (files && files.length > 0) {
    for (const file of files) {
      execSync(`git checkout --${strategy} -- "${file}"`, { cwd: dir, stdio: 'pipe' });
      execSync(`git add "${file}"`, { cwd: dir, stdio: 'pipe' });
    }
  } else {
    // Accept for all conflicted files
    const conflicts = getMergeConflicts(dir);
    for (const conflict of conflicts) {
      execSync(`git checkout --${strategy} -- "${conflict.path}"`, { cwd: dir, stdio: 'pipe' });
      execSync(`git add "${conflict.path}"`, { cwd: dir, stdio: 'pipe' });
    }
  }
}

/**
 * Get current git tag or "dev" if none
 */
export function getCurrentVersion(cwd?: string): string {
  const dir = cwd ?? process.cwd();
  try {
    // Try to get the exact tag at HEAD
    const tag = execSync('git describe --exact-match --tags HEAD 2>/dev/null || echo ""', {
      cwd: dir,
      stdio: 'pipe',
      encoding: 'utf-8',
      shell: '/bin/bash'
    }).trim();

    if (tag) return tag;

    // Fallback to latest tag with commit info
    const describe = execSync('git describe --tags --always 2>/dev/null || echo "dev"', {
      cwd: dir,
      stdio: 'pipe',
      encoding: 'utf-8',
      shell: '/bin/bash'
    }).trim();

    return describe || 'dev';
  } catch {
    return 'dev';
  }
}

/**
 * Check if working directory is clean
 */
export function isWorkingDirectoryClean(cwd?: string): boolean {
  try {
    const output = execSync('git status --porcelain', { cwd: cwd ?? process.cwd(), stdio: 'pipe', encoding: 'utf-8' }).trim();
    return output === '';
  } catch {
    return false;
  }
}

/**
 * Get the number of commits ahead/behind remote
 */
export function getAheadBehind(local: string, remote: string, cwd?: string): { ahead: number; behind: number } {
  try {
    const output = execSync(`git rev-list --left-right --count ${local}...${remote}`, {
      cwd: cwd ?? process.cwd(),
      stdio: 'pipe',
      encoding: 'utf-8'
    }).trim();

    const [ahead, behind] = output.split('\t').map(n => parseInt(n, 10));
    return { ahead: ahead || 0, behind: behind || 0 };
  } catch {
    return { ahead: 0, behind: 0 };
  }
}
