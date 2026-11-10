#!/usr/bin/env python3
"""
Tests for the TinCan Cyberspace Discussion Board, BM25 + GraphRAG Knowledge Base,
and @verifier-agent Identity Verification Form workflow.
"""

import json
import os
import tempfile
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from iot_federated_agent_memory.account_registry import PeerAccountRegistry
from iot_federated_agent_memory.cyberspace_board import (
    BM25Retriever,
    CyberspaceBoardEngine,
    parse_cyberspace_tags,
)
from iot_federated_agent_memory.tincan_cli import main as cli_main


def test_parse_cyberspace_tags_separates_users_agents_and_hashtags():
    text = (
        "Hey @alejandro and @harper, let's ask @gemini-brain and @verifier-agent "
        "about #GraphRAG and #BM25 in #cyberspace!"
    )
    parsed = parse_cyberspace_tags(text)
    assert parsed["user_mentions"] == ["alejandro", "harper"]
    assert parsed["agent_mentions"] == ["gemini-brain", "verifier-agent"]
    assert parsed["hashtags"] == ["graphrag", "bm25", "cyberspace"]


def test_topic_creation_self_and_peer_tagging_and_auto_agent_reply():
    with tempfile.TemporaryDirectory() as tmpdir:
        reg = PeerAccountRegistry(db_path=os.path.join(tmpdir, "accounts.db"))
        board = CyberspaceBoardEngine(
            db_path=os.path.join(tmpdir, "board.db"),
            account_registry=reg,
            seed=True,
        )

        topic = board.create_topic(
            peer_id="peer-alejandro",
            title="Building Federated Knowledge Graphs with BM25 and GraphRAG",
            body="Tagging myself @alejandro, my peer @harper, and summoning @gemini-brain for #graphrag #bm25 synthesis!",
            category="research",
            author_username="alejandro",
            auto_agent_reply=True,
        )

        assert topic["author_username"] == "alejandro"
        assert "alejandro" in topic["user_mentions"]
        assert "harper" in topic["user_mentions"]
        assert "gemini-brain" in topic["agent_mentions"]
        assert "graphrag" in topic["tags"]
        assert "bm25" in topic["tags"]

        # Verify @gemini-brain automatically posted a synthesis reply in the topic
        assert topic["reply_count"] >= 1
        agent_posts = [p for p in topic["posts"] if p["is_agent"] and p["author_username"] == "gemini-brain"]
        assert len(agent_posts) == 1
        assert "@alejandro" in agent_posts[0]["body"]


def test_bm25_and_graphrag_hybrid_information_retrieval():
    with tempfile.TemporaryDirectory() as tmpdir:
        board = CyberspaceBoardEngine(
            db_path=os.path.join(tmpdir, "board.db"),
            seed=True,
        )

        board.create_topic(
            peer_id="peer-quant",
            title="Zero-Knowledge Ed25519 Signatures in Cyberspace",
            body="@quant_dev and @claude-brain analyzing #ed25519 curve25519 #cryptography proofs.",
            category="cryptography",
            author_username="quant_dev",
        )

        # 1. BM25 Lexical Retrieval
        bm25_res = board.search("ed25519 curve25519 cryptography", mode="bm25", top_k=5)
        assert bm25_res["count"] >= 1
        top_bm25 = bm25_res["results"][0]
        assert top_bm25["bm25_score"] > 0
        assert "ed25519" in top_bm25["matched_terms"]

        # 2. GraphRAG Multi-Hop Retrieval (searching by @username + @agent + #tag)
        graph_res = board.search("@alejandro @gemini-brain #graphrag", mode="graphrag", top_k=5)
        assert graph_res["count"] >= 1
        top_graph = graph_res["results"][0]
        assert top_graph["graphrag_score"] > 0
        assert len(top_graph["graph_paths"]) >= 1
        assert len(graph_res["subgraph"]["nodes"]) >= 3

        # 3. Hybrid Search (BM25 + GraphRAG fusion)
        hybrid_res = board.search("BM25 term saturation @harper #graphrag", mode="hybrid", top_k=5)
        assert hybrid_res["count"] >= 1
        assert "GraphRAG + BM25 Synthesis" in hybrid_res["synthesis"]
        assert hybrid_res["results"][0]["score"] > 0


def test_verification_agent_form_dispatch_and_submission():
    with tempfile.TemporaryDirectory() as tmpdir:
        reg = PeerAccountRegistry(db_path=os.path.join(tmpdir, "accounts.db"))
        board = CyberspaceBoardEngine(
            db_path=os.path.join(tmpdir, "board.db"),
            account_registry=reg,
            seed=False,
        )

        unverified_peer = "peer-newcomer-99"
        verified_before, _ = board.is_peer_verified(unverified_peer)
        assert verified_before is False

        # Attempting to post when require_verification=True triggers @verifier-agent to send the form
        blocked = board.create_topic(
            peer_id=unverified_peer,
            title="Unverified Post Attempt",
            body="Hello #cyberspace from @newcomer!",
            author_username="newcomer",
            require_verification=True,
        )
        assert blocked["require_verification"] is True
        assert blocked["agent"] == "@verifier-agent"
        req_id = blocked["verification_dispatch"]["request_id"]
        assert req_id.startswith("vrf-")

        # Check status shows pending form sent by @verifier-agent
        status_pending = board.get_verification_status(unverified_peer)
        assert status_pending["verified"] is False
        assert len(status_pending["pending_forms"]) == 1

        # User fills out and submits the verification form to @verifier-agent
        sub_res = board.submit_verification_form(
            peer_id=unverified_peer,
            full_name="Alejandro Londono",
            username="newcomer",
            email="newcomer@fau.edu",
            phone_number="+15615550199",
            role="FAU Graduate School / Academic",
            bio="GraphRAG & Distributed Cyberspace Researcher",
            consent_pii=True,
            request_id=req_id,
        )
        assert sub_res["verified"] is True
        assert sub_res["agent"] == "@verifier-agent"
        assert sub_res["username"] == "@newcomer"
        assert len(sub_res["attestation_hash"]) == 24

        # Now the user is verified and can post with require_verification=True!
        created = board.create_topic(
            peer_id=unverified_peer,
            title="Verified Cyberspace Post",
            body="Now verified as @newcomer tagging @gemini-brain in #cyberspace!",
            require_verification=True,
        )
        assert created["topic_id"].startswith("topic-")
        assert created["author_verified"] is True


def test_http_endpoints_and_cli_for_board_and_verifier_agent():
    import server as srv

    srv_thread_server = ThreadingHTTPServer(("127.0.0.1", 0), srv.MeshGatewayHandler)
    port = srv_thread_server.server_port
    t = threading.Thread(target=srv_thread_server.serve_forever, daemon=True)
    t.start()
    base_url = f"http://127.0.0.1:{port}"

    try:
        # 1. Dispatch verification form via POST /api/verify/send
        req = urllib.request.Request(
            f"{base_url}/api/verify/send",
            data=json.dumps({"peer_id": "peer-http-test", "username": "cyber_student"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            send_data = json.loads(resp.read().decode("utf-8"))
        assert send_data["status"] == "dispatched"
        assert send_data["agent"] == "@verifier-agent"

        # 2. Submit verification form via POST /api/verify/submit
        req_sub = urllib.request.Request(
            f"{base_url}/api/verify/submit",
            data=json.dumps({
                "peer_id": "peer-http-test",
                "full_name": "Cyber Student",
                "username": "cyber_student",
                "email": "cyber_student@fau.edu",
                "phone_number": "+15615550999",
                "consent_pii": True,
                "request_id": send_data["request_id"],
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req_sub, timeout=5) as resp:
            sub_data = json.loads(resp.read().decode("utf-8"))
        assert sub_data["verified"] is True

        # 3. Create topic via POST /api/board/topics tagging self, peer, and @openai-brain
        req_topic = urllib.request.Request(
            f"{base_url}/api/board/topics",
            data=json.dumps({
                "peer_id": "peer-http-test",
                "username": "cyber_student",
                "title": "Hybrid BM25 + GraphRAG Benchmark",
                "body": "Testing @cyber_student with @alejandro and @openai-brain on #bm25 #graphrag!",
                "category": "benchmarks",
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req_topic, timeout=5) as resp:
            t_data = json.loads(resp.read().decode("utf-8"))
        assert t_data["status"] == "created"
        topic_id = t_data["topic"]["topic_id"]
        assert t_data["topic"]["reply_count"] >= 1

        # 4. Search via GET /api/board/search
        with urllib.request.urlopen(f"{base_url}/api/board/search?q=BM25+GraphRAG+@cyber_student&mode=hybrid", timeout=5) as resp:
            s_data = json.loads(resp.read().decode("utf-8"))
        assert s_data["count"] >= 1
        assert any(r["topic_id"] == topic_id for r in s_data["results"])
        assert "bm25_diagnostics" in s_data
        assert s_data["bm25_diagnostics"]["corpus_size"] >= 1

        # 5. Upvote topic via POST /api/board/vote
        req_vote = urllib.request.Request(
            f"{base_url}/api/board/vote",
            data=json.dumps({
                "target_type": "topic",
                "target_id": topic_id,
                "peer_id": "peer-voter-2",
                "direction": "up",
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req_vote, timeout=5) as resp:
            v_data = json.loads(resp.read().decode("utf-8"))
        assert v_data["upvotes"] >= 2

        # 6. Mark reply as Accepted Solution via POST /api/board/solution
        first_post_id = t_data["topic"]["posts"][0]["post_id"]
        req_sol = urllib.request.Request(
            f"{base_url}/api/board/solution",
            data=json.dumps({
                "topic_id": topic_id,
                "post_id": first_post_id,
                "peer_id": "peer-http-test",
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req_sol, timeout=5) as resp:
            sol_data = json.loads(resp.read().decode("utf-8"))
        assert sol_data["resolved"] is True
        assert sol_data["accepted_post_id"] == first_post_id

        # 7. Shortest-path entity finder via GET /api/board/graph/path
        with urllib.request.urlopen(f"{base_url}/api/board/graph/path?from=@cyber_student&to=@openai-brain", timeout=5) as resp:
            path_data = json.loads(resp.read().decode("utf-8"))
        assert path_data["found"] is True
        assert path_data["hops"] >= 1

        # 8. Roster, Citizen Profile & Verification List via GET endpoints
        with urllib.request.urlopen(f"{base_url}/api/board/roster", timeout=5) as resp:
            roster_data = json.loads(resp.read().decode("utf-8"))
        assert any(u["username"] == "@cyber_student" for u in roster_data["users"])

        with urllib.request.urlopen(f"{base_url}/api/board/profile?user=cyber_student", timeout=5) as resp:
            prof_data = json.loads(resp.read().decode("utf-8"))
        assert prof_data["verified"] is True

        with urllib.request.urlopen(f"{base_url}/api/verify/list", timeout=5) as resp:
            vlist_data = json.loads(resp.read().decode("utf-8"))
        assert vlist_data["verified_count"] >= 1

        # 9. CLI check (`tincan board search`)
        rc = cli_main(["board", "search", "graphrag bm25", "--mode", "hybrid", "--json"])
        assert rc == 0
    finally:
        srv_thread_server.shutdown()
        srv_thread_server.server_close()
