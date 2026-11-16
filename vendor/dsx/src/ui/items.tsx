import React from 'react';
import { Box, Text } from 'ink';
import { Markdown, FormattedText } from './MarkdownView.js';
import { theme } from './theme.js';

export type HistoryItem =
  | { kind: 'user'; text: string }
  | { kind: 'assistant'; text: string }
  | { kind: 'tool'; name: string; summary: string; result: string; isError: boolean }
  | { kind: 'info'; text: string }
  | { kind: 'error'; text: string }
  // Full un-truncated output pushed by /expand — rendered without the
  // PREVIEW_LINES cap so the whole thing lands in scrollback (#19).
  | { kind: 'expanded'; text: string };

export const PREVIEW_LINES = 25;

/**
 * Tighter preview cap for the file-read tool (#64). File reads are noisy and
 * rarely need 25 lines inline, so their tool result previews cap at 5 lines;
 * the full content is still recoverable via /expand. Keyed off the real tool
 * name `read_file` (see src/tools/files.ts).
 */
export const READ_PREVIEW_LINES = 5;

/** Real registry name of the file-read tool (src/tools/files.ts). */
export const READ_TOOL_NAME = 'read_file';

/**
 * Tools whose result is clean markdown (a metadata header + the doc body) rather
 * than raw JSON, so the transcript should render it with the Markdown component.
 * Everything else stays on FormattedText + syntax highlighting.
 */
const MARKDOWN_RESULT_TOOLS = new Set(['nyx_read_doc']);

/**
 * Display-only pretty-printer for JSON tool results. When `text` is a JSON
 * object or array, return it re-indented with 2 spaces so the transcript shows
 * readable structure instead of a compact/escaped one-liner. Anything else —
 * non-JSON, a bare scalar, or invalid/truncated JSON (e.g. cut at nyxFetch's
 * 8000-char limit) — is returned unchanged. Pure and exception-safe: it never
 * throws and never alters the model-facing result string (see src/agent.ts).
 */
export function prettyIfJson(text: string): string {
  const trimmed = text.trim();
  // Only objects/arrays — guard against JSON.parse succeeding on a bare number,
  // string, or boolean and reformatting plain text.
  if (!trimmed.startsWith('{') && !trimmed.startsWith('[')) return text;
  try {
    return JSON.stringify(JSON.parse(trimmed), null, 2);
  } catch {
    return text;
  }
}

/**
 * Cap `text` to the first `max` lines (default PREVIEW_LINES). Returns the
 * capped text plus the number of hidden lines (0 when nothing was cut). Used by
 * the assistant and tool cases so long output renders a bounded preview; the
 * full content is always recoverable via /expand (see App.tsx). Read-tool
 * results pass READ_PREVIEW_LINES for a tighter 5-line cap (#64).
 */
export function capLines(
  text: string,
  max: number = PREVIEW_LINES,
): { preview: string; hidden: number } {
  const lines = text.split('\n');
  if (lines.length <= max) return { preview: text, hidden: 0 };
  return { preview: lines.slice(0, max).join('\n'), hidden: lines.length - max };
}

export function HistoryItemView({ item }: { item: HistoryItem }) {
  switch (item.kind) {
    case 'user':
      return (
        <Box marginTop={1}>
          <Text color={theme.accentBright} bold>
            › {item.text}
          </Text>
        </Box>
      );
    case 'assistant': {
      const { preview, hidden } = capLines(item.text);
      return (
        <Box flexDirection="column" marginTop={1}>
          <Markdown content={preview} />
          {hidden > 0 && (
            <Text dimColor>… +{hidden} more lines (/expand to read)</Text>
          )}
        </Box>
      );
    }
    case 'tool': {
      const isMarkdown = !item.isError && MARKDOWN_RESULT_TOOLS.has(item.name);
      // Pretty-print JSON results (display-only) before capping, so a truncated
      // preview never feeds invalid JSON into the parser. Markdown-allowlisted
      // tools (#68) and error results are rendered as-is.
      const rendered = isMarkdown || item.isError ? item.result : prettyIfJson(item.result);
      // The file-read tool gets a tighter 5-line preview (#64); everything else
      // keeps the shared 25-line cap.
      const max = item.name === READ_TOOL_NAME ? READ_PREVIEW_LINES : PREVIEW_LINES;
      const { preview, hidden } = capLines(rendered, max);
      return (
        <Box flexDirection="column" marginTop={1}>
          <Text color={item.isError ? theme.error : theme.accentBright}>
            ⏺ {item.name}({item.summary})
          </Text>
          <Box flexDirection="column" marginLeft={2}>
            {isMarkdown ? (
              <Markdown content={preview} />
            ) : (
              <FormattedText text={preview} />
            )}
            {hidden > 0 && (
              <Text dimColor>… +{hidden} more lines (/expand to read)</Text>
            )}
          </Box>
        </Box>
      );
    }
    case 'info':
      return (
        <Box marginTop={1}>
          <Text color={theme.success}>{item.text}</Text>
        </Box>
      );
    case 'error':
      return (
        <Box marginTop={1}>
          <Text color={theme.error}>✗ {item.text}</Text>
        </Box>
      );
    case 'expanded':
      return (
        <Box marginTop={1}>
          <FormattedText text={item.text} />
        </Box>
      );
  }
}
