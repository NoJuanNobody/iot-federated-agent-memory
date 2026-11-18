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
  <link rel="stylesheet" href="/assets/vendor/xterm/xterm.css">
  <script src="/assets/vendor/xterm/xterm.js"></script>
  <script src="/assets/vendor/xterm/addon-fit.js"></script>
  <style>
    /*TC_SHELL_CSS*/
    /*TC_COPILOT_CSS*/
    /*TC_TOKEN_VAULT_CSS*/
    /*TC_AI_HOME_CSS*/
    /* Ranger VFS: resizable split + read-only viewer */
    @media (min-width: 768px) {
      #rangerListPane { width: var(--ranger-list-w, 38%); min-width: 180px; }
    }
    .ranger-code { border-collapse: collapse; width: 100%; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 11px; line-height: 1.55; }
    .ranger-code td.ln { width: 1%; padding: 0 0.6rem 0 0.5rem; text-align: right; color: #475569; user-select: none; vertical-align: top; border-right: 1px solid #1e293b; white-space: nowrap; }
    .ranger-code td.lc { padding: 0 0.75rem; color: #e2e8f0; white-space: pre; }
    .ranger-code.wrap td.lc { white-space: pre-wrap; word-break: break-word; }
    .ranger-code tr:hover td { background: rgba(30, 41, 59, 0.5); }
    .tk-c { color: #64748b; font-style: italic; } .tk-s { color: #86efac; } .tk-n { color: #fbbf24; }
    .tk-w { color: #c4b5fd; } .tk-f { color: #67e8f9; } .tk-k { color: #93c5fd; } .tk-t { color: #f9a8d4; }
    .ranger-md { color: #cbd5e1; font-size: 12px; line-height: 1.6; }
    .ranger-md h1, .ranger-md h2, .ranger-md h3, .ranger-md h4 { color: #f1f5f9; font-weight: 700; margin: 0.9em 0 0.4em; }
    .ranger-md h1 { font-size: 1.35em; border-bottom: 1px solid #1e293b; padding-bottom: 0.2em; } .ranger-md h2 { font-size: 1.18em; } .ranger-md h3 { font-size: 1.05em; }
    .ranger-md p, .ranger-md ul, .ranger-md ol, .ranger-md blockquote, .ranger-md pre, .ranger-md table { margin: 0.5em 0; }
    .ranger-md ul { list-style: disc; padding-left: 1.4em; } .ranger-md ol { list-style: decimal; padding-left: 1.4em; }
    .ranger-md code { background: #0f172a; border: 1px solid #1e293b; border-radius: 4px; padding: 0 0.3em; font-size: 0.92em; color: #c4b5fd; }
    .ranger-md pre { background: #020617; border: 1px solid #1e293b; border-radius: 8px; padding: 0.6em 0.8em; overflow-x: auto; }
    .ranger-md pre code { background: none; border: 0; padding: 0; color: #e2e8f0; }
    .ranger-md blockquote { border-left: 3px solid #7c3aed; padding-left: 0.8em; color: #94a3b8; }
    .ranger-md hr { border: 0; border-top: 1px solid #1e293b; margin: 1em 0; }
    .ranger-md table { border-collapse: collapse; } .ranger-md th, .ranger-md td { border: 1px solid #1e293b; padding: 0.25em 0.6em; } .ranger-md th { background: #0f172a; color: #e2e8f0; }
    :root {
    --sumi: #0e0d0b;
    --sumi-2: #17150f;
    --sumi-card: #201d16;
    --sumi-well: #0a0907;
    --washi: #ece6da;
    --washi-quiet: rgba(236, 230, 218, 0.70);
    --washi-dim: rgba(236, 230, 218, 0.40);
    --line: rgba(236, 230, 218, 0.14);
    --kaki: #d0703f;
    --rust: #964622;
    --moss: #42522e;
    --indigo: #2e365c;
    --mincho: 'Shippori Mincho', serif;
    --gothic: 'Zen Kaku Gothic New', sans-serif;
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

    /* Spatial Draggable & Resizable Windows */
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
      min-width: 300px;
      min-height: 180px;
      max-width: calc(100vw - 12px);
      max-height: calc(100vh - 70px);
    }
    .mesh-window > .window-body {
      flex: 1 1 auto;
      min-height: 0;
    }
    .mesh-window[data-resized="true"] > .window-body,
    .mesh-window.maximized > .window-body,
    .mesh-window.popout-fullscreen > .window-body {
      height: auto !important;
      max-height: none !important;
      flex: 1 1 auto !important;
    }

    .window-resize-handle {
      position: absolute;
      bottom: 0;
      right: 0;
      width: 22px;
      height: 22px;
      cursor: nwse-resize;
      z-index: 52;
      display: flex;
      align-items: flex-end;
      justify-content: flex-end;
      padding: 4px;
      user-select: none;
      touch-action: none;
    }
    .window-resize-handle::after {
      content: "";
      width: 9px;
      height: 9px;
      border-right: 2px solid rgba(17, 17, 17, 0.45);
      border-bottom: 2px solid rgba(17, 17, 17, 0.45);
      border-bottom-right-radius: 2px;
    }
    .window-resize-handle:hover::after {
      border-color: #111111;
    }
    .window-resize-e {
      position: absolute;
      top: 44px;
      bottom: 18px;
      right: 0;
      width: 7px;
      cursor: ew-resize;
      z-index: 51;
      touch-action: none;
    }
    .window-resize-s {
      position: absolute;
      left: 16px;
      right: 18px;
      bottom: 0;
      height: 7px;
      cursor: ns-resize;
      z-index: 51;
      touch-action: none;
    }
    .window-resize-e:hover,
    .window-resize-s:hover {
      background: rgba(17, 17, 17, 0.12);
    }
    @media (max-width: 768px) {
      .mesh-window:not(.hidden) {
        left: 6px !important;
        right: 6px !important;
        width: calc(100vw - 12px) !important;
        max-width: calc(100vw - 12px) !important;
        max-height: calc(100vh - 78px) !important;
      }
      #meshOsDock {
        max-width: calc(100vw - 12px);
        overflow-x: auto;
        justify-content: flex-start;
        scrollbar-width: none;
      }
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
      position: fixed !important;
      top: 56px !important;
      left: 8px !important;
      right: 8px !important;
      bottom: 8px !important;
      width: calc(100vw - 16px) !important;
      height: calc(100vh - 64px) !important;
      min-height: calc(100vh - 64px) !important;
      max-height: calc(100vh - 64px) !important;
      z-index: 100 !important;
      border-radius: 12px !important;
      background: #020617 !important;
      box-shadow: 0 0 50px rgba(0, 0, 0, 0.9) !important;
    }

    .mesh-window.popout-fullscreen .window-body {
      max-height: calc(100vh - 110px) !important;
      height: calc(100vh - 110px) !important;
      overflow-y: auto !important;
    }

    .mesh-window.maximized .window-resize-handle,
    .mesh-window.maximized .window-resize-e,
    .mesh-window.maximized .window-resize-s,
    .mesh-window.popout-fullscreen .window-resize-handle,
    .mesh-window.popout-fullscreen .window-resize-e,
    .mesh-window.popout-fullscreen .window-resize-s {
      display: none !important;
    }

    .mesh-window.minimized {
      min-height: 0 !important;
      height: auto !important;
    }

    .mesh-window.minimized .window-body,
    .mesh-window.minimized .window-resize-handle,
    .mesh-window.minimized .window-resize-e,
    .mesh-window.minimized .window-resize-s {
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

    /* ==========================================================================
       Aeonik / Celadon & Ink Industrial Design System Styles
       ========================================================================== */
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Aeonik", "Inter", sans-serif !important;
      color: #111111 !important;
      background-color: #ecf1e6 !important;
    }

    .mesh-window[data-zen-window="true"],
    .mesh-window {
      background: #ecf1e6 !important;
      border: 1px solid #111111 !important;
      border-radius: 24px !important;
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.08), 0 0 0 1px #111111 !important;
      color: #111111 !important;
      overflow: hidden;
    }

    .mesh-window .window-header {
      background: #ecf1e6 !important;
      border-bottom: 1px solid #111111 !important;
      color: #111111 !important;
      font-family: -apple-system, BlinkMacSystemFont, "Aeonik", "Inter", sans-serif !important;
      font-weight: 600 !important;
      letter-spacing: -0.01em !important;
      padding: 12px 18px !important;
    }

    .mesh-window .window-header .window-title {
      font-family: -apple-system, BlinkMacSystemFont, "Aeonik", "Inter", sans-serif !important;
      color: #111111 !important;
      font-size: 1.15rem !important;
      letter-spacing: -0.02em !important;
    }

    .mesh-window .window-controls button {
      background: transparent !important;
      border: none !important;
      color: #111111 !important;
      font-size: 14px !important;
      font-weight: 500 !important;
      padding: 2px 6px !important;
      cursor: pointer;
    }

    .mesh-window .window-body {
      background: #ecf1e6 !important;
      color: #111111 !important;
      font-family: -apple-system, BlinkMacSystemFont, "Aeonik", "Inter", sans-serif !important;
    }

    .mesh-window .stat-card,
    .mesh-window .card,
    .mesh-window .panel-card,
    .mesh-window .stream-card,
    .mesh-window .quest-card {
      background: #f4f8f0 !important;
      border: 1px solid #111111 !important;
      border-radius: 16px !important;
      color: #111111 !important;
    }

    .mesh-window input,
    .mesh-window textarea,
    .mesh-window select {
      background: #ffffff !important;
      border: 1px solid #111111 !important;
      color: #111111 !important;
      font-family: "JetBrains Mono", monospace !important;
      border-radius: 8px !important;
    }

    .mesh-window input:focus,
    .mesh-window textarea:focus,
    .mesh-window select:focus {
      border-color: #000000 !important;
      outline: none !important;
      box-shadow: 0 0 0 1px #000000 !important;
    }

    .mesh-window button.btn-primary,
    .mesh-window .btn-action,
    .btn-kaki {
      background: #111111 !important;
      color: #ecf1e6 !important;
      border-radius: 9999px !important;
      border: none !important;
      font-weight: 600 !important;
    }

    .mesh-window button.btn-primary:hover,
    .mesh-window .btn-action:hover,
    .btn-kaki:hover {
      background: #333333 !important;
      color: #ffffff !important;
    }

    .mesh-window table th {
      border-bottom: 1px solid #111111 !important;
      color: #111111 !important;
      font-family: "JetBrains Mono", monospace !important;
      text-transform: uppercase;
      font-size: 0.75rem;
    }

    .mesh-window table td {
      border-bottom: 1px solid rgba(17, 17, 17, 0.12) !important;
      color: #111111 !important;
      font-family: "JetBrains Mono", monospace !important;
    }

    /* ==========================================================================
       Board unified search bar (Aeonik Celadon & Ink)
       ========================================================================== */
    .ubar-wrap { position: relative; font-family: "JetBrains Mono", ui-monospace, monospace; }
    .ubar-row { display: flex; gap: 0.5rem; align-items: stretch; }
    .ubar { flex: 1; min-width: 0; display: flex; align-items: center; flex-wrap: wrap; gap: 0.35rem; padding: 0.35rem 0.5rem 0.35rem 0.85rem;
            background: #ffffff; border: 1px solid #111111; border-radius: 9999px; cursor: text; }
    .ubar:focus-within { box-shadow: 0 0 0 1px #111111; }
    .ubar-icon { color: #111111; font-size: 14px; line-height: 1; }
    .ubar-chips { display: contents; }
    .ubar-chip { display: inline-flex; align-items: center; gap: 0.25rem; padding: 0.05rem 0.25rem 0.05rem 0.55rem; border: 1px solid #111111;
                 border-radius: 9999px; background: #ecf1e6; color: #111111; font-size: 11px; line-height: 1.5; }
    .ubar-chip[data-kind="filter"] { background: #111111; color: #ecf1e6; }
    .ubar-chip button { border: 0; background: transparent; color: inherit; cursor: pointer; font-size: 10px; padding: 0 0.2rem; border-radius: 9999px; }
    .ubar-chip button:hover, .ubar-chip button:focus-visible { background: rgba(17,17,17,0.12); outline: none; }
    .ubar input#boardSearchInput, .mesh-window .ubar input#boardSearchInput {
      flex: 1; min-width: 10rem; border: 0 !important; box-shadow: none !important; background: transparent !important; padding: 0.15rem 0 !important;
      font-size: 12px; color: #111111 !important; outline: none !important; }
    .ubar-kbd { font-size: 10px; color: #525252; border: 1px solid rgba(17,17,17,0.25); border-radius: 6px; padding: 0 0.35rem; }
    .ubar-sortwrap { display: inline-flex; align-items: center; gap: 0.3rem; margin-left: auto; padding-left: 0.6rem; border-left: 1px solid rgba(17,17,17,0.2); white-space: nowrap; }
    .ubar-sort-label { font-size: 10px; letter-spacing: 0.08em; text-transform: uppercase; color: #4a4a4a; }
    .mesh-window select.ubar-sort, select.ubar-sort { border: 0 !important; background: transparent !important; box-shadow: none !important; color: #111111; padding: 0.1rem 0.2rem; font-size: 11px; font-weight: 600; cursor: pointer; }
    .mesh-window select.ubar-sort:focus-visible { outline: 1px solid #111111; outline-offset: 2px; }
    .ubar-trend-empty { color: #4a4a4a; font-size: 11px; }
    .ubar-suggest { position: absolute; z-index: 60; left: 0; right: 0; top: 2.75rem; max-height: 320px; overflow-y: auto; padding: 0.35rem;
                    background: #f4f8f0; border: 1px solid #111111; border-radius: 16px; box-shadow: 0 16px 40px rgba(0,0,0,0.08); }
    .ubar-suggest.hidden { display: none; }
    .ubar-group-title { font-size: 10px; letter-spacing: 0.08em; text-transform: uppercase; color: #525252; padding: 0.4rem 0.6rem 0.2rem; }
    .ubar-option { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; padding: 0.3rem 0.6rem; border-radius: 10px;
                   font-size: 12px; color: #111111; cursor: pointer; }
    .ubar-option .ubar-opt-label { color: #525252; font-size: 11px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .ubar-option .ubar-opt-count { color: #525252; font-size: 10px; flex-shrink: 0; }
    .ubar-option[aria-selected="true"], .ubar-option:hover { background: #111111; color: #ecf1e6; }
    .ubar-option[aria-selected="true"] .ubar-opt-label, .ubar-option[aria-selected="true"] .ubar-opt-count,
    .ubar-option:hover .ubar-opt-label, .ubar-option:hover .ubar-opt-count { color: rgba(236,241,230,0.8); }
    .ubar-meta { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 0.5rem; font-size: 11px; color: #111111; }
    .ubar-trending { display: flex; flex-wrap: wrap; align-items: center; gap: 0.3rem; }
    .ubar-trending .ubar-trend-label { color: #525252; font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; margin-right: 0.2rem; }
    .ubar-trend { border: 1px solid #111111; border-radius: 9999px; padding: 0 0.5rem; background: transparent; color: #111111; font-size: 11px; cursor: pointer; }
    .ubar-trend:hover, .ubar-trend:focus-visible { background: #111111; color: #ecf1e6; outline: none; }
    .ubar-trend span { color: #525252; font-size: 10px; margin-left: 0.2rem; }
    .ubar-trend:hover span { color: rgba(236,241,230,0.8); }
    .ubar-rank summary, .ubar-rank-mini summary { cursor: pointer; color: #525252; font-size: 10px; text-decoration: underline; text-underline-offset: 2px; list-style: none; }
    .ubar-rank summary::-webkit-details-marker, .ubar-rank-mini summary::-webkit-details-marker { display: none; }
    .ubar-rank[open] { flex-basis: 100%; }
    .ubar-rank-body, .ubar-rank-mini-body { margin-top: 0.4rem; padding: 0.6rem 0.75rem; border: 1px solid #111111; border-radius: 16px; background: #f4f8f0;
                     font-size: 11px; color: #111111; }
    .ubar-rank-body table { width: 100%; border-collapse: collapse; margin-top: 0.35rem; }
    .ubar-rank-body th, .ubar-rank-body td { text-align: left; padding: 0.15rem 0.3rem; border-bottom: 1px solid rgba(17,17,17,0.12); font-size: 10px; }

    #accountSetupModal[data-zen-modal="true"],
    #accountSetupModal {
      backdrop-filter: blur(16px) !important;
    }

    #accountSetupModal .modal-content,
    #accountSetupModal .bg-slate-900 {
      background: var(--sumi-2) !important;
      border: 1px solid var(--line) !important;
      box-shadow: 0 24px 48px rgba(0, 0, 0, 0.7) !important;
      color: var(--washi) !important;
    }

    #accountSetupModal h2,
    #accountSetupModal h3 {
      font-family: var(--mincho) !important;
      color: var(--washi) !important;
    }

    /* ==========================================================================
       Aeonik Celadon & Ink: notification bar
       ========================================================================== */
    .aeonik-notice {
      position: fixed; top: 4.25rem; left: 50%; transform: translateX(-50%); z-index: 100;
      width: min(640px, calc(100% - 1.5rem));
      display: flex; align-items: center; justify-content: space-between; gap: 0.75rem;
      padding: 0.4rem 0.45rem 0.4rem 0.9rem;
      background: #ecf1e6; color: #111111;
      border: 1px solid #111111; border-radius: 9999px;
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.08);
      font-family: "JetBrains Mono", ui-monospace, monospace; font-size: 11px; line-height: 1.4;
    }
    .aeonik-notice.hidden { display: none; }
    .aeonik-notice__body { display: flex; align-items: center; gap: 0.55rem; min-width: 0; }
    .aeonik-notice__dot { width: 6px; height: 6px; border-radius: 9999px; background: #111111; flex-shrink: 0; }
    .aeonik-notice__label {
      flex-shrink: 0; padding: 0.05rem 0.55rem; border-radius: 9999px; border: 1px solid #111111;
      font-size: 10px; font-weight: 600; letter-spacing: 0.06em; background: #111111; color: #ecf1e6;
    }
    .aeonik-notice[data-variant="info"] .aeonik-notice__label { background: transparent; color: #111111; }
    .aeonik-notice[data-variant="info"] .aeonik-notice__dot { background: transparent; border: 1px solid #111111; }
    .aeonik-notice__text { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #111111; }
    .aeonik-notice__close {
      flex-shrink: 0; width: 1.6rem; height: 1.6rem; border-radius: 9999px; border: 1px solid #111111;
      background: transparent; color: #111111; font-size: 11px; line-height: 1; cursor: pointer; transition: background 0.15s, color 0.15s;
    }
    .aeonik-notice__close:hover, .aeonik-notice__close:focus-visible { background: #111111; color: #ecf1e6; outline: none; }

    /* ==========================================================================
       Aeonik Celadon & Ink scope for the rebuilt Ranger file panes and the arena
       model pickers: remaps the legacy slate/purple/cyan utilities to paper + ink.
       ========================================================================== */
    .aeonik-scope { color: #111111; }
    .aeonik-scope :is([class~="bg-slate-950"],[class~="bg-slate-900"],[class~="bg-slate-900/70"],[class~="bg-slate-900/90"]) { background: #f4f8f0 !important; }
    .aeonik-scope :is([class~="bg-slate-800"],[class~="bg-slate-700"]) { background: #ffffff !important; }
    .aeonik-scope :is([class~="hover:bg-slate-900"],[class~="hover:bg-slate-800"],[class~="hover:bg-slate-700"]):hover { background: rgba(17, 17, 17, 0.07) !important; }
    .aeonik-scope :is([class~="border-slate-800"],[class~="border-slate-700"],[class~="border-emerald-900/60"],[class~="border-cyan-900/60"],[class~="border-cyan-700/60"],[class~="border-purple-800"]) { border-color: #111111 !important; }
    .aeonik-scope :is([class~="divide-slate-800/40"]) > * + * { border-color: rgba(17, 17, 17, 0.12) !important; }
    .aeonik-scope :is([class~="text-slate-100"],[class~="text-slate-200"],[class~="text-slate-300"],[class~="text-purple-200"],[class~="text-purple-300"],[class~="text-purple-400"],[class~="text-cyan-300"],[class~="text-cyan-400"],[class~="text-emerald-300"],[class~="text-emerald-400"]) { color: #111111 !important; }
    .aeonik-scope :is([class~="text-slate-400"],[class~="text-slate-500"]) { color: #525252 !important; }
    .aeonik-scope :is([class~="text-slate-600"],[class~="text-slate-600/70"]) { color: #737373 !important; }
    .aeonik-scope :is([class~="hover:text-slate-200"],[class~="hover:text-slate-300"]):hover { color: #000000 !important; text-decoration: underline; }
    .aeonik-scope :is([class~="bg-purple-950"],[class~="bg-purple-950/80"]) { background: #111111 !important; color: #ecf1e6 !important; }
    .aeonik-scope :is([class~="bg-purple-950"],[class~="bg-purple-950/80"]) * { color: #ecf1e6 !important; }
    .aeonik-scope [class~="hover:bg-purple-900"]:hover { background: #333333 !important; }
    .aeonik-scope [class~="border-purple-400"] { border-color: #ecf1e6 !important; }
    .aeonik-scope [class~="bg-cyan-700/80"] { background: #111111 !important; color: #ecf1e6 !important; border-radius: 9999px; }
    .aeonik-scope button[class*="rounded"] { border-radius: 9999px; }
    .aeonik-scope [class~="rounded-xl"], .aeonik-scope [class~="rounded-lg"] { border-radius: 16px !important; }
    .aeonik-scope select { background: #ffffff !important; color: #111111 !important; border: 1px solid #111111 !important; border-radius: 8px !important; font-family: "JetBrains Mono", monospace !important; }
    .aeonik-scope #rangerSplitter > div { background: rgba(17, 17, 17, 0.25) !important; }
    .aeonik-scope #rangerSplitter:hover > div, .aeonik-scope #rangerSplitter:focus > div { background: #111111 !important; }
    .aeonik-scope #spaceFileList:focus { box-shadow: 0 0 0 1px #111111; border-radius: 8px; }
    .aeonik-scope .ring-purple-500\/70 { --tw-ring-color: #111111 !important; }
    .aeonik-scope .ranger-code td.ln { color: #737373; border-right-color: rgba(17, 17, 17, 0.15); }
    .aeonik-scope .ranger-code td.lc { color: #111111; }
    .aeonik-scope .ranger-code tr:hover td { background: rgba(17, 17, 17, 0.05); }
    .aeonik-scope .tk-c { color: #737373; } .aeonik-scope .tk-s { color: #2f6b3f; } .aeonik-scope .tk-n { color: #9a5b13; }
    .aeonik-scope .tk-w { color: #5b3b8c; } .aeonik-scope .tk-f { color: #1f5f73; } .aeonik-scope .tk-k { color: #111111; font-weight: 600; } .aeonik-scope .tk-t { color: #8c2f5e; }
    .aeonik-scope .ranger-md { color: #262626; }
    .aeonik-scope .ranger-md h1, .aeonik-scope .ranger-md h2, .aeonik-scope .ranger-md h3, .aeonik-scope .ranger-md h4 { color: #111111; }
    .aeonik-scope .ranger-md h1, .aeonik-scope .ranger-md hr { border-color: rgba(17, 17, 17, 0.15); }
    .aeonik-scope .ranger-md code { background: #ffffff; border-color: rgba(17, 17, 17, 0.2); color: #111111; }
    .aeonik-scope .ranger-md pre { background: #ffffff; border-color: #111111; }
    .aeonik-scope .ranger-md pre code { color: #111111; }
    .aeonik-scope .ranger-md blockquote { border-left-color: #111111; color: #525252; }
    .aeonik-scope .ranger-md th, .aeonik-scope .ranger-md td { border-color: rgba(17, 17, 17, 0.2); }
    .aeonik-scope .ranger-md th { background: #f4f8f0; color: #111111; }
    .aeonik-scope .ranger-md a { color: #111111 !important; }
    .aeonik-scope #finderImageContainer { background-image: none !important; }

    #zenDirtSurface {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      pointer-events: none;
      opacity: 0.035;
      z-index: 99999;
      mix-blend-mode: overlay;
    }
  </style>
</head>
<body class="theme-slate bg-slate-950 text-slate-100 min-h-screen overflow-x-hidden font-sans select-none">

  <!-- Zen Interior feTurbulence dirty-gradient noise layer -->
  <svg id="zenDirtSurface" aria-hidden="true">
    <filter id="zenDirt">
      <feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves="3" stitchTiles="stitch" />
      <feColorMatrix type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 0.25 0" />
    </filter>
    <rect width="100%" height="100%" filter="url(#zenDirt)" />
  </svg>

  <!-- Interactive Background Canvas: Peer Topology & Flying Packets -->
  <canvas id="meshTopologyCanvas" class="fixed inset-0 pointer-events-none z-0"></canvas>

  <!-- Multiplayer Peer Cursors Layer -->
  <div id="multiplayerCursorsLayer" class="fixed inset-0 pointer-events-none z-40 overflow-hidden"></div>

  <!-- Notification bar (admin broadcasts + quick notices). Aeonik Celadon & Ink: celadon paper, 1px ink hairline, pill shape, JetBrains Mono, ink-only accents. -->
  <div id="adminBroadcastBanner" role="status" aria-live="polite" data-variant="admin" class="aeonik-notice hidden">
    <div class="aeonik-notice__body">
      <span id="adminBroadcastAccent" class="aeonik-notice__dot" aria-hidden="true"></span>
      <span id="adminBroadcastLabel" class="aeonik-notice__label">ADMIN</span>
      <span id="adminBroadcastText" class="aeonik-notice__text"></span>
    </div>
    <button type="button" onclick="dismissAdminBanner()" aria-label="Dismiss" class="aeonik-notice__close">&#x2715;</button>
  </div>

  <!-- ===================================================================== -->
  <!-- Non-Negotiable Account Registration & Identity Gate Modal -->
  <!-- ===================================================================== -->
  <div id="accountSetupModal" data-zen-modal="true" class="hidden fixed inset-0 z-[9999] bg-slate-950/95 backdrop-blur-xl flex items-center justify-center p-4 pointer-events-auto select-none">
    <div class="bg-slate-900 border-2 border-emerald-500/80 rounded-2xl max-w-lg w-full shadow-[0_0_80px_rgba(16,185,129,0.35)] overflow-hidden p-6 space-y-4">
      <div class="flex items-center justify-between border-b border-slate-800 pb-3">
        <div class="flex items-center gap-3">
          <span class="text-3xl">🛡️</span>
          <div>
            <h3 class="text-sm font-bold text-white font-mono flex items-center gap-2">
              <span>Interactive Mesh Gate &amp; Operator Registry</span>
              <span class="px-2 py-0.5 rounded-full bg-cyan-950 border border-cyan-500 text-cyan-300 text-[9px] uppercase font-bold tracking-wider">Watching is Free</span>
            </h3>
            <p class="text-[11px] text-slate-400">Watching TV &amp; spectator feeds is 100% free! Registering your call-sign unlocks interactive chat, terminal CLI link, and agent sandboxes.</p>
          </div>
        </div>
        <button type="button" onclick="continueAsSpectator()" class="text-slate-400 hover:text-white text-lg px-1.5" title="Continue watching free as spectator">✕</button>
      </div>

      <!-- Starter Perks Banner -->
      <div class="p-3 bg-gradient-to-r from-emerald-950/60 to-cyan-950/60 border border-emerald-500/40 rounded-xl space-y-1.5 font-mono text-[11px]">
        <div class="text-emerald-300 font-bold flex items-center gap-1.5">
          <span>🎁</span> <span>Claim Verified Mesh Operator Credentials:</span>
        </div>
        <div class="flex justify-between text-slate-300 pl-4">
          <span>• Complimentary Tokens:</span>
          <span class="font-bold text-emerald-400">10 🪙 Starter Pack</span>
        </div>
        <div class="flex justify-between text-slate-300 pl-4">
          <span>• Sandbox API Credit:</span>
          <span class="font-bold text-cyan-400">$0.10 USD</span>
        </div>
        <div class="flex justify-between text-slate-300 pl-4">
          <span>• Hardware Node Peer ID:</span>
          <span id="modalPeerIdLabel" class="text-slate-400 truncate max-w-[160px]">...</span>
        </div>
      </div>

      <!-- Passwordless sign-in: passkey (Face ID / fingerprint) or one-time email code -->
      <div id="passkeySignInPanel" class="p-3 bg-slate-950 rounded-xl border border-cyan-500/40 space-y-2 font-mono text-[11px]">
        <div class="flex items-center justify-between gap-2">
          <span class="text-slate-300">Already have an account?</span>
          <button type="button" id="passkeySignInBtn" onclick="signInWithPasskey()" class="px-3 py-1.5 rounded-lg bg-cyan-700 hover:bg-cyan-600 text-white font-bold transition active:scale-95 flex items-center gap-1.5">
            <span>🔑</span> <span>Sign in with passkey</span>
          </button>
        </div>
        <button type="button" onclick="toggleRecoveryPanel(true)" class="text-cyan-300 hover:text-cyan-200 underline">No passkey yet? Get a one-time email code</button>
        <div id="passkeyRecoveryPanel" class="hidden space-y-2 pt-2 border-t border-slate-800">
          <p class="text-slate-400">We'll email a 6-digit code to the address on your account. It works once, for 10 minutes, and lets this device set up a passkey.</p>
          <div class="flex gap-2">
            <input id="recoveryEmailInput" type="email" autocomplete="email" placeholder="you@example.com" class="flex-1 px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white placeholder-slate-600 focus:border-cyan-500 focus:outline-none" />
            <button type="button" id="recoverySendBtn" onclick="requestRecoveryCode()" class="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-bold">Email code</button>
          </div>
          <div class="flex gap-2">
            <input id="recoveryCodeInput" type="text" inputmode="numeric" autocomplete="one-time-code" maxlength="6" placeholder="123456" class="flex-1 px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white placeholder-slate-600 tracking-widest focus:border-cyan-500 focus:outline-none" />
            <button type="button" id="recoveryVerifyBtn" onclick="verifyRecoveryCode()" class="px-3 py-2 rounded-lg bg-emerald-700 hover:bg-emerald-600 text-white font-bold">Verify &amp; add passkey</button>
          </div>
        </div>
        <div id="passkeyStatus" class="hidden p-2 rounded border"></div>
      </div>

      <!-- Registration Form -->
      <form id="accountSetupForm" onsubmit="handleAccountFormSubmit(event)" class="space-y-3 font-mono text-xs">
        <div>
          <label class="block text-slate-300 font-semibold mb-1">Full Legal / Real Name <span class="text-red-400">*</span></label>
          <input id="accInputFullName" type="text" required minlength="2" placeholder="e.g. Jane Doe" class="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white placeholder-slate-600 focus:border-emerald-500 focus:outline-none" />
        </div>

        <div>
          <label class="block text-slate-300 font-semibold mb-1">Username / Mesh Call-Sign <span class="text-red-400">*</span></label>
          <div class="relative">
            <span class="absolute left-3 top-2 text-slate-500">@</span>
            <input id="accInputUsername" type="text" required minlength="3" placeholder="handle_or_callsign" class="w-full pl-7 pr-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white placeholder-slate-600 focus:border-emerald-500 focus:outline-none" />
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="block text-slate-300 font-semibold mb-1">Contact Email <span class="text-red-400">*</span></label>
            <input id="accInputEmail" type="email" required placeholder="you@fau.edu or email" class="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white placeholder-slate-600 focus:border-emerald-500 focus:outline-none" />
          </div>
          <div>
            <label class="block text-slate-300 font-semibold mb-1">Phone Number (SMS/2FA) <span class="text-red-400">*</span></label>
            <input id="accInputPhone" type="tel" required minlength="10" placeholder="+1 561 555 0199" class="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white placeholder-slate-600 focus:border-emerald-500 focus:outline-none" />
          </div>
        </div>

        <div>
          <label class="block text-slate-300 font-semibold mb-1">Affiliation / Purpose</label>
          <select id="accInputRole" class="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none">
            <option value="FAU Graduate School / Academic">FAU Graduate School / Academic Research</option>
            <option value="AI Systems Engineer">AI Systems Engineer / Developer</option>
            <option value="Mesh Operator">Decentralized Mesh Operator</option>
            <option value="Security Auditor">Security Auditor / Observer</option>
          </select>
        </div>

        <!-- Non-Negotiable PII Consent Accordion/Box -->
        <div class="p-3 bg-slate-950 rounded-xl border border-amber-500/40 space-y-2">
          <label class="flex items-start gap-2.5 cursor-pointer text-slate-200">
            <input id="accInputConsentPii" type="checkbox" required class="mt-0.5 w-4 h-4 rounded bg-slate-900 border-amber-500 text-emerald-500 focus:ring-0 focus:outline-none shrink-0" />
            <span class="text-[11px] leading-relaxed">
              <strong class="text-amber-300">Mandatory PII &amp; Operator Consent:</strong> I explicitly consent to the collection, cryptographic attestation, and federated storage of my Name, Email, Phone Number, Node IP, and AI usage telemetry for operator moderation and billing auditing.
            </span>
          </label>
        </div>

        <div id="accFormError" class="hidden text-red-400 text-[11px] p-2 bg-red-950/40 border border-red-800 rounded"></div>

        <div class="pt-2">
          <button type="submit" id="accSubmitBtn" class="w-full py-2.5 bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 hover:brightness-110 text-white font-bold rounded-lg shadow-lg transition active:scale-95 flex items-center justify-center gap-1.5 text-xs">
            <span>🛡️</span> <span>Sign Identity &amp; Unlock TinCan Mesh OS</span>
          </button>
          <p class="text-[10px] text-center text-slate-400 mt-2">
            ⚠️ This step is mandatory. Desktop and agent windows remain locked until verified.
          </p>
        </div>
      </form>
    </div>
  </div>

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
          <span id="osAdminBadge" class="hidden text-[10px] font-mono ml-1.5 px-2 py-0.5 rounded-full bg-amber-950/90 text-amber-300 border border-amber-500 font-bold tracking-wider shadow-[0_0_10px_rgba(245,158,11,0.4)]">🛡️ ADMIN MOD</span>
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
      <!-- User Account & Token Chip -->
      <button id="hudAccountBtn" onclick="openAccountModal()" class="text-xs font-mono px-2.5 py-1 rounded border border-emerald-600/70 bg-emerald-950/80 text-emerald-300 hover:bg-emerald-900 transition flex items-center gap-1.5 active:scale-95 shadow-sm font-semibold" title="View or manage your mesh account & token billing balance">
        <span>👤</span> <span id="hudAccountName">Set Username</span> <span id="hudTokenPill" class="px-1.5 py-0.2 rounded-full bg-emerald-500 text-slate-950 text-[10px] font-bold">0 🪙</span>
      </button>

      <!-- Admin Mode Toggle & Mod Panel -->
      <button id="osAdminToggleBtn" onclick="toggleAdminMode()" class="text-xs font-mono px-2.5 py-1 rounded border border-slate-700 bg-slate-900 text-slate-300 hover:text-amber-400 hover:border-amber-600 transition flex items-center gap-1.5 active:scale-95 shadow-sm font-semibold">
        <span>🛡️</span> <span id="osAdminToggleText">Admin Mode</span>
      </button>
      <button id="osModPanelBtn" onclick="toggleWindow('win-moderator')" class="hidden text-xs font-mono px-2.5 py-1 rounded border border-amber-500 bg-amber-950 text-amber-300 hover:bg-amber-900 transition flex items-center gap-1.5 active:scale-95 shadow-sm font-bold">
        <span>🛡️</span> <span>Mod Panel</span>
      </button>

      <!-- Direct Live Chat Toggle -->
      <button onclick="focusChatWindow()" class="text-xs font-mono px-2.5 py-1 rounded border border-cyan-700 bg-cyan-950 text-cyan-300 hover:bg-cyan-900 transition flex items-center gap-1.5 active:scale-95 shadow-sm">
        <span>💬</span> <span class="font-bold">Chat</span> <span id="hudChatBadge" class="px-1.5 py-0.2 rounded-full bg-cyan-400 text-black text-[10px] font-bold">Live</span>
      </button>

      <!-- Active Peer & Network Pop-Out Launcher -->
      <button id="osPeerCount" onclick="toggleWindow('win-network')" class="text-xs font-mono px-2.5 py-1 rounded bg-emerald-950/90 border border-emerald-600/90 text-emerald-300 hover:bg-emerald-900 transition flex items-center gap-1.5 shadow-sm active:scale-95 cursor-pointer font-bold" title="Click to open Mesh Peers, Web Visitors & Leaderboard">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        <span>👥 <span id="osPeerCountNum">0</span> Active ↗</span>
      </button>

      <!-- Layout Tiling Mode Switcher -->
      <div class="hidden md:flex items-center bg-slate-900 border border-slate-700/80 rounded-lg p-0.5 font-mono text-[11px] shadow-sm">
        <button id="btnLayoutTile2x2" onclick="setDesktopLayout('tile2x2')" class="px-2 py-0.5 rounded text-slate-300 hover:text-white transition flex items-center gap-1" title="Tile 2x2 Grid (4 Quadrants)">
          <span>🪟</span> <span>2x2 Grid</span>
        </button>
        <button id="btnLayoutSplit" onclick="setDesktopLayout('split2col')" class="px-2 py-0.5 rounded text-slate-400 hover:text-white transition flex items-center gap-1" title="Split 2-Column Side-by-Side">
          <span>📑</span> <span>Split</span>
        </button>
        <button id="btnLayoutFree" onclick="setDesktopLayout('free')" class="px-2 py-0.5 rounded text-slate-400 hover:text-white transition flex items-center gap-1" title="Free Draggable Mode">
          <span>🗔</span> <span>Free</span>
        </button>
      </div>

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

      <!-- Pop Out Mode Guide -->
      <button onclick="togglePopoutGuide()" class="text-xs font-mono px-2 py-1 rounded border border-slate-700 bg-slate-900 text-slate-300 hover:bg-slate-800 transition">
        ↗ Pop Out Guide
      </button>

      <!-- One-Click Install Menu Launcher -->
      <button id="hudQuickInstallBtn" onclick="openTerminalQuickStart()" class="text-xs font-mono px-2.5 py-1 rounded border border-cyan-500/70 bg-cyan-950/80 text-cyan-300 hover:bg-cyan-900 transition flex items-center gap-1.5 active:scale-95 shadow-sm font-semibold" title="One-Click Install: CLI &amp; Agent Skills instructions">
        <span>📦</span> <span>One-Click Install</span>
      </button>
    </div>
  </header>

  <!-- ===================================================================== -->
  <!-- One-Click Install Instructions Modal (Menu) -->
  <!-- ===================================================================== -->
  <div id="terminalQuickStartModal" class="hidden fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="bg-[#ecf1e6] text-[#111111] border border-black rounded-2xl w-[680px] max-w-full overflow-hidden shadow-2xl space-y-4 p-6 font-mono text-xs">
      <div class="flex items-center justify-between border-b border-black pb-3">
        <div class="flex items-center gap-2">
          <span class="text-xl">📦</span>
          <div>
            <h2 class="text-sm font-bold text-black uppercase tracking-wider">One-Click Installer &amp; Quick Start CLI</h2>
            <p class="text-[11px] text-neutral-600">Install the TinCan 2.2 CLI, Agent Skills, and link your workstation in 10 seconds.</p>
          </div>
        </div>
        <button onclick="closeTerminalQuickStart()" class="text-neutral-600 hover:text-black text-base font-bold">✕</button>
      </div>

      <!-- Interactive One-Click Install Card (in Menu Modal, or ask Chat Agent) -->
      <!--TC_INSTALL_CARD {"id": "menu", "compact": false, "shell": "#termShellMount"}-->

      <!-- Step 1: Additional Manual Installer Options -->
      <div class="space-y-1.5">
        <div class="text-[11px] font-bold text-black flex items-center justify-between">
          <span>1. One-Line Terminal Installer (Homebrew or curl | bash)</span>
          <a href="/install.command" download="Install-TinCan.command" class="px-2.5 py-0.5 bg-black text-[#ecf1e6] rounded-full text-[10px] hover:opacity-80 transition">⬇ Download .command Launcher</a>
        </div>
        <div class="relative bg-white border border-black rounded-xl p-2.5 flex items-center justify-between gap-2">
          <code class="text-black font-semibold text-xs overflow-x-auto select-all">brew install https://iot-federated-agent-memory-production.up.railway.app/Formula/tincan.rb</code>
          <div class="flex items-center gap-1.5 shrink-0">
            <button onclick="copyToClipboard('brew install https://iot-federated-agent-memory-production.up.railway.app/Formula/tincan.rb', this)" class="px-3 py-1 bg-black hover:bg-neutral-800 text-[#ecf1e6] rounded-full text-[11px] font-bold active:scale-95 transition">
              🍺 Copy brew
            </button>
            <button onclick="closeTerminalQuickStart(); switchInstallCmdTab('brew'); execAeonikShellCommand('brew install tincan context-palace');" class="px-3 py-1 border border-black hover:bg-black hover:text-[#ecf1e6] text-black rounded-full text-[11px] font-bold active:scale-95 transition">
              ▶ Run brew
            </button>
          </div>
        </div>
        <div class="relative bg-white border border-black rounded-xl p-2.5 flex items-center justify-between gap-2">
          <code class="text-black font-semibold text-xs overflow-x-auto select-all">curl -sSL https://iot-federated-agent-memory-production.up.railway.app/install.sh | bash</code>
          <div class="flex items-center gap-1.5 shrink-0">
            <button onclick="copyToClipboard('curl -sSL https://iot-federated-agent-memory-production.up.railway.app/install.sh | bash', this)" class="px-3 py-1 bg-black hover:bg-neutral-800 text-[#ecf1e6] rounded-full text-[11px] font-bold active:scale-95 transition">
              📋 Copy
            </button>
            <button onclick="closeTerminalQuickStart(); simulateOneClickInstall();" title="Copies the installer command for your computer's terminal" class="px-3 py-1 border border-black hover:bg-black hover:text-[#ecf1e6] text-black rounded-full text-[11px] font-bold active:scale-95 transition">
              ▶ Run in Terminal
            </button>
          </div>
        </div>
      </div>

      <!-- Step 2: Check Identity -->
      <div class="space-y-1.5">
        <div class="text-[11px] font-bold text-black flex items-center gap-1.5">
          <span>2. Verify Cryptographic Peer Identity (Zero Accounts)</span>
        </div>
        <div class="relative bg-white border border-black rounded-xl p-2.5 flex items-center justify-between">
          <code class="text-black text-xs select-all">tincan whoami</code>
          <button onclick="copyToClipboard('tincan whoami', this)" class="ml-2 px-3 py-1 bg-black hover:bg-neutral-800 text-[#ecf1e6] rounded-full text-[11px] font-bold shrink-0 active:scale-95 transition">
            📋 Copy
          </button>
        </div>
      </div>

      <!-- Step 3: Connect -->
      <div class="space-y-1.5">
        <div class="text-[11px] font-bold text-black flex items-center gap-1.5">
          <span>3. Connect Workstation &amp; Live Telemetry</span>
        </div>
        <div class="relative bg-white border border-black rounded-xl p-2.5 flex items-center justify-between">
          <code class="text-black text-xs select-all">tincan connect --relay https://iot-federated-agent-memory-production.up.railway.app</code>
          <button onclick="copyToClipboard('tincan connect --relay https://iot-federated-agent-memory-production.up.railway.app', this)" class="ml-2 px-3 py-1 bg-black hover:bg-neutral-800 text-[#ecf1e6] rounded-full text-[11px] font-bold shrink-0 active:scale-95 transition">
            📋 Copy
          </button>
        </div>
      </div>

      <div class="flex justify-between items-center pt-3 border-t border-black">
        <span class="text-[10px] text-neutral-600">Watching the TV stream is always free. No account required.</span>
        <button onclick="closeTerminalQuickStart()" class="px-4 py-1.5 bg-black hover:bg-neutral-800 text-[#ecf1e6] font-bold rounded-full text-xs transition active:scale-95">
          Enter Mesh OS 🚀
        </button>
      </div>
    </div>
  </div>

  <!-- Desktop Spatial Workspace (Houses Draggable .mesh-window Containers) -->
  <main id="desktopWorkspace" class="relative w-full min-h-screen pt-16 pb-24 px-3 sm:px-6 z-10 select-text">

    <!-- ===================================================================== -->
    <!-- ===================================================================== -->
    <!-- Window 1: Terminal & Quickstart.exe (Aeonik Celadon Industrial Layout) -->
    <!-- ===================================================================== -->
    <div id="win-terminal" class="mesh-window w-[960px] max-w-[96vw]" data-zen-window="true" data-window-id="win-terminal" style="top: 60px; left: 32px; z-index: 20;">
      <!--TC_TITLEBAR {"id": "win-terminal", "title": "Terminal", "meta_html": "<span id=\"aeonikHeaderClock\">--:--</span> <span id=\"aeonikHeaderCwd\" class=\"hidden sm:inline\">~/space</span>", "extra_controls_html": "<a href=\"/fono\" target=\"_blank\" class=\"tc-ctl\" title=\"Open the Fono mobile controller\">Fono</a>"}-->
      <!-- The terminal is just the terminal: install card top-left, the shell/TUI below taking the rest. Files live in Space. -->
      <div class="window-body tc-term-body p-0 font-mono text-xs border-b border-black bg-[#ecf1e6]" style="display: flex; flex-direction: column; height: min(680px, calc(100vh - 120px)); overflow: hidden;">
        <div class="tc-term-top px-3 py-2 flex flex-wrap items-center justify-between gap-2 border-b border-black/20" style="flex: 0 0 auto;">
          <div id="termHarnessBar" class="flex flex-wrap items-center gap-1 text-[10px]">
            <span class="font-bold uppercase tracking-wider text-neutral-800 mr-1">Harnesses:</span>
            <button type="button" onclick="if(typeof execAeonikShellCommand==='function')execAeonikShellCommand('harness best');else if(window.TinCanShell)window.TinCanShell.run('harness best')" class="px-2 py-0.5 rounded-full bg-[#111111] text-[#ecf1e6] font-bold hover:opacity-85" title="Inspect best available coding harness">Auto Best</button>
            <button type="button" onclick="if(typeof execAeonikShellCommand==='function')execAeonikShellCommand('harness inspect antigravity');else if(window.TinCanShell)window.TinCanShell.run('harness inspect antigravity')" class="px-2 py-0.5 rounded-full border border-[#111111] bg-white hover:bg-[#111111] hover:text-[#ecf1e6] transition">Antigravity (agy)</button>
            <button type="button" onclick="if(typeof execAeonikShellCommand==='function')execAeonikShellCommand('harness inspect claude-code');else if(window.TinCanShell)window.TinCanShell.run('harness inspect claude-code')" class="px-2 py-0.5 rounded-full border border-[#111111] bg-white hover:bg-[#111111] hover:text-[#ecf1e6] transition">Claude Code</button>
            <button type="button" onclick="if(typeof execAeonikShellCommand==='function')execAeonikShellCommand('harness inspect opencode');else if(window.TinCanShell)window.TinCanShell.run('harness inspect opencode')" class="px-2 py-0.5 rounded-full border border-[#111111] bg-white hover:bg-[#111111] hover:text-[#ecf1e6] transition">OpenCode</button>
            <button type="button" onclick="if(typeof execAeonikShellCommand==='function')execAeonikShellCommand('harness inspect dsx');else if(window.TinCanShell)window.TinCanShell.run('harness inspect dsx')" class="px-2 py-0.5 rounded-full border border-[#111111] bg-[#f4f8f0] hover:bg-[#111111] hover:text-[#ecf1e6] transition" title="Fallback harness: github.com/NoJuanNobody/dsx">DSX (Fallback)</button>
            <button type="button" onclick="if(typeof execAeonikShellCommand==='function')execAeonikShellCommand('harnesses');else if(window.TinCanShell)window.TinCanShell.run('harnesses')" class="px-2 py-0.5 rounded-full border border-neutral-500 text-neutral-800 hover:bg-[#111111] hover:text-[#ecf1e6] transition">+ All</button>
          </div>
          <div class="flex items-center gap-1.5 text-[10px] text-neutral-700">
            <button type="button" onclick="toggleWindow('win-agentspace')" class="px-2 py-0.5 rounded-full border border-[#111111] bg-white hover:bg-[#111111] hover:text-[#ecf1e6] font-semibold transition">Workstation Files</button>
            <button type="button" onclick="openTerminalQuickStart()" class="px-2 py-0.5 rounded-full border border-neutral-500 hover:bg-[#111111] hover:text-[#ecf1e6] transition">One-Click Install</button>
          </div>
        </div>
        <div class="px-3 py-2" style="flex: 1 1 auto; min-height: 0;">
          <div id="termShellMount" data-tc-shell-mount data-shell-title="Shell" style="height: 100%;"></div>
        </div>
      </div>

      <!-- Bottom status bar -->
      <div class="px-6 py-2.5 bg-[#ecf1e6] flex items-center justify-between font-mono text-xs text-neutral-800 border-t border-black">
        <div class="flex items-center gap-3">
          <span id="aeonikGitBranch" title="Merkle root of your .space">merkle –</span>
          <span>|</span>
          <span id="aeonikStatusCwd">~/space</span>
        </div>
        <div class="flex items-center gap-4 text-neutral-600">
          <span id="termStatusScope">user scope</span>
          <span>|</span>
          <span id="termStatusDrive">drive: –</span>
          <span>|</span>
          <span>UTF-8</span>
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- Window 2: Relay TV Watch Party.app (Baked-in Ads & Memes) -->
    <!-- ===================================================================== -->
    <div id="win-tv" class="mesh-window w-[520px]" data-zen-window="true" data-window-id="win-tv" style="top: 72px; right: 24px; z-index: 21;">
      <!--TC_TITLEBAR {"id": "win-tv", "icon": "📺", "title": "Watch Party", "badge": "Ads & memes"}-->
      <div id="tv" class="window-body p-4 space-y-3 max-h-[620px] overflow-y-auto">
        <div class="w-full flex items-center justify-between">
          <div>
            <h2 class="font-bold text-white text-sm">Relay Video Channel (Ads &amp; Memes Feed)</h2>
            <p id="nowPlayingTitle" class="text-[11px] text-slate-400">Self-hosted Native MP4 · <span class="text-pink-400 font-mono">@nojuannobody</span></p>
          </div>
          <span id="playlistCounterBadge" class="text-[10px] bg-pink-950 text-pink-300 border border-pink-800 px-2.5 py-0.5 rounded-full font-mono uppercase">1 / 1 · Loop</span>
        </div>

        <!-- Video Player with Overlay for Multiplayer Floating Reactions -->
        <div class="relative w-full flex flex-col items-center justify-center overflow-hidden rounded-lg bg-black border border-slate-800 h-[380px]">
          <div class="absolute top-2 right-2 z-20 bg-pink-950/80 border border-pink-600 text-pink-200 text-[9px] font-mono px-2 py-0.5 rounded-full pointer-events-none">
            📣 ADS &amp; MEMES FEED
          </div>
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

        <!-- Admin Intelligence Gathering Banner (Mandatory Ad View) -->
        <div id="adminAdIntelNotice" class="hidden p-2.5 bg-gradient-to-r from-amber-950/90 via-slate-950 to-amber-950/90 border border-amber-500/70 rounded-lg text-xs font-mono flex items-center justify-between shadow-lg">
          <div class="flex items-center gap-2">
            <span class="text-base animate-pulse">📡</span>
            <div>
              <div class="font-bold text-amber-300 flex items-center gap-1.5">
                <span>Admin Intelligence Gathering Active</span>
                <span class="px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[9px] uppercase font-bold">Required</span>
              </div>
              <div class="text-[10px] text-amber-200/80">Admins must watch sponsored ads to completion for market intelligence. Skipping locked.</div>
            </div>
          </div>
          <span id="adminAdIntelTimer" class="px-2 py-0.5 rounded bg-amber-950 border border-amber-700 text-amber-300 font-mono text-[10px] font-bold shrink-0 animate-pulse">🔒 Ad View Required</span>
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
            <button id="playlistPrevBtn" onclick="prevPlaylistVideo()" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 transition">⏮ Prev</button>
            <button id="playlistNextBtn" onclick="nextPlaylistVideo()" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 transition">Next ⏭</button>
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
    <div id="win-arena" class="mesh-window w-[560px]" data-zen-window="true" data-window-id="win-arena" style="top: 720px; left: 24px; z-index: 22;">
      <!--TC_TITLEBAR {"id": "win-arena", "icon": "🧠", "title": "AI Brain Router & Arena"}-->
      <div class="window-body p-4 space-y-4 max-h-[620px] overflow-y-auto">
        <!-- Two-brain duel with per-brain context (arena_duel_ui.py) -->
        <!--ARENA_DUEL:arenaWin-->

        <div class="flex flex-wrap justify-between items-center gap-2">
          <div>
            <h2 class="text-sm font-bold text-white flex items-center gap-2">
              <span>💳</span> OpenRouter &amp; NanoGPT Cost, Spend &amp; Credit Dashboard
            </h2>
            <p class="text-[11px] text-slate-400">Live account credits, NanoGPT USD/NANO balance, key usage, and per-model token pricing</p>
          </div>
          <div id="analyticsHeader" class="text-right text-[11px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800 px-2.5 py-1 rounded-md">
            Fetching live OpenRouter billing...
          </div>
        </div>

        <!-- Shown instead of four "--" tiles when the server has no OpenRouter billing connection -->
        <div id="orDashEmpty" class="tc-empty hidden" role="status">
          <strong>OpenRouter billing is not connected on this server.</strong>
          <span id="orDashEmptyReason">Balance, lifetime spend and key usage appear here once an OpenRouter key is configured for the relay.</span>
          Calls, tokens and cost routed through TinCan are still counted above.
        </div>
        <div id="orStatGrid" class="grid grid-cols-2 gap-2 text-xs">
          <div class="tc-stat p-2.5 border rounded-lg">
            <div class="tc-stat__label">Remaining balance</div>
            <div id="orRemaining" class="tc-stat__value">--</div>
            <div id="orCreditsTotal" class="tc-stat__sub">of -- credits</div>
          </div>
          <div class="tc-stat p-2.5 border rounded-lg">
            <div class="tc-stat__label">Lifetime spend</div>
            <div id="orTotalUsage" class="tc-stat__value">--</div>
            <div class="tc-stat__sub">Account aggregate</div>
          </div>
          <div class="tc-stat p-2.5 border rounded-lg">
            <div class="tc-stat__label">Active key usage</div>
            <div id="orKeyUsage" class="tc-stat__value">--</div>
            <div id="orKeyToday" class="tc-stat__sub">Today: --</div>
          </div>
          <div class="tc-stat p-2.5 border rounded-lg">
            <div class="tc-stat__label">Key budget cap</div>
            <div id="orKeyLimitRem" class="tc-stat__value">--</div>
            <div id="orKeyLabel" class="tc-stat__sub truncate">Key: --</div>
          </div>
        </div>

        <div id="nanoDashBanner" class="flex flex-wrap items-center justify-between gap-2 p-2.5 rounded-lg border border-cyan-800/60 bg-cyan-950/30 text-[11px] font-mono">
          <div class="flex items-center gap-2 min-w-0">
            <span class="px-1.5 py-0.5 rounded bg-cyan-900/70 text-cyan-200 border border-cyan-700/70 font-bold shrink-0">NanoGPT</span>
            <span id="nanoDashStatus" class="text-slate-300 truncate">Checking NanoGPT gateway balance...</span>
          </div>
          <a href="/api/models/nanogpt" target="_blank" rel="noopener" class="text-cyan-300 hover:text-cyan-200 underline shrink-0">/api/models/nanogpt</a>
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
          <div class="tc-swap-grid grid grid-cols-1 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] gap-2 text-xs items-end">
            <div class="min-w-0">
              <label for="aliasSelect" class="block text-slate-400 mb-1 text-[11px]">Target alias</label>
              <select id="aliasSelect" onchange="syncSelectedAliasModel(true); this.title = this.options[this.selectedIndex]?.text || ''" class="tc-truncate w-full min-w-0 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white font-mono">
                <option value="gemini-brain">gemini-brain → google/gemini-2.5-flash</option>
                <option value="claude-brain">claude-brain → anthropic/claude-sonnet-5.5</option>
                <option value="grok-brain">grok-brain → x-ai/grok-4.7</option>
                <option value="openai-brain">openai-brain → openai/gpt-4o</option>
                <option value="nanogpt-brain">nanogpt-brain → nanogpt/pqhaz/DeepSeek-V4.1-Flash-1017-heretic</option>
              </select>
            </div>
            <div class="min-w-0">
              <label for="modelInput" class="block text-slate-400 mb-1 text-[11px]">Model ID (OpenRouter or nanogpt/*)</label>
              <input type="text" id="modelInput" placeholder="e.g. nanogpt/pqhaz/DeepSeek-V4.1-Flash-1017-heretic" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white font-mono placeholder:text-slate-600">
            </div>
            <div class="flex items-end">
              <button onclick="updateModel()" class="tc-btn w-full whitespace-nowrap bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded px-2.5 py-1.5 transition active:scale-95 text-xs">
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
            <button type="button" onclick="quickPickModel('nanogpt/pqhaz/DeepSeek-V4.1-Flash-1017-heretic')" class="px-1.5 py-0.5 rounded bg-cyan-950/70 hover:bg-cyan-900 text-cyan-200 border border-cyan-700/70">nanogpt-heretic</button>
            <button type="button" onclick="quickPickModel('nanogpt/abliteration-ai/abliterated-model-large-v2')" class="px-1.5 py-0.5 rounded bg-cyan-950/70 hover:bg-cyan-900 text-cyan-200 border border-cyan-700/70">nanogpt-abliterated-v2</button>
            <button type="button" onclick="quickPickModel('nanogpt/TEE/deepseek-v4.1-flash')" class="px-1.5 py-0.5 rounded bg-cyan-950/70 hover:bg-cyan-900 text-cyan-200 border border-cyan-700/70">nanogpt-tee</button>
          </div>
          <p id="updateFeedback" class="text-xs mt-2 font-mono hidden"></p>
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- Window 4A: WebRTC Video & Voice Studio.app -->
    <!-- ===================================================================== -->
    <div id="win-call" class="mesh-window w-[540px]" data-zen-window="true" data-window-id="win-call" style="top: 720px; right: 24px; z-index: 23;">
      <!--TC_TITLEBAR {"id": "win-call", "icon": "📹", "title": "WebRTC Video Studio"}-->
      <div id="call" class="window-body p-4 space-y-3 max-h-[620px] overflow-y-auto">
        <div class="flex flex-wrap justify-between items-center gap-2">
          <div>
            <h2 class="text-xs font-bold text-white uppercase tracking-wider">WebRTC Video &amp; Voice Studio</h2>
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

        <!-- Active Room Peers -->
        <div class="pt-2 border-t border-slate-800">
          <div class="text-[11px] font-semibold text-slate-400 mb-1.5">Active Room &amp; UDP Streams</div>
          <div id="roomPeersGrid" class="space-y-1.5 text-xs font-mono">
            <div class="p-2 bg-slate-800/40 rounded border border-slate-700/60 text-slate-400 text-center">
              No active peers connected to this room yet.
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- Window 4B: Encrypted Mesh Chat & Comms.app (Separated from Video) -->
    <!-- ===================================================================== -->
    <div id="win-comms" class="mesh-window w-[680px] max-w-[96vw]" data-zen-window="true" data-window-id="win-comms" style="top: 720px; left: 620px; z-index: 23;">
      <!--TC_TITLEBAR {"id": "win-comms", "icon": "💬", "title": "Encrypted Mesh Chat"}-->
      <div class="window-body p-4 space-y-3 max-h-[620px] overflow-y-auto">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
              <span>🔒</span> Zero-Account Blind Relay Chat
            </h2>
            <p class="text-[11px] text-slate-400">Ed25519 sealed blind messaging across federated peers</p>
          </div>
          <span id="chatCounterBadge" class="text-[10px] font-mono text-cyan-400 bg-cyan-950/80 px-2 py-0.5 rounded border border-cyan-800">0 messages</span>
        </div>

        <!-- Discord-Style Channels + People Sidebar & Encrypted Message Stream -->
        <div class="grid grid-cols-1 sm:grid-cols-[185px_minmax(0,1fr)] gap-3 items-stretch">
          <aside class="bg-slate-950/90 border border-slate-800 rounded-lg p-2.5 flex flex-col gap-3 text-xs font-mono">
            <div>
              <div class="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                <span>Channels</span>
                <button type="button" onclick="promptNewChatChannel()" class="px-1.5 py-0.5 rounded border border-slate-700 text-cyan-300 hover:bg-slate-800" title="Create channel">+</button>
              </div>
              <div id="chatChannelsList" class="space-y-1">
                <button type="button" data-channel="main" onclick="selectChatTarget('channel', 'main', '#main')" class="w-full text-left px-2 py-1 rounded bg-cyan-950/80 border border-cyan-700/70 text-cyan-200 font-bold text-[11px] flex items-center justify-between">#main</button>
                <button type="button" data-channel="architecture" onclick="selectChatTarget('channel', 'architecture', '#architecture')" class="w-full text-left px-2 py-1 rounded text-slate-300 hover:bg-slate-900 text-[11px] flex items-center justify-between">#architecture</button>
                <button type="button" data-channel="cyberspace" onclick="selectChatTarget('channel', 'cyberspace', '#cyberspace')" class="w-full text-left px-2 py-1 rounded text-slate-300 hover:bg-slate-900 text-[11px] flex items-center justify-between">#cyberspace</button>
                <button type="button" data-channel="arena" onclick="selectChatTarget('channel', 'arena', '#arena')" class="w-full text-left px-2 py-1 rounded text-slate-300 hover:bg-slate-900 text-[11px] flex items-center justify-between">#arena</button>
              </div>
            </div>
            <div class="border-t border-slate-800 pt-2 flex-1 min-h-0 flex flex-col">
              <div class="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                <span>People in Room</span>
                <button type="button" onclick="refreshCommsPeopleRoster()" class="text-slate-400 hover:text-cyan-300" title="Refresh people roster">↻</button>
              </div>
              <div id="chatPeopleList" class="space-y-1 max-h-40 overflow-y-auto">
                <div class="text-[10px] text-slate-500 italic">Loading room people...</div>
              </div>
            </div>
          </aside>

          <div class="flex flex-col gap-2 min-w-0">
            <!-- Chat Filter / Recipient Bar -->
            <div class="bg-slate-950/80 border border-slate-800 rounded-lg p-2 flex flex-wrap items-center gap-2 text-xs font-mono">
              <span id="chatActiveTargetBanner" class="text-[11px] font-bold text-emerald-300 bg-emerald-950/60 border border-emerald-800/80 rounded px-2 py-0.5">#main · Broadcast</span>
              <select id="chatChannelSelect" onchange="onChatModeSelectChange(this.value)" class="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-cyan-300 text-xs focus:outline-none">
                <option value="room">🌐 Room Channel</option>
                <option value="direct">👤 Direct Sealed P2P</option>
              </select>
              <input id="chatDirectPeerInput" type="text" placeholder="Peer ID or @handle (for DM)" class="hidden flex-1 min-w-[140px] bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
            </div>

            <!-- Message stream -->
            <div id="chatMessagesList" class="h-64 overflow-y-auto p-3 bg-slate-950/90 border border-slate-800 rounded-lg space-y-2 text-xs font-mono">
              <div class="text-slate-500 text-[11px] italic">No messages yet. Select a #channel or a person on the left to chat.</div>
            </div>

            <!-- Message input -->
            <div class="flex gap-1.5">
              <input id="chatInput" type="text" placeholder="Message #main or type @peer..." class="flex-1 min-w-0 bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white font-mono placeholder:text-slate-600 focus:border-cyan-400 focus:outline-none" onkeydown="if(event.key==='Enter') sendChatMessage()">
              <button onclick="sendChatMessage()" class="px-4 py-2 bg-gradient-to-r from-cyan-600 to-indigo-600 hover:brightness-110 text-white rounded-lg text-xs font-bold font-mono transition active:scale-95 shrink-0 flex items-center gap-1 shadow">
                <span>Send</span>
                <span>↵</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- Window 5: Rewards, Arena & Operator Leaderboard.app -->
    <!-- ===================================================================== -->
    <div id="win-quests" class="mesh-window w-[1100px] max-w-full" data-zen-window="true" data-window-id="win-quests" style="top: 1380px; left: 24px; z-index: 24;">
      <!--TC_TITLEBAR {"id": "win-quests", "icon": "🪙", "title": "Quests · Onboarding & Credit Requests"}-->
      <div class="window-body p-4 space-y-6 max-h-[750px] overflow-y-auto">

        <!-- Top Section: Admin-Controlled $TINCAN Minting & User Request / Add Money -->
        <div class="space-y-4">
          <div class="p-4 bg-gradient-to-r from-slate-900/95 via-slate-900/90 to-emerald-950/50 rounded-xl border border-emerald-500/40 space-y-3">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div class="flex items-center gap-2.5">
                <span class="text-2xl">🪙</span>
                <div>
                  <h2 class="text-sm font-bold text-white font-mono flex items-center gap-2">
                    <span>$TINCAN Credit &amp; Minting Program</span>
                    <span class="px-2 py-0.5 rounded-full bg-slate-900 text-emerald-300 border border-emerald-600/70 text-[10px] font-bold uppercase tracking-wider">ADMIN CONTROLLED</span>
                  </h2>
                  <p class="text-xs text-slate-300">Add money via Stripe to auto-mint credits, or request an operator credit grant. Only company admins can mint &amp; route $TINCAN directly.</p>
                </div>
              </div>
              <div class="flex flex-wrap items-center gap-2 font-mono">
                <button onclick="toggleMintRequestDrawer()" id="btnRequestMintDrawer" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-emerald-300 border border-emerald-600/70 font-bold rounded-lg text-xs transition active:scale-95 flex items-center gap-1.5">
                  <span>➕</span> <span>Request $TINCAN</span>
                </button>
                <button onclick="openAddMoneyFromQuests()" class="px-3 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-lg text-xs transition active:scale-95 shadow flex items-center gap-1.5">
                  <span>💳</span> <span>Add Money (Auto-Mint)</span>
                </button>
              </div>
            </div>

            <!-- User Mint Request Drawer (non-privileged; queued for admin review) -->
            <div id="mintRequestDrawer" class="hidden p-3 bg-slate-950/90 border border-slate-800 rounded-lg space-y-2.5 font-mono text-xs">
              <div class="flex items-center justify-between">
                <span class="text-emerald-300 font-bold">Request Admin $TINCAN Credit Grant</span>
                <button onclick="toggleMintRequestDrawer()" class="text-slate-400 hover:text-white text-[11px]">✕ Close</button>
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Amount Requested ($TINCAN)</label>
                  <input id="mintReqAmountInput" type="number" min="1" max="100000" value="100" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
                <div class="sm:col-span-2">
                  <label class="text-[10px] text-slate-400 block mb-0.5">Reason / Workflow Note</label>
                  <input id="mintReqReasonInput" type="text" placeholder="e.g. Onboarding pilot compute grant or customer credit" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
              </div>
              <div class="flex items-center justify-between gap-2">
                <span id="mintRequestStatusBanner" class="text-[11px] text-slate-400">Requests remain pending until approved by an admin.</span>
                <button onclick="submitMintRequest()" class="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded text-[11px] transition active:scale-95">Submit Mint Request</button>
              </div>
              <div id="myMintRequestsList" class="space-y-1 text-[11px]"></div>
            </div>

            <!-- Admin-Only Mint & Customer Routing Console -->
            <div id="questsAdminMintCard" class="hidden p-3.5 bg-amber-950/25 border border-amber-500/60 rounded-lg space-y-3 font-mono text-xs">
              <div class="flex flex-wrap items-center justify-between gap-2 border-b border-amber-800/50 pb-2">
                <div class="text-amber-300 font-bold flex items-center gap-1.5">
                  <span>🛡️</span> <span>Admin Mint &amp; Route Credits (Internal Only)</span>
                </div>
                <span class="text-[10px] text-amber-400/90">Requires valid X-Admin-Key</span>
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-4 gap-2">
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Customer Peer ID *</label>
                  <input id="adminMintTargetPeer" list="adminMintPeerSuggestions" type="text" placeholder="peer-customer-id" class="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                  <datalist id="adminMintPeerSuggestions"></datalist>
                </div>
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Credits ($TINCAN)</label>
                  <input id="adminMintTokensInput" type="number" min="1" value="500" class="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">USD Book Value</label>
                  <input id="adminMintUsdInput" type="number" step="0.01" min="0" value="0.00" class="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Admin Key *</label>
                  <input id="adminMintKeyInput" type="password" placeholder="TINCAN_ADMIN_KEY" class="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
              </div>
              <div class="flex flex-wrap items-center justify-between gap-2">
                <span id="adminMintFeedback" class="text-[11px] text-slate-300">Route free promotional or customer credits directly to any registered peer.</span>
                <div class="flex items-center gap-2">
                  <button onclick="fetchMintRequests(true)" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded text-[11px]">⟳ Load Requests</button>
                  <button onclick="adminMintAndRouteTokens()" class="px-3 py-1 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded text-[11px] transition active:scale-95">🔨 Mint &amp; Route</button>
                </div>
              </div>
              <div id="adminMintRequestsList" class="space-y-1.5 text-[11px]"></div>
            </div>

            <!-- Token Ledger KPI Grid (Synced to real account balance) -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-center pt-1">
              <div class="p-2 bg-slate-950/80 rounded-lg border border-slate-800">
                <div class="text-[10px] text-slate-400">Verified Balance</div>
                <div id="rewardsMintedBalance" class="text-base font-bold text-amber-300 mt-0.5">0 $TINCAN</div>
              </div>
              <div class="p-2 bg-slate-950/80 rounded-lg border border-slate-800">
                <div class="text-[10px] text-slate-400">Self-Serve Funding</div>
                <div class="text-base font-bold text-emerald-400 mt-0.5">Stripe / Ads</div>
              </div>
              <div class="p-2 bg-slate-950/80 rounded-lg border border-slate-800">
                <div class="text-[10px] text-slate-400">Sponsored Clip Auto-Earn</div>
                <div class="text-base font-bold text-cyan-300 mt-0.5">+5,000 CR</div>
              </div>
              <div class="p-2 bg-slate-950/80 rounded-lg border border-slate-800">
                <div class="text-[10px] text-slate-400">Sign-On Onboarding</div>
                <div class="text-base font-bold text-indigo-300 mt-0.5">1x Per Peer</div>
              </div>
            </div>
          </div>

          <!-- One-Time Sign-On Onboarding Quests (Preserving questDeckGrid ID for test invariants) -->
          <div>
            <div class="flex flex-wrap items-center justify-between gap-2 mb-2">
              <div class="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
                <span>🌱</span> <span>Sign-On Onboarding Walkthroughs</span>
              </div>
              <span class="text-[11px] font-mono text-amber-300 bg-amber-950/60 border border-amber-800 px-2 py-0.5 rounded">
                One-Time Sign-On Bonus · No Repeat Drain
              </span>
            </div>

            <div id="questDeckGrid" class="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div class="p-3 bg-slate-950/80 rounded-lg border border-slate-800 flex flex-col justify-between space-y-2">
                <div>
                  <div class="flex justify-between items-center gap-1">
                    <span class="font-bold text-xs text-emerald-400 font-mono">1. Sealed Courier Relay</span>
                    <span id="questBadge-sealed_courier" class="text-[10px] bg-emerald-950 text-emerald-300 border border-emerald-800 px-1.5 py-0.5 rounded font-mono">Sign-On 1x</span>
                  </div>
                  <p class="text-xs text-slate-300 mt-1">First-run walkthrough: dispatch an Ed25519 sealed envelope through TinCan Blind Relay.</p>
                </div>
                <button id="questBtn-sealed_courier" onclick="triggerQuestAction('sealed_courier')" class="w-full py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-mono font-semibold transition active:scale-95">
                  🥫 Run Sign-On Relay (1x)
                </button>
              </div>

              <div class="p-3 bg-slate-950/80 rounded-lg border border-slate-800 flex flex-col justify-between space-y-2">
                <div>
                  <div class="flex justify-between items-center gap-1">
                    <span class="font-bold text-xs text-indigo-400 font-mono">2. AI Arbiter Duel Vote</span>
                    <span id="questBadge-arena_vote" class="text-[10px] bg-indigo-950 text-indigo-300 border border-indigo-800 px-1.5 py-0.5 rounded font-mono">Sign-On 1x</span>
                  </div>
                  <p class="text-xs text-slate-300 mt-1">First-run walkthrough: try one dual-model comparison and cast your sign-on vote.</p>
                </div>
                <button id="questBtn-arena_vote" onclick="triggerQuestAction('arena_vote')" class="w-full py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-mono font-semibold transition active:scale-95">
                  🧠 Log Sign-On Evaluation (1x)
                </button>
              </div>

              <div class="p-3 bg-slate-950/80 rounded-lg border border-slate-800 flex flex-col justify-between space-y-2">
                <div>
                  <div class="flex justify-between items-center gap-1">
                    <span class="font-bold text-xs text-amber-400 font-mono">3. Sandboxed Agent Run</span>
                    <span id="questBadge-coop_action" class="text-[10px] bg-amber-950 text-amber-300 border border-amber-800 px-1.5 py-0.5 rounded font-mono">Sign-On 1x</span>
                  </div>
                  <p class="text-xs text-slate-300 mt-1">First-run walkthrough: test one isolated VFS agent run during initial onboarding.</p>
                </div>
                <button id="questBtn-coop_action" onclick="triggerQuestAction('coop_action')" class="w-full py-1.5 bg-amber-600 hover:bg-amber-500 text-white rounded text-xs font-mono font-semibold transition active:scale-95">
                  ⚡ Run Sign-On Sandbox (1x)
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Gentle OS Routing Cards: Route users cleanly to Brain Arena.app or Network.app instead of crowding Quests -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono">
          <div class="p-3.5 bg-slate-950/75 border border-slate-800 rounded-xl flex items-center justify-between gap-3">
            <div>
              <div class="text-xs font-bold text-white flex items-center gap-1.5"><span>🧠</span> <span>Model Comparison Workspace</span></div>
              <p class="text-[11px] text-slate-400 font-sans mt-0.5">Optional side-by-side prompt evaluation lives in its own OS app window.</p>
            </div>
            <button onclick="toggleWindow('win-arena')" class="shrink-0 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 text-[11px] font-bold transition active:scale-95">
              Open Arena.app ↗
            </button>
          </div>
          <div class="p-3.5 bg-slate-950/75 border border-slate-800 rounded-xl flex items-center justify-between gap-3">
            <div>
              <div class="text-xs font-bold text-white flex items-center gap-1.5"><span>👥</span> <span>Directory &amp; Rankings</span></div>
              <p class="text-[11px] text-slate-400 font-sans mt-0.5">Find online peers, ping visitors, or view optional XP rankings inside Network.</p>
            </div>
            <button onclick="toggleWindow('win-network'); switchNetTab('leaderboard');" class="shrink-0 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-emerald-300 border border-slate-700 text-[11px] font-bold transition active:scale-95">
              Open Network.app ↗
            </button>
          </div>
        </div>

        <!-- Collapsed-by-default Disclosure: Keeps inline Brain Arena DOM intact without interrupting OS flow -->
        <details id="questsArenaDisclosure" class="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3">
          <summary class="cursor-pointer text-xs font-mono text-slate-400 hover:text-slate-200 select-none flex items-center justify-between">
            <span>▸ Optional: Expand inline Brain Arena duel here</span>
            <span class="text-[10px] text-slate-500">Opens inside Arena.app by default</span>
          </summary>
          <div class="pt-3">
            <!--ARENA_DUEL:arena-->
          </div>
        </details>

        <!-- Collapsed-by-default Disclosure: Keeps Operator Leaderboard DOM intact gently -->
        <details id="questsLeaderboardDisclosure" class="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3">
          <summary class="cursor-pointer text-xs font-mono text-slate-400 hover:text-slate-200 select-none flex items-center justify-between">
            <span>▸ Optional: Expand Live Mesh Operator Rankings summary</span>
            <span class="text-[10px] text-slate-500">Real connected peers only</span>
          </summary>
          <div class="pt-3 space-y-2">
            <div class="flex items-center justify-between">
              <h3 class="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                <span>🏆</span> Live Mesh Operator Leaderboard
              </h3>
              <button onclick="toggleWindow('win-network')" class="text-[10px] font-mono text-emerald-400 hover:text-emerald-300 bg-emerald-950/80 border border-emerald-700/80 px-2 py-0.5 rounded transition flex items-center gap-1 active:scale-95">
                <span>👥</span> <span>Open Network Window ↗</span>
              </button>
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
                    <td colspan="5" class="px-3 py-3 text-center text-slate-500">No operator sessions recorded yet.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </details>

      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- Window 6: Admin Moderator Control Panel -->
    <!-- ===================================================================== -->
    <div id="win-moderator" class="mesh-window w-[680px] hidden" data-zen-window="true" data-window-id="win-moderator" style="top: 84px; left: 180px; z-index: 25;">
      <!--TC_TITLEBAR {"id": "win-moderator", "icon": "🛡️", "title": "Admin Moderator", "badge": "Authority: high"}-->
      <div class="window-body p-4 space-y-4 max-h-[660px] overflow-y-auto">

        <!-- Moderator KPI Cards -->
        <div class="grid grid-cols-3 gap-2 font-mono">
          <div class="bg-slate-900/90 border border-slate-800 rounded-lg p-2.5 text-center">
            <div class="text-[10px] text-slate-400 uppercase tracking-wider">Web Visitors</div>
            <div id="modWebCount" class="text-xl font-bold text-emerald-400 mt-0.5">0</div>
            <div class="text-[9px] text-emerald-500/80">Active Browser Tabs</div>
          </div>
          <div class="bg-slate-900/90 border border-slate-800 rounded-lg p-2.5 text-center">
            <div class="text-[10px] text-slate-400 uppercase tracking-wider">Mesh Streams</div>
            <div id="modMeshCount" class="text-xl font-bold text-cyan-400 mt-0.5">0</div>
            <div class="text-[9px] text-cyan-500/80">WebRTC / Workstations</div>
          </div>
          <div class="bg-slate-900/90 border border-amber-900/40 rounded-lg p-2.5 text-center">
            <div class="text-[10px] text-amber-400/90 uppercase tracking-wider">Admin Status</div>
            <div class="text-sm font-bold text-amber-300 mt-1 flex items-center justify-center gap-1">
              <span class="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
              <span>ACTIVE 🛡️</span>
            </div>
            <div class="text-[9px] text-slate-400">Total Mesh Authority</div>
          </div>
        </div>

        <!-- Emergency Moderator Broadcast -->
        <div class="bg-slate-900/90 border border-amber-700/60 rounded-xl p-3.5 space-y-2">
          <div class="flex items-center justify-between">
            <div class="text-xs font-bold text-amber-300 font-mono flex items-center gap-1.5">
              <span>📢</span>
              <span>System-Wide Moderator Announcement</span>
            </div>
            <span class="text-[10px] text-slate-400 font-mono">Pushes banner to all web &amp; mesh clients</span>
          </div>
          <div class="flex gap-2">
            <input type="text" id="adminAnnouncementInput" placeholder="Enter high-priority announcement (e.g., 'Scheduled maintenance in 10 mins' or 'Welcome to the lab')..." class="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white font-mono placeholder:text-slate-600 focus:outline-none focus:border-amber-500">
            <button onclick="sendAdminBroadcast()" class="px-3 py-1.5 bg-gradient-to-r from-amber-600 to-yellow-600 hover:brightness-110 text-slate-950 font-bold rounded-lg text-xs font-mono transition active:scale-95 shadow flex items-center gap-1">
              <span>⚡</span> <span>Broadcast</span>
            </button>
          </div>
        </div>

        <!-- Section 1: Relay Website Visitors -->
        <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5 space-y-2.5">
          <div class="flex items-center justify-between border-b border-slate-800/80 pb-2">
            <div class="text-xs font-bold text-emerald-400 font-mono flex items-center gap-1.5">
              <span>🌐</span>
              <span>Relay Website Visitors (Active Browser Cursors)</span>
            </div>
            <span id="modWebVisitorsCountTag" class="text-[11px] font-mono text-slate-400">0 connected</span>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left font-mono text-xs">
              <thead class="text-slate-400 bg-slate-950/60 border-b border-slate-800 text-[11px]">
                <tr>
                  <th class="px-2.5 py-1.5">Peer ID</th>
                  <th class="px-2.5 py-1.5">Room</th>
                  <th class="px-2.5 py-1.5">Focus Window</th>
                  <th class="px-2.5 py-1.5">Cursor Pos</th>
                  <th class="px-2.5 py-1.5">Last Seen</th>
                  <th class="px-2.5 py-1.5 text-right">Moderator Action</th>
                </tr>
              </thead>
              <tbody id="modWebVisitorsTable" class="divide-y divide-slate-800/50">
                <tr><td colspan="6" class="px-3 py-3 text-center text-slate-500 text-[11px]">Polling live website cursors...</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Section 2: Connected Mesh Nodes -->
        <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5 space-y-2.5">
          <div class="flex items-center justify-between border-b border-slate-800/80 pb-2">
            <div class="text-xs font-bold text-cyan-400 font-mono flex items-center gap-1.5">
              <span>📡</span>
              <span>Connected Mesh Nodes (Live WebRTC Streams &amp; Workstations)</span>
            </div>
            <span id="modMeshNodesCountTag" class="text-[11px] font-mono text-slate-400">0 streams</span>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left font-mono text-xs">
              <thead class="text-slate-400 bg-slate-950/60 border-b border-slate-800 text-[11px]">
                <tr>
                  <th class="px-2.5 py-1.5">Peer / Node ID</th>
                  <th class="px-2.5 py-1.5">Display Name</th>
                  <th class="px-2.5 py-1.5">Room</th>
                  <th class="px-2.5 py-1.5">Media Capabilities</th>
                  <th class="px-2.5 py-1.5">UDP Port</th>
                  <th class="px-2.5 py-1.5 text-right">Moderator Action</th>
                </tr>
              </thead>
              <tbody id="modMeshNodesTable" class="divide-y divide-slate-800/50">
                <tr><td colspan="6" class="px-3 py-3 text-center text-slate-500 text-[11px]">Polling active WebRTC streams...</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Section 3: Video & Sponsored Ad Fleet Studio (Admin CRUD) -->
        <div class="bg-slate-900/80 border border-pink-900/50 rounded-xl p-3.5 space-y-3">
          <div class="flex items-center justify-between border-b border-slate-800/80 pb-2">
            <div class="text-xs font-bold text-pink-400 font-mono flex items-center gap-1.5">
              <span>🎬</span>
              <span>Video &amp; Sponsored Ad Fleet Studio (Admin CRUD)</span>
            </div>
            <div class="flex items-center gap-1.5">
              <button onclick="toggleAdminTab('videos')" id="adminTabBtnVideos" class="px-2 py-0.5 rounded bg-pink-950 text-pink-300 border border-pink-700 text-[10px] font-mono font-bold">Videos (<span id="adminVideosCount">0</span>)</button>
              <button onclick="toggleAdminTab('sponsors')" id="adminTabBtnSponsors" class="px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 text-[10px] font-mono">Sponsor Ads (<span id="adminSponsorsCount">0</span>)</button>
            </div>
          </div>

          <!-- Sub-Panel A: Videos CRUD -->
          <div id="adminVideosPanel" class="space-y-2.5">
            <div class="flex items-center justify-between">
              <span class="text-[11px] text-slate-300 font-mono">Relay Watch Party Collection (S3 Backed)</span>
              <button onclick="toggleAddVideoDrawer()" class="px-2.5 py-1 bg-pink-600 hover:bg-pink-500 text-white font-mono text-[10px] rounded font-bold transition flex items-center gap-1 active:scale-95">
                <span>+</span> <span>Add Video / Ingest MP4</span>
              </button>
            </div>

            <!-- Add Video Drawer -->
            <div id="adminAddVideoDrawer" class="hidden p-2.5 bg-slate-950 border border-pink-800/60 rounded-lg space-y-2 text-xs font-mono">
              <div class="grid grid-cols-2 gap-2">
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Video URL or TikTok ID *</label>
                  <input id="adminNewVideoUrl" type="text" placeholder="https://www.tiktok.com/@creator/video/123... or ID" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Display Title</label>
                  <input id="adminNewVideoTitle" type="text" placeholder="Video Title" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
              </div>
              <div class="grid grid-cols-3 gap-2">
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Creator Handle</label>
                  <input id="adminNewVideoCreator" type="text" placeholder="@creator" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Category</label>
                  <select id="adminNewVideoCategory" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                    <option value="spotlight">spotlight</option>
                    <option value="instruction">instruction</option>
                    <option value="ad">ad (sponsored)</option>
                  </select>
                </div>
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Duration (Seconds)</label>
                  <input id="adminNewVideoDuration" type="number" value="35" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
              </div>
              <div class="flex justify-end gap-1.5 pt-1">
                <button onclick="toggleAddVideoDrawer()" class="px-2.5 py-1 bg-slate-800 text-slate-300 rounded text-[10px]">Cancel</button>
                <button onclick="adminSubmitAddVideo()" class="px-3 py-1 bg-pink-600 hover:bg-pink-500 text-white font-bold rounded text-[10px] active:scale-95">Save &amp; Ingest to S3</button>
              </div>
            </div>

            <!-- Videos Table -->
            <div class="overflow-x-auto">
              <table class="w-full text-left font-mono text-xs">
                <thead class="text-slate-400 bg-slate-950/60 border-b border-slate-800 text-[11px]">
                  <tr>
                    <th class="px-2.5 py-1.5">ID / Stream</th>
                    <th class="px-2.5 py-1.5">Title</th>
                    <th class="px-2.5 py-1.5">Creator</th>
                    <th class="px-2.5 py-1.5">Category</th>
                    <th class="px-2.5 py-1.5">Dur</th>
                    <th class="px-2.5 py-1.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody id="adminVideosTableBody" class="divide-y divide-slate-800/50">
                  <tr><td colspan="6" class="px-3 py-3 text-center text-slate-500 text-[11px]">Loading video collection...</td></tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Sub-Panel B: Sponsor Ads CRUD -->
          <div id="adminSponsorsPanel" class="hidden space-y-2.5">
            <div class="flex items-center justify-between">
              <span class="text-[11px] text-slate-300 font-mono">Sponsor Creatives &amp; Ad Subsidies</span>
              <button onclick="toggleAddSponsorDrawer()" class="px-2.5 py-1 bg-amber-600 hover:bg-amber-500 text-slate-950 font-mono text-[10px] rounded font-bold transition flex items-center gap-1 active:scale-95">
                <span>+</span> <span>Add Sponsor Creative</span>
              </button>
            </div>

            <!-- Add Sponsor Drawer -->
            <div id="adminAddSponsorDrawer" class="hidden p-2.5 bg-slate-950 border border-amber-800/60 rounded-lg space-y-2 text-xs font-mono">
              <div class="grid grid-cols-3 gap-2">
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Sponsor Name *</label>
                  <input id="adminNewSponsorName" type="text" placeholder="e.g. Anthropic Claude" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Icon / Emoji</label>
                  <input id="adminNewSponsorIcon" type="text" value="🌟" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Badge Text</label>
                  <input id="adminNewSponsorBadge" type="text" value="Partner" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
              </div>
              <div class="grid grid-cols-2 gap-2">
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Tagline</label>
                  <input id="adminNewSponsorTagline" type="text" placeholder="Tagline description" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Destination URL</label>
                  <input id="adminNewSponsorUrl" type="text" placeholder="https://..." class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
              </div>
              <div class="grid grid-cols-3 gap-2">
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">CTA Button</label>
                  <input id="adminNewSponsorCta" type="text" value="Visit Partner ↗" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Reward Tokens</label>
                  <input id="adminNewSponsorRewardTokens" type="number" value="5000" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Reward USD</label>
                  <input id="adminNewSponsorRewardUsd" type="number" step="0.01" value="0.05" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
              </div>
              <div class="flex justify-end gap-1.5 pt-1">
                <button onclick="toggleAddSponsorDrawer()" class="px-2.5 py-1 bg-slate-800 text-slate-300 rounded text-[10px]">Cancel</button>
                <button onclick="adminSubmitAddSponsor()" class="px-3 py-1 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded text-[10px] active:scale-95">Save Sponsor Ad</button>
              </div>
            </div>

            <!-- Sponsors Table -->
            <div class="overflow-x-auto">
              <table class="w-full text-left font-mono text-xs">
                <thead class="text-slate-400 bg-slate-950/60 border-b border-slate-800 text-[11px]">
                  <tr>
                    <th class="px-2.5 py-1.5">Sponsor</th>
                    <th class="px-2.5 py-1.5">Badge</th>
                    <th class="px-2.5 py-1.5">Reward</th>
                    <th class="px-2.5 py-1.5">Telemetry (Imp/Clk/Comp)</th>
                    <th class="px-2.5 py-1.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody id="adminSponsorsTableBody" class="divide-y divide-slate-800/50">
                  <tr><td colspan="5" class="px-3 py-3 text-center text-slate-500 text-[11px]">Loading sponsor creatives...</td></tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Section 4: Peer Ban Management (Ban & Revoke Access) -->
        <div class="bg-slate-900/80 border border-red-900/60 rounded-xl p-3.5 space-y-3">
          <div class="flex items-center justify-between border-b border-slate-800/80 pb-2">
            <div class="text-xs font-bold text-red-400 font-mono flex items-center gap-1.5">
              <span>🚫</span>
              <span>Peer Ban Management (Spaces &amp; Mesh Access)</span>
            </div>
            <button onclick="fetchBannedPeers()" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-mono border border-slate-700">⟳ Refresh</button>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <input id="adminBanPeerInput" type="text" placeholder="Peer ID or Username to ban..." class="bg-slate-950 border border-slate-700 rounded px-2.5 py-1 text-white text-xs font-mono focus:border-red-500 focus:outline-none">
            <input id="adminBanReasonInput" type="text" placeholder="Reason (e.g. Malicious code execution, abuse)" class="bg-slate-950 border border-slate-700 rounded px-2.5 py-1 text-white text-xs font-mono focus:border-red-500 focus:outline-none">
            <button onclick="adminBanPeerAction()" class="px-3 py-1 bg-red-700 hover:bg-red-600 text-white font-mono text-xs font-bold rounded transition active:scale-95 flex items-center justify-center gap-1">
              <span>🚫</span> <span>Ban Peer from Mesh</span>
            </button>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left font-mono text-xs">
              <thead class="text-slate-400 bg-slate-950/60 border-b border-slate-800 text-[11px]">
                <tr>
                  <th class="px-2.5 py-1.5">Banned Peer</th>
                  <th class="px-2.5 py-1.5">Reason</th>
                  <th class="px-2.5 py-1.5">Banned By</th>
                  <th class="px-2.5 py-1.5">Date</th>
                  <th class="px-2.5 py-1.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody id="modBannedPeersTable" class="divide-y divide-slate-800/50">
                <tr><td colspan="5" class="px-3 py-2 text-center text-slate-500 text-[11px]">No peers currently banned.</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Section 5: Reported Digital Artifacts Inspector -->
        <div class="bg-slate-900/80 border border-purple-900/60 rounded-xl p-3.5 space-y-3">
          <div class="flex items-center justify-between border-b border-slate-800/80 pb-2">
            <div class="text-xs font-bold text-purple-300 font-mono flex items-center gap-1.5">
              <span>🔎</span>
              <span>Reported Digital Artifacts Inspector</span>
            </div>
            <button onclick="fetchReportedArtifacts()" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-mono border border-slate-700">⟳ Refresh</button>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left font-mono text-xs">
              <thead class="text-slate-400 bg-slate-950/60 border-b border-slate-800 text-[11px]">
                <tr>
                  <th class="px-2.5 py-1.5">Report ID</th>
                  <th class="px-2.5 py-1.5">Reported Peer</th>
                  <th class="px-2.5 py-1.5">Artifact Path</th>
                  <th class="px-2.5 py-1.5">Reason</th>
                  <th class="px-2.5 py-1.5 text-right">Moderator Review</th>
                </tr>
              </thead>
              <tbody id="modReportedArtifactsTable" class="divide-y divide-slate-800/50">
                <tr><td colspan="5" class="px-3 py-2 text-center text-slate-500 text-[11px]">No reported artifacts to review.</td></tr>
              </tbody>
            </table>
          </div>
          <!-- Artifact Preview Box -->
          <div id="reportedArtifactViewer" class="hidden p-3 bg-slate-950 border border-purple-800/60 rounded-lg space-y-2 text-xs font-mono">
            <div class="flex items-center justify-between">
              <span id="reportedArtifactTitle" class="text-purple-300 font-bold">Artifact Details</span>
              <button onclick="document.getElementById('reportedArtifactViewer').classList.add('hidden')" class="text-slate-400 hover:text-white">✕</button>
            </div>
            <pre id="reportedArtifactContent" class="p-2 bg-black/80 rounded border border-slate-800 text-slate-300 max-h-40 overflow-y-auto whitespace-pre-wrap"></pre>
          </div>
        </div>

      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- Window 7: Token Billing, Top-Up & Sponsored Ads.app -->
    <!-- ===================================================================== -->
    <!--TC_TOKEN_VAULT_WINDOW-->

    <!-- ===================================================================== -->
    <!-- Window 8: Cyberspace Discussion Board · GraphRAG + BM25 + @verifier-agent -->
    <!-- ===================================================================== -->
    <div id="win-board" class="mesh-window w-[940px] max-w-full" data-zen-window="true" data-window-id="win-board" style="top: 84px; left: 130px; z-index: 27;">
      <!--TC_TITLEBAR {"id": "win-board", "icon": "🌐", "title": "Cyberspace Board", "badge": "GraphRAG + BM25"}-->

      <div id="board" class="window-body p-4 space-y-3.5 max-h-[780px] overflow-y-auto text-xs font-sans bg-[#ecf1e6] text-[#111111]">
        <!-- Identity Verification Agent (@verifier-agent) Status & Form Dispatch Banner -->
        <div id="boardVerifierBanner" class="p-3 bg-[#f4f8f0] rounded-2xl border border-[#111111] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-[#111111]">
          <div class="flex items-center gap-2.5">
            <span class="text-xl">🛡️</span>
            <div>
              <div class="font-mono font-bold text-[#111111] text-xs flex flex-wrap items-center gap-2">
                <span>Identity Agent: <span class="text-[#107a47]">@verifier-agent</span></span>
                <span id="boardVerifiedBadge" class="px-2 py-0.5 rounded-full bg-[#ffffff] text-[#107a47] border border-[#107a47] text-[10px] font-semibold">Checking...</span>
                <span id="boardAttestationBadge" class="hidden px-2 py-0.5 rounded-full bg-[#ffffff] text-[#111111] border border-[#111111]/40 text-[10px] font-mono"></span>
              </div>
              <p id="boardVerifierSubtext" class="text-[11px] text-[#4a4a4a] mt-0.5">
                Verify your identity to tag @usernames, summon @ai-agents, vote on threads, and build the Cyberspace Knowledge Graph.
              </p>
            </div>
          </div>
          <div class="flex items-center gap-1.5 shrink-0">
            <button type="button" onclick="requestAgentVerificationForm()" class="px-3 py-1.5 rounded-full bg-[#111111] hover:bg-[#107a47] text-[#ecf1e6] font-mono font-bold text-[11px] transition active:scale-95">
              📨 Have @verifier-agent Send Form
            </button>
            <button type="button" onclick="switchBoardTab('verify')" class="px-3 py-1.5 rounded-full bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border border-[#111111] font-mono font-bold text-[11px] transition">
              🛡️ Open Verification Form
            </button>
          </div>
        </div>

        <!-- Navigation Tabs + Graph Telemetry Pill -->
        <div class="flex flex-wrap items-center justify-between gap-2 border-b border-[#111111]/20 pb-2.5 font-mono">
          <div class="flex flex-wrap items-center gap-1.5">
            <button id="boardTabBtn-discussions" type="button" onclick="switchBoardTab('discussions')" class="px-3 py-1.5 rounded-full bg-[#111111] text-[#ecf1e6] border border-[#111111] font-bold text-xs transition flex items-center gap-1">
              💬 Discussions
            </button>
            <button id="boardTabBtn-feed" type="button" onclick="switchBoardTab('feed')" class="px-3 py-1.5 rounded-full bg-[#ffffff] hover:bg-[#f4f8f0] text-[#111111] border border-[#111111] text-xs transition flex items-center gap-1">
              <span>📰 Feed &amp; Threads</span>
              <span id="boardCuratedCountBadge" class="px-1.5 py-0.2 rounded-full bg-[#107a47] text-[#ffffff] text-[10px] font-bold">0</span>
            </button>
            <button id="boardTabBtn-graph" type="button" onclick="switchBoardTab('graph')" class="px-3 py-1.5 rounded-full bg-[#ffffff] hover:bg-[#f4f8f0] text-[#111111] border border-[#111111] text-xs transition flex items-center gap-1">
              🕸️ Knowledge Graph Explorer
            </button>
            <button id="boardTabBtn-verify" type="button" onclick="switchBoardTab('verify')" class="px-3 py-1.5 rounded-full bg-[#ffffff] hover:bg-[#f4f8f0] text-[#111111] border border-[#111111] text-xs transition flex items-center gap-1">
              <span>🛡️ @verifier-agent Center</span>
              <span id="boardPendingVerifyCount" class="px-1.5 py-0.2 rounded-full bg-[#107a47]/15 text-[#107a47] border border-[#107a47]/50 text-[10px] font-bold">0</span>
            </button>
          </div>
          <div class="flex items-center gap-2">
            <span id="boardGraphStatsBadge" class="text-[10px] font-mono text-[#107a47] bg-[#ffffff] px-2.5 py-1 rounded-full border border-[#111111]/30 font-semibold">● Graph: loading...</span>
            <button type="button" onclick="loadCyberspaceBoard()" class="px-2.5 py-1 rounded-full bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border border-[#111111] text-[10px] font-semibold transition" title="Refresh Board & S3 Sync">🔄 Sync</button>
          </div>
        </div>

        <!-- Citizen Profile & Attestation Inspector Drawer (Hidden until a @username is clicked) -->
        <div id="boardProfileDrawer" class="hidden p-3 bg-[#ffffff] rounded-2xl border border-[#111111] space-y-2 font-mono text-xs shadow-lg text-[#111111]">
          <div class="flex items-center justify-between border-b border-[#111111]/15 pb-1.5">
            <div class="flex items-center gap-2">
              <span class="text-base">🪪</span>
              <span id="boardProfileName" class="font-bold text-[#111111] text-sm">@username</span>
              <span id="boardProfileVerifiedPill" class="px-2 py-0.5 rounded-full text-[10px]"></span>
            </div>
            <button type="button" onclick="document.getElementById('boardProfileDrawer').classList.add('hidden')" class="text-[#4a4a4a] hover:text-[#111111] px-1.5">✕</button>
          </div>
          <div id="boardProfileMeta" class="text-[11px] text-[#111111] grid grid-cols-1 sm:grid-cols-3 gap-2"></div>
          <div id="boardProfileTopics" class="text-[10px] text-[#4a4a4a] space-y-1 pt-1 border-t border-[#111111]/15"></div>
        </div>

        <!-- =============================================================== -->
        <!-- TAB 1: DISCUSSIONS & THREADS -->
        <!-- =============================================================== -->
        <div id="boardTab-discussions" class="space-y-3.5">
          <!-- Unified search bar: one input. #topics, @people/@agents, /search, /topic, is:verified. Cmd/Ctrl+K focuses it. -->
          <div id="boardUnifiedSearch" class="ubar-wrap p-3 bg-[#ffffff] rounded-2xl border border-[#111111] space-y-2">
            <div class="ubar-row">
              <div id="boardUnifiedBar" class="ubar" onclick="document.getElementById('boardSearchInput').focus()">
                <span class="ubar-icon" aria-hidden="true">&#x2315;</span>
                <div id="boardSearchChips" class="ubar-chips" aria-label="Active filters"></div>
                <input id="boardSearchInput" type="text" autocomplete="off" spellcheck="false"
                       role="combobox" aria-expanded="false" aria-autocomplete="list" aria-controls="boardSuggestList"
                       aria-label="Search or start topic on Cyberspace"
                       placeholder="/search or start topic: /search <query>, @peer, #hashtag, or /thread <name>..."
                       oninput="onBoardSearchInput(event)" onkeydown="onBoardSearchKeydown(event)" onblur="setTimeout(closeBoardSuggest, 150)" />
                <label class="ubar-sortwrap" onclick="event.stopPropagation()" title="Sort results (or type /sort activity)">
                  <span class="ubar-sort-label">sort</span>
                  <select id="boardSortSelect" onchange="onBoardSortChange()" class="ubar-sort" aria-label="Sort">
                    <option value="hot">Hot</option>
                    <option value="activity">Activity</option>
                    <option value="new">Newest</option>
                    <option value="top">Top</option>
                    <option value="discussed">Most discussed</option>
                  </select>
                </label>
                <button type="button" onclick="event.stopPropagation(); submitBoardOmniInput()" class="px-3 py-1 rounded-full bg-[#111111] hover:bg-[#107a47] text-[#ecf1e6] font-mono font-bold text-[10px] shrink-0 transition" title="Execute /search, /post, /thread, /feed or search">Post / Search ↵</button>
                <kbd class="ubar-kbd" title="Cmd/Ctrl+K focuses search">&#x2318;K</kbd>
              </div>
            </div>

            <!-- Persistent Always-Visible Inline Free-Model AI Suggestions Chip Strip -->
            <div id="boardAiSuggestBar" class="px-3 py-2 bg-[#f4f8f0] rounded-xl border border-[#107a47]/50 font-mono text-[11px]">
              <div id="boardAiSuggestionsBar" class="flex flex-wrap items-center justify-between gap-2">
                <div class="flex flex-wrap items-center gap-1.5 min-w-0">
                  <span class="text-[#107a47] font-bold uppercase tracking-wider text-[10px]">✦ AI Suggestions</span>
                  <span id="boardAiModelBadge" class="px-2 py-0.5 rounded-full bg-[#ffffff] text-[#107a47] border border-[#107a47]/50 text-[10px] font-semibold">Free Model · $0</span>
                  <div id="boardAiSuggestionChips" class="flex flex-wrap items-center gap-1.5">
                    <button type="button" onclick="applyBoardAiSuggestion('#graphrag')" class="px-2 py-0.5 rounded-full bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border border-[#111111]/40 text-[10px] transition">[#graphrag]</button>
                    <button type="button" onclick="applyBoardAiSuggestion('@gemini-brain')" class="px-2 py-0.5 rounded-full bg-[#ffffff] hover:bg-[#107a47] hover:text-[#ffffff] text-[#107a47] border border-[#107a47]/60 text-[10px] font-semibold transition">[@gemini-brain]</button>
                    <button type="button" onclick="applyBoardAiSuggestion('/search bm25')" class="px-2 py-0.5 rounded-full bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border border-[#111111]/40 text-[10px] transition">[/search bm25]</button>
                    <button type="button" onclick="applyBoardAiSuggestion('/thread ')" class="px-2 py-0.5 rounded-full bg-[#107a47] hover:bg-[#111111] text-[#ffffff] border border-[#107a47] text-[10px] font-semibold transition">[/thread + New]</button>
                  </div>
                </div>
                <div class="flex items-center gap-1.5 text-[10px] text-[#4a4a4a] shrink-0">
                  <span class="hidden sm:inline">Slash: <code>/search</code> <code>/post</code> <code>/thread</code> <code>/feed</code></span>
                  <button type="button" onclick="loadBoardAiSuggestions(true)" class="px-2.5 py-0.5 rounded-full bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border border-[#111111] text-[10px] font-semibold transition">↻ Suggest</button>
                </div>
              </div>
            </div>

            <div id="boardSuggestList" role="listbox" class="ubar-suggest hidden" style="top: 3.35rem;"></div>
            <div class="ubar-meta">
              <div id="boardTrending" class="ubar-trending" aria-label="Trending topics"></div>
              <details id="boardRankDetails" class="ubar-rank">
                <summary>how this ranked</summary>
                <div id="boardRankBody" class="ubar-rank-body">Search with words or an @mention to see how hybrid BM25 + GraphRAG ranked the results.</div>
              </details>
            </div>

            <!-- Inline GraphRAG + BM25 Search Synthesis Box -->
            <div id="boardSynthesisBox" class="hidden p-2.5 bg-[#f4f8f0] border border-[#107a47] rounded-xl space-y-2 font-mono text-[11px] text-[#111111]">
              <div class="flex items-center justify-between">
                <span class="text-[10px] uppercase tracking-wider text-[#107a47] font-bold">🧠 Hybrid GraphRAG + Okapi BM25 Synthesis</span>
                <button type="button" onclick="openBoardRankDetails()" class="text-[10px] text-[#111111] underline hover:text-[#107a47]">how this ranked</button>
              </div>
              <div id="boardSynthesisText" class="text-[#111111] leading-relaxed"></div>
              <div id="boardSubgraphEntities" class="flex flex-wrap gap-1.5 pt-1"></div>
            </div>
          </div>

          <!-- Topics Feed & Active Thread View -->
          <div id="boardTopicsFeed" class="space-y-3"></div>
        </div>

        <!-- =============================================================== -->
        <!-- TAB 3: INTERACTIVE KNOWLEDGE GRAPH EXPLORER & PATH FINDER -->
        <!-- =============================================================== -->
        <div id="boardTab-graph" class="hidden space-y-3.5 font-mono">
          <div class="p-3.5 bg-[#ffffff] rounded-2xl border border-[#111111] space-y-3 text-[#111111]">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h3 class="text-xs font-bold text-[#111111] uppercase tracking-wider">🕸️ Cyberspace Multi-Relational Knowledge Graph</h3>
                <p class="text-[11px] text-[#4a4a4a] font-sans">Multi-entity semantic topology linking posts, authors, and AI agents.</p>
              </div>
              <div class="flex flex-wrap items-center gap-1.5 text-[10px]">
                <span class="px-2 py-0.5 rounded-full bg-[#f4f8f0] text-[#111111] border border-[#111111]/40">● Topic</span>
                <span class="px-2 py-0.5 rounded-full bg-[#f4f8f0] text-[#107a47] border border-[#107a47]">● @User</span>
                <span class="px-2 py-0.5 rounded-full bg-[#f4f8f0] text-[#111111] border border-[#111111]/60">● @Agent</span>
                <span class="px-2 py-0.5 rounded-full bg-[#f4f8f0] text-[#4a4a4a] border border-[#111111]/30">● #Tag</span>
                <button type="button" onclick="loadAndDrawBoardGraph()" class="px-2.5 py-0.5 rounded-full bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border border-[#111111] font-semibold transition">⟳ Re-Layout</button>
              </div>
            </div>

            <!-- Knowledge Graph Architecture Explanation & Collapsible Toggle -->
            <div class="p-3 bg-[#f4f8f0] border border-[#111111]/40 rounded-xl space-y-1.5 font-sans">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <span class="text-base">💡</span>
                  <span class="text-xs font-bold text-[#111111] font-mono">What is the Cyberspace Knowledge Graph showing?</span>
                </div>
                <button type="button" onclick="toggleKnowledgeGraphView()" class="px-2.5 py-0.5 rounded-full bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] font-mono text-[10px] border border-[#111111] transition">
                  <span id="kgToggleText">👁️ Hide Canvas</span>
                </button>
              </div>
              <p class="text-[11px] text-[#4a4a4a] leading-relaxed">
                The Cyberspace Knowledge Graph visualizes multi-relational connections between discussion topics, registered operators (<code class="text-[#107a47] font-semibold">@users</code>), AI models (<code class="text-[#111111] font-semibold">@agents</code>), and topical hashtags (<code class="text-[#111111] font-semibold">#tags</code>). Edges represent cryptographic co-authoring, thread citations, and semantic co-occurrence. GraphRAG uses this topology to execute Personalized PageRank ($\alpha=0.85$), enabling AI agents to synthesize cross-topic answers without keyword hallucination.
              </p>
            </div>

            <!-- Canvas & Path Container (Collapsible) -->
            <div id="boardGraphCanvasContainer" class="space-y-3">
              <!-- Shortest-Path Entity Finder -->
              <div class="p-2.5 bg-[#f4f8f0] rounded-xl border border-[#111111]/40 flex flex-col sm:flex-row items-stretch sm:items-center gap-2 text-xs">
                <span class="text-[#4a4a4a] text-[11px] shrink-0 font-semibold">Shortest Path:</span>
                <input id="graphPathSource" type="text" value="@alejandro" placeholder="From (e.g. @alejandro, #bm25)" class="px-2.5 py-1 rounded-lg bg-[#ffffff] border border-[#111111] text-[#111111] text-xs flex-1" />
                <span class="text-[#4a4a4a] text-center">⟶</span>
                <input id="graphPathTarget" type="text" value="@verifier-agent" placeholder="To (e.g. @verifier-agent, #graphrag)" class="px-2.5 py-1 rounded-lg bg-[#ffffff] border border-[#111111] text-[#111111] text-xs flex-1" />
                <button type="button" onclick="findCyberspaceEntityPath()" class="px-3 py-1 rounded-full bg-[#111111] hover:bg-[#107a47] text-[#ecf1e6] font-bold text-xs shrink-0 transition">
                  Find Relational Path
                </button>
              </div>
              <div id="graphPathOutput" class="hidden p-2.5 bg-[#107a47]/10 border border-[#107a47] rounded-xl text-[11px] text-[#111111]"></div>

              <!-- Interactive HTML5 Canvas -->
              <div class="relative bg-[#f4f8f0] rounded-xl border border-[#111111] overflow-hidden">
                <canvas id="boardGraphCanvas" width="860" height="380" class="w-full h-[380px] cursor-grab active:cursor-grabbing"></canvas>
                <div id="boardGraphNodeInspector" class="absolute bottom-2 left-2 right-2 p-2 bg-[#ffffff]/95 border border-[#111111] rounded-lg text-[10px] text-[#111111] flex items-center justify-between gap-2">
                  <span>Click any node on the graph canvas to inspect its connections and filter topics.</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- =============================================================== -->
        <!-- TAB 4: @VERIFIER-AGENT IDENTITY VERIFICATION CENTER & FORM -->
        <!-- =============================================================== -->
        <div id="boardTab-verify" class="hidden space-y-4 font-mono">
          <!-- Step 1: @verifier-agent Dispatch Console -->
          <div class="p-3.5 bg-[#f4f8f0] rounded-2xl border border-[#111111] space-y-2.5 text-[#111111]">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h3 class="text-xs font-bold text-[#111111] uppercase tracking-wider flex items-center gap-1.5">
                  <span>🛡️</span> <span>@verifier-agent Automated Form Dispatcher</span>
                </h3>
                <p class="text-[11px] text-[#4a4a4a] font-sans">
                  Have <code class="text-[#107a47] font-semibold">@verifier-agent</code> send a cryptographic verification form + challenge code (<code class="text-[#111111] font-semibold">CYBER-XXXXXX</code>) to yourself or any unverified peer in the mesh.
                </p>
              </div>
              <span class="px-2.5 py-0.5 rounded-full bg-[#ffffff] text-[#107a47] border border-[#107a47] text-[10px] font-bold">Ed25519 + SHA-256 Attestation</span>
            </div>
            <div class="flex flex-col sm:flex-row gap-2">
              <input id="verifyDispatchTargetUser" type="text" placeholder="Target @username or peer_id (leave blank to send to yourself)" class="flex-1 px-3 py-1.5 rounded-lg bg-[#ffffff] border border-[#111111] text-[#111111] text-xs" />
              <input id="verifyDispatchReason" type="text" value="Cyberspace Discussion Board Identity Verification" placeholder="Reason for verification" class="flex-1 px-3 py-1.5 rounded-lg bg-[#ffffff] border border-[#111111] text-[#4a4a4a] text-xs" />
              <button type="button" onclick="dispatchVerifierAgentFormFromCenter()" class="px-4 py-1.5 rounded-full bg-[#111111] hover:bg-[#107a47] text-[#ecf1e6] font-bold text-xs transition active:scale-95 shrink-0">
                📨 Dispatch Form via @verifier-agent
              </button>
            </div>
            <div id="verifyDispatchFeedback" class="hidden p-2.5 rounded-xl bg-[#107a47]/10 border border-[#107a47] text-[#111111] text-[11px]"></div>
          </div>

          <!-- Step 2: Dedicated Cyberspace Identity Verification Form -->
          <div class="p-4 bg-[#ffffff] rounded-2xl border border-[#111111] space-y-3 text-[#111111]">
            <div class="flex items-center justify-between border-b border-[#111111]/15 pb-2">
              <div>
                <h3 class="text-sm font-bold text-[#111111] flex items-center gap-2">
                  <span>✍️</span> <span>Official Cyberspace Identity Verification Form</span>
                </h3>
                <p class="text-[11px] text-[#4a4a4a] font-sans">Fill out and submit this form to <code class="text-[#107a47] font-semibold">@verifier-agent</code> to receive your <code class="text-[#107a47] font-semibold">✅ Verified Cyberspace Citizen</code> badge and SHA-256 attestation hash.</p>
              </div>
              <span id="verifyFormRequestIdBadge" class="px-2.5 py-0.5 rounded-full bg-[#f4f8f0] text-[#107a47] border border-[#107a47] text-[10px] font-semibold">Ready</span>
            </div>

            <input type="hidden" id="verifyFormRequestId" value="" />

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div>
                <label class="block text-[10px] text-[#4a4a4a] font-semibold mb-1">Full Legal / Real Name *</label>
                <input id="verifyFormFullName" type="text" placeholder="e.g. Alejandro Londono" class="w-full px-3 py-1.5 rounded-lg bg-[#ffffff] border border-[#111111] text-[#111111] focus:border-[#107a47] focus:outline-none" />
              </div>
              <div>
                <label class="block text-[10px] text-[#4a4a4a] font-semibold mb-1">Cyberspace @username Handle *</label>
                <input id="verifyFormUsername" type="text" placeholder="e.g. alejandro" class="w-full px-3 py-1.5 rounded-lg bg-[#ffffff] border border-[#111111] text-[#111111] focus:border-[#107a47] focus:outline-none" />
              </div>
              <div>
                <label class="block text-[10px] text-[#4a4a4a] font-semibold mb-1">Verified Contact Email *</label>
                <input id="verifyFormEmail" type="email" placeholder="e.g. operator@fau.edu" class="w-full px-3 py-1.5 rounded-lg bg-[#ffffff] border border-[#111111] text-[#111111] focus:border-[#107a47] focus:outline-none" />
              </div>
              <div>
                <label class="block text-[10px] text-[#4a4a4a] font-semibold mb-1">2FA Contact Phone Number *</label>
                <input id="verifyFormPhone" type="tel" placeholder="e.g. +15615550199" class="w-full px-3 py-1.5 rounded-lg bg-[#ffffff] border border-[#111111] text-[#111111] focus:border-[#107a47] focus:outline-none" />
              </div>
              <div>
                <label class="block text-[10px] text-[#4a4a4a] font-semibold mb-1">Role / Institution / Affiliation</label>
                <input id="verifyFormRole" type="text" value="Graduate Researcher / Mesh Engineer" class="w-full px-3 py-1.5 rounded-lg bg-[#ffffff] border border-[#111111] text-[#107a47] focus:border-[#107a47] focus:outline-none" />
              </div>
              <div>
                <label class="block text-[10px] text-[#4a4a4a] font-semibold mb-1">@verifier-agent Challenge Code</label>
                <input id="verifyFormChallengeCode" type="text" placeholder="e.g. CYBER-A1B2C3 (auto-filled on dispatch)" class="w-full px-3 py-1.5 rounded-lg bg-[#ffffff] border border-[#111111] text-[#111111] focus:border-[#107a47] focus:outline-none" />
              </div>
            </div>

            <div>
              <label class="block text-[10px] text-[#4a4a4a] font-semibold mb-1">Cyberspace Bio &amp; Knowledge Domains (Indexed in GraphRAG)</label>
              <textarea id="verifyFormBio" rows="2" placeholder="e.g. Building federated GraphRAG + BM25 knowledge bases, WebRTC mesh systems, and autonomous agents." class="w-full px-3 py-1.5 rounded-lg bg-[#ffffff] border border-[#111111] text-[#111111] text-xs focus:border-[#107a47] focus:outline-none"></textarea>
            </div>

            <label class="flex items-start gap-2 text-[11px] text-[#4a4a4a] font-sans cursor-pointer">
              <input id="verifyFormConsent" type="checkbox" checked class="mt-0.5 rounded border-[#111111] bg-[#ffffff]" />
              <span>I attest that this identity information is accurate and consent to cryptographic SHA-256 identity attestation by <code class="text-[#107a47] font-semibold">@verifier-agent</code> for the TinCan Cyberspace Knowledge Base.</span>
            </label>

            <div id="verifyFormStatusMsg" class="hidden p-2.5 rounded-xl text-xs"></div>

            <div class="flex items-center justify-end gap-2 pt-1">
              <button type="button" onclick="submitCyberspaceVerificationForm()" class="px-5 py-2 rounded-full bg-[#111111] hover:bg-[#107a47] text-[#ecf1e6] font-bold text-xs transition active:scale-95">
                ✅ Submit Verification Form &amp; Claim Citizen Badge
              </button>
            </div>
          </div>

          <!-- Step 3: Live Pending Requests & Verified Citizens Ledger -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div class="p-3 bg-[#ffffff] rounded-2xl border border-[#111111] space-y-2 text-[#111111]">
              <div class="flex items-center justify-between border-b border-[#111111]/15 pb-1.5">
                <span class="text-xs font-bold text-[#111111]">📨 Pending @verifier-agent Forms</span>
                <button type="button" onclick="loadVerificationCenterData()" class="text-[10px] text-[#4a4a4a] hover:text-[#111111] font-semibold">🔄 Refresh</button>
              </div>
              <div id="verifyPendingList" class="space-y-1.5 text-[11px] max-h-48 overflow-y-auto"></div>
            </div>

            <div class="p-3 bg-[#ffffff] rounded-2xl border border-[#111111] space-y-2 text-[#111111]">
              <div class="flex items-center justify-between border-b border-[#111111]/15 pb-1.5">
                <span class="text-xs font-bold text-[#107a47]">🏛️ Verified Cyberspace Citizens</span>
                <span id="verifyCitizensCount" class="text-[10px] text-[#5c5c5c]">0 verified</span>
              </div>
              <div id="verifyCitizensList" class="space-y-1.5 text-[11px] max-h-48 overflow-y-auto"></div>
            </div>
          </div>
        </div>

        <!-- =============================================================== -->
        <!-- TAB 5: CURATED FEED & DISCORD-STYLE ACTIVE THREADS (ACTIVITY)   -->
        <!-- =============================================================== -->
        <div id="boardTab-feed" class="hidden space-y-3 font-mono">
          <div class="flex flex-wrap items-center justify-between gap-2 p-2.5 bg-[#ffffff] rounded-2xl border border-[#111111]">
            <div class="flex flex-wrap items-center gap-1.5">
              <button id="boardFeedFilter-all" type="button" onclick="setBoardFeedFilter('all')" class="px-3 py-1 rounded-full bg-[#111111] text-[#ecf1e6] border border-[#111111] font-bold text-[11px] transition">All (0)</button>
              <button id="boardFeedFilter-curated" type="button" onclick="setBoardFeedFilter('curated')" class="px-3 py-1 rounded-full bg-[#f4f8f0] hover:bg-[#ecf1e6] text-[#111111] border border-[#111111]/40 text-[11px] transition">★ Curated (0)</button>
              <button id="boardFeedFilter-solved" type="button" onclick="setBoardFeedFilter('solved')" class="px-3 py-1 rounded-full bg-[#f4f8f0] hover:bg-[#ecf1e6] text-[#107a47] border border-[#107a47]/50 text-[11px] transition">✓ Solved (0)</button>
            </div>
            <div class="flex items-center gap-2 flex-1 min-w-[200px] max-w-md">
              <input id="boardFeedFilterInput" type="text" placeholder="Search curated feed or filter threads..." oninput="loadBoardFeedAndThreads()" onkeydown="if(event.key==='Enter')loadBoardFeedAndThreads()" class="flex-1 px-2.5 py-1 rounded-lg bg-[#f4f8f0] border border-[#111111] text-[#111111] text-xs focus:border-[#107a47] focus:outline-none" />
              <button type="button" onclick="loadBoardFeedAndThreads()" class="px-3 py-1 rounded-full bg-[#111111] hover:bg-[#107a47] text-[#ecf1e6] font-semibold text-[11px] transition">Filter</button>
            </div>
          </div>
          <div class="grid grid-cols-1 lg:grid-cols-12 gap-3">
            <div class="lg:col-span-7 bg-[#ffffff] rounded-2xl border border-[#111111] p-3.5 space-y-2.5 text-[#111111]">
              <div class="flex items-center justify-between border-b border-[#111111]/15 pb-1.5">
                <span class="text-[11px] font-bold uppercase tracking-wider text-[#111111]">📰 Curated Feed · All Topics</span>
                <span id="boardFeedStatusMeta" class="text-[10px] text-[#5c5c5c]">All topics</span>
              </div>
              <div id="boardCuratedFeedList" class="space-y-2.5 max-h-[430px] overflow-y-auto pr-1"></div>
            </div>
            <div class="lg:col-span-5 bg-[#ffffff] rounded-2xl border border-[#111111] p-3.5 space-y-2.5 text-[#111111]">
              <div class="flex items-center justify-between border-b border-[#111111]/15 pb-1.5">
                <span class="text-[11px] font-bold uppercase tracking-wider text-[#111111]">🧵 Active Threads · Ranked by Activity</span>
                <button type="button" onclick="promptNewBoardThread()" class="px-2.5 py-0.5 rounded-full bg-[#111111] hover:bg-[#107a47] text-[#ecf1e6] font-bold text-[10px] transition">+ New Thread</button>
              </div>
              <div id="boardActiveThreadsList" class="space-y-2.5 max-h-[430px] overflow-y-auto pr-1"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- Window 9: Network Presence, Peers & Leaderboard.app -->
    <!-- ===================================================================== -->
    <div id="win-network" class="mesh-window w-[560px] max-w-full" data-zen-window="true" data-window-id="win-network" style="top: 72px; right: 24px; z-index: 28;">
      <!--TC_TITLEBAR {"id": "win-network", "icon": "👥", "title": "Network Presence & Leaderboard", "meta_html": "<span id=\"netWinActiveBadge\"><span id=\"netWinActiveNum\">0</span> online</span>"}-->
      <div class="window-body p-4 space-y-4 max-h-[680px] overflow-y-auto">
        <!-- Unified Stat-Tab Bar (merges statistical cards + navigation tabs) -->
        <div class="grid grid-cols-3 gap-2 font-mono text-center">
          <button onclick="switchNetTab('peers')" id="btnNetTab-peers" class="p-2.5 rounded-lg bg-emerald-950/90 text-emerald-300 border border-emerald-600 font-bold text-center transition active:scale-95">
            <div class="text-sm font-bold flex items-center justify-center gap-1.5">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span id="netMetricPeers">0</span>
            </div>
            <div class="text-[10px] mt-0.5">🟢 Mesh Peers</div>
          </button>
          <button onclick="switchNetTab('visitors')" id="btnNetTab-visitors" class="p-2.5 rounded-lg bg-slate-950/90 text-slate-300 border border-slate-800 hover:border-slate-700 text-center transition active:scale-95">
            <div class="text-sm font-bold text-cyan-400" id="netMetricVisitors">0</div>
            <div class="text-[10px] text-slate-400 mt-0.5">🌐 Web Visitors</div>
          </button>
          <button onclick="switchNetTab('leaderboard')" id="btnNetTab-leaderboard" class="p-2.5 rounded-lg bg-slate-950/90 text-slate-300 border border-slate-800 hover:border-slate-700 text-center transition active:scale-95">
            <div class="text-sm font-bold text-amber-400" id="netMetricTopXp">0 XP</div>
            <div class="text-[10px] text-slate-400 mt-0.5">🏆 Leaderboard</div>
          </button>
        </div>

        <!-- Inline Direct Message Drawer (for pinging/messaging Mesh Peers & Web Visitors) -->
        <div id="netMessageDrawer" class="hidden p-3 bg-slate-950/95 border border-cyan-700/70 rounded-lg space-y-2 font-mono text-xs">
          <div class="flex items-center justify-between">
            <span class="text-cyan-300 font-bold">✉️ Direct Message → <span id="netMsgTargetLabel">Peer</span></span>
            <button onclick="closePeerMessage()" class="text-slate-400 hover:text-white text-[11px]">✕ Cancel</button>
          </div>
          <div class="flex items-center gap-2">
            <input id="netMsgInput" type="text" placeholder="Type message for this peer..." onkeydown="if(event.key==='Enter')sendDirectPeerMessage()" class="flex-1 bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-white text-xs focus:border-cyan-500 focus:outline-none">
            <button onclick="sendDirectPeerMessage()" class="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white font-bold rounded text-xs transition active:scale-95">Send</button>
          </div>
        </div>

        <!-- Tab 1: Mesh Peers List -->
        <div id="netPanel-peers" class="space-y-2">
          <div class="text-[11px] text-slate-400 font-mono flex items-center justify-between">
            <span>Connected Mesh Peers (Live Online Heartbeat)</span>
            <span class="text-emerald-400 font-bold">● Real Telemetry</span>
          </div>
          <div id="netPeersList" class="space-y-2 font-mono">
            <!-- Dynamically populated via pollMeshState -->
          </div>
        </div>

        <!-- Tab 2: Web Visitors & Live Cursors -->
        <div id="netPanel-visitors" class="space-y-2 hidden">
          <div class="text-[11px] text-slate-400 font-mono flex items-center justify-between">
            <span>Active Web Visitors &amp; Live Cursors (Ping &amp; Message)</span>
            <span class="text-cyan-400 font-bold">● Real-time Sync</span>
          </div>
          <div id="netVisitorsList" class="space-y-1.5 font-mono text-xs max-h-72 overflow-y-auto">
            <!-- Dynamically populated via pollMeshState -->
          </div>
        </div>

        <!-- Tab 3: Operator Leaderboard -->
        <div id="netPanel-leaderboard" class="space-y-2 hidden">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono flex items-center gap-1.5">
              <span>🏆</span> Live Operator Leaderboard
            </span>
            <span class="text-[10px] font-mono text-slate-400">Ranked by Lifetime XP</span>
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
              <tbody id="operatorLeaderboardStandalone" class="divide-y divide-slate-800/60">
                <!-- Dynamically updated -->
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- Window 9: 📁 Mesh Finder & Filesystem (Ranger VFS).app -->
    <!-- ===================================================================== -->
    <div id="win-agentspace" class="mesh-window w-[980px] max-w-full hidden" data-zen-window="true" data-window-id="win-agentspace" style="top: 76px; left: 140px; z-index: 35;">
      <!--TC_TITLEBAR {"id": "win-agentspace", "icon": "📁", "title": "Workstation", "badge": "VFS · 3D"}-->
      <style>
        /* Space IDE: Celadon, VS Code layout (explorer | tabbed editor | bottom terminal | status bar) */
        #win-agentspace .ide { display: flex; flex-direction: column; flex: 1 1 auto; min-height: 320px; height: min(720px, calc(100vh - 150px)); overflow: hidden; padding: 0; background: #ecf1e6; color: #111111; font-family: "Inter", -apple-system, sans-serif; font-size: 12px; }
        #win-agentspace[data-resized="true"] .ide,
        #win-agentspace.maximized .ide,
        #win-agentspace.popout-fullscreen .ide { height: 100% !important; max-height: none !important; flex: 1 1 auto !important; }
        #win-agentspace .hidden:not(#rangerSplitter) { display: none !important; }
        #win-agentspace .ide-head { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 10px; padding: 6px 10px; border-bottom: 1px solid #111111; flex: 0 0 auto; }
        #win-agentspace .ide-group { display: inline-flex; align-items: center; gap: 6px; min-width: 0; }
        #win-agentspace .ide-spacer { flex: 1 1 auto; }
        #win-agentspace .ide-seg { display: inline-flex; border: 1px solid #111111; border-radius: 9999px; overflow: hidden; background: #ffffff; }
        #win-agentspace .ide-seg button { padding: 2px 10px; font-size: 11px; font-weight: 600; background: transparent; color: #111111; border: 0; cursor: pointer; white-space: nowrap; }
        #win-agentspace .ide-seg button:hover { background: rgba(17,17,17,0.08); }
        #win-agentspace .ide-seg button.is-active { background: #111111; color: #ecf1e6; }
        #win-agentspace .ide-btn { font-size: 11px; font-weight: 600; padding: 2px 10px; border: 1px solid #111111; border-radius: 9999px; background: transparent; color: #111111; cursor: pointer; white-space: nowrap; font-family: inherit; }
        #win-agentspace .ide-btn:hover { background: #111111; color: #ecf1e6; }
        #win-agentspace .ide-btn--solid { background: #111111; color: #ecf1e6; }
        #win-agentspace .ide-btn--solid:hover { opacity: 0.85; }
        #win-agentspace .ide-btn--sm { font-size: 10px; padding: 1px 8px; font-weight: 500; }
        #win-agentspace .ide-btn--danger { border-color: #8a1c1c; color: #8a1c1c; }
        #win-agentspace .ide-btn--danger:hover { background: #8a1c1c; color: #ecf1e6; }
        #win-agentspace .ide-owner { width: 150px; font: 11px "JetBrains Mono", monospace; padding: 2px 8px; }
        #win-agentspace .ide-count { font: 10px "JetBrains Mono", monospace; padding: 1px 8px; border: 1px solid #111111; border-radius: 9999px; background: #ffffff; }
        #win-agentspace #finderTab-files { flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column; }
        #win-agentspace #finderTab-3dstudio { flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }
        #win-agentspace #finderTab-vscode:not(.hidden), #win-agentspace #finderTab-artcraft:not(.hidden) { flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column; overflow: auto; margin: 10px; }
        #win-agentspace #rangerSplit { flex: 1 1 auto; min-height: 0; display: flex; flex-direction: row; }
        #win-agentspace #rangerListPane { width: var(--ranger-list-w, 24%); min-width: 170px; flex: 0 0 auto; display: flex; flex-direction: column; min-height: 0; background: #f4f8f0; }
        #win-agentspace #rangerSplitter { width: 6px; flex: 0 0 auto; border-left: 1px solid #111111; }
        #win-agentspace #rangerViewerPane { flex: 1 1 0; min-width: 0; min-height: 0; display: flex; flex-direction: column; background: #ffffff; }
        #win-agentspace .ide-sec { display: flex; align-items: center; justify-content: space-between; gap: 6px; padding: 5px 8px; font-size: 10px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; border-bottom: 1px solid rgba(17,17,17,0.22); flex: 0 0 auto; }
        #win-agentspace .ide-files { flex: 1 1 auto; min-height: 60px; overflow-y: auto; font-family: "JetBrains Mono", monospace; font-size: 11px; }
        #win-agentspace .ide-hint { padding: 2px 8px; font: 9px "JetBrains Mono", monospace; color: #5c5c5c; text-align: center; flex: 0 0 auto; user-select: none; pointer-events: none; }
        #win-agentspace .ide-details { border-top: 1px solid rgba(17,17,17,0.22); flex: 0 0 auto; }
        #win-agentspace .ide-details > summary { cursor: pointer; padding: 5px 8px; font-size: 10px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; list-style: none; display: flex; align-items: center; justify-content: space-between; gap: 6px; }
        #win-agentspace .ide-details > summary::-webkit-details-marker { display: none; }
        #win-agentspace .ide-details > summary::before { content: "\25B8"; margin-right: 4px; }
        #win-agentspace .ide-details[open] > summary::before { content: "\25BE"; }
        #win-agentspace .ide-details > summary > span:first-child { flex: 1; min-width: 0; }
        #win-agentspace .ide-details-body { padding: 4px 8px 8px; min-height: 80px; max-height: 45vh; resize: vertical; overflow-y: auto; }
        #win-agentspace .ide-tabs { display: flex; align-items: stretch; overflow-x: auto; background: #f4f8f0; border-bottom: 1px solid #111111; flex: 0 0 auto; min-height: 30px; }
        #win-agentspace .ide-tabs-empty { padding: 6px 12px; font-size: 11px; color: #5c5c5c; }
        #win-agentspace .ide-tab { display: flex; align-items: center; gap: 6px; padding: 0 6px 0 12px; border-right: 1px solid rgba(17,17,17,0.22); font: 11px "JetBrains Mono", monospace; cursor: pointer; white-space: nowrap; color: #4a4a4a; border-top: 2px solid transparent; }
        #win-agentspace .ide-tab:hover { background: rgba(17,17,17,0.05); }
        #win-agentspace .ide-tab.is-active { background: #ffffff; color: #111111; border-top-color: #111111; font-weight: 600; margin-bottom: -1px; }
        #win-agentspace .ide-dirty { font-size: 9px; }
        #win-agentspace .ide-tab-x { border: 0; background: transparent; color: inherit; cursor: pointer; font-size: 14px; line-height: 1; padding: 0 4px; border-radius: 4px; }
        #win-agentspace .ide-tab-x:hover { background: #111111; color: #ecf1e6; }
        #win-agentspace .ide-toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 8px; padding: 4px 10px; border-bottom: 1px solid rgba(17,17,17,0.22); flex: 0 0 auto; background: #ffffff; }
        #win-agentspace .ide-path { font: 600 11px "JetBrains Mono", monospace; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        #win-agentspace .ide-meta { display: inline-flex; align-items: center; gap: 6px; font: 10px "JetBrains Mono", monospace; color: #5c5c5c; }
        #win-agentspace .ide-chip { padding: 0 7px; border: 1px solid #111111; border-radius: 9999px; font: 10px "JetBrains Mono", monospace; background: #ffffff; color: #111111; }
        #win-agentspace .ide-editor-body { flex: 1 1 auto; min-height: 0; position: relative; overflow: auto; }
        #win-agentspace .ide-media { min-height: 100%; display: flex; flex-direction: column; }
        #win-agentspace .ide-media > div:not(.hidden) { flex: 1 1 auto; }
        #win-agentspace .ide-code { display: flex; flex-direction: column; min-height: 120px; }
        #win-agentspace .ide-textarea { display: block; width: 100%; flex: 1 1 auto; min-height: 160px; resize: none; border: 0 !important; border-radius: 0 !important; outline: 0; padding: 8px 12px; background: #ffffff !important; color: #111111 !important; font: 12px/1.55 "JetBrains Mono", ui-monospace, monospace; tab-size: 2; }
        #win-agentspace #finderViewer { border: 0 !important; border-radius: 0 !important; background: #ffffff !important; font-family: "JetBrains Mono", monospace; }
        #win-agentspace #finderViewerContainer, #win-agentspace #finderViewerContainer > #finderViewer { min-height: 100%; }
        #win-agentspace .ide-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; gap: 4px; padding: 24px; color: #4a4a4a; min-height: 160px; }
        #win-agentspace .ide-empty-title { font-weight: 600; font-size: 13px; color: #111111; }
        #win-agentspace .ide-runbar { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 6px; padding: 4px 10px; border-top: 1px solid rgba(17,17,17,0.22); background: #f4f8f0; flex: 0 0 auto; font-size: 11px; }
        #win-agentspace .ide-runbar select { font-size: 11px; padding: 1px 6px; }
        #win-agentspace .ide-panel { flex: 0 0 auto; height: var(--ide-panel-h, 210px); display: flex; flex-direction: column; border-top: 1px solid #111111; background: #ffffff; min-height: 0; position: relative; }
        #win-agentspace .ide-panel.is-collapsed { height: auto; }
        #win-agentspace .ide-panel.is-collapsed .ide-panel-body, #win-agentspace .ide-panel.is-collapsed #idePanelHandle { display: none; }
        #win-agentspace #idePanelHandle { position: absolute; left: 0; right: 0; top: -4px; height: 8px; cursor: row-resize; z-index: 4; touch-action: none; display: flex; align-items: center; justify-content: center; }
        #win-agentspace #idePanelHandle::after { content: ""; width: 42px; height: 3px; border-radius: 9999px; background: rgba(17,17,17,0.28); transition: background 120ms ease, width 120ms ease; }
        #win-agentspace #idePanelHandle:hover::after { background: #111111; width: 64px; }
        #win-agentspace .ide-panel-head { display: flex; align-items: center; gap: 2px; padding: 0 6px; background: #f4f8f0; border-bottom: 1px solid rgba(17,17,17,0.22); flex: 0 0 auto; }
        #win-agentspace .ide-panel-tab { padding: 4px 10px; font-size: 10px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; background: transparent; border: 0; border-bottom: 2px solid transparent; cursor: pointer; color: #4a4a4a; }
        #win-agentspace .ide-panel-tab.is-active { color: #111111; border-bottom-color: #111111; }
        #win-agentspace .ide-panel-body { flex: 1 1 auto; min-height: 0; position: relative; }
        #win-agentspace .ide-panel-body > div { position: absolute; inset: 0; }
        #win-agentspace .ide-panel-body > div.hidden { display: none; }
        #win-agentspace #ideTermMount .tcsh { border: 0; border-radius: 0; }
        #win-agentspace .ide-output { margin: 0; padding: 8px 12px; height: 100%; overflow: auto; white-space: pre-wrap; font: 11px/1.5 "JetBrains Mono", monospace; color: #111111; background: #ffffff; }
        #win-agentspace .ide-status { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 14px; padding: 2px 10px; border-top: 1px solid #111111; background: #f4f8f0; font: 10px "JetBrains Mono", monospace; color: #262626; flex: 0 0 auto; }
        #win-agentspace .ide-status span { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 280px; }
        @media (max-width: 767px) {
          #win-agentspace #rangerSplit { flex-direction: column; }
          #win-agentspace #rangerListPane { width: 100% !important; max-height: 34%; }
          #win-agentspace .ide-owner { width: 110px; }
        }
      </style>
      <!-- Space is a VS Code style IDE: Explorer | tabbed editor | integrated terminal | status bar -->
      <div class="window-body ide aeonik-scope" data-ide="space">
        <!-- Header: scope switching, owner, load/export, and the other studio views -->
        <div class="ide-head">
          <div class="ide-group">
            <div class="ide-seg" role="group" aria-label="Space scope">
              <button id="scopeUserBtn" type="button" class="is-active" onclick="switchSpaceScope('user')" title="Your own space">User</button>
              <button id="scopeTopicBtn" type="button" onclick="switchSpaceScope('topic')" title="A forum topic space">Topic</button>
              <button id="scopeDynamicBtn" type="button" onclick="switchSpaceScope('dynamic')" title="A dynamic sandbox space">Sandbox</button>
            </div>
            <div class="relative inline-flex items-center">
              <input id="spaceOwnerInput" type="text" placeholder="Topic ID / Content IR Search or Owner ID" aria-label="Space owner or topic search" class="ide-owner" style="width: 215px;" onkeydown="onSpaceOwnerKeydown(event)" oninput="onSpaceOwnerInput(event)">
              <div id="spaceTopicSearchResults" class="hidden absolute left-0 top-full mt-1 w-[340px] max-w-[85vw] max-h-[240px] overflow-y-auto bg-white border border-black rounded-lg shadow-xl z-50 p-1 font-mono text-[11px] text-neutral-900"></div>
            </div>
            <button type="button" class="ide-btn" onclick="resolveAndLoadSpaceOwner()" title="Search Topic by ID or content (IR) and load .space">Load</button>
          </div>
          <span class="ide-spacer"></span>
          <div class="ide-group">
            <span id="spaceFileCountBadge" class="ide-count">0 Files</span>
            <button type="button" id="spaceToggleTerminalBtn" class="ide-btn" onclick="ideTogglePanel()" title="Dock/open or close the integrated Terminal drawer">&gt;_ Terminal</button>
            <button type="button" class="ide-btn" onclick="exportAgentSpace()" title="Download this space as a .space file">Export .space</button>
            <button type="button" class="ide-btn" id="spaceOpenWorkstationBtn" onclick="open3dStudioFromWorkstation()" title="Switch to 3D Studio (docked in Workstation or floating window)">3D Studio</button>
            <div class="ide-seg" role="group" aria-label="Studio views">
              <button id="finderTabBtn-files" type="button" class="is-active" onclick="switchFinderTab('files')">IDE</button>
              <button id="finderTabBtn-3dstudio" type="button" onclick="switchFinderTab('3dstudio')">3D Studio</button>
              <button id="finderTabBtn-vscode" type="button" onclick="switchFinderTab('vscode')">Extensions</button>
              <button id="finderTabBtn-artcraft" type="button" onclick="switchFinderTab('artcraft')">ArtCraft</button>
            </div>
          </div>
        </div>

        <!-- IDE view -->
        <div id="finderTab-files">
          <div id="rangerSplit">
            <!-- Explorer (the existing Ranger list, drive places and Rodin tool) -->
            <div id="rangerListPane" aria-label="Explorer">
              <div class="ide-sec">
                <span id="rangerListTitle" class="tc-truncate min-w-0 flex-1" title="Files in VFS">Files in VFS</span>
                <button id="rangerNewFileBtn" type="button" class="ide-btn ide-btn--sm shrink-0" onclick="promptCreateFile()" title="New file in this space">+ New</button>
              </div>
              <div id="rangerBreadcrumb" class="hidden flex flex-wrap items-center gap-0.5 px-2 py-1 font-mono text-[10px]"></div>
              <div id="spaceFileList" tabindex="0" role="listbox" aria-label="Files" class="ide-files divide-y divide-slate-800/40 focus:outline-none">
                <div class="text-slate-500 py-2 text-center text-xs">Loading .space VFS...</div>
              </div>
              <div class="ide-hint" aria-hidden="true">↑ ↓ ← → arrow keys to navigate</div>
              <details class="ide-details">
                <summary><span>Places · This Computer</span><button type="button" class="ide-btn ide-btn--sm" onclick="event.preventDefault(); event.stopPropagation(); gatherDriveMirror('manual')" title="Re-scan the drive now">&#8635;&#xFE0E; rescan</button></summary>
                <div class="ide-details-body">
                  <!-- Mirrors the real drive. Gathered fresh at login / session start, held in memory only, never saved. -->
                  <div id="drivePlacesList" class="space-y-0.5 font-mono text-xs max-h-[130px] overflow-y-auto">
                    <div class="text-slate-500 py-1 text-[10px]">Scanning your drive…</div>
                  </div>
                  <div id="drivePlacesStatus" class="text-[10px] font-mono leading-snug"></div>
                  <button id="drivePickBtn" type="button" onclick="pickBrowserFolder()" class="hidden w-full text-left px-2 py-1.5 font-mono text-xs transition hover:bg-slate-900">📂 Mirror a folder from this computer…</button>
                  <button type="button" onclick="showSpaceVfs()" class="w-full text-left px-2 py-1.5 hover:bg-slate-900 font-mono text-xs flex items-center gap-1.5 transition" title="Files you uploaded or imported into your TinCan .space"><span>🥫</span> <span>TinCan .space (uploads &amp; imports)</span></button>
                </div>
              </details>
              <details class="ide-details">
                <summary><span>Hyper3D Rodin 3D</span><span class="tc-chip shrink-0 font-mono">GEN-3D</span></summary>
                <div class="ide-details-body">
                  <!-- Rodin 3D Generative Mesh Tool -->
            <div class="p-2 space-y-2">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-1.5">
                  <span class="text-cyan-400">🧊</span>
                  <span class="font-bold text-cyan-300 font-mono text-xs">Hyper3D Rodin 3D</span>
                </div>
                <span class="tc-chip shrink-0 font-mono">GEN-3D</span>
              </div>
              <input id="rodinPromptInput" type="text" placeholder="e.g. Cyberpunk hovercar mesh" class="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1 text-white font-mono text-xs focus:border-cyan-500 focus:outline-none">
              <div class="grid grid-cols-2 gap-2 text-xs font-mono">
                <select id="rodinTierSelect" class="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-[11px]">
                  <option value="Regular">Regular ($0.50)</option>
                  <option value="Sketch">Sketch ($0.25)</option>
                  <option value="Detail">Detail ($1.00)</option>
                  <option value="Smooth">Smooth ($0.75)</option>
                </select>
                <select id="rodinFormatSelect" class="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-[11px]">
                  <option value="glb">GLB (Binary)</option>
                  <option value="fbx">FBX</option>
                  <option value="obj">OBJ</option>
                  <option value="usdz">USDZ</option>
                </select>
              </div>
              <button id="generateRodinBtn" onclick="generateAgentSpaceRodin3D()" class="w-full py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white font-mono text-xs font-semibold rounded-lg transition active:scale-95 flex items-center justify-center gap-1.5">
                <span>🧊</span> Generate 3D &amp; Save
              </button>
              <div id="rodinStatusNotice" class="text-[10px] font-mono text-slate-400 text-center truncate">Ready to generate 3D assets.</div>
            </div>

                </div>
              </details>
            </div>

            <!-- Draggable vertical divider (md+ only) -->
            <div id="rangerSplitter" role="separator" aria-orientation="vertical" aria-label="Resize explorer" tabindex="0"
                 class="hidden md:flex cursor-col-resize items-stretch justify-center group select-none" style="touch-action: none;">
              <div class="w-px my-0 bg-slate-800 transition"></div>
            </div>

            <!-- Editor group: open-file tabs, file toolbar, viewer/editor, run bar -->
            <div id="rangerViewerPane" aria-label="Editor">
              <div id="ideTabs" class="ide-tabs" role="tablist" aria-label="Open files"><span class="ide-tabs-empty">No file open</span></div>
              <div class="ide-toolbar">
                <span id="viewerFileIcon">📄</span>
                <span class="ide-path" id="activeFilePath" title="">/src/main.py</span>
                <span class="ide-meta">
                  <span id="viewerSourceBadge" class="ide-chip">.space</span>
                  <span id="activeFileMime">text/plain</span>
                  <span id="viewerFileSize"></span>
                  <span id="viewerFileMtime"></span>
                </span>
                <span class="ide-spacer"></span>
                <div id="viewerSpaceActions" class="inline-flex items-center gap-1">
                  <button id="viewerEditBtn" type="button" class="ide-btn ide-btn--sm" onclick="toggleViewerEdit()">✎ Edit</button>
                  <button type="button" class="ide-btn ide-btn--sm ide-btn--solid" onclick="saveAgentSpaceFile()" title="Save to .space (Cmd/Ctrl+S)">Save</button>
                  <button type="button" class="ide-btn ide-btn--sm ide-btn--danger" onclick="deleteAgentSpaceFile()" title="Delete from .space">Delete</button>
                </div>
                <div class="inline-flex flex-wrap items-center gap-1">
                  <button type="button" class="ide-btn ide-btn--sm" onclick="copyViewerPath()">Copy path</button>
                  <button type="button" class="ide-btn ide-btn--sm" onclick="downloadViewerFile()">Download</button>
                  <button id="viewerRawToggle" type="button" class="hidden ide-btn ide-btn--sm" onclick="toggleViewerRaw()">Raw</button>
                  <button id="viewerWrapToggle" type="button" class="ide-btn ide-btn--sm" onclick="toggleViewerWrap()">Wrap</button>
                  <a id="viewerVsCodeLink" href="#" class="hidden ide-btn ide-btn--sm no-underline" title="Opens the real file in VS Code on this computer (needs VS Code installed)">Open in VS Code ↗</a>
                </div>
              </div>
              <div id="ideEditorBody" class="ide-editor-body">
                <div id="finderMediaPreviewBox" class="ide-media">
                <div id="ideEmptyPane" class="ide-empty">
                  <div class="ide-empty-title">No file open</div>
                  <p>Pick a file in the Explorer, or press <b>+ New</b>. Edits save to your .space with <b>Save</b> or Cmd/Ctrl+S.</p>
                </div>
                
                <!-- Video Player Preview (for .mp4, .webm) -->
                <div id="finderVideoContainer" class="hidden relative bg-black rounded-lg overflow-hidden border border-slate-800 aspect-video flex items-center justify-center">
                  <video id="finderVideoPlayer" controls class="w-full h-full object-contain"></video>
                </div>

                <!-- Audio Player Preview (for .mp3, .wav) -->
                <div id="finderAudioContainer" class="hidden p-3 bg-slate-900 rounded-lg border border-slate-800 text-center space-y-2">
                  <div class="text-xs font-mono text-cyan-300">🎵 Audio Playback</div>
                  <audio id="finderAudioPlayer" controls class="w-full"></audio>
                </div>

                <!-- Image Preview -->
                <div id="finderImageContainer" class="hidden bg-slate-900 rounded-lg border border-slate-800 p-2 flex items-center justify-center" style="background-image: linear-gradient(45deg,#0f172a 25%,transparent 25%),linear-gradient(-45deg,#0f172a 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#0f172a 75%),linear-gradient(-45deg,transparent 75%,#0f172a 75%); background-size: 16px 16px;">
                  <img id="finderImagePreview" alt="" class="max-w-full max-h-full object-contain">
                </div>

                <!-- 3D GLB Model Preview (model-viewer loaded on demand) -->
                <div id="finder3dContainer" class="hidden relative bg-slate-900 rounded-lg overflow-hidden border border-cyan-700/60 min-h-[280px] flex-1 flex flex-col items-center justify-center text-center font-mono">
                  <div id="finder3dStage" class="absolute inset-0"></div>
                  <div id="finder3dFallback" class="relative p-3">
                    <span class="text-3xl mb-1">🧊</span>
                    <div class="text-xs font-bold text-cyan-300">3D Mesh Asset (.glb/.gltf)</div>
                    <p id="finder3dNote" class="text-[10px] text-slate-400 mt-1">Loading 3D preview…</p>
                  </div>
                  <div id="finder3dRigBar" class="absolute top-2 left-2 right-2 z-10 flex flex-wrap items-center justify-between gap-1.5 px-2 py-1.5 rounded bg-slate-950/85 border border-cyan-700/50 backdrop-blur-sm text-left">
                    <div class="flex flex-wrap items-center gap-1.5">
                      <select id="finder3dRigEngine" title="Auto-Rigging Model / Engine" class="bg-slate-900 border border-emerald-600/60 rounded px-1.5 py-0.5 text-[10px] text-emerald-200 font-semibold">
                        <option value="hyper3d/rigging">Neural: Hyper3D Rig ($0.20)</option>
                        <option value="meshy/rigging">Neural: Meshy Rig ($0.24)</option>
                        <option value="tripo3d/rig">Neural: Tripo3D Rig ($0.30)</option>
                        <option value="nanogpt">Neural: NanoGPT Auto ($0.20+)</option>
                        <option value="local">Local Heuristic ($0 Free)</option>
                      </select>
                      <select id="finder3dRigType" title="Skeleton Archetype" class="bg-slate-900 border border-slate-700 rounded px-1.5 py-0.5 text-[10px] text-slate-200">
                        <option value="auto">Auto Rig</option>
                        <option value="biped_creature">Biped Creature (Pikachu)</option>
                        <option value="quadruped">Quadruped (4-Leg)</option>
                        <option value="humanoid">Humanoid (Biped)</option>
                      </select>
                      <select id="finder3dAnimClip" title="Animation Clip to Synthesize" class="bg-slate-900 border border-slate-700 rounded px-1.5 py-0.5 text-[10px] text-slate-200">
                        <option value="walk">Walk Cycle</option>
                        <option value="run">Run Cycle</option>
                        <option value="idle">Idle Breath</option>
                        <option value="dance">Dance Loop</option>
                        <option value="all">All 4 Clips</option>
                      </select>
                      <button id="finder3dRigBtn" type="button" onclick="rigActiveSpaceGlb()" class="px-2 py-0.5 bg-emerald-600/90 hover:bg-emerald-500 text-white text-[10px] font-semibold rounded transition">
                        🦴 Rig &amp; Animate
                      </button>
                      <select id="finder3dAnimSelect" onchange="selectFinder3dAnimation(this.value)" title="Play embedded glTF animation clip" class="hidden bg-emerald-950/80 border border-emerald-600/60 rounded px-1.5 py-0.5 text-[10px] text-emerald-200"></select>
                    </div>
                    <span id="finder3dRigStatus" class="text-[10px] text-slate-300 truncate max-w-[240px]">NanoGPT neural models or $0 local rig</span>
                  </div>
                  <button onclick="launchArtCraftWasmApp('cadcraft')" class="absolute bottom-2 right-2 px-2 py-0.5 bg-cyan-700/80 hover:bg-cyan-600 text-white text-[10px] rounded transition">
                    Open in CadCraft Web ↗
                  </button>
                </div>

                <!-- PDF Document Preview -->
                <div id="finderPdfContainer" class="hidden relative bg-white rounded-lg overflow-hidden border border-slate-700 min-h-[380px] flex-1 flex flex-col">
                  <iframe id="finderPdfFrame" class="w-full h-full flex-1 border-0 bg-white" title="PDF Document Preview"></iframe>
                </div>

                <!-- HTML Live Web App Preview -->
                <div id="finderHtmlContainer" class="hidden relative bg-white rounded-lg overflow-hidden border border-emerald-700/50 min-h-[380px] flex-1 flex flex-col">
                  <div class="flex items-center justify-between gap-2 px-2.5 py-1.5 bg-slate-950 text-slate-200 border-b border-slate-800 text-[11px] font-mono">
                    <span id="finderHtmlUrlLabel" class="truncate text-emerald-300">HTML Live Preview</span>
                    <div class="flex items-center gap-1.5 shrink-0">
                      <button type="button" onclick="openCurrentHtmlInLocalhostBrowser()" class="px-2 py-0.5 bg-emerald-600 hover:bg-emerald-500 text-white text-[10px] font-semibold rounded transition">🌐 Open in Localhost Browser ↗</button>
                    </div>
                  </div>
                  <iframe id="finderHtmlFrame" class="w-full h-full flex-1 border-0 bg-white" title="HTML Web Preview"></iframe>
                </div>

                <!-- Universal Rich File / Data / Doc / Archive / Font / DXF / Hex Inspector -->
                <div id="finderRichContainer" class="hidden p-3 bg-slate-900 rounded-lg border border-slate-800 overflow-auto flex-1 font-mono text-xs text-slate-200 space-y-3"></div>

                <!-- Binary / too-large notice -->
                <div id="finderBinaryContainer" class="hidden p-4 bg-slate-900 rounded-lg border border-slate-800 text-center font-mono space-y-1">
                  <div class="text-2xl">📦</div>
                  <div id="finderBinaryText" class="text-xs text-slate-300">Binary file</div>
                  <div class="text-[10px] text-slate-500">Use ⬇ Download for raw binary transfer.</div>
                </div>

                <!-- Read-only viewer: highlighted code with line numbers, or rendered Markdown -->
                <div id="finderViewerContainer" class="hidden">
                  <div id="finderViewerNotice" class="hidden mb-1 px-2 py-1 rounded bg-amber-950/40 border border-amber-800/50 text-amber-300 font-mono text-[10px]"></div>
                  <div id="finderViewer" class="ranger-viewer overflow-auto bg-slate-900/90 border border-slate-800 rounded-lg text-xs select-text"></div>
                </div>

                <!-- Text/Code Editor (edit mode for .space files) -->
                <div id="finderCodeContainer" class="ide-code">
                  <textarea id="agentspaceEditor" rows="8" spellcheck="false" class="ide-textarea select-text" placeholder="Write Python, JS, or Wasm bytecode..."></textarea>
                </div>
              </div>

              </div>
              <div class="ide-runbar">
                <div class="inline-flex items-center gap-1.5">
                  <span>Sandbox</span>
                  <select id="playgroundRuntimeSelect">
                    <option value="auto">auto (detect)</option>
                    <option value="python">pyodide-wasm (Python)</option>
                    <option value="js">quickjs-wasm (JS)</option>
                    <option value="node">node (JS, server toolchain)</option>
                    <option value="rust">rustc (Rust)</option>
                    <option value="wasm">wasi-wasm (Bytecode)</option>
                    <option value="three-glb-viewer">three-glb-viewer (3D)</option>
                  </select>
                </div>
                <div class="inline-flex items-center gap-1.5">
                  <button type="button" class="ide-btn" onclick="ideShowPanel('output'); runAgentSpaceAgent()">🤖 Space Agent</button>
                  <button type="button" class="ide-btn ide-btn--solid" onclick="ideShowPanel('output'); runAgentSpacePlayground()">▶ Run Sandbox</button>
                </div>
              </div>
            </div>
          </div><!-- /#rangerSplit -->

          <!-- Integrated panel (collapsed by default so Workstation focuses on files/3D viewer; dockable on demand) -->
          <div id="idePanel" class="ide-panel is-collapsed">
            <div id="idePanelHandle" role="separator" aria-orientation="horizontal" aria-label="Resize panel" tabindex="0"></div>
            <div class="ide-panel-head">
              <button id="ideTab-terminal" type="button" class="ide-panel-tab is-active" onclick="ideShowPanel('terminal')">Terminal</button>
              <button id="ideTab-output" type="button" class="ide-panel-tab" onclick="ideShowPanel('output')">Output <span id="playgroundExitCode" class="font-mono font-normal normal-case tracking-normal">Exit: 0</span></button>
              <span class="ide-spacer"></span>
              <button type="button" class="ide-btn ide-btn--sm" onclick="toggleWindow('win-terminal')" title="Open standalone Terminal window">Float Terminal ↗</button>
              <button id="ideTogglePanelBtn" type="button" class="ide-btn ide-btn--sm" onclick="ideTogglePanel()" title="Show or hide the docked panel">Show ▴</button>
            </div>
            <div class="ide-panel-body">
              <div id="idePane-terminal"><div id="ideTermMount" data-tc-shell-mount data-shell-title="this space" style="height: 100%;"></div></div>
              <div id="idePane-output" class="hidden"><pre id="agentspaceOutput" class="ide-output select-text">Ready. Click 'Run Sandbox' to execute in isolated mini-environment.</pre></div>
            </div>
          </div>

          <!-- Status bar -->
          <div id="ideStatus" class="ide-status" role="status">
            <span id="ideStatSpace" title="Space owner">space</span>
            <span id="ideStatScope" title="Scope">user</span>
            <span id="ideStatFile" title="Open file">no file</span>
            <span id="ideStatLang" title="Language">–</span>
            <span class="ide-spacer"></span>
            <span id="ideStatMerkle" title="Merkle root of this .space">merkle –</span>
            <span id="ideStatDrive" title="Drive mirror">drive: off</span>
          </div>
        </div>

        <!-- =============================================================== -->
        <!-- TAB 2: VS CODE & OPEN VSX PLUGIN EXTENSIONS MARKETPLACE -->
        <!-- =============================================================== -->
        <div id="finderTab-vscode" class="hidden space-y-4 font-mono">
          <div class="p-3.5 bg-slate-900/90 rounded-xl border border-blue-500/40 space-y-3">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h3 class="text-xs font-bold text-blue-300 uppercase tracking-wider flex items-center gap-1.5">
                  <span>🧩</span> <span>VS Code &amp; Open VSX Extensions Repository Integration</span>
                </h3>
                <p class="text-[11px] text-slate-400 font-sans">Tap into the worldwide VS Code extension ecosystem. Install tools, formatters, and viewers to interact with VFS files and execute services.</p>
              </div>
              <span class="px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-700 text-[10px]">Open VSX Compatible</span>
            </div>

            <!-- Search Bar -->
            <div class="flex gap-2">
              <input id="vscodeExtensionSearchInput" type="text" placeholder="Search VS Code extensions (e.g. Python, Prettier, glTF, ESLint, Docker)..." class="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white placeholder:text-slate-600 focus:border-blue-500 focus:outline-none">
              <button onclick="searchVsCodeExtensions()" class="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg text-xs transition active:scale-95">
                Search Marketplace
              </button>
            </div>

            <!-- Featured Extensions Grid -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5 pt-1">
              <div class="p-2.5 bg-slate-950/80 rounded-lg border border-slate-800 flex flex-col justify-between space-y-2">
                <div class="flex items-start gap-2.5">
                  <span class="text-2xl">🐍</span>
                  <div class="flex-1 min-w-0">
                    <div class="font-bold text-xs text-white truncate">ms-python.python</div>
                    <div class="text-[10px] text-slate-400">Python Language Server, Pyodide Wasm Runner &amp; Linting</div>
                  </div>
                </div>
                <div class="flex items-center justify-between text-[10px] pt-1 border-t border-slate-800">
                  <span class="text-emerald-400">● Installed (VFS)</span>
                  <button onclick="launchPluginService('python')" class="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded">Run Service ➔</button>
                </div>
              </div>

              <div class="p-2.5 bg-slate-950/80 rounded-lg border border-slate-800 flex flex-col justify-between space-y-2">
                <div class="flex items-start gap-2.5">
                  <span class="text-2xl">🧊</span>
                  <div class="flex-1 min-w-0">
                    <div class="font-bold text-xs text-white truncate">cesium.gltf-tools</div>
                    <div class="text-[10px] text-slate-400">glTF &amp; GLB 3D Model Inspector, PBR Validator &amp; Mesh View</div>
                  </div>
                </div>
                <div class="flex items-center justify-between text-[10px] pt-1 border-t border-slate-800">
                  <span class="text-emerald-400">● Installed (VFS)</span>
                  <button onclick="launchPluginService('gltf')" class="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded">Run Service ➔</button>
                </div>
              </div>

              <div class="p-2.5 bg-slate-950/80 rounded-lg border border-slate-800 flex flex-col justify-between space-y-2">
                <div class="flex items-start gap-2.5">
                  <span class="text-2xl">✨</span>
                  <div class="flex-1 min-w-0">
                    <div class="font-bold text-xs text-white truncate">esbenp.prettier-vscode</div>
                    <div class="text-[10px] text-slate-400">Opinionated Code Formatter for JS, TS, HTML, CSS &amp; JSON</div>
                  </div>
                </div>
                <div class="flex items-center justify-between text-[10px] pt-1 border-t border-slate-800">
                  <span class="text-cyan-400">Ready</span>
                  <button onclick="installVsCodePlugin('prettier')" class="px-2 py-0.5 bg-blue-700 hover:bg-blue-600 text-white rounded">Install to VFS</button>
                </div>
              </div>

              <div class="p-2.5 bg-slate-950/80 rounded-lg border border-slate-800 flex flex-col justify-between space-y-2">
                <div class="flex items-start gap-2.5">
                  <span class="text-2xl">🎬</span>
                  <div class="flex-1 min-w-0">
                    <div class="font-bold text-xs text-white truncate">humao.media-previewer</div>
                    <div class="text-[10px] text-slate-400">High-Performance H.264 Video, WebM &amp; Audio Stream Inspector</div>
                  </div>
                </div>
                <div class="flex items-center justify-between text-[10px] pt-1 border-t border-slate-800">
                  <span class="text-emerald-400">● Installed (VFS)</span>
                  <button onclick="launchPluginService('media')" class="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded">Run Service ➔</button>
                </div>
              </div>

              <div class="p-2.5 bg-slate-950/80 rounded-lg border border-slate-800 flex flex-col justify-between space-y-2">
                <div class="flex items-start gap-2.5">
                  <span class="text-2xl">📄</span>
                  <div class="flex-1 min-w-0">
                    <div class="font-bold text-xs text-white truncate">shd101wyy.markdown-preview</div>
                    <div class="text-[10px] text-slate-400">Markdown Preview Enhanced with MathJax &amp; Mermaid Diagrams</div>
                  </div>
                </div>
                <div class="flex items-center justify-between text-[10px] pt-1 border-t border-slate-800">
                  <span class="text-cyan-400">Ready</span>
                  <button onclick="installVsCodePlugin('markdown')" class="px-2 py-0.5 bg-blue-700 hover:bg-blue-600 text-white rounded">Install to VFS</button>
                </div>
              </div>

              <div class="p-2.5 bg-slate-950/80 rounded-lg border border-slate-800 flex flex-col justify-between space-y-2">
                <div class="flex items-start gap-2.5">
                  <span class="text-2xl">🐳</span>
                  <div class="flex-1 min-w-0">
                    <div class="font-bold text-xs text-white truncate">ms-azuretools.vscode-docker</div>
                    <div class="text-[10px] text-slate-400">Sandboxed Container &amp; Isolated Process Task Runner</div>
                  </div>
                </div>
                <div class="flex items-center justify-between text-[10px] pt-1 border-t border-slate-800">
                  <span class="text-cyan-400">Ready</span>
                  <button onclick="installVsCodePlugin('docker')" class="px-2 py-0.5 bg-blue-700 hover:bg-blue-600 text-white rounded">Install to VFS</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- =============================================================== -->
        <!-- TAB 3: ARTCRAFT 15 WASM META-STUDIO SUITE -->
        <!-- =============================================================== -->
        <div id="finderTab-artcraft" class="hidden p-3 bg-gradient-to-r from-slate-900/90 via-purple-950/40 to-slate-900/90 rounded-xl border border-purple-500/30 space-y-3">
          <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              <span class="text-lg">🎨</span>
              <div>
                <span class="font-bold text-white font-mono text-xs">ArtCraft 15 Wasm Meta-Studio Suite</span>
                <span class="text-[10px] text-purple-300 font-mono block">Zero-Latency In-Browser WebAssembly Bridge (?host=parent)</span>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span id="artcraftStatusPill" class="px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 text-[10px] font-mono">STANDBY</span>
              <select id="artcraftAppSelect" class="bg-slate-950 border border-slate-700 rounded px-2.5 py-1 text-white font-mono text-xs">
                <option value="cadcraft">📐 CadCraft Web (3D CAD, DXF, STL)</option>
                <option value="vectorcraft">✒️ VectorCraft Web (SVG &amp; Vector)</option>
                <option value="deckcraft">📊 DeckCraft Web (Presentations &amp; Decks)</option>
                <option value="designcraft">📰 DesignCraft Web (Editorial &amp; Layout)</option>
                <option value="effectcraft">✨ EffectCraft Web (VFX &amp; Motion)</option>
                <option value="figcraft">🎨 FigCraft Web (UI/UX Components)</option>
                <option value="filmcraft">🎬 FilmCraft Web (Video Sequences)</option>
                <option value="gridcraft">📈 GridCraft Web (Spreadsheets &amp; Data)</option>
                <option value="lightcraft">💡 LightCraft Web (RAW &amp; Color Grade)</option>
                <option value="pdfcraft">📄 PdfCraft Web (PDF &amp; Forms)</option>
                <option value="photocraft">🖼️ PhotoCraft Web (Raster Imaging)</option>
                <option value="scriptcraft">📜 ScriptCraft Web (Screenplays)</option>
                <option value="soundcraft">🎵 SoundCraft Web (DAW &amp; Audio)</option>
                <option value="wordcraft">📝 WordCraft Web (Prose &amp; Markdown)</option>
                <option value="artcraft">🛸 ArtCraft Meta-Studio (Launcher)</option>
              </select>
              <button onclick="launchArtCraftWasmApp()" class="px-3 py-1 bg-gradient-to-r from-purple-600 to-indigo-600 hover:brightness-110 text-white font-mono text-xs font-bold rounded-lg transition active:scale-95 shadow-md">
                🎨 Launch in Wasm
              </button>
              <button onclick="openArtCraftOnPC()" class="px-3 py-1 bg-emerald-700 hover:bg-emerald-600 text-white font-mono text-xs font-bold rounded-lg transition active:scale-95 shadow-md" title="Open file in native PC Craft app via ArtCraft Launcher (getartcraft.com)">
                🖥️ Open on PC
              </button>
              <a href="https://getartcraft.com" target="_blank" rel="noopener" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-cyan-700/60 font-mono text-[11px] rounded-lg transition" title="Download ArtCraft Launcher for macOS, Windows, Linux &amp; FreeBSD">
                📦 getartcraft.com ↗
              </a>
            </div>
          </div>
          <!-- ArtCraft Iframe Container -->
          <div id="artcraftIframeWrapper" class="hidden relative w-full flex-1 min-h-[320px] bg-black rounded-lg border border-purple-500/40 overflow-hidden shadow-2xl" style="resize: vertical;">
            <iframe id="artcraftWasmFrame" src="about:blank" class="w-full h-full border-0"></iframe>
          </div>
        </div>

        <!-- =============================================================== -->
        <!-- TAB 4: MERGED 3D STUDIO HOST (mounts #win-workstation .ws-body)  -->
        <!-- =============================================================== -->
        <div id="finderTab-3dstudio" class="hidden tc-ws-host aeonik-scope">
          <div id="finder3dStudioPlaceholder" class="p-4 font-mono text-xs text-neutral-700">Initializing 3D Studio workspace...</div>
        </div>
      </div>
    </div>

    <!--TC_WORKSTATION_WINDOW-->

    <!--TC_BROWSER_WINDOW-->

    <!--TC_LOCALHOST_WINDOW-->

    <!--TC_NODES_WINDOW-->

    <!--TC_COPILOT_WINDOW-->

    <!-- Window 10: TinCan AI Command Shell & Hub (Aeonik Home Overlay Window) -->
    <div id="win-ai-home" class="mesh-window w-[1080px] max-w-[96vw] hidden" data-zen-window="true" data-window-id="win-ai-home" style="top: 64px; left: 72px; z-index: 21;">
      <!--TC_TITLEBAR {"id": "win-ai-home", "title": "TinCan AI · Terminal Home & AI Command Hub", "badge": "HOME · ROUTER"}-->
      <div class="window-body p-4 max-h-[780px] overflow-y-auto bg-[#ecf1e6]">
        <!--TC_AI_HOME_HUB-->
      </div>
    </div>

  </main>

  <!-- Bottom OS Dock -->
  <footer id="meshOsDock" class="fixed bottom-3 left-1/2 -translate-x-1/2 z-50 bg-slate-900/90 border border-slate-700/80 rounded-2xl px-3 py-2 flex items-center gap-1.5 sm:gap-2.5 backdrop-blur-md shadow-2xl select-none font-sans">
    <button id="dockBtn-win-terminal" onclick="toggleWindow('win-terminal')" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="Terminal & Quickstart">
      <span>⚡</span> <span class="hidden md:inline">Terminal</span>
    </button>
    <button id="dockBtn-win-tv" onclick="toggleWindow('win-tv')" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="Relay Watch Party TV (Ads &amp; Memes)">
      <span>📺</span> <span class="hidden md:inline">Watch Party TV</span>
    </button>
    <button id="dockBtn-win-board" onclick="toggleWindow('win-board')" class="px-2.5 py-1.5 bg-indigo-950/90 hover:bg-indigo-900 border border-indigo-500/80 text-indigo-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95 font-bold" title="Cyberspace Discussion Board · GraphRAG + BM25">
      <span>🌐</span> <span class="hidden md:inline">Cyberspace</span>
    </button>
    <button id="dockBtn-win-network" onclick="toggleWindow('win-network')" class="px-2.5 py-1.5 bg-emerald-950/90 hover:bg-emerald-900 border border-emerald-500/80 text-emerald-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95 font-bold" title="Active Network Roster, Live Visitors & Standalone Leaderboard">
      <span>👥</span> <span class="hidden md:inline">2 Active &amp; Ranks</span>
    </button>
    <button id="dockBtn-win-arena" onclick="toggleWindow('win-arena')" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="AI Brain Router & Arena">
      <span>🧠</span> <span class="hidden md:inline">AI Arena</span>
    </button>
    <button id="dockBtn-win-call" onclick="toggleWindow('win-call')" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="WebRTC Video &amp; Voice Studio">
      <span>📹</span> <span class="hidden md:inline">Video Studio</span>
    </button>
    <button id="dockBtn-win-comms" onclick="toggleWindow('win-comms')" class="px-2.5 py-1.5 bg-cyan-950 hover:bg-cyan-900 border border-cyan-800 text-cyan-300 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="Encrypted Mesh Chat &amp; Sealed Messaging">
      <span>💬</span> <span class="hidden md:inline font-bold">Mesh Chat</span>
    </button>
    <button id="dockBtn-chat" onclick="focusChatWindow()" class="hidden"></button>
    <button id="dockBtn-win-quests" onclick="toggleWindow('win-quests')" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="Rewards &amp; Token Minting Program">
      <span>🪙</span> <span class="hidden md:inline">Rewards &amp; Mint</span>
    </button>
    <button id="dockBtn-win-agentspace" onclick="toggleWindow('win-agentspace')" class="px-2.5 py-1.5 bg-slate-800/80 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="Workstation · User, Topic &amp; Sandbox VFS + 3D Studio">
      <span>📁</span> <span class="hidden md:inline">Workstation</span>
    </button>
    <button id="dockBtn-win-workstation" onclick="toggleWindow('win-workstation')" class="px-2.5 py-1.5 bg-slate-800/80 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="3D Studio · Multi-Model Foundry &amp; Hyper3D Rodin 3D">
      <span>🛠️</span> <span class="hidden md:inline">3D Studio</span>
    </button>
    <button id="dockBtn-win-browser" onclick="toggleWindow('win-browser')" class="px-2.5 py-1.5 bg-slate-800/80 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="TinCan Browser · Playwright Chromium &amp; Reader">
      <span>🧭</span> <span class="hidden md:inline">Browser</span>
    </button>
    <button id="dockBtn-win-localhost" onclick="toggleWindow('win-localhost')" class="px-2.5 py-1.5 bg-slate-800/80 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="Localhost &amp; .space Pages Browser (gh-pages + :port proxy)">
      <span>🌐</span> <span class="hidden md:inline">Localhost</span>
    </button>
    <button id="dockBtn-win-nodes" onclick="toggleWindow('win-nodes')" class="px-2.5 py-1.5 bg-slate-800/80 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="Aeonik Node Studio · Prompt Island, Timeline &amp; Filter Graph">
      <span>⬢</span> <span class="hidden md:inline">Node Studio</span>
    </button>
    <button id="dockBtn-win-ai-home" onclick="toggleWindow('win-ai-home')" class="px-2.5 py-1.5 bg-slate-800/80 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="TinCan AI Command Shell &amp; Workflow Hub">
      <span>⌘</span> <span class="hidden md:inline">AI Hub</span>
    </button>
    <button id="dockBtn-win-copilot" onclick="toggleWindow('win-copilot')" class="px-2.5 py-1.5 bg-slate-800/80 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="AI Copilot · Multi-Model Router &amp; Context Palace">
      <span>✦</span> <span class="hidden md:inline">AI Copilot</span>
    </button>
    <button id="dockBtn-win-billing" onclick="toggleWindow('win-billing')" class="px-2.5 py-1.5 bg-emerald-950/80 hover:bg-emerald-900 border border-emerald-600/80 text-emerald-300 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95 font-semibold" title="Ad Credits &amp; Token Vault (No Subscriptions)">
      <span>💳</span> <span class="hidden md:inline">Credits &amp; Ads</span>
    </button>
    <button id="dockModBtn" onclick="toggleWindow('win-moderator')" class="hidden px-2.5 py-1.5 bg-amber-950/80 hover:bg-amber-900 border border-amber-600 text-amber-300 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="Admin Moderator Control Panel">
      <span>🛡️</span> <span class="hidden md:inline font-bold">Mod Panel</span>
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
    const savedPeerId = localStorage.getItem('tincan_peer_id');
    const myPeerId = urlParams.get('peer') || savedPeerId || ('peer-' + Math.random().toString(36).substring(2, 8));
    localStorage.setItem('tincan_peer_id', myPeerId);
    const currentRoom = urlParams.get('room') || 'main';
    let singleWindowParam = urlParams.get('window');
    const instanceParam = urlParams.get('instance') || '';
    const isEmbedInstance = urlParams.get('embed') === '1';
    window.TINCAN_INSTANCE_ID = instanceParam;
    function scopedStorageKey(baseKey) {
      return instanceParam ? (baseKey + '::' + instanceParam) : baseKey;
    }
    function notifyParentInstanceTitle(subtitle) {
      if (!instanceParam || typeof window === 'undefined' || !window.parent || window.parent === window) return;
      try {
        window.parent.postMessage({ type: 'TC_INSTANCE_TITLE', instanceId: instanceParam, subtitle: String(subtitle || '') }, window.location.origin);
      } catch (e) {}
    }
    window.scopedStorageKey = scopedStorageKey;
    window.notifyParentInstanceTitle = notifyParentInstanceTitle;

    // Route alias normalization: support /tv, /call, or window=tv, window=call, etc.
    if (!singleWindowParam) {
      if (window.location.pathname === '/tv') singleWindowParam = 'win-tv';
      else if (window.location.pathname === '/call') singleWindowParam = 'win-call';
      else if (window.location.pathname === '/comms' || window.location.pathname === '/chat') singleWindowParam = 'win-comms';
      else if (window.location.pathname === '/arena') singleWindowParam = 'win-arena';
      else if (window.location.pathname === '/terminal') singleWindowParam = 'win-terminal';
      else if (window.location.pathname === '/billing' || window.location.pathname === '/tokens') singleWindowParam = 'win-billing';
      else if (window.location.pathname === '/board' || window.location.pathname === '/cyberspace') singleWindowParam = 'win-board';
      else if (['/space', '/files', '/finder', '/agentspace', '/workstation'].includes(window.location.pathname)) singleWindowParam = 'win-agentspace';
      else if (window.location.pathname === '/3dstudio') singleWindowParam = 'win-workstation';
      else if (window.location.pathname === '/browser') singleWindowParam = 'win-browser';
      else if (window.location.pathname === '/localhost') singleWindowParam = 'win-localhost';
      else if (window.location.pathname === '/copilot') singleWindowParam = 'win-copilot';
      else if (window.location.pathname === '/ai' || window.location.pathname === '/home') singleWindowParam = 'win-ai-home';
      else if (window.location.pathname === '/rewards' || window.location.pathname === '/quests') singleWindowParam = 'win-quests';
      else if (window.location.pathname === '/network') singleWindowParam = 'win-network';
      else if (window.location.pathname === '/nodes' || window.location.pathname.startsWith('/nodes/')) singleWindowParam = 'win-nodes';
    }
    if (singleWindowParam && !singleWindowParam.startsWith('win-')) {
      singleWindowParam = 'win-' + singleWindowParam;
    }

    if (document.getElementById('roomInput')) document.getElementById('roomInput').value = currentRoom;
    if (document.getElementById('localPeerLabel')) document.getElementById('localPeerLabel').innerText = myPeerId;

    // Admin Moderator State & Controls
    let isAdmin = (urlParams.get('role') === 'admin' || urlParams.get('admin') === 'true' || localStorage.getItem('tincan_admin') === 'true');

    function updateAdminUI() {
      const badge = document.getElementById('osAdminBadge');
      const modBtn = document.getElementById('osModPanelBtn');
      const dockBtn = document.getElementById('dockModBtn');
      const toggleText = document.getElementById('osAdminToggleText');
      const toggleBtn = document.getElementById('osAdminToggleBtn');
      const adminMintCard = document.getElementById('questsAdminMintCard');
      if (isAdmin) {
        if (badge) badge.classList.remove('hidden');
        if (modBtn) modBtn.classList.remove('hidden');
        if (dockBtn && !(typeof poppedOutWindows !== 'undefined' && poppedOutWindows.has('win-moderator'))) {
          dockBtn.classList.remove('hidden');
          dockBtn.style.display = '';
        }
        if (adminMintCard) adminMintCard.classList.remove('hidden');
        if (toggleText) toggleText.innerText = 'Admin: ACTIVE 🛡️';
        if (toggleBtn) {
          toggleBtn.className = 'text-xs font-mono px-2.5 py-1 rounded border border-amber-500 bg-amber-950 text-amber-300 transition flex items-center gap-1.5 shadow-sm font-bold';
        }
      } else {
        if (badge) badge.classList.add('hidden');
        if (modBtn) modBtn.classList.add('hidden');
        if (dockBtn) dockBtn.classList.add('hidden');
        if (adminMintCard) adminMintCard.classList.add('hidden');
        if (toggleText) toggleText.innerText = 'Admin Mode';
        if (toggleBtn) {
          toggleBtn.className = 'text-xs font-mono px-2.5 py-1 rounded border border-slate-700 bg-slate-900 text-slate-300 hover:text-amber-400 hover:border-amber-600 transition flex items-center gap-1.5 shadow-sm font-semibold';
        }
      }
    }

    function toggleAdminMode() {
      isAdmin = !isAdmin;
      localStorage.setItem('tincan_admin', isAdmin ? 'true' : 'false');
      updateAdminUI();
      if (isAdmin) {
        toggleWindow('win-moderator');
        playXpChime();
      }
    }

    async function kickPeerNode(peerId, room = 'main') {
      if (!confirm(`Are you sure you want to disconnect / kick '${peerId}' from room '${room}'?`)) return;
      try {
        const res = await fetch('/api/webrtc/leave', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ peer_id: peerId, room })
        });
        if (res.ok) {
          playXpChime();
          await pollMeshState();
        }
      } catch (err) {
        alert('Kick request failed: ' + err);
      }
    }

    async function sendAdminBroadcast() {
      const input = document.getElementById('adminAnnouncementInput');
      const text = input ? input.value.trim() : '';
      if (!text) return;
      input.value = '';
      const room = document.getElementById('roomInput').value.trim() || 'main';
      try {
        await fetch('/api/webrtc/signal', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            from: myPeerId,
            to: '*',
            type: 'admin_broadcast',
            room,
            payload: {
              text,
              sender: myPeerId,
              role: 'admin',
              timestamp: Date.now()
            }
          })
        });
        showAdminBanner(text, myPeerId);
        playXpChime();
      } catch (err) {
        alert('Broadcast failed: ' + err);
      }
    }

    // Switch the notification bar between the admin (filled ink label) and info (outlined label) variants.
    function setNotificationVariant(variant) {
      const banner = document.getElementById('adminBroadcastBanner');
      if (!banner) return;
      const admin = variant !== 'info';
      banner.dataset.variant = admin ? 'admin' : 'info';
      const label = document.getElementById('adminBroadcastLabel');
      if (label) label.textContent = admin ? 'ADMIN' : 'TINCAN';
    }

    function showAdminBanner(text, sender) {
      const banner = document.getElementById('adminBroadcastBanner');
      const textEl = document.getElementById('adminBroadcastText');
      if (banner && textEl) {
        setNotificationVariant('admin');
        textEl.innerText = `${text} (by ${sender || 'Admin'})`;
        textEl.title = textEl.innerText;
        banner.classList.remove('hidden');
      }
    }

    function dismissAdminBanner() {
      const banner = document.getElementById('adminBroadcastBanner');
      if (banner) banner.classList.add('hidden');
    }

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

    // Window Manager: Draggable, Resizable, Focus, Minimize, Maximize, Pop Out, Multi-Instance
    let highestZ = 45;
    const allWindows = ['win-terminal', 'win-tv', 'win-arena', 'win-call', 'win-comms', 'win-quests', 'win-moderator', 'win-billing', 'win-board', 'win-network', 'win-agentspace', 'win-workstation', 'win-browser', 'win-localhost', 'win-copilot', 'win-ai-home', 'win-nodes'];
    const poppedOutWindows = new Set();

    function switchNetTab(tabName) {
      ['peers', 'visitors', 'leaderboard'].forEach(t => {
        const btn = document.getElementById(`btnNetTab-${t}`);
        const panel = document.getElementById(`netPanel-${t}`);
        if (btn) {
          if (t === tabName) {
            btn.className = 'p-2.5 rounded-lg bg-emerald-950/90 text-emerald-300 border border-emerald-600 font-bold text-center transition active:scale-95';
          } else {
            btn.className = 'p-2.5 rounded-lg bg-slate-950/90 text-slate-300 border border-slate-800 hover:border-slate-700 text-center transition active:scale-95';
          }
        }
        if (panel) {
          panel.classList.toggle('hidden', t !== tabName);
        }
      });
    }

    function bringToFront(winEl) {
      highestZ += 1;
      winEl.style.zIndex = highestZ;
      document.querySelectorAll('.mesh-window').forEach(w => w.classList.remove('window-focused'));
      winEl.classList.add('window-focused');
      if (typeof syncDockIndicators === 'function') {
        syncDockIndicators();
      }
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
        document.body.classList.add('tc-dragging-window');
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
          document.body.classList.remove('tc-dragging-window');
          window.removeEventListener('mousemove', onMouseMove);
          window.removeEventListener('mouseup', onMouseUp);
        }

        window.addEventListener('mousemove', onMouseMove);
        window.addEventListener('mouseup', onMouseUp);
      });
    }

    function makeWindowResizable(winEl) {
      let handle = winEl.querySelector('.window-resize-handle');
      if (!handle) {
        handle = document.createElement('div');
        handle.className = 'window-resize-handle';
        handle.title = 'Drag to resize window (double-click to reset)';
        winEl.appendChild(handle);
      }
      let handleE = winEl.querySelector('.window-resize-e');
      if (!handleE) {
        handleE = document.createElement('div');
        handleE.className = 'window-resize-e';
        handleE.title = 'Drag right edge to resize width (double-click to reset)';
        winEl.appendChild(handleE);
      }
      let handleS = winEl.querySelector('.window-resize-s');
      if (!handleS) {
        handleS = document.createElement('div');
        handleS.className = 'window-resize-s';
        handleS.title = 'Drag bottom edge to resize height (double-click to reset)';
        winEl.appendChild(handleS);
      }

      const geomKey = winEl.id ? ('tincan_win_geom_' + winEl.id) : null;
      const bodyEl = winEl.querySelector('.window-body');
      if (geomKey && !winEl.classList.contains('popout-fullscreen')) {
        try {
          const saved = JSON.parse(localStorage.getItem(geomKey) || 'null');
          if (saved && saved.w >= 300 && saved.h >= 180) {
            const maxW = Math.max(320, (window.innerWidth || 1280) - 16);
            const maxH = Math.max(220, (window.innerHeight || 820) - 74);
            winEl.style.width = Math.min(maxW, saved.w) + 'px';
            winEl.style.height = Math.min(maxH, saved.h) + 'px';
            winEl.dataset.resized = 'true';
            if (bodyEl) {
              bodyEl.style.maxHeight = 'none';
              bodyEl.style.height = 'auto';
            }
          }
        } catch (e) {}
      }

      function bindEdge(target, axis) {
        target.addEventListener('pointerdown', (e) => {
          if (winEl.classList.contains('maximized') || winEl.classList.contains('popout-fullscreen')) {
            return;
          }
          e.stopPropagation();
          e.preventDefault();
          bringToFront(winEl);
          document.body.classList.add('tc-dragging-window');
          if (target.setPointerCapture) {
            try { target.setPointerCapture(e.pointerId); } catch (err) {}
          }

          const startX = e.clientX;
          const startY = e.clientY;
          const rect = winEl.getBoundingClientRect();
          const startW = winEl.offsetWidth || rect.width;
          const startH = winEl.offsetHeight || rect.height;
          if (winEl.style.right && winEl.style.right !== 'auto') {
            winEl.style.left = Math.max(8, rect.left) + 'px';
            winEl.style.right = 'auto';
          }
          winEl.dataset.resized = 'true';
          if (bodyEl) {
            bodyEl.style.maxHeight = 'none';
            bodyEl.style.height = 'auto';
          }

          function onPointerMove(moveEvent) {
            const vw = window.innerWidth || 1280;
            const vh = window.innerHeight || 820;
            const maxW = Math.max(320, vw - Math.max(8, winEl.getBoundingClientRect().left) - 8);
            const maxH = Math.max(220, vh - Math.max(8, winEl.getBoundingClientRect().top) - 14);
            if (axis === 'se' || axis === 'e') {
              const newW = Math.min(maxW, Math.max(300, startW + (moveEvent.clientX - startX)));
              winEl.style.width = `${Math.round(newW)}px`;
            }
            if (axis === 'se' || axis === 's') {
              const newH = Math.min(maxH, Math.max(180, startH + (moveEvent.clientY - startY)));
              winEl.style.height = `${Math.round(newH)}px`;
            }
            try { window.dispatchEvent(new Event('resize')); } catch (err) {}
          }

          function onPointerUp(upEvent) {
            document.body.classList.remove('tc-dragging-window');
            if (target.releasePointerCapture) {
              try { target.releasePointerCapture(upEvent.pointerId); } catch (err) {}
            }
            window.removeEventListener('pointermove', onPointerMove);
            window.removeEventListener('pointerup', onPointerUp);
            window.removeEventListener('pointercancel', onPointerUp);
            if (geomKey) {
              try {
                localStorage.setItem(geomKey, JSON.stringify({
                  w: winEl.offsetWidth,
                  h: winEl.offsetHeight,
                }));
              } catch (err) {}
            }
            try { window.dispatchEvent(new Event('resize')); } catch (err) {}
          }

          window.addEventListener('pointermove', onPointerMove);
          window.addEventListener('pointerup', onPointerUp);
          window.addEventListener('pointercancel', onPointerUp);
        });

        target.addEventListener('dblclick', (e) => {
          e.stopPropagation();
          delete winEl.dataset.resized;
          winEl.style.width = '';
          winEl.style.height = '';
          if (bodyEl) {
            bodyEl.style.height = '';
            bodyEl.style.maxHeight = '';
          }
          if (geomKey) {
            try { localStorage.removeItem(geomKey); } catch (err) {}
          }
          try { window.dispatchEvent(new Event('resize')); } catch (err) {}
        });
      }

      bindEdge(handle, 'se');
      bindEdge(handleE, 'e');
      bindEdge(handleS, 's');
    }

    function getDockButton(winId) {
      if (winId === 'win-moderator') {
        return document.getElementById('dockModBtn') || document.getElementById('dockBtn-win-moderator');
      }
      return document.getElementById(`dockBtn-${winId}`);
    }

    function setWindowPoppedOut(winId, isPoppedOut) {
      // In a pop-out standalone tab, never hide our own primary window!
      if (singleWindowParam && singleWindowParam === winId) {
        return;
      }

      if (winId === 'win-workstation' && typeof _is3dStudioDocked !== 'undefined' && _is3dStudioDocked && typeof mount3dStudioInWorkstation === 'function') {
        mount3dStudioInWorkstation(false);
        if (typeof switchFinderTab === 'function') switchFinderTab('files');
      }
      const win = document.getElementById(winId);
      const dockBtn = getDockButton(winId);

      if (isPoppedOut) {
        poppedOutWindows.add(winId);
        if (win) {
          win.style.display = 'none';
          win.classList.add('hidden', 'popped-out');
        }
        if (dockBtn) {
          dockBtn.dataset.poppedOut = 'true';
          dockBtn.classList.add('ring-2', 'ring-indigo-400', 'bg-indigo-950/80', 'text-indigo-200');
          dockBtn.title = `${winId} is open in a pop-out window. Click to focus or redock.`;
        }
        if (winId === 'win-comms') {
          const chatDockBtn = document.getElementById('dockBtn-chat');
          if (chatDockBtn) {
            chatDockBtn.classList.add('ring-2', 'ring-indigo-400');
            chatDockBtn.title = 'Live Chat is open in pop-out window.';
          }
        }
      } else {
        poppedOutWindows.delete(winId);
        if (dockBtn) {
          delete dockBtn.dataset.poppedOut;
          dockBtn.classList.remove('ring-2', 'ring-indigo-400', 'bg-indigo-950/80', 'text-indigo-200');
          dockBtn.title = '';
          if (winId === 'win-moderator') {
            if (isAdmin) {
              dockBtn.style.display = '';
              dockBtn.classList.remove('hidden');
            }
          } else {
            dockBtn.style.display = '';
            dockBtn.classList.remove('hidden');
          }
        }
        if (winId === 'win-comms') {
          const chatDockBtn = document.getElementById('dockBtn-chat');
          if (chatDockBtn) {
            chatDockBtn.classList.remove('ring-2', 'ring-indigo-400');
            chatDockBtn.title = 'Live Mesh Chat & Comms';
          }
        }
        if (win) {
          win.classList.remove('hidden', 'minimized', 'popped-out');
          win.style.display = 'flex';
          bringToFront(win);
        }
      }
      syncDockIndicators();
    }

    const windowInstances = new Map();
    const windowInstanceCounters = new Map();
    window.windowInstances = windowInstances;

    function _escapeInstHtml(v) {
      return String(v == null ? '' : v).replace(/[&<>"']/g, (c) => (
        { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
      ));
    }

    function resolveBaseWindowId(winId) {
      const raw = String(winId || '').trim();
      const el = document.getElementById(raw);
      if (el && el.dataset && el.dataset.baseWindow) return el.dataset.baseWindow;
      const idx = raw.indexOf('--inst-');
      return idx !== -1 ? raw.slice(0, idx) : raw;
    }

    function buildWindowInstanceUrl(baseWinId, opts, instanceSlug) {
      const o = opts || {};
      const params = new URLSearchParams();
      params.set('window', baseWinId);
      params.set('embed', o.popout ? '0' : '1');
      if (o.popout) params.delete('embed');
      params.set('instance', instanceSlug);
      params.set('room', o.room || currentRoom || 'main');
      params.set('peer', o.peer || myPeerId || '');
      [
        'scope', 'owner', 'file', 'cmd', 'topic', 'boardTab', 'feedFilter',
        'q', 'channel', 'dm', 'dmLabel', 'modelA', 'modelB', 'prompt',
        'thread', 'model', 'priority', 'fresh', 'video', 'ask', 'job',
      ].forEach((k) => {
        if (o[k] !== undefined && o[k] !== null && String(o[k]) !== '') {
          params.set(k, String(o[k]));
        }
      });
      return '/?' + params.toString();
    }

    function syncDockIndicators() {
      allWindows.forEach(id => {
        const win = document.getElementById(id);
        const dockBtn = getDockButton(id);
        if (!win || !dockBtn) return;

        let openInstances = 0;
        let focusedInstance = false;
        windowInstances.forEach((meta, instId) => {
          if (meta.baseWinId !== id) return;
          const el = document.getElementById(instId);
          if (!el || el.style.display === 'none' || el.classList.contains('hidden') || el.classList.contains('minimized')) return;
          openInstances += 1;
          if (el.classList.contains('window-focused')) focusedInstance = true;
        });

        const baseClosed = win.style.display === 'none' || win.classList.contains('hidden') || win.classList.contains('minimized');
        const totalOpen = (baseClosed ? 0 : 1) + openInstances;
        const isClosed = totalOpen === 0;
        const isFocused = (!baseClosed && win.classList.contains('window-focused')) || focusedInstance;

        if (isFocused) {
          dockBtn.classList.add('ring-2', 'ring-cyan-400');
          dockBtn.classList.remove('opacity-70');
        } else if (!isClosed) {
          dockBtn.classList.remove('ring-2', 'ring-cyan-400');
          dockBtn.classList.add('ring-1', 'ring-slate-500');
          dockBtn.classList.remove('opacity-70');
        } else {
          dockBtn.classList.remove('ring-1', 'ring-2', 'ring-cyan-400', 'ring-slate-500');
          dockBtn.classList.add('opacity-70');
        }

        let countEl = dockBtn.querySelector('.tc-instance-count');
        if (totalOpen > 1) {
          if (!countEl && typeof document.createElement === 'function') {
            countEl = document.createElement('span');
            countEl.className = 'tc-instance-count';
            dockBtn.appendChild(countEl);
          }
          if (countEl) countEl.textContent = `${totalOpen}×`;
        } else if (countEl && typeof countEl.remove === 'function') {
          countEl.remove();
        }
      });
    }

    function closeWindowInstance(instanceId) {
      const meta = windowInstances.get(instanceId);
      const win = document.getElementById(instanceId);
      if (win && typeof win.remove === 'function') {
        win.remove();
      }
      windowInstances.delete(instanceId);
      if (meta && meta.baseWinId) {
        const base = document.getElementById(meta.baseWinId);
        if (base && base.style.display !== 'none' && !base.classList.contains('hidden')) {
          bringToFront(base);
        }
      }
      syncDockIndicators();
    }
    window.closeWindowInstance = closeWindowInstance;

    function openWindowInstance(winId, opts) {
      // Forward calls inside an embedded iframe up to the parent desktop window manager cleanly.
      if (isEmbedInstance && window.parent && window.parent !== window && typeof window.parent.openWindowInstance === 'function') {
        return window.parent.openWindowInstance(winId, opts);
      }
      const o = Object.assign({}, opts || {});
      const baseWinId = resolveBaseWindowId(winId);
      const baseWin = document.getElementById(baseWinId);
      const nextSeq = (windowInstanceCounters.get(baseWinId) || 1) + 1;
      windowInstanceCounters.set(baseWinId, nextSeq);

      const instanceSlug = o.instance || (`inst-${nextSeq}-${Math.random().toString(36).slice(2, 6)}`);
      const instanceDomId = `${baseWinId}--${instanceSlug}`;

      if (baseWinId === 'win-copilot' && !o.thread && o.fresh === undefined) {
        o.fresh = '1';
        o.thread = `tincan-thread-${nextSeq}`;
      }
      const existingSubtitle =
        o.subtitle || o.title ||
        (o.owner ? `${o.scope || 'topic'}: ${o.owner}` : '') ||
        (o.channel ? `#${String(o.channel).replace(/^#/, '')}` : '') ||
        (o.dmLabel ? `DM ${o.dmLabel}` : (o.dm ? `DM ${o.dm}` : '')) ||
        (o.thread ? `thread: ${o.thread}` : '') ||
        (o.modelA && o.modelB ? `${o.modelA} vs ${o.modelB}` : '') ||
        `Instance #${nextSeq}`;

      const titleEl = baseWin ? baseWin.querySelector('.tc-titlebar__title') : null;
      const iconEl = baseWin ? baseWin.querySelector('.tc-titlebar__icon') : null;
      const baseTitle = (titleEl && titleEl.textContent) || baseWinId;
      const baseIcon = (iconEl && iconEl.textContent) || '';

      const baseRect = (baseWin && baseWin.getBoundingClientRect && baseWin.style.display !== 'none' && !baseWin.classList.contains('hidden'))
        ? baseWin.getBoundingClientRect()
        : null;
      const vw = Math.max(800, window.innerWidth || 1280);
      const vh = Math.max(600, window.innerHeight || 820);
      const width = Math.min(vw - 32, Math.max(460, Math.round((baseRect && baseRect.width) || (baseWin && parseInt(baseWin.style.width || '0', 10)) || 880)));
      const height = Math.min(vh - 130, Math.max(380, Math.round((baseRect && baseRect.height) || 580)));
      const offset = ((nextSeq - 1) % 6) * 28;
      const left = Math.min(Math.max(16, vw - width - 20), Math.max(16, Math.round((baseRect ? baseRect.left : 96) + offset)));
      const top = Math.min(Math.max(58, vh - height - 76), Math.max(58, Math.round((baseRect ? baseRect.top : 74) + offset)));

      const iframeUrl = buildWindowInstanceUrl(baseWinId, o, instanceSlug);
      const winEl = document.createElement('div');
      winEl.id = instanceDomId;
      winEl.className = 'mesh-window mesh-window-instance max-w-full';
      winEl.dataset.zenWindow = 'true';
      winEl.dataset.windowId = instanceDomId;
      winEl.dataset.baseWindow = baseWinId;
      winEl.dataset.instanceId = instanceSlug;
      winEl.style.top = `${top}px`;
      winEl.style.left = `${left}px`;
      winEl.style.width = `${width}px`;
      winEl.style.height = `${height}px`;
      winEl.style.display = 'flex';

      const iconSpan = baseIcon ? `<span class="tc-titlebar__icon" aria-hidden="true">${_escapeInstHtml(baseIcon)}</span>` : '';
      const optsLiteral = JSON.stringify(Object.assign({}, o, { instance: instanceSlug })).replace(/"/g, '&quot;');
      winEl.innerHTML =
        `<div class="window-header tc-titlebar" data-tc-titlebar="${_escapeInstHtml(instanceDomId)}">` +
          `<div class="tc-titlebar__lead">` +
            iconSpan +
            `<span class="window-title tc-titlebar__title" title="${_escapeInstHtml(baseTitle)}">${_escapeInstHtml(baseTitle)}</span>` +
            `<span class="tc-titlebar__badge" title="Window Instance #${nextSeq}">#${nextSeq}</span>` +
            `<span id="${_escapeInstHtml(instanceDomId)}--subtitle" class="tc-titlebar__meta" title="${_escapeInstHtml(existingSubtitle)}">${_escapeInstHtml(existingSubtitle)}</span>` +
          `</div>` +
          `<div class="window-controls tc-titlebar__controls">` +
            `<button type="button" class="tc-ctl tc-ctl--new" onclick="openWindowInstance('${_escapeInstHtml(baseWinId)}')" title="Open another independent ${_escapeInstHtml(baseTitle)} window" aria-label="New ${_escapeInstHtml(baseTitle)} window">+ New</button>` +
            `<button type="button" class="tc-ctl tc-ctl--pop" onclick="openPopoutWindow('${_escapeInstHtml(baseWinId)}', JSON.parse('${optsLiteral}'))" title="Pop out into a separate browser window" aria-label="Pop out">&#x2197;&#xFE0E; Pop Out</button>` +
            `<button type="button" class="tc-ctl tc-ctl--max" onclick="maximizeWindow('${_escapeInstHtml(instanceDomId)}')" title="Maximize" aria-label="Maximize">&#x25A1;</button>` +
            `<button type="button" class="tc-ctl tc-ctl--close" onclick="closeWindowInstance('${_escapeInstHtml(instanceDomId)}')" title="Close window" aria-label="Close">&#x2715;</button>` +
          `</div>` +
        `</div>` +
        `<div class="window-body p-0 overflow-hidden">` +
          `<iframe src="${_escapeInstHtml(iframeUrl)}" data-instance-frame="${_escapeInstHtml(instanceDomId)}" class="w-full h-full border-0 block" style="width:100%;height:100%;border:0;display:block;" title="${_escapeInstHtml(baseTitle)} — ${_escapeInstHtml(existingSubtitle)}" allow="clipboard-read; clipboard-write; microphone; camera"></iframe>` +
        `</div>`;

      const host = document.getElementById('desktopWorkspace') || document.body;
      host.appendChild(winEl);
      windowInstances.set(instanceDomId, { baseWinId, instanceSlug, seq: nextSeq, subtitle: existingSubtitle, opts: o });

      makeWindowDraggable(winEl);
      makeWindowResizable(winEl);
      if (document.body.classList.contains('zen')) {
        document.body.classList.add('zen-working');
      }
      bringToFront(winEl);
      syncDockIndicators();
      return winEl;
    }
    window.openWindowInstance = openWindowInstance;

    window.addEventListener('message', (ev) => {
      if (ev.origin && window.location && ev.origin !== window.location.origin) return;
      const d = ev.data;
      if (!d || d.type !== 'TC_INSTANCE_TITLE' || !d.instanceId) return;
      windowInstances.forEach((meta, instDomId) => {
        if (meta.instanceSlug === d.instanceId && d.subtitle) {
          meta.subtitle = d.subtitle;
          const subEl = document.getElementById(`${instDomId}--subtitle`);
          if (subEl) {
            subEl.textContent = d.subtitle;
            subEl.title = d.subtitle;
          }
        }
      });
    });

    function toggleWindow(winId) {
      if (poppedOutWindows.has(winId)) {
        const handle = popoutWindowHandles.get(winId);
        if (handle && !handle.closed) {
          try { handle.focus(); } catch (e) {}
          const shouldRedock = confirm(`Window '${winId}' is currently open in a pop-out window on your second screen.\n\nClick OK to pull it back and redock onto this main desktop, or Cancel to leave it open.`);
          if (shouldRedock) {
            try { handle.close(); } catch(e){}
            popoutWindowHandles.delete(winId);
            setWindowPoppedOut(winId, false);
          }
          return;
        } else {
          setWindowPoppedOut(winId, false);
          return;
        }
      }

      if (winId === 'win-workstation' && typeof _is3dStudioDocked !== 'undefined' && _is3dStudioDocked && typeof mount3dStudioInWorkstation === 'function') {
        mount3dStudioInWorkstation(false);
        if (typeof switchFinderTab === 'function') switchFinderTab('files');
      }
      const win = document.getElementById(winId);
      if (!win) return;
      const isHidden = win.style.display === 'none' || win.classList.contains('hidden') || win.classList.contains('minimized');
      if (isHidden) {
        win.style.display = 'flex';
        win.classList.remove('hidden', 'minimized');
        // Clamp initial position inside viewport on smaller laptops/tablets
        try {
          const vw = window.innerWidth || 1280;
          const vh = window.innerHeight || 820;
          const rect = win.getBoundingClientRect();
          if (rect.width > vw - 16) {
            win.style.left = '8px';
            win.style.right = 'auto';
            win.style.width = (vw - 16) + 'px';
          } else if (rect.right > vw - 8) {
            win.style.left = Math.max(8, vw - rect.width - 8) + 'px';
            win.style.right = 'auto';
          }
          if (rect.top > vh - 120) {
            win.style.top = Math.max(58, vh - rect.height - 76) + 'px';
          }
        } catch (e) {}
        bringToFront(win);
        try { window.dispatchEvent(new Event('resize')); } catch (e) {}
      } else {
        if (win.classList.contains('window-focused')) {
          minimizeWindow(winId);
          return;
        } else {
          bringToFront(win);
        }
      }
      syncDockIndicators();
    }

    function focusChatWindow() {
      const win = document.getElementById('win-comms');
      if (!win) return;
      win.style.display = 'flex';
      win.classList.remove('minimized', 'hidden');
      bringToFront(win);
      win.scrollIntoView({ behavior: 'smooth', block: 'center' });
      const inp = document.getElementById('chatInput');
      if (inp) inp.focus();
      syncDockIndicators();
    }

    function minimizeWindow(winId) {
      if (windowInstances.has(winId)) {
        closeWindowInstance(winId);
        return;
      }
      const win = document.getElementById(winId);
      if (!win) return;
      if (win.classList.contains('mesh-window-instance')) {
        closeWindowInstance(winId);
        return;
      }
      win.classList.add('minimized', 'hidden');
      win.style.display = 'none';
      win.classList.remove('window-focused');
      syncDockIndicators();
    }

    function maximizeWindow(winId) {
      if (winId === 'win-workstation' && typeof _is3dStudioDocked !== 'undefined' && _is3dStudioDocked && typeof mount3dStudioInWorkstation === 'function') {
        mount3dStudioInWorkstation(false);
        if (typeof switchFinderTab === 'function') switchFinderTab('files');
      }
      const win = document.getElementById(winId);
      if (!win) return;
      win.classList.remove('minimized', 'hidden');
      win.style.display = 'flex';
      win.classList.toggle('maximized');
      bringToFront(win);
      syncDockIndicators();
    }

    const popoutWindowHandles = new Map();

    function openPopoutWindow(winId, opts) {
      if (opts && opts.instance) {
        const baseWinId = resolveBaseWindowId(winId);
        const popOpts = Object.assign({}, opts, { popout: true });
        const popUrl = buildWindowInstanceUrl(baseWinId, popOpts, opts.instance);
        const popWin = window.open(popUrl, `_tincan_popout_${baseWinId}_${opts.instance}`, 'width=1120,height=760,menubar=no,toolbar=no,location=no,status=no');
        if (!popWin || popWin.closed || typeof popWin.closed === 'undefined') {
          alert('⚠️ Pop-up was blocked by your browser!\n\nPlease click the pop-up icon in your address bar and select "Always allow pop-ups for this site" to open windows in separate monitors.');
        }
        return;
      }
      const targetUrl = `/?window=${encodeURIComponent(winId)}&room=${encodeURIComponent(currentRoom)}&peer=${encodeURIComponent(myPeerId)}`;
      const popWin = window.open(targetUrl, `_tincan_popout_${winId}`, 'width=1120,height=760,menubar=no,toolbar=no,location=no,status=no');

      if (!popWin || popWin.closed || typeof popWin.closed === 'undefined') {
        alert('⚠️ Pop-up was blocked by your browser!\n\nPlease click the pop-up icon in your address bar and select "Always allow pop-ups for this site" to open windows in separate monitors.');
        return;
      }

      popoutWindowHandles.set(winId, popWin);
      setWindowPoppedOut(winId, true);

      const timer = setInterval(() => {
        if (popWin.closed) {
          clearInterval(timer);
          popoutWindowHandles.delete(winId);
          setWindowPoppedOut(winId, false);
          meshBus.postMessage({ type: 'WINDOW_REDOCK', winId: winId });
        }
      }, 400);

      meshBus.postMessage({ type: 'WINDOW_POPOUT', winId: winId });
    }
    window.toggleWindow = toggleWindow;
    window.minimizeWindow = minimizeWindow;
    window.maximizeWindow = maximizeWindow;
    window.openPopoutWindow = openPopoutWindow;

    let currentDesktopLayout = localStorage.getItem('tincan_layout_mode') || 'free';

    function setDesktopLayout(mode) {
      currentDesktopLayout = mode;
      localStorage.setItem('tincan_layout_mode', mode);

      const btn2x2 = document.getElementById('btnLayoutTile2x2');
      const btnSplit = document.getElementById('btnLayoutSplit');
      const btnFree = document.getElementById('btnLayoutFree');

      if (btn2x2) btn2x2.className = (mode === 'tile2x2') ? 'px-2 py-0.5 rounded bg-indigo-600 text-white font-bold shadow transition flex items-center gap-1' : 'px-2 py-0.5 rounded text-slate-400 hover:text-white transition flex items-center gap-1';
      if (btnSplit) btnSplit.className = (mode === 'split2col') ? 'px-2 py-0.5 rounded bg-indigo-600 text-white font-bold shadow transition flex items-center gap-1' : 'px-2 py-0.5 rounded text-slate-400 hover:text-white transition flex items-center gap-1';
      if (btnFree) btnFree.className = (mode === 'free') ? 'px-2 py-0.5 rounded bg-indigo-600 text-white font-bold shadow transition flex items-center gap-1' : 'px-2 py-0.5 rounded text-slate-400 hover:text-white transition flex items-center gap-1';

      if (mode === 'free') {
        allWindows.forEach(id => {
          const w = document.getElementById(id);
          if (w) {
            w.style.height = '';
            const body = w.querySelector('.window-body');
            if (body) body.style.height = '';
          }
        });
        return;
      }

      const isMobile = window.innerWidth < 768;
      const vw = window.innerWidth;
      const vh = window.innerHeight;
      const topBarHeight = 56;
      const dockHeight = 64;
      const pad = 12;
      const availH = vh - topBarHeight - dockHeight - (pad * 2);

      if (isMobile) {
        let top = 70;
        ['win-tv', 'win-arena', 'win-board', 'win-network'].forEach(id => {
          const w = document.getElementById(id);
          if (!w) return;
          w.style.display = 'flex';
          w.classList.remove('maximized', 'minimized', 'hidden');
          w.style.left = '10px';
          w.style.right = '10px';
          w.style.top = `${top}px`;
          w.style.width = 'calc(100vw - 20px)';
          top += 580;
        });
        return;
      }

      if (mode === 'tile2x2') {
        const halfW = Math.floor((vw - (pad * 3)) / 2);
        const halfH = Math.max(340, Math.floor(availH / 2));

        const quadrants = [
          { id: 'win-tv', x: pad, y: topBarHeight + pad, w: halfW, h: halfH },
          { id: 'win-arena', x: pad + halfW + pad, y: topBarHeight + pad, w: halfW, h: halfH },
          { id: 'win-board', x: pad, y: topBarHeight + pad + halfH + pad, w: halfW, h: halfH },
          { id: 'win-network', x: pad + halfW + pad, y: topBarHeight + pad + halfH + pad, w: halfW, h: halfH }
        ];

        quadrants.forEach(q => {
          const w = document.getElementById(q.id);
          if (w) {
            w.style.display = 'flex';
            w.classList.remove('hidden', 'minimized', 'maximized');
            w.style.left = `${q.x}px`;
            w.style.top = `${q.y}px`;
            w.style.width = `${q.w}px`;
            w.style.height = `${q.h}px`;
            const body = w.querySelector('.window-body');
            if (body) {
              body.style.maxHeight = `${q.h - 44}px`;
              body.style.height = `${q.h - 44}px`;
            }
            bringToFront(w);
          }
        });
      } else if (mode === 'split2col') {
        const halfW = Math.floor((vw - (pad * 3)) / 2);
        const halfH = Math.max(340, Math.floor(availH / 2));

        const splits = [
          { id: 'win-tv', x: pad, y: topBarHeight + pad, w: halfW, h: halfH },
          { id: 'win-board', x: pad, y: topBarHeight + pad + halfH + pad, w: halfW, h: halfH },
          { id: 'win-arena', x: pad + halfW + pad, y: topBarHeight + pad, w: halfW, h: halfH },
          { id: 'win-network', x: pad + halfW + pad, y: topBarHeight + pad + halfH + pad, w: halfW, h: halfH }
        ];

        splits.forEach(s => {
          const w = document.getElementById(s.id);
          if (w) {
            w.style.display = 'flex';
            w.classList.remove('hidden', 'minimized', 'maximized');
            w.style.left = `${s.x}px`;
            w.style.top = `${s.y}px`;
            w.style.width = `${s.w}px`;
            w.style.height = `${s.h}px`;
            const body = w.querySelector('.window-body');
            if (body) {
              body.style.maxHeight = `${s.h - 44}px`;
              body.style.height = `${s.h - 44}px`;
            }
            bringToFront(w);
          }
        });
      }
    }

    function tileWindows() {
      setDesktopLayout('tile2x2');
    }

    function togglePopoutGuide() {
      alert('TinCan Mesh OS Pop-Out Mode:\n\n1. Click [ ↗ Pop Out ] on any window titlebar.\n2. Move the pop-out window to your secondary monitor.\n3. Packet flights, watch-party playback, cursor telemetry, and XP sync across all windows in real time via BroadcastChannel!');
    }

    // Initialize Windows
    allWindows.forEach(id => {
      const w = document.getElementById(id);
      if (w) {
        makeWindowDraggable(w);
        makeWindowResizable(w);
      }
    });
    syncDockIndicators();

    // Handle Pop-Out Single-Window Viewport Optimization
    if (singleWindowParam && allWindows.includes(singleWindowParam)) {
      allWindows.forEach(id => {
        const w = document.getElementById(id);
        if (w) {
          if (id === singleWindowParam) {
            w.classList.remove('hidden', 'minimized');
            w.classList.add('popout-fullscreen');
            w.style.display = 'flex';
            bringToFront(w);

            // Transform the Pop Out button in header into a Redock button
            const popBtn = w.querySelector('button[onclick*="openPopoutWindow"]');
            if (popBtn) {
              const openedAsPopout = !!urlParams.get('window') && !!window.opener;
              popBtn.innerText = openedAsPopout ? '↙ Redock' : '⌂ Desktop';
              popBtn.onclick = openedAsPopout ? () => window.close() : () => { window.location.href = '/'; };
              popBtn.title = openedAsPopout ? 'Close pop-out and return window to main desktop' : 'Open the full TinCan desktop';
              popBtn.setAttribute('aria-label', popBtn.title);
              popBtn.className = 'tc-ctl tc-ctl--pop';
            }

            // Hide the minimize button in popout window as it fills the window
            const minBtn = w.querySelector('button[onclick*="minimizeWindow"]');
            if (minBtn) minBtn.style.display = 'none';

            // Hide the maximize button in popout window
            const maxBtn = w.querySelector('button[onclick*="maximizeWindow"]');
            if (maxBtn) maxBtn.style.display = 'none';

            document.body.classList.add('tc-single');
            if (isEmbedInstance) document.body.classList.add('tc-embed');

            // If this is the TV watch party, ensure video starts playing
            if (id === 'win-tv') {
              const vid = document.getElementById('relayNativeVideo');
              if (vid) {
                vid.play().catch(e => console.warn('Pop-out video autoplay notice:', e));
              }
            }
          } else {
            w.style.display = 'none';
            w.classList.add('hidden');
          }
        }
      });

      // In pop-out mode, hide background topology canvas, cursors, and dock to maximize app workspace
      const bgCanvas = document.getElementById('meshTopologyCanvas');
      if (bgCanvas) bgCanvas.style.display = 'none';
      const cursors = document.getElementById('multiplayerCursorsLayer');
      if (cursors) cursors.style.display = 'none';
      const dock = document.getElementById('meshOsDock');
      if (dock) dock.style.display = 'none';

      document.title = `[Pop-Out] TinCan Mesh OS — ${singleWindowParam}`;

      if (!isEmbedInstance && !instanceParam) {
        window.addEventListener('beforeunload', () => {
          meshBus.postMessage({ type: 'WINDOW_REDOCK', winId: singleWindowParam });
        });
      }
    }

    // =========================================================================
    // Account Setup, Username Prompt & Onboarding Engine (Mandatory Non-Negotiable Gate)
    // =========================================================================
    const REGISTRATION_EPOCH = 'epoch_20261109_v3_strict_pii';

    function isIdentityVerified() {
      return (
        localStorage.getItem('tincan_registration_epoch') === REGISTRATION_EPOCH &&
        Boolean((localStorage.getItem('tincan_fullname') || '').trim()) &&
        Boolean((localStorage.getItem('tincan_username') || '').trim()) &&
        Boolean((localStorage.getItem('tincan_email') || '').trim()) &&
        Boolean((localStorage.getItem('tincan_phone') || '').trim()) &&
        localStorage.getItem('tincan_consent_pii') === 'true'
      );
    }

    // Handles are stored without the leading @; tolerate older values saved as "@name".
    function cleanHandle(u) { return String(u == null ? '' : u).trim().replace(/^@+/, ''); }
    function formatHandle(u) { const h = cleanHandle(u); return h ? '@' + h : ''; }

    function getVerifiedDisplayName() {
      const fn = (localStorage.getItem('tincan_fullname') || '').trim();
      const un = cleanHandle(localStorage.getItem('tincan_username'));
      if (fn && un) return `${fn} (@${un})`;
      if (un) return `@${un}`;
      if (fn) return fn;
      return myPeerId;
    }

    function requireVerifiedIdentity(actionDescription = 'enter the room') {
      if (isIdentityVerified()) return true;
      openAccountModal(true);
      const errEl = document.getElementById('accFormError');
      if (errEl) {
        errEl.innerText = `Mandatory Identity Gate: You must identify yourself (Full Name, Username, Email, Phone & PII Consent) to ${actionDescription}.`;
        errEl.classList.remove('hidden');
      }
      return false;
    }

    function openAccountModal(isMandatory = false) {
      if (isEmbedInstance && window.parent && window.parent !== window && typeof window.parent.openAccountModal === 'function') {
        try { return window.parent.openAccountModal(isMandatory); } catch (e) {}
      }
      const modal = document.getElementById('accountSetupModal');
      const peerLabel = document.getElementById('modalPeerIdLabel');
      const nameInp = document.getElementById('accInputFullName');
      const userInp = document.getElementById('accInputUsername');
      const emailInp = document.getElementById('accInputEmail');
      const phoneInp = document.getElementById('accInputPhone');
      const errEl = document.getElementById('accFormError');
      if (errEl) errEl.classList.add('hidden');
      if (peerLabel) peerLabel.innerText = myPeerId;

      if (nameInp && localStorage.getItem('tincan_fullname')) nameInp.value = localStorage.getItem('tincan_fullname');
      if (userInp && localStorage.getItem('tincan_username')) userInp.value = localStorage.getItem('tincan_username');
      if (emailInp && localStorage.getItem('tincan_email')) emailInp.value = localStorage.getItem('tincan_email');
      if (phoneInp && localStorage.getItem('tincan_phone')) phoneInp.value = localStorage.getItem('tincan_phone');

      if (modal) {
        modal.classList.remove('hidden');
        if (nameInp && !nameInp.value) nameInp.focus();
        else if (userInp) userInp.focus();
      }
    }

    function closeAccountModal() {
      const isRegistered = localStorage.getItem('tincan_registration_epoch') === REGISTRATION_EPOCH 
        && localStorage.getItem('tincan_username') 
        && localStorage.getItem('tincan_consent_pii') === 'true';
      if (!isRegistered) {
        // Enforce non-negotiable mandatory registration: cannot close until identity & PII consent are confirmed!
        return;
      }
      const modal = document.getElementById('accountSetupModal');
      if (modal) modal.classList.add('hidden');
    }

    // Intercept Escape key to prevent modal bypass
    window.addEventListener('keydown', (e) => {
      const isRegistered = localStorage.getItem('tincan_registration_epoch') === REGISTRATION_EPOCH 
        && localStorage.getItem('tincan_username') 
        && localStorage.getItem('tincan_consent_pii') === 'true';
      if (!isRegistered && e.key === 'Escape') {
        e.preventDefault();
        e.stopPropagation();
      }
    }, true);

    function awardLocalXp(amount, reason) {
      try {
        if (sfxEnabled && typeof playXpChime === 'function') playXpChime();
        fetch('/api/mesh/quest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            action_key: 'workstation_handshake',
            display_name: localStorage.getItem('tincan_username') || myPeerId
          })
        }).catch(() => {});
      } catch (e) {
        console.warn('awardLocalXp caught error:', e);
      }
    }

    // =========================================================================
    // Passwordless passkey (WebAuthn) sign-in + one-time email code recovery
    // =========================================================================
    const EMAIL_EXISTS_TEXT = 'You already have an account \u2014 sign in with your passkey.';

    function b64urlToBuf(value) {
      const pad = '='.repeat((4 - (value.length % 4)) % 4);
      const b64 = (value + pad).replace(/-/g, '+').replace(/_/g, '/');
      const bin = atob(b64);
      const out = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
      return out.buffer;
    }

    function bufToB64url(buf) {
      const bytes = new Uint8Array(buf);
      let bin = '';
      for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
      return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    }

    function passkeysSupported() {
      return Boolean(window.PublicKeyCredential && navigator.credentials && window.isSecureContext);
    }

    function showPasskeyStatus(text, kind = 'info') {
      const el = document.getElementById('passkeyStatus');
      if (!el) return;
      const styles = {
        info: 'text-cyan-200 bg-cyan-950/40 border-cyan-800',
        ok: 'text-emerald-200 bg-emerald-950/40 border-emerald-800',
        error: 'text-red-300 bg-red-950/40 border-red-800'
      };
      el.className = 'p-2 rounded border ' + (styles[kind] || styles.info);
      el.innerText = text;
      el.classList.remove('hidden');
    }

    function toggleRecoveryPanel(show) {
      const panel = document.getElementById('passkeyRecoveryPanel');
      if (!panel) return;
      panel.classList.toggle('hidden', !show);
      const emailInp = document.getElementById('recoveryEmailInput');
      const formEmail = document.getElementById('accInputEmail');
      if (show && emailInp && !emailInp.value && formEmail && formEmail.value) emailInp.value = formEmail.value.trim();
    }

    async function postJson(url, payload) {
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      let data = {};
      try { data = await resp.json(); } catch (e) { data = {}; }
      return { ok: resp.ok, status: resp.status, data };
    }

    function serializeCredential(cred) {
      if (cred && typeof cred.toJSON === 'function') {
        try { return cred.toJSON(); } catch (e) { /* fall through to manual encoding */ }
      }
      const r = cred.response;
      const response = { clientDataJSON: bufToB64url(r.clientDataJSON) };
      if (r.attestationObject) {
        response.attestationObject = bufToB64url(r.attestationObject);
        if (typeof r.getTransports === 'function') response.transports = r.getTransports();
      }
      if (r.authenticatorData) response.authenticatorData = bufToB64url(r.authenticatorData);
      if (r.signature) response.signature = bufToB64url(r.signature);
      if (r.userHandle) response.userHandle = bufToB64url(r.userHandle);
      return {
        id: cred.id,
        rawId: bufToB64url(cred.rawId),
        type: cred.type,
        response,
        authenticatorAttachment: cred.authenticatorAttachment || undefined,
        clientExtensionResults: typeof cred.getClientExtensionResults === 'function' ? cred.getClientExtensionResults() : {}
      };
    }

    function applySignedInAccount(account) {
      if (!account) return;
      const username = (account.username || (account.full_name || '').split(' ')[0] || '').trim();
      localStorage.setItem('tincan_registration_epoch', REGISTRATION_EPOCH);
      localStorage.setItem('tincan_fullname', account.full_name || username);
      localStorage.setItem('tincan_username', cleanHandle(username));
      localStorage.setItem('tincan_email', account.email || '');
      localStorage.setItem('tincan_phone', account.phone_number || '');
      localStorage.setItem('tincan_role', account.role || 'Mesh Operator');
      localStorage.setItem('tincan_consent_pii', 'true');
      const hudName = document.getElementById('hudAccountName');
      if (hudName && username) hudName.innerText = formatHandle(username);
      const localLbl = document.getElementById('localPeerLabel');
      if (localLbl) localLbl.innerText = getVerifiedDisplayName();
      const modal = document.getElementById('accountSetupModal');
      if (modal) modal.classList.add('hidden');
      try { refreshBillingWindow(); } catch (e) {}
      // Login: re-gather the drive mirror fresh so spaces reflect the disk right now.
      try { gatherDriveMirror('login'); } catch (e) {}
    }

    async function createPasskeyWithToken(enrollToken) {
      if (!passkeysSupported()) throw new Error('This browser does not support passkeys.');
      const opts = await postJson('/api/passkey/register/options', { peer_id: myPeerId, enroll_token: enrollToken });
      if (!opts.ok) throw new Error(opts.data.error || 'Could not start passkey setup.');
      const pk = opts.data.publicKey;
      pk.challenge = b64urlToBuf(pk.challenge);
      pk.user.id = b64urlToBuf(pk.user.id);
      (pk.excludeCredentials || []).forEach((c) => { c.id = b64urlToBuf(c.id); });
      const cred = await navigator.credentials.create({ publicKey: pk });
      if (!cred) throw new Error('Passkey setup was cancelled.');
      const done = await postJson('/api/passkey/register/verify', {
        peer_id: myPeerId,
        challenge_id: opts.data.challenge_id,
        credential: serializeCredential(cred)
      });
      if (!done.ok) throw new Error(done.data.error || 'Could not save the passkey.');
      return done.data.account;
    }

    async function signInWithPasskey() {
      if (!passkeysSupported()) {
        showPasskeyStatus('This browser does not support passkeys. Open TinCan in Safari or Chrome over https.', 'error');
        return;
      }
      const btn = document.getElementById('passkeySignInBtn');
      if (btn) btn.disabled = true;
      try {
        const emailHint = ((document.getElementById('accInputEmail') || {}).value || '').trim();
        const opts = await postJson('/api/passkey/login/options', { peer_id: myPeerId, email: emailHint });
        if (!opts.ok) throw new Error(opts.data.error || 'Could not start passkey sign-in.');
        const pk = opts.data.publicKey;
        pk.challenge = b64urlToBuf(pk.challenge);
        (pk.allowCredentials || []).forEach((c) => { c.id = b64urlToBuf(c.id); });
        const cred = await navigator.credentials.get({ publicKey: pk });
        if (!cred) throw new Error('Passkey sign-in was cancelled.');
        const done = await postJson('/api/passkey/login/verify', {
          peer_id: myPeerId,
          challenge_id: opts.data.challenge_id,
          credential: serializeCredential(cred)
        });
        if (!done.ok) throw new Error(done.data.error || 'Passkey sign-in failed.');
        showPasskeyStatus('Signed in. Welcome back!', 'ok');
        applySignedInAccount(done.data.account);
        if (typeof sfxEnabled !== 'undefined' && sfxEnabled && typeof playXpChime === 'function') playXpChime();
      } catch (err) {
        const msg = err && err.name === 'NotAllowedError' ? 'Passkey sign-in was cancelled or timed out.' : (err.message || String(err));
        showPasskeyStatus(msg, 'error');
      } finally {
        if (btn) btn.disabled = false;
      }
    }

    async function requestRecoveryCode() {
      const email = ((document.getElementById('recoveryEmailInput') || {}).value || '').trim();
      if (!email || !email.includes('@')) {
        showPasskeyStatus('Enter the email on your account.', 'error');
        return;
      }
      const btn = document.getElementById('recoverySendBtn');
      if (btn) btn.disabled = true;
      try {
        const res = await postJson('/api/account/recovery/request', { email, peer_id: myPeerId });
        if (!res.ok) throw new Error(res.data.error || 'Could not send a code.');
        if (res.data.delivery_configured === false) {
          showPasskeyStatus('Email delivery is not set up on this server yet, so no code can be sent. Ask the TinCan operator to enable it.', 'error');
        } else {
          showPasskeyStatus(res.data.message || 'Check your email for a 6-digit code.', 'info');
          const codeInp = document.getElementById('recoveryCodeInput');
          if (codeInp) codeInp.focus();
        }
      } catch (err) {
        showPasskeyStatus(err.message || String(err), 'error');
      } finally {
        if (btn) btn.disabled = false;
      }
    }

    async function verifyRecoveryCode() {
      const email = ((document.getElementById('recoveryEmailInput') || {}).value || '').trim();
      const code = ((document.getElementById('recoveryCodeInput') || {}).value || '').replace(/\D/g, '');
      if (code.length !== 6) {
        showPasskeyStatus('Enter the 6-digit code from your email.', 'error');
        return;
      }
      const btn = document.getElementById('recoveryVerifyBtn');
      if (btn) btn.disabled = true;
      try {
        const res = await postJson('/api/account/recovery/verify', { email, code, peer_id: myPeerId });
        if (!res.ok) throw new Error(res.data.error || 'That code did not work.');
        showPasskeyStatus('Code accepted. Confirm with Face ID or your fingerprint to create your passkey.', 'info');
        const account = await createPasskeyWithToken(res.data.enroll_token);
        showPasskeyStatus('Passkey created. You are signed in on this device.', 'ok');
        applySignedInAccount(account);
      } catch (err) {
        const msg = err && err.name === 'NotAllowedError' ? 'Passkey setup was cancelled or timed out.' : (err.message || String(err));
        showPasskeyStatus(msg, 'error');
      } finally {
        if (btn) btn.disabled = false;
      }
    }

    async function handleAccountFormSubmit(e) {
      e.preventDefault();
      const fullName = (document.getElementById('accInputFullName') ? document.getElementById('accInputFullName').value : '').trim();
      const username = (document.getElementById('accInputUsername') ? document.getElementById('accInputUsername').value : '').trim();
      const email = (document.getElementById('accInputEmail') ? document.getElementById('accInputEmail').value : '').trim();
      const phone = (document.getElementById('accInputPhone') ? document.getElementById('accInputPhone').value : '').trim();
      const role = document.getElementById('accInputRole') ? document.getElementById('accInputRole').value : 'Mesh Operator';
      const consentPii = document.getElementById('accInputConsentPii') ? document.getElementById('accInputConsentPii').checked : false;
      const submitBtn = document.getElementById('accSubmitBtn');
      const errEl = document.getElementById('accFormError');

      if (!fullName || fullName.length < 2) {
        if (errEl) {
          errEl.innerText = 'Full Legal / Real Name is non-negotiable (minimum 2 characters).';
          errEl.classList.remove('hidden');
        }
        return;
      }

      if (!username || username.length < 2) {
        if (errEl) {
          errEl.innerText = 'Username / Mesh Call-Sign is non-negotiable (minimum 2 characters).';
          errEl.classList.remove('hidden');
        }
        return;
      }

      if (!email || !email.includes('@')) {
        if (errEl) {
          errEl.innerText = 'A valid contact email address is required for operator records.';
          errEl.classList.remove('hidden');
        }
        return;
      }

      const cleanPhone = phone.replace(/[^\d+]/g, '');
      if (!cleanPhone || cleanPhone.replace(/\D/g, '').length < 10) {
        if (errEl) {
          errEl.innerText = 'A valid phone number (minimum 10 digits) is non-negotiable for operator 2FA verification.';
          errEl.classList.remove('hidden');
        }
        return;
      }

      if (!consentPii) {
        if (errEl) {
          errEl.innerText = 'You must explicitly consent to PII storage, node telemetry, and operator auditing.';
          errEl.classList.remove('hidden');
        }
        return;
      }

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span>⏳</span> <span>Verifying &amp; Attesting Operator Identity...</span>';
      }

      try {
        const resp = await fetch('/api/account/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            full_name: fullName,
            name: fullName,
            username: username,
            email: email,
            phone: phone,
            phone_number: phone,
            role: role,
            consent_pii: true
          })
        });

        const data = await resp.json();
        if (resp.ok && data.status === 'success') {
          if (data.enroll_token && passkeysSupported()) {
            // Tie a passkey (Face ID / fingerprint) to the new account so other devices can sign in.
            try {
              await createPasskeyWithToken(data.enroll_token);
            } catch (pkErr) {
              console.warn('Passkey setup skipped:', pkErr && pkErr.message);
            }
          }
          localStorage.setItem('tincan_registration_epoch', REGISTRATION_EPOCH);
          localStorage.setItem('tincan_fullname', fullName);
          localStorage.setItem('tincan_username', cleanHandle(username));
          localStorage.setItem('tincan_email', email);
          localStorage.setItem('tincan_phone', phone);
          localStorage.setItem('tincan_role', role);
          localStorage.setItem('tincan_consent_pii', 'true');
          const hudName = document.getElementById('hudAccountName');
          if (hudName) hudName.innerText = formatHandle(username);
          const localLbl = document.getElementById('localPeerLabel');
          if (localLbl) localLbl.innerText = getVerifiedDisplayName();

          if (sfxEnabled) playXpChime();
          awardLocalXp(100, `Verified identity @${username}`);
          const modal = document.getElementById('accountSetupModal');
          if (modal) modal.classList.add('hidden');
          refreshBillingWindow();
          fetch('/api/mesh/cursor', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              peer_id: myPeerId,
              display_name: getVerifiedDisplayName(),
              x: 120,
              y: 120,
              room: currentRoom
            })
          }).catch(() => {});
          alert(`🎉 Identity Verified! Welcome Operator @${username}. 50,000 tokens have been credited to your account.`);
        } else if (data.code === 'email_exists') {
          if (errEl) {
            errEl.innerText = EMAIL_EXISTS_TEXT;
            errEl.classList.remove('hidden');
          }
          showPasskeyStatus(EMAIL_EXISTS_TEXT + ' No passkey yet? Use the email code option above.', 'info');
          const recEmail = document.getElementById('recoveryEmailInput');
          if (recEmail) recEmail.value = email;
          const signInPanel = document.getElementById('passkeySignInPanel');
          if (signInPanel && signInPanel.scrollIntoView) signInPanel.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else {
          if (errEl) {
            errEl.innerText = data.error || 'Failed to verify account. Please check your contact information.';
            errEl.classList.remove('hidden');
          }
        }
      } catch (err) {
        if (errEl) {
          errEl.innerText = 'Connection error: ' + err.message;
          errEl.classList.remove('hidden');
        }
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<span>🛡️</span> <span>Sign Identity &amp; Unlock TinCan Mesh OS</span>';
        }
      }
    }

    async function initAccountState() {
      const epochValid = localStorage.getItem('tincan_registration_epoch') === REGISTRATION_EPOCH;
      const savedUser = localStorage.getItem('tincan_username');
      const savedConsent = localStorage.getItem('tincan_consent_pii') === 'true';
      const hudName = document.getElementById('hudAccountName');

      if (!epochValid || !savedUser || !savedConsent) {
        // Enforce mandatory non-negotiable registration for EVERYONE
        openAccountModal(true);
        return;
      }

      if (savedUser) {
        if (hudName) hudName.innerText = formatHandle(savedUser);
        const localLbl = document.getElementById('localPeerLabel');
        if (localLbl) localLbl.innerText = getVerifiedDisplayName();
        // Re-sync localStorage identity to server in case container restarted
        fetch('/api/account/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            full_name: localStorage.getItem('tincan_fullname') || savedUser,
            name: localStorage.getItem('tincan_fullname') || savedUser,
            username: savedUser,
            email: localStorage.getItem('tincan_email') || `${savedUser}@mesh.local`,
            phone: localStorage.getItem('tincan_phone') || '+10000000000',
            phone_number: localStorage.getItem('tincan_phone') || '+10000000000',
            role: localStorage.getItem('tincan_role') || 'Mesh Operator',
            consent_pii: true
          })
        }).then(() => refreshBillingWindow()).catch(() => {});
        return;
      }

      openAccountModal(true);
    }

    setTimeout(initAccountState, 250);

    // =========================================================================
    // Token Billing, Top-Up & Sponsored Ads Interaction Engine
    // =========================================================================
    let isWatchingAd = false;
    let currentSponsor = {
      id: "vercel-ai",
      name: "Vercel AI SDK & MicroVMs",
      tagline: "Deploy durable agent sandboxes and AI gateways with zero server management.",
      cta: "Visit Partner ↗",
      url: "https://sdk.vercel.ai?utm_source=tincan-mesh",
      icon: "⚡",
      badge: "Sponsored",
      video_url: "/videos/7705677376465767711.mp4",
      duration_seconds: 10,
      reward_tokens: 5000,
      reward_usd: 0.05
    };

    async function loadActiveSponsor(sponsorId) {
      try {
        const url = sponsorId ? `/api/ads/sponsor?id=${encodeURIComponent(sponsorId)}` : '/api/ads/sponsor';
        const resp = await fetch(url);
        if (resp.ok) {
          const data = await resp.json();
          if (data && data.sponsor) {
            currentSponsor = data.sponsor;
            renderSponsorCard();
          }
        }
      } catch (err) {
        console.warn('Failed to load active sponsor:', err);
      }
    }

    function renderSponsorCard() {
      const nameEl = document.getElementById('adSponsorName');
      const tagEl = document.getElementById('adSponsorTagline');
      const badgeEl = document.getElementById('adSponsorBadge');
      const iconEl = document.getElementById('adSponsorIcon');
      const ctaBtn = document.getElementById('adSponsorCtaBtn');
      const titleEl = document.getElementById('adVideoTitle');

      if (nameEl) nameEl.innerText = currentSponsor.name || 'Developer Sponsor';
      if (tagEl) tagEl.innerText = currentSponsor.tagline || 'Fund free mesh AI tokens.';
      if (badgeEl) badgeEl.innerText = currentSponsor.badge || 'Sponsored';
      if (iconEl) iconEl.innerText = currentSponsor.icon || '⚡';
      if (titleEl) titleEl.innerText = currentSponsor.name || 'Sponsor Ad';
      if (ctaBtn) {
        ctaBtn.href = currentSponsor.url || '#';
        ctaBtn.innerText = currentSponsor.cta || 'Visit Partner ↗';
      }
    }

    async function fetchNextSponsor() {
      await loadActiveSponsor();
    }

    async function trackSponsorClick() {
      if (!currentSponsor || !currentSponsor.id) return;
      try {
        await fetch('/api/ads/click', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sponsor_id: currentSponsor.id })
        });
      } catch (e) {}
    }

    function openSponsorInfoModal() {
      alert("📣 Real Ads & Direct Sponsorships on TinCan:\n\n1. Direct Partner Sponsorship: Real developer brands (Railway, Vercel, Supabase) sponsor AI compute via verified video ads & click-through links.\n2. Developer Ad Networks: Integration-ready for EthicalAds (ETHICALADS_PUBLISHER_ID) and Carbon Ads.\n3. Rewarded Video Ads: Configurable Google AdSense Rewarded Ads (ADSENSE_CLIENT_ID).\n4. Community Ad Slots: Any peer can feature an ad in rotation using:\n   tincan playlist add <mp4_or_tiktok_url> --category ad");
    }

    async function refreshBillingWindow() {
      try {
        loadActiveSponsor();
        const resp = await fetch(`/api/account/billing?peer_id=${encodeURIComponent(myPeerId)}`);
        if (resp.ok) {
          const data = await resp.json();
          const tokEl = document.getElementById('billingWindowTokens');
          const credEl = document.getElementById('billingWindowCredits');
          const totalUsedEl = document.getElementById('billingTotalUsedText');
          if (tokEl) tokEl.innerText = Number(data.token_balance || 0).toLocaleString();
          if (credEl) credEl.innerText = `$${Number(data.credit_balance_usd || 0).toFixed(2)} USD`;
          if (totalUsedEl) totalUsedEl.innerText = `Total used: ${Number(data.total_tokens_used || 0).toLocaleString()} tokens ($${Number(data.total_billed_usd || 0).toFixed(4)})`;

          const pill = document.getElementById('hudTokenPill');
          const toks = Number(data.token_balance || 0);
          if (pill) {
            pill.innerText = toks >= 1000 ? `${Math.round(toks / 1000)}k 🪙` : `${toks} 🪙`;
          }
          const questsBal = document.getElementById('rewardsMintedBalance');
          if (questsBal) {
            questsBal.innerText = `${toks.toLocaleString()} $TINCAN`;
          }

          const rowsEl = document.getElementById('billingLedgerRows');
          if (rowsEl && data.recent_invoices && data.recent_invoices.length > 0) {
            rowsEl.innerHTML = data.recent_invoices.map(inv => {
              const d = new Date(inv.timestamp * 1000);
              const timeStr = `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}`;
              return `
                <tr class="hover:bg-slate-900/60 transition">
                  <td class="py-1 text-cyan-400 font-bold">${inv.model}</td>
                  <td class="py-1 text-slate-200">${Number(inv.total_tokens).toLocaleString()}</td>
                  <td class="py-1 text-emerald-400">$${Number(inv.cost_usd).toFixed(5)}</td>
                  <td class="py-1 text-right text-slate-500">${timeStr}</td>
                </tr>
              `;
            }).join('');
          }
        }
        try {
          const rResp = await fetch('/api/3d/balance');
          if (rResp.ok) {
            const rData = await rResp.json();
            const badge = document.getElementById('rodinBillingStatusBadge');
            const creds = document.getElementById('rodinBalanceCredits');
            const usd = document.getElementById('rodinBalanceUsd');
            const tasks = document.getElementById('rodinSessionTasks');
            const keyLbl = document.getElementById('rodinKeyLabel');
            if (badge) {
              badge.textContent = rData.connected ? 'ONLINE / POOLED' : 'SIMULATED / ACTIVE';
              badge.className = rData.connected ? 'px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] font-mono border border-emerald-500/40 font-bold' : 'px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 text-[10px] font-mono border border-cyan-500/40 font-bold';
            }
            if (creds) creds.textContent = (rData.account_remaining_credits || 0).toFixed(1);
            if (usd) usd.textContent = '$' + (rData.account_remaining_balance_usd || 0).toFixed(2);
            if (tasks) tasks.textContent = (rData.session_total_tasks || 0);
            if (keyLbl) keyLbl.textContent = rData.key_label || 'pooled-key';
          }
        } catch (rErr) {}
      } catch (err) {
        console.warn('Billing refresh failed:', err);
      }
    }

    let currentAdViewToken = null;

    function watchSponsoredAd() {
      if (isWatchingAd) return;
      isWatchingAd = true;
      const btn = document.getElementById('watchAdBtn');
      const videoBox = document.getElementById('adVideoContainer');
      const videoEl = document.getElementById('adVideoPlayer');
      const bar = document.getElementById('adProgressBar');
      const timerText = document.getElementById('adTimerText');
      const progressText = document.getElementById('adProgressText');

      if (btn) btn.disabled = true;
      if (videoBox) videoBox.classList.remove('hidden');
      if (bar) bar.style.width = '0%';

      const duration = currentSponsor.duration_seconds || 10;
      currentAdViewToken = null;
      fetch('/api/ads/view/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ peer_id: myPeerId, sponsor_id: currentSponsor.id })
      }).then(r => r.json()).then(d => { currentAdViewToken = d.view_token || null; if (d.error) console.warn('Ad reward unavailable:', d.error); })
        .catch(e => console.warn('Ad view start failed:', e));
      let secondsLeft = duration;
      if (timerText) timerText.innerText = `${secondsLeft}s remaining`;
      if (progressText) progressText.innerText = `Streaming ${currentSponsor.name || 'sponsor'} video...`;

      let adFinished = false;
      let interval = null;

      const completeAd = () => {
        if (adFinished) return;
        adFinished = true;
        if (interval) clearInterval(interval);
        finishSponsoredAd();
      };

      if (videoEl && currentSponsor.video_url) {
        videoEl.src = currentSponsor.video_url;
        videoEl.currentTime = 0;
        videoEl.muted = true;
        videoEl.play().catch(e => {
          console.warn('Ad video autoplay policy note:', e);
        });
        videoEl.onended = completeAd;
      }

      interval = setInterval(() => {
        secondsLeft -= 1;
        const progressPct = Math.min(100, ((duration - secondsLeft) / duration) * 100);
        if (bar) bar.style.width = `${progressPct}%`;
        if (timerText) timerText.innerText = `${Math.max(0, secondsLeft)}s remaining`;

        if (secondsLeft <= 0) {
          completeAd();
        }
      }, 1000);
    }

    async function finishSponsoredAd() {
      const videoBox = document.getElementById('adVideoContainer');
      const videoEl = document.getElementById('adVideoPlayer');
      const btn = document.getElementById('watchAdBtn');

      if (videoEl) {
        try { videoEl.pause(); } catch(e){}
      }
      if (videoBox) videoBox.classList.add('hidden');
      if (btn) btn.disabled = false;
      isWatchingAd = false;

      if (!currentAdViewToken) return;
      try {
        const resp = await fetch('/api/ads/view/complete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ peer_id: myPeerId, view_token: currentAdViewToken })
        });
        currentAdViewToken = null;
        const data = await resp.json();
        if (resp.ok) {
          const rewardTokens = data.reward_tokens || 0;
          if (sfxEnabled) playXpChime();
          awardLocalXp(50, `Sponsored Ad Watched (+${rewardTokens.toLocaleString()} Tokens)`);
          refreshBillingWindow();
          alert(`🎉 Sponsor video completed! +${rewardTokens.toLocaleString()} Free Tokens credited from ${currentSponsor.name || 'Sponsor'}.`);
        } else {
          console.warn('Ad reward not credited:', data.error);
        }
      } catch (e) {
        console.error('Failed to credit ad tokens:', e);
      }
    }

    async function buyTokens(amountUsd, tokens) {
      // Server prices the pack and returns a Stripe-hosted checkout; tokens are credited
      // only when Stripe's signed webhook confirms payment.
      const pack = `pack_${Math.round(amountUsd * 100)}`;  // price in cents: pack_100, pack_500, pack_2000
      try {
        const resp = await fetch('/api/billing/checkout', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ peer_id: myPeerId, pack: pack })
        });
        const data = await resp.json();
        if (resp.ok && data.checkout_url) {
          window.location.href = data.checkout_url;
        } else {
          alert('Checkout unavailable: ' + (data.error || resp.status));
        }
      } catch (e) {
        alert('Top-up request failed: ' + e);
      }
    }

    setTimeout(refreshBillingWindow, 1500);

    /*TC_INSTALL_CARD_JS*/

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
      const remoteTopologyPeers = (window.latestOnlinePeers || [])
        .filter(p => p && p.peer_id && p.peer_id !== myPeerId)
        .slice(0, 6);
      const peers = [
        { id: myPeerId, label: 'You (Local)', x: w * (remoteTopologyPeers.length ? 0.32 : 0.5), y: h * 0.70 },
        ...remoteTopologyPeers.map((p, idx) => ({
          id: p.peer_id,
          label: p.display_name || p.peer_id,
          x: w * Math.min(0.84, 0.50 + idx * 0.14),
          y: h * (idx % 2 === 0 ? 0.74 : 0.66)
        }))
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
    // Multiplayer Cursor Telemetry (Throttled, Visibility & Identity-Gated)
    // =========================================================================
    let lastCursorSend = 0;
    let lastCursorX = -1;
    let lastCursorY = -1;
    window.addEventListener('mousemove', (e) => {
      if (document.hidden || !isIdentityVerified()) return;
      const now = Date.now();
      const dx = Math.abs(e.clientX - lastCursorX);
      const dy = Math.abs(e.clientY - lastCursorY);
      if (now - lastCursorSend > 280 && (dx >= 4 || dy >= 4)) {
        lastCursorSend = now;
        lastCursorX = e.clientX;
        lastCursorY = e.clientY;
        fetch('/api/mesh/cursor', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            display_name: getVerifiedDisplayName(),
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
    // AI Brain Arena: pickers, duel, voting and per-brain context live in arena_duel_ui.py
    // =========================================================================

    const peerRttMap = {};
    const pendingPings = {};
    let directMsgTargetPeer = null;
    let directMsgTargetLabel = '';

    function formatSeenAge(epochSec) {
      if (!epochSec) return 'just now';
      const diff = Math.max(0, Math.round(Date.now() / 1000 - Number(epochSec)));
      if (diff <= 5) return 'just now';
      if (diff < 60) return `${diff}s ago`;
      return `${Math.round(diff / 60)}m ago`;
    }

    async function pingNetworkPeer(targetPeerId, label) {
      if (!targetPeerId) return;
      if (targetPeerId === myPeerId) {
        if (typeof showQuickNotification === 'function') showQuickNotification('● Local session online (0ms)');
        return;
      }
      const room = (document.getElementById('roomInput') && document.getElementById('roomInput').value.trim()) || currentRoom || 'main';
      pendingPings[targetPeerId] = performance.now();
      spawnPacketFlight(myPeerId, targetPeerId, 'ping', 'PING');
      try {
        await fetch('/api/webrtc/signal', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            from: myPeerId,
            to: targetPeerId,
            type: 'ping',
            room,
            payload: {
              sent_at: Date.now(),
              sender: typeof getVerifiedDisplayName === 'function' ? getVerifiedDisplayName() : myPeerId
            }
          })
        });
        if (typeof showQuickNotification === 'function') {
          showQuickNotification(`📡 Ping sent to ${label || targetPeerId}`);
        }
      } catch (e) {
        if (typeof showQuickNotification === 'function') showQuickNotification(`⚠️ Ping failed for ${label || targetPeerId}`);
      }
    }

    function openPeerMessage(targetPeerId, label) {
      if (!targetPeerId) return;
      if (typeof requireVerifiedIdentity === 'function' && !requireVerifiedIdentity('send direct messages to peers')) return;
      directMsgTargetPeer = targetPeerId;
      directMsgTargetLabel = label || targetPeerId;
      const drawer = document.getElementById('netMessageDrawer');
      const lbl = document.getElementById('netMsgTargetLabel');
      const inp = document.getElementById('netMsgInput');
      if (lbl) lbl.innerText = `${directMsgTargetLabel} (${directMsgTargetPeer})`;
      if (drawer) drawer.classList.remove('hidden');
      if (inp) { inp.value = ''; inp.focus(); }
    }

    function closePeerMessage() {
      directMsgTargetPeer = null;
      const drawer = document.getElementById('netMessageDrawer');
      if (drawer) drawer.classList.add('hidden');
    }

    async function sendDirectPeerMessage() {
      if (!directMsgTargetPeer) return;
      if (typeof requireVerifiedIdentity === 'function' && !requireVerifiedIdentity('send direct messages to peers')) return;
      const inp = document.getElementById('netMsgInput');
      const text = inp ? inp.value.trim() : '';
      if (!text) return;
      inp.value = '';
      const room = (document.getElementById('roomInput') && document.getElementById('roomInput').value.trim()) || currentRoom || 'main';
      const senderLabel = typeof getVerifiedDisplayName === 'function' ? getVerifiedDisplayName() : myPeerId;
      try {
        await fetch('/api/webrtc/signal', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            from: myPeerId,
            to: directMsgTargetPeer,
            type: 'chat',
            room,
            payload: {
              text: `[DM] ${text}`,
              sender: senderLabel,
              target: directMsgTargetPeer,
              direct: true,
              timestamp: Date.now()
            }
          })
        });
        if (typeof appendChatMessage === 'function') {
          appendChatMessage(`${senderLabel} → ${directMsgTargetLabel}`, text, true, Date.now());
        }
        if (typeof showQuickNotification === 'function') {
          showQuickNotification(`✉️ Direct message sent to ${directMsgTargetLabel}`);
        }
        closePeerMessage();
      } catch (e) {
        if (typeof showQuickNotification === 'function') showQuickNotification('⚠️ Failed to send direct message');
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
        if (typeof showQuickNotification === 'function') {
          if (data && data.status === 'already_completed') {
            showQuickNotification('✓ Sign-on onboarding step already claimed for this peer.');
          } else {
            showQuickNotification('🌱 Sign-on onboarding step completed!');
          }
        }
        pollMeshState();
      } catch (e) {}
    }

    // =========================================================================
    // Polling Loop: State, Quests, Leaderboard & Readiness Progression
    // =========================================================================
    async function pollMeshState(force = false) {
      if (!force && document.hidden) return;
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
        const squadXp = state.xp !== undefined ? state.xp : (state.squad_xp || 0);
        const targetXp = state.tier?.next_tier_xp || state.tier?.target_xp || 200;
        const pct = Math.min(100, Math.round((squadXp / targetXp) * 100));
        document.getElementById('osXpBar').style.width = `${pct}%`;
        document.getElementById('osXpText').innerText = `${squadXp.toLocaleString()} / ${targetXp.toLocaleString()} XP`;

        const streamsArr = Array.isArray(state.active_webrtc_streams) ? state.active_webrtc_streams : [];
        const onlinePeers = streamsArr.filter(s => s && s.is_online !== false);
        window.latestOnlinePeers = onlinePeers;
        const count = (state.peers_count !== undefined && state.peers_count !== null)
          ? Number(state.peers_count)
          : onlinePeers.length;
        const osCountEl = document.getElementById('osPeerCountNum');
        if (osCountEl) osCountEl.innerText = count;
        const netWinBadgeEl = document.getElementById('netWinActiveNum');
        if (netWinBadgeEl) netWinBadgeEl.innerText = count;
        const netMetricPeersEl = document.getElementById('netMetricPeers');
        if (netMetricPeersEl) netMetricPeersEl.innerText = count;

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

        // Update Leaderboard in both win-quests and standalone win-network
        if (state.leaderboard && Array.isArray(state.leaderboard)) {
          const renderLdRows = (rows) => {
            if (!rows || rows.length === 0) {
              return '<tr><td colspan="5" class="px-3 py-3 text-center text-slate-500">No operator sessions recorded yet.</td></tr>';
            }
            return rows.map((p, idx) => `
              <tr>
                <td class="px-3 py-2 text-${idx === 0 ? 'amber-400' : 'slate-400'} font-bold">#${idx + 1}</td>
                <td class="px-3 py-2 text-white font-bold">${escapeHtml(p.display_name || p.peer_id)}</td>
                <td class="px-3 py-2 text-emerald-400">${escapeHtml(p.tier || 'L1: Isolated Node')}</td>
                <td class="px-3 py-2">
                  ${(p.badges || []).length > 0 ? p.badges.map(b => `<span class="px-1.5 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-700 text-[10px] mr-1">${escapeHtml(b)}</span>`).join('') : '<span class="text-slate-500 text-[10px]">—</span>'}
                </td>
                <td class="px-3 py-2 text-right text-cyan-300 font-bold">${(p.xp || 0).toLocaleString()} XP</td>
              </tr>
            `).join('');
          };

          const tbody = document.getElementById('operatorLeaderboard');
          if (tbody) tbody.innerHTML = renderLdRows(state.leaderboard);

          const tbodyStandalone = document.getElementById('operatorLeaderboardStandalone');
          if (tbodyStandalone) tbodyStandalone.innerHTML = renderLdRows(state.leaderboard);

          const topRank = state.leaderboard[0];
          const topXpEl = document.getElementById('netMetricTopXp');
          if (topXpEl) {
            topXpEl.innerText = topRank ? `${(topRank.xp || 0).toLocaleString()} XP` : '0 XP';
          }

          // Mark any one-time sign-on quests completed by current peer
          const myBoardRow = state.leaderboard.find(p => p.peer_id === myPeerId);
          const completedSet = new Set((myBoardRow && myBoardRow.completed_quests) || []);
          ['sealed_courier', 'arena_vote', 'coop_action'].forEach(qk => {
            const btnEl = document.getElementById(`questBtn-${qk}`);
            const badgeEl = document.getElementById(`questBadge-${qk}`);
            const done = completedSet.has(qk);
            if (badgeEl && done) {
              badgeEl.textContent = '✓ Claimed';
              badgeEl.className = 'text-[10px] bg-slate-900 text-emerald-400 border border-emerald-700 px-1.5 py-0.5 rounded font-mono';
            }
            if (btnEl && done) {
              btnEl.disabled = true;
              btnEl.classList.add('opacity-50', 'cursor-not-allowed');
              btnEl.textContent = '✓ Sign-On Completed (1x)';
            }
          });
        }

        // Update win-network Mesh Peers Roster (real peers only — never hardcoded seed nodes)
        const netPeersListEl = document.getElementById('netPeersList');
        if (netPeersListEl) {
          if (onlinePeers.length === 0) {
            netPeersListEl.innerHTML = `
              <div class="p-3 bg-slate-950/70 border border-slate-800 rounded-lg text-center text-slate-400 text-xs">
                No mesh peers currently online in room "${escapeHtml(currentRoom)}". Join WebRTC or run <code class="text-emerald-300">tincan start</code> on a peer node.
              </div>
            `;
          } else {
            netPeersListEl.innerHTML = onlinePeers.map(p => {
              const peerId = p.peer_id || '';
              const label = p.display_name || peerId || 'Mesh Peer';
              const isLocal = peerId === myPeerId;
              const isOnline = p.is_online !== false;
              const caps = [];
              if (p.has_video) caps.push('Video');
              if (p.has_audio) caps.push('Audio');
              if (p.has_screen) caps.push('Screen');
              const hasMedia = caps.length > 0 || Boolean(p.has_live_media);
              const statusText = isOnline
                ? (hasMedia ? `Online · Live Media (${caps.join(', ')})` : 'Online · Relay Connected')
                : 'Offline';
              const rttMs = peerRttMap[peerId];
              const rightTelemetry = rttMs !== undefined
                ? `${rttMs}ms RTT`
                : `Seen ${formatSeenAge(p.last_seen || p.connected_at)}`;
              return `
                <div class="p-3 bg-slate-950/80 border border-slate-800 rounded-lg space-y-1.5 hover:border-slate-700 transition">
                  <div class="flex items-center justify-between gap-2">
                    <span class="text-xs font-bold text-white flex items-center gap-1.5">
                      <span>🖥️</span> <span>${escapeHtml(label)}</span>
                      ${isLocal ? '<span class="text-[10px] text-cyan-400 font-normal">(you)</span>' : ''}
                    </span>
                    <span class="px-1.5 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-700 text-[10px]">
                      Room: ${escapeHtml(p.room || currentRoom || 'main')}
                    </span>
                  </div>
                  <div class="flex items-center justify-between text-[11px] text-slate-400">
                    <span class="${isOnline ? 'text-emerald-400' : 'text-slate-500'}">${isOnline ? '●' : '○'} ${escapeHtml(statusText)}</span>
                    <span class="font-mono text-cyan-300">${escapeHtml(rightTelemetry)}</span>
                  </div>
                  <div class="flex flex-wrap items-center gap-1.5 pt-1 border-t border-slate-800/80 text-[10px]">
                    <button onclick="pingNetworkPeer('${escapeHtml(peerId)}', '${escapeHtml(label)}')" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 transition active:scale-95">📡 Ping</button>
                    <button onclick="openPeerMessage('${escapeHtml(peerId)}', '${escapeHtml(label)}')" class="px-2 py-0.5 rounded bg-indigo-950/80 hover:bg-indigo-900 text-indigo-200 border border-indigo-800 transition active:scale-95">✉️ Message</button>
                    ${!isLocal ? `<button onclick="startDirectCall('${escapeHtml(peerId)}')" class="px-2 py-0.5 rounded bg-emerald-900/80 hover:bg-emerald-800 text-emerald-200 border border-emerald-700 transition active:scale-95">📞 Call</button>` : ''}
                    ${hasMedia ? `<button onclick="toggleWindow('win-comms')" class="px-2 py-0.5 rounded bg-cyan-950/80 hover:bg-cyan-900 text-cyan-300 border border-cyan-800 transition active:scale-95">📺 View Stream</button>` : ''}
                  </div>
                </div>
              `;
            }).join('');
          }
        }

        const cursorsArr = Array.isArray(state.cursors) ? state.cursors : Object.values(state.cursors || {});
        const visitorsCount = cursorsArr.length;
        const netMetricVisitorsEl = document.getElementById('netMetricVisitors');
        if (netMetricVisitorsEl) netMetricVisitorsEl.innerText = visitorsCount;

        const netVisitorsListEl = document.getElementById('netVisitorsList');
        if (netVisitorsListEl) {
          if (cursorsArr.length === 0) {
            netVisitorsListEl.innerHTML = `
              <div class="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg text-slate-400 text-xs text-center">
                No active web visitors right now.
              </div>
            `;
          } else {
            const nowSec = Date.now() / 1000;
            netVisitorsListEl.innerHTML = cursorsArr.map(c => {
              const peerId = c.peer_id || '';
              const label = c.user || c.display_name || peerId || 'Web Visitor';
              const isLocal = peerId === myPeerId;
              const ageSec = Math.max(0, Math.round(nowSec - (c.updated_at || nowSec)));
              const onlineBadge = ageSec <= 20
                ? '<span class="text-emerald-400">● Online</span>'
                : `<span class="text-yellow-400">◐ ${ageSec}s ago</span>`;
              const rttTag = peerRttMap[peerId] !== undefined
                ? `<span class="text-[10px] text-cyan-300 font-mono">${peerRttMap[peerId]}ms</span>`
                : '';
              return `
                <div class="p-2.5 bg-slate-950/70 border border-slate-800 rounded-lg space-y-1.5 text-[11px]">
                  <div class="flex items-center justify-between gap-2">
                    <div class="flex items-center gap-2 min-w-0">
                      <span class="w-2 h-2 rounded-full shrink-0" style="background-color: ${c.color || '#38bdf8'}"></span>
                      <span class="text-white font-bold truncate">${escapeHtml(label)}</span>
                      ${isLocal ? '<span class="text-[10px] text-cyan-400">(you)</span>' : ''}
                    </div>
                    <div class="flex items-center gap-2 shrink-0 text-[10px]">
                      ${rttTag}
                      ${onlineBadge}
                      <span class="text-slate-400 font-mono">${escapeHtml(c.window_id || c.focused_window || 'desktop')}</span>
                    </div>
                  </div>
                  <div class="flex items-center justify-end gap-1.5 pt-1 border-t border-slate-800/60 text-[10px]">
                    <button onclick="pingNetworkPeer('${escapeHtml(peerId)}', '${escapeHtml(label)}')" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 transition active:scale-95">📡 Ping</button>
                    ${!isLocal ? `<button onclick="openPeerMessage('${escapeHtml(peerId)}', '${escapeHtml(label)}')" class="px-2 py-0.5 rounded bg-indigo-950/80 hover:bg-indigo-900 text-indigo-200 border border-indigo-800 transition active:scale-95">✉️ Message</button>` : '<span class="text-slate-500 px-1.5">Local tab</span>'}
                  </div>
                </div>
              `;
            }).join('');
          }
        }

        // Populate customer peer suggestions for Admin Minting console
        const dl = document.getElementById('adminMintPeerSuggestions');
        if (dl) {
          const seenIds = new Set();
          [myPeerId, ...onlinePeers.map(p => p.peer_id), ...cursorsArr.map(c => c.peer_id)].forEach(id => {
            if (id) seenIds.add(id);
          });
          dl.innerHTML = Array.from(seenIds).map(id => `<option value="${escapeHtml(id)}">`).join('');
        }

        // Update Moderator Panel Rosters
        const modWebCountEl = document.getElementById('modWebCount');
        const modMeshCountEl = document.getElementById('modMeshCount');
        const modWebTagEl = document.getElementById('modWebVisitorsCountTag');
        const modMeshTagEl = document.getElementById('modMeshNodesCountTag');

        if (modWebCountEl) modWebCountEl.innerText = cursorsArr.length;
        if (modMeshCountEl) modMeshCountEl.innerText = onlinePeers.length;
        if (modWebTagEl) modWebTagEl.innerText = `${cursorsArr.length} connected`;
        if (modMeshTagEl) modMeshTagEl.innerText = `${onlinePeers.length} online`;

        const webTbody = document.getElementById('modWebVisitorsTable');
        if (webTbody) {
          if (cursorsArr.length === 0) {
            webTbody.innerHTML = '<tr><td colspan="6" class="px-3 py-3 text-center text-slate-500 text-[11px]">No active web cursors detected</td></tr>';
          } else {
            const now = Date.now() / 1000;
            webTbody.innerHTML = cursorsArr.map(c => {
              const diff = Math.max(0, Math.round(now - (c.updated_at || now)));
              const isLocal = c.peer_id === myPeerId;
              const badge = diff <= 15 ? '<span class="text-emerald-400 font-bold">● Active</span>' :
                            diff <= 60 ? `<span class="text-yellow-400">◐ ${diff}s ago</span>` :
                            `<span class="text-slate-500">○ ${diff}s ago</span>`;
              return `
                <tr class="hover:bg-slate-800/40 transition">
                  <td class="px-2.5 py-1.5 text-white font-bold">${escapeHtml(c.display_name || c.peer_id)} <span class="text-[10px] text-slate-400 font-mono">(${escapeHtml(c.peer_id)})</span> ${isLocal ? '<span class="text-[10px] text-cyan-400">(you)</span>' : ''}</td>
                  <td class="px-2.5 py-1.5 text-slate-300">${c.room || 'main'}</td>
                  <td class="px-2.5 py-1.5 text-slate-400">${c.window_id || 'desktop'}</td>
                  <td class="px-2.5 py-1.5 text-slate-400 font-mono">(${Math.round(c.x || 0)}, ${Math.round(c.y || 0)})</td>
                  <td class="px-2.5 py-1.5">${badge}</td>
                  <td class="px-2.5 py-1.5 text-right">
                    ${!isLocal ? `<button onclick="kickPeerNode('${c.peer_id}', '${c.room || 'main'}')" class="px-2 py-0.5 rounded bg-red-950/80 hover:bg-red-800 text-red-300 border border-red-800 text-[10px] font-bold transition">⛔ Kick</button>` : '<span class="text-slate-600 text-[10px]">Host</span>'}
                  </td>
                </tr>
              `;
            }).join('');
          }
        }

        const meshTbody = document.getElementById('modMeshNodesTable');
        if (meshTbody) {
          if (streamsArr.length === 0) {
            meshTbody.innerHTML = '<tr><td colspan="6" class="px-3 py-3 text-center text-slate-500 text-[11px]">No active WebRTC / workstation streams</td></tr>';
          } else {
            meshTbody.innerHTML = streamsArr.map(s => {
              const isLocal = s.peer_id === myPeerId;
              const caps = [];
              if (s.has_video) caps.push('📹 Video');
              if (s.has_audio) caps.push('🎙️ Voice');
              if (s.has_screen) caps.push('🖥️ Screen');
              if (caps.length === 0) caps.push('⚡ Signaling');
              return `
                <tr class="hover:bg-slate-800/40 transition">
                  <td class="px-2.5 py-1.5 text-cyan-300 font-bold">${s.peer_id} ${isLocal ? '<span class="text-[10px] text-cyan-400">(you)</span>' : ''}</td>
                  <td class="px-2.5 py-1.5 text-white">${s.display_name || s.peer_id}</td>
                  <td class="px-2.5 py-1.5 text-slate-300">${s.room || 'main'}</td>
                  <td class="px-2.5 py-1.5 text-slate-400">${caps.join(', ')}</td>
                  <td class="px-2.5 py-1.5 text-slate-400 font-mono">UDP/${s.udp_port || 'auto'}</td>
                  <td class="px-2.5 py-1.5 text-right">
                    ${!isLocal ? `<button onclick="kickPeerNode('${s.peer_id}', '${s.room || 'main'}')" class="px-2 py-0.5 rounded bg-red-950/80 hover:bg-red-800 text-red-300 border border-red-800 text-[10px] font-bold transition">⛔ Disconnect</button>` : '<span class="text-slate-600 text-[10px]">Host</span>'}
                  </td>
                </tr>
              `;
            }).join('');
          }
        }
      } catch (e) {}
    }

    setInterval(() => pollMeshState(false), 4000);
    pollMeshState(true);

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
      } else if (msg.type === 'WINDOW_POPOUT' && msg.winId) {
        if (!singleWindowParam) {
          setWindowPoppedOut(msg.winId, true);
        }
      } else if (msg.type === 'WINDOW_REDOCK' && msg.winId) {
        if (!singleWindowParam) {
          setWindowPoppedOut(msg.winId, false);
        }
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

    function startDirectCall(peerId) {
      toggleWindow('win-call');
      const roomEl = document.getElementById('roomInput');
      if (roomEl && peerId && !roomEl.value.trim()) {
        roomEl.value = 'main';
      }
      startCall('video');
    }

    async function startCall(mode = 'video') {
      if (!requireVerifiedIdentity('join a live WebRTC call')) return;
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
            display_name: getVerifiedDisplayName(),
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
      if (!requireVerifiedIdentity('share your screen in a room')) return;
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
            display_name: getVerifiedDisplayName() + ' (Screen)',
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

    async function pollSignals(force = false) {
      if (!force && document.hidden && !pc) return;
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
          } else if (sig.type === 'chat' || sig.type === 'message') {
            const sigKey = `${sig.seq || ''}-${sig.from}-${sig.timestamp || ''}`;
            if (!seenChatIds.has(sigKey)) {
              seenChatIds.add(sigKey);
              const payload = sig.payload && typeof sig.payload === 'object' ? sig.payload : {};
              const txt = (payload && (payload.text || payload.message)) || (typeof sig.payload === 'string' ? sig.payload : '');
              const sender = (payload && payload.sender) || sig.from || 'Peer';
              const targetKey = sig.to && sig.to !== '*'
                ? `dm:${sig.from === myPeerId ? sig.to : sig.from}`
                : `channel:${payload.channel || sig.room || 'main'}`;
              if (txt && sig.from !== myPeerId) {
                appendChatMessage(sender, txt, false, sig.timestamp ? sig.timestamp * 1000 : null, targetKey);
                playXpChime();
              }
            }
          } else if (sig.type === 'admin_broadcast') {
            const sigKey = `admin-${sig.seq || ''}-${sig.from}-${sig.timestamp || ''}`;
            if (!seenChatIds.has(sigKey)) {
              seenChatIds.add(sigKey);
              const txt = (sig.payload && (sig.payload.text || sig.payload.message)) || (typeof sig.payload === 'string' ? sig.payload : '');
              showAdminBanner(txt, sig.from);
              playXpChime();
            }
          } else if (sig.type === 'verification_form') {
            const sigKey = `verify-${sig.seq || ''}-${sig.from}-${sig.timestamp || ''}`;
            if (!seenChatIds.has(sigKey)) {
              seenChatIds.add(sigKey);
              playXpChime();
              const winEl = document.getElementById('win-board');
              if (winEl && winEl.classList.contains('hidden')) {
                toggleWindow('win-board');
              }
              switchBoardTab('verify');
              if (sig.payload) {
                prefillVerificationFormFromSignal(sig.payload);
              }
            }
          } else if (sig.type === 'board_event') {
            const sigKey = `board-${sig.seq || ''}-${sig.from}-${sig.timestamp || ''}`;
            if (!seenChatIds.has(sigKey)) {
              seenChatIds.add(sigKey);
              loadCyberspaceBoard();
            }
          } else if (sig.type === 'ping') {
            const sigKey = `ping-${sig.seq || ''}-${sig.from}-${sig.timestamp || ''}`;
            if (!seenChatIds.has(sigKey)) {
              seenChatIds.add(sigKey);
              const sender = (sig.payload && sig.payload.sender) || sig.from || 'Peer';
              if (typeof showQuickNotification === 'function') {
                showQuickNotification(`📡 Ping received from ${sender} — replying pong`);
              }
              if (typeof sendSignal === 'function') {
                sendSignal('pong', {
                  sent_at: sig.payload && sig.payload.sent_at,
                  responder: typeof getVerifiedDisplayName === 'function' ? getVerifiedDisplayName() : myPeerId
                }, sig.from);
              }
            }
          } else if (sig.type === 'pong') {
            const sigKey = `pong-${sig.seq || ''}-${sig.from}-${sig.timestamp || ''}`;
            if (!seenChatIds.has(sigKey)) {
              seenChatIds.add(sigKey);
              const sentPerf = pendingPings[sig.from];
              const rttMs = sentPerf
                ? Math.max(1, Math.round(performance.now() - sentPerf))
                : ((sig.payload && sig.payload.sent_at) ? Math.max(1, Math.round(Date.now() - Number(sig.payload.sent_at))) : null);
              delete pendingPings[sig.from];
              if (rttMs !== null) {
                peerRttMap[sig.from] = rttMs;
              }
              const responder = (sig.payload && sig.payload.responder) || sig.from || 'Peer';
              if (typeof showQuickNotification === 'function') {
                showQuickNotification(`✅ Pong from ${responder}${rttMs !== null ? ` (${rttMs}ms RTT)` : ''}`);
              }
              pollMeshState(true);
            }
          }
        }
      } catch (e) {}
    }
    pollTimer = setInterval(() => pollSignals(false), 3000);

    // =========================================================================
    // Live Mesh & Peer Chat Engine (Discord-Style Channels + Room People DMs)
    // =========================================================================
    let chatMsgCount = 0;
    const seenChatIds = new Set();
    const chatStreamsByTarget = new Map();
    const customChatChannels = ['main', 'architecture', 'cyberspace', 'arena'];
    let activeChatTarget = { mode: 'channel', id: 'main', label: '#main', peerId: '' };

    function escapeHtml(str) {
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }

    function _activeChatKey() {
      return activeChatTarget.mode === 'direct'
        ? `dm:${activeChatTarget.peerId || activeChatTarget.id}`
        : `channel:${activeChatTarget.id || 'main'}`;
    }

    function _renderActiveChatStream() {
      const list = document.getElementById('chatMessagesList');
      if (!list) return;
      const key = _activeChatKey();
      const rows = chatStreamsByTarget.get(key) || [];
      const counter = document.getElementById('chatCounterBadge');
      if (counter) counter.innerText = `${rows.length} message${rows.length === 1 ? '' : 's'}`;
      if (!rows.length) {
        const emptyLabel = activeChatTarget.mode === 'direct'
          ? `No direct sealed messages with ${activeChatTarget.label || activeChatTarget.peerId} yet.`
          : `No messages in #${activeChatTarget.id || 'main'} yet. Say hello to peers in the room.`;
        list.innerHTML = `<div class="text-slate-500 text-[11px] italic">${escapeHtml(emptyLabel)}</div>`;
        return;
      }
      list.innerHTML = '';
      for (const m of rows) {
        const timeStr = new Date(m.timestamp || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const row = document.createElement('div');
        row.className = `p-2 rounded text-xs font-mono border transition-all ${m.isMe ? 'bg-cyan-950/40 border-cyan-800/60 ml-4' : 'bg-slate-900/90 border-slate-800 mr-4'}`;
        row.innerHTML = `
          <div class="flex items-center justify-between text-[10px] text-slate-400 mb-0.5">
            <span class="font-bold ${m.isMe ? 'text-cyan-300' : 'text-emerald-400'}">${escapeHtml(m.sender)}${m.isMe ? ' (you)' : ''}</span>
            <span class="text-[9px] text-slate-500">${timeStr}</span>
          </div>
          <div class="text-slate-100 break-words leading-relaxed">${escapeHtml(m.text)}</div>
        `;
        list.appendChild(row);
      }
      list.scrollTop = list.scrollHeight;
    }

    function _renderChatChannelsSidebar() {
      const host = document.getElementById('chatChannelsList');
      if (!host) return;
      const curKey = _activeChatKey();
      host.innerHTML = customChatChannels.map((ch) => {
        const active = curKey === `channel:${ch}`;
        const cls = active
          ? 'bg-cyan-950/80 border border-cyan-700/70 text-cyan-200 font-bold'
          : 'text-slate-300 hover:bg-slate-900';
        return `<button type="button" data-channel="${escapeHtml(ch)}" onclick="selectChatTarget('channel', '${escapeHtml(ch)}', '#${escapeHtml(ch)}')" class="w-full text-left px-2 py-1 rounded ${cls} text-[11px] flex items-center justify-between">#${escapeHtml(ch)}</button>`;
      }).join('');
    }

    function onChatModeSelectChange(mode) {
      const dmInput = document.getElementById('chatDirectPeerInput');
      if (mode === 'direct') {
        if (dmInput) dmInput.classList.remove('hidden');
        const targetPeer = (dmInput && dmInput.value.trim()) || activeChatTarget.peerId || '';
        activeChatTarget = { mode: 'direct', id: targetPeer, peerId: targetPeer, label: targetPeer || 'Direct Peer' };
      } else {
        if (dmInput) dmInput.classList.add('hidden');
        const ch = activeChatTarget.mode === 'channel' ? (activeChatTarget.id || 'main') : 'main';
        activeChatTarget = { mode: 'channel', id: ch, label: '#' + ch, peerId: '' };
      }
      _updateChatBannerAndInputs();
      _renderChatChannelsSidebar();
      _renderActiveChatStream();
    }

    function _updateChatBannerAndInputs() {
      const banner = document.getElementById('chatActiveTargetBanner');
      const sel = document.getElementById('chatChannelSelect');
      const dmInput = document.getElementById('chatDirectPeerInput');
      const chatInput = document.getElementById('chatInput');
      const isDirect = activeChatTarget.mode === 'direct';
      if (sel) sel.value = isDirect ? 'direct' : 'room';
      if (dmInput) {
        dmInput.classList.toggle('hidden', !isDirect);
        if (isDirect && activeChatTarget.peerId) dmInput.value = activeChatTarget.peerId;
      }
      if (banner) {
        banner.innerText = isDirect
          ? `🔒 DM · ${activeChatTarget.label || activeChatTarget.peerId || 'Select person'}`
          : `#${activeChatTarget.id || 'main'} · Broadcast`;
      }
      if (chatInput) {
        chatInput.placeholder = isDirect
          ? `Sealed DM to ${activeChatTarget.label || activeChatTarget.peerId || 'peer'}...`
          : `Message #${activeChatTarget.id || 'main'}...`;
      }
    }

    function selectChatTarget(mode, id, label) {
      if (mode === 'direct') {
        activeChatTarget = { mode: 'direct', id, peerId: id, label: label || id };
      } else {
        const clean = String(id || 'main').replace(/^#+/, '').toLowerCase() || 'main';
        if (!customChatChannels.includes(clean)) customChatChannels.push(clean);
        activeChatTarget = { mode: 'channel', id: clean, label: '#' + clean, peerId: '' };
      }
      _updateChatBannerAndInputs();
      _renderChatChannelsSidebar();
      _renderActiveChatStream();
      if (typeof notifyParentInstanceTitle === 'function') {
        notifyParentInstanceTitle(activeChatTarget.mode === 'direct' ? ('DM ' + (activeChatTarget.label || activeChatTarget.peerId)) : ('#' + activeChatTarget.id));
      }
    }
    window.selectChatTarget = selectChatTarget;
    window.onChatModeSelectChange = onChatModeSelectChange;

    function promptNewChatChannel() {
      const name = window.prompt('Create encrypted mesh channel (e.g. research, ops):', 'research');
      if (!name) return;
      const slug = name.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '-').replace(/^-+|-+$/g, '');
      if (!slug) return;
      selectChatTarget('channel', slug, '#' + slug);
    }
    window.promptNewChatChannel = promptNewChatChannel;

    async function refreshCommsPeopleRoster() {
      const host = document.getElementById('chatPeopleList');
      if (!host) return;
      try {
        const [meshRes, rosterRes] = await Promise.all([
          fetch(`/api/mesh/state?room=${encodeURIComponent(currentRoom)}`).catch(() => null),
          fetch('/api/board/roster').catch(() => null),
        ]);
        const merged = new Map();
        if (meshRes && meshRes.ok) {
          const st = await meshRes.json();
          const peersObj = (st && st.peers) || {};
          for (const [pid, info] of Object.entries(peersObj)) {
            if (!pid) continue;
            merged.set(pid, {
              peer_id: pid,
              label: (info && (info.display_name || info.name || info.username)) || pid,
              online: true,
              role: (info && info.role) || 'Peer',
            });
          }
        }
        if (rosterRes && rosterRes.ok) {
          const rd = await rosterRes.json();
          for (const u of (rd.users || [])) {
            const id = String(u.peer_id || u.username || '').trim();
            if (!id) continue;
            const handle = String(u.username || id).replace(/^@+/, '');
            if (!merged.has(id)) {
              merged.set(id, {
                peer_id: id,
                label: '@' + handle,
                online: !!u.verified,
                role: u.role || 'Peer',
              });
            }
          }
        }
        const entries = Array.from(merged.values()).filter((p) => p.peer_id !== myPeerId);
        if (!entries.length) {
          host.innerHTML = '<div class="text-[10px] text-slate-500 italic">No other peers in room yet.</div>';
          return;
        }
        const curKey = _activeChatKey();
        host.innerHTML = entries.map((p) => {
          const active = curKey === `dm:${p.peer_id}`;
          const cls = active
            ? 'bg-emerald-950/80 border border-emerald-600/80 text-emerald-200 font-bold'
            : 'text-slate-300 hover:bg-slate-900';
          const dot = p.online ? 'bg-emerald-400' : 'bg-slate-500';
          return `<button type="button" data-dm-peer="${escapeHtml(p.peer_id)}" onclick="selectChatTarget('direct', '${escapeHtml(p.peer_id)}', '${escapeHtml(p.label)}')" class="w-full text-left px-2 py-1 rounded ${cls} text-[11px] flex items-center gap-1.5 truncate" title="Direct sealed chat with ${escapeHtml(p.peer_id)}"><span class="w-1.5 h-1.5 rounded-full ${dot} shrink-0"></span><span class="truncate">${escapeHtml(p.label)}</span></button>`;
        }).join('');
      } catch (e) {}
    }
    window.refreshCommsPeopleRoster = refreshCommsPeopleRoster;

    function appendChatMessage(sender, text, isMe = false, timestamp = null, targetKey = null) {
      chatMsgCount++;
      const key = targetKey || _activeChatKey();
      const arr = chatStreamsByTarget.get(key) || [];
      arr.push({ sender, text, isMe, timestamp: timestamp || Date.now() });
      chatStreamsByTarget.set(key, arr.slice(-150));
      if (key === _activeChatKey()) {
        _renderActiveChatStream();
      }
    }

    async function sendChatMessage() {
      if (!requireVerifiedIdentity('send messages in the room chat')) return;
      const input = document.getElementById('chatInput');
      if (!input) return;
      const text = input.value.trim();
      if (!text) return;
      input.value = '';
      const modeSel = document.getElementById('chatChannelSelect');
      const dmInp = document.getElementById('chatDirectPeerInput');
      const isDirect = (modeSel && modeSel.value === 'direct') || activeChatTarget.mode === 'direct';
      const recipientPeer = isDirect ? ((dmInp && dmInp.value.trim()) || activeChatTarget.peerId || '*').trim() : '*';
      const channelId = isDirect ? 'direct' : (activeChatTarget.id || 'main');
      const targetKey = isDirect && recipientPeer !== '*' ? `dm:${recipientPeer}` : `channel:${channelId}`;
      const room = document.getElementById('roomInput').value.trim() || 'main';
      const senderLabel = getVerifiedDisplayName();

      appendChatMessage(senderLabel, text, true, Date.now(), targetKey);
      playXpChime();

      try {
        await fetch('/api/webrtc/signal', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            from: myPeerId,
            to: recipientPeer || '*',
            type: 'chat',
            room: room,
            payload: {
              text: text,
              sender: senderLabel,
              channel: channelId,
              recipient: recipientPeer,
              timestamp: Date.now()
            }
          })
        });
      } catch (err) {
        console.error('Failed to send chat message:', err);
      }
    }
    setTimeout(() => { refreshCommsPeopleRoster(); }, 900);
    setInterval(() => {
      const w = document.getElementById('win-comms');
      if (w && !w.classList.contains('hidden')) refreshCommsPeopleRoster();
    }, 10000);

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

    async function loadAnalytics(force = false) {
      if (!force && document.hidden) return;
      try {
        const res = await fetch('/api/models/analytics');
        const data = await res.json();
        const or = data.openrouter || {};

        const orGrid = document.getElementById('orStatGrid');
        const orEmpty = document.getElementById('orDashEmpty');
        if (orGrid && orEmpty) {
          orGrid.classList.toggle('hidden', !or.connected);
          orEmpty.classList.toggle('hidden', !!or.connected);
          const why = document.getElementById('orDashEmptyReason');
          if (why && !or.connected && or.error) why.textContent = `OpenRouter did not answer: ${String(or.error).slice(0, 140)}.`;
        }
        if (or.connected) {
          document.getElementById('orRemaining').innerText = `$${Number(or.account_remaining_balance_usd).toFixed(4)}`;
          document.getElementById('orCreditsTotal').innerText = `of $${Number(or.account_total_credits_usd).toFixed(2)} total credits`;
          document.getElementById('orTotalUsage').innerText = `$${Number(or.account_total_usage_usd).toFixed(4)}`;
          document.getElementById('orKeyUsage').innerText = `$${Number(or.key_usage_total_usd).toFixed(6)}`;
          document.getElementById('orKeyToday').innerText = `Today: $${Number(or.key_usage_daily_usd).toFixed(6)}`;
          document.getElementById('orKeyLimitRem').innerText = or.key_remaining_usd != null ? `$${Number(or.key_remaining_usd).toFixed(4)}` : 'Unlimited';
          document.getElementById('orKeyLabel').innerText = `Key: ${or.key_label || '--'}`;
        }

        const ng = data.nanogpt || {};
        const nanoEl = document.getElementById('nanoDashStatus');
        if (nanoEl) {
          if (ng.connected) {
            nanoEl.textContent = `Connected · $${Number(ng.account_remaining_balance_usd || 0).toFixed(4)} USD (${Number(ng.account_remaining_nano || 0).toFixed(4)} NANO) · Calls: ${Number(ng.session_total_calls || 0)}`;
          } else if (ng.key_label && ng.key_label !== 'not_configured') {
            nanoEl.textContent = `Key configured (${ng.key_label}) · Balance check pending`;
          } else {
            nanoEl.textContent = 'Set NANOGPT_API_KEY on server for live NanoGPT inference & balance (catalog browsable via /api/models/nanogpt)';
          }
        }

        document.getElementById('analyticsHeader').innerText = 
          `Calls: ${data.total_calls} | Tokens: ${data.total_tokens} | Cost: $${Number(data.total_spend_usd).toFixed(6)}`;
        
        window.latestProvidersMap = latestProvidersMap = data.providers || {};
        const sel = document.getElementById('aliasSelect');
        const prevSelected = sel ? sel.value : 'gemini-brain';
        if (sel && Object.keys(latestProvidersMap).length > 0) {
          sel.innerHTML = Object.entries(latestProvidersMap).map(([alias, info]) =>
            `<option value="${alias}" title="${alias} → ${info.model}">${alias} → ${info.model}</option>`
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
          card.className = `tc-provider-card cursor-pointer p-3 rounded-lg border ${isSelected ? 'is-selected' : ''} space-y-2 text-xs transition`;
          card.title = `Click to swap ${alias}`;
          const esc = (v) => String(v ?? '').replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
          card.innerHTML = `
            <div class="flex justify-between items-center gap-2 min-w-0">
              <span class="font-semibold font-mono truncate">${esc(alias)}</span>
              <span class="tc-chip shrink-0">${esc(info.gateway || 'openrouter')} · ${esc(info.display_name)}</span>
            </div>
            <div class="tc-truncate font-mono text-[11px]" title="${esc(info.model)}"><span class="tc-stat__label">Model</span> ${esc(info.model)}</div>
            <dl class="tc-provider-stats">
              <div><dt>In / 1M</dt><dd>$${Number(info.input_cost_per_1m_usd || 0).toFixed(2)}</dd></div>
              <div><dt>Out / 1M</dt><dd>$${Number(info.output_cost_per_1m_usd || 0).toFixed(2)}</dd></div>
              <div><dt>Calls</dt><dd>${Number(info.total_calls ?? info.call_count ?? 0)}</dd></div>
            </dl>
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

    let adminAdWatchCompleted = false;
    let currentAdMaxWatchedTime = 0;

    function isCurrentVideoAd() {
      if (!playlistVideos.length || currentVideoIdx < 0 || currentVideoIdx >= playlistVideos.length) return false;
      const v = playlistVideos[currentVideoIdx];
      return !!v && (v.category === 'ad' || v.category === 'community_video');
    }

    function checkAdminMustWatchAd() {
      return isAdmin && isCurrentVideoAd() && !adminAdWatchCompleted;
    }

    function showAdminAdLockToast() {
      const banner = document.getElementById('adminAdIntelNotice');
      if (banner) {
        banner.classList.remove('hidden');
        banner.classList.add('ring-2', 'ring-amber-400');
        setTimeout(() => banner.classList.remove('ring-2', 'ring-amber-400'), 1500);
      }
      alert('🔒 Intelligence Gathering Active: Admins are required to watch sponsored ads in full before skipping.');
    }

    function canSkipVideo() {
      if (checkAdminMustWatchAd()) {
        showAdminAdLockToast();
        return false;
      }
      return true;
    }

    function updateAdminAdIntelUI(isAd, item) {
      const notice = document.getElementById('adminAdIntelNotice');
      const prevBtn = document.getElementById('playlistPrevBtn');
      const nextBtn = document.getElementById('playlistNextBtn');

      const mustWatch = isAdmin && isAd && !adminAdWatchCompleted;
      if (notice) {
        if (isAdmin && isAd) {
          notice.classList.remove('hidden');
          const timerEl = document.getElementById('adminAdIntelTimer');
          if (timerEl) {
            timerEl.innerText = adminAdWatchCompleted ? '✅ Intel Gathered' : '🔒 Ad View Required';
            timerEl.className = adminAdWatchCompleted
              ? 'px-2 py-0.5 rounded bg-emerald-950 border border-emerald-700 text-emerald-300 font-mono text-[10px] font-bold shrink-0'
              : 'px-2 py-0.5 rounded bg-amber-950 border border-amber-700 text-amber-300 font-mono text-[10px] font-bold shrink-0 animate-pulse';
          }
        } else {
          notice.classList.add('hidden');
        }
      }

      if (prevBtn) {
        if (mustWatch) {
          prevBtn.classList.add('opacity-40', 'cursor-not-allowed');
          prevBtn.title = 'Locked: Admins must watch ads for intelligence gathering';
        } else {
          prevBtn.classList.remove('opacity-40', 'cursor-not-allowed');
          prevBtn.title = '';
        }
      }

      if (nextBtn) {
        if (mustWatch) {
          nextBtn.classList.add('opacity-40', 'cursor-not-allowed');
          nextBtn.title = 'Locked: Admins must watch ads for intelligence gathering';
        } else {
          nextBtn.classList.remove('opacity-40', 'cursor-not-allowed');
          nextBtn.title = '';
        }
      }
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
      const isAd = item && (item.category === 'ad' || item.category === 'community_video');

      const vidEl = document.getElementById('relayNativeVideo');
      const targetSrc = item.embed_url || `/videos/${item.video_id}.mp4`;
      const isNewVideo = vidEl && vidEl.getAttribute('data-vid') !== item.id;
      if (isNewVideo) {
        adminAdWatchCompleted = !isAd;
        currentAdMaxWatchedTime = 0;
      }

      badge.innerText = `${currentVideoIdx + 1} / ${total} · ${autoRotateEnabled ? 'Loop' : 'Paused'}`;
      document.getElementById('nowPlayingTitle').innerHTML =
        `${item.title} · <span class="text-pink-400 font-mono">${item.creator}</span>${isAd ? ' <span class="text-amber-400 font-mono text-[10px] uppercase font-bold">[SPONSORED AD]</span>' : ''}`;

      if (vidEl) {
        vidEl.loop = (total === 1 && autoRotateEnabled && !isAd);
        if (isNewVideo) {
          vidEl.setAttribute('data-vid', item.id);
          vidEl.src = targetSrc;
          vidEl.play().catch(() => {});
        }
      }

      updateAdminAdIntelUI(isAd, item);

      queue.innerHTML = playlistVideos.map((v, idx) => `
        <div onclick="selectPlaylistVideo(${idx})" class="cursor-pointer px-2.5 py-1 rounded border flex justify-between items-center transition ${idx === currentVideoIdx ? 'bg-pink-950/60 border-pink-700 text-white' : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'}">
          <span class="truncate">${idx + 1}. ${v.title} (${v.creator})</span>
          <div class="flex items-center gap-1.5 ml-2 shrink-0">
            <span class="text-[10px] uppercase px-1.5 py-0.5 rounded bg-slate-900 text-slate-300">${v.category}</span>
            ${isAdmin ? `
              <button onclick="event.stopPropagation(); openEditVideoModal('${v.video_id}')" class="px-1.5 py-0.5 bg-slate-800 hover:bg-slate-700 text-cyan-300 rounded text-[10px] border border-slate-700" title="Edit Video">✏️</button>
              <button onclick="event.stopPropagation(); adminDeleteVideo('${v.video_id}')" class="px-1.5 py-0.5 bg-red-950 hover:bg-red-800 text-red-300 rounded text-[10px] border border-red-800" title="Delete Video">🗑️</button>
            ` : ''}
          </div>
        </div>
      `).join('');
    }

    function selectPlaylistVideo(idx) {
      if (idx < 0 || idx >= playlistVideos.length) return;
      if (idx === currentVideoIdx) return;
      if (!canSkipVideo()) return;
      currentVideoIdx = idx;
      renderPlaylistUI();
    }

    function nextPlaylistVideo() {
      if (!playlistVideos.length) return;
      if (!canSkipVideo()) return;
      currentVideoIdx = (currentVideoIdx + 1) % playlistVideos.length;
      renderPlaylistUI();
    }

    function prevPlaylistVideo() {
      if (!playlistVideos.length) return;
      if (!canSkipVideo()) return;
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

    const relayVid = document.getElementById('relayNativeVideo');
    if (relayVid) {
      relayVid.addEventListener('timeupdate', () => {
        if (isCurrentVideoAd() && isAdmin) {
          currentAdMaxWatchedTime = Math.max(currentAdMaxWatchedTime, relayVid.currentTime);
          const timerEl = document.getElementById('adminAdIntelTimer');
          if (timerEl && !adminAdWatchCompleted && relayVid.duration) {
            const rem = Math.max(0, Math.ceil(relayVid.duration - relayVid.currentTime));
            timerEl.innerText = `🔒 Intel Gather: ${rem}s left`;
          }
        }
      });
      relayVid.addEventListener('seeking', () => {
        if (checkAdminMustWatchAd()) {
          if (relayVid.currentTime > currentAdMaxWatchedTime + 1.0) {
            relayVid.currentTime = currentAdMaxWatchedTime;
          }
        }
      });
      relayVid.addEventListener('ended', () => {
        if (isCurrentVideoAd() && isAdmin) {
          adminAdWatchCompleted = true;
          const currentItem = playlistVideos[currentVideoIdx];
          updateAdminAdIntelUI(true, currentItem);
          fetch('/api/ads/intel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              peer_id: myPeerId,
              video_id: currentItem ? (currentItem.video_id || currentItem.id) : 'ad',
              title: currentItem ? currentItem.title : 'Sponsored Ad',
              category: 'ad',
              metadata: { source: 'watch_party_tv', watched_duration: currentAdMaxWatchedTime }
            })
          }).catch(() => {});
        }
        if (autoRotateEnabled && playlistVideos.length > 1) {
          nextPlaylistVideo();
        } else if (autoRotateEnabled && playlistVideos.length === 1) {
          relayVid.currentTime = 0;
          relayVid.play().catch(() => {});
        }
      });
    }

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

    // =========================================================================
    // Admin Video & Sponsor CRUD Functions
    // =========================================================================
    let adminActiveTab = 'videos';
    let allSponsorsList = [];

    function toggleAdminTab(tab) {
      adminActiveTab = tab;
      const vPanel = document.getElementById('adminVideosPanel');
      const sPanel = document.getElementById('adminSponsorsPanel');
      const vBtn = document.getElementById('adminTabBtnVideos');
      const sBtn = document.getElementById('adminTabBtnSponsors');
      if (tab === 'videos') {
        if (vPanel) vPanel.classList.remove('hidden');
        if (sPanel) sPanel.classList.add('hidden');
        if (vBtn) vBtn.className = 'px-2 py-0.5 rounded bg-pink-950 text-pink-300 border border-pink-700 text-[10px] font-mono font-bold';
        if (sBtn) sBtn.className = 'px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 text-[10px] font-mono';
      } else {
        if (vPanel) vPanel.classList.add('hidden');
        if (sPanel) sPanel.classList.remove('hidden');
        if (vBtn) vBtn.className = 'px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 text-[10px] font-mono';
        if (sBtn) sBtn.className = 'px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-700 text-[10px] font-mono font-bold';
      }
      renderAdminCrudTables();
    }

    function toggleAddVideoDrawer() {
      const d = document.getElementById('adminAddVideoDrawer');
      if (d) d.classList.toggle('hidden');
    }

    function toggleAddSponsorDrawer() {
      const d = document.getElementById('adminAddSponsorDrawer');
      if (d) d.classList.toggle('hidden');
    }

    function openAdminSponsorStudio() {
      toggleWindow('win-moderator');
      toggleAdminTab('sponsors');
    }

    async function adminSubmitAddVideo() {
      const url = document.getElementById('adminNewVideoUrl').value.trim();
      const title = document.getElementById('adminNewVideoTitle').value.trim();
      const creator = document.getElementById('adminNewVideoCreator').value.trim();
      const category = document.getElementById('adminNewVideoCategory').value;
      const duration = parseInt(document.getElementById('adminNewVideoDuration').value) || 35;
      if (!url) {
        alert('Please enter a video URL or ID');
        return;
      }
      try {
        const res = await fetch('/api/playlist/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ input: url, title, creator, category, duration_seconds: duration, peer_id: myPeerId }),
        });
        const data = await res.json();
        if (res.ok) {
          document.getElementById('adminNewVideoUrl').value = '';
          document.getElementById('adminNewVideoTitle').value = '';
          document.getElementById('adminNewVideoCreator').value = '';
          toggleAddVideoDrawer();
          await loadPlaylist(false);
          renderAdminCrudTables();
          playXpChime();
        } else {
          alert('Error adding video: ' + (data.error || 'Unknown error'));
        }
      } catch (e) {
        alert('Request failed: ' + e.message);
      }
    }

    function openEditVideoModal(vidId) {
      const v = playlistVideos.find(it => it.video_id === vidId || it.id === vidId);
      if (!v) return;
      document.getElementById('editVideoId').value = v.video_id;
      document.getElementById('editVideoTitle').value = v.title || '';
      document.getElementById('editVideoCreator').value = v.creator || '';
      document.getElementById('editVideoCategory').value = v.category || 'spotlight';
      document.getElementById('editVideoDuration').value = v.duration_seconds || 35;
      document.getElementById('editVideoEmbedUrl').value = v.embed_url || `/videos/${v.video_id}.mp4`;
      document.getElementById('adminEditVideoModal').classList.remove('hidden');
    }

    function closeEditVideoModal() {
      document.getElementById('adminEditVideoModal').classList.add('hidden');
    }

    async function adminSubmitSaveVideoEdit() {
      const vidId = document.getElementById('editVideoId').value;
      const title = document.getElementById('editVideoTitle').value.trim();
      const creator = document.getElementById('editVideoCreator').value.trim();
      const category = document.getElementById('editVideoCategory').value;
      const duration = parseInt(document.getElementById('editVideoDuration').value) || 35;
      const embed_url = document.getElementById('editVideoEmbedUrl').value.trim();

      try {
        const res = await fetch('/api/playlist/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: vidId, title, creator, category, duration_seconds: duration, embed_url }),
        });
        const data = await res.json();
        if (res.ok) {
          closeEditVideoModal();
          await loadPlaylist(false);
          renderAdminCrudTables();
        } else {
          alert('Error updating video: ' + (data.error || 'Unknown error'));
        }
      } catch (e) {
        alert('Failed to update: ' + e.message);
      }
    }

    async function adminDeleteVideo(vidId) {
      if (!confirm(`Are you sure you want to remove video ${vidId} from the playlist and S3 manifest?`)) return;
      try {
        const res = await fetch('/api/playlist/remove', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: vidId }),
        });
        const data = await res.json();
        if (res.ok) {
          await loadPlaylist(false);
          renderAdminCrudTables();
        } else {
          alert('Error deleting video: ' + (data.error || 'Unknown error'));
        }
      } catch (e) {
        alert('Failed to delete: ' + e.message);
      }
    }

    async function loadSponsorsData() {
      try {
        const res = await fetch('/api/sponsors');
        if (!res.ok) return;
        const data = await res.json();
        allSponsorsList = data.all_sponsors || [];
        renderAdminCrudTables();
      } catch (e) {}
    }

    async function adminSubmitAddSponsor() {
      const name = document.getElementById('adminNewSponsorName').value.trim();
      const icon = document.getElementById('adminNewSponsorIcon').value.trim() || '🌟';
      const badge = document.getElementById('adminNewSponsorBadge').value.trim() || 'Partner';
      const tagline = document.getElementById('adminNewSponsorTagline').value.trim();
      const url = document.getElementById('adminNewSponsorUrl').value.trim() || '/';
      const cta = document.getElementById('adminNewSponsorCta').value.trim() || 'Visit Partner ↗';
      const rewardTokens = parseInt(document.getElementById('adminNewSponsorRewardTokens').value) || 5000;
      const rewardUsd = parseFloat(document.getElementById('adminNewSponsorRewardUsd').value) || 0.05;

      if (!name) {
        alert('Please enter sponsor name');
        return;
      }

      try {
        const res = await fetch('/api/sponsors/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, icon, badge, tagline, url, cta, reward_tokens: rewardTokens, reward_usd: rewardUsd }),
        });
        const data = await res.json();
        if (res.ok) {
          document.getElementById('adminNewSponsorName').value = '';
          document.getElementById('adminNewSponsorTagline').value = '';
          toggleAddSponsorDrawer();
          await loadSponsorsData();
        } else {
          alert('Error adding sponsor: ' + (data.error || 'Unknown error'));
        }
      } catch (e) {
        alert('Failed to add: ' + e.message);
      }
    }

    function openEditSponsorModal(sId) {
      const s = allSponsorsList.find(it => it.id === sId);
      if (!s) return;
      document.getElementById('editSponsorId').value = s.id;
      document.getElementById('editSponsorName').value = s.name || '';
      document.getElementById('editSponsorIcon').value = s.icon || '🌟';
      document.getElementById('editSponsorBadge').value = s.badge || 'Partner';
      document.getElementById('editSponsorTagline').value = s.tagline || '';
      document.getElementById('editSponsorCta').value = s.cta || 'Visit Partner ↗';
      document.getElementById('editSponsorUrl').value = s.url || '/';
      document.getElementById('editSponsorRewardTokens').value = s.reward_tokens || 5000;
      document.getElementById('editSponsorRewardUsd').value = s.reward_usd || 0.05;
      document.getElementById('adminEditSponsorModal').classList.remove('hidden');
    }

    function closeEditSponsorModal() {
      document.getElementById('adminEditSponsorModal').classList.add('hidden');
    }

    async function adminSubmitSaveSponsorEdit() {
      const sId = document.getElementById('editSponsorId').value;
      const name = document.getElementById('editSponsorName').value.trim();
      const icon = document.getElementById('editSponsorIcon').value.trim();
      const badge = document.getElementById('editSponsorBadge').value.trim();
      const tagline = document.getElementById('editSponsorTagline').value.trim();
      const cta = document.getElementById('editSponsorCta').value.trim();
      const url = document.getElementById('editSponsorUrl').value.trim();
      const rewardTokens = parseInt(document.getElementById('editSponsorRewardTokens').value) || 5000;
      const rewardUsd = parseFloat(document.getElementById('editSponsorRewardUsd').value) || 0.05;

      try {
        const res = await fetch('/api/sponsors/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: sId, name, icon, badge, tagline, cta, url, reward_tokens: rewardTokens, reward_usd: rewardUsd }),
        });
        const data = await res.json();
        if (res.ok) {
          closeEditSponsorModal();
          await loadSponsorsData();
        } else {
          alert('Error updating sponsor: ' + (data.error || 'Unknown error'));
        }
      } catch (e) {
        alert('Failed to update: ' + e.message);
      }
    }

    async function adminDeleteSponsor(sId) {
      if (!confirm(`Are you sure you want to remove sponsor '${sId}' from rotation?`)) return;
      try {
        const res = await fetch('/api/sponsors/remove', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: sId }),
        });
        const data = await res.json();
        if (res.ok) {
          await loadSponsorsData();
        } else {
          alert('Error deleting sponsor: ' + (data.error || 'Unknown error'));
        }
      } catch (e) {
        alert('Failed to delete: ' + e.message);
      }
    }

    function renderAdminCrudTables() {
      const vCount = document.getElementById('adminVideosCount');
      const sCount = document.getElementById('adminSponsorsCount');
      if (vCount) vCount.innerText = playlistVideos.length;
      if (sCount) sCount.innerText = allSponsorsList.length;

      const vTable = document.getElementById('adminVideosTableBody');
      if (vTable) {
        if (!playlistVideos.length) {
          vTable.innerHTML = '<tr><td colspan="6" class="px-3 py-3 text-center text-slate-500">No videos in playlist</td></tr>';
        } else {
          vTable.innerHTML = playlistVideos.map(v => `
            <tr class="hover:bg-slate-800/40">
              <td class="px-2.5 py-2 font-mono text-[11px] text-pink-300">
                <a href="${v.embed_url || `/videos/${v.video_id}.mp4`}" target="_blank" class="hover:underline">${v.video_id}</a>
              </td>
              <td class="px-2.5 py-2 font-semibold text-white max-w-[160px] truncate" title="${v.title}">${v.title}</td>
              <td class="px-2.5 py-2 text-slate-400 font-mono text-[11px]">${v.creator}</td>
              <td class="px-2.5 py-2">
                <span class="px-1.5 py-0.5 rounded text-[9px] uppercase font-mono ${v.category === 'ad' ? 'bg-amber-950 text-amber-300 border border-amber-800' : 'bg-slate-800 text-slate-300 border border-slate-700'}">${v.category}</span>
              </td>
              <td class="px-2.5 py-2 text-slate-400 font-mono text-[11px]">${v.duration_seconds || 35}s</td>
              <td class="px-2.5 py-2 text-right space-x-1 shrink-0">
                <button onclick="openEditVideoModal('${v.video_id}')" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 text-[10px]">Edit</button>
                <button onclick="adminDeleteVideo('${v.video_id}')" class="px-2 py-0.5 rounded bg-red-950 hover:bg-red-800 text-red-300 border border-red-800 text-[10px]">Delete</button>
              </td>
            </tr>
          `).join('');
        }
      }

      const sTable = document.getElementById('adminSponsorsTableBody');
      if (sTable) {
        if (!allSponsorsList.length) {
          sTable.innerHTML = '<tr><td colspan="5" class="px-3 py-3 text-center text-slate-500">No active sponsors</td></tr>';
        } else {
          sTable.innerHTML = allSponsorsList.map(s => `
            <tr class="hover:bg-slate-800/40">
              <td class="px-2.5 py-2 font-mono text-[11px]">
                <div class="flex items-center gap-1.5">
                  <span>${s.icon || '🌟'}</span>
                  <span class="font-bold text-white">${s.name}</span>
                </div>
                <div class="text-[10px] text-slate-400 truncate max-w-[180px]">${s.tagline || ''}</div>
              </td>
              <td class="px-2.5 py-2">
                <span class="px-1.5 py-0.5 rounded text-[9px] uppercase font-mono bg-indigo-950 text-indigo-300 border border-indigo-800">${s.badge || 'Partner'}</span>
              </td>
              <td class="px-2.5 py-2 font-mono text-emerald-400 text-[11px]">+${s.reward_tokens || 5000}</td>
              <td class="px-2.5 py-2 font-mono text-slate-400 text-[10px]">
                Imp: ${s.impressions || 0} / Clk: ${s.clicks || 0}
              </td>
              <td class="px-2.5 py-2 text-right space-x-1 shrink-0">
                <button onclick="openEditSponsorModal('${s.id}')" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 text-[10px]">Edit</button>
                <button onclick="adminDeleteSponsor('${s.id}')" class="px-2 py-0.5 rounded bg-red-950 hover:bg-red-800 text-red-300 border border-red-800 text-[10px]">Delete</button>
              </td>
            </tr>
          `).join('');
        }
      }
    }

    // =========================================================================
    // Cyberspace Discussion Board · GraphRAG + BM25 + @verifier-agent Engine
    // =========================================================================
    let activeBoardTopicId = null;
    let activeBoardTab = 'discussions';
    let activeBoardCategoryFilter = '';
    let activeReplyParentPostByTopic = {};
    let _boardTopicsById = {};
    let boardGraphSnapshot = { nodes: [], edges: [] };
    let boardGraphLayoutNodes = [];
    let selectedGraphNodeId = null;

    function switchBoardTab(tabName) {
      activeBoardTab = tabName;
      if (tabName === 'search') {
        // The old Search Lab now lives behind the "how this ranked" disclosure.
        tabName = 'discussions';
        activeBoardTab = tabName;
        openBoardRankDetails();
      }
      ['discussions', 'feed', 'graph', 'verify'].forEach(t => {
        const panel = document.getElementById(`boardTab-${t}`);
        const btn = document.getElementById(`boardTabBtn-${t}`);
        if (panel) panel.classList.toggle('hidden', t !== tabName);
        if (btn) {
          if (t === tabName) {
            btn.className = 'px-3 py-1.5 rounded-full bg-[#111111] text-[#ecf1e6] border border-[#111111] font-bold text-xs transition flex items-center gap-1';
          } else {
            btn.className = 'px-3 py-1.5 rounded-full bg-[#ffffff] hover:bg-[#f4f8f0] text-[#111111] border border-[#111111] text-xs transition flex items-center gap-1';
          }
        }
      });
      if (tabName === 'graph') {
        loadAndDrawBoardGraph();
      } else if (tabName === 'feed') {
        loadBoardFeedAndThreads();
      } else if (tabName === 'verify') {
        prefillVerificationFormDefaults();
        loadVerificationCenterData();
      }
    }

    function setBoardCategoryFilter(cat) {
      // Categories are just topics in the single search bar.
      if (!cat) { boardChips = boardChips.filter(c => !c.startsWith('#')); renderBoardChips(); loadCyberspaceBoard(); return; }
      addBoardChip('#' + String(cat).replace(/^#/, ''));
    }

    function formatBoardMentions(text) {
      const raw = String(text || '');
      const tokenRe = /(?<![\w.&])([@#])([a-zA-Z0-9_\-]+)/g;
      let out = '';
      let lastIdx = 0;
      let match;
      while ((match = tokenRe.exec(raw)) !== null) {
        if (match.index > lastIdx) {
          out += escapeHtml(raw.slice(lastIdx, match.index));
        }
        const sigil = match[1];
        const token = match[2];
        if (sigil === '@') {
          const low = token.toLowerCase();
          const isAgent = low.endsWith('-brain') || low.endsWith('-agent') || low === 'claude-sonnet' || low === 'gpt-4o' || low === 'deepseek-r1';
          if (isAgent) {
            out += `<span onclick="quickSearchBoardEntity('@${token}')" title="Search @${token} across Cyberspace" class="cursor-pointer px-1.5 py-0.2 rounded-full bg-[#f4f8f0] hover:bg-[#107a47] hover:text-[#ffffff] text-[#107a47] border border-[#107a47] font-mono text-[11px] font-bold">🤖 @${token}</span>`;
          } else {
            out += `<span onclick="inspectCyberspaceUserProfile('${token}')" title="Inspect @${token}'s Cyberspace profile & attestation" class="cursor-pointer px-1.5 py-0.2 rounded-full bg-[#f4f8f0] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border border-[#111111]/40 font-mono text-[11px] font-semibold">🪪 @${token}</span>`;
          }
        } else {
          out += `<span onclick="quickSearchBoardEntity('#${token}')" class="cursor-pointer px-1.5 py-0.2 rounded-full bg-[#f4f8f0] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border border-[#111111]/30 font-mono text-[11px]">#${token}</span>`;
        }
        lastIdx = tokenRe.lastIndex;
      }
      if (lastIdx < raw.length) {
        out += escapeHtml(raw.slice(lastIdx));
      }
      return out;
    }

    function insertBoardTag(tagStr, targetId = 'boardSearchInput') {
      const el = document.getElementById(targetId) || document.getElementById('boardSearchInput');
      if (!el) return;
      const cur = el.value;
      const prefix = (cur && !cur.endsWith(' ')) ? ' ' : '';
      el.value = cur + prefix + tagStr + ' ';
      el.focus();
    }

    function insertBoardSelfTag(targetId = 'boardSearchInput') {
      const un = (localStorage.getItem('tincan_username') || '').trim().replace(/^@/, '');
      if (!un) {
        switchBoardTab('verify');
        requestAgentVerificationForm();
        return;
      }
      insertBoardTag('@' + un, targetId);
    }

    function quickSearchBoardEntity(entityToken) {
      switchBoardTab('discussions');
      const tok = String(entityToken || '').trim();
      if (/^[#@][A-Za-z0-9_\-]+$/.test(tok)) {
        addBoardChip(tok);
      } else {
        const inp = document.getElementById('boardSearchInput');
        if (inp) inp.value = tok;
        searchCyberspaceBoard();
      }
    }

    // ---------------------------------------------------------------------
    // Unified board search bar: chips, slash commands, autocomplete, trending
    // ---------------------------------------------------------------------
    let boardChips = [];
    let boardSuggestItems = [];
    let boardSuggestIndex = -1;
    let boardSuggestSeq = 0;
    const BOARD_SLASH_COMMANDS = [
      { token: '/search ', name: '/search', label: 'Search posts, people and agents (hybrid BM25 + GraphRAG)' },
      { token: '/post ', name: '/post', label: 'Start a new topic/thread: /post Title #tag @agent :: details' },
      { token: '/thread ', name: '/thread', label: 'Open a Discord-style active thread: /thread Title' },
      { token: '/topic ', name: '/topic', label: 'Jump to a topic: /topic graphrag' },
      { token: '/feed', name: '/feed', label: 'Open Curated Feed & Active Threads view' },
      { token: '/curate ', name: '/curate', label: 'Toggle curated topics view or curate a topic ID' },
      { token: '/sort ', name: '/sort', label: 'Sort results: /sort hot, activity, new, top or discussed' },
    ];
    const BOARD_SORTS = [
      { token: 'sort:hot', name: 'sort:hot', label: 'Hot: activity weighted by age' },
      { token: 'sort:activity', name: 'sort:activity', label: 'Activity: highest recent thread activity' },
      { token: 'sort:new', name: 'sort:new', label: 'Newest first' },
      { token: 'sort:top', name: 'sort:top', label: 'Most upvoted' },
      { token: 'sort:discussed', name: 'sort:discussed', label: 'Most replies' },
    ];

    function setBoardSort(value) {
      const sel = document.getElementById('boardSortSelect');
      if (!sel || ![...sel.options].some(o => o.value === value)) return false;
      sel.value = value;
      onBoardSortChange();
      return true;
    }

    function onBoardSortChange() {
      if (boardChips.length || (document.getElementById('boardSearchInput')?.value || '').trim()) searchCyberspaceBoard();
      else loadCyberspaceBoard();
    }

    // "/sort new" or a "sort:top" token in the bar sets the sort and is removed from the query.
    function consumeBoardSortToken(inp) {
      const m = inp.value.match(/^\/sort\s+(\w+)\s*$/i) || inp.value.match(/(?:^|\s)sort:(\w+)(?=\s|$)/i);
      if (!m) return false;
      const v = m[1].toLowerCase() === 'newest' ? 'new' : m[1].toLowerCase();
      if (!setBoardSort(v)) return false;
      inp.value = inp.value.replace(m[0], ' ').replace(/\s+/g, ' ').trim();
      return true;
    }
    const BOARD_FILTERS = [{ token: 'is:verified', name: 'is:verified', label: 'Only posts by verified citizens' }];

    function boardChipKind(tok) { return tok.startsWith('#') ? 'topic' : tok.startsWith('@') ? 'mention' : 'filter'; }

    function renderBoardChips() {
      const box = document.getElementById('boardSearchChips');
      if (!box) return;
      box.innerHTML = boardChips.map((c, i) =>
        `<span class="ubar-chip" data-kind="${boardChipKind(c)}">${escapeHtml(c)}<button type="button" aria-label="Remove ${escapeHtml(c)}" onclick="event.stopPropagation(); removeBoardChip(${i})">&#x2715;</button></span>`
      ).join('');
    }

    function addBoardChip(tok, runSearch = true) {
      tok = String(tok || '').trim();
      if (!tok) return;
      if (/^is:verified$/i.test(tok)) tok = 'is:verified';
      else tok = tok[0] + tok.slice(1).toLowerCase();
      if (!boardChips.includes(tok)) boardChips.push(tok);
      renderBoardChips();
      if (runSearch) searchCyberspaceBoard();
    }

    function removeBoardChip(i) {
      boardChips.splice(i, 1);
      renderBoardChips();
      if (boardChips.length || (document.getElementById('boardSearchInput')?.value || '').trim()) searchCyberspaceBoard();
      else resetCyberspaceSearch();
    }

    function buildBoardQuery() {
      // sort: tokens and /sort set the sort control; they are not search terms.
      const text = (document.getElementById('boardSearchInput')?.value || '')
        .replace(/(?:^|\s)sort:\w+(?=\s|$)/gi, ' ').replace(/^\s*\/sort\b\s*\w*/i, '').trim();
      // A slash command must lead the query.
      const m = text.match(/^\/(search|topic)\b\s*/i);
      const cmd = m ? m[0].trim() + ' ' : '';
      const rest = m ? text.slice(m[0].length) : text;
      return (cmd + [...boardChips, rest].filter(Boolean).join(' ')).trim();
    }

    function boardCurrentToken(inp) {
      const v = inp.value;
      const caret = inp.selectionStart ?? v.length;
      const before = v.slice(0, caret);
      const m = before.match(/(^|\s)(\S*)$/);
      const tok = m ? m[2] : '';
      return { tok, start: caret - tok.length, end: caret };
    }

    function closeBoardSuggest() {
      const list = document.getElementById('boardSuggestList');
      const inp = document.getElementById('boardSearchInput');
      if (list) list.classList.add('hidden');
      if (inp) { inp.setAttribute('aria-expanded', 'false'); inp.removeAttribute('aria-activedescendant'); }
      boardSuggestItems = [];
      boardSuggestIndex = -1;
    }

    function renderBoardSuggest(groups) {
      const list = document.getElementById('boardSuggestList');
      const inp = document.getElementById('boardSearchInput');
      if (!list) return;
      boardSuggestItems = [];
      let html = '';
      groups.forEach(g => {
        if (!g.items.length) return;
        html += `<div class="ubar-group-title" role="presentation">${escapeHtml(g.title)}</div>`;
        g.items.forEach(it => {
          const idx = boardSuggestItems.length;
          boardSuggestItems.push(it);
          const count = it.count ? `<span class="ubar-opt-count">${Number(it.count)}</span>` : (it.verified ? '<span class="ubar-opt-count">verified</span>' : '');
          html += `<div id="boardSuggestOpt-${idx}" role="option" aria-selected="false" class="ubar-option" onmousedown="event.preventDefault(); applyBoardSuggestion(${idx})">
              <span>${escapeHtml(it.token.trim())}</span>
              <span class="ubar-opt-label">${escapeHtml(it.label && it.label !== it.token ? it.label : '')}</span>${count}</div>`;
        });
      });
      if (!boardSuggestItems.length) { closeBoardSuggest(); return; }
      list.innerHTML = html;
      list.classList.remove('hidden');
      if (inp) inp.setAttribute('aria-expanded', 'true');
      boardSuggestIndex = 0;
      highlightBoardSuggestion();
    }

    function highlightBoardSuggestion() {
      const inp = document.getElementById('boardSearchInput');
      boardSuggestItems.forEach((_, i) => {
        const el = document.getElementById(`boardSuggestOpt-${i}`);
        if (!el) return;
        const on = i === boardSuggestIndex;
        el.setAttribute('aria-selected', on ? 'true' : 'false');
        if (on) { el.scrollIntoView({ block: 'nearest' }); if (inp) inp.setAttribute('aria-activedescendant', el.id); }
      });
    }

    function applyBoardSuggestion(idx) {
      const it = boardSuggestItems[idx];
      const inp = document.getElementById('boardSearchInput');
      if (!it || !inp) return;
      const { start, end } = boardCurrentToken(inp);
      const before = inp.value.slice(0, start);
      const after = inp.value.slice(end);
      if (it.token.startsWith('sort:')) {
        inp.value = (before + after).replace(/^\/sort\s*/i, '').replace(/\s+/g, ' ').trim();
        closeBoardSuggest();
        setBoardSort(it.token.slice(5));
        inp.focus();
        return;
      }
      if (it.token.startsWith('/')) {
        inp.value = it.token + (before + after).trim();
        inp.setSelectionRange(inp.value.length, inp.value.length);
        closeBoardSuggest();
        inp.focus();
        if (it.token.trim() === '/feed') submitBoardOmniInput();
        return;
      }
      inp.value = (before + after).replace(/\s+/g, ' ').trimStart();
      closeBoardSuggest();
      addBoardChip(it.token);
      inp.focus();
    }

    let _boardAiSuggestTimer = null;
    function scheduleBoardAiSuggestions(q) {
      clearTimeout(_boardAiSuggestTimer);
      _boardAiSuggestTimer = setTimeout(() => loadBoardAiSuggestions(false, q), 280);
    }

    async function loadBoardAiSuggestions(forcePost = false, explicitQuery = null) {
      const chipsEl = document.getElementById('boardAiSuggestionChips');
      const badgeEl = document.getElementById('boardAiModelBadge');
      if (!chipsEl) return;
      const inp = document.getElementById('boardSearchInput');
      const q = explicitQuery !== null ? String(explicitQuery) : (inp ? inp.value.trim() : '');
      try {
        const res = forcePost
          ? await fetch('/api/board/ai-suggest', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ query: q, limit: 6 })
            })
          : await fetch(`/api/board/ai-suggest?q=${encodeURIComponent(q)}&limit=6`);
        if (!res.ok) return;
        const data = await res.json();
        const suggestions = Array.isArray(data.suggestions) ? data.suggestions : [];
        if (badgeEl) {
          const mdl = (data.model || 'free-model').split('/').pop();
          badgeEl.textContent = `${mdl} · ${data.used_live_llm || data.source === 'free_llm' ? 'Free LLM $0' : 'Indexed $0'}`;
        }
        if (!suggestions.length) return;
        chipsEl.innerHTML = suggestions.map(s => {
          const rawToken = String(s.text || s.token || '');
          const text = rawToken.trim();
          const kind = String(s.kind || 'search');
          const reason = String(s.reason || '');
          const label = text === '/thread' ? '/thread + New' : (text === '/search' ? '/search ...' : text);
          const colorCls = kind === 'post' || kind === 'thread' || kind === 'command'
            ? 'bg-[#107a47]/10 hover:bg-[#107a47] hover:text-[#ffffff] text-[#107a47] border-[#107a47]/60 font-semibold'
            : kind === 'agent' || kind === 'ai'
              ? 'bg-[#ffffff] hover:bg-[#107a47] hover:text-[#ffffff] text-[#107a47] border-[#107a47] font-semibold'
              : 'bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border-[#111111]/40';
          return `<button type="button" onclick="applyBoardAiSuggestion('${escapeHtml(rawToken).replace(/'/g, '&#39;')}')" title="${escapeHtml(reason)}" class="px-2 py-0.5 rounded-full border text-[10px] transition ${colorCls}">[${escapeHtml(label)}]</button>`;
        }).join('');
      } catch (e) {}
    }

    function applyBoardAiSuggestion(text) {
      const inp = document.getElementById('boardSearchInput');
      if (!inp) return;
      const clean = String(text || '').trim().replace(/^\[|\]$/g, '');
      if (!clean) return;
      if (clean.startsWith('/post') || clean.startsWith('/thread') || clean.startsWith('/search') || clean.startsWith('/feed')) {
        inp.value = clean + (clean.endsWith(' ') ? '' : ' ');
        inp.focus();
        if (clean.startsWith('/search ') && clean.length > '/search '.length) searchCyberspaceBoard();
        else if (clean === '/feed') submitBoardOmniInput();
        return;
      }
      if (/^[#@][A-Za-z0-9_\-]+$/.test(clean) && !inp.value.trim().startsWith('/post') && !inp.value.trim().startsWith('/thread')) {
        addBoardChip(clean);
        inp.focus();
        return;
      }
      const cur = inp.value;
      const sep = cur && !cur.endsWith(' ') ? ' ' : '';
      inp.value = cur + sep + clean + ' ';
      inp.focus();
    }

    async function onBoardSearchInput(ev) {
      const inp = ev.target;
      const { tok, start } = boardCurrentToken(inp);
      const seq = ++boardSuggestSeq;
      // Turn a finished "#tag " / "@name " / "is:verified " into a chip as soon as space is typed.
      if (ev.data === ' ') {
        const isCreating = /^\s*\/(post|new|thread)\b/i.test(inp.value);
        const prev = !isCreating && inp.value.slice(0, inp.selectionStart - 1).match(/(^|\s)([#@][A-Za-z0-9_\-]+|is:verified)$/i);
        if (prev) {
          const t = prev[2];
          inp.value = (inp.value.slice(0, inp.selectionStart - 1 - t.length) + inp.value.slice(inp.selectionStart)).replace(/\s+/g, ' ').trimStart();
          closeBoardSuggest();
          addBoardChip(t);
          return;
        }
      }
      scheduleBoardAiSuggestions(inp.value);
      const sortCmd = inp.value.match(/^\/sort\s+(\S*)$/i);
      if (sortCmd || (tok.length >= 2 && ('sort:'.startsWith(tok.toLowerCase()) || tok.toLowerCase().startsWith('sort:')))) {
        const want = (sortCmd ? sortCmd[1] : tok.slice(5)).toLowerCase();
        const { tok: cur } = boardCurrentToken(inp);
        renderBoardSuggest([{ title: 'Sort', items: BOARD_SORTS.filter(o => o.token.slice(5).startsWith(want) || cur.toLowerCase() === '/sort') }]);
        return;
      }
      if (start === 0 && tok.startsWith('/')) {
        renderBoardSuggest([{ title: 'Commands', items: BOARD_SLASH_COMMANDS.filter(c => c.name.startsWith(tok.toLowerCase())) }]);
        return;
      }
      if (tok.length >= 2 && 'is:verified'.startsWith(tok.toLowerCase())) {
        renderBoardSuggest([{ title: 'Filters', items: BOARD_FILTERS }]);
        return;
      }
      if (!(tok.startsWith('#') || tok.startsWith('@') || tok.length >= 2)) { closeBoardSuggest(); return; }
      try {
        const res = await fetch(`/api/board/suggest?q=${encodeURIComponent(tok)}&limit=5`);
        if (!res.ok || seq !== boardSuggestSeq) return;
        const data = await res.json();
        if (seq !== boardSuggestSeq) return;
        renderBoardSuggest(data.groups || []);
      } catch (e) {}
    }

    function onBoardSearchKeydown(ev) {
      const inp = ev.target;
      const open = boardSuggestItems.length > 0;
      if (ev.key === 'ArrowDown' && open) { ev.preventDefault(); boardSuggestIndex = (boardSuggestIndex + 1) % boardSuggestItems.length; highlightBoardSuggestion(); return; }
      if (ev.key === 'ArrowUp' && open) { ev.preventDefault(); boardSuggestIndex = (boardSuggestIndex - 1 + boardSuggestItems.length) % boardSuggestItems.length; highlightBoardSuggestion(); return; }
      if ((ev.key === 'Enter' || ev.key === 'Tab') && open && boardSuggestIndex >= 0) { ev.preventDefault(); applyBoardSuggestion(boardSuggestIndex); return; }
      if (ev.key === 'Escape') { if (open) { ev.preventDefault(); closeBoardSuggest(); } else if (inp.value) { inp.value = ''; } return; }
      if (ev.key === 'Enter') {
        ev.preventDefault(); closeBoardSuggest();
        submitBoardOmniInput(); return;
      }
      if (ev.key === 'Backspace' && !inp.value && boardChips.length) { ev.preventDefault(); removeBoardChip(boardChips.length - 1); }
    }

    async function submitBoardOmniInput() {
      const inp = document.getElementById('boardSearchInput');
      if (!inp) return;
      if (consumeBoardSortToken(inp) && !inp.value.trim() && !boardChips.length) return;
      const raw = (inp.value || '').trim();
      const postMatch = raw.match(/^\/(post|new|thread)\b\s*(.*)$/i);
      if (postMatch) {
        const cmd = postMatch[1].toLowerCase();
        const payload = (postMatch[2] || '').trim();
        if (!payload) {
          inp.focus();
          showQuickNotification(`Type a topic after /${cmd}, e.g. /${cmd} GraphRAG tuning #graphrag @gemini-brain`);
          return;
        }
        await createCyberspaceTopic(raw);
        return;
      }
      if (/^\/feed\b/i.test(raw)) {
        const rest = raw.replace(/^\/feed\b\s*/i, '').trim();
        inp.value = '';
        switchBoardTab('feed');
        if (rest) {
          const fi = document.getElementById('boardFeedFilterInput');
          if (fi) { fi.value = rest; loadBoardFeedAndThreads(); }
        }
        return;
      }
      if (/^\/curate\b/i.test(raw)) {
        const arg = raw.replace(/^\/curate\b\s*/i, '').trim();
        inp.value = '';
        if (arg.startsWith('topic-')) {
          await curateCyberspaceTopic(arg);
          return;
        }
        setBoardFeedFilter('curated');
        switchBoardTab('feed');
        return;
      }
      searchCyberspaceBoard();
    }

    function focusBoardSearch() {
      const win = document.getElementById('win-board');
      if (win && (win.classList.contains('hidden') || win.classList.contains('minimized') || win.style.display === 'none')) {
        if (typeof toggleWindow === 'function') toggleWindow('win-board');
      }
      if (typeof switchBoardTab === 'function' && activeBoardTab !== 'discussions') switchBoardTab('discussions');
      const inp = document.getElementById('boardSearchInput');
      if (inp) { inp.focus(); inp.select(); }
    }

    function boardWindowVisible() {
      const win = document.getElementById('win-board');
      return !!win && !win.classList.contains('hidden') && !win.classList.contains('minimized') && win.style.display !== 'none';
    }

    // Cmd/Ctrl+K focuses the board search while the board is open. Otherwise the
    // keystroke falls through to the Zen shell launcher, which also owns Cmd/Ctrl+K.
    window.addEventListener('keydown', (ev) => {
      if (!((ev.metaKey || ev.ctrlKey) && !ev.altKey && !ev.shiftKey && (ev.key === 'k' || ev.key === 'K'))) return;
      if (document.body.classList.contains('zen-launcher') || !boardWindowVisible()) return;
      const gate = document.getElementById('accountSetupModal');
      if (gate && !gate.classList.contains('hidden')) return;
      ev.preventDefault();
      ev.stopImmediatePropagation();
      focusBoardSearch();
    }, true);

    function openBoardRankDetails() {
      const d = document.getElementById('boardRankDetails');
      if (d) { d.open = true; d.scrollIntoView({ block: 'nearest' }); }
    }

    function renderBoardRankDiagnostics(data) {
      const body = document.getElementById('boardRankBody');
      if (!body) return;
      const d = (data && data.diagnostics) || {};
      const p = (data && data.parsed) || {};
      const filters = [
        ...(p.tags || []).map(t => '#' + t), ...(p.mentions || []).map(m => '@' + m), p.verified_only ? 'is:verified' : ''
      ].filter(Boolean);
      if (d.mode !== 'hybrid') {
        body.innerHTML = `Filtered by ${filters.length ? escapeHtml(filters.join(' ')) : 'nothing'} and sorted by ${escapeHtml(d.sort_by || 'hot')}. Add words or an @mention to rank with hybrid BM25 + GraphRAG.`;
        return;
      }
      const bm = d.bm25 || {};
      const terms = bm.query_terms || [];
      const rows = terms.length ? terms.map(t => `<tr><td>${escapeHtml(t.term)}</td><td>${Number(t.df || 0)} / ${Number(bm.corpus_size || 0)}</td><td>${Number(t.idf || 0).toFixed(4)}</td></tr>`).join('')
        : '<tr><td colspan="3">No lexical terms.</td></tr>';
      const sg = d.subgraph || {};
      body.innerHTML = `
        <div>Hybrid score = ${Number((d.weights || {}).bm25 || 0.55)} &times; BM25 + ${Number((d.weights || {}).graphrag || 0.45)} &times; GraphRAG (personalized PageRank, &alpha;=0.85), each normalized to the top result.</div>
        <div>Query: <code>${escapeHtml(d.query || '')}</code>${filters.length ? ` &middot; filters ${escapeHtml(filters.join(' '))}` : ''}</div>
        <div>BM25 corpus: N=${Number(bm.corpus_size || 0)} docs &middot; avgdl=${escapeHtml(String(bm.avg_doc_length ?? 0))} &middot; k1=${escapeHtml(String(bm.k1 ?? 1.5))} &middot; b=${escapeHtml(String(bm.b ?? 0.75))}</div>
        <table><thead><tr><th>Term</th><th>Doc freq</th><th>IDF</th></tr></thead><tbody>${rows}</tbody></table>
        <div style="margin-top:0.35rem">GraphRAG subgraph: ${Number(sg.nodes || 0)} nodes &middot; ${Number(sg.edges || 0)} edges${(sg.seed_entities || []).length ? ` &middot; seeds ${escapeHtml(sg.seed_entities.join(', '))}` : ''}</div>`;
    }

    async function loadBoardTrending() {
      const box = document.getElementById('boardTrending');
      if (!box) return;
      try {
        const res = await fetch('/api/board/trending?days=7&limit=6');
        if (!res.ok) return;
        const data = await res.json();
        const items = data.items || [];
        if (!items.length) {
          box.innerHTML = '<span class="ubar-trend-label">Trending</span><span class="ubar-trend-empty">No tagged topics yet. Start one with #tags and it will show up here.</span>';
          return;
        }
        const label = data.window === 'all' ? 'Top topics' : `Trending ${escapeHtml(data.window)}`;
        box.innerHTML = `<span class="ubar-trend-label">${label}</span>` + items.map(it =>
          `<button type="button" class="ubar-trend" onclick="addBoardChip('${escapeHtml(it.tag)}')" title="${Number(it.topics)} new topic(s), ${Number(it.posts)} repl${it.posts === 1 ? 'y' : 'ies'}">${escapeHtml(it.tag)}<span>${Number(it.activity)}</span></button>`
        ).join('');
      } catch (e) {}
    }

    async function loadBoardDynamicRoster() {
      try {
        const res = await fetch('/api/board/roster');
        if (!res.ok) return;
        const data = await res.json();
        const userBox = document.getElementById('boardDynamicUserChips');
        if (userBox && Array.isArray(data.users)) {
          userBox.innerHTML = data.users.slice(0, 14).map(u => {
            const handle = (u.username || '').replace(/^@/, '');
            const verifiedIcon = u.verified ? '✅' : '👤';
            return `<button type="button" onclick="insertBoardTag('@${escapeHtml(handle)}', 'boardTopicBody')" title="${escapeHtml(u.full_name || handle)} (${escapeHtml(u.role || 'Peer')})" class="px-2 py-0.5 rounded-full bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border border-[#111111]/40">${verifiedIcon} @${escapeHtml(handle)}</button>`;
          }).join('');
        }
      } catch (e) {}
    }

    async function inspectCyberspaceUserProfile(usernameOrHandle) {
      const clean = (usernameOrHandle || '').replace(/^@/, '').trim();
      if (!clean) return;
      try {
        const res = await fetch(`/api/board/profile?user=${encodeURIComponent(clean)}`);
        if (!res.ok) return;
        const data = await res.json();
        const drawer = document.getElementById('boardProfileDrawer');
        const nameEl = document.getElementById('boardProfileName');
        const pillEl = document.getElementById('boardProfileVerifiedPill');
        const metaEl = document.getElementById('boardProfileMeta');
        const topicsEl = document.getElementById('boardProfileTopics');
        if (!drawer) return;
        drawer.classList.remove('hidden');

        const p = data.profile || {};
        if (nameEl) nameEl.innerText = `${p.full_name || clean} (@${clean})`;
        if (pillEl) {
          if (data.verified) {
            pillEl.innerText = '✅ Verified Cyberspace Citizen';
            pillEl.className = 'px-2 py-0.5 rounded-full bg-[#107a47]/10 text-[#107a47] border border-[#107a47] text-[10px] font-bold';
          } else {
            pillEl.innerText = '⚠️ Unverified Peer';
            pillEl.className = 'px-2 py-0.5 rounded-full bg-[#f4f8f0] text-[#111111] border border-[#111111]/40 text-[10px] font-bold';
          }
        }
        if (metaEl) {
          metaEl.innerHTML = `
            <div class="p-2 bg-[#f4f8f0] rounded-lg border border-[#111111]/25">
              <div class="text-[9px] text-[#5c5c5c] uppercase">Role / Institution</div>
              <div class="text-[#107a47] font-bold truncate">${escapeHtml(p.role || 'Mesh Collaborator')}</div>
            </div>
            <div class="p-2 bg-[#f4f8f0] rounded-lg border border-[#111111]/25">
              <div class="text-[9px] text-[#5c5c5c] uppercase">SHA-256 Attestation</div>
              <div class="text-[#111111] truncate">${escapeHtml(p.attestation_hash || 'pending-verification')}</div>
            </div>
            <div class="p-2 bg-[#f4f8f0] rounded-lg border border-[#111111]/25">
              <div class="text-[9px] text-[#5c5c5c] uppercase">Graph Contributions</div>
              <div class="text-[#111111] font-bold">${data.authored_count || 0} topics · ${data.reply_count || 0} replies · ${data.mentioned_count || 0} mentions</div>
            </div>
          `;
        }
        if (topicsEl) {
          const bioLine = p.bio ? `<div class="text-[#4a4a4a] italic pb-1">"${escapeHtml(p.bio)}"</div>` : '';
          const authoredLinks = (data.authored_topics || []).slice(0, 4).map(t =>
            `<span onclick="quickSearchBoardEntity('${escapeHtml(t.title)}')" class="cursor-pointer px-1.5 py-0.5 rounded-full bg-[#f4f8f0] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border border-[#111111]/30 inline-block mr-1 mb-1">📌 ${escapeHtml(t.title)}</span>`
          ).join('');
          topicsEl.innerHTML = `${bioLine}<div><span class="text-[#5c5c5c] mr-1">Filter Board:</span> <button type="button" onclick="quickSearchBoardEntity('@${escapeHtml(clean)}')" class="px-2 py-0.5 rounded-full bg-[#111111] hover:bg-[#107a47] text-[#ecf1e6] border border-[#111111]">🔍 Show All Threads with @${escapeHtml(clean)}</button> ${authoredLinks}</div>`;
        }
      } catch (e) {}
    }

    async function refreshBoardVerificationBadge() {
      const badge = document.getElementById('boardVerifiedBadge');
      const attBadge = document.getElementById('boardAttestationBadge');
      const subtext = document.getElementById('boardVerifierSubtext');
      const pendingCountBadge = document.getElementById('boardPendingVerifyCount');
      if (!badge) return;
      try {
        const unParam = encodeURIComponent(localStorage.getItem('tincan_username') || '');
        const res = await fetch(`/api/verify/status?peer_id=${encodeURIComponent(myPeerId)}&username=${unParam}`);
        if (!res.ok) return;
        const data = await res.json();
        const un = (data.profile && data.profile.username) || localStorage.getItem('tincan_username') || myPeerId;
        const pendingArr = data.pending_requests || [];
        if (pendingCountBadge) {
          pendingCountBadge.innerText = String(pendingArr.length);
        }
        if (data.verified) {
          badge.innerText = `✅ Verified Citizen (@${String(un).replace(/^@/, '')})`;
          badge.className = 'px-2 py-0.5 rounded-full bg-[#107a47]/10 text-[#107a47] border border-[#107a47] text-[10px] font-bold';
          if (attBadge && data.profile && data.profile.attestation_hash) {
            attBadge.innerText = `SHA256:${data.profile.attestation_hash.slice(0, 10)}`;
            attBadge.classList.remove('hidden');
          }
          if (subtext) {
            subtext.innerText = `Attested by @verifier-agent. You can tag yourself (@${String(un).replace(/^@/, '')}), tag peers, vote, and summon @ai-agents.`;
          }
        } else {
          badge.innerText = '⚠️ Unverified Peer — Fill Form';
          badge.className = 'px-2 py-0.5 rounded-full bg-[#ffffff] text-[#111111] border border-[#111111] text-[10px] font-bold';
        }
      } catch (e) {}
    }

    function prefillVerificationFormDefaults() {
      const fn = document.getElementById('verifyFormFullName');
      const un = document.getElementById('verifyFormUsername');
      const em = document.getElementById('verifyFormEmail');
      const ph = document.getElementById('verifyFormPhone');
      const rl = document.getElementById('verifyFormRole');
      if (fn && !fn.value && localStorage.getItem('tincan_fullname')) fn.value = localStorage.getItem('tincan_fullname');
      if (un && !un.value && localStorage.getItem('tincan_username')) un.value = localStorage.getItem('tincan_username');
      if (em && !em.value && localStorage.getItem('tincan_email')) em.value = localStorage.getItem('tincan_email');
      if (ph && !ph.value && localStorage.getItem('tincan_phone')) ph.value = localStorage.getItem('tincan_phone');
      if (rl && !rl.value && localStorage.getItem('tincan_role')) rl.value = localStorage.getItem('tincan_role');
    }

    function prefillVerificationFormFromSignal(payload) {
      prefillVerificationFormDefaults();
      const reqInp = document.getElementById('verifyFormRequestId');
      const reqBadge = document.getElementById('verifyFormRequestIdBadge');
      const codeInp = document.getElementById('verifyFormChallengeCode');
      const userInp = document.getElementById('verifyFormUsername');
      const fb = document.getElementById('verifyDispatchFeedback');
      const reqId = payload.request_id || (payload.form && payload.form.request_id) || '';
      const challenge = payload.challenge_code || (payload.form && payload.form.challenge_code) || '';
      if (reqInp && reqId) reqInp.value = reqId;
      if (reqBadge && reqId) reqBadge.innerText = `Form #${reqId}`;
      if (codeInp && challenge) codeInp.value = challenge;
      if (userInp && payload.target_username && !userInp.value) userInp.value = payload.target_username;
      if (fb) {
        fb.classList.remove('hidden');
        fb.innerHTML = `🛡️ <strong>@verifier-agent</strong> dispatched Verification Form <code>#${escapeHtml(reqId)}</code> with Challenge Code <code>${escapeHtml(challenge)}</code>. Complete &amp; submit the form below!`;
      }
      loadVerificationCenterData();
    }

    async function requestAgentVerificationForm() {
      const un = (localStorage.getItem('tincan_username') || '').trim();
      switchBoardTab('verify');
      try {
        const res = await fetch('/api/verify/send', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            username: un,
            reason: 'Requested Cyberspace Identity Verification Form from Discussion Board'
          })
        });
        const data = await res.json();
        playXpChime();
        spawnPacketFlight('@verifier-agent', myPeerId, 'verification_form', '🛡️ Verify Form');
        prefillVerificationFormFromSignal(data);
      } catch (err) {
        prefillVerificationFormDefaults();
      }
    }

    async function dispatchVerifierAgentFormFromCenter() {
      const targetEl = document.getElementById('verifyDispatchTargetUser');
      const reasonEl = document.getElementById('verifyDispatchReason');
      const targetUser = (targetEl ? targetEl.value.trim() : '') || (localStorage.getItem('tincan_username') || '').trim();
      const reason = (reasonEl ? reasonEl.value.trim() : '') || 'Mandatory Cyberspace Identity Verification';
      try {
        const res = await fetch('/api/verify/send', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            username: targetUser,
            reason
          })
        });
        const data = await res.json();
        playXpChime();
        spawnPacketFlight('@verifier-agent', targetUser || myPeerId, 'verification_form', '🛡️ Verify Form');
        prefillVerificationFormFromSignal(data);
      } catch (e) {}
    }

    async function submitCyberspaceVerificationForm() {
      const fullName = (document.getElementById('verifyFormFullName')?.value || '').trim();
      const username = (document.getElementById('verifyFormUsername')?.value || '').trim().replace(/^@/, '');
      const email = (document.getElementById('verifyFormEmail')?.value || '').trim();
      const phone = (document.getElementById('verifyFormPhone')?.value || '').trim();
      const role = (document.getElementById('verifyFormRole')?.value || 'Researcher / Student').trim();
      const bio = (document.getElementById('verifyFormBio')?.value || '').trim();
      const challengeCode = (document.getElementById('verifyFormChallengeCode')?.value || '').trim();
      const requestId = (document.getElementById('verifyFormRequestId')?.value || '').trim();
      const consent = Boolean(document.getElementById('verifyFormConsent')?.checked);
      const statusBox = document.getElementById('verifyFormStatusMsg');

      const showStatus = (msg, isErr = false) => {
        if (!statusBox) return;
        statusBox.classList.remove('hidden');
        statusBox.className = isErr
          ? 'p-2.5 rounded-xl text-xs bg-[#8a1c1c]/10 border border-[#8a1c1c] text-[#8a1c1c] font-mono'
          : 'p-2.5 rounded-xl text-xs bg-[#107a47]/10 border border-[#107a47] text-[#107a47] font-mono';
        statusBox.innerHTML = msg;
      };

      try {
        const res = await fetch('/api/verify/submit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            full_name: fullName,
            username,
            email,
            phone_number: phone,
            role,
            bio,
            challenge_code: challengeCode || undefined,
            request_id: requestId || undefined,
            consent_pii: consent
          })
        });
        const data = await res.json();
        if (!res.ok) {
          showStatus(`⚠️ Verification Error: ${escapeHtml(data.error || 'Could not verify identity')}`, true);
          return;
        }
        localStorage.setItem('tincan_registration_epoch', REGISTRATION_EPOCH);
        localStorage.setItem('tincan_fullname', fullName);
        localStorage.setItem('tincan_username', cleanHandle(username));
        localStorage.setItem('tincan_email', email);
        localStorage.setItem('tincan_phone', phone);
        localStorage.setItem('tincan_role', role);
        localStorage.setItem('tincan_consent_pii', 'true');
        const hudName = document.getElementById('hudAccountName');
        if (hudName) hudName.innerText = formatHandle(username);

        playXpChime();
        spawnPacketFlight(myPeerId, '@verifier-agent', 'verified', '✅ Attested');
        showStatus(`✅ <strong>Identity Verified &amp; Attested by @verifier-agent!</strong> Citizen Handle: <code>@${escapeHtml(username)}</code> · SHA-256 Attestation: <code>${escapeHtml(data.attestation_hash || '')}</code>`, false);
        await refreshBoardVerificationBadge();
        await loadBoardDynamicRoster();
        await loadVerificationCenterData();
        await loadCyberspaceBoard();
      } catch (err) {
        showStatus(`⚠️ Network error: ${escapeHtml(err.message)}`, true);
      }
    }

    async function loadVerificationCenterData() {
      try {
        const res = await fetch('/api/verify/list');
        if (!res.ok) return;
        const data = await res.json();
        const pendingEl = document.getElementById('verifyPendingList');
        const citizensEl = document.getElementById('verifyCitizensList');
        const countEl = document.getElementById('verifyCitizensCount');
        const badgeEl = document.getElementById('boardPendingVerifyCount');

        const reqs = (data.requests || []).filter(r => r.status === 'pending');
        if (badgeEl) badgeEl.innerText = String(reqs.length);

        if (pendingEl) {
          if (!reqs.length) {
            pendingEl.innerHTML = '<div class="text-[#5c5c5c] text-[11px] py-2">No pending verification forms. Click "Dispatch Form via @verifier-agent" above to generate a fresh challenge form.</div>';
          } else {
            pendingEl.innerHTML = reqs.map(r => `
              <div class="p-2 bg-[#f4f8f0] rounded-lg border border-[#111111]/30 flex items-center justify-between gap-2">
                <div>
                  <div class="text-[#111111] font-bold">#${escapeHtml(r.request_id)} · Challenge: <code>${escapeHtml(r.challenge_code || '')}</code></div>
                  <div class="text-[10px] text-[#4a4a4a]">Target: ${escapeHtml(r.target_username || r.peer_id)} · ${escapeHtml(r.reason || '')}</div>
                </div>
                <button type="button" onclick='prefillVerificationFormFromSignal(${JSON.stringify({request_id: r.request_id, challenge_code: r.challenge_code, target_username: r.target_username})})' class="px-2.5 py-1 rounded-full bg-[#111111] hover:bg-[#107a47] text-[#ecf1e6] font-bold text-[10px] shrink-0">
                  ✍️ Load Form
                </button>
              </div>
            `).join('');
          }
        }

        const citizens = data.verified_citizens || [];
        if (countEl) countEl.innerText = `${citizens.length} verified`;
        if (citizensEl) {
          if (!citizens.length) {
            citizensEl.innerHTML = '<div class="text-[#5c5c5c] text-[11px] py-2">No verified citizens yet.</div>';
          } else {
            citizensEl.innerHTML = citizens.map(c => `
              <div onclick="inspectCyberspaceUserProfile('${escapeHtml(c.username)}')" class="cursor-pointer p-2 bg-[#f4f8f0] hover:bg-[#ecf1e6] rounded-lg border border-[#107a47]/50 flex items-center justify-between gap-2 transition">
                <div>
                  <div class="text-[#107a47] font-bold">✅ @${escapeHtml(c.username)} <span class="text-[#4a4a4a] font-normal">(${escapeHtml(c.full_name)})</span></div>
                  <div class="text-[10px] text-[#4a4a4a]">${escapeHtml(c.role || 'Citizen')} · ${escapeHtml(c.bio || '')}</div>
                </div>
                <span class="px-1.5 py-0.5 rounded-full bg-[#ffffff] text-[#111111] border border-[#111111]/30 text-[9px]">SHA256:${escapeHtml((c.attestation_hash || '').slice(0, 10))}</span>
              </div>
            `).join('');
          }
        }
      } catch (e) {}
    }

    async function loadCyberspaceBoard() {
      refreshBoardVerificationBadge();
      loadBoardDynamicRoster();
      loadBoardTrending();
      loadBoardAiSuggestions(false);
      if (buildBoardQuery()) { searchCyberspaceBoard(); return; }
      try {
        const sortBy = document.getElementById('boardSortSelect')?.value || 'hot';
        const res = await fetch(`/api/board/topics?limit=40&sort_by=${encodeURIComponent(sortBy)}`);
        if (!res.ok) return;
        const data = await res.json();
        const topics = Array.isArray(data.topics) ? data.topics : [];
        topics.forEach(t => { if (t && t.topic_id) _boardTopicsById[t.topic_id] = t; });
        const gBadge = document.getElementById('boardGraphStatsBadge');
        if (gBadge && data.graph_stats) {
          gBadge.innerText = `● Graph: ${data.graph_stats.total_nodes || 0} nodes · ${data.graph_stats.total_edges || 0} edges`;
        }
        const curatedBadge = document.getElementById('boardCuratedCountBadge');
        if (curatedBadge) {
          curatedBadge.textContent = String(topics.filter(t => t.curated).length);
        }
        renderCyberspaceTopics(topics, false);
        if (activeBoardTab === 'feed') loadBoardFeedAndThreads();
      } catch (e) {}
    }

    let boardFeedFilter = 'all';
    function setBoardFeedFilter(mode) {
      boardFeedFilter = mode || 'all';
      ['all', 'curated', 'solved'].forEach(m => {
        const btn = document.getElementById(`boardFeedFilter-${m}`);
        if (!btn) return;
        if (m === boardFeedFilter) {
          btn.className = 'px-3 py-1 rounded-full bg-[#111111] text-[#ecf1e6] border border-[#111111] font-bold text-[11px] transition';
        } else if (m === 'solved') {
          btn.className = 'px-3 py-1 rounded-full bg-[#f4f8f0] hover:bg-[#ecf1e6] text-[#107a47] border border-[#107a47]/50 text-[11px] transition';
        } else {
          btn.className = 'px-3 py-1 rounded-full bg-[#f4f8f0] hover:bg-[#ecf1e6] text-[#111111] border border-[#111111]/40 text-[11px] transition';
        }
      });
      loadBoardFeedAndThreads();
    }

    function isBoardAiAuthor(post) {
      if (!post) return false;
      if (post.is_agent) return true;
      const raw = String(post.author_username || post.author || '').trim().toLowerCase();
      const cleaned = raw.replace(/^@/, '');
      return /^(ai:|agent:)/.test(cleaned) || cleaned.endsWith('-brain') || cleaned.endsWith('-agent') || cleaned.includes('agent') || cleaned === 'claude-sonnet' || cleaned === 'gpt-4o' || cleaned === 'deepseek-r1';
    }

    function formatBoardActivityScore(topic) {
      const posts = Array.isArray(topic && topic.posts) ? topic.posts : [];
      const raw = Number((topic && topic.activity_score !== undefined && topic.activity_score !== null) ? topic.activity_score : posts.length);
      return Number.isInteger(raw) ? String(raw) : raw.toFixed(1);
    }

    async function loadBoardFeedAndThreads() {
      const feedEl = document.getElementById('boardCuratedFeedList');
      const threadsEl = document.getElementById('boardActiveThreadsList');
      const statusEl = document.getElementById('boardFeedStatusMeta');
      if (!feedEl && !threadsEl) return;
      const q = (document.getElementById('boardFeedFilterInput')?.value || '').trim().toLowerCase();
      try {
        const res = await fetch('/api/board/topics?limit=50&sort_by=activity');
        if (!res.ok) return;
        const data = await res.json();
        const allTopics = Array.isArray(data.topics) ? data.topics.slice() : [];
        allTopics.forEach(t => { if (t && t.topic_id) _boardTopicsById[t.topic_id] = t; });

        const totalAll = allTopics.length;
        const totalCurated = allTopics.filter(t => Boolean(t.curated)).length;
        const totalSolved = allTopics.filter(t => Boolean(t.accepted_post_id || t.resolved)).length;

        const btnAll = document.getElementById('boardFeedFilter-all');
        const btnCur = document.getElementById('boardFeedFilter-curated');
        const btnSol = document.getElementById('boardFeedFilter-solved');
        if (btnAll) btnAll.textContent = `All (${totalAll})`;
        if (btnCur) btnCur.textContent = `★ Curated (${totalCurated})`;
        if (btnSol) btnSol.textContent = `✓ Solved (${totalSolved})`;

        const curatedBadge = document.getElementById('boardCuratedCountBadge');
        if (curatedBadge) curatedBadge.textContent = String(totalCurated);

        let topics = allTopics.slice();
        if (boardFeedFilter === 'curated') {
          topics = topics.filter(t => Boolean(t.curated));
        } else if (boardFeedFilter === 'solved') {
          topics = topics.filter(t => Boolean(t.accepted_post_id || t.resolved));
        }
        if (q) {
          topics = topics.filter(t =>
            (t.title || '').toLowerCase().includes(q) ||
            (t.body || '').toLowerCase().includes(q) ||
            (t.author_username || '').toLowerCase().includes(q) ||
            (t.tags || []).some(tag => String(tag).toLowerCase().includes(q)) ||
            (t.posts || []).some(p => (p.body || '').toLowerCase().includes(q))
          );
        }
        if (statusEl) statusEl.textContent = `${topics.length} topic(s) · ${boardFeedFilter}`;

        if (feedEl) {
          if (!topics.length) {
            feedEl.innerHTML = '<div class="p-4 text-center text-xs text-[#5c5c5c] border border-dashed border-[#111111]/30 rounded-xl bg-[#f4f8f0]">No feed items match right now.</div>';
          } else {
            feedEl.innerHTML = topics.map(t => {
              const posts = Array.isArray(t.posts) ? t.posts : [];
              const actScore = formatBoardActivityScore(t);
              const upvotes = Number(t.upvotes ?? t.score ?? t.votes ?? 0);
              const author = String(t.author_username || 'peer').replace(/^@/, '');
              const isSolved = Boolean(t.accepted_post_id || t.resolved);
              const tagsHtml = (t.tags || []).slice(0, 4).map(tg => `<span class="text-[#107a47] font-semibold text-[10px]">#${escapeHtml(tg)}</span>`).join(' ');
              const cardSurface = t.curated
                ? 'bg-[#f4f8f0] border-[#111111]'
                : 'bg-[#ffffff] border-[#111111]/40 hover:border-[#111111]';
              const starCls = t.curated
                ? 'bg-[#107a47] text-[#ffffff] border-[#107a47]'
                : 'bg-[#ffffff] text-[#111111] border-[#111111]/50 hover:border-[#111111]';
              return `
                <div class="p-3 rounded-xl border space-y-1.5 transition ${cardSurface}">
                  <div class="flex flex-wrap items-center justify-between gap-1.5 text-[10px] font-mono">
                    <div class="flex flex-wrap items-center gap-1.5 min-w-0">
                      ${t.curated ? '<span class="text-[#107a47] font-bold">★ CURATED</span><span class="text-[#5c5c5c]">·</span>' : ''}
                      ${isSolved ? '<span class="text-[#107a47] font-bold">✓ SOLVED</span><span class="text-[#5c5c5c]">·</span>' : ''}
                      ${tagsHtml ? `${tagsHtml}<span class="text-[#5c5c5c]">·</span>` : ''}
                      <span class="text-[#4a4a4a]">@${escapeHtml(author)}</span>
                      <span class="text-[#5c5c5c]">·</span>
                      <span class="px-1.5 py-0.2 rounded-full bg-[#107a47]/10 text-[#107a47] border border-[#107a47]/40 font-semibold">ACTIVITY SCORE ${actScore}</span>
                    </div>
                    <button type="button" onclick="curateCyberspaceTopic('${escapeHtml(t.topic_id)}', ${t.curated ? 'false' : 'true'})" class="px-2 py-0.5 rounded-full border text-[10px] font-semibold shrink-0 transition ${starCls}">${t.curated ? '★ Curated' : '☆ Curate'}</button>
                  </div>
                  <button type="button" onclick="openBoardThreadFromFeed('${escapeHtml(t.topic_id)}')" class="text-left font-bold text-[#111111] hover:text-[#107a47] text-[13px] leading-snug block w-full">${escapeHtml(t.title || t.topic_id)}</button>
                  <p class="text-[11px] text-[#4a4a4a] line-clamp-2 font-sans leading-relaxed">${escapeHtml((t.body || '').slice(0, 180))}</p>
                  <div class="flex flex-wrap items-center justify-between gap-2 text-[10px] text-[#4a4a4a] pt-0.5">
                    <span>▲ ${upvotes} upvotes · ${posts.length} thread msgs</span>
                    <div class="flex flex-wrap items-center gap-2 font-semibold">
                      <button type="button" onclick="openBoardThreadFromFeed('${escapeHtml(t.topic_id)}')" class="text-[#111111] hover:text-[#107a47]">[Open Thread →]</button>
                      <button type="button" onclick="openWindowInstance('win-board', { topic: '${escapeHtml(t.topic_id)}', boardTab: 'discussions', subtitle: '${escapeHtml(String(t.title || t.topic_id).slice(0, 42))}' })" class="text-[#111111] hover:text-[#107a47]" title="Open thread in a new Cyberspace Board window">[↗ New Board]</button>
                      <button type="button" onclick="curateCyberspaceTopic('${escapeHtml(t.topic_id)}', ${t.curated ? 'false' : 'true'})" class="text-[#111111] hover:text-[#107a47]">[${t.curated ? 'Curate ★' : 'Curate ☆'}]</button>
                      <button type="button" onclick="loadTopicIntoWorkstation('${escapeHtml(t.topic_id)}')" class="text-[#107a47] hover:underline">[Load in Workstation]</button>
                      <button type="button" onclick="openWindowInstance('win-agentspace', { scope: 'topic', owner: '${escapeHtml(t.topic_id)}', subtitle: 'Topic · ${escapeHtml(String(t.title || t.topic_id).slice(0, 36))}' })" class="text-[#107a47] hover:underline" title="Open topic files in a new Workstation window">[↗ New Win]</button>
                    </div>
                  </div>
                </div>
              `;
            }).join('');
          }
        }

        if (threadsEl) {
          const ranked = topics.slice().sort((a, b) => Number(b.activity_score || 0) - Number(a.activity_score || 0));
          if (!ranked.length) {
            threadsEl.innerHTML = '<div class="p-4 text-center text-xs text-[#5c5c5c] border border-dashed border-[#111111]/30 rounded-xl bg-[#f4f8f0]">No active threads yet.</div>';
          } else {
            threadsEl.innerHTML = ranked.map((t, idx) => {
              const posts = Array.isArray(t.posts) ? t.posts : [];
              const lastPost = posts[posts.length - 1];
              const actScore = formatBoardActivityScore(t);
              if (idx === 0) {
                const recentReplies = posts.slice(-2);
                const repliesHtml = recentReplies.length
                  ? recentReplies.map(p => {
                      const pAuthor = String(p.author_username || p.author || 'peer').trim().replace(/^@/, '');
                      const isAi = isBoardAiAuthor(p);
                      if (isAi) {
                        return `
                          <div class="p-2 rounded-lg bg-[#107a47]/10 border border-[#107a47] space-y-0.5">
                            <div class="font-mono text-[10px] font-bold text-[#107a47]">[AI] @${escapeHtml(pAuthor)}${p.is_agent ? ' (Free Model Suggest)' : ''}</div>
                            <div class="text-[11px] text-[#111111] font-sans leading-snug">${escapeHtml((p.body || '').slice(0, 160))}</div>
                          </div>
                        `;
                      }
                      return `
                        <div class="p-2 rounded-lg bg-[#f4f8f0] border border-[#111111]/20 space-y-0.5">
                          <div class="font-mono text-[10px] font-semibold text-[#4a4a4a]">@${escapeHtml(pAuthor)}</div>
                          <div class="text-[11px] text-[#111111] font-sans leading-snug">${escapeHtml((p.body || '').slice(0, 160))}</div>
                        </div>
                      `;
                    }).join('')
                  : `<div class="p-2 rounded-lg bg-[#f4f8f0] border border-[#111111]/20 text-[11px] text-[#4a4a4a] font-sans leading-snug">${escapeHtml((t.body || '').slice(0, 140))}</div>`;
                return `
                  <div class="p-3 rounded-xl bg-[#ffffff] border border-[#111111] space-y-2">
                    <div class="flex items-center justify-between gap-2 text-[10px] font-mono">
                      <span class="font-bold text-[#107a47] uppercase tracking-wider">#1 MOST ACTIVE · ACTIVITY SCORE ${actScore}</span>
                      <span class="px-1.5 py-0.2 rounded-full bg-[#f4f8f0] text-[#111111] border border-[#111111]/30 shrink-0">${posts.length} MSGS</span>
                    </div>
                    <button type="button" onclick="openBoardThreadFromFeed('${escapeHtml(t.topic_id)}')" class="text-left font-bold text-[#111111] hover:text-[#107a47] text-[13px] leading-snug block w-full">${escapeHtml(t.title || t.topic_id)}</button>
                    <div class="space-y-1.5">${repliesHtml}</div>
                    <div class="flex items-center gap-1.5 pt-0.5">
                      <input id="threadQuickReply-${t.topic_id}" type="text" placeholder="Reply in thread (@peer, @agent, #tag)..." onkeydown="if(event.key==='Enter')replyQuickThread('${t.topic_id}')" class="flex-1 px-2.5 py-1 rounded-lg bg-[#ffffff] border border-[#111111] text-[#111111] text-[11px] focus:border-[#107a47] focus:outline-none" />
                      <button type="button" onclick="replyQuickThread('${t.topic_id}')" class="px-2.5 py-1 rounded-full bg-[#111111] hover:bg-[#107a47] text-[#ecf1e6] font-bold text-[10px] shrink-0 transition">Send ↵</button>
                    </div>
                  </div>
                `;
              }
              return `
                <div class="p-2.5 rounded-xl bg-[#f4f8f0] border border-[#111111]/35 space-y-1.5">
                  <div class="flex items-center justify-between gap-2 text-[10px] font-mono">
                    <span class="text-[#5c5c5c] font-semibold">#${idx + 1} · ACTIVITY SCORE ${actScore}</span>
                    <span class="text-[#5c5c5c] shrink-0">${posts.length} MSGS</span>
                  </div>
                  <button type="button" onclick="openBoardThreadFromFeed('${escapeHtml(t.topic_id)}')" class="truncate text-left font-bold text-[#111111] hover:text-[#107a47] text-xs block w-full">${escapeHtml(t.title || t.topic_id)}</button>
                  <div class="text-[10px] text-[#4a4a4a] font-sans truncate">
                    ${lastPost ? `@${escapeHtml(String(lastPost.author_username || 'peer').replace(/^@/, ''))}: ${escapeHtml((lastPost.body || '').slice(0, 90))}` : escapeHtml((t.body || '').slice(0, 90))}
                  </div>
                  <div class="flex items-center gap-1.5">
                    <input id="threadQuickReply-${t.topic_id}" type="text" placeholder="Reply in #thread..." onkeydown="if(event.key==='Enter')replyQuickThread('${t.topic_id}')" class="flex-1 px-2 py-1 rounded-lg bg-[#ffffff] border border-[#111111] text-[#111111] text-[11px] focus:border-[#107a47] focus:outline-none" />
                    <button type="button" onclick="replyQuickThread('${t.topic_id}')" class="px-2.5 py-1 rounded-full bg-[#111111] hover:bg-[#107a47] text-[#ecf1e6] font-bold text-[10px] transition">Send ↵</button>
                  </div>
                </div>
              `;
            }).join('');
          }
        }
      } catch (e) {}
    }

    function openAgentSpaceWithTopic(topicId, topicTitle = '') {
      const tid = String(topicId || '').trim();
      if (!tid) return;
      if (typeof selectWorkstationTopicResult === 'function') {
        selectWorkstationTopicResult(tid);
      } else {
        if (typeof switchSpaceScope === 'function') switchSpaceScope('topic');
        const ownerInput = document.getElementById('spaceOwnerInput');
        if (ownerInput) ownerInput.value = tid;
        if (typeof resolveAndLoadSpaceOwner === 'function') resolveAndLoadSpaceOwner();
      }
    }

    async function loadTopicIntoWorkstation(topicId) {
      let tid = String(topicId || '').trim();
      if (!tid) return;
      let topicTitle = (_boardTopicsById[tid] && _boardTopicsById[tid].title) || '';
      if (!topicTitle && typeof fetch === 'function') {
        try {
          const res = await fetch(`/api/board/topic?id=${encodeURIComponent(tid)}&increment_views=0`);
          if (res.ok) {
            const data = await res.json();
            if (data && data.topic) {
              _boardTopicsById[tid] = data.topic;
              topicTitle = data.topic.title || '';
              if (data.topic.topic_id) tid = data.topic.topic_id;
            }
          }
        } catch (e) {}
      }

      const spWin = document.getElementById('win-agentspace');
      if (spWin) {
        const isClosed = spWin.style.display === 'none' || spWin.classList.contains('hidden') || spWin.classList.contains('minimized');
        if (isClosed) {
          if (typeof toggleWindow === 'function') {
            toggleWindow('win-agentspace');
          } else {
            spWin.classList.remove('hidden', 'minimized');
            spWin.style.display = 'flex';
          }
        } else if (typeof bringToFront === 'function') {
          bringToFront(spWin);
        }
      }
      if (typeof switchFinderTab === 'function') switchFinderTab('files');
      openAgentSpaceWithTopic(tid, topicTitle);
      if (typeof showQuickNotification === 'function') {
        showQuickNotification(`📂 Loaded ${topicTitle || tid} in Workstation`);
      }
    }

    function openBoardThreadFromFeed(topicId) {
      activeBoardTopicId = topicId;
      switchBoardTab('discussions');
      loadCyberspaceBoard();
      if (typeof notifyParentInstanceTitle === 'function') {
        const meta = _boardTopicsById[topicId];
        notifyParentInstanceTitle(meta && meta.title ? meta.title.slice(0, 48) : ('Topic: ' + topicId));
      }
    }

    function promptNewBoardThread() {
      switchBoardTab('discussions');
      const inp = document.getElementById('boardSearchInput');
      if (inp) {
        inp.value = '/thread ';
        inp.focus();
      }
    }

    async function curateCyberspaceTopic(topicId, nextState) {
      try {
        const res = await fetch('/api/board/curate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic_id: topicId, peer_id: myPeerId, curated: nextState })
        });
        if (res.ok) {
          playXpChime();
          await loadBoardFeedAndThreads();
          await loadCyberspaceBoard();
        }
      } catch (e) {}
    }

    async function replyQuickThread(topicId) {
      if (!requireVerifiedIdentity('reply in an active thread')) {
        requestAgentVerificationForm();
        return;
      }
      const inp = document.getElementById(`threadQuickReply-${topicId}`);
      const body = inp ? inp.value.trim() : '';
      if (!body) return;
      const username = (localStorage.getItem('tincan_username') || '').trim();
      try {
        const res = await fetch('/api/board/reply', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic_id: topicId, peer_id: myPeerId, username, body, auto_agent_reply: true })
        });
        if (res.ok) {
          if (inp) inp.value = '';
          playXpChime();
          await loadBoardFeedAndThreads();
        }
      } catch (e) {}
    }

    async function searchCyberspaceBoard() {
      const q = buildBoardQuery();
      if (!q) {
        resetCyberspaceSearch();
        return;
      }
      try {
        const sortBy = document.getElementById('boardSortSelect')?.value || 'hot';
        // Hybrid (BM25 + GraphRAG) always runs behind the bar; there is no mode picker.
        const res = await fetch(`/api/board/query?q=${encodeURIComponent(q)}&top_k=15&sort_by=${encodeURIComponent(sortBy)}`);
        if (!res.ok) return;
        const data = await res.json();
        // "/topic name" and finished #tags become chips so the bar shows what is applied.
        const parsed = data.parsed || {};
        const inp = document.getElementById('boardSearchInput');
        if (parsed.command === 'topic' && inp && /^\/topic\b/i.test(inp.value.trim())) {
          inp.value = '';
          (parsed.tags || []).forEach(t => { if (!boardChips.includes('#' + t)) boardChips.push('#' + t); });
          if (parsed.verified_only && !boardChips.includes('is:verified')) boardChips.push('is:verified');
          renderBoardChips();
        }
        const synBox = document.getElementById('boardSynthesisBox');
        const synText = document.getElementById('boardSynthesisText');
        const subEntities = document.getElementById('boardSubgraphEntities');
        if (synBox && synText) {
          synBox.classList.toggle('hidden', !data.synthesis);
          synText.innerHTML = `<strong>${escapeHtml(data.synthesis || '')}</strong>`;
          if (subEntities) {
            const seeds = ((data.diagnostics || {}).subgraph || {}).seed_entities || [];
            subEntities.innerHTML = seeds.slice(0, 14).map(n =>
              `<span onclick="quickSearchBoardEntity('${escapeHtml(n)}')" class="cursor-pointer px-2 py-0.5 rounded-full border text-[10px] bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border-[#111111]/40">${escapeHtml(n)}</span>`
            ).join('');
          }
        }
        const results = data.results || [];
        results.forEach(t => { if (t && t.topic_id) _boardTopicsById[t.topic_id] = t; });
        renderBoardRankDiagnostics(data);
        renderCyberspaceTopics(results, (data.diagnostics || {}).mode === 'hybrid');
      } catch (e) {}
    }

    function resetCyberspaceSearch() {
      const inp = document.getElementById('boardSearchInput');
      if (inp) inp.value = '';
      boardChips = [];
      renderBoardChips();
      closeBoardSuggest();
      const synBox = document.getElementById('boardSynthesisBox');
      if (synBox) synBox.classList.add('hidden');
      renderBoardRankDiagnostics(null);
      loadCyberspaceBoard();
    }

    async function voteCyberspaceItem(targetType, targetId, direction) {
      try {
        const res = await fetch('/api/board/vote', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            target_type: targetType,
            target_id: targetId,
            peer_id: myPeerId,
            direction
          })
        });
        if (res.ok) {
          playXpChime();
          await loadCyberspaceBoard();
        }
      } catch (e) {}
    }

    async function markAcceptedSolution(topicId, postId) {
      try {
        const res = await fetch('/api/board/solution', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            topic_id: topicId,
            post_id: postId,
            peer_id: myPeerId
          })
        });
        if (res.ok) {
          activeBoardTopicId = topicId;
          playXpChime();
          await loadCyberspaceBoard();
        }
      } catch (e) {}
    }

    async function togglePinTopic(topicId, currentPinned) {
      try {
        const res = await fetch('/api/board/topic/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            topic_id: topicId,
            peer_id: myPeerId,
            pinned: !currentPinned
          })
        });
        if (res.ok) {
          await loadCyberspaceBoard();
        }
      } catch (e) {}
    }

    async function deleteCyberspaceTopic(topicId) {
      if (!window.confirm('Delete this topic from the Cyberspace Knowledge Base?')) return;
      try {
        const res = await fetch('/api/board/topic/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic_id: topicId, peer_id: myPeerId })
        });
        if (res.ok) {
          await loadCyberspaceBoard();
        }
      } catch (e) {}
    }

    async function deleteCyberspacePost(topicId, postId) {
      try {
        const res = await fetch('/api/board/post/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ post_id: postId, peer_id: myPeerId })
        });
        if (res.ok) {
          activeBoardTopicId = topicId;
          await loadCyberspaceBoard();
        }
      } catch (e) {}
    }

    function setReplyToNestedPost(topicId, postId, authorHandle) {
      activeReplyParentPostByTopic[topicId] = postId;
      const indicator = document.getElementById(`replyParentBanner-${topicId}`);
      const inp = document.getElementById(`replyInput-${topicId}`);
      if (indicator) {
        indicator.classList.remove('hidden');
        indicator.innerHTML = `<span>↪ Replying to post <code>#${escapeHtml(postId)}</code> (@${escapeHtml(authorHandle)})</span> <button type="button" onclick="clearReplyToNestedPost('${topicId}')" class="text-[#8a1c1c] hover:underline ml-2">✕ Cancel</button>`;
      }
      if (inp) {
        if (!inp.value.includes(`@${authorHandle}`)) {
          inp.value = `@${authorHandle} ` + inp.value;
        }
        inp.focus();
      }
    }

    function clearReplyToNestedPost(topicId) {
      delete activeReplyParentPostByTopic[topicId];
      const indicator = document.getElementById(`replyParentBanner-${topicId}`);
      if (indicator) indicator.classList.add('hidden');
    }

    function renderCyberspaceTopics(topics, isSearchResult = false) {
      const feed = document.getElementById('boardTopicsFeed');
      if (!feed) return;
      if (!topics.length) {
        feed.innerHTML = '<div class="p-4 bg-[#ffffff] rounded-xl border border-[#111111]/20 text-center text-[#5c5c5c] font-mono">No matching Cyberspace topics found. Start a new topic above!</div>';
        return;
      }

      const myUn = (localStorage.getItem('tincan_username') || '').toLowerCase();

      feed.innerHTML = topics.map(t => {
        if (t && t.topic_id) _boardTopicsById[t.topic_id] = t;
        const author = (t.author_username || 'peer').replace(/^@/, '');
        const posts = t.posts || [];
        const isExpanded = activeBoardTopicId === t.topic_id || isSearchResult;
        const canModifyTopic = isAdmin || t.author_peer_id === myPeerId || (myUn && author.toLowerCase() === myUn);

        const scoreBadges = (t.bm25_score !== undefined || t.graphrag_score !== undefined) ? `
          <details class="ubar-rank-mini font-mono"><summary>how this ranked</summary><div class="ubar-rank-mini-body space-y-1">
          <div class="flex flex-wrap items-center gap-1 font-mono text-[10px]">
            <span class="px-1.5 py-0.5 rounded-full bg-[#111111] text-[#ecf1e6] font-semibold">Hybrid: ${Number(t.score || 0).toFixed(3)}</span>
            <span class="px-1.5 py-0.5 rounded-full bg-[#f4f8f0] text-[#107a47] border border-[#107a47]/40">BM25: ${Number(t.bm25_score || 0).toFixed(3)}</span>
            <span class="px-1.5 py-0.5 rounded-full bg-[#ecf1e6] text-[#111111] border border-[#111111]/25">GraphRAG: ${Number(t.graphrag_score || 0).toFixed(3)}</span>
          </div>
          ${(t.matched_terms && t.matched_terms.length) ? `<div class="text-[10px] text-[#4a4a4a]">Matched terms: ${t.matched_terms.map(x => escapeHtml(x)).join(', ')}</div>` : ''}
          ${(t.graph_paths && t.graph_paths.length) ? `<div class="text-[10px] text-[#4a4a4a]">Graph paths: ${t.graph_paths.map(p => escapeHtml(p)).join(' · ')}</div>` : ''}
          </div></details>
        ` : '';

        const snippetHtml = t.highlighted_snippet ? `
          <div class="p-2 bg-[#f4f8f0] border border-[#107a47]/35 rounded-lg text-[11px] text-[#111111] font-mono">
            ${t.highlighted_snippet}
          </div>
        ` : '';

        const graphPathsHtml = '';

        const tagsHtml = (t.tags || []).map(tag =>
          `<span onclick="quickSearchBoardEntity('#${escapeHtml(tag)}')" class="cursor-pointer px-1.5 py-0.5 rounded-full bg-[#f4f8f0] hover:bg-[#ecf1e6] text-[#111111] border border-[#111111]/20 font-mono text-[10px]">#${escapeHtml(tag)}</span>`
        ).join('');

        // Organize posts with nested indentation for parent_post_id
        const postMap = {};
        posts.forEach(p => { postMap[p.post_id] = p; });

        const postsHtml = posts.map(p => {
          const pAuthor = (p.author_username || 'peer').replace(/^@/, '');
          const isAgent = Boolean(p.is_agent) || isBoardAiAuthor(p);
          const isAccepted = Boolean(p.is_accepted);
          const parentPost = p.parent_post_id ? postMap[p.parent_post_id] : null;
          const indentCls = p.parent_post_id ? 'ml-5 border-l-2 border-l-[#107a47]' : '';
          const canDeletePost = isAdmin || p.author_peer_id === myPeerId || (myUn && pAuthor.toLowerCase() === myUn);

          return `
            <div class="p-2.5 rounded-lg border ${indentCls} ${isAccepted ? 'bg-[#107a47]/10 border-[#107a47]' : (isAgent ? 'bg-[#f4f8f0] border-[#107a47]/50' : 'bg-[#ffffff] border-[#111111]/20')} space-y-1.5">
              <div class="flex flex-wrap items-center justify-between gap-1 font-mono text-[10px]">
                <div class="flex items-center gap-1.5 flex-wrap">
                  <span onclick="${isAgent ? `quickSearchBoardEntity('@${escapeHtml(pAuthor)}')` : `inspectCyberspaceUserProfile('${escapeHtml(pAuthor)}')`}" class="cursor-pointer font-bold ${isAgent ? 'text-[#107a47]' : 'text-[#111111]'} hover:underline">
                    ${isAgent ? '[AI]' : '✅'} @${escapeHtml(pAuthor)}
                  </span>
                  ${parentPost ? `<span class="text-[#5c5c5c]">↪ in reply to @${escapeHtml((parentPost.author_username || 'peer').replace(/^@/, ''))}</span>` : ''}
                  ${isAccepted ? '<span class="px-1.5 py-0.5 rounded-full bg-[#107a47] text-[#ffffff] font-bold">✅ Accepted Solution</span>' : ''}
                </div>
                <div class="flex items-center gap-1.5">
                  <button type="button" onclick="voteCyberspaceItem('post', '${p.post_id}', 'up')" class="px-1.5 py-0.5 rounded-full bg-[#ffffff] hover:bg-[#f4f8f0] text-[#107a47] border border-[#111111]/20">▲ ${Number(p.upvotes || 0)}</button>
                  <button type="button" onclick="setReplyToNestedPost('${t.topic_id}', '${p.post_id}', '${escapeHtml(pAuthor)}')" class="px-1.5 py-0.5 rounded-full bg-[#ffffff] hover:bg-[#f4f8f0] text-[#111111] border border-[#111111]/20">↪ Reply</button>
                  ${!isAccepted ? `<button type="button" onclick="markAcceptedSolution('${t.topic_id}', '${p.post_id}')" class="px-1.5 py-0.5 rounded-full bg-[#ffffff] hover:bg-[#f4f8f0] text-[#5c5c5c] hover:text-[#107a47] border border-[#111111]/20" title="Mark as Accepted Solution">✓ Solution</button>` : ''}
                  ${canDeletePost ? `<button type="button" onclick="deleteCyberspacePost('${t.topic_id}', '${p.post_id}')" class="px-1.5 py-0.5 rounded-full text-[#8a1c1c] hover:bg-[#8a1c1c]/10">🗑️</button>` : ''}
                  <span class="text-[#5c5c5c]">${p.created_at ? new Date(p.created_at * 1000).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}) : ''}</span>
                </div>
              </div>
              <div class="text-[#111111] text-xs leading-relaxed">${formatBoardMentions(p.body)}</div>
            </div>
          `;
        }).join('');

        return `
          <div class="p-3.5 bg-[#ffffff] rounded-xl border ${t.pinned ? 'border-[#111111]' : (t.resolved ? 'border-[#107a47]' : 'border-[#111111]/20')} hover:border-[#111111] transition space-y-2.5 shadow-sm">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5">
              <div class="flex items-center gap-1.5 flex-wrap">
                ${t.pinned ? '<span class="px-2 py-0.5 rounded-full bg-[#111111] text-[#ecf1e6] font-mono text-[10px] font-bold">📌 PINNED</span>' : ''}
                ${t.resolved ? '<span class="px-2 py-0.5 rounded-full bg-[#107a47] text-[#ffffff] font-mono text-[10px] font-bold">✅ SOLVED</span>' : ''}
                <span onclick="setBoardCategoryFilter('${escapeHtml(t.category || 'cyberspace')}')" class="cursor-pointer px-2 py-0.5 rounded-full bg-[#f4f8f0] text-[#111111] border border-[#111111]/20 font-mono text-[10px] uppercase font-bold">#${escapeHtml(t.category || 'cyberspace')}</span>
                <h4 onclick="toggleBoardTopicThread('${t.topic_id}')" class="cursor-pointer font-bold text-[#111111] text-sm hover:text-[#107a47] transition">${escapeHtml(t.title)}</h4>
              </div>
              <div class="flex items-center gap-1.5 font-mono text-[10px]">
                ${scoreBadges}
                <div class="flex items-center bg-[#f4f8f0] rounded-full border border-[#111111]/20 px-2 py-0.5 gap-1.5">
                  <button type="button" onclick="voteCyberspaceItem('topic', '${t.topic_id}', 'up')" class="text-[#107a47] hover:underline font-bold" title="Upvote Topic">▲</button>
                  <span class="text-[#111111] font-bold">${Number(t.upvotes || 0)}</span>
                  <button type="button" onclick="voteCyberspaceItem('topic', '${t.topic_id}', 'down')" class="text-[#5c5c5c] hover:text-[#8a1c1c]" title="Downvote Topic">▼</button>
                </div>
              </div>
            </div>

            <div class="text-[#111111] text-xs leading-relaxed">${formatBoardMentions(t.body)}</div>

            ${snippetHtml}

            <div class="flex flex-wrap items-center justify-between gap-2 pt-1.5 border-t border-[#111111]/15">
              <div class="flex flex-wrap items-center gap-1.5">
                <span onclick="inspectCyberspaceUserProfile('${escapeHtml(author)}')" class="cursor-pointer font-mono text-[10px] ${t.author_verified ? 'text-[#107a47]' : 'text-[#5c5c5c]'} font-semibold hover:underline">
                  ${t.author_verified ? '✅' : '⚠️'} @${escapeHtml(author)}
                </span>
                <span class="text-[#5c5c5c]">·</span>
                <span class="font-mono text-[10px] text-[#5c5c5c]">👁️ ${Number(t.views || 1)} views</span>
                <span class="text-[#5c5c5c]">·</span>
                ${tagsHtml}
              </div>
              <div class="flex flex-wrap items-center gap-1.5 font-mono text-[10px]">
                <button type="button" onclick="loadTopicIntoWorkstation('${t.topic_id}')" class="px-2.5 py-0.5 rounded-full bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border border-[#111111] font-bold transition" title="Load topic in Workstation">[Load in Workstation]</button>
                <button type="button" onclick="openWindowInstance('win-agentspace', { scope: 'topic', owner: '${t.topic_id}', subtitle: 'Topic · ${escapeHtml(String(t.title || t.topic_id).slice(0, 36))}' })" class="px-2 py-0.5 rounded-full bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#107a47] border border-[#107a47] font-bold transition" title="Open topic in a new Workstation window">[↗ New Win]</button>
                <button type="button" onclick="togglePinTopic('${t.topic_id}', ${Boolean(t.pinned)})" class="px-2 py-0.5 rounded-full bg-[#f4f8f0] hover:bg-[#ecf1e6] text-[#111111] border border-[#111111]/20" title="Pin/Unpin Topic">📌 ${t.pinned ? 'Unpin' : 'Pin'}</button>
                ${canModifyTopic ? `<button type="button" onclick="deleteCyberspaceTopic('${t.topic_id}')" class="px-2 py-0.5 rounded-full bg-[#ffffff] hover:bg-[#8a1c1c]/10 text-[#8a1c1c] border border-[#8a1c1c]/40" title="Delete Topic">🗑️</button>` : ''}
                <button type="button" onclick="toggleBoardTopicThread('${t.topic_id}')" class="px-2.5 py-1 rounded-full bg-[#111111] hover:bg-[#107a47] text-[#ecf1e6] font-bold transition">
                  💬 ${posts.length} Repl${posts.length === 1 ? 'y' : 'ies'} / Thread
                </button>
              </div>
            </div>

            ${graphPathsHtml}

            <div id="boardThread-${t.topic_id}" class="${isExpanded ? '' : 'hidden'} pt-2 space-y-2 border-t border-[#111111]/15">
              <div class="space-y-2">${postsHtml || '<div class="text-[#5c5c5c] font-mono text-[11px]">No replies yet. Tag an @username or @gemini-brain below!</div>'}</div>
              <div id="replyParentBanner-${t.topic_id}" class="hidden px-2.5 py-1 rounded-lg bg-[#f4f8f0] border border-[#107a47] text-[#111111] font-mono text-[10px] flex items-center justify-between"></div>
              <div class="flex flex-wrap gap-1 pt-1 font-mono text-[10px]">
                <button type="button" onclick="insertBoardSelfTag('replyInput-${t.topic_id}')" class="px-2 py-0.5 rounded-full bg-[#f4f8f0] hover:bg-[#ecf1e6] text-[#107a47] border border-[#107a47]/35 font-semibold">🙋 @Me</button>
                <button type="button" onclick="insertBoardTag('@gemini-brain', 'replyInput-${t.topic_id}')" class="px-2 py-0.5 rounded-full bg-[#f4f8f0] hover:bg-[#ecf1e6] text-[#111111] border border-[#111111]/20 font-semibold">🤖 @gemini-brain</button>
                <button type="button" onclick="insertBoardTag('@claude-brain', 'replyInput-${t.topic_id}')" class="px-2 py-0.5 rounded-full bg-[#f4f8f0] hover:bg-[#ecf1e6] text-[#111111] border border-[#111111]/20 font-semibold">🤖 @claude-brain</button>
                <button type="button" onclick="insertBoardTag('@openai-brain', 'replyInput-${t.topic_id}')" class="px-2 py-0.5 rounded-full bg-[#f4f8f0] hover:bg-[#ecf1e6] text-[#111111] border border-[#111111]/20 font-semibold">🤖 @openai-brain</button>
                <button type="button" onclick="insertBoardTag('@verifier-agent', 'replyInput-${t.topic_id}')" class="px-2 py-0.5 rounded-full bg-[#f4f8f0] hover:bg-[#ecf1e6] text-[#107a47] border border-[#107a47]/35 font-semibold">🛡️ @verifier-agent</button>
              </div>
              <div class="flex gap-2">
                <input id="replyInput-${t.topic_id}" type="text" placeholder="Reply with @username, @gemini-brain, @verifier-agent, or #tags..." onkeydown="if(event.key==='Enter') replyCyberspaceTopic('${t.topic_id}')" class="flex-1 px-3 py-1.5 rounded-full bg-[#ffffff] border border-[#111111] text-[#111111] placeholder-[#5c5c5c] font-mono text-xs focus:outline-none" />
                <button type="button" onclick="replyCyberspaceTopic('${t.topic_id}')" class="px-3.5 py-1.5 rounded-full bg-[#111111] hover:bg-[#107a47] text-[#ecf1e6] font-mono font-bold text-xs transition">
                  Reply
                </button>
              </div>
            </div>
          </div>
        `;
      }).join('');
    }

    function toggleBoardTopicThread(topicId) {
      activeBoardTopicId = (activeBoardTopicId === topicId) ? null : topicId;
      const el = document.getElementById(`boardThread-${topicId}`);
      if (el) el.classList.toggle('hidden');
    }

    async function createCyberspaceTopic(omniText = null) {
      if (!requireVerifiedIdentity('create a topic on the Cyberspace Knowledge Board')) {
        requestAgentVerificationForm();
        return;
      }
      const rawOmni = String(omniText !== null ? omniText : (document.getElementById('boardSearchInput')?.value || '')).trim();
      const cleaned = rawOmni.replace(/^\/(post|new|thread)\b\s*/i, '').trim();
      const parts = cleaned.split(/\s*::\s*/);
      let title = (parts[0] || '').trim();
      let body = parts.length > 1 ? parts.slice(1).join(' :: ').trim() : title;
      const chipTags = boardChips.filter(c => c.startsWith('#')).map(c => c.slice(1));
      const inlineTags = [...cleaned.matchAll(/#([a-zA-Z0-9_\-]+)/g)].map(m => m[1].toLowerCase());
      const allTags = [...new Set([...chipTags, ...inlineTags])];
      const category = allTags.find(t => ['cyberspace', 'ai', 'architecture', 'security', 'qa'].includes(t)) || 'cyberspace';
      const tags = allTags.join(', ');
      if (!title || !body) {
        alert('Type /post <Title> #tag @agent (optionally :: details) in the Cyberspace input.');
        return;
      }
      const username = (localStorage.getItem('tincan_username') || '').trim();
      try {
        const res = await fetch('/api/board/topics', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            username,
            title,
            category,
            tags,
            body,
            auto_agent_reply: true
          })
        });
        const data = await res.json();
        if (res.status === 403 && data.require_verification) {
          requestAgentVerificationForm();
          return;
        }
        if (res.ok && data.topic) {
          const searchInp = document.getElementById('boardSearchInput');
          if (searchInp) searchInp.value = '';
          activeBoardTopicId = data.topic.topic_id;
          playXpChime();
          spawnPacketFlight(myPeerId, 'relay', 'cyberspace_topic', `#${category}`);
          await loadCyberspaceBoard();
        } else {
          alert('Could not create topic: ' + (data.error || 'Unknown error'));
        }
      } catch (err) {
        alert('Failed to post topic: ' + err.message);
      }
    }

    async function replyCyberspaceTopic(topicId) {
      if (!requireVerifiedIdentity('reply on the Cyberspace Knowledge Board')) {
        requestAgentVerificationForm();
        return;
      }
      const inp = document.getElementById(`replyInput-${topicId}`);
      const body = inp ? inp.value.trim() : '';
      if (!body) return;
      const username = (localStorage.getItem('tincan_username') || '').trim();
      const parentPostId = activeReplyParentPostByTopic[topicId] || '';
      try {
        const res = await fetch('/api/board/reply', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            topic_id: topicId,
            peer_id: myPeerId,
            username,
            body,
            parent_post_id: parentPostId,
            auto_agent_reply: true
          })
        });
        const data = await res.json();
        if (res.status === 403 && data.require_verification) {
          requestAgentVerificationForm();
          return;
        }
        if (res.ok) {
          if (inp) inp.value = '';
          clearReplyToNestedPost(topicId);
          activeBoardTopicId = topicId;
          playXpChime();
          spawnPacketFlight(myPeerId, 'relay', 'cyberspace_reply', '💬 Board Reply');
          await loadCyberspaceBoard();
        } else {
          alert('Reply error: ' + (data.error || 'Unknown error'));
        }
      } catch (err) {
        alert('Reply failed: ' + err.message);
      }
    }

    // =========================================================================
    // Tab 3: Interactive HTML5 Canvas Knowledge Graph & Shortest-Path Finder
    // =========================================================================
    async function loadAndDrawBoardGraph() {
      try {
        const res = await fetch('/api/board/graph');
        if (!res.ok) return;
        boardGraphSnapshot = await res.json();
        layoutBoardGraphNodes();
        drawBoardGraphCanvas();
      } catch (e) {}
    }

    function layoutBoardGraphNodes() {
      const canvas = document.getElementById('boardGraphCanvas');
      const w = canvas ? canvas.width : 860;
      const h = canvas ? canvas.height : 380;
      const nodes = (boardGraphSnapshot.nodes || []).slice(0, 48);
      const edges = boardGraphSnapshot.edges || [];

      boardGraphLayoutNodes = nodes.map((n, i) => {
        const angle = (2 * Math.PI * i) / Math.max(1, nodes.length);
        const radius = n.type === 'topic' ? 85 : (n.type === 'agent' ? 135 : 155);
        return {
          ...n,
          x: w / 2 + Math.cos(angle) * radius * (1.2 + (i % 3) * 0.18),
          y: h / 2 + Math.sin(angle) * (radius * 0.82),
          vx: 0,
          vy: 0
        };
      });

      const idMap = {};
      boardGraphLayoutNodes.forEach(n => { idMap[n.id] = n; });

      // Run 45 iterations of force-directed relaxation
      for (let iter = 0; iter < 45; iter++) {
        for (let i = 0; i < boardGraphLayoutNodes.length; i++) {
          for (let j = i + 1; j < boardGraphLayoutNodes.length; j++) {
            const a = boardGraphLayoutNodes[i];
            const b = boardGraphLayoutNodes[j];
            let dx = b.x - a.x;
            let dy = b.y - a.y;
            let distSq = dx * dx + dy * dy + 1;
            let force = 1600 / distSq;
            let dist = Math.sqrt(distSq);
            a.vx -= (dx / dist) * force;
            a.vy -= (dy / dist) * force;
            b.vx += (dx / dist) * force;
            b.vy += (dy / dist) * force;
          }
        }
        edges.forEach(e => {
          const s = idMap[e.source];
          const t = idMap[e.target];
          if (!s || !t) return;
          const dx = t.x - s.x;
          const dy = t.y - s.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const spring = (dist - 95) * 0.025;
          s.vx += (dx / dist) * spring;
          s.vy += (dy / dist) * spring;
          t.vx -= (dx / dist) * spring;
          t.vy -= (dy / dist) * spring;
        });
        boardGraphLayoutNodes.forEach(n => {
          n.vx += (w / 2 - n.x) * 0.015;
          n.vy += (h / 2 - n.y) * 0.015;
          n.x = Math.max(48, Math.min(w - 48, n.x + n.vx * 0.25));
          n.y = Math.max(28, Math.min(h - 38, n.y + n.vy * 0.25));
          n.vx *= 0.6;
          n.vy *= 0.6;
        });
      }
    }

    function drawBoardGraphCanvas() {
      const canvas = document.getElementById('boardGraphCanvas');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);

      const idMap = {};
      boardGraphLayoutNodes.forEach(n => { idMap[n.id] = n; });

      // Draw edges
      (boardGraphSnapshot.edges || []).forEach(e => {
        const s = idMap[e.source];
        const t = idMap[e.target];
        if (!s || !t) return;
        const isHighlighted = selectedGraphNodeId && (e.source === selectedGraphNodeId || e.target === selectedGraphNodeId);
        ctx.beginPath();
        ctx.moveTo(s.x, s.y);
        ctx.lineTo(t.x, t.y);
        ctx.strokeStyle = isHighlighted ? '#107a47' : 'rgba(17, 17, 17, 0.20)';
        ctx.lineWidth = isHighlighted ? 2.0 : 1.0;
        ctx.stroke();
      });

      // Draw nodes
      boardGraphLayoutNodes.forEach(n => {
        const color = n.type === 'topic' ? '#111111' :
                      n.type === 'user' ? '#107a47' :
                      n.type === 'agent' ? '#0f766e' :
                      n.type === 'tag' ? '#4a4a4a' : '#2f5e46';
        const r = n.id === selectedGraphNodeId ? 10 : Math.min(9, 5 + Math.sqrt(n.degree || 1));
        ctx.beginPath();
        ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.lineWidth = n.id === selectedGraphNodeId ? 2.5 : 1.2;
        ctx.strokeStyle = n.id === selectedGraphNodeId ? '#107a47' : '#ffffff';
        ctx.stroke();

        ctx.font = '10px ui-monospace, SFMono-Regular, Menlo, monospace';
        ctx.fillStyle = '#111111';
        const lbl = (n.label || n.id).slice(0, 22);
        ctx.fillText(lbl, n.x + r + 4, n.y + 3);
      });
    }

    (function initBoardGraphCanvasInteraction() {
      setTimeout(() => {
        const canvas = document.getElementById('boardGraphCanvas');
        if (!canvas) return;
        canvas.addEventListener('click', (ev) => {
          const rect = canvas.getBoundingClientRect();
          const scaleX = canvas.width / rect.width;
          const scaleY = canvas.height / rect.height;
          const mx = (ev.clientX - rect.left) * scaleX;
          const my = (ev.clientY - rect.top) * scaleY;
          let clicked = null;
          for (const n of boardGraphLayoutNodes) {
            const dx = mx - n.x;
            const dy = my - n.y;
            if (dx * dx + dy * dy <= 144) {
              clicked = n;
              break;
            }
          }
          if (clicked) {
            selectedGraphNodeId = clicked.id;
            drawBoardGraphCanvas();
            const insp = document.getElementById('boardGraphNodeInspector');
            if (insp) {
              const neighbors = (boardGraphSnapshot.edges || [])
                .filter(e => e.source === clicked.id || e.target === clicked.id)
                .map(e => `${e.relation} → ${e.source === clicked.id ? e.target : e.source}`);
              insp.innerHTML = `
                <div><strong class="text-[#107a47]">${escapeHtml(clicked.type.toUpperCase())}: ${escapeHtml(clicked.label)}</strong> · Degree: ${clicked.degree || 0} · Connections: ${escapeHtml(neighbors.slice(0, 5).join(', '))}</div>
                <button type="button" onclick="quickSearchBoardEntity('${escapeHtml(clicked.label)}')" class="px-2.5 py-0.5 rounded-full bg-[#111111] text-[#ecf1e6] font-bold text-[10px]">🔍 Search Node in Board</button>
              `;
            }
          }
        });
      }, 400);
    })();

    async function findCyberspaceEntityPath() {
      const src = (document.getElementById('graphPathSource')?.value || '').trim();
      const dst = (document.getElementById('graphPathTarget')?.value || '').trim();
      const out = document.getElementById('graphPathOutput');
      if (!src || !dst || !out) return;
      try {
        const res = await fetch(`/api/board/graph/path?from=${encodeURIComponent(src)}&to=${encodeURIComponent(dst)}`);
        const data = await res.json();
        out.classList.remove('hidden');
        if (data.found) {
          out.innerHTML = `✅ <strong>Shortest Path (${data.hops} hop${data.hops === 1 ? '' : 's'}):</strong> <code>${escapeHtml(data.formatted_path)}</code>`;
        } else {
          out.innerHTML = `⚠️ ${escapeHtml(data.message || 'No path found between those entities.')}`;
        }
      } catch (e) {}
    }

    // Init Playlist, Sponsors, Cyberspace Board & Analytics (Visibility-Aware Polling)
    loadPlaylist(false).then(() => renderAdminCrudTables());
    loadSponsorsData();
    loadCyberspaceBoard();
    loadAnalytics(true);
    if (isAdmin) {
      const bBtn = document.getElementById('billingAdminSponsorBtn');
      if (bBtn) bBtn.classList.remove('hidden');
    }
    setInterval(() => loadAnalytics(false), 15000);
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) {
        pollMeshState(true);
        pollSignals(true);
        loadAnalytics(true);
        loadSponsorsData();
      }
    });
  </script>

  <!-- Modal: Admin Edit Video -->
  <div id="adminEditVideoModal" class="hidden fixed inset-0 z-[120] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="bg-slate-900 border border-pink-700 rounded-xl max-w-md w-full p-4 space-y-3 font-mono text-xs shadow-2xl">
      <div class="flex items-center justify-between border-b border-slate-800 pb-2">
        <span class="font-bold text-pink-300 text-sm flex items-center gap-1.5"><span>✏️</span> Edit Relay Video</span>
        <button onclick="closeEditVideoModal()" class="text-slate-400 hover:text-white text-base">✕</button>
      </div>
      <input type="hidden" id="editVideoId">
      <div class="space-y-2">
        <div>
          <label class="text-[10px] text-slate-400 block mb-0.5">Title</label>
          <input type="text" id="editVideoTitle" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
        </div>
        <div>
          <label class="text-[10px] text-slate-400 block mb-0.5">Creator Handle</label>
          <input type="text" id="editVideoCreator" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
        </div>
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="text-[10px] text-slate-400 block mb-0.5">Category</label>
            <select id="editVideoCategory" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
              <option value="spotlight">spotlight</option>
              <option value="instruction">instruction</option>
              <option value="ad">ad (sponsored)</option>
            </select>
          </div>
          <div>
            <label class="text-[10px] text-slate-400 block mb-0.5">Duration (Seconds)</label>
            <input type="number" id="editVideoDuration" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
          </div>
        </div>
        <div>
          <label class="text-[10px] text-slate-400 block mb-0.5">Embed Stream URL</label>
          <input type="text" id="editVideoEmbedUrl" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
        </div>
      </div>
      <div class="flex justify-end gap-2 pt-2 border-t border-slate-800">
        <button onclick="closeEditVideoModal()" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded">Cancel</button>
        <button onclick="adminSubmitSaveVideoEdit()" class="px-4 py-1.5 bg-pink-600 hover:bg-pink-500 text-white font-bold rounded">Save Changes</button>
      </div>
    </div>
  </div>

  <!-- Modal: Admin Edit Sponsor -->
  <div id="adminEditSponsorModal" class="hidden fixed inset-0 z-[120] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="bg-slate-900 border border-amber-700 rounded-xl max-w-md w-full p-4 space-y-3 font-mono text-xs shadow-2xl">
      <div class="flex items-center justify-between border-b border-slate-800 pb-2">
        <span class="font-bold text-amber-300 text-sm flex items-center gap-1.5"><span>✏️</span> Edit Sponsor Creative</span>
        <button onclick="closeEditSponsorModal()" class="text-slate-400 hover:text-white text-base">✕</button>
      </div>
      <input type="hidden" id="editSponsorId">
      <div class="space-y-2">
        <div class="grid grid-cols-3 gap-2">
          <div class="col-span-2">
            <label class="text-[10px] text-slate-400 block mb-0.5">Sponsor Name</label>
            <input type="text" id="editSponsorName" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
          </div>
          <div>
            <label class="text-[10px] text-slate-400 block mb-0.5">Icon Emoji</label>
            <input type="text" id="editSponsorIcon" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
          </div>
        </div>
        <div>
          <label class="text-[10px] text-slate-400 block mb-0.5">Tagline</label>
          <input type="text" id="editSponsorTagline" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
        </div>
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="text-[10px] text-slate-400 block mb-0.5">CTA Text</label>
            <input type="text" id="editSponsorCta" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
          </div>
          <div>
            <label class="text-[10px] text-slate-400 block mb-0.5">Badge</label>
            <input type="text" id="editSponsorBadge" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
          </div>
        </div>
        <div>
          <label class="text-[10px] text-slate-400 block mb-0.5">Destination URL</label>
          <input type="text" id="editSponsorUrl" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
        </div>
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="text-[10px] text-slate-400 block mb-0.5">Reward Tokens</label>
            <input type="number" id="editSponsorRewardTokens" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
          </div>
          <div>
            <label class="text-[10px] text-slate-400 block mb-0.5">Reward USD</label>
            <input type="number" step="0.01" id="editSponsorRewardUsd" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
          </div>
        </div>
      </div>
      <div class="flex justify-end gap-2 pt-2 border-t border-slate-800">
        <button onclick="closeEditSponsorModal()" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded">Cancel</button>
        <button onclick="adminSubmitSaveSponsorEdit()" class="px-4 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded">Save Sponsor</button>
      </div>
    </div>
  </div>

  <!-- AgentSpace / Ranger VFS scripts (this code used to sit outside any script tag, so it never ran) -->
  <script>
    // -------------------------------------------------------------------------
    // AgentSpace & Wasm Studio (Single-File SQLite VFS + Rodin 3D + 15 ArtCraft Apps)
    // -------------------------------------------------------------------------
    let currentSpaceScope = 'user';
    let currentSpaceOwner = '';
    let currentSpaceFile = '/src/main.py';
    window.currentSpaceScope = currentSpaceScope;
    window.currentSpaceOwner = currentSpaceOwner;
    window.currentSpaceFile = currentSpaceFile;

    function switchSpaceScope(scope) {
      currentSpaceScope = scope;
      window.currentSpaceScope = scope;
      ['user', 'topic', 'dynamic'].forEach(k => {
        const btn = document.getElementById('scope' + k.charAt(0).toUpperCase() + k.slice(1) + 'Btn');
        if (btn) btn.classList.toggle('is-active', k === scope);
      });
      const ownerInput = document.getElementById('spaceOwnerInput');
      if (scope === 'user') {
        if (ownerInput) { ownerInput.value = myPeerId || ''; ownerInput.placeholder = 'User Peer ID'; }
      } else if (ownerInput) {
        ownerInput.placeholder = scope === 'topic' ? 'Topic ID or Content IR Search (Enter)' : 'Sandbox ID';
        if (scope === 'topic' && !ownerInput.value.startsWith('topic-')) ownerInput.value = '';
      }
      hideSpaceTopicSearchResults();
      refreshAgentSpace();
    }

    let _spaceTopicSearchTimer = null;
    function hideSpaceTopicSearchResults() {
      const box = document.getElementById('spaceTopicSearchResults');
      if (box) box.classList.add('hidden');
    }

    function onSpaceOwnerInput(ev) {
      const val = (ev && ev.target ? ev.target.value : '').trim();
      clearTimeout(_spaceTopicSearchTimer);
      if (!val || currentSpaceScope === 'user') {
        hideSpaceTopicSearchResults();
        return;
      }
      _spaceTopicSearchTimer = setTimeout(() => searchSpaceTopicsIR(val, false), 220);
    }

    function onSpaceOwnerKeydown(ev) {
      if (ev.key === 'Escape') { hideSpaceTopicSearchResults(); return; }
      if (ev.key === 'Enter') {
        ev.preventDefault();
        resolveAndLoadSpaceOwner();
      }
    }

    function selectWorkstationTopicResult(topicId) {
      currentSpaceScope = 'topic';
      window.currentSpaceScope = 'topic';
      ['user', 'topic', 'dynamic'].forEach(k => {
        const btn = document.getElementById('scope' + k.charAt(0).toUpperCase() + k.slice(1) + 'Btn');
        if (btn) btn.classList.toggle('is-active', k === 'topic');
      });
      const ownerInput = document.getElementById('spaceOwnerInput');
      if (ownerInput) ownerInput.value = topicId;
      hideSpaceTopicSearchResults();
      refreshAgentSpace();
    }

    async function searchSpaceTopicsIR(query, autoLoadFirst = false) {
      const box = document.getElementById('spaceTopicSearchResults');
      const q = String(query || '').trim();
      if (!q) { hideSpaceTopicSearchResults(); return null; }
      try {
        const [irRes, listRes] = await Promise.all([
          fetch(`/api/board/query?q=${encodeURIComponent(q)}&top_k=6`),
          fetch('/api/board/topics?limit=30&sort_by=hot')
        ]);
        const hits = [];
        const seen = new Set();
        if (irRes.ok) {
          const irData = await irRes.json();
          (irData.results || []).forEach(r => {
            if (r.topic_id && !seen.has(r.topic_id)) { seen.add(r.topic_id); hits.push(r); }
          });
        }
        if (listRes.ok) {
          const lData = await listRes.json();
          const low = q.toLowerCase();
          (lData.topics || []).forEach(t => {
            if (!t.topic_id || seen.has(t.topic_id)) return;
            if (t.topic_id.toLowerCase().includes(low) || (t.title || '').toLowerCase().includes(low) || (t.body || '').toLowerCase().includes(low)) {
              seen.add(t.topic_id);
              hits.push(t);
            }
          });
        }
        if (autoLoadFirst && hits.length > 0) {
          selectWorkstationTopicResult(hits[0].topic_id);
          return hits[0].topic_id;
        }
        if (box) {
          if (!hits.length) {
            box.innerHTML = '<div class="p-2 text-neutral-500">No matching Topic ID or content found. Press Enter to load exact Owner/Sandbox ID.</div>';
          } else {
            box.innerHTML = hits.slice(0, 8).map(t =>
              `<button type="button" onmousedown="event.preventDefault(); selectWorkstationTopicResult('${rangerEsc(t.topic_id)}')" class="w-full text-left px-2 py-1.5 hover:bg-[#ecf1e6] rounded border-b border-black/10 last:border-0">
                 <div class="font-bold text-black truncate">${rangerEsc(t.title || t.topic_id)}</div>
                 <div class="text-[10px] text-neutral-600 truncate">${rangerEsc(t.topic_id)} · ${(t.tags || []).slice(0, 3).map(tg => '#' + tg).join(' ')}</div>
               </button>`
            ).join('');
          }
          box.classList.remove('hidden');
        }
        return hits.length ? hits[0].topic_id : null;
      } catch (e) {
        return null;
      }
    }

    async function resolveAndLoadSpaceOwner() {
      const ownerInput = document.getElementById('spaceOwnerInput');
      const raw = (ownerInput ? ownerInput.value : '').trim();
      hideSpaceTopicSearchResults();
      if (!raw) { refreshAgentSpace(); return; }
      const looksLikeContentSearch = (currentSpaceScope === 'topic' && !/^topic-[a-z0-9_-]+$/i.test(raw)) || raw.includes(' ');
      if (looksLikeContentSearch || /^topic-/i.test(raw)) {
        if (/^topic-[a-z0-9_-]+$/i.test(raw)) {
          selectWorkstationTopicResult(raw);
          return;
        }
        const matchedId = await searchSpaceTopicsIR(raw, true);
        if (matchedId) return;
      }
      refreshAgentSpace();
    }

    async function refreshAgentSpace(opts) {
      const background = opts === 'background';
      if (!background) rangerMode = 'space';
      const ownerInput = document.getElementById('spaceOwnerInput');
      currentSpaceOwner = (ownerInput && ownerInput.value.trim()) || (myPeerId || 'default');
      window.currentSpaceScope = currentSpaceScope;
      window.currentSpaceOwner = currentSpaceOwner;
      if (typeof notifyParentInstanceTitle === 'function' && (singleWindowParam === 'win-agentspace' || singleWindowParam === 'win-workstation')) {
        notifyParentInstanceTitle(`${currentSpaceScope}: ${currentSpaceOwner}${currentSpaceFile ? (' · ' + currentSpaceFile.split('/').pop()) : ''}`);
      }
      ideSpaceChanged();
      if (!background && window.TinCanWorkstation && typeof window.TinCanWorkstation.refresh === 'function') {
        try { window.TinCanWorkstation.refresh({ immediate: false }); } catch (e) {}
      }
      const fileListEl = document.getElementById('spaceFileList');
      const badgeEl = document.getElementById('spaceFileCountBadge');
      if (!fileListEl) return;
      if (rangerMode === 'space') {
        setRangerListHeader();
        fileListEl.innerHTML = '<div class="text-slate-500 py-2 text-center text-xs">Fetching .space VFS...</div>';
      }

      try {
        const resp = await fetch(`/api/space/ls?scope=${currentSpaceScope}&owner_id=${encodeURIComponent(currentSpaceOwner)}`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        const files = data.files || [];
        if (badgeEl) badgeEl.textContent = `${files.length} File${files.length === 1 ? '' : 's'}`;
        ideMerkle = String(data.merkle_root || '').slice(0, 10);
        ideUpdateStatus();
        if (rangerMode !== 'space') return; // the drive mirror is showing; keep it

        if (files.length === 0) {
          rangerItems = [];
          fileListEl.innerHTML = '<div class="text-slate-500 py-2 text-center text-xs">No files in space yet. Click + New File or Generate 3D.</div>';
          return;
        }
        renderRangerList(files.map(f => ({ kind: 'file', source: 'space', path: f.path, name: f.path, size: f.size_bytes, mime: f.mime_type })));

        if (!document.getElementById('agentspaceEditor').value && !ideClosedAll && files.length > 0) {
          openAgentSpaceFile(files[0].path);
        }
      } catch (err) {
        if (rangerMode === 'space') fileListEl.innerHTML = `<div class="text-red-400 py-2 text-center text-xs">Error loading space: ${rangerEsc(err.message)}</div>`;
      }
    }

    async function openAgentSpaceFile(path) {
      currentSpaceFile = path;
      window.currentSpaceFile = currentSpaceFile;
      if (typeof notifyParentInstanceTitle === 'function' && singleWindowParam === 'win-agentspace') {
        notifyParentInstanceTitle(`${currentSpaceScope}: ${currentSpaceOwner} · ${String(path || '').split('/').pop()}`);
      }
      const pathEl = document.getElementById('activeFilePath');
      const editor = document.getElementById('agentspaceEditor');
      if (pathEl) pathEl.textContent = path;
      if (editor) editor.value = 'Loading...';
      markRangerSelected(path);

      try {
        const resp = await fetch(`/api/space/file?scope=${currentSpaceScope}&owner_id=${encodeURIComponent(currentSpaceOwner)}&path=${encodeURIComponent(path)}`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const rec = await resp.json();
        const isText = rec.content !== null && rec.content !== undefined;
        if (editor) {
          editor.value = isText ? rec.content : `[Binary Asset: ${rec.size_bytes} bytes | SHA256: ${rec.sha256}]\n(Base64 payload available in .space)`;
        }
        const fpath = rec.path || path;
        const kind = rangerKind(fpath, rec.mime_type);
        let mediaUrl = null;
        if (['image', 'video', 'audio', 'model', 'pdf', 'html', 'font'].includes(kind)) {
          if (rec.content_b64 && (rec.size_bytes || 0) <= 48 * 1024 * 1024) {
            mediaUrl = rangerObjectUrl(b64ToBlob(rec.content_b64, rec.mime_type || 'application/octet-stream'));
          } else if (isText) {
            const extMime = kind === 'html' ? 'text/html' : (rangerExt(fpath) === 'svg' ? 'image/svg+xml' : (rec.mime_type || 'text/plain'));
            mediaUrl = rangerObjectUrl(new Blob([rec.content], { type: extMime }));
          }
        }
        const pagesUrl = `/pages/${encodeURIComponent(currentSpaceScope || 'user')}/${encodeURIComponent(currentSpaceOwner || 'default')}${fpath.startsWith('/') ? fpath : '/' + fpath}`;
        showFileInViewer({
          source: 'space', path: fpath, name: fpath.split('/').pop(),
          size: rec.size_bytes, mtime: rec.updated_at, mime: rec.mime_type || 'text/plain',
          text: isText ? rec.content : null, binary: !isText, mediaUrl, pagesUrl,
          b64: rec.content_b64 || null,
        });
      } catch (err) {
        if (editor) editor.value = `Error loading file: ${err.message}`;
        showViewerError(path, err.message);
      }
    }

    async function saveAgentSpaceFile() {
      const editor = document.getElementById('agentspaceEditor');
      if (!editor) return;
      const content = editor.value;
      try {
        const resp = await fetch('/api/space/file', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            scope: currentSpaceScope,
            owner_id: currentSpaceOwner,
            path: currentSpaceFile,
            content: content,
            action: 'write',
            updated_by: myPeerId || 'user'
          })
        });
        if (resp.ok) {
          if (typeof playXpChime === 'function') playXpChime();
          ideMarkSaved();
          refreshAgentSpace();
          const outEl = document.getElementById('agentspaceOutput');
          if (outEl) outEl.textContent = `[+] File ${currentSpaceFile} saved to ${currentSpaceScope}:${currentSpaceOwner}.space!`;
        } else {
          alert('Save failed: ' + resp.statusText);
        }
      } catch (err) {
        alert('Save error: ' + err.message);
      }
    }

    async function deleteAgentSpaceFile() {
      if (!confirm(`Delete ${currentSpaceFile} from space?`)) return;
      try {
        const resp = await fetch('/api/space/file', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            scope: currentSpaceScope,
            owner_id: currentSpaceOwner,
            path: currentSpaceFile,
            action: 'delete'
          })
        });
        if (resp.ok) {
          ideForgetTab('space:' + currentSpaceFile);
          currentSpaceFile = '/src/main.py';
          window.currentSpaceFile = currentSpaceFile;
          refreshAgentSpace();
        }
      } catch (err) {
        alert('Delete error: ' + err.message);
      }
    }

    function promptCreateFile() {
      const name = prompt('Enter new file path inside space (e.g. /src/solution.py, /artcraft/notes.md):', '/src/script.py');
      if (!name) return;
      currentSpaceFile = name;
      window.currentSpaceFile = currentSpaceFile;
      const editor = document.getElementById('agentspaceEditor');
      if (editor) editor.value = '# New file in AgentSpace VFS\n';
      rangerMode = 'space';
      setViewerEditMode();
      saveAgentSpaceFile();
    }

    async function runAgentSpacePlayground() {
      const outEl = document.getElementById('agentspaceOutput');
      const exitEl = document.getElementById('playgroundExitCode');
      const rtSelect = document.getElementById('playgroundRuntimeSelect');
      const editor = document.getElementById('agentspaceEditor');
      const runtime = (rtSelect && rtSelect.value) || 'auto';
      if (outEl) outEl.textContent = '🚀 Running code / Wasm bridge...';

      try {
        const resp = await fetch('/api/space/exec', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            scope: currentSpaceScope,
            owner_id: currentSpaceOwner,
            entrypoint: currentSpaceFile,
            runtime: runtime,
            code_override: editor ? editor.value : null
          })
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        if (exitEl) exitEl.textContent = `Exit: ${data.exit_code}`;
        let txt = '';
        if (data.stdout) txt += data.stdout;
        if (data.stderr) txt += (txt ? '\n' : '') + data.stderr;
        if (!txt) txt = `[Execution finished with exit code ${data.exit_code}]`;
        if (outEl) {
          outEl.textContent = txt;
          outEl.className = data.exit_code === 0 ? 'whitespace-pre-wrap select-text text-emerald-400' : 'whitespace-pre-wrap select-text text-red-400';
        }
      } catch (err) {
        if (outEl) {
          outEl.textContent = `Execution error: ${err.message}`;
          outEl.className = 'whitespace-pre-wrap select-text text-red-400';
        }
      }
    }

    async function runAgentSpaceAgent() {
      const promptText = prompt('Ask Space Agent (generates solutions inside this VFS):', 'Refactor and test this code');
      if (!promptText) return;
      const outEl = document.getElementById('agentspaceOutput');
      if (outEl) outEl.textContent = `🤖 Space Agent analyzing ${currentSpaceFile}...`;

      try {
        const resp = await fetch('/api/space/agent', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            scope: currentSpaceScope,
            owner_id: currentSpaceOwner,
            prompt: promptText,
            model_alias: 'gemini-brain',
            author: myPeerId || 'user'
          })
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        if (outEl) {
          outEl.textContent = `[🤖 ${data.model}]\n${data.reply}`;
          outEl.className = 'whitespace-pre-wrap select-text text-cyan-300';
        }
      } catch (err) {
        if (outEl) outEl.textContent = `Space agent error: ${err.message}`;
      }
    }

    async function generateAgentSpaceRodin3D() {
      const pInput = document.getElementById('rodinPromptInput');
      const tSelect = document.getElementById('rodinTierSelect');
      const fSelect = document.getElementById('rodinFormatSelect');
      const notice = document.getElementById('rodinStatusNotice');
      const btn = document.getElementById('generateRodinBtn');
      const promptVal = (pInput && pInput.value.trim()) || 'futuristic rover 3d mesh';
      const tierVal = (tSelect && tSelect.value) || 'Regular';
      const formatVal = (fSelect && fSelect.value) || 'glb';

      if (btn) btn.disabled = true;
      if (notice) notice.textContent = 'Dispatched to Hyper3D Rodin...';

      try {
        const savePath = `/models3d/${promptVal.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase().slice(0, 20)}.${formatVal}`;
        const resp = await fetch('/api/3d/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: promptVal,
            tier: tierVal,
            format: formatVal,
            scope: currentSpaceScope,
            owner_id: currentSpaceOwner,
            save_path: savePath,
            peer_id: myPeerId || 'user'
          })
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        let data = await resp.json();
        let activeUuid = data.uuid || '';
        let subKey = data.subscription_key || activeUuid;
        let activeModel = data.model || 'hyper3d/rodin-v2.5';
        let finalPath = (data.saved_to_space && data.saved_to_space.path) || data.pending_save_path || savePath;
        let ready = Boolean(data.glb_bytes_b64) && (Boolean(data.simulated) || Boolean(data.downloaded) || String(data.status || '') === 'Done');
        if (!ready) {
          if (String(data.status || '') === 'Failed') {
            throw new Error(data.remote_error || data.error || '3D generation failed');
          }
          const sleepMs = (ms) => new Promise((r) => setTimeout(r, ms));
          for (let attempt = 1; attempt <= 45; attempt++) {
            if (notice) notice.textContent = `Rendering 3D (${activeModel})… poll ${attempt}/45`;
            await sleepMs(3000);
            const stResp = await fetch('/api/3d/status', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ subscription_key: subKey, key: subKey })
            });
            const st = await stResp.json();
            if (st.subscription_key) subKey = st.subscription_key;
            if (st.uuid) activeUuid = st.uuid;
            if (st.model) activeModel = st.model;
            const stVal = String(st.status || (st.jobs && st.jobs[0] && st.jobs[0].status) || 'Processing');
            if (stVal === 'Failed') throw new Error(st.error || 'Upstream 3D generation failed');
            if (stVal === 'Done') {
              const dlResp = await fetch('/api/3d/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  task_uuid: activeUuid,
                  uuid: activeUuid,
                  prompt: promptVal,
                  scope: currentSpaceScope,
                  owner_id: currentSpaceOwner,
                  save_path: finalPath,
                  peer_id: myPeerId || 'user'
                })
              });
              const dl = await dlResp.json();
              if (dl.download_error && !dl.glb_bytes_b64) throw new Error(dl.download_error);
              if (dl.glb_bytes_b64) {
                if (dl.saved_to_space && dl.saved_to_space.path) finalPath = dl.saved_to_space.path;
                data = Object.assign({}, data, dl, { uuid: activeUuid, status: 'Done' });
                ready = true;
                break;
              }
            }
          }
          if (!ready) throw new Error('Timed out waiting for real 3D GLB mesh');
        }
        if (notice) notice.textContent = `✅ Generated 3D: ${activeUuid} (Saved: ${finalPath})`;
        refreshAgentSpace();
        refreshBillingWindow();
      } catch (err) {
        if (notice) notice.textContent = `Generation error: ${err.message}`;
      } finally {
        if (btn) btn.disabled = false;
      }
    }

    function launchArtCraftWasmApp() {
      const appSelect = document.getElementById('artcraftAppSelect');
      const wrapper = document.getElementById('artcraftIframeWrapper');
      const frame = document.getElementById('artcraftWasmFrame');
      const statusPill = document.getElementById('artcraftStatusPill');
      const appId = (appSelect && appSelect.value) || 'cadcraft';
      if (!wrapper || !frame) return;

      wrapper.classList.remove('hidden');
      if (statusPill) {
        statusPill.textContent = 'CONNECTING (?host=parent)';
        statusPill.className = 'px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 text-[10px] font-mono border border-purple-500/40 font-semibold';
      }

      const appUrl = `https://getartcraft.com/apps/${appId}?host=parent`;
      frame.src = appUrl;
    }

    async function openArtCraftOnPC() {
      const appSelect = document.getElementById('artcraftAppSelect');
      const statusPill = document.getElementById('artcraftStatusPill');
      const appId = (appSelect && appSelect.value) || 'cadcraft';
      try {
        const resp = await fetch('/api/artcraft/open', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            app_id: appId,
            scope: currentSpaceScope,
            owner_id: currentSpaceOwner || (myPeerId || 'default'),
            path: currentSpaceFile,
            launch_process: true
          })
        });
        const data = await resp.json();
        if (data.mode === 'native-pc-app' || data.mode === 'artcraft-launcher-pc') {
          if (statusPill) {
            statusPill.textContent = `OPENED ON PC (${data.app.pc_version || 'NATIVE'})`;
            statusPill.className = 'px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] font-mono border border-emerald-500/40 font-semibold';
          }
        } else {
          window.open(data.getartcraft_url || 'https://getartcraft.com', '_blank', 'noopener');
        }
      } catch (err) {
        window.open('https://getartcraft.com', '_blank', 'noopener');
      }
    }

    async function exportAgentSpace() {
      try {
        const resp = await fetch(`/api/space/export?scope=${currentSpaceScope}&owner_id=${encodeURIComponent(currentSpaceOwner)}`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        const blob = new Blob([Uint8Array.from(atob(data.space_b64), c => c.charCodeAt(0))], { type: 'application/octet-stream' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = data.filename || `${currentSpaceOwner}.space`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } catch (err) {
        alert('Export error: ' + err.message);
      }
    }

    // ArtCraft Wasm (?host=parent) PostMessage Bridge
    window.addEventListener("message", async function(event) {
      const data = event.data;
      if (!data || typeof data !== 'object') return;
      const eventType = data.type || data.event || '';

      if (eventType.endsWith(':ready')) {
        const appPrefix = eventType.split(':')[0];
        console.log(`[ArtCraft Wasm Bridge] App ${appPrefix} is READY. Sending ${appPrefix}:open...`);
        const statusEl = document.getElementById('artcraftStatusPill');
        if (statusEl) {
          statusEl.textContent = 'READY';
          statusEl.className = 'px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] font-mono border border-emerald-500/40 font-semibold';
        }
        const editor = document.getElementById('agentspaceEditor');
        const content = editor ? editor.value : '';
        const frame = document.getElementById('artcraftWasmFrame');
        if (frame && frame.contentWindow) {
          frame.contentWindow.postMessage({
            type: `${appPrefix}:open`,
            name: currentSpaceFile.split('/').pop(),
            path: currentSpaceFile,
            content: content,
            format: currentSpaceFile.split('.').pop()
          }, '*');
        }
      } else if (eventType.endsWith(':dirty')) {
        const statusEl = document.getElementById('artcraftStatusPill');
        if (statusEl) {
          statusEl.textContent = data.dirty ? 'UNSAVED CHANGES' : 'CLEAN';
          statusEl.className = data.dirty ? 'px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 text-[10px] font-mono border border-amber-500/40 font-semibold' : 'px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 text-[10px] font-mono';
        }
      } else if (eventType.endsWith(':save')) {
        const appPrefix = eventType.split(':')[0];
        console.log(`[ArtCraft Wasm Bridge] Received ${appPrefix}:save event. Writing to .space VFS...`);
        const savePath = data.path || currentSpaceFile;
        const saveContent = data.content !== undefined ? data.content : (data.bytes || '');
        const isB64 = Boolean(data.is_base64 || data.bytes);
        try {
          const resp = await fetch('/api/space/file', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              scope: currentSpaceScope,
              owner_id: currentSpaceOwner || (myPeerId || 'default'),
              path: savePath,
              content: saveContent,
              action: 'write',
              is_base64: isB64,
              updated_by: myPeerId || 'user'
            })
          });
          if (resp.ok) {
            const statusEl = document.getElementById('artcraftStatusPill');
            if (statusEl) {
              statusEl.textContent = 'SAVED TO VFS';
              statusEl.className = 'px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] font-mono border border-emerald-500/40 font-semibold';
            }
            refreshAgentSpace();
          }
        } catch (e) {
          console.error('[ArtCraft Wasm Bridge] Failed to save file:', e);
        }
      }
    });

    // =========================================================================
    // Quick Start CLI & Spectator Mode
    // =========================================================================
    function openTerminalQuickStart() {
      const modal = document.getElementById('terminalQuickStartModal');
      if (modal) modal.classList.remove('hidden');
    }
    function closeTerminalQuickStart() {
      const modal = document.getElementById('terminalQuickStartModal');
      if (modal) modal.classList.add('hidden');
      localStorage.setItem('tincan_quickstart_seen', 'true');
    }
    async function copyToClipboard(text, btnEl) {
      try {
        await navigator.clipboard.writeText(text);
        if (btnEl) {
          const orig = btnEl.innerText;
          btnEl.innerText = '✓ Copied!';
          setTimeout(() => { btnEl.innerText = orig; }, 1600);
        }
        if (typeof showQuickNotification === 'function') {
          showQuickNotification('✓ Copied to clipboard: ' + text);
        }
      } catch (e) {
        window.prompt('Copy command:', text);
      }
    }
    function continueAsSpectator() {
      const modal = document.getElementById('accountSetupModal');
      if (modal) modal.classList.add('hidden');
      localStorage.setItem('tincan_spectator_mode', 'true');
      showQuickNotification('👀 Spectator Mode: Watching TV & feeds is 100% free.');
    }

    // =========================================================================
    // Knowledge Graph Collapsible Toggle
    // =========================================================================
    function toggleKnowledgeGraphView() {
      const container = document.getElementById('boardGraphCanvasContainer');
      const toggleText = document.getElementById('kgToggleText');
      if (!container) return;
      const isHidden = container.classList.toggle('hidden');
      if (toggleText) {
        toggleText.innerText = isHidden ? '👁️ Show Canvas' : '👁️ Hide Canvas';
      }
    }

    // =========================================================================
    // Admin-Controlled $TINCAN Minting & User Request / Add Money Flows
    // =========================================================================
    function toggleMintRequestDrawer() {
      const drawer = document.getElementById('mintRequestDrawer');
      if (!drawer) return;
      const opening = drawer.classList.toggle('hidden') === false;
      if (opening) {
        fetchMintRequests(false);
      }
    }

    function openAddMoneyFromQuests() {
      if (typeof toggleWindow === 'function') {
        toggleWindow('win-billing');
      }
      if (typeof refreshBillingWindow === 'function') {
        refreshBillingWindow();
      }
    }

    async function submitMintRequest() {
      if (typeof requireVerifiedIdentity === 'function' && !requireVerifiedIdentity('submit a $TINCAN mint request')) return;
      const amtEl = document.getElementById('mintReqAmountInput');
      const reasonEl = document.getElementById('mintReqReasonInput');
      const banner = document.getElementById('mintRequestStatusBanner');
      const tokens = Math.max(1, parseInt((amtEl && amtEl.value) || '100', 10) || 100);
      const reason = (reasonEl && reasonEl.value.trim()) || 'User requested onboarding / compute grant';
      try {
        const res = await fetch('/api/tokens/mint-request', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            target_peer_id: myPeerId,
            tokens,
            reason
          })
        });
        const data = await res.json();
        if (!res.ok) {
          if (banner) {
            banner.textContent = data.error || 'Could not submit mint request.';
            banner.className = 'text-[11px] text-amber-400';
          }
          return;
        }
        if (reasonEl) reasonEl.value = '';
        if (banner) {
          banner.textContent = `✓ Request ${data.request.id} submitted (${data.request.tokens} $TINCAN) — awaiting admin approval.`;
          banner.className = 'text-[11px] text-emerald-400';
        }
        if (typeof showQuickNotification === 'function') {
          showQuickNotification(`🪙 Mint request (${tokens} $TINCAN) queued for admin approval.`);
        }
        fetchMintRequests(false);
      } catch (e) {
        if (banner) banner.textContent = 'Network error submitting mint request.';
      }
    }

    function _getAdminKeyInput() {
      const inp = document.getElementById('adminMintKeyInput');
      const val = inp ? inp.value.trim() : '';
      if (val) {
        try { sessionStorage.setItem('tincan_admin_key', val); } catch (e) {}
        return val;
      }
      try { return sessionStorage.getItem('tincan_admin_key') || ''; } catch (e) { return ''; }
    }

    async function fetchMintRequests(adminView = false) {
      const headers = {};
      if (adminView) {
        const key = _getAdminKeyInput();
        if (key) headers['X-Admin-Key'] = key;
      }
      const url = adminView
        ? '/api/tokens/mint-requests'
        : `/api/tokens/mint-requests?peer_id=${encodeURIComponent(myPeerId)}`;
      try {
        const res = await fetch(url, { headers });
        if (!res.ok) return;
        const data = await res.json();
        const items = Array.isArray(data.requests) ? data.requests : [];
        if (adminView) {
          const listEl = document.getElementById('adminMintRequestsList');
          const fbEl = document.getElementById('adminMintFeedback');
          if (!data.admin_authenticated && fbEl) {
            fbEl.textContent = 'Enter a valid TINCAN_ADMIN_KEY to approve/mint requests.';
            fbEl.className = 'text-[11px] text-amber-400';
          }
          if (listEl) {
            if (items.length === 0) {
              listEl.innerHTML = '<div class="text-slate-500 py-1">No mint requests in queue.</div>';
            } else {
              listEl.innerHTML = items.slice(0, 10).map(r => `
                <div class="p-2 bg-slate-950/90 border border-slate-800 rounded flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <span class="text-white font-bold">${escapeHtml(r.username || r.peer_id)}</span>
                    <span class="text-amber-300 font-bold ml-1">+${Number(r.tokens || 0).toLocaleString()} $TC</span>
                    <span class="text-slate-400 ml-1">(${escapeHtml(r.status)})</span>
                    <div class="text-[10px] text-slate-400">${escapeHtml(r.reason || '')} · target: ${escapeHtml(r.target_peer_id)}</div>
                  </div>
                  ${r.status === 'pending' ? `
                    <div class="flex items-center gap-1.5">
                      <button onclick="resolveMintRequest('${escapeHtml(r.id)}', 'approve')" class="px-2 py-0.5 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-[10px] font-bold">✓ Approve</button>
                      <button onclick="resolveMintRequest('${escapeHtml(r.id)}', 'reject')" class="px-2 py-0.5 rounded bg-red-900/80 hover:bg-red-800 text-red-200 text-[10px]">✕ Reject</button>
                    </div>
                  ` : `<span class="text-[10px] text-slate-500 font-mono">${escapeHtml(r.id)}</span>`}
                </div>
              `).join('');
            }
          }
        } else {
          const mineEl = document.getElementById('myMintRequestsList');
          if (mineEl && items.length > 0) {
            mineEl.innerHTML = items.slice(0, 4).map(r => `
              <div class="px-2 py-1 bg-slate-900/80 border border-slate-800 rounded flex items-center justify-between">
                <span>${escapeHtml(r.id)} · ${Number(r.tokens || 0).toLocaleString()} $TINCAN</span>
                <span class="${r.status === 'approved' ? 'text-emerald-400' : (r.status === 'rejected' ? 'text-red-400' : 'text-amber-300')} uppercase font-bold">${escapeHtml(r.status)}</span>
              </div>
            `).join('');
          }
        }
      } catch (e) {}
    }

    async function adminMintAndRouteTokens() {
      const targetEl = document.getElementById('adminMintTargetPeer');
      const tokEl = document.getElementById('adminMintTokensInput');
      const usdEl = document.getElementById('adminMintUsdInput');
      const fbEl = document.getElementById('adminMintFeedback');
      const peerId = (targetEl && targetEl.value.trim()) || myPeerId;
      const tokens = Math.max(1, parseInt((tokEl && tokEl.value) || '500', 10) || 0);
      const amountUsd = Math.max(0, parseFloat((usdEl && usdEl.value) || '0') || 0);
      const adminKey = _getAdminKeyInput();
      if (!adminKey) {
        if (fbEl) {
          fbEl.textContent = 'Admin Key required to mint & route credits.';
          fbEl.className = 'text-[11px] text-amber-400';
        }
        return;
      }
      try {
        const res = await fetch('/api/account/billing/topup', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-Admin-Key': adminKey },
          body: JSON.stringify({ peer_id: peerId, tokens, amount_usd: amountUsd })
        });
        const data = await res.json();
        if (!res.ok) {
          if (fbEl) {
            fbEl.textContent = data.error || 'Mint rejected (check X-Admin-Key or target peer).';
            fbEl.className = 'text-[11px] text-red-400';
          }
          return;
        }
        if (fbEl) {
          fbEl.textContent = `✓ Minted & routed ${tokens.toLocaleString()} $TINCAN to ${peerId}.`;
          fbEl.className = 'text-[11px] text-emerald-400';
        }
        if (typeof refreshBillingWindow === 'function') refreshBillingWindow();
        if (window.TinCanTokenVault && typeof window.TinCanTokenVault.refresh === 'function') {
          window.TinCanTokenVault.refresh();
        }
        if (typeof showQuickNotification === 'function') {
          showQuickNotification(`🛡️ Admin minted ${tokens.toLocaleString()} $TINCAN to ${peerId}`);
        }
      } catch (e) {
        if (fbEl) fbEl.textContent = 'Request failed.';
      }
    }

    async function resolveMintRequest(requestId, decision) {
      const fbEl = document.getElementById('adminMintFeedback');
      const adminKey = _getAdminKeyInput();
      if (!adminKey) {
        if (fbEl) {
          fbEl.textContent = 'Enter TINCAN_ADMIN_KEY before resolving requests.';
          fbEl.className = 'text-[11px] text-amber-400';
        }
        return;
      }
      try {
        const res = await fetch('/api/tokens/mint-requests/resolve', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-Admin-Key': adminKey },
          body: JSON.stringify({ request_id: requestId, decision })
        });
        const data = await res.json();
        if (!res.ok) {
          if (fbEl) {
            fbEl.textContent = data.error || 'Resolution failed.';
            fbEl.className = 'text-[11px] text-red-400';
          }
          return;
        }
        if (fbEl) {
          fbEl.textContent = `✓ Request ${requestId} ${data.status}.`;
          fbEl.className = 'text-[11px] text-emerald-400';
        }
        fetchMintRequests(true);
        if (typeof refreshBillingWindow === 'function') refreshBillingWindow();
        if (window.TinCanTokenVault && typeof window.TinCanTokenVault.refresh === 'function') {
          window.TinCanTokenVault.refresh();
        }
      } catch (e) {}
    }

    function mintTincanRewardTokens() {
      toggleMintRequestDrawer();
    }

    // =========================================================================
    // Moderator Ban Management & Reported Artifacts Inspector
    // =========================================================================
    async function fetchBannedPeers() {
      try {
        const res = await fetch('/api/moderator/banned');
        if (!res.ok) return;
        const data = await res.json();
        const tbody = document.getElementById('modBannedPeersTable');
        if (!tbody) return;
        const peers = data.banned_peers || [];
        if (peers.length === 0) {
          tbody.innerHTML = '<tr><td colspan="5" class="px-3 py-2 text-center text-slate-500 text-[11px]">No peers currently banned.</td></tr>';
          return;
        }
        tbody.innerHTML = peers.map(p => `
          <tr class="hover:bg-slate-900/60 font-mono text-xs">
            <td class="px-2.5 py-1.5 font-bold text-red-400">${escapeHtml(p.peer_id || '')}</td>
            <td class="px-2.5 py-1.5 text-slate-300">${escapeHtml(p.reason || 'Banned')}</td>
            <td class="px-2.5 py-1.5 text-slate-400">${escapeHtml(p.banned_by || 'admin')}</td>
            <td class="px-2.5 py-1.5 text-slate-500">${new Date((p.banned_at || 0) * 1000).toLocaleTimeString()}</td>
            <td class="px-2.5 py-1.5 text-right">
              <button onclick="adminUnbanPeer('${escapeHtml(p.peer_id || '')}')" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-emerald-400 border border-emerald-800 text-[10px] transition active:scale-95">Unban</button>
            </td>
          </tr>
        `).join('');
      } catch (err) {
        console.error('Error fetching banned peers:', err);
      }
    }

    async function adminBanPeerAction(specifiedPeerId = '', customReason = '') {
      const peerInput = document.getElementById('adminBanPeerInput');
      const reasonInput = document.getElementById('adminBanReasonInput');
      const peerId = (specifiedPeerId || (peerInput ? peerInput.value.trim() : '')).trim();
      const reason = (customReason || (reasonInput ? reasonInput.value.trim() : 'Moderator ban')).trim();
      if (!peerId) {
        alert('Please specify a peer ID or username to ban.');
        return;
      }
      try {
        const res = await fetch('/api/moderator/ban', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ peer_id: peerId, reason, admin_id: myPeerId, action: 'ban' })
        });
        const out = await res.json();
        if (res.ok) {
          if (peerInput) peerInput.value = '';
          if (reasonInput) reasonInput.value = '';
          alert(`🚫 Peer '${peerId}' has been banned from the mesh.`);
          fetchBannedPeers();
        } else {
          alert('Ban failed: ' + (out.error || 'unknown error'));
        }
      } catch (err) {
        alert('Ban request error: ' + err);
      }
    }

    async function adminUnbanPeer(peerId) {
      if (!peerId) return;
      try {
        await fetch('/api/moderator/ban', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ peer_id: peerId, action: 'unban', admin_id: myPeerId })
        });
        fetchBannedPeers();
      } catch (err) {
        alert('Unban request error: ' + err);
      }
    }

    async function fetchReportedArtifacts() {
      try {
        const res = await fetch('/api/moderator/artifacts');
        if (!res.ok) return;
        const data = await res.json();
        const tbody = document.getElementById('modReportedArtifactsTable');
        if (!tbody) return;
        const artifacts = data.reported_artifacts || [];
        if (artifacts.length === 0) {
          tbody.innerHTML = '<tr><td colspan="5" class="px-3 py-2 text-center text-slate-500 text-[11px]">No reported artifacts to review.</td></tr>';
          return;
        }
        tbody.innerHTML = artifacts.map(a => `
          <tr class="hover:bg-slate-900/60 font-mono text-xs">
            <td class="px-2.5 py-1.5 font-bold text-amber-300">${escapeHtml(a.id || '')}</td>
            <td class="px-2.5 py-1.5 text-cyan-300">${escapeHtml(a.reported_peer || '')}</td>
            <td class="px-2.5 py-1.5 text-slate-300">${escapeHtml(a.artifact_path || '')}</td>
            <td class="px-2.5 py-1.5 text-slate-400">${escapeHtml(a.reason || '')}</td>
            <td class="px-2.5 py-1.5 text-right space-x-1">
              <button onclick="inspectReportedArtifact('${escapeHtml(a.id || '')}')" class="px-2 py-0.5 rounded bg-purple-900 hover:bg-purple-800 text-purple-200 border border-purple-700 text-[10px]">Inspect</button>
              <button onclick="adminBanPeerAction('${escapeHtml(a.reported_peer || '')}', 'Reported artifact violation: ${escapeHtml(a.artifact_path || '')}')" class="px-2 py-0.5 rounded bg-red-900 hover:bg-red-800 text-red-200 border border-red-700 text-[10px]">Ban Author</button>
            </td>
          </tr>
        `).join('');
      } catch (err) {
        console.error('Error fetching reported artifacts:', err);
      }
    }

    async function inspectReportedArtifact(reportId) {
      try {
        const res = await fetch('/api/moderator/artifacts');
        const data = await res.json();
        const rep = (data.reported_artifacts || []).find(r => r.id === reportId);
        if (!rep) return;
        const viewer = document.getElementById('reportedArtifactViewer');
        const titleEl = document.getElementById('reportedArtifactTitle');
        const contentEl = document.getElementById('reportedArtifactContent');
        if (viewer && titleEl && contentEl) {
          titleEl.innerText = `Artifact Report: ${rep.artifact_path} (By @${rep.reported_peer})`;
          contentEl.innerText = `Reported By: ${rep.reporter_id}\nReason: ${rep.reason}\nSpace: ${rep.space_id}\nDate: ${new Date(rep.timestamp * 1000).toLocaleString()}\n\n--- Content Preview ---\n${rep.content_preview || '(empty or binary artifact)'}`;
          viewer.classList.remove('hidden');
        }
      } catch (err) {
        alert('Could not inspect artifact: ' + err);
      }
    }

    // =========================================================================
    // Finder VFS & Ranger Multi-Format Previewer
    // =========================================================================
    let _is3dStudioDocked = false;
    function mount3dStudioInWorkstation(dock) {
      const wsWin = document.getElementById('win-workstation');
      const host = document.getElementById('finderTab-3dstudio');
      const wsBody = document.querySelector('[data-ws-root="true"]');
      const dockBtn = document.getElementById('wsTileSpaceBtn');
      if (!wsWin || !host || !wsBody) return;
      if (dock) {
        if (!_is3dStudioDocked) {
          host.innerHTML = '';
          host.appendChild(wsBody);
          _is3dStudioDocked = true;
        }
        wsWin.classList.add('hidden');
        wsWin.style.display = 'none';
        if (dockBtn) dockBtn.textContent = 'Undock Window';
        if (window.TinCanWorkstation && typeof window.TinCanWorkstation.refresh === 'function') {
          window.TinCanWorkstation.refresh({ immediate: true });
        }
      } else if (_is3dStudioDocked) {
        wsWin.appendChild(wsBody);
        host.innerHTML = '<div class="p-4 font-mono text-xs text-neutral-700">3D Studio is open in its floating window. Click Dock in Workstation or switch back to re-attach.</div>';
        _is3dStudioDocked = false;
        if (dockBtn) dockBtn.textContent = 'Dock in Workstation';
      }
    }

    window.toggleDock3dStudio = function () {
      const wsWin = document.getElementById('win-workstation');
      if (_is3dStudioDocked) {
        mount3dStudioInWorkstation(false);
        switchFinderTab('files');
        if (wsWin) {
          wsWin.classList.remove('hidden', 'minimized');
          wsWin.style.display = 'flex';
          if (typeof bringToFront === 'function') bringToFront(wsWin);
        }
      } else {
        const spWin = document.getElementById('win-agentspace');
        if (spWin) {
          spWin.classList.remove('hidden', 'minimized');
          spWin.style.display = 'flex';
          if (typeof bringToFront === 'function') bringToFront(spWin);
        }
        switchFinderTab('3dstudio');
      }
    };

    function open3dStudioFromWorkstation() {
      const curActive = !document.getElementById('finderTab-3dstudio')?.classList.contains('hidden');
      if (curActive) {
        mount3dStudioInWorkstation(false);
        switchFinderTab('files');
        if (typeof toggleWindow === 'function') {
          const wsWin = document.getElementById('win-workstation');
          if (wsWin && wsWin.classList.contains('hidden')) toggleWindow('win-workstation');
        }
      } else {
        switchFinderTab('3dstudio');
      }
    }

    function switchFinderTab(tab) {
      if (tab === '3dstudio') {
        mount3dStudioInWorkstation(true);
      } else if (_is3dStudioDocked) {
        mount3dStudioInWorkstation(false);
      }
      ['files', '3dstudio', 'vscode', 'artcraft'].forEach(t => {
        const btn = document.getElementById(`finderTabBtn-${t}`);
        const panel = document.getElementById(`finderTab-${t}`);
        if (btn) btn.classList.toggle('is-active', t === tab);
        if (panel) panel.classList.toggle('hidden', t !== tab);
      });
    }

    // ---- Ranger state (memory only; the drive mirror is never saved) ----------
    let rangerMode = 'space';          // 'space' (.space VFS) | 'drive' (hard-drive mirror)
    let rangerItems = [];              // rows currently shown in #spaceFileList
    let rangerIndex = -1;              // keyboard selection
    let rangerView = null;             // file currently in the viewer
    let rangerRaw = false;             // Markdown raw toggle
    let rangerWrap = false;
    let rangerEditing = false;
    let rangerUrls = [];
    const driveState = { provider: null, mirror: null, cwd: '/', rootHandle: null, fileMap: null, rootLabel: '' };
    const RANGER_SKIP = new Set(['node_modules', '.git', '__pycache__', '.venv', 'venv', '.next', 'dist', 'build', 'target', '.cache', '.DS_Store']);
    const RANGER_TEXT_LIMIT = 512 * 1024;
    const RANGER_HL_LIMIT = 200 * 1024;
    const RANGER_LINE_LIMIT = 20000;

    function rangerEsc(s) {
      return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    }
    function rangerFmtSize(n) {
      if (n == null || isNaN(n)) return '';
      if (n < 1024) return `${n} B`;
      if (n < 1048576) return `${(n / 1024).toFixed(1)} KB`;
      if (n < 1073741824) return `${(n / 1048576).toFixed(1)} MB`;
      return `${(n / 1073741824).toFixed(2)} GB`;
    }
    function rangerFmtTime(t) {
      if (!t) return '';
      const ms = typeof t === 'number' ? (t > 1e12 ? t : t * 1000) : Date.parse(t);
      return isNaN(ms) ? '' : 'modified ' + new Date(ms).toLocaleString();
    }
    function rangerExt(p) { const m = /\.([^.\/]+)$/.exec(p || ''); return m ? m[1].toLowerCase() : ''; }
    function rangerKind(path, mime) {
      const e = rangerExt(path);
      if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp', 'ico', 'avif', 'tif', 'tiff'].includes(e)) return 'image';
      if (['mp4', 'webm', 'mov', 'm4v', 'ogv', 'mkv'].includes(e)) return 'video';
      if (['mp3', 'wav', 'ogg', 'm4a', 'flac', 'aac', 'opus'].includes(e)) return 'audio';
      if (['glb', 'gltf', 'obj', 'stl', 'ply'].includes(e)) return 'model';
      if (e === 'pdf' || mime === 'application/pdf') return 'pdf';
      if (['html', 'htm', 'xhtml'].includes(e) || mime === 'text/html') return 'html';
      if (['csv', 'tsv'].includes(e)) return 'table';
      if (e === 'ipynb') return 'notebook';
      if (['woff', 'woff2', 'ttf', 'otf'].includes(e)) return 'font';
      if (e === 'dxf') return 'dxf';
      if (['zip', 'whl', 'jar', 'epub', '3mf', 'tar', 'gz', 'tgz', 'tbz2', 'docx', 'xlsx', 'pptx', 'odt', 'sqlite', 'sqlite3', 'db', 'space', 'wasm', 'bin', 'exe', 'so', 'dylib', 'dll', 'npy', 'npz', 'pkl', 'onnx', 'pt', 'safetensors'].includes(e)) return 'inspectable';
      if (['md', 'markdown', 'mdx'].includes(e)) return 'markdown';
      if (mime && /^image\//.test(mime) && !/^image\/vnd\./.test(mime)) return 'image';
      if (mime && /^video\//.test(mime)) return 'video';
      if (mime && /^audio\//.test(mime)) return 'audio';
      if (mime && /^font\//.test(mime)) return 'font';
      return 'text';
    }
    function rangerIcon(item) {
      if (item.kind === 'up') return '↰';
      if (item.kind === 'dir') return '📁';
      const k = rangerKind(item.path, item.mime);
      return { image: '🖼', video: '🎬', audio: '🎵', model: '🧊', markdown: '📝', pdf: '📕', html: '🌐', table: '📊', notebook: '📓', font: '🔤', dxf: '📐', inspectable: '🗜️' }[k] ||
        ({ py: '🐍', js: '⚡', ts: '⚡', rs: '🦀', json: '🔧', sh: '💲' }[rangerExt(item.path)] || '📄');
    }
    function rangerObjectUrl(blob) { const u = URL.createObjectURL(blob); rangerUrls.push(u); return u; }
    function rangerReleaseUrls() { rangerUrls.forEach(u => { try { URL.revokeObjectURL(u); } catch (e) {} }); rangerUrls = []; }
    function b64ToBlob(b64, mime) {
      const bin = atob(b64); const arr = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
      return new Blob([arr], { type: mime || 'application/octet-stream' });
    }

    // ---- File list (shared by .space and drive mirror) ----------------------
    function setRangerListHeader() {
      ideUpdateStatus();
      const title = document.getElementById('rangerListTitle');
      const newBtn = document.getElementById('rangerNewFileBtn');
      const crumb = document.getElementById('rangerBreadcrumb');
      if (rangerMode === 'drive') {
        if (title) title.textContent = `${driveState.rootLabel || 'Drive'} (read-only mirror)`;
        if (newBtn) newBtn.classList.add('hidden');
        if (crumb) {
          crumb.classList.remove('hidden');
          const parts = (driveState.cwd || '/').split('/').filter(Boolean);
          let acc = '';
          const bits = [`<button class="hover:text-slate-200" data-crumb="/">${rangerEsc(driveState.rootLabel || '~')}</button>`];
          parts.forEach(p => { acc += '/' + p; bits.push(`<span>/</span><button class="hover:text-slate-200" data-crumb="${rangerEsc(acc)}">${rangerEsc(p)}</button>`); });
          crumb.innerHTML = bits.join('');
        }
      } else {
        if (title) title.textContent = 'Files in VFS';
        if (newBtn) newBtn.classList.remove('hidden');
        if (crumb) { crumb.classList.add('hidden'); crumb.innerHTML = ''; }
      }
    }

    function renderRangerList(items) {
      const el = document.getElementById('spaceFileList');
      if (!el) return;
      rangerItems = items;
      setRangerListHeader();
      if (!items.length) {
        el.innerHTML = '<div class="text-slate-500 py-2 text-center text-xs">This folder is empty.</div>';
        rangerIndex = -1;
        return;
      }
      el.innerHTML = items.map((it, i) => {
        const sel = it.kind === 'file' && rangerView && rangerView.source === it.source && rangerView.path === it.path;
        const bg = sel ? 'bg-purple-950/80 text-purple-200 font-bold border-l-2 border-purple-400' : 'hover:bg-slate-900 text-slate-300';
        const size = it.kind === 'file' && it.size != null ? rangerFmtSize(it.size) : (it.kind === 'dir' ? '›' : '');
        return `<div role="option" data-idx="${i}" title="${rangerEsc(it.path || it.name)}" class="ranger-row px-2 py-1.5 cursor-pointer flex items-center justify-between gap-2 transition ${bg}">
              <div class="flex items-center gap-1.5 min-w-0 flex-1"><span class="shrink-0">${rangerIcon(it)}</span><span class="tc-truncate min-w-0">${rangerEsc(it.name)}</span></div>
              <span class="text-[9px] text-slate-500 shrink-0 font-mono">${rangerEsc(size)}</span>
            </div>`;
      }).join('');
      const selIdx = items.findIndex(it => it.kind === 'file' && rangerView && rangerView.source === it.source && rangerView.path === it.path);
      setRangerIndex(selIdx >= 0 ? selIdx : (rangerIndex >= 0 && rangerIndex < items.length ? rangerIndex : -1), false);
    }

    function setRangerIndex(i, scroll = true) {
      const el = document.getElementById('spaceFileList');
      if (!el) return;
      rangerIndex = i;
      el.querySelectorAll('.ranger-row').forEach(r => r.classList.toggle('ring-1', Number(r.dataset.idx) === i));
      el.querySelectorAll('.ranger-row').forEach(r => r.classList.toggle('ring-purple-500/70', Number(r.dataset.idx) === i));
      const row = el.querySelector(`.ranger-row[data-idx="${i}"]`);
      if (row && scroll) row.scrollIntoView({ block: 'nearest' });
    }

    function markRangerSelected(path) {
      const i = rangerItems.findIndex(it => it.path === path);
      if (i >= 0) setRangerIndex(i);
    }

    function activateRangerItem(it) {
      if (!it) return;
      if (it.kind === 'up') return rangerGoUp();
      if (it.kind === 'dir') return navigateDrive(it.path);
      if (it.source === 'space') return openAgentSpaceFile(it.path);
      return openDriveFile(it.path);
    }

    function rangerGoUp() {
      if (rangerMode !== 'drive' || !driveState.cwd || driveState.cwd === '/') return;
      const from = driveState.cwd;
      const parent = from.replace(/\/[^\/]+\/?$/, '') || '/';
      navigateDrive(parent, from);
    }

    (function initRangerListEvents() {
      const el = document.getElementById('spaceFileList');
      const crumb = document.getElementById('rangerBreadcrumb');
      if (crumb) crumb.addEventListener('click', ev => { const b = ev.target.closest('[data-crumb]'); if (b) navigateDrive(b.dataset.crumb); });
      if (!el) return;
      el.addEventListener('click', ev => {
        const row = ev.target.closest('.ranger-row'); if (!row) return;
        const i = Number(row.dataset.idx); setRangerIndex(i, false); el.focus({ preventScroll: true });
        activateRangerItem(rangerItems[i]);
      });
      el.addEventListener('keydown', ev => {
        if (!rangerItems.length && ev.key !== 'ArrowLeft' && ev.key !== 'Backspace') return;
        const n = rangerItems.length;
        if (ev.key === 'ArrowDown') { ev.preventDefault(); setRangerIndex(Math.min(n - 1, rangerIndex + 1)); }
        else if (ev.key === 'ArrowUp') { ev.preventDefault(); setRangerIndex(Math.max(0, rangerIndex - 1)); }
        else if (ev.key === 'Home') { ev.preventDefault(); setRangerIndex(0); }
        else if (ev.key === 'End') { ev.preventDefault(); setRangerIndex(n - 1); }
        else if (ev.key === 'Enter' || ev.key === 'ArrowRight') { ev.preventDefault(); activateRangerItem(rangerItems[rangerIndex]); }
        else if (ev.key === 'ArrowLeft' || ev.key === 'Backspace') { ev.preventDefault(); rangerGoUp(); }
      });
    })();

    function showSpaceVfs() { refreshAgentSpace(); }

    // ---- Hard-drive mirror: gathered fresh at login, held in memory only ------
    async function gatherDriveMirror(trigger) {
      const statusEl = document.getElementById('drivePlacesStatus');
      const listEl = document.getElementById('drivePlacesList');
      const pickBtn = document.getElementById('drivePickBtn');
      driveState.mirror = null;
      if (driveState.provider === 'server') driveState.provider = null;
      if (listEl) listEl.innerHTML = '<div class="text-slate-500 py-1 text-[10px]">Scanning your drive…</div>';
      let status = { available: false };
      try {
        const r = await fetch('/api/drive/status', { cache: 'no-store' });
        if (r.ok) status = await r.json();
      } catch (e) {}
      if (status.available) {
        try {
          const r = await fetch('/api/drive/mirror', { cache: 'no-store' });
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          const m = await r.json();
          driveState.provider = 'server';
          driveState.mirror = m;
          driveState.rootLabel = '~';
          renderDrivePlaces();
          if (pickBtn) pickBtn.classList.add('hidden');
          if (statusEl) statusEl.textContent = `Mirrored ${m.root} · ${m.dev_folder ? 'dev folder ' + m.dev_folder : 'no dev folder found'} · ${m.elapsed_ms} ms${m.truncated ? ' · capped' : ''}`;
          // At login / session start the dev folder opens automatically.
          if ((trigger === 'login' || trigger === 'session-start') && m.dev_folder) navigateDrive(m.dev_folder);
          return;
        } catch (err) {
          if (statusEl) statusEl.textContent = `Drive scan failed: ${err.message}`;
        }
      }
      // Remote server (e.g. Railway): it can't see this computer's disk.
      if (driveState.provider === 'browser' || driveState.provider === 'filelist') {
        renderDrivePlaces();
        return;
      }
      if (listEl) listEl.innerHTML = '';
      if (pickBtn) pickBtn.classList.remove('hidden');
      if (statusEl) statusEl.textContent = status.on_railway
        ? 'TinCan is running on Railway, so it can\'t see your disk. Pick your dev folder to mirror it for this session (read-only, nothing is uploaded or saved).'
        : 'Your drive isn\'t visible from this server. Pick a folder to mirror it for this session (read-only).';
    }

    function renderDrivePlaces() {
      const listEl = document.getElementById('drivePlacesList');
      if (!listEl) return;
      const m = driveState.mirror;
      if (!m) { listEl.innerHTML = ''; return; }
      const node = (n, depth) => {
        const icon = n.kind === 'dev' ? '⭐' : '📁';
        const label = `<span class="truncate">${rangerEsc(n.name)}${n.kind === 'dev' ? ' <span class="text-amber-400/80 text-[9px]">dev</span>' : ''}</span>`;
        const btn = `<button data-place="${rangerEsc(n.path)}" class="flex-1 min-w-0 text-left flex items-center gap-1.5 truncate"><span>${icon}</span>${label}</button>`;
        const kids = (n.children || []);
        if (!kids.length) return `<div class="px-2 py-1 rounded hover:bg-slate-900 text-slate-300 flex items-center" style="padding-left:${0.5 + depth * 0.75}rem">${btn}</div>`;
        return `<details ${n.kind === 'dev' ? 'open' : ''}><summary class="px-2 py-1 rounded hover:bg-slate-900 text-slate-300 flex items-center gap-1 cursor-pointer list-none" style="padding-left:${0.5 + depth * 0.75}rem"><span class="text-slate-600 text-[9px]">▸</span>${btn}</summary>${kids.map(k => node(k, depth + 1)).join('')}</details>`;
      };
      listEl.innerHTML = (m.places || []).map(p => node(p, 0)).join('') || '<div class="text-slate-500 text-[10px]">No folders found.</div>';
    }

    (function initDrivePlacesEvents() {
      const listEl = document.getElementById('drivePlacesList');
      if (!listEl) return;
      listEl.addEventListener('click', ev => {
        const b = ev.target.closest('[data-place]');
        if (!b) return;
        ev.preventDefault();
        navigateDrive(b.dataset.place);
      });
    })();

    // Browser fallback: File System Access API handle, kept in memory for this tab only.
    async function pickBrowserFolder() {
      const statusEl = document.getElementById('drivePlacesStatus');
      if (window.showDirectoryPicker) {
        try {
          const handle = await window.showDirectoryPicker({ id: 'tincan-dev', mode: 'read' });
          driveState.provider = 'browser';
          driveState.rootHandle = handle;
          driveState.fileMap = null;
          driveState.rootLabel = handle.name;
          await buildBrowserMirror();
          navigateDrive('/');
        } catch (err) {
          if (err && err.name !== 'AbortError' && statusEl) statusEl.textContent = `Couldn't open folder: ${err.message}`;
        }
        return;
      }
      // Safari / Firefox: read-only <input webkitdirectory> snapshot.
      const inp = document.createElement('input');
      inp.type = 'file'; inp.webkitdirectory = true; inp.multiple = true;
      inp.onchange = () => {
        const map = new Map();
        let rootName = '';
        for (const f of inp.files) {
          const rel = f.webkitRelativePath || f.name;
          const parts = rel.split('/'); rootName = rootName || parts[0];
          if (parts.some(p => RANGER_SKIP.has(p) || (p.startsWith('.') && p !== rootName))) continue;
          map.set('/' + parts.slice(1).join('/'), f);
        }
        driveState.provider = 'filelist';
        driveState.fileMap = map;
        driveState.rootHandle = null;
        driveState.rootLabel = rootName || 'folder';
        driveState.mirror = { places: [{ name: driveState.rootLabel, path: '/', kind: 'dev', children: [] }] };
        renderDrivePlaces();
        if (statusEl) statusEl.textContent = `Mirroring ${driveState.rootLabel} for this session (${map.size} files, read-only).`;
        navigateDrive('/');
      };
      inp.click();
    }

    async function buildBrowserMirror() {
      const statusEl = document.getElementById('drivePlacesStatus');
      let budget = 1500;
      const walk = async (dirHandle, path, depth) => {
        const node = { name: dirHandle.name, path, children: [] };
        if (depth >= 3) return node;
        const subs = [];
        for await (const [name, h] of dirHandle.entries()) {
          if (h.kind === 'directory' && !RANGER_SKIP.has(name) && !name.startsWith('.')) subs.push([name, h]);
        }
        subs.sort((a, b) => a[0].localeCompare(b[0]));
        for (const [name, h] of subs) {
          if (budget-- <= 0) break;
          node.children.push(await walk(h, (path === '/' ? '' : path) + '/' + name, depth + 1));
        }
        return node;
      };
      const root = await walk(driveState.rootHandle, '/', 0);
      root.kind = 'dev';
      driveState.mirror = { places: [root] };
      renderDrivePlaces();
      const pickBtn = document.getElementById('drivePickBtn');
      if (pickBtn) pickBtn.textContent = '📂 Mirror a different folder…';
      if (statusEl) statusEl.textContent = `Mirroring "${driveState.rootLabel}" for this session only (read-only; not uploaded or saved).`;
    }

    async function browserDirHandle(path) {
      let h = driveState.rootHandle;
      for (const part of (path || '/').split('/').filter(Boolean)) h = await h.getDirectoryHandle(part);
      return h;
    }

    async function driveList(path) {
      if (driveState.provider === 'server') {
        const r = await fetch(`/api/drive/ls?path=${encodeURIComponent(path)}`, { cache: 'no-store' });
        if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || `HTTP ${r.status}`);
        return r.json();
      }
      if (driveState.provider === 'browser') {
        const dh = await browserDirHandle(path);
        const dirs = [], files = [];
        const base = path === '/' ? '' : path;
        for await (const [name, h] of dh.entries()) {
          if (RANGER_SKIP.has(name) || name.startsWith('.')) continue;
          if (dirs.length + files.length >= 300) break;
          if (h.kind === 'directory') dirs.push({ name, path: base + '/' + name });
          else { const f = await h.getFile(); files.push({ name, path: base + '/' + name, size_bytes: f.size, mtime: f.lastModified, mime_type: f.type }); }
        }
        const by = (a, b) => a.name.localeCompare(b.name);
        return { path, dirs: dirs.sort(by), files: files.sort(by) };
      }
      if (driveState.provider === 'filelist') {
        const base = path === '/' ? '' : path;
        const dirs = new Set(), files = [];
        for (const [p, f] of driveState.fileMap) {
          if (!p.startsWith(base + '/')) continue;
          const rest = p.slice(base.length + 1); const i = rest.indexOf('/');
          if (i >= 0) dirs.add(rest.slice(0, i));
          else files.push({ name: rest, path: p, size_bytes: f.size, mtime: f.lastModified, mime_type: f.type });
        }
        return { path, dirs: [...dirs].sort().map(n => ({ name: n, path: base + '/' + n })), files: files.sort((a, b) => a.name.localeCompare(b.name)) };
      }
      throw new Error('No drive mirror yet. Pick a folder first.');
    }

    async function navigateDrive(path, selectPath) {
      const el = document.getElementById('spaceFileList');
      rangerMode = 'drive';
      driveState.cwd = path || '/';
      setRangerListHeader();
      if (el) el.innerHTML = '<div class="text-slate-500 py-2 text-center text-xs">Reading folder…</div>';
      try {
        const data = await driveList(driveState.cwd);
        if (rangerMode !== 'drive' || driveState.cwd !== (path || '/')) return;
        const items = [];
        if (driveState.cwd !== '/') items.push({ kind: 'up', name: '..', path: driveState.cwd.replace(/\/[^\/]+\/?$/, '') || '/' });
        (data.dirs || []).forEach(d => items.push({ kind: 'dir', source: 'drive', name: d.name, path: d.path }));
        (data.files || []).forEach(f => items.push({ kind: 'file', source: 'drive', name: f.name, path: f.path, size: f.size_bytes, mime: f.mime_type }));
        rangerIndex = -1;
        renderRangerList(items);
        if (data.truncated && el) el.insertAdjacentHTML('beforeend', '<div class="text-[10px] text-slate-500 py-1 text-center">Showing the first 300 entries.</div>');
        const back = selectPath ? items.findIndex(it => it.path === selectPath) : -1;
        if (back >= 0) setRangerIndex(back);
        else if (rangerIndex < 0 && items.length) setRangerIndex(Math.min(items.length - 1, driveState.cwd !== '/' ? 1 : 0), false);
      } catch (err) {
        if (el) el.innerHTML = `<div class="text-red-400 py-2 text-center text-xs">Couldn't read folder: ${rangerEsc(err.message)}</div>`;
      }
    }

    async function openDriveFile(path) {
      markRangerSelected(path);
      const name = path.split('/').pop();
      try {
        if (driveState.provider === 'server') {
          const r = await fetch(`/api/drive/file?path=${encodeURIComponent(path)}`, { cache: 'no-store' });
          const rec = await r.json();
          if (!r.ok) throw new Error(rec.error || `HTTP ${r.status}`);
          const kind = rangerKind(path, rec.mime_type);
          const rawUrl = `/api/drive/raw?path=${encodeURIComponent(path)}`;
          showFileInViewer({
            source: 'drive', path, name, size: rec.size_bytes, mtime: rec.mtime, mime: rec.mime_type,
            text: rec.content, binary: rec.is_binary, truncated: rec.truncated, absPath: rec.abs_path,
            mediaUrl: ['image', 'video', 'audio', 'model', 'pdf', 'html', 'font'].includes(kind) ? rawUrl : null,
            downloadUrl: rawUrl + '&download=1',
          });
          return;
        }
        let file;
        if (driveState.provider === 'browser') {
          const parts = path.split('/').filter(Boolean); const fname = parts.pop();
          const dh = await browserDirHandle('/' + parts.join('/'));
          file = await (await dh.getFileHandle(fname)).getFile();
        } else {
          file = driveState.fileMap.get(path);
        }
        if (!file) throw new Error('File not found');
        const kind = rangerKind(path, file.type);
        const view = { source: 'drive', path, name, size: file.size, mtime: file.lastModified, mime: file.type || 'application/octet-stream', file };
        if (['image', 'video', 'audio', 'model', 'pdf', 'html', 'font'].includes(kind)) {
          view.mediaUrl = rangerObjectUrl(file);
        }
        if (['markdown', 'text', 'html', 'table', 'notebook', 'dxf'].includes(kind) || !view.mediaUrl) {
          const head = new Uint8Array(await file.slice(0, 8192).arrayBuffer());
          view.binary = head.includes(0);
          if (!view.binary) {
            view.text = await file.slice(0, RANGER_TEXT_LIMIT).text();
            view.truncated = file.size > RANGER_TEXT_LIMIT;
          }
        }
        showFileInViewer(view);
      } catch (err) {
        showViewerError(path, err.message);
      }
    }

    // ---- Viewer -------------------------------------------------------------
    const RANGER_PANES = ['finderVideoContainer', 'finderAudioContainer', 'finderImageContainer', 'finder3dContainer', 'finderPdfContainer', 'finderHtmlContainer', 'finderRichContainer', 'finderBinaryContainer', 'finderViewerContainer', 'finderCodeContainer', 'ideEmptyPane'];
    function rangerShowPane(id) { RANGER_PANES.forEach(p => { const el = document.getElementById(p); if (el) el.classList.toggle('hidden', p !== id); }); }

    function showViewerError(path, msg) {
      rangerShowPane('finderBinaryContainer');
      const t = document.getElementById('finderBinaryText');
      if (t) t.textContent = `Couldn't open ${path}: ${msg}`;
    }

    function openCurrentHtmlInLocalhostBrowser() {
      const v = rangerView;
      if (!v) return;
      if (v.source === 'space' && typeof window.openInLocalhostBrowser === 'function') {
        window.openInLocalhostBrowser(v.path, { scope: currentSpaceScope || 'user', ownerId: currentSpaceOwner || 'default' });
        return;
      }
      if (v.mediaUrl) window.open(v.mediaUrl, '_blank', 'noopener');
    }

    function _parseCsvRows(text, delim) {
      const rows = [];
      let row = [], cur = '', inQ = false;
      for (let i = 0; i < text.length; i++) {
        const ch = text[i];
        if (inQ) {
          if (ch === '"' && text[i + 1] === '"') { cur += '"'; i++; }
          else if (ch === '"') { inQ = false; }
          else cur += ch;
        } else {
          if (ch === '"') inQ = true;
          else if (ch === delim) { row.push(cur); cur = ''; }
          else if (ch === '\n' || ch === '\r') {
            if (ch === '\r' && text[i + 1] === '\n') i++;
            row.push(cur); rows.push(row); row = []; cur = '';
            if (rows.length >= 250) break;
          } else cur += ch;
        }
      }
      if (cur.length || row.length) { row.push(cur); rows.push(row); }
      return rows;
    }

    function renderCsvTableView(view) {
      const box = document.getElementById('finderRichContainer');
      if (!box) return;
      const delim = rangerExt(view.path) === 'tsv' ? '\t' : ',';
      const rows = _parseCsvRows(view.text || '', delim);
      if (!rows.length) { box.innerHTML = '<div class="text-slate-400">Empty table.</div>'; return; }
      const head = rows[0];
      const body = rows.slice(1);
      box.innerHTML = `
        <div class="flex items-center justify-between text-[11px] text-emerald-300 border-b border-slate-800 pb-1.5">
          <span>📊 ${rangerEsc(view.name)} (${body.length} row${body.length === 1 ? '' : 's'} shown, ${head.length} cols)</span>
          <span class="text-slate-400">Click Raw above for source</span>
        </div>
        <div class="overflow-auto max-h-[520px] border border-slate-800 rounded">
          <table class="min-w-full border-collapse text-[11px]">
            <thead class="bg-slate-950 sticky top-0 text-emerald-200">
              <tr>${head.map(c => `<th class="px-2 py-1 text-left border-b border-slate-800 font-semibold whitespace-nowrap">${rangerEsc(c)}</th>`).join('')}</tr>
            </thead>
            <tbody>
              ${body.map((r, ri) => `<tr class="${ri % 2 ? 'bg-slate-900/40' : 'bg-slate-900/80'} hover:bg-slate-800/70">${head.map((_, ci) => `<td class="px-2 py-1 border-b border-slate-800/60 whitespace-nowrap max-w-[240px] truncate" title="${rangerEsc(r[ci] || '')}">${rangerEsc(r[ci] || '')}</td>`).join('')}</tr>`).join('')}
            </tbody>
          </table>
        </div>`;
    }

    function renderNotebookView(view) {
      const box = document.getElementById('finderRichContainer');
      if (!box) return;
      let nb;
      try { nb = JSON.parse(view.text || '{}'); }
      catch (e) { rangerShowPane('finderViewerContainer'); renderTextView(view); return; }
      const cells = Array.isArray(nb.cells) ? nb.cells : [];
      const lang = (nb.metadata && nb.metadata.kernelspec && nb.metadata.kernelspec.language) || 'python';
      const cards = cells.slice(0, 120).map((cell, idx) => {
        const src = Array.isArray(cell.source) ? cell.source.join('') : String(cell.source || '');
        if (cell.cell_type === 'markdown') {
          return `<div class="p-2.5 rounded border border-slate-800 bg-slate-950/60 ranger-md">${typeof renderMarkdown === 'function' ? renderMarkdown(src) : rangerEsc(src)}</div>`;
        }
        const outs = (Array.isArray(cell.outputs) ? cell.outputs : []).map(o => {
          const data = o.data || {};
          if (data['image/png']) return `<img src="data:image/png;base64,${data['image/png']}" class="max-w-full rounded mt-1 bg-white p-1">`;
          const txt = Array.isArray(o.text) ? o.text.join('') : (Array.isArray(data['text/plain']) ? data['text/plain'].join('') : (data['text/plain'] || o.evalue || ''));
          return txt ? `<pre class="mt-1 p-1.5 rounded bg-black/50 text-emerald-300 text-[10px] overflow-x-auto">${rangerEsc(txt)}</pre>` : '';
        }).join('');
        return `<div class="p-2 rounded border border-slate-800 bg-slate-950/90 space-y-1">
          <div class="text-[10px] text-slate-400">In [${cell.execution_count != null ? cell.execution_count : idx + 1}] · ${rangerEsc(lang)}</div>
          <pre class="overflow-x-auto text-[11px] text-cyan-200">${rangerEsc(src)}</pre>${outs}
        </div>`;
      }).join('');
      box.innerHTML = `<div class="text-[11px] text-cyan-300 border-b border-slate-800 pb-1">📓 Jupyter Notebook (${cells.length} cell${cells.length === 1 ? '' : 's'})</div>${cards || '<div class="text-slate-400">No cells in notebook.</div>'}`;
    }

    async function renderFontPreview(view) {
      const box = document.getElementById('finderRichContainer');
      if (!box) return;
      const fam = 'TinCanFont_' + Math.random().toString(36).slice(2, 8);
      box.innerHTML = `
        <div class="text-[11px] text-cyan-300 border-b border-slate-800 pb-1.5">🔤 Font Specimen · ${rangerEsc(view.name)}</div>
        <div id="finderFontStage" class="space-y-3 p-3 bg-white text-slate-900 rounded">
          <div style="font-size:32px;line-height:1.2">Sphinx of black quartz, judge my vow. 0123456789</div>
          <div style="font-size:18px">ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz !@#$%&amp;*()</div>
          <div style="font-size:13px;color:#475569">The quick brown fox jumps over the lazy dog — TinCan Specimen Preview.</div>
        </div>`;
      try {
        if (typeof FontFace !== 'undefined') {
          const ff = new FontFace(fam, `url("${view.mediaUrl}")`);
          await ff.load();
          document.fonts.add(ff);
          const st = document.getElementById('finderFontStage');
          if (st) st.style.fontFamily = `"${fam}", sans-serif`;
        }
      } catch (e) {}
    }

    function _renderInspectPayload(box, data) {
      if (!data || !data.ok) {
        box.innerHTML = `<div class="text-red-300 text-xs">Inspection failed: ${rangerEsc((data && data.error) || 'unknown error')}</div>`;
        return;
      }
      const header = `<div class="flex flex-wrap items-center justify-between gap-2 text-[11px] border-b border-slate-800 pb-1.5">
        <span class="text-emerald-300 font-semibold">${rangerEsc(data.signature || data.kind || 'Binary Inspector')} · ${rangerFmtSize(data.size_bytes)}</span>
        <span class="text-slate-400 truncate max-w-[300px]" title="SHA-256">${rangerEsc((data.sha256 || '').slice(0, 16))}…</span>
      </div>`;

      if (data.kind === 'archive') {
        const rows = (data.entries || []).map(e => `<tr><td class="px-2 py-0.5 text-cyan-200">${rangerEsc(e.name)}</td><td class="px-2 py-0.5 text-right text-slate-400">${rangerFmtSize(e.size)}</td></tr>`).join('');
        box.innerHTML = header + `<div class="text-[11px] text-slate-300">Archive (${rangerEsc(data.format)}) · ${data.entry_count} entries</div><div class="max-h-[480px] overflow-auto border border-slate-800 rounded"><table class="w-full text-[11px]"><tbody>${rows}</tbody></table></div>`;
        return;
      }
      if (data.kind === 'docx') {
        const paras = (data.paragraphs || []).map(p => `<p class="mb-2 text-slate-100 leading-relaxed">${rangerEsc(p)}</p>`).join('');
        box.innerHTML = header + `<div class="p-3 bg-slate-950 rounded border border-slate-800 max-h-[500px] overflow-auto font-sans text-xs">${paras || '<em>Empty document</em>'}</div>`;
        return;
      }
      if (data.kind === 'xlsx') {
        const sheetsHtml = (data.sheets || []).map(sh => {
          const rws = (sh.rows || []).map((r, ri) => `<tr>${r.map(c => `<td class="px-2 py-0.5 border border-slate-800 ${ri === 0 ? 'font-bold bg-slate-950 text-emerald-200' : ''}">${rangerEsc(c)}</td>`).join('')}</tr>`).join('');
          return `<div class="space-y-1"><div class="text-cyan-300 font-semibold text-[11px]">Sheet: ${rangerEsc(sh.name)}</div><div class="overflow-auto max-h-[300px] border border-slate-800 rounded"><table class="text-[11px] border-collapse"><tbody>${rws}</tbody></table></div></div>`;
        }).join('');
        box.innerHTML = header + (sheetsHtml || '<div class="text-slate-400">No sheets found.</div>');
        return;
      }
      if (data.kind === 'pptx') {
        const slides = (data.slides || []).map(sl => `<div class="p-2.5 rounded border border-slate-800 bg-slate-950 space-y-1"><div class="text-emerald-300 font-semibold text-[10px]">Slide ${sl.slide}</div>${(sl.texts || []).map(t => `<div class="text-slate-100 text-xs">${rangerEsc(t)}</div>`).join('')}</div>`).join('');
        box.innerHTML = header + (slides || '<div class="text-slate-400">No slides extracted.</div>');
        return;
      }
      if (data.kind === 'sqlite') {
        const tbls = (data.tables || []).map(t => {
          const head = (t.columns || []).map(c => `<th class="px-2 py-0.5 text-left border border-slate-800 bg-slate-950 text-cyan-200">${rangerEsc(c)}</th>`).join('');
          const rows = (t.rows || []).map(r => `<tr>${r.map(v => `<td class="px-2 py-0.5 border border-slate-800 max-w-[200px] truncate">${rangerEsc(v)}</td>`).join('')}</tr>`).join('');
          return `<div class="p-2 rounded border border-slate-800 bg-slate-950/70 space-y-1">
            <div class="text-emerald-300 text-[11px] font-semibold">🗄️ ${rangerEsc(t.name)} (${t.row_count} rows)</div>
            <div class="overflow-auto max-h-[220px]"><table class="text-[10px] border-collapse"><thead><tr>${head}</tr></thead><tbody>${rows}</tbody></table></div>
          </div>`;
        }).join('');
        box.innerHTML = header + (tbls || '<div class="text-slate-400">Empty SQLite database.</div>');
        return;
      }
      if (data.kind === 'dxf') {
        const [minx, miny, maxx, maxy] = data.bounds || [0, 0, 100, 100];
        const w = Math.max(1, maxx - minx), h = Math.max(1, maxy - miny), pad = Math.max(w, h) * 0.08;
        const linesSvg = (data.segments || []).map(([x1, y1, x2, y2]) => `<line x1="${x1}" y1="${-y1}" x2="${x2}" y2="${-y2}" stroke="#34d399" stroke-width="${Math.max(w, h) * 0.006}"/>`).join('');
        const circSvg = (data.circles || []).map(([cx, cy, r]) => `<circle cx="${cx}" cy="${-cy}" r="${r}" fill="none" stroke="#38bdf8" stroke-width="${Math.max(w, h) * 0.006}"/>`).join('');
        box.innerHTML = header + `
          <div class="flex items-center justify-between text-[11px] text-slate-300">
            <span>📐 DXF Wireframe (${(data.segments || []).length} lines, ${(data.circles || []).length} circles)</span>
            <button type="button" onclick="launchArtCraftWasmApp('cadcraft')" class="px-2 py-0.5 bg-cyan-700 hover:bg-cyan-600 text-white rounded text-[10px]">Open in CadCraft Web ↗</button>
          </div>
          <svg viewBox="${minx - pad} ${-maxy - pad} ${w + pad * 2} ${h + pad * 2}" class="w-full h-[380px] bg-slate-950 rounded border border-slate-800">${linesSvg}${circSvg}</svg>`;
        return;
      }
      if (data.kind === 'gzip_text') {
        box.innerHTML = header + `<div class="text-[11px] text-emerald-300">Gzip decompressed preview (${rangerFmtSize(data.uncompressed_bytes)})</div><pre class="p-2.5 bg-slate-950 rounded border border-slate-800 overflow-auto max-h-[480px] text-[11px] text-slate-200">${rangerEsc(data.text_preview || '')}</pre>`;
        return;
      }
      box.innerHTML = header + `<pre class="p-2.5 bg-slate-950 rounded border border-slate-800 overflow-auto max-h-[500px] text-[11px] text-emerald-200 leading-relaxed">${rangerEsc(data.hex_dump || '')}</pre>`;
    }

    async function renderBinaryInspectView(view, convert3d) {
      const box = document.getElementById('finderRichContainer');
      if (box && !convert3d) {
        box.innerHTML = `<div class="text-slate-400">Inspecting ${rangerEsc(view.name)}…</div>`;
      }
      try {
        const body = { path: view.path, source: view.source || 'space' };
        if (view.source === 'space') {
          body.scope = currentSpaceScope || 'user';
          body.owner_id = currentSpaceOwner || 'default';
        } else if (view.b64) {
          body.bytes_b64 = view.b64;
        } else if (view.file) {
          const cap = Math.min(view.file.size, 18 * 1024 * 1024);
          const buf = new Uint8Array(await view.file.slice(0, cap).arrayBuffer());
          body.bytes_b64 = _uint8ToBase64(buf);
        }
        const resp = await fetch('/api/file/inspect', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        const data = await resp.json();
        if (!rangerView || rangerView.path !== view.path) return;
        if (convert3d && data.kind === 'model_glb' && data.glb_b64) {
          const nextUrl = rangerObjectUrl(b64ToBlob(data.glb_b64, 'model/gltf-binary'));
          rangerView.b64 = data.glb_b64;
          rangerView.mediaUrl = nextUrl;
          rangerShowPane('finder3dContainer');
          renderModelPreview(nextUrl);
          return;
        }
        if (box) {
          rangerShowPane('finderRichContainer');
          _renderInspectPayload(box, data);
        }
      } catch (err) {
        if (box) box.innerHTML = `<div class="text-red-300">Inspect error: ${rangerEsc(err.message)}</div>`;
      }
    }

    function showFileInViewer(view) {
      if (!rangerView || rangerView.mediaUrl !== view.mediaUrl) {
        // free blob URLs from the previous file (keep the new one)
        rangerUrls = rangerUrls.filter(u => { if (u === view.mediaUrl) return true; try { URL.revokeObjectURL(u); } catch (e) {} return false; });
      }
      rangerView = view;
      rangerRaw = false;
      if (view.source !== 'space') rangerEditing = false;
      const kind = view.binary && !view.mediaUrl ? rangerKind(view.path, view.mime) : rangerKind(view.path, view.mime);
      view.kind = kind;
      const set = (id, txt) => { const el = document.getElementById(id); if (el) el.textContent = txt; };
      const pathEl = document.getElementById('activeFilePath');
      const fullPath = view.absPath || (view.source === 'drive' ? `${driveState.rootLabel || ''}${view.path}` : view.path);
      if (pathEl) { pathEl.textContent = view.path; pathEl.title = fullPath; }
      set('viewerFileIcon', rangerIcon({ kind: 'file', path: view.path, mime: view.mime }));
      set('activeFileMime', view.mime || 'text/plain');
      set('viewerFileSize', rangerFmtSize(view.size));
      set('viewerFileMtime', rangerFmtTime(view.mtime));
      const badge = document.getElementById('viewerSourceBadge');
      if (badge) {
        badge.textContent = view.source === 'space' ? '.space' : 'drive · read-only';
        badge.className = 'ide-chip';
      }
      const spaceActions = document.getElementById('viewerSpaceActions');
      if (spaceActions) spaceActions.classList.toggle('hidden', view.source !== 'space');
      const editBtn = document.getElementById('viewerEditBtn');
      if (editBtn) editBtn.classList.toggle('hidden', view.text == null);
      const rawBtn = document.getElementById('viewerRawToggle');
      const rawCapable = view.text != null && ['markdown', 'html', 'table', 'notebook', 'dxf', 'image', 'model'].includes(kind);
      if (rawBtn) { rawBtn.classList.toggle('hidden', !rawCapable); rawBtn.textContent = 'Raw'; }
      const vs = document.getElementById('viewerVsCodeLink');
      if (vs) {
        // Only offered where it can work: a real file on this computer, served by a local TinCan.
        const ok = view.source === 'drive' && driveState.provider === 'server' && view.absPath;
        vs.classList.toggle('hidden', !ok);
        vs.href = ok ? 'vscode://file' + encodeURI(view.absPath) : '#';
      }
      renderViewerBody();
      ideOnView(view);
    }

    function renderViewerBody() {
      const view = rangerView;
      if (!view) return;
      const kind = view.kind;
      if (rangerEditing && view.source === 'space' && view.text != null) { rangerShowPane('finderCodeContainer'); return; }
      if (rangerRaw && view.text != null) { rangerShowPane('finderViewerContainer'); renderTextView(view); return; }
      if (kind === 'image' && view.mediaUrl) {
        rangerShowPane('finderImageContainer');
        const img = document.getElementById('finderImagePreview'); if (img) { img.src = view.mediaUrl; img.alt = view.name; }
      } else if (kind === 'video' && view.mediaUrl) {
        rangerShowPane('finderVideoContainer');
        const v = document.getElementById('finderVideoPlayer'); if (v) v.src = view.mediaUrl;
      } else if (kind === 'audio' && view.mediaUrl) {
        rangerShowPane('finderAudioContainer');
        const a = document.getElementById('finderAudioPlayer'); if (a) a.src = view.mediaUrl;
      } else if (kind === 'pdf' && view.mediaUrl) {
        rangerShowPane('finderPdfContainer');
        const pf = document.getElementById('finderPdfFrame'); if (pf) pf.src = view.mediaUrl;
      } else if (kind === 'html' && (view.pagesUrl || view.mediaUrl)) {
        rangerShowPane('finderHtmlContainer');
        const hf = document.getElementById('finderHtmlFrame');
        const hl = document.getElementById('finderHtmlUrlLabel');
        const target = view.pagesUrl || view.mediaUrl;
        if (hf) hf.src = target;
        if (hl) hl.textContent = view.pagesUrl ? ('Live URL: ' + view.pagesUrl) : ('HTML Preview · ' + view.name);
      } else if (kind === 'model' && view.mediaUrl) {
        if (['glb', 'gltf'].includes(rangerExt(view.path))) {
          rangerShowPane('finder3dContainer');
          renderModelPreview(view.mediaUrl);
        } else {
          rangerShowPane('finderRichContainer');
          const box = document.getElementById('finderRichContainer');
          if (box) box.innerHTML = `<div class="text-cyan-300">Converting ${rangerEsc(view.name)} to glTF 2.0 3D preview…</div>`;
          renderBinaryInspectView(view, true);
        }
      } else if (kind === 'table' && view.text != null) {
        rangerShowPane('finderRichContainer');
        renderCsvTableView(view);
      } else if (kind === 'notebook' && view.text != null) {
        rangerShowPane('finderRichContainer');
        renderNotebookView(view);
      } else if (kind === 'font' && view.mediaUrl) {
        rangerShowPane('finderRichContainer');
        renderFontPreview(view);
      } else if (kind === 'dxf' || kind === 'inspectable') {
        rangerShowPane('finderRichContainer');
        renderBinaryInspectView(view, false);
      } else if (view.text != null) {
        rangerShowPane('finderViewerContainer');
        renderTextView(view);
      } else {
        rangerShowPane('finderRichContainer');
        renderBinaryInspectView(view, false);
      }
    }

    function renderTextView(view) {
      const box = document.getElementById('finderViewer');
      const notice = document.getElementById('finderViewerNotice');
      if (!box) return;
      const notes = [];
      if (view.truncated) notes.push(`Showing the first ${rangerFmtSize(RANGER_TEXT_LIMIT)} of ${rangerFmtSize(view.size)}. Download for the full file.`);
      let text = view.text || '';
      if (view.kind === 'markdown' && !rangerRaw && text.length <= RANGER_HL_LIMIT) {
        box.innerHTML = `<div class="ranger-md p-3">${renderMarkdown(text)}</div>`;
      } else {
        let lines = text.split('\n');
        if (lines.length > RANGER_LINE_LIMIT) { notes.push(`Showing the first ${RANGER_LINE_LIMIT.toLocaleString()} lines.`); lines = lines.slice(0, RANGER_LINE_LIMIT); text = lines.join('\n'); }
        const lang = rangerLang(view.path);
        const doHl = text.length <= RANGER_HL_LIMIT && lang !== 'text';
        if (!doHl && lang !== 'text') notes.push('Large file: syntax colours off.');
        const htmlLines = doHl ? highlightCode(text, lang) : lines.map(rangerEsc);
        box.innerHTML = `<table class="ranger-code${rangerWrap ? ' wrap' : ''}"><tbody>${htmlLines.map((l, i) => `<tr><td class="ln">${i + 1}</td><td class="lc">${l || ' '}</td></tr>`).join('')}</tbody></table>`;
      }
      if (notice) { notice.textContent = notes.join(' '); notice.classList.toggle('hidden', !notes.length); }
    }

    function toggleViewerRaw() {
      rangerRaw = !rangerRaw;
      const b = document.getElementById('viewerRawToggle'); if (b) b.textContent = rangerRaw ? 'Rendered' : 'Raw';
      renderViewerBody();
    }
    function toggleViewerWrap() {
      rangerWrap = !rangerWrap;
      const b = document.getElementById('viewerWrapToggle'); if (b) b.classList.toggle('is-active', rangerWrap);
      renderViewerBody();
    }
    function toggleViewerEdit(force) {
      if (!rangerView || rangerView.source !== 'space') return;
      rangerEditing = typeof force === 'boolean' ? force : !rangerEditing;
      const b = document.getElementById('viewerEditBtn'); if (b) b.textContent = rangerEditing ? '👁 View' : '✎ Edit';
      if (!rangerEditing) {
        const ed = document.getElementById('agentspaceEditor');
        if (ed && rangerView.text != null) rangerView.text = ed.value;
      }
      renderViewerBody();
    }
    function setViewerEditMode() {
      // Used by flows that drop text into the editor (arena transfer, new file).
      rangerEditing = true;
      const b = document.getElementById('viewerEditBtn'); if (b) b.textContent = '👁 View';
      rangerShowPane('finderCodeContainer');
    }

    async function copyViewerPath() {
      if (!rangerView) return;
      const p = rangerView.absPath || rangerView.path;
      try { await navigator.clipboard.writeText(p); showQuickNotification(`Copied ${p}`); }
      catch (e) { prompt('Copy path:', p); }
    }

    function downloadViewerFile() {
      const v = rangerView;
      if (!v) return;
      let url = v.downloadUrl;
      if (!url) {
        let blob = null;
        if (v.file) blob = v.file;
        else if (v.b64) blob = b64ToBlob(v.b64, v.mime);
        else if (v.text != null) blob = new Blob([v.source === 'space' ? (document.getElementById('agentspaceEditor') || {}).value || v.text : v.text], { type: v.mime || 'text/plain' });
        if (!blob) return;
        url = rangerObjectUrl(blob);
      }
      const a = document.createElement('a');
      a.href = url; a.download = v.name || 'file'; document.body.appendChild(a); a.click(); a.remove();
    }

    let rangerModelViewerLoading = null;
    let activeFinder3dViewer = null;
    function _syncFinder3dAnimations(mv) {
      const sel = document.getElementById('finder3dAnimSelect');
      const statusEl = document.getElementById('finder3dRigStatus');
      if (!mv || !sel) return;
      const anims = Array.isArray(mv.availableAnimations) ? mv.availableAnimations : [];
      sel.innerHTML = '';
      if (anims.length > 0) {
        anims.forEach(a => {
          const opt = document.createElement('option');
          opt.value = a;
          opt.textContent = a;
          sel.appendChild(opt);
        });
        sel.classList.remove('hidden');
        mv.animationName = anims[0];
        if (typeof mv.play === 'function') {
          try { mv.play(); } catch (e) {}
        }
        if (statusEl && (!statusEl.dataset || statusEl.dataset.sticky !== '1')) {
          statusEl.textContent = `Playing ${anims[0]} (${anims.length} clip${anims.length === 1 ? '' : 's'})`;
        }
      } else {
        sel.classList.add('hidden');
        if (statusEl && (!statusEl.dataset || statusEl.dataset.sticky !== '1')) {
          statusEl.textContent = 'Static mesh · Click 🦴 Rig & Animate ($0)';
        }
      }
    }

    function selectFinder3dAnimation(clipName) {
      const mv = activeFinder3dViewer;
      if (!mv) return;
      mv.animationName = clipName;
      if (typeof mv.play === 'function') {
        try { mv.play(); } catch (e) {}
      }
      const statusEl = document.getElementById('finder3dRigStatus');
      if (statusEl) statusEl.textContent = `Playing ${clipName}`;
    }

    function _uint8ToBase64(bytes) {
      let bin = '';
      const chunk = 0x8000;
      for (let i = 0; i < bytes.length; i += chunk) {
        bin += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
      }
      return btoa(bin);
    }

    async function rigActiveSpaceGlb() {
      const view = rangerView;
      if (!view) return;
      const btn = document.getElementById('finder3dRigBtn');
      const statusEl = document.getElementById('finder3dRigStatus');
      const engine = (document.getElementById('finder3dRigEngine') || {}).value || 'hyper3d/rigging';
      const rigType = (document.getElementById('finder3dRigType') || {}).value || 'auto';
      const animation = (document.getElementById('finder3dAnimClip') || {}).value || 'walk';
      const isCloud = engine !== 'local';
      if (btn) btn.disabled = true;
      if (statusEl) {
        statusEl.dataset.sticky = '1';
        statusEl.textContent = isCloud ? `Submitting to ${engine}...` : 'Fitting local bones, weights & walk cycle ($0)...';
      }
      try {
        const peerId = (typeof myPeerId !== 'undefined' && myPeerId) ? myPeerId : 'user';
        const scope = (typeof currentSpaceScope !== 'undefined' && currentSpaceScope) ? currentSpaceScope : 'user';
        const ownerId = (typeof currentSpaceOwner !== 'undefined' && currentSpaceOwner) ? currentSpaceOwner : peerId;
        const payload = { scope, owner_id: ownerId, peer_id: peerId, engine, rig_type: rigType, animation, wait: false };
        if (view.source === 'space' && view.path && /\.glb$/i.test(view.path)) {
          payload.path = view.path;
        } else if (view.b64) {
          if (view.path) payload.path = view.path;
          payload.glb_bytes_b64 = view.b64;
        } else if (view.mediaUrl) {
          const buf = await (await fetch(view.mediaUrl)).arrayBuffer();
          payload.glb_bytes_b64 = _uint8ToBase64(new Uint8Array(buf));
        } else {
          throw new Error('No GLB bytes loaded to rig');
        }
        const resp = await fetch('/api/3d/rig', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        let data = await resp.json();
        if (!resp.ok || !data.ok) {
          throw new Error((data && data.error) || `HTTP ${resp.status}`);
        }
        const costUsd = Number(data.cost_usd || 0);
        if (!data.glb_bytes_b64 && data.uuid) {
          let activeId = data.uuid;
          let activeModel = data.model || engine;
          for (let i = 0; i < 65; i++) {
            await new Promise(r => setTimeout(r, 2500));
            const sr = await fetch('/api/3d/status', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ subscription_key: activeId, key: activeId }),
            });
            const st = await sr.json();
            if (st.uuid && st.uuid !== activeId) activeId = st.uuid;
            if (st.model) activeModel = st.model;
            if (statusEl) statusEl.textContent = `${activeModel}: ${st.status || 'Processing'} (${(i + 1) * 2.5}s)...`;
            if (st.status === 'Done') break;
            if (st.status === 'Failed') throw new Error(st.error || 'Neural rigging failed');
          }
          const dr = await fetch('/api/3d/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              task_uuid: activeId, uuid: activeId, scope, owner_id: ownerId, peer_id: peerId,
              save_path: data.pending_save_path || '', animation, animate_if_empty: true,
            }),
          });
          data = await dr.json();
          if (!dr.ok || (!data.glb_bytes_b64 && !data.downloaded)) {
            throw new Error((data && (data.download_error || data.error)) || 'Neural rig download not ready');
          }
        }
        const animLabel = Array.isArray(data.animations) && data.animations.length ? data.animations.join(', ') : animation;
        if (statusEl) statusEl.textContent = `✓ ${data.model || data.rig_type || engine} (${data.bone_count || 0} bones) · ${animLabel} · $${costUsd.toFixed(2)}`;
        if (typeof refreshAgentSpace === 'function') {
          try { await refreshAgentSpace('background'); } catch (e) {}
        }
        if (data.path && typeof openAgentSpaceFile === 'function') {
          await openAgentSpaceFile(data.path);
          if (statusEl) statusEl.textContent = `✓ Rigged ${data.path.split('/').pop()} (${data.bone_count || 0} bones) · $${costUsd.toFixed(2)}`;
        } else if (data.glb_bytes_b64) {
          const nextUrl = rangerObjectUrl(b64ToBlob(data.glb_bytes_b64, 'model/gltf-binary'));
          rangerView = { ...view, mediaUrl: nextUrl, b64: data.glb_bytes_b64 };
          renderModelPreview(nextUrl);
        }
      } catch (err) {
        if (statusEl) statusEl.textContent = `Rig error: ${err.message}`;
      } finally {
        if (btn) btn.disabled = false;
        if (statusEl) setTimeout(() => { if (statusEl.dataset) delete statusEl.dataset.sticky; }, 3500);
      }
    }

    function renderModelPreview(url) {
      const stage = document.getElementById('finder3dStage');
      const note = document.getElementById('finder3dNote');
      const fallback = document.getElementById('finder3dFallback');
      const sel = document.getElementById('finder3dAnimSelect');
      if (!stage) return;
      stage.innerHTML = '';
      activeFinder3dViewer = null;
      if (sel) sel.classList.add('hidden');
      if (fallback) fallback.classList.remove('hidden');
      if (note) note.textContent = 'Loading 3D preview…';
      if (!rangerModelViewerLoading) {
        rangerModelViewerLoading = new Promise((resolve, reject) => {
          if (window.customElements && customElements.get('model-viewer')) return resolve();
          const s = document.createElement('script');
          s.type = 'module';
          s.src = 'https://unpkg.com/@google/model-viewer@3.5.0/dist/model-viewer.min.js';
          s.onload = () => resolve(); s.onerror = () => reject(new Error('3D viewer could not load (offline?)'));
          document.head.appendChild(s);
        });
      }
      rangerModelViewerLoading.then(() => {
        if (!rangerView || rangerView.mediaUrl !== url) return;
        const mv = document.createElement('model-viewer');
        mv.setAttribute('src', url);
        mv.setAttribute('camera-controls', '');
        mv.setAttribute('auto-rotate', '');
        mv.setAttribute('autoplay', '');
        mv.style.width = '100%'; mv.style.height = '100%'; mv.style.background = 'transparent';
        mv.addEventListener('load', () => _syncFinder3dAnimations(mv));
        activeFinder3dViewer = mv;
        stage.appendChild(mv);
        if (fallback) fallback.classList.add('hidden');
      }).catch(err => { rangerModelViewerLoading = null; if (note) note.textContent = err.message; });
    }

    // ---- Tiny syntax highlighter (no external deps) --------------------------
    const RANGER_LANGS = {
      py: 'py', pyw: 'py', js: 'js', mjs: 'js', cjs: 'js', jsx: 'js', ts: 'js', tsx: 'js', json: 'json', jsonc: 'js',
      rs: 'c', go: 'c', c: 'c', h: 'c', cpp: 'c', hpp: 'c', cc: 'c', java: 'c', kt: 'c', swift: 'c', cs: 'c', css: 'css', scss: 'c',
      sh: 'sh', bash: 'sh', zsh: 'sh', fish: 'sh', yml: 'sh', yaml: 'sh', toml: 'sh', ini: 'sh', cfg: 'sh', conf: 'sh', env: 'sh', rb: 'sh', dockerfile: 'sh', makefile: 'sh', r: 'sh',
      sql: 'sql', lua: 'sql', html: 'html', htm: 'html', xml: 'html', svg: 'html', vue: 'html', md: 'text', txt: 'text', log: 'text', csv: 'text',
    };
    function rangerLang(path) {
      const base = (path || '').split('/').pop().toLowerCase();
      if (base === 'dockerfile' || base === 'makefile') return 'sh';
      return RANGER_LANGS[rangerExt(path)] || 'text';
    }
    const RANGER_KW = new Set(('and as assert async await break case catch class const continue def default del delete do elif else enum export extends ' +
      'false finally fn for from func function global go if impl import in interface is lambda let loop match mod mut new nil none None not null ' +
      'or package pass pub raise return self Self static struct super switch this throw true True False try type typeof use var void where while with yield ' +
      'select insert update delete from where join left right inner outer on group by order having limit values into create table drop alter and or not null ' +
      'echo fi then esac done local export function').split(' '));
    const RANGER_RE_CACHE = {};
    function rangerRegex(lang) {
      if (RANGER_RE_CACHE[lang]) return RANGER_RE_CACHE[lang];
      const parts = [];
      if (lang === 'js' || lang === 'c' || lang === 'css') parts.push('\\/\\*[\\s\\S]*?\\*\\/');
      if (lang === 'js' || lang === 'c') parts.push('\\/\\/[^\\n]*');
      if (lang === 'py' || lang === 'sh') parts.push('#[^\\n]*');
      if (lang === 'sql') parts.push('--[^\\n]*');
      if (lang === 'html') parts.push('<!--[\\s\\S]*?-->', '<\\/?[A-Za-z][\\w:-]*', '\\/?>');
      if (lang === 'py') parts.push('"{3}[\\s\\S]*?"{3}', "'{3}[\\s\\S]*?'{3}");
      parts.push('"(?:\\\\.|[^"\\\\\\n])*"', "'(?:\\\\.|[^'\\\\\\n])*'");
      if (lang === 'js' || lang === 'sh') parts.push('`(?:\\\\.|[^`\\\\])*`');
      parts.push('\\b0x[0-9A-Fa-f]+\\b', '\\b\\d[\\d_]*(?:\\.\\d+)?(?:[eE][+-]?\\d+)?\\b', '[A-Za-z_$][\\w$]*');
      return (RANGER_RE_CACHE[lang] = new RegExp(parts.join('|'), 'g'));
    }
    function highlightCode(src, lang) {
      const re = rangerRegex(lang);
      const toks = [];
      let last = 0, m;
      re.lastIndex = 0;
      while ((m = re.exec(src))) {
        const t = m[0];
        if (!t) { re.lastIndex++; continue; }
        if (m.index > last) toks.push(['', src.slice(last, m.index)]);
        const c = t[0];
        let cls = '';
        if (t.startsWith('/*') || t.startsWith('//') || t.startsWith('<!--') || (c === '#' && (lang === 'py' || lang === 'sh')) || (t.startsWith('--') && lang === 'sql')) cls = 'tk-c';
        else if (c === '"' || c === "'" || c === '`') cls = (lang === 'json' && /^\s*:/.test(src.slice(m.index + t.length))) ? 'tk-k' : 'tk-s';
        else if (c === '<' || (c === '/' && lang === 'html')) cls = 'tk-t';
        else if (/\d/.test(c)) cls = 'tk-n';
        else if (RANGER_KW.has(t) || (lang === 'sql' && RANGER_KW.has(t.toLowerCase()))) cls = 'tk-w';
        else if (src[m.index + t.length] === '(') cls = 'tk-f';
        toks.push([cls, t]);
        last = m.index + t.length;
      }
      if (last < src.length) toks.push(['', src.slice(last)]);
      const lines = [''];
      toks.forEach(([cls, text]) => {
        text.split('\n').forEach((piece, i) => {
          if (i > 0) lines.push('');
          if (piece) lines[lines.length - 1] += cls ? `<span class="${cls}">${rangerEsc(piece)}</span>` : rangerEsc(piece);
        });
      });
      return lines;
    }

    // ---- Small, safe Markdown renderer ---------------------------------------
    function rangerInlineMd(s) {
      let out = rangerEsc(s);
      const codes = [];
      out = out.replace(/`([^`]+)`/g, (_, c) => { codes.push(c); return `\u0000${codes.length - 1}\u0000`; });
      out = out.replace(/!\[([^\]]*)\]\(([^)\s]+)[^)]*\)/g, (_, alt) => `<span class="text-slate-500">[image: ${alt}]</span>`);
      out = out.replace(/\[([^\]]+)\]\(([^)\s]+)[^)]*\)/g, (_, t, u) => {
        const safe = /^(https?:|mailto:|#|\.{0,2}\/|[\w.-]+(\/|$))/i.test(u) && !/^\s*javascript:/i.test(u);
        return safe ? `<a href="${u}" target="_blank" rel="noopener noreferrer" class="text-cyan-300 underline">${t}</a>` : t;
      });
      out = out.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>').replace(/__([^_]+)__/g, '<strong>$1</strong>');
      out = out.replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>').replace(/~~([^~]+)~~/g, '<del>$1</del>');
      return out.replace(/\u0000(\d+)\u0000/g, (_, i) => `<code>${codes[Number(i)]}</code>`);
    }
    function renderMarkdown(src) {
      const lines = src.replace(/\r\n?/g, '\n').split('\n');
      const out = [];
      let para = [], list = null, i = 0;
      const flush = () => { if (para.length) { out.push(`<p>${rangerInlineMd(para.join(' '))}</p>`); para = []; } };
      const closeList = () => { if (list) { out.push(`</${list}>`); list = null; } };
      while (i < lines.length) {
        const line = lines[i];
        let m;
        if ((m = /^\s*(```|~~~)\s*([\w+-]*)/.exec(line))) {
          flush(); closeList();
          const fence = m[1], lang = RANGER_LANGS[(m[2] || '').toLowerCase()] || (m[2] ? (RANGER_LANGS[m[2]] || 'js') : 'text');
          const body = []; i++;
          while (i < lines.length && !lines[i].trim().startsWith(fence)) body.push(lines[i++]);
          i++;
          const code = body.join('\n');
          out.push(`<pre><code>${lang === 'text' ? rangerEsc(code) : highlightCode(code, lang).join('\n')}</code></pre>`);
          continue;
        }
        if ((m = /^(#{1,6})\s+(.*)$/.exec(line))) { flush(); closeList(); out.push(`<h${m[1].length}>${rangerInlineMd(m[2])}</h${m[1].length}>`); }
        else if (/^\s*([-*_])(\s*\1){2,}\s*$/.test(line)) { flush(); closeList(); out.push('<hr>'); }
        else if ((m = /^\s*>\s?(.*)$/.exec(line))) { flush(); closeList(); out.push(`<blockquote>${rangerInlineMd(m[1])}</blockquote>`); }
        else if ((m = /^\s*([-*+]|\d+[.)])\s+(.*)$/.exec(line))) {
          flush();
          const want = /\d/.test(m[1]) ? 'ol' : 'ul';
          if (list !== want) { closeList(); out.push(`<${want}>`); list = want; }
          const task = /^\[([ xX])\]\s+(.*)$/.exec(m[2]);
          out.push(task ? `<li>${task[1].trim() ? '☑' : '☐'} ${rangerInlineMd(task[2])}</li>` : `<li>${rangerInlineMd(m[2])}</li>`);
        }
        else if (/^\s*\|.*\|\s*$/.test(line)) {
          flush(); closeList();
          const rows = [];
          while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) rows.push(lines[i++]);
          const cells = r => r.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim());
          const body = rows.filter(r => !/^\s*\|?\s*:?-{2,}/.test(r));
          out.push('<table>' + body.map((r, ri) => `<tr>${cells(r).map(c => ri === 0 ? `<th>${rangerInlineMd(c)}</th>` : `<td>${rangerInlineMd(c)}</td>`).join('')}</tr>`).join('') + '</table>');
          continue;
        }
        else if (!line.trim()) { flush(); closeList(); }
        else { closeList(); para.push(line.trim()); }
        i++;
      }
      flush(); closeList();
      return out.join('\n');
    }

    // ---- Resizable split between file list and viewer ------------------------
    (function initRangerSplit() {
      const KEY = 'tincan_ide_explorer_pct';
      const split = document.getElementById('rangerSplit');
      const handle = document.getElementById('rangerSplitter');
      if (!split || !handle) return;
      const MIN_LIST = 170, MIN_VIEW = 260, DEFAULT = 24;
      let pct = parseFloat(localStorage.getItem(KEY));
      if (!(pct > 5 && pct < 95)) pct = DEFAULT;
      const clamp = p => {
        const w = split.getBoundingClientRect().width;
        if (!w) return Math.min(80, Math.max(15, p));
        const lo = (MIN_LIST / w) * 100, hi = 100 - ((MIN_VIEW + 12) / w) * 100;
        return hi <= lo ? lo : Math.min(hi, Math.max(lo, p));
      };
      const apply = (p, save) => {
        pct = clamp(p);
        split.style.setProperty('--ranger-list-w', pct.toFixed(2) + '%');
        handle.setAttribute('aria-valuenow', String(Math.round(pct)));
        if (save) { try { localStorage.setItem(KEY, pct.toFixed(2)); } catch (e) {} }
      };
      apply(pct, false);
      let dragging = false;
      // While dragging, freeze the window's height so rewrapping text in the
      // narrower pane cannot shrink or grow it, and stop text selection.
      let frozen = null;
      handle.addEventListener('pointerdown', ev => {
        dragging = true; handle.setPointerCapture(ev.pointerId);
        document.body.style.userSelect = 'none'; document.body.classList.add('tc-dragging'); ev.preventDefault();
        const win = split.closest('.mesh-window');
        const body = split.closest('.window-body');
        frozen = [];
        [[win, 'height'], [body, 'height'], [split, 'minHeight']].forEach(([el, prop]) => {
          if (!el) return;
          frozen.push([el, prop, el.style[prop]]);
          el.style[prop] = el.getBoundingClientRect().height + 'px';
        });
      });
      handle.addEventListener('pointermove', ev => {
        if (!dragging) return;
        const r = split.getBoundingClientRect();
        if (r.width) apply(((ev.clientX - r.left) / r.width) * 100, false);
      });
      const end = ev => {
        if (!dragging) return;
        dragging = false; document.body.style.userSelect = ''; document.body.classList.remove('tc-dragging');
        (frozen || []).forEach(([el, prop, prev]) => { el.style[prop] = prev; });
        frozen = null;
        try { handle.releasePointerCapture(ev.pointerId); } catch (e) {}
        apply(pct, true);
      };
      handle.addEventListener('pointerup', end);
      handle.addEventListener('pointercancel', end);
      handle.addEventListener('dblclick', () => apply(DEFAULT, true));
      handle.addEventListener('keydown', ev => {
        if (ev.key === 'ArrowLeft') { ev.preventDefault(); apply(pct - 2, true); }
        else if (ev.key === 'ArrowRight') { ev.preventDefault(); apply(pct + 2, true); }
      });
      window.addEventListener('resize', () => apply(pct, false));
      // Re-clamp when the window is shown (width was 0 while hidden).
      if (window.ResizeObserver) new ResizeObserver(() => apply(pct, false)).observe(split);
    })();

    // =========================================================================
    // Space IDE: open-file tabs, bottom panel (terminal | output), status bar
    // =========================================================================
    const ideTabs = [];               // {key, source, path, name, view, dirty, buffer}
    let ideActiveKey = null;
    let ideMerkle = '';
    let ideClosedAll = false;         // the user closed every tab: don't auto-open the first file again
    let ideSpaceId = '';
    const IDE_LANGS = { py: 'Python', js: 'JavaScript', mjs: 'JavaScript', jsx: 'JavaScript React', ts: 'TypeScript', tsx: 'TypeScript React', json: 'JSON', rs: 'Rust', go: 'Go',
      c: 'C', h: 'C', cpp: 'C++', java: 'Java', kt: 'Kotlin', swift: 'Swift', cs: 'C#', css: 'CSS', scss: 'SCSS', html: 'HTML', htm: 'HTML', xml: 'XML', svg: 'SVG', md: 'Markdown',
      txt: 'Plain Text', log: 'Log', csv: 'CSV', sh: 'Shell', bash: 'Shell', zsh: 'Shell', yml: 'YAML', yaml: 'YAML', toml: 'TOML', sql: 'SQL', rb: 'Ruby', lua: 'Lua',
      wasm: 'WebAssembly', glb: '3D model', gltf: '3D model', png: 'Image', jpg: 'Image', jpeg: 'Image', gif: 'Image', webp: 'Image', mp4: 'Video', webm: 'Video', mp3: 'Audio', wav: 'Audio' };

    function ideEsc(v) { return String(v == null ? '' : v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }
    function ideKey(view) { return (view.source || 'space') + ':' + view.path; }
    function ideLangName(path) {
      const base = String(path || '').split('/').pop().toLowerCase();
      if (base === 'dockerfile') return 'Dockerfile';
      if (base === 'makefile') return 'Makefile';
      const ext = base.includes('.') ? base.split('.').pop() : '';
      return IDE_LANGS[ext] || 'Plain Text';
    }

    function ideUpdateStatus() {
      const set = (id, v) => { const el = document.getElementById(id); if (el) { el.textContent = v; el.title = v; } };
      set('ideStatSpace', (typeof currentSpaceOwner !== 'undefined' && currentSpaceOwner) || myPeerId || 'default');
      set('ideStatScope', currentSpaceScope + ' scope');
      const v = rangerView;
      set('ideStatFile', v ? (v.source === 'drive' ? 'drive:' : '') + v.path : 'no file');
      set('ideStatLang', v ? ideLangName(v.path) : '–');
      set('ideStatMerkle', 'merkle ' + (ideMerkle || '–'));
      set('ideStatDrive', 'drive: ' + ((driveState && (driveState.rootLabel || driveState.provider)) || 'off'));
    }

    function ideRenderTabs() {
      const box = document.getElementById('ideTabs');
      if (!box) return;
      if (!ideTabs.length) { box.innerHTML = '<span class="ide-tabs-empty">No file open</span>'; return; }
      box.innerHTML = ideTabs.map(t =>
        `<div class="ide-tab${t.key === ideActiveKey ? ' is-active' : ''}" role="tab" aria-selected="${t.key === ideActiveKey}" data-key="${ideEsc(t.key)}" title="${ideEsc((t.source === 'drive' ? 'drive: ' : '') + t.path)}">` +
        `<span class="ide-tab-name">${ideEsc(t.name)}</span><span class="ide-dirty${t.dirty ? '' : ' hidden'}" title="Unsaved changes">●</span>` +
        `<button type="button" class="ide-tab-x" data-close="${ideEsc(t.key)}" aria-label="Close ${ideEsc(t.name)}">×</button></div>`
      ).join('');
      const act = box.querySelector('.ide-tab.is-active');
      if (act && act.scrollIntoView) act.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    }

    function ideOnView(view) {
      const key = ideKey(view);
      let t = ideTabs.find(x => x.key === key);
      if (!t) {
        t = { key, source: view.source || 'space', path: view.path, name: view.name || String(view.path).split('/').pop(), view, dirty: false, buffer: null };
        ideTabs.push(t);
      } else { t.view = view; }
      ideActiveKey = key;
      ideClosedAll = false;
      if (view.source === 'space' && view.text != null) {
        const ed = document.getElementById('agentspaceEditor');
        if (t.buffer != null && ed) ed.value = t.buffer;
        if (!rangerEditing) toggleViewerEdit(true);   // IDE: text files open ready to edit
      }
      ideRenderTabs();
      ideUpdateStatus();
    }

    async function ideActivate(key) {
      const cur = ideTabs.find(x => x.key === ideActiveKey);
      const ed = document.getElementById('agentspaceEditor');
      if (cur && cur.source === 'space' && cur.dirty && ed) cur.buffer = ed.value;
      const t = ideTabs.find(x => x.key === key);
      if (!t) return;
      if (t.source === 'space') await openAgentSpaceFile(t.path);
      else if (typeof openDriveFile === 'function') await openDriveFile(t.path);
      else showFileInViewer(t.view);
    }

    function ideForgetTab(key) {
      const i = ideTabs.findIndex(x => x.key === key);
      if (i < 0) return;
      ideTabs.splice(i, 1);
      if (key === ideActiveKey) ideShowEmpty(i);
      ideRenderTabs();
    }

    function ideShowEmpty(nearIndex) {
      const next = ideTabs[Math.min(nearIndex, ideTabs.length - 1)];
      if (next) { ideActivate(next.key); return; }
      ideActiveKey = null;
      ideClosedAll = true;
      rangerView = null;
      const ed = document.getElementById('agentspaceEditor'); if (ed) ed.value = '';
      const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
      set('activeFilePath', ''); set('activeFileMime', ''); set('viewerFileSize', ''); set('viewerFileMtime', '');
      const actions = document.getElementById('viewerSpaceActions'); if (actions) actions.classList.add('hidden');
      rangerShowPane('ideEmptyPane');
      ideUpdateStatus();
    }

    function ideCloseTab(key) {
      const t = ideTabs.find(x => x.key === key);
      if (!t) return;
      if (t.dirty && !confirm(`Discard unsaved changes to ${t.name}?`)) return;
      ideForgetTab(key);
    }

    function ideMarkSaved() {
      const ed = document.getElementById('agentspaceEditor');
      const t = ideTabs.find(x => x.key === 'space:' + currentSpaceFile);
      if (t) {
        t.dirty = false; t.buffer = null;
        if (t.view && ed) t.view.text = ed.value;
        ideRenderTabs();
      } else {
        setTimeout(() => openAgentSpaceFile(currentSpaceFile), 0);   // a file created from the Explorer opens in a tab
      }
    }

    // Switching space (scope or owner) drops that space's tabs; drive tabs stay.
    function ideSpaceChanged() {
      const id = currentSpaceScope + ':' + currentSpaceOwner;
      if (ideSpaceId && ideSpaceId !== id) {
        const doomed = ideTabs.filter(t => t.source === 'space');
        doomed.forEach(t => { const i = ideTabs.indexOf(t); if (i >= 0) ideTabs.splice(i, 1); });
        if (doomed.some(t => t.key === ideActiveKey)) ideShowEmpty(0);
        ideClosedAll = false;
        ideRenderTabs();
      }
      ideSpaceId = id;
      ideUpdateStatus();
    }

    function ideShowPanel(which) {
      ['terminal', 'output'].forEach(n => {
        const pane = document.getElementById('idePane-' + n);
        const tab = document.getElementById('ideTab-' + n);
        if (pane) pane.classList.toggle('hidden', n !== which);
        if (tab) tab.classList.toggle('is-active', n === which);
      });
      const panel = document.getElementById('idePanel');
      if (panel && panel.classList.contains('is-collapsed')) ideTogglePanel();
      if (which === 'terminal') { const m = document.getElementById('ideTermMount'); if (m && m.__tcShell) m.__tcShell.focus(); }
    }

    function ideTogglePanel() {
      const panel = document.getElementById('idePanel');
      const btn = document.getElementById('ideTogglePanelBtn');
      if (!panel) return;
      const collapsed = panel.classList.toggle('is-collapsed');
      if (btn) btn.textContent = collapsed ? 'Show ▴' : 'Hide ▾';
    }

    (function initIde() {
      const box = document.getElementById('ideTabs');
      if (box) {
        box.addEventListener('click', ev => {
          const x = ev.target.closest('[data-close]');
          if (x) { ev.stopPropagation(); ideCloseTab(x.getAttribute('data-close')); return; }
          const tab = ev.target.closest('.ide-tab');
          if (tab && tab.getAttribute('data-key') !== ideActiveKey) ideActivate(tab.getAttribute('data-key'));
        });
        box.addEventListener('auxclick', ev => {
          const tab = ev.target.closest('.ide-tab');
          if (tab && ev.button === 1) { ev.preventDefault(); ideCloseTab(tab.getAttribute('data-key')); }
        });
      }
      const ed = document.getElementById('agentspaceEditor');
      if (ed) {
        ed.addEventListener('input', () => {
          const t = ideTabs.find(x => x.key === ideActiveKey);
          if (t && t.source === 'space' && !t.dirty) { t.dirty = true; ideRenderTabs(); }
        });
        ed.addEventListener('keydown', ev => {
          if ((ev.metaKey || ev.ctrlKey) && ev.key.toLowerCase() === 's') { ev.preventDefault(); saveAgentSpaceFile(); return; }
          if (ev.key === 'Tab' && !ev.shiftKey && !ev.ctrlKey && !ev.metaKey && !ev.altKey) {
            ev.preventDefault();
            ed.setRangeText('  ', ed.selectionStart, ed.selectionEnd, 'end');
            ed.dispatchEvent(new Event('input'));
          }
        });
      }
      // Resizable bottom panel
      const handle = document.getElementById('idePanelHandle');
      const panel = document.getElementById('idePanel');
      if (handle && panel) {
        let dragging = false;
        handle.addEventListener('pointerdown', ev => { dragging = true; handle.setPointerCapture(ev.pointerId); document.body.style.userSelect = 'none'; ev.preventDefault(); });
        handle.addEventListener('pointermove', ev => {
          if (!dragging) return;
          const host = panel.parentElement.getBoundingClientRect();
          const status = (document.getElementById('ideStatus') || {}).offsetHeight || 0;
          const h = Math.max(90, Math.min(host.height - 150, host.bottom - status - ev.clientY));
          panel.style.setProperty('--ide-panel-h', h + 'px');
        });
        const end = ev => { if (!dragging) return; dragging = false; document.body.style.userSelect = ''; try { handle.releasePointerCapture(ev.pointerId); } catch (e) {} };
        handle.addEventListener('pointerup', end);
        handle.addEventListener('pointercancel', end);
        handle.addEventListener('dblclick', () => panel.style.removeProperty('--ide-panel-h'));
      }
      rangerShowPane('ideEmptyPane');
      ideUpdateStatus();
    })();

    // Back-compat for older callers.
    function navigateFinderPath(path) { navigateDrive(path); }
    function previewFileInFinder(fpath, content = '') {
      showFileInViewer({ source: 'space', path: fpath, name: (fpath || '').split('/').pop(), mime: 'text/plain', text: content || '' });
    }

    function searchVsCodeExtensions() {
      const q = document.getElementById('vscodeExtensionSearchInput')?.value.trim();
      showQuickNotification(`Filtering Open VSX extensions for: "${q || 'all'}"`);
    }

    function installVsCodePlugin(pluginId) {
      showQuickNotification(`✅ Installed ${pluginId} extension to VFS sandbox`);
    }

    function launchPluginService(serviceId) {
      showQuickNotification(`🚀 Launching ${serviceId} microservice in dynamic space`);
      switchFinderTab('files');
    }

    // =========================================================================
    // Notifications
    // =========================================================================
    function showQuickNotification(msg) {
      const banner = document.getElementById('adminBroadcastBanner');
      const textEl = document.getElementById('adminBroadcastText');
      if (banner && textEl) {
        if (typeof setNotificationVariant === 'function') setNotificationVariant('info');
        textEl.innerText = msg;
        textEl.title = msg;
        banner.classList.remove('hidden');
        clearTimeout(showQuickNotification._t);
        showQuickNotification._t = setTimeout(() => {
          // Don't hide an admin broadcast that arrived in the meantime.
          if (banner.dataset.variant === 'info') banner.classList.add('hidden');
        }, 3500);
      }
    }

    function applyInstanceContentParams() {
      const pScope = urlParams.get('scope');
      const pOwner = urlParams.get('owner');
      const pFile = urlParams.get('file');
      const pCmd = urlParams.get('cmd');
      const pTopic = urlParams.get('topic');
      const pBoardTab = urlParams.get('boardTab');
      const pFeedFilter = urlParams.get('feedFilter');
      const pBoardQ = urlParams.get('q');
      const pChannel = urlParams.get('channel');
      const pDm = urlParams.get('dm');
      const pDmLabel = urlParams.get('dmLabel');
      const pAsk = urlParams.get('ask');

      if (pScope && typeof switchSpaceScope === 'function') {
        switchSpaceScope(pScope);
      }
      if (pOwner) {
        const ownerInput = document.getElementById('spaceOwnerInput');
        if (ownerInput) ownerInput.value = pOwner;
        currentSpaceOwner = pOwner;
        window.currentSpaceOwner = pOwner;
        if (!pScope && /^topic-/i.test(pOwner) && typeof selectWorkstationTopicResult === 'function') {
          selectWorkstationTopicResult(pOwner);
        } else if (typeof refreshAgentSpace === 'function') {
          refreshAgentSpace();
        }
      }
      if (pFile && typeof openAgentSpaceFile === 'function') {
        setTimeout(() => openAgentSpaceFile(pFile), 250);
      }
      if (pCmd && typeof execAeonikShellCommand === 'function') {
        setTimeout(() => execAeonikShellCommand(pCmd), 350);
      }
      if (pTopic) {
        activeBoardTopicId = pTopic;
        if (typeof switchBoardTab === 'function') switchBoardTab(pBoardTab || 'discussions');
        if (typeof loadCyberspaceBoard === 'function') loadCyberspaceBoard();
        if (typeof notifyParentInstanceTitle === 'function') notifyParentInstanceTitle('Topic: ' + pTopic);
      } else {
        if (pFeedFilter && typeof setBoardFeedFilter === 'function') setBoardFeedFilter(pFeedFilter);
        if (pBoardTab && typeof switchBoardTab === 'function') switchBoardTab(pBoardTab);
      }
      if (pBoardQ) {
        const bInp = document.getElementById('boardSearchInput');
        if (bInp) bInp.value = pBoardQ;
        if (typeof searchCyberspaceBoard === 'function') searchCyberspaceBoard(pBoardQ);
      }
      if (pDm && typeof selectChatTarget === 'function') {
        selectChatTarget('direct', pDm, pDmLabel || pDm);
      } else if (pChannel && typeof selectChatTarget === 'function') {
        selectChatTarget('channel', pChannel, '#' + String(pChannel).replace(/^#/, ''));
      }
      if (pAsk) {
        const askInp = document.getElementById('aiHomePromptInput') || document.getElementById('aiHomeAskInput');
        if (askInp) askInp.value = pAsk;
      }
    }
    window.applyInstanceContentParams = applyInstanceContentParams;
    setTimeout(applyInstanceContentParams, 120);

    setTimeout(() => {
      const hasPinnedSpace = !!(urlParams.get('scope') || urlParams.get('owner') || urlParams.get('topic') || urlParams.get('file'));
      const ownerInput = document.getElementById('spaceOwnerInput');
      if (!hasPinnedSpace) {
        if (ownerInput && myPeerId) ownerInput.value = myPeerId;
        refreshAgentSpace('background');
      }
      // Session start: gather the drive's folder structure fresh (never saved).
      gatherDriveMirror('session-start');
    }, 2000);

    /*TC_COPILOT_JS*/
    /*TC_TOKEN_VAULT_JS*/
    /*TC_AI_HOME_JS*/
    /*TC_SHELL_JS*/
  </script>
</body>
</html>
"""

# Reusable terminal components: the one-click install card and the TinCanShell shell.
from .install_card import apply_install_card  # noqa: E402
from .shell_component import apply_shell_component  # noqa: E402

MESH_OS_HTML_UI = apply_install_card(apply_shell_component(MESH_OS_HTML_UI))

# Two-brain arena duel + context panel in every arena view (win-arena and win-quests).
from .arena_duel_ui import apply_arena_duel  # noqa: E402

MESH_OS_HTML_UI = apply_arena_duel(MESH_OS_HTML_UI)

# Dedicated TinCan Workstation Studio (NanoGPT OpenRouter/TEE/Heretic + Hyper3D Rodin + Space Bridge).
from .workstation_ui import render_workstation_window_html  # noqa: E402
from .browser_ui import render_browser_window_html  # noqa: E402
from .localhost_ui import render_localhost_window_html  # noqa: E402
try:
    from .node_studio_ui import render_node_studio_window_html  # noqa: E402
except Exception:
    def render_node_studio_window_html() -> str:
        return (
            '<div id="win-nodes" class="mesh-window w-[1080px] max-w-full hidden" '
            'data-zen-window="true" data-window-id="win-nodes" style="top: 68px; left: 88px; z-index: 40;">'
            '<!--TC_TITLEBAR {"id": "win-nodes", "title": "Node Studio · Prompt Island, Timeline & Filter Graph", "badge": "NANOGPT + GEMINI"}-->'
            '<div class="window-body p-4 bg-[#ecf1e6]">'
            '<div class="font-mono text-xs text-[#111111]">Aeonik Node Studio · Image / Text / Video DAG &amp; Non-Destructive Filter Rack</div>'
            '</div>'
            '</div>'
        )

MESH_OS_HTML_UI = MESH_OS_HTML_UI.replace("<!--TC_WORKSTATION_WINDOW-->", render_workstation_window_html(), 1)
MESH_OS_HTML_UI = MESH_OS_HTML_UI.replace("<!--TC_BROWSER_WINDOW-->", render_browser_window_html(), 1)
MESH_OS_HTML_UI = MESH_OS_HTML_UI.replace("<!--TC_LOCALHOST_WINDOW-->", render_localhost_window_html(), 1)
MESH_OS_HTML_UI = MESH_OS_HTML_UI.replace("<!--TC_NODES_WINDOW-->", render_node_studio_window_html(), 1)

# TinCan Terminal AI components: Home AI Command Hub, Copilot Router, and Token Vault Store.
from .ai_home_shell import apply_ai_home_shell  # noqa: E402
from .copilot_ui import apply_copilot_ui  # noqa: E402
from .token_vault_ui import apply_token_vault_ui  # noqa: E402

MESH_OS_HTML_UI = apply_ai_home_shell(apply_copilot_ui(apply_token_vault_ui(MESH_OS_HTML_UI)))

# Zen startup shell (calm feed + launcher), injected so the classic markup above stays untouched.
from .zen_shell import apply_zen_shell  # noqa: E402

MESH_OS_HTML_UI = apply_zen_shell(MESH_OS_HTML_UI)

# Shared Celadon window chrome: one titlebar component, design tokens, fonts, legacy palette compiler.
from .window_chrome import apply_window_chrome  # noqa: E402

MESH_OS_HTML_UI = apply_window_chrome(MESH_OS_HTML_UI)
