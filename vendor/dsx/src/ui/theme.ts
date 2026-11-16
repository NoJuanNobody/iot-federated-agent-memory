/**
 * Nyx visual identity — "Goddess of Night" (issue #49).
 *
 * Single source of truth for the Ink UI's accent colors. Values are hex so
 * truecolor terminals render the exact violet; Ink/chalk automatically
 * downsamples to the nearest 256/16-color on lesser terminals. (The startup
 * banner in `src/index.tsx` uses the same violet register via ANSI-256 and
 * proves the fallback reads well.)
 *
 * Design notes:
 * - We deliberately do NOT define a background color. A TUI should inherit the
 *   user's terminal background instead of fighting their theme; forcing a dark
 *   fill looks broken on light terminals.
 * - `accent` is the canonical brand violet from the Higgsfield design sheet.
 *   `accentBright` is a lighter lavender used wherever violet sits directly on
 *   the terminal background as TEXT (carets, headers, selection) and needs more
 *   contrast — mirroring the logo, which pairs a light wordmark face with a
 *   deep-violet shadow.
 * - Semantic colors come straight from the design sheet so success/warning/
 *   error/info read conventionally while still matching the brand palette.
 */
export const theme = {
  /** Brand violet (design sheet #8A28E2) — overlay borders, spinner. */
  accent: '#8A28E2',
  /** Lavender — violet-as-text: carets, headers, the user prompt, selection. */
  accentBright: '#B794F6',
  /** Moonlit silver — primary text where we want lift above the terminal default. */
  text: '#E0E0EA',
  /** Secondary / muted text. Named so it tracks the user's dim convention. */
  dim: 'gray',

  /** Semantic palette (design sheet). */
  success: '#00C853',
  warning: '#FFAB00',
  error: '#D22F2F',
  info: '#0080FF',

  /**
   * Syntax-highlighting palette for fenced code blocks. A Night-Owl-style set
   * tuned to sit alongside the violet brand: mauve keywords, soft-green strings,
   * coral numbers, slate comments. See `highlight.ts`.
   */
  code: {
    keyword: '#C792EA', // mauve/violet — keywords, control flow
    string: '#C3E88D', // soft green — string/char literals
    number: '#F78C6C', // coral — numeric literals
    comment: '#637777', // muted slate — comments
    func: '#82AAFF', // blue — function/method calls
    builtin: '#89DDFF', // cyan — builtins, constants (true/false/null/self)
  },
} as const;
