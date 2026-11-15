"""The two-brain duel and its context panel render in every arena view."""

import collections
import gzip
import re
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

import server
from iot_federated_agent_memory.arena_duel_ui import ARENA_DUEL_SCRIPT, ARENA_VIEWS, render_arena_duel
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI
from iot_federated_agent_memory.window_chrome import legacy_palette_classes


@pytest.fixture(scope="module")
def base():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.MeshGatewayHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def _window(html, win_id):
    start = html.index(f'<div id="{win_id}" class="mesh-window')
    nxt = html.find('class="mesh-window', start + 40)
    return html[start: nxt if nxt != -1 else len(html)]


BRAIN_PANEL_IDS = ("Slot{s}", "Result{s}", "Model{s}Input", "Agent{s}", "Used{s}", "Files{s}", "Upload{s}",
                   "PasteText{s}", "VoteBtn{s}", "UseCtx{s}")


def test_arena_route_shows_both_brain_slots(base):
    req = urllib.request.Request(base + "/arena", headers={"Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        body = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)
    html = body.decode("utf-8")
    # /arena opens win-arena in single-window mode ...
    assert "window.location.pathname === '/arena') singleWindowParam = 'win-arena'" in html
    # ... and win-arena now holds the duel with both brain slots and their context panels.
    win = _window(html, "win-arena")
    assert 'id="arenaWinBattleBox"' in win
    for side in "AB":
        for pat in BRAIN_PANEL_IDS:
            assert f'id="arenaWin{pat.format(s=side)}"' in win, pat.format(s=side)
        assert f'data-arena-slot="{side}"' in win
    assert 'id="arenaWinPromptInput"' in win and "arenaDuelRun('arenaWin')" in win


def test_quests_window_keeps_its_duel():
    win = _window(MESH_OS_HTML_UI, "win-quests")
    assert 'id="arenaBattleBox"' in win
    for side in "AB":
        for pat in BRAIN_PANEL_IDS:
            assert f'id="arena{pat.format(s=side)}"' in win
    assert 'id="arenaWinBattleBox"' not in win


def test_no_duplicate_ids_across_arena_views():
    ids = re.findall(r'\bid="([^"]+)"', MESH_OS_HTML_UI)
    counts = collections.Counter(ids)
    arena_ids = [i for i in counts if i.startswith("arena")]
    assert len(arena_ids) > 40
    dupes = [i for i in arena_ids if counts[i] > 1]
    assert dupes == []
    assert "<!--ARENA_DUEL:" not in MESH_OS_HTML_UI


def test_single_shared_script_and_legacy_entry_points():
    assert MESH_OS_HTML_UI.count('id="arenaDuelScript"') == 1
    script = MESH_OS_HTML_UI[MESH_OS_HTML_UI.index('id="arenaDuelScript"'):]
    assert 'const VIEWS = ["arenaWin", "arena"]' in script
    for fn in ("window.runArenaBattle", "window.voteArenaWinner", "window.updateArenaModelLabels",
               "window.sendArenaResultToSpace", "window.onArenaModelChange", "window.swapArenaModels",
               "window.loadArenaModels", "/api/mesh/arena/match", "/api/mesh/arena/models",
               "/api/mesh/arena/vote", "tincan_arena_models", "/api/arena/context/ingest",
               "/api/arena/context/import", "/api/arena/context/drive/link"):
        assert fn in script
    # Identity is the session cookie; a client peer header is never sent as a credential.
    assert "'X-TinCan-Peer'" not in script and "/api/arena/duel" not in script
    assert "arena: true" in script and "match_id" in script and "arena_side" in script and "agent_id" in script
    # The old inline duel is gone; one shared implementation serves both views.
    assert "async function runArenaBattle" not in MESH_OS_HTML_UI
    assert "body: JSON.stringify({ model: 'gemini-brain', prompt })" not in MESH_OS_HTML_UI


def test_launcher_and_dock_open_the_window_with_the_duel():
    assert "{ id: 'win-arena', name: 'Arena'" in MESH_OS_HTML_UI
    assert "toggleWindow('win-arena')" in MESH_OS_HTML_UI
    assert set(p for p, _w, _l in ARENA_VIEWS) == {"arenaWin", "arena"}


def test_render_is_prefix_scoped():
    a, b = render_arena_duel("x1"), render_arena_duel("y2")
    ids_a = set(re.findall(r'\bid="([^"]+)"', a))
    ids_b = set(re.findall(r'\bid="([^"]+)"', b))
    assert ids_a and not (ids_a & ids_b)
    assert all(i.startswith("x1") for i in ids_a)


@pytest.mark.parametrize("route", ["/arena", "/quests", "/rewards"])
def test_arena_view_routes_are_served(base, route):
    with urllib.request.urlopen(base + route) as resp:
        assert resp.status == 200
        html = resp.read().decode("utf-8")
    assert 'id="arenaWinBattleBox"' in html and 'id="arenaBattleBox"' in html


def test_celadon_surfaces_and_zero_legacy_palette_classes():
    rendered = render_arena_duel("arena", "Quests")
    assert legacy_palette_classes(rendered) == []
    assert legacy_palette_classes(ARENA_DUEL_SCRIPT) == []
    combined = rendered + ARENA_DUEL_SCRIPT
    for forbidden in ("bg-slate-900", "bg-slate-950", "from-indigo-600", "to-cyan-600", "text-slate-200"):
        assert forbidden not in combined
    for token in ("#ecf1e6", "#f4f8f0", "#ffffff", "#111111", "#107a47", "#8a1c1c"):
        assert token in combined


def test_local_vs_cloud_preset_rag_cap_savings_and_pro_strip():
    for prefix, win_id in (("arenaWin", "win-arena"), ("arena", "win-quests")):
        win = _window(MESH_OS_HTML_UI, win_id)
        assert f'id="{prefix}PresetLocalCloudBtn"' in win
        assert f"arenaPresetLocalVsCloud('{prefix}')" in win
        assert f'id="{prefix}RagBadge"' in win
        assert f'id="{prefix}PreAuthCap"' in win
        assert f'id="{prefix}ProStrip"' in win
        assert "AD-SUPPORTED AI CREDITS" in win
        assert "Watch Home Screen Ads" in win
        assert "zenWatchHomeAd" in win
        assert "toggleWindow('win-ai-home')" in win
        assert "Run Arena" in win
        for side in "AB":
            assert f'id="{prefix}Savings{side}"' in win
            assert f'id="{prefix}TierTag{side}"' in win

    custom = render_arena_duel("customArena")
    custom_ids = set(re.findall(r'\bid="([^"]+)"', custom))
    expected_new_ids = {
        "customArenaPresetLocalCloudBtn",
        "customArenaPresetStatus",
        "customArenaRagBadge",
        "customArenaPreAuthCap",
        "customArenaSavingsA",
        "customArenaSavingsB",
        "customArenaTierTagA",
        "customArenaTierTagB",
        "customArenaProStrip",
        "customArenaProTelemetryTitle",
        "customArenaProTelemetrySub",
        "customArenaUpgradeProBtn",
    }
    assert expected_new_ids <= custom_ids
    assert all(eid.startswith("customArena") for eid in custom_ids)


def test_arena_preset_preauth_and_zero_burn_savings_js():
    import json
    import shutil
    import subprocess

    node_bin = shutil.which("node")
    assert node_bin, "node binary required to test arena_duel_ui JS logic"
    m = re.search(r'<script id="arenaDuelScript">(.*?)</script>', MESH_OS_HTML_UI, flags=re.DOTALL)
    assert m, "arenaDuelScript must exist in MESH_OS_HTML_UI"
    script_body = m.group(1)

    harness = r"""
const store = {};
const elements = {};
function makeEl(id, extra) {
  const el = Object.assign({
    id,
    value: '',
    textContent: '',
    innerHTML: '',
    className: '',
    checked: true,
    disabled: false,
    classList: {
      toggle() {},
      add() {},
      remove() {},
    },
    querySelectorAll() { return []; },
  }, extra || {});
  elements[id] = el;
  return el;
}
for (const p of ['arenaWin', 'arena']) {
  makeEl(p + 'BattleBox');
  makeEl(p + 'Account');
  makeEl(p + 'RagBadge');
  makeEl(p + 'PreAuthCap');
  makeEl(p + 'PresetStatus');
  makeEl(p + 'ModelsNote');
  makeEl(p + 'PromptInput', { value: 'Summarize what my files say about deploying TinCan.' });
  makeEl(p + 'ModelAInput', { value: 'gemini-brain', options: [{ value: 'gemini-brain' }, { value: 'claude-brain' }, { value: 'ollama/qwen2.5:3b' }] });
  makeEl(p + 'ModelBInput', { value: 'claude-brain', options: [{ value: 'gemini-brain' }, { value: 'claude-brain' }, { value: 'ollama/qwen2.5:3b' }] });
  makeEl(p + 'ProTelemetryTitle');
  for (const s of ['A', 'B']) {
    makeEl(p + 'Label' + s);
    makeEl(p + 'TierTag' + s);
    makeEl(p + 'Bill' + s);
    makeEl(p + 'Result' + s);
    makeEl(p + 'Savings' + s);
    makeEl(p + 'Agent' + s, { value: 'brain-' + s.toLowerCase() });
    makeEl(p + 'UseCtx' + s, { checked: true });
    makeEl(p + 'Files' + s);
    makeEl(p + 'CtxMsg' + s);
    makeEl(p + 'DriveBtn' + s);
  }
}

global.window = global;
global.localStorage = {
  getItem(k) { return Object.prototype.hasOwnProperty.call(store, k) ? store[k] : null; },
  setItem(k, v) { store[k] = String(v); },
};
global.document = {
  readyState: 'complete',
  getElementById(id) { return elements[id] || null; },
};
global.fetch = async (url) => {
  if (url === '/api/mesh/arena/models') {
    return {
      ok: true,
      status: 200,
      async json() {
        return {
          models: [
            { id: 'gemini-brain', name: 'Google Gemini Flash', secondary: 'google/gemini-2.5-flash', provider: 'google', kind: 'configured' },
            { id: 'claude-brain', name: 'Anthropic Claude Sonnet', secondary: 'anthropic/claude-sonnet-5.5', provider: 'anthropic', kind: 'configured' },
            { id: 'ollama/qwen2.5:3b', name: 'qwen2.5:3b', secondary: 'ollama/qwen2.5:3b', provider: 'Ollama (Local)', gateway: 'ollama', kind: 'catalog' },
          ],
          default: { a: 'gemini-brain', b: 'claude-brain' },
        };
      },
    };
  }
  if (url === '/api/arena/context/status') {
    return {
      ok: true,
      status: 200,
      async json() {
        return {
          account: { peer_id: 'acct-1', username: 'alice', token_balance: 300 },
          drive_mirror: { allowed_here: false },
        };
      },
    };
  }
  if (String(url).startsWith('/api/arena/context/files')) {
    const isA = String(url).includes('agent_id=brain-a');
    return {
      ok: true,
      status: 200,
      async json() {
        return isA
          ? { files: [{ path: '/uploads/relay.py', source: 'upload', chunk_count: 2 }], count: 1, chunk_count: 2 }
          : { files: [], count: 0, chunk_count: 0 };
      },
    };
  }
  return { ok: true, status: 200, async json() { return {}; } };
};
""" + script_body + r"""
(async () => {
  await new Promise((r) => setTimeout(r, 30));
  const pair = window.arenaPresetLocalVsCloud('arenaWin');
  window.arenaUpdatePreAuthCap('arenaWin');
  window.arenaRenderSavings('arenaWin', {
    A: { cost: 0, tokens: 312, ttft: 0.42, model: 'ollama/qwen2.5:3b' },
    B: { cost: 0.018, tokens: 684, ttft: 1.14, model: 'claude-brain' },
  });
  process.stdout.write(JSON.stringify({
    pair,
    winA: elements['arenaWinModelAInput'].value,
    winB: elements['arenaWinModelBInput'].value,
    questA: elements['arenaModelAInput'].value,
    questB: elements['arenaModelBInput'].value,
    tierA: elements['arenaWinTierTagA'].textContent,
    tierACls: elements['arenaWinTierTagA'].className,
    tierB: elements['arenaWinTierTagB'].textContent,
    presetStatus: elements['arenaWinPresetStatus'].textContent,
    preAuthText: elements['arenaWinPreAuthCap'].textContent,
    preAuthCls: elements['arenaWinPreAuthCap'].className,
    ragBadge: elements['arenaWinRagBadge'].textContent,
    savingsA: elements['arenaWinSavingsA'].textContent,
    savingsACls: elements['arenaWinSavingsA'].className,
    savingsB: elements['arenaWinSavingsB'].textContent,
    savingsBCls: elements['arenaWinSavingsB'].className,
    proTitle: elements['arenaWinProTelemetryTitle'].textContent,
  }));
})();
"""
    proc = subprocess.run([node_bin, "-e", harness], capture_output=True, text=True, check=True)
    out = json.loads(proc.stdout)
    assert out["pair"] == {"a": "ollama/qwen2.5:3b", "b": "claude-brain"}
    assert out["winA"] == "ollama/qwen2.5:3b" and out["questA"] == "ollama/qwen2.5:3b"
    assert out["winB"] == "claude-brain" and out["questB"] == "claude-brain"
    assert out["tierA"] == "LOCAL" and "#107a47" in out["tierACls"]
    assert out["tierB"] == "CLOUD"
    assert "ollama/qwen2.5:3b" in out["presetStatus"]
    assert "533" in out["preAuthText"] and "LOW BAL (300)" in out["preAuthText"]
    assert "#8a1c1c" in out["preAuthCls"]
    assert "/uploads/relay.py" in out["ragBadge"]
    assert "ZERO-BURN FREE" in out["savingsA"] and "0.018000" in out["savingsA"] and "#107a47" in out["savingsACls"]
    assert "CLOUD BILLED" in out["savingsB"] and "#8a1c1c" in out["savingsBCls"]
    assert "AD-SUPPORTED CREDITS: ZERO-BURN SAVED 100% VS CLOUD" in out["proTitle"]
