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
    MODALITY_TABS,
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
    assert len(models_list) == 14
    assert len(AVAILABLE_MODELS) == 14
    assert [t["id"] for t in MODALITY_TABS] == ["image", "text", "video", "audio", "3d", "atlas"]

    # First 4 must remain the Nano Banana image models
    assert [m["id"] for m in models_list[:4]] == [
        "gemini-nano-banana-2.1",
        "gemini-3-pro-image",
        "gemini-3.1-flash-image",
        "gemini-3.1-flash-lite-image",
    ]

    # Must include Text, Video, Audio, 3D Mesh, and World Labs Spatial models
    by_id = {m["id"]: m for m in models_list}
    assert by_id["gemini-3.1-pro"]["modality"] == "text"
    assert by_id["nanogpt/TEE/deepseek-v4.1-flash"]["modality"] == "text"
    assert by_id["nanogpt/Gemma-4-31B-Gembrain-uncensored-heretic"]["modality"] == "text"
    assert by_id["worldlabs/atlas-v2"]["name"] == "World Labs Atlas v2"
    assert by_id["worldlabs/atlas-v2"]["badge"] == "Spatial"
    assert by_id["google/lyria-3.5"]["name"] == "Lyria 3.5 + ElevenLabs v4"
    assert by_id["google/lyria-3.5"]["modality"] == "audio"
    assert by_id["kling-4.0"]["name"] == "Kling 4.0 + LTX-2.5"
    assert by_id["kling-4.0"]["badge"] == "Video"
    assert by_id["hyper3d/rodin-v2.5"]["name"] == "Hyper3D Rodin v2.5 + Rig"
    assert by_id["hyper3d/rodin-v2.5"]["badge"] == "3D"

    for mid in (
        "gemini-3.1-pro",
        "nanogpt/TEE/deepseek-v4.1-flash",
        "worldlabs/atlas-v2",
        "google/lyria-3.5",
        "elevenlabs/eleven-v4",
        "kling-4.0",
        "ltx-video",
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
        "nsModalityBar",
        "nsModTab-image",
        "nsModTab-text",
        "nsModTab-video",
        "nsModTab-audio",
        "nsModTab-3d",
        "nsModTab-atlas",
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

    # Confusing Atlas v2 Pipeline bar must be completely removed from the Prompt Island
    assert "nsAtlasWorkflowBar" not in html
    assert "ATLAS v2 PIPELINE" not in html
    assert "nsAtlasWorkflowBar" not in win_html
    assert 'id="nsActiveSlashPill" type="button" class="ns-active-slash-pill hidden"' in html
    assert 'id="nsFloatingTerminal" class="ns-floating-terminal ns-terminal-drawer hidden"' in html

    # Verify #nsModalityBar, #nsSlashRouterPopover, and #nsActiveSlashPill are inside #nsPromptIsland
    island_match = re.search(
        r'<div id="nsPromptIsland" class="ns-island">(.*?)<!-- Bottom-Center',
        html + "<!-- Bottom-Center",
        flags=re.DOTALL,
    )
    assert island_match
    island_block = island_match.group(1)
    assert 'id="nsModalityBar"' in island_block
    assert 'id="nsSlashRouterPopover"' in island_block
    assert 'id="nsActiveSlashPill"' in island_block

    # Verify floating terminal, grouped model picker, and omni-modal node cards content
    for token in (
        "NODE STUDIO DARK TERMINAL · /api/omni/route",
        "RUN ↵",
        "SLASH-COMMAND OMNI-MODAL ROUTER",
        "/atlas splat",
        "ATLAS · images2PosedRGBD",
        "AUDIO · TTS + SCORE + SFX",
        "│┃│┃┃│┃┃",
        "OMNI-WORLD MASTER · SPLAT + GLB + MP4",
        "Gemini 3.1 Pro",
        "DeepSeek v4.1 Flash (TEE)",
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
  "nsFloatingTerminal", "nsTerminalLog", "nsTerminalInput", "nsTerminalRunBtn",
  "nsTerminalHideBtn", "nsTerminalToggleBtn", "nsTerminalToggleState",
  "nsSaveGraphBtn", "nsSaveGraphStatus", "nsGraphsMenuBtn", "nsGraphsPopover",
  "nsGraphNameInput", "nsGraphSaveAsBtn", "nsGraphsList", "nsGraphNewBtn", "nsGraphExportBtn",
  "nsSplatViewerModal", "nsSplatModalTitle", "nsSplatModalMeta", "nsSplatModalCanvas"
].forEach((id) => elements.set(id, makeEl(id)));

const fetchCalls = [];
const mockGraphStore = new Map();
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
  const method = (opts && opts.method) || "GET";
  const body = opts && opts.body ? JSON.parse(opts.body) : null;
  fetchCalls.push({{ url, method, body }});
  if (url === "/api/nodes/graph" && method === "POST" && body && body.path) {{
    mockGraphStore.set(body.path, body.graph);
    return Promise.resolve({{ status: 200, ok: true, json: async () => ({{ ok: true, path: body.path, name: body.name, node_count: (body.graph.nodes || []).length }}) }});
  }}
  if (String(url).startsWith("/api/nodes/graphs")) {{
    const graphs = Array.from(mockGraphStore.keys()).map((p) => ({{ path: p, name: p.replace("/nodes/", "").replace(".nodes.json", ""), size_bytes: 2048 }}));
    return Promise.resolve({{ status: 200, ok: true, json: async () => ({{ ok: true, graphs, count: graphs.length }}) }});
  }}
  if (String(url).startsWith("/api/nodes/graph?")) {{
    const m = String(url).match(/path=([^&]+)/);
    const p = m ? decodeURIComponent(m[1]) : "/nodes/workspace.nodes.json";
    if (!mockGraphStore.has(p)) {{
      return Promise.resolve({{ status: 404, ok: false, json: async () => ({{ ok: false }}) }});
    }}
    return Promise.resolve({{ status: 200, ok: true, json: async () => ({{ ok: true, path: p, graph: mockGraphStore.get(p) }}) }});
  }}
  if (url === "/api/omni/route" && fetchCalls.filter((c) => c.url === "/api/omni/route").length === 2) {{
    return Promise.resolve({{ status: 404, ok: false, json: async () => ({{ ok: false }}) }});
  }}
  return Promise.resolve({{
    status: 200,
    ok: true,
    json: async () => ({{
      ok: true,
      saved_to_space: {{
        scope: "user",
        owner_id: "default",
        files: ["/worlds/torii_3e78434c/refinedSplats_2000000.spz"],
        path: "/worlds/torii_3e78434c/refinedSplats_2000000.spz"
      }}
    }})
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

  // 5. Selecting World Labs Atlas v2 model, attaching 4 multi-view photos, and running generate() sends all 4 to /api/omni/route
  api.selectModel("worldlabs/atlas-v2");
  api.handleFilesSelected([
    {{ name: "view_01.jpg", type: "image/jpeg", size: 1024, url: "data:image/jpeg;base64,AAAA1111" }},
    {{ name: "view_02.jpg", type: "image/jpeg", size: 1024, url: "data:image/jpeg;base64,BBBB2222" }},
    {{ name: "view_03.jpg", type: "image/jpeg", size: 1024, url: "data:image/jpeg;base64,CCCC3333" }},
    {{ name: "view_04.jpg", type: "image/jpeg", size: 1024, url: "data:image/jpeg;base64,DDDD4444" }}
  ]);
  out.multiRefCount = api.getState().references.length;
  out.refCounterText = elements.get("nsRefCounter").textContent;
  // Clearing canvas selection must preserve uploaded multi-view photos
  api.clearSelection();
  out.multiRefCountAfterClearSel = api.getState().references.length;

  elements.get("nsPromptInput").value = "Lake Ashi shrine at twilight";
  await api.generate();
  const lastOmniCall = fetchCalls.filter((c) => c.url === "/api/omni/route").pop();
  out.sentMultiRefCount = lastOmniCall && lastOmniCall.body && Array.isArray(lastOmniCall.body.references)
    ? lastOmniCall.body.references.length : 0;
  out.sentMultiRefB64Count = lastOmniCall && lastOmniCall.body && Array.isArray(lastOmniCall.body.references)
    ? lastOmniCall.body.references.filter((r) => !!r.base64).length : 0;

  // 6. Opening and closing Fullscreen 3D Gaussian Splat Viewer Modal
  const latestNodeId = api.getState().nodes[api.getState().nodes.length - 1].id;
  api.setNodeSplatMode(latestNodeId, "depth");
  api.toggleNodeFrustums(latestNodeId);
  api.openSplatViewer(latestNodeId);
  out.splatModalVisible = !elements.get("nsSplatViewerModal").classList.contains("hidden");
  out.splatModalTitle = elements.get("nsSplatModalTitle").textContent;
  out.splatModalMeta = elements.get("nsSplatModalMeta").textContent;
  api.closeSplatViewer();
  out.splatModalClosed = elements.get("nsSplatViewerModal").classList.contains("hidden");

  // 7. Hiding and showing the Node Studio Dark Terminal
  api.toggleTerminal(false);
  out.terminalHidden = elements.get("nsFloatingTerminal").classList.contains("hidden");
  out.terminalLabelWhenHidden = elements.get("nsTerminalToggleState").textContent;
  api.toggleTerminal(true);
  out.terminalShownAgain = !elements.get("nsFloatingTerminal").classList.contains("hidden");
  out.terminalLabelWhenShown = elements.get("nsTerminalToggleState").textContent;

  // 8. Saving .nodes.json to .space, starting a blank canvas, and reopening it intact
  const savedMeta = await api.saveGraphToSpace("torii_scene", false);
  out.savedGraphPath = savedMeta.path;
  api.newBlankGraph();
  out.nodeCountAfterBlank = api.getState().nodes.length;
  const reopenedOk = await api.loadGraphFromSpace("/nodes/torii_scene.nodes.json", false);
  out.reopenedOk = reopenedOk;
  out.nodeCountAfterReopen = api.getState().nodes.length;
  out.refCountAfterReopen = api.getState().references.length;
  out.graphNameAfterReopen = api.getState().graphName;

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
    assert res["nodeCount"] == 4
    assert res["multiRefCount"] == 4
    assert res["multiRefCountAfterClearSel"] == 4
    assert "4/14 views" in res["refCounterText"]
    assert res["sentMultiRefCount"] == 4
    assert res["sentMultiRefB64Count"] == 4
    assert res["splatModalVisible"] is True
    assert res["splatModalClosed"] is True
    assert res["terminalHidden"] is True
    assert res["terminalLabelWhenHidden"] == "[Show]"
    assert res["terminalShownAgain"] is True
    assert res["terminalLabelWhenShown"] == "[Hide]"
    assert res["savedGraphPath"] == "/nodes/torii_scene.nodes.json"
    assert res["nodeCountAfterBlank"] == 0
    assert res["reopenedOk"] is True
    assert res["nodeCountAfterReopen"] == 4
    assert res["refCountAfterReopen"] == 4
    assert res["graphNameAfterReopen"] == "torii_scene"
    assert "3D GAUSSIAN SPLAT VIEWER (.SPZ)" in res["splatModalTitle"]
    assert "[object Object]" not in res["splatModalMeta"]
    assert "[object Object]" not in res["nodesHtml"]
    assert "[object Object]" not in res["terminalLogHtml"]
    assert "ns-splat-canvas" in res["nodesHtml"]
    assert "View 3D Splat" in res["nodesHtml"]
    assert "ATLAS · images2PosedRGBD" in res["nodesHtml"]
    assert "AUDIO · TTS + SCORE + SFX" in res["nodesHtml"]
    assert "│┃│┃┃│┃┃" in res["nodesHtml"]
    assert "OMNI-WORLD MASTER · SPLAT + GLB + MP4" in res["nodesHtml"]
    assert "you@tincan:~/space$" in res["terminalLogHtml"]


def test_modality_switching_image_merge_and_non_atlas_generation_in_node() -> None:
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
    _classes: new Set(id === "nsActiveSlashPill" || id === "nsFloatingTerminal" ? ["hidden"] : []),
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
  "nsAspectWrap", "nsAspectSelect", "nsAspectVal", "nsResWrap", "nsResSelect", "nsResVal",
  "nsFpsWrap", "nsFpsSelect", "nsFpsVal", "nsAudioKindWrap", "nsAudioKindSelect", "nsAudioKindVal",
  "nsMeshTierWrap", "nsMeshTierSelect", "nsMeshTierVal", "nsAtlasTaskWrap", "nsAtlasTaskSelect", "nsAtlasTaskVal",
  "nsAtlasQualWrap", "nsAtlasQualSelect", "nsAtlasQualVal",
  "nsThinkWrap", "nsThinkSelect", "nsThinkVal", "nsThoughtsBtn",
  "nsSearchWrap", "nsSearchSelect", "nsSearchVal", "nsViaVal", "nsViaSelect", "nsRefCounter",
  "nsActiveRunsCount", "nsGenerateBtn", "nsResponseToast",
  "nsSlashRouterPopover", "nsActiveSlashPill", "nsActiveSlashPillText",
  "nsFloatingTerminal", "nsTerminalLog", "nsTerminalInput", "nsTerminalRunBtn",
  "nsTerminalHideBtn", "nsTerminalToggleBtn", "nsTerminalToggleState"
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
  const method = (opts && opts.method) || "GET";
  const body = opts && opts.body ? JSON.parse(opts.body) : null;
  fetchCalls.push({{ url, method, body }});
  if (url === "/api/nodes/generate") {{
    const mod = (body && body.modality) || "image";
    if (mod === "text") {{
      return Promise.resolve({{
        status: 200,
        ok: true,
        json: async () => ({{
          ok: true,
          modality: "text",
          node: {{
            id: "node-txt-1",
            data: {{
              content: {{ text: "A golden retriever floating peacefully through a vibrant nebula." }},
              metadata: {{ model: (body.config && body.config.model) || "gemini-3.1-pro", prompt: body.prompt }}
            }}
          }}
        }})
      }});
    }}
    if (mod === "video") {{
      return Promise.resolve({{
        status: 200,
        ok: true,
        json: async () => ({{
          ok: true,
          modality: "video",
          node: {{
            id: "node-vid-1",
            data: {{
              content: {{ videoUrl: "https://cdn.example.com/dog_space.mp4", fps: 60, text: "Video ready" }},
              metadata: {{ model: "kling-4.0", prompt: body.prompt }}
            }}
          }}
        }})
      }});
    }}
    return Promise.resolve({{
      status: 200,
      ok: true,
      json: async () => ({{
        ok: true,
        modality: "image",
        mode: "MERGE",
        node: {{
          id: "merge-dog-space",
          data: {{
            content: {{
              imageUrl: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg==",
              base64: "iVBORw0KGgoAAAANSUhEUg==",
              mimeType: "image/png",
              text: "Merged dog in space"
            }},
            metadata: {{ model: (body.config && body.config.model) || "gemini-3.1-flash-image", prompt: body.prompt }}
          }}
        }}
      }})
    }});
  }}
  if (url === "/api/omni/route") {{
    const mod = (body && body.modality) || "audio";
    if (mod === "audio") {{
      return Promise.resolve({{
        status: 200,
        ok: true,
        json: async () => ({{
          ok: true,
          result: {{ ok: true, kind: "music", audio_bytes_b64: "UklGRg==", mime_type: "audio/wav", path: "/audio/space_score.wav" }},
          saved_to_space: {{ path: "/audio/space_score.wav" }},
          files_b64: {{ "/audio/space_score.wav": "UklGRg==" }}
        }})
      }});
    }}
    if (mod === "3d") {{
      return Promise.resolve({{
        status: 200,
        ok: true,
        json: async () => ({{
          ok: true,
          result: {{ ok: true, path: "/models3d/space_dog.glb", glb_bytes_b64: "Z2xURg==" }},
          saved_to_space: {{ path: "/models3d/space_dog.glb" }},
          files_b64: {{ "/models3d/space_dog.glb": "Z2xURg==" }}
        }})
      }});
    }}
  }}
  return Promise.resolve({{ status: 200, ok: true, json: async () => ({{ ok: true }}) }});
}};

{script}

(async () => {{
  const api = window.TinCanNodeStudio;
  const out = {{}};

  // 0. Fresh state must NOT default to /atlas splat
  out.initialSlashCmd = api.getState().activeSlashCommand;
  out.initialModality = api.getState().modality;

  // 1. User selects 2 images, switches to Nano Banana 2 (even after touching Atlas!), and merges: "Put this dog in space"
  api.applySlashRoute("/atlas splat");
  api.selectModel("gemini-3.1-flash-image");
  out.slashClearedAfterModelSelect = api.getState().activeSlashCommand;
  out.providerAfterModelSelect = api.getState().provider;

  api.getState().nodes.push(
    {{ id: "img-dog", type: "GENERATED", modality: "image", morphingStatus: "image", label: "Dog", x: 100, y: 100, width: 256, height: 256, content: {{ imageUrl: "data:image/png;base64,RE9H", base64: "RE9H", mimeType: "image/png" }}, metadata: {{}} }},
    {{ id: "img-space", type: "GENERATED", modality: "image", morphingStatus: "image", label: "Space", x: 400, y: 100, width: 256, height: 256, content: {{ imageUrl: "data:image/png;base64,U1BBQ0U=", base64: "U1BBQ0U=", mimeType: "image/png" }}, metadata: {{}} }}
  );
  api.addNodeAsRef("img-dog");
  api.addNodeAsRef("img-space");
  out.mergeModePill = elements.get("nsModePill").textContent;
  elements.get("nsPromptInput").value = "Put this dog in space";
  await api.generate();

  const genCalls = fetchCalls.filter((c) => c.url === "/api/nodes/generate");
  const omniCallsAfterMerge = fetchCalls.filter((c) => c.url === "/api/omni/route");
  const mergedNode = api.getState().nodes[api.getState().nodes.length - 1];
  out.mergeCalledGenerate = genCalls.length === 1;
  out.mergeCalledOmni = omniCallsAfterMerge.length;
  out.mergePayloadModality = genCalls[0].body.modality;
  out.mergePayloadModel = genCalls[0].body.config.model;
  out.mergePayloadRefCount = genCalls[0].body.references.length;
  out.mergeNodeStatus = mergedNode.morphingStatus;

  // 2. Switch to Text modality -> aspect/res hidden, generates readable Text node, -> To Image works
  api.clearSelection();
  api.selectModality("text");
  out.textModalityModel = api.getState().model;
  out.aspectHiddenInText = elements.get("nsAspectWrap").classList.contains("hidden");
  elements.get("nsPromptInput").value = "Write a vivid prompt for a dog in space";
  await api.generate();
  const textNode = api.getState().nodes[api.getState().nodes.length - 1];
  out.textNodeStatus = textNode.morphingStatus;
  out.textNodeHtmlHasActions = elements.get("nsNodesLayer").innerHTML.includes("→ To Image") && elements.get("nsNodesLayer").innerHTML.includes("Copy");
  api.sendTextToImage(textNode.id);
  out.modalityAfterSendToImage = api.getState().modality;
  out.promptAfterSendToImage = elements.get("nsPromptInput").value;

  // 3. Switch to Audio modality -> generates playable <audio controls> card
  api.clearSelection();
  api.selectModality("audio");
  out.audioKindVisible = !elements.get("nsAudioKindWrap").classList.contains("hidden");
  elements.get("nsPromptInput").value = "Ambient synthwave space dog theme";
  await api.generate();
  const audioNode = api.getState().nodes[api.getState().nodes.length - 1];
  out.audioNodeStatus = audioNode.morphingStatus;
  out.audioHasPlayer = elements.get("nsNodesLayer").innerHTML.includes("<audio class=\\"ns-audio-player\\" controls");

  // 4. Switch to Video modality -> generates Video card (NOT a 3D Splat!)
  api.clearSelection();
  api.selectModality("video");
  out.fpsVisibleInVideo = !elements.get("nsFpsWrap").classList.contains("hidden");
  elements.get("nsPromptInput").value = "Slow orbital camera around space dog";
  await api.generate();
  const videoNode = api.getState().nodes[api.getState().nodes.length - 1];
  out.videoNodeStatus = videoNode.morphingStatus;
  out.videoHasPlayer = elements.get("nsNodesLayer").innerHTML.includes("<video class=\\"ns-video-player\\"");

  // 5. Switch to 3D Mesh modality -> generates 3D Mesh .GLB card (NOT a 3D Splat!)
  api.clearSelection();
  api.selectModality("3d");
  out.meshTierVisible = !elements.get("nsMeshTierWrap").classList.contains("hidden");
  elements.get("nsPromptInput").value = "Astronaut corgi figurine";
  await api.generate();
  const meshNode = api.getState().nodes[api.getState().nodes.length - 1];
  out.meshNodeStatus = meshNode.morphingStatus;
  out.meshHasAutoRig = elements.get("nsNodesLayer").innerHTML.includes("Auto-Rig Walk");

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

    assert res["initialSlashCmd"] == ""
    assert res["initialModality"] == "image"
    assert res["slashClearedAfterModelSelect"] == ""
    assert res["providerAfterModelSelect"] == "auto"
    assert res["mergeModePill"] == "MERGE MODE"
    assert res["mergeCalledGenerate"] is True
    assert res["mergeCalledOmni"] == 0, "Merging 2 images with Nano Banana 2 must NEVER route to Atlas/Omni 3D Splat!"
    assert res["mergePayloadModality"] == "image"
    assert res["mergePayloadModel"] == "gemini-3.1-flash-image"
    assert res["mergePayloadRefCount"] == 2
    assert res["mergeNodeStatus"] == "image"

    assert res["textModalityModel"] == "gemini-3.1-pro"
    assert res["aspectHiddenInText"] is True
    assert res["textNodeStatus"] == "text"
    assert res["textNodeHtmlHasActions"] is True
    assert res["modalityAfterSendToImage"] == "image"
    assert "golden retriever" in res["promptAfterSendToImage"]

    assert res["audioKindVisible"] is True
    assert res["audioNodeStatus"] == "audio"
    assert res["audioHasPlayer"] is True

    assert res["fpsVisibleInVideo"] is True
    assert res["videoNodeStatus"] == "video"
    assert res["videoHasPlayer"] is True

    assert res["meshTierVisible"] is True
    assert res["meshNodeStatus"] == "mesh3d"
    assert res["meshHasAutoRig"] is True
