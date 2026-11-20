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


def test_async_media_mesh_modal_chat_and_library_markup_and_compliance() -> None:
    html = render_node_studio_html()
    win_html = render_node_studio_window_html()

    required_ids = (
        "nsMeshViewerModal",
        "nsMeshModalTitle",
        "nsMeshModalMeta",
        "nsMeshModalViewport",
        "nsMeshModalBadge",
        "nsMeshModalWireCanvas",
        "nsMeshModalAutoRotateBtn",
        "nsMeshModalAnimBtn",
        "nsMeshModalDownloadBtn",
        "nsMeshModalCloseBtn",
        "nsChatHeaderMeta",
        "nsChatFeed",
        "nsChatComposer",
        "nsChatInput",
        "nsChatSendBtn",
        "nsLibFilterBar",
        "nsLibSearchInput",
        "nsLibChip-all",
        "nsLibChip-image",
        "nsLibChip-text",
        "nsLibChip-video",
        "nsLibChip-audio",
        "nsLibChip-3d",
        "nsLibChip-atlas",
        "nsLibraryViewGrid",
        "nsBatchWrap",
        "nsBatchVal",
        "nsBatchSelect",
        "nsImageLightboxModal",
        "nsLightboxTitle",
        "nsLightboxMeta",
        "nsLightboxCounter",
        "nsLightboxZoomBtn",
        "nsLightboxUseRefBtn",
        "nsLightboxPopOutBtn",
        "nsLightboxDownloadBtn",
        "nsLightboxCloseBtn",
        "nsLightboxStage",
        "nsLightboxPrevBtn",
        "nsLightboxImg",
        "nsLightboxNextBtn",
        "nsLightboxStrip",
    )
    for dom_id in required_ids:
        assert f'id="{dom_id}"' in html, f"Missing id={dom_id} in standalone HTML"
        assert f'id="{dom_id}"' in win_html, f"Missing id={dom_id} in window HTML"

    for token in (
        '<h2 class="ns-alt-title">Conversation Editor</h2>',
        '<h2 class="ns-alt-title">Asset Library</h2>',
        "https://unpkg.com/@google/model-viewer@3.5.0/dist/model-viewer.min.js",
        "/api/nodes/video/status",
        "/api/nodes/mesh/status",
        "/api/nodes/audio/status",
        "pollAudioJobForNode",
        "pollVideoJobForNode",
        "pollMeshJobForNode",
        "openMeshViewer",
        "closeMeshViewer",
        "toggleMeshModalAutoRotate",
        "toggleMeshModalAnim",
        "sendChatPrompt",
        "focusNodeOnCanvas",
        "setLibraryFilter",
        "setLibrarySearch",
        "renderConversationView",
    ):
        assert token in html
        assert token in win_html

    # Strict Aeonik Celadon & Monochrome Dark Mode compliance
    for doc in (html, win_html):
        assert legacy_palette_classes(doc) == []
        assert celadonize_classes(doc) == doc
        for forbidden in FORBIDDEN_UTILITY_PREFIXES:
            assert forbidden not in doc, f"Forbidden utility prefix {forbidden} found"

    # Zero duplicate IDs inside render_node_studio_window_html() or MESH_OS_HTML_UI
    ns_ids = re.findall(r'(?<![\w-])id="([^"]+)"', win_html)
    assert len(ns_ids) == len(set(ns_ids)), "Duplicate IDs found in render_node_studio_window_html()"
    mesh_counts = Counter(re.findall(r'(?<![\w-])id="([^"]+)"', MESH_OS_HTML_UI))
    duplicates = [eid for eid in ns_ids if mesh_counts[eid] != 1]
    assert duplicates == [], f"Duplicate IDs in MESH_OS_HTML_UI: {duplicates}"


def test_async_video_and_mesh_live_polling_runtime_in_node() -> None:
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
    children: [],
    _classes: new Set(id === "nsMeshViewerModal" || id === "nsSplatViewerModal" || id === "nsResponseToast" ? ["hidden"] : []),
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
    removeAttribute(k) {{ delete el.attributes[k]; }},
    addEventListener() {{}},
    querySelectorAll() {{ return []; }},
    appendChild(child) {{ child.parentNode = el; el.children.push(child); }},
    removeChild(child) {{ el.children = el.children.filter((c) => c !== child); child.parentNode = null; }},
    focus() {{}},
    getBoundingClientRect() {{ return {{ left: 0, top: 0, width: 1200, height: 800 }}; }}
  }};
  return el;
}}
[
  "nsDotCanvas", "nsEmptyState", "nsCanvasWorld", "nsEdgesSvg", "nsNodesLayer",
  "nsSelectionBox", "nsDropOverlay", "nsConversationView", "nsLibraryView",
  "nsLibraryViewGrid", "nsChatHeaderMeta", "nsChatFeed", "nsChatComposer",
  "nsChatInput", "nsChatSendBtn", "nsLibFilterBar", "nsLibSearchInput",
  "nsCopyIndicator", "nsAutoLayoutBtn", "nsShortcutsBtn", "nsShortcutsPopover",
  "nsLeftPillWrap", "nsLeftDrawer", "nsAssetSearchInput", "nsLibAssetGrid",
  "nsLibTemplateList", "nsNewTemplateBtn", "nsModePill", "nsConvPill", "nsBranchPill",
  "nsApiBtn", "nsApiMenu", "nsApiGeminiStatus", "nsApiNanogptStatus", "nsApiSourceText",
  "nsApiClearBtn", "nsGeminiKeyInput", "nsNanogptKeyInput", "nsModelBtn", "nsModelBtnLabel",
  "nsModelMenu", "nsRefsStrip", "nsRefsRow", "nsPromptInput", "nsAttachTrigger", "nsFileInput",
  "nsAspectWrap", "nsAspectSelect", "nsAspectVal", "nsResWrap", "nsResSelect", "nsResVal",
  "nsFpsWrap", "nsFpsSelect", "nsFpsVal", "nsAudioKindWrap", "nsAudioKindSelect", "nsAudioKindVal",
  "nsMeshTierWrap", "nsMeshTierSelect", "nsMeshTierVal", "nsAtlasTaskWrap", "nsAtlasTaskSelect",
  "nsAtlasTaskVal", "nsAtlasQualWrap", "nsAtlasQualSelect", "nsAtlasQualVal",
  "nsThinkWrap", "nsThinkSelect", "nsThinkVal", "nsThoughtsBtn", "nsSearchWrap",
  "nsSearchSelect", "nsSearchVal", "nsViaVal", "nsViaSelect", "nsRefCounter",
  "nsActiveRunsCount", "nsGenerateBtn", "nsResponseToast", "nsSlashRouterPopover",
  "nsActiveSlashPill", "nsActiveSlashPillText", "nsFloatingTerminal", "nsTerminalLog",
  "nsTerminalInput", "nsTerminalRunBtn", "nsTerminalHideBtn", "nsTerminalToggleBtn",
  "nsTerminalToggleState", "nsMeshViewerModal", "nsMeshModalTitle", "nsMeshModalMeta",
  "nsMeshModalViewport", "nsMeshModalBadge", "nsMeshModalWireCanvas",
  "nsMeshModalAutoRotateBtn", "nsMeshModalAnimBtn", "nsMeshModalDownloadBtn", "nsMeshModalCloseBtn"
].forEach((id) => elements.set(id, makeEl(id)));

let timerSeq = 0;
const intervals = new Map();
global.setInterval = (fn, ms) => {{
  timerSeq += 1;
  intervals.set(timerSeq, {{ fn, ms }});
  return timerSeq;
}};
global.clearInterval = (id) => {{ intervals.delete(id); }};

const fetchCalls = [];
const videoPollCounts = {{}};
const meshPollCounts = {{}};
const mockGraphs = new Map();

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
  createElement(tag) {{ const el = makeEl(tag); el.tagName = String(tag || "").toUpperCase(); return el; }},
  body: {{ appendChild() {{}}, removeChild() {{}} }}
}};
global.fetch = (url, opts) => {{
  const method = (opts && opts.method) || "GET";
  const headers = (opts && opts.headers) || {{}};
  const body = opts && opts.body ? JSON.parse(opts.body) : null;
  fetchCalls.push({{ url: String(url), method, headers, body }});

  if (url === "/api/nodes/generate" && body && body.modality === "video") {{
    const isErrJob = String(body.prompt || "").includes("quota fail");
    const jid = isErrJob ? "vid-job-err" : "vid-job-99";
    return Promise.resolve({{
      status: 200,
      ok: true,
      json: async () => ({{
        ok: true,
        async: true,
        done: false,
        job_id: jid,
        model_slug: "kling-4.0",
        node: {{
          id: "n-" + jid,
          data: {{
            content: {{ jobStatus: "RUNNING", fps: 60 }},
            metadata: {{ model: "kling-4.0", jobStatus: "RUNNING", prompt: body.prompt }}
          }}
        }}
      }})
    }});
  }}

  if (String(url).startsWith("/api/nodes/video/status")) {{
    const m = String(url).match(/job_id=([^&]+)/);
    const jid = m ? decodeURIComponent(m[1]) : "";
    videoPollCounts[jid] = (videoPollCounts[jid] || 0) + 1;
    if (jid === "vid-job-err") {{
      return Promise.resolve({{
        status: 200,
        ok: true,
        json: async () => ({{ ok: false, done: true, status: "FAILED", error: "GPU quota exceeded" }})
      }});
    }}
    if (videoPollCounts[jid] === 1) {{
      return Promise.resolve({{
        status: 200,
        ok: true,
        json: async () => ({{ ok: true, done: false, status: "RUNNING" }})
      }});
    }}
    return Promise.resolve({{
      status: 200,
      ok: true,
      json: async () => ({{
        ok: true,
        done: true,
        status: "SUCCEEDED",
        video_url: "/api/space/file?raw=1&scope=user&owner_id=default&path=%2Fvideos%2Fspace_dog.mp4",
        vfs_path: "/videos/space_dog.mp4"
      }})
    }});
  }}

  if (url === "/api/omni/route" && body && body.modality === "3d") {{
    const isErrMesh = String(body.prompt || "").includes("balance fail");
    const jid = isErrMesh ? "mesh-job-err" : "mesh-job-77";
    return Promise.resolve({{
      status: 200,
      ok: true,
      json: async () => ({{
        ok: true,
        async: true,
        done: false,
        job_id: jid,
        result: {{ ok: true, job_id: jid, jobStatus: "RUNNING" }}
      }})
    }});
  }}

  if (String(url).startsWith("/api/nodes/mesh/status")) {{
    const m = String(url).match(/job_id=([^&]+)/);
    const jid = m ? decodeURIComponent(m[1]) : "";
    meshPollCounts[jid] = (meshPollCounts[jid] || 0) + 1;
    if (jid === "mesh-job-err") {{
      return Promise.resolve({{
        status: 200,
        ok: true,
        json: async () => ({{ ok: false, status: "FAILED", error: "Hyper3D balance empty" }})
      }});
    }}
    if (meshPollCounts[jid] === 1) {{
      return Promise.resolve({{
        status: 200,
        ok: true,
        json: async () => ({{ ok: true, done: false, status: "RUNNING" }})
      }});
    }}
    return Promise.resolve({{
      status: 200,
      ok: true,
      json: async () => ({{
        ok: true,
        done: true,
        status: "SUCCEEDED",
        glb_raw_url: "/api/space/file?raw=1&path=%2Fmodels3d%2Ffox.glb",
        glb_bytes_b64: "Z2xURg==",
        vfs_path: "/models3d/fox.glb"
      }})
    }});
  }}

  if (url === "/api/nodes/graph" && method === "POST" && body && body.path) {{
    mockGraphs.set(body.path, body.graph);
    return Promise.resolve({{ status: 200, ok: true, json: async () => ({{ ok: true, path: body.path }}) }});
  }}
  if (String(url).startsWith("/api/nodes/graph?")) {{
    const m = String(url).match(/path=([^&]+)/);
    const p = m ? decodeURIComponent(m[1]) : "";
    if (!mockGraphs.has(p)) return Promise.resolve({{ status: 404, ok: false, json: async () => ({{ ok: false }}) }});
    return Promise.resolve({{ status: 200, ok: true, json: async () => ({{ ok: true, path: p, graph: mockGraphs.get(p) }}) }});
  }}
  return Promise.resolve({{ status: 200, ok: true, json: async () => ({{ ok: true }}) }});
}};

{script}

(async () => {{
  const api = window.TinCanNodeStudio;
  const out = {{}};

  // 1. Async Video RUNNING -> SUCCEEDED hot-swap to <video>
  api.setNanogptKey("sk-nano-live-key");
  api.selectModality("video");
  elements.get("nsPromptInput").value = "Orbit around space dog";
  await api.generate();
  const vidNode = api.getState().nodes[api.getState().nodes.length - 1];
  out.vidInitialStatus = vidNode.metadata.jobStatus;
  out.vidInitialJobId = vidNode.metadata.jobId;
  out.vidInitialHtml = elements.get("nsNodesLayer").innerHTML;
  out.vidTimerActiveAfterSubmit = intervals.has(vidNode._pollTimer);

  // Tick 1: still RUNNING
  await intervals.get(vidNode._pollTimer).fn();
  const firstVidPoll = fetchCalls.find((c) => c.url.startsWith("/api/nodes/video/status"));
  out.vidPollUrl = firstVidPoll ? firstVidPoll.url : "";
  out.vidPollHeaderKey = firstVidPoll && firstVidPoll.headers ? firstVidPoll.headers["X-NanoGPT-Api-Key"] : "";
  out.vidStatusAfterTick1 = vidNode.metadata.jobStatus;

  // Tick 2: SUCCEEDED -> hot-swaps into playable <video>
  await intervals.get(vidNode._pollTimer).fn();
  out.vidStatusAfterTick2 = vidNode.metadata.jobStatus;
  out.vidTimerClearedOnDone = vidNode._pollTimer === null;
  out.vidFinalUrl = vidNode.content.videoUrl;
  out.vidFinalVfsPath = vidNode.content.vfsPath;
  out.vidFinalHtmlHasVideoTag = elements.get("nsNodesLayer").innerHTML.includes('<video class="ns-video-player" controls playsinline loop src="/api/space/file?raw=1');

  // 2. Async Video ERROR handling -> red .ns-omni-error-box
  elements.get("nsPromptInput").value = "Trigger quota fail test";
  await api.generate();
  const vidErrNode = api.getState().nodes[api.getState().nodes.length - 1];
  await intervals.get(vidErrNode._pollTimer).fn();
  out.vidErrStatus = vidErrNode.metadata.jobStatus;
  out.vidErrMsg = vidErrNode.metadata.jobError;
  out.vidErrTimerCleared = vidErrNode._pollTimer === null;
  out.vidErrHtmlHasBox = elements.get("nsNodesLayer").innerHTML.includes("ns-omni-error-box") && elements.get("nsNodesLayer").innerHTML.includes("GPU quota exceeded");

  // 3. Async 3D Mesh RUNNING -> SUCCEEDED with glbRawUrl & glbB64
  const meshNode = await api.runTerminalCommand('/3d "Astronaut fox figurine"');
  out.meshInitialStatus = meshNode.metadata.jobStatus;
  out.meshInitialJobId = meshNode.metadata.jobId;
  out.meshRunningHtmlHasBadge = elements.get("nsNodesLayer").innerHTML.includes("⟳ GENERATING .GLB (");

  await intervals.get(meshNode._pollTimer).fn();
  const firstMeshPoll = fetchCalls.find((c) => c.url.startsWith("/api/nodes/mesh/status"));
  out.meshPollUrl = firstMeshPoll ? firstMeshPoll.url : "";
  out.meshStatusAfterTick1 = meshNode.metadata.jobStatus;

  await intervals.get(meshNode._pollTimer).fn();
  out.meshStatusAfterTick2 = meshNode.metadata.jobStatus;
  out.meshTimerCleared = meshNode._pollTimer === null;
  out.meshGlbRawUrl = meshNode.content.glbRawUrl;
  out.meshGlbB64 = meshNode.content.glbB64;
  out.meshVfsPath = meshNode.content.vfsPath;
  const meshDoneHtml = elements.get("nsNodesLayer").innerHTML;
  out.meshDoneHasStage = meshDoneHtml.includes('class="ns-mesh-stage"') && meshDoneHtml.includes('<model-viewer class="ns-model-viewer"') && meshDoneHtml.includes("⤢ Inspect 3D");

  // 4. Async 3D Mesh ERROR handling
  const meshErrNode = await api.runTerminalCommand('/3d "Trigger balance fail test"');
  await intervals.get(meshErrNode._pollTimer).fn();
  out.meshErrStatus = meshErrNode.metadata.jobStatus;
  out.meshErrMsg = meshErrNode.metadata.jobError;
  out.meshErrTimerCleared = meshErrNode._pollTimer === null;

  // 5. Restoring graph with RUNNING video & mesh3d nodes automatically resumes polling!
  mockGraphs.set("/nodes/resume_test.nodes.json", {{
    schema: "tincan.node_studio.graph.v1",
    name: "resume_test",
    path: "/nodes/resume_test.nodes.json",
    nodes: [
      {{ id: "r-vid", type: "VIDEO", modality: "video", morphingStatus: "video", label: "Resume vid", x: 10, y: 10, width: 320, height: 250, content: {{}}, metadata: {{ jobId: "vid-resume-1", modelSlug: "kling-4.0", jobStatus: "RUNNING" }} }},
      {{ id: "r-mesh", type: "3D", modality: "3d", morphingStatus: "mesh3d", label: "Resume mesh", x: 400, y: 10, width: 320, height: 326, content: {{}}, metadata: {{ jobId: "mesh-resume-1", jobStatus: "RUNNING" }} }}
    ],
    edges: [],
    references: []
  }});
  await api.loadGraphFromSpace("resume_test", false);
  const restoredVid = api.getState().nodes.find((n) => n.id === "r-vid");
  const restoredMesh = api.getState().nodes.find((n) => n.id === "r-mesh");
  out.resumedVidPolling = !!(restoredVid && intervals.has(restoredVid._pollTimer));
  out.resumedMeshPolling = !!(restoredMesh && intervals.has(restoredMesh._pollTimer));

  // Cleanup all intervals cleanly
  api.newBlankGraph();
  out.intervalsRemainingAfterBlank = intervals.size;

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

    assert res["vidInitialStatus"] == "RUNNING"
    assert res["vidInitialJobId"] == "vid-job-99"
    assert "⟳ RENDERING VIDEO (" in res["vidInitialHtml"]
    assert res["vidTimerActiveAfterSubmit"] is True
    assert "job_id=vid-job-99" in res["vidPollUrl"]
    assert "model=kling-4.0" in res["vidPollUrl"]
    assert "scope=user" in res["vidPollUrl"]
    assert res["vidPollHeaderKey"] == "sk-nano-live-key"
    assert res["vidStatusAfterTick1"] == "RUNNING"
    assert res["vidStatusAfterTick2"] == "SUCCEEDED"
    assert res["vidTimerClearedOnDone"] is True
    assert res["vidFinalUrl"].startswith("/api/space/file?raw=1")
    assert res["vidFinalVfsPath"] == "/videos/space_dog.mp4"
    assert res["vidFinalHtmlHasVideoTag"] is True

    assert res["vidErrStatus"] == "ERROR"
    assert res["vidErrMsg"] == "GPU quota exceeded"
    assert res["vidErrTimerCleared"] is True
    assert res["vidErrHtmlHasBox"] is True

    assert res["meshInitialStatus"] == "RUNNING"
    assert res["meshInitialJobId"] == "mesh-job-77"
    assert res["meshRunningHtmlHasBadge"] is True
    assert "job_id=mesh-job-77" in res["meshPollUrl"]
    assert res["meshStatusAfterTick1"] == "RUNNING"
    assert res["meshStatusAfterTick2"] == "SUCCEEDED"
    assert res["meshTimerCleared"] is True
    assert res["meshGlbRawUrl"] == "/api/space/file?raw=1&path=%2Fmodels3d%2Ffox.glb"
    assert res["meshGlbB64"] == "Z2xURg=="
    assert res["meshVfsPath"] == "/models3d/fox.glb"
    assert res["meshDoneHasStage"] is True

    assert res["meshErrStatus"] == "ERROR"
    assert res["meshErrMsg"] == "Hyper3D balance empty"
    assert res["meshErrTimerCleared"] is True

    assert res["resumedVidPolling"] is True
    assert res["resumedMeshPolling"] is True
    assert res["intervalsRemainingAfterBlank"] == 0


def test_inline_3d_mesh_viewer_modal_and_synced_chat_library_in_node() -> None:
    node_bin = shutil.which("node")
    if not node_bin:
        pytest.skip("node binary not available for JS runtime check")

    html = render_node_studio_html()
    script = _extract_inline_script(html)

    harness = f"""
const elements = new Map();
const docListeners = {{}};
function makeEl(id) {{
  const el = {{
    id,
    tagName: "DIV",
    textContent: "",
    innerHTML: "",
    value: "",
    placeholder: "",
    disabled: false,
    dataset: {{}},
    style: {{}},
    attributes: {{}},
    scrollHeight: 50,
    children: [],
    _classes: new Set(id === "nsMeshViewerModal" || id === "nsSplatViewerModal" || id === "nsConversationView" || id === "nsLibraryView" ? ["hidden"] : []),
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
    removeAttribute(k) {{ delete el.attributes[k]; }},
    addEventListener() {{}},
    querySelectorAll() {{ return []; }},
    appendChild(child) {{ child.parentNode = el; el.children.push(child); }},
    removeChild(child) {{ el.children = el.children.filter((c) => c !== child); child.parentNode = null; }},
    focus() {{}},
    getBoundingClientRect() {{ return {{ left: 0, top: 0, width: 1200, height: 800 }}; }}
  }};
  return el;
}}
[
  "nsDotCanvas", "nsEmptyState", "nsCanvasWorld", "nsEdgesSvg", "nsNodesLayer",
  "nsSelectionBox", "nsDropOverlay", "nsConversationView", "nsLibraryView",
  "nsLibraryViewGrid", "nsChatHeaderMeta", "nsChatFeed", "nsChatComposer",
  "nsChatInput", "nsChatSendBtn", "nsLibFilterBar", "nsLibSearchInput",
  "nsCopyIndicator", "nsAutoLayoutBtn", "nsShortcutsBtn", "nsShortcutsPopover",
  "nsLeftPillWrap", "nsLeftDrawer", "nsAssetSearchInput", "nsLibAssetGrid",
  "nsLibTemplateList", "nsNewTemplateBtn", "nsModePill", "nsConvPill", "nsBranchPill",
  "nsApiBtn", "nsApiMenu", "nsApiGeminiStatus", "nsApiNanogptStatus", "nsApiSourceText",
  "nsApiClearBtn", "nsGeminiKeyInput", "nsNanogptKeyInput", "nsModelBtn", "nsModelBtnLabel",
  "nsModelMenu", "nsRefsStrip", "nsRefsRow", "nsPromptInput", "nsAttachTrigger", "nsFileInput",
  "nsAspectWrap", "nsAspectSelect", "nsAspectVal", "nsResWrap", "nsResSelect", "nsResVal",
  "nsFpsWrap", "nsFpsSelect", "nsFpsVal", "nsAudioKindWrap", "nsAudioKindSelect", "nsAudioKindVal",
  "nsMeshTierWrap", "nsMeshTierSelect", "nsMeshTierVal", "nsAtlasTaskWrap", "nsAtlasTaskSelect",
  "nsAtlasTaskVal", "nsAtlasQualWrap", "nsAtlasQualSelect", "nsAtlasQualVal",
  "nsThinkWrap", "nsThinkSelect", "nsThinkVal", "nsThoughtsBtn", "nsSearchWrap",
  "nsSearchSelect", "nsSearchVal", "nsViaVal", "nsViaSelect", "nsRefCounter",
  "nsActiveRunsCount", "nsGenerateBtn", "nsResponseToast", "nsSlashRouterPopover",
  "nsActiveSlashPill", "nsActiveSlashPillText", "nsFloatingTerminal", "nsTerminalLog",
  "nsTerminalInput", "nsTerminalRunBtn", "nsTerminalHideBtn", "nsTerminalToggleBtn",
  "nsTerminalToggleState", "nsSplatViewerModal", "nsMeshViewerModal", "nsMeshModalTitle",
  "nsMeshModalMeta", "nsMeshModalViewport", "nsMeshModalBadge", "nsMeshModalWireCanvas",
  "nsMeshModalAutoRotateBtn", "nsMeshModalAnimBtn", "nsMeshModalDownloadBtn", "nsMeshModalCloseBtn"
].forEach((id) => elements.set(id, makeEl(id)));

const revokedUrls = [];
const origCreateObjectURL = global.URL && global.URL.createObjectURL;
const origRevokeObjectURL = global.URL && global.URL.revokeObjectURL;
if (global.URL) {{
  global.URL.createObjectURL = (blob) => "blob:mock-" + (blob ? blob.size : 0) + "-" + Math.random().toString(16).slice(2, 6);
  global.URL.revokeObjectURL = (u) => {{ revokedUrls.push(u); }};
}}

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
  addEventListener(type, fn) {{
    if (!docListeners[type]) docListeners[type] = [];
    docListeners[type].push(fn);
  }},
  createElement(tag) {{
    const el = makeEl(tag);
    el.tagName = String(tag || "").toUpperCase();
    return el;
  }},
  body: {{ appendChild() {{}}, removeChild() {{}} }}
}};
global.fetch = (url, opts) => {{
  const body = opts && opts.body ? JSON.parse(opts.body) : null;
  if (url === "/api/nodes/generate") {{
    return Promise.resolve({{
      status: 200,
      ok: true,
      json: async () => ({{
        ok: true,
        modality: body.modality || "text",
        node: {{
          id: "chat-gen-1",
          data: {{
            content: {{ text: "Golden sunset rim lighting across the alpine ridge." }},
            metadata: {{ model: (body.config && body.config.model) || "gemini-3.1-pro", prompt: body.prompt }}
          }}
        }}
      }})
    }});
  }}
  return Promise.resolve({{ status: 200, ok: true, json: async () => ({{ ok: true }}) }});
}};

{script}

(async () => {{
  const api = window.TinCanNodeStudio;
  const st = api.getState();
  const out = {{}};

  // Seed diverse multi-modal DAG: root-img -> mid-text -> leaf-audio, plus unrelated other-video & rigged-mesh
  st.nodes.push(
    {{
      id: "root-img", type: "GENERATED", modality: "image", morphingStatus: "image",
      label: "Alpine shrine concept", x: 100, y: 100, width: 256, height: 256,
      content: {{ imageUrl: "data:image/png;base64,iVBORw0KGgo=" }},
      metadata: {{ model: "gemini-nano-banana-2.1", prompt: "Alpine shrine concept" }}
    }},
    {{
      id: "mid-text", type: "TEXT", modality: "text", morphingStatus: "text",
      label: "Shrine storyboard script", x: 100, y: 400, width: 320, height: 220,
      content: {{ text: "Act I: Mist rises slowly around the vermilion pillars." }},
      metadata: {{ model: "gemini-3.1-pro", prompt: "Write Act I beat for shrine" }}
    }},
    {{
      id: "leaf-audio", type: "AUDIO", modality: "audio", morphingStatus: "audio",
      label: "Ambient koto score", x: 100, y: 700, width: 310, height: 218,
      content: {{ kind: "music", audioUrl: "data:audio/wav;base64,UklGRg==", vfsPath: "/audio/koto.wav" }},
      metadata: {{ model: "google/lyria-3.5", prompt: "Ambient koto score" }}
    }},
    {{
      id: "other-video", type: "VIDEO", modality: "video", morphingStatus: "video",
      label: "Unrelated drone flyby", x: 520, y: 100, width: 320, height: 250,
      content: {{ videoUrl: "https://cdn.example.com/drone.mp4", fps: 60 }},
      metadata: {{ model: "kling-4.0", prompt: "Unrelated drone flyby" }}
    }},
    {{
      id: "rigged-mesh", type: "3D", modality: "3d", morphingStatus: "mesh3d",
      label: "Shrine guardian fox statue", x: 520, y: 420, width: 320, height: 326,
      content: {{ glbB64: "Z2xURg==", glbPath: "/models3d/fox_rigged.glb", rigged: true, animation: "walk" }},
      metadata: {{ model: "hyper3d/rodin-v2.5", prompt: "Shrine guardian fox statue" }}
    }}
  );
  st.edges.push(
    {{ id: "e1", source: "root-img", target: "mid-text" }},
    {{ id: "e2", source: "mid-text", target: "leaf-audio" }}
  );
  api.selectModality("text");

  // 1. Inline 3D Mesh card preview + Blob URL caching + Fullscreen Modal + Esc close
  api.switchView("nodes");
  api.renderConversationView();
  api.renderLibraryViewGrid();
  api.focusNodeOnCanvas("rigged-mesh");
  const meshNode = st.nodes.find((n) => n.id === "rigged-mesh");
  const nodesHtml = elements.get("nsNodesLayer").innerHTML;
  out.meshCardHasStage = nodesHtml.includes('class="ns-mesh-stage"') && nodesHtml.includes('class="ns-model-viewer"') && nodesHtml.includes('class="ns-mesh-wire-canvas"');
  out.meshCardHasRigControls = nodesHtml.includes("✓ RIGGED (walk)") && nodesHtml.includes("Pause Anim") && nodesHtml.includes("⤢ Inspect 3D");
  out.meshBlobCreated = typeof meshNode._glbBlobUrl === "string" && meshNode._glbBlobUrl.startsWith("blob:");

  api.openMeshViewer("rigged-mesh");
  out.meshModalOpen = !elements.get("nsMeshViewerModal").classList.contains("hidden");
  out.meshModalTitle = elements.get("nsMeshModalTitle").textContent;
  out.meshModalAnimBtnVisible = !elements.get("nsMeshModalAnimBtn").classList.contains("hidden");
  out.meshModalHasModelViewerChild = elements.get("nsMeshModalViewport").children.some((c) => c.tagName === "MODEL-VIEWER");

  api.toggleMeshModalAnim();
  out.meshModalAnimLabelAfterPause = elements.get("nsMeshModalAnimBtn").textContent;
  api.toggleMeshModalAutoRotate();
  out.meshModalAutoRotateActive = elements.get("nsMeshModalAutoRotateBtn").classList.contains("is-active");

  // Esc closes the 3D Mesh Inspector Modal
  (docListeners.keydown || []).forEach((fn) => fn({{ key: "Escape", preventDefault() {{}} }}));
  out.meshModalClosedOnEsc = elements.get("nsMeshViewerModal").classList.contains("hidden");

  // 2. Synced Chat View: full session when nothing selected, lineage-only when leaf-audio selected
  api.clearSelection();
  api.switchView("conversation");
  const allChatHtml = elements.get("nsChatFeed").innerHTML;
  out.chatAllShowsAll5 =
    allChatHtml.includes("Alpine shrine concept") &&
    allChatHtml.includes("Act I: Mist rises") &&
    allChatHtml.includes("<audio class=\\"ns-audio-player\\" controls") &&
    allChatHtml.includes("<video class=\\"ns-video-player\\" controls") &&
    allChatHtml.includes("Shrine guardian fox statue");

  st.selectedIds = ["leaf-audio"];
  api.renderConversationView();
  const lineageHtml = elements.get("nsChatFeed").innerHTML;
  out.chatLineageHeader = elements.get("nsChatHeaderMeta").textContent;
  out.chatLineageHasRootMidLeaf =
    lineageHtml.includes("root-img") &&
    lineageHtml.includes("mid-text") &&
    lineageHtml.includes("leaf-audio");
  out.chatLineageExcludesUnrelated = !lineageHtml.includes("other-video") && !lineageHtml.includes("rigged-mesh");
  out.chatLineageOrderCorrect =
    lineageHtml.indexOf("root-img") < lineageHtml.indexOf("mid-text") &&
    lineageHtml.indexOf("mid-text") < lineageHtml.indexOf("leaf-audio");

  // Submitting #nsChatInput via sendChatPrompt delegates cleanly to generate() & updates #nsChatFeed
  api.selectModality("text");
  elements.get("nsChatInput").value = "Describe the lighting";
  await api.sendChatPrompt();
  out.chatInputCleared = elements.get("nsChatInput").value === "";
  out.chatFeedUpdatedWithNewTurn = elements.get("nsChatFeed").innerHTML.includes("Golden sunset rim lighting");

  // Focus on Canvas from Chat switches back to Editor and selects target node
  api.focusNodeOnCanvas("mid-text");
  out.viewAfterFocus = st.view;
  out.selectedAfterFocus = st.selectedIds.slice();

  // 3. Synced Library View: modality filter chips + search + actions + Blob URL revocation on deleteNode
  api.switchView("library");
  const libAllHtml = elements.get("nsLibraryViewGrid").innerHTML;
  out.libHasActions = libAllHtml.includes(">Focus</button>") && libAllHtml.includes(">+ Ref</button>") && libAllHtml.includes(">↓</button>") && libAllHtml.includes(">×</button>");

  api.setLibraryFilter("audio");
  const libAudioHtml = elements.get("nsLibraryViewGrid").innerHTML;
  out.libAudioFilterWorks = libAudioHtml.includes("leaf-audio") && !libAudioHtml.includes("root-img") && !libAudioHtml.includes("other-video");

  api.setLibraryFilter("3d");
  const lib3dHtml = elements.get("nsLibraryViewGrid").innerHTML;
  out.lib3dFilterWorks = lib3dHtml.includes("rigged-mesh") && !lib3dHtml.includes("leaf-audio");

  api.setLibraryFilter("all");
  api.setLibrarySearch("lighting");
  const libSearchHtml = elements.get("nsLibraryViewGrid").innerHTML;
  out.libSearchWorks = libSearchHtml.includes("Describe the lighting") && !libSearchHtml.includes("other-video");

  // Deleting rigged-mesh revokes its cached Blob URL cleanly
  const prevBlob = meshNode._glbBlobUrl;
  api.deleteNode("rigged-mesh");
  out.meshBlobRevokedOnDelete = revokedUrls.includes(prevBlob);

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

    assert res["meshCardHasStage"] is True
    assert res["meshCardHasRigControls"] is True
    assert res["meshBlobCreated"] is True
    assert res["meshModalOpen"] is True
    assert "3D MESH INSPECTOR (.GLB)" in res["meshModalTitle"]
    assert res["meshModalAnimBtnVisible"] is True
    assert res["meshModalHasModelViewerChild"] is True
    assert "Play Anim" in res["meshModalAnimLabelAfterPause"]
    assert res["meshModalAutoRotateActive"] is False
    assert res["meshModalClosedOnEsc"] is True

    assert res["chatAllShowsAll5"] is True
    assert "Branch lineage · 3 turns" in res["chatLineageHeader"]
    assert res["chatLineageHasRootMidLeaf"] is True
    assert res["chatLineageExcludesUnrelated"] is True
    assert res["chatLineageOrderCorrect"] is True
    assert res["chatInputCleared"] is True
    assert res["chatFeedUpdatedWithNewTurn"] is True
    assert res["viewAfterFocus"] == "nodes"
    assert res["selectedAfterFocus"] == ["mid-text"]

    assert res["libHasActions"] is True
    assert res["libAudioFilterWorks"] is True
    assert res["lib3dFilterWorks"] is True
    assert res["libSearchWorks"] is True
    assert res["meshBlobRevokedOnDelete"] is True


def test_async_audio_polling_streaming_and_upload_in_node() -> None:
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
    tagName: "DIV",
    textContent: "",
    innerHTML: "",
    value: "",
    placeholder: "",
    disabled: false,
    dataset: {{}},
    style: {{}},
    attributes: {{}},
    scrollHeight: 50,
    children: [],
    _classes: new Set(id === "nsMeshViewerModal" || id === "nsSplatViewerModal" || id === "nsResponseToast" ? ["hidden"] : []),
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
    removeAttribute(k) {{ delete el.attributes[k]; }},
    addEventListener() {{}},
    querySelectorAll() {{ return []; }},
    appendChild(child) {{ child.parentNode = el; el.children.push(child); }},
    removeChild(child) {{ el.children = el.children.filter((c) => c !== child); child.parentNode = null; }},
    focus() {{}},
    getBoundingClientRect() {{ return {{ left: 0, top: 0, width: 1200, height: 800 }}; }}
  }};
  return el;
}}
[
  "nsDotCanvas", "nsEmptyState", "nsCanvasWorld", "nsEdgesSvg", "nsNodesLayer",
  "nsSelectionBox", "nsDropOverlay", "nsConversationView", "nsLibraryView",
  "nsLibraryViewGrid", "nsChatHeaderMeta", "nsChatFeed", "nsChatComposer",
  "nsChatInput", "nsChatSendBtn", "nsLibFilterBar", "nsLibSearchInput",
  "nsCopyIndicator", "nsAutoLayoutBtn", "nsShortcutsBtn", "nsShortcutsPopover",
  "nsLeftPillWrap", "nsLeftDrawer", "nsAssetSearchInput", "nsLibAssetGrid",
  "nsLibTemplateList", "nsNewTemplateBtn", "nsModePill", "nsConvPill", "nsBranchPill",
  "nsApiBtn", "nsApiMenu", "nsApiGeminiStatus", "nsApiNanogptStatus", "nsApiSourceText",
  "nsApiClearBtn", "nsGeminiKeyInput", "nsNanogptKeyInput", "nsModelBtn", "nsModelBtnLabel",
  "nsModelMenu", "nsRefsStrip", "nsRefsRow", "nsPromptInput", "nsAttachTrigger", "nsFileInput",
  "nsAspectWrap", "nsAspectSelect", "nsAspectVal", "nsResWrap", "nsResSelect", "nsResVal",
  "nsFpsWrap", "nsFpsSelect", "nsFpsVal", "nsAudioKindWrap", "nsAudioKindSelect", "nsAudioKindVal",
  "nsMeshTierWrap", "nsMeshTierSelect", "nsMeshTierVal", "nsAtlasTaskWrap", "nsAtlasTaskSelect",
  "nsAtlasTaskVal", "nsAtlasQualWrap", "nsAtlasQualSelect", "nsAtlasQualVal",
  "nsThinkWrap", "nsThinkSelect", "nsThinkVal", "nsThoughtsBtn", "nsSearchWrap",
  "nsSearchSelect", "nsSearchVal", "nsViaVal", "nsViaSelect", "nsRefCounter",
  "nsActiveRunsCount", "nsGenerateBtn", "nsResponseToast", "nsSlashRouterPopover",
  "nsActiveSlashPill", "nsActiveSlashPillText", "nsFloatingTerminal", "nsTerminalLog",
  "nsTerminalInput", "nsTerminalRunBtn", "nsTerminalHideBtn", "nsTerminalToggleBtn",
  "nsTerminalToggleState"
].forEach((id) => elements.set(id, makeEl(id)));

let timerSeq = 0;
const intervals = new Map();
global.setInterval = (fn, ms) => {{ timerSeq += 1; intervals.set(timerSeq, {{ fn, ms }}); return timerSeq; }};
global.clearInterval = (id) => {{ intervals.delete(id); }};

const fetchCalls = [];
const audioPollCounts = {{}};
const mockGraphs = new Map();

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
  createElement(tag) {{ const el = makeEl(tag); el.tagName = String(tag || "").toUpperCase(); return el; }},
  body: {{ appendChild() {{}}, removeChild() {{}} }}
}};
global.fetch = (url, opts) => {{
  const headers = (opts && opts.headers) || {{}};
  const body = opts && opts.body ? JSON.parse(opts.body) : null;
  fetchCalls.push({{ url: String(url), headers, body }});

  if (url === "/api/omni/route" && body && body.modality === "audio") {{
    const isErr = String(body.prompt || "").includes("quota fail");
    const jid = isErr ? "aud-job-err" : "aud-job-55";
    return Promise.resolve({{
      status: 200,
      ok: true,
      json: async () => ({{
        ok: true,
        async: true,
        done: false,
        status: "RUNNING",
        job_id: jid,
        model: "google/lyria-3.5",
        cost: 0.11,
        payment_source: "USD",
        result: {{ ok: true, async: true, done: false, status: "RUNNING", job_id: jid, kind: "music" }}
      }})
    }});
  }}
  if (String(url).startsWith("/api/nodes/audio/status")) {{
    const m = String(url).match(/job_id=([^&]+)/);
    const jid = m ? decodeURIComponent(m[1]) : "";
    audioPollCounts[jid] = (audioPollCounts[jid] || 0) + 1;
    if (jid === "aud-job-err") {{
      return Promise.resolve({{
        status: 200,
        ok: true,
        json: async () => ({{ ok: false, done: true, status: "FAILED", error: "NanoGPT Lyria balance empty" }})
      }});
    }}
    if (audioPollCounts[jid] === 1) {{
      return Promise.resolve({{
        status: 200,
        ok: true,
        json: async () => ({{ ok: true, done: false, status: "RUNNING" }})
      }});
    }}
    return Promise.resolve({{
      status: 200,
      ok: true,
      json: async () => ({{
        ok: true,
        done: true,
        status: "SUCCEEDED",
        audio_url: "/api/space/file?raw=1&scope=user&owner_id=default&path=%2Faudio%2Fmusic_koto.mp3",
        audio_raw_url: "/api/space/file?raw=1&scope=user&owner_id=default&path=%2Faudio%2Fmusic_koto.mp3",
        vfs_path: "/audio/music_koto.mp3",
        mime_type: "audio/mpeg",
        ext: ".mp3"
      }})
    }});
  }}
  if (String(url).startsWith("/api/nodes/graph?")) {{
    const m = String(url).match(/path=([^&]+)/);
    const p = m ? decodeURIComponent(m[1]) : "";
    return Promise.resolve({{ status: 200, ok: true, json: async () => ({{ ok: true, path: p, graph: mockGraphs.get(p) }}) }});
  }}
  return Promise.resolve({{ status: 200, ok: true, json: async () => ({{ ok: true }}) }});
}};

{script}

(async () => {{
  const api = window.TinCanNodeStudio;
  const out = {{}};

  api.setNanogptKey("sk-nano-audio-key");
  api.selectModality("audio");
  elements.get("nsPromptInput").value = "Warm lo-fi synthwave skyline";
  await api.generate();
  const audNode = api.getState().nodes[api.getState().nodes.length - 1];
  out.initialStatus = audNode.metadata.jobStatus;
  out.initialJobId = audNode.metadata.jobId;
  out.runningBadge = elements.get("nsNodesLayer").innerHTML.includes("⟳ GENERATING AUDIO (");
  out.timerActive = intervals.has(audNode._pollTimer);

  // Tick 1: still RUNNING
  await intervals.get(audNode._pollTimer).fn();
  const firstPoll = fetchCalls.find((c) => c.url.startsWith("/api/nodes/audio/status"));
  out.pollUrl = firstPoll ? firstPoll.url : "";
  out.pollKeyHeader = firstPoll && firstPoll.headers ? firstPoll.headers["X-NanoGPT-Api-Key"] : "";
  out.statusAfterTick1 = audNode.metadata.jobStatus;

  // Tick 2: SUCCEEDED -> hot-swaps into streaming <audio controls preload="metadata" src="/api/space/file?raw=1..."> + ↓ .MP3
  await intervals.get(audNode._pollTimer).fn();
  out.statusAfterTick2 = audNode.metadata.jobStatus;
  out.timerCleared = audNode._pollTimer === null;
  out.finalAudioSrc = audNode.content.audioRawUrl;
  const doneHtml = elements.get("nsNodesLayer").innerHTML;
  out.hasStreamingAudioTag = doneHtml.includes('<audio class="ns-audio-player" controls preload="metadata" src="/api/space/file?raw=1');
  out.hasMp3DownloadBtn = doneHtml.includes("↓ .MP3");

  // Error job -> .ns-omni-error-box
  elements.get("nsPromptInput").value = "Trigger quota fail audio";
  await api.generate();
  const errNode = api.getState().nodes[api.getState().nodes.length - 1];
  await intervals.get(errNode._pollTimer).fn();
  out.errStatus = errNode.metadata.jobStatus;
  out.errHtmlHasBox = elements.get("nsNodesLayer").innerHTML.includes("NanoGPT Lyria balance empty");

  // Uploading local .mp3 file via attach spawns playable AUDIO card + ♪ AUDIO ref chip
  api.handleFilesSelected([
    {{ name: "demo_track.mp3", type: "audio/mpeg", size: 4096, url: "data:audio/mpeg;base64,SUQz" }}
  ]);
  const upNode = api.getState().nodes[api.getState().nodes.length - 1];
  out.uploadedAudioModality = upNode.morphingStatus;
  out.uploadedAudioHasMp3Tag = elements.get("nsNodesLayer").innerHTML.includes("demo_track.mp3");
  out.uploadedAudioRefChip = elements.get("nsRefsRow").innerHTML.includes("♪ AUDIO");

  // Graph reload resumes RUNNING audio polling cleanly
  mockGraphs.set("/nodes/audio_resume.nodes.json", {{
    schema: "tincan.node_studio.graph.v1",
    name: "audio_resume",
    path: "/nodes/audio_resume.nodes.json",
    nodes: [
      {{ id: "r-aud", type: "AUDIO", modality: "audio", morphingStatus: "audio", label: "Resume aud", x: 10, y: 10, width: 320, height: 256, content: {{ kind: "music" }}, metadata: {{ jobId: "aud-resume-1", model: "google/lyria-3.5", jobStatus: "RUNNING" }} }}
    ],
    edges: [],
    references: []
  }});
  await api.loadGraphFromSpace("audio_resume", false);
  const restoredAud = api.getState().nodes.find((n) => n.id === "r-aud");
  out.resumedAudioPolling = !!(restoredAud && intervals.has(restoredAud._pollTimer));
  api.newBlankGraph();
  out.intervalsLeft = intervals.size;

  console.log(JSON.stringify(out));
}})();
"""
    run_res = subprocess.run([node_bin, "-e", harness], text=True, capture_output=True, check=False)
    assert run_res.returncode == 0, f"Node runtime failed: {run_res.stderr}"
    res = json.loads(run_res.stdout.strip())

    assert res["initialStatus"] == "RUNNING"
    assert res["initialJobId"] == "aud-job-55"
    assert res["runningBadge"] is True
    assert res["timerActive"] is True
    assert "job_id=aud-job-55" in res["pollUrl"]
    assert "cost=0.11" in res["pollUrl"]
    assert "payment_source=USD" in res["pollUrl"]
    assert res["pollKeyHeader"] == "sk-nano-audio-key"
    assert res["statusAfterTick1"] == "RUNNING"
    assert res["statusAfterTick2"] == "SUCCEEDED"
    assert res["timerCleared"] is True
    assert res["finalAudioSrc"].startswith("/api/space/file?raw=1")
    assert res["hasStreamingAudioTag"] is True
    assert res["hasMp3DownloadBtn"] is True
    assert res["errStatus"] == "ERROR"
    assert res["errHtmlHasBox"] is True
    assert res["uploadedAudioModality"] == "audio"
    assert res["uploadedAudioHasMp3Tag"] is True
    assert res["uploadedAudioRefChip"] is True
    assert res["resumedAudioPolling"] is True
    assert res["intervalsLeft"] == 0


def test_smooth_damped_wheel_zoom_and_cursor_anchoring_in_node() -> None:
    node_bin = shutil.which("node")
    if not node_bin:
        pytest.skip("node binary not available for JS runtime check")

    html = render_node_studio_html()
    script = _extract_inline_script(html)

    harness = f"""
const elements = new Map();
const listeners = new Map();
function makeEl(id) {{
  const el = {{
    id,
    tagName: "DIV",
    textContent: "",
    innerHTML: "",
    value: "",
    style: {{}},
    dataset: {{}},
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
    setAttribute() {{}},
    addEventListener(type, fn) {{
      if (!listeners.has(id)) listeners.set(id, {{}});
      if (!listeners.get(id)[type]) listeners.get(id)[type] = [];
      listeners.get(id)[type].push(fn);
    }},
    querySelectorAll() {{ return []; }},
    getBoundingClientRect() {{ return {{ left: 0, top: 0, width: 1200, height: 800 }}; }}
  }};
  return el;
}}
[
  "nsDotCanvas", "nsEmptyState", "nsCanvasWorld", "nsEdgesSvg", "nsNodesLayer",
  "nsSelectionBox", "nsDropOverlay", "nsRefsStrip", "nsRefsRow", "nsPromptInput",
  "nsModelBtnLabel", "nsModePill", "nsRefCounter", "nsActiveRunsCount", "nsGenerateBtn"
].forEach((id) => elements.set(id, makeEl(id)));

global.window = {{ innerWidth: 1200, innerHeight: 800, location: {{ href: "http://localhost:8013/nodes", search: "" }}, addEventListener() {{}} }};
global.document = {{
  readyState: "complete",
  getElementById(id) {{ return elements.get(id) || null; }},
  querySelectorAll() {{ return []; }},
  addEventListener() {{}},
  createElement(tag) {{ return makeEl(tag); }},
  body: {{ appendChild() {{}}, removeChild() {{}} }}
}};
global.fetch = () => Promise.resolve({{ status: 200, ok: true, json: async () => ({{ ok: true }}) }});

{script}

const api = window.TinCanNodeStudio;
const st = api.getState();
const wheelFns = (listeners.get("nsDotCanvas") || {{}}).wheel || [];
const fireWheel = (ev) => wheelFns.forEach((fn) => fn(Object.assign({{ preventDefault() {{}}, target: {{}} }}, ev)));

// 1. 20 tiny Mac trackpad ticks (-4px each = -80px total) should zoom smoothly by ~10%, NOT 500%!
st.zoom = 1; st.panX = 0; st.panY = 0;
for (let i = 0; i < 20; i++) {{
  fireWheel({{ deltaY: -4, deltaX: 0, deltaMode: 0, clientX: 600, clientY: 400 }});
}}
const afterTrackpadZoom = st.zoom;
const afterTrackpadPanX = st.panX;
const afterTrackpadPanY = st.panY;

// 2. Horizontal two-finger swipe pans panX instead of zooming
const zoomBeforeHoriz = st.zoom;
const panXBeforeHoriz = st.panX;
fireWheel({{ deltaX: 40, deltaY: 2, deltaMode: 0, clientX: 600, clientY: 400 }});
const zoomAfterHoriz = st.zoom;
const panXAfterHoriz = st.panX;

// 3. Scrolling inside an overflowing .ns-text-body does NOT zoom the canvas
let preventedInsideScrollable = false;
const zoomBeforeTextScroll = st.zoom;
fireWheel({{
  deltaY: 40, deltaX: 0, deltaMode: 0, clientX: 300, clientY: 300,
  preventDefault() {{ preventedInsideScrollable = true; }},
  target: {{ closest() {{ return {{ scrollHeight: 400, clientHeight: 120 }}; }} }}
}});
const zoomAfterTextScroll = st.zoom;

console.log(JSON.stringify({{
  afterTrackpadZoom,
  afterTrackpadPanX,
  afterTrackpadPanY,
  zoomBeforeHoriz,
  zoomAfterHoriz,
  panXBeforeHoriz,
  panXAfterHoriz,
  preventedInsideScrollable,
  zoomBeforeTextScroll,
  zoomAfterTextScroll
}}));
"""
    run_res = subprocess.run([node_bin, "-e", harness], text=True, capture_output=True, check=False)
    assert run_res.returncode == 0, f"Node runtime failed: {run_res.stderr}"
    res = json.loads(run_res.stdout.strip())

    # 20 x -4px = -80px -> exp(80 * 0.0012) ~= 1.1008 (smooth ~10% zoom, nowhere near old 1.08^20 = 4.66x!)
    assert 1.06 <= res["afterTrackpadZoom"] <= 1.15, f"Unexpected trackpad zoom: {res['afterTrackpadZoom']}"
    # Cursor-anchored around (600, 400) -> pan shifts negative to keep cursor point pinned
    assert res["afterTrackpadPanX"] < 0
    assert res["afterTrackpadPanY"] < 0
    # Horizontal swipe pans instead of zooming
    assert res["zoomAfterHoriz"] == res["zoomBeforeHoriz"]
    assert res["panXAfterHoriz"] < res["panXBeforeHoriz"]
    # Scrollable text card scrolls natively without zooming canvas
    assert res["preventedInsideScrollable"] is False
    assert res["zoomAfterTextScroll"] == res["zoomBeforeTextScroll"]


def test_smart_node_placement_auto_layout_and_text_error_in_node() -> None:
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
    tagName: "DIV",
    textContent: "",
    innerHTML: "",
    value: "",
    style: {{}},
    dataset: {{}},
    _classes: new Set(id === "nsResponseToast" ? ["hidden"] : []),
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
    setAttribute() {{}},
    addEventListener() {{}},
    querySelectorAll() {{ return []; }},
    getBoundingClientRect() {{ return {{ left: 0, top: 0, width: 1200, height: 800 }}; }}
  }};
  return el;
}}
[
  "nsDotCanvas", "nsEmptyState", "nsCanvasWorld", "nsEdgesSvg", "nsNodesLayer",
  "nsSelectionBox", "nsDropOverlay", "nsRefsStrip", "nsRefsRow", "nsPromptInput",
  "nsModelBtnLabel", "nsModePill", "nsRefCounter", "nsActiveRunsCount", "nsGenerateBtn",
  "nsResponseToast", "nsAutoLayoutBtn"
].forEach((id) => elements.set(id, makeEl(id)));

let resolvePendingGen = null;
global.window = {{ innerWidth: 1200, innerHeight: 800, location: {{ href: "http://localhost:8013/nodes", search: "" }}, addEventListener() {{}} }};
global.document = {{
  readyState: "complete",
  getElementById(id) {{ return elements.get(id) || null; }},
  querySelectorAll() {{ return []; }},
  addEventListener() {{}},
  createElement(tag) {{ return makeEl(tag); }},
  body: {{ appendChild() {{}}, removeChild() {{}} }}
}};
global.fetch = (url, opts) => {{
  const body = opts && opts.body ? JSON.parse(opts.body) : null;
  if (url === "/api/nodes/generate") {{
    if (body && String(body.prompt || "").includes("trigger_400")) {{
      return Promise.resolve({{
        status: 400,
        ok: false,
        json: async () => ({{ ok: false, error: "Upstream chat model error" }})
      }});
    }}
    if (body && String(body.prompt || "").includes("deferred_child")) {{
      return new Promise((resolve) => {{
        resolvePendingGen = () => resolve({{
          status: 200,
          ok: true,
          json: async () => ({{
            ok: true,
            modality: "text",
            node: {{
              id: "gen-txt-1",
              data: {{
                content: {{ text: "Real LLM output grounded in parent." }},
                metadata: {{ model: "gemini-3.1-pro", prompt: body.prompt }}
              }}
            }}
          }})
        }});
      }});
    }}
    return Promise.resolve({{
      status: 200,
      ok: true,
      json: async () => ({{
        ok: true,
        modality: body.modality || "text",
        node: {{
          id: "gen-node",
          data: {{
            content: {{ text: "Output for: " + body.prompt }},
            metadata: {{ model: "gemini-3.1-pro", prompt: body.prompt }}
          }}
        }}
      }})
    }});
  }}
  return Promise.resolve({{ status: 200, ok: true, json: async () => ({{ ok: true }}) }});
}};

{script}

(async () => {{
  const api = window.TinCanNodeStudio;
  const st = api.getState();
  const out = {{}};

  // 1. Parent at (900, 500): generating child spawns directly beneath it (NOT hardcoded 420,120!)
  st.nodes.push({{
    id: "p-far", type: "GENERATED", modality: "image", morphingStatus: "image",
    label: "Far Parent", x: 900, y: 500, width: 256, height: 256,
    content: {{ imageUrl: "data:image/png;base64,AAAA" }}, metadata: {{}}
  }});
  st.selectedIds = ["p-far"];
  api.selectModality("text");
  elements.get("nsPromptInput").value = "deferred_child describe far parent";
  const genPromise = api.generate();

  // While still generating (before fetch resolves), spinner is centered inside the reserved slot directly beneath p-far
  await Promise.resolve();
  const child1 = st.nodes[st.nodes.length - 1];
  out.spinnerStatus = child1.morphingStatus;
  out.spinnerYBelowParent = child1.y > 500 + 256;
  out.spinnerXNearParentCenter = Math.abs((child1.x + 48) - (900 + 128)) <= 4;

  resolvePendingGen();
  await genPromise;
  out.finalStatus = child1.morphingStatus;
  out.finalYBelowParent = child1.y >= 500 + 256 + 60;
  out.finalCenterAlignedWithParent = Math.abs((child1.x + child1.width / 2) - (900 + 128)) <= 4;

  // 2. Generating a 2nd child from the SAME parent avoids colliding with child1
  st.selectedIds = ["p-far"];
  elements.get("nsPromptInput").value = "second sibling branch";
  await api.generate();
  const child2 = st.nodes[st.nodes.length - 1];
  const overlap12 =
    child1.x < child2.x + child2.width &&
    child1.x + child1.width > child2.x &&
    child1.y < child2.y + child2.height &&
    child1.y + child1.height > child2.y;
  out.siblingNoOverlap = !overlap12;

  // 3. Server 400 on Text shows real error box instead of silently faking "(staged locally)"
  st.selectedIds = [];
  elements.get("nsPromptInput").value = "trigger_400 test";
  await api.generate();
  const errNode = st.nodes[st.nodes.length - 1];
  out.errStatus = errNode.metadata.jobStatus;
  out.errNotStagedLocally = !String((errNode.content && errNode.content.text) || "").includes("staged locally");
  out.errBoxRendered = elements.get("nsNodesLayer").innerHTML.includes("Upstream chat model error");

  // 4. autoLayout() respects tall cards (368px Splat) with zero vertical overlap against child row
  st.nodes = [
    {{ id: "tall-splat", type: "ATLAS", modality: "atlas", morphingStatus: "omni", label: "Tall Splat", x: 0, y: 0, width: 340, height: 368, content: {{}}, metadata: {{}} }},
    {{ id: "child-mesh", type: "3D", modality: "3d", morphingStatus: "mesh3d", label: "Child Mesh", x: 0, y: 0, width: 320, height: 326, content: {{}}, metadata: {{}} }}
  ];
  st.edges = [{{ id: "e-tall", source: "tall-splat", target: "child-mesh" }}];
  api.autoLayout();
  const nTop = st.nodes.find((n) => n.id === "tall-splat");
  const nBot = st.nodes.find((n) => n.id === "child-mesh");
  out.autoLayoutNoVerticalOverlap = nBot.y >= nTop.y + nTop.height + 40;

  console.log(JSON.stringify(out));
}})();
"""
    run_res = subprocess.run([node_bin, "-e", harness], text=True, capture_output=True, check=False)
    assert run_res.returncode == 0, f"Node runtime failed: {run_res.stderr}"
    res = json.loads(run_res.stdout.strip())

    assert res["spinnerStatus"] == "generating"
    assert res["spinnerYBelowParent"] is True
    assert res["spinnerXNearParentCenter"] is True
    assert res["finalStatus"] == "text"
    assert res["finalYBelowParent"] is True
    assert res["finalCenterAlignedWithParent"] is True
    assert res["siblingNoOverlap"] is True
    assert res["errStatus"] == "ERROR"
    assert res["errNotStagedLocally"] is True
    assert res["errBoxRendered"] is True
    assert res["autoLayoutNoVerticalOverlap"] is True


def test_resizable_text_notes_image_collections_and_lightbox_in_node() -> None:
    node_bin = shutil.which("node")
    if not node_bin:
        pytest.skip("node binary not available for JS runtime check")

    html = render_node_studio_html()
    script = _extract_inline_script(html)

    harness = f"""
const elements = new Map();
const docListeners = {{}};
const elListeners = new Map();
function makeEl(id) {{
  const el = {{
    id,
    tagName: "DIV",
    textContent: "",
    innerHTML: "",
    value: "",
    src: "",
    alt: "",
    style: {{}},
    dataset: {{}},
    _classes: new Set(id === "nsImageLightboxModal" || id === "nsMeshViewerModal" || id === "nsSplatViewerModal" || id === "nsResponseToast" ? ["hidden"] : []),
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
    setAttribute() {{}},
    addEventListener(type, fn) {{
      if (!elListeners.has(id)) elListeners.set(id, {{}});
      if (!elListeners.get(id)[type]) elListeners.get(id)[type] = [];
      elListeners.get(id)[type].push(fn);
    }},
    querySelectorAll() {{ return []; }},
    getBoundingClientRect() {{ return {{ left: 0, top: 0, width: 1200, height: 800 }}; }}
  }};
  return el;
}}
[
  "nsDotCanvas", "nsEmptyState", "nsCanvasWorld", "nsEdgesSvg", "nsNodesLayer",
  "nsSelectionBox", "nsDropOverlay", "nsRefsStrip", "nsRefsRow", "nsPromptInput",
  "nsModelBtnLabel", "nsModePill", "nsRefCounter", "nsActiveRunsCount", "nsGenerateBtn",
  "nsResponseToast", "nsBatchWrap", "nsBatchVal", "nsBatchSelect",
  "nsImageLightboxModal", "nsLightboxTitle", "nsLightboxMeta", "nsLightboxCounter",
  "nsLightboxZoomBtn", "nsLightboxUseRefBtn", "nsLightboxPopOutBtn", "nsLightboxDownloadBtn",
  "nsLightboxCloseBtn", "nsLightboxStage", "nsLightboxPrevBtn", "nsLightboxImg",
  "nsLightboxNextBtn", "nsLightboxStrip"
].forEach((id) => elements.set(id, makeEl(id)));

const fetchCalls = [];
global.window = {{ innerWidth: 1200, innerHeight: 800, location: {{ href: "http://localhost:8013/nodes", search: "" }}, addEventListener() {{}} }};
global.document = {{
  readyState: "complete",
  getElementById(id) {{ return elements.get(id) || null; }},
  querySelectorAll() {{ return []; }},
  addEventListener(type, fn) {{
    if (!docListeners[type]) docListeners[type] = [];
    docListeners[type].push(fn);
  }},
  createElement(tag) {{ const el = makeEl(tag); el.click = () => {{}}; return el; }},
  body: {{ appendChild() {{}}, removeChild() {{}} }}
}};
global.fetch = (url, opts) => {{
  const body = opts && opts.body ? JSON.parse(opts.body) : null;
  fetchCalls.push({{ url: String(url), body }});
  if (url === "/api/nodes/generate") {{
    const cnt = (body && body.config && body.config.count) || 1;
    const imgs = [];
    for (let i = 0; i < cnt; i++) {{
      imgs.push({{
        index: i,
        imageUrl: "data:image/png;base64,SU1HXz" + (i + 1),
        base64: "SU1HXz" + (i + 1),
        mimeType: "image/png"
      }});
    }}
    return Promise.resolve({{
      status: 200,
      ok: true,
      json: async () => ({{
        ok: true,
        modality: "image",
        collectionCount: imgs.length,
        images: imgs,
        node: {{
          id: "coll-1",
          data: {{
            type: imgs.length > 1 ? "COLLECTION" : "GENERATED",
            content: {{ imageUrl: imgs[0].imageUrl, base64: imgs[0].base64, mimeType: "image/png", images: imgs }},
            metadata: {{ model: "gemini-3.1-flash-image", prompt: body.prompt, resolution: "1K" }}
          }}
        }}
      }})
    }});
  }}
  return Promise.resolve({{ status: 200, ok: true, json: async () => ({{ ok: true }}) }});
}};

{script}

(async () => {{
  const api = window.TinCanNodeStudio;
  const st = api.getState();
  const out = {{}};

  // 1. Resizable Text note: 1-click Expand / Compact AND drag-to-resize corner handle
  st.nodes.push({{
    id: "txt-note-1", type: "TEXT", modality: "text", morphingStatus: "text",
    label: "Long screenplay beat", x: 100, y: 100, width: 340, height: 250,
    content: {{ text: "A ".repeat(400) }},
    metadata: {{ model: "gemini-3.1-pro", prompt: "Write a long scene" }}
  }});
  api.selectModality("image");
  api.toggleNodeExpand("txt-note-1");
  const txtNode = st.nodes.find((n) => n.id === "txt-note-1");
  out.expandedTextW = txtNode.width;
  out.expandedTextH = txtNode.height;
  out.expandBtnNowCompact = elements.get("nsNodesLayer").innerHTML.includes("↙ Compact");

  // Simulate corner drag resize (+120px right, +90px down at zoom=1)
  const canvasMousedown = (elListeners.get("nsDotCanvas") || {{}}).mousedown || [];
  canvasMousedown.forEach((fn) => fn({{
    clientX: 500, clientY: 500, preventDefault() {{}}, stopPropagation() {{}},
    target: {{ closest(sel) {{ return sel === ".ns-resize-handle" ? {{ dataset: {{ resizeNodeId: "txt-note-1" }} }} : null; }} }}
  }}));
  (docListeners.mousemove || []).forEach((fn) => fn({{ clientX: 620, clientY: 590 }}));
  (docListeners.mouseup || []).forEach((fn) => fn({{}}));
  out.resizedTextW = txtNode.width;
  out.resizedTextH = txtNode.height;
  out.resizeClearedOnUp = st.resizeNodeId === null;

  // Toggle compact restores pre-expand dimensions
  api.toggleNodeExpand("txt-note-1");
  out.compactedTextW = txtNode.width;

  // 2. Nano Banana 4-Image Collection generation -> grid UI + Lightbox navigation + Ref + Pop Out + Split
  api.selectModel("gemini-3.1-flash-image");
  api.updateConfig("imageCount", "4");
  out.batchBadge = elements.get("nsBatchVal").textContent;
  elements.get("nsPromptInput").value = "Brutalist ceramic lamps collection";
  api.handlePromptInput(elements.get("nsPromptInput").value);
  out.genBtnText = elements.get("nsGenerateBtn").textContent;
  await api.generate();

  const genCall = fetchCalls.find((c) => c.url === "/api/nodes/generate");
  out.sentCount = genCall && genCall.body && genCall.body.config ? genCall.body.config.count : 0;
  const collNode = st.nodes[st.nodes.length - 1];
  out.collType = collNode.type;
  out.collImgCount = collNode.content.images.length;
  const nodesHtml = elements.get("nsNodesLayer").innerHTML;
  out.collGridRendered = nodesHtml.includes("COLLECTION · 4 IMAGES") && nodesHtml.includes("ns-collection-grid") && nodesHtml.includes("Split Nodes");

  // Open Lightbox at index 1 (image #2 of 4)
  api.openImageLightbox(collNode.id, 1);
  out.lbOpen = !elements.get("nsImageLightboxModal").classList.contains("hidden");
  out.lbCounterInitial = elements.get("nsLightboxCounter").textContent;
  out.lbImgSrcInitial = elements.get("nsLightboxImg").src;
  out.lbStripHas4 = (elements.get("nsLightboxStrip").innerHTML.match(/ns-lightbox-thumb/g) || []).length === 4;

  // Keyboard ArrowRight advances to image #3 of 4; zoom toggles; Esc closes
  (docListeners.keydown || []).forEach((fn) => fn({{ key: "ArrowRight", preventDefault() {{}} }}));
  out.lbCounterAfterRight = elements.get("nsLightboxCounter").textContent;
  api.toggleLightboxZoom();
  out.lbZoomed = elements.get("nsLightboxImg").classList.contains("is-zoomed");

  // Use image #3 as reference attaches it cleanly and closes lightbox
  api.useLightboxImageAsRef();
  out.lbClosedAfterUseRef = elements.get("nsImageLightboxModal").classList.contains("hidden");
  out.refAddedFromLightbox = st.references.some((r) => r.url === "data:image/png;base64,SU1HXz3");

  // Reopen & Pop Out image #2 to standalone canvas node
  api.openImageLightbox(collNode.id, 1);
  const countBeforePop = st.nodes.length;
  api.popOutLightboxImage();
  out.nodeAddedOnPopOut = st.nodes.length === countBeforePop + 1;
  out.poppedNodeUrl = st.nodes[st.nodes.length - 1].content.imageUrl;

  // Reopen & Escape closes cleanly
  api.openImageLightbox(collNode.id, 0);
  (docListeners.keydown || []).forEach((fn) => fn({{ key: "Escape", preventDefault() {{}} }}));
  out.lbClosedOnEsc = elements.get("nsImageLightboxModal").classList.contains("hidden");

  // Split collection spawns all 4 standalone nodes
  const countBeforeSplit = st.nodes.length;
  api.splitCollectionToNodes(collNode.id);
  out.nodesAddedOnSplit = st.nodes.length - countBeforeSplit;

  console.log(JSON.stringify(out));
}})();
"""
    run_res = subprocess.run([node_bin, "-e", harness], text=True, capture_output=True, check=False)
    assert run_res.returncode == 0, f"Node runtime failed: {run_res.stderr}"
    res = json.loads(run_res.stdout.strip())

    assert res["expandedTextW"] >= 520
    assert res["expandedTextH"] >= 460
    assert res["expandBtnNowCompact"] is True
    assert res["resizedTextW"] == res["expandedTextW"] + 120
    assert res["resizedTextH"] == res["expandedTextH"] + 90
    assert res["resizeClearedOnUp"] is True
    assert res["compactedTextW"] == 340

    assert res["batchBadge"] == "4x"
    assert "4 Images" in res["genBtnText"]
    assert res["sentCount"] == 4
    assert res["collType"] == "COLLECTION"
    assert res["collImgCount"] == 4
    assert res["collGridRendered"] is True

    assert res["lbOpen"] is True
    assert res["lbCounterInitial"] == "2 / 4"
    assert res["lbImgSrcInitial"] == "data:image/png;base64,SU1HXz2"
    assert res["lbStripHas4"] is True
    assert res["lbCounterAfterRight"] == "3 / 4"
    assert res["lbZoomed"] is True
    assert res["lbClosedAfterUseRef"] is True
    assert res["refAddedFromLightbox"] is True
    assert res["nodeAddedOnPopOut"] is True
    assert res["poppedNodeUrl"] == "data:image/png;base64,SU1HXz2"
    assert res["lbClosedOnEsc"] is True
    assert res["nodesAddedOnSplit"] == 4


def test_node_studio_preserves_peer_space_and_last_graph_across_reload() -> None:
    node_bin = shutil.which("node")
    if not node_bin:
        pytest.skip("node binary not available for JS runtime check")

    html = render_node_studio_html()
    script = _extract_inline_script(html)

    harness = f"""
const elements = new Map();
function makeEl(id) {{
  const el = {{
    id, tagName: "DIV", textContent: "", innerHTML: "", value: "", style: {{}}, dataset: {{}},
    _classes: new Set(),
    classList: {{
      toggle(c, f) {{ if (f === undefined) {{ if (el._classes.has(c)) {{ el._classes.delete(c); return false; }} el._classes.add(c); return true; }} if (f) el._classes.add(c); else el._classes.delete(c); return !!f; }},
      add(c) {{ el._classes.add(c); }}, remove(c) {{ el._classes.delete(c); }}, contains(c) {{ return el._classes.has(c); }}
    }},
    setAttribute() {{}}, addEventListener() {{}}, querySelectorAll() {{ return []; }},
    getBoundingClientRect() {{ return {{ left: 0, top: 0, width: 1200, height: 800 }}; }}
  }};
  return el;
}}
[
  "nsDotCanvas", "nsEmptyState", "nsCanvasWorld", "nsEdgesSvg", "nsNodesLayer",
  "nsSelectionBox", "nsDropOverlay", "nsRefsStrip", "nsRefsRow", "nsPromptInput",
  "nsModelBtnLabel", "nsModePill", "nsRefCounter", "nsActiveRunsCount", "nsGenerateBtn",
  "nsSaveGraphStatus", "nsGraphNameInput", "nsSavedGraphsList"
].forEach((id) => elements.set(id, makeEl(id)));

const lsStore = new Map([
  ["tincan_peer_id", "peer-jewkdo"],
  ["tincan_ns_last_graph_user_peer-jewkdo", "test"]
]);
global.localStorage = {{
  getItem(k) {{ return lsStore.has(k) ? lsStore.get(k) : null; }},
  setItem(k, v) {{ lsStore.set(k, String(v)); }}
}};
const fetchedUrls = [];
global.window = {{
  innerWidth: 1200, innerHeight: 800,
  currentSpaceScope: "user",
  currentSpaceOwner: "", // Simulates Mesh OS initial boot before refreshAgentSpace() runs!
  location: {{ href: "http://localhost:8013/nodes", search: "" }},
  addEventListener() {{}}
}};
global.document = {{
  readyState: "complete",
  getElementById(id) {{ return elements.get(id) || null; }},
  querySelectorAll() {{ return []; }},
  addEventListener() {{}},
  createElement(tag) {{ return makeEl(tag); }},
  body: {{ appendChild() {{}}, removeChild() {{}} }}
}};
global.fetch = (url) => {{
  fetchedUrls.push(String(url));
  if (String(url).includes("/api/nodes/graph?") && String(url).includes("owner_id=peer-jewkdo") && String(url).includes("test.nodes.json")) {{
    return Promise.resolve({{
      status: 200, ok: true,
      json: async () => ({{
        ok: true,
        path: "/nodes/test.nodes.json",
        graph: {{
          name: "test",
          path: "/nodes/test.nodes.json",
          nodes: [{{ id: "surv-1", type: "TEXT", modality: "text", morphingStatus: "text", label: "Survived deploy", x: 100, y: 100, width: 340, height: 250, content: {{ text: "Persisted across deploy!" }}, metadata: {{}} }}],
          edges: [],
          references: []
        }}
      }})
    }});
  }}
  if (String(url).includes("/api/nodes/graphs?")) {{
    return Promise.resolve({{
      status: 200, ok: true,
      json: async () => ({{ ok: true, graphs: [{{ name: "test", path: "/nodes/test.nodes.json", size_bytes: 12000 }}] }})
    }});
  }}
  return Promise.resolve({{ status: 404, ok: false, json: async () => ({{ ok: false }}) }});
}};

{script}

setTimeout(() => {{
  const api = window.TinCanNodeStudio;
  const st = api.getState();
  console.log(JSON.stringify({{
    fetchedUrls,
    restoredGraphName: st.graphName,
    restoredNodeCount: st.nodes.length,
    restoredText: st.nodes[0] && st.nodes[0].content ? st.nodes[0].content.text : ""
  }}));
}}, 40);
"""
    run_res = subprocess.run([node_bin, "-e", harness], text=True, capture_output=True, check=False)
    assert run_res.returncode == 0, f"Node runtime failed: {run_res.stderr}"
    res = json.loads(run_res.stdout.strip())

    assert any("owner_id=peer-jewkdo" in u for u in res["fetchedUrls"]), f"Expected peer-jewkdo fetch, got {res['fetchedUrls']}"
    assert not any("owner_id=default" in u for u in res["fetchedUrls"]), "Must NOT fall back to empty default space when tincan_peer_id exists!"
    assert res["restoredGraphName"] == "test"
    assert res["restoredNodeCount"] == 1
    assert res["restoredText"] == "Persisted across deploy!"
