import React from 'react';
import { Box, Text, useInput, useStdout } from 'ink';
import { theme } from './theme.js';
import { highlightLine, isHighlightableLang } from './highlight.js';

export function Markdown({ content }: { content: string }) {
  const blocks = parseBlocks(content);
  return (
    <Box flexDirection="column">
      {blocks.map((block, i) => (
        <BlockView key={i} block={block} isFirst={i === 0} />
      ))}
    </Box>
  );
}

export function MarkdownViewer({ content, path, onClose }: { content: string; path: string; onClose: () => void }) {
  // Own the Esc handler here (like LightTable) rather than relying on a
  // toggled isActive handler in the parent — a freshly-mounted, always-active
  // useInput closes reliably. The file renders in full; scroll it with the
  // terminal's native scrollback.
  useInput((_input, key) => {
    if (key.escape) onClose();
  });
  return (
    <Box borderStyle="round" borderColor={theme.accent} flexDirection="column" paddingX={1} marginTop={1}>
      <Text bold color={theme.accentBright}>
        {path}
      </Text>
      <Box flexDirection="column" marginTop={1}>
        <Markdown content={content} />
      </Box>
      <Box marginTop={1}>
        <Text dimColor>Esc close</Text>
      </Box>
    </Box>
  );
}

type Block =
  | { type: 'h1'; text: string }
  | { type: 'h2'; text: string }
  | { type: 'h3'; text: string }
  | { type: 'paragraph'; text: string }
  | { type: 'code'; lines: string[]; lang?: string }
  | { type: 'ul'; items: string[] }
  | { type: 'ol'; items: string[] }
  | { type: 'quote'; text: string }
  | { type: 'hr' }
  | { type: 'image'; alt: string; src: string }
  | { type: 'table'; header: string[]; rows: string[][] };

function parseBlocks(content: string): Block[] {
  const lines = content.split('\n');
  const blocks: Block[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (!line || line.trim() === '') {
      i++;
      continue;
    }

    if (line.startsWith('# ')) {
      blocks.push({ type: 'h1', text: stripInlineMarkers(line.slice(2)) });
      i++;
      continue;
    }
    if (line.startsWith('## ')) {
      blocks.push({ type: 'h2', text: stripInlineMarkers(line.slice(3)) });
      i++;
      continue;
    }
    if (line.startsWith('### ')) {
      blocks.push({ type: 'h3', text: stripInlineMarkers(line.slice(4)) });
      i++;
      continue;
    }
    if (line.startsWith('#### ') || line.startsWith('##### ') || line.startsWith('###### ')) {
      blocks.push({ type: 'h3', text: stripInlineMarkers(line.replace(/^#{4,}\s+/, '')) });
      i++;
      continue;
    }

    if (line.startsWith('```')) {
      const lang = line.slice(3).trim() || undefined;
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing ```
      blocks.push({ type: 'code', lines: codeLines, lang });
      continue;
    }

    if (line.match(/^(---|\*\*\*|___)\s*$/)) {
      blocks.push({ type: 'hr' });
      i++;
      continue;
    }

    if (line.match(/^( {0,3})([-*])\s+/)) {
      const items: string[] = [];
      while (i < lines.length) {
        const m = lines[i].match(/^( {0,3})[-*]\s+(.*)$/);
        if (!m) break;
        items.push(m[2]);
        i++;
      }
      blocks.push({ type: 'ul', items });
      continue;
    }

    if (line.match(/^( {0,3})\d+\.\s+/)) {
      const items: string[] = [];
      while (i < lines.length) {
        const m = lines[i].match(/^( {0,3})\d+\.\s+(.*)$/);
        if (!m) break;
        items.push(m[2]);
        i++;
      }
      blocks.push({ type: 'ol', items });
      continue;
    }

    if (line.startsWith('> ')) {
      blocks.push({ type: 'quote', text: line.slice(2) });
      i++;
      continue;
    }

    // Table block
    if (line.startsWith('|')) {
      const tableLines: string[] = [line];
      i++;
      while (i < lines.length && lines[i].startsWith('|')) {
        tableLines.push(lines[i]);
        i++;
      }
      const parsed = parseTable(tableLines);
      if (parsed) {
        blocks.push(parsed);
      }
      continue;
    }

    // Standalone image line: ![alt](src)
    const standaloneImg = line.match(/^!\[([^\]]*)\]\(([^)]+)\)$/);
    if (standaloneImg) {
      blocks.push({ type: 'image', alt: standaloneImg[1], src: standaloneImg[2] });
      i++;
      continue;
    }

    // Paragraph — absorb consecutive non-empty, non-special lines
    const paraLines: string[] = [line];
    i++;
    while (i < lines.length && lines[i].trim() && !isSpecialLine(lines[i])) {
      paraLines.push(lines[i]);
      i++;
    }
    blocks.push({ type: 'paragraph', text: paraLines.join('\n') });
  }

  return blocks;
}

function isSpecialLine(line: string): boolean {
  return (
    line.startsWith('#') ||
    line.startsWith('```') ||
    line.match(/^( {0,3})[-*]\s+/) !== null ||
    line.match(/^( {0,3})\d+\.\s+/) !== null ||
    line.startsWith('> ') ||
    line.startsWith('|') ||
    line.match(/^!\[[^\]]*\]\([^)]+\)$/) !== null ||
    line.match(/^(---|\*\*\*|___)\s*$/) !== null
  );
}

function BlockView({ block, isFirst }: { block: Block; isFirst?: boolean }) {
  const mt: 0 | 1 = isFirst ? 0 : 1;
  switch (block.type) {
    case 'h1':
      return (
        <Box marginTop={mt}>
          <Text bold color={theme.accentBright} underline>
            {block.text}
          </Text>
        </Box>
      );
    case 'h2':
      return (
        <Box marginTop={mt}>
          <Text bold color={theme.accent}>
            {block.text}
          </Text>
        </Box>
      );
    case 'h3':
      return (
        <Box marginTop={mt}>
          <Text bold color={theme.text}>
            {block.text}
          </Text>
        </Box>
      );
    case 'paragraph':
      return (
        <Box marginTop={mt}>
          <InlineText text={block.text} />
        </Box>
      );
    case 'code': {
      // Only tokenize when the fence names a language we render well; an
      // untagged or non-code fence (text, logs, data, ASCII tables) renders
      // verbatim so its contents don't get colored as if they were code.
      const doHighlight = isHighlightableLang(block.lang);
      return (
        <Box
          marginTop={mt}
          borderStyle="single"
          borderColor={theme.accent}
          paddingX={1}
          flexDirection="column"
        >
          {block.lang && (
            <Text color={theme.accentBright} italic>
              {block.lang}
            </Text>
          )}
          {block.lines.map((line, i) => (
            <Text key={i}>
              {!line
                ? ' '
                : doHighlight
                  ? highlightLine(line).map((s, j) => (
                      <Text key={j} color={s.color}>{s.text}</Text>
                    ))
                  : line}
            </Text>
          ))}
        </Box>
      );
    }
    case 'ul':
      return (
        <Box flexDirection="column" marginTop={mt}>
          {block.items.map((item, i) => (
            <Box key={i} flexDirection="row">
              <Text dimColor>  • </Text>
              <Box flexGrow={1}>
                <InlineText text={item} />
              </Box>
            </Box>
          ))}
        </Box>
      );
    case 'ol':
      return (
        <Box flexDirection="column" marginTop={mt}>
          {block.items.map((item, i) => (
            <Box key={i} flexDirection="row">
              <Text dimColor>  {i + 1}. </Text>
              <Box flexGrow={1}>
                <InlineText text={item} />
              </Box>
            </Box>
          ))}
        </Box>
      );
    case 'quote':
      return (
        <Box marginTop={mt} marginLeft={2}>
          <Text color={theme.accent} dimColor>
            │ {block.text}
          </Text>
        </Box>
      );
    case 'image':
      return (
        <Box marginTop={mt} marginLeft={2}>
          <Text dimColor>
            🖼 {block.alt ? `[${block.alt}]` : 'image'}
          </Text>
          <Text dimColor color="gray">
            {' '}({block.src})
          </Text>
        </Box>
      );
    case 'table':
      return <TableView block={block} mt={mt} />;
    case 'hr':
      return (
        <Box marginTop={mt}>
          <Text dimColor>───────────────────────────────────────</Text>
        </Box>
      );
  }
}

/**
 * Render a markdown table with aligned columns. Each cell lives in a
 * fixed-width box so columns line up row-to-row and wrapped cell text stays
 * within its own column instead of pushing the separators out of place.
 */
function TableView({ block, mt }: { block: Extract<Block, { type: 'table' }>; mt: 0 | 1 }) {
  const { stdout } = useStdout();
  const numCols = Math.max(block.header.length, ...block.rows.map((r) => r.length), 1);
  const pad = (row: string[]) =>
    Array.from({ length: numCols }, (_, i) => row[i] ?? '');
  const header = pad(block.header);
  const rows = block.rows.map(pad);

  // Width budget: terminal columns minus the border (2), paddingX (2),
  // a small safety margin, and the ` │ ` separators (3 chars each).
  const sepWidth = 3;
  const termWidth = stdout?.columns ?? 80;
  const avail = Math.max(numCols * 4, termWidth - 6 - sepWidth * (numCols - 1));

  // Natural width per column = widest cell (measured without inline markers).
  const natural = Array.from({ length: numCols }, (_, c) =>
    Math.max(stripInlineMarkers(header[c]).length, ...rows.map((r) => stripInlineMarkers(r[c]).length), 1),
  );

  // Shrink proportionally if the table is wider than the available space.
  let widths = natural;
  const total = natural.reduce((a, b) => a + b, 0);
  if (total > avail) {
    const minW = 6;
    const scale = avail / total;
    widths = natural.map((w) => Math.max(minW, Math.floor(w * scale)));
  }

  const tableWidth = widths.reduce((a, b) => a + b, 0) + sepWidth * (numCols - 1);

  const Row = ({ cells, bold }: { cells: string[]; bold?: boolean }) => (
    <Box flexDirection="row">
      {cells.map((cell, ci) => (
        <React.Fragment key={ci}>
          <Box width={widths[ci]} flexShrink={0}>
            {bold ? (
              <Text bold wrap="wrap">{stripInlineMarkers(cell)}</Text>
            ) : (
              <InlineText text={cell} />
            )}
          </Box>
          {ci < numCols - 1 && <Text dimColor>{' │ '}</Text>}
        </React.Fragment>
      ))}
    </Box>
  );

  return (
    <Box marginTop={mt} borderStyle="single" borderColor="gray" flexDirection="column" paddingX={1}>
      <Row cells={header} bold />
      <Box>
        <Text dimColor>{'─'.repeat(tableWidth)}</Text>
      </Box>
      {rows.map((row, ri) => (
        <Row key={ri} cells={row} />
      ))}
    </Box>
  );
}

/** Strip common inline markdown markers so raw text is readable in headers. */
function stripInlineMarkers(text: string): string {
  return text
    .replace(/\*{3}(.*?)\*{3}/g, '$1')
    .replace(/\*{2}(.+?)\*{2}/g, '$1')
    .replace(/\*(.+?)\*/g, '$1')
    .replace(/_(.+?)_/g, '$1')
    .replace(/`(.+?)`/g, '$1');
}

function parseTable(lines: string[]): Block | null {
  if (lines.length < 2) return null;
  const splitRow = (row: string) =>
    row
      .trim()
      .replace(/^\|/, '')
      .replace(/\|$/, '')
      .split('|')
      .map((c) => c.trim());

  const header = splitRow(lines[0]);
  // Second line should be separator like |---|---|
  const sep = splitRow(lines[1]);
  if (!sep.every((s) => /^[\s:-]+$/.test(s))) return null;

  const rows = lines.slice(2).map(splitRow);
  return { type: 'table', header, rows };
}

/**
 * Render raw, non-markdown output (tool/bash results, `/expand`, approval
 * previews). Lines are tokenized with the syntax palette only when `lang` names
 * a language the highlighter renders well; otherwise they render verbatim.
 * Arbitrary output has no language, so it stays plain rather than being colored
 * as if it were code (which turned prose and data into a patchwork). Verbatim —
 * not markdown — because this text is literal output, where `*`/`_`/backticks
 * are content, not formatting.
 */
export function FormattedText({ text, lang }: { text: string; lang?: string }) {
  const doHighlight = isHighlightableLang(lang);
  return (
    <Box flexDirection="column">
      {text.split('\n').map((line, i) =>
        doHighlight ? (
          <Text key={i}>
            {line
              ? highlightLine(line).map((s, j) => (
                  <Text key={j} color={s.color}>
                    {s.text}
                  </Text>
                ))
              : ' '}
          </Text>
        ) : (
          <Text key={i}>{line || ' '}</Text>
        ),
      )}
    </Box>
  );
}

/** Render a line of text with inline **bold**, *italic*, _italic_, ***bold+italic***, and `code` formatting. */
function InlineText({ text }: { text: string }) {
  const nodes: React.ReactNode[] = [];
  let remaining = text;
  let key = 0;

  while (remaining.length > 0) {
    type Marker = { idx: number; len: number; type: 'bold-italic' | 'bold' | 'italic' | 'italic2' | 'code' };
    const markers: Marker[] = [];

    const bi3 = remaining.indexOf('***');
    if (bi3 >= 0) markers.push({ idx: bi3, len: 3, type: 'bold-italic' });
    const bi = remaining.indexOf('**');
    if (bi >= 0) markers.push({ idx: bi, len: 2, type: 'bold' });
    const ii = remaining.indexOf('*');
    if (ii >= 0) markers.push({ idx: ii, len: 1, type: 'italic' });
    const ui = remaining.indexOf('_');
    if (ui >= 0) markers.push({ idx: ui, len: 1, type: 'italic2' });
    const ci = remaining.indexOf('`');
    if (ci >= 0) markers.push({ idx: ci, len: 1, type: 'code' });

    if (markers.length === 0) {
      nodes.push(<Text key={key}>{remaining}</Text>);
      break;
    }

    // Pick earliest; if tie, prefer longer marker
    markers.sort((a, b) => a.idx - b.idx || b.len - a.len);
    const earliest = markers[0];

    if (earliest.idx > 0) {
      nodes.push(<Text key={key}>{remaining.slice(0, earliest.idx)}</Text>);
      key++;
    }

    const searchFrom = earliest.idx + earliest.len;
    const closeMarker =
      earliest.type === 'bold-italic'
        ? '***'
        : earliest.type === 'bold'
          ? '**'
          : earliest.type === 'italic'
            ? '*'
            : earliest.type === 'italic2'
              ? '_'
              : '`';
    const endIdx = remaining.indexOf(closeMarker, searchFrom);

    if (endIdx < 0) {
      nodes.push(<Text key={key}>{remaining.slice(earliest.idx)}</Text>);
      break;
    }

    const content = remaining.slice(earliest.idx + earliest.len, endIdx);
    const isBold =
      earliest.type === 'bold' || earliest.type === 'bold-italic';
    const isItalic =
      earliest.type === 'italic' ||
      earliest.type === 'italic2' ||
      earliest.type === 'bold-italic';

    if (earliest.type === 'code') {
      nodes.push(
        <Text key={key} color={theme.warning}>
          {content}
        </Text>
      );
    } else {
      nodes.push(
        <Text key={key} bold={isBold} italic={isItalic}>
          {content}
        </Text>
      );
    }
    key++;

    remaining = remaining.slice(endIdx + earliest.len);
  }

  return <Text>{nodes}</Text>;
}
