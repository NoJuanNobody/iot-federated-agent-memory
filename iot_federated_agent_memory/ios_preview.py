"""iOS Simulator and Wire Contract Bridge for TinCan 2.2.

Unites all 9 native iOS app design screens into a single interactive simulator
with live wire API actions, Zen CSS tokens, and dirty-gradient SVG filters.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, Tuple

IOS_SCREENS: Tuple[str, ...] = (
    "01-onboarding",
    "02-inbox",
    "03-thread",
    "04-verify",
    "05-arena",
    "06-call",
    "07-keys",
    "08-relay",
    "09-credits",
)

IOS_TABS: Tuple[str, ...] = (
    "inbox",
    "arena",
    "calls",
    "you",
)

_SCREEN_TITLES: Dict[str, str] = {
    "01-onboarding": "1. Onboarding",
    "02-inbox": "2. Inbox",
    "03-thread": "3. Thread",
    "04-verify": "4. Verify",
    "05-arena": "5. Arena",
    "06-call": "6. Call",
    "07-keys": "7. Keys & Devices",
    "08-relay": "8. Relay Settings",
    "09-credits": "9. Credits & Usage",
}


def get_ios_wire_contract() -> Dict[str, Any]:
    """Returns the structured wire contract specification for the TinCan 2.2 native iOS app."""
    return {
        "version": "2.2.0",
        "app_name": "TinCan Native iOS",
        "default_relay": "https://iot-federated-agent-memory-production.up.railway.app",
        "screens": list(IOS_SCREENS),
        "tabs": list(IOS_TABS),
        "wire_endpoints": [
            {
                "path": "/api/tincan/send",
                "method": "POST",
                "description": "Send NaCl-sealed envelope to recipient tc: address (to, from, box, sig).",
                "auth": "Ed25519 signature",
                "request_body": {
                    "to": "string (tc:... recipient address)",
                    "from": "string (tc:... sender address)",
                    "box": "string (base64-encoded encrypted payload)",
                    "sig": "string (base64-encoded Ed25519 signature)",
                },
                "response": {"status": "sent", "seq": "int", "timestamp": "float"},
            },
            {
                "path": "/api/tincan/inbox",
                "method": "GET",
                "description": "Fetch sealed ciphertext messages for an address. Short timeout=0 on iOS.",
                "query_params": {
                    "address": "string (tc:... address)",
                    "since_seq": "int (last known sequence number)",
                    "timeout": "float (0 for immediate poll on iOS)",
                },
                "response": {"messages": "list", "latest_seq": "int"},
            },
            {
                "path": "/api/tincan/whoami",
                "method": "GET",
                "description": "Retrieve active peer identity, public key, and tc: address.",
                "response": {
                    "address": "string (tc:...)",
                    "public_key": "string (hex)",
                    "alias": "string",
                },
            },
            {
                "path": "/api/mesh/arena/battle",
                "method": "POST",
                "description": "Dispatch a duel prompt to two AI models simultaneously.",
                "request_body": {
                    "prompt": "string",
                    "model_a": "string (optional model alias)",
                    "model_b": "string (optional model alias)",
                },
                "response": {
                    "status": "completed",
                    "model_a": {"alias": "string", "response": "string"},
                    "model_b": {"alias": "string", "response": "string"},
                },
            },
            {
                "path": "/api/mesh/arena/vote",
                "method": "POST",
                "description": "Cast vote for Model A or B duel winner and award XP.",
                "request_body": {
                    "peer_id": "string",
                    "winner_alias": "string",
                    "prompt_preview": "string",
                    "display_name": "string (optional)",
                },
                "response": {"status": "voted", "winner": "string", "xp_awarded": "int", "total_xp": "int"},
            },
            {
                "path": "/api/mesh/xp/award",
                "method": "POST",
                "description": "Award XP to peer for mesh activities and record flight.",
                "request_body": {
                    "peer_id": "string",
                    "action_key": "string",
                    "display_name": "string (optional)",
                },
                "response": {"status": "awarded", "award": "dict", "flight": "dict"},
            },
            {
                "path": "/api/webrtc/register",
                "method": "POST",
                "description": "Register peer session in WebRTC call room for audio/video/screenshare.",
                "request_body": {
                    "peer_id": "string",
                    "room": "string",
                    "display_name": "string",
                    "has_video": "bool",
                    "has_audio": "bool",
                    "has_screen": "bool",
                },
                "response": {"status": "registered", "peer_id": "string", "room": "string", "peers": "list"},
            },
            {
                "path": "/api/webrtc/signal",
                "method": "POST",
                "description": "Post WebRTC SDP offer/answer or ICE candidate to room peer.",
                "request_body": {
                    "from": "string",
                    "to": "string",
                    "signal": "dict (SDP / ICE)",
                    "room": "string",
                },
                "response": {"status": "signaled", "signal": "dict"},
            },
            {
                "path": "/api/webrtc/signals",
                "method": "GET",
                "description": "Poll incoming WebRTC signaling messages for a peer.",
                "query_params": {
                    "peer_id": "string",
                    "room": "string",
                    "since_seq": "int",
                },
                "response": {"signals": "list", "latest_seq": "int", "peers": "list"},
            },
            {
                "path": "/api/webrtc/leave",
                "method": "POST",
                "description": "Leave WebRTC room and clean up active signaling stream.",
                "request_body": {
                    "peer_id": "string",
                    "room": "string",
                },
                "response": {"status": "left", "peer_id": "string"},
            },
            {
                "path": "/api/account/billing",
                "method": "GET",
                "description": "Get account balance, usage, and billing ledger for peer.",
                "query_params": {"peer_id": "string"},
                "response": {
                    "balance_usd": "float",
                    "today_spend_usd": "float",
                    "month_spend_usd": "float",
                    "total_spend_usd": "float",
                    "rates": "dict",
                },
            },
            {
                "path": "/api/account/billing/topup",
                "method": "POST",
                "description": "Operator manual credit topup or StoreKit verified purchase credit.",
                "request_body": {
                    "peer_id": "string",
                    "amount_usd": "float",
                    "tx_hash": "string (optional StoreKit receipt token)",
                },
                "response": {"status": "topup_success", "account": "dict"},
            },
            {
                "path": "/api/version",
                "method": "GET",
                "description": "Relay API version and capabilities.",
                "response": {
                    "version": "2.2.0",
                    "service": "iot-federated-agent-memory",
                    "relay_url": "string",
                },
            },
        ],
    }


def _load_design_files(html_dir: str) -> Dict[str, str]:
    """Loads shared CSS and individual screen HTML documents from docs/designs/ios-app/html."""
    screens_raw: Dict[str, str] = {}
    for screen_name in IOS_SCREENS:
        filepath = os.path.join(html_dir, f"{screen_name}.html")
        if os.path.isfile(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                screens_raw[screen_name] = f.read()
        else:
            screens_raw[screen_name] = f"<div class='body'><p>Screen {screen_name} not found</p></div>"
    return screens_raw


def _extract_screen_ui(html_content: str) -> str:
    """Extracts the .ui element contents from a screen HTML file."""
    m = re.search(r'<div class="ui">(.*?)</div>\s*<div class="homebar"></div>\s*</div>\s*</body>', html_content, re.DOTALL)
    if m:
        ui_inner = m.group(1).strip()
        # Remove inner tabbar and duplicate homebar from the screen body since the simulator shell provides unified tabbar & switcher
        ui_inner = re.sub(r'<nav class="tabbar">.*?</nav>\s*<div class="homebar"></div>', '', ui_inner, flags=re.DOTALL)
        return ui_inner
    return html_content


def _extract_dirt_layer(html_content: str) -> str:
    """Extracts the .dirt element and its feTurbulence SVG filters."""
    m = re.search(r'(<div class="dirt"[^>]*>.*?</div>\s*<div class="vignette"[^>]*></div>)', html_content, re.DOTALL)
    if m:
        return m.group(1)
    return ""


def render_ios_simulator_html(initial_screen: str = "02-inbox", base_dir: str | None = None) -> str:
    """Renders the comprehensive 9-screen TinCan 2.2 interactive iOS simulator page."""
    if initial_screen not in IOS_SCREENS:
        initial_screen = "02-inbox"

    if base_dir is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "designs", "ios-app"))
    html_dir = os.path.join(base_dir, "html")

    # Read shared CSS
    shared_css_path = os.path.join(html_dir, "shared.css")
    shared_css = ""
    if os.path.isfile(shared_css_path):
        with open(shared_css_path, "r", encoding="utf-8") as f:
            shared_css = f.read()

    # Read all screens
    screens_raw = _load_design_files(html_dir)

    # Build screen frames
    screen_cards = []
    for screen_id in IOS_SCREENS:
        raw_doc = screens_raw.get(screen_id, "")
        dirt_layer = _extract_dirt_layer(raw_doc)
        ui_content = _extract_screen_ui(raw_doc)
        title = _SCREEN_TITLES.get(screen_id, screen_id)

        # Tab mapping
        tab_tag = "other"
        if screen_id in ("02-inbox", "03-thread", "04-verify"):
            tab_tag = "inbox"
        elif screen_id in ("05-arena",):
            tab_tag = "arena"
        elif screen_id in ("06-call",):
            tab_tag = "calls"
        elif screen_id in ("07-keys", "08-relay", "09-credits"):
            tab_tag = "you"

        screen_cards.append(f"""
        <div id="screen-{screen_id}" class="screen-container {'active' if screen_id == initial_screen else ''}" data-screen="{screen_id}" data-tab="{tab_tag}">
          {dirt_layer}
          <div class="vignette" aria-hidden="true"></div>
          <div class="ui">
            {ui_content}
          </div>
        </div>
        """)

    screens_html_bundle = "\n".join(screen_cards)

    # Rail switcher items
    rail_items = []
    for s_id in IOS_SCREENS:
        rail_title = _SCREEN_TITLES.get(s_id, s_id)
        rail_items.append(
            f'<button class="rail-btn {"active" if s_id == initial_screen else ""}" '
            f'data-target="{s_id}" onclick="switchScreen(\'{s_id}\')">{rail_title}</button>'
        )
    rail_html = "\n".join(rail_items)

    wire_spec = get_ios_wire_contract()
    import json
    wire_spec_json = json.dumps(wire_spec, indent=2)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TinCan 2.2 · Native iOS Interactive Simulator</title>
<style>
/* Embedded Zen CSS Tokens & Component Foundations */
{shared_css}

/* Studio & Interactive Simulator Harness Styling */
html, body {{
  width: 100%;
  height: 100%;
  overflow-x: hidden;
  overflow-y: auto;
  background: #090806;
  color: var(--washi);
  font-family: var(--gothic);
  margin: 0;
  padding: 0;
}}

.sim-workspace {{
  display: flex;
  flex-direction: row;
  min-height: 100vh;
  background:
    radial-gradient(ellipse 70% 50% at 20% 0%, rgba(208, 112, 63, 0.15), transparent 60%),
    radial-gradient(ellipse 60% 60% at 85% 90%, rgba(66, 82, 46, 0.22), transparent 50%),
    #090806;
}}

/* Left Navigation Rail */
.sim-rail {{
  width: 290px;
  background: rgba(14, 13, 11, 0.92);
  border-right: 1px solid var(--line);
  padding: 24px 18px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  backdrop-filter: blur(16px);
  z-index: 10;
}}

.sim-brand {{
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--line);
}}

.sim-brand h1 {{
  font-family: var(--mincho);
  font-size: 19px;
  font-weight: 600;
  color: var(--washi);
  margin: 0;
  letter-spacing: 0.02em;
}}

.sim-brand .tag {{
  font-size: 11px;
  font-family: var(--gothic);
  background: rgba(208, 112, 63, 0.18);
  color: var(--kaki);
  border: 1px solid rgba(208, 112, 63, 0.4);
  padding: 2px 7px;
  border-radius: 4px;
}}

.rail-section {{
  display: flex;
  flex-direction: column;
  gap: 8px;
}}

.rail-section-title {{
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--washi-3);
  margin-bottom: 4px;
  font-weight: 500;
}}

.rail-btn {{
  display: block;
  width: 100%;
  text-align: left;
  padding: 8px 12px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  color: var(--washi-2);
  font-size: 13.5px;
  cursor: pointer;
  transition: all 0.16s ease;
}}

.rail-btn:hover {{
  background: rgba(236, 230, 218, 0.05);
  color: var(--washi);
}}

.rail-btn.active {{
  background: rgba(208, 112, 63, 0.14);
  color: var(--washi);
  border-color: rgba(208, 112, 63, 0.45);
  font-weight: 500;
}}

/* Center Phone Stage */
.sim-stage {{
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 24px;
  min-height: 100vh;
}}

.phone-bezel {{
  position: relative;
  width: 402px;
  height: 856px;
  background: #020202;
  border-radius: 54px;
  padding: 6px;
  box-shadow:
    0 0 0 1px rgba(236, 230, 218, 0.15),
    0 24px 64px -12px rgba(0, 0, 0, 0.9),
    0 0 40px rgba(208, 112, 63, 0.12);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}}

.phone-inner {{
  position: relative;
  width: 390px;
  height: 844px;
  border-radius: 48px;
  overflow: hidden;
  background: var(--sumi);
}}

.screen-container {{
  position: absolute;
  inset: 0;
  display: none;
  opacity: 0;
  transition: opacity 0.22s ease-in-out;
  overflow: hidden;
}}

.screen-container.active {{
  display: block;
  opacity: 1;
}}

/* Unified Simulator Tab Bar */
.sim-tabbar {{
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: var(--tab);
  background: rgba(14, 13, 11, 0.95);
  border-top: 1px solid var(--line);
  backdrop-filter: blur(20px);
  display: flex;
  justify-content: space-around;
  padding-top: 10px;
  z-index: 50;
}}

.sim-tabbar .tab {{
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  color: var(--washi-3);
  font-size: 11px;
  cursor: pointer;
  transition: color 0.15s ease;
  user-select: none;
}}

.sim-tabbar .tab svg {{
  width: 24px;
  height: 24px;
}}

.sim-tabbar .tab:hover {{
  color: var(--washi);
}}

.sim-tabbar .tab.on {{
  color: var(--kaki);
}}

.phone-homebar {{
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  width: 140px;
  height: 5px;
  background: var(--washi);
  border-radius: 3px;
  opacity: 0.65;
  pointer-events: none;
  z-index: 60;
}}

/* Right Live Wire Console & Controls */
.sim-console {{
  width: 360px;
  background: rgba(14, 13, 11, 0.92);
  border-left: 1px solid var(--line);
  padding: 24px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  backdrop-filter: blur(16px);
  overflow-y: auto;
  max-height: 100vh;
}}

.console-card {{
  background: var(--sumi-2);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}}

.console-card h3 {{
  margin: 0;
  font-size: 13px;
  font-weight: 500;
  color: var(--washi);
  display: flex;
  align-items: center;
  justify-content: space-between;
}}

.console-btn {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 12px;
  background: rgba(208, 112, 63, 0.16);
  border: 1px solid rgba(208, 112, 63, 0.4);
  border-radius: 6px;
  color: var(--washi);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}}

.console-btn:hover {{
  background: rgba(208, 112, 63, 0.28);
}}

.console-btn.ghost {{
  background: transparent;
  border-color: var(--line);
  color: var(--washi-2);
}}

.console-btn.ghost:hover {{
  background: rgba(236, 230, 218, 0.05);
  color: var(--washi);
}}

.wire-log {{
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 11px;
  background: #060504;
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 10px;
  color: #a8b39a;
  max-height: 240px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}}

.wire-badge {{
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(66, 82, 46, 0.3);
  color: #8fae63;
  border: 1px solid rgba(66, 82, 46, 0.6);
}}
</style>
</head>
<body>

<div class="sim-workspace">
  <!-- Left Screen Switcher Rail -->
  <aside class="sim-rail">
    <div class="sim-brand">
      <svg width="28" height="28" viewBox="0 0 44 44" fill="none" aria-hidden="true">
        <path d="M29.2 11.2A13.2 13.2 0 1 0 30.4 20.8" stroke="#ece6da" stroke-width="2.4" stroke-linecap="round"/>
        <circle cx="30.3" cy="15.8" r="2" fill="#d0703f"/>
      </svg>
      <div>
        <h1>TinCan 2.2</h1>
        <div style="font-size:11px;color:var(--washi-3)">iOS Simulator & Wire Bridge</div>
      </div>
      <span class="tag">9 Screens</span>
    </div>

    <div class="rail-section">
      <div class="rail-section-title">Design Flow Screens</div>
      {rail_html}
    </div>

    <div class="rail-section" style="margin-top:auto">
      <div class="rail-section-title">Wire Contract Status</div>
      <div style="font-size:11.5px;color:var(--washi-3);line-height:1.4">
        13 Endpoints Documented<br>
        Relay: <span style="color:var(--kaki);word-break:break-all">iot-federated-agent-memory-production.up.railway.app</span>
      </div>
    </div>
  </aside>

  <!-- Center iPhone Bezel Simulator -->
  <main class="sim-stage">
    <div class="phone-bezel">
      <div class="phone-inner">
        <!-- Rendered Screen Bundle -->
        {screens_html_bundle}

        <!-- Unified Interactive Tab Bar -->
        <nav id="simTabBar" class="sim-tabbar">
          <div class="tab on" data-tab="inbox" onclick="switchTab('inbox')">
            <svg viewBox="0 0 24 24" fill="none"><rect x="3" y="6" width="18" height="13" rx="3" stroke="currentColor" stroke-width="1.7"/><path d="M4.5 8.2L12 13.2 19.5 8.2" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <span>Inbox</span>
          </div>
          <div class="tab" data-tab="arena" onclick="switchTab('arena')">
            <svg viewBox="0 0 24 24" fill="none"><circle cx="7" cy="12" r="3.2" stroke="currentColor" stroke-width="1.7"/><circle cx="17" cy="12" r="3.2" stroke="currentColor" stroke-width="1.7"/><path d="M10.3 12h3.4" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>
            <span>Arena</span>
          </div>
          <div class="tab" data-tab="calls" onclick="switchTab('calls')">
            <svg viewBox="0 0 24 24" fill="none"><path d="M6 16.5V8.5a4 4 0 0 1 4-4h3" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/><path d="M10.5 2.8l4.2 4.2-4.2 4.2" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/><path d="M6 16.5c2.2 2.6 5.4 4 9.2 4 1.4 0 2.3-.6 2.3-1.7 0-.7-.5-1-1.3-1.3l-2-.6c-.6-.2-.8-.5-.8-1 0-.3.1-.6.5-1.1" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>
            <span>Calls</span>
          </div>
          <div class="tab" data-tab="you" onclick="switchTab('you')">
            <svg viewBox="0 0 24 24" fill="none"><path d="M16.2 6.4A7 7 0 1 0 16.8 11.5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/><circle cx="16.7" cy="8.7" r="1.3" fill="currentColor"/></svg>
            <span>You</span>
          </div>
        </nav>
        <div class="phone-homebar"></div>
      </div>
    </div>
  </main>

  <!-- Right Live Wire Console -->
  <aside class="sim-console">
    <div class="console-card">
      <h3>
        <span>Live Wire Actions</span>
        <span class="wire-badge">ONLINE</span>
      </h3>
      <p style="font-size:12px;color:var(--washi-3);margin:0">Execute wire API endpoints against the running server:</p>
      
      <div style="display:flex;flex-direction:column;gap:6px">
        <button class="console-btn" onclick="callWire('whoami')">GET /api/tincan/whoami</button>
        <button class="console-btn" onclick="callWire('inbox')">GET /api/tincan/inbox</button>
        <button class="console-btn" onclick="callWire('send')">POST /api/tincan/send</button>
        <button class="console-btn" onclick="callWire('arena')">POST /api/mesh/arena/battle</button>
        <button class="console-btn" onclick="callWire('billing')">GET /api/account/billing</button>
      </div>
    </div>

    <div class="console-card">
      <h3>
        <span>Wire Event Log</span>
        <button class="console-btn ghost" style="padding:2px 6px;font-size:10px" onclick="clearWireLog()">Clear</button>
      </h3>
      <div id="wireLog" class="wire-log">// Ready. Click any wire action above...</div>
    </div>

    <div class="console-card">
      <h3>Wire Contract Specification</h3>
      <div style="max-height:180px;overflow-y:auto">
        <pre class="wire-log" style="font-size:10px;margin:0">{wire_spec_json}</pre>
      </div>
    </div>
  </aside>
</div>

<script>
let currentScreenId = '{initial_screen}';

function logWire(msg) {{
  const logEl = document.getElementById('wireLog');
  const ts = new Date().toLocaleTimeString();
  logEl.textContent = `[${{ts}}] ${{msg}}\\n` + logEl.textContent;
}}

function clearWireLog() {{
  document.getElementById('wireLog').textContent = '// Ready.';
}}

function switchScreen(screenId) {{
  currentScreenId = screenId;
  document.querySelectorAll('.screen-container').forEach(el => {{
    el.classList.toggle('active', el.getAttribute('data-screen') === screenId);
  }});
  document.querySelectorAll('.rail-btn').forEach(btn => {{
    btn.classList.toggle('active', btn.getAttribute('data-target') === screenId);
  }});

  // Update simulator tabbar active tab
  const activeEl = document.getElementById('screen-' + screenId);
  const tab = activeEl ? activeEl.getAttribute('data-tab') : null;
  if (tab && tab !== 'other') {{
    document.querySelectorAll('#simTabBar .tab').forEach(t => {{
      t.classList.toggle('on', t.getAttribute('data-tab') === tab);
    }});
    document.getElementById('simTabBar').style.display = 'flex';
  }} else {{
    // Hide tabbar on onboarding, call or verify sheets if desired, or keep accessible
    if (screenId === '01-onboarding' || screenId === '06-call' || screenId === '04-verify') {{
      document.getElementById('simTabBar').style.display = 'none';
    }} else {{
      document.getElementById('simTabBar').style.display = 'flex';
    }}
  }}

  logWire(`Switched view to screen: ${{screenId}}`);
}}

function switchTab(tabId) {{
  document.querySelectorAll('#simTabBar .tab').forEach(t => {{
    t.classList.toggle('on', t.getAttribute('data-tab') === tabId);
  }});

  const tabDefaults = {{
    'inbox': '02-inbox',
    'arena': '05-arena',
    'calls': '06-call',
    'you': '07-keys'
  }};

  const target = tabDefaults[tabId] || '02-inbox';
  switchScreen(target);
}}

async function callWire(endpoint) {{
  logWire(`Calling endpoint ${{endpoint}}...`);
  try {{
    if (endpoint === 'whoami') {{
      const res = await fetch('/api/tincan/whoami');
      const data = await res.json();
      logWire(`whoami -> ${{JSON.stringify(data)}}`);
    }} else if (endpoint === 'inbox') {{
      const res = await fetch('/api/tincan/inbox?address=tc:simulator_test&timeout=0');
      const data = await res.json();
      logWire(`inbox -> ${{JSON.stringify(data)}}`);
    }} else if (endpoint === 'send') {{
      const res = await fetch('/api/tincan/send', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{
          to: 'tc:maya_peer',
          from: 'tc:tony_ios',
          box: 'YWJjZGVmZ2hpams=',
          sig: 'c2lnbmF0dXJlX2J5dGVz'
        }})
      }});
      const data = await res.json();
      logWire(`send -> ${{JSON.stringify(data)}}`);
    }} else if (endpoint === 'arena') {{
      const res = await fetch('/api/mesh/arena/vote', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{
          peer_id: 'tc:tony_ios',
          winner_alias: 'gemini-brain',
          prompt_preview: 'WebRTC zero knowledge TURN fallback'
        }})
      }});
      const data = await res.json();
      logWire(`arena vote -> ${{JSON.stringify(data)}}`);
    }} else if (endpoint === 'billing') {{
      const res = await fetch('/api/account/billing?peer_id=tc:tony_ios');
      const data = await res.json();
      logWire(`billing -> ${{JSON.stringify(data)}}`);
    }}
  }} catch (err) {{
    logWire(`[ERROR] ${{err.message}}`);
  }}
}}

// Setup in-screen button wiring
document.addEventListener('DOMContentLoaded', () => {{
  // Inbox row click opens thread
  document.querySelectorAll('#screen-02-inbox .row').forEach(row => {{
    row.style.cursor = 'pointer';
    row.addEventListener('click', () => switchScreen('03-thread'));
  }});

  // Thread back button opens inbox
  document.querySelectorAll('#screen-03-thread .nav .back').forEach(btn => {{
    btn.style.cursor = 'pointer';
    btn.addEventListener('click', () => switchScreen('02-inbox'));
  }});

  // Thread sealbar opens verify sheet
  document.querySelectorAll('#screen-03-thread .sealbar').forEach(sb => {{
    sb.style.cursor = 'pointer';
    sb.addEventListener('click', () => switchScreen('04-verify'));
  }});

  // Verify sheet back / close
  document.querySelectorAll('#screen-04-verify .nav .back, #screen-04-verify .btn').forEach(b => {{
    b.style.cursor = 'pointer';
    b.addEventListener('click', () => switchScreen('03-thread'));
  }});

  // Onboarding buttons
  document.querySelectorAll('#screen-01-onboarding .btn').forEach(b => {{
    b.style.cursor = 'pointer';
    b.addEventListener('click', () => switchScreen('02-inbox'));
  }});

  // Arena votes
  document.querySelectorAll('#screen-05-arena .vote').forEach(v => {{
    v.style.cursor = 'pointer';
    v.addEventListener('click', () => {{
      callWire('arena');
    }});
  }});

  // Call screen end button
  document.querySelectorAll('#screen-06-call .ctl.end').forEach(ctl => {{
    ctl.style.cursor = 'pointer';
    ctl.addEventListener('click', () => switchScreen('02-inbox'));
  }});

  switchScreen(currentScreenId);
}});
</script>
</body>
</html>
"""
