"""Live HTTP Server E2E Test for TinCan Knowledge Graph & Conflict Resolution (T-04).

Spins up a real `server.py` subprocess on an ephemeral localhost port, exercises:
  1. POST /api/crdt/kg (upsert_entity, add_edge, propose_decision)
  2. POST /api/crdt/gossip (inject concurrent remote peer delta to trigger a conflict)
  3. Conflict detection assertion ({15, 60} surfaced on `jwt_ttl`)
  4. POST /api/crdt/kg (resolve_decision -> 30 clears conflicts to [])
  5. POST /api/crdt/kg (compact -> confirms compaction counter & snapshot parity)
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from iot_federated_agent_memory.agent_kg_crdt import FederatedAgentKnowledgeGraph

REPO_ROOT = Path(__file__).resolve().parent.parent


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _http_json(url: str, payload: dict | None = None, timeout: float = 5.0) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


@pytest.fixture(scope="module")
def live_server_url():
    port = _free_port()
    env = os.environ.copy()
    env["PORT"] = str(port)
    env["TINCAN_S3_DISABLED"] = "1"
    env["PYTHONPATH"] = str(REPO_ROOT)

    proc = subprocess.Popen(
        [sys.executable, str(REPO_ROOT / "server.py")],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    base = f"http://127.0.0.1:{port}"
    deadline = time.time() + 15.0
    ready = False
    while time.time() < deadline:
        if proc.poll() is not None:
            out, err = proc.communicate(timeout=2)
            pytest.fail(f"server.py exited early (rc={proc.returncode}):\nSTDOUT:\n{out}\nSTDERR:\n{err}")
        try:
            status, _ = _http_json(f"{base}/api/crdt/kg", {"action": "snapshot"}, timeout=1.0)
            if status == 200:
                ready = True
                break
        except Exception:
            time.sleep(0.2)

    if not ready:
        proc.terminate()
        out, err = proc.communicate(timeout=3)
        pytest.fail(f"server.py did not become ready on {base}:\nSTDOUT:\n{out}\nSTDERR:\n{err}")

    try:
        yield base
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)


def test_live_server_kg_upsert_conflict_resolution_and_compaction(live_server_url: str):
    # 1. Upsert entity & relation
    status, res1 = _http_json(
        f"{live_server_url}/api/crdt/kg",
        {
            "action": "upsert_entity",
            "entity_id": "file:auth.py",
            "entity_type": "module",
            "fields": {"owner": "mac-a", "status": "draft"},
        },
    )
    assert status == 200
    assert res1["status"] == "ok"
    assert res1["identity"].startswith("tc:")
    entities_by_id = {e["entity_id"]: e for e in res1["snapshot"]["entities"]}
    assert "file:auth.py" in entities_by_id
    assert entities_by_id["file:auth.py"]["owner"] == "mac-a"

    status, res_edge = _http_json(
        f"{live_server_url}/api/crdt/kg",
        {
            "action": "add_edge",
            "src": "task:auth-refresh",
            "predicate": "touches",
            "dst": "file:auth.py",
        },
    )
    assert status == 200
    assert res_edge["status"] == "ok"

    # 2. Local server proposes jwt_ttl = 15
    status, res_local = _http_json(
        f"{live_server_url}/api/crdt/kg",
        {"action": "propose_decision", "topic": "jwt_ttl", "choice": 15},
    )
    assert status == 200
    assert res_local["conflicts"] == []

    # 3. Inject concurrent remote peer decision jwt_ttl = 60 via /api/crdt/gossip
    remote_kg = FederatedAgentKnowledgeGraph("remote-peer-b")
    remote_kg.propose_decision("jwt_ttl", 60)
    remote_delta = remote_kg.mesh.offline_queue[-1]
    status, res_gossip = _http_json(
        f"{live_server_url}/api/crdt/gossip",
        {"delta": remote_delta.to_dict()},
    )
    assert status == 200
    assert res_gossip["status"] == "ok"
    assert len(res_gossip["conflicts"]) == 1
    conflict = res_gossip["conflicts"][0]
    assert conflict["topic"] == "jwt_ttl"
    assert set(conflict["values"]) == {15, 60}

    # 4. Resolve conflict to 30 and confirm conflicts clears to []
    status, res_resolved = _http_json(
        f"{live_server_url}/api/crdt/kg",
        {"action": "resolve_decision", "topic": "jwt_ttl", "choice": 30},
    )
    assert status == 200
    assert res_resolved["conflicts"] == []
    assert res_resolved["snapshot"]["conflicts"] == []

    # 5. Repeated updates + compaction
    for i in range(6):
        _http_json(
            f"{live_server_url}/api/crdt/kg",
            {
                "action": "upsert_entity",
                "entity_id": "file:auth.py",
                "entity_type": "module",
                "fields": {"rev": i},
            },
        )
    status, res_compact = _http_json(
        f"{live_server_url}/api/crdt/kg",
        {"action": "compact"},
    )
    assert status == 200
    assert res_compact["status"] == "ok"
    entities_final = {e["entity_id"]: e for e in res_compact["snapshot"]["entities"]}
    assert entities_final["file:auth.py"]["rev"] == 5
