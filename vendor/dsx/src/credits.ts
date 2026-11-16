/**
 * OpenRouter account balance. The `/credits` endpoint (authenticated with the
 * API key) reports total granted credits and total usage; remaining is the
 * difference. Shared by the `/credits` command and the status line.
 */

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

export interface CreditBalance {
  total: number;
  used: number;
  remaining: number;
}

export async function fetchCredits(baseURL: string, apiKey: string): Promise<CreditBalance> {
  const url = `${baseURL.replace(/\/$/, '')}/credits`;
  const res = await fetch(url, { headers: { Authorization: `Bearer ${apiKey}` } });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const json = (await res.json()) as { data?: { total_credits?: number; total_usage?: number } };
  const total = Number(json.data?.total_credits ?? 0);
  const used = Number(json.data?.total_usage ?? 0);
  return { total, used, remaining: total - used };
}

const usd = (n: number) => `$${n.toFixed(2)}`;

/** "Credits: $6.50 remaining ($3.50 of $10.00 used)" — for the /credits command. */
export function formatCredits(c: CreditBalance): string {
  return `Credits: ${usd(c.remaining)} remaining (${usd(c.used)} of ${usd(c.total)} used)`;
}

/** "$6.50 left" — compact form for the status line. */
export function formatCreditsShort(c: CreditBalance): string {
  return `${usd(c.remaining)} left`;
}

/**
 * Estimate the USD cost of a turn from its token usage and the model's per-token
 * prices (as reported by the OpenRouter catalog). Returns undefined when no
 * pricing is known, so callers can simply omit the segment (#31).
 */
export function estimateTurnCost(
  usage: { promptTokens: number; completionTokens: number },
  prices: { promptPrice?: number; completionPrice?: number },
): number | undefined {
  if (prices.promptPrice === undefined && prices.completionPrice === undefined) return undefined;
  return usage.promptTokens * (prices.promptPrice ?? 0) + usage.completionTokens * (prices.completionPrice ?? 0);
}

/** Compact USD with up to 4 decimals for small per-turn amounts (e.g. "$0.0123"). */
export function formatCostShort(n: number): string {
  if (n === 0) return '$0';
  if (n < 0.01) return `$${n.toFixed(4)}`;
  return `$${n.toFixed(2)}`;
}

interface PersistedCredits extends CreditBalance {
  updatedAt: string;
}

const RUNTIME_DIR = path.join(os.homedir(), '.dsx');
const CREDITS_FILE = path.join(RUNTIME_DIR, 'credits.json');

/**
 * Load the last known credit balance from ~/.dsx/credits.json. Returns null
 * when the file is missing or malformed so callers can fall back to fetching.
 */
export function loadPersistedCredits(): CreditBalance | null {
  try {
    const raw = fs.readFileSync(CREDITS_FILE, 'utf8');
    const parsed = JSON.parse(raw) as PersistedCredits;
    if (
      typeof parsed.total === 'number' &&
      typeof parsed.used === 'number' &&
      typeof parsed.remaining === 'number' &&
      Number.isFinite(parsed.total) &&
      Number.isFinite(parsed.used) &&
      Number.isFinite(parsed.remaining)
    ) {
      return {
        total: parsed.total,
        used: parsed.used,
        remaining: parsed.remaining,
      };
    }
  } catch {
    // Missing or malformed file — fine, we'll fetch fresh.
  }
  return null;
}

/**
 * Persist the latest credit balance to ~/.dsx/credits.json so the status line
 * can show a cached value on the next launch while the live fetch completes.
 */
export function savePersistedCredits(balance: CreditBalance): void {
  try {
    fs.mkdirSync(RUNTIME_DIR, { recursive: true });
    fs.writeFileSync(
      CREDITS_FILE,
      `${JSON.stringify({ ...balance, updatedAt: new Date().toISOString() }, null, 2)}\n`,
      'utf8',
    );
  } catch {
    // ~/.dsx unwritable — skip persistence rather than crash.
  }
}
