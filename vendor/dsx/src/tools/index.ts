import type { Skill } from '../skills.js';
import { bashTool } from './bash.js';
import { fetchUrlTool } from './fetch.js';
import { readFileTool, writeFileTool, editFileTool, multiEditTool, listFilesTool, listDirectoryTool } from './files.js';
import { grepTool } from './grep.js';
import { renameSymbolTool } from './refactor.js';
import { webSearchTool } from './search.js';
import { generateImageTool } from './image.js';
import { nyxTools } from './nyx.js';
import { makeUseSkillTool } from './skill.js';

export interface ToolContext {
  cwd: string;
  skills: Skill[];
  /** Brave Search key for web_search; undefined → tool reports "not configured". */
  braveApiKey?: string;
  /** OpenRouter API key for generate_image; undefined → tool reports "not configured". */
  openRouterApiKey?: string;
  /** OpenRouter base URL for generate_image (default https://openrouter.ai/api/v1). */
  openRouterBaseURL?: string;
  /** Nyx backend base URL for nyx_* tools (default http://localhost:3001). */
  nyxApiUrl?: string;
  /** Nyx API key (sd_-prefixed); undefined → nyx_* tools report "not configured". */
  nyxApiKey?: string;
  /** Default team id for nyx_* tools that require one. */
  nyxTeamId?: string;
  /** Aborts when the user interrupts; long-running tools should honor it. */
  signal?: AbortSignal;
  /**
   * The active parent IO's approval callback, injected by the Agent at
   * tool-execution time. Lets a tool (e.g. the write-capable `delegate`
   * subagent) route its child's mutations back to the SAME user approval
   * prompt the parent uses, instead of auto-approving or denying.
   */
  requestApproval?: (req: {
    tool: string;
    summary: string;
    preview?: string;
  }) => Promise<'yes' | 'no' | 'always' | 'persist'>;
}

export interface Tool {
  name: string;
  description: string;
  /** JSON Schema for the function-calling API. */
  parameters: Record<string, unknown>;
  /** Mutating tools require user approval; read-only tools run freely. */
  needsApproval: boolean;
  /** Short human-readable description of a specific call, for the UI. */
  summarize(args: Record<string, unknown>): string;
  /**
   * Optional rich preview shown at approval time: a diff with `+`/`-` lines, or
   * a structured doc preview (see `src/ui/docPreview.ts`). May be async so a
   * preview can fetch state it needs to render a real diff (e.g. the current
   * Nyx document content for `nyx_update_doc`).
   */
  preview?(args: Record<string, unknown>, ctx: ToolContext): string | Promise<string>;
  run(args: Record<string, unknown>, ctx: ToolContext): Promise<string>;
}

export function buildTools(skills: Skill[]): Tool[] {
  return [
    bashTool,
    readFileTool,
    writeFileTool,
    editFileTool,
    multiEditTool,
    listFilesTool,
    listDirectoryTool,
    grepTool,
    renameSymbolTool,
    webSearchTool,
    fetchUrlTool,
    generateImageTool,
    ...nyxTools,
    makeUseSkillTool(skills),
  ];
}

/** Shape the registry into the OpenAI/DeepSeek function-calling format. */
export function toolSchemas(tools: Tool[]) {
  return tools.map((t) => ({
    type: 'function' as const,
    function: {
      name: t.name,
      description: t.description,
      parameters: t.parameters,
    },
  }));
}

export function truncate(text: string, maxChars = 8000): string {
  if (text.length <= maxChars) return text;
  return `${text.slice(0, maxChars)}\n... [truncated ${text.length - maxChars} chars]`;
}
