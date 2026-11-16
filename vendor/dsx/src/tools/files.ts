import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import fg from 'fast-glob';
import type { Tool } from './index.js';
import { truncate } from './index.js';
import { buildCodeDiff, capCodeDiff, encodeCodeDiff } from '../ui/codeDiff.js';

const DEFAULT_IGNORE = ['**/node_modules/**', '**/.git/**', '**/dist/**', '**/build/**'];

function resolveIn(cwd: string, p: string): string {
  return path.isAbsolute(p) ? p : path.resolve(cwd, p);
}

/** A removed block (`-`) followed by an added block (`+`), for approval previews. */
export function diffBlock(oldStr: string, newStr: string): string[] {
  return [
    ...oldStr.split('\n').map((l) => `- ${l}`),
    ...newStr.split('\n').map((l) => `+ ${l}`),
  ];
}

/** Join preview lines, capping at `max` so a huge change can't flood the prompt. */
function capLines(lines: string[], max = 40): string {
  if (lines.length <= max) return lines.join('\n');
  return [...lines.slice(0, max), `… (+${lines.length - max} more lines)`].join('\n');
}

/** Display path for a diff header: relative to cwd, or ~-shortened absolute. */
function displayPath(cwd: string, file: string): string {
  const rel = path.relative(cwd, file);
  if (rel && !rel.startsWith('..') && !path.isAbsolute(rel)) return rel;
  const home = os.homedir();
  return home && file.startsWith(home) ? `~${file.slice(home.length)}` : file;
}

/**
 * Build a contextual, line-numbered approval preview for a file edit/write and
 * encode it for `DiffView`. `before`/`after` are the full file contents
 * (`before === '' && kind === 'create'` marks a brand-new file). Degrades
 * gracefully: any failure falls back to the legacy contextless `-`/`+` view.
 */
function codeDiffPreview(
  kind: 'create' | 'update',
  cwd: string,
  file: string,
  before: string,
  after: string,
): string {
  try {
    const diff = buildCodeDiff(kind, displayPath(cwd, file), before, after, 1);
    const { diff: capped } = capCodeDiff(diff);
    return encodeCodeDiff(capped);
  } catch {
    return capLines(diffBlock(before, after));
  }
}

interface FileEdit {
  old_string: string;
  new_string: string;
}

function parseEdits(raw: unknown): FileEdit[] {
  if (!Array.isArray(raw)) return [];
  return raw.map((e) => ({
    old_string: String((e as Record<string, unknown>)?.old_string ?? ''),
    new_string: String((e as Record<string, unknown>)?.new_string ?? ''),
  }));
}

export const readFileTool: Tool = {
  name: 'read_file',
  description:
    'Read a text file. Returns up to 2000 lines starting at the optional offset. ' +
    'Each line is prefixed with its line number and an arrow (e.g. "12→const x"). ' +
    'The prefix is not part of the file — strip it when quoting text for edit_file/write_file. ' +
    'Always read a file before editing it.',
  parameters: {
    type: 'object',
    properties: {
      path: { type: 'string', description: 'File path (absolute or relative to cwd).' },
      offset: { type: 'number', description: '1-based line to start reading from.' },
      limit: { type: 'number', description: 'Max lines to return (default 2000).' },
    },
    required: ['path'],
  },
  needsApproval: false,
  summarize: (args) => String(args.path ?? ''),
  async run(args, ctx) {
    const file = resolveIn(ctx.cwd, String(args.path ?? ''));
    const content = fs.readFileSync(file, 'utf8');
    if (content === '') return '(empty file)';
    const lines = content.split('\n');
    const offset = Math.max(1, Number(args.offset) || 1);
    const limit = Math.min(Number(args.limit) || 2000, 2000);
    const slice = lines.slice(offset - 1, offset - 1 + limit);
    let out = slice.map((line, i) => `${offset + i}→${line}`).join('\n');
    if (offset - 1 + limit < lines.length) {
      out += `\n... [${lines.length - (offset - 1 + limit)} more lines — re-read with offset=${offset + limit}]`;
    }
    return truncate(out, 50_000);
  },
};

export const writeFileTool: Tool = {
  name: 'write_file',
  description:
    'Create or overwrite a file with the given content. Creates parent directories as needed. ' +
    'Prefer edit_file for small changes to existing files.',
  parameters: {
    type: 'object',
    properties: {
      path: { type: 'string', description: 'File path (absolute or relative to cwd).' },
      content: { type: 'string', description: 'Full file content to write.' },
    },
    required: ['path', 'content'],
  },
  needsApproval: true,
  summarize: (args) => String(args.path ?? ''),
  preview(args, ctx) {
    const file = resolveIn(ctx.cwd, String(args.path ?? ''));
    const content = String(args.content ?? '');
    try {
      if (fs.existsSync(file)) {
        const old = fs.readFileSync(file, 'utf8');
        return codeDiffPreview('update', ctx.cwd, file, old, content);
      }
      return codeDiffPreview('create', ctx.cwd, file, '', content);
    } catch {
      if (fs.existsSync(file)) {
        const old = fs.readFileSync(file, 'utf8');
        return `overwrite ${file}\n${capLines(diffBlock(old, content))}`;
      }
      return `new file ${file}\n${capLines(content.split('\n').map((l) => `+ ${l}`))}`;
    }
  },
  async run(args, ctx) {
    const file = resolveIn(ctx.cwd, String(args.path ?? ''));
    const content = String(args.content ?? '');
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, content, 'utf8');
    return `Wrote ${content.length} chars to ${file}`;
  },
};

export const editFileTool: Tool = {
  name: 'edit_file',
  description:
    'Replace an exact string in a file. old_string must appear exactly once — include enough ' +
    'surrounding context to make it unique. Read the file first.',
  parameters: {
    type: 'object',
    properties: {
      path: { type: 'string', description: 'File path (absolute or relative to cwd).' },
      old_string: { type: 'string', description: 'Exact text to replace (must be unique).' },
      new_string: { type: 'string', description: 'Replacement text.' },
    },
    required: ['path', 'old_string', 'new_string'],
  },
  needsApproval: true,
  summarize: (args) => String(args.path ?? ''),
  preview(args, ctx) {
    const oldString = String(args.old_string ?? '');
    const newString = String(args.new_string ?? '');
    try {
      const file = resolveIn(ctx.cwd, String(args.path ?? ''));
      const before = fs.readFileSync(file, 'utf8');
      if (oldString && before.split(oldString).length - 1 === 1) {
        const after = before.replace(oldString, newString);
        return codeDiffPreview('update', ctx.cwd, file, before, after);
      }
    } catch {
      /* fall through to contextless diff */
    }
    return capLines(diffBlock(oldString, newString));
  },
  async run(args, ctx) {
    const file = resolveIn(ctx.cwd, String(args.path ?? ''));
    const oldString = String(args.old_string ?? '');
    const newString = String(args.new_string ?? '');
    if (!oldString) throw new Error('old_string must not be empty');
    const content = fs.readFileSync(file, 'utf8');
    const count = content.split(oldString).length - 1;
    if (count === 0) throw new Error('old_string not found in file');
    if (count > 1) {
      throw new Error(`old_string found ${count} times — add surrounding context to make it unique`);
    }
    fs.writeFileSync(file, content.replace(oldString, newString), 'utf8');
    return `Edited ${file}`;
  },
};

export const multiEditTool: Tool = {
  name: 'multi_edit',
  description:
    'Apply several exact-string replacements to one file in a single approval. ' +
    'Edits apply in order; each old_string must appear exactly once at the moment it is applied. ' +
    'All-or-nothing: if any replacement fails, the file is left untouched and the failing edit is reported. ' +
    'Read the file first and strip any "N→" line-number prefixes from quoted text.',
  parameters: {
    type: 'object',
    properties: {
      path: { type: 'string', description: 'File path (absolute or relative to cwd).' },
      edits: {
        type: 'array',
        description: 'Replacements applied in order.',
        items: {
          type: 'object',
          properties: {
            old_string: { type: 'string', description: 'Exact text to replace (unique when applied).' },
            new_string: { type: 'string', description: 'Replacement text.' },
          },
          required: ['old_string', 'new_string'],
        },
      },
    },
    required: ['path', 'edits'],
  },
  needsApproval: true,
  summarize: (args) => {
    const edits = parseEdits(args.edits);
    return `${String(args.path ?? '')} (${edits.length} edit${edits.length === 1 ? '' : 's'})`;
  },
  preview(args, ctx) {
    const edits = parseEdits(args.edits);
    try {
      const file = resolveIn(ctx.cwd, String(args.path ?? ''));
      const before = fs.readFileSync(file, 'utf8');
      let after = before;
      for (const e of edits) {
        if (!e.old_string || after.split(e.old_string).length - 1 !== 1) {
          throw new Error('edit not uniquely applicable for preview');
        }
        after = after.replace(e.old_string, e.new_string);
      }
      return codeDiffPreview('update', ctx.cwd, file, before, after);
    } catch {
      return capLines(edits.flatMap((e) => diffBlock(e.old_string, e.new_string)));
    }
  },
  async run(args, ctx) {
    const file = resolveIn(ctx.cwd, String(args.path ?? ''));
    const edits = parseEdits(args.edits);
    if (edits.length === 0) throw new Error('edits must be a non-empty array');
    let content = fs.readFileSync(file, 'utf8');
    edits.forEach((e, idx) => {
      if (!e.old_string) throw new Error(`edit ${idx + 1}: old_string must not be empty`);
      const count = content.split(e.old_string).length - 1;
      if (count === 0) throw new Error(`edit ${idx + 1}: old_string not found`);
      if (count > 1) {
        throw new Error(`edit ${idx + 1}: old_string found ${count} times — add surrounding context to make it unique`);
      }
      content = content.replace(e.old_string, e.new_string);
    });
    fs.writeFileSync(file, content, 'utf8');
    return `Applied ${edits.length} edit(s) to ${file}`;
  },
};

export const listFilesTool: Tool = {
  name: 'list_files',
  description:
    'List files matching a glob pattern (e.g. "src/**/*.ts"). ' +
    'Ignores node_modules, .git, dist, and build. Returns at most 200 paths.',
  parameters: {
    type: 'object',
    properties: {
      pattern: { type: 'string', description: 'Glob pattern (default "**/*").' },
    },
  },
  needsApproval: false,
  summarize: (args) => String(args.pattern ?? '**/*'),
  async run(args, ctx) {
    const pattern = String(args.pattern ?? '**/*');
    const files = await fg(pattern, {
      cwd: ctx.cwd,
      ignore: DEFAULT_IGNORE,
      dot: false,
      onlyFiles: true,
    });
    if (files.length === 0) return 'No files matched.';
    const shown = files.slice(0, 200).sort();
    let out = shown.join('\n');
    if (files.length > 200) out += `\n... [${files.length - 200} more files]`;
    return out;
  },
};

export const listDirectoryTool: Tool = {
  name: 'list_directory',
  description:
    'Browse a directory for interactive file browsing. ' +
    'Returns a JSON array of entries with name, path, size, mtime, isDir, and lineCount. ' +
    'Use arg "subdir" for a relative folder path (default "" = cwd).',
  parameters: {
    type: 'object',
    properties: {
      subdir: { type: 'string', description: 'Relative subdirectory to list (default "" = cwd).' },
      pattern: { type: 'string', description: 'Optional glob pattern to filter children.' },
    },
  },
  needsApproval: false,
  summarize: (args) => `dir ${String(args.subdir ?? '.')}`,
  async run(args, ctx) {
    const subdir = String(args.subdir ?? '');
    const dir = subdir ? path.resolve(ctx.cwd, subdir) : ctx.cwd;
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    const ignored = new Set(DEFAULT_IGNORE.map((p) => p.replace(/^\*\*\//, '').replace(/\/$/, '')));
    const items = entries
      .filter((e) => !e.name.startsWith('.') && !ignored.has(e.name))
      .map((e) => {
        const full = path.join(dir, e.name);
        const rel = path.relative(ctx.cwd, full);
        const stat = fs.statSync(full);
        const isDir = e.isDirectory();
        let lineCount: number | undefined;
        if (!isDir && stat.size < 2 * 1024 * 1024) {
          try {
            const buf = fs.readFileSync(full, 'utf8');
            lineCount = buf.split('\n').length;
          } catch {
            // binary or unreadable
          }
        }
        return { name: e.name, path: rel, size: stat.size, mtime: stat.mtime.toISOString(), isDir, lineCount };
      })
      .sort((a, b) => Number(b.isDir) - Number(a.isDir) || a.name.localeCompare(b.name));
    return JSON.stringify(items.slice(0, 200));
  },
};
