"""The two-brain duel and its context panel render in every arena view."""

import collections
import gzip
import re
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

import server
from iot_federated_agent_memory.arena_duel_ui import ARENA_VIEWS, render_arena_duel
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI


@pytest.fixture(scope="module")
def base():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.MeshGatewayHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def _window(html, win_id):
    start = html.index(f'<div id="{win_id}" class="mesh-window')
    nxt = html.find('class="mesh-window', start + 40)
    return html[start: nxt if nxt != -1 else len(html)]


BRAIN_PANEL_IDS = ("Slot{s}", "Result{s}", "Model{s}Input", "Agent{s}", "Used{s}", "Files{s}", "Upload{s}",
                   "PasteText{s}", "VoteBtn{s}", "UseCtx{s}")


def test_arena_route_shows_both_brain_slots(base):
    req = urllib.request.Request(base + "/arena", headers={"Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        body = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)
    html = body.decode("utf-8")
    # /arena opens win-arena in single-window mode ...
    assert "window.location.pathname === '/arena') singleWindowParam = 'win-arena'" in html
    # ... and win-arena now holds the duel with both brain slots and their context panels.
    win = _window(html, "win-arena")
    assert 'id="arenaWinBattleBox"' in win
    for side in "AB":
        for pat in BRAIN_PANEL_IDS:
            assert f'id="arenaWin{pat.format(s=side)}"' in win, pat.format(s=side)
        assert f'data-arena-slot="{side}"' in win
    assert 'id="arenaWinPromptInput"' in win and "arenaDuelRun('arenaWin')" in win


def test_quests_window_keeps_its_duel():
    win = _window(MESH_OS_HTML_UI, "win-quests")
    assert 'id="arenaBattleBox"' in win
    for side in "AB":
        for pat in BRAIN_PANEL_IDS:
            assert f'id="arena{pat.format(s=side)}"' in win
    assert 'id="arenaWinBattleBox"' not in win


def test_no_duplicate_ids_across_arena_views():
    ids = re.findall(r'\bid="([^"]+)"', MESH_OS_HTML_UI)
    counts = collections.Counter(ids)
    arena_ids = [i for i in counts if i.startswith("arena")]
    assert len(arena_ids) > 40
    dupes = [i for i in arena_ids if counts[i] > 1]
    assert dupes == []
    assert "<!--ARENA_DUEL:" not in MESH_OS_HTML_UI


def test_single_shared_script_and_legacy_entry_points():
    assert MESH_OS_HTML_UI.count('id="arenaDuelScript"') == 1
    script = MESH_OS_HTML_UI[MESH_OS_HTML_UI.index('id="arenaDuelScript"'):]
    assert 'const VIEWS = ["arenaWin", "arena"]' in script
    for fn in ("window.runArenaBattle", "window.voteArenaWinner", "window.updateArenaModelLabels",
               "window.sendArenaResultToSpace", "window.onArenaModelChange", "window.swapArenaModels",
               "window.loadArenaModels", "/api/mesh/arena/match", "/api/mesh/arena/models",
               "/api/mesh/arena/vote", "tincan_arena_models", "/api/arena/context/ingest",
               "/api/arena/context/import", "/api/arena/context/drive/link"):
        assert fn in script
    # Identity is the session cookie; a client peer header is never sent as a credential.
    assert "'X-TinCan-Peer'" not in script and "/api/arena/duel" not in script
    assert "arena: true" in script and "match_id" in script and "arena_side" in script and "agent_id" in script
    # The old inline duel is gone; one shared implementation serves both views.
    assert "async function runArenaBattle" not in MESH_OS_HTML_UI
    assert "body: JSON.stringify({ model: 'gemini-brain', prompt })" not in MESH_OS_HTML_UI


def test_launcher_and_dock_open_the_window_with_the_duel():
    assert "{ id: 'win-arena', name: 'Arena'" in MESH_OS_HTML_UI
    assert "toggleWindow('win-arena')" in MESH_OS_HTML_UI
    assert set(p for p, _w, _l in ARENA_VIEWS) == {"arenaWin", "arena"}


def test_render_is_prefix_scoped():
    a, b = render_arena_duel("x1"), render_arena_duel("y2")
    ids_a = set(re.findall(r'\bid="([^"]+)"', a))
    ids_b = set(re.findall(r'\bid="([^"]+)"', b))
    assert ids_a and not (ids_a & ids_b)
    assert all(i.startswith("x1") for i in ids_a)


@pytest.mark.parametrize("route", ["/arena", "/quests", "/rewards"])
def test_arena_view_routes_are_served(base, route):
    with urllib.request.urlopen(base + route) as resp:
        assert resp.status == 200
        html = resp.read().decode("utf-8")
    assert 'id="arenaWinBattleBox"' in html and 'id="arenaBattleBox"' in html
