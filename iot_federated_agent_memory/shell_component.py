"""TinCan Mesh OS: the reusable shell component (``window.TinCanShell``).

One command interpreter, two ways to use it:

* ``TinCanShell.run(line, opts?)`` runs a single command headlessly and
  resolves to ``{ok: boolean, text: string}`` (plain text, no HTML).
* ``TinCanShell.mount(containerEl, opts?)`` renders an interactive shell
  (transcript growing upward, input pinned at the bottom) into any element.
  Every instance has its own transcript, input and history, and every command
  goes through the same interpreter as ``run``.

Commands (all against the caller's own ``.space`` VFS): ``ls``, ``cat``,
``open``, ``tree``, ``run``, ``py``/``exec``, ``runs``, ``drive``, ``status``,
``brew``, ``ask`` (anything else goes to the AI gateway), ``help`` and
``clear``.

The JS lives inside the page's main script (``/*TC_SHELL_JS*/`` slot) so it can
read the Mesh OS globals (``currentSpaceScope``, ``currentSpaceOwner``,
``myPeerId``, ``driveState``); ``apply_shell_component`` fills the slot and adds
the shell CSS. Containers marked ``data-tc-shell-mount`` are mounted
automatically.
"""

from __future__ import annotations

SHELL_JS_SLOT = "/*TC_SHELL_JS*/"
SHELL_CSS_SLOT = "/*TC_SHELL_CSS*/"

SHELL_CSS = r"""
    /* TinCanShell (shell_component.py): a mountable terminal, Celadon look */
    .tcsh { display: flex; flex-direction: column; min-height: 0; min-width: 0; height: 100%; background: #ffffff; color: #111111;
      border: 1px solid #111111; border-radius: 12px; overflow: hidden;
      font-family: "JetBrains Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace; font-size: 12px; line-height: 1.5; }
    .tcsh-bar { display: flex; align-items: center; gap: 6px; padding: 4px 10px; background: #f4f8f0; border-bottom: 1px solid rgba(17,17,17,0.22);
      font-size: 10px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; flex: 0 0 auto; }
    .tcsh-bar .tcsh-spacer { flex: 1; }
    .tcsh-bar button { font: inherit; font-size: 9px; letter-spacing: 0; text-transform: none; padding: 1px 8px; border: 1px solid #111111; border-radius: 9999px;
      background: transparent; color: #111111; cursor: pointer; }
    .tcsh-bar button:hover { background: #111111; color: #ecf1e6; }
    .tcsh-pill { padding: 1px 8px; border: 1px solid #111111; border-radius: 9999px; font-size: 9px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }
    .tcsh-scroll { flex: 1 1 auto; min-height: 0; overflow-y: auto; overscroll-behavior: contain; cursor: text; }
    .tcsh-log { min-height: 100%; display: flex; flex-direction: column; justify-content: flex-end; padding: 8px 12px 4px; gap: 1px; user-select: text; }
    .tcsh-help { color: #4a4a4a; margin: 0 0 4px; white-space: pre-wrap; }
    .tcsh-cmd { margin-top: 6px; word-break: break-word; }
    .tcsh-ps { font-weight: 700; color: #111111; }
    .tcsh-out { margin: 0; padding-left: 8px; white-space: pre-wrap; word-break: break-word; font: inherit; color: #262626; }
    .tcsh-out.tcsh-err { color: #8a1c1c; }
    .tcsh-note { margin-top: 6px; color: #262626; word-break: break-word; }
    .tcsh-row { display: flex; align-items: center; gap: 8px; padding: 6px 12px; border-top: 1px solid #111111; background: #f4f8f0; flex: 0 0 auto; margin: 0; }
    .tcsh-row .tcsh-ps { flex: 0 0 auto; }
    .tcsh .tcsh-input { flex: 1 1 auto; min-width: 0; background: transparent !important; border: 0 !important; outline: 0; box-shadow: none; color: #111111 !important;
      font: inherit; padding: 2px 0; border-radius: 0 !important; }
    .tcsh .tcsh-input::placeholder { color: #5c5c5c; }
    .tcsh-run { flex: 0 0 auto; font: inherit; font-size: 10px; font-weight: 700; padding: 2px 10px; border: 1px solid #111111; border-radius: 9999px; background: #111111; color: #ecf1e6; cursor: pointer; }
    .tcsh-run:hover { opacity: 0.85; }
"""

SHELL_JS = r"""
    // =========================================================================
    // TinCanShell (shell_component.py): one interpreter, headless run() + mountable UI
    // =========================================================================
    const termEsc = (v) => String(v == null ? '' : v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    let termSummary = null;
    let termDrive = { available: null, mirror: null };

    function termScope() { return (typeof currentSpaceScope !== 'undefined' && currentSpaceScope) || 'user'; }
    function termOwner() {
      return (typeof currentSpaceOwner !== 'undefined' && currentSpaceOwner) || myPeerId || 'default';
    }
    function termHandle() {
      const u = (localStorage.getItem('tincan_username') || '').trim().replace(/^@+/, '');
      return u || 'you';
    }
    function termBytes(n) {
      n = Number(n) || 0;
      if (n < 1024) return n + 'B';
      if (n < 1048576) return (n / 1024).toFixed(1) + 'K';
      return (n / 1048576).toFixed(1) + 'M';
    }
    function termPrompt() { return termHandle() + '@tincan:~/space$'; }

    // Scope/owner for one call: opts may pin them (string or function), else follow the Space window.
    function termCtx(o) {
      o = o || {};
      const pick = (v, d) => (typeof v === 'function' ? v() : (v != null && v !== '' ? v : d()));
      return { scope: pick(o.scope, termScope), owner: pick(o.owner, termOwner), pinned: o.scope != null || o.owner != null };
    }

    async function termFetchSummary(c) {
      c = c || termCtx();
      const r = await fetch(`/api/space/ls?scope=${encodeURIComponent(c.scope)}&owner_id=${encodeURIComponent(c.owner)}`, { cache: 'no-store' });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const s = await r.json();
      if (!c.pinned) termSummary = s;
      return s;
    }

    async function termFetchDrive() {
      try {
        if (typeof driveState !== 'undefined' && driveState && driveState.mirror) {
          termDrive = { available: true, mirror: driveState.mirror };
          return termDrive;
        }
        const r = await fetch('/api/drive/status', { cache: 'no-store' });
        const st = r.ok ? await r.json() : { available: false };
        if (!st.available) { termDrive = { available: false, mirror: null, on_railway: !!st.on_railway }; return termDrive; }
        const m = await fetch('/api/drive/mirror?depth=2', { cache: 'no-store' });
        termDrive = { available: true, mirror: m.ok ? await m.json() : null };
      } catch (e) {
        termDrive = { available: false, mirror: null };
      }
      return termDrive;
    }

    async function termExec(body, o) {
      const c = termCtx(o);
      const r = await fetch('/api/space/exec', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(Object.assign({ scope: c.scope, owner_id: c.owner }, body))
      });
      const d = await r.json();
      if (!r.ok || d.error) throw new Error(d.error || `HTTP ${r.status}`);
      return d;
    }

    function termBuildTree(files) {
      const root = {};
      files.forEach(f => {
        const parts = String(f.path || '').split('/').filter(Boolean);
        let node = root;
        parts.forEach((part, i) => {
          if (i === parts.length - 1) { node[part] = { __file: f }; return; }
          if (!node[part] || node[part].__file) node[part] = {};
          node = node[part];
        });
      });
      return root;
    }

    function termLinesOf(node, prefix, out) {
      const names = Object.keys(node).sort((a, b) => {
        const fa = !!node[a].__file, fb = !!node[b].__file;
        return fa === fb ? a.localeCompare(b) : (fa ? 1 : -1);
      });
      names.forEach((name, i) => {
        const last = i === names.length - 1;
        const child = node[name];
        if (child.__file) out.push(prefix + (last ? '└── ' : '├── ') + name + '  (' + termBytes(child.__file.size_bytes) + ')');
        else { out.push(prefix + (last ? '└── ' : '├── ') + name + '/'); termLinesOf(child, prefix + (last ? '    ' : '│   '), out); }
      });
      return out;
    }

    const TC_SHELL_HELP = [
      'ls [dir]      list files in your space',
      'cat <file>    print a file',
      'open <file>   open a file in the Space editor',
      'tree          show your space as a tree',
      'run [file]    run a file in the sandbox (default /src/main.py)',
      'py <code>     run Python in the sandbox',
      'runs          list recent runs',
      'drive         drive mirror status',
      'status        mesh room status',
      'brew <args>   TinCan Homebrew (brew install tincan context-palace)',
      'ask <q>       ask the AI gateway',
      'clear         clear the screen',
      'help          this list'
    ].join('\n');

    const TC_SHELL_INTRO = 'Commands run against your own .space: ls [dir], cat file, open file, tree, run [file], py code, runs, drive, status, ask question, help.';

    function termDone(ok, text, extra) { return Object.assign({ ok: !!ok, text: String(text == null ? '' : text) }, extra || {}); }
    function termSpaceChanged(c) {
      try { window.dispatchEvent(new CustomEvent('tincan:space-changed', { detail: { scope: c.scope, owner: c.owner } })); } catch (e) {}
    }

    // The one interpreter. Returns {ok, text, clear?}. Throws are caught by the callers.
    async function termInterpret(line, o) {
      o = o || {};
      const cmd = String(line || '').trim();
      if (!cmd) return termDone(true, '');
      const c = termCtx(o);
      const progress = typeof o.progress === 'function' ? o.progress : function () {};
      const [verb, ...rest] = cmd.split(/\s+/);
      const arg = rest.join(' ');
      const absPath = (p) => (p.startsWith('/') ? p : '/' + p);
      try {
        if (cmd === 'clear') return termDone(true, '', { clear: true });
        if (verb === 'help') return termDone(true, TC_SHELL_HELP);
        if (verb === 'ls') {
          const s = await termFetchSummary(c);
          const dir = arg ? ('/' + arg.replace(/^\/+|\/+$/g, '') + '/') : '/';
          const names = new Set();
          (s.files || []).forEach(f => {
            if (!String(f.path).startsWith(dir)) return;
            const restPath = String(f.path).slice(dir.length);
            const first = restPath.split('/')[0];
            names.add(restPath.includes('/') ? first + '/' : first);
          });
          return names.size ? termDone(true, Array.from(names).sort().join('  ')) : termDone(false, `ls: ${dir}: no files`);
        }
        if ((verb === 'cat' || verb === 'open' || verb === 'edit' || verb === 'code') && !arg) {
          return termDone(false, `${verb}: usage: ${verb} <file>`);
        }
        if (verb === 'open' || verb === 'edit' || verb === 'code') {
          const p = absPath(arg);
          if (!c.pinned && typeof openAgentSpaceFile === 'function') {
            const win = document.getElementById('win-agentspace');
            if (win && win.classList.contains('hidden') && typeof toggleWindow === 'function') toggleWindow('win-agentspace');
            await openAgentSpaceFile(p);
            return termDone(true, 'Opened ' + p + ' in Space.');
          }
          // no editor to open it in: fall through to cat
        }
        if (verb === 'cat' || verb === 'open' || verb === 'edit' || verb === 'code') {
          const p = absPath(arg);
          const r = await fetch(`/api/space/file?scope=${encodeURIComponent(c.scope)}&owner_id=${encodeURIComponent(c.owner)}&path=${encodeURIComponent(p)}`, { cache: 'no-store' });
          const d = await r.json();
          if (!r.ok || d.error) throw new Error(d.error || `HTTP ${r.status}`);
          if (d.content != null) return termDone(true, d.content);
          return termDone(true, `${p}: ${d.mime_type || 'binary'} · ${termBytes(d.size_bytes)} · binary file (use "open ${p}" to preview it in Space)`);
        }
        if (verb === 'tree') {
          const s = await termFetchSummary(c);
          const files = s.files || [];
          if (!files.length) return termDone(true, '~/space · ' + c.owner + '\n(empty)');
          const lines = ['~/space · ' + c.owner];
          termLinesOf(termBuildTree(files), '', lines);
          const dirs = new Set();
          files.forEach(f => { const parts = String(f.path).split('/').filter(Boolean); for (let i = 1; i < parts.length; i++) dirs.add(parts.slice(0, i).join('/')); });
          lines.push('', `${dirs.size} director${dirs.size === 1 ? 'y' : 'ies'}, ${files.length} file${files.length === 1 ? '' : 's'}`);
          return termDone(true, lines.join('\n'));
        }
        if (verb === 'run') {
          const entry = arg ? absPath(arg) : '/src/main.py';
          const d = await termExec({ entrypoint: entry, runtime: 'auto' }, o);
          termSpaceChanged(c);
          return termDone(!Number(d.exit_code), ((d.stdout || '') + (d.stderr ? '\n' + d.stderr : '')) || `exit ${d.exit_code}`);
        }
        if (verb === 'py' || verb === 'exec') {
          if (!arg) return termDone(false, `${verb}: usage: ${verb} <code>`);
          const d = await termExec({ runtime: 'python', code_override: arg }, o);
          termSpaceChanged(c);
          return termDone(!Number(d.exit_code), ((d.stdout || '') + (d.stderr ? '\n' + d.stderr : '')) || `exit ${d.exit_code}`);
        }
        if (verb === 'runs') {
          const s = await termFetchSummary(c);
          return termDone(true, (s.recent_runs || []).map(r => `${r.created_at || ''}  ${r.runtime}  exit ${r.exit_code}  ${r.duration_ms}ms  ${r.entrypoint || '(inline)'}`).join('\n') || 'No runs yet.');
        }
        if (verb === 'drive') {
          await termFetchDrive();
          return termDone(true, termDrive.available ? `Mirroring ${termDrive.mirror ? termDrive.mirror.root : 'drive'} (read-only, never saved).` : 'Drive mirror is off here: it only runs when TinCan runs on this computer.');
        }
        if (verb === 'status' || cmd === 'tincan status') {
          const r = await fetch('/api/mesh/state');
          const d = await r.json();
          return termDone(true, `room ${d.room || 'main'} · ${Object.keys(d.peers || {}).length} peers · relay online`);
        }
        if (verb === 'brew' || cmd.startsWith('tincan brew')) {
          const cleanBrewCmd = cmd.replace(/^tincan\s+/i, '');
          progress('==> Contacting TinCan Homebrew Tap & Cellar...');
          const r = await fetch('/api/terminal/brew', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: cleanBrewCmd, peer_id: (typeof myPeerId !== 'undefined' && myPeerId) || 'aeonik' })
          });
          const d = await r.json();
          if (typeof awardLocalXp === 'function' && cleanBrewCmd.includes('install')) {
            awardLocalXp(35, 'Installed package via TinCan Homebrew');
          }
          return termDone(r.ok, d.output || (Array.isArray(d.lines) ? d.lines.join('\n') : JSON.stringify(d)));
        }
        if (verb === 'ask' && !arg) return termDone(false, 'ask: usage: ask <question>');
        const prompt = cmd.replace(/^(ask|tincan chat)\s+/i, '');
        progress('Asking the AI gateway…');
        const r = await fetch('/api/chat', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ model: 'gemini-brain', prompt: prompt, peer_id: (typeof myPeerId !== 'undefined' && myPeerId) || 'terminal' })
        });
        const d = await r.json();
        const text = d.content || d.response || d.error || JSON.stringify(d);
        return termDone(r.ok && !d.error, text);
      } catch (e) {
        return termDone(false, verb + ': ' + (e && e.message ? e.message : e));
      }
    }

    window.TinCanShell = (function () {
      const instances = [];

      async function run(line, opts) {
        try {
          const r = await termInterpret(line, opts);
          return { ok: !!r.ok, text: String(r.text == null ? '' : r.text) };
        } catch (e) {
          return { ok: false, text: String(e && e.message ? e.message : e) };
        }
      }

      function mount(el, opts) {
        if (typeof el === 'string') el = document.querySelector(el);
        if (!el) return null;
        if (el.__tcShell) return el.__tcShell;
        opts = opts || {};
        el.classList.add('tcsh');
        el.setAttribute('data-tc-shell', '1');
        el.innerHTML =
          '<div class="tcsh-bar"><span>' + termEsc(opts.title || 'Shell') + '</span><span class="tcsh-spacer"></span>' +
          '<button type="button" data-act="clear">Clear</button><span class="tcsh-pill" data-role="pill">Ready</span></div>' +
          '<div class="tcsh-scroll" data-role="scroll"><div class="tcsh-log" data-role="log" role="log" aria-live="polite"></div></div>' +
          '<form class="tcsh-row" autocomplete="off"><span class="tcsh-ps" data-role="prompt"></span>' +
          '<input class="tcsh-input" data-role="input" type="text" spellcheck="false" autocapitalize="off" aria-label="Shell command" placeholder="' +
          termEsc(opts.placeholder || 'ls, cat /src/main.py, run, py print(1), ask …') + '" />' +
          '<button type="submit" class="tcsh-run">RUN</button></form>';
        const $ = (r) => el.querySelector('[data-role="' + r + '"]');
        const log = $('log'), scroll = $('scroll'), input = $('input'), pill = $('pill'), ps = $('prompt');
        const history = [];
        let hIdx = 0;

        const refreshPrompt = () => { ps.textContent = termPrompt(); };
        const toBottom = () => { scroll.scrollTop = scroll.scrollHeight; };
        const setPill = (t) => { pill.textContent = t; };
        function intro() {
          const p = document.createElement('div');
          p.className = 'tcsh-help';
          p.textContent = opts.intro || TC_SHELL_INTRO;
          log.appendChild(p);
        }

        function clear() { log.innerHTML = ''; intro(); }
        function note(html) {
          const d = document.createElement('div');
          d.className = 'tcsh-note';
          d.innerHTML = html;
          log.appendChild(d);
          toBottom();
        }

        async function exec(line) {
          line = String(line == null ? '' : line).trim();
          if (!line) return { ok: true, text: '' };
          history.push(line);
          hIdx = history.length;
          refreshPrompt();
          if (line === 'clear') { clear(); return { ok: true, text: '' }; }
          const cmdLine = document.createElement('div');
          cmdLine.className = 'tcsh-cmd';
          cmdLine.innerHTML = '<span class="tcsh-ps">' + termEsc(termPrompt()) + '</span> ' + termEsc(line);
          const out = document.createElement('pre');
          out.className = 'tcsh-out';
          log.appendChild(cmdLine);
          log.appendChild(out);
          setPill('Running');
          toBottom();
          const o = Object.assign({}, opts, { progress: (t) => { out.textContent = t; toBottom(); } });
          const r = await termInterpret(line, o);
          if (r.clear) clear();
          out.textContent = r.text;
          out.classList.toggle('tcsh-err', !r.ok);
          setPill('Ready');
          toBottom();
          return { ok: !!r.ok, text: String(r.text) };
        }

        function submit() {
          const v = input.value;
          input.value = '';
          return exec(v);
        }

        el.querySelector('form').addEventListener('submit', (ev) => { ev.preventDefault(); submit(); });
        el.querySelector('[data-act="clear"]').addEventListener('click', clear);
        scroll.addEventListener('click', (ev) => { if (!window.getSelection || window.getSelection().isCollapsed) input.focus(); });
        input.addEventListener('keydown', (ev) => {
          if (ev.key === 'ArrowUp') { if (hIdx > 0) { hIdx--; input.value = history[hIdx]; } ev.preventDefault(); }
          else if (ev.key === 'ArrowDown') { if (hIdx < history.length - 1) { hIdx++; input.value = history[hIdx]; } else { hIdx = history.length; input.value = ''; } ev.preventDefault(); }
          else if (ev.key === 'l' && ev.ctrlKey) { ev.preventDefault(); clear(); }
          ev.stopPropagation();
        });

        refreshPrompt();
        intro();
        const inst = { el, history, exec, submit, clear, note, focus: () => input.focus(), refreshPrompt, destroy() {
          const i = instances.indexOf(inst); if (i >= 0) instances.splice(i, 1);
          el.__tcShell = null; el.innerHTML = '';
        } };
        el.__tcShell = inst;
        instances.push(inst);
        return inst;
      }

      return { version: 1, run, mount, instances };
    })();

    // Legacy names: thin wrappers over the Terminal window's shell instance.
    function _tcTerminalShell() {
      const host = document.getElementById('termShellMount');
      return (host && host.__tcShell) || window.TinCanShell.instances[0] || null;
    }
    function execAeonikShellCommand(presetCmd) {
      const inst = _tcTerminalShell();
      if (!inst) return window.TinCanShell.run(presetCmd || '');
      return presetCmd ? inst.exec(presetCmd) : inst.submit();
    }
    function clearAeonikShell() { const inst = _tcTerminalShell(); if (inst) inst.clear(); }

    // Terminal window header + status bar (cwd, merkle, scope, drive). The files live in Space now.
    function termTickClock() {
      const el = document.getElementById('aeonikHeaderClock');
      if (el) el.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      window.TinCanShell.instances.forEach(i => i.refreshPrompt());
    }
    setInterval(termTickClock, 15000);

    async function refreshTerminalSpace() {
      termTickClock();
      const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
      try {
        const s = await termFetchSummary();
        set('aeonikHeaderCwd', '~/space · ' + termOwner());
        set('aeonikStatusCwd', '~/space · ' + termOwner());
        set('termStatusScope', termScope() + ' scope');
        set('aeonikGitBranch', 'merkle ' + String(s.merkle_root || '–').slice(0, 10));
      } catch (e) {
        set('aeonikStatusCwd', 'space unavailable: ' + e.message);
      }
      await termFetchDrive();
      set('termStatusDrive', termDrive.available ? 'drive: ' + (((termDrive.mirror && termDrive.mirror.places) || []).length) + ' places' : 'drive: off');
    }
    window.addEventListener('tincan:space-changed', () => {
      refreshTerminalSpace();
      if (typeof refreshAgentSpace === 'function') refreshAgentSpace('background');
    });

    // Auto-mount every container marked data-tc-shell-mount, then wire install cards to them.
    function tcInitShells() {
      document.querySelectorAll('[data-tc-shell-mount]').forEach(el => {
        window.TinCanShell.mount(el, { title: el.getAttribute('data-shell-title') || 'Shell' });
      });
      if (window.TinCanInstallCard) window.TinCanInstallCard.init();
    }
    tcInitShells();
    window.addEventListener('load', () => { setTimeout(refreshTerminalSpace, 2600); });
"""


def apply_shell_component(html: str) -> str:
    """Fill the shell script and CSS slots (idempotent)."""
    return html.replace(SHELL_JS_SLOT, SHELL_JS).replace(SHELL_CSS_SLOT, SHELL_CSS)
