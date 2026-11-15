"""TinCan Mesh OS: Aeonik Celadon & Ink AI Copilot & Multi-Model Router window.

Exports ``COPILOT_CSS``, ``COPILOT_SCRIPT``, ``render_copilot_window_html() -> str``,
and ``apply_copilot_ui(html: str) -> str`` for ``#win-copilot``.

All styling is strictly scoped under ``#win-copilot`` using the Aeonik Celadon & Ink
design tokens (``#ecf1e6``, ``#f4f8f0``, ``#ffffff``, ``#111111``, ``#107a47``,
``#8a1c1c``) with ``Inter`` + ``JetBrains Mono`` and zero legacy dark slate or neon
utility classes.
"""

from __future__ import annotations

import html as _html
import json
from typing import Any, Dict, List, Tuple

COPILOT_WINDOW_ID = "win-copilot"
COPILOT_WINDOW_SLOT = "<!--TC_COPILOT_WINDOW-->"
COPILOT_CSS_SLOT = "/*TC_COPILOT_CSS*/"
COPILOT_JS_SLOT = "/*TC_COPILOT_JS*/"

# (priority_key, pill_label, gateway_id, default_model, header_route, status_pill, route_badge)
PRIORITY_DEFS: Tuple[Tuple[str, str, str, str, str, str, str], ...] = (
    (
        "local",
        "Local Free",
        "ollama",
        "ollama/qwen2.5:3b",
        "direct ollama localhost:11434",
        "DIRECT LOCALHOST:11434 · 0ms HOP",
        "LOCAL ZERO-BURN",
    ),
    (
        "owlchat",
        "OwlChat",
        "fau-owlchat",
        "owlchat/llama-3.3-70b",
        "direct fau-owlchat hpc",
        "FAU OWLCHAT HPC · BYOK 0 CR",
        "BYOK HPC",
    ),
    (
        "tee",
        "TEE",
        "nanogpt-tee",
        "nanogpt/TEE/deepseek-v4.1-flash",
        "nanogpt-tee enclave",
        "NANOGPT TEE · HARDWARE ATTESTED",
        "TEE ATTESTED",
    ),
    (
        "cloud",
        "Cloud",
        "openrouter",
        "anthropic/claude-3.7-sonnet",
        "openrouter pooled",
        "OPENROUTER POOLED · CLOUD",
        "CLOUD POOLED",
    ),
)

DEFAULT_GATEWAY_CARDS: Tuple[Dict[str, Any], ...] = (
    {
        "id": "ollama",
        "name": "ollama (local)",
        "priority": 1,
        "priority_key": "local",
        "rate_label": "FREE · $0.00",
        "quota_pct": 100,
        "is_zero_burn": True,
    },
    {
        "id": "fau-owlchat",
        "name": "fau-owlchat",
        "priority": 2,
        "priority_key": "owlchat",
        "rate_label": "BYOK · HPC",
        "quota_pct": 82,
        "is_zero_burn": True,
    },
    {
        "id": "nanogpt-tee",
        "name": "nanogpt-tee",
        "priority": 3,
        "priority_key": "tee",
        "rate_label": "$0.00 pool",
        "quota_pct": 34,
        "is_zero_burn": False,
    },
    {
        "id": "openrouter",
        "name": "openrouter",
        "priority": 4,
        "priority_key": "cloud",
        "rate_label": "$0.00 pool",
        "quota_pct": 48,
        "is_zero_burn": False,
    },
)

DEFAULT_COPILOT_MODELS: List[Dict[str, Any]] = [
    {
        "id": "ollama/qwen2.5:3b",
        "label": "ollama/qwen2.5:3b (Local)",
        "gateway": "ollama",
        "priority_key": "local",
        "in_per_1m": 0.0,
        "out_per_1m": 0.0,
    },
    {
        "id": "ollama/qwen2.5-coder:7b",
        "label": "ollama/qwen2.5-coder:7b (Local)",
        "gateway": "ollama",
        "priority_key": "local",
        "in_per_1m": 0.0,
        "out_per_1m": 0.0,
    },
    {
        "id": "ollama/llama3.2:3b",
        "label": "ollama/llama3.2:3b (Local)",
        "gateway": "ollama",
        "priority_key": "local",
        "in_per_1m": 0.0,
        "out_per_1m": 0.0,
    },
    {
        "id": "owlchat/llama-3.3-70b",
        "label": "owlchat/llama-3.3-70b (HPC)",
        "gateway": "fau-owlchat",
        "priority_key": "owlchat",
        "in_per_1m": 0.0,
        "out_per_1m": 0.0,
    },
    {
        "id": "owlchat/qwen2.5-coder-32b",
        "label": "owlchat/qwen2.5-coder-32b (HPC)",
        "gateway": "fau-owlchat",
        "priority_key": "owlchat",
        "in_per_1m": 0.0,
        "out_per_1m": 0.0,
    },
    {
        "id": "trussed/deepseek-r1",
        "label": "trussed/deepseek-r1 (HPC)",
        "gateway": "fau-owlchat",
        "priority_key": "owlchat",
        "in_per_1m": 0.0,
        "out_per_1m": 0.0,
    },
    {
        "id": "nanogpt/TEE/deepseek-v4.1-flash",
        "label": "nanogpt/TEE/deepseek-v4.1-flash (TEE)",
        "gateway": "nanogpt-tee",
        "priority_key": "tee",
        "in_per_1m": 0.375,
        "out_per_1m": 1.50,
    },
    {
        "id": "nanogpt/TEE/gemma-4-26b-a4b-uncensored",
        "label": "nanogpt/TEE/gemma-4-26b-a4b-uncensored (TEE)",
        "gateway": "nanogpt-tee",
        "priority_key": "tee",
        "in_per_1m": 0.15,
        "out_per_1m": 0.70,
    },
    {
        "id": "nanogpt/pqhaz/DeepSeek-V4.1-Flash-1017-heretic",
        "label": "nanogpt/DeepSeek-V4.1-Flash-heretic (NanoGPT)",
        "gateway": "nanogpt-tee",
        "priority_key": "tee",
        "in_per_1m": 0.198,
        "out_per_1m": 0.792,
    },
    {
        "id": "anthropic/claude-3.7-sonnet",
        "label": "anthropic/claude-3.7-sonnet (Cloud)",
        "gateway": "openrouter",
        "priority_key": "cloud",
        "in_per_1m": 3.00,
        "out_per_1m": 15.00,
    },
    {
        "id": "google/gemini-2.5-flash",
        "label": "google/gemini-2.5-flash (Cloud)",
        "gateway": "openrouter",
        "priority_key": "cloud",
        "in_per_1m": 0.15,
        "out_per_1m": 0.60,
    },
    {
        "id": "openai/gpt-4o",
        "label": "openai/gpt-4o (Cloud)",
        "gateway": "openrouter",
        "priority_key": "cloud",
        "in_per_1m": 2.50,
        "out_per_1m": 10.00,
    },
    {
        "id": "deepseek/deepseek-r1",
        "label": "deepseek/deepseek-r1 (Cloud)",
        "gateway": "openrouter",
        "priority_key": "cloud",
        "in_per_1m": 0.55,
        "out_per_1m": 2.19,
    },
]

_SEED_DIFF_LINES: Tuple[Tuple[str, str], ...] = (
    ("file", "iot_federated_agent_memory/ai_gateway.py · direct local + OpenAI-compat"),
    ("add", '+ DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"'),
    ("add", '+ OWLCHAT_BASE_URL        = "https://chat.hpc.fau.edu/openai"'),
    ("add", '+ TRUSSED_AI_BASE_URL     = "https://trussed.ai.hpc.fau.edu/provider/generic"'),
    ("add", "+ if gw in _OPENAI_COMPAT_GATEWAYS: # 0 CR · no cloud fallback"),
)


def _safe_json_for_script(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=True).replace("</", "<\\/")


COPILOT_CSS = r"""
/* TinCan Copilot & Multi-Model Router (Aeonik Celadon & Ink) */
#win-copilot {
  --cp-bg: #ecf1e6;
  --cp-card: #f4f8f0;
  --cp-paper: #ffffff;
  --cp-ink: #111111;
  --cp-muted: #4a4a4a;
  --cp-faint: #5c5c5c;
  --cp-pos: #107a47;
  --cp-pos-bg: #eaf5ee;
  --cp-danger: #8a1c1c;
  --cp-danger-bg: #fceeee;
  --cp-hair: 1px solid #111111;
  --cp-hair-soft: 1px solid rgba(17, 17, 17, 0.16);
  --cp-font: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --cp-mono: "JetBrains Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace;
}
#win-copilot .hidden { display: none !important; }
#win-copilot .cp-body {
  display: flex;
  flex-direction: column;
  height: min(720px, calc(100vh - 140px));
  min-height: 440px;
  overflow: hidden;
  padding: 0;
  background: var(--cp-bg);
  color: var(--cp-ink);
  font-family: var(--cp-font);
  font-size: 12px;
  container-type: inline-size;
  container-name: cpbody;
}
#win-copilot.maximized .cp-body,
#win-copilot.popout-fullscreen .cp-body {
  height: 100%;
  max-height: none;
}
#win-copilot .cp-grid {
  flex: 1 1 auto;
  min-height: 0;
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  overflow: hidden;
}
#win-copilot .cp-sidebar {
  min-width: 0;
  min-height: 0;
  overflow-y: auto;
  padding: 10px;
  background: var(--cp-card);
  border-right: var(--cp-hair);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
#win-copilot .cp-main {
  min-width: 0;
  min-height: 0;
  padding: 10px 12px;
  background: var(--cp-bg);
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow: hidden;
}
#win-copilot .cp-sec {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}
#win-copilot .cp-sec-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--cp-faint);
}
#win-copilot .cp-sec-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}
#win-copilot .cp-card {
  background: var(--cp-paper);
  border: var(--cp-hair);
  border-radius: 12px;
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 7px;
  min-width: 0;
}
#win-copilot .cp-card--celadon { background: var(--cp-card); }
#win-copilot .cp-mono { font-family: var(--cp-mono); }
#win-copilot .cp-mono-xs { font-family: var(--cp-mono); font-size: 10px; line-height: 1.45; }
#win-copilot .cp-muted { color: var(--cp-muted); }
#win-copilot .cp-pos { color: var(--cp-pos); }
#win-copilot .cp-danger { color: var(--cp-danger); }
#win-copilot .cp-truncate {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Segmented priority selector */
#win-copilot .cp-seg {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  width: 100%;
  border: var(--cp-hair);
  border-radius: 9999px;
  overflow: hidden;
  background: var(--cp-paper);
}
#win-copilot .cp-seg-btn {
  padding: 5px 4px;
  border: 0;
  border-right: var(--cp-hair-soft);
  background: transparent;
  color: var(--cp-ink);
  font-family: var(--cp-font);
  font-size: 10px;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  transition: background 120ms ease, color 120ms ease;
}
#win-copilot .cp-seg-btn:last-child { border-right: 0; }
#win-copilot .cp-seg-btn:hover { background: rgba(17, 17, 17, 0.08); }
#win-copilot .cp-seg-btn.is-active {
  background: var(--cp-ink);
  color: var(--cp-paper);
}

/* Gateway quota meters */
#win-copilot .cp-gw-list {
  display: flex;
  flex-direction: column;
  gap: 7px;
}
#win-copilot .cp-gw-row {
  display: flex;
  flex-direction: column;
  gap: 3px;
  width: 100%;
  padding: 3px 4px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--cp-ink);
  text-align: left;
  cursor: pointer;
  transition: background 120ms ease;
}
#win-copilot .cp-gw-row:hover { background: var(--cp-card); }
#win-copilot .cp-gw-row.is-active { background: var(--cp-card); }
#win-copilot .cp-gw-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  font-family: var(--cp-mono);
  font-size: 10px;
  font-weight: 600;
}
#win-copilot .cp-meter-track {
  width: 100%;
  height: 5px;
  border-radius: 9999px;
  background: rgba(17, 17, 17, 0.14);
  overflow: hidden;
}
#win-copilot .cp-meter-fill {
  height: 100%;
  border-radius: 9999px;
  background: var(--cp-ink);
  transition: width 180ms ease;
}
#win-copilot .cp-meter-fill--pos { background: var(--cp-pos); }

/* Context file chips */
#win-copilot .cp-ctx-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
#win-copilot .cp-ctx-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  padding: 4px 7px;
  border: var(--cp-hair-soft);
  border-radius: 8px;
  background: var(--cp-card);
  font-family: var(--cp-mono);
  font-size: 10px;
}
#win-copilot .cp-ctx-remove {
  border: 0;
  background: transparent;
  color: var(--cp-faint);
  font-family: var(--cp-mono);
  font-size: 10px;
  cursor: pointer;
  padding: 0 2px;
}
#win-copilot .cp-ctx-remove:hover { color: var(--cp-danger); }
#win-copilot .cp-attach-drawer {
  border-top: var(--cp-hair-soft);
  padding-top: 6px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 132px;
  overflow-y: auto;
}
#win-copilot .cp-attach-pick {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  width: 100%;
  padding: 3px 6px;
  border: var(--cp-hair-soft);
  border-radius: 6px;
  background: var(--cp-paper);
  color: var(--cp-ink);
  font-family: var(--cp-mono);
  font-size: 10px;
  cursor: pointer;
  text-align: left;
}
#win-copilot .cp-attach-pick:hover { background: var(--cp-card); }
#win-copilot .cp-attach-pick.is-attached {
  background: var(--cp-ink);
  color: var(--cp-paper);
}

/* Pills & buttons */
#win-copilot .cp-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 5px 12px;
  border: var(--cp-hair);
  border-radius: 9999px;
  background: var(--cp-paper);
  color: var(--cp-ink);
  font-family: var(--cp-font);
  font-size: 11px;
  font-weight: 600;
  line-height: 1.3;
  white-space: nowrap;
  cursor: pointer;
  transition: background 120ms ease, color 120ms ease, opacity 120ms ease;
}
#win-copilot .cp-btn:hover { background: var(--cp-ink); color: var(--cp-paper); }
#win-copilot .cp-btn:disabled { opacity: 0.45; cursor: not-allowed; }
#win-copilot .cp-btn--solid {
  background: var(--cp-ink);
  color: var(--cp-paper);
}
#win-copilot .cp-btn--solid:hover { opacity: 0.86; }
#win-copilot .cp-btn--sm { padding: 2px 9px; font-size: 10px; }
#win-copilot .cp-btn--full { width: 100%; padding: 7px 12px; font-size: 11px; }
#win-copilot .cp-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 9px;
  border: var(--cp-hair);
  border-radius: 9999px;
  background: var(--cp-paper);
  color: var(--cp-ink);
  font-family: var(--cp-mono);
  font-size: 10px;
  font-weight: 600;
  white-space: nowrap;
}
#win-copilot .cp-badge--ink {
  background: var(--cp-ink);
  color: var(--cp-paper);
}
#win-copilot .cp-badge--pos {
  border-color: var(--cp-pos);
  background: var(--cp-pos-bg);
  color: var(--cp-pos);
}
#win-copilot .cp-badge--danger {
  border-color: var(--cp-danger);
  background: var(--cp-danger-bg);
  color: var(--cp-danger);
}
#win-copilot .cp-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 9999px;
  background: var(--cp-ink);
  flex: 0 0 auto;
}
#win-copilot .cp-dot--pos { background: var(--cp-pos); }
#win-copilot .cp-dot--paper { background: var(--cp-paper); }

/* Right thread column */
#win-copilot .cp-thread-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 7px 10px;
  background: var(--cp-paper);
  border: var(--cp-hair);
  border-radius: 12px;
  flex: 0 0 auto;
}
#win-copilot .cp-thread-meta {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  font-family: var(--cp-mono);
  font-size: 11px;
  min-width: 0;
}
#win-copilot .cp-stream {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-right: 2px;
}
#win-copilot .cp-msg {
  border: var(--cp-hair);
  border-radius: 12px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
#win-copilot .cp-msg--user { background: var(--cp-card); }
#win-copilot .cp-msg--assistant { background: var(--cp-paper); }
#win-copilot .cp-msg-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
#win-copilot .cp-msg-lead {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
#win-copilot .cp-msg-body {
  font-size: 12px;
  line-height: 1.5;
  color: var(--cp-ink);
  white-space: pre-wrap;
  word-break: break-word;
}
#win-copilot .cp-diff-box {
  background: var(--cp-card);
  border: var(--cp-hair-soft);
  border-radius: 8px;
  padding: 8px 10px;
  font-family: var(--cp-mono);
  font-size: 11px;
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre;
}
#win-copilot .cp-diff-line { display: block; padding: 0 4px; border-radius: 2px; }
#win-copilot .cp-diff-file { color: var(--cp-faint); font-weight: 600; margin-bottom: 3px; }
#win-copilot .cp-diff-add { color: var(--cp-pos); background: var(--cp-pos-bg); }
#win-copilot .cp-diff-del { color: var(--cp-danger); background: var(--cp-danger-bg); }
#win-copilot .cp-diff-hunk { color: var(--cp-faint); font-weight: 700; }
#win-copilot .cp-diff-ctx { color: var(--cp-ink); }
#win-copilot .cp-actions-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

/* Composer */
#win-copilot .cp-composer {
  flex: 0 0 auto;
  background: var(--cp-paper);
  border: var(--cp-hair);
  border-radius: 12px;
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
#win-copilot .cp-textarea {
  width: 100%;
  min-width: 0;
  resize: none;
  border: 0;
  outline: none;
  background: transparent;
  color: var(--cp-ink);
  font-family: var(--cp-mono);
  font-size: 11px;
  line-height: 1.45;
  padding: 2px 0;
}
#win-copilot .cp-composer-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  border-top: var(--cp-hair-soft);
  padding-top: 7px;
}
#win-copilot .cp-select {
  max-width: 280px;
  min-width: 0;
  background: var(--cp-card);
  color: var(--cp-ink);
  border: var(--cp-hair);
  border-radius: 9999px;
  padding: 4px 12px;
  font-family: var(--cp-mono);
  font-size: 11px;
  font-weight: 600;
  outline: none;
  cursor: pointer;
}
#win-copilot .cp-select:focus {
  box-shadow: 0 0 0 2px rgba(17, 17, 17, 0.16);
}
#win-copilot .cp-arbitrage-lines {
  display: flex;
  flex-direction: column;
  gap: 3px;
  font-family: var(--cp-mono);
  font-size: 10px;
  line-height: 1.45;
}

/* Responsive collapse on narrow viewports or narrow tiled containers */
@media (max-width: 920px) {
  #win-copilot .cp-body {
    height: auto;
    max-height: calc(100vh - 120px);
    overflow-y: auto;
  }
  #win-copilot .cp-grid {
    grid-template-columns: 1fr;
    overflow: visible;
  }
  #win-copilot .cp-sidebar {
    border-right: 0;
    border-bottom: var(--cp-hair);
    overflow-y: visible;
  }
  #win-copilot .cp-main { overflow: visible; }
}
@container cpbody (max-width: 820px) {
  #win-copilot .cp-body { overflow-y: auto; }
  #win-copilot .cp-grid {
    grid-template-columns: 1fr;
    overflow: visible;
  }
  #win-copilot .cp-sidebar {
    border-right: 0;
    border-bottom: var(--cp-hair);
    overflow-y: visible;
  }
  #win-copilot .cp-main { overflow: visible; }
}
"""


def _render_priority_pills() -> str:
    parts = []
    for idx, (prio_key, label, _gw, _model, _route, _status, _badge) in enumerate(PRIORITY_DEFS):
        active = " is-active" if idx == 0 else ""
        selected = "true" if idx == 0 else "false"
        parts.append(
            f'<button id="copilotPrioBtn-{prio_key}" type="button" role="tab" aria-selected="{selected}" '
            f'data-copilot-priority="{prio_key}" class="cp-seg-btn{active}" '
            f'onclick="window.TinCanCopilot && window.TinCanCopilot.setPriority(\'{prio_key}\')">'
            f"{_html.escape(label)}</button>"
        )
    return "".join(parts)


def _render_initial_gateways() -> str:
    rows = []
    for idx, gw in enumerate(DEFAULT_GATEWAY_CARDS):
        active = " is-active" if idx == 0 else ""
        rate_cls = "cp-pos" if gw["is_zero_burn"] else "cp-muted"
        fill_cls = "cp-meter-fill cp-meter-fill--pos" if gw["id"] == "ollama" else "cp-meter-fill"
        rows.append(
            f'<button type="button" class="cp-gw-row{active}" data-copilot-gw="{_html.escape(gw["id"])}" '
            f'onclick="window.TinCanCopilot && window.TinCanCopilot.setPriority(\'{_html.escape(gw["priority_key"])}\')">'
            f'<div class="cp-gw-top"><span>{_html.escape(gw["name"])}</span>'
            f'<span class="{rate_cls}">{_html.escape(gw["rate_label"])}</span></div>'
            f'<div class="cp-meter-track"><div class="{fill_cls}" style="width: {int(gw["quota_pct"])}%;"></div></div>'
            f"</button>"
        )
    return "".join(rows)


def _render_model_options() -> str:
    opts = []
    for item in DEFAULT_COPILOT_MODELS:
        mid = _html.escape(str(item["id"]))
        lbl = _html.escape(str(item["label"]))
        sel = " selected" if item["id"] == "ollama/qwen2.5:3b" else ""
        opts.append(f'<option value="{mid}"{sel}>{lbl}</option>')
    return "".join(opts)


def _render_seed_diff_html() -> str:
    lines = []
    for kind, text in _SEED_DIFF_LINES:
        lines.append(f'<span class="cp-diff-line cp-diff-{kind}">{_html.escape(text)}</span>')
    return "".join(lines)


def _build_copilot_script() -> str:
    priorities_json = _safe_json_for_script(
        {
            p[0]: {
                "label": p[1],
                "gateway": p[2],
                "defaultModel": p[3],
                "headerRoute": p[4],
                "statusPill": p[5],
                "routeBadge": p[6],
            }
            for p in PRIORITY_DEFS
        }
    )
    gateways_json = _safe_json_for_script(list(DEFAULT_GATEWAY_CARDS))
    models_json = _safe_json_for_script(DEFAULT_COPILOT_MODELS)

    raw_js = r"""(function () {
  if (typeof window === 'undefined' || typeof document === 'undefined') return;

  const PRIORITIES = __PRIORITIES_JSON__;
  const DEFAULT_GATEWAYS = __GATEWAYS_JSON__;
  const DEFAULT_MODELS = __MODELS_JSON__;

  const state = {
    initialized: false,
    priority: 'local',
    model: 'ollama/qwen2.5:3b',
    threadId: '',
    threadName: 'tincan-terminal-ai',
    scope: 'user',
    ownerId: 'default_user',
    merkleRoot: '',
    gateways: DEFAULT_GATEWAYS.map((g) => Object.assign({}, g)),
    models: DEFAULT_MODELS.map((m) => Object.assign({}, m)),
    spaceFiles: [],
    driveFiles: [],
    attachedFiles: [
      { path: '/ai_gateway.py', source: 'space', tag: 'PY', estTokens: 2140, rag: false },
      { path: '/tincan_agent.py', source: 'space', tag: 'PY', estTokens: 1080, rag: false },
      { path: '/Vault/FAU-Thesis.md', source: 'drive', tag: 'MD', estTokens: 860, rag: true }
    ],
    attachDrawerOpen: false,
    arbitrage: {
      localTurns: 0,
      cloudTurns: 0,
      usdSaved: 0.0,
      totalTokens: 0
    },
    turns: [
      {
        id: 'seed-1',
        prompt: 'Audit our TinCan router and patch direct local Ollama + FAU OwlChat dispatch without burning OpenRouter credits.',
        reply: 'Direct routing active. Requests with ollama/, owlchat/, trussed/, or --base-url bypass the relay and keep pooled OpenRouter balances untouched.',
        model: 'ollama/qwen2.5:3b',
        gateway: 'ollama',
        creditsBilled: 0,
        costUsd: 0.0,
        tokPerSec: 410,
        ttftSec: 0.38,
        routeBadge: 'LOCAL ZERO-BURN',
        diffText: [
          '--- a/iot_federated_agent_memory/ai_gateway.py',
          '+++ b/iot_federated_agent_memory/ai_gateway.py',
          '@@ -20,3 +20,4 @@',
          '+ DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"',
          '+ OWLCHAT_BASE_URL        = "https://chat.hpc.fau.edu/openai"',
          '+ TRUSSED_AI_BASE_URL     = "https://trussed.ai.hpc.fau.edu/provider/generic"',
          '+ if gw in _OPENAI_COMPAT_GATEWAYS: # 0 CR · no cloud fallback'
        ].join('\n'),
        patchPath: '/iot_federated_agent_memory/ai_gateway.py'
      }
    ],
    seededOnly: true
  };

  const controllers = {};

  function el(id) {
    return document.getElementById(id);
  }

  function esc(val) {
    return String(val == null ? '' : val).replace(/[&<>"']/g, (c) => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    }[c]));
  }

  function safeGetStorage(key) {
    try {
      if (typeof localStorage !== 'undefined' && localStorage) {
        return localStorage.getItem(key) || '';
      }
    } catch (e) {}
    return '';
  }

  function resolvePeerId() {
    if (typeof window.myPeerId === 'string' && window.myPeerId) return window.myPeerId;
    return safeGetStorage('tincan_peer_id') || 'peer';
  }

  function resolveUserHandle() {
    const raw = safeGetStorage('tincan_username').trim().replace(/^@+/, '');
    return raw || resolvePeerId() || 'alejandro';
  }

  function resolveSpaceContext() {
    const scopeEl = el('spaceScopeSelect');
    const ownerEl = el('spaceOwnerInput');
    if (scopeEl && scopeEl.value) state.scope = scopeEl.value;
    else if (typeof window.currentSpaceScope === 'string' && window.currentSpaceScope) state.scope = window.currentSpaceScope;
    if (ownerEl && ownerEl.value) state.ownerId = ownerEl.value;
    else if (typeof window.currentSpaceOwner === 'string' && window.currentSpaceOwner) state.ownerId = window.currentSpaceOwner;
    else state.ownerId = resolvePeerId() || 'default_user';
  }

  function notify(msg, isError) {
    if (!isError && typeof window.showQuickNotification === 'function') {
      try { window.showQuickNotification(msg); return; } catch (e) {}
    }
    const statusEl = el('copilotActiveStatus');
    if (statusEl) {
      statusEl.textContent = msg;
      statusEl.className = isError ? 'cp-badge cp-badge--danger' : 'cp-badge cp-badge--pos';
    }
  }

  async function apiJson(url, opts) {
    if (typeof fetch !== 'function') {
      throw new Error('fetch unavailable');
    }
    opts = opts || {};
    const channel = opts.channel;
    let signal;
    if (channel && typeof AbortController !== 'undefined') {
      if (controllers[channel]) {
        try { controllers[channel].abort(); } catch (e) {}
      }
      controllers[channel] = new AbortController();
      signal = controllers[channel].signal;
    }
    const headers = opts.body ? { 'Content-Type': 'application/json' } : {};
    const res = await fetch(url, {
      method: opts.method || (opts.body ? 'POST' : 'GET'),
      headers,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
      credentials: 'same-origin',
      signal
    });
    let data = {};
    try { data = await res.json(); } catch (e) { data = {}; }
    if (!res.ok) {
      const err = new Error((data && data.error) || ('HTTP ' + res.status));
      err.status = res.status;
      err.data = data;
      throw err;
    }
    return data;
  }

  function classifyModelGateway(modelId) {
    const low = String(modelId || '').toLowerCase();
    if (!low || low.indexOf('ollama/') === 0 || low === 'ollama-brain' || low.indexOf('local/') === 0 || low.indexOf('openai-compat/') === 0) {
      return 'ollama';
    }
    if (low.indexOf('owlchat/') === 0 || low === 'owlchat-brain' || low.indexOf('trussed/') === 0 || low === 'trussed-brain') {
      return 'fau-owlchat';
    }
    if (low.indexOf('nanogpt/') === 0 || low === 'nanogpt-brain' || low.indexOf('/tee/') !== -1) {
      return 'nanogpt-tee';
    }
    return 'openrouter';
  }

  function priorityForGateway(gw) {
    if (gw === 'ollama') return 'local';
    if (gw === 'fau-owlchat') return 'owlchat';
    if (gw === 'nanogpt-tee') return 'tee';
    return 'cloud';
  }

  function findModelMeta(modelId) {
    return state.models.find((m) => m.id === modelId) || null;
  }

  function estimatePreflight(modelId, promptText) {
    const alias = String(modelId || state.model || 'ollama/qwen2.5:3b').trim();
    const chars = String(promptText || '').length;
    const estPromptTokens = chars > 0 ? Math.max(1, Math.ceil(chars / 4)) : 128;
    const estCompTokens = Math.max(128, Math.min(1024, Math.floor(estPromptTokens / 2) + 128));
    const gw = classifyModelGateway(alias);
    const isZeroBurn = gw === 'ollama' || gw === 'fau-owlchat';

    const cloudEqUsd = (estPromptTokens / 1000000) * 3.0 + (estCompTokens / 1000000) * 15.0;
    const cloudEqCredits = Math.max(3, Math.round(cloudEqUsd * 1000));

    if (isZeroBurn) {
      return {
        model_alias: alias,
        gateway: gw,
        is_zero_burn: true,
        estimated_credits: 0,
        estimated_usd: 0.0,
        cloud_equivalent_credits: cloudEqCredits,
        recommended_route: gw === 'fau-owlchat' ? 'direct fau-owlchat hpc' : 'direct ollama localhost:11434',
        display_badge: 'Est: 0 CR Free | Cloud Eq: ' + cloudEqCredits + ' CR'
      };
    }

    const meta = findModelMeta(alias);
    const inRate = meta && typeof meta.in_per_1m === 'number' ? meta.in_per_1m : (gw === 'nanogpt-tee' ? 0.5 : 1.0);
    const outRate = meta && typeof meta.out_per_1m === 'number' ? meta.out_per_1m : (gw === 'nanogpt-tee' ? 1.5 : 3.0);
    const estUsd = (estPromptTokens / 1000000) * inRate + (estCompTokens / 1000000) * outRate;
    const estCredits = Math.max(1, Math.round(estUsd * 1000));
    return {
      model_alias: alias,
      gateway: gw,
      is_zero_burn: false,
      estimated_credits: estCredits,
      estimated_usd: estUsd,
      cloud_equivalent_credits: Math.max(estCredits, cloudEqCredits),
      recommended_route: gw === 'nanogpt-tee' ? 'nanogpt-tee enclave' : 'openrouter pooled',
      display_badge: 'Est: ' + estCredits + ' CR (~$' + estUsd.toFixed(4) + ')'
    };
  }

  function updatePreflightBadge() {
    const badge = el('copilotPreflightCost');
    const inp = el('copilotPromptInput');
    const sel = el('copilotModelSelect');
    const modelId = (sel && sel.value) || state.model;
    const text = (inp && inp.value) || '';
    const est = estimatePreflight(modelId, text);
    if (badge) {
      badge.textContent = est.display_badge;
      badge.className = est.is_zero_burn ? 'cp-badge cp-badge--pos' : 'cp-badge';
    }
    return est;
  }

  function renderPriorityUI() {
    const info = PRIORITIES[state.priority] || PRIORITIES.local;
    Object.keys(PRIORITIES).forEach((key) => {
      const btn = el('copilotPrioBtn-' + key);
      if (btn) {
        const active = key === state.priority;
        btn.classList.toggle('is-active', active);
        btn.setAttribute('aria-selected', active ? 'true' : 'false');
      }
    });
    const headerRoute = el('copilotHeaderRoute');
    if (headerRoute) headerRoute.textContent = info.headerRoute;
    const activeStatus = el('copilotActiveStatus');
    if (activeStatus) {
      activeStatus.innerHTML = '<span class="cp-dot cp-dot--pos"></span><span>' + esc(info.statusPill) + '</span>';
      activeStatus.className = 'cp-badge cp-badge--pos';
    }
    renderGatewayCards();
  }

  function renderGatewayCards() {
    const container = el('copilotGatewaysList');
    if (!container) return;
    const activeGw = (PRIORITIES[state.priority] || PRIORITIES.local).gateway;
    container.innerHTML = state.gateways.map((gw) => {
      const isAct = gw.id === activeGw;
      const rateCls = gw.is_zero_burn ? 'cp-pos' : 'cp-muted';
      const fillCls = gw.id === 'ollama' ? 'cp-meter-fill cp-meter-fill--pos' : 'cp-meter-fill';
      const pct = Math.max(6, Math.min(100, Number(gw.quota_pct || 0)));
      return (
        '<button type="button" class="cp-gw-row' + (isAct ? ' is-active' : '') + '" ' +
        'data-copilot-gw="' + esc(gw.id) + '" ' +
        'onclick="window.TinCanCopilot && window.TinCanCopilot.setPriority(\'' + esc(gw.priority_key || priorityForGateway(gw.id)) + '\')">' +
        '<div class="cp-gw-top"><span>' + esc(gw.name) + '</span>' +
        '<span class="' + rateCls + '">' + esc(gw.rate_label) + '</span></div>' +
        '<div class="cp-meter-track"><div class="' + fillCls + '" style="width: ' + pct + '%;"></div></div>' +
        '</button>'
      );
    }).join('');
  }

  function renderModelSelect() {
    const sel = el('copilotModelSelect');
    if (!sel) return;
    const seen = new Set();
    const opts = [];
    state.models.forEach((m) => {
      if (!m || !m.id || seen.has(m.id)) return;
      seen.add(m.id);
      opts.push('<option value="' + esc(m.id) + '">' + esc(m.label || m.id) + '</option>');
    });
    sel.innerHTML = opts.join('');
    if (seen.has(state.model)) {
      sel.value = state.model;
    } else if (state.models.length) {
      state.model = state.models[0].id;
      sel.value = state.model;
    }
    updatePreflightBadge();
  }

  function renderContextFiles() {
    const box = el('copilotContextFiles');
    if (box) {
      if (!state.attachedFiles.length) {
        box.innerHTML = '<div class="cp-mono-xs cp-muted">No files attached. Click below to attach .space or Drive context.</div>';
      } else {
        box.innerHTML = state.attachedFiles.map((f, idx) => {
          const badgeTxt = f.rag ? '<span class="cp-pos">RAG ON</span>' : '<span class="cp-muted">' + Number(f.estTokens || 0).toLocaleString() + ' tok</span>';
          const shortName = String(f.path || '').replace(/^\/+/, '');
          return (
            '<div class="cp-ctx-item" data-copilot-ctx="' + esc(f.path) + '">' +
            '<span class="cp-truncate">[' + esc(f.tag || 'FILE') + '] ' + esc(shortName) + '</span>' +
            '<span style="display:inline-flex;align-items:center;gap:4px;flex:0 0 auto;">' + badgeTxt +
            '<button type="button" class="cp-ctx-remove" title="Remove context file" aria-label="Remove ' + esc(shortName) + '" ' +
            'onclick="window.TinCanCopilot && window.TinCanCopilot.removeContextFile(' + idx + ')">&#x2715;</button></span>' +
            '</div>'
          );
        }).join('');
      }
    }
    renderAttachDrawer();
  }

  function renderAttachDrawer() {
    const drawer = el('copilotAttachDrawer');
    if (!drawer) return;
    drawer.classList.toggle('hidden', !state.attachDrawerOpen);
    if (!state.attachDrawerOpen) return;

    const candidates = [];
    state.spaceFiles.forEach((f) => {
      if (f && f.path) candidates.push({ path: f.path, source: 'space', size: Number(f.size_bytes || 0) });
    });
    state.driveFiles.forEach((f) => {
      const p = typeof f === 'string' ? f : (f && (f.path || f.name));
      if (p) candidates.push({ path: p, source: 'drive', size: Number((f && f.size_bytes) || 0) });
    });

    if (!candidates.length) {
      drawer.innerHTML = '<div class="cp-mono-xs cp-muted">No extra .space or Drive files found yet.</div>';
      return;
    }
    const attachedSet = new Set(state.attachedFiles.map((a) => a.path));
    drawer.innerHTML = candidates.slice(0, 24).map((c) => {
      const isAtt = attachedSet.has(c.path);
      return (
        '<button type="button" class="cp-attach-pick' + (isAtt ? ' is-attached' : '') + '" ' +
        'onclick="window.TinCanCopilot && window.TinCanCopilot.attachContextFile(\'' + esc(c.path).replace(/'/g, '\\\'') + '\', \'' + esc(c.source) + '\')">' +
        '<span class="cp-truncate">' + esc(c.path) + '</span>' +
        '<span>' + esc(isAtt ? 'ATTACHED' : c.source.toUpperCase()) + '</span>' +
        '</button>'
      );
    }).join('');
  }

  function renderArbitrageStats() {
    const localEl = el('copilotLocalTurns');
    const burnedEl = el('copilotBurnedUsd');
    const savedEl = el('copilotSavedUsd');
    const merkleEl = el('copilotThreadMerkle');
    if (localEl) localEl.textContent = String(state.arbitrage.localTurns);
    if (burnedEl) burnedEl.textContent = '$0.00';
    if (savedEl) savedEl.textContent = '$' + Number(state.arbitrage.usdSaved || 0).toFixed(2);
    if (merkleEl) {
      merkleEl.textContent = state.merkleRoot
        ? String(state.merkleRoot).slice(0, 10) + ' persisted'
        : (state.threadId ? String(state.threadId).slice(0, 8) + ' persisted' : 'ready');
    }
  }

  function extractDiffAndPath(text) {
    const raw = String(text || '');
    const fenceMatch = raw.match(/```(?:diff|patch|python|py|js|ts|sh|bash)?\n([\s\S]*?)```/);
    const block = fenceMatch ? fenceMatch[1] : raw;
    const lines = block.split('\n');
    const hasDiffMarkers = lines.some((l) => l.indexOf('+++ ') === 0 || l.indexOf('--- ') === 0 || l.indexOf('@@ ') === 0) ||
      (lines.some((l) => l.indexOf('+ ') === 0 || (l.indexOf('+') === 0 && l.indexOf('+++') !== 0)) &&
       lines.some((l) => l.indexOf('- ') === 0 || (l.indexOf('-') === 0 && l.indexOf('---') !== 0)));
    if (!hasDiffMarkers && !fenceMatch) {
      return { diffText: '', patchPath: '' };
    }
    let patchPath = '';
    for (let i = 0; i < lines.length; i++) {
      const m = lines[i].match(/^\+\+\+\s+(?:b\/)?(.+)$/);
      if (m && m[1] && m[1] !== '/dev/null') {
        patchPath = m[1].trim();
        break;
      }
    }
    return { diffText: block.trim(), patchPath };
  }

  function renderDiffHtml(diffText) {
    return String(diffText || '').split('\n').map((line) => {
      let cls = 'cp-diff-ctx';
      if (line.indexOf('--- ') === 0 || line.indexOf('+++ ') === 0) cls = 'cp-diff-file';
      else if (line.indexOf('@@') === 0) cls = 'cp-diff-hunk';
      else if (line.indexOf('+') === 0) cls = 'cp-diff-add';
      else if (line.indexOf('-') === 0) cls = 'cp-diff-del';
      return '<span class="cp-diff-line ' + cls + '">' + esc(line) + '</span>';
    }).join('');
  }

  function renderThreadLog() {
    const log = el('copilotThreadLog');
    if (!log) return;
    const handle = resolveUserHandle();
    const tidTag = el('copilotThreadIdTag');
    if (tidTag) {
      tidTag.textContent = state.threadId ? ('threads/' + String(state.threadId).slice(0, 8)) : 'threads/new';
    }
    if (!state.turns.length) {
      log.innerHTML =
        '<div class="cp-msg cp-msg--assistant">' +
        '<div class="cp-msg-head">' +
        '<span class="cp-badge cp-badge--ink"><span class="cp-dot cp-dot--paper"></span><span>' + esc(state.model) + '</span></span>' +
        '<span class="cp-badge">NEW THREAD</span>' +
        '</div>' +
        '<div class="cp-msg-body">Thread ready. Messages dispatched with ollama/, owlchat/, or trussed/ route directly with 0 CR OpenRouter burn.</div>' +
        '</div>';
      return;
    }

    log.innerHTML = state.turns.map((turn, idx) => {
      const tid = esc(turn.id || ('turn-' + idx));
      const userCard =
        '<article class="cp-msg cp-msg--user" data-copilot-turn="' + tid + '">' +
        '<div class="cp-mono-xs cp-muted">@' + esc(handle) + ' · /chat</div>' +
        '<div class="cp-msg-body">' + esc(turn.prompt) + '</div>' +
        '</article>';

      const telemStr = Number(turn.creditsBilled || 0) === 0
        ? ('0 CR BILLED ($0.0000)' + (turn.tokPerSec ? ' · ' + turn.tokPerSec + ' tok/s' : '') + (turn.ttftSec ? ' · ' + Number(turn.ttftSec).toFixed(2) + 's TTFT' : ''))
        : (Number(turn.creditsBilled) + ' CR BILLED ($' + Number(turn.costUsd || 0).toFixed(4) + ')');

      const diffBlock = turn.diffText
        ? '<div class="cp-diff-box">' + renderDiffHtml(turn.diffText) + '</div>'
        : '';

      const statusNote = turn.actionNote
        ? '<div class="cp-mono-xs ' + (turn.actionError ? 'cp-danger' : 'cp-pos') + '">' + esc(turn.actionNote) + '</div>'
        : '';

      const assistantCard =
        '<article class="cp-msg cp-msg--assistant" data-copilot-reply="' + tid + '">' +
        '<div class="cp-msg-head">' +
        '<div class="cp-msg-lead">' +
        '<span class="cp-badge cp-badge--ink"><span class="cp-dot cp-dot--paper"></span><span>' + esc(turn.model) + '</span></span>' +
        '<span class="cp-mono-xs cp-pos">' + esc(telemStr) + '</span>' +
        '</div>' +
        '<span class="cp-badge">' + esc(turn.routeBadge || 'LOCAL ZERO-BURN') + '</span>' +
        '</div>' +
        '<div class="cp-msg-body">' + esc(turn.reply) + '</div>' +
        diffBlock +
        statusNote +
        '<div class="cp-actions-row">' +
        '<button type="button" class="cp-btn cp-btn--solid" onclick="window.TinCanCopilot && window.TinCanCopilot.applyPatch(\'' + tid + '\')">Apply Patch to .space &#x2192;</button>' +
        '<button type="button" class="cp-btn" onclick="window.TinCanCopilot && window.TinCanCopilot.duelInArena(\'' + tid + '\')">Duel in /arena</button>' +
        '<button type="button" class="cp-btn" onclick="window.TinCanCopilot && window.TinCanCopilot.runPytestInSpace(\'' + tid + '\')">&#x25B6; Run pytest in .space</button>' +
        '</div>' +
        '</article>';

      return userCard + assistantCard;
    }).join('');
    log.scrollTop = log.scrollHeight;
  }

  function setPriority(prioKey) {
    if (!PRIORITIES[prioKey]) return;
    state.priority = prioKey;
    const info = PRIORITIES[prioKey];
    const matching = state.models.find((m) => m.priority_key === prioKey || m.gateway === info.gateway);
    state.model = (matching && matching.id) || info.defaultModel;
    const sel = el('copilotModelSelect');
    if (sel) sel.value = state.model;
    renderPriorityUI();
    updatePreflightBadge();
  }

  function selectModel(modelId) {
    if (!modelId) return;
    state.model = String(modelId);
    const gw = classifyModelGateway(state.model);
    state.priority = priorityForGateway(gw);
    const sel = el('copilotModelSelect');
    if (sel) sel.value = state.model;
    renderPriorityUI();
    updatePreflightBadge();
  }

  function removeContextFile(idx) {
    if (idx < 0 || idx >= state.attachedFiles.length) return;
    state.attachedFiles.splice(idx, 1);
    renderContextFiles();
  }

  function toggleAttachDrawer() {
    state.attachDrawerOpen = !state.attachDrawerOpen;
    renderAttachDrawer();
    if (state.attachDrawerOpen) {
      refreshSpaceAndDrive();
    }
  }

  function attachContextFile(path, source) {
    if (!path) return;
    const existingIdx = state.attachedFiles.findIndex((f) => f.path === path);
    if (existingIdx !== -1) {
      state.attachedFiles.splice(existingIdx, 1);
      renderContextFiles();
      return;
    }
    const ext = (String(path).split('.').pop() || 'TXT').toUpperCase().slice(0, 4);
    const spaceHit = state.spaceFiles.find((f) => f.path === path);
    const size = spaceHit ? Number(spaceHit.size_bytes || 0) : 512;
    state.attachedFiles.push({
      path,
      source: source || 'space',
      tag: ext,
      estTokens: Math.max(12, Math.ceil(size / 4)),
      rag: ext === 'MD' || ext === 'TXT'
    });
    renderContextFiles();
  }

  async function refreshAnalytics() {
    try {
      const data = await apiJson('/api/models/analytics', { channel: 'analytics' });
      const orInfo = (data && data.openrouter) || {};
      const ngInfo = (data && data.nanogpt) || {};
      const providers = (data && data.providers) || {};

      let localCalls = 0;
      let cloudCalls = 0;
      let totalTokens = Number((data && data.total_tokens) || 0);
      Object.keys(providers).forEach((k) => {
        const p = providers[k] || {};
        const gw = String(p.gateway || classifyModelGateway(p.model || k)).toLowerCase();
        const calls = Number(p.total_calls || 0);
        if (gw === 'ollama' || gw === 'local' || gw === 'owlchat' || gw === 'trussed' || gw === 'fau-owlchat') {
          localCalls += calls;
        } else {
          cloudCalls += calls;
        }
      });

      if (localCalls > state.arbitrage.localTurns) state.arbitrage.localTurns = localCalls;
      if (cloudCalls > state.arbitrage.cloudTurns) state.arbitrage.cloudTurns = cloudCalls;
      if (totalTokens > state.arbitrage.totalTokens) state.arbitrage.totalTokens = totalTokens;
      if (state.arbitrage.localTurns > 0) {
        state.arbitrage.usdSaved = Math.max(state.arbitrage.usdSaved, state.arbitrage.localTurns * 0.02);
      }

      const ngBal = Number(ngInfo.account_remaining_balance_usd || 0);
      const orBal = Number(orInfo.account_remaining_balance_usd || 0);
      state.gateways = state.gateways.map((gw) => {
        if (gw.id === 'nanogpt-tee') {
          return Object.assign({}, gw, {
            rate_label: (ngInfo.connected || ngBal > 0) ? ('$' + ngBal.toFixed(2) + ' pool') : '$0.00 pool',
            quota_pct: (ngInfo.connected || ngBal > 0) ? Math.min(100, Math.max(14, Math.round((ngBal / 50) * 100))) : gw.quota_pct
          });
        }
        if (gw.id === 'openrouter') {
          return Object.assign({}, gw, {
            rate_label: (orInfo.connected || orBal > 0) ? ('$' + orBal.toFixed(2) + ' pool') : '$0.00 pool',
            quota_pct: (orInfo.connected || orBal > 0) ? Math.min(100, Math.max(14, Math.round((orBal / 150) * 100))) : gw.quota_pct
          });
        }
        return gw;
      });
      renderGatewayCards();
      renderArbitrageStats();
    } catch (e) {}
  }

  async function refreshModels() {
    const merged = DEFAULT_MODELS.map((m) => Object.assign({}, m));
    const seen = new Set(merged.map((m) => m.id));
    const endpoints = [
      { url: '/api/models/available?gateway=ollama', gw: 'ollama', prio: 'local' },
      { url: '/api/models/nanogpt?live=0', gw: 'nanogpt-tee', prio: 'tee' },
      { url: '/api/models/openrouter', gw: 'openrouter', prio: 'cloud' }
    ];
    for (let i = 0; i < endpoints.length; i++) {
      const ep = endpoints[i];
      try {
        const data = await apiJson(ep.url, { channel: 'models_' + ep.prio });
        const list = Array.isArray(data) ? data : (data.models || []);
        list.forEach((item) => {
          if (!item || !item.id || seen.has(item.id)) return;
          if (String(item.id).indexOf('ronin/') === 0) return;
          seen.add(item.id);
          const gw = classifyModelGateway(item.id);
          const pricing = item.pricing || {};
          const inRate = pricing.prompt_per_1m != null ? Number(pricing.prompt_per_1m) : (Number(pricing.prompt || 0) * 1000000);
          const outRate = pricing.completion_per_1m != null ? Number(pricing.completion_per_1m) : (Number(pricing.completion || 0) * 1000000);
          merged.push({
            id: item.id,
            label: item.id + ' (' + (gw === 'ollama' ? 'Local' : (gw === 'fau-owlchat' ? 'HPC' : (gw === 'nanogpt-tee' ? 'TEE' : 'Cloud'))) + ')',
            gateway: gw,
            priority_key: priorityForGateway(gw),
            in_per_1m: Number.isFinite(inRate) ? inRate : 0.0,
            out_per_1m: Number.isFinite(outRate) ? outRate : 0.0
          });
        });
      } catch (e) {}
    }
    state.models = merged;
    renderModelSelect();
  }

  async function refreshSpaceAndDrive() {
    resolveSpaceContext();
    try {
      const sp = await apiJson(
        '/api/space/ls?scope=' + encodeURIComponent(state.scope) + '&owner_id=' + encodeURIComponent(state.ownerId),
        { channel: 'spaceLs' }
      );
      state.spaceFiles = Array.isArray(sp.files) ? sp.files : [];
      if (sp.merkle_root) state.merkleRoot = sp.merkle_root;
      renderArbitrageStats();
      renderAttachDrawer();
    } catch (e) {}
    try {
      const dr = await apiJson('/api/drive/ls?path=/', { channel: 'driveLs' });
      state.driveFiles = Array.isArray(dr.files) ? dr.files : [];
      renderAttachDrawer();
    } catch (e) {}
  }

  async function refresh() {
    await Promise.all([refreshAnalytics(), refreshModels(), refreshSpaceAndDrive()]);
  }

  async function gatherAttachedContextSnippets() {
    resolveSpaceContext();
    const snippets = [];
    for (let i = 0; i < state.attachedFiles.length && i < 4; i++) {
      const f = state.attachedFiles[i];
      try {
        const url = f.source === 'drive'
          ? ('/api/drive/file?path=' + encodeURIComponent(f.path))
          : ('/api/space/file?scope=' + encodeURIComponent(state.scope) + '&owner_id=' + encodeURIComponent(state.ownerId) + '&path=' + encodeURIComponent(f.path));
        const res = await apiJson(url);
        const content = String((res && res.content) || '').slice(0, 1500);
        if (content) snippets.push('[' + f.path + ']\n' + content);
      } catch (e) {}
    }
    return snippets.join('\n\n');
  }

  async function sendMessage() {
    const inp = el('copilotPromptInput');
    const btn = el('copilotSendBtn');
    if (!inp) return;
    const promptText = inp.value.trim();
    if (!promptText) {
      inp.focus();
      return;
    }

    const modelId = (el('copilotModelSelect') && el('copilotModelSelect').value) || state.model;
    const gw = classifyModelGateway(modelId);
    const prio = priorityForGateway(gw);
    const info = PRIORITIES[prio] || PRIORITIES.local;
    const turnId = 'turn-' + Date.now().toString(36);

    if (state.seededOnly) {
      state.turns = [];
      state.seededOnly = false;
    }

    if (btn) btn.disabled = true;
    inp.value = '';
    updatePreflightBadge();

    const t0 = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
    const ctxText = await gatherAttachedContextSnippets();
    const fullPrompt = ctxText ? (promptText + '\n\n--- Attached .space / Drive Context ---\n' + ctxText) : promptText;

    const turnObj = {
      id: turnId,
      prompt: promptText,
      reply: 'Dispatching to ' + modelId + '…',
      model: modelId,
      gateway: gw,
      creditsBilled: 0,
      costUsd: 0.0,
      tokPerSec: 0,
      ttftSec: 0.0,
      routeBadge: info.routeBadge,
      diffText: '',
      patchPath: (state.attachedFiles[0] && state.attachedFiles[0].path) || '/src/main.py'
    };
    state.turns.push(turnObj);
    renderThreadLog();

    try {
      const payload = {
        model: modelId,
        prompt: fullPrompt,
        peer_id: resolvePeerId()
      };
      if (state.threadId) payload.thread_id = state.threadId;

      const res = await apiJson('/api/chat', { channel: 'chat', body: payload });
      const t1 = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
      const elapsedSec = Math.max(0.05, (t1 - t0) / 1000);

      const content =
        (res.choices && res.choices[0] && res.choices[0].message && res.choices[0].message.content) ||
        res.content || res.reply || res.response || res.text || '(empty response)';

      const usage = res.usage || {};
      const compToks = Number(usage.completion_tokens || Math.max(12, Math.ceil(String(content).length / 4)));
      const totalToks = Number(usage.total_tokens || compToks);
      const costUsd = Number(res.cost_usd != null ? res.cost_usd : (usage.cost || 0));
      const isZeroBurn = gw === 'ollama' || gw === 'fau-owlchat';
      const creditsBilled = isZeroBurn ? 0 : Math.max(costUsd > 0 ? 1 : 0, Math.round(costUsd * 1000));

      if (res.thread_id) state.threadId = String(res.thread_id);

      const parsed = extractDiffAndPath(content);
      turnObj.reply = String(content);
      turnObj.creditsBilled = creditsBilled;
      turnObj.costUsd = isZeroBurn ? 0.0 : costUsd;
      turnObj.tokPerSec = Math.round(compToks / elapsedSec);
      turnObj.ttftSec = Number(elapsedSec.toFixed(2));
      turnObj.diffText = parsed.diffText;
      if (parsed.patchPath) turnObj.patchPath = parsed.patchPath;

      if (isZeroBurn) {
        state.arbitrage.localTurns += 1;
        state.arbitrage.usdSaved += 0.02;
      } else {
        state.arbitrage.cloudTurns += 1;
      }
      state.arbitrage.totalTokens += totalToks;

      renderThreadLog();
      renderArbitrageStats();
      refreshAnalytics();
    } catch (err) {
      turnObj.reply = 'Dispatch error (' + (err && err.message ? err.message : 'unknown') + ').';
      turnObj.actionError = true;
      turnObj.actionNote = 'Failed via ' + info.headerRoute;
      renderThreadLog();
    } finally {
      if (btn) btn.disabled = false;
      inp.focus();
    }
  }

  function findTurn(turnId) {
    return state.turns.find((t) => t.id === turnId) || state.turns[state.turns.length - 1] || null;
  }

  async function applyPatch(turnId) {
    const turn = findTurn(turnId);
    if (!turn) return;
    resolveSpaceContext();
    const targetPath = turn.patchPath || (state.attachedFiles[0] && state.attachedFiles[0].path) || '/src/main.py';
    const instruction = turn.diffText
      ? ('Apply patch from TinCan Copilot:\n' + turn.diffText)
      : ('Apply Copilot output:\n' + turn.reply.slice(0, 1200));

    try {
      const proposeRes = await apiJson('/api/space/notes/propose', {
        channel: 'applyPatch',
        body: {
          scope: state.scope,
          owner_id: state.ownerId,
          model: state.model,
          instruction,
          note_body: instruction,
          path: targetPath
        }
      });
      if (proposeRes && proposeRes.plan_id) {
        const commitRes = await apiJson('/api/space/notes/commit', {
          channel: 'commitPatch',
          body: {
            scope: state.scope,
            owner_id: state.ownerId,
            plan_id: proposeRes.plan_id
          }
        });
        if (commitRes && commitRes.merkle_root) state.merkleRoot = commitRes.merkle_root;
        turn.actionError = false;
        turn.actionNote = 'Patch committed to .space (' + (commitRes.version_id || proposeRes.plan_id) + ')';
      } else {
        turn.actionError = false;
        turn.actionNote = 'Patch staged in Space Notes for ' + targetPath;
      }
      renderThreadLog();
      renderArbitrageStats();
      if (typeof window.dispatchEvent === 'function' && typeof window.CustomEvent === 'function') {
        try { window.dispatchEvent(new window.CustomEvent('tincan:space-changed')); } catch (e) {}
      }
      if (typeof window.refreshAgentSpace === 'function') {
        try { window.refreshAgentSpace('background'); } catch (e) {}
      }
    } catch (err) {
      turn.actionError = true;
      turn.actionNote = 'Patch apply failed: ' + (err && err.message ? err.message : 'offline');
      renderThreadLog();
    }
  }

  function duelInArena(turnId) {
    const turn = findTurn(turnId);
    const promptText = (turn && turn.prompt) || ((el('copilotPromptInput') || {}).value || '').trim() || 'Compare routing responses';
    ['arenaWinPromptInput', 'arenaPromptInput'].forEach((id) => {
      const inp = el(id);
      if (inp) inp.value = promptText;
    });
    ['arenaWinModelAInput', 'arenaModelAInput'].forEach((id) => {
      const sel = el(id);
      if (!sel || !state.model) return;
      try {
        if (!sel.options || Array.from(sel.options).some((o) => o.value === state.model)) {
          sel.value = state.model;
        }
      } catch (e) {}
    });
    if (typeof window.toggleWindow === 'function') {
      try {
        const arenaWin = el('win-arena');
        if (arenaWin && (arenaWin.classList.contains('hidden') || arenaWin.style.display === 'none')) {
          window.toggleWindow('win-arena');
        }
      } catch (e) {}
    } else {
      const arenaWin = el('win-arena');
      if (arenaWin) {
        arenaWin.classList.remove('hidden', 'minimized');
        arenaWin.style.display = 'flex';
      }
    }
    if (turn) {
      turn.actionError = false;
      turn.actionNote = 'Loaded prompt into /arena for side-by-side duel.';
      renderThreadLog();
    }
  }

  async function runPytestInSpace(turnId) {
    const turn = findTurn(turnId);
    resolveSpaceContext();
    const testCandidate = state.spaceFiles.find((f) => f && f.path && /test_.*\.py$/i.test(f.path));
    const entrypoint = (testCandidate && testCandidate.path) || '/src/main.py';

    try {
      const res = await apiJson('/api/space/exec', {
        channel: 'spaceExec',
        body: {
          scope: state.scope,
          owner_id: state.ownerId,
          entrypoint,
          runtime: 'python'
        }
      });
      const code = Number(res.exit_code != null ? res.exit_code : 0);
      const out = String(res.stdout || res.stderr || '').trim().split('\n').slice(-2).join(' ');
      if (turn) {
        turn.actionError = code !== 0;
        turn.actionNote = 'pytest/exec ' + entrypoint + ' -> exit ' + code + (out ? (' · ' + out) : '');
        renderThreadLog();
      }
    } catch (err) {
      if (turn) {
        turn.actionError = true;
        turn.actionNote = 'Space exec failed: ' + (err && err.message ? err.message : 'offline');
        renderThreadLog();
      }
    }
  }

  function newThread() {
    state.threadId = '';
    state.turns = [];
    state.seededOnly = false;
    state.threadName = 'tincan-thread-' + Date.now().toString(36).slice(-4);
    const nameEl = el('copilotThreadName');
    if (nameEl) nameEl.textContent = state.threadName;
    renderThreadLog();
    renderArbitrageStats();
    const inp = el('copilotPromptInput');
    if (inp && typeof inp.focus === 'function') inp.focus();
  }

  function exportMarkdown() {
    const lines = ['# TinCan Copilot Thread: ' + state.threadName, ''];
    state.turns.forEach((t, idx) => {
      lines.push('## Turn ' + (idx + 1) + ' (' + t.model + ')');
      lines.push('**Prompt:** ' + t.prompt);
      lines.push('');
      lines.push(t.reply);
      if (t.diffText) {
        lines.push('');
        lines.push('```diff');
        lines.push(t.diffText);
        lines.push('```');
      }
      lines.push('');
    });
    const md = lines.join('\n');
    try {
      if (typeof Blob !== 'undefined' && typeof URL !== 'undefined' && typeof URL.createObjectURL === 'function') {
        const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = (state.threadName || 'tincan-copilot') + '.md';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        notify('Exported ' + a.download, false);
        return md;
      }
    } catch (e) {}
    notify('Markdown export prepared (' + md.length + ' chars)', false);
    return md;
  }

  function wireDomEvents() {
    const inp = el('copilotPromptInput');
    if (inp && !inp.__cpBound) {
      inp.__cpBound = true;
      inp.addEventListener('input', () => updatePreflightBadge());
      inp.addEventListener('keydown', (ev) => {
        if (ev.key === 'Enter' && !ev.shiftKey) {
          ev.preventDefault();
          sendMessage();
        }
      });
    }
    const sel = el('copilotModelSelect');
    if (sel && !sel.__cpBound) {
      sel.__cpBound = true;
      sel.addEventListener('change', () => selectModel(sel.value));
    }
    const winEl = el('win-copilot');
    if (winEl && !winEl.__cpKeyBound) {
      winEl.__cpKeyBound = true;
      winEl.addEventListener('keydown', (ev) => {
        if ((ev.metaKey || ev.ctrlKey) && String(ev.key || '').toLowerCase() === 'n') {
          ev.preventDefault();
          newThread();
        }
      });
    }
    if (winEl && typeof MutationObserver !== 'undefined' && !winEl.__cpObserved) {
      winEl.__cpObserved = true;
      const obs = new MutationObserver(() => {
        if (!winEl.classList.contains('hidden') && winEl.style.display !== 'none') {
          refresh();
        }
      });
      try { obs.observe(winEl, { attributes: true, attributeFilter: ['class', 'style'] }); } catch (e) {}
    }
  }

  function init() {
    if (state.initialized) return;
    state.initialized = true;
    resolveSpaceContext();
    renderPriorityUI();
    renderModelSelect();
    renderContextFiles();
    renderArbitrageStats();
    renderThreadLog();
    wireDomEvents();
  }

  window.TinCanCopilot = {
    version: 1,
    init,
    refresh,
    setPriority,
    selectModel,
    estimatePreflight,
    sendMessage,
    newThread,
    exportMarkdown,
    toggleAttachDrawer,
    attachContextFile,
    removeContextFile,
    applyPatch,
    duelInArena,
    runPytestInSpace,
    getState: () => Object.assign({}, state)
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();"""

    return (
        raw_js.replace("__PRIORITIES_JSON__", priorities_json)
        .replace("__GATEWAYS_JSON__", gateways_json)
        .replace("__MODELS_JSON__", models_json)
    )


COPILOT_SCRIPT = _build_copilot_script()


def render_copilot_window_html(include_css: bool = True, include_js: bool = True) -> str:
    """Render the complete ``#win-copilot`` Aeonik Celadon AI Copilot window markup."""
    priority_pills = _render_priority_pills()
    gateway_cards = _render_initial_gateways()
    model_options = _render_model_options()
    seed_diff = _render_seed_diff_html()
    css_block = f'\n      <style id="tc-copilot-css">{COPILOT_CSS}</style>' if include_css else ""
    js_block = f'\n      <script id="copilotUiScript">\n{COPILOT_SCRIPT}\n      </script>' if include_js else ""

    return f"""<div id="win-copilot" class="mesh-window w-[1080px] max-w-full hidden" data-zen-window="true" data-window-id="win-copilot" style="top: 64px; left: 96px; z-index: 37;">
      <!--TC_TITLEBAR {{"id": "win-copilot", "title": "AI Copilot · Multi-Model Router & Space Diffs", "badge": "COPILOT + ROUTER", "meta_html": "<span id=\\"copilotHeaderRoute\\">direct ollama localhost:11434</span>"}}-->{css_block}
      <div class="window-body cp-body aeonik-scope" data-copilot-root="true">
        <div class="cp-grid">
          <aside class="cp-sidebar" aria-label="Model router priority and gateway quotas">
            <section class="cp-sec">
              <span class="cp-sec-label">MODEL ROUTER PRIORITY</span>
              <div class="cp-seg" role="tablist" aria-label="Model router priority">
                {priority_pills}
              </div>
            </section>

            <section class="cp-card">
              <div class="cp-sec-head">
                <span class="cp-sec-label">ACTIVE GATEWAYS &amp; QUOTAS</span>
                <button id="copilotRefreshGatewaysBtn" type="button" class="cp-btn cp-btn--sm" onclick="window.TinCanCopilot && window.TinCanCopilot.refresh()" title="Refresh gateway balances and models">&#x21BB;&#xFE0E;</button>
              </div>
              <div id="copilotGatewaysList" class="cp-gw-list">
                {gateway_cards}
              </div>
            </section>

            <section class="cp-card">
              <span class="cp-sec-label">SPACE + DRIVE MIRROR CONTEXT</span>
              <div id="copilotContextFiles" class="cp-ctx-list">
                <div class="cp-ctx-item" data-copilot-ctx="/ai_gateway.py">
                  <span class="cp-truncate">[PY] ai_gateway.py</span>
                  <span class="cp-muted">2,140 tok</span>
                </div>
                <div class="cp-ctx-item" data-copilot-ctx="/tincan_agent.py">
                  <span class="cp-truncate">[PY] tincan_agent.py</span>
                  <span class="cp-muted">1,080 tok</span>
                </div>
                <div class="cp-ctx-item" data-copilot-ctx="/Vault/FAU-Thesis.md">
                  <span class="cp-truncate">[MD] Vault/FAU-Thesis.md</span>
                  <span class="cp-pos">RAG ON</span>
                </div>
              </div>
              <div id="copilotAttachDrawer" class="cp-attach-drawer hidden" aria-label="Available Space and Drive files"></div>
              <button id="copilotAttachCtxBtn" type="button" class="cp-btn cp-btn--full" onclick="window.TinCanCopilot && window.TinCanCopilot.toggleAttachDrawer()">+ Attach .space / Drive Files</button>
            </section>

            <section class="cp-card">
              <span class="cp-sec-label">SESSION ARBITRAGE TELEMETRY</span>
              <div id="copilotArbitrageStats" class="cp-arbitrage-lines">
                <div>Local turns: <span id="copilotLocalTurns">0</span> (<span id="copilotBurnedUsd">$0.00</span> burned)</div>
                <div class="cp-pos">OpenRouter saved: <span id="copilotSavedUsd">$0.00</span></div>
                <div class="cp-muted">Thread merkle <span id="copilotThreadMerkle">ready</span></div>
              </div>
            </section>

            <button id="copilotNewThreadBtn" type="button" class="cp-btn cp-btn--solid cp-btn--full" onclick="window.TinCanCopilot && window.TinCanCopilot.newThread()">+ New AI Thread [Cmd+N]</button>
          </aside>

          <main class="cp-main" aria-label="Copilot thread and pre-flight composer">
            <div class="cp-thread-bar">
              <div class="cp-thread-meta">
                <span class="cp-dot"></span>
                <span>THREAD: <strong id="copilotThreadName">tincan-terminal-ai</strong></span>
                <span class="cp-muted">|</span>
                <button id="copilotExportMdBtn" type="button" class="cp-btn cp-btn--sm" onclick="window.TinCanCopilot && window.TinCanCopilot.exportMarkdown()">+ Export .md</button>
                <span class="cp-muted">|</span>
                <span id="copilotThreadIdTag" class="cp-muted">threads/new</span>
              </div>
              <span id="copilotActiveStatus" class="cp-badge cp-badge--pos"><span class="cp-dot cp-dot--pos"></span><span>DIRECT LOCALHOST:11434 · 0ms HOP</span></span>
            </div>

            <div id="copilotThreadLog" class="cp-stream" role="log" aria-live="polite">
              <article class="cp-msg cp-msg--user" data-copilot-turn="seed-1">
                <div class="cp-mono-xs cp-muted">@alejandro · /chat</div>
                <div class="cp-msg-body">Audit our TinCan router and patch direct local Ollama + FAU OwlChat dispatch without burning OpenRouter credits.</div>
              </article>

              <article class="cp-msg cp-msg--assistant" data-copilot-reply="seed-1">
                <div class="cp-msg-head">
                  <div class="cp-msg-lead">
                    <span class="cp-badge cp-badge--ink"><span class="cp-dot cp-dot--paper"></span><span>ollama/qwen2.5:3b</span></span>
                    <span class="cp-mono-xs cp-pos">0 CR BILLED ($0.0000) · 410 tok/s · 0.38s TTFT</span>
                  </div>
                  <span class="cp-badge">LOCAL ZERO-BURN</span>
                </div>
                <div class="cp-msg-body">Direct routing active. Requests with ollama/, owlchat/, trussed/, or --base-url bypass the relay and keep pooled OpenRouter balances untouched.</div>
                <div class="cp-diff-box">{seed_diff}</div>
                <div class="cp-actions-row">
                  <button type="button" class="cp-btn cp-btn--solid" onclick="window.TinCanCopilot && window.TinCanCopilot.applyPatch('seed-1')">Apply Patch to .space &#x2192;</button>
                  <button type="button" class="cp-btn" onclick="window.TinCanCopilot && window.TinCanCopilot.duelInArena('seed-1')">Duel in /arena</button>
                  <button type="button" class="cp-btn" onclick="window.TinCanCopilot && window.TinCanCopilot.runPytestInSpace('seed-1')">&#x25B6; Run pytest in .space</button>
                </div>
              </article>
            </div>

            <div class="cp-composer">
              <textarea id="copilotPromptInput" rows="2" class="cp-textarea" placeholder="Ask TinCan Copilot, attach .space files, or request a unified diff..."></textarea>
              <div class="cp-composer-bar">
                <select id="copilotModelSelect" class="cp-select" aria-label="Select Copilot model">
                  {model_options}
                </select>
                <span id="copilotPreflightCost" class="cp-badge cp-badge--pos">Est: 0 CR Free | Cloud Eq: 3 CR</span>
                <button id="copilotSendBtn" type="button" class="cp-btn cp-btn--solid" onclick="window.TinCanCopilot && window.TinCanCopilot.sendMessage()">Send Message [Enter]</button>
              </div>
            </div>
          </main>
        </div>
      </div>{js_block}
    </div>"""


def apply_copilot_ui(html: str) -> str:
    """Replace copilot window, CSS, and JS markers inside ``html`` idempotently."""
    if not html:
        return html
    has_win_slot = COPILOT_WINDOW_SLOT in html
    has_css_slot = COPILOT_CSS_SLOT in html
    has_js_slot = COPILOT_JS_SLOT in html

    if not (has_win_slot or has_css_slot or has_js_slot):
        return html

    out = html
    if has_win_slot:
        win_markup = (
            ""
            if 'id="win-copilot"' in out
            else render_copilot_window_html(include_css=not has_css_slot, include_js=not has_js_slot)
        )
        out = out.replace(COPILOT_WINDOW_SLOT, win_markup, 1).replace(COPILOT_WINDOW_SLOT, "")

    if has_css_slot:
        css_payload = "" if ('id="tc-copilot-css"' in out or "/*TC_COPILOT_CSS_MOUNTED*/" in out) else f"/*TC_COPILOT_CSS_MOUNTED*/\n{COPILOT_CSS}"
        out = out.replace(COPILOT_CSS_SLOT, css_payload, 1).replace(COPILOT_CSS_SLOT, "")

    if has_js_slot:
        js_payload = "" if ('id="copilotUiScript"' in out or "/*TC_COPILOT_JS_MOUNTED*/" in out) else f"/*TC_COPILOT_JS_MOUNTED*/\n{COPILOT_SCRIPT}"
        out = out.replace(COPILOT_JS_SLOT, js_payload, 1).replace(COPILOT_JS_SLOT, "")

    return out


__all__ = [
    "COPILOT_CSS",
    "COPILOT_CSS_SLOT",
    "COPILOT_JS_SLOT",
    "COPILOT_SCRIPT",
    "COPILOT_WINDOW_ID",
    "COPILOT_WINDOW_SLOT",
    "DEFAULT_COPILOT_MODELS",
    "DEFAULT_GATEWAY_CARDS",
    "PRIORITY_DEFS",
    "apply_copilot_ui",
    "render_copilot_window_html",
]
