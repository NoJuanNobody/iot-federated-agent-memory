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

AVAILABLE_MODELS: Tuple[Dict[str, str], ...] = (
    {
        "id": "gemini-nano-banana-2.1",
        "name": "Nano Banana 2.1",
        "badge": "Default",
        "description": "Text/Img/Vid/PDF • 1K-4K • 14 refs (4 chars, 10 objs) • Panoramic • Web+Img Search • Think",
    },
    {
        "id": "gemini-3-pro-image",
        "name": "Nano Banana Pro",
        "badge": "Pro",
        "description": "Text/Img • Studio 4K • Advanced Reasoning • Web Search Grounding",
    },
    {
        "id": "gemini-3.1-flash-image",
        "name": "Nano Banana 2",
        "badge": "Flash",
        "description": "Text/Img/Vid/PDF • 512-4K • 14 refs • Panoramic • Web+Img Search",
    },
    {
        "id": "gemini-3.1-flash-lite-image",
        "name": "Nano Banana 2 Lite",
        "badge": "Lite",
        "description": "Text/Img/Vid/PDF • Ultra-low latency 1K • Thinking minimal/high",
    },
)

MODEL_CAPABILITIES: Dict[str, Dict[str, Any]] = {
    "gemini-nano-banana-2.1": {
        "resolutions": ["1K", "2K", "4K"],
        "groundingModes": ["Off", "Web", "Image", "Web+Img"],
        "panoramicAspects": True,
        "thinkingLevels": ["minimal", "medium", "high"],
        "defaultThinkingLevel": "medium",
        "supportsVideoAndPdf": True,
        "maxReferences": 14,
    },
    "gemini-3-pro-image": {
        "resolutions": ["1K", "2K", "4K"],
        "groundingModes": ["Off", "Web"],
        "panoramicAspects": False,
        "thinkingLevels": None,
        "supportsVideoAndPdf": False,
        "maxReferences": 14,
    },
    "gemini-3.1-flash-image": {
        "resolutions": ["512", "1K", "2K", "4K"],
        "groundingModes": ["Off", "Web", "Image", "Web+Img"],
        "panoramicAspects": True,
        "thinkingLevels": ["minimal", "high"],
        "defaultThinkingLevel": "minimal",
        "supportsVideoAndPdf": True,
        "maxReferences": 14,
    },
    "gemini-3.1-flash-lite-image": {
        "resolutions": ["1K"],
        "groundingModes": ["Off"],
        "panoramicAspects": False,
        "thinkingLevels": ["minimal", "high"],
        "defaultThinkingLevel": "minimal",
        "supportsVideoAndPdf": True,
        "maxReferences": 14,
    },
    "default": {
        "resolutions": ["1K"],
        "groundingModes": ["Off"],
        "panoramicAspects": False,
        "thinkingLevels": None,
        "supportsVideoAndPdf": False,
        "maxReferences": 14,
    },
}

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
    rows.append(
        '<button type="button" id="nsNewTemplateBtn" class="ns-tpl-new" '
        'onclick="window.TinCanNodeStudio.addCustomTemplate()">'
        "<span>+ New Template</span></button>"
    )
    return "".join(rows)


def _render_model_menu_items_html() -> str:
    items: List[str] = []
    for idx, m in enumerate(AVAILABLE_MODELS):
        mid = _html.escape(m["id"], quote=True)
        active_cls = " is-selected" if idx == 0 else ""
        items.append(
            f'<button type="button" class="ns-model-opt{active_cls}" data-model-id="{mid}" '
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
    z-index: 50;
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

  /* Stage 2: MessageContent (280x160) */
  .ns-msg-card {
    width: 100%;
    height: 100%;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    background: var(--ns-card);
  }
  .ns-msg-head { display: flex; align-items: center; gap: 6px; font-family: var(--ns-mono); font-size: 10px; font-weight: 700; color: var(--ns-muted); text-transform: uppercase; }
  .ns-msg-body { font-size: 12px; line-height: 1.45; color: var(--ns-ink); overflow-y: auto; flex: 1 1 auto; white-space: pre-wrap; }

  /* Stage 3: Image Node */
  .ns-img-node { position: relative; width: 100%; height: 100%; background: var(--ns-paper); }
  .ns-img-node img { width: 100%; height: 100%; object-fit: cover; display: block; }
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

  .ns-model-menu { width: 360px; padding: 5px; gap: 2px; }
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
    z-index: 10;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 70px 24px 32px;
    background-color: var(--ns-bg);
    background-image: radial-gradient(rgba(17, 17, 17, 0.24) 1px, transparent 1px);
    background-size: 24px 24px;
  }
  .ns-alt-view.hidden { display: none; }
  .ns-alt-card {
    width: 100%;
    max-width: 720px;
    background: var(--ns-card);
    border: var(--ns-hair);
    border-radius: 14px;
    padding: 20px;
    box-shadow: var(--ns-shadow);
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .ns-alt-title { margin: 0; font-size: 18px; font-weight: 600; }
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

  /* Code / Terminal Drawers & CLI Consoles (#000000 background with 1.5px solid #ffffff border) */
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
</style>"""


def _node_studio_js(initial_view: str) -> str:
    models_json = _safe_json(list(AVAILABLE_MODELS))
    caps_json = _safe_json(MODEL_CAPABILITIES)
    std_aspects_json = _safe_json(list(STANDARD_ASPECT_RATIOS))
    pano_aspects_json = _safe_json(list(PANORAMIC_ASPECT_RATIOS))
    filters_json = _safe_json(list(FILTER_PRESETS))
    templates_json = _safe_json(list(LUMINA_TEMPLATES))
    assets_json = _safe_json(list(LUMINA_ASSETS))

    template = r"""<script id="nodeStudioUiScript">
(function () {
  const MODELS = __MODELS_JSON__;
  const CAPS = __CAPS_JSON__;
  const STD_ASPECTS = __STD_ASPECTS_JSON__;
  const PANO_ASPECTS = __PANO_ASPECTS_JSON__;
  const FILTER_PRESETS = __FILTERS_JSON__;
  const TEMPLATES = __TEMPLATES_JSON__;
  const ASSETS = __ASSETS_JSON__;
  const MAX_CONCURRENT_RUNS = 2;

  const state = {
    view: __INIT_VIEW__,
    nodes: [],
    edges: [],
    selectedIds: [],
    references: [],
    model: "gemini-nano-banana-2.1",
    aspectRatio: "1:1",
    resolution: "1K",
    thinkingLevel: "medium",
    includeThoughts: false,
    groundingMode: "Off",
    provider: "auto",
    activeRuns: 0,
    activeConversationNodeId: null,
    apiKey: "",
    nanogptKey: "",
    serverStatus: { hasServerKey: false, hasGeminiKey: false, hasNanogptKey: false },
    panX: 0,
    panY: 0,
    zoom: 1,
    isPanning: false,
    panStart: { x: 0, y: 0 },
    dragNodeId: null,
    dragNodeOffset: { x: 0, y: 0 },
    isBoxSelecting: false,
    boxStart: { x: 0, y: 0 },
    connectFromId: null,
    metaHeld: false,
    isShortcutsPinned: false,
    isLeftCollapsed: true,
    pillPos: { x: 10, y: 240 },
    isDraggingPill: false,
    pillOffset: { x: 0, y: 0 },
    dragRefIndex: null,
    openFilterNodeId: null,
    sections: { references: true, assets: true, templates: false },
    libRefs: [],
    templates: TEMPLATES.slice(),
    nodeSeq: 0
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

  function deriveMode() {
    if (state.references.length > 1 || state.selectedIds.length > 1) return "MERGE";
    if (state.references.length === 1 || state.selectedIds.length === 1) return "EDIT";
    return "GENERATE";
  }

  function syncCapabilitiesAndControls() {
    const caps = getCaps();
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

    const aspectSel = $("nsAspectSelect");
    if (aspectSel) {
      aspectSel.innerHTML = aspects.map((a) => '<option value="' + a + '">' + a + "</option>").join("");
      aspectSel.value = state.aspectRatio;
    }
    const aspectVal = $("nsAspectVal");
    if (aspectVal) aspectVal.textContent = state.aspectRatio;

    const resSel = $("nsResSelect");
    if (resSel) {
      resSel.innerHTML = caps.resolutions.map((r) => '<option value="' + r + '">' + r + "</option>").join("");
      resSel.value = state.resolution;
    }
    const resVal = $("nsResVal");
    if (resVal) resVal.textContent = state.resolution;
    const resWrap = $("nsResWrap");
    if (resWrap) resWrap.classList.toggle("is-disabled", caps.resolutions.length <= 1);

    const thinkWrap = $("nsThinkWrap");
    const thoughtsBtn = $("nsThoughtsBtn");
    if (thinkWrap) thinkWrap.classList.toggle("is-disabled", !caps.thinkingLevels);
    if (thoughtsBtn) {
      thoughtsBtn.classList.toggle("hidden", !caps.thinkingLevels);
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
    if (searchWrap) searchWrap.classList.toggle("is-disabled", caps.groundingModes.length <= 1);
    const searchSel = $("nsSearchSelect");
    if (searchSel) {
      searchSel.innerHTML = caps.groundingModes.map((g) => '<option value="' + g + '">' + g + "</option>").join("");
      searchSel.value = state.groundingMode;
    }
    const searchVal = $("nsSearchVal");
    if (searchVal) searchVal.textContent = state.groundingMode;

    const viaVal = $("nsViaVal");
    if (viaVal) viaVal.textContent = state.provider;

    const refCounter = $("nsRefCounter");
    if (refCounter) {
      refCounter.textContent = state.references.length + "/" + caps.maxReferences +
        (caps.supportsVideoAndPdf ? " refs (Img/Vid/PDF)" : " refs");
    }

    const promptInput = $("nsPromptInput");
    if (promptInput) {
      promptInput.placeholder = state.references.length > 0
        ? "Describe how to change or combine these references..."
        : "Describe what you want to generate...";
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
    const genBtn = $("nsGenerateBtn");
    if (genBtn) genBtn.disabled = !hasPrompt || state.activeRuns >= MAX_CONCURRENT_RUNS;
  }

  function renderReferencesStrip() {
    const strip = $("nsRefsStrip");
    const row = $("nsRefsRow");
    const attachTrigger = $("nsAttachTrigger");
    if (!strip || !row) return;

    strip.classList.toggle("has-refs", state.references.length > 0);
    if (attachTrigger) attachTrigger.classList.toggle("hidden", state.references.length > 0);

    const chips = state.references.map((ref, idx) => {
      let inner = "";
      if (ref.type === "image" && ref.url) {
        inner = '<img src="' + escapeHtml(ref.url) + '" alt="' + escapeHtml(ref.name) + '">';
      } else {
        const badge = ref.type === "pdf" ? "PDF" : (ref.type === "video" ? "VIDEO" : ref.type.toUpperCase());
        inner = '<div class="ns-ref-badge-box"><strong>' + escapeHtml(badge) + '</strong><span>' + escapeHtml(ref.name) + "</span></div>";
      }
      return '<div class="ns-ref-chip" draggable="true" data-ref-index="' + idx + '" title="' + escapeHtml(ref.name) + '">' +
        inner +
        '<button type="button" class="ns-ref-remove" onclick="window.TinCanNodeStudio.removeRef(\'' + escapeHtml(ref.id) + '\')">×</button>' +
        "</div>";
    });

    if (state.references.length > 0) {
      chips.push(
        '<button type="button" class="ns-ref-slot-btn" title="Add more references" onclick="window.TinCanNodeStudio.triggerFileInput()">+</button>'
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
    const selectedNodes = state.nodes.filter((n) => state.selectedIds.indexOf(n.id) !== -1);
    const nextRefs = [];
    selectedNodes.forEach((n) => {
      if (n.content && (n.content.imageUrl || n.content.base64)) {
        nextRefs.push({
          id: n.id,
          url: n.content.imageUrl || "",
          base64: n.content.base64 || "",
          mimeType: n.content.mimeType || "image/png",
          name: n.label || n.id,
          type: "image"
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
      const w = mStatus === "generating" ? 96 : (mStatus === "message" ? 280 : (node.width || 256));
      const h = mStatus === "generating" ? 96 : (mStatus === "message" ? 160 : (node.height || 256));
      node.width = w;
      node.height = h;

      let inner = "";
      if (mStatus === "generating") {
        inner =
          '<div class="ns-living-cube-wrap">' +
          '<div class="ns-living-cube"><div class="ns-living-ring"><div class="ns-living-core"></div></div></div>' +
          '<div class="ns-living-label">Generating...</div></div>';
      } else if (mStatus === "message") {
        inner =
          '<div class="ns-msg-card">' +
          '<div class="ns-msg-head"><span>Gemini</span></div>' +
          '<div class="ns-msg-body">' + escapeHtml((node.content && node.content.text) || node.label) + "</div>" +
          "</div>";
      } else {
        const imgUrl = node.content && node.content.imageUrl;
        const imgStyle = "filter:" + buildFilterCss(node.filters) + ";";
        inner =
          '<div class="ns-img-node">' +
          '<span class="ns-node-type-badge">' + escapeHtml(node.type || "GENERATED") + "</span>" +
          (imgUrl ? '<button type="button" class="ns-node-dl-btn" title="Download" onclick="event.stopPropagation();window.TinCanNodeStudio.downloadNode(\'' + escapeHtml(node.id) + '\')">↓</button>' : "") +
          (imgUrl
            ? '<img src="' + escapeHtml(imgUrl) + '" alt="' + escapeHtml(node.label) + '" style="' + imgStyle + '" draggable="false">'
            : '<div class="ns-msg-card"><div class="ns-msg-body">' + escapeHtml((node.content && node.content.text) || node.label) + "</div></div>") +
          '<div class="ns-node-meta-overlay">' +
          '<div class="ns-node-prompt-txt">' + escapeHtml((node.metadata && node.metadata.prompt) || node.label) + "</div>" +
          '<div class="ns-node-sub-txt"><span>' + escapeHtml((node.metadata && node.metadata.resolution) || "1K") +
          '</span><span>' + escapeHtml((node.metadata && node.metadata.model) || "Nano Banana 2.1") + "</span></div>" +
          "</div></div>";
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

      const quickBar = mStatus !== "generating"
        ? ('<div class="ns-node-quickbar" onclick="event.stopPropagation()">' +
           '<button type="button" class="ns-qact-btn" onclick="window.TinCanNodeStudio.addNodeAsRef(\'' + escapeHtml(node.id) + '\')">+ Ref</button>' +
           '<span class="ns-qact-sep"></span>' +
           '<button type="button" class="ns-qact-btn" onclick="window.TinCanNodeStudio.editNode(\'' + escapeHtml(node.id) + '\')">Edit</button>' +
           '<button type="button" class="ns-qact-btn" onclick="window.TinCanNodeStudio.openFilterPopover(\'' + escapeHtml(node.id) + '\')">Filter</button>' +
           '<button type="button" class="ns-qact-btn" onclick="window.TinCanNodeStudio.duplicateNode(\'' + escapeHtml(node.id) + '\')">Copy</button>' +
           '<button type="button" class="ns-qact-btn" onclick="window.TinCanNodeStudio.downloadNode(\'' + escapeHtml(node.id) + '\')">Download</button>' +
           '<span class="ns-qact-sep"></span>' +
           '<button type="button" class="ns-qact-btn is-danger" onclick="window.TinCanNodeStudio.deleteNode(\'' + escapeHtml(node.id) + '\')">Delete</button>' +
           "</div>")
        : "";

      return '<div id="nsCanvasNode-' + escapeHtml(node.id) + '" class="ns-canvas-node' + (isSel ? " is-selected" : "") + '" ' +
        'data-node-id="' + escapeHtml(node.id) + '" ' +
        'style="left:' + node.x + "px;top:" + node.y + "px;width:" + w + "px;height:" + h + 'px;">' +
        '<div class="ns-node-handle ns-node-handle--top" data-handle="top" data-node-id="' + escapeHtml(node.id) + '"></div>' +
        '<div class="ns-node-handle ns-node-handle--bottom" data-handle="bottom" data-node-id="' + escapeHtml(node.id) + '"></div>' +
        quickBar + filterPop +
        '<div class="ns-morph-card">' + inner + "</div>" +
        "</div>";
    }).join("");

    renderEdges();
    renderLibraryViewGrid();
  }

  function renderLibraryViewGrid() {
    const grid = $("nsLibraryViewGrid");
    if (!grid) return;
    if (!state.nodes.length) {
      grid.innerHTML = '<div class="ns-alt-desc">No generated assets yet. Generate or drop images in Editor view to populate your Asset Library.</div>';
      return;
    }
    grid.innerHTML = state.nodes.map((n) =>
      '<div class="ns-asset-card" onclick="window.TinCanNodeStudio.switchView(\'nodes\')">' +
      '<div class="ns-asset-thumb">' +
      (n.content && n.content.imageUrl ? '<img src="' + escapeHtml(n.content.imageUrl) + '" style="width:100%;height:100%;object-fit:cover;border-radius:5px;">' : '<span>TEXT</span>') +
      '</div><div class="ns-asset-name">' + escapeHtml(n.label || n.id) + "</div></div>"
    ).join("");
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
  }

  function autoLayout() {
    if (!state.nodes.length) return;
    const roots = state.nodes.filter((n) => !state.edges.some((e) => e.target === n.id));
    const levels = {};
    const queue = (roots.length ? roots : [state.nodes[0]]).map((n) => ({ id: n.id, lvl: 0 }));
    while (queue.length) {
      const cur = queue.shift();
      if (levels[cur.id] !== undefined && levels[cur.id] >= cur.lvl) continue;
      levels[cur.id] = cur.lvl;
      state.edges.filter((e) => e.source === cur.id).forEach((e) => {
        queue.push({ id: e.target, lvl: cur.lvl + 1 });
      });
    }
    const byLvl = {};
    state.nodes.forEach((n) => {
      const lvl = levels[n.id] || 0;
      if (!byLvl[lvl]) byLvl[lvl] = [];
      byLvl[lvl].push(n);
    });
    Object.keys(byLvl).forEach((lvlStr) => {
      const lvl = parseInt(lvlStr, 10);
      const list = byLvl[lvlStr];
      const totalW = list.reduce((acc, n) => acc + (n.width || 256) + 40, -40);
      let cursorX = 480 - totalW / 2;
      list.forEach((n) => {
        n.x = Math.round(cursorX);
        n.y = 90 + lvl * 310;
        cursorX += (n.width || 256) + 40;
      });
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

  function zoomBy(factor) {
    state.zoom = Math.max(0.1, Math.min(3.0, Number((state.zoom * factor).toFixed(2))));
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
    copy.x = orig.x + 40;
    copy.y = orig.y + 40;
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
    if (!node || !node.content || !node.content.imageUrl) return;
    const a = document.createElement("a");
    a.href = node.content.imageUrl;
    a.download = (node.label || "node") + ".png";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  function addFilesToRefs(fileList) {
    const caps = getCaps();
    const files = Array.from(fileList || []);
    files.forEach((file) => {
      if (state.references.length >= caps.maxReferences) return;
      const mime = file.type || (file.name.toLowerCase().endsWith(".pdf") ? "application/pdf" : "image/png");
      const rType = mime === "application/pdf" ? "pdf" : (mime.indexOf("video/") === 0 ? "video" : "image");
      if (!caps.supportsVideoAndPdf && rType !== "image") return;
      const url = typeof URL !== "undefined" && URL.createObjectURL ? URL.createObjectURL(file) : "";
      state.references.push({
        id: "ref-" + Date.now() + "-" + Math.random().toString(16).slice(2, 6),
        url: url,
        name: file.name,
        type: rType,
        mimeType: mime,
        size: file.size
      });
    });
    renderReferencesStrip();
  }

  function addImageFilesToCanvas(fileList, clientX, clientY) {
    const canvas = $("nsDotCanvas");
    const rect = canvas ? canvas.getBoundingClientRect() : { left: 0, top: 0 };
    const flowX = (clientX - rect.left - state.panX) / state.zoom;
    const flowY = (clientY - rect.top - state.panY) / state.zoom;
    Array.from(fileList || []).forEach((file, idx) => {
      if (!file.type || file.type.indexOf("image/") !== 0) return;
      const reader = new FileReader();
      reader.onload = function () {
        state.nodeSeq += 1;
        state.nodes.push({
          id: "uploaded-" + state.nodeSeq,
          type: "UPLOADED",
          morphingStatus: "image",
          label: file.name,
          x: Math.round(flowX + idx * 24),
          y: Math.round(flowY + idx * 24),
          width: 256,
          height: 256,
          content: { imageUrl: String(reader.result || ""), mimeType: file.type },
          metadata: { resolution: "1024x1024", model: "Uploaded", prompt: "Uploaded: " + file.name },
          filters: {}
        });
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
    state.nodes.push({
      id: nid,
      type: "UPLOADED",
      morphingStatus: "message",
      label: asset.name,
      x: 320 + (state.nodeSeq * 25) % 240,
      y: 120 + (state.nodeSeq * 25) % 160,
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
    const prompt = promptEl ? promptEl.value.trim() : "";
    if (!prompt || state.activeRuns >= MAX_CONCURRENT_RUNS) return;

    state.activeRuns += 1;
    renderPromptIslandStatus();
    showToast("", false);

    const mode = deriveMode();
    state.nodeSeq += 1;
    const parentIds = state.selectedIds.slice();
    const newId = (mode === "EDIT" && parentIds.length === 1)
      ? (parentIds[0] + ".n" + state.nodeSeq)
      : ("node-" + state.nodeSeq);

    const newNode = {
      id: newId,
      type: mode === "MERGE" ? "MERGED" : (mode === "EDIT" ? "EDITED" : "GENERATED"),
      morphingStatus: "generating",
      label: prompt,
      x: 420 + (state.nodeSeq % 3) * 40,
      y: 120 + (parentIds.length ? 280 : 0),
      width: 96,
      height: 96,
      content: {},
      metadata: { prompt: prompt, model: state.model, resolution: state.resolution, conversationHistory: [] },
      filters: {}
    };
    state.nodes.push(newNode);
    parentIds.forEach((pid) => {
      state.edges.push({ id: "e-" + pid + "-" + newId, source: pid, target: newId });
    });
    state.selectedIds = [newId];
    renderNodes();

    const headers = { "Content-Type": "application/json" };
    if (state.apiKey) headers["X-Gemini-Api-Key"] = state.apiKey;
    if (state.nanogptKey) headers["X-NanoGPT-Api-Key"] = state.nanogptKey;

    const payload = {
      prompt: prompt,
      modality: "image",
      selectedNodeIds: parentIds,
      references: state.references.map((r) => ({ id: r.id, name: r.name, type: r.type, url: r.url, base64: r.base64, mimeType: r.mimeType })),
      config: {
        model: state.model,
        aspectRatio: state.aspectRatio,
        resolution: state.resolution,
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
      if (data.image && data.image.data && !newNode.content.imageUrl) {
        newNode.content.imageUrl = "data:" + (data.image.mimeType || "image/png") + ";base64," + data.image.data;
      }
      newNode.morphingStatus = newNode.content.imageUrl ? "image" : "message";
      newNode.width = newNode.morphingStatus === "image" ? 256 : 280;
      newNode.height = newNode.morphingStatus === "image" ? 256 : 160;
      if (rData.metadata) newNode.metadata = Object.assign(newNode.metadata, rData.metadata);
      if (newNode.content.text) showToast(newNode.content.text, false);
    } catch (err) {
      newNode.morphingStatus = "message";
      newNode.width = 280;
      newNode.height = 160;
      newNode.content = { text: prompt + " (staged locally)" };
      if (err && err.message && err.message.indexOf("Failed to fetch") === -1) {
        showToast(err.message, true);
      }
    } finally {
      state.activeRuns = Math.max(0, state.activeRuns - 1);
      if (promptEl) promptEl.value = "";
      renderNodes();
      renderPromptIslandStatus();
    }
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
        ev.preventDefault();
        zoomBy(ev.deltaY < 0 ? 1.08 : 0.92);
      }, { passive: false });

      canvas.addEventListener("mousedown", (ev) => {
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

    const promptEl = $("nsPromptInput");
    if (promptEl) {
      promptEl.addEventListener("input", () => {
        promptEl.style.height = "auto";
        promptEl.style.height = Math.min(promptEl.scrollHeight, 200) + "px";
        renderPromptIslandStatus();
      });
      promptEl.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter" && !ev.shiftKey) {
          ev.preventDefault();
          generate();
        }
      });
    }

    document.addEventListener("keydown", (ev) => {
      if (ev.metaKey || ev.ctrlKey) {
        state.metaHeld = true;
        const ci = $("nsCopyIndicator");
        if (ci) ci.classList.remove("hidden");
      }
      const tag = ev.target && ev.target.tagName ? ev.target.tagName.toLowerCase() : "";
      if (tag === "input" || tag === "textarea" || tag === "select") {
        if ((ev.metaKey || ev.ctrlKey) && ev.key === "Enter") {
          ev.preventDefault();
          generate();
        }
        return;
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
    });
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
    selectModel: function (mid) {
      state.model = mid;
      const m = $("nsModelMenu");
      if (m) m.classList.add("hidden");
      syncCapabilitiesAndControls();
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
      state[key] = val;
      syncCapabilitiesAndControls();
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
        for r in ("1K", "2K", "4K")
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
        for v in ("auto", "gemini", "nanogpt")
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

  <!-- Chat View (ConversationView) -->
  <section id="nsConversationView" class="ns-alt-view{" hidden" if active_view != "conversation" else ""}" aria-label="Conversation Editor">
    <div class="ns-alt-card">
      <h2 class="ns-alt-title">Conversation Editor</h2>
      <p class="ns-alt-desc">Interact with Gemini and NanoGPT using the tree-based conversation context synced directly with your canvas nodes.</p>
    </div>
  </section>

  <!-- Library View (LibraryView) -->
  <section id="nsLibraryView" class="ns-alt-view{" hidden" if active_view != "library" else ""}" aria-label="Asset Library">
    <div class="ns-alt-card">
      <h2 class="ns-alt-title">Asset Library</h2>
      <p class="ns-alt-desc">Browse generated assets and conversation history from your Node Studio session.</p>
      <div id="nsLibraryViewGrid" class="ns-asset-grid"></div>
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
    <div id="nsShortcutsPopover" class="ns-shortcuts-popover hidden"
      onmouseenter="window.TinCanNodeStudio.toggleShortcutsPopover(false)"
      onmouseleave="window.TinCanNodeStudio.hideShortcutsIfUnpinned()">
      <div class="ns-shortcuts-title">Keyboard Shortcuts</div>
      <div class="ns-shortcut-line"><span>Delete nodes</span><span>Delete / Backspace</span></div>
      <div class="ns-shortcut-line"><span>Auto-layout</span><span>⌘/Ctrl + A</span></div>
      <div class="ns-shortcut-line"><span>Select all nodes</span><span>A</span></div>
      <div class="ns-shortcut-line"><span>Fit view</span><span>F</span></div>
      <div class="ns-shortcut-line"><span>Invert image selection</span><span>I</span></div>
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
            <span class="ns-lib-ref-label">DROP OR CLICK</span>
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
          <input id="nsAssetSearchInput" type="text" class="ns-asset-search" placeholder="Search assets..." oninput="window.TinCanNodeStudio.filterAssets(this.value)">
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
        <div class="ns-island-top">
          <div class="ns-island-badges">
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
          <button id="nsAttachTrigger" type="button" class="ns-attach-trigger" title="Attach references (Images, Video, PDF — up to 14)" onclick="window.TinCanNodeStudio.triggerFileInput()">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
            </svg>
          </button>
          <input id="nsFileInput" type="file" class="ns-hidden-input" multiple accept="image/*,video/*,application/pdf" onchange="window.TinCanNodeStudio.handleFilesSelected(this.files);this.value='';">
        </div>

        <div class="ns-action-bar">
          <div class="ns-settings-group">
            <div class="ns-setting-wrap">
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
    "MODEL_CAPABILITIES",
    "PANORAMIC_ASPECT_RATIOS",
    "STANDARD_ASPECT_RATIOS",
    "render_node_studio_html",
    "render_node_studio_window_html",
]
