import fs from 'node:fs';
import path from 'node:path';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
import type { Transport } from '@modelcontextprotocol/sdk/shared/transport.js';
import type { Tool } from './tools/index.js';
import { truncate } from './tools/index.js';

/** A single MCP server entry in `.dsx/mcp.json`. */
export interface McpServerConfig {
  /** stdio transport: executable to launch. */
  command?: string;
  args?: string[];
  env?: Record<string, string>;
  /** HTTP transport: streamable-HTTP endpoint URL. */
  url?: string;
  /** HTTP transport: custom headers sent with every request. */
  headers?: Record<string, string>;
}

interface McpConfig {
  mcpServers?: Record<string, McpServerConfig>;
}

export interface McpConnectResult {
  tools: Tool[];
  warnings: string[];
  close: () => Promise<void>;
}

/** Absolute path to the project's MCP config file. */
function mcpConfigPath(cwd: string): string {
  return path.join(cwd, '.dsx', 'mcp.json');
}

/** Read and parse `<cwd>/.dsx/mcp.json`, returning {} if absent or malformed. */
function readMcpConfig(cwd: string): McpConfig {
  const file = mcpConfigPath(cwd);
  if (!fs.existsSync(file)) return {};
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8')) as McpConfig;
  } catch {
    return {};
  }
}

/** Return the configured MCP servers (name → config) from `<cwd>/.dsx/mcp.json`. */
export function listMcpServers(cwd: string): Record<string, McpServerConfig> {
  return readMcpConfig(cwd).mcpServers ?? {};
}

/**
 * Add an MCP server to `<cwd>/.dsx/mcp.json`, creating `.dsx/` if needed and
 * preserving existing servers. Mirrors the read/merge/write pattern of
 * `addAllowRule`. Validates: non-empty name, at least one of command/url, and
 * no duplicate name. Throws an Error (with a user-facing message) on failure.
 *
 * Note: servers connect once at startup, so a newly added server only takes
 * effect after restarting dsx (hot-reconnect is out of scope, #53).
 */
export function addMcpServer(cwd: string, name: string, config: McpServerConfig): void {
  const trimmed = name.trim();
  if (!trimmed) throw new Error('Server name is required.');
  if (!config.command && !config.url) {
    throw new Error('A server needs a "command" (stdio) or a "url" (http).');
  }
  const cfg = readMcpConfig(cwd);
  const servers = cfg.mcpServers ?? {};
  if (servers[trimmed]) throw new Error(`A server named "${trimmed}" already exists.`);
  servers[trimmed] = config;
  cfg.mcpServers = servers;
  const dir = path.join(cwd, '.dsx');
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(mcpConfigPath(cwd), `${JSON.stringify(cfg, null, 2)}\n`, 'utf8');
}

/**
 * Remove a named MCP server from `<cwd>/.dsx/mcp.json`, preserving the rest.
 * Throws if the server doesn't exist.
 */
export function removeMcpServer(cwd: string, name: string): void {
  const cfg = readMcpConfig(cwd);
  const servers = cfg.mcpServers ?? {};
  if (!servers[name]) throw new Error(`No server named "${name}".`);
  delete servers[name];
  cfg.mcpServers = servers;
  const dir = path.join(cwd, '.dsx');
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(mcpConfigPath(cwd), `${JSON.stringify(cfg, null, 2)}\n`, 'utf8');
}

/** Monotonic counter so multiple images from one result get distinct filenames. */
let imageCounter = 0;

/** Map a content part's mimeType to a file extension. */
function extFromMime(mimeType: string | undefined): string {
  switch ((mimeType ?? '').toLowerCase()) {
    case 'image/png':
      return 'png';
    case 'image/jpeg':
    case 'image/jpg':
      return 'jpg';
    case 'image/gif':
      return 'gif';
    case 'image/webp':
      return 'webp';
    case 'image/svg+xml':
      return 'svg';
    default:
      return 'bin';
  }
}

/**
 * Flatten an MCP tool result's content parts into a single string.
 *
 * Text parts are concatenated as-is. Image parts (base64 `data` + `mimeType`)
 * are written to disk under `<cwd>/.dsx/screenshots/` and the saved path is
 * included in the returned text, so image-returning tools (e.g. Playwright
 * screenshots) are usable by the model instead of being silently dropped.
 */
function extractContent(result: unknown, cwd: string): string {
  const content = (result as { content?: unknown })?.content;
  if (!Array.isArray(content)) return '';
  const parts: string[] = [];
  for (const item of content) {
    if (!item || typeof item !== 'object') continue;
    const type = (item as { type?: string }).type;
    if (type === 'text') {
      parts.push(String((item as { text?: unknown }).text ?? ''));
    } else if (type === 'image') {
      const data = (item as { data?: unknown }).data;
      if (typeof data !== 'string' || data.length === 0) continue;
      const mimeType = (item as { mimeType?: unknown }).mimeType;
      const ext = extFromMime(typeof mimeType === 'string' ? mimeType : undefined);
      const dir = path.join(cwd, '.dsx', 'screenshots');
      try {
        fs.mkdirSync(dir, { recursive: true });
        const file = path.join(dir, `image-${Date.now()}-${imageCounter++}.${ext}`);
        fs.writeFileSync(file, Buffer.from(data, 'base64'));
        parts.push(`[image saved to ${file}]`);
      } catch (err) {
        parts.push(`[image could not be saved: ${(err as Error).message}]`);
      }
    }
  }
  return parts.join('\n');
}

/**
 * Connect to every MCP server declared in `<cwd>/.dsx/mcp.json` and adapt their
 * tools into dsx `Tool`s. A server that fails to start becomes a warning string
 * rather than throwing, so one bad server never takes down the agent.
 */
export async function connectMcpServers(cwd: string): Promise<McpConnectResult> {
  const tools: Tool[] = [];
  const warnings: string[] = [];
  const clients: Client[] = [];

  const close = async (): Promise<void> => {
    await Promise.all(clients.map((c) => c.close().catch(() => {})));
  };

  const configPath = path.join(cwd, '.dsx', 'mcp.json');
  if (!fs.existsSync(configPath)) return { tools, warnings, close };

  let config: McpConfig;
  try {
    config = JSON.parse(fs.readFileSync(configPath, 'utf8')) as McpConfig;
  } catch (err) {
    warnings.push(`MCP: failed to parse ${configPath}: ${(err as Error).message}`);
    return { tools, warnings, close };
  }

  const servers = config.mcpServers ?? {};
  for (const [name, server] of Object.entries(servers)) {
    try {
      let transport: Transport;
      if (server.url) {
        const opts: ConstructorParameters<typeof StreamableHTTPClientTransport>[1] = {};
        if (server.headers && Object.keys(server.headers).length > 0) {
          opts.requestInit = { headers: server.headers };
        }
        transport = new StreamableHTTPClientTransport(new URL(server.url), opts);
      } else if (server.command) {
        transport = new StdioClientTransport({
          command: server.command,
          args: server.args ?? [],
          env: { ...process.env as Record<string, string>, ...(server.env ?? {}) },
          // MCP stdio servers (e.g. `mcp-remote`) are chatty on stderr. The SDK
          // defaults to 'inherit', which dumps that noise into our TUI. Drop it
          // by default; set DSX_MCP_DEBUG=1 to surface it when troubleshooting.
          stderr: process.env.DSX_MCP_DEBUG ? 'inherit' : 'ignore',
        });
      } else {
        warnings.push(`MCP server "${name}" has neither "command" nor "url"; skipping.`);
        continue;
      }

      const client = new Client({ name: 'dsx', version: '0.1.0' });
      await client.connect(transport);
      clients.push(client);

      const { tools: mcpTools } = await client.listTools();
      for (const mcpTool of mcpTools) {
        const toolName = `mcp__${name}__${mcpTool.name}`;
        tools.push({
          name: toolName,
          description: mcpTool.description ?? `MCP tool ${mcpTool.name} from ${name}`,
          parameters: (mcpTool.inputSchema as Record<string, unknown>) ?? {
            type: 'object',
            properties: {},
          },
          needsApproval: true,
          summarize(args: Record<string, unknown>): string {
            return truncate(JSON.stringify(args ?? {}), 200);
          },
          async run(args: Record<string, unknown>): Promise<string> {
            const result = await client.callTool({ name: mcpTool.name, arguments: args });
            if ((result as { isError?: boolean }).isError) {
              return truncate(`MCP tool ${toolName} returned an error:\n${extractContent(result, cwd)}`);
            }
            return truncate(extractContent(result, cwd));
          },
        });
      }
    } catch (err) {
      warnings.push(`MCP server "${name}" failed to start: ${(err as Error).message}`);
    }
  }

  return { tools, warnings, close };
}
