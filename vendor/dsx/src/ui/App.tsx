import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Box, Static, Text, useApp, useInput, useStdout } from 'ink';
import TextInput from 'ink-text-input';
import Spinner from 'ink-spinner';
import type { Agent, AgentEvent } from '../agent.js';
import { SUGGESTED_MODELS, loadModelProfiles, saveRating, type RoutingSettings } from '../config.js';
import type { Skill } from '../skills.js';
import { findSkill, findSubcommand, skillInvocationMessage } from '../skills.js';
import { fetchModels, type ModelInfo } from '../models.js';
import {
  fetchCredits,
  formatCredits,
  formatCreditsShort,
  loadPersistedCredits,
  savePersistedCredits,
  estimateTurnCost,
  formatCostShort,
  type CreditBalance,
} from '../credits.js';
import { currentBranch } from '../git.js';
import { ModelPicker } from './ModelPicker.js';
import { McpManager } from './McpManager.js';
import { listMcpServers, addMcpServer, removeMcpServer, type McpServerConfig } from '../mcp.js';
import {
  Autocomplete,
  activeToken,
  createFileProvider,
  createSlashProvider,
  type AutocompleteProvider,
  type Suggestion,
} from './Autocomplete.js';
import { StatusLine } from './StatusLine.js';
import { LightTable, type FileEntry } from './LightTable.js';
import { Markdown, MarkdownViewer, FormattedText } from './MarkdownView.js';
import { DiffView, looksLikeDiff } from './DiffView.js';
import { DocPreviewView } from './DocPreviewView.js';
import { decodeDocPreview } from './docPreview.js';
import { decodeCodeDiff } from './codeDiff.js';
import {
  HistoryItemView,
  capLines,
  READ_PREVIEW_LINES,
  READ_TOOL_NAME,
  PREVIEW_LINES,
  type HistoryItem,
} from './items.js';
import { theme } from './theme.js';
import { syncTrackedDocs, trackedDocCount } from '../tools/nyxSync.js';
import { fetchDocRaw } from '../tools/nyx.js';
import type { ToolContext } from '../tools/index.js';

interface Approval {
  tool: string;
  summary: string;
  preview?: string;
  resolve: (decision: 'yes' | 'no' | 'always' | 'persist') => void;
}

interface Props {
  agent: Agent;
  skills: Skill[];
  /** OpenRouter base URL, used to fetch the model catalog and account credits. */
  baseURL: string;
  /** OpenRouter API key, used to authenticate the /credits balance lookup. */
  apiKey: string;
  /** Working directory, shown in the status line and used to read the git branch. */
  cwd: string;
  /** Roll over to a new session file when history is cleared. */
  onClear?: () => void;
  /** Persist the last-used model slug across sessions (#33). */
  onSaveModel?: (model: string) => void;
  /** Routing settings: budget guardrails, free-tier fallback, heavy-task routing (#31). */
  routing?: RoutingSettings;
  /**
   * Extra autocomplete providers registered at runtime (#42). These are tried
   * before the built-in slash + file providers, so a custom provider can claim
   * an input shape ahead of the defaults.
   */
  autocompleteProviders?: AutocompleteProvider[];
  /**
   * Nyx backend config for the background doc-sync poller (#67). When the API
   * key is absent the poller no-ops; when present it refreshes locally-pulled
   * docs from the cloud on an interval.
   */
  nyx?: { apiUrl?: string; apiKey?: string; teamId?: string };
}

/**
 * Background sync interval in ms (#67). Configurable via NYX_SYNC_INTERVAL_MS;
 * defaults to 5 minutes. Values below 10s are clamped up so a typo can't spin.
 */
function syncIntervalMs(): number {
  const raw = Number(process.env.NYX_SYNC_INTERVAL_MS);
  if (Number.isFinite(raw) && raw > 0) return Math.max(10_000, raw);
  return 5 * 60_000;
}

const HELP_TEXT = `Commands:
  /help            show this help
  /skills          list installed skills
  /<skill> [args]  invoke a skill directly
  /init            explore the project and write a starter DSX.md
  /model [slug]    switch model by slug, or no arg to browse/search the list
  /mcp             add, list, or remove MCP servers (.dsx/mcp.json)
  /files [subdir]  open interactive light-table file browser
                   (subdirectory optional; default is cwd)
  /view <path>     open markdown viewer for a file
                   (raw text shown for non-markdown files)
  /compact         summarize older history to free up context
  /credits         show OpenRouter account balance
  /rate <1-5> [note]  rate the last turn's quality (saved to ~/.dsx/feedback.json)
  /expand [n]      print the full un-truncated output of the most recent
                   capped item (or the nth, counting back) to scrollback
  /clear           clear conversation history
  /exit            quit

Approvals: y = allow once, a = always allow this tool, p = persist allow rule to .dsx/settings.json, n = deny
Press Esc to interrupt the current turn. Esc also closes an overlay.`;

/**
 * Built-in slash commands, used both by /help and the autocomplete dropdown's
 * slash-command provider. Skills (custom slash commands) are appended at
 * runtime from the loaded skill list.
 */
const BUILTIN_COMMANDS: { name: string; description: string }[] = [
  { name: 'help', description: 'show this help' },
  { name: 'skills', description: 'list installed skills' },
  { name: 'init', description: 'explore the project and write a starter DSX.md' },
  { name: 'model', description: 'switch model by slug, or browse/search the list' },
  { name: 'mcp', description: 'add, list, or remove MCP servers' },
  { name: 'files', description: 'open interactive light-table file browser' },
  { name: 'view', description: 'open markdown viewer for a file' },
  { name: 'compact', description: 'summarize older history to free up context' },
  { name: 'credits', description: 'show OpenRouter account balance' },
  { name: 'rate', description: "rate the last turn's quality (1-5, saved to feedback.json)" },
  { name: 'expand', description: 'print the full un-truncated output of a capped item' },
  { name: 'clear', description: 'clear conversation history' },
  { name: 'exit', description: 'quit' },
];

/**
 * Max rendered terminal rows the live streaming / reasoning previews may
 * occupy (see tailByRows, which bounds by wrapped height — not chars or
 * newlines). The growing dynamic frame was what made Ink repaint (and flicker)
 * once output passed the terminal height; the complete message is committed to
 * <Static> on `text-done`, so capping the live preview loses nothing.
 */
const STREAM_TAIL_LINES = 12;
const REASONING_TAIL_LINES = 3;

/**
 * Take the tail of `text` bounded to ~`maxRows` *rendered* terminal rows.
 * Capping by character count alone doesn't bound height (many short lines use
 * few chars but many rows); capping by newline count alone doesn't either (one
 * long paragraph is a single line that wraps to many rows). This walks lines
 * from the end, counting each line's wrapped row span (ceil(len/cols)), so the
 * live preview's height stays bounded regardless of line shape — which is what
 * keeps the dynamic frame from exceeding terminal height and flickering.
 */
function tailByRows(text: string, cols: number, maxRows: number): { tail: string; truncated: boolean } {
  const lines = text.split('\n');
  const out: string[] = [];
  let rows = 0;
  let truncated = false;
  for (let i = lines.length - 1; i >= 0; i--) {
    const line = lines[i];
    const lineRows = Math.max(1, Math.ceil(line.length / cols));
    if (rows + lineRows > maxRows) {
      // If even a single line overflows the budget, keep only its last rows.
      if (out.length === 0) out.unshift(line.slice(-maxRows * cols));
      truncated = true;
      break;
    }
    out.unshift(line);
    rows += lineRows;
  }
  return { tail: out.join('\n'), truncated };
}

const INIT_PROMPT = `Explore this project and create a concise DSX.md file at the repository root.
Read the package manifest(s), build/test configuration, the README, and enough of the
source tree to understand the layout. The DSX.md should capture: what the project is,
the tech stack, how to build/test/run it, and any conventions a contributor must follow
(so a future session doesn't have to rediscover them). Write it with write_file — keep it
short and high-signal.`;

export function App({ agent, skills, baseURL, apiKey, cwd, onClear, onSaveModel, routing, autocompleteProviders, nyx }: Props) {
  const { exit } = useApp();
  const { stdout } = useStdout();
  const [model, setModel] = useState(agent.model);
  const [items, setItems] = useState<HistoryItem[]>([
    { kind: 'info', text: `nyx harness · ${agent.model} · ${skills.length} skill(s) · /help for commands` },
  ]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [streamText, setStreamText] = useState('');
  const [reasoningText, setReasoningText] = useState('');
  const [runningTool, setRunningTool] = useState<string | null>(null);
  const [approval, setApproval] = useState<Approval | null>(null);
  const approvalRef = useRef<Approval | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const [picker, setPicker] = useState<ModelInfo[] | null>(null);
  const modelsCacheRef = useRef<ModelInfo[] | null>(null);
  const [credits, setCredits] = useState<string | null>(() => {
    const saved = loadPersistedCredits();
    return saved ? formatCreditsShort(saved) : null;
  });
  // Cost tracking (#31): last-turn and cumulative session cost, plus the model
  // that produced the last turn (used by /rate to attribute the rating).
  const [lastTurnCost, setLastTurnCost] = useState<string | null>(null);
  const [sessionCost, setSessionCost] = useState<number>(0);
  const lastTurnModelRef = useRef<string>(agent.model);
  // Last known credit balance, used for free-tier fallback decisions (#31).
  const lastBalanceRef = useRef<CreditBalance | null>(null);
  // True once we've already downgraded to the free model, so we warn only once.
  const downgradedRef = useRef(false);
  const [branch, setBranch] = useState<string | undefined>(() => currentBranch(cwd));
  const [lightTable, setLightTable] = useState<{ entries: FileEntry[]; subdir: string } | null>(null);
  const [viewer, setViewer] = useState<{ path: string; content: string } | null>(null);
  const [mcpManager, setMcpManager] = useState<Record<string, McpServerConfig> | null>(null);

  // Autocomplete dropdown (#42): suggestions for the current input, the
  // highlighted row, and whether the user dismissed it (Esc) for this token.
  const [acIndex, setAcIndex] = useState(0);
  const [acSuggestions, setAcSuggestions] = useState<Suggestion[]>([]);
  const [acDismissed, setAcDismissed] = useState(false);
  const acProviders = useMemo<AutocompleteProvider[]>(
    () => [
      ...(autocompleteProviders ?? []),
      createSlashProvider(BUILTIN_COMMANDS, skills),
      createFileProvider(cwd),
    ],
    [autocompleteProviders, skills, cwd],
  );
  // The dropdown is live only when not busy, no overlay is open, input is
  // non-empty, the user hasn't dismissed it, and we actually have suggestions.
  const acOpen =
    !busy &&
    !approval &&
    !picker &&
    !lightTable &&
    !viewer &&
    !mcpManager &&
    input.length > 0 &&
    !acDismissed &&
    acSuggestions.length > 0;
  // Mirror acOpen in a ref so handleSubmit (called by ink-text-input on Enter)
  // can suppress submission when the dropdown is consuming the Enter key.
  const acOpenRef = useRef(false);
  acOpenRef.current = acOpen;

  // Refresh the status-line data (credits + branch). Credits are fetched at
  // startup and after each turn; a failed fetch keeps the last known value.
  const refreshStatus = useCallback(async () => {
    setBranch(currentBranch(cwd));
    try {
      const balance = await fetchCredits(baseURL, apiKey);
      lastBalanceRef.current = balance;
      savePersistedCredits(balance);
      setCredits(formatCreditsShort(balance));
    } catch {
      // Network/auth hiccup — leave the previous credits value in place.
    }
  }, [baseURL, apiKey, cwd]);

  // Resolve a model's per-token prices from the cached catalog, fetching it
  // once if needed. Returns {} when pricing is unavailable (cost is then
  // simply omitted from the status line) (#31).
  const priceFor = useCallback(
    async (slug: string): Promise<{ promptPrice?: number; completionPrice?: number }> => {
      let models = modelsCacheRef.current;
      if (!models) {
        try {
          models = await fetchModels(baseURL);
          modelsCacheRef.current = models;
        } catch {
          return {};
        }
      }
      const m = models.find((x) => x.id === slug);
      return m ? { promptPrice: m.promptPrice, completionPrice: m.completionPrice } : {};
    },
    [baseURL],
  );

  useEffect(() => {
    void refreshStatus();
  }, [refreshStatus]);

  const pushItem = useCallback((item: HistoryItem) => {
    setItems((prev) => [...prev, item]);
  }, []);

  // Background Nyx doc sync (#67). A timer refreshes locally-pulled docs from
  // the cloud while the session runs. It starts ONLY when Nyx is configured AND
  // there are tracked docs; otherwise it no-ops. Each tick fetches each tracked
  // doc, rewrites files whose cloud copy is newer (skipping locally-edited ones
  // with a warning), and surfaces a concise info line. Failures stay quiet so a
  // down backend produces no error storm. The interval is cleared on unmount.
  useEffect(() => {
    if (!nyx?.apiKey) return;
    if (trackedDocCount(cwd) === 0) return;
    const ctx: ToolContext = {
      cwd,
      skills: [],
      nyxApiUrl: nyx.apiUrl,
      nyxApiKey: nyx.apiKey,
      nyxTeamId: nyx.teamId,
    };
    let running = false;
    const tick = async () => {
      if (running || trackedDocCount(cwd) === 0) return;
      running = true;
      try {
        const result = await syncTrackedDocs(cwd, ctx, (id) => fetchDocRaw(ctx, id));
        if (result.synced > 0) {
          pushItem({ kind: 'info', text: `Synced ${result.synced} Nyx doc(s) from cloud` });
        }
        if (result.skippedLocalEdits.length > 0) {
          pushItem({
            kind: 'info',
            text: `Skipped ${result.skippedLocalEdits.length} Nyx doc(s) with local edits: ${result.skippedLocalEdits.join(
              ', ',
            )}`,
          });
        }
      } catch {
        // Sync pass failed — stay quiet, the next tick will retry.
      } finally {
        running = false;
      }
    };
    const timer = setInterval(() => void tick(), syncIntervalMs());
    return () => clearInterval(timer);
  }, [cwd, nyx?.apiKey, nyx?.apiUrl, nyx?.teamId, pushItem]);

  const handleEvent = useCallback(
    (event: AgentEvent) => {
      switch (event.type) {
        case 'reasoning-delta':
          setReasoningText((prev) => prev + event.text);
          break;
        case 'text-delta':
          setReasoningText('');
          setStreamText((prev) => prev + event.text);
          break;
        case 'text-done':
          setStreamText('');
          setReasoningText('');
          pushItem({ kind: 'assistant', text: event.text });
          break;
        case 'tool-start':
          setRunningTool(`${event.name}(${event.summary})`);
          break;
        case 'tool-end':
          setRunningTool(null);
          pushItem({
            kind: 'tool',
            name: event.name,
            summary: event.summary,
            result: event.result,
            isError: event.isError,
          });
          break;
        case 'info':
          pushItem({ kind: 'info', text: event.text });
          break;
        case 'error':
          pushItem({ kind: 'error', text: event.message });
          break;
      }
    },
    [pushItem],
  );

  const requestApproval = useCallback(
    (req: { tool: string; summary: string; preview?: string }) =>
      new Promise<'yes' | 'no' | 'always' | 'persist'>((resolve) => {
        const pending: Approval = { ...req, resolve };
        approvalRef.current = pending;
        setApproval(pending);
      }),
    [],
  );

  const io = useMemo(() => ({ onEvent: handleEvent, requestApproval }), [handleEvent, requestApproval]);

  useInput(
    (char) => {
      const pending = approvalRef.current;
      if (!pending) return;
      const decision =
        char === 'y' ? 'yes' : char === 'a' ? 'always' : char === 'p' ? 'persist' : char === 'n' ? 'no' : null;
      if (!decision) return;
      approvalRef.current = null;
      setApproval(null);
      pending.resolve(decision);
    },
    { isActive: approval !== null },
  );

  // Esc while the agent is working interrupts the turn. If an approval is
  // pending, deny it too so the run loop unblocks and can wind down cleanly.
  useInput(
    (_input, key) => {
      if (!key.escape) return;
      abortRef.current?.abort();
      const pending = approvalRef.current;
      if (pending) {
        approvalRef.current = null;
        setApproval(null);
        pending.resolve('no');
      }
    },
    { isActive: busy },
  );

  const runAgent = useCallback(
    async (message: string) => {
      const controller = new AbortController();
      abortRef.current = controller;
      const turnModel = agent.model;
      lastTurnModelRef.current = turnModel;
      setBusy(true);
      await agent.run(message, io, controller.signal);
      abortRef.current = null;
      setBusy(false);
      void refreshStatus();

      // Last-turn cost: estimate from the API's token usage and the model's
      // pricing. Degrades gracefully — when pricing is unknown the segment is
      // simply omitted rather than shown as a guess (#31).
      void (async () => {
        const usage = agent.lastTurnUsage();
        const prices = await priceFor(turnModel);
        const cost = estimateTurnCost(usage, prices);
        if (cost === undefined) {
          setLastTurnCost(null);
          return;
        }
        setLastTurnCost(formatCostShort(cost));
        const newSession = sessionCost + cost;
        setSessionCost(newSession);
        // Budget guardrail: warn once the per-session cap is exceeded (#31).
        const cap = routing?.maxCostPerSession;
        if (cap !== undefined && sessionCost <= cap && newSession > cap) {
          pushItem({
            kind: 'info',
            text: `Budget warning: session cost $${newSession.toFixed(2)} exceeds the $${cap.toFixed(2)} cap (max-cost-per-session). Consider /model cheap-default.`,
          });
        }
      })();

      // Free-tier fallback: if remaining credits dropped below the threshold,
      // downgrade to the configured free model (once) (#31).
      const balance = lastBalanceRef.current;
      const threshold = routing?.lowCreditsThreshold;
      const freeModel = routing?.freeModel;
      if (
        !downgradedRef.current &&
        freeModel &&
        threshold !== undefined &&
        balance &&
        balance.remaining < threshold &&
        agent.model !== freeModel
      ) {
        downgradedRef.current = true;
        agent.model = freeModel;
        setModel(freeModel);
        onSaveModel?.(freeModel);
        pushItem({
          kind: 'info',
          text: `Credits low ($${balance.remaining.toFixed(2)} < $${threshold.toFixed(2)}) — switched to free model ${freeModel}.`,
        });
      }
    },
    [agent, io, refreshStatus, priceFor, sessionCost, routing, onSaveModel, pushItem],
  );

  const openModelPicker = useCallback(async () => {
    let models = modelsCacheRef.current;
    if (!models) {
      pushItem({ kind: 'info', text: 'Fetching models from OpenRouter…' });
      try {
        models = await fetchModels(baseURL);
        modelsCacheRef.current = models;
      } catch (err) {
        pushItem({
          kind: 'error',
          text: `Couldn't fetch the model list (${err instanceof Error ? err.message : String(err)}). Showing suggestions — use /model <slug> to set any model directly.`,
        });
        models = SUGGESTED_MODELS.map((id) => ({ id, name: id }));
      }
    }
    setPicker(models);
  }, [baseURL, pushItem]);

  const handleSlashCommand = useCallback(
    (raw: string): void => {
      const [cmd, ...rest] = raw.slice(1).split(' ');
      const args = rest.join(' ').trim();
      switch (cmd) {
        case 'help':
          pushItem({ kind: 'info', text: HELP_TEXT });
          return;
        case 'skills':
          pushItem({
            kind: 'info',
            text:
              skills.length === 0
                ? 'No skills installed. Add skills/<name>/SKILL.md to this project or ~/.dsx/skills/.'
                : skills.map((s) => `/${s.name} — ${s.description} (${s.source})`).join('\n'),
          });
          return;
        case 'model':
          // With an arg, resolve it as a named profile from ~/.dsx/models.json
          // first (#31); if it isn't a known profile, treat it as a raw slug (any
          // OpenRouter slug works — a bad one surfaces as an API error on the next
          // message). With no args, open the interactive browse/search picker.
          if (args) {
            const slug = loadModelProfiles()[args] ?? args;
            agent.model = slug;
            setModel(slug);
            onSaveModel?.(slug);
            pushItem({
              kind: 'info',
              text: slug === args ? `Model switched to ${slug}` : `Model switched to ${slug} (profile ${args})`,
            });
            // Budget guardrail: warn when switching to a model whose prompt
            // price exceeds the configured per-1K threshold (#31).
            void (async () => {
              const threshold = routing?.expensiveThresholdPer1k;
              if (threshold === undefined) return;
              const { promptPrice } = await priceFor(slug);
              if (promptPrice !== undefined && promptPrice * 1000 > threshold) {
                pushItem({
                  kind: 'info',
                  text: `Heads up: ${slug} costs ~$${(promptPrice * 1000).toFixed(4)}/1K prompt tokens, above your $${threshold.toFixed(4)}/1K threshold.`,
                });
              }
            })();
          } else {
            void openModelPicker();
          }
          return;
        case 'mcp':
          setMcpManager(listMcpServers(cwd));
          return;
        case 'credits':
          void (async () => {
            pushItem({ kind: 'info', text: 'Fetching credits…' });
            try {
              pushItem({ kind: 'info', text: formatCredits(await fetchCredits(baseURL, apiKey)) });
            } catch (err) {
              pushItem({
                kind: 'error',
                text: `Couldn't fetch credits (${err instanceof Error ? err.message : String(err)}).`,
              });
            }
          })();
          return;
        case 'rate': {
          // Record a 1–5 quality rating for the last turn so it can inform
          // future model selection. Minimal feedback store (#31).
          const [scoreRaw, ...noteParts] = args.split(' ');
          const score = Number.parseInt(scoreRaw, 10);
          if (!Number.isInteger(score) || score < 1 || score > 5) {
            pushItem({ kind: 'error', text: 'Usage: /rate <1-5> [note]' });
            return;
          }
          const note = noteParts.join(' ').trim() || undefined;
          saveRating({ model: lastTurnModelRef.current, rating: score, note, at: new Date().toISOString() });
          pushItem({
            kind: 'info',
            text: `Recorded rating ${score}/5 for ${lastTurnModelRef.current}${note ? ` — "${note}"` : ''} (saved to ~/.dsx/feedback.json).`,
          });
          return;
        }
        case 'expand': {
          // Walk the history newest-first, collecting items whose rendered
          // content was capped (assistant text / tool result over PREVIEW_LINES).
          // Push the full text of the most recent capped item — or the nth,
          // counting back — into history so it lands in <Static> and the
          // terminal's native scrollback holds it. Lowest-risk approach (#19):
          // no alternate screen buffer, no change to input/approval focus.
          const n = args ? Math.max(1, Number.parseInt(args, 10) || 1) : 1;
          const capped: { text: string; label: string }[] = [];
          for (let i = items.length - 1; i >= 0; i--) {
            const it = items[i];
            const full =
              it.kind === 'assistant' ? it.text : it.kind === 'tool' ? it.result : undefined;
            if (full === undefined) continue;
            // Use the same per-tool cap the renderer applies so read-tool
            // truncation is detected at 5 lines, not 25 (#64).
            const max =
              it.kind === 'tool' && it.name === READ_TOOL_NAME ? READ_PREVIEW_LINES : PREVIEW_LINES;
            if (capLines(full, max).hidden > 0) {
              const label = it.kind === 'tool' ? `${it.name}(${it.summary})` : 'assistant';
              capped.push({ text: full, label });
            }
          }
          if (capped.length === 0) {
            pushItem({ kind: 'info', text: 'Nothing to expand — no truncated output in history.' });
            return;
          }
          const target = capped[Math.min(n, capped.length) - 1];
          pushItem({ kind: 'info', text: `Expanded ${target.label} (full output):` });
          pushItem({ kind: 'expanded', text: target.text });
          return;
        }
        case 'clear':
          agent.clearHistory();
          onClear?.();
          pushItem({ kind: 'info', text: 'Conversation history cleared.' });
          return;
        case 'init':
          pushItem({ kind: 'user', text: '/init' });
          void runAgent(INIT_PROMPT);
          return;
        case 'files': {
          void (async () => {
            try {
              const dir = args || '';
              const tool = agent.tools.find((t) => t.name === 'list_directory');
              if (!tool) {
                pushItem({ kind: 'error', text: 'list_directory tool not found.' });
                return;
              }
              const raw = await tool.run({ subdir: dir }, { cwd, skills: [] });
              const entries: FileEntry[] = JSON.parse(raw).map((e: any) => ({ ...e, mtime: new Date(e.mtime) }));
              setLightTable({ entries, subdir: dir });
            } catch (err) {
              pushItem({ kind: 'error', text: String(err) });
            }
          })();
          return;
        }
        case 'view': {
          if (!args) {
            pushItem({ kind: 'error', text: 'Usage: /view <path>' });
            return;
          }
          void (async () => {
            try {
              const tool = agent.tools.find((t) => t.name === 'read_file');
              if (!tool) {
                pushItem({ kind: 'error', text: 'read_file tool not found.' });
                return;
              }
              const raw = await tool.run({ path: args }, { cwd, skills: [] });
              // Strip line-number prefix that read_file adds
              const content = raw
                .split('\n')
                .map((l) => l.replace(/^\d+→/, ''))
                .join('\n');
              setViewer({ path: args, content });
            } catch (err) {
              pushItem({ kind: 'error', text: String(err) });
            }
          })();
          return;
        }
        case 'compact':
          setBusy(true);
          void agent
            .compact(io)
            .catch((err) => pushItem({ kind: 'error', text: String(err) }))
            .finally(() => setBusy(false));
          return;
        case 'exit':
        case 'quit':
          exit();
          return;
        default: {
          // Support namespaced subcommands like `/gsd:progress`. Prefer the
          // subcommand's own SKILL.md (loaded from <skill>/commands/<sub>/) so
          // its specific instructions drive the run; fall back to the parent
          // skill with the subcommand folded into args when there's no such
          // command file (the parent then dispatches on it).
          const colon = cmd.indexOf(':');
          if (colon !== -1) {
            const sub = findSubcommand(skills, cmd);
            if (sub) {
              pushItem({ kind: 'user', text: raw });
              void runAgent(skillInvocationMessage(sub, args));
              return;
            }
          }
          const skillName = colon === -1 ? cmd : cmd.slice(0, colon);
          const subcommand = colon === -1 ? '' : cmd.slice(colon + 1);
          const skill = findSkill(skills, skillName);
          if (skill) {
            const fullArgs = [subcommand, args].filter(Boolean).join(' ');
            pushItem({ kind: 'user', text: raw });
            void runAgent(skillInvocationMessage(skill, fullArgs));
            return;
          }
          pushItem({ kind: 'error', text: `Unknown command /${cmd} — try /help` });
        }
      }
    },
    [agent, apiKey, baseURL, cwd, exit, items, onClear, onSaveModel, openModelPicker, priceFor, pushItem, routing, runAgent, skills],
  );

  // Replace the active token with the chosen suggestion's value. For commands
  // (no space yet) this swaps the whole `/cmd`; for paths it splices the value
  // back after the prefix. A trailing space is added for commands so the user
  // can keep typing args, but kept off for directories so they can drill in.
  const acceptSuggestion = useCallback(
    (s: Suggestion) => {
      const { prefix } = activeToken(input);
      const trailing = s.kind === 'command' ? ' ' : '';
      setInput(`${prefix}${s.value}${trailing}`);
      setAcIndex(0);
      setAcDismissed(false);
    },
    [input],
  );

  // Typing edits the token, so re-enable the dropdown and reset the cursor.
  const handleInputChange = useCallback((value: string) => {
    setInput(value);
    setAcIndex(0);
    setAcDismissed(false);
  }, []);

  // Keyboard nav for the dropdown. Active only while it's open; runs before
  // ink-text-input sees the key for ↑/↓/Enter/Esc, which it otherwise ignores.
  useInput(
    (_char, key) => {
      if (key.upArrow) {
        setAcIndex((i) => Math.max(0, i - 1));
        return;
      }
      if (key.downArrow) {
        setAcIndex((i) => Math.min(acSuggestions.length - 1, i + 1));
        return;
      }
      if (key.return) {
        const sel = acSuggestions[Math.min(acIndex, acSuggestions.length - 1)];
        if (sel) acceptSuggestion(sel);
        return;
      }
      if (key.escape) {
        setAcDismissed(true);
      }
    },
    { isActive: acOpen },
  );

  const handleSubmit = useCallback(
    (value: string) => {
      // When the dropdown is open, Enter accepts a suggestion (handled by the
      // dropdown's useInput) and must not submit the message.
      if (acOpenRef.current) return;
      const text = value.trim();
      if (!text || busy) return;
      setInput('');
      setAcDismissed(false);
      setAcIndex(0);
      if (text.startsWith('/')) {
        handleSlashCommand(text);
        return;
      }
      pushItem({ kind: 'user', text });
      void runAgent(text);
    },
    [busy, handleSlashCommand, pushItem, runAgent],
  );

  // Bound both live previews by rendered terminal rows (see tailByRows): this
  // keeps the dynamic frame shorter than the terminal so Ink repaints in place
  // instead of flickering, whether the output is one long paragraph or many
  // short lines. Rendered as a single wrapping <Text> so Ink's height matches.
  // Render at terminal width minus a 2-column safety gutter. Letting content
  // occupy the full width makes the terminal hard-wrap the final cell, which
  // splits words mid-line ("li" / "ne."). The width must be applied to both the
  // dynamic root box AND <Static> (whose history renders into its own buffer
  // sized by its own computed width), so we set it in both places.
  const width = Math.max(20, (stdout?.columns ?? 80) - 2);
  const reasoningTail = tailByRows(reasoningText, width, REASONING_TAIL_LINES).tail;
  const { tail: streamTail, truncated: streamTruncated } = tailByRows(streamText, width, STREAM_TAIL_LINES);

  return (
    <Box flexDirection="column" width={width}>
      <Static items={items} style={{ width }}>
        {(item, index) => <HistoryItemView key={index} item={item} />}
      </Static>

      {reasoningTail !== '' && (
        <Box marginTop={1}>
          <Text dimColor italic>
            {reasoningTail}
          </Text>
        </Box>
      )}
      {streamText !== '' && (
        <Box flexDirection="column" marginTop={1}>
          {streamTruncated && <Text dimColor>… (streaming — full message appears below when done)</Text>}
          <Text>{streamTail}</Text>
        </Box>
      )}

      {picker ? (
        <ModelPicker
          models={picker}
          current={model}
          onSelect={(id) => {
            agent.model = id;
            setModel(id);
            onSaveModel?.(id);
            setPicker(null);
            pushItem({ kind: 'info', text: `Model switched to ${id}` });
          }}
          onCancel={() => {
            setPicker(null);
            pushItem({ kind: 'info', text: 'Model unchanged.' });
          }}
        />
      ) : mcpManager ? (
        <McpManager
          servers={mcpManager}
          onAdd={(name, config) => {
            addMcpServer(cwd, name, config);
            setMcpManager(listMcpServers(cwd));
            pushItem({ kind: 'info', text: `MCP server "${name}" added — restart dsx to connect.` });
          }}
          onRemove={(name) => {
            removeMcpServer(cwd, name);
            setMcpManager(listMcpServers(cwd));
            pushItem({ kind: 'info', text: `MCP server "${name}" removed.` });
          }}
          onClose={() => setMcpManager(null)}
        />
      ) : viewer ? (
        <MarkdownViewer
          path={viewer.path}
          content={viewer.content}
          onClose={() => setViewer(null)}
        />
      ) : lightTable ? (
        <LightTable
          entries={lightTable.entries}
          title={lightTable.subdir ? `Files — ${lightTable.subdir}` : 'Files'}
          onOpen={async (entry) => {
            if (entry.isDir) {
              const tool = agent.tools.find((t) => t.name === 'list_directory');
              if (!tool) return;
              const raw = await tool.run({ subdir: entry.path }, { cwd, skills: [] });
              const entries: FileEntry[] = JSON.parse(raw).map((e: any) => ({ ...e, mtime: new Date(e.mtime) }));
              setLightTable({ entries, subdir: entry.path });
            } else {
              const tool = agent.tools.find((t) => t.name === 'read_file');
              if (!tool) return;
              const raw = await tool.run({ path: entry.path }, { cwd, skills: [] });
              const content = raw
                .split('\n')
                .map((l) => l.replace(/^\d+→/, ''))
                .join('\n');
              setViewer({ path: entry.path, content });
              setLightTable(null);
            }
          }}
          onClose={() => setLightTable(null)}
        />
      ) : approval ? (
        <Box borderStyle="round" borderColor={theme.accent} flexDirection="column" paddingX={1} marginTop={1}>
          <Text color={theme.accentBright} bold>
            Allow {approval.tool}?
          </Text>
          {/* The structured code-diff header already shows the path, so don't
              repeat the generic summary line above it. */}
          {!(approval.preview && decodeCodeDiff(approval.preview)) && (
            <Text>{approval.summary}</Text>
          )}
          {approval.preview ? (
            <Box flexDirection="column" marginTop={1}>
              {(() => {
                const doc = decodeDocPreview(approval.preview);
                if (doc) return <DocPreviewView preview={doc} />;
                return looksLikeDiff(approval.preview) ? (
                  <DiffView text={approval.preview} />
                ) : (
                  <FormattedText text={approval.preview} />
                );
              })()}
            </Box>
          ) : null}
          <Text dimColor>[y] yes once · [a] always this session · [p] persist allow rule · [n] no</Text>
        </Box>
      ) : busy ? (
        <Box marginTop={1}>
          <Text color={theme.accent}>
            <Spinner type="dots" />
          </Text>
          <Text dimColor> {runningTool ?? 'thinking…'}</Text>
        </Box>
      ) : (
        <Box flexDirection="column">
          <Box borderStyle="round" borderColor="gray" paddingX={1} marginTop={1}>
            <Text color={theme.accentBright}>› </Text>
            <TextInput
              value={input}
              onChange={handleInputChange}
              onSubmit={handleSubmit}
              focus={lightTable === null && viewer === null && mcpManager === null}
            />
          </Box>
          {!acDismissed && input.length > 0 && (
            <Autocomplete
              input={input}
              providers={acProviders}
              selectedIndex={acIndex}
              onSuggestions={setAcSuggestions}
            />
          )}
        </Box>
      )}

      <StatusLine
        model={model}
        cwd={cwd}
        credits={credits}
        usedTokens={agent.usedTokens()}
        budgetTokens={agent.contextBudget()}
        branch={branch}
        lastTurnCost={lastTurnCost}
        sessionCost={sessionCost}
        maxCostPerSession={routing?.maxCostPerSession}
      />
    </Box>
  );
}
