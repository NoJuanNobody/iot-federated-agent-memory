"""Tests for Terminal Aeonik Workstation World Labs Atlas v2 UI, Slash Omnibar, TinCanShell, and Token Vault."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter

WORKTREE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKTREE_DIR in sys.path:
    sys.path.remove(WORKTREE_DIR)
sys.path.insert(0, WORKTREE_DIR)

PARENT_DIR = os.path.dirname(os.path.dirname(WORKTREE_DIR))
while PARENT_DIR in sys.path:
    sys.path.remove(PARENT_DIR)

for mod in list(sys.modules.keys()):
    if mod.startswith("iot_federated_agent_memory"):
        del sys.modules[mod]

from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI  # noqa: E402
from iot_federated_agent_memory.shell_component import (  # noqa: E402
    SHELL_CSS,
    SHELL_JS,
    apply_shell_component,
)
from iot_federated_agent_memory.token_vault_ui import (  # noqa: E402
    TOKEN_VAULT_CSS,
    TOKEN_VAULT_JS,
    render_token_vault_window_html,
)
from iot_federated_agent_memory.window_chrome import (  # noqa: E402
    legacy_palette_classes,
)
from iot_federated_agent_memory.workstation_ui import (  # noqa: E402
    FALLBACK_MODELS,
    GATEWAY_DEFS,
    MODE_DEFS,
    render_workstation_window_html,
)


def _extract_workstation_script(html: str) -> str:
    m = re.search(
        r'<script\s+id="workstationUiScript"[^>]*>(.*?)</script>',
        html,
        flags=re.DOTALL,
    )
    assert m, "workstationUiScript block must exist inside render_workstation_window_html()"
    return m.group(1)


def test_workstation_gateway_and_mode_defs_include_atlas() -> None:
    assert ("atlas", "Atlas v2", "SPATIAL", "attested", "World Labs Atlas v2") in GATEWAY_DEFS
    gw_keys = [g[0] for g in GATEWAY_DEFS]
    assert {"atlas", "tee", "heretic", "openrouter"}.issubset(gw_keys)

    assert "atlas" in FALLBACK_MODELS
    atlas_model_ids = {m["id"] for m in FALLBACK_MODELS["atlas"]}
    assert {
        "worldlabs/images2PosedRGBD",
        "worldlabs/posedImages2Splats",
        "worldlabs/atlasGenerate",
        "worldlabs/splats2Mesh",
    }.issubset(atlas_model_ids)

    assert ("atlas", "Atlas World & Splat", "/worlds/torii_3e78434c/refinedSplats_2M.spz") in MODE_DEFS
    mode_keys = [m[0] for m in MODE_DEFS]
    assert mode_keys == ["atlas", "3d", "audit", "arena"]


def test_workstation_atlas_markup_and_terminal_aeonik_palette() -> None:
    html = render_workstation_window_html()

    # Zero legacy dark-slate or neon Tailwind classes
    assert legacy_palette_classes(html) == []
    for forbidden in ("slate-", "zinc-", "cyan-", "purple-", "emerald-", "indigo-"):
        assert forbidden not in html

    # Strict Aeonik Celadon & Ink + Pitch-Black terminal tokens
    for token in ("#ecf1e6", "#f4f8f0", "#ffffff", "#111111", "#107a47", "#8a1c1c", "#000000"):
        assert token in html.lower()

    # Required DOM elements for Atlas World & Splat stage + Slash Directive Omnibar
    for elem_id in (
        "wsGwBtn-atlas",
        "wsModeBtn-atlas",
        "wsStage-atlas",
        "wsStage-3d",
        "wsStage-audit",
        "wsStage-arena",
        "wsDirectiveInput",
        "wsSlashRouteBadge",
        "wsOpenNodeStudioBtn",
        "wsAtlasViewport",
        "wsAtlasOrbitBadge",
        "wsAtlasRubCamBadge",
        "wsAtlasDepthConfidence",
        "wsAtlasStatusNote",
        "wsAtlasSaveBtn",
        "wsOmniTraceConsole",
        "wsOmniTraceLog",
        "wsStatAtlasVal",
        "wsStatOmniVal",
    ):
        assert f'id="{elem_id}"' in html, f"Missing required element id={elem_id}"

    assert "SLASH DIRECTIVE OMNIBAR (⌘K or /)" in html
    assert "Open in Node Studio" in html
    assert "fx=893.4" in html and "fy=893.9" in html
    assert "+98.4% Linear Depth Confidence (.exr verified)" in html
    assert "Pose RGBD $0.05" in html
    assert "24fps Path $0.25" in html
    assert "Splat + GLB $0.50" in html

    # Unique DOM IDs inside Workstation and across MESH_OS_HTML_UI
    ws_ids = re.findall(r'(?<![\w-])id="([^"]+)"', html)
    assert len(ws_ids) == len(set(ws_ids))
    mesh_counts = Counter(re.findall(r'(?<![\w-])id="([^"]+)"', MESH_OS_HTML_UI))
    duplicates = [eid for eid in ws_ids if mesh_counts[eid] != 1]
    assert duplicates == []


def test_workstation_js_slash_omnibar_and_atlas_dispatch() -> None:
    node = shutil.which("node")
    assert node is not None, "Node.js is required to verify workstation JS"

    html = render_workstation_window_html()
    script = _extract_workstation_script(html)

    check = subprocess.run(
        [node, "--check", "-"],
        input=script,
        text=True,
        capture_output=True,
        check=False,
    )
    assert check.returncode == 0, f"node --check failed: {check.stderr}"

    harness = r"""
const vm = require('vm');
const assert = require('assert');

function makeElem(id) {
  return {
    id,
    value: id === 'wsDirectiveInput' ? '/atlas splat /images/torii_gate.jpg --views 14 --mesh --rig walk' : '',
    textContent: '',
    innerHTML: '',
    disabled: false,
    checked: true,
    dataset: {},
    style: {},
    _attrs: {},
    setAttribute(k, v) { this._attrs[k] = String(v); },
    getAttribute(k) { return Object.prototype.hasOwnProperty.call(this._attrs, k) ? this._attrs[k] : null; },
    classList: {
      _set: new Set(id === 'win-workstation' ? ['hidden'] : []),
      add(c) { this._set.add(c); },
      remove(c) { this._set.delete(c); },
      toggle(c, force) {
        if (force === undefined) {
          if (this._set.has(c)) this._set.delete(c); else this._set.add(c);
        } else if (force) {
          this._set.add(c);
        } else {
          this._set.delete(c);
        }
      },
      contains(c) { return this._set.has(c); }
    },
    addEventListener() {},
    appendChild() {},
    removeChild() {},
    querySelector() { return null; },
    querySelectorAll() { return []; },
    getBoundingClientRect() { return { width: 1080, height: 700 }; },
    focus() {},
    scrollIntoView() {}
  };
}

const elements = new Map();
const fetchCalls = [];
const document = {
  readyState: 'complete',
  head: makeElem('head'),
  body: makeElem('body'),
  getElementById(id) {
    if (!elements.has(id)) elements.set(id, makeElem(id));
    return elements.get(id);
  },
  querySelector() { return null; },
  querySelectorAll() { return []; },
  createElement(tag) { return makeElem(tag); },
  addEventListener() {}
};

const window = {
  document,
  addEventListener() {},
  location: { search: '', href: '' }
};

const sandbox = {
  window,
  document,
  console,
  setTimeout,
  clearTimeout,
  AbortController,
  MutationObserver: function() { return { observe() {}, disconnect() {} }; },
  URLSearchParams,
  fetch: async (url, opts) => {
    const bodyObj = opts && opts.body ? JSON.parse(opts.body) : null;
    fetchCalls.push({ url, body: bodyObj });
    if (String(url) === '/api/omni/route') {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ok: true,
          route: {
            is_slash: true,
            command: 'atlas',
            subcommand: 'splat',
            modality: 'atlas',
            model: 'worldlabs/posedImages2Splats',
            atlas_task: 'posedImages2Splats',
            pill_label: '● /atlas splat',
          },
          result: {
            ok: true,
            operation_id: 'op_3e78434c27d24ebfabb4753ebe13a709',
            rub_camera: { fx: 893.4, fy: 893.9, centroidWorld: [-1.99, 0, -36.35] },
            saved_files: [
              '/worlds/torii_3e78434c/refinedSplats_2M.spz',
              '/models3d/torii_rigged.glb'
            ]
          },
          saved_to_space: [
            '/worlds/torii_3e78434c/refinedSplats_2M.spz',
            '/models3d/torii_rigged.glb'
          ]
        })
      };
    }
    return { ok: true, status: 200, json: async () => ({}) };
  }
};
sandbox.globalThis = sandbox;
const code = require('fs').readFileSync(0, 'utf8');
vm.runInNewContext(code, sandbox);

(async () => {
  const api = window.TinCanWorkstation;
  assert.ok(api, 'TinCanWorkstation missing');

  // Verify all 8 slash commands parse cleanly
  const slashFixtures = [
    ['/atlas splat /images/torii.jpg --views 14', 'atlas', '● /atlas splat'],
    ['/image --model flux-2-max cyberpunk shrine', 'image', '◐ /image'],
    ['/video --fps 24 shrine flythrough', 'video', '▶ /video'],
    ['/audio music koto rain', 'audio', '♪ /audio music'],
    ['/3d --tier Regular stone lantern', '3d', '◆ /3d'],
    ['/rig --anim walk /models3d/guardian.glb', 'rig', '🦴 /rig'],
    ['/text summarize world telemetry', 'text', '¶ /text'],
    ['/mux --video /videos/a.mp4 --audio /audio/b.wav', 'mux', '⊕ /mux'],
  ];
  for (const [cmd, expectedVerb, expectedPill] of slashFixtures) {
    const parsed = api.parseSlashDirective(cmd);
    assert.strictEqual(parsed.is_slash, true, 'Expected is_slash for ' + cmd);
    assert.strictEqual(parsed.command, expectedVerb);
    assert.strictEqual(parsed.pill_label, expectedPill);
  }

  // Test typing into #wsDirectiveInput updates #wsSlashRouteBadge
  const dirInput = document.getElementById('wsDirectiveInput');
  dirInput.value = '/audio music ambient rain';
  if (typeof dirInput.oninput === 'function') dirInput.oninput();
  assert.strictEqual(document.getElementById('wsSlashRouteBadge').textContent, '♪ /audio music');

  // Test dispatching /atlas command to /api/omni/route
  dirInput.value = '/atlas splat /images/torii_gate.jpg --views 14 --mesh --rig walk';
  if (typeof dirInput.oninput === 'function') dirInput.oninput();
  await api.dispatch();

  const omniCall = fetchCalls.find((c) => c.url === '/api/omni/route');
  assert.ok(omniCall, 'Expected POST to /api/omni/route');
  assert.ok(omniCall.body.command.startsWith('/atlas splat'));
  assert.ok(document.getElementById('wsAtlasRubCamBadge').textContent.includes('fx=893.4'));
  assert.ok(document.getElementById('wsAtlasRubCamBadge').textContent.includes('fy=893.9'));
  assert.ok(document.getElementById('wsAtlasDepthConfidence').textContent.includes('+98.4% Linear Depth Confidence (.exr verified)'));
  assert.ok(document.getElementById('wsStagedList').innerHTML.includes('/worlds/torii_3e78434c/refinedSplats_2M.spz'));
  assert.ok(document.getElementById('wsStagedList').innerHTML.includes('/models3d/torii_rigged.glb'));

  // Test Open in Node Studio button
  api.openInNodeStudio();
  assert.strictEqual(document.getElementById('win-nodes').classList.contains('hidden'), false);
  process.stdout.write('WS_ATLAS_OK');
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
"""
    run = subprocess.run(
        [node, "-e", harness],
        input=script,
        text=True,
        capture_output=True,
        check=False,
    )
    assert run.returncode == 0, f"Workstation VM test failed: {run.stderr}"
    assert run.stdout.strip() == "WS_ATLAS_OK"


def test_tincan_shell_pitch_black_and_omni_slash_commands() -> None:
    # Always-Dark Pitch-Black #000000 with #ffffff border and zero legacy palette classes
    assert "#000000" in SHELL_CSS.lower()
    assert "1.5px solid #ffffff" in SHELL_CSS.lower()
    assert legacy_palette_classes(SHELL_CSS) == []
    assert legacy_palette_classes(SHELL_JS) == []
    for forbidden in ("slate-", "zinc-", "cyan-", "purple-", "emerald-", "indigo-"):
        assert forbidden not in SHELL_CSS
        assert forbidden not in SHELL_JS

    rendered = apply_shell_component("/*TC_SHELL_CSS*/\n/*TC_SHELL_JS*/")
    assert "/api/omni/route" in rendered

    node = shutil.which("node")
    assert node is not None, "Node.js is required to test SHELL_JS"

    check = subprocess.run(
        [node, "--check", "-"],
        input=SHELL_JS,
        text=True,
        capture_output=True,
        check=False,
    )
    assert check.returncode == 0, f"SHELL_JS syntax check failed: {check.stderr}"

    harness = r"""
const vm = require('vm');
const assert = require('assert');

const postedPayloads = [];
const sandbox = {
  console,
  setInterval: () => 0,
  clearInterval: () => {},
  setTimeout: () => 0,
  CustomEvent: function(name, init) { this.name = name; this.detail = init && init.detail; },
  localStorage: { getItem: () => 'aeonik' },
  currentSpaceScope: 'user',
  currentSpaceOwner: 'owner_atlas',
  myPeerId: 'peer_atlas',
  document: {
    getElementById: () => null,
    querySelectorAll: () => [],
  },
  window: {
    addEventListener: () => {},
    dispatchEvent: () => {},
  },
  fetch: async (url, opts) => {
    const body = opts && opts.body ? JSON.parse(opts.body) : {};
    postedPayloads.push({ url, body });
    return {
      ok: true,
      status: 200,
      json: async () => ({
        ok: true,
        route: {
          is_slash: true,
          command: body.command.split(/\s+/)[0].replace(/^\//, ''),
          subcommand: 'splat',
          modality: body.command.startsWith('/audio') ? 'audio' : 'atlas',
          model: body.command.startsWith('/audio') ? 'google/lyria-3.5' : 'worldlabs/posedImages2Splats',
          pill_label: body.command.startsWith('/audio') ? '♪ /audio music' : '● /atlas splat'
        },
        result: {
          operation_id: 'op_3e78434c27d24ebfabb4753ebe13a709',
          rub_camera: { fx: 893.4, fy: 893.9 },
          sparkline: body.command.startsWith('/audio') ? '│┃│┃┃│┃┃' : undefined,
          lufs: -14.0,
          saved_files: [
            '/worlds/torii_3e78434c/refinedSplats_2M.spz',
            '/models3d/torii_rigged.glb'
          ]
        },
        saved_to_space: [
          '/worlds/torii_3e78434c/refinedSplats_2M.spz',
          '/models3d/torii_rigged.glb'
        ]
      })
    };
  }
};
sandbox.window.TinCanShell = null;
const code = require('fs').readFileSync(0, 'utf8');
vm.runInNewContext(code, sandbox);

(async () => {
  const shell = sandbox.window.TinCanShell;
  assert.ok(shell && typeof shell.run === 'function', 'TinCanShell.run missing');

  const commands = [
    '/atlas splat /images/torii_gate.jpg --views 14 --mesh --rig walk',
    '/image --model gemini-nano-banana-2.1 neon torii',
    '/video --model kling-4.0 lake flythrough',
    '/audio music Japanese koto & rain',
    '/3d --model hyper3d/rodin-v2.5 guardian statue',
    '/rig --anim walk /models3d/guardian.glb',
    '/text architectural critique',
    '/mux --video /videos/torii.mp4 --audio /audio/koto.wav',
  ];

  for (const cmd of commands) {
    const res = await shell.run(cmd);
    assert.strictEqual(res.ok, true, 'Command failed: ' + cmd + ' -> ' + res.text);
    assert.ok(res.text.includes('op_3e78434c27d24ebfabb4753ebe13a709'), 'Missing operation ID in output');
    assert.ok(res.text.includes('/worlds/torii_3e78434c/refinedSplats_2M.spz'), 'Missing saved VFS path');
  }

  assert.strictEqual(postedPayloads.length, commands.length);
  assert.strictEqual(postedPayloads[0].url, '/api/omni/route');
  assert.strictEqual(postedPayloads[0].body.command, commands[0]);
  assert.strictEqual(postedPayloads[0].body.prompt, commands[0]);
  assert.strictEqual(postedPayloads[0].body.scope, 'user');
  assert.strictEqual(postedPayloads[0].body.owner_id, 'owner_atlas');

  const atlasRes = await shell.run(commands[0]);
  assert.ok(atlasRes.text.includes('fx=893.4') && atlasRes.text.includes('fy=893.9'));

  const audioRes = await shell.run(commands[3]);
  assert.ok(audioRes.text.includes('│┃│┃┃│┃┃'));

  process.stdout.write('SHELL_OMNI_OK');
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
"""
    run = subprocess.run(
        [node, "-e", harness],
        input=SHELL_JS,
        text=True,
        capture_output=True,
        check=False,
    )
    assert run.returncode == 0, f"SHELL_JS VM execution failed: {run.stderr}"
    assert run.stdout.strip() == "SHELL_OMNI_OK"


def test_token_vault_worldlabs_atlas_pool_indicator() -> None:
    html = render_token_vault_window_html()

    assert legacy_palette_classes(html) == []
    assert legacy_palette_classes(TOKEN_VAULT_CSS) == []
    assert legacy_palette_classes(TOKEN_VAULT_JS) == []
    for forbidden in ("slate-", "zinc-", "cyan-", "purple-", "emerald-", "indigo-"):
        assert forbidden not in html
        assert forbidden not in TOKEN_VAULT_CSS

    assert "World Labs Atlas v2" in html
    assert "WLT_API_KEY" in html
    assert "1,000 CR = $1.00" in html
    for elem_id in ("tvAtlasPoolCard", "tvAtlasPoolVal", "tvAtlasPoolSub", "tvAtlasBillingStatusBadge"):
        assert f'id="{elem_id}"' in html
