"""Unit tests for ai_gateway_telemetry and copilot_ui."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from types import SimpleNamespace
from unittest.mock import MagicMock

WORKTREE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKTREE_DIR not in sys.path:
    sys.path.insert(0, WORKTREE_DIR)

from iot_federated_agent_memory.agent_space import SingleFileSpaceVFS  # noqa: E402
from iot_federated_agent_memory.ai_gateway import DynamicAIGatewayRouter  # noqa: E402
from iot_federated_agent_memory.ai_gateway_telemetry import (  # noqa: E402
    classify_gateway,
    collect_gateway_telemetry,
    estimate_preflight,
)
from iot_federated_agent_memory.copilot_ui import (  # noqa: E402
    COPILOT_CSS,
    COPILOT_CSS_SLOT,
    COPILOT_JS_SLOT,
    COPILOT_SCRIPT,
    COPILOT_WINDOW_SLOT,
    DEFAULT_GATEWAY_CARDS,
    PRIORITY_DEFS,
    apply_copilot_ui,
    render_copilot_window_html,
)
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI  # noqa: E402
from iot_federated_agent_memory.window_chrome import (  # noqa: E402
    apply_window_chrome,
    expand_titlebars,
    legacy_palette_classes,
)


def _extract_inline_script(html: str) -> str:
    m = re.search(
        r'<script\s+id="copilotUiScript"[^>]*>(.*?)</script>',
        html,
        flags=re.DOTALL,
    )
    assert m, "copilotUiScript block must exist inside render_copilot_window_html()"
    return m.group(1)


# ---------------------------------------------------------------------------
# Backend telemetry & pre-flight tests
# ---------------------------------------------------------------------------


def test_collect_gateway_telemetry_with_real_router_and_usage(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("NANOGPT_API_KEY", raising=False)
    monkeypatch.delenv("OWLCHAT_API_KEY", raising=False)
    monkeypatch.delenv("FAU_OWLCHAT_API_KEY", raising=False)

    router = DynamicAIGatewayRouter(openrouter_key=None, nanogpt_key=None)
    monkeypatch.setattr(router, "get_ollama_models", lambda: [{"id": "ollama/qwen2.5:3b", "name": "qwen2.5:3b"}])
    monkeypatch.setattr(
        router,
        "get_nanogpt_billing",
        lambda: {"connected": True, "account_remaining_balance_usd": 42.10},
    )
    monkeypatch.setattr(
        router,
        "get_openrouter_billing",
        lambda: {"connected": True, "account_remaining_balance_usd": 128.40},
    )

    # Record 3 local Ollama turns + 1 FAU OwlChat turn + 1 OpenRouter cloud turn
    for _ in range(3):
        router.route_request("ollama/qwen2.5:3b")
        router.record_usage("ollama/qwen2.5:3b", 200, 100, 300, 0.0)
    router.route_request("owlchat/llama-3.3-70b")
    router.record_usage("owlchat/llama-3.3-70b", 300, 150, 450, 0.0)
    router.route_request("claude-brain", estimated_cost=0.02)
    router.record_usage("claude-brain", 250, 150, 400, 0.003)

    space_file = tmp_path / "test_copilot.space"
    vfs = SingleFileSpaceVFS(
        scope="user",
        owner_id="alejandro",
        space_path=str(space_file),
        enable_s3_sync=False,
    )
    vfs.write_file("/ai_gateway.py", "print('hello copilot')\n", updated_by="alejandro")

    telem = collect_gateway_telemetry(router, space_owner="alejandro", vfs=vfs)

    gateways = telem["gateways"]
    assert [g["id"] for g in gateways] == ["ollama", "fau-owlchat", "nanogpt-tee", "openrouter"]
    assert [g["priority"] for g in gateways] == [1, 2, 3, 4]

    by_id = {g["id"]: g for g in gateways}
    assert by_id["ollama"]["name"] == "ollama (local)"
    assert by_id["ollama"]["rate_label"] == "FREE · $0.00"
    assert by_id["ollama"]["connected"] is True
    assert by_id["ollama"]["models_count"] == 1
    assert by_id["ollama"]["calls"] == 3

    assert by_id["fau-owlchat"]["name"] == "fau-owlchat"
    assert by_id["fau-owlchat"]["rate_label"] == "BYOK · HPC"
    assert by_id["fau-owlchat"]["calls"] == 1

    assert by_id["nanogpt-tee"]["connected"] is True
    assert by_id["nanogpt-tee"]["balance_usd"] == 42.10
    assert "$42.10 pool" == by_id["nanogpt-tee"]["rate_label"]

    assert by_id["openrouter"]["connected"] is True
    assert by_id["openrouter"]["balance_usd"] == 128.40
    assert "$128.40 pool" == by_id["openrouter"]["rate_label"]
    assert by_id["openrouter"]["calls"] == 1

    arb = telem["arbitrage"]
    assert arb["local_turns"] == 4
    assert arb["cloud_turns"] == 1
    assert arb["total_calls"] == 5
    assert arb["total_tokens"] == 3 * 300 + 450 + 400
    assert arb["local_ratio"] == 0.8
    assert arb["estimated_usd_saved"] >= 0.08

    assert telem["space"]["owner_id"] == "alejandro"
    assert telem["space"]["file_count"] >= 1
    assert telem["space"]["merkle_root"]
    assert any(f["path"] == "/ai_gateway.py" for f in telem["space"]["files"])


def test_collect_gateway_telemetry_tolerates_mocked_offline_and_broken_routers() -> None:
    def _boom(*args, **kwargs):
        raise ConnectionError("network offline")

    partial_router = SimpleNamespace(
        get_nanogpt_billing=_boom,
        get_openrouter_billing=_boom,
        get_ollama_models=_boom,
        get_analytics=_boom,
        routing_log=[
            {"lab": "ollama", "model": "ollama/qwen2.5:3b"},
            {"lab": "openrouter", "model": "anthropic/claude-3.7-sonnet"},
        ],
    )
    telem = collect_gateway_telemetry(partial_router)
    assert len(telem["gateways"]) == 4
    assert telem["gateways"][0]["rate_label"] == "FREE · $0.00"
    assert telem["gateways"][1]["rate_label"] == "BYOK · HPC"
    assert telem["gateways"][2]["connected"] is False
    assert telem["gateways"][3]["connected"] is False
    assert telem["arbitrage"]["local_turns"] == 1
    assert telem["arbitrage"]["cloud_turns"] == 1
    assert telem["arbitrage"]["local_ratio"] == 0.5

    # Completely bare / MagicMock / None routers never crash
    for stub in (None, object(), MagicMock()):
        res = collect_gateway_telemetry(stub)
        assert [g["id"] for g in res["gateways"]] == ["ollama", "fau-owlchat", "nanogpt-tee", "openrouter"]
        assert isinstance(res["arbitrage"]["local_turns"], int)
        assert isinstance(res["arbitrage"]["cloud_turns"], int)
        assert isinstance(res["arbitrage"]["local_ratio"], float)
        assert isinstance(res["arbitrage"]["estimated_usd_saved"], float)


def test_estimate_preflight_zero_burn_vs_cloud_and_classify_gateway() -> None:
    assert classify_gateway("ollama/qwen2.5:3b") == "ollama"
    assert classify_gateway("owlchat/llama-3.3-70b") == "fau-owlchat"
    assert classify_gateway("trussed/deepseek-r1") == "fau-owlchat"
    assert classify_gateway("nanogpt/TEE/deepseek-v4.1-flash") == "nanogpt-tee"
    assert classify_gateway("anthropic/claude-3.7-sonnet") == "openrouter"

    for local_alias in (
        "ollama/qwen2.5:3b",
        "ollama-brain",
        "owlchat/llama-3.3-70b",
        "trussed/deepseek-r1",
        "local/custom-7b",
    ):
        est = estimate_preflight(local_alias, prompt_chars=800)
        assert est["estimated_credits"] == 0
        assert est["estimated_usd"] == 0.0
        assert est["credits_label"] == "0 CR"
        assert est["is_zero_burn"] is True
        assert est["cloud_equivalent_credits"] >= 3
        assert "0 CR Free" in est["display_badge"]
        assert est["recommended_route"]

    cloud_short = estimate_preflight("claude-brain", prompt_chars=200)
    cloud_long = estimate_preflight("claude-brain", prompt_chars=24000)
    assert cloud_short["is_zero_burn"] is False
    assert cloud_short["estimated_credits"] > 0
    assert cloud_short["estimated_usd"] > 0.0
    assert cloud_short["credits_label"].endswith(" CR")
    assert cloud_short["recommended_route"] == "openrouter pooled"
    assert cloud_long["estimated_credits"] > cloud_short["estimated_credits"]

    tee_est = estimate_preflight("nanogpt/TEE/deepseek-v4.1-flash", prompt_chars=4000)
    assert tee_est["is_zero_burn"] is False
    assert tee_est["estimated_credits"] > 0
    assert tee_est["recommended_route"] == "nanogpt-tee enclave"


# ---------------------------------------------------------------------------
# UI markup, scoping, palette, and idempotency tests
# ---------------------------------------------------------------------------


def test_render_copilot_window_root_titlebar_and_structure() -> None:
    html = render_copilot_window_html()
    assert isinstance(html, str)
    expected_root = (
        '<div id="win-copilot" class="mesh-window w-[1080px] max-w-full hidden" '
        'data-zen-window="true" data-window-id="win-copilot" '
        'style="top: 64px; left: 96px; z-index: 37;">'
    )
    assert html.startswith(expected_root)
    assert html.rstrip().endswith("</div>")

    after_root = html[len(expected_root) :].lstrip()
    expected_titlebar = (
        '<!--TC_TITLEBAR {"id": "win-copilot", '
        '"title": "AI Copilot · Multi-Model Router & Space Diffs", '
        '"badge": "COPILOT + ROUTER", '
        '"meta_html": "<span id=\\"copilotHeaderRoute\\">direct ollama localhost:11434</span>"}-->'
    )
    assert after_root.startswith(expected_titlebar)

    expanded = expand_titlebars(html)
    assert "<!--TC_TITLEBAR" not in expanded
    assert 'data-tc-titlebar="win-copilot"' in expanded
    assert "AI Copilot · Multi-Model Router &amp; Space Diffs" in expanded
    assert "COPILOT + ROUTER" in expanded
    assert 'id="copilotHeaderRoute"' in expanded

    page = f"<!doctype html><html><head></head><body>{html}</body></html>"
    chromed = apply_window_chrome(page)
    assert "<!--TC_TITLEBAR" not in chromed
    assert 'id="tc-celadon"' in chromed
    assert 'id="win-copilot"' in chromed
    assert legacy_palette_classes(chromed.split("<body>", 1)[1]) == []


def test_aeonik_celadon_scoping_and_zero_legacy_dark_classes() -> None:
    html = render_copilot_window_html()

    assert legacy_palette_classes(html) == []
    assert legacy_palette_classes(COPILOT_CSS) == []
    assert legacy_palette_classes(COPILOT_SCRIPT) == []
    for forbidden in ("bg-slate-9", "slate-9", "bg-indigo-9", "bg-black", "text-cyan-3", "bg-gradient-to"):
        assert forbidden not in html
        assert forbidden not in COPILOT_CSS
        assert forbidden not in COPILOT_SCRIPT

    for token in ("#ecf1e6", "#f4f8f0", "#ffffff", "#111111", "#107a47", "#8a1c1c"):
        assert token in html.lower()

    assert "Inter" in COPILOT_CSS
    assert "JetBrains Mono" in COPILOT_CSS
    assert "260px" in COPILOT_CSS
    assert "@media (max-width: 920px)" in COPILOT_CSS
    assert "@container cpbody (max-width: 820px)" in COPILOT_CSS

    # Every CSS selector rule inside COPILOT_CSS must stay strictly scoped under #win-copilot
    for raw_line in COPILOT_CSS.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("/*") or line.startswith("*"):
            continue
        if line.endswith("{") and not line.startswith(("@media", "@container")):
            assert "#win-copilot" in line, f"Unscoped CSS selector in COPILOT_CSS: {line}"


def test_copilot_widgets_gateways_hooks_and_unique_ids() -> None:
    raw_html = render_copilot_window_html()
    html = expand_titlebars(raw_html)

    assert len(PRIORITY_DEFS) == 4
    for label in ("Local Free", "OwlChat", "TEE", "Cloud"):
        assert label in html

    assert len(DEFAULT_GATEWAY_CARDS) == 4
    for gw_text in ("ollama (local)", "FREE · $0.00", "fau-owlchat", "BYOK · HPC", "nanogpt-tee", "openrouter"):
        assert gw_text in html

    for required_id in (
        "win-copilot",
        "copilotHeaderRoute",
        "copilotPrioBtn-local",
        "copilotPrioBtn-owlchat",
        "copilotPrioBtn-tee",
        "copilotPrioBtn-cloud",
        "copilotGatewaysList",
        "copilotContextFiles",
        "copilotAttachDrawer",
        "copilotAttachCtxBtn",
        "copilotArbitrageStats",
        "copilotNewThreadBtn",
        "copilotThreadName",
        "copilotExportMdBtn",
        "copilotActiveStatus",
        "copilotThreadLog",
        "copilotPromptInput",
        "copilotModelSelect",
        "copilotPreflightCost",
        "copilotSendBtn",
    ):
        assert f'id="{required_id}"' in html

    for hook_text in (
        "MODEL ROUTER PRIORITY",
        "ACTIVE GATEWAYS &amp; QUOTAS",
        "SPACE + DRIVE MIRROR CONTEXT",
        "+ Attach .space / Drive Files",
        "SESSION ARBITRAGE TELEMETRY",
        "+ New AI Thread",
        "THREAD:",
        "+ Export .md",
        "Apply Patch to .space",
        "Duel in /arena",
        "Run pytest in .space",
        "Send Message [Enter]",
        "/api/chat",
        "/api/space/notes/propose",
        "/api/space/notes/commit",
        "/api/space/exec",
        "/api/space/ls",
        "/api/drive/ls",
        "win-arena",
    ):
        assert hook_text in html

    assert "cp-meter-track" in html
    assert "cp-meter-fill" in html
    assert "cp-diff-box" in html
    assert "cp-diff-add" in html

    cp_ids = re.findall(r'(?<![\w-])id="([^"]+)"', html)
    assert len(cp_ids) == len(set(cp_ids))

    mesh_counts = Counter(re.findall(r'(?<![\w-])id="([^"]+)"', MESH_OS_HTML_UI))
    # tc-copilot-css and copilotUiScript are only emitted in standalone include_css/include_js mode;
    # when mounted into MESH_OS_HTML_UI via /*TC_COPILOT_CSS*/ and /*TC_COPILOT_JS*/, check DOM widget IDs once.
    dom_ids = [eid for eid in cp_ids if eid not in ("tc-copilot-css", "copilotUiScript")]
    collisions = {eid: mesh_counts[eid] for eid in dom_ids if mesh_counts[eid] != 1}
    assert collisions == {}, f"Expected every #win-copilot ID once in MESH_OS_HTML_UI: {collisions}"
    assert "/*TC_COPILOT_CSS_MOUNTED*/" in MESH_OS_HTML_UI
    assert "/*TC_COPILOT_JS_MOUNTED*/" in MESH_OS_HTML_UI


def test_apply_copilot_ui_marker_replacement_and_idempotency() -> None:
    template = (
        "<!doctype html><html><head>"
        f"<style>{COPILOT_CSS_SLOT}</style>"
        "</head><body>"
        f"<main>{COPILOT_WINDOW_SLOT}</main>"
        f"<script>{COPILOT_JS_SLOT}</script>"
        "</body></html>"
    )
    rendered = apply_copilot_ui(template)
    assert COPILOT_WINDOW_SLOT not in rendered
    assert COPILOT_CSS_SLOT not in rendered
    assert COPILOT_JS_SLOT not in rendered
    assert 'id="win-copilot"' in rendered
    assert "#win-copilot .cp-grid" in rendered
    assert "window.TinCanCopilot" in rendered

    # CSS and JS injected exactly once (not duplicated inside #win-copilot as well)
    assert rendered.count("/* TinCan Copilot & Multi-Model Router") == 1
    assert rendered.count("window.TinCanCopilot = {") == 1

    # Calling apply_copilot_ui twice is strictly idempotent
    assert apply_copilot_ui(rendered) == rendered

    # Also works cleanly when only <!--TC_COPILOT_WINDOW--> is present
    window_only = f"<html><body>{COPILOT_WINDOW_SLOT}</body></html>"
    rendered_standalone = apply_copilot_ui(window_only)
    assert COPILOT_WINDOW_SLOT not in rendered_standalone
    assert 'id="tc-copilot-css"' in rendered_standalone
    assert 'id="copilotUiScript"' in rendered_standalone
    assert apply_copilot_ui(rendered_standalone) == rendered_standalone


def test_copilot_js_syntax_and_vm_runtime() -> None:
    html = render_copilot_window_html()
    script = _extract_inline_script(html)
    assert script.strip() == COPILOT_SCRIPT.strip()

    node = shutil.which("node")
    if node is None:
        return

    check = subprocess.run(
        [node, "--check", "-"],
        input=script,
        text=True,
        capture_output=True,
        check=False,
    )
    assert check.returncode == 0, f"node --check failed: {check.stderr}"

    harness = """
const vm = require('vm');
function makeElem(id) {
  return {
    id,
    value: '',
    textContent: '',
    innerHTML: '',
    disabled: false,
    scrollTop: 0,
    scrollHeight: 100,
    style: {},
    _attrs: {},
    setAttribute(k, v) { this._attrs[k] = String(v); },
    getAttribute(k) { return Object.prototype.hasOwnProperty.call(this._attrs, k) ? this._attrs[k] : null; },
    classList: {
      _set: new Set(id === 'win-copilot' || id === 'win-arena' ? ['hidden'] : []),
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
    focus() {}
  };
}
const elements = new Map();
const document = {
  readyState: 'complete',
  head: makeElem('head'),
  body: makeElem('body'),
  getElementById(id) {
    if (!elements.has(id)) elements.set(id, makeElem(id));
    return elements.get(id);
  },
  createElement(tag) { return makeElem(tag); },
  addEventListener() {}
};
const window = {
  document,
  addEventListener() {},
  toggleWindow(winId) { document.getElementById(winId).classList.remove('hidden'); }
};
const sandbox = {
  window,
  document,
  console,
  setTimeout,
  clearTimeout,
  AbortController,
  MutationObserver: function() { return { observe() {} }; },
  fetch: undefined
};
sandbox.globalThis = sandbox;
const code = require('fs').readFileSync(0, 'utf8');
vm.runInNewContext(code, sandbox);

const api = window.TinCanCopilot;
if (!api || typeof api !== 'object') throw new Error('missing TinCanCopilot');
api.init();

const localEst = api.estimatePreflight('ollama/qwen2.5:3b', 'hello world');
if (localEst.estimated_credits !== 0 || !localEst.is_zero_burn) throw new Error('local preflight should be 0 CR');
const owlEst = api.estimatePreflight('owlchat/llama-3.3-70b', 'hello world');
if (owlEst.estimated_credits !== 0 || !owlEst.is_zero_burn) throw new Error('owlchat preflight should be 0 CR');
const cloudEst = api.estimatePreflight('anthropic/claude-3.7-sonnet', 'hello world');
if (cloudEst.estimated_credits <= 0 || cloudEst.is_zero_burn) throw new Error('cloud preflight should estimate credits');

api.setPriority('owlchat');
if (document.getElementById('copilotHeaderRoute').textContent.indexOf('owlchat') === -1) throw new Error('owlchat header route not updated');
api.setPriority('tee');
api.setPriority('cloud');
api.setPriority('local');
api.toggleAttachDrawer();
api.attachContextFile('/notes/spec.md', 'space');
api.duelInArena('seed-1');
if (document.getElementById('win-arena').classList.contains('hidden')) throw new Error('duelInArena should unhide win-arena');
const md = api.exportMarkdown();
if (md.indexOf('TinCan Copilot Thread') === -1) throw new Error('markdown export failed');
api.newThread();
if (api.getState().turns.length !== 0) throw new Error('newThread should clear turns');

document.getElementById('copilotPromptInput').value = 'Explain direct ollama routing';
Promise.resolve(api.refresh()).then(() => api.sendMessage()).then(() => {
  process.stdout.write('OK:' + api.version);
}).catch((err) => {
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
    assert run.returncode == 0, f"sandbox execution failed: {run.stderr}"
    assert run.stdout.strip() == "OK:1"


def test_copilot_js_mocked_fetch_chat_patch_and_pytest_flow() -> None:
    script = _extract_inline_script(render_copilot_window_html())
    node = shutil.which("node")
    if node is None:
        return

    harness = """
const vm = require('vm');
function makeElem(id) {
  return {
    id, value: '', textContent: '', innerHTML: '', disabled: false,
    scrollTop: 0, scrollHeight: 100, style: {}, _attrs: {},
    setAttribute(k, v) { this._attrs[k] = String(v); },
    getAttribute(k) { return Object.prototype.hasOwnProperty.call(this._attrs, k) ? this._attrs[k] : null; },
    classList: {
      _set: new Set(id === 'win-copilot' ? ['hidden'] : []),
      add(c) { this._set.add(c); },
      remove(c) { this._set.delete(c); },
      toggle(c, force) {
        if (force === undefined) {
          if (this._set.has(c)) this._set.delete(c); else this._set.add(c);
        } else if (force) this._set.add(c); else this._set.delete(c);
      },
      contains(c) { return this._set.has(c); }
    },
    addEventListener() {}, appendChild() {}, removeChild() {}, focus() {}
  };
}
const elements = new Map();
const document = {
  readyState: 'complete',
  head: makeElem('head'),
  body: makeElem('body'),
  getElementById(id) {
    if (!elements.has(id)) elements.set(id, makeElem(id));
    return elements.get(id);
  },
  createElement(tag) { return makeElem(tag); },
  addEventListener() {}
};
const window = { document, addEventListener() {}, toggleWindow() {} };
const calls = [];
async function mockFetch(url, opts) {
  calls.push(url);
  if (url.startsWith('/api/chat')) {
    return {
      ok: true, status: 200,
      async json() {
        return {
          model: 'ollama/qwen2.5:3b',
          thread_id: 'abcd1234ef56',
          cost_usd: 0.0,
          usage: { completion_tokens: 48, total_tokens: 96 },
          choices: [{ message: { role: 'assistant', content: 'Patched cleanly:\\n```diff\\n--- a/src/main.py\\n+++ b/src/main.py\\n@@ -1 +1 @@\\n-old\\n+new\\n```' } }]
        };
      }
    };
  }
  if (url === '/api/space/notes/propose') {
    return { ok: true, status: 200, async json() { return { plan_id: 'plan_01' }; } };
  }
  if (url === '/api/space/notes/commit') {
    return { ok: true, status: 200, async json() { return { version_id: 'ver_01', merkle_root: '99aabbccdd11' }; } };
  }
  if (url === '/api/space/exec') {
    return { ok: true, status: 200, async json() { return { exit_code: 0, stdout: '4 passed in 0.12s' }; } };
  }
  if (url === '/api/models/analytics') {
    return {
      ok: true, status: 200,
      async json() {
        return {
          total_tokens: 96,
          nanogpt: { connected: true, account_remaining_balance_usd: 42.10 },
          openrouter: { connected: true, account_remaining_balance_usd: 128.40 },
          providers: { 'ollama/qwen2.5:3b': { gateway: 'ollama', total_calls: 2 } }
        };
      }
    };
  }
  if (url.startsWith('/api/space/ls')) {
    return { ok: true, status: 200, async json() { return { merkle_root: '99aabbccdd11', files: [{ path: '/tests/test_app.py', size_bytes: 200 }] }; } };
  }
  return { ok: true, status: 200, async json() { return { models: [], files: [] }; } };
}
const sandbox = {
  window, document, console, setTimeout, clearTimeout,
  AbortController, MutationObserver: function() { return { observe() {} }; },
  fetch: mockFetch
};
sandbox.globalThis = sandbox;
vm.runInNewContext(require('fs').readFileSync(0, 'utf8'), sandbox);

const api = window.TinCanCopilot;
api.init();
document.getElementById('copilotPromptInput').value = 'Patch main.py via local ollama';
Promise.resolve()
  .then(() => api.refresh())
  .then(() => api.sendMessage())
  .then(() => api.applyPatch())
  .then(() => api.runPytestInSpace())
  .then(() => {
    const st = api.getState();
    if (st.turns.length !== 1 || !st.turns[0].diffText) throw new Error('expected diff turn');
    if (document.getElementById('copilotGatewaysList').innerHTML.indexOf('$42.10 pool') === -1) throw new Error('missing nanogpt pool');
    if (document.getElementById('copilotGatewaysList').innerHTML.indexOf('$128.40 pool') === -1) throw new Error('missing openrouter pool');
    if (document.getElementById('copilotThreadLog').innerHTML.indexOf('4 passed in 0.12s') === -1) throw new Error('missing pytest output');
    if (document.getElementById('copilotLocalTurns').textContent === '0') throw new Error('local turns should increment');
    process.stdout.write('FLOW_OK:' + calls.length);
  })
  .catch((err) => { console.error(err); process.exit(1); });
"""
    run = subprocess.run(
        [node, "-e", harness],
        input=script,
        text=True,
        capture_output=True,
        check=False,
    )
    assert run.returncode == 0, f"flow execution failed: {run.stderr}"
    assert run.stdout.strip().startswith("FLOW_OK:")
