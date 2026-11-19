"""Tests for World Labs Atlas v2, Omni-Modal Slash Router, Pitch-Black Terminal, and Terminal Aeonik UI in Node Studio."""

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
    MODEL_CAPABILITIES,
    SLASH_ROUTER_COMMANDS,
    render_node_studio_html,
    render_node_studio_window_html,
)
from iot_federated_agent_memory.window_chrome import (  # noqa: E402
    celadonize_classes,
    legacy_palette_classes,
)


FORBIDDEN_UTILITY_PREFIXES = (
    "bg-slate-",
    "text-slate-",
    "border-slate-",
    "bg-zinc-",
    "text-zinc-",
    "border-zinc-",
    "bg-cyan-",
    "text-cyan-",
    "border-cyan-",
    "bg-purple-",
    "text-purple-",
    "border-purple-",
    "bg-pink-",
    "text-pink-",
    "border-pink-",
    "bg-emerald-",
    "text-emerald-",
    "border-emerald-",
    "bg-indigo-",
    "text-indigo-",
    "border-indigo-",
    "bg-blue-",
    "text-blue-",
    "border-blue-",
    "bg-gradient-to-",
)


def _extract_inline_script(html: str) -> str:
    m = re.search(
        r'<script\s+id="nodeStudioUiScript"[^>]*>(.*?)</script>',
        html,
        flags=re.DOTALL,
    )
    assert m, "nodeStudioUiScript block must exist"
    return m.group(1)


def test_available_models_capabilities_and_slash_router_commands() -> None:
    models_list = list(AVAILABLE_MODELS)
    assert len(models_list) == 8
    assert len(AVAILABLE_MODELS) == 8

    # First 4 must remain the Nano Banana models
    assert [m["id"] for m in models_list[:4]] == [
        "gemini-nano-banana-2.1",
        "gemini-3-pro-image",
        "gemini-3.1-flash-image",
        "gemini-3.1-flash-lite-image",
    ]

    # Next 4 must be World Labs Atlas v2 and Omni-Modal models
    by_id = {m["id"]: m for m in models_list}
    assert by_id["worldlabs/atlas-v2"]["name"] == "World Labs Atlas v2"
    assert by_id["worldlabs/atlas-v2"]["badge"] == "Spatial"
    assert by_id["google/lyria-3.5"]["name"] == "Lyria 3.5 + ElevenLabs v4"
    assert by_id["google/lyria-3.5"]["badge"] == "Audio"
    assert by_id["kling-4.0"]["name"] == "Kling 4.0 + LTX-2.5"
    assert by_id["kling-4.0"]["badge"] == "Video"
    assert by_id["hyper3d/rodin-v2.5"]["name"] == "Hyper3D Rodin v2.5 + Rig"
    assert by_id["hyper3d/rodin-v2.5"]["badge"] == "3D"

    for mid in (
        "worldlabs/atlas-v2",
        "google/lyria-3.5",
        "kling-4.0",
        "hyper3d/rodin-v2.5",
    ):
        assert mid in MODEL_CAPABILITIES
        assert MODEL_CAPABILITIES[mid]["maxReferences"] == 14

    slash_cmds = [c["command"] for c in SLASH_ROUTER_COMMANDS]
    for expected_cmd in (
        "/atlas splat",
        "/atlas pose",
        "/atlas flythrough",
        "/atlas mesh",
        "/image",
        "/video",
        "/audio",
        "/3d",
        "/rig",
        "/text",
    ):
        assert expected_cmd in slash_cmds


def test_strict_terminal_aeonik_celadon_and_monochrome_dark_mode_tokens() -> None:
    for html in (render_node_studio_html(), render_node_studio_window_html()):
        assert legacy_palette_classes(html) == []
        assert celadonize_classes(html) == html
        for forbidden in FORBIDDEN_UTILITY_PREFIXES:
            assert forbidden not in html, f"Forbidden utility class prefix {forbidden} found"

        low = html.lower()
        # Light Mode Aeonik Celadon tokens
        for token in (
            "#ecf1e6",
            "#f4f8f0",
            "#ffffff",
            "#111111",
            "#4a4a4a",
            "#5c5c5c",
            "#107a47",
            "#8a1c1c",
            "1px solid #111111",
        ):
            assert token in low, f"Missing Light Mode Aeonik token: {token}"

        # Dark Mode Monochrome B&W + Pitch-Black #000000 Terminal tokens
        assert 'html[data-theme="dark"]' in html
        assert "body.tc-dark" in html
        for dark_token in (
            "#080808",
            "#0e0e0e",
            "#151515",
            "#f5f5f5",
            "#2e2e2e",
            "#000000",
            "1.5px solid #ffffff",
        ):
            assert dark_token in low, f"Missing Dark Mode Monochrome token: {dark_token}"

    assert AEONIK_PALETTE == {
        "bg": "#ecf1e6",
        "card": "#f4f8f0",
        "paper": "#ffffff",
        "ink": "#111111",
        "muted": "#4a4a4a",
        "faint": "#5c5c5c",
        "green": "#107a47",
        "danger": "#8a1c1c",
    }


def test_slash_router_popover_floating_terminal_and_omni_modal_cards_markup() -> None:
    html = render_node_studio_html()
    win_html = render_node_studio_window_html()

    required_ids = (
        "nsSlashRouterPopover",
        "nsActiveSlashPill",
        "nsActiveSlashPillText",
        "nsFloatingTerminal",
        "nsTerminalLog",
        "nsTerminalInput",
        "nsTerminalRunBtn",
        "nsPromptIsland",
        "nsPromptInput",
    )
    for dom_id in required_ids:
        assert f'id="{dom_id}"' in html
        assert f'id="{dom_id}"' in win_html

    # Verify #nsSlashRouterPopover and #nsActiveSlashPill are inside #nsPromptIsland
    island_match = re.search(
        r'<div id="nsPromptIsland" class="ns-island">(.*?)<!-- Bottom-Center',
        html + "<!-- Bottom-Center",
        flags=re.DOTALL,
    )
    assert island_match
    island_block = island_match.group(1)
    assert 'id="nsSlashRouterPopover"' in island_block
    assert 'id="nsActiveSlashPill"' in island_block

    # Verify floating terminal and omni-modal node cards content
    for token in (
        "NODE STUDIO DARK TERMINAL · /api/omni/route",
        "RUN ↵",
        "SLASH-COMMAND OMNI-MODAL ROUTER",
        "● /atlas splat",
        "ATLAS · images2PosedRGBD",
        "AUDIO · TTS + SCORE + SFX",
        "│┃│┃┃│┃┃",
        "OMNI-WORLD MASTER · SPLAT + GLB + MP4",
        "World Labs Atlas v2",
        "Lyria 3.5 + ElevenLabs v4",
        "Kling 4.0 + LTX-2.5",
        "Hyper3D Rodin v2.5 + Rig",
    ):
        assert token in html

    # Verify no duplicate IDs inside #win-nodes or MESH_OS_HTML_UI
    ns_ids = re.findall(r'(?<![\w-])id="([^"]+)"', win_html)
    assert len(ns_ids) == len(set(ns_ids))
    mesh_counts = Counter(re.findall(r'(?<![\w-])id="([^"]+)"', MESH_OS_HTML_UI))
    duplicates = [eid for eid in ns_ids if mesh_counts[eid] != 1]
    assert duplicates == []


def test_slash_router_and_terminal_runtime_in_node() -> None:
    node_bin = shutil.which("node")
    if not node_bin:
        pytest.skip("node binary not available for JS runtime check")

    html = render_node_studio_html()
    script = _extract_inline_script(html)

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
    _classes: new Set(["hidden"]),
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
  "nsActiveRunsCount", "nsGenerateBtn", "nsResponseToast",
  "nsSlashRouterPopover", "nsActiveSlashPill", "nsActiveSlashPillText",
  "nsFloatingTerminal", "nsTerminalLog", "nsTerminalInput", "nsTerminalRunBtn"
].forEach((id) => elements.set(id, makeEl(id)));

const fetchCalls = [];
global.window = {{
  innerWidth: 1280,
  innerHeight: 800,
  location: {{ href: "http://localhost:8013/nodes", search: "" }},
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
global.fetch = (url, opts) => {{
  fetchCalls.push({{ url, method: (opts && opts.method) || "GET", body: opts && opts.body ? JSON.parse(opts.body) : null }});
  if (url === "/api/omni/route" && fetchCalls.filter((c) => c.url === "/api/omni/route").length === 2) {{
    return Promise.resolve({{ status: 404, ok: false, json: async () => ({{ ok: false }}) }});
  }}
  return Promise.resolve({{
    status: 200,
    ok: true,
    json: async () => ({{ ok: true, saved_to_space: "/worlds/torii_3e78434c/refinedSplats_2000000.spz" }})
  }});
}};

{script}

(async () => {{
  const api = window.TinCanNodeStudio;
  const out = {{}};

  // 1. parseSlashCommand across modalities
  out.parsedSplat = api.parseSlashCommand('/atlas splat /images/torii.jpg --views 14 --mesh');
  out.parsedPose = api.parseSlashCommand('/atlas pose /images/torii.jpg');
  out.parsedAudio = api.parseSlashCommand('/audio music "Ambient dusk koto"');
  out.parsedVideo = api.parseSlashCommand('/video --model kling-4.0 "Crane shot"');
  out.parsed3d = api.parseSlashCommand('/3d --rig walk "Fox statue"');

  // 2. Typing '/' in #nsPromptInput opens #nsSlashRouterPopover
  elements.get("nsPromptInput").value = "/atlas";
  api.handlePromptInput("/atlas");
  out.popoverOpenOnSlash = !elements.get("nsSlashRouterPopover").classList.contains("hidden");

  // 3. applySlashRoute updates #nsActiveSlashPill and active model/modality
  api.applySlashRoute("/audio");
  out.activePillAfterAudio = elements.get("nsActiveSlashPillText").textContent;
  out.activeModelAfterAudio = api.getState().model;
  out.popoverClosedAfterApply = elements.get("nsSlashRouterPopover").classList.contains("hidden");

  // 4. runTerminalCommand calls /api/omni/route and spawns Omni-Modal cards
  await api.runTerminalCommand('/atlas pose /images/torii_gate.jpg');
  await api.runTerminalCommand('/audio music "Koto + waves"'); // triggers 404 fallback to /api/nodes/generate
  await api.runTerminalCommand('/atlas splat /images/torii_gate.jpg --views 14');

  out.nodesHtml = elements.get("nsNodesLayer").innerHTML;
  out.terminalLogHtml = elements.get("nsTerminalLog").innerHTML;
  out.fetchUrls = fetchCalls.map((c) => c.url);
  out.nodeCount = api.getState().nodes.length;

  console.log(JSON.stringify(out));
}})();
"""
    run_res = subprocess.run(
        [node_bin, "-e", harness],
        text=True,
        capture_output=True,
        check=False,
    )
    assert run_res.returncode == 0, f"Node runtime failed: {run_res.stderr}"
    res = json.loads(run_res.stdout.strip())

    assert res["parsedSplat"]["is_slash"] is True
    assert res["parsedSplat"]["command"] == "atlas"
    assert res["parsedSplat"]["subcommand"] == "splat"
    assert res["parsedSplat"]["modality"] == "atlas"
    assert res["parsedSplat"]["model"] == "worldlabs/atlas-v2"
    assert res["parsedSplat"]["atlas_task"] == "posedImages2Splats"

    assert res["parsedPose"]["atlas_task"] == "images2PosedRGBD"
    assert res["parsedAudio"]["modality"] == "audio"
    assert res["parsedAudio"]["model"] == "google/lyria-3.5"
    assert res["parsedVideo"]["modality"] == "video"
    assert res["parsedVideo"]["model"] == "kling-4.0"
    assert res["parsed3d"]["modality"] == "3d"
    assert res["parsed3d"]["model"] == "hyper3d/rodin-v2.5"

    assert res["popoverOpenOnSlash"] is True
    assert "♪ /audio" in res["activePillAfterAudio"]
    assert res["activeModelAfterAudio"] == "google/lyria-3.5"
    assert res["popoverClosedAfterApply"] is True

    assert "/api/omni/route" in res["fetchUrls"]
    assert "/api/nodes/generate" in res["fetchUrls"]
    assert res["nodeCount"] == 3
    assert "ATLAS · images2PosedRGBD" in res["nodesHtml"]
    assert "AUDIO · TTS + SCORE + SFX" in res["nodesHtml"]
    assert "│┃│┃┃│┃┃" in res["nodesHtml"]
    assert "OMNI-WORLD MASTER · SPLAT + GLB + MP4" in res["nodesHtml"]
    assert "you@tincan:~/space$" in res["terminalLogHtml"]
