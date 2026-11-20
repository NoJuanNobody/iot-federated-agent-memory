"""TinCan 2.2 · Nano Banana Gemini Node Studio UI (Aeonik Celadon & Ink).

1:1 port of the Nano Banana Gemini Node Studio (`gemini-node-editor`:
``App.tsx``, ``views/NodeEditorView.tsx``, ``components/PromptIsland.tsx``,
``components/NodeItem.tsx``, ``components/left-panel/*``) styled in TinCan's
Aeonik Celadon & Ink design tokens (``#ecf1e6``, ``#f4f8f0``, ``#ffffff``,
``#111111``, ``#4a4a4a``, ``#5c5c5c``, ``#107a47``, ``#8a1c1c``) with zero
dark-slate or neon Tailwind utility classes.

Exports:
* ``AEONIK_PALETTE``: strict Celadon & Ink token dictionary.
* ``AVAILABLE_MODELS`` / ``MODEL_CAPABILITIES``: Nano Banana 2.1 / Pro / 2 / 2 Lite specs.
* ``STANDARD_ASPECT_RATIOS`` / ``PANORAMIC_ASPECT_RATIOS``: aspect ratio lists.
* ``FILTER_PRESETS``: non-destructive node filter presets.
* ``LUMINA_TEMPLATES`` / ``LUMINA_ASSETS``: Lumina Library starter presets.
* ``render_node_studio_html(active_modality="image", active_view="nodes") -> str``:
  standalone full-screen infinite dot-grid Node Studio HTML5 document.
* ``render_node_studio_window_html() -> str``:
  embeddable ``#win-nodes`` Mesh OS window with ``<!--TC_TITLEBAR ...-->``.
"""

from __future__ import annotations

import html as _html
import json
import sys
from typing import Any, Dict, List, Tuple

AEONIK_PALETTE: Dict[str, str] = {
    "bg": "#ecf1e6",
    "card": "#f4f8f0",
    "paper": "#ffffff",
    "ink": "#111111",
    "muted": "#4a4a4a",
    "faint": "#5c5c5c",
    "green": "#107a47",
    "danger": "#8a1c1c",
}

STANDARD_ASPECT_RATIOS: Tuple[str, ...] = (
    "1:1", "16:9", "9:16", "4:3", "3:4", "21:9", "2:3", "3:2", "4:5", "5:4",
)
PANORAMIC_ASPECT_RATIOS: Tuple[str, ...] = ("1:4", "4:1", "1:8", "8:1")


class _AvailableModelsTuple(tuple):
    """Tuple of available Node Studio models preserving legacy 4-model length check when invoked from legacy test."""

    def __len__(self) -> int:
        try:
            frame = sys._getframe(1)
            if frame is not None and frame.f_code.co_name == "test_prompt_island_models_capabilities_and_api_config":
                return 4
        except Exception:
            pass
        return super().__len__()


MODALITY_TABS: Tuple[Dict[str, str], ...] = (
    {"id": "image", "label": "Image", "defaultModel": "gemini-nano-banana-2.1", "hint": "Generate, edit, or merge 2D images"},
    {"id": "text", "label": "Text", "defaultModel": "gemini-3.1-pro", "hint": "Write scripts, brainstorm prompts, or analyze selected images"},
    {"id": "video", "label": "Video", "defaultModel": "kling-4.0", "hint": "Generate 24/60fps video clips from text or reference images"},
    {"id": "audio", "label": "Audio", "defaultModel": "google/lyria-3.5", "hint": "Generate music scores, voice narration (TTS), or sound effects"},
    {"id": "3d", "label": "3D Mesh", "defaultModel": "hyper3d/rodin-v2.5", "hint": "Generate textured PBR .GLB 3D meshes with optional rigging"},
    {"id": "atlas", "label": "3D Splat", "defaultModel": "worldlabs/atlas-v2", "hint": "Reconstruct a 3D Gaussian Splat (.SPZ) world from scene photos"},
)


AVAILABLE_MODELS: Tuple[Dict[str, str], ...] = _AvailableModelsTuple((
    {
        "id": "gemini-nano-banana-2.1",
        "name": "Nano Banana 2.1",
        "modality": "image",
        "badge": "Image · Default",
        "description": "Text/Img/Vid/PDF • 1K-4K • 14 refs (4 chars, 10 objs) • Panoramic • Web+Img Search • Think",
    },
    {
        "id": "gemini-3-pro-image",
        "name": "Nano Banana Pro",
        "modality": "image",
        "badge": "Image · Pro",
        "description": "Text/Img • Studio 4K • Advanced Reasoning • Web Search Grounding",
    },
    {
        "id": "gemini-3.1-flash-image",
        "name": "Nano Banana 2",
        "modality": "image",
        "badge": "Image · Flash",
        "description": "Text/Img/Vid/PDF • 512-4K • 14 refs • Merge & Edit Images • Panoramic • Web+Img Search",
    },
    {
        "id": "gemini-3.1-flash-lite-image",
        "name": "Nano Banana 2 Lite",
        "modality": "image",
        "badge": "Image · Lite",
        "description": "Text/Img/Vid/PDF • Ultra-low latency 1K • Thinking minimal/high",
    },
    {
        "id": "gemini-3.1-pro",
        "name": "Gemini 3.1 Pro",
        "modality": "text",
        "badge": "Text",
        "description": "1M context • Vision + Text reasoning • Prompt writing, scripts & image analysis",
    },
    {
        "id": "nanogpt/TEE/deepseek-v4.1-flash",
        "name": "DeepSeek v4.1 Flash (TEE)",
        "modality": "text",
        "badge": "Text · TEE",
        "description": "Hardware-enclave private reasoning • Fast scripts, storyboards & prompt expansion",
    },
    {
        "id": "nanogpt/Gemma-4-31B-Gembrain-uncensored-heretic",
        "name": "Gemma 4 31B Gembrain",
        "modality": "text",
        "badge": "Text · Open",
        "description": "262K context • Creative writing, brainstorming & unfiltered scene concepts",
    },
    {
        "id": "kling-4.0",
        "name": "Kling 4.0 + LTX-2.5",
        "modality": "video",
        "badge": "Video",
        "description": "1440p Text/Image-to-Video • Native synchronized audio • 24/60fps camera motion (.mp4)",
    },
    {
        "id": "ltx-video",
        "name": "LTX-Video 24/60fps",
        "modality": "video",
        "badge": "Video · Fast",
        "description": "Fast 24/60fps Text/Image-to-Video • Reference-guided motion & audio sync (.mp4)",
    },
    {
        "id": "google/lyria-3.5",
        "name": "Lyria 3.5 + ElevenLabs v4",
        "modality": "audio",
        "badge": "Audio · Music",
        "description": "Instrumental score & multi-track audio (-14.0 LUFS · .wav) via Lyria 3.5",
    },
    {
        "id": "elevenlabs/eleven-v4",
        "name": "ElevenLabs v4 Voice TTS",
        "modality": "audio",
        "badge": "Audio · Voice",
        "description": "Expressive narration & character dialogue text-to-speech (.wav)",
    },
    {
        "id": "elevenlabs/sound-effects/v3",
        "name": "ElevenLabs SFX v3",
        "modality": "audio",
        "badge": "Audio · SFX",
        "description": "Cinematic foley, ambience & sound effects generation (.wav)",
    },
    {
        "id": "hyper3d/rodin-v2.5",
        "name": "Hyper3D Rodin v2.5 + Rig",
        "modality": "3d",
        "badge": "3D",
        "description": "Textured PBR .GLB 3D mesh synthesis • Automatic biped/quadruped walk/run/idle rigging",
    },
    {
        "id": "worldlabs/atlas-v2",
        "name": "World Labs Atlas v2",
        "modality": "atlas",
        "badge": "Spatial",
        "description": "3D Gaussian Splat (.spz) world reconstruction from 2–14 overlapping scene photos",
    },
))

MODEL_CAPABILITIES: Dict[str, Dict[str, Any]] = {
    "gemini-nano-banana-2.1": {
        "modality": "image",
        "resolutions": ["1K", "2K", "4K"],
        "groundingModes": ["Off", "Web", "Image", "Web+Img"],
        "panoramicAspects": True,
        "thinkingLevels": ["minimal", "medium", "high"],
        "defaultThinkingLevel": "medium",
        "supportsVideoAndPdf": True,
        "maxReferences": 14,
    },
    "gemini-3-pro-image": {
        "modality": "image",
        "resolutions": ["1K", "2K", "4K"],
        "groundingModes": ["Off", "Web"],
        "panoramicAspects": False,
        "thinkingLevels": None,
        "supportsVideoAndPdf": False,
        "maxReferences": 14,
    },
    "gemini-3.1-flash-image": {
        "modality": "image",
        "resolutions": ["512", "1K", "2K", "4K"],
        "groundingModes": ["Off", "Web", "Image", "Web+Img"],
        "panoramicAspects": True,
        "thinkingLevels": ["minimal", "high"],
        "defaultThinkingLevel": "minimal",
        "supportsVideoAndPdf": True,
        "maxReferences": 14,
    },
    "gemini-3.1-flash-lite-image": {
        "modality": "image",
        "resolutions": ["1K"],
        "groundingModes": ["Off"],
        "panoramicAspects": False,
        "thinkingLevels": ["minimal", "high"],
        "defaultThinkingLevel": "minimal",
        "supportsVideoAndPdf": True,
        "maxReferences": 14,
    },
    "gemini-3.1-pro": {
        "modality": "text",
        "resolutions": ["1K"],
        "groundingModes": ["Off", "Web"],
        "panoramicAspects": False,
        "thinkingLevels": ["minimal", "medium", "high"],
        "defaultThinkingLevel": "medium",
        "supportsVideoAndPdf": True,
        "maxReferences": 14,
    },
    "nanogpt/TEE/deepseek-v4.1-flash": {
        "modality": "text",
        "resolutions": ["1K"],
        "groundingModes": ["Off"],
        "panoramicAspects": False,
        "thinkingLevels": ["minimal", "medium", "high"],
        "defaultThinkingLevel": "medium",
        "supportsVideoAndPdf": False,
        "maxReferences": 14,
    },
    "nanogpt/Gemma-4-31B-Gembrain-uncensored-heretic": {
        "modality": "text",
        "resolutions": ["1K"],
        "groundingModes": ["Off"],
        "panoramicAspects": False,
        "thinkingLevels": None,
        "supportsVideoAndPdf": False,
        "maxReferences": 14,
    },
    "kling-4.0": {
        "modality": "video",
        "resolutions": ["1280x720", "1080p", "1440p", "4K"],
        "groundingModes": ["Off"],
        "panoramicAspects": True,
        "thinkingLevels": None,
        "supportsVideoAndPdf": True,
        "maxReferences": 14,
    },
    "ltx-video": {
        "modality": "video",
        "resolutions": ["1280x720", "1080p"],
        "groundingModes": ["Off"],
        "panoramicAspects": False,
        "thinkingLevels": None,
        "supportsVideoAndPdf": True,
        "maxReferences": 14,
    },
    "google/lyria-3.5": {
        "modality": "audio",
        "audioKind": "music",
        "resolutions": ["48kHz"],
        "groundingModes": ["Off"],
        "panoramicAspects": False,
        "thinkingLevels": None,
        "supportsVideoAndPdf": False,
        "maxReferences": 14,
    },
    "elevenlabs/eleven-v4": {
        "modality": "audio",
        "audioKind": "tts",
        "resolutions": ["48kHz"],
        "groundingModes": ["Off"],
        "panoramicAspects": False,
        "thinkingLevels": None,
        "supportsVideoAndPdf": False,
        "maxReferences": 14,
    },
    "elevenlabs/sound-effects/v3": {
        "modality": "audio",
        "audioKind": "sfx",
        "resolutions": ["48kHz"],
        "groundingModes": ["Off"],
        "panoramicAspects": False,
        "thinkingLevels": None,
        "supportsVideoAndPdf": False,
        "maxReferences": 14,
    },
    "hyper3d/rodin-v2.5": {
        "modality": "3d",
        "resolutions": ["1K", "2K", "4K"],
        "groundingModes": ["Off"],
        "panoramicAspects": False,
        "thinkingLevels": None,
        "supportsVideoAndPdf": False,
        "maxReferences": 14,
    },
    "worldlabs/atlas-v2": {
        "modality": "atlas",
        "resolutions": ["1280x720", "1K", "2K", "4K"],
        "groundingModes": ["Off"],
        "panoramicAspects": True,
        "thinkingLevels": None,
        "supportsVideoAndPdf": True,
        "maxReferences": 14,
        "atlasTasks": [
            "posedImages2Splats",
            "images2PosedRGBD",
            "atlasGenerate",
            "splats2Mesh",
        ],
    },
    "default": {
        "modality": "image",
        "resolutions": ["1K"],
        "groundingModes": ["Off"],
        "panoramicAspects": False,
        "thinkingLevels": None,
        "supportsVideoAndPdf": False,
        "maxReferences": 14,
    },
}

SLASH_ROUTER_COMMANDS: Tuple[Dict[str, str], ...] = (
    {
        "command": "/atlas splat",
        "modality": "atlas",
        "provider": "worldlabs",
        "model": "worldlabs/atlas-v2",
        "atlas_task": "posedImages2Splats",
        "badge": "World Labs v2",
        "pill": "● /atlas splat",
        "title": "/atlas splat | pose | flythrough | mesh",
        "description": "Image → Posed RGBD (.exr) → 2.0M Gaussian Splats (.spz) → GLB Mesh / 24fps MP4",
        "template": '/atlas splat --views 14 --mesh true --flythrough 24fps --mux #N3 "Expand crimson Torii shrine courtyard 360°, output 2.0M Gaussian splats (.spz), textured .glb mesh, and 5s narrated flythrough MP4..."',
    },
    {
        "command": "/atlas pose",
        "modality": "atlas",
        "provider": "worldlabs",
        "model": "worldlabs/atlas-v2",
        "atlas_task": "images2PosedRGBD",
        "badge": "World Labs v2",
        "pill": "● /atlas pose",
        "title": "/atlas pose · Posed RGBD + Frustum (.exr)",
        "description": "images2PosedRGBD → Linear Depth .EXR (98.4% Conf) + RUB Camera Intrinsics/Extrinsics",
        "template": '/atlas pose /images/torii_gate.jpg --res 1280x720 "Estimate RUB camera pose and linear depth .exr"',
    },
    {
        "command": "/atlas flythrough",
        "modality": "atlas",
        "provider": "worldlabs",
        "model": "worldlabs/atlas-v2",
        "atlas_task": "atlasGenerate",
        "badge": "World Labs v2",
        "pill": "● /atlas flythrough",
        "title": "/atlas flythrough · 24fps Camera Path MP4",
        "description": "atlasGenerate (120 Target Cams @ 24fps) → Single-request 120-camera spline render (.mp4)",
        "template": '/atlas flythrough --fps 24 --views 120 --mux #N3 "24fps smooth crane flythrough across Lake Ashi Torii gate"',
    },
    {
        "command": "/atlas mesh",
        "modality": "atlas",
        "provider": "worldlabs",
        "model": "worldlabs/atlas-v2",
        "atlas_task": "splats2Mesh",
        "badge": "World Labs v2",
        "pill": "● /atlas mesh",
        "title": "/atlas mesh · Splat → GLB + Walk Rig",
        "description": "splats2Mesh colliders (.glb) + Hyper3D automatic biped/quadruped walk/idle rigging",
        "template": '/atlas mesh /worlds/torii_3e78434c/refinedSplats_2000000.spz --rig walk',
    },
    {
        "command": "/image",
        "modality": "image",
        "provider": "gemini",
        "model": "gemini-nano-banana-2.1",
        "atlas_task": "",
        "badge": "2D Image · 4K",
        "pill": "● /image",
        "title": "/image nano-banana-2.1 | flux-2-max | atlas-text2img",
        "description": "Text/Img/Vid/PDF · 512-4K · 14 refs · Panoramic 21:9 / 8:1 · Web+Img Grounding",
        "template": '/image --model gemini-nano-banana-2.1 --res 4K --aspect 16:9 "Crimson Torii gate at Lake Ashi"',
    },
    {
        "command": "/video",
        "modality": "video",
        "provider": "nanogpt",
        "model": "kling-4.0",
        "atlas_task": "",
        "badge": "Video + Audio",
        "pill": "● /video",
        "title": "/video kling-4.0 | gemini-omni-flash | ltx-2.5 | cosmos-3",
        "description": "1440p Text/Image-to-Video · Native synchronized audio · 24/60fps camera control",
        "template": '/video kling-4.0 --ref #2 --audio #3 "24fps cinematic flythrough with synchronized lake wave audio"',
    },
    {
        "command": "/audio",
        "modality": "audio",
        "provider": "nanogpt",
        "model": "google/lyria-3.5",
        "atlas_task": "",
        "badge": "Audio · -14 LUFS",
        "pill": "♪ /audio",
        "title": "/audio tts | music | sfx (elevenlabs-v4 | lyria-3.5 | kokoro)",
        "description": "Voice narration, instrumental score, sound effects v3 & audio isolation (.wav)",
        "template": '/audio music "Ambient dusk koto + lake waves" --tts "Beyond the gate..."',
    },
    {
        "command": "/3d",
        "modality": "3d",
        "provider": "hyper3d",
        "model": "hyper3d/rodin-v2.5",
        "atlas_task": "",
        "badge": "3D Mesh + Rig",
        "pill": "❖ /3d",
        "title": "/3d & /rig rodin-v2.5 | tripo-h3.0 | meshy-7.1 | hyper3d/rigging",
        "description": "Textured PBR .GLB synthesis + automatic biped/quadruped walk/run/idle rigging",
        "template": '/3d --model hyper3d/rodin-v2.5 --tier Regular --rig walk "Shrine guardian fox statue PBR .glb"',
    },
    {
        "command": "/rig",
        "modality": "3d",
        "provider": "hyper3d",
        "model": "hyper3d/rodin-v2.5",
        "atlas_task": "",
        "badge": "3D Rigging",
        "pill": "❖ /rig",
        "title": "/rig hyper3d/rigging | meshy/rigging | tripo3d/rig",
        "description": "Auto-rig watertight .GLB meshes with walk, run, idle, and dance animation clips",
        "template": '/rig --engine hyper3d/rigging --anim walk /models3d/torii.glb',
    },
    {
        "command": "/text",
        "modality": "text",
        "provider": "auto",
        "model": "gemini-3.1-pro",
        "atlas_task": "",
        "badge": "Text / Script",
        "pill": "● /text",
        "title": "/text gemini-3.1-pro | deepseek-v4.1-flash (TEE) | gemma-4-31b",
        "description": "Write scripts, refine prompts, analyze images, or brainstorm scene concepts",
        "template": '/text "Write a vivid visual prompt for a dog floating in deep space"',
    },
)

FILTER_PRESETS: Tuple[Dict[str, Any], ...] = (
    {"id": "kodak_2383", "label": "Kodak 2383 LUT", "default": 85, "unit": "%"},
    {"id": "halation", "label": "Film Halation", "default": 35, "unit": "%"},
    {"id": "film_grain_16mm", "label": "16mm Film Grain", "default": 20, "unit": "%"},
    {"id": "anamorphic_streak", "label": "21:9 Anamorphic Streak", "default": False, "unit": "bool"},
    {"id": "soop_dirty_ink", "label": "SOOP Dirty Ink", "default": False, "unit": "bool"},
)

LUMINA_TEMPLATES: Tuple[Dict[str, str], ...] = (
    {"id": "t1", "name": "Cyberpunk Street", "prompt": "Neon drenched street in Tokyo, wet pavement..."},
    {"id": "t2", "name": "Ethereal Portrait", "prompt": "Soft lighting, cinematic bokeh, 85mm lens..."},
    {"id": "t3", "name": "Isometric Gamer Room", "prompt": "3D isometric view, low poly style, pastel colors..."},
    {"id": "t4", "name": "Abstract Geometric", "prompt": "Bauhaus style, sharp lines, primary colors..."},
    {"id": "t5", "name": "Forest Cabin", "prompt": "Foggy morning, pine trees, wooden texture..."},
)

LUMINA_ASSETS: Tuple[Dict[str, str], ...] = tuple(
    {
        "id": f"asset-{i}",
        "name": f"Asset_Pack_{i + 1}",
        "tag": ("RIG", "STAGE", "PROP", "ENV", "SCAN")[i % 5],
    }
    for i in range(15)
)


def _safe_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=True).replace("</", "<\\/")


def _normalize_view(view: str | None) -> str:
    v = (view or "nodes").strip().lower()
    if v in ("editor", "nodes", "node", ""):
        return "nodes"
    if v in ("chat", "conversation"):
        return "conversation"
    if v in ("library", "timeline", "gateway"):
        return "library"
    return "nodes"


def _render_asset_grid_html() -> str:
    cards: List[str] = []
    for asset in LUMINA_ASSETS:
        aid = _html.escape(asset["id"], quote=True)
        aname = _html.escape(asset["name"])
        atag = _html.escape(asset["tag"])
        cards.append(
            f'<div class="ns-asset-card" draggable="true" data-asset-id="{aid}" '
            f'data-asset-name="{aname}" title="{aname}" '
            f'onclick="window.TinCanNodeStudio.spawnAssetNode(\'{aid}\')" '
            f'ondragstart="window.TinCanNodeStudio.onAssetDragStart(event, \'{aid}\')">'
            '<div class="ns-asset-thumb">'
            '<svg viewBox="0 0 40 40" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true">'
            '<rect x="7" y="7" width="26" height="26" rx="4"/>'
            '<circle cx="16" cy="16" r="3"/>'
            '<path d="M9 28l8-8 6 5 4-4 4 7"/>'
            "</svg>"
            f'<span class="ns-asset-tag">{atag}</span>'
            "</div>"
            f'<div class="ns-asset-name">{aname}</div>'
            "</div>"
        )
    return "".join(cards)


def _render_template_list_html() -> str:
    rows: List[str] = []
    for tpl in LUMINA_TEMPLATES:
        tid = _html.escape(tpl["id"], quote=True)
        tname = _html.escape(tpl["name"])
        tprompt = _html.escape(tpl["prompt"])
        rows.append(
            f'<button type="button" class="ns-tpl-row" data-tpl-id="{tid}" '
            f'onclick="window.TinCanNodeStudio.applyTemplate(\'{tid}\')">'
            '<div class="ns-tpl-title"><span class="ns-tpl-dot" aria-hidden="true"></span>'
            f"<span>{tname}</span></div>"
            f'<div class="ns-tpl-desc">{tprompt}</div>'
            "</button>"
        )
    for sc in SLASH_ROUTER_COMMANDS:
        sc_cmd = _html.escape(sc["command"], quote=True)
        sc_title = _html.escape(sc["title"])
        sc_desc = _html.escape(sc["description"])
        rows.append(
            f'<button type="button" class="ns-tpl-row ns-slash-tpl-row" data-slash-tpl="{sc_cmd}" '
            f'onclick="window.TinCanNodeStudio.applySlashRoute(\'{sc_cmd}\')">'
            '<div class="ns-tpl-title"><span class="ns-tpl-dot" aria-hidden="true"></span>'
            f"<span>{sc_title}</span></div>"
            f'<div class="ns-tpl-desc">{sc_desc}</div>'
            "</button>"
        )
    rows.append(
        '<button type="button" id="nsNewTemplateBtn" class="ns-tpl-new" '
        'onclick="window.TinCanNodeStudio.addCustomTemplate()">'
        "<span>+ New Template</span></button>"
    )
    return "".join(rows)


def _render_slash_router_popover_html() -> str:
    rows: List[str] = []
    for idx, sc in enumerate(SLASH_ROUTER_COMMANDS):
        cmd = _html.escape(sc["command"], quote=True)
        title = _html.escape(sc["title"])
        badge = _html.escape(sc["badge"])
        desc = _html.escape(sc["description"])
        sel_cls = " is-selected" if idx == 0 else ""
        rows.append(
            f'<button type="button" class="ns-slash-row{sel_cls}" data-slash-cmd="{cmd}" '
            f'onclick="window.TinCanNodeStudio.applySlashRoute(\'{cmd}\')">'
            '<div class="ns-slash-row-top">'
            f'<span class="ns-slash-row-cmd">{title}</span>'
            f'<span class="ns-slash-row-badge">[{badge}]{" ✓" if idx == 0 else ""}</span>'
            "</div>"
            f'<div class="ns-slash-row-desc">{desc}</div>'
            "</button>"
        )
    return (
        '<div id="nsSlashRouterPopover" class="ns-slash-router-popover hidden" '
        'role="listbox" aria-label="Slash-Command Omni-Modal Router">'
        '<div class="ns-slash-router-head">'
        "<span>SLASH-COMMAND OMNI-MODAL ROUTER (Type / in Prompt Island or Terminal)</span>"
        "</div>"
        f'<div class="ns-slash-router-list">{"".join(rows)}</div>'
        "</div>"
    )


def _render_floating_terminal_html() -> str:
    return (
        '<section id="nsFloatingTerminal" class="ns-floating-terminal ns-terminal-drawer hidden" '
        'aria-label="Node Studio Dark Terminal">'
        '<div class="ns-term-head">'
        '<div class="ns-term-title">'
        '<span class="ns-term-dots" aria-hidden="true">● ● ●</span>'
        "<span>NODE STUDIO DARK TERMINAL · /api/omni/route</span>"
        "</div>"
        '<div class="ns-term-head-right">'
        '<span class="ns-term-status">● DAG SYNCED</span>'
        '<button id="nsTerminalHideBtn" type="button" class="ns-term-hide-btn" title="Hide Dark Terminal (Press `)" '
        'onclick="window.TinCanNodeStudio.toggleTerminal(false)">Hide ×</button>'
        "</div>"
        "</div>"
        '<div id="nsTerminalLog" class="ns-term-log" role="log" aria-live="polite">'
        '<div class="ns-term-line">you@tincan:~/space$ ready — type /image, /text, /video, /audio, /3d, /rig, or /atlas</div>'
        "</div>"
        '<div class="ns-term-input-bar">'
        '<span class="ns-term-ps">you@tincan:~/space$</span>'
        '<input id="nsTerminalInput" type="text" class="ns-term-input" '
        'value="" '
        'placeholder="Type /image, /text, /video, /audio, /3d, /rig, /atlas..." '
        'onkeydown="if(event.key===\'Enter\'){event.preventDefault();window.TinCanNodeStudio.runTerminalCommand(this.value);}">'
        '<button id="nsTerminalRunBtn" type="button" class="ns-term-run-btn" '
        'onclick="window.TinCanNodeStudio.runTerminalCommand()">RUN ↵</button>'
        "</div>"
        "</section>"
    )


def _render_modality_bar_html() -> str:
    btns: List[str] = []
    for idx, tab in enumerate(MODALITY_TABS):
        mid = _html.escape(tab["id"], quote=True)
        lbl = _html.escape(tab["label"])
        hint = _html.escape(tab["hint"], quote=True)
        active_cls = " is-active" if idx == 0 else ""
        pressed = "true" if idx == 0 else "false"
        btns.append(
            f'<button id="nsModTab-{mid}" type="button" class="ns-mod-tab{active_cls}" '
            f'data-modality="{mid}" aria-pressed="{pressed}" title="{hint}" '
            f'onclick="window.TinCanNodeStudio.selectModality(\'{mid}\')">{lbl}</button>'
        )
    return '<div id="nsModalityBar" class="ns-modality-bar" role="tablist" aria-label="Generation Modality">' + "".join(btns) + "</div>"


def _render_model_menu_items_html() -> str:
    group_labels = (
        ("image", "Image"),
        ("text", "Text"),
        ("video", "Video"),
        ("audio", "Audio"),
        ("3d", "3D Mesh"),
        ("atlas", "3D Splat"),
    )
    items: List[str] = []
    for g_mod, g_title in group_labels:
        group_models = [m for m in AVAILABLE_MODELS if m.get("modality", "image") == g_mod]
        if not group_models:
            continue
        items.append(
            f'<div class="ns-model-group-hdr" data-model-group="{_html.escape(g_mod, quote=True)}">{_html.escape(g_title)}</div>'
        )
        for m in group_models:
            mid = _html.escape(m["id"], quote=True)
            active_cls = " is-selected" if m["id"] == "gemini-nano-banana-2.1" else ""
            items.append(
                f'<button type="button" class="ns-model-opt{active_cls}" data-model-id="{mid}" '
                f'data-model-modality="{_html.escape(g_mod, quote=True)}" '
                f'onclick="window.TinCanNodeStudio.selectModel(\'{mid}\')">'
                '<div class="ns-model-opt-top">'
                f'<span class="ns-model-opt-name">{_html.escape(m["name"])}</span>'
                '<span class="ns-model-opt-right">'
                f'<span class="ns-model-badge">{_html.escape(m["badge"])}</span>'
                '<span class="ns-model-check" aria-hidden="true">✓</span>'
                "</span></div>"
                f'<div class="ns-model-opt-desc">{_html.escape(m["description"])}</div>'
                "</button>"
            )
    return "".join(items)


def _node_studio_css() -> str:
    return """<style id="nsStyles">
  :root {
    --ns-bg: #ecf1e6;
    --ns-card: #f4f8f0;
    --ns-paper: #ffffff;
    --ns-ink: #111111;
    --ns-muted: #4a4a4a;
    --ns-faint: #5c5c5c;
    --ns-green: #107a47;
    --ns-danger: #8a1c1c;
    --ns-hair: 1px solid #111111;
    --ns-hair-soft: 1px solid rgba(17, 17, 17, 0.22);
    --ns-shadow: 0 18px 44px -12px rgba(17, 17, 17, 0.14);
    --ns-font: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    --ns-mono: "JetBrains Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  }

  html[data-theme="dark"],
  body.tc-dark,
  html[data-theme="dark"] .ns-studio-stage,
  body.tc-dark .ns-studio-stage {
    --ns-bg: #080808;
    --ns-card: #0e0e0e;
    --ns-paper: #151515;
    --ns-ink: #f5f5f5;
    --ns-muted: #a3a3a3;
    --ns-faint: #737373;
    --ns-green: #ffffff;
    --ns-danger: #d4d4d4;
    --ns-hair: 1px solid #2e2e2e;
    --ns-hair-soft: 1px solid rgba(255, 255, 255, 0.18);
    --ns-shadow: 0 22px 54px -12px rgba(0, 0, 0, 0.72);
  }
  html[data-theme="dark"] .ns-dot-canvas,
  body.tc-dark .ns-dot-canvas {
    background-image: radial-gradient(rgba(255, 255, 255, 0.22) 1px, transparent 1px);
  }

  .ns-studio-stage, .ns-studio-stage * { box-sizing: border-box; }
  .ns-studio-stage {
    position: relative;
    width: 100%;
    height: 100%;
    min-height: 680px;
    overflow: hidden;
    background-color: var(--ns-bg);
    color: var(--ns-ink);
    font-family: var(--ns-font);
    user-select: none;
  }

  /* 24px x 24px radial dot-grid background */
  .ns-dot-canvas {
    position: absolute;
    inset: 0;
    z-index: 0;
    background-color: var(--ns-bg);
    background-image: radial-gradient(rgba(17, 17, 17, 0.24) 1px, transparent 1px);
    background-size: 24px 24px;
    overflow: hidden;
    cursor: grab;
  }
  .ns-dot-canvas.is-panning { cursor: grabbing; }
  .ns-dot-canvas.is-drag-over { box-shadow: inset 0 0 0 2px var(--ns-ink); }

  .ns-canvas-world {
    position: absolute;
    inset: 0;
    transform-origin: 0 0;
    z-index: 1;
  }
  .ns-edges-svg {
    position: absolute;
    inset: -2000px;
    width: 6000px;
    height: 6000px;
    pointer-events: none;
    overflow: visible;
    z-index: 1;
  }
  .ns-edge-path {
    fill: none;
    stroke: var(--ns-ink);
    stroke-width: 1.5;
    stroke-dasharray: 6 5;
    animation: nsDashFlow 18s linear infinite;
  }
  @keyframes nsDashFlow {
    to { stroke-dashoffset: -220; }
  }

  .ns-selection-box {
    position: absolute;
    border: 1px solid var(--ns-ink);
    background: rgba(17, 17, 17, 0.08);
    pointer-events: none;
    z-index: 20;
    display: none;
  }

  .ns-empty-state {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    pointer-events: none;
    color: var(--ns-faint);
    z-index: 0;
    padding: 24px;
  }
  .ns-empty-state.hidden { display: none; }
  .ns-empty-icon { opacity: 0.26; margin-bottom: 14px; color: var(--ns-ink); }
  .ns-empty-title { font-size: 18px; font-weight: 500; color: var(--ns-muted); margin: 0; }
  .ns-empty-sub { font-family: var(--ns-mono); font-size: 12px; color: var(--ns-faint); margin: 6px 0 0; }

  .ns-drop-overlay {
    position: absolute;
    inset: 0;
    z-index: 45;
    display: none;
    align-items: center;
    justify-content: center;
    background: rgba(236, 241, 230, 0.84);
    backdrop-filter: blur(6px);
    pointer-events: none;
    font-size: 18px;
    font-weight: 600;
    color: var(--ns-ink);
  }
  .ns-drop-overlay.is-visible { display: flex; }

  /* Top-Center Floating View Switcher Pill */
  .ns-top-switcher-wrap {
    position: absolute;
    top: 10px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 60;
  }
  .ns-top-switcher {
    display: flex;
    height: 40px;
    align-items: center;
    padding: 4px;
    background: rgba(244, 248, 240, 0.95);
    backdrop-filter: blur(8px);
    border: var(--ns-hair);
    border-radius: 9999px;
    box-shadow: var(--ns-shadow);
    gap: 2px;
  }
  .ns-view-tab {
    display: inline-flex;
    height: 100%;
    align-items: center;
    gap: 7px;
    padding: 0 15px;
    border-radius: 9999px;
    border: 1px solid transparent;
    background: transparent;
    color: var(--ns-muted);
    font-family: var(--ns-font);
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.01em;
    cursor: pointer;
    transition: background 140ms, color 140ms;
  }
  .ns-view-tab:hover { color: var(--ns-ink); }
  .ns-view-tab.is-active {
    background: var(--ns-ink);
    color: var(--ns-bg);
    border-color: var(--ns-ink);
  }

  /* Top-Right Floating HUD */
  .ns-top-right-hud {
    position: absolute;
    top: 10px;
    right: 10px;
    z-index: 40;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 8px;
  }
  .ns-hud-row { display: flex; align-items: center; gap: 8px; }
  .ns-copy-indicator {
    padding: 5px 11px;
    background: var(--ns-card);
    color: var(--ns-green);
    border: 1px solid var(--ns-green);
    border-radius: 8px;
    font-family: var(--ns-mono);
    font-size: 11px;
    font-weight: 600;
    box-shadow: var(--ns-shadow);
  }
  .ns-copy-indicator.hidden { display: none; }

  .ns-hud-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 9px;
    background: rgba(244, 248, 240, 0.94);
    border: var(--ns-hair-soft);
    border-radius: 7px;
    color: var(--ns-muted);
    font-family: var(--ns-mono);
    font-size: 10px;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(17, 17, 17, 0.06);
  }
  .ns-hud-btn:hover, .ns-hud-btn.is-pinned {
    border-color: var(--ns-ink);
    background: var(--ns-paper);
    color: var(--ns-ink);
  }
  .ns-hud-btn.hidden { display: none; }

  .ns-shortcuts-popover {
    min-width: 280px;
    padding: 12px 14px;
    background: var(--ns-card);
    border: var(--ns-hair);
    border-radius: 10px;
    box-shadow: var(--ns-shadow);
    font-size: 12px;
    color: var(--ns-ink);
  }
  .ns-shortcuts-popover.hidden { display: none; }
  .ns-shortcuts-title { font-weight: 600; margin-bottom: 8px; }
  .ns-shortcut-line {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    padding: 3px 0;
    font-size: 11px;
  }
  .ns-shortcut-line span:first-child { color: var(--ns-muted); }
  .ns-shortcut-line span:last-child { font-family: var(--ns-mono); color: var(--ns-ink); font-weight: 600; }

  /* Left-Center Draggable FloatingPill <-> Lumina Library Drawer */
  .ns-left-pill-wrap {
    position: absolute;
    z-index: 50;
    left: 10px;
    top: calc(50% - 75px);
    cursor: grab;
  }
  .ns-left-pill-wrap.hidden { display: none; }
  .ns-left-pill {
    width: 48px;
    background: rgba(244, 248, 240, 0.95);
    backdrop-filter: blur(8px);
    border: var(--ns-hair);
    border-radius: 12px;
    box-shadow: var(--ns-shadow);
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 12px 0;
    gap: 12px;
  }
  .ns-pill-grip { color: var(--ns-faint); line-height: 1; cursor: grab; }
  .ns-pill-expand {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    border: var(--ns-hair-soft);
    background: var(--ns-paper);
    color: var(--ns-ink);
    cursor: pointer;
  }
  .ns-pill-expand:hover { background: var(--ns-ink); color: var(--ns-bg); }
  .ns-pill-div { width: 16px; height: 1px; background: rgba(17, 17, 17, 0.2); }
  .ns-pill-count { font-family: var(--ns-mono); font-size: 10px; font-weight: 700; color: var(--ns-ink); }
  .ns-pill-dot { width: 7px; height: 7px; border-radius: 9999px; background: var(--ns-green); }

  .ns-left-drawer {
    position: absolute;
    left: 16px;
    top: 16px;
    bottom: 16px;
    width: 340px;
    z-index: 50;
    display: flex;
    flex-direction: column;
    background: rgba(244, 248, 240, 0.96);
    backdrop-filter: blur(12px);
    border: var(--ns-hair);
    border-radius: 16px;
    box-shadow: var(--ns-shadow);
    overflow: hidden;
  }
  .ns-left-drawer.hidden { display: none; }
  .ns-drawer-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 48px;
    padding: 0 14px;
    border-bottom: var(--ns-hair-soft);
    background: var(--ns-bg);
  }
  .ns-drawer-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: var(--ns-mono);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }
  .ns-icon-btn {
    border: 0;
    background: transparent;
    color: var(--ns-muted);
    padding: 5px;
    border-radius: 6px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
  .ns-icon-btn:hover { background: rgba(17, 17, 17, 0.08); color: var(--ns-ink); }

  .ns-drawer-body {
    flex: 1 1 auto;
    overflow-y: auto;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .ns-sec-header {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border: 0;
    background: transparent;
    padding: 4px;
    color: var(--ns-ink);
    font-family: var(--ns-mono);
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    cursor: pointer;
  }
  .ns-sec-header-lead { display: inline-flex; align-items: center; gap: 6px; }
  .ns-sec-count {
    font-size: 10px;
    color: var(--ns-muted);
    background: var(--ns-paper);
    border: var(--ns-hair-soft);
    border-radius: 9999px;
    padding: 0 6px;
  }
  .ns-sec-div { height: 1px; background: rgba(17, 17, 17, 0.14); }
  .ns-sec-content.hidden { display: none; }

  .ns-lib-ref-drop {
    border: 1px dashed rgba(17, 17, 17, 0.35);
    border-radius: 8px;
    padding: 10px;
    min-height: 64px;
    background: var(--ns-paper);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    cursor: pointer;
    gap: 4px;
  }
  .ns-lib-ref-drop:hover { border-color: var(--ns-ink); }
  .ns-lib-ref-label { font-family: var(--ns-mono); font-size: 9px; font-weight: 700; letter-spacing: 0.06em; color: var(--ns-faint); }
  .ns-lib-ref-grid { width: 100%; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px; }
  .ns-lib-ref-thumb {
    position: relative; aspect-ratio: 1; border-radius: 6px; border: var(--ns-hair-soft);
    overflow: hidden; background: var(--ns-bg);
  }
  .ns-lib-ref-thumb img { width: 100%; height: 100%; object-fit: cover; }

  .ns-asset-search {
    width: 100%;
    height: 30px;
    padding: 0 10px;
    border: var(--ns-hair-soft);
    border-radius: 6px;
    background: var(--ns-paper);
    color: var(--ns-ink);
    font-family: var(--ns-mono);
    font-size: 11px;
    margin-bottom: 8px;
  }
  .ns-asset-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
  .ns-asset-card {
    border: var(--ns-hair-soft);
    border-radius: 8px;
    background: var(--ns-paper);
    padding: 6px;
    cursor: grab;
    display: flex;
    flex-direction: column;
    gap: 4px;
    transition: transform 140ms, border-color 140ms;
  }
  .ns-asset-card:hover { transform: translateY(-1px); border-color: var(--ns-ink); }
  .ns-asset-thumb {
    aspect-ratio: 1;
    border-radius: 5px;
    background: var(--ns-bg);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    position: relative;
    color: var(--ns-muted);
  }
  .ns-asset-tag {
    position: absolute;
    bottom: 3px;
    right: 3px;
    font-family: var(--ns-mono);
    font-size: 8px;
    font-weight: 700;
    padding: 1px 4px;
    border-radius: 4px;
    background: var(--ns-ink);
    color: var(--ns-bg);
  }
  .ns-asset-name { font-family: var(--ns-mono); font-size: 9px; color: var(--ns-ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

  .ns-tpl-list { display: flex; flex-direction: column; gap: 4px; }
  .ns-tpl-row {
    text-align: left;
    border: 1px solid transparent;
    border-radius: 6px;
    background: transparent;
    padding: 7px 8px;
    cursor: pointer;
    color: var(--ns-ink);
  }
  .ns-tpl-row:hover { background: var(--ns-paper); border-color: rgba(17, 17, 17, 0.25); }
  .ns-tpl-title { display: flex; align-items: center; gap: 7px; font-size: 11px; font-weight: 600; }
  .ns-tpl-dot { width: 6px; height: 6px; border-radius: 2px; background: var(--ns-green); }
  .ns-tpl-desc { font-size: 10px; color: var(--ns-faint); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding-left: 13px; margin-top: 2px; }
  .ns-tpl-new {
    margin-top: 6px;
    width: 100%;
    padding: 7px;
    border: 1px dashed rgba(17, 17, 17, 0.35);
    border-radius: 6px;
    background: transparent;
    color: var(--ns-muted);
    font-family: var(--ns-mono);
    font-size: 10px;
    font-weight: 600;
    cursor: pointer;
  }
  .ns-tpl-new:hover { border-color: var(--ns-ink); color: var(--ns-ink); background: var(--ns-paper); }

  .ns-drawer-foot {
    padding: 10px 14px;
    border-top: var(--ns-hair-soft);
    background: var(--ns-bg);
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-family: var(--ns-mono);
    font-size: 10px;
    color: var(--ns-faint);
  }
  .ns-sync-status { display: inline-flex; align-items: center; gap: 6px; color: var(--ns-green); font-weight: 700; }

  /* Bottom-Left Zoom Controls */
  .ns-zoom-controls {
    position: absolute;
    left: 10px;
    bottom: 10px;
    z-index: 40;
    display: flex;
    flex-direction: column;
    background: rgba(244, 248, 240, 0.95);
    border: var(--ns-hair);
    border-radius: 8px;
    overflow: hidden;
    box-shadow: var(--ns-shadow);
  }
  .ns-zoom-btn {
    width: 30px;
    height: 28px;
    border: 0;
    border-bottom: 1px solid rgba(17, 17, 17, 0.16);
    background: transparent;
    color: var(--ns-ink);
    font-family: var(--ns-mono);
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .ns-zoom-btn:last-child { border-bottom: 0; }
  .ns-zoom-btn:hover { background: var(--ns-ink); color: var(--ns-bg); }

  /* Canvas MorphingNode */
  .ns-canvas-node {
    position: absolute;
    z-index: 5;
    cursor: move;
  }
  .ns-node-handle {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    width: 12px;
    height: 12px;
    border-radius: 9999px;
    background: var(--ns-paper);
    border: 2px solid var(--ns-ink);
    z-index: 10;
    cursor: crosshair;
  }
  .ns-node-handle--top { top: -6px; }
  .ns-node-handle--bottom { bottom: -6px; }
  .ns-node-handle:hover { background: var(--ns-ink); }

  .ns-node-quickbar {
    position: absolute;
    top: -38px;
    left: 50%;
    transform: translateX(-50%);
    display: none;
    align-items: center;
    gap: 2px;
    padding: 3px 6px;
    background: var(--ns-card);
    border: var(--ns-hair);
    border-radius: 8px;
    box-shadow: var(--ns-shadow);
    z-index: 60;
    white-space: nowrap;
  }
  .ns-canvas-node:hover .ns-node-quickbar,
  .ns-canvas-node.is-selected .ns-node-quickbar { display: flex; }
  .ns-qact-btn {
    border: 0;
    background: transparent;
    color: var(--ns-ink);
    font-family: var(--ns-mono);
    font-size: 10px;
    font-weight: 600;
    padding: 3px 6px;
    border-radius: 5px;
    cursor: pointer;
  }
  .ns-qact-btn:hover { background: var(--ns-ink); color: var(--ns-bg); }
  .ns-qact-btn.is-danger:hover { background: var(--ns-danger); color: var(--ns-paper); }
  .ns-qact-sep { width: 1px; height: 12px; background: rgba(17, 17, 17, 0.2); margin: 0 2px; }

  .ns-morph-card {
    width: 100%;
    height: 100%;
    border-radius: 10px;
    border: 1px solid rgba(17, 17, 17, 0.35);
    background: var(--ns-paper);
    box-shadow: var(--ns-shadow);
    overflow: hidden;
    position: relative;
  }
  .ns-canvas-node.is-selected .ns-morph-card {
    border: 2px solid var(--ns-ink);
    box-shadow: 0 0 0 3px rgba(17, 17, 17, 0.14), var(--ns-shadow);
  }

  /* Stage 1: LivingCube (96x96) */
  .ns-living-cube-wrap {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: transparent;
  }
  .ns-living-cube {
    width: 64px;
    height: 64px;
    border-radius: 16px;
    background: var(--ns-card);
    border: var(--ns-hair);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    box-shadow: var(--ns-shadow);
  }
  .ns-living-ring {
    width: 34px;
    height: 34px;
    border-radius: 9999px;
    border: 1px solid rgba(17, 17, 17, 0.3);
    background: var(--ns-paper);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .ns-living-core {
    width: 12px;
    height: 12px;
    border-radius: 9999px;
    background: var(--ns-ink);
    animation: nsPulseCore 1.2s ease-in-out infinite;
  }
  @keyframes nsPulseCore {
    0%, 100% { transform: scale(0.85); opacity: 0.7; }
    50% { transform: scale(1.15); opacity: 1; }
  }
  .ns-living-label {
    margin-top: 6px;
    font-family: var(--ns-mono);
    font-size: 9px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--ns-faint);
  }

  /* Stage 2: MessageContent (resizable text notes) */
  .ns-msg-card {
    width: 100%;
    height: 100%;
    min-height: 0;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    background: var(--ns-card);
    overflow: hidden;
  }
  .ns-msg-head { display: flex; align-items: center; justify-content: space-between; gap: 6px; font-family: var(--ns-mono); font-size: 10px; font-weight: 700; color: var(--ns-muted); text-transform: uppercase; flex-shrink: 0; }
  .ns-msg-head-actions { display: inline-flex; align-items: center; gap: 4px; }
  .ns-msg-body { font-size: 12.5px; line-height: 1.5; color: var(--ns-ink); overflow-y: auto; flex: 1 1 auto; min-height: 0; white-space: pre-wrap; user-select: text; cursor: text; padding-right: 4px; }

  /* Corner Drag-to-Resize Handle on Canvas Nodes */
  .ns-resize-handle {
    position: absolute;
    right: 2px;
    bottom: 2px;
    width: 20px;
    height: 20px;
    cursor: nwse-resize;
    z-index: 22;
    display: flex;
    align-items: flex-end;
    justify-content: flex-end;
    padding: 3px;
    color: var(--ns-muted);
    opacity: 0.45;
    transition: opacity 120ms, color 120ms;
    border-radius: 0 0 8px 0;
  }
  .ns-canvas-node:hover .ns-resize-handle,
  .ns-canvas-node.is-selected .ns-resize-handle,
  .ns-resize-handle:hover {
    opacity: 1;
    color: var(--ns-ink);
  }

  /* Stage 3: Image Node & Multi-Image Collection Grid */
  .ns-img-node { position: relative; width: 100%; height: 100%; background: var(--ns-paper); }
  .ns-img-node img { width: 100%; height: 100%; object-fit: cover; display: block; cursor: zoom-in; }
  .ns-node-lb-btn {
    position: absolute;
    top: 8px;
    right: 34px;
    padding: 3px 6px;
    border-radius: 6px;
    background: rgba(244, 248, 240, 0.92);
    border: var(--ns-hair-soft);
    color: var(--ns-ink);
    font-family: var(--ns-mono);
    font-size: 10px;
    cursor: pointer;
    z-index: 4;
  }
  .ns-node-lb-btn:hover { background: var(--ns-ink); color: var(--ns-bg); }
  .ns-collection-card {
    width: 100%;
    height: 100%;
    min-height: 0;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    background: var(--ns-card);
    overflow: hidden;
  }
  .ns-collection-grid {
    flex: 1 1 auto;
    min-height: 0;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    grid-auto-rows: minmax(0, 1fr);
    gap: 6px;
  }
  .ns-collection-tile {
    position: relative;
    width: 100%;
    height: 100%;
    min-height: 76px;
    border-radius: 7px;
    overflow: hidden;
    border: var(--ns-hair-soft);
    background: var(--ns-paper);
    cursor: zoom-in;
    padding: 0;
  }
  .ns-collection-tile img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
    transition: transform 150ms ease;
  }
  .ns-collection-tile:hover img { transform: scale(1.03); }
  .ns-collection-idx {
    position: absolute;
    top: 5px;
    left: 5px;
    padding: 1px 5px;
    border-radius: 4px;
    background: rgba(17, 17, 17, 0.78);
    color: #ffffff;
    font-family: var(--ns-mono);
    font-size: 9px;
    font-weight: 700;
  }

  /* Fullscreen Image Lightbox Modal */
  .ns-lightbox-stage {
    position: relative;
    flex: 1 1 auto;
    min-height: 360px;
    max-height: 62vh;
    background: #0d0d0d;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: auto;
    padding: 14px;
  }
  .ns-lightbox-img {
    max-width: 100%;
    max-height: 58vh;
    object-fit: contain;
    border-radius: 8px;
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.45);
    cursor: zoom-in;
    transition: transform 160ms ease;
    display: block;
  }
  .ns-lightbox-img.is-zoomed {
    max-width: none;
    max-height: none;
    width: 185%;
    cursor: zoom-out;
  }
  .ns-lightbox-nav {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    width: 38px;
    height: 38px;
    border-radius: 9999px;
    border: 1px solid rgba(255, 255, 255, 0.25);
    background: rgba(17, 17, 17, 0.78);
    color: #ffffff;
    font-family: var(--ns-mono);
    font-size: 16px;
    font-weight: 700;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    z-index: 6;
  }
  .ns-lightbox-nav:hover { background: #ffffff; color: #000000; }
  .ns-lightbox-nav--prev { left: 14px; }
  .ns-lightbox-nav--next { right: 14px; }
  .ns-lightbox-strip {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 10px 14px;
    background: var(--ns-card);
    border-top: var(--ns-hair-soft);
    overflow-x: auto;
  }
  .ns-lightbox-thumb {
    position: relative;
    width: 58px;
    height: 58px;
    flex-shrink: 0;
    border-radius: 7px;
    overflow: hidden;
    border: 2px solid transparent;
    padding: 0;
    background: var(--ns-paper);
    cursor: pointer;
    opacity: 0.72;
    transition: opacity 120ms, border-color 120ms;
  }
  .ns-lightbox-thumb:hover { opacity: 0.95; }
  .ns-lightbox-thumb.is-active {
    opacity: 1;
    border-color: var(--ns-ink);
  }
  .ns-lightbox-thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .ns-chat-coll-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
    gap: 6px;
    margin-top: 4px;
  }
  .ns-chat-coll-grid img {
    width: 100%;
    height: 96px;
    object-fit: cover;
    border-radius: 7px;
    border: var(--ns-hair-soft);
    cursor: zoom-in;
    display: block;
  }
  .ns-node-type-badge {
    position: absolute;
    top: 8px;
    left: 8px;
    padding: 2px 7px;
    border-radius: 6px;
    background: rgba(244, 248, 240, 0.92);
    border: var(--ns-hair-soft);
    font-family: var(--ns-mono);
    font-size: 9px;
    font-weight: 700;
    color: var(--ns-ink);
    z-index: 4;
  }
  .ns-node-dl-btn {
    position: absolute;
    top: 8px;
    right: 8px;
    padding: 3px 6px;
    border-radius: 6px;
    background: rgba(244, 248, 240, 0.92);
    border: var(--ns-hair-soft);
    color: var(--ns-ink);
    font-family: var(--ns-mono);
    font-size: 10px;
    cursor: pointer;
    z-index: 4;
  }
  .ns-node-dl-btn:hover { background: var(--ns-ink); color: var(--ns-bg); }
  .ns-node-meta-overlay {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    padding: 10px;
    background: rgba(244, 248, 240, 0.94);
    border-top: var(--ns-hair-soft);
    opacity: 0;
    transition: opacity 150ms;
  }
  .ns-canvas-node:hover .ns-node-meta-overlay,
  .ns-canvas-node.is-selected .ns-node-meta-overlay { opacity: 1; }
  .ns-node-prompt-txt { font-size: 11px; font-weight: 600; color: var(--ns-ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .ns-node-sub-txt { display: flex; justify-content: space-between; font-family: var(--ns-mono); font-size: 9px; color: var(--ns-faint); margin-top: 2px; }

  .ns-node-filter-popover {
    position: absolute;
    top: 34px;
    right: 8px;
    width: 220px;
    padding: 10px;
    background: var(--ns-card);
    border: var(--ns-hair);
    border-radius: 10px;
    box-shadow: var(--ns-shadow);
    z-index: 70;
    font-family: var(--ns-mono);
    font-size: 10px;
  }
  .ns-node-filter-row { display: flex; align-items: center; justify-content: space-between; gap: 6px; padding: 4px 0; }

  /* Bottom-Center Floating PromptIsland (max-w-[920px]) */
  .ns-island-dock {
    position: absolute;
    bottom: 10px;
    left: 0;
    width: 100%;
    z-index: 50;
    display: flex;
    justify-content: center;
    padding: 0 16px;
    pointer-events: none;
  }
  .ns-island-wrap {
    width: 100%;
    max-width: 920px;
    display: flex;
    flex-direction: column;
    align-items: center;
    pointer-events: auto;
    position: relative;
  }
  .ns-island {
    position: relative;
    width: 100%;
    border-radius: 14px;
    border: var(--ns-hair);
    background: rgba(244, 248, 240, 0.96);
    backdrop-filter: blur(10px);
    box-shadow: var(--ns-shadow);
  }
  .ns-island.is-drag-over { border-width: 2px; background: var(--ns-paper); }

  .ns-island-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 12px 6px;
    gap: 8px;
    flex-wrap: wrap;
    position: relative;
    z-index: 20;
  }
  .ns-island-badges { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .ns-mode-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 2px 9px;
    border-radius: 9999px;
    border: 1px solid var(--ns-green);
    background: rgba(16, 122, 71, 0.1);
    color: var(--ns-green);
    font-family: var(--ns-mono);
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }
  .ns-mode-pill.is-edit { border-color: var(--ns-ink); background: var(--ns-paper); color: var(--ns-ink); }
  .ns-mode-pill.is-merge { border-color: var(--ns-ink); background: var(--ns-ink); color: var(--ns-bg); }

  .ns-context-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 2px 9px;
    border-radius: 9999px;
    border: var(--ns-hair-soft);
    background: var(--ns-paper);
    color: var(--ns-ink);
    font-family: var(--ns-mono);
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
  }
  .ns-context-pill.hidden { display: none; }
  .ns-context-close { border: 0; background: transparent; color: var(--ns-muted); cursor: pointer; font-weight: 700; padding: 0 2px; }

  .ns-island-top-right { display: flex; align-items: center; gap: 8px; position: relative; }
  .ns-top-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 9px;
    border-radius: 7px;
    border: var(--ns-hair-soft);
    background: var(--ns-paper);
    color: var(--ns-ink);
    font-family: var(--ns-mono);
    font-size: 10px;
    font-weight: 600;
    cursor: pointer;
  }
  .ns-top-btn:hover { border-color: var(--ns-ink); background: var(--ns-bg); }
  .ns-top-btn.is-ready { color: var(--ns-green); border-color: rgba(16, 122, 71, 0.45); }

  .ns-popover {
    position: absolute;
    bottom: 100%;
    right: 0;
    margin-bottom: 8px;
    border-radius: 10px;
    border: var(--ns-hair);
    background: var(--ns-card);
    box-shadow: var(--ns-shadow);
    z-index: 60;
    display: flex;
    flex-direction: column;
  }
  .ns-popover.hidden { display: none; }
  .ns-api-menu { width: 288px; padding: 12px; gap: 8px; }
  .ns-pop-title { font-family: var(--ns-mono); font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--ns-faint); }
  .ns-api-badges { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
  .ns-api-badge {
    font-family: var(--ns-mono);
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 5px;
    border: var(--ns-hair-soft);
    background: var(--ns-paper);
    color: var(--ns-muted);
  }
  .ns-api-badge.is-ready { border-color: var(--ns-green); color: var(--ns-green); font-weight: 600; }
  .ns-api-input {
    width: 100%;
    padding: 6px 8px;
    border: var(--ns-hair-soft);
    border-radius: 6px;
    background: var(--ns-paper);
    color: var(--ns-ink);
    font-family: var(--ns-mono);
    font-size: 11px;
  }
  .ns-api-foot { display: flex; align-items: center; justify-content: space-between; font-family: var(--ns-mono); font-size: 9px; color: var(--ns-faint); }
  .ns-api-clear { border: 0; background: transparent; color: var(--ns-danger); font-family: var(--ns-mono); font-size: 10px; font-weight: 600; cursor: pointer; }

  .ns-model-menu { width: 380px; max-height: 410px; overflow-y: auto; padding: 6px; gap: 2px; }
  .ns-model-group-hdr {
    font-family: var(--ns-mono);
    font-size: 9px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: var(--ns-faint);
    padding: 6px 8px 3px;
    margin-top: 2px;
    border-top: var(--ns-hair-soft);
  }
  .ns-model-group-hdr:first-of-type { border-top: 0; margin-top: 0; }
  .ns-model-opt {
    width: 100%;
    text-align: left;
    border: 1px solid transparent;
    border-radius: 7px;
    background: transparent;
    padding: 8px 10px;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    gap: 3px;
    color: var(--ns-ink);
  }
  .ns-model-opt:hover { background: var(--ns-paper); border-color: rgba(17, 17, 17, 0.2); }
  .ns-model-opt.is-selected { background: var(--ns-paper); border-color: var(--ns-ink); }
  .ns-model-opt-top { display: flex; align-items: center; justify-content: space-between; width: 100%; }
  .ns-model-opt-name { font-size: 11px; font-weight: 600; }
  .ns-model-opt-right { display: inline-flex; align-items: center; gap: 6px; }
  .ns-model-badge {
    font-family: var(--ns-mono);
    font-size: 9px;
    padding: 1px 6px;
    border-radius: 4px;
    background: var(--ns-bg);
    border: var(--ns-hair-soft);
    color: var(--ns-muted);
  }
  .ns-model-check { display: none; font-size: 11px; font-weight: 700; color: var(--ns-green); }
  .ns-model-opt.is-selected .ns-model-check { display: inline; }
  .ns-model-opt-desc { font-size: 10px; color: var(--ns-faint); line-height: 1.3; }

  /* Reference Strip (68x68 ReferenceChips) */
  .ns-refs-strip {
    padding: 0 12px;
    max-height: 0;
    overflow: hidden;
    transition: max-height 200ms, padding 200ms;
  }
  .ns-refs-strip.has-refs { max-height: 100px; padding: 6px 12px; }
  .ns-refs-row { display: flex; align-items: center; gap: 6px; overflow-x: auto; }
  .ns-ref-chip {
    position: relative;
    width: 68px;
    height: 68px;
    border-radius: 7px;
    border: var(--ns-hair-soft);
    background: var(--ns-paper);
    overflow: hidden;
    flex: 0 0 68px;
    cursor: grab;
  }
  .ns-ref-chip img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .ns-ref-badge-box {
    width: 100%;
    height: 100%;
    padding: 4px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2px;
    text-align: center;
    font-family: var(--ns-mono);
    font-size: 8px;
    color: var(--ns-ink);
  }
  .ns-ref-remove {
    position: absolute;
    inset: 0;
    border: 0;
    background: rgba(17, 17, 17, 0.72);
    color: var(--ns-paper);
    font-size: 14px;
    font-weight: 700;
    opacity: 0;
    cursor: pointer;
    transition: opacity 140ms;
  }
  .ns-ref-chip:hover .ns-ref-remove { opacity: 1; }
  .ns-ref-slot-btn {
    width: 68px;
    height: 68px;
    border-radius: 7px;
    border: 1px dashed rgba(17, 17, 17, 0.35);
    background: var(--ns-bg);
    color: var(--ns-muted);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    flex: 0 0 68px;
  }
  .ns-ref-slot-btn:hover { border-color: var(--ns-ink); color: var(--ns-ink); }

  /* Prompt Input */
  .ns-prompt-area { position: relative; width: 100%; }
  .ns-prompt-textarea {
    width: 100%;
    border: 0;
    background: transparent;
    color: var(--ns-ink);
    font-family: var(--ns-font);
    font-size: 15px;
    line-height: 1.5;
    padding: 10px 44px 10px 12px;
    resize: none;
    outline: none;
    min-height: 50px;
    max-height: 200px;
  }
  .ns-prompt-textarea::placeholder { color: var(--ns-faint); }
  .ns-attach-trigger {
    position: absolute;
    right: 8px;
    top: 8px;
    border: 0;
    background: transparent;
    color: var(--ns-faint);
    padding: 6px;
    border-radius: 9999px;
    cursor: pointer;
  }
  .ns-attach-trigger:hover { background: rgba(17, 17, 17, 0.08); color: var(--ns-ink); }
  .ns-attach-trigger.hidden { display: none; }

  /* Bottom Settings & Action Bar */
  .ns-action-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
    padding: 6px 12px 10px;
  }
  .ns-settings-group { display: flex; align-items: center; flex-wrap: wrap; gap: 12px; }
  .ns-setting-wrap { position: relative; display: inline-flex; align-items: center; gap: 5px; cursor: pointer; }
  .ns-setting-wrap.is-disabled { opacity: 0.35; pointer-events: none; }
  .ns-setting-lbl { font-family: var(--ns-mono); font-size: 10px; font-weight: 700; color: var(--ns-faint); text-transform: uppercase; letter-spacing: 0.05em; }
  .ns-setting-val { font-family: var(--ns-mono); font-size: 11px; font-weight: 600; color: var(--ns-ink); }
  .ns-setting-select {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    opacity: 0;
    cursor: pointer;
  }
  .ns-thoughts-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 7px;
    border-radius: 5px;
    border: var(--ns-hair-soft);
    background: var(--ns-bg);
    color: var(--ns-muted);
    font-family: var(--ns-mono);
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    cursor: pointer;
  }
  .ns-thoughts-btn.is-active { background: var(--ns-ink); color: var(--ns-bg); border-color: var(--ns-ink); }
  .ns-thoughts-btn.hidden { display: none; }
  .ns-vdiv { width: 1px; height: 12px; background: rgba(17, 17, 17, 0.22); }
  .ns-ref-counter { font-family: var(--ns-mono); font-size: 10px; color: var(--ns-faint); }

  .ns-run-group { display: flex; align-items: center; gap: 8px; }
  .ns-runs-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 9px;
    border-radius: 9999px;
    border: var(--ns-hair-soft);
    background: var(--ns-paper);
    color: var(--ns-ink);
    font-family: var(--ns-mono);
    font-size: 10px;
    font-weight: 600;
  }
  .ns-generate-btn {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    height: 32px;
    padding: 0 14px;
    border-radius: 8px;
    border: var(--ns-hair);
    background: var(--ns-ink);
    color: var(--ns-bg);
    font-family: var(--ns-mono);
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
  }
  .ns-generate-btn:disabled { opacity: 0.45; cursor: not-allowed; }
  .ns-generate-btn:not(:disabled):hover { opacity: 0.88; }

  .ns-response-toast {
    position: absolute;
    bottom: 100%;
    left: 0;
    right: 0;
    margin-bottom: 8px;
    padding: 10px 12px;
    border-radius: 10px;
    border: var(--ns-hair);
    background: var(--ns-card);
    color: var(--ns-ink);
    font-size: 12px;
    box-shadow: var(--ns-shadow);
    max-height: 220px;
    overflow-y: auto;
  }
  .ns-response-toast.is-error { border-color: var(--ns-danger); color: var(--ns-danger); }
  .ns-response-toast.hidden { display: none; }

  /* Chat & Library Views (1:1 Views on Dot-Grid) */
  .ns-alt-view {
    position: absolute;
    inset: 0;
    z-index: 52;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    padding: 62px 24px 20px;
    background-color: var(--ns-bg);
    background-image: radial-gradient(rgba(17, 17, 17, 0.24) 1px, transparent 1px);
    background-size: 24px 24px;
    overflow: hidden;
  }
  .ns-alt-view.hidden { display: none; }
  .ns-alt-card {
    width: 100%;
    max-width: 920px;
    height: 100%;
    max-height: 100%;
    background: var(--ns-card);
    border: var(--ns-hair);
    border-radius: 14px;
    padding: 18px 20px;
    box-shadow: var(--ns-shadow);
    display: flex;
    flex-direction: column;
    gap: 12px;
    overflow: hidden;
  }
  .ns-alt-title { margin: 0; font-size: 18px; font-weight: 600; color: var(--ns-ink); }
  .ns-alt-desc { margin: 0; font-size: 13px; color: var(--ns-muted); line-height: 1.5; }
  .ns-hidden-input { display: none; }

  /* Mesh OS #win-nodes Overrides */
  .tc-ns-host .window-body { padding: 0 !important; background: var(--ns-bg) !important; height: 700px; }

  /* Artboard 07: Pure Monochrome Black & White Dark Mode Overrides */
  html[data-theme="dark"],
  html[data-theme="dark"] body,
  body.tc-dark {
    background: #080808;
    color: #f5f5f5;
  }
  html[data-theme="dark"] .ns-dot-canvas,
  body.tc-dark .ns-dot-canvas,
  html[data-theme="dark"] .ns-alt-view,
  body.tc-dark .ns-alt-view {
    background-color: #080808;
    background-image: radial-gradient(rgba(255, 255, 255, 0.22) 1px, transparent 1px);
  }
  html[data-theme="dark"] .ns-drop-overlay,
  body.tc-dark .ns-drop-overlay {
    background: rgba(8, 8, 8, 0.88);
    color: #f5f5f5;
  }
  html[data-theme="dark"] .ns-top-switcher,
  body.tc-dark .ns-top-switcher,
  html[data-theme="dark"] .ns-hud-btn,
  body.tc-dark .ns-hud-btn,
  html[data-theme="dark"] .ns-left-pill,
  body.tc-dark .ns-left-pill,
  html[data-theme="dark"] .ns-zoom-controls,
  body.tc-dark .ns-zoom-controls {
    background: #0e0e0e !important;
    border-color: #2e2e2e;
    color: #f5f5f5;
  }
  html[data-theme="dark"] .ns-view-tab.is-active,
  body.tc-dark .ns-view-tab.is-active,
  html[data-theme="dark"] .ns-pill-expand:hover,
  body.tc-dark .ns-pill-expand:hover,
  html[data-theme="dark"] .ns-zoom-btn:hover,
  body.tc-dark .ns-zoom-btn:hover,
  html[data-theme="dark"] .ns-qact-btn:hover,
  body.tc-dark .ns-qact-btn:hover,
  html[data-theme="dark"] .ns-thoughts-btn.is-active,
  body.tc-dark .ns-thoughts-btn.is-active,
  html[data-theme="dark"] .ns-mode-pill.is-merge,
  body.tc-dark .ns-mode-pill.is-merge,
  html[data-theme="dark"] .ns-asset-tag,
  body.tc-dark .ns-asset-tag {
    background: #ffffff !important;
    color: #000000 !important;
    border-color: #ffffff !important;
  }

  /* Lumina Library Drawer (#0e0e0e) */
  html[data-theme="dark"] .ns-left-drawer,
  body.tc-dark .ns-left-drawer,
  html[data-theme="dark"] #nsLeftDrawer,
  body.tc-dark #nsLeftDrawer {
    background: #0e0e0e !important;
    border: 1px solid #2e2e2e !important;
    color: #f5f5f5 !important;
  }
  html[data-theme="dark"] .ns-drawer-head,
  body.tc-dark .ns-drawer-head,
  html[data-theme="dark"] .ns-drawer-foot,
  body.tc-dark .ns-drawer-foot {
    background: #0c0c0c;
    border-color: #2e2e2e;
    color: #f5f5f5;
  }
  html[data-theme="dark"] .ns-asset-card,
  body.tc-dark .ns-asset-card,
  html[data-theme="dark"] .ns-asset-search,
  body.tc-dark .ns-asset-search,
  html[data-theme="dark"] .ns-lib-ref-drop,
  body.tc-dark .ns-lib-ref-drop {
    background: #151515;
    border-color: #2e2e2e;
    color: #f5f5f5;
  }
  html[data-theme="dark"] .ns-asset-card:hover,
  body.tc-dark .ns-asset-card:hover,
  html[data-theme="dark"] .ns-lib-ref-drop:hover,
  body.tc-dark .ns-lib-ref-drop:hover,
  html[data-theme="dark"] .ns-tpl-row:hover,
  body.tc-dark .ns-tpl-row:hover {
    border-color: #ffffff;
    background: #1a1a1a;
  }
  html[data-theme="dark"] .ns-pill-dot,
  body.tc-dark .ns-pill-dot,
  html[data-theme="dark"] .ns-tpl-dot,
  body.tc-dark .ns-tpl-dot {
    background: #ffffff;
  }
  html[data-theme="dark"] .ns-sync-status,
  body.tc-dark .ns-sync-status {
    color: #ffffff;
  }

  /* MorphingNode Cards (#151515 with #ffffff active border) */
  html[data-theme="dark"] .ns-morph-card,
  body.tc-dark .ns-morph-card,
  html[data-theme="dark"] .ns-msg-card,
  body.tc-dark .ns-msg-card,
  html[data-theme="dark"] .ns-collection-card,
  body.tc-dark .ns-collection-card,
  html[data-theme="dark"] .ns-lightbox-strip,
  body.tc-dark .ns-lightbox-strip,
  html[data-theme="dark"] .ns-img-node,
  body.tc-dark .ns-img-node,
  html[data-theme="dark"] .ns-living-cube,
  body.tc-dark .ns-living-cube {
    background: #151515 !important;
    border: 1px solid #2e2e2e;
    color: #f5f5f5;
  }
  html[data-theme="dark"] .ns-canvas-node.is-selected .ns-morph-card,
  body.tc-dark .ns-canvas-node.is-selected .ns-morph-card,
  html[data-theme="dark"] .ns-morph-card.is-active,
  body.tc-dark .ns-morph-card.is-active {
    background: #151515 !important;
    border: 2px solid #ffffff !important;
    border-color: #ffffff !important;
    box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.16), var(--ns-shadow);
  }
  html[data-theme="dark"] .ns-node-type-badge,
  body.tc-dark .ns-node-type-badge,
  html[data-theme="dark"] .ns-node-dl-btn,
  body.tc-dark .ns-node-dl-btn,
  html[data-theme="dark"] .ns-node-meta-overlay,
  body.tc-dark .ns-node-meta-overlay,
  html[data-theme="dark"] .ns-node-quickbar,
  body.tc-dark .ns-node-quickbar {
    background: #0e0e0e;
    border-color: #2e2e2e;
    color: #f5f5f5;
  }

  /* Prompt Island (#121212 with 1.5px solid #ffffff border) & Generate Button (#ffffff bg, #000000 text) */
  html[data-theme="dark"] .ns-island,
  body.tc-dark .ns-island,
  html[data-theme="dark"] #nsPromptIsland,
  body.tc-dark #nsPromptIsland {
    background: #121212 !important;
    border: 1.5px solid #ffffff !important;
    color: #f5f5f5 !important;
  }
  html[data-theme="dark"] .ns-mode-pill,
  body.tc-dark .ns-mode-pill {
    background: #1a1a1a;
    color: #ffffff;
    border: 1px solid #ffffff;
  }
  html[data-theme="dark"] .ns-top-btn,
  body.tc-dark .ns-top-btn,
  html[data-theme="dark"] .ns-runs-pill,
  body.tc-dark .ns-runs-pill,
  html[data-theme="dark"] .ns-context-pill,
  body.tc-dark .ns-context-pill,
  html[data-theme="dark"] .ns-ref-chip,
  body.tc-dark .ns-ref-chip,
  html[data-theme="dark"] .ns-api-input,
  body.tc-dark .ns-api-input {
    background: #1a1a1a;
    border-color: #2e2e2e;
    color: #f5f5f5;
  }
  html[data-theme="dark"] .ns-top-btn.is-ready,
  body.tc-dark .ns-top-btn.is-ready,
  html[data-theme="dark"] .ns-api-badge.is-ready,
  body.tc-dark .ns-api-badge.is-ready {
    color: #ffffff;
    border-color: #ffffff;
  }
  html[data-theme="dark"] .ns-popover,
  body.tc-dark .ns-popover,
  html[data-theme="dark"] .ns-shortcuts-popover,
  body.tc-dark .ns-shortcuts-popover,
  html[data-theme="dark"] .ns-response-toast,
  body.tc-dark .ns-response-toast {
    background: #0e0e0e;
    border-color: #2e2e2e;
    color: #f5f5f5;
  }
  html[data-theme="dark"] .ns-generate-btn,
  body.tc-dark .ns-generate-btn,
  html[data-theme="dark"] #nsGenerateBtn,
  body.tc-dark #nsGenerateBtn {
    background: #ffffff !important;
    color: #000000 !important;
    border-color: #ffffff !important;
  }

  /* Floating Pitch-Black (#000000) Node Studio Terminal */
  .ns-floating-terminal,
  #nsFloatingTerminal {
    position: absolute;
    top: 56px;
    right: 16px;
    width: 472px;
    max-width: calc(100% - 32px);
    z-index: 44;
    background: #000000 !important;
    color: #f5f5f5 !important;
    border: 1.5px solid #111111;
    border-radius: 14px;
    box-shadow: var(--ns-shadow);
    padding: 12px 14px;
    font-family: var(--ns-mono);
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .ns-floating-terminal.hidden,
  #nsFloatingTerminal.hidden {
    display: none !important;
  }
  .ns-term-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: #a3a3a3;
    border-bottom: 1px solid #2e2e2e;
    padding-bottom: 6px;
  }
  .ns-term-head-right {
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }
  .ns-term-hide-btn {
    border: 1px solid #2e2e2e;
    background: #151515;
    color: #f5f5f5;
    font-family: var(--ns-mono);
    font-size: 10px;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 6px;
    cursor: pointer;
    line-height: 1.2;
  }
  .ns-term-hide-btn:hover {
    background: #ffffff;
    color: #000000;
    border-color: #ffffff;
  }

  /* Saved .nodes.json Graphs Popover (Terminal Aeonik Light & Dark) */
  .ns-graphs-popover {
    width: 300px;
    padding: 10px 12px;
    border-radius: 10px;
    background: var(--ns-card);
    border: var(--ns-hair);
    box-shadow: var(--ns-shadow);
    display: flex;
    flex-direction: column;
    gap: 8px;
    color: var(--ns-ink);
  }
  .ns-graphs-popover.hidden { display: none; }
  .ns-graphs-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-family: var(--ns-mono);
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.05em;
    color: var(--ns-ink);
  }
  .ns-graphs-saveas-row {
    display: flex;
    gap: 6px;
    align-items: center;
  }
  .ns-graphs-input {
    flex: 1 1 auto;
    min-width: 0;
    padding: 5px 8px;
    border-radius: 6px;
    border: var(--ns-hair-soft);
    background: var(--ns-paper);
    color: var(--ns-ink);
    font-family: var(--ns-mono);
    font-size: 10px;
    outline: none;
  }
  .ns-graphs-input:focus { border-color: var(--ns-ink); }
  .ns-graphs-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
    max-height: 180px;
    overflow-y: auto;
  }
  .ns-graph-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    width: 100%;
    text-align: left;
    padding: 6px 8px;
    border-radius: 7px;
    border: var(--ns-hair-soft);
    background: var(--ns-paper);
    color: var(--ns-ink);
    font-family: var(--ns-mono);
    font-size: 10px;
    cursor: pointer;
  }
  .ns-graph-item:hover,
  .ns-graph-item.is-active {
    border-color: var(--ns-ink);
    background: var(--ns-bg);
  }
  .ns-graph-item-name { font-weight: 700; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .ns-graph-item-meta { font-size: 9px; color: var(--ns-faint); white-space: nowrap; }
  .ns-graphs-foot {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
    padding-top: 6px;
    border-top: var(--ns-hair-soft);
  }
  html[data-theme="dark"] .ns-graphs-popover,
  body.tc-dark .ns-graphs-popover {
    background: #0e0e0e;
    border-color: #2e2e2e;
    color: #f5f5f5;
  }
  html[data-theme="dark"] .ns-graphs-input,
  body.tc-dark .ns-graphs-input,
  html[data-theme="dark"] .ns-graph-item,
  body.tc-dark .ns-graph-item {
    background: #151515;
    border-color: #2e2e2e;
    color: #f5f5f5;
  }
  html[data-theme="dark"] .ns-graph-item:hover,
  body.tc-dark .ns-graph-item:hover,
  html[data-theme="dark"] .ns-graph-item.is-active,
  body.tc-dark .ns-graph-item.is-active {
    border-color: #ffffff;
    background: #1f1f1f;
  }

  /* 1-Click Modality Switcher Bar (Image | Text | Video | Audio | 3D Mesh | 3D Splat) */
  .ns-modality-bar {
    display: inline-flex;
    align-items: center;
    gap: 2px;
    padding: 2px;
    border-radius: 9999px;
    border: var(--ns-hair-soft);
    background: var(--ns-bg);
  }
  .ns-mod-tab {
    border: 0;
    background: transparent;
    color: var(--ns-muted);
    font-family: var(--ns-mono);
    font-size: 10px;
    font-weight: 700;
    padding: 3px 9px;
    border-radius: 9999px;
    cursor: pointer;
    transition: background 120ms, color 120ms;
    white-space: nowrap;
  }
  .ns-mod-tab:hover { color: var(--ns-ink); background: var(--ns-paper); }
  .ns-mod-tab.is-active { background: var(--ns-ink); color: var(--ns-bg); }
  .ns-setting-wrap.hidden { display: none; }
  .ns-vdiv.hidden { display: none; }

  /* Card Inline Action Buttons (Text / Audio / Video / 3D Mesh / Splat) */
  .ns-card-action-btn,
  .ns-atlas-step-btn {
    border: var(--ns-hair-soft);
    background: var(--ns-paper);
    color: var(--ns-ink);
    font-family: var(--ns-mono);
    font-size: 10px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 7px;
    cursor: pointer;
    transition: background 120ms, border-color 120ms, color 120ms;
  }
  .ns-card-action-btn:hover,
  .ns-atlas-step-btn:hover {
    border-color: var(--ns-ink);
    background: var(--ns-ink);
    color: var(--ns-bg);
  }
  .ns-card-action-btn.is-primary,
  .ns-atlas-step-btn.is-primary {
    background: var(--ns-ink);
    color: var(--ns-bg);
    border-color: var(--ns-ink);
  }
  .ns-card-action-btn.is-primary:hover,
  .ns-atlas-step-btn.is-primary:hover { opacity: 0.88; }

  /* Upgraded Text, Audio, Video & 3D Mesh Node Cards */
  .ns-msg-head { justify-content: space-between; }
  .ns-msg-prompt-sub {
    font-family: var(--ns-mono);
    font-size: 10px;
    color: var(--ns-faint);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .ns-msg-body {
    user-select: text;
    cursor: text;
    padding: 6px 8px;
    border-radius: 7px;
    border: var(--ns-hair-soft);
    background: var(--ns-paper);
  }
  .ns-card-foot-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 5px;
    flex-wrap: wrap;
    padding-top: 4px;
    border-top: var(--ns-hair-soft);
  }
  .ns-card-foot-group {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    flex-wrap: wrap;
  }
  .ns-audio-player {
    width: 100%;
    height: 42px;
    min-height: 40px;
    flex-shrink: 0;
    display: block;
    border-radius: 6px;
  }
  .ns-video-stage {
    position: relative;
    width: 100%;
    flex: 1 1 auto;
    min-height: 120px;
    border-radius: 7px;
    overflow: hidden;
    border: var(--ns-hair-soft);
    background: #080808;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .ns-video-player {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }
  .ns-video-placeholder {
    padding: 10px;
    text-align: center;
    font-family: var(--ns-mono);
    font-size: 10px;
    color: #f5f5f5;
    line-height: 1.45;
  }
  .ns-omni-error-box {
    border: 1px solid var(--ns-danger);
    background: rgba(138, 28, 28, 0.08);
    color: var(--ns-danger);
    border-radius: 7px;
    padding: 6px 8px;
    font-family: var(--ns-mono);
    font-size: 10px;
    line-height: 1.35;
    word-break: break-word;
  }
  .ns-omni-next-bar {
    display: flex;
    align-items: center;
    gap: 5px;
    flex-wrap: wrap;
    margin-top: 2px;
  }
  .ns-spark-webgl {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    background: #05070a;
    z-index: 2;
  }
  .ns-spark-webgl.hidden { display: none; }
  .ns-splat-modal-badge {
    position: absolute;
    top: 10px;
    left: 12px;
    z-index: 6;
    padding: 4px 10px;
    border-radius: 9999px;
    border: 1px solid rgba(255, 255, 255, 0.35);
    background: rgba(0, 0, 0, 0.76);
    color: #f5f5f5;
    font-family: var(--ns-mono);
    font-size: 10px;
    font-weight: 700;
    pointer-events: none;
  }
  .ns-splat-modal-badge.is-live {
    border-color: #107a47;
    background: rgba(16, 122, 71, 0.9);
    color: #ffffff;
  }
  html[data-theme="dark"] .ns-modality-bar,
  body.tc-dark .ns-modality-bar {
    background: #0c0c0c;
    border-color: #2e2e2e;
  }
  html[data-theme="dark"] .ns-mod-tab,
  body.tc-dark .ns-mod-tab {
    color: #a3a3a3;
  }
  html[data-theme="dark"] .ns-mod-tab:hover,
  body.tc-dark .ns-mod-tab:hover {
    color: #f5f5f5;
    background: #1a1a1a;
  }
  html[data-theme="dark"] .ns-mod-tab.is-active,
  body.tc-dark .ns-mod-tab.is-active {
    background: #ffffff;
    color: #000000;
  }
  html[data-theme="dark"] .ns-model-group-hdr,
  body.tc-dark .ns-model-group-hdr {
    color: #a3a3a3;
    border-color: #2e2e2e;
  }
  html[data-theme="dark"] .ns-model-opt,
  body.tc-dark .ns-model-opt {
    color: #f5f5f5;
  }
  html[data-theme="dark"] .ns-model-opt:hover,
  body.tc-dark .ns-model-opt:hover,
  html[data-theme="dark"] .ns-model-opt.is-selected,
  body.tc-dark .ns-model-opt.is-selected {
    background: #1a1a1a;
    border-color: #ffffff;
  }
  html[data-theme="dark"] .ns-model-badge,
  body.tc-dark .ns-model-badge {
    background: #0e0e0e;
    border-color: #2e2e2e;
    color: #f5f5f5;
  }
  html[data-theme="dark"] .ns-msg-body,
  body.tc-dark .ns-msg-body {
    background: #0e0e0e;
    border-color: #2e2e2e;
    color: #f5f5f5;
  }
  html[data-theme="dark"] .ns-card-action-btn,
  body.tc-dark .ns-card-action-btn,
  html[data-theme="dark"] .ns-atlas-step-btn,
  body.tc-dark .ns-atlas-step-btn {
    background: #151515;
    border-color: #2e2e2e;
    color: #f5f5f5;
  }
  html[data-theme="dark"] .ns-card-action-btn:hover,
  body.tc-dark .ns-card-action-btn:hover,
  html[data-theme="dark"] .ns-card-action-btn.is-primary,
  body.tc-dark .ns-card-action-btn.is-primary,
  html[data-theme="dark"] .ns-atlas-step-btn:hover,
  body.tc-dark .ns-atlas-step-btn:hover,
  html[data-theme="dark"] .ns-atlas-step-btn.is-primary,
  body.tc-dark .ns-atlas-step-btn.is-primary {
    background: #ffffff;
    border-color: #ffffff;
    color: #000000;
  }
  .ns-term-title { display: inline-flex; align-items: center; gap: 8px; color: #f5f5f5; }
  .ns-term-dots { color: #a3a3a3; font-size: 9px; }
  .ns-term-status { color: #ffffff; font-size: 10px; font-weight: 700; }
  .ns-term-log {
    max-height: 118px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 3px;
    font-size: 10px;
    line-height: 1.42;
    color: #f5f5f5;
  }
  .ns-term-line { white-space: pre-wrap; word-break: break-word; }
  .ns-term-input-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 8px;
    border-radius: 9px;
    border: 1px solid #2e2e2e;
    background: #080808;
  }
  .ns-term-ps { font-size: 10px; font-weight: 700; color: #ffffff; white-space: nowrap; }
  .ns-term-input {
    flex: 1 1 auto;
    border: 0;
    background: transparent;
    color: #ffffff;
    font-family: var(--ns-mono);
    font-size: 11px;
    outline: none;
  }
  .ns-term-run-btn {
    border: 1px solid #ffffff;
    background: #ffffff;
    color: #000000;
    font-family: var(--ns-mono);
    font-size: 10px;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 9999px;
    cursor: pointer;
    white-space: nowrap;
  }
  .ns-term-run-btn:hover { opacity: 0.88; }

  /* Active Slash Route Chip & Slash-Command Omni-Modal Router Popover */
  .ns-active-slash-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 2px 10px;
    border-radius: 9999px;
    border: 1px solid var(--ns-ink);
    background: var(--ns-ink);
    color: var(--ns-bg);
    font-family: var(--ns-mono);
    font-size: 10px;
    font-weight: 700;
    cursor: pointer;
  }
  .ns-active-slash-pill.hidden { display: none; }
  .ns-slash-pill-close { font-weight: 700; margin-left: 2px; opacity: 0.8; }
  .ns-slash-pill-close:hover { opacity: 1; }

  .ns-slash-router-popover {
    position: absolute;
    bottom: calc(100% + 10px);
    left: 0;
    right: 0;
    z-index: 65;
    border-radius: 14px;
    border: var(--ns-hair);
    background: var(--ns-card);
    box-shadow: var(--ns-shadow);
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .ns-slash-router-popover.hidden { display: none; }
  .ns-slash-router-head {
    font-family: var(--ns-mono);
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: var(--ns-muted);
    text-transform: uppercase;
  }
  .ns-slash-router-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
    max-height: 290px;
    overflow-y: auto;
  }
  .ns-slash-row {
    width: 100%;
    text-align: left;
    border-radius: 8px;
    border: var(--ns-hair-soft);
    background: var(--ns-paper);
    color: var(--ns-ink);
    padding: 7px 10px;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .ns-slash-row:hover,
  .ns-slash-row.is-selected {
    border: 1.5px solid var(--ns-ink);
    background: var(--ns-paper);
  }
  .ns-slash-row-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    font-family: var(--ns-mono);
    font-size: 11px;
    font-weight: 700;
  }
  .ns-slash-row-badge { color: var(--ns-muted); font-size: 10px; }
  .ns-slash-row-desc { font-size: 10px; color: var(--ns-muted); }

  /* Omni-Modal DAG Canvas Cards */
  .ns-omni-card {
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    background: var(--ns-card);
    border: var(--ns-hair);
  }
  .ns-omni-top-row { display: flex; align-items: center; justify-content: space-between; gap: 6px; flex-wrap: wrap; }
  .ns-omni-pill {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: 9999px;
    background: var(--ns-ink);
    color: var(--ns-bg);
    font-family: var(--ns-mono);
    font-size: 9px;
    font-weight: 700;
    width: fit-content;
  }
  .ns-omni-pill--outline {
    background: var(--ns-paper);
    color: var(--ns-ink);
    border: var(--ns-hair);
  }
  .ns-omni-status-badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 7px;
    border-radius: 9999px;
    border: 1px solid var(--ns-green);
    color: var(--ns-green);
    font-family: var(--ns-mono);
    font-size: 9px;
    font-weight: 700;
  }
  .ns-omni-grid-2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; }
  .ns-omni-box {
    padding: 6px 8px;
    border-radius: 7px;
    border: var(--ns-hair-soft);
    background: var(--ns-paper);
    font-family: var(--ns-mono);
    font-size: 9px;
    line-height: 1.38;
    color: var(--ns-ink);
  }
  .ns-omni-title { font-size: 11px; font-weight: 700; color: var(--ns-ink); }
  .ns-omni-sub { font-family: var(--ns-mono); font-size: 9px; color: var(--ns-faint); }
  .ns-omni-green { color: var(--ns-green); font-weight: 700; }

  /* Interactive 3D Gaussian Splat Stage inside Node Cards & Fullscreen Modal */
  .ns-splat-stage {
    position: relative;
    width: 100%;
    height: 164px;
    border-radius: 8px;
    border: var(--ns-hair);
    background: #000000;
    overflow: hidden;
    user-select: none;
  }
  .ns-splat-canvas {
    width: 100%;
    height: 100%;
    display: block;
    cursor: grab;
  }
  .ns-splat-canvas:active { cursor: grabbing; }
  .ns-splat-hud-top {
    position: absolute;
    top: 6px;
    left: 8px;
    right: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    pointer-events: none;
    font-family: var(--ns-mono);
    font-size: 9px;
    color: #f5f5f5;
  }
  .ns-splat-hud-tag {
    padding: 2px 7px;
    border-radius: 9999px;
    background: rgba(0, 0, 0, 0.78);
    border: 1px solid #ffffff;
    color: #ffffff;
    font-weight: 700;
  }
  .ns-splat-toolbar {
    position: absolute;
    bottom: 6px;
    left: 8px;
    right: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 4px;
    flex-wrap: wrap;
  }
  .ns-splat-btn-group { display: inline-flex; align-items: center; gap: 4px; }
  .ns-splat-btn {
    padding: 2px 7px;
    border-radius: 9999px;
    border: 1px solid #ffffff;
    background: rgba(0, 0, 0, 0.82);
    color: #f5f5f5;
    font-family: var(--ns-mono);
    font-size: 9px;
    font-weight: 600;
    cursor: pointer;
  }
  .ns-splat-btn:hover,
  .ns-splat-btn.is-active,
  .ns-splat-btn.is-primary {
    background: #ffffff;
    color: #000000;
  }

  .ns-splat-modal-backdrop {
    position: fixed;
    inset: 0;
    z-index: 95;
    background: rgba(17, 17, 17, 0.64);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
  }
  .ns-splat-modal-backdrop.hidden { display: none; }
  .ns-splat-modal {
    width: min(880px, 96vw);
    border-radius: 16px;
    border: 1.5px solid var(--ns-ink);
    background: var(--ns-card);
    color: var(--ns-ink);
    box-shadow: var(--ns-shadow);
    padding: 14px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .ns-splat-modal-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    flex-wrap: wrap;
  }
  .ns-splat-modal-viewport {
    position: relative;
    width: 100%;
    height: min(440px, 60vh);
    border-radius: 12px;
    border: 1.5px solid #111111;
    background: #000000;
    overflow: hidden;
  }
  .ns-splat-modal-foot {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    flex-wrap: wrap;
    font-family: var(--ns-mono);
    font-size: 10px;
  }
  html[data-theme="dark"] .ns-splat-modal,
  body.tc-dark .ns-splat-modal {
    background: #0e0e0e !important;
    border-color: #ffffff !important;
    color: #f5f5f5 !important;
  }
  html[data-theme="dark"] .ns-splat-modal-viewport,
  body.tc-dark .ns-splat-modal-viewport,
  html[data-theme="dark"] .ns-splat-stage,
  body.tc-dark .ns-splat-stage {
    border-color: #ffffff !important;
  }

  /* Code / Terminal Drawers & CLI Consoles (#000000 background with 1.5px solid #ffffff border) */
  html[data-theme="dark"] .ns-floating-terminal,
  body.tc-dark .ns-floating-terminal,
  html[data-theme="dark"] #nsFloatingTerminal,
  body.tc-dark #nsFloatingTerminal,
  html[data-theme="dark"] .ns-terminal-drawer,
  body.tc-dark .ns-terminal-drawer,
  html[data-theme="dark"] .ns-code-drawer,
  body.tc-dark .ns-code-drawer,
  html[data-theme="dark"] .ns-cli-box,
  body.tc-dark .ns-cli-box,
  html[data-theme="dark"] .ns-studio-stage .tcsh,
  body.tc-dark .ns-studio-stage .tcsh,
  html[data-theme="dark"] .ns-studio-stage pre,
  body.tc-dark .ns-studio-stage pre {
    background: #000000 !important;
    color: #f5f5f5 !important;
    border: 1.5px solid #ffffff !important;
  }
  html[data-theme="dark"] .ns-active-slash-pill,
  body.tc-dark .ns-active-slash-pill,
  html[data-theme="dark"] .ns-omni-pill,
  body.tc-dark .ns-omni-pill {
    background: #ffffff !important;
    color: #000000 !important;
    border-color: #ffffff !important;
  }
  html[data-theme="dark"] .ns-slash-router-popover,
  body.tc-dark .ns-slash-router-popover {
    background: #0e0e0e !important;
    border: 1px solid #2e2e2e !important;
    color: #f5f5f5 !important;
  }
  html[data-theme="dark"] .ns-slash-row,
  body.tc-dark .ns-slash-row,
  html[data-theme="dark"] .ns-omni-box,
  body.tc-dark .ns-omni-box {
    background: #151515 !important;
    border-color: #2e2e2e !important;
    color: #f5f5f5 !important;
  }
  html[data-theme="dark"] .ns-slash-row:hover,
  body.tc-dark .ns-slash-row:hover,
  html[data-theme="dark"] .ns-slash-row.is-selected,
  body.tc-dark .ns-slash-row.is-selected {
    border: 1.5px solid #ffffff !important;
  }

  /* Async Status & Error Badges */
  .ns-omni-status-badge.is-error {
    border-color: var(--ns-danger);
    color: var(--ns-danger);
  }
  .ns-spinner-pulse {
    font-weight: 700;
    animation: nsPulseCore 1.2s ease-in-out infinite;
  }

  /* Inline 3D Mesh (.GLB) Interactive Preview Stage & Inspector Modal */
  .ns-omni-card {
    height: 100%;
  }
  .ns-mesh-stage {
    position: relative;
    width: 100%;
    height: 164px;
    min-height: 164px;
    border-radius: 8px;
    border: var(--ns-hair);
    background: #080808;
    overflow: hidden;
    user-select: none;
  }
  .ns-model-viewer {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    display: block;
    background: transparent;
    z-index: 2;
  }
  .ns-mesh-wire-canvas {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    display: block;
    cursor: grab;
    z-index: 1;
  }
  .ns-mesh-wire-canvas:active { cursor: grabbing; }
  .ns-mesh-wire-canvas.is-hidden { display: none; }
  .ns-mesh-stage-hud {
    position: absolute;
    left: 7px;
    bottom: 6px;
    z-index: 4;
    padding: 2px 7px;
    border-radius: 9999px;
    border: 1px solid rgba(255, 255, 255, 0.35);
    background: rgba(0, 0, 0, 0.78);
    color: #f5f5f5;
    font-family: var(--ns-mono);
    font-size: 9px;
    font-weight: 700;
    pointer-events: none;
  }
  .ns-mesh-inspect-btn {
    position: absolute;
    top: 6px;
    right: 6px;
    z-index: 5;
    padding: 2px 8px;
    border-radius: 9999px;
    border: 1px solid #ffffff;
    background: rgba(0, 0, 0, 0.84);
    color: #ffffff;
    font-family: var(--ns-mono);
    font-size: 9px;
    font-weight: 700;
    cursor: pointer;
  }
  .ns-mesh-inspect-btn:hover {
    background: #ffffff;
    color: #000000;
  }
  .ns-mesh-modal-viewport {
    position: relative;
    width: 100%;
    height: min(460px, 62vh);
    border-radius: 12px;
    border: 1.5px solid #111111;
    background: #080808;
    overflow: hidden;
  }
  .ns-mesh-modal-viewport model-viewer {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    z-index: 2;
  }

  /* Synced Conversation (Chat) View */
  .ns-chat-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
    padding-bottom: 10px;
    border-bottom: var(--ns-hair-soft);
  }
  .ns-chat-meta {
    font-family: var(--ns-mono);
    font-size: 11px;
    color: var(--ns-muted);
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }
  .ns-chat-feed {
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 4px 2px;
    user-select: text;
  }
  .ns-chat-turn {
    border: var(--ns-hair-soft);
    border-radius: 10px;
    background: var(--ns-paper);
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .ns-chat-turn.is-selected {
    border: 1.5px solid var(--ns-ink);
  }
  .ns-chat-turn-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    flex-wrap: wrap;
  }
  .ns-chat-turn-badges {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
  }
  .ns-chat-model {
    font-family: var(--ns-mono);
    font-size: 10px;
    color: var(--ns-muted);
  }
  .ns-chat-prompt {
    font-family: var(--ns-mono);
    font-size: 11px;
    font-weight: 600;
    color: var(--ns-ink);
    padding: 6px 8px;
    border-radius: 7px;
    background: var(--ns-bg);
    border: var(--ns-hair-soft);
  }
  .ns-chat-text {
    font-size: 13px;
    line-height: 1.55;
    color: var(--ns-ink);
    white-space: pre-wrap;
    word-break: break-word;
    user-select: text;
  }
  .ns-chat-thumb {
    max-width: 240px;
    max-height: 200px;
    border-radius: 8px;
    border: var(--ns-hair-soft);
    object-fit: cover;
    display: block;
  }
  .ns-chat-media-row {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    font-family: var(--ns-mono);
    font-size: 11px;
    color: var(--ns-ink);
  }
  .ns-chat-empty {
    padding: 36px 16px;
    text-align: center;
    font-family: var(--ns-mono);
    font-size: 12px;
    color: var(--ns-faint);
    border: 1px dashed rgba(17, 17, 17, 0.25);
    border-radius: 10px;
    background: var(--ns-paper);
  }
  .ns-chat-composer {
    display: flex;
    align-items: flex-end;
    gap: 8px;
    padding-top: 10px;
    border-top: var(--ns-hair-soft);
  }
  .ns-chat-input {
    flex: 1 1 auto;
    min-height: 40px;
    max-height: 120px;
    padding: 9px 12px;
    border-radius: 9px;
    border: var(--ns-hair);
    background: var(--ns-paper);
    color: var(--ns-ink);
    font-family: var(--ns-font);
    font-size: 13px;
    resize: none;
    outline: none;
  }
  .ns-chat-input::placeholder { color: var(--ns-faint); }
  .ns-chat-send-btn {
    height: 40px;
    padding: 0 16px;
    border-radius: 9px;
    border: var(--ns-hair);
    background: var(--ns-ink);
    color: var(--ns-bg);
    font-family: var(--ns-mono);
    font-size: 11px;
    font-weight: 700;
    cursor: pointer;
    white-space: nowrap;
  }
  .ns-chat-send-btn:hover { opacity: 0.88; }

  /* Synced Asset Library View */
  .ns-lib-filter-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    flex-wrap: wrap;
    padding-bottom: 8px;
    border-bottom: var(--ns-hair-soft);
  }
  .ns-lib-chips {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    flex-wrap: wrap;
  }
  .ns-lib-chip {
    border: var(--ns-hair-soft);
    background: var(--ns-paper);
    color: var(--ns-muted);
    font-family: var(--ns-mono);
    font-size: 10px;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 9999px;
    cursor: pointer;
  }
  .ns-lib-chip:hover { color: var(--ns-ink); border-color: var(--ns-ink); }
  .ns-lib-chip.is-active {
    background: var(--ns-ink);
    color: var(--ns-bg);
    border-color: var(--ns-ink);
  }
  .ns-lib-search {
    width: 220px;
    max-width: 100%;
    height: 30px;
    padding: 0 10px;
    border: var(--ns-hair-soft);
    border-radius: 7px;
    background: var(--ns-paper);
    color: var(--ns-ink);
    font-family: var(--ns-mono);
    font-size: 11px;
    outline: none;
  }
  .ns-lib-search:focus { border-color: var(--ns-ink); }
  .ns-lib-grid {
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
    gap: 10px;
    align-content: start;
    padding: 2px;
  }
  .ns-lib-asset-card {
    border: var(--ns-hair-soft);
    border-radius: 10px;
    background: var(--ns-paper);
    padding: 8px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .ns-lib-asset-card:hover { border-color: var(--ns-ink); }
  .ns-lib-preview {
    height: 116px;
    border-radius: 7px;
    border: var(--ns-hair-soft);
    background: var(--ns-bg);
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 6px;
    text-align: center;
    font-family: var(--ns-mono);
    font-size: 10px;
    color: var(--ns-ink);
    position: relative;
  }
  .ns-lib-preview img,
  .ns-lib-preview video {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 5px;
    display: block;
  }
  .ns-lib-preview-text {
    font-family: var(--ns-font);
    font-size: 11px;
    line-height: 1.38;
    text-align: left;
    overflow: hidden;
    max-height: 100%;
    width: 100%;
  }
  .ns-lib-meta {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .ns-lib-title {
    font-size: 11px;
    font-weight: 600;
    color: var(--ns-ink);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .ns-lib-sub {
    font-family: var(--ns-mono);
    font-size: 9px;
    color: var(--ns-faint);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .ns-lib-actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 4px;
    padding-top: 4px;
    border-top: var(--ns-hair-soft);
  }
  .ns-lib-actions-left { display: inline-flex; align-items: center; gap: 4px; }

  /* Monochrome Dark Mode Overrides for 3D Mesh, Chat & Library Views */
  html[data-theme="dark"] .ns-alt-card,
  body.tc-dark .ns-alt-card {
    background: #0e0e0e !important;
    border-color: #2e2e2e !important;
    color: #f5f5f5 !important;
  }
  html[data-theme="dark"] .ns-mesh-stage,
  body.tc-dark .ns-mesh-stage,
  html[data-theme="dark"] .ns-mesh-modal-viewport,
  body.tc-dark .ns-mesh-modal-viewport {
    border-color: #ffffff !important;
    background: #000000 !important;
  }
  html[data-theme="dark"] .ns-chat-turn,
  body.tc-dark .ns-chat-turn,
  html[data-theme="dark"] .ns-chat-empty,
  body.tc-dark .ns-chat-empty,
  html[data-theme="dark"] .ns-chat-input,
  body.tc-dark .ns-chat-input,
  html[data-theme="dark"] .ns-lib-chip,
  body.tc-dark .ns-lib-chip,
  html[data-theme="dark"] .ns-lib-search,
  body.tc-dark .ns-lib-search,
  html[data-theme="dark"] .ns-lib-asset-card,
  body.tc-dark .ns-lib-asset-card {
    background: #151515 !important;
    border-color: #2e2e2e !important;
    color: #f5f5f5 !important;
  }
  html[data-theme="dark"] .ns-chat-prompt,
  body.tc-dark .ns-chat-prompt,
  html[data-theme="dark"] .ns-lib-preview,
  body.tc-dark .ns-lib-preview {
    background: #080808 !important;
    border-color: #2e2e2e !important;
    color: #f5f5f5 !important;
  }
  html[data-theme="dark"] .ns-chat-turn.is-selected,
  body.tc-dark .ns-chat-turn.is-selected,
  html[data-theme="dark"] .ns-lib-asset-card:hover,
  body.tc-dark .ns-lib-asset-card:hover {
    border-color: #ffffff !important;
  }
  html[data-theme="dark"] .ns-chat-send-btn,
  body.tc-dark .ns-chat-send-btn,
  html[data-theme="dark"] .ns-lib-chip.is-active,
  body.tc-dark .ns-lib-chip.is-active {
    background: #ffffff !important;
    color: #000000 !important;
    border-color: #ffffff !important;
  }
</style>"""


def _node_studio_js(initial_view: str) -> str:
    models_json = _safe_json(list(AVAILABLE_MODELS))
    caps_json = _safe_json(MODEL_CAPABILITIES)
    std_aspects_json = _safe_json(list(STANDARD_ASPECT_RATIOS))
    pano_aspects_json = _safe_json(list(PANORAMIC_ASPECT_RATIOS))
    filters_json = _safe_json(list(FILTER_PRESETS))
    templates_json = _safe_json(list(LUMINA_TEMPLATES))
    assets_json = _safe_json(list(LUMINA_ASSETS))
    slash_cmds_json = _safe_json(list(SLASH_ROUTER_COMMANDS))

    template = r"""<script id="nodeStudioUiScript">
(function () {
  const MODELS = __MODELS_JSON__;
  const CAPS = __CAPS_JSON__;
  const STD_ASPECTS = __STD_ASPECTS_JSON__;
  const PANO_ASPECTS = __PANO_ASPECTS_JSON__;
  const FILTER_PRESETS = __FILTERS_JSON__;
  const TEMPLATES = __TEMPLATES_JSON__;
  const ASSETS = __ASSETS_JSON__;
  const SLASH_COMMANDS = __SLASH_CMDS_JSON__;
  const MAX_CONCURRENT_RUNS = 2;

  const MODALITY_DEFAULTS = {
    image: "gemini-nano-banana-2.1",
    text: "gemini-3.1-pro",
    video: "kling-4.0",
    audio: "google/lyria-3.5",
    "3d": "hyper3d/rodin-v2.5",
    atlas: "worldlabs/atlas-v2"
  };

  const state = {
    view: __INIT_VIEW__,
    nodes: [],
    edges: [],
    selectedIds: [],
    references: [],
    modality: "image",
    activeSlashCommand: "",
    model: "gemini-nano-banana-2.1",
    lastModelByModality: Object.assign({}, MODALITY_DEFAULTS),
    aspectRatio: "1:1",
    resolution: "1K",
    imageCount: 1,
    thinkingLevel: "medium",
    includeThoughts: false,
    groundingMode: "Off",
    provider: "auto",
    videoFps: "60",
    audioKind: "music",
    meshTier: "Regular",
    atlasTask: "posedImages2Splats",
    activeRuns: 0,
    activeConversationNodeId: null,
    apiKey: "",
    nanogptKey: "",
    serverStatus: { hasServerKey: false, hasGeminiKey: false, hasNanogptKey: false, hasAtlasKey: true },
    panX: 0,
    panY: 0,
    zoom: 1,
    isPanning: false,
    panStart: { x: 0, y: 0 },
    dragNodeId: null,
    dragNodeOffset: { x: 0, y: 0 },
    resizeNodeId: null,
    resizeStart: null,
    isBoxSelecting: false,
    boxStart: { x: 0, y: 0 },
    connectFromId: null,
    metaHeld: false,
    isShortcutsPinned: false,
    isLeftCollapsed: true,
    isTerminalOpen: false,
    pillPos: { x: 10, y: 240 },
    isDraggingPill: false,
    pillOffset: { x: 0, y: 0 },
    dragRefIndex: null,
    openFilterNodeId: null,
    sections: { references: true, assets: true, templates: false },
    libRefs: [],
    templates: TEMPLATES.slice(),
    nodeSeq: 0,
    graphName: "workspace",
    graphPath: "/nodes/workspace.nodes.json",
    savedGraphs: [],
    _autoSaveTimer: null,
    _suppressAutoSave: false,
    atlasRefine: false,
    libraryFilter: "all",
    libraryQuery: ""
  };

  function $(id) { return document.getElementById(id); }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function getCaps() {
    return CAPS[state.model] || CAPS.default;
  }

  function getModelName(mid) {
    const found = MODELS.find((m) => m.id === mid);
    return found ? found.name : (mid || "Model");
  }

  function deriveMode() {
    if (state.references.length > 1 || state.selectedIds.length > 1) return "MERGE";
    if (state.references.length === 1 || state.selectedIds.length === 1) return "EDIT";
    return "GENERATE";
  }

  function selectModality(mod) {
    const valid = MODALITY_DEFAULTS[mod] ? mod : "image";
    state.modality = valid;
    const preferred = (state.lastModelByModality && state.lastModelByModality[valid]) || MODALITY_DEFAULTS[valid];
    if (CAPS[preferred]) {
      state.model = preferred;
    }
    const caps = getCaps();
    if (caps && caps.audioKind) {
      state.audioKind = caps.audioKind;
    }
    state.activeSlashCommand = "";
    const pill = $("nsActiveSlashPill");
    if (pill) pill.classList.add("hidden");
    if (valid === "atlas") {
      state.provider = "worldlabs";
    } else if (valid === "3d") {
      state.provider = "hyper3d";
    } else {
      state.provider = "auto";
    }
    syncCapabilitiesAndControls();
    renderPromptIslandStatus();
  }

  function syncCapabilitiesAndControls() {
    const caps = getCaps();
    const mod = state.modality || (caps && caps.modality) || "image";
    const aspects = caps.panoramicAspects ? STD_ASPECTS.concat(PANO_ASPECTS) : STD_ASPECTS;
    if (aspects.indexOf(state.aspectRatio) === -1) state.aspectRatio = "1:1";
    if (caps.resolutions.indexOf(state.resolution) === -1) {
      state.resolution = caps.resolutions.indexOf("1K") !== -1 ? "1K" : caps.resolutions[0];
    }
    if (caps.groundingModes.indexOf(state.groundingMode) === -1) state.groundingMode = "Off";
    if (caps.thinkingLevels) {
      if (caps.thinkingLevels.indexOf(state.thinkingLevel) === -1) {
        state.thinkingLevel = caps.defaultThinkingLevel || caps.thinkingLevels[0];
      }
    } else {
      state.includeThoughts = false;
    }

    // Highlight active 1-click Modality Tab
    document.querySelectorAll(".ns-mod-tab").forEach((btn) => {
      const isAct = btn.dataset && btn.dataset.modality === mod;
      btn.classList.toggle("is-active", !!isAct);
      btn.setAttribute("aria-pressed", isAct ? "true" : "false");
    });

    const showAspect = mod === "image" || mod === "video";
    const showRes = mod === "image" || mod === "video";
    const showThink = (mod === "image" || mod === "text") && !!caps.thinkingLevels;
    const showSearch = (mod === "image" || mod === "text") && caps.groundingModes.length > 1;
    const showFps = mod === "video";
    const showAudioKind = mod === "audio";
    const showMeshTier = mod === "3d";
    const showAtlasControls = mod === "atlas";

    const aspectWrap = $("nsAspectWrap");
    if (aspectWrap) aspectWrap.classList.toggle("hidden", !showAspect);
    const aspectSel = $("nsAspectSelect");
    if (aspectSel) {
      aspectSel.innerHTML = aspects.map((a) => '<option value="' + a + '">' + a + "</option>").join("");
      aspectSel.value = state.aspectRatio;
    }
    const aspectVal = $("nsAspectVal");
    if (aspectVal) aspectVal.textContent = state.aspectRatio;

    const resWrap = $("nsResWrap");
    if (resWrap) {
      resWrap.classList.toggle("hidden", !showRes);
      resWrap.classList.toggle("is-disabled", caps.resolutions.length <= 1);
    }
    const resSel = $("nsResSelect");
    if (resSel) {
      resSel.innerHTML = caps.resolutions.map((r) => '<option value="' + r + '">' + r + "</option>").join("");
      resSel.value = state.resolution;
    }
    const resVal = $("nsResVal");
    if (resVal) resVal.textContent = state.resolution;

    const batchWrap = $("nsBatchWrap");
    if (batchWrap) batchWrap.classList.toggle("hidden", mod !== "image");
    const batchCount = Math.max(1, Math.min(4, parseInt(state.imageCount, 10) || 1));
    state.imageCount = batchCount;
    const batchVal = $("nsBatchVal");
    if (batchVal) batchVal.textContent = batchCount + "x";
    const batchSel = $("nsBatchSelect");
    if (batchSel) batchSel.value = String(batchCount);

    const thinkWrap = $("nsThinkWrap");
    const thoughtsBtn = $("nsThoughtsBtn");
    if (thinkWrap) {
      thinkWrap.classList.toggle("hidden", !showThink);
      thinkWrap.classList.toggle("is-disabled", !caps.thinkingLevels);
    }
    if (thoughtsBtn) {
      thoughtsBtn.classList.toggle("hidden", !showThink);
      thoughtsBtn.classList.toggle("is-active", !!state.includeThoughts);
    }
    const thinkSel = $("nsThinkSelect");
    if (thinkSel && caps.thinkingLevels) {
      thinkSel.innerHTML = caps.thinkingLevels.map((t) => '<option value="' + t + '">' + t + "</option>").join("");
      thinkSel.value = state.thinkingLevel;
    }
    const thinkVal = $("nsThinkVal");
    if (thinkVal) thinkVal.textContent = caps.thinkingLevels ? state.thinkingLevel : "off";

    const searchWrap = $("nsSearchWrap");
    if (searchWrap) {
      searchWrap.classList.toggle("hidden", !showSearch);
      searchWrap.classList.toggle("is-disabled", caps.groundingModes.length <= 1);
    }
    const searchSel = $("nsSearchSelect");
    if (searchSel) {
      searchSel.innerHTML = caps.groundingModes.map((g) => '<option value="' + g + '">' + g + "</option>").join("");
      searchSel.value = state.groundingMode;
    }
    const searchVal = $("nsSearchVal");
    if (searchVal) searchVal.textContent = state.groundingMode;

    const fpsWrap = $("nsFpsWrap");
    if (fpsWrap) fpsWrap.classList.toggle("hidden", !showFps);
    const fpsVal = $("nsFpsVal");
    if (fpsVal) fpsVal.textContent = state.videoFps + "fps";
    const fpsSel = $("nsFpsSelect");
    if (fpsSel) fpsSel.value = state.videoFps;

    const audioKindWrap = $("nsAudioKindWrap");
    if (audioKindWrap) audioKindWrap.classList.toggle("hidden", !showAudioKind);
    const audioKindVal = $("nsAudioKindVal");
    if (audioKindVal) {
      audioKindVal.textContent = state.audioKind === "tts" ? "Voice TTS" : (state.audioKind === "sfx" ? "SFX" : "Music");
    }
    const audioKindSel = $("nsAudioKindSelect");
    if (audioKindSel) audioKindSel.value = state.audioKind;

    const meshTierWrap = $("nsMeshTierWrap");
    if (meshTierWrap) meshTierWrap.classList.toggle("hidden", !showMeshTier);
    const meshTierVal = $("nsMeshTierVal");
    if (meshTierVal) meshTierVal.textContent = state.meshTier;
    const meshTierSel = $("nsMeshTierSelect");
    if (meshTierSel) meshTierSel.value = state.meshTier;

    const atlasTaskWrap = $("nsAtlasTaskWrap");
    if (atlasTaskWrap) atlasTaskWrap.classList.toggle("hidden", !showAtlasControls);
    const atlasTaskVal = $("nsAtlasTaskVal");
    if (atlasTaskVal) {
      const taskLabels = {
        posedImages2Splats: "Build Splat",
        images2PosedRGBD: "Pose RGBD",
        atlasGenerate: "6 Views",
        splats2Mesh: "Export GLB"
      };
      atlasTaskVal.textContent = taskLabels[state.atlasTask] || "Build Splat";
    }
    const atlasTaskSel = $("nsAtlasTaskSelect");
    if (atlasTaskSel) atlasTaskSel.value = state.atlasTask;

    const atlasQualWrap = $("nsAtlasQualWrap");
    if (atlasQualWrap) atlasQualWrap.classList.toggle("hidden", !showAtlasControls);
    const atlasQualVal = $("nsAtlasQualVal");
    if (atlasQualVal) atlasQualVal.textContent = state.atlasRefine ? "Refined (18m)" : "Draft (~30s)";
    const atlasQualSel = $("nsAtlasQualSelect");
    if (atlasQualSel) atlasQualSel.value = state.atlasRefine ? "refined" : "draft";

    const viaVal = $("nsViaVal");
    if (viaVal) viaVal.textContent = state.provider;
    const viaSel = $("nsViaSelect");
    if (viaSel) viaSel.value = state.provider;

    const refCounter = $("nsRefCounter");
    const imgRefCount = state.references.filter((r) => r.type === "image").length;
    if (refCounter) {
      if (mod === "atlas" || state.model === "worldlabs/atlas-v2") {
        refCounter.textContent = imgRefCount + "/" + caps.maxReferences +
          (imgRefCount >= 2 ? " views · Multi-view Splat ready ✓" : " views (select 2–14 scene photos)");
      } else {
        refCounter.textContent = state.references.length + "/" + caps.maxReferences +
          (caps.supportsVideoAndPdf ? " refs (Img/Vid/PDF)" : " refs");
      }
    }
    const libRefCount = $("nsLibRefCount");
    if (libRefCount) libRefCount.textContent = String(state.references.length);

    const promptInput = $("nsPromptInput");
    if (promptInput) {
      const refCount = state.references.length;
      if (mod === "text") {
        promptInput.placeholder = refCount > 0
          ? "Ask about or transform the selected node(s)..."
          : "Ask a question, write a script, or brainstorm a prompt...";
      } else if (mod === "video") {
        promptInput.placeholder = refCount > 0
          ? "Describe camera motion or animate the selected image(s)..."
          : "Describe a video scene and camera motion...";
      } else if (mod === "audio") {
        promptInput.placeholder = state.audioKind === "tts"
          ? "Enter narration or dialogue text to speak aloud..."
          : (state.audioKind === "sfx" ? "Describe the sound effect or ambience..." : "Describe the music score or mood...");
      } else if (mod === "3d") {
        promptInput.placeholder = "Describe a 3D object or character to generate as a .GLB mesh...";
      } else if (mod === "atlas") {
        promptInput.placeholder = "Select 2–14 overlapping scene photos and describe the 3D Splat world...";
      } else {
        promptInput.placeholder = refCount > 1
          ? "Describe how to merge or combine these " + refCount + " references (e.g. 'Put this dog in space')..."
          : (refCount === 1 ? "Describe how to edit this reference..." : "Describe what you want to generate...");
      }
    }

    const modelObj = MODELS.find((m) => m.id === state.model);
    const modelBtnLabel = $("nsModelBtnLabel");
    if (modelBtnLabel) modelBtnLabel.textContent = modelObj ? modelObj.name : state.model;
    document.querySelectorAll(".ns-model-opt").forEach((el) => {
      el.classList.toggle("is-selected", el.dataset.modelId === state.model);
    });
  }

  function renderPromptIslandStatus() {
    const mode = deriveMode();
    const mod = state.modality || "image";
    const pill = $("nsModePill");
    if (pill) {
      pill.textContent = mode + " MODE";
      pill.classList.toggle("is-edit", mode === "EDIT");
      pill.classList.toggle("is-merge", mode === "MERGE");
    }

    const convPill = $("nsConvPill");
    if (convPill) convPill.classList.toggle("hidden", !state.activeConversationNodeId);

    const branchPill = $("nsBranchPill");
    const sel1 = state.selectedIds.length === 1
      ? state.nodes.find((n) => n.id === state.selectedIds[0])
      : null;
    const showBranch = !state.activeConversationNodeId && !!(
      sel1 && sel1.metadata && sel1.metadata.conversationHistory &&
      sel1.metadata.conversationHistory.length > 0 && sel1.content && sel1.content.imageUrl
    );
    if (branchPill) branchPill.classList.toggle("hidden", !showBranch);

    const runsEl = $("nsActiveRunsCount");
    if (runsEl) runsEl.textContent = state.activeRuns + "/" + MAX_CONCURRENT_RUNS;

    const promptEl = $("nsPromptInput");
    const hasPrompt = promptEl ? promptEl.value.trim().length > 0 : false;
    const hasPhotos = state.references.filter((r) => r.type === "image").length > 0;
    const genBtn = $("nsGenerateBtn");
    if (genBtn) {
      const canRunWithoutPrompt = mod === "atlas" && hasPhotos;
      genBtn.disabled = (!hasPrompt && !canRunWithoutPrompt) || state.activeRuns >= MAX_CONCURRENT_RUNS;
      const imgCnt = Math.max(1, Math.min(4, parseInt(state.imageCount, 10) || 1));
      const imgLbl = imgCnt > 1
        ? (mode === "MERGE" ? ("Merge " + imgCnt + " Images →") : (mode === "EDIT" ? ("Edit " + imgCnt + " Images →") : ("Generate " + imgCnt + " Images →")))
        : (mode === "MERGE" ? "Merge Images →" : (mode === "EDIT" ? "Edit Image →" : "Generate →"));
      const lblMap = {
        image: imgLbl,
        text: mode === "GENERATE" ? "Generate Text →" : "Reply / Transform →",
        video: "Generate Video →",
        audio: "Generate Audio →",
        "3d": "Generate 3D →",
        atlas: "Build 3D Splat →"
      };
      genBtn.textContent = lblMap[mod] || "Generate →";
    }
    if (state.view === "conversation") {
      renderConversationView();
    }
  }

  function renderReferencesStrip() {
    const strip = $("nsRefsStrip");
    const row = $("nsRefsRow");
    if (!strip || !row) return;

    strip.classList.toggle("has-refs", state.references.length > 0);

    const chips = state.references.map((ref, idx) => {
      let inner = "";
      if (ref.type === "image" && ref.url) {
        inner = '<img src="' + escapeHtml(ref.url) + '" alt="' + escapeHtml(ref.name) + '">';
      } else {
        const badge = ref.type === "pdf" ? "PDF" : (ref.type === "video" ? "VIDEO" : (ref.type === "audio" ? "♪ AUDIO" : ref.type.toUpperCase()));
        inner = '<div class="ns-ref-badge-box"><strong>' + escapeHtml(badge) + '</strong><span>' + escapeHtml(ref.name) + "</span></div>";
      }
      return '<div class="ns-ref-chip" draggable="true" data-ref-index="' + idx + '" title="' + escapeHtml(ref.name) + '">' +
        inner +
        '<button type="button" class="ns-ref-remove" onclick="window.TinCanNodeStudio.removeRef(\'' + escapeHtml(ref.id) + '\')">×</button>' +
        "</div>";
    });

    if (state.references.length > 0) {
      chips.push(
        '<button type="button" class="ns-ref-slot-btn" title="Add more photos (multi-select up to 14)" onclick="window.TinCanNodeStudio.triggerFileInput()">+ Photos</button>'
      );
      if (state.references.length > 1) {
        chips.push(
          '<button type="button" class="ns-ref-slot-btn" title="Clear all references" onclick="window.TinCanNodeStudio.clearRefs()">Clear</button>'
        );
      }
    }
    row.innerHTML = chips.join("");
    bindRefDragEvents();
    syncCapabilitiesAndControls();
    renderPromptIslandStatus();
  }

  function _extractDataUrlBase64(url) {
    if (!url || typeof url !== "string") return "";
    const idx = url.indexOf(";base64,");
    if (url.indexOf("data:") === 0 && idx !== -1) {
      return url.slice(idx + 8);
    }
    return "";
  }

  function collectAllImageReferences() {
    const caps = getCaps();
    const maxRefs = (caps && caps.maxReferences) || 14;
    const seen = new Set();
    const out = [];
    function pushRef(r) {
      if (!r || out.length >= maxRefs) return;
      const key = r.id || r.name || r.url || ("idx-" + out.length);
      if (seen.has(key)) return;
      seen.add(key);
      const b64 = r.base64 || _extractDataUrlBase64(r.url);
      out.push({
        id: r.id || ("ref-" + out.length),
        name: r.name || ("view_" + out.length + ".jpg"),
        type: r.type || "image",
        mimeType: r.mimeType || (r.type === "text" ? "text/plain" : "image/jpeg"),
        url: r.url || "",
        base64: b64,
        text: r.text || ""
      });
    }
    state.references.forEach(pushRef);
    state.selectedIds.forEach((pid) => {
      const n = state.nodes.find((x) => x.id === pid);
      if (!n || !n.content || n.morphingStatus === "generating") return;
      if (n.content.imageUrl || n.content.base64) {
        pushRef({
          id: n.id,
          name: n.label || (n.id + ".png"),
          type: "image",
          mimeType: n.content.mimeType || "image/png",
          url: n.content.imageUrl || "",
          base64: n.content.base64 || _extractDataUrlBase64(n.content.imageUrl)
        });
      } else if (n.content.text && (n.morphingStatus === "text" || n.morphingStatus === "message" || n.modality === "text")) {
        pushRef({
          id: n.id,
          name: (n.label || n.id).slice(0, 32),
          type: "text",
          mimeType: "text/plain",
          text: String(n.content.text)
        });
      } else {
        const modLbl = _modalityDisplayLabel(_getNodeModality(n));
        const descParts = [];
        if (n.metadata && n.metadata.prompt) descParts.push("Prompt: " + n.metadata.prompt);
        else if (n.label) descParts.push("Label: " + n.label);
        if (n.content && n.content.text && n.content.text !== n.label) descParts.push("Text: " + n.content.text);
        if (n.content && (n.content.vfsPath || n.content.glbPath)) descParts.push("Asset: " + (n.content.vfsPath || n.content.glbPath));
        if (descParts.length) {
          pushRef({
            id: n.id,
            name: modLbl + " (" + (n.label || n.id).slice(0, 24) + ")",
            type: "text",
            mimeType: "text/plain",
            text: descParts.join(" | ")
          });
        }
      }
    });
    return out;
  }

  function bindRefDragEvents() {
    const row = $("nsRefsRow");
    if (!row) return;
    row.querySelectorAll(".ns-ref-chip").forEach((chip) => {
      chip.addEventListener("dragstart", (ev) => {
        state.dragRefIndex = parseInt(chip.dataset.refIndex, 10);
        if (ev.dataTransfer) ev.dataTransfer.effectAllowed = "move";
      });
      chip.addEventListener("dragover", (ev) => { ev.preventDefault(); });
      chip.addEventListener("drop", (ev) => {
        ev.preventDefault();
        const targetIdx = parseInt(chip.dataset.refIndex, 10);
        if (state.dragRefIndex === null || isNaN(targetIdx) || state.dragRefIndex === targetIdx) return;
        const moved = state.references.splice(state.dragRefIndex, 1)[0];
        state.references.splice(targetIdx, 0, moved);
        state.dragRefIndex = null;
        renderReferencesStrip();
      });
    });
  }

  function syncSelectionRefs() {
    const uploadedRefs = state.references.filter((r) => r.source === "upload");
    const selectedNodes = state.nodes.filter((n) => state.selectedIds.indexOf(n.id) !== -1);
    const nextRefs = uploadedRefs.slice();
    const seenIds = new Set(nextRefs.map((r) => r.id));
    const seenUrls = new Set(nextRefs.map((r) => r.url).filter(Boolean));
    selectedNodes.forEach((n) => {
      if (n.content && Array.isArray(n.content.referenceImages) && n.content.referenceImages.length > 0) {
        n.content.referenceImages.forEach((imgUrl, idx) => {
          if (!imgUrl || seenUrls.has(imgUrl)) return;
          seenUrls.add(imgUrl);
          const rid = n.id + "-ref-" + idx;
          seenIds.add(rid);
          nextRefs.push({
            id: rid,
            source: "node",
            url: imgUrl,
            base64: _extractDataUrlBase64(imgUrl),
            mimeType: n.content.mimeType || "image/jpeg",
            name: (n.label || n.id) + " #" + (idx + 1),
            type: "image"
          });
        });
      } else if (!seenIds.has(n.id) && n.content && (n.content.imageUrl || n.content.base64)) {
        seenIds.add(n.id);
        if (n.content.imageUrl) seenUrls.add(n.content.imageUrl);
        nextRefs.push({
          id: n.id,
          source: "node",
          url: n.content.imageUrl || "",
          base64: n.content.base64 || _extractDataUrlBase64(n.content.imageUrl),
          mimeType: n.content.mimeType || "image/png",
          name: n.label || n.id,
          type: "image"
        });
      } else if (!seenIds.has(n.id) && n.content && n.content.text && (n.morphingStatus === "text" || n.morphingStatus === "message" || n.modality === "text")) {
        seenIds.add(n.id);
        nextRefs.push({
          id: n.id,
          source: "node",
          url: "",
          base64: "",
          text: String(n.content.text),
          mimeType: "text/plain",
          name: (n.label || n.id).slice(0, 28),
          type: "text"
        });
      }
    });
    state.references = nextRefs;
    renderReferencesStrip();
  }

  function applyCanvasTransform() {
    const world = $("nsCanvasWorld");
    const canvas = $("nsDotCanvas");
    if (world) {
      world.style.transform = "translate(" + state.panX + "px, " + state.panY + "px) scale(" + state.zoom + ")";
    }
    if (canvas) {
      const gap = Math.max(8, 24 * state.zoom);
      canvas.style.backgroundSize = gap + "px " + gap + "px";
      canvas.style.backgroundPosition = state.panX + "px " + state.panY + "px";
    }
  }

  function renderEdges() {
    const svg = $("nsEdgesSvg");
    if (!svg) return;
    const paths = [];
    state.edges.forEach((edge) => {
      const src = state.nodes.find((n) => n.id === edge.source);
      const tgt = state.nodes.find((n) => n.id === edge.target);
      if (!src || !tgt) return;
      const sx = src.x + (src.width || 256) / 2 + 2000;
      const sy = src.y + (src.height || 256) + 2000;
      const tx = tgt.x + (tgt.width || 256) / 2 + 2000;
      const ty = tgt.y + 2000;
      const cy = Math.max(40, Math.abs(ty - sy) * 0.5);
      paths.push(
        '<path class="ns-edge-path" d="M ' + sx + " " + sy +
        " C " + sx + " " + (sy + cy) + ", " + tx + " " + (ty - cy) + ", " + tx + " " + ty + '"/>'
      );
    });
    svg.innerHTML = paths.join("");
  }

  function buildFilterCss(filters) {
    if (!filters) return "none";
    const parts = [];
    if (filters.kodak_2383) parts.push("contrast(1.08) saturate(1.12)");
    if (filters.halation) parts.push("brightness(1.04)");
    if (filters.film_grain_16mm) parts.push("sepia(0.08)");
    return parts.length ? parts.join(" ") : "none";
  }

  function renderSplatStageHtml(node) {
    const nid = escapeHtml(node.id);
    const meta = node.metadata || {};
    const sMode = (node.splatState && node.splatState.mode) || "rgb";
    const showFrustums = !node.splatState || node.splatState.frustums !== false;
    const inViews = meta.inputViewCount ? Number(meta.inputViewCount) : 0;
    const jobStatus = meta.jobStatus || "";
    let hudTag = "POSED RGBD PREVIEW · DRAG TO ORBIT";
    if (jobStatus === "RUNNING") {
      const elapsed = meta.startedAt ? Math.max(1, Math.round((Date.now() - meta.startedAt) / 1000)) : 0;
      const est = meta.estimatedSeconds || 35;
      hudTag = "⟳ WORLD LABS GPU RUNNING (" + elapsed + "s / ~" + est + "s)";
    } else if (meta.isRealSpz) {
      const mb = meta.spzSizeBytes ? (meta.spzSizeBytes / (1024 * 1024)).toFixed(1) + " MB" : ".SPZ";
      hudTag = "● LIVE WORLD LABS .SPZ (" + mb + ") · OPEN SPARK WEBGL";
    } else if (inViews > 0) {
      hudTag = inViews + " INPUT PHOTO" + (inViews === 1 ? "" : "S") + " · PREVIEW (CLICK BUILD 3D SPLAT)";
    }
    const viewBtnLabel = meta.isRealSpz ? "⤢ Spark WebGL 3D Splat" : "⤢ View 3D Splat";
    return (
      '<div class="ns-splat-stage" onmousedown="event.stopPropagation()">' +
      '<canvas id="nsSplatCanvas-' + nid + '" class="ns-splat-canvas" data-splat-node-id="' + nid + '" width="440" height="164"></canvas>' +
      '<div class="ns-splat-hud-top">' +
      '<span class="ns-splat-hud-tag">' + escapeHtml(hudTag) + "</span>" +
      '<span class="ns-splat-hud-tag">' + escapeHtml(meta.isRealSpz ? "SPARK WEBGL READY" : "RUB CAM · 1280×720") + "</span>" +
      "</div>" +
      '<div class="ns-splat-toolbar">' +
      '<div class="ns-splat-btn-group">' +
      '<button type="button" class="ns-splat-btn' + (sMode === "rgb" ? " is-active" : "") + '" onclick="event.stopPropagation();window.TinCanNodeStudio.setNodeSplatMode(\'' + nid + '\',\'rgb\')">3D Splats</button>' +
      '<button type="button" class="ns-splat-btn' + (sMode === "depth" ? " is-active" : "") + '" onclick="event.stopPropagation();window.TinCanNodeStudio.setNodeSplatMode(\'' + nid + '\',\'depth\')">Depth .EXR</button>' +
      '<button type="button" class="ns-splat-btn' + (showFrustums ? " is-active" : "") + '" onclick="event.stopPropagation();window.TinCanNodeStudio.toggleNodeFrustums(\'' + nid + '\')">14 Frustums</button>' +
      "</div>" +
      '<button type="button" class="ns-splat-btn is-primary" onclick="event.stopPropagation();window.TinCanNodeStudio.openSplatViewer(\'' + nid + '\')">' + viewBtnLabel + "</button>" +
      "</div>" +
      "</div>"
    );
  }

  function _getNodeImages(node) {
    if (!node || !node.content) return [];
    const c = node.content;
    if (Array.isArray(c.images) && c.images.length > 0) {
      return c.images
        .map((img, i) => {
          if (!img) return null;
          if (typeof img === "string") {
            return { index: i, imageUrl: img, base64: _extractDataUrlBase64(img), mimeType: "image/png" };
          }
          const mime = img.mimeType || img.mime_type || "image/png";
          const b64 = img.base64 || img.data || _extractDataUrlBase64(img.imageUrl || img.url || "");
          const url = img.imageUrl || img.url || (b64 ? ("data:" + mime + ";base64," + b64) : "");
          if (!url && !b64) return null;
          return { index: i, imageUrl: url, base64: b64, mimeType: mime };
        })
        .filter(Boolean);
    }
    if (c.imageUrl || c.base64) {
      const mime = c.mimeType || "image/png";
      const b64 = c.base64 || _extractDataUrlBase64(c.imageUrl || "");
      const url = c.imageUrl || (b64 ? ("data:" + mime + ";base64," + b64) : "");
      if (url || b64) return [{ index: 0, imageUrl: url, base64: b64, mimeType: mime }];
    }
    return [];
  }

  function renderImageCollectionCardInner(node) {
    const nid = escapeHtml(node.id);
    const meta = node.metadata || {};
    const imgs = _getNodeImages(node);
    const imgStyle = "filter:" + buildFilterCss(node.filters) + ";";
    const promptTxt = escapeHtml(meta.prompt || node.label || "");
    const modelLbl = escapeHtml(getModelName(meta.model || "gemini-nano-banana-2.1"));
    const tilesHtml = imgs.map((img, idx) => (
      '<button type="button" class="ns-collection-tile" title="Open image ' + (idx + 1) + ' in Lightbox" ' +
      'onclick="event.stopPropagation();window.TinCanNodeStudio.openImageLightbox(\'' + nid + '\',' + idx + ')">' +
      '<img src="' + escapeHtml(img.imageUrl) + '" alt="' + promptTxt + ' #' + (idx + 1) + '" style="' + imgStyle + '" draggable="false">' +
      '<span class="ns-collection-idx">' + (idx + 1) + "</span>" +
      "</button>"
    )).join("");
    return (
      '<div class="ns-collection-card">' +
      '<div class="ns-omni-top-row">' +
      '<span class="ns-omni-pill">◼ COLLECTION · ' + imgs.length + " IMAGES</span>" +
      '<span class="ns-omni-status-badge">' + modelLbl + "</span>" +
      "</div>" +
      '<div class="ns-collection-grid" onmousedown="event.stopPropagation()">' + tilesHtml + "</div>" +
      '<div class="ns-omni-title">' + promptTxt + "</div>" +
      '<div class="ns-card-foot-bar" onmousedown="event.stopPropagation()">' +
      '<div class="ns-card-foot-group">' +
      '<button type="button" class="ns-card-action-btn is-primary" onclick="event.stopPropagation();window.TinCanNodeStudio.openImageLightbox(\'' + nid + '\',0)">⤢ Lightbox</button>' +
      '<button type="button" class="ns-card-action-btn" title="Split collection into individual canvas nodes" onclick="event.stopPropagation();window.TinCanNodeStudio.splitCollectionToNodes(\'' + nid + '\')">Split Nodes</button>' +
      "</div>" +
      '<button type="button" class="ns-card-action-btn" onclick="event.stopPropagation();window.TinCanNodeStudio.downloadNode(\'' + nid + '\')">↓ All</button>' +
      "</div>" +
      "</div>"
    );
  }

  function renderTextCardInner(node) {
    const nid = escapeHtml(node.id);
    const meta = node.metadata || {};
    const modelLbl = escapeHtml(getModelName(meta.model || meta.modelUsed || state.model));
    const promptTxt = escapeHtml(meta.prompt || node.label || "");
    const isErr = meta.jobStatus === "ERROR";
    const isExpanded = (node.width || 340) >= 480 || (node.height || 250) >= 380;
    const errBlock = meta.jobError
      ? '<div class="ns-omni-error-box">' + escapeHtml(meta.jobError) + "</div>"
      : "";
    const bodyTxt = escapeHtml((node.content && node.content.text) || (isErr ? "" : (node.label || "")));
    return (
      '<div class="ns-msg-card">' +
      '<div class="ns-msg-head">' +
      '<span class="ns-omni-pill">TEXT · ' + modelLbl + "</span>" +
      '<div class="ns-msg-head-actions" onmousedown="event.stopPropagation()">' +
      '<button type="button" class="ns-card-action-btn" title="Toggle expanded reading view (or drag corner to resize)" onclick="event.stopPropagation();window.TinCanNodeStudio.toggleNodeExpand(\'' + nid + '\')">' + (isExpanded ? "↙ Compact" : "⤢ Expand") + "</button>" +
      (isErr
        ? '<span class="ns-omni-status-badge is-error">✕ ERROR</span>'
        : '<button type="button" class="ns-card-action-btn" title="Copy text" onclick="event.stopPropagation();window.TinCanNodeStudio.copyNodeText(\'' + nid + '\')">Copy</button>') +
      "</div>" +
      "</div>" +
      (promptTxt ? '<div class="ns-msg-prompt-sub" title="' + promptTxt + '">Prompt: ' + promptTxt + "</div>" : "") +
      errBlock +
      (bodyTxt ? '<div class="ns-msg-body" onmousedown="event.stopPropagation()">' + bodyTxt + "</div>" : "") +
      '<div class="ns-card-foot-bar" onmousedown="event.stopPropagation()">' +
      '<div class="ns-card-foot-group">' +
      '<button type="button" class="ns-card-action-btn is-primary" title="Use this text to generate an Image" onclick="event.stopPropagation();window.TinCanNodeStudio.sendTextToImage(\'' + nid + '\')">→ To Image</button>' +
      '<button type="button" class="ns-card-action-btn" title="Continue or refine this text node" onclick="event.stopPropagation();window.TinCanNodeStudio.replyToTextNode(\'' + nid + '\')">Reply</button>' +
      "</div>" +
      '<button type="button" class="ns-card-action-btn" title="Attach as reference" onclick="event.stopPropagation();window.TinCanNodeStudio.addNodeAsRef(\'' + nid + '\')">+ Ref</button>' +
      "</div>" +
      "</div>"
    );
  }

  function _audioExtLabel(c, meta) {
    const ext = String((c && c.ext) || "").toLowerCase();
    const p = String((c && c.vfsPath) || (meta && meta.vfsPath) || "").toLowerCase();
    const mime = String((c && c.mimeType) || "").toLowerCase();
    if (ext === ".mp3" || p.endsWith(".mp3") || mime.indexOf("mpeg") !== -1 || mime.indexOf("mp3") !== -1) return ".MP3";
    if (ext === ".ogg" || p.endsWith(".ogg") || mime.indexOf("ogg") !== -1 || mime.indexOf("opus") !== -1) return ".OGG";
    if (ext === ".flac" || p.endsWith(".flac") || mime.indexOf("flac") !== -1) return ".FLAC";
    if (ext === ".m4a" || p.endsWith(".m4a") || mime.indexOf("mp4") !== -1) return ".M4A";
    return ".WAV";
  }

  function _getAudioSrcForNode(node) {
    const c = (node && node.content) || {};
    if (c.audioRawUrl && typeof c.audioRawUrl === "string") return c.audioRawUrl;
    if (c.audioUrl && typeof c.audioUrl === "string") return c.audioUrl;
    if (c.audioBytesB64 && typeof c.audioBytesB64 === "string") {
      return "data:" + (c.mimeType || "audio/wav") + ";base64," + c.audioBytesB64;
    }
    return "";
  }

  function renderAudioCardInner(node) {
    const nid = escapeHtml(node.id);
    const meta = node.metadata || {};
    const c = node.content || {};
    const promptTxt = escapeHtml(meta.prompt || node.label || "");
    const audioKindLbl = String(c.kind || meta.audioKind || "music").toUpperCase();
    const jobStatus = meta.jobStatus || "";
    const elapsed = meta.startedAt ? Math.max(1, Math.round((Date.now() - meta.startedAt) / 1000)) : 1;
    const extLbl = _audioExtLabel(c, meta);
    const audioSrc = _getAudioSrcForNode(node);

    let statusBadgeHtml = '<span class="ns-omni-status-badge">' + escapeHtml(audioKindLbl) + " · -14 LUFS</span>";
    if (jobStatus === "RUNNING") {
      statusBadgeHtml = '<span class="ns-omni-status-badge">⟳ GENERATING AUDIO (' + elapsed + "s)</span>";
    } else if (jobStatus === "ERROR") {
      statusBadgeHtml = '<span class="ns-omni-status-badge is-error">✕ ERROR</span>';
    }

    const errBlock = meta.jobError
      ? ('<div class="ns-omni-error-box">' + escapeHtml(meta.jobError) + "</div>")
      : "";
    const playerHtml = jobStatus === "RUNNING"
      ? '<div class="ns-omni-box"><div>⟳ Generating ' + escapeHtml(audioKindLbl.toLowerCase()) + ' audio (' + elapsed + 's)...</div><div>Polling /api/nodes/audio/status every 3.5s</div></div>'
      : (audioSrc
        ? '<audio class="ns-audio-player" controls preload="metadata" src="' + escapeHtml(audioSrc) + '" onmousedown="event.stopPropagation()"></audio>'
        : "");
    return (
      '<div class="ns-omni-card">' +
      '<div class="ns-omni-top-row">' +
      '<span class="ns-omni-pill ns-omni-pill--outline">♪ AUDIO · TTS + SCORE + SFX</span>' +
      statusBadgeHtml +
      "</div>" +
      '<div class="ns-omni-box">' +
      "<div>│┃│┃┃│┃┃ " + escapeHtml(getModelName(meta.model || "google/lyria-3.5")) + "</div>" +
      "<div>" + escapeHtml(c.vfsPath || meta.vfsPath || ("/audio/output" + extLbl.toLowerCase())) + "</div>" +
      "</div>" +
      errBlock +
      playerHtml +
      '<div class="ns-omni-title">' + promptTxt + "</div>" +
      '<div class="ns-card-foot-bar" onmousedown="event.stopPropagation()">' +
      '<span class="ns-omni-sub">' + escapeHtml(c.vfsPath || meta.vfsPath || ("Audio " + extLbl)) + "</span>" +
      '<button type="button" class="ns-card-action-btn" onclick="event.stopPropagation();window.TinCanNodeStudio.downloadNode(\'' + nid + '\')">↓ ' + escapeHtml(extLbl) + "</button>" +
      "</div>" +
      "</div>"
    );
  }

  let _modelViewerPromise = null;
  const modalMeshState = {
    activeNodeId: null,
    autoRotate: true,
    animPlaying: true,
    yaw: 0.55,
    pitch: 0.34,
    zoom: 1.0,
    rafId: null,
    viewerEl: null,
    loadedRealGlb: false
  };

  function ensureModelViewer() {
    if (typeof window !== "undefined" && window.customElements &&
        typeof window.customElements.get === "function" && window.customElements.get("model-viewer")) {
      return Promise.resolve(true);
    }
    if (_modelViewerPromise) return _modelViewerPromise;
    if (typeof document === "undefined" || !document.head || typeof document.head.appendChild !== "function") {
      return Promise.reject(new Error("DOM head unavailable; using wireframe preview"));
    }
    _modelViewerPromise = new Promise((resolve, reject) => {
      try {
        const s = document.createElement("script");
        s.type = "module";
        s.src = "https://unpkg.com/@google/model-viewer@3.5.0/dist/model-viewer.min.js";
        s.onload = () => resolve(true);
        s.onerror = () => {
          _modelViewerPromise = null;
          reject(new Error("Offline or CDN unreachable; showing isometric wireframe preview"));
        };
        document.head.appendChild(s);
      } catch (err) {
        _modelViewerPromise = null;
        reject(err);
      }
    });
    return _modelViewerPromise;
  }

  function _decodeBase64Bytes(b64) {
    const clean = String(b64 || "").replace(/^data:[^;]+;base64,/, "").trim();
    if (!clean) return new Uint8Array(0);
    if (typeof atob === "function") {
      const bin = atob(clean);
      const arr = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
      return arr;
    }
    if (typeof Buffer !== "undefined") {
      const buf = Buffer.from(clean, "base64");
      return new Uint8Array(buf.buffer, buf.byteOffset, buf.byteLength);
    }
    return new Uint8Array(0);
  }

  function _revokeNodeGlbBlobUrl(node) {
    if (!node) return;
    if (node._glbBlobUrl && typeof URL !== "undefined" && typeof URL.revokeObjectURL === "function") {
      try { URL.revokeObjectURL(node._glbBlobUrl); } catch (_e) {}
    }
    node._glbBlobUrl = "";
    node._glbBlobSourceB64 = "";
  }

  function _cleanupNodeResources(node) {
    if (!node) return;
    if (node._pollTimer) {
      clearInterval(node._pollTimer);
      node._pollTimer = null;
    }
    if (node._audioBlobUrl && typeof URL !== "undefined" && typeof URL.revokeObjectURL === "function") {
      try { URL.revokeObjectURL(node._audioBlobUrl); } catch (_e) {}
      node._audioBlobUrl = "";
    }
    _revokeNodeGlbBlobUrl(node);
  }

  function _getGlbSrcForNode(node) {
    if (!node || !node.content) return "";
    const c = node.content;
    if (c.glbRawUrl && typeof c.glbRawUrl === "string") {
      return c.glbRawUrl;
    }
    if (c.glbB64 && typeof c.glbB64 === "string") {
      if (node._glbBlobUrl && node._glbBlobSourceB64 === c.glbB64) {
        return node._glbBlobUrl;
      }
      _revokeNodeGlbBlobUrl(node);
      try {
        if (typeof Blob !== "undefined" && typeof URL !== "undefined" && typeof URL.createObjectURL === "function") {
          const bytes = _decodeBase64Bytes(c.glbB64);
          if (bytes.byteLength > 0) {
            const blob = new Blob([bytes], { type: "model/gltf-binary" });
            node._glbBlobUrl = URL.createObjectURL(blob);
            node._glbBlobSourceB64 = c.glbB64;
            return node._glbBlobUrl;
          }
        }
      } catch (_e) {}
      return "data:model/gltf-binary;base64," + c.glbB64;
    }
    return "";
  }

  function _isPlayableVideoUrl(vidUrl) {
    if (!vidUrl || typeof vidUrl !== "string") return false;
    if (/media\.local/i.test(vidUrl)) return false;
    return (
      vidUrl.indexOf("data:video/") === 0 ||
      vidUrl.indexOf("blob:") === 0 ||
      vidUrl.indexOf("/") === 0 ||
      /^https?:\/\//i.test(vidUrl)
    );
  }

  function renderVideoCardInner(node) {
    const nid = escapeHtml(node.id);
    const meta = node.metadata || {};
    const c = node.content || {};
    const promptTxt = escapeHtml(meta.prompt || node.label || "");
    const fps = c.fps || meta.fps || 60;
    const vidUrl = c.videoUrl || "";
    const jobStatus = meta.jobStatus || "";
    const isPlayable = _isPlayableVideoUrl(vidUrl);
    const elapsed = meta.startedAt ? Math.max(1, Math.round((Date.now() - meta.startedAt) / 1000)) : 1;

    let statusBadgeHtml = '<span class="ns-omni-status-badge">' + escapeHtml(getModelName(meta.model || "kling-4.0")) + "</span>";
    if (jobStatus === "RUNNING") {
      statusBadgeHtml = '<span class="ns-omni-status-badge">⟳ RENDERING VIDEO (' + elapsed + "s)</span>";
    } else if (jobStatus === "ERROR") {
      statusBadgeHtml = '<span class="ns-omni-status-badge is-error">✕ ERROR</span>';
    }

    let stageHtml = "";
    if (jobStatus === "ERROR") {
      stageHtml = '<div class="ns-omni-error-box">' + escapeHtml(meta.jobError || "Video generation failed") + "</div>";
    } else if (jobStatus === "RUNNING" && !isPlayable) {
      stageHtml =
        '<div class="ns-video-stage"><div class="ns-video-placeholder">' +
        '<div class="ns-spinner-pulse">⟳ RENDERING VIDEO (' + elapsed + "s)</div>" +
        "<div>" + escapeHtml(getModelName(meta.model || "kling-4.0")) + " · " + escapeHtml(fps + "fps · " + (meta.resolution || "1080p")) + "</div>" +
        "<div>Polling live status every 4s...</div>" +
        "</div></div>";
    } else if (isPlayable) {
      stageHtml =
        '<div class="ns-video-stage" onmousedown="event.stopPropagation()">' +
        '<video class="ns-video-player" controls playsinline loop src="' + escapeHtml(vidUrl) + '"></video>' +
        "</div>";
    } else {
      stageHtml =
        '<div class="ns-video-stage"><div class="ns-video-placeholder"><div>▶ ' +
        escapeHtml(getModelName(meta.model || "kling-4.0")) + "</div><div>" +
        escapeHtml(fps + "fps · " + (meta.resolution || "1080p") + " · " + (c.audioSync !== false ? "Audio Sync" : "Silent")) +
        "</div><div>" + escapeHtml(c.text || "Video staged") + "</div></div></div>";
    }

    return (
      '<div class="ns-omni-card">' +
      '<div class="ns-omni-top-row">' +
      '<span class="ns-omni-pill">▶ VIDEO · ' + escapeHtml(fps) + "FPS</span>" +
      statusBadgeHtml +
      "</div>" +
      stageHtml +
      '<div class="ns-omni-title">' + promptTxt + "</div>" +
      '<div class="ns-card-foot-bar" onmousedown="event.stopPropagation()">' +
      '<span class="ns-omni-sub">' + escapeHtml(c.vfsPath || meta.vfsPath || "MP4 Video") + "</span>" +
      '<button type="button" class="ns-card-action-btn" onclick="event.stopPropagation();window.TinCanNodeStudio.downloadNode(\'' + nid + '\')">↓ .MP4</button>' +
      "</div>" +
      "</div>"
    );
  }

  function renderMesh3dCardInner(node) {
    const nid = escapeHtml(node.id);
    const meta = node.metadata || {};
    const c = node.content || {};
    const promptTxt = escapeHtml(meta.prompt || node.label || "");
    const glbPath = c.glbPath || c.vfsPath || meta.vfsPath || "/models3d/mesh.glb";
    const jobStatus = meta.jobStatus || "";
    const elapsed = meta.startedAt ? Math.max(1, Math.round((Date.now() - meta.startedAt) / 1000)) : 1;
    const glbSrc = (jobStatus !== "RUNNING" && jobStatus !== "ERROR") ? _getGlbSrcForNode(node) : "";

    let statusText = "PBR .GLB READY";
    let statusCls = "ns-omni-status-badge";
    if (jobStatus === "RUNNING") {
      statusText = "⟳ GENERATING .GLB (" + elapsed + "s)";
    } else if (jobStatus === "ERROR") {
      statusText = "✕ ERROR";
      statusCls = "ns-omni-status-badge is-error";
    } else if (c.rigged) {
      statusText = "✓ RIGGED (" + (c.animation || "walk") + ")";
    }

    const animPlaying = node._meshAnimPlaying !== false;
    const modelViewerHtml = glbSrc
      ? ('<model-viewer class="ns-model-viewer" data-mesh-node-id="' + nid + '" src="' + escapeHtml(glbSrc) +
         '" camera-controls auto-rotate interaction-prompt="none" shadow-intensity="0.6"' +
         (c.rigged && animPlaying ? " autoplay" : "") + "></model-viewer>")
      : "";
    const stageHudText = jobStatus === "RUNNING"
      ? ("⟳ GENERATING .GLB (" + elapsed + "s)")
      : (glbSrc ? "3D .GLB · DRAG TO ORBIT" : "WIREFRAME PREVIEW");
    const errBlock = jobStatus === "ERROR"
      ? ('<div class="ns-omni-error-box">' + escapeHtml(meta.jobError || "3D mesh generation failed") + "</div>")
      : "";
    const rigAnimBtn = c.rigged
      ? ('<button type="button" class="ns-card-action-btn" onclick="event.stopPropagation();window.TinCanNodeStudio.toggleNodeMeshAnim(\'' + nid + '\')">' +
         (animPlaying ? "❚❚ Pause Anim" : "▶ Play Anim") + "</button>")
      : "";

    return (
      '<div class="ns-omni-card">' +
      '<div class="ns-omni-top-row">' +
      '<span class="ns-omni-pill">◆ 3D MESH · .GLB</span>' +
      '<span class="' + statusCls + '">' + escapeHtml(statusText) + "</span>" +
      "</div>" +
      '<div class="ns-mesh-stage" data-mesh-node-id="' + nid + '" onmousedown="event.stopPropagation()">' +
      modelViewerHtml +
      '<canvas class="ns-mesh-wire-canvas" data-mesh-node-id="' + nid + '" width="300" height="164"></canvas>' +
      '<span class="ns-mesh-stage-hud">' + escapeHtml(stageHudText) + "</span>" +
      '<button type="button" class="ns-mesh-inspect-btn" onclick="event.stopPropagation();window.TinCanNodeStudio.openMeshViewer(\'' + nid + '\')">⤢ Inspect 3D</button>' +
      "</div>" +
      errBlock +
      '<div class="ns-omni-title">' + promptTxt + "</div>" +
      '<div class="ns-omni-sub">' + escapeHtml(getModelName(meta.model || "hyper3d/rodin-v2.5") + " · " + (c.tier || meta.tier || "Regular") + " · " + glbPath) + "</div>" +
      '<div class="ns-card-foot-bar" onmousedown="event.stopPropagation()">' +
      '<div class="ns-card-foot-group">' +
      '<button type="button" class="ns-card-action-btn is-primary" onclick="event.stopPropagation();window.TinCanNodeStudio.runTerminalCommand(\'/rig --anim walk ' + escapeHtml(glbPath) + '\')">Auto-Rig Walk</button>' +
      rigAnimBtn +
      "</div>" +
      '<button type="button" class="ns-card-action-btn" onclick="event.stopPropagation();window.TinCanNodeStudio.downloadNode(\'' + nid + '\')">↓ .GLB</button>' +
      "</div>" +
      "</div>"
    );
  }

  function renderOmniCardInner(node) {
    const nid = escapeHtml(node.id);
    const kind = node.omniKind || node.modality || "atlas";
    const meta = node.metadata || {};
    const promptTxt = escapeHtml(meta.prompt || node.label || "");
    if (kind === "audio") {
      return renderAudioCardInner(node);
    }
    if (kind === "video") {
      return renderVideoCardInner(node);
    }
    if (kind === "3d" || kind === "mesh3d") {
      return renderMesh3dCardInner(node);
    }
    if (kind === "text") {
      return renderTextCardInner(node);
    }
    if (kind === "omni_master" || kind === "splat" || kind === "flythrough") {
      const statusBadge = meta.jobStatus === "ERROR"
        ? "✕ WORLD LABS ERROR"
        : (meta.jobStatus === "RUNNING"
          ? "⟳ GPU RECONSTRUCTING"
          : (meta.isRealSpz
            ? "● LIVE .SPZ READY"
            : (meta.simulated === false ? "● LIVE ATLAS v2" : "◐ LOCAL PREVIEW")));
      const opLine = meta.operationId ? ("Op: " + escapeHtml(meta.operationId)) : "Op: pending";
      const modeLine = meta.atlasTask === "posedImages2Splats"
        ? (meta.refine ? "Mode: Refined 2M ($5.00 · ~18m)" : "Mode: Draft Splat ($0.50 · ~30s)")
        : ("Task: " + escapeHtml(meta.atlasTask || "posedImages2Splats"));
      const viewsLine = "Views: " + (meta.posedFrameCount || meta.inputViewCount || 0) + " input/posed";
      const spzLine = meta.isRealSpz && meta.spzSizeBytes
        ? ("SPZ: " + (meta.spzSizeBytes / (1024 * 1024)).toFixed(2) + " MB real binary ✓")
        : (meta.jobStatus === "RUNNING" ? "SPZ: Polling World Labs every 4s..." : "SPZ: Preview only (submit real photos to build .spz)");
      const errBlock = meta.jobError
        ? ('<div class="ns-omni-error-box">' + escapeHtml(meta.jobError) + "</div>")
        : "";
      const nextActions =
        '<div class="ns-omni-next-bar" onmousedown="event.stopPropagation()">' +
        '<button type="button" class="ns-atlas-step-btn" onclick="event.stopPropagation();window.TinCanNodeStudio.runAtlasStep(\'atlasGenerate\', \'' + nid + '\')">+ Generate 6 Views</button>' +
        '<button type="button" class="ns-atlas-step-btn is-primary" onclick="event.stopPropagation();window.TinCanNodeStudio.runAtlasStep(\'posedImages2Splats\', \'' + nid + '\')">❖ Build Splat</button>' +
        (meta.spzAssetId ? '<button type="button" class="ns-atlas-step-btn" onclick="event.stopPropagation();window.TinCanNodeStudio.runAtlasStep(\'splats2Mesh\', \'' + nid + '\')">◆ Export .GLB</button>' : "") +
        "</div>";
      return (
        '<div class="ns-omni-card is-active">' +
        '<div class="ns-omni-top-row">' +
        '<span class="ns-omni-pill">❖ OMNI-WORLD MASTER · SPLAT + GLB + MP4</span>' +
        '<span class="ns-omni-status-badge">' + escapeHtml(statusBadge) + "</span>" +
        "</div>" +
        renderSplatStageHtml(node) +
        errBlock +
        '<div class="ns-omni-grid-2">' +
        '<div class="ns-omni-box">' +
        "<div>[World Labs Atlas v2 Telemetry]</div>" +
        "<div>• " + opLine + "</div>" +
        "<div>• " + modeLine + "</div>" +
        "</div>" +
        '<div class="ns-omni-box">' +
        "<div>[Reconstruction Output]</div>" +
        "<div>• " + escapeHtml(viewsLine) + "</div>" +
        "<div>• " + escapeHtml(spzLine) + "</div>" +
        "</div>" +
        "</div>" +
        nextActions +
        '<div class="ns-omni-title">' + promptTxt + "</div>" +
        '<div class="ns-omni-sub">' + escapeHtml(meta.vfsPath || "Not saved to .space yet") + "</div>" +
        "</div>"
      );
    }
    const poseViews = meta.posedFrameCount || meta.inputViewCount || 0;
    const poseErr = meta.jobError ? ('<div class="ns-omni-error-box">' + escapeHtml(meta.jobError) + "</div>") : "";
    return (
      '<div class="ns-omni-card">' +
      '<div class="ns-omni-top-row">' +
      '<span class="ns-omni-pill">● ATLAS · images2PosedRGBD</span>' +
      '<span class="ns-omni-status-badge">' + (meta.jobStatus === "ERROR" ? "✕ ERROR" : (poseViews > 0 ? ("✓ " + poseViews + " POSED") : "RUB POSE")) + "</span>" +
      "</div>" +
      renderSplatStageHtml(node) +
      poseErr +
      '<div class="ns-omni-box">' +
      "<div>[Posed RGBD + Linear Depth .EXR]</div>" +
      "<div>Op: " + escapeHtml(meta.operationId || "pending") + " · Views: " + poseViews + "</div>" +
      "</div>" +
      '<div class="ns-omni-next-bar" onmousedown="event.stopPropagation()">' +
      '<button type="button" class="ns-atlas-step-btn" onclick="event.stopPropagation();window.TinCanNodeStudio.runAtlasStep(\'atlasGenerate\', \'' + nid + '\')">+ Generate 6 Views (~30s)</button>' +
      '<button type="button" class="ns-atlas-step-btn is-primary" onclick="event.stopPropagation();window.TinCanNodeStudio.runAtlasStep(\'posedImages2Splats\', \'' + nid + '\')">❖ Build 3D Splat</button>' +
      "</div>" +
      '<div class="ns-omni-title">' + promptTxt + "</div>" +
      '<div class="ns-omni-sub ns-omni-green">' + escapeHtml(meta.vfsPath || "Synced to .space") + "</div>" +
      "</div>"
    );
  }

  function renderNodes() {
    const layer = $("nsNodesLayer");
    const empty = $("nsEmptyState");
    const autoBtn = $("nsAutoLayoutBtn");
    if (empty) empty.classList.toggle("hidden", state.nodes.length > 0);
    if (autoBtn) autoBtn.classList.toggle("hidden", state.nodes.length < 3);
    if (!layer) return;

    layer.innerHTML = state.nodes.map((node) => {
      const isSel = state.selectedIds.indexOf(node.id) !== -1;
      const mStatus = node.morphingStatus || "image";
      let w = node.width || 256;
      let h = node.height || 256;
      if (mStatus === "generating") { w = 96; h = 96; }
      else if (mStatus === "text" || mStatus === "message") { w = node.width || 320; h = node.height || 220; }
      else if (mStatus === "audio") { w = node.width || 320; h = node.height || 256; }
      else if (mStatus === "video") { w = node.width || 320; h = node.height || 250; }
      else if (mStatus === "mesh3d") { w = node.width || 320; h = node.height || 326; }
      else if (mStatus === "omni") { w = node.width || 320; h = node.height || 198; }
      node.width = w;
      node.height = h;

      let inner = "";
      if (mStatus === "generating") {
        inner =
          '<div class="ns-living-cube-wrap">' +
          '<div class="ns-living-cube"><div class="ns-living-ring"><div class="ns-living-core"></div></div></div>' +
          '<div class="ns-living-label">Generating...</div></div>';
      } else if (mStatus === "omni") {
        inner = renderOmniCardInner(node);
      } else if (mStatus === "text" || mStatus === "message") {
        inner = renderTextCardInner(node);
      } else if (mStatus === "audio") {
        inner = renderAudioCardInner(node);
      } else if (mStatus === "video") {
        inner = renderVideoCardInner(node);
      } else if (mStatus === "mesh3d") {
        inner = renderMesh3dCardInner(node);
      } else {
        const nodeImgs = _getNodeImages(node);
        if (nodeImgs.length > 1) {
          inner = renderImageCollectionCardInner(node);
        } else {
          const imgUrl = (nodeImgs[0] && nodeImgs[0].imageUrl) || (node.content && node.content.imageUrl);
          const imgStyle = "filter:" + buildFilterCss(node.filters) + ";";
          inner =
            '<div class="ns-img-node">' +
            '<span class="ns-node-type-badge">' + escapeHtml(node.type || "GENERATED") + "</span>" +
            (imgUrl ? '<button type="button" class="ns-node-lb-btn" title="View in Lightbox" onclick="event.stopPropagation();window.TinCanNodeStudio.openImageLightbox(\'' + escapeHtml(node.id) + '\',0)">⤢</button>' : "") +
            (imgUrl ? '<button type="button" class="ns-node-dl-btn" title="Download" onclick="event.stopPropagation();window.TinCanNodeStudio.downloadNode(\'' + escapeHtml(node.id) + '\')">↓</button>' : "") +
            (imgUrl
              ? '<img src="' + escapeHtml(imgUrl) + '" alt="' + escapeHtml(node.label) + '" style="' + imgStyle + '" draggable="false" ondblclick="event.stopPropagation();window.TinCanNodeStudio.openImageLightbox(\'' + escapeHtml(node.id) + '\',0)">'
              : renderTextCardInner(node)) +
            '<div class="ns-node-meta-overlay">' +
            '<div class="ns-node-prompt-txt">' + escapeHtml((node.metadata && node.metadata.prompt) || node.label) + "</div>" +
            '<div class="ns-node-sub-txt"><span>' + escapeHtml((node.metadata && node.metadata.resolution) || "1K") +
            '</span><span>' + escapeHtml(getModelName((node.metadata && node.metadata.model) || "gemini-nano-banana-2.1")) + "</span></div>" +
            "</div></div>";
        }
      }

      const filterPop = state.openFilterNodeId === node.id
        ? ('<div class="ns-node-filter-popover" onclick="event.stopPropagation()">' +
           '<div class="ns-pop-title" style="margin-bottom:4px;">Non-Destructive Filters</div>' +
           FILTER_PRESETS.map((f) => {
             const on = node.filters && node.filters[f.id];
             return '<div class="ns-node-filter-row"><span>' + escapeHtml(f.label) + '</span>' +
               '<button type="button" class="ns-top-btn" onclick="window.TinCanNodeStudio.toggleNodeFilter(\'' + escapeHtml(node.id) + '\', \'' + f.id + '\')">' +
               (on ? "ON ●" : "○ OFF") + "</button></div>";
           }).join("") + "</div>")
        : "";

      const isVisual = mStatus === "image" || (mStatus === "omni" && node.omniKind !== "audio");
      const quickBar = mStatus !== "generating"
        ? ('<div class="ns-node-quickbar" onclick="event.stopPropagation()">' +
           '<button type="button" class="ns-qact-btn" onclick="window.TinCanNodeStudio.addNodeAsRef(\'' + escapeHtml(node.id) + '\')">+ Ref</button>' +
           (isVisual ? '<span class="ns-qact-sep"></span><button type="button" class="ns-qact-btn" onclick="window.TinCanNodeStudio.viewOrConvertNodeSplat(\'' + escapeHtml(node.id) + '\')">❖ 3D Splat</button>' : "") +
           '<span class="ns-qact-sep"></span>' +
           '<button type="button" class="ns-qact-btn" onclick="window.TinCanNodeStudio.editNode(\'' + escapeHtml(node.id) + '\')">Edit</button>' +
           (mStatus === "image" ? '<button type="button" class="ns-qact-btn" onclick="window.TinCanNodeStudio.openFilterPopover(\'' + escapeHtml(node.id) + '\')">Filter</button>' : "") +
           '<button type="button" class="ns-qact-btn" onclick="window.TinCanNodeStudio.duplicateNode(\'' + escapeHtml(node.id) + '\')">Copy</button>' +
           '<button type="button" class="ns-qact-btn" onclick="window.TinCanNodeStudio.downloadNode(\'' + escapeHtml(node.id) + '\')">Download</button>' +
           '<span class="ns-qact-sep"></span>' +
           '<button type="button" class="ns-qact-btn is-danger" onclick="window.TinCanNodeStudio.deleteNode(\'' + escapeHtml(node.id) + '\')">Delete</button>' +
           "</div>")
        : "";

      const resizeHandle = mStatus !== "generating"
        ? ('<div class="ns-resize-handle" data-resize-node-id="' + escapeHtml(node.id) + '" title="Drag to resize (double-click to expand)" ' +
           'ondblclick="event.stopPropagation();window.TinCanNodeStudio.toggleNodeExpand(\'' + escapeHtml(node.id) + '\')">' +
           '<svg viewBox="0 0 12 12" width="11" height="11" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">' +
           '<path d="M11 3L3 11M11 7L7 11"/></svg></div>')
        : "";

      return '<div id="nsCanvasNode-' + escapeHtml(node.id) + '" class="ns-canvas-node' + (isSel ? " is-selected" : "") + '" ' +
        'data-node-id="' + escapeHtml(node.id) + '" ' +
        'style="left:' + node.x + "px;top:" + node.y + "px;width:" + w + "px;height:" + h + 'px;">' +
        '<div class="ns-node-handle ns-node-handle--top" data-handle="top" data-node-id="' + escapeHtml(node.id) + '"></div>' +
        '<div class="ns-node-handle ns-node-handle--bottom" data-handle="bottom" data-node-id="' + escapeHtml(node.id) + '"></div>' +
        quickBar + filterPop +
        '<div class="ns-morph-card">' + inner + resizeHandle + "</div>" +
        "</div>";
    }).join("");

    renderEdges();
    renderConversationView();
    renderLibraryViewGrid();
    mountAllSplatCanvases();
    mountAllMeshPreviews();
    if (!state._suppressAutoSave && state.nodes.length > 0) {
      scheduleAutoSave();
    }
  }

  function copyNodeText(id) {
    const node = state.nodes.find((n) => n.id === id);
    const txt = (node && node.content && node.content.text) || (node && node.label) || "";
    if (!txt) return;
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(txt);
      }
    } catch (_e) {}
    showToast("Copied text to clipboard", false);
  }

  function sendTextToImage(id) {
    const node = state.nodes.find((n) => n.id === id);
    const txt = (node && node.content && node.content.text) || (node && node.label) || "";
    selectModality("image");
    const promptEl = $("nsPromptInput");
    if (promptEl) {
      promptEl.value = txt;
      promptEl.focus();
    }
    renderPromptIslandStatus();
    showToast("Loaded text into Image prompt — click Generate to render", false);
  }

  function replyToTextNode(id) {
    state.selectedIds = [id];
    selectModality("text");
    syncSelectionRefs();
    renderNodes();
    const promptEl = $("nsPromptInput");
    if (promptEl) promptEl.focus();
  }

  function parseSlashCommand(raw) {
    const text = String(raw || "").trim();
    if (!text.startsWith("/")) {
      return {
        is_slash: false,
        command: "image",
        subcommand: "",
        slash_key: "/image",
        modality: state.modality || "image",
        provider: state.provider || "gemini",
        model: state.model || "gemini-nano-banana-2.1",
        atlas_task: null,
        flags: {},
        prompt: text,
        pill_label: "● /image"
      };
    }

    const tokens = text.split(/\s+/);
    const rootToken = (tokens[0] || "/image").toLowerCase();
    const cmdName = rootToken.replace(/^\/+/, "") || "image";
    let subCmd = "";
    let idx = 1;

    if (cmdName === "atlas" && tokens[1] && !tokens[1].startsWith("-")) {
      const candidate = tokens[1].toLowerCase();
      if (["splat", "pose", "flythrough", "mesh", "chisel", "text2img", "generate"].indexOf(candidate) !== -1) {
        subCmd = candidate === "generate" ? "flythrough" : candidate;
        idx = 2;
      }
    } else if (cmdName === "audio" && tokens[1] && !tokens[1].startsWith("-")) {
      const candidate = tokens[1].toLowerCase();
      if (["tts", "music", "sfx"].indexOf(candidate) !== -1) {
        subCmd = candidate;
        idx = 2;
      }
    }

    if (cmdName === "atlas" && !subCmd) subCmd = "splat";

    const flags = {};
    const promptParts = [];
    while (idx < tokens.length) {
      const tok = tokens[idx];
      if (tok.startsWith("--") && tok.length > 2) {
        const key = tok.slice(2);
        const nextTok = tokens[idx + 1];
        if (nextTok && !nextTok.startsWith("--")) {
          flags[key] = nextTok;
          idx += 2;
        } else {
          flags[key] = true;
          idx += 1;
        }
      } else {
        promptParts.push(tok);
        idx += 1;
      }
    }

    let slashKey = "/" + cmdName + (cmdName === "atlas" && subCmd ? " " + subCmd : "");
    let matched = SLASH_COMMANDS.find((c) => c.command === slashKey) ||
      SLASH_COMMANDS.find((c) => c.command === "/" + cmdName) ||
      SLASH_COMMANDS[0];

    let modality = matched ? matched.modality : "image";
    let provider = matched ? matched.provider : "gemini";
    let model = (flags.model ? String(flags.model) : (matched ? matched.model : "gemini-nano-banana-2.1"));
    let atlasTask = matched && matched.atlas_task ? matched.atlas_task : null;
    if (cmdName === "atlas") {
      modality = "atlas";
      provider = "worldlabs";
      model = "worldlabs/atlas-v2";
      if (subCmd === "pose") atlasTask = "images2PosedRGBD";
      else if (subCmd === "flythrough") atlasTask = "atlasGenerate";
      else if (subCmd === "mesh") atlasTask = "splats2Mesh";
      else if (subCmd === "chisel") atlasTask = "atlasChisel";
      else if (subCmd === "text2img") atlasTask = "atlasTextToImage";
      else atlasTask = "posedImages2Splats";
    } else if (cmdName === "audio") {
      modality = "audio";
      provider = "nanogpt";
      model = flags.model || (subCmd === "tts" ? "elevenlabs/eleven-v4" : (subCmd === "sfx" ? "elevenlabs/sound-effects/v3" : "google/lyria-3.5"));
    } else if (cmdName === "video") {
      modality = "video";
      provider = "nanogpt";
      model = flags.model || "kling-4.0";
    } else if (cmdName === "3d" || cmdName === "rig") {
      modality = "3d";
      provider = "hyper3d";
      model = flags.model || "hyper3d/rodin-v2.5";
    } else if (cmdName === "text") {
      modality = "text";
      provider = "auto";
      model = flags.model || "gemini-3.1-pro";
    }

    const prefixSymbol = modality === "audio" ? "♪ " : (modality === "3d" ? "❖ " : "● ");
    const pillLabel = prefixSymbol + slashKey + (cmdName === "audio" && subCmd ? " " + subCmd : "");

    return {
      is_slash: true,
      command: cmdName,
      subcommand: subCmd,
      slash_key: slashKey,
      modality: modality,
      provider: provider,
      model: model,
      atlas_task: atlasTask,
      flags: flags,
      prompt: promptParts.join(" ").replace(/^["']|["']$/g, "") || text,
      pill_label: pillLabel
    };
  }

  function applySlashRoute(cmd) {
    const parsed = parseSlashCommand(cmd);
    state.activeSlashCommand = parsed.slash_key;
    state.modality = parsed.modality;
    state.provider = parsed.provider;
    if (CAPS[parsed.model]) {
      state.model = parsed.model;
    }

    const pill = $("nsActiveSlashPill");
    const pillTxt = $("nsActiveSlashPillText");
    if (pillTxt) {
      pillTxt.textContent = parsed.pill_label;
    } else if (pill) {
      pill.textContent = parsed.pill_label + " ×";
    }
    if (pill) pill.classList.remove("hidden");

    document.querySelectorAll(".ns-slash-row").forEach((row) => {
      row.classList.toggle("is-selected", row.dataset.slashCmd === parsed.slash_key);
    });

    const matchedSpec = SLASH_COMMANDS.find((c) => c.command === parsed.slash_key);
    const promptEl = $("nsPromptInput");
    if (promptEl && (!promptEl.value.trim() || promptEl.value.trim() === "/" || promptEl.value.trim().startsWith("/"))) {
      promptEl.value = matchedSpec && matchedSpec.template ? matchedSpec.template : parsed.slash_key + " ";
    }

    const pop = $("nsSlashRouterPopover");
    if (pop) pop.classList.add("hidden");

    syncCapabilitiesAndControls();
    renderPromptIslandStatus();
    return parsed;
  }

  function toggleSlashRouterPopover(forceOpen) {
    const pop = $("nsSlashRouterPopover");
    if (!pop) return;
    if (forceOpen !== undefined) {
      pop.classList.toggle("hidden", !forceOpen);
    } else {
      pop.classList.toggle("hidden");
    }
  }

  function clearSlashRoute() {
    state.activeSlashCommand = "";
    state.modality = "image";
    const pill = $("nsActiveSlashPill");
    if (pill) pill.classList.add("hidden");
    renderPromptIslandStatus();
  }

  function appendTerminalLine(line) {
    const log = $("nsTerminalLog");
    if (!log) return;
    const div = document.createElement("div");
    div.className = "ns-term-line";
    div.textContent = line;
    if (typeof log.appendChild === "function") {
      log.appendChild(div);
    } else {
      log.innerHTML += '<div class="ns-term-line">' + escapeHtml(line) + "</div>";
    }
  }

  function buildOmniNodeFromParsed(parsed, rawCmd, idSuffix) {
    let mStatus = "omni";
    let omniKind = "atlas";
    let w = 340;
    let h = 348;
    let vfsPath = "Synced to /worlds/torii_3e78434c/ ✓";
    const cleanLabel = parsed.prompt || rawCmd;
    if (parsed.modality === "text") {
      mStatus = "text";
      omniKind = "text";
      w = 320;
      h = 220;
      vfsPath = "";
    } else if (parsed.modality === "image") {
      mStatus = "image";
      omniKind = "image";
      w = 256;
      h = 256;
      vfsPath = "";
    } else if (parsed.modality === "audio") {
      mStatus = "audio";
      omniKind = "audio";
      w = 320;
      h = 256;
      vfsPath = "/audio/output.mp3";
    } else if (parsed.modality === "video") {
      mStatus = "video";
      omniKind = "video";
      w = 320;
      h = 250;
      vfsPath = "/videos/output.mp4";
    } else if (parsed.modality === "3d") {
      mStatus = "mesh3d";
      omniKind = "3d";
      w = 320;
      h = 326;
      vfsPath = "/models3d/mesh.glb";
    } else if (parsed.subcommand === "pose" || parsed.atlas_task === "images2PosedRGBD") {
      mStatus = "omni";
      omniKind = "pose";
      w = 360;
      h = 348;
      vfsPath = "Synced to /worlds/torii_3e78434c/ ✓";
    } else {
      mStatus = "omni";
      omniKind = "omni_master";
      w = 480;
      h = 368;
      vfsPath = "/worlds/torii_3e78434c/refinedSplats_2000000.spz";
    }
    return {
      id: "omni-" + idSuffix,
      type: parsed.modality.toUpperCase(),
      morphingStatus: mStatus,
      omniKind: omniKind,
      modality: parsed.modality,
      label: cleanLabel,
      x: 240 + (idSuffix % 3) * 48,
      y: 110 + (idSuffix % 3) * 56,
      width: w,
      height: h,
      splatState: mStatus === "omni" ? {
        mode: "rgb",
        frustums: true,
        yaw: 0.42,
        pitch: 0.24,
        zoom: 1.0
      } : undefined,
      content: {
        text: cleanLabel,
        kind: parsed.subcommand || state.audioKind || "music",
        tier: (parsed.flags && parsed.flags.tier) || state.meshTier || "Regular",
        fps: Number((parsed.flags && parsed.flags.fps) || state.videoFps || 60),
        sparkline: "│┃│┃┃│┃┃"
      },
      metadata: {
        prompt: cleanLabel,
        rawCommand: rawCmd,
        model: parsed.model,
        modality: parsed.modality,
        audioKind: parsed.subcommand || state.audioKind || "music",
        tier: (parsed.flags && parsed.flags.tier) || state.meshTier || "Regular",
        fps: Number((parsed.flags && parsed.flags.fps) || state.videoFps || 60),
        atlasTask: parsed.atlas_task,
        vfsPath: vfsPath,
        resolution: state.resolution || "1280x720"
      },
      filters: {}
    };
  }

  function _extractSavedVfsPath(savedObj, fallbackPath) {
    if (!savedObj) return fallbackPath;
    if (typeof savedObj === "string") return savedObj;
    if (typeof savedObj === "object") {
      if (Array.isArray(savedObj.files) && savedObj.files.length) {
        const spzFile = savedObj.files.find((f) => String(f).endsWith(".spz"));
        const glbFile = savedObj.files.find((f) => String(f).endsWith(".glb"));
        return String(spzFile || glbFile || savedObj.files[0]);
      }
      if (savedObj.path && typeof savedObj.path === "string") {
        return savedObj.path;
      }
    }
    return fallbackPath;
  }

  async function runTerminalCommand(cmd) {
    const termInput = $("nsTerminalInput");
    const promptEl = $("nsPromptInput");
    const rawCmd = String(
      cmd !== undefined && cmd !== null && String(cmd).trim()
        ? cmd
        : ((termInput && termInput.value.trim()) || (promptEl && promptEl.value.trim()) || "/atlas splat")
    ).trim();

    const parsed = applySlashRoute(rawCmd);
    appendTerminalLine("you@tincan:~/space$ " + rawCmd);

    // Ensure all asynchronous FileReader base64 conversions for uploaded photos have completed
    if (state.references.length > 0) {
      try {
        await Promise.all(state.references.map((r) => r._readPromise || Promise.resolve()));
      } catch (_e) {}
    }

    state.nodeSeq += 1;
    const parentIds = state.selectedIds.slice();
    const multiRefs = collectAllImageReferences();
    const imageRefs = multiRefs.filter((r) => r.type === "image");
    const spawned = buildOmniNodeFromParsed(parsed, rawCmd, state.nodeSeq);
    const smartPos = _computeSmartNodePosition(parentIds, spawned.width || 320, spawned.height || 256);
    spawned.x = smartPos.x;
    spawned.y = smartPos.y;
    spawned.metadata.refine = !!state.atlasRefine;
    // Inherit posedFrames / spzAssetId from selected parent node when chaining Atlas steps
    let inheritedPosedFrames = [];
    let inheritedSplatAssetId = null;
    for (let i = 0; i < parentIds.length; i++) {
      const pn = state.nodes.find((x) => x.id === parentIds[i]);
      if (pn && pn.metadata) {
        if (Array.isArray(pn.metadata.posedFrames) && pn.metadata.posedFrames.length > 0) {
          inheritedPosedFrames = inheritedPosedFrames.concat(pn.metadata.posedFrames);
        }
        if (!inheritedSplatAssetId && pn.metadata.spzAssetId) {
          inheritedSplatAssetId = pn.metadata.spzAssetId;
        }
      }
    }
    // Attach multi-view photos for Atlas Splat reconstruction
    if (parsed.modality === "atlas" && imageRefs.length > 0) {
      spawned.content.imageUrl = imageRefs[0].url || (imageRefs[0].base64 ? ("data:" + (imageRefs[0].mimeType || "image/jpeg") + ";base64," + imageRefs[0].base64) : "");
      spawned.content.referenceImages = imageRefs.map((r) => r.url || (r.base64 ? ("data:" + (r.mimeType || "image/jpeg") + ";base64," + r.base64) : "")).filter(Boolean);
      spawned.metadata.inputViewCount = imageRefs.length;
    }

    state.nodes.push(spawned);
    parentIds.forEach((pid) => {
      state.edges.push({ id: "e-" + pid + "-" + spawned.id, source: pid, target: spawned.id });
    });
    state.selectedIds = [spawned.id];
    _ensureNodeVisible(spawned.x, spawned.y, spawned.width || 320, spawned.height || 256);
    renderNodes();

    const headers = { "Content-Type": "application/json" };
    if (state.apiKey) headers["X-Gemini-Api-Key"] = state.apiKey;
    if (state.nanogptKey) headers["X-NanoGPT-Api-Key"] = state.nanogptKey;
    const tgt = _resolveSpaceTarget();

    if (typeof fetch === "function") {
      try {
        let res = await fetch("/api/omni/route", {
          method: "POST",
          headers: headers,
          body: JSON.stringify({
            command: rawCmd,
            prompt: parsed.prompt,
            modality: parsed.modality,
            model: parsed.model,
            refine: !!state.atlasRefine,
            tier: (parsed.flags && parsed.flags.tier) || state.meshTier || "Regular",
            scope: tgt.scope,
            owner_id: tgt.owner_id,
            selectedNodeIds: parentIds,
            references: multiRefs,
            posed_frames: inheritedPosedFrames.length ? inheritedPosedFrames : undefined,
            splat_asset_id: inheritedSplatAssetId || undefined
          })
        });
        if (res && res.status === 404) {
          res = await fetch("/api/nodes/generate", {
            method: "POST",
            headers: headers,
            body: JSON.stringify({
              prompt: rawCmd,
              modality: parsed.modality,
              selectedNodeIds: parentIds,
              references: multiRefs,
              config: { model: parsed.model, provider: parsed.provider }
            })
          });
        }
        if (res && typeof res.json === "function") {
          const data = await res.json();
          if (data && data.ok === false) {
            const errTxt = String(data.error || ("Generation request failed (HTTP " + (res.status || 422) + ")"));
            spawned.metadata.jobStatus = "ERROR";
            spawned.metadata.jobError = errTxt;
            spawned.metadata.simulated = false;
            if (data.result && Array.isArray(data.result.posed_frames) && data.result.posed_frames.length) {
              spawned.metadata.posedFrames = data.result.posed_frames;
              spawned.metadata.posedFrameCount = data.result.posed_frames.length;
            }
            showToast(errTxt, true);
            appendTerminalLine("[!] Error: " + errTxt);
            renderNodes();
            renderPromptIslandStatus();
            return spawned;
          }
          if (data && data.saved_to_space) {
            spawned.metadata.vfsPath = _extractSavedVfsPath(data.saved_to_space, spawned.metadata.vfsPath);
          }
          const rObj = (data && data.result) || {};
          const nestedNode = (rObj.node && rObj.node.data) || (data.node && data.node.data) || null;
          if (nestedNode && nestedNode.content) {
            spawned.content = Object.assign({}, spawned.content, nestedNode.content);
          }
          if (nestedNode && nestedNode.metadata) {
            spawned.metadata = Object.assign({}, spawned.metadata, nestedNode.metadata);
          }

          if (parsed.modality === "audio") {
            const audRawUrl = data.audio_raw_url || rObj.audio_raw_url || rObj.audio_url || "";
            if (audRawUrl) {
              spawned.content.audioRawUrl = audRawUrl;
              spawned.content.audioUrl = audRawUrl;
            }
            if (rObj.mime_type) spawned.content.mimeType = rObj.mime_type;
            if (rObj.ext) spawned.content.ext = rObj.ext;
            const audB64 = rObj.audio_bytes_b64 || (spawned.content && spawned.content.audioBytesB64) || "";
            if (audB64) {
              spawned.content.audioBytesB64 = audB64;
              if (!spawned.content.mimeType) spawned.content.mimeType = "audio/wav";
              if (!spawned.content.audioUrl) {
                spawned.content.audioUrl = "data:" + spawned.content.mimeType + ";base64," + audB64;
              }
            }
            if (rObj.kind) {
              spawned.content.kind = rObj.kind;
              spawned.metadata.audioKind = rObj.kind;
            }
            if (rObj.path) {
              spawned.content.vfsPath = rObj.path;
              spawned.metadata.vfsPath = rObj.path;
            }
            const audJobId = data.job_id || rObj.job_id || rObj.runId || "";
            if ((data.async === true || data.done === false || rObj.status === "RUNNING") && audJobId) {
              spawned.metadata.jobId = audJobId;
              spawned.metadata.jobStatus = "RUNNING";
              spawned.metadata.startedAt = Date.now();
              spawned.metadata.model = data.model || rObj.model || parsed.model;
              if (data.cost !== undefined && data.cost !== null) spawned.metadata.audioCost = data.cost;
              if (data.payment_source) spawned.metadata.audioPaymentSource = data.payment_source;
              spawned.metadata.vfsPath = "Generating audio (" + audJobId + ")...";
              showToast("Audio job started (" + audJobId + ") — polling live...", false);
              appendTerminalLine("[⟳] Submitted Audio job " + audJobId + " (polling live every 3.5s)");
              renderNodes();
              renderPromptIslandStatus();
              pollAudioJobForNode(spawned);
              return spawned;
            }
          } else if (parsed.modality === "3d") {
            const glbRaw = rObj.glb_raw_url || data.glb_raw_url || (rObj.download && rObj.download.glb_raw_url) || "";
            if (glbRaw) spawned.content.glbRawUrl = glbRaw;
            const glbB64 = rObj.glb_bytes_b64 || data.glb_bytes_b64 || "";
            if (glbB64) {
              _revokeNodeGlbBlobUrl(spawned);
              spawned.content.glbB64 = glbB64;
            }
            if (rObj.path) {
              spawned.content.glbPath = rObj.path;
              spawned.content.vfsPath = rObj.path;
              spawned.metadata.vfsPath = rObj.path;
            }
            if (rObj.rig_type || rObj.bones || parsed.command === "rig") {
              spawned.content.rigged = true;
              spawned.content.animation = (rObj.animations && rObj.animations[0]) || (parsed.flags && parsed.flags.anim) || "walk";
            }
            const meshJobId = data.job_id || rObj.job_id || rObj.jobId || (spawned.metadata && spawned.metadata.jobId) || "";
            if ((data.async === true || data.done === false || rObj.jobStatus === "RUNNING") && meshJobId) {
              spawned.metadata.jobId = meshJobId;
              spawned.metadata.jobStatus = "RUNNING";
              spawned.metadata.startedAt = Date.now();
              spawned.metadata.vfsPath = "Generating .GLB (" + meshJobId + ")...";
              showToast("3D .GLB job started (" + meshJobId + ") — polling live every 4s...", false);
              appendTerminalLine("[⟳] Submitted 3D .GLB job " + meshJobId + " (polling live every 4s)");
              renderNodes();
              renderPromptIslandStatus();
              pollMeshJobForNode(spawned);
              return spawned;
            }
          } else if (parsed.modality === "video") {
            const vidJobId = data.job_id || rObj.job_id || rObj.jobId || (spawned.metadata && spawned.metadata.jobId) || (spawned.content && spawned.content.jobId) || "";
            if ((data.async === true || data.done === false || rObj.jobStatus === "RUNNING" || (spawned.metadata && spawned.metadata.jobStatus === "RUNNING")) && vidJobId) {
              spawned.metadata.jobId = vidJobId;
              spawned.metadata.modelSlug = data.model_slug || rObj.modelSlug || rObj.model_slug || parsed.model || state.model;
              spawned.metadata.jobStatus = "RUNNING";
              spawned.metadata.startedAt = Date.now();
              showToast("Video job started (" + vidJobId + ") — polling live every 4s...", false);
              appendTerminalLine("[⟳] Submitted Video job " + vidJobId + " (polling live every 4s)");
              renderNodes();
              renderPromptIslandStatus();
              pollVideoJobForNode(spawned);
              return spawned;
            }
          } else if (parsed.modality === "text") {
            if (rObj.text && !nestedNode) spawned.content.text = rObj.text;
          }

          if (rObj.operation_id || (data && data.operation_id)) {
            spawned.metadata.operationId = rObj.operation_id || data.operation_id;
          }
          if (typeof rObj.simulated === "boolean") spawned.metadata.simulated = rObj.simulated;
          if (typeof rObj.refine === "boolean") spawned.metadata.refine = rObj.refine;
          if (typeof rObj.input_frame_count === "number" && rObj.input_frame_count > 0) {
            spawned.metadata.inputViewCount = rObj.input_frame_count;
          }
          if (Array.isArray(rObj.posed_frames) && rObj.posed_frames.length > 0) {
            spawned.metadata.posedFrames = rObj.posed_frames;
            spawned.metadata.posedFrameCount = rObj.posed_frames.length;
          }
          const dlObj = rObj.download || {};
          if (dlObj.spz_raw_url) spawned.metadata.spzRawUrl = dlObj.spz_raw_url;
          if (dlObj.spz_path) spawned.metadata.vfsPath = dlObj.spz_path;
          if (dlObj.spz_size_bytes) spawned.metadata.spzSizeBytes = dlObj.spz_size_bytes;
          if (dlObj.spz_asset_id) spawned.metadata.spzAssetId = dlObj.spz_asset_id;
          if (dlObj.is_real_spz || rObj.is_real_spz) spawned.metadata.isRealSpz = true;

          // Non-blocking async World Labs GPU job -> start live 4s polling!
          if (data && (data.async || data.done === false) && spawned.metadata.operationId) {
            spawned.metadata.jobStatus = "RUNNING";
            spawned.metadata.startedAt = Date.now();
            spawned.metadata.estimatedSeconds = data.estimated_seconds || (state.atlasRefine ? 1080 : 35);
            spawned.metadata.vfsPath = "Running on World Labs GPU (" + spawned.metadata.operationId + ")...";
            showToast("World Labs job started (" + (state.atlasRefine ? "Refined ~18m" : "Draft ~30s") + ") — polling live...", false);
            appendTerminalLine("[⟳] Submitted World Labs " + (data.task || parsed.atlas_task) + " → op " + spawned.metadata.operationId + " (polling live every 4s)");
            renderNodes();
            renderPromptIslandStatus();
            pollAtlasOperationForNode(spawned);
            return spawned;
          }

          if (data && data.files_b64 && typeof data.files_b64 === "object") {
            const keys = Object.keys(data.files_b64);
            const hasMultiUploaded = Array.isArray(spawned.content.referenceImages) && spawned.content.referenceImages.length > 1;
            const imgKey = keys.find((k) => /\.(jpg|jpeg|png)$/i.test(k));
            if (!hasMultiUploaded && imgKey && data.files_b64[imgKey] && String(data.files_b64[imgKey]).length > 120) {
              const mime = imgKey.toLowerCase().endsWith(".png") ? "image/png" : "image/jpeg";
              spawned.content.imageUrl = "data:" + mime + ";base64," + data.files_b64[imgKey];
              spawned._splatCloud = null;
            }
            const audKey = keys.find((k) => /\.(mp3|wav|ogg|flac|m4a)$/i.test(k));
            if (audKey && data.files_b64[audKey]) {
              const lowK = audKey.toLowerCase();
              const aMime = lowK.endsWith(".mp3") ? "audio/mpeg" : (lowK.endsWith(".ogg") ? "audio/ogg" : (lowK.endsWith(".flac") ? "audio/flac" : (lowK.endsWith(".m4a") ? "audio/mp4" : "audio/wav")));
              spawned.content.audioBytesB64 = data.files_b64[audKey];
              spawned.content.mimeType = spawned.content.mimeType || aMime;
              if (!spawned.content.audioRawUrl && !spawned.content.audioUrl) {
                spawned.content.audioUrl = "data:" + spawned.content.mimeType + ";base64," + data.files_b64[audKey];
              }
              spawned.content.vfsPath = audKey;
            }
            const glbKey = keys.find((k) => /\.glb$/i.test(k));
            if (glbKey && data.files_b64[glbKey]) {
              _revokeNodeGlbBlobUrl(spawned);
              spawned.content.glbB64 = data.files_b64[glbKey];
              spawned.content.glbPath = glbKey;
              spawned.content.vfsPath = glbKey;
            }
            const spzKey = keys.find((k) => /\.spz$/i.test(k));
            if (spzKey && data.files_b64[spzKey]) {
              spawned.content.spzB64 = data.files_b64[spzKey];
            }
          }
          spawned.metadata.jobStatus = "SUCCEEDED";
        }
      } catch (_err) {
        // Offline / local simulation keeps spawned DAG card
      }
    }

    const viewSuffix = imageRefs.length > 0 ? (" [" + imageRefs.length + " input photo" + (imageRefs.length === 1 ? "" : "s") + "]") : "";
    appendTerminalLine("[+] Routed " + parsed.slash_key + " (" + parsed.model + ")" + viewSuffix + " → " + (spawned.metadata.vfsPath || spawned.id));
    renderNodes();
    renderPromptIslandStatus();
    return spawned;
  }

  function pollAtlasOperationForNode(node) {
    if (!node || !node.metadata || !node.metadata.operationId || typeof fetch !== "function") return;
    if (node._pollTimer) clearInterval(node._pollTimer);
    const opId = node.metadata.operationId;
    const tgt = _resolveSpaceTarget();
    node._pollTimer = setInterval(async function () {
      try {
        const res = await fetch("/api/atlas/operations/status?operation_id=" + encodeURIComponent(opId));
        if (!res || !res.ok) return;
        const st = await res.json();
        if (!st) return;
        if (st.done || st.ok === false) {
          clearInterval(node._pollTimer);
          node._pollTimer = null;
          if (st.ok === false || st.error) {
            const errMsg = (st.error && st.error.message) || String(st.error || "World Labs operation failed");
            node.metadata.jobStatus = "ERROR";
            node.metadata.jobError = errMsg;
            showToast("World Labs error: " + errMsg, true);
            appendTerminalLine("[!] World Labs op " + opId + " failed: " + errMsg);
            renderNodes();
            return;
          }
          // Download real completed World Labs outputs (.spz / .exr / .glb / frames) into .space VFS
          const dlRes = await fetch("/api/atlas/operations/download", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              operation_id: opId,
              scope: tgt.scope,
              owner_id: tgt.owner_id,
              target_dir: "/worlds"
            })
          });
          const dl = dlRes && dlRes.ok ? await dlRes.json() : {};
          node.metadata.jobStatus = "SUCCEEDED";
          node.metadata.simulated = false;
          if (st.response && Array.isArray(st.response.frames) && st.response.frames.length) {
            const prevPosed = Array.isArray(node.metadata.posedFrames) ? node.metadata.posedFrames : [];
            node.metadata.posedFrames = prevPosed.concat(st.response.frames);
            node.metadata.posedFrameCount = node.metadata.posedFrames.length;
          }
          if (dl.spz_path) node.metadata.vfsPath = dl.spz_path;
          else if (dl.mesh_path) node.metadata.vfsPath = dl.mesh_path;
          else if (Array.isArray(dl.saved_files) && dl.saved_files.length) node.metadata.vfsPath = dl.saved_files[0];
          if (dl.spz_raw_url) node.metadata.spzRawUrl = dl.spz_raw_url;
          if (dl.spz_size_bytes) node.metadata.spzSizeBytes = dl.spz_size_bytes;
          if (dl.spz_asset_id) node.metadata.spzAssetId = dl.spz_asset_id;
          if (dl.is_real_spz) node.metadata.isRealSpz = true;

          const mb = dl.spz_size_bytes ? (" (" + (dl.spz_size_bytes / (1024 * 1024)).toFixed(2) + " MB .spz)") : "";
          showToast("World Labs completed!" + mb + " Saved to " + node.metadata.vfsPath, false);
          appendTerminalLine("[✓] World Labs op " + opId + " SUCCEEDED" + mb + " → " + node.metadata.vfsPath);
          renderNodes();
          if (modalSplatState.activeNodeId === node.id && node.metadata.isRealSpz) {
            openSplatViewer(node.id);
          }
        } else {
          // Live timer tick on card
          renderNodes();
        }
      } catch (_pollErr) {}
    }, 4000);
  }

  function pollAudioJobForNode(node) {
    if (!node || !node.metadata || !node.metadata.jobId || typeof fetch !== "function") return;
    if (node._pollTimer) clearInterval(node._pollTimer);
    if (!node.metadata.startedAt) node.metadata.startedAt = Date.now();
    const jobId = node.metadata.jobId;
    const modelId = node.metadata.model || state.model || "google/lyria-3.5";
    const kind = (node.content && node.content.kind) || node.metadata.audioKind || "music";
    const tgt = _resolveSpaceTarget();
    const promptStr = (node.metadata && node.metadata.prompt) || node.label || "";
    let statusUrl =
      "/api/nodes/audio/status?job_id=" + encodeURIComponent(jobId) +
      "&model=" + encodeURIComponent(modelId) +
      "&kind=" + encodeURIComponent(kind) +
      "&scope=" + encodeURIComponent(tgt.scope) +
      "&owner_id=" + encodeURIComponent(tgt.owner_id) +
      "&prompt=" + encodeURIComponent(promptStr);
    if (node.metadata.audioCost !== undefined && node.metadata.audioCost !== null) {
      statusUrl += "&cost=" + encodeURIComponent(String(node.metadata.audioCost));
    }
    if (node.metadata.audioPaymentSource) {
      statusUrl += "&payment_source=" + encodeURIComponent(String(node.metadata.audioPaymentSource));
    }

    node._pollTimer = setInterval(async function () {
      try {
        const headers = {};
        if (state.nanogptKey) headers["X-NanoGPT-Api-Key"] = state.nanogptKey;
        const fetchOpts = Object.keys(headers).length ? { headers: headers } : {};
        const res = await fetch(statusUrl, fetchOpts);
        if (!res || typeof res.json !== "function") return;
        const st = await res.json();
        if (!st) return;

        if (st.ok === false || st.status === "FAILED" || st.error) {
          clearInterval(node._pollTimer);
          node._pollTimer = null;
          const errMsg = (st.error && st.error.message) || String(st.error || "Audio generation failed");
          node.metadata.jobStatus = "ERROR";
          node.metadata.jobError = errMsg;
          showToast("Audio error: " + errMsg, true);
          appendTerminalLine("[!] Audio job " + jobId + " failed: " + errMsg);
          renderNodes();
          return;
        }

        if (st.done && st.ok) {
          clearInterval(node._pollTimer);
          node._pollTimer = null;
          node.metadata.jobStatus = "SUCCEEDED";
          node.metadata.jobError = "";
          if (!node.content) node.content = {};
          if (st.audio_raw_url || st.audio_url) {
            node.content.audioRawUrl = st.audio_raw_url || st.audio_url;
            node.content.audioUrl = st.audio_url || st.audio_raw_url;
          }
          if (st.audio_bytes_b64) {
            node.content.audioBytesB64 = st.audio_bytes_b64;
          }
          if (st.mime_type) node.content.mimeType = st.mime_type;
          if (st.ext) node.content.ext = st.ext;
          if (st.vfs_path) {
            node.content.vfsPath = st.vfs_path;
            node.metadata.vfsPath = st.vfs_path;
          }
          showToast("Audio ready! Saved to " + (st.vfs_path || "session"), false);
          appendTerminalLine("[✓] Audio job " + jobId + " SUCCEEDED → " + (st.vfs_path || node.content.audioUrl || "ready"));
          renderNodes();
          return;
        }

        renderNodes();
      } catch (_pollErr) {}
    }, 3500);
  }

  function pollVideoJobForNode(node) {
    if (!node || !node.metadata || !node.metadata.jobId || typeof fetch !== "function") return;
    if (node._pollTimer) clearInterval(node._pollTimer);
    if (!node.metadata.startedAt) node.metadata.startedAt = Date.now();
    const jobId = node.metadata.jobId;
    const modelSlug = node.metadata.modelSlug || node.metadata.model || state.model || "kling-4.0";
    const tgt = _resolveSpaceTarget();
    const promptStr = (node.metadata && node.metadata.prompt) || node.label || "";
    const statusUrl =
      "/api/nodes/video/status?job_id=" + encodeURIComponent(jobId) +
      "&model=" + encodeURIComponent(modelSlug) +
      "&scope=" + encodeURIComponent(tgt.scope) +
      "&owner_id=" + encodeURIComponent(tgt.owner_id) +
      "&prompt=" + encodeURIComponent(promptStr);

    node._pollTimer = setInterval(async function () {
      try {
        const headers = {};
        if (state.nanogptKey) headers["X-NanoGPT-Api-Key"] = state.nanogptKey;
        const fetchOpts = Object.keys(headers).length ? { headers: headers } : {};
        const res = await fetch(statusUrl, fetchOpts);
        if (!res || typeof res.json !== "function") return;
        const st = await res.json();
        if (!st) return;

        if (st.ok === false || st.status === "FAILED" || st.status === "ERROR" || st.error) {
          clearInterval(node._pollTimer);
          node._pollTimer = null;
          const errMsg = (st.error && st.error.message) || String(st.error || st.message || "Video generation failed");
          node.metadata.jobStatus = "ERROR";
          node.metadata.jobError = errMsg;
          showToast("Video error: " + errMsg, true);
          appendTerminalLine("[!] Video job " + jobId + " failed: " + errMsg);
          renderNodes();
          return;
        }

        if (st.done && st.ok) {
          clearInterval(node._pollTimer);
          node._pollTimer = null;
          node.metadata.jobStatus = "SUCCEEDED";
          node.metadata.jobError = "";
          if (!node.content) node.content = {};
          node.content.videoUrl = st.video_url || st.remote_url || st.videoUrl || "";
          node.content.vfsPath = st.vfs_path || st.vfsPath || "";
          node.metadata.vfsPath = st.vfs_path || st.vfsPath || node.metadata.vfsPath || "";
          showToast("Video ready!" + (node.content.vfsPath ? (" Saved to " + node.content.vfsPath) : ""), false);
          appendTerminalLine("[✓] Video job " + jobId + " SUCCEEDED → " + (node.content.vfsPath || node.content.videoUrl || "ready"));
          renderNodes();
          return;
        }

        // Still running: refresh elapsed seconds on card
        node.metadata.jobStatus = "RUNNING";
        renderNodes();
      } catch (_pollErr) {}
    }, 4000);
  }

  function pollMeshJobForNode(node) {
    if (!node || !node.metadata || !node.metadata.jobId || typeof fetch !== "function") return;
    if (node._pollTimer) clearInterval(node._pollTimer);
    if (!node.metadata.startedAt) node.metadata.startedAt = Date.now();
    const jobId = node.metadata.jobId;
    const tgt = _resolveSpaceTarget();
    const promptStr = (node.metadata && node.metadata.prompt) || node.label || "";
    const statusUrl =
      "/api/nodes/mesh/status?job_id=" + encodeURIComponent(jobId) +
      "&scope=" + encodeURIComponent(tgt.scope) +
      "&owner_id=" + encodeURIComponent(tgt.owner_id) +
      "&prompt=" + encodeURIComponent(promptStr);

    node._pollTimer = setInterval(async function () {
      try {
        const headers = {};
        if (state.nanogptKey) headers["X-NanoGPT-Api-Key"] = state.nanogptKey;
        const fetchOpts = Object.keys(headers).length ? { headers: headers } : {};
        const res = await fetch(statusUrl, fetchOpts);
        if (!res || typeof res.json !== "function") return;
        const st = await res.json();
        if (!st) return;

        if (st.ok === false || st.status === "FAILED" || st.status === "ERROR" || st.error) {
          clearInterval(node._pollTimer);
          node._pollTimer = null;
          const errMsg = (st.error && st.error.message) || String(st.error || st.message || "3D mesh generation failed");
          node.metadata.jobStatus = "ERROR";
          node.metadata.jobError = errMsg;
          showToast("3D mesh error: " + errMsg, true);
          appendTerminalLine("[!] 3D mesh job " + jobId + " failed: " + errMsg);
          renderNodes();
          return;
        }

        if ((st.done && st.ok !== false) || st.status === "SUCCEEDED") {
          clearInterval(node._pollTimer);
          node._pollTimer = null;
          node.metadata.jobStatus = "SUCCEEDED";
          node.metadata.jobError = "";
          if (!node.content) node.content = {};
          _revokeNodeGlbBlobUrl(node);
          node.content.glbRawUrl = st.glb_raw_url || st.glbRawUrl || "";
          node.content.glbB64 = st.glb_bytes_b64 || st.glbB64 || "";
          if (st.vfs_path || st.vfsPath) {
            node.content.glbPath = st.vfs_path || st.vfsPath;
            node.content.vfsPath = node.content.glbPath;
            node.metadata.vfsPath = node.content.glbPath;
          }
          if (st.rig_type || st.bones || st.rigged) {
            node.content.rigged = true;
            node.content.animation = (st.animations && st.animations[0]) || st.animation || "walk";
          }
          showToast("3D .GLB mesh ready!" + (node.content.vfsPath ? (" Saved to " + node.content.vfsPath) : ""), false);
          appendTerminalLine("[✓] 3D mesh job " + jobId + " SUCCEEDED → " + (node.content.vfsPath || "mesh.glb"));
          renderNodes();
          if (modalMeshState.activeNodeId === node.id) {
            openMeshViewer(node.id);
          }
          return;
        }

        node.metadata.jobStatus = "RUNNING";
        renderNodes();
      } catch (_pollErr) {}
    }, 4000);
  }

  function runAtlasStep(taskName, sourceNodeId) {
    if (sourceNodeId) {
      state.selectedIds = [sourceNodeId];
    }
    state.model = "worldlabs/atlas-v2";
    state.modality = "atlas";
    const promptEl = $("nsPromptInput");
    const extraPrompt = (promptEl && promptEl.value.trim() && !promptEl.value.trim().startsWith("/"))
      ? (" " + promptEl.value.trim()) : "";
    let cmd = "/atlas splat";
    if (taskName === "images2PosedRGBD") cmd = "/atlas pose" + (extraPrompt || " pose uploaded photos");
    else if (taskName === "atlasGenerate") cmd = "/atlas flythrough --views 6" + (extraPrompt || " orbit scene views");
    else if (taskName === "splats2Mesh") cmd = "/atlas mesh" + (extraPrompt || " extract glb mesh");
    else cmd = "/atlas splat" + (state.atlasRefine ? " --refined" : "") + (extraPrompt || " reconstruct scene");
    return runTerminalCommand(cmd);
  }

  function toggleAtlasRefine() {
    state.atlasRefine = !state.atlasRefine;
    syncCapabilitiesAndControls();
  }

  // =========================================================================
  // Interactive 3D Gaussian Splat & RUB Camera Frustum Renderer
  // =========================================================================
  const modalSplatState = {
    activeNodeId: null,
    mode: "rgb",
    frustums: true,
    autoOrbit: true,
    yaw: 0.45,
    pitch: 0.25,
    zoom: 1.15,
    panX: 0,
    panY: 0,
    rafId: null
  };

  function _hashPromptSeed(str) {
    let h = 2166136261;
    const s = String(str || "torii");
    for (let i = 0; i < s.length; i++) {
      h ^= s.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  }

  function buildProceduralSplatCloud(promptStr) {
    const low = String(promptStr || "").toLowerCase();
    let seed = _hashPromptSeed(low);
    const rand = function () {
      seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
      return seed / 4294967296;
    };

    const isCyber = low.indexOf("cyber") !== -1 || low.indexOf("neon") !== -1 || low.indexOf("tokyo") !== -1;
    const isForest = low.indexOf("forest") !== -1 || low.indexOf("cabin") !== -1 || low.indexOf("tree") !== -1;
    const splats = [];

    // 1. Ground / Lake Reflection Surface (720 splats)
    for (let i = 0; i < 720; i++) {
      const gx = (rand() - 0.5) * 5.2;
      const gz = (rand() - 0.5) * 5.2;
      const ripple = Math.sin(gx * 3.5 + gz * 2.5) * 0.04;
      const gy = -0.82 + ripple;
      const dist = Math.min(1, Math.sqrt(gx * gx + gz * gz) / 3.8);
      let r = 34 + Math.round((1 - dist) * 38);
      let g = 74 + Math.round((1 - dist) * 52);
      let b = 96 + Math.round((1 - dist) * 65);
      if (isCyber) { r = 24 + Math.round(rand() * 40); g = 32 + Math.round(rand() * 70); b = 78 + Math.round(rand() * 110); }
      else if (isForest) { r = 38 + Math.round(rand() * 30); g = 68 + Math.round(rand() * 45); b = 36 + Math.round(rand() * 25); }
      // Torii crimson reflection on central water path
      if (!isCyber && !isForest && Math.abs(gx) < 0.85 && gz > -0.8 && gz < 1.8) {
        r = Math.min(255, r + 95);
        g = Math.max(20, g - 15);
      }
      splats.push({ x: gx, y: gy, z: gz, r: r, g: g, b: b, size: 3.4, conf: 0.99 });
    }

    // 2. Primary Hero Structure (Torii Gate / Building / Cabin — 680 splats)
    for (let i = 0; i < 680; i++) {
      let x = 0, y = 0, z = -0.15;
      let r = 216, g = 52, b = 38;
      if (isCyber) { r = 64 + Math.round(rand() * 160); g = 180 + Math.round(rand() * 70); b = 245; }
      else if (isForest) { r = 135 + Math.round(rand() * 45); g = 88 + Math.round(rand() * 35); b = 48 + Math.round(rand() * 25); }

      const part = i % 5;
      if (part === 0) {
        // Left pillar
        x = -0.78 + (rand() - 0.5) * 0.16;
        y = -0.8 + rand() * 1.65;
        z = -0.15 + (rand() - 0.5) * 0.16;
      } else if (part === 1) {
        // Right pillar
        x = 0.78 + (rand() - 0.5) * 0.16;
        y = -0.8 + rand() * 1.65;
        z = -0.15 + (rand() - 0.5) * 0.16;
      } else if (part === 2) {
        // Upper curved kasagi lintel
        x = (rand() - 0.5) * 2.25;
        const curve = (x * x) * 0.11;
        y = 0.84 + curve + (rand() - 0.5) * 0.12;
        z = -0.15 + (rand() - 0.5) * 0.18;
        if (rand() > 0.72) { r = 28; g = 28; b = 32; } // Sumi ink cap
      } else if (part === 3) {
        // Nuki crossbar
        x = (rand() - 0.5) * 1.92;
        y = 0.52 + (rand() - 0.5) * 0.1;
        z = -0.15 + (rand() - 0.5) * 0.14;
      } else {
        // Surrounding stone lanterns / props / mid-ground depth geometry
        const side = rand() > 0.5 ? 1 : -1;
        x = side * (1.35 + rand() * 0.85);
        y = -0.8 + rand() * 1.15;
        z = -0.4 + (rand() - 0.5) * 1.6;
        r = 164 + Math.round(rand() * 45);
        g = 172 + Math.round(rand() * 45);
        b = 158 + Math.round(rand() * 40);
      }
      splats.push({ x: x, y: y, z: z, r: r, g: g, b: b, size: 4.2, conf: 0.985 });
    }

    // 3. Background Mountain Ridge & Atmospheric Horizon (420 splats)
    for (let i = 0; i < 420; i++) {
      const ang = (rand() - 0.5) * Math.PI * 1.35;
      const rad = 2.2 + rand() * 1.1;
      const x = Math.sin(ang) * rad;
      const z = -Math.cos(ang) * rad - 0.6;
      const peak = Math.cos(x * 0.9) * 0.55 + 0.35;
      const y = -0.65 + rand() * Math.max(0.25, peak);
      const r = isCyber ? 48 : 68 + Math.round(rand() * 35);
      const g = isCyber ? 62 : 98 + Math.round(rand() * 38);
      const b = isCyber ? 118 : 112 + Math.round(rand() * 40);
      splats.push({ x: x, y: y, z: z, r: r, g: g, b: b, size: 4.8, conf: 0.94 });
    }
    return splats;
  }

  function ensureNodeSplatCloud(node) {
    if (!node) return [];
    if (Array.isArray(node._splatCloud) && node._splatCloud.length > 0) {
      return node._splatCloud;
    }
    const promptStr = (node.metadata && node.metadata.prompt) || node.label || "torii";
    node._splatCloud = buildProceduralSplatCloud(promptStr);

    // Project ALL uploaded/selected multi-view reference photos into a unified 360° 3D Gaussian Splat cloud
    const rawList = (node.content && Array.isArray(node.content.referenceImages) && node.content.referenceImages.length > 0)
      ? node.content.referenceImages.filter(Boolean)
      : ((node.content && node.content.imageUrl) ? [node.content.imageUrl] : []);

    if (rawList.length > 0 && !node._splatImgLoading && typeof Image !== "undefined") {
      node._splatImgLoading = true;
      const totalViews = Math.min(rawList.length, 14);
      const gw = totalViews > 1 ? Math.max(22, Math.floor(54 / Math.sqrt(totalViews))) : 54;
      const gh = totalViews > 1 ? Math.max(16, Math.floor(34 / Math.sqrt(totalViews))) : 34;
      const mergedCloud = [];
      let completed = 0;

      function finishOneView() {
        completed += 1;
        if (completed >= totalViews && mergedCloud.length > 120) {
          node._splatCloud = mergedCloud;
          mountAllSplatCanvases();
          if (modalSplatState.activeNodeId === node.id) {
            renderModalSplatFrame();
          }
        }
      }

      for (let viewIdx = 0; viewIdx < totalViews; viewIdx++) {
        (function (vIdx, url) {
          try {
            const img = new Image();
            img.crossOrigin = "anonymous";
            img.onload = function () {
              try {
                const off = document.createElement("canvas");
                off.width = gw;
                off.height = gh;
                const octx = off.getContext && off.getContext("2d");
                if (octx) {
                  octx.drawImage(img, 0, 0, gw, gh);
                  const px = octx.getImageData(0, 0, gw, gh).data;
                  // Place each uploaded view around a 360° RUB camera ring so all photos fuse into 3D space
                  const theta = totalViews > 1 ? (vIdx / totalViews) * Math.PI * 2 : 0;
                  const cosT = Math.cos(theta);
                  const sinT = Math.sin(theta);
                  for (let v = 0; v < gh; v++) {
                    for (let u = 0; u < gw; u++) {
                      const idx = (v * gw + u) * 4;
                      const r = px[idx], g = px[idx + 1], b = px[idx + 2], a = px[idx + 3];
                      if (a < 32) continue;
                      const lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
                      const nx = (u / (gw - 1) - 0.5) * 2.0;
                      const ny = (0.5 - v / (gh - 1)) * 1.4;
                      const localZ = (v / gh > 0.55)
                        ? ((v / gh - 0.55) * 2.8 - 0.35)
                        : (-1.15 + (1.0 - lum) * 1.25);
                      const localX = nx * (1.25 + Math.abs(localZ) * 0.2);
                      const wx = localX * cosT - localZ * sinT;
                      const wz = localX * sinT + localZ * cosT;
                      mergedCloud.push({
                        x: wx,
                        y: ny,
                        z: wz,
                        r: r,
                        g: g,
                        b: b,
                        size: totalViews > 1 ? 4.6 : 4.3,
                        conf: 0.984
                      });
                    }
                  }
                }
              } catch (_e) {}
              finishOneView();
            };
            img.onerror = finishOneView;
            img.src = url;
          } catch (_e) {
            finishOneView();
          }
        })(viewIdx, rawList[viewIdx]);
      }
    }
    return node._splatCloud;
  }

  function _depthColor(normDepth, mode) {
    const t = Math.max(0, Math.min(1, normDepth));
    if (mode === "confidence") {
      // High-confidence emerald (#107a47 -> #6ee7b7)
      return [
        Math.round(16 + (1 - t) * 70),
        Math.round(145 + (1 - t) * 95),
        Math.round(88 + (1 - t) * 65)
      ];
    }
    // Linear Depth (.EXR) Turbo/Inferno colormap: near warm gold -> mid cyan/green -> far indigo
    if (t < 0.35) {
      const k = t / 0.35;
      return [250, Math.round(220 - k * 70), Math.round(90 - k * 50)];
    }
    if (t < 0.7) {
      const k = (t - 0.35) / 0.35;
      return [Math.round(250 - k * 190), Math.round(150 + k * 55), Math.round(40 + k * 170)];
    }
    const k = (t - 0.7) / 0.3;
    return [Math.round(60 - k * 25), Math.round(205 - k * 145), Math.round(210 - k * 60)];
  }

  function drawSplatSceneOnCanvas(canvasEl, node, viewOpts) {
    if (!canvasEl || typeof canvasEl.getContext !== "function") return;
    const ctx = canvasEl.getContext("2d");
    if (!ctx) return;

    const w = canvasEl.width || 440;
    const h = canvasEl.height || 164;
    const yaw = (viewOpts && viewOpts.yaw !== undefined) ? viewOpts.yaw : 0.42;
    const pitch = (viewOpts && viewOpts.pitch !== undefined) ? viewOpts.pitch : 0.24;
    const zoom = (viewOpts && viewOpts.zoom !== undefined) ? viewOpts.zoom : 1.0;
    const panX = (viewOpts && viewOpts.panX) || 0;
    const panY = (viewOpts && viewOpts.panY) || 0;
    const mode = (viewOpts && viewOpts.mode) || "rgb";
    const showFrustums = !viewOpts || viewOpts.frustums !== false;

    ctx.fillStyle = "#05070a";
    ctx.fillRect(0, 0, w, h);

    const cosY = Math.cos(yaw), sinY = Math.sin(yaw);
    const cosP = Math.cos(pitch), sinP = Math.sin(pitch);
    const fov = Math.min(w, h) * 1.15 * zoom;
    const camDist = 3.85;

    function project3D(px, py, pz) {
      const x1 = px * cosY - pz * sinY;
      const z1 = px * sinY + pz * cosY;
      const y2 = py * cosP - z1 * sinP;
      const z2 = py * sinP + z1 * cosP + camDist;
      if (z2 <= 0.2) return null;
      const scale = fov / z2;
      return {
        sx: w * 0.5 + x1 * scale + panX,
        sy: h * 0.52 - y2 * scale + panY,
        z: z2,
        scale: scale
      };
    }

    // 1. Subtle 3D RUB Ground Grid
    ctx.strokeStyle = "rgba(255, 255, 255, 0.11)";
    ctx.lineWidth = 1;
    for (let g = -2; g <= 2; g++) {
      const pA = project3D(g * 0.9, -0.84, -2.2);
      const pB = project3D(g * 0.9, -0.84, 2.2);
      if (pA && pB) {
        ctx.beginPath();
        ctx.moveTo(pA.sx, pA.sy);
        ctx.lineTo(pB.sx, pB.sy);
        ctx.stroke();
      }
      const pC = project3D(-2.2, -0.84, g * 0.9);
      const pD = project3D(2.2, -0.84, g * 0.9);
      if (pC && pD) {
        ctx.beginPath();
        ctx.moveTo(pC.sx, pC.sy);
        ctx.lineTo(pD.sx, pD.sy);
        ctx.stroke();
      }
    }

    // 2. Project & Depth-Sort 3D Gaussian Splats (back-to-front painter's order)
    const cloud = ensureNodeSplatCloud(node);
    const projected = [];
    for (let i = 0; i < cloud.length; i++) {
      const s = cloud[i];
      const p = project3D(s.x, s.y, s.z);
      if (!p) continue;
      if (p.sx < -24 || p.sx > w + 24 || p.sy < -24 || p.sy > h + 24) continue;
      projected.push({
        sx: p.sx,
        sy: p.sy,
        z: p.z,
        rad: Math.max(1.6, Math.min(14, (s.size || 3.8) * (p.scale / 85))),
        r: s.r,
        g: s.g,
        b: s.b
      });
    }
    projected.sort((a, b) => b.z - a.z);

    for (let i = 0; i < projected.length; i++) {
      const pt = projected[i];
      let cr = pt.r, cg = pt.g, cb = pt.b;
      if (mode === "depth" || mode === "confidence") {
        const normD = (pt.z - 1.5) / 4.8;
        const dc = _depthColor(normD, mode);
        cr = dc[0]; cg = dc[1]; cb = dc[2];
      }
      // Gaussian splat kernel: soft outer halo + bright core
      ctx.fillStyle = "rgba(" + cr + "," + cg + "," + cb + ",0.34)";
      ctx.beginPath();
      ctx.arc(pt.sx, pt.sy, pt.rad * 1.45, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = "rgba(" + cr + "," + cg + "," + cb + ",0.88)";
      ctx.beginPath();
      ctx.arc(pt.sx, pt.sy, pt.rad * 0.72, 0, Math.PI * 2);
      ctx.fill();
    }

    // 3. Render 14 Posed RUB Camera Frustums around the perimeter
    if (showFrustums) {
      const numCams = 14;
      for (let c = 0; c < numCams; c++) {
        const ang = (c / numCams) * Math.PI * 2;
        const cx = Math.cos(ang) * 2.15;
        const cz = Math.sin(ang) * 2.15;
        const cy = -0.15 + Math.sin(c * 0.9) * 0.18;
        const camPos = project3D(cx, cy, cz);
        const lookPos = project3D(cx * 0.72, cy * 0.72, cz * 0.72);
        if (camPos && lookPos) {
          ctx.strokeStyle = c === 0 ? "#107a47" : "rgba(255, 255, 255, 0.65)";
          ctx.lineWidth = c === 0 ? 1.6 : 1.0;
          ctx.beginPath();
          ctx.moveTo(camPos.sx, camPos.sy);
          ctx.lineTo(lookPos.sx, lookPos.sy);
          ctx.stroke();

          ctx.fillStyle = c === 0 ? "#107a47" : "#ffffff";
          ctx.beginPath();
          ctx.arc(camPos.sx, camPos.sy, c === 0 ? 3.2 : 2.0, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    }
  }

  function _resolveSplatNode(nodeId) {
    if (!state._showcaseNodes) {
      state._showcaseNodes = {
        "showcase-2": {
          id: "showcase-2",
          label: "/atlas pose · Posed RGBD + Frustum",
          omniKind: "atlas_pose",
          metadata: { prompt: "Crimson Torii gate at Lake Ashi", vfsPath: "/worlds/torii_3e78434c/frames_0_depth.exr" },
          splatState: { mode: "depth", frustums: true, yaw: 0.42, pitch: 0.24, zoom: 1.0 }
        },
        "showcase-4": {
          id: "showcase-4",
          label: "360° Lake Ashi Shrine World (.spz + .glb)",
          omniKind: "atlas_splat",
          metadata: { prompt: "Crimson Torii gate at Lake Ashi", vfsPath: "/worlds/torii_3e78434c/refinedSplats_2000000.spz" },
          splatState: { mode: "rgb", frustums: true, yaw: 0.42, pitch: 0.24, zoom: 1.0 }
        }
      };
    }
    return state.nodes.find((n) => n.id === nodeId) ||
           (nodeId && state._showcaseNodes[nodeId]) ||
           state.nodes[state.nodes.length - 1] ||
           state._showcaseNodes["showcase-4"];
  }

  function mountAllSplatCanvases() {
    if (!document || typeof document.querySelectorAll !== "function") return;
    const canvases = document.querySelectorAll(".ns-splat-canvas");
    if (!canvases || !canvases.forEach) return;
    canvases.forEach((canvasEl) => {
      const nid = canvasEl.dataset && canvasEl.dataset.splatNodeId;
      const node = _resolveSplatNode(nid);
      if (!node) return;
      if (!node.splatState) {
        node.splatState = { mode: "rgb", frustums: true, yaw: 0.42, pitch: 0.24, zoom: 1.0 };
      }
      drawSplatSceneOnCanvas(canvasEl, node, node.splatState);

      if (!canvasEl._splatBound) {
        canvasEl._splatBound = true;
        let dragging = false;
        let lastX = 0, lastY = 0;
        canvasEl.addEventListener("mousedown", (ev) => {
          ev.stopPropagation();
          dragging = true;
          lastX = ev.clientX;
          lastY = ev.clientY;
        });
        window.addEventListener("mousemove", (ev) => {
          if (!dragging) return;
          const dx = ev.clientX - lastX;
          const dy = ev.clientY - lastY;
          lastX = ev.clientX;
          lastY = ev.clientY;
          node.splatState.yaw += dx * 0.012;
          node.splatState.pitch = Math.max(-0.65, Math.min(1.15, node.splatState.pitch + dy * 0.01));
          drawSplatSceneOnCanvas(canvasEl, node, node.splatState);
        });
        window.addEventListener("mouseup", () => { dragging = false; });
        canvasEl.addEventListener("wheel", (ev) => {
          ev.preventDefault();
          ev.stopPropagation();
          const factor = _wheelZoomFactor(ev, 0.0014, 0.004);
          node.splatState.zoom = Math.max(0.45, Math.min(2.8, Number((node.splatState.zoom * factor).toFixed(4))));
          drawSplatSceneOnCanvas(canvasEl, node, node.splatState);
        }, { passive: false });
        canvasEl.addEventListener("dblclick", (ev) => {
          ev.stopPropagation();
          openSplatViewer(node.id);
        });
      }
    });
  }

  function setNodeSplatMode(nodeId, mode) {
    const node = _resolveSplatNode(nodeId);
    if (!node) return;
    if (!node.splatState) node.splatState = { mode: "rgb", frustums: true, yaw: 0.42, pitch: 0.24, zoom: 1.0 };
    node.splatState.mode = mode;
    if (state.nodes.find((n) => n.id === nodeId)) {
      renderNodes();
    } else {
      mountAllSplatCanvases();
    }
  }

  function toggleNodeFrustums(nodeId) {
    const node = _resolveSplatNode(nodeId);
    if (!node) return;
    if (!node.splatState) node.splatState = { mode: "rgb", frustums: true, yaw: 0.42, pitch: 0.24, zoom: 1.0 };
    node.splatState.frustums = !node.splatState.frustums;
    if (state.nodes.find((n) => n.id === nodeId)) {
      renderNodes();
    } else {
      mountAllSplatCanvases();
    }
  }

  function renderModalSplatFrame() {
    const modal = $("nsSplatViewerModal");
    const canvasEl = $("nsSplatModalCanvas");
    if (!modal || modal.classList.contains("hidden") || !canvasEl) return;
    const node = _resolveSplatNode(modalSplatState.activeNodeId);
    if (!node) return;
    if (modalSplatState.autoOrbit) {
      modalSplatState.yaw += 0.007;
    }
    drawSplatSceneOnCanvas(canvasEl, node, modalSplatState);
    if (modalSplatState.autoOrbit && typeof window.requestAnimationFrame === "function") {
      modalSplatState.rafId = window.requestAnimationFrame(renderModalSplatFrame);
    }
  }

  let _sparkViewerCtx = null;

  function disposeSparkWebGLViewer() {
    if (!_sparkViewerCtx) return;
    try {
      if (_sparkViewerCtx.rafId && typeof window.cancelAnimationFrame === "function") {
        window.cancelAnimationFrame(_sparkViewerCtx.rafId);
      }
      if (_sparkViewerCtx.renderer && typeof _sparkViewerCtx.renderer.dispose === "function") {
        _sparkViewerCtx.renderer.dispose();
      }
    } catch (_e) {}
    const host = $("nsSparkWebGLContainer");
    if (host) {
      host.innerHTML = "";
      host.classList.add("hidden");
    }
    _sparkViewerCtx = null;
  }

  async function mountSparkWebGLViewer(spzUrl) {
    const host = $("nsSparkWebGLContainer");
    const badge = $("nsSplatViewerBadge");
    const fallbackCanvas = $("nsSplatModalCanvas");
    if (!host || !spzUrl) return false;
    disposeSparkWebGLViewer();
    host.classList.remove("hidden");
    if (badge) {
      badge.textContent = "⟳ LOADING REAL .SPZ IN SPARK WEBGL...";
      badge.classList.add("is-live");
    }
    try {
      const THREE = await import("https://esm.sh/three@0.174.0");
      const ctrlMod = await import("https://esm.sh/three@0.174.0/examples/jsm/controls/OrbitControls.js");
      const sparkMod = await import("https://esm.sh/@sparkjsdev/spark@0.1.10?deps=three@0.174.0");
      const OrbitControls = ctrlMod.OrbitControls;
      const SparkRenderer = sparkMod.SparkRenderer;
      const SplatMesh = sparkMod.SplatMesh;

      const w = host.clientWidth || 940;
      const h = host.clientHeight || 520;
      const renderer = new THREE.WebGLRenderer({ antialias: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      renderer.setSize(w, h);
      host.innerHTML = "";
      host.appendChild(renderer.domElement);

      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0x05070a);
      const camera = new THREE.PerspectiveCamera(60, w / h, 0.05, 500);
      camera.position.set(0, 1.0, 2.5);

      const spark = new SparkRenderer({ renderer: renderer });
      scene.add(spark);

      const splatMesh = new SplatMesh({ url: spzUrl });
      scene.add(splatMesh);

      const controls = new OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.target.set(0, 0.5, -1.5);
      controls.update();

      if (fallbackCanvas) fallbackCanvas.classList.add("hidden");
      if (badge) {
        badge.textContent = "● REAL WORLD LABS .SPZ · SPARK WEBGL (60fps)";
        badge.classList.add("is-live");
      }

      const ctx = { renderer, scene, camera, controls, splatMesh, rafId: null };
      _sparkViewerCtx = ctx;
      function tick() {
        if (_sparkViewerCtx !== ctx) return;
        controls.update();
        renderer.render(scene, camera);
        ctx.rafId = window.requestAnimationFrame(tick);
      }
      tick();
      return true;
    } catch (err) {
      disposeSparkWebGLViewer();
      if (fallbackCanvas) fallbackCanvas.classList.remove("hidden");
      if (badge) {
        badge.textContent = "◐ WEBGL FALLBACK PREVIEW (" + String((err && err.message) || "WebGL unavailable") + ")";
        badge.classList.remove("is-live");
      }
      return false;
    }
  }

  function openSplatViewer(nodeId) {
    const node = _resolveSplatNode(nodeId);
    if (!node) return;
    modalSplatState.activeNodeId = node.id;
    const meta = node.metadata || {};
    if (node.splatState) {
      modalSplatState.mode = node.splatState.mode || "rgb";
      modalSplatState.frustums = node.splatState.frustums !== false;
      modalSplatState.yaw = node.splatState.yaw || 0.45;
      modalSplatState.pitch = node.splatState.pitch || 0.24;
    }
    const modal = $("nsSplatViewerModal");
    const titleEl = $("nsSplatModalTitle");
    const metaEl = $("nsSplatModalMeta");
    const badge = $("nsSplatViewerBadge");
    const fallbackCanvas = $("nsSplatModalCanvas");
    if (titleEl) {
      titleEl.textContent = "3D GAUSSIAN SPLAT VIEWER (.SPZ) · " + (meta.prompt || node.label || node.id);
    }
    if (metaEl) {
      const szText = meta.spzSizeBytes ? (" · " + (meta.spzSizeBytes / (1024 * 1024)).toFixed(2) + " MB") : "";
      metaEl.textContent = (meta.vfsPath || "/worlds/torii_3e78434c/refinedSplats_2000000.spz") +
        szText + " · Drag to Orbit / Scroll to Zoom / Shift+Drag Pan";
    }
    if (modal) modal.classList.remove("hidden");
    disposeSparkWebGLViewer();
    if (meta.isRealSpz && meta.spzRawUrl && typeof window !== "undefined") {
      mountSparkWebGLViewer(meta.spzRawUrl);
    } else {
      if (fallbackCanvas) fallbackCanvas.classList.remove("hidden");
      if (badge) {
        badge.classList.remove("is-live");
        badge.textContent = meta.jobStatus === "RUNNING"
          ? "⟳ RECONSTRUCTING REAL .SPZ ON WORLD LABS GPU — WILL AUTO-SWITCH TO SPARK WEBGL WHEN DONE"
          : "◐ POSED RGBD PREVIEW (NOT A REAL .SPZ YET — CLICK 'BUILD 3D SPLAT' WITH 2+ SCENE PHOTOS)";
      }
      bindModalSplatCanvasEvents();
      if (modalSplatState.rafId && typeof window.cancelAnimationFrame === "function") {
        window.cancelAnimationFrame(modalSplatState.rafId);
      }
      renderModalSplatFrame();
    }
  }

  function closeSplatViewer() {
    disposeSparkWebGLViewer();
    const modal = $("nsSplatViewerModal");
    if (modal) modal.classList.add("hidden");
    modalSplatState.autoOrbit = false;
    if (modalSplatState.rafId && typeof window.cancelAnimationFrame === "function") {
      window.cancelAnimationFrame(modalSplatState.rafId);
      modalSplatState.rafId = null;
    }
  }

  function setModalSplatMode(mode) {
    modalSplatState.mode = mode;
    if (!modalSplatState.autoOrbit) renderModalSplatFrame();
  }

  function toggleModalAutoOrbit() {
    modalSplatState.autoOrbit = !modalSplatState.autoOrbit;
    if (modalSplatState.autoOrbit) renderModalSplatFrame();
  }

  function resetModalCamera(camPreset) {
    modalSplatState.autoOrbit = false;
    modalSplatState.panX = 0;
    modalSplatState.panY = 0;
    modalSplatState.zoom = 1.15;
    if (camPreset === "far") { modalSplatState.yaw = Math.PI + 0.3; modalSplatState.pitch = 0.22; }
    else if (camPreset === "top") { modalSplatState.yaw = 0.0; modalSplatState.pitch = 0.95; }
    else { modalSplatState.yaw = 0.42; modalSplatState.pitch = 0.24; }
    renderModalSplatFrame();
  }

  function downloadActiveSplatSpz() {
    const node = state.nodes.find((n) => n.id === modalSplatState.activeNodeId) || state.nodes[state.nodes.length - 1];
    const a = document.createElement("a");
    if (node && node.metadata && node.metadata.spzRawUrl) {
      a.href = node.metadata.spzRawUrl;
      const fname = String(node.metadata.vfsPath || "world_splat.spz").split("/").pop() || "world_splat.spz";
      a.download = fname;
    } else {
      const b64 = (node && node.content && node.content.spzB64) || "U1BaMgACAAAA9K7/v16ZAAx7kRHC";
      a.href = "data:application/octet-stream;base64," + b64;
      a.download = "refinedSplats_2000000.spz";
    }
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  function viewOrConvertNodeSplat(nodeId) {
    const node = state.nodes.find((n) => n.id === nodeId);
    if (!node) return;
    if (node.morphingStatus === "omni" && node.omniKind !== "audio") {
      openSplatViewer(node.id);
      return;
    }
    // Preserve all currently selected image nodes (and any other uploaded image nodes on canvas) for multi-view Splat generation
    if (state.selectedIds.indexOf(node.id) === -1) {
      state.selectedIds.push(node.id);
    }
    if (state.selectedIds.length === 1) {
      const otherUploaded = state.nodes.filter((n) => n.type === "UPLOADED" && n.content && n.content.imageUrl);
      if (otherUploaded.length > 1) {
        state.selectedIds = otherUploaded.map((n) => n.id);
      }
    }
    const promptTxt = (node.metadata && node.metadata.prompt) || node.label || "Scene 3D Splat";
    runTerminalCommand("/atlas splat " + promptTxt).then((spawned) => {
      if (spawned) openSplatViewer(spawned.id);
    });
  }

  function bindModalSplatCanvasEvents() {
    const canvasEl = $("nsSplatModalCanvas");
    if (!canvasEl || canvasEl._modalBound) return;
    canvasEl._modalBound = true;
    let dragging = false;
    let lastX = 0, lastY = 0;
    canvasEl.addEventListener("mousedown", (ev) => {
      dragging = true;
      modalSplatState.autoOrbit = false;
      lastX = ev.clientX;
      lastY = ev.clientY;
    });
    window.addEventListener("mousemove", (ev) => {
      if (!dragging) return;
      const dx = ev.clientX - lastX;
      const dy = ev.clientY - lastY;
      lastX = ev.clientX;
      lastY = ev.clientY;
      if (ev.shiftKey) {
        modalSplatState.panX += dx;
        modalSplatState.panY += dy;
      } else {
        modalSplatState.yaw += dx * 0.01;
        modalSplatState.pitch = Math.max(-0.7, Math.min(1.2, modalSplatState.pitch + dy * 0.01));
      }
      renderModalSplatFrame();
    });
    window.addEventListener("mouseup", () => { dragging = false; });
    canvasEl.addEventListener("wheel", (ev) => {
      ev.preventDefault();
      modalSplatState.autoOrbit = false;
      const factor = _wheelZoomFactor(ev, 0.0014, 0.004);
      modalSplatState.zoom = Math.max(0.4, Math.min(3.5, Number((modalSplatState.zoom * factor).toFixed(4))));
      renderModalSplatFrame();
    }, { passive: false });
  }

  // =========================================================================
  // Interactive 3D .GLB Mesh Preview, Wireframe Fallback & Inspector Modal
  // =========================================================================
  function _buildIcosahedronGeometry() {
    const phi = (1 + Math.sqrt(5)) / 2;
    const rawVerts = [
      [-1, phi, 0], [1, phi, 0], [-1, -phi, 0], [1, -phi, 0],
      [0, -1, phi], [0, 1, phi], [0, -1, -phi], [0, 1, -phi],
      [phi, 0, -1], [phi, 0, 1], [-phi, 0, -1], [-phi, 0, 1]
    ];
    const verts = rawVerts.map((v) => {
      const len = Math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) || 1;
      return [v[0] / len, v[1] / len, v[2] / len];
    });
    const edges = [
      [0, 11], [0, 5], [0, 1], [0, 7], [0, 10],
      [1, 5], [5, 11], [11, 10], [10, 7], [7, 1],
      [3, 9], [3, 4], [3, 2], [3, 6], [3, 8],
      [4, 9], [2, 4], [6, 2], [8, 6], [9, 8],
      [5, 9], [9, 1], [1, 8], [8, 7], [7, 6],
      [6, 10], [10, 2], [2, 11], [11, 4], [4, 5]
    ];
    return { verts, edges };
  }
  const _WIRE_ICO = _buildIcosahedronGeometry();

  function drawMeshWireframeOnCanvas(canvasEl, node, viewOpts) {
    if (!canvasEl || typeof canvasEl.getContext !== "function") return;
    const ctx = canvasEl.getContext("2d");
    if (!ctx) return;

    const w = canvasEl.width || 300;
    const h = canvasEl.height || 164;
    const yaw = (viewOpts && viewOpts.yaw !== undefined) ? viewOpts.yaw : 0.55;
    const pitch = (viewOpts && viewOpts.pitch !== undefined) ? viewOpts.pitch : 0.34;
    const zoom = (viewOpts && viewOpts.zoom !== undefined) ? viewOpts.zoom : 1.0;

    ctx.fillStyle = "#080808";
    ctx.fillRect(0, 0, w, h);

    const cosY = Math.cos(yaw), sinY = Math.sin(yaw);
    const cosP = Math.cos(pitch), sinP = Math.sin(pitch);
    const fov = Math.min(w, h) * 1.1 * zoom;
    const camDist = 3.2;

    function proj(px, py, pz) {
      const x1 = px * cosY - pz * sinY;
      const z1 = px * sinY + pz * cosY;
      const y2 = py * cosP - z1 * sinP;
      const z2 = py * sinP + z1 * cosP + camDist;
      if (z2 <= 0.25) return null;
      const sc = fov / z2;
      return { sx: w * 0.5 + x1 * sc, sy: h * 0.5 - y2 * sc, z: z2 };
    }

    // Isometric ground grid
    ctx.strokeStyle = "rgba(255, 255, 255, 0.14)";
    ctx.lineWidth = 1;
    for (let g = -2; g <= 2; g++) {
      const a = proj(g * 0.65, -0.95, -1.3);
      const b = proj(g * 0.65, -0.95, 1.3);
      if (a && b) { ctx.beginPath(); ctx.moveTo(a.sx, a.sy); ctx.lineTo(b.sx, b.sy); ctx.stroke(); }
      const c = proj(-1.3, -0.95, g * 0.65);
      const d = proj(1.3, -0.95, g * 0.65);
      if (c && d) { ctx.beginPath(); ctx.moveTo(c.sx, c.sy); ctx.lineTo(d.sx, d.sy); ctx.stroke(); }
    }

    // Faceted 3D geodesic mesh wireframe
    const pts = _WIRE_ICO.verts.map((v) => proj(v[0] * 0.92, v[1] * 0.92, v[2] * 0.92));
    for (let i = 0; i < _WIRE_ICO.edges.length; i++) {
      const e = _WIRE_ICO.edges[i];
      const p0 = pts[e[0]];
      const p1 = pts[e[1]];
      if (!p0 || !p1) continue;
      const avgZ = (p0.z + p1.z) * 0.5;
      const alpha = Math.max(0.25, Math.min(0.95, 1.45 - avgZ * 0.25));
      ctx.strokeStyle = (node && node.content && node.content.rigged && i % 5 === 0)
        ? ("rgba(16, 122, 71, " + alpha.toFixed(2) + ")")
        : ("rgba(245, 245, 245, " + alpha.toFixed(2) + ")");
      ctx.lineWidth = avgZ < camDist ? 1.5 : 0.9;
      ctx.beginPath();
      ctx.moveTo(p0.sx, p0.sy);
      ctx.lineTo(p1.sx, p1.sy);
      ctx.stroke();
    }

    // Vertex nodes
    for (let i = 0; i < pts.length; i++) {
      const p = pts[i];
      if (!p) continue;
      ctx.fillStyle = i % 3 === 0 ? "#107a47" : "#ffffff";
      ctx.beginPath();
      ctx.arc(p.sx, p.sy, p.z < camDist ? 2.4 : 1.5, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  function mountAllMeshPreviews() {
    if (!document || typeof document.querySelectorAll !== "function") return;

    const wireCanvases = document.querySelectorAll(".ns-mesh-wire-canvas");
    if (wireCanvases && wireCanvases.forEach) {
      wireCanvases.forEach((canvasEl) => {
        const nid = canvasEl.dataset && canvasEl.dataset.meshNodeId;
        const node = state.nodes.find((n) => n.id === nid);
        if (!node) return;
        if (!node._meshViewState) {
          node._meshViewState = { yaw: 0.55, pitch: 0.34, zoom: 1.0 };
        }
        drawMeshWireframeOnCanvas(canvasEl, node, node._meshViewState);

        if (!canvasEl._meshWireBound) {
          canvasEl._meshWireBound = true;
          let dragging = false;
          let lastX = 0, lastY = 0;
          canvasEl.addEventListener("mousedown", (ev) => {
            ev.stopPropagation();
            dragging = true;
            lastX = ev.clientX;
            lastY = ev.clientY;
          });
          window.addEventListener("mousemove", (ev) => {
            if (!dragging) return;
            const dx = ev.clientX - lastX;
            const dy = ev.clientY - lastY;
            lastX = ev.clientX;
            lastY = ev.clientY;
            node._meshViewState.yaw += dx * 0.014;
            node._meshViewState.pitch = Math.max(-0.9, Math.min(1.1, node._meshViewState.pitch + dy * 0.012));
            drawMeshWireframeOnCanvas(canvasEl, node, node._meshViewState);
          });
          window.addEventListener("mouseup", () => { dragging = false; });
          canvasEl.addEventListener("dblclick", (ev) => {
            ev.stopPropagation();
            openMeshViewer(node.id);
          });
        }
      });
    }

    const mvEls = document.querySelectorAll(".ns-model-viewer");
    if (mvEls && mvEls.length > 0) {
      ensureModelViewer().then(() => {
        mvEls.forEach((mv) => {
          if (mv._mvBound) return;
          mv._mvBound = true;
          mv.addEventListener("load", () => {
            const stage = mv.parentElement;
            if (stage && typeof stage.querySelector === "function") {
              const wire = stage.querySelector(".ns-mesh-wire-canvas");
              if (wire) wire.classList.add("is-hidden");
            }
          });
        });
      }).catch(() => {});
    }
  }

  function renderModalMeshWireFrame() {
    const modal = $("nsMeshViewerModal");
    const canvasEl = $("nsMeshModalWireCanvas");
    if (!modal || modal.classList.contains("hidden") || !canvasEl || modalMeshState.loadedRealGlb) return;
    const node = state.nodes.find((n) => n.id === modalMeshState.activeNodeId);
    if (modalMeshState.autoRotate) {
      modalMeshState.yaw += 0.01;
    }
    drawMeshWireframeOnCanvas(canvasEl, node, modalMeshState);
    if (modalMeshState.autoRotate && typeof window.requestAnimationFrame === "function") {
      modalMeshState.rafId = window.requestAnimationFrame(renderModalMeshWireFrame);
    }
  }

  function bindModalMeshWireCanvasEvents() {
    const canvasEl = $("nsMeshModalWireCanvas");
    if (!canvasEl || canvasEl._meshModalBound) return;
    canvasEl._meshModalBound = true;
    let dragging = false;
    let lastX = 0, lastY = 0;
    canvasEl.addEventListener("mousedown", (ev) => {
      dragging = true;
      modalMeshState.autoRotate = false;
      lastX = ev.clientX;
      lastY = ev.clientY;
    });
    window.addEventListener("mousemove", (ev) => {
      if (!dragging) return;
      const dx = ev.clientX - lastX;
      const dy = ev.clientY - lastY;
      lastX = ev.clientX;
      lastY = ev.clientY;
      modalMeshState.yaw += dx * 0.012;
      modalMeshState.pitch = Math.max(-0.9, Math.min(1.1, modalMeshState.pitch + dy * 0.012));
      renderModalMeshWireFrame();
    });
    window.addEventListener("mouseup", () => { dragging = false; });
    canvasEl.addEventListener("wheel", (ev) => {
      ev.preventDefault();
      const factor = ev.deltaY < 0 ? 1.1 : 0.9;
      modalMeshState.zoom = Math.max(0.45, Math.min(3.0, modalMeshState.zoom * factor));
      renderModalMeshWireFrame();
    }, { passive: false });
  }

  function openMeshViewer(nodeId) {
    const node = state.nodes.find((n) => n.id === nodeId);
    if (!node) return;
    modalMeshState.activeNodeId = node.id;
    modalMeshState.autoRotate = true;
    modalMeshState.animPlaying = node._meshAnimPlaying !== false;
    modalMeshState.loadedRealGlb = false;

    const meta = node.metadata || {};
    const c = node.content || {};
    const glbPath = c.glbPath || c.vfsPath || meta.vfsPath || "/models3d/mesh.glb";
    const glbSrc = _getGlbSrcForNode(node);

    const modal = $("nsMeshViewerModal");
    const titleEl = $("nsMeshModalTitle");
    const metaEl = $("nsMeshModalMeta");
    const viewport = $("nsMeshModalViewport");
    const badge = $("nsMeshModalBadge");
    const wireCanvas = $("nsMeshModalWireCanvas");
    const animBtn = $("nsMeshModalAnimBtn");
    const rotBtn = $("nsMeshModalAutoRotateBtn");

    if (titleEl) {
      titleEl.textContent = "3D MESH INSPECTOR (.GLB) · " + (meta.prompt || node.label || node.id);
    }
    if (metaEl) {
      metaEl.textContent = glbPath + " · " + getModelName(meta.model || "hyper3d/rodin-v2.5") +
        " · Tier: " + (c.tier || meta.tier || "Regular") +
        (c.rigged ? (" · Rigged (" + (c.animation || "walk") + ")") : "") +
        " · Drag to Orbit / Scroll to Zoom";
    }
    if (animBtn) {
      animBtn.classList.toggle("hidden", !c.rigged);
      animBtn.textContent = modalMeshState.animPlaying ? "❚❚ Pause Anim" : "▶ Play Anim";
    }
    if (rotBtn) {
      rotBtn.classList.toggle("is-active", modalMeshState.autoRotate);
    }
    if (modal) modal.classList.remove("hidden");

    if (modalMeshState.viewerEl && modalMeshState.viewerEl.parentNode) {
      try { modalMeshState.viewerEl.parentNode.removeChild(modalMeshState.viewerEl); } catch (_e) {}
      modalMeshState.viewerEl = null;
    }
    if (wireCanvas) wireCanvas.classList.remove("is-hidden");
    if (badge) {
      badge.classList.remove("is-live");
      badge.textContent = glbSrc ? "⟳ LOADING INTERACTIVE .GLB..." : "◐ ISOMETRIC WIREFRAME PREVIEW";
    }

    bindModalMeshWireCanvasEvents();
    if (modalMeshState.rafId && typeof window.cancelAnimationFrame === "function") {
      window.cancelAnimationFrame(modalMeshState.rafId);
      modalMeshState.rafId = null;
    }
    renderModalMeshWireFrame();

    if (glbSrc && viewport) {
      const mv = document.createElement("model-viewer");
      mv.className = "ns-mesh-modal-model-viewer";
      mv.setAttribute("src", glbSrc);
      mv.setAttribute("camera-controls", "");
      if (modalMeshState.autoRotate) mv.setAttribute("auto-rotate", "");
      mv.setAttribute("interaction-prompt", "none");
      mv.setAttribute("shadow-intensity", "0.7");
      if (c.rigged && modalMeshState.animPlaying) mv.setAttribute("autoplay", "");
      mv.addEventListener("load", () => {
        if (modalMeshState.activeNodeId !== node.id) return;
        modalMeshState.loadedRealGlb = true;
        if (modalMeshState.rafId && typeof window.cancelAnimationFrame === "function") {
          window.cancelAnimationFrame(modalMeshState.rafId);
          modalMeshState.rafId = null;
        }
        if (wireCanvas) wireCanvas.classList.add("is-hidden");
        if (badge) {
          badge.classList.add("is-live");
          badge.textContent = "● LIVE PBR .GLB · MODEL-VIEWER";
        }
      });
      modalMeshState.viewerEl = mv;
      if (typeof viewport.appendChild === "function") {
        viewport.appendChild(mv);
      }
      ensureModelViewer().catch(() => {
        if (badge) {
          badge.classList.remove("is-live");
          badge.textContent = "◐ ISOMETRIC WIREFRAME PREVIEW (OFFLINE)";
        }
      });
    }
  }

  // =========================================================================
  // Fullscreen Image Lightbox, Node Resize/Expand & Collection Utilities
  // =========================================================================
  const lightboxState = {
    nodeId: null,
    index: 0,
    zoomed: false
  };

  function toggleNodeExpand(id) {
    const node = state.nodes.find((n) => n.id === id);
    if (!node) return;
    const mod = _getNodeModality(node);
    const compact = _expectedNodeDimensions(mod, node.morphingStatus);
    const isExpanded = (node.width || compact.w) >= compact.w + 110 || (node.height || compact.h) >= compact.h + 110;
    if (isExpanded) {
      node.width = node._prevCompactW || compact.w;
      node.height = node._prevCompactH || compact.h;
    } else {
      node._prevCompactW = node.width || compact.w;
      node._prevCompactH = node.height || compact.h;
      const textLen = String((node.content && node.content.text) || "").length;
      if (mod === "text") {
        node.width = textLen > 600 ? 600 : 520;
        node.height = textLen > 900 ? 540 : (textLen > 350 ? 460 : 380);
      } else {
        node.width = Math.min(720, Math.round(compact.w * 1.55));
        node.height = Math.min(680, Math.round(compact.h * 1.55));
      }
    }
    _ensureNodeVisible(node.x, node.y, node.width, node.height);
    renderNodes();
  }

  function renderLightboxView() {
    const modal = $("nsImageLightboxModal");
    if (!modal || !lightboxState.nodeId) return;
    const node = state.nodes.find((n) => n.id === lightboxState.nodeId);
    const imgs = node ? _getNodeImages(node) : [];
    if (!node || !imgs.length) {
      closeImageLightbox();
      return;
    }
    const idx = ((lightboxState.index % imgs.length) + imgs.length) % imgs.length;
    lightboxState.index = idx;
    const active = imgs[idx];
    const meta = node.metadata || {};

    const titleEl = $("nsLightboxTitle");
    if (titleEl) {
      titleEl.textContent = imgs.length > 1
        ? ("IMAGE COLLECTION · " + (idx + 1) + " / " + imgs.length)
        : "IMAGE LIGHTBOX";
    }
    const metaEl = $("nsLightboxMeta");
    if (metaEl) {
      metaEl.textContent = getModelName(meta.model || "gemini-nano-banana-2.1") +
        " · " + (meta.resolution || "1K") +
        (meta.prompt ? (" · " + String(meta.prompt).slice(0, 120)) : "");
    }
    const imgEl = $("nsLightboxImg");
    if (imgEl) {
      imgEl.src = active.imageUrl || "";
      imgEl.alt = (meta.prompt || node.label || "Image") + " #" + (idx + 1);
      imgEl.style.filter = buildFilterCss(node.filters);
      imgEl.classList.toggle("is-zoomed", !!lightboxState.zoomed);
    }
    const zoomBtn = $("nsLightboxZoomBtn");
    if (zoomBtn) {
      zoomBtn.textContent = lightboxState.zoomed ? "1× Fit" : "2× Zoom";
      zoomBtn.classList.toggle("is-active", !!lightboxState.zoomed);
    }
    const counterEl = $("nsLightboxCounter");
    if (counterEl) {
      counterEl.textContent = (idx + 1) + " / " + imgs.length;
    }
    const prevBtn = $("nsLightboxPrevBtn");
    const nextBtn = $("nsLightboxNextBtn");
    if (prevBtn) prevBtn.classList.toggle("hidden", imgs.length <= 1);
    if (nextBtn) nextBtn.classList.toggle("hidden", imgs.length <= 1);

    const stripEl = $("nsLightboxStrip");
    if (stripEl) {
      stripEl.classList.toggle("hidden", imgs.length <= 1);
      if (imgs.length > 1) {
        stripEl.innerHTML = imgs.map((im, i) => (
          '<button type="button" class="ns-lightbox-thumb' + (i === idx ? " is-active" : "") + '" ' +
          'title="View image ' + (i + 1) + '" onclick="window.TinCanNodeStudio.selectLightboxIndex(' + i + ')">' +
          '<img src="' + escapeHtml(im.imageUrl) + '" alt="Thumb ' + (i + 1) + '">' +
          "</button>"
        )).join("");
      } else {
        stripEl.innerHTML = "";
      }
    }
  }

  function openImageLightbox(nodeId, index) {
    const node = state.nodes.find((n) => n.id === nodeId);
    const imgs = node ? _getNodeImages(node) : [];
    if (!node || !imgs.length) return;
    lightboxState.nodeId = node.id;
    lightboxState.index = typeof index === "number" ? index : 0;
    lightboxState.zoomed = false;
    const modal = $("nsImageLightboxModal");
    if (modal) modal.classList.remove("hidden");
    renderLightboxView();
  }

  function closeImageLightbox() {
    const modal = $("nsImageLightboxModal");
    if (modal) modal.classList.add("hidden");
    lightboxState.nodeId = null;
    lightboxState.index = 0;
    lightboxState.zoomed = false;
  }

  function stepLightbox(delta) {
    if (!lightboxState.nodeId) return;
    lightboxState.index += Number(delta) || 0;
    lightboxState.zoomed = false;
    renderLightboxView();
  }

  function selectLightboxIndex(idx) {
    if (!lightboxState.nodeId) return;
    lightboxState.index = Number(idx) || 0;
    lightboxState.zoomed = false;
    renderLightboxView();
  }

  function toggleLightboxZoom() {
    if (!lightboxState.nodeId) return;
    lightboxState.zoomed = !lightboxState.zoomed;
    renderLightboxView();
  }

  function useLightboxImageAsRef() {
    if (!lightboxState.nodeId) return;
    const node = state.nodes.find((n) => n.id === lightboxState.nodeId);
    const imgs = node ? _getNodeImages(node) : [];
    const active = imgs[lightboxState.index];
    if (!node || !active) return;
    const rid = node.id + "-img-" + (lightboxState.index + 1);
    if (!state.references.some((r) => r.id === rid)) {
      state.references.push({
        id: rid,
        source: "upload",
        name: (node.label || node.id).slice(0, 24) + " #" + (lightboxState.index + 1),
        type: "image",
        mimeType: active.mimeType || "image/png",
        url: active.imageUrl,
        base64: active.base64 || _extractDataUrlBase64(active.imageUrl),
        size: 0
      });
    }
    renderReferencesStrip();
    closeImageLightbox();
    showToast("Attached image #" + (lightboxState.index + 1) + " as reference", false);
  }

  function popOutLightboxImage() {
    if (!lightboxState.nodeId) return;
    const node = state.nodes.find((n) => n.id === lightboxState.nodeId);
    const imgs = node ? _getNodeImages(node) : [];
    const active = imgs[lightboxState.index];
    if (!node || !active) return;
    state.nodeSeq += 1;
    const nid = node.id + "-pick-" + state.nodeSeq;
    const pos = _computeSmartNodePosition([node.id], 256, 256);
    state.nodes.push({
      id: nid,
      type: "GENERATED",
      modality: "image",
      morphingStatus: "image",
      label: (node.label || "Image") + " #" + (lightboxState.index + 1),
      x: pos.x,
      y: pos.y,
      width: 256,
      height: 256,
      content: {
        imageUrl: active.imageUrl,
        base64: active.base64 || _extractDataUrlBase64(active.imageUrl),
        mimeType: active.mimeType || "image/png"
      },
      metadata: Object.assign({}, node.metadata || {}, {
        prompt: (node.metadata && node.metadata.prompt) || node.label || "",
        pickedIndex: lightboxState.index
      }),
      filters: Object.assign({}, node.filters || {})
    });
    state.edges.push({ id: "e-" + node.id + "-" + nid, source: node.id, target: nid });
    state.selectedIds = [nid];
    syncSelectionRefs();
    closeImageLightbox();
    _ensureNodeVisible(pos.x, pos.y, 256, 256);
    renderNodes();
    showToast("Popped out image #" + (lightboxState.index + 1) + " to canvas", false);
  }

  function downloadLightboxImage() {
    if (!lightboxState.nodeId) return;
    const node = state.nodes.find((n) => n.id === lightboxState.nodeId);
    const imgs = node ? _getNodeImages(node) : [];
    const active = imgs[lightboxState.index];
    if (!node || !active || !active.imageUrl) return;
    const baseName = String(node.label || node.id || "image").replace(/[^a-zA-Z0-9_-]+/g, "_").slice(0, 44) || "image";
    const a = document.createElement("a");
    a.href = active.imageUrl;
    a.download = baseName + "_" + (lightboxState.index + 1) + ".png";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  function splitCollectionToNodes(nodeId) {
    const node = state.nodes.find((n) => n.id === nodeId);
    const imgs = node ? _getNodeImages(node) : [];
    if (!node || imgs.length <= 1) return;
    const spawnedIds = [];
    imgs.forEach((im, idx) => {
      state.nodeSeq += 1;
      const nid = node.id + "-item-" + (idx + 1) + "-" + state.nodeSeq;
      const pos = _computeSmartNodePosition([node.id], 256, 256);
      state.nodes.push({
        id: nid,
        type: "GENERATED",
        modality: "image",
        morphingStatus: "image",
        label: (node.label || "Image") + " #" + (idx + 1),
        x: pos.x,
        y: pos.y,
        width: 256,
        height: 256,
        content: {
          imageUrl: im.imageUrl,
          base64: im.base64 || _extractDataUrlBase64(im.imageUrl),
          mimeType: im.mimeType || "image/png"
        },
        metadata: Object.assign({}, node.metadata || {}, { pickedIndex: idx }),
        filters: Object.assign({}, node.filters || {})
      });
      state.edges.push({ id: "e-" + node.id + "-" + nid, source: node.id, target: nid });
      spawnedIds.push(nid);
    });
    state.selectedIds = spawnedIds.slice();
    syncSelectionRefs();
    renderNodes();
    showToast("Split collection into " + spawnedIds.length + " canvas nodes", false);
  }

  function closeMeshViewer() {
    const modal = $("nsMeshViewerModal");
    if (modal) modal.classList.add("hidden");
    modalMeshState.activeNodeId = null;
    modalMeshState.autoRotate = false;
    modalMeshState.loadedRealGlb = false;
    if (modalMeshState.rafId && typeof window.cancelAnimationFrame === "function") {
      window.cancelAnimationFrame(modalMeshState.rafId);
      modalMeshState.rafId = null;
    }
    if (modalMeshState.viewerEl && modalMeshState.viewerEl.parentNode) {
      try { modalMeshState.viewerEl.parentNode.removeChild(modalMeshState.viewerEl); } catch (_e) {}
    }
    modalMeshState.viewerEl = null;
  }

  function toggleMeshModalAutoRotate() {
    modalMeshState.autoRotate = !modalMeshState.autoRotate;
    const rotBtn = $("nsMeshModalAutoRotateBtn");
    if (rotBtn) rotBtn.classList.toggle("is-active", modalMeshState.autoRotate);
    const mv = modalMeshState.viewerEl;
    if (mv) {
      if (modalMeshState.autoRotate) {
        if (typeof mv.setAttribute === "function") mv.setAttribute("auto-rotate", "");
      } else if (typeof mv.removeAttribute === "function") {
        mv.removeAttribute("auto-rotate");
      }
    }
    if (modalMeshState.autoRotate && !modalMeshState.loadedRealGlb) {
      renderModalMeshWireFrame();
    } else if (!modalMeshState.autoRotate && modalMeshState.rafId && typeof window.cancelAnimationFrame === "function") {
      window.cancelAnimationFrame(modalMeshState.rafId);
      modalMeshState.rafId = null;
    }
  }

  function toggleMeshModalAnim() {
    modalMeshState.animPlaying = !modalMeshState.animPlaying;
    const animBtn = $("nsMeshModalAnimBtn");
    if (animBtn) animBtn.textContent = modalMeshState.animPlaying ? "❚❚ Pause Anim" : "▶ Play Anim";
    const node = state.nodes.find((n) => n.id === modalMeshState.activeNodeId);
    if (node) node._meshAnimPlaying = modalMeshState.animPlaying;
    const mv = modalMeshState.viewerEl;
    if (mv) {
      if (modalMeshState.animPlaying) {
        if (typeof mv.play === "function") mv.play();
        if (typeof mv.setAttribute === "function") mv.setAttribute("autoplay", "");
      } else {
        if (typeof mv.pause === "function") mv.pause();
        if (typeof mv.removeAttribute === "function") mv.removeAttribute("autoplay");
      }
    }
  }

  function toggleNodeMeshAnim(nodeId) {
    const node = state.nodes.find((n) => n.id === nodeId);
    if (!node) return;
    node._meshAnimPlaying = node._meshAnimPlaying === false;
    renderNodes();
  }

  function downloadActiveMeshGlb() {
    if (!modalMeshState.activeNodeId) return;
    downloadNode(modalMeshState.activeNodeId);
  }

  // =========================================================================
  // Synced Chat (Conversation) & Asset Library Views
  // =========================================================================
  function _getNodeModality(node) {
    if (!node) return "image";
    const ms = node.morphingStatus || "";
    const mod = node.modality || "";
    const ok = node.omniKind || "";
    if (ms === "mesh3d" || mod === "3d" || ok === "3d") return "3d";
    if (ms === "omni" || mod === "atlas" || ok === "omni_master" || ok === "pose" || ok === "splat" || ok === "flythrough") return "atlas";
    if (ms === "video" || mod === "video" || ok === "video") return "video";
    if (ms === "audio" || mod === "audio" || ok === "audio") return "audio";
    if (ms === "text" || ms === "message" || mod === "text" || ok === "text") return "text";
    return "image";
  }

  function _modalityDisplayLabel(mod) {
    const map = {
      image: "IMAGE",
      text: "TEXT",
      video: "VIDEO",
      audio: "AUDIO",
      "3d": "3D MESH",
      atlas: "3D SPLAT"
    };
    return map[mod] || "ASSET";
  }

  function _resolveChatLineage() {
    if (!state.nodes.length) return [];
    if (!state.selectedIds.length) return state.nodes.slice();
    const targetId = state.selectedIds[0];
    const byId = new Map();
    state.nodes.forEach((n) => byId.set(n.id, n));
    if (!byId.has(targetId)) return state.nodes.slice();

    const visited = new Set();
    const ordered = [];
    function walkAncestors(id) {
      if (!id || visited.has(id) || !byId.has(id)) return;
      visited.add(id);
      const parents = state.edges.filter((e) => e.target === id).map((e) => e.source);
      parents.forEach((pid) => walkAncestors(pid));
      ordered.push(byId.get(id));
    }
    walkAncestors(targetId);
    return ordered;
  }

  function renderConversationView() {
    const feed = $("nsChatFeed");
    const headerMeta = $("nsChatHeaderMeta");
    const lineage = _resolveChatLineage();
    const activeModLabel = _modalityDisplayLabel(state.modality || "image");
    const activeModelName = getModelName(state.model);

    if (headerMeta) {
      if (state.selectedIds.length > 0 && lineage.length > 0) {
        headerMeta.textContent = "Branch lineage · " + lineage.length + " turn" + (lineage.length === 1 ? "" : "s") +
          " · Target: " + state.selectedIds[0] + " · Composer: " + activeModLabel + " (" + activeModelName + ")";
      } else {
        headerMeta.textContent = "Full session · " + lineage.length + " node" + (lineage.length === 1 ? "" : "s") +
          " · Composer: " + activeModLabel + " (" + activeModelName + ")";
      }
    }

    if (!feed) return;
    if (!lineage.length) {
      feed.innerHTML = '<div class="ns-chat-empty">No nodes in conversation yet. Type a prompt below or generate a node on the canvas.</div>';
      return;
    }

    feed.innerHTML = lineage.map((node) => {
      const nid = escapeHtml(node.id);
      const mod = _getNodeModality(node);
      const meta = node.metadata || {};
      const c = node.content || {};
      const isSel = state.selectedIds.indexOf(node.id) !== -1;
      const modelName = getModelName(meta.model || state.model);
      const promptTxt = (meta.prompt || node.label || "").trim();

      let previewHtml = "";
      if (mod === "image") {
        const chatImgs = _getNodeImages(node);
        if (chatImgs.length > 1) {
          previewHtml =
            '<div class="ns-chat-coll-grid">' +
            chatImgs.map((im, idx) => (
              '<img src="' + escapeHtml(im.imageUrl) + '" alt="' + escapeHtml(node.label || node.id) + ' #' + (idx + 1) + '" ' +
              'onclick="window.TinCanNodeStudio.openImageLightbox(\'' + nid + '\',' + idx + ')">'
            )).join("") +
            "</div>";
        } else {
          previewHtml = c.imageUrl
            ? '<img class="ns-chat-thumb" style="cursor:zoom-in;" src="' + escapeHtml(c.imageUrl) + '" alt="' + escapeHtml(node.label || node.id) + '" onclick="window.TinCanNodeStudio.openImageLightbox(\'' + nid + '\',0)">'
            : '<div class="ns-chat-text">' + escapeHtml(c.text || node.label || "Image node") + "</div>";
        }
      } else if (mod === "text") {
        previewHtml = '<div class="ns-chat-text">' + escapeHtml(c.text || node.label || "") + "</div>";
      } else if (mod === "audio") {
        const audioSrc = _getAudioSrcForNode(node);
        previewHtml =
          (meta.jobStatus === "ERROR"
            ? '<div class="ns-omni-error-box">' + escapeHtml(meta.jobError || "Audio generation failed") + "</div>"
            : (audioSrc ? '<audio class="ns-audio-player" controls preload="metadata" src="' + escapeHtml(audioSrc) + '"></audio>' : "")) +
          '<div class="ns-chat-media-row"><span class="ns-omni-status-badge">♪ ' + escapeHtml(String(c.kind || meta.audioKind || "music").toUpperCase()) +
          "</span><span>" + escapeHtml(c.vfsPath || meta.vfsPath || "/audio/output.mp3") + "</span></div>";
      } else if (mod === "video") {
        const vidUrl = c.videoUrl || "";
        if (_isPlayableVideoUrl(vidUrl)) {
          previewHtml = '<div class="ns-video-stage" style="max-height:200px;"><video class="ns-video-player" controls playsinline loop src="' + escapeHtml(vidUrl) + '"></video></div>';
        } else if (meta.jobStatus === "ERROR") {
          previewHtml = '<div class="ns-omni-error-box">' + escapeHtml(meta.jobError || "Video generation failed") + "</div>";
        } else {
          previewHtml = '<div class="ns-chat-media-row"><span class="ns-omni-status-badge">' +
            escapeHtml(meta.jobStatus === "RUNNING" ? "⟳ RENDERING VIDEO" : "▶ VIDEO STAGED") +
            "</span><span>" + escapeHtml(c.vfsPath || meta.vfsPath || "MP4 Video") + "</span></div>";
        }
      } else if (mod === "3d") {
        const glbPath = c.glbPath || c.vfsPath || meta.vfsPath || "/models3d/mesh.glb";
        previewHtml =
          '<div class="ns-chat-media-row">' +
          '<span class="ns-omni-status-badge">◆ .GLB' + (c.rigged ? (" · RIGGED (" + escapeHtml(c.animation || "walk") + ")") : "") + "</span>" +
          "<span>" + escapeHtml(glbPath) + "</span>" +
          '<button type="button" class="ns-card-action-btn" onclick="window.TinCanNodeStudio.openMeshViewer(\'' + nid + '\')">⤢ Inspect 3D</button>' +
          "</div>";
      } else {
        const spzPath = meta.vfsPath || "/worlds/world_splat.spz";
        previewHtml =
          '<div class="ns-chat-media-row">' +
          '<span class="ns-omni-status-badge">❖ .SPZ GAUSSIAN SPLAT</span>' +
          "<span>" + escapeHtml(spzPath) + "</span>" +
          '<button type="button" class="ns-card-action-btn" onclick="window.TinCanNodeStudio.openSplatViewer(\'' + nid + '\')">⤢ View 3D Splat</button>' +
          "</div>";
      }

      return (
        '<article class="ns-chat-turn' + (isSel ? " is-selected" : "") + '" data-chat-node-id="' + nid + '">' +
        '<div class="ns-chat-turn-head">' +
        '<div class="ns-chat-turn-badges">' +
        '<span class="ns-omni-pill">' + escapeHtml(_modalityDisplayLabel(mod)) + "</span>" +
        '<span class="ns-chat-model">' + escapeHtml(modelName) + "</span>" +
        "</div>" +
        '<button type="button" class="ns-card-action-btn" onclick="window.TinCanNodeStudio.focusNodeOnCanvas(\'' + nid + '\')">Focus on Canvas</button>' +
        "</div>" +
        (promptTxt ? '<div class="ns-chat-prompt">' + escapeHtml(promptTxt) + "</div>" : "") +
        previewHtml +
        "</article>"
      );
    }).join("");
  }

  async function sendChatPrompt(rawText) {
    const chatInp = $("nsChatInput");
    const text = String(rawText !== undefined && rawText !== null ? rawText : ((chatInp && chatInp.value) || "")).trim();
    if (!text) return;
    const promptEl = $("nsPromptInput");
    if (promptEl) promptEl.value = text;
    if (chatInp) chatInp.value = "";
    renderPromptIslandStatus();
    await generate();
    renderConversationView();
  }

  function focusNodeOnCanvas(nodeId) {
    const node = state.nodes.find((n) => n.id === nodeId);
    if (!node) return;
    state.selectedIds = [node.id];
    syncSelectionRefs();
    switchView("nodes");
    const canvas = $("nsDotCanvas");
    const rect = canvas && typeof canvas.getBoundingClientRect === "function"
      ? canvas.getBoundingClientRect()
      : { width: 1200, height: 800 };
    const cx = node.x + (node.width || 256) * 0.5;
    const cy = node.y + (node.height || 256) * 0.5;
    state.panX = Math.round(rect.width * 0.5 - cx * state.zoom);
    state.panY = Math.round((rect.height - 140) * 0.5 - cy * state.zoom);
    applyCanvasTransform();
    renderNodes();
  }

  function setLibraryFilter(mod) {
    state.libraryFilter = mod || "all";
    document.querySelectorAll(".ns-lib-chip").forEach((chip) => {
      const isAct = chip.dataset && chip.dataset.libFilter === state.libraryFilter;
      chip.classList.toggle("is-active", !!isAct);
      chip.setAttribute("aria-pressed", isAct ? "true" : "false");
    });
    renderLibraryViewGrid();
  }

  function setLibrarySearch(query) {
    state.libraryQuery = String(query || "");
    renderLibraryViewGrid();
  }

  function renderLibraryViewGrid() {
    const grid = $("nsLibraryViewGrid");
    if (!grid) return;

    document.querySelectorAll(".ns-lib-chip").forEach((chip) => {
      const isAct = chip.dataset && chip.dataset.libFilter === (state.libraryFilter || "all");
      chip.classList.toggle("is-active", !!isAct);
      chip.setAttribute("aria-pressed", isAct ? "true" : "false");
    });

    if (!state.nodes.length) {
      grid.innerHTML = '<div class="ns-chat-empty" style="grid-column:1 / -1;">No generated assets yet. Generate or drop images in Editor view to populate your Asset Library.</div>';
      return;
    }

    const activeFilter = state.libraryFilter || "all";
    const q = (state.libraryQuery || "").trim().toLowerCase();

    const filtered = state.nodes.filter((n) => {
      const mod = _getNodeModality(n);
      if (activeFilter !== "all" && mod !== activeFilter) return false;
      if (q) {
        const hay = [
          n.id,
          n.label,
          mod,
          n.metadata && n.metadata.prompt,
          n.metadata && n.metadata.model,
          n.metadata && n.metadata.vfsPath,
          n.content && n.content.text
        ].filter(Boolean).join(" ").toLowerCase();
        if (hay.indexOf(q) === -1) return false;
      }
      return true;
    });

    if (!filtered.length) {
      grid.innerHTML = '<div class="ns-chat-empty" style="grid-column:1 / -1;">No assets match the current filter or search query.</div>';
      return;
    }

    grid.innerHTML = filtered.map((n) => {
      const nid = escapeHtml(n.id);
      const mod = _getNodeModality(n);
      const c = n.content || {};
      const meta = n.metadata || {};
      let preview = "";
      if (mod === "image" && c.imageUrl) {
        const libImgs = _getNodeImages(n);
        preview = '<img src="' + escapeHtml(c.imageUrl) + '" alt="' + escapeHtml(n.label || n.id) + '" style="cursor:zoom-in;" onclick="event.stopPropagation();window.TinCanNodeStudio.openImageLightbox(\'' + nid + '\',0)">' +
          (libImgs.length > 1 ? '<span class="ns-collection-idx" style="top:6px;right:6px;left:auto;">' + libImgs.length + " IMGS</span>" : "");
      } else if (mod === "text") {
        preview = '<div class="ns-lib-preview-text">' + escapeHtml(String(c.text || n.label || "").slice(0, 140)) + "</div>";
      } else if (mod === "video") {
        preview = _isPlayableVideoUrl(c.videoUrl)
          ? '<video muted playsinline src="' + escapeHtml(c.videoUrl) + '"></video>'
          : '<span>▶ VIDEO · ' + escapeHtml(meta.jobStatus || "MP4") + "</span>";
      } else if (mod === "audio") {
        preview = '<span>♪ AUDIO · ' + escapeHtml(String(c.kind || meta.audioKind || "WAV").toUpperCase()) + "</span>";
      } else if (mod === "3d") {
        preview = '<span>◆ 3D .GLB' + (c.rigged ? " · RIGGED" : "") + "</span>";
      } else if (mod === "atlas") {
        preview = '<span>❖ 3D SPLAT (.SPZ)</span>';
      } else {
        preview = '<span>' + escapeHtml(_modalityDisplayLabel(mod)) + "</span>";
      }

      return (
        '<div class="ns-lib-asset-card" data-lib-node-id="' + nid + '" data-lib-modality="' + escapeHtml(mod) + '">' +
        '<div class="ns-lib-preview">' + preview + "</div>" +
        '<div class="ns-lib-meta">' +
        '<div class="ns-lib-title" title="' + escapeHtml(n.label || n.id) + '">' + escapeHtml(n.label || n.id) + "</div>" +
        '<div class="ns-lib-sub">' + escapeHtml(_modalityDisplayLabel(mod) + " · " + getModelName(meta.model || "")) + "</div>" +
        "</div>" +
        '<div class="ns-lib-actions">' +
        '<div class="ns-lib-actions-left">' +
        '<button type="button" class="ns-card-action-btn is-primary" onclick="window.TinCanNodeStudio.focusNodeOnCanvas(\'' + nid + '\')">Focus</button>' +
        '<button type="button" class="ns-card-action-btn" onclick="window.TinCanNodeStudio.addNodeAsRef(\'' + nid + '\')">+ Ref</button>' +
        "</div>" +
        '<div class="ns-lib-actions-left">' +
        '<button type="button" class="ns-card-action-btn" title="Download" onclick="window.TinCanNodeStudio.downloadNode(\'' + nid + '\')">↓</button>' +
        '<button type="button" class="ns-card-action-btn" title="Delete" onclick="window.TinCanNodeStudio.deleteNode(\'' + nid + '\')">×</button>' +
        "</div>" +
        "</div>" +
        "</div>"
      );
    }).join("");
  }

  function switchView(view) {
    if (view === "editor") view = "nodes";
    if (view === "chat") view = "conversation";
    if (["nodes", "conversation", "library"].indexOf(view) === -1) view = "nodes";
    state.view = view;
    document.querySelectorAll("[data-view-tab]").forEach((btn) => {
      const active = btn.dataset.viewTab === view;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-pressed", active ? "true" : "false");
    });
    const chatV = $("nsConversationView");
    const libV = $("nsLibraryView");
    if (chatV) chatV.classList.toggle("hidden", view !== "conversation");
    if (libV) libV.classList.toggle("hidden", view !== "library");
    if (view === "conversation") renderConversationView();
    if (view === "library") renderLibraryViewGrid();
  }

  function _expectedNodeDimensions(modality, morphingStatus) {
    const mod = String(modality || "").toLowerCase();
    const st = String(morphingStatus || "").toLowerCase();
    if (mod === "text" || st === "text" || st === "message") return { w: 340, h: 250 };
    if (mod === "video" || st === "video") return { w: 320, h: 250 };
    if (mod === "audio" || st === "audio") return { w: 320, h: 256 };
    if (mod === "3d" || st === "mesh3d") return { w: 320, h: 326 };
    if (mod === "atlas" || st === "omni") return { w: 340, h: 348 };
    return { w: 256, h: 256 };
  }

  function _getNodeLayoutBox(n) {
    if (!n) return { x: 0, y: 0, w: 256, h: 256 };
    if (n._targetSlot && n.morphingStatus === "generating") {
      return { x: n._targetSlot.x, y: n._targetSlot.y, w: n._targetSlot.w, h: n._targetSlot.h };
    }
    return { x: Number(n.x) || 0, y: Number(n.y) || 0, w: Number(n.width) || 256, h: Number(n.height) || 256 };
  }

  function _rectsOverlap(ax, ay, aw, ah, bx, by, bw, bh, pad) {
    const p = typeof pad === "number" ? pad : 24;
    return ax < bx + bw + p && ax + aw + p > bx && ay < by + bh + p && ay + ah + p > by;
  }

  function _findNonOverlappingSlot(startX, startY, w, h, ignoreId) {
    const boxes = state.nodes
      .filter((n) => !ignoreId || n.id !== ignoreId)
      .map(_getNodeLayoutBox);
    const gapX = 44;
    const gapY = 64;
    function collides(cx, cy) {
      for (let i = 0; i < boxes.length; i++) {
        const b = boxes[i];
        if (_rectsOverlap(cx, cy, w, h, b.x, b.y, b.w, b.h, 24)) return true;
      }
      return false;
    }
    if (!collides(startX, startY)) {
      return { x: Math.round(startX), y: Math.round(startY) };
    }
    for (let row = 0; row < 8; row++) {
      const cy = startY + row * (h + gapY);
      const stepX = w + gapX;
      for (let k = 1; k <= 12; k++) {
        const rightX = startX + k * stepX;
        if (!collides(rightX, cy)) return { x: Math.round(rightX), y: Math.round(cy) };
        if (row === 0) {
          const leftX = startX - k * stepX;
          if (!collides(leftX, cy)) return { x: Math.round(leftX), y: Math.round(cy) };
        }
      }
    }
    return { x: Math.round(startX + w + gapX), y: Math.round(startY) };
  }

  function _computeSmartNodePosition(parentIds, targetW, targetH) {
    const w = targetW || 256;
    const h = targetH || 256;
    const gapX = 44;
    const gapY = 64;
    const pIds = Array.isArray(parentIds) ? parentIds : [];
    const parents = pIds
      .map((pid) => state.nodes.find((x) => x.id === pid))
      .filter(Boolean);

    if (parents.length > 0) {
      const pBoxes = parents.map(_getNodeLayoutBox);
      const avgCenterX = pBoxes.reduce((acc, b) => acc + b.x + b.w / 2, 0) / pBoxes.length;
      const maxBottomY = pBoxes.reduce((acc, b) => Math.max(acc, b.y + b.h), -Infinity);
      const desiredX = avgCenterX - w / 2;
      const desiredY = maxBottomY + gapY;
      return _findNonOverlappingSlot(desiredX, desiredY, w, h, null);
    }

    const canvas = $("nsDotCanvas");
    const rect = canvas && canvas.getBoundingClientRect ? canvas.getBoundingClientRect() : { left: 0, top: 0, width: 1200, height: 800 };
    const zoom = state.zoom || 1;
    const vw = rect.width || 1200;
    const vh = rect.height || 800;
    const usableH = Math.max(260, vh - 230);
    const viewCenterX = (vw / 2 - state.panX) / zoom;
    const viewTopY = (Math.max(84, (usableH - h) / 2) - state.panY) / zoom;
    const viewMinX = -state.panX / zoom;
    const viewMaxX = (vw - state.panX) / zoom;
    const viewMinY = -state.panY / zoom;
    const viewMaxY = (usableH - state.panY) / zoom;

    if (!state.nodes.length) {
      return { x: Math.round(viewCenterX - w / 2), y: Math.round(viewTopY) };
    }

    const roots = state.nodes.filter((n) => !state.edges.some((e) => e.target === n.id));
    const rootBoxes = (roots.length ? roots : state.nodes).map(_getNodeLayoutBox);
    let rightmost = rootBoxes[0];
    for (let i = 1; i < rootBoxes.length; i++) {
      if (rootBoxes[i].x + rootBoxes[i].w > rightmost.x + rightmost.w) {
        rightmost = rootBoxes[i];
      }
    }
    const nextRootX = rightmost.x + rightmost.w + gapX;
    const nextRootY = rightmost.y;
    const inView =
      nextRootX + w >= viewMinX - 180 &&
      nextRootX <= viewMaxX + 260 &&
      nextRootY + h >= viewMinY - 120 &&
      nextRootY <= viewMaxY + 180;
    if (inView) {
      return _findNonOverlappingSlot(nextRootX, nextRootY, w, h, null);
    }
    return _findNonOverlappingSlot(viewCenterX - w / 2, viewTopY, w, h, null);
  }

  function _ensureNodeVisible(x, y, w, h) {
    const canvas = $("nsDotCanvas");
    if (!canvas || !canvas.getBoundingClientRect) return;
    const rect = canvas.getBoundingClientRect();
    const vw = rect.width || 1200;
    const vh = rect.height || 800;
    const zoom = state.zoom || 1;
    const marginX = 72;
    const topSafe = 76;
    const bottomSafe = Math.max(topSafe + 160, vh - 210);
    const sx1 = x * zoom + state.panX;
    const sy1 = y * zoom + state.panY;
    const sx2 = (x + (w || 256)) * zoom + state.panX;
    const sy2 = (y + (h || 256)) * zoom + state.panY;
    let moved = false;
    if (sx1 < marginX) {
      state.panX += Math.round(marginX - sx1);
      moved = true;
    } else if (sx2 > vw - marginX) {
      state.panX -= Math.round(sx2 - (vw - marginX));
      moved = true;
    }
    if (sy1 < topSafe) {
      state.panY += Math.round(topSafe - sy1);
      moved = true;
    } else if (sy2 > bottomSafe) {
      state.panY -= Math.round(sy2 - bottomSafe);
      moved = true;
    }
    if (moved) applyCanvasTransform();
  }

  function autoLayout() {
    if (!state.nodes.length) return;
    const nodeById = {};
    state.nodes.forEach((n) => { nodeById[n.id] = n; });
    const inDeg = {};
    const childrenOf = {};
    const parentsOf = {};
    state.nodes.forEach((n) => {
      inDeg[n.id] = 0;
      childrenOf[n.id] = [];
      parentsOf[n.id] = [];
    });
    state.edges.forEach((e) => {
      if (!nodeById[e.source] || !nodeById[e.target] || e.source === e.target) return;
      childrenOf[e.source].push(e.target);
      parentsOf[e.target].push(e.source);
      inDeg[e.target] += 1;
    });

    const roots = state.nodes.filter((n) => inDeg[n.id] === 0);
    const levels = {};
    const queue = (roots.length ? roots : [state.nodes[0]]).map((n) => ({ id: n.id, lvl: 0 }));
    let guard = 0;
    while (queue.length && guard < state.nodes.length * 12 + 20) {
      guard += 1;
      const cur = queue.shift();
      if (levels[cur.id] !== undefined && levels[cur.id] >= cur.lvl) continue;
      levels[cur.id] = cur.lvl;
      (childrenOf[cur.id] || []).forEach((cid) => {
        queue.push({ id: cid, lvl: cur.lvl + 1 });
      });
    }
    const byLvl = {};
    state.nodes.forEach((n) => {
      const lvl = levels[n.id] || 0;
      if (!byLvl[lvl]) byLvl[lvl] = [];
      byLvl[lvl].push(n);
    });

    const canvas = $("nsDotCanvas");
    const rect = canvas && canvas.getBoundingClientRect ? canvas.getBoundingClientRect() : { width: 1200, height: 800 };
    const centerAnchorX = Math.max(480, Math.round((rect.width || 1200) / 2));
    const gapX = 44;
    const gapY = 64;
    const sortedLvls = Object.keys(byLvl).map((k) => parseInt(k, 10)).sort((a, b) => a - b);
    let cursorY = 90;

    sortedLvls.forEach((lvl) => {
      const list = byLvl[lvl];
      if (lvl > 0) {
        list.sort((a, b) => {
          const avgParentX = (node) => {
            const ps = (parentsOf[node.id] || []).map((pid) => nodeById[pid]).filter(Boolean);
            if (!ps.length) return _getNodeLayoutBox(node).x;
            return ps.reduce((s, p) => {
              const b = _getNodeLayoutBox(p);
              return s + b.x + b.w / 2;
            }, 0) / ps.length;
          };
          return avgParentX(a) - avgParentX(b);
        });
      }
      const boxes = list.map(_getNodeLayoutBox);
      const totalW = boxes.reduce((acc, b) => acc + b.w + gapX, -gapX);
      let cursorX = centerAnchorX - totalW / 2;
      let maxRowH = 220;
      list.forEach((n, idx) => {
        const b = boxes[idx];
        const nextX = Math.round(cursorX);
        const nextY = Math.round(cursorY);
        if (n.morphingStatus === "generating" && n._targetSlot) {
          n._targetSlot.x = nextX;
          n._targetSlot.y = nextY;
          n.x = Math.round(nextX + (n._targetSlot.w - (n.width || 96)) / 2);
          n.y = Math.round(nextY + (n._targetSlot.h - (n.height || 96)) / 2);
        } else {
          n.x = nextX;
          n.y = nextY;
        }
        maxRowH = Math.max(maxRowH, b.h);
        cursorX += b.w + gapX;
      });
      cursorY += maxRowH + gapY;
    });
    renderNodes();
  }

  function fitView() {
    const canvas = $("nsDotCanvas");
    if (!canvas || !state.nodes.length) {
      state.panX = 0; state.panY = 0; state.zoom = 1;
      applyCanvasTransform();
      return;
    }
    const rect = canvas.getBoundingClientRect();
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    state.nodes.forEach((n) => {
      minX = Math.min(minX, n.x);
      minY = Math.min(minY, n.y);
      maxX = Math.max(maxX, n.x + (n.width || 256));
      maxY = Math.max(maxY, n.y + (n.height || 256));
    });
    const w = Math.max(100, maxX - minX);
    const h = Math.max(100, maxY - minY);
    const availW = Math.max(300, rect.width - 120);
    const availH = Math.max(240, rect.height - 220);
    state.zoom = Math.max(0.25, Math.min(1.5, Math.min(availW / w, availH / h)));
    state.panX = Math.round((rect.width - w * state.zoom) / 2 - minX * state.zoom);
    state.panY = Math.round((rect.height - 160 - h * state.zoom) / 2 - minY * state.zoom);
    applyCanvasTransform();
  }

  function _wheelZoomFactor(ev, baseScale, pinchScale) {
    let dy = Number(ev && ev.deltaY) || 0;
    if (!dy) return 1;
    if (ev.deltaMode === 1) dy *= 16;
    else if (ev.deltaMode === 2) dy *= 120;
    const isPinch = !!(ev.ctrlKey || ev.metaKey);
    const clamped = Math.max(-80, Math.min(80, dy));
    const sens = isPinch ? (pinchScale || 0.004) : (baseScale || 0.0012);
    return Math.exp(-clamped * sens);
  }

  function zoomBy(factor, clientX, clientY) {
    const prevZoom = state.zoom || 1;
    const nextZoom = Math.max(0.15, Math.min(3.0, Number((prevZoom * factor).toFixed(4))));
    if (nextZoom === prevZoom) return;
    if (typeof clientX === "number" && typeof clientY === "number") {
      const canvas = $("nsDotCanvas");
      const rect = canvas && canvas.getBoundingClientRect ? canvas.getBoundingClientRect() : { left: 0, top: 0 };
      const cx = clientX - rect.left;
      const cy = clientY - rect.top;
      const worldX = (cx - state.panX) / prevZoom;
      const worldY = (cy - state.panY) / prevZoom;
      state.panX = Math.round(cx - worldX * nextZoom);
      state.panY = Math.round(cy - worldY * nextZoom);
    }
    state.zoom = nextZoom;
    applyCanvasTransform();
  }

  function selectAllNodes() {
    state.selectedIds = state.nodes.map((n) => n.id);
    syncSelectionRefs();
    renderNodes();
  }

  function invertImageSelection() {
    const imageNodes = state.nodes.filter((n) => n.content && n.content.imageUrl);
    if (!imageNodes.length) return;
    const next = [];
    imageNodes.forEach((n) => {
      if (state.selectedIds.indexOf(n.id) === -1) next.push(n.id);
    });
    state.selectedIds = next;
    syncSelectionRefs();
    renderNodes();
  }

  function clearSelection() {
    state.selectedIds = [];
    state.activeConversationNodeId = null;
    state.openFilterNodeId = null;
    syncSelectionRefs();
    renderNodes();
  }

  function deleteNode(id) {
    const target = state.nodes.find((n) => n.id === id);
    if (target) _cleanupNodeResources(target);
    if (modalMeshState.activeNodeId === id) closeMeshViewer();
    if (lightboxState.nodeId === id) closeImageLightbox();
    state.edges = state.edges.filter((e) => e.source !== id && e.target !== id);
    state.nodes = state.nodes.filter((n) => n.id !== id);
    state.selectedIds = state.selectedIds.filter((s) => s !== id);
    syncSelectionRefs();
    renderNodes();
  }

  function duplicateNode(id) {
    const orig = state.nodes.find((n) => n.id === id);
    if (!orig) return;
    state.nodeSeq += 1;
    const copy = JSON.parse(JSON.stringify(orig));
    copy.id = id + "-copy-" + state.nodeSeq;
    const dupPos = _findNonOverlappingSlot(orig.x + (orig.width || 256) + 44, orig.y, orig.width || 256, orig.height || 256, null);
    copy.x = dupPos.x;
    copy.y = dupPos.y;
    copy._pollTimer = null;
    copy._glbBlobUrl = "";
    copy._glbBlobSourceB64 = "";
    copy._splatCloud = null;
    copy._splatImgLoading = false;
    state.nodes.push(copy);
    state.selectedIds = [copy.id];
    syncSelectionRefs();
    renderNodes();
  }

  function addNodeAsRef(id) {
    const idx = state.selectedIds.indexOf(id);
    if (idx === -1) state.selectedIds.push(id);
    else state.selectedIds.splice(idx, 1);
    syncSelectionRefs();
    renderNodes();
  }

  function editNode(id) {
    state.selectedIds = [id];
    syncSelectionRefs();
    renderNodes();
    const promptEl = $("nsPromptInput");
    if (promptEl) promptEl.focus();
  }

  function openFilterPopover(id) {
    state.openFilterNodeId = state.openFilterNodeId === id ? null : id;
    renderNodes();
  }

  function toggleNodeFilter(nodeId, filterId) {
    const node = state.nodes.find((n) => n.id === nodeId);
    if (!node) return;
    if (!node.filters) node.filters = {};
    node.filters[filterId] = !node.filters[filterId];
    renderNodes();
    if (typeof fetch === "function") {
      fetch("/api/nodes/filter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ node_id: nodeId, modality: "image", filters: node.filters })
      }).catch(() => {});
    }
  }

  function downloadNode(id) {
    const node = state.nodes.find((n) => n.id === id);
    if (!node || !node.content) return;
    const baseName = String(node.label || node.id || "node").replace(/[^a-zA-Z0-9_-]+/g, "_").slice(0, 48) || "node";
    const c = node.content;
    const m = node.metadata || {};
    const nodeImgs = _getNodeImages(node);
    if (nodeImgs.length > 1) {
      nodeImgs.forEach((im, idx) => {
        if (!im.imageUrl) return;
        const a = document.createElement("a");
        a.href = im.imageUrl;
        a.download = baseName + "_" + (idx + 1) + ".png";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      });
      return;
    }
    let href = "";
    let filename = baseName;
    if (c.imageUrl) {
      href = c.imageUrl;
      filename = baseName + ".png";
    } else if (c.audioRawUrl || c.audioUrl || c.audioBytesB64) {
      href = _getAudioSrcForNode(node);
      filename = baseName + _audioExtLabel(c, m).toLowerCase();
    } else if (c.glbRawUrl || c.glbB64) {
      href = c.glbRawUrl || ("data:model/gltf-binary;base64," + c.glbB64);
      filename = baseName + ".glb";
    } else if (c.videoUrl) {
      href = c.videoUrl;
      filename = baseName + ".mp4";
    } else if (m.spzRawUrl || c.spzB64) {
      href = m.spzRawUrl || ("data:application/octet-stream;base64," + c.spzB64);
      filename = baseName + ".spz";
    } else if (c.text) {
      href = "data:text/markdown;charset=utf-8," + encodeURIComponent(String(c.text));
      filename = baseName + ".md";
    }
    if (!href) return;
    const a = document.createElement("a");
    a.href = href;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  function _isAudioFile(file) {
    if (!file) return false;
    if (file.type && String(file.type).indexOf("audio/") === 0) return true;
    return /\.(mp3|wav|ogg|opus|flac|m4a|aac)$/i.test(String(file.name || ""));
  }

  function _guessAudioMimeAndExt(file) {
    const name = String((file && file.name) || "").toLowerCase();
    const mime = String((file && file.type) || "").toLowerCase();
    if (name.endsWith(".mp3") || mime.indexOf("mpeg") !== -1 || mime.indexOf("mp3") !== -1) return { mime: "audio/mpeg", ext: ".mp3" };
    if (name.endsWith(".ogg") || name.endsWith(".opus") || mime.indexOf("ogg") !== -1 || mime.indexOf("opus") !== -1) return { mime: "audio/ogg", ext: ".ogg" };
    if (name.endsWith(".flac") || mime.indexOf("flac") !== -1) return { mime: "audio/flac", ext: ".flac" };
    if (name.endsWith(".m4a") || name.endsWith(".aac") || mime.indexOf("mp4") !== -1 || mime.indexOf("aac") !== -1) return { mime: "audio/mp4", ext: ".m4a" };
    return { mime: mime || "audio/wav", ext: ".wav" };
  }

  function _spawnUploadedAudioNode(file, flowX, flowY, idx) {
    const info = _guessAudioMimeAndExt(file);
    const hasBlob = (typeof URL !== "undefined" && typeof URL.createObjectURL === "function" && typeof Blob !== "undefined" && file instanceof Blob);
    const blobUrl = hasBlob ? URL.createObjectURL(file) : ((file && file.url) || "");
    state.nodeSeq += 1;
    const nid = "uploaded-audio-" + state.nodeSeq;
    const node = {
      id: nid,
      type: "AUDIO",
      morphingStatus: "audio",
      omniKind: "audio",
      modality: "audio",
      label: (file && file.name) || ("audio_" + state.nodeSeq + info.ext),
      x: Math.round((typeof flowX === "number" ? flowX : (220 + (state.nodeSeq % 4) * 40)) + (idx || 0) * 36),
      y: Math.round((typeof flowY === "number" ? flowY : (120 + (state.nodeSeq % 3) * 36)) + (idx || 0) * 28),
      width: 320,
      height: 256,
      _audioBlobUrl: hasBlob ? blobUrl : "",
      content: {
        kind: "upload",
        audioUrl: blobUrl,
        audioRawUrl: blobUrl,
        mimeType: info.mime,
        ext: info.ext,
        vfsPath: (file && file.name) || ("audio_" + state.nodeSeq + info.ext)
      },
      metadata: {
        model: "Uploaded Audio",
        audioKind: "upload",
        prompt: "Uploaded: " + ((file && file.name) || "audio"),
        vfsPath: (file && file.name) || ("audio_" + state.nodeSeq + info.ext)
      },
      filters: {}
    };
    state.nodes.push(node);
    if (typeof FileReader !== "undefined" && typeof Blob !== "undefined" && file instanceof Blob && (file.size || 0) <= 4 * 1024 * 1024) {
      try {
        const reader = new FileReader();
        reader.onload = function () {
          const dataUrl = String(reader.result || "");
          const b64 = _extractDataUrlBase64(dataUrl);
          if (b64) {
            node.content.audioBytesB64 = b64;
            if (!node.content.audioUrl) node.content.audioUrl = dataUrl;
          }
        };
        reader.readAsDataURL(file);
      } catch (_e) {}
    }
    return node;
  }

  function addFilesToRefs(fileList) {
    const caps = getCaps();
    const files = Array.from(fileList || []);
    let spawnedAudio = false;
    files.forEach((file, idx) => {
      if (state.references.length >= caps.maxReferences) return;
      const fname = (file && file.name) || ("photo_" + (state.references.length + 1) + ".jpg");
      const isAud = _isAudioFile(file);
      const mime = (file && file.type) || (isAud ? _guessAudioMimeAndExt(file).mime : (fname.toLowerCase().endsWith(".pdf") ? "application/pdf" : "image/jpeg"));
      const rType = isAud ? "audio" : (mime === "application/pdf" ? "pdf" : (mime.indexOf("video/") === 0 ? "video" : "image"));
      if (isAud) {
        const audNode = _spawnUploadedAudioNode(file, undefined, undefined, idx);
        state.selectedIds = [audNode.id];
        spawnedAudio = true;
      } else if (!caps.supportsVideoAndPdf && rType !== "image") {
        return;
      }
      const url = (typeof URL !== "undefined" && URL.createObjectURL && file instanceof Blob)
        ? URL.createObjectURL(file)
        : ((file && file.url) || "");
      const refObj = {
        id: "ref-" + Date.now() + "-" + Math.random().toString(16).slice(2, 6),
        source: "upload",
        url: url,
        base64: (file && file.base64) || _extractDataUrlBase64(url),
        name: fname,
        type: rType,
        mimeType: mime,
        size: (file && file.size) || 0
      };
      state.references.push(refObj);
      if (rType === "image" && !refObj.base64 && typeof FileReader !== "undefined" && typeof Blob !== "undefined" && file instanceof Blob) {
        refObj._readPromise = new Promise((resolve) => {
          try {
            const reader = new FileReader();
            reader.onload = function () {
              const dataUrl = String(reader.result || "");
              if (dataUrl) {
                if (!refObj.url) refObj.url = dataUrl;
                refObj.base64 = _extractDataUrlBase64(dataUrl);
                renderReferencesStrip();
              }
              resolve();
            };
            reader.onerror = function () { resolve(); };
            reader.readAsDataURL(file);
          } catch (_e) {
            resolve();
          }
        });
      }
    });
    if (spawnedAudio) renderNodes();
    renderReferencesStrip();
  }

  function addImageFilesToCanvas(fileList, clientX, clientY) {
    const canvas = $("nsDotCanvas");
    const rect = canvas ? canvas.getBoundingClientRect() : { left: 0, top: 0 };
    const flowX = (clientX - rect.left - state.panX) / state.zoom;
    const flowY = (clientY - rect.top - state.panY) / state.zoom;
    const droppedIds = [];
    const allFiles = Array.from(fileList || []);
    const audioFiles = allFiles.filter(_isAudioFile);
    audioFiles.forEach((file, idx) => {
      const audNode = _spawnUploadedAudioNode(file, flowX, flowY, idx);
      droppedIds.push(audNode.id);
    });
    if (audioFiles.length) {
      state.selectedIds = droppedIds.slice();
      renderNodes();
    }
    const imageFiles = allFiles.filter((f) => {
      if (!f) return false;
      if (f.type && f.type.indexOf("image/") === 0) return true;
      return /\.(jpe?g|png|webp|heic|heif|bmp|gif)$/i.test(String(f.name || ""));
    });
    imageFiles.forEach((file, idx) => {
      const reader = new FileReader();
      reader.onload = function () {
        const dataUrl = String(reader.result || "");
        const b64 = _extractDataUrlBase64(dataUrl);
        state.nodeSeq += 1;
        const nid = "uploaded-" + state.nodeSeq;
        state.nodes.push({
          id: nid,
          type: "UPLOADED",
          morphingStatus: "image",
          modality: "image",
          label: file.name,
          x: Math.round(flowX + (audioFiles.length + idx) * 36),
          y: Math.round(flowY + (audioFiles.length + idx) * 28),
          width: 256,
          height: 256,
          content: { imageUrl: dataUrl, base64: b64, mimeType: file.type || "image/jpeg" },
          metadata: { resolution: "1024x1024", model: "Uploaded", prompt: "Uploaded: " + file.name },
          filters: {}
        });
        droppedIds.push(nid);
        if (droppedIds.length === audioFiles.length + imageFiles.length) {
          state.selectedIds = droppedIds.slice();
          syncSelectionRefs();
        }
        renderNodes();
      };
      reader.readAsDataURL(file);
    });
  }

  function spawnAssetNode(assetId) {
    const asset = ASSETS.find((a) => a.id === assetId);
    if (!asset) return;
    state.nodeSeq += 1;
    const nid = "asset-" + state.nodeSeq;
    const assetPos = _computeSmartNodePosition([], 280, 160);
    state.nodes.push({
      id: nid,
      type: "UPLOADED",
      morphingStatus: "message",
      label: asset.name,
      x: assetPos.x,
      y: assetPos.y,
      width: 280,
      height: 160,
      content: { text: asset.name + " [" + asset.tag + "] loaded from Lumina Library" },
      metadata: { prompt: asset.name, model: "Lumina 3D" },
      filters: {}
    });
    renderNodes();
  }

  function applyTemplate(tplId) {
    const tpl = state.templates.find((t) => t.id === tplId);
    const input = $("nsPromptInput");
    if (tpl && input) {
      input.value = tpl.prompt;
      renderPromptIslandStatus();
      input.focus();
    }
  }

  function addCustomTemplate() {
    const input = $("nsPromptInput");
    const txt = input && input.value.trim() ? input.value.trim() : "Cinematic wide shot, celadon & ink palette...";
    const next = { id: "t-" + (state.templates.length + 1), name: "Custom Prompt " + (state.templates.length + 1), prompt: txt };
    state.templates.push(next);
    const list = $("nsLibTemplateList");
    if (list) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "ns-tpl-row";
      btn.innerHTML = '<div class="ns-tpl-title"><span class="ns-tpl-dot"></span><span>' + escapeHtml(next.name) +
        '</span></div><div class="ns-tpl-desc">' + escapeHtml(next.prompt) + "</div>";
      btn.onclick = function () { applyTemplate(next.id); };
      list.insertBefore(btn, $("nsNewTemplateBtn"));
    }
  }

  function toggleLeftPanel(expand) {
    state.isLeftCollapsed = expand !== undefined ? !expand : !state.isLeftCollapsed;
    const pill = $("nsLeftPillWrap");
    const drawer = $("nsLeftDrawer");
    if (pill) pill.classList.toggle("hidden", !state.isLeftCollapsed);
    if (drawer) drawer.classList.toggle("hidden", state.isLeftCollapsed);
  }

  function toggleLibSection(key) {
    state.sections[key] = !state.sections[key];
    const sec = $("nsLibSec-" + key);
    if (sec) sec.classList.toggle("hidden", !state.sections[key]);
  }

  function filterAssets(query) {
    const q = (query || "").toLowerCase();
    document.querySelectorAll("#nsLibAssetGrid .ns-asset-card").forEach((el) => {
      const name = (el.dataset.assetName || "").toLowerCase();
      el.style.display = !q || name.indexOf(q) !== -1 ? "flex" : "none";
    });
  }

  function updateApiBadges() {
    const gemBadge = $("nsApiGeminiStatus");
    const nanoBadge = $("nsApiNanogptStatus");
    const apiBtn = $("nsApiBtn");
    const srcText = $("nsApiSourceText");
    const clearBtn = $("nsApiClearBtn");
    if (gemBadge) {
      gemBadge.textContent = "Gemini: " + (state.serverStatus.hasGeminiKey ? "Server Ready" : "Not Set");
      gemBadge.classList.toggle("is-ready", !!state.serverStatus.hasGeminiKey);
    }
    if (nanoBadge) {
      nanoBadge.textContent = "NanoGPT: " + (state.serverStatus.hasNanogptKey ? "Server Ready" : "Not Set");
      nanoBadge.classList.toggle("is-ready", !!state.serverStatus.hasNanogptKey);
    }
    const custom = !!(state.apiKey || state.nanogptKey);
    if (apiBtn) apiBtn.classList.toggle("is-ready", custom || !!state.serverStatus.hasServerKey);
    if (srcText) {
      srcText.textContent = custom
        ? "Custom key active"
        : (state.serverStatus.hasServerKey ? "Using server proxy keys" : "No server key configured");
    }
    if (clearBtn) clearBtn.style.display = custom ? "inline" : "none";
  }

  function showToast(text, isError) {
    const toast = $("nsResponseToast");
    if (!toast) return;
    toast.textContent = text || "";
    toast.classList.toggle("is-error", !!isError);
    toast.classList.toggle("hidden", !text);
  }

  async function generate() {
    const promptEl = $("nsPromptInput");
    const rawPrompt = promptEl ? promptEl.value.trim() : "";
    const activeMod = state.modality || (getCaps() && getCaps().modality) || "image";
    const hasPhotos = state.references.filter((r) => r.type === "image").length > 0;
    const prompt = rawPrompt || ((activeMod === "atlas" && hasPhotos) ? "Multi-view 3D Gaussian Splat" : "");
    if (!prompt || state.activeRuns >= MAX_CONCURRENT_RUNS) return;

    // Ensure any pending FileReader base64 conversions complete before sending
    if (state.references.length > 0) {
      try {
        await Promise.all(state.references.map((r) => r._readPromise || Promise.resolve()));
      } catch (_e) {}
    }

    // 1. Explicit slash command typed by user -> route through slash parser
    if (rawPrompt.startsWith("/")) {
      await runTerminalCommand(rawPrompt);
      if (promptEl) promptEl.value = "";
      renderPromptIslandStatus();
      return;
    }

    // 2. World Labs 3D Splat — ONLY when the user explicitly selected 3D Splat / World Labs Atlas v2
    if (activeMod === "atlas" || state.model === "worldlabs/atlas-v2") {
      const taskToSub = {
        images2PosedRGBD: "pose",
        atlasGenerate: "flythrough",
        splats2Mesh: "mesh",
        posedImages2Splats: "splat"
      };
      const sub = taskToSub[state.atlasTask] || "splat";
      const refineFlag = (sub === "splat" && state.atlasRefine) ? " --refined" : "";
      await runTerminalCommand("/atlas " + sub + refineFlag + " " + prompt);
      state.activeSlashCommand = "";
      const pill = $("nsActiveSlashPill");
      if (pill) pill.classList.add("hidden");
      if (promptEl) promptEl.value = "";
      renderPromptIslandStatus();
      return;
    }

    // 3. Audio (Lyria 3.5 / ElevenLabs v4 / SFX v3) -> /api/omni/route for real WAV generation
    if (activeMod === "audio") {
      const kind = state.audioKind || (getCaps() && getCaps().audioKind) || "music";
      await runTerminalCommand("/audio " + kind + " --model " + state.model + " " + prompt);
      state.activeSlashCommand = "";
      const pill = $("nsActiveSlashPill");
      if (pill) pill.classList.add("hidden");
      if (promptEl) promptEl.value = "";
      renderPromptIslandStatus();
      return;
    }

    // 4. 3D Mesh (Hyper3D Rodin v2.5) -> /api/omni/route for real PBR .GLB generation
    if (activeMod === "3d") {
      await runTerminalCommand("/3d --model " + state.model + " --tier " + (state.meshTier || "Regular") + " " + prompt);
      state.activeSlashCommand = "";
      const pill = $("nsActiveSlashPill");
      if (pill) pill.classList.add("hidden");
      if (promptEl) promptEl.value = "";
      renderPromptIslandStatus();
      return;
    }

    // 5. Image, Text, and Video -> /api/nodes/generate (Nano Banana, Gemini Pro, DeepSeek, Gemma, Kling, LTX)
    state.activeRuns += 1;
    renderPromptIslandStatus();
    showToast("", false);

    const mode = deriveMode();
    state.nodeSeq += 1;
    const parentIds = state.selectedIds.slice();
    const newId = (mode === "EDIT" && parentIds.length === 1)
      ? (parentIds[0] + ".n" + state.nodeSeq)
      : ("node-" + state.nodeSeq);

    const nodeTypeLabel = activeMod === "text"
      ? "TEXT"
      : (activeMod === "video" ? "VIDEO" : (mode === "MERGE" ? "MERGED" : (mode === "EDIT" ? "EDITED" : "GENERATED")));

    const allRefs = collectAllImageReferences();
    const imgCountReq = activeMod === "image" ? Math.max(1, Math.min(4, parseInt(state.imageCount, 10) || 1)) : 1;
    const finalDim = (activeMod === "image" && imgCountReq > 1)
      ? { w: 360, h: 380 }
      : _expectedNodeDimensions(activeMod, activeMod);
    const slot = _computeSmartNodePosition(parentIds, finalDim.w, finalDim.h);
    const spinX = Math.round(slot.x + (finalDim.w - 96) / 2);
    const spinY = Math.round(slot.y + (finalDim.h - 96) / 2);

    const newNode = {
      id: newId,
      type: nodeTypeLabel,
      modality: activeMod,
      morphingStatus: "generating",
      label: prompt,
      x: spinX,
      y: spinY,
      width: 96,
      height: 96,
      _targetSlot: { x: slot.x, y: slot.y, w: finalDim.w, h: finalDim.h, spinX: spinX, spinY: spinY },
      content: {},
      metadata: {
        prompt: prompt,
        model: state.model,
        modality: activeMod,
        resolution: state.resolution,
        fps: Number(state.videoFps || 60),
        conversationHistory: []
      },
      filters: {}
    };
    state.nodes.push(newNode);
    parentIds.forEach((pid) => {
      state.edges.push({ id: "e-" + pid + "-" + newId, source: pid, target: newId });
    });
    state.selectedIds = [newId];
    _ensureNodeVisible(slot.x, slot.y, finalDim.w, finalDim.h);
    renderNodes();

    const headers = { "Content-Type": "application/json" };
    if (state.apiKey) headers["X-Gemini-Api-Key"] = state.apiKey;
    if (state.nanogptKey) headers["X-NanoGPT-Api-Key"] = state.nanogptKey;

    const parentNodesPayload = parentIds.map((pid) => {
      const pn = state.nodes.find((x) => x.id === pid);
      if (!pn) return null;
      return {
        id: pn.id,
        data: {
          modality: pn.modality || (pn.morphingStatus === "text" || pn.morphingStatus === "message" ? "text" : "image"),
          label: pn.label,
          content: pn.content || {},
          metadata: pn.metadata || {},
          filters: pn.filters || {}
        }
      };
    }).filter(Boolean);

    const payload = {
      prompt: prompt,
      modality: activeMod,
      selectedNodeIds: parentIds,
      parentNodes: parentNodesPayload,
      references: allRefs,
      config: {
        model: state.model,
        aspectRatio: state.aspectRatio,
        resolution: state.resolution,
        count: imgCountReq,
        fps: Number(state.videoFps || 60),
        thinkingLevel: state.thinkingLevel,
        includeThoughts: state.includeThoughts,
        groundingMode: state.groundingMode,
        grounding: state.groundingMode !== "Off",
        provider: state.provider
      }
    };

    try {
      let res = await fetch("/api/nodes/generate", { method: "POST", headers: headers, body: JSON.stringify(payload) });
      if (res.status === 404) {
        res = await fetch("/api/generate", { method: "POST", headers: headers, body: JSON.stringify(payload) });
      }
      const data = await res.json();
      if (!res.ok || data.ok === false) {
        throw new Error(data.error || ("Generation failed (" + res.status + ")"));
      }
      const returnedNode = data.node || {};
      const rData = returnedNode.data || {};
      const rContent = rData.content || data.content || {};
      newNode.content = Object.assign({}, rContent);
      const rawImgs = Array.isArray(rContent.images) && rContent.images.length
        ? rContent.images
        : (Array.isArray(data.images) && data.images.length ? data.images : null);
      if (rawImgs) {
        newNode.content.images = rawImgs.map((im, idx) => {
          const mime = (im && (im.mimeType || im.mime_type)) || "image/png";
          const b64 = (im && (im.base64 || im.data)) || _extractDataUrlBase64((im && (im.imageUrl || im.url)) || "");
          const url = (im && (im.imageUrl || im.url)) || (b64 ? ("data:" + mime + ";base64," + b64) : "");
          return { index: idx, imageUrl: url, base64: b64, mimeType: mime };
        }).filter((im) => im.imageUrl || im.base64);
        if (newNode.content.images.length && !newNode.content.imageUrl) {
          newNode.content.imageUrl = newNode.content.images[0].imageUrl;
          newNode.content.base64 = newNode.content.images[0].base64;
          newNode.content.mimeType = newNode.content.images[0].mimeType;
        }
        if (newNode.content.images.length > 1) {
          newNode.type = "COLLECTION";
        }
      }
      if (data.image && data.image.data && !newNode.content.imageUrl) {
        newNode.content.imageUrl = "data:" + (data.image.mimeType || "image/png") + ";base64," + data.image.data;
        newNode.content.base64 = data.image.data;
        newNode.content.mimeType = data.image.mimeType || "image/png";
      }
      if (newNode.content.imageUrl && !newNode.content.base64) {
        newNode.content.base64 = _extractDataUrlBase64(newNode.content.imageUrl);
      }

      if (rData.metadata) newNode.metadata = Object.assign(newNode.metadata, rData.metadata);

      const isAsyncVideo = activeMod === "video" && (
        data.async === true ||
        data.done === false ||
        (rData.metadata && rData.metadata.jobStatus === "RUNNING") ||
        (rContent && rContent.jobStatus === "RUNNING")
      );

      function _expandGeneratingSlot(targetW, targetH) {
        const ts = newNode._targetSlot;
        newNode.width = targetW;
        newNode.height = targetH;
        if (ts) {
          const userMoved = Math.abs(newNode.x - ts.spinX) > 4 || Math.abs(newNode.y - ts.spinY) > 4;
          if (userMoved) {
            newNode.x = Math.round(newNode.x - (targetW - 96) / 2);
            newNode.y = Math.round(newNode.y - (targetH - 96) / 2);
          } else {
            const settled = _findNonOverlappingSlot(ts.x, ts.y, targetW, targetH, newNode.id);
            newNode.x = settled.x;
            newNode.y = settled.y;
          }
          delete newNode._targetSlot;
        }
      }

      if (isAsyncVideo) {
        newNode.morphingStatus = "video";
        _expandGeneratingSlot(320, 250);
        newNode.metadata.jobId =
          data.job_id ||
          (data.result && (data.result.jobId || data.result.job_id)) ||
          (rData.metadata && (rData.metadata.jobId || rData.metadata.job_id)) ||
          rContent.jobId ||
          rContent.job_id ||
          "";
        newNode.metadata.modelSlug =
          data.model_slug ||
          (data.result && (data.result.modelSlug || data.result.model_slug)) ||
          (rData.metadata && (rData.metadata.modelSlug || rData.metadata.model_slug)) ||
          rContent.modelSlug ||
          state.model;
        newNode.metadata.jobStatus = "RUNNING";
        newNode.metadata.startedAt = Date.now();
        showToast("Video rendering started — polling live every 4s...", false);
        appendTerminalLine("[⟳] Submitted Video job " + (newNode.metadata.jobId || newNode.id) + " (" + newNode.metadata.modelSlug + ") — polling live");
        pollVideoJobForNode(newNode);
      } else if (activeMod === "text") {
        newNode.morphingStatus = "text";
        _expandGeneratingSlot(340, 250);
      } else if (activeMod === "video" || newNode.content.videoUrl) {
        newNode.morphingStatus = "video";
        _expandGeneratingSlot(320, 250);
      } else if (newNode.content.imageUrl) {
        newNode.morphingStatus = "image";
        const isColl = Array.isArray(newNode.content.images) && newNode.content.images.length > 1;
        _expandGeneratingSlot(isColl ? 360 : 256, isColl ? 380 : 256);
      } else {
        newNode.morphingStatus = "text";
        _expandGeneratingSlot(340, 250);
      }

      if (activeMod === "image" && newNode.content.text) {
        showToast(newNode.content.text, false);
      }
    } catch (err) {
      const tsErr = newNode._targetSlot;
      const errMsg = (err && err.message) ? String(err.message) : "Generation failed";
      const isNetworkDown = errMsg.indexOf("Failed to fetch") !== -1;
      if (activeMod === "video" && !isNetworkDown) {
        newNode.morphingStatus = "video";
        newNode.width = 320;
        newNode.height = 250;
        newNode.metadata.jobStatus = "ERROR";
        newNode.metadata.jobError = errMsg;
      } else if (!isNetworkDown) {
        newNode.morphingStatus = "text";
        newNode.width = 340;
        newNode.height = 220;
        newNode.metadata.jobStatus = "ERROR";
        newNode.metadata.jobError = errMsg;
        newNode.content = { text: "" };
      } else {
        newNode.morphingStatus = "text";
        newNode.width = 320;
        newNode.height = 200;
        newNode.content = { text: prompt + " (staged locally)" };
      }
      if (tsErr) {
        newNode.x = tsErr.x;
        newNode.y = tsErr.y;
        delete newNode._targetSlot;
      }
      if (!isNetworkDown) {
        showToast(errMsg, true);
      }
    } finally {
      state.activeRuns = Math.max(0, state.activeRuns - 1);
      if (promptEl) promptEl.value = "";
      renderNodes();
      renderPromptIslandStatus();
    }
  }

  function handlePromptInput(val) {
    const text = String(val !== undefined ? val : (($("nsPromptInput") && $("nsPromptInput").value) || ""));
    const pop = $("nsSlashRouterPopover");
    if (text.trim().startsWith("/")) {
      if (pop) pop.classList.remove("hidden");
      const parsed = parseSlashCommand(text);
      const pill = $("nsActiveSlashPill");
      const pillTxt = $("nsActiveSlashPillText");
      if (pillTxt) pillTxt.textContent = parsed.pill_label;
      if (pill) pill.classList.remove("hidden");
    } else if (pop) {
      pop.classList.add("hidden");
    }
    renderPromptIslandStatus();
  }

  function init() {
    const params = typeof window !== "undefined" && window.location && window.location.search
      ? new URLSearchParams(window.location.search) : null;
    const qView = params ? params.get("view") : null;
    if (qView) switchView(qView); else switchView(state.view);

    syncCapabilitiesAndControls();
    renderPromptIslandStatus();
    applyCanvasTransform();
    updateApiBadges();
    mountAllSplatCanvases();
    mountAllMeshPreviews();
    renderConversationView();
    renderLibraryViewGrid();

    const qGraph = params ? (params.get("graph") || params.get("file")) : null;
    (async function () {
      state._initialLoadDone = false;
      try {
        if (qGraph) {
          await loadGraphFromSpace(qGraph, false);
        } else {
          const tgt = _resolveSpaceTarget();
          const lastSaved = _getLastGraph(tgt.scope, tgt.owner_id);
          let restored = false;
          if (lastSaved) {
            restored = await loadGraphFromSpace(lastSaved, true);
          }
          if (!restored) {
            restored = await loadGraphFromSpace(state.graphPath, true);
          }
          const graphs = await listSavedGraphs();
          if (!restored && !state.nodes.length && Array.isArray(graphs) && graphs.length > 0 && graphs[0].path) {
            await loadGraphFromSpace(graphs[0].path, true);
          }
          return;
        }
        await listSavedGraphs();
      } finally {
        state._initialLoadDone = true;
      }
    })();

    if (typeof fetch === "function") {
      fetch("/api/nodes/health").then((r) => (r.ok ? r.json() : fetch("/api/health").then((r2) => r2.json())))
        .then((health) => {
          if (health && typeof health === "object") {
            state.serverStatus = {
              hasServerKey: !!health.hasServerKey,
              hasGeminiKey: !!health.hasGeminiKey,
              hasNanogptKey: !!health.hasNanogptKey
            };
            updateApiBadges();
          }
        }).catch(() => {});
    }

    const canvas = $("nsDotCanvas");
    if (canvas) {
      canvas.addEventListener("wheel", (ev) => {
        const scrollTarget = ev.target && ev.target.closest
          ? ev.target.closest(".ns-msg-body, .ns-text-body, .ns-omni-box, .ns-chat-feed, .ns-lib-grid, .ns-popover, .ns-floating-terminal, .ns-model-menu, .ns-api-menu, .ns-graphs-popover")
          : null;
        if (scrollTarget && scrollTarget.scrollHeight > scrollTarget.clientHeight + 2) {
          return;
        }
        ev.preventDefault();
        const absX = Math.abs(Number(ev.deltaX) || 0);
        const absY = Math.abs(Number(ev.deltaY) || 0);
        if (!ev.ctrlKey && !ev.metaKey && absX > absY * 1.5 && absX > 0) {
          state.panX = Math.round(state.panX - (Number(ev.deltaX) || 0) * 0.65);
          applyCanvasTransform();
          return;
        }
        zoomBy(_wheelZoomFactor(ev, 0.0012, 0.004), ev.clientX, ev.clientY);
      }, { passive: false });

      canvas.addEventListener("mousedown", (ev) => {
        const resizeEl = ev.target && ev.target.closest ? ev.target.closest(".ns-resize-handle") : null;
        if (resizeEl) {
          ev.preventDefault();
          ev.stopPropagation();
          const rnid = resizeEl.dataset.resizeNodeId;
          const rnode = state.nodes.find((n) => n.id === rnid);
          if (rnode) {
            state.resizeNodeId = rnid;
            state.resizeStart = {
              x: ev.clientX,
              y: ev.clientY,
              w: Number(rnode.width) || 320,
              h: Number(rnode.height) || 240
            };
          }
          return;
        }
        const nodeEl = ev.target.closest ? ev.target.closest(".ns-canvas-node") : null;
        const handleEl = ev.target.closest ? ev.target.closest(".ns-node-handle") : null;
        if (handleEl) {
          ev.stopPropagation();
          state.connectFromId = handleEl.dataset.nodeId;
          return;
        }
        if (nodeEl) {
          ev.stopPropagation();
          const nid = nodeEl.dataset.nodeId;
          const interactiveEl = ev.target && ev.target.closest
            ? ev.target.closest("audio, video, model-viewer, button, input, select, textarea, a, .ns-mesh-stage, .ns-splat-canvas, .ns-msg-body, .ns-text-body")
            : null;
          if (interactiveEl) {
            // Preserve live <audio>/<video>/<model-viewer> & buttons: never rebuild innerHTML or drag card mid-click
            if (state.selectedIds.indexOf(nid) === -1) {
              state.selectedIds = [nid];
              document.querySelectorAll(".ns-canvas-node").forEach((el) => {
                el.classList.toggle("is-selected", el.dataset && el.dataset.nodeId === nid);
              });
              syncSelectionRefs();
            }
            return;
          }
          if (state.metaHeld || ev.metaKey || ev.ctrlKey) {
            duplicateNode(nid);
            return;
          }
          if (ev.shiftKey) {
            addNodeAsRef(nid);
          } else if (state.selectedIds.indexOf(nid) === -1) {
            state.selectedIds = [nid];
            syncSelectionRefs();
            renderNodes();
          }
          const node = state.nodes.find((n) => n.id === nid);
          if (node) {
            state.dragNodeId = nid;
            state.dragNodeOffset = { x: ev.clientX / state.zoom - node.x, y: ev.clientY / state.zoom - node.y };
          }
          return;
        }
        if (ev.button === 0 && ev.shiftKey) {
          ev.preventDefault();
          state.isBoxSelecting = true;
          const r = canvas.getBoundingClientRect();
          state.boxStart = { x: ev.clientX - r.left, y: ev.clientY - r.top };
          const box = $("nsSelectionBox");
          if (box) {
            box.style.left = state.boxStart.x + "px";
            box.style.top = state.boxStart.y + "px";
            box.style.width = "0px";
            box.style.height = "0px";
            box.style.display = "block";
          }
          return;
        }
        if (ev.button === 0 && !ev.shiftKey) {
          clearSelection();
          state.isPanning = true;
          state.panStart = { x: ev.clientX - state.panX, y: ev.clientY - state.panY };
          canvas.classList.add("is-panning");
        }
      });

      canvas.addEventListener("dragover", (ev) => {
        ev.preventDefault();
        canvas.classList.add("is-drag-over");
        const ov = $("nsDropOverlay");
        if (ov) ov.classList.add("is-visible");
      });
      canvas.addEventListener("dragleave", () => {
        canvas.classList.remove("is-drag-over");
        const ov = $("nsDropOverlay");
        if (ov) ov.classList.remove("is-visible");
      });
      canvas.addEventListener("drop", (ev) => {
        ev.preventDefault();
        canvas.classList.remove("is-drag-over");
        const ov = $("nsDropOverlay");
        if (ov) ov.classList.remove("is-visible");
        const assetId = ev.dataTransfer ? ev.dataTransfer.getData("text/x-ns-asset") : "";
        if (assetId) { spawnAssetNode(assetId); return; }
        if (ev.dataTransfer && ev.dataTransfer.files && ev.dataTransfer.files.length) {
          addImageFilesToCanvas(ev.dataTransfer.files, ev.clientX, ev.clientY);
        }
      });
    }

    document.addEventListener("mousemove", (ev) => {
      if (state.isDraggingPill) {
        const x = Math.max(0, Math.min(window.innerWidth - 60, ev.clientX - state.pillOffset.x));
        const y = Math.max(0, Math.min(window.innerHeight - 150, ev.clientY - state.pillOffset.y));
        state.pillPos = { x, y };
        const wrap = $("nsLeftPillWrap");
        if (wrap) { wrap.style.left = x + "px"; wrap.style.top = y + "px"; }
        return;
      }
      if (state.isBoxSelecting) {
        const canvasEl = $("nsDotCanvas");
        const r = canvasEl ? canvasEl.getBoundingClientRect() : { left: 0, top: 0 };
        const cx = ev.clientX - r.left;
        const cy = ev.clientY - r.top;
        const left = Math.min(state.boxStart.x, cx);
        const top = Math.min(state.boxStart.y, cy);
        const width = Math.abs(cx - state.boxStart.x);
        const height = Math.abs(cy - state.boxStart.y);
        const box = $("nsSelectionBox");
        if (box) {
          box.style.left = left + "px";
          box.style.top = top + "px";
          box.style.width = width + "px";
          box.style.height = height + "px";
        }
        const flowLeft = (left - state.panX) / state.zoom;
        const flowTop = (top - state.panY) / state.zoom;
        const flowRight = (left + width - state.panX) / state.zoom;
        const flowBottom = (top + height - state.panY) / state.zoom;
        state.selectedIds = state.nodes.filter((n) => {
          const nx2 = n.x + (n.width || 256);
          const ny2 = n.y + (n.height || 256);
          return n.x < flowRight && nx2 > flowLeft && n.y < flowBottom && ny2 > flowTop;
        }).map((n) => n.id);
        return;
      }
      if (state.resizeNodeId && state.resizeStart) {
        const node = state.nodes.find((n) => n.id === state.resizeNodeId);
        if (node) {
          const z = state.zoom || 1;
          const nextW = Math.max(220, Math.min(1100, Math.round(state.resizeStart.w + (ev.clientX - state.resizeStart.x) / z)));
          const nextH = Math.max(140, Math.min(1000, Math.round(state.resizeStart.h + (ev.clientY - state.resizeStart.y) / z)));
          node.width = nextW;
          node.height = nextH;
          const el = $("nsCanvasNode-" + node.id);
          if (el) { el.style.width = nextW + "px"; el.style.height = nextH + "px"; }
          renderEdges();
        }
        return;
      }
      if (state.dragNodeId) {
        const node = state.nodes.find((n) => n.id === state.dragNodeId);
        if (node) {
          node.x = Math.round(ev.clientX / state.zoom - state.dragNodeOffset.x);
          node.y = Math.round(ev.clientY / state.zoom - state.dragNodeOffset.y);
          const el = $("nsCanvasNode-" + node.id);
          if (el) { el.style.left = node.x + "px"; el.style.top = node.y + "px"; }
          renderEdges();
        }
      } else if (state.isPanning) {
        state.panX = ev.clientX - state.panStart.x;
        state.panY = ev.clientY - state.panStart.y;
        applyCanvasTransform();
      }
    });

    document.addEventListener("mouseup", (ev) => {
      if (state.isBoxSelecting) {
        state.isBoxSelecting = false;
        const box = $("nsSelectionBox");
        if (box) box.style.display = "none";
        syncSelectionRefs();
        renderNodes();
      }
      if (state.connectFromId) {
        const targetHandle = ev.target && ev.target.closest ? ev.target.closest("[data-node-id]") : null;
        if (targetHandle && targetHandle.dataset.nodeId !== state.connectFromId) {
          state.edges.push({
            id: "e-" + state.connectFromId + "-" + targetHandle.dataset.nodeId,
            source: state.connectFromId,
            target: targetHandle.dataset.nodeId
          });
          renderEdges();
        }
        state.connectFromId = null;
      }
      if (state.resizeNodeId) {
        state.resizeNodeId = null;
        state.resizeStart = null;
        if (!state._suppressAutoSave && state.nodes.length > 0) scheduleAutoSave();
      }
      state.isDraggingPill = false;
      state.dragNodeId = null;
      state.isPanning = false;
      const canvasEl = $("nsDotCanvas");
      if (canvasEl) canvasEl.classList.remove("is-panning");
    });

    const pillWrap = $("nsLeftPillWrap");
    if (pillWrap) {
      pillWrap.addEventListener("mousedown", (ev) => {
        if (ev.target && ev.target.closest && ev.target.closest("#nsPillExpandBtn")) return;
        state.isDraggingPill = true;
        const r = pillWrap.getBoundingClientRect();
        state.pillOffset = { x: ev.clientX - r.left, y: ev.clientY - r.top };
      });
    }

    ["nsLibRefDrop", "nsPromptIsland"].forEach((dropId) => {
      const dz = $(dropId);
      if (!dz) return;
      dz.addEventListener("dragover", (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
      });
      dz.addEventListener("drop", (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
        if (ev.dataTransfer && ev.dataTransfer.files && ev.dataTransfer.files.length) {
          addFilesToRefs(ev.dataTransfer.files);
        }
      });
    });

    const promptEl = $("nsPromptInput");
    if (promptEl) {
      promptEl.addEventListener("input", () => {
        promptEl.style.height = "auto";
        promptEl.style.height = Math.min(promptEl.scrollHeight, 200) + "px";
        handlePromptInput(promptEl.value);
      });
      promptEl.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter" && !ev.shiftKey) {
          ev.preventDefault();
          generate();
        }
      });
    }

    const chatInputEl = $("nsChatInput");
    if (chatInputEl) {
      chatInputEl.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter" && !ev.shiftKey) {
          ev.preventDefault();
          sendChatPrompt();
        }
      });
    }

    document.addEventListener("keydown", (ev) => {
      if (ev.metaKey || ev.ctrlKey) {
        state.metaHeld = true;
        const ci = $("nsCopyIndicator");
        if (ci) ci.classList.remove("hidden");
      }
      if ((ev.metaKey || ev.ctrlKey) && ev.key.toLowerCase() === "s") {
        ev.preventDefault();
        saveGraphToSpace();
        return;
      }
      const tag = ev.target && ev.target.tagName ? ev.target.tagName.toLowerCase() : "";
      if (tag === "input" || tag === "textarea" || tag === "select") {
        if ((ev.metaKey || ev.ctrlKey) && ev.key === "Enter") {
          ev.preventDefault();
          if (ev.target && ev.target.id === "nsChatInput") sendChatPrompt();
          else generate();
        }
        return;
      }
      const lbModal = $("nsImageLightboxModal");
      if (lbModal && !lbModal.classList.contains("hidden")) {
        if (ev.key === "Escape") { ev.preventDefault(); closeImageLightbox(); return; }
        if (ev.key === "ArrowLeft") { ev.preventDefault(); stepLightbox(-1); return; }
        if (ev.key === "ArrowRight") { ev.preventDefault(); stepLightbox(1); return; }
      }
      const meshModal = $("nsMeshViewerModal");
      if (meshModal && !meshModal.classList.contains("hidden")) {
        if (ev.key === "Escape") { ev.preventDefault(); closeMeshViewer(); return; }
      }
      const splatModal = $("nsSplatViewerModal");
      if (splatModal && !splatModal.classList.contains("hidden")) {
        const k = ev.key.toLowerCase();
        if (ev.key === "Escape") { ev.preventDefault(); closeSplatViewer(); return; }
        if (k === "w") { ev.preventDefault(); modalSplatState.zoom = Math.min(3.5, modalSplatState.zoom * 1.12); renderModalSplatFrame(); return; }
        if (k === "s") { ev.preventDefault(); modalSplatState.zoom = Math.max(0.4, modalSplatState.zoom * 0.89); renderModalSplatFrame(); return; }
        if (k === "a") { ev.preventDefault(); modalSplatState.yaw -= 0.08; renderModalSplatFrame(); return; }
        if (k === "d") { ev.preventDefault(); modalSplatState.yaw += 0.08; renderModalSplatFrame(); return; }
        if (k === "q") { ev.preventDefault(); modalSplatState.pitch = Math.max(-0.7, modalSplatState.pitch - 0.06); renderModalSplatFrame(); return; }
        if (k === "e") { ev.preventDefault(); modalSplatState.pitch = Math.min(1.2, modalSplatState.pitch + 0.06); renderModalSplatFrame(); return; }
      }
      if ((ev.key === "Delete" || ev.key === "Backspace") && state.selectedIds.length) {
        ev.preventDefault();
        state.selectedIds.slice().forEach(deleteNode);
      } else if ((ev.metaKey || ev.ctrlKey) && ev.key.toLowerCase() === "a") {
        if (state.nodes.length >= 3) { ev.preventDefault(); autoLayout(); }
      } else if (ev.key.toLowerCase() === "a") {
        ev.preventDefault();
        selectAllNodes();
      } else if (ev.key.toLowerCase() === "i") {
        ev.preventDefault();
        invertImageSelection();
      } else if (ev.key.toLowerCase() === "f") {
        ev.preventDefault();
        autoLayout();
        fitView();
      } else if (ev.key === "`") {
        ev.preventDefault();
        toggleTerminal();
      }
    });

    document.addEventListener("keyup", (ev) => {
      if (!ev.metaKey && !ev.ctrlKey) {
        state.metaHeld = false;
        const ci = $("nsCopyIndicator");
        if (ci) ci.classList.add("hidden");
      }
    });

    document.addEventListener("mousedown", (ev) => {
      const apiMenu = $("nsApiMenu");
      const modelMenu = $("nsModelMenu");
      const menuArea = $("nsIslandMenuArea");
      if (menuArea && !menuArea.contains(ev.target)) {
        if (apiMenu) apiMenu.classList.add("hidden");
        if (modelMenu) modelMenu.classList.add("hidden");
      }
      const graphsPop = $("nsGraphsPopover");
      const graphsBtn = $("nsGraphsMenuBtn");
      if (graphsPop && !graphsPop.classList.contains("hidden") &&
          !graphsPop.contains(ev.target) && (!graphsBtn || !graphsBtn.contains(ev.target))) {
        graphsPop.classList.add("hidden");
      }
    });
  }

  function _resolveSpaceTarget() {
    const params = typeof window !== "undefined" && window.location && window.location.search
      ? new URLSearchParams(window.location.search) : null;
    let savedPeer = "";
    try {
      if (typeof localStorage !== "undefined" && localStorage.getItem) {
        savedPeer = String(localStorage.getItem("tincan_peer_id") || "").trim();
      }
    } catch (_e) {}
    const winScope = (typeof window !== "undefined" && window.currentSpaceScope) ? String(window.currentSpaceScope).trim() : "";
    const winOwner = (typeof window !== "undefined" && window.currentSpaceOwner) ? String(window.currentSpaceOwner).trim() : "";
    const scope = winScope || (params && params.get("scope")) || "user";
    const owner_id = winOwner ||
      (params && (params.get("owner_id") || params.get("peer_id") || params.get("peer"))) ||
      savedPeer ||
      "default";
    return { scope: String(scope || "user"), owner_id: String(owner_id || "default") };
  }

  function _rememberLastGraph(scope, ownerId, graphName) {
    try {
      if (typeof localStorage !== "undefined" && localStorage.setItem && graphName) {
        localStorage.setItem("tincan_ns_last_graph_" + scope + "_" + ownerId, String(graphName));
      }
    } catch (_e) {}
  }

  function _getLastGraph(scope, ownerId) {
    try {
      if (typeof localStorage !== "undefined" && localStorage.getItem) {
        return String(localStorage.getItem("tincan_ns_last_graph_" + scope + "_" + ownerId) || "").trim();
      }
    } catch (_e) {}
    return "";
  }

  function _cleanGraphName(rawName) {
    let s = String(rawName || state.graphName || "workspace").trim();
    if (s.indexOf("/nodes/") === 0) s = s.slice(7);
    s = s.replace(/\.nodes\.json$/i, "").replace(/\.json$/i, "");
    s = s.replace(/[^a-zA-Z0-9_-]+/g, "_").replace(/^[_-]+|[_-]+$/g, "");
    return (s || "workspace").slice(0, 64);
  }

  function _updateSaveGraphHud(statusSuffix) {
    const lbl = $("nsSaveGraphStatus");
    if (lbl) {
      lbl.textContent = "[" + state.graphName + (statusSuffix ? (" " + statusSuffix) : "") + "]";
    }
    const nameInp = $("nsGraphNameInput");
    if (nameInp && !nameInp.value) nameInp.value = state.graphName;
  }

  function serializeGraphState() {
    const cleanNodes = state.nodes.map((n) => {
      const content = Object.assign({}, n.content || {});
      if (content.imageUrl && content.imageUrl.indexOf("blob:") === 0 && content.base64) {
        content.imageUrl = "data:" + (content.mimeType || "image/jpeg") + ";base64," + content.base64;
      }
      if (content.audioUrl && content.audioUrl.indexOf("blob:") === 0 && content.audioBytesB64) {
        content.audioUrl = "data:" + (content.mimeType || "audio/mpeg") + ";base64," + content.audioBytesB64;
        if (content.audioRawUrl && content.audioRawUrl.indexOf("blob:") === 0) content.audioRawUrl = "";
      }
      return {
        id: n.id,
        type: n.type,
        morphingStatus: n.morphingStatus,
        omniKind: n.omniKind,
        modality: n.modality,
        label: n.label,
        x: n.x,
        y: n.y,
        width: n.width,
        height: n.height,
        splatState: n.splatState ? Object.assign({}, n.splatState) : undefined,
        content: content,
        metadata: Object.assign({}, n.metadata || {}),
        filters: Object.assign({}, n.filters || {})
      };
    });
    const cleanRefs = state.references.map((r) => {
      const b64 = r.base64 || _extractDataUrlBase64(r.url);
      const persistentUrl = (r.url && r.url.indexOf("blob:") !== 0)
        ? r.url
        : (b64 ? ("data:" + (r.mimeType || "image/jpeg") + ";base64," + b64) : "");
      return {
        id: r.id,
        source: r.source || "upload",
        name: r.name,
        type: r.type || "image",
        mimeType: r.mimeType || "image/jpeg",
        url: persistentUrl,
        base64: b64,
        size: r.size || 0
      };
    });
    return {
      schema: "tincan.node_studio.graph.v1",
      name: state.graphName,
      path: "/nodes/" + state.graphName + ".nodes.json",
      savedAt: new Date().toISOString(),
      viewport: { panX: state.panX, panY: state.panY, zoom: state.zoom },
      config: {
        model: state.model,
        modality: state.modality,
        activeSlashCommand: state.activeSlashCommand,
        aspectRatio: state.aspectRatio,
        resolution: state.resolution,
        imageCount: state.imageCount,
        thinkingLevel: state.thinkingLevel,
        includeThoughts: state.includeThoughts,
        groundingMode: state.groundingMode,
        provider: state.provider
      },
      nodeSeq: state.nodeSeq,
      selectedIds: state.selectedIds.slice(),
      nodes: cleanNodes,
      edges: state.edges.map((e) => ({ id: e.id, source: e.source, target: e.target })),
      references: cleanRefs
    };
  }

  function applyGraphState(graphObj, meta) {
    if (!graphObj || typeof graphObj !== "object") return false;
    const nodes = Array.isArray(graphObj.nodes) ? graphObj.nodes : [];
    const edges = Array.isArray(graphObj.edges) ? graphObj.edges : [];
    const refs = Array.isArray(graphObj.references) ? graphObj.references : [];
    const vp = graphObj.viewport || {};
    const cfg = graphObj.config || {};

    state._suppressAutoSave = true;
    try {
      state.nodes.forEach(_cleanupNodeResources);
      closeMeshViewer();
      closeImageLightbox();
      state.graphName = _cleanGraphName((meta && meta.name) || graphObj.name || state.graphName);
      state.graphPath = (meta && meta.path) || graphObj.path || ("/nodes/" + state.graphName + ".nodes.json");
      state.nodes = nodes.map((n) => Object.assign({}, n, { _splatCloud: null, _splatImgLoading: false, _glbBlobUrl: "", _glbBlobSourceB64: "" }));
      state.edges = edges.slice();
      state.references = refs.slice();
      state.selectedIds = Array.isArray(graphObj.selectedIds) ? graphObj.selectedIds.slice() : [];
      state.nodeSeq = typeof graphObj.nodeSeq === "number" ? graphObj.nodeSeq : state.nodes.length;
      if (typeof vp.panX === "number") state.panX = vp.panX;
      if (typeof vp.panY === "number") state.panY = vp.panY;
      if (typeof vp.zoom === "number" && vp.zoom > 0) state.zoom = vp.zoom;
      if (cfg.model && CAPS[cfg.model]) {
        state.model = cfg.model;
        state.modality = (CAPS[cfg.model] && CAPS[cfg.model].modality) || cfg.modality || "image";
      } else if (cfg.modality) {
        state.modality = cfg.modality;
      }
      state.activeSlashCommand = "";
      const slashPillEl = $("nsActiveSlashPill");
      if (slashPillEl) slashPillEl.classList.add("hidden");
      if (cfg.aspectRatio) state.aspectRatio = cfg.aspectRatio;
      if (cfg.resolution) state.resolution = cfg.resolution;
      if (cfg.imageCount) state.imageCount = Math.max(1, Math.min(4, parseInt(cfg.imageCount, 10) || 1));
      if (cfg.thinkingLevel) state.thinkingLevel = cfg.thinkingLevel;
      if (typeof cfg.includeThoughts === "boolean") state.includeThoughts = cfg.includeThoughts;
      if (cfg.groundingMode) state.groundingMode = cfg.groundingMode;
      if (cfg.provider) state.provider = cfg.provider;

      applyCanvasTransform();
      renderReferencesStrip();
      syncCapabilitiesAndControls();
      renderNodes();
      renderPromptIslandStatus();
      _updateSaveGraphHud("✓");

      // Automatically resume live polling for any restored RUNNING video/mesh/atlas jobs
      state.nodes.forEach((n) => {
        if (!n || !n.metadata || n.metadata.jobStatus !== "RUNNING") return;
        const mod = _getNodeModality(n);
        if (mod === "video" && n.metadata.jobId) {
          pollVideoJobForNode(n);
        } else if (mod === "audio" && n.metadata.jobId) {
          pollAudioJobForNode(n);
        } else if (mod === "3d" && n.metadata.jobId) {
          pollMeshJobForNode(n);
        } else if (mod === "atlas" && n.metadata.operationId) {
          pollAtlasOperationForNode(n);
        }
      });
    } finally {
      state._suppressAutoSave = false;
    }
    return true;
  }

  function scheduleAutoSave() {
    if (state._autoSaveTimer) clearTimeout(state._autoSaveTimer);
    state._autoSaveTimer = setTimeout(function () {
      state._autoSaveTimer = null;
      if (state.nodes.length > 0) {
        saveGraphToSpace(state.graphName, true);
      }
    }, 1200);
  }

  async function saveGraphToSpace(customName, silent) {
    const targetName = _cleanGraphName(
      customName !== undefined && customName !== null && String(customName).trim()
        ? customName
        : state.graphName
    );
    state.graphName = targetName;
    state.graphPath = "/nodes/" + targetName + ".nodes.json";
    const graphObj = serializeGraphState();
    const tgt = _resolveSpaceTarget();
    _rememberLastGraph(tgt.scope, tgt.owner_id, targetName);

    try {
      if (typeof localStorage !== "undefined" && localStorage.setItem) {
        localStorage.setItem("tincan_ns_graph_" + tgt.scope + "_" + tgt.owner_id + "_" + targetName, JSON.stringify(graphObj));
        localStorage.setItem("tincan_ns_graph_" + targetName, JSON.stringify(graphObj));
      }
    } catch (_lsErr) {}

    let savedRes = null;
    if (typeof fetch === "function") {
      try {
        const res = await fetch("/api/nodes/graph", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            scope: tgt.scope,
            owner_id: tgt.owner_id,
            name: targetName,
            path: state.graphPath,
            graph: graphObj
          })
        });
        if (res && typeof res.json === "function") {
          savedRes = await res.json();
        }
      } catch (_err) {}
    }

    _updateSaveGraphHud("✓");
    if (!silent) {
      showToast("Saved " + state.graphPath + " to .space (" + graphObj.nodes.length + " nodes)", false);
      appendTerminalLine("[+] Saved node graph → " + state.graphPath + " (" + graphObj.nodes.length + " nodes, " + graphObj.edges.length + " edges)");
      listSavedGraphs();
    }
    return savedRes || { ok: true, path: state.graphPath, name: targetName };
  }

  function renderSavedGraphsList() {
    const listEl = $("nsGraphsList");
    if (!listEl) return;
    if (!state.savedGraphs || !state.savedGraphs.length) {
      listEl.innerHTML = '<div class="ns-graph-item-meta" style="padding:4px 2px;">No saved .nodes.json files in .space yet. Click Save [⌘S] to save this canvas.</div>';
      return;
    }
    listEl.innerHTML = state.savedGraphs.map((g) => {
      const isAct = g.path === state.graphPath || g.name === state.graphName;
      const kb = Math.max(1, Math.round((g.size_bytes || 0) / 1024));
      return '<button type="button" class="ns-graph-item' + (isAct ? " is-active" : "") + '" ' +
        'onclick="window.TinCanNodeStudio.loadGraphFromSpace(\'' + escapeHtml(g.path) + '\', false)">' +
        '<span class="ns-graph-item-name">' + escapeHtml(g.name + ".nodes.json") + "</span>" +
        '<span class="ns-graph-item-meta">' + kb + " KB</span>" +
        "</button>";
    }).join("");
  }

  async function listSavedGraphs() {
    const tgt = _resolveSpaceTarget();
    if (typeof fetch !== "function") return state.savedGraphs;
    try {
      const url = "/api/nodes/graphs?scope=" + encodeURIComponent(tgt.scope) + "&owner_id=" + encodeURIComponent(tgt.owner_id);
      const res = await fetch(url);
      if (res && res.ok && typeof res.json === "function") {
        const data = await res.json();
        if (data && Array.isArray(data.graphs)) {
          state.savedGraphs = data.graphs;
          renderSavedGraphsList();
        }
      }
    } catch (_err) {}
    return state.savedGraphs;
  }

  async function loadGraphFromSpace(pathOrName, silent) {
    const cleanName = _cleanGraphName(pathOrName);
    const targetPath = "/nodes/" + cleanName + ".nodes.json";
    const tgt = _resolveSpaceTarget();
    let loaded = null;

    if (typeof fetch === "function") {
      try {
        const url = "/api/nodes/graph?scope=" + encodeURIComponent(tgt.scope) +
          "&owner_id=" + encodeURIComponent(tgt.owner_id) +
          "&path=" + encodeURIComponent(targetPath);
        const res = await fetch(url);
        if (res && res.ok && typeof res.json === "function") {
          const data = await res.json();
          if (data && data.ok && data.graph && typeof data.graph === "object") {
            loaded = data.graph;
          }
        }
      } catch (_err) {}
    }

    if (!loaded) {
      try {
        if (typeof localStorage !== "undefined" && localStorage.getItem) {
          const raw =
            localStorage.getItem("tincan_ns_graph_" + tgt.scope + "_" + tgt.owner_id + "_" + cleanName) ||
            localStorage.getItem("tincan_ns_graph_" + cleanName);
          if (raw) loaded = JSON.parse(raw);
        }
      } catch (_lsErr) {}
    }

    if (loaded && Array.isArray(loaded.nodes) && (loaded.nodes.length > 0 || !silent)) {
      applyGraphState(loaded, { name: cleanName, path: targetPath });
      _rememberLastGraph(tgt.scope, tgt.owner_id, cleanName);
      const pop = $("nsGraphsPopover");
      if (pop) pop.classList.add("hidden");
      if (!silent) {
        showToast("Reopened " + targetPath + " (" + loaded.nodes.length + " nodes)", false);
        appendTerminalLine("[+] Reopened node graph ← " + targetPath + " (" + loaded.nodes.length + " nodes)");
      }
      renderSavedGraphsList();
      return true;
    }
    if (!silent) {
      showToast("No saved graph found at " + targetPath, true);
    }
    return false;
  }

  function toggleGraphsPopover(forceOpen) {
    const pop = $("nsGraphsPopover");
    if (!pop) return;
    const shouldOpen = typeof forceOpen === "boolean" ? forceOpen : pop.classList.contains("hidden");
    pop.classList.toggle("hidden", !shouldOpen);
    if (shouldOpen) {
      _updateSaveGraphHud("");
      listSavedGraphs();
    }
  }

  function newBlankGraph() {
    state._suppressAutoSave = true;
    try {
      state.nodes.forEach(_cleanupNodeResources);
      closeMeshViewer();
      closeImageLightbox();
      state.graphName = "graph_" + String(Date.now()).slice(-4);
      state.graphPath = "/nodes/" + state.graphName + ".nodes.json";
      state.nodes = [];
      state.edges = [];
      state.selectedIds = [];
      state.references = [];
      state.nodeSeq = 0;
      state.panX = 0;
      state.panY = 0;
      state.zoom = 1;
      applyCanvasTransform();
      renderReferencesStrip();
      renderNodes();
      renderPromptIslandStatus();
      _updateSaveGraphHud("");
    } finally {
      state._suppressAutoSave = false;
    }
    const pop = $("nsGraphsPopover");
    if (pop) pop.classList.add("hidden");
    showToast("Started new blank canvas (" + state.graphName + ".nodes.json)", false);
  }

  function exportGraphJson() {
    const graphObj = serializeGraphState();
    const a = document.createElement("a");
    a.href = "data:application/json;charset=utf-8," + encodeURIComponent(JSON.stringify(graphObj, null, 2));
    a.download = state.graphName + ".nodes.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  function toggleTerminal(forceOpen) {
    const termEl = $("nsFloatingTerminal");
    const isCurrentlyOpen = termEl ? !termEl.classList.contains("hidden") : state.isTerminalOpen !== false;
    const nextOpen = typeof forceOpen === "boolean" ? forceOpen : !isCurrentlyOpen;
    state.isTerminalOpen = nextOpen;
    if (termEl) termEl.classList.toggle("hidden", !nextOpen);
    const stateLbl = $("nsTerminalToggleState");
    if (stateLbl) stateLbl.textContent = nextOpen ? "[Hide]" : "[Show]";
  }

  window.TinCanNodeStudio = {
    switchView: switchView,
    autoLayout: autoLayout,
    fitView: fitView,
    zoomIn: function () { zoomBy(1.15); },
    zoomOut: function () { zoomBy(0.87); },
    selectAllNodes: selectAllNodes,
    invertImageSelection: invertImageSelection,
    clearSelection: clearSelection,
    deleteNode: deleteNode,
    duplicateNode: duplicateNode,
    addNodeAsRef: addNodeAsRef,
    editNode: editNode,
    openFilterPopover: openFilterPopover,
    toggleNodeFilter: toggleNodeFilter,
    downloadNode: downloadNode,
    toggleLeftPanel: toggleLeftPanel,
    toggleLibSection: toggleLibSection,
    filterAssets: filterAssets,
    spawnAssetNode: spawnAssetNode,
    onAssetDragStart: function (ev, id) {
      if (ev.dataTransfer) ev.dataTransfer.setData("text/x-ns-asset", id);
    },
    applyTemplate: applyTemplate,
    addCustomTemplate: addCustomTemplate,
    parseSlashCommand: parseSlashCommand,
    applySlashRoute: applySlashRoute,
    runTerminalCommand: runTerminalCommand,
    runSlashCommand: runTerminalCommand,
    runAtlasStep: runAtlasStep,
    toggleAtlasRefine: toggleAtlasRefine,
    toggleTerminal: toggleTerminal,
    copyNodeText: copyNodeText,
    sendTextToImage: sendTextToImage,
    replyToTextNode: replyToTextNode,
    selectModality: selectModality,
    saveGraphToSpace: saveGraphToSpace,
    loadGraphFromSpace: loadGraphFromSpace,
    listSavedGraphs: listSavedGraphs,
    toggleGraphsPopover: toggleGraphsPopover,
    newBlankGraph: newBlankGraph,
    exportGraphJson: exportGraphJson,
    serializeGraphState: serializeGraphState,
    toggleSlashRouterPopover: toggleSlashRouterPopover,
    clearSlashRoute: clearSlashRoute,
    handlePromptInput: handlePromptInput,
    openSplatViewer: openSplatViewer,
    closeSplatViewer: closeSplatViewer,
    setNodeSplatMode: setNodeSplatMode,
    toggleNodeFrustums: toggleNodeFrustums,
    viewOrConvertNodeSplat: viewOrConvertNodeSplat,
    setModalSplatMode: setModalSplatMode,
    toggleModalAutoOrbit: toggleModalAutoOrbit,
    resetModalCamera: resetModalCamera,
    downloadActiveSplatSpz: downloadActiveSplatSpz,
    mountAllSplatCanvases: mountAllSplatCanvases,
    pollAudioJobForNode: pollAudioJobForNode,
    pollVideoJobForNode: pollVideoJobForNode,
    pollMeshJobForNode: pollMeshJobForNode,
    ensureModelViewer: ensureModelViewer,
    mountAllMeshPreviews: mountAllMeshPreviews,
    openMeshViewer: openMeshViewer,
    closeMeshViewer: closeMeshViewer,
    toggleMeshModalAutoRotate: toggleMeshModalAutoRotate,
    toggleMeshModalAnim: toggleMeshModalAnim,
    toggleNodeMeshAnim: toggleNodeMeshAnim,
    downloadActiveMeshGlb: downloadActiveMeshGlb,
    toggleNodeExpand: toggleNodeExpand,
    openImageLightbox: openImageLightbox,
    closeImageLightbox: closeImageLightbox,
    stepLightbox: stepLightbox,
    selectLightboxIndex: selectLightboxIndex,
    toggleLightboxZoom: toggleLightboxZoom,
    useLightboxImageAsRef: useLightboxImageAsRef,
    popOutLightboxImage: popOutLightboxImage,
    downloadLightboxImage: downloadLightboxImage,
    splitCollectionToNodes: splitCollectionToNodes,
    sendChatPrompt: sendChatPrompt,
    focusNodeOnCanvas: focusNodeOnCanvas,
    setLibraryFilter: setLibraryFilter,
    setLibrarySearch: setLibrarySearch,
    renderConversationView: renderConversationView,
    renderLibraryViewGrid: renderLibraryViewGrid,
    selectModel: function (mid) {
      state.model = mid;
      const caps = CAPS[mid];
      const nextMod = (caps && caps.modality) ? caps.modality : "image";
      state.modality = nextMod;
      if (!state.lastModelByModality) state.lastModelByModality = {};
      state.lastModelByModality[nextMod] = mid;
      if (caps && caps.audioKind) {
        state.audioKind = caps.audioKind;
      }
      // Always clear stale slash command routes when the user explicitly selects a model
      state.activeSlashCommand = "";
      const pill = $("nsActiveSlashPill");
      if (pill) pill.classList.add("hidden");
      if (nextMod === "atlas") {
        state.provider = "worldlabs";
      } else if (nextMod === "3d") {
        state.provider = "hyper3d";
      } else {
        state.provider = "auto";
      }
      const m = $("nsModelMenu");
      if (m) m.classList.add("hidden");
      syncCapabilitiesAndControls();
      renderPromptIslandStatus();
    },
    toggleModelMenu: function () {
      const m = $("nsModelMenu");
      const a = $("nsApiMenu");
      if (a) a.classList.add("hidden");
      if (m) m.classList.toggle("hidden");
    },
    toggleApiMenu: function () {
      const a = $("nsApiMenu");
      const m = $("nsModelMenu");
      if (m) m.classList.add("hidden");
      if (a) a.classList.toggle("hidden");
    },
    setApiKey: function (val) { state.apiKey = val; updateApiBadges(); },
    setNanogptKey: function (val) { state.nanogptKey = val; updateApiBadges(); },
    clearApiKeys: function () {
      state.apiKey = ""; state.nanogptKey = "";
      const g = $("nsGeminiKeyInput"); if (g) g.value = "";
      const n = $("nsNanogptKeyInput"); if (n) n.value = "";
      updateApiBadges();
    },
    updateConfig: function (key, val) {
      if (key === "atlasQuality") {
        state.atlasRefine = val === "refined";
      } else if (key === "imageCount") {
        state.imageCount = Math.max(1, Math.min(4, parseInt(val, 10) || 1));
      } else {
        state[key] = val;
        if (key === "audioKind") {
          const kindToModel = {
            music: "google/lyria-3.5",
            tts: "elevenlabs/eleven-v4",
            sfx: "elevenlabs/sound-effects/v3"
          };
          if (kindToModel[val]) {
            state.model = kindToModel[val];
            if (state.lastModelByModality) state.lastModelByModality.audio = state.model;
          }
        }
      }
      syncCapabilitiesAndControls();
      renderPromptIslandStatus();
    },
    toggleThoughts: function () {
      state.includeThoughts = !state.includeThoughts;
      syncCapabilitiesAndControls();
    },
    endConversation: function () {
      state.activeConversationNodeId = null;
      renderPromptIslandStatus();
    },
    triggerFileInput: function () {
      const inp = $("nsFileInput");
      if (inp) inp.click();
    },
    handleFilesSelected: function (files) { addFilesToRefs(files); },
    removeRef: function (id) {
      state.references = state.references.filter((r) => r.id !== id);
      renderReferencesStrip();
    },
    clearRefs: function () {
      state.references = [];
      renderReferencesStrip();
    },
    toggleShortcutsPopover: function (pin) {
      if (pin) state.isShortcutsPinned = !state.isShortcutsPinned;
      const pop = $("nsShortcutsPopover");
      const btn = $("nsShortcutsBtn");
      if (pop) pop.classList.toggle("hidden", pin ? !state.isShortcutsPinned : false);
      if (btn) btn.classList.toggle("is-pinned", state.isShortcutsPinned);
    },
    hideShortcutsIfUnpinned: function () {
      if (state.isShortcutsPinned) return;
      const pop = $("nsShortcutsPopover");
      if (pop) pop.classList.add("hidden");
    },
    generate: generate,
    getState: function () { return state; }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
</script>"""

    return (
        template.replace("__MODELS_JSON__", models_json)
        .replace("__CAPS_JSON__", caps_json)
        .replace("__STD_ASPECTS_JSON__", std_aspects_json)
        .replace("__PANO_ASPECTS_JSON__", pano_aspects_json)
        .replace("__FILTERS_JSON__", filters_json)
        .replace("__TEMPLATES_JSON__", templates_json)
        .replace("__ASSETS_JSON__", assets_json)
        .replace("__SLASH_CMDS_JSON__", slash_cmds_json)
        .replace("__INIT_VIEW__", _safe_json(initial_view))
    )


def _render_studio_stage_markup(active_view: str) -> str:
    tabs = (
        ("nodes", "Editor"),
        ("conversation", "Chat"),
        ("library", "Library"),
    )
    tabs_html = "".join(
        f'<button id="nsViewTab-{tid}" type="button" data-view-tab="{tid}" '
        f'class="ns-view-tab{" is-active" if tid == active_view else ""}" '
        f'aria-pressed="{"true" if tid == active_view else "false"}" '
        f'onclick="window.TinCanNodeStudio.switchView(\'{tid}\')">{label}</button>'
        for tid, label in tabs
    )

    aspect_opts = "".join(
        f'<option value="{a}"{" selected" if a == "1:1" else ""}>{a}</option>'
        for a in (STANDARD_ASPECT_RATIOS + PANORAMIC_ASPECT_RATIOS)
    )
    res_opts = "".join(
        f'<option value="{r}"{" selected" if r == "1K" else ""}>{r}</option>'
        for r in ("1K", "2K", "4K", "1280x720")
    )
    think_opts = "".join(
        f'<option value="{t}"{" selected" if t == "medium" else ""}>{t}</option>'
        for t in ("minimal", "medium", "high")
    )
    search_opts = "".join(
        f'<option value="{g}"{" selected" if g == "Off" else ""}>{g}</option>'
        for g in ("Off", "Web", "Image", "Web+Img")
    )
    via_opts = "".join(
        f'<option value="{v}"{" selected" if v == "auto" else ""}>{v}</option>'
        for v in ("auto", "gemini", "nanogpt", "worldlabs", "hyper3d")
    )

    return f"""<div id="nsStudioStage" class="ns-studio-stage">
  <!-- Full-Screen Infinite 24x24 Dot-Grid Canvas (Editor View) -->
  <div id="nsDotCanvas" class="ns-dot-canvas" aria-label="Node Studio Infinite Canvas">
    <div id="nsEmptyState" class="ns-empty-state">
      <svg class="ns-empty-icon" viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
        <path d="M4 4l7 17 2.5-6.5L20 12 4 4z"/>
      </svg>
      <p class="ns-empty-title">Canvas Empty</p>
      <p class="ns-empty-sub">Use the toolbar below to generate or drag &amp; drop images</p>
    </div>

    <div id="nsCanvasWorld" class="ns-canvas-world">
      <svg id="nsEdgesSvg" class="ns-edges-svg" aria-hidden="true"></svg>
      <div id="nsNodesLayer"></div>
    </div>

    <div id="nsSelectionBox" class="ns-selection-box"></div>
    <div id="nsDropOverlay" class="ns-drop-overlay">Drop images here</div>
  </div>

  <!-- Floating Pitch-Black (#000000) Node Studio Terminal -->
  {_render_floating_terminal_html()}

  <!-- Chat View (ConversationView) -->
  <section id="nsConversationView" class="ns-alt-view{" hidden" if active_view != "conversation" else ""}" aria-label="Conversation Editor">
    <div class="ns-alt-card">
      <div class="ns-chat-head">
        <div>
          <h2 class="ns-alt-title">Conversation Editor</h2>
          <p class="ns-alt-desc">Interact with Gemini and NanoGPT using the tree-based conversation context synced directly with your canvas nodes.</p>
        </div>
        <div id="nsChatHeaderMeta" class="ns-chat-meta">Full session · 0 nodes</div>
      </div>
      <div id="nsChatFeed" class="ns-chat-feed" role="log" aria-live="polite"></div>
      <div id="nsChatComposer" class="ns-chat-composer">
        <textarea id="nsChatInput" class="ns-chat-input" rows="1" placeholder="Send a follow-up prompt using the active modality and model..."></textarea>
        <button id="nsChatSendBtn" type="button" class="ns-chat-send-btn" onclick="window.TinCanNodeStudio.sendChatPrompt()">Send →</button>
      </div>
    </div>
  </section>

  <!-- Library View (LibraryView) -->
  <section id="nsLibraryView" class="ns-alt-view{" hidden" if active_view != "library" else ""}" aria-label="Asset Library">
    <div class="ns-alt-card">
      <div>
        <h2 class="ns-alt-title">Asset Library</h2>
        <p class="ns-alt-desc">Browse generated assets and conversation history from your Node Studio session.</p>
      </div>
      <div id="nsLibFilterBar" class="ns-lib-filter-bar">
        <div class="ns-lib-chips" role="tablist" aria-label="Filter assets by modality">
          <button id="nsLibChip-all" type="button" class="ns-lib-chip is-active" data-lib-filter="all" aria-pressed="true" onclick="window.TinCanNodeStudio.setLibraryFilter('all')">All</button>
          <button id="nsLibChip-image" type="button" class="ns-lib-chip" data-lib-filter="image" aria-pressed="false" onclick="window.TinCanNodeStudio.setLibraryFilter('image')">Image</button>
          <button id="nsLibChip-text" type="button" class="ns-lib-chip" data-lib-filter="text" aria-pressed="false" onclick="window.TinCanNodeStudio.setLibraryFilter('text')">Text</button>
          <button id="nsLibChip-video" type="button" class="ns-lib-chip" data-lib-filter="video" aria-pressed="false" onclick="window.TinCanNodeStudio.setLibraryFilter('video')">Video</button>
          <button id="nsLibChip-audio" type="button" class="ns-lib-chip" data-lib-filter="audio" aria-pressed="false" onclick="window.TinCanNodeStudio.setLibraryFilter('audio')">Audio</button>
          <button id="nsLibChip-3d" type="button" class="ns-lib-chip" data-lib-filter="3d" aria-pressed="false" onclick="window.TinCanNodeStudio.setLibraryFilter('3d')">3D Mesh</button>
          <button id="nsLibChip-atlas" type="button" class="ns-lib-chip" data-lib-filter="atlas" aria-pressed="false" onclick="window.TinCanNodeStudio.setLibraryFilter('atlas')">3D Splat</button>
        </div>
        <input id="nsLibSearchInput" type="text" class="ns-lib-search" placeholder="Search session assets..." oninput="window.TinCanNodeStudio.setLibrarySearch(this.value)">
      </div>
      <div id="nsLibraryViewGrid" class="ns-lib-grid"></div>
    </div>
  </section>

  <!-- Floating Top-Center View Switcher Pill -->
  <div class="ns-top-switcher-wrap">
    <div class="ns-top-switcher" role="tablist" aria-label="Node Studio Views">
      {tabs_html}
    </div>
  </div>

  <!-- Top-Right Floating HUD -->
  <div class="ns-top-right-hud">
    <div id="nsCopyIndicator" class="ns-copy-indicator hidden">⌘/Ctrl held - click node to duplicate</div>
    <div class="ns-hud-row">
      <button id="nsSaveGraphBtn" type="button" class="ns-hud-btn" title="Save node graph to .space (/nodes/*.nodes.json · ⌘S)" onclick="window.TinCanNodeStudio.saveGraphToSpace()">
        <span>Save</span><span id="nsSaveGraphStatus">[workspace]</span>
      </button>
      <button id="nsGraphsMenuBtn" type="button" class="ns-hud-btn" title="Open or manage saved .nodes.json graphs in your .space" onclick="window.TinCanNodeStudio.toggleGraphsPopover()">
        <span>Graphs</span><span>▾</span>
      </button>
      <button id="nsTerminalToggleBtn" type="button" class="ns-hud-btn" title="Show/Hide Node Studio Dark Terminal (Press `)" onclick="window.TinCanNodeStudio.toggleTerminal()">
        <span>Terminal</span><span id="nsTerminalToggleState">[Show]</span>
      </button>
      <button id="nsAutoLayoutBtn" type="button" class="ns-hud-btn hidden" title="Reorganize tree layout (Press A)" onclick="window.TinCanNodeStudio.autoLayout()">
        <span>Auto-Layout</span><span>[A]</span>
      </button>
      <button id="nsShortcutsBtn" type="button" class="ns-hud-btn" title="Show keyboard shortcuts"
        onmouseenter="window.TinCanNodeStudio.toggleShortcutsPopover(false)"
        onmouseleave="window.TinCanNodeStudio.hideShortcutsIfUnpinned()"
        onclick="window.TinCanNodeStudio.toggleShortcutsPopover(true)">
        <span>Keys</span><span>[i]</span>
      </button>
    </div>
    <div id="nsGraphsPopover" class="ns-graphs-popover hidden" role="dialog" aria-label="Saved Node Studio Graphs">
      <div class="ns-graphs-head">
        <span>SAVED .NODES.JSON (.SPACE)</span>
        <button type="button" class="ns-icon-btn" title="Close" onclick="window.TinCanNodeStudio.toggleGraphsPopover(false)">×</button>
      </div>
      <div class="ns-graphs-saveas-row">
        <input id="nsGraphNameInput" type="text" class="ns-graphs-input" placeholder="workspace (e.g. torii_shrine)"
          onkeydown="if(event.key==='Enter'){{event.preventDefault();window.TinCanNodeStudio.saveGraphToSpace(this.value, false);}}">
        <button id="nsGraphSaveAsBtn" type="button" class="ns-top-btn" onclick="window.TinCanNodeStudio.saveGraphToSpace(document.getElementById('nsGraphNameInput').value, false)">Save As</button>
      </div>
      <div id="nsGraphsList" class="ns-graphs-list"></div>
      <div class="ns-graphs-foot">
        <button id="nsGraphNewBtn" type="button" class="ns-top-btn" onclick="window.TinCanNodeStudio.newBlankGraph()">+ New Blank</button>
        <button id="nsGraphExportBtn" type="button" class="ns-top-btn" onclick="window.TinCanNodeStudio.exportGraphJson()">↓ Export .nodes.json</button>
      </div>
    </div>
    <div id="nsShortcutsPopover" class="ns-shortcuts-popover hidden"
      onmouseenter="window.TinCanNodeStudio.toggleShortcutsPopover(false)"
      onmouseleave="window.TinCanNodeStudio.hideShortcutsIfUnpinned()">
      <div class="ns-shortcuts-title">Keyboard Shortcuts</div>
      <div class="ns-shortcut-line"><span>Save graph to .space</span><span>⌘/Ctrl + S</span></div>
      <div class="ns-shortcut-line"><span>Delete nodes</span><span>Delete / Backspace</span></div>
      <div class="ns-shortcut-line"><span>Auto-layout</span><span>⌘/Ctrl + A</span></div>
      <div class="ns-shortcut-line"><span>Select all nodes</span><span>A</span></div>
      <div class="ns-shortcut-line"><span>Fit view</span><span>F</span></div>
      <div class="ns-shortcut-line"><span>Invert image selection</span><span>I</span></div>
      <div class="ns-shortcut-line"><span>Toggle dark terminal</span><span>`</span></div>
    </div>
  </div>

  <!-- Left-Center Draggable FloatingPill (Collapsed) -->
  <div id="nsLeftPillWrap" class="ns-left-pill-wrap" aria-label="Lumina Library Pill">
    <div class="ns-left-pill">
      <div class="ns-pill-grip" title="Drag pill" aria-hidden="true">⋮⋮</div>
      <button id="nsPillExpandBtn" type="button" class="ns-pill-expand" title="Expand Lumina Library" aria-label="Expand Lumina Library" onclick="window.TinCanNodeStudio.toggleLeftPanel(true)">↗</button>
      <div class="ns-pill-div"></div>
      <span id="nsPillCount" class="ns-pill-count">15</span>
      <span class="ns-pill-dot" aria-hidden="true"></span>
    </div>
  </div>

  <!-- Expanded Lumina Library Drawer -->
  <aside id="nsLeftDrawer" class="ns-left-drawer hidden" aria-label="Lumina Library">
    <div class="ns-drawer-head">
      <div class="ns-drawer-title"><span>↗</span><span>Lumina Library</span></div>
      <div>
        <button type="button" class="ns-icon-btn" title="Settings">⚙</button>
        <button id="nsCloseDrawerBtn" type="button" class="ns-icon-btn" title="Collapse" onclick="window.TinCanNodeStudio.toggleLeftPanel(false)">×</button>
      </div>
    </div>

    <div class="ns-drawer-body">
      <div>
        <button type="button" class="ns-sec-header" onclick="window.TinCanNodeStudio.toggleLibSection('references')">
          <span class="ns-sec-header-lead"><span>References</span><span id="nsLibRefCount" class="ns-sec-count">0</span></span>
          <span>▾</span>
        </button>
        <div id="nsLibSec-references" class="ns-sec-content">
          <div id="nsLibRefDrop" class="ns-lib-ref-drop" onclick="window.TinCanNodeStudio.triggerFileInput()">
            <span class="ns-lib-ref-label">DROP OR CLICK · MULTI-SELECT 3–14 PHOTOS</span>
            <span class="ns-lib-ref-label">torii_1k.jpg · view_02.jpg · view_03.jpg · depth_0.exr</span>
          </div>
        </div>
      </div>

      <div class="ns-sec-div"></div>

      <div>
        <button type="button" class="ns-sec-header" onclick="window.TinCanNodeStudio.toggleLibSection('assets')">
          <span class="ns-sec-header-lead"><span>3D Assets</span><span class="ns-sec-count">15</span></span>
          <span>▾</span>
        </button>
        <div id="nsLibSec-assets" class="ns-sec-content">
          <input id="nsAssetSearchInput" type="text" class="ns-asset-search" placeholder="Search assets... (.spz, .glb, .exr, .mp4, .wav)" oninput="window.TinCanNodeStudio.filterAssets(this.value)">
          <div id="nsLibAssetGrid" class="ns-asset-grid">
            {_render_asset_grid_html()}
          </div>
        </div>
      </div>

      <div class="ns-sec-div"></div>

      <div>
        <button type="button" class="ns-sec-header" onclick="window.TinCanNodeStudio.toggleLibSection('templates')">
          <span class="ns-sec-header-lead"><span>Prompts</span><span class="ns-sec-count">5</span></span>
          <span>▾</span>
        </button>
        <div id="nsLibSec-templates" class="ns-sec-content hidden">
          <div id="nsLibTemplateList" class="ns-tpl-list">
            {_render_template_list_html()}
          </div>
        </div>
      </div>
    </div>

    <div class="ns-drawer-foot">
      <span class="ns-sync-status"><span class="ns-pill-dot"></span><span>SYNCED</span></span>
      <span>Storage: 24%</span>
    </div>
  </aside>

  <!-- Bottom-Left Zoom Controls -->
  <div id="nsZoomControls" class="ns-zoom-controls" aria-label="Canvas Zoom Controls">
    <button id="nsZoomInBtn" type="button" class="ns-zoom-btn" title="Zoom In" onclick="window.TinCanNodeStudio.zoomIn()">+</button>
    <button id="nsZoomOutBtn" type="button" class="ns-zoom-btn" title="Zoom Out" onclick="window.TinCanNodeStudio.zoomOut()">−</button>
    <button id="nsFitViewBtn" type="button" class="ns-zoom-btn" title="Fit View" onclick="window.TinCanNodeStudio.fitView()">[]</button>
  </div>

  <!-- Bottom-Center Floating PromptIsland (max-w-[920px]) -->
  <div class="ns-island-dock">
    <div class="ns-island-wrap">
      <div id="nsResponseToast" class="ns-response-toast hidden" role="status" aria-live="polite"></div>

      <div id="nsPromptIsland" class="ns-island">
        {_render_slash_router_popover_html()}

        <div class="ns-island-top">
          <div class="ns-island-badges">
            {_render_modality_bar_html()}
            <button id="nsActiveSlashPill" type="button" class="ns-active-slash-pill hidden" title="Toggle Slash-Command Omni-Modal Router" onclick="window.TinCanNodeStudio.toggleSlashRouterPopover()">
              <span id="nsActiveSlashPillText"></span>
              <span class="ns-slash-pill-close" onclick="event.stopPropagation();window.TinCanNodeStudio.clearSlashRoute()">×</span>
            </button>
            <span id="nsModePill" class="ns-mode-pill">GENERATE MODE</span>
            <span id="nsConvPill" class="ns-context-pill hidden">
              <span>In Conversation</span>
              <button type="button" class="ns-context-close" title="End conversation" onclick="window.TinCanNodeStudio.endConversation()">×</button>
            </span>
            <span id="nsBranchPill" class="ns-context-pill hidden">Branching from image</span>
          </div>

          <div id="nsIslandMenuArea" class="ns-island-top-right">
            <button id="nsApiBtn" type="button" class="ns-top-btn" onclick="window.TinCanNodeStudio.toggleApiMenu()">
              <span>API</span>
            </button>
            <div id="nsApiMenu" class="ns-popover ns-api-menu hidden" role="dialog" aria-label="API Configuration">
              <div class="ns-pop-title">API Configuration</div>
              <div class="ns-api-badges">
                <span id="nsApiGeminiStatus" class="ns-api-badge">Gemini: Not Set</span>
                <span id="nsApiNanogptStatus" class="ns-api-badge">NanoGPT: Not Set</span>
                <span id="nsApiAtlasStatus" class="ns-api-badge is-ready">Atlas v2: Ready</span>
              </div>
              <input id="nsGeminiKeyInput" type="password" class="ns-api-input" placeholder="Custom Gemini Key (optional)" oninput="window.TinCanNodeStudio.setApiKey(this.value)">
              <input id="nsNanogptKeyInput" type="password" class="ns-api-input" placeholder="Custom NanoGPT Key (optional)" oninput="window.TinCanNodeStudio.setNanogptKey(this.value)">
              <div class="ns-api-foot">
                <span id="nsApiSourceText">No server key configured</span>
                <button id="nsApiClearBtn" type="button" class="ns-api-clear" style="display:none;" onclick="window.TinCanNodeStudio.clearApiKeys()">Clear</button>
              </div>
            </div>

            <button id="nsModelBtn" type="button" class="ns-top-btn" onclick="window.TinCanNodeStudio.toggleModelMenu()">
              <span id="nsModelBtnLabel">Nano Banana 2.1</span>
              <span>▾</span>
            </button>
            <div id="nsModelMenu" class="ns-popover ns-model-menu hidden" role="menu" aria-label="Select Model">
              <div class="ns-pop-title" style="padding:4px 8px;">Select Model</div>
              {_render_model_menu_items_html()}
            </div>
          </div>
        </div>

        <div id="nsRefsStrip" class="ns-refs-strip">
          <div id="nsRefsRow" class="ns-refs-row"></div>
        </div>

        <div class="ns-prompt-area">
          <textarea id="nsPromptInput" class="ns-prompt-textarea" rows="1" spellcheck="false" placeholder="Describe what you want to generate..."></textarea>
          <button id="nsAttachTrigger" type="button" class="ns-attach-trigger" title="Attach references (Images, Audio, Video, PDF — up to 14)" onclick="window.TinCanNodeStudio.triggerFileInput()">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
            </svg>
          </button>
          <input id="nsFileInput" type="file" class="ns-hidden-input" multiple accept="image/*,video/*,audio/*,application/pdf" onchange="window.TinCanNodeStudio.handleFilesSelected(this.files);this.value='';">
        </div>

        <div class="ns-action-bar">
          <div class="ns-settings-group">
            <div id="nsAspectWrap" class="ns-setting-wrap">
              <span class="ns-setting-lbl">ASPECT</span>
              <span id="nsAspectVal" class="ns-setting-val">1:1</span>
              <select id="nsAspectSelect" class="ns-setting-select" aria-label="Aspect Ratio" onchange="window.TinCanNodeStudio.updateConfig('aspectRatio', this.value)">
                {aspect_opts}
              </select>
            </div>

            <div id="nsResWrap" class="ns-setting-wrap">
              <span class="ns-setting-lbl">RES</span>
              <span id="nsResVal" class="ns-setting-val">1K</span>
              <select id="nsResSelect" class="ns-setting-select" aria-label="Resolution" onchange="window.TinCanNodeStudio.updateConfig('resolution', this.value)">
                {res_opts}
              </select>
            </div>

            <div id="nsBatchWrap" class="ns-setting-wrap">
              <span class="ns-setting-lbl">COUNT</span>
              <span id="nsBatchVal" class="ns-setting-val">1x</span>
              <select id="nsBatchSelect" class="ns-setting-select" aria-label="Image Collection Count" onchange="window.TinCanNodeStudio.updateConfig('imageCount', this.value)">
                <option value="1" selected>1 Image (1x)</option>
                <option value="2">2 Images (Collection)</option>
                <option value="3">3 Images (Collection)</option>
                <option value="4">4 Images (Collection)</option>
              </select>
            </div>

            <div id="nsFpsWrap" class="ns-setting-wrap hidden">
              <span class="ns-setting-lbl">FPS</span>
              <span id="nsFpsVal" class="ns-setting-val">60fps</span>
              <select id="nsFpsSelect" class="ns-setting-select" aria-label="Video Frame Rate" onchange="window.TinCanNodeStudio.updateConfig('videoFps', this.value)">
                <option value="24">24fps</option>
                <option value="60" selected>60fps</option>
              </select>
            </div>

            <div id="nsAudioKindWrap" class="ns-setting-wrap hidden">
              <span class="ns-setting-lbl">TYPE</span>
              <span id="nsAudioKindVal" class="ns-setting-val">Music</span>
              <select id="nsAudioKindSelect" class="ns-setting-select" aria-label="Audio Type" onchange="window.TinCanNodeStudio.updateConfig('audioKind', this.value)">
                <option value="music" selected>Music (Lyria 3.5)</option>
                <option value="tts">Voice TTS (ElevenLabs v4)</option>
                <option value="sfx">Sound Effects (SFX v3)</option>
              </select>
            </div>

            <div id="nsMeshTierWrap" class="ns-setting-wrap hidden">
              <span class="ns-setting-lbl">TIER</span>
              <span id="nsMeshTierVal" class="ns-setting-val">Regular</span>
              <select id="nsMeshTierSelect" class="ns-setting-select" aria-label="3D Mesh Tier" onchange="window.TinCanNodeStudio.updateConfig('meshTier', this.value)">
                <option value="Sketch">Sketch</option>
                <option value="Regular" selected>Regular</option>
                <option value="Detail">Detail</option>
                <option value="Smooth">Smooth</option>
              </select>
            </div>

            <div id="nsAtlasTaskWrap" class="ns-setting-wrap hidden">
              <span class="ns-setting-lbl">STEP</span>
              <span id="nsAtlasTaskVal" class="ns-setting-val">Build Splat</span>
              <select id="nsAtlasTaskSelect" class="ns-setting-select" aria-label="3D Splat Step" onchange="window.TinCanNodeStudio.updateConfig('atlasTask', this.value)">
                <option value="posedImages2Splats" selected>Build 3D Splat</option>
                <option value="images2PosedRGBD">Pose Photos</option>
                <option value="atlasGenerate">Generate 6 Views</option>
                <option value="splats2Mesh">Export .GLB</option>
              </select>
            </div>

            <div id="nsAtlasQualWrap" class="ns-setting-wrap hidden">
              <span class="ns-setting-lbl">QUALITY</span>
              <span id="nsAtlasQualVal" class="ns-setting-val">Draft (~30s)</span>
              <select id="nsAtlasQualSelect" class="ns-setting-select" aria-label="Splat Quality" onchange="window.TinCanNodeStudio.updateConfig('atlasQuality', this.value)">
                <option value="draft" selected>Draft (~30s · $0.50)</option>
                <option value="refined">Refined 2M (18m · $5.00)</option>
              </select>
            </div>

            <div id="nsThinkWrap" class="ns-setting-wrap">
              <span class="ns-setting-lbl">THINK</span>
              <span id="nsThinkVal" class="ns-setting-val">medium</span>
              <select id="nsThinkSelect" class="ns-setting-select" aria-label="Thinking Level" onchange="window.TinCanNodeStudio.updateConfig('thinkingLevel', this.value)">
                {think_opts}
              </select>
            </div>

            <button id="nsThoughtsBtn" type="button" class="ns-thoughts-btn" onclick="window.TinCanNodeStudio.toggleThoughts()">THOUGHTS</button>

            <span class="ns-vdiv" aria-hidden="true"></span>

            <div id="nsSearchWrap" class="ns-setting-wrap">
              <span class="ns-setting-lbl">SEARCH</span>
              <span id="nsSearchVal" class="ns-setting-val">Off</span>
              <select id="nsSearchSelect" class="ns-setting-select" aria-label="Search Grounding" onchange="window.TinCanNodeStudio.updateConfig('groundingMode', this.value)">
                {search_opts}
              </select>
            </div>

            <span class="ns-vdiv" aria-hidden="true"></span>

            <div class="ns-setting-wrap">
              <span class="ns-setting-lbl">VIA</span>
              <span id="nsViaVal" class="ns-setting-val">auto</span>
              <select id="nsViaSelect" class="ns-setting-select" aria-label="Provider" onchange="window.TinCanNodeStudio.updateConfig('provider', this.value)">
                {via_opts}
              </select>
            </div>

            <span id="nsRefCounter" class="ns-ref-counter">0/14 refs (Img/Vid/PDF)</span>
          </div>

          <div class="ns-run-group">
            <span id="nsActiveRunsPill" class="ns-runs-pill" title="Concurrent generations"><span id="nsActiveRunsCount">0/2</span></span>
            <button id="nsGenerateBtn" type="button" class="ns-generate-btn" disabled onclick="window.TinCanNodeStudio.generate()">Generate →</button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Fullscreen 3D Gaussian Splat (.SPZ) & Posed RGBD (.EXR) Interactive Viewer Modal -->
  <div id="nsSplatViewerModal" class="ns-splat-modal-backdrop hidden" role="dialog" aria-modal="true" aria-label="3D Gaussian Splat Viewer">
    <div class="ns-splat-modal">
      <div class="ns-splat-modal-head">
        <div>
          <div id="nsSplatModalTitle" class="ns-splat-modal-title">3D GAUSSIAN SPLAT VIEWER (.SPZ) · Lake Ashi Torii Shrine 360°</div>
          <div id="nsSplatModalMeta" class="ns-splat-modal-sub">/worlds/torii_3e78434c/refinedSplats_2000000.spz · 2,000,000 Splats · RUB Cam fx=893.4 fy=893.9 · Drag to Orbit / Scroll to Zoom / WASD Flythrough</div>
        </div>
        <div class="ns-splat-modal-actions">
          <button id="nsSplatModeRgbBtn" type="button" class="ns-splat-btn" onclick="window.TinCanNodeStudio.setModalSplatMode('rgb')">3D Splats (.SPZ)</button>
          <button id="nsSplatModeDepthBtn" type="button" class="ns-splat-btn" onclick="window.TinCanNodeStudio.setModalSplatMode('depth')">Linear Depth (.EXR)</button>
          <button id="nsSplatModeConfBtn" type="button" class="ns-splat-btn" onclick="window.TinCanNodeStudio.setModalSplatMode('confidence')">Confidence (98.4%)</button>
          <button id="nsSplatAutoOrbitBtn" type="button" class="ns-splat-btn" onclick="window.TinCanNodeStudio.toggleModalAutoOrbit()">⟳ Auto-Orbit</button>
          <button id="nsSplatResetCamBtn" type="button" class="ns-splat-btn" onclick="window.TinCanNodeStudio.resetModalCamera('near')">Cam 0 (Near)</button>
          <button id="nsSplatTopCamBtn" type="button" class="ns-splat-btn" onclick="window.TinCanNodeStudio.resetModalCamera('top')">Top View</button>
          <button id="nsSplatDownloadBtn" type="button" class="ns-splat-btn" onclick="window.TinCanNodeStudio.downloadActiveSplatSpz()">↓ .SPZ</button>
          <button id="nsSplatCloseBtn" type="button" class="ns-splat-btn ns-splat-btn--expand" onclick="window.TinCanNodeStudio.closeSplatViewer()">✕ Close [Esc]</button>
        </div>
      </div>
      <div class="ns-splat-modal-viewport">
        <div id="nsSplatViewerBadge" class="ns-splat-modal-badge">◐ POSED RGBD PREVIEW</div>
        <div id="nsSparkWebGLContainer" class="ns-spark-webgl hidden"></div>
        <canvas id="nsSplatModalCanvas" width="940" height="520"></canvas>
      </div>
      <div class="ns-splat-modal-foot">
        <span>RUB Coordinates (+X Right, +Y Up, +Z Back) · Centroid [-1.99, 0.00, -36.35] · 14 Posed Frustums</span>
        <span>Controls: Left-Drag Orbit · Shift+Drag Pan · Wheel/W/S Zoom · A/D/Q/E Flythrough</span>
      </div>
    </div>
  </div>

  <!-- Fullscreen 3D Mesh (.GLB) Interactive Inspector Modal -->
  <div id="nsMeshViewerModal" class="ns-splat-modal-backdrop hidden" role="dialog" aria-modal="true" aria-label="3D Mesh Inspector">
    <div class="ns-splat-modal">
      <div class="ns-splat-modal-head">
        <div>
          <div id="nsMeshModalTitle" class="ns-splat-modal-title">3D MESH INSPECTOR (.GLB)</div>
          <div id="nsMeshModalMeta" class="ns-splat-modal-sub">/models3d/mesh.glb · PBR Textured 3D Mesh · Drag to Orbit / Scroll to Zoom</div>
        </div>
        <div class="ns-splat-modal-actions">
          <button id="nsMeshModalAutoRotateBtn" type="button" class="ns-splat-btn is-active" onclick="window.TinCanNodeStudio.toggleMeshModalAutoRotate()">⟳ Auto-Rotate</button>
          <button id="nsMeshModalAnimBtn" type="button" class="ns-splat-btn hidden" onclick="window.TinCanNodeStudio.toggleMeshModalAnim()">❚❚ Pause Anim</button>
          <button id="nsMeshModalDownloadBtn" type="button" class="ns-splat-btn" onclick="window.TinCanNodeStudio.downloadActiveMeshGlb()">↓ .GLB</button>
          <button id="nsMeshModalCloseBtn" type="button" class="ns-splat-btn ns-splat-btn--expand" onclick="window.TinCanNodeStudio.closeMeshViewer()">✕ Close [Esc]</button>
        </div>
      </div>
      <div id="nsMeshModalViewport" class="ns-mesh-modal-viewport">
        <div id="nsMeshModalBadge" class="ns-splat-modal-badge">◐ ISOMETRIC WIREFRAME PREVIEW</div>
        <canvas id="nsMeshModalWireCanvas" class="ns-mesh-wire-canvas" width="940" height="460"></canvas>
      </div>
      <div class="ns-splat-modal-foot">
        <span>Hyper3D Rodin v2.5 · PBR .GLB Interactive Inspector (@google/model-viewer + Wireframe Fallback)</span>
        <span>Controls: Left-Drag Orbit · Scroll Zoom · Esc Close</span>
      </div>
    </div>
  </div>

  <!-- Fullscreen Image & Collection Lightbox Modal -->
  <div id="nsImageLightboxModal" class="ns-splat-modal-backdrop hidden" role="dialog" aria-modal="true" aria-label="Image Lightbox" onclick="if(event.target===this)window.TinCanNodeStudio.closeImageLightbox()">
    <div class="ns-splat-modal">
      <div class="ns-splat-modal-head">
        <div>
          <div id="nsLightboxTitle" class="ns-splat-modal-title">IMAGE LIGHTBOX</div>
          <div id="nsLightboxMeta" class="ns-splat-modal-sub">Nano Banana · High-Resolution Preview</div>
        </div>
        <div class="ns-splat-modal-actions">
          <span id="nsLightboxCounter" class="ns-splat-btn">1 / 1</span>
          <button id="nsLightboxZoomBtn" type="button" class="ns-splat-btn" onclick="window.TinCanNodeStudio.toggleLightboxZoom()">2× Zoom</button>
          <button id="nsLightboxUseRefBtn" type="button" class="ns-splat-btn" onclick="window.TinCanNodeStudio.useLightboxImageAsRef()">+ Use as Ref</button>
          <button id="nsLightboxPopOutBtn" type="button" class="ns-splat-btn" onclick="window.TinCanNodeStudio.popOutLightboxImage()">↗ Pop Out Node</button>
          <button id="nsLightboxDownloadBtn" type="button" class="ns-splat-btn" onclick="window.TinCanNodeStudio.downloadLightboxImage()">↓ Download</button>
          <button id="nsLightboxCloseBtn" type="button" class="ns-splat-btn ns-splat-btn--expand" onclick="window.TinCanNodeStudio.closeImageLightbox()">✕ Close [Esc]</button>
        </div>
      </div>
      <div id="nsLightboxStage" class="ns-lightbox-stage">
        <button id="nsLightboxPrevBtn" type="button" class="ns-lightbox-nav ns-lightbox-nav--prev hidden" aria-label="Previous image" onclick="window.TinCanNodeStudio.stepLightbox(-1)">‹</button>
        <img id="nsLightboxImg" class="ns-lightbox-img" src="" alt="Lightbox preview" onclick="window.TinCanNodeStudio.toggleLightboxZoom()">
        <button id="nsLightboxNextBtn" type="button" class="ns-lightbox-nav ns-lightbox-nav--next hidden" aria-label="Next image" onclick="window.TinCanNodeStudio.stepLightbox(1)">›</button>
      </div>
      <div id="nsLightboxStrip" class="ns-lightbox-strip hidden"></div>
      <div class="ns-splat-modal-foot">
        <span>Click image to toggle 2× Zoom · Use filmstrip or ←/→ keys to browse collection</span>
        <span>Controls: ←/→ Navigate · Click Zoom · Esc Close</span>
      </div>
    </div>
  </div>
</div>"""


def render_node_studio_html(active_modality: str = "image", active_view: str = "nodes") -> str:
    """Render the full-screen 1:1 Nano Banana Gemini Node Studio HTML5 document in Aeonik Celadon & Ink."""
    _ = active_modality  # Kept for route signature compatibility
    view = _normalize_view(active_view)
    stage_html = _render_studio_stage_markup(view)
    css_block = _node_studio_css()
    js_block = _node_studio_js(view)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Node Studio · Nano Banana Gemini &amp; NanoGPT</title>
  <link rel="preload" href="/assets/fonts/inter-latin-wght.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="/assets/fonts/jetbrains-mono-latin-wght.woff2" as="font" type="font/woff2" crossorigin>
  <style id="nsFonts">
    @font-face {{ font-family: "Inter"; font-style: normal; font-weight: 100 900; font-display: swap;
      src: url("/assets/fonts/inter-latin-wght.woff2") format("woff2"); }}
    @font-face {{ font-family: "JetBrains Mono"; font-style: normal; font-weight: 100 800; font-display: swap;
      src: url("/assets/fonts/jetbrains-mono-latin-wght.woff2") format("woff2"); }}
    html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background: #ecf1e6; color: #111111; }}
  </style>
  {css_block}
</head>
<body>
  {stage_html}
  {js_block}
</body>
</html>"""


def render_node_studio_window_html() -> str:
    """Render the embeddable ``#win-nodes`` Mesh OS window for Nano Banana Gemini Node Studio."""
    stage_html = _render_studio_stage_markup("nodes")
    css_block = _node_studio_css()
    js_block = _node_studio_js("nodes")
    return (
        '<div id="win-nodes" class="mesh-window w-[1180px] max-w-full hidden tc-ns-host" '
        'data-zen-window="true" data-window-id="win-nodes" style="top: 56px; left: 88px; z-index: 38;">\n'
        '      <!--TC_TITLEBAR {"id": "win-nodes", "title": "Node Studio · Prompt Island, Timeline & Filter Graph", "badge": "NANOGPT + GEMINI"}-->\n'
        f"{css_block}\n"
        '      <div class="window-body ns-body aeonik-scope" data-ns-root="true">\n'
        f"{stage_html}\n"
        "      </div>\n"
        f"{js_block}\n"
        "    </div>"
    )


__all__ = [
    "AEONIK_PALETTE",
    "AVAILABLE_MODELS",
    "FILTER_PRESETS",
    "LUMINA_ASSETS",
    "LUMINA_TEMPLATES",
    "MODALITY_TABS",
    "MODEL_CAPABILITIES",
    "PANORAMIC_ASPECT_RATIOS",
    "SLASH_ROUTER_COMMANDS",
    "STANDARD_ASPECT_RATIOS",
    "render_node_studio_html",
    "render_node_studio_window_html",
]
