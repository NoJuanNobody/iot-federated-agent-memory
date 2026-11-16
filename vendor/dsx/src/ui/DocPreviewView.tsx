import React from 'react';
import { Box, Text } from 'ink';
import { Markdown } from './MarkdownView.js';
import { DiffView } from './DiffView.js';
import { theme } from './theme.js';
import type { DocPreview } from './docPreview.js';

/**
 * Renders a structured Nyx doc approval preview (#65): a plain-text metadata
 * header (method/path/title/stage) above a body that is either rendered
 * markdown (create / new content) or a red/green diff (update vs. current
 * content). When only non-content fields change the body is omitted entirely so
 * there's no empty diff block.
 */
export function DocPreviewView({ preview }: { preview: DocPreview }) {
  return (
    <Box flexDirection="column">
      {preview.meta.map((line, i) => (
        <Text key={i} color={theme.accent}>
          {line === '' ? ' ' : line}
        </Text>
      ))}
      {preview.body.kind !== 'none' && (
        <Box flexDirection="column" marginTop={1}>
          {preview.body.kind === 'markdown' ? (
            <Markdown content={preview.body.content} />
          ) : (
            <DiffView text={preview.body.lines.join('\n')} />
          )}
        </Box>
      )}
    </Box>
  );
}
