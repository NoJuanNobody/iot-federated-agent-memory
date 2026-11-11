"""
Unit and integration tests for Hyper3D Rodin Generative 3D,
Single-File .space SQLite VFS, Wasm Playground, ArtCraft 15 Apps Bridge,
CLI subparsers, MCP protocol tools, and HTTP Server Endpoints.
"""

import os
import sys

# Ensure this worktree has highest priority in sys.path
WORKTREE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKTREE_DIR in sys.path:
    sys.path.remove(WORKTREE_DIR)
sys.path.insert(0, WORKTREE_DIR)

PARENT_DIR = os.path.dirname(os.path.dirname(WORKTREE_DIR))
while PARENT_DIR in sys.path:
    sys.path.remove(PARENT_DIR)

# Evict any cached modules that might have been imported from parent
for mod in list(sys.modules.keys()):
    if mod.startswith("iot_federated_agent_memory") or mod == "server":
        del sys.modules[mod]

import base64
import json
import io
import os
import sys
import tempfile
import threading
import time
import urllib.request
import urllib.parse
from http.server import ThreadingHTTPServer

import pytest

from iot_federated_agent_memory import tincan_cli
from iot_federated_agent_memory.tincan_mcp import (
    MCP_TOOLS_DEFINITIONS,
    TinCanMCPClient,
    handle_mcp_request,
)
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI
import server


@pytest.fixture(scope="module")
def live_server():
    """Spins up a lightweight background HTTP server on an ephemeral port."""
    test_port = 18099
    httpd = ThreadingHTTPServer(("127.0.0.1", test_port), server.MeshGatewayHandler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    base_url = f"http://127.0.0.1:{test_port}"
    time.sleep(0.3)
    yield base_url
    httpd.shutdown()
    httpd.server_close()


def run_cli_capture(args: list[str]) -> tuple[int, str]:
    """Helper to execute tincan_cli.main and capture stdout."""
    old_stdout = sys.stdout
    buf = io.StringIO()
    sys.stdout = buf
    try:
        code = tincan_cli.main(args)
    finally:
        sys.stdout = old_stdout
    return code, buf.getvalue()


# -----------------------------------------------------------------------------
# 1. CLI Subparsers & Commands: tincan rodin, credits, space
# -----------------------------------------------------------------------------

def test_cli_rodin_generate():
    code, out = run_cli_capture(["rodin", "cyberpunk hovercar", "--tier", "Regular", "--format", "glb", "--json"])
    assert code == 0
    data = json.loads(out)
    assert data["prompt"] == "cyberpunk hovercar"
    assert data["tier"] == "Regular"
    assert data["format"] == "glb"
    assert "uuid" in data
    assert "glb_bytes_b64" in data
    assert data["status"] == "Done"


def test_cli_rodin_status():
    code, out = run_cli_capture(["rodin", "status", "sub-test999", "--json"])
    assert code == 0
    data = json.loads(out)
    assert data["subscription_key"] == "sub-test999"
    assert data["status"] == "Done"


def test_cli_rodin_balance():
    code, out = run_cli_capture(["rodin", "balance", "--json"])
    assert code == 0
    data = json.loads(out)
    assert "account_remaining_credits" in data
    assert "tier_pricing_usd" in data
    assert data["tier_pricing_usd"]["Regular"] == 0.50
    assert data["tier_pricing_usd"]["Sketch"] == 0.25


def test_cli_credits_dashboard():
    # Test JSON output
    code, out = run_cli_capture(["credits", "--json"])
    assert code == 0
    data = json.loads(out)
    assert "hyper3d" in data
    assert "tier_pricing_usd" in data["hyper3d"]

    # Test formatted text output
    code, text_out = run_cli_capture(["credits"])
    assert code == 0
    assert "=== 🧊 Hyper3D Rodin (Ronin) 3D Credit Pool ===" in text_out
    assert "Tier Pricing:" in text_out
    assert "Regular" in text_out


def test_cli_space_lifecycle(tmp_path):
    test_user = "cli-test-peer"

    # Write file
    code, out = run_cli_capture(["space", "write", "/src/calc.py", "print(10 + 32)", "--user", test_user, "--json"])
    assert code == 0
    data = json.loads(out)
    assert data["path"] == "/src/calc.py"
    assert data["size_bytes"] > 0

    # Read file
    code, out = run_cli_capture(["space", "read", "/src/calc.py", "--user", test_user, "--json"])
    assert code == 0
    data = json.loads(out)
    assert data["content"] == "print(10 + 32)"

    # Run playground
    code, out = run_cli_capture(["space", "run", "/src/calc.py", "--user", test_user, "--json"])
    assert code == 0
    data = json.loads(out)
    assert data["exit_code"] == 0
    assert "42" in data["stdout"]
    assert data["wasm_bridge"] is True

    # List files
    code, out = run_cli_capture(["space", "ls", "--user", test_user, "--json"])
    assert code == 0
    summary = json.loads(out)
    assert summary["file_count"] >= 1
    assert "merkle_root" in summary
    assert any(f["path"] == "/src/calc.py" for f in summary["files"])

    # Agent turn
    code, out = run_cli_capture(["space", "agent", "Write unit test", "--user", test_user, "--json"])
    assert code == 0
    agent_turn = json.loads(out)
    assert "turn_id" in agent_turn
    assert "reply" in agent_turn

    # Wasm manifest
    code, out = run_cli_capture(["space", "wasm", "--json"])
    assert code == 0
    manifest = json.loads(out)
    assert len(manifest["artcraft_apps"]) == 15
    assert any(a["id"] == "cadcraft" for a in manifest["artcraft_apps"])
    assert any(a["id"] == "vectorcraft" for a in manifest["artcraft_apps"])
    assert len(manifest["wasm_runtimes"]) >= 4

    # Export space
    exp_file = str(tmp_path / "exported.space")
    code, out = run_cli_capture(["space", "export", exp_file, "--user", test_user, "--json"])
    assert code == 0
    assert os.path.exists(exp_file)
    assert os.path.getsize(exp_file) > 0


# -----------------------------------------------------------------------------
# 2. MCP Protocol Server Tool Definitions & Handlers
# -----------------------------------------------------------------------------

def test_mcp_tool_definitions():
    tool_names = [t["name"] for t in MCP_TOOLS_DEFINITIONS]
    assert "tincan_rodin_generate" in tool_names
    assert "tincan_space_ls" in tool_names
    assert "tincan_space_write" in tool_names
    assert "tincan_space_exec" in tool_names
    assert "tincan_space_agent" in tool_names


def test_mcp_rpc_dispatch():
    # Test tools/list
    res = handle_mcp_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert res is not None
    tools = res["result"]["tools"]
    assert any(t["name"] == "tincan_rodin_generate" for t in tools)

    # Test tools/call tincan_space_write
    write_req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "tincan_space_write",
            "arguments": {
                "path": "/src/mcp_test.py",
                "content": "val = 99",
                "scope": "user",
                "owner_id": "mcp-user",
            },
        },
    }
    write_res = handle_mcp_request(write_req)
    assert write_res is not None
    assert "result" in write_res
    write_data = json.loads(write_res["result"]["content"][0]["text"])
    assert write_data["path"] == "/src/mcp_test.py"

    # Test tools/call tincan_space_ls
    ls_req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "tincan_space_ls",
            "arguments": {"scope": "user", "owner_id": "mcp-user"},
        },
    }
    ls_res = handle_mcp_request(ls_req)
    ls_data = json.loads(ls_res["result"]["content"][0]["text"])
    assert any(f["path"] == "/src/mcp_test.py" for f in ls_data["files"])

    # Test tools/call tincan_rodin_generate
    rodin_req = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "tincan_rodin_generate",
            "arguments": {"prompt": "sci-fi drone", "tier": "Regular"},
        },
    }
    rodin_res = handle_mcp_request(rodin_req)
    rodin_data = json.loads(rodin_res["result"]["content"][0]["text"])
    assert "uuid" in rodin_data
    assert rodin_data["status"] == "Done"


# -----------------------------------------------------------------------------
# 3. MeshOS Wasm UI Artifact Verification
# -----------------------------------------------------------------------------

def test_mesh_os_ui_elements():
    # Window and Dock buttons
    assert 'id="win-agentspace"' in MESH_OS_HTML_UI
    assert 'id="dockBtn-win-agentspace"' in MESH_OS_HTML_UI
    assert "AgentSpace &amp; Wasm Studio.app" in MESH_OS_HTML_UI
    # Rodin 3D Generator elements
    assert "Hyper3D Rodin 3D" in MESH_OS_HTML_UI
    assert 'id="generateRodinBtn"' in MESH_OS_HTML_UI
    assert "Hyper3D Rodin (Ronin) 3D Generative Credit Pool" in MESH_OS_HTML_UI
    # ArtCraft 15 Wasm Applications
    assert "cadcraft" in MESH_OS_HTML_UI
    assert "vectorcraft" in MESH_OS_HTML_UI
    assert "deckcraft" in MESH_OS_HTML_UI
    assert "designcraft" in MESH_OS_HTML_UI
    assert "?host=parent" in MESH_OS_HTML_UI
    # PostMessage bridge event listener
    assert ':ready' in MESH_OS_HTML_UI
    assert ':save' in MESH_OS_HTML_UI
    assert ':dirty' in MESH_OS_HTML_UI


# -----------------------------------------------------------------------------
# 4. HTTP Server Endpoints Verification
# -----------------------------------------------------------------------------

def http_post(url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5.0) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=5.0) as resp:
        return json.loads(resp.read().decode("utf-8"))


def test_http_3d_routes(live_server):
    # GET /api/3d/balance
    balance = http_get(f"{live_server}/api/3d/balance")
    assert "account_remaining_credits" in balance
    assert "tier_pricing_usd" in balance

    # POST /api/3d/generate
    gen = http_post(f"{live_server}/api/3d/generate", {
        "prompt": "hypercar concept",
        "tier": "Regular",
        "format": "glb",
        "scope": "user",
        "owner_id": "http-tester",
        "save_path": "/models3d/hypercar.glb",
    })
    assert gen["status"] == "Done"
    assert "saved_to_space" in gen
    assert gen["saved_to_space"]["path"] == "/models3d/hypercar.glb"

    # POST /api/3d/status
    st = http_post(f"{live_server}/api/3d/status", {"subscription_key": gen["subscription_key"]})
    assert st["status"] == "Done"

    # POST /api/3d/download
    dl = http_post(f"{live_server}/api/3d/download", {"task_uuid": gen["uuid"]})
    assert dl["task_uuid"] == gen["uuid"]
    assert "glb_bytes_b64" in dl


def test_http_space_routes(live_server):
    owner = "http-tester"

    # POST /api/space/file (write)
    wr = http_post(f"{live_server}/api/space/file", {
        "scope": "user",
        "owner_id": owner,
        "path": "/src/math.py",
        "content": "def add(a, b): return a + b\nprint(add(20, 22))",
        "action": "write",
    })
    assert wr["path"] == "/src/math.py"

    # GET /api/space/file
    rf = http_get(f"{live_server}/api/space/file?scope=user&owner_id={owner}&path=/src/math.py")
    assert "add(20, 22)" in rf["content"]

    # POST /api/space/exec
    ex = http_post(f"{live_server}/api/space/exec", {
        "scope": "user",
        "owner_id": owner,
        "entrypoint": "/src/math.py",
        "runtime": "python",
    })
    assert ex["exit_code"] == 0
    assert "42" in ex["stdout"]

    # POST /api/space/agent
    ag = http_post(f"{live_server}/api/space/agent", {
        "scope": "user",
        "owner_id": owner,
        "prompt": "Review math module",
        "model_alias": "gemini-brain",
    })
    assert "turn_id" in ag
    assert "reply" in ag

    # GET /api/space/ls
    ls = http_get(f"{live_server}/api/space/ls?scope=user&owner_id={owner}")
    assert any(f["path"] == "/src/math.py" for f in ls["files"])
    assert any(f["path"] == "/models3d/hypercar.glb" for f in ls["files"])

    # GET /api/wasm/manifest
    wm = http_get(f"{live_server}/api/wasm/manifest")
    assert len(wm["artcraft_apps"]) == 15
    assert len(wm["wasm_runtimes"]) >= 4
    assert wm["contract"]["protocol"] == "artcraft-wasm-bridge-v1"

    # GET /api/space/export
    exp = http_get(f"{live_server}/api/space/export?scope=user&owner_id={owner}")
    assert exp["filename"] == f"{owner}.space"
    assert "space_b64" in exp
    raw_space = base64.b64decode(exp["space_b64"])
    assert len(raw_space) > 0
