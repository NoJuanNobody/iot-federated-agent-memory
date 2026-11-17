"""TinCan Mesh OS — Integrated Desktop Browser Window (`#win-browser`, Aeonik Celadon UI).

Exports ``render_browser_window_html() -> str`` for ``#win-browser``, rendered into
``MESH_OS_HTML_UI`` and compiled cleanly by ``window_chrome.py``.

Supports:
- Real interactive Playwright Chromium streaming view (click coordinates directly on
  rendered screenshot frames, fill/click semantic ``@eN`` DOM elements, scroll, type keys)
  so even ``X-Frame-Options: DENY`` & JS-heavy apps work inside TinCan.
- Clean Reader Markdown extraction & Link Inspector.
- Resizable vertical pane splitter (viewport | inspector), collapse toggle, and
  1-click save to ``.space`` (``/notes/web_*.md`` or ``/images/web_*.png``).
"""

from __future__ import annotations

import html as _html

DEFAULT_BROWSER_BOOKMARKS = (
    ("TinCan Health", "https://iot-federated-agent-memory-production.up.railway.app/api/health"),
    ("GitHub", "https://github.com/NoJuanNobody"),
    ("arXiv AI", "https://arxiv.org/list/cs.AI/recent"),
    ("NanoGPT", "https://nano-gpt.com"),
    ("Hacker News", "https://news.ycombinator.com"),
)


def _browser_css() -> str:
    return r"""      <style id="browserUiCss">
        /* TinCan Browser: Aeonik Celadon & Ink (#ecf1e6 / #f4f8f0 / #ffffff / #111111) */
        #win-browser {
          --br-bg: #ecf1e6;
          --br-card: #f4f8f0;
          --br-paper: #ffffff;
          --br-ink: #111111;
          --br-muted: #4a4a4a;
          --br-faint: #5c5c5c;
          --br-pos: #107a47;
          --br-pos-bg: rgba(16, 122, 71, 0.09);
          --br-hair: 1px solid #111111;
          --br-hair-soft: 1px solid rgba(17, 17, 17, 0.16);
          --br-font: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          --br-mono: "JetBrains Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace;
        }
        #win-browser .hidden { display: none !important; }
        #win-browser .br-body {
          display: flex;
          flex-direction: column;
          flex: 1 1 auto;
          height: min(740px, calc(100vh - 140px));
          min-height: 360px;
          overflow: hidden;
          padding: 0;
          background: var(--br-bg);
          color: var(--br-ink);
          font-family: var(--br-font);
          font-size: 12px;
        }
        #win-browser[data-resized="true"] .br-body,
        #win-browser.maximized .br-body,
        #win-browser.popout-fullscreen .br-body {
          height: 100%;
          max-height: none;
          flex: 1 1 auto;
        }
        #win-browser .br-toolbar {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          gap: 6px;
          padding: 7px 10px;
          background: var(--br-card);
          border-bottom: var(--br-hair);
          flex: 0 0 auto;
        }
        #win-browser .br-nav-group {
          display: inline-flex;
          align-items: center;
          gap: 4px;
        }
        #win-browser .br-btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 4px;
          padding: 4px 10px;
          border: var(--br-hair);
          border-radius: 9999px;
          background: var(--br-paper);
          color: var(--br-ink);
          font-family: var(--br-font);
          font-size: 11px;
          font-weight: 600;
          cursor: pointer;
          white-space: nowrap;
        }
        #win-browser .br-btn:hover { background: var(--br-ink); color: var(--br-bg); }
        #win-browser .br-btn:disabled { opacity: 0.45; cursor: not-allowed; }
        #win-browser .br-btn--solid { background: var(--br-ink); color: var(--br-bg); }
        #win-browser .br-btn--pos { border-color: var(--br-pos); color: var(--br-pos); }
        #win-browser .br-btn--pos:hover { background: var(--br-pos); color: var(--br-paper); }
        #win-browser .br-btn--sm { padding: 2px 9px; font-size: 10px; }
        #win-browser .br-url-form {
          flex: 1 1 260px;
          min-width: 160px;
          display: flex;
          align-items: center;
          gap: 5px;
        }
        #win-browser .br-url-input {
          flex: 1 1 auto;
          min-width: 0;
          padding: 4px 10px;
          border: var(--br-hair);
          border-radius: 9999px;
          background: var(--br-paper);
          color: var(--br-ink);
          font-family: var(--br-mono);
          font-size: 11px;
          outline: none;
        }
        #win-browser .br-subbar {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          justify-content: space-between;
          gap: 6px 10px;
          padding: 4px 10px;
          background: var(--br-bg);
          border-bottom: var(--br-hair-soft);
          flex: 0 0 auto;
        }
        #win-browser .br-seg {
          display: inline-flex;
          border: var(--br-hair);
          border-radius: 9999px;
          overflow: hidden;
          background: var(--br-paper);
        }
        #win-browser .br-seg-btn {
          padding: 2px 10px;
          border: 0;
          background: transparent;
          color: var(--br-ink);
          font-size: 10px;
          font-weight: 600;
          cursor: pointer;
          white-space: nowrap;
        }
        #win-browser .br-seg-btn.is-active { background: var(--br-ink); color: var(--br-bg); }
        #win-browser .br-grid {
          --br-insp-w: 300px;
          flex: 1 1 auto;
          min-height: 0;
          display: grid;
          grid-template-columns: minmax(280px, 1fr) 6px minmax(190px, var(--br-insp-w, 300px));
          overflow: hidden;
        }
        #win-browser .br-grid.is-inspector-collapsed {
          grid-template-columns: minmax(280px, 1fr) 0px 0px;
        }
        #win-browser .br-grid.is-inspector-collapsed #brSplitter,
        #win-browser .br-grid.is-inspector-collapsed #brInspector {
          display: none;
        }
        #win-browser .br-main {
          min-width: 0;
          min-height: 0;
          display: flex;
          flex-direction: column;
          background: var(--br-paper);
          overflow: hidden;
        }
        #win-browser .br-splitter {
          cursor: col-resize;
          border-left: var(--br-hair-soft);
          border-right: var(--br-hair-soft);
          background: transparent;
          touch-action: none;
        }
        #win-browser .br-splitter:hover,
        #win-browser .br-splitter.is-dragging { background: rgba(17, 17, 17, 0.1); }
        #win-browser .br-screen-wrap {
          flex: 1 1 auto;
          min-height: 0;
          overflow: auto;
          background: #f4f8f0;
          display: flex;
          align-items: flex-start;
          justify-content: center;
          padding: 8px;
          position: relative;
        }
        #win-browser #brScreenImg {
          max-width: 100%;
          height: auto;
          border: var(--br-hair);
          border-radius: 6px;
          cursor: crosshair;
          display: block;
          background: #ffffff;
        }
        #win-browser .br-reader {
          flex: 1 1 auto;
          min-height: 0;
          overflow-y: auto;
          padding: 14px 18px;
          font-family: var(--br-mono);
          font-size: 12px;
          line-height: 1.6;
          white-space: pre-wrap;
          color: var(--br-ink);
          background: var(--br-paper);
        }
        #win-browser .br-inspector {
          min-width: 0;
          min-height: 0;
          overflow-y: auto;
          padding: 10px;
          background: var(--br-card);
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        #win-browser .br-card {
          background: var(--br-paper);
          border: var(--br-hair);
          border-radius: 10px;
          padding: 8px;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        #win-browser .br-kicker {
          font-size: 10px;
          font-weight: 700;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: var(--br-faint);
        }
        #win-browser .br-list {
          display: flex;
          flex-direction: column;
          gap: 4px;
          min-height: 64px;
          max-height: 36vh;
          resize: vertical;
          overflow-y: auto;
        }
        #win-browser .br-row-btn {
          text-align: left;
          padding: 4px 6px;
          border: var(--br-hair-soft);
          border-radius: 6px;
          background: var(--br-card);
          color: var(--br-ink);
          font-family: var(--br-mono);
          font-size: 10px;
          cursor: pointer;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        #win-browser .br-row-btn:hover { background: var(--br-ink); color: var(--br-bg); }
        #win-browser .br-status {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          padding: 4px 10px;
          background: var(--br-bg);
          border-top: var(--br-hair);
          font-family: var(--br-mono);
          font-size: 10px;
          color: var(--br-muted);
          flex: 0 0 auto;
        }
        @media (max-width: 820px) {
          #win-browser .br-grid,
          #win-browser .br-grid.is-inspector-collapsed {
            grid-template-columns: 1fr;
          }
          #win-browser .br-splitter { display: none; }
        }
      </style>"""


def _browser_js() -> str:
    return r"""      <script id="browserUiScript">
      (function () {
        if (typeof window === 'undefined' || typeof document === 'undefined') return;

        const el = (id) => document.getElementById(id);
        const readStore = (k) => {
          try { return typeof localStorage !== 'undefined' ? localStorage.getItem(k) : null; } catch (e) { return null; }
        };
        const writeStore = (k, v) => {
          try { if (typeof localStorage !== 'undefined') localStorage.setItem(k, v); } catch (e) {}
        };

        const state = {
          sessionId: readStore('tincan_browser_session') || ('br-' + Math.random().toString(36).slice(2, 10)),
          viewMode: 'live',
          current: null,
          busy: false,
        };
        writeStore('tincan_browser_session', state.sessionId);

        function setBusy(on, msg) {
          state.busy = on;
          const stEl = el('brStatusNote');
          if (stEl && msg) stEl.textContent = msg;
          ['brGoBtn', 'brBackBtn', 'brFwdBtn', 'brReloadBtn', 'brSaveMdBtn', 'brSavePngBtn'].forEach((id) => {
            const b = el(id);
            if (b && id !== 'brBackBtn' && id !== 'brFwdBtn') b.disabled = on;
          });
        }

        function esc(v) {
          return String(v == null ? '' : v).replace(/[&<>"']/g, (c) => (
            { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
          ));
        }

        function switchViewMode(mode) {
          state.viewMode = mode;
          ['live', 'reader', 'elements'].forEach((m) => {
            const btn = el('brModeBtn-' + m);
            if (btn) btn.classList.toggle('is-active', m === mode);
          });
          const livePane = el('brLivePane');
          const readerPane = el('brReaderPane');
          const elPane = el('brElementsStage');
          if (livePane) livePane.classList.toggle('hidden', mode !== 'live');
          if (readerPane) readerPane.classList.toggle('hidden', mode !== 'reader');
          if (elPane) elPane.classList.toggle('hidden', mode !== 'elements');
        }

        function applySnapshot(data) {
          if (!data || typeof data !== 'object') return;
          state.current = data;
          const urlInp = el('brUrlInput');
          if (urlInp && data.url && data.url !== 'about:blank') urlInp.value = data.url;
          const backBtn = el('brBackBtn');
          const fwdBtn = el('brFwdBtn');
          if (backBtn) backBtn.disabled = !data.can_back;
          if (fwdBtn) fwdBtn.disabled = !data.can_forward;

          const engineEl = el('brEngineBadge');
          if (engineEl) engineEl.textContent = String(data.engine || 'reader').toUpperCase() + ' · ' + String(data.status || 200);
          const titleEl = el('brPageTitle');
          if (titleEl) titleEl.textContent = data.title || data.url || 'Ready';

          const img = el('brScreenImg');
          const empty = el('brEmptyNotice');
          if (img && data.screenshot_b64) {
            img.src = 'data:image/png;base64,' + data.screenshot_b64;
            img.classList.remove('hidden');
            if (empty) empty.classList.add('hidden');
          }

          const reader = el('brReaderPane');
          if (reader) {
            reader.textContent = data.text || '(No readable text extracted from this page.)';
          }

          const links = Array.isArray(data.links) ? data.links : [];
          const linksEl = el('brLinksList');
          if (linksEl) {
            linksEl.innerHTML = links.length
              ? links.slice(0, 35).map((l) => (
                  '<button type="button" class="br-row-btn" data-br-nav="' + esc(l.href || '') + '" title="' + esc(l.href || '') + '">' +
                  esc(l.text || l.href || '') + '</button>'
                )).join('')
              : '<div style="font-size:10px;color:#5c5c5c;">No links extracted yet.</div>';
          }

          const elems = Array.isArray(data.elements) ? data.elements : [];
          const elemsHtml = elems.length
            ? elems.slice(0, 40).map((item) => (
                '<button type="button" class="br-row-btn" data-br-click="' + esc(item.ref || item.selector || '') + '" title="' + esc(item.selector || '') + '">' +
                esc((item.ref || '') + ' [' + (item.tag || '') + '] ' + (item.label || '')) + '</button>'
              )).join('')
            : '<div style="font-size:10px;color:#5c5c5c;">No interactive elements captured yet.</div>';
          const inspElems = el('brElementsList');
          const stageElems = el('brElementsStageList');
          if (inspElems) inspElems.innerHTML = elemsHtml;
          if (stageElems) stageElems.innerHTML = elemsHtml;

          const stEl = el('brStatusNote');
          if (stEl) stEl.textContent = (data.engine || 'reader') + ' · HTTP ' + (data.status || 200) + ' · ' + (data.url || '');
        }

        async function apiPost(path, body) {
          if (typeof fetch !== 'function') throw new Error('fetch unavailable');
          const resp = await fetch(path, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body || {}),
          });
          const data = await resp.json();
          if (!resp.ok || data.error) throw new Error(data.error || ('HTTP ' + resp.status));
          return data;
        }

        async function navigate(targetUrl) {
          const inp = el('brUrlInput');
          const url = String(targetUrl || (inp && inp.value) || '').trim();
          if (!url) return null;
          setBusy(true, 'Loading ' + url + '…');
          try {
            const data = await apiPost('/api/browser/navigate', {
              session_id: state.sessionId,
              url,
            });
            applySnapshot(data);
            return data;
          } catch (err) {
            const stEl = el('brStatusNote');
            if (stEl) stEl.textContent = 'Error: ' + err.message;
            return null;
          } finally {
            setBusy(false);
          }
        }

        async function runAction(actionName, opts) {
          setBusy(true, 'Running ' + actionName + '…');
          try {
            const data = await apiPost('/api/browser/action', Object.assign({
              session_id: state.sessionId,
              action: actionName,
            }, opts || {}));
            applySnapshot(data);
            return data;
          } catch (err) {
            const stEl = el('brStatusNote');
            if (stEl) stEl.textContent = 'Action error: ' + err.message;
            return null;
          } finally {
            setBusy(false);
          }
        }

        async function saveToSpace(kind) {
          if (!state.current || !state.current.url || state.current.url === 'about:blank') return null;
          const scope = (typeof currentSpaceScope !== 'undefined' && currentSpaceScope) || 'user';
          const owner = (typeof currentSpaceOwner !== 'undefined' && currentSpaceOwner) || (readStore('tincan_peer_id') || 'default');
          const peer = (typeof myPeerId !== 'undefined' && myPeerId) || owner;
          setBusy(true, 'Saving ' + kind + ' to .space…');
          try {
            const res = await apiPost('/api/browser/save', {
              session_id: state.sessionId,
              scope,
              owner_id: owner,
              peer_id: peer,
              kind,
            });
            const stEl = el('brStatusNote');
            if (stEl) stEl.textContent = 'Saved to .space: ' + (res.path || '');
            if (typeof window.refreshAgentSpace === 'function') {
              try { window.refreshAgentSpace('background'); } catch (e) {}
            }
            return res;
          } catch (err) {
            const stEl = el('brStatusNote');
            if (stEl) stEl.textContent = 'Save error: ' + err.message;
            return null;
          } finally {
            setBusy(false);
          }
        }

        function initSplitter() {
          const grid = el('brGrid');
          const handle = el('brSplitter');
          if (!grid || !handle) return;
          let widthPx = parseFloat(readStore('tincan_br_insp_w') || '') || 300;
          const applyW = (w, save) => {
            widthPx = Math.max(190, Math.min(520, Math.round(w)));
            if (grid.style && typeof grid.style.setProperty === 'function') grid.style.setProperty('--br-insp-w', widthPx + 'px');
            if (save) writeStore('tincan_br_insp_w', String(widthPx));
          };
          applyW(widthPx, false);
          let dragging = false;
          let startX = 0;
          let startW = widthPx;
          handle.addEventListener('pointerdown', (ev) => {
            dragging = true;
            startX = ev.clientX;
            startW = widthPx;
            handle.classList.add('is-dragging');
            if (handle.setPointerCapture) { try { handle.setPointerCapture(ev.pointerId); } catch (e) {} }
            if (ev.preventDefault) ev.preventDefault();
          });
          handle.addEventListener('pointermove', (ev) => {
            if (!dragging) return;
            applyW(startW - (ev.clientX - startX), false);
          });
          const end = (ev) => {
            if (!dragging) return;
            dragging = false;
            handle.classList.remove('is-dragging');
            if (handle.releasePointerCapture) { try { handle.releasePointerCapture(ev.pointerId); } catch (e) {} }
            applyW(widthPx, true);
          };
          handle.addEventListener('pointerup', end);
          handle.addEventListener('pointercancel', end);
          handle.addEventListener('dblclick', () => applyW(300, true));
        }

        function init() {
          const form = el('brUrlForm');
          if (form) form.onsubmit = (ev) => { ev.preventDefault(); navigate(); };
          const backBtn = el('brBackBtn');
          const fwdBtn = el('brFwdBtn');
          const relBtn = el('brReloadBtn');
          if (backBtn) backBtn.onclick = () => runAction('back');
          if (fwdBtn) fwdBtn.onclick = () => runAction('forward');
          if (relBtn) relBtn.onclick = () => runAction('reload');

          const saveMdBtn = el('brSaveMdBtn');
          const savePngBtn = el('brSavePngBtn');
          if (saveMdBtn) saveMdBtn.onclick = () => saveToSpace('markdown');
          if (savePngBtn) savePngBtn.onclick = () => saveToSpace('screenshot');

          const inspBtn = el('brToggleInspectorBtn');
          const grid = el('brGrid');
          if (inspBtn && grid) {
            inspBtn.onclick = () => {
              const hidden = grid.classList.toggle('is-inspector-collapsed');
              inspBtn.classList.toggle('is-active', hidden);
            };
          }

          ['live', 'reader', 'elements'].forEach((m) => {
            const b = el('brModeBtn-' + m);
            if (b) b.onclick = () => switchViewMode(m);
          });

          const img = el('brScreenImg');
          if (img) {
            img.addEventListener('click', (ev) => {
              if (!img.naturalWidth || !img.naturalHeight) return;
              const rect = img.getBoundingClientRect();
              if (!rect.width || !rect.height) return;
              const x = Math.round(((ev.clientX - rect.left) / rect.width) * 1280);
              const y = Math.round(((ev.clientY - rect.top) / rect.height) * 800);
              runAction('click_xy', { x, y });
            });
          }

          const typeBtn = el('brSendTypeBtn');
          const enterBtn = el('brSendEnterBtn');
          const scrollDownBtn = el('brScrollDownBtn');
          const scrollUpBtn = el('brScrollUpBtn');
          if (typeBtn) {
            typeBtn.onclick = () => {
              const txtInp = el('brTypeInput');
              const selInp = el('brSelectorInput');
              const val = txtInp ? txtInp.value : '';
              const sel = selInp ? selInp.value.trim() : '';
              if (!val) return;
              runAction(sel ? 'fill' : 'type', { selector: sel || undefined, text: val });
            };
          }
          if (enterBtn) enterBtn.onclick = () => runAction('press', { key: 'Enter' });
          if (scrollDownBtn) scrollDownBtn.onclick = () => runAction('scroll', { delta_y: 520 });
          if (scrollUpBtn) scrollUpBtn.onclick = () => runAction('scroll', { delta_y: -520 });

          const winEl = el('win-browser');
          if (winEl) {
            winEl.addEventListener('click', (ev) => {
              const bm = ev.target && ev.target.closest ? ev.target.closest('[data-br-nav]') : null;
              if (bm) { navigate(bm.getAttribute('data-br-nav')); return; }
              const cl = ev.target && ev.target.closest ? ev.target.closest('[data-br-click]') : null;
              if (cl) { runAction('click', { selector: cl.getAttribute('data-br-click') }); }
            });
          }

          initSplitter();
        }

        window.TinCanBrowser = { version: 1, navigate, action: runAction, saveToSpace, switchViewMode };
        if (document.readyState === 'loading') {
          document.addEventListener('DOMContentLoaded', init);
        } else {
          init();
        }
      })();
      </script>"""


def render_browser_window_html() -> str:
    """Render the complete ``#win-browser`` Aeonik Celadon Browser window markup."""
    bookmarks = "".join(
        f'<button type="button" class="br-btn br-btn--sm" data-br-nav="{_html.escape(url, quote=True)}">{_html.escape(label)}</button>'
        for label, url in DEFAULT_BROWSER_BOOKMARKS
    )
    css_block = _browser_css()
    js_block = _browser_js()

    return f"""<div id="win-browser" class="mesh-window w-[1060px] max-w-full hidden" data-zen-window="true" data-window-id="win-browser" style="top: 66px; left: 84px; z-index: 38;">
      <!--TC_TITLEBAR {{"id": "win-browser", "title": "Browser", "badge": "CHROMIUM + READER"}}-->
{css_block}
      <div class="window-body br-body aeonik-scope" data-browser-root="true">
        <div class="br-toolbar">
          <div class="br-nav-group">
            <button id="brBackBtn" type="button" class="br-btn br-btn--sm" disabled title="Back">←</button>
            <button id="brFwdBtn" type="button" class="br-btn br-btn--sm" disabled title="Forward">→</button>
            <button id="brReloadBtn" type="button" class="br-btn br-btn--sm" title="Reload page">↻</button>
          </div>
          <form id="brUrlForm" class="br-url-form">
            <input id="brUrlInput" type="text" class="br-url-input" placeholder="Enter URL or domain (e.g. github.com, arxiv.org)…" value="https://arxiv.org/list/cs.AI/recent" aria-label="Browser URL">
            <button id="brGoBtn" type="submit" class="br-btn br-btn--solid">Go</button>
          </form>
          <div class="br-nav-group">
            <button id="brSaveMdBtn" type="button" class="br-btn br-btn--sm br-btn--pos" title="Save extracted Markdown notes into .space /notes/">Save MD</button>
            <button id="brSavePngBtn" type="button" class="br-btn br-btn--sm" title="Save screenshot into .space /images/">Save PNG</button>
            <button id="brToggleInspectorBtn" type="button" class="br-btn br-btn--sm" title="Show/hide Inspector sidebar">Inspector</button>
          </div>
        </div>

        <div class="br-subbar">
          <div class="br-nav-group">
            <span class="br-kicker">Bookmarks:</span>
            {bookmarks}
          </div>
          <div class="br-seg" role="tablist" aria-label="Browser View Mode">
            <button id="brModeBtn-live" type="button" class="br-seg-btn is-active">Chromium View</button>
            <button id="brModeBtn-reader" type="button" class="br-seg-btn">Reader Text</button>
            <button id="brModeBtn-elements" type="button" class="br-seg-btn">DOM Elements</button>
          </div>
        </div>

        <div id="brGrid" class="br-grid">
          <div class="br-main">
            <div class="br-subbar" style="background: var(--br-card);">
              <div class="br-nav-group" style="flex: 1 1 auto; min-width: 180px;">
                <input id="brSelectorInput" type="text" class="br-url-input" style="max-width: 150px;" placeholder="@e1 or selector (opt)">
                <input id="brTypeInput" type="text" class="br-url-input" placeholder="Type text to send or fill selector…">
                <button id="brSendTypeBtn" type="button" class="br-btn br-btn--sm br-btn--solid">Send Text</button>
                <button id="brSendEnterBtn" type="button" class="br-btn br-btn--sm">Enter ↵</button>
              </div>
              <div class="br-nav-group">
                <button id="brScrollUpBtn" type="button" class="br-btn br-btn--sm" title="Scroll up">↑</button>
                <button id="brScrollDownBtn" type="button" class="br-btn br-btn--sm" title="Scroll down">↓</button>
              </div>
            </div>

            <div id="brLivePane" class="br-screen-wrap">
              <div id="brEmptyNotice" style="margin:auto;text-align:center;max-width:440px;padding:20px;font-family:var(--br-mono);">
                <div style="font-size:13px;font-weight:700;margin-bottom:6px;">TinCan Server Browser (Playwright Chromium + Reader)</div>
                <div style="font-size:11px;color:#4a4a4a;">Enter a URL above or click a bookmark to render real JS websites interactively (click directly on screenshots, extract Reader Markdown, or drive via <code>tincan-browse</code> in Terminal).</div>
              </div>
              <img id="brScreenImg" class="hidden" alt="Live TinCan Browser Frame">
            </div>

            <pre id="brReaderPane" class="br-reader hidden">Navigate to a URL to extract clean readable page text.</pre>

            <div id="brElementsStage" class="br-screen-wrap hidden" style="flex-direction:column;align-items:stretch;gap:8px;padding:10px;background:#ffffff;">
              <div class="br-kicker">Click any interactive DOM element below to trigger click:</div>
              <div id="brElementsStageList" class="br-list" style="max-height:none;flex:1 1 auto;"></div>
            </div>
          </div>

          <div id="brSplitter" class="br-splitter" role="separator" aria-orientation="vertical" aria-label="Resize browser inspector"></div>

          <aside id="brInspector" class="br-inspector" aria-label="Browser page inspector">
            <section class="br-card">
              <div class="br-kicker">Page Status</div>
              <div id="brEngineBadge" style="font-family:var(--br-mono);font-size:11px;font-weight:700;">READY</div>
              <div id="brPageTitle" style="font-size:11px;color:#111111;word-break:break-word;">No page loaded</div>
            </section>
            <section class="br-card">
              <div class="br-kicker">Interactive Elements (@eN)</div>
              <div id="brElementsList" class="br-list"></div>
            </section>
            <section class="br-card">
              <div class="br-kicker">Extracted Links</div>
              <div id="brLinksList" class="br-list"></div>
            </section>
          </aside>
        </div>

        <div class="br-status">
          <span id="brStatusNote">Browser ready · click Go to load a page</span>
          <span>Playwright Chromium + HTTP Reader Fallback</span>
        </div>
      </div>
{js_block}
    </div>"""
