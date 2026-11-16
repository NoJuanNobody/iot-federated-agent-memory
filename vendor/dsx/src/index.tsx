#!/usr/bin/env node
import React from 'react';
import { render } from 'ink';
import { Agent, type AgentEvent } from './agent.js';
import {
  loadConfig,
  loadProjectMemory,
  loadPermissions,
  addAllowRule,
  saveModel,
  loadRoutingSettings,
} from './config.js';
import { createClient } from './client.js';
import { buildSystemPrompt } from './prompt.js';
import { loadSkills } from './skills.js';
import { buildTools } from './tools/index.js';
import { createSession, appendMessage, latestSession, loadSession, listSessions } from './session.js';
import { makeAgentTool } from './tools/agent-tool.js';
import { connectMcpServers } from './mcp.js';
import { App } from './ui/App.js';

const config = loadConfig(process.argv.slice(2));

if (!config.apiKey) {
  console.error('Error: OPENROUTER_API_KEY is not set.');
  console.error('Get a key at https://openrouter.ai/keys and export OPENROUTER_API_KEY=sk-or-...');
  process.exit(1);
}

if (config.sessions) {
  // List saved sessions for this directory and exit.
  const infos = listSessions(config.cwd);
  if (infos.length === 0) {
    console.log('No saved sessions for this directory.');
  } else {
    for (const s of infos) {
      console.log(`${s.id}  ${s.mtime.toISOString()}  ${s.messageCount} message(s)`);
    }
  }
  process.exit(0);
}

// Resume an existing session (latest or by id) or start a fresh one. On resume,
// seed the agent's history so the model retains prior context.
const restored =
  config.resume !== undefined
    ? config.resume
      ? loadSession(config.cwd, config.resume)
      : latestSession(config.cwd)
    : null;
if (config.resume !== undefined && !restored) {
  console.error(
    config.resume ? `Error: no session "${config.resume}" for this directory.` : 'Error: no sessions to resume.',
  );
  process.exit(1);
}
let session = restored ? restored.session : createSession(config.cwd);

const skills = loadSkills(config.cwd);
const tools = buildTools(skills);
const client = createClient(config);
const ctx = {
  cwd: config.cwd,
  skills,
  braveApiKey: config.braveApiKey,
  openRouterApiKey: config.apiKey || undefined,
  openRouterBaseURL: config.baseURL,
  nyxApiUrl: config.nyxApiUrl,
  nyxApiKey: config.nyxApiKey,
  nyxTeamId: config.nyxTeamId,
};
// MCP: connect configured servers and register their (approval-gated) tools (#11).
const mcp = await connectMcpServers(config.cwd);
tools.push(...mcp.tools);
for (const warning of mcp.warnings) process.stderr.write(`⚠ ${warning}\n`);
// Subagent tool: delegate read-only scoped tasks to isolated child loops (#10).
// Pushed after MCP so children (read-only filter) naturally exclude MCP tools.
tools.push(...makeAgentTool({ client, model: config.model, tools, ctx }));
// Routing settings (#31): heavy-task auto-routing to a reasoning model.
const routing = loadRoutingSettings();
const agent = new Agent(
  client,
  config.model,
  buildSystemPrompt(config.cwd, skills, loadProjectMemory(config.cwd)),
  tools,
  ctx,
  config.contextTokens,
  loadPermissions(config.cwd),
  (rule) => addAllowRule(config.cwd, rule),
  (message) => appendMessage(session, message),
  new Set(routing.heavyTools),
  routing.reasoningModel ?? null,
);

if (restored) agent.restore(restored.messages);

if (config.print !== undefined) {
  // Print mode: no Ink, stream to stdout, suitable for scripting.
  const controller = new AbortController();
  process.on('SIGINT', () => controller.abort());
  const startedAt = Date.now();
  await agent.run(config.print, {
    onEvent(event: AgentEvent) {
      switch (event.type) {
        case 'text-delta':
          process.stdout.write(event.text);
          break;
        case 'text-done':
          process.stdout.write('\n');
          break;
        case 'tool-start':
          process.stderr.write(`⏺ ${event.name}(${event.summary})\n`);
          break;
        case 'tool-end':
          if (event.isError) process.stderr.write(`  ✗ ${event.result.split('\n')[0]}\n`);
          break;
        case 'info':
          process.stderr.write(`ℹ ${event.text}\n`);
          break;
        case 'error':
          process.stderr.write(`✗ ${event.message}\n`);
          process.exitCode = 1;
          break;
      }
    },
    async requestApproval({ tool, summary }) {
      if (config.autoApprove) return 'yes';
      process.stderr.write(`✗ denied ${tool}(${summary}) — pass --yes to auto-approve in print mode\n`);
      return 'no';
    },
  }, controller.signal);
  if (config.stats) {
    const stats = { promptTokens: agent.usedTokens(), ms: Date.now() - startedAt };
    process.stdout.write(`\n__DSX_STATS__ ${JSON.stringify(stats)}\n`);
  }
} else {
  if (!process.stdin.isTTY) {
    console.error('Interactive mode needs a TTY. Use -p "prompt" for non-interactive runs.');
    process.exit(1);
  }
  // /clear rolls over to a fresh session file (append target follows `session`).
  const onClear = () => {
    session = createSession(config.cwd);
  };
  // Logo + purple palette mirror the `nyx chat` CLI banner exactly.
  const purple = '\x1b[38;5;141m';
  const midPurple = '\x1b[38;5;134m';
  const deepPurple = '\x1b[38;5;99m';
  const stars = '\x1b[38;5;229m';
  const dim = '\x1b[2m';
  const reset = '\x1b[0m';

  const nyxLogo = [
    '',
    `${dim}${deepPurple}              .  ${stars}*${deepPurple}                          ${stars}.${reset}`,
    `${dim}${deepPurple}        ${stars}*${deepPurple}          ${stars}·${reset}`,
    `${purple}    ███╗   ██╗██╗   ██╗██╗  ██╗${reset}`,
    `${purple}    ████╗  ██║╚██╗ ██╔╝╚██╗██╔╝${reset}`,
    `${midPurple}    ██╔██╗ ██║ ╚████╔╝  ╚███╔╝${reset}`,
    `${midPurple}    ██║╚██╗██║  ╚██╔╝   ██╔██╗${reset}`,
    `${deepPurple}    ██║ ╚████║   ██║   ██╔╝ ██╗${reset}`,
    `${deepPurple}    ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝${reset}`,
    `${dim}${deepPurple}        ${stars}·${deepPurple}        ${stars}*${deepPurple}       ${dim}${midPurple}nyx harness${reset}`,
    `${dim}${deepPurple}    ${stars}*${deepPurple}                      ${dim}${midPurple}coding agent${reset}`,
    '',
  ].join('\n');

console.log(nyxLogo);
render(
    <App
      agent={agent}
      skills={skills}
      baseURL={config.baseURL}
      apiKey={config.apiKey}
      cwd={config.cwd}
      onClear={onClear}
      onSaveModel={saveModel}
      nyx={{ apiUrl: config.nyxApiUrl, apiKey: config.nyxApiKey, teamId: config.nyxTeamId }}
      routing={routing}
    />,
  );
}
