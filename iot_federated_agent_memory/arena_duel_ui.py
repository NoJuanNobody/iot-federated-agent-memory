"""Two-brain Arena duel + per-brain context panel, rendered into every arena view.

``mesh_os_ui`` places a marker comment where a duel belongs
(``<!--ARENA_DUEL:<prefix>-->``); :func:`apply_arena_duel` swaps each marker
for :func:`render_arena_duel` with that prefix and injects the shared script
once. Every element id is prefixed, so the duel can live in win-arena
(``/arena``, the dock button, the launcher, pop-outs) and in win-quests at the
same time without duplicate ids. The win-quests prefix is ``arena``, which
keeps its historic ids (``arenaBattleBox``, ``arenaPromptInput``,
``arenaResultA`` ...).
"""

from __future__ import annotations

import html
import re

ARENA_VIEWS = (
    # (prefix, window id, label)
    ("arenaWin", "win-arena", "Arena"),
    ("arena", "win-quests", "Quests"),
)

# (side, colour, default model alias, default brain store)
_SIDES = (
    ("A", "emerald", "gemini-brain", "brain-a"),
    ("B", "cyan", "claude-brain", "brain-b"),
)

_MARKER_RE = re.compile(r"<!--ARENA_DUEL:([A-Za-z][A-Za-z0-9]*)-->")


def _brain_column(p: str, side: str, color: str, model: str, agent: str) -> str:
    return f"""
            <div class="arena-brain-slot p-3 bg-slate-900/90 rounded-lg border border-slate-800 flex flex-col gap-2" data-arena-slot="{side}" id="{p}Slot{side}">
              <div class="flex justify-between items-center pb-1.5 border-b border-slate-800 gap-2">
                <span class="font-bold text-xs text-{color}-300 font-mono">Brain {side}</span>
                <span id="{p}Label{side}" class="text-[10px] text-slate-400 font-mono truncate max-w-[200px]">{html.escape(model)}</span>
              </div>
              <div id="{p}Result{side}" class="text-xs font-mono text-slate-200 min-h-[90px] max-h-[200px] overflow-y-auto whitespace-pre-wrap bg-black/40 p-2.5 rounded" aria-live="polite">Click "Battle 2 Brains" to send the prompt to both brains.</div>
              <div id="{p}Bill{side}" class="text-[10px] font-mono text-slate-500 min-h-[12px]"></div>

              <div class="arena-ctx rounded border border-slate-800 bg-slate-950/70 p-2 space-y-2" id="{p}Ctx{side}">
                <div class="flex items-center justify-between gap-2">
                  <span class="text-[10px] uppercase tracking-wider text-slate-400 font-mono">Context used</span>
                  <label class="text-[10px] text-slate-400 font-mono flex items-center gap-1"><input type="checkbox" id="{p}UseCtx{side}" checked onchange="arenaCtxSaveSettings('{p}')"> use files</label>
                </div>
                <div id="{p}Used{side}" class="text-[11px] font-mono text-slate-400 space-y-1">No duel yet.</div>

                <div class="flex items-center gap-1.5 pt-1 border-t border-slate-800">
                  <span class="text-[10px] text-slate-500 font-mono shrink-0">Brain store</span>
                  <input id="{p}Agent{side}" value="{agent}" maxlength="48" onchange="arenaCtxAgentChanged('{p}','{side}')" class="flex-1 min-w-0 bg-slate-900 border border-slate-700 rounded px-1.5 py-0.5 text-[11px] text-{color}-300 font-mono" aria-label="Brain {side} store id">
                  <button type="button" onclick="arenaCtxRefresh('{p}','{side}')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-mono" title="Reload this brain's files">↻</button>
                </div>
                <div id="{p}Files{side}" class="max-h-[120px] overflow-y-auto text-[11px] font-mono text-slate-300 space-y-0.5"></div>
                <div id="{p}Viewer{side}" class="hidden max-h-[160px] overflow-y-auto whitespace-pre-wrap text-[10px] font-mono text-slate-300 bg-black/50 p-2 rounded border border-slate-800"></div>

                <div class="flex flex-wrap gap-1 text-[10px] font-mono">
                  <label class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 cursor-pointer">⬆ Upload<input type="file" multiple class="hidden" id="{p}Upload{side}" onchange="arenaCtxUpload('{p}','{side}', this)"></label>
                  <button type="button" onclick="arenaCtxTogglePaste('{p}','{side}')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200">✎ Paste</button>
                  <button type="button" onclick="arenaCtxImportSpace('{p}','{side}')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200" title="Copy the files in your own Agent Space into this brain">⇣ Import my Space</button>
                  <button type="button" id="{p}DriveBtn{side}" onclick="arenaCtxToggleDrive('{p}','{side}')" class="hidden px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200" title="Link files from your local drive mirror">⌂ Link drive</button>
                </div>
                <div id="{p}PasteBox{side}" class="hidden space-y-1">
                  <input id="{p}PasteName{side}" placeholder="notes.md" maxlength="120" class="w-full bg-slate-900 border border-slate-700 rounded px-1.5 py-0.5 text-[11px] text-white font-mono">
                  <textarea id="{p}PasteText{side}" rows="4" placeholder="Paste text this brain should know..." class="w-full bg-slate-900 border border-slate-700 rounded px-1.5 py-1 text-[11px] text-white font-mono"></textarea>
                  <button type="button" onclick="arenaCtxPaste('{p}','{side}')" class="w-full py-1 bg-slate-700 hover:bg-slate-600 text-white rounded text-[10px] font-mono">Add to Brain {side}</button>
                </div>
                <div id="{p}DriveBox{side}" class="hidden space-y-1">
                  <input id="{p}DrivePath{side}" placeholder="/dev/project/README.md or a folder" class="w-full bg-slate-900 border border-slate-700 rounded px-1.5 py-0.5 text-[11px] text-white font-mono">
                  <button type="button" onclick="arenaCtxLinkDrive('{p}','{side}')" class="w-full py-1 bg-slate-700 hover:bg-slate-600 text-white rounded text-[10px] font-mono">Link to Brain {side}</button>
                </div>
                <div id="{p}CtxMsg{side}" class="text-[10px] font-mono text-slate-500 min-h-[12px]" aria-live="polite"></div>
              </div>

              <div class="space-y-1.5 pt-1">
                <button id="{p}VoteBtn{side}" onclick="arenaDuelVote('{p}','{side}')" class="w-full py-1.5 bg-{color}-700/80 hover:bg-{color}-600 text-white font-semibold rounded text-xs transition active:scale-95 font-mono">🏆 Vote Brain {side} (+150 XP)</button>
                <button onclick="arenaDuelToSpace('{p}','{side}')" class="w-full py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[10px] font-mono flex items-center justify-center gap-1 border border-slate-700 transition active:scale-95" title="Copy this answer to your Agent Space and sandbox">🚀 Use in Agent Space &amp; Sandbox</button>
              </div>
            </div>"""


def render_arena_duel(prefix: str, view_label: str = "") -> str:
    """Duel markup for one arena view. All ids start with ``prefix``."""
    p = prefix
    (sa, ca, ma, _), (sb, cb, mb, _) = _SIDES
    columns = "".join(_brain_column(p, side, color, model, agent) for side, color, model, agent in _SIDES)
    return f"""
        <div id="{p}BattleBox" class="arena-duel bg-slate-950/90 border border-indigo-900/60 rounded-xl p-4 space-y-3" data-arena-view="{p}" data-arena-view-label="{html.escape(view_label)}">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 class="text-xs font-bold uppercase tracking-wider text-indigo-300 flex items-center gap-1.5"><span>⚔️</span> Side-by-Side AI Brain Arena Duel</h3>
              <p class="text-[11px] text-slate-400">Pick two chat models the router supports. Each brain answers with the files in its own store, and both sides are billed to your signed-in account. Vote for the better answer (+150 XP).</p>
            </div>
            <span id="{p}Account" role="button" tabindex="0" onclick="arenaCtxStatus(true)" title="Refresh sign-in and files" class="cursor-pointer text-[11px] font-mono text-cyan-400 bg-cyan-950/60 border border-cyan-800 px-2 py-0.5 rounded">Checking sign-in…</span>
          </div>

          <!-- Model A & Model B pickers: filled from /api/mesh/arena/models (what the AI router actually supports) -->
          <div class="aeonik-scope flex flex-col md:flex-row items-stretch md:items-center gap-2 pt-1">
            <div class="flex-1 min-w-0 bg-slate-900/70 border border-{ca}-900/60 rounded-lg p-2 flex items-center gap-2">
              <label for="{p}Model{sa}Input" class="text-[11px] font-mono text-{ca}-400 font-bold shrink-0">Model {sa}:</label>
              <select id="{p}Model{sa}Input" data-arena-picker="{sa}" onchange="arenaDuelModelChange('{p}')" class="flex-1 min-w-0 bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-{ca}-300 font-mono focus:border-{ca}-500 focus:outline-none">
                <option value="{ma}">{ma}</option>
              </select>
            </div>
            <button id="{p}SwapBtn" onclick="arenaDuelSwap('{p}')" title="Swap left and right models" aria-label="Swap models" class="self-center px-2 py-1 bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700 rounded-lg font-mono text-xs transition active:scale-95">⇄</button>
            <div class="flex-1 min-w-0 bg-slate-900/70 border border-{cb}-900/60 rounded-lg p-2 flex items-center gap-2">
              <label for="{p}Model{sb}Input" class="text-[11px] font-mono text-{cb}-400 font-bold shrink-0">Model {sb}:</label>
              <select id="{p}Model{sb}Input" data-arena-picker="{sb}" onchange="arenaDuelModelChange('{p}')" class="flex-1 min-w-0 bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-{cb}-300 font-mono focus:border-{cb}-500 focus:outline-none">
                <option value="{mb}">{mb}</option>
              </select>
            </div>
          </div>
          <div id="{p}ModelsNote" class="text-[10px] font-mono text-slate-500 -mt-1"></div>

          <div class="flex gap-2">
            <input id="{p}PromptInput" type="text" value="Summarize what my files say about deploying TinCan." class="flex-1 min-w-0 bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-xs text-white font-mono placeholder:text-slate-600" aria-label="Duel prompt" onkeydown="if(event.key==='Enter')arenaDuelRun('{p}')">
            <button id="{p}RunBtn" onclick="arenaDuelRun('{p}')" class="px-4 py-1.5 bg-gradient-to-r from-indigo-600 to-cyan-600 hover:brightness-110 text-white font-semibold rounded text-xs transition active:scale-95 shrink-0 flex items-center gap-1.5"><span>⚔️</span> <span>Battle 2 Brains</span></button>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">{columns}
          </div>
        </div>"""


ARENA_DUEL_SCRIPT = r"""
<script id="arenaDuelScript">
(function () {
  const VIEWS = __ARENA_VIEWS__;
  const SIDES = ['A', 'B'];
  const lastDuel = {};
  const MODELS_KEY = 'tincan_arena_models';   // shared with the #12 pickers
  let driveAllowed = false;
  let modelList = [];

  const el = (id) => document.getElementById(id);
  const peer = () => (typeof myPeerId !== 'undefined' ? myPeerId : (localStorage.getItem('tincan_peer_id') || ''));
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const agentOf = (p, side) => ((el(p + 'Agent' + side) || {}).value || ('brain-' + side.toLowerCase())).trim().toLowerCase();
  const modelOf = (p, side) => ((el(p + 'Model' + side + 'Input') || {}).value || '').trim();

  async function api(path, opts) {
    opts = opts || {};
    const headers = opts.body ? {'Content-Type': 'application/json'} : {};
    const res = await fetch(path, {method: opts.method || (opts.body ? 'POST' : 'GET'), headers, body: opts.body ? JSON.stringify(opts.body) : undefined, credentials: 'same-origin'});
    let data = {};
    try { data = await res.json(); } catch (e) { data = {error: 'Unexpected server response (' + res.status + ')'}; }
    if (!res.ok) { const err = new Error(data.error || ('HTTP ' + res.status)); err.status = res.status; err.data = data; throw err; }
    return data;
  }

  function msg(p, side, text, isError) {
    const m = el(p + 'CtxMsg' + side);
    if (m) { m.textContent = text || ''; m.className = 'text-[10px] font-mono min-h-[12px] ' + (isError ? 'text-rose-400' : 'text-slate-500'); }
  }

  function settingsKey(side) { return 'tincan_arena_brain_' + side; }
  function loadSettings() {
    SIDES.forEach((side) => {
      let st = {};
      try { st = JSON.parse(localStorage.getItem(settingsKey(side)) || '{}'); } catch (e) {}
      VIEWS.forEach((p) => {
        if (st.agent && el(p + 'Agent' + side)) el(p + 'Agent' + side).value = st.agent;
        if (typeof st.useCtx === 'boolean' && el(p + 'UseCtx' + side)) el(p + 'UseCtx' + side).checked = st.useCtx;
      });
    });
  }
  window.arenaCtxSaveSettings = function (p) {
    SIDES.forEach((side) => {
      const st = {agent: agentOf(p, side), useCtx: !!(el(p + 'UseCtx' + side) || {}).checked};
      localStorage.setItem(settingsKey(side), JSON.stringify(st));
      VIEWS.forEach((q) => {
        if (q === p) return;
        if (el(q + 'Agent' + side)) el(q + 'Agent' + side).value = st.agent;
        if (el(q + 'UseCtx' + side)) el(q + 'UseCtx' + side).checked = st.useCtx;
      });
    });
  };

  function labels(p) {
    SIDES.forEach((side) => { const l = el(p + 'Label' + side); if (l) l.textContent = modelOf(p, side) || ('Brain ' + side); });
  }

  // ---- model pickers (from /api/mesh/arena/models), mirrored across every view
  function setPair(pair) {
    try { localStorage.setItem(MODELS_KEY, JSON.stringify(pair)); } catch (e) {}
    VIEWS.forEach((q) => {
      const a = el(q + 'ModelAInput'), b = el(q + 'ModelBInput');
      if (a && pair.a) a.value = pair.a;
      if (b && pair.b) b.value = pair.b;
      labels(q);
    });
  }
  async function loadModels() {
    let data = null;
    try {
      const r = await fetch('/api/mesh/arena/models');
      if (!r.ok) throw new Error('HTTP ' + r.status);
      data = await r.json();
    } catch (err) {
      VIEWS.forEach((q) => { const n = el(q + 'ModelsNote'); if (n) n.textContent = "Couldn't load the model list (" + err.message + '); using the default brains.'; labels(q); });
      return;
    }
    modelList = data.models || [];
    const groups = {configured: 'Configured brains', catalog: 'Router catalog'};
    const optionsHtml = Object.entries(groups).map(([kind, label]) => {
      const opts = modelList.filter((m) => m.kind === kind)
        .map((m) => '<option value="' + esc(m.id) + '" title="' + esc(m.secondary || m.id) + '">' + esc(m.name || m.id) + (m.secondary && m.secondary !== m.name ? ' \u00b7 ' + esc(m.secondary) : '') + '</option>').join('');
      return opts ? '<optgroup label="' + label + '">' + opts + '</optgroup>' : '';
    }).join('');
    VIEWS.forEach((q) => {
      ['A', 'B'].forEach((side) => { const sel = el(q + 'Model' + side + 'Input'); if (sel) sel.innerHTML = optionsHtml; });
      const n = el(q + 'ModelsNote');
      if (n) n.textContent = modelList.length + ' models from the AI router. Sign in to duel: each side is billed to your own account at the model\'s real cost.';
    });
    let saved = null;
    try { saved = JSON.parse(localStorage.getItem(MODELS_KEY) || 'null'); } catch (e) {}
    const ids = new Set(modelList.map((m) => m.id));
    const def = data.default || {a: 'gemini-brain', b: 'claude-brain'};
    setPair({a: saved && ids.has(saved.a) ? saved.a : def.a, b: saved && ids.has(saved.b) ? saved.b : def.b});
  }
  window.arenaDuelModelChange = function (p) { setPair({a: modelOf(p, 'A'), b: modelOf(p, 'B')}); };
  window.arenaDuelSwap = function (p) { setPair({a: modelOf(p, 'B'), b: modelOf(p, 'A')}); };
  window.arenaDuelLabels = function (p) { labels(p); };

  function renderFiles(p, side, data) {
    const box = el(p + 'Files' + side);
    if (!box) return;
    const files = data.files || [];
    if (!files.length) { box.innerHTML = '<div class="text-slate-500">No files yet. Upload, paste or import some.</div>'; return; }
    box.innerHTML = files.map((f) => {
      const stale = f.source === 'drive' && f.drive_available === false ? ' <span class="text-amber-400" title="Drive mirror is off; using the last copy">(snapshot)</span>' : '';
      return '<div class="flex items-center gap-1 group" data-ctx-file="' + esc(f.path) + '">' +
        '<button type="button" class="flex-1 min-w-0 text-left truncate hover:text-white" data-act="view">' + esc(f.path) + '</button>' +
        '<span class="text-slate-500 shrink-0">' + esc(f.source) + ' · ' + esc(f.chunk_count) + 'ch</span>' + stale +
        '<button type="button" class="text-rose-400 hover:text-rose-300 shrink-0 px-1" data-act="del" title="Remove from this brain">✕</button></div>';
    }).join('');
    box.querySelectorAll('[data-ctx-file]').forEach((row) => {
      const path = row.getAttribute('data-ctx-file');
      row.querySelector('[data-act="view"]').onclick = () => window.arenaCtxView(p, side, path);
      row.querySelector('[data-act="del"]').onclick = () => window.arenaCtxDelete(p, side, path);
    });
  }

  function renderUsed(p, side, sideResult) {
    const box = el(p + 'Used' + side);
    if (!box) return;
    const ctx = (sideResult && sideResult.context) || null;
    if (!ctx) { box.textContent = 'No duel yet.'; return; }
    if (!ctx.enabled) { box.innerHTML = '<div class="text-slate-500">Files were switched off for this answer.</div>'; return; }
    const snips = ctx.snippets || [];
    if (!snips.length) { box.innerHTML = '<div class="text-slate-500">No file in this brain matched the prompt.</div>'; return; }
    box.innerHTML = '<div class="text-slate-500">' + esc(ctx.files.length) + ' file(s), ' + esc(snips.length) + ' snippet(s), ~' + esc(ctx.tokens) + ' tokens</div>' +
      snips.map((s) => '<details class="arena-snippet border border-slate-800 rounded px-1.5 py-1"><summary class="cursor-pointer truncate"><span class="text-slate-200">' + esc(s.path) + '</span> <span class="text-slate-500">#' + esc(s.chunk) + ' · ' + esc(s.source) + ' · score ' + esc(s.score) + '</span></summary><div class="whitespace-pre-wrap text-[10px] text-slate-300 pt-1">' + esc(s.text) + '</div></details>').join('');
  }

  async function refresh(p, side) {
    const agent = agentOf(p, side);
    try {
      const data = await api('/api/arena/context/files?agent_id=' + encodeURIComponent(agent));
      renderFiles(p, side, data);
      msg(p, side, data.count + ' file(s) · ' + data.chunk_count + ' chunk(s) in ' + agent);
    } catch (e) {
      const box = el(p + 'Files' + side); if (box) box.innerHTML = '';
      msg(p, side, e.message, true);
    }
  }
  window.arenaCtxRefresh = function (p, side) { return refresh(p, side); };
  function refreshEverywhere(side, agent) {
    VIEWS.forEach((q) => { if (el(q + 'BattleBox') && agentOf(q, side) === agent) refresh(q, side); });
  }

  window.arenaCtxAgentChanged = function (p, side) {
    const input = el(p + 'Agent' + side);
    input.value = input.value.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '-').replace(/^[-_]+/, '').slice(0, 48) || ('brain-' + side.toLowerCase());
    window.arenaCtxSaveSettings(p);
    VIEWS.forEach((q) => refresh(q, side));
  };

  window.arenaCtxView = async function (p, side, path) {
    const v = el(p + 'Viewer' + side);
    try {
      const f = await api('/api/arena/context/file?agent_id=' + encodeURIComponent(agentOf(p, side)) + '&path=' + encodeURIComponent(path));
      v.textContent = f.path + '  (' + f.size_bytes + ' bytes, ' + f.chunk_count + ' chunks)\n\n' + (f.content || '');
      v.classList.remove('hidden');
    } catch (e) { msg(p, side, e.message, true); }
  };

  window.arenaCtxDelete = async function (p, side, path) {
    if (!confirm('Remove ' + path + ' from ' + agentOf(p, side) + '?')) return;
    try {
      await api('/api/arena/context/delete', {body: {agent_id: agentOf(p, side), path}});
      const v = el(p + 'Viewer' + side); if (v) v.classList.add('hidden');
      refreshEverywhere(side, agentOf(p, side));
    } catch (e) { msg(p, side, e.message, true); }
  };

  function reportIngest(p, side, data) {
    const added = (data.added || []).length;
    const errs = (data.errors || []).map((x) => x.name + ': ' + x.error).join('; ');
    msg(p, side, 'Added ' + added + ' file(s)' + (errs ? ' · ' + errs : ''), !!errs && !added);
    refreshEverywhere(side, agentOf(p, side));
  }

  function fileToB64(file) {
    return new Promise((resolve, reject) => {
      const r = new FileReader();
      r.onload = () => resolve(String(r.result).split(',')[1] || '');
      r.onerror = () => reject(r.error);
      r.readAsDataURL(file);
    });
  }

  window.arenaCtxUpload = async function (p, side, input) {
    const files = Array.from(input.files || []);
    input.value = '';
    if (!files.length) return;
    msg(p, side, 'Uploading ' + files.length + ' file(s)…');
    try {
      const payload = [];
      for (const f of files.slice(0, 50)) {
        if (f.size > 16 * 1024 * 1024) { msg(p, side, f.name + ' is too large', true); continue; }
        payload.push({name: f.name, content_b64: await fileToB64(f), source: 'upload'});
      }
      if (!payload.length) return;
      reportIngest(p, side, await api('/api/arena/context/ingest', {body: {agent_id: agentOf(p, side), files: payload}}));
    } catch (e) { msg(p, side, e.message + (e.data && e.data.errors ? ' · ' + e.data.errors.map((x) => x.error).join('; ') : ''), true); }
  };

  window.arenaCtxTogglePaste = function (p, side) { const b = el(p + 'PasteBox' + side); if (b) b.classList.toggle('hidden'); };
  window.arenaCtxToggleDrive = function (p, side) { const b = el(p + 'DriveBox' + side); if (b) b.classList.toggle('hidden'); };

  window.arenaCtxPaste = async function (p, side) {
    const name = (el(p + 'PasteName' + side).value || '').trim() || ('note-' + new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-') + '.md');
    const text = el(p + 'PasteText' + side).value || '';
    if (!text.trim()) { msg(p, side, 'Paste some text first.', true); return; }
    try {
      const data = await api('/api/arena/context/ingest', {body: {agent_id: agentOf(p, side), files: [{name, content: text, source: 'paste'}]}});
      el(p + 'PasteText' + side).value = '';
      reportIngest(p, side, data);
    } catch (e) { msg(p, side, e.message + (e.data && e.data.errors ? ' · ' + e.data.errors.map((x) => x.error).join('; ') : ''), true); }
  };

  window.arenaCtxImportSpace = async function (p, side) {
    msg(p, side, 'Importing your Agent Space…');
    try { reportIngest(p, side, await api('/api/arena/context/import', {body: {agent_id: agentOf(p, side), space_owner: peer()}})); }
    catch (e) { msg(p, side, e.message, true); }
  };

  window.arenaCtxLinkDrive = async function (p, side) {
    const path = (el(p + 'DrivePath' + side).value || '').trim();
    if (!path) { msg(p, side, 'Enter a drive path.', true); return; }
    try { reportIngest(p, side, await api('/api/arena/context/drive/link', {body: {agent_id: agentOf(p, side), drive_path: path}})); }
    catch (e) { msg(p, side, e.message, true); }
  };

  async function status(promptSignIn) {
    try {
      const s = await api('/api/arena/context/status');
      driveAllowed = !!(s.drive_mirror && s.drive_mirror.allowed_here);
      VIEWS.forEach((p) => {
        const a = el(p + 'Account');
        if (a) a.textContent = 'Billed to ' + (s.account.username || s.account.peer_id) + ' · ' + s.account.token_balance + ' tokens';
        SIDES.forEach((side) => { const b = el(p + 'DriveBtn' + side); if (b) b.classList.toggle('hidden', !driveAllowed); });
      });
      VIEWS.forEach((p) => SIDES.forEach((side) => refresh(p, side)));
    } catch (e) {
      VIEWS.forEach((p) => {
        const a = el(p + 'Account');
        if (a) a.textContent = e.status === 401 || e.status === 403 ? 'Sign in to duel' : 'Arena offline';
        SIDES.forEach((side) => msg(p, side, e.message, true));
      });
      if (promptSignIn === true && (e.status === 401 || e.status === 403) && typeof openAccountModal === 'function') { try { openAccountModal(false); } catch (x) {} }
    }
  }
  window.arenaCtxStatus = status;

  function sayBoth(p, text) { SIDES.forEach((side) => { el(p + 'Result' + side).textContent = text; }); }

  window.arenaDuelRun = async function (p) {
    if (typeof initAudio === 'function') { try { initAudio(); } catch (e) {} }
    const prompt = (el(p + 'PromptInput').value || '').trim();
    if (!prompt) return;
    const btn = el(p + 'RunBtn');
    if (btn) btn.disabled = true;
    lastDuel[p] = null;
    const models = {A: modelOf(p, 'A'), B: modelOf(p, 'B')};
    SIDES.forEach((side) => {
      el(p + 'Result' + side).textContent = 'Brain ' + side + ' (' + models[side] + ') is reading ' + agentOf(p, side) + '…';
      el(p + 'Bill' + side).textContent = '';
      if (typeof spawnPacketFlight === 'function') { try { spawnPacketFlight(peer(), models[side], 'ai_prompt', models[side]); } catch (e) {} }
    });
    try {
      // 1) Open a match for the signed-in account (server session), 2) run each side against it.
      let match;
      try {
        match = (await api('/api/mesh/arena/match', {body: {model_a: models.A, model_b: models.B, prompt}})).match;
      } catch (e) {
        if (e.status === 401) {
          sayBoth(p, 'Sign in to duel. Brain Arena duels are billed to your own account.');
          if (typeof openAccountModal === 'function') { try { openAccountModal(false); } catch (x) {} }
        } else if (e.status === 402) {
          sayBoth(p, (e.message || 'Not enough tokens for this duel.') + ' Top up or watch a sponsor ad to continue.');
        } else {
          sayBoth(p, 'Battle error: ' + e.message);
        }
        return;
      }
      const results = {};
      // Sequential on purpose: side B is checked against the balance left after side A.
      for (const side of SIDES) {
        try {
          results[side] = await api('/api/chat', {body: {
            model: models[side], prompt, arena: true, match_id: match.match_id, arena_side: side,
            agent_id: agentOf(p, side), use_context: !!(el(p + 'UseCtx' + side) || {}).checked,
          }});
          const r = results[side];
          el(p + 'Result' + side).textContent = (r.choices && r.choices[0] && r.choices[0].message && r.choices[0].message.content) || r.text || '(empty answer)';
          const b = r.billing;
          el(p + 'Bill' + side).textContent = b ? ('Billed to you: ' + b.tokens_billed + ' tokens · $' + Number(b.cost_usd || 0).toFixed(6) + (String(r.id || '').indexOf('sim-') === 0 ? ' · simulated (no API key)' : '')) : '';
          renderUsed(p, side, {context: r.arena_context});
        } catch (e) {
          el(p + 'Result' + side).textContent = e.status === 402 ? ((e.message || 'Not enough tokens for this side.') + ' Top up to continue.') : ('Brain ' + side + ' error: ' + e.message);
        }
      }
      if (results.A && results.B) {
        lastDuel[p] = {a: models.A, b: models.B, prompt, match_id: match.match_id};
        const total = (results.B.billing && results.B.billing.match_total_cost_usd) || 0;
        if (typeof showQuickNotification === 'function') showQuickNotification('Duel billed to your account: $' + Number(total).toFixed(6) + ' (' + match.match_id.slice(0, 14) + '…)');
      }
      status();
    } finally {
      if (btn) btn.disabled = false;
    }
  };

  window.arenaDuelVote = async function (p, side) {
    if (typeof initAudio === 'function') { try { initAudio(); } catch (e) {} }
    const duel = lastDuel[p];
    if (!duel || !duel.match_id) {
      if (typeof showQuickNotification === 'function') showQuickNotification('Run a duel first: votes are recorded against a billed match.');
      return;
    }
    const winnerSide = side === 'B' ? 'B' : 'A';
    const winnerModel = winnerSide === 'A' ? duel.a : duel.b;
    if (typeof playXpChime === 'function') { try { playXpChime(); } catch (e) {} }
    try {
      await api('/api/mesh/arena/vote', {body: {
        match_id: duel.match_id, winner_side: winnerSide, prompt_preview: (duel.prompt || '').substring(0, 40),
        display_name: peer(), room: (typeof currentRoom !== 'undefined' ? currentRoom : 'main'),
      }});
      if (typeof showQuickNotification === 'function') showQuickNotification('🏆 Vote recorded for ' + winnerModel + ' (' + duel.a + ' vs ' + duel.b + '). +150 XP.');
      if (typeof pollMeshState === 'function') pollMeshState();
    } catch (e) {
      if (typeof showQuickNotification === 'function') showQuickNotification('Vote error: ' + e.message);
    }
  };

  window.arenaDuelToSpace = function (p, side) {
    const content = (el(p + 'Result' + side) || {}).innerText || '';
    if (!content) return;
    const editor = el('agentspaceEditor');
    if (editor) editor.value = content;
    if (typeof setViewerEditMode === 'function') { try { setViewerEditMode(); } catch (e) {} }
    if (typeof toggleWindow === 'function') toggleWindow('win-agentspace');
    if (typeof showQuickNotification === 'function') showQuickNotification('Sent Brain ' + side + ' output to your Agent Space');
  };

  // Backward-compatible entry points (the win-quests markup and older code used these names).
  window.runArenaBattle = () => window.arenaDuelRun('arena');
  window.voteArenaWinner = (side) => window.arenaDuelVote('arena', side === 'B' ? 'B' : 'A');
  window.updateArenaModelLabels = () => window.arenaDuelLabels('arena');
  window.onArenaModelChange = () => window.arenaDuelModelChange('arena');
  window.swapArenaModels = () => window.arenaDuelSwap('arena');
  window.loadArenaModels = () => loadModels();
  window.sendArenaResultToSpace = (side) => window.arenaDuelToSpace('arena', side === 'B' ? 'B' : 'A');

  function boot() {
    loadSettings();
    loadModels();
    status();
    // Re-check after sign-in / account creation in another tab or the account modal.
    window.addEventListener('focus', () => status());
    window.addEventListener('storage', (ev) => { if (ev.key && ev.key.indexOf('tincan_') === 0) status(); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
</script>
"""


def apply_arena_duel(page: str) -> str:
    """Replace every ``<!--ARENA_DUEL:prefix-->`` marker and add the script once."""
    labels = {p: label for p, _win, label in ARENA_VIEWS}
    prefixes = []

    def _sub(m: "re.Match[str]") -> str:
        p = m.group(1)
        prefixes.append(p)
        return render_arena_duel(p, labels.get(p, p))

    page = _MARKER_RE.sub(_sub, page)
    if prefixes and 'id="arenaDuelScript"' not in page:
        import json as _json
        script = ARENA_DUEL_SCRIPT.replace("__ARENA_VIEWS__", _json.dumps(prefixes))
        end = page.rfind("</body>")
        page = page[:end] + script + page[end:] if end != -1 else page + script
    return page
