import type { Tool } from './index.js';
import { truncate } from './index.js';

const FETCH_TIMEOUT_MS = 30_000;
const MAX_CHARS = 20_000;

const ENTITIES: Record<string, string> = {
  '&amp;': '&',
  '&lt;': '<',
  '&gt;': '>',
  '&quot;': '"',
  '&#39;': "'",
  '&apos;': "'",
  '&nbsp;': ' ',
};

export function htmlToText(html: string): string {
  return html
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<style[\s\S]*?<\/style>/gi, '')
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/<\/(p|div|li|h[1-6]|tr|br|section|article)>/gi, '\n')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&[a-z]+;|&#\d+;/gi, (e) => ENTITIES[e.toLowerCase()] ?? ' ')
    .replace(/[ \t]+/g, ' ')
    .replace(/\s*\n\s*/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

export const fetchUrlTool: Tool = {
  name: 'fetch_url',
  description:
    'Fetch a URL and return its content as readable text. HTML is stripped to plain text; ' +
    'JSON, markdown, and plain text pass through unmodified. Use after web_search to read a result in full.',
  parameters: {
    type: 'object',
    properties: {
      url: { type: 'string', description: 'The http(s) URL to fetch.' },
      max_chars: { type: 'number', description: `Max characters to return (default ${MAX_CHARS}).` },
    },
    required: ['url'],
  },
  // The model controls the URL, so every fetch is an outward-facing request —
  // gate it behind approval like bash/write, not like the local read-only tools.
  needsApproval: true,
  summarize: (args) => String(args.url ?? ''),
  async run(args) {
    const url = String(args.url ?? '');
    if (!/^https?:\/\//i.test(url)) {
      return 'Error: only http(s) URLs are supported.';
    }
    const maxChars = Math.min(Number(args.max_chars) || MAX_CHARS, 100_000);

    let response: Response;
    try {
      response = await fetch(url, {
        signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
        headers: { 'User-Agent': 'dsx/0.1 (coding agent)' },
      });
    } catch (err) {
      const reason = err instanceof Error && err.name === 'TimeoutError'
        ? `timed out after ${FETCH_TIMEOUT_MS / 1000}s`
        : err instanceof Error ? err.message : String(err);
      return `Error: fetch failed — ${reason}`;
    }

    if (!response.ok) {
      return `Error: HTTP ${response.status} ${response.statusText} for ${url}`;
    }

    const contentType = response.headers.get('content-type') ?? '';
    const body = await response.text();
    const text = contentType.includes('text/html') ? htmlToText(body) : body;
    return truncate(text || '(empty response)', maxChars);
  },
};
