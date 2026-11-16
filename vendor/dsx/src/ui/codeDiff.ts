/**
 * Structured, line-numbered code diff for edit/write approval previews (#77).
 *
 * Instead of two flat `- old` / `+ new` blocks, the producer (in
 * `src/tools/files.ts`) reads the target file, locates the change, and builds a
 * Claude-Code-style diff: a header (`Update (path)` / `Create (path)`), an
 * "Added N, removed M" summary, and one or more hunks. Each hunk row carries
 * its original line number so the renderer can draw a left gutter with a few
 * lines of surrounding context, removed lines in red, added lines in green.
 *
 * The structure is encoded as JSON behind a magic marker; `decodeCodeDiff`
 * recovers it in the UI. Decoding degrades gracefully — if anything is missing
 * the renderer falls back to the legacy DiffView/FormattedText path.
 */

const MARKER = ' codediff ';

export type DiffRowKind = 'context' | 'add' | 'remove';

export interface DiffRow {
  kind: DiffRowKind;
  /**
   * 1-based line number to show in the gutter. For `remove`/`context` rows this
   * is the line number in the original file; for `add` rows it is the line
   * number in the new file. Undefined rows render with a blank gutter.
   */
  num?: number;
  text: string;
}

export interface DiffHunk {
  rows: DiffRow[];
}

export interface CodeDiff {
  kind: 'create' | 'update';
  /** Path shown in the header (already made relative / display-friendly). */
  path: string;
  added: number;
  removed: number;
  hunks: DiffHunk[];
  /** Width to reserve for the gutter (max line-number digits). */
  gutterWidth: number;
}

export function encodeCodeDiff(diff: CodeDiff): string {
  return MARKER + JSON.stringify(diff);
}

/** Returns the structured diff if `text` was produced by `encodeCodeDiff`, else null. */
export function decodeCodeDiff(text: string): CodeDiff | null {
  if (!text.startsWith(MARKER)) return null;
  try {
    const parsed = JSON.parse(text.slice(MARKER.length)) as CodeDiff;
    if (parsed && Array.isArray(parsed.hunks) && typeof parsed.path === 'string') return parsed;
  } catch {
    /* fall through */
  }
  return null;
}

/** A single edit/replacement op against the original line array. */
interface Op {
  kind: DiffRowKind;
  /** 0-based index into the original lines (for context/remove). */
  oldIndex?: number;
  /** 0-based index into the new lines (for add). */
  newIndex?: number;
  text: string;
}

/**
 * Longest-common-subsequence line diff. Returns a flat op list aligned to the
 * original (context/remove carry oldIndex) and the new file (add carries
 * newIndex). Used to build hunks with correct original line numbers.
 */
function lcsDiff(oldLines: string[], newLines: string[]): Op[] {
  const n = oldLines.length;
  const m = newLines.length;
  // DP table of LCS lengths. (n+1) x (m+1).
  const dp: number[][] = Array.from({ length: n + 1 }, () => new Array<number>(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      dp[i][j] = oldLines[i] === newLines[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
    }
  }
  const ops: Op[] = [];
  let i = 0;
  let j = 0;
  while (i < n && j < m) {
    if (oldLines[i] === newLines[j]) {
      ops.push({ kind: 'context', oldIndex: i, newIndex: j, text: oldLines[i] });
      i++;
      j++;
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      ops.push({ kind: 'remove', oldIndex: i, text: oldLines[i] });
      i++;
    } else {
      ops.push({ kind: 'add', newIndex: j, text: newLines[j] });
      j++;
    }
  }
  while (i < n) ops.push({ kind: 'remove', oldIndex: i, text: oldLines[i++] });
  while (j < m) ops.push({ kind: 'add', newIndex: j, text: newLines[j++] });
  return ops;
}

/**
 * Build a contextual diff from the full original and new file contents.
 *
 * `baseLine` is the 1-based original line number of the first line in
 * `oldText`/`newText` (1 when diffing whole files; the location of an edit's
 * old_string within the file otherwise) so the gutter shows real numbers.
 *
 * `context` controls how many unchanged lines surround each change; runs of
 * unchanged lines longer than 2*context are split into separate hunks.
 */
export function buildCodeDiff(
  kind: 'create' | 'update',
  displayPath: string,
  oldText: string,
  newText: string,
  baseLine = 1,
  context = 3,
): CodeDiff {
  const oldLines = oldText === '' && kind === 'create' ? [] : oldText.split('\n');
  const newLines = newText.split('\n');
  const ops = lcsDiff(oldLines, newLines);

  let added = 0;
  let removed = 0;
  for (const op of ops) {
    if (op.kind === 'add') added++;
    else if (op.kind === 'remove') removed++;
  }

  // Convert ops into rows with absolute (1-based) gutter numbers.
  const rows: DiffRow[] = ops.map((op) => {
    if (op.kind === 'add') return { kind: 'add', num: baseLine + (op.newIndex ?? 0), text: op.text };
    return { kind: op.kind, num: baseLine + (op.oldIndex ?? 0), text: op.text };
  });

  // Group rows into hunks: keep up to `context` context rows around changes,
  // drop long unchanged stretches between separate changes.
  const changeIdx = rows.flatMap((r, idx) => (r.kind === 'context' ? [] : [idx]));
  let hunks: DiffHunk[] = [];
  if (changeIdx.length === 0) {
    hunks = [];
  } else {
    const ranges: Array<[number, number]> = [];
    let start = Math.max(0, changeIdx[0] - context);
    let end = Math.min(rows.length - 1, changeIdx[0] + context);
    for (let k = 1; k < changeIdx.length; k++) {
      const c = changeIdx[k];
      if (c - context <= end + 1) {
        end = Math.min(rows.length - 1, c + context);
      } else {
        ranges.push([start, end]);
        start = Math.max(0, c - context);
        end = Math.min(rows.length - 1, c + context);
      }
    }
    ranges.push([start, end]);
    hunks = ranges.map(([s, e]) => ({ rows: rows.slice(s, e + 1) }));
  }

  const maxNum = rows.reduce((mx, r) => Math.max(mx, r.num ?? 0), 0);
  const gutterWidth = Math.max(String(maxNum).length, 1);

  return { kind, path: displayPath, added, removed, hunks, gutterWidth };
}

/** Pluralized "Added N line(s), removed M line(s)" summary. */
export function diffSummary(added: number, removed: number): string {
  const a = `${added} ${added === 1 ? 'line' : 'lines'}`;
  const r = `${removed} ${removed === 1 ? 'line' : 'lines'}`;
  return `Added ${a}, removed ${r}`;
}

/**
 * Cap a CodeDiff so a huge change can't flood the prompt: limit the total
 * number of rendered rows across hunks. Returns the (possibly truncated) diff
 * and how many rows were dropped.
 */
export function capCodeDiff(diff: CodeDiff, max = 40): { diff: CodeDiff; dropped: number } {
  let budget = max;
  const hunks: DiffHunk[] = [];
  let dropped = 0;
  for (const hunk of diff.hunks) {
    if (budget <= 0) {
      dropped += hunk.rows.length;
      continue;
    }
    if (hunk.rows.length <= budget) {
      hunks.push(hunk);
      budget -= hunk.rows.length;
    } else {
      hunks.push({ rows: hunk.rows.slice(0, budget) });
      dropped += hunk.rows.length - budget;
      budget = 0;
    }
  }
  return { diff: { ...diff, hunks }, dropped };
}
