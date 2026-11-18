"""TinCan 2.2 · Aeonik Celadon & Ink + Zen Design Systems Showcase Gallery.

Provides a unified, responsive showcase for all updated design mockups across:
0. Aeonik Celadon & Ink Reskin (4-quadrant Industrial Terminal + Aeonik Fono Mobile UI)
1. Native iOS App (9 screen mockups + composite sheets + live simulator)
2. Car Head-Unit UI (1280x720 Sumi-Dock driving, parked, dashcam, identity mockups + live UI)
3. Mesh OS Desktop (11-window Zen contact sheet + tiled grid + Workstation Studio mockups)
4. Terminal AI Redesign (AI Home Shell, AI Copilot, Blind Brain Arena & Token Vault mockups)
"""

from typing import Dict, List, Any

AEONIK_MOCKUPS: List[Dict[str, str]] = [
    {
        "id": "aeonik-term",
        "title": "Aeonik Industrial Terminal",
        "desc": "4-quadrant desktop terminal: SHELL git status, SYSTEM metrics & sparklines, TREE filesystem, and RECENT build logs.",
        "img": "/docs/designs/aeonik-terminal.png",
        "link": "/mesh",
        "link_label": "Open Terminal Window",
    },
    {
        "id": "aeonik-fono",
        "title": "Aeonik Fono Mobile Interface",
        "desc": "Minimalist celadon mobile interface: circular gauge ring capsule, modular equipment cards, and schedule table with pill toggles.",
        "img": "/docs/designs/aeonik-fono.png",
        "link": "/fono",
        "link_label": "Open Aeonik Fono",
    },
    {
        "id": "aeonik-node-terminal-04",
        "title": "Aeonik Node Studio · Image DAG & LUT Filter Rack",
        "desc": "4-quadrant Aeonik Celadon & Ink Node Studio for image workflows: orthogonal DAG canvas, Kodak 2383 LUT + Halation filter rack, .space tree, and Prompt Island.",
        "img": "/assets/designs/tincan_gemini_node_terminal_04.png",
        "link": "/nodes?modality=image",
        "link_label": "Open Image Node Studio",
    },
    {
        "id": "aeonik-node-terminal-04-text",
        "title": "Aeonik Node Studio · Text Prose Filter & Beat Timeline",
        "desc": "Text modality DAG with DeepSeek-v4.1-TEE / Gemini 3.1 Pro routing, WGA Tighten & Fact Lock prose filters, and beat timeline.",
        "img": "/assets/designs/tincan_gemini_node_terminal_04_text.png",
        "link": "/nodes?modality=text",
        "link_label": "Open Text Node Studio",
    },
    {
        "id": "aeonik-node-terminal-04-video",
        "title": "Aeonik Node Studio · Video Cut Timeline & 60fps/LUFS Rack",
        "desc": "Video modality DAG with LTX-Video / Kling 1.6 synthesis, 60fps Optical Flow, Temporal Deflicker, and -14 LUFS J-Cut ducking.",
        "img": "/assets/designs/tincan_gemini_node_terminal_04_video.png",
        "link": "/nodes?modality=video",
        "link_label": "Open Video Node Studio",
    },
    {
        "id": "aeonik-node-terminal-04-sheet",
        "title": "Aeonik Node Studio · 3-Modality Master Sheet (Image · Text · Video)",
        "desc": "Composite contact sheet unifying Image, Text, and Video Aeonik Node Studio industrial terminals over a shared .space DAG.",
        "img": "/assets/designs/tincan_gemini_node_terminal_04_modalities_sheet.png",
        "link": "/nodes",
        "link_label": "Open Node Studio",
    },
    {
        "id": "aeonik-node-studio-01",
        "title": "Node Studio Window · Prompt Island & DAG Canvas",
        "desc": "Primary Mesh OS #win-nodes window spec featuring selection-driven Prompt Island and orthogonal node graph.",
        "img": "/assets/designs/tincan_gemini_node_studio_01.png",
        "link": "/nodes",
        "link_label": "Open Node Studio",
    },
    {
        "id": "aeonik-node-spec-02",
        "title": "Node Timeline & Non-Destructive Filter Rack",
        "desc": "Time-indexed 00:00 -> 00:09 DAG timeline strip paired with toggleable non-destructive filter rack and sparklines.",
        "img": "/assets/designs/tincan_gemini_node_spec_02.png",
        "link": "/nodes?view=timeline",
        "link_label": "Open Timeline View",
    },
    {
        "id": "aeonik-node-modes-03",
        "title": "Prompt Island Modes (Generate / Edit / Merge) & NanoGPT Hookup",
        "desc": "Selection-driven Generate (0), Edit + Filter (1), and Merge (2+) Prompt Island state machine wired to NanoGPT and Gemini.",
        "img": "/assets/designs/tincan_gemini_node_modes_03.png",
        "link": "/nodes?view=gateway",
        "link_label": "Open Gateway View",
    },
]

IOS_MOCKUPS: List[Dict[str, str]] = [
    {"id": "01-onboarding", "title": "1. Onboarding & Key Wrap", "desc": "Ed25519 key generation, 24-word seed restore, Secure Enclave FaceID wrap.", "img": "/docs/designs/ios-app/01-onboarding.png"},
    {"id": "02-inbox", "title": "2. Sealed Inbox", "desc": "NaCl-sealed message inbox, TOFU trust badges, low-latency push alerts.", "img": "/docs/designs/ios-app/02-inbox.png"},
    {"id": "03-thread", "title": "3. Encrypted Thread", "desc": "End-to-end sealed chat bubbles, Kokoro voice message player, seal verification bar.", "img": "/docs/designs/ios-app/03-thread.png"},
    {"id": "04-verify", "title": "4. Key Verification", "desc": "Side-by-side TOFU key fingerprint comparison and camera QR scan verification.", "img": "/docs/designs/ios-app/04-verify.png"},
    {"id": "05-arena", "title": "5. AI Brain Arena", "desc": "Live AI model duels, blind model benchmarking, voting stream, and XP rewards.", "img": "/docs/designs/ios-app/05-arena.png"},
    {"id": "06-call", "title": "6. WebRTC Call", "desc": "Encrypted sub-80ms voice, video, and screenshare room with CallKit integration.", "img": "/docs/designs/ios-app/06-call.png"},
    {"id": "07-keys", "title": "7. Keys & Devices", "desc": "Device linking, hardware passkey pairing, and cold-storage seed export.", "img": "/docs/designs/ios-app/07-keys.png"},
    {"id": "08-relay", "title": "8. Relay Settings", "desc": "Blind relay selection, latency ping monitor, zero-knowledge ciphertext proof.", "img": "/docs/designs/ios-app/08-relay.png"},
    {"id": "09-credits", "title": "9. Credits & Billing", "desc": "OpenRouter token spend ledger, rate breakdown, and StoreKit top-up.", "img": "/docs/designs/ios-app/09-credits.png"},
    {"id": "sheet-messages", "title": "Composite Sheet 1: Messaging", "desc": "Complete master overview sheet of onboarding, inbox, thread, and verify.", "img": "/docs/designs/ios-app/SHEET_1_messages.png"},
    {"id": "sheet-mesh", "title": "Composite Sheet 2: Mesh & Arena", "desc": "Complete master overview sheet of arena, calls, keys, relay, and credits.", "img": "/docs/designs/ios-app/SHEET_2_mesh.png"},
]

CAR_MOCKUPS: List[Dict[str, str]] = [
    {"id": "car-driving", "title": "1. Driving Mode (Glanceable)", "desc": "Moving status, persistent Sumi dock, REC pill, high-contrast typography, locked precision gates.", "img": "/docs/designs/car-ui/sumi-dock-driving.png"},
    {"id": "car-parked", "title": "2. Parked Home (Unlocked)", "desc": "Parked state with video feed atmosphere, space access, driver switcher, full interactive controls.", "img": "/docs/designs/car-ui/sumi-dock-parked.png"},
    {"id": "car-dashcam", "title": "3. Triple Dashcam Monitor", "desc": "Front (1080p60), cabin (night-vision), and rear camera telemetry with clip bookmarks.", "img": "/docs/designs/car-ui/sumi-dock-dashcam.png"},
    {"id": "car-identity", "title": "4. Driver Identity & Passkeys", "desc": "Quick driver profile switching, Ed25519 car keycard, and NFC/QR mobile pairing.", "img": "/docs/designs/car-ui/sumi-dock-identity.png"},
    {"id": "car-sheet", "title": "Car Composite Sheet", "desc": "Master 4-screen landscape overview of all aftermarket dashboard states.", "img": "/docs/designs/car-ui/EARLY_direction1_sheet.png"},
]

DESKTOP_MOCKUPS: List[Dict[str, str]] = [
    {"id": "win-contact", "title": "Mesh OS Zen Windows Contact Sheet", "desc": "Master contact sheet uniting all 11 tool windows in the Zen design system.", "img": "/assets/designs/tincan_zen_windows_contact_sheet.png"},
    {"id": "win-tiled", "title": "Tiled Desktop Design", "desc": "Responsive 2x2 window tiling layout designed in FigCraft.", "img": "/assets/designs/tiled_desktop_design.png"},
    {"id": "win-peers", "title": "Peers & Leaderboard Pop-Out", "desc": "Dedicated pop-out window for active peers, XP ranking, and presence.", "img": "/assets/designs/peers_popout_design.png"},
    {
        "id": "ws-studio",
        "title": "Workstation · Multi-Model & 3D Studio",
        "desc": "FigCraft spec for /workstation combining NanoGPT TEE/Heretic routing, Hyper3D Rodin v2 mesh synthesis, enclave diff patches, and .space Merkle sync.",
        "img": "/assets/designs/workstation_studio_design.png",
        "link": "/workstation",
        "link_label": "Open Workstation",
    },
    {
        "id": "ws-stories",
        "title": "Workstation · 4 User Story Workflows",
        "desc": "End-to-end user journeys for 3D Asset Foundry, Private TEE Enclave Audit, Arena Calibration, and Live Peer + Rodin Review.",
        "img": "/assets/designs/workstation_user_stories.png",
    },
    {
        "id": "ws-dual",
        "title": "Space + Workstation Dual Zen Desktop",
        "desc": "Side-by-side tiled layout pairing Space Ranger VFS & Wasm Studio (/space) with Workstation Foundry & Enclave (/workstation) over shared .space state.",
        "img": "/assets/designs/workstation_dual_space_desktop.png",
    },
]

TERMINAL_AI_MOCKUPS: List[Dict[str, str]] = [
    {
        "id": "term-ai-sheet",
        "title": "TinCan Terminal AI · Master Contact Sheet",
        "desc": "4-screen Aeonik Celadon & Ink redesign sheet uniting AI Home Shell, AI Copilot, Blind Brain Arena, and Token Vault.",
        "img": "/assets/designs/tincan_terminal_ai_sheet.png",
        "link": "/",
        "link_label": "Open AI Home",
    },
    {
        "id": "term-ai-home",
        "title": "01 · AI Gateway & Mesh Home Shell",
        "desc": "tincan ask command hero, zero-burn local Ollama / FAU OwlChat / NanoGPT TEE router chips, 4 workflow cards, and monochrome telemetry.",
        "img": "/assets/designs/tincan_terminal_01_home.png",
        "link": "/",
        "link_label": "Open AI Home",
    },
    {
        "id": "term-ai-copilot",
        "title": "02 · AI Copilot & .space Code Diffs",
        "desc": "Dedicated thread workspace with direct localhost Ollama & OwlChat BYOK routing, .space RAG file context, and one-click patch apply.",
        "img": "/assets/designs/tincan_terminal_02_copilot.png",
        "link": "/copilot",
        "link_label": "Open AI Copilot",
    },
    {
        "id": "term-ai-arena",
        "title": "03 · AI Brain Arena (Local vs Cloud)",
        "desc": "Side-by-side blind duel comparing zero-burn local open-weight models against frontier cloud with pre-auth credit caps and +25 XP votes.",
        "img": "/assets/designs/tincan_terminal_03_arena.png",
        "link": "/arena",
        "link_label": "Open AI Brain Arena",
    },
    {
        "id": "term-ai-tokens",
        "title": "04 · Token Vault & Sponsor Arbitrage",
        "desc": "USD-normalized credits (1 CR = $0.001), Stripe $1/$5/$20 top-up packs, rate card, +50 CR sponsor video clips, and audit ledger.",
        "img": "/assets/designs/tincan_terminal_04_tokens.png",
        "link": "/tokens",
        "link_label": "Open Token Vault",
    },
]


def _build_card_html(m: Dict[str, str], action_href: str = "", action_label: str = "") -> str:
    img = m["img"]
    title = m["title"]
    desc = m["desc"]
    extra_btn = ""
    if action_href and action_label:
        extra_btn = f'<a href="{action_href}" class="btn-sm primary">{action_label}</a>'
    return (
        '<div class="mockup-card">\n'
        '  <div class="card-preview">\n'
        f'    <img src="{img}" alt="{title}" loading="lazy" onclick="openLightbox(\'{img}\')">\n'
        '  </div>\n'
        '  <div class="card-content">\n'
        '    <div>\n'
        f'      <div class="card-title">{title}</div>\n'
        f'      <div class="card-desc">{desc}</div>\n'
        '    </div>\n'
        '    <div class="card-links">\n'
        f'      <a href="{img}" target="_blank" class="btn-sm">View Full Res</a>\n'
        f'      {extra_btn}\n'
        '    </div>\n'
        '  </div>\n'
        '</div>'
    )


def render_designs_gallery_html(active_tab: str = "aeonik") -> str:
    """Renders the comprehensive mockups gallery page in Aeonik Celadon & Ink style (Python 3.11+ safe)."""
    valid_tabs = {"aeonik", "ios", "car", "desktop", "terminal-ai"}
    selected_tab = active_tab if active_tab in valid_tabs else "aeonik"
    tab_cls = lambda key: " active" if selected_tab == key else ""

    aeonik_cards = "\n".join(
        _build_card_html(m, m.get("link", "/mesh"), m.get("link_label", "Open Live View"))
        for m in AEONIK_MOCKUPS
    )
    ios_cards = "\n".join(
        _build_card_html(
            m,
            f"/ios/{m['id'] if not m['id'].startswith('sheet') else '02-inbox'}",
            "Open in Simulator",
        )
        for m in IOS_MOCKUPS
    )
    car_cards = "\n".join(
        _build_card_html(
            m,
            f"/car/{m['id'].replace('car-', '') if m['id'] != 'car-sheet' else 'driving'}",
            "Open in Head-Unit",
        )
        for m in CAR_MOCKUPS
    )
    desktop_cards = "\n".join(
        _build_card_html(m, m.get("link", "/mesh"), m.get("link_label", "Open Desktop"))
        for m in DESKTOP_MOCKUPS
    )
    terminal_ai_cards = "\n".join(
        _build_card_html(m, m.get("link", "/"), m.get("link_label", "Open Live View"))
        for m in TERMINAL_AI_MOCKUPS
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TinCan 2.2 · Design Systems & Mockups Showcase</title>
<style>
:root {{
  --aeonik-bg: #ecf1e6;
  --aeonik-card: #f3f7ee;
  --aeonik-fg: #111111;
  --aeonik-dim: #555555;
  --aeonik-line: #111111;
  --aeonik-sans: -apple-system, BlinkMacSystemFont, "Aeonik", "Inter", "Helvetica Neue", sans-serif;
  --aeonik-mono: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace;
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  background: var(--aeonik-bg);
  color: var(--aeonik-fg);
  font-family: var(--aeonik-sans);
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
  padding: 0 0 60px 0;
}}

header.topbar {{
  background: var(--aeonik-bg);
  border-bottom: 1px solid var(--aeonik-line);
  padding: 18px 32px;
  position: sticky; top: 0; z-index: 100;
  display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px;
}}
.brand {{
  display: flex; align-items: center; gap: 12px;
}}
.brand h1 {{
  font-size: 1.5rem; font-weight: 600; letter-spacing: -0.02em;
}}
.brand .pill {{
  font-family: var(--aeonik-mono);
  font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
  background: var(--aeonik-fg); color: var(--aeonik-bg);
  padding: 3px 10px; border-radius: 999px;
}}

.nav-actions {{
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
}}
.nav-link {{
  color: var(--aeonik-fg); text-decoration: none; font-size: 0.82rem; font-weight: 500;
  padding: 6px 14px; border-radius: 999px; border: 1px solid var(--aeonik-line);
  transition: all 0.15s;
}}
.nav-link:hover {{
  background: var(--aeonik-fg); color: var(--aeonik-bg);
}}
.btn-cta {{
  background: var(--aeonik-fg); color: var(--aeonik-bg); font-weight: 600; font-size: 0.85rem;
  padding: 8px 18px; border-radius: 999px; text-decoration: none; border: 1px solid var(--aeonik-line);
  cursor: pointer; transition: opacity 0.15s;
}}
.btn-cta:hover {{ opacity: 0.85; }}
.btn-cta.outline {{
  background: transparent; color: var(--aeonik-fg);
}}
.btn-cta.outline:hover {{
  background: var(--aeonik-fg); color: var(--aeonik-bg);
}}

.tabs-bar {{
  max-width: 1400px; margin: 28px auto 0; padding: 0 32px;
  display: flex; gap: 8px; flex-wrap: wrap; border-bottom: 1px solid var(--aeonik-line);
  padding-bottom: 14px;
}}
.tab-btn {{
  background: transparent; border: 1px solid var(--aeonik-line); color: var(--aeonik-fg);
  font-family: var(--aeonik-mono); font-size: 0.8rem; font-weight: 600;
  padding: 8px 16px; border-radius: 999px; cursor: pointer; transition: all 0.15s;
}}
.tab-btn:hover {{
  background: rgba(17, 17, 17, 0.08);
}}
.tab-btn.active {{
  background: var(--aeonik-fg); color: var(--aeonik-bg);
}}

main.container {{
  max-width: 1400px; margin: 28px auto 0; padding: 0 32px;
}}

.intro-panel {{
  background: var(--aeonik-bg); border: 1px solid var(--aeonik-line);
  border-radius: 20px; padding: 24px 28px; margin-bottom: 28px;
  display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;
}}
.intro-text h2 {{
  font-size: 1.55rem; margin-bottom: 6px; font-weight: 600; letter-spacing: -0.02em;
}}
.intro-text p {{
  color: var(--aeonik-dim); font-size: 0.92rem; max-width: 780px;
}}

.grid-gallery {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 24px;
}}

.mockup-card {{
  background: var(--aeonik-bg);
  border: 1px solid var(--aeonik-line);
  border-radius: 20px;
  overflow: hidden;
  display: flex; flex-direction: column;
  transition: transform 0.2s, box-shadow 0.2s;
}}
.mockup-card:hover {{
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.08);
}}
.card-preview {{
  width: 100%; aspect-ratio: 16 / 10; overflow: hidden; background: #dfe5d8;
  border-bottom: 1px solid var(--aeonik-line);
  display: flex; align-items: center; justify-content: center;
}}
.card-preview img {{
  width: 100%; height: 100%; object-fit: contain; cursor: pointer;
  transition: transform 0.25s;
}}
.card-preview img:hover {{
  transform: scale(1.02);
}}
.card-content {{
  padding: 16px 20px; flex: 1; display: flex; flex-direction: column; justify-content: space-between;
}}
.card-title {{
  font-size: 1.1rem; font-weight: 600; letter-spacing: -0.01em; margin-bottom: 6px;
}}
.card-desc {{
  font-size: 0.84rem; color: var(--aeonik-dim); margin-bottom: 14px;
}}
.card-links {{
  display: flex; gap: 8px; flex-wrap: wrap;
}}
.btn-sm {{
  font-family: var(--aeonik-mono); font-size: 0.72rem; font-weight: 600;
  padding: 5px 12px; border-radius: 999px; text-decoration: none;
  border: 1px solid var(--aeonik-line); color: var(--aeonik-fg); transition: all 0.15s;
}}
.btn-sm:hover, .btn-sm.primary {{
  background: var(--aeonik-fg); color: var(--aeonik-bg);
}}

/* Lightbox Modal */
#lightbox {{
  position: fixed; inset: 0; background: rgba(17, 17, 17, 0.92); z-index: 1000;
  display: none; align-items: center; justify-content: center; padding: 24px;
}}
#lightbox.active {{ display: flex; }}
#lightbox img {{
  max-width: 95vw; max-height: 92vh; object-fit: contain; border-radius: 12px;
  border: 1px solid #fff;
}}
#lightboxClose {{
  position: absolute; top: 24px; right: 32px; color: #fff; font-size: 32px;
  background: none; border: none; cursor: pointer;
}}

/* Tab sections */
.tab-section {{ display: none; }}
.tab-section.active {{ display: block; }}

/* One-Click Terminal Installer Banner */
.install-banner {{
  background: #ffffff;
  border: 1px solid var(--aeonik-line);
  border-radius: 20px;
  padding: 18px 24px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}}
.install-cmd-box {{
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--aeonik-bg);
  border: 1px solid var(--aeonik-line);
  border-radius: 999px;
  padding: 6px 8px 6px 16px;
  flex: 1;
  min-width: 280px;
  max-width: 720px;
  justify-content: space-between;
}}
.install-cmd-box code {{
  font-family: var(--aeonik-mono);
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--aeonik-fg);
  overflow-x: auto;
  white-space: nowrap;
  user-select: all;
}}
</style>
</head>
<body>

<header class="topbar">
  <div class="brand">
    <span style="font-family: var(--aeonik-mono); font-size: 0.85rem;">14:41</span>
    <h1>TinCan 2.2 Design Systems</h1>
    <span class="pill">Aeonik Celadon &amp; Ink</span>
  </div>
  <div class="nav-actions">
    <a href="/mesh" class="nav-link">⚡ Terminal &amp; Desktop</a>
    <a href="/fono" class="nav-link">📱 Aeonik Fono</a>
    <a href="/ios" class="nav-link">📱 iOS Simulator</a>
    <a href="/car" class="nav-link">🚗 Car Head-Unit</a>
  </div>
</header>

<div class="tabs-bar">
  <button class="tab-btn{tab_cls('aeonik')}" onclick="switchGalleryTab('aeonik')">01 · Aeonik Celadon &amp; Ink ({len(AEONIK_MOCKUPS)})</button>
  <button class="tab-btn{tab_cls('ios')}" onclick="switchGalleryTab('ios')">02 · Native iOS App (11)</button>
  <button class="tab-btn{tab_cls('car')}" onclick="switchGalleryTab('car')">03 · Car Head-Unit UI (5)</button>
  <button class="tab-btn{tab_cls('desktop')}" onclick="switchGalleryTab('desktop')">04 · Mesh OS Windows ({len(DESKTOP_MOCKUPS)})</button>
  <button class="tab-btn{tab_cls('terminal-ai')}" onclick="switchGalleryTab('terminal-ai')">05 · Terminal AI Redesign ({len(TERMINAL_AI_MOCKUPS)})</button>
</div>

<main class="container">
  <!-- ONE-CLICK TERMINAL INSTALLER BANNER -->
  <div class="install-banner">
    <div>
      <div style="font-family: var(--aeonik-mono); font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">⚡ One-Click Terminal Installer</div>
      <div style="font-size: 0.86rem; color: var(--aeonik-dim);">Install TinCan 2.2 CLI, Ed25519 identity &amp; 6 agent skills in 10 seconds</div>
    </div>
    <div class="install-cmd-box">
      <code id="galleryInstallCmd">curl -sSL https://iot-federated-agent-memory-production.up.railway.app/install.sh | bash</code>
      <button class="btn-cta" style="padding: 6px 14px; font-size: 0.75rem;" onclick="copyGalleryInstall(this)">📋 Copy Command</button>
    </div>
    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
      <a href="/Formula/tincan.rb" target="_blank" class="btn-cta outline" style="font-size: 0.78rem;">🍺 brew Formula</a>
      <a href="/install.command" download="Install-TinCan.command" class="btn-cta outline" style="font-size: 0.78rem;">⬇ macOS .command</a>
      <a href="/mesh" class="btn-cta" style="font-size: 0.78rem;">▶ Open Terminal</a>
    </div>
  </div>

  <!-- TAB 0: AEONIK RESKIN -->
  <div id="tab-aeonik" class="tab-section{tab_cls('aeonik')}">
    <div class="intro-panel">
      <div class="intro-text">
        <h2>Aeonik Celadon &amp; Ink Design System (Live Interactive + Reference)</h2>
        <p>Industrial minimalist aesthetic (#ecf1e6 Celadon canvas + 1px #111111 hairline borders). Interact directly with the live 4-quadrant Terminal (SHELL command execution, SYSTEM telemetry, clickable TREE file inspector, RECENT build runner) and live Aeonik Fono mobile controller below.</p>
      </div>
      <div style="display: flex; gap: 10px; flex-wrap: wrap;">
        <a href="/terminal" class="btn-cta">⚡ Launch Fullscreen Terminal</a>
        <a href="/nodes" class="btn-cta outline">⬢ Launch Node Studio</a>
        <a href="/fono" class="btn-cta outline">📱 Launch Aeonik Fono</a>
      </div>
    </div>

    <!-- LIVE INTERACTIVE EMBEDDED WORKSPACE -->
    <div style="display: grid; grid-template-columns: 1.55fr 1fr; gap: 24px; margin-bottom: 28px; align-items: start;">
      <div class="mockup-card">
        <div style="padding: 12px 18px; border-bottom: 1px solid var(--aeonik-line); display: flex; justify-content: space-between; align-items: center; font-family: var(--aeonik-mono); font-size: 0.76rem; font-weight: 600;">
          <span>● LIVE INTERACTIVE · AEONIK 4-QUADRANT TERMINAL (/terminal)</span>
          <a href="/terminal" target="_blank" style="color: var(--aeonik-fg);">Open Fullscreen ↗</a>
        </div>
        <iframe src="/terminal" title="Live Aeonik Terminal" style="width: 100%; height: 820px; border: none; background: #ecf1e6;"></iframe>
      </div>
      <div class="mockup-card">
        <div style="padding: 12px 18px; border-bottom: 1px solid var(--aeonik-line); display: flex; justify-content: space-between; align-items: center; font-family: var(--aeonik-mono); font-size: 0.76rem; font-weight: 600;">
          <span>● LIVE INTERACTIVE · AEONIK FONO CONTROLLER (/fono)</span>
          <a href="/fono" target="_blank" style="color: var(--aeonik-fg);">Open Fullscreen ↗</a>
        </div>
        <iframe src="/fono" title="Live Aeonik Fono" style="width: 100%; height: 820px; border: none; background: #ecf1e6;"></iframe>
      </div>
    </div>

    <div class="grid-gallery">
      {aeonik_cards}
    </div>
  </div>

  <!-- TAB 1: iOS APP -->
  <div id="tab-ios" class="tab-section{tab_cls('ios')}">
    <div class="intro-panel">
      <div class="intro-text">
        <h2>TinCan 2.2 · Native iOS App</h2>
        <p>Purpose-built zero-account native iOS app for iPhone. Secure Enclave Ed25519 keypair, TOFU messaging, live AI Brain Arena, CallKit WebRTC audio/video rooms, and StoreKit credit billing.</p>
      </div>
      <a href="/ios" class="btn-cta">📱 Launch Live iOS Simulator</a>
    </div>
    <div class="grid-gallery">
      {ios_cards}
    </div>
  </div>

  <!-- TAB 2: CAR UI -->
  <div id="tab-car" class="tab-section{tab_cls('car')}">
    <div class="intro-panel">
      <div class="intro-text">
        <h2>TinCan OS · Aftermarket Car Head-Unit UI</h2>
        <p>1280×720 landscape dashboard interface for vehicle cabins. Low-glare night Sumi-Dock, 76px+ touch targets, parked-safety gates, triple dashcam telemetry, and client-side mode switching.</p>
      </div>
      <a href="/car" class="btn-cta">🚗 Launch Live Car UI</a>
    </div>
    <div class="grid-gallery">
      {car_cards}
    </div>
  </div>

  <!-- TAB 3: MESH OS WINDOWS -->
  <div id="tab-desktop" class="tab-section{tab_cls('desktop')}">
    <div class="intro-panel">
      <div class="intro-text">
        <h2>TinCan Mesh OS · Zen Desktop Windows</h2>
        <p>All 11 tool windows plus Workstation Studio with responsive 2x2 grid window tiling and dedicated pop-out windows.</p>
      </div>
      <a href="/mesh" class="btn-cta">🖥️ Open Mesh OS Desktop</a>
    </div>
    <div class="grid-gallery">
      {desktop_cards}
    </div>
  </div>

  <!-- TAB 4: TERMINAL AI REDESIGN -->
  <div id="tab-terminal-ai" class="tab-section{tab_cls('terminal-ai')}">
    <div class="intro-panel">
      <div class="intro-text">
        <h2>TinCan Terminal AI Redesign · Home, Copilot, Arena &amp; Token Vault</h2>
        <p>Aeonik Celadon &amp; Ink v2.2 terminal AI specs: zero-burn local Ollama &amp; FAU OwlChat command routing, .space code diffs in AI Copilot, blind local-vs-cloud Brain Arena duels, and USD-normalized Stripe + sponsor arbitrage Token Vault.</p>
      </div>
      <div style="display: flex; gap: 8px; flex-wrap: wrap;">
        <a href="/" class="btn-cta">⚡ AI Home</a>
        <a href="/copilot" class="btn-cta outline">💬 /copilot</a>
        <a href="/arena" class="btn-cta outline">⚔️ /arena</a>
        <a href="/tokens" class="btn-cta outline">💳 /tokens</a>
      </div>
    </div>
    <div class="grid-gallery">
      {terminal_ai_cards}
    </div>
  </div>
</main>

<div id="lightbox" onclick="closeLightbox()">
  <button id="lightboxClose" onclick="closeLightbox()">&times;</button>
  <img id="lightboxImg" src="" alt="Enlarged mockup">
</div>

<script>
function switchGalleryTab(tabKey) {{
  document.querySelectorAll('.tab-btn').forEach((btn) => {{
    btn.classList.toggle('active', btn.getAttribute('onclick').includes("'" + tabKey + "'"));
  }});
  document.querySelectorAll('.tab-section').forEach(sec => {{
    sec.classList.toggle('active', sec.id === 'tab-' + tabKey);
  }});
}}

function openLightbox(src) {{
  const lb = document.getElementById('lightbox');
  const img = document.getElementById('lightboxImg');
  img.src = src;
  lb.classList.add('active');
}}

function closeLightbox() {{
  document.getElementById('lightbox').classList.remove('active');
}}

document.addEventListener('keydown', (e) => {{
  if (e.key === 'Escape') closeLightbox();
}});

function copyGalleryInstall(btn) {{
  const el = document.getElementById('galleryInstallCmd');
  if (!el) return;
  const text = el.innerText;
  if (navigator.clipboard) {{
    navigator.clipboard.writeText(text).then(() => {{
      const orig = btn.innerText;
      btn.innerText = '✓ Copied!';
      setTimeout(() => {{ btn.innerText = orig; }}, 1600);
    }});
  }}
}}
</script>
</body>
</html>
"""
