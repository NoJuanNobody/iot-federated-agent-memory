import React, { useState } from 'react';
import { Box, Text, useInput } from 'ink';
import TextInput from 'ink-text-input';
import type { McpServerConfig } from '../mcp.js';
import { theme } from './theme.js';

interface Props {
  servers: Record<string, McpServerConfig>;
  /** Persist a new server; throws (with a user message) on validation failure. */
  onAdd: (name: string, config: McpServerConfig) => void;
  /** Remove a server by name. */
  onRemove: (name: string) => void;
  onClose: () => void;
}

/** One-line transport summary for the list view. */
function summarize(c: McpServerConfig): string {
  if (c.url) return `http · ${c.url}`;
  const cmd = [c.command, ...(c.args ?? [])].join(' ');
  return `stdio · ${cmd}`;
}

type Step =
  | { kind: 'list' }
  | { kind: 'name' }
  | { kind: 'transport' }
  | { kind: 'command' }
  | { kind: 'args' }
  | { kind: 'env' }
  | { kind: 'url' };

interface Draft {
  name: string;
  transport: 'stdio' | 'http';
  command: string;
  args: string;
  env: string;
  url: string;
}

const emptyDraft: Draft = { name: '', transport: 'stdio', command: '', args: '', env: '', url: '' };

/** Parse `K=V,K2=V2` (or newline-separated) into a record; ignores blanks. */
function parseEnv(raw: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const pair of raw.split(/[\n,]/)) {
    const trimmed = pair.trim();
    if (!trimmed) continue;
    const eq = trimmed.indexOf('=');
    if (eq === -1) continue;
    out[trimmed.slice(0, eq).trim()] = trimmed.slice(eq + 1).trim();
  }
  return out;
}

/**
 * Interactive MCP server manager (#53). Lists servers configured in
 * `<cwd>/.dsx/mcp.json` with a key to remove, plus an add flow that walks
 * name → transport → command/args/env or url. Rendered in place of the input
 * box, so it owns keyboard focus. Esc backs out a step, then closes.
 */
export function McpManager({ servers, onAdd, onRemove, onClose }: Props) {
  const [step, setStep] = useState<Step>({ kind: 'list' });
  const [index, setIndex] = useState(0);
  const [draft, setDraft] = useState<Draft>(emptyDraft);
  const [field, setField] = useState('');
  const [error, setError] = useState<string | null>(null);

  const names = Object.keys(servers);
  const selectedIndex = Math.min(index, Math.max(0, names.length - 1));

  const reset = () => {
    setStep({ kind: 'list' });
    setDraft(emptyDraft);
    setField('');
  };

  const commitAdd = (d: Draft) => {
    const config: McpServerConfig =
      d.transport === 'http'
        ? { url: d.url.trim() }
        : {
            command: d.command.trim(),
            ...(d.args.trim() ? { args: d.args.trim().split(/\s+/) } : {}),
            ...(Object.keys(parseEnv(d.env)).length ? { env: parseEnv(d.env) } : {}),
          };
    try {
      onAdd(d.name.trim(), config);
      reset();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setStep({ kind: 'name' });
      setField(d.name);
    }
  };

  useInput((input, key) => {
    setError(null);
    if (key.escape) {
      if (step.kind === 'list') onClose();
      else reset();
      return;
    }
    if (step.kind === 'list') {
      if (key.upArrow) {
        setIndex(Math.max(0, selectedIndex - 1));
        return;
      }
      if (key.downArrow) {
        setIndex(Math.min(names.length - 1, selectedIndex + 1));
        return;
      }
      if (input === 'a') {
        setStep({ kind: 'name' });
        setField('');
        return;
      }
      if ((input === 'd' || input === 'x') && names[selectedIndex]) {
        onRemove(names[selectedIndex]);
        setIndex(0);
        return;
      }
      return;
    }
    if (step.kind === 'transport') {
      if (input === 's' || input === '1') {
        setDraft((d) => ({ ...d, transport: 'stdio' }));
        setStep({ kind: 'command' });
        setField('');
        return;
      }
      if (input === 'h' || input === '2') {
        setDraft((d) => ({ ...d, transport: 'http' }));
        setStep({ kind: 'url' });
        setField('');
        return;
      }
    }
  });

  // Text-entry steps: ink-text-input owns chars; Enter advances via onSubmit.
  const submitField = (value: string) => {
    const v = value;
    switch (step.kind) {
      case 'name':
        if (!v.trim()) {
          setError('Server name is required.');
          return;
        }
        setDraft((d) => ({ ...d, name: v }));
        setStep({ kind: 'transport' });
        setField('');
        return;
      case 'command':
        setDraft((d) => ({ ...d, command: v }));
        setStep({ kind: 'args' });
        setField('');
        return;
      case 'args':
        setDraft((d) => ({ ...d, args: v }));
        setStep({ kind: 'env' });
        setField('');
        return;
      case 'env':
        setDraft((d) => {
          const next = { ...d, env: v };
          commitAdd(next);
          return next;
        });
        return;
      case 'url':
        setDraft((d) => {
          const next = { ...d, url: v };
          commitAdd(next);
          return next;
        });
        return;
    }
  };

  const border = (
    <>
      {error && <Text color="red">{error}</Text>}
    </>
  );

  if (step.kind === 'list') {
    return (
      <Box borderStyle="round" borderColor={theme.accent} flexDirection="column" paddingX={1} marginTop={1}>
        <Text bold color={theme.accentBright}>
          MCP servers — {names.length} configured
        </Text>
        {names.length === 0 && <Text dimColor>None yet. Press [a] to add one.</Text>}
        {names.map((name, i) => {
          const isSel = i === selectedIndex;
          return (
            <Text key={name} inverse={isSel} color={isSel ? theme.accentBright : undefined}>
              {isSel ? '❯ ' : '  '}
              {name} — {summarize(servers[name])}
            </Text>
          );
        })}
        {border}
        <Text dimColor>↑/↓ navigate · [a] add · [d] remove · Esc close</Text>
      </Box>
    );
  }

  if (step.kind === 'transport') {
    return (
      <Box borderStyle="round" borderColor={theme.accent} flexDirection="column" paddingX={1} marginTop={1}>
        <Text bold color={theme.accentBright}>
          Add MCP server “{draft.name}” — transport
        </Text>
        <Text>[s] stdio (local command) · [h] http (URL endpoint)</Text>
        {border}
        <Text dimColor>press s or h · Esc cancel</Text>
      </Box>
    );
  }

  const prompts: Record<string, { title: string; hint: string }> = {
    name: { title: 'Add MCP server — name', hint: 'e.g. playwright · Enter next · Esc cancel' },
    command: { title: `Add “${draft.name}” — command`, hint: 'executable, e.g. npx · Enter next · Esc cancel' },
    args: { title: `Add “${draft.name}” — args`, hint: 'space-separated, optional · Enter next · Esc cancel' },
    env: { title: `Add “${draft.name}” — env`, hint: 'K=V,K2=V2 optional · Enter to save · Esc cancel' },
    url: { title: `Add “${draft.name}” — url`, hint: 'https://… · Enter to save · Esc cancel' },
  };
  const p = prompts[step.kind];

  return (
    <Box borderStyle="round" borderColor={theme.accent} flexDirection="column" paddingX={1} marginTop={1}>
      <Text bold color={theme.accentBright}>
        {p.title}
      </Text>
      <Box>
        <Text color={theme.accentBright}>› </Text>
        <TextInput value={field} onChange={setField} onSubmit={submitField} />
      </Box>
      {border}
      <Text dimColor>{p.hint}</Text>
    </Box>
  );
}
