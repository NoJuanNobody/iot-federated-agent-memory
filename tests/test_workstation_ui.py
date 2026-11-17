"""Unit tests for iot_federated_agent_memory.workstation_ui."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys

WORKTREE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKTREE_DIR not in sys.path:
    sys.path.insert(0, WORKTREE_DIR)

from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI  # noqa: E402
from iot_federated_agent_memory.window_chrome import (  # noqa: E402
    apply_window_chrome,
    expand_titlebars,
    legacy_palette_classes,
)
from iot_federated_agent_memory.workstation_ui import (  # noqa: E402
    COST_CAP_OPTIONS,
    FALLBACK_MODELS,
    GATEWAY_DEFS,
    MODE_DEFS,
    RODIN_TIERS,
    render_workstation_window_html,
)


def _extract_inline_script(html: str) -> str:
    m = re.search(
        r'<script\s+id="workstationUiScript"[^>]*>(.*?)</script>',
        html,
        flags=re.DOTALL,
    )
    assert m, "workstationUiScript block must exist inside render_workstation_window_html()"
    return m.group(1)


def test_render_workstation_window_root_and_titlebar_marker() -> None:
    html = render_workstation_window_html()
    assert isinstance(html, str)
    expected_root = (
        '<div id="win-workstation" class="mesh-window w-[1080px] max-w-full hidden tc-ws-host" '
        'data-zen-window="true" data-window-id="win-workstation" '
        'style="top: 72px; left: 110px; z-index: 36;">'
    )
    assert html.startswith(expected_root)
    assert html.rstrip().endswith("</div>")

    after_root = html[len(expected_root) :].lstrip()
    expected_titlebar = (
        '<!--TC_TITLEBAR {"id": "win-workstation", '
        '"title": "3D Studio", '
        '"badge": "RODIN + NANOGPT"}-->'
    )
    assert after_root.startswith(expected_titlebar)

    assert "Dock in Workstation" in html
    assert 'id="wsTileSpaceBtn"' in html
    assert 'id="wsMerkleBadge"' in html
    assert 'id="wsSpaceScopeBadge"' in html
    assert 'id="wsRefreshBtn"' in html


def test_aeonik_celadon_palette_and_zero_legacy_dark_slate() -> None:
    html = render_workstation_window_html()

    assert legacy_palette_classes(html) == []
    for forbidden in ("bg-slate-9", "text-cyan-3", "bg-cyan-9", "slate-8"):
        assert forbidden not in html

    for token in ("#ecf1e6", "#f4f8f0", "#ffffff", "#111111", "#107a47", "#8a1c1c"):
        assert token in html.lower()

    assert "9999px" in html
    assert "310px" in html
    assert "@media (max-width: 980px)" in html


def test_unique_element_ids_and_no_mesh_os_collisions() -> None:
    from collections import Counter

    html = render_workstation_window_html()
    ws_ids = re.findall(r'(?<![\w-])id="([^"]+)"', html)
    assert len(ws_ids) >= 50
    assert len(ws_ids) == len(set(ws_ids))

    mesh_counts = Counter(re.findall(r'(?<![\w-])id="([^"]+)"', MESH_OS_HTML_UI))
    duplicates = [eid for eid in ws_ids if mesh_counts[eid] != 1]
    assert duplicates == []


def test_left_pane_gateways_context_and_guardrails() -> None:
    html = render_workstation_window_html()

    assert len(GATEWAY_DEFS) == 3
    for gw_label in ("TEE Private", "Heretic", "OpenRouter"):
        assert gw_label in html
    for badge in ("ATTESTED", "UNCENSORED", "POOLED"):
        assert badge in html

    for fallback_key in ("tee", "heretic", "openrouter"):
        assert FALLBACK_MODELS[fallback_key]

    for elem_id in (
        "wsGwBtn-tee",
        "wsGwBtn-heretic",
        "wsGwBtn-openrouter",
        "wsModelSelect",
        "wsActiveModelCard",
        "wsActiveModelName",
        "wsActiveModelBadge",
        "wsActiveModelId",
        "wsActiveModelCtx",
        "wsActiveModelPrice",
        "wsSelectedCtxPath",
        "wsContextList",
        "wsEnclaveGuardToggle",
        "wsDirectiveInput",
        "wsMaxCostSelect",
        "wsDispatchBtn",
    ):
        assert f'id="{elem_id}"' in html

    for endpoint in ("/api/models/nanogpt", "/api/models/openrouter", "/api/space/ls", "/api/drive/ls", "/api/space/file"):
        assert endpoint in html

    for cap in ("$0.25", "$0.50", "$0.75", "$1.00", "$1.50"):
        assert cap in html
    assert list(COST_CAP_OPTIONS) == [0.25, 0.50, 0.75, 1.00, 1.50]
    assert "Dispatch Run" in html


def test_center_pane_modes_rodin_audit_arena_and_patch_preview() -> None:
    html = render_workstation_window_html()

    assert len(MODE_DEFS) == 3
    for mode_label in ("3D Rodin Stage", "TEE Audit &amp; Diff", "Arena Benchmark"):
        assert mode_label in html
    assert 'id="wsOutputTargetTag"' in html

    assert len(RODIN_TIERS) == 4
    for tier_name, tier_price in (("Sketch", "$0.25"), ("Regular", "$0.50"), ("Smooth", "$0.75"), ("Detail", "$1.00")):
        assert tier_name in html
        assert tier_price in html
        assert f'id="wsTierBtn-{tier_name}"' in html

    assert "ws3dControlCard" in html
    assert "3D Dispatch &amp; Route Control" in html
    assert 'id="wsOpenInWorkstationBtn"' in html
    assert "Open in ArtCraft" in html
    assert "Save to .space" in html
    assert "/api/3d/generate" in html
    assert "/api/artcraft/open" in html

    for audit_marker in (
        "/api/space/notes",
        "/api/space/notes/propose",
        "/api/space/notes/commit",
        "/api/space/notes/revert",
        "Commit Patch",
        "Revert Last",
        "ws-diff-add",
        "ws-diff-del",
        'id="wsAuditDiffBox"',
    ):
        assert audit_marker in html

    for arena_marker in (
        "/api/mesh/arena/match",
        "/api/chat",
        "/api/mesh/arena/vote",
        "+150 XP",
        'id="wsArenaModelA"',
        'id="wsArenaModelB"',
    ):
        assert arena_marker in html

    for preview_id in (
        "wsPatchPreviewFrame",
        "wsNotesCountBadge",
        "wsPlanIdBadge",
        "wsPreviewRefreshBtn",
        "wsPreviewCommitBtn",
        "wsPreviewRevertBtn",
        "wsPatchPreviewDiff",
    ):
        assert f'id="{preview_id}"' in html


def test_right_pane_telemetry_queue_and_mesh_handoff() -> None:
    html = render_workstation_window_html()

    from iot_federated_agent_memory.token_vault_ui import render_token_vault_window_html
    tv_html = render_token_vault_window_html()
    assert "Hyper3D Rodin &amp; NanoGPT Compute Pools" in tv_html
    assert 'id="rodinBalanceCredits"' in tv_html
    assert 'id="tvNanoPoolVal"' in tv_html

    assert 'id="wsTokensPoolsBtn"' in html
    assert "/api/workstation/status" in html
    assert "Workstation Job Queue" in html
    assert "Attestation &amp; Cost Trace" in html
    assert "Staged Outputs -&gt; .space" in html
    assert "Space &amp; Mesh Handoff" in html
    assert "Commit Patch &amp; .glb to TinCan Space" in html
    assert "Post to @board · WebRTC Review" in html
    assert "/api/board/topics" in html
    assert "win-comms" in html
    assert "win-board" in html

    for elem_id in (
        "wsTokensPoolsBtn",
        "wsJobQueueList",
        "wsTraceCard",
        "wsTraceSpend",
        "wsTracePrivacy",
        "wsTraceMerkle",
        "wsStagedList",
        "wsHandoffCommitBtn",
        "wsHandoffBoardBtn",
    ):
        assert f'id="{elem_id}"' in html


def test_window_chrome_expands_tc_titlebar_and_applies_celadon() -> None:
    html = render_workstation_window_html()

    expanded = expand_titlebars(html)
    assert "<!--TC_TITLEBAR" not in expanded
    assert 'class="window-header tc-titlebar"' in expanded
    assert 'data-tc-titlebar="win-workstation"' in expanded
    assert '<span class="window-title tc-titlebar__title" title="3D Studio">3D Studio</span>' in expanded
    assert "RODIN + NANOGPT" in expanded
    assert legacy_palette_classes(expanded) == []

    page = f"<!doctype html><html><head></head><body>{html}</body></html>"
    chromed = apply_window_chrome(page)
    assert "<!--TC_TITLEBAR" not in chromed
    assert 'id="tc-celadon"' in chromed
    assert 'id="win-workstation"' in chromed
    assert 'data-zen-window="true"' in chromed
    body_html = chromed.split("<body>", 1)[1]
    assert legacy_palette_classes(body_html) == []


def test_workstation_js_api_syntax_and_partial_global_safety() -> None:
    html = render_workstation_window_html()
    script = _extract_inline_script(html)

    for symbol in (
        "window.TinCanWorkstation",
        "init",
        "refresh",
        "openWithContext",
        "switchGateway",
        "switchMode",
        "tileWithSpace",
        "dispatch",
        "MutationObserver",
        "AbortController",
    ):
        assert symbol in script

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

    # Verify script attaches and guards missing DOM/mesh globals cleanly.
    harness = """
const vm = require('vm');
function makeElem(id) {
  return {
    id,
    value: '',
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
  location: { search: '' }
};
const sandbox = {
  window,
  document,
  console,
  setTimeout,
  clearTimeout,
  AbortController,
  MutationObserver: function() { return { observe() {} }; },
  fetch: undefined,
  URLSearchParams
};
sandbox.globalThis = sandbox;
const code = require('fs').readFileSync(0, 'utf8');
vm.runInNewContext(code, sandbox);
const api = window.TinCanWorkstation;
if (!api || typeof api !== 'object') throw new Error('missing TinCanWorkstation');
for (const fn of ['init', 'refresh', 'openWithContext', 'switchGateway', 'switchMode', 'tileWithSpace', 'dispatch']) {
  if (typeof api[fn] !== 'function') throw new Error('missing method: ' + fn);
}
api.init();
api.switchGateway('heretic');
api.switchGateway('openrouter');
api.switchGateway('tee');
api.switchMode('audit');
api.switchMode('arena');
api.switchMode('3d');
api.openWithContext('/notes/hello.md');
api.tileWithSpace();
Promise.resolve(api.refresh()).then(() => api.dispatch()).then(() => {
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


def test_mesh_os_html_ui_wires_workstation_and_space_tiling() -> None:
    assert "<!--TC_WORKSTATION_WINDOW-->" not in MESH_OS_HTML_UI
    assert "<!--TC_TITLEBAR" not in MESH_OS_HTML_UI
    assert 'id="win-workstation"' in MESH_OS_HTML_UI
    ws_idx = MESH_OS_HTML_UI.find('id="win-workstation"')
    assert 'data-zen-window="true"' in MESH_OS_HTML_UI[ws_idx : ws_idx + 180]
    assert 'id="dockBtn-win-workstation"' in MESH_OS_HTML_UI
    assert 'id="spaceOpenWorkstationBtn"' in MESH_OS_HTML_UI
    assert "'win-agentspace', 'win-workstation'" in MESH_OS_HTML_UI
    assert "window.location.pathname === '/3dstudio'" in MESH_OS_HTML_UI
    assert "'/workstation'" in MESH_OS_HTML_UI and "singleWindowParam = 'win-agentspace'" in MESH_OS_HTML_UI
    assert "singleWindowParam = 'win-workstation'" in MESH_OS_HTML_UI
    assert "toggleDock3dStudio" in MESH_OS_HTML_UI and 'id="finderTab-3dstudio"' in MESH_OS_HTML_UI
    assert '<span class="window-title tc-titlebar__title" title="3D Studio">3D Studio</span>' in MESH_OS_HTML_UI


def test_mesh_os_html_ui_workstation_window_has_zero_legacy_palette_classes() -> None:
    ws_idx = MESH_OS_HTML_UI.find('id="win-workstation"')
    main_end = MESH_OS_HTML_UI.find("</main>", ws_idx)
    assert ws_idx != -1 and main_end > ws_idx
    workstation_slice = MESH_OS_HTML_UI[ws_idx:main_end]
    assert legacy_palette_classes(workstation_slice) == []


def test_workstation_three_way_route_sync() -> None:
    import server as srv
    from iot_federated_agent_memory.designs_gallery import DESKTOP_MOCKUPS

    assert "/workstation" in srv.SINGLE_WINDOW_ROUTES
    assert "/3dstudio" in srv.SINGLE_WINDOW_ROUTES
    assert "'/workstation'" in MESH_OS_HTML_UI
    assert "'/3dstudio'" in MESH_OS_HTML_UI
    assert "tool: 'win-agentspace'" in MESH_OS_HTML_UI
    assert "tool: 'win-workstation'" in MESH_OS_HTML_UI
    assert "window.location.pathname === '/3dstudio'" in MESH_OS_HTML_UI
    assert "singleWindowParam = 'win-workstation'" in MESH_OS_HTML_UI
    assert "singleWindowParam = 'win-agentspace'" in MESH_OS_HTML_UI
    mockup_ids = {m["id"] for m in DESKTOP_MOCKUPS}
    assert {"ws-studio", "ws-stories", "ws-dual"}.issubset(mockup_ids)
