"""TinCan Mesh OS — terminal theme.

Every window speaks the Terminal window's language (docs/designs/aeonik-terminal.png):
celadon paper, sumi ink, one hairline weight, monospace text, square panes, a big
grotesk title over a small clock, a path on the right and a status bar underneath.
Colour is reserved for the content people bring (video, images), never the chrome.

Applied as a post-process after the zen shell (`apply_terminal_theme`) so the classic
window markup keeps working. It also carries the two engines that need real behaviour:
`tcTerm` (the browser shell in win-terminal) and `tcComms` (the chat room in win-comms).
"""

THEME_HEAD = r"""
  <link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
  <script>
    // A popped-out window (or a single-window route) shows only that window, full-bleed:
    // none of the desktop around it (old HUD, dock, feed, launcher mark).
    (function () {
      var q = new URLSearchParams(location.search);
      var single = ['/tv', '/call', '/arena', '/terminal', '/billing', '/tokens', '/board', '/cyberspace'];
      if (q.get('window') || single.indexOf(location.pathname) !== -1) document.documentElement.classList.add('tc-popout');
    })();
  </script>
  <script id="tcAdCreditsScript">
    // Passive ad credits, shared by the feed and the Watch Party player. When a sponsored
    // clip starts, the server issues a one-time view token; once the clip has actually played
    // its length (seeks and loops don't count) the client redeems it and the server credits
    // AI tokens after checking its own clock. Daily cap and sign-in are enforced server-side.
    window.tcAdCredits = (function () {
      const peerId = () => { try { return localStorage.getItem('tincan_peer_id') || ''; } catch (e) { return ''; } };
      const isAdClip = (c) => !!c && (c.category === 'ad' || c.category === 'community_video' || !!c.sponsor_id);
      const sponsorIdFor = (c) => c.sponsor_id || ('video-' + (c.video_id || c.id || ''));
      const shared = { balance: null, today: 0, hint: '' };
      const listeners = new Set();
      let toastEl = null;

      function toast(text) {
        if (!toastEl) {
          toastEl = document.createElement('div');
          toastEl.id = 'tcCreditToast';
          toastEl.setAttribute('role', 'status');
          toastEl.setAttribute('aria-live', 'polite');
          document.body.appendChild(toastEl);
        }
        toastEl.textContent = text;
        toastEl.classList.add('tc-show');
        clearTimeout(toastEl._h);
        toastEl._h = setTimeout(() => toastEl.classList.remove('tc-show'), 2600);
      }
      function emit() { listeners.forEach((fn) => fn()); }
      function refreshBalance() {
        const id = peerId();
        if (!id) return;
        fetch('/api/account/get?peer_id=' + encodeURIComponent(id)).then((r) => (r.ok ? r.json() : null)).then((d) => {
          if (d && d.account) { shared.balance = d.account.token_balance || 0; if (shared.hint === 'register') shared.hint = ''; }
          emit();
        }).catch(() => {});
      }

      function track(video, onState) {
        let view = null;   // { token, minSeconds, startedAt, watched, done, last }
        const state = () => ({
          balance: shared.balance, today: shared.today, hint: shared.hint,
          earning: view && view.token && !view.done ? Math.min(100, (view.watched / target(view)) * 100) : null,
        });
        const notify = () => { if (onState) onState(state()); };
        listeners.add(notify);
        // Listed durations are often longer than the real file, so the goal is whichever is shorter.
        const target = (v) => Math.max(1, Math.min(v.minSeconds, video.duration || Infinity) * 0.92);

        function redeem(v, attempt) {
          fetch('/api/ads/view/complete', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ peer_id: peerId(), view_token: v.token }),
          }).then((r) => r.json().then((d) => ({ ok: r.ok, d }))).then(({ ok, d }) => {
            if (ok && d.status === 'credited') {
              const n = Number(d.reward_tokens) || 0;
              shared.today += n;
              if (d.account && typeof d.account.token_balance === 'number') shared.balance = d.account.token_balance;
              toast(`+${n.toLocaleString()} AI credits`);
            } else if (/not complete/i.test(d.error || '') && attempt < 4) {
              setTimeout(() => redeem(v, attempt + 1), 1500);
            }
            emit();
          }).catch(() => { if (attempt < 4) setTimeout(() => redeem(v, attempt + 1), 3000); });
        }
        // The server credits once the token is old enough for the listed duration. If the clip
        // finished sooner, wait out the gap in the background; the feed keeps moving meanwhile.
        function complete(v) {
          if (v.done) return;
          v.done = true;
          const wait = Math.max(0, v.minSeconds * 0.9 + 0.6 - (performance.now() - v.startedAt) / 1000);
          setTimeout(() => redeem(v, 0), wait * 1000);
          notify();
        }

        video.addEventListener('timeupdate', () => {
          const v = view;
          if (!v || v.done || !v.token) return;
          const now = video.currentTime;
          if (v.last !== null && !video.paused && !document.hidden) {
            const step = now - v.last;
            if (step > 0 && step < 1.5) v.watched += step;   // seeks and loop resets don't count
          }
          v.last = now;
          notify();
          if (v.watched >= target(v)) complete(v);
        });

        return {
          clip(c) {
            view = null;
            if (!isAdClip(c) || shared.hint === 'cap') { notify(); return; }
            const v = { token: null, minSeconds: Number(c.duration_seconds) || 10, startedAt: 0, watched: 0, done: false, last: null };
            view = v;
            fetch('/api/ads/view/start', {
              method: 'POST', headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ peer_id: peerId(), sponsor_id: sponsorIdFor(c) }),
            }).then((r) => r.json().then((d) => ({ ok: r.ok, status: r.status, d }))).then(({ ok, status, d }) => {
              if (view !== v) return;
              if (ok && d.view_token) { v.token = d.view_token; v.startedAt = performance.now(); v.minSeconds = Number(d.min_seconds) || v.minSeconds; }
              else if (status === 429) shared.hint = 'cap';
              else if (/register/i.test(d.error || '')) shared.hint = 'register';
              emit();
            }).catch(() => {});
          },
        };
      }

      refreshBalance();
      setInterval(refreshBalance, 60000);
      return { track, isAdClip, refreshBalance };
    })();
  </script>
  <style id="tcTheme">
    :root {
      --tc-paper: #ecf1e6;
      --tc-paper-2: #e2e9da;
      --tc-ink: #111111;
      --tc-ink-2: #3d413a;
      --tc-ink-3: #6a6f66;
      --tc-hair: rgba(17, 17, 17, 0.22);
      --tc-hair-2: rgba(17, 17, 17, 0.1);
      --tc-mono: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
      --tc-sans: "Inter Tight", -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
    }

    /* ---------- the room around the windows: paper, not paint ---------- */
    body.zen #zenWash { display: none !important; }
    body.zen #zenStage { background: var(--tc-paper) !important; }
    body.zen #zenBackdrop { filter: blur(48px) grayscale(1) contrast(0.9) brightness(1.25) !important; opacity: 0.22 !important; }
    body.zen #zenGrain { opacity: 0.07 !important; mix-blend-mode: multiply !important; }
    body.zen #zenFrame { border-radius: 4px !important; box-shadow: 0 0 0 1px var(--tc-ink), 0 30px 60px -36px rgba(17, 17, 17, 0.5) !important; }
    body.zen-working #zenFrame { opacity: 0.18 !important; filter: blur(8px) grayscale(1) !important; }
    body.zen #zenCaption { text-shadow: none !important; font-family: var(--tc-mono); }
    body.zen #zenCaption .zen-title { font-family: var(--tc-sans) !important; font-size: 1.25rem !important; letter-spacing: -0.01em; }
    body.zen #zenCaption .zen-meta { font-family: var(--tc-mono) !important; color: var(--tc-ink-3) !important; }
    body.zen #zenJoin, body.zen #zenSound { font-family: var(--tc-mono) !important; border-radius: 0 !important; }

    #tcCreditToast {
      position: fixed; left: 50%; top: max(1.25rem, env(safe-area-inset-top)); z-index: 10000;
      transform: translate(-50%, -8px); opacity: 0; pointer-events: none;
      font-family: var(--tc-mono); font-size: 13px; background: var(--tc-ink); color: var(--tc-paper);
      padding: 8px 14px; transition: opacity 200ms ease, transform 200ms ease;
    }
    #tcCreditToast.tc-show { opacity: 1; transform: translate(-50%, 0); }

    /* ---------- pop-out: the window is the whole page ---------- */
    html.tc-popout body { background: var(--tc-paper) !important; overflow: hidden !important; }
    html.tc-popout #meshOsHud, html.tc-popout #meshOsDock, html.tc-popout #meshTopologyCanvas,
    html.tc-popout #multiplayerCursorsLayer, html.tc-popout #zenStage, html.tc-popout .zen-chrome,
    html.tc-popout #zenLauncher, html.tc-popout #zenDirtSurface { display: none !important; }
    html.tc-popout #desktopWorkspace { padding: 0 !important; min-height: 0 !important; }
    html.tc-popout .mesh-window:not(.hidden):not(.minimized) {
      position: fixed !important; inset: 0 !important; width: auto !important; max-width: none !important;
      height: 100dvh !important; border: 0 !important; border-radius: 0 !important; box-shadow: none !important; transform: none !important;
    }
    html.tc-popout .mesh-window .window-body { flex: 1 1 auto; min-height: 0; max-height: none !important; }
    html.tc-popout #win-terminal .tc-term-body, html.tc-popout #win-comms .tc-comms-body, html.tc-popout #win-agentspace .tc-space-body { height: auto !important; }
    html.tc-popout .mesh-window > .window-header { cursor: default; }
    html.tc-popout .mesh-window > .window-header .window-controls button:not(.tc-close) { display: none !important; }

    /* ---------- header meta: account · peers · chat, beside the clock ---------- */
    .mesh-window > .window-header .tc-kicker { display: flex; gap: 0; align-items: baseline; }
    .mesh-window > .window-header .tc-meta { display: inline-flex; align-items: baseline; }
    .mesh-window > .window-header .tc-meta button {
      border: 0 !important; background: none !important; padding: 0 !important; margin: 0 !important; cursor: pointer;
      font-size: 12px !important; color: var(--tc-ink-2) !important; text-decoration: underline; text-decoration-color: var(--tc-hair); text-underline-offset: 3px;
    }
    .mesh-window > .window-header .tc-meta button:hover { color: var(--tc-ink) !important; text-decoration-color: var(--tc-ink); }
    .mesh-window > .window-header .tc-meta > span::before { content: "·"; padding: 0 8px; color: var(--tc-ink-3); }

    /* ---------- window frame ---------- */
    .mesh-window, .mesh-window[data-zen-window="true"] {
      background: var(--tc-paper) !important;
      color: var(--tc-ink) !important;
      border: 1px solid var(--tc-ink) !important;
      border-radius: 18px !important;
      box-shadow: 0 30px 70px -40px rgba(17, 17, 17, 0.45) !important;
      backdrop-filter: none !important;
      font-family: var(--tc-mono) !important;
    }
    .mesh-window.window-focused { box-shadow: 0 34px 80px -36px rgba(17, 17, 17, 0.6) !important; }
    .mesh-window, .mesh-window * { font-family: var(--tc-mono) !important; letter-spacing: 0 !important; }

    /* ---------- header: clock, big title, path, controls ---------- */
    .mesh-window > .window-header {
      display: grid !important;
      grid-template-columns: 1fr auto;
      grid-template-rows: auto auto;
      align-items: end;
      gap: 0 1rem;
      padding: 14px 22px 12px !important;
      background: var(--tc-paper) !important;
      border-bottom: 1px solid var(--tc-ink) !important;
      color: var(--tc-ink) !important;
      cursor: grab;
    }
    .mesh-window > .window-header .tc-head-left { grid-column: 1; grid-row: 1 / span 2; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
    .mesh-window > .window-header .tc-kicker { font-size: 12px; color: var(--tc-ink-2) !important; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .mesh-window > .window-header .tc-title {
      font-family: var(--tc-sans) !important;
      font-weight: 400; font-size: clamp(26px, 3.2vw, 44px); line-height: 1.02;
      letter-spacing: -0.035em !important; color: var(--tc-ink) !important;
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .mesh-window > .window-header .tc-path {
      grid-column: 2; grid-row: 2; justify-self: end;
      font-size: 13px; color: var(--tc-ink-2) !important;
      padding-left: 14px; border-left: 1px solid var(--tc-ink); white-space: nowrap;
      max-width: 34ch; overflow: hidden; text-overflow: ellipsis;
    }
    .mesh-window > .window-header .window-controls { grid-column: 2; grid-row: 1; justify-self: end; align-self: start; display: flex !important; gap: 2px !important; }
    .mesh-window > .window-header .window-controls > :not(button) { display: none !important; }
    .mesh-window > .window-header .window-controls button {
      width: 30px; height: 26px; padding: 0 !important; display: inline-grid; place-items: center;
      background: transparent !important; border: 0 !important; border-radius: 0 !important;
      color: var(--tc-ink) !important; font-size: 15px !important; line-height: 1; cursor: pointer;
    }
    .mesh-window > .window-header .window-controls button:hover { background: var(--tc-ink) !important; color: var(--tc-paper) !important; }
    .mesh-window > .window-header .window-controls button:focus-visible { outline: 1px solid var(--tc-ink); outline-offset: 2px; }

    /* ---------- status bar ---------- */
    .mesh-window .tc-status {
      display: flex; align-items: center; gap: 12px; flex-shrink: 0;
      padding: 9px 22px; border-top: 1px solid var(--tc-ink);
      font-size: 12px; color: var(--tc-ink-2) !important; background: var(--tc-paper) !important;
      white-space: nowrap; overflow: hidden;
    }
    .mesh-window .tc-status .tc-sep { width: 1px; align-self: stretch; background: var(--tc-ink) !important; }
    .mesh-window .tc-status .tc-grow { flex: 1; }

    /* ---------- body: strip the paint, keep the structure ---------- */
    .mesh-window .window-body {
      background: var(--tc-paper) !important;
      color: var(--tc-ink) !important;
      font-size: 12px;
    }
    .mesh-window .window-body *:not(video):not(img):not(canvas):not(svg):not(svg *):not(iframe) {
      color: var(--tc-ink) !important;
      background-image: none !important;
      box-shadow: none !important;
      text-shadow: none !important;
      backdrop-filter: none !important;
    }
    .mesh-window .window-body [class*="bg-"]:not(button):not(a):not(video):not(.tc-keep) { background-color: transparent !important; }
    .mesh-window .window-body [class*="border"] { border-color: var(--tc-hair) !important; }
    .mesh-window .window-body [class*="rounded"] { border-radius: 0 !important; }
    .mesh-window .window-body [class*="text-slate-4"], .mesh-window .window-body [class*="text-slate-5"],
    .mesh-window .window-body [class*="text-slate-6"], .mesh-window .window-body [class*="text-gray-4"],
    .mesh-window .window-body [class*="text-gray-5"], .mesh-window .window-body [class*="text-neutral-5"],
    .mesh-window .window-body [class*="text-neutral-6"], .mesh-window .window-body .tc-dim,
    .mesh-window .tc-dim { color: var(--tc-ink-3) !important; }
    .mesh-window .window-body h1, .mesh-window .window-body h2, .mesh-window .window-body h3 {
      font-size: 11px !important; font-weight: 700 !important; text-transform: uppercase; letter-spacing: 0.08em !important;
    }
    .mesh-window .window-body h4 { font-size: 12px !important; font-weight: 700 !important; }
    .mesh-window .window-body b, .mesh-window .window-body strong, .mesh-window .window-body [class*="font-bold"] { font-weight: 700 !important; }
    .mesh-window .window-body [class*="text-2xl"], .mesh-window .window-body [class*="text-3xl"], .mesh-window .window-body [class*="text-xl"] {
      font-family: var(--tc-mono) !important; font-weight: 400 !important;
    }

    /* tiny status dots stay round and inked; progress fills are ink on a hairline track */
    .mesh-window .window-body span[class*="w-2"][class*="rounded-full"],
    .mesh-window .window-body span[class*="w-1.5"][class*="rounded-full"],
    .mesh-window .window-body span[class*="w-2.5"][class*="rounded-full"] { background-color: var(--tc-ink) !important; border-radius: 50% !important; }
    .mesh-window .window-body [class*="overflow-hidden"][class*="h-1"],
    .mesh-window .window-body [class*="overflow-hidden"][class*="h-2"],
    .mesh-window .window-body [class*="overflow-hidden"][class*="h-1.5"] { background-color: var(--tc-hair-2) !important; }
    .mesh-window .window-body div[style*="width"][class*="bg-"],
    .mesh-window .window-body div[style*="width"][class*="h-full"] { background-color: var(--tc-ink) !important; }

    /* media keeps its colour and a black stage */
    .mesh-window .window-body video { background: #000 !important; border-radius: 0 !important; }
    .mesh-window .window-body img, .mesh-window .window-body canvas { border-radius: 0 !important; }

    /* buttons: outlined, invert on hover; anything that used to be a loud fill is solid ink */
    .mesh-window .window-body button, .mesh-window .window-body .tc-btn, .mesh-window .window-body a[class*="px-"] {
      background: transparent !important; color: var(--tc-ink) !important;
      border: 1px solid var(--tc-ink) !important; border-radius: 0 !important;
      font-size: 11px !important; font-weight: 500 !important; text-decoration: none !important;
      cursor: pointer; transition: background-color 120ms ease, color 120ms ease;
    }
    .mesh-window .window-body .tc-solid, .mesh-window .window-body .tc-btn-solid,
    .mesh-window .window-body button[aria-pressed="true"], .mesh-window .window-body button[aria-selected="true"] {
      background: var(--tc-ink) !important; color: var(--tc-paper) !important;
    }
    .mesh-window .window-body button:hover:not(:disabled), .mesh-window .window-body .tc-btn:hover, .mesh-window .window-body a[class*="px-"]:hover {
      background: var(--tc-ink) !important; color: var(--tc-paper) !important;
    }
    .mesh-window .window-body .tc-solid *, .mesh-window .window-body .tc-btn-solid *, .mesh-window .window-body button:hover:not(:disabled) *,
    .mesh-window .window-body a[class*="px-"]:hover * { color: var(--tc-paper) !important; }
    .mesh-window .window-body .tc-solid:hover, .mesh-window .window-body .tc-btn-solid:hover { background: var(--tc-ink-2) !important; }
    .mesh-window .window-body button:disabled { opacity: 0.4; cursor: not-allowed; }
    .mesh-window .window-body button:focus-visible, .mesh-window .window-body a:focus-visible { outline: 1px solid var(--tc-ink); outline-offset: 2px; }
    .mesh-window .window-body button:active:not(:disabled) { transform: translateY(1px); }
    .mesh-window .window-body .tc-emoji-only { filter: grayscale(1); }

    /* fields: transparent, hairline, ink on focus */
    .mesh-window .window-body input:not([type="checkbox"]):not([type="radio"]):not([type="range"]),
    .mesh-window .window-body textarea, .mesh-window .window-body select {
      background: transparent !important; color: var(--tc-ink) !important;
      border: 1px solid var(--tc-hair) !important; border-radius: 0 !important; box-shadow: none !important;
      font-size: 12px !important;
    }
    .mesh-window .window-body input:focus, .mesh-window .window-body textarea:focus, .mesh-window .window-body select:focus {
      border-color: var(--tc-ink) !important; outline: none !important;
    }
    .mesh-window .window-body ::placeholder { color: var(--tc-ink-3) !important; opacity: 1; }
    .mesh-window .window-body input[type="checkbox"], .mesh-window .window-body input[type="radio"], .mesh-window .window-body input[type="range"] { accent-color: var(--tc-ink); }
    .mesh-window .window-body select option { background: var(--tc-paper); color: var(--tc-ink); }
    .mesh-window .window-body table { border-collapse: collapse; }
    .mesh-window .window-body th { text-transform: uppercase; font-weight: 700 !important; font-size: 11px; border-bottom: 1px solid var(--tc-ink) !important; }
    .mesh-window .window-body ::selection { background: var(--tc-ink); color: var(--tc-paper); }
    .mesh-window ::-webkit-scrollbar { width: 9px; height: 9px; }
    .mesh-window ::-webkit-scrollbar-thumb { background: var(--tc-hair); border: 2px solid var(--tc-paper); }
    .mesh-window ::-webkit-scrollbar-track { background: transparent; }

    /* ---------- shared pane primitives ---------- */
    .mesh-window .tc-pane-h {
      display: flex; align-items: center; justify-content: space-between; gap: 10px;
      padding: 10px 16px 9px; border-bottom: 1px solid var(--tc-ink);
      font-size: 12px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.06em !important;
    }
    .mesh-window .tc-pane-h .tc-dim { text-transform: none; letter-spacing: 0 !important; }
    .mesh-window .tc-pane-h-sub { border-top: 1px solid var(--tc-ink); }
    .mesh-window .tc-pane-actions { display: flex; gap: 4px; }
    .mesh-window .window-body .tc-pane-actions button, .mesh-window .window-body .tc-link {
      border: 0 !important; padding: 1px 6px !important; text-transform: lowercase; letter-spacing: 0 !important; font-size: 11px !important;
    }
    .mesh-window .window-body .tc-link { text-decoration: underline !important; text-underline-offset: 3px; text-transform: none; }
    .mesh-window .tc-btn { padding: 4px 9px; display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; }
    .mesh-window .tc-grow { flex: 1; }

    /* ---------- Terminal ---------- */
    #win-terminal .tc-term-body {
      display: grid !important; padding: 0 !important; overflow: hidden !important;
      grid-template-columns: minmax(0, 1.5fr) minmax(300px, 1fr);
      grid-template-rows: minmax(0, 1fr);
      height: min(560px, calc(100dvh - 210px)); max-height: none !important;
    }
    #win-terminal .tc-pane { display: flex; flex-direction: column; min-width: 0; min-height: 0; }
    #win-terminal .tc-pane-shell { border-right: 1px solid var(--tc-ink); }
    #win-terminal .tc-pane-install { overflow-y: auto; overflow-x: hidden; }
    #win-terminal .tc-term-out { flex: 1; overflow-y: auto; padding: 12px 16px 4px; font-size: 12.5px; line-height: 1.55; }
    #win-terminal .tc-block { position: relative; padding: 2px 0 8px; }
    #win-terminal .tc-block-cmd { display: flex; gap: 8px; align-items: baseline; }
    #win-terminal .tc-block-cmd .tc-prompt { font-weight: 700; }
    #win-terminal .tc-block-tools { margin-left: auto; display: none; gap: 2px; }
    #win-terminal .tc-block:hover .tc-block-tools { display: flex; }
    #win-terminal .tc-block-tools button { border: 0 !important; padding: 0 5px !important; font-size: 10.5px !important; color: var(--tc-ink-3) !important; }
    #win-terminal .tc-block-tools button:hover { color: var(--tc-paper) !important; }
    #win-terminal .tc-block-out { white-space: pre-wrap; word-break: break-word; padding-left: 0; }
    #win-terminal .tc-block-out .tc-err { text-decoration: underline wavy var(--tc-ink-3); text-underline-offset: 4px; }
    #win-terminal .tc-block-out .tc-ok { font-weight: 700; }
    #win-terminal .tc-block.tc-failed .tc-block-cmd::before { content: "×"; margin-right: -2px; font-weight: 700; }
    #win-terminal .tc-block-out a, #win-terminal .tc-block-out .tc-path-link {
      color: var(--tc-ink) !important; text-decoration: underline !important; text-decoration-color: var(--tc-hair) !important;
      text-underline-offset: 3px; cursor: pointer; background: none !important; border: 0 !important; padding: 0 !important; font: inherit !important;
    }
    #win-terminal .tc-block-out .tc-path-link:hover, #win-terminal .tc-block-out a:hover { text-decoration-color: var(--tc-ink) !important; }
    #win-terminal .tc-block-out .tc-chip { border: 1px solid var(--tc-ink) !important; padding: 1px 7px !important; margin: 2px 4px 2px 0; display: inline-block; font-size: 11px !important; }
    #win-terminal .tc-block-out .tc-chip:hover { background: var(--tc-ink) !important; color: var(--tc-paper) !important; }
    #win-terminal .tc-spin::after { content: "⠋"; display: inline-block; animation: tcSpin 0.8s steps(8) infinite; }
    @keyframes tcSpin { 0%{content:"⠋"} 12%{content:"⠙"} 25%{content:"⠹"} 37%{content:"⠸"} 50%{content:"⠼"} 62%{content:"⠴"} 75%{content:"⠦"} 87%{content:"⠧"} }
    #win-terminal .tc-term-line { display: flex; gap: 8px; align-items: center; padding: 6px 16px 12px; font-size: 12.5px; cursor: text; }
    #win-terminal .tc-term-line .tc-prompt { font-weight: 700; white-space: nowrap; }
    #win-terminal .tc-term-inputwrap { position: relative; flex: 1; min-width: 0; }
    #win-terminal #tcTermInput {
      width: 100%; border: 0 !important; padding: 0 !important; background: transparent !important;
      font-size: 12.5px !important; caret-color: var(--tc-ink); position: relative; z-index: 1;
    }
    #win-terminal .tc-ghost { position: absolute; left: 0; top: 0; white-space: pre; color: var(--tc-ink-3) !important; pointer-events: none; font-size: 12.5px; }
    #win-terminal .tc-install { padding: 12px 16px; display: grid; grid-template-columns: minmax(0, 1fr); gap: 8px; }
    #win-terminal .tc-install-row { min-width: 0; display: flex; gap: 8px; align-items: center; border: 1px solid var(--tc-ink); padding: 6px 6px 6px 10px; }
    #win-terminal .tc-code { flex: 1; min-width: 0; overflow-x: auto; white-space: nowrap; font-size: 11.5px; scrollbar-width: none; }
    #win-terminal .tc-install-actions { display: flex; flex-wrap: wrap; gap: 6px; }
    #win-terminal .tc-stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; padding: 12px 16px 6px; }
    #win-terminal .tc-stats > div { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
    #win-terminal .tc-k { font-size: 11px; text-transform: uppercase; color: var(--tc-ink-2) !important; }
    #win-terminal .tc-v { font-size: 22px; line-height: 1.15; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    #win-terminal .tc-spark { display: flex; align-items: flex-end; gap: 3px; height: 40px; margin: 6px 16px; padding: 8px 0; border-top: 1px solid var(--tc-ink); border-bottom: 1px solid var(--tc-ink); }
    #win-terminal .tc-spark i { display: block; flex: 1; background: var(--tc-ink) !important; min-height: 2px; max-width: 2px; }
    #win-terminal .tc-table { padding: 4px 16px 12px; font-size: 12px; display: grid; grid-template-columns: auto auto 1fr; gap: 3px 16px; }
    #win-terminal .tc-table .tc-th { text-transform: uppercase; font-size: 11px; padding-bottom: 3px; }

    /* ---------- Comms ---------- */
    #win-comms .tc-comms-body {
      display: grid !important; grid-template-columns: 210px minmax(0, 1fr); padding: 0 !important;
      height: min(560px, calc(100dvh - 210px)); max-height: none !important; overflow: hidden !important;
    }
    #win-comms .tc-comms-side { border-right: 1px solid var(--tc-ink); overflow-y: auto; display: flex; flex-direction: column; }
    #win-comms .tc-comms-side .tc-pane-h { padding: 10px 14px 8px; }
    #win-comms .tc-comms-side .tc-pane-h:not(:first-child) { border-top: 1px solid var(--tc-ink); }
    #win-comms .tc-chan-list { list-style: none; margin: 0; padding: 6px 0; }
    #win-comms .tc-chan-list button {
      width: 100%; display: flex; justify-content: space-between; gap: 8px; text-align: left;
      border: 0 !important; padding: 5px 14px !important; font-size: 12.5px !important; font-weight: 400 !important;
    }
    #win-comms .tc-chan-list button[aria-current="true"] { background: var(--tc-ink) !important; color: var(--tc-paper) !important; }
    #win-comms .tc-chan-list button[aria-current="true"] * { color: var(--tc-paper) !important; }
    #win-comms .tc-chan-list .tc-unread { font-weight: 700; }
    #win-comms .tc-online li { display: flex; gap: 8px; align-items: baseline; padding: 3px 14px; font-size: 12px; }
    #win-comms .tc-online li::before { content: "●"; font-size: 8px; }
    #win-comms .tc-online li.tc-empty::before { content: none; }
    #win-comms .tc-dm-new { display: flex; gap: 4px; padding: 2px 14px 10px; }
    #win-comms .tc-dm-new input { flex: 1; min-width: 0; padding: 4px 6px !important; font-size: 11.5px !important; }
    #win-comms .tc-dm-new button { padding: 0 9px !important; }
    #win-comms .tc-comms-main { display: flex; flex-direction: column; min-width: 0; min-height: 0; }
    #win-comms .tc-comms-main .tc-pane-h { text-transform: none; letter-spacing: 0 !important; }
    #win-comms #tcChanTitle { font-weight: 700; }
    #win-comms #tcChanTopic { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    #win-comms .tc-chatlog { flex: 1; overflow-y: auto; padding: 10px 0; font-size: 12.5px; line-height: 1.5; }
    #win-comms .tc-msg { display: grid; grid-template-columns: 46px 14ch minmax(0, 1fr); gap: 0 12px; padding: 2px 16px; }
    #win-comms .tc-msg:hover { background: var(--tc-paper-2) !important; }
    #win-comms .tc-msg time { color: var(--tc-ink-3) !important; font-size: 11.5px; padding-top: 1px; }
    #win-comms .tc-msg .tc-nick { text-align: right; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--tc-ink-2) !important; }
    #win-comms .tc-msg.tc-me .tc-nick { font-weight: 700; color: var(--tc-ink) !important; }
    #win-comms .tc-msg .tc-text { white-space: pre-wrap; word-break: break-word; border-left: 1px solid var(--tc-hair); padding-left: 12px; }
    #win-comms .tc-msg.tc-cont time, #win-comms .tc-msg.tc-cont .tc-nick { visibility: hidden; }
    #win-comms .tc-msg.tc-sys .tc-text { color: var(--tc-ink-3) !important; }
    #win-comms .tc-day { text-align: center; color: var(--tc-ink-3) !important; font-size: 11px; margin: 8px 16px; display: flex; gap: 10px; align-items: center; }
    #win-comms .tc-day::before, #win-comms .tc-day::after { content: ""; flex: 1; height: 1px; background: var(--tc-hair) !important; }
    #win-comms .tc-empty-log { padding: 24px 16px; color: var(--tc-ink-3) !important; }
    #win-comms .tc-chat-input { display: flex; gap: 10px; align-items: center; padding: 10px 16px; border-top: 1px solid var(--tc-ink); }
    #win-comms .tc-chat-input .tc-prompt { font-weight: 700; white-space: nowrap; }
    #win-comms .tc-chat-input input { flex: 1; min-width: 0; border: 0 !important; padding: 4px 0 !important; font-size: 12.5px !important; }

    @media (max-width: 760px) {
      #win-terminal .tc-term-body { grid-template-columns: 1fr; grid-template-rows: minmax(300px, 1fr) auto; overflow-y: auto !important; }
      #win-terminal .tc-pane-shell { border-right: 0; border-bottom: 1px solid var(--tc-ink); }
      #win-comms .tc-comms-body { grid-template-columns: 1fr; grid-template-rows: auto minmax(0, 1fr); }
      #win-comms .tc-comms-side { border-right: 0; border-bottom: 1px solid var(--tc-ink); max-height: 132px; }
      #win-comms .tc-msg { grid-template-columns: 40px 9ch minmax(0, 1fr); gap: 0 8px; padding: 2px 12px; }
      .mesh-window > .window-header .tc-path { display: none; }
    }
    @media (prefers-reduced-motion: reduce) { #win-terminal .tc-spin::after { animation: none; } }
  </style>
"""

THEME_BODY = r"""
  <script id="tcThemeScript">
  (function () {
    const $ = (id) => document.getElementById(id);
    const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    const store = {
      get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
      set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} },
    };
    const peer = () => (typeof myPeerId !== 'undefined' ? myPeerId : (localStorage.getItem('tincan_peer_id') || 'peer'));
    const handle = () => {
      try { const u = (localStorage.getItem('tincan_username') || '').trim(); if (u) return u.replace(/^@/, ''); } catch (e) {}
      return peer();
    };
    const hhmm = (d) => (d || new Date()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });

    // ---------------------------------------------------------------------------------
    // Window chrome: every header becomes clock + big title + path + controls,
    // every window gets a status bar, and decorative emoji leave the chrome.
    // ---------------------------------------------------------------------------------
    const WINDOWS = {
      'win-terminal': ['Terminal', '~/space'],
      'win-comms': ['Comms', '~/comms/#main'],
      'win-tv': ['Watch Party', '~/tv'],
      'win-board': ['Board', '~/board'],
      'win-agentspace': ['Space', '~/space'],
      'win-arena': ['Arena', '~/arena'],
      'win-network': ['Network', '~/network'],
      'win-quests': ['Quests', '~/quests'],
      'win-billing': ['Tokens', '~/tokens'],
      'win-call': ['Call', '~/call'],
      'win-moderator': ['Moderate', '~/admin'],
    };
    const EMOJI = /(?:\p{Extended_Pictographic}|\p{Regional_Indicator})(?:️|‍(?:\p{Extended_Pictographic}))*️?|️|⃣/gu;
    const CONTROL_GLYPH = [[/pop|↗/i, '↗'], [/^—|minim/i, '—'], [/□|⤢|max/i, '□'], [/✕|×|close/i, '×']];

    const POPOUT = document.documentElement.classList.contains('tc-popout');

    // account · peers · chat in every window header; in a pop-out they open other pop-outs
    function openOther(winId) {
      if (POPOUT && typeof openPopoutWindow === 'function') { openPopoutWindow(winId); return; }
      if (winId === 'win-comms' && typeof focusChatWindow === 'function') { focusChatWindow(); return; }
      const w = $(winId);
      if (!w) return;
      if ((w.style.display === 'none' || w.classList.contains('hidden')) && typeof toggleWindow === 'function') toggleWindow(winId);
      else if (typeof bringToFront === 'function') bringToFront(w);
    }
    function renderMeta() {
      let label = 'join';
      try { if (typeof isIdentityVerified === 'function' && isIdentityVerified()) label = '@' + handle(); } catch (e) {}
      document.querySelectorAll('.tc-meta-account').forEach((b) => { b.textContent = label; b.title = label === 'join' ? 'Create your TinCan identity' : 'Your account'; });
    }
    document.addEventListener('click', (e) => {
      const b = e.target.closest('[data-tc-meta]');
      if (!b) return;
      const what = b.dataset.tcMeta;
      if (what === 'account') { if (typeof openAccountModal === 'function') openAccountModal(false); }
      else if (what === 'peers') openOther('win-network');
      else if (what === 'chat') openOther('win-comms');
    });

    function setPath(winId, path) {
      const w = $(winId);
      const el = w && w.querySelector('.tc-path');
      if (el) el.textContent = path;
    }
    window.tcSetWindowPath = setPath;

    function normalizeHeader(w) {
      const head = w.querySelector(':scope > .window-header');
      if (!head || head.dataset.tc) return;
      head.dataset.tc = '1';
      const left = head.firstElementChild && !head.firstElementChild.classList.contains('window-controls') ? head.firstElementChild : null;
      const raw = left ? (left.querySelector('.window-title') || left).textContent : w.id;
      const preset = WINDOWS[w.id];
      const title = preset ? preset[0] : raw.replace(EMOJI, '').replace(/\.(app|exe)\b.*$/i, '').replace(/\s+/g, ' ').trim();
      const path = preset ? preset[1] : '~/' + title.toLowerCase().replace(/[^a-z0-9]+/g, '-');
      const box = document.createElement('div');
      box.className = 'tc-head-left';
      box.innerHTML = '<span class="tc-kicker"><span class="tc-clock"></span><span class="tc-meta">' +
        '<span><button type="button" data-tc-meta="account" class="tc-meta-account">join</button></span>' +
        (w.id === 'win-network' ? '' : '<span><button type="button" data-tc-meta="peers" class="tc-meta-peers">peers</button></span>') +
        (w.id === 'win-comms' ? '' : '<span><button type="button" data-tc-meta="chat">chat</button></span>') +
        '</span></span><span class="tc-title"></span>';
      box.querySelector('.tc-title').textContent = title;
      if (left) left.replaceWith(box); else head.prepend(box);
      const p = document.createElement('div');
      p.className = 'tc-path';
      p.textContent = path;
      head.appendChild(p);
      head.querySelectorAll('.window-controls button').forEach((b) => {
        const t = (b.textContent || '').trim() + ' ' + (b.title || '');
        for (const [re, g] of CONTROL_GLYPH) { if (re.test(t)) { b.textContent = g; if (!b.getAttribute('aria-label')) b.setAttribute('aria-label', b.title || g); break; } }
        // in a pop-out the only control is close, and it closes the pop-out itself
        if (b.textContent === '×' && POPOUT) { b.classList.add('tc-close'); b.removeAttribute('onclick'); b.addEventListener('click', () => window.close()); }
      });
    }

    function addStatusBar(w) {
      if (w.dataset.tcOwnStatus || w.querySelector(':scope > .tc-status')) return;
      const bar = document.createElement('div');
      bar.className = 'tc-status';
      const path = (WINDOWS[w.id] || [null, '~'])[1];
      bar.innerHTML = '<span>⎇ mesh</span><span class="tc-sep"></span><span class="tc-status-path"></span><span class="tc-grow"></span><span class="tc-status-peer"></span><span class="tc-sep"></span><span class="tc-status-relay">relay …</span><span class="tc-sep"></span><span>UTF-8</span>';
      bar.querySelector('.tc-status-path').textContent = path;
      bar.querySelector('.tc-status-peer').textContent = 'tc:' + peer();
      w.appendChild(bar);
    }

    // Emoji are dropped from chrome (buttons, headings, labels, tabs, badges) but kept in
    // what people write. Reaction buttons that are nothing but an emoji go grey instead.
    const CHROME_SEL = 'button, h1, h2, h3, h4, label, summary, th, .window-title, span[class*="uppercase"], span[class*="rounded"], span.text-base, span.text-lg, span.text-xl, span.text-2xl, option';
    const KEEP_SEL = '#chatMessagesList, .tc-chatlog, #tcTermOut, textarea, input, pre, code, [contenteditable="true"], .tc-user';
    function stripEmoji(root) {
      const nodes = root.matches && root.matches(CHROME_SEL) ? [root] : [];
      root.querySelectorAll && root.querySelectorAll(CHROME_SEL).forEach((n) => nodes.push(n));
      nodes.forEach((el) => {
        if (el.closest(KEEP_SEL) || el.dataset.tcEmoji) return;
        const txt = el.textContent || '';
        if (!EMOJI.test(txt)) return;
        EMOJI.lastIndex = 0;
        if (!txt.replace(EMOJI, '').trim()) {
          // icon-only: a lone decorative span disappears, an icon-only button keeps its glyph in grey
          if (el.tagName === 'BUTTON' || el.closest('button')) { el.classList.add('tc-emoji-only'); el.dataset.tcEmoji = '1'; }
          else if (el.tagName === 'SPAN' && !el.children.length) el.style.display = 'none';
          return;
        }
        el.dataset.tcEmoji = '1';
        const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
        const texts = [];
        while (walker.nextNode()) texts.push(walker.currentNode);
        texts.forEach((t) => {
          const v = t.nodeValue.replace(EMOJI, '');
          if (v !== t.nodeValue) t.nodeValue = v.replace(/^\s+/, (m) => (t.previousSibling ? ' ' : '')).replace(/\s{2,}/g, ' ');
        });
        el.querySelectorAll('span').forEach((s) => { if (!s.textContent.trim() && !s.children.length && !/\bw-|\bh-/.test(s.className)) s.style.display = 'none'; });
      });
    }

    // A button that used to carry a loud fill (bg-<hue>-500..700, a gradient, black) is a
    // primary action or the active tab: it renders as solid ink. Hover-only classes don't count.
    const LOUD = /^(bg-(?!slate|gray|zinc|neutral|stone|transparent|white)[a-z]+-[5-9]00(\/\d+)?|bg-black|bg-gradient-.+|from-.+)$/;
    function classifyButton(b) {
      if (!b.classList || b.closest('.window-header')) return;
      const loud = Array.from(b.classList).some((c) => LOUD.test(c));
      if (loud !== b.classList.contains('tc-solid')) b.classList.toggle('tc-solid', loud);
    }
    function classify(root) {
      if (root.tagName === 'BUTTON' || root.tagName === 'A') classifyButton(root);
      root.querySelectorAll && root.querySelectorAll('button, a[class*="px-"]').forEach(classifyButton);
    }

    function themeWindow(w) {
      normalizeHeader(w);
      addStatusBar(w);
      stripEmoji(w);
      classify(w);
    }

    function tickClocks() {
      const t = hhmm();
      document.querySelectorAll('.mesh-window .tc-clock').forEach((c) => { c.textContent = t; });
    }

    let pending = new Set();
    let scheduled = false;
    const observer = new MutationObserver((muts) => {
      muts.forEach((m) => {
        if (m.type === 'attributes') { if (m.target.tagName === 'BUTTON' || m.target.tagName === 'A') classifyButton(m.target); return; }
        m.addedNodes.forEach((n) => { if (n.nodeType === 1) pending.add(n); });
      });
      if (!scheduled && pending.size) {
        scheduled = true;
        requestAnimationFrame(() => {
          scheduled = false;
          const batch = pending; pending = new Set();
          batch.forEach((n) => { if (n.isConnected && n.closest('.mesh-window')) { stripEmoji(n); classify(n); } });
        });
      }
    });

    function relayStatus() {
      fetch('/api/status').then((r) => r.json()).then((d) => {
        const streams = (d.active_webrtc_streams || []).length;
        const label = d.status === 'online' ? `relay online · ${streams} stream${streams === 1 ? '' : 's'}` : 'relay offline';
        document.querySelectorAll('.tc-status-relay, #tcStatusRelay').forEach((e) => { e.textContent = label; });
        document.querySelectorAll('.tc-meta-peers').forEach((e) => { e.textContent = `${streams} peer${streams === 1 ? '' : 's'}`; });
        renderMeta();
        if (window.tcTerm) window.tcTerm.system(d);
      }).catch(() => {
        document.querySelectorAll('.tc-status-relay, #tcStatusRelay').forEach((e) => { e.textContent = 'relay unreachable'; });
      });
    }

    // ---------------------------------------------------------------------------------
    // tcTerm — the browser shell. Commands map to the relay's REST API and to the
    // visitor's Space VFS (scope=user, owner=peer id). Blocks, history, tab completion,
    // ghost suggestions, clickable paths, Ctrl+R / Ctrl+L / Ctrl+C / Ctrl+U.
    // ---------------------------------------------------------------------------------
    function makeTerminal() {
      const out = $('tcTermOut'), input = $('tcTermInput'), ghost = $('tcTermGhost'), promptEl = $('tcTermPrompt');
      if (!out || !input) return null;
      const origin = location.origin;
      const space = { scope: 'user', owner: peer() };
      let cwd = '/';
      let files = [];            // [{path, size_bytes, mime_type, updated_at}]
      let history = store.get('tc_term_history', []);
      let hIdx = history.length, draft = '';
      let tabCount = 0, lastTab = '';
      let search = null;         // { q, idx } during Ctrl+R
      let inflight = null;       // AbortController for the running command
      const sparkVals = [];

      // ---------- filesystem helpers ----------
      const norm = (p) => {
        const abs = p.startsWith('/') ? p : (cwd.replace(/\/$/, '') + '/' + p);
        const parts = [];
        abs.split('/').forEach((seg) => { if (!seg || seg === '.') return; if (seg === '..') parts.pop(); else parts.push(seg); });
        return '/' + parts.join('/');
      };
      const dirs = () => {
        const set = new Set(['/']);
        files.forEach((f) => { const segs = f.path.split('/').filter(Boolean); for (let i = 1; i < segs.length; i++) set.add('/' + segs.slice(0, i).join('/')); });
        return set;
      };
      const isDir = (p) => dirs().has(p);
      const isFile = (p) => files.some((f) => f.path === p);
      const children = (dir) => {
        const base = dir === '/' ? '/' : dir + '/';
        const names = new Map();
        files.forEach((f) => {
          if (!f.path.startsWith(base)) return;
          const rest = f.path.slice(base.length);
          const name = rest.split('/')[0];
          if (!name) return;
          const dirEntry = rest.includes('/');
          if (!names.has(name) || dirEntry) names.set(name, dirEntry ? { name, dir: true } : { name, dir: false, f });
        });
        return [...names.values()].sort((a, b) => (a.dir === b.dir ? a.name.localeCompare(b.name) : a.dir ? -1 : 1));
      };
      const tilde = (p) => '~/space' + (p === '/' ? '' : p);

      async function api(path, opts = {}) {
        const ctl = new AbortController();
        inflight = ctl;
        try {
          const r = await fetch(path, { ...opts, signal: ctl.signal, headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) } });
          let d = null;
          try { d = await r.json(); } catch (e) { d = {}; }
          if (!r.ok) throw new Error(d.error || ('HTTP ' + r.status));
          return d;
        } finally { if (inflight === ctl) inflight = null; }
      }
      const post = (path, body) => api(path, { method: 'POST', body: JSON.stringify(body) });

      async function loadFiles() {
        const d = await api(`/api/space/ls?scope=${space.scope}&owner_id=${encodeURIComponent(space.owner)}`);
        files = (d.files || []).slice().sort((a, b) => a.path.localeCompare(b.path));
        return files;
      }
      async function readFile(p) {
        const d = await api(`/api/space/file?scope=${space.scope}&owner_id=${encodeURIComponent(space.owner)}&path=${encodeURIComponent(p)}`);
        if (d.is_base64 || d.encoding === 'base64') return { binary: true, d };
        return { text: d.content != null ? d.content : (d.text != null ? d.text : ''), d };
      }
      const writeFile = (p, content) => post('/api/space/file', { scope: space.scope, owner_id: space.owner, path: p, content, updated_by: handle() });
      const deleteFile = (p) => post('/api/space/file', { scope: space.scope, owner_id: space.owner, path: p, action: 'delete', updated_by: handle() });

      // ---------- rendering ----------
      function setPrompt() {
        const p = `${handle()}@tincan:${tilde(cwd).replace('~/space', '~')}$`;
        promptEl.textContent = p;
        const sc = $('tcStatusCwd'); if (sc) sc.textContent = tilde(cwd);
        setPath('win-terminal', tilde(cwd));
      }
      const promptText = () => promptEl.textContent;

      function linkify(html) {
        // URLs open in a new tab; /paths that exist in the Space open in the editor.
        return html
          .replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>')
          .replace(/(^|[\s(])(\/[A-Za-z0-9_.\-/]+)/g, (m, pre, p) => (isFile(p) || isDir(p) ? `${pre}<button type="button" class="tc-path-link" data-tc-open="${esc(p)}">${esc(p)}</button>` : m));
      }

      function block(cmd) {
        const b = document.createElement('div');
        b.className = 'tc-block';
        b.innerHTML = '<div class="tc-block-cmd"><span class="tc-prompt"></span><span class="tc-cmdtext"></span><span class="tc-block-tools"><button type="button" data-a="copy">copy</button><button type="button" data-a="rerun">rerun</button></span></div><div class="tc-block-out"></div>';
        b.querySelector('.tc-prompt').textContent = promptText();
        b.querySelector('.tc-cmdtext').textContent = cmd;
        b.querySelector('[data-a="copy"]').addEventListener('click', () => copy(b.querySelector('.tc-block-out').innerText || cmd));
        b.querySelector('[data-a="rerun"]').addEventListener('click', () => run(cmd));
        out.appendChild(b);
        while (out.children.length > 400) out.firstElementChild.remove();
        const o = b.querySelector('.tc-block-out');
        return {
          el: b,
          text(t, cls) { const s = document.createElement('div'); if (cls) s.className = cls; s.innerHTML = linkify(esc(t)); o.appendChild(s); scroll(); return s; },
          html(h) { const s = document.createElement('div'); s.innerHTML = h; o.appendChild(s); scroll(); return s; },
          err(t) { b.classList.add('tc-failed'); this.text(t, 'tc-err'); },
          spin(label) { const s = this.html(`<span class="tc-dim">${esc(label || '')}</span> <span class="tc-spin"></span>`); return () => s.remove(); },
        };
      }
      function scroll() {
        if (out.scrollHeight - out.scrollTop - out.clientHeight < 120) out.scrollTop = out.scrollHeight;
      }
      function copy(text) {
        try { navigator.clipboard.writeText(text); } catch (e) {}
      }

      function treeText(dir) {
        const lines = [tilde(dir) + '/'];
        let nd = 0, nf = 0;
        const walk = (d, prefix) => {
          const kids = children(d).filter((k) => !k.name.startsWith('.'));
          kids.forEach((k, i) => {
            const last = i === kids.length - 1;
            lines.push(prefix + (last ? '└── ' : '├── ') + (d === '/' ? '' : d) + '/' + k.name + (k.dir ? '/' : ''));
            if (k.dir) { nd++; walk((d === '/' ? '' : d) + '/' + k.name, prefix + (last ? '    ' : '│   ')); } else nf++;
          });
        };
        walk(dir, '');
        lines.push('', `${nd} director${nd === 1 ? 'y' : 'ies'}, ${nf} file${nf === 1 ? '' : 's'}`);
        return lines.join('\n');
      }
      // Files are browsed and edited in the Space window; the shell hands paths over to it.
      function openInSpace(p, edit) {
        if (window.tcSpace) window.tcSpace.open(p, { edit });
      }

      // ---------- commands ----------
      const APPS = { comms: 'chat', chat: 'chat', tv: 'win-tv', watch: 'win-tv', board: 'win-board', space: 'win-agentspace', arena: 'win-arena', network: 'win-network', quests: 'win-quests', tokens: 'win-billing', billing: 'win-billing', call: 'win-call' };
      const CLI_ONLY = ['call', 'video', 'say', 'serve', 'start', 'screensaver', 'upgrade', 'mcp', 'trigger', 'dismiss', 'actions', 'add-contact', 'contacts', 'ping'];
      const C = {
        help: { args: '[command]', desc: 'list commands, or explain one' },
        install: { args: '[--mac]', desc: 'one-click install of the TinCan CLI and skills' },
        whoami: { desc: 'your peer id, handle and credit balance' },
        status: { desc: 'relay status, readiness tier and live streams' },
        peers: { desc: 'who is on the relay right now' },
        credits: { desc: 'AI credit balance (earn more by watching sponsored clips in the feed)' },
        ask: { args: '<prompt>', desc: 'ask the pooled AI models (spends credits)' },
        models: { desc: 'AI models available on this relay' },
        playlist: { args: '[add <url>]', desc: 'the watch party collection, or add a clip' },
        board: { args: '[search terms]', desc: 'latest board topics, or search them' },
        leaderboard: { desc: 'XP rankings on the mesh' },
        msg: { args: '<text>', desc: 'post to #main in Comms' },
        open: { args: '<app>', desc: 'open a window: comms tv board space arena network quests tokens call' },
        pwd: { desc: 'print the working directory in your Space' },
        ls: { args: '[path]', desc: 'list files in your Space' },
        cd: { args: '<dir>', desc: 'change directory' },
        tree: { args: '[path]', desc: 'print the file tree' },
        cat: { args: '<file>', desc: 'print a file' },
        edit: { args: '<file>', desc: 'open a file in Space to edit it (creates it if missing)' },
        touch: { args: '<file>', desc: 'create an empty file' },
        mkdir: { args: '<dir>', desc: 'create a directory' },
        rm: { args: '<file>', desc: 'delete a file' },
        echo: { args: '<text> [> file]', desc: 'print text, or write it to a file' },
        run: { args: '[file]', desc: 'run a file in the Space sandbox (python / js)' },
        agent: { args: '<prompt>', desc: 'let the Space agent edit your files' },
        history: { desc: 'commands you ran' },
        clear: { desc: 'clear the screen (Ctrl+L)' },
      };
      const words = (s) => (s.match(/"[^"]*"|'[^']*'|\S+/g) || []).map((w) => w.replace(/^["']|["']$/g, ''));
      function lev(a, b) {
        const m = Array.from({ length: a.length + 1 }, (_, i) => [i]);
        for (let j = 1; j <= b.length; j++) m[0][j] = j;
        for (let i = 1; i <= a.length; i++) for (let j = 1; j <= b.length; j++) m[i][j] = Math.min(m[i - 1][j] + 1, m[i][j - 1] + 1, m[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
        return m[a.length][b.length];
      }
      const chip = (cmd, label) => `<button type="button" class="tc-chip" data-tc-run="${esc(cmd)}">${esc(label || cmd)}</button>`;
      const pad = (s, n) => String(s).padEnd(n);

      async function exec(line, b) {
        let argv = words(line);
        if (argv[0] === 'tincan' || argv[0] === 'tc') argv = argv.slice(1);
        const cmd = (argv[0] || '').toLowerCase();
        const rest = line.replace(/^\s*(tincan|tc)\s+/, '').replace(/^\s*\S+\s*/, '');
        const a1 = argv[1];
        switch (cmd) {
          case '': return;
          case 'help': {
            if (a1 && C[a1]) { b.text(`${a1} ${C[a1].args || ''}\n  ${C[a1].desc}`); return; }
            b.text(Object.entries(C).map(([k, v]) => `${pad(k + ' ' + (v.args || ''), 26)}${v.desc}`).join('\n'));
            b.html('<span class="tc-dim">Every command also works as </span>tincan &lt;command&gt;<span class="tc-dim">. Tab completes, ↑ ↓ history, Ctrl+R search, Ctrl+L clear.</span>');
            return;
          }
          case 'clear': out.innerHTML = ''; return;
          case 'history': b.text(history.map((h, i) => `${String(i + 1).padStart(4)}  ${h}`).join('\n') || 'no history yet'); return;
          case 'install': {
            const curl = `curl -sSL ${origin}/install.sh | bash`;
            if (a1 === '--mac') { location.href = '/install.command'; b.text('Downloading Install-TinCan.command. Open it from Downloads to install.', 'tc-ok'); return; }
            b.text('1  Copy this into your own terminal (macOS or Linux):');
            b.html(`<div style="margin:4px 0 6px 3ch"><b>${esc(curl)}</b></div>`);
            b.text('2  Or on a Mac, download a double-clickable installer.\n3  Then try:  tincan whoami   tincan send   tincan call');
            b.html(chip('copy-install', 'copy curl command') + chip('install --mac', 'download .command') + `<button type="button" class="tc-chip" data-tc-copy-text="npx skills add NoJuanNobody/tincan-skills -g -y">copy npx skills</button>`);
            return;
          }
          case 'copy-install': copy(`curl -sSL ${origin}/install.sh | bash`); b.text('copied', 'tc-ok'); return;
          case 'whoami': {
            const id = peer();
            let acct = null;
            try { acct = (await api('/api/account/get?peer_id=' + encodeURIComponent(id))).account; } catch (e) {}
            b.text(`peer     ${id}\nhandle   ${handle()}\naccount  ${acct ? 'registered' : 'not registered (open any tool to join)'}${acct ? `\ncredits  ${Number(acct.token_balance || 0).toLocaleString()}` : ''}`);
            return;
          }
          case 'status': {
            const d = await api('/api/status');
            const s = d.active_webrtc_streams || [];
            b.text(`relay    ${d.status}\ntier     ${d.readiness_tier || '–'}\nscore    ${d.composite_score != null ? d.composite_score : '–'}\nstreams  ${s.length}`);
            system(d);
            return;
          }
          case 'peers': {
            const d = await api('/api/status');
            const s = d.active_webrtc_streams || [];
            if (!s.length) { b.text('nobody streaming right now'); return; }
            b.text(pad('PEER', 22) + pad('NAME', 26) + 'MODE\n' + s.map((p) => pad(p.peer_id || '?', 22) + pad(p.display_name || '', 26) + (p.has_screen ? 'screen' : p.has_video ? 'video' : 'voice')).join('\n'));
            return;
          }
          case 'credits': case 'balance': {
            let acct = null;
            try { acct = (await api('/api/account/get?peer_id=' + encodeURIComponent(peer()))).account; } catch (e) {}
            if (!acct) { b.text('No account yet. Open any tool to join, then watch sponsored clips in the feed to earn credits.'); return; }
            b.text(`${Number(acct.token_balance || 0).toLocaleString()} credits`, 'tc-ok');
            b.text('Sponsored clips in the feed credit you automatically when they play through.', 'tc-dim');
            return;
          }
          case 'ask': case 'chat': {
            if (!rest.trim()) { b.err('usage: ask <prompt>'); return; }
            const stop = b.spin('thinking');
            const d = await post('/api/chat', { peer_id: peer(), prompt: rest });
            stop();
            const msg = (d.choices && d.choices[0] && d.choices[0].message && d.choices[0].message.content) || d.reply || d.text || JSON.stringify(d);
            b.text(msg);
            if (d.model) b.text(`— ${d.model}`, 'tc-dim');
            return;
          }
          case 'models': {
            const d = await api('/api/models/available');
            const list = d.models || d.available || d.aliases || d;
            b.text(Array.isArray(list) ? list.map((m) => (typeof m === 'string' ? m : (m.alias || m.id || m.name) + (m.model ? '  ' + m.model : ''))).join('\n') : JSON.stringify(list, null, 2));
            return;
          }
          case 'playlist': {
            if (a1 === 'add') {
              const url = argv[2];
              if (!url) { b.err('usage: playlist add <url>'); return; }
              const stop = b.spin('adding');
              const d = await post('/api/playlist/add', { url, peer_id: peer() });
              stop();
              b.text(`added ${d.title || d.video_id || url}`, 'tc-ok');
              return;
            }
            const d = await api('/api/playlist');
            b.text((d.videos || []).map((v, i) => `${String(i + 1).padStart(2)}  ${pad((v.category || '').slice(0, 11), 12)}${v.title || v.video_id}  ${v.creator || ''}`).join('\n') || 'empty');
            b.html(chip('open tv', 'open watch party'));
            return;
          }
          case 'board': {
            const q = rest.trim();
            const d = q ? await api('/api/board/search?q=' + encodeURIComponent(q)) : await api('/api/board/topics');
            const topics = d.topics || d.results || d.items || [];
            if (!topics.length) { b.text(q ? 'no matches' : 'no topics yet'); b.html(chip('open board', 'open board')); return; }
            b.text(topics.slice(0, 15).map((t) => `${pad(t.score != null ? (t.score + '▲') : '', 6)}${(t.title || t.topic_title || '').slice(0, 64)}  ${t.author_username ? '@' + t.author_username : ''}`).join('\n'));
            b.html(chip('open board', 'open board'));
            return;
          }
          case 'leaderboard': {
            const d = await api('/api/mesh/leaderboard');
            const rows = d.leaderboard || [];
            b.text(rows.length ? rows.map((r, i) => `${String(i + 1).padStart(2)}  ${pad(r.display_name || r.peer_id, 28)}${r.xp} xp`).join('\n') : 'no rankings yet');
            if (d.tier) b.text(`you: ${d.tier.tier_name} · ${d.tier.xp} xp`, 'tc-dim');
            return;
          }
          case 'msg': {
            if (!rest.trim()) { b.err('usage: msg <text>'); return; }
            const inp = $('chatInput');
            if (window.tcComms) window.tcComms.select('main');
            if (inp) { inp.value = rest; if (typeof sendChatMessage === 'function') await sendChatMessage(); }
            b.text('sent to #main', 'tc-ok');
            return;
          }
          case 'open': {
            const target = APPS[(a1 || '').toLowerCase()];
            if (!target) { b.err('usage: open <' + Object.keys(APPS).join('|') + '>'); return; }
            if (target === 'chat') { if (typeof focusChatWindow === 'function') focusChatWindow(); }
            else if (typeof toggleWindow === 'function') { const w = $(target); if (w && (w.style.display === 'none' || w.classList.contains('hidden'))) toggleWindow(target); else if (w && typeof bringToFront === 'function') bringToFront(w); }
            b.text(`opened ${a1}`, 'tc-ok');
            return;
          }
          case 'pwd': b.text(tilde(cwd)); return;
          case 'ls': {
            await loadFiles();
            const p = norm(a1 || '.');
            if (isFile(p)) { const f = files.find((x) => x.path === p); b.text(`${f.size_bytes}  ${p}`); return; }
            if (!isDir(p)) { b.err(`ls: ${a1}: no such directory`); return; }
            const kids = children(p);
            b.html(kids.map((k) => { const full = (p === '/' ? '' : p) + '/' + k.name; return `<button type="button" class="tc-path-link" data-tc-open="${esc(full)}">${esc(k.dir ? k.name + '/' : k.name)}</button>`; }).join('   ') || '<span class="tc-dim">(empty)</span>');
            return;
          }
          case 'cd': {
            if (!files.length) await loadFiles();
            const p = norm(a1 || '/');
            if (!isDir(p)) { b.err(`cd: ${a1}: no such directory`); return; }
            cwd = p; setPrompt();
            return;
          }
          case 'tree': {
            await loadFiles();
            b.text(treeText(norm(a1 || '.')));
            return;
          }
          case 'cat': {
            if (!a1) { b.err('usage: cat <file>'); return; }
            const r = await readFile(norm(a1));
            if (r.binary) { b.text(`(binary ${r.d.mime_type || ''}, ${r.d.size_bytes || '?'} bytes)`, 'tc-dim'); return; }
            b.text(r.text || '(empty)');
            return;
          }
          case 'edit': case 'open-file': case 'vim': case 'nano': case 'code': {
            if (!a1) { b.err('usage: edit <file>'); return; }
            const p = norm(a1);
            if (!files.length) await loadFiles();
            openInSpace(p, true);
            b.text(`opened ${p} in Space  (⌘S save · ⌘↵ run · esc back to the file list)`, 'tc-dim');
            return;
          }
          case 'touch': {
            if (!a1) { b.err('usage: touch <file>'); return; }
            const p = norm(a1);
            if (!files.length) await loadFiles();
            if (!isFile(p)) await writeFile(p, '');
            await loadFiles();
            b.text(`created ${p}`, 'tc-ok');
            return;
          }
          case 'mkdir': {
            if (!a1) { b.err('usage: mkdir <dir>'); return; }
            const p = norm(a1);
            await writeFile(p + '/.keep', '');
            await loadFiles();
            b.text(`created ${p}/`, 'tc-ok');
            return;
          }
          case 'rm': {
            if (!a1) { b.err('usage: rm <file>'); return; }
            const p = norm(a1);
            if (!files.length) await loadFiles();
            if (!isFile(p)) { b.err(`rm: ${a1}: no such file`); return; }
            await deleteFile(p);
            await loadFiles();
            b.text(`removed ${p}`, 'tc-ok');
            return;
          }
          case 'echo': {
            const m = rest.match(/^(.*?)\s*(>>?)\s*(\S+)\s*$/);
            if (!m) { b.text(rest.replace(/^["']|["']$/g, '')); return; }
            const p = norm(m[3]);
            let content = m[1].replace(/^["']|["']$/g, '') + '\n';
            if (m[2] === '>>') { try { const r = await readFile(p); if (!r.binary) content = r.text + content; } catch (e) {} }
            await writeFile(p, content);
            await loadFiles();
            b.text(`wrote ${p}`, 'tc-ok');
            return;
          }
          case 'run': case 'python': case 'node': {
            const p = a1 ? norm(a1) : '/src/main.py';
            const stop = b.spin(`running ${p}`);
            const d = await post('/api/space/exec', { scope: space.scope, owner_id: space.owner, entrypoint: p, runtime: 'auto', args: argv.slice(2) });
            stop();
            if (d.stdout) b.text(d.stdout.replace(/\n$/, ''));
            if (d.stderr) b.err(d.stderr.replace(/\n$/, ''));
            b.text(`exit ${d.exit_code} · ${d.runtime || ''} · ${d.duration_ms != null ? Math.round(d.duration_ms) + ' ms' : ''}`, d.exit_code === 0 ? 'tc-dim' : 'tc-err');
            if (d.exit_code !== 0) b.el.classList.add('tc-failed');
            return;
          }
          case 'agent': {
            if (!rest.trim()) { b.err('usage: agent <what to change in your Space>'); return; }
            const stop = b.spin('agent working');
            const d = await post('/api/space/agent', { scope: space.scope, owner_id: space.owner, prompt: rest, author: handle() });
            stop();
            b.text(d.summary || d.reply || d.message || 'done', 'tc-ok');
            const changed = d.files_written || d.changed_files || d.written || [];
            if (changed.length) b.text('changed: ' + changed.map((f) => (typeof f === 'string' ? f : f.path)).join('  '));
            await loadFiles();
            return;
          }
        }
        if (CLI_ONLY.includes(cmd)) {
          b.text(`tincan ${cmd} runs on your own machine (camera, mic, local keys).`);
          b.html(chip('install', 'install the CLI'));
          return;
        }
        const names = Object.keys(C);
        const best = names.map((n) => [n, lev(cmd, n)]).sort((x, y) => x[1] - y[1])[0];
        b.err(`${cmd}: command not found`);
        if (best && best[1] <= 2) b.html(`did you mean ${chip(line.replace(cmd, best[0]), best[0])}`);
        else b.html(chip('help'));
      }

      async function run(line) {
        line = String(line || '').trim();
        if (!line) { block(''); return; }
        if (history[history.length - 1] !== line) { history.push(line); if (history.length > 500) history = history.slice(-500); store.set('tc_term_history', history); }
        hIdx = history.length; draft = '';
        if (line === 'clear') { out.innerHTML = ''; return; }
        const b = block(line);
        out.scrollTop = out.scrollHeight;
        try { await exec(line, b); }
        catch (e) { b.err(e.name === 'AbortError' ? '^C' : (e.message || String(e))); }
        out.scrollTop = out.scrollHeight;
      }

      // ---------- input: history, completion, ghost text, reverse search ----------
      function suggestion(v) {
        if (!v) return '';
        for (let i = history.length - 1; i >= 0; i--) if (history[i].startsWith(v) && history[i] !== v) return history[i];
        return '';
      }
      function paintGhost() {
        if (search) { ghost.textContent = ''; return; }
        const v = input.value, s = suggestion(v);
        ghost.textContent = s && input.selectionStart === v.length ? v + s.slice(v.length) : '';
        ghost.style.visibility = s ? 'visible' : 'hidden';
      }
      function completions(v) {
        const parts = v.split(/\s+/);
        if (parts.length <= 1) {
          const pre = parts[0] || '';
          return Object.keys(C).filter((k) => k.startsWith(pre)).map((k) => k + ' ');
        }
        if (parts[0] === 'open') {
          const pre = parts[parts.length - 1];
          return Object.keys(APPS).filter((k) => k.startsWith(pre)).map((k) => parts.slice(0, -1).join(' ') + ' ' + k);
        }
        const token = parts[parts.length - 1];
        const slash = token.lastIndexOf('/');
        const dirPart = slash >= 0 ? token.slice(0, slash + 1) : '';
        const namePre = slash >= 0 ? token.slice(slash + 1) : token;
        const dir = norm(dirPart || '.');
        const head = parts.slice(0, -1).join(' ') + ' ';
        return children(dir).filter((k) => k.name.startsWith(namePre)).map((k) => head + dirPart + k.name + (k.dir ? '/' : ''));
      }
      function commonPrefix(arr) {
        if (!arr.length) return '';
        let p = arr[0];
        arr.forEach((s) => { while (!s.startsWith(p)) p = p.slice(0, -1); });
        return p;
      }

      input.addEventListener('keydown', async (e) => {
        if (search) {
          if (e.key === 'Escape' || (e.ctrlKey && e.key.toLowerCase() === 'g')) { e.preventDefault(); search = null; input.value = draft; promptEl.textContent = promptText(); setPrompt(); return; }
          if (e.ctrlKey && e.key.toLowerCase() === 'r') { e.preventDefault(); search.idx--; doSearch(); return; }
          if (e.key === 'Enter') { e.preventDefault(); const v = input.dataset.match || ''; search = null; setPrompt(); input.value = ''; run(v); return; }
          setTimeout(() => { search.q = input.value; search.idx = history.length - 1; doSearch(); }, 0);
          return;
        }
        if (e.key !== 'Tab') tabCount = 0;
        if (e.key === 'Enter') { e.preventDefault(); const v = input.value; input.value = ''; paintGhost(); await run(v); return; }
        if (e.key === 'ArrowUp') { e.preventDefault(); if (hIdx === history.length) draft = input.value; if (hIdx > 0) { hIdx--; input.value = history[hIdx]; } paintGhost(); return; }
        if (e.key === 'ArrowDown') { e.preventDefault(); if (hIdx < history.length) { hIdx++; input.value = hIdx === history.length ? draft : history[hIdx]; } paintGhost(); return; }
        if ((e.key === 'ArrowRight' || e.key === 'End') && input.selectionStart === input.value.length) {
          const s = suggestion(input.value); if (s) { e.preventDefault(); input.value = s; paintGhost(); } return;
        }
        if (e.key === 'Tab') {
          e.preventDefault();
          if (!files.length) { try { await loadFiles(); } catch (err) {} }
          const v = input.value;
          const opts = completions(v);
          if (!opts.length) return;
          if (opts.length === 1) { input.value = opts[0]; tabCount = 0; paintGhost(); return; }
          const cp = commonPrefix(opts);
          if (cp.length > v.length) { input.value = cp; paintGhost(); return; }
          tabCount = lastTab === v ? tabCount + 1 : 1; lastTab = v;
          if (tabCount >= 2) { const b = block(v); b.text(opts.map((o) => o.trim().split(/\s+/).pop()).join('   ')); tabCount = 0; }
          return;
        }
        if (e.ctrlKey && !e.metaKey) {
          const k = e.key.toLowerCase();
          if (k === 'l') { e.preventDefault(); out.innerHTML = ''; return; }
          if (k === 'c') { e.preventDefault(); if (inflight) inflight.abort(); else { const b = block(input.value + '^C'); b.el.classList.add('tc-dim'); input.value = ''; paintGhost(); } return; }
          if (k === 'u') { e.preventDefault(); input.value = input.value.slice(input.selectionStart); input.setSelectionRange(0, 0); paintGhost(); return; }
          if (k === 'a') { e.preventDefault(); input.setSelectionRange(0, 0); return; }
          if (k === 'e') { e.preventDefault(); input.setSelectionRange(input.value.length, input.value.length); return; }
          if (k === 'w') { e.preventDefault(); const s = input.selectionStart; const before = input.value.slice(0, s).replace(/\S+\s*$/, ''); input.value = before + input.value.slice(s); input.setSelectionRange(before.length, before.length); paintGhost(); return; }
          if (k === 'r') { e.preventDefault(); draft = input.value; search = { q: '', idx: history.length - 1 }; input.value = ''; doSearch(); return; }
        }
      });
      input.addEventListener('input', paintGhost);
      input.addEventListener('click', paintGhost);
      function doSearch() {
        const q = search.q;
        let found = '';
        for (let i = Math.min(search.idx, history.length - 1); i >= 0; i--) { if (!q || history[i].includes(q)) { found = history[i]; search.idx = i; break; } }
        input.dataset.match = found;
        promptEl.textContent = `(reverse-i-search)'${q}': ${found}`;
      }

      // clicks: paths open in the editor / cd into dirs; chips run commands; copy buttons copy
      $('win-terminal').addEventListener('click', async (e) => {
        const openBtn = e.target.closest('[data-tc-open]');
        if (openBtn) {
          const p = openBtn.dataset.tcOpen;
          if (!files.length) await loadFiles();
          if (isDir(p)) { cwd = p; setPrompt(); run('ls'); }
          else openInSpace(p, false);
          return;
        }
        const runBtn = e.target.closest('[data-tc-run]');
        if (runBtn) { run(runBtn.dataset.tcRun); input.focus(); return; }
        const copyBtn = e.target.closest('[data-tc-copy]');
        if (copyBtn) {
          const src = $(copyBtn.dataset.tcCopy);
          if (src) { copy(src.textContent.trim()); const t = copyBtn.textContent; copyBtn.textContent = 'copied'; setTimeout(() => { copyBtn.textContent = t; }, 1200); }
          return;
        }
        const copyText = e.target.closest('[data-tc-copy-text]');
        if (copyText) { copy(copyText.dataset.tcCopyText); copyText.textContent = 'copied'; return; }
      });
      out.addEventListener('mouseup', () => { if (!String(window.getSelection())) input.focus(); });

      // ---------- live system pane ----------
      async function system(d) {
        const streams = (d && d.active_webrtc_streams) || [];
        const set = (id, v) => { const el = $(id); if (el) el.textContent = v; };
        set('tcSysPeers', String(streams.length));
        set('tcSysScore', d && d.composite_score != null ? String(d.composite_score) : '–');
        set('tcSysTier', d && d.readiness_tier ? d.readiness_tier.split(':')[0] : '–');
        sparkVals.push(streams.length + (d && d.composite_score ? d.composite_score / 25 : 0) + Math.random() * 0.6);
        while (sparkVals.length > 48) sparkVals.shift();
        const max = Math.max(1, ...sparkVals);
        const sp = $('tcSysSpark');
        if (sp) sp.innerHTML = sparkVals.map((v) => `<i style="height:${Math.max(6, (v / max) * 100).toFixed(0)}%"></i>`).join('');
        const tbl = $('tcSysPeerTable');
        if (tbl) {
          tbl.innerHTML = '<span class="tc-th">Peer</span><span class="tc-th">Mode</span><span class="tc-th">Name</span>' +
            (streams.length ? streams.slice(0, 6).map((p) => `<span>${esc((p.peer_id || '').slice(0, 14))}</span><span>${p.has_screen ? 'screen' : p.has_video ? 'video' : 'voice'}</span><span>${esc(p.display_name || '')}</span>`).join('')
              : '<span class="tc-dim">nobody</span><span></span><span></span>');
        }
        try {
          const a = await fetch('/api/account/get?peer_id=' + encodeURIComponent(peer()));
          const j = a.ok ? await a.json() : null;
          set('tcSysCredits', j && j.account ? Number(j.account.token_balance || 0).toLocaleString() : 'join');
        } catch (e) {}
      }

      // ---------- boot ----------
      document.querySelectorAll('#win-terminal .tc-code').forEach((c) => { c.textContent = c.textContent.replace('https://iot-federated-agent-memory-production.up.railway.app', origin); });
      setPrompt();
      const welcome = block('');
      welcome.el.querySelector('.tc-block-cmd').remove();
      welcome.text('TinCan shell. Type help to see what it can do.');
      welcome.text('Run tincan commands here. Files you make show up in Space, under ~/space.', 'tc-dim');
      welcome.html(chip('help') + chip('install') + chip('whoami') + chip('ls') + chip('ask what can tincan do?', 'ask …'));
      loadFiles().catch(() => {});
      return { run, system, focus: () => input.focus(), clear: () => { out.innerHTML = ''; } };
    }

    // ---------------------------------------------------------------------------------
    // tcComms — a chat room: channel list on the left, IRC-style log in the middle.
    // Room channels ride the room's signal with payload.channel; direct messages go to one
    // peer; #ai answers with the pooled models. History stays in this browser.
    // ---------------------------------------------------------------------------------
    function makeComms() {
      const list = $('chatMessagesList');
      if (!list || !$('tcChanList')) return null;
      const CHANNELS = [
        { id: 'main', topic: 'everyone in the room' },
        { id: 'ai', topic: 'ask the pooled AI models · spends credits' },
        { id: 'watch-party', topic: 'talk over what is playing' },
        { id: 'board', topic: 'chatter about board threads' },
        { id: 'help', topic: 'questions about TinCan' },
      ];
      let logs = store.get('tc_comms_logs', {});
      let dms = store.get('tc_comms_dms', []);
      let unread = {};
      let current = store.get('tc_comms_current', 'main');
      if (!CHANNELS.some((c) => c.id === current) && !current.startsWith('dm:')) current = 'main';
      let online = [];
      let saveT = null;
      const persist = () => { clearTimeout(saveT); saveT = setTimeout(() => { store.set('tc_comms_logs', logs); store.set('tc_comms_dms', dms); }, 250); };
      const label = (id) => (id.startsWith('dm:') ? '@' + id.slice(3) : '#' + id);

      function renderSide() {
        const chan = $('tcChanList'), dm = $('tcDmList');
        chan.innerHTML = CHANNELS.map((c) => `<li><button type="button" data-ch="${c.id}"${c.id === current ? ' aria-current="true"' : ''} class="${unread[c.id] ? 'tc-unread' : ''}"><span># ${c.id}</span><span>${unread[c.id] || ''}</span></button></li>`).join('');
        dm.innerHTML = dms.length ? dms.map((p) => { const id = 'dm:' + p; return `<li><button type="button" data-ch="${esc(id)}"${id === current ? ' aria-current="true"' : ''} class="${unread[id] ? 'tc-unread' : ''}"><span>@ ${esc(p.slice(0, 16))}</span><span>${unread[id] || ''}</span></button></li>`; }).join('')
          : '<li class="tc-dim" style="padding:4px 14px;font-size:11.5px">no direct chats</li>';
        const on = $('tcOnlineList');
        $('tcOnlineCount').textContent = String(online.length);
        on.innerHTML = online.length ? online.map((p) => `<li><button type="button" data-dm="${esc(p.peer_id)}" style="border:0;padding:0;font-size:12px;font-weight:400;text-align:left" title="Message ${esc(p.peer_id)}">${esc(p.display_name || p.peer_id)}</button></li>`).join('')
          : '<li class="tc-empty tc-dim">just you</li>';
      }

      function msgRow(m, prev) {
        const d = new Date(m.t || Date.now());
        const cont = prev && prev.nick === m.nick && (m.t - prev.t) < 5 * 60 * 1000 && !m.sys;
        const row = document.createElement('div');
        row.className = 'tc-msg' + (m.me ? ' tc-me' : '') + (cont ? ' tc-cont' : '') + (m.sys ? ' tc-sys' : '');
        row.innerHTML = `<time datetime="${d.toISOString()}">${hhmm(d)}</time><span class="tc-nick"></span><span class="tc-text"></span>`;
        row.querySelector('.tc-nick').textContent = m.sys ? '—' : m.nick;
        row.querySelector('.tc-text').textContent = m.text;
        return row;
      }

      function renderLog() {
        const msgs = logs[current] || [];
        list.innerHTML = '';
        if (!msgs.length) {
          const c = CHANNELS.find((x) => x.id === current);
          list.innerHTML = `<div class="tc-empty-log">${current === 'ai' ? 'Ask anything. Replies come from the pooled models and spend AI credits.' : current.startsWith('dm:') ? 'Direct messages go only to this peer.' : `This is the start of ${esc(label(current))}${c ? ' — ' + esc(c.topic) : ''}.`}</div>`;
        }
        let lastDay = '';
        msgs.forEach((m, i) => {
          const day = new Date(m.t).toDateString();
          if (day !== lastDay) { const s = document.createElement('div'); s.className = 'tc-day'; s.textContent = day === new Date().toDateString() ? 'today' : day; list.appendChild(s); lastDay = day; }
          list.appendChild(msgRow(m, msgs[i - 1]));
        });
        list.scrollTop = list.scrollHeight;
        const n = msgs.length;
        $('chatCounterBadge').textContent = `${n} message${n === 1 ? '' : 's'}`;
      }

      function select(id) {
        current = id;
        unread[id] = 0;
        store.set('tc_comms_current', id);
        const c = CHANNELS.find((x) => x.id === id);
        $('tcChanTitle').textContent = label(id);
        $('tcChanTopic').textContent = c ? c.topic : 'direct · only this peer sees it';
        $('tcChatPrompt').textContent = label(id) + ' ›';
        $('chatInput').placeholder = 'message ' + label(id);
        const sel = $('chatChannelSelect'); if (sel) sel.value = id.startsWith('dm:') ? 'direct' : 'room';
        setPath('win-comms', '~/comms/' + label(id));
        renderSide();
        renderLog();
      }

      function receive({ sender, text, isMe, timestamp, channel, fromPeer }) {
        const ch = channel || 'main';
        if (ch.startsWith('dm:') && !dms.includes(ch.slice(3))) dms.unshift(ch.slice(3));
        const m = { nick: isMe ? handle() : String(sender || fromPeer || 'peer').replace(/^.*\(@(.+)\)$/, '$1'), text: String(text), t: timestamp || Date.now(), me: !!isMe };
        (logs[ch] = logs[ch] || []).push(m);
        if (logs[ch].length > 300) logs[ch] = logs[ch].slice(-300);
        persist();
        if (ch === current) {
          const msgs = logs[ch];
          if (msgs.length === 1) renderLog();
          else { list.appendChild(msgRow(m, msgs[msgs.length - 2])); const near = list.scrollHeight - list.scrollTop - list.clientHeight < 160; if (near || isMe) list.scrollTop = list.scrollHeight; $('chatCounterBadge').textContent = `${msgs.length} messages`; }
        } else {
          unread[ch] = (unread[ch] || 0) + 1;
          renderSide();
        }
      }

      async function askAi(prompt) {
        const thinking = { nick: 'tincan-ai', text: '…', t: Date.now(), sys: true };
        (logs.ai = logs.ai || []).push(thinking);
        if (current === 'ai') renderLog();
        try {
          const history = (logs.ai || []).filter((m) => !m.sys).slice(-10).map((m) => ({ role: m.me ? 'user' : 'assistant', content: m.text }));
          const r = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ peer_id: peer(), messages: history.length ? history : [{ role: 'user', content: prompt }] }) });
          const d = await r.json();
          logs.ai = logs.ai.filter((m) => m !== thinking);
          const reply = r.ok ? ((d.choices && d.choices[0] && d.choices[0].message && d.choices[0].message.content) || d.reply || d.text || '(no reply)') : (d.error || 'The AI is unavailable right now.');
          logs.ai.push({ nick: 'tincan-ai', text: reply, t: Date.now(), me: false, sys: !r.ok });
        } catch (e) {
          logs.ai = logs.ai.filter((m) => m !== thinking);
          logs.ai.push({ nick: 'tincan-ai', text: 'The AI is unavailable right now.', t: Date.now(), sys: true });
        }
        persist();
        if (current === 'ai') renderLog(); else { unread.ai = (unread.ai || 0) + 1; renderSide(); }
      }

      function startDm(p) {
        p = String(p || '').trim();
        if (!p || p === peer()) return;
        if (!dms.includes(p)) dms.unshift(p);
        persist();
        select('dm:' + p);
        $('chatInput').focus();
      }

      $('win-comms').addEventListener('click', (e) => {
        const b = e.target.closest('[data-ch]');
        if (b) { select(b.dataset.ch); $('chatInput').focus(); return; }
        const d = e.target.closest('[data-dm]');
        if (d) startDm(d.dataset.dm);
      });
      $('tcDmNew').addEventListener('submit', (e) => { e.preventDefault(); const inp = $('chatDirectPeerInput'); startDm(inp.value); inp.value = ''; });
      $('chatInput').addEventListener('keydown', (e) => {
        if (!e.altKey) return;
        const all = CHANNELS.map((c) => c.id).concat(dms.map((p) => 'dm:' + p));
        const i = all.indexOf(current);
        if (e.key === 'ArrowDown') { e.preventDefault(); select(all[(i + 1) % all.length]); }
        if (e.key === 'ArrowUp') { e.preventDefault(); select(all[(i - 1 + all.length) % all.length]); }
      });

      select(current);
      return {
        receive, askAi, select, current: () => current,
        peers(ps) { online = (ps || []).filter((p) => p.peer_id !== peer()); renderSide(); },
      };
    }

    // The Watch Party player earns the same way as the feed: sponsored items credit on their own.
    function watchPartyCredits() {
      const vid = $('relayNativeVideo');
      if (!vid || !window.tcAdCredits) return;
      const line = document.createElement('div');
      line.id = 'tcTvCredits';
      line.className = 'tc-dim';
      line.style.cssText = 'font-size:11.5px;padding:2px 0 0';
      const title = $('nowPlayingTitle');
      if (title && title.parentElement) title.parentElement.appendChild(line);
      const tracker = window.tcAdCredits.track(vid, (st) => {
        const bits = [];
        if (st.earning !== null) bits.push(`sponsored · earning ${st.earning.toFixed(0)}%`);
        else if (st.today) bits.push(`+${st.today.toLocaleString()} credits today`);
        if (st.hint === 'register') bits.push('join the mesh to earn credits from ads');
        else if (st.hint === 'cap') bits.push('daily ad credits reached');
        line.textContent = bits.join(' · ');
      });
      let lastSrc = '';
      const sync = () => {
        const id = vid.getAttribute('data-vid') || vid.currentSrc || vid.src;
        if (!id || id === lastSrc) return;
        lastSrc = id;
        const list = typeof playlistVideos !== 'undefined' ? playlistVideos : [];
        const idx = typeof currentVideoIdx !== 'undefined' ? currentVideoIdx : 0;
        tracker.clip(list[idx] || null);
      };
      vid.addEventListener('loadedmetadata', sync);
      vid.addEventListener('play', sync);
    }

    function boot() {
      document.querySelectorAll('.mesh-window').forEach(themeWindow);
      window.tcComms = makeComms();
      window.tcTerm = makeTerminal();
      document.querySelectorAll('.mesh-window').forEach((w) => observer.observe(w, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] }));
      watchPartyCredits();
      tickClocks();
      setInterval(tickClocks, 15000);
      relayStatus();
      setInterval(() => { if (!document.hidden) relayStatus(); }, 20000);
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
    else boot();
  })();
  </script>
"""


def apply_terminal_theme(html: str) -> str:
    """Inject the terminal theme and engines into the Mesh OS HTML (idempotent)."""
    if 'id="tcTheme"' in html:
        return html
    head_end = html.find("</head>")
    if head_end == -1:
        return html
    html = html[:head_end] + THEME_HEAD + html[head_end:]
    body_end = html.rfind("</body>")
    if body_end == -1:
        return html
    return html[:body_end] + THEME_BODY + html[body_end:]
