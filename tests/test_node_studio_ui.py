"""Unit and JS runtime tests for the 1:1 Nano Banana Gemini Node Studio UI."""

from __future__ import annotations

from collections import Counter
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

WORKTREE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKTREE_DIR not in sys.path:
    sys.path.insert(0, WORKTREE_DIR)

from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI  # noqa: E402
from iot_federated_agent_memory.node_studio_ui import (  # noqa: E402
    AEONIK_PALETTE,
    AVAILABLE_MODELS,
    FILTER_PRESETS,
    LUMINA_ASSETS,
    LUMINA_TEMPLATES,
    MODEL_CAPABILITIES,
    PANORAMIC_ASPECT_RATIOS,
    STANDARD_ASPECT_RATIOS,
    render_node_studio_html,
    render_node_studio_window_html,
)
from iot_federated_agent_memory.window_chrome import (  # noqa: E402
    apply_window_chrome,
    celadonize_classes,
    expand_titlebars,
    legacy_palette_classes,
)


def _extract_inline_script(html: str) -> str:
    m = re.search(
        r'<script\s+id="nodeStudioUiScript"[^>]*>(.*?)</script>',
        html,
        flags=re.DOTALL,
    )
    assert m, "nodeStudioUiScript block must exist"
    return m.group(1)


def test_aeonik_celadon_compliance_and_no_four_quadrant_table() -> None:
    html = render_node_studio_html()
    assert html.startswith("<!doctype html>")
    assert legacy_palette_classes(html) == []
    assert celadonize_classes(html) == html
    for forbidden in ("bg-slate-", "text-cyan-", "bg-cyan-", "bg-emerald-", "bg-zinc-", "bg-gradient-to-"):
        assert forbidden not in html
    for hex_token in ("#ecf1e6", "#f4f8f0", "#ffffff", "#111111", "#4a4a4a", "#5c5c5c", "#107a47"):
        assert hex_token in html.lower()
    assert set(AEONIK_PALETTE.values()) >= {"#ecf1e6", "#f4f8f0", "#ffffff", "#111111", "#107a47"}

    # Must be full-screen infinite dot-grid canvas, NOT the scrapped 4-quadrant layout
    assert "24px 24px" in html
    assert "radial-gradient(" in html
    assert "ns-quad-grid" not in html
    assert "NODE GRAPH · DAG &amp; SERIAL FILTER CHAIN" not in html


def test_top_switcher_hud_left_panel_and_zoom_controls() -> None:
    html = render_node_studio_html()

    # Top-Center Floating View Switcher
    for tab in ("Editor", "Chat", "Library"):
        assert tab in html

    # Empty Canvas State & Drop Overlay
    assert "Canvas Empty" in html
    assert "Use the toolbar below to generate or drag &amp; drop images" in html
    assert "Drop images here" in html

    # Top-Right Floating HUD & Keyboard Shortcuts
    for hud_tok in (
        "⌘/Ctrl held - click node to duplicate",
        "Auto-Layout",
        "[A]",
        "Keys",
        "[i]",
        "Keyboard Shortcuts",
        "Delete / Backspace",
        "⌘/Ctrl + A",
        "Fit view",
        "Invert image selection",
    ):
        assert hud_tok in html

    # Left-Center Floating Pill <-> Lumina Library Drawer
    for left_tok in (
        "nsLeftPillWrap",
        "nsLeftDrawer",
        "Lumina Library",
        "References",
        "DROP OR CLICK",
        "3D Assets",
        "Search assets...",
        "Prompts",
        "Cyberpunk Street",
        "Ethereal Portrait",
        "Isometric Gamer Room",
        "Abstract Geometric",
        "Forest Cabin",
        "New Template",
        "SYNCED",
        "Storage: 24%",
        "Asset_Pack_1",
        "Asset_Pack_15",
    ):
        assert left_tok in html

    # Bottom-Left Zoom Controls
    for zoom_id in ("nsZoomInBtn", "nsZoomOutBtn", "nsFitViewBtn"):
        assert f'id="{zoom_id}"' in html


def test_prompt_island_models_capabilities_and_api_config() -> None:
    html = render_node_studio_html()

    for tok in (
        "max-width: 920px",
        "GENERATE MODE",
        "In Conversation",
        "Branching from image",
        "API Configuration",
        "Gemini: Not Set",
        "NanoGPT: Not Set",
        "Custom Gemini Key (optional)",
        "Custom NanoGPT Key (optional)",
        "Select Model",
        "Nano Banana 2.1",
        "Nano Banana Pro",
        "Nano Banana 2",
        "Nano Banana 2 Lite",
        "Describe what you want to generate...",
        "ASPECT",
        "RES",
        "THINK",
        "THOUGHTS",
        "SEARCH",
        "VIA",
        "0/14 refs (Img/Vid/PDF)",
        "0/2",
        "Generate →",
        "/api/nodes/generate",
        "/api/generate",
        "/api/nodes/health",
    ):
        assert tok in html

    for ratio in STANDARD_ASPECT_RATIOS + PANORAMIC_ASPECT_RATIOS:
        assert f'value="{ratio}"' in html

    assert len(AVAILABLE_MODELS) == 4
    assert set(MODEL_CAPABILITIES.keys()) >= {
        "gemini-nano-banana-2.1",
        "gemini-3-pro-image",
        "gemini-3.1-flash-image",
        "gemini-3.1-flash-lite-image",
    }
    assert len(FILTER_PRESETS) == 5
    assert len(LUMINA_TEMPLATES) == 5
    assert len(LUMINA_ASSETS) == 15


def test_render_node_studio_views_and_window_chrome_integration() -> None:
    chat_html = render_node_studio_html(active_view="chat")
    assert 'id="nsConversationView" class="ns-alt-view"' in chat_html
    assert "Conversation Editor" in chat_html

    lib_html = render_node_studio_html(active_view="library")
    assert 'id="nsLibraryView" class="ns-alt-view"' in lib_html
    assert "Asset Library" in lib_html

    win_html = render_node_studio_window_html()
    assert win_html.startswith('<div id="win-nodes" class="mesh-window')
    assert (
        '<!--TC_TITLEBAR {"id": "win-nodes", "title": "Node Studio · Prompt Island, Timeline & Filter Graph", "badge": "NANOGPT + GEMINI"}-->'
        in win_html
    )
    assert legacy_palette_classes(win_html) == []
    assert celadonize_classes(win_html) == win_html

    ns_ids = re.findall(r'(?<![\w-])id="([^"]+)"', win_html)
    assert len(ns_ids) >= 40
    assert len(ns_ids) == len(set(ns_ids))

    mesh_counts = Counter(re.findall(r'(?<![\w-])id="([^"]+)"', MESH_OS_HTML_UI))
    duplicates = [eid for eid in ns_ids if mesh_counts[eid] != 1]
    assert duplicates == []

    expanded = expand_titlebars(win_html)
    assert "<!--TC_TITLEBAR" not in expanded
    assert "NANOGPT + GEMINI" in expanded

    page = f"<!doctype html><html><head></head><body>{win_html}</body></html>"
    chromed = apply_window_chrome(page)
    assert 'id="tc-celadon"' in chromed
    assert "<!--TC_TITLEBAR" not in chromed
    assert apply_window_chrome(chromed) == chromed


def test_inline_js_syntax_and_studio_interactions_in_node() -> None:
    node_bin = shutil.which("node")
    if not node_bin:
        pytest.skip("node binary not available for JS check")

    html = render_node_studio_html()
    script = _extract_inline_script(html)

    proc = subprocess.run(
        [node_bin, "--check"],
        input=script,
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, f"JS syntax error: {proc.stderr}"

    harness = f"""
const elements = new Map();
function makeEl(id) {{
  const el = {{
    id,
    textContent: "",
    innerHTML: "",
    value: "",
    placeholder: "",
    disabled: false,
    dataset: {{}},
    style: {{}},
    attributes: {{}},
    scrollHeight: 50,
    _classes: new Set(),
    classList: {{
      toggle(c, force) {{
        if (force === undefined) {{
          if (el._classes.has(c)) {{ el._classes.delete(c); return false; }}
          el._classes.add(c); return true;
        }}
        if (force) el._classes.add(c); else el._classes.delete(c);
        return !!force;
      }},
      add(c) {{ el._classes.add(c); }},
      remove(c) {{ el._classes.delete(c); }},
      contains(c) {{ return el._classes.has(c); }}
    }},
    setAttribute(k, v) {{ el.attributes[k] = String(v); }},
    addEventListener() {{}},
    querySelectorAll() {{ return []; }},
    focus() {{}},
    getBoundingClientRect() {{ return {{ left: 0, top: 0, width: 1200, height: 800 }}; }}
  }};
  return el;
}}
[
  "nsDotCanvas", "nsEmptyState", "nsCanvasWorld", "nsEdgesSvg", "nsNodesLayer",
  "nsSelectionBox", "nsDropOverlay", "nsConversationView", "nsLibraryView",
  "nsLibraryViewGrid", "nsCopyIndicator", "nsAutoLayoutBtn", "nsShortcutsBtn",
  "nsShortcutsPopover", "nsLeftPillWrap", "nsLeftDrawer", "nsAssetSearchInput",
  "nsLibAssetGrid", "nsLibTemplateList", "nsNewTemplateBtn", "nsModePill",
  "nsConvPill", "nsBranchPill", "nsApiBtn", "nsApiMenu", "nsApiGeminiStatus",
  "nsApiNanogptStatus", "nsApiSourceText", "nsApiClearBtn", "nsGeminiKeyInput",
  "nsNanogptKeyInput", "nsModelBtn", "nsModelBtnLabel", "nsModelMenu",
  "nsRefsStrip", "nsRefsRow", "nsPromptInput", "nsAttachTrigger", "nsFileInput",
  "nsAspectSelect", "nsAspectVal", "nsResWrap", "nsResSelect", "nsResVal",
  "nsThinkWrap", "nsThinkSelect", "nsThinkVal", "nsThoughtsBtn",
  "nsSearchWrap", "nsSearchSelect", "nsSearchVal", "nsViaVal", "nsRefCounter",
  "nsActiveRunsCount", "nsGenerateBtn", "nsResponseToast"
].forEach((id) => elements.set(id, makeEl(id)));

global.window = {{
  innerWidth: 1280,
  innerHeight: 800,
  location: {{ href: "http://localhost:8000/nodes", search: "" }},
  addEventListener() {{}}
}};
global.document = {{
  readyState: "complete",
  getElementById(id) {{ return elements.get(id) || null; }},
  querySelectorAll() {{ return []; }},
  addEventListener() {{}},
  createElement() {{ return makeEl("tmp"); }},
  body: {{ appendChild() {{}}, removeChild() {{}} }}
}};
global.fetch = () => Promise.resolve({{ ok: true, json: async () => ({{ ok: true, hasServerKey: true, hasGeminiKey: true, hasNanogptKey: true }}) }});

{script}

const api = window.TinCanNodeStudio;
const out = {{}};

// Initial mode
out.initialMode = elements.get("nsModePill").textContent;

// Spawn 2 assets -> edit -> merge
api.spawnAssetNode("asset-0");
api.addNodeAsRef(api.getState().nodes[0].id);
out.editMode = elements.get("nsModePill").textContent;

api.spawnAssetNode("asset-1");
api.addNodeAsRef(api.getState().nodes[1].id);
out.mergeMode = elements.get("nsModePill").textContent;

// Toggle non-destructive filter on node
const firstId = api.getState().nodes[0].id;
api.toggleNodeFilter(firstId, "kodak_2383");
out.nodeFilterOn = !!api.getState().nodes[0].filters.kodak_2383;

// Duplicate & auto-layout with 3 nodes
api.duplicateNode(firstId);
out.nodeCountAfterDup = api.getState().nodes.length;
api.autoLayout();
out.autoLayoutHidden = elements.get("nsAutoLayoutBtn").classList.contains("hidden");

// Model capability switching (Pro -> 1:1 resets panoramic 1:8, Lite -> 1K)
api.updateConfig("aspectRatio", "1:8");
out.panoAspect = api.getState().aspectRatio;
api.selectModel("gemini-3-pro-image");
out.proAspectFallback = api.getState().aspectRatio;
api.selectModel("gemini-3.1-flash-lite-image");
out.liteRes = api.getState().resolution;

// Left panel expand/collapse & template apply
api.toggleLeftPanel(true);
out.drawerVisible = !elements.get("nsLeftDrawer").classList.contains("hidden");
api.applyTemplate("t1");
out.appliedPrompt = elements.get("nsPromptInput").value;

// Clear selection resets to GENERATE MODE
api.clearSelection();
out.clearedMode = elements.get("nsModePill").textContent;

console.log(JSON.stringify(out));
"""
    run_res = subprocess.run(
        [node_bin, "-e", harness],
        text=True,
        capture_output=True,
        check=False,
    )
    assert run_res.returncode == 0, f"Node runtime failed: {run_res.stderr}"
    res = json.loads(run_res.stdout.strip())
    assert res["initialMode"] == "GENERATE MODE"
    assert res["editMode"] == "EDIT MODE"
    assert res["mergeMode"] == "MERGE MODE"
    assert res["nodeFilterOn"] is True
    assert res["nodeCountAfterDup"] == 3
    assert res["autoLayoutHidden"] is False
    assert res["panoAspect"] == "1:8"
    assert res["proAspectFallback"] == "1:1"
    assert res["liteRes"] == "1K"
    assert res["drawerVisible"] is True
    assert "Tokyo" in res["appliedPrompt"]
    assert res["clearedMode"] == "GENERATE MODE"
