import { theme } from './theme.js';

/** A run of code with an optional foreground color (undefined = inherit). */
export interface Span {
  text: string;
  color?: string;
}

/**
 * Languages this tokenizer renders well: C-family/scripting languages where
 * `//`/`#` comments, quoted strings, and numeric literals carry the same
 * meaning the tokenizer assumes. A code fence tagged with one of these (or any
 * common alias) gets syntax colors; anything else — no tag, `text`, `log`,
 * `console`, prose, data dumps — renders verbatim. Highlighting only when the
 * language is known keeps the tokenizer away from content that isn't code.
 */
const HIGHLIGHTABLE_LANGS = new Set([
  'js', 'jsx', 'mjs', 'cjs', 'javascript', 'node',
  'ts', 'tsx', 'typescript',
  'py', 'python', 'python3',
  'sh', 'bash', 'shell', 'zsh', 'ksh',
  'json', 'jsonc', 'json5',
  'c', 'h', 'cpp', 'cc', 'cxx', 'hpp', 'hxx', 'objc',
  'java', 'kt', 'kotlin', 'scala', 'groovy',
  'go', 'golang', 'rs', 'rust',
  'rb', 'ruby', 'php', 'swift', 'dart',
  'css', 'scss', 'sass', 'less',
  'sql',
]);

/**
 * Whether a fenced-code `lang` tag names a language the tokenizer should color.
 * Case- and whitespace-insensitive; undefined/empty/unrecognized → false, so
 * untagged or non-code fences render plain.
 */
export function isHighlightableLang(lang?: string): boolean {
  if (!lang) return false;
  return HIGHLIGHTABLE_LANGS.has(lang.trim().toLowerCase());
}

/**
 * Keywords and constants, unioned across the languages we commonly render
 * (JS/TS, Python, shell, JSON-ish). Highlighting doesn't need to be a real
 * parser — a generous union reads well across snippets without per-language
 * dispatch.
 *
 * Deliberately excludes words that are also common in English prose (`in`, `of`,
 * `as`, `with`, `and`, `or`, `is`, `not`, `do`, `new`, `this`, `super`, `from`,
 * `then`, `type`, `case`, `match`). This tokenizer runs over arbitrary tool
 * output and markdown code fences whose contents aren't always real code, so
 * coloring those words turned prose into a patchwork rather than aiding reading.
 */
const KEYWORDS = new Set([
  // JS/TS
  'const', 'let', 'var', 'function', 'return', 'if', 'else', 'for', 'while',
  'switch', 'break', 'continue', 'class', 'extends',
  'import', 'export', 'default', 'async', 'await', 'yield', 'try', 'catch',
  'finally', 'throw', 'typeof', 'instanceof', 'void', 'delete', 'interface',
  'enum', 'implements', 'public', 'private', 'protected', 'readonly', 'static',
  // Python
  'def', 'elif', 'lambda', 'pass', 'raise',
  'except', 'global', 'nonlocal', 'assert', 'del',
  // shell
  'fi', 'esac', 'fn',
]);

/**
 * Constants / common builtins, rendered in the builtin color. Drops `set` and
 * `list`, which read as ordinary English nouns far more often than as builtins.
 */
const BUILTINS = new Set([
  'true', 'false', 'null', 'undefined', 'None', 'True', 'False', 'NaN', 'Infinity',
  'self', 'cls', 'console', 'print', 'len', 'range', 'int', 'str', 'float', 'bool',
  'dict', 'tuple', 'Object', 'Array', 'String', 'Number', 'Boolean',
]);

// One token at a time, in priority order:
//   1 comment  2 string (incl. triple-quoted / template)  3 number  4 word  5 ws  6 other
//
// Single-quoted strings require a non-word char (or start of line) before the
// opening quote so apostrophes in prose contractions/possessives ("doesn't",
// "it's") don't open a "string" that smears color across the rest of the line.
const TOKEN = new RegExp(
  [
    /(\/\/[^\n]*|#[^\n]*)/.source, // 1 line comment (// or #)
    /("""[\s\S]*?"""|(?<![A-Za-z0-9_$])'''[\s\S]*?'''|"(?:\\.|[^"\\])*"|(?<![A-Za-z0-9_$])'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`)/.source, // 2 string
    /(\b\d[\d_]*\.?\d*(?:e[+-]?\d+)?\b)/.source, // 3 number
    /([A-Za-z_$][A-Za-z0-9_$]*)/.source, // 4 word
    /(\s+)/.source, // 5 whitespace
    /(.)/.source, // 6 anything else (operators, punctuation)
  ].join('|'),
  'gi',
);

/**
 * Tokenize a single line of code into colored spans. Line-based (so a string or
 * comment that spans multiple physical lines is highlighted per visible line),
 * which is the right granularity for the Ink renderer. Falls back to no color
 * for plain identifiers, operators, and whitespace so the result stays legible
 * rather than a rainbow.
 */
export function highlightLine(line: string): Span[] {
  const spans: Span[] = [];
  TOKEN.lastIndex = 0;
  let m: RegExpExecArray | null;
  while ((m = TOKEN.exec(line)) !== null) {
    const [, comment, str, num, word, ws] = m;
    if (comment !== undefined) {
      spans.push({ text: comment, color: theme.code.comment });
    } else if (str !== undefined) {
      spans.push({ text: str, color: theme.code.string });
    } else if (num !== undefined) {
      spans.push({ text: num, color: theme.code.number });
    } else if (word !== undefined) {
      // No word-before-`(` → function heuristic: in prose, every parenthetical
      // ("output (we saw…)") lit up the preceding word. Color only known
      // keywords/builtins, which are deliberately scoped to non-prose words.
      if (KEYWORDS.has(word)) spans.push({ text: word, color: theme.code.keyword });
      else if (BUILTINS.has(word)) spans.push({ text: word, color: theme.code.builtin });
      else spans.push({ text: word });
    } else if (ws !== undefined) {
      spans.push({ text: ws });
    } else {
      spans.push({ text: m[6] });
    }
  }
  return spans;
}
