"""Cyberspace Board single search bar: parsing, autocomplete, trending, hybrid + filters, and the UI markup."""

import json
import os
import threading
import time
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from iot_federated_agent_memory.cyberspace_board import CyberspaceBoardEngine


@pytest.fixture()
def board(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    return CyberspaceBoardEngine(db_path=str(tmp_path / "board.db"), seed=True, enable_s3_sync=False)


def test_parse_unified_query():
    P = CyberspaceBoardEngine.parse_unified_query
    assert P("crdt #Architecture @gemini-brain is:verified") == {
        "command": "search", "tags": ["architecture"], "mentions": ["gemini-brain"],
        "verified_only": True, "text": "crdt"}
    assert P("/topic graph rag")["tags"] == ["graph-rag"]
    assert P("/topic graph rag")["text"] == "" and P("/topic bm25")["command"] == "topic"
    assert P("/search webrtc mesh")["text"] == "webrtc mesh"
    assert P("email@example.com")["mentions"] == []  # not a mention
    assert P("")["text"] == "" and P("")["tags"] == []


def test_suggest_groups_come_from_board_data(board):
    out = board.suggest("#arch")
    groups = {g["group"]: g for g in out["groups"]}
    assert "architecture" in groups
    assert groups["architecture"]["items"][0]["token"] == "#architecture"
    agents = board.suggest("@gem")["groups"]
    assert agents[0]["group"] == "agents" and agents[0]["items"][0]["token"] == "@gemini-brain"
    # Every suggested #tag actually exists on the board (or is a real category).
    real_tags = {t.lower() for topic in board._load_all_topics_from_db() for t in topic["tags"]}
    from iot_federated_agent_memory.cyberspace_board import BOARD_CATEGORIES
    real = real_tags | {c["id"] for c in BOARD_CATEGORIES}
    for g in board.suggest("#")["groups"]:
        for it in g["items"]:
            assert it["name"] in real
    titles = [g["title"] for g in board.suggest("")["groups"]]
    assert titles[:3] == ["Cyberspace topics", "AI agents", "Architecture"]
    assert board.suggest("#zzzz-not-a-tag")["count"] == 0


def test_trending_is_real_activity_with_honest_fallback(board):
    now = time.time()
    tr = board.trending(window_days=7, now=now)
    assert tr["window"] == "7d" and tr["items"]
    real_tags = {t.lower() for topic in board._load_all_topics_from_db() for t in topic["tags"]}
    for it in tr["items"]:
        assert it["name"] in real_tags
        assert it["activity"] == it["topics"] + it["posts"] > 0
    acts = [it["activity"] for it in tr["items"]]
    assert acts == sorted(acts, reverse=True)
    # Far future: nothing in the last 7 days, so it says "all" instead of inventing numbers.
    later = board.trending(window_days=7, now=now + 365 * 86400)
    assert later["window"] == "all" and later["items"]


def test_unified_search_hybrid_and_filters(board):
    res = board.unified_search("crdt gossip")
    assert res["diagnostics"]["mode"] == "hybrid" and res["count"] >= 1
    assert "bm25" in res["diagnostics"] and "subgraph" in res["diagnostics"]
    tag_only = board.unified_search("#security")
    assert tag_only["diagnostics"]["mode"] == "filter"
    assert all("security" in [t.lower() for t in r["tags"]] or r["category"] == "security" for r in tag_only["results"])
    ver = board.unified_search("is:verified")
    assert all(r["author_verified"] for r in ver["results"])
    topic_cmd = board.unified_search("/topic bm25")
    assert topic_cmd["parsed"]["tags"] == ["bm25"]
    assert all("bm25" in [t.lower() for t in r["tags"]] for r in topic_cmd["results"]) and topic_cmd["count"] >= 1
    none = board.unified_search("#zzzz-not-a-tag")
    assert none["count"] == 0


@pytest.fixture()
def live(board, monkeypatch):
    import server
    monkeypatch.setattr(server, "cyberspace_board", board)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.MeshGatewayHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def _get(url):
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.loads(r.read())


def test_endpoints(live):
    q = _get(f"{live}/api/board/query?q=%23architecture%20is%3Averified")
    assert q["parsed"]["tags"] == ["architecture"] and q["parsed"]["verified_only"] is True
    s = _get(f"{live}/api/board/suggest?q=%40gem&limit=3")
    assert s["groups"][0]["items"][0]["token"] == "@gemini-brain"
    t = _get(f"{live}/api/board/trending?days=7&limit=3")
    assert len(t["items"]) <= 3 and t["window"] in ("7d", "all")


def test_ui_has_one_search_input_and_no_old_form():
    from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI as H
    start = H.index('id="win-board"')
    end = H.index('id="boardTab-graph"', start)
    board = H[start:end]
    for gone in ('id="boardSearchMode"', 'id="boardCategoryBar"', 'id="boardVerifiedOnlyToggle"',
                 'id="boardLabSearchInput"', 'id="boardTab-search"', 'id="boardTabBtn-search"', ">\n                Search\n"):
        assert gone not in board, gone
    assert board.count('id="boardSearchInput"') == 1
    assert 'role="combobox"' in board and 'id="boardSuggestList"' in board and 'id="boardTrending"' in board
    assert 'how this ranked' in board
    for needle in ("/api/board/suggest", "/api/board/query", "/api/board/trending", "'/search '", "'/topic '",
                   "is:verified", "ev.metaKey || ev.ctrlKey", "ArrowDown", "ArrowUp"):
        assert needle in H, needle
