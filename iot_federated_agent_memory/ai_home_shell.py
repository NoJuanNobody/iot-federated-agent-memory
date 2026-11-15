"""TinCan 2.2 · Aeonik Celadon & Ink AI Home Shell component.

Provides the unified AI Command Shell & Gateway Router hero, 4 equal workflow
launch cards (AI Copilot, AI Brain Arena, Rodin 3D + Space, Token Vault + Ads),
and monochrome telemetry sparkline strip scoped strictly under ``#aiHomeHub``.

Exports:
* ``WORKFLOW_CARDS``: tuple of the 4 AI workflow launch card definitions.
* ``ROUTER_CHIPS``: tuple of the 4 gateway router chip labels.
* ``render_ai_home_hub_html()``: self-contained fragment scoped under ``#aiHomeHub``.
* ``AI_HOME_SHELL_CSS`` / ``AI_HOME_SHELL_JS``: scoped stylesheet and controller script.
* ``apply_ai_home_shell(html)``: idempotent marker expander for
  ``<!--TC_AI_HOME_HUB-->``, ``/*TC_AI_HOME_CSS*/``, and ``/*TC_AI_HOME_JS*/``.
"""

from __future__ import annotations

import html as _html
from typing import Any, Dict, Tuple

HOME_HUB_MARKER = "<!--TC_AI_HOME_HUB-->"
HOME_CSS_SLOT = "/*TC_AI_HOME_CSS*/"
HOME_JS_SLOT = "/*TC_AI_HOME_JS*/"

#: 4 gateway router chips displayed beneath the tincan ask hero command input.
ROUTER_CHIPS: Tuple[str, ...] = (
    "ollama/qwen2.5:3b · $0 FREE",
    "FAU OWLCHAT · BYOK HPC",
    "NANOGPT TEE · $0.002/1K",
    "CLAUDE SONNET · SERVER POOL",
)

#: Gateway metadata keyed by exact chip label in ``ROUTER_CHIPS``.
ROUTER_CHIP_SPECS: Dict[str, Dict[str, str]] = {
    "ollama/qwen2.5:3b · $0 FREE": {
        "gateway": "ollama",
        "model": "ollama/qwen2.5:3b",
        "status": "LOCAL FIRST · OPENROUTER POOL PROTECTED",
    },
    "FAU OWLCHAT · BYOK HPC": {
        "gateway": "owlchat",
        "model": "owlchat/gpt-4o-mini",
        "status": "FAU OWLCHAT · HPC BYOK DIRECT",
    },
    "NANOGPT TEE · $0.002/1K": {
        "gateway": "nanogpt-tee",
        "model": "nanogpt/TEE/deepseek-v4.1-flash",
        "status": "NANOGPT TEE · ATTESTED ENCLAVE",
    },
    "CLAUDE SONNET · SERVER POOL": {
        "gateway": "openrouter",
        "model": "claude-brain",
        "status": "SERVER POOL · OPENROUTER METERED",
    },
}

#: 4 equal workflow launch cards rendered in the responsive 4-column grid.
WORKFLOW_CARDS: Tuple[Dict[str, Any], ...] = (
    {
        "id": "aiHomeCardCopilot",
        "title": "AI Copilot",
        "badge": "NEW WORKSPACE · /copilot",
        "window_id": "win-copilot",
        "fallback_window_id": "win-terminal",
        "route": "/copilot",
        "desc": "Dedicated thread workspace with .space code diffs, local Ollama zero-burn routing & live cost preview.",
        "metric": "RATE: 0 CR (Local) / 3 CR (Cloud)",
        "metric_tone": "ink",
        "progress_pct": 84,
        "cta": "Open AI Copilot \u2192",
        "cta_primary": True,
    },
    {
        "id": "aiHomeCardArena",
        "title": "AI Brain Arena",
        "badge": "BLIND DUEL · /arena",
        "window_id": "win-arena",
        "fallback_window_id": "win-arena",
        "route": "/arena",
        "desc": "Pit Local Open-Weight vs Frontier Cloud side-by-side with Vault RAG context & earn +25 XP per vote.",
        "metric": "SAVINGS: Up to 94% on Open-Weight",
        "metric_tone": "ink",
        "progress_pct": 72,
        "cta": "Start 2-Brain Duel \u2192",
        "cta_primary": False,
    },
    {
        "id": "aiHomeCardWorkstation",
        "title": "3D Studio + Workstation",
        "badge": "3D STUDIO · /3dstudio",
        "window_id": "win-workstation",
        "fallback_window_id": "win-agentspace",
        "route": "/workstation",
        "desc": "Generate GLB 3D meshes via Hyper3D Rodin v2 inside 3D Studio, synced directly with Workstation VFS & Sandboxes.",
        "metric": "DELIVERABLE COST: 750 CR / GLB (Ad-Earned)",
        "metric_tone": "ink",
        "progress_pct": 68,
        "cta": "Open 3D Studio \u2192",
        "cta_primary": False,
    },
    {
        "id": "aiHomeCardTokens",
        "title": "Ad Credits & Token Vault",
        "badge": "AD CREDITS · /tokens",
        "window_id": "win-billing",
        "fallback_window_id": "win-billing",
        "route": "/tokens",
        "desc": "Zero subscriptions. Watch Home Screen sponsor ads to earn tokens & AI credits for models and 3D deliverables.",
        "metric": "HOME AD REWARD: +5,000 CR ($5.00 USD) · NO SUBS",
        "metric_tone": "positive",
        "progress_pct": 62,
        "cta": "Watch Ads · Earn Credits \u2192",
        "cta_primary": False,
    },
)

#: Normalized heights (in viewBox px out of 36) for the monochrome sparkline bars.
SPARKLINE_BARS: Tuple[int, ...] = (
    8, 12, 16, 11, 20, 14, 24, 18, 12, 26, 17, 13, 28, 22,
    15, 30, 20, 14, 25, 19, 13, 27, 23, 16, 22, 18, 26, 21,
)


def _render_router_chip(index: int, label: str) -> str:
    spec = ROUTER_CHIP_SPECS[label]
    is_active = index == 0
    active_cls = " is-active" if is_active else ""
    pressed = "true" if is_active else "false"
    dot_html = '<span class="tc-ai-dot" aria-hidden="true"></span>' if is_active else ""
    return (
        f'<button type="button" class="tc-ai-chip{active_cls}" '
        f'data-gateway="{_html.escape(spec["gateway"], quote=True)}" '
        f'data-model="{_html.escape(spec["model"], quote=True)}" '
        f'data-chip-label="{_html.escape(label, quote=True)}" '
        f'data-status-text="{_html.escape(spec["status"], quote=True)}" '
        f'aria-pressed="{pressed}">{dot_html}<span>{_html.escape(label)}</span></button>'
    )


def _render_workflow_card(card: Dict[str, Any]) -> str:
    cid = _html.escape(str(card["id"]), quote=True)
    win_id = _html.escape(str(card["window_id"]), quote=True)
    fallback_id = _html.escape(str(card["fallback_window_id"]), quote=True)
    route = _html.escape(str(card["route"]), quote=True)
    badge = _html.escape(str(card["badge"]))
    title = _html.escape(str(card["title"]))
    desc = _html.escape(str(card["desc"]))
    metric = _html.escape(str(card["metric"]))
    cta = _html.escape(str(card["cta"]))
    is_primary = bool(card.get("cta_primary"))
    is_positive = card.get("metric_tone") == "positive"
    badge_cls = "tc-ai-badge is-solid" if is_primary else "tc-ai-badge"
    metric_cls = "tc-ai-card-metric is-positive" if is_positive else "tc-ai-card-metric"
    cta_cls = "tc-ai-card-cta is-primary" if is_primary else "tc-ai-card-cta"
    pct = max(8, min(100, int(card.get("progress_pct", 60))))
    return (
        f'<article id="{cid}" class="tc-ai-card" data-card-id="{cid}" '
        f'data-window="{win_id}" data-fallback-window="{fallback_id}" data-route="{route}">'
        '<div class="tc-ai-card-top">'
        f'<span class="{badge_cls}">{badge}</span>'
        f'<h3 class="tc-ai-card-title">{title}</h3>'
        f'<p class="tc-ai-card-desc">{desc}</p>'
        '</div>'
        '<div class="tc-ai-card-foot">'
        f'<div class="{metric_cls}">{metric}</div>'
        f'<div class="tc-ai-card-rail" aria-hidden="true"><span class="tc-ai-card-fill" style="width: {pct}%;"></span></div>'
        f'<button type="button" class="{cta_cls}" data-launch-card="{cid}" '
        f'data-window="{win_id}" data-fallback-window="{fallback_id}" data-route="{route}">{cta}</button>'
        '</div>'
        '</article>'
    )


def _render_sparkline_svg() -> str:
    step = 12
    bar_w = 5
    height = 38
    width = len(SPARKLINE_BARS) * step
    rects = "".join(
        f'<rect x="{idx * step + 3}" y="{height - bar_h}" width="{bar_w}" '
        f'height="{bar_h}" rx="1.5" fill="#111111" data-spark-bar="{idx}" '
        f'data-base-h="{bar_h}" />'
        for idx, bar_h in enumerate(SPARKLINE_BARS)
    )
    return (
        f'<svg id="aiHomeSparkline" class="tc-ai-sparkline" viewBox="0 0 {width} {height}" '
        'preserveAspectRatio="none" role="img" '
        'aria-label="Monochrome local routing ratio and .space telemetry sparkline">'
        f'{rects}</svg>'
    )


def render_ai_home_hub_html(*, include_assets: bool = False) -> str:
    """Render the self-contained Aeonik Celadon AI Home hub scoped under ``#aiHomeHub``."""
    chips_html = "\n          ".join(
        _render_router_chip(idx, label) for idx, label in enumerate(ROUTER_CHIPS)
    )
    cards_html = "\n        ".join(
        _render_workflow_card(card) for card in WORKFLOW_CARDS
    )
    sparkline_svg = _render_sparkline_svg()

    fragment = f"""<section id="aiHomeHub" class="tc-ai-home" aria-label="TinCan AI Home Shell" style="--tc-desk: #dfe6d7; --tc-bg: #ecf1e6; --tc-surface: #f4f8f0; --tc-card: #ffffff; --tc-ink: #111111; --tc-green: #107a47; --tc-crimson: #8a1c1c;">
  <div class="tc-ai-hero">
    <div class="tc-ai-hero-head">
      <span class="tc-ai-eyebrow">AI COMMAND SHELL &amp; GATEWAY ROUTER</span>
      <span id="aiHomeRouterStatus" class="tc-ai-status-pill" aria-live="polite">
        <span class="tc-ai-dot" aria-hidden="true"></span>
        <span data-role="status-text">LOCAL FIRST · OPENROUTER POOL PROTECTED</span>
      </span>
    </div>
    <form id="aiHomeCommandForm" class="tc-ai-cmd-bar" autocomplete="off">
      <span id="aiHomePromptPrefix" class="tc-ai-prompt-prefix">you@tincan:~/space$</span>
      <input id="aiHomePromptInput" type="text" class="tc-ai-prompt-input" autocomplete="off" spellcheck="false" aria-label="tincan ask command shell input" placeholder='tincan ask "Audit relay_router.py with .space RAG context"'>
      <button id="aiHomeDispatchBtn" type="submit" class="tc-ai-dispatch-btn">&#9654;&#xFE0E; Dispatch [Enter]</button>
    </form>
    <div class="tc-ai-chips-row" role="group" aria-label="AI gateway router presets">
      {chips_html}
    </div>
    <div id="aiHomeDispatchOut" class="tc-ai-output is-hidden" role="status" aria-live="polite">
      <div class="tc-ai-output-head">
        <span id="aiHomeDispatchMeta" class="tc-ai-output-meta">gateway · ready</span>
        <button id="aiHomeDispatchClear" type="button" class="tc-ai-output-close" aria-label="Clear dispatch output">&times;</button>
      </div>
      <pre id="aiHomeDispatchBody" class="tc-ai-output-body"></pre>
    </div>
  </div>

  <div class="tc-ai-cards-grid" aria-label="AI Workflows">
    {cards_html}
  </div>

  <div class="tc-ai-telemetry" aria-label="System and .space telemetry">
    <div class="tc-ai-telemetry-head">
      <span class="tc-ai-eyebrow">SYSTEM &amp; .SPACE TELEMETRY</span>
      <span id="aiHomeTelemetryMerkleBadge" class="tc-ai-merkle-pill" data-merkle-hook="space">
        <span class="tc-ai-dot" aria-hidden="true"></span>
        <span data-role="merkle-label">.space merkle · 7a4c9f</span>
      </span>
    </div>
    <div class="tc-ai-kpi-grid">
      <div class="tc-ai-kpi">
        <span class="tc-ai-kpi-label">LOCAL ROUTING</span>
        <strong id="aiHomeTelemetryLocal" class="tc-ai-kpi-val">100% Free</strong>
      </div>
      <div class="tc-ai-kpi">
        <span class="tc-ai-kpi-label">SAVED (OLLAMA)</span>
        <strong id="aiHomeTelemetrySaved" class="tc-ai-kpi-val">$14.80</strong>
      </div>
      <div class="tc-ai-kpi">
        <span class="tc-ai-kpi-label">AD ARBITRAGE</span>
        <strong id="aiHomeTelemetryArbitrage" class="tc-ai-kpi-val">+96% Net</strong>
      </div>
      <div class="tc-ai-kpi">
        <span class="tc-ai-kpi-label">MERKLE VFS</span>
        <strong id="aiHomeTelemetryMerkle" class="tc-ai-kpi-val tc-ai-mono" data-space-merkle="true">7a4c9f</strong>
      </div>
    </div>
    <div class="tc-ai-sparkline-wrap">
      {sparkline_svg}
    </div>
  </div>
</section>"""
    if not include_assets:
        return fragment
    return (
        f'<style id="tc-ai-home-css">\n{AI_HOME_SHELL_CSS}\n</style>\n'
        f"{fragment}\n"
        f'<script id="tc-ai-home-js">\n{AI_HOME_SHELL_JS}\n</script>'
    )


AI_HOME_SHELL_CSS = r"""
/* TinCan 2.2 · Aeonik Celadon & Ink AI Home Shell (#aiHomeHub) */
#aiHomeHub {
  --tc-desk: #dfe6d7;
  --tc-bg: #ecf1e6;
  --tc-surface: #f4f8f0;
  --tc-card: #ffffff;
  --tc-ink: #111111;
  --tc-muted: #4a4a4a;
  --tc-faint: #5c5c5c;
  --tc-green: #107a47;
  --tc-crimson: #8a1c1c;
  --tc-font: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --tc-mono: "JetBrains Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  font-family: var(--tc-font);
  color: var(--tc-ink);
  background: var(--tc-bg);
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 14px;
  box-sizing: border-box;
}

#aiHomeHub *,
#aiHomeHub *::before,
#aiHomeHub *::after {
  box-sizing: border-box;
}

#aiHomeHub .tc-ai-mono {
  font-family: var(--tc-mono);
}

#aiHomeHub .tc-ai-eyebrow {
  font-family: var(--tc-mono);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--tc-muted);
}

#aiHomeHub .tc-ai-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 9999px;
  background: var(--tc-green);
  flex-shrink: 0;
}

#aiHomeHub .tc-ai-hero,
#aiHomeHub .tc-ai-telemetry {
  background: var(--tc-card);
  border: 1px solid var(--tc-ink);
  border-radius: 16px;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

#aiHomeHub .tc-ai-hero-head,
#aiHomeHub .tc-ai-telemetry-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

#aiHomeHub .tc-ai-status-pill,
#aiHomeHub .tc-ai-merkle-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--tc-mono);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.03em;
  color: var(--tc-green);
}

#aiHomeHub .tc-ai-cmd-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--tc-card);
  border: 1px solid var(--tc-ink);
  border-radius: 12px;
  padding: 6px 8px 6px 14px;
}

#aiHomeHub .tc-ai-cmd-bar:focus-within {
  box-shadow: 0 0 0 2px rgba(17, 17, 17, 0.14);
}

#aiHomeHub .tc-ai-prompt-prefix {
  font-family: var(--tc-mono);
  font-size: 12px;
  font-weight: 600;
  color: var(--tc-ink);
  white-space: nowrap;
  flex-shrink: 0;
}

#aiHomeHub .tc-ai-prompt-input {
  flex: 1 1 auto;
  min-width: 0;
  border: 0;
  outline: none;
  background: transparent;
  color: var(--tc-ink);
  font-family: var(--tc-mono);
  font-size: 13px;
  line-height: 1.4;
  padding: 6px 0;
}

#aiHomeHub .tc-ai-prompt-input::placeholder {
  color: var(--tc-faint);
}

#aiHomeHub .tc-ai-dispatch-btn {
  appearance: none;
  border: 1px solid var(--tc-ink);
  background: var(--tc-ink);
  color: var(--tc-bg);
  font-family: var(--tc-font);
  font-size: 12px;
  font-weight: 600;
  padding: 8px 16px;
  border-radius: 9999px;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  transition: opacity 120ms ease, transform 120ms ease;
}

#aiHomeHub .tc-ai-dispatch-btn:hover {
  opacity: 0.88;
}

#aiHomeHub .tc-ai-dispatch-btn:active {
  transform: scale(0.98);
}

#aiHomeHub .tc-ai-chips-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

#aiHomeHub .tc-ai-chip {
  appearance: none;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 9999px;
  border: 1px solid var(--tc-ink);
  background: var(--tc-surface);
  color: var(--tc-ink);
  font-family: var(--tc-mono);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: background 120ms ease, color 120ms ease;
}

#aiHomeHub .tc-ai-chip:hover {
  background: var(--tc-desk);
}

#aiHomeHub .tc-ai-chip.is-active {
  background: var(--tc-ink);
  color: var(--tc-bg);
}

#aiHomeHub .tc-ai-output {
  background: var(--tc-surface);
  border: 1px solid var(--tc-ink);
  border-radius: 12px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

#aiHomeHub .tc-ai-output.is-hidden {
  display: none;
}

#aiHomeHub .tc-ai-output.is-error {
  border-color: var(--tc-crimson);
}

#aiHomeHub .tc-ai-output.is-error .tc-ai-output-meta,
#aiHomeHub .tc-ai-output.is-error .tc-ai-output-body {
  color: var(--tc-crimson);
}

#aiHomeHub .tc-ai-output-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

#aiHomeHub .tc-ai-output-meta {
  font-family: var(--tc-mono);
  font-size: 11px;
  font-weight: 600;
  color: var(--tc-green);
}

#aiHomeHub .tc-ai-output-close {
  appearance: none;
  border: 1px solid var(--tc-ink);
  background: transparent;
  color: var(--tc-ink);
  border-radius: 9999px;
  width: 22px;
  height: 22px;
  line-height: 1;
  font-size: 14px;
  cursor: pointer;
}

#aiHomeHub .tc-ai-output-body {
  margin: 0;
  font-family: var(--tc-mono);
  font-size: 12px;
  line-height: 1.5;
  color: var(--tc-ink);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 180px;
  overflow-y: auto;
}

#aiHomeHub .tc-ai-cards-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  align-items: stretch;
}

#aiHomeHub .tc-ai-card {
  background: var(--tc-card);
  border: 1px solid var(--tc-ink);
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 14px;
  min-width: 0;
  transition: transform 140ms ease, box-shadow 140ms ease;
}

#aiHomeHub .tc-ai-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(17, 17, 17, 0.08);
}

#aiHomeHub .tc-ai-card-top {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
}

#aiHomeHub .tc-ai-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 9999px;
  border: 1px solid var(--tc-ink);
  background: var(--tc-surface);
  color: var(--tc-ink);
  font-family: var(--tc-mono);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  white-space: nowrap;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

#aiHomeHub .tc-ai-badge.is-solid {
  background: var(--tc-ink);
  color: var(--tc-bg);
}

#aiHomeHub .tc-ai-card-title {
  margin: 0;
  font-family: var(--tc-font);
  font-size: 17px;
  font-weight: 700;
  letter-spacing: -0.015em;
  color: var(--tc-ink);
  line-height: 1.25;
}

#aiHomeHub .tc-ai-card-desc {
  margin: 0;
  font-size: 12px;
  line-height: 1.48;
  color: var(--tc-muted);
}

#aiHomeHub .tc-ai-card-foot {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

#aiHomeHub .tc-ai-card-metric {
  font-family: var(--tc-mono);
  font-size: 11px;
  font-weight: 600;
  color: var(--tc-ink);
}

#aiHomeHub .tc-ai-card-metric.is-positive {
  color: var(--tc-green);
}

#aiHomeHub .tc-ai-card-rail {
  width: 100%;
  height: 5px;
  border-radius: 9999px;
  border: 1px solid var(--tc-ink);
  background: var(--tc-desk);
  overflow: hidden;
}

#aiHomeHub .tc-ai-card-fill {
  display: block;
  height: 100%;
  background: var(--tc-ink);
}

#aiHomeHub .tc-ai-card-cta {
  appearance: none;
  width: 100%;
  padding: 9px 14px;
  border-radius: 9999px;
  border: 1px solid var(--tc-ink);
  background: var(--tc-card);
  color: var(--tc-ink);
  font-family: var(--tc-font);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  text-align: center;
  transition: background 120ms ease, color 120ms ease;
}

#aiHomeHub .tc-ai-card-cta:hover,
#aiHomeHub .tc-ai-card-cta.is-primary {
  background: var(--tc-ink);
  color: var(--tc-bg);
}

#aiHomeHub .tc-ai-card-cta.is-primary:hover {
  opacity: 0.88;
}

#aiHomeHub .tc-ai-kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

#aiHomeHub .tc-ai-kpi {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

#aiHomeHub .tc-ai-kpi-label {
  font-family: var(--tc-mono);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--tc-faint);
}

#aiHomeHub .tc-ai-kpi-val {
  font-family: var(--tc-font);
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--tc-ink);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

#aiHomeHub .tc-ai-sparkline-wrap {
  padding-top: 6px;
  border-top: 1px solid rgba(17, 17, 17, 0.14);
}

#aiHomeHub .tc-ai-sparkline {
  display: block;
  width: 100%;
  height: 36px;
}

@media (max-width: 980px) {
  #aiHomeHub .tc-ai-cards-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  #aiHomeHub .tc-ai-kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 560px) {
  #aiHomeHub .tc-ai-cards-grid,
  #aiHomeHub .tc-ai-kpi-grid {
    grid-template-columns: minmax(0, 1fr);
  }
  #aiHomeHub .tc-ai-cmd-bar {
    flex-wrap: wrap;
    padding: 8px 10px;
  }
  #aiHomeHub .tc-ai-dispatch-btn {
    width: 100%;
  }
}
"""


AI_HOME_SHELL_JS = r"""
    // =========================================================================
    // TinCanAIHome (ai_home_shell.py): Home shell router, cards & telemetry
    // =========================================================================
    window.TinCanAIHome = (function () {
      const state = {
        gateway: 'ollama',
        model: 'ollama/qwen2.5:3b',
        chipLabel: 'ollama/qwen2.5:3b \u00b7 $0 FREE',
        localCalls: 0,
        totalCalls: 0,
        savedUsd: 14.80,
      };
      let boundRoot = null;

      const SHELL_VERB_RE = /^(?:>|\$|ls|cat|open|tree|run|py|exec|runs|drive|status|brew|help|clear)(?:\s|$)/i;

      function rootEl() {
        return document.getElementById('aiHomeHub');
      }

      function setStatus(text) {
        const el = document.querySelector('#aiHomeRouterStatus [data-role="status-text"]');
        if (el) el.textContent = String(text || '');
      }

      function showOutput(meta, body, isError) {
        const box = document.getElementById('aiHomeDispatchOut');
        const metaEl = document.getElementById('aiHomeDispatchMeta');
        const bodyEl = document.getElementById('aiHomeDispatchBody');
        if (!box || !metaEl || !bodyEl) return;
        metaEl.textContent = String(meta || '');
        bodyEl.textContent = String(body || '');
        box.classList.toggle('is-error', !!isError);
        box.classList.remove('is-hidden');
      }

      function hideOutput() {
        const box = document.getElementById('aiHomeDispatchOut');
        if (box) box.classList.add('is-hidden');
      }

      function selectGateway(btn) {
        const hub = rootEl();
        if (!hub || !btn) return;
        const gw = btn.getAttribute('data-gateway') || 'ollama';
        const model = btn.getAttribute('data-model') || 'ollama/qwen2.5:3b';
        const label = btn.getAttribute('data-chip-label') || model;
        const statusText = btn.getAttribute('data-status-text') || (gw.toUpperCase() + ' READY');
        state.gateway = gw;
        state.model = model;
        state.chipLabel = label;

        hub.querySelectorAll('.tc-ai-chip[data-gateway]').forEach((chip) => {
          const on = chip === btn;
          chip.classList.toggle('is-active', on);
          chip.setAttribute('aria-pressed', on ? 'true' : 'false');
        });
        setStatus(statusText);
      }

      function bumpTelemetry(isLocal) {
        state.totalCalls += 1;
        if (isLocal) {
          state.localCalls += 1;
          state.savedUsd += 0.04;
        }
        const localEl = document.getElementById('aiHomeTelemetryLocal');
        const savedEl = document.getElementById('aiHomeTelemetrySaved');
        if (localEl && state.totalCalls > 0) {
          const pct = Math.round((state.localCalls / state.totalCalls) * 100);
          localEl.textContent = pct === 100 ? '100% Free' : `${pct}% Free`;
        }
        if (savedEl) {
          savedEl.textContent = `$${state.savedUsd.toFixed(2)}`;
        }
        const bars = document.querySelectorAll('#aiHomeSparkline [data-spark-bar]');
        if (bars.length) {
          const last = bars[bars.length - 1];
          const nextH = Math.max(8, Math.min(36, (isLocal ? 30 : 18) + (state.totalCalls % 6)));
          last.setAttribute('height', String(nextH));
          last.setAttribute('y', String(38 - nextH));
        }
      }

      function openWindowTarget(winId, fallbackId, route) {
        const ev = new CustomEvent('tincan:ai-home-launch', {
          cancelable: true,
          detail: { windowId: winId, fallbackWindowId: fallbackId, route: route }
        });
        if (!window.dispatchEvent(ev)) return false;

        const target = (winId && document.getElementById(winId)) ||
          (fallbackId && document.getElementById(fallbackId)) || null;
        if (target) {
          const isHidden = target.style.display === 'none' ||
            target.classList.contains('hidden') ||
            target.classList.contains('minimized');
          if (isHidden && typeof window.toggleWindow === 'function') {
            window.toggleWindow(target.id);
          } else {
            target.style.display = 'flex';
            target.classList.remove('hidden', 'minimized');
            if (typeof window.bringToFront === 'function') window.bringToFront(target);
            if (typeof window.syncDockIndicators === 'function') window.syncDockIndicators();
          }
          return true;
        }
        if (route && typeof window.location === 'object' && typeof window.location.assign === 'function') {
          window.location.assign(route);
        }
        return false;
      }

      async function dispatch(overrideLine) {
        const input = document.getElementById('aiHomePromptInput');
        const raw = String(overrideLine != null ? overrideLine : (input ? input.value : '')).trim();
        if (!raw) {
          if (input) input.focus();
          showOutput('command shell · idle', 'Enter a tincan ask prompt or .space shell command.', false);
          return { ok: false, text: '' };
        }

        const isShell = SHELL_VERB_RE.test(raw) || /^tincan\s+(?!ask\b)/i.test(raw);
        const shellLine = raw.replace(/^[>$]\s*/, '').replace(/^tincan\s+(?=status\b|brew\b)/i, '');
        const cleanPrompt = raw.replace(/^(?:tincan\s+)?ask\s+/i, '').replace(/^["'](.*)["']$/, '$1');
        const btn = document.getElementById('aiHomeDispatchBtn');
        if (btn) btn.disabled = true;

        try {
          if (isShell && window.TinCanShell && typeof window.TinCanShell.run === 'function') {
            showOutput(`shell · ${shellLine}`, 'Executing in .space shell…', false);
            const res = await window.TinCanShell.run(shellLine, { gateway: state.gateway, model: state.model });
            const ok = !!(res && res.ok);
            const text = (res && res.text) != null ? String(res.text) : '';
            showOutput(`shell · ${ok ? 'ok' : 'error'}`, text, !ok);
            return { ok, text };
          }

          if (typeof fetch !== 'function' && window.TinCanShell && typeof window.TinCanShell.run === 'function') {
            const res = await window.TinCanShell.run(`ask ${cleanPrompt}`, { gateway: state.gateway, model: state.model });
            const ok = !!(res && res.ok);
            const text = (res && res.text) != null ? String(res.text) : '';
            showOutput(`${state.model} · ${ok ? 'ok' : 'error'}`, text, !ok);
            return { ok, text };
          }

          const peerId = (typeof window.myPeerId === 'string' && window.myPeerId) || 'home';
          showOutput(`${state.model} · routing via ${state.gateway}`, 'Dispatching prompt…', false);
          const resp = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              model: state.model,
              gateway: state.gateway,
              prompt: cleanPrompt,
              peer_id: peerId,
            }),
          });
          const data = await resp.json().catch(() => ({}));
          if (!resp.ok || data.error) {
            const errMsg = data.error || `HTTP ${resp.status}`;
            showOutput(`${state.model} · error`, errMsg, true);
            return { ok: false, text: errMsg };
          }
          const reply = data.content || data.response || JSON.stringify(data);
          const isLocal = state.gateway === 'ollama' || state.gateway === 'owlchat';
          bumpTelemetry(isLocal);
          showOutput(`${state.model} · ${isLocal ? '0 CR local' : 'routed'}`, reply, false);
          return { ok: true, text: String(reply) };
        } catch (err) {
          const msg = err && err.message ? err.message : String(err);
          showOutput(`${state.model} · error`, msg, true);
          return { ok: false, text: msg };
        } finally {
          if (btn) btn.disabled = false;
        }
      }

      async function refreshTelemetry() {
        if (typeof fetch !== 'function') return null;
        try {
          const scope = typeof window.termScope === 'function' ? window.termScope() : 'user';
          const owner = typeof window.termOwner === 'function'
            ? window.termOwner()
            : ((typeof window.myPeerId === 'string' && window.myPeerId) || 'default');
          const r = await fetch(`/api/space/ls?scope=${encodeURIComponent(scope)}&owner_id=${encodeURIComponent(owner)}`, { cache: 'no-store' });
          if (!r.ok) return null;
          const s = await r.json();
          const root = String(s.merkle_root || '').slice(0, 6);
          if (root) {
            const valEl = document.getElementById('aiHomeTelemetryMerkle');
            const badgeEl = document.querySelector('#aiHomeTelemetryMerkleBadge [data-role="merkle-label"]');
            if (valEl) valEl.textContent = root;
            if (badgeEl) badgeEl.textContent = `.space merkle · ${root}`;
          }
          return s;
        } catch (e) {
          return null;
        }
      }

      function init() {
        const hub = rootEl();
        if (!hub || boundRoot === hub) return;
        boundRoot = hub;

        hub.addEventListener('click', (ev) => {
          const chip = ev.target.closest('.tc-ai-chip[data-gateway]');
          if (chip && hub.contains(chip)) {
            selectGateway(chip);
            return;
          }
          const cardTrigger = ev.target.closest('[data-launch-card], .tc-ai-card[data-window]');
          if (cardTrigger && hub.contains(cardTrigger)) {
            openWindowTarget(
              cardTrigger.getAttribute('data-window'),
              cardTrigger.getAttribute('data-fallback-window'),
              cardTrigger.getAttribute('data-route')
            );
          }
        });

        const form = document.getElementById('aiHomeCommandForm');
        if (form) {
          form.addEventListener('submit', (ev) => {
            ev.preventDefault();
            dispatch();
          });
        }
        const clearBtn = document.getElementById('aiHomeDispatchClear');
        if (clearBtn) clearBtn.addEventListener('click', hideOutput);

        window.addEventListener('tincan:space-changed', refreshTelemetry);
        refreshTelemetry();
      }

      if (typeof document !== 'undefined') {
        if (document.readyState === 'loading') {
          document.addEventListener('DOMContentLoaded', init);
        } else {
          init();
        }
      }

      return {
        version: 1,
        state,
        init,
        dispatch,
        selectGateway,
        openWindowTarget,
        refreshTelemetry,
      };
    })();
"""


def apply_ai_home_shell(html: str) -> str:
    """Replace AI home hub markers in ``html`` if present (idempotent).

    Leaves unmatched strings completely untouched so standalone fragments or
    callers without every slot remain safe.
    """
    if not isinstance(html, str) or not html:
        return html
    out = html
    if HOME_HUB_MARKER in out:
        out = out.replace(HOME_HUB_MARKER, render_ai_home_hub_html())
    if HOME_CSS_SLOT in out:
        out = out.replace(HOME_CSS_SLOT, AI_HOME_SHELL_CSS)
    if HOME_JS_SLOT in out:
        out = out.replace(HOME_JS_SLOT, AI_HOME_SHELL_JS)
    return out
