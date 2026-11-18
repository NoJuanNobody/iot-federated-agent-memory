"""TinCan Mesh OS — Separate Live-URL Localhost & GitHub-Pages-Style Browser (`#win-localhost`).

Exports ``render_localhost_window_html() -> str`` for ``#win-localhost`` in Aeonik Celadon UI.
Two live browser modes directly on the TinCan deployment URL:
1. ``.space Pages`` (``/pages/<scope>/<owner_id>/...``): GitHub Pages-style multi-file static/build
   hosting straight from ``.space`` VFS (``/index.html``, ``/dist/index.html``, ``/models3d/pikachu_walk.html``,
   with full relative JS/CSS/GLB/PNG resolution).
2. ``Localhost :port`` (``/localhost/<port>/...``): Same-origin reverse proxy to local dev servers
   (Vite :5173, Next :3000, HTTP :8080, preview :4173) running inside the container or local machine.
"""

from __future__ import annotations

import html as _html


def _localhost_css() -> str:
    return """      <style id="localhostWindowCss">
        #win-localhost {
          --lh-bg: #FAFAFA;
          --lh-card: #FFFFFF;
          --lh-ink: #111111;
          --lh-muted: #5A5F66;
          --lh-pos: #107a47;
          --lh-pos-soft: rgba(16, 122, 71, 0.12);
          --lh-hair: 1px solid rgba(17, 17, 17, 0.14);
          --lh-hair-soft: 1px solid rgba(17, 17, 17, 0.08);
          --lh-sans: "Aeonik", "Inter", -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
          --lh-mono: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
          width: min(1040px, 96vw);
          max-width: 100%;
        }
        #win-localhost .hidden { display: none !important; }
        #win-localhost .lh-body {
          background: var(--lh-bg);
          color: var(--lh-ink);
          font-family: var(--lh-sans);
          display: flex;
          flex-direction: column;
          height: clamp(500px, 74vh, 840px);
          min-height: 360px;
          overflow: hidden;
        }
        #win-localhost[data-resized="true"] .lh-body,
        #win-localhost.maximized .lh-body,
        #win-localhost.popout-fullscreen .lh-body {
          height: auto;
          flex: 1 1 auto;
          min-height: 220px;
        }
        #win-localhost .lh-toolbar {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          gap: 6px;
          padding: 7px 10px;
          background: var(--lh-card);
          border-bottom: var(--lh-hair);
          flex: 0 0 auto;
        }
        #win-localhost .lh-subbar {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          padding: 5px 10px;
          background: #F4F4F2;
          border-bottom: var(--lh-hair-soft);
          flex: 0 0 auto;
        }
        #win-localhost .lh-group {
          display: flex;
          align-items: center;
          flex-wrap: wrap;
          gap: 5px;
        }
        #win-localhost .lh-seg {
          display: inline-flex;
          border: var(--lh-hair);
          border-radius: 7px;
          overflow: hidden;
          background: var(--lh-card);
        }
        #win-localhost .lh-seg-btn {
          border: 0;
          border-right: var(--lh-hair-soft);
          background: transparent;
          color: var(--lh-muted);
          padding: 4px 10px;
          font-family: var(--lh-mono);
          font-size: 10px;
          font-weight: 700;
          cursor: pointer;
        }
        #win-localhost .lh-seg-btn:last-child { border-right: 0; }
        #win-localhost .lh-seg-btn.is-active { background: var(--lh-ink); color: var(--lh-bg); }
        #win-localhost .lh-btn {
          font-family: var(--lh-mono);
          font-size: 11px;
          font-weight: 600;
          padding: 4px 10px;
          border-radius: 6px;
          border: var(--lh-hair);
          background: var(--lh-card);
          color: var(--lh-ink);
          cursor: pointer;
          text-decoration: none;
          white-space: nowrap;
        }
        #win-localhost .lh-btn:hover { background: var(--lh-ink); color: var(--lh-bg); }
        #win-localhost .lh-btn--sm { padding: 2px 8px; font-size: 10px; }
        #win-localhost .lh-btn--solid { background: var(--lh-ink); color: var(--lh-bg); }
        #win-localhost .lh-btn--pos { border-color: var(--lh-pos); color: var(--lh-pos); }
        #win-localhost .lh-btn--pos:hover { background: var(--lh-pos); color: var(--lh-card); }
        #win-localhost .lh-input,
        #win-localhost .lh-select {
          font-family: var(--lh-mono);
          font-size: 11px;
          padding: 4px 8px;
          border-radius: 6px;
          border: var(--lh-hair);
          background: var(--lh-bg);
          color: var(--lh-ink);
          outline: none;
        }
        #win-localhost .lh-input:focus,
        #win-localhost .lh-select:focus { border-color: var(--lh-ink); background: var(--lh-card); }
        #win-localhost .lh-kicker {
          font-family: var(--lh-mono);
          font-size: 9px;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: var(--lh-muted);
          font-weight: 700;
        }
        #win-localhost .lh-frame-wrap {
          flex: 1 1 auto;
          min-height: 0;
          position: relative;
          background: #FFFFFF;
          display: flex;
          flex-direction: column;
        }
        #win-localhost .lh-frame {
          width: 100%;
          height: 100%;
          flex: 1 1 auto;
          border: 0;
          background: #FFFFFF;
        }
        #win-localhost .lh-status {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          padding: 4px 10px;
          background: var(--lh-bg);
          border-top: var(--lh-hair);
          font-family: var(--lh-mono);
          font-size: 10px;
          color: var(--lh-muted);
          flex: 0 0 auto;
        }
        /* Monochrome Black & White Dark Mode */
        html[data-theme="dark"] #win-localhost,
        body.tc-dark #win-localhost {
          --lh-bg: #0e0e0e;
          --lh-card: #141414;
          --lh-ink: #f5f5f5;
          --lh-muted: #a3a3a3;
          --lh-pos: #ffffff;
          --lh-pos-soft: rgba(255, 255, 255, 0.12);
          --lh-hair: 1px solid #2e2e2e;
          --lh-hair-soft: 1px solid #262626;
          background: #0e0e0e;
          color: #f5f5f5;
        }
        html[data-theme="dark"] #win-localhost .lh-body,
        body.tc-dark #win-localhost .lh-body {
          background: #0e0e0e;
          color: #f5f5f5;
        }
        html[data-theme="dark"] #win-localhost .lh-toolbar,
        body.tc-dark #win-localhost .lh-toolbar,
        html[data-theme="dark"] #win-localhost .lh-subbar,
        body.tc-dark #win-localhost .lh-subbar {
          background: #141414;
          border-color: #2e2e2e;
          color: #f5f5f5;
        }
        html[data-theme="dark"] #win-localhost .lh-input,
        body.tc-dark #win-localhost .lh-input,
        html[data-theme="dark"] #win-localhost .lh-select,
        body.tc-dark #win-localhost .lh-select,
        html[data-theme="dark"] #win-localhost #lhLiveUrlLabel,
        body.tc-dark #win-localhost #lhLiveUrlLabel,
        html[data-theme="dark"] #win-localhost .lh-status,
        body.tc-dark #win-localhost .lh-status {
          background: #000000;
          color: #f5f5f5;
          border: 1.5px solid #ffffff;
        }
        html[data-theme="dark"] #win-localhost .lh-btn--solid,
        body.tc-dark #win-localhost .lh-btn--solid,
        html[data-theme="dark"] #win-localhost .lh-seg-btn.is-active,
        body.tc-dark #win-localhost .lh-seg-btn.is-active,
        html[data-theme="dark"] #win-localhost .lh-btn:hover,
        body.tc-dark #win-localhost .lh-btn:hover {
          background: #ffffff;
          color: #000000;
          border-color: #ffffff;
        }
        html[data-theme="dark"] #win-localhost .lh-frame-wrap,
        body.tc-dark #win-localhost .lh-frame-wrap {
          background: #0e0e0e;
        }
      </style>"""


def _localhost_js() -> str:
    return r"""      <script id="localhostUiScript">
      (function () {
        if (typeof window === 'undefined' || typeof document === 'undefined') return;

        const el = (id) => document.getElementById(id);
        const state = {
          mode: 'pages',
          scope: 'user',
          ownerId: 'default',
          pagePath: '/',
          port: 5173,
          portPath: '/',
          autoReload: true,
          lastMerkle: '',
          merkleTimer: null,
        };

        function syncSpaceOwnerDefaults() {
          if (window.currentSpaceScope) state.scope = String(window.currentSpaceScope);
          if (window.currentSpaceOwner) state.ownerId = String(window.currentSpaceOwner);
          else {
            const ownerInp = el('spaceOwnerInput');
            if (ownerInp && ownerInp.value.trim()) state.ownerId = ownerInp.value.trim();
            else if (typeof window.myPeerId === 'string' && window.myPeerId) state.ownerId = window.myPeerId;
          }
          const sEl = el('lhScopeSelect');
          const oEl = el('lhOwnerInput');
          if (sEl && !sEl.dataset.dirty) sEl.value = state.scope;
          if (oEl && !oEl.dataset.dirty) oEl.value = state.ownerId;
        }

        function computeTargetUrl() {
          const sEl = el('lhScopeSelect');
          const oEl = el('lhOwnerInput');
          const pEl = el('lhPathInput');
          const portEl = el('lhPortInput');
          if (state.mode === 'localhost') {
            const pNum = Math.max(1024, Math.min(65535, parseInt((portEl && portEl.value) || state.port, 10) || 5173));
            state.port = pNum;
            let rel = ((pEl && pEl.value) || '/').trim() || '/';
            if (!rel.startsWith('/')) rel = '/' + rel;
            state.portPath = rel;
            return '/localhost/' + pNum + rel;
          }
          state.scope = (sEl && sEl.value) || state.scope || 'user';
          state.ownerId = ((oEl && oEl.value) || state.ownerId || 'default').trim();
          let sub = ((pEl && pEl.value) || '/').trim() || '/';
          if (!sub.startsWith('/')) sub = '/' + sub;
          state.pagePath = sub;
          return '/pages/' + encodeURIComponent(state.scope) + '/' + encodeURIComponent(state.ownerId) + sub;
        }

        function setMode(nextMode) {
          state.mode = nextMode === 'localhost' ? 'localhost' : 'pages';
          const btnPages = el('lhModePagesBtn');
          const btnPort = el('lhModePortBtn');
          if (btnPages) btnPages.classList.toggle('is-active', state.mode === 'pages');
          if (btnPort) btnPort.classList.toggle('is-active', state.mode === 'localhost');
          const pagesCtrls = el('lhPagesControls');
          const portCtrls = el('lhPortControls');
          if (pagesCtrls) pagesCtrls.classList.toggle('hidden', state.mode !== 'pages');
          if (portCtrls) portCtrls.classList.toggle('hidden', state.mode !== 'localhost');
          const pEl = el('lhPathInput');
          if (pEl) pEl.value = state.mode === 'localhost' ? state.portPath : state.pagePath;
        }

        function navigate(opts) {
          if (opts && opts.mode) setMode(opts.mode);
          const url = computeTargetUrl();
          const frame = el('lhFrame');
          const label = el('lhLiveUrlLabel');
          const tabLink = el('lhOpenTabLink');
          const st = el('lhStatusNote');
          const absUrl = (typeof location !== 'undefined' && location.origin && location.origin !== 'null')
            ? (location.origin + url)
            : url;
          if (label) label.textContent = absUrl;
          if (tabLink) tabLink.href = url;
          if (st) st.textContent = 'Serving ' + url + (state.mode === 'pages' ? ' (.space gh-pages route)' : ' (localhost reverse proxy)');
          if (frame) frame.src = url;
        }

        async function refreshPagesList(autoLoadEntry) {
          syncSpaceOwnerDefaults();
          const sEl = el('lhScopeSelect');
          const oEl = el('lhOwnerInput');
          const entrySel = el('lhEntrySelect');
          const scope = (sEl && sEl.value) || state.scope;
          const ownerId = ((oEl && oEl.value) || state.ownerId || 'default').trim();
          try {
            const resp = await fetch('/api/pages/list?scope=' + encodeURIComponent(scope) + '&owner_id=' + encodeURIComponent(ownerId), { cache: 'no-store' });
            if (!resp.ok) return;
            const data = await resp.json();
            if (data.merkle_root) state.lastMerkle = String(data.merkle_root);
            if (entrySel) {
              const prev = entrySel.value;
              const entries = Array.isArray(data.entrypoints) ? data.entrypoints : ['/'];
              entrySel.innerHTML = '';
              entries.forEach((ep) => {
                const opt = document.createElement('option');
                opt.value = ep.path || ep;
                opt.textContent = ep.label || opt.value;
                entrySel.appendChild(opt);
              });
              if (prev && [...entrySel.options].some((o) => o.value === prev)) {
                entrySel.value = prev;
              }
            }
            if (autoLoadEntry && data.default_path) {
              const pEl = el('lhPathInput');
              if (pEl && (!pEl.value || pEl.value === '/')) pEl.value = '/';
            }
          } catch (e) {}
        }

        async function checkAutoReload() {
          if (!state.autoReload || state.mode !== 'pages') return;
          const win = el('win-localhost');
          if (!win || win.classList.contains('hidden')) return;
          try {
            const resp = await fetch('/api/space/ls?scope=' + encodeURIComponent(state.scope) + '&owner_id=' + encodeURIComponent(state.ownerId), { cache: 'no-store' });
            if (!resp.ok) return;
            const data = await resp.json();
            const m = String(data.merkle_root || '');
            if (state.lastMerkle && m && m !== state.lastMerkle) {
              state.lastMerkle = m;
              await refreshPagesList(false);
              navigate();
            } else if (m) {
              state.lastMerkle = m;
            }
          } catch (e) {}
        }

        function openSpacePage(path, opts) {
          syncSpaceOwnerDefaults();
          if (opts && opts.scope) {
            state.scope = opts.scope;
            const sEl = el('lhScopeSelect');
            if (sEl) sEl.value = opts.scope;
          }
          if (opts && opts.ownerId) {
            state.ownerId = opts.ownerId;
            const oEl = el('lhOwnerInput');
            if (oEl) oEl.value = opts.ownerId;
          }
          setMode('pages');
          const pEl = el('lhPathInput');
          if (pEl) pEl.value = path || '/';
          if (typeof window.openSingleWindow === 'function' || typeof window.toggleWindow === 'function') {
            const win = el('win-localhost');
            if (win && win.classList.contains('hidden') && typeof window.toggleWindow === 'function') {
              window.toggleWindow('win-localhost');
            }
          }
          refreshPagesList(false).then(() => navigate());
        }

        function openLocalhostPort(port, path) {
          setMode('localhost');
          const portEl = el('lhPortInput');
          const pEl = el('lhPathInput');
          if (portEl && port) portEl.value = String(port);
          if (pEl) pEl.value = path || '/';
          const win = el('win-localhost');
          if (win && win.classList.contains('hidden') && typeof window.toggleWindow === 'function') {
            window.toggleWindow('win-localhost');
          }
          navigate();
        }

        function init() {
          syncSpaceOwnerDefaults();
          const form = el('lhNavForm');
          if (form) form.addEventListener('submit', (ev) => { ev.preventDefault(); navigate(); });
          const modePages = el('lhModePagesBtn');
          const modePort = el('lhModePortBtn');
          if (modePages) modePages.onclick = () => { setMode('pages'); navigate(); };
          if (modePort) modePort.onclick = () => { setMode('localhost'); navigate(); };
          const reloadBtn = el('lhReloadBtn');
          if (reloadBtn) reloadBtn.onclick = () => { refreshPagesList(false); navigate(); };
          const copyBtn = el('lhCopyUrlBtn');
          if (copyBtn) {
            copyBtn.onclick = async () => {
              const txt = (el('lhLiveUrlLabel') || {}).textContent || computeTargetUrl();
              try {
                await navigator.clipboard.writeText(txt);
                const st = el('lhStatusNote');
                if (st) st.textContent = 'Copied live URL: ' + txt;
              } catch (e) {}
            };
          }
          const sEl = el('lhScopeSelect');
          const oEl = el('lhOwnerInput');
          if (sEl) sEl.addEventListener('change', () => { sEl.dataset.dirty = '1'; refreshPagesList(false).then(() => navigate()); });
          if (oEl) oEl.addEventListener('change', () => { oEl.dataset.dirty = '1'; refreshPagesList(false).then(() => navigate()); });
          const entrySel = el('lhEntrySelect');
          if (entrySel) {
            entrySel.addEventListener('change', () => {
              const pEl = el('lhPathInput');
              if (pEl) pEl.value = entrySel.value || '/';
              navigate();
            });
          }
          const autoChk = el('lhAutoReloadChk');
          if (autoChk) autoChk.addEventListener('change', () => { state.autoReload = Boolean(autoChk.checked); });
          const winEl = el('win-localhost');
          if (winEl) {
            winEl.addEventListener('click', (ev) => {
              const chip = ev.target && ev.target.closest ? ev.target.closest('[data-lh-port]') : null;
              if (chip) openLocalhostPort(chip.getAttribute('data-lh-port'), '/');
            });
          }
          refreshPagesList(true).then(() => navigate());
          if (!state.merkleTimer) {
            state.merkleTimer = setInterval(checkAutoReload, 4000);
          }
        }

        window.TinCanLocalhost = {
          version: 1,
          openSpacePage,
          openLocalhostPort,
          reload: () => navigate(),
          refreshPagesList,
        };
        window.openInLocalhostBrowser = openSpacePage;

        if (document.readyState === 'loading') {
          document.addEventListener('DOMContentLoaded', init);
        } else {
          init();
        }
      })();
      </script>"""


def render_localhost_window_html() -> str:
    """Render the complete ``#win-localhost`` Aeonik Celadon Live Localhost & Pages window markup."""
    presets = "".join(
        f'<button type="button" class="lh-btn lh-btn--sm" data-lh-port="{_html.escape(str(port))}">:{port}</button>'
        for port in (5173, 3000, 8080, 4173, 3001)
    )
    css_block = _localhost_css()
    js_block = _localhost_js()

    return f"""<div id="win-localhost" class="mesh-window w-[1040px] max-w-full hidden" data-zen-window="true" data-window-id="win-localhost" style="top: 74px; left: 96px; z-index: 39;">
      <!--TC_TITLEBAR {{"id": "win-localhost", "title": "Localhost", "badge": "GH-PAGES · :PORT"}}-->
{css_block}
      <div class="window-body lh-body aeonik-scope" data-localhost-root="true">
        <div class="lh-toolbar">
          <div class="lh-seg" role="tablist" aria-label="Localhost Preview Mode">
            <button id="lhModePagesBtn" type="button" class="lh-seg-btn is-active">.space Pages (gh-pages)</button>
            <button id="lhModePortBtn" type="button" class="lh-seg-btn">Localhost :port</button>
          </div>

          <form id="lhNavForm" class="lh-group" style="flex: 1 1 auto; min-width: 220px;">
            <span id="lhPagesControls" class="lh-group">
              <select id="lhScopeSelect" class="lh-select" aria-label="Space scope">
                <option value="user">user</option>
                <option value="topic">topic</option>
                <option value="project">project</option>
              </select>
              <input id="lhOwnerInput" type="text" class="lh-input" style="width: 110px;" placeholder="owner_id" value="default" aria-label="Space owner">
              <select id="lhEntrySelect" class="lh-select" style="max-width: 190px;" aria-label="Built pages in .space">
                <option value="/">/ (auto index / dir)</option>
              </select>
            </span>

            <span id="lhPortControls" class="lh-group hidden">
              <input id="lhPortInput" type="number" min="1024" max="65535" value="5173" class="lh-input" style="width: 82px;" aria-label="Localhost port">
              {presets}
            </span>

            <input id="lhPathInput" type="text" class="lh-input" style="flex: 1 1 150px;" value="/" placeholder="/ or /dist/index.html or /models3d/pikachu_walk.html" aria-label="Site subpath">
            <button id="lhGoBtn" type="submit" class="lh-btn lh-btn--solid">Go</button>
          </form>

          <div class="lh-group">
            <button id="lhReloadBtn" type="button" class="lh-btn lh-btn--sm" title="Reload iframe">↻ Reload</button>
            <button id="lhCopyUrlBtn" type="button" class="lh-btn lh-btn--sm" title="Copy live URL">Copy URL</button>
            <a id="lhOpenTabLink" href="/pages/user/default/" target="_blank" rel="noopener" class="lh-btn lh-btn--sm lh-btn--pos">Live Tab ↗</a>
          </div>
        </div>

        <div class="lh-subbar">
          <div class="lh-group" style="min-width: 0; flex: 1 1 auto;">
            <span class="lh-kicker">Live URL:</span>
            <code id="lhLiveUrlLabel" style="font-family: var(--lh-mono); font-size: 10px; color: var(--lh-ink); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">/pages/user/default/</code>
          </div>
          <label class="lh-group" style="font-family: var(--lh-mono); font-size: 10px; color: var(--lh-muted); cursor: pointer;">
            <input id="lhAutoReloadChk" type="checkbox" checked> Auto-reload on build
          </label>
        </div>

        <div class="lh-frame-wrap">
          <iframe id="lhFrame" class="lh-frame" src="about:blank" title="TinCan Localhost &amp; Pages Preview"></iframe>
        </div>

        <div class="lh-status">
          <span id="lhStatusNote">Ready · .space builds serve live like GitHub Pages at /pages/&lt;scope&gt;/&lt;owner&gt;/</span>
          <span>Live Same-Origin Interactive Preview · WebGL / Three.js / WASM Enabled</span>
        </div>
      </div>
{js_block}
    </div>"""
