import fs from 'node:fs';
import path from 'node:path';
import fg from 'fast-glob';
import type { Tool } from './index.js';

const MAX_MATCHES = 200;
const MAX_FILES = 5000;
const MAX_FILE_SIZE = 1024 * 1024; // skip files >1MB

export const grepTool: Tool = {
  name: 'grep',
  description:
    'Search file contents with a regular expression. Returns matches as path:line: text. ' +
    'Scope the search with a glob pattern when you can.',
  parameters: {
    type: 'object',
    properties: {
      pattern: { type: 'string', description: 'JavaScript regular expression to search for.' },
      glob: { type: 'string', description: 'Glob to restrict files (default "**/*").' },
      ignore_case: { type: 'boolean', description: 'Case-insensitive search.' },
    },
    required: ['pattern'],
  },
  needsApproval: false,
  summarize: (args) =>
    `/${String(args.pattern ?? '')}/ in ${String(args.glob ?? '**/*')}`,
  async run(args, ctx) {
    const regex = new RegExp(String(args.pattern ?? ''), args.ignore_case ? 'i' : '');
    const files = await fg(String(args.glob ?? '**/*'), {
      cwd: ctx.cwd,
      ignore: ['**/node_modules/**', '**/.git/**', '**/dist/**', '**/build/**'],
      dot: false,
      onlyFiles: true,
    });

    const matches: string[] = [];
    let scanned = 0;
    for (const rel of files) {
      if (scanned++ >= MAX_FILES || matches.length >= MAX_MATCHES) break;
      const file = path.join(ctx.cwd, rel);
      let content: string;
      try {
        if (fs.statSync(file).size > MAX_FILE_SIZE) continue;
        content = fs.readFileSync(file, 'utf8');
      } catch {
        continue;
      }
      if (content.includes('\0')) continue; // binary
      const lines = content.split('\n');
      for (let i = 0; i < lines.length && matches.length < MAX_MATCHES; i++) {
        if (regex.test(lines[i])) {
          matches.push(`${rel}:${i + 1}: ${lines[i].trim().slice(0, 250)}`);
        }
      }
    }

    if (matches.length === 0) return 'No matches.';
    let out = matches.join('\n');
    if (matches.length >= MAX_MATCHES) out += `\n... [capped at ${MAX_MATCHES} matches]`;
    return out;
  },
};
