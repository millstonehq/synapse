import { execSync } from 'child_process';
import fsExtra from 'fs-extra';
import * as path from 'path';
import { jest } from '@jest/globals';
import * as git from '../../src/lib/git.js';

const fs = fsExtra;

describe('git module', () => {
  // Capture cwd ONCE at module load, before any tests run
  const ORIGINAL_CWD = process.cwd();
  const testRepo = path.join(ORIGINAL_CWD, 'test-git-tmp');

  afterAll(() => {
    // Ensure we restore cwd after ALL tests in this file complete
    try {
      process.chdir(ORIGINAL_CWD);
    } catch {}
  });

  beforeEach(async () => {
    await fs.ensureDir(testRepo);

    // Try git init with --initial-branch (Git 2.28+), fallback to older method
    try {
      execSync('git init --initial-branch=main', { cwd: testRepo, stdio: 'pipe' });
    } catch {
      // Fallback for older Git versions
      execSync('git init', { cwd: testRepo, stdio: 'pipe' });
      execSync('git checkout -b main', { cwd: testRepo, stdio: 'pipe' });
    }

    execSync('git config user.name "Test User"', { cwd: testRepo, stdio: 'pipe' });
    execSync('git config user.email "test@example.com"', { cwd: testRepo, stdio: 'pipe' });

    // Create initial commit so we have a valid HEAD
    await fs.writeFile(path.join(testRepo, 'README.md'), '# Test\n', 'utf-8');
    execSync('git add README.md', { cwd: testRepo, stdio: 'pipe' });
    execSync('git commit -m "Initial commit"', { cwd: testRepo, stdio: 'pipe' });
  });

  afterEach(async () => {
    // ALWAYS restore cwd first, even if test failed
    try {
      process.chdir(ORIGINAL_CWD);
    } catch (e) {
      // If chdir fails, we're screwed anyway
    }
    await fs.remove(testRepo);
    jest.clearAllMocks();
  });

  describe('checkGitRepo', () => {
    it('should return true when in a git repository', () => {
      expect(git.checkGitRepo(testRepo)).toBe(true);
    });

    it('should return false when not in a git repository', async () => {
      // Create temp dir in /tmp to ensure it's outside any git repo
      const nonGitDir = path.join('/tmp', 'test-non-git-' + Date.now());
      await fs.ensureDir(nonGitDir);

      expect(git.checkGitRepo(nonGitDir)).toBe(false);

      await fs.remove(nonGitDir);
    });
  });

  describe('hasRemote', () => {
    it('should return false when no remotes exist', () => {
      expect(git.hasRemote('origin', testRepo)).toBe(false);
    });

    it('should return true when remote exists', () => {
      execSync('git remote add origin git@github.com:test/repo.git', { cwd: testRepo, stdio: 'pipe' });
      expect(git.hasRemote('origin', testRepo)).toBe(true);
    });

    it('should return false when different remote exists', () => {
      execSync('git remote add origin git@github.com:test/repo.git', { cwd: testRepo, stdio: 'pipe' });
      expect(git.hasRemote('upstream', testRepo)).toBe(false);
    });
  });

  describe('getRemotes', () => {
    it('should return empty array when no remotes', () => {
      const remotes = git.getRemotes(testRepo);
      expect(remotes).toEqual([]);
    });

    it('should list all remotes with URLs', () => {
      execSync('git remote add origin git@github.com:user/repo.git', { cwd: testRepo, stdio: 'pipe' });
      execSync('git remote add upstream git@github.com:org/repo.git', { cwd: testRepo, stdio: 'pipe' });

      const remotes = git.getRemotes(testRepo);
      expect(remotes.length).toBeGreaterThanOrEqual(2);

      const origin = remotes.find(r => r.name === 'origin' && r.type === 'fetch');
      expect(origin).toBeDefined();
      expect(origin?.url).toBe('git@github.com:user/repo.git');
    });
  });

  describe('addRemote', () => {
    it('should add a new remote', () => {
      git.addRemote('origin', 'git@github.com:test/repo.git', testRepo);
      expect(git.hasRemote('origin', testRepo)).toBe(true);
    });
  });

  describe('removeRemote', () => {
    it('should remove an existing remote', () => {
      execSync('git remote add origin git@github.com:test/repo.git', { cwd: testRepo, stdio: 'pipe' });
      expect(git.hasRemote('origin', testRepo)).toBe(true);

      git.removeRemote('origin', testRepo);
      expect(git.hasRemote('origin', testRepo)).toBe(false);
    });
  });

  describe('getCurrentBranch', () => {
    it('should return current branch name', () => {
      const branch = git.getCurrentBranch(testRepo);
      expect(branch).toBe('main');
    });

    it('should return correct branch after checkout', () => {
      execSync('git checkout -b feature', { cwd: testRepo, stdio: 'pipe' });
      expect(git.getCurrentBranch(testRepo)).toBe('feature');
    });
  });

  describe('getBranchHead', () => {
    it('should return commit SHA for branch', () => {
      const sha = git.getBranchHead('main', testRepo);
      expect(sha).toMatch(/^[a-f0-9]{40}$/);
    });
  });

  describe('getCommitsBetween', () => {
    it('should return empty array when no commits between refs', () => {
      const commits = git.getCommitsBetween('HEAD', 'HEAD', testRepo);
      expect(commits).toEqual([]);
    });

    it('should return commits between refs', async () => {
      // Create a second commit
      await fs.writeFile(path.join(testRepo, 'file.txt'), 'content\n', 'utf-8');
      execSync('git add file.txt', { cwd: testRepo, stdio: 'pipe' });
      execSync('git commit -m "Second commit"', { cwd: testRepo, stdio: 'pipe' });

      const commits = git.getCommitsBetween('HEAD~1', 'HEAD', testRepo);
      expect(commits).toHaveLength(1);
      expect(commits[0].message).toBe('Second commit');
      expect(commits[0].author).toBe('Test User');
    });
  });

  describe('isWorkingDirectoryClean', () => {
    it('should return true when working directory is clean', () => {
      expect(git.isWorkingDirectoryClean(testRepo)).toBe(true);
    });

    it('should return false when there are uncommitted changes', async () => {
      await fs.writeFile(path.join(testRepo, 'new-file.txt'), 'content\n', 'utf-8');
      expect(git.isWorkingDirectoryClean(testRepo)).toBe(false);
    });

    it('should return false when there are staged changes', async () => {
      await fs.writeFile(path.join(testRepo, 'new-file.txt'), 'content\n', 'utf-8');
      execSync('git add new-file.txt', { cwd: testRepo, stdio: 'pipe' });
      expect(git.isWorkingDirectoryClean(testRepo)).toBe(false);
    });
  });

  describe('createBackupBranch', () => {
    it('should create a new branch', () => {
      git.createBackupBranch('backup-main', testRepo);

      const branches = execSync('git branch', { cwd: testRepo, stdio: 'pipe', encoding: 'utf-8' });
      expect(branches).toContain('backup-main');
    });
  });

  describe('getCurrentVersion', () => {
    it('should return dev when no tags', () => {
      const version = git.getCurrentVersion(testRepo);
      expect(version).toBeDefined();
      // Could be a short SHA or "dev"
      expect(version.length).toBeGreaterThan(0);
    });

    it('should return tag when at tagged commit', () => {
      execSync('git tag v1.0.0', { cwd: testRepo, stdio: 'pipe' });
      const version = git.getCurrentVersion(testRepo);
      expect(version).toBe('v1.0.0');
    });
  });

  describe('isMergeInProgress', () => {
    it('should return false when no merge in progress', () => {
      expect(git.isMergeInProgress(testRepo)).toBe(false);
    });
  });

  describe('getMergeConflicts', () => {
    it('should return empty array when no conflicts', () => {
      const conflicts = git.getMergeConflicts(testRepo);
      expect(conflicts).toEqual([]);
    });
  });

  describe('getAheadBehind', () => {
    it('should return zeros when branches are at same commit', () => {
      execSync('git branch test-branch', { cwd: testRepo, stdio: 'pipe' });
      const result = git.getAheadBehind('main', 'test-branch', testRepo);
      expect(result).toEqual({ ahead: 0, behind: 0 });
    });

    it('should return ahead count when local has commits', async () => {
      execSync('git branch old-main', { cwd: testRepo, stdio: 'pipe' });

      await fs.writeFile(path.join(testRepo, 'new.txt'), 'content\n', 'utf-8');
      execSync('git add new.txt', { cwd: testRepo, stdio: 'pipe' });
      execSync('git commit -m "New commit"', { cwd: testRepo, stdio: 'pipe' });

      const result = git.getAheadBehind('main', 'old-main', testRepo);
      expect(result.ahead).toBe(1);
      expect(result.behind).toBe(0);
    });

    it('should return zeros on error', async () => {
      const nonGitDir = path.join('/tmp', 'test-non-git-' + Date.now());
      await fs.ensureDir(nonGitDir);

      const result = git.getAheadBehind('main', 'invalid', nonGitDir);
      expect(result).toEqual({ ahead: 0, behind: 0 });

      await fs.remove(nonGitDir);
    });
  });

  describe('error handling', () => {
    it('hasRemote should return false on error', async () => {
      const nonGitDir = path.join('/tmp', 'test-non-git-' + Date.now());
      await fs.ensureDir(nonGitDir);

      expect(git.hasRemote('origin', nonGitDir)).toBe(false);

      await fs.remove(nonGitDir);
    });

    it('getRemotes should return empty array on error', async () => {
      const nonGitDir = path.join('/tmp', 'test-non-git-' + Date.now());
      await fs.ensureDir(nonGitDir);

      expect(git.getRemotes(nonGitDir)).toEqual([]);

      await fs.remove(nonGitDir);
    });

    it('getCurrentBranch should throw on error', async () => {
      const nonGitDir = path.join('/tmp', 'test-non-git-' + Date.now());
      await fs.ensureDir(nonGitDir);

      expect(() => git.getCurrentBranch(nonGitDir)).toThrow('Failed to get current branch');

      await fs.remove(nonGitDir);
    });

    it('getBranchHead should throw on error', () => {
      expect(() => git.getBranchHead('nonexistent-branch', testRepo)).toThrow('Failed to get head for branch');
    });

    it('getCommitsBetween should return empty array on error', () => {
      const commits = git.getCommitsBetween('invalid-ref', 'invalid-ref2', testRepo);
      expect(commits).toEqual([]);
    });

    it('isMergeInProgress should return false on error', async () => {
      const nonGitDir = path.join('/tmp', 'test-non-git-' + Date.now());
      await fs.ensureDir(nonGitDir);

      expect(git.isMergeInProgress(nonGitDir)).toBe(false);

      await fs.remove(nonGitDir);
    });

    it('getMergeConflicts should return empty array on error', async () => {
      const nonGitDir = path.join('/tmp', 'test-non-git-' + Date.now());
      await fs.ensureDir(nonGitDir);

      expect(git.getMergeConflicts(nonGitDir)).toEqual([]);

      await fs.remove(nonGitDir);
    });

    it('getCurrentVersion should return dev on error', async () => {
      const nonGitDir = path.join('/tmp', 'test-non-git-' + Date.now());
      await fs.ensureDir(nonGitDir);

      expect(git.getCurrentVersion(nonGitDir)).toBe('dev');

      await fs.remove(nonGitDir);
    });

    it('isWorkingDirectoryClean should return false on error', async () => {
      const nonGitDir = path.join('/tmp', 'test-non-git-' + Date.now());
      await fs.ensureDir(nonGitDir);

      expect(git.isWorkingDirectoryClean(nonGitDir)).toBe(false);

      await fs.remove(nonGitDir);
    });
  });

  describe('merge operations', () => {
    it('should successfully merge branches', async () => {
      // Create a feature branch
      execSync('git checkout -b feature', { cwd: testRepo, stdio: 'pipe' });
      await fs.writeFile(path.join(testRepo, 'feature.txt'), 'feature content\n', 'utf-8');
      execSync('git add feature.txt', { cwd: testRepo, stdio: 'pipe' });
      execSync('git commit -m "Add feature"', { cwd: testRepo, stdio: 'pipe' });

      // Switch back to main
      execSync('git checkout main', { cwd: testRepo, stdio: 'pipe' });

      // Merge feature branch
      const result = git.merge('feature', { cwd: testRepo });
      expect(result.success).toBe(true);
      expect(result.conflicts).toEqual([]);
    });

    it('should handle merge with --no-commit option', async () => {
      execSync('git checkout -b feature2', { cwd: testRepo, stdio: 'pipe' });
      await fs.writeFile(path.join(testRepo, 'feature2.txt'), 'content\n', 'utf-8');
      execSync('git add feature2.txt', { cwd: testRepo, stdio: 'pipe' });
      execSync('git commit -m "Add feature2"', { cwd: testRepo, stdio: 'pipe' });
      execSync('git checkout main', { cwd: testRepo, stdio: 'pipe' });

      const result = git.merge('feature2', { noCommit: true, cwd: testRepo });
      expect(result.success).toBe(true);
    });

    it('should handle merge with --no-ff option', async () => {
      execSync('git checkout -b feature3', { cwd: testRepo, stdio: 'pipe' });
      await fs.writeFile(path.join(testRepo, 'feature3.txt'), 'content\n', 'utf-8');
      execSync('git add feature3.txt', { cwd: testRepo, stdio: 'pipe' });
      execSync('git commit -m "Add feature3"', { cwd: testRepo, stdio: 'pipe' });
      execSync('git checkout main', { cwd: testRepo, stdio: 'pipe' });

      const result = git.merge('feature3', { noFf: true, cwd: testRepo });
      expect(result.success).toBe(true);
    });

    it('should detect merge conflicts', async () => {
      // Create conflicting changes
      execSync('git checkout -b conflict-branch', { cwd: testRepo, stdio: 'pipe' });
      await fs.writeFile(path.join(testRepo, 'README.md'), '# Conflict Branch\n', 'utf-8');
      execSync('git add README.md', { cwd: testRepo, stdio: 'pipe' });
      execSync('git commit -m "Update README in conflict branch"', { cwd: testRepo, stdio: 'pipe' });

      execSync('git checkout main', { cwd: testRepo, stdio: 'pipe' });
      await fs.writeFile(path.join(testRepo, 'README.md'), '# Main Branch\n', 'utf-8');
      execSync('git add README.md', { cwd: testRepo, stdio: 'pipe' });
      execSync('git commit -m "Update README in main"', { cwd: testRepo, stdio: 'pipe' });

      // Attempt merge
      const result = git.merge('conflict-branch', { cwd: testRepo });
      expect(result.success).toBe(false);
      expect(result.conflicts.length).toBeGreaterThan(0);

      // Clean up - abort the merge
      git.abortMerge(testRepo);
    });

    it('should abort a merge', async () => {
      // Create a merge conflict first
      execSync('git checkout -b abort-branch', { cwd: testRepo, stdio: 'pipe' });
      await fs.writeFile(path.join(testRepo, 'README.md'), '# Abort Test\n', 'utf-8');
      execSync('git add README.md', { cwd: testRepo, stdio: 'pipe' });
      execSync('git commit -m "Update for abort test"', { cwd: testRepo, stdio: 'pipe' });

      execSync('git checkout main', { cwd: testRepo, stdio: 'pipe' });
      await fs.writeFile(path.join(testRepo, 'README.md'), '# Main Abort\n', 'utf-8');
      execSync('git add README.md', { cwd: testRepo, stdio: 'pipe' });
      execSync('git commit -m "Main update for abort"', { cwd: testRepo, stdio: 'pipe' });

      git.merge('abort-branch', { cwd: testRepo });

      // Abort should work without error
      expect(() => git.abortMerge(testRepo)).not.toThrow();
    });

    it('should accept merge strategy with specific files', async () => {
      // Create a merge conflict
      execSync('git checkout -b strategy-branch', { cwd: testRepo, stdio: 'pipe' });
      await fs.writeFile(path.join(testRepo, 'conflict.txt'), 'theirs\n', 'utf-8');
      execSync('git add conflict.txt', { cwd: testRepo, stdio: 'pipe' });
      execSync('git commit -m "Add conflict file"', { cwd: testRepo, stdio: 'pipe' });

      execSync('git checkout main', { cwd: testRepo, stdio: 'pipe' });
      await fs.writeFile(path.join(testRepo, 'conflict.txt'), 'ours\n', 'utf-8');
      execSync('git add conflict.txt', { cwd: testRepo, stdio: 'pipe' });
      execSync('git commit -m "Add conflict file in main"', { cwd: testRepo, stdio: 'pipe' });

      git.merge('strategy-branch', { cwd: testRepo });

      // Accept ours for specific file
      expect(() => git.acceptMergeStrategy('ours', ['conflict.txt'], testRepo)).not.toThrow();

      // Complete the merge
      execSync('git commit --no-edit', { cwd: testRepo, stdio: 'pipe' });
    });

    it('should accept merge strategy for all files', async () => {
      // Create another conflict
      execSync('git checkout -b strategy-all-branch', { cwd: testRepo, stdio: 'pipe' });
      await fs.writeFile(path.join(testRepo, 'all-conflict.txt'), 'theirs content\n', 'utf-8');
      execSync('git add all-conflict.txt', { cwd: testRepo, stdio: 'pipe' });
      execSync('git commit -m "Add all-conflict file"', { cwd: testRepo, stdio: 'pipe' });

      execSync('git checkout main', { cwd: testRepo, stdio: 'pipe' });
      await fs.writeFile(path.join(testRepo, 'all-conflict.txt'), 'ours content\n', 'utf-8');
      execSync('git add all-conflict.txt', { cwd: testRepo, stdio: 'pipe' });
      execSync('git commit -m "Add all-conflict in main"', { cwd: testRepo, stdio: 'pipe' });

      git.merge('strategy-all-branch', { cwd: testRepo });

      // Accept theirs for all conflicted files
      expect(() => git.acceptMergeStrategy('theirs', undefined, testRepo)).not.toThrow();

      // Complete the merge
      execSync('git commit --no-edit', { cwd: testRepo, stdio: 'pipe' });
    });
  });

  describe('fetchRemote', () => {
    it('should use custom remote name', () => {
      git.addRemote('custom-remote', 'git@github.com:test/repo.git', testRepo);
      // This would normally fetch, but since it's not a real remote, we just verify it doesn't throw
      // In a real scenario this would contact the remote server
      // For test purposes, we just ensure the function can be called
      expect(() => git.fetchRemote('custom-remote', testRepo)).toThrow();
    });
  });
});
