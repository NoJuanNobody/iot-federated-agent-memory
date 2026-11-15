"""Tests for iot_federated_agent_memory.ai_home_shell (Aeonik Celadon AI Home Hub)."""

from __future__ import annotations

import inspect
import os
import re
import shutil
import subprocess
import sys

WORKTREE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKTREE_DIR not in sys.path:
    sys.path.insert(0, WORKTREE_DIR)

from iot_federated_agent_memory import ai_home_shell  # noqa: E402
from iot_federated_agent_memory.ai_home_shell import (  # noqa: E402
    AI_HOME_SHELL_CSS,
    AI_HOME_SHELL_JS,
    HOME_CSS_SLOT,
    HOME_HUB_MARKER,
    HOME_JS_SLOT,
    ROUTER_CHIPS,
    WORKFLOW_CARDS,
    apply_ai_home_shell,
    render_ai_home_hub_html,
)
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI  # noqa: E402
from iot_federated_agent_memory.window_chrome import (  # noqa: E402
    apply_window_chrome,
    celadonize_classes,
    legacy_palette_classes,
)


def test_router_chips_and_workflow_cards_contract() -> None:
    assert isinstance(ROUTER_CHIPS, tuple)
    assert ROUTER_CHIPS == (
        "ollama/qwen2.5:3b · $0 FREE",
        "FAU OWLCHAT · BYOK HPC",
        "NANOGPT TEE · $0.002/1K",
        "CLAUDE SONNET · SERVER POOL",
    )

    assert isinstance(WORKFLOW_CARDS, tuple)
    assert len(WORKFLOW_CARDS) == 4
    by_id = {c["id"]: c for c in WORKFLOW_CARDS}
    assert set(by_id) == {
        "aiHomeCardCopilot",
        "aiHomeCardArena",
        "aiHomeCardWorkstation",
        "aiHomeCardTokens",
    }

    assert by_id["aiHomeCardCopilot"]["title"] == "AI Copilot"
    assert by_id["aiHomeCardCopilot"]["badge"] == "NEW WORKSPACE · /copilot"
    assert by_id["aiHomeCardCopilot"]["window_id"] == "win-copilot"
    assert by_id["aiHomeCardCopilot"]["fallback_window_id"] == "win-terminal"
    assert by_id["aiHomeCardCopilot"]["route"] == "/copilot"

    assert by_id["aiHomeCardArena"]["title"] == "AI Brain Arena"
    assert by_id["aiHomeCardArena"]["badge"] == "BLIND DUEL · /arena"
    assert by_id["aiHomeCardArena"]["window_id"] == "win-arena"
    assert by_id["aiHomeCardArena"]["route"] == "/arena"

    assert by_id["aiHomeCardWorkstation"]["title"] == "Rodin 3D + Space"
    assert by_id["aiHomeCardWorkstation"]["badge"] == "PRO ASSETS · /workstation"
    assert by_id["aiHomeCardWorkstation"]["window_id"] == "win-workstation"
    assert by_id["aiHomeCardWorkstation"]["route"] == "/workstation"

    assert by_id["aiHomeCardTokens"]["title"] == "Token Vault + Ads"
    assert by_id["aiHomeCardTokens"]["badge"] == "MONETIZE · /tokens"
    assert by_id["aiHomeCardTokens"]["window_id"] == "win-billing"
    assert by_id["aiHomeCardTokens"]["route"] == "/tokens"


def test_render_ai_home_hub_html_structure_and_hooks() -> None:
    frag = render_ai_home_hub_html()
    assert frag.startswith('<section id="aiHomeHub"')
    assert frag.rstrip().endswith("</section>")

    # Hero command shell input + Dispatch CTA
    assert 'id="aiHomePromptInput"' in frag
    assert 'id="aiHomeDispatchBtn"' in frag
    assert "Dispatch [Enter]" in frag
    assert "tincan ask" in frag

    # All 4 interactive router chip buttons with data-gateway attributes
    for chip in ROUTER_CHIPS:
        assert chip in frag
    for gw in ("ollama", "owlchat", "nanogpt-tee", "openrouter"):
        assert f'data-gateway="{gw}"' in frag

    # All 4 workflow cards and launch targets
    for card in WORKFLOW_CARDS:
        assert f'id="{card["id"]}"' in frag
        assert card["title"] in frag
        assert card["badge"] in frag
        assert f'data-window="{card["window_id"]}"' in frag
        assert f'data-route="{card["route"]}"' in frag

    # Monochrome telemetry sparkline strip & .space Merkle status hooks
    assert 'id="aiHomeSparkline"' in frag
    assert 'fill="#111111"' in frag
    assert 'id="aiHomeTelemetryLocal"' in frag
    assert 'id="aiHomeTelemetrySaved"' in frag
    assert 'id="aiHomeTelemetryMerkle"' in frag
    assert 'data-merkle-hook="space"' in frag


def test_aeonik_celadon_palette_and_no_legacy_slate_neon() -> None:
    frag = render_ai_home_hub_html()
    full_src = inspect.getsource(ai_home_shell)

    assert legacy_palette_classes(frag) == []
    assert legacy_palette_classes(AI_HOME_SHELL_CSS) == []
    assert legacy_palette_classes(AI_HOME_SHELL_JS) == []

    forbidden_tokens = (
        "bg-slate-9",
        "bg-slate-8",
        "text-slate-",
        "border-slate-",
        "text-cyan-",
        "bg-cyan-",
        "bg-emerald-",
        "text-emerald-",
        "text-indigo-",
        "bg-indigo-",
        "bg-gradient-to-",
        "#020617",
        "#0f172a",
    )
    for bad in forbidden_tokens:
        assert bad not in frag, f"Forbidden token {bad!r} in fragment"
        assert bad not in AI_HOME_SHELL_CSS, f"Forbidden token {bad!r} in CSS"
        assert bad not in full_src, f"Forbidden token {bad!r} in ai_home_shell.py"

    for color in ("#dfe6d7", "#ecf1e6", "#f4f8f0", "#ffffff", "#111111", "#107a47", "#8a1c1c"):
        assert color in AI_HOME_SHELL_CSS.lower()
        assert color in frag.lower()

    assert "Inter" in AI_HOME_SHELL_CSS
    assert "JetBrains Mono" in AI_HOME_SHELL_CSS
    assert "grid-template-columns: repeat(4, minmax(0, 1fr))" in AI_HOME_SHELL_CSS
    assert "@media (max-width: 980px)" in AI_HOME_SHELL_CSS
    assert "@media (max-width: 560px)" in AI_HOME_SHELL_CSS
    assert "window.TinCanShell" in AI_HOME_SHELL_JS
    assert "/api/chat" in AI_HOME_SHELL_JS


def test_apply_ai_home_shell_idempotency_and_fragment_safety() -> None:
    tpl = f"""<!DOCTYPE html>
<html>
<head><style>{HOME_CSS_SLOT}</style></head>
<body>
  <main>{HOME_HUB_MARKER}</main>
  <script>{HOME_JS_SLOT}</script>
</body>
</html>"""

    once = apply_ai_home_shell(tpl)
    assert HOME_HUB_MARKER not in once
    assert HOME_CSS_SLOT not in once
    assert HOME_JS_SLOT not in once
    assert 'id="aiHomeHub"' in once
    assert "#aiHomeHub .tc-ai-cards-grid" in once
    assert "window.TinCanAIHome" in once

    # Idempotent second pass
    assert apply_ai_home_shell(once) == once

    # Safe with unmatched fragments or empty strings
    for untouched in ("", "<div>plain fragment</div>", "<section>no markers here</section>"):
        assert apply_ai_home_shell(untouched) == untouched

    # Existing MESH_OS_HTML_UI without home markers stays untouched
    assert apply_ai_home_shell(MESH_OS_HTML_UI) == MESH_OS_HTML_UI

    # Compatible with apply_window_chrome (no mangling of AI Home markup or JS strings)
    assert celadonize_classes(once) == once
    chromed = apply_window_chrome(once)
    assert 'id="aiHomeHub"' in chromed
    assert "window.TinCanAIHome" in chromed
    assert "tincan:ai-home-launch" in chromed
    assert legacy_palette_classes(chromed.split('id="aiHomeHub"', 1)[1]) == []

    # include_assets=True produces a standalone fragment with style + script
    standalone = render_ai_home_hub_html(include_assets=True)
    assert '<style id="tc-ai-home-css">' in standalone
    assert '<script id="tc-ai-home-js">' in standalone
    assert 'id="aiHomeHub"' in standalone


def test_unique_ids_and_no_mesh_os_collisions_or_terminal_regressions() -> None:
    frag = render_ai_home_hub_html()
    hub_ids = re.findall(r'(?<![\w-])id="([^"]+)"', frag)
    assert len(hub_ids) >= 12
    assert len(hub_ids) == len(set(hub_ids))

    mesh_counts = re.findall(r'(?<![\w-])id="([^"]+)"', MESH_OS_HTML_UI)
    from collections import Counter

    counts = Counter(mesh_counts)
    assert all(counts[eid] == 1 for eid in hub_ids), f"Duplicate or missing hub IDs in MESH_OS_HTML_UI: { {eid: counts[eid] for eid in hub_ids if counts[eid] != 1} }"

    # Ensure none of the forbidden #win-terminal elements from test_terminal_space_ide.py appear
    for forbidden in ("termTree", "termDriveTree", "termStatFiles", "termRunsTable", "aeonikRecentOutput", "RECENT"):
        assert forbidden not in frag


def test_ai_home_shell_js_syntax_and_runtime_behavior() -> None:
    node_bin = shutil.which("node")
    assert node_bin, "node binary required to validate AI_HOME_SHELL_JS"

    syntax_proc = subprocess.run(
        [node_bin, "--input-type=commonjs", "--check"],
        input=AI_HOME_SHELL_JS,
        capture_output=True,
        text=True,
    )
    assert syntax_proc.returncode == 0, f"JS syntax error: {syntax_proc.stderr}"

    harness = f"""
const assert = require('assert');

function makeEl(id, attrs = {{}}) {{
  const classes = new Set();
  const children = [];
  const listeners = {{}};
  return {{
    id,
    value: '',
    textContent: '',
    disabled: false,
    style: {{}},
    attrs: Object.assign({{}}, attrs),
    classList: {{
      add: (...c) => c.forEach(x => classes.add(x)),
      remove: (...c) => c.forEach(x => classes.delete(x)),
      toggle: (c, force) => (force === undefined ? (classes.has(c) ? classes.delete(c) : classes.add(c)) : (force ? classes.add(c) : classes.delete(c))),
      contains: (c) => classes.has(c),
    }},
    getAttribute(k) {{ return this.attrs[k] ?? null; }},
    setAttribute(k, v) {{ this.attrs[k] = String(v); }},
    addEventListener(t, fn) {{ (listeners[t] = listeners[t] || []).push(fn); }},
    querySelectorAll() {{ return []; }},
    querySelector() {{ return null; }},
    contains() {{ return true; }},
    closest() {{ return null; }},
    focus() {{ this._focused = true; }},
    _listeners: listeners,
    _children: children,
  }};
}}

const els = {{
  aiHomeHub: makeEl('aiHomeHub'),
  aiHomePromptInput: makeEl('aiHomePromptInput'),
  aiHomeDispatchBtn: makeEl('aiHomeDispatchBtn'),
  aiHomeDispatchOut: makeEl('aiHomeDispatchOut'),
  aiHomeDispatchMeta: makeEl('aiHomeDispatchMeta'),
  aiHomeDispatchBody: makeEl('aiHomeDispatchBody'),
  aiHomeCommandForm: makeEl('aiHomeCommandForm'),
  aiHomeDispatchClear: makeEl('aiHomeDispatchClear'),
  aiHomeTelemetryLocal: makeEl('aiHomeTelemetryLocal'),
  aiHomeTelemetrySaved: makeEl('aiHomeTelemetrySaved'),
  aiHomeTelemetryMerkle: makeEl('aiHomeTelemetryMerkle'),
  'win-terminal': makeEl('win-terminal'),
}};
els['win-terminal'].classList.add('hidden');
const statusSpan = makeEl('statusSpan');
const merkleSpan = makeEl('merkleSpan');

const chipOllama = makeEl('chip0', {{ 'data-gateway': 'ollama', 'data-model': 'ollama/qwen2.5:3b', 'data-chip-label': 'ollama/qwen2.5:3b · $0 FREE', 'data-status-text': 'LOCAL FIRST' }});
const chipTee = makeEl('chip2', {{ 'data-gateway': 'nanogpt-tee', 'data-model': 'nanogpt/TEE/deepseek-v4.1-flash', 'data-chip-label': 'NANOGPT TEE · $0.002/1K', 'data-status-text': 'NANOGPT TEE · ATTESTED ENCLAVE' }});
const chips = [chipOllama, chipTee];
els.aiHomeHub.querySelectorAll = (sel) => (sel.includes('tc-ai-chip') ? chips : []);

const shellCalls = [];
const fetchCalls = [];
const toggledWindows = [];

global.CustomEvent = function(type, init) {{ this.type = type; this.detail = init && init.detail; }};
global.document = {{
  readyState: 'complete',
  getElementById: (id) => els[id] || null,
  querySelector: (sel) => {{
    if (sel.includes('status-text')) return statusSpan;
    if (sel.includes('merkle-label')) return merkleSpan;
    return null;
  }},
  querySelectorAll: () => [],
  addEventListener: () => {{}},
}};
global.window = {{
  document: global.document,
  addEventListener: () => {{}},
  dispatchEvent: () => true,
  TinCanShell: {{
    run: async (line, opts) => {{
      shellCalls.push({{ line, opts }});
      return {{ ok: true, text: 'src/  tests/' }};
    }}
  }},
  toggleWindow: (id) => {{
    toggledWindows.push(id);
    if (els[id]) els[id].classList.remove('hidden');
  }},
}};
global.fetch = async (url, init) => {{
  fetchCalls.push({{ url, init }});
  if (url.startsWith('/api/space/ls')) {{
    return {{ ok: true, json: async () => ({{ merkle_root: '9b2e41aa' }}) }};
  }}
  if (url === '/api/chat') {{
    return {{ ok: true, json: async () => ({{ content: 'Patched relay_router.py cleanly.' }}) }};
  }}
  return {{ ok: false, status: 404, json: async () => ({{}}) }};
}};

{AI_HOME_SHELL_JS}

(async () => {{
  const api = window.TinCanAIHome;
  assert.strictEqual(api.version, 1);

  // 1. Telemetry refresh from /api/space/ls
  await api.refreshTelemetry();
  assert.strictEqual(els.aiHomeTelemetryMerkle.textContent, '9b2e41');
  assert.strictEqual(merkleSpan.textContent, '.space merkle · 9b2e41');

  // 2. Shell verb dispatches via TinCanShell.run
  const shellRes = await api.dispatch('ls');
  assert.strictEqual(shellRes.ok, true);
  assert.strictEqual(shellCalls.length, 1);
  assert.strictEqual(shellCalls[0].line, 'ls');

  // 3. Gateway chip switch + tincan ask prompt routes to /api/chat with chosen model
  api.selectGateway(chipTee);
  assert.strictEqual(api.state.gateway, 'nanogpt-tee');
  assert.strictEqual(api.state.model, 'nanogpt/TEE/deepseek-v4.1-flash');
  assert.strictEqual(statusSpan.textContent, 'NANOGPT TEE · ATTESTED ENCLAVE');

  const chatRes = await api.dispatch('tincan ask "Audit relay_router.py"');
  assert.strictEqual(chatRes.ok, true);
  assert.strictEqual(chatRes.text, 'Patched relay_router.py cleanly.');
  const chatCall = fetchCalls.find(c => c.url === '/api/chat');
  assert.ok(chatCall, 'Expected POST /api/chat call');
  const payload = JSON.parse(chatCall.init.body);
  assert.strictEqual(payload.model, 'nanogpt/TEE/deepseek-v4.1-flash');
  assert.strictEqual(payload.gateway, 'nanogpt-tee');
  assert.strictEqual(payload.prompt, 'Audit relay_router.py');

  // 4. Copilot card falls back to win-terminal when win-copilot is not in DOM
  const openedFallback = api.openWindowTarget('win-copilot', 'win-terminal', '/copilot');
  assert.strictEqual(openedFallback, true);
  assert.deepStrictEqual(toggledWindows, ['win-terminal']);

  // 5. When win-copilot IS in DOM, opens win-copilot directly
  els['win-copilot'] = makeEl('win-copilot');
  els['win-copilot'].classList.add('hidden');
  const openedPrimary = api.openWindowTarget('win-copilot', 'win-terminal', '/copilot');
  assert.strictEqual(openedPrimary, true);
  assert.deepStrictEqual(toggledWindows, ['win-terminal', 'win-copilot']);

  // 6. When neither window exists, navigates to route
  let navigated = null;
  global.window.location = {{ assign: (r) => {{ navigated = r; }} }};
  const openedStandalone = api.openWindowTarget('win-missing', 'win-also-missing', '/tokens');
  assert.strictEqual(openedStandalone, false);
  assert.strictEqual(navigated, '/tokens');

  // 7. Error path on /api/chat marks output with is-error
  const origFetch = global.fetch;
  global.fetch = async () => ({{ ok: false, status: 502, json: async () => ({{ error: 'Upstream offline' }}) }});
  const errRes = await api.dispatch('hello');
  assert.strictEqual(errRes.ok, false);
  assert.strictEqual(errRes.text, 'Upstream offline');
  assert.strictEqual(els.aiHomeDispatchOut.classList.contains('is-error'), true);

  // 8. Fallback to TinCanShell.run when fetch is unavailable
  global.fetch = undefined;
  const fbRes = await api.dispatch('tincan ask "fallback check"');
  assert.strictEqual(fbRes.ok, true);
  assert.strictEqual(shellCalls[shellCalls.length - 1].line, 'ask fallback check');
  global.fetch = origFetch;
}})().catch((err) => {{
  console.error(err);
  process.exit(1);
}});
"""
    run_proc = subprocess.run([node_bin, "-e", harness], capture_output=True, text=True)
    assert run_proc.returncode == 0, f"JS runtime test failed:\n{run_proc.stderr}\n{run_proc.stdout}"
