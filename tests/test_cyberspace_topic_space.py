#!/usr/bin/env python3
"""
Tests for Cyberspace Forum Topic Single-File .space Filesystem Integration,
Hyper3D Rodin 3D Studio Agent (@rodin-agent / @ronin-agent),
ArtCraft Wasm & Code Playground Agent (@artcraft-agent),
and BM25 + CyberspaceGraphRAG File Indexing.
"""

import os
import sys
import tempfile
from pathlib import Path
import pytest

_WORKTREE_ROOT = str(Path(__file__).resolve().parent.parent)
if _WORKTREE_ROOT not in sys.path or sys.path[0] != _WORKTREE_ROOT:
    sys.path.insert(0, _WORKTREE_ROOT)

from iot_federated_agent_memory.account_registry import PeerAccountRegistry
from iot_federated_agent_memory.cyberspace_board import (
    BM25Retriever,
    CyberspaceBoardEngine,
    CyberspaceGraphRAG,
    KNOWN_AI_AGENTS,
    generate_minimal_glb,
    parse_cyberspace_tags,
)


def test_known_ai_agents_includes_rodin_and_artcraft():
    """Verify rodin-agent (with ronin alias) and artcraft-agent exist in KNOWN_AI_AGENTS."""
    assert "rodin-agent" in KNOWN_AI_AGENTS
    assert "ronin-agent" in KNOWN_AI_AGENTS
    assert "artcraft-agent" in KNOWN_AI_AGENTS

    rodin = KNOWN_AI_AGENTS["rodin-agent"]
    assert rodin["handle"] == "@rodin-agent"
    assert "Hyper3D Rodin" in rodin["display_name"]
    assert ".glb" in rodin["specialty"]

    ronin = KNOWN_AI_AGENTS["ronin-agent"]
    assert ronin["handle"] == "@ronin-agent"

    artcraft = KNOWN_AI_AGENTS["artcraft-agent"]
    assert artcraft["handle"] == "@artcraft-agent"
    assert "ArtCraft" in artcraft["display_name"]
    assert "CADCraft" in artcraft["specialty"]

    # Verify parser separates them as agent mentions
    parsed = parse_cyberspace_tags("Hello @rodin-agent, @ronin-agent, and @artcraft-agent with @alice")
    assert "rodin-agent" in parsed["agent_mentions"]
    assert "ronin-agent" in parsed["agent_mentions"]
    assert "artcraft-agent" in parsed["agent_mentions"]
    assert "alice" in parsed["user_mentions"]


def test_topic_creation_provisions_space_filesystem():
    """Verify that creating a topic provisions spaces/topics/{topic_id}.space with starter files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        reg = PeerAccountRegistry(db_path=os.path.join(tmpdir, "accounts.db"))
        board = CyberspaceBoardEngine(
            db_path=os.path.join(tmpdir, "board.db"),
            account_registry=reg,
            seed=True,
        )

        # Check seeded topics provisioned their .space files
        topics = board.list_topics(limit=10)["topics"]
        assert len(topics) >= 1
        for t in topics:
            assert "space" in t
            assert t["space"]["file_count"] >= 3
            assert os.path.exists(t["space"]["space_file"])

        # Create a new topic
        new_topic = board.create_topic(
            peer_id="peer-gamma",
            title="Next-Gen 3D Spatial-Temporal Compute Architecture",
            body="Proposing high-performance spatial nodes and CAD engineering workflows.",
            category="architecture",
            author_username="gamma_engineer",
            auto_agent_reply=False,
        )

        topic_id = new_topic["topic_id"]
        assert "space" in new_topic
        space_meta = new_topic["space"]
        assert space_meta["topic_id"] == topic_id
        assert space_meta["scope"] == "topic"
        assert space_meta["file_count"] >= 3
        assert os.path.exists(space_meta["space_file"])
        assert space_meta["merkle_root"] != ""

        # Verify starter files exist in the space
        files = {f["path"] for f in space_meta["files"]}
        assert "/README.md" in files
        assert "/src/main.py" in files
        assert "/artcraft/drawing.dxf" in files
        assert "/models3d/README.txt" in files

        # Verify get_topic includes space metadata
        fetched = board.get_topic(topic_id)
        assert fetched is not None
        assert "space" in fetched
        assert fetched["space"]["file_count"] >= 3

        # Verify list_topics includes space metadata
        listed = board.list_topics(limit=10)
        matching = [t for t in listed["topics"] if t["topic_id"] == topic_id]
        assert len(matching) == 1
        assert matching[0]["space"]["file_count"] >= 3


def test_read_and_write_topic_files():
    """Verify write_topic_file and read_topic_file functionality on a topic filesystem."""
    with tempfile.TemporaryDirectory() as tmpdir:
        board = CyberspaceBoardEngine(
            db_path=os.path.join(tmpdir, "board.db"),
            seed=False,
        )

        topic = board.create_topic(
            peer_id="peer-alice",
            title="Robotics Controller Workspace",
            body="Workspace for custom actuator control scripts.",
            author_username="alice",
            auto_agent_reply=False,
        )
        topic_id = topic["topic_id"]

        # Read starter file
        readme = board.read_topic_file(topic_id, "/README.md")
        assert readme["path"] == "/README.md"
        assert "Robotics Controller Workspace" in readme["content"]
        assert readme["size"] > 0
        assert readme["hash"] != ""

        # Write a python script
        py_code = "def compute_torque(current):\n    return current * 0.12\n"
        w_res = board.write_topic_file(
            topic_id=topic_id,
            path="/src/actuator.py",
            content=py_code,
            updated_by="alice",
        )
        assert w_res["path"] == "/src/actuator.py"
        assert w_res["size"] == len(py_code.encode("utf-8"))
        assert w_res["merkle_root"] != ""

        # Read written python script
        read_py = board.read_topic_file(topic_id, "/src/actuator.py")
        assert read_py["content"] == py_code
        assert read_py["updated_by"] == "alice"

        # Write binary file (minimal GLB)
        glb_data = generate_minimal_glb("actuator")
        w_glb = board.write_topic_file(
            topic_id=topic_id,
            path="/models3d/actuator.glb",
            content=glb_data,
            updated_by="alice",
        )
        assert w_glb["path"] == "/models3d/actuator.glb"
        assert w_glb["size"] == len(glb_data)

        # Read back GLB file
        read_glb = board.read_topic_file(topic_id, "/models3d/actuator.glb")
        assert read_glb["size"] == len(glb_data)
        assert read_glb["hash"] == w_glb["hash"]

        # Verify summary counts updated
        summary = board.get_topic_space_summary(topic_id)
        assert summary["file_count"] >= 6  # 4 starter + 2 written

        # Reading non-existent file raises FileNotFoundError
        with pytest.raises(FileNotFoundError):
            board.read_topic_file(topic_id, "/non_existent_file.txt")


def test_agent_tagging_writes_artifacts_and_replies():
    """Verify that tagging @rodin-agent and @artcraft-agent writes artifacts and references them in replies."""
    with tempfile.TemporaryDirectory() as tmpdir:
        board = CyberspaceBoardEngine(
            db_path=os.path.join(tmpdir, "board.db"),
            seed=False,
        )

        # 1. Tag @rodin-agent in topic creation
        t_rodin = board.create_topic(
            peer_id="peer-bob",
            title="Autonomous Drone Stator Mesh",
            body="Hey @rodin-agent, generate a 3D mesh model for our stator housing #3d #cad",
            author_username="bob",
            auto_agent_reply=True,
        )
        topic_id_rodin = t_rodin["topic_id"]

        # Verify agent replied
        posts = t_rodin["posts"]
        agent_posts = [p for p in posts if p["is_agent"] and p["author_username"] == "rodin-agent"]
        assert len(agent_posts) >= 1
        rodin_post = agent_posts[0]

        # Verify post references .glb file path
        expected_glb_path = f"/models3d/{topic_id_rodin}_mesh.glb"
        assert expected_glb_path in rodin_post["body"]

        # Verify .glb file was written to topic space and has valid glTF magic
        glb_rec = board.read_topic_file(topic_id_rodin, expected_glb_path)
        assert glb_rec["size"] > 0
        # If read as raw from space, check magic
        summary = board.get_topic_space_summary(topic_id_rodin)
        file_paths = [f["path"] for f in summary["files"]]
        assert expected_glb_path in file_paths

        # 2. Tag @artcraft-agent in a reply
        post_res = board.create_post(
            topic_id=topic_id_rodin,
            peer_id="peer-bob",
            body="Now summoning @artcraft-agent for Wasm playground code and CADCraft drawing",
            author_username="bob",
            auto_agent_reply=True,
        )

        # Verify artcraft agent reply
        artcraft_replies = [p for p in post_res.get("agent_replies", []) if p.get("author_username", "").lstrip("@") == "artcraft-agent"]
        assert len(artcraft_replies) >= 1
        art_post = artcraft_replies[0]

        # Verify reply references /src/agent_solution.py and/or /artcraft/agent_design.dxf
        assert "/src/agent_solution.py" in art_post["body"]
        assert "/artcraft/agent_design.dxf" in art_post["body"]

        # Verify files were written into the topic space
        sol_rec = board.read_topic_file(topic_id_rodin, "/src/agent_solution.py")
        assert "ArtCraft Agent Solution" in sol_rec["content"]

        dxf_rec = board.read_topic_file(topic_id_rodin, "/artcraft/agent_design.dxf")
        assert "SECTION" in dxf_rec["content"]


def test_bm25_and_graphrag_index_topic_files():
    """Verify that BM25 and CyberspaceGraphRAG index files stored in topic spaces."""
    with tempfile.TemporaryDirectory() as tmpdir:
        board = CyberspaceBoardEngine(
            db_path=os.path.join(tmpdir, "board.db"),
            seed=False,
        )

        topic = board.create_topic(
            peer_id="peer-carol",
            title="High-Speed Drone Aerodynamics",
            body="Optimizing airflow dynamics across rotor blades.",
            author_username="carol",
            auto_agent_reply=False,
        )
        topic_id = topic["topic_id"]

        # Write unique custom filename
        board.write_topic_file(
            topic_id=topic_id,
            path="/simulations/supersonic_flow_benchmark.py",
            content="print('aerodynamics simulation running')",
            updated_by="carol",
        )

        # 1. Test BM25 Lexical Retrieval matches the file name / path
        bm25_res = board.search("supersonic flow benchmark", mode="bm25", top_k=5)
        assert bm25_res["count"] >= 1
        matched_topic = bm25_res["results"][0]
        assert matched_topic["topic_id"] == topic_id
        assert matched_topic["bm25_score"] > 0
        assert any("supersonic" in t or "benchmark" in t for t in matched_topic["matched_terms"])

        # 2. Test CyberspaceGraphRAG contains file node and HAS_FILE edge
        file_node_id = f"file:{topic_id}:/simulations/supersonic_flow_benchmark.py"
        assert file_node_id in board.graphrag.nodes
        node_meta = board.graphrag.nodes[file_node_id]
        assert node_meta["type"] == "file"
        assert node_meta["path"] == "/simulations/supersonic_flow_benchmark.py"

        # Check HAS_FILE edge
        t_node = f"topic:{topic_id}"
        has_file_edges = [
            e for e in board.graphrag.edges
            if e["source"] == t_node and e["target"] == file_node_id and e["relation"] == "HAS_FILE"
        ]
        assert len(has_file_edges) >= 1

        # Check GraphRAG relational shortest path finder connects topic to file
        path_res = board.graphrag.find_entity_path(t_node, file_node_id)
        assert path_res["found"] is True
        assert path_res["hops"] == 1
        assert "--[HAS_FILE]-->" in path_res["path_string"]
