import React, { useEffect, useRef, useState } from 'react';
import { Box, Text, useStdout } from 'ink';
import { theme } from './theme.js';
import fg from 'fast-glob';
import fs from 'node:fs';
import path from 'node:path';
import type { Skill } from '../skills.js';

/** A single autocomplete suggestion. */
export interface Suggestion {
  /** Text inserted into the input when accepted (replaces the active token). */
  value: string;
  /** Primary label shown in the dropdown (defaults to `value`). */
  label?: string;
  /** Secondary hint shown dimmed after the label (description/usage). */
  hint?: string;
  /** Marks directory-style suggestions for distinct rendering. */
  isDir?: boolean;
  /** Source kind, used purely for the leading glyph. */
  kind?: 'file' | 'command';
}

/**
 * A pluggable autocomplete provider. `match` is a cheap synchronous predicate
 * deciding whether this provider applies to the current input; `suggest` does
 * the (possibly async) work of producing candidates. Built-in providers cover
 * files and slash commands; callers may register more at runtime.
 */
export interface AutocompleteProvider {
  match(input: string): boolean;
  suggest(input: string): Promise<Suggestion[]>;
}

/** Max candidates a provider returns (all navigable; the view scrolls them). */
const MAX_SUGGESTIONS = 50;

/** Rows shown at once; the visible window scrolls to keep the selection in view. */
const VISIBLE_ROWS = 8;

/**
 * Lowercase subsequence fuzzy match: every char of `needle` appears in `hay`
 * in order. Returns a score (lower is better) favouring earlier/tighter runs,
 * or null when there's no match. An empty needle matches everything.
 */
export function fuzzyScore(hay: string, needle: string): number | null {
  if (!needle) return 0;
  const h = hay.toLowerCase();
  const n = needle.toLowerCase();
  let hi = 0;
  let score = 0;
  let prev = -1;
  for (let ni = 0; ni < n.length; ni++) {
    const c = n[ni];
    const found = h.indexOf(c, hi);
    if (found === -1) return null;
    // Penalise gaps between matched characters and a late first match.
    if (prev !== -1) score += found - prev - 1;
    else score += found;
    prev = found;
    hi = found + 1;
  }
  return score;
}

/**
 * The active token is the last whitespace-delimited chunk of the input — the
 * part autocomplete operates on. Returns the token plus the prefix before it
 * so completion can splice the chosen value back in.
 */
export function activeToken(input: string): { prefix: string; token: string } {
  const m = input.match(/(\S*)$/);
  const token = m ? m[1] : '';
  const prefix = input.slice(0, input.length - token.length);
  return { prefix, token };
}

/** True when the token looks like a filesystem path we should complete. */
function looksLikePath(token: string): boolean {
  return token.startsWith('./') || token.startsWith('../') || token.startsWith('/') || token.includes('/');
}

/** Always-excluded directories, even when no .gitignore is present. */
const DEFAULT_IGNORE = ['**/node_modules/**', '**/.git/**', '**/dist/**'];

/**
 * Read the project's root `.gitignore` and turn each non-comment line into a
 * fast-glob ignore pattern (fast-glob has no native gitignore support, unlike
 * globby — so we do a lightweight translation). Combined with DEFAULT_IGNORE.
 * Cached per-cwd so it isn't re-read on every keystroke.
 */
const gitignoreCache = new Map<string, string[]>();
function gitignorePatterns(cwd: string): string[] {
  const cached = gitignoreCache.get(cwd);
  if (cached) return cached;
  const patterns: string[] = [...DEFAULT_IGNORE];
  try {
    const raw = fs.readFileSync(path.join(cwd, '.gitignore'), 'utf8');
    for (const line of raw.split('\n')) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#') || trimmed.startsWith('!')) continue;
      const clean = trimmed.replace(/^\/+/, '').replace(/\/+$/, '');
      if (!clean) continue;
      patterns.push(`**/${clean}/**`, `**/${clean}`);
    }
  } catch {
    // No .gitignore — DEFAULT_IGNORE still applies.
  }
  gitignoreCache.set(cwd, patterns);
  return patterns;
}

/**
 * Built-in slash-command provider. Suggests when the whole input is a single
 * `/word` with no space yet. Combines the built-in command list with skills
 * (custom slash commands registered at runtime).
 */
export function createSlashProvider(
  builtins: { name: string; description: string }[],
  skills: Skill[],
): AutocompleteProvider {
  return {
    match(input) {
      return input.startsWith('/') && !input.includes(' ');
    },
    async suggest(input) {
      const q = input.slice(1); // drop leading '/'
      const commands: { name: string; description: string }[] = [...builtins];
      for (const s of skills) {
        commands.push({ name: s.name, description: s.description });
        // Surface namespaced subcommands (e.g. /gsd:progress) so they're
        // discoverable; they route to their own instructions on invocation.
        for (const sub of s.subcommands ?? []) {
          commands.push({ name: sub.name, description: sub.description });
        }
      }
      // De-dupe by name (a skill could shadow nothing built-in, but be safe).
      const seen = new Set<string>();
      const scored: { s: Suggestion; score: number }[] = [];
      for (const c of commands) {
        if (seen.has(c.name)) continue;
        seen.add(c.name);
        const score = fuzzyScore(c.name, q);
        if (score === null) continue;
        scored.push({
          s: { value: `/${c.name}`, label: `/${c.name}`, hint: c.description, kind: 'command' },
          score,
        });
      }
      scored.sort((a, b) => a.score - b.score || a.s.value.localeCompare(b.s.value));
      return scored.slice(0, MAX_SUGGESTIONS).map((x) => x.s);
    },
  };
}

/**
 * Built-in file provider. Suggests files/dirs from `cwd` when the active token
 * looks like a path. Uses fast-glob (gitignore-aware) and fuzzy-filters on the
 * basename. Directories are marked with a trailing slash.
 */
export function createFileProvider(cwd: string): AutocompleteProvider {
  return {
    match(input) {
      return looksLikePath(activeToken(input).token);
    },
    async suggest(input) {
      const { token } = activeToken(input);
      // Split the token into a directory portion (already typed) and the
      // fragment being completed, so we glob the right directory and fuzzy
      // match only the trailing fragment.
      const slash = token.lastIndexOf('/');
      const dirPart = slash >= 0 ? token.slice(0, slash + 1) : '';
      const frag = slash >= 0 ? token.slice(slash + 1) : token;

      const absolute = path.isAbsolute(dirPart || token);
      const baseDir = absolute ? (dirPart || path.dirname(token)) : path.join(cwd, dirPart);

      let entries: string[];
      try {
        entries = await fg('*', {
          cwd: baseDir,
          onlyFiles: false,
          dot: true,
          markDirectories: true,
          followSymbolicLinks: false,
          suppressErrors: true,
          ignore: gitignorePatterns(cwd),
          deep: 1,
        });
      } catch {
        return [];
      }

      const scored: { s: Suggestion; score: number }[] = [];
      for (const entry of entries) {
        const isDir = entry.endsWith('/');
        const name = isDir ? entry.slice(0, -1) : entry;
        const base = path.basename(name);
        const score = fuzzyScore(base, frag);
        if (score === null) continue;
        const value = `${dirPart}${base}${isDir ? '/' : ''}`;
        scored.push({
          s: { value, label: value, isDir, kind: 'file' },
          score: score + (isDir ? -0.5 : 0), // gently favour directories
        });
      }
      scored.sort((a, b) => a.score - b.score || a.s.value.localeCompare(b.s.value));
      return scored.slice(0, MAX_SUGGESTIONS).map((x) => x.s);
    },
  };
}

interface Props {
  /** Current raw input string. */
  input: string;
  /** Ordered list of providers; the first matching one wins. */
  providers: AutocompleteProvider[];
  /** Currently highlighted index (owned by the parent for key handling). */
  selectedIndex: number;
  /** Reports the loaded suggestions back to the parent (for accept handling). */
  onSuggestions: (suggestions: Suggestion[]) => void;
}

/**
 * Ink autocomplete dropdown. Renders a fixed-height region below the input so
 * it never causes layout shift — empty when there are no suggestions. The
 * parent owns keyboard navigation and the selected index; this component only
 * resolves the active provider, loads suggestions (async-safe), and renders
 * them with the selected row highlighted.
 *
 * Terminal-UI note: the issue's ARIA/screen-reader criterion does not apply in
 * a TTY (no DOM/ARIA). The equivalent here is unambiguous visual highlighting
 * of the selected row (inverse + ❯ marker), implemented below.
 */
export function Autocomplete({ input, providers, selectedIndex, onSuggestions }: Props) {
  const { stdout } = useStdout();
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  // Guards against out-of-order async resolutions clobbering newer results.
  const reqRef = useRef(0);

  const provider = providers.find((p) => p.match(input));

  useEffect(() => {
    if (!provider) {
      setSuggestions([]);
      onSuggestions([]);
      return;
    }
    const id = ++reqRef.current;
    let cancelled = false;
    void provider.suggest(input).then((next) => {
      if (cancelled || id !== reqRef.current) return;
      setSuggestions(next);
      onSuggestions(next);
    });
    return () => {
      cancelled = true;
    };
    // input drives the query; provider is derived from input.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [input, provider]);

  if (suggestions.length === 0) return null;

  const total = suggestions.length;
  const sel = Math.min(selectedIndex, total - 1);

  // Cap the window to the terminal so the dropdown never dominates a short
  // screen. The panel's own chrome (≤2 scroll indicators + footer + margin) is
  // ~4 rows; reserving 12 keeps roughly 8 rows free for the input and history.
  // Clamp into [3, VISIBLE_ROWS].
  const termRows = stdout?.rows ?? 24;
  const rows = Math.max(3, Math.min(VISIBLE_ROWS, termRows - 12));

  // Slide a `rows`-tall window so the selected row stays in view, keeping it
  // roughly centered until we hit either end of the list.
  const start =
    total <= rows ? 0 : Math.min(Math.max(0, sel - Math.floor(rows / 2)), total - rows);
  const visible = suggestions.slice(start, start + rows);
  const hiddenAbove = start;
  const hiddenBelow = total - (start + rows);

  return (
    <Box flexDirection="column" marginTop={1} paddingX={1}>
      {hiddenAbove > 0 ? <Text dimColor>{`  ↑ ${hiddenAbove} more`}</Text> : null}
      {visible.map((s, i) => {
        const idx = start + i;
        const isSelected = idx === sel;
        const glyph = s.kind === 'command' ? '/' : s.isDir ? '▸' : '·';
        return (
          // truncate-end keeps every row to a single terminal line, so a long
          // hint can't wrap and balloon the dropdown's height past VISIBLE_ROWS.
          <Text
            key={s.value}
            wrap="truncate-end"
            inverse={isSelected}
            color={isSelected ? theme.accentBright : undefined}
          >
            {isSelected ? '❯ ' : '  '}
            {glyph} {s.label ?? s.value}
            {s.hint ? <Text dimColor={!isSelected}>{`  — ${s.hint}`}</Text> : null}
          </Text>
        );
      })}
      {hiddenBelow > 0 ? <Text dimColor>{`  ↓ ${hiddenBelow} more`}</Text> : null}
      <Text dimColor>{`↑/↓ navigate · Enter accept · Esc dismiss · ${sel + 1}/${total}`}</Text>
    </Box>
  );
}
