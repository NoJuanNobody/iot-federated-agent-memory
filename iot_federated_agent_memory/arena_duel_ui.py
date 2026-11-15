"""Two-brain Arena duel + per-brain context panel, rendered into every arena view.

``mesh_os_ui`` places a marker comment where a duel belongs
(``<!--ARENA_DUEL:<prefix>-->``); :func:`apply_arena_duel` swaps each marker
for :func:`render_arena_duel` with that prefix and injects the shared script
once. Every element id is prefixed, so the duel can live in win-arena
(``/arena``, the dock button, the launcher, pop-outs) and in win-quests at the
same time without duplicate ids. The win-quests prefix is ``arena``, which
keeps its historic ids (``arenaBattleBox``, ``arenaPromptInput``,
``arenaResultA`` ...).

Styled with TinCan's Aeonik Celadon & Ink design tokens (``#ecf1e6``,
``#f4f8f0``, ``#ffffff``, ``#111111``, plus surgical ``#107a47`` / ``#8a1c1c``
inline telemetry accents).
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
            <div class="arena-brain-slot p-3 bg-[#ffffff] text-[#111111] rounded-xl border border-[#111111] flex flex-col gap-2" data-arena-slot="{side}" id="{p}Slot{side}">
              <div class="flex flex-wrap justify-between items-center pb-1.5 border-b border-[#111111]/15 gap-2">
                <div class="flex items-center gap-1.5 min-w-0">
                  <span class="font-bold text-xs text-[#111111] font-mono uppercase tracking-wider shrink-0">Brain {side}</span>
                  <span class="text-[#5c5c5c] font-mono text-xs shrink-0">·</span>
                  <span id="{p}Label{side}" class="text-[11px] text-[#4a4a4a] font-mono truncate max-w-[180px]">{html.escape(model)}</span>
                  <span id="{p}TierTag{side}" class="text-[9px] font-mono uppercase tracking-wider px-1.5 py-0.5 rounded-full border border-[#111111]/30 bg-[#f4f8f0] text-[#4a4a4a] shrink-0">CLOUD</span>
                </div>
                <div id="{p}Bill{side}" class="text-[10px] font-mono text-[#4a4a4a] min-h-[12px] text-right"></div>
              </div>
              <div id="{p}Result{side}" class="text-xs font-mono text-[#111111] min-h-[96px] max-h-[210px] overflow-y-auto whitespace-pre-wrap bg-[#f4f8f0] border border-[#111111]/20 p-2.5 rounded-lg" aria-live="polite">Click "Run Arena" to send the prompt to both brains.</div>
              <div id="{p}Savings{side}" class="text-[10px] font-mono text-[#4a4a4a] bg-[#ffffff] border border-[#111111]/25 rounded-lg px-2 py-1 min-h-[22px] flex items-center justify-between gap-2">Awaiting duel telemetry · cost delta &amp; TTFT</div>

              <div class="arena-ctx rounded-lg border border-[#111111]/25 bg-[#f4f8f0] p-2.5 space-y-2" id="{p}Ctx{side}">
                <div class="flex items-center justify-between gap-2">
                  <span class="text-[10px] uppercase tracking-wider text-[#4a4a4a] font-mono font-semibold">Context used</span>
                  <label class="text-[10px] text-[#4a4a4a] font-mono flex items-center gap-1 cursor-pointer"><input type="checkbox" id="{p}UseCtx{side}" class="accent-[#111111]" checked onchange="arenaCtxSaveSettings('{p}')"> use files</label>
                </div>
                <div id="{p}Used{side}" class="text-[11px] font-mono text-[#4a4a4a] space-y-1">No duel yet.</div>

                <div class="flex items-center gap-1.5 pt-1 border-t border-[#111111]/15">
                  <span class="text-[10px] text-[#5c5c5c] font-mono shrink-0">Brain store</span>
                  <input id="{p}Agent{side}" value="{agent}" maxlength="48" onchange="arenaCtxAgentChanged('{p}','{side}')" class="flex-1 min-w-0 bg-[#ffffff] border border-[#111111]/40 rounded px-1.5 py-0.5 text-[11px] text-[#111111] font-mono" aria-label="Brain {side} store id">
                  <button type="button" onclick="arenaCtxRefresh('{p}','{side}')" class="px-2 py-0.5 rounded-full bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border border-[#111111]/40 text-[10px] font-mono transition" title="Reload this brain's files">↻</button>
                </div>
                <div id="{p}Files{side}" class="max-h-[140px] overflow-y-auto text-[11px] font-mono text-[#111111] space-y-1"></div>
                <div id="{p}Viewer{side}" class="hidden max-h-[190px] overflow-y-auto text-[10px] font-mono text-[#111111] bg-[#ffffff] p-2 rounded border border-[#111111]/30 space-y-1.5"></div>
                <div id="{p}EditBox{side}" class="hidden space-y-1.5 bg-[#ffffff] border border-[#111111]/40 rounded p-2">
                  <div class="flex items-center justify-between gap-2">
                    <span id="{p}EditPathLabel{side}" class="text-[10px] font-mono font-bold text-[#111111] truncate">/path</span>
                    <button type="button" onclick="arenaCtxCancelEdit('{p}','{side}')" class="text-[10px] font-mono text-[#5c5c5c] hover:text-[#111111]">Cancel</button>
                  </div>
                  <input id="{p}EditDesc{side}" placeholder="Context description / summary..." maxlength="280" class="w-full bg-[#f4f8f0] border border-[#111111]/40 rounded px-1.5 py-0.5 text-[11px] text-[#111111] font-mono">
                  <textarea id="{p}EditText{side}" rows="4" placeholder="Edit file content..." class="w-full bg-[#f4f8f0] border border-[#111111]/40 rounded px-1.5 py-1 text-[11px] text-[#111111] font-mono"></textarea>
                  <button type="button" onclick="arenaCtxSaveEdit('{p}','{side}')" class="w-full py-1 bg-[#111111] hover:bg-[#333333] text-[#ecf1e6] rounded-full text-[10px] font-mono font-semibold">Save Context Update</button>
                </div>

                <div class="flex flex-wrap gap-1 text-[10px] font-mono">
                  <label class="px-2 py-0.5 rounded-full bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border border-[#111111]/40 cursor-pointer transition">⬆ Upload<input type="file" multiple class="hidden" id="{p}Upload{side}" onchange="arenaCtxUpload('{p}','{side}', this)"></label>
                  <button type="button" onclick="arenaCtxTogglePaste('{p}','{side}')" class="px-2 py-0.5 rounded-full bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border border-[#111111]/40 transition">✎ Paste</button>
                  <button type="button" onclick="arenaCtxImportSpace('{p}','{side}')" class="px-2 py-0.5 rounded-full bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border border-[#111111]/40 transition" title="Copy the files in your own Workstation Space into this brain">⇣ Import Space</button>
                  <button type="button" id="{p}DriveBtn{side}" onclick="arenaCtxToggleDrive('{p}','{side}')" class="hidden px-2 py-0.5 rounded-full bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border border-[#111111]/40 transition" title="Link files from your local drive mirror">⌂ Link drive</button>
                </div>
                <div id="{p}PasteBox{side}" class="hidden space-y-1">
                  <input id="{p}PasteName{side}" placeholder="notes.md" maxlength="120" class="w-full bg-[#ffffff] border border-[#111111]/40 rounded px-1.5 py-0.5 text-[11px] text-[#111111] font-mono">
                  <input id="{p}PasteDesc{side}" placeholder="Short description (optional)" maxlength="280" class="w-full bg-[#ffffff] border border-[#111111]/40 rounded px-1.5 py-0.5 text-[11px] text-[#111111] font-mono">
                  <textarea id="{p}PasteText{side}" rows="4" placeholder="Paste text this brain should know..." class="w-full bg-[#ffffff] border border-[#111111]/40 rounded px-1.5 py-1 text-[11px] text-[#111111] font-mono"></textarea>
                  <button type="button" onclick="arenaCtxPaste('{p}','{side}')" class="w-full py-1 bg-[#111111] hover:bg-[#333333] text-[#ecf1e6] rounded-full text-[10px] font-mono font-semibold">Add to Brain {side}</button>
                </div>
                <div id="{p}DriveBox{side}" class="hidden space-y-1">
                  <input id="{p}DrivePath{side}" placeholder="/dev/project/README.md or a folder" class="w-full bg-[#ffffff] border border-[#111111]/40 rounded px-1.5 py-0.5 text-[11px] text-[#111111] font-mono">
                  <button type="button" onclick="arenaCtxLinkDrive('{p}','{side}')" class="w-full py-1 bg-[#111111] hover:bg-[#333333] text-[#ecf1e6] rounded-full text-[10px] font-mono font-semibold">Link to Brain {side}</button>
                </div>
                <div id="{p}CtxMsg{side}" class="text-[10px] font-mono text-[#4a4a4a] min-h-[12px]" aria-live="polite"></div>
              </div>

              <div class="pt-1">
                <button type="button" id="{p}VoteBtn{side}" onclick="arenaDuelVote('{p}','{side}')" class="w-full py-1.5 px-3 bg-[#111111] hover:bg-[#333333] text-[#ecf1e6] font-semibold rounded-full text-xs transition active:scale-95 font-mono border border-[#111111]">🏆 Vote Brain {side} (+150 XP)</button>
              </div>
            </div>"""


def render_arena_duel(prefix: str, view_label: str = "") -> str:
    """Duel markup for one arena view. All ids start with ``prefix``."""
    p = prefix
    (sa, ca, ma, _), (sb, cb, mb, _) = _SIDES
    columns = "".join(_brain_column(p, side, color, model, agent) for side, color, model, agent in _SIDES)
    return f"""
        <div id="{p}BattleBox" class="arena-duel bg-[#f4f8f0] text-[#111111] border border-[#111111] rounded-xl p-4 space-y-3" data-arena-view="{p}" data-arena-view-label="{html.escape(view_label)}">
          <div class="flex flex-wrap items-center justify-between gap-2 pb-1 border-b border-[#111111]/15">
            <div class="space-y-0.5">
              <div class="flex flex-wrap items-center gap-2">
                <h3 class="text-xs font-bold uppercase tracking-wider text-[#111111] flex items-center gap-1.5"><span>⚔️</span> AI Brain Arena · Blind Multi-Model Duel</h3>
                <span class="px-2 py-0.5 rounded-full bg-[#111111] text-[#ecf1e6] text-[10px] font-mono font-semibold uppercase tracking-wider">BLIND DUEL</span>
                <span class="text-[11px] font-mono text-[#4a4a4a]">+150 XP per vote · ad-supported credits</span>
              </div>
              <p class="text-[11px] text-[#4a4a4a]">Pick two chat models, load shared or per-brain context (Workstation, Drive, or Context Palace), click Run Arena — the floating vote modal pops up in the bottom corner once a run finishes (+150 XP).</p>
            </div>
            <span id="{p}Account" role="button" tabindex="0" onclick="arenaCtxStatus(true)" title="Refresh sign-in and files" class="cursor-pointer text-[11px] font-mono text-[#111111] bg-[#ffffff] border border-[#111111] hover:bg-[#111111] hover:text-[#ecf1e6] px-2.5 py-1 rounded-full transition">Checking sign-in…</span>
          </div>

          <div class="bg-[#ffffff] border border-[#111111] rounded-xl p-3 space-y-2.5">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <span class="text-[10px] font-mono uppercase tracking-wider text-[#4a4a4a] font-semibold">ARENA PROMPT, CONTEXT INVENTORY &amp; PALACE</span>
              <div class="flex flex-wrap items-center gap-1.5">
                <span id="{p}RagBadge" class="inline-flex items-center px-2.5 py-0.5 rounded-full bg-[#ecf1e6] text-[#111111] border border-[#111111] text-[10px] font-mono">RAG: .space (ready)</span>
                <span id="{p}PreAuthCap" class="inline-flex items-center px-2.5 py-0.5 rounded-full bg-[#ecf1e6] text-[#107a47] border border-[#107a47] text-[10px] font-mono font-semibold">PRE-AUTH CAP: 533 TOK/SIDE MAX</span>
              </div>
            </div>

            <div class="flex flex-wrap items-center justify-between gap-2">
              <div class="flex flex-wrap items-center gap-1.5">
                <button type="button" id="{p}PresetLocalCloudBtn" onclick="arenaPresetLocalVsCloud('{p}')" class="px-3 py-1 rounded-full bg-[#ecf1e6] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border border-[#111111] text-[10px] font-mono font-semibold transition active:scale-95" title="Arm a zero-burn local or open-weight model on Brain A against a frontier cloud model on Brain B">⚡ Local vs Cloud Preset</button>
                <button type="button" id="{p}BothToggleBtn" onclick="arenaCtxToggleBoth('{p}')" class="px-2.5 py-1 rounded-full bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border border-[#111111] text-[10px] font-mono font-semibold transition">➕ Add Context to Both</button>
                <button type="button" id="{p}InventoryBtn" onclick="arenaCtxToggleInventory('{p}')" class="px-2.5 py-1 rounded-full bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border border-[#111111] text-[10px] font-mono font-semibold transition">📦 Universal Inventory</button>
                <button type="button" id="{p}PalaceBtn" onclick="arenaCtxTogglePalace('{p}')" class="px-2.5 py-1 rounded-full bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border border-[#111111] text-[10px] font-mono font-semibold transition">🏛️ Context Palace</button>
                <button type="button" id="{p}ImportBothBtn" onclick="arenaCtxImportBoth('{p}')" class="px-2.5 py-1 rounded-full bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border border-[#111111] text-[10px] font-mono transition" title="Copy Workstation Space files to BOTH Brain A and Brain B">⇣ Space → Both</button>
              </div>
              <span id="{p}PresetStatus" class="text-[10px] font-mono text-[#4a4a4a]">Compare local Ollama / open-weight vs frontier cloud</span>
            </div>

            <div id="{p}BothBox" class="hidden rounded-lg border border-[#111111]/40 bg-[#f4f8f0] p-2.5 space-y-1.5">
              <div class="flex flex-wrap items-center justify-between gap-2">
                <span class="text-[10px] font-mono font-bold uppercase tracking-wider text-[#111111]">Add Context to Both Brain A &amp; Brain B at Once</span>
                <label class="px-2 py-0.5 rounded-full bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border border-[#111111] text-[10px] font-mono cursor-pointer transition">⬆ Upload File(s) to Both<input type="file" multiple class="hidden" id="{p}BothUpload" onchange="arenaCtxUploadBoth('{p}', this)"></label>
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                <input id="{p}BothName" placeholder="/shared/context.md" maxlength="120" class="w-full bg-[#ffffff] border border-[#111111]/40 rounded px-2 py-1 text-[11px] text-[#111111] font-mono">
                <input id="{p}BothDesc" placeholder="Short description (what is in this context)" maxlength="280" class="w-full bg-[#ffffff] border border-[#111111]/40 rounded px-2 py-1 text-[11px] text-[#111111] font-mono">
              </div>
              <textarea id="{p}BothText" rows="3" placeholder="Paste context document or notes to inject into BOTH brains simultaneously..." class="w-full bg-[#ffffff] border border-[#111111]/40 rounded px-2 py-1 text-[11px] text-[#111111] font-mono"></textarea>
              <div class="flex items-center justify-between gap-2">
                <span id="{p}BothMsg" class="text-[10px] font-mono text-[#4a4a4a]"></span>
                <button type="button" id="{p}BothSaveBtn" onclick="arenaCtxPasteBoth('{p}')" class="px-3 py-1 bg-[#111111] hover:bg-[#333333] text-[#ecf1e6] rounded-full text-[10px] font-mono font-semibold">Add to Both Brains</button>
              </div>
            </div>

            <div id="{p}InventoryBox" class="hidden rounded-lg border border-[#111111]/40 bg-[#f4f8f0] p-2.5 space-y-2">
              <div class="flex flex-wrap items-center justify-between gap-2">
                <span class="text-[10px] font-mono font-bold uppercase tracking-wider text-[#111111]">Universal System Context Inventory</span>
                <div class="flex items-center gap-1.5">
                  <input id="{p}InvSearch" placeholder="Filter inventory by path or description..." oninput="arenaCtxLoadInventory('{p}')" class="w-48 sm:w-64 bg-[#ffffff] border border-[#111111]/40 rounded px-2 py-0.5 text-[11px] text-[#111111] font-mono">
                  <button type="button" onclick="arenaCtxLoadInventory('{p}')" class="px-2 py-0.5 rounded-full bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] border border-[#111111]/40 text-[10px] font-mono">↻</button>
                </div>
              </div>
              <div id="{p}InvStats" class="text-[10px] font-mono text-[#4a4a4a]">Click ↻ to load Brain A, Brain B, Workstation .space, Context Palace &amp; Drive Mirror items.</div>
              <div id="{p}InvList" class="max-h-[180px] overflow-y-auto space-y-1 text-[11px] font-mono"></div>
            </div>

            <div id="{p}PalaceBox" class="hidden rounded-lg border border-[#111111]/40 bg-[#f4f8f0] p-2.5 space-y-2">
              <div class="flex flex-wrap items-center justify-between gap-2">
                <span class="text-[10px] font-mono font-bold uppercase tracking-wider text-[#111111]">Context Palace Memory Lake (CRUD + Import)</span>
                <div class="flex items-center gap-1.5">
                  <input id="{p}PalaceSearch" placeholder="Search Palace concepts..." oninput="arenaCtxLoadPalace('{p}')" class="w-44 bg-[#ffffff] border border-[#111111]/40 rounded px-2 py-0.5 text-[11px] text-[#111111] font-mono">
                  <button type="button" onclick="arenaCtxImportPalace('{p}', 'both')" class="px-2.5 py-0.5 rounded-full bg-[#111111] hover:bg-[#333333] text-[#ecf1e6] text-[10px] font-mono font-semibold">Import All → Both</button>
                </div>
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-1.5">
                <input id="{p}PalaceName" placeholder="Concept title (e.g. FAU Architecture)" class="bg-[#ffffff] border border-[#111111]/40 rounded px-2 py-0.5 text-[11px] text-[#111111] font-mono">
                <input id="{p}PalaceCategory" placeholder="Category (knowledge)" class="bg-[#ffffff] border border-[#111111]/40 rounded px-2 py-0.5 text-[11px] text-[#111111] font-mono">
                <input id="{p}PalaceSummary" placeholder="Short summary..." class="bg-[#ffffff] border border-[#111111]/40 rounded px-2 py-0.5 text-[11px] text-[#111111] font-mono">
              </div>
              <div class="flex gap-1.5">
                <input id="{p}PalaceValue" placeholder="Concept value / memory text..." class="flex-1 min-w-0 bg-[#ffffff] border border-[#111111]/40 rounded px-2 py-0.5 text-[11px] text-[#111111] font-mono">
                <button type="button" onclick="arenaCtxPalaceSave('{p}')" class="px-3 py-0.5 rounded-full bg-[#111111] hover:bg-[#333333] text-[#ecf1e6] text-[10px] font-mono font-semibold shrink-0">+ Save Concept</button>
              </div>
              <div id="{p}PalaceList" class="max-h-[160px] overflow-y-auto space-y-1 text-[11px] font-mono"></div>
            </div>

            <!-- Model A & Model B pickers: locked 3-track CSS grid so dropdowns never clip or overlap -->
            <div class="aeonik-scope w-full" style="display:grid; grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr); align-items:center; gap:0.5rem;">
              <div class="min-w-0 overflow-hidden bg-[#f4f8f0] border border-[#111111] rounded-lg p-2 flex items-center gap-2">
                <label for="{p}Model{sa}Input" class="text-[11px] font-mono text-[#111111] font-bold shrink-0">Model {sa}:</label>
                <select id="{p}Model{sa}Input" data-arena-picker="{sa}" onchange="arenaDuelModelChange('{p}')" class="flex-1 min-w-0 w-full max-w-full bg-[#ffffff] border border-[#111111] rounded px-2 py-1 text-xs text-[#111111] font-mono focus:outline-none" style="width:100%; min-width:0; max-width:100%; overflow:hidden; text-overflow:ellipsis;">
                  <option value="{ma}">{ma}</option>
                </select>
              </div>
              <button type="button" id="{p}SwapBtn" onclick="arenaDuelSwap('{p}')" title="Swap left and right models" aria-label="Swap models" class="shrink-0 px-2.5 py-1 bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] text-[#111111] border border-[#111111] rounded-full font-mono text-xs transition active:scale-95">⇄</button>
              <div class="min-w-0 overflow-hidden bg-[#f4f8f0] border border-[#111111] rounded-lg p-2 flex items-center gap-2">
                <label for="{p}Model{sb}Input" class="text-[11px] font-mono text-[#111111] font-bold shrink-0">Model {sb}:</label>
                <select id="{p}Model{sb}Input" data-arena-picker="{sb}" onchange="arenaDuelModelChange('{p}')" class="flex-1 min-w-0 w-full max-w-full bg-[#ffffff] border border-[#111111] rounded px-2 py-1 text-xs text-[#111111] font-mono focus:outline-none" style="width:100%; min-width:0; max-width:100%; overflow:hidden; text-overflow:ellipsis;">
                  <option value="{mb}">{mb}</option>
                </select>
              </div>
            </div>
            <div id="{p}ModelsNote" class="text-[10px] font-mono text-[#4a4a4a]"></div>

            <div class="flex flex-col sm:flex-row gap-2">
              <input id="{p}PromptInput" type="text" value="Summarize what my files say about deploying TinCan." class="flex-1 min-w-0 bg-[#f4f8f0] border border-[#111111] rounded-lg px-3 py-1.5 text-xs text-[#111111] font-mono placeholder:text-[#5c5c5c]" aria-label="Duel prompt" oninput="if(typeof arenaUpdatePreAuthCap==='function')arenaUpdatePreAuthCap('{p}')" onkeydown="if(event.key==='Enter')arenaDuelRun('{p}')">
              <button type="button" id="{p}RunBtn" onclick="arenaDuelRun('{p}')" class="px-4 py-1.5 bg-[#111111] hover:bg-[#333333] text-[#ecf1e6] font-semibold rounded-full text-xs transition active:scale-95 shrink-0 flex items-center justify-center gap-1.5 border border-[#111111]"><span>⚔️</span> <span>Run Arena</span></button>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">{columns}
          </div>

          <form id="{p}VoteForm" role="dialog" aria-modal="false" aria-labelledby="{p}VoteModalTitle" data-arena-vote-modal="{p}" onsubmit="event.preventDefault(); arenaDuelSubmitVote('{p}');" onkeydown="if(event.key==='Escape')arenaDuelCloseVoteModal('{p}')" class="hidden fixed bottom-[5.25rem] right-5 z-[220] w-[420px] max-w-[calc(100vw-2rem)] bg-[#ffffff] text-[#111111] border-2 border-[#111111] rounded-2xl p-3.5 shadow-[0_20px_50px_rgba(0,0,0,0.28)] space-y-2.5" style="position:fixed; bottom:5.25rem; right:1.25rem; z-index:220; width:420px; max-width:calc(100vw - 2rem);">
            <div class="flex items-start justify-between gap-2 pb-2 border-b border-[#111111]/15">
              <div class="min-w-0">
                <div id="{p}VoteModalTitle" class="text-xs font-mono font-bold text-[#111111] flex items-center gap-1.5"><span>🏆</span><span>Run Complete · Cast Your Vote (+150 XP)</span></div>
                <div id="{p}VoteModalPrompt" class="text-[10px] font-mono text-[#4a4a4a] truncate">Pick Brain A or Brain B while reviewing answers above.</div>
              </div>
              <button type="button" id="{p}VoteCloseBtn" onclick="arenaDuelCloseVoteModal('{p}')" aria-label="Close vote popup" class="shrink-0 px-2 py-0.5 rounded-full border border-[#111111]/25 text-[10px] font-mono text-[#4a4a4a] hover:bg-[#111111] hover:text-[#ecf1e6] transition">Close ✕</button>
            </div>
            <div class="grid grid-cols-2 gap-2 text-xs font-mono font-bold">
              <label id="{p}VoteCardA" class="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#111111]/40 bg-[#f4f8f0] text-[#111111] hover:border-[#111111] cursor-pointer transition select-none">
                <input type="radio" name="{p}VoteWinner" id="{p}VotePickA" value="A" onchange="arenaDuelSelectVoteSide('{p}','A')" class="accent-[#111111]"> <span>Brain A</span>
              </label>
              <label id="{p}VoteCardB" class="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#111111]/40 bg-[#f4f8f0] text-[#111111] hover:border-[#111111] cursor-pointer transition select-none">
                <input type="radio" name="{p}VoteWinner" id="{p}VotePickB" value="B" onchange="arenaDuelSelectVoteSide('{p}','B')" class="accent-[#111111]"> <span>Brain B</span>
              </label>
            </div>
            <div class="space-y-1.5 text-[10px] font-mono">
              <select id="{p}VoteTagSelect" class="w-full bg-[#f4f8f0] border border-[#111111]/40 rounded-lg px-2 py-1 text-[11px] text-[#111111] font-mono">
                <option value="More accurate">More accurate</option>
                <option value="Better context recall">Better context recall</option>
                <option value="Faster &amp; cleaner">Faster &amp; cleaner</option>
                <option value="More helpful code/reasoning">More helpful code/reasoning</option>
              </select>
              <div class="flex items-center gap-1.5">
                <input id="{p}VoteReasonInput" type="text" maxlength="400" placeholder="Which one did you like and why was it better?" class="flex-1 min-w-0 bg-[#f4f8f0] border border-[#111111]/40 rounded-lg px-2.5 py-1 text-xs text-[#111111] font-mono">
                <button type="submit" id="{p}VoteSubmitBtn" class="shrink-0 px-3.5 py-1.5 bg-[#111111] hover:bg-[#333333] text-[#ecf1e6] font-semibold rounded-full text-xs font-mono border border-[#111111]">Submit Vote</button>
              </div>
            </div>
            <div id="{p}VoteStatus" class="text-[10px] font-mono text-[#4a4a4a]" aria-live="polite"></div>
          </form>

          <div id="{p}LastVoteBadge" data-arena-last-vote-badge="{p}" class="hidden bg-[#ffffff] border border-[#111111] rounded-xl px-3 py-2 flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-[#111111]" aria-live="polite">
            <span id="{p}LastVoteText" class="min-w-0 flex-1 break-words">Duel ready · Cast vote (+150 XP)</span>
            <button type="button" id="{p}ReopenVoteBtn" onclick="arenaDuelReopenVote('{p}')" class="hidden shrink-0 px-3 py-1 rounded-full bg-[#111111] hover:bg-[#333333] text-[#ecf1e6] text-[10px] font-mono font-semibold border border-[#111111] transition active:scale-95">Re-open Vote Popup</button>
          </div>

          <div id="{p}ProStrip" class="bg-[#ffffff] border border-[#111111] rounded-xl p-3 flex flex-wrap items-center justify-between gap-3">
            <div class="min-w-0 space-y-0.5">
              <div id="{p}ProTelemetryTitle" class="text-[10px] font-mono font-bold uppercase tracking-wider text-[#111111]">AD-SUPPORTED AI CREDITS · ZERO SUBSCRIPTIONS</div>
              <p id="{p}ProTelemetrySub" class="text-[11px] text-[#4a4a4a]">No subscriptions. Watch sponsor ads on the Home Screen to earn AI credits and tokens for AI deliverables, or run zero-burn via local Ollama.</p>
            </div>
            <button type="button" id="{p}UpgradeProBtn" onclick="if(typeof zenWatchHomeAd==='function')zenWatchHomeAd();else if(typeof toggleWindow==='function')toggleWindow('win-ai-home')" class="px-4 py-1.5 bg-[#111111] hover:bg-[#333333] text-[#ecf1e6] font-semibold rounded-full text-xs font-mono transition active:scale-95 shrink-0 border border-[#111111]">Watch Home Screen Ads →</button>
          </div>
        </div>"""


ARENA_DUEL_SCRIPT = r"""
<script id="arenaDuelScript">
(function () {
  const VIEWS = __ARENA_VIEWS__;
  const SIDES = ['A', 'B'];
  const lastDuel = {};
  const ragStats = {};
  const MODELS_KEY = 'tincan_arena_models';   // shared with the #12 pickers
  let driveAllowed = false;
  let modelList = [];
  let lastTokenBalance = null;

  const el = (id) => document.getElementById(id);
  const peer = () => (typeof myPeerId !== 'undefined' ? myPeerId : (localStorage.getItem('tincan_peer_id') || ''));
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const agentOf = (p, side) => ((el(p + 'Agent' + side) || {}).value || ('brain-' + side.toLowerCase())).trim().toLowerCase();
  const modelOf = (p, side) => ((el(p + 'Model' + side + 'Input') || {}).value || '').trim();
  const nowMs = () => (typeof performance !== 'undefined' && performance && typeof performance.now === 'function' ? performance.now() : Date.now());

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
    if (m) { m.textContent = text || ''; m.className = 'text-[10px] font-mono min-h-[12px] ' + (isError ? 'text-[#8a1c1c] font-semibold' : 'text-[#4a4a4a]'); }
  }

  function isLocalModelId(id) {
    const v = String(id || '').trim().toLowerCase();
    if (!v) return false;
    if (v.startsWith('ollama/') || v.startsWith('local/') || v.startsWith('openai-compat/') || v.startsWith('owlchat/') || v.startsWith('trussed/')) return true;
    if (v === 'ollama-brain' || v === 'local-brain' || v.endsWith(':free')) return true;
    const meta = modelList.find((m) => m && m.id === id);
    if (meta) {
      const gw = String(meta.gateway || '').toLowerCase();
      const prov = String(meta.provider || '').toLowerCase();
      if (gw === 'ollama' || gw === 'local' || prov.indexOf('ollama') !== -1 || prov.indexOf('local') !== -1) return true;
    }
    return false;
  }

  function isOpenWeightModelId(id) {
    if (isLocalModelId(id)) return true;
    const v = String(id || '').trim().toLowerCase();
    if (!v) return false;
    const meta = modelList.find((m) => m && m.id === id);
    if (meta && meta.open_weights) return true;
    return v === 'nanogpt-brain' || v.startsWith('nanogpt/') || v.startsWith('deepseek/') || v.startsWith('meta-llama/') || v.startsWith('qwen/') || v.startsWith('mistralai/');
  }

  function getAvailableOptions(p) {
    if (modelList && modelList.length) return modelList.slice();
    const sel = el(p + 'ModelAInput') || el(p + 'ModelBInput');
    if (!sel || !sel.options) return [];
    return Array.from(sel.options).map((o) => ({id: o.value, name: o.textContent || o.value, provider: '', kind: 'catalog'}));
  }

  function updateRagBadge(p, matchedInfo) {
    const badge = el(p + 'RagBadge');
    if (!badge) return;
    if (matchedInfo && (matchedInfo.files > 0 || matchedInfo.tokens > 0)) {
      badge.textContent = 'RAG: .space · ' + matchedInfo.files + ' file(s) · ~' + matchedInfo.tokens + ' tok';
      badge.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full bg-[#ecf1e6] text-[#107a47] border border-[#107a47] text-[10px] font-mono font-semibold';
      return;
    }
    const useA = !!(el(p + 'UseCtxA') || {}).checked;
    const useB = !!(el(p + 'UseCtxB') || {}).checked;
    if (!useA && !useB) {
      badge.textContent = 'RAG: .space (off)';
      badge.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full bg-[#f4f8f0] text-[#5c5c5c] border border-[#111111]/40 text-[10px] font-mono';
      return;
    }
    const st = ragStats[p] || {};
    const totalFiles = (useA && st.A ? st.A.count : 0) + (useB && st.B ? st.B.count : 0);
    const totalChunks = (useA && st.A ? st.A.chunks : 0) + (useB && st.B ? st.B.chunks : 0);
    const firstPath = (useA && st.A && st.A.firstPath) || (useB && st.B && st.B.firstPath) || '';
    if (totalFiles > 0) {
      badge.textContent = totalFiles === 1 && firstPath
        ? ('RAG: ' + firstPath + ' (' + totalChunks + ' ch)')
        : ('RAG: .space · ' + totalFiles + ' file(s) · ' + totalChunks + ' ch');
      badge.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full bg-[#ecf1e6] text-[#107a47] border border-[#107a47] text-[10px] font-mono font-semibold';
    } else {
      badge.textContent = 'RAG: .space (0 files · ready)';
      badge.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full bg-[#ecf1e6] text-[#111111] border border-[#111111] text-[10px] font-mono';
    }
  }

  function estimateSideTokens(prompt) {
    const len = String(prompt || '').length;
    return Math.floor((len + 3) / 4) + 8 + 512;
  }

  window.arenaUpdatePreAuthCap = function (p) {
    const cap = el(p + 'PreAuthCap');
    if (!cap) return;
    const prompt = ((el(p + 'PromptInput') || {}).value || '').trim();
    const est = estimateSideTokens(prompt);
    if (lastTokenBalance !== null && lastTokenBalance < est) {
      cap.textContent = 'PRE-AUTH CAP: ' + est + ' TOK/SIDE · LOW BAL (' + lastTokenBalance + ')';
      cap.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full bg-[#ecf1e6] text-[#8a1c1c] border border-[#8a1c1c] text-[10px] font-mono font-semibold';
    } else {
      cap.textContent = 'PRE-AUTH CAP: ' + est + ' TOK/SIDE MAX';
      cap.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full bg-[#ecf1e6] text-[#107a47] border border-[#107a47] text-[10px] font-mono font-semibold';
    }
  };

  function renderSavingsDelta(p, telemetry) {
    if (!telemetry) return;
    SIDES.forEach((side) => {
      const mine = telemetry[side];
      if (!mine) return;
      const otherSide = side === 'A' ? 'B' : 'A';
      const other = telemetry[otherSide];
      const box = el(p + 'Savings' + side);
      const bill = el(p + 'Bill' + side);
      const ttftText = Number(mine.ttft || 0).toFixed(2) + 's TTFT';
      const cost = Number(mine.cost || 0);
      const tokens = Number(mine.tokens || 0);
      if (bill) {
        if (cost <= 0) {
          bill.className = 'text-[10px] font-mono text-[#107a47] font-semibold min-h-[12px] text-right';
          bill.textContent = tokens + ' tok · $0.000000 (FREE) · ' + ttftText + (mine.simulated ? ' · simulated' : '');
        } else {
          bill.className = 'text-[10px] font-mono ' + (other && Number(other.cost || 0) <= 0 ? 'text-[#8a1c1c] font-semibold' : 'text-[#4a4a4a]') + ' min-h-[12px] text-right';
          bill.textContent = 'Billed: ' + tokens + ' tok · $' + cost.toFixed(6) + ' · ' + ttftText + (mine.simulated ? ' · simulated' : '');
        }
      }
      if (!box) return;
      if (cost <= 0) {
        box.className = 'text-[10px] font-mono text-[#107a47] bg-[#ffffff] border border-[#107a47] rounded-lg px-2 py-1 min-h-[22px] flex items-center justify-between gap-2 font-semibold';
        if (other && Number(other.cost || 0) > 0) {
          box.textContent = '● ZERO-BURN FREE ($0) · SAVES $' + Number(other.cost).toFixed(6) + ' (100%) VS BRAIN ' + otherSide + ' · ' + ttftText;
        } else {
          box.textContent = '● ZERO-BURN FREE ($0.000000) · LOCAL / ZERO POOL BURN · ' + ttftText;
        }
      } else if (other && Number(other.cost || 0) <= 0) {
        box.className = 'text-[10px] font-mono text-[#8a1c1c] bg-[#ffffff] border border-[#111111]/25 rounded-lg px-2 py-1 min-h-[22px] flex items-center justify-between gap-2';
        box.textContent = 'CLOUD BILLED · +$' + cost.toFixed(6) + ' vs Brain ' + otherSide + ' ($0 free) · ' + ttftText;
      } else if (other && cost < Number(other.cost)) {
        const diff = Number(other.cost) - cost;
        const pct = Math.round((diff / Number(other.cost)) * 100);
        box.className = 'text-[10px] font-mono text-[#107a47] bg-[#ffffff] border border-[#107a47] rounded-lg px-2 py-1 min-h-[22px] flex items-center justify-between gap-2 font-semibold';
        box.textContent = '● LOWER BURN · SAVES $' + diff.toFixed(6) + ' (' + pct + '%) VS BRAIN ' + otherSide + ' · ' + ttftText;
      } else if (other && cost > Number(other.cost)) {
        const delta = cost - Number(other.cost);
        box.className = 'text-[10px] font-mono text-[#4a4a4a] bg-[#ffffff] border border-[#111111]/25 rounded-lg px-2 py-1 min-h-[22px] flex items-center justify-between gap-2';
        box.textContent = '+$' + delta.toFixed(6) + ' vs Brain ' + otherSide + ' (' + tokens + ' tok) · ' + ttftText;
      } else {
        box.className = 'text-[10px] font-mono text-[#4a4a4a] bg-[#ffffff] border border-[#111111]/25 rounded-lg px-2 py-1 min-h-[22px] flex items-center justify-between gap-2';
        box.textContent = tokens + ' tok · $' + cost.toFixed(6) + ' · ' + ttftText;
      }
    });
    const proTitle = el(p + 'ProTelemetryTitle');
    if (proTitle && telemetry.A && telemetry.B) {
      const ca = Number(telemetry.A.cost || 0);
      const cb = Number(telemetry.B.cost || 0);
      const totalTok = Number(telemetry.A.tokens || 0) + Number(telemetry.B.tokens || 0);
      if ((ca <= 0 && cb > 0) || (cb <= 0 && ca > 0)) {
        const paid = Math.max(ca, cb);
        proTitle.className = 'text-[10px] font-mono font-bold uppercase tracking-wider text-[#107a47]';
        proTitle.textContent = 'AD-SUPPORTED CREDITS: ZERO-BURN SAVED 100% VS CLOUD ($' + paid.toFixed(6) + '/DUEL)';
      } else if (ca !== cb && Math.max(ca, cb) > 0) {
        const hi = Math.max(ca, cb);
        const lo = Math.min(ca, cb);
        const pct = Math.round(((hi - lo) / hi) * 100);
        proTitle.className = 'text-[10px] font-mono font-bold uppercase tracking-wider text-[#107a47]';
        proTitle.textContent = 'AD-SUPPORTED CREDITS: SAVED $' + (hi - lo).toFixed(6) + ' (' + pct + '%) ON LOWER-COST MODEL';
      } else {
        proTitle.className = 'text-[10px] font-mono font-bold uppercase tracking-wider text-[#111111]';
        proTitle.textContent = 'AD-SUPPORTED CREDITS: DUEL COST $' + (ca + cb).toFixed(6) + ' (' + totalTok + ' TOK)';
      }
    }
  }
  window.arenaRenderSavings = renderSavingsDelta;

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
    VIEWS.forEach((p) => updateRagBadge(p));
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
    VIEWS.forEach((q) => updateRagBadge(q));
  };

  function labels(p) {
    SIDES.forEach((side) => {
      const m = modelOf(p, side);
      const l = el(p + 'Label' + side);
      if (l) l.textContent = m || ('Brain ' + side);
      const tag = el(p + 'TierTag' + side);
      if (tag) {
        const local = isLocalModelId(m);
        tag.textContent = local ? 'LOCAL' : 'CLOUD';
        tag.className = 'text-[9px] font-mono uppercase tracking-wider px-1.5 py-0.5 rounded-full border shrink-0 ' + (local ? 'border-[#107a47] bg-[#ecf1e6] text-[#107a47] font-semibold' : 'border-[#111111]/30 bg-[#f4f8f0] text-[#4a4a4a]');
      }
    });
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

  window.arenaPresetLocalVsCloud = function (p) {
    const opts = getAvailableOptions(p);
    if (!opts.length) return null;
    const localStrict = opts.find((m) => isLocalModelId(m.id));
    const localPick = localStrict || opts.find((m) => isOpenWeightModelId(m.id)) || opts[0];
    const cloudPrefs = ['claude-brain', 'anthropic/claude-sonnet-5.5', 'anthropic/claude-3.7-sonnet', 'anthropic/claude-3.5-sonnet', 'openai-brain', 'openai/gpt-4o', 'grok-brain', 'gemini-brain', 'google/gemini-2.5-pro'];
    let cloudPick = null;
    for (const pref of cloudPrefs) {
      cloudPick = opts.find((m) => m.id === pref && m.id !== localPick.id);
      if (cloudPick) break;
    }
    if (!cloudPick) {
      cloudPick = opts.find((m) => m.id !== localPick.id && !isLocalModelId(m.id)) || opts.find((m) => m.id !== localPick.id) || localPick;
    }
    const pair = {a: localPick.id, b: cloudPick.id};
    setPair(pair);
    const note = localStrict
      ? ('Armed: ' + pair.a + ' (local/free) vs ' + pair.b + ' (cloud)')
      : ('Armed: ' + pair.a + ' (open-weight) vs ' + pair.b + ' (cloud)');
    VIEWS.forEach((q) => {
      const st = el(q + 'PresetStatus');
      if (st) {
        st.textContent = note;
        st.className = 'text-[10px] font-mono ' + (localStrict ? 'text-[#107a47] font-semibold' : 'text-[#4a4a4a]');
      }
    });
    return pair;
  };

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
    if (!files.length) { box.innerHTML = '<div class="text-[#5c5c5c]">No files yet. Upload, paste, import from Space/Palace, or add to Both Brains.</div>'; return; }
    box.innerHTML = files.map((f) => {
      const stale = f.source === 'drive' && f.drive_available === false ? ' <span class="text-[#8a1c1c]" title="Drive mirror is off; using the last copy">(snapshot)</span>' : '';
      const descLine = f.description ? ('<div class="text-[10px] text-[#5c5c5c] truncate pl-1">' + esc(f.description) + '</div>') : '';
      return '<div class="border-b border-[#111111]/10 pb-0.5" data-ctx-file="' + esc(f.path) + '">' +
        '<div class="flex items-center gap-1 group">' +
        '<button type="button" class="flex-1 min-w-0 text-left truncate text-[#111111] hover:underline font-semibold" data-act="view" title="' + esc(f.description || f.path) + '">' + esc(f.path) + '</button>' +
        '<span class="text-[#5c5c5c] shrink-0 text-[10px]">' + esc(f.source) + ' · ' + esc(f.chunk_count) + 'ch</span>' + stale +
        '<button type="button" class="text-[#111111] hover:underline shrink-0 px-1 text-[10px]" data-act="edit" title="Edit content & description">✎</button>' +
        '<button type="button" class="text-[#8a1c1c] hover:underline shrink-0 px-1 font-semibold" data-act="del" title="Remove from this brain">✕</button></div>' +
        descLine + '</div>';
    }).join('');
    box.querySelectorAll('[data-ctx-file]').forEach((row) => {
      const path = row.getAttribute('data-ctx-file');
      row.querySelector('[data-act="view"]').onclick = () => window.arenaCtxView(p, side, path);
      row.querySelector('[data-act="edit"]').onclick = () => window.arenaCtxEdit(p, side, path);
      row.querySelector('[data-act="del"]').onclick = () => window.arenaCtxDelete(p, side, path);
    });
  }

  function renderUsed(p, side, sideResult) {
    const box = el(p + 'Used' + side);
    if (!box) return;
    const ctx = (sideResult && sideResult.context) || null;
    if (!ctx) { box.textContent = 'No duel yet.'; return; }
    if (!ctx.enabled) { box.innerHTML = '<div class="text-[#5c5c5c]">Files were switched off for this answer.</div>'; return; }
    const snips = ctx.snippets || [];
    if (!snips.length) { box.innerHTML = '<div class="text-[#5c5c5c]">No file in this brain matched the prompt.</div>'; return; }
    box.innerHTML = '<div class="text-[#5c5c5c]">' + esc(ctx.files.length) + ' file(s), ' + esc(snips.length) + ' snippet(s), ~' + esc(ctx.tokens) + ' tokens</div>' +
      snips.map((s) => '<details class="arena-snippet border border-[#111111]/20 bg-[#ffffff] rounded px-1.5 py-1"><summary class="cursor-pointer truncate"><span class="text-[#111111] font-semibold">' + esc(s.path) + '</span> <span class="text-[#5c5c5c]">#' + esc(s.chunk) + ' · ' + esc(s.source) + ' · score ' + esc(s.score) + '</span></summary><div class="whitespace-pre-wrap text-[10px] text-[#111111] pt-1">' + esc(s.text) + '</div></details>').join('');
  }

  async function refresh(p, side) {
    const agent = agentOf(p, side);
    try {
      const data = await api('/api/arena/context/files?agent_id=' + encodeURIComponent(agent));
      renderFiles(p, side, data);
      ragStats[p] = ragStats[p] || {};
      ragStats[p][side] = {
        count: Number(data.count || 0),
        chunks: Number(data.chunk_count || 0),
        firstPath: (data.files && data.files[0] && data.files[0].path) || '',
      };
      updateRagBadge(p);
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

  const editTarget = {};
  let editingPalaceId = '';

  window.arenaCtxView = async function (p, side, path) {
    const v = el(p + 'Viewer' + side);
    if (!v) return;
    try {
      const f = await api('/api/arena/context/file?agent_id=' + encodeURIComponent(agentOf(p, side)) + '&path=' + encodeURIComponent(path));
      const desc = f.description ? ('<div class="text-[10px] text-[#4a4a4a] border-b border-[#111111]/15 pb-1"><strong>About:</strong> ' + esc(f.description) + '</div>') : '';
      v.innerHTML = '<div class="flex items-center justify-between gap-2 border-b border-[#111111]/20 pb-1">' +
        '<span class="font-bold truncate">' + esc(f.path) + ' (' + esc(f.size_bytes) + ' B · ' + esc(f.chunk_count) + ' ch)</span>' +
        '<span class="flex items-center gap-1 shrink-0">' +
        '<button type="button" class="px-1.5 py-0.5 rounded bg-[#ecf1e6] border border-[#111111]/40 text-[10px]" data-viewer-edit="1">✎ Edit</button>' +
        '<button type="button" class="px-1.5 py-0.5 rounded bg-[#f4f8f0] border border-[#111111]/30 text-[10px]" data-viewer-close="1">✕</button>' +
        '</span></div>' + desc +
        '<pre class="whitespace-pre-wrap text-[10px] font-mono text-[#111111] pt-1">' + esc(f.content || '') + '</pre>';
      const editBtn = v.querySelector('[data-viewer-edit]');
      if (editBtn) editBtn.onclick = () => window.arenaCtxEdit(p, side, path);
      const closeBtn = v.querySelector('[data-viewer-close]');
      if (closeBtn) closeBtn.onclick = () => v.classList.add('hidden');
      v.classList.remove('hidden');
    } catch (e) { msg(p, side, e.message, true); }
  };

  window.arenaCtxEdit = async function (p, side, path) {
    const box = el(p + 'EditBox' + side);
    if (!box) return;
    try {
      const f = await api('/api/arena/context/file?agent_id=' + encodeURIComponent(agentOf(p, side)) + '&path=' + encodeURIComponent(path));
      editTarget[p + ':' + side] = f.path;
      const lbl = el(p + 'EditPathLabel' + side);
      if (lbl) lbl.textContent = f.path;
      if (el(p + 'EditDesc' + side)) el(p + 'EditDesc' + side).value = f.description || '';
      if (el(p + 'EditText' + side)) el(p + 'EditText' + side).value = f.content || '';
      box.classList.remove('hidden');
    } catch (e) { msg(p, side, e.message, true); }
  };

  window.arenaCtxCancelEdit = function (p, side) {
    delete editTarget[p + ':' + side];
    const box = el(p + 'EditBox' + side);
    if (box) box.classList.add('hidden');
  };

  window.arenaCtxSaveEdit = async function (p, side) {
    const path = editTarget[p + ':' + side];
    if (!path) return;
    const description = el(p + 'EditDesc' + side) ? el(p + 'EditDesc' + side).value : '';
    const content = el(p + 'EditText' + side) ? el(p + 'EditText' + side).value : '';
    try {
      await api('/api/arena/context/update', {body: {agent_id: agentOf(p, side), path, description, content}});
      window.arenaCtxCancelEdit(p, side);
      msg(p, side, 'Updated ' + path);
      refreshEverywhere(side, agentOf(p, side));
      window.arenaCtxView(p, side, path);
    } catch (e) { msg(p, side, e.message, true); }
  };

  window.arenaCtxDelete = async function (p, side, path) {
    if (!confirm('Remove ' + path + ' from ' + agentOf(p, side) + '?')) return;
    try {
      await api('/api/arena/context/delete', {body: {agent_id: agentOf(p, side), path}});
      const v = el(p + 'Viewer' + side); if (v) v.classList.add('hidden');
      window.arenaCtxCancelEdit(p, side);
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
    const description = el(p + 'PasteDesc' + side) ? (el(p + 'PasteDesc' + side).value || '').trim() : '';
    const text = el(p + 'PasteText' + side).value || '';
    if (!text.trim()) { msg(p, side, 'Paste some text first.', true); return; }
    try {
      const data = await api('/api/arena/context/ingest', {body: {agent_id: agentOf(p, side), files: [{name, description, content: text, source: 'paste'}]}});
      el(p + 'PasteText' + side).value = '';
      if (el(p + 'PasteDesc' + side)) el(p + 'PasteDesc' + side).value = '';
      reportIngest(p, side, data);
    } catch (e) { msg(p, side, e.message + (e.data && e.data.errors ? ' · ' + e.data.errors.map((x) => x.error).join('; ') : ''), true); }
  };

  window.arenaCtxToggleBoth = function (p) {
    const b = el(p + 'BothBox');
    if (b) b.classList.toggle('hidden');
  };

  function bothMsg(p, text, isErr) {
    const m = el(p + 'BothMsg');
    if (m) { m.textContent = text || ''; m.className = 'text-[10px] font-mono ' + (isErr ? 'text-[#8a1c1c] font-semibold' : 'text-[#107a47]'); }
  }

  window.arenaCtxPasteBoth = async function (p) {
    const name = (el(p + 'BothName') && el(p + 'BothName').value || '').trim() || ('shared-' + new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-') + '.md');
    const description = el(p + 'BothDesc') ? (el(p + 'BothDesc').value || '').trim() : '';
    const content = el(p + 'BothText') ? (el(p + 'BothText').value || '') : '';
    if (!content.trim()) { bothMsg(p, 'Enter text to add to both brains.', true); return; }
    try {
      const res = await api('/api/arena/context/ingest', {
        body: {agent_id: 'both', agent_ids: [agentOf(p, 'A'), agentOf(p, 'B')], files: [{name, description, content, source: 'paste'}]}
      });
      if (el(p + 'BothText')) el(p + 'BothText').value = '';
      if (el(p + 'BothDesc')) el(p + 'BothDesc').value = '';
      bothMsg(p, 'Added ' + name + ' to Brain A & Brain B (' + (res.added || []).length + ' total entries).');
      SIDES.forEach((s) => refreshEverywhere(s, agentOf(p, s)));
    } catch (e) { bothMsg(p, e.message, true); }
  };

  window.arenaCtxUploadBoth = async function (p, input) {
    const files = Array.from(input.files || []);
    input.value = '';
    if (!files.length) return;
    bothMsg(p, 'Uploading ' + files.length + ' file(s) to Brain A & Brain B…');
    try {
      const payload = [];
      for (const f of files.slice(0, 50)) {
        if (f.size > 16 * 1024 * 1024) continue;
        payload.push({name: f.name, content_b64: await fileToB64(f), source: 'upload'});
      }
      if (!payload.length) return;
      await api('/api/arena/context/ingest', {body: {agent_id: 'both', agent_ids: [agentOf(p, 'A'), agentOf(p, 'B')], files: payload}});
      bothMsg(p, 'Uploaded ' + payload.length + ' file(s) to BOTH Brain A & Brain B.');
      SIDES.forEach((s) => refreshEverywhere(s, agentOf(p, s)));
    } catch (e) { bothMsg(p, e.message, true); }
  };

  window.arenaCtxImportBoth = async function (p) {
    try {
      const res = await api('/api/arena/context/import', {
        body: {agent_id: 'both', agent_ids: [agentOf(p, 'A'), agentOf(p, 'B')], space_owner: peer()}
      });
      bothMsg(p, 'Imported Workstation Space into Brain A & Brain B (' + (res.added || []).length + ' entries).');
      SIDES.forEach((s) => refreshEverywhere(s, agentOf(p, s)));
      if (typeof showQuickNotification === 'function') showQuickNotification('Imported .space into BOTH brains!');
    } catch (e) { bothMsg(p, e.message, true); }
  };

  window.arenaCtxToggleInventory = function (p) {
    const box = el(p + 'InventoryBox');
    if (!box) return;
    box.classList.toggle('hidden');
    if (!box.classList.contains('hidden')) window.arenaCtxLoadInventory(p);
  };

  window.arenaCtxLoadInventory = async function (p) {
    const listEl = el(p + 'InvList');
    const statsEl = el(p + 'InvStats');
    if (!listEl) return;
    const q = el(p + 'InvSearch') ? (el(p + 'InvSearch').value || '').trim() : '';
    try {
      const data = await api('/api/arena/context/inventory?agent_a=' + encodeURIComponent(agentOf(p, 'A')) +
        '&agent_b=' + encodeURIComponent(agentOf(p, 'B')) + '&q=' + encodeURIComponent(q));
      const c = data.counts || {};
      if (statsEl) {
        statsEl.textContent = 'A: ' + (c.brain_a || 0) + ' · B: ' + (c.brain_b || 0) + ' · Shared: ' + (c.shared || 0) +
          ' · Space: ' + (c.space || 0) + ' · Palace: ' + (c.palace || 0) + ' · Drive: ' + (c.drive || 0);
      }
      const items = data.items || [];
      if (!items.length) {
        listEl.innerHTML = '<div class="text-[#5c5c5c]">No inventory items match. Add files, Space docs, or Context Palace concepts.</div>';
        return;
      }
      listEl.innerHTML = items.map((it, idx) => {
        const kindBadge = String(it.kind || '').toUpperCase();
        return '<div class="bg-[#ffffff] border border-[#111111]/25 rounded p-1.5 flex flex-wrap items-center justify-between gap-2" data-inv-idx="' + idx + '">' +
          '<div class="min-w-0 flex-1">' +
          '<div class="flex items-center gap-1.5"><span class="px-1.5 py-0.5 rounded bg-[#ecf1e6] border border-[#111111]/30 text-[9px] font-bold">' + esc(kindBadge) + '</span>' +
          '<span class="font-semibold truncate text-[#111111]">' + esc(it.title || it.path) + '</span></div>' +
          '<div class="text-[10px] text-[#5c5c5c] truncate">' + esc(it.description || it.path) + '</div></div>' +
          '<div class="flex items-center gap-1 shrink-0 text-[10px]">' +
          '<button type="button" class="px-2 py-0.5 rounded-full bg-[#ecf1e6] hover:bg-[#111111] hover:text-[#ecf1e6] border border-[#111111]/40" data-inv-both="1">→ Both Brains</button>' +
          (it.kind === 'palace' ? '<button type="button" class="px-2 py-0.5 rounded-full bg-[#ffffff] hover:bg-[#111111] hover:text-[#ecf1e6] border border-[#111111]/40" data-inv-palace-edit="1">✎</button>' : '') +
          '</div></div>';
      }).join('');
      listEl.querySelectorAll('[data-inv-idx]').forEach((row) => {
        const it = items[Number(row.getAttribute('data-inv-idx'))];
        const btnBoth = row.querySelector('[data-inv-both]');
        if (btnBoth) {
          btnBoth.onclick = async () => {
            try {
              if (it.source_group === 'palace') {
                await api('/api/arena/context/palace/import', {body: {agent_id: 'both', node_ids: [it.node_id || it.id]}});
              } else if (it.source_group === 'space') {
                await api('/api/arena/context/import', {body: {agent_id: 'both', space_owner: peer(), paths: [it.path]}});
              } else if (it.source_group === 'drive') {
                await api('/api/arena/context/drive/link', {body: {agent_id: 'both', drive_path: it.path}});
              } else {
                const srcAgent = it.in_a ? agentOf(p, 'A') : agentOf(p, 'B');
                const rec = await api('/api/arena/context/file?agent_id=' + encodeURIComponent(srcAgent) + '&path=' + encodeURIComponent(it.path));
                await api('/api/arena/context/ingest', {
                  body: {agent_id: 'both', files: [{path: it.path, description: rec.description || it.description, content: rec.content || '', source: 'import'}]}
                });
              }
              SIDES.forEach((s) => refreshEverywhere(s, agentOf(p, s)));
              window.arenaCtxLoadInventory(p);
            } catch (err) { if (statsEl) statsEl.textContent = 'Copy error: ' + err.message; }
          };
        }
        const btnEdit = row.querySelector('[data-inv-palace-edit]');
        if (btnEdit && it.source_group === 'palace') {
          btnEdit.onclick = () => window.arenaCtxPalaceEdit(p, it);
        }
      });
    } catch (e) {
      if (statsEl) statsEl.textContent = e.message;
    }
  };

  window.arenaCtxTogglePalace = function (p) {
    const box = el(p + 'PalaceBox');
    if (!box) return;
    box.classList.toggle('hidden');
    if (!box.classList.contains('hidden')) window.arenaCtxLoadPalace(p);
  };

  window.arenaCtxLoadPalace = async function (p) {
    const listEl = el(p + 'PalaceList');
    if (!listEl) return;
    const q = el(p + 'PalaceSearch') ? (el(p + 'PalaceSearch').value || '').trim() : '';
    try {
      const data = await api('/api/arena/context/palace?q=' + encodeURIComponent(q) + '&limit=60');
      const concepts = data.concepts || [];
      if (!concepts.length) {
        listEl.innerHTML = '<div class="text-[#5c5c5c]">No Context Palace concepts yet. Add one above to store reusable memory across Router &amp; Arena.</div>';
        return;
      }
      listEl.innerHTML = concepts.map((c, idx) =>
        '<div class="bg-[#ffffff] border border-[#111111]/25 rounded p-1.5 flex flex-wrap items-center justify-between gap-2" data-pal-idx="' + idx + '">' +
        '<div class="min-w-0 flex-1">' +
        '<div class="flex items-center gap-1.5"><span class="px-1.5 py-0.5 rounded bg-[#ecf1e6] border border-[#111111]/30 text-[9px]">' + esc(c.category) + '</span>' +
        '<span class="font-bold text-[#111111] truncate">' + esc(c.canonical_name) + '</span></div>' +
        '<div class="text-[10px] text-[#5c5c5c] truncate">' + esc(c.summary || c.value) + '</div></div>' +
        '<div class="flex items-center gap-1 shrink-0 text-[10px]">' +
        '<button type="button" class="px-2 py-0.5 rounded-full bg-[#111111] text-[#ecf1e6]" data-pal-both="1">→ Both</button>' +
        '<button type="button" class="px-2 py-0.5 rounded-full bg-[#ffffff] border border-[#111111]/40" data-pal-edit="1">✎</button>' +
        '<button type="button" class="px-2 py-0.5 rounded-full bg-[#ffffff] border border-[#8a1c1c]/40 text-[#8a1c1c]" data-pal-del="1">✕</button>' +
        '</div></div>'
      ).join('');
      listEl.querySelectorAll('[data-pal-idx]').forEach((row) => {
        const c = concepts[Number(row.getAttribute('data-pal-idx'))];
        row.querySelector('[data-pal-both]').onclick = () => window.arenaCtxImportPalace(p, 'both', [c.node_id]);
        row.querySelector('[data-pal-edit]').onclick = () => window.arenaCtxPalaceEdit(p, c);
        row.querySelector('[data-pal-del]').onclick = () => window.arenaCtxPalaceDelete(p, c.node_id);
      });
    } catch (e) { listEl.innerHTML = '<div class="text-[#8a1c1c]">' + esc(e.message) + '</div>'; }
  };

  window.arenaCtxPalaceEdit = function (p, c) {
    const box = el(p + 'PalaceBox');
    if (box) box.classList.remove('hidden');
    editingPalaceId = c.node_id || '';
    if (el(p + 'PalaceName')) el(p + 'PalaceName').value = c.canonical_name || c.title || '';
    if (el(p + 'PalaceCategory')) el(p + 'PalaceCategory').value = c.category || 'knowledge';
    if (el(p + 'PalaceSummary')) el(p + 'PalaceSummary').value = c.summary || c.description || '';
    if (el(p + 'PalaceValue')) el(p + 'PalaceValue').value = c.value || c.active_value || '';
  };

  window.arenaCtxPalaceSave = async function (p) {
    const canonical_name = (el(p + 'PalaceName') && el(p + 'PalaceName').value || '').trim();
    const category = (el(p + 'PalaceCategory') && el(p + 'PalaceCategory').value || 'knowledge').trim() || 'knowledge';
    const summary = (el(p + 'PalaceSummary') && el(p + 'PalaceSummary').value || '').trim();
    const value = (el(p + 'PalaceValue') && el(p + 'PalaceValue').value || '').trim();
    if (!canonical_name || !value) return;
    const action = editingPalaceId ? 'update' : 'create';
    await api('/api/arena/context/palace/crud', {
      body: {action, node_id: editingPalaceId || undefined, canonical_name, category, summary, value}
    });
    editingPalaceId = '';
    if (el(p + 'PalaceName')) el(p + 'PalaceName').value = '';
    if (el(p + 'PalaceSummary')) el(p + 'PalaceSummary').value = '';
    if (el(p + 'PalaceValue')) el(p + 'PalaceValue').value = '';
    await window.arenaCtxLoadPalace(p);
  };

  window.arenaCtxPalaceDelete = async function (p, nodeId) {
    if (!confirm('Delete Context Palace node ' + nodeId + '?')) return;
    await api('/api/arena/context/palace/crud', {body: {action: 'delete', node_id: nodeId}});
    await window.arenaCtxLoadPalace(p);
  };

  window.arenaCtxImportPalace = async function (p, targetAgentId, nodeIds) {
    const q = el(p + 'PalaceSearch') ? (el(p + 'PalaceSearch').value || '').trim() : '';
    await api('/api/arena/context/palace/import', {
      body: {agent_id: targetAgentId || 'both', node_ids: nodeIds || null, query: q}
    });
    SIDES.forEach((s) => refreshEverywhere(s, agentOf(p, s)));
    if (typeof showQuickNotification === 'function') showQuickNotification('Imported Context Palace into Brain A & Brain B!');
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
      lastTokenBalance = (s.account && s.account.token_balance != null) ? Number(s.account.token_balance) : null;
      VIEWS.forEach((p) => {
        const a = el(p + 'Account');
        if (a) {
          a.textContent = 'Billed to ' + (s.account.username || s.account.peer_id) + ' · ' + s.account.token_balance + ' tokens';
          a.className = 'cursor-pointer text-[11px] font-mono text-[#111111] bg-[#ffffff] border border-[#111111] hover:bg-[#111111] hover:text-[#ecf1e6] px-2.5 py-1 rounded-full transition';
        }
        window.arenaUpdatePreAuthCap(p);
        SIDES.forEach((side) => { const b = el(p + 'DriveBtn' + side); if (b) b.classList.toggle('hidden', !driveAllowed); });
      });
      VIEWS.forEach((p) => SIDES.forEach((side) => refresh(p, side)));
    } catch (e) {
      lastTokenBalance = null;
      VIEWS.forEach((p) => {
        const a = el(p + 'Account');
        if (a) {
          a.textContent = e.status === 401 || e.status === 403 ? 'Sign in to duel' : 'Arena offline';
          a.className = 'cursor-pointer text-[11px] font-mono bg-[#ffffff] border px-2.5 py-1 rounded-full transition ' + (e.status === 401 || e.status === 403 ? 'text-[#111111] border-[#111111] hover:bg-[#111111] hover:text-[#ecf1e6]' : 'text-[#8a1c1c] border-[#8a1c1c]');
        }
        window.arenaUpdatePreAuthCap(p);
        SIDES.forEach((side) => msg(p, side, e.message, true));
      });
      if (promptSignIn === true && (e.status === 401 || e.status === 403) && typeof openAccountModal === 'function') { try { openAccountModal(false); } catch (x) {} }
    }
  }
  window.arenaCtxStatus = status;

  function sayBoth(p, text) { SIDES.forEach((side) => { el(p + 'Result' + side).textContent = text; }); }

  function hoistVoteModal(p) {
    const form = el(p + 'VoteForm');
    if (!form) return null;
    if (typeof document !== 'undefined' && document.body && typeof document.body.appendChild === 'function' && form.parentNode !== document.body) {
      try { document.body.appendChild(form); } catch (e) {}
    }
    return form;
  }

  function syncVoteChoiceStyles(p) {
    const pickA = el(p + 'VotePickA');
    const pickB = el(p + 'VotePickB');
    const cardA = el(p + 'VoteCardA');
    const cardB = el(p + 'VoteCardB');
    const base = 'inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-mono font-bold cursor-pointer transition select-none ';
    if (cardA) cardA.className = base + (pickA && pickA.checked ? 'bg-[#111111] text-[#ecf1e6] border-[#111111]' : 'border-[#111111]/40 bg-[#f4f8f0] text-[#111111] hover:border-[#111111]');
    if (cardB) cardB.className = base + (pickB && pickB.checked ? 'bg-[#111111] text-[#ecf1e6] border-[#111111]' : 'border-[#111111]/40 bg-[#f4f8f0] text-[#111111] hover:border-[#111111]');
  }

  function setHidden(node, hide) {
    if (!node || !node.classList) return;
    if (hide) {
      if (typeof node.classList.add === 'function') node.classList.add('hidden');
    } else if (typeof node.classList.remove === 'function') {
      node.classList.remove('hidden');
    }
  }

  const BADGE_BASE_CLS = 'rounded-xl px-3 py-2 flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono ';

  function setLastVoteBadge(p, mode, text) {
    const badge = el(p + 'LastVoteBadge');
    const txt = el(p + 'LastVoteText');
    const reopenBtn = el(p + 'ReopenVoteBtn');
    if (txt && text !== undefined) txt.textContent = text;
    if (!badge) return;
    if (mode === 'dismissed') {
      badge.className = BADGE_BASE_CLS + 'bg-[#f4f8f0] border border-[#111111] text-[#111111]';
      setHidden(badge, false);
      setHidden(reopenBtn, false);
      return;
    }
    if (mode === 'voted') {
      badge.className = BADGE_BASE_CLS + 'bg-[#ecf1e6] border border-[#107a47] text-[#107a47] font-semibold';
      setHidden(badge, false);
      setHidden(reopenBtn, true);
      return;
    }
    badge.className = 'hidden ' + BADGE_BASE_CLS + 'bg-[#ffffff] border border-[#111111] text-[#111111]';
    setHidden(badge, true);
    setHidden(reopenBtn, true);
  }

  function closeVoteModal(p) {
    const form = el(p + 'VoteForm');
    setHidden(form, true);
  }

  function openVoteModal(p, winnerSide) {
    VIEWS.forEach((other) => { if (other !== p) closeVoteModal(other); });
    const form = hoistVoteModal(p);
    if (!form) return false;
    const pickA = el(p + 'VotePickA');
    const pickB = el(p + 'VotePickB');
    if (pickA) pickA.checked = (winnerSide === 'A');
    if (pickB) pickB.checked = (winnerSide === 'B');
    syncVoteChoiceStyles(p);
    const duel = lastDuel[p] || {};
    if (!duel.voted) setLastVoteBadge(p, 'hidden');
    const promptMeta = el(p + 'VoteModalPrompt');
    if (promptMeta) {
      const snippet = (duel.prompt || '').trim();
      promptMeta.textContent = snippet ? ('Run complete · "' + snippet.slice(0, 72) + (snippet.length > 72 ? '…' : '') + '"') : 'Pick Brain A or Brain B while reviewing answers above.';
    }
    const st = el(p + 'VoteStatus');
    if (st) st.textContent = winnerSide ? ('Brain ' + winnerSide + ' selected — optional note & Submit (+150 XP).') : 'Run complete — pick Brain A or Brain B and submit (+150 XP).';
    setHidden(form, false);
    const inp = el(p + 'VoteReasonInput');
    if (inp && typeof inp.focus === 'function') inp.focus();
    return true;
  }

  window.arenaDuelCloseVoteModal = function (p) {
    closeVoteModal(p);
    const duel = lastDuel[p];
    if (duel && duel.match_id && !duel.voted) {
      setLastVoteBadge(p, 'dismissed', 'Duel ready · Cast vote (+150 XP)');
    }
  };
  window.arenaDuelReopenVote = function (p) {
    const duel = lastDuel[p];
    if (!duel || !duel.match_id) {
      if (typeof showQuickNotification === 'function') showQuickNotification('Click "Run Arena" first: votes are recorded after both brains answer.');
      return false;
    }
    const pickA = el(p + 'VotePickA');
    const pickB = el(p + 'VotePickB');
    const side = (pickB && pickB.checked) ? 'B' : ((pickA && pickA.checked) ? 'A' : null);
    return openVoteModal(p, side);
  };
  window.arenaDuelSelectVoteSide = function (p, side) {
    const pickA = el(p + 'VotePickA');
    const pickB = el(p + 'VotePickB');
    if (pickA) pickA.checked = (side === 'A');
    if (pickB) pickB.checked = (side === 'B');
    syncVoteChoiceStyles(p);
    const st = el(p + 'VoteStatus');
    if (st) st.textContent = 'Brain ' + side + ' selected — click Submit Vote (+150 XP).';
  };

  window.arenaDuelRun = async function (p) {
    if (typeof initAudio === 'function') { try { initAudio(); } catch (e) {} }
    const prompt = (el(p + 'PromptInput').value || '').trim();
    if (!prompt) return;
    window.arenaUpdatePreAuthCap(p);
    const btn = el(p + 'RunBtn');
    if (btn) btn.disabled = true;
    lastDuel[p] = null;
    closeVoteModal(p);
    setLastVoteBadge(p, 'hidden', '');
    const models = {A: modelOf(p, 'A'), B: modelOf(p, 'B')};
    const telemetry = {A: null, B: null};
    SIDES.forEach((side) => {
      el(p + 'Result' + side).textContent = 'Brain ' + side + ' (' + models[side] + ') is reading ' + agentOf(p, side) + '…';
      el(p + 'Bill' + side).textContent = '';
      const sav = el(p + 'Savings' + side);
      if (sav) {
        sav.className = 'text-[10px] font-mono text-[#4a4a4a] bg-[#ffffff] border border-[#111111]/25 rounded-lg px-2 py-1 min-h-[22px] flex items-center justify-between gap-2';
        sav.textContent = 'Running telemetry…';
      }
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
          const cap = el(p + 'PreAuthCap');
          if (cap) {
            cap.textContent = 'PRE-AUTH CAP: EXCEEDED (402)';
            cap.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full bg-[#ecf1e6] text-[#8a1c1c] border border-[#8a1c1c] text-[10px] font-mono font-semibold';
          }
        } else {
          sayBoth(p, 'Battle error: ' + e.message);
        }
        SIDES.forEach((side) => {
          const sav = el(p + 'Savings' + side);
          if (sav) {
            sav.className = 'text-[10px] font-mono text-[#8a1c1c] bg-[#ffffff] border border-[#8a1c1c] rounded-lg px-2 py-1 min-h-[22px] flex items-center justify-between gap-2 font-semibold';
            sav.textContent = '● ' + (e.status === 402 ? 'CAP ALERT · ' : 'ERROR · ') + e.message;
          }
        });
        return;
      }
      const results = {};
      let matchedFiles = 0;
      let matchedTokens = 0;
      // Sequential on purpose: side B is checked against the balance left after side A.
      for (const side of SIDES) {
        const startedAt = nowMs();
        try {
          results[side] = await api('/api/chat', {body: {
            model: models[side], prompt, arena: true, match_id: match.match_id, arena_side: side,
            agent_id: agentOf(p, side), use_context: !!(el(p + 'UseCtx' + side) || {}).checked,
          }});
          const r = results[side];
          const elapsedSec = Math.max(0.01, (nowMs() - startedAt) / 1000);
          const ttft = (r && r.ttft_s != null) ? Number(r.ttft_s) : (r && r.latency_ms != null ? Number(r.latency_ms) / 1000 : elapsedSec);
          el(p + 'Result' + side).textContent = (r.choices && r.choices[0] && r.choices[0].message && r.choices[0].message.content) || r.text || '(empty answer)';
          const b = r.billing;
          telemetry[side] = {cost: b ? Number(b.cost_usd || 0) : 0, tokens: b ? Number(b.tokens_billed || 0) : 0, ttft: ttft, model: models[side], simulated: String(r.id || '').indexOf('sim-') === 0};
          renderSavingsDelta(p, telemetry);
          renderUsed(p, side, {context: r.arena_context});
          if (r.arena_context) {
            matchedFiles += Number((r.arena_context.files || []).length);
            matchedTokens += Number(r.arena_context.tokens || 0);
          }
        } catch (e) {
          el(p + 'Result' + side).textContent = e.status === 402 ? ((e.message || 'Not enough tokens for this side.') + ' Top up to continue.') : ('Brain ' + side + ' error: ' + e.message);
          const sav = el(p + 'Savings' + side);
          if (sav) {
            sav.className = 'text-[10px] font-mono text-[#8a1c1c] bg-[#ffffff] border border-[#8a1c1c] rounded-lg px-2 py-1 min-h-[22px] flex items-center justify-between gap-2 font-semibold';
            sav.textContent = '● ' + (e.status === 402 ? 'CAP ALERT · ' : 'ERROR · ') + e.message;
          }
          if (e.status === 402) {
            const cap = el(p + 'PreAuthCap');
            if (cap) {
              cap.textContent = 'PRE-AUTH CAP: EXCEEDED (402)';
              cap.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full bg-[#ecf1e6] text-[#8a1c1c] border border-[#8a1c1c] text-[10px] font-mono font-semibold';
            }
          }
        }
      }
      if (matchedFiles > 0 || matchedTokens > 0) {
        updateRagBadge(p, {files: matchedFiles, tokens: matchedTokens});
      }
      if (results.A && results.B) {
        lastDuel[p] = {a: models.A, b: models.B, prompt, match_id: match.match_id};
        const total = (results.B.billing && results.B.billing.match_total_cost_usd) || 0;
        if (typeof showQuickNotification === 'function') showQuickNotification('Duel billed to your account: $' + Number(total).toFixed(6) + ' (' + match.match_id.slice(0, 14) + '…)');
        openVoteModal(p, null);
      }
      status();
    } finally {
      if (btn) btn.disabled = false;
    }
  };

  window.arenaDuelVote = async function (p, side, opts) {
    if (typeof initAudio === 'function') { try { initAudio(); } catch (e) {} }
    const duel = lastDuel[p];
    if (!duel || !duel.match_id) {
      if (typeof showQuickNotification === 'function') showQuickNotification('Click "Run Arena" first: votes are recorded after both brains answer.');
      return;
    }
    const winnerSide = side === 'B' ? 'B' : 'A';
    if (!(opts && opts.immediate) && openVoteModal(p, winnerSide)) {
      return;
    }
    return window.arenaDuelSubmitVote(p, winnerSide);
  };

  window.arenaDuelSubmitVote = async function (p, explicitSide) {
    const duel = lastDuel[p];
    if (!duel || !duel.match_id) {
      if (typeof showQuickNotification === 'function') showQuickNotification('Click "Run Arena" first before submitting a vote.');
      return;
    }
    const pickA = el(p + 'VotePickA');
    const pickB = el(p + 'VotePickB');
    let winnerSide = explicitSide || ((pickB && pickB.checked) ? 'B' : ((pickA && pickA.checked) ? 'A' : ''));
    if (!winnerSide && !pickA && !pickB) winnerSide = 'A';
    if (!winnerSide) {
      const st = el(p + 'VoteStatus');
      if (st) st.textContent = 'Select Brain A or Brain B first before submitting.';
      if (typeof showQuickNotification === 'function') showQuickNotification('Pick Brain A or Brain B in the vote popup first.');
      return;
    }
    const winnerModel = winnerSide === 'A' ? duel.a : duel.b;
    const tag = (el(p + 'VoteTagSelect') && el(p + 'VoteTagSelect').value) || '';
    const note = (el(p + 'VoteReasonInput') && el(p + 'VoteReasonInput').value || '').trim();
    const feedback = [tag, note].filter(Boolean).join(' — ');
    if (typeof playXpChime === 'function') { try { playXpChime(); } catch (e) {} }
    try {
      await api('/api/mesh/arena/vote', {body: {
        match_id: duel.match_id, winner_side: winnerSide, feedback,
        prompt_preview: (duel.prompt || '').substring(0, 40),
        display_name: peer(), room: (typeof currentRoom !== 'undefined' ? currentRoom : 'main'),
      }});
      const st = el(p + 'VoteStatus');
      if (st) st.textContent = 'Recorded Brain ' + winnerSide + ' (' + winnerModel + ') (+150 XP)' + (feedback ? (' · "' + feedback + '"') : '');
      duel.voted = true;
      const fbSnippet = feedback
        ? (' · "' + feedback.slice(0, 72) + (feedback.length > 72 ? '…' : '') + '"')
        : '';
      setLastVoteBadge(p, 'voted', '🏆 Last Vote: Brain ' + winnerSide + ' (' + winnerModel + ') · +150 XP' + fbSnippet);
      closeVoteModal(p);
      if (el(p + 'VoteReasonInput')) el(p + 'VoteReasonInput').value = '';
      if (typeof showQuickNotification === 'function') showQuickNotification('🏆 Vote recorded for ' + winnerModel + ' (' + duel.a + ' vs ' + duel.b + '). +150 XP.');
      if (typeof pollMeshState === 'function') pollMeshState();
    } catch (e) {
      const st = el(p + 'VoteStatus');
      if (st) st.textContent = 'Vote error: ' + e.message;
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
    if (typeof showQuickNotification === 'function') showQuickNotification('Sent Brain ' + side + ' output to Workstation');
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
    VIEWS.forEach((p) => { window.arenaUpdatePreAuthCap(p); hoistVoteModal(p); });
    loadModels();
    status();
    // Re-check after sign-in / account creation in another tab or the account modal.
    if (typeof window.addEventListener === 'function') {
      window.addEventListener('focus', () => status());
      window.addEventListener('storage', (ev) => { if (ev.key && ev.key.indexOf('tincan_') === 0) status(); });
    }
  }
  if (document.readyState === 'loading' && typeof document.addEventListener === 'function') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
</script>
"""


ARENA_DUEL_RESPONSIVE_CSS = r"""
<style id="arenaDuelResponsiveCss">
[data-arena-vote-modal].hidden,
[data-arena-last-vote-badge].hidden {
  display: none !important;
}
@media (max-width: 640px) {
  [data-arena-vote-modal] {
    left: 0.75rem !important;
    right: 0.75rem !important;
    width: auto !important;
    max-width: none !important;
    bottom: 4.5rem !important;
    box-sizing: border-box !important;
  }
  [data-arena-last-vote-badge] {
    align-items: flex-start !important;
  }
}
</style>
"""


def apply_arena_duel(page: str) -> str:
    """Replace every ``<!--ARENA_DUEL:prefix-->`` marker and add the CSS & script once."""
    labels = {p: label for p, _win, label in ARENA_VIEWS}
    prefixes = []

    def _sub(m: "re.Match[str]") -> str:
        p = m.group(1)
        prefixes.append(p)
        return render_arena_duel(p, labels.get(p, p))

    page = _MARKER_RE.sub(_sub, page)
    if prefixes:
        injections = []
        if 'id="arenaDuelResponsiveCss"' not in page:
            injections.append(ARENA_DUEL_RESPONSIVE_CSS)
        if 'id="arenaDuelScript"' not in page:
            import json as _json
            injections.append(ARENA_DUEL_SCRIPT.replace("__ARENA_VIEWS__", _json.dumps(prefixes)))
        if injections:
            bundle = "".join(injections)
            end = page.rfind("</body>")
            page = page[:end] + bundle + page[end:] if end != -1 else page + bundle
    return page
