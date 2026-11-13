"""TinCan Mesh OS — Space window: a ranger-style file manager over the Space VFS.

Three miller columns (parent / current / preview at 1:3:4), ranger's keys (hjkl, gg/G,
space marks, yy/dd/pp, dD, cw/a/A/I, / n N, f, zf, o<key>, zh, m/' bookmarks, g<key>,
gn/gt tabs, H/L history), a `:` console, real previews served from /api/space/raw, and
two side panes that do real work: Open VSX extensions recorded in .vscode/extensions.json
(some of which light up here: Prettier, Markdown preview, glTF viewers, Python), and the
ArtCraft desktop apps (open on the relay's computer when it has them, otherwise download).

Applied after the terminal theme (`apply_space_finder`); exposes `window.tcSpace`.
"""

SPACE_HEAD = r"""
  <style id="tcSpaceStyle">
    #win-agentspace .tc-space-body { display: flex !important; flex-direction: column; padding: 0 !important; height: min(660px, calc(100dvh - 210px)); max-height: none !important; overflow: hidden !important; }
    #win-agentspace .tc-space-bar { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; padding: 10px 16px; border-bottom: 1px solid var(--tc-ink); }
    #win-agentspace .tc-seg { display: inline-flex; }
    #win-agentspace .tc-seg button { padding: 4px 10px !important; margin-right: -1px; }
    #win-agentspace #tcSpacePick { max-width: 260px; padding: 4px 6px !important; }
    #win-agentspace .tc-space-tabs { display: flex; align-items: stretch; border-bottom: 1px solid var(--tc-ink); padding: 0 16px; }
    #win-agentspace .tc-space-tabs [role="tab"] { border: 0 !important; border-bottom: 2px solid transparent !important; padding: 8px 12px 7px !important; font-size: 12px !important; text-transform: lowercase; }
    #win-agentspace .tc-space-tabs [role="tab"][aria-selected="true"] { background: transparent !important; color: var(--tc-ink) !important; border-bottom-color: var(--tc-ink) !important; font-weight: 700 !important; }
    #win-agentspace .tc-space-tabs [role="tab"]:hover { background: var(--tc-paper-2) !important; color: var(--tc-ink) !important; }
    #win-agentspace .tc-space-tabs .tc-link { align-self: center; }

    /* ranger */
    #win-agentspace .tc-ranger { flex: 1; min-height: 0; display: flex; flex-direction: column; outline: none; }
    #win-agentspace .tc-ranger:focus-visible { box-shadow: inset 0 0 0 1px var(--tc-ink) !important; }
    #win-agentspace .tc-rg-title { display: flex; gap: 12px; padding: 7px 16px; font-size: 12.5px; border-bottom: 1px solid var(--tc-hair); white-space: nowrap; overflow: hidden; }
    #win-agentspace .tc-rg-title b { font-weight: 700; }
    #win-agentspace #tcRgTabs span { padding: 0 6px; margin-left: 2px; }
    #win-agentspace #tcRgTabs span[aria-current="true"] { background: var(--tc-ink) !important; color: var(--tc-paper) !important; }
    #win-agentspace .tc-rg-cols { flex: 1; min-height: 0; display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 3fr) minmax(0, 4fr); }
    #win-agentspace .tc-rg-col { margin: 0; padding: 4px 0; list-style: none; overflow: auto; min-width: 0; font-size: 12.5px; line-height: 1.6; }
    #win-agentspace .tc-rg-parent, #win-agentspace .tc-rg-cur { border-right: 1px solid var(--tc-hair); }
    #win-agentspace .tc-rg-col li { display: flex; gap: 8px; padding: 0 10px 0 12px; white-space: nowrap; cursor: default; user-select: none; }
    #win-agentspace .tc-rg-col li .n { flex: 1; overflow: hidden; text-overflow: ellipsis; }
    #win-agentspace .tc-rg-col li .s { color: var(--tc-ink-3) !important; font-size: 11.5px; }
    #win-agentspace .tc-rg-col li.d .n { font-weight: 700; }
    #win-agentspace .tc-rg-col li.on { background: var(--tc-ink) !important; color: var(--tc-paper) !important; }
    #win-agentspace .tc-rg-col li.on * { color: var(--tc-paper) !important; }
    #win-agentspace .tc-rg-parent li.on { background: var(--tc-ink-3) !important; }
    #win-agentspace .tc-rg-col li.mk .n::before { content: "+ "; font-weight: 700; }
    #win-agentspace .tc-rg-col li.cut .n { text-decoration: line-through; }
    #win-agentspace .tc-rg-col li.hit .n { text-decoration: underline; text-underline-offset: 3px; }
    #win-agentspace .tc-rg-empty { padding: 4px 12px; color: var(--tc-ink-3) !important; }
    #win-agentspace .tc-rg-preview { padding: 0; display: flex; flex-direction: column; }
    #win-agentspace .tc-rg-preview > .pv { padding: 6px 14px 10px; overflow: auto; flex: 1; min-height: 0; }
    #win-agentspace .tc-rg-preview pre { margin: 0; white-space: pre; font-size: 12px; line-height: 1.55; tab-size: 4; }
    #win-agentspace .tc-rg-preview pre .ln { color: var(--tc-ink-3) !important; user-select: none; display: inline-block; width: 4ch; text-align: right; margin-right: 1.5ch; }
    #win-agentspace .tc-rg-preview img, #win-agentspace .tc-rg-preview video, #win-agentspace .tc-rg-preview iframe, #win-agentspace .tc-rg-preview model-viewer {
      display: block; width: 100%; max-height: 100%; border: 1px solid var(--tc-hair) !important; background: #fff;
    }
    #win-agentspace .tc-rg-preview iframe, #win-agentspace .tc-rg-preview model-viewer { height: 100%; min-height: 320px; }
    #win-agentspace .tc-rg-preview audio { width: 100%; margin-top: 8px; }
    #win-agentspace .tc-rg-preview .tc-md { font-family: var(--tc-sans) !important; font-size: 14px; line-height: 1.55; }
    #win-agentspace .tc-rg-preview .tc-md * { font-family: inherit !important; }
    #win-agentspace .tc-rg-preview .tc-md h1, #win-agentspace .tc-rg-preview .tc-md h2, #win-agentspace .tc-rg-preview .tc-md h3 { text-transform: none !important; letter-spacing: -0.01em !important; font-weight: 600 !important; margin: 0.8em 0 0.3em; }
    #win-agentspace .tc-rg-preview .tc-md h1 { font-size: 22px !important; } #win-agentspace .tc-rg-preview .tc-md h2 { font-size: 18px !important; } #win-agentspace .tc-rg-preview .tc-md h3 { font-size: 15px !important; }
    #win-agentspace .tc-rg-preview .tc-md code, #win-agentspace .tc-rg-preview .tc-md pre { font-family: var(--tc-mono) !important; font-size: 12px; }
    #win-agentspace .tc-rg-preview .tc-md pre { background: var(--tc-paper-2) !important; padding: 8px; overflow: auto; }
    #win-agentspace .tc-rg-preview .tc-md ul { padding-left: 1.3em; list-style: disc; } #win-agentspace .tc-rg-preview .tc-md ol { padding-left: 1.3em; list-style: decimal; }
    #win-agentspace .tc-rg-preview .tc-md a { text-decoration: underline; }
    #win-agentspace .tc-rg-preview .pv-head { display: flex; gap: 8px; align-items: center; padding: 6px 14px; border-bottom: 1px solid var(--tc-hair); font-size: 11.5px; }
    #win-agentspace .tc-rg-preview .pv-head .tc-grow { flex: 1; }
    #win-agentspace .tc-rg-preview .pv-head button { border: 0 !important; padding: 0 6px !important; text-decoration: underline; text-underline-offset: 3px; }
    #win-agentspace .tc-rg-preview textarea.tc-rg-edit { flex: 1; resize: none; border: 0 !important; padding: 8px 14px !important; font-size: 12.5px !important; line-height: 1.55; white-space: pre; tab-size: 4; }
    #win-agentspace .tc-rg-preview .tc-keys { columns: 2; column-gap: 24px; font-size: 12px; }
    #win-agentspace .tc-rg-preview .tc-keys div { break-inside: avoid; display: flex; gap: 10px; }
    #win-agentspace .tc-rg-preview .tc-keys b { min-width: 8ch; }
    #win-agentspace .tc-rg-preview .tc-keys h4 { margin: 8px 0 2px !important; text-transform: uppercase; font-size: 11px !important; column-span: none; }
    #win-agentspace .tc-rg-console { display: flex; gap: 6px; align-items: center; padding: 6px 16px; border-top: 1px solid var(--tc-ink); font-size: 12.5px; }
    #win-agentspace .tc-rg-console input { flex: 1; border: 0 !important; padding: 0 !important; font-size: 12.5px !important; }
    #win-agentspace .tc-rg-drop { box-shadow: inset 0 0 0 2px var(--tc-ink) !important; }
    #win-agentspace .tc-status { font-size: 11.5px; gap: 16px; }
    #win-agentspace #tcRgStatL, #win-agentspace #tcRgStatR { white-space: pre; overflow: hidden; text-overflow: ellipsis; }

    /* extensions + artcraft */
    #win-agentspace .tc-space-pane { flex: 1; min-height: 0; overflow: auto; }
    #win-agentspace .tc-ext-search { display: flex; gap: 6px; padding: 12px 16px; }
    #win-agentspace .tc-ext-search input { flex: 1; padding: 6px 8px !important; }
    #win-agentspace .tc-ext-cols { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.4fr); border-top: 1px solid var(--tc-ink); }
    #win-agentspace .tc-ext-cols > div:first-child { border-right: 1px solid var(--tc-ink); }
    #win-agentspace .tc-ext-list { list-style: none; margin: 0; padding: 4px 0; }
    #win-agentspace .tc-ext-list li { display: grid; grid-template-columns: 28px minmax(0, 1fr) auto; gap: 4px 10px; padding: 8px 16px; border-bottom: 1px solid var(--tc-hair-2); align-items: start; }
    #win-agentspace .tc-ext-list img { width: 28px; height: 28px; object-fit: contain; filter: grayscale(1); }
    #win-agentspace .tc-ext-list .t { font-weight: 700; } #win-agentspace .tc-ext-list .i { font-size: 11px; color: var(--tc-ink-3) !important; }
    #win-agentspace .tc-ext-list .d { font-size: 11.5px; color: var(--tc-ink-2) !important; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
    #win-agentspace .tc-ext-list .cap { font-size: 11px; font-weight: 700; }
    #win-agentspace .tc-ext-note { padding: 10px 16px; font-size: 11.5px; line-height: 1.5; }
    #win-agentspace .tc-art-status { padding: 12px 16px 4px; font-size: 12px; line-height: 1.5; }
    #win-agentspace .tc-art-file { padding: 4px 16px 10px; font-size: 12px; }
    #win-agentspace .tc-art-apps { list-style: none; margin: 0; padding: 0; border-top: 1px solid var(--tc-ink); display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); }
    #win-agentspace .tc-art-apps li { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 2px 10px; padding: 9px 16px; border-bottom: 1px solid var(--tc-hair-2); border-right: 1px solid var(--tc-hair-2); font-size: 12px; }
    #win-agentspace .tc-art-apps li.fit { background: var(--tc-paper-2) !important; }
    #win-agentspace .tc-art-apps .x { grid-column: 1; font-size: 11px; color: var(--tc-ink-3) !important; }
    #win-agentspace .tc-art-apps .a { grid-column: 2; grid-row: 1 / span 2; display: flex; gap: 4px; align-items: center; }
    @media (max-width: 760px) {
      #win-agentspace .tc-rg-cols { grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr); }
      #win-agentspace .tc-rg-parent { display: none; }
      #win-agentspace .tc-ext-cols { grid-template-columns: 1fr; }
    }
  </style>
"""

SPACE_BODY = r"""
  <script id="tcSpaceScript">
  (function () {
    const $ = (id) => document.getElementById(id);
    const win = $('win-agentspace');
    if (!win || !$('tcRgCur')) return;
    const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    const store = {
      get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
      set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} },
    };
    const peer = () => (typeof myPeerId !== 'undefined' ? myPeerId : (localStorage.getItem('tincan_peer_id') || 'peer'));
    const handle = () => { try { return (localStorage.getItem('tincan_username') || '').replace(/^@/, '') || peer(); } catch (e) { return peer(); } };
    const size = (n) => (n == null ? '' : n < 1024 ? n + ' B' : n < 1048576 ? (n / 1024).toFixed(n < 10240 ? 1 : 0) + ' K' : (n / 1048576).toFixed(1) + ' M');
    const when = (t) => { if (!t) return ''; const d = new Date(t * 1000); return d.toISOString().slice(0, 10) + ' ' + d.toTimeString().slice(0, 5); };
    const extOf = (p) => { const m = /\.([^./]+)$/.exec(p || ''); return m ? m[1].toLowerCase() : ''; };
    const baseOf = (p) => p.split('/').pop();
    const dirOf = (p) => { const i = p.lastIndexOf('/'); return i <= 0 ? '/' : p.slice(0, i); };
    const join = (d, n) => (d === '/' ? '' : d) + '/' + n;
    const copyText = (t) => { try { navigator.clipboard.writeText(t); } catch (e) {} };
    function loadScript(src, attrs) {
      return new Promise((res, rej) => {
        if (document.querySelector(`script[src="${src}"]`)) return res();
        const s = document.createElement('script');
        s.src = src; Object.assign(s, attrs || {});
        s.onload = () => res(); s.onerror = () => rej(new Error('could not load ' + src));
        document.head.appendChild(s);
      });
    }

    // ---------------------------------------------------------------- VFS client
    let sp = { scope: 'user', owner: peer() };
    const qs = (s) => `scope=${encodeURIComponent(s.scope)}&owner_id=${encodeURIComponent(s.owner)}`;
    async function api(url, opts) {
      const r = await fetch(url, { ...(opts || {}), headers: { 'Content-Type': 'application/json' } });
      let d = {};
      try { d = await r.json(); } catch (e) {}
      if (!r.ok) throw new Error(d.error || ('HTTP ' + r.status));
      return d;
    }
    const vfs = {
      ls: (s) => api(`/api/space/ls?${qs(s)}`),
      read: (s, p) => api(`/api/space/file?${qs(s)}&path=${encodeURIComponent(p)}`),
      write: (s, p, content, b64) => api('/api/space/file', { method: 'POST', body: JSON.stringify({ scope: s.scope, owner_id: s.owner, path: p, content, is_base64: !!b64, updated_by: handle() }) }),
      del: (s, p) => api('/api/space/file', { method: 'POST', body: JSON.stringify({ scope: s.scope, owner_id: s.owner, path: p, action: 'delete', updated_by: handle() }) }),
      raw: (s, p, dl) => `/api/space/raw?${qs(s)}&path=${encodeURIComponent(p)}${dl ? '&download=1' : ''}`,
    };

    // ---------------------------------------------------------------- state
    let files = [];
    let index = new Map();            // dir -> [{name, dir, path, f, count}]
    let cwd = '/';
    const cursorMem = new Map();      // dir -> name under the cursor
    let marks = new Set();            // full paths in this space
    let buffer = null;                // { mode: 'copy'|'cut', sp, items: [{path, dir}] }
    let showHidden = false;
    let sortBy = store.get('tc_rg_sort', { key: 'natural', rev: false });
    let filterText = '';
    let searchRe = null;
    let back = [], fwd = [], prevDir = '/';
    let tabs = [{ cwd: '/' }], tabIdx = 0;
    let editing = null;               // { path, clean }
    let output = null;                // { title, text, err } shown in the preview until the cursor moves
    let message = '';
    let recs = [];                    // .vscode/extensions.json recommendations
    let caps = { format: false, markdown: false, gltf: false, python: false };
    let bookmarks = {};
    const spaceKey = () => `${sp.scope}:${sp.owner}`;

    function buildIndex() {
      index = new Map([['/', []]]);
      const ensureDir = (d) => {
        if (index.has(d)) return;
        index.set(d, []);
        const parent = dirOf(d);
        ensureDir(parent);
        index.get(parent).push({ name: baseOf(d), dir: true, path: d });
      };
      files.forEach((f) => { const d = dirOf(f.path); ensureDir(d); index.get(d).push({ name: baseOf(f.path), dir: false, path: f.path, f }); });
      index.forEach((list) => list.forEach((e) => { if (e.dir) e.count = (index.get(e.path) || []).filter((c) => !c.name.startsWith('.')).length; }));
    }
    const isDir = (p) => index.has(p);
    const isFile = (p) => files.some((f) => f.path === p);
    const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: 'base' });
    function entries(dir, opts) {
      let list = (index.get(dir) || []).slice();
      if (!showHidden) list = list.filter((e) => !e.name.startsWith('.'));
      if (opts && opts.filter && filterText) list = list.filter((e) => e.name.toLowerCase().includes(filterText.toLowerCase()));
      const k = sortBy.key;
      const val = (e) => k === 'size' ? (e.dir ? e.count : e.f.size_bytes) : k === 'mtime' ? (e.f ? e.f.updated_at : 0) : k === 'type' ? (e.f ? e.f.mime_type : '') : k === 'ext' ? extOf(e.name) : e.name;
      list.sort((a, b) => {
        if (a.dir !== b.dir) return a.dir ? -1 : 1;
        const va = val(a), vb = val(b);
        const c = typeof va === 'number' ? va - vb : (k === 'basename' ? String(va).localeCompare(String(vb)) : collator.compare(String(va), String(vb)));
        return (k === 'size' || k === 'mtime' ? -c : c) || collator.compare(a.name, b.name);
      });
      if (sortBy.rev) list.reverse();
      return list;
    }
    function here() {
      const es = entries(cwd, { filter: true });
      let i = es.findIndex((e) => e.name === cursorMem.get(cwd));
      if (i < 0) i = 0;
      return { es, i, e: es[i] || null };
    }
    function setIdx(i) {
      const { es } = here();
      if (!es.length) return;
      i = Math.max(0, Math.min(es.length - 1, i));
      cursorMem.set(cwd, es[i].name);
      output = null;
      render();
    }
    function cd(dir, opts) {
      if (!isDir(dir)) { flash(`cd: ${dir}: no such directory`); return; }
      if (dir === cwd) return;
      if (!(opts && opts.noHistory)) { back.push(cwd); fwd = []; }
      prevDir = cwd;
      const from = cwd;
      cwd = dir;
      filterText = '';
      if (dir === dirOf(from) && !cursorMem.has(dir)) cursorMem.set(dir, baseOf(from));
      if (opts && opts.select) cursorMem.set(cwd, opts.select);
      tabs[tabIdx].cwd = cwd;
      editing = null; output = null;
      render();
    }
    function targets() {
      if (marks.size) return [...marks].map((p) => ({ path: p, dir: isDir(p) }));
      const { e } = here();
      return e ? [{ path: e.path, dir: e.dir }] : [];
    }
    function flash(text) { message = text; renderStatus(); clearTimeout(flash.t); flash.t = setTimeout(() => { message = ''; renderStatus(); }, 4000); }

    // ---------------------------------------------------------------- loading
    async function reload(keepCursor) {
      try {
        const d = await vfs.ls(sp);
        files = (d.files || []).slice();
        buildIndex();
        if (!isDir(cwd)) cwd = '/';
        marks = new Set([...marks].filter((p) => isFile(p) || isDir(p)));
        await loadRecs();
        render();
        $('tcRgStatR') && renderStatus();
      } catch (e) { flash('could not load space: ' + e.message); }
    }
    async function loadRecs() {
      recs = [];
      if (isFile('/.vscode/extensions.json')) {
        try { const r = await vfs.read(sp, '/.vscode/extensions.json'); recs = (JSON.parse(r.content || '{}').recommendations || []).filter((x) => typeof x === 'string'); } catch (e) {}
      }
      caps = {
        format: recs.some((id) => /prettier/i.test(id)),
        markdown: recs.some((id) => /markdown/i.test(id)),
        gltf: recs.some((id) => /gl(b|tf)|3d-model|model-viewer/i.test(id)),
        python: recs.some((id) => /^ms-python\.python$/i.test(id)),
      };
    }

    // ---------------------------------------------------------------- rendering
    function rowHtml(e, on, extraCls) {
      const cls = [e.dir ? 'd' : 'f', on ? 'on' : '', marks.has(e.path) ? 'mk' : '', buffer && buffer.mode === 'cut' && buffer.sp.scope === sp.scope && buffer.sp.owner === sp.owner && buffer.items.some((it) => it.path === e.path) ? 'cut' : '', searchRe && searchRe.test(e.name) ? 'hit' : '', extraCls || ''].filter(Boolean).join(' ');
      const sz = e.dir ? String(e.count) : size(e.f.size_bytes);
      return `<li class="${cls}" data-path="${esc(e.path)}" role="option" aria-selected="${on}"><span class="n">${esc(e.name)}${e.dir ? '/' : ''}</span><span class="s">${sz}</span></li>`;
    }
    function render() {
      const { es, i, e } = here();
      const tabTitle = $('tcRgTitle');
      tabTitle.innerHTML = `${esc(handle())}@${esc(sp.scope === 'user' ? 'space' : sp.owner)}:${esc(cwd === '/' ? '/' : cwd + '/')}<b>${e ? esc(e.name) : ''}</b>${filterText ? `  <span class="tc-dim">filter: ${esc(filterText)}</span>` : ''}`;
      $('tcRgTabs').innerHTML = tabs.length > 1 ? tabs.map((t, k) => `<span${k === tabIdx ? ' aria-current="true"' : ''}>${k + 1}</span>`).join('') : '';
      // parent column
      const par = $('tcRgParent');
      if (cwd === '/') par.innerHTML = `<li class="d on"><span class="n">/</span></li>`;
      else par.innerHTML = entries(dirOf(cwd)).map((pe) => rowHtml(pe, pe.path === cwd)).join('');
      // current column
      const curEl = $('tcRgCur');
      curEl.innerHTML = es.length ? es.map((ce, k) => rowHtml(ce, k === i)).join('') : `<li class="tc-rg-empty">${filterText ? 'no match' : 'empty'}</li>`;
      const onEl = curEl.querySelector('li.on');
      if (onEl) onEl.scrollIntoView({ block: 'nearest' });
      const pOn = par.querySelector('li.on'); if (pOn) pOn.scrollIntoView({ block: 'nearest' });
      renderPreview(e);
      renderStatus();
      if (window.tcSetWindowPath) window.tcSetWindowPath('win-agentspace', (sp.scope === 'user' ? '~/space' : '~/' + sp.scope + '/' + sp.owner) + (cwd === '/' ? '' : cwd));
      if ($('tcSpaceArt') && !$('tcSpaceArt').hidden) renderArt();
    }
    function renderStatus() {
      const { es, i, e } = here();
      let left = message;
      if (!left) {
        if (marks.size) {
          const total = [...marks].reduce((n, p) => n + ((files.find((f) => f.path === p) || {}).size_bytes || 0), 0);
          left = `Mrk: ${marks.size} item${marks.size === 1 ? '' : 's'}, ${size(total)}`;
        } else if (e && e.dir) left = `drwxr-xr-x  ${e.count} item${e.count === 1 ? '' : 's'}  ${e.name}/`;
        else if (e) left = `-rw-r--r--  ${e.f.updated_by || '-'}  ${size(e.f.size_bytes)}  ${when(e.f.updated_at)}  ${e.f.mime_type || ''}`;
        else left = 'empty';
      }
      const parts = [];
      if (buffer) parts.push(`${buffer.mode === 'cut' ? 'Cut' : 'Copy'}: ${buffer.items.length}`);
      if (sortBy.key !== 'natural' || sortBy.rev) parts.push(`sort: ${sortBy.key}${sortBy.rev ? ' rev' : ''}`);
      if (showHidden) parts.push('hidden: shown');
      parts.push(es.length ? `${i + 1}/${es.length}` : '0/0');
      parts.push(es.length <= 1 ? 'All' : i === 0 ? 'Top' : i === es.length - 1 ? 'Bot' : Math.round((i / (es.length - 1)) * 100) + '%');
      $('tcRgStatL').textContent = left;
      $('tcRgStatR').textContent = parts.join('   ');
    }

    let previewToken = 0;
    const TEXT_EXT = /^(txt|md|markdown|py|js|mjs|cjs|jsx|ts|tsx|json|html|htm|css|scss|less|sh|rs|go|java|c|h|cpp|toml|yaml|yml|xml|svg|csv|ini|cfg|env|sql|rb|php|swift|kt|fountain|dxf|obj|gltf|log|space-notes)$/;
    async function renderPreview(e) {
      const pv = $('tcRgPreview');
      const token = ++previewToken;
      if (output) {
        pv.innerHTML = `<div class="pv-head"><b>${esc(output.title)}</b><span class="tc-grow"></span><button type="button" data-pv="close">close esc</button></div>` +
          (output.html ? `<div class="pv tc-keys">${output.html}</div>` : `<div class="pv"><pre>${esc(output.text)}</pre></div>`);
        return;
      }
      if (!e) { pv.innerHTML = ''; return; }
      if (e.dir) {
        const kids = entries(e.path);
        pv.innerHTML = `<ol class="tc-rg-col" style="padding:4px 0">${kids.length ? kids.map((k) => rowHtml(k, false)).join('') : '<li class="tc-rg-empty">empty</li>'}</ol>`;
        return;
      }
      if (editing && editing.path === e.path) {
        pv.innerHTML = `<div class="pv-head"><b>editing</b><span class="tc-dim" id="tcRgEdState">saved</span><span class="tc-grow"></span><button type="button" data-pv="save">save ⌘S</button>${runnable(e.path) ? '<button type="button" data-pv="run">run ⌘↵</button>' : ''}${caps.format && parserFor(e.path) ? '<button type="button" data-pv="format">format</button>' : ''}<button type="button" data-pv="close">close esc</button></div><textarea class="tc-rg-edit" id="tcRgEdit" spellcheck="false" aria-label="Edit ${esc(e.name)}"></textarea>`;
        const ta = $('tcRgEdit');
        ta.value = editing.value != null ? editing.value : editing.clean;
        ta.addEventListener('input', () => { editing.value = ta.value; const st = $('tcRgEdState'); if (st) st.textContent = ta.value === editing.clean ? 'saved' : 'modified'; });
        ta.addEventListener('keydown', editorKeys);
        setTimeout(() => ta.focus(), 0);
        return;
      }
      const f = e.f, ext = extOf(e.name), mime = f.mime_type || '';
      const head = (extra) => `<div class="pv-head"><span class="tc-dim">${esc(mime || ext)} · ${size(f.size_bytes)}</span><span class="tc-grow"></span>${extra || ''}<a class="tc-link" href="${vfs.raw(sp, e.path, true)}" download>download</a></div>`;
      const raw = vfs.raw(sp, e.path);
      if (/^image\//.test(mime) || /^(png|jpe?g|gif|webp|svg|avif|bmp)$/.test(ext)) { pv.innerHTML = head() + `<div class="pv"><img src="${raw}" alt="${esc(e.name)}"></div>`; return; }
      if (/^video\//.test(mime) || /^(mp4|webm|mov|m4v)$/.test(ext)) { pv.innerHTML = head() + `<div class="pv"><video src="${raw}" controls preload="metadata"></video></div>`; return; }
      if (/^audio\//.test(mime) || /^(mp3|wav|ogg|m4a|flac)$/.test(ext)) { pv.innerHTML = head() + `<div class="pv"><audio src="${raw}" controls preload="metadata"></audio></div>`; return; }
      if (ext === 'pdf') { pv.innerHTML = head() + `<div class="pv"><iframe src="${raw}" title="${esc(e.name)}"></iframe></div>`; return; }
      if (ext === 'glb' || ext === 'gltf') {
        if (!caps.gltf) { pv.innerHTML = head() + `<div class="pv tc-dim">3D model. Add a glTF/GLB viewer in <b>extensions</b> to preview it here, or open it in ArtCraft.</div>`; return; }
        pv.innerHTML = head() + `<div class="pv"><span class="tc-dim">loading viewer…</span></div>`;
        try { await loadScript('https://unpkg.com/@google/model-viewer@3.5.0/dist/model-viewer.min.js', { type: 'module' }); } catch (err) {}
        if (token !== previewToken) return;
        pv.innerHTML = head() + `<div class="pv"><model-viewer src="${raw}" camera-controls auto-rotate shadow-intensity="0.6" alt="${esc(e.name)}"></model-viewer></div>`;
        return;
      }
      if (!TEXT_EXT.test(ext) && !/^text\/|json|javascript|xml/.test(mime) || f.size_bytes > 1048576) {
        pv.innerHTML = head() + `<div class="pv tc-dim">binary · not previewed</div>`;
        return;
      }
      pv.innerHTML = head() + `<div class="pv tc-dim">…</div>`;
      let rec;
      try { rec = await vfs.read(sp, e.path); } catch (err) { if (token === previewToken) pv.innerHTML = head() + `<div class="pv">${esc(err.message)}</div>`; return; }
      if (token !== previewToken) return;
      if (rec.content == null) { pv.innerHTML = head() + `<div class="pv tc-dim">binary · not previewed</div>`; return; }
      const editBtn = '<button type="button" data-pv="edit" class="tc-link" style="border:0;padding:0 6px">edit E</button>';
      if ((ext === 'md' || ext === 'markdown') && caps.markdown) {
        try {
          await loadScript('https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.2/marked.min.js');
          await loadScript('https://cdnjs.cloudflare.com/ajax/libs/dompurify/3.1.6/purify.min.js');
          if (token !== previewToken) return;
          pv.innerHTML = head(editBtn) + `<div class="pv tc-md">${window.DOMPurify.sanitize(window.marked.parse(rec.content))}</div>`;
          return;
        } catch (err) {}
      }
      const lines = rec.content.split('\n');
      const shown = lines.slice(0, 600).map((l, k) => `<span class="ln">${k + 1}</span>${esc(l)}`).join('\n');
      pv.innerHTML = head(editBtn) + `<div class="pv"><pre>${shown}${lines.length > 600 ? `\n<span class="tc-dim">… ${lines.length - 600} more lines</span>` : ''}</pre></div>`;
    }

    // ---------------------------------------------------------------- editor
    const runnable = (p) => /\.(py|js|mjs)$/.test(p);
    async function edit(path) {
      try {
        const rec = await vfs.read(sp, path);
        if (rec.content == null) { flash(`${baseOf(path)} is binary`); return; }
        cd(dirOf(path), { select: baseOf(path) });
        cursorMem.set(dirOf(path), baseOf(path));
        editing = { path, clean: rec.content, value: null };
        output = null;
        render();
      } catch (err) { flash(err.message); }
    }
    async function saveEdit() {
      if (!editing) return;
      const v = editing.value != null ? editing.value : editing.clean;
      try { await vfs.write(sp, editing.path, v); editing.clean = v; editing.value = null; const st = $('tcRgEdState'); if (st) st.textContent = 'saved'; flash(`wrote ${editing.path}`); await reload(); }
      catch (err) { flash('save failed: ' + err.message); }
    }
    function closeEdit() {
      if (editing && editing.value != null && editing.value !== editing.clean && !confirmInline('discard changes?')) return;
      editing = null; render(); $('tcSpaceFiles').focus();
    }
    function editorKeys(ev) {
      const mod = ev.metaKey || ev.ctrlKey;
      if (mod && ev.key.toLowerCase() === 's') { ev.preventDefault(); saveEdit(); }
      else if (mod && ev.key === 'Enter') { ev.preventDefault(); saveEdit().then(() => run(editing ? editing.path : null)); }
      else if (ev.key === 'Escape') { ev.preventDefault(); closeEdit(); }
      else if (ev.key === 'Tab') { ev.preventDefault(); const t = ev.target, s = t.selectionStart; t.setRangeText('    ', s, t.selectionEnd, 'end'); t.dispatchEvent(new Event('input')); }
      ev.stopPropagation();
    }
    // A plain synchronous confirm is a browser dialog; keep it to the rare "discard edits" case.
    function confirmInline(q) { return window.confirm(q); }

    // ---------------------------------------------------------------- file operations
    function freeName(dir, name, overwrite) {
      if (overwrite) return join(dir, name);
      let n = name;
      while (isFile(join(dir, n)) || isDir(join(dir, n))) n += '_';
      return join(dir, n);
    }
    async function listOf(s, path, dir) {
      if (!dir) return [path];
      const all = (s.scope === sp.scope && s.owner === sp.owner) ? files : ((await vfs.ls(s)).files || []);
      return all.map((f) => f.path).filter((p) => p.startsWith(path + '/'));
    }
    async function copyItem(srcSp, item, destPath) {
      const paths = await listOf(srcSp, item.path, item.dir);
      for (const p of paths) {
        const rec = await vfs.read(srcSp, p);
        const target = item.dir ? destPath + p.slice(item.path.length) : destPath;
        await vfs.write(sp, target, rec.content_b64 || '', true);
      }
    }
    async function removeItem(s, item) {
      const paths = await listOf(s, item.path, item.dir);
      for (const p of paths) await vfs.del(s, p);
    }
    async function paste(overwrite) {
      if (!buffer || !buffer.items.length) { flash('nothing to paste: yy copies, dd cuts'); return; }
      const n = buffer.items.length;
      flash(`${buffer.mode === 'cut' ? 'moving' : 'copying'} ${n} item${n === 1 ? '' : 's'}…`);
      try {
        for (const item of buffer.items) {
          const dest = freeName(cwd, baseOf(item.path), overwrite);
          if (item.dir && (cwd + '/').startsWith(item.path + '/') && buffer.sp.owner === sp.owner && buffer.sp.scope === sp.scope) { flash('cannot paste a folder into itself'); return; }
          await copyItem(buffer.sp, item, dest);
          if (buffer.mode === 'cut') await removeItem(buffer.sp, item);
        }
        if (buffer.mode === 'cut') buffer = null;
        marks.clear();
        await reload();
        flash(`pasted ${n} item${n === 1 ? '' : 's'}`);
      } catch (err) { flash('paste failed: ' + err.message); await reload(); }
    }
    async function remove(items) {
      for (const it of items) await removeItem(sp, it);
      marks.clear();
      await reload();
      flash(`deleted ${items.length} item${items.length === 1 ? '' : 's'}`);
    }
    async function rename(newName) {
      const { e } = here();
      if (!e || !newName || newName === e.name) return;
      if (/[\/]/.test(newName)) { flash('use :mkdir and pp to move between folders'); return; }
      const dest = join(cwd, newName);
      if (isFile(dest) || isDir(dest)) { flash(`${newName} already exists`); return; }
      const keep = buffer; buffer = null;
      await copyItem(sp, { path: e.path, dir: e.dir }, dest);
      await removeItem(sp, { path: e.path, dir: e.dir });
      buffer = keep;
      cursorMem.set(cwd, newName);
      await reload();
      flash(`renamed to ${newName}`);
    }
    async function mkdir(name) {
      const p = name.startsWith('/') ? name : join(cwd, name);
      await vfs.write(sp, p.replace(/\/$/, '') + '/.keep', '');
      await reload();
      cursorMem.set(cwd, baseOf(p));
      render();
    }
    async function touch(name) {
      const p = name.startsWith('/') ? name : join(cwd, name);
      if (!isFile(p)) await vfs.write(sp, p, '');
      await reload();
      cd(dirOf(p), { select: baseOf(p) });
      cursorMem.set(dirOf(p), baseOf(p));
      render();
      return p;
    }
    async function run(path) {
      const { e } = here();
      const p = path || (e && !e.dir ? e.path : null);
      if (!p || !runnable(p)) { flash('r runs .py and .js files'); return; }
      output = { title: `run ${p}`, text: 'running…' };
      renderPreview(here().e);
      try {
        const d = await api('/api/space/exec', { method: 'POST', body: JSON.stringify({ scope: sp.scope, owner_id: sp.owner, entrypoint: p, runtime: 'auto' }) });
        output = { title: `run ${p} · exit ${d.exit_code} · ${Math.round(d.duration_ms || 0)} ms`, text: (d.stdout || '') + (d.stderr ? '\n' + d.stderr : '') || '(no output)' };
      } catch (err) { output = { title: `run ${p}`, text: err.message }; }
      editing = null;
      renderPreview(here().e);
    }
    const PARSERS = { js: 'babel', mjs: 'babel', cjs: 'babel', jsx: 'babel', ts: 'typescript', tsx: 'typescript', json: 'json', css: 'css', scss: 'scss', less: 'less', html: 'html', htm: 'html', md: 'markdown', markdown: 'markdown', yaml: 'yaml', yml: 'yaml' };
    const parserFor = (p) => PARSERS[extOf(p)];
    async function format() {
      const { e } = here();
      const p = editing ? editing.path : e && !e.dir ? e.path : null;
      if (!p) return;
      if (!caps.format) { flash('add Prettier in extensions to format files'); return; }
      const parser = parserFor(p);
      if (!parser) { flash(`prettier has no parser for .${extOf(p)}`); return; }
      try {
        const base = 'https://unpkg.com/prettier@3.3.3/';
        await loadScript(base + 'standalone.js');
        for (const pl of ['babel', 'estree', 'typescript', 'postcss', 'html', 'markdown', 'yaml']) await loadScript(`${base}plugins/${pl}.js`);
        const src = editing && editing.path === p ? (editing.value != null ? editing.value : editing.clean) : (await vfs.read(sp, p)).content;
        const out = await window.prettier.format(src, { parser, plugins: Object.values(window.prettierPlugins || {}) });
        if (editing && editing.path === p) { editing.value = out; render(); flash('formatted (not saved yet)'); }
        else { await vfs.write(sp, p, out); await reload(); flash(`formatted ${baseOf(p)}`); }
      } catch (err) { flash('format failed: ' + err.message.split('\n')[0]); }
    }
    async function upload(fileList) {
      const list = [...fileList];
      for (const file of list) {
        if (file.size > 25 * 1048576) { flash(`${file.name} is over 25 MB`); continue; }
        const b64 = await new Promise((res, rej) => { const r = new FileReader(); r.onload = () => res(String(r.result).split(',')[1] || ''); r.onerror = rej; r.readAsDataURL(file); });
        await vfs.write(sp, freeName(cwd, file.name), b64, true);
      }
      await reload();
      flash(`uploaded ${list.length} file${list.length === 1 ? '' : 's'} to ${cwd}`);
    }

    // ---------------------------------------------------------------- console
    let consoleMode = null;   // null | 'cmd' | 'search' | 'find' | 'confirm'
    let confirmAction = null;
    let consoleHist = store.get('tc_rg_console_hist', []);
    let chIdx = consoleHist.length;
    function openConsole(prefill, mode, caret) {
      consoleMode = mode || 'cmd';
      const row = $('tcRgConsoleRow'), inp = $('tcRgConsole');
      $('tcRgConsolePrompt').textContent = consoleMode === 'search' ? '/' : consoleMode === 'find' ? 'find:' : consoleMode === 'confirm' ? '' : ':';
      row.hidden = false;
      inp.value = prefill || '';
      inp.readOnly = consoleMode === 'confirm';
      setTimeout(() => { inp.focus(); const c = caret == null ? inp.value.length : caret; inp.setSelectionRange(c, c); }, 0);
      chIdx = consoleHist.length;
    }
    function closeConsole() { consoleMode = null; confirmAction = null; $('tcRgConsoleRow').hidden = true; $('tcSpaceFiles').focus(); }
    function ask(question, action) { confirmAction = action; openConsole(question + '  (y/N)', 'confirm'); }
    $('tcRgConsole').addEventListener('keydown', (ev) => {
      ev.stopPropagation();
      const inp = ev.target;
      if (consoleMode === 'confirm') {
        ev.preventDefault();
        const act = confirmAction;
        closeConsole();
        if (ev.key.toLowerCase() === 'y' && act) act();
        else flash('cancelled');
        return;
      }
      if (ev.key === 'Escape') { ev.preventDefault(); if (consoleMode === 'find') { filterText = ''; } closeConsole(); render(); return; }
      if (consoleMode === 'cmd' && (ev.key === 'ArrowUp' || ev.key === 'ArrowDown')) {
        ev.preventDefault();
        chIdx = Math.max(0, Math.min(consoleHist.length, chIdx + (ev.key === 'ArrowUp' ? -1 : 1)));
        inp.value = consoleHist[chIdx] || '';
        return;
      }
      if (consoleMode === 'cmd' && ev.key === 'Tab') {
        ev.preventDefault();
        const parts = inp.value.split(' ');
        if (parts.length === 1) { const m = Object.keys(COMMANDS).filter((c) => c.startsWith(parts[0])); if (m.length === 1) inp.value = m[0] + ' '; else if (m.length) flash(m.join('  ')); }
        else { const pre = parts[parts.length - 1]; const m = entries(cwd).filter((x) => x.name.startsWith(pre)); if (m.length === 1) { parts[parts.length - 1] = m[0].name; inp.value = parts.join(' '); } else if (m.length) flash(m.map((x) => x.name).join('  ')); }
      }
    });
    $('tcRgConsole').addEventListener('input', (ev) => {
      if (consoleMode === 'find') {
        // find-as-you-type: narrow and jump; a single match opens
        const q = ev.target.value.toLowerCase();
        const es = entries(cwd);
        const m = es.filter((x) => x.name.toLowerCase().includes(q));
        if (m.length) cursorMem.set(cwd, m[0].name);
        render();
        if (q && m.length === 1) { closeConsole(); open(m[0]); }
      } else if (consoleMode === 'search') {
        try { searchRe = ev.target.value ? new RegExp(ev.target.value, 'i') : null; } catch (e) { searchRe = null; }
        render();
      }
    });
    $('tcRgConsoleRow').addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const v = $('tcRgConsole').value;
      const mode = consoleMode;
      closeConsole();
      if (mode === 'search') { searchJump(1, true); return; }
      if (mode === 'find') return;
      if (v.trim()) { consoleHist.push(v); consoleHist = consoleHist.slice(-100); store.set('tc_rg_console_hist', consoleHist); }
      await command(v);
    });
    function searchJump(dir, fromCurrent) {
      if (!searchRe) return;
      const { es, i } = here();
      for (let k = fromCurrent ? 0 : 1; k <= es.length; k++) {
        const j = (i + dir * k + es.length * 2) % es.length;
        if (searchRe.test(es[j].name)) { setIdx(j); return; }
      }
      flash('no match');
    }

    const COMMANDS = {
      cd: 'cd <dir>', mkdir: 'mkdir <name>', touch: 'touch <name>', rename: 'rename <new name>', delete: 'delete marked or current',
      edit: 'edit [file]', run: 'run [file]', format: 'format current file (Prettier)', filter: 'filter <text>', search: 'search <regex>',
      find: 'find <text>', agent: 'agent <what to change>', upload: 'upload files here', export: 'download .space', zip: 'download as folder for VS Code',
      gen3d: 'gen3d <prompt>', open: 'open current in ArtCraft tab', mark: 'mark <regex>', unmark: 'unmark all', sort: 'sort natural|size|mtime|type|ext|basename', help: 'keys and commands',
    };
    async function command(line) {
      const m = /^\s*(\S+)\s*(.*)$/.exec(line || '');
      if (!m) return;
      const [, name, arg] = m;
      const a = arg.trim();
      try {
        switch (name) {
          case 'cd': { const p = !a ? '/' : a === '-' ? prevDir : a.startsWith('/') ? a.replace(/\/$/, '') || '/' : normalize(join(cwd, a)); cd(p); return; }
          case 'mkdir': if (!a) return flash('usage: :mkdir <name>'); await mkdir(a); flash(`created ${a}/`); return;
          case 'touch': if (!a) return flash('usage: :touch <name>'); await touch(a); flash(`created ${a}`); return;
          case 'rename': if (!a) return flash('usage: :rename <new name>'); await rename(a); return;
          case 'delete': { const t = targets(); if (!t.length) return; ask(`delete ${t.length === 1 ? baseOf(t[0].path) + (t[0].dir ? '/ and everything in it' : '') : t.length + ' items'}?`, () => remove(t)); return; }
          case 'edit': { if (a) { const p = a.startsWith('/') ? a : join(cwd, a); if (!isFile(p)) await touch(p); return edit(p); } const { e } = here(); if (e && !e.dir) edit(e.path); return; }
          case 'run': return run(a ? (a.startsWith('/') ? a : join(cwd, a)) : null);
          case 'format': return format();
          case 'filter': filterText = a; render(); return;
          case 'search': try { searchRe = a ? new RegExp(a, 'i') : null; } catch (e) { return flash('bad pattern'); } searchJump(1, true); render(); return;
          case 'find': { const hit = entries(cwd).find((x) => x.name.toLowerCase().includes(a.toLowerCase())); if (hit) { cursorMem.set(cwd, hit.name); render(); } else flash('no match'); return; }
          case 'mark': { let re; try { re = new RegExp(a || '.', 'i'); } catch (e) { return flash('bad pattern'); } entries(cwd).forEach((x) => { if (re.test(x.name)) marks.add(x.path); }); render(); return; }
          case 'unmark': marks.clear(); render(); return;
          case 'sort': if (!a) return flash(COMMANDS.sort); sortBy = { key: a, rev: false }; store.set('tc_rg_sort', sortBy); render(); return;
          case 'agent': {
            if (!a) return flash('usage: :agent <what to change in this space>');
            output = { title: 'agent', text: 'working…' }; renderPreview(here().e);
            const d = await api('/api/space/agent', { method: 'POST', body: JSON.stringify({ scope: sp.scope, owner_id: sp.owner, prompt: a, author: handle() }) });
            output = { title: 'agent', text: d.summary || d.reply || d.message || JSON.stringify(d, null, 2) };
            await reload();
            return;
          }
          case 'gen3d': return gen3d(a);
          case 'upload': $('tcSpaceUpload').click(); return;
          case 'export': return exportSpace();
          case 'zip': return zipSpace();
          case 'open': showTab('art'); return;
          case 'help': showKeys(); return;
          case 'q': case 'quit': if (typeof minimizeWindow === 'function') minimizeWindow('win-agentspace'); return;
          default: flash(`${name}: unknown command (Tab completes, :help lists)`);
        }
      } catch (err) { flash(`${name}: ${err.message}`); }
    }
    function normalize(p) {
      const out = [];
      p.split('/').forEach((s) => { if (!s || s === '.') return; if (s === '..') out.pop(); else out.push(s); });
      return '/' + out.join('/');
    }

    // ---------------------------------------------------------------- keys
    function open(e) {
      if (!e) return;
      if (e.dir) { cd(e.path); return; }
      const ext = extOf(e.name);
      if (TEXT_EXT.test(ext) && ext !== 'svg') edit(e.path);
      else { const media = $('tcRgPreview').querySelector('video, audio'); if (media) media.play().catch(() => {}); }
    }
    let seq = '';
    let count = '';
    let seqTimer = null;
    const pageSize = () => Math.max(3, Math.floor(($('tcRgCur').clientHeight || 300) / 20));
    const SEQ = {
      j: (n) => setIdx(here().i + n), k: (n) => setIdx(here().i - n), ArrowDown: (n) => setIdx(here().i + n), ArrowUp: (n) => setIdx(here().i - n),
      h: () => cwd !== '/' && cd(dirOf(cwd)), ArrowLeft: () => cwd !== '/' && cd(dirOf(cwd)),
      l: () => open(here().e), ArrowRight: () => open(here().e), Enter: () => open(here().e),
      gg: (n) => setIdx(count ? n - 1 : 0), G: (n) => setIdx(count ? n - 1 : 1e9), Home: () => setIdx(0), End: () => setIdx(1e9),
      J: () => setIdx(here().i + Math.floor(pageSize() / 2)), K: () => setIdx(here().i - Math.floor(pageSize() / 2)),
      'C-d': () => setIdx(here().i + Math.floor(pageSize() / 2)), 'C-u': () => setIdx(here().i - Math.floor(pageSize() / 2)),
      'C-f': () => setIdx(here().i + pageSize()), 'C-b': () => setIdx(here().i - pageSize()), PageDown: () => setIdx(here().i + pageSize()), PageUp: () => setIdx(here().i - pageSize()),
      H: () => { if (back.length) { fwd.push(cwd); cd(back.pop(), { noHistory: true }); } }, L: () => { if (fwd.length) { back.push(cwd); cd(fwd.pop(), { noHistory: true }); } },
      '[': () => sibling(-1), ']': () => sibling(1),
      ' ': () => { const { e, i } = here(); if (e) { marks.has(e.path) ? marks.delete(e.path) : marks.add(e.path); setIdx(i + 1); render(); } },
      v: () => { entries(cwd).forEach((x) => (marks.has(x.path) ? marks.delete(x.path) : marks.add(x.path))); render(); },
      uv: () => { marks.clear(); render(); },
      yy: () => { const t = targets(); if (t.length) { buffer = { mode: 'copy', sp: { ...sp }, items: t }; flash(`copied ${t.length} — pp to paste`); render(); } },
      dd: () => { const t = targets(); if (t.length) { buffer = { mode: 'cut', sp: { ...sp }, items: t }; flash(`cut ${t.length} — pp to move here`); render(); } },
      pp: () => paste(false), po: () => paste(true),
      dD: () => command('delete'),
      yp: () => { const { e } = here(); if (e) { copyText(e.path); flash('copied path ' + e.path); } },
      yn: () => { const { e } = here(); if (e) { copyText(e.name); flash('copied name'); } },
      yd: () => { copyText(cwd); flash('copied ' + cwd); },
      cw: () => { const { e } = here(); if (e) openConsole('rename ' + e.name); },
      a: () => { const { e } = here(); if (e) { const dot = e.dir ? -1 : e.name.lastIndexOf('.'); openConsole('rename ' + e.name, 'cmd', 7 + (dot > 0 ? dot : e.name.length)); } },
      A: () => { const { e } = here(); if (e) openConsole('rename ' + e.name); },
      I: () => { const { e } = here(); if (e) openConsole('rename ' + e.name, 'cmd', 7); },
      ':': () => openConsole(''), ';': () => openConsole(''),
      '/': () => openConsole('', 'search'), n: () => searchJump(1), N: () => searchJump(-1),
      f: () => openConsole('', 'find'), zf: () => openConsole('filter ' + filterText),
      zh: () => { showHidden = !showHidden; render(); }, Backspace: () => { showHidden = !showHidden; render(); },
      os: () => sortKey('size'), on: () => sortKey('natural'), ob: () => sortKey('basename'), om: () => sortKey('mtime'), ot: () => sortKey('type'), oe: () => sortKey('ext'), or: () => { sortBy.rev = !sortBy.rev; store.set('tc_rg_sort', sortBy); render(); },
      oS: () => sortKey('size', true), oN: () => sortKey('natural', true), oB: () => sortKey('basename', true), oM: () => sortKey('mtime', true), oT: () => sortKey('type', true), oE: () => sortKey('ext', true),
      E: () => { const { e } = here(); if (e && !e.dir) edit(e.path); },
      r: () => run(), '=': () => format(), R: () => reload().then(() => flash('reloaded')),
      gh: () => cd('/'), 'g/': () => cd('/'), gr: () => cd('/'), gs: () => go('/src'), gd: () => go('/docs'), gn: () => newTab(), gt: () => switchTab(1), gT: () => switchTab(-1), gc: () => closeTab(),
      gm: () => go('/models3d'), ga: () => go('/artcraft'), gN: () => go('/notes'),
      Tab: () => switchTab(1), 'S-Tab': () => switchTab(-1), 'C-n': () => newTab(), 'C-w': () => closeTab(),
      q: () => (tabs.length > 1 ? closeTab() : typeof minimizeWindow === 'function' && minimizeWindow('win-agentspace')),
      "''": () => cd(prevDir), '``': () => cd(prevDir),
      S: () => { openTerminal(); if (window.tcTerm) window.tcTerm.run(`cd ${cwd}`); },
      '?': () => showKeys(), Escape: () => { if (output) { output = null; render(); } else if (marks.size) { marks.clear(); render(); } else if (filterText) { filterText = ''; render(); } },
    };
    const PREFIXES = new Set(['g', 'y', 'd', 'p', 'u', 'c', 'z', 'o', 'm', "'", '`']);
    function sortKey(key, rev) { sortBy = { key, rev: !!rev }; store.set('tc_rg_sort', sortBy); render(); }
    function go(dir) { if (isDir(dir)) cd(dir); else flash(`${dir} does not exist yet — :mkdir ${dir}`); }
    function sibling(d) {
      if (cwd === '/') return;
      const sib = entries(dirOf(cwd)).filter((x) => x.dir);
      const i = sib.findIndex((x) => x.path === cwd);
      const n = sib[i + d];
      if (n) cd(n.path, { noHistory: true });
    }
    function newTab() { tabs.push({ cwd }); tabIdx = tabs.length - 1; render(); }
    function switchTab(d) { if (tabs.length < 2) return; tabIdx = (tabIdx + d + tabs.length) % tabs.length; cd(tabs[tabIdx].cwd, { noHistory: true }); render(); }
    function closeTab() { if (tabs.length < 2) return; tabs.splice(tabIdx, 1); tabIdx = Math.min(tabIdx, tabs.length - 1); cd(tabs[tabIdx].cwd, { noHistory: true }); render(); }
    function openTerminal() {
      const w = $('win-terminal');
      if (w && (w.style.display === 'none' || w.classList.contains('hidden')) && typeof toggleWindow === 'function') toggleWindow('win-terminal');
      if (window.tcTerm) window.tcTerm.focus();
    }
    function bookmarkSet(k) { bookmarks[k] = cwd; store.set('tc_rg_bm_' + spaceKey(), bookmarks); flash(`bookmark ${k} → ${cwd}`); }
    function bookmarkGo(k) { if (bookmarks[k]) cd(bookmarks[k]); else flash(`no bookmark ${k}`); }

    $('tcSpaceFiles').addEventListener('keydown', (ev) => {
      const t = ev.target;
      if (t.closest('input, textarea, select, [contenteditable="true"]') || ev.metaKey || ev.altKey) return;
      let k = ev.key;
      if (k === 'Shift' || k === 'Control') return;
      if (ev.ctrlKey) k = 'C-' + k.toLowerCase();
      if (ev.shiftKey && k === 'Tab') k = 'S-Tab';
      if (!seq && /^[1-9]$/.test(k) || (count && /^[0-9]$/.test(k) && !seq)) { count += k; ev.preventDefault(); return; }
      const s = seq + k;
      clearTimeout(seqTimer);
      // bookmarks take any key after their prefix
      if (seq === 'm') { seq = ''; ev.preventDefault(); bookmarkSet(k); return; }
      if ((seq === "'" || seq === '`') && k !== "'" && k !== '`') { seq = ''; ev.preventDefault(); bookmarkGo(k); return; }
      if (SEQ[s]) {
        ev.preventDefault();
        const n = Math.max(1, parseInt(count || '1', 10));
        seq = ''; const hadCount = !!count;
        try { SEQ[s](n, hadCount); } finally { count = ''; }
        return;
      }
      const isPrefix = Object.keys(SEQ).some((x) => x.length > s.length && x.startsWith(s)) || (s.length === 1 && PREFIXES.has(s));
      if (isPrefix) { seq = s; ev.preventDefault(); seqTimer = setTimeout(() => { seq = ''; }, 1200); return; }
      seq = ''; count = '';
    });

    // mouse: click selects, double click opens, parent/preview rows navigate
    $('tcRgCur').addEventListener('click', (ev) => {
      const li = ev.target.closest('li[data-path]'); if (!li) return;
      const { es } = here(); const i = es.findIndex((x) => x.path === li.dataset.path);
      if (i >= 0) setIdx(i);
      $('tcSpaceFiles').focus();
    });
    $('tcRgCur').addEventListener('dblclick', (ev) => { const li = ev.target.closest('li[data-path]'); if (li) open(here().e); });
    $('tcRgParent').addEventListener('click', (ev) => { const li = ev.target.closest('li[data-path]'); if (li) { const p = li.dataset.path; if (isDir(p)) cd(p); else cd(dirOf(p), { select: baseOf(p) }); } });
    $('tcRgPreview').addEventListener('click', (ev) => {
      const li = ev.target.closest('li[data-path]');
      if (li) { const p = li.dataset.path; if (isDir(p)) cd(p); else { cd(dirOf(p), { select: baseOf(p) }); cursorMem.set(dirOf(p), baseOf(p)); render(); } return; }
      const b = ev.target.closest('[data-pv]'); if (!b) return;
      const act = b.dataset.pv;
      if (act === 'edit') edit(here().e.path);
      else if (act === 'save') saveEdit();
      else if (act === 'run') saveEdit().then(() => run(editing ? editing.path : null));
      else if (act === 'format') format();
      else if (act === 'close') { if (editing) closeEdit(); else { output = null; render(); } }
    });
    // drag files in from the desktop to upload into the current folder
    const zone = $('tcSpaceFiles');
    zone.addEventListener('dragover', (ev) => { if (ev.dataTransfer && [...ev.dataTransfer.types].includes('Files')) { ev.preventDefault(); zone.classList.add('tc-rg-drop'); } });
    zone.addEventListener('dragleave', () => zone.classList.remove('tc-rg-drop'));
    zone.addEventListener('drop', (ev) => { if (ev.dataTransfer && ev.dataTransfer.files.length) { ev.preventDefault(); zone.classList.remove('tc-rg-drop'); upload(ev.dataTransfer.files); } });

    function showKeys() {
      const groups = [
        ['move', [['h j k l', 'left / down / up / open'], ['gg G', 'top / bottom (5G = row 5)'], ['J K', 'half page'], ['H L', 'back / forward'], ['[ ]', 'previous / next folder']]],
        ['select', [['space', 'mark + down'], ['v', 'invert marks'], ['uv', 'unmark all'], [':mark re', 'mark by pattern']]],
        ['files', [['yy dd', 'copy / cut'], ['pp po', 'paste / overwrite'], ['dD', 'delete'], ['cw a A I', 'rename'], ['yp yn', 'copy path / name'], ['E', 'edit'], ['r', 'run .py / .js'], ['=', 'format (Prettier)']]],
        ['find', [['/ n N', 'search'], ['f', 'find as you type'], ['zf', 'filter'], ['o s/n/m/t/e', 'sort (O reverses)'], ['zh', 'hidden files']]],
        ['go', [['gh g/', 'root'], ['gs gd gm gN', '/src /docs /models3d /notes'], ["m<k> '<k>", 'set / go bookmark'], ["''", 'previous folder']]],
        ['tabs & more', [['gn gt gT gc', 'new / next / prev / close tab'], [':', 'console (Tab completes)'], ['S', 'terminal here'], ['R', 'reload'], ['q', 'close']]],
      ];
      output = { title: 'keys', html: groups.map(([g, ks]) => `<h4>${g}</h4>` + ks.map(([k, d]) => `<div><b>${esc(k)}</b><span>${esc(d)}</span></div>`).join('')).join('') +
        `<h4>console</h4>` + Object.entries(COMMANDS).map(([k, d]) => `<div><b>:${k}</b><span>${esc(d.replace(/^\S+\s?/, ''))}</span></div>`).join('') };
      renderPreview(here().e);
      showTab('files');
      $('tcSpaceFiles').focus();
    }

    // ---------------------------------------------------------------- space switching
    async function setScope(scope, owner) {
      if (editing && editing.value != null && editing.value !== editing.clean && !confirmInline('discard unsaved edits?')) return;
      editing = null; output = null; marks.clear(); cwd = '/'; cursorMem.clear(); back = []; fwd = []; tabs = [{ cwd: '/' }]; tabIdx = 0; filterText = ''; searchRe = null;
      win.querySelectorAll('[data-scope]').forEach((b) => b.setAttribute('aria-pressed', b.dataset.scope === scope ? 'true' : 'false'));
      const pick = $('tcSpacePick');
      $('tcSpaceNew').hidden = scope !== 'dynamic';
      win.querySelector('[data-act="fork"]').hidden = scope === 'user';
      if (scope === 'user') { pick.hidden = true; sp = { scope, owner: peer() }; }
      else {
        pick.hidden = false;
        pick.innerHTML = '<option>loading…</option>';
        const [list, topics] = await Promise.all([
          api(`/api/spaces?scope=${scope}`).then((d) => d.spaces || []).catch(() => []),
          scope === 'topic' ? api('/api/board/topics').then((d) => d.topics || []).catch(() => []) : Promise.resolve([]),
        ]);
        const titles = new Map(topics.map((t) => ['topic-' + String(t.id || t.topic_id || '').replace(/^topic-/, ''), t.title]));
        const opts = list.map((s) => ({ id: s.owner_id, label: titles.get(s.owner_id) || s.title || s.owner_id, n: s.file_count })).sort((a, b) => a.label.localeCompare(b.label));
        if (owner && !opts.some((o) => o.id === owner)) opts.unshift({ id: owner, label: owner, n: 0 });
        if (!opts.length) {
          pick.innerHTML = `<option value="">no ${scope === 'topic' ? 'topic spaces yet — post on the Board' : 'sandboxes yet'}</option>`;
          sp = { scope, owner: '' }; files = []; buildIndex(); render(); return;
        }
        pick.innerHTML = opts.map((o) => `<option value="${esc(o.id)}">${esc(o.label.slice(0, 48))} · ${o.n} files</option>`).join('');
        const chosen = owner || store.get('tc_space_last_' + scope, '') || opts[0].id;
        pick.value = opts.some((o) => o.id === chosen) ? chosen : opts[0].id;
        sp = { scope, owner: pick.value };
      }
      store.set('tc_space_last_' + scope, sp.owner);
      bookmarks = store.get('tc_rg_bm_' + spaceKey(), {});
      await reload();
    }
    win.querySelectorAll('[data-scope]').forEach((b) => b.addEventListener('click', () => setScope(b.dataset.scope)));
    $('tcSpacePick').addEventListener('change', (ev) => { if (ev.target.value) setScope(sp.scope, ev.target.value); });
    $('tcSpaceNew').addEventListener('click', async () => {
      const title = `sandbox ${new Date().toISOString().slice(5, 16).replace('T', ' ')}`;
      try { const d = await api('/api/space/create', { method: 'POST', body: JSON.stringify({ scope: 'dynamic', title, template: 'python' }) }); await setScope('dynamic', d.owner_id); flash(`created ${d.owner_id}`); }
      catch (err) { flash('could not create sandbox: ' + err.message); }
    });

    async function exportSpace() {
      try {
        const d = await api(`/api/space/export?${qs(sp)}`);
        const blob = new Blob([Uint8Array.from(atob(d.space_b64), (c) => c.charCodeAt(0))], { type: 'application/octet-stream' });
        download(blob, d.filename || `${sp.owner}.space`);
      } catch (err) { flash('export failed: ' + err.message); }
    }
    async function zipSpace() {
      try {
        flash('packing…');
        await loadScript('https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js');
        const zip = new window.JSZip();
        for (const f of files) { const rec = await vfs.read(sp, f.path); zip.file(f.path.slice(1), rec.content_b64 || '', { base64: true }); }
        if (!isFile('/.vscode/extensions.json')) zip.file('.vscode/extensions.json', JSON.stringify({ recommendations: recs }, null, 2));
        download(await zip.generateAsync({ type: 'blob' }), `${sp.scope === 'user' ? 'my-space' : sp.owner}.zip`);
        flash('downloaded — unzip and open the folder in VS Code');
      } catch (err) { flash('zip failed: ' + err.message); }
    }
    function download(blob, name) {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = name;
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 2000);
    }
    win.querySelector('[data-act="upload"]').addEventListener('click', () => $('tcSpaceUpload').click());
    $('tcSpaceUpload').addEventListener('change', (ev) => { if (ev.target.files.length) upload(ev.target.files); ev.target.value = ''; });
    win.querySelector('[data-act="import"]').addEventListener('click', () => $('tcSpaceImport').click());
    $('tcSpaceImport').addEventListener('change', (ev) => {
      const file = ev.target.files[0]; ev.target.value = '';
      if (!file) return;
      showTab('files');
      ask(`import ${file.name}? it replaces all ${files.length} files in this space`, async () => {
        const b64 = await new Promise((res) => { const r = new FileReader(); r.onload = () => res(String(r.result).split(',')[1] || ''); r.readAsDataURL(file); });
        try { await api('/api/space/import', { method: 'POST', body: JSON.stringify({ scope: sp.scope, owner_id: sp.owner, data: b64 }) }); await reload(); flash(`imported ${file.name}`); }
        catch (err) { flash('import failed: ' + err.message); }
      });
    });
    win.querySelector('[data-act="export"]').addEventListener('click', exportSpace);
    win.querySelector('[data-act="zip"]').addEventListener('click', zipSpace);
    win.querySelector('[data-act="fork"]').addEventListener('click', async () => {
      // copy into a folder of my space instead of overwriting it
      const from = { ...sp }, dest = '/from-' + sp.owner;
      flash(`copying ${files.length} files to my space ${dest}/ …`);
      try {
        for (const f of files) { const rec = await vfs.read(from, f.path); await api('/api/space/file', { method: 'POST', body: JSON.stringify({ scope: 'user', owner_id: peer(), path: dest + f.path, content: rec.content_b64 || '', is_base64: true, updated_by: handle() }) }); }
        await setScope('user'); cd(dest); flash(`copied into ${dest}/`);
      } catch (err) { flash('copy failed: ' + err.message); }
    });
    win.querySelector('[data-act="keys"]').addEventListener('click', showKeys);

    // ---------------------------------------------------------------- tabs: files / extensions / artcraft
    function showTab(tab) {
      win.querySelectorAll('[data-tab]').forEach((b) => b.setAttribute('aria-selected', b.dataset.tab === tab ? 'true' : 'false'));
      $('tcSpaceFiles').hidden = tab !== 'files';
      $('tcSpaceExt').hidden = tab !== 'ext';
      $('tcSpaceArt').hidden = tab !== 'art';
      if (tab === 'files') { $('tcSpaceFiles').focus(); renderStatus(); }
      if (tab === 'ext') { renderInstalled(); if (!$('tcExtResults').children.length) searchExt(''); }
      if (tab === 'art') renderArt();
    }
    win.querySelectorAll('[data-tab]').forEach((b) => b.addEventListener('click', () => showTab(b.dataset.tab)));

    // extensions: real Open VSX search, recorded in .vscode/extensions.json
    const CAP_NOTE = (id) => /prettier/i.test(id) ? 'works here: = or :format' : /markdown/i.test(id) ? 'works here: rendered .md preview' : /gl(b|tf)|3d-model|model-viewer/i.test(id) ? 'works here: 3D preview' : /^ms-python\.python$/i.test(id) ? 'works here: r runs .py' : 'recommended for VS Code';
    async function writeRecs(next) {
      recs = [...new Set(next)];
      await vfs.write(sp, '/.vscode/extensions.json', JSON.stringify({ recommendations: recs }, null, 2) + '\n');
      await reload();
      renderInstalled();
      win.querySelectorAll('#tcExtResults [data-ext]').forEach((b) => { const on = recs.includes(b.dataset.ext); b.textContent = on ? 'remove' : 'add'; b.classList.toggle('tc-btn-solid', !on); });
    }
    function renderInstalled() {
      const ul = $('tcExtInstalled');
      $('tcExtCount').textContent = recs.length ? String(recs.length) : '';
      ul.innerHTML = recs.length ? recs.map((id) => `<li><span></span><div><div class="t">${esc(id)}</div><div class="cap">${esc(CAP_NOTE(id))}</div></div><button type="button" class="tc-btn" data-ext="${esc(id)}">remove</button></li>`).join('')
        : '<li><span></span><div class="tc-dim">No extensions in this space yet. Search Open VSX and add some.</div></li>';
    }
    async function searchExt(q) {
      const ul = $('tcExtResults');
      ul.innerHTML = '<li><span></span><div class="tc-dim">searching Open VSX…</div></li>';
      try {
        const r = await fetch(`https://open-vsx.org/api/-/search?query=${encodeURIComponent(q)}&size=25&sortBy=${q ? 'relevance' : 'downloadCount'}&sortOrder=desc`);
        const d = await r.json();
        $('tcExtTotal').textContent = q ? `${(d.totalSize || 0).toLocaleString()} results` : 'most downloaded';
        ul.innerHTML = (d.extensions || []).map((x) => {
          const id = `${x.namespace}.${x.name}`;
          const on = recs.includes(id);
          return `<li><img src="${esc((x.files && x.files.icon) || '')}" alt="" loading="lazy" onerror="this.style.visibility='hidden'"><div><div class="t">${esc(x.displayName || x.name)}</div><div class="i">${esc(id)} · v${esc(x.version)} · ${Number(x.downloadCount || 0).toLocaleString()} installs</div><div class="d">${esc(x.description || '')}</div><div class="cap">${esc(CAP_NOTE(id))}</div></div><button type="button" class="tc-btn${on ? '' : ' tc-btn-solid'}" data-ext="${esc(id)}">${on ? 'remove' : 'add'}</button></li>`;
        }).join('') || '<li><span></span><div class="tc-dim">no results</div></li>';
      } catch (err) { ul.innerHTML = `<li><span></span><div class="tc-dim">Open VSX unreachable: ${esc(err.message)}</div></li>`; }
    }
    $('tcExtGo').addEventListener('click', () => searchExt($('tcExtQuery').value.trim()));
    $('tcExtQuery').addEventListener('keydown', (ev) => { if (ev.key === 'Enter') { ev.preventDefault(); searchExt(ev.target.value.trim()); } });
    $('tcSpaceExt').addEventListener('click', (ev) => {
      const b = ev.target.closest('[data-ext]'); if (!b) return;
      const id = b.dataset.ext;
      writeRecs(recs.includes(id) ? recs.filter((x) => x !== id) : recs.concat(id)).then(() => flash(`${recs.includes(id) ? 'added' : 'removed'} ${id}`)).catch((err) => flash(err.message));
    });

    // artcraft: desktop apps; open directly only when the relay runs on the same computer
    let manifest = null;
    const relayIsLocal = () => ['localhost', '127.0.0.1', '::1'].includes(location.hostname);
    async function renderArt() {
      if (!manifest) { try { manifest = await api('/api/wasm/manifest'); } catch (err) { $('tcArtStatus').textContent = 'Could not reach the ArtCraft manifest: ' + err.message; return; } }
      const launcher = manifest.artcraft_launcher || {};
      const local = relayIsLocal() && launcher.installed_on_pc;
      $('tcArtStatus').innerHTML = local
        ? `This relay runs on your computer and found <b>ArtCraft Launcher ${esc(launcher.pc_version || '')}</b>. <b>open</b> sends the file straight into the desktop app; <b>sync back</b> pulls your saved edits into the space.`
        : `ArtCraft apps are desktop apps (macOS, Windows, Linux). This relay runs in the cloud, so it can’t launch them for you: <b>download</b> the file and open it in the app, or get the app from getartcraft.com. When the relay runs on your own computer, files open directly.`;
      const { e } = here();
      const fileExt = e && !e.dir ? '.' + extOf(e.name) : '';
      $('tcArtFile').innerHTML = e && !e.dir ? `current file <b>${esc(e.path)}</b> · <a class="tc-link" href="${vfs.raw(sp, e.path, true)}" download>download</a>` : '<span class="tc-dim">Select a file in <b>files</b> to see which apps open it.</span>';
      const apps = Object.entries(manifest.artcraft_apps || {}).map(([id, a]) => ({ id, ...a, fit: !!fileExt && (a.extensions || []).includes(fileExt) })).sort((x, y) => (y.fit - x.fit) || x.display_name.localeCompare(y.display_name));
      $('tcArtApps').innerHTML = apps.map((a) => `<li class="${a.fit ? 'fit' : ''}"><span><b>${esc(a.display_name)}</b></span><span class="x">${esc((a.extensions || []).join(' '))}</span><span class="a">${local && a.installed_on_pc && a.fit ? `<button type="button" class="tc-btn tc-btn-solid" data-art-open="${esc(a.id)}">open</button><button type="button" class="tc-btn" data-art-sync="${esc(a.id)}">sync back</button>` : ''}<a class="tc-btn" href="${esc(a.website || 'https://getartcraft.com/apps/' + a.id)}" target="_blank" rel="noopener">${local && a.installed_on_pc ? 'site' : 'get app'}</a></span></li>`).join('');
    }
    $('tcArtApps').addEventListener('click', async (ev) => {
      const o = ev.target.closest('[data-art-open], [data-art-sync]'); if (!o) return;
      const { e } = here(); if (!e || e.dir) return;
      const sync = !!o.dataset.artSync;
      try {
        const d = await api('/api/artcraft/open', { method: 'POST', body: JSON.stringify({ app_id: o.dataset.artOpen || o.dataset.artSync, scope: sp.scope, owner_id: sp.owner, path: e.path, launch_process: true, sync }) });
        flash(sync ? `synced ${e.name} from the desktop app` : `opened ${e.name} (${d.mode || 'desktop'})`);
        if (sync) await reload();
      } catch (err) { flash('ArtCraft: ' + err.message); }
    });
    async function gen3d(prompt) {
      if (!prompt) { flash('describe the model first'); return; }
      const slug = prompt.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40) || 'model';
      $('tcArtGenOut').textContent = 'generating…';
      try {
        const d = await api('/api/3d/generate', { method: 'POST', body: JSON.stringify({ prompt, peer_id: peer(), scope: sp.scope, owner_id: sp.owner, save_path: `/models3d/${slug}.glb`, format: 'glb' }) });
        const saved = d.save_path || d.saved_path || d.path || `/models3d/${slug}.glb`;
        $('tcArtGenOut').textContent = `${d.status || 'done'} · saved ${saved}${d.simulated ? ' (simulated — no Rodin key on this relay)' : ''}`;
        await reload();
        if (isFile(saved)) cd(dirOf(saved), { select: baseOf(saved) });
      } catch (err) { $('tcArtGenOut').textContent = 'generation failed: ' + err.message; }
    }
    $('tcArtGen').addEventListener('submit', (ev) => { ev.preventDefault(); gen3d($('tcArtGenPrompt').value.trim()); });

    // ---------------------------------------------------------------- public API
    function showWindow() {
      if ((win.style.display === 'none' || win.classList.contains('hidden')) && typeof toggleWindow === 'function') toggleWindow('win-agentspace');
      else if (typeof bringToFront === 'function') bringToFront(win);
    }
    window.tcSpace = {
      reload,
      async open(path, opts) {
        if (sp.scope !== 'user') await setScope('user');
        else await reload();
        showWindow(); showTab('files');
        if (isDir(path)) cd(path);
        else if (isFile(path)) { cd(dirOf(path), { select: baseOf(path) }); cursorMem.set(dirOf(path), baseOf(path)); render(); if (opts && opts.edit) edit(path); }
        else if (opts && opts.edit) { await touch(path); edit(path); }
        $('tcSpaceFiles').focus();
      },
      async saveAndOpen(path, content) { await vfs.write({ scope: 'user', owner: peer() }, path, content); return this.open(path); },
    };
    window.refreshAgentSpace = () => reload();

    win.addEventListener('mousedown', (ev) => { if (!ev.target.closest('input, textarea, select, button, a, [role="tab"]') && !$('tcSpaceFiles').hidden) setTimeout(() => $('tcSpaceFiles').focus(), 0); });
    setScope('user');
  })();
  </script>
"""


def apply_space_finder(html: str) -> str:
    """Inject the Space file manager styles and engine into the Mesh OS HTML (idempotent)."""
    if 'id="tcSpaceScript"' in html:
        return html
    head_end = html.find("</head>")
    if head_end == -1:
        return html
    html = html[:head_end] + SPACE_HEAD + html[head_end:]
    body_end = html.rfind("</body>")
    if body_end == -1:
        return html
    return html[:body_end] + SPACE_BODY + html[body_end:]
