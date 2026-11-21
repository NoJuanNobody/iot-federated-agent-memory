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
  height: calc(100% - 42px);
  max-height: calc(100vh - 48px);
  min-height: 0;
  overflow: hidden;
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
  padding-top: 7px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
#win-copilot .cp-inv-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
}
#win-copilot .cp-inv-search {
  flex: 1 1 auto;
  min-width: 0;
  border: var(--cp-hair-soft);
  border-radius: 9999px;
  background: var(--cp-paper);
  color: var(--cp-ink);
  font-family: var(--cp-mono);
  font-size: 10px;
  padding: 3px 8px;
  outline: none;
}
#win-copilot .cp-inv-search:focus { border-color: var(--cp-ink); }
#win-copilot .cp-inv-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
#win-copilot .cp-inv-tab {
  padding: 2px 7px;
  border: var(--cp-hair-soft);
  border-radius: 9999px;
  background: var(--cp-paper);
  color: var(--cp-ink);
  font-family: var(--cp-mono);
  font-size: 10px;
  font-weight: 600;
  cursor: pointer;
}
#win-copilot .cp-inv-tab.is-active {
  background: var(--cp-ink);
  color: var(--cp-paper);
  border-color: var(--cp-ink);
}
#win-copilot .cp-inv-list {
  max-height: 168px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
#win-copilot .cp-inv-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 5px 7px;
  border: var(--cp-hair-soft);
  border-radius: 8px;
  background: var(--cp-paper);
  font-family: var(--cp-mono);
  font-size: 10px;
}
#win-copilot .cp-inv-row.is-attached {
  border-color: var(--cp-pos);
  background: var(--cp-pos-bg);
}
#win-copilot .cp-inv-row-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
  min-width: 0;
}
#win-copilot .cp-inv-row-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
}
#win-copilot .cp-inv-pill {
  padding: 1px 6px;
  border: var(--cp-hair-soft);
  border-radius: 9999px;
  background: var(--cp-card);
  color: var(--cp-ink);
  font-family: var(--cp-mono);
  font-size: 9px;
  font-weight: 600;
  cursor: pointer;
}
#win-copilot .cp-inv-pill:hover {
  background: var(--cp-ink);
  color: var(--cp-paper);
}
#win-copilot .cp-inv-pill--pos {
  border-color: var(--cp-pos);
  background: var(--cp-pos-bg);
  color: var(--cp-pos);
}
#win-copilot .cp-inspector {
  background: var(--cp-paper);
  border: var(--cp-hair);
  border-radius: 12px;
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
#win-copilot .cp-insp-field {
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
  border: var(--cp-hair-soft);
  border-radius: 6px;
  background: var(--cp-card);
  color: var(--cp-ink);
  font-family: var(--cp-mono);
  font-size: 10px;
  padding: 4px 6px;
  outline: none;
}
#win-copilot .cp-insp-field:focus {
  border-color: var(--cp-ink);
  background: var(--cp-paper);
}
#win-copilot .cp-insp-meta {
  background: var(--cp-card);
  border: var(--cp-hair-soft);
  border-radius: 6px;
  padding: 4px 6px;
  font-family: var(--cp-mono);
  font-size: 9px;
  line-height: 1.4;
  color: var(--cp-muted);
  word-break: break-word;
}
#win-copilot .cp-insp-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
}
#win-copilot .cp-btn--pos {
  border-color: var(--cp-pos);
  background: var(--cp-pos);
  color: var(--cp-paper);
}
#win-copilot .cp-btn--pos:hover { opacity: 0.88; }
#win-copilot .cp-btn--danger {
  border-color: var(--cp-danger);
  background: var(--cp-paper);
  color: var(--cp-danger);
}
#win-copilot .cp-btn--danger:hover {
  background: var(--cp-danger);
  color: var(--cp-paper);
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
  flex: 1 1 0%;
  min-height: 160px;
  max-height: 100%;
  overflow-y: auto !important;
  overflow-x: hidden;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
  scrollbar-gutter: stable;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-right: 4px;
}
#win-copilot .cp-msg {
  flex: 0 0 auto;
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
  overflow-wrap: anywhere;
  max-height: 55vh;
  overflow-y: auto;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
  padding-right: 2px;
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
#win-copilot .cp-capsules {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 5px;
  padding-bottom: 6px;
  border-bottom: var(--cp-hair-soft);
}
#win-copilot .cp-capsule-summary {
  font-family: var(--cp-mono);
  font-size: 10px;
  font-weight: 700;
  color: var(--cp-faint);
  letter-spacing: 0.03em;
}
#win-copilot .cp-capsule-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 7px;
  border-radius: 9999px;
  border: 1px solid var(--cp-pos);
  background: var(--cp-pos-bg);
  color: var(--cp-pos);
  font-family: var(--cp-mono);
  font-size: 10px;
  font-weight: 600;
  max-width: 100%;
}
#win-copilot .cp-capsule-chip--file {
  border: var(--cp-hair-soft);
  background: var(--cp-card);
  color: var(--cp-ink);
}
#win-copilot .cp-capsule-btn {
  border: 0;
  background: transparent;
  color: inherit;
  font-family: inherit;
  font-size: inherit;
  font-weight: inherit;
  padding: 0;
  cursor: pointer;
}
#win-copilot .cp-capsule-rm {
  border: 0;
  background: transparent;
  color: inherit;
  font-family: var(--cp-mono);
  font-size: 10px;
  font-weight: 700;
  padding: 0 2px;
  cursor: pointer;
  line-height: 1;
}
#win-copilot .cp-capsule-rm:hover { color: var(--cp-danger); }
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
  #win-copilot .cp-stream { max-height: 52vh; overflow-y: auto !important; }
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
  #win-copilot .cp-stream { max-height: 52vh; overflow-y: auto !important; }
}

/* Monochrome Black & White Dark Mode (html[data-theme="dark"] / body.tc-dark) */
html[data-theme="dark"] #copilotRoot, body.tc-dark #copilotRoot, html[data-theme="dark"] #win-copilot, body.tc-dark #win-copilot {
  --cp-bg: #0e0e0e;
  --cp-card: #151515;
  --cp-paper: #1a1a1a;
  --cp-ink: #f5f5f5;
  --cp-muted: #a3a3a3;
  --cp-faint: #737373;
  --cp-pos: #ffffff;
  --cp-pos-bg: #181818;
  --cp-danger: #d4d4d4;
  --cp-danger-bg: #1f1f1f;
  --cp-hair: 1px solid #2e2e2e;
  --cp-hair-soft: 1px solid #2e2e2e;
  background: #0e0e0e;
  color: #f5f5f5;
}
html[data-theme="dark"] #copilotRoot.cp-body, body.tc-dark #copilotRoot.cp-body, html[data-theme="dark"] #win-copilot .cp-body, body.tc-dark #win-copilot .cp-body, html[data-theme="dark"] #copilotRoot .cp-main, body.tc-dark #copilotRoot .cp-main, html[data-theme="dark"] #win-copilot .cp-main, body.tc-dark #win-copilot .cp-main {
  background: #0e0e0e;
  color: #f5f5f5;
}
html[data-theme="dark"] #copilotRoot .cp-sidebar, body.tc-dark #copilotRoot .cp-sidebar, html[data-theme="dark"] #win-copilot .cp-sidebar, body.tc-dark #win-copilot .cp-sidebar, html[data-theme="dark"] #copilotRoot .cp-inspector, body.tc-dark #copilotRoot .cp-inspector, html[data-theme="dark"] #win-copilot .cp-inspector, body.tc-dark #win-copilot .cp-inspector {
  background: #131313;
  border-color: #2e2e2e;
  color: #f5f5f5;
}
html[data-theme="dark"] #copilotRoot .cp-card, body.tc-dark #copilotRoot .cp-card, html[data-theme="dark"] #win-copilot .cp-card, body.tc-dark #win-copilot .cp-card, html[data-theme="dark"] #copilotRoot .cp-thread-bar, body.tc-dark #copilotRoot .cp-thread-bar, html[data-theme="dark"] #win-copilot .cp-thread-bar, body.tc-dark #win-copilot .cp-thread-bar, html[data-theme="dark"] #copilotRoot .cp-msg, body.tc-dark #copilotRoot .cp-msg, html[data-theme="dark"] #win-copilot .cp-msg, body.tc-dark #win-copilot .cp-msg, html[data-theme="dark"] #win-copilot .cp-msg--user, body.tc-dark #win-copilot .cp-msg--user, html[data-theme="dark"] #win-copilot .cp-msg--assistant, body.tc-dark #win-copilot .cp-msg--assistant {
  background: #151515;
  border-color: #2e2e2e;
  color: #f5f5f5;
}
html[data-theme="dark"] #copilotRoot .cp-msg-body, body.tc-dark #copilotRoot .cp-msg-body, html[data-theme="dark"] #win-copilot .cp-msg-body, body.tc-dark #win-copilot .cp-msg-body {
  color: #f5f5f5;
}
html[data-theme="dark"] #copilotRoot .cp-muted, body.tc-dark #copilotRoot .cp-muted, html[data-theme="dark"] #win-copilot .cp-muted, body.tc-dark #win-copilot .cp-muted, html[data-theme="dark"] #copilotRoot .cp-sec-label, body.tc-dark #copilotRoot .cp-sec-label, html[data-theme="dark"] #win-copilot .cp-sec-label, body.tc-dark #win-copilot .cp-sec-label {
  color: #a3a3a3;
}
html[data-theme="dark"] #copilotRoot .cp-pos, body.tc-dark #copilotRoot .cp-pos, html[data-theme="dark"] #win-copilot .cp-pos, body.tc-dark #win-copilot .cp-pos {
  color: #ffffff;
}
html[data-theme="dark"] #copilotRoot .cp-seg, body.tc-dark #copilotRoot .cp-seg, html[data-theme="dark"] #win-copilot .cp-seg, body.tc-dark #win-copilot .cp-seg {
  background: #151515;
  border-color: #2e2e2e;
}
html[data-theme="dark"] #copilotRoot .cp-seg-btn, body.tc-dark #copilotRoot .cp-seg-btn, html[data-theme="dark"] #win-copilot .cp-seg-btn, body.tc-dark #win-copilot .cp-seg-btn {
  color: #a3a3a3;
  border-color: #2e2e2e;
}
html[data-theme="dark"] #copilotRoot .cp-seg-btn:hover, body.tc-dark #copilotRoot .cp-seg-btn:hover, html[data-theme="dark"] #win-copilot .cp-seg-btn:hover, body.tc-dark #win-copilot .cp-seg-btn:hover {
  background: #222222;
  color: #ffffff;
}
html[data-theme="dark"] #copilotRoot .cp-seg-btn.is-active, body.tc-dark #copilotRoot .cp-seg-btn.is-active, html[data-theme="dark"] #win-copilot .cp-seg-btn.is-active, body.tc-dark #win-copilot .cp-seg-btn.is-active, html[data-theme="dark"] #copilotRoot .cp-inv-tab.is-active, body.tc-dark #copilotRoot .cp-inv-tab.is-active, html[data-theme="dark"] #win-copilot .cp-inv-tab.is-active, body.tc-dark #win-copilot .cp-inv-tab.is-active, html[data-theme="dark"] #copilotRoot .cp-btn--solid, body.tc-dark #copilotRoot .cp-btn--solid, html[data-theme="dark"] #win-copilot .cp-btn--solid, body.tc-dark #win-copilot .cp-btn--solid, html[data-theme="dark"] #copilotRoot .cp-btn--pos, body.tc-dark #copilotRoot .cp-btn--pos, html[data-theme="dark"] #win-copilot .cp-btn--pos, body.tc-dark #win-copilot .cp-btn--pos, html[data-theme="dark"] #copilotRoot #copilotSendBtn, body.tc-dark #copilotRoot #copilotSendBtn, html[data-theme="dark"] #win-copilot #copilotSendBtn, body.tc-dark #win-copilot #copilotSendBtn {
  background: #ffffff !important;
  color: #000000 !important;
  border-color: #ffffff !important;
}
html[data-theme="dark"] #copilotRoot .cp-gw-row, body.tc-dark #copilotRoot .cp-gw-row, html[data-theme="dark"] #win-copilot .cp-gw-row, body.tc-dark #win-copilot .cp-gw-row {
  color: #f5f5f5;
}
html[data-theme="dark"] #copilotRoot .cp-gw-row:hover, body.tc-dark #copilotRoot .cp-gw-row:hover, html[data-theme="dark"] #win-copilot .cp-gw-row:hover, body.tc-dark #win-copilot .cp-gw-row:hover, html[data-theme="dark"] #copilotRoot .cp-gw-row.is-active, body.tc-dark #copilotRoot .cp-gw-row.is-active, html[data-theme="dark"] #win-copilot .cp-gw-row.is-active, body.tc-dark #win-copilot .cp-gw-row.is-active {
  background: #1a1a1a;
  color: #f5f5f5;
}
html[data-theme="dark"] #copilotRoot .cp-meter-track, body.tc-dark #copilotRoot .cp-meter-track, html[data-theme="dark"] #win-copilot .cp-meter-track, body.tc-dark #win-copilot .cp-meter-track {
  background: #2e2e2e;
}
html[data-theme="dark"] #copilotRoot .cp-meter-fill, body.tc-dark #copilotRoot .cp-meter-fill, html[data-theme="dark"] #win-copilot .cp-meter-fill, body.tc-dark #win-copilot .cp-meter-fill, html[data-theme="dark"] #win-copilot .cp-meter-fill--pos, body.tc-dark #win-copilot .cp-meter-fill--pos {
  background: #ffffff;
}
html[data-theme="dark"] #copilotRoot .cp-ctx-item, body.tc-dark #copilotRoot .cp-ctx-item, html[data-theme="dark"] #win-copilot .cp-ctx-item, body.tc-dark #win-copilot .cp-ctx-item, html[data-theme="dark"] #copilotRoot .cp-inv-row, body.tc-dark #copilotRoot .cp-inv-row, html[data-theme="dark"] #win-copilot .cp-inv-row, body.tc-dark #win-copilot .cp-inv-row, html[data-theme="dark"] #copilotRoot .cp-insp-field, body.tc-dark #copilotRoot .cp-insp-field, html[data-theme="dark"] #win-copilot .cp-insp-field, body.tc-dark #win-copilot .cp-insp-field, html[data-theme="dark"] #copilotRoot .cp-insp-meta, body.tc-dark #copilotRoot .cp-insp-meta, html[data-theme="dark"] #win-copilot .cp-insp-meta, body.tc-dark #win-copilot .cp-insp-meta, html[data-theme="dark"] #copilotRoot .cp-select, body.tc-dark #copilotRoot .cp-select, html[data-theme="dark"] #win-copilot .cp-select, body.tc-dark #win-copilot .cp-select {
  background: #151515;
  border-color: #2e2e2e;
  color: #f5f5f5;
}
html[data-theme="dark"] #copilotRoot .cp-btn, body.tc-dark #copilotRoot .cp-btn, html[data-theme="dark"] #win-copilot .cp-btn, body.tc-dark #win-copilot .cp-btn, html[data-theme="dark"] #copilotRoot .cp-badge, body.tc-dark #copilotRoot .cp-badge, html[data-theme="dark"] #win-copilot .cp-badge, body.tc-dark #win-copilot .cp-badge {
  background: #1a1a1a;
  border-color: #2e2e2e;
  color: #f5f5f5;
}
html[data-theme="dark"] #copilotRoot .cp-badge--ink, body.tc-dark #copilotRoot .cp-badge--ink, html[data-theme="dark"] #win-copilot .cp-badge--ink, body.tc-dark #win-copilot .cp-badge--ink {
  background: #ffffff;
  border-color: #ffffff;
  color: #000000;
}
html[data-theme="dark"] #copilotRoot .cp-dot, body.tc-dark #copilotRoot .cp-dot, html[data-theme="dark"] #win-copilot .cp-dot, body.tc-dark #win-copilot .cp-dot, html[data-theme="dark"] #win-copilot .cp-dot--pos, body.tc-dark #win-copilot .cp-dot--pos {
  background: #ffffff;
}
html[data-theme="dark"] #copilotRoot .cp-dot--paper, body.tc-dark #copilotRoot .cp-dot--paper, html[data-theme="dark"] #win-copilot .cp-dot--paper, body.tc-dark #win-copilot .cp-dot--paper {
  background: #000000;
}
html[data-theme="dark"] #copilotRoot .cp-diff-box, body.tc-dark #copilotRoot .cp-diff-box, html[data-theme="dark"] #win-copilot .cp-diff-box, body.tc-dark #win-copilot .cp-diff-box, html[data-theme="dark"] #copilotRoot .cp-composer, body.tc-dark #copilotRoot .cp-composer, html[data-theme="dark"] #win-copilot .cp-composer, body.tc-dark #win-copilot .cp-composer, html[data-theme="dark"] #copilotRoot pre, body.tc-dark #copilotRoot pre, html[data-theme="dark"] #win-copilot pre, body.tc-dark #win-copilot pre, html[data-theme="dark"] #copilotRoot code, body.tc-dark #copilotRoot code, html[data-theme="dark"] #win-copilot code, body.tc-dark #win-copilot code {
  background: #000000 !important;
  color: #f5f5f5 !important;
  border: 1.5px solid #ffffff !important;
}
html[data-theme="dark"] #copilotRoot .cp-textarea, body.tc-dark #copilotRoot .cp-textarea, html[data-theme="dark"] #win-copilot .cp-textarea, body.tc-dark #win-copilot .cp-textarea {
  background: #000000 !important;
  color: #f5f5f5 !important;
  caret-color: #ffffff !important;
}
html[data-theme="dark"] #copilotRoot .cp-diff-add, body.tc-dark #copilotRoot .cp-diff-add, html[data-theme="dark"] #win-copilot .cp-diff-add, body.tc-dark #win-copilot .cp-diff-add {
  background: #141414;
  color: #ffffff;
}
html[data-theme="dark"] #copilotRoot .cp-diff-del, body.tc-dark #copilotRoot .cp-diff-del, html[data-theme="dark"] #win-copilot .cp-diff-del, body.tc-dark #win-copilot .cp-diff-del {
  background: #1a1a1a;
  color: #a3a3a3;
}
html[data-theme="dark"] #copilotRoot .cp-diff-file, body.tc-dark #copilotRoot .cp-diff-file, html[data-theme="dark"] #win-copilot .cp-diff-file, body.tc-dark #win-copilot .cp-diff-file, html[data-theme="dark"] #win-copilot .cp-diff-hunk, body.tc-dark #win-copilot .cp-diff-hunk {
  color: #a3a3a3;
}
html[data-theme="dark"] #copilotRoot .cp-capsules, body.tc-dark #copilotRoot .cp-capsules, html[data-theme="dark"] #win-copilot .cp-capsules, body.tc-dark #win-copilot .cp-capsules, html[data-theme="dark"] #copilotRoot .cp-composer-bar, body.tc-dark #copilotRoot .cp-composer-bar, html[data-theme="dark"] #win-copilot .cp-composer-bar, body.tc-dark #win-copilot .cp-composer-bar {
  border-color: #2e2e2e;
}
"""

_COPILOT_CSS = COPILOT_CSS


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
    palaceNodes: [],
    inventoryItems: [],
    inventoryFetched: false,
    inventoryTab: 'all',
    inventoryQuery: '',
    renderedInventory: [],
    inspector: {
      open: false,
      mode: 'create',
      nodeId: '',
      canonical_name: '',
      category: 'router_memory',
      summary: '',
      value: '',
      valid_from: '',
      edges: [],
      updated_at: 0,
      tokens_est: 0,
      original: null,
      statusNote: '',
      statusError: false
    },
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

  function _getUrlParams() {
    try {
      if (typeof window !== 'undefined' && window.location && window.location.search) {
        return new URLSearchParams(window.location.search);
      }
    } catch (e) {}
    return null;
  }

  function _notifyCopilotInstanceTitle() {
    const q = _getUrlParams();
    const sw = q ? (q.get('window') || '') : '';
    if (sw && sw !== 'win-copilot' && sw !== 'copilot') return;
    if (typeof window.notifyParentInstanceTitle === 'function') {
      try {
        window.notifyParentInstanceTitle((state.threadName || 'thread') + ' · ' + (state.model || ''));
      } catch (e) {}
    }
  }

  function resolveSpaceContext() {
    const q = _getUrlParams();
    const qScope = q ? q.get('scope') : '';
    const qOwner = q ? q.get('owner') : '';
    const scopeEl = el('spaceScopeSelect');
    const ownerEl = el('spaceOwnerInput');
    if (qScope) state.scope = qScope;
    else if (scopeEl && scopeEl.value) state.scope = scopeEl.value;
    else if (typeof window.currentSpaceScope === 'string' && window.currentSpaceScope) state.scope = window.currentSpaceScope;
    if (qOwner) state.ownerId = qOwner;
    else if (ownerEl && ownerEl.value) state.ownerId = ownerEl.value;
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
    if (state.model && !state.models.some((m) => m && m.id === state.model)) {
      seen.add(state.model);
      opts.push('<option value="' + esc(state.model) + '">' + esc(state.model) + '</option>');
    }
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

  function renderActiveCapsules() {
    const bar = el('copilotActiveCapsules');
    if (!bar) return;
    let totalTok = 0;
    state.attachedFiles.forEach((f) => { totalTok += Number((f && f.estTokens) || 0); });
    const summaryHtml = '<span class="cp-capsule-summary">Active Capsules (' + totalTok.toLocaleString() + 't):</span>';
    if (!state.attachedFiles.length) {
      bar.innerHTML = summaryHtml + '<span class="cp-mono-xs cp-muted">none attached</span>';
      return;
    }
    const chipsHtml = state.attachedFiles.map((f, idx) => {
      const isPalace = f.source === 'palace';
      const prefix = isPalace ? 'Palace' : (f.source === 'drive' ? 'Drive' : '.space');
      const shortName = isPalace
        ? String(f.path || '').replace(/^\/palace\//, '')
        : String(f.path || '').replace(/^\/+/, '');
      const tok = Number(f.estTokens || 0);
      const chipCls = isPalace ? 'cp-capsule-chip' : 'cp-capsule-chip cp-capsule-chip--file';
      const labelHtml = isPalace
        ? '<button type="button" class="cp-capsule-btn" title="Inspect in Context Inspector" onclick="window.TinCanCopilot && window.TinCanCopilot.openPalaceInspector(\'' + esc(f.nodeId || shortName).replace(/'/g, '\\\'') + '\')">' + esc(prefix + ': ' + shortName + ' (' + tok + 't)') + '</button>'
        : '<span>' + esc(prefix + ': ' + shortName + ' (' + tok + 't)') + '</span>';
      return (
        '<span class="' + chipCls + '" data-copilot-capsule="' + esc(f.path) + '">' +
        labelHtml +
        '<button type="button" class="cp-capsule-rm" aria-label="Detach ' + esc(shortName) + '" title="Detach capsule" ' +
        'onclick="window.TinCanCopilot && window.TinCanCopilot.removeContextFile(' + idx + ')">&#x00D7;</button>' +
        '</span>'
      );
    }).join('');
    bar.innerHTML = summaryHtml + chipsHtml;
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
    renderActiveCapsules();
    renderAttachDrawer();
  }

  function getNormalizedInventoryItems() {
    const palaceById = new Map();
    const palaceByName = new Map();
    state.palaceNodes.forEach((n) => {
      if (!n) return;
      if (n.node_id) palaceById.set(n.node_id, n);
      if (n.canonical_name) palaceByName.set(n.canonical_name, n);
    });

    const out = [];
    const seen = new Set();

    function pushItem(it) {
      if (!it || !it.path) return;
      const src = it.source || 'space';
      const key = src + ':' + (it.nodeId || it.path);
      if (seen.has(key)) return;
      seen.add(key);
      out.push(it);
    }

    if (state.inventoryFetched && Array.isArray(state.inventoryItems)) {
      state.inventoryItems.forEach((it) => {
        if (!it) return;
        const sg = String(it.source_group || it.source || it.kind || '').toLowerCase();
        const isPalace = sg === 'palace' || it.kind === 'palace';
        const src = isPalace ? 'palace' : (sg === 'drive' ? 'drive' : (sg === 'space' ? 'space' : (it.source || 'space')));
        const pNode = isPalace ? (palaceById.get(it.node_id || it.id) || palaceByName.get(it.title || '')) : null;
        const val = (pNode && (pNode.value || pNode.active_value)) || it.value || '';
        const estTokens = Number(
          it.tokens_est || (pNode && pNode.tokens_est) || Math.max(12, Math.ceil(String(val || it.size_bytes || '').length / 4 || Number(it.size_bytes || 0) / 4))
        );
        pushItem({
          path: it.path || (isPalace ? ('/palace/' + (it.title || it.node_id || 'concept')) : ''),
          title: it.title || it.canonical_name || it.path,
          category: it.category || (pNode && pNode.category) || '',
          desc: it.description || (pNode && pNode.summary) || '',
          value: val,
          source: src,
          sourceGroup: isPalace ? 'palace' : (sg === 'drive' ? 'drive' : (sg === 'space' ? 'space' : 'brains')),
          kind: it.kind || src,
          nodeId: it.node_id || (isPalace ? it.id : '') || '',
          tokensEst: estTokens,
          size: Number(it.size_bytes || String(val).length || 0),
          validFrom: (pNode && pNode.valid_from) || it.valid_from || '',
          edges: (pNode && pNode.edges) || it.edges || [],
          updatedAt: (pNode && pNode.updated_at) || it.updated_at || 0
        });
      });
    }

    state.palaceNodes.forEach((n) => {
      if (!n || !n.canonical_name) return;
      const val = String(n.value || n.active_value || '');
      pushItem({
        path: '/palace/' + n.canonical_name,
        title: n.canonical_name,
        category: n.category || '',
        desc: n.summary || '',
        value: val,
        source: 'palace',
        sourceGroup: 'palace',
        kind: 'palace',
        nodeId: n.node_id || '',
        tokensEst: Number(n.tokens_est || Math.max(12, Math.ceil(val.length / 4))),
        size: val.length,
        validFrom: n.valid_from || '',
        edges: n.edges || [],
        updatedAt: n.updated_at || 0
      });
    });
    state.spaceFiles.forEach((f) => {
      if (!f || !f.path) return;
      const sz = Number(f.size_bytes || 0);
      pushItem({
        path: f.path,
        title: f.path,
        category: '',
        desc: f.description || '',
        value: '',
        source: 'space',
        sourceGroup: 'space',
        kind: 'space',
        nodeId: '',
        tokensEst: Math.max(12, Math.ceil(sz / 4)),
        size: sz
      });
    });
    state.driveFiles.forEach((f) => {
      const p = typeof f === 'string' ? f : (f && (f.path || f.name));
      if (!p) return;
      const sz = Number((f && f.size_bytes) || 0);
      pushItem({
        path: p,
        title: p,
        category: '',
        desc: (f && f.description) || 'Local Drive Mirror',
        value: '',
        source: 'drive',
        sourceGroup: 'drive',
        kind: 'drive',
        nodeId: '',
        tokensEst: Math.max(12, Math.ceil(sz / 4)),
        size: sz
      });
    });

    return out;
  }

  function renderAttachDrawer() {
    const drawer = el('copilotAttachDrawer');
    if (!drawer) return;
    drawer.classList.toggle('hidden', !state.attachDrawerOpen);
    if (!state.attachDrawerOpen) return;

    const searchInp = el('copilotInventorySearch');
    if (searchInp && searchInp.value !== state.inventoryQuery) {
      searchInp.value = state.inventoryQuery;
    }

    const allItems = getNormalizedInventoryItems();
    const counts = {
      all: allItems.length,
      palace: allItems.filter((i) => i.source === 'palace').length,
      space: allItems.filter((i) => i.source === 'space').length,
      drive: allItems.filter((i) => i.source === 'drive').length
    };
    const tabLabels = {
      all: 'All (' + counts.all + ')',
      palace: 'Palace (' + counts.palace + ')',
      space: '.space (' + counts.space + ')',
      drive: 'Drive (' + counts.drive + ')'
    };
    ['all', 'palace', 'space', 'drive'].forEach((tabKey) => {
      const tbtn = el('copilotInvTab-' + tabKey);
      if (tbtn) {
        const active = state.inventoryTab === tabKey;
        tbtn.classList.toggle('is-active', active);
        tbtn.setAttribute('aria-selected', active ? 'true' : 'false');
        tbtn.textContent = tabLabels[tabKey];
      }
    });

    const q = String(state.inventoryQuery || '').trim().toLowerCase();
    const qTerms = q ? q.split(/\s+/).filter(Boolean) : [];
    const filtered = allItems.filter((it) => {
      if (state.inventoryTab !== 'all' && it.source !== state.inventoryTab) return false;
      if (!qTerms.length) return true;
      const hay = [it.title, it.path, it.category, it.desc, it.value].join(' ').toLowerCase();
      return qTerms.every((t) => hay.indexOf(t) !== -1);
    });
    state.renderedInventory = filtered.slice(0, 36);

    const sumEl = el('copilotInventorySummary');
    if (sumEl) {
      sumEl.textContent = filtered.length + ' shown · ' + allItems.length + ' total';
    }

    const listEl = el('copilotInventoryList');
    if (!listEl) return;

    if (!state.renderedInventory.length) {
      listEl.innerHTML = '<div class="cp-mono-xs cp-muted">No matching Palace, .space, or Drive items found.</div>';
      return;
    }

    const attachedSet = new Set(state.attachedFiles.map((a) => a.path));
    listEl.innerHTML = state.renderedInventory.map((c, idx) => {
      const isAtt = attachedSet.has(c.path);
      const kindTag = c.source === 'palace' ? 'PALACE' : (c.source === 'drive' ? 'DRIVE' : '.SPACE');
      const catBadge = c.category ? (' · ' + c.category) : '';
      const tokBadge = Number(c.tokensEst || 0) + 't';
      const editBtn = c.source === 'palace'
        ? '<button type="button" class="cp-inv-pill" data-palace-edit-idx="' + idx + '" onclick="window.TinCanCopilot && window.TinCanCopilot._invEdit(' + idx + ')">Edit &#x270E;</button>'
        : '';
      const arenaBtn = c.source === 'palace'
        ? '<button type="button" class="cp-inv-pill" onclick="window.TinCanCopilot && window.TinCanCopilot._invToArena(' + idx + ')">&#x2192; Both</button>'
        : '';
      return (
        '<div class="cp-inv-row' + (isAtt ? ' is-attached' : '') + '" data-inv-source="' + esc(c.source) + '" data-inv-path="' + esc(c.path) + '">' +
          '<div class="cp-inv-row-top">' +
            '<span class="cp-truncate">[' + esc(kindTag) + '] ' + esc(c.title || c.path) + esc(catBadge) + '</span>' +
            '<span class="cp-muted" style="flex:0 0 auto;">' + esc(tokBadge) + '</span>' +
          '</div>' +
          (c.desc ? '<div class="cp-truncate cp-muted" style="font-size:9px;">' + esc(c.desc) + '</div>' : '') +
          '<div class="cp-inv-row-actions">' +
            '<button type="button" class="cp-inv-pill' + (isAtt ? ' cp-inv-pill--pos' : '') + '" onclick="window.TinCanCopilot && window.TinCanCopilot._invAttach(' + idx + ')">' + (isAtt ? 'Attached &#x2713;' : '+ Router') + '</button>' +
            editBtn +
            arenaBtn +
          '</div>' +
        '</div>'
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

  function toggleAttachDrawer(tabOverride) {
    if (typeof tabOverride === 'string' && tabOverride) {
      if (state.attachDrawerOpen && state.inventoryTab === tabOverride) {
        state.attachDrawerOpen = false;
      } else {
        state.inventoryTab = tabOverride;
        state.attachDrawerOpen = true;
      }
    } else {
      state.attachDrawerOpen = !state.attachDrawerOpen;
    }
    renderAttachDrawer();
    if (state.attachDrawerOpen) {
      refreshSpaceAndDrive();
    }
  }

  function setInventoryTab(tabKey) {
    const allowed = { all: true, palace: true, space: true, drive: true };
    if (!allowed[tabKey]) return;
    state.inventoryTab = tabKey;
    state.attachDrawerOpen = true;
    renderAttachDrawer();
  }

  function setInventoryQuery(q) {
    state.inventoryQuery = String(q == null ? '' : q);
    state.attachDrawerOpen = true;
    renderAttachDrawer();
    if (typeof fetch === 'function') {
      refreshInventory(state.inventoryQuery);
    }
  }

  function _findInventoryItemMeta(path, source) {
    const cleanName = String(path || '').replace(/^\/palace\//, '');
    if (source === 'palace') {
      const pNode = state.palaceNodes.find((n) => n && (n.canonical_name === cleanName || ('/palace/' + n.canonical_name) === path));
      if (pNode) return pNode;
    }
    return state.inventoryItems.find((it) => it && (it.path === path || it.title === cleanName)) || null;
  }

  function attachContextFile(path, source, itemMeta) {
    if (!path) return;
    const existingIdx = state.attachedFiles.findIndex((f) => f.path === path);
    if (existingIdx !== -1) {
      state.attachedFiles.splice(existingIdx, 1);
      renderContextFiles();
      return;
    }
    if (source === 'palace') {
      const hit = itemMeta || _findInventoryItemMeta(path, 'palace');
      const val = hit ? String(hit.value || hit.active_value || hit.summary || hit.description || '') : '';
      const est = Number((hit && hit.tokens_est) || (hit && hit.tokensEst) || Math.max(12, Math.ceil(val.length / 4)));
      state.attachedFiles.push({
        path,
        source: 'palace',
        nodeId: (hit && (hit.node_id || hit.nodeId || hit.id)) || '',
        palaceContent: val,
        tag: 'PALACE',
        estTokens: est,
        rag: true
      });
      renderContextFiles();
      return;
    }
    const ext = (String(path).split('.').pop() || 'TXT').toUpperCase().slice(0, 4);
    const spaceHit = itemMeta || state.spaceFiles.find((f) => f.path === path) || _findInventoryItemMeta(path, source);
    const size = spaceHit ? Number(spaceHit.size_bytes || spaceHit.size || 0) : 512;
    state.attachedFiles.push({
      path,
      source: source || 'space',
      tag: ext,
      estTokens: Number((spaceHit && (spaceHit.tokens_est || spaceHit.tokensEst)) || Math.max(12, Math.ceil(size / 4))),
      rag: ext === 'MD' || ext === 'TXT'
    });
    renderContextFiles();
  }

  function ensurePalaceAttached(concept) {
    if (!concept || !concept.canonical_name) return;
    const path = '/palace/' + concept.canonical_name;
    const val = String(concept.value || concept.active_value || concept.summary || '');
    const est = Number(concept.tokens_est || Math.max(12, Math.ceil(val.length / 4)));
    const idx = state.attachedFiles.findIndex((f) =>
      f.source === 'palace' && ((concept.node_id && f.nodeId === concept.node_id) || f.path === path)
    );
    const entry = {
      path,
      source: 'palace',
      nodeId: concept.node_id || '',
      palaceContent: val,
      tag: 'PALACE',
      estTokens: est,
      rag: true
    };
    if (idx !== -1) {
      state.attachedFiles[idx] = entry;
    } else {
      state.attachedFiles.push(entry);
    }
    renderContextFiles();
  }

  function _formatTimestamp(ts) {
    if (ts == null || ts === '') return '';
    if (typeof ts === 'string' && isNaN(Number(ts))) return ts;
    const num = Number(ts);
    if (!Number.isFinite(num) || num <= 0) return '';
    try {
      const ms = num > 1e12 ? num : num * 1000;
      return new Date(ms).toISOString().replace('.000Z', 'Z');
    } catch (e) {
      return String(ts);
    }
  }

  function _formatEdgesText(edges) {
    if (!Array.isArray(edges) || !edges.length) return '';
    return edges.slice(0, 4).map((edge) => {
      if (typeof edge === 'string') return edge;
      if (!edge || typeof edge !== 'object') return '';
      const rel = edge.relation_type || edge.rel || '';
      const tgt = edge.target_name || edge.target_id || edge.target || '';
      return (rel ? (rel + ' ') : '') + '-> ' + tgt;
    }).filter(Boolean).join(', ');
  }

  function _formatInspectorMeta(insp) {
    if (insp.mode !== 'edit' && !insp.nodeId) {
      return 'new concept · unsaved (Context Palace)';
    }
    const parts = [];
    const vf = _formatTimestamp(insp.valid_from || insp.updated_at);
    if (insp.valid_from) {
      parts.push('valid_from: ' + vf);
    } else if (vf) {
      parts.push('updated: ' + vf);
    }
    const edgesStr = _formatEdgesText(insp.edges);
    if (edgesStr) {
      parts.push('edges: ' + edgesStr);
    } else if (Array.isArray(insp.edges)) {
      parts.push('edges: 0');
    }
    if (insp.nodeId) parts.push('id: ' + insp.nodeId);
    const tok = insp.tokens_est || Math.max(1, Math.ceil(String(insp.value || '').length / 4));
    parts.push(tok + ' tok');
    return parts.join(' | ');
  }

  function _findPalaceConcept(nodeOrId) {
    if (!nodeOrId) return null;
    if (typeof nodeOrId === 'object') return nodeOrId;
    const key = String(nodeOrId).trim();
    const clean = key.replace(/^\/palace\//, '');
    const fromPalace = state.palaceNodes.find((n) => n && (n.node_id === key || n.canonical_name === clean || ('/palace/' + n.canonical_name) === key));
    if (fromPalace) return fromPalace;
    const fromInv = state.inventoryItems.find((it) =>
      it && (it.source_group === 'palace' || it.kind === 'palace') &&
      (it.node_id === key || it.id === key || it.title === clean || it.path === key)
    );
    if (fromInv) {
      return {
        node_id: fromInv.node_id || fromInv.id || '',
        canonical_name: fromInv.title || clean,
        category: fromInv.category || 'router_memory',
        summary: fromInv.description || '',
        value: fromInv.value || fromInv.active_value || '',
        valid_from: fromInv.valid_from || '',
        edges: fromInv.edges || [],
        updated_at: fromInv.updated_at || 0,
        tokens_est: fromInv.tokens_est || 0
      };
    }
    return null;
  }

  function _upsertPalaceConcept(concept, previousName) {
    if (!concept) return;
    const nid = concept.node_id || '';
    const idx = state.palaceNodes.findIndex((n) =>
      n && ((nid && n.node_id === nid) || (previousName && n.canonical_name === previousName) || n.canonical_name === concept.canonical_name)
    );
    if (idx !== -1) {
      state.palaceNodes[idx] = Object.assign({}, state.palaceNodes[idx], concept);
    } else {
      state.palaceNodes.unshift(concept);
    }
    if (Array.isArray(state.inventoryItems)) {
      const invIdx = state.inventoryItems.findIndex((it) =>
        it && (it.source_group === 'palace' || it.kind === 'palace') &&
        ((nid && (it.node_id === nid || it.id === nid)) || (previousName && it.title === previousName))
      );
      const invRec = {
        kind: 'palace',
        source_group: 'palace',
        id: nid || concept.canonical_name,
        node_id: nid,
        path: '/palace/' + concept.canonical_name,
        title: concept.canonical_name,
        category: concept.category || 'router_memory',
        description: concept.summary || '',
        value: concept.value || concept.active_value || '',
        tokens_est: concept.tokens_est || Math.max(12, Math.ceil(String(concept.value || '').length / 4)),
        valid_from: concept.valid_from || '',
        edges: concept.edges || [],
        updated_at: concept.updated_at || 0
      };
      if (invIdx !== -1) state.inventoryItems[invIdx] = Object.assign({}, state.inventoryItems[invIdx], invRec);
      else if (state.inventoryFetched) state.inventoryItems.unshift(invRec);
    }
    const oldPath = previousName ? ('/palace/' + previousName) : '';
    const newPath = '/palace/' + concept.canonical_name;
    const val = String(concept.value || concept.active_value || '');
    state.attachedFiles = state.attachedFiles.map((f) => {
      if (f.source === 'palace' && ((nid && f.nodeId === nid) || (oldPath && f.path === oldPath) || f.path === newPath)) {
        return Object.assign({}, f, {
          path: newPath,
          nodeId: nid || f.nodeId,
          palaceContent: val,
          estTokens: Number(concept.tokens_est || Math.max(12, Math.ceil(val.length / 4)))
        });
      }
      return f;
    });
  }

  function _removePalaceConceptFromState(nodeId, canonicalName) {
    const oldPath = canonicalName ? ('/palace/' + canonicalName) : '';
    state.palaceNodes = state.palaceNodes.filter((n) =>
      n && !(nodeId && n.node_id === nodeId) && !(canonicalName && n.canonical_name === canonicalName)
    );
    state.inventoryItems = state.inventoryItems.filter((it) =>
      it && !(nodeId && (it.node_id === nodeId || it.id === nodeId)) && !(oldPath && it.path === oldPath)
    );
    state.attachedFiles = state.attachedFiles.filter((f) =>
      !(f.source === 'palace' && ((nodeId && f.nodeId === nodeId) || (oldPath && f.path === oldPath)))
    );
  }

  function renderInspector(syncInputs) {
    const panel = el('copilotContextInspector');
    if (panel) panel.classList.toggle('hidden', !state.inspector.open);
    const titleEl = el('copilotInspectorTitle');
    if (titleEl) {
      titleEl.textContent = state.inspector.mode === 'edit'
        ? 'CONTEXT INSPECTOR · EDIT'
        : 'CONTEXT INSPECTOR · NEW NODE';
    }
    if (syncInputs) {
      const nEl = el('copilotInspectorName');
      const cEl = el('copilotInspectorCategory');
      const dEl = el('copilotInspectorDesc');
      const vEl = el('copilotInspectorValue');
      if (nEl) nEl.value = state.inspector.canonical_name || '';
      if (cEl) cEl.value = state.inspector.category || 'router_memory';
      if (dEl) dEl.value = state.inspector.summary || '';
      if (vEl) vEl.value = state.inspector.value || '';
    }
    const metaEl = el('copilotInspectorMeta');
    if (metaEl) metaEl.textContent = _formatInspectorMeta(state.inspector);
    const delBtn = el('copilotInspectorDeleteBtn');
    if (delBtn) delBtn.disabled = !(state.inspector.mode === 'edit' && state.inspector.nodeId);
    const stEl = el('copilotInspectorStatus');
    if (stEl) {
      stEl.textContent = state.inspector.statusNote || '';
      stEl.className = 'cp-mono-xs ' + (state.inspector.statusError ? 'cp-danger' : (state.inspector.statusNote ? 'cp-pos' : 'cp-muted'));
    }
  }

  function openPalaceInspector(nodeOrId) {
    const hit = _findPalaceConcept(nodeOrId);
    if (hit) {
      const snap = {
        nodeId: hit.node_id || '',
        canonical_name: hit.canonical_name || hit.title || '',
        category: hit.category || 'router_memory',
        summary: hit.summary || hit.description || '',
        value: hit.value != null ? String(hit.value) : String(hit.active_value || ''),
        valid_from: hit.valid_from || '',
        edges: Array.isArray(hit.edges) ? hit.edges.slice() : [],
        updated_at: hit.updated_at || 0,
        tokens_est: hit.tokens_est || 0
      };
      state.inspector = Object.assign({
        open: true,
        mode: snap.nodeId ? 'edit' : 'create',
        original: Object.assign({}, snap),
        statusNote: 'Inspecting ' + snap.canonical_name,
        statusError: false
      }, snap);
    } else {
      const emptySnap = {
        nodeId: '',
        canonical_name: '',
        category: 'router_memory',
        summary: '',
        value: '',
        valid_from: '',
        edges: [],
        updated_at: 0,
        tokens_est: 0
      };
      state.inspector = Object.assign({
        open: true,
        mode: 'create',
        original: Object.assign({}, emptySnap),
        statusNote: 'Create a new Context Palace ConceptNode.',
        statusError: false
      }, emptySnap);
    }
    renderInspector(true);
    const nameEl = el('copilotInspectorName');
    if (nameEl && typeof nameEl.focus === 'function') nameEl.focus();
  }

  function closePalaceInspector() {
    state.inspector.open = false;
    state.inspector.statusNote = '';
    state.inspector.statusError = false;
    renderInspector(false);
  }

  async function readPalaceConcept(nodeIdOrName) {
    if (!nodeIdOrName) return null;
    try {
      const res = await apiJson('/api/arena/context/palace/crud', {
        method: 'POST',
        body: { action: 'read', node_id: String(nodeIdOrName) }
      });
      if (res && res.concept) {
        _upsertPalaceConcept(res.concept);
        openPalaceInspector(res.concept);
        return res.concept;
      }
    } catch (err) {
      state.inspector.statusNote = 'Read failed: ' + (err && err.message ? err.message : 'offline');
      state.inspector.statusError = true;
      renderInspector(false);
    }
    return null;
  }

  async function savePalaceInspector() {
    const name = ((el('copilotInspectorName') && el('copilotInspectorName').value) || '').trim();
    const category = ((el('copilotInspectorCategory') && el('copilotInspectorCategory').value) || 'router_memory').trim() || 'router_memory';
    const summary = ((el('copilotInspectorDesc') && el('copilotInspectorDesc').value) || '').trim();
    const value = ((el('copilotInspectorValue') && el('copilotInspectorValue').value) || '').trim();
    if (!name || !value) {
      state.inspector.statusNote = 'Concept name and value are required.';
      state.inspector.statusError = true;
      renderInspector(false);
      return null;
    }
    const isEdit = state.inspector.mode === 'edit' && Boolean(state.inspector.nodeId);
    const action = isEdit ? 'update' : 'create';
    const prevName = state.inspector.original ? state.inspector.original.canonical_name : '';
    const payload = {
      action,
      canonical_name: name,
      category,
      summary,
      description: summary,
      value
    };
    if (isEdit) payload.node_id = state.inspector.nodeId;
    try {
      const res = await apiJson('/api/arena/context/palace/crud', {
        method: 'POST',
        body: payload
      });
      const concept = (res && res.concept) || Object.assign({}, payload, {
        node_id: state.inspector.nodeId || ('pal-' + Date.now().toString(36)),
        tokens_est: Math.max(12, Math.ceil(value.length / 4))
      });
      _upsertPalaceConcept(concept, prevName);
      openPalaceInspector(concept);
      state.inspector.statusNote = (action === 'update' ? 'Updated "' : 'Created "') + concept.canonical_name + '".';
      state.inspector.statusError = false;
      renderInspector(false);
      renderContextFiles();
      notify('Context Palace ' + action + ': ' + concept.canonical_name, false);
      refreshSpaceAndDrive().catch(() => {});
      return concept;
    } catch (err) {
      state.inspector.statusNote = 'Save failed: ' + (err && err.message ? err.message : 'sign in first');
      state.inspector.statusError = true;
      renderInspector(false);
      notify('Context Palace save failed: ' + (err && err.message ? err.message : 'failed'), true);
      return null;
    }
  }

  function revertPalaceInspector() {
    const orig = state.inspector.original;
    if (orig) {
      state.inspector.nodeId = orig.nodeId || '';
      state.inspector.canonical_name = orig.canonical_name || '';
      state.inspector.category = orig.category || 'router_memory';
      state.inspector.summary = orig.summary || '';
      state.inspector.value = orig.value || '';
      state.inspector.valid_from = orig.valid_from || '';
      state.inspector.edges = Array.isArray(orig.edges) ? orig.edges.slice() : [];
      state.inspector.updated_at = orig.updated_at || 0;
      state.inspector.tokens_est = orig.tokens_est || 0;
    }
    state.inspector.statusNote = 'Reverted unsaved changes.';
    state.inspector.statusError = false;
    renderInspector(true);
  }

  async function deletePalaceInspector() {
    const nodeId = state.inspector.nodeId;
    const name = state.inspector.canonical_name || (state.inspector.original && state.inspector.original.canonical_name) || '';
    if (!nodeId) {
      state.inspector.statusNote = 'Nothing to delete (unsaved concept).';
      state.inspector.statusError = true;
      renderInspector(false);
      return false;
    }
    try {
      await apiJson('/api/arena/context/palace/crud', {
        method: 'POST',
        body: { action: 'delete', node_id: nodeId }
      });
      _removePalaceConceptFromState(nodeId, name);
      state.inspector.open = false;
      state.inspector.mode = 'create';
      state.inspector.nodeId = '';
      state.inspector.canonical_name = '';
      state.inspector.summary = '';
      state.inspector.value = '';
      state.inspector.original = null;
      state.inspector.statusNote = 'Deleted "' + (name || nodeId) + '".';
      state.inspector.statusError = false;
      renderInspector(true);
      renderContextFiles();
      notify('Deleted "' + (name || nodeId) + '" from Context Palace.', false);
      refreshSpaceAndDrive().catch(() => {});
      return true;
    } catch (err) {
      state.inspector.statusNote = 'Delete failed: ' + (err && err.message ? err.message : 'failed');
      state.inspector.statusError = true;
      renderInspector(false);
      return false;
    }
  }

  async function sendInspectorToRouter() {
    let nodeId = state.inspector.nodeId;
    const name = ((el('copilotInspectorName') && el('copilotInspectorName').value) || state.inspector.canonical_name || '').trim();
    const category = ((el('copilotInspectorCategory') && el('copilotInspectorCategory').value) || state.inspector.category || 'router_memory').trim();
    const summary = ((el('copilotInspectorDesc') && el('copilotInspectorDesc').value) || state.inspector.summary || '').trim();
    const value = ((el('copilotInspectorValue') && el('copilotInspectorValue').value) || state.inspector.value || '').trim();

    if (!nodeId && name && value && typeof fetch === 'function') {
      const created = await savePalaceInspector();
      if (created) {
        ensurePalaceAttached(created);
        state.inspector.statusNote = 'Created & attached "' + created.canonical_name + '" to Router.';
        state.inspector.statusError = false;
        renderInspector(false);
        return created;
      }
      return null;
    }
    if (!name) {
      state.inspector.statusNote = 'Enter or select a ConceptNode before attaching to Router.';
      state.inspector.statusError = true;
      renderInspector(false);
      return null;
    }
    const concept = {
      node_id: nodeId || '',
      canonical_name: name,
      category,
      summary,
      value: value || summary,
      tokens_est: state.inspector.tokens_est || Math.max(12, Math.ceil((value || summary).length / 4))
    };
    _upsertPalaceConcept(concept);
    ensurePalaceAttached(concept);
    state.inspector.statusNote = 'Injected "' + name + '" into Router active capsules.';
    state.inspector.statusError = false;
    renderInspector(false);
    notify('Attached Palace capsule "' + name + '" to AI Brain Router.', false);
    return concept;
  }

  async function sendInspectorToArenaBoth() {
    let nodeId = state.inspector.nodeId;
    if (!nodeId) {
      const created = await savePalaceInspector();
      if (!created || !created.node_id) return null;
      nodeId = created.node_id;
    }
    try {
      const res = await apiJson('/api/arena/context/palace/import', {
        method: 'POST',
        body: { agent_id: 'both', node_ids: [nodeId] }
      });
      state.inspector.statusNote = 'Sent to Arena Brain A & Brain B!';
      state.inspector.statusError = false;
      renderInspector(false);
      notify('Imported ConceptNode to Brain A & Brain B!', false);
      if (typeof window.arenaCtxRefresh === 'function') {
        window.arenaCtxRefresh('arenaWin', 'A');
        window.arenaCtxRefresh('arenaWin', 'B');
      }
      return res;
    } catch (err) {
      state.inspector.statusNote = 'Arena import failed: ' + (err && err.message ? err.message : 'sign in first');
      state.inspector.statusError = true;
      renderInspector(false);
      return null;
    }
  }

  function _invAttach(idx) {
    const it = state.renderedInventory[idx];
    if (!it) return;
    attachContextFile(it.path, it.source, it);
  }

  function _invEdit(idx) {
    const it = state.renderedInventory[idx];
    if (!it) return;
    openPalaceInspector(it.nodeId || it.title || it.path);
  }

  async function _invToArena(idx) {
    const it = state.renderedInventory[idx];
    if (!it || !it.nodeId) {
      await sendPalaceToArenaBoth();
      return;
    }
    try {
      const res = await apiJson('/api/arena/context/palace/import', {
        method: 'POST',
        body: { agent_id: 'both', node_ids: [it.nodeId] }
      });
      notify('Imported "' + (it.title || it.nodeId) + '" to Brain A & Brain B!', false);
      if (typeof window.arenaCtxRefresh === 'function') {
        window.arenaCtxRefresh('arenaWin', 'A');
        window.arenaCtxRefresh('arenaWin', 'B');
      }
      return res;
    } catch (err) {
      notify('Could not import Palace to Arena: ' + (err && err.message ? err.message : 'sign in first'), true);
    }
  }

  async function promptCreatePalaceConcept(titleArg, valueArg, opts) {
    // Interactive UI flow opens the inline Context Inspector & Editor without browser prompt dialogs.
    if (typeof titleArg !== 'string' || !titleArg.trim() || typeof valueArg !== 'string' || !valueArg.trim()) {
      openPalaceInspector(null);
      return null;
    }
    const extra = opts || {};
    try {
      const res = await apiJson('/api/arena/context/palace/crud', {
        method: 'POST',
        body: {
          action: 'create',
          canonical_name: titleArg.trim(),
          category: String(extra.category || 'router_memory'),
          summary: String(extra.summary || extra.description || ''),
          value: valueArg.trim()
        }
      });
      const concept = (res && res.concept) || {
        node_id: '',
        canonical_name: titleArg.trim(),
        category: String(extra.category || 'router_memory'),
        summary: String(extra.summary || extra.description || ''),
        value: valueArg.trim()
      };
      _upsertPalaceConcept(concept);
      ensurePalaceAttached(concept);
      notify('Added "' + titleArg.trim() + '" to Context Palace & attached to Copilot.', false);
      refreshSpaceAndDrive().catch(() => {});
      return concept;
    } catch (err) {
      notify('Context Palace save requires sign-in: ' + (err && err.message ? err.message : 'failed'), true);
      return null;
    }
  }

  async function sendPalaceToArenaBoth() {
    const palaceAtt = state.attachedFiles.filter((f) => f.source === 'palace' && f.nodeId).map((f) => f.nodeId);
    try {
      const res = await apiJson('/api/arena/context/palace/import', {
        method: 'POST',
        body: { agent_id: 'both', node_ids: palaceAtt.length ? palaceAtt : null }
      });
      notify('Imported ' + (res.imported_count || 0) + ' Context Palace item(s) to Brain A & Brain B!', false);
      if (typeof window.arenaCtxRefresh === 'function') {
        window.arenaCtxRefresh('arenaWin', 'A');
        window.arenaCtxRefresh('arenaWin', 'B');
      }
    } catch (err) {
      notify('Could not import Palace to Arena: ' + (err && err.message ? err.message : 'sign in first'), true);
    }
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

  async function refreshInventory(queryOverride) {
    const q = typeof queryOverride === 'string' ? queryOverride : state.inventoryQuery;
    try {
      const inv = await apiJson(
        '/api/arena/context/inventory?q=' + encodeURIComponent(q || ''),
        { channel: 'inventoryLs' }
      );
      if (inv && Array.isArray(inv.items)) {
        state.inventoryItems = inv.items;
        state.inventoryFetched = true;
      }
      if (inv && inv.palace && Array.isArray(inv.palace.concepts)) {
        state.palaceNodes = inv.palace.concepts;
      }
      renderAttachDrawer();
    } catch (e) {}
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
    try {
      const pl = await apiJson('/api/arena/context/palace?limit=40', { channel: 'palaceLs' });
      if (Array.isArray(pl.concepts)) {
        state.palaceNodes = pl.concepts;
      }
      renderAttachDrawer();
    } catch (e) {}
    await refreshInventory(state.inventoryQuery);
  }

  async function refresh() {
    await Promise.all([refreshAnalytics(), refreshModels(), refreshSpaceAndDrive()]);
  }

  async function gatherAttachedContextSnippets() {
    resolveSpaceContext();
    const snippets = [];
    for (let i = 0; i < state.attachedFiles.length && i < 8; i++) {
      const f = state.attachedFiles[i];
      if (f.source === 'palace') {
        const hit = state.palaceNodes.find((n) => n.node_id === f.nodeId || ('/palace/' + n.canonical_name) === f.path);
        const body = String((hit && (hit.value || hit.active_value)) || f.palaceContent || '').slice(0, 1500);
        if (body) snippets.push('[' + f.path + ' · Context Palace]\n' + body);
        continue;
      }
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
        scope: state.scope || 'user',
        owner_id: state.ownerId || resolvePeerId(),
        active_file: (typeof window !== 'undefined' && window.currentSpaceFile) || null,
        use_space_context: true,
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
    _notifyCopilotInstanceTitle();
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
    const q = _getUrlParams();
    if (q) {
      if (q.get('fresh') === '1') {
        state.turns = [];
        state.seededOnly = false;
        state.threadId = '';
      }
      if (q.get('thread')) {
        state.threadName = q.get('thread');
        const nameEl = el('copilotThreadName');
        if (nameEl) nameEl.textContent = state.threadName;
      }
      if (q.get('priority') && PRIORITIES[q.get('priority')]) {
        state.priority = q.get('priority');
      }
      if (q.get('model')) {
        state.model = q.get('model');
      }
      if (q.get('prompt') && el('copilotPromptInput')) {
        el('copilotPromptInput').value = q.get('prompt');
      }
    }
    renderPriorityUI();
    renderModelSelect();
    renderContextFiles();
    renderInspector(false);
    renderArbitrageStats();
    renderThreadLog();
    wireDomEvents();
    _notifyCopilotInstanceTitle();
  }

  window.TinCanCopilot = {
    version: 1,
    init,
    refresh,
    refreshInventory,
    setPriority,
    selectModel,
    estimatePreflight,
    sendMessage,
    newThread,
    exportMarkdown,
    toggleAttachDrawer,
    setInventoryTab,
    setInventoryQuery,
    attachContextFile,
    removeContextFile,
    openPalaceInspector,
    closePalaceInspector,
    readPalaceConcept,
    savePalaceInspector,
    revertPalaceInspector,
    deletePalaceInspector,
    sendInspectorToRouter,
    sendInspectorToArenaBoth,
    promptCreatePalaceConcept,
    sendPalaceToArenaBoth,
    applyPatch,
    duelInArena,
    runPytestInSpace,
    _invAttach,
    _invEdit,
    _invToArena,
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
      <div id="copilotRoot" class="window-body cp-body aeonik-scope" data-copilot-root="true">
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
              <div id="copilotAttachDrawer" class="cp-attach-drawer hidden" aria-label="Available Space, Drive, and Context Palace items">
                <div class="cp-inv-toolbar">
                  <input id="copilotInventorySearch" type="search" class="cp-inv-search" placeholder="Search Palace, .space, Drive..." aria-label="Search Universal Context Inventory" oninput="window.TinCanCopilot && window.TinCanCopilot.setInventoryQuery(this.value)" />
                  <button type="button" id="copilotPalaceNewBtn" class="cp-btn cp-btn--sm cp-btn--solid" onclick="window.TinCanCopilot && window.TinCanCopilot.openPalaceInspector()">+ New Node</button>
                </div>
                <div id="copilotInventoryTabs" class="cp-inv-tabs" role="tablist" aria-label="Context inventory source filter">
                  <button type="button" id="copilotInvTab-all" role="tab" aria-selected="true" class="cp-inv-tab is-active" onclick="window.TinCanCopilot && window.TinCanCopilot.setInventoryTab('all')">All</button>
                  <button type="button" id="copilotInvTab-palace" role="tab" aria-selected="false" class="cp-inv-tab" onclick="window.TinCanCopilot && window.TinCanCopilot.setInventoryTab('palace')">Palace</button>
                  <button type="button" id="copilotInvTab-space" role="tab" aria-selected="false" class="cp-inv-tab" onclick="window.TinCanCopilot && window.TinCanCopilot.setInventoryTab('space')">.space</button>
                  <button type="button" id="copilotInvTab-drive" role="tab" aria-selected="false" class="cp-inv-tab" onclick="window.TinCanCopilot && window.TinCanCopilot.setInventoryTab('drive')">Drive</button>
                </div>
                <div class="cp-inv-toolbar" style="justify-content: space-between;">
                  <span id="copilotInventorySummary" class="cp-mono-xs cp-muted">0 items</span>
                  <button type="button" id="copilotPalaceToArenaBtn" class="cp-btn cp-btn--sm" onclick="window.TinCanCopilot && window.TinCanCopilot.sendPalaceToArenaBoth()">&#x2192; Arena Both</button>
                </div>
                <div id="copilotInventoryList" class="cp-inv-list"></div>
              </div>
              <button id="copilotAttachCtxBtn" type="button" class="cp-btn cp-btn--full" onclick="window.TinCanCopilot && window.TinCanCopilot.toggleAttachDrawer()">+ Attach .space / Drive Files</button>
              <button id="copilotAttachPalaceBtn" type="button" class="cp-btn cp-btn--sm cp-btn--full" style="margin-top:4px;" onclick="window.TinCanCopilot && window.TinCanCopilot.toggleAttachDrawer('palace')">🏛️ Import Context Palace → Router &amp; Arena</button>
            </section>

            <section id="copilotContextInspector" class="cp-card cp-inspector hidden" aria-label="Context Palace Inspector and Editor">
              <div class="cp-sec-head">
                <span id="copilotInspectorTitle" class="cp-sec-label">CONTEXT INSPECTOR &amp; EDITOR</span>
                <button id="copilotInspectorCloseBtn" type="button" class="cp-ctx-remove" aria-label="Close context inspector" onclick="window.TinCanCopilot && window.TinCanCopilot.closePalaceInspector()">&#x2715;</button>
              </div>
              <div class="cp-insp-actions">
                <button id="copilotInspectorSaveBtn" type="button" class="cp-btn cp-btn--sm cp-btn--pos" onclick="window.TinCanCopilot && window.TinCanCopilot.savePalaceInspector()">Save Edit</button>
                <button id="copilotInspectorRevertBtn" type="button" class="cp-btn cp-btn--sm" onclick="window.TinCanCopilot && window.TinCanCopilot.revertPalaceInspector()">Revert</button>
                <button id="copilotInspectorDeleteBtn" type="button" class="cp-btn cp-btn--sm cp-btn--danger" onclick="window.TinCanCopilot && window.TinCanCopilot.deletePalaceInspector()">Delete</button>
              </div>
              <input id="copilotInspectorName" type="text" class="cp-insp-field" placeholder="Concept name (e.g. bitemporal-crdt-sync)" aria-label="Concept name" />
              <input id="copilotInspectorCategory" type="text" class="cp-insp-field" placeholder="Category (e.g. router_memory)" aria-label="Concept category" />
              <input id="copilotInspectorDesc" type="text" class="cp-insp-field" placeholder="Description / summary..." aria-label="Concept description" />
              <div id="copilotInspectorMeta" class="cp-insp-meta">new concept · unsaved (Context Palace)</div>
              <textarea id="copilotInspectorValue" rows="3" class="cp-insp-field" placeholder="Concept value / memory rules..." aria-label="Concept value"></textarea>
              <div class="cp-insp-actions">
                <button id="copilotInspectorToRouterBtn" type="button" class="cp-btn cp-btn--sm" onclick="window.TinCanCopilot && window.TinCanCopilot.sendInspectorToRouter()">&#x2192; Router</button>
                <button id="copilotInspectorToArenaBtn" type="button" class="cp-btn cp-btn--sm cp-btn--solid" onclick="window.TinCanCopilot && window.TinCanCopilot.sendInspectorToArenaBoth()">&#x2192; Arena Both</button>
              </div>
              <div id="copilotInspectorStatus" class="cp-mono-xs cp-muted" aria-live="polite"></div>
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
              <div id="copilotActiveCapsules" class="cp-capsules" aria-label="Active attached Context Palace and Space capsules">
                <span class="cp-capsule-summary">Active Capsules (4,080t):</span>
                <span class="cp-capsule-chip cp-capsule-chip--file" data-copilot-capsule="/ai_gateway.py"><span>.space: ai_gateway.py (2140t)</span><button type="button" class="cp-capsule-rm" aria-label="Detach ai_gateway.py" onclick="window.TinCanCopilot && window.TinCanCopilot.removeContextFile(0)">&#x00D7;</button></span>
                <span class="cp-capsule-chip cp-capsule-chip--file" data-copilot-capsule="/tincan_agent.py"><span>.space: tincan_agent.py (1080t)</span><button type="button" class="cp-capsule-rm" aria-label="Detach tincan_agent.py" onclick="window.TinCanCopilot && window.TinCanCopilot.removeContextFile(1)">&#x00D7;</button></span>
                <span class="cp-capsule-chip cp-capsule-chip--file" data-copilot-capsule="/Vault/FAU-Thesis.md"><span>Drive: Vault/FAU-Thesis.md (860t)</span><button type="button" class="cp-capsule-rm" aria-label="Detach Vault/FAU-Thesis.md" onclick="window.TinCanCopilot && window.TinCanCopilot.removeContextFile(2)">&#x00D7;</button></span>
              </div>
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
    "_COPILOT_CSS",
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
