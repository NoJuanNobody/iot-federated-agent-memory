"""TinCan Mesh OS: the reusable one-click install card.

One component, any mount point. The card shows the install commands (brew,
``curl | bash``, ``npx skills``, AI Chat) behind four tabs, a copy box and the
quick actions (Copy install command, brew install, macOS .command, npx skills).

* ``render_install_card(card_id)`` returns the card markup. Every element is
  found through ``data-*`` attributes inside the card root, so any number of
  cards can live on one page without id collisions.
* ``INSTALL_CARD_JS`` defines ``window.TinCanInstallCard`` (``mount`` / ``init``)
  and the legacy global helpers (``switchInstallCmdTab`` and friends).
* ``apply_install_card(html)`` expands ``<!--TC_INSTALL_CARD {"id": "..."}-->``
  placeholders and fills the ``/*TC_INSTALL_CARD_JS*/`` slot in the page script.
"""

from __future__ import annotations

import html as _html
import json
import re
from typing import Dict, Optional

BASE_URL = "https://iot-federated-agent-memory-production.up.railway.app"

#: The exact commands the card offers. Tab key -> command text.
INSTALL_COMMANDS: Dict[str, str] = {
    "brew": f"brew install {BASE_URL}/Formula/tincan.rb",
    "curl": f"curl -sSL {BASE_URL}/install.sh | bash",
    "npx": "npx skills add NoJuanNobody/tincan-skills -g -y",
    "chat": (
        f"curl -s -X POST {BASE_URL}/api/chat -H \"Content-Type: application/json\" "
        "-d '{\"prompt\":\"Hello world!\"}'"
    ),
}

#: Order and labels of the tabs; ``curl`` is the default tab.
INSTALL_TABS = (
    ("brew", "\U0001F37A brew"),
    ("curl", "curl | bash"),
    ("npx", "npx skills"),
    ("chat", "AI Chat"),
)
DEFAULT_TAB = "curl"

#: The one command the "brew install" quick action runs in the shell.
BREW_SHELL_COMMAND = "brew install tincan context-palace"

INSTALL_CARD_PLACEHOLDER_RE = re.compile(r"<!--TC_INSTALL_CARD (\{.*?\})-->")
INSTALL_CARD_JS_SLOT = "/*TC_INSTALL_CARD_JS*/"

_TAB_ON = "px-2 py-0.5 bg-black text-[#ecf1e6] rounded-full border border-black font-semibold transition"
_TAB_OFF = "px-2 py-0.5 bg-transparent text-black rounded-full border border-black font-semibold transition"
_PILL_SOLID = "px-2.5 py-1 bg-black text-[#ecf1e6] rounded-full text-[10px] font-semibold hover:opacity-85 active:scale-95 transition"
_PILL_LINE = "px-2.5 py-1 border border-black text-black rounded-full text-[10px] font-semibold hover:bg-black hover:text-[#ecf1e6] active:scale-95 transition"


def render_install_card(card_id: str = "install", compact: bool = True, shell: Optional[str] = None) -> str:
    """Return the install card markup for one mount point.

    ``card_id`` only namespaces the root element id; nothing inside the card
    relies on a global id, so several cards can coexist. ``shell`` is an
    optional CSS selector of a mounted TinCanShell container: the "brew install"
    action runs in it and "Copy install command" leaves its note there.
    """
    cid = _html.escape(str(card_id), quote=True)
    shell_attr = f' data-shell="{_html.escape(str(shell), quote=True)}"' if shell else ""
    tabs = "\n".join(
        f'            <button type="button" data-tab="{key}" class="{_TAB_ON if key == DEFAULT_TAB else _TAB_OFF}">{label}</button>'
        for key, label in INSTALL_TABS
    )
    hidden = "\n".join(
        f'            <code data-cmd="{key}">{_html.escape(cmd, quote=False)}</code>'
        for key, cmd in INSTALL_COMMANDS.items()
    )
    pad = "p-3" if compact else "p-4"
    return f"""<div id="tcInstallCard-{cid}" data-tc-install="{cid}" data-default-tab="{DEFAULT_TAB}"{shell_attr} class="tc-install {pad} space-y-2 font-mono text-xs bg-[#f4f8f0] border border-black rounded-xl min-w-0">
          <div class="flex flex-wrap items-center justify-between gap-1.5">
            <div class="text-[10px] font-bold uppercase text-black tracking-wider">⚡ One-Click Terminal Install</div>
            <div class="flex flex-wrap items-center gap-1 text-[9px]" role="tablist" aria-label="Install method">
{tabs}
            </div>
          </div>
          <div class="bg-white border border-black rounded-xl p-2 flex items-center justify-between gap-2">
            <code data-role="display" class="text-[10px] text-black font-semibold select-all overflow-x-auto whitespace-nowrap min-w-0">{_html.escape(INSTALL_COMMANDS[DEFAULT_TAB], quote=False)}</code>
            <button type="button" data-action="copy" class="px-2.5 py-1 bg-black text-[#ecf1e6] rounded-full text-[10px] font-bold shrink-0 hover:opacity-85 active:scale-95 transition">\U0001F4CB Copy</button>
          </div>
          <div class="flex flex-wrap items-center gap-1.5 pt-0.5">
            <button type="button" data-action="copy-install" class="{_PILL_SOLID}">Copy install command</button>
            <button type="button" data-action="brew" class="{_PILL_LINE}">\U0001F37A brew install</button>
            <a href="/install.command" download="Install-TinCan.command" class="{_PILL_LINE} no-underline">⬇ macOS .command</a>
            <button type="button" data-action="npx" class="{_PILL_LINE}">npx skills</button>
          </div>
          <div class="hidden">
{hidden}
          </div>
        </div>"""


def expand_install_cards(html: str) -> str:
    """Replace every ``<!--TC_INSTALL_CARD {...}-->`` placeholder with the card."""

    def _sub(m: "re.Match[str]") -> str:
        try:
            spec = json.loads(m.group(1))
        except ValueError:
            spec = {}
        return render_install_card(spec.get("id", "install"), bool(spec.get("compact", True)), spec.get("shell"))

    return INSTALL_CARD_PLACEHOLDER_RE.sub(_sub, html)


INSTALL_CARD_JS = r"""
    // ---- One-click install card (install_card.py) ---------------------------
    // Reusable: every card is self-contained (data-* hooks inside its own root).
    window.TinCanInstallCard = (function () {
      const BREW_SHELL = __BREW_SHELL__;
      const cards = [];
      const TAB_ON = __TAB_ON__;
      const TAB_OFF = __TAB_OFF__;

      function copyText(text, btn) {
        if (typeof copyToClipboard === 'function') return copyToClipboard(text, btn);
        try { navigator.clipboard.writeText(text); } catch (e) {}
      }

      function mount(root, opts) {
        if (typeof root === 'string') root = document.querySelector(root);
        if (!root) return null;
        if (root.__tcInstall) return root.__tcInstall;
        opts = opts || {};
        const q = (sel) => root.querySelector(sel);
        const cmdText = (tab) => { const el = q('[data-cmd="' + tab + '"]'); return el ? el.textContent : ''; };
        let tab = root.getAttribute('data-default-tab') || 'curl';

        function shell() {
          const s = typeof opts.shell === 'function' ? opts.shell() : opts.shell;
          if (s) return s;
          const sel = root.getAttribute('data-shell');
          const host = sel ? document.querySelector(sel) : null;
          return (host && host.__tcShell) || null;
        }

        function setTab(next) {
          tab = ['brew', 'curl', 'npx', 'chat'].indexOf(next) >= 0 ? next : 'curl';
          const disp = q('[data-role="display"]');
          if (disp) disp.textContent = cmdText(tab);
          root.querySelectorAll('[data-tab]').forEach(b => {
            const on = b.getAttribute('data-tab') === tab;
            b.className = on ? TAB_ON : TAB_OFF;
            b.setAttribute('aria-selected', on ? 'true' : 'false');
          });
        }

        function installNote(text) {
          const s = shell();
          const html = 'Copied to your clipboard. Paste it into the terminal on your computer to install TinCan:<br><code class="select-all break-all">' +
            String(text).replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c])) + '</code>';
          if (s && s.note) s.note(html);
        }

        const api = {
          root,
          active: () => tab,
          command: (t) => cmdText(t || tab),
          setTab,
          copy(btn) { copyText(cmdText(tab), btn); },
          copyInstall() {
            // A browser cannot run commands on your computer: copy the real installer
            // command and say so, instead of printing a pretend install log.
            const text = cmdText(tab);
            if (tab === 'brew') {
              copyText(text);
              const s = shell();
              if (s) s.exec(BREW_SHELL);
              return;
            }
            if (text) copyText(text);
            installNote(text);
          },
          brew() { setTab('brew'); const s = shell(); if (s) s.exec(BREW_SHELL); },
          npx(btn) { copyText(cmdText('npx'), btn); },
        };

        root.addEventListener('click', (ev) => {
          const t = ev.target.closest('[data-tab],[data-action]');
          if (!t || !root.contains(t)) return;
          if (t.hasAttribute('data-tab')) { setTab(t.getAttribute('data-tab')); return; }
          const a = t.getAttribute('data-action');
          if (a === 'copy') api.copy(t);
          else if (a === 'copy-install') api.copyInstall();
          else if (a === 'brew') api.brew();
          else if (a === 'npx') api.npx(t);
        });

        root.__tcInstall = api;
        cards.push(api);
        setTab(tab);
        return api;
      }

      function init() {
        document.querySelectorAll('[data-tc-install]').forEach(el => mount(el));
      }
      return { mount, init, cards, commands: __COMMANDS__ };
    })();

    // Legacy globals (the quickstart modal and older callers use these names).
    function _tcPrimaryInstallCard() { const c = window.TinCanInstallCard.cards; return c.length ? c[0] : null; }
    function switchInstallCmdTab(tab) { const c = _tcPrimaryInstallCard(); if (c) c.setTab(tab); }
    function copyActiveInstallCmd(btnEl) { const c = _tcPrimaryInstallCard(); if (c) c.copy(btnEl); }
    function copyCommand(id, btnEl) {
      const el = document.getElementById(id);
      if (!el) return;
      copyToClipboard(el.innerText, btnEl);
    }
    function simulateOneClickInstall() {
      const win = document.getElementById('win-terminal');
      if (win && win.classList.contains('hidden')) win.classList.remove('hidden');
      const c = _tcPrimaryInstallCard();
      if (c) c.copyInstall();
    }
"""


def install_card_js() -> str:
    """The card script with the command table and tab styles filled in."""
    return (
        INSTALL_CARD_JS
        .replace("__BREW_SHELL__", json.dumps(BREW_SHELL_COMMAND))
        .replace("__TAB_ON__", json.dumps(_TAB_ON))
        .replace("__TAB_OFF__", json.dumps(_TAB_OFF))
        .replace("__COMMANDS__", json.dumps(INSTALL_COMMANDS))
    )


def apply_install_card(html: str, js: Optional[str] = None) -> str:
    """Expand card placeholders and inject the card script (idempotent)."""
    html = expand_install_cards(html)
    return html.replace(INSTALL_CARD_JS_SLOT, js if js is not None else install_card_js())
