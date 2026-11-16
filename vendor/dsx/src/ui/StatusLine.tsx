import React from 'react';
import os from 'node:os';
import { Box, Text } from 'ink';
import { theme } from './theme.js';

interface Props {
  model: string;
  cwd: string;
  /** Compact credits string (e.g. "$6.36 left"), or null while unknown/unavailable. */
  credits: string | null;
  usedTokens: number;
  budgetTokens: number;
  /** Git branch, or undefined when not in a repo. */
  branch?: string;
  /** Estimated cost of the last turn (e.g. "$0.0123"), or null when unknown (#31). */
  lastTurnCost?: string | null;
  /** Cumulative estimated session cost in USD, or null when unknown (#31). */
  sessionCost?: number | null;
  /** Max USD per session; when sessionCost exceeds it, the cost segment warns (#31). */
  maxCostPerSession?: number;
}

function abbreviateHome(p: string): string {
  const home = os.homedir();
  return p === home || p.startsWith(`${home}/`) ? `~${p.slice(home.length)}` : p;
}

function fmtK(n: number): string {
  return n >= 1000 ? `${Math.round(n / 1000)}k` : `${n}`;
}

/**
 * Persistent bottom status line: model · folder · credits · context · branch.
 * Segments that aren't available (credits not yet loaded, not a git repo) are
 * dropped rather than shown blank.
 */
export function StatusLine({
  model,
  cwd,
  credits,
  usedTokens,
  budgetTokens,
  branch,
  lastTurnCost,
  sessionCost,
  maxCostPerSession,
}: Props) {
  // Budget guardrail: the session cost segment turns red once it crosses the
  // configured per-session cap, so an overrun is visible at a glance (#31).
  const overBudget =
    maxCostPerSession !== undefined && sessionCost !== null && sessionCost !== undefined && sessionCost > maxCostPerSession;
  const costSegment =
    lastTurnCost != null
      ? `${lastTurnCost}/turn${maxCostPerSession !== undefined && sessionCost != null ? ` ($${sessionCost.toFixed(2)}/$${maxCostPerSession.toFixed(2)})` : ''}`
      : null;

  // The model name carries a faint violet tint so the brand accent is present
  // even in the persistent status line; the remaining segments stay dim so the
  // line reads as ambient metadata, not chrome that competes with content.
  const rest = [
    abbreviateHome(cwd),
    credits,
    `${fmtK(usedTokens)}/${fmtK(budgetTokens)} ctx`,
    branch ? `⎇ ${branch}` : null,
  ].filter(Boolean);

  return (
    <Box marginTop={1}>
      <Text color={theme.accentBright}>{model}</Text>
      <Text dimColor>{` · ${rest.join(' · ')}`}</Text>
      {costSegment && (
        <Text color={overBudget ? 'red' : undefined} dimColor={!overBudget}>
          {` · ${costSegment}`}
        </Text>
      )}
    </Box>
  );
}
