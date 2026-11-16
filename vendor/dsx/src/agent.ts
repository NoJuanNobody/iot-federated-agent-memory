import OpenAI from 'openai';
import type { ChatCompletionMessageParam, ChatCompletionMessageToolCall } from 'openai/resources/chat/completions';
import type { Tool, ToolContext } from './tools/index.js';
import { toolSchemas, truncate } from './tools/index.js';
import { matchPermission, type PermissionRules } from './config.js';

const MAX_TURNS = 40;
/** Compact when estimated prompt tokens exceed this fraction of the budget. */
const COMPACT_THRESHOLD = 0.7;
/** How many recent messages to keep verbatim through a compaction. */
const KEEP_RECENT = 6;

/** Transient-failure retry budget for model calls. */
const MAX_RETRIES = 3;
const RETRY_BASE_MS = 500;
const RETRY_MAX_MS = 8000;

const COMPACT_SYSTEM_PROMPT = `You compress the history of a coding-agent conversation so the agent can continue with less context. Summarize faithfully and specifically:
- the user's goals and any decisions made
- files examined or modified (exact paths) and what changed
- commands run and their key outcomes
- the current state of the task and unresolved next steps
Keep it under 500 words. Output only the summary.`;

export type AgentEvent =
  | { type: 'text-delta'; text: string }
  | { type: 'reasoning-delta'; text: string }
  | { type: 'text-done'; text: string }
  | { type: 'tool-start'; name: string; summary: string }
  | { type: 'tool-end'; name: string; summary: string; result: string; isError: boolean }
  | { type: 'info'; text: string }
  | { type: 'error'; message: string };

export interface AgentIO {
  onEvent(event: AgentEvent): void;
  requestApproval(req: {
    tool: string;
    summary: string;
    preview?: string;
  }): Promise<'yes' | 'no' | 'always' | 'persist'>;
}

interface PendingToolCall {
  id: string;
  name: string;
  args: string;
}

/** Prompt + completion token counts the API reported for a span of work. */
export interface TokenUsage {
  promptTokens: number;
  completionTokens: number;
}

export class Agent {
  private messages: ChatCompletionMessageParam[] = [];
  private alwaysAllowed = new Set<string>();
  /** Prompt tokens reported by the API on the most recent completion. */
  private lastPromptTokens = 0;
  /** Cumulative prompt/completion tokens for the most recent user turn (#31). */
  private lastTurn: TokenUsage = { promptTokens: 0, completionTokens: 0 };
  /**
   * When a heavy tool runs (see heavyTools), the NEXT completion routes to this
   * reasoning model instead of `model`. One-shot per heavy call, then reverts so
   * normal chat is never affected (#31).
   */
  private routeNextTo: string | null = null;

  constructor(
    private client: OpenAI,
    public model: string,
    private systemPrompt: string,
    public readonly tools: Tool[],
    private ctx: ToolContext,
    private contextTokens = 64_000,
    private permissions: PermissionRules = { allow: [], deny: [] },
    private onPersistRule: (rule: string) => void = () => {},
    private onRecord: (message: ChatCompletionMessageParam) => void = () => {},
    /** Tool names whose results should be reasoned about by `reasoningModel`. */
    private heavyTools: Set<string> = new Set(),
    /** Reasoning model slug heavy tasks auto-route to; null disables routing. */
    private reasoningModel: string | null = null,
  ) {}

  /** Token usage (prompt + completion) accumulated over the most recent turn (#31). */
  lastTurnUsage(): TokenUsage {
    return { ...this.lastTurn };
  }

  /** Append a message to history and notify the recorder (for session persistence). */
  private record(message: ChatCompletionMessageParam): void {
    this.messages.push(message);
    this.onRecord(message);
  }

  /** Seed history from a restored session. Does NOT re-record (already persisted). */
  restore(messages: ChatCompletionMessageParam[]): void {
    this.messages = [...messages];
    this.lastPromptTokens = 0;
  }

  clearHistory(): void {
    this.messages = [];
    this.lastPromptTokens = 0;
  }

  /**
   * Best available estimate of the next call's prompt size: the API's real
   * count when we have one (lags by one completion), else chars/4.
   */
  usedTokens(): number {
    if (this.lastPromptTokens > 0) return this.lastPromptTokens;
    return Math.ceil((this.systemPrompt.length + JSON.stringify(this.messages).length) / 4);
  }

  /** The configured context-window budget in tokens (for the status line). */
  contextBudget(): number {
    return this.contextTokens;
  }

  /** Run one user turn: stream model output, execute tool calls, loop until plain text. */
  async run(userText: string, io: AgentIO, signal?: AbortSignal): Promise<void> {
    this.record({ role: 'user', content: userText });
    // Reset per-turn token accounting so the status line shows THIS turn (#31).
    this.lastTurn = { promptTokens: 0, completionTokens: 0 };

    try {
      for (let turn = 0; turn < MAX_TURNS; turn++) {
        if (signal?.aborted) break;
        if (this.usedTokens() > this.contextTokens * COMPACT_THRESHOLD) {
          await this.compact(io);
        }

        let text: string;
        let toolCalls: PendingToolCall[];
        try {
          ({ text, toolCalls } = await this.streamCompletion(io, signal));
        } catch (err) {
          // Aborted before the assistant message was pushed — history stays clean.
          if (isAbort(err)) break;
          throw err;
        }

        this.record({
          role: 'assistant',
          content: text || null,
          ...(toolCalls.length > 0 && {
            tool_calls: toolCalls.map(
              (tc): ChatCompletionMessageToolCall => ({
                id: tc.id,
                type: 'function',
                function: { name: tc.name, arguments: tc.args },
              }),
            ),
          }),
        });

        if (text) io.onEvent({ type: 'text-done', text });
        if (toolCalls.length === 0) return;

        for (const tc of toolCalls) {
          // Once interrupted, pair every remaining tool_call with a synthetic
          // result so the next turn has no dangling tool_calls (which 400 the API).
          if (signal?.aborted) {
            this.record({ role: 'tool', tool_call_id: tc.id, content: '[interrupted by user]' });
            continue;
          }
          const result = await this.executeToolCall(tc, io, signal);
          this.record({ role: 'tool', tool_call_id: tc.id, content: result });
          // Auto-route: a known heavy tool's result should be reasoned about by
          // the configured reasoning model. Arm a one-shot override for the next
          // completion only; normal chat keeps the user's selected model (#31).
          if (this.reasoningModel && this.heavyTools.has(tc.name)) {
            this.routeNextTo = this.reasoningModel;
            io.onEvent({
              type: 'info',
              text: `Heavy task ${tc.name} — routing next step to ${this.reasoningModel}.`,
            });
          }
        }
        if (signal?.aborted) break;
      }
      if (signal?.aborted) {
        io.onEvent({ type: 'info', text: 'Interrupted.' });
        return;
      }
      io.onEvent({ type: 'error', message: `Stopped after ${MAX_TURNS} tool turns.` });
    } catch (err) {
      if (isAbort(err) || signal?.aborted) {
        io.onEvent({ type: 'info', text: 'Interrupted.' });
        return;
      }
      io.onEvent({ type: 'error', message: err instanceof Error ? err.message : String(err) });
    }
  }

  private async streamCompletion(
    io: AgentIO,
    signal?: AbortSignal,
  ): Promise<{ text: string; toolCalls: PendingToolCall[] }> {
    let emptyRetried = false;
    for (;;) {
      const result = await this.withRetry(io, signal, () => this.streamOnce(io, signal));
      if (!signal?.aborted && result.text === '' && result.toolCalls.length === 0 && !emptyRetried) {
        emptyRetried = true;
        io.onEvent({ type: 'info', text: 'Model returned an empty response — retrying once…' });
        continue;
      }
      return result;
    }
  }

  /** One streamed completion attempt: open the stream and drain it. */
  private async streamOnce(
    io: AgentIO,
    signal?: AbortSignal,
  ): Promise<{ text: string; toolCalls: PendingToolCall[] }> {
    // A heavy tool may have armed a one-shot reasoning-model override; consume
    // it here so exactly this completion uses it, then revert to `model` (#31).
    const model = this.routeNextTo ?? this.model;
    this.routeNextTo = null;
    const stream = await this.client.chat.completions.create(
      {
        model,
        messages: [{ role: 'system', content: this.systemPrompt }, ...this.messages],
        tools: toolSchemas(this.tools),
        stream: true,
        stream_options: { include_usage: true },
      },
      { signal },
    );

    let text = '';
    const toolCalls: PendingToolCall[] = [];

    for await (const chunk of stream) {
      if (chunk.usage?.prompt_tokens) {
        this.lastPromptTokens = chunk.usage.prompt_tokens;
        // Accumulate this turn's usage for last-turn cost estimation (#31).
        this.lastTurn.promptTokens += chunk.usage.prompt_tokens;
      }
      if (chunk.usage?.completion_tokens) {
        this.lastTurn.completionTokens += chunk.usage.completion_tokens;
      }
      const delta = chunk.choices[0]?.delta;
      if (!delta) continue;

      // Reasoning models stream their chain of thought in a non-standard field:
      // OpenRouter normalizes it to `reasoning`; DeepSeek direct uses `reasoning_content`.
      const d = delta as { reasoning?: string; reasoning_content?: string };
      const reasoning = d.reasoning ?? d.reasoning_content;
      if (reasoning) io.onEvent({ type: 'reasoning-delta', text: reasoning });

      if (delta.content) {
        text += delta.content;
        io.onEvent({ type: 'text-delta', text: delta.content });
      }

      for (const d of delta.tool_calls ?? []) {
        const slot = (toolCalls[d.index] ??= { id: '', name: '', args: '' });
        if (d.id) slot.id = d.id;
        if (d.function?.name) slot.name += d.function.name;
        if (d.function?.arguments) slot.args += d.function.arguments;
      }
    }

    return { text, toolCalls: toolCalls.filter(Boolean) };
  }

  /**
   * Retry a model call through transient failures (429, 5xx, network blips)
   * with exponential backoff + jitter, honoring Retry-After when present.
   * Gives up after MAX_RETRIES; non-retryable errors (400/401) rethrow at once.
   */
  private async withRetry<T>(io: AgentIO, signal: AbortSignal | undefined, fn: () => Promise<T>): Promise<T> {
    for (let attempt = 0; ; attempt++) {
      try {
        return await fn();
      } catch (err) {
        // A user interrupt is never a transient failure — surface it at once.
        if (signal?.aborted || isAbort(err)) throw err;
        const info = classifyError(err);
        if (!info.retryable || attempt >= MAX_RETRIES) throw err;
        const delay = Math.min(info.retryAfterMs ?? backoffDelay(attempt), RETRY_MAX_MS);
        io.onEvent({
          type: 'info',
          text: `Model request failed (${describeError(err)}) — retrying ${attempt + 1}/${MAX_RETRIES} in ${(delay / 1000).toFixed(1)}s…`,
        });
        await sleep(delay);
      }
    }
  }

  private async executeToolCall(tc: PendingToolCall, io: AgentIO, signal?: AbortSignal): Promise<string> {
    const tool = this.tools.find((t) => t.name === tc.name);
    if (!tool) {
      return `Error: unknown tool "${tc.name}"`;
    }

    let args: Record<string, unknown>;
    try {
      args = tc.args ? JSON.parse(tc.args) : {};
    } catch {
      return `Error: tool arguments were not valid JSON: ${truncate(tc.args, 500)}`;
    }

    const summary = tool.summarize(args);

    const perm = matchPermission(this.permissions, tool.name, summary);
    if (perm === 'deny') {
      const result = `Blocked by a deny rule in .dsx/settings.json — ${tool.name}(${summary}) was not run.`;
      io.onEvent({ type: 'tool-end', name: tc.name, summary, result, isError: true });
      return result;
    }

    if (tool.needsApproval && perm !== 'allow' && !this.alwaysAllowed.has(tool.name)) {
      let preview: string | undefined;
      try {
        preview = await tool.preview?.(args, this.ctx);
      } catch {
        preview = undefined;
      }
      const decision = await io.requestApproval({ tool: tool.name, summary, preview });
      if (decision === 'no') {
        const result = 'User denied permission for this tool call.';
        io.onEvent({ type: 'tool-end', name: tc.name, summary, result, isError: true });
        return result;
      }
      if (decision === 'always') this.alwaysAllowed.add(tool.name);
      if (decision === 'persist') {
        const rule = `${tool.name}(${summary})`;
        this.permissions.allow.push(rule);
        this.onPersistRule(rule);
        io.onEvent({ type: 'info', text: `Saved allow rule to .dsx/settings.json: ${rule}` });
      }
    }

    io.onEvent({ type: 'tool-start', name: tc.name, summary });
    try {
      // Thread the active IO's approval callback so tools that spawn their own
      // child loops (the write-capable `delegate` subagent) can route the
      // child's mutations back to this same user approval prompt.
      const result = await tool.run(args, {
        ...this.ctx,
        signal,
        requestApproval: (req) => io.requestApproval(req),
      });
      io.onEvent({ type: 'tool-end', name: tc.name, summary, result, isError: false });
      return result;
    } catch (err) {
      const result = `Error: ${err instanceof Error ? err.message : String(err)}`;
      io.onEvent({ type: 'tool-end', name: tc.name, summary, result, isError: true });
      return result;
    }
  }

  /**
   * Shrink history: summarize everything before a safe cut point into one
   * message, keeping the most recent messages verbatim. Falls back to
   * trimming old tool results when no safe cut exists.
   */
  async compact(io: AgentIO): Promise<void> {
    const before = this.usedTokens();
    const cut = this.findCutIndex();

    if (cut === null) {
      const trimmed = this.trimOldToolResults();
      this.lastPromptTokens = 0;
      if (trimmed > 0) {
        io.onEvent({ type: 'info', text: `Compacted: trimmed ${trimmed} old tool result(s).` });
      }
      return;
    }

    const head = this.messages.slice(0, cut);
    const tail = this.messages.slice(cut);

    const summaryResponse = await this.withRetry(io, undefined, () =>
      this.client.chat.completions.create({
        model: this.model,
        messages: [
          { role: 'system', content: COMPACT_SYSTEM_PROMPT },
          { role: 'user', content: renderForSummary(head) },
        ],
      }),
    );
    const summary = summaryResponse.choices[0]?.message?.content?.trim();
    if (!summary) {
      io.onEvent({ type: 'info', text: 'Compaction skipped: summarizer returned nothing.' });
      return;
    }

    this.messages = [
      {
        role: 'user',
        content: `[Earlier conversation was compacted to save context. Summary of everything so far:]\n\n${summary}`,
      },
      ...tail,
    ];
    this.lastPromptTokens = 0;
    const after = this.usedTokens();
    io.onEvent({
      type: 'info',
      text: `Compacted context: ~${Math.round(before / 1000)}k → ~${Math.round(after / 1000)}k tokens.`,
    });
  }

  /**
   * Largest index that keeps ~KEEP_RECENT recent messages and doesn't split
   * an assistant tool_calls message from its tool results (i.e. never cut
   * directly before a `tool` message). Null when there's nothing worth cutting.
   */
  private findCutIndex(): number | null {
    let cut = this.messages.length - KEEP_RECENT;
    while (cut > 0 && cut < this.messages.length && this.messages[cut].role === 'tool') {
      cut++;
    }
    return cut >= 4 && cut < this.messages.length ? cut : null;
  }

  /** Replace the contents of all but the most recent tool results with a stub. */
  private trimOldToolResults(): number {
    let trimmed = 0;
    const cutoff = this.messages.length - KEEP_RECENT;
    for (let i = 0; i < cutoff; i++) {
      const m = this.messages[i];
      if (m.role === 'tool' && typeof m.content === 'string' && m.content.length > 300) {
        m.content = `${m.content.slice(0, 200)}\n[trimmed during compaction — re-run the tool if needed]`;
        trimmed++;
      }
    }
    return trimmed;
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** True when an error is the result of a user-initiated abort. */
function isAbort(err: unknown): boolean {
  return err instanceof OpenAI.APIUserAbortError || (err instanceof Error && err.name === 'AbortError');
}

/** Exponential backoff with jitter: ~0.5s, 1s, 2s, … plus up to 0.5s. */
function backoffDelay(attempt: number): number {
  return RETRY_BASE_MS * 2 ** attempt + Math.floor(Math.random() * RETRY_BASE_MS);
}

/** Decide whether a failed model call is worth retrying, and for how long. */
function classifyError(err: unknown): { retryable: boolean; retryAfterMs?: number } {
  // APIConnectionError (and its APITimeoutError subclass) carry no status but
  // are exactly the transient network blips worth retrying. Check first.
  if (err instanceof OpenAI.APIConnectionError) return { retryable: true };
  if (err instanceof OpenAI.APIError) {
    const status = err.status;
    if (status === 429 || (typeof status === 'number' && status >= 500)) {
      return { retryable: true, retryAfterMs: parseRetryAfter(err.headers) };
    }
  }
  return { retryable: false };
}

function describeError(err: unknown): string {
  if (err instanceof OpenAI.APIError && typeof err.status === 'number') return `HTTP ${err.status}`;
  if (err instanceof Error) return err.name || 'network error';
  return 'unknown error';
}

/** Parse a Retry-After header (delta-seconds or HTTP date) into milliseconds. */
function parseRetryAfter(headers: unknown): number | undefined {
  const raw = readHeader(headers, 'retry-after');
  if (!raw) return undefined;
  const seconds = Number(raw);
  if (Number.isFinite(seconds)) return seconds * 1000;
  const when = Date.parse(raw);
  return Number.isFinite(when) ? Math.max(0, when - Date.now()) : undefined;
}

/** Read a header from either a Headers instance or a plain record. */
function readHeader(headers: unknown, name: string): string | undefined {
  if (!headers) return undefined;
  if (typeof (headers as { get?: unknown }).get === 'function') {
    return (headers as Headers).get(name) ?? undefined;
  }
  const rec = headers as Record<string, string>;
  return rec[name] ?? rec[name.toLowerCase()];
}

/** Flatten messages into a plain transcript the summarizer can read. */
function renderForSummary(messages: ChatCompletionMessageParam[]): string {
  const lines: string[] = [];
  for (const m of messages) {
    if (m.role === 'user') {
      lines.push(`USER: ${m.content}`);
    } else if (m.role === 'assistant') {
      if (m.content) lines.push(`ASSISTANT: ${m.content}`);
      for (const tc of m.tool_calls ?? []) {
        if (tc.type === 'function') {
          lines.push(`ASSISTANT called ${tc.function.name}(${truncate(tc.function.arguments, 200)})`);
        }
      }
    } else if (m.role === 'tool' && typeof m.content === 'string') {
      lines.push(`TOOL RESULT: ${truncate(m.content, 400)}`);
    }
  }
  return lines.join('\n');
}
