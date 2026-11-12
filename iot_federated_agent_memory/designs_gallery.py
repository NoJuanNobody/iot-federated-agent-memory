"""TinCan 2.2 · Zen Design Systems & Mockups Showcase Gallery.

Provides a unified, responsive showcase for all updated design mockups across:
1. Native iOS App (9 screen mockups + composite sheets + live simulator)
2. Car Head-Unit UI (1280x720 Sumi-Dock driving, parked, dashcam, identity mockups + live UI)
3. Narrative Storyboard (3x2 master contact sheet + 6 scene panels + audio drama player)
4. Mesh OS Desktop (11-window Zen contact sheet + tiled grid mockups)
"""

from typing import Dict, List, Any

AEONIK_MOCKUPS = [
    {"id": "aeonik-term", "title": "Aeonik Industrial Terminal", "desc": "4-quadrant desktop terminal: SHELL git status, SYSTEM metrics & sparklines, TREE filesystem, and RECENT build logs.", "img": "/docs/designs/aeonik-terminal.png", "link": "/mesh"},
    {"id": "aeonik-fono", "title": "Aeonik Fono Mobile Interface", "desc": "Minimalist celadon mobile interface: circular gauge ring capsule, modular equipment cards, and schedule table with pill toggles.", "img": "/docs/designs/aeonik-fono.png", "link": "/fono"},
]

IOS_MOCKUPS = [
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

CAR_MOCKUPS = [
    {"id": "car-driving", "title": "1. Driving Mode (Glanceable)", "desc": "Moving status, persistent Sumi dock, REC pill, high-contrast typography, locked precision gates.", "img": "/docs/designs/car-ui/sumi-dock-driving.png"},
    {"id": "car-parked", "title": "2. Parked Home (Unlocked)", "desc": "Parked state with video feed atmosphere, space access, driver switcher, full interactive controls.", "img": "/docs/designs/car-ui/sumi-dock-parked.png"},
    {"id": "car-dashcam", "title": "3. Triple Dashcam Monitor", "desc": "Front (1080p60), cabin (night-vision), and rear camera telemetry with clip bookmarks.", "img": "/docs/designs/car-ui/sumi-dock-dashcam.png"},
    {"id": "car-identity", "title": "4. Driver Identity & Passkeys", "desc": "Quick driver profile switching, Ed25519 car keycard, and NFC/QR mobile pairing.", "img": "/docs/designs/car-ui/sumi-dock-identity.png"},
    {"id": "car-sheet", "title": "Car Composite Sheet", "desc": "Master 4-screen landscape overview of all aftermarket dashboard states.", "img": "/docs/designs/car-ui/EARLY_direction1_sheet.png"},
]

STORYBOARD_MOCKUPS = [
    {"id": "sb-contact", "title": "Zen Master Contact Sheet (3x2)", "desc": "Procedural high-res contact sheet spanning all 6 narrative audio drama scenes.", "img": "/docs/panels/zen_storyboard_contact_sheet.png"},
    {"id": "sb-01", "title": "Scene 1: Cyber Lab & Zen Sanctuary", "desc": "The transition from noisy CRT terminal to calm Japanese zen sanctuary.", "img": "/docs/panels/panel_01_zen_sanctuary.png"},
    {"id": "sb-02", "title": "Scene 2: Kokoro Neural Voice Alert", "desc": "Local 82M voice synthesis engine whispering urgent cryptographic dispatch.", "img": "/docs/panels/panel_02_kokoro_whisper.png"},
    {"id": "sb-03", "title": "Scene 3: Toronto Loft TOFU Contact", "desc": "Trust-On-First-Use contact verification across peer mesh nodes.", "img": "/docs/panels/panel_03_toronto_loft_tofu.png"},
    {"id": "sb-04", "title": "Scene 4: WebRTC Capsule Flight", "desc": "Sub-80ms STUN signaling relay traversing transatlantic flight corridors.", "img": "/docs/panels/panel_04_webrtc_capsule_flight.png"},
    {"id": "sb-05", "title": "Scene 5: AI Brain Arena Duel", "desc": "Competitive model evaluation and XP progression in the decentralized arena.", "img": "/docs/panels/panel_05_ai_brain_arena.png"},
    {"id": "sb-06", "title": "Scene 6: L5 Mesh Sovereign", "desc": "Autonomous edge agent cluster achieving self-sovereign L5 coordination.", "img": "/docs/panels/panel_06_l5_mesh_sovereign.png"},
]

DESKTOP_MOCKUPS = [
    {"id": "win-contact", "title": "Mesh OS Zen Windows Contact Sheet", "desc": "Master contact sheet uniting all 11 tool windows in the Zen design system.", "img": "/assets/designs/tincan_zen_windows_contact_sheet.png"},
    {"id": "win-tiled", "title": "Tiled Desktop Design", "desc": "Responsive 2x2 window tiling layout designed in FigCraft.", "img": "/assets/designs/tiled_desktop_design.png"},
    {"id": "win-peers", "title": "Peers & Leaderboard Pop-Out", "desc": "Dedicated pop-out window for active peers, XP ranking, and presence.", "img": "/assets/designs/peers_popout_design.png"},
]


def render_designs_gallery_html(active_tab: str = "ios") -> str:
    """Renders the comprehensive mockups gallery page."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TinCan 2.2 · Updated Design Mockups Showcase</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@500;600&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root {{
  --sumi: #0e0d0b;
  --sumi-soft: #17150f;
  --sumi-card: #201d16;
  --washi: #ece6da;
  --washi-dim: rgba(236, 230, 218, 0.72);
  --washi-hairline: rgba(236, 230, 218, 0.14);
  --kaki: #d0703f;
  --rust: #964622;
  --moss: #42522e;
  --mincho: "Shippori Mincho", "Noto Serif", serif;
  --gothic: "Zen Kaku Gothic New", -apple-system, sans-serif;
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  background: var(--sumi);
  color: var(--washi);
  font-family: var(--gothic);
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
  padding: 0 0 60px 0;
}}

/* Grain filter overlay */
.grain-overlay {{
  position: fixed; inset: 0; pointer-events: none; opacity: 0.18; z-index: 999;
  background-image: radial-gradient(rgba(236, 230, 218, 0.15) 1px, transparent 0);
  background-size: 4px 4px;
}}

header.topbar {{
  background: rgba(14, 13, 11, 0.88);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--washi-hairline);
  padding: 18px 32px;
  position: sticky; top: 0; z-index: 100;
  display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px;
}}
.brand {{
  display: flex; align-items: center; gap: 12px;
}}
.brand svg {{
  width: 32px; height: 32px;
}}
.brand h1 {{
  font-family: var(--mincho); font-size: 1.35rem; font-weight: 600; letter-spacing: 0.02em;
}}
.brand .pill {{
  font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
  background: rgba(208, 112, 63, 0.16); color: var(--kaki);
  border: 1px solid rgba(208, 112, 63, 0.35); padding: 2px 8px; border-radius: 999px;
}}

.nav-actions {{
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
}}
.nav-link {{
  color: var(--washi-dim); text-decoration: none; font-size: 0.85rem; padding: 6px 12px;
  border-radius: 6px; border: 1px solid var(--washi-hairline); transition: all 0.2s;
}}
.nav-link:hover, .nav-link.active {{
  color: var(--washi); border-color: var(--kaki); background: rgba(208, 112, 63, 0.1);
}}
.btn-cta {{
  background: var(--kaki); color: #fff; font-weight: 500; font-size: 0.85rem;
  padding: 7px 16px; border-radius: 6px; text-decoration: none; border: none; cursor: pointer;
  transition: opacity 0.2s;
}}
.btn-cta:hover {{ opacity: 0.9; }}

.tabs-bar {{
  max-width: 1400px; margin: 32px auto 0; padding: 0 32px;
  display: flex; gap: 10px; border-bottom: 1px solid var(--washi-hairline);
}}
.tab-btn {{
  background: none; border: none; color: var(--washi-dim); font-family: var(--gothic);
  font-size: 0.95rem; font-weight: 500; padding: 12px 18px; cursor: pointer;
  border-bottom: 2px solid transparent; transition: all 0.2s;
}}
.tab-btn:hover {{ color: var(--washi); }}
.tab-btn.active {{
  color: var(--kaki); border-bottom-color: var(--kaki); font-weight: 700;
}}

main.container {{
  max-width: 1400px; margin: 32px auto 0; padding: 0 32px;
}}

.intro-panel {{
  background: var(--sumi-soft); border: 1px solid var(--washi-hairline);
  border-radius: 12px; padding: 24px 28px; margin-bottom: 32px;
  display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;
}}
.intro-text h2 {{
  font-family: var(--mincho); font-size: 1.5rem; margin-bottom: 6px; font-weight: 600;
}}
.intro-text p {{
  color: var(--washi-dim); font-size: 0.95rem; max-width: 800px;
}}

.grid-gallery {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 24px;
}}

.mockup-card {{
  background: var(--sumi-soft);
  border: 1px solid var(--washi-hairline);
  border-radius: 12px;
  overflow: hidden;
  display: flex; flex-direction: column;
  transition: transform 0.25s, border-color 0.25s, box-shadow 0.25s;
}}
.mockup-card:hover {{
  transform: translateY(-3px);
  border-color: rgba(208, 112, 63, 0.4);
  box-shadow: 0 12px 28px -6px rgba(0, 0, 0, 0.6);
}}
.card-preview {{
  width: 100%; aspect-ratio: 16 / 10; overflow: hidden; background: #000; position: relative;
  display: flex; align-items: center; justify-content: center;
}}
.card-preview img {{
  width: 100%; height: 100%; object-fit: contain; background: #000; cursor: pointer;
  transition: transform 0.3s;
}}
.card-preview img:hover {{
  transform: scale(1.02);
}}
.card-content {{
  padding: 16px 20px; flex: 1; display: flex; flex-direction: column; justify-content: space-between;
}}
.card-title {{
  font-family: var(--mincho); font-size: 1.15rem; font-weight: 600; margin-bottom: 6px;
}}
.card-desc {{
  font-size: 0.85rem; color: var(--washi-dim); margin-bottom: 14px;
}}
.card-links {{
  display: flex; gap: 8px;
}}
.btn-sm {{
  font-size: 0.75rem; padding: 4px 10px; border-radius: 4px; text-decoration: none;
  border: 1px solid var(--washi-hairline); color: var(--washi); transition: all 0.15s;
}}
.btn-sm:hover {{
  border-color: var(--kaki); color: var(--kaki); background: rgba(208, 112, 63, 0.08);
}}

/* Lightbox Modal */
#lightbox {{
  position: fixed; inset: 0; background: rgba(0, 0, 0, 0.92); z-index: 1000;
  display: none; align-items: center; justify-content: center; padding: 24px;
}}
#lightbox.active {{ display: flex; }}
#lightbox img {{
  max-width: 95vw; max-height: 92vh; object-fit: contain; border-radius: 8px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.8);
}}
#lightboxClose {{
  position: absolute; top: 24px; right: 32px; color: #fff; font-size: 32px;
  background: none; border: none; cursor: pointer;
}}

/* Tab sections */
.tab-section {{ display: none; }}
.tab-section.active {{ display: block; }}
</style>
</head>
<body>
<div class="grain-overlay" aria-hidden="true"></div>

<header class="topbar">
  <div class="brand">
    <svg viewBox="0 0 44 44" fill="none">
      <path d="M29.2 11.2A13.2 13.2 0 1 0 30.4 20.8" stroke="#ece6da" stroke-width="2.4" stroke-linecap="round"/>
      <circle cx="30.3" cy="15.8" r="2" fill="#d0703f"/>
    </svg>
    <h1>TinCan 2.2 Design Systems</h1>
    <span class="pill">Updated Mockups</span>
  </div>
  <div class="nav-actions">
    <a href="/mesh" class="nav-link">🖥️ Mesh OS Desktop</a>
    <a href="/fono" class="nav-link">📱 Aeonik Fono</a>
    <a href="/ios" class="nav-link">📱 iOS Simulator</a>
    <a href="/car" class="nav-link">🚗 Car Head-Unit</a>
    <a href="/storyboard" class="nav-link">🎬 Storyboard</a>
  </div>
</header>

<div class="tabs-bar">
  <button class="tab-btn active" onclick="switchGalleryTab('aeonik')">🌿 Aeonik Celadon &amp; Ink (New Reskin)</button>
  <button class="tab-btn" onclick="switchGalleryTab('ios')">📱 Native iOS App (11 Mockups)</button>
  <button class="tab-btn" onclick="switchGalleryTab('car')">🚗 Car Head-Unit UI (5 Mockups)</button>
  <button class="tab-btn" onclick="switchGalleryTab('storyboard')">🎬 Zen Storyboard (7 Panels)</button>
  <button class="tab-btn" onclick="switchGalleryTab('desktop')">🖥️ Mesh OS Windows (3 Mockups)</button>
</div>

<main class="container">
  <!-- TAB 0: AEONIK RESKIN -->
  <div id="tab-aeonik" class="tab-section active">
    <div class="intro-panel">
      <div class="intro-text">
        <h2>Aeonik Celadon &amp; Ink Design System</h2>
        <p>Industrial minimalist design system (#ecf1e6 Celadon + 1px #111111 hairline borders). Features 4-quadrant desktop terminal (git status, system sparklines, filesystem tree) and Aeonik Fono mobile interface with circular gauge rings and schedule pill toggles.</p>
      </div>
      <div style="display: flex; gap: 10px; flex-wrap: wrap;">
        <a href="/mesh" class="btn-cta">⚡ Open Reskinned Terminal</a>
        <a href="/fono" class="btn-cta" style="background: #111;">📱 Open Aeonik Fono</a>
      </div>
    </div>
    <div class="grid-gallery">
      {''.join(f"""
      <div class="mockup-card">
        <div class="card-preview">
          <img src="{m['img']}" alt="{m['title']}" loading="lazy" onclick="openLightbox('{m['img']}')">
        </div>
        <div class="card-content">
          <div>
            <div class="card-title">{m['title']}</div>
            <div class="card-desc">{m['desc']}</div>
          </div>
          <div class="card-links">
            <a href="{m['img']}" target="_blank" class="btn-sm">View Full Res</a>
            <a href="{m['link']}" class="btn-sm">Open Live View</a>
          </div>
        </div>
      </div>
      """ for m in AEONIK_MOCKUPS)}
    </div>
  </div>

  <!-- TAB 1: iOS APP -->
  <div id="tab-ios" class="tab-section">
    <div class="intro-panel">
      <div class="intro-text">
        <h2>TinCan 2.2 · Native iOS App</h2>
        <p>Purpose-built zero-account native iOS app for iPhone. Secure Enclave Ed25519 keypair, TOFU messaging, live AI Brain Arena, CallKit WebRTC audio/video rooms, and StoreKit credit billing.</p>
      </div>
      <a href="/ios" class="btn-cta">📱 Launch Live iOS Simulator</a>
    </div>
    <div class="grid-gallery">
      {''.join(f"""
      <div class="mockup-card">
        <div class="card-preview">
          <img src="{m['img']}" alt="{m['title']}" loading="lazy" onclick="openLightbox('{m['img']}')">
        </div>
        <div class="card-content">
          <div>
            <div class="card-title">{m['title']}</div>
            <div class="card-desc">{m['desc']}</div>
          </div>
          <div class="card-links">
            <a href="{m['img']}" target="_blank" class="btn-sm">View Full Res</a>
            <a href="/ios/{m['id'] if not m['id'].startswith('sheet') else '02-inbox'}" class="btn-sm">Open in Simulator</a>
          </div>
        </div>
      </div>
      """ for m in IOS_MOCKUPS)}
    </div>
  </div>

  <!-- TAB 2: CAR UI -->
  <div id="tab-car" class="tab-section">
    <div class="intro-panel">
      <div class="intro-text">
        <h2>TinCan OS · Aftermarket Car Head-Unit UI</h2>
        <p>1280×720 landscape dashboard interface for vehicle cabins. Low-glare night Sumi-Dock, 76px+ touch targets, parked-safety gates, triple dashcam telemetry, and client-side mode switching.</p>
      </div>
      <a href="/car" class="btn-cta">🚗 Launch Live Car UI</a>
    </div>
    <div class="grid-gallery">
      {''.join(f"""
      <div class="mockup-card">
        <div class="card-preview">
          <img src="{m['img']}" alt="{m['title']}" loading="lazy" onclick="openLightbox('{m['img']}')">
        </div>
        <div class="card-content">
          <div>
            <div class="card-title">{m['title']}</div>
            <div class="card-desc">{m['desc']}</div>
          </div>
          <div class="card-links">
            <a href="{m['img']}" target="_blank" class="btn-sm">View Full Res</a>
            <a href="/car/{m['id'].replace('car-', '')}" class="btn-sm">Open in Head-Unit</a>
          </div>
        </div>
      </div>
      """ for m in CAR_MOCKUPS)}
    </div>
  </div>

  <!-- TAB 3: STORYBOARD -->
  <div id="tab-storyboard" class="tab-section">
    <div class="intro-panel">
      <div class="intro-text">
        <h2>TinCan 2.2 · Zen Narrative Storyboard</h2>
        <p>Master 3×2 contact sheet and 6 narrative audio drama scenes rendered in the Japanese Zen aesthetic (Sumi ink, Washi paper, Shippori Mincho typography).</p>
      </div>
      <a href="/storyboard" class="btn-cta">🎬 Launch Storyboard Player</a>
    </div>
    <div class="grid-gallery">
      {''.join(f"""
      <div class="mockup-card">
        <div class="card-preview">
          <img src="{m['img']}" alt="{m['title']}" loading="lazy" onclick="openLightbox('{m['img']}')">
        </div>
        <div class="card-content">
          <div>
            <div class="card-title">{m['title']}</div>
            <div class="card-desc">{m['desc']}</div>
          </div>
          <div class="card-links">
            <a href="{m['img']}" target="_blank" class="btn-sm">View Full Res</a>
          </div>
        </div>
      </div>
      """ for m in STORYBOARD_MOCKUPS)}
    </div>
  </div>

  <!-- TAB 4: MESH OS WINDOWS -->
  <div id="tab-desktop" class="tab-section">
    <div class="intro-panel">
      <div class="intro-text">
        <h2>TinCan Mesh OS · Zen Desktop Windows</h2>
        <p>All 11 tool windows refreshed into the Zen Interior Design System with responsive 2x2 grid window tiling and dedicated pop-out windows.</p>
      </div>
      <a href="/mesh" class="btn-cta">🖥️ Open Mesh OS Desktop</a>
    </div>
    <div class="grid-gallery">
      {''.join(f"""
      <div class="mockup-card">
        <div class="card-preview">
          <img src="{m['img']}" alt="{m['title']}" loading="lazy" onclick="openLightbox('{m['img']}')">
        </div>
        <div class="card-content">
          <div>
            <div class="card-title">{m['title']}</div>
            <div class="card-desc">{m['desc']}</div>
          </div>
          <div class="card-links">
            <a href="{m['img']}" target="_blank" class="btn-sm">View Full Res</a>
          </div>
        </div>
      </div>
      """ for m in DESKTOP_MOCKUPS)}
    </div>
  </div>
</main>

<div id="lightbox" onclick="closeLightbox()">
  <button id="lightboxClose" onclick="closeLightbox()">&times;</button>
  <img id="lightboxImg" src="" alt="Enlarged mockup">
</div>

<script>
function switchGalleryTab(tabKey) {{
  document.querySelectorAll('.tab-btn').forEach((btn, idx) => {{
    btn.classList.toggle('active', btn.getAttribute('onclick').includes(tabKey));
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
</script>
</body>
</html>
"""
