"""Tests for Plan B: Context Palace Inline Inspector/CRUD, Inventory Tabs, & Active Capsule Chips."""

from __future__ import annotations

import json
import re
import subprocess
import zipfile
from pathlib import Path

from iot_federated_agent_memory.copilot_ui import (
    COPILOT_CSS,
    COPILOT_SCRIPT,
    apply_copilot_ui,
    render_copilot_window_html,
)


def _extract_dom_elements_spec(html: str) -> list[dict[str, object]]:
    """Extract (id, classes) pairs from rendered HTML for Node VM DOM fidelity."""
    specs: list[dict[str, object]] = []
    seen: set[str] = set()
    for match in re.finditer(r"<([a-zA-Z0-9_-]+)\b([^>]*)>", html, flags=re.DOTALL):
        attrs = match.group(2)
        id_match = re.search(r'\bid="([^"]+)"', attrs)
        if not id_match:
            continue
        el_id = id_match.group(1)
        if el_id in seen:
            continue
        seen.add(el_id)
        class_match = re.search(r'\bclass="([^"]*)"', attrs)
        classes = class_match.group(1).split() if class_match else []
        value_match = re.search(r'\bvalue="([^"]*)"', attrs)
        initial_value = value_match.group(1) if value_match else ""
        specs.append({"id": el_id, "classes": classes, "value": initial_value})
    return specs


def _run_copilot_node(test_body: str, *, mock_handler_js: str = "") -> dict:
    """Execute COPILOT_SCRIPT inside a realistic Node.js VM harness with DOM & fetch mocks."""
    html = render_copilot_window_html()
    dom_specs = _extract_dom_elements_spec(html)

    node_script = f"""
const vm = require('vm');

const DOM_SPECS = {json.dumps(dom_specs)};
const COPILOT_JS = {json.dumps(COPILOT_SCRIPT)};

function makeClassList(initialClasses) {{
  const set = new Set(Array.isArray(initialClasses) ? initialClasses : []);
  return {{
    add: (...cls) => cls.forEach(c => c && set.add(c)),
    remove: (...cls) => cls.forEach(c => set.delete(c)),
    toggle: (c, force) => {{
      if (force === true) {{ set.add(c); return true; }}
      if (force === false) {{ set.delete(c); return false; }}
      if (set.has(c)) {{ set.delete(c); return false; }}
      set.add(c); return true;
    }},
    contains: (c) => set.has(c),
    toArray: () => Array.from(set),
  }};
}}

function makeElem(id, initialClasses, initialValue) {{
  const listeners = {{}};
  const classList = makeClassList(initialClasses);
  const el = {{
    id,
    value: initialValue || '',
    textContent: '',
    innerHTML: '',
    disabled: false,
    scrollTop: 0,
    scrollHeight: 120,
    style: {{}},
    children: [],
    _attrs: {{}},
    classList,
    setAttribute(k, v) {{ this._attrs[k] = String(v); }},
    getAttribute(k) {{ return this._attrs[k] ?? null; }},
    addEventListener(evt, fn) {{
      if (!listeners[evt]) listeners[evt] = [];
      listeners[evt].push(fn);
    }},
    dispatchEvent(evtObj) {{
      const name = typeof evtObj === 'string' ? evtObj : evtObj.type;
      (listeners[name] || []).forEach(fn => fn(evtObj));
    }},
    click() {{ this.dispatchEvent({{ type: 'click', target: this, preventDefault() {{}} }}); }},
    appendChild(c) {{ this.children.push(c); return c; }},
    removeChild(c) {{
      const i = this.children.indexOf(c);
      if (i >= 0) this.children.splice(i, 1);
      return c;
    }},
    focus() {{ this._focused = true; }},
  }};
  Object.defineProperty(el, 'className', {{
    get() {{ return classList.toArray().join(' '); }},
    set(val) {{
      const next = String(val || '').split(/\\s+/).filter(Boolean);
      classList.toArray().forEach(c => classList.remove(c));
      next.forEach(c => classList.add(c));
    }},
  }});
  return el;
}}

const elements = {{}};
for (const spec of DOM_SPECS) {{
  elements[spec.id] = makeElem(spec.id, spec.classes, spec.value);
}}

const fetchCalls = [];
const promptCalls = [];
const alertCalls = [];
const confirmCalls = [];
const arenaRefreshCalls = [];
const localStore = {{}};

function defaultMockFetch(url, opts) {{
  const method = (opts && opts.method) || 'GET';
  let body = null;
  if (opts && opts.body) {{
    try {{ body = JSON.parse(opts.body); }} catch (_) {{ body = opts.body; }}
  }}
  fetchCalls.push({{ url, method, body }});
  if (typeof customMockFetch === 'function') {{
    const customRes = customMockFetch(url, opts, body);
    if (customRes !== undefined) return customRes;
  }}
  if (url.startsWith('/api/arena/context/inventory')) {{
    return Promise.resolve({{
      ok: true,
      json: async () => ({{ items: [] }}),
    }});
  }}
  if (url === '/api/arena/context/palace') {{
    return Promise.resolve({{
      ok: true,
      json: async () => ({{ concepts: [] }}),
    }});
  }}
  if (url === '/api/health') {{
    return Promise.resolve({{
      ok: true,
      json: async () => ({{ router_status: 'ONLINE', openrouter_key_present: true }}),
    }});
  }}
  if (url === '/api/openrouter/credits') {{
    return Promise.resolve({{
      ok: true,
      json: async () => ({{ balance: 12.50, active_keys: 2 }}),
    }});
  }}
  return Promise.resolve({{
    ok: true,
    json: async () => ({{ ok: true }}),
  }});
}}

{mock_handler_js}

const documentObj = {{
  getElementById: (id) => elements[id] || null,
  createElement: (tag) => makeElem('dyn-' + tag + '-' + Math.random().toString(36).slice(2, 6), [], ''),
  querySelectorAll: () => [],
}};

const sandbox = {{
  console,
  Math,
  Date,
  JSON,
  Promise,
  Array,
  Object,
  String,
  Number,
  Boolean,
  RegExp,
  Error,
  encodeURIComponent,
  decodeURIComponent,
  setTimeout: (fn) => 1,
  clearTimeout: () => {{}},
  setInterval: () => 1,
  clearInterval: () => {{}},
  document: documentObj,
  localStorage: {{
    getItem: (k) => (Object.prototype.hasOwnProperty.call(localStore, k) ? localStore[k] : null),
    setItem: (k, v) => {{ localStore[k] = String(v); }},
    removeItem: (k) => {{ delete localStore[k]; }},
  }},
  fetch: defaultMockFetch,
  prompt: (msg, def) => {{ promptCalls.push({{ msg, def }}); return null; }},
  alert: (msg) => {{ alertCalls.push(String(msg)); }},
  confirm: (msg) => {{ confirmCalls.push(String(msg)); return true; }},
  arenaCtxRefresh: (...args) => {{ arenaRefreshCalls.push(args); }},
  marked: {{ parse: (s) => String(s || '') }},
}};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
sandbox.self = sandbox;

const ctx = vm.createContext(sandbox);
vm.runInContext(COPILOT_JS, ctx);

(async () => {{
  const testApi = {{
    win: sandbox,
    elements,
    el: (id) => elements[id] || null,
    fetchCalls,
    promptCalls,
    alertCalls,
    confirmCalls,
    arenaRefreshCalls,
    flush: () => new Promise(r => setImmediate(r)),
  }};
  const fn = vm.runInContext(`(async function(ctxHarness) {{
    const {{ win, elements, el, fetchCalls, promptCalls, alertCalls, confirmCalls, arenaRefreshCalls, flush }} = ctxHarness;
    {test_body}
  }})`, ctx);
  const out = await fn(testApi);
  process.stdout.write(JSON.stringify(out === undefined ? {{ ok: true }} : out));
}})().catch((err) => {{
  console.error(err && err.stack ? err.stack : String(err));
  process.exit(1);
}});
"""
    proc = subprocess.run(
        ["node", "-"],
        input=node_script,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"Node test failed:\nSTDERR:\n{proc.stderr}\nSTDOUT:\n{proc.stdout}"
    return json.loads(proc.stdout or "{}")


def test_plan_b_html_css_scoping_and_required_dom_ids():
    html = render_copilot_window_html()
    required_ids = [
        "copilotAttachPalaceBtn",
        "copilotInventorySearch",
        "copilotPalaceNewBtn",
        "copilotInventoryTabs",
        "copilotInvTab-all",
        "copilotInvTab-palace",
        "copilotInvTab-space",
        "copilotInvTab-drive",
        "copilotInventorySummary",
        "copilotPalaceToArenaBtn",
        "copilotInventoryList",
        "copilotContextInspector",
        "copilotInspectorTitle",
        "copilotInspectorCloseBtn",
        "copilotInspectorSaveBtn",
        "copilotInspectorRevertBtn",
        "copilotInspectorDeleteBtn",
        "copilotInspectorName",
        "copilotInspectorCategory",
        "copilotInspectorDesc",
        "copilotInspectorMeta",
        "copilotInspectorValue",
        "copilotInspectorToRouterBtn",
        "copilotInspectorToArenaBtn",
        "copilotInspectorStatus",
        "copilotActiveCapsules",
    ]
    for req_id in required_ids:
        assert f'id="{req_id}"' in html, f"Missing required ID {req_id} in render_copilot_window_html()"

    # #copilotContextInspector starts hidden
    insp_match = re.search(r'<[a-zA-Z0-9_-]+[^>]+id="copilotContextInspector"[^>]*>', html)
    assert insp_match is not None
    assert "hidden" in insp_match.group(0)

    # #copilotActiveCapsules sits directly inside composer before #copilotPromptInput
    composer_pos = html.index("cp-composer")
    capsules_pos = html.index('id="copilotActiveCapsules"')
    prompt_pos = html.index('id="copilotPromptInput"')
    assert composer_pos < capsules_pos < prompt_pos

    # CSS scoping contract: every selector rule inside COPILOT_CSS must include #win-copilot
    for raw_line in COPILOT_CSS.splitlines():
        line = raw_line.strip()
        if line.endswith("{") and not line.startswith("@"):
            assert "#win-copilot" in line, f"Unscoped CSS rule in COPILOT_CSS: {line}"

    # No interactive window.prompt() calls left in COPILOT_SCRIPT
    assert "window.prompt(" not in COPILOT_SCRIPT
    assert "prompt(" not in COPILOT_SCRIPT

    # apply_copilot_ui cleanly renders full Plan B markup inside a host shell
    shell = "<html><head><style></style></head><body><!-- COPILOT_WINDOW --></body></html>"
    merged = apply_copilot_ui(shell.replace("<!-- COPILOT_WINDOW -->", html))
    assert "copilotContextInspector" in merged
    assert "copilotActiveCapsules" in merged
    assert "copilotInventoryTabs" in merged
    assert ".cp-capsule-chip" in merged


def test_figcraft_design_synced_with_floating_vote_modal():
    repo_root = Path(__file__).resolve().parents[1]
    fig_path = repo_root / "assets" / "designs" / "context_palace_router_arena.figcraft"
    png_path = repo_root / "assets" / "designs" / "context_palace_router_arena.png"
    assert fig_path.is_file()
    assert png_path.is_file()
    assert png_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"

    with zipfile.ZipFile(fig_path, "r") as zf:
        assert "document.json" in zf.namelist()
        doc = json.loads(zf.read("document.json").decode("utf-8"))
    root = doc.get("root", doc)
    serialized = json.dumps(root)
    assert "Floating Bottom-Right Vote Modal" in serialized
    assert "Vote Brain A (+150 XP)" in serialized
    assert "Vote Brain B (+150 XP)" in serialized
    assert "Run Complete" in serialized


def test_context_inspector_crud_lifecycle_and_programmatic_fallback():
    mock_handler = """
    let nextSeq = 100;
    const palaceDb = {
      'node-seed-1': {
        node_id: 'node-seed-1',
        canonical_name: 'Delta KV Cache Spec',
        category: 'architecture',
        summary: 'Edge delta paging hierarchy',
        description: 'Three-tier L1/L2/L3 KV state eviction protocol',
        value: 'Keep hot tokens pinned in SRAM while compressing cold blocks.',
        valid_from: '2026-11-10T09:00:00Z',
        edges: [
          { relation_type: 'relates_to', target_name: 'Speculative Edge Router' },
          { relation_type: 'verified_by', target_name: 'Bench Suite 04' },
        ],
      },
    };
    function customMockFetch(url, opts, body) {
      if (url === '/api/arena/context/inventory' || url.startsWith('/api/arena/context/inventory?')) {
        const items = Object.values(palaceDb).map((n) => ({
          id: n.node_id,
          node_id: n.node_id,
          source_group: 'palace',
          kind: 'palace',
          title: n.canonical_name,
          canonical_name: n.canonical_name,
          category: n.category,
          summary: n.summary,
          description: n.description,
          value: n.value,
          valid_from: n.valid_from,
          edges: n.edges,
          path: '/palace/' + n.canonical_name,
          tokens_est: Math.max(12, Math.ceil((n.value || '').length / 4)),
        }));
        return Promise.resolve({ ok: true, json: async () => ({ items }) });
      }
      if (url.startsWith('/api/arena/context/palace?') || url === '/api/arena/context/palace') {
        return Promise.resolve({ ok: true, json: async () => ({ concepts: Object.values(palaceDb) }) });
      }
      if (url === '/api/arena/context/palace/crud') {
        const action = body.action;
        if (action === 'create') {
          const id = 'node-new-' + (++nextSeq);
          const created = {
            node_id: id,
            canonical_name: body.canonical_name,
            category: body.category || 'concept',
            summary: body.summary || body.description || '',
            description: body.description || '',
            value: body.value || '',
            valid_from: '2026-11-15T21:30:00Z',
            edges: [{ relation_type: 'authored_in', target_name: 'TinCan Copilot' }],
          };
          palaceDb[id] = created;
          return Promise.resolve({ ok: true, json: async () => ({ ok: true, concept: created }) });
        }
        if (action === 'read') {
          const concept = palaceDb[body.node_id];
          return Promise.resolve({ ok: !!concept, json: async () => (concept ? { ok: true, concept } : { error: 'not found' }) });
        }
        if (action === 'update') {
          const concept = palaceDb[body.node_id];
          Object.assign(concept, {
            canonical_name: body.canonical_name ?? concept.canonical_name,
            category: body.category ?? concept.category,
            summary: body.summary ?? concept.summary,
            description: body.description ?? concept.description,
            value: body.value ?? concept.value,
          });
          return Promise.resolve({ ok: true, json: async () => ({ ok: true, concept }) });
        }
        if (action === 'delete') {
          const deleted = palaceDb[body.node_id];
          delete palaceDb[body.node_id];
          return Promise.resolve({ ok: true, json: async () => ({ ok: true, deleted: deleted ? deleted.node_id : null }) });
        }
      }
      if (url === '/api/arena/context/palace/import') {
        return Promise.resolve({ ok: true, json: async () => ({ ok: true, imported: body.node_ids || [] }) });
      }
      return undefined;
    }
    """

    test_body = """
    win.TinCanCopilot.init();
    await win.TinCanCopilot.refresh();
    await flush();

    // 1. Clicking/calling promptCreatePalaceConcept() opens inline inspector without window.prompt()
    win.TinCanCopilot.promptCreatePalaceConcept();
    if (promptCalls.length !== 0) throw new Error('Expected zero window.prompt calls');
    const inspEl = el('copilotContextInspector');
    if (inspEl.classList.contains('hidden')) throw new Error('Inspector should open on promptCreatePalaceConcept()');
    if (win.TinCanCopilot.getState().inspector.mode !== 'create') {
      throw new Error('Expected create mode, got ' + win.TinCanCopilot.getState().inspector.mode);
    }

    // 2. Create ConceptNode inline via inspector inputs + savePalaceInspector()
    el('copilotInspectorName').value = 'Neural Mesh Spec';
    el('copilotInspectorCategory').value = 'architecture';
    el('copilotInspectorDesc').value = 'Distributed sync protocol';
    el('copilotInspectorValue').value = 'CRDT delta state over WebRTC';
    await win.TinCanCopilot.savePalaceInspector();
    await flush();

    const createCall = fetchCalls.find(c => c.url === '/api/arena/context/palace/crud' && c.body && c.body.action === 'create');
    if (!createCall) throw new Error('Expected POST /api/arena/context/palace/crud create call');
    if (createCall.body.canonical_name !== 'Neural Mesh Spec') throw new Error('Wrong canonical_name');
    if (createCall.body.category !== 'architecture') throw new Error('Wrong category');
    if (createCall.body.description !== 'Distributed sync protocol') throw new Error('Wrong description');

    const afterCreateState = win.TinCanCopilot.getState();
    if (afterCreateState.inspector.mode !== 'edit') throw new Error('Expected edit mode after save');
    const createdId = afterCreateState.inspector.nodeId;
    if (!createdId) throw new Error('Expected created nodeId');
    if (!el('copilotInspectorMeta').textContent.includes('valid_from: 2026-11-15T21:30:00Z')) {
      throw new Error('Expected valid_from metadata in #copilotInspectorMeta: ' + el('copilotInspectorMeta').textContent);
    }
    if (!el('copilotInspectorMeta').textContent.includes('authored_in')) {
      throw new Error('Expected edges metadata in #copilotInspectorMeta: ' + el('copilotInspectorMeta').textContent);
    }

    // 3. Read / Inspect existing node via readPalaceConcept()
    await win.TinCanCopilot.readPalaceConcept('node-seed-1');
    const readCall = fetchCalls.find(c => c.url === '/api/arena/context/palace/crud' && c.body && c.body.action === 'read' && c.body.node_id === 'node-seed-1');
    if (!readCall) throw new Error('Expected POST /api/arena/context/palace/crud read call');
    if (el('copilotInspectorName').value !== 'Delta KV Cache Spec') throw new Error('Expected hydrated seed name');
    if (!el('copilotInspectorMeta').textContent.includes('Speculative Edge Router')) {
      throw new Error('Expected edge target in #copilotInspectorMeta');
    }

    // Switch back to created node for revert + update + router/arena + delete
    await win.TinCanCopilot.readPalaceConcept(createdId);

    // 4. Revert restores snapshot
    el('copilotInspectorName').value = 'Temp Unsaved Name';
    el('copilotInspectorValue').value = 'Temp Unsaved Body';
    win.TinCanCopilot.revertPalaceInspector();
    if (el('copilotInspectorName').value !== 'Neural Mesh Spec') throw new Error('Revert failed on name');
    if (el('copilotInspectorValue').value !== 'CRDT delta state over WebRTC') throw new Error('Revert failed on value');

    // 5. Attach to Router idempotently & update via inspector -> capsule chip updates
    win.TinCanCopilot.sendInspectorToRouter();
    win.TinCanCopilot.sendInspectorToRouter();
    const matchedAttached = win.TinCanCopilot.getState().attachedFiles.filter(f => f.nodeId === createdId);
    if (matchedAttached.length !== 1) throw new Error('sendInspectorToRouter should be idempotent, got ' + matchedAttached.length);

    el('copilotInspectorDesc').value = 'Updated sync protocol v2';
    el('copilotInspectorValue').value = 'CRDT delta state over WebRTC with deterministic Merkle checkpoints for zero-drift verification.';
    await win.TinCanCopilot.savePalaceInspector();
    await flush();
    const updateCall = fetchCalls.find(c => c.url === '/api/arena/context/palace/crud' && c.body && c.body.action === 'update' && c.body.node_id === createdId);
    if (!updateCall) throw new Error('Expected POST /api/arena/context/palace/crud update call');
    const updatedAttached = win.TinCanCopilot.getState().attachedFiles.find(f => f.nodeId === createdId);
    if (!updatedAttached || !updatedAttached.palaceContent.includes('Merkle checkpoints')) {
      throw new Error('Attached capsule did not sync updated content: ' + JSON.stringify(updatedAttached));
    }
    if (!el('copilotActiveCapsules').innerHTML.includes('Palace: Neural Mesh Spec')) {
      throw new Error('Active capsule chip missing updated Palace label: ' + el('copilotActiveCapsules').innerHTML);
    }

    // 6. Send to Arena Both
    await win.TinCanCopilot.sendInspectorToArenaBoth();
    const importCall = fetchCalls.find(c => c.url === '/api/arena/context/palace/import');
    if (!importCall || importCall.body.agent_id !== 'both' || importCall.body.node_ids[0] !== createdId) {
      throw new Error('Invalid /api/arena/context/palace/import payload: ' + JSON.stringify(importCall));
    }
    if (arenaRefreshCalls.map(a => a[1]).join(',') !== 'A,B') {
      throw new Error('Expected arenaCtxRefresh A,B calls, got ' + JSON.stringify(arenaRefreshCalls));
    }

    // 7. Delete concept removes from Palace, inventory, and active capsules
    await win.TinCanCopilot.deletePalaceInspector();
    await flush();
    const deleteCall = fetchCalls.find(c => c.url === '/api/arena/context/palace/crud' && c.body && c.body.action === 'delete' && c.body.node_id === createdId);
    if (!deleteCall) throw new Error('Expected POST /api/arena/context/palace/crud delete call');
    if (!el('copilotContextInspector').classList.contains('hidden')) throw new Error('Inspector should hide after delete');
    if (win.TinCanCopilot.getState().attachedFiles.some(f => f.nodeId === createdId)) {
      throw new Error('Deleted Palace node must be detached from active capsules');
    }

    // 8. Programmatic promptCreatePalaceConcept(title, value) fallback creates + attaches without window.prompt()
    await win.TinCanCopilot.promptCreatePalaceConcept('Programmatic Anchor', 'Signed fallback snippet');
    if (promptCalls.length !== 0) throw new Error('Programmatic fallback must still never invoke window.prompt');
    const progCreated = win.TinCanCopilot.getState().attachedFiles.find(f => f.path === '/palace/Programmatic Anchor');
    if (!progCreated) throw new Error('Programmatic fallback should attach newly created Palace concept');

    return {
      ok: true,
      promptCallCount: promptCalls.length,
      createdId,
      crudActions: fetchCalls.filter(c => c.url === '/api/arena/context/palace/crud').map(c => c.body.action),
      arenaRefreshAgents: arenaRefreshCalls.map(a => a[1]),
    };
    """

    result = _run_copilot_node(test_body, mock_handler_js=mock_handler)
    assert result["ok"] is True
    assert result["promptCallCount"] == 0
    assert result["crudActions"] == ["create", "read", "read", "update", "delete", "create"]
    assert result["arenaRefreshAgents"] == ["A", "B"]


def test_inventory_filter_tabs_search_edit_button_and_offline_fallback():
    online_mock_handler = """
    function customMockFetch(url) {
      if (url === '/api/arena/context/inventory' || url.startsWith('/api/arena/context/inventory?')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            items: [
              {
                id: 'pal-1',
                node_id: 'pal-1',
                source_group: 'palace',
                kind: 'palace',
                title: 'Merkle Sync Spine',
                category: 'protocol',
                description: 'Content-addressed node graph',
                value: 'SHA-256 DAG state sync',
                valid_from: '2026-11-11T12:00:00Z',
                edges: [{ relation_type: 'feeds', target_name: 'Arena Context' }],
                path: '/palace/Merkle Sync Spine',
                tokens_est: 42,
              },
              {
                id: 'pal-2',
                node_id: 'pal-2',
                source_group: 'palace',
                kind: 'palace',
                title: 'Voice Resilience Policy',
                category: 'guardrail',
                description: 'WER threshold config',
                value: 'Threshold 0.12',
                path: '/palace/Voice Resilience Policy',
                tokens_est: 18,
              },
              {
                id: 'sp-1',
                source_group: 'space',
                kind: 'space',
                title: 'kernel_merkle.py',
                path: 'core/kernel_merkle.py',
                tokens_est: 640,
              },
              {
                id: 'sp-2',
                source_group: 'space',
                kind: 'space',
                title: 'router.rs',
                path: 'edge/router.rs',
                tokens_est: 510,
              },
              {
                id: 'drv-1',
                source_group: 'drive',
                kind: 'drive',
                title: 'Benchmarks Q4.md',
                path: 'drive://Vault/Benchmarks Q4.md',
                tokens_est: 300,
              },
            ],
          }),
        });
      }
      if (url.startsWith('/api/arena/context/palace')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            concepts: [
              {
                node_id: 'pal-1',
                canonical_name: 'Merkle Sync Spine',
                category: 'protocol',
                summary: 'Content-addressed node graph',
                value: 'SHA-256 DAG state sync',
                valid_from: '2026-11-11T12:00:00Z',
                edges: [{ relation_type: 'feeds', target_name: 'Arena Context' }],
              },
              {
                node_id: 'pal-2',
                canonical_name: 'Voice Resilience Policy',
                category: 'guardrail',
                summary: 'WER threshold config',
                value: 'Threshold 0.12',
              },
            ],
          }),
        });
      }
      return undefined;
    }
    """

    online_test_body = """
    win.TinCanCopilot.init();
    win.TinCanCopilot.toggleAttachDrawer('all');
    await win.TinCanCopilot.refresh();
    await flush();

    const allTab = el('copilotInvTab-all').textContent;
    const palaceTab = el('copilotInvTab-palace').textContent;
    const spaceTab = el('copilotInvTab-space').textContent;
    const driveTab = el('copilotInvTab-drive').textContent;
    if (!allTab.includes('5') || !palaceTab.includes('2') || !spaceTab.includes('2') || !driveTab.includes('1')) {
      throw new Error('Unexpected tab counts: ' + JSON.stringify({ allTab, palaceTab, spaceTab, driveTab }));
    }

    // Switch to Palace tab and verify Edit button opens inline inspector
    win.TinCanCopilot.setInventoryTab('palace');
    const palaceRendered = win.TinCanCopilot.getState().renderedInventory;
    if (palaceRendered.length !== 2 || palaceRendered.some(i => i.source !== 'palace')) {
      throw new Error('Palace filter failed');
    }
    const listHtml = el('copilotInventoryList').innerHTML;
    if (!listHtml.includes('_invEdit(0)') || !listHtml.includes('Edit')) {
      throw new Error('Expected Edit button in Palace inventory rows: ' + listHtml);
    }
    win.TinCanCopilot._invEdit(0);
    if (el('copilotContextInspector').classList.contains('hidden')) {
      throw new Error('Clicking Edit should reveal #copilotContextInspector');
    }
    if (el('copilotInspectorName').value !== 'Merkle Sync Spine') {
      throw new Error('Inspector did not load clicked Palace row: ' + el('copilotInspectorName').value);
    }

    // Verify .space & drive tabs
    win.TinCanCopilot.setInventoryTab('space');
    if (win.TinCanCopilot.getState().renderedInventory.length !== 2) throw new Error('Space tab count mismatch');
    win.TinCanCopilot.setInventoryTab('drive');
    if (win.TinCanCopilot.getState().renderedInventory.length !== 1) throw new Error('Drive tab count mismatch');

    // Search query across All tab ('merkle' matches 1 palace + 1 space)
    win.TinCanCopilot.setInventoryTab('all');
    win.TinCanCopilot.setInventoryQuery('merkle');
    const searchMatches = win.TinCanCopilot.getState().renderedInventory;
    if (searchMatches.length !== 2) {
      throw new Error('Expected 2 search matches for merkle, got ' + searchMatches.length);
    }

    return {
      ok: true,
      tabLabels: { allTab, palaceTab, spaceTab, driveTab },
      searchMatches: searchMatches.map(i => i.title),
    };
    """

    online_res = _run_copilot_node(online_test_body, mock_handler_js=online_mock_handler)
    assert online_res["ok"] is True
    assert online_res["searchMatches"] == ["Merkle Sync Spine", "kernel_merkle.py"]

    # Offline fallback when /api/arena/context/inventory fails -> merges palaceNodes, spaceFiles, driveFiles
    offline_mock_handler = """
    function customMockFetch(url) {
      if (url.startsWith('/api/arena/context/inventory')) {
        return Promise.reject(new Error('inventory endpoint offline'));
      }
      if (url.startsWith('/api/space/ls')) {
        return Promise.resolve({ ok: true, json: async () => ({ files: [{ path: '/offline_router.py', size_bytes: 1200 }] }) });
      }
      if (url.startsWith('/api/drive/ls')) {
        return Promise.resolve({ ok: true, json: async () => ({ files: ['/Vault/OfflineNotes.md'] }) });
      }
      if (url.startsWith('/api/arena/context/palace')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            concepts: [
              { node_id: 'pal-off-1', canonical_name: 'Offline Spine', category: 'spec', summary: 'Cached concept', value: 'Local palace rule' },
            ],
          }),
        });
      }
      return undefined;
    }
    """
    offline_test_body = """
    win.TinCanCopilot.init();
    win.TinCanCopilot.toggleAttachDrawer('all');
    await win.TinCanCopilot.refresh();
    await flush();

    const stOffline = win.TinCanCopilot.getState();
    if (stOffline.inventoryFetched !== false) throw new Error('Expected inventoryFetched=false on offline failure');
    const offlineRendered = stOffline.renderedInventory;
    if (offlineRendered.length !== 3) {
      throw new Error('Expected 3 fallback items (1 palace + 1 space + 1 drive), got ' + offlineRendered.length);
    }
    win.TinCanCopilot.setInventoryTab('palace');
    if (win.TinCanCopilot.getState().renderedInventory.length !== 1) throw new Error('Offline palace filter failed');
    win.TinCanCopilot.setInventoryTab('space');
    if (win.TinCanCopilot.getState().renderedInventory.length !== 1) throw new Error('Offline space filter failed');
    win.TinCanCopilot.setInventoryTab('drive');
    if (win.TinCanCopilot.getState().renderedInventory.length !== 1) throw new Error('Offline drive filter failed');

    return { ok: true, offlineCount: offlineRendered.length };
    """
    offline_res = _run_copilot_node(offline_test_body, mock_handler_js=offline_mock_handler)
    assert offline_res["ok"] is True
    assert offline_res["offlineCount"] == 3


def test_active_capsules_chips_removal_and_chat_prompt_injection():
    mock_handler = """
    function customMockFetch(url, opts, body) {
      if (url.startsWith('/api/arena/context/palace')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            concepts: [
              {
                node_id: 'pal-capsule-1',
                canonical_name: 'Edge Routing Spec',
                category: 'spec',
                summary: 'Low-latency hop table',
                value: 'Pin critical edge agents to local relay when RTT > 80ms.',
              },
            ],
          }),
        });
      }
      if (url === '/api/arena/context/inventory' || url.startsWith('/api/arena/context/inventory?')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            items: [
              {
                id: 'pal-capsule-1',
                node_id: 'pal-capsule-1',
                source_group: 'palace',
                kind: 'palace',
                title: 'Edge Routing Spec',
                category: 'spec',
                description: 'Low-latency hop table',
                value: 'Pin critical edge agents to local relay when RTT > 80ms.',
                path: '/palace/Edge Routing Spec',
                tokens_est: 64,
              },
            ],
          }),
        });
      }
      if (url === '/api/chat') {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            response: 'Routing plan synthesized.',
            model_used: body.model,
            cost_usd: 0.001,
          }),
        });
      }
      return undefined;
    }
    """

    test_body = """
    win.TinCanCopilot.init();
    await win.TinCanCopilot.refresh();
    await flush();

    const capsulesEl = el('copilotActiveCapsules');
    if (!capsulesEl.innerHTML.includes('4,080t')) {
      throw new Error('Expected initial 4,080t total in #copilotActiveCapsules: ' + capsulesEl.innerHTML);
    }

    // Open drawer and attach Palace item from inventory
    win.TinCanCopilot.setInventoryTab('all');
    win.TinCanCopilot._invAttach(0);
    if (win.TinCanCopilot.getState().attachedFiles.length !== 4) {
      throw new Error('Expected 4 attached files after Palace attach, got ' + win.TinCanCopilot.getState().attachedFiles.length);
    }
    if (!capsulesEl.innerHTML.includes('Palace: Edge Routing Spec (64t)')) {
      throw new Error('Expected Palace chip in #copilotActiveCapsules: ' + capsulesEl.innerHTML);
    }
    if (!capsulesEl.innerHTML.includes('4,144t')) {
      throw new Error('Expected updated total 4,144t in #copilotActiveCapsules: ' + capsulesEl.innerHTML);
    }

    // Remove newly attached Palace chip, verify revert to 4,080t, then re-attach for chat injection check
    win.TinCanCopilot.removeContextFile(3);
    if (win.TinCanCopilot.getState().attachedFiles.length !== 3) throw new Error('Expected 3 attached files after removal');
    if (!capsulesEl.innerHTML.includes('4,080t') || capsulesEl.innerHTML.includes('Edge Routing Spec')) {
      throw new Error('Chip did not clear on removeContextFile: ' + capsulesEl.innerHTML);
    }

    // Re-attach Palace capsule alongside the 3 initial files (tests >3 snippet inclusion!) and send message
    win.TinCanCopilot._invAttach(0);
    el('copilotPromptInput').value = 'Propose edge fallback order';
    await win.TinCanCopilot.sendMessage();
    await flush();

    const chatCall = fetchCalls.find(c => c.url === '/api/chat');
    if (!chatCall) throw new Error('Expected POST /api/chat');
    const sentPrompt = chatCall.body.prompt || '';
    if (!sentPrompt.includes('Edge Routing Spec') || !sentPrompt.includes('Pin critical edge agents to local relay')) {
      throw new Error('Attached Palace capsule missing from /api/chat prompt: ' + sentPrompt);
    }

    return {
      ok: true,
      attachedCount: win.TinCanCopilot.getState().attachedFiles.length,
      promptLength: sentPrompt.length,
    };
    """

    result = _run_copilot_node(test_body, mock_handler_js=mock_handler)
    assert result["ok"] is True
    assert result["attachedCount"] == 4
