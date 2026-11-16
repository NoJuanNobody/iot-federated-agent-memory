import OpenAI from 'openai';
import { Agent, type AgentEvent, type AgentIO } from '../agent.js';
import type { Tool, ToolContext } from './index.js';
import { truncate } from './index.js';

/** Cap on concurrently running subagents so parallel delegations stay bounded. */
const MAX_CONCURRENT_CHILDREN = 4;
/** Each child's conclusion is truncated to this many chars before returning. */
const MAX_RESULT_CHARS = 8000;

export interface AgentToolDeps {
  client: OpenAI;
  model: string;
  /** The parent's full tool registry; filtered to read-only for the child. */
  tools: Tool[];
  ctx: ToolContext;
}

/**
 * A simple counting semaphore so that, however the nyx-harness schedules `agent`
 * calls (sequentially in the parent loop, or in parallel), no more than
 * MAX_CONCURRENT_CHILDREN child loops run at once.
 */
class Semaphore {
  private active = 0;
  private waiters: Array<() => void> = [];
  constructor(private readonly max: number) {}

  async acquire(): Promise<void> {
    if (this.active < this.max) {
      this.active++;
      return;
    }
    await new Promise<void>((resolve) => this.waiters.push(resolve));
    this.active++;
  }

  release(): void {
    this.active--;
    const next = this.waiters.shift();
    if (next) next();
  }
}

const semaphore = new Semaphore(MAX_CONCURRENT_CHILDREN);

/**
 * Mutating children run ONE at a time. A write-capable child surfaces each
 * mutation through the parent's single Ink approval prompt; allowing several
 * concurrently would let their prompts collide on the same TUI. A size-1
 * semaphore serializes them (and the whole run, including approvals) so the
 * user only ever sees one delegated approval at a time.
 */
const writeSemaphore = new Semaphore(1);

const CHILD_SYSTEM_PROMPT = `You are a focused sub-agent spawned by a parent coding agent to handle one scoped, read-only task.

- You have read-only tools (read files, list, grep, search, fetch). You cannot modify files or run mutating commands.
- Investigate efficiently, then STOP. Do not ask the parent questions — it cannot answer.
- Your FINAL message is the only thing the parent receives. Make it a self-contained, concise conclusion that directly answers the task: include exact file paths, names, and the key facts. Omit your investigation play-by-play.`;

const WRITE_CHILD_SYSTEM_PROMPT = `You are a focused sub-agent spawned by a parent coding agent to carry out one scoped task that MAY modify the codebase.

- You have full tools: read AND write (edit files, run bash, etc.). Each mutating action is surfaced to the user for approval — proceed normally; the user gates writes.
- Stay strictly within the delegated task. Do NOT spawn further sub-agents.
- Work efficiently, then STOP. Do not ask the parent questions — it cannot answer.
- Your FINAL message is the only thing the parent receives. Make it a self-contained, concise conclusion that states what you DID and lists every file you changed (exact paths). Omit your step-by-step.`;

/**
 * Run a fresh child Agent loop over `task` with the given tools, system prompt,
 * and child IO, then return its final conclusion (truncated). Shared by both
 * the read-only `agent` tool and the write-capable `delegate` tool.
 */
async function runChild(
  deps: AgentToolDeps,
  systemPrompt: string,
  childTools: Tool[],
  task: string,
  io: AgentIO,
  signal: AbortSignal | undefined,
): Promise<void> {
  const child = new Agent(
    deps.client,
    deps.model,
    systemPrompt,
    childTools,
    // Inherit cwd/skills/keys; thread the (possibly fresh) signal from this call.
    { ...deps.ctx, signal },
  );
  await child.run(task, io, signal);
}

/**
 * Build the subagent delegation tools:
 *  - `agent`   — read-only delegation (unchanged): the child is restricted to
 *                non-mutating tools and every approval is denied.
 *  - `delegate` — write-capable delegation (#26): the child may use mutating
 *                tools, and each mutation routes to the PARENT's approval flow
 *                so the user confirms every change.
 *
 * In both cases the child's tool calls never enter the parent's history — the
 * parent context grows by roughly one message (the final conclusion). The child
 * cannot recurse: both `agent` and `delegate` are excluded from its tool set.
 */
export function makeAgentTool(deps: AgentToolDeps): Tool[] {
  // Read-only subset: keep tools that run freely, drop both delegation tools.
  const readOnlyTools = deps.tools.filter(
    (t) => !t.needsApproval && t.name !== 'agent' && t.name !== 'delegate',
  );
  // Write subset: keep everything EXCEPT the delegation tools (recursion guard:
  // a child still cannot spawn further mutating children).
  const writeTools = deps.tools.filter((t) => t.name !== 'agent' && t.name !== 'delegate');

  const agentTool: Tool = {
    name: 'agent',
    description:
      'Delegate a focused, read-only sub-task to an isolated sub-agent and receive only its final conclusion. ' +
      'Use this to investigate questions like "find where X is implemented" without filling your own context with the search steps. ' +
      'The task must be fully self-contained — the sub-agent shares your working directory but none of your conversation. ' +
      'The sub-agent is read-only: it cannot modify files or run mutating commands. You may run several in parallel for independent questions.',
    parameters: {
      type: 'object',
      properties: {
        task: {
          type: 'string',
          description:
            'A complete, standalone instruction for the sub-agent, including any context it needs. ' +
            'State exactly what conclusion you want back (e.g. "Report just the file path").',
        },
      },
      required: ['task'],
    },
    needsApproval: false,
    summarize: (args) => truncate(String(args.task ?? ''), 80),
    async run(args, ctx) {
      const task = String(args.task ?? '').trim();
      if (!task) return 'Error: agent requires a non-empty "task".';

      await semaphore.acquire();
      try {
        // Silent IO: capture the latest final assistant text; deny any approval
        // (children are read-only, so this should never trigger).
        let finalText = '';
        let lastError = '';
        const io: AgentIO = {
          onEvent(event: AgentEvent) {
            if (event.type === 'text-done') finalText = event.text;
            else if (event.type === 'error') lastError = event.message;
          },
          async requestApproval() {
            return 'no';
          },
        };

        await runChild(deps, CHILD_SYSTEM_PROMPT, readOnlyTools, task, io, ctx.signal);

        const conclusion = finalText.trim();
        if (conclusion) return truncate(conclusion, MAX_RESULT_CHARS);
        if (lastError) return `Sub-agent failed: ${lastError}`;
        return 'Sub-agent finished without producing a conclusion.';
      } finally {
        semaphore.release();
      }
    },
  };

  const delegateTool: Tool = {
    name: 'delegate',
    description:
      'Delegate a focused, write-capable sub-task to an isolated sub-agent and receive only its final conclusion. ' +
      'Unlike `agent`, the sub-agent CAN modify files and run mutating commands to carry out delegated work. ' +
      'Each change it makes is still surfaced to YOU/the user for approval — nothing is auto-applied. ' +
      'The task must be fully self-contained — the sub-agent shares your working directory but none of your conversation. ' +
      'Only ONE write-capable delegation runs at a time. The sub-agent reports the files it changed.',
    parameters: {
      type: 'object',
      properties: {
        task: {
          type: 'string',
          description:
            'A complete, standalone instruction for the sub-agent, including any context it needs and exactly what to change. ' +
            'The sub-agent will report what it did and which files it touched.',
        },
      },
      required: ['task'],
    },
    // The delegate call itself is benign; the child surfaces its own mutations
    // for approval, so the parent need not gate the delegation call.
    needsApproval: false,
    summarize: (args) => truncate(String(args.task ?? ''), 80),
    async run(args, ctx) {
      const task = String(args.task ?? '').trim();
      if (!task) return 'Error: delegate requires a non-empty "task".';

      // The parent's live approval callback is injected by the Agent. Without
      // it (e.g. print mode with no approver) we cannot safely route mutations.
      const parentApproval = ctx.requestApproval;
      if (!parentApproval) {
        return 'Error: delegate is unavailable here — no approval channel to route the sub-agent\'s changes through.';
      }

      // Serialize write-capable children to one at a time so their approval
      // prompts never collide (see writeSemaphore above).
      await writeSemaphore.acquire();
      try {
        let finalText = '';
        let lastError = '';
        const io: AgentIO = {
          onEvent(event: AgentEvent) {
            if (event.type === 'text-done') finalText = event.text;
            else if (event.type === 'error') lastError = event.message;
          },
          // Route every child approval to the PARENT's prompt so the user
          // confirms each mutation (never silently auto-approved).
          requestApproval: parentApproval,
        };

        await runChild(deps, WRITE_CHILD_SYSTEM_PROMPT, writeTools, task, io, ctx.signal);

        const conclusion = finalText.trim();
        if (conclusion) return truncate(conclusion, MAX_RESULT_CHARS);
        if (lastError) return `Sub-agent failed: ${lastError}`;
        return 'Sub-agent finished without producing a conclusion.';
      } finally {
        writeSemaphore.release();
      }
    },
  };

  return [agentTool, delegateTool];
}
