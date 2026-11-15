"""Offline/in-process test suite covering the 9 TinCan Mesh OS UX/UI/backend updates."""

from __future__ import annotations

import http.client
import json
import re
import shutil
import sqlite3
import subprocess
import threading
from contextlib import contextmanager
from http.server import ThreadingHTTPServer
from typing import Any, Dict, Iterator, Tuple

import pytest

import server
from iot_federated_agent_memory.account_registry import PeerAccountRegistry
from iot_federated_agent_memory.agent_space import AgentSpaceManager
from iot_federated_agent_memory.ai_home_shell import WORKFLOW_CARDS, render_ai_home_hub_html
from iot_federated_agent_memory.arena_context import (
    ArenaContextRegistry,
    ContextStoreError,
    DriveMirrorSource,
)
from iot_federated_agent_memory.arena_duel_ui import ARENA_DUEL_SCRIPT, render_arena_duel
from iot_federated_agent_memory.copilot_ui import COPILOT_SCRIPT, render_copilot_window_html
from iot_federated_agent_memory.cyberspace_board import CyberspaceBoardEngine
from iot_federated_agent_memory.mesh_os_engine import TinCanMeshOSEngine
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI
from iot_federated_agent_memory.shell_component import SHELL_JS
from iot_federated_agent_memory.tincan_brew import (
    HARNESS_CATALOG,
    discover_harnesses,
    handle_harness_command,
)
from iot_federated_agent_memory.workstation_ui import render_workstation_window_html
from iot_federated_agent_memory.zen_shell import ZEN_BODY, ZEN_HEAD


# ---------------------------------------------------------------------------
# Shared test helpers
# ---------------------------------------------------------------------------

def _extract_window(html_text: str, win_id: str) -> str:
    """Return markup slice for one top-level `.mesh-window` container."""
    marker = f'<div id="{win_id}" class="mesh-window'
    start = html_text.index(marker)
    nxt = html_text.find('<div id="win-', start + len(marker))
    if nxt == -1:
        nxt = html_text.find('<footer id="meshOsDock"', start + len(marker))
    return html_text[start : nxt if nxt != -1 else len(html_text)]


def _extract_dock(html_text: str) -> str:
    """Return markup slice for `<footer id="meshOsDock">...</footer>`."""
    start = html_text.index('<footer id="meshOsDock"')
    end = html_text.index("</footer>", start) + len("</footer>")
    return html_text[start:end]


def _run_node(js_code: str) -> Dict[str, Any]:
    """Execute inline JS in Node.js and parse JSON stdout."""
    node_bin = shutil.which("node")
    assert node_bin, "Node.js binary is required for DOM/JS checks"
    proc = subprocess.run([node_bin, "-e", js_code], capture_output=True, text=True)
    assert proc.returncode == 0, f"Node check failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    return json.loads(proc.stdout)


def _extract_js_range(source: str, start_anchor: str, end_anchor: str) -> str:
    """Slice JS source between two deterministic anchor comments or declarations."""
    i0 = source.index(start_anchor)
    i1 = source.index(end_anchor, i0 + len(start_anchor))
    return source[i0:i1]


@contextmanager
def _live_server() -> Iterator[Tuple[str, int]]:
    """Run an isolated ThreadingHTTPServer and tear down sockets cleanly."""
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.MeshGatewayHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield httpd.server_address
    finally:
        httpd.shutdown()
        httpd.server_close()


def _http_json(
    addr: Tuple[str, int],
    method: str,
    path: str,
    body: Dict[str, Any] | None = None,
    token: str | None = None,
) -> Tuple[int, Dict[str, Any]]:
    """Issue a single HTTP JSON request against a local ThreadingHTTPServer."""
    conn = http.client.HTTPConnection(*addr, timeout=15)
    try:
        headers: Dict[str, str] = {}
        payload = None
        if body is not None:
            payload = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if token:
            headers["Authorization"] = f"Bearer {token}"
        conn.request(method, path, body=payload, headers=headers)
        resp = conn.getresponse()
        raw = resp.read().decode("utf-8", errors="replace")
        return resp.status, (json.loads(raw) if raw else {})
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 1. Command-K & #meshOsDock cleanup + /3dstudio & Watch Ad +CR
# ---------------------------------------------------------------------------

def test_command_k_and_dock_remove_legacy_simulators_and_add_3dstudio_watch_ad():
    dock_html = _extract_dock(MESH_OS_HTML_UI)
    zen_full = ZEN_HEAD + "\n" + ZEN_BODY

    for forbidden in ("/designs", "/ios", "/car", "Design Mockups", "iOS App Simulator", "Car Head-Unit"):
        assert forbidden not in zen_full
        assert forbidden not in dock_html
        assert forbidden not in MESH_OS_HTML_UI

    # /3dstudio and Watch Ad +CR must exist in Zen quickbar/routes/TOOLS/SLASH and dock
    assert "'/3dstudio'" in ZEN_HEAD
    assert 'id="zenWatchAdQuickBtn"' in ZEN_BODY
    assert 'data-action="watch-ad"' in ZEN_BODY
    assert "Watch Ad +CR" in ZEN_BODY
    assert "window.zenWatchHomeAd" in ZEN_BODY
    assert 'id="dockBtn-win-workstation"' in dock_html
    assert "3D Studio" in dock_html
    assert "window.location.pathname === '/3dstudio'" in MESH_OS_HTML_UI

    tools_src = _extract_js_range(ZEN_BODY, "const TOOLS = [", "];") + "];"
    slash_src = _extract_js_range(ZEN_BODY, "const SLASH = [", "];") + "];"
    help_src = _extract_js_range(ZEN_BODY, "const HELP_TEXT =", ";\n") + ";"
    out = _run_node(
        f"""
        {tools_src}
        {slash_src}
        {help_src}
        console.log(JSON.stringify({{
          toolIds: TOOLS.map(t => t.id),
          toolNames: TOOLS.map(t => t.name),
          slashCmds: SLASH.map(s => s.cmd),
          studioSlash: SLASH.find(s => s.cmd === '/3dstudio'),
          helpText: HELP_TEXT,
        }}));
        """
    )
    assert "win-workstation" in out["toolIds"]
    assert "3D Studio" in out["toolNames"]
    assert "Workstation" in out["toolNames"]
    assert "/3dstudio" in out["slashCmds"]
    assert out["studioSlash"]["tool"] == "win-workstation"
    assert "/3dstudio" in out["helpText"]


# ---------------------------------------------------------------------------
# 2. #win-comms Discord-style channels sidebar + People in Room DM roster
# ---------------------------------------------------------------------------

def test_win_comms_channels_sidebar_and_people_roster_markup():
    comms = _extract_window(MESH_OS_HTML_UI, "win-comms")
    for token in (
        'id="chatChannelsList"',
        'data-channel="main"',
        'data-channel="architecture"',
        'data-channel="cyberspace"',
        'data-channel="arena"',
        'onclick="promptNewChatChannel()"',
        "People in Room",
        'id="chatPeopleList"',
        'onclick="refreshCommsPeopleRoster()"',
        'id="chatActiveTargetBanner"',
        'id="chatChannelSelect"',
        'id="chatDirectPeerInput"',
        'id="chatMessagesList"',
        'id="chatInput"',
        'onclick="sendChatMessage()"',
    ):
        assert token in comms


def test_win_comms_channels_and_dm_roster_js_behavior():
    comms_js = _extract_js_range(
        MESH_OS_HTML_UI,
        "let chatMsgCount = 0;",
        "setTimeout(() => { refreshCommsPeopleRoster(); }",
    )
    out = _run_node(
        f"""
        function makeEl(id, extra) {{
          const classes = new Set();
          return Object.assign({{
            id,
            value: '',
            innerText: '',
            innerHTML: '',
            placeholder: '',
            scrollTop: 0,
            scrollHeight: 0,
            children: [],
            appendChild(node) {{ this.children.push(node); }},
            classList: {{
              add(c) {{ classes.add(c); }},
              remove(c) {{ classes.delete(c); }},
              toggle(c, force) {{
                if (force === undefined) {{
                  if (classes.has(c)) classes.delete(c); else classes.add(c);
                }} else if (force) classes.add(c); else classes.delete(c);
              }},
              contains(c) {{ return classes.has(c); }},
            }},
          }}, extra || {{}});
        }}
        const elems = {{
          chatChannelsList: makeEl('chatChannelsList'),
          chatPeopleList: makeEl('chatPeopleList'),
          chatActiveTargetBanner: makeEl('chatActiveTargetBanner'),
          chatChannelSelect: makeEl('chatChannelSelect', {{ value: 'room' }}),
          chatDirectPeerInput: makeEl('chatDirectPeerInput'),
          chatMessagesList: makeEl('chatMessagesList'),
          chatCounterBadge: makeEl('chatCounterBadge'),
          chatInput: makeEl('chatInput'),
          roomInput: makeEl('roomInput', {{ value: 'main' }}),
        }};
        elems.chatDirectPeerInput.classList.add('hidden');
        const document = {{
          getElementById(id) {{ return elems[id] || null; }},
          createElement() {{ return makeEl('dyn'); }},
        }};
        const window = {{ prompt: () => 'Research Ops!' }};
        const myPeerId = 'peer-self';
        const currentRoom = 'main';
        const fetch = async (url) => {{
          if (url.startsWith('/api/mesh/state')) {{
            return {{ ok: true, json: async () => ({{ peers: {{ 'peer-self': {{ display_name: 'Self' }}, 'peer-alice': {{ display_name: 'Alice' }} }} }}) }};
          }}
          if (url === '/api/board/roster') {{
            return {{ ok: true, json: async () => ({{ users: [{{ peer_id: 'peer-bob', username: 'bob', verified: true, role: 'Operator' }}] }}) }};
          }}
          return {{ ok: false, json: async () => ({{}}) }};
        }};
        {comms_js}
        (async () => {{
          await refreshCommsPeopleRoster();
          const peopleHtml = elems.chatPeopleList.innerHTML;
          promptNewChatChannel();
          const channelsAfterCreate = elems.chatChannelsList.innerHTML;
          const channelBanner = elems.chatActiveTargetBanner.innerText;
          selectChatTarget('direct', 'peer-bob', '@bob');
          const dmBanner = elems.chatActiveTargetBanner.innerText;
          const dmSelect = elems.chatChannelSelect.value;
          const dmHidden = elems.chatDirectPeerInput.classList.contains('hidden');
          const dmPeerVal = elems.chatDirectPeerInput.value;
          onChatModeSelectChange('room');
          const backToRoomBanner = elems.chatActiveTargetBanner.innerText;
          console.log(JSON.stringify({{
            peopleHtml,
            channelsAfterCreate,
            channelBanner,
            dmBanner,
            dmSelect,
            dmHidden,
            dmPeerVal,
            backToRoomBanner,
          }}));
        }})();
        """
    )
    assert "peer-alice" in out["peopleHtml"]
    assert "peer-bob" in out["peopleHtml"]
    assert "peer-self" not in out["peopleHtml"]
    assert 'data-channel="research-ops"' in out["channelsAfterCreate"]
    assert out["channelBanner"] == "#research-ops · Broadcast"
    assert out["dmBanner"] == "🔒 DM · @bob"
    assert out["dmSelect"] == "direct"
    assert out["dmHidden"] is False
    assert out["dmPeerVal"] == "peer-bob"
    assert out["backToRoomBanner"] == "#main · Broadcast"


# ---------------------------------------------------------------------------
# 3. Cyberspace Board omni-bar, AI suggestions, query parser, curation, feed
# ---------------------------------------------------------------------------

def test_cyberspace_board_omni_bar_and_feed_markup():
    board_win = _extract_window(MESH_OS_HTML_UI, "win-board")
    assert 'id="boardUnifiedBar"' in board_win
    assert 'id="boardSearchInput"' in board_win
    assert 'id="boardComposeRow"' not in board_win
    assert 'id="boardComposerDetails"' not in board_win
    assert 'id="boardAiSuggestionsBar"' in board_win
    assert 'id="boardAiSuggestionChips"' in board_win
    assert 'id="boardAiModelBadge"' in board_win
    assert '<option value="activity">Activity</option>' in board_win

    for token in (
        'id="boardTabBtn-feed"',
        'id="boardTab-feed"',
        'id="boardCuratedCountBadge"',
        'id="boardFeedFilter-all"',
        'id="boardFeedFilter-curated"',
        'id="boardFeedFilter-solved"',
        'id="boardFeedFilterInput"',
        'id="boardCuratedFeedList"',
        'id="boardActiveThreadsList"',
        "loadBoardFeedAndThreads",
        "curateCyberspaceTopic",
        "replyQuickThread",
        "submitBoardOmniInput",
        "loadBoardAiSuggestions",
    ):
        assert token in board_win or token in MESH_OS_HTML_UI

    # Node check for omni-bar slash routing in submitBoardOmniInput
    omni_fn = _extract_js_range(
        MESH_OS_HTML_UI,
        "async function submitBoardOmniInput()",
        "function focusBoardSearch()",
    )
    out = _run_node(
        f"""
        let calls = [];
        const boardChips = [];
        const elems = {{
          boardSearchInput: {{ value: '' }},
          boardFeedFilterInput: {{ value: '' }},
        }};
        const document = {{ getElementById: (id) => elems[id] || null }};
        function consumeBoardSortToken() {{ return false; }}
        function showQuickNotification(msg) {{ calls.push(['notify', msg]); }}
        async function createCyberspaceTopic(raw) {{ calls.push(['create', raw]); }}
        function switchBoardTab(tab) {{ calls.push(['tab', tab]); }}
        function loadBoardFeedAndThreads() {{ calls.push(['loadFeed', elems.boardFeedFilterInput.value]); }}
        async function curateCyberspaceTopic(id) {{ calls.push(['curate', id]); }}
        function setBoardFeedFilter(f) {{ calls.push(['filter', f]); }}
        function searchCyberspaceBoard() {{ calls.push(['search', elems.boardSearchInput.value]); }}
        {omni_fn}
        (async () => {{
          elems.boardSearchInput.value = '/post New Mesh Thread #graphrag';
          await submitBoardOmniInput();
          elems.boardSearchInput.value = '/thread Active Thread Title';
          await submitBoardOmniInput();
          elems.boardSearchInput.value = '/feed crdt';
          await submitBoardOmniInput();
          elems.boardSearchInput.value = '/curate topic-abc123';
          await submitBoardOmniInput();
          elems.boardSearchInput.value = '/curate';
          await submitBoardOmniInput();
          console.log(JSON.stringify({{ calls }}));
        }})();
        """
    )
    assert ["create", "/post New Mesh Thread #graphrag"] in out["calls"]
    assert ["create", "/thread Active Thread Title"] in out["calls"]
    assert ["tab", "feed"] in out["calls"]
    assert ["loadFeed", "crdt"] in out["calls"]
    assert ["curate", "topic-abc123"] in out["calls"]
    assert ["filter", "curated"] in out["calls"]


def test_parse_unified_query_new_commands_and_curated_filter():
    parse = CyberspaceBoardEngine.parse_unified_query
    assert parse("/post Launch CRDT Mesh #crdt @gemini-brain") == {
        "command": "post",
        "tags": ["crdt"],
        "mentions": ["gemini-brain"],
        "verified_only": False,
        "curated_only": False,
        "text": "Launch CRDT Mesh",
    }
    assert parse("/thread Discuss GraphRAG") == {
        "command": "thread",
        "tags": [],
        "mentions": [],
        "verified_only": False,
        "curated_only": False,
        "text": "Discuss GraphRAG",
    }
    assert parse("/curate is:curated #architecture") == {
        "command": "curate",
        "tags": ["architecture"],
        "mentions": [],
        "verified_only": False,
        "curated_only": True,
        "text": "",
    }
    assert parse("/feed is:curated @claude-brain") == {
        "command": "feed",
        "tags": [],
        "mentions": ["claude-brain"],
        "verified_only": False,
        "curated_only": True,
        "text": "",
    }
    assert parse("/search hybrid bm25 #graphrag")["command"] == "search"


def test_board_curate_activity_ranking_and_offline_ai_suggest(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    db_path = str(tmp_path / "board.db")
    board = CyberspaceBoardEngine(db_path=db_path, seed=False, enable_s3_sync=False)

    t1 = board.create_topic(
        peer_id="peer-a",
        title="Quiet Topic #notes",
        body="Single post topic about notes.",
        author_username="alice",
        auto_agent_reply=False,
    )
    t2 = board.create_topic(
        peer_id="peer-b",
        title="Hot GraphRAG Thread #graphrag",
        body="Multi-reply active thread with GraphRAG.",
        author_username="bob",
        auto_agent_reply=False,
    )
    board.create_post(t2["topic_id"], "peer-a", "First follow-up reply", author_username="alice", auto_agent_reply=False)
    board.create_post(t2["topic_id"], "peer-c", "Second follow-up reply", author_username="carol", auto_agent_reply=False)

    # Curate toggle & explicit value
    curated_t2 = board.curate_topic(t2["topic_id"], peer_id="peer-mod")
    assert curated_t2["curated"] is True
    curated_only = board.list_topics(curated_only=True, sort_by="activity")
    assert [t["topic_id"] for t in curated_only["topics"]] == [t2["topic_id"]]
    assert curated_only["topics"][0]["activity_score"] > t1["activity_score"]

    # Ranked activity across all topics puts t2 ahead of t1
    all_ranked = board.list_topics(curated_only=False, sort_by="activity")
    scores = [t["activity_score"] for t in all_ranked["topics"]]
    assert all_ranked["topics"][0]["topic_id"] == t2["topic_id"]
    assert scores == sorted(scores, reverse=True)

    # unified_search respects is:curated
    curated_search = board.unified_search("is:curated")
    assert curated_search["parsed"]["curated_only"] is True
    assert [r["topic_id"] for r in curated_search["results"]] == [t2["topic_id"]]

    # Uncurating removes it from curated_only list
    uncurated = board.curate_topic(t2["topic_id"], peer_id="peer-mod", curated=False)
    assert uncurated["curated"] is False
    assert board.list_topics(curated_only=True)["topics"] == []

    with pytest.raises(ValueError):
        board.curate_topic("topic-missing", peer_id="peer-mod")

    # Verify DB persistence cleanly and close connection
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT curated FROM cyberspace_topics WHERE topic_id = ?", (t2["topic_id"],)).fetchone()
        assert row is not None and row[0] == 0
    finally:
        conn.close()

    # Offline AI suggest fallback
    sugg = board.ai_suggest(query="graph", limit=6)
    assert sugg["is_free"] is True
    assert sugg["cost_usd"] == 0.0
    assert sugg["used_live_llm"] is False
    assert len(sugg["suggestions"]) >= 1
    assert any("graph" in (s["token"] + " " + s["reason"]).lower() for s in sugg["suggestions"])


def test_board_curate_activity_and_ai_suggest_http_endpoints(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    board = CyberspaceBoardEngine(db_path=str(tmp_path / "board_http.db"), seed=False, enable_s3_sync=False)
    monkeypatch.setattr(server, "cyberspace_board", board)

    t1 = board.create_topic("p1", "Low activity #misc", "Body one", author_username="u1", auto_agent_reply=False)
    t2 = board.create_topic("p2", "Active GraphRAG #graphrag", "Body two", author_username="u2", auto_agent_reply=False)
    board.create_post(t2["topic_id"], "p1", "Active reply", author_username="u1", auto_agent_reply=False)

    with _live_server() as addr:
        st_cur, curated = _http_json(
            addr,
            "POST",
            "/api/board/curate",
            {"topic_id": t2["topic_id"], "peer_id": "p1", "curated": True},
        )
        assert st_cur == 200
        assert curated["curated"] is True

        st2, feed = _http_json(addr, "GET", "/api/board/topics?sort_by=activity&curated_only=1")
        assert st2 == 200
        assert [t["topic_id"] for t in feed["topics"]] == [t2["topic_id"]]
        assert feed["topics"][0]["activity_score"] > t1["activity_score"]

        st_uncur, uncurated = _http_json(
            addr,
            "POST",
            "/api/board/curate",
            {"topic_id": t2["topic_id"], "peer_id": "p1", "curated": False},
        )
        assert st_uncur == 200
        assert uncurated["curated"] is False

        st_empty, feed_empty = _http_json(addr, "GET", "/api/board/topics?sort_by=activity&curated_only=1")
        assert st_empty == 200
        assert feed_empty["topics"] == []

        st_bad_cur, bad_cur = _http_json(
            addr,
            "POST",
            "/api/board/curate",
            {"topic_id": "nonexistent-topic-id", "peer_id": "p1", "curated": True},
        )
        assert st_bad_cur == 400
        assert "error" in bad_cur

        st3, sg_get = _http_json(addr, "GET", "/api/board/ai-suggest?q=graph&limit=5")
        assert st3 == 200 and sg_get["is_free"] is True and len(sg_get["suggestions"]) >= 1

        st4, sg_post = _http_json(
            addr,
            "POST",
            "/api/board/ai-suggest",
            {"query": "/post", "limit": 4},
        )
        assert st4 == 200
        assert sg_post["is_free"] is True
        assert sg_post["cost_usd"] == 0.0
        assert sg_post["used_live_llm"] is False
        assert 1 <= len(sg_post["suggestions"]) <= 4


# ---------------------------------------------------------------------------
# 4. Workstation, 3D Studio, IR Topic Search + Enter load & docking merge
# ---------------------------------------------------------------------------

def test_workstation_3dstudio_facets_and_docking_markup():
    ws_space = _extract_window(MESH_OS_HTML_UI, "win-agentspace")
    ws_studio_win = _extract_window(MESH_OS_HTML_UI, "win-workstation")
    ws_3d = render_workstation_window_html()

    assert 'title="Workstation">Workstation<' in ws_space
    for token in (
        'id="scopeUserBtn"', ">User<",
        'id="scopeTopicBtn"', ">Topic<",
        'id="scopeDynamicBtn"', ">Sandbox<",
        'id="spaceOwnerInput"',
        'onkeydown="onSpaceOwnerKeydown(event)"',
        'oninput="onSpaceOwnerInput(event)"',
        'id="spaceTopicSearchResults"',
        'id="finderTabBtn-3dstudio"',
        'id="finderTab-3dstudio"',
        "tc-ws-host",
    ):
        assert token in ws_space

    assert 'title="3D Studio">3D Studio<' in ws_studio_win
    assert '"title": "3D Studio"' in ws_3d
    assert '<span class="ws-kicker">3D Studio</span>' in ws_3d
    assert 'id="wsTileSpaceBtn"' in ws_3d
    assert "Dock in Workstation" in ws_3d
    assert "tc-ws-host" in ws_3d
    # CSS scoping rewrote #win-workstation selectors so styles apply inside #finderTab-3dstudio
    assert ".tc-ws-host .ws-body" in ws_3d
    assert "#win-workstation .ws-body" not in ws_3d
    assert "window.toggleDock3dStudio()" in ws_3d
    assert "mount3dStudioInWorkstation" in MESH_OS_HTML_UI
    assert "toggleDock3dStudio" in MESH_OS_HTML_UI


def test_workstation_docking_and_space_owner_enter_js():
    dock_js = _extract_js_range(
        MESH_OS_HTML_UI,
        "let _is3dStudioDocked = false;",
        "// ---- Ranger state",
    )
    key_js = _extract_js_range(
        MESH_OS_HTML_UI,
        "function onSpaceOwnerKeydown(ev)",
        "function selectWorkstationTopicResult(",
    )
    out = _run_node(
        f"""
        function makeNode(id) {{
          const classes = new Set();
          return {{
            id,
            textContent: '',
            innerHTML: '',
            style: {{}},
            children: [],
            appendChild(child) {{
              if (child._parent && child._parent !== this) {{
                child._parent.children = child._parent.children.filter(c => c !== child);
              }}
              child._parent = this;
              this.children.push(child);
            }},
            classList: {{
              add(...cs) {{ cs.forEach(c => classes.add(c)); }},
              remove(...cs) {{ cs.forEach(c => classes.delete(c)); }},
              toggle(c, force) {{
                if (force === undefined) {{
                  if (classes.has(c)) classes.delete(c); else classes.add(c);
                }} else if (force) classes.add(c); else classes.delete(c);
              }},
              contains(c) {{ return classes.has(c); }},
            }},
          }};
        }}
        const wsWin = makeNode('win-workstation');
        const spWin = makeNode('win-agentspace');
        const host = makeNode('finderTab-3dstudio');
        const filesPanel = makeNode('finderTab-files');
        const filesBtn = makeNode('finderTabBtn-files');
        const studioBtn = makeNode('finderTabBtn-3dstudio');
        const dockBtn = makeNode('wsTileSpaceBtn');
        dockBtn.textContent = 'Dock in Workstation';
        const wsBody = makeNode('wsBody');
        wsWin.appendChild(wsBody);
        host.classList.add('hidden');

        const map = {{
          'win-workstation': wsWin,
          'win-agentspace': spWin,
          'finderTab-3dstudio': host,
          'finderTab-files': filesPanel,
          'finderTabBtn-files': filesBtn,
          'finderTabBtn-3dstudio': studioBtn,
          'wsTileSpaceBtn': dockBtn,
        }};
        const document = {{
          getElementById: (id) => map[id] || null,
          querySelector: (sel) => (sel === '[data-ws-root="true"]' ? wsBody : null),
        }};
        let resolvedCalls = 0;
        let hiddenSearch = 0;
        const window = {{
          TinCanWorkstation: {{ refresh() {{}} }},
        }};
        function hideSpaceTopicSearchResults() {{ hiddenSearch++; }}
        function resolveAndLoadSpaceOwner() {{ resolvedCalls++; }}
        function bringToFront() {{}}
        function toggleWindow() {{}}
        {dock_js}
        {key_js}

        switchFinderTab('3dstudio');
        const dockedInHost = host.children.includes(wsBody);
        const dockedBtnText = dockBtn.textContent;
        const wsHiddenWhileDocked = wsWin.classList.contains('hidden');

        window.toggleDock3dStudio();
        const returnedToWs = wsWin.children.includes(wsBody);
        const undockedBtnText = dockBtn.textContent;
        const wsVisibleAfterUndock = !wsWin.classList.contains('hidden');

        let prevented = false;
        onSpaceOwnerKeydown({{ key: 'Enter', preventDefault() {{ prevented = true; }} }});
        console.log(JSON.stringify({{
          dockedInHost,
          dockedBtnText,
          wsHiddenWhileDocked,
          returnedToWs,
          undockedBtnText,
          wsVisibleAfterUndock,
          prevented,
          resolvedCalls,
        }}));
        """
    )
    assert out["dockedInHost"] is True
    assert out["dockedBtnText"] == "Undock Window"
    assert out["wsHiddenWhileDocked"] is True
    assert out["returnedToWs"] is True
    assert out["undockedBtnText"] == "Dock in Workstation"
    assert out["wsVisibleAfterUndock"] is True
    assert out["prevented"] is True
    assert out["resolvedCalls"] == 1


# ---------------------------------------------------------------------------
# 5. Terminal Harnesses (tincan_brew.py, shell_component.py, mesh_os_ui.py)
# ---------------------------------------------------------------------------

def test_harness_catalog_discovery_and_commands(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    catalog_clis = {h["cli"]: h for h in HARNESS_CATALOG}
    assert {"agy", "claude", "opencode", "dsx"}.issubset(catalog_clis.keys())
    assert catalog_clis["dsx"]["fallback"] is True
    assert "NoJuanNobody/dsx" in catalog_clis["dsx"]["repo"]

    # Simulate only dsx installed on PATH -> dsx becomes best_harness
    monkeypatch.setattr(shutil, "which", lambda cmd: "/usr/local/bin/dsx" if cmd == "dsx" else None)
    snap_dsx = discover_harnesses(str(tmp_path))
    assert snap_dsx["best_harness"] == "dsx"
    assert snap_dsx["best_cli"] == "dsx"
    assert snap_dsx["fallback_harness"] == "dsx"

    # Simulate agy + claude installed -> agy (tier 1 first entry) wins over fallback dsx
    monkeypatch.setattr(
        shutil,
        "which",
        lambda cmd: f"/opt/bin/{cmd}" if cmd in ("agy", "claude", "dsx") else None,
    )
    snap_agy = discover_harnesses(str(tmp_path))
    assert snap_agy["best_harness"] == "antigravity"
    assert snap_agy["best_cli"] == "agy"

    for cmd in (
        "harnesses",
        "harness best",
        "harness inspect antigravity",
        "harness inspect dsx",
        "agy refactor relay",
        "claude audit auth",
        "opencode check tests",
        "dsx build bundle",
    ):
        res = handle_harness_command(cmd, peer_id="tester", config_dir=str(tmp_path), queue_hitl=False)
        assert res["status"] == "ok", f"Failed command: {cmd} -> {res}"
        assert res["output"]


def test_shell_component_and_win_terminal_harness_bar():
    # shell_component.py help & dispatch
    for token in ("harnesses", "harness <cmd>", "<agy|claude|opencode|dsx> <prompt>", "/api/terminal/harness"):
        assert token in SHELL_JS
    for verb in ("'harnesses'", "'harness'", "'agy'", "'claude'", "'opencode'", "'dsx'"):
        assert verb in SHELL_JS

    # #win-terminal contains #termHarnessBar and zero forbidden legacy IDs
    term = _extract_window(MESH_OS_HTML_UI, "win-terminal")
    assert 'id="termHarnessBar"' in term
    for action in (
        "harness best",
        "harness inspect antigravity",
        "harness inspect claude-code",
        "harness inspect opencode",
        "harness inspect dsx",
        "harnesses",
    ):
        assert action in term

    for forbidden in (
        "termTree",
        "termDriveTree",
        "termStatFiles",
        "termRunsTable",
        "aeonikRecentOutput",
        "RECENT",
        'id="aeonikShellInput"',
        'id="termShellTranscript"',
        'id="termShellStatusPill"',
    ):
        assert forbidden not in term
        assert forbidden not in MESH_OS_HTML_UI


def test_terminal_harnesses_http_endpoints(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(shutil, "which", lambda cmd: "/usr/local/bin/agy" if cmd == "agy" else None)

    with _live_server() as addr:
        st_get, data_get = _http_json(addr, "GET", "/api/terminal/harnesses")
        assert st_get == 200
        assert data_get["best_cli"] == "agy"
        assert {h["cli"] for h in data_get["harnesses"]} >= {"agy", "claude", "opencode", "dsx"}

        st_post, data_post = _http_json(
            addr, "POST", "/api/terminal/harness", {"command": "opencode inspect workspace", "peer_id": "tester"}
        )
        assert st_post == 200
        assert data_post["harness"]["cli"] == "opencode"
        assert "opencode" in data_post["command"]


# ---------------------------------------------------------------------------
# 6. Arena Dropdown Overlap Fix (arena_duel_ui.py)
# ---------------------------------------------------------------------------

def test_arena_dropdown_grid_and_ellipsis_styles():
    for markup in (render_arena_duel("arenaWin", "Arena"), MESH_OS_HTML_UI):
        assert "grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr)" in markup
        assert 'class="min-w-0 overflow-hidden bg-[#f4f8f0] border border-[#111111] rounded-lg p-2 flex items-center gap-2"' in markup
        for side in ("A", "B"):
            sel_match = re.search(rf'<select id="arenaWinModel{side}Input"[^>]+>', markup)
            assert sel_match, f"Missing Model {side} select picker"
            tag = sel_match.group(0)
            assert "overflow:hidden; text-overflow:ellipsis;" in tag
            assert "width:100%; min-width:0; max-width:100%;" in tag


# ---------------------------------------------------------------------------
# 7. Arena Context CRUD, Universal Inventory, Context Palace CRUD/Import, Copilot
# ---------------------------------------------------------------------------

def test_arena_context_update_palace_crud_import_both_and_inventory(tmp_path, monkeypatch):
    # Verify CONTEXT_PALACE_DB env var resolution
    env_palace = str(tmp_path / "env_palace.db")
    monkeypatch.setenv("CONTEXT_PALACE_DB", env_palace)
    reg_env = ArenaContextRegistry(str(tmp_path / "ctx_env"), drive=DriveMirrorSource(module=None))
    try:
        assert reg_env.palace_path() == env_palace
    finally:
        reg_env.close_all()

    palace_db = str(tmp_path / "palace.db")
    reg = ArenaContextRegistry(
        str(tmp_path / "ctx"),
        drive=DriveMirrorSource(module=None),
        palace_db_path=palace_db,
    )
    space_mgr = AgentSpaceManager(base_dir=str(tmp_path / "spaces"))
    acct = "acct-ux-test"

    try:
        # 1) AgentContextStore.update_file() description + content CRUD
        st_a = reg.store(acct, "brain-a")
        st_a.ingest_text("guide.md", "# Guide\nInitial body", source="paste", description="Initial desc")

        upd_desc = st_a.update_file("/pasted/guide.md", description="Updated summary only")
        assert upd_desc["description"] == "Updated summary only"
        assert "Initial body" in upd_desc["content"]

        upd_both = st_a.update_file("/pasted/guide.md", content="# Guide\nRevised content", description="Revised desc")
        assert upd_both["description"] == "Revised desc"
        assert "Revised content" in upd_both["content"]
        assert any(f["path"] == "/pasted/guide.md" and f["description"] == "Revised desc" for f in st_a.list_files())

        with pytest.raises(ContextStoreError) as exc_missing:
            st_a.update_file("/pasted/missing.md", description="nope")
        assert exc_missing.value.status == 404

        with pytest.raises(ContextStoreError) as exc_empty:
            st_a.update_file("/pasted/guide.md")
        assert exc_empty.value.status == 400

        # 2) ArenaContextRegistry.palace_crud() create/list/read/update/pin/delete
        created = reg.palace_crud("create", {
            "canonical_name": "Mesh Architecture",
            "category": "architecture",
            "summary": "Blind relay + WebRTC topology",
            "value": "Ed25519 sealed relay envelopes with sub-80ms WebRTC data channels.",
        })
        node_id = created["concept"]["node_id"]
        assert created["action"] == "create"

        listed = reg.palace_crud("list", {"q": "WebRTC"})
        assert listed["count"] == 1 and listed["concepts"][0]["node_id"] == node_id

        read_res = reg.palace_crud("read", {"node_id": node_id})
        assert read_res["concept"]["canonical_name"] == "Mesh Architecture"

        upd_res = reg.palace_crud("update", {
            "node_id": node_id,
            "summary": "Updated topology summary",
            "value": "Updated memory text with Context Palace.",
        })
        assert upd_res["concept"]["summary"] == "Updated topology summary"

        pin_res = reg.palace_crud("pin", {"node_id": node_id, "pinned": True})
        assert pin_res["concept"]["pinned"] is True

        # Create a second concept to be deleted while keeping the first for import/inventory
        temp_concept = reg.palace_crud("create", {
            "canonical_name": "Temp Concept",
            "value": "To be deleted",
        })
        temp_id = temp_concept["concept"]["node_id"]
        del_res = reg.palace_crud("delete", {"node_id": temp_id})
        assert del_res["action"] == "delete"
        active_ids = {c["node_id"] for c in reg.palace_crud("list")["concepts"]}
        assert node_id in active_ids and temp_id not in active_ids

        # 3) import_from_palace(..., agent_id="both") populates BOTH brain-a and brain-b
        imp = reg.import_from_palace(acct, agent_id="both", node_ids=[node_id], added_by="tester")
        assert imp["agent_id"] == "both"
        assert set(imp["agent_ids"]) == {"brain-a", "brain-b"}
        files_a = {f["path"] for f in reg.store(acct, "brain-a").list_files()}
        files_b = {f["path"] for f in reg.store(acct, "brain-b").list_files()}
        assert "/palace/mesh-architecture.md" in files_a
        assert "/palace/mesh-architecture.md" in files_b
        assert "Updated memory text with Context Palace." in reg.store(acct, "brain-b").read_file("/palace/mesh-architecture.md")["content"]

        # 4) get_universal_inventory() aggregates Brain A, Brain B, .space, and Context Palace
        user_space = space_mgr.get_or_create_space("user", acct)
        user_space.write_file("/notes/runbook.md", b"# Runbook\nDeploy steps\n", updated_by="tester")
        inv = reg.get_universal_inventory(acct, space_manager=space_mgr)
        assert inv["counts"]["brain_a"] >= 2
        assert inv["counts"]["brain_b"] >= 1
        assert inv["counts"]["space"] >= 1
        assert inv["counts"]["palace"] >= 1
        assert "/palace/mesh-architecture.md" in inv["shared_in_both"]
        groups = {item["source_group"] for item in inv["items"]}
        assert {"brains", "space", "palace"}.issubset(groups)
    finally:
        reg.close_all()


def test_arena_context_http_both_ingest_update_palace_and_inventory(tmp_path, monkeypatch):
    accounts = PeerAccountRegistry(db_path=str(tmp_path / "accounts.db"))
    reg = ArenaContextRegistry(
        str(tmp_path / "ctx_http"),
        drive=DriveMirrorSource(module=None),
        palace_db_path=str(tmp_path / "palace_http.db"),
    )
    space_mgr = AgentSpaceManager(base_dir=str(tmp_path / "spaces_http"))

    monkeypatch.setattr(server, "account_registry", accounts)
    monkeypatch.setattr(server.ARENA_CONTEXT_API, "registry", reg)
    monkeypatch.setattr(server, "_space_manager", space_mgr)

    acct_id = "http-ctx-user"
    accounts.register_account(
        peer_id=acct_id,
        full_name="HTTP Context Tester",
        phone_number="+15615550101",
        email="httpctx@example.com",
        initial_tokens=2000,
        initial_credit_usd=2.0,
    )
    token = accounts.create_session(acct_id)
    space_mgr.get_or_create_space("user", acct_id).write_file(
        "/src/app.py", b"print('mesh')\n", updated_by="tester"
    )

    try:
        with _live_server() as addr:
            # POST /api/arena/context/ingest with agent_id="both"
            st, ing = _http_json(
                addr,
                "POST",
                "/api/arena/context/ingest",
                {
                    "agent_id": "both",
                    "files": [{"name": "shared.md", "content": "Shared spec v1", "description": "Spec v1"}],
                },
                token=token,
            )
            assert st == 200 and ing["agent_id"] == "both"
            assert set(ing["agent_ids"]) == {"brain-a", "brain-b"}

            # POST /api/arena/context/update updating both brains
            st2, upd = _http_json(
                addr,
                "POST",
                "/api/arena/context/update",
                {
                    "agent_id": "both",
                    "path": "/uploads/shared.md",
                    "content": "Shared spec v2",
                    "description": "Spec v2",
                },
                token=token,
            )
            assert st2 == 200 and upd["updated"]["description"] == "Spec v2"
            assert "Shared spec v2" in reg.store(acct_id, "brain-a").read_file("/uploads/shared.md")["content"]
            assert "Shared spec v2" in reg.store(acct_id, "brain-b").read_file("/uploads/shared.md")["content"]

            # Create & import a Context Palace item so inventory includes Palace too
            st3, pc = _http_json(
                addr,
                "POST",
                "/api/arena/context/palace/crud",
                {"action": "create", "canonical_name": "HTTP Concept", "value": "Palace memory body"},
                token=token,
            )
            assert st3 == 200
            node_id = pc["concept"]["node_id"]

            st3b, pl = _http_json(addr, "GET", "/api/arena/context/palace?q=HTTP", token=token)
            assert st3b == 200 and any(c["node_id"] == node_id for c in pl["concepts"])

            st3c, imp = _http_json(
                addr,
                "POST",
                "/api/arena/context/palace/import",
                {"agent_id": "both", "node_ids": [node_id]},
                token=token,
            )
            assert st3c == 200 and imp["agent_id"] == "both"
            assert set(imp["agent_ids"]) == {"brain-a", "brain-b"}

            st4, inv = _http_json(addr, "GET", "/api/arena/context/inventory", token=token)
            assert st4 == 200
            assert inv["counts"]["brain_a"] >= 1
            assert inv["counts"]["brain_b"] >= 1
            assert inv["counts"]["space"] >= 1
            assert inv["counts"]["palace"] >= 1
            assert "/uploads/shared.md" in inv["shared_in_both"]
            assert any(i.get("node_id") == node_id for i in inv["items"])
    finally:
        reg.close_all()


def test_copilot_ui_palace_hooks():
    html = render_copilot_window_html()
    for token in (
        'id="copilotAttachPalaceBtn"',
        "/api/arena/context/palace",
        "/api/arena/context/palace/crud",
        "/api/arena/context/palace/import",
    ):
        assert token in html or token in COPILOT_SCRIPT
        assert token in MESH_OS_HTML_UI


# ---------------------------------------------------------------------------
# 8. Simplified Arena Run + Vote A/B + Short Feedback Form + Persistence
# ---------------------------------------------------------------------------

def test_arena_run_button_vote_form_and_removed_legacy_buttons():
    arena_html = render_arena_duel("arenaWin", "Arena")
    for text in ("Run Arena", 'id="arenaWinRunBtn"', 'id="arenaWinVoteForm"', 'id="arenaWinVotePickA"',
                 'id="arenaWinVotePickB"', 'id="arenaWinVoteTagSelect"', 'id="arenaWinVoteReasonInput"',
                 'id="arenaWinVoteSubmitBtn"'):
        assert text in arena_html

    for legacy in ("Battle 2 Brains", "Use in Agent Space & Sandbox", "Use in Agent Space"):
        assert legacy not in arena_html
        assert legacy not in ARENA_DUEL_SCRIPT
        assert legacy not in MESH_OS_HTML_UI

    # Node.js check: clicking Vote A opens form, submitting sends feedback to /api/mesh/arena/vote
    duel_js = _extract_js_range(
        ARENA_DUEL_SCRIPT,
        "const VIEWS = __ARENA_VIEWS__;",
        "function boot()",
    ).replace("__ARENA_VIEWS__", '["arenaWin"]')
    out = _run_node(
        f"""
        function makeEl(id, extra) {{
          const classes = new Set();
          return Object.assign({{
            id,
            value: '',
            textContent: '',
            checked: false,
            style: {{}},
            focus() {{}},
            classList: {{
              add(c) {{ classes.add(c); }},
              remove(c) {{ classes.delete(c); }},
              contains(c) {{ return classes.has(c); }},
            }},
          }}, extra || {{}});
        }}
        const elems = {{
          arenaWinVoteForm: makeEl('arenaWinVoteForm'),
          arenaWinVotePickA: makeEl('arenaWinVotePickA'),
          arenaWinVotePickB: makeEl('arenaWinVotePickB'),
          arenaWinVoteTagSelect: makeEl('arenaWinVoteTagSelect', {{ value: 'Better context recall' }}),
          arenaWinVoteReasonInput: makeEl('arenaWinVoteReasonInput', {{ value: 'Cited /uploads/shared.md directly' }}),
          arenaWinVoteStatus: makeEl('arenaWinVoteStatus'),
        }};
        elems.arenaWinVoteForm.classList.add('hidden');
        const posted = [];
        const document = {{
          getElementById: (id) => elems[id] || null,
          addEventListener() {{}},
        }};
        const window = {{}};
        const localStorage = {{ getItem: () => '', setItem() {{}} }};
        const currentRoom = 'main';
        const myPeerId = 'peer-voter';
        function fetch(url, opts) {{
          posted.push({{ url, body: JSON.parse((opts && opts.body) || '{{}}') }});
          return Promise.resolve({{ ok: true, json: async () => ({{ status: 'voted' }}) }});
        }}
        {duel_js}
        lastDuel['arenaWin'] = {{ match_id: 'arena_m1', a: 'gemini-brain', b: 'claude-brain', prompt: 'Audit spec' }};
        (async () => {{
          await window.arenaDuelVote('arenaWin', 'A');
          const formVisibleAfterClick = !elems.arenaWinVoteForm.classList.contains('hidden');
          const pickAChecked = elems.arenaWinVotePickA.checked;
          await window.arenaDuelSubmitVote('arenaWin');
          const formHiddenAfterSubmit = elems.arenaWinVoteForm.classList.contains('hidden');
          console.log(JSON.stringify({{
            formVisibleAfterClick,
            pickAChecked,
            formHiddenAfterSubmit,
            posted,
            statusText: elems.arenaWinVoteStatus.textContent,
          }}));
        }})();
        """
    )
    assert out["formVisibleAfterClick"] is True
    assert out["pickAChecked"] is True
    assert out["formHiddenAfterSubmit"] is True
    vote_call = next(p for p in out["posted"] if p["url"] == "/api/mesh/arena/vote")
    assert vote_call["body"]["match_id"] == "arena_m1"
    assert vote_call["body"]["winner_side"] == "A"
    assert vote_call["body"]["feedback"] == "Better context recall — Cited /uploads/shared.md directly"
    assert "Better context recall" in out["statusText"]


def test_arena_vote_feedback_backend_and_http_persistence(tmp_path, monkeypatch):
    accounts = PeerAccountRegistry(db_path=str(tmp_path / "vote_accounts.db"))
    engine = TinCanMeshOSEngine(seed=False)
    monkeypatch.setattr(server, "account_registry", accounts)
    monkeypatch.setattr(server, "mesh_os", engine)

    pid = "voter-peer-1"
    accounts.register_account(
        peer_id=pid,
        full_name="Arena Voter",
        phone_number="+15615550102",
        email="voter@example.com",
        initial_tokens=5000,
        initial_credit_usd=5.0,
    )
    token = accounts.create_session(pid)
    match = accounts.create_arena_match(pid, "gemini-brain", "claude-brain", prompt_preview="Summarize mesh")
    accounts.bill_arena_side(pid, match["match_id"], "A", "gemini-brain", 10, 10, 20, 0.001)
    accounts.bill_arena_side(pid, match["match_id"], "B", "claude-brain", 10, 12, 22, 0.002)

    with _live_server() as addr:
        st, resp = _http_json(
            addr,
            "POST",
            "/api/mesh/arena/vote",
            {
                "match_id": match["match_id"],
                "winner_side": "B",
                "feedback": "More helpful code/reasoning — Cleaner synthesis",
                "display_name": "Arena Voter",
            },
            token=token,
        )
        assert st == 200
        assert resp["status"] == "voted"
        assert resp["winner_side"] == "B"
        assert resp["feedback"] == "More helpful code/reasoning — Cleaner synthesis"
        assert resp["match"]["vote_feedback"] == "More helpful code/reasoning — Cleaner synthesis"

        # Unbilled duel vote also preserves feedback cleanly
        st2, resp2 = _http_json(
            addr,
            "POST",
            "/api/mesh/arena/vote",
            {
                "peer_id": "guest-voter",
                "winner_alias": "gemini-brain",
                "feedback": "Faster & cleaner",
            },
        )
        assert st2 == 200
        assert resp2["feedback"] == "Faster & cleaner"

    persisted_match = accounts.get_arena_match(match["match_id"])
    assert persisted_match is not None
    assert persisted_match["vote_feedback"] == "More helpful code/reasoning — Cleaner synthesis"
    assert engine.arena_matches[-1]["feedback"] == "Faster & cleaner"


# ---------------------------------------------------------------------------
# 9. Subscriptions Removed -> Ad-Supported Home Screen Credits
# ---------------------------------------------------------------------------

def test_subscriptions_removed_and_ad_supported_credits_present():
    arena_html = render_arena_duel("arenaWin", "Arena")
    home_html = render_ai_home_hub_html(include_assets=True)
    zen_html = ZEN_HEAD + "\n" + ZEN_BODY

    assert "AD-SUPPORTED AI CREDITS · ZERO SUBSCRIPTIONS" in arena_html
    assert "Watch Home Screen Ads →" in arena_html
    assert "AD-SUPPORTED AI CREDITS · ZERO SUBSCRIPTIONS" in MESH_OS_HTML_UI
    assert "Watch Home Screen Ads →" in MESH_OS_HTML_UI

    tokens_card = next(c for c in WORKFLOW_CARDS if c["id"] == "aiHomeCardTokens")
    assert "Zero subscriptions" in tokens_card["desc"]
    assert "NO SUBS" in tokens_card["metric"]
    assert "Watch Ads" in tokens_card["cta"]
    assert "Zero subscriptions" in home_html

    assert "Watch Ad +CR" in zen_html
    assert "zero subscriptions" in zen_html.lower()

    for blob in (arena_html, ARENA_DUEL_SCRIPT, home_html, zen_html, MESH_OS_HTML_UI):
        assert "Upgrade Arena Pro" not in blob
        assert "PRO MONETIZATION" not in blob
