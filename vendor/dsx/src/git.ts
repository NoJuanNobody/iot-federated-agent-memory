import fs from 'node:fs';
import path from 'node:path';

/**
 * Current git branch for a directory, read straight from `.git/HEAD` (no child
 * process). Walks up to find the repo, follows the `.git`-file indirection used
 * by worktrees/submodules, and returns a short SHA when HEAD is detached.
 * Returns undefined when not inside a git repo.
 */
export function currentBranch(cwd: string): string | undefined {
  let dir = path.resolve(cwd);
  for (;;) {
    const gitPath = path.join(dir, '.git');
    try {
      const stat = fs.statSync(gitPath);
      let headFile = path.join(gitPath, 'HEAD');
      if (stat.isFile()) {
        // Worktree/submodule: `.git` is a file `gitdir: <path>`.
        const m = fs.readFileSync(gitPath, 'utf8').trim().match(/^gitdir:\s*(.+)$/);
        if (m) headFile = path.join(path.resolve(dir, m[1]), 'HEAD');
      }
      const head = fs.readFileSync(headFile, 'utf8').trim();
      const ref = head.match(/^ref:\s*refs\/heads\/(.+)$/);
      return ref ? ref[1] : head.slice(0, 7);
    } catch {
      // No repo here — walk up.
    }
    const parent = path.dirname(dir);
    if (parent === dir) return undefined;
    dir = parent;
  }
}
