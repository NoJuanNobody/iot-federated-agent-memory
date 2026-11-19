"""Tests for World Labs Atlas v2 server endpoints, unified /api/omni/route slash router,
tincan-gen atlas/audio/slash CLI in PTY sandboxes, PTY secret scrubbing, and MCP tools.
"""

from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Tuple

from iot_federated_agent_memory.agent_space import (
    PTY_SCRUBBED_SECRET_KEYS,
    AgentSpaceManager,
    prepare_harness_sandbox_env,
)
from iot_federated_agent_memory.pty_sessions import PTYSessionManager
from iot_federated_agent_memory.tincan_mcp import (
    MCP_TOOLS_DEFINITIONS,
    TinCanMCPClient,
    handle_mcp_request,
)
import tests.test_tincan_ux_updates as ux_mod


_TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
_TINY_JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"


def _req(
    base_url: str,
    method: str,
    path: str,
    payload: Dict[str, Any] | None = None,
    headers: Dict[str, str] | None = None,
) -> Tuple[int, Dict[str, Any]]:
    url = f"{base_url}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    hdrs = {"Accept": "application/json"}
    if data is not None:
        hdrs["Content-Type"] = "application/json"
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")
        try:
            return err.code, json.loads(body)
        except Exception:
            return err.code, {"error": body}


def test_atlas_rest_endpoints_and_vfs_download(tmp_path, monkeypatch):
    srv = ux_mod.server
    temp_mgr = AgentSpaceManager(base_dir=str(tmp_path / "spaces"), ai_router=srv.router)
    monkeypatch.setattr(srv, "_space_manager", temp_mgr)
    monkeypatch.setattr(srv, "_get_space_manager", lambda: temp_mgr)

    # Seed an image file in user's .space for VFS asset upload test
    sp = temp_mgr.get_or_create_space("user", "atlas_peer")
    sp.write_file("/images/torii_ref.jpg", _TINY_JPEG, mime_type="image/jpeg", updated_by="atlas_peer")

    with ux_mod._live_server() as (host, port):
        base_url = f"http://{host}:{port}"

        # 1. GET /api/atlas/health
        st_health, health = _req(base_url, "GET", "/api/atlas/health")
        assert st_health == 200
        assert health["ok"] is True
        assert "key_configured" in health

        # 2a. POST /api/atlas/assets/upload via vfs_path
        st_up_vfs, up_vfs = _req(
            base_url,
            "POST",
            "/api/atlas/assets/upload",
            {
                "scope": "user",
                "owner_id": "atlas_peer",
                "vfs_path": "/images/torii_ref.jpg",
            },
        )
        assert st_up_vfs == 200, up_vfs
        assert up_vfs["ok"] is True
        assert str(up_vfs.get("asset_id") or up_vfs.get("id")).startswith("asset_")
        assert up_vfs["vfs_path"] == "/images/torii_ref.jpg"

        # 2b. POST /api/atlas/assets/upload via data_b64
        st_up_b64, up_b64 = _req(
            base_url,
            "POST",
            "/api/atlas/assets/upload",
            {
                "data_b64": base64.b64encode(_TINY_PNG).decode("ascii"),
                "mime_type": "image/png",
                "filename": "frame0.png",
            },
        )
        assert st_up_b64 == 200, up_b64
        assert up_b64["ok"] is True
        assert up_b64["filename"] == "frame0.png"
        assert up_b64["size_bytes"] == len(_TINY_PNG)

        # 3. POST /api/atlas/tasks/run across all 6 World Labs Atlas v2 tasks
        six_tasks = (
            "atlasTextToImage",
            "images2PosedRGBD",
            "atlasGenerate",
            "atlasChisel",
            "posedImages2Splats",
            "splats2Mesh",
        )
        last_op_id = ""
        for idx, tname in enumerate(six_tasks):
            idem = f"idem-test-{idx}-{tname}"
            st_run, run_data = _req(
                base_url,
                "POST",
                "/api/atlas/tasks/run",
                {
                    "task": tname,
                    "request_body": {"prompt": f"kyoto scene for {tname}", "views": 14},
                    "idempotency_key": idem,
                },
            )
            assert st_run == 200, run_data
            assert run_data["ok"] is True
            assert run_data["task"] == tname
            assert run_data["idempotency_key"] == idem
            op_id = run_data.get("operation_id") or run_data.get("id")
            assert op_id
            last_op_id = op_id

        # Invalid task returns 400
        st_bad, bad_data = _req(
            base_url,
            "POST",
            "/api/atlas/tasks/run",
            {"task": "notARealAtlasTask", "request_body": {}},
        )
        assert st_bad == 400
        assert bad_data["ok"] is False

        # 4. GET and POST /api/atlas/operations/status
        st_get_op, get_op = _req(
            base_url,
            "GET",
            f"/api/atlas/operations/status?operation_id={last_op_id}",
        )
        assert st_get_op == 200, get_op
        assert get_op["ok"] is True
        assert (get_op.get("operation_id") or get_op.get("id")) == last_op_id

        st_post_op, post_op = _req(
            base_url,
            "POST",
            "/api/atlas/operations/status",
            {"operation_id": last_op_id},
        )
        assert st_post_op == 200, post_op
        assert post_op["ok"] is True
        assert (post_op.get("operation_id") or post_op.get("id")) == last_op_id

        # 5. POST /api/atlas/operations/download into .space VFS
        st_dl, dl_data = _req(
            base_url,
            "POST",
            "/api/atlas/operations/download",
            {
                "operation_id": last_op_id,
                "scope": "user",
                "owner_id": "atlas_peer",
                "target_dir": "/worlds",
            },
        )
        assert st_dl == 200, dl_data
        assert dl_data["ok"] is True
        saved_files = dl_data.get("saved_files") or []
        assert len(saved_files) >= 2
        vfs_paths = {f["path"] for f in sp.list_files()}
        for sf in saved_files:
            assert sf in vfs_paths


def test_audio_generate_and_omni_slash_router_endpoints(tmp_path, monkeypatch):
    srv = ux_mod.server
    temp_mgr = AgentSpaceManager(base_dir=str(tmp_path / "spaces"), ai_router=srv.router)
    monkeypatch.setattr(srv, "_space_manager", temp_mgr)
    monkeypatch.setattr(srv, "_get_space_manager", lambda: temp_mgr)

    with ux_mod._live_server() as (host, port):
        base_url = f"http://{host}:{port}"

        # 1. POST /api/audio/generate (music, tts, sfx)
        for kind in ("music", "tts", "sfx"):
            st_aud, aud = _req(
                base_url,
                "POST",
                "/api/audio/generate",
                {
                    "prompt": f"aeonik {kind} cue",
                    "kind": kind,
                    "scope": "user",
                    "owner_id": "omni_peer",
                },
            )
            assert st_aud == 200, aud
            assert aud["ok"] is True
            assert aud["kind"] == kind
            assert aud["path"].startswith("/audio/")
            assert aud["path"].endswith(".wav")
            assert aud["sparkline"] == "│┃│┃┃│┃┃"
            assert aud["lufs"] == -14.0
            assert aud["saved_to_space"]["path"] == aud["path"]

        # 2. POST /api/omni/route for /atlas, /audio, /3d, /rodin, /rig, /image, /video, /text
        st_r_atlas, r_atlas = _req(
            base_url,
            "POST",
            "/api/omni/route",
            {
                "command": "/atlas splat --views 14 --res 1280x720 kyoto bamboo sanctuary",
                "scope": "user",
                "owner_id": "omni_peer",
            },
        )
        assert st_r_atlas == 200, r_atlas
        assert r_atlas["ok"] is True
        assert r_atlas["route"]["command"] == "atlas"
        assert r_atlas["route"]["atlas_task"] == "posedImages2Splats"
        assert len(r_atlas["saved_to_space"]["files"]) >= 2

        st_r_audio, r_audio = _req(
            base_url,
            "POST",
            "/api/omni/route",
            {
                "command": "/audio music --model google/lyria-3.5 rain on temple roof",
                "scope": "user",
                "owner_id": "omni_peer",
            },
        )
        assert st_r_audio == 200, r_audio
        assert r_audio["ok"] is True
        assert r_audio["route"]["command"] == "audio"
        assert r_audio["saved_to_space"]["path"].startswith("/audio/")

        # Multi-view Atlas Splat route with 4 uploaded photos
        tiny_jpg_b64 = base64.b64encode(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9").decode("ascii")
        st_multi, r_multi = _req(
            base_url,
            "POST",
            "/api/omni/route",
            {
                "command": "/atlas splat multi-view courtyard",
                "scope": "user",
                "owner_id": "omni_peer",
                "references": [
                    {"name": f"view_{i}.jpg", "type": "image", "mimeType": "image/jpeg", "base64": tiny_jpg_b64}
                    for i in range(4)
                ],
            },
        )
        assert st_multi == 200, r_multi
        assert r_multi["ok"] is True
        assert r_multi["result"]["input_frame_count"] == 4
        assert len(r_multi["result"]["uploaded_assets"]) == 4
        assert r_multi["result"].get("stage1_pose_operation_id")

        # Node Studio .nodes.json graph persistence (save -> list -> reopen from .space VFS)
        st_gsave, r_gsave = _req(
            base_url,
            "POST",
            "/api/nodes/graph",
            {
                "scope": "user",
                "owner_id": "omni_peer",
                "name": "courtyard_world",
                "graph": {
                    "nodes": [{"id": "omni-1", "label": "Courtyard Splat", "x": 120, "y": 140}],
                    "edges": [],
                    "references": [{"id": "r1", "name": "view_0.jpg", "type": "image"}],
                    "viewport": {"panX": 15, "panY": -10, "zoom": 1.1},
                },
            },
        )
        assert st_gsave == 200, r_gsave
        assert r_gsave["ok"] is True
        assert r_gsave["path"] == "/nodes/courtyard_world.nodes.json"
        assert r_gsave["node_count"] == 1

        st_glist, r_glist = _req(base_url, "GET", "/api/nodes/graphs?scope=user&owner_id=omni_peer")
        assert st_glist == 200, r_glist
        assert any(g["path"] == "/nodes/courtyard_world.nodes.json" for g in r_glist["graphs"])

        st_gload, r_gload = _req(
            base_url,
            "GET",
            "/api/nodes/graph?scope=user&owner_id=omni_peer&path=/nodes/courtyard_world.nodes.json",
        )
        assert st_gload == 200, r_gload
        assert r_gload["ok"] is True
        assert r_gload["graph"]["nodes"][0]["label"] == "Courtyard Splat"
        assert r_gload["graph"]["viewport"]["zoom"] == 1.1

        st_r_3d, r_3d = _req(
            base_url,
            "POST",
            "/api/omni/route",
            {
                "command": "/rodin --tier Regular bronze guardian lion",
                "scope": "user",
                "owner_id": "omni_peer",
            },
        )
        assert st_r_3d == 200, r_3d
        assert r_3d["ok"] is True
        assert r_3d["route"]["command"] == "3d"
        glb_path = r_3d["saved_to_space"]["path"]
        assert glb_path.startswith("/models3d/") and glb_path.endswith(".glb")

        st_r_rig, r_rig = _req(
            base_url,
            "POST",
            "/api/omni/route",
            {
                "command": f"/rig --engine local --anim walk {glb_path}",
                "scope": "user",
                "owner_id": "omni_peer",
            },
        )
        assert st_r_rig == 200, r_rig
        assert r_rig["ok"] is True
        assert r_rig["route"]["command"] == "rig"
        assert r_rig["saved_to_space"]["path"].endswith("_rigged.glb")

        for slash_cmd, expected_mod in (
            ("/text summarize spatial camera extrinsics", "text"),
            ("/image --res 4K celadon botanical studio", "image"),
            ("/video --fps 24 orbital crane shot", "video"),
        ):
            st_ns, r_ns = _req(
                base_url,
                "POST",
                "/api/omni/route",
                {
                    "command": slash_cmd,
                    "scope": "user",
                    "owner_id": "omni_peer",
                },
            )
            assert st_ns == 200, r_ns
            assert r_ns["ok"] is True
            assert r_ns["route"]["modality"] == expected_mod
            assert r_ns["saved_to_space"] is not None


def test_pty_scrubs_wlt_and_provider_api_keys_and_runs_tincan_gen_atlas(tmp_path, monkeypatch):
    srv = ux_mod.server
    temp_mgr = AgentSpaceManager(base_dir=str(tmp_path / "spaces"), ai_router=srv.router)
    pty_mgr = PTYSessionManager()
    monkeypatch.setattr(srv, "_space_manager", temp_mgr)
    monkeypatch.setattr(srv, "_get_space_manager", lambda: temp_mgr)
    monkeypatch.setattr(srv, "_pty_manager", pty_mgr)
    monkeypatch.setattr(srv, "_get_pty_manager", lambda: pty_mgr)

    # Set all sensitive keys in host environment and verify none leak to interactive user PTYs
    monkeypatch.setenv("WLT_API_KEY", "wlt-secret-never-leak")
    monkeypatch.setenv("WORLDLABS_API_KEY", "worldlabs-secret-never-leak")
    monkeypatch.setenv("HYPER3D_API_KEY", "hyper3d-secret-never-leak")
    monkeypatch.setenv("NANOGPT_API_KEY", "nanogpt-secret-never-leak")
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-secret-never-leak")

    scrubbed_env = prepare_harness_sandbox_env(
        str(tmp_path / "work"),
        str(tmp_path / "cache"),
        extra_env={"WLT_API_KEY": "attempt-inject", "WORLDLABS_API_KEY": "attempt-inject"},
        scrub_secrets=True,
    )
    for secret_key in PTY_SCRUBBED_SECRET_KEYS:
        assert secret_key not in scrubbed_env

    with ux_mod._live_server() as (host, port):
        base_url = f"http://{host}:{port}"
        st_start, start_data = _req(
            base_url,
            "POST",
            "/api/terminal/pty/start",
            {"harness": "bash", "scope": "user", "owner_id": "pty_atlas_user"},
        )
        assert st_start == 200, start_data
        sid = start_data["session_id"]
        sess = pty_mgr.get(sid)
        assert sess is not None

        for secret_key in ("WLT_API_KEY", "WORLDLABS_API_KEY", "HYPER3D_API_KEY", "NANOGPT_API_KEY", "OPENROUTER_API_KEY"):
            assert secret_key not in sess.env

        for fn in ("AGENTS.md", "CLAUDE.md", "GEMINI.md", ".tincan/SPACE_CONTEXT.md"):
            ctx_text = Path(sess.tmpdir, fn).read_text(encoding="utf-8")
            assert "tincan-gen atlas" in ctx_text
            assert "tincan-gen audio" in ctx_text
            assert "tincan-gen slash" in ctx_text

        cmd = (
            b"for k in WLT_API_KEY WORLDLABS_API_KEY HYPER3D_API_KEY NANOGPT_API_KEY OPENROUTER_API_KEY; do "
            b"if printenv $k >/dev/null 2>&1; then echo LEAKED_$k; fi; done; "
            b"echo NO_LEAKS_CHECK_DONE; "
            b"tincan-gen atlas splats 'kyoto shrine' && "
            b"tincan-gen audio music 'ambient bell' && "
            b"tincan-gen slash '/atlas pose torii gate' && "
            b"printf 'ATLAS_PTY_%s\\n' 'COMPLETE'\n"
        )
        sess.write(cmd)
        deadline = time.time() + 15.0
        collected = b""
        off = 0
        while time.time() < deadline:
            chunk, off, _ = sess.read_since(off, timeout=0.25)
            collected += chunk
            if b"ATLAS_PTY_COMPLETE" in collected:
                break

        out_str = collected.decode("utf-8", errors="replace")
        assert "NO_LEAKS_CHECK_DONE" in out_str
        for secret_key in ("WLT_API_KEY", "WORLDLABS_API_KEY", "HYPER3D_API_KEY", "NANOGPT_API_KEY", "OPENROUTER_API_KEY"):
            assert f"LEAKED_{secret_key}" not in out_str
            assert f"{secret_key.lower().split('_')[0]}-secret-never-leak" not in out_str
        assert "ATLAS_PTY_COMPLETE" in out_str

        sp = temp_mgr.get_or_create_space("user", "pty_atlas_user")
        paths = {f["path"] for f in sp.list_files()}
        assert any(p.startswith("/worlds/") and p.endswith(".spz") for p in paths)
        assert any(p.startswith("/audio/") and p.endswith(".wav") for p in paths)
        pty_mgr.close(sid)


def test_tincan_mcp_atlas_and_omni_slash_tools(tmp_path, monkeypatch):
    srv = ux_mod.server
    temp_mgr = AgentSpaceManager(base_dir=str(tmp_path / "spaces"), ai_router=srv.router)
    monkeypatch.setattr(srv, "_space_manager", temp_mgr)
    monkeypatch.setattr(srv, "_get_space_manager", lambda: temp_mgr)

    tool_names = {t["name"] for t in MCP_TOOLS_DEFINITIONS}
    for expected in (
        "tincan_atlas_run_task",
        "tincan_atlas_operation_status",
        "tincan_atlas_download",
        "tincan_omni_slash",
    ):
        assert expected in tool_names

    with ux_mod._live_server() as (host, port):
        client = TinCanMCPClient(
            relay_url=f"http://{host}:{port}",
            config_dir=str(tmp_path / "tincan_cfg"),
        )

        # 1. tincan_atlas_run_task via JSON-RPC handle_mcp_request
        r_run = handle_mcp_request(
            {
                "jsonrpc": "2.0",
                "id": 101,
                "method": "tools/call",
                "params": {
                    "name": "tincan_atlas_run_task",
                    "arguments": {
                        "task": "posedImages2Splats",
                        "prompt": "zen rock garden",
                        "idempotency_key": "mcp-idem-101",
                        "scope": "user",
                        "owner_id": "mcp_peer",
                    },
                },
            },
            client=client,
        )
        assert r_run is not None and not r_run["result"].get("isError")
        run_payload = json.loads(r_run["result"]["content"][0]["text"])
        assert run_payload["ok"] is True
        op_id = run_payload["operation_id"]

        # 2. tincan_atlas_operation_status
        r_status = handle_mcp_request(
            {
                "jsonrpc": "2.0",
                "id": 102,
                "method": "tools/call",
                "params": {
                    "name": "tincan_atlas_operation_status",
                    "arguments": {"operation_id": op_id},
                },
            },
            client=client,
        )
        assert r_status is not None and not r_status["result"].get("isError")
        status_payload = json.loads(r_status["result"]["content"][0]["text"])
        assert status_payload["ok"] is True

        # 3. tincan_atlas_download
        r_dl = handle_mcp_request(
            {
                "jsonrpc": "2.0",
                "id": 103,
                "method": "tools/call",
                "params": {
                    "name": "tincan_atlas_download",
                    "arguments": {
                        "operation_id": op_id,
                        "scope": "user",
                        "owner_id": "mcp_peer",
                    },
                },
            },
            client=client,
        )
        assert r_dl is not None and not r_dl["result"].get("isError")
        dl_payload = json.loads(r_dl["result"]["content"][0]["text"])
        assert dl_payload["ok"] is True
        assert len(dl_payload["saved_files"]) >= 2

        # 4. tincan_omni_slash
        r_slash = handle_mcp_request(
            {
                "jsonrpc": "2.0",
                "id": 104,
                "method": "tools/call",
                "params": {
                    "name": "tincan_omni_slash",
                    "arguments": {
                        "command": "/atlas flythrough --fps 24 bamboo forest path",
                        "scope": "user",
                        "owner_id": "mcp_peer",
                    },
                },
            },
            client=client,
        )
        assert r_slash is not None and not r_slash["result"].get("isError")
        slash_payload = json.loads(r_slash["result"]["content"][0]["text"])
        assert slash_payload["ok"] is True
        assert slash_payload["route"]["command"] == "atlas"
        assert slash_payload["route"]["atlas_task"] == "atlasGenerate"
