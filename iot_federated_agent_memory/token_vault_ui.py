"""TinCan Mesh OS: Aeonik Celadon & Ink Token Vault & Sponsor Store UI.

Provides ``#win-billing`` markup, scoped Aeonik Celadon CSS, and hydration JS
aligned with server ``TOKEN_PACKS`` (``pack_100`` -> 120, ``pack_500`` -> 650,
``pack_2000`` -> 2800), ``AD_DAILY_REWARD_CAP``, and Hyper3D Rodin pool billing.

All legacy ``#win-billing`` DOM IDs and ``onclick`` callbacks referenced by
``mesh_os_ui.py`` are preserved intact.
"""

from __future__ import annotations

import html as _html
import json
from typing import Any, Dict

from .token_ledger import (
    DEFAULT_AD_COMPUTE_COST_USD,
    DEFAULT_AD_PAYOUT_USD,
    DEFAULT_AD_REWARD_TOKENS,
    SERVICE_RATE_CARD,
    TOKEN_PACK_CATALOG,
)

TOKEN_VAULT_WINDOW_SLOT = "<!--TC_TOKEN_VAULT_WINDOW-->"
TOKEN_VAULT_CSS_SLOT = "/*TC_TOKEN_VAULT_CSS*/"
TOKEN_VAULT_JS_SLOT = "/*TC_TOKEN_VAULT_JS*/"

TOKEN_VAULT_TITLEBAR = (
    '<!--TC_TITLEBAR {"id": "win-billing", '
    '"title": "Token Vault · Stripe Packs & Sponsor Arbitrage", '
    '"badge": "STRIPE + ARBITRAGE"}-->'
)

TOKEN_VAULT_CSS = r"""
/* tc-token-vault-css */
/* Aeonik Celadon & Ink (#dfe6d7 desk / #ecf1e6 canvas / #f4f8f0 card / #ffffff paper / #111111 ink) */
#win-billing {
  --tv-desk: #dfe6d7;
  --tv-bg: #ecf1e6;
  --tv-card: #f4f8f0;
  --tv-paper: #ffffff;
  --tv-ink: #111111;
  --tv-muted: #4a4a4a;
  --tv-faint: #5c5c5c;
  --tv-pos: #107a47;
  --tv-pos-bg: rgba(16, 122, 71, 0.09);
  --tv-danger: #8a1c1c;
  --tv-danger-bg: rgba(138, 28, 28, 0.08);
  --tv-hair: 1px solid #111111;
  --tv-hair-soft: 1px solid rgba(17, 17, 17, 0.16);
  --tv-font: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --tv-mono: "JetBrains Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace;
}
#win-billing .hidden { display: none !important; }
#win-billing .tv-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px 14px;
  max-height: min(760px, calc(100vh - 110px));
  overflow-y: auto;
  background: var(--tv-bg);
  color: var(--tv-ink);
  font-family: var(--tv-font);
  font-size: 12px;
  line-height: 1.45;
  container-type: inline-size;
  container-name: tvbody;
}
#win-billing.maximized .tv-body,
#win-billing.popout-fullscreen .tv-body {
  max-height: none;
  height: 100%;
}

/* Sub-header telemetry strip */
#win-billing .tv-subbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 12px;
  padding: 6px 10px;
  background: var(--tv-card);
  border: var(--tv-hair);
  border-radius: 10px;
}
#win-billing .tv-subbar-group {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  min-width: 0;
}
#win-billing .tv-mono { font-family: var(--tv-mono); font-variant-numeric: tabular-nums; }
#win-billing .tv-mono-xs { font-family: var(--tv-mono); font-size: 10px; line-height: 1.4; font-variant-numeric: tabular-nums; }
#win-billing .tv-muted { color: var(--tv-muted); }
#win-billing .tv-faint { color: var(--tv-faint); }
#win-billing .tv-pos { color: var(--tv-pos); }
#win-billing .tv-danger { color: var(--tv-danger); }
#win-billing .tv-truncate { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Pills & Badges */
#win-billing .tv-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 4px 12px;
  border: var(--tv-hair);
  border-radius: 9999px;
  background: var(--tv-paper);
  color: var(--tv-ink);
  font-family: var(--tv-mono);
  font-size: 11px;
  font-weight: 600;
  line-height: 1.3;
  white-space: nowrap;
  text-decoration: none;
  cursor: pointer;
  transition: background 120ms ease, color 120ms ease, opacity 120ms ease;
}
#win-billing .tv-pill:hover { background: var(--tv-ink); color: var(--tv-bg); }
#win-billing .tv-pill:disabled { opacity: 0.48; cursor: not-allowed; }
#win-billing .tv-pill--solid { background: var(--tv-ink); color: var(--tv-bg); }
#win-billing .tv-pill--solid:hover { opacity: 0.86; background: #262626; color: var(--tv-bg); }
#win-billing .tv-pill--sm { padding: 2px 9px; font-size: 10px; }
#win-billing .tv-pill--full { width: 100%; padding: 8px 14px; font-size: 11px; }

#win-billing .tv-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border: var(--tv-hair);
  border-radius: 9999px;
  background: var(--tv-paper);
  color: var(--tv-ink);
  font-family: var(--tv-mono);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  white-space: nowrap;
}
#win-billing .tv-badge--ink { background: var(--tv-ink); color: var(--tv-bg); }
#win-billing .tv-badge--pos { border-color: var(--tv-pos); background: var(--tv-pos-bg); color: var(--tv-pos); }
#win-billing .tv-badge--danger { border-color: var(--tv-danger); background: var(--tv-danger-bg); color: var(--tv-danger); }

/* 4-KPI Row */
#win-billing .tv-kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}
#win-billing .tv-kpi-card {
  background: var(--tv-paper);
  border: var(--tv-hair);
  border-radius: 12px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}
#win-billing .tv-kpi-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--tv-faint);
}
#win-billing .tv-kpi-row {
  display: flex;
  align-items: baseline;
  gap: 5px;
  min-width: 0;
}
#win-billing .tv-kpi-val {
  font-family: var(--tv-mono);
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--tv-ink);
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}
#win-billing .tv-kpi-val--pos { color: var(--tv-pos); }
#win-billing .tv-kpi-unit {
  font-family: var(--tv-mono);
  font-size: 11px;
  font-weight: 600;
  color: var(--tv-muted);
}
#win-billing .tv-kpi-sub {
  font-size: 10px;
  color: var(--tv-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Credit Margin Dial (Operator Control) */
#win-billing .tv-dial-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 12px;
  padding: 8px 12px;
  background: var(--tv-card);
  border: var(--tv-hair);
  border-radius: 12px;
}
#win-billing .tv-dial-controls {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  flex: 1 1 280px;
}
#win-billing .tv-dial-slider {
  flex: 1 1 140px;
  min-width: 110px;
  accent-color: var(--tv-ink);
  cursor: pointer;
}
#win-billing .tv-dial-presets {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 5px;
}

/* Main 2-column grid */
#win-billing .tv-main-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.32fr) minmax(0, 1fr);
  gap: 12px;
  align-items: stretch;
}
#win-billing .tv-col {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}
#win-billing .tv-panel {
  background: var(--tv-paper);
  border: var(--tv-hair);
  border-radius: 14px;
  padding: 11px 12px;
  display: flex;
  flex-direction: column;
  gap: 9px;
  min-width: 0;
}
#win-billing .tv-panel--celadon {
  background: var(--tv-card);
}
#win-billing .tv-sec-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}
#win-billing .tv-sec-title {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--tv-faint);
}

/* Stripe 3-pack row */
#win-billing .tv-pack-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 9px;
}
#win-billing .tv-pack-card {
  background: var(--tv-paper);
  border: var(--tv-hair);
  border-radius: 12px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 8px;
  min-width: 0;
}
#win-billing .tv-pack-card--featured {
  border: 2px solid var(--tv-ink);
  box-shadow: 0 3px 0 rgba(17, 17, 17, 0.12);
}
#win-billing .tv-pack-tier {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--tv-faint);
}
#win-billing .tv-pack-price {
  font-family: var(--tv-mono);
  font-size: 19px;
  font-weight: 700;
  color: var(--tv-ink);
  font-variant-numeric: tabular-nums;
  margin-top: 2px;
}
#win-billing .tv-pack-credits {
  font-family: var(--tv-mono);
  font-size: 11px;
  font-weight: 600;
  color: var(--tv-pos);
  margin-top: 1px;
}
#win-billing .tv-pack-desc {
  font-size: 10px;
  line-height: 1.4;
  color: var(--tv-muted);
  margin-top: 4px;
}

/* Service Rate Card */
#win-billing .tv-rate-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px 12px;
}
#win-billing .tv-rate-item {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 6px;
  padding: 4px 0;
  border-bottom: var(--tv-hair-soft);
  font-size: 11px;
  min-width: 0;
}
#win-billing .tv-rate-name {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: var(--tv-ink);
  min-width: 0;
}
#win-billing .tv-dot {
  width: 6px;
  height: 6px;
  border-radius: 9999px;
  background: var(--tv-ink);
  flex: 0 0 auto;
}
#win-billing .tv-rate-val {
  font-family: var(--tv-mono);
  font-size: 10px;
  font-weight: 600;
  color: var(--tv-muted);
  white-space: nowrap;
}

/* Sponsor Video Compute Subsidy */
#win-billing .tv-sponsor-box {
  background: var(--tv-card);
  border: var(--tv-hair);
  border-radius: 10px;
  padding: 9px 10px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}
#win-billing .tv-sponsor-lead {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  min-width: 0;
  flex: 1 1 auto;
}
#win-billing .tv-sponsor-icon {
  width: 36px;
  height: 36px;
  border: var(--tv-hair);
  border-radius: 9px;
  background: var(--tv-paper);
  color: var(--tv-ink);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex: 0 0 auto;
}
#win-billing .tv-sponsor-name {
  font-weight: 700;
  font-size: 12px;
  color: var(--tv-ink);
}
#win-billing .tv-sponsor-tag {
  font-size: 11px;
  color: var(--tv-muted);
  margin-top: 2px;
  line-height: 1.38;
}
#win-billing .tv-cap-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
#win-billing .tv-cap-track {
  width: 100%;
  height: 8px;
  border: var(--tv-hair);
  border-radius: 9999px;
  background: var(--tv-paper);
  overflow: hidden;
}
#win-billing .tv-cap-fill {
  height: 100%;
  background: var(--tv-ink);
  transition: width 220ms ease;
}
#win-billing .tv-cap-label {
  font-family: var(--tv-mono);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.03em;
  color: var(--tv-ink);
}
#win-billing .tv-arb-box {
  background: var(--tv-card);
  border: var(--tv-hair-soft);
  border-radius: 10px;
  padding: 8px 10px;
  font-family: var(--tv-mono);
  font-size: 10px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
#win-billing .tv-arb-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
#win-billing .tv-ad-player-box {
  background: var(--tv-card);
  border: var(--tv-hair);
  border-radius: 10px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
#win-billing .tv-ad-video-stage {
  position: relative;
  background: #111111;
  border-radius: 8px;
  overflow: hidden;
  aspect-ratio: 16 / 9;
  display: flex;
  align-items: center;
  justify-content: center;
}
#win-billing .tv-ad-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
#win-billing .tv-ad-overlay {
  position: absolute;
  top: 6px;
  left: 6px;
  padding: 2px 8px;
  border-radius: 9999px;
  background: rgba(236, 241, 230, 0.92);
  color: #111111;
  border: var(--tv-hair);
  font-family: var(--tv-mono);
  font-size: 10px;
  font-weight: 600;
}
#win-billing .tv-ad-progress-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
#win-billing .tv-ad-progress-meta {
  display: flex;
  justify-content: space-between;
  font-family: var(--tv-mono);
  font-size: 10px;
  color: var(--tv-ink);
}
#win-billing .tv-ad-progress-track {
  width: 100%;
  height: 6px;
  border: var(--tv-hair);
  border-radius: 9999px;
  background: var(--tv-paper);
  overflow: hidden;
}
#win-billing .tv-ad-progress-fill {
  height: 100%;
  background: var(--tv-ink);
  transition: width 260ms linear;
}
#win-billing .tv-sponsor-foot {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  font-family: var(--tv-mono);
  font-size: 10px;
  color: var(--tv-faint);
}
#win-billing .tv-link-btn {
  background: transparent;
  border: 0;
  padding: 0;
  font-family: var(--tv-mono);
  font-size: 10px;
  font-weight: 600;
  color: var(--tv-ink);
  text-decoration: underline;
  cursor: pointer;
}

/* Ledger table */
#win-billing .tv-ledger-wrap {
  max-height: 200px;
  overflow: auto;
  border: var(--tv-hair-soft);
  border-radius: 10px;
  background: var(--tv-paper);
}
#win-billing .tv-ledger-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--tv-mono);
  font-size: 10.5px;
  font-variant-numeric: tabular-nums;
  text-align: left;
}
#win-billing .tv-ledger-table th {
  position: sticky;
  top: 0;
  background: var(--tv-card);
  color: var(--tv-faint);
  font-size: 9.5px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 6px 9px;
  border-bottom: var(--tv-hair);
  white-space: nowrap;
}
#win-billing .tv-ledger-table td {
  padding: 6px 9px;
  border-bottom: var(--tv-hair-soft);
  color: var(--tv-ink);
  white-space: nowrap;
}
#win-billing .tv-ledger-table tbody tr:last-child td { border-bottom: 0; }
#win-billing .tv-ledger-table tbody tr:hover td { background: var(--tv-card); }
#win-billing .tv-num { text-align: right; }
#win-billing .tv-cell-pos { color: var(--tv-pos); font-weight: 600; }
#win-billing .tv-cell-danger { color: var(--tv-danger); font-weight: 600; }
#win-billing .tv-cell-muted { color: var(--tv-muted); }

/* Compact Hyper3D Rodin Pool Strip */
#win-billing .tv-rodin-strip {
  background: var(--tv-card);
  border: var(--tv-hair);
  border-radius: 12px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
#win-billing .tv-rodin-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}
#win-billing .tv-rodin-stat {
  background: var(--tv-paper);
  border: var(--tv-hair-soft);
  border-radius: 8px;
  padding: 6px 8px;
  min-width: 0;
}
#win-billing .tv-rodin-k {
  display: block;
  font-family: var(--tv-mono);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--tv-faint);
}
#win-billing .tv-rodin-v {
  display: block;
  font-family: var(--tv-mono);
  font-size: 13px;
  font-weight: 700;
  color: var(--tv-ink);
  font-variant-numeric: tabular-nums;
  margin-top: 1px;
}

/* Footer integrity strip */
#win-billing .tv-footer-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding-top: 6px;
  border-top: var(--tv-hair-soft);
  font-family: var(--tv-mono);
  font-size: 10px;
  color: var(--tv-faint);
}

@container tvbody (max-width: 780px) {
  #win-billing .tv-kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  #win-billing .tv-main-grid { grid-template-columns: 1fr; }
  #win-billing .tv-pack-grid { grid-template-columns: 1fr; }
  #win-billing .tv-rate-grid { grid-template-columns: 1fr; }
  #win-billing .tv-rodin-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 820px) {
  #win-billing .tv-kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  #win-billing .tv-main-grid { grid-template-columns: 1fr; }
  #win-billing .tv-rodin-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 540px) {
  #win-billing .tv-kpi-grid { grid-template-columns: 1fr; }
  #win-billing .tv-pack-grid { grid-template-columns: 1fr; }
  #win-billing .tv-rate-grid { grid-template-columns: 1fr; }
}

/* Monochrome Black & White Dark Mode (Artboard 05: Token Vault & Sponsor Store) */
html[data-theme="dark"],
body.tc-dark,
html[data-theme="dark"] #win-billing,
body.tc-dark #win-billing {
  --tv-desk: #080808;
  --tv-bg: #0e0e0e;
  --tv-card: #151515;
  --tv-paper: #1a1a1a;
  --tv-ink: #f5f5f5;
  --tv-muted: #a3a3a3;
  --tv-faint: #737373;
  --tv-line: #2e2e2e;
  --tv-green: #ffffff;
  --tv-pos: #ffffff;
  --tv-pos-bg: rgba(255, 255, 255, 0.12);
  --tv-danger: #d4d4d4;
  --tv-danger-bg: rgba(255, 255, 255, 0.08);
  --tv-hair: 1px solid #2e2e2e;
  --tv-hair-soft: 1px solid rgba(255, 255, 255, 0.14);
}
html[data-theme="dark"] #win-billing .tv-body,
body.tc-dark #win-billing .tv-body {
  background: #0e0e0e !important;
  color: #f5f5f5 !important;
}
html[data-theme="dark"] #win-billing .tv-subbar,
body.tc-dark #win-billing .tv-subbar,
html[data-theme="dark"] #win-billing .tv-kpi-card,
body.tc-dark #win-billing .tv-kpi-card,
html[data-theme="dark"] #win-billing .tv-panel,
body.tc-dark #win-billing .tv-panel,
html[data-theme="dark"] #win-billing .tv-panel--celadon,
body.tc-dark #win-billing .tv-panel--celadon,
html[data-theme="dark"] #win-billing .tv-sponsor-box,
body.tc-dark #win-billing .tv-sponsor-box,
html[data-theme="dark"] #win-billing .tv-arb-box,
body.tc-dark #win-billing .tv-arb-box,
html[data-theme="dark"] #win-billing .tv-rodin-strip,
body.tc-dark #win-billing .tv-rodin-strip,
html[data-theme="dark"] #win-billing .tv-rodin-stat,
body.tc-dark #win-billing .tv-rodin-stat {
  background: #151515 !important;
  border-color: #2e2e2e !important;
  color: #f5f5f5 !important;
}
html[data-theme="dark"] #win-billing .tv-pack-card,
body.tc-dark #win-billing .tv-pack-card {
  background: #171717 !important;
  border: 1px solid #2e2e2e !important;
  color: #f5f5f5 !important;
}
html[data-theme="dark"] #win-billing .tv-pack-card--featured,
body.tc-dark #win-billing .tv-pack-card--featured,
html[data-theme="dark"] #win-billing .tv-pack-card[data-pack-id="pack_500"],
body.tc-dark #win-billing .tv-pack-card[data-pack-id="pack_500"] {
  background: #171717 !important;
  border: 1.5px solid #ffffff !important;
  box-shadow: none !important;
}
html[data-theme="dark"] #win-billing .tv-pill,
body.tc-dark #win-billing .tv-pill {
  background: #1a1a1a;
  color: #f5f5f5;
  border-color: #2e2e2e;
}
html[data-theme="dark"] #win-billing .tv-pill:hover,
body.tc-dark #win-billing .tv-pill:hover {
  background: #ffffff !important;
  color: #000000 !important;
  border-color: #ffffff !important;
}
html[data-theme="dark"] #win-billing .tv-pill--solid,
body.tc-dark #win-billing .tv-pill--solid,
html[data-theme="dark"] #win-billing .tv-pack-card--featured .tv-pill,
body.tc-dark #win-billing .tv-pack-card--featured .tv-pill,
html[data-theme="dark"] #win-billing #watchAdBtn,
body.tc-dark #win-billing #watchAdBtn,
html[data-theme="dark"] #win-billing #adSponsorCtaBtn,
body.tc-dark #win-billing #adSponsorCtaBtn,
html[data-theme="dark"] #win-billing .tv-badge--ink,
body.tc-dark #win-billing .tv-badge--ink {
  background: #ffffff !important;
  color: #000000 !important;
  border-color: #ffffff !important;
}
html[data-theme="dark"] #win-billing .tv-ad-player-box,
body.tc-dark #win-billing .tv-ad-player-box,
html[data-theme="dark"] #win-billing #adVideoContainer,
body.tc-dark #win-billing #adVideoContainer,
html[data-theme="dark"] #win-billing .tv-ad-video-stage,
body.tc-dark #win-billing .tv-ad-video-stage,
html[data-theme="dark"] #win-billing #adVideoPlayer,
body.tc-dark #win-billing #adVideoPlayer,
html[data-theme="dark"] #win-billing .tv-ledger-wrap,
body.tc-dark #win-billing .tv-ledger-wrap {
  background: #000000 !important;
  color: #f5f5f5 !important;
  border: 1.5px solid #ffffff !important;
}
html[data-theme="dark"] #win-billing .tv-ad-overlay,
body.tc-dark #win-billing .tv-ad-overlay {
  background: #0c0c0c !important;
  color: #f5f5f5 !important;
  border: 1px solid #ffffff !important;
}
html[data-theme="dark"] #win-billing .tv-ledger-table th,
body.tc-dark #win-billing .tv-ledger-table th {
  background: #0c0c0c !important;
  color: #a3a3a3 !important;
  border-bottom: 1px solid #2e2e2e !important;
}
html[data-theme="dark"] #win-billing .tv-ledger-table td,
body.tc-dark #win-billing .tv-ledger-table td {
  background: #000000 !important;
  color: #f5f5f5 !important;
  border-bottom: 1px solid #2e2e2e !important;
}
html[data-theme="dark"] #win-billing .tv-ledger-table tbody tr:hover td,
body.tc-dark #win-billing .tv-ledger-table tbody tr:hover td {
  background: #151515 !important;
}
html[data-theme="dark"] #win-billing .tv-cap-track,
body.tc-dark #win-billing .tv-cap-track,
html[data-theme="dark"] #win-billing .tv-ad-progress-track,
body.tc-dark #win-billing .tv-ad-progress-track {
  background: #0c0c0c !important;
  border-color: #2e2e2e !important;
}
html[data-theme="dark"] #win-billing .tv-cap-fill,
body.tc-dark #win-billing .tv-cap-fill,
html[data-theme="dark"] #win-billing .tv-ad-progress-fill,
body.tc-dark #win-billing .tv-ad-progress-fill,
html[data-theme="dark"] #win-billing .tv-dot,
body.tc-dark #win-billing .tv-dot {
  background: #ffffff !important;
}
"""


def _render_stripe_pack_cards() -> str:
    """Render the 3 Stripe credit packs directly from TOKEN_PACK_CATALOG."""
    cards = []
    for pack_id in ("pack_100", "pack_500", "pack_2000"):
        pack: Dict[str, Any] = TOKEN_PACK_CATALOG[pack_id]
        price_usd = float(pack["price_usd"])
        credits = int(pack["credits"])
        bonus_pct = int(pack["bonus_pct"])
        featured = bool(pack["featured"])
        card_cls = "tv-pack-card tv-pack-card--featured" if featured else "tv-pack-card"
        btn_cls = "tv-pill tv-pill--solid tv-pill--full" if featured else "tv-pill tv-pill--full"
        bonus_str = f" · +{bonus_pct}%" if bonus_pct > 0 else ""
        credits_line = f"{credits:,} Credits{bonus_str}"
        cards.append(
            f"""              <div class="{card_cls}" data-pack-id="{_html.escape(pack_id, quote=True)}">
                <div>
                  <div class="tv-pack-tier">{_html.escape(str(pack["badge"]))}</div>
                  <div class="tv-pack-price">${price_usd:.2f}</div>
                  <div class="tv-pack-credits">{_html.escape(credits_line)}</div>
                  <div class="tv-pack-desc">{_html.escape(str(pack["tagline"]))}</div>
                </div>
                <button type="button" class="{btn_cls}" onclick="buyTokens({price_usd:.2f}, {credits})">{_html.escape(str(pack["cta_label"]))}</button>
              </div>"""
        )
    return "\n".join(cards)


def _render_rate_card_items() -> str:
    """Render Service Rate Card entries directly from SERVICE_RATE_CARD."""
    items = []
    for entry in SERVICE_RATE_CARD:
        items.append(
            f"""                <div class="tv-rate-item" data-rate-id="{_html.escape(str(entry["id"]), quote=True)}">
                  <span class="tv-rate-name"><span class="tv-dot" aria-hidden="true"></span><span>{_html.escape(str(entry["service"]))}</span></span>
                  <span class="tv-rate-val">{_html.escape(str(entry["rate_label"]))}</span>
                </div>"""
        )
    return "\n".join(items)


def render_token_vault_window_html() -> str:
    """Return the complete Aeonik Celadon & Ink ``#win-billing`` Token Vault window."""
    pack_cards = _render_stripe_pack_cards()
    rate_items = _render_rate_card_items()
    default_payout = DEFAULT_AD_PAYOUT_USD
    default_cost = DEFAULT_AD_COMPUTE_COST_USD
    default_margin_pct = round(((default_payout - default_cost) / default_payout) * 100.0)
    default_reward_cr = DEFAULT_AD_REWARD_TOKENS

    return f"""<div id="win-billing" class="mesh-window w-[960px] max-w-full" data-zen-window="true" data-window-id="win-billing" style="top: 84px; left: 110px; z-index: 26;">
      {TOKEN_VAULT_TITLEBAR}
      <div class="window-body tv-body aeonik-scope" data-tv-root="true">
        <!-- Telemetry Header Bar -->
        <div class="tv-subbar">
          <div class="tv-subbar-group">
            <span id="tvRoleBadge" class="tv-badge tv-badge--ink">PERSONAL WALLET</span>
            <span id="tvRateBasisText" class="tv-mono-xs tv-muted">NanoGPT + OpenRouter credits · Local Ollama always 0 CR</span>
          </div>
          <div class="tv-subbar-group">
            <button type="button" id="tvPreviewUserBtn" class="hidden tv-pill tv-pill--sm" onclick="window.TinCanTokenVault && window.TinCanTokenVault.toggleUserPreview()">Preview as User</button>
            <button type="button" id="tvOpenAdminTreasuryBtn" class="hidden tv-pill tv-pill--solid tv-pill--sm" onclick="toggleWindow('win-admin-treasury'); window.TinCanAdminTreasury && window.TinCanAdminTreasury.refresh()">Admin Treasury →</button>
            <button type="button" id="tvExportCsvBtn" class="tv-pill tv-pill--sm" onclick="window.TinCanTokenVault && window.TinCanTokenVault.exportCsv()">Export Receipts</button>
            <button type="button" id="tvRefreshBtn" class="tv-pill tv-pill--sm" onclick="refreshBillingWindow()">↻ Refresh</button>
          </div>
        </div>

        <!-- 4-KPI Unit Economics Row -->
        <div class="tv-kpi-grid">
          <div class="tv-kpi-card">
            <span class="tv-kpi-label">Credit Pool Balance</span>
            <div class="tv-kpi-row">
              <span id="billingWindowTokens" class="tv-kpi-val">10</span>
              <span class="tv-kpi-unit">CR</span>
            </div>
            <div class="tv-kpi-sub"><span id="billingWindowCredits">$0.10 USD</span> · fixed margin</div>
          </div>

          <div class="tv-kpi-card">
            <span class="tv-kpi-label">Local Zero-Burn Saved</span>
            <div class="tv-kpi-row">
              <span id="tvLocalSavedUsd" class="tv-kpi-val tv-kpi-val--pos">$0.00</span>
            </div>
            <div id="tvLocalTurnsSub" class="tv-kpi-sub">0 local turns @ $0.00</div>
          </div>

          <div class="tv-kpi-card">
            <span class="tv-kpi-label">Sponsor Ad Arbitrage</span>
            <div class="tv-kpi-row">
              <span id="tvAdArbitrageVal" class="tv-kpi-val tv-kpi-val--pos">+{default_reward_cr * 5:,} CR/day</span>
            </div>
            <div id="tvAdArbitrageSub" class="tv-kpi-sub">5 ads × {default_reward_cr:,} CR · {default_margin_pct}% net margin</div>
          </div>

          <div class="tv-kpi-card">
            <span class="tv-kpi-label">Unit Economics</span>
            <div class="tv-kpi-row">
              <span id="tvUnitEconVal" class="tv-kpi-val">1.25x Markup</span>
            </div>
            <div id="tvUnitEconSub" class="tv-kpi-sub">Billed by cost_usd (no 1:1 burn)</div>
          </div>
        </div>

        <!-- Operator Credit Margin Dial (Admin-only visibility) -->
        <section id="tvMarginDialBar" class="tv-dial-bar hidden" aria-label="Credit Margin Dial">
          <div class="tv-subbar-group">
            <span class="tv-sec-title">Credit Margin Dial</span>
            <span id="tvMarginDialReadout" class="tv-badge tv-badge--pos">1.25x · 20.0% gross margin</span>
          </div>
          <div class="tv-dial-controls">
            <input id="tvMarginDialSlider" class="tv-dial-slider" type="range" min="1.00" max="2.00" step="0.01" value="1.25" aria-label="Credit markup multiplier" oninput="window.TinCanTokenVault && window.TinCanTokenVault.previewMarginDial(this.value)" />
            <div class="tv-dial-presets">
              <button type="button" class="tv-pill tv-pill--sm" onclick="window.TinCanTokenVault && window.TinCanTokenVault.setMarginPreset(1.00)">1.00x (0%)</button>
              <button type="button" class="tv-pill tv-pill--sm" onclick="window.TinCanTokenVault && window.TinCanTokenVault.setMarginPreset(1.25)">1.25x (20%)</button>
              <button type="button" class="tv-pill tv-pill--sm" onclick="window.TinCanTokenVault && window.TinCanTokenVault.setMarginPreset(1.30)">1.30x (23%)</button>
              <button type="button" class="tv-pill tv-pill--sm" onclick="window.TinCanTokenVault && window.TinCanTokenVault.setMarginPreset(1.43)">1.43x (30%)</button>
            </div>
            <button type="button" id="tvMarginDialApplyBtn" class="tv-pill tv-pill--solid tv-pill--sm" onclick="window.TinCanTokenVault && window.TinCanTokenVault.applyMarginDial()">Apply</button>
          </div>
        </section>

        <!-- Middle 2-Column Layout: Stripe Packs + Rate Card | Sponsor Compute Subsidy -->
        <div class="tv-main-grid">
          <div class="tv-col">
            <!-- Stripe Credit Packs & Tier Rates -->
            <section class="tv-panel tv-panel--celadon" aria-label="Stripe Credit Packs">
              <div class="tv-sec-head">
                <span class="tv-sec-title">Stripe Credit Packs &amp; Tier Rates</span>
                <span class="tv-mono-xs tv-muted">Server-signed Stripe webhook credit</span>
              </div>
              <div class="tv-pack-grid">
{pack_cards}
              </div>
            </section>

            <!-- Service Rate Card -->
            <section id="tvRateCardSection" class="tv-panel" aria-label="Service Rate Card">
              <div class="tv-sec-head">
                <span class="tv-sec-title">Service Rate Card (Transparent Margin Routing)</span>
                <span class="tv-mono-xs tv-muted">Local BYOK = 0 CR</span>
              </div>
              <div id="tvRateCardGrid" class="tv-rate-grid">
{rate_items}
              </div>
            </section>
          </div>

          <!-- Right Column: Sponsor Video Compute Subsidy -->
          <div class="tv-col">
            <section class="tv-panel" aria-label="Sponsor Video Compute Subsidy">
              <div class="tv-sec-head">
                <span class="tv-sec-title">Sponsor Video Compute Subsidy</span>
                <button type="button" onclick="fetchNextSponsor()" title="Rotate to next sponsor" class="tv-pill tv-pill--sm">⟳ Next Sponsor</button>
              </div>

              <div id="sponsorAdContainer" class="tv-sponsor-box">
                <div class="tv-sponsor-lead">
                  <div id="adSponsorIcon" class="tv-sponsor-icon" aria-hidden="true">▲</div>
                  <div class="min-w-0 flex-1">
                    <div class="tv-subbar-group">
                      <span id="adSponsorName" class="tv-sponsor-name tv-truncate">Vercel AI SDK &amp; MicroVMs</span>
                      <span id="adSponsorBadge" class="tv-badge">Sponsored</span>
                    </div>
                    <div id="adSponsorTagline" class="tv-sponsor-tag">Deploy durable agent sandboxes and AI gateways with zero server management.</div>
                  </div>
                </div>
                <a id="adSponsorCtaBtn" href="https://sdk.vercel.ai?utm_source=tincan-mesh" target="_blank" rel="noopener noreferrer" onclick="trackSponsorClick()" class="tv-pill tv-pill--sm shrink-0">Visit Partner ↗</a>
              </div>

              <div class="tv-cap-wrap">
                <div class="tv-cap-track" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" aria-labelledby="tokenAdCapLabel">
                  <div id="tokenAdCapBar" class="tv-cap-fill" style="width: 0%;"></div>
                </div>
                <div id="tokenAdCapLabel" class="tv-cap-label">DAILY AD CAP: 0 / 5 VIEWS COMPLETED (+0 CR EARNED TODAY)</div>
              </div>

              <div class="tv-arb-box">
                <div class="tv-sec-title">Relay Ad Arbitrage Math</div>
                <div class="tv-arb-row">
                  <span>+ Sponsor payout per 10s verified view</span>
                  <span id="tvArbPayout" class="tv-pos">${default_payout:.4f} (+{default_reward_cr:,} CR)</span>
                </div>
                <div class="tv-arb-row">
                  <span>- Avg open-weight compute cost</span>
                  <span id="tvArbCost" class="tv-muted">${default_cost:.4f} ({default_margin_pct}% net margin)</span>
                </div>
              </div>

              <button id="watchAdBtn" type="button" onclick="watchSponsoredAd()" class="tv-pill tv-pill--solid tv-pill--full">▶ Watch 10s Sponsor Clip (+{default_reward_cr:,} CR)</button>

              <!-- Active Video Player Box -->
              <div id="adVideoContainer" class="hidden tv-ad-player-box">
                <div class="tv-ad-video-stage">
                  <video id="adVideoPlayer" playsinline preload="auto" class="tv-ad-video"></video>
                  <div class="tv-ad-overlay">Sponsor Clip: <span id="adVideoTitle">Partner Ad</span></div>
                </div>
                <div id="adProgressWrap" class="tv-ad-progress-wrap">
                  <div class="tv-ad-progress-meta">
                    <span id="adProgressText">Streaming verified sponsor video...</span>
                    <span id="adTimerText">10s remaining</span>
                  </div>
                  <div class="tv-ad-progress-track">
                    <div id="adProgressBar" class="tv-ad-progress-fill" style="width: 0%;"></div>
                  </div>
                </div>
              </div>

              <div class="tv-sponsor-foot">
                <span>Direct Partner Ads · EthicalAds · AdSense · Community</span>
                <div class="tv-subbar-group">
                  <button type="button" onclick="openSponsorInfoModal()" class="tv-link-btn">How to Advertise ℹ</button>
                  <button type="button" id="billingAdminSponsorBtn" onclick="openAdminSponsorStudio()" class="hidden tv-pill tv-pill--sm">Admin Studio</button>
                </div>
              </div>
            </section>
          </div>
        </div>

        <!-- Token & Margin Ledger -->
        <section class="tv-panel" aria-label="Token and Margin Ledger">
          <div class="tv-sec-head">
            <span class="tv-sec-title">Token &amp; Margin Ledger (Audit Trail)</span>
            <span id="billingTotalUsedText" class="tv-mono-xs tv-muted">Total used: 0 tokens ($0.0000)</span>
          </div>
          <div class="tv-ledger-wrap">
            <table class="tv-ledger-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Workflow</th>
                  <th>Gateway</th>
                  <th class="tv-num">Tokens</th>
                  <th class="tv-num">Upstream</th>
                  <th class="tv-num">Credits_Net</th>
                  <th class="tv-num">Margin</th>
                </tr>
              </thead>
              <tbody id="billingLedgerRows">
                <tr><td colspan="7" class="tv-cell-muted" style="text-align:center;padding:12px;">No token deductions or gateway routes recorded yet.</td></tr>
              </tbody>
            </table>
          </div>
        </section>

        <!-- Compact Aeonik Hyper3D Rodin + NanoGPT + World Labs Atlas v2 Pool Strip -->
        <section class="tv-rodin-strip" aria-label="Hyper3D Rodin, NanoGPT, and World Labs Atlas v2 Compute Pools">
          <div class="tv-sec-head">
            <div class="tv-subbar-group">
              <span class="tv-sec-title">Hyper3D Rodin &amp; NanoGPT Compute Pools · World Labs Atlas v2</span>
              <span id="rodinBillingStatusBadge" class="tv-badge tv-badge--pos">ONLINE / POOLED</span>
              <span id="tvAtlasBillingStatusBadge" class="tv-badge tv-badge--pos">WLT_API_KEY · 1,000 CR = $1.00</span>
            </div>
            <div class="tv-subbar-group">
              <button type="button" class="tv-pill tv-pill--sm" onclick="toggleWindow('win-workstation')">Open 3D Studio Controls →</button>
              <button type="button" class="tv-pill tv-pill--sm" onclick="toggleWindow('win-agentspace')">Open Workstation →</button>
            </div>
          </div>
          <div class="tv-rodin-metrics">
            <div class="tv-rodin-stat">
              <span class="tv-rodin-k">Rodin Credits</span>
              <span id="rodinBalanceCredits" class="tv-rodin-v">100.0</span>
            </div>
            <div class="tv-rodin-stat">
              <span class="tv-rodin-k">USD Balance</span>
              <span id="rodinBalanceUsd" class="tv-rodin-v tv-pos">$50.00</span>
            </div>
            <div class="tv-rodin-stat">
              <span class="tv-rodin-k">NanoGPT Pool</span>
              <span id="tvNanoPoolVal" class="tv-rodin-v">-- TEE</span>
              <span id="tvNanoPoolSub" class="tv-mono-xs tv-muted">Checking catalog…</span>
            </div>
            <div class="tv-rodin-stat" id="tvAtlasPoolCard">
              <span class="tv-rodin-k">World Labs Atlas v2</span>
              <span id="tvAtlasPoolVal" class="tv-rodin-v tv-pos">1,000 CR = $1.00</span>
              <span id="tvAtlasPoolSub" class="tv-mono-xs tv-muted">WLT_API_KEY · RUB RGBD + 2.0M .SPZ</span>
            </div>
            <div class="tv-rodin-stat">
              <span class="tv-rodin-k">Session 3D Tasks</span>
              <span id="rodinSessionTasks" class="tv-rodin-v">0</span>
            </div>
            <div class="tv-rodin-stat">
              <span class="tv-rodin-k">Active Key</span>
              <span id="rodinKeyLabel" class="tv-rodin-v tv-truncate" title="pooled-rodin">pooled-rodin</span>
            </div>
          </div>
          <div class="tv-mono-xs tv-muted">Tier Pricing: Sketch ($0.25) · Regular ($0.50) · Smooth ($0.75) · Detail ($1.00) · World Labs Atlas v2 (WLT_API_KEY · 1,000 CR = $1.00 · Pose RGBD $0.05 · 24fps Path $0.25 · Splat + GLB $0.50)</div>
        </section>

        <!-- Footer Bar -->
        <div class="tv-footer-bar">
          <span>stripe webhook verified · sponsor ad cap <span id="tvFooterAdCap">0/5</span> · ledger integrity ok</span>
          <span>[r] refresh · [w] watch 10s ad · [e] export csv · TinCan Mesh OS 2.2</span>
        </div>
      </div>
    </div>"""


TOKEN_VAULT_JS = r"""
    /* tc-token-vault-js */
    // =========================================================================
    // Token Vault & Sponsor Arbitrage UI (token_vault_ui.py)
    // =========================================================================
    window.TinCanTokenVault = (function () {
      const state = {
        lastSummary: null,
        ledgerRows: [],
        previewAsUser: false,
      };

      const el = (id) => (typeof document !== 'undefined' ? document.getElementById(id) : null);
      const esc = (v) => String(v == null ? '' : v).replace(/[&<>"']/g, (c) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
      }[c]));
      const getPeerId = () => {
        if (typeof myPeerId !== 'undefined' && myPeerId) return myPeerId;
        try {
          if (typeof localStorage !== 'undefined' && localStorage) {
            return localStorage.getItem('tincan_peer_id') || '';
          }
        } catch (e) {}
        return '';
      };

      function fmtTime(ts) {
        if (!ts) return '--:--:--';
        const d = new Date(Number(ts) * 1000);
        if (Number.isNaN(d.getTime())) return '--:--:--';
        return [d.getHours(), d.getMinutes(), d.getSeconds()]
          .map((n) => String(n).padStart(2, '0'))
          .join(':');
      }

      function renderLedgerRows(rows) {
        const tbody = el('billingLedgerRows');
        const list = Array.isArray(rows) ? rows : [];
        state.ledgerRows = list;
        if (!tbody) return;
        if (!list.length) {
          tbody.innerHTML = '<tr><td colspan="7" class="tv-cell-muted" style="text-align:center;padding:12px;">No token deductions or gateway routes recorded yet.</td></tr>';
          return;
        }
        tbody.innerHTML = list.map((row) => {
          const timeLabel = row.time_label || fmtTime(row.timestamp);
          const workflow = row.workflow || (row.kind ? `gateway ${row.kind}` : 'gateway chat');
          const gateway = row.gateway || row.model || 'gateway';
          const tokens = Number(row.tokens != null ? row.tokens : (row.total_tokens || 0));
          const upstream = Number(row.upstream_usd != null ? row.upstream_usd : (row.cost_usd || 0));
          const creditsNet = row.credits_net != null ? Number(row.credits_net) : (upstream === 0 && tokens === 0 ? 0 : -tokens);
          const creditsStr = creditsNet > 0 ? `+${creditsNet.toLocaleString()} CR` : (creditsNet < 0 ? `${creditsNet.toLocaleString()} CR` : '0 CR');
          const marginLabel = row.margin_label || (upstream === 0 ? 'LOCAL FREE' : `+$${(upstream * 0.25).toFixed(4)}`);
          const creditCls = creditsNet > 0 ? 'tv-cell-pos' : (creditsNet < 0 ? 'tv-cell-danger' : 'tv-cell-muted');
          const marginCls = String(marginLabel).indexOf('+') !== -1 || marginLabel === 'LOCAL FREE' ? 'tv-cell-pos' : 'tv-cell-muted';
          return (
            `<tr>` +
              `<td class="tv-cell-muted">${esc(timeLabel)}</td>` +
              `<td>${esc(workflow)}</td>` +
              `<td class="tv-cell-muted">${esc(gateway)}</td>` +
              `<td class="tv-num">${tokens.toLocaleString()}</td>` +
              `<td class="tv-num">$${upstream.toFixed(4)}</td>` +
              `<td class="tv-num ${creditCls}">${esc(creditsStr)}</td>` +
              `<td class="tv-num ${marginCls}">${esc(marginLabel)}</td>` +
            `</tr>`
          );
        }).join('');
      }

      function renderRateCard(rateCard) {
        const grid = el('tvRateCardGrid');
        if (!grid || !Array.isArray(rateCard) || !rateCard.length) return;
        grid.innerHTML = rateCard.map((item) => (
          `<div class="tv-rate-item" data-rate-id="${esc(item.id || '')}">` +
            `<span class="tv-rate-name"><span class="tv-dot" aria-hidden="true"></span><span>${esc(item.service || '')}</span></span>` +
            `<span class="tv-rate-val">${esc(item.rate_label || '')}</span>` +
          `</div>`
        )).join('');
      }

      function renderRodin(rodin) {
        if (!rodin || typeof rodin !== 'object') return;
        const badge = el('rodinBillingStatusBadge');
        const creds = el('rodinBalanceCredits');
        const usd = el('rodinBalanceUsd');
        const tasks = el('rodinSessionTasks');
        const keyLbl = el('rodinKeyLabel');
        const connected = Boolean(rodin.connected);
        if (badge) {
          badge.textContent = connected ? 'ONLINE / POOLED' : 'SIMULATED / ACTIVE';
          badge.className = connected ? 'tv-badge tv-badge--pos' : 'tv-badge';
        }
        if (creds) creds.textContent = Number(rodin.account_remaining_credits || 0).toFixed(1);
        if (usd) usd.textContent = '$' + Number(rodin.account_remaining_balance_usd || 0).toFixed(2);
        if (tasks) tasks.textContent = String(Number(rodin.session_total_tasks || 0));
        if (keyLbl) {
          const lbl = rodin.key_label || 'pooled-rodin';
          keyLbl.textContent = lbl;
          keyLbl.title = lbl;
        }
      }

      function applySponsorView(sponsor) {
        if (!sponsor || typeof sponsor !== 'object') return;
        const nameEl = el('adSponsorName');
        const tagEl = el('adSponsorTagline');
        const badgeEl = el('adSponsorBadge');
        const iconEl = el('adSponsorIcon');
        const ctaBtn = el('adSponsorCtaBtn');
        const titleEl = el('adVideoTitle');
        if (nameEl) nameEl.innerText = sponsor.name || 'Developer Sponsor';
        if (tagEl) tagEl.innerText = sponsor.tagline || 'Fund free mesh AI compute.';
        if (badgeEl) badgeEl.innerText = sponsor.badge || 'Sponsored';
        if (iconEl) iconEl.innerText = sponsor.icon || '▲';
        if (titleEl) titleEl.innerText = sponsor.name || 'Sponsor Ad';
        if (ctaBtn) {
          ctaBtn.href = sponsor.url || '#';
          ctaBtn.innerText = sponsor.cta || 'Visit Partner ↗';
        }
      }

      function renderSummary(summary) {
        if (!summary || typeof summary !== 'object') return;
        state.lastSummary = summary;

        const credits = Number(summary.credits_balance != null ? summary.credits_balance : (summary.token_balance || 0));
        const balUsd = Number(summary.balance_usd != null ? summary.balance_usd : (summary.credit_balance_usd || 0));
        const usedTok = Number(summary.total_tokens_used || 0);
        const billedUsd = Number(summary.total_billed_usd || 0);
        const localTurns = Number(summary.local_turns || 0);
        const localSaved = Number(summary.local_usd_saved || 0);
        const cap = Math.max(0, Number(summary.daily_ad_cap != null ? summary.daily_ad_cap : 5));
        const views = Math.min(Math.max(0, Number(summary.ad_views_today || 0)), cap);
        const capPct = cap > 0 ? Math.min(100, Math.max(0, (views / cap) * 100)) : 0;
        const payout = Number(summary.ad_payout_usd != null ? summary.ad_payout_usd : 0.05);
        const compCost = Number(summary.ad_compute_cost_usd != null ? summary.ad_compute_cost_usd : 0.002);
        const marginPct = Number(summary.ad_margin_pct != null ? summary.ad_margin_pct : 96);
        const rewardCr = Number(summary.ad_reward_tokens != null ? summary.ad_reward_tokens : 5000);
        const earnedCr = Number(summary.ad_earned_today_tokens != null ? summary.ad_earned_today_tokens : (views * rewardCr));
        const maxDayCr = Number(summary.ad_daily_max_tokens != null ? summary.ad_daily_max_tokens : (cap * rewardCr));
        const markup = Number(summary.markup_multiplier || 1.25);

        const tokEl = el('billingWindowTokens');
        const credEl = el('billingWindowCredits');
        const usedEl = el('billingTotalUsedText');
        if (tokEl) tokEl.innerText = credits.toLocaleString();
        if (credEl) credEl.innerText = `$${balUsd.toFixed(2)} USD`;
        if (usedEl) usedEl.innerText = `Total used: ${usedTok.toLocaleString()} tokens ($${billedUsd.toFixed(4)})`;

        const pill = el('hudTokenPill');
        if (pill) {
          pill.innerText = credits >= 1000 ? `${Math.round(credits / 1000)}k 🪙` : `${credits} 🪙`;
        }

        const localUsdEl = el('tvLocalSavedUsd');
        const localSubEl = el('tvLocalTurnsSub');
        if (localUsdEl) localUsdEl.innerText = `$${localSaved.toFixed(2)}`;
        if (localSubEl) localSubEl.innerText = `${localTurns.toLocaleString()} local turns @ $0.00`;

        const arbValEl = el('tvAdArbitrageVal');
        const arbSubEl = el('tvAdArbitrageSub');
        if (arbValEl) arbValEl.innerText = `+${maxDayCr.toLocaleString()} CR/day`;
        if (arbSubEl) arbSubEl.innerText = `${cap} ads × ${rewardCr.toLocaleString()} CR · ${Math.round(marginPct)}% net margin`;

        const isAdmin = Boolean(summary.is_admin || String(summary.role_tier || '').toLowerCase() === 'admin');
        const canOpenTreasury = Boolean(summary.can_open_admin_treasury || isAdmin || summary.peer_id);
        const showAdminChrome = canOpenTreasury && !state.previewAsUser;
        const roleTier = String(summary.role_tier || 'free').toUpperCase();
        const roleBadge = el('tvRoleBadge');
        if (roleBadge) {
          roleBadge.textContent = state.previewAsUser
            ? 'PERSONAL WALLET · USER PREVIEW'
            : (isAdmin ? 'PERSONAL WALLET · ADMIN' : `PERSONAL WALLET · ${roleTier}`);
        }
        const previewBtn = el('tvPreviewUserBtn');
        if (previewBtn) {
          if (previewBtn.classList) previewBtn.classList.toggle('hidden', !canOpenTreasury);
          previewBtn.textContent = state.previewAsUser ? '← Back to Admin' : 'Preview as User';
        }
        const adminBtn = el('tvOpenAdminTreasuryBtn');
        if (adminBtn && adminBtn.classList) {
          adminBtn.classList.toggle('hidden', !showAdminChrome);
        }
        const dialBar = el('tvMarginDialBar');
        if (dialBar && dialBar.classList) {
          dialBar.classList.toggle('hidden', !showAdminChrome);
        }

        const econValEl = el('tvUnitEconVal');
        const econSubEl = el('tvUnitEconSub');
        const grossMarginPct = summary.gross_margin_pct != null
          ? Number(summary.gross_margin_pct)
          : (markup > 1 ? ((markup - 1) / markup) * 100 : 0);
        if (econValEl) econValEl.innerText = `${markup.toFixed(2)}x Markup`;
        if (econSubEl) econSubEl.innerText = `${grossMarginPct.toFixed(1)}% gross margin · billed by ${summary.billing_mode || 'cost_usd'}`;
        previewMarginDial(markup);

        const capBar = el('tokenAdCapBar');
        const capLbl = el('tokenAdCapLabel');
        const footCap = el('tvFooterAdCap');
        if (capBar) capBar.style.width = `${capPct.toFixed(1)}%`;
        if (capLbl) capLbl.innerText = `DAILY AD CAP: ${views} / ${cap} VIEWS COMPLETED (+${earnedCr.toLocaleString()} CR EARNED TODAY)`;
        if (footCap) footCap.innerText = `${views}/${cap}`;

        const arbPayoutEl = el('tvArbPayout');
        const arbCostEl = el('tvArbCost');
        const watchBtn = el('watchAdBtn');
        if (arbPayoutEl) arbPayoutEl.innerText = `$${payout.toFixed(4)} (+${rewardCr.toLocaleString()} CR)`;
        if (arbCostEl) arbCostEl.innerText = `$${compCost.toFixed(4)} (${Math.round(marginPct)}% net margin)`;
        if (watchBtn && !watchBtn.disabled) {
          watchBtn.innerText = `▶ Watch 10s Sponsor Clip (+${rewardCr.toLocaleString()} CR)`;
        }

        if (summary.active_sponsor) applySponsorView(summary.active_sponsor);
        if (Array.isArray(summary.rate_card)) renderRateCard(summary.rate_card);
        renderLedgerRows(summary.ledger_rows || summary.recent_invoices || []);
        if (summary.rodin) renderRodin(summary.rodin);
      }

      async function fetchJsonSafe(url) {
        if (typeof fetch !== 'function') return null;
        try {
          const resp = await fetch(url);
          if (!resp || !resp.ok) return null;
          return await resp.json();
        } catch (e) {
          return null;
        }
      }

      async function refresh() {
        if (typeof fetch !== 'function') return state.lastSummary;
        const peerId = getPeerId();
        if (typeof loadActiveSponsor === 'function') {
          try { loadActiveSponsor(); } catch (e) {}
        }

        const q = peerId ? `?peer_id=${encodeURIComponent(peerId)}` : '';
        const [summary, wsStatus] = await Promise.all([
          fetchJsonSafe(`/api/tokens/summary${q}`),
          fetchJsonSafe('/api/workstation/status'),
        ]);
        if (wsStatus && wsStatus.nanogpt) {
          const nano = wsStatus.nanogpt;
          const nv = el('tvNanoPoolVal');
          const ns = el('tvNanoPoolSub');
          if (nv) nv.textContent = `${nano.tee_count ?? 0} TEE`;
          if (ns) ns.textContent = `+ ${nano.heretic_count ?? 0} Heretic · ${nano.total_count ?? 0} total`;
        }
        if (wsStatus && wsStatus.atlas) {
          const atlas = wsStatus.atlas;
          const av = el('tvAtlasPoolVal');
          const as = el('tvAtlasPoolSub');
          const ab = el('tvAtlasBillingStatusBadge');
          if (av) av.textContent = atlas.credits != null ? `${Number(atlas.credits).toLocaleString()} CR` : '1,000 CR = $1.00';
          if (as) as.textContent = `WLT_API_KEY · ${atlas.key_configured ? 'LIVE' : 'SIMULATED'} · 1,000 CR = $1.00`;
          if (ab) ab.textContent = `WLT_API_KEY · 1,000 CR = $1.00 (${atlas.key_configured ? 'LIVE' : 'READY'})`;
        }
        if (summary && typeof summary === 'object' && !summary.error) {
          renderSummary(summary);
          if (!summary.rodin) {
            const rodin = (wsStatus && wsStatus.rodin) || await fetchJsonSafe('/api/3d/balance');
            if (rodin) renderRodin(rodin);
          }
          return summary;
        }

        // Graceful fallback when /api/tokens/summary is unavailable
        const [billing, analytics, sponsorState, rodin] = await Promise.all([
          peerId ? fetchJsonSafe(`/api/account/billing?peer_id=${encodeURIComponent(peerId)}`) : Promise.resolve(null),
          fetchJsonSafe('/api/models/analytics'),
          fetchJsonSafe('/api/ads/state'),
          fetchJsonSafe('/api/3d/balance'),
        ]);

        const fallback = {
          credits_balance: billing ? (billing.token_balance || 0) : 0,
          balance_usd: billing ? (billing.credit_balance_usd || 0) : 0,
          total_tokens_used: billing ? (billing.total_tokens_used || 0) : 0,
          total_billed_usd: billing ? (billing.total_billed_usd || 0) : 0,
          local_turns: 0,
          local_usd_saved: 0,
          ad_views_today: 0,
          daily_ad_cap: 5,
          ad_payout_usd: 0.05,
          ad_compute_cost_usd: 0.002,
          ad_margin_pct: 96,
          ad_reward_tokens: (sponsorState && sponsorState.active_sponsor && sponsorState.active_sponsor.reward_tokens) || 5000,
          active_sponsor: sponsorState ? sponsorState.active_sponsor : null,
          ledger_rows: (billing && billing.recent_invoices) || (analytics && analytics.recent_routing_log) || [],
          rodin: rodin || (analytics && analytics.hyper3d) || null,
        };
        if (analytics && analytics.providers) {
          let turns = 0;
          Object.values(analytics.providers).forEach((p) => {
            if (!p) return;
            const gw = String(p.gateway || '').toLowerCase();
            if (gw === 'ollama' || gw === 'owlchat' || gw === 'trussed' || gw === 'local') {
              turns += Number(p.total_calls || 0);
            }
          });
          fallback.local_turns = turns;
          fallback.local_usd_saved = Number((turns * 0.0135).toFixed(2));
        }
        renderSummary(fallback);
        return fallback;
      }

      function exportCsv() {
        const header = ['time', 'workflow', 'gateway', 'tokens', 'upstream_usd', 'credits_net', 'margin'];
        const csvCell = (val) => `"${String(val == null ? '' : val).replace(/"/g, '""')}"`;
        const lines = [header.join(',')];
        (state.ledgerRows || []).forEach((r) => {
          lines.push([
            csvCell(r.time_label || fmtTime(r.timestamp)),
            csvCell(r.workflow || ''),
            csvCell(r.gateway || r.model || ''),
            Number(r.tokens != null ? r.tokens : (r.total_tokens || 0)),
            Number(r.upstream_usd != null ? r.upstream_usd : (r.cost_usd || 0)).toFixed(6),
            Number(r.credits_net || 0),
            csvCell(r.margin_label || ''),
          ].join(','));
        });
        const csvText = lines.join('\n') + '\n';
        try {
          if (typeof Blob === 'function' && typeof URL !== 'undefined' && typeof document !== 'undefined' && document.createElement) {
            const blob = new Blob([csvText], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'tincan-token-ledger.csv';
            if (document.body && document.body.appendChild) document.body.appendChild(a);
            if (typeof a.click === 'function') a.click();
            if (a.parentNode && a.parentNode.removeChild) a.parentNode.removeChild(a);
            setTimeout(() => { try { URL.revokeObjectURL(url); } catch (e) {} }, 500);
          }
        } catch (e) {}
        return csvText;
      }

      function previewMarginDial(rawVal) {
        const m = Math.max(1.0, Math.min(2.0, Number(rawVal || 1.25)));
        const gross = m > 1.0 ? ((m - 1.0) / m) * 100.0 : 0.0;
        const slider = el('tvMarginDialSlider');
        const readout = el('tvMarginDialReadout');
        if (slider && Math.abs(Number(slider.value) - m) > 0.001) {
          slider.value = m.toFixed(2);
        }
        if (readout) {
          readout.textContent = `${m.toFixed(2)}x · ${gross.toFixed(1)}% gross margin`;
        }
        return m;
      }

      async function setMarginPreset(mult) {
        previewMarginDial(mult);
        return applyMarginDial(mult);
      }

      async function applyMarginDial(explicitMult) {
        if (typeof fetch !== 'function') return null;
        const slider = el('tvMarginDialSlider');
        const target = previewMarginDial(explicitMult != null ? explicitMult : (slider ? slider.value : 1.25));
        const headers = { 'Content-Type': 'application/json' };
        try {
          if (typeof localStorage !== 'undefined' && localStorage) {
            const adminKey = localStorage.getItem('tincan_admin_key') || '';
            if (adminKey) headers['X-Admin-Key'] = adminKey;
          }
        } catch (e) {}
        const applyBtn = el('tvMarginDialApplyBtn');
        if (applyBtn) applyBtn.disabled = true;
        try {
          const resp = await fetch('/api/tokens/markup', {
            method: 'POST',
            headers,
            body: JSON.stringify({ markup_multiplier: target }),
          });
          const data = await resp.json().catch(() => ({}));
          if (resp.ok) {
            await refresh();
          } else if (data && data.error) {
            const readout = el('tvMarginDialReadout');
            if (readout) readout.textContent = data.error;
          }
          return data;
        } finally {
          if (applyBtn) applyBtn.disabled = false;
        }
      }

      function toggleUserPreview() {
        state.previewAsUser = !state.previewAsUser;
        if (state.lastSummary) {
          renderSummary(state.lastSummary);
        }
        return state.previewAsUser;
      }

      function init() {
        if (typeof window !== 'undefined') {
          window.refreshBillingWindow = refresh;
          if (typeof window.buyTokens !== 'function') {
            window.buyTokens = async function (amountUsd) {
              if (typeof fetch !== 'function') return;
              const pack = `pack_${Math.round(Number(amountUsd || 0) * 100)}`;
              const resp = await fetch('/api/billing/checkout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ peer_id: getPeerId(), pack }),
              });
              const data = await resp.json();
              if (resp.ok && data.checkout_url && typeof window.location !== 'undefined') {
                window.location.href = data.checkout_url;
              }
            };
          }
          if (typeof window.fetchNextSponsor !== 'function') {
            window.fetchNextSponsor = async function () {
              const d = await fetchJsonSafe('/api/ads/sponsor');
              if (d && d.sponsor) applySponsorView(d.sponsor);
            };
          }
          if (typeof window.trackSponsorClick !== 'function') {
            window.trackSponsorClick = function () {};
          }
          if (typeof window.openSponsorInfoModal !== 'function') {
            window.openSponsorInfoModal = function () {};
          }
          if (typeof window.openAdminSponsorStudio !== 'function') {
            window.openAdminSponsorStudio = function () {
              if (typeof window.toggleWindow === 'function') window.toggleWindow('win-moderator');
            };
          }
          if (typeof window.watchSponsoredAd !== 'function') {
            window.watchSponsoredAd = function () {};
          }
        }
      }

      init();
      return {
        version: 1,
        init,
        refresh,
        renderSummary,
        renderLedgerRows,
        exportCsv,
        previewMarginDial,
        setMarginPreset,
        applyMarginDial,
        toggleUserPreview,
      };
    })();
"""


def apply_token_vault_ui(html: str) -> str:
    """Inject Token Vault markup, Aeonik Celadon CSS, and JS into ``html`` idempotently."""
    if not isinstance(html, str):
        return html

    window_html = render_token_vault_window_html()

    if TOKEN_VAULT_CSS_SLOT in html:
        html = html.replace(TOKEN_VAULT_CSS_SLOT, TOKEN_VAULT_CSS, 1)
    elif "/* tc-token-vault-css */" not in html and "</head>" in html:
        head_idx = html.find("</head>")
        html = f"{html[:head_idx]}<style id=\"tcTokenVaultCss\">{TOKEN_VAULT_CSS}</style>\n{html[head_idx:]}"

    if TOKEN_VAULT_WINDOW_SLOT in html:
        html = html.replace(TOKEN_VAULT_WINDOW_SLOT, window_html, 1)

    if TOKEN_VAULT_JS_SLOT in html:
        html = html.replace(TOKEN_VAULT_JS_SLOT, TOKEN_VAULT_JS, 1)
    elif "/* tc-token-vault-js */" not in html and "</body>" in html:
        body_idx = html.rfind("</body>")
        html = f"{html[:body_idx]}<script id=\"tcTokenVaultJs\">{TOKEN_VAULT_JS}</script>\n{html[body_idx:]}"

    return html
