import React from 'react';
import { Box, Text } from 'ink';
import { theme } from './theme.js';
import { decodeCodeDiff, diffSummary, type CodeDiff } from './codeDiff.js';

/**
 * Renders a file-edit approval diff. Two paths:
 *
 * 1. Structured (#77): a `CodeDiff` encoded by `encodeCodeDiff` renders a
 *    Claude-Code-style view — an `Update (path)` / `Create (path)` header, an
 *    "Added N, removed M" summary, a left line-number gutter, context lines in
 *    the default color, removed lines red and added lines green.
 * 2. Legacy text: lines prefixed with `+ ` / `- ` (or `<gutter> +/- text`) are
 *    colored green/red; everything else is rendered as-is. Used as the
 *    graceful-degradation fallback and by multi-file rename previews.
 */
export function DiffView({ text }: { text: string }) {
  const structured = decodeCodeDiff(text);
  if (structured) return <CodeDiffView diff={structured} />;
  return <LegacyDiffView text={text} />;
}

function CodeDiffView({ diff }: { diff: CodeDiff }) {
  const verb = diff.kind === 'create' ? 'Create' : 'Update';
  return (
    <Box flexDirection="column">
      <Text color={theme.accentBright} bold>
        {verb} ({diff.path})
      </Text>
      <Text dimColor>{diffSummary(diff.added, diff.removed)}</Text>
      <Box flexDirection="column" marginTop={1}>
        {diff.hunks.map((hunk, hi) => (
          <Box key={hi} flexDirection="column">
            {hi > 0 && <Text dimColor>{'⋮'.padStart(diff.gutterWidth + 1)}</Text>}
            {hunk.rows.map((row, ri) => {
              const color =
                row.kind === 'add' ? theme.success : row.kind === 'remove' ? theme.error : undefined;
              const sign = row.kind === 'add' ? '+' : row.kind === 'remove' ? '-' : ' ';
              const gutter = String(row.num ?? '').padStart(diff.gutterWidth);
              return (
                <Box key={ri}>
                  <Text dimColor>{gutter} </Text>
                  <Text color={color}>
                    {sign} {row.text === '' ? '' : row.text}
                  </Text>
                </Box>
              );
            })}
          </Box>
        ))}
      </Box>
    </Box>
  );
}

/** Color by the change marker, tolerating an optional leading line-number gutter. */
function LegacyDiffView({ text }: { text: string }) {
  const lines = text.split('\n');
  return (
    <Box flexDirection="column">
      {lines.map((line, i) => {
        const m = /^\s*\d+\s+([+-])/.exec(line);
        const marker = m ? m[1] : line.startsWith('+') ? '+' : line.startsWith('-') ? '-' : '';
        const color = marker === '+' ? theme.success : marker === '-' ? theme.error : undefined;
        return (
          <Text key={i} color={color}>
            {line === '' ? ' ' : line}
          </Text>
        );
      })}
    </Box>
  );
}

/** Heuristic: does this preview text represent a diff (structured or legacy)? */
export function looksLikeDiff(text: string): boolean {
  if (decodeCodeDiff(text)) return true;
  return text
    .split('\n')
    .some((l) => l.startsWith('+ ') || l.startsWith('- ') || /^\s*\d+\s+[+-]\s/.test(l) || l.startsWith('@@ '));
}
