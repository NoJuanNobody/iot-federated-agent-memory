import React, { useMemo, useState } from 'react';
import { Box, Text, useInput } from 'ink';
import { theme } from './theme.js';

export interface FileEntry {
  name: string;
  path: string;
  size: number;
  mtime: Date;
  isDir: boolean;
  lineCount?: number;
}

function fmtSize(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${Math.round(n / 1024)} KB`;
  return `${Math.round(n / (1024 * 1024))} MB`;
}

function fmtDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function fileKind(entry: FileEntry): string {
  if (entry.isDir) return 'dir';
  if (entry.name.match(/\.(md|mdx)$/i)) return 'md';
  if (entry.name.match(/\.(tsx?|jsx?)$/)) return 'js';
  if (entry.name.match(/\.(py)$/)) return 'py';
  if (entry.name.match(/\.(json|yaml|yml)$/)) return 'cfg';
  if (entry.name.match(/\.(css|scss|less)$/)) return 'css';
  if (entry.name.match(/\.(html|htm)$/)) return 'html';
  if (entry.name.match(/\.(png|jpe?g|gif|svg|webp|bmp)$/)) return 'img';
  if (entry.name.match(/\.(mp3|wav|ogg|mp4|mov|avi)$/)) return 'media';
  return 'txt';
}

interface Props {
  entries: FileEntry[];
  onOpen: (entry: FileEntry) => void;
  onClose: () => void;
  initialFilter?: string;
  title?: string;
}

const VISIBLE = 12;
const MAX_ROWS = 200;

export function LightTable({ entries, onOpen, onClose, initialFilter = '', title = 'Files' }: Props) {
  const [filter, setFilter] = useState(initialFilter);
  const [index, setIndex] = useState(0);

  const filtered = useMemo(() => {
    const f = filter.trim().toLowerCase();
    if (!f) return entries.slice(0, MAX_ROWS);
    const out = entries
      .filter((e) => e.name.toLowerCase().includes(f) || e.path.toLowerCase().includes(f))
      .slice(0, MAX_ROWS);
    return out;
  }, [entries, filter]);

  const selectedIndex = Math.min(index, Math.max(0, filtered.length - 1));

  useInput((input, key) => {
    if (key.escape) {
      onClose();
      return;
    }
    if (key.return) {
      const sel = filtered[selectedIndex];
      if (sel) onOpen(sel);
      return;
    }
    if (key.upArrow) {
      setIndex(Math.max(0, selectedIndex - 1));
      return;
    }
    if (key.downArrow) {
      setIndex(Math.min(filtered.length - 1, selectedIndex + 1));
      return;
    }
    if (key.backspace || key.delete) {
      setFilter((f) => f.slice(0, -1));
      setIndex(0);
      return;
    }
    if (input && !key.ctrl && !key.meta && input.length === 1) {
      setFilter((f) => f + input);
      setIndex(0);
      return;
    }
  });

  const start = Math.max(0, Math.min(selectedIndex - Math.floor(VISIBLE / 2), Math.max(0, filtered.length - VISIBLE)));
  const window = filtered.slice(start, start + VISIBLE);

  const maxName = Math.min(40, Math.max(...filtered.map((e) => e.name.length), 10));
  const colPad = { name: maxName + 2, kind: 6, size: 8, date: 11, lines: 7 };

  return (
    <Box borderStyle="round" borderColor={theme.accent} flexDirection="column" paddingX={1} marginTop={1}>
      <Text bold color={theme.accentBright}>
        {title} — {filtered.length} / {entries.length}
      </Text>

      <Box>
        <Text color={theme.accentBright}>search › </Text>
        <Text color="white">{filter}</Text>
        <Text dimColor>_</Text>
      </Box>

      {/* Header */}
      <Box marginTop={1}>
        <Text dimColor bold>
          {' '.repeat(2)}{'name'.padEnd(colPad.name)}
          {'kind'.padEnd(colPad.kind)}
          {'size'.padStart(colPad.size)}
          {'date'.padStart(colPad.date)}
          {filtered[0]?.lineCount !== undefined ? ' lines'.padStart(colPad.lines) : ''}
        </Text>
      </Box>

      {/* Rows */}
      {window.map((e, i) => {
        const isSelected = start + i === selectedIndex;
        const kind = fileKind(e);
        const icon = e.isDir ? '📁' : kind === 'img' ? '🖼' : kind === 'md' ? '📝' : '📄';
        return (
          <Box key={e.path}>
            <Text inverse={isSelected} color={isSelected ? theme.accentBright : undefined}>
              {isSelected ? '❯ ' : '  '}
              {icon}{' '}
              {e.name.padEnd(colPad.name - 2)}
              {' '}
              {kind.padEnd(colPad.kind)}
              {fmtSize(e.size).padStart(colPad.size)}
              {fmtDate(e.mtime).padStart(colPad.date)}
              {e.lineCount !== undefined ? String(e.lineCount).padStart(colPad.lines) : ''}
            </Text>
          </Box>
        );
      })}

      {filtered.length === 0 && (
        <Box><Text dimColor>No files match "{filter}".</Text></Box>
      )}

      <Box marginTop={1}>
        <Text dimColor>
          {'\u2191/\u2193 navigate \u00b7 Enter open \u00b7 Esc close'}
        </Text>
      </Box>
    </Box>
  );
}
