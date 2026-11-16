import fs from 'node:fs';
import path from 'node:path';
import { Project, Node, SyntaxKind, type SourceFile } from 'ts-morph';
import type { Tool, ToolContext } from './index.js';
import { buildCodeDiff } from '../ui/codeDiff.js';

const TS_EXTENSIONS = new Set(['.ts', '.tsx', '.mts', '.cts', '.js', '.jsx', '.mjs', '.cjs']);

function resolveIn(cwd: string, p: string): string {
  return path.isAbsolute(p) ? p : path.resolve(cwd, p);
}

/** A removed block (`-`) followed by an added block (`+`), for approval previews. */
function diffBlock(oldStr: string, newStr: string): string[] {
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

interface RenameArgs {
  path: string;
  symbol?: string;
  line?: number;
  column?: number;
  new_name: string;
}

function parseArgs(args: Record<string, unknown>): RenameArgs {
  return {
    path: String(args.path ?? ''),
    symbol: args.symbol != null ? String(args.symbol) : undefined,
    line: args.line != null ? Number(args.line) : undefined,
    column: args.column != null ? Number(args.column) : undefined,
    new_name: String(args.new_name ?? ''),
  };
}

/**
 * Result of loading the project and locating the symbol to rename.
 * `error` is a human-readable, no-op message (e.g. symbol not found);
 * otherwise `project` and `node` are populated.
 */
interface Located {
  error?: string;
  project?: Project;
  node?: Node;
}

/** Build a ts-morph Project rooted at ctx.cwd, honoring tsconfig.json if present. */
function loadProject(cwd: string): Project {
  const tsconfig = path.join(cwd, 'tsconfig.json');
  if (fs.existsSync(tsconfig)) {
    return new Project({ tsConfigFilePath: tsconfig });
  }
  // No tsconfig: an in-memory-ish project; we add files on demand below.
  return new Project({
    compilerOptions: { allowJs: true, checkJs: false },
    skipAddingFilesFromTsConfig: true,
  });
}

/** Locate the identifier node the user wants to rename within `file`. */
function locate(args: RenameArgs, cwd: string): Located {
  const file = resolveIn(cwd, args.path);
  const ext = path.extname(file).toLowerCase();
  if (!TS_EXTENSIONS.has(ext)) {
    return {
      error: `Unsupported file type "${ext || '(none)'}". rename_symbol only handles TypeScript/JavaScript files (${[...TS_EXTENSIONS].join(', ')}).`,
    };
  }
  if (!fs.existsSync(file)) {
    return { error: `File not found: ${file}` };
  }
  if (!args.new_name.trim()) {
    return { error: 'new_name must not be empty.' };
  }

  const project = loadProject(cwd);
  let source: SourceFile | undefined = project.getSourceFile(file);
  if (!source) {
    // Not part of tsconfig (or no tsconfig): add it so references can be resolved.
    source = project.addSourceFileAtPathIfExists(file);
  }
  if (!source) {
    return { error: `Could not load source file: ${file}` };
  }

  let target: Node | undefined;

  if (args.line != null) {
    // Position-based: find the identifier at the given 1-based line/column.
    const lineStarts: number[] = [];
    const text = source.getFullText();
    lineStarts.push(0);
    for (let i = 0; i < text.length; i++) {
      if (text[i] === '\n') lineStarts.push(i + 1);
    }
    const lineIdx = args.line - 1;
    if (lineIdx < 0 || lineIdx >= lineStarts.length) {
      return { error: `Line ${args.line} is out of range for ${file}.` };
    }
    const col = args.column != null ? args.column - 1 : 0;
    const pos = lineStarts[lineIdx] + Math.max(0, col);
    const node = source.getDescendantAtPos(pos);
    if (node && Node.isIdentifier(node)) target = node;
    else if (node) target = node.getFirstDescendant((d) => Node.isIdentifier(d)) ?? node;
    if (!target) {
      return { error: `No identifier found at ${args.path}:${args.line}:${args.column ?? 1}.` };
    }
  } else if (args.symbol) {
    // Name-based: find the first identifier whose text matches `symbol` and
    // which actually declares/binds that name (so we rename the definition).
    const matches = source
      .getDescendantsOfKind(SyntaxKind.Identifier)
      .filter((id) => id.getText() === args.symbol);
    // Prefer an identifier that is the name of a declaration.
    target =
      matches.find((id) => {
        const parent = id.getParent();
        return parent != null && Node.isNamed(parent) && parent.getNameNode?.() === id;
      }) ?? matches[0];
    if (!target) {
      return { error: `Symbol "${args.symbol}" not found in ${args.path}.` };
    }
  } else {
    return { error: 'Provide either "symbol" (a name) or "line" (a 1-based position) to identify what to rename.' };
  }

  return { project, node: target };
}

/**
 * Perform the rename in-memory and return the set of changed files with their
 * before/after text. Does NOT write to disk — callers decide that.
 */
function computeRename(
  args: RenameArgs,
  located: Located,
): { error?: string; changes?: Array<{ path: string; before: string; after: string }> } {
  const { project, node } = located;
  if (!project || !node) return { error: located.error ?? 'Internal error: nothing located.' };

  // Snapshot original text of every source file so we can diff afterwards.
  const before = new Map<string, string>();
  for (const sf of project.getSourceFiles()) {
    before.set(sf.getFilePath(), sf.getFullText());
  }

  // The node may be an identifier; find the renameable node.
  let renameTarget = node;
  if (!Node.isRenameable(renameTarget)) {
    const parent = renameTarget.getParent();
    if (parent && Node.isRenameable(parent)) renameTarget = parent;
  }
  if (!Node.isRenameable(renameTarget)) {
    return { error: 'The selected node cannot be renamed (not a renameable symbol).' };
  }

  try {
    renameTarget.rename(args.new_name);
  } catch (err) {
    return { error: `Rename failed: ${(err as Error).message}` };
  }

  const changes: Array<{ path: string; before: string; after: string }> = [];
  for (const sf of project.getSourceFiles()) {
    const p = sf.getFilePath();
    const oldText = before.get(p) ?? '';
    const newText = sf.getFullText();
    if (oldText !== newText) {
      changes.push({ path: p, before: oldText, after: newText });
    }
  }

  if (changes.length === 0) {
    return { error: `No occurrences of the symbol were changed (already named "${args.new_name}"?).` };
  }

  return { changes };
}

/**
 * Contextual, line-numbered diff of two file versions (#77). Multi-file rename
 * previews concatenate one of these per touched file, so this stays a text form
 * the legacy DiffView path can color (`+`/`-`/context) while showing original
 * line numbers and a few lines of surrounding context per hunk.
 */
function fileDiff(relPath: string, before: string, after: string): string[] {
  const out: string[] = [`@@ ${relPath} @@`];
  try {
    const diff = buildCodeDiff('update', relPath, before, after, 1);
    const w = diff.gutterWidth;
    for (let h = 0; h < diff.hunks.length; h++) {
      if (h > 0) out.push('  ⋮');
      for (const row of diff.hunks[h].rows) {
        const gutter = String(row.num ?? '').padStart(w);
        const sign = row.kind === 'add' ? '+' : row.kind === 'remove' ? '-' : ' ';
        out.push(`${gutter} ${sign} ${row.text}`);
      }
    }
    return out;
  } catch {
    const oldLines = before.split('\n');
    const newLines = after.split('\n');
    const max = Math.max(oldLines.length, newLines.length);
    for (let i = 0; i < max; i++) {
      const o = oldLines[i];
      const n = newLines[i];
      if (o === n) continue;
      if (o !== undefined) out.push(`- ${o}`);
      if (n !== undefined) out.push(`+ ${n}`);
    }
    return out;
  }
}

export const renameSymbolTool: Tool = {
  name: 'rename_symbol',
  description:
    'Semantically rename a TypeScript/JavaScript symbol (variable, function, class, interface, ' +
    'type, method, etc.) and ALL of its references across the whole project in one operation. ' +
    'Unlike a text search-and-replace this is AST-aware (powered by ts-morph): it only touches ' +
    'genuine references to the same symbol and follows imports/exports. ' +
    'Identify the symbol either by name ("symbol") or by a 1-based source position ("line"/"column") ' +
    'within the given file. The project root and tsconfig.json are resolved from the working directory. ' +
    'All-or-nothing: on any failure nothing is written. Only TypeScript/JavaScript files are supported.',
  parameters: {
    type: 'object',
    properties: {
      path: {
        type: 'string',
        description: 'Path (absolute or relative to cwd) to a TS/JS file containing the symbol.',
      },
      symbol: {
        type: 'string',
        description:
          'Current name of the symbol to rename. Prefer this when the name is unambiguous in the file. ' +
          'Omit if you are using line/column instead.',
      },
      line: {
        type: 'number',
        description:
          '1-based line of an occurrence of the symbol (use with "column"). Use this instead of "symbol" ' +
          'to disambiguate when a name appears multiple times.',
      },
      column: {
        type: 'number',
        description: '1-based column of the symbol on the given line (used with "line").',
      },
      new_name: {
        type: 'string',
        description: 'The new name for the symbol.',
      },
    },
    required: ['path', 'new_name'],
  },
  needsApproval: true,
  summarize: (args) => {
    const a = parseArgs(args);
    const what = a.symbol ? a.symbol : a.line != null ? `${a.path}:${a.line}:${a.column ?? 1}` : a.path;
    return `rename ${what} → ${a.new_name}`;
  },
  preview(args, ctx) {
    const a = parseArgs(args);
    const located = locate(a, ctx.cwd);
    if (located.error) return located.error;
    const result = computeRename(a, located);
    if (result.error || !result.changes) return result.error ?? 'No changes.';
    const lines: string[] = [];
    for (const c of result.changes) {
      const rel = path.relative(ctx.cwd, c.path) || c.path;
      lines.push(...fileDiff(rel, c.before, c.after));
    }
    const header = `rename "${a.symbol ?? `${a.path}:${a.line}:${a.column ?? 1}`}" → "${a.new_name}" across ${result.changes.length} file(s)`;
    return `${header}\n${capLines(lines)}`;
  },
  async run(args, ctx) {
    const a = parseArgs(args);
    if (ctx.signal?.aborted) throw new Error('Aborted before start.');

    const located = locate(a, ctx.cwd);
    if (located.error) return located.error; // no-op, clear message (e.g. symbol not found)

    const result = computeRename(a, located);
    if (result.error || !result.changes) return result.error ?? 'No changes.';

    if (ctx.signal?.aborted) throw new Error('Aborted before writing.');

    // All-or-nothing write: stage every change, then flush. If anything throws
    // mid-write we still attempt to restore previously written files.
    const written: Array<{ path: string; before: string }> = [];
    try {
      for (const c of result.changes) {
        written.push({ path: c.path, before: c.before });
        fs.writeFileSync(c.path, c.after, 'utf8');
      }
    } catch (err) {
      for (const w of written) {
        try {
          fs.writeFileSync(w.path, w.before, 'utf8');
        } catch {
          // best-effort rollback
        }
      }
      throw new Error(`Rename write failed, rolled back: ${(err as Error).message}`);
    }

    const files = result.changes.map((c) => path.relative(ctx.cwd, c.path) || c.path);
    return `Renamed to "${a.new_name}" across ${files.length} file(s):\n${files.join('\n')}`;
  },
};
