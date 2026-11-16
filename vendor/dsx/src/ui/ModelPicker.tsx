import React, { useMemo, useState } from 'react';
import { Box, Text, useInput } from 'ink';
import TextInput from 'ink-text-input';
import { type ModelInfo, filterModels, formatContext, formatPrice } from '../models.js';
import { theme } from './theme.js';

/** How many rows of the (scrolling) list to show at once. */
const VISIBLE = 8;

interface Props {
  models: ModelInfo[];
  current: string;
  onSelect: (id: string) => void;
  onCancel: () => void;
}

/**
 * Interactive model picker: a filter field over a scrolling, arrow-navigable
 * list. Enter selects the highlighted row, Esc cancels. Rendered in place of
 * the input box, so it owns keyboard focus while open.
 */
export function ModelPicker({ models, current, onSelect, onCancel }: Props) {
  const [filter, setFilter] = useState('');
  const [index, setIndex] = useState(0);

  const filtered = useMemo(() => filterModels(models, filter), [models, filter]);
  // The list shrinks as the filter narrows; keep the cursor in range.
  const selectedIndex = Math.min(index, Math.max(0, filtered.length - 1));

  // ink-text-input handles character input, backspace, and left/right cursor;
  // up/down and Enter are ignored there (we omit onSubmit), so we own them here.
  useInput((_input, key) => {
    if (key.escape) {
      onCancel();
      return;
    }
    if (key.return) {
      const sel = filtered[selectedIndex];
      if (sel) onSelect(sel.id);
      return;
    }
    if (key.upArrow) {
      setIndex(Math.max(0, selectedIndex - 1));
      return;
    }
    if (key.downArrow) {
      setIndex(Math.min(filtered.length - 1, selectedIndex + 1));
    }
  });

  // Scroll window centered on the selection.
  const start = Math.max(0, Math.min(selectedIndex - Math.floor(VISIBLE / 2), Math.max(0, filtered.length - VISIBLE)));
  const window = filtered.slice(start, start + VISIBLE);

  return (
    <Box borderStyle="round" borderColor={theme.accent} flexDirection="column" paddingX={1} marginTop={1}>
      <Text bold color={theme.accentBright}>
        Select a model — {filtered.length} match{filtered.length === 1 ? '' : 'es'}
      </Text>
      <Box>
        <Text color={theme.accentBright}>search › </Text>
        <TextInput
          value={filter}
          onChange={(v) => {
            setFilter(v);
            setIndex(0);
          }}
        />
      </Box>
      {window.map((m, i) => {
        const isSelected = start + i === selectedIndex;
        const meta = [formatContext(m), formatPrice(m)].filter(Boolean).join(' · ');
        return (
          <Text key={m.id} inverse={isSelected} color={isSelected ? theme.accentBright : undefined}>
            {isSelected ? '❯ ' : '  '}
            {m.id}
            {m.id === current ? ' (current)' : ''}
            {meta ? `  ${meta}` : ''}
          </Text>
        );
      })}
      {filtered.length === 0 && <Text dimColor>No models match “{filter}”.</Text>}
      <Text dimColor>↑/↓ navigate · Enter select · Esc cancel</Text>
    </Box>
  );
}
