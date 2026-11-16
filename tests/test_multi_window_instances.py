"""Tests for multi-instance Mesh OS windows with independent content per instance."""

from __future__ import annotations

import json
import re
import shutil
import subprocess

from iot_federated_agent_memory.arena_duel_ui import ARENA_DUEL_SCRIPT
from iot_federated_agent_memory.copilot_ui import COPILOT_SCRIPT
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI
from iot_federated_agent_memory.window_chrome import CELADON_HEAD, render_titlebar


def _run_node(js_code: str) -> dict:
    node = shutil.which("node")
    assert node, "node binary required to run multi-window JS runtime checks"
    res = subprocess.run([node, "-e", js_code], capture_output=True, text=True)
    if res.returncode != 0:
        raise AssertionError(f"node failed (rc={res.returncode}):\nSTDERR:\n{res.stderr}\nSTDOUT:\n{res.stdout}")
    lines = [ln for ln in res.stdout.strip().splitlines() if ln.strip()]
    return json.loads(lines[-1])


def _extract_js_range(source: str, start_marker: str, end_marker: str | None = None) -> str:
    s_idx = source.index(start_marker)
    if end_marker is None:
        return source[s_idx:]
    e_idx = source.index(end_marker, s_idx)
    return source[s_idx:e_idx]


def test_titlebar_and_celadon_css_have_new_instance_and_embed_rules():
    tb = render_titlebar("win-terminal", "Terminal")
    assert 'class="tc-ctl tc-ctl--new"' in tb
    assert "openWindowInstance('win-terminal')" in tb
    assert 'class="tc-ctl tc-ctl--pop"' in tb

    for marker in (
        ".tc-ctl--new",
        ".tc-dragging-window iframe { pointer-events: none !important; }",
        ".mesh-window-instance .window-body",
        ".tc-instance-count",
        "body.tc-embed #desktopWorkspace",
        "body.tc-embed .mesh-window.popout-fullscreen .tc-titlebar",
    ):
        assert marker in CELADON_HEAD

    # Every expanded Mesh OS titlebar carries the + New window launcher
    for win_id in ("win-terminal", "win-arena", "win-board", "win-comms", "win-agentspace", "win-workstation", "win-copilot"):
        assert f"openWindowInstance('{win_id}')" in MESH_OS_HTML_UI


def test_open_window_instance_spawns_isolated_windows_and_syncs_dock():
    # Extract core window-manager + multi-instance JS block cleanly
    wm_block = _extract_js_range(
        MESH_OS_HTML_UI,
        "// Window Manager: Draggable, Resizable, Focus, Minimize, Maximize, Pop Out, Multi-Instance",
        "// Handle Pop-Out Single-Window Viewport Optimization",
    )

    out = _run_node(
        f"""
        const vm = require('vm');
        function makeEl(id, tag) {{
          const classes = new Set();
          const children = [];
          const attrs = {{}};
          const el = {{
            id: id || '',
            tagName: (tag || 'div').toUpperCase(),
            style: {{}},
            dataset: {{}},
            children,
            className: '',
            textContent: '',
            innerHTML: '',
            title: '',
            parentNode: null,
            classList: {{
              add(...cs) {{ cs.forEach(c => classes.add(c)); }},
              remove(...cs) {{ cs.forEach(c => classes.delete(c)); }},
              toggle(c, force) {{
                if (force === true) classes.add(c);
                else if (force === false) classes.delete(c);
                else if (classes.has(c)) classes.delete(c);
                else classes.add(c);
              }},
              contains(c) {{ return classes.has(c); }},
            }},
            appendChild(child) {{
              child.parentNode = el;
              children.push(child);
              if (child.id) elems[child.id] = child;
              return child;
            }},
            remove() {{
              if (el.parentNode && Array.isArray(el.parentNode.children)) {{
                el.parentNode.children = el.parentNode.children.filter(c => c !== el);
              }}
              if (el.id) delete elems[el.id];
            }},
            addEventListener() {{}},
            querySelector(sel) {{
              if (sel === '.tc-titlebar__title') return {{ textContent: attrs.title || el.id }};
              if (sel === '.tc-titlebar__icon') return {{ textContent: '📁' }};
              if (sel === '.tc-instance-count') return children.find(c => (c.className || '').includes('tc-instance-count')) || null;
              return null;
            }},
            getBoundingClientRect() {{ return {{ left: 80, top: 70, width: 780, height: 540 }}; }},
            _attrs: attrs,
          }};
          return el;
        }}
        const elems = {{
          desktopWorkspace: makeEl('desktopWorkspace', 'div'),
        }};
        ['win-terminal', 'win-tv', 'win-arena', 'win-call', 'win-comms', 'win-quests', 'win-moderator',
         'win-billing', 'win-board', 'win-network', 'win-agentspace', 'win-workstation', 'win-copilot', 'win-ai-home'].forEach(id => {{
          const w = makeEl(id, 'div');
          w._attrs.title = id.replace('win-', '');
          w.style.display = id === 'win-agentspace' ? 'flex' : 'none';
          if (id !== 'win-agentspace') w.classList.add('hidden');
          elems[id] = w;
          const dock = makeEl('dockBtn-' + id, 'button');
          elems['dockBtn-' + id] = dock;
        }});

        const msgHandlers = [];
        const popouts = [];
        const bodyClasses = new Set();
        const sandbox = {{
          console,
          Math,
          URLSearchParams,
          Set,
          Map,
          Date,
          JSON,
          parseInt,
          encodeURIComponent,
          setTimeout,
          clearTimeout,
          setInterval: () => 1,
          clearInterval() {{}},
          currentRoom: 'main',
          myPeerId: 'peer-1',
          isAdmin: false,
          singleWindowParam: null,
          instanceParam: '',
          isEmbedInstance: false,
          urlParams: new URLSearchParams(''),
          meshBus: {{ postMessage() {{}} }},
          document: {{
            body: Object.assign(makeEl('body', 'body'), {{
              classList: {{
                add: (...c) => c.forEach(x => bodyClasses.add(x)),
                remove: (...c) => c.forEach(x => bodyClasses.delete(x)),
                contains: (c) => bodyClasses.has(c),
              }},
            }}),
            getElementById: (id) => {{
              if (elems[id]) return elems[id];
              // Support dynamically populated subtitle inside innerHTML string check
              for (const k of Object.keys(elems)) {{
                if ((elems[k].innerHTML || '').includes(`id="${{id}}"`)) {{
                  if (!elems[id]) elems[id] = makeEl(id, 'span');
                  return elems[id];
                }}
              }}
              return null;
            }},
            createElement: (tag) => makeEl('', tag),
            querySelectorAll: (sel) => Object.values(elems).filter(e => sel === '.mesh-window' && e.id.startsWith('win-')),
          }},
          window: {{
            innerWidth: 1440,
            innerHeight: 900,
            location: {{ origin: 'https://tincan.local' }},
            addEventListener(type, fn) {{ if (type === 'message') msgHandlers.push(fn); }},
            removeEventListener() {{}},
            open(url, target) {{ popouts.push({{ url, target }}); return {{ closed: false }}; }},
          }},
          localStorage: {{
            _s: {{}},
            getItem(k) {{ return this._s[k] || null; }},
            setItem(k, v) {{ this._s[k] = String(v); }},
          }},
        }};
        sandbox.window.window = sandbox.window;
        vm.runInNewContext({json.dumps(wm_block)}, sandbox);

        const w2 = sandbox.window.openWindowInstance('win-agentspace', {{
          scope: 'topic',
          owner: 'topic-alpha',
          subtitle: 'Topic: alpha',
        }});
        const w3 = sandbox.window.openWindowInstance('win-agentspace', {{
          scope: 'dynamic',
          owner: 'sandbox-beta',
          subtitle: 'Sandbox: beta',
        }});
        const cop = sandbox.window.openWindowInstance('win-copilot', {{}});

        // Simulate child iframe posting TC_INSTANCE_TITLE update
        msgHandlers.forEach(fn => fn({{
          origin: 'https://tincan.local',
          data: {{ type: 'TC_INSTANCE_TITLE', instanceId: w2.dataset.instanceId, subtitle: 'topic: topic-alpha · notes.md' }},
        }}));

        const dockCountText = elems['dockBtn-win-agentspace'].querySelector('.tc-instance-count').textContent;
        // Test independent popout for spawned instance does not hide base win-agentspace
        sandbox.window.openPopoutWindow('win-agentspace', {{ instance: w2.dataset.instanceId, scope: 'topic', owner: 'topic-alpha' }});
        const baseHiddenAfterInstancePopout = elems['win-agentspace'].classList.contains('hidden');

        // Close w2 via minimizeWindow -> disposes spawned DOM instance
        sandbox.window.minimizeWindow(w2.id);
        const w2StillInDom = !!elems[w2.id];
        const w3StillInDom = !!elems[w3.id];
        const dockCountAfterClose = elems['dockBtn-win-agentspace'].querySelector('.tc-instance-count').textContent;

        console.log(JSON.stringify({{
          w2Id: w2.id,
          w3Id: w3.id,
          w2Html: w2.innerHTML,
          w3Html: w3.innerHTML,
          copHtml: cop.innerHTML,
          w2Pos: {{ left: w2.style.left, top: w2.style.top }},
          w3Pos: {{ left: w3.style.left, top: w3.style.top }},
          updatedSubtitle: (elems[w2.id + '--subtitle'] || {{}}).textContent || '',
          dockCountText,
          dockCountAfterClose,
          popouts,
          baseHiddenAfterInstancePopout,
          w2StillInDom,
          w3StillInDom,
        }}));
        """
    )

    assert out["w2Id"].startswith("win-agentspace--inst-2-")
    assert out["w3Id"].startswith("win-agentspace--inst-3-")
    assert out["w2Pos"] != out["w3Pos"]
    assert "embed=1" in out["w2Html"]
    assert "scope=topic&amp;owner=topic-alpha" in out["w2Html"]
    assert "scope=dynamic&amp;owner=sandbox-beta" in out["w3Html"]
    assert "thread=tincan-thread-2" in out["copHtml"] and "fresh=1" in out["copHtml"]
    assert out["updatedSubtitle"] == "topic: topic-alpha · notes.md"
    assert out["dockCountText"] == "3×"
    assert out["dockCountAfterClose"] == "2×"
    assert out["baseHiddenAfterInstancePopout"] is False
    assert out["w2StillInDom"] is False
    assert out["w3StillInDom"] is True
    assert len(out["popouts"]) == 1
    assert out["popouts"][0]["target"].startswith("_tincan_popout_win-agentspace_inst-2-")


def test_copilot_and_arena_per_instance_query_isolation():
    out = _run_node(
        f"""
        const vm = require('vm');
        function makeEl(id, extra) {{
          const classes = new Set();
          return Object.assign({{
            id,
            value: '',
            textContent: '',
            innerHTML: '',
            checked: false,
            style: {{}},
            classList: {{
              add(c) {{ classes.add(c); }},
              remove(c) {{ classes.delete(c); }},
              toggle(c, f) {{ if (f === false) classes.delete(c); else classes.add(c); }},
              contains(c) {{ return classes.has(c); }},
            }},
            addEventListener() {{}},
          }}, extra || {{}});
        }}
        const cpElems = {{
          'win-copilot': makeEl('win-copilot'),
          copilotThreadName: makeEl('copilotThreadName'),
          copilotThreadLog: makeEl('copilotThreadLog'),
          copilotPromptInput: makeEl('copilotPromptInput'),
          copilotModelSelect: makeEl('copilotModelSelect'),
          copilotPreflightCost: makeEl('copilotPreflightCost'),
          copilotActiveStatus: makeEl('copilotActiveStatus'),
          copilotHeaderRoute: makeEl('copilotHeaderRoute'),
          copilotContextFiles: makeEl('copilotContextFiles'),
          copilotActiveCapsules: makeEl('copilotActiveCapsules'),
          copilotArbitrageStats: makeEl('copilotArbitrageStats'),
        }};
        const parentMessages = [];
        const cpSandbox = {{
          console, URLSearchParams, Date, Math, Set, Map, JSON,
          fetch: async () => ({{ ok: true, json: async () => ({{}}) }}),
          document: {{
            readyState: 'complete',
            getElementById: (id) => cpElems[id] || null,
            querySelectorAll: () => [],
            addEventListener() {{}},
          }},
          window: {{
            location: {{ origin: 'https://tincan.local', search: '?window=win-copilot&embed=1&instance=inst-2&fresh=1&thread=topic-42-chat&priority=max&model=claude-brain&prompt=Audit+bridge&scope=topic&owner=topic-42' }},
            notifyParentInstanceTitle(sub) {{ parentMessages.push(sub); }},
          }},
          localStorage: {{ getItem: () => '', setItem() {{}} }},
        }};
        vm.runInNewContext({json.dumps(COPILOT_SCRIPT)}, cpSandbox);
        const cpState = cpSandbox.window.TinCanCopilot.getState();

        // Arena per-instance storage isolation
        const arenaStore = {{ 'tincan_arena_models': JSON.stringify({{ a: 'gemini-brain', b: 'claude-brain' }}) }};
        const arenaElems = {{
          arenaWinPromptInput: makeEl('arenaWinPromptInput', {{ value: 'default prompt' }}),
          arenaWinModelAInput: makeEl('arenaWinModelAInput', {{ value: 'gemini-brain', options: [{{ value: 'gemini-brain' }}, {{ value: 'openai-brain' }}, {{ value: 'grok-brain' }}] }}),
          arenaWinModelBInput: makeEl('arenaWinModelBInput', {{ value: 'claude-brain', options: [{{ value: 'claude-brain' }}, {{ value: 'openai-brain' }}, {{ value: 'grok-brain' }}] }}),
          arenaWinModelsNote: makeEl('arenaWinModelsNote'),
          arenaWinPreAuthCap: makeEl('arenaWinPreAuthCap'),
          arenaWinRagBadge: makeEl('arenaWinRagBadge'),
        }};
        const duelJs = {json.dumps(_extract_js_range(ARENA_DUEL_SCRIPT, "(function () {", "</script>"))}
          .replace("__ARENA_VIEWS__", '["arenaWin"]');
        const arSandbox = {{
          console, URLSearchParams, Date, Math, Set, Map, JSON,
          fetch: async () => ({{ ok: false, status: 503, json: async () => ({{}}) }}),
          document: {{
            readyState: 'complete',
            getElementById: (id) => arenaElems[id] || null,
            addEventListener() {{}},
          }},
          window: {{
            location: {{ origin: 'https://tincan.local', search: '?window=win-arena&embed=1&instance=inst-9&prompt=Compare+custom+instance+models' }},
          }},
          localStorage: {{
            getItem: (k) => (Object.prototype.hasOwnProperty.call(arenaStore, k) ? arenaStore[k] : null),
            setItem: (k, v) => {{ arenaStore[k] = String(v); }},
          }},
        }};
        arSandbox.window.window = arSandbox.window;
        vm.runInNewContext(duelJs, arSandbox);
        arSandbox.arenaWinModelAInput = arenaElems.arenaWinModelAInput;
        arenaElems.arenaWinModelAInput.value = 'openai-brain';
        arenaElems.arenaWinModelBInput.value = 'grok-brain';
        arSandbox.window.arenaDuelModelChange('arenaWin');

        console.log(JSON.stringify({{
          cpState: {{
            threadName: cpState.threadName,
            turnsLen: cpState.turns.length,
            model: cpState.model,
            scope: cpState.scope,
            ownerId: cpState.ownerId,
            promptVal: cpElems.copilotPromptInput.value,
          }},
          parentMessages,
          arenaPrompt: arenaElems.arenaWinPromptInput.value,
          arenaStoreKeys: Object.keys(arenaStore),
          arenaPrimaryUntouched: JSON.parse(arenaStore['tincan_arena_models']),
          arenaScopedPair: JSON.parse(arenaStore['tincan_arena_models::inst-9']),
        }}));
        """
    )

    assert out["cpState"]["threadName"] == "topic-42-chat"
    assert out["cpState"]["turnsLen"] == 0
    assert out["cpState"]["model"] == "claude-brain"
    assert out["cpState"]["scope"] == "topic"
    assert out["cpState"]["ownerId"] == "topic-42"
    assert out["cpState"]["promptVal"] == "Audit bridge"
    assert any("topic-42-chat" in m for m in out["parentMessages"])
    assert out["arenaPrompt"] == "Compare custom instance models"
    assert out["arenaPrimaryUntouched"] == {"a": "gemini-brain", "b": "claude-brain"}
    assert out["arenaScopedPair"] == {"a": "openai-brain", "b": "grok-brain"}


def test_embed_instance_content_params_and_board_new_win_launchers():
    assert "openWindowInstance('win-agentspace'" in MESH_OS_HTML_UI
    assert "openWindowInstance('win-board'" in MESH_OS_HTML_UI
    assert "if (!isEmbedInstance && !instanceParam)" in MESH_OS_HTML_UI
    assert "if (isEmbedInstance) document.body.classList.add('tc-embed');" in MESH_OS_HTML_UI

    boot_snippet = _extract_js_range(
        MESH_OS_HTML_UI,
        "function applyInstanceContentParams()",
        "    }, 2000);",
    ) + "\n    }, 2000);"
    out = _run_node(
        f"""
        const vm = require('vm');
        const called = [];
        const elems = {{
          spaceOwnerInput: {{ value: '' }},
          boardSearchInput: {{ value: '' }},
        }};
        const sandbox = {{
          console,
          URLSearchParams,
          myPeerId: 'default-peer',
          currentSpaceOwner: '',
          activeBoardTopicId: null,
          urlParams: new URLSearchParams('window=win-agentspace&embed=1&instance=inst-7&scope=topic&owner=topic-crdt&file=/src/merge.py&channel=architecture'),
          document: {{ getElementById: (id) => elems[id] || null }},
          window: {{
            location: {{ origin: 'https://tincan.local' }},
          }},
          setTimeout(fn) {{ fn(); }},
          switchSpaceScope(s) {{ called.push(['scope', s]); }},
          selectWorkstationTopicResult(tid) {{ called.push(['topicResult', tid]); }},
          refreshAgentSpace(arg) {{ called.push(['refresh', arg || '']); }},
          openAgentSpaceFile(f) {{ called.push(['file', f]); }},
          selectChatTarget(m, id, lbl) {{ called.push(['chat', m, id, lbl]); }},
          gatherDriveMirror(arg) {{ called.push(['drive', arg]); }},
        }};
        vm.runInNewContext({json.dumps(boot_snippet)}, sandbox);
        console.log(JSON.stringify({{
          ownerVal: elems.spaceOwnerInput.value,
          globalOwner: sandbox.window.currentSpaceOwner,
          called,
        }}));
        """
    )

    assert out["ownerVal"] == "topic-crdt"
    assert out["globalOwner"] == "topic-crdt"
    assert ["scope", "topic"] in out["called"]
    assert ["file", "/src/merge.py"] in out["called"]
    assert ["chat", "channel", "architecture", "#architecture"] in out["called"]
    # Guarded: 2s background boot MUST NOT overwrite pinned ?owner=topic-crdt with default-peer
    assert ["refresh", "background"] not in out["called"]

