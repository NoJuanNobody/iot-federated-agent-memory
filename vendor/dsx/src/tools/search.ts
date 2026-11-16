import type { Tool } from './index.js';

const BRAVE_ENDPOINT = 'https://api.search.brave.com/res/v1/web/search';
const SEARCH_TIMEOUT_MS = 15_000;

interface BraveResult {
  title?: string;
  url?: string;
  description?: string;
}

export const webSearchTool: Tool = {
  name: 'web_search',
  description:
    'Search the web and return results as numbered title/URL/snippet entries. ' +
    'Follow up with fetch_url on any result worth reading in full.',
  parameters: {
    type: 'object',
    properties: {
      query: { type: 'string', description: 'The search query.' },
      count: { type: 'number', description: 'Number of results, 1-10 (default 5).' },
    },
    required: ['query'],
  },
  // Queries go to a fixed, trusted endpoint and return text the user can see
  // in the transcript — low enough risk to run without a prompt, like grep.
  needsApproval: false,
  summarize: (args) => String(args.query ?? ''),
  async run(args, ctx) {
    if (!ctx.braveApiKey) {
      return (
        'Web search is not configured. Tell the user to get a free key at ' +
        'https://brave.com/search/api and export BRAVE_API_KEY, then restart dsx.'
      );
    }

    const query = String(args.query ?? '').trim();
    if (!query) return 'Error: query must not be empty.';
    const count = Math.min(Math.max(Number(args.count) || 5, 1), 10);

    const params = new URLSearchParams({ q: query, count: String(count) });
    let response: Response;
    try {
      response = await fetch(`${BRAVE_ENDPOINT}?${params}`, {
        signal: AbortSignal.timeout(SEARCH_TIMEOUT_MS),
        headers: {
          Accept: 'application/json',
          'X-Subscription-Token': ctx.braveApiKey,
        },
      });
    } catch (err) {
      return `Error: search request failed — ${err instanceof Error ? err.message : String(err)}`;
    }

    if (response.status === 429) {
      return 'Error: Brave Search rate limit hit — wait a moment before searching again.';
    }
    if (!response.ok) {
      return `Error: Brave Search returned HTTP ${response.status} ${response.statusText}`;
    }

    const data = (await response.json()) as { web?: { results?: BraveResult[] } };
    const results = data.web?.results ?? [];
    if (results.length === 0) return 'No results.';

    return results
      .slice(0, count)
      .map((r, i) => `${i + 1}. ${r.title ?? '(untitled)'}\n   ${r.url ?? ''}\n   ${r.description ?? ''}`)
      .join('\n\n');
  },
};
