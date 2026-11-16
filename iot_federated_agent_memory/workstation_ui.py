"""TinCan Mesh OS: Aeonik Celadon & Ink 3-Pane Workstation Studio window.

Exports ``render_workstation_window_html() -> str`` for ``#win-workstation``,
combining multi-gateway AI routing (NanoGPT TEE Private, NanoGPT Heretic,
OpenRouter), Hyper3D Rodin 3D GLB generation + lazy ``<model-viewer>`` with
isometric SVG wireframe fallback, Space Notes TEE Audit & Diff (propose /
commit / revert), Arena side-by-side benchmarking, and live telemetry/handoff.

All styling is scoped under ``#win-workstation`` using the Aeonik Celadon & Ink
palette (``#ecf1e6``, ``#f4f8f0``, ``#ffffff``, ``#111111``, ``#107a47``,
``#8a1c1c``) with zero legacy dark slate or neon utility classes.
"""

from __future__ import annotations

import html as _html
import json
import re as _re
from typing import Any, Dict, List, Tuple

# (key, label, badge_text, badge_kind, privacy_mode_label)
GATEWAY_DEFS: Tuple[Tuple[str, str, str, str, str], ...] = (
    ("tee", "TEE Private", "ATTESTED", "attested", "TEE Hardware Enclave"),
    ("heretic", "Heretic", "UNCENSORED", "uncensored", "Heretic Uncensored"),
    ("openrouter", "OpenRouter", "POOLED", "pooled", "OpenRouter Pooled"),
)

# (key, label, default_target_hint)
MODE_DEFS: Tuple[Tuple[str, str, str], ...] = (
    ("3d", "3D Rodin Stage", "/models3d/studio_mesh.glb"),
    ("audit", "TEE Audit & Diff", "/notes/tee_audit.patch"),
    ("arena", "Arena Benchmark", "/notes/arena_benchmark.md"),
)

# (tier_id, price_usd)
RODIN_TIERS: Tuple[Tuple[str, float], ...] = (
    ("Sketch", 0.25),
    ("Regular", 0.50),
    ("Smooth", 0.75),
    ("Detail", 1.00),
)

COST_CAP_OPTIONS: Tuple[float, ...] = (0.25, 0.50, 0.75, 1.00, 1.50)

FALLBACK_MODELS: Dict[str, List[Dict[str, Any]]] = {
    "tee": [
        {
            "id": "nanogpt/TEE/deepseek-v4.1-flash",
            "name": "NanoGPT Private/TEE DeepSeek V4.1 Flash",
            "context_length": 1048576,
            "pricing": {"prompt_per_1m": 0.375, "completion_per_1m": 1.50},
            "category": "Private/TEE",
        },
        {
            "id": "nanogpt/TEE/gemma-4-26b-a4b-uncensored",
            "name": "NanoGPT Private/TEE Gemma 4 26B Uncensored",
            "context_length": 65536,
            "pricing": {"prompt_per_1m": 0.15, "completion_per_1m": 0.70},
            "category": "Private/TEE",
        },
    ],
    "heretic": [
        {
            "id": "nanogpt/pqhaz/DeepSeek-V4.1-Flash-1017-heretic",
            "name": "NanoGPT DeepSeek V4.1 Flash Heretic",
            "context_length": 512000,
            "pricing": {"prompt_per_1m": 0.198, "completion_per_1m": 0.792},
            "category": "Uncensored",
        },
        {
            "id": "nanogpt/Gemma-4-31B-Gembrain-uncensored-heretic",
            "name": "NanoGPT Gemma 4 31B Gembrain Heretic",
            "context_length": 262144,
            "pricing": {"prompt_per_1m": 0.306, "completion_per_1m": 0.306},
            "category": "Uncensored",
        },
        {
            "id": "nanogpt/abliteration-ai/abliterated-model-large-v2",
            "name": "NanoGPT Abliterated Large V2",
            "context_length": 1000000,
            "pricing": {"prompt_per_1m": 3.00, "completion_per_1m": 5.00},
            "category": "Uncensored",
        },
    ],
    "openrouter": [
        {
            "id": "anthropic/claude-3.7-sonnet",
            "name": "Anthropic Claude 3.7 Sonnet",
            "context_length": 200000,
            "pricing": {"prompt": "0.000003", "completion": "0.000015"},
            "category": "Advanced Reasoning",
        },
        {
            "id": "google/gemini-2.5-flash",
            "name": "Google Gemini 2.5 Flash",
            "context_length": 1048576,
            "pricing": {"prompt": "0.00000015", "completion": "0.0000006"},
            "category": "Fast Reasoning",
        },
        {
            "id": "deepseek/deepseek-r1",
            "name": "DeepSeek R1",
            "context_length": 128000,
            "pricing": {"prompt": "0.00000055", "completion": "0.00000219"},
            "category": "Deep Reasoning",
        },
    ],
}


def _safe_json_for_script(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=True).replace("</", "<\\/")


def _render_gateway_tabs() -> str:
    parts = []
    for idx, (gw_id, label, _badge, _kind, _priv) in enumerate(GATEWAY_DEFS):
        active = " is-active" if idx == 0 else ""
        selected = "true" if idx == 0 else "false"
        parts.append(
            f'<button id="wsGwBtn-{gw_id}" type="button" role="tab" aria-selected="{selected}" '
            f'data-ws-gateway="{gw_id}" class="ws-seg-btn{active}" '
            f'onclick="window.TinCanWorkstation && window.TinCanWorkstation.switchGateway(\'{gw_id}\')">'
            f"{_html.escape(label)}</button>"
        )
    return "".join(parts)


def _render_cost_options() -> str:
    parts = []
    for cap in COST_CAP_OPTIONS:
        val = f"{cap:.2f}"
        sel = " selected" if abs(cap - 0.50) < 1e-6 else ""
        parts.append(f'<option value="{val}"{sel}>${val}</option>')
    return "".join(parts)


def _render_mode_tabs() -> str:
    parts = []
    for idx, (mode_id, label, _hint) in enumerate(MODE_DEFS):
        active = " is-active" if idx == 0 else ""
        selected = "true" if idx == 0 else "false"
        parts.append(
            f'<button id="wsModeBtn-{mode_id}" type="button" role="tab" aria-selected="{selected}" '
            f'data-ws-mode="{mode_id}" class="ws-seg-btn{active}" '
            f'onclick="window.TinCanWorkstation && window.TinCanWorkstation.switchMode(\'{mode_id}\')">'
            f"{_html.escape(label)}</button>"
        )
    return "".join(parts)


def _render_rodin_tiers() -> str:
    parts = []
    for tier_id, price in RODIN_TIERS:
        active = " is-active" if tier_id == "Regular" else ""
        checked = "true" if tier_id == "Regular" else "false"
        p_str = f"{price:.2f}"
        parts.append(
            f'<button id="wsTierBtn-{tier_id}" type="button" role="radio" aria-checked="{checked}" '
            f'data-ws-tier="{tier_id}" data-price="{p_str}" class="ws-pill ws-tier-pill{active}">'
            f"{_html.escape(tier_id)} ${p_str}</button>"
        )
    return "".join(parts)


def _render_arena_column(side: str, subtitle: str, default_model: str, default_name: str) -> str:
    return f"""
                <div class="ws-arena-col" data-ws-arena-side="{side}" id="wsArenaCol{side}">
                  <div class="ws-arena-col-head">
                    <div class="ws-arena-col-title">
                      <span class="ws-arena-tag">Model {side}</span>
                      <span class="ws-muted-xs">{_html.escape(subtitle)}</span>
                    </div>
                    <span id="wsArenaLabel{side}" class="ws-mono-xs ws-truncate">{_html.escape(default_model)}</span>
                  </div>
                  <div id="wsArenaOut{side}" class="ws-arena-out" aria-live="polite">Ready to benchmark {_html.escape(default_name)}. Enter a prompt in Directive and click Dispatch Run or Run Benchmark.</div>
                  <div class="ws-arena-col-foot">
                    <span id="wsArenaMeta{side}" class="ws-mono-xs ws-muted">-- tok · -- ms · $0.0000</span>
                    <button id="wsArenaVote{side}" type="button" class="ws-btn ws-btn--sm" data-ws-vote="{side}">
                      <span>Vote Model {side}</span>
                      <span id="wsArenaXp{side}" class="ws-xp-badge">+150 XP</span>
                    </button>
                  </div>
                </div>"""


def _workstation_css() -> str:
    raw = r"""      <style id="workstationUiCss">
        /* TinCan 3D Studio: Aeonik Celadon & Ink (#ecf1e6 / #f4f8f0 / #ffffff / #111111) */
        #win-workstation {
          --ws-bg: #ecf1e6;
          --ws-card: #f4f8f0;
          --ws-paper: #ffffff;
          --ws-ink: #111111;
          --ws-muted: #4a4a4a;
          --ws-faint: #5c5c5c;
          --ws-pos: #107a47;
          --ws-pos-bg: rgba(16, 122, 71, 0.09);
          --ws-danger: #8a1c1c;
          --ws-danger-bg: rgba(138, 28, 28, 0.08);
          --ws-hair: 1px solid #111111;
          --ws-hair-soft: 1px solid rgba(17, 17, 17, 0.16);
          --ws-font: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          --ws-mono: "JetBrains Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace;
        }
        #win-workstation .hidden { display: none !important; }
        #win-workstation .ws-body {
          display: flex;
          flex-direction: column;
          height: min(740px, calc(100vh - 140px));
          min-height: 440px;
          overflow: hidden;
          padding: 0;
          background: var(--ws-bg);
          color: var(--ws-ink);
          font-family: var(--ws-font);
          font-size: 12px;
          container-type: inline-size;
          container-name: wsbody;
        }
        #win-workstation.maximized .ws-body,
        #win-workstation.popout-fullscreen .ws-body {
          height: 100%;
          max-height: none;
        }
        #win-workstation .ws-topbar {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          justify-content: space-between;
          gap: 8px 12px;
          padding: 7px 12px;
          background: var(--ws-card);
          border-bottom: var(--ws-hair);
          flex: 0 0 auto;
        }
        #win-workstation .ws-top-group {
          display: inline-flex;
          flex-wrap: wrap;
          align-items: center;
          gap: 6px;
          min-width: 0;
        }
        #win-workstation .ws-kicker {
          font-size: 10px;
          font-weight: 700;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: var(--ws-ink);
        }
        #win-workstation .ws-mono { font-family: var(--ws-mono); }
        #win-workstation .ws-mono-xs { font-family: var(--ws-mono); font-size: 10px; line-height: 1.4; }
        #win-workstation .ws-muted { color: var(--ws-muted); }
        #win-workstation .ws-muted-xs { font-size: 10px; color: var(--ws-faint); }
        #win-workstation .ws-truncate {
          min-width: 0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        /* Pills, buttons, segments */
        #win-workstation .ws-pill {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          padding: 2px 10px;
          border: var(--ws-hair);
          border-radius: 9999px;
          background: var(--ws-paper);
          color: var(--ws-ink);
          font-family: var(--ws-mono);
          font-size: 10px;
          font-weight: 600;
          line-height: 1.45;
          white-space: nowrap;
          cursor: pointer;
          transition: background 120ms ease, color 120ms ease, opacity 120ms ease;
        }
        #win-workstation button.ws-pill:hover { background: rgba(17, 17, 17, 0.08); }
        #win-workstation button.ws-pill.is-active { background: var(--ws-ink); color: var(--ws-bg); }
        #win-workstation .ws-badge {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 1px 8px;
          border: var(--ws-hair);
          border-radius: 9999px;
          background: var(--ws-paper);
          color: var(--ws-ink);
          font-family: var(--ws-mono);
          font-size: 10px;
          font-weight: 600;
          letter-spacing: 0.03em;
          white-space: nowrap;
        }
        #win-workstation .ws-badge--pos {
          border-color: var(--ws-pos);
          background: var(--ws-pos-bg);
          color: var(--ws-pos);
        }
        #win-workstation .ws-badge--ink {
          border-color: var(--ws-ink);
          background: var(--ws-ink);
          color: var(--ws-bg);
        }
        #win-workstation .ws-badge--danger {
          border-color: var(--ws-danger);
          background: var(--ws-danger-bg);
          color: var(--ws-danger);
        }
        #win-workstation .ws-seg {
          display: inline-flex;
          align-items: stretch;
          width: 100%;
          border: var(--ws-hair);
          border-radius: 9999px;
          overflow: hidden;
          background: var(--ws-paper);
        }
        #win-workstation .ws-seg--auto { width: auto; }
        #win-workstation .ws-seg-btn {
          flex: 1 1 0;
          padding: 4px 10px;
          border: 0;
          background: transparent;
          color: var(--ws-ink);
          font-family: var(--ws-font);
          font-size: 11px;
          font-weight: 600;
          white-space: nowrap;
          cursor: pointer;
          transition: background 120ms ease, color 120ms ease;
        }
        #win-workstation .ws-seg--auto .ws-seg-btn { flex: 0 0 auto; }
        #win-workstation .ws-seg-btn:hover { background: rgba(17, 17, 17, 0.07); }
        #win-workstation .ws-seg-btn.is-active { background: var(--ws-ink); color: var(--ws-bg); }

        #win-workstation .ws-btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          padding: 5px 12px;
          border: var(--ws-hair);
          border-radius: 9999px;
          background: var(--ws-paper);
          color: var(--ws-ink);
          font-family: var(--ws-font);
          font-size: 11px;
          font-weight: 600;
          line-height: 1.3;
          white-space: nowrap;
          cursor: pointer;
          transition: background 120ms ease, color 120ms ease, opacity 120ms ease;
        }
        #win-workstation .ws-btn:hover { background: var(--ws-ink); color: var(--ws-bg); }
        #win-workstation .ws-btn:disabled { opacity: 0.45; cursor: not-allowed; }
        #win-workstation .ws-btn--solid { background: var(--ws-ink); color: var(--ws-bg); }
        #win-workstation .ws-btn--solid:hover { opacity: 0.86; }
        #win-workstation .ws-btn--pos { border-color: var(--ws-pos); color: var(--ws-pos); background: var(--ws-paper); }
        #win-workstation .ws-btn--pos:hover { background: var(--ws-pos); color: var(--ws-paper); }
        #win-workstation .ws-btn--danger { border-color: var(--ws-danger); color: var(--ws-danger); background: var(--ws-paper); }
        #win-workstation .ws-btn--danger:hover { background: var(--ws-danger); color: var(--ws-paper); }
        #win-workstation .ws-btn--sm { padding: 3px 9px; font-size: 10px; }
        #win-workstation .ws-btn--full { width: 100%; padding: 7px 14px; font-size: 12px; }

        /* 3-pane studio grid */
        #win-workstation .ws-grid {
          flex: 1 1 auto;
          min-height: 0;
          display: grid;
          grid-template-columns: 310px minmax(0, 1fr) 310px;
          overflow: hidden;
        }
        #win-workstation .ws-pane {
          min-width: 0;
          min-height: 0;
          overflow-y: auto;
          padding: 10px;
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        #win-workstation .ws-pane--left {
          background: var(--ws-card);
          border-right: var(--ws-hair);
        }
        #win-workstation .ws-pane--center {
          background: var(--ws-bg);
        }
        #win-workstation .ws-pane--right {
          background: var(--ws-card);
          border-left: var(--ws-hair);
        }

        /* Cards & inputs */
        #win-workstation .ws-card {
          background: var(--ws-paper);
          border: var(--ws-hair);
          border-radius: 12px;
          padding: 9px 10px;
          display: flex;
          flex-direction: column;
          gap: 7px;
          min-width: 0;
        }
        #win-workstation .ws-card--celadon { background: var(--ws-card); }
        #win-workstation .ws-sec-head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 6px;
        }
        #win-workstation .ws-sec-title {
          font-size: 10px;
          font-weight: 700;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: var(--ws-faint);
        }
        #win-workstation .ws-input,
        #win-workstation .ws-select,
        #win-workstation .ws-textarea {
          width: 100%;
          max-width: 100%;
          min-width: 0;
          box-sizing: border-box;
          background: var(--ws-paper);
          color: var(--ws-ink);
          border: var(--ws-hair);
          border-radius: 8px;
          padding: 5px 8px;
          font-family: var(--ws-mono);
          font-size: 11px;
          line-height: 1.45;
          outline: none;
        }
        #win-workstation .ws-select {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        #win-workstation .ws-textarea { resize: vertical; min-height: 66px; }
        #win-workstation .ws-input:focus,
        #win-workstation .ws-select:focus,
        #win-workstation .ws-textarea:focus {
          box-shadow: 0 0 0 2px rgba(17, 17, 17, 0.16);
        }

        /* Active model card */
        #win-workstation .ws-model-card {
          background: var(--ws-card);
          border: var(--ws-hair-soft);
          border-radius: 8px;
          padding: 7px 8px;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        #win-workstation .ws-model-name {
          font-size: 11px;
          font-weight: 600;
          color: var(--ws-ink);
          min-width: 0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        #win-workstation .ws-model-meta {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 6px;
          font-family: var(--ws-mono);
          font-size: 10px;
          color: var(--ws-muted);
          border-top: var(--ws-hair-soft);
          padding-top: 4px;
        }

        /* Context picker */
        #win-workstation .ws-ctx-list {
          max-height: 164px;
          overflow-y: auto;
          border: var(--ws-hair-soft);
          border-radius: 8px;
          background: var(--ws-paper);
          display: flex;
          flex-direction: column;
        }
        #win-workstation .ws-ctx-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 6px;
          width: 100%;
          text-align: left;
          padding: 4px 8px;
          border: 0;
          border-bottom: var(--ws-hair-soft);
          background: transparent;
          color: var(--ws-ink);
          font-family: var(--ws-mono);
          font-size: 10px;
          cursor: pointer;
        }
        #win-workstation .ws-ctx-row:last-child { border-bottom: 0; }
        #win-workstation .ws-ctx-row:hover { background: var(--ws-card); }
        #win-workstation .ws-ctx-row.is-selected {
          background: var(--ws-ink);
          color: var(--ws-bg);
          font-weight: 600;
        }
        #win-workstation .ws-ctx-row.is-selected .ws-ctx-src { color: var(--ws-bg); opacity: 0.85; }
        #win-workstation .ws-ctx-src {
          flex: 0 0 auto;
          font-size: 9px;
          text-transform: uppercase;
          color: var(--ws-faint);
        }

        /* Center stage header & viewports */
        #win-workstation .ws-stage-head {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
        }
        #win-workstation .ws-stage-panel {
          display: flex;
          flex-direction: column;
          gap: 8px;
          flex: 1 1 auto;
          min-height: 230px;
        }
        #win-workstation .ws-3d-viewport {
          position: relative;
          flex: 1 1 auto;
          min-height: 210px;
          background: var(--ws-paper);
          background-image:
            linear-gradient(to right, rgba(17, 17, 17, 0.05) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(17, 17, 17, 0.05) 1px, transparent 1px);
          background-size: 24px 24px;
          border: var(--ws-hair);
          border-radius: 12px;
          overflow: hidden;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
        }
        #win-workstation #wsModelViewerStage {
          position: absolute;
          inset: 0;
          z-index: 2;
        }
        #win-workstation #wsWireframeFallback {
          position: relative;
          z-index: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
          gap: 6px;
          padding: 14px;
          max-width: 92%;
        }
        #win-workstation .ws-wire-svg {
          width: 144px;
          height: 112px;
          stroke: var(--ws-ink);
          fill: none;
        }
        #win-workstation .ws-3d-controls {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          justify-content: space-between;
          gap: 6px;
        }
        #win-workstation .ws-tier-row {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          gap: 4px;
        }

        /* Diff & patch preview boxes */
        #win-workstation .ws-diff-box {
          background: var(--ws-paper);
          border: var(--ws-hair);
          border-radius: 8px;
          padding: 8px 10px;
          font-family: var(--ws-mono);
          font-size: 11px;
          line-height: 1.5;
          overflow: auto;
          min-height: 130px;
          max-height: 240px;
          white-space: pre;
        }
        #win-workstation .ws-diff-box--compact {
          min-height: 78px;
          max-height: 135px;
        }
        #win-workstation .ws-diff-line { display: block; padding: 0 4px; border-radius: 2px; }
        #win-workstation .ws-diff-add { color: var(--ws-pos); background: var(--ws-pos-bg); }
        #win-workstation .ws-diff-del { color: var(--ws-danger); background: var(--ws-danger-bg); }
        #win-workstation .ws-diff-hunk { color: var(--ws-faint); font-weight: 600; }
        #win-workstation .ws-diff-file { color: var(--ws-ink); font-weight: 700; border-bottom: var(--ws-hair-soft); margin: 4px 0 2px; }
        #win-workstation .ws-diff-ctx { color: var(--ws-ink); }
        #win-workstation .ws-patch-frame {
          background: var(--ws-card);
          border: var(--ws-hair);
          border-radius: 12px;
          padding: 8px 10px;
          display: flex;
          flex-direction: column;
          gap: 6px;
          flex: 0 0 auto;
        }

        /* Arena 2-column benchmark */
        #win-workstation .ws-arena-bar {
          display: grid;
          grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr) auto;
          align-items: center;
          gap: 6px;
        }
        #win-workstation .ws-arena-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 8px;
          flex: 1 1 auto;
          min-height: 0;
        }
        #win-workstation .ws-arena-col {
          background: var(--ws-card);
          border: var(--ws-hair);
          border-radius: 12px;
          padding: 8px;
          display: flex;
          flex-direction: column;
          gap: 6px;
          min-width: 0;
        }
        #win-workstation .ws-arena-col.is-winner {
          box-shadow: inset 0 0 0 1px var(--ws-pos);
          border-color: var(--ws-pos);
        }
        #win-workstation .ws-arena-col-head {
          display: flex;
          flex-direction: column;
          gap: 2px;
          border-bottom: var(--ws-hair-soft);
          padding-bottom: 4px;
        }
        #win-workstation .ws-arena-col-title {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 6px;
        }
        #win-workstation .ws-arena-tag {
          font-size: 10px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.06em;
        }
        #win-workstation .ws-arena-out {
          flex: 1 1 auto;
          min-height: 110px;
          max-height: 190px;
          overflow-y: auto;
          background: var(--ws-paper);
          border: var(--ws-hair-soft);
          border-radius: 8px;
          padding: 7px 8px;
          font-family: var(--ws-mono);
          font-size: 11px;
          line-height: 1.48;
          white-space: pre-wrap;
          word-break: break-word;
        }
        #win-workstation .ws-arena-col-foot {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }
        #win-workstation .ws-xp-badge {
          display: inline-flex;
          align-items: center;
          padding: 0 6px;
          border-radius: 9999px;
          border: 1px solid var(--ws-pos);
          background: var(--ws-pos-bg);
          color: var(--ws-pos);
          font-family: var(--ws-mono);
          font-size: 9px;
          font-weight: 700;
        }
        #win-workstation .ws-btn:hover .ws-xp-badge {
          background: var(--ws-paper);
          color: var(--ws-pos);
        }

        /* Right pane stats, queue, trace, handoff */
        #win-workstation .ws-stats-2up {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 8px;
        }
        #win-workstation .ws-stat-card {
          background: var(--ws-paper);
          border: var(--ws-hair);
          border-radius: 12px;
          padding: 8px 9px;
          display: flex;
          flex-direction: column;
          gap: 2px;
          min-width: 0;
        }
        #win-workstation .ws-stat-label {
          font-size: 9px;
          font-weight: 700;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: var(--ws-faint);
        }
        #win-workstation .ws-stat-val {
          font-family: var(--ws-mono);
          font-size: 16px;
          font-weight: 700;
          color: var(--ws-ink);
          font-variant-numeric: tabular-nums;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        #win-workstation .ws-stat-sub {
          font-family: var(--ws-mono);
          font-size: 10px;
          color: var(--ws-muted);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        #win-workstation .ws-queue-list,
        #win-workstation .ws-staged-list {
          display: flex;
          flex-direction: column;
          gap: 5px;
          max-height: 122px;
          overflow-y: auto;
        }
        #win-workstation .ws-queue-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 6px;
          padding: 4px 7px;
          background: var(--ws-card);
          border: var(--ws-hair-soft);
          border-radius: 8px;
          font-family: var(--ws-mono);
          font-size: 10px;
        }
        #win-workstation .ws-trace-dl {
          display: grid;
          grid-template-columns: auto minmax(0, 1fr);
          gap: 4px 10px;
          margin: 0;
          font-family: var(--ws-mono);
          font-size: 10px;
        }
        #win-workstation .ws-trace-dl dt { color: var(--ws-faint); white-space: nowrap; }
        #win-workstation .ws-trace-dl dd {
          margin: 0;
          color: var(--ws-ink);
          font-weight: 600;
          text-align: right;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        #win-workstation .ws-guardrail-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
        }
        #win-workstation .ws-check-label {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          font-family: var(--ws-mono);
          font-size: 10px;
          color: var(--ws-ink);
          cursor: pointer;
          white-space: nowrap;
        }

        /* Responsive collapse (< 980px viewport or narrow container when tiled) */
        @media (max-width: 980px) {
          #win-workstation .ws-body {
            height: auto;
            max-height: calc(100vh - 120px);
            overflow-y: auto;
          }
          #win-workstation .ws-grid {
            grid-template-columns: 1fr;
            overflow: visible;
          }
          #win-workstation .ws-pane { overflow-y: visible; }
          #win-workstation .ws-pane--left { border-right: 0; border-bottom: var(--ws-hair); }
          #win-workstation .ws-pane--right { border-left: 0; border-top: var(--ws-hair); }
          #win-workstation .ws-arena-bar { grid-template-columns: 1fr; }
          #win-workstation .ws-arena-grid { grid-template-columns: 1fr; }
        }
        @container wsbody (max-width: 920px) {
          #win-workstation .ws-body {
            overflow-y: auto;
          }
          #win-workstation .ws-grid {
            grid-template-columns: 1fr;
            overflow: visible;
          }
          #win-workstation .ws-pane { overflow-y: visible; }
          #win-workstation .ws-pane--left { border-right: 0; border-bottom: var(--ws-hair); }
          #win-workstation .ws-pane--right { border-left: 0; border-top: var(--ws-hair); }
          #win-workstation .ws-arena-bar { grid-template-columns: 1fr; }
          #win-workstation .ws-arena-grid { grid-template-columns: 1fr; }
        }
      </style>"""
    return _re.sub(r"#win-workstation(?![A-Za-z0-9_-])", ".tc-ws-host", raw)


def _workstation_js() -> str:
    gateways_json = _safe_json_for_script(
        {g[0]: {"label": g[1], "badge": g[2], "kind": g[3], "privacy": g[4]} for g in GATEWAY_DEFS}
    )
    modes_json = _safe_json_for_script({m[0]: {"label": m[1], "hint": m[2]} for m in MODE_DEFS})
    tiers_json = _safe_json_for_script({t[0]: t[1] for t in RODIN_TIERS})
    fallback_json = _safe_json_for_script(FALLBACK_MODELS)

    template = r"""      <script id="workstationUiScript">
      (function () {
        if (typeof window === 'undefined' || typeof document === 'undefined') return;

        const GATEWAYS = __GATEWAYS_JSON__;
        const MODES = __MODES_JSON__;
        const RODIN_TIERS = __TIERS_JSON__;
        const FALLBACK_MODELS = __FALLBACK_JSON__;

        const state = {
          initialized: false,
          gateway: 'tee',
          mode: '3d',
          scope: 'user',
          ownerId: 'default_user',
          rodinTier: 'Regular',
          maxCostUsd: 0.50,
          activeModelId: 'nanogpt/TEE/deepseek-v4.1-flash',
          modelsByGateway: {
            tee: FALLBACK_MODELS.tee.slice(),
            heretic: FALLBACK_MODELS.heretic.slice(),
            openrouter: FALLBACK_MODELS.openrouter.slice(),
          },
          spaceFiles: [],
          drivePath: '/',
          driveDirs: [],
          driveFiles: [],
          driveAvailable: null,
          ctxFilter: 'all',
          selectedSource: 'space',
          selectedPath: '/src/main.py',
          selectedContent: null,
          merkleRoot: '',
          lastGlbB64: '',
          lastGlbUrl: '',
          lastGlbPath: '/models3d/studio_mesh.glb',
          lastRodinUuid: '',
          stagedPlan: null,
          stagedPlanCommitted: false,
          lastVersionId: '',
          pendingNotesCount: 0,
          sessionSpendUsd: 0.0,
          jobs: [],
          stagedOutputs: [],
          arenaMatchId: '',
          arenaLast: null,
          statusData: null,
        };

        const controllers = {};
        let refreshTimer = null;
        let modelViewerLoader = null;
        let wasVisible = false;
        let visObserver = null;

        const el = (id) => document.getElementById(id);
        const esc = (v) => String(v == null ? '' : v).replace(/[&<>"']/g, (c) => (
          { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
        ));

        function safeStorageGet(key) {
          try { return window.localStorage ? window.localStorage.getItem(key) : null; }
          catch (e) { return null; }
        }

        function resolvePeerId() {
          if (typeof window.myPeerId !== 'undefined' && window.myPeerId) return String(window.myPeerId);
          return safeStorageGet('tincan_peer_id') || 'default_user';
        }

        function resolveSpaceCtx() {
          let qScope = '';
          let qOwner = '';
          try {
            if (typeof window !== 'undefined' && window.location && window.location.search) {
              const qp = new URLSearchParams(window.location.search);
              qScope = qp.get('scope') || '';
              qOwner = qp.get('owner') || '';
            }
          } catch (e) {}
          const domOwner = (el('spaceOwnerInput') && el('spaceOwnerInput').value) ? String(el('spaceOwnerInput').value).trim() : '';
          const scope = qScope || ((typeof window.currentSpaceScope !== 'undefined' && window.currentSpaceScope)
            ? String(window.currentSpaceScope) : state.scope);
          const owner = qOwner || ((typeof window.currentSpaceOwner !== 'undefined' && window.currentSpaceOwner)
            ? String(window.currentSpaceOwner) : (domOwner || resolvePeerId()));
          return { scope: scope || 'user', ownerId: owner || 'default_user' };
        }

        function notify(msg, isError) {
          const noteEl = el('wsTraceNote');
          if (noteEl) {
            noteEl.textContent = msg;
            noteEl.title = msg;
            noteEl.style.color = isError ? 'var(--ws-danger)' : 'var(--ws-ink)';
          }
          if (typeof window.showQuickNotification === 'function') {
            try { window.showQuickNotification(msg); } catch (e) {}
          }
        }

        function isWindowVisible(winEl) {
          if (!winEl) return false;
          if (winEl.classList.contains('hidden') || winEl.classList.contains('minimized')) return false;
          if (winEl.style && winEl.style.display === 'none') return false;
          return true;
        }

        function openWindowSafe(winId) {
          if (typeof window.toggleWindow === 'function') {
            const target = el(winId);
            if (target && !isWindowVisible(target)) {
              window.toggleWindow(winId);
              return;
            }
            if (target && typeof window.bringToFront === 'function') {
              window.bringToFront(target);
              return;
            }
          }
          const target = el(winId);
          if (!target) return;
          target.classList.remove('hidden', 'minimized');
          target.style.display = 'flex';
          if (typeof window.bringToFront === 'function') {
            try { window.bringToFront(target); } catch (e) {}
          }
        }

        function abortChannel(name) {
          if (controllers[name]) {
            try { controllers[name].abort(); } catch (e) {}
          }
          if (typeof AbortController !== 'undefined') {
            controllers[name] = new AbortController();
            return controllers[name].signal;
          }
          return undefined;
        }

        async function apiJson(url, opts) {
          opts = opts || {};
          if (typeof fetch !== 'function') throw new Error('fetch unavailable');
          const signal = opts.channel ? abortChannel(opts.channel) : undefined;
          const headers = opts.body ? { 'Content-Type': 'application/json' } : {};
          const res = await fetch(url, {
            method: opts.method || (opts.body ? 'POST' : 'GET'),
            headers,
            body: opts.body ? JSON.stringify(opts.body) : undefined,
            credentials: 'same-origin',
            cache: 'no-store',
            signal,
          });
          let data = {};
          try { data = await res.json(); } catch (e) { data = {}; }
          if (!res.ok) {
            const err = new Error(data.error || ('HTTP ' + res.status));
            err.status = res.status;
            err.data = data;
            throw err;
          }
          return data;
        }

        function slugifyDirective(text) {
          const clean = String(text || '')
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '_')
            .replace(/^_+|_+$/g, '')
            .slice(0, 24);
          return clean || 'studio_mesh';
        }

        function formatCtxLen(n) {
          const v = Number(n || 0);
          if (!v) return '128K ctx';
          if (v >= 1000000) return (v / 1048576).toFixed(1).replace(/\.0$/, '') + 'M ctx';
          if (v >= 1000) return Math.round(v / 1000) + 'K ctx';
          return v + ' ctx';
        }

        function formatModelPrice(p) {
          if (!p || typeof p !== 'object') return 'Pooled rate';
          if (p.prompt_per_1m != null) {
            return '$' + Number(p.prompt_per_1m).toFixed(2) + ' / $' + Number(p.completion_per_1m || 0).toFixed(2) + ' per 1M';
          }
          if (typeof p.prompt === 'string' && p.prompt.indexOf('/') !== -1) {
            return '$' + p.prompt;
          }
          const pin = Number(p.prompt || 0);
          const pout = Number(p.completion || 0);
          if (!pin && !pout) return 'Included';
          if (pin < 0.01 && pout < 0.01) {
            return '$' + (pin * 1e6).toFixed(2) + ' / $' + (pout * 1e6).toFixed(2) + ' per 1M';
          }
          return '$' + pin.toFixed(2) + ' / $' + pout.toFixed(2);
        }

        function addJob(id, kind, label, status, detail) {
          state.jobs.unshift({
            id: String(id || (kind + '-' + Math.random().toString(16).slice(2, 7))),
            kind,
            label,
            status,
            detail: detail || '',
            ts: new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
          });
          if (state.jobs.length > 14) state.jobs.length = 14;
          renderJobQueue();
        }

        function renderJobQueue() {
          const box = el('wsJobQueueList');
          if (!box) return;
          if (!state.jobs.length) {
            box.innerHTML = '<div class="ws-muted-xs">No jobs dispatched yet. Select a directive and run 3D, TEE Audit, or Arena.</div>';
            return;
          }
          box.innerHTML = state.jobs.map((j) => {
            const cls = j.status === 'ERROR' || j.status === 'BLOCKED'
              ? 'ws-badge--danger'
              : (j.status === 'DONE' || j.status === 'COMMITTED' ? 'ws-badge--pos' : 'ws-badge--ink');
            return '<div class="ws-queue-item">' +
              '<div class="ws-truncate"><strong>' + esc(j.id) + '</strong> · ' + esc(j.label) +
              (j.detail ? ' <span class="ws-muted">(' + esc(j.detail) + ')</span>' : '') + '</div>' +
              '<span class="ws-badge ' + cls + '">' + esc(j.status) + '</span>' +
              '</div>';
          }).join('');
        }

        function recordStagedOutput(item) {
          state.stagedOutputs = state.stagedOutputs.filter((x) => x.key !== item.key);
          state.stagedOutputs.unshift(item);
          if (state.stagedOutputs.length > 8) state.stagedOutputs.length = 8;
          renderStagedOutputs();
        }

        function renderStagedOutputs() {
          const box = el('wsStagedList');
          if (!box) return;
          if (!state.stagedOutputs.length) {
            box.innerHTML = '<div class="ws-muted-xs">No staged .glb or Space patch artifacts yet.</div>';
            return;
          }
          box.innerHTML = state.stagedOutputs.map((o) => {
            const cls = o.committed ? 'ws-badge--pos' : 'ws-badge--ink';
            return '<div class="ws-queue-item">' +
              '<span class="ws-truncate" title="' + esc(o.label) + '">' + esc(o.label) + '</span>' +
              '<span class="ws-badge ' + cls + '">' + esc(o.status) + '</span>' +
              '</div>';
          }).join('');
        }

        function renderTrace() {
          const spendEl = el('wsTraceSpend');
          const privEl = el('wsTracePrivacy');
          const merkleEl = el('wsTraceMerkle');
          const merkleBadge = el('wsMerkleBadge');
          const scopeBadge = el('wsSpaceScopeBadge');

          const cap = Number((el('wsMaxCostSelect') && el('wsMaxCostSelect').value) || state.maxCostUsd || 0.50);
          if (spendEl) spendEl.textContent = '$' + state.sessionSpendUsd.toFixed(4) + ' / $' + cap.toFixed(2) + ' cap';
          if (privEl) {
            const gwMeta = GATEWAYS[state.gateway] || GATEWAYS.tee;
            const encl = el('wsEnclaveGuardToggle');
            privEl.textContent = gwMeta.privacy + (encl && encl.checked && state.gateway === 'tee' ? ' · Zero-Retention' : '');
          }
          const shortMerkle = state.merkleRoot ? state.merkleRoot.slice(0, 12) : '--';
          if (merkleEl) {
            merkleEl.textContent = shortMerkle;
            merkleEl.title = state.merkleRoot || 'Space Merkle Root';
          }
          if (merkleBadge) {
            merkleBadge.textContent = 'merkle: ' + shortMerkle;
            merkleBadge.title = state.merkleRoot || 'Space Merkle Root';
          }
          if (scopeBadge) {
            scopeBadge.textContent = state.scope + ':' + state.ownerId;
          }
        }

        function renderActiveModelCard() {
          const list = state.modelsByGateway[state.gateway] || [];
          const sel = el('wsModelSelect');
          const wantedId = (sel && sel.value) || state.activeModelId;
          const m = list.find((x) => x.id === wantedId) || list[0] || { id: wantedId, name: wantedId };
          if (m && m.id) state.activeModelId = m.id;

          const gwMeta = GATEWAYS[state.gateway] || GATEWAYS.tee;
          const nameEl = el('wsActiveModelName');
          const idEl = el('wsActiveModelId');
          const ctxEl = el('wsActiveModelCtx');
          const priceEl = el('wsActiveModelPrice');
          const badgeEl = el('wsActiveModelBadge');
          const auditModelTag = el('wsAuditModelTag');

          if (nameEl) nameEl.textContent = m.name || m.id || 'Model';
          if (idEl) idEl.textContent = m.id || '';
          if (ctxEl) ctxEl.textContent = formatCtxLen(m.context_length);
          if (priceEl) priceEl.textContent = formatModelPrice(m.pricing);
          if (badgeEl) {
            badgeEl.textContent = gwMeta.badge;
            badgeEl.className = 'ws-badge ' + (
              gwMeta.kind === 'attested' ? 'ws-badge--pos' : (gwMeta.kind === 'uncensored' ? 'ws-badge--ink' : '')
            );
          }
          if (auditModelTag) auditModelTag.textContent = m.id || 'nanogpt/TEE/deepseek-v4.1-flash';
          renderTrace();
        }

        function populateModelSelect() {
          const sel = el('wsModelSelect');
          if (!sel) return;
          const list = (state.modelsByGateway[state.gateway] || []).filter(
            (m) => !String(m.id || '').startsWith('ronin/')
          );
          const effective = list.length ? list : (FALLBACK_MODELS[state.gateway] || []);
          sel.innerHTML = effective.map((m) => (
            '<option value="' + esc(m.id) + '">' + esc(m.name || m.id) + '</option>'
          )).join('');
          const match = effective.find((m) => m.id === state.activeModelId);
          if (match) {
            sel.value = match.id;
          } else if (effective.length) {
            sel.value = effective[0].id;
            state.activeModelId = effective[0].id;
          }
          renderActiveModelCard();
        }

        function populateArenaSelects() {
          const selA = el('wsArenaModelA');
          const selB = el('wsArenaModelB');
          if (!selA || !selB) return;
          const openrouterList = (state.modelsByGateway.openrouter || FALLBACK_MODELS.openrouter).filter(
            (m) => !String(m.id || '').startsWith('ronin/')
          );
          const hereticList = state.modelsByGateway.heretic || FALLBACK_MODELS.heretic;
          const teeList = state.modelsByGateway.tee || FALLBACK_MODELS.tee;
          const merged = [];
          const seen = new Set();
          [openrouterList, hereticList, teeList].forEach((arr) => {
            arr.forEach((m) => {
              if (m && m.id && !seen.has(m.id)) {
                seen.add(m.id);
                merged.push(m);
              }
            });
          });
          const opts = merged.map((m) => '<option value="' + esc(m.id) + '">' + esc(m.name || m.id) + '</option>').join('');
          const prevA = selA.value;
          const prevB = selB.value;
          selA.innerHTML = opts;
          selB.innerHTML = opts;
          const defA = (openrouterList[0] && openrouterList[0].id) || 'anthropic/claude-3.7-sonnet';
          const defB = (hereticList[0] && hereticList[0].id) || 'nanogpt/pqhaz/DeepSeek-V4.1-Flash-1017-heretic';
          selA.value = seen.has(prevA) ? prevA : defA;
          selB.value = seen.has(prevB) ? prevB : defB;
          updateArenaLabels();
        }

        function updateArenaLabels() {
          const selA = el('wsArenaModelA');
          const selB = el('wsArenaModelB');
          const lblA = el('wsArenaLabelA');
          const lblB = el('wsArenaLabelB');
          if (lblA && selA) lblA.textContent = selA.value || 'Model A';
          if (lblB && selB) lblB.textContent = selB.value || 'Model B';
        }

        function updateOutputTargetTag() {
          const tag = el('wsOutputTargetTag');
          const dirInput = el('wsDirectiveInput');
          if (state.mode === '3d') {
            const dirText = (dirInput && dirInput.value.trim()) || '';
            if (!state.selectedPath || !/\.glb$/i.test(state.selectedPath)) {
              state.lastGlbPath = '/models3d/' + slugifyDirective(dirText) + '.glb';
            }
            if (tag) tag.textContent = state.lastGlbPath;
          } else if (state.mode === 'audit') {
            const p = (state.selectedSource === 'space' && state.selectedPath) ? state.selectedPath : '/notes/tee_audit.patch';
            if (tag) tag.textContent = '/notes/' + p.replace(/^\/+/, '');
            const auditPathEl = el('wsAuditTargetPath');
            if (auditPathEl) auditPathEl.textContent = state.selectedPath || '/src/main.py';
          } else {
            if (tag) tag.textContent = '/notes/arena_benchmark.md';
          }
        }

        function renderContextList() {
          const box = el('wsContextList');
          const selBadge = el('wsSelectedCtxPath');
          if (selBadge) selBadge.textContent = state.selectedPath || 'none';
          if (!box) return;

          const items = [];
          if (state.ctxFilter === 'all' || state.ctxFilter === 'space') {
            (state.spaceFiles || []).forEach((f) => {
              items.push({ source: 'space', path: f.path, kind: 'file', size: f.size_bytes });
            });
          }
          if (state.ctxFilter === 'all' || state.ctxFilter === 'drive') {
            if (state.drivePath && state.drivePath !== '/') {
              const parts = state.drivePath.split('/').filter(Boolean);
              parts.pop();
              const parentPath = '/' + parts.join('/');
              items.push({ source: 'drive', path: parentPath || '/', kind: 'up', label: '.. (up)' });
            }
            (state.driveDirs || []).forEach((d) => {
              items.push({ source: 'drive', path: d.path, kind: 'dir', label: d.name + '/' });
            });
            (state.driveFiles || []).forEach((f) => {
              items.push({ source: 'drive', path: f.path, kind: 'file', size: f.size_bytes });
            });
          }

          if (!items.length) {
            box.innerHTML = '<div class="ws-muted-xs" style="padding:8px;">No context files found in this view.</div>';
            return;
          }

          box.innerHTML = items.map((it) => {
            const active = (it.source === state.selectedSource && it.path === state.selectedPath && it.kind === 'file') ? ' is-selected' : '';
            const label = it.label || it.path;
            const tag = it.kind === 'dir' ? 'dir' : (it.kind === 'up' ? 'up' : it.source);
            return '<button type="button" role="option" class="ws-ctx-row' + active + '" data-src="' + esc(it.source) + '" data-kind="' + esc(it.kind) + '" data-path="' + esc(it.path) + '">' +
              '<span class="ws-truncate">' + esc(label) + '</span>' +
              '<span class="ws-ctx-src">' + esc(tag) + '</span>' +
              '</button>';
          }).join('');

          box.querySelectorAll('.ws-ctx-row').forEach((btn) => {
            btn.onclick = () => selectContextItem(btn.dataset.src, btn.dataset.kind, btn.dataset.path);
          });
        }

        async function selectContextItem(source, kind, path) {
          if (source === 'drive' && (kind === 'dir' || kind === 'up')) {
            state.drivePath = path || '/';
            await fetchDriveLs();
            return;
          }
          state.selectedSource = source;
          state.selectedPath = path;
          renderContextList();
          updateOutputTargetTag();

          if (source === 'space') {
            try {
              const rec = await apiJson(
                '/api/space/file?scope=' + encodeURIComponent(state.scope) +
                '&owner_id=' + encodeURIComponent(state.ownerId) +
                '&path=' + encodeURIComponent(path),
                { channel: 'spaceFile' }
              );
              state.selectedContent = rec.content != null ? rec.content : null;
              if (/\.glb$/i.test(path) && rec.content_b64) {
                state.lastGlbPath = path;
                state.lastGlbB64 = rec.content_b64;
                mountGlbPreview(rec.content_b64, path);
                if (state.mode !== '3d') switchMode('3d');
              } else if (state.mode === 'audit') {
                updateOutputTargetTag();
              }
            } catch (err) {
              if (err.name !== 'AbortError') notify('File read note: ' + err.message, true);
            }
          }
        }

        function b64ToBytes(b64) {
          const bin = atob(b64);
          const arr = new Uint8Array(bin.length);
          for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
          return arr;
        }

        function ensureModelViewer() {
          if (window.customElements && window.customElements.get('model-viewer')) {
            return Promise.resolve();
          }
          if (modelViewerLoader) return modelViewerLoader;
          modelViewerLoader = new Promise((resolve, reject) => {
            const s = document.createElement('script');
            s.type = 'module';
            s.src = 'https://unpkg.com/@google/model-viewer@3.5.0/dist/model-viewer.min.js';
            s.onload = () => resolve();
            s.onerror = () => {
              modelViewerLoader = null;
              reject(new Error('Offline or CDN unreachable; showing isometric wireframe preview.'));
            };
            document.head.appendChild(s);
          });
          return modelViewerLoader;
        }

        function mountGlbPreview(b64, pathLabel) {
          const stage = el('wsModelViewerStage');
          const fallback = el('wsWireframeFallback');
          const note = el('ws3dStatusNote');
          const meta = el('ws3dMeshMeta');
          if (!stage) return;

          if (state.lastGlbUrl && typeof URL !== 'undefined' && URL.revokeObjectURL) {
            try { URL.revokeObjectURL(state.lastGlbUrl); } catch (e) {}
            state.lastGlbUrl = '';
          }
          stage.innerHTML = '';
          if (fallback) fallback.classList.remove('hidden');

          let byteLen = 0;
          try {
            const bytes = b64ToBytes(b64);
            byteLen = bytes.byteLength;
            if (typeof Blob !== 'undefined' && typeof URL !== 'undefined' && URL.createObjectURL) {
              const blob = new Blob([bytes], { type: 'model/gltf-binary' });
              state.lastGlbUrl = URL.createObjectURL(blob);
            }
          } catch (e) {
            if (note) note.textContent = 'GLB decode error: ' + e.message;
            return;
          }

          if (meta) meta.textContent = (pathLabel || state.lastGlbPath) + ' · ' + byteLen + ' B';
          if (note) note.textContent = 'GLB ready (' + byteLen + ' bytes) · loading <model-viewer>…';
          if (!state.lastGlbUrl) return;

          ensureModelViewer().then(() => {
            if (!state.lastGlbUrl || !stage) return;
            const mv = document.createElement('model-viewer');
            mv.setAttribute('src', state.lastGlbUrl);
            mv.setAttribute('camera-controls', '');
            mv.setAttribute('auto-rotate', '');
            mv.setAttribute('alt', pathLabel || 'Rodin 3D GLB Asset');
            mv.style.width = '100%';
            mv.style.height = '100%';
            mv.style.background = 'transparent';
            stage.appendChild(mv);
            if (fallback) fallback.classList.add('hidden');
          }).catch((err) => {
            if (note) note.textContent = (pathLabel || state.lastGlbPath) + ' (' + byteLen + ' B) · ' + err.message;
          });
        }

        function colorizeDiffText(unifiedText, fallbackTitle) {
          if (!unifiedText) {
            return '<span class="ws-diff-ctx">No diff lines returned yet.</span>';
          }
          const lines = String(unifiedText).split(/\r?\n/);
          const header = fallbackTitle ? '<span class="ws-diff-line ws-diff-file">' + esc(fallbackTitle) + '</span>' : '';
          return header + lines.map((ln) => {
            let cls = 'ws-diff-ctx';
            if (ln.startsWith('+++') || ln.startsWith('---') || ln.startsWith('diff ')) cls = 'ws-diff-file';
            else if (ln.startsWith('@@')) cls = 'ws-diff-hunk';
            else if (ln.startsWith('+')) cls = 'ws-diff-add';
            else if (ln.startsWith('-')) cls = 'ws-diff-del';
            return '<span class="ws-diff-line ' + cls + '">' + esc(ln) + '</span>';
          }).join('');
        }

        function synthesizePlanDiff(plan) {
          if (!plan) return '';
          if (Array.isArray(plan.diff_preview) && plan.diff_preview.length) {
            return plan.diff_preview.map((d) => colorizeDiffText(d.unified || '', d.path ? ('file: ' + d.path) : '')).join('');
          }
          const edits = Array.isArray(plan.edits) ? plan.edits : [];
          if (!edits.length) return '<span class="ws-diff-ctx">Plan has 0 file edits.</span>';
          return edits.map((e) => {
            const p = e.path || '/unknown';
            if (e.op === 'patch') {
              const delLines = String(e.target || '').split(/\r?\n/).map((l) => '- ' + l).join('\n');
              const addLines = String(e.replacement || '').split(/\r?\n/).map((l) => '+ ' + l).join('\n');
              return colorizeDiffText('--- a' + p + '\n+++ b' + p + '\n@@ patch @@\n' + delLines + '\n' + addLines);
            }
            if (e.op === 'delete') {
              return colorizeDiffText('--- a' + p + '\n+++ /dev/null\n- [deleted file]');
            }
            const writeLines = String(e.content || '').split(/\r?\n/).slice(0, 40).map((l) => '+ ' + l).join('\n');
            return colorizeDiffText('--- /dev/null\n+++ b' + p + '\n@@ write @@\n' + writeLines);
          }).join('');
        }

        function renderDiffBoxes(plan, fallbackMsg) {
          const auditBox = el('wsAuditDiffBox');
          const previewBox = el('wsPatchPreviewDiff');
          const sumEl = el('wsAuditSummary');
          const planBadge = el('wsPlanIdBadge');

          if (plan) {
            const htmlDiff = synthesizePlanDiff(plan);
            if (auditBox) auditBox.innerHTML = htmlDiff;
            if (previewBox) previewBox.innerHTML = htmlDiff;
            if (sumEl) {
              const editCount = Array.isArray(plan.edits) ? plan.edits.length : 0;
              sumEl.textContent = (plan.summary || 'Patch proposed') + ' · ' + editCount + ' edit(s)';
            }
            if (planBadge) planBadge.textContent = plan.plan_id || 'plan_staged';
          } else {
            const msg = '<span class="ws-diff-ctx">' + esc(fallbackMsg || 'No staged Space Notes patch yet.') + '</span>';
            if (auditBox) auditBox.innerHTML = msg;
            if (previewBox) previewBox.innerHTML = msg;
            if (planBadge) planBadge.textContent = state.lastVersionId ? ('committed: ' + state.lastVersionId) : 'no plan';
          }
        }

        async function fetchStatus() {
          try {
            const url = '/api/workstation/status?scope=' + encodeURIComponent(state.scope) +
              '&owner_id=' + encodeURIComponent(state.ownerId);
            const data = await apiJson(url, { channel: 'status' });
            state.statusData = data;
            if (data.space && data.space.merkle_root) state.merkleRoot = data.space.merkle_root;
            if (data.drive_mirror && typeof data.drive_mirror.available === 'boolean') {
              state.driveAvailable = data.drive_mirror.available;
            }
            const rodinVal = el('wsStatRodinVal');
            const rodinSub = el('wsStatRodinSub');
            const nanoVal = el('wsStatNanoVal');
            const nanoSub = el('wsStatNanoSub');
            const rodin = data.rodin || {};
            const nano = data.nanogpt || {};
            if (rodinVal) rodinVal.textContent = Number(rodin.credits ?? 0).toFixed(1) + ' CR';
            if (rodinSub) {
              rodinSub.textContent = '$' + Number(rodin.balance_usd ?? 0).toFixed(2) + ' ' + (rodin.status || 'live');
              if (rodin.key_label) rodinSub.title = rodin.key_label;
            }
            if (nanoVal) nanoVal.textContent = (nano.tee_count ?? 0) + ' TEE';
            if (nanoSub) nanoSub.textContent = '+ ' + (nano.heretic_count ?? 0) + ' Heretic · ' + (nano.total_count ?? 0) + ' total';

            if (data.rodin_tiers && typeof data.rodin_tiers === 'object') {
              Object.keys(data.rodin_tiers).forEach((t) => {
                const price = Number(data.rodin_tiers[t]);
                if (!Number.isNaN(price)) {
                  RODIN_TIERS[t] = price;
                  const btn = el('wsTierBtn-' + t);
                  if (btn) {
                    btn.dataset.price = price.toFixed(2);
                    btn.textContent = t + ' $' + price.toFixed(2);
                  }
                }
              });
            }
            const statusPill = el('wsStatusPill');
            if (statusPill) statusPill.textContent = (nano.configured ? 'CONNECTED' : 'READY');
            renderTrace();
          } catch (err) {
            if (err.name === 'AbortError') return;
            const rodinSub = el('wsStatRodinSub');
            if (rodinSub && rodinSub.textContent === 'Checking balance…') rodinSub.textContent = 'Offline fallback';
          }
        }

        async function fetchGatewayModels(gw) {
          const targetGw = gw || state.gateway;
          let url = '/api/models/nanogpt?tee=1&live=0';
          if (targetGw === 'heretic') url = '/api/models/nanogpt?uncensored=1&live=0';
          else if (targetGw === 'openrouter') url = '/api/models/openrouter';

          try {
            const data = await apiJson(url, { channel: 'models_' + targetGw });
            const list = Array.isArray(data) ? data : (data.models || []);
            if (list.length) state.modelsByGateway[targetGw] = list;
            if (state.gateway === targetGw) populateModelSelect();
            populateArenaSelects();
          } catch (err) {
            if (err.name === 'AbortError') return;
            if (state.gateway === targetGw) populateModelSelect();
            populateArenaSelects();
          }
        }

        async function fetchSpaceLs() {
          try {
            const data = await apiJson(
              '/api/space/ls?scope=' + encodeURIComponent(state.scope) +
              '&owner_id=' + encodeURIComponent(state.ownerId),
              { channel: 'spaceLs' }
            );
            state.spaceFiles = data.files || [];
            if (data.merkle_root) state.merkleRoot = data.merkle_root;
            if (state.spaceFiles.length && !state.spaceFiles.some((f) => f.path === state.selectedPath)) {
              const preferred = state.spaceFiles.find((f) => /\.(py|md|js|txt)$/i.test(f.path)) || state.spaceFiles[0];
              state.selectedSource = 'space';
              state.selectedPath = preferred.path;
            }
            renderContextList();
            updateOutputTargetTag();
            renderTrace();
          } catch (err) {
            if (err.name === 'AbortError') return;
          }
        }

        async function fetchDriveLs() {
          try {
            const data = await apiJson('/api/drive/ls?path=' + encodeURIComponent(state.drivePath || '/'), { channel: 'driveLs' });
            state.driveAvailable = true;
            state.driveDirs = data.dirs || [];
            state.driveFiles = data.files || [];
            renderContextList();
          } catch (err) {
            if (err.name === 'AbortError') return;
            state.driveAvailable = false;
            state.driveDirs = [];
            state.driveFiles = [];
            renderContextList();
          }
        }

        async function fetchSpaceNotes() {
          try {
            const data = await apiJson(
              '/api/space/notes?scope=' + encodeURIComponent(state.scope) +
              '&owner_id=' + encodeURIComponent(state.ownerId),
              { channel: 'spaceNotes' }
            );
            const notes = Array.isArray(data) ? data : (data.notes || []);
            const versions = Array.isArray(data.versions) ? data.versions : [];
            const pendingCount = data.pending_count != null ? data.pending_count : notes.length;
            state.pendingNotesCount = pendingCount;
            const countBadge = el('wsNotesCountBadge');
            if (countBadge) countBadge.textContent = pendingCount + ' pending';
            if (!state.lastVersionId && versions.length) {
              const activeVer = versions.find((v) => !v.reverted);
              if (activeVer && activeVer.version_id) state.lastVersionId = activeVer.version_id;
            }
            if (!state.stagedPlan && notes.length) {
              const summaryLines = notes.slice(-4).map((n) => '[' + (n.kind || 'note') + '] ' + (n.path || '/') + ': ' + (n.body || '')).join('\n');
              renderDiffBoxes(null, summaryLines);
            }
          } catch (err) {
            if (err.name === 'AbortError') return;
          }
        }

        async function runRodin3D() {
          const dirInput = el('wsDirectiveInput');
          const promptVal = (dirInput && dirInput.value.trim()) || 'Sleek modular telemetry rover 3D mesh';
          const tier = state.rodinTier || 'Regular';
          const tierPrice = Number(RODIN_TIERS[tier] ?? 0.50);
          const cap = Number((el('wsMaxCostSelect') && el('wsMaxCostSelect').value) || state.maxCostUsd || 0.50);
          const noteEl = el('ws3dStatusNote');
          const btn = el('wsDispatchBtn');

          if (tierPrice > cap + 1e-9) {
            const msg = 'Guardrail blocked: ' + tier + ' ($' + tierPrice.toFixed(2) + ') exceeds max cost cap $' + cap.toFixed(2) + '.';
            if (noteEl) noteEl.textContent = msg;
            addJob('rodin-guard', 'rodin', tier + ' GLB', 'BLOCKED', '$' + tierPrice.toFixed(2) + ' > $' + cap.toFixed(2));
            notify(msg, true);
            return;
          }

          const savePath = '/models3d/' + slugifyDirective(promptVal) + '.glb';
          state.lastGlbPath = savePath;
          updateOutputTargetTag();
          if (btn) btn.disabled = true;
          if (noteEl) noteEl.textContent = 'Generating ' + tier + ' GLB via Hyper3D Rodin…';

          try {
            const res = await apiJson('/api/3d/generate', {
              channel: 'dispatch',
              body: {
                prompt: promptVal,
                tier,
                format: 'glb',
                peer_id: resolvePeerId(),
                scope: state.scope,
                owner_id: state.ownerId,
                save_path: savePath,
                max_cost_usd: cap,
              },
            });
            const cost = Number(res.cost_usd ?? tierPrice);
            state.sessionSpendUsd += cost;
            state.lastRodinUuid = res.uuid || ('rodin-' + Date.now());
            state.lastGlbB64 = res.glb_bytes_b64 || '';
            state.lastGlbPath = (res.saved_to_space && res.saved_to_space.path) || savePath;

            if (state.lastGlbB64) {
              mountGlbPreview(state.lastGlbB64, state.lastGlbPath);
            }
            addJob(state.lastRodinUuid, 'rodin', tier + ' GLB', 'DONE', '$' + cost.toFixed(2));
            recordStagedOutput({
              key: 'glb:' + state.lastGlbPath,
              label: state.lastGlbPath,
              status: res.saved_to_space ? 'SAVED' : 'STAGED',
              committed: Boolean(res.saved_to_space),
            });
            renderTrace();
            notify('3D GLB ready: ' + state.lastGlbPath + ' ($' + cost.toFixed(2) + ')', false);
            fetchSpaceLs();
            fetchStatus();
            if (typeof window.refreshAgentSpace === 'function') {
              try { window.refreshAgentSpace('background'); } catch (e) {}
            }
          } catch (err) {
            if (err.name === 'AbortError') return;
            if (noteEl) noteEl.textContent = 'Rodin error: ' + err.message;
            addJob('rodin-err', 'rodin', tier + ' GLB', 'ERROR', err.message);
            notify('3D generation failed: ' + err.message, true);
          } finally {
            if (btn) btn.disabled = false;
          }
        }

        async function saveGlbToSpace() {
          if (!state.lastGlbB64) {
            notify('Generate or select a .glb mesh before saving to .space.', true);
            return;
          }
          const targetPath = state.lastGlbPath || '/models3d/studio_mesh.glb';
          try {
            await apiJson('/api/space/file', {
              channel: 'saveGlb',
              body: {
                scope: state.scope,
                owner_id: state.ownerId,
                path: targetPath,
                content: state.lastGlbB64,
                is_base64: true,
                mime_type: 'model/gltf-binary',
                action: 'write',
                updated_by: resolvePeerId(),
              },
            });
            recordStagedOutput({
              key: 'glb:' + targetPath,
              label: targetPath,
              status: 'SAVED',
              committed: true,
            });
            notify('Saved ' + targetPath + ' to .space VFS', false);
            await fetchSpaceLs();
            await fetchStatus();
            if (typeof window.refreshAgentSpace === 'function') {
              try { window.refreshAgentSpace('background'); } catch (e) {}
            }
          } catch (err) {
            if (err.name !== 'AbortError') notify('Save to .space failed: ' + err.message, true);
          }
        }

        async function openInArtCraft() {
          const targetPath = (state.mode === '3d' && state.lastGlbPath)
            ? state.lastGlbPath
            : (state.selectedPath || '/artcraft/drawing.dxf');
          try {
            const data = await apiJson('/api/artcraft/open', {
              channel: 'artcraft',
              body: {
                app_id: 'cadcraft',
                scope: state.scope,
                owner_id: state.ownerId,
                path: targetPath,
              },
            });
            if (data.mode === 'native-pc-app' || data.mode === 'artcraft-launcher-pc') {
              notify('Opened ' + targetPath + ' in ArtCraft (' + ((data.app && data.app.name) || 'CadCraft') + ')', false);
            } else {
              notify('ArtCraft ready (' + (data.status || 'wasm') + ') for ' + targetPath, false);
              if (data.getartcraft_url && typeof window.open === 'function') {
                try { window.open(data.getartcraft_url, '_blank', 'noopener'); } catch (e) {}
              }
            }
          } catch (err) {
            if (err.name !== 'AbortError') notify('ArtCraft open failed: ' + err.message, true);
          }
        }

        async function runAuditPropose() {
          const dirInput = el('wsDirectiveInput');
          const instruction = (dirInput && dirInput.value.trim()) || 'Audit active file and propose minimal verified patch.';
          const targetPath = state.selectedPath || '/src/main.py';
          const model = state.activeModelId || 'nanogpt/TEE/deepseek-v4.1-flash';
          const btn = el('wsAuditProposeBtn');
          if (btn) btn.disabled = true;

          try {
            const res = await apiJson('/api/space/notes/propose', {
              channel: 'auditPropose',
              body: {
                scope: state.scope,
                owner_id: state.ownerId,
                model,
                instruction,
                note_body: instruction,
                path: targetPath,
              },
            });
            state.stagedPlan = res;
            state.stagedPlanCommitted = false;
            renderDiffBoxes(res);
            const planId = res.plan_id || ('tee-' + Date.now());
            addJob('tee-' + String(planId).slice(-8), 'tee', targetPath, 'STAGED', model.split('/').pop());
            recordStagedOutput({
              key: 'plan:' + planId,
              label: planId + ' (' + targetPath + ')',
              status: 'STAGED',
              committed: false,
            });
            notify('Staged TEE patch ' + planId + ' for ' + targetPath, false);
            fetchSpaceNotes();
          } catch (err) {
            if (err.name === 'AbortError') return;
            addJob('tee-err', 'tee', targetPath, 'ERROR', err.message);
            renderDiffBoxes(null, 'Propose error: ' + err.message);
            notify('TEE Audit propose failed: ' + err.message, true);
          } finally {
            if (btn) btn.disabled = false;
          }
        }

        async function commitAuditPatch() {
          if (!state.stagedPlan || !state.stagedPlan.plan_id) {
            notify('No proposed patch staged. Run TEE Audit & Diff first.', true);
            return false;
          }
          const planId = state.stagedPlan.plan_id;
          try {
            const res = await apiJson('/api/space/notes/commit', {
              channel: 'auditCommit',
              body: {
                scope: state.scope,
                owner_id: state.ownerId,
                plan_id: planId,
              },
            });
            state.stagedPlanCommitted = true;
            if (res.version_id) state.lastVersionId = res.version_id;
            if (res.merkle_root) state.merkleRoot = res.merkle_root;
            addJob('tee-' + String(res.version_id || planId).slice(-8), 'tee', 'Commit patch', 'COMMITTED', res.version_id || '');
            recordStagedOutput({
              key: 'plan:' + planId,
              label: (res.version_id || planId) + ' committed',
              status: 'COMMITTED',
              committed: true,
            });
            const sumEl = el('wsAuditSummary');
            if (sumEl) sumEl.textContent = 'Committed ' + (res.version_id || planId) + ' · Merkle ' + (state.merkleRoot || '').slice(0, 10);
            const planBadge = el('wsPlanIdBadge');
            if (planBadge) planBadge.textContent = 'committed: ' + (res.version_id || planId);
            notify('Committed patch ' + (res.version_id || planId) + ' to .space', false);
            await fetchSpaceLs();
            await fetchSpaceNotes();
            await fetchStatus();
            if (typeof window.refreshAgentSpace === 'function') {
              try { window.refreshAgentSpace('background'); } catch (e) {}
            }
            return true;
          } catch (err) {
            if (err.name !== 'AbortError') notify('Commit patch failed: ' + err.message, true);
            return false;
          }
        }

        async function revertLastPatch() {
          if (!state.lastVersionId) {
            await fetchSpaceNotes();
          }
          if (!state.lastVersionId) {
            notify('No committed version available to revert.', true);
            return;
          }
          const verId = state.lastVersionId;
          try {
            const res = await apiJson('/api/space/notes/revert', {
              channel: 'auditRevert',
              body: {
                scope: state.scope,
                owner_id: state.ownerId,
                version_id: verId,
              },
            });
            if (res.merkle_root) state.merkleRoot = res.merkle_root;
            state.lastVersionId = '';
            addJob('tee-rev-' + String(verId).slice(-6), 'tee', 'Revert ' + verId, 'DONE', 'reverted');
            renderDiffBoxes(null, 'Reverted version ' + verId + '. Notes returned to pending.');
            notify('Reverted ' + verId, false);
            await fetchSpaceLs();
            await fetchSpaceNotes();
            await fetchStatus();
            if (typeof window.refreshAgentSpace === 'function') {
              try { window.refreshAgentSpace('background'); } catch (e) {}
            }
          } catch (err) {
            if (err.name !== 'AbortError') notify('Revert failed: ' + err.message, true);
          }
        }

        async function runArenaBenchmark() {
          const selA = el('wsArenaModelA');
          const selB = el('wsArenaModelB');
          const modelA = (selA && selA.value) || 'anthropic/claude-3.7-sonnet';
          const modelB = (selB && selB.value) || 'nanogpt/pqhaz/DeepSeek-V4.1-Flash-1017-heretic';
          const dirInput = el('wsDirectiveInput');
          const prompt = (dirInput && dirInput.value.trim()) || 'Evaluate architectural trade-offs for zero-knowledge blind relays.';
          const btn = el('wsArenaRunBtn');
          if (btn) btn.disabled = true;

          state.arenaMatchId = '';
          state.arenaLast = null;
          ['A', 'B'].forEach((s) => {
            const col = el('wsArenaCol' + s);
            const out = el('wsArenaOut' + s);
            const meta = el('wsArenaMeta' + s);
            const xp = el('wsArenaXp' + s);
            if (col) col.classList.remove('is-winner');
            if (out) out.textContent = 'Running benchmark…';
            if (meta) meta.textContent = 'Dispatching…';
            if (xp) xp.textContent = '+150 XP';
          });

          try {
            let matchId = '';
            try {
              const mRes = await apiJson('/api/mesh/arena/match', {
                body: { model_a: modelA, model_b: modelB, prompt },
              });
              matchId = (mRes.match && mRes.match.match_id) || mRes.match_id || '';
              state.arenaMatchId = matchId;
            } catch (matchErr) {
              if (matchErr.status && matchErr.status !== 401 && matchErr.status !== 403) {
                notify('Arena match notice: ' + matchErr.message, true);
              }
            }

            const runSide = async (side, modelId) => {
              const t0 = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
              const body = { model: modelId, prompt, peer_id: resolvePeerId() };
              if (matchId) {
                body.arena = true;
                body.match_id = matchId;
                body.arena_side = side;
              }
              try {
                const res = await apiJson('/api/chat', { body });
                const t1 = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
                const ms = Math.max(1, Math.round(t1 - t0));
                const text = (res.choices && res.choices[0] && res.choices[0].message && res.choices[0].message.content) ||
                  res.reply || res.text || '(empty response)';
                const toks = (res.usage && res.usage.total_tokens) || (res.billing && res.billing.tokens_billed) || 0;
                const cost = Number(res.cost_usd ?? (res.billing && res.billing.cost_usd) ?? 0);
                state.sessionSpendUsd += cost;
                const outEl = el('wsArenaOut' + side);
                const metaEl = el('wsArenaMeta' + side);
                if (outEl) outEl.textContent = text;
                if (metaEl) metaEl.textContent = toks + ' tok · ' + ms + ' ms · $' + cost.toFixed(5);
                return { ok: true, toks, ms, cost };
              } catch (sideErr) {
                const outEl = el('wsArenaOut' + side);
                const metaEl = el('wsArenaMeta' + side);
                if (outEl) outEl.textContent = 'Error: ' + sideErr.message;
                if (metaEl) metaEl.textContent = 'failed';
                return { ok: false };
              }
            };

            const resA = await runSide('A', modelA);
            const resB = await runSide('B', modelB);
            state.arenaLast = { modelA, modelB, prompt, matchId };
            const jobId = matchId ? ('arena-' + String(matchId).slice(-6)) : ('arena-' + Date.now().toString(16).slice(-6));
            addJob(jobId, 'arena', 'A vs B', (resA.ok && resB.ok) ? 'DONE' : 'PARTIAL', modelB.split('/').pop());
            renderTrace();
            notify('Arena benchmark complete (' + modelA.split('/').pop() + ' vs ' + modelB.split('/').pop() + ')', false);
          } finally {
            if (btn) btn.disabled = false;
          }
        }

        async function voteArena(side) {
          const winnerSide = side === 'B' ? 'B' : 'A';
          const selA = el('wsArenaModelA');
          const selB = el('wsArenaModelB');
          const modelA = (state.arenaLast && state.arenaLast.modelA) || (selA && selA.value) || 'anthropic/claude-3.7-sonnet';
          const modelB = (state.arenaLast && state.arenaLast.modelB) || (selB && selB.value) || 'nanogpt/pqhaz/DeepSeek-V4.1-Flash-1017-heretic';
          const winnerAlias = winnerSide === 'A' ? modelA : modelB;
          const promptPreview = ((state.arenaLast && state.arenaLast.prompt) || (el('wsDirectiveInput') && el('wsDirectiveInput').value) || '').slice(0, 40);

          const payload = {
            peer_id: resolvePeerId(),
            winner_side: winnerSide,
            winner_alias: winnerAlias,
            model_a: modelA,
            model_b: modelB,
            prompt_preview: promptPreview,
            display_name: safeStorageGet('tincan_username') || resolvePeerId(),
          };
          if (state.arenaMatchId) payload.match_id = state.arenaMatchId;

          try {
            await apiJson('/api/mesh/arena/vote', { body: payload });
            ['A', 'B'].forEach((s) => {
              const col = el('wsArenaCol' + s);
              const xp = el('wsArenaXp' + s);
              if (col) col.classList.toggle('is-winner', s === winnerSide);
              if (xp) xp.textContent = s === winnerSide ? 'Voted · +150 XP' : '+150 XP';
            });
            if (typeof window.playXpChime === 'function') {
              try { window.playXpChime(); } catch (e) {}
            }
            if (typeof window.pollMeshState === 'function') {
              try { window.pollMeshState(); } catch (e) {}
            }
            notify('Voted Model ' + winnerSide + ' (' + winnerAlias + ') · +150 XP', false);
          } catch (err) {
            notify('Vote error: ' + err.message, true);
          }
        }

        async function handoffCommitToSpace() {
          let didSomething = false;
          if (state.stagedPlan && state.stagedPlan.plan_id && !state.stagedPlanCommitted) {
            const ok = await commitAuditPatch();
            if (ok) didSomething = true;
          }
          if (state.lastGlbB64) {
            await saveGlbToSpace();
            didSomething = true;
          }
          if (!didSomething) {
            notify('Nothing pending to commit — generate a 3D .glb or propose a TEE patch first.', true);
          }
        }

        async function handoffPostToBoard() {
          const title = 'Workstation Review · ' + (MODES[state.mode] ? MODES[state.mode].label : state.mode);
          const lines = [
            'Space: ' + state.scope + ':' + state.ownerId + ' (Merkle ' + (state.merkleRoot || 'pending').slice(0, 12) + ')',
            'Model: ' + state.activeModelId + ' [' + (GATEWAYS[state.gateway] ? GATEWAYS[state.gateway].badge : state.gateway) + ']',
          ];
          if (state.lastGlbPath && state.lastGlbB64) lines.push('3D GLB Artifact: ' + state.lastGlbPath);
          if (state.stagedPlan && state.stagedPlan.plan_id) {
            lines.push('Patch Plan: ' + state.stagedPlan.plan_id + ' — ' + (state.stagedPlan.summary || ''));
          }
          const dir = el('wsDirectiveInput') && el('wsDirectiveInput').value.trim();
          if (dir) lines.push('Directive: ' + dir);

          try {
            await apiJson('/api/board/topics', {
              channel: 'boardPost',
              body: {
                peer_id: resolvePeerId(),
                username: safeStorageGet('tincan_username') || resolvePeerId(),
                title,
                body: lines.join('\n'),
                category: 'workstation',
                tags: ['workstation', state.mode, state.gateway],
                auto_agent_reply: true,
              },
            });
            notify('Posted workstation review to @board', false);
            if (typeof window.loadCyberspaceBoard === 'function') {
              try { window.loadCyberspaceBoard(); } catch (e) {}
            }
            if (el('win-board')) openWindowSafe('win-board');
            else if (el('win-comms')) openWindowSafe('win-comms');
          } catch (err) {
            if (err.name !== 'AbortError') notify('Board handoff failed: ' + err.message, true);
          }
        }

        function switchGateway(gw) {
          if (!GATEWAYS[gw]) return;
          state.gateway = gw;
          Object.keys(GATEWAYS).forEach((k) => {
            const b = el('wsGwBtn-' + k);
            if (b) {
              b.classList.toggle('is-active', k === gw);
              b.setAttribute('aria-selected', k === gw ? 'true' : 'false');
            }
          });
          const enclaveChk = el('wsEnclaveGuardToggle');
          if (enclaveChk) enclaveChk.checked = (gw === 'tee');
          populateModelSelect();
          fetchGatewayModels(gw);
        }

        function switchMode(mode) {
          if (!MODES[mode]) return;
          state.mode = mode;
          Object.keys(MODES).forEach((k) => {
            const b = el('wsModeBtn-' + k);
            const panel = el('wsStage-' + k);
            if (b) {
              b.classList.toggle('is-active', k === mode);
              b.setAttribute('aria-selected', k === mode ? 'true' : 'false');
            }
            if (panel) panel.classList.toggle('hidden', k !== mode);
          });
          updateOutputTargetTag();
        }

        function tileWithSpace() {
          if (typeof window.toggleDock3dStudio === 'function') {
            window.toggleDock3dStudio();
            refresh({ immediate: true });
            return;
          }
          const wsWin = el('win-workstation');
          const spWin = el('win-agentspace');
          if (!wsWin) return;

          [wsWin, spWin].forEach((w) => {
            if (!w) return;
            w.classList.remove('hidden', 'minimized', 'maximized');
            w.style.display = 'flex';
          });

          const vw = window.innerWidth || 1280;
          const vh = window.innerHeight || 800;
          const topBar = 56;
          const dockH = 64;
          const pad = 12;
          const availH = Math.max(460, vh - topBar - dockH - pad * 2);

          if (vw < 980) {
            let y = topBar + pad;
            [wsWin, spWin].forEach((w) => {
              if (!w) return;
              w.style.left = '10px';
              w.style.top = y + 'px';
              w.style.width = 'calc(100vw - 20px)';
              w.style.height = 'auto';
              y += 540;
            });
          } else if (spWin) {
            const availW = vw - pad * 3;
            const wsW = Math.max(540, Math.floor(availW * 0.56));
            const spW = Math.max(360, availW - wsW);
            wsWin.style.left = pad + 'px';
            wsWin.style.top = (topBar + pad) + 'px';
            wsWin.style.width = wsW + 'px';
            wsWin.style.height = availH + 'px';
            spWin.style.left = (pad * 2 + wsW) + 'px';
            spWin.style.top = (topBar + pad) + 'px';
            spWin.style.width = spW + 'px';
            spWin.style.height = availH + 'px';
            [wsWin, spWin].forEach((w) => {
              const b = w.querySelector('.window-body');
              if (b) {
                b.style.height = (availH - 44) + 'px';
                b.style.maxHeight = (availH - 44) + 'px';
              }
            });
          } else {
            const wsW = Math.min(1080, vw - pad * 2);
            wsWin.style.left = pad + 'px';
            wsWin.style.top = (topBar + pad) + 'px';
            wsWin.style.width = wsW + 'px';
            wsWin.style.height = availH + 'px';
          }

          if (typeof window.bringToFront === 'function') {
            try { window.bringToFront(wsWin); } catch (e) {}
          }
          if (typeof window.syncDockIndicators === 'function') {
            try { window.syncDockIndicators(); } catch (e) {}
          }
          refresh({ immediate: true });
        }

        function dispatch() {
          if (state.mode === '3d') return runRodin3D();
          if (state.mode === 'audit') return runAuditPropose();
          return runArenaBenchmark();
        }

        function refresh(opts) {
          opts = opts || {};
          const ctx = resolveSpaceCtx();
          state.scope = ctx.scope;
          state.ownerId = ctx.ownerId;
          renderTrace();

          const exec = () => {
            fetchStatus();
            fetchGatewayModels(state.gateway);
            if (state.gateway !== 'openrouter') fetchGatewayModels('openrouter');
            if (state.gateway !== 'heretic') fetchGatewayModels('heretic');
            fetchSpaceLs();
            fetchDriveLs();
            fetchSpaceNotes();
          };
          if (refreshTimer) {
            clearTimeout(refreshTimer);
            refreshTimer = null;
          }
          if (opts.immediate) {
            exec();
          } else {
            refreshTimer = setTimeout(exec, 120);
          }
        }

        function openWithContext(ctx) {
          if (typeof ctx === 'string') ctx = { path: ctx };
          ctx = ctx || {};
          if (ctx.scope) state.scope = String(ctx.scope);
          if (ctx.owner_id) state.ownerId = String(ctx.owner_id);
          if (ctx.path) {
            state.selectedSource = ctx.source || 'space';
            state.selectedPath = String(ctx.path);
          }
          const dirInput = el('wsDirectiveInput');
          if (dirInput && (ctx.directive || ctx.prompt)) {
            dirInput.value = String(ctx.directive || ctx.prompt);
          }
          if (ctx.gateway && GATEWAYS[ctx.gateway]) switchGateway(ctx.gateway);
          if (ctx.mode && MODES[ctx.mode]) switchMode(ctx.mode);
          openWindowSafe('win-workstation');
          renderContextList();
          updateOutputTargetTag();
          refresh({ immediate: true });
        }

        function bindEvents() {
          const modelSel = el('wsModelSelect');
          if (modelSel) {
            modelSel.onchange = () => {
              state.activeModelId = modelSel.value;
              renderActiveModelCard();
            };
          }
          const dirInput = el('wsDirectiveInput');
          if (dirInput) {
            dirInput.oninput = () => updateOutputTargetTag();
          }
          const maxCostSel = el('wsMaxCostSelect');
          if (maxCostSel) {
            maxCostSel.onchange = () => {
              state.maxCostUsd = Number(maxCostSel.value || 0.50);
              renderTrace();
            };
          }
          const enclChk = el('wsEnclaveGuardToggle');
          if (enclChk) enclChk.onchange = () => renderTrace();

          document.querySelectorAll('#win-workstation [data-ws-ctx-filter]').forEach((btn) => {
            btn.onclick = () => {
              state.ctxFilter = btn.dataset.wsCtxFilter || 'all';
              document.querySelectorAll('#win-workstation [data-ws-ctx-filter]').forEach((b) => {
                b.classList.toggle('is-active', b === btn);
              });
              renderContextList();
            };
          });

          document.querySelectorAll('#win-workstation [data-ws-tier]').forEach((btn) => {
            btn.onclick = () => {
              state.rodinTier = btn.dataset.wsTier || 'Regular';
              document.querySelectorAll('#win-workstation [data-ws-tier]').forEach((b) => {
                const active = b === btn;
                b.classList.toggle('is-active', active);
                b.setAttribute('aria-checked', active ? 'true' : 'false');
              });
            };
          });

          const artBtn = el('wsOpenArtcraftBtn');
          if (artBtn) artBtn.onclick = openInArtCraft;
          const saveGlbBtn = el('wsSaveGlbBtn');
          if (saveGlbBtn) saveGlbBtn.onclick = saveGlbToSpace;

          const proposeBtn = el('wsAuditProposeBtn');
          if (proposeBtn) proposeBtn.onclick = runAuditPropose;
          const commitBtn = el('wsAuditCommitBtn');
          if (commitBtn) commitBtn.onclick = commitAuditPatch;
          const revertBtn = el('wsAuditRevertBtn');
          if (revertBtn) revertBtn.onclick = revertLastPatch;
          const previewCommitBtn = el('wsPreviewCommitBtn');
          if (previewCommitBtn) previewCommitBtn.onclick = commitAuditPatch;
          const previewRevertBtn = el('wsPreviewRevertBtn');
          if (previewRevertBtn) previewRevertBtn.onclick = revertLastPatch;
          const previewRefreshBtn = el('wsPreviewRefreshBtn');
          if (previewRefreshBtn) previewRefreshBtn.onclick = fetchSpaceNotes;

          const arenaA = el('wsArenaModelA');
          const arenaB = el('wsArenaModelB');
          if (arenaA) arenaA.onchange = updateArenaLabels;
          if (arenaB) arenaB.onchange = updateArenaLabels;
          const swapBtn = el('wsArenaSwapBtn');
          if (swapBtn && arenaA && arenaB) {
            swapBtn.onclick = () => {
              const tmp = arenaA.value;
              arenaA.value = arenaB.value;
              arenaB.value = tmp;
              updateArenaLabels();
            };
          }
          const arenaRunBtn = el('wsArenaRunBtn');
          if (arenaRunBtn) arenaRunBtn.onclick = runArenaBenchmark;
          const voteA = el('wsArenaVoteA');
          const voteB = el('wsArenaVoteB');
          if (voteA) voteA.onclick = () => voteArena('A');
          if (voteB) voteB.onclick = () => voteArena('B');

          const handoffCommitBtn = el('wsHandoffCommitBtn');
          if (handoffCommitBtn) handoffCommitBtn.onclick = handoffCommitToSpace;
          const handoffBoardBtn = el('wsHandoffBoardBtn');
          if (handoffBoardBtn) handoffBoardBtn.onclick = handoffPostToBoard;
        }

        function observeVisibility() {
          const winEl = el('win-workstation');
          if (!winEl || typeof MutationObserver === 'undefined') return;
          wasVisible = isWindowVisible(winEl);
          if (visObserver) visObserver.disconnect();
          visObserver = new MutationObserver(() => {
            const nowVis = isWindowVisible(winEl);
            if (nowVis && !wasVisible) {
              wasVisible = true;
              refresh({ immediate: true });
            } else if (!nowVis) {
              wasVisible = false;
            }
          });
          visObserver.observe(winEl, { attributes: true, attributeFilter: ['class', 'style'] });
        }

        function init() {
          if (!state.initialized) {
            bindEvents();
            populateModelSelect();
            populateArenaSelects();
            renderContextList();
            updateOutputTargetTag();
            renderJobQueue();
            renderStagedOutputs();
            renderTrace();
            observeVisibility();
            state.initialized = true;
          }
          const winEl = el('win-workstation');
          const mountedInWorkstation = !!(document.getElementById('finderTab-3dstudio')?.querySelector('[data-ws-root="true"]'));
          if (isWindowVisible(winEl) || mountedInWorkstation) {
            refresh({ immediate: true });
          }
        }

        window.TinCanWorkstation = {
          version: 1,
          init,
          refresh,
          openWithContext,
          switchGateway,
          switchMode,
          tileWithSpace,
          dispatch,
        };

        if (document.readyState === 'loading') {
          document.addEventListener('DOMContentLoaded', init);
        } else {
          init();
        }
      })();
      </script>"""

    return (
        template.replace("__GATEWAYS_JSON__", gateways_json)
        .replace("__MODES_JSON__", modes_json)
        .replace("__TIERS_JSON__", tiers_json)
        .replace("__FALLBACK_JSON__", fallback_json)
    )


def render_workstation_window_html() -> str:
    """Render the complete ``#win-workstation`` Mesh OS studio window markup."""
    gateway_tabs = _render_gateway_tabs()
    cost_options = _render_cost_options()
    mode_tabs = _render_mode_tabs()
    rodin_tiers = _render_rodin_tiers()
    arena_col_a = _render_arena_column("A", "Frontier OpenRouter", "anthropic/claude-3.7-sonnet", "Model A")
    arena_col_b = _render_arena_column("B", "NanoGPT Heretic", "nanogpt/pqhaz/DeepSeek-V4.1-Flash-1017-heretic", "Model B")
    css_block = _workstation_css()
    js_block = _workstation_js()

    return f"""<div id="win-workstation" class="mesh-window w-[1080px] max-w-full hidden tc-ws-host" data-zen-window="true" data-window-id="win-workstation" style="top: 72px; left: 110px; z-index: 36;">
      <!--TC_TITLEBAR {{"id": "win-workstation", "title": "3D Studio", "badge": "RODIN + NANOGPT"}}-->
{css_block}
      <div class="window-body ws-body aeonik-scope" data-ws-root="true">
        <!-- Studio Header Strip -->
        <div class="ws-topbar">
          <div class="ws-top-group">
            <span class="ws-kicker">3D Studio</span>
            <span id="wsSpaceScopeBadge" class="ws-badge">user:default_user</span>
            <span id="wsMerkleBadge" class="ws-badge" title="Current Space Merkle Root">merkle: --</span>
          </div>
          <div class="ws-top-group">
            <span id="wsStatusPill" class="ws-badge ws-badge--pos">READY</span>
            <button id="wsRefreshBtn" type="button" class="ws-pill" onclick="window.TinCanWorkstation && window.TinCanWorkstation.refresh({{immediate: true}})" title="Refresh status, catalogs, and Space VFS">&#x21BB;&#xFE0E; Refresh</button>
            <button id="wsTileSpaceBtn" type="button" class="ws-pill" onclick="window.TinCanWorkstation && window.TinCanWorkstation.tileWithSpace()" title="Dock 3D Studio inside Workstation or open floating window">Dock in Workstation</button>
          </div>
        </div>

        <!-- 3-Pane Studio Workspace -->
        <div class="ws-grid">
          <!-- LEFT PANE (310px): Gateway, Model Card, Context Picker, Directive & Guardrails -->
          <aside class="ws-pane ws-pane--left" aria-label="Model gateway and context controls">
            <section class="ws-card">
              <div class="ws-sec-head">
                <span class="ws-sec-title">AI Gateway</span>
                <span class="ws-muted-xs">NanoGPT + OpenRouter</span>
              </div>
              <div class="ws-seg" role="tablist" aria-label="Model gateway switch">
                {gateway_tabs}
              </div>
              <select id="wsModelSelect" class="ws-select" aria-label="Select active model"></select>
              <div id="wsActiveModelCard" class="ws-model-card">
                <div class="ws-sec-head">
                  <span id="wsActiveModelName" class="ws-model-name">NanoGPT Private/TEE DeepSeek V4.1 Flash</span>
                  <span id="wsActiveModelBadge" class="ws-badge ws-badge--pos">ATTESTED</span>
                </div>
                <div id="wsActiveModelId" class="ws-mono-xs ws-muted ws-truncate">nanogpt/TEE/deepseek-v4.1-flash</div>
                <div class="ws-model-meta">
                  <span id="wsActiveModelCtx">1M ctx</span>
                  <span id="wsActiveModelPrice">$0.38 / $1.50 per 1M</span>
                </div>
              </div>
            </section>

            <section class="ws-card">
              <div class="ws-sec-head">
                <span class="ws-sec-title">Context Picker</span>
                <span id="wsSelectedCtxPath" class="ws-mono-xs ws-muted ws-truncate" style="max-width: 145px;">/src/main.py</span>
              </div>
              <div class="ws-top-group">
                <button type="button" class="ws-pill is-active" data-ws-ctx-filter="all">All</button>
                <button type="button" class="ws-pill" data-ws-ctx-filter="space">.space</button>
                <button type="button" class="ws-pill" data-ws-ctx-filter="drive">Drive</button>
              </div>
              <div id="wsContextList" class="ws-ctx-list" role="listbox" aria-label="Space and Drive context files">
                <div class="ws-muted-xs" style="padding: 8px;">Loading .space &amp; Drive files…</div>
              </div>
            </section>

            <section class="ws-card">
              <div class="ws-sec-head">
                <span class="ws-sec-title">Directive &amp; Guardrail</span>
                <label class="ws-check-label" title="Prefer zero-retention hardware TEE inference when available">
                  <input id="wsEnclaveGuardToggle" type="checkbox" checked>
                  <span>TEE Enclave</span>
                </label>
              </div>
              <textarea id="wsDirectiveInput" rows="3" class="ws-textarea" placeholder="Describe a 3D mesh for Rodin, a TEE patch directive, or an Arena benchmark prompt…"></textarea>
              <div class="ws-guardrail-row">
                <label for="wsMaxCostSelect" class="ws-sec-title">Max Cost Cap</label>
                <select id="wsMaxCostSelect" class="ws-select" style="width: auto; min-width: 112px;" aria-label="Maximum cost guardrail USD">
                  {cost_options}
                </select>
              </div>
              <button id="wsDispatchBtn" type="button" class="ws-btn ws-btn--solid ws-btn--full" onclick="window.TinCanWorkstation && window.TinCanWorkstation.dispatch()">Dispatch Run -&gt;</button>
            </section>
          </aside>

          <!-- CENTER PANE: Mode Switch, Active Stage (3D / TEE Audit / Arena), Persistent Patch Preview -->
          <main class="ws-pane ws-pane--center" aria-label="Workstation active stage">
            <div class="ws-stage-head">
              <div class="ws-seg ws-seg--auto" role="tablist" aria-label="Workstation modes">
                {mode_tabs}
              </div>
              <span id="wsOutputTargetTag" class="ws-badge" title="Active output target">/models3d/studio_mesh.glb</span>
            </div>

            <!-- Stage 1: 3D Rodin Stage (US-01) -->
            <section id="wsStage-3d" class="ws-stage-panel" aria-label="3D Rodin Stage">
              <div id="ws3dViewport" class="ws-3d-viewport">
                <div id="wsModelViewerStage"></div>
                <div id="wsWireframeFallback">
                  <svg class="ws-wire-svg" viewBox="0 0 160 120" aria-hidden="true">
                    <polygon points="80,14 132,42 132,84 80,110 28,84 28,42" stroke-width="1.5"/>
                    <polyline points="28,42 80,68 132,42" stroke-width="1.3"/>
                    <line x1="80" y1="68" x2="80" y2="110" stroke-width="1.3"/>
                    <polyline points="54,28 106,55 106,97" stroke-width="0.9" stroke-dasharray="3 3"/>
                    <polyline points="106,28 54,55 54,97" stroke-width="0.9" stroke-dasharray="3 3"/>
                    <ellipse cx="80" cy="64" rx="22" ry="12" stroke-width="1" stroke-dasharray="2 2"/>
                  </svg>
                  <div class="ws-kicker">Isometric Wireframe Preview</div>
                  <div id="ws3dMeshMeta" class="ws-mono-xs ws-muted">Ready · GLB binary target</div>
                  <div id="ws3dStatusNote" class="ws-mono-xs ws-muted">Dispatch a prompt to generate a Hyper3D Rodin .glb mesh (loads &lt;model-viewer&gt; when GLB bytes arrive).</div>
                </div>
              </div>
              <div class="ws-3d-controls">
                <div class="ws-tier-row" role="radiogroup" aria-label="Rodin generation tier">
                  {rodin_tiers}
                </div>
                <div class="ws-top-group">
                  <button id="wsOpenArtcraftBtn" type="button" class="ws-btn ws-btn--sm">Open in ArtCraft</button>
                  <button id="wsSaveGlbBtn" type="button" class="ws-btn ws-btn--sm ws-btn--solid">Save to .space</button>
                </div>
              </div>
            </section>

            <!-- Stage 2: TEE Audit & Diff (US-02) -->
            <section id="wsStage-audit" class="ws-stage-panel hidden" aria-label="TEE Audit and Diff">
              <div class="ws-card">
                <div class="ws-stage-head">
                  <div class="ws-top-group">
                    <span class="ws-sec-title">Audit Target</span>
                    <span id="wsAuditTargetPath" class="ws-badge">/src/main.py</span>
                    <span id="wsAuditModelTag" class="ws-badge ws-badge--pos">nanogpt/TEE/deepseek-v4.1-flash</span>
                  </div>
                  <div class="ws-top-group">
                    <button id="wsAuditProposeBtn" type="button" class="ws-btn ws-btn--sm ws-btn--solid">Propose Patch</button>
                    <button id="wsAuditCommitBtn" type="button" class="ws-btn ws-btn--sm ws-btn--pos">Commit Patch</button>
                    <button id="wsAuditRevertBtn" type="button" class="ws-btn ws-btn--sm ws-btn--danger">Revert Last</button>
                  </div>
                </div>
                <div id="wsAuditSummary" class="ws-mono-xs ws-muted">Click Propose Patch or Dispatch Run to compile a verified Space Notes diff via /api/space/notes/propose.</div>
                <div id="wsAuditDiffBox" class="ws-diff-box" aria-live="polite"><span class="ws-diff-ctx">Unified +/- patch preview will appear here.</span></div>
              </div>
            </section>

            <!-- Stage 3: Arena Benchmark (US-03) -->
            <section id="wsStage-arena" class="ws-stage-panel hidden" aria-label="Arena Benchmark">
              <div class="ws-arena-bar">
                <select id="wsArenaModelA" class="ws-select" aria-label="Arena Model A">
                  <option value="anthropic/claude-3.7-sonnet">Anthropic Claude 3.7 Sonnet</option>
                </select>
                <button id="wsArenaSwapBtn" type="button" class="ws-btn ws-btn--sm" title="Swap Model A and Model B">&#x21C4;</button>
                <select id="wsArenaModelB" class="ws-select" aria-label="Arena Model B">
                  <option value="nanogpt/pqhaz/DeepSeek-V4.1-Flash-1017-heretic">NanoGPT DeepSeek V4.1 Flash Heretic</option>
                </select>
                <button id="wsArenaRunBtn" type="button" class="ws-btn ws-btn--sm ws-btn--solid">Run Benchmark</button>
              </div>
              <div id="wsArenaGrid" class="ws-arena-grid">
                {arena_col_a}
                {arena_col_b}
              </div>
            </section>

            <!-- Persistent Space Notes Patch Preview Box -->
            <section id="wsPatchPreviewFrame" class="ws-patch-frame" aria-label="Space Notes Patch Preview">
              <div class="ws-sec-head">
                <div class="ws-top-group">
                  <span class="ws-sec-title">Space Notes Patch Preview</span>
                  <span id="wsNotesCountBadge" class="ws-badge">0 pending</span>
                  <span id="wsPlanIdBadge" class="ws-badge">no plan</span>
                </div>
                <div class="ws-top-group">
                  <button id="wsPreviewRefreshBtn" type="button" class="ws-btn ws-btn--sm">Notes</button>
                  <button id="wsPreviewCommitBtn" type="button" class="ws-btn ws-btn--sm ws-btn--pos">Commit</button>
                  <button id="wsPreviewRevertBtn" type="button" class="ws-btn ws-btn--sm ws-btn--danger">Revert</button>
                </div>
              </div>
              <div id="wsPatchPreviewDiff" class="ws-diff-box ws-diff-box--compact"><span class="ws-diff-ctx">Pending Space Notes and staged unified diffs appear here across all studio modes.</span></div>
            </section>
          </main>

          <!-- RIGHT PANE (310px): Telemetry Stats, Job Queue, Attestation Trace, Staged Outputs, Handoff -->
          <aside class="ws-pane ws-pane--right" aria-label="Telemetry, queue, and Space handoff">
            <div class="ws-stats-2up">
              <div class="ws-stat-card">
                <span class="ws-stat-label">RODIN CREDITS</span>
                <span id="wsStatRodinVal" class="ws-stat-val">-- CR</span>
                <span id="wsStatRodinSub" class="ws-stat-sub">Checking balance…</span>
              </div>
              <div class="ws-stat-card">
                <span class="ws-stat-label">NANOGPT POOL</span>
                <span id="wsStatNanoVal" class="ws-stat-val">-- TEE</span>
                <span id="wsStatNanoSub" class="ws-stat-sub">Loading catalog…</span>
              </div>
            </div>

            <section id="wsJobQueueCard" class="ws-card">
              <div class="ws-sec-head">
                <span class="ws-sec-title">Workstation Job Queue</span>
                <span class="ws-muted-xs">rodin · tee · arena</span>
              </div>
              <div id="wsJobQueueList" class="ws-queue-list"></div>
            </section>

            <section id="wsTraceCard" class="ws-card">
              <div class="ws-sec-head">
                <span class="ws-sec-title">Attestation &amp; Cost Trace</span>
              </div>
              <dl class="ws-trace-dl">
                <dt>Session Spend</dt>
                <dd id="wsTraceSpend">$0.0000 / $0.50 cap</dd>
                <dt>Privacy Mode</dt>
                <dd id="wsTracePrivacy">TEE Hardware Enclave</dd>
                <dt>Merkle Root</dt>
                <dd id="wsTraceMerkle">--</dd>
                <dt>Status</dt>
                <dd id="wsTraceNote">Idle · ready for dispatch</dd>
              </dl>
            </section>

            <section id="wsStagedCard" class="ws-card">
              <div class="ws-sec-head">
                <span class="ws-sec-title">Staged Outputs -&gt; .space</span>
              </div>
              <div id="wsStagedList" class="ws-staged-list"></div>
            </section>

            <section id="wsHandoffCard" class="ws-card ws-card--celadon">
              <div class="ws-sec-head">
                <span class="ws-sec-title">Space &amp; Mesh Handoff</span>
              </div>
              <button id="wsHandoffCommitBtn" type="button" class="ws-btn ws-btn--solid ws-btn--full">Commit Patch &amp; .glb to TinCan Space</button>
              <button id="wsHandoffBoardBtn" type="button" class="ws-btn ws-btn--full">Post to @board · WebRTC Review</button>
            </section>
          </aside>
        </div>
      </div>
{js_block}
    </div>"""
