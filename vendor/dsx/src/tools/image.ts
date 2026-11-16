import fs from 'node:fs';
import path from 'node:path';
import type { Tool } from './index.js';

const IMAGE_TIMEOUT_MS = 120_000;
const DEFAULT_MODEL = 'google/gemini-2.5-flash-image';
const DEFAULT_OUTPUT = 'generated-image.png';

/**
 * OpenRouter slugs that actually support image OUTPUT via the chat-completions
 * `modalities` field. Models outside this set (or invented ones like
 * `black-forest-labs/flux-schnell`, which OpenRouter doesn't host) return an
 * HTTP 400 "not a valid model ID". Kept here so we can reject a bad `model`
 * arg with a helpful message instead of a raw 400.
 */
const KNOWN_IMAGE_MODELS = [
  'google/gemini-2.5-flash-image',
  'google/gemini-3-pro-image-preview',
  'google/gemini-3.1-flash-image-preview',
  'openai/gpt-5-image',
  'openai/gpt-5-image-mini',
  'openai/gpt-5.4-image-2',
];

/** OpenRouter chat-completions message shape with optional generated images. */
interface ImageChoice {
  message?: {
    content?: string;
    images?: Array<{ image_url?: { url?: string } }>;
  };
}

/** Map a data: URL or http(s) URL to raw bytes. */
async function urlToBuffer(url: string, signal?: AbortSignal): Promise<Buffer> {
  if (url.startsWith('data:')) {
    const comma = url.indexOf(',');
    if (comma === -1) throw new Error('malformed data URL');
    const meta = url.slice(5, comma);
    const payload = url.slice(comma + 1);
    if (meta.includes('base64')) return Buffer.from(payload, 'base64');
    return Buffer.from(decodeURIComponent(payload), 'utf8');
  }
  const response = await fetch(url, {
    signal: signal ?? AbortSignal.timeout(IMAGE_TIMEOUT_MS),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status} fetching image URL`);
  return Buffer.from(await response.arrayBuffer());
}

export const generateImageTool: Tool = {
  name: 'generate_image',
  description:
    'Generate an image from a text prompt (logos, favicons, hero images, placeholders) ' +
    'using an OpenRouter image model, and save it into the project. Returns the saved path. ' +
    'Supports an output path plus width/height/format hints.',
  parameters: {
    type: 'object',
    properties: {
      prompt: { type: 'string', description: 'Description of the image to generate.' },
      output: {
        type: 'string',
        description: `Output file path relative to cwd (default ${DEFAULT_OUTPUT}).`,
      },
      width: { type: 'number', description: 'Desired width in pixels (hint to the model).' },
      height: { type: 'number', description: 'Desired height in pixels (hint to the model).' },
      format: {
        type: 'string',
        description: 'Desired format hint, e.g. png or svg (where the model supports it).',
      },
      model: {
        type: 'string',
        description:
          'OPTIONAL. Leave unset unless the user names a specific model — the ' +
          `default (${DEFAULT_MODEL}) works for most cases. Do NOT invent a slug. ` +
          `Only these OpenRouter image-output models are valid: ${KNOWN_IMAGE_MODELS.join(', ')}.`,
      },
    },
    required: ['prompt'],
  },
  // Makes an outward network call to OpenRouter AND writes a file — gate it.
  needsApproval: true,
  summarize: (args) => String(args.prompt ?? ''),
  async run(args, ctx) {
    if (!ctx.openRouterApiKey) {
      return (
        'Image generation is not configured. Set OPENROUTER_API_KEY in the environment, ' +
        './.env, or ~/.dsx/.env, then restart dsx.'
      );
    }

    const prompt = String(args.prompt ?? '').trim();
    if (!prompt) return 'Error: prompt must not be empty.';

    const model = String(args.model || DEFAULT_MODEL);
    // Reject an unknown slug up front with guidance, rather than letting it
    // become a cryptic HTTP 400 "not a valid model ID" from OpenRouter.
    if (!KNOWN_IMAGE_MODELS.includes(model)) {
      return (
        `Error: "${model}" is not a known OpenRouter image-output model. ` +
        `Use one of: ${KNOWN_IMAGE_MODELS.join(', ')} — or omit the model arg to use the default (${DEFAULT_MODEL}).`
      );
    }
    const baseURL = (ctx.openRouterBaseURL ?? 'https://openrouter.ai/api/v1').replace(/\/$/, '');

    // Fold the dimension/format hints into the prompt — image models take these
    // as natural-language guidance rather than dedicated API fields.
    const hints: string[] = [];
    const width = Number(args.width);
    const height = Number(args.height);
    if (width > 0 && height > 0) hints.push(`Dimensions: ${width}x${height} pixels.`);
    else if (width > 0) hints.push(`Width: ${width} pixels.`);
    else if (height > 0) hints.push(`Height: ${height} pixels.`);
    const format = String(args.format || '').trim().toLowerCase();
    if (format) hints.push(`Format: ${format}.`);
    const fullPrompt = hints.length ? `${prompt}\n\n${hints.join(' ')}` : prompt;

    let response: Response;
    try {
      response = await fetch(`${baseURL}/chat/completions`, {
        method: 'POST',
        signal: ctx.signal ?? AbortSignal.timeout(IMAGE_TIMEOUT_MS),
        headers: {
          Authorization: `Bearer ${ctx.openRouterApiKey}`,
          'Content-Type': 'application/json',
          'HTTP-Referer': 'https://github.com/NoJuanNobody/dsx',
          'X-Title': 'dsx',
        },
        body: JSON.stringify({
          model,
          modalities: ['image', 'text'],
          messages: [{ role: 'user', content: fullPrompt }],
        }),
      });
    } catch (err) {
      const reason = err instanceof Error && err.name === 'TimeoutError'
        ? `timed out after ${IMAGE_TIMEOUT_MS / 1000}s`
        : err instanceof Error ? err.message : String(err);
      return `Error: image request failed — ${reason}`;
    }

    if (!response.ok) {
      let detail = '';
      try {
        detail = (await response.text()).slice(0, 500);
      } catch {
        // ignore
      }
      return `Error: OpenRouter returned HTTP ${response.status} ${response.statusText}${detail ? ` — ${detail}` : ''}`;
    }

    let data: { choices?: ImageChoice[] };
    try {
      data = (await response.json()) as { choices?: ImageChoice[] };
    } catch (err) {
      return `Error: could not parse OpenRouter response — ${err instanceof Error ? err.message : String(err)}`;
    }

    const message = data.choices?.[0]?.message;
    const imageUrl = message?.images?.[0]?.image_url?.url;
    if (!imageUrl) {
      const text = message?.content?.trim();
      return (
        `Error: model "${model}" returned no image` +
        (text ? ` — it replied: ${text.slice(0, 300)}` : '. Try an image-capable model slug.')
      );
    }

    let buffer: Buffer;
    try {
      buffer = await urlToBuffer(imageUrl, ctx.signal);
    } catch (err) {
      return `Error: failed to retrieve generated image — ${err instanceof Error ? err.message : String(err)}`;
    }

    const rel = String(args.output || DEFAULT_OUTPUT);
    const outPath = path.isAbsolute(rel) ? rel : path.join(ctx.cwd, rel);
    try {
      fs.mkdirSync(path.dirname(outPath), { recursive: true });
      fs.writeFileSync(outPath, buffer);
    } catch (err) {
      return `Error: could not write image to ${outPath} — ${err instanceof Error ? err.message : String(err)}`;
    }

    return `Saved generated image (${buffer.length} bytes) to ${outPath}`;
  },
};
