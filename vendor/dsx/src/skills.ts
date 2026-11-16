import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import matter from 'gray-matter';

export interface Skill {
  /** Slug used for /name invocation and the use_skill tool. */
  name: string;
  /** One-line summary shown to the model in the system prompt. */
  description: string;
  /** Full markdown instructions (frontmatter stripped). */
  body: string;
  /** Directory containing SKILL.md, for skills that ship support files. */
  dir: string;
  source: 'project' | 'user';
  /**
   * Namespaced subcommands discovered from `<dir>/commands/<sub>/SKILL.md`
   * (e.g. `gsd:progress`). These are surfaced in autocomplete and routed to
   * their own instructions, but kept OUT of the system-prompt skill list so a
   * skill with many commands doesn't bloat the prompt.
   */
  subcommands?: Skill[];
}

/**
 * Skills live in <dir>/<skill-name>/SKILL.md with YAML frontmatter:
 *
 *   ---
 *   name: commit
 *   description: Create a well-formed git commit
 *   ---
 *   <instructions...>
 *
 * Project skills (./skills) take precedence over user skills (~/.dsx/skills)
 * when names collide.
 */
export function loadSkills(cwd: string): Skill[] {
  // Skills are discovered from dsx-native roots and the standard Claude Code
  // roots (same SKILL.md + frontmatter format), so skills authored for Claude
  // Code show up here too. Earlier roots win on name collisions: project before
  // user, and dsx-native before .claude.
  const roots: Array<{ dir: string; source: Skill['source'] }> = [
    { dir: path.join(cwd, 'skills'), source: 'project' },
    { dir: path.join(cwd, '.claude', 'skills'), source: 'project' },
    { dir: path.join(os.homedir(), '.dsx', 'skills'), source: 'user' },
    { dir: path.join(os.homedir(), '.claude', 'skills'), source: 'user' },
  ];

  const byName = new Map<string, Skill>();
  for (const root of roots) {
    for (const skill of loadFromRoot(root.dir, root.source)) {
      if (!byName.has(skill.name)) byName.set(skill.name, skill);
    }
  }
  return [...byName.values()].sort((a, b) => a.name.localeCompare(b.name));
}

function loadFromRoot(root: string, source: Skill['source']): Skill[] {
  let entries: fs.Dirent[];
  try {
    entries = fs.readdirSync(root, { withFileTypes: true });
  } catch {
    return [];
  }

  const skills: Skill[] = [];
  for (const entry of entries) {
    const dir = path.join(root, entry.name);
    // Follow symlinks: plugin/marketplace managers often install a skill as a
    // symlink to its real directory (e.g. ~/.claude/skills/foo -> ...), and
    // Dirent.isDirectory() is false for symlinks. statSync resolves the target.
    let isDir = entry.isDirectory();
    if (!isDir && entry.isSymbolicLink()) {
      try {
        isDir = fs.statSync(dir).isDirectory();
      } catch {
        isDir = false;
      }
    }
    if (!isDir) continue;
    const skill = parseSkillDir(dir, entry.name, source);
    if (!skill) continue;
    skill.subcommands = loadSubcommands(dir, source);
    skills.push(skill);
  }
  return skills;
}

/**
 * Parse a single `<dir>/SKILL.md` into a Skill (without subcommands). Returns
 * undefined when the file is missing, has malformed frontmatter, or lacks a
 * name/description — callers skip those rather than crashing the session.
 */
function parseSkillDir(dir: string, fallbackName: string, source: Skill['source']): Skill | undefined {
  let raw: string;
  try {
    raw = fs.readFileSync(path.join(dir, 'SKILL.md'), 'utf8');
  } catch {
    return undefined;
  }
  try {
    const parsed = matter(raw);
    const name = String(parsed.data.name ?? fallbackName).trim();
    const description = String(parsed.data.description ?? '').trim();
    if (!name || !description) return undefined;
    return { name, description, body: parsed.content.trim(), dir, source };
  } catch {
    return undefined;
  }
}

/**
 * Discover a skill's namespaced subcommands from its `commands/` directory.
 * Each `commands/<sub>/SKILL.md` declares its own `name:` (e.g. `gsd:progress`);
 * we fall back to `<skill>:<sub>` when the frontmatter name omits the colon.
 */
function loadSubcommands(skillDir: string, source: Skill['source']): Skill[] {
  const commandsDir = path.join(skillDir, 'commands');
  let entries: fs.Dirent[];
  try {
    entries = fs.readdirSync(commandsDir, { withFileTypes: true });
  } catch {
    return [];
  }
  const subs: Skill[] = [];
  for (const entry of entries) {
    const dir = path.join(commandsDir, entry.name);
    let isDir = entry.isDirectory();
    if (!isDir && entry.isSymbolicLink()) {
      try {
        isDir = fs.statSync(dir).isDirectory();
      } catch {
        isDir = false;
      }
    }
    if (!isDir) continue;
    const parentName = path.basename(skillDir);
    const sub = parseSkillDir(dir, `${parentName}:${entry.name}`, source);
    if (sub) subs.push(sub);
  }
  return subs.sort((a, b) => a.name.localeCompare(b.name));
}

export function findSkill(skills: Skill[], name: string): Skill | undefined {
  return skills.find((s) => s.name === name);
}

/** Find a namespaced subcommand (e.g. `gsd:progress`) by its full name. */
export function findSubcommand(skills: Skill[], fullName: string): Skill | undefined {
  for (const s of skills) {
    const sub = s.subcommands?.find((c) => c.name === fullName);
    if (sub) return sub;
  }
  return undefined;
}

/** Message injected when the user force-invokes a skill with /name args. */
export function skillInvocationMessage(skill: Skill, args: string): string {
  return [
    `The user invoked the "${skill.name}" skill${args ? ` with arguments: "${args}"` : ''}.`,
    `Skill files live in: ${skill.dir}`,
    '',
    'Follow these skill instructions:',
    '',
    skill.body,
  ].join('\n');
}
