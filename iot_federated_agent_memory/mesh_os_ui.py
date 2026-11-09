"""TinCan Mesh OS — Multi-Window, Multiplayer & Gamified UI Specification.

Provides MESH_OS_HTML_UI with retro-futuristic spatial window manager,
top gamified telemetry HUD, interactive packet-flight background canvas,
multiplayer cursor layer, and multi-monitor pop-out window capabilities.
"""

MESH_OS_HTML_UI = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TinCan Mesh OS 2.1 — Multi-Window, Multiplayer &amp; AI Mesh Gateway</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    :root {
      --bg-color: #020617;
      --panel-bg: rgba(15, 23, 42, 0.92);
      --border-color: rgba(51, 65, 85, 0.7);
      --accent-color: #38bdf8;
    }

    body.theme-slate {
      --bg-color: #020617;
      --panel-bg: rgba(15, 23, 42, 0.92);
      --border-color: rgba(51, 65, 85, 0.7);
      --accent-color: #38bdf8;
    }

    body.theme-amber-crt {
      --bg-color: #120900;
      --panel-bg: rgba(26, 16, 3, 0.94);
      --border-color: rgba(245, 158, 11, 0.7);
      --accent-color: #f59e0b;
    }
    body.theme-amber-crt::after {
      content: " ";
      position: fixed;
      inset: 0;
      background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.28) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.03), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.03));
      background-size: 100% 3px, 6px 100%;
      pointer-events: none;
      z-index: 9999;
    }

    body.theme-crypto-emerald {
      --bg-color: #021a0f;
      --panel-bg: rgba(2, 36, 20, 0.93);
      --border-color: rgba(16, 185, 129, 0.75);
      --accent-color: #10b981;
    }

    body.theme-webrtc-cyan {
      --bg-color: #031726;
      --panel-bg: rgba(6, 30, 48, 0.92);
      --border-color: rgba(6, 182, 212, 0.8);
      --accent-color: #06b6d4;
    }

    body.theme-messiah-gold {
      --bg-color: #1a1403;
      --panel-bg: rgba(38, 28, 5, 0.95);
      --border-color: rgba(234, 179, 8, 0.85);
      --accent-color: #eab308;
    }

    /* Spatial Draggable Windows */
    .mesh-window {
      position: absolute;
      background: var(--panel-bg);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      box-shadow: 0 20px 45px -10px rgba(0, 0, 0, 0.7);
      transition: box-shadow 0.2s ease, opacity 0.2s ease;
      backdrop-filter: blur(12px);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      min-width: 340px;
    }

    .mesh-window.window-focused {
      border-color: var(--accent-color);
      box-shadow: 0 0 25px -4px var(--accent-color), 0 25px 50px -12px rgba(0, 0, 0, 0.85);
    }

    .mesh-window.maximized {
      top: 64px !important;
      left: 16px !important;
      right: 16px !important;
      bottom: 76px !important;
      width: calc(100vw - 32px) !important;
      height: calc(100vh - 140px) !important;
      z-index: 100 !important;
    }

    .mesh-window.popout-fullscreen {
      top: 60px !important;
      left: 8px !important;
      right: 8px !important;
      bottom: 8px !important;
      width: calc(100vw - 16px) !important;
      height: calc(100vh - 68px) !important;
      z-index: 100 !important;
    }

    .mesh-window.minimized .window-body {
      display: none !important;
    }

    .window-header {
      cursor: grab;
      user-select: none;
    }
    .window-header:active {
      cursor: grabbing;
    }

    /* Floating Reactions */
    @keyframes floatUpFade {
      0% {
        opacity: 1;
        transform: translateY(0) scale(0.8) rotate(0deg);
      }
      50% {
        opacity: 0.9;
        transform: translateY(-80px) scale(1.3) rotate(-10deg);
      }
      100% {
        opacity: 0;
        transform: translateY(-160px) scale(1.6) rotate(15deg);
      }
    }
    .reaction-particle {
      position: absolute;
      pointer-events: none;
      animation: floatUpFade 2s ease-out forwards;
      font-size: 2rem;
      z-index: 50;
    }

    /* Multiplayer Cursors */
    .remote-cursor {
      position: absolute;
      pointer-events: none;
      transition: transform 0.12s linear;
      z-index: 999;
    }

    /* Custom Scrollbar */
    ::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }
    ::-webkit-scrollbar-track {
      background: rgba(0, 0, 0, 0.2);
    }
    ::-webkit-scrollbar-thumb {
      background: rgba(148, 163, 184, 0.3);
      border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
      background: rgba(148, 163, 184, 0.5);
    }
  </style>
</head>
<body class="theme-slate bg-slate-950 text-slate-100 min-h-screen overflow-x-hidden font-sans select-none">

  <!-- Interactive Background Canvas: Peer Topology & Flying Packets -->
  <canvas id="meshTopologyCanvas" class="fixed inset-0 pointer-events-none z-0"></canvas>

  <!-- Multiplayer Peer Cursors Layer -->
  <div id="multiplayerCursorsLayer" class="fixed inset-0 pointer-events-none z-40 overflow-hidden"></div>

  <!-- Top Gamified Mesh OS HUD Bar -->
  <header id="meshOsHud" class="fixed top-0 left-0 right-0 h-14 bg-slate-950/90 border-b border-slate-800/80 backdrop-blur-md z-50 flex items-center justify-between px-3 sm:px-6 select-none">
    <div class="flex items-center gap-3">
      <div class="flex items-center gap-2">
        <span class="text-xl">🥫</span>
        <div>
          <span class="font-bold text-sm tracking-wide bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
            TinCan Mesh OS
          </span>
          <span class="hidden sm:inline-block text-[10px] text-slate-400 font-mono ml-1.5 px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800">v2.1</span>
        </div>
      </div>

      <!-- Readiness Tier Badge -->
      <div id="osTierBadge" class="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-800 shadow-sm flex items-center gap-1.5">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        <span>L5: Autonomous Mesh (94.5%)</span>
      </div>

      <!-- Live Squad XP Progress Bar -->
      <div class="hidden lg:flex items-center gap-2 font-mono text-xs">
        <div class="w-40 bg-slate-900 border border-slate-700/80 rounded-full h-2.5 overflow-hidden p-0.5">
          <div id="osXpBar" class="bg-gradient-to-r from-emerald-500 via-cyan-400 to-indigo-500 h-full rounded-full transition-all duration-500" style="width: 72%;"></div>
        </div>
        <span id="osXpText" class="text-cyan-300 text-[11px]">1,450 / 2,000 XP</span>
      </div>
    </div>

    <!-- HUD Right Controls -->
    <div class="flex items-center gap-2">
      <!-- Active Peer Count -->
      <span id="osPeerCount" class="text-xs font-mono px-2 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300 flex items-center gap-1">
        <span>👥</span> <span id="osPeerCountNum">2</span> <span class="hidden sm:inline">Active</span>
      </span>

      <!-- Unlockable Theme Selector -->
      <select id="osThemeSelect" onchange="changeTheme(this.value)" class="text-xs bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 font-mono cursor-pointer hover:border-slate-500 transition">
        <option value="slate">Theme: Slate Standard (L1)</option>
        <option value="amber-crt">Theme: Amber Phosphor CRT (L2)</option>
        <option value="crypto-emerald">Theme: Cryptographic Emerald (L3)</option>
        <option value="webrtc-cyan">Theme: WebRTC Cyan Pulse (L4)</option>
        <option value="messiah-gold">Theme: AI Messiah Cyber Gold (L5)</option>
      </select>

      <!-- Audio Chimes SFX Toggle -->
      <button id="osSfxBtn" onclick="toggleSfx()" class="text-xs font-mono px-2.5 py-1 rounded border border-emerald-800 bg-emerald-950 text-emerald-300 hover:brightness-110 transition active:scale-95">
        🔔 SFX: ON
      </button>

      <!-- Tile / Reset Windows -->
      <button id="osTileBtn" onclick="tileWindows()" class="hidden md:inline-flex text-xs font-mono px-2.5 py-1 rounded border border-indigo-800 bg-indigo-950 text-indigo-300 hover:bg-indigo-900 transition active:scale-95">
        🪟 Tile Windows
      </button>

      <!-- Pop Out Mode Guide -->
      <button onclick="togglePopoutGuide()" class="text-xs font-mono px-2 py-1 rounded border border-slate-700 bg-slate-900 text-slate-300 hover:bg-slate-800 transition">
        ↗ Pop Out Mode
      </button>
    </div>
  </header>

  <!-- Desktop Spatial Workspace (Houses Draggable .mesh-window Containers) -->
  <main id="desktopWorkspace" class="relative w-full min-h-screen pt-16 pb-24 px-3 sm:px-6 z-10 select-text">

    <!-- ===================================================================== -->
    <!-- Window 1: Terminal & Quickstart.exe -->
    <!-- ===================================================================== -->
    <div id="win-terminal" class="mesh-window w-[540px]" data-window-id="win-terminal" style="top: 72px; left: 24px; z-index: 20;">
      <div class="window-header flex items-center justify-between px-3 py-2 bg-slate-900/90 border-b border-slate-800">
        <div class="flex items-center gap-2">
          <span class="text-base">⚡</span>
          <span class="text-xs font-bold text-white font-mono">Terminal &amp; Quickstart.exe</span>
          <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
        </div>
        <div class="window-controls flex items-center gap-1.5 font-mono text-xs">
          <button onclick="openPopoutWindow('win-terminal')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[10px]" title="Pop out into separate monitor">↗ Pop Out</button>
          <button onclick="minimizeWindow('win-terminal')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">—</button>
          <button onclick="maximizeWindow('win-terminal')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">□</button>
        </div>
      </div>
      <div class="window-body p-4 space-y-4 max-h-[620px] overflow-y-auto">
        <div class="flex items-center justify-between">
          <h2 class="font-bold text-white text-sm">Quickstart &amp; One-Line Curl Commands</h2>
          <span class="text-[10px] bg-indigo-950 text-indigo-300 border border-indigo-800 px-2 py-0.5 rounded font-mono">Instant Terminal Access</span>
        </div>

        <div>
          <p class="text-xs text-slate-400 mb-1.5">1. Install &amp; setup peer mesh + TinCan CLI (no account needed):</p>
          <div class="bg-black/80 border border-slate-800 rounded-lg p-2.5 flex items-center justify-between font-mono text-xs">
            <code id="installCmd" class="text-emerald-400 select-all overflow-x-auto">curl -sSL https://iot-federated-agent-memory-production.up.railway.app/install.sh | bash</code>
            <button onclick="copyCommand('installCmd')" class="ml-3 px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-[11px] font-sans font-semibold transition shrink-0 active:scale-95">
              Copy Curl
            </button>
          </div>
        </div>

        <div>
          <p class="text-xs text-slate-400 mb-1.5">2. Live AI Model Prompt over OpenRouter Gateway (Gemini 2.5, Claude, Grok, GPT-4o):</p>
          <div class="bg-black/80 border border-slate-800 rounded-lg p-2.5 flex items-center justify-between font-mono text-xs">
            <code id="chatCmd" class="text-cyan-400 select-all overflow-x-auto">curl -s -X POST https://iot-federated-agent-memory-production.up.railway.app/api/chat -H "Content-Type: application/json" -d '{"prompt":"Hello world!"}'</code>
            <button onclick="copyCommand('chatCmd')" class="ml-3 px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[11px] font-sans font-semibold transition shrink-0 active:scale-95">
              Copy Curl
            </button>
          </div>
        </div>

        <div class="bg-slate-950/80 border border-slate-800 rounded-lg p-3 space-y-2">
          <div class="flex items-center justify-between">
            <h3 class="text-xs font-bold uppercase tracking-wider text-amber-400">TinCan Voice, Video &amp; Mesh Cheat Sheet</h3>
            <span class="text-[10px] font-mono text-slate-400">Watch the @nojuannobody walkthrough →</span>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 font-mono text-xs">
            <div class="p-2 bg-slate-900 rounded border border-slate-800">
              <div class="text-slate-400 text-[10px]">Speak + Send Remote TTS</div>
              <div class="text-emerald-300 mt-0.5">tincan say "Hey!" --to peer1</div>
            </div>
            <div class="p-2 bg-slate-900 rounded border border-slate-800">
              <div class="text-slate-400 text-[10px]">Live 2-Way Voice Call</div>
              <div class="text-cyan-300 mt-0.5">tincan call peer1 --voice-only</div>
            </div>
            <div class="p-2 bg-slate-900 rounded border border-slate-800">
              <div class="text-slate-400 text-[10px]">Live Video / Screenshare</div>
              <div class="text-indigo-300 mt-0.5">tincan call peer1 --screen</div>
            </div>
            <div class="p-2 bg-slate-900 rounded border border-slate-800">
              <div class="text-slate-400 text-[10px]">Approve Queued Peer Action</div>
              <div class="text-amber-300 mt-0.5">tincan trigger 1</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- Window 2: Relay TV Watch Party.app -->
    <!-- ===================================================================== -->
    <div id="win-tv" class="mesh-window w-[520px]" data-window-id="win-tv" style="top: 72px; right: 24px; z-index: 21;">
      <div class="window-header flex items-center justify-between px-3 py-2 bg-slate-900/90 border-b border-slate-800">
        <div class="flex items-center gap-2">
          <span class="text-base">📺</span>
          <span class="text-xs font-bold text-white font-mono">Relay TV Watch Party.app</span>
          <span class="w-2 h-2 rounded-full bg-pink-500"></span>
        </div>
        <div class="window-controls flex items-center gap-1.5 font-mono text-xs">
          <button onclick="openPopoutWindow('win-tv')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[10px]" title="Pop out into separate monitor">↗ Pop Out</button>
          <button onclick="minimizeWindow('win-tv')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">—</button>
          <button onclick="maximizeWindow('win-tv')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">□</button>
        </div>
      </div>
      <div id="tv" class="window-body p-4 space-y-3 max-h-[620px] overflow-y-auto">
        <div class="w-full flex items-center justify-between">
          <div>
            <h2 class="font-bold text-white text-sm">Relay Video Channel &amp; Collection</h2>
            <p id="nowPlayingTitle" class="text-[11px] text-slate-400">Self-hosted Native MP4 · <span class="text-pink-400 font-mono">@nojuannobody</span></p>
          </div>
          <span id="playlistCounterBadge" class="text-[10px] bg-pink-950 text-pink-300 border border-pink-800 px-2.5 py-0.5 rounded-full font-mono uppercase">1 / 1 · Loop</span>
        </div>

        <!-- Video Player with Overlay for Multiplayer Floating Reactions -->
        <div class="relative w-full flex flex-col items-center justify-center overflow-hidden rounded-lg bg-black border border-slate-800 h-[380px]">
          <video
            id="relayNativeVideo"
            src="/videos/7705677376465767711.mp4"
            autoplay
            loop
            muted
            playsinline
            controls
            class="w-full h-full object-contain bg-black"
          ></video>
          <!-- Floating Reaction Particles Spawn In This Overlay -->
          <div id="reactionOverlay" class="absolute inset-0 pointer-events-none overflow-hidden"></div>
        </div>

        <!-- Watch Party Reactions Bar & Room Sync -->
        <div class="p-2.5 bg-slate-950/80 border border-pink-900/50 rounded-lg flex items-center justify-between gap-2">
          <div class="flex items-center gap-1.5 text-sm">
            <span class="text-[11px] font-mono text-slate-400 mr-1">React:</span>
            <button onclick="sendReaction('🔥')" class="px-2 py-1 bg-slate-900 hover:bg-pink-950 rounded border border-slate-700 hover:border-pink-600 transition active:scale-125">🔥</button>
            <button onclick="sendReaction('🥫')" class="px-2 py-1 bg-slate-900 hover:bg-pink-950 rounded border border-slate-700 hover:border-pink-600 transition active:scale-125">🥫</button>
            <button onclick="sendReaction('⚡')" class="px-2 py-1 bg-slate-900 hover:bg-pink-950 rounded border border-slate-700 hover:border-pink-600 transition active:scale-125">⚡</button>
            <button onclick="sendReaction('🧠')" class="px-2 py-1 bg-slate-900 hover:bg-pink-950 rounded border border-slate-700 hover:border-pink-600 transition active:scale-125">🧠</button>
            <button onclick="sendReaction('🚀')" class="px-2 py-1 bg-slate-900 hover:bg-pink-950 rounded border border-slate-700 hover:border-pink-600 transition active:scale-125">🚀</button>
          </div>
          <button onclick="syncWatchParty()" class="px-3 py-1 bg-pink-900/70 hover:bg-pink-800 border border-pink-700 text-pink-200 rounded text-xs font-mono transition active:scale-95 shrink-0 flex items-center gap-1">
            <span>🔗</span> <span>Sync Party</span>
          </button>
        </div>

        <!-- Playlist Controls -->
        <div class="flex items-center justify-between gap-2 text-xs font-mono">
          <div class="flex items-center gap-1.5">
            <button onclick="prevPlaylistVideo()" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 transition">⏮ Prev</button>
            <button onclick="nextPlaylistVideo()" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 transition">Next ⏭</button>
            <button id="autoRotateBtn" onclick="toggleAutoRotate()" class="px-2.5 py-1 bg-emerald-950 text-emerald-300 rounded border border-emerald-800 transition">🔁 Auto-Loop: ON</button>
          </div>
          <button id="soundToggleBtn" onclick="toggleVideoSound()" class="px-2.5 py-1 bg-pink-950 hover:bg-pink-900 text-pink-300 rounded border border-pink-800 transition">
            🔊 Tap to Unmute
          </button>
        </div>

        <!-- Collection Queue List -->
        <div id="playlistQueue" class="space-y-1 max-h-24 overflow-y-auto pr-1 text-xs font-mono">
          <!-- Populated dynamically from /api/playlist -->
        </div>

        <!-- Add Video Form -->
        <div class="pt-2 border-t border-slate-800 flex gap-1.5 text-xs">
          <input id="newVideoInput" type="text" placeholder="Paste video URL or ID to ingest MP4 into relay collection..." class="flex-1 bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white font-mono placeholder:text-slate-600">
          <button onclick="addVideoToPlaylist()" class="px-3 py-1.5 bg-pink-600 hover:bg-pink-500 text-white font-semibold rounded transition shrink-0 active:scale-95">
            + Ingest MP4
          </button>
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- Window 3: AI Brain Router & Model Arena.app -->
    <!-- ===================================================================== -->
    <div id="win-arena" class="mesh-window w-[560px]" data-window-id="win-arena" style="top: 720px; left: 24px; z-index: 22;">
      <div class="window-header flex items-center justify-between px-3 py-2 bg-slate-900/90 border-b border-slate-800">
        <div class="flex items-center gap-2">
          <span class="text-base">🧠</span>
          <span class="text-xs font-bold text-white font-mono">AI Brain Router &amp; Arena.app</span>
          <span class="w-2 h-2 rounded-full bg-indigo-400"></span>
        </div>
        <div class="window-controls flex items-center gap-1.5 font-mono text-xs">
          <button onclick="openPopoutWindow('win-arena')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[10px]" title="Pop out into separate monitor">↗ Pop Out</button>
          <button onclick="minimizeWindow('win-arena')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">—</button>
          <button onclick="maximizeWindow('win-arena')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">□</button>
        </div>
      </div>
      <div class="window-body p-4 space-y-4 max-h-[620px] overflow-y-auto">
        <div class="flex flex-wrap justify-between items-center gap-2">
          <div>
            <h2 class="text-sm font-bold text-white flex items-center gap-2">
              <span>💳</span> OpenRouter Cost, Spend &amp; Credit Dashboard
            </h2>
            <p class="text-[11px] text-slate-400">Live account credits, lifetime spend, key usage, and per-model token pricing</p>
          </div>
          <div id="analyticsHeader" class="text-right text-[11px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800 px-2.5 py-1 rounded-md">
            Fetching live OpenRouter billing...
          </div>
        </div>

        <div class="grid grid-cols-2 gap-2 text-xs font-mono">
          <div class="p-2.5 bg-slate-950/80 border border-slate-800 rounded-lg">
            <div class="text-slate-400 text-[10px]">OpenRouter Remaining Balance</div>
            <div id="orRemaining" class="text-base font-bold text-emerald-400 mt-0.5">--</div>
            <div id="orCreditsTotal" class="text-[10px] text-slate-500">of -- credits</div>
          </div>
          <div class="p-2.5 bg-slate-950/80 border border-slate-800 rounded-lg">
            <div class="text-slate-400 text-[10px]">Total Lifetime Spend</div>
            <div id="orTotalUsage" class="text-base font-bold text-amber-400 mt-0.5">--</div>
            <div class="text-[10px] text-slate-500">Account aggregate</div>
          </div>
          <div class="p-2.5 bg-slate-950/80 border border-slate-800 rounded-lg">
            <div class="text-slate-400 text-[10px]">Active Key Usage</div>
            <div id="orKeyUsage" class="text-base font-bold text-cyan-400 mt-0.5">--</div>
            <div id="orKeyToday" class="text-[10px] text-slate-500">Today: --</div>
          </div>
          <div class="p-2.5 bg-slate-950/80 border border-slate-800 rounded-lg">
            <div class="text-slate-400 text-[10px]">Key Budget Cap</div>
            <div id="orKeyLimitRem" class="text-base font-bold text-indigo-400 mt-0.5">--</div>
            <div id="orKeyLabel" class="text-[10px] text-slate-500 truncate">Key: --</div>
          </div>
        </div>

        <!-- Hidden elements to preserve backward compatibility for top cards -->
        <div class="hidden">
          <div id="topBalanceValue">Loading...</div>
          <div id="topBalanceSub">Live OpenRouter Credit Pool</div>
        </div>

        <!-- Live Provider & Cost Cards Grid -->
        <div id="providerCards" class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <!-- Injected via JavaScript -->
        </div>

        <!-- Configure / Swap Model Form -->
        <div class="bg-slate-950/70 border border-slate-800 rounded-lg p-3 space-y-2.5">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <h3 class="text-xs font-semibold text-slate-200">Configure / Swap Model Target</h3>
            <span id="currentTargetModelBadge" class="text-[10px] font-mono bg-indigo-950/80 text-indigo-300 border border-indigo-800 px-2 py-0.5 rounded">
              Active: gemini-brain → google/gemini-2.5-flash
            </span>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-4 gap-2 text-xs">
            <div>
              <label class="block text-slate-400 mb-1 text-[11px]">Target Alias</label>
              <select id="aliasSelect" onchange="syncSelectedAliasModel(true)" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white font-mono">
                <option value="gemini-brain">gemini-brain → google/gemini-2.5-flash</option>
                <option value="claude-brain">claude-brain → anthropic/claude-sonnet-5.5</option>
                <option value="grok-brain">grok-brain → x-ai/grok-4.7</option>
                <option value="openai-brain">openai-brain → openai/gpt-4o</option>
              </select>
            </div>
            <div class="sm:col-span-2">
              <label class="block text-slate-400 mb-1 text-[11px]">OpenRouter Model ID</label>
              <input type="text" id="modelInput" placeholder="e.g. meta-llama/llama-3.3-70b-instruct" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white font-mono placeholder:text-slate-600">
            </div>
            <div class="flex items-end">
              <button onclick="updateModel()" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded px-2.5 py-1.5 transition active:scale-95 text-xs">
                Update Model
              </button>
            </div>
          </div>
          <div class="flex flex-wrap items-center gap-1 pt-1 text-[10px] font-mono">
            <span class="text-slate-500 mr-1">Quick Swap:</span>
            <button type="button" onclick="quickPickModel('google/gemini-2.5-pro')" class="px-1.5 py-0.5 rounded bg-slate-900 hover:bg-indigo-950 text-slate-300 border border-slate-700">gemini-2.5-pro</button>
            <button type="button" onclick="quickPickModel('anthropic/claude-3.7-sonnet')" class="px-1.5 py-0.5 rounded bg-slate-900 hover:bg-indigo-950 text-slate-300 border border-slate-700">claude-3.7-sonnet</button>
            <button type="button" onclick="quickPickModel('x-ai/grok-3')" class="px-1.5 py-0.5 rounded bg-slate-900 hover:bg-indigo-950 text-slate-300 border border-slate-700">x-ai/grok-3</button>
            <button type="button" onclick="quickPickModel('openai/gpt-4o')" class="px-1.5 py-0.5 rounded bg-slate-900 hover:bg-indigo-950 text-slate-300 border border-slate-700">openai/gpt-4o</button>
            <button type="button" onclick="quickPickModel('meta-llama/llama-3.3-70b-instruct')" class="px-1.5 py-0.5 rounded bg-slate-900 hover:bg-indigo-950 text-slate-300 border border-slate-700">llama-3.3-70b</button>
            <button type="button" onclick="quickPickModel('deepseek/deepseek-r1')" class="px-1.5 py-0.5 rounded bg-slate-900 hover:bg-indigo-950 text-slate-300 border border-slate-700">deepseek-r1</button>
          </div>
          <p id="updateFeedback" class="text-xs mt-2 font-mono hidden"></p>
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- Window 4: WebRTC Comms & Screenshare Studio.app -->
    <!-- ===================================================================== -->
    <div id="win-comms" class="mesh-window w-[540px]" data-window-id="win-comms" style="top: 720px; right: 24px; z-index: 23;">
      <div class="window-header flex items-center justify-between px-3 py-2 bg-slate-900/90 border-b border-slate-800">
        <div class="flex items-center gap-2">
          <span class="text-base">📹</span>
          <span class="text-xs font-bold text-white font-mono">WebRTC Comms Studio.app</span>
          <span class="w-2 h-2 rounded-full bg-cyan-400"></span>
        </div>
        <div class="window-controls flex items-center gap-1.5 font-mono text-xs">
          <button onclick="openPopoutWindow('win-comms')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[10px]" title="Pop out into separate monitor">↗ Pop Out</button>
          <button onclick="minimizeWindow('win-comms')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">—</button>
          <button onclick="maximizeWindow('win-comms')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">□</button>
        </div>
      </div>
      <div id="call" class="window-body p-4 space-y-3 max-h-[620px] overflow-y-auto">
        <div class="flex flex-wrap justify-between items-center gap-2">
          <div>
            <h2 class="text-xs font-bold text-white uppercase tracking-wider">P2P Encrypted Mesh Comms</h2>
            <p class="text-[11px] text-slate-400">Multi-peer voice calling, H.264 video &amp; desktop screenshare</p>
          </div>
          <div class="flex items-center gap-1.5 text-xs font-mono">
            <span class="text-slate-400 text-[11px]">Room:</span>
            <input id="roomInput" type="text" value="main" class="bg-slate-950 border border-slate-700 rounded px-2 py-0.5 text-cyan-300 w-20 text-xs">
            <button onclick="copyInviteLink()" class="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded text-slate-200 transition text-[11px]">
              Copy Link
            </button>
            <span id="callStatusBadge" class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[11px]">Idle</span>
          </div>
        </div>

        <!-- Call Action Buttons -->
        <div class="flex flex-wrap gap-1.5 text-xs font-mono">
          <button onclick="startCall('video')" class="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded transition active:scale-95">
            🎥 Video + Voice
          </button>
          <button onclick="startCall('voice')" class="px-2.5 py-1 bg-teal-600 hover:bg-teal-500 text-white font-semibold rounded transition active:scale-95">
            🎙️ Voice Call
          </button>
          <button onclick="startScreenShare()" class="px-2.5 py-1 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold rounded transition active:scale-95">
            🖥️ Screen Share
          </button>
          <button id="muteBtn" onclick="toggleMute()" class="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded border border-slate-700 transition">
            🔇 Mute Mic
          </button>
          <button id="camBtn" onclick="toggleCamera()" class="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded border border-slate-700 transition">
            📷 Toggle Cam
          </button>
          <button onclick="hangupCall()" class="px-2.5 py-1 bg-rose-700 hover:bg-rose-600 text-white font-semibold rounded transition ml-auto active:scale-95">
            ⏹ End
          </button>
        </div>

        <!-- Video Viewports -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <div class="relative bg-black rounded-lg border border-slate-800 overflow-hidden aspect-video flex items-center justify-center">
            <video id="localVideo" autoplay playsinline muted class="w-full h-full object-cover"></video>
            <div class="absolute bottom-1.5 left-1.5 px-1.5 py-0.5 bg-black/75 rounded text-[10px] font-mono text-emerald-300 border border-emerald-900">
              Local (<span id="localPeerLabel">you</span>)
            </div>
          </div>
          <div class="relative bg-black rounded-lg border border-slate-800 overflow-hidden aspect-video flex items-center justify-center">
            <video id="remoteVideo" autoplay playsinline class="w-full h-full object-cover"></video>
            <div class="absolute bottom-1.5 left-1.5 px-1.5 py-0.5 bg-black/75 rounded text-[10px] font-mono text-cyan-300 border border-cyan-900">
              Remote (<span id="remotePeerLabel">waiting for peer...</span>)
            </div>
          </div>
        </div>

        <!-- Active UDP Streams -->
        <div class="pt-2 border-t border-slate-800">
          <div class="text-[11px] font-semibold text-slate-400 mb-1.5">Active Room &amp; UDP Streams</div>
          <div id="roomPeersGrid" class="space-y-1.5 text-xs font-mono">
            <div class="p-2 bg-slate-800/60 rounded border border-slate-700 flex justify-between items-center">
              <span class="text-white">Mac Studio (M1 Max)</span>
              <span class="bg-emerald-900 text-emerald-300 px-1.5 py-0.5 rounded text-[10px]">UDP: 50004</span>
            </div>
            <div class="p-2 bg-slate-800/60 rounded border border-slate-700 flex justify-between items-center">
              <span class="text-white">Collaborator MacBook</span>
              <span class="bg-cyan-900 text-cyan-300 px-1.5 py-0.5 rounded text-[10px]">UDP: 50006</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- Window 5: Quests, Arena & Operator Leaderboard.app -->
    <!-- ===================================================================== -->
    <div id="win-quests" class="mesh-window w-[1100px] max-w-full" data-window-id="win-quests" style="top: 1380px; left: 24px; z-index: 24;">
      <div class="window-header flex items-center justify-between px-3 py-2 bg-slate-900/90 border-b border-slate-800">
        <div class="flex items-center gap-2">
          <span class="text-base">🎯</span>
          <span class="text-xs font-bold text-white font-mono">Quests, Arena &amp; Operator Leaderboard.app</span>
          <span class="w-2 h-2 rounded-full bg-amber-400"></span>
        </div>
        <div class="window-controls flex items-center gap-1.5 font-mono text-xs">
          <button onclick="openPopoutWindow('win-quests')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[10px]" title="Pop out into separate monitor">↗ Pop Out</button>
          <button onclick="minimizeWindow('win-quests')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">—</button>
          <button onclick="maximizeWindow('win-quests')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">□</button>
        </div>
      </div>
      <div class="window-body p-4 space-y-6 max-h-[750px] overflow-y-auto">

        <!-- Top Section: Cooperative Quest Deck -->
        <div>
          <div class="flex items-center justify-between mb-3">
            <div>
              <h2 class="text-sm font-bold text-white flex items-center gap-2">
                <span>⚔️</span> Cooperative Quest Deck &amp; L1 $\rightarrow$ L5 Ascension Loop
              </h2>
              <p class="text-xs text-slate-400">Complete peer actions to award Squad XP, unlock desktop themes, and level up the mesh.</p>
            </div>
            <span class="text-xs font-mono text-amber-400 bg-amber-950/60 border border-amber-800 px-2.5 py-1 rounded">
              Active Squad Quests
            </span>
          </div>

          <div id="questDeckGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <!-- Dynamically populated or rendered via JS from /api/mesh/state -->
            <div class="p-3 bg-slate-950/80 rounded-lg border border-slate-800 flex flex-col justify-between space-y-2">
              <div>
                <div class="flex justify-between items-center">
                  <span class="font-bold text-xs text-emerald-400 font-mono">L1 Sealed Courier</span>
                  <span class="text-[10px] bg-emerald-950 text-emerald-300 border border-emerald-800 px-1.5 py-0.5 rounded font-mono">+100 XP</span>
                </div>
                <p class="text-xs text-slate-300 mt-1">Dispatch an Ed25519 sealed envelope through TinCan Blind Relay.</p>
              </div>
              <button onclick="triggerQuestAction('sealed_courier')" class="w-full py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-mono font-semibold transition active:scale-95">
                🥫 Dispatch Sealed Ping (+100 XP)
              </button>
            </div>

            <div class="p-3 bg-slate-950/80 rounded-lg border border-slate-800 flex flex-col justify-between space-y-2">
              <div>
                <div class="flex justify-between items-center">
                  <span class="font-bold text-xs text-indigo-400 font-mono">L4 Synapse Battle</span>
                  <span class="text-[10px] bg-indigo-950 text-indigo-300 border border-indigo-800 px-1.5 py-0.5 rounded font-mono">+150 XP</span>
                </div>
                <p class="text-xs text-slate-300 mt-1">Run dual completion duel and vote for winning AI brain.</p>
              </div>
              <button onclick="triggerQuestAction('arena_vote')" class="w-full py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-mono font-semibold transition active:scale-95">
                🧠 Run Blind Arena Battle (+150 XP)
              </button>
            </div>

            <div class="p-3 bg-slate-950/80 rounded-lg border border-slate-800 flex flex-col justify-between space-y-2">
              <div>
                <div class="flex justify-between items-center">
                  <span class="font-bold text-xs text-amber-400 font-mono">L5 HITL Trigger</span>
                  <span class="text-[10px] bg-amber-950 text-amber-300 border border-amber-800 px-1.5 py-0.5 rounded font-mono">+200 XP</span>
                </div>
                <p class="text-xs text-slate-300 mt-1">Execute human-in-the-loop approved peer command.</p>
              </div>
              <button onclick="triggerQuestAction('coop_action')" class="w-full py-1.5 bg-amber-600 hover:bg-amber-500 text-white rounded text-xs font-mono font-semibold transition active:scale-95">
                ⚡ Trigger Co-Op Action (+200 XP)
              </button>
            </div>
          </div>
        </div>

        <!-- Middle Section: Side-by-Side AI Brain Arena -->
        <div id="arenaBattleBox" class="bg-slate-950/90 border border-indigo-900/60 rounded-xl p-4 space-y-3">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 class="text-xs font-bold uppercase tracking-wider text-indigo-300 flex items-center gap-1.5">
                <span>⚔️</span> Side-by-Side AI Brain Arena Duel
              </h3>
              <p class="text-[11px] text-slate-400">Dispatch dual completion to Gemini 2.5 vs Claude 3.7 and vote for the best response (+150 XP).</p>
            </div>
            <span class="text-[11px] font-mono text-cyan-400 bg-cyan-950/60 border border-cyan-800 px-2 py-0.5 rounded">
              Blind Duel Protocol
            </span>
          </div>

          <div class="flex gap-2">
            <input id="arenaPromptInput" type="text" value="Explain zero-knowledge proofs and federated CRDT meshes in two concise sentences." class="flex-1 bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-xs text-white font-mono placeholder:text-slate-600">
            <button onclick="runArenaBattle()" class="px-4 py-1.5 bg-gradient-to-r from-indigo-600 to-cyan-600 hover:brightness-110 text-white font-semibold rounded text-xs transition active:scale-95 shrink-0 flex items-center gap-1.5">
              <span>⚔️</span> <span>Battle 2 Brains</span>
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
            <!-- Brain A: Gemini -->
            <div class="p-3 bg-slate-900/90 rounded-lg border border-slate-800 flex flex-col justify-between space-y-2">
              <div class="flex justify-between items-center pb-1.5 border-b border-slate-800">
                <span class="font-bold text-xs text-emerald-300 font-mono">Brain A (gemini-brain)</span>
                <span class="text-[10px] text-slate-400 font-mono">Gemini 2.5 Flash</span>
              </div>
              <div id="arenaResultA" class="text-xs font-mono text-slate-200 min-h-[90px] max-h-[160px] overflow-y-auto whitespace-pre-wrap bg-black/40 p-2.5 rounded">
                Click "Battle 2 Brains" above to dispatch simultaneous prompts...
              </div>
              <button onclick="voteArenaWinner('gemini-brain')" class="w-full py-1.5 bg-emerald-700/80 hover:bg-emerald-600 text-white font-semibold rounded text-xs transition active:scale-95 font-mono">
                🏆 Vote Brain A (+150 XP)
              </button>
            </div>

            <!-- Brain B: Claude -->
            <div class="p-3 bg-slate-900/90 rounded-lg border border-slate-800 flex flex-col justify-between space-y-2">
              <div class="flex justify-between items-center pb-1.5 border-b border-slate-800">
                <span class="font-bold text-xs text-cyan-300 font-mono">Brain B (claude-brain)</span>
                <span class="text-[10px] text-slate-400 font-mono">Claude 3.7 Sonnet</span>
              </div>
              <div id="arenaResultB" class="text-xs font-mono text-slate-200 min-h-[90px] max-h-[160px] overflow-y-auto whitespace-pre-wrap bg-black/40 p-2.5 rounded">
                Click "Battle 2 Brains" above to dispatch simultaneous prompts...
              </div>
              <button onclick="voteArenaWinner('claude-brain')" class="w-full py-1.5 bg-cyan-700/80 hover:bg-cyan-600 text-white font-semibold rounded text-xs transition active:scale-95 font-mono">
                🏆 Vote Brain B (+150 XP)
              </button>
            </div>
          </div>
        </div>

        <!-- Bottom Section: Live Operator Leaderboard -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
              <span>🏆</span> Live Mesh Operator Leaderboard
            </h3>
            <span class="text-[11px] font-mono text-slate-400">Ranked by Lifetime XP</span>
          </div>

          <div class="bg-slate-950/80 border border-slate-800 rounded-lg overflow-hidden">
            <table class="w-full text-left text-xs font-mono">
              <thead class="bg-slate-900 text-slate-400 border-b border-slate-800">
                <tr>
                  <th class="px-3 py-2">Rank</th>
                  <th class="px-3 py-2">Operator Peer</th>
                  <th class="px-3 py-2">Readiness Tier</th>
                  <th class="px-3 py-2">Badges</th>
                  <th class="px-3 py-2 text-right">Squad XP</th>
                </tr>
              </thead>
              <tbody id="operatorLeaderboard" class="divide-y divide-slate-800/60">
                <tr>
                  <td class="px-3 py-2 text-amber-400 font-bold">#1</td>
                  <td class="px-3 py-2 text-white font-bold">Mac Studio (M1 Max)</td>
                  <td class="px-3 py-2 text-emerald-400">L5: Autonomous Mesh</td>
                  <td class="px-3 py-2">
                    <span class="px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-[10px]">🟢 Initiate</span>
                    <span class="px-1.5 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 text-[10px]">🥫 Postmaster</span>
                  </td>
                  <td class="px-3 py-2 text-right text-cyan-300 font-bold">850 XP</td>
                </tr>
                <tr>
                  <td class="px-3 py-2 text-slate-400 font-bold">#2</td>
                  <td class="px-3 py-2 text-slate-200">Collaborator MacBook</td>
                  <td class="px-3 py-2 text-emerald-400">L4: CRDT Gossip</td>
                  <td class="px-3 py-2">
                    <span class="px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-[10px]">🟢 Initiate</span>
                  </td>
                  <td class="px-3 py-2 text-right text-cyan-300 font-bold">600 XP</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>

  </main>

  <!-- Bottom OS Dock -->
  <footer id="meshOsDock" class="fixed bottom-3 left-1/2 -translate-x-1/2 z-50 bg-slate-900/90 border border-slate-700/80 rounded-2xl px-3 py-2 flex items-center gap-1.5 sm:gap-2.5 backdrop-blur-md shadow-2xl select-none font-sans">
    <button onclick="toggleWindow('win-terminal')" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="Terminal & Quickstart">
      <span>⚡</span> <span class="hidden md:inline">Terminal</span>
    </button>
    <button onclick="toggleWindow('win-tv')" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="Relay Watch Party TV">
      <span>📺</span> <span class="hidden md:inline">Watch Party TV</span>
    </button>
    <button onclick="toggleWindow('win-arena')" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="AI Brain Router & Arena">
      <span>🧠</span> <span class="hidden md:inline">AI Arena</span>
    </button>
    <button onclick="toggleWindow('win-comms')" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="WebRTC Comms Studio">
      <span>📹</span> <span class="hidden md:inline">WebRTC Comms</span>
    </button>
    <button onclick="toggleWindow('win-quests')" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="Quests, Arena & Leaderboard">
      <span>🎯</span> <span class="hidden md:inline">Quests &amp; Leaderboard</span>
    </button>
    <div class="h-5 w-px bg-slate-700 mx-1"></div>
    <button onclick="fireTestPacket()" class="px-3 py-1.5 bg-gradient-to-r from-emerald-600 to-cyan-600 hover:brightness-110 text-white rounded-xl text-xs font-mono font-semibold transition active:scale-95 flex items-center gap-1 shadow-md" title="Launch animated test packet across mesh topology">
      <span>🥫</span> <span>Fire Test Packet</span>
    </button>
  </footer>

  <!-- ===================================================================== -->
  <!-- Master JavaScript Engine for TinCan Mesh OS -->
  <!-- ===================================================================== -->
  <script>
    // URL Params & Core Identity
    const urlParams = new URLSearchParams(window.location.search);
    const myPeerId = urlParams.get('peer') || ('peer-' + Math.random().toString(36).substring(2, 8));
    const currentRoom = urlParams.get('room') || 'main';
    const singleWindowParam = urlParams.get('window');

    document.getElementById('roomInput').value = currentRoom;
    document.getElementById('localPeerLabel').innerText = myPeerId;

    // Cross-Window BroadcastChannel ('tincan-mesh-bus')
    const meshBus = new BroadcastChannel('tincan-mesh-bus');

    // WebAudio SFX Engine (Pentatonic Major Chords)
    let audioCtx = null;
    let sfxEnabled = true;

    function initAudio() {
      if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (audioCtx.state === 'suspended') {
        audioCtx.resume();
      }
    }

    function playXpChime() {
      if (!sfxEnabled) return;
      initAudio();
      if (!audioCtx) return;
      const now = audioCtx.currentTime;
      const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
      notes.forEach((freq, idx) => {
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, now + idx * 0.07);
        gain.gain.setValueAtTime(0.08, now + idx * 0.07);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + idx * 0.07 + 0.32);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start(now + idx * 0.07);
        osc.stop(now + idx * 0.07 + 0.35);
      });
    }

    function toggleSfx() {
      sfxEnabled = !sfxEnabled;
      const btn = document.getElementById('osSfxBtn');
      btn.innerText = sfxEnabled ? '🔔 SFX: ON' : '🔕 SFX: OFF';
      btn.className = sfxEnabled
        ? 'text-xs font-mono px-2.5 py-1 rounded border border-emerald-800 bg-emerald-950 text-emerald-300 hover:brightness-110 transition active:scale-95'
        : 'text-xs font-mono px-2.5 py-1 rounded border border-slate-700 bg-slate-900 text-slate-400 hover:brightness-110 transition active:scale-95';
      if (sfxEnabled) playXpChime();
    }

    // Theme Switcher
    function changeTheme(themeName) {
      document.body.className = `theme-${themeName} bg-slate-950 text-slate-100 min-h-screen overflow-x-hidden font-sans select-none`;
      document.getElementById('osThemeSelect').value = themeName;
    }

    // Window Manager: Draggable, Focus, Minimize, Maximize, Pop Out
    let highestZ = 30;
    const allWindows = ['win-terminal', 'win-tv', 'win-arena', 'win-comms', 'win-quests'];

    function bringToFront(winEl) {
      highestZ += 1;
      winEl.style.zIndex = highestZ;
      document.querySelectorAll('.mesh-window').forEach(w => w.classList.remove('window-focused'));
      winEl.classList.add('window-focused');
    }

    function makeWindowDraggable(winEl) {
      const header = winEl.querySelector('.window-header');
      if (!header) return;

      winEl.addEventListener('mousedown', () => bringToFront(winEl));

      header.addEventListener('mousedown', (e) => {
        if (e.target.tagName === 'BUTTON' || winEl.classList.contains('maximized') || winEl.classList.contains('popout-fullscreen')) {
          return;
        }
        bringToFront(winEl);
        let startX = e.clientX;
        let startY = e.clientY;
        const rect = winEl.getBoundingClientRect();
        let origLeft = rect.left;
        let origTop = rect.top;

        function onMouseMove(moveEvent) {
          const dx = moveEvent.clientX - startX;
          const dy = moveEvent.clientY - startY;
          winEl.style.left = `${Math.max(10, origLeft + dx)}px`;
          winEl.style.top = `${Math.max(60, origTop + dy)}px`;
          winEl.style.right = 'auto';
        }

        function onMouseUp() {
          window.removeEventListener('mousemove', onMouseMove);
          window.removeEventListener('mouseup', onMouseUp);
        }

        window.addEventListener('mousemove', onMouseMove);
        window.addEventListener('mouseup', onMouseUp);
      });
    }

    function toggleWindow(winId) {
      const win = document.getElementById(winId);
      if (!win) return;
      if (win.style.display === 'none') {
        win.style.display = 'flex';
        win.classList.remove('minimized');
        bringToFront(win);
      } else if (win.classList.contains('minimized')) {
        win.classList.remove('minimized');
        bringToFront(win);
      } else {
        bringToFront(win);
      }
    }

    function minimizeWindow(winId) {
      const win = document.getElementById(winId);
      if (!win) return;
      win.classList.toggle('minimized');
    }

    function maximizeWindow(winId) {
      const win = document.getElementById(winId);
      if (!win) return;
      win.classList.toggle('maximized');
      bringToFront(win);
    }

    function openPopoutWindow(winId) {
      const url = `/?window=${encodeURIComponent(winId)}&room=${encodeURIComponent(currentRoom)}`;
      window.open(url, `_blank_${winId}`, 'width=1120,height=760,menubar=no,toolbar=no,location=no');
    }

    function tileWindows() {
      const isMobile = window.innerWidth < 768;
      const winTerm = document.getElementById('win-terminal');
      const winTv = document.getElementById('win-tv');
      const winArena = document.getElementById('win-arena');
      const winComms = document.getElementById('win-comms');
      const winQuests = document.getElementById('win-quests');

      allWindows.forEach(id => {
        const w = document.getElementById(id);
        if (w) {
          w.style.display = 'flex';
          w.classList.remove('maximized', 'minimized');
        }
      });

      if (isMobile) {
        let top = 70;
        [winTerm, winTv, winArena, winComms, winQuests].forEach(w => {
          if (!w) return;
          w.style.left = '10px';
          w.style.right = '10px';
          w.style.top = `${top}px`;
          w.style.width = 'calc(100vw - 20px)';
          top += 580;
        });
      } else {
        const halfWidth = Math.floor((window.innerWidth - 64) / 2);
        if (winTerm) {
          winTerm.style.left = '20px';
          winTerm.style.top = '72px';
          winTerm.style.width = `${halfWidth}px`;
        }
        if (winTv) {
          winTv.style.left = `${halfWidth + 36}px`;
          winTv.style.top = '72px';
          winTv.style.width = `${halfWidth}px`;
        }
        if (winArena) {
          winArena.style.left = '20px';
          winArena.style.top = '680px';
          winArena.style.width = `${halfWidth}px`;
        }
        if (winComms) {
          winComms.style.left = `${halfWidth + 36}px`;
          winComms.style.top = '680px';
          winComms.style.width = `${halfWidth}px`;
        }
        if (winQuests) {
          winQuests.style.left = '20px';
          winQuests.style.top = '1320px';
          winQuests.style.width = `${window.innerWidth - 48}px`;
        }
      }
    }

    function togglePopoutGuide() {
      alert('TinCan Mesh OS Pop-Out Mode:\n\n1. Click [ ↗ Pop Out ] on any window titlebar.\n2. Move the pop-out window to your secondary monitor.\n3. Packet flights, watch-party playback, cursor telemetry, and XP sync across all windows in real time via BroadcastChannel!');
    }

    // Initialize Windows
    allWindows.forEach(id => {
      const w = document.getElementById(id);
      if (w) makeWindowDraggable(w);
    });

    // Handle Pop-Out Single-Window Viewport Optimization
    if (singleWindowParam && allWindows.includes(singleWindowParam)) {
      allWindows.forEach(id => {
        const w = document.getElementById(id);
        if (w) {
          if (id === singleWindowParam) {
            w.classList.add('popout-fullscreen');
            w.style.display = 'flex';
          } else {
            w.style.display = 'none';
          }
        }
      });
      document.title = `[Pop-Out] TinCan Mesh OS — ${singleWindowParam}`;
    }

    // Copy Command Helper
    function copyCommand(id) {
      const text = document.getElementById(id).innerText;
      navigator.clipboard.writeText(text);
      alert('Copied curl command to clipboard:\n' + text);
    }

    // =========================================================================
    // Background Canvas: Mesh Topology, Taut String Tethers & Packet Flights
    // =========================================================================
    const canvas = document.getElementById('meshTopologyCanvas');
    const ctx = canvas.getContext('2d');
    let activeFlights = [];

    function resizeCanvas() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    function spawnPacketFlight(fromNode, toNode, kind = 'envelope', label = 'Packet') {
      const flight = {
        id: 'fl-' + Math.random().toString(36).substring(2, 8),
        from: fromNode,
        to: toNode,
        kind,
        label,
        progress: 0,
        speed: 0.018 + Math.random() * 0.012
      };
      activeFlights.push(flight);
      meshBus.postMessage({ type: 'FLIGHT', flight });
    }

    function fireTestPacket() {
      initAudio();
      playXpChime();
      spawnPacketFlight(myPeerId, 'relay', 'test', '🥫 Sealed Courier');
      fetch('/api/mesh/quest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          peer_id: myPeerId,
          action_key: 'test_packet',
          from_node: myPeerId,
          to_node: 'relay',
          room: currentRoom
        })
      }).catch(() => {});
    }

    function renderTopology() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const w = canvas.width;
      const h = canvas.height;

      // Define Node Anchors
      const pMap = window.latestProvidersMap || {};
      const relayPos = { x: w * 0.5, y: h * 0.42, label: 'Central Railway Relay' };
      const brains = [
        { id: 'gemini-brain', label: pMap['gemini-brain']?.model || 'Gemini 2.5', x: w * 0.28, y: h * 0.22 },
        { id: 'claude-brain', label: pMap['claude-brain']?.model || 'Claude Sonnet', x: w * 0.42, y: h * 0.18 },
        { id: 'grok-brain', label: pMap['grok-brain']?.model || 'Grok', x: w * 0.58, y: h * 0.18 },
        { id: 'openai-brain', label: pMap['openai-brain']?.model || 'GPT-4o', x: w * 0.72, y: h * 0.22 },
      ];
      const peers = [
        { id: myPeerId, label: 'You (Local)', x: w * 0.32, y: h * 0.68 },
        { id: 'peer-primary-mac', label: 'Mac Studio (M1 Max)', x: w * 0.5, y: h * 0.74 },
        { id: 'peer-secondary-node', label: 'Collaborator MacBook', x: w * 0.68, y: h * 0.68 },
      ];

      function getNodePos(nodeId) {
        if (nodeId === 'relay' || nodeId === 'central-relay') return relayPos;
        const b = brains.find(x => x.id === nodeId || nodeId.includes(x.id));
        if (b) return b;
        const p = peers.find(x => x.id === nodeId || nodeId.includes(x.id));
        if (p) return p;
        return relayPos;
      }

      // Draw Taut "Tin-Can String" Tethers (with subtle acoustic vibration)
      const nowMs = Date.now() * 0.003;
      ctx.save();
      peers.forEach(peer => {
        ctx.beginPath();
        ctx.moveTo(peer.x, peer.y);
        const midX = (peer.x + relayPos.x) / 2;
        const midY = (peer.y + relayPos.y) / 2 + Math.sin(nowMs + peer.x) * 6;
        ctx.quadraticCurveTo(midX, midY, relayPos.x, relayPos.y);
        ctx.strokeStyle = 'rgba(56, 189, 248, 0.22)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 4]);
        ctx.stroke();
      });

      brains.forEach(brain => {
        ctx.beginPath();
        ctx.moveTo(relayPos.x, relayPos.y);
        const midX = (relayPos.x + brain.x) / 2;
        const midY = (relayPos.y + brain.y) / 2 - Math.sin(nowMs + brain.x) * 4;
        ctx.quadraticCurveTo(midX, midY, brain.x, brain.y);
        ctx.strokeStyle = 'rgba(168, 85, 247, 0.25)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([3, 5]);
        ctx.stroke();
      });
      ctx.restore();

      // Draw Relay Node
      ctx.beginPath();
      ctx.arc(relayPos.x, relayPos.y, 14, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(16, 185, 129, 0.35)';
      ctx.fill();
      ctx.strokeStyle = '#10b981';
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = '#6ee7b7';
      ctx.font = '10px monospace';
      ctx.fillText(relayPos.label, relayPos.x - 55, relayPos.y + 26);

      // Draw Brain Nodes
      brains.forEach(b => {
        ctx.beginPath();
        ctx.arc(b.x, b.y, 10, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(99, 102, 241, 0.3)';
        ctx.fill();
        ctx.strokeStyle = '#818cf8';
        ctx.lineWidth = 1.5;
        ctx.stroke();
        ctx.fillStyle = '#c7d2fe';
        ctx.font = '9px monospace';
        ctx.fillText(b.label, b.x - 25, b.y - 14);
      });

      // Draw Peer Nodes
      peers.forEach(p => {
        ctx.beginPath();
        ctx.arc(p.x, p.y, 10, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(14, 165, 233, 0.3)';
        ctx.fill();
        ctx.strokeStyle = '#38bdf8';
        ctx.lineWidth = 1.5;
        ctx.stroke();
        ctx.fillStyle = '#bae6fd';
        ctx.font = '9px monospace';
        ctx.fillText(p.label, p.x - 30, p.y + 22);
      });

      // Draw Active Packet Flights
      activeFlights.forEach((fl, idx) => {
        fl.progress += fl.speed;
        const p1 = getNodePos(fl.from);
        const p2 = getNodePos(fl.to);
        const t = Math.min(1.0, fl.progress);

        // Bezier trajectory
        const midX = (p1.x + p2.x) / 2;
        const midY = (p1.y + p2.y) / 2 + (p1.y > p2.y ? -20 : 20);
        const curX = (1 - t) * (1 - t) * p1.x + 2 * (1 - t) * t * midX + t * t * p2.x;
        const curY = (1 - t) * (1 - t) * p1.y + 2 * (1 - t) * t * midY + t * t * p2.y;

        // Glowing packet capsule
        ctx.beginPath();
        ctx.arc(curX, curY, 6, 0, Math.PI * 2);
        ctx.fillStyle = fl.kind === 'ai_prompt' ? '#ec4899' : '#38bdf8';
        ctx.shadowColor = fl.kind === 'ai_prompt' ? '#ec4899' : '#06b6d4';
        ctx.shadowBlur = 12;
        ctx.fill();
        ctx.shadowBlur = 0;

        ctx.fillStyle = '#ffffff';
        ctx.font = '9px monospace';
        ctx.fillText(fl.label || 'Packet', curX + 9, curY - 4);
      });

      // Clean up finished flights
      activeFlights = activeFlights.filter(fl => fl.progress < 1.0);

      requestAnimationFrame(renderTopology);
    }
    requestAnimationFrame(renderTopology);

    // =========================================================================
    // Watch Party Reactions Bar & Live Emoji Particle Engine
    // =========================================================================
    function spawnEmojiParticle(emoji) {
      const overlay = document.getElementById('reactionOverlay');
      if (!overlay) return;
      const span = document.createElement('span');
      span.className = 'reaction-particle';
      span.innerText = emoji;
      span.style.left = `${20 + Math.random() * 60}%`;
      span.style.bottom = `${10 + Math.random() * 20}%`;
      overlay.appendChild(span);
      setTimeout(() => span.remove(), 2100);
    }

    async function sendReaction(emoji) {
      initAudio();
      spawnEmojiParticle(emoji);
      meshBus.postMessage({ type: 'REACTION', emoji });
      try {
        await fetch('/api/mesh/react', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            emoji,
            display_name: myPeerId,
            room: currentRoom
          })
        });
      } catch (e) {}
    }

    async function syncWatchParty() {
      const vid = document.getElementById('relayNativeVideo');
      if (!vid) return;
      const isPlaying = !vid.paused;
      const currentTime = vid.currentTime;
      try {
        await fetch('/api/mesh/watchparty', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            video_idx: currentVideoIdx,
            is_playing: isPlaying,
            current_time: currentTime,
            room: currentRoom
          })
        });
        meshBus.postMessage({
          type: 'WATCH_PARTY_SYNC',
          video_idx: currentVideoIdx,
          is_playing: isPlaying,
          current_time: currentTime
        });
        alert('Synchronized Watch Party across room peers!');
      } catch (e) {
        alert('Sync error: ' + e.message);
      }
    }

    // =========================================================================
    // Multiplayer Cursor Telemetry
    // =========================================================================
    let lastCursorSend = 0;
    window.addEventListener('mousemove', (e) => {
      const now = Date.now();
      if (now - lastCursorSend > 160) {
        lastCursorSend = now;
        fetch('/api/mesh/cursor', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            display_name: myPeerId,
            x: e.clientX,
            y: e.clientY,
            room: currentRoom
          })
        }).catch(() => {});
      }
    });

    function renderMultiplayerCursors(cursors) {
      const layer = document.getElementById('multiplayerCursorsLayer');
      if (!layer) return;

      Object.entries(cursors || {}).forEach(([peerId, c]) => {
        if (peerId === myPeerId) return;
        let el = document.getElementById('cur-' + peerId);
        if (!el) {
          el = document.createElement('div');
          el.id = 'cur-' + peerId;
          el.className = 'remote-cursor';
          el.innerHTML = `
            <svg class="w-4 h-4 text-cyan-400 drop-shadow" fill="currentColor" viewBox="0 0 24 24">
              <path d="M4 0l16 12-7 2-3 8z"/>
            </svg>
            <span class="text-[10px] bg-slate-900/90 text-cyan-300 border border-cyan-800 px-1.5 py-0.5 rounded font-mono ml-3 -mt-2 inline-block whitespace-nowrap">
              ${c.display_name || peerId}
            </span>
          `;
          layer.appendChild(el);
        }
        el.style.transform = `translate(${c.x}px, ${c.y}px)`;
      });
    }

    // =========================================================================
    // AI Brain Arena Battle Engine & Peer Voting
    // =========================================================================
    async function runArenaBattle() {
      initAudio();
      const prompt = document.getElementById('arenaPromptInput').value.trim();
      const resA = document.getElementById('arenaResultA');
      const resB = document.getElementById('arenaResultB');

      resA.innerText = 'Routing prompt to Gemini 2.5 Flash...';
      resB.innerText = 'Routing prompt to Claude 3.7 Sonnet...';

      spawnPacketFlight(myPeerId, 'gemini-brain', 'ai_prompt', 'gemini-brain');
      spawnPacketFlight(myPeerId, 'claude-brain', 'ai_prompt', 'claude-brain');

      try {
        const [respA, respB] = await Promise.all([
          fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: 'gemini-brain', prompt })
          }).then(r => r.json()),
          fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: 'claude-brain', prompt })
          }).then(r => r.json())
        ]);

        resA.innerText = respA.choices?.[0]?.message?.content || respA.text || JSON.stringify(respA, null, 2);
        resB.innerText = respB.choices?.[0]?.message?.content || respB.text || JSON.stringify(respB, null, 2);
      } catch (err) {
        resA.innerText = 'Battle error: ' + err.message;
        resB.innerText = 'Battle error: ' + err.message;
      }
    }

    async function voteArenaWinner(winnerAlias) {
      initAudio();
      playXpChime();
      spawnPacketFlight(myPeerId, winnerAlias, 'ai_prompt', `Vote: ${winnerAlias}`);
      try {
        const res = await fetch('/api/mesh/arena/vote', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            winner_alias: winnerAlias,
            prompt_preview: document.getElementById('arenaPromptInput').value.substring(0, 40),
            display_name: myPeerId,
            room: currentRoom
          })
        });
        const data = await res.json();
        alert(`🏆 Vote recorded for ${winnerAlias}! +150 XP awarded to your squad.`);
        pollMeshState();
      } catch (err) {
        alert('Vote error: ' + err.message);
      }
    }

    async function triggerQuestAction(actionKey) {
      initAudio();
      playXpChime();
      spawnPacketFlight(myPeerId, 'relay', actionKey, actionKey);
      try {
        const res = await fetch('/api/mesh/quest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            action_key: actionKey,
            display_name: myPeerId,
            from_node: myPeerId,
            to_node: 'relay',
            room: currentRoom
          })
        });
        const data = await res.json();
        pollMeshState();
      } catch (e) {}
    }

    // =========================================================================
    // Polling Loop: State, Quests, Leaderboard & Readiness Progression
    // =========================================================================
    async function pollMeshState() {
      try {
        const res = await fetch(`/api/mesh/state?room=${encodeURIComponent(currentRoom)}`);
        if (!res.ok) return;
        const state = await res.json();

        // Update Tier Badge
        if (state.tier) {
          const badge = document.getElementById('osTierBadge');
          const tierLabel = state.tier.tier_name || state.tier.tier || 'L3: Cryptographic Multi-Account Bridge';
          const tierPct = state.tier.progress_pct !== undefined ? state.tier.progress_pct : (state.tier.score || '94.5');
          badge.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span><span>${tierLabel} (${tierPct}%)</span>`;
        }

        // Update Squad XP Progress Bar
        const squadXp = state.xp !== undefined ? state.xp : (state.squad_xp || 550);
        const targetXp = state.tier?.next_tier_xp || state.tier?.target_xp || 1000;
        const pct = Math.min(100, Math.round((squadXp / targetXp) * 100));
        document.getElementById('osXpBar').style.width = `${pct}%`;
        document.getElementById('osXpText').innerText = `${squadXp.toLocaleString()} / ${targetXp.toLocaleString()} XP`;

        // Update Peer Count
        const count = state.peers_count || (state.active_webrtc_streams?.length || 2);
        document.getElementById('osPeerCountNum').innerText = count;

        // Render Multiplayer Cursors
        if (state.cursors) {
          const cursorMap = {};
          if (Array.isArray(state.cursors)) {
            state.cursors.forEach(c => { cursorMap[c.peer_id] = c; });
          } else {
            Object.assign(cursorMap, state.cursors);
          }
          renderMultiplayerCursors(cursorMap);
        }

        // Update Leaderboard
        if (state.leaderboard && Array.isArray(state.leaderboard)) {
          const tbody = document.getElementById('operatorLeaderboard');
          tbody.innerHTML = state.leaderboard.map((p, idx) => `
            <tr>
              <td class="px-3 py-2 text-${idx === 0 ? 'amber-400' : 'slate-400'} font-bold">#${idx + 1}</td>
              <td class="px-3 py-2 text-white font-bold">${p.display_name || p.peer_id}</td>
              <td class="px-3 py-2 text-emerald-400">${p.tier || 'L3: Cryptographic Bridge'}</td>
              <td class="px-3 py-2">
                ${(p.badges || ['🟢 Initiate']).map(b => `<span class="px-1.5 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-700 text-[10px] mr-1">${b}</span>`).join('')}
              </td>
              <td class="px-3 py-2 text-right text-cyan-300 font-bold">${(p.xp || 0).toLocaleString()} XP</td>
            </tr>
          `).join('');
        }
      } catch (e) {}
    }

    setInterval(pollMeshState, 2000);
    pollMeshState();

    // BroadcastChannel Listener
    meshBus.onmessage = (ev) => {
      const msg = ev.data;
      if (!msg) return;
      if (msg.type === 'REACTION' && msg.emoji) {
        spawnEmojiParticle(msg.emoji);
      } else if (msg.type === 'FLIGHT' && msg.flight) {
        activeFlights.push(msg.flight);
      } else if (msg.type === 'MODEL_UPDATED') {
        loadAnalytics();
      }
    };

    // =========================================================================
    // Core WebRTC Signaling & Media Engine (Preserved)
    // =========================================================================
    let pc = null;
    let localStream = null;
    let lastSignalSeq = 0;
    let pollTimer = null;
    let isMuted = false;
    let isCamOff = false;

    const rtcConfig = {
      iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
      ]
    };

    function setCallStatus(text, tone = 'slate') {
      const badge = document.getElementById('callStatusBadge');
      badge.innerText = text;
      badge.className = `px-2 py-0.5 rounded border text-[11px] font-mono bg-${tone}-950 text-${tone}-300 border-${tone}-800`;
    }

    function copyInviteLink() {
      const room = document.getElementById('roomInput').value.trim() || 'main';
      const inviteUrl = `${window.location.origin}/?room=${encodeURIComponent(room)}#call`;
      navigator.clipboard.writeText(inviteUrl);
      alert('Copied WebRTC room invite link:\n' + inviteUrl);
    }

    async function sendSignal(type, payload, to = '*') {
      const room = document.getElementById('roomInput').value.trim() || 'main';
      await fetch('/api/webrtc/signal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from: myPeerId, to, room, type, payload })
      });
    }

    function ensurePeerConnection() {
      if (pc) return pc;
      pc = new RTCPeerConnection(rtcConfig);
      pc.onicecandidate = (ev) => {
        if (ev.candidate) {
          sendSignal('candidate', { candidate: ev.candidate });
        }
      };
      pc.ontrack = (ev) => {
        const remoteVideo = document.getElementById('remoteVideo');
        if (ev.streams && ev.streams[0]) {
          remoteVideo.srcObject = ev.streams[0];
          setCallStatus('Connected (Live Media)', 'emerald');
        }
      };
      if (localStream) {
        localStream.getTracks().forEach(track => pc.addTrack(track, localStream));
      }
      return pc;
    }

    async function startCall(mode = 'video') {
      try {
        const room = document.getElementById('roomInput').value.trim() || 'main';
        setCallStatus('Requesting mic/cam...', 'amber');
        localStream = await navigator.mediaDevices.getUserMedia({
          video: mode === 'video',
          audio: true
        });
        document.getElementById('localVideo').srcObject = localStream;

        await fetch('/api/webrtc/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            display_name: myPeerId,
            room,
            has_video: mode === 'video',
            has_audio: true,
            has_screen: false
          })
        });

        ensurePeerConnection();
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        await sendSignal('offer', { sdp: pc.localDescription });
        setCallStatus('Calling room ' + room + '...', 'cyan');
        if (!pollTimer) pollTimer = setInterval(pollSignals, 1200);
      } catch (err) {
        setCallStatus('Media error: ' + err.message, 'rose');
      }
    }

    async function startScreenShare() {
      try {
        const room = document.getElementById('roomInput').value.trim() || 'main';
        const screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
        localStream = screenStream;
        document.getElementById('localVideo').srcObject = screenStream;

        await fetch('/api/webrtc/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            display_name: myPeerId + ' (Screen)',
            room,
            has_video: true,
            has_audio: true,
            has_screen: true
          })
        });

        ensurePeerConnection();
        const videoTrack = screenStream.getVideoTracks()[0];
        const sender = pc.getSenders().find(s => s.track && s.track.kind === 'video');
        if (sender && videoTrack) {
          await sender.replaceTrack(videoTrack);
        } else {
          screenStream.getTracks().forEach(t => pc.addTrack(t, screenStream));
        }
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        await sendSignal('offer', { sdp: pc.localDescription });
        setCallStatus('Sharing Screen in ' + room, 'cyan');
        if (!pollTimer) pollTimer = setInterval(pollSignals, 1200);
      } catch (err) {
        setCallStatus('Screenshare error: ' + err.message, 'rose');
      }
    }

    function toggleMute() {
      if (!localStream) return;
      isMuted = !isMuted;
      localStream.getAudioTracks().forEach(t => { t.enabled = !isMuted; });
      document.getElementById('muteBtn').innerText = isMuted ? '🔊 Unmute Mic' : '🔇 Mute Mic';
    }

    function toggleCamera() {
      if (!localStream) return;
      isCamOff = !isCamOff;
      localStream.getVideoTracks().forEach(t => { t.enabled = !isCamOff; });
      document.getElementById('camBtn').innerText = isCamOff ? '📷 Cam On' : '📷 Toggle Cam';
    }

    async function hangupCall() {
      const room = document.getElementById('roomInput').value.trim() || 'main';
      if (localStream) {
        localStream.getTracks().forEach(t => t.stop());
        localStream = null;
      }
      if (pc) {
        pc.close();
        pc = null;
      }
      document.getElementById('localVideo').srcObject = null;
      document.getElementById('remoteVideo').srcObject = null;
      document.getElementById('remotePeerLabel').innerText = 'waiting for peer...';
      await fetch('/api/webrtc/leave', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ peer_id: myPeerId, room })
      });
      setCallStatus('Call Ended', 'slate');
    }

    async function pollSignals() {
      try {
        const room = document.getElementById('roomInput').value.trim() || 'main';
        const res = await fetch(`/api/webrtc/signals?peer_id=${encodeURIComponent(myPeerId)}&room=${encodeURIComponent(room)}&since_seq=${lastSignalSeq}`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.latest_seq && data.latest_seq > lastSignalSeq) {
          lastSignalSeq = data.latest_seq;
        }
        if (data.peers) {
          const grid = document.getElementById('roomPeersGrid');
          grid.innerHTML = data.peers.map(p => `
            <div class="p-2 bg-slate-800/60 rounded border border-slate-700 flex justify-between items-center text-xs font-mono">
              <span class="text-white">${p.display_name}</span>
              <span class="bg-emerald-900 text-emerald-300 px-1.5 py-0.5 rounded text-[10px]">${p.has_screen ? 'SCREEN' : (p.has_video ? 'VIDEO+VOICE' : 'VOICE')} · UDP:${p.udp_port}</span>
            </div>
          `).join('');
        }
        for (const sig of (data.signals || [])) {
          document.getElementById('remotePeerLabel').innerText = sig.from;
          if (sig.type === 'offer' && sig.payload && sig.payload.sdp) {
            // Peripheral & Connection Consent Guard: Never auto-answer an incoming WebRTC offer
            // without explicit human consent.
            const accepted = window.confirm(`Incoming WebRTC call offer from '${sig.from}'. Accept connection? (Your camera/mic remain OFF unless you explicitly enable them)`);
            if (!accepted) {
              setCallStatus('Declined offer from ' + sig.from, 'amber');
              continue;
            }
            ensurePeerConnection();
            await pc.setRemoteDescription(new RTCSessionDescription(sig.payload.sdp));
            const answer = await pc.createAnswer();
            await pc.setLocalDescription(answer);
            await sendSignal('answer', { sdp: pc.localDescription }, sig.from);
            setCallStatus('Connected with ' + sig.from, 'emerald');
          } else if (sig.type === 'answer' && sig.payload && sig.payload.sdp && pc) {
            await pc.setRemoteDescription(new RTCSessionDescription(sig.payload.sdp));
            setCallStatus('Connected with ' + sig.from, 'emerald');
          } else if (sig.type === 'candidate' && sig.payload && sig.payload.candidate && pc) {
            try {
              await pc.addIceCandidate(new RTCIceCandidate(sig.payload.candidate));
            } catch (e) {}
          } else if (sig.type === 'hangup') {
            document.getElementById('remoteVideo').srcObject = null;
            document.getElementById('remotePeerLabel').innerText = 'peer hung up';
            setCallStatus('Peer disconnected', 'amber');
          }
        }
      } catch (e) {}
    }
    pollTimer = setInterval(pollSignals, 2000);

    // =========================================================================
    // OpenRouter Analytics & Model Configuration Engine (Preserved & Synced)
    // =========================================================================
    var latestProvidersMap = window.latestProvidersMap = {};

    function syncSelectedAliasModel(forcePopulateInput = false) {
      const sel = document.getElementById('aliasSelect');
      const inp = document.getElementById('modelInput');
      const badge = document.getElementById('currentTargetModelBadge');
      if (!sel) return;
      const alias = sel.value;
      const info = latestProvidersMap[alias];
      const currentModel = info ? info.model : '';
      if (badge && currentModel) {
        badge.innerText = `Active: ${alias} → ${currentModel}`;
      }
      if (inp && currentModel && (forcePopulateInput || document.activeElement !== inp)) {
        if (forcePopulateInput || !inp.dataset.userEdited) {
          inp.value = currentModel;
          delete inp.dataset.userEdited;
        }
      }
    }

    document.getElementById('modelInput').addEventListener('input', (ev) => {
      ev.target.dataset.userEdited = 'true';
    });

    function quickPickModel(modelId) {
      const inp = document.getElementById('modelInput');
      if (!inp) return;
      inp.value = modelId;
      inp.dataset.userEdited = 'true';
      updateModel();
    }

    function selectProviderCardForSwap(alias) {
      const sel = document.getElementById('aliasSelect');
      if (!sel) return;
      sel.value = alias;
      syncSelectedAliasModel(true);
      document.getElementById('modelInput')?.focus();
    }

    async function loadAnalytics() {
      try {
        const res = await fetch('/api/models/analytics');
        const data = await res.json();
        const or = data.openrouter || {};

        if (or.connected) {
          document.getElementById('orRemaining').innerText = `$${Number(or.account_remaining_balance_usd).toFixed(4)}`;
          document.getElementById('orCreditsTotal').innerText = `of $${Number(or.account_total_credits_usd).toFixed(2)} total credits`;
          document.getElementById('orTotalUsage').innerText = `$${Number(or.account_total_usage_usd).toFixed(4)}`;
          document.getElementById('orKeyUsage').innerText = `$${Number(or.key_usage_total_usd).toFixed(6)}`;
          document.getElementById('orKeyToday').innerText = `Today: $${Number(or.key_usage_daily_usd).toFixed(6)}`;
          document.getElementById('orKeyLimitRem').innerText = or.key_remaining_usd != null ? `$${Number(or.key_remaining_usd).toFixed(4)}` : 'Unlimited';
          document.getElementById('orKeyLabel').innerText = `Key: ${or.key_label || '--'}`;
        }

        document.getElementById('analyticsHeader').innerText = 
          `Calls: ${data.total_calls} | Tokens: ${data.total_tokens} | Cost: $${Number(data.total_spend_usd).toFixed(6)}`;
        
        window.latestProvidersMap = latestProvidersMap = data.providers || {};
        const sel = document.getElementById('aliasSelect');
        const prevSelected = sel ? sel.value : 'gemini-brain';
        if (sel && Object.keys(latestProvidersMap).length > 0) {
          sel.innerHTML = Object.entries(latestProvidersMap).map(([alias, info]) =>
            `<option value="${alias}">${alias} → ${info.model}</option>`
          ).join('');
          if (latestProvidersMap[prevSelected]) {
            sel.value = prevSelected;
          }
          syncSelectedAliasModel(false);
        }

        const container = document.getElementById('providerCards');
        container.innerHTML = '';
        for (const [alias, info] of Object.entries(latestProvidersMap)) {
          const isSelected = sel && sel.value === alias;
          const card = document.createElement('div');
          card.onclick = () => selectProviderCardForSwap(alias);
          card.className = `cursor-pointer p-3 bg-slate-800/60 rounded-lg border ${isSelected ? 'border-indigo-500 ring-1 ring-indigo-500/40' : 'border-slate-700/80 hover:border-slate-600'} space-y-1.5 font-mono text-xs transition`;
          card.innerHTML = `
            <div class="flex justify-between items-center">
              <span class="font-bold text-white">${alias}</span>
              <span class="text-[10px] bg-indigo-950 text-indigo-300 px-1.5 py-0.5 rounded border border-indigo-800">${info.display_name}</span>
            </div>
            <div class="text-emerald-300 truncate text-[11px] font-semibold"><span class="text-slate-500 font-normal">Model:</span> ${info.model}</div>
            <div class="grid grid-cols-3 gap-1 pt-1 text-slate-300 border-t border-slate-700/50 text-[10px]">
              <div><span class="text-slate-500">In/1M:</span> <span class="text-amber-300">$${Number(info.input_cost_per_1m_usd || 0).toFixed(2)}</span></div>
              <div><span class="text-slate-500">Out/1M:</span> <span class="text-amber-300">$${Number(info.output_cost_per_1m_usd || 0).toFixed(2)}</span></div>
              <div><span class="text-slate-500">Calls:</span> <span class="text-cyan-300">${info.total_calls ?? info.call_count ?? 0}</span></div>
            </div>
          `;
          container.appendChild(card);
        }
      } catch (e) {}
    }

    async function updateModel() {
      const sel = document.getElementById('aliasSelect');
      const inp = document.getElementById('modelInput');
      const alias = sel.value;
      const model = inp.value.trim();
      const fb = document.getElementById('updateFeedback');
      if (!model) {
        fb.innerText = 'Please enter a valid model identifier';
        fb.className = 'text-xs mt-2 font-mono text-red-400 block';
        return;
      }
      try {
        const res = await fetch('/api/models/set', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({alias, model})
        });
        const resp = await res.json();
        if (res.ok) {
          if (!latestProvidersMap[resp.alias]) {
            latestProvidersMap[resp.alias] = { display_name: resp.display_name || resp.alias, model: resp.model };
          } else {
            latestProvidersMap[resp.alias].model = resp.model;
          }
          delete inp.dataset.userEdited;
          inp.value = resp.model;
          syncSelectedAliasModel(true);
          fb.innerText = `✓ Updated ${resp.alias} → ${resp.model}`;
          fb.className = 'text-xs mt-2 font-mono text-emerald-400 block';
          spawnPacketFlight(myPeerId, resp.alias, 'ai_prompt', `Swap: ${resp.model}`);
          meshBus.postMessage({ type: 'MODEL_UPDATED', alias: resp.alias, model: resp.model });
          await loadAnalytics();
        } else {
          fb.innerText = `Error: ${resp.error}`;
          fb.className = 'text-xs mt-2 font-mono text-red-400 block';
        }
      } catch (err) {
        fb.innerText = `Request failed: ${err.message}`;
        fb.className = 'text-xs mt-2 font-mono text-red-400 block';
      }
    }

    // =========================================================================
    // Relay Video Channel & Auto-Rotating Playlist Engine (Preserved)
    // =========================================================================
    let playlistVideos = [];
    let currentVideoIdx = 0;
    let autoRotateEnabled = true;
    let rotateTimer = null;

    async function loadPlaylist(preserveIndex = true) {
      try {
        const res = await fetch('/api/playlist');
        if (!res.ok) return;
        const data = await res.json();
        playlistVideos = data.videos || [];
        if (!preserveIndex || currentVideoIdx >= playlistVideos.length) {
          currentVideoIdx = 0;
        }
        renderPlaylistUI();
      } catch (e) {}
    }

    function renderPlaylistUI() {
      const total = playlistVideos.length;
      const badge = document.getElementById('playlistCounterBadge');
      const queue = document.getElementById('playlistQueue');
      if (!total) {
        badge.innerText = '0 / 0';
        queue.innerHTML = '<div class="text-slate-500">No videos in collection</div>';
        return;
      }

      const item = playlistVideos[currentVideoIdx];
      badge.innerText = `${currentVideoIdx + 1} / ${total} · ${autoRotateEnabled ? 'Loop' : 'Paused'}`;
      document.getElementById('nowPlayingTitle').innerHTML =
        `${item.title} · <span class="text-pink-400 font-mono">${item.creator}</span>`;

      const vidEl = document.getElementById('relayNativeVideo');
      const targetSrc = item.embed_url || `/videos/${item.video_id}.mp4`;
      if (vidEl) {
        vidEl.loop = (total === 1 && autoRotateEnabled);
        if (vidEl.getAttribute('data-vid') !== item.id) {
          vidEl.setAttribute('data-vid', item.id);
          vidEl.src = targetSrc;
          vidEl.play().catch(() => {});
        }
      }

      queue.innerHTML = playlistVideos.map((v, idx) => `
        <div onclick="selectPlaylistVideo(${idx})" class="cursor-pointer px-2.5 py-1 rounded border flex justify-between items-center transition ${idx === currentVideoIdx ? 'bg-pink-950/60 border-pink-700 text-white' : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'}">
          <span class="truncate">${idx + 1}. ${v.title} (${v.creator})</span>
          <span class="text-[10px] uppercase px-1.5 py-0.5 rounded bg-slate-900 text-slate-300 ml-2 shrink-0">${v.category}</span>
        </div>
      `).join('');
    }

    function selectPlaylistVideo(idx) {
      if (idx < 0 || idx >= playlistVideos.length) return;
      currentVideoIdx = idx;
      renderPlaylistUI();
    }

    function nextPlaylistVideo() {
      if (!playlistVideos.length) return;
      currentVideoIdx = (currentVideoIdx + 1) % playlistVideos.length;
      renderPlaylistUI();
    }

    function prevPlaylistVideo() {
      if (!playlistVideos.length) return;
      currentVideoIdx = (currentVideoIdx - 1 + playlistVideos.length) % playlistVideos.length;
      renderPlaylistUI();
    }

    function toggleAutoRotate() {
      autoRotateEnabled = !autoRotateEnabled;
      const btn = document.getElementById('autoRotateBtn');
      btn.innerText = autoRotateEnabled ? '🔁 Auto-Loop: ON' : '⏸ Auto-Loop: OFF';
      btn.className = autoRotateEnabled
        ? 'px-2.5 py-1 bg-emerald-950 text-emerald-300 rounded border border-emerald-800 transition'
        : 'px-2.5 py-1 bg-slate-800 text-slate-400 rounded border border-slate-700 transition';
      renderPlaylistUI();
    }

    function toggleVideoSound() {
      const vidEl = document.getElementById('relayNativeVideo');
      const btn = document.getElementById('soundToggleBtn');
      if (!vidEl) return;
      vidEl.muted = !vidEl.muted;
      btn.innerText = vidEl.muted ? '🔊 Tap to Unmute' : '🔇 Mute Audio';
      vidEl.play().catch(() => {});
    }

    document.getElementById('relayNativeVideo').addEventListener('ended', () => {
      if (autoRotateEnabled && playlistVideos.length > 1) {
        nextPlaylistVideo();
      } else if (autoRotateEnabled && playlistVideos.length === 1) {
        const vidEl = document.getElementById('relayNativeVideo');
        vidEl.currentTime = 0;
        vidEl.play().catch(() => {});
      }
    });

    async function addVideoToPlaylist() {
      const inp = document.getElementById('newVideoInput');
      const raw = inp.value.trim();
      if (!raw) return;
      try {
        const res = await fetch('/api/playlist/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ input: raw, category: 'spotlight', peer_id: myPeerId })
        });
        const data = await res.json();
        if (res.ok) {
          inp.value = '';
          playlistVideos = data.playlist.videos || [];
          currentVideoIdx = playlistVideos.length - 1;
          renderPlaylistUI();
          playXpChime();
        } else {
          alert('Could not add video: ' + (data.error || 'Unknown error'));
        }
      } catch (err) {
        alert('Failed to add video: ' + err.message);
      }
    }

    // Init Playlist & Analytics
    loadPlaylist(false);
    loadAnalytics();
    setInterval(loadAnalytics, 5000);
  </script>
</body>
</html>
"""
