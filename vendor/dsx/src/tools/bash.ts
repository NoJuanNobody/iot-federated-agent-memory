import { exec } from 'node:child_process';
import type { Tool } from './index.js';
import { truncate } from './index.js';

export const bashTool: Tool = {
  name: 'bash',
  description:
    'Run a shell command in the working directory and return stdout/stderr. ' +
    'Use for git, package managers, builds, tests, and anything the other tools do not cover.',
  parameters: {
    type: 'object',
    properties: {
      command: { type: 'string', description: 'The shell command to execute.' },
      timeout_ms: {
        type: 'number',
        description: 'Optional timeout in milliseconds (default 120000, max 600000).',
      },
    },
    required: ['command'],
  },
  needsApproval: true,
  summarize: (args) => String(args.command ?? ''),
  run(args, ctx) {
    const command = String(args.command ?? '');
    const timeout = Math.min(Number(args.timeout_ms) || 120_000, 600_000);
    return new Promise((resolve) => {
      exec(
        command,
        { cwd: ctx.cwd, timeout, maxBuffer: 10 * 1024 * 1024, signal: ctx.signal },
        (error, stdout, stderr) => {
          let output = '';
          if (stdout) output += stdout;
          if (stderr) output += (output ? '\n--- stderr ---\n' : '') + stderr;
          if (error) {
            const reason = ctx.signal?.aborted
              ? 'interrupted by user'
              : error.killed
              ? `command timed out after ${timeout}ms`
              : `exit code ${error.code ?? 'unknown'}`;
            output += `${output ? '\n' : ''}[${reason}]`;
          }
          resolve(truncate(output || '(no output)'));
        },
      );
    });
  },
};
