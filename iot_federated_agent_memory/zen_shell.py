"""TinCan Mesh OS — Zen startup shell.

Wraps MESH_OS_HTML_UI so the desktop opens calm: the relay's video collection plays as a
vertical feed behind everything, no windows are open, and every tool lives behind one mark
(or Cmd/Ctrl+K). Registration still gates every tool; it simply waits until a visitor
reaches for one instead of covering the first clip.

Injected as a post-process (`apply_zen_shell`) rather than edited into mesh_os_ui.py so
other agents can keep changing the classic UI without merge conflicts. Pop-out windows,
single-window routes (/tv, /call, /board, ...) and `?classic=1` keep the classic desktop.
"""

ZEN_HEAD = r"""
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@500;600&family=Zen+Kaku+Gothic+New:wght@400;500&display=swap" rel="stylesheet">
  <script>
    (function () {
      // /arena/ and /arena open the same window: drop the trailing slash before the shell reads the path.
      if (location.pathname.length > 1 && /\/$/.test(location.pathname)) {
        history.replaceState(null, '', location.pathname.replace(/\/+$/, '') + location.search + location.hash);
      }
      var q = new URLSearchParams(location.search);
      var singleRoutes = ['/tv', '/call', '/comms', '/chat', '/arena', '/terminal', '/billing', '/tokens', '/board', '/cyberspace',
                          '/space', '/files', '/finder', '/agentspace', '/quests', '/rewards', '/network'];
      if (q.get('classic') === '1' || q.get('window') || singleRoutes.indexOf(location.pathname) !== -1) return;
      document.documentElement.classList.add('zen-boot');
    })();
  </script>
  <style>
    :root {
      --zen-sumi: #ecf1e6;
      --zen-sumi-2: #ecf1e6;
      --zen-washi: #111111;
      --zen-washi-2: rgba(17, 17, 17, 0.7);
      --zen-washi-3: rgba(17, 17, 17, 0.5);
      --zen-tick: rgba(17, 17, 17, 0.38);
      --zen-line: #111111;
      --zen-kaki: #111111;
      --zen-ease: cubic-bezier(0.16, 1, 0.3, 1);
      --zen-mincho: -apple-system, BlinkMacSystemFont, "Aeonik", "Inter", sans-serif;
      --zen-gothic: -apple-system, BlinkMacSystemFont, "Aeonik", "Inter", sans-serif;
    }

    html.zen-boot .mesh-window,
    html.zen-boot #meshOsHud,
    html.zen-boot #meshOsDock,
    html.zen-boot #accountSetupModal { visibility: hidden; }

    body.zen {
      background: var(--zen-sumi);
      color: var(--zen-washi);
      overflow: hidden;
      height: 100dvh;
    }
    body.zen ::selection { background: rgba(208, 112, 63, 0.45); color: var(--zen-washi); }
    body.zen #meshOsHud,
    body.zen #meshOsDock,
    body.zen #meshTopologyCanvas { display: none !important; }
    body.zen #desktopWorkspace { pointer-events: none; padding: 0; min-height: 0; }
    body.zen:not(.zen-working) #multiplayerCursorsLayer { display: none; }
    body.zen #desktopWorkspace .mesh-window { pointer-events: auto; }

    /* ---------- stage: flat celadon paper with the clip framed on it ---------- */
    #zenStage { position: fixed; inset: 0; z-index: 1; overflow: hidden; background: var(--zen-sumi); }
    #zenFrame {
      position: absolute; left: 50%; top: 50%;
      --zen-ar: 0.5625;
      height: min(84dvh, calc((100vw - 2rem) / var(--zen-ar)));
      aspect-ratio: var(--zen-ar);
      transform: translate(-50%, -50%);
      border-radius: 16px;
      overflow: hidden;
      background: #111111;
      border: 1px solid var(--zen-line);
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.08);
      transition: opacity 420ms var(--zen-ease), transform 620ms var(--zen-ease), filter 900ms var(--zen-ease);
      cursor: pointer;
    }
    #zenFrame.zen-leave-up { opacity: 0; transform: translate(-50%, calc(-50% - 4%)); }
    #zenFrame.zen-leave-down { opacity: 0; transform: translate(-50%, calc(-50% + 4%)); }
    #zenFrame.zen-enter-up { opacity: 0; transform: translate(-50%, calc(-50% + 4%)); transition: none; }
    #zenFrame.zen-enter-down { opacity: 0; transform: translate(-50%, calc(-50% - 4%)); transition: none; }
    #zenVideo { width: 100%; height: 100%; object-fit: cover; display: block; }
    /* Clip tag: makes it obvious the framed video is a clip in the feed, not a dialog */
    #zenClipTag {
      position: absolute; left: 0.75rem; top: 0.75rem; z-index: 2; pointer-events: none;
      display: inline-flex; align-items: center; gap: 0.4rem; max-width: calc(100% - 1.5rem);
      padding: 0.2rem 0.65rem; border: 1px solid #111111; border-radius: 9999px; background: #ecf1e6; color: #111111;
      font-family: "JetBrains Mono", ui-monospace, monospace; font-size: 11px; line-height: 1.4;
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    /* ---------- feed chrome ---------- */
    .zen-chrome { position: fixed; z-index: 30; transition: opacity 600ms var(--zen-ease), transform 600ms var(--zen-ease); }
    body.zen-working .zen-chrome.zen-feed-only,
    body.zen-launcher .zen-chrome.zen-feed-only { opacity: 0; pointer-events: none; transform: translateY(6px); }
    body.zen-working #zenFrame { opacity: 0.32; filter: blur(6px) saturate(0.6); }
    body.zen-launcher #zenFrame { filter: blur(10px) saturate(0.6); opacity: 0.35; transform: translate(-50%, -50%) scale(0.97); }

    .zen-btn {
      appearance: none; background: none; border: 0; color: inherit; cursor: pointer;
      font: inherit; padding: 0; -webkit-tap-highlight-color: transparent;
    }
    .zen-btn:focus-visible, #zenLauncher button:focus-visible {
      outline: 1px solid var(--zen-washi); outline-offset: 4px; border-radius: 6px;
    }

    #zenMark {
      z-index: 70;
      top: max(1.25rem, env(safe-area-inset-top)); left: 1.5rem;
      display: flex; align-items: center; gap: 0.7rem;
      font-family: var(--zen-mincho); font-weight: 600; font-size: 1.05rem; letter-spacing: 0.02em;
      color: var(--zen-washi);
    }
    #zenMark svg { width: 30px; height: 30px; transition: transform 900ms var(--zen-ease); }
    #zenMark:hover svg { transform: rotate(-24deg); }
    #zenMark .zen-hint {
      display: none;
      font-family: var(--zen-gothic); font-weight: 400; font-size: 0.72rem; letter-spacing: 0.04em;
      color: #4a4a4a; margin-left: 0.15rem;
      opacity: 0; transform: translateX(-4px); transition: opacity 400ms var(--zen-ease), transform 400ms var(--zen-ease);
    }
    #zenMark:hover .zen-hint, #zenMark:focus-visible .zen-hint { opacity: 1; transform: none; }

    #zenCaption {
      left: 1.5rem; bottom: max(1.5rem, env(safe-area-inset-bottom));
      max-width: min(30ch, 34vw);
    }
    #zenCaption .zen-title { font-family: var(--zen-mincho); font-weight: 500; font-size: 1.12rem; line-height: 1.35; text-wrap: balance; }
    #zenCaption .zen-meta { margin-top: 0.4rem; font-family: var(--zen-gothic); font-size: 0.8rem; color: #4a4a4a; letter-spacing: 0.02em; }

    #zenActions {
      right: 1.5rem; bottom: max(1.5rem, env(safe-area-inset-bottom));
      display: flex; align-items: center; gap: 1.4rem;
      font-family: var(--zen-gothic); font-size: 0.86rem;
    }
    #zenSound { display: flex; align-items: center; gap: 0.5rem; color: #4a4a4a; }
    #zenSound:hover { color: var(--zen-washi); }
    #zenSound svg { width: 18px; height: 18px; }
    #zenJoin {
      color: #111111;
      padding: 0.5rem 1rem;
      border: 1px solid #111111;
      border-radius: 9999px;
      background: #ecf1e6;
      font-family: "JetBrains Mono", ui-monospace, monospace; font-size: 0.8rem; font-weight: 500;
      max-width: 16rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
      transition: background 200ms var(--zen-ease), color 200ms var(--zen-ease);
    }
    #zenJoin:hover, #zenJoin:focus-visible { background: #111111; color: #ecf1e6; }

    /* Quick launch: the tools people reach for most, always visible on the feed. */
    #zenQuick { display: flex; align-items: center; gap: 0.4rem; }
    #zenQuick button {
      color: #111111; background: transparent;
      padding: 0.42rem 0.8rem; border: 1px solid rgba(17, 17, 17, 0.28); border-radius: 9999px;
      font-family: "JetBrains Mono", ui-monospace, monospace; font-size: 0.76rem; font-weight: 500; white-space: nowrap;
      transition: background 200ms var(--zen-ease), color 200ms var(--zen-ease), border-color 200ms var(--zen-ease);
    }
    #zenQuick button:hover, #zenQuick button:focus-visible { background: #111111; color: #ecf1e6; border-color: #111111; }
    #zenQuick kbd { font: inherit; opacity: 0.6; margin-left: 0.3rem; }

    #zenTicks {
      right: 1.5rem; top: 50%; transform: translateY(-50%);
      display: flex; flex-direction: column; gap: 0.55rem; list-style: none; margin: 0; padding: 0;
    }
    body.zen-working #zenTicks, body.zen-launcher #zenTicks { transform: translateY(-50%); }
    #zenTicks button { display: block; width: 2px; height: 18px; background: rgba(17, 17, 17, 0.35); border-radius: 1px; transition: background 400ms, height 400ms var(--zen-ease); }
    #zenTicks button::after { content: ""; position: absolute; inset: -6px -10px; }
    #zenTicks li { position: relative; }
    #zenTicks button[aria-current="true"] { background: var(--zen-kaki); height: 30px; }


    /* ---------- launcher ---------- */
    #zenLauncher {
      position: fixed; inset: 0; z-index: 60;
      display: flex; align-items: center;
      padding: 6vh max(1.5rem, 9vw);
      background: rgba(236, 241, 230, 0.94);
      backdrop-filter: blur(16px);
      opacity: 0; visibility: hidden;
      transition: opacity 520ms var(--zen-ease), visibility 0s linear 520ms;
    }
    body.zen-launcher #zenLauncher { opacity: 1; visibility: visible; transition: opacity 520ms var(--zen-ease), visibility 0s; }
    #zenLauncher .zl-inner { width: min(42rem, 100%); max-height: 100%; display: flex; flex-direction: column; }
    #zenLauncher label { display: flex; align-items: center; gap: 0.75rem; border-bottom: 1px solid var(--zen-line); padding-bottom: 0.8rem; margin-bottom: 1.4rem; }
    #zenSearch {
      flex: 1; background: transparent; border: 0; color: var(--zen-washi); caret-color: var(--zen-kaki);
      font-family: var(--zen-gothic); font-size: 0.95rem; letter-spacing: 0.02em;
    }
    #zenSearch::placeholder { color: #5c5c5c; }
    #zenSearch:focus { outline: none; }
    #zenLauncher label:focus-within { border-bottom-width: 2px; }
    #zenLauncher kbd { font-family: var(--zen-gothic); font-size: 0.72rem; color: #4a4a4a; border: 1px solid var(--zen-line); border-radius: 5px; padding: 0.1rem 0.4rem; }
    #zenTools { list-style: none; margin: 0; padding: 0; overflow-y: auto; }
    #zenTools button {
      position: relative; width: 100%; text-align: left; display: grid; grid-template-columns: minmax(0, 19rem) minmax(0, 1fr) auto; align-items: baseline; gap: 1.5rem;
      padding: 0.5rem 0 0.5rem 1.5rem; color: var(--zen-washi-2);
      transition: color 260ms var(--zen-ease);
    }
    #zenTools button.zl-cmd { grid-template-columns: minmax(0, 1fr) auto; gap: 1rem; }
    #zenTools .zl-act { font-family: "JetBrains Mono", ui-monospace, monospace; font-size: 0.68rem; font-weight: 500; letter-spacing: 0.04em; text-transform: uppercase; color: #4a4a4a; border: 1px solid var(--zen-line); border-radius: 999px; padding: 0.1rem 0.55rem; white-space: nowrap; justify-self: end; }
    #zenTools button[aria-selected="true"] .zl-act { background: #111111; color: #ecf1e6; }
    #zenTools .zl-cmd .zl-name { font-size: clamp(1.05rem, 1.7vw, 1.35rem); }
    #zenHint { margin: 0 0 1rem; font-family: var(--zen-gothic); font-size: 0.82rem; color: #4a4a4a; letter-spacing: 0.02em; }
    #zenHint:empty, #zenHint[hidden] { display: none; }
    #zenStatus { margin: 0.6rem 0 0; min-height: 1.1rem; font-family: "JetBrains Mono", ui-monospace, monospace; font-size: 0.74rem; color: #4a4a4a; }
    #zenOut {
      margin: 1rem 0 0; padding: 0.7rem 0.9rem; max-height: 34vh; overflow: auto; white-space: pre-wrap; word-break: break-word;
      font-family: "JetBrains Mono", ui-monospace, monospace; font-size: 0.78rem; line-height: 1.45; color: var(--zen-washi);
      border: 1px solid var(--zen-line); border-radius: 8px; background: rgba(255, 255, 255, 0.55);
    }
    #zenOut[hidden] { display: none; }
    #zenTools button::before {
      content: ""; position: absolute; left: 0.2rem; top: 50%; width: 7px; height: 7px; margin-top: -3px;
      border-radius: 50%; background: var(--zen-kaki); opacity: 0; transform: scale(0.4);
      transition: opacity 260ms var(--zen-ease), transform 420ms var(--zen-ease);
    }
    #zenTools button[aria-selected="true"]::before { opacity: 1; transform: none; }
    #zenTools .zl-name { font-family: var(--zen-mincho); font-weight: 500; font-size: clamp(1.4rem, 2.4vw, 2rem); line-height: 1.2; letter-spacing: -0.015em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0; }
    #zenTools .zl-desc { font-family: var(--zen-gothic); font-size: 0.85rem; color: #4a4a4a; line-height: 1.35; transition: color 260ms; min-width: 0; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
    #zenTools button:hover, #zenTools button[aria-selected="true"] { color: var(--zen-washi); }
    #zenTools button:hover .zl-desc, #zenTools button[aria-selected="true"] .zl-desc { color: #111111; }
    #zenTools .zl-empty { font-family: var(--zen-gothic); font-size: 0.85rem; color: #4a4a4a; padding: 0.5rem 0; }
    #zenLauncher .zl-foot { margin-top: 1.6rem; font-family: var(--zen-gothic); font-size: 0.78rem; color: #4a4a4a; letter-spacing: 0.02em; }

    /* ---------- classic windows and the identity gate, re-dressed ---------- */
    body.zen .mesh-window {
      position: fixed;
      max-width: calc(100vw - 2rem);
      max-height: calc(100dvh - 6rem);
      background: rgba(23, 21, 15, 0.9);
      border: 1px solid var(--zen-line);
      border-radius: 14px;
      box-shadow: 0 30px 80px -24px rgba(0, 0, 0, 0.8);
      backdrop-filter: blur(22px) saturate(0.85);
      z-index: 40;
    }
    body.zen .mesh-window .window-header { background: transparent; border-bottom-color: rgba(236, 230, 218, 0.08); }
    body.zen .mesh-window .window-body { overflow: auto; }
    body.zen #accountSetupModal { background: rgba(14, 13, 11, 0.62); backdrop-filter: blur(18px) saturate(0.8); }
    body.zen #accountSetupModal > div {
      background: rgba(23, 21, 15, 0.96); border: 1px solid var(--zen-line); border-radius: 16px;
      box-shadow: 0 40px 100px -30px rgba(0, 0, 0, 0.85);
      max-height: calc(100dvh - 2rem); overflow-y: auto;
    }
    #zenGateBack {
      display: block; margin: 0.5rem auto 0; padding: 0.35rem 0.5rem; color: var(--zen-washi-2);
      font-family: var(--zen-gothic); font-size: 0.9rem; letter-spacing: 0.02em;
      text-decoration: underline; text-decoration-color: rgba(236, 230, 218, 0.3); text-underline-offset: 0.3em;
      transition: color 260ms var(--zen-ease), text-decoration-color 260ms var(--zen-ease);
    }
    #zenGateBack:hover { color: var(--zen-washi); text-decoration-color: var(--zen-washi); }

    /* ---------- phones: the clip is the screen ---------- */
    @media (max-aspect-ratio: 11/16), (max-width: 560px) {
      #zenFrame { height: 100dvh; width: 100vw; aspect-ratio: auto; border-radius: 0; box-shadow: none; }
      #zenFrame::before, #zenFrame::after { content: ""; position: absolute; left: 0; right: 0; z-index: 1; pointer-events: none; }
      #zenFrame::before { top: 0; height: 9rem; background: linear-gradient(rgba(14, 13, 11, 0.82), rgba(14, 13, 11, 0)); }
      #zenFrame::after { bottom: 0; height: 15rem; background: linear-gradient(rgba(14, 13, 11, 0), rgba(14, 13, 11, 0.88)); }
      #zenMark { left: 1.1rem; }
      #zenCaption { left: 1.1rem; right: 5.5rem; max-width: none; bottom: calc(max(1.1rem, env(safe-area-inset-bottom)) + 3.4rem); }
      #zenActions { left: 1.1rem; right: 1.1rem; bottom: max(1.1rem, env(safe-area-inset-bottom)); justify-content: space-between; }
      #zenTicks { right: 1rem; }
      #zenQuick .zq-extra, #zenQuick kbd { display: none; }
      #zenTools button { grid-template-columns: 1fr; gap: 0.15rem; padding: 0.55rem 0 0.55rem 1.4rem; }
      body.zen .mesh-window { left: 0.75rem !important; right: 0.75rem !important; width: auto !important; max-width: none; top: 4rem !important; }
    }

    @media (hover: hover) and (pointer: fine) { #zenMark .zen-hint { display: inline; } }

    @media (prefers-reduced-motion: reduce) {
      #zenFrame { animation: none; }
      #zenFrame, #zenLauncher, .zen-chrome, #zenTools button { transition-duration: 1ms !important; }
    }
  </style>
"""

ZEN_BODY = r"""
  <div id="zenStage" aria-hidden="false">
    <div id="zenFrame" role="button" tabindex="-1" aria-label="Tap for sound">
      <span id="zenClipTag" aria-hidden="true">&#9654;&#xFE0E; Clip</span>
      <video id="zenVideo" playsinline muted autoplay preload="auto"></video>
    </div>
  </div>

  <button id="zenMark" class="zen-btn zen-chrome" type="button" aria-label="Open tools" aria-haspopup="dialog" aria-controls="zenLauncher">
    <svg viewBox="0 0 32 32" aria-hidden="true" fill="none">
      <path d="M26.6 10.4A12 12 0 1 0 27.7 19" stroke="#111111" stroke-width="2.4" stroke-linecap="round"/>
      <circle cx="27.6" cy="14.6" r="1.6" fill="#111111"/>
    </svg>
    <span>TinCan</span>
    <span class="zen-hint">tools · ⌘K</span>
  </button>

  <div id="zenCaption" class="zen-chrome zen-feed-only" aria-live="polite">
    <p class="zen-title" id="zenTitle"></p>
    <p class="zen-meta" id="zenMeta"></p>
  </div>

  <div id="zenActions" class="zen-chrome zen-feed-only">
    <nav id="zenQuick" aria-label="Quick launch">
      <button class="zen-btn" type="button" data-tool="win-terminal">Terminal</button>
      <button class="zen-btn zq-extra" type="button" data-tool="win-agentspace">Space</button>
      <button class="zen-btn zq-extra" type="button" data-tool="win-arena">Arena</button>
      <button class="zen-btn" type="button" data-tool="all" aria-haspopup="dialog" aria-controls="zenLauncher">All tools<kbd>⌘K</kbd></button>
    </nav>
    <button id="zenSound" class="zen-btn" type="button" aria-pressed="false">
      <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
        <path d="M3.5 7.5h2.8L10.5 4v12l-4.2-3.5H3.5z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>
        <path class="zen-wave" d="M13.4 7.2a4 4 0 0 1 0 5.6M15.6 5.2a7 7 0 0 1 0 9.6" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" style="display:none"/>
        <path class="zen-x" d="M13.2 8l4 4M17.2 8l-4 4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
      </svg>
      <span id="zenSoundLabel">Sound off</span>
    </button>
    <button id="zenJoin" class="zen-btn" type="button">Join the mesh</button>
  </div>

  <ol id="zenTicks" class="zen-chrome zen-feed-only" aria-label="Clips"></ol>

  <div id="zenLauncher" role="dialog" aria-modal="true" aria-label="Command bar">
    <div class="zl-inner">
      <label for="zenSearch">
        <input id="zenSearch" type="text" placeholder="Search, @message, > run…" autocomplete="off" spellcheck="false" aria-controls="zenTools" aria-autocomplete="list">
        <kbd>esc</kbd>
      </label>
      <p id="zenHint">Search tools · @ message someone · > run a command · / commands</p>
      <ul id="zenTools" role="listbox" aria-label="Results"></ul>
      <pre id="zenOut" hidden tabindex="0" aria-label="Output"></pre>
      <p id="zenStatus" role="status" aria-live="polite"></p>
      <p class="zl-foot">↑ ↓ to move · enter to run · esc to return to the feed</p>
    </div>
  </div>

  <script>
    (function () {
      if (!document.documentElement.classList.contains('zen-boot')) return;
      if (typeof singleWindowParam !== 'undefined' && singleWindowParam) {
        document.documentElement.classList.remove('zen-boot');
        return;
      }
      const $ = (id) => document.getElementById(id);
      const body = document.body;
      body.classList.add('zen');

      // ---- Tools ---------------------------------------------------------------
      const TOOLS = [
        { id: 'win-mockups', name: 'Design Mockups', desc: 'Updated iOS App & Car UI mockups, contact sheets, and specs', gate: 'view mockups', url: '/designs' },
        { id: 'win-ios', name: 'iOS App Simulator', desc: '9-screen native TinCan 2.2 iOS interactive simulator', gate: 'launch iOS simulator', url: '/ios' },
        { id: 'win-car', name: 'Car Head-Unit', desc: '1280x720 Sumi-Dock aftermarket dashboard UI', gate: 'launch car head-unit', url: '/car' },
        { id: 'win-tv', name: 'Watch party', desc: 'The collection together, with reactions', gate: 'join a watch party' },
        { id: 'chat', name: 'Talk', desc: 'Room chat, voice and video calls', gate: 'talk in the room' },
        { id: 'win-board', name: 'Board', desc: 'Topics, threads and the knowledge graph', gate: 'open the board' },
        { id: 'win-agentspace', name: 'Space', desc: 'Files, code runs and the notes editor', gate: 'open your space' },
        { id: 'win-terminal', name: 'Terminal', desc: 'Quickstart and commands', gate: 'open the terminal' },
        { id: 'win-arena', name: 'Arena', desc: 'AI models, routing and duels', gate: 'use the AI arena' },
        { id: 'win-network', name: 'Network', desc: "Who's here, peers and the leaderboard", gate: 'see the network' },
        { id: 'win-quests', name: 'Quests', desc: 'Quests, XP and rankings', gate: 'start quests' },
        { id: 'win-billing', name: 'Tokens', desc: 'Balance, store and sponsors', gate: 'manage tokens' },
        { id: 'win-moderator', name: 'Moderate', desc: 'Admin controls', gate: 'moderate', admin: true },
      ];
      const isAdmin = () => {
        const b = $('dockModBtn');
        return !!b && !b.classList.contains('hidden') && b.style.display !== 'none';
      };

      // ---- Calm start: close every window the classic desktop opened ------------
      function closeAllWindows() {
        document.querySelectorAll('.mesh-window').forEach((w) => {
          if (typeof minimizeWindow === 'function') minimizeWindow(w.id);
          else { w.classList.add('hidden'); w.style.display = 'none'; }
        });
        const tv = $('relayNativeVideo');
        if (tv) { try { tv.pause(); } catch (e) {} }
      }
      closeAllWindows();

      // ---- Identity gate waits until a visitor reaches for a tool --------------
      let gateArmed = false;
      const classicOpenAccount = window.openAccountModal;
      if (typeof classicOpenAccount === 'function') {
        window.openAccountModal = function () {
          if (!gateArmed) return;
          return classicOpenAccount.apply(this, arguments);
        };
      }
      const verified = () => (typeof isIdentityVerified === 'function' ? isIdentityVerified() : true);
      function requireIdentity(what) {
        gateArmed = true;
        if (typeof requireVerifiedIdentity === 'function') return requireVerifiedIdentity(what);
        return true;
      }
      const gateCard = document.querySelector('#accountSetupModal > div');
      if (gateCard && !$('zenGateBack')) {
        const back = document.createElement('button');
        back.id = 'zenGateBack';
        back.type = 'button';
        back.className = 'zen-btn';
        back.textContent = 'Not now — back to the feed';
        back.addEventListener('click', dismissGate);
        gateCard.appendChild(back);
        $('accountSetupModal').addEventListener('click', (e) => { if (e.target === $('accountSetupModal')) dismissGate(); });
      }
      function dismissGate() {
        if (verified()) return;
        $('accountSetupModal').classList.add('hidden');
        gateArmed = false;
      }

      // ---- Working state follows the classic window manager ---------------------
      const anyWindowOpen = () => Array.from(document.querySelectorAll('.mesh-window')).some(
        (w) => w.style.display !== 'none' && !w.classList.contains('hidden') && !w.classList.contains('minimized')
      );
      function syncWorking() {
        const working = anyWindowOpen();
        body.classList.toggle('zen-working', working);
        if (working) video.pause();
        else if (!body.classList.contains('zen-launcher')) playQuietly();
      }
      const classicSync = window.syncDockIndicators;
      if (typeof classicSync === 'function') {
        window.syncDockIndicators = function () {
          try { classicSync.apply(this, arguments); } catch (e) {}
          syncWorking();
        };
      }

      function place(winId) {
        const w = $(winId);
        if (!w) return;
        w.style.right = 'auto';
        const r = w.getBoundingClientRect();
        const width = Math.min(r.width, window.innerWidth - 32);
        const height = Math.min(r.height, window.innerHeight - 96);
        w.style.left = Math.max(16, Math.round((window.innerWidth - width) / 2)) + 'px';
        w.style.top = Math.max(56, Math.round((window.innerHeight - height) / 2)) + 'px';
      }

      function openTool(tool) {
        closeLauncher(false);
        if (tool.url) {
          window.location.href = tool.url;
          return;
        }
        if (!requireIdentity(tool.gate)) return;
        if (tool.id === 'chat') {
          if (typeof focusChatWindow === 'function') focusChatWindow();
          place('win-comms');
        } else {
          const w = $(tool.id);
          if (!w) return;
          const hidden = w.style.display === 'none' || w.classList.contains('hidden') || w.classList.contains('minimized');
          if (hidden && typeof toggleWindow === 'function') toggleWindow(tool.id);
          else if (typeof bringToFront === 'function') bringToFront(w);
          place(tool.id);
        }
        syncWorking();
      }

      // ---- Feed -----------------------------------------------------------------
      const video = $('zenVideo');
      const frame = $('zenFrame');
      let clips = [];
      let index = 0;
      let soundOn = false;
      let switching = false;
      let zenAdWatchCompleted = false;
      let zenAdMaxWatched = 0;

      // This clip is a screen recording of the Aleploi voice app, so label it as that.
      const FALLBACK = [{ embed_url: '/videos/7705677376465767711.mp4', title: 'Aleploi Voice demo (screen recording)', creator: '@nojuannobody' }];

      function playQuietly() {
        if (!video.src || body.classList.contains('zen-working')) return;
        const p = video.play();
        if (p && p.catch) p.catch(() => {});
      }

      function renderTicks() {
        const ol = $('zenTicks');
        ol.innerHTML = '';
        if (clips.length < 2) return;
        clips.forEach((c, i) => {
          const li = document.createElement('li');
          const b = document.createElement('button');
          b.type = 'button';
          b.className = 'zen-btn';
          b.setAttribute('aria-label', `Clip ${i + 1}: ${c.title || 'untitled'}`);
          b.addEventListener('click', () => go(i));
          li.appendChild(b);
          ol.appendChild(li);
        });
      }

      function show(i) {
        const c = clips[i];
        const isAd = c && (c.category === 'ad' || c.category === 'community_video');
        zenAdWatchCompleted = !isAd;
        zenAdMaxWatched = 0;
        video.src = c.embed_url || c.cite_url;
        video.muted = !soundOn;
        $('zenTitle').textContent = c.title || '';
        $('zenClipTag').textContent = '\u25B6\uFE0E Clip ' + (i + 1) + '/' + clips.length + (c.creator ? ' · ' + c.creator : '');
        const meta = [
          c.creator,
          isAd ? (isAdmin() ? '🛡️ Intelligence Gathering · Ad View Required' : 'Sponsored') : ''
        ].filter(Boolean).join(' · ');
        $('zenMeta').textContent = meta;
        document.querySelectorAll('#zenTicks button').forEach((b, j) => {
          b.setAttribute('aria-current', j === i ? 'true' : 'false');
          if (isAdmin() && isAd && !zenAdWatchCompleted && j !== i) {
            b.style.opacity = '0.3';
            b.style.pointerEvents = 'none';
          } else {
            b.style.opacity = '';
            b.style.pointerEvents = '';
          }
        });
        playQuietly();
      }

      function canSkipZenClip() {
        const c = clips[index];
        const isAd = c && (c.category === 'ad' || c.category === 'community_video');
        if (isAdmin() && isAd && !zenAdWatchCompleted) {
          flashZenIntelNotice();
          return false;
        }
        return true;
      }

      function flashZenIntelNotice() {
        const meta = $('zenMeta');
        if (meta) {
          const orig = meta.textContent;
          meta.textContent = '🔒 Intelligence Gathering Active · Admins must watch ads in full!';
          meta.style.color = '#fbbf24';
          setTimeout(() => {
            meta.textContent = orig;
            meta.style.color = '';
          }, 1800);
        }
      }

      function go(target) {
        if (switching || !clips.length) return;
        if (!canSkipZenClip()) return;
        const next = (target + clips.length) % clips.length;
        if (next === index && video.src) return;
        const down = target > index || (index === clips.length - 1 && next === 0);
        switching = true;
        frame.classList.add(down ? 'zen-leave-up' : 'zen-leave-down');
        setTimeout(() => {
          index = next;
          frame.classList.remove('zen-leave-up', 'zen-leave-down');
          frame.classList.add(down ? 'zen-enter-up' : 'zen-enter-down');
          show(index);
          void frame.offsetWidth;
          frame.classList.remove('zen-enter-up', 'zen-enter-down');
          setTimeout(() => { switching = false; }, 380);
        }, 300);
      }
      const nextClip = () => go(index + 1);
      const prevClip = () => go(index - 1);

      video.addEventListener('loadedmetadata', () => {
        if (video.videoWidth && video.videoHeight) frame.style.setProperty('--zen-ar', (video.videoWidth / video.videoHeight).toFixed(4));
      });
      video.addEventListener('timeupdate', () => {
        const c = clips[index];
        const isAd = c && (c.category === 'ad' || c.category === 'community_video');
        if (isAdmin() && isAd) {
          zenAdMaxWatched = Math.max(zenAdMaxWatched, video.currentTime);
        }
      });
      video.addEventListener('seeking', () => {
        const c = clips[index];
        const isAd = c && (c.category === 'ad' || c.category === 'community_video');
        if (isAdmin() && isAd && !zenAdWatchCompleted) {
          if (video.currentTime > zenAdMaxWatched + 1.0) {
            video.currentTime = zenAdMaxWatched;
          }
        }
      });
      video.addEventListener('ended', () => {
        const c = clips[index];
        const isAd = c && (c.category === 'ad' || c.category === 'community_video');
        if (isAdmin() && isAd) {
          zenAdWatchCompleted = true;
          document.querySelectorAll('#zenTicks button').forEach((b) => {
            b.style.opacity = '';
            b.style.pointerEvents = '';
          });
          fetch('/api/ads/intel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              peer_id: localStorage.getItem('tincan_peer_id') || 'admin-zen',
              video_id: c.video_id || c.id || 'zen-ad',
              title: c.title || 'Sponsored Ad',
              category: 'ad',
              metadata: { source: 'zen_feed', watched_duration: zenAdMaxWatched }
            })
          }).catch(() => {});
        }
        nextClip();
      });
      video.addEventListener('error', () => { if (clips.length > 1) setTimeout(nextClip, 600); });

      function setSound(on) {
        soundOn = on;
        video.muted = !on;
        if (on) playQuietly();
        $('zenSound').setAttribute('aria-pressed', on ? 'true' : 'false');
        $('zenSoundLabel').textContent = on ? 'Sound on' : 'Sound off';
        $('zenSound').querySelector('.zen-wave').style.display = on ? '' : 'none';
        $('zenSound').querySelector('.zen-x').style.display = on ? 'none' : '';
        frame.setAttribute('aria-label', on ? 'Tap to mute' : 'Tap for sound');
      }
      $('zenSound').addEventListener('click', () => setSound(!soundOn));
      frame.addEventListener('click', () => { if (feedHasFocus()) setSound(!soundOn); });

      fetch('/api/playlist').then((r) => r.json()).then((d) => {
        const vids = (d && d.videos) || [];
        clips = vids.filter((v) => v.embed_url || v.cite_url);
        if (!clips.length) clips = FALLBACK;
      }).catch(() => { clips = FALLBACK; }).then(() => {
        renderTicks();
        show(0);
      });

      // ---- Launcher ---------------------------------------------------------------
      let filtered = [];
      let sel = 0;
      let busy = false;
      const SLASH = [
        { cmd: '/terminal', tool: 'win-terminal', desc: 'Quickstart and commands' },
        { cmd: '/space', tool: 'win-agentspace', desc: 'Files, code runs and the notes editor' },
        { cmd: '/arena', tool: 'win-arena', desc: 'AI models, routing and duels' },
        { cmd: '/board', tool: 'win-board', desc: 'Topics, threads and the knowledge graph' },
        { cmd: '/talk', tool: 'chat', desc: 'Room chat, voice and video calls' },
        { cmd: '/tokens', tool: 'win-billing', desc: 'Balance, store and sponsors' },
        { cmd: '/quests', tool: 'win-quests', desc: 'Quests, XP and rankings' },
        { cmd: '/help', help: true, desc: 'Show what the prefixes do' },
      ];
      const HELP_TEXT = 'Search tools      type a name, enter opens it\n' +
        '@name message     tag someone in the room chat\n' +
        '> command         run a command in your space ($ works too)\n' +
        '/command          /terminal /space /arena /board /talk /tokens /quests /help\n' +
        'Tab completes an @name, esc returns to the feed';

      // ---- Command bar adapters (one small seam per outside system) ----------------
      const peerId = () => (typeof myPeerId !== 'undefined' && myPeerId) || 'zen';
      const roomName = () => ((($('roomInput') || {}).value || '').trim() || 'main');
      const spaceScope = () => (typeof termScope === 'function' ? termScope() : 'user');
      const spaceOwner = () => (typeof termOwner === 'function' ? termOwner() : peerId());
      async function postJson(url, payload) {
        const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        const d = await r.json().catch(() => ({}));
        if (!r.ok || d.error) throw new Error(d.error || ('HTTP ' + r.status));
        return d;
      }
      async function spaceExec(body) {
        return postJson('/api/space/exec', Object.assign({ scope: spaceScope(), owner_id: spaceOwner() }, body));
      }
      // Shell adapter: the shared TinCanShell interpreter when the page has it, else a small
      // headless interpreter over the same /api/space/* endpoints the Terminal uses.
      async function runShell(line) {
        if (window.TinCanShell && typeof window.TinCanShell.run === 'function') return window.TinCanShell.run(line);
        return legacyShell(line);
      }
      async function legacyShell(line) {
        const [verb, ...rest] = line.split(/\s+/);
        const arg = rest.join(' ');
        const fmt = (d) => ((d.stdout || '') + (d.stderr ? '\n' + d.stderr : '')) || ('exit ' + d.exit_code);
        try {
          if (verb === 'help') return { ok: true, text: 'ls [dir]    list files in your space\nrun [file]  run a file in the sandbox (default /src/main.py)\npy <code>   run Python in the sandbox\nruns        list recent runs\nstatus      mesh room status\nask <q>     ask the AI gateway\nclear       clear this output' };
          if (verb === 'ls') {
            const r = await fetch('/api/space/ls?scope=' + encodeURIComponent(spaceScope()) + '&owner_id=' + encodeURIComponent(spaceOwner()), { cache: 'no-store' });
            const s = await r.json();
            if (!r.ok || s.error) throw new Error(s.error || ('HTTP ' + r.status));
            const dir = arg ? ('/' + arg.replace(/^\/+|\/+$/g, '') + '/') : '/';
            const names = new Set();
            (s.files || []).forEach((f) => {
              if (!String(f.path).startsWith(dir)) return;
              const tail = String(f.path).slice(dir.length);
              names.add(tail.includes('/') ? tail.split('/')[0] + '/' : tail);
            });
            return { ok: true, text: names.size ? Array.from(names).sort().join('  ') : 'ls: ' + dir + ': no files' };
          }
          if (verb === 'run') return { ok: true, text: fmt(await spaceExec({ entrypoint: arg ? (arg.startsWith('/') ? arg : '/' + arg) : '/src/main.py', runtime: 'auto' })) };
          if (verb === 'py' || verb === 'exec') return { ok: true, text: fmt(await spaceExec({ runtime: 'python', code_override: arg })) };
          if (verb === 'runs') {
            const r = await fetch('/api/space/ls?scope=' + encodeURIComponent(spaceScope()) + '&owner_id=' + encodeURIComponent(spaceOwner()), { cache: 'no-store' });
            const s = await r.json();
            return { ok: true, text: (s.recent_runs || []).map((x) => (x.runtime + '  exit ' + x.exit_code + '  ' + x.duration_ms + 'ms  ' + (x.entrypoint || '(inline)'))).join('\n') || 'No runs yet.' };
          }
          if (verb === 'status') {
            const d = await (await fetch('/api/mesh/state')).json();
            return { ok: true, text: 'room ' + (d.room || 'main') + ' · ' + Object.keys(d.peers || {}).length + ' peers · relay online' };
          }
          if (verb === 'ask' && arg) return { ok: true, text: await askAI(arg) };
          return { ok: false, text: verb + ': command not found. Type help.' };
        } catch (e) {
          return { ok: false, text: verb + ': ' + e.message };
        }
      }
      async function askAI(prompt) {
        const d = await postJson('/api/chat', { model: 'gemini-brain', prompt: prompt, peer_id: peerId() });
        return d.content || d.response || JSON.stringify(d);
      }
      // Room chat: reuse the Talk window's send path so the message also lands in this user's own log.
      async function sendRoom(text) {
        const input = $('chatInput');
        if (input && typeof sendChatMessage === 'function') {
          input.value = text;
          await sendChatMessage();
          return;
        }
        const name = (typeof getVerifiedDisplayName === 'function' ? getVerifiedDisplayName() : peerId());
        await postJson('/api/webrtc/signal', { from: peerId(), to: '*', type: 'chat', room: roomName(), payload: { text: text, sender: name, timestamp: Date.now() } });
      }

      // ---- People (@): the board roster, loaded when the bar opens ------------------
      let people = [];
      let peopleAt = 0;
      async function loadPeople() {
        if (Date.now() - peopleAt < 30000) return;
        peopleAt = Date.now();
        try {
          const r = await fetch('/api/board/roster');
          if (!r.ok) return;
          const d = await r.json();
          people = (d.users || []).map((u) => ({
            handle: String(u.username || '').replace(/^@+/, ''),
            name: u.full_name || '',
            role: u.role || 'Peer',
            verified: !!u.verified,
          })).filter((u) => u.handle);
          if (body.classList.contains('zen-launcher') && $('zenSearch').value.trim().startsWith('@')) renderTools();
        } catch (e) { peopleAt = 0; }
      }

      // ---- Output pane + status ------------------------------------------------------
      let outLines = [];
      function showOut(lines) {
        const pre = $('zenOut');
        if (lines === null) { outLines = []; pre.hidden = true; pre.textContent = ''; return; }
        outLines = lines.slice(-200);
        pre.textContent = outLines.join('\n');
        pre.hidden = !outLines.length;
        pre.scrollTop = pre.scrollHeight;
      }
      const appendOut = (text) => showOut(outLines.concat(String(text).split('\n')));
      function setStatus(msg) { $('zenStatus').textContent = msg || ''; }

      // ---- Result building -----------------------------------------------------------
      const subseq = (text, q) => { let i = 0; for (const c of text) { if (c === q[i]) i++; if (i === q.length) return true; } return !q.length; };
      function toolItem(t) {
        return { act: 'Open', name: t.name, desc: t.desc, run: () => openTool(t) };
      }
      function cmdItem(act, name, desc, run, extra) {
        return Object.assign({ act: act, name: name, desc: desc, cmd: true, run: run }, extra || {});
      }
      function gated(what, fn) {
        return async () => {
          if (!requireIdentity(what)) return;
          if (busy) return;
          busy = true;
          try { await fn(); } catch (e) { setStatus('Failed: ' + e.message); } finally { busy = false; }
        };
      }
      async function doSend(text, label) {
        setStatus('Sending…');
        await sendRoom(text);
        $('zenSearch').value = '';
        sel = 0;
        setStatus('');
        showOut(null);
        loadPeople();
        renderTools();
        setStatus('Sent' + (label ? ' to ' + label : '') + ' · #' + roomName());
      }
      async function doAsk(prompt) {
        showOut(['> ask ' + prompt, 'Asking the AI gateway…']);
        try {
          const text = await askAI(prompt);
          showOut(['> ask ' + prompt].concat(text.split('\n')));
        } catch (e) {
          showOut(['> ask ' + prompt, 'Error: ' + e.message]);
        }
      }
      function doBoard(q) {
        const tool = TOOLS.find((t) => t.id === 'win-board');
        openTool(tool);
        setTimeout(() => {
          const inp = $('boardSearchInput');
          if (!inp) return;
          inp.value = q;
          if (typeof searchCyberspaceBoard === 'function') searchCyberspaceBoard();
        }, 120);
      }
      async function doShell(line) {
        const pre = $('zenOut');
        if (line === 'clear') { showOut(null); $('zenSearch').value = ''; renderTools(); return; }
        appendOut('$ ' + line);
        setStatus('Running…');
        const res = await runShell(line);
        const text = String((res && res.text) != null ? res.text : '').replace(/\s+$/, '');
        appendOut(text || '(no output)');
        setStatus(res && res.ok ? 'Done' : 'Exited with an error');
        $('zenSearch').value = '';
        sel = 0;
        renderTools();
        pre.scrollTop = pre.scrollHeight;
        $('zenSearch').focus();
      }

      function buildItems(raw) {
        const q = raw.trim();
        const ql = q.toLowerCase();
        const first = q.charAt(0);
        if (first === '>' || first === '$') {
          const line = q.slice(1).trim();
          if (!line) return [cmdItem('Run', 'Type a command', 'ls · run · py print(1) · help', () => {}, { idle: true })];
          return [cmdItem('Run', line, 'Run in your space', gated('run commands', () => doShell(line)))];
        }
        if (first === '/') {
          const word = ql.split(/\s+/)[0];
          return SLASH.filter((c) => c.cmd.startsWith(word)).map((c) => cmdItem(c.help ? 'Help' : 'Open', c.cmd, c.desc, () => {
            if (c.help) { showOut(HELP_TEXT.split('\n')); $('zenSearch').value = ''; sel = 0; renderTools(); return; }
            openTool(TOOLS.find((t) => t.id === c.tool));
          }, { complete: c.cmd }));
        }
        if (first === '@') {
          const m = q.match(/^@(\S*)(?:\s+([\s\S]*))?$/);
          const typed = (m ? m[1] : '').toLowerCase();
          const msg = m && m[2] ? m[2].trim() : '';
          const matches = people.filter((u) => u.handle.toLowerCase().startsWith(typed) || u.name.toLowerCase().includes(typed) && typed.length > 1);
          const exact = people.find((u) => u.handle.toLowerCase() === typed);
          if (!msg) {
            const list = matches.slice(0, 8).map((u) => cmdItem('Tag', '@' + u.handle, (u.verified ? 'verified · ' : '') + (u.name ? u.name + ' · ' : '') + u.role,
              () => { $('zenSearch').value = '@' + u.handle + ' '; sel = 0; renderTools(); $('zenSearch').focus(); }, { complete: '@' + u.handle + ' ' }));
            if (!list.length) list.push(cmdItem('Tag', '@' + typed, typed ? 'Not on the roster yet. Keep typing a message to tag them anyway.' : 'Nobody on the roster yet.', () => {}, { idle: true }));
            return list;
          }
          const target = exact || (matches.length === 1 ? matches[0] : null);
          const handle = target ? target.handle : (m ? m[1] : '');
          const text = '@' + handle + ' ' + msg;
          return [cmdItem('Send', 'Tag @' + handle + ' in the room', msg, gated('send messages in the room chat', () => doSend(text, '@' + handle)))];
        }
        const items = TOOLS.filter((t) => (!t.admin || isAdmin()) &&
          (!ql || t.name.toLowerCase().includes(ql) || t.desc.toLowerCase().includes(ql) || (ql.length >= 4 && subseq(t.name.toLowerCase(), ql)))).map(toolItem);
        if (q) {
          items.push(cmdItem('Send', 'Send to room', q, gated('send messages in the room chat', () => doSend(q, ''))));
          items.push(cmdItem('Ask AI', 'Ask AI', q, gated('use the AI gateway', () => doAsk(q))));
          items.push(cmdItem('Board', 'Search the board', q, () => { if (requireIdentity('open the board')) doBoard(q); }));
        }
        return items;
      }
      function runSelected() {
        const it = filtered[sel];
        if (!it || it.idle) return;
        it.run();
      }
      function renderTools() {
        const raw = $('zenSearch').value;
        $('zenHint').hidden = !!raw.trim();
        filtered = buildItems(raw);
        sel = Math.min(sel, Math.max(0, filtered.length - 1));
        const ul = $('zenTools');
        ul.innerHTML = '';
        if (!filtered.length) {
          const li = document.createElement('li');
          li.className = 'zl-empty';
          li.textContent = raw.trim().charAt(0) === '/' ? 'No such command. Try /help.' : 'Nothing by that name.';
          ul.appendChild(li);
          return;
        }
        filtered.forEach((t, i) => {
          const li = document.createElement('li');
          const b = document.createElement('button');
          b.type = 'button';
          b.className = t.cmd ? 'zl-cmd' : '';
          b.setAttribute('role', 'option');
          b.setAttribute('aria-selected', i === sel ? 'true' : 'false');
          b.innerHTML = '<span class="zl-name"></span><span class="zl-desc"></span><span class="zl-act"></span>';
          b.children[0].textContent = t.name;
          b.children[1].textContent = t.desc;
          b.children[2].textContent = t.act;
          if (t.cmd) { b.children[1].style.gridColumn = '1'; b.children[2].style.gridRow = '1 / span 2'; b.children[2].style.gridColumn = '2'; }
          b.addEventListener('click', () => { sel = i; runSelected(); });
          b.addEventListener('mousemove', () => { if (sel !== i) { sel = i; mark(); } });
          li.appendChild(b);
          ul.appendChild(li);
        });
      }
      function mark() {
        document.querySelectorAll('#zenTools button').forEach((b, i) => b.setAttribute('aria-selected', i === sel ? 'true' : 'false'));
      }
      let lastFocus = null;
      function openLauncher() {
        if (body.classList.contains('zen-launcher')) return;
        lastFocus = document.activeElement;
        $('zenSearch').value = '';
        sel = 0;
        renderTools();
        body.classList.add('zen-launcher');
        setTimeout(() => $('zenSearch').focus(), 60);
      }
      function closeLauncher(restoreFocus = true) {
        if (!body.classList.contains('zen-launcher')) return;
        body.classList.remove('zen-launcher');
        if (restoreFocus && lastFocus && lastFocus.focus) lastFocus.focus();
        if (!anyWindowOpen()) playQuietly();
      }
      $('zenMark').addEventListener('click', () => (body.classList.contains('zen-launcher') ? closeLauncher() : openLauncher()));
      $('zenLauncher').addEventListener('click', (e) => { if (e.target === $('zenLauncher')) closeLauncher(); });
      document.querySelectorAll('#zenQuick button').forEach((b) => b.addEventListener('click', () => {
        const id = b.dataset.tool;
        if (id === 'all') { openLauncher(); return; }
        const tool = TOOLS.find((t) => t.id === id);
        if (tool) openTool(tool);
      }));
      $('zenSearch').addEventListener('input', () => { sel = 0; setStatus(''); renderTools(); });

      function refreshJoin() {
        const u = (localStorage.getItem('tincan_username') || '').trim().replace(/^@+/, '');
        $('zenJoin').textContent = verified() && u ? '@' + u : 'Join the mesh';
        $('zenJoin').title = verified() && u ? 'Signed in as @' + u + ' · open tools' : 'Create your TinCan identity';
      }
      $('zenJoin').addEventListener('click', () => {
        if (verified()) openLauncher();
        else { gateArmed = true; classicOpenAccount && classicOpenAccount(true); }
      });
      refreshJoin();
      window.addEventListener('storage', refreshJoin);
      setInterval(refreshJoin, 4000);

      // ---- Keys, wheel, touch -------------------------------------------------------
      const typing = (el) => el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT' || el.isContentEditable);
      const gateOpen = () => { const m = $('accountSetupModal'); return m && !m.classList.contains('hidden'); };
      const feedHasFocus = () => !body.classList.contains('zen-launcher') && !anyWindowOpen() && !gateOpen();

      // The classic UI swallows Escape in the capture phase while unverified; listen on the same phase.
      window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && gateOpen() && !verified()) { e.preventDefault(); dismissGate(); }
      }, true);

      window.addEventListener('keydown', (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
          if (gateOpen()) return;
          e.preventDefault();
          body.classList.contains('zen-launcher') ? closeLauncher() : openLauncher();
          return;
        }
        if (body.classList.contains('zen-launcher')) {
          if (e.key === 'Escape') { e.preventDefault(); closeLauncher(); }
          else if (e.key === 'ArrowDown') { e.preventDefault(); if (filtered.length) { sel = (sel + 1) % filtered.length; mark(); } }
          else if (e.key === 'ArrowUp') { e.preventDefault(); if (filtered.length) { sel = (sel - 1 + filtered.length) % filtered.length; mark(); } }
          else if (e.key === 'Enter') { e.preventDefault(); runSelected(); }
          else if (e.key === 'Tab' && filtered[sel] && filtered[sel].complete) { e.preventDefault(); $('zenSearch').value = filtered[sel].complete; sel = 0; renderTools(); }
          return;
        }
        if (typing(document.activeElement)) return;
        if (e.key === 'Escape' && anyWindowOpen() && !gateOpen()) {
          const focused = document.querySelector('.mesh-window.window-focused');
          if (focused && typeof minimizeWindow === 'function') { minimizeWindow(focused.id); e.preventDefault(); }
          return;
        }
        if (!feedHasFocus()) return;
        if (e.key === '/') { e.preventDefault(); openLauncher(); }
        else if (e.key === 'ArrowDown' || e.key === 'PageDown' || e.key === 'j') { e.preventDefault(); nextClip(); }
        else if (e.key === 'ArrowUp' || e.key === 'PageUp' || e.key === 'k') { e.preventDefault(); prevClip(); }
        else if (e.key === 'm') setSound(!soundOn);
        else if (e.key === ' ') { e.preventDefault(); video.paused ? playQuietly() : video.pause(); }
      });

      let wheelAcc = 0;
      let wheelLock = 0;
      window.addEventListener('wheel', (e) => {
        if (!feedHasFocus() || e.target.closest('.mesh-window')) return;
        const now = Date.now();
        if (now < wheelLock) return;
        wheelAcc += e.deltaY;
        if (Math.abs(wheelAcc) > 70) {
          wheelAcc > 0 ? nextClip() : prevClip();
          wheelAcc = 0;
          wheelLock = now + 900;
        }
      }, { passive: true });

      let touchY = null;
      $('zenStage').addEventListener('touchstart', (e) => { touchY = e.touches[0].clientY; }, { passive: true });
      $('zenStage').addEventListener('touchend', (e) => {
        if (touchY === null || !feedHasFocus()) return;
        const dy = e.changedTouches[0].clientY - touchY;
        touchY = null;
        if (Math.abs(dy) > 50) (dy < 0 ? nextClip : prevClip)();
      }, { passive: true });

      document.addEventListener('visibilitychange', () => { if (document.hidden) video.pause(); else if (feedHasFocus()) playQuietly(); });

      document.documentElement.classList.remove('zen-boot');
    })();
  </script>
"""


def apply_zen_shell(html: str) -> str:
    """Inject the zen startup shell into the classic Mesh OS HTML (idempotent)."""
    if 'id="zenStage"' in html:
        return html
    head_end = html.find("</head>")
    body_end = html.rfind("</body>")
    if head_end == -1 or body_end == -1:
        return html
    html = html[:head_end] + ZEN_HEAD + html[head_end:]
    body_end = html.rfind("</body>")
    return html[:body_end] + ZEN_BODY + html[body_end:]
