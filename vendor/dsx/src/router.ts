/**
 * Multi-model routing core (#31).
 *
 * A small, dependency-free router that picks an OpenRouter model slug for a
 * given task type, optionally constrained by a budget tier. This is the
 * foundational piece: it has no opinions about cost tracking, quality feedback,
 * or auto-routing of specific tools — those are deferred follow-ups.
 */

import type { ModelProfiles } from './config.js';
import { DEFAULT_MODEL } from './config.js';

/**
 * Coarse task categories the router knows how to route. `default` is the
 * catch-all used when a caller has no more specific category.
 */
export type TaskType = 'default' | 'spec' | 'code' | 'cheap';

/**
 * Budget tier hint. `low` prefers cheaper profiles, `high` allows premium
 * ones. `any` (the default) imposes no constraint.
 */
export type Budget = 'any' | 'low' | 'high';

export interface RouteRequest {
  /** What kind of work is this? Defaults to `default`. */
  task?: TaskType;
  /** Budget constraint hint. Defaults to `any`. */
  budget?: Budget;
}

/**
 * Maps a task type to the profile name the router prefers for it. Resolution
 * falls back to the `default` profile, then to the configured fallback slug.
 */
const TASK_PROFILE: Record<TaskType, string> = {
  default: 'default',
  spec: 'spec-writer',
  code: 'coder',
  cheap: 'cheap-default',
};

/**
 * Selects a model slug given a task type and optional budget. Pure and
 * synchronous: it reads only the profiles passed in plus a fallback slug.
 */
export class TaskRouter {
  private readonly profiles: ModelProfiles;
  private readonly fallback: string;

  /**
   * @param profiles Named profiles (name → slug), e.g. from ~/.dsx/models.json.
   * @param fallback Slug to use when no profile matches (default: DEFAULT_MODEL).
   */
  constructor(profiles: ModelProfiles = {}, fallback: string = DEFAULT_MODEL) {
    this.profiles = profiles;
    this.fallback = fallback;
  }

  /** Resolve a profile name to its slug, if defined. */
  resolveProfile(name: string): string | undefined {
    return this.profiles[name];
  }

  /**
   * Pick a model slug for the request. Order of preference:
   *   1. A `low` budget prefers the `cheap-default` profile when present.
   *   2. The profile mapped to the task type.
   *   3. The `default` profile.
   *   4. The fallback slug.
   */
  route(req: RouteRequest = {}): string {
    const task = req.task ?? 'default';
    const budget = req.budget ?? 'any';

    if (budget === 'low') {
      const cheap = this.profiles[TASK_PROFILE.cheap];
      if (cheap) return cheap;
    }

    return (
      this.profiles[TASK_PROFILE[task]] ??
      this.profiles[TASK_PROFILE.default] ??
      this.fallback
    );
  }
}
