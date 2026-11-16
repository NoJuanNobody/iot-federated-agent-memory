import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

export interface Config {
  apiKey: string;
  baseURL: string;
  model: string;
  cwd: string;
  /** Optional Brave Search key enabling the web_search tool. */
  braveApiKey?: string;
  /** Nyx backend base URL for the nyx_* tools (default http://localhost:3001). */
  nyxApiUrl?: string;
  /** Nyx API key (sd_-prefixed) enabling the nyx_* tools. */
  nyxApiKey?: string;
  /** Default team id for nyx_* tools that require one. */
  nyxTeamId?: string;
  /** One-shot prompt for print mode (-p). Undefined → interactive UI. */
  print?: string;
  /** Auto-approve mutating tools in print mode (--yes). */
  autoApprove: boolean;
  /** Emit a final machine-readable stats line in print mode (--stats). */
  stats: boolean;
  /** Context budget in tokens; compaction triggers at ~70% of this. */
  contextTokens: number;
  /**
   * Resume a prior session. Empty string → resume the latest session for the
   * cwd; a session id → resume that specific one. Undefined → fresh session.
   */
  resume?: string;
  /** List sessions for the cwd and exit. */
  sessions: boolean;
}

export const DEFAULT_MODEL = 'moonshotai/kimi-k2';
/** Suggested models — any OpenRouter model slug works with /model or --model. */
export const SUGGESTED_MODELS = ['moonshotai/kimi-k2', 'deepseek/deepseek-chat', 'deepseek/deepseek-r1'];

const HELP = `dsx — a coding agent powered by OpenRouter models

Usage:
  dsx                       interactive session
  dsx -p "prompt"           one-shot print mode
  dsx -p "prompt" --yes     print mode, auto-approve bash/write/edit

Options:
  -m, --model <slug>        any OpenRouter model slug (default: ${DEFAULT_MODEL})
                            e.g. ${SUGGESTED_MODELS.join(', ')}
  -p, --print <prompt>      run a single prompt and exit
  -y, --yes                 auto-approve mutating tools (print mode)
      --resume [id]         resume the latest session for this dir, or <id>
      --sessions            list saved sessions for this dir and exit
      --stats               print mode: emit a final __DSX_STATS__ JSON line
  -h, --help                show this help

Environment:
  OPENROUTER_API_KEY        required
  OPENROUTER_BASE_URL       optional (default: https://openrouter.ai/api/v1)
  BRAVE_API_KEY             optional — enables the web_search tool
  NYX_API_URL               optional — Nyx backend URL (default http://localhost:3001)
  NYX_API_KEY               optional — enables the nyx_* tools (sd_-prefixed key)
  NYX_TEAM_ID               optional — default team id for nyx_* tools
  DSX_CONTEXT_TOKENS        context budget for auto-compaction (default 64000)

  Variables are read from the environment, ./.env, then ~/.dsx/.env —
  first definition wins.
`;

/**
 * Load .env files via Node's built-in loader. loadEnvFile never overrides
 * variables that are already set, so the precedence is:
 * real environment > project ./.env > global ~/.dsx/.env
 */
function loadEnvFiles(cwd: string): void {
  for (const file of [path.join(cwd, '.env'), path.join(os.homedir(), '.dsx', '.env')]) {
    try {
      process.loadEnvFile(file);
    } catch {
      // File doesn't exist — fine, it's optional.
    }
  }
}

/**
 * Read project memory from DSX.md files: global (~/.dsx/DSX.md) first, then
 * project (./DSX.md) last so project guidance takes precedence by position.
 * Missing files are skipped. Returns '' when none exist.
 */
export function loadProjectMemory(cwd: string): string {
  const parts: string[] = [];
  for (const file of [path.join(os.homedir(), '.dsx', 'DSX.md'), path.join(cwd, 'DSX.md')]) {
    try {
      const content = fs.readFileSync(file, 'utf8').trim();
      if (content) parts.push(content);
    } catch {
      // File doesn't exist — fine, it's optional.
    }
  }
  return parts.join('\n\n');
}

export interface PermissionRules {
  /** Rules like `bash(npm test*)` that auto-approve a matching call. */
  allow: string[];
  /** Rules that block a matching call without prompting. Deny wins over allow. */
  deny: string[];
}

interface SettingsFile {
  permissions?: { allow?: string[]; deny?: string[] };
  /** Last-used model slug, persisted globally so it survives across sessions (#33). */
  model?: string;
}

function readSettings(file: string): SettingsFile {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8')) as SettingsFile;
  } catch {
    return {};
  }
}

/**
 * Load permission rules from ~/.dsx/settings.json (global) and
 * ./.dsx/settings.json (project). Lists combine, project last.
 */
export function loadPermissions(cwd: string): PermissionRules {
  const global = readSettings(path.join(os.homedir(), '.dsx', 'settings.json'));
  const project = readSettings(path.join(cwd, '.dsx', 'settings.json'));
  return {
    allow: [...(global.permissions?.allow ?? []), ...(project.permissions?.allow ?? [])],
    deny: [...(global.permissions?.deny ?? []), ...(project.permissions?.deny ?? [])],
  };
}

const RULE_RE = /^([a-zA-Z_][\w-]*)\((.*)\)$/s;

/** Convert a rule glob (`*`, `?`) into an anchored RegExp. */
function globToRegExp(pattern: string): RegExp {
  let out = '';
  for (const ch of pattern) {
    if (ch === '*') out += '.*';
    else if (ch === '?') out += '.';
    else out += ch.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }
  return new RegExp(`^${out}$`, 's');
}

function ruleMatches(rule: string, tool: string, summary: string): boolean {
  const m = RULE_RE.exec(rule.trim());
  return m !== null && m[1] === tool && globToRegExp(m[2]).test(summary);
}

/** Resolve a tool call against the rules: deny wins, then allow, else undecided. */
export function matchPermission(
  rules: PermissionRules,
  tool: string,
  summary: string,
): 'allow' | 'deny' | null {
  if (rules.deny.some((r) => ruleMatches(r, tool, summary))) return 'deny';
  if (rules.allow.some((r) => ruleMatches(r, tool, summary))) return 'allow';
  return null;
}

/** Append an allow rule to the project's ./.dsx/settings.json (idempotent). */
export function addAllowRule(cwd: string, rule: string): void {
  const dir = path.join(cwd, '.dsx');
  const file = path.join(dir, 'settings.json');
  const settings = readSettings(file);
  const permissions = settings.permissions ?? {};
  const allow = permissions.allow ?? [];
  if (!allow.includes(rule)) allow.push(rule);
  settings.permissions = { ...permissions, allow };
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(file, `${JSON.stringify(settings, null, 2)}\n`, 'utf8');
}

/**
 * Persist the last-used model slug to the GLOBAL ~/.dsx/settings.json, reusing
 * the read/merge/write pattern of addAllowRule. Degrades gracefully if ~/.dsx
 * is unwritable — persistence is best-effort and must never crash the app (#33).
 */
export function saveModel(model: string): void {
  try {
    const dir = path.join(os.homedir(), '.dsx');
    const file = path.join(dir, 'settings.json');
    const settings = readSettings(file);
    settings.model = model;
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(file, `${JSON.stringify(settings, null, 2)}\n`, 'utf8');
  } catch {
    // ~/.dsx unwritable — skip persistence rather than crash.
  }
}

/** Read the persisted model slug from the global ~/.dsx/settings.json, if any (#33). */
export function loadSavedModel(): string | undefined {
  return readSettings(path.join(os.homedir(), '.dsx', 'settings.json')).model;
}

/**
 * Named model profiles (#31): a map from a profile name (e.g. "spec-writer",
 * "cheap-default") to an OpenRouter model slug. Used by /model <profile> and the
 * TaskRouter so a stable name can stand in for whichever slug is preferred.
 */
export type ModelProfiles = Record<string, string>;

/**
 * Routing settings (#31): budget guardrails, free-tier fallback, and the
 * reasoning model used to auto-route known heavy tasks. All fields are optional
 * and degrade gracefully when absent.
 */
export interface RoutingSettings {
  /** Max USD spend per session; a soft cap used for status-line warnings. */
  maxCostPerSession?: number;
  /**
   * Warn before switching to a model whose prompt price exceeds this USD per
   * 1K tokens (the issue's ">$0.01/1K token" guardrail). Default 0.01.
   */
  expensiveThresholdPer1k: number;
  /** Downgrade to `freeModel` once remaining credits fall below this USD value. */
  lowCreditsThreshold?: number;
  /** Free model slug to fall back to when credits are low. */
  freeModel?: string;
  /** Reasoning model slug heavy tasks (e.g. nyx_detect_drift) auto-route to. */
  reasoningModel?: string;
  /** Tool names treated as "heavy" and auto-routed to `reasoningModel`. */
  heavyTools: string[];
}

export const DEFAULT_ROUTING: RoutingSettings = {
  expensiveThresholdPer1k: 0.01,
  heavyTools: ['nyx_detect_drift'],
};

/**
 * Shape of ~/.dsx/models.json. The `profiles` object maps profile names to
 * model slugs; `routing` holds budget/fallback/auto-route settings (#31).
 * Example:
 *   {
 *     "profiles": {
 *       "cheap-default": "deepseek/deepseek-chat",
 *       "spec-writer":   "anthropic/claude-opus-4",
 *       "coder":         "moonshotai/kimi-k2"
 *     },
 *     "routing": {
 *       "maxCostPerSession": 1.00,
 *       "expensiveThresholdPer1k": 0.01,
 *       "lowCreditsThreshold": 0.50,
 *       "freeModel": "deepseek/deepseek-chat:free",
 *       "reasoningModel": "deepseek/deepseek-r1",
 *       "heavyTools": ["nyx_detect_drift"]
 *     }
 *   }
 */
interface ModelsFile {
  profiles?: Record<string, unknown>;
  routing?: Partial<RoutingSettings>;
}

/**
 * Load routing settings from ~/.dsx/models.json, merged over DEFAULT_ROUTING.
 * Degrades gracefully: a missing or malformed file yields the defaults (#31).
 */
export function loadRoutingSettings(): RoutingSettings {
  const file = path.join(os.homedir(), '.dsx', 'models.json');
  let parsed: ModelsFile;
  try {
    parsed = JSON.parse(fs.readFileSync(file, 'utf8')) as ModelsFile;
  } catch {
    return { ...DEFAULT_ROUTING };
  }
  const r = parsed.routing ?? {};
  return {
    maxCostPerSession:
      typeof r.maxCostPerSession === 'number' ? r.maxCostPerSession : undefined,
    expensiveThresholdPer1k:
      typeof r.expensiveThresholdPer1k === 'number'
        ? r.expensiveThresholdPer1k
        : DEFAULT_ROUTING.expensiveThresholdPer1k,
    lowCreditsThreshold:
      typeof r.lowCreditsThreshold === 'number' ? r.lowCreditsThreshold : undefined,
    freeModel: typeof r.freeModel === 'string' && r.freeModel.trim() ? r.freeModel.trim() : undefined,
    reasoningModel:
      typeof r.reasoningModel === 'string' && r.reasoningModel.trim()
        ? r.reasoningModel.trim()
        : undefined,
    heavyTools: Array.isArray(r.heavyTools)
      ? r.heavyTools.filter((t): t is string => typeof t === 'string')
      : [...DEFAULT_ROUTING.heavyTools],
  };
}

/**
 * A single quality rating for one turn, persisted to ~/.dsx/feedback.json so it
 * can inform future model selection (#31). Minimal by design: the model used,
 * a 1–5 score, an optional note, and a timestamp.
 */
export interface TurnRating {
  model: string;
  rating: number;
  note?: string;
  at: string;
}

/**
 * Append a turn rating to ~/.dsx/feedback.json (read/merge/write, like
 * saveModel). Best-effort: never throws if ~/.dsx is unwritable (#31).
 */
export function saveRating(entry: TurnRating): void {
  try {
    const dir = path.join(os.homedir(), '.dsx');
    const file = path.join(dir, 'feedback.json');
    let list: TurnRating[];
    try {
      const parsed = JSON.parse(fs.readFileSync(file, 'utf8')) as { ratings?: TurnRating[] };
      list = Array.isArray(parsed.ratings) ? parsed.ratings : [];
    } catch {
      list = [];
    }
    list.push(entry);
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(file, `${JSON.stringify({ ratings: list }, null, 2)}\n`, 'utf8');
  } catch {
    // ~/.dsx unwritable — skip persistence rather than crash.
  }
}

/**
 * Load named model profiles from ~/.dsx/models.json. Degrades gracefully: a
 * missing or malformed file yields {}. Only string-valued entries are kept, so
 * a partially-broken file still contributes its valid profiles (#31).
 */
export function loadModelProfiles(): ModelProfiles {
  const file = path.join(os.homedir(), '.dsx', 'models.json');
  let parsed: ModelsFile;
  try {
    parsed = JSON.parse(fs.readFileSync(file, 'utf8')) as ModelsFile;
  } catch {
    // File doesn't exist or isn't valid JSON — profiles are optional.
    return {};
  }
  const out: ModelProfiles = {};
  for (const [name, slug] of Object.entries(parsed.profiles ?? {})) {
    if (typeof slug === 'string' && slug.trim()) out[name] = slug.trim();
  }
  return out;
}

export function loadConfig(argv: string[]): Config {
  loadEnvFiles(process.cwd());

  const config: Config = {
    apiKey: process.env.OPENROUTER_API_KEY ?? '',
    baseURL: process.env.OPENROUTER_BASE_URL ?? 'https://openrouter.ai/api/v1',
    braveApiKey: process.env.BRAVE_API_KEY || undefined,
    nyxApiUrl: process.env.NYX_API_URL ?? 'http://localhost:3001',
    nyxApiKey: process.env.NYX_API_KEY || undefined,
    nyxTeamId: process.env.NYX_TEAM_ID || undefined,
    model: loadSavedModel() ?? DEFAULT_MODEL,
    cwd: process.cwd(),
    autoApprove: false,
    stats: false,
    contextTokens: Number(process.env.DSX_CONTEXT_TOKENS) || 64_000,
    sessions: false,
  };

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    switch (arg) {
      case '-h':
      case '--help':
        process.stdout.write(HELP);
        process.exit(0);
        break;
      case '-m':
      case '--model': {
        // An explicit -m/--model overrides any persisted model AND is itself
        // persisted, so the next session defaults to it (#33).
        const next = argv[++i];
        if (next !== undefined) {
          config.model = next;
          saveModel(next);
        }
        break;
      }
      case '-p':
      case '--print':
        config.print = argv[++i] ?? '';
        break;
      case '-y':
      case '--yes':
        config.autoApprove = true;
        break;
      case '--resume': {
        // Optional id: consume the next token only if it isn't another flag.
        const next = argv[i + 1];
        config.resume = next !== undefined && !next.startsWith('-') ? argv[++i] : '';
        break;
      }
      case '--sessions':
        config.sessions = true;
        break;
      case '--stats':
        config.stats = true;
        break;
      default:
        // Bare positional prompt behaves like -p.
        if (!arg.startsWith('-') && config.print === undefined) {
          config.print = arg;
        }
    }
  }

  return config;
}
