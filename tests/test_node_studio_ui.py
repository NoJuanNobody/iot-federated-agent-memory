"""Unit and JS runtime tests for iot_federated_agent_memory.node_studio_ui."""

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
    FILTER_RACK_SPECS,
    MODALITY_SPECS,
    MODEL_OPTIONS,
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


@pytest.mark.parametrize("modality", ["image", "text", "video"])
def test_aeonik_celadon_compliance_across_modalities(modality: str) -> None:
    html = render_node_studio_html(modality)
    assert html.startswith("<!doctype html>")
    assert legacy_palette_classes(html) == []
    assert celadonize_classes(html) == html
    for forbidden in ("bg-slate-", "text-cyan-", "bg-cyan-", "bg-emerald-", "bg-gradient-to-"):
        assert forbidden not in html
    for hex_token in ("#ecf1e6", "#f4f8f0", "#ffffff", "#111111", "#4a4a4a", "#5c5c5c", "#107a47"):
        assert hex_token in html.lower()
    assert set(AEONIK_PALETTE.values()) >= {"#ecf1e6", "#f4f8f0", "#ffffff", "#111111", "#107a47"}


def test_render_node_studio_image_four_quadrants_and_controls() -> None:
    html = render_node_studio_html("image")

    # Top Bar
    for token in (
        "14:41",
        "Node Studio · Image",
        "~/space/nodes",
        "Editor",
        "Timeline",
        "Library",
        "Text",
        "Image",
        "Video",
    ):
        assert token in html

    # Quadrant 1: DAG & Serial Filter Chain
    for q1_token in (
        "NODE GRAPH · DAG &amp; SERIAL FILTER CHAIN",
        "[01 · GENERATED]",
        "[02 · UPLOADED REF]",
        "[03 · FILTER + EDIT]",
        "[04 · MERGED 21:9 *SEL]",
        "[05 · 4K]",
        "LivingCube",
        "[A] Auto-Layout",
        "[F] Fit View",
        "[Cmd+D] Bypass Filter",
        "+ Ref",
        "00:00 [#01]",
        "00:03 [#03 LUT]",
        "00:06 [#04 21:9]",
        "00:09 [#05 4K]",
    ):
        assert q1_token in html

    # Quadrant 2: Telemetry & Filter Rack
    for q2_token in (
        "NANOGPT &amp; FILTER RACK",
        "LUT MIX",
        "85%",
        "HALATION",
        "+35%",
        "5,000 CR",
        "12.0s",
        "ON ●",
    ):
        assert q2_token in html

    for filter_id in (
        "kodak_2383",
        "halation",
        "film_grain_16mm",
        "wga_tighten",
        "fact_lock",
        "optical_flow_60fps",
        "temporal_deflicker",
        "j_cut_dialogue_duck",
    ):
        assert filter_id in html
        assert f'id="nsFilterBtn-{filter_id}"' in html

    # Quadrant 3: Tree
    for q3_token in (
        "TREE ~/space/nodes/timeline",
        "├──",
        "└──",
        "main.dag",
        "kodak_2383.cube",
        "char_rig_sheet.png",
    ):
        assert q3_token in html

    # Quadrant 4: Prompt Island
    for q4_token in (
        "PROMPT ISLAND",
        "MODE: MERGE (2 SELECTED)",
        "In Conversation",
        "API: NanoGPT + Gemini Ready",
        "X-NanoGPT-Api-Key",
        "X-Gemini-Api-Key",
        "[REF #01]",
        "[REF #02]",
        "[REF #03]",
        "+ Attach .space / Drop Ref",
        "ASPECT 21:9",
        "RES 4K",
        "THINK HIGH",
        "SEARCH WEB+IMG",
        "VIA AUTO (NANOGPT)",
        "/api/nodes/generate",
    ):
        assert q4_token in html

    for model_id in (
        "nano-banana-2.1",
        "nano-banana-pro",
        "nano-banana-2",
        "nano-banana-2-lite",
        "deepseek-v4.1-tee",
        "ltx-video",
    ):
        assert f'value="{model_id}"' in html

    # Bottom Status Bar
    for status_token in ("main ↑1 ↓0", "~/space/nodes", "3/14 refs", "nanogpt-2.1", "zsh", "120×34", "UTF-8"):
        assert status_token in html


def test_render_node_studio_text_and_video_modalities() -> None:
    text_html = render_node_studio_html("text")
    for token in (
        "Node Studio · Text",
        "~/space/notes",
        "TEXT NODE GRAPH · BRANCHING DRAFTS &amp; PROSE FILTER CHAIN",
        "410 t/s",
        "-38%",
        "128K tok",
        "4 Beats",
        "TREE ~/space/notes/text-nodes",
        "deepseek-v4.1-tee",
        "FAILOVER.pdf",
    ):
        assert token in text_html

    video_html = render_node_studio_html("video")
    for token in (
        "Node Studio · Video",
        "~/space/video",
        "VIDEO NODE GRAPH · MULTI-SHOT &amp; TEMPORAL CHAIN",
        "60 fps",
        "-14 LUFS",
        "98% Lock",
        "14.0s",
        "TREE ~/space/video/timeline-cuts",
        "ltx-video",
        "vo_kokoro_narration.wav",
    ):
        assert token in video_html

    fallback_html = render_node_studio_html("unknown-modality")
    assert "Node Studio · Image" in fallback_html


def test_render_node_studio_window_html_and_chrome_integration() -> None:
    win_html = render_node_studio_window_html()
    assert win_html.startswith('<div id="win-nodes" class="mesh-window')
    assert (
        '<!--TC_TITLEBAR {"id": "win-nodes", "title": "Node Studio · Prompt Island, Timeline & Filter Graph", "badge": "NANOGPT + GEMINI"}-->'
        in win_html
    )
    assert legacy_palette_classes(win_html) == []
    assert celadonize_classes(win_html) == win_html

    # Unique IDs inside win-nodes and zero collisions with other windows in MESH_OS_HTML_UI
    ns_ids = re.findall(r'(?<![\w-])id="([^"]+)"', win_html)
    assert len(ns_ids) >= 35
    assert len(ns_ids) == len(set(ns_ids))

    mesh_counts = Counter(re.findall(r'(?<![\w-])id="([^"]+)"', MESH_OS_HTML_UI))
    # win-nodes is mounted in MESH_OS_HTML_UI once, so every ID must appear exactly once.
    collisions = {eid: mesh_counts[eid] for eid in ns_ids if mesh_counts[eid] != 1}
    assert collisions == {}, f"Expected every #win-nodes ID once in MESH_OS_HTML_UI: {collisions}"

    # Expand titlebars and apply_window_chrome cleanly
    expanded = expand_titlebars(win_html)
    assert "<!--TC_TITLEBAR" not in expanded
    assert "Node Studio · Prompt Island, Timeline &amp; Filter Graph" in expanded
    assert "NANOGPT + GEMINI" in expanded

    page = f"<!doctype html><html><head></head><body>{win_html}</body></html>"
    chromed = apply_window_chrome(page)
    assert 'id="tc-celadon"' in chromed
    assert "<!--TC_TITLEBAR" not in chromed
    assert apply_window_chrome(chromed) == chromed


def test_view_parameter_and_registry_constants() -> None:
    assert len(MODALITY_SPECS) == 3
    assert len(FILTER_RACK_SPECS) == 8
    assert len(MODEL_OPTIONS) >= 6

    tl_html = render_node_studio_html("image", active_view="timeline")
    assert 'id="nsTimelineSubview" class="ns-subview"' in tl_html
    assert 'id="nsQuadGrid" class="ns-quad-grid hidden"' in tl_html

    lib_html = render_node_studio_html("image", active_view="library")
    assert 'id="nsLibrarySubview" class="ns-subview"' in lib_html


def test_inline_js_syntax_and_interactive_state_transitions_in_node() -> None:
    node_bin = shutil.which("node")
    if not node_bin:
        pytest.skip("node binary not available for JS check")

    html = render_node_studio_html("image")
    script = _extract_inline_script(html)

    # Syntax check via node --check using stdin
    proc = subprocess.run(
        [node_bin, "--check"],
        input=script,
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, f"JS syntax error: {proc.stderr}"

    # Behavioral runtime check in Node with lightweight DOM stub
    harness = f"""
const elements = new Map();
function makeEl(id) {{
  const el = {{
    id,
    textContent: "",
    innerHTML: "",
    value: "",
    dataset: {{}},
    style: {{}},
    attributes: {{}},
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
    getBoundingClientRect() {{ return {{ left: 0, top: 0, right: 100, height: 60, width: 800 }}; }}
  }};
  return el;
}}
[
  "nsTopClock", "nsModePill", "nsCliPreview", "nsBottomStatusLeft", "nsDagCanvas", "nsDagWires",
  "nsRefsRow", "nsHeroTitle", "nsHeaderCwd", "nsQ1Title", "nsQ2Title", "nsQ2Endpoint",
  "nsQ3Title", "nsApiStatusBtn", "nsGenerateBtn", "nsPromptInput", "nsModelSelect",
  "nsKpiGrid", "nsSparkWrap", "nsDagNodes", "nsTlPrefix", "nsTlStops", "nsNodeTableBody",
  "nsTreeList", "nsTreeFooter", "nsQuadGrid", "nsTimelineSubview", "nsLibrarySubview",
  "nsGenFeedback", "nsFilterBtn-kodak_2383", "nsFilterBtn-wga_tighten"
].forEach((id) => elements.set(id, makeEl(id)));

global.window = {{
  location: {{ href: "http://localhost:8000/nodes", search: "" }},
  history: {{ replaceState() {{}} }},
  addEventListener() {{}}
}};
global.document = {{
  readyState: "complete",
  getElementById(id) {{ return elements.get(id) || null; }},
  querySelectorAll() {{ return []; }},
  addEventListener() {{}}
}};
global.setInterval = () => 0;
global.clearInterval = () => {{}};
global.setTimeout = () => 0;
global.fetch = () => Promise.resolve({{ ok: true, json: async () => ({{ node: {{ id: "06" }} }}) }});

{script}

const api = window.TinCanNodeStudio;
const results = {{}};

// Initial image state has 2 selected nodes -> MERGE MODE
results.initialMode = elements.get("nsModePill").textContent;

// Clear selection -> 0 selected -> GENERATE MODE
api.clearSelection();
results.zeroMode = elements.get("nsModePill").textContent;

// Select 1 node -> EDIT + FILTER MODE
api.toggleNode("01");
results.oneMode = elements.get("nsModePill").textContent;

// Select 2nd node -> MERGE MODE
api.toggleNode("02");
results.twoMode = elements.get("nsModePill").textContent;

// Toggle filter kodak_2383 off -> ○ OFF
api.toggleFilter("kodak_2383");
results.filterOffText = elements.get("nsFilterBtn-kodak_2383").textContent;

// Switch to text modality
api.applyModality("text", false);
results.textTitle = elements.get("nsHeroTitle").textContent;
results.textPath = elements.get("nsHeaderCwd").textContent;

// Switch to video modality
api.applyModality("video", false);
results.videoTitle = elements.get("nsHeroTitle").textContent;
results.videoPath = elements.get("nsHeaderCwd").textContent;

// Attach and remove ref
api.attachQuickRef("custom_ref.png");
results.refCountAfterAdd = api.getState().refs.length;
api.removeRef(0);
results.refCountAfterRemove = api.getState().refs.length;

console.log(JSON.stringify(results));
"""
    run_res = subprocess.run(
        [node_bin, "-e", harness],
        text=True,
        capture_output=True,
        check=False,
    )
    assert run_res.returncode == 0, f"Node runtime failed: {run_res.stderr}"
    out = json.loads(run_res.stdout.strip())
    assert out["initialMode"] == "MODE: MERGE (2 SELECTED)"
    assert out["zeroMode"] == "MODE: GENERATE (0 SELECTED)"
    assert out["oneMode"] == "MODE: EDIT + FILTER (1 SELECTED)"
    assert out["twoMode"] == "MODE: MERGE (2 SELECTED)"
    assert out["filterOffText"] == "○ OFF"
    assert out["textTitle"] == "Node Studio · Text"
    assert out["textPath"] == "~/space/notes"
    assert out["videoTitle"] == "Node Studio · Video"
    assert out["videoPath"] == "~/space/video"
    assert out["refCountAfterAdd"] == 4
    assert out["refCountAfterRemove"] == 3
