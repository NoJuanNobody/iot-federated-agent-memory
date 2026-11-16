/**
 * OpenRouter's model catalog. The `/models` endpoint needs no API key, so the
 * picker can populate itself from the live list and fall back to SUGGESTED_MODELS
 * only when the fetch fails.
 */
export interface ModelInfo {
  id: string;
  name: string;
  /** Max context window in tokens, when reported. */
  contextLength?: number;
  /** USD per prompt token (OpenRouter reports a per-token price). */
  promptPrice?: number;
  /** USD per completion token. */
  completionPrice?: number;
}

interface RawModel {
  id?: string;
  name?: string;
  context_length?: number | string;
  pricing?: { prompt?: number | string; completion?: number | string };
}

function num(value: unknown): number | undefined {
  if (value === undefined || value === null || value === '') return undefined;
  const n = Number(value);
  return Number.isFinite(n) ? n : undefined;
}

/** Fetch and normalize the OpenRouter model catalog from `${baseURL}/models`. */
export async function fetchModels(baseURL: string): Promise<ModelInfo[]> {
  const url = `${baseURL.replace(/\/$/, '')}/models`;
  const res = await fetch(url, {
    headers: { 'HTTP-Referer': 'https://github.com/NoJuanNobody/dsx', 'X-Title': 'dsx' },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const json = (await res.json()) as { data?: RawModel[] };
  const data = Array.isArray(json.data) ? json.data : [];
  return data
    .map((m): ModelInfo => ({
      id: String(m.id ?? ''),
      name: String(m.name ?? m.id ?? ''),
      contextLength: num(m.context_length),
      promptPrice: num(m.pricing?.prompt),
      completionPrice: num(m.pricing?.completion),
    }))
    .filter((m) => m.id !== '')
    .sort((a, b) => a.id.localeCompare(b.id));
}

/** "128k ctx" / "" when unknown. */
export function formatContext(m: ModelInfo): string {
  if (!m.contextLength) return '';
  const k = m.contextLength >= 1000 ? `${Math.round(m.contextLength / 1000)}k` : `${m.contextLength}`;
  return `${k} ctx`;
}

/** "$0.50/$1.50 per 1M" (prompt/completion), or "" when no pricing reported. */
export function formatPrice(m: ModelInfo): string {
  if (m.promptPrice === undefined && m.completionPrice === undefined) return '';
  const perM = (p?: number) => (p === undefined ? '?' : `$${(p * 1_000_000).toFixed(2)}`);
  return `${perM(m.promptPrice)}/${perM(m.completionPrice)} per 1M`;
}

/** Substring match against id and human name. */
export function filterModels(models: ModelInfo[], query: string): ModelInfo[] {
  const q = query.trim().toLowerCase();
  if (!q) return models;
  return models.filter((m) => m.id.toLowerCase().includes(q) || m.name.toLowerCase().includes(q));
}
