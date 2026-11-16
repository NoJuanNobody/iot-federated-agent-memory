import path from 'node:path';
import type { Tool, ToolContext } from './index.js';
import { truncate } from './index.js';
import { diffBlock } from './files.js';
import { encodeDocPreview, type DocPreview } from '../ui/docPreview.js';
import { parseNyxDoc, writePulledDoc } from './nyxSync.js';

/** Cap diff/markdown previews so a huge change can't flood the approval prompt. */
function capPreviewLines(lines: string[], max = 80): string[] {
  if (lines.length <= max) return lines;
  return [...lines.slice(0, max), `… (+${lines.length - max} more lines)`];
}

const NYX_DEFAULT_URL = 'http://localhost:3001';
const NYX_TIMEOUT_MS = 30_000;

const NOT_CONFIGURED =
  'Nyx is not configured — set NYX_API_KEY (and NYX_TEAM_ID), then restart dsx.';

/** Base URL without a trailing slash so path joins stay clean. */
function baseUrl(ctx: ToolContext): string {
  return (ctx.nyxApiUrl ?? NYX_DEFAULT_URL).replace(/\/+$/, '');
}

interface NyxRequest {
  method: 'GET' | 'POST' | 'PUT';
  /** Path beginning with `/`, e.g. `/api/documents`. */
  path: string;
  /** Parsed and JSON-stringified as the request body when present. */
  body?: unknown;
}

/**
 * Issue an authenticated request to the Nyx backend. Returns either the
 * truncated JSON response body (success) or a clear error string — never
 * throws, so a misbehaving backend can't crash the agent loop.
 */
async function nyxFetch(ctx: ToolContext, req: NyxRequest): Promise<string> {
  if (!ctx.nyxApiKey) return NOT_CONFIGURED;

  const headers: Record<string, string> = {
    Accept: 'application/json',
    Authorization: `Bearer ${ctx.nyxApiKey}`,
  };
  if (req.body !== undefined) headers['Content-Type'] = 'application/json';

  let response: Response;
  try {
    response = await fetch(`${baseUrl(ctx)}${req.path}`, {
      method: req.method,
      headers,
      body: req.body !== undefined ? JSON.stringify(req.body) : undefined,
      signal: ctx.signal ?? AbortSignal.timeout(NYX_TIMEOUT_MS),
    });
  } catch (err) {
    return `Error: Nyx request failed — ${err instanceof Error ? err.message : String(err)}`;
  }

  const text = await response.text();
  if (!response.ok) {
    return `Error: Nyx returned HTTP ${response.status} ${response.statusText}${
      text ? `\n${truncate(text, 2000)}` : ''
    }`;
  }
  return truncate(text || '(empty response)');
}

/** Resolve the team id: an explicit arg overrides the configured default. */
function teamId(args: Record<string, unknown>, ctx: ToolContext): string | undefined {
  const arg = args.teamId;
  if (arg !== undefined && arg !== null && String(arg).trim()) return String(arg).trim();
  return ctx.nyxTeamId;
}

export const nyxSearchDocsTool: Tool = {
  name: 'nyx_search_docs',
  description:
    'List documents from the Nyx backend for a team. Returns a Document[] as JSON. ' +
    'Optionally filter/sort by stage, sort, limit, and includeArchived.',
  parameters: {
    type: 'object',
    properties: {
      teamId: { type: 'string', description: 'Team id (defaults to NYX_TEAM_ID).' },
      stage: { type: 'string', description: 'Filter by lifecycle stage.' },
      sort: { type: 'string', description: 'Sort order for results.' },
      limit: { type: 'number', description: 'Max number of documents to return.' },
      includeArchived: { type: 'boolean', description: 'Include archived (soft-deleted) docs.' },
    },
  },
  needsApproval: false,
  summarize: (args) => `team ${teamIdSummary(args)}`,
  async run(args, ctx) {
    if (!ctx.nyxApiKey) return NOT_CONFIGURED;
    const team = teamId(args, ctx);
    if (!team) return 'Error: no teamId — pass teamId or set NYX_TEAM_ID.';
    const params = new URLSearchParams({ teamId: team });
    if (args.stage !== undefined) params.set('stage', String(args.stage));
    if (args.sort !== undefined) params.set('sort', String(args.sort));
    if (args.limit !== undefined) params.set('limit', String(args.limit));
    if (args.includeArchived !== undefined) {
      params.set('includeArchived', String(Boolean(args.includeArchived)));
    }
    return nyxFetch(ctx, { method: 'GET', path: `/api/documents?${params}` });
  },
};

export const nyxReadDocTool: Tool = {
  name: 'nyx_read_doc',
  description: 'Read a single Nyx document by id. Returns the Document as JSON (404 if missing).',
  parameters: {
    type: 'object',
    properties: {
      id: { type: 'string', description: 'Document id.' },
    },
    required: ['id'],
  },
  needsApproval: false,
  summarize: (args) => String(args.id ?? ''),
  async run(args, ctx) {
    if (!ctx.nyxApiKey) return NOT_CONFIGURED;
    const id = String(args.id ?? '').trim();
    if (!id) return 'Error: id must not be empty.';
    const raw = await nyxFetch(ctx, {
      method: 'GET',
      path: `/api/documents/${encodeURIComponent(id)}`,
    });
    if (raw.startsWith('Error:') || raw === NOT_CONFIGURED) return raw;
    return formatDocAsMarkdown(raw);
  },
};

/**
 * Turn the backend's raw document JSON into readable markdown: a short metadata
 * header (id, title, stage, path, updatedAt — whichever are present) followed by
 * the document `content` body. The result is BOTH shown in the transcript AND
 * recorded as the model's tool message, so it stays clean and parseable for the
 * model (ids are right there in the header). Degrades gracefully: if the JSON
 * can't be parsed (e.g. an 8000-char truncation), the raw text is returned.
 */
function formatDocAsMarkdown(raw: string): string {
  let doc: Record<string, unknown>;
  try {
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return raw;
    doc = parsed as Record<string, unknown>;
  } catch {
    return raw;
  }

  const str = (v: unknown): string | undefined =>
    typeof v === 'string' && v.trim() ? v : v != null && typeof v !== 'object' ? String(v) : undefined;

  const meta: string[] = [];
  const title = str(doc.title);
  if (title) meta.push(`**${title}**`);
  for (const [label, key] of [
    ['id', 'id'],
    ['stage', 'stage'],
    ['path', 'path'],
    ['updatedAt', 'updatedAt'],
  ] as const) {
    const value = str(doc[key]);
    if (value) meta.push(`${label}: ${value}`);
  }

  const content = typeof doc.content === 'string' ? doc.content : '';
  const header = meta.join('  \n');
  if (!header) return content || raw;
  return content ? `${header}\n\n---\n\n${content}` : header;
}

/**
 * Fetch a single document's raw JSON from `GET /api/documents/:id` — the same
 * endpoint `nyx_read_doc` uses. Exported so the background poller can reuse the
 * exact request shape (auth, timeout, error handling) the tools use.
 */
export function fetchDocRaw(ctx: ToolContext, id: string): Promise<string> {
  return nyxFetch(ctx, {
    method: 'GET',
    path: `/api/documents/${encodeURIComponent(id)}`,
  });
}

export const nyxPullDocTool: Tool = {
  name: 'nyx_pull_doc',
  description:
    'Pull a Nyx document by id into the working folder as a viewable markdown file under ' +
    '<cwd>/.nyx/docs/, with YAML frontmatter (id, title, stage, path, updatedAt). The file ' +
    'is tracked in <cwd>/.nyx/manifest.json and kept in sync from the cloud by the background ' +
    'poller. Returns the local path on success.',
  parameters: {
    type: 'object',
    properties: {
      id: { type: 'string', description: 'Document id to pull (required).' },
    },
    required: ['id'],
  },
  needsApproval: true,
  summarize: (args) => String(args.id ?? ''),
  preview(args, ctx) {
    const id = String(args.id ?? '').trim();
    const target = path.join(ctx.cwd, '.nyx', 'docs', `<title>-${id || 'id'}.md`);
    return encodeDocPreview({
      meta: [`GET /api/documents/${id}`, `→ writes ${target}`],
      body: { kind: 'none' },
    });
  },
  async run(args, ctx) {
    if (!ctx.nyxApiKey) return NOT_CONFIGURED;
    const id = String(args.id ?? '').trim();
    if (!id) return 'Error: id must not be empty.';
    const raw = await fetchDocRaw(ctx, id);
    if (raw.startsWith('Error:') || raw === NOT_CONFIGURED) return raw;
    const doc = parseNyxDoc(raw, id);
    if (!doc) return 'Error: could not parse the document response from Nyx.';
    let entry;
    try {
      entry = writePulledDoc(ctx.cwd, doc);
    } catch (err) {
      return `Error: failed to write the doc — ${err instanceof Error ? err.message : String(err)}`;
    }
    return `Pulled "${doc.title}" → ${entry.localPath}${
      doc.updatedAt ? ` (updatedAt ${doc.updatedAt})` : ''
    }`;
  },
};

export const nyxCreateDocTool: Tool = {
  name: 'nyx_create_doc',
  description:
    'Create a new Nyx document. title and teamId are required (teamId defaults to NYX_TEAM_ID). ' +
    'Returns the created Document as JSON.',
  parameters: {
    type: 'object',
    properties: {
      title: { type: 'string', description: 'Document title (required).' },
      teamId: { type: 'string', description: 'Team id (defaults to NYX_TEAM_ID).' },
      content: { type: 'string', description: 'Document body.' },
      path: { type: 'string', description: 'Logical path for the document.' },
      stage: { type: 'string', description: 'Lifecycle stage.' },
      templateId: { type: 'string', description: 'Template to base the document on.' },
    },
    required: ['title'],
  },
  needsApproval: true,
  summarize: (args) => String(args.title ?? ''),
  preview(args, ctx) {
    const body = createDocBody(args, ctx);
    const meta = ['POST /api/documents'];
    if (body.title) meta.push(`title: ${body.title}`);
    meta.push(`teamId: ${body.teamId || '(NYX_TEAM_ID)'}`);
    if (body.path) meta.push(`path: ${body.path}`);
    if (body.stage) meta.push(`stage: ${body.stage}`);
    if (body.templateId) meta.push(`templateId: ${body.templateId}`);
    const preview: DocPreview =
      body.content !== undefined && body.content !== ''
        ? { meta, body: { kind: 'markdown', content: body.content } }
        : { meta, body: { kind: 'none' } };
    return encodeDocPreview(preview);
  },
  async run(args, ctx) {
    if (!ctx.nyxApiKey) return NOT_CONFIGURED;
    const body = createDocBody(args, ctx);
    if (!body.title) return 'Error: title is required.';
    if (!body.teamId) return 'Error: no teamId — pass teamId or set NYX_TEAM_ID.';
    return nyxFetch(ctx, { method: 'POST', path: '/api/documents', body });
  },
};

export const nyxUpdateDocTool: Tool = {
  name: 'nyx_update_doc',
  description:
    'Update an existing Nyx document by id. Any of title, content, path, stage may be set. ' +
    'Returns the updated Document as JSON.',
  parameters: {
    type: 'object',
    properties: {
      id: { type: 'string', description: 'Document id (required).' },
      title: { type: 'string', description: 'New title.' },
      content: { type: 'string', description: 'New body.' },
      path: { type: 'string', description: 'New logical path.' },
      stage: { type: 'string', description: 'New lifecycle stage.' },
    },
    required: ['id'],
  },
  needsApproval: true,
  summarize: (args) => String(args.id ?? ''),
  async preview(args, ctx) {
    const id = String(args.id ?? '');
    const body = updateDocBody(args);
    const meta = [`PUT /api/documents/${id}`];
    if (body.title !== undefined) meta.push(`title: ${body.title}`);
    if (body.path !== undefined) meta.push(`path: ${body.path}`);
    if (body.stage !== undefined) meta.push(`stage: ${body.stage}`);

    // No content change → just the metadata, no (empty) diff block.
    if (body.content === undefined) {
      return encodeDocPreview({ meta, body: { kind: 'none' } });
    }

    // Fetch the document's CURRENT content so the diff's red lines reflect what
    // is actually being replaced. Degrade gracefully: if Nyx is unreachable /
    // not configured / the doc can't be parsed, show the new content as
    // all-added markdown rather than crashing the approval prompt.
    const current = await fetchDocContent(ctx, id);
    if (current === null) {
      return encodeDocPreview({ meta, body: { kind: 'markdown', content: body.content } });
    }
    if (current === body.content) {
      meta.push('(content unchanged)');
      return encodeDocPreview({ meta, body: { kind: 'none' } });
    }
    const lines = capPreviewLines(diffBlock(current, body.content));
    return encodeDocPreview({ meta, body: { kind: 'diff', lines } });
  },
  async run(args, ctx) {
    if (!ctx.nyxApiKey) return NOT_CONFIGURED;
    const id = String(args.id ?? '').trim();
    if (!id) return 'Error: id must not be empty.';
    return nyxFetch(ctx, {
      method: 'PUT',
      path: `/api/documents/${encodeURIComponent(id)}`,
      body: updateDocBody(args),
    });
  },
};

export const nyxDetectDriftTool: Tool = {
  name: 'nyx_detect_drift',
  description:
    'Detect drift between a spec and its implementation. Pass the raw spec and code content; ' +
    'returns { hasDrift, driftScore (0-10), details, suggestions[] } as JSON.',
  parameters: {
    type: 'object',
    properties: {
      specContent: { type: 'string', description: 'The spec/document content (required).' },
      codeContent: { type: 'string', description: 'The implementation/code content (required).' },
    },
    required: ['specContent', 'codeContent'],
  },
  needsApproval: false,
  summarize: () => 'drift check',
  async run(args, ctx) {
    if (!ctx.nyxApiKey) return NOT_CONFIGURED;
    const specContent = String(args.specContent ?? '');
    const codeContent = String(args.codeContent ?? '');
    if (!specContent || !codeContent) {
      return 'Error: both specContent and codeContent are required.';
    }
    return nyxFetch(ctx, {
      method: 'POST',
      path: '/api/ai/detect-drift',
      body: { specContent, codeContent },
    });
  },
};

export const nyxCreateTicketTool: Tool = {
  name: 'nyx_create_ticket',
  description:
    'Create a GitHub or Jira ticket linked to a Nyx document. Requires the team to have the ' +
    'matching integration configured. Returns the created Ticket as JSON.',
  parameters: {
    type: 'object',
    properties: {
      id: { type: 'string', description: 'Document id to attach the ticket to (required).' },
      provider: { type: 'string', enum: ['github', 'jira'], description: 'Ticket provider (required).' },
      title: { type: 'string', description: 'Ticket title (required).' },
      body: { type: 'string', description: 'Ticket body (required).' },
      repo: {
        type: 'object',
        description: 'Target repo for github tickets.',
        properties: {
          owner: { type: 'string' },
          name: { type: 'string' },
        },
      },
    },
    required: ['id', 'provider', 'title', 'body'],
  },
  needsApproval: true,
  summarize: (args) => `${String(args.provider ?? '')}: ${String(args.title ?? '')}`,
  preview(args) {
    const id = String(args.id ?? '');
    return `POST /api/documents/${id}/tickets\n${JSON.stringify(ticketBody(args), null, 2)}`;
  },
  async run(args, ctx) {
    if (!ctx.nyxApiKey) return NOT_CONFIGURED;
    const id = String(args.id ?? '').trim();
    if (!id) return 'Error: id must not be empty.';
    const body = ticketBody(args);
    if (!body.provider || !body.title || !body.body) {
      return 'Error: provider, title, and body are required.';
    }
    return nyxFetch(ctx, {
      method: 'POST',
      path: `/api/documents/${encodeURIComponent(id)}/tickets`,
      body,
    });
  },
};

export const nyxListTemplatesTool: Tool = {
  name: 'nyx_list_templates',
  description:
    'List the document templates available in Nyx so a doc can be drafted on the right one. ' +
    'Returns a Template[] as JSON; each template has id, name, description, content, the single ' +
    'lifecycle `stage` slug it belongs to, sortOrder, lifecycleId, and teamId (null = built-in). ' +
    'Pass teamId to also include that team\'s custom templates; pass stage to filter to one stage. ' +
    'Templates do NOT embed their stage list — use nyx_list_lifecycles to see the ordered stages a ' +
    'doc advances through. Use this before nyx_create_doc to pick a templateId. ' +
    'Read-only; runs without approval.',
  // CONFIRMED against the Nyx backend (apps/api/src/routes/templates.ts):
  //   GET /api/templates[?teamId=&stage=&lifecycleId=]
  //   -> [{ id, stage, name, description, content, sortOrder, teamId, lifecycleId, createdAt }]
  // Lifecycle stages are a SEPARATE resource (see nyxListLifecyclesTool).
  parameters: {
    type: 'object',
    properties: {
      teamId: {
        type: 'string',
        description: 'Team id to scope templates to (defaults to NYX_TEAM_ID).',
      },
      stage: {
        type: 'string',
        description: 'Optional lifecycle stage slug to filter by (e.g. "definition").',
      },
    },
  },
  needsApproval: false,
  summarize: (args) => `team ${teamIdSummary(args)}`,
  async run(args, ctx) {
    if (!ctx.nyxApiKey) return NOT_CONFIGURED;
    const team = teamId(args, ctx);
    const stage = String(args.stage ?? '').trim();
    const params = new URLSearchParams();
    if (team) params.set('teamId', team);
    if (stage) params.set('stage', stage);
    const query = params.toString();
    return nyxFetch(ctx, {
      method: 'GET',
      path: `/api/templates${query ? `?${query}` : ''}`,
    });
  },
};

export const nyxListLifecyclesTool: Tool = {
  name: 'nyx_list_lifecycles',
  description:
    'List Nyx lifecycles, each with its ordered `stages`, so the agent can walk a document ' +
    'stage-by-stage. Returns a Lifecycle[] (or a single Lifecycle when slug is given) as JSON; ' +
    'each stage has slug, label, sortOrder (the ordering), and description. A template\'s ' +
    'lifecycleId / stage slug map into these. Read-only; runs without approval.',
  // CONFIRMED against the Nyx backend (apps/api/src/routes/lifecycles.ts):
  //   GET /api/lifecycles            -> [{ ...lifecycle, stages: [{ slug, label, sortOrder, description, ... }] }]
  //   GET /api/lifecycles/:slug      -> single lifecycle with the same nested stages
  parameters: {
    type: 'object',
    properties: {
      slug: {
        type: 'string',
        description: 'Optional lifecycle slug to fetch a single lifecycle (omit to list all).',
      },
    },
  },
  needsApproval: false,
  summarize: (args) => String(args.slug ?? 'all'),
  async run(args, ctx) {
    if (!ctx.nyxApiKey) return NOT_CONFIGURED;
    const slug = String(args.slug ?? '').trim();
    return nyxFetch(ctx, {
      method: 'GET',
      path: slug ? `/api/lifecycles/${encodeURIComponent(slug)}` : '/api/lifecycles',
    });
  },
};

export const nyxGetTimelineTool: Tool = {
  name: 'nyx_get_timeline',
  description:
    'Get the activity timeline for a Nyx document. Returns { documentId, events: [] } as JSON.',
  parameters: {
    type: 'object',
    properties: {
      id: { type: 'string', description: 'Document id (required).' },
    },
    required: ['id'],
  },
  needsApproval: false,
  summarize: (args) => String(args.id ?? ''),
  async run(args, ctx) {
    if (!ctx.nyxApiKey) return NOT_CONFIGURED;
    const id = String(args.id ?? '').trim();
    if (!id) return 'Error: id must not be empty.';
    return nyxFetch(ctx, {
      method: 'GET',
      path: `/api/documents/${encodeURIComponent(id)}/timeline`,
    });
  },
};

/**
 * Best-effort fetch of a document's current `content` for the update diff.
 * Returns the content string, or `null` if Nyx isn't configured/reachable or
 * the response can't be parsed — callers fall back to an all-added preview.
 */
async function fetchDocContent(ctx: ToolContext, id: string): Promise<string | null> {
  if (!ctx.nyxApiKey || !id) return null;
  const raw = await nyxFetch(ctx, {
    method: 'GET',
    path: `/api/documents/${encodeURIComponent(id)}`,
  });
  if (raw.startsWith('Error:') || raw === NOT_CONFIGURED) return null;
  try {
    const doc = JSON.parse(raw) as { content?: unknown };
    return typeof doc.content === 'string' ? doc.content : '';
  } catch {
    return null;
  }
}

// --- Body builders (shared by preview + run so the two never drift) -----------

function teamIdSummary(args: Record<string, unknown>): string {
  const arg = args.teamId;
  return arg !== undefined && arg !== null && String(arg).trim() ? String(arg).trim() : '(NYX_TEAM_ID)';
}

interface CreateDocBody {
  title: string;
  teamId: string;
  content?: string;
  path?: string;
  stage?: string;
  templateId?: string;
}

function createDocBody(args: Record<string, unknown>, ctx: ToolContext): CreateDocBody {
  const body: CreateDocBody = {
    title: String(args.title ?? '').trim(),
    teamId: teamId(args, ctx) ?? '',
  };
  if (args.content !== undefined) body.content = String(args.content);
  if (args.path !== undefined) body.path = String(args.path);
  if (args.stage !== undefined) body.stage = String(args.stage);
  if (args.templateId !== undefined) body.templateId = String(args.templateId);
  return body;
}

function updateDocBody(args: Record<string, unknown>): Record<string, string> {
  const body: Record<string, string> = {};
  for (const key of ['title', 'content', 'path', 'stage'] as const) {
    if (args[key] !== undefined) body[key] = String(args[key]);
  }
  return body;
}

interface TicketBody {
  provider: string;
  title: string;
  body: string;
  repo?: { owner?: string; name?: string };
}

function ticketBody(args: Record<string, unknown>): TicketBody {
  const body: TicketBody = {
    provider: String(args.provider ?? '').trim(),
    title: String(args.title ?? '').trim(),
    body: String(args.body ?? ''),
  };
  if (args.repo && typeof args.repo === 'object') {
    const repo = args.repo as Record<string, unknown>;
    body.repo = {
      owner: repo.owner !== undefined ? String(repo.owner) : undefined,
      name: repo.name !== undefined ? String(repo.name) : undefined,
    };
  }
  return body;
}

export const nyxTools: Tool[] = [
  nyxSearchDocsTool,
  nyxReadDocTool,
  nyxPullDocTool,
  nyxListTemplatesTool,
  nyxListLifecyclesTool,
  nyxCreateDocTool,
  nyxUpdateDocTool,
  nyxDetectDriftTool,
  nyxCreateTicketTool,
  nyxGetTimelineTool,
];
