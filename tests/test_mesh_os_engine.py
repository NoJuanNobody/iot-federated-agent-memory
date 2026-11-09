"""Unit tests for TinCanMeshOSEngine."""

import threading
import time
import pytest

from iot_federated_agent_memory.mesh_os_engine import QUEST_CATALOG, TinCanMeshOSEngine


def test_tier_progression_and_themes():
    """Verify tier progression L1 -> L5, next_tier_xp, unlocked themes, and progress percentage."""
    engine = TinCanMeshOSEngine(seed=False)

    # L1: 0..199
    l1_zero = engine.get_tier_info(0)
    assert l1_zero["tier_code"] == "L1"
    assert l1_zero["tier_name"] == "L1: Isolated Node"
    assert l1_zero["next_tier_xp"] == 200
    assert l1_zero["unlocked_themes"] == ["slate"]
    assert l1_zero["progress_pct"] == 0.0

    l1_mid = engine.get_tier_info(100)
    assert l1_mid["tier_code"] == "L1"
    assert l1_mid["progress_pct"] == 50.0

    l1_edge = engine.get_tier_info(199)
    assert l1_edge["tier_code"] == "L1"
    assert l1_edge["progress_pct"] == 99.5

    # L2: 200..499
    l2_start = engine.get_tier_info(200)
    assert l2_start["tier_code"] == "L2"
    assert l2_start["tier_name"] == "L2: Local Shared Workspace"
    assert l2_start["next_tier_xp"] == 500
    assert l2_start["unlocked_themes"] == ["slate", "amber-crt"]
    assert l2_start["progress_pct"] == 0.0

    l2_mid = engine.get_tier_info(350)
    assert l2_mid["tier_code"] == "L2"
    assert l2_mid["progress_pct"] == 50.0

    # L3: 500..999
    l3_start = engine.get_tier_info(500)
    assert l3_start["tier_code"] == "L3"
    assert l3_start["tier_name"] == "L3: Cryptographic Multi-Account Bridge"
    assert l3_start["next_tier_xp"] == 1000
    assert l3_start["unlocked_themes"] == ["slate", "amber-crt", "crypto-emerald"]
    assert l3_start["progress_pct"] == 0.0

    l3_seed = engine.get_tier_info(550)
    assert l3_seed["tier_code"] == "L3"
    assert l3_seed["progress_pct"] == 10.0

    # L4: 1000..1999
    l4_start = engine.get_tier_info(1000)
    assert l4_start["tier_code"] == "L4"
    assert l4_start["tier_name"] == "L4: CRDT Gossip & Real-Time WebRTC Mesh"
    assert l4_start["next_tier_xp"] == 2000
    assert l4_start["unlocked_themes"] == [
        "slate",
        "amber-crt",
        "crypto-emerald",
        "webrtc-cyan",
    ]
    assert l4_start["progress_pct"] == 0.0

    l4_mid = engine.get_tier_info(1500)
    assert l4_mid["tier_code"] == "L4"
    assert l4_mid["progress_pct"] == 50.0

    # L5: >=2000
    l5_start = engine.get_tier_info(2000)
    assert l5_start["tier_code"] == "L5"
    assert l5_start["tier_name"] == "L5: Autonomous Cognitive Mesh"
    assert l5_start["next_tier_xp"] == 2000
    assert l5_start["unlocked_themes"] == [
        "slate",
        "amber-crt",
        "crypto-emerald",
        "webrtc-cyan",
        "messiah-gold",
    ]
    assert l5_start["progress_pct"] == 100.0

    l5_super = engine.get_tier_info(4500)
    assert l5_super["tier_code"] == "L5"
    assert l5_super["progress_pct"] == 100.0


def test_seeded_vs_unseeded_initial_state():
    """Verify seeded state starts with 550 XP, 2 peers, 2 flights, and unseeded is clean."""
    seeded = TinCanMeshOSEngine(seed=True)
    assert seeded.total_xp == 550
    assert len(seeded.peers) == 2
    assert "peer-primary-mac" in seeded.peers
    assert "peer-secondary-node" in seeded.peers
    assert seeded.peers["peer-primary-mac"]["xp"] == 350
    assert seeded.peers["peer-primary-mac"]["display_name"] == "Mac Studio (M1 Max)"
    assert seeded.peers["peer-secondary-node"]["xp"] == 200
    assert seeded.peers["peer-secondary-node"]["display_name"] == "Collaborator MacBook"
    assert len(seeded.flights) == 2
    assert seeded.get_tier_info()["tier_code"] == "L3"

    clean = TinCanMeshOSEngine(seed=False)
    assert clean.total_xp == 0
    assert len(clean.peers) == 0
    assert len(clean.flights) == 0
    assert clean.get_tier_info()["tier_code"] == "L1"


def test_quest_catalog_coverage():
    """Ensure all 7 required quest keys are present in QUEST_CATALOG with proper attributes."""
    expected_quests = [
        "workstation_handshake",
        "sealed_courier",
        "inbox_decryption",
        "brain_arena_match",
        "curator_drop",
        "coop_hitl_trigger",
        "watchparty_reaction",
    ]
    for key in expected_quests:
        assert key in QUEST_CATALOG
        q = QUEST_CATALOG[key]
        assert "title" in q
        assert "badge" in q
        assert "xp" in q and q["xp"] > 0
        assert "description" in q


def test_award_xp_and_quest_completion():
    """Verify award_xp updates total XP, peer stats, badges, and quest completions."""
    engine = TinCanMeshOSEngine(seed=False)

    # 1. Award handshake (50 XP)
    res1 = engine.award_xp(
        peer_id="node-alpha",
        action_key="workstation_handshake",
        display_name="Alpha Node",
    )
    assert res1["awarded_xp"] == 50
    assert res1["total_xp"] == 50
    assert res1["peer"]["peer_id"] == "node-alpha"
    assert res1["peer"]["display_name"] == "Alpha Node"
    assert res1["peer"]["xp"] == 50
    assert "🟢 Mesh Initiate" in res1["peer"]["badges"]
    assert res1["tier"]["tier_code"] == "L1"

    # Verify quest completion
    quest_handshake = engine.quests["workstation_handshake"]
    assert quest_handshake["completions"] == 1
    assert "node-alpha" in quest_handshake["completed_by"]

    # 2. Award sealed courier (100 XP)
    res2 = engine.award_xp(
        peer_id="node-alpha",
        action_key="sealed_courier",
        metadata={"tokens_routed": 256},
    )
    assert res2["awarded_xp"] == 100
    assert res2["total_xp"] == 150
    assert res2["peer"]["envelopes_sealed"] == 1
    assert res2["peer"]["tokens_routed"] == 256
    assert "🥫 Cipher Postmaster" in res2["peer"]["badges"]

    # 3. Award custom XP
    res3 = engine.award_xp(
        peer_id="node-beta",
        action_key="custom_action",
        custom_xp=400,
        display_name="Beta Node",
    )
    assert res3["awarded_xp"] == 400
    assert res3["total_xp"] == 550  # 150 + 400 = 550 (L3!)
    assert res3["tier"]["tier_code"] == "L3"
    assert res3["peer"]["xp"] == 400


def test_cursor_presence_and_filtering():
    """Verify cursor updates and room-specific filtering."""
    engine = TinCanMeshOSEngine(seed=False)

    c1 = engine.update_cursor(
        peer_id="peer-1",
        x=45.2,
        y=88.7,
        window_id="code",
        display_name="Peer 1",
        room="main",
    )
    assert c1["peer_id"] == "peer-1"
    assert c1["x"] == 45.2
    assert c1["y"] == 88.7

    c2 = engine.update_cursor(
        peer_id="peer-2",
        x=12.0,
        y=99.0,
        room="sandbox",
        display_name="Peer 2",
    )
    assert c2["room"] == "sandbox"

    state_main = engine.get_state(room="main")
    main_cursor_ids = [c["peer_id"] for c in state_main["cursors"]]
    assert "peer-1" in main_cursor_ids
    assert "peer-2" not in main_cursor_ids

    state_sandbox = engine.get_state(room="sandbox")
    sandbox_cursor_ids = [c["peer_id"] for c in state_sandbox["cursors"]]
    assert "peer-2" in sandbox_cursor_ids
    assert "peer-1" not in sandbox_cursor_ids


def test_record_flight_ring_buffer_capping():
    """Verify packet flight ring buffer caps at 30 entries."""
    engine = TinCanMeshOSEngine(seed=False)
    for i in range(40):
        engine.record_flight(
            from_node=f"node-{i}",
            to_node="hub",
            kind="envelope",
            label="X25519",
            byte_size=100 + i,
        )

    assert len(engine.flights) == 30
    assert engine.flights[0]["from_node"] == "node-10"
    assert engine.flights[-1]["from_node"] == "node-39"


def test_sync_watch_party():
    """Verify watch party playback synchronization."""
    engine = TinCanMeshOSEngine(seed=False)
    sync_res = engine.sync_watch_party(
        peer_id="peer-host",
        video_idx=3,
        is_playing=True,
        current_time=124.8,
    )
    assert sync_res["peer_id"] == "peer-host"
    assert sync_res["video_idx"] == 3
    assert sync_res["is_playing"] is True
    assert sync_res["current_time"] == 124.8

    state = engine.get_state()
    assert state["watch_party"]["video_idx"] == 3
    assert state["watch_party"]["is_playing"] is True


def test_add_reaction_ring_buffer_and_xp():
    """Verify watch party reactions award XP and buffer caps at 25."""
    engine = TinCanMeshOSEngine(seed=False)

    for i in range(30):
        rx = engine.add_reaction(
            peer_id="peer-fan",
            emoji="🔥",
            display_name="Fan Node",
        )
        assert rx["emoji"] == "🔥"

    assert len(engine.reactions) == 25
    peer = engine.peers["peer-fan"]
    assert peer["reactions_sent"] == 30
    # 30 * 15 XP = 450 XP
    assert peer["xp"] == 450
    assert "🔥 Vibe Synchronizer" in peer["badges"]


def test_vote_arena():
    """Verify AI arena voting increments votes, awards XP, and records flight."""
    engine = TinCanMeshOSEngine(seed=False)

    vote1 = engine.vote_arena(
        peer_id="peer-judge",
        winner_alias="claude-3-7-sonnet",
        prompt_preview="CRDT merge protocol",
        display_name="Judge Peer",
    )
    assert vote1["winner_alias"] == "claude-3-7-sonnet"
    assert vote1["votes"] == 1
    assert vote1["xp_awarded"] == 150
    assert vote1["flight"]["kind"] == "arena_vote"
    assert vote1["flight"]["to_node"] == "claude-3-7-sonnet"

    vote2 = engine.vote_arena(
        peer_id="peer-judge",
        winner_alias="claude-3-7-sonnet",
    )
    assert vote2["votes"] == 2
    assert engine.arena_votes["claude-3-7-sonnet"] == 2

    peer = engine.peers["peer-judge"]
    assert peer["votes_cast"] == 2
    assert peer["xp"] == 300
    assert "🧠 Synapse Arbiter" in peer["badges"]


def test_leaderboard_ordering():
    """Verify leaderboard sorts peers descending by XP."""
    engine = TinCanMeshOSEngine(seed=False)
    engine.award_xp("peer-low", "workstation_handshake", custom_xp=50)
    engine.award_xp("peer-high", "workstation_handshake", custom_xp=800)
    engine.award_xp("peer-mid", "workstation_handshake", custom_xp=300)

    board = engine.get_leaderboard()
    assert len(board) == 3
    assert [p["peer_id"] for p in board] == ["peer-high", "peer-mid", "peer-low"]
    assert [p["xp"] for p in board] == [800, 300, 50]
    assert board[0]["xp"] == 800
    assert board[1]["xp"] == 300
    assert board[2]["xp"] == 50


def test_get_state_structure():
    """Verify get_state returns all required keys and correct data types."""
    engine = TinCanMeshOSEngine(seed=True)
    state = engine.get_state(room="main")

    required_keys = [
        "xp",
        "tier",
        "quests",
        "leaderboard",
        "cursors",
        "watch_party",
        "flights",
        "arena_votes",
        "room",
        "timestamp",
    ]
    for key in required_keys:
        assert key in state

    assert isinstance(state["xp"], int)
    assert isinstance(state["tier"], dict)
    assert isinstance(state["quests"], list)
    assert isinstance(state["leaderboard"], list)
    assert isinstance(state["cursors"], list)
    assert isinstance(state["watch_party"], dict)
    assert isinstance(state["flights"], list)
    assert isinstance(state["arena_votes"], dict)
    assert state["room"] == "main"
    assert isinstance(state["timestamp"], float)


def test_thread_safety_concurrent_access():
    """Stress test multi-threaded XP awards, cursor updates, and state reads."""
    engine = TinCanMeshOSEngine(seed=False)
    threads = []
    num_threads = 8
    iterations_per_thread = 25

    def worker(tid: int):
        for i in range(iterations_per_thread):
            engine.award_xp(
                peer_id=f"worker-{tid}",
                action_key="workstation_handshake",
                custom_xp=10,
            )
            engine.update_cursor(
                peer_id=f"worker-{tid}",
                x=float(tid * 10),
                y=float(i),
            )
            engine.record_flight(
                from_node=f"worker-{tid}",
                to_node="hub",
                kind="telemetry",
            )
            _ = engine.get_state()

    for tid in range(num_threads):
        t = threading.Thread(target=worker, args=(tid,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    expected_total_xp = num_threads * iterations_per_thread * 10
    assert engine.total_xp == expected_total_xp
    assert len(engine.peers) == num_threads
    assert len(engine.flights) == 30  # capped at 30
