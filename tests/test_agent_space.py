"""Comprehensive tests for Single-File Space VFS (*.space), Wasm Runner, and Agent Space Harness."""

import json
import os
import struct
import tempfile
import pytest

from iot_federated_agent_memory.agent_space import (
    ARTCRAFT_WASM_APPS,
    AgentSpaceHarness,
    AgentSpaceManager,
    SingleFileSpaceVFS,
    WasmAndCodePlaygroundRunner,
    generate_minimal_glb_bytes,
)


@pytest.fixture
def temp_spaces_dir():
    with tempfile.TemporaryDirectory(prefix="test_spaces_") as tmpdir:
        yield tmpdir


def test_single_file_space_creation_user_and_topic(temp_spaces_dir):
    manager = AgentSpaceManager(base_dir=temp_spaces_dir)

    # 1. User space
    user_vfs = manager.get_space(scope="user", owner_id="alice")
    expected_user_path = os.path.join(temp_spaces_dir, "spaces", "users", "alice.space")
    assert user_vfs.space_path == expected_user_path
    assert os.path.isfile(expected_user_path)

    # Verify SQLite header
    with open(expected_user_path, "rb") as f:
        header = f.read(16)
    assert header.startswith(b"SQLite format 3\x00")

    # 2. Topic space
    topic_vfs = manager.get_space(scope="topic", owner_id="topic-mesh-42", title="Mesh Optimization", description="Topic space discussion")
    expected_topic_path = os.path.join(temp_spaces_dir, "spaces", "topics", "topic-mesh-42.space")
    assert topic_vfs.space_path == expected_topic_path
    assert os.path.isfile(expected_topic_path)

    # 3. Verify starter files seeded
    starter_files = [f["path"] for f in user_vfs.list_files()]
    assert "/README.md" in starter_files
    assert "/src/main.py" in starter_files
    assert "/src/app.js" in starter_files
    assert "/artcraft/drawing.dxf" in starter_files
    assert "/models3d/README.txt" in starter_files

    # Check DXF starter file
    dxf_rec = user_vfs.read_file("/artcraft/drawing.dxf")
    assert "SECTION" in dxf_rec["content"]
    assert "ENTITIES" in dxf_rec["content"]
    assert "EOF" in dxf_rec["content"]


def test_file_crud_and_patching(temp_spaces_dir):
    vfs = SingleFileSpaceVFS(scope="user", owner_id="tester", base_dir=temp_spaces_dir)

    # Write text file
    write_rec = vfs.write_file("/docs/spec.md", "# Specification\nTarget: alpha\n", mime_type="text/markdown", updated_by="developer")
    assert write_rec["path"] == "/docs/spec.md"
    assert write_rec["size_bytes"] > 0
    assert write_rec["mime_type"] == "text/markdown"

    # Read text file
    read_rec = vfs.read_file("/docs/spec.md", as_text=True)
    assert "Target: alpha" in read_rec["content"]
    assert read_rec["content_b64"] is not None

    # Patch file
    patched = vfs.patch_file("/docs/spec.md", target="alpha", replacement="beta", updated_by="agent")
    read_patched = vfs.read_file("/docs/spec.md", as_text=True)
    assert "Target: beta" in read_patched["content"]
    assert "Target: alpha" not in read_patched["content"]

    # Write binary file
    binary_payload = b"\x00\x01\x02\xff\xfe\xfd"
    vfs.write_file("/data/binary.dat", binary_payload, updated_by="sensor")
    bin_rec = vfs.read_file("/data/binary.dat", as_text=False)
    assert bin_rec["size_bytes"] == len(binary_payload)
    assert bin_rec["content"] is None  # as_text=False

    # List files with prefix
    docs_files = vfs.list_files(prefix="/docs")
    assert len(docs_files) == 1
    assert docs_files[0]["path"] == "/docs/spec.md"

    # Delete file
    del_res = vfs.delete_file("/docs/spec.md")
    assert del_res["deleted"] is True
    with pytest.raises(FileNotFoundError):
        vfs.read_file("/docs/spec.md")


def test_merkle_root_and_snapshots(temp_spaces_dir):
    vfs = SingleFileSpaceVFS(scope="user", owner_id="merkle_test", base_dir=temp_spaces_dir)
    m1 = vfs.compute_merkle_root()
    assert isinstance(m1, str)
    assert len(m1) == 64

    # Snapshot 1
    snap1 = vfs.create_snapshot(label="initial")
    assert snap1["merkle_root"] == m1
    assert len(snap1["manifest"]) > 0

    # Modify filesystem
    vfs.write_file("/notes/log.txt", "Entry 1\n")
    m2 = vfs.compute_merkle_root()
    assert m1 != m2

    # Snapshot 2
    snap2 = vfs.create_snapshot(label="after_log")
    assert snap2["merkle_root"] == m2

    snapshots = vfs.list_snapshots()
    assert len(snapshots) == 2
    assert snapshots[0]["label"] == "after_log"
    assert snapshots[1]["label"] == "initial"


def test_export_and_import_space_bytes(temp_spaces_dir):
    manager = AgentSpaceManager(base_dir=temp_spaces_dir)
    vfs_src = manager.get_space(scope="user", owner_id="source_user")
    vfs_src.write_file("/custom.json", json.dumps({"key": "value"}))

    space_bytes = vfs_src.export_space_bytes()
    assert isinstance(space_bytes, bytes)
    assert space_bytes.startswith(b"SQLite format 3\x00")

    # Import into target space
    vfs_dst = manager.get_space(scope="user", owner_id="dest_user")
    import_res = vfs_dst.import_space_bytes(space_bytes)
    assert import_res["imported"] is True

    # Verify custom.json is now in target space
    dst_rec = vfs_dst.read_file("/custom.json", as_text=True)
    assert json.loads(dst_rec["content"]) == {"key": "value"}

    # Test error handling on bad SQLite header
    with pytest.raises(ValueError, match="Invalid SQLite space file header"):
        vfs_dst.import_space_bytes(b"bad_header_bytes_1234567")


def test_playground_runner_python_sync_files(temp_spaces_dir):
    vfs = SingleFileSpaceVFS(scope="topic", owner_id="compute_topic", base_dir=temp_spaces_dir)
    runner = WasmAndCodePlaygroundRunner()

    py_script = (
        'import json, os\n'
        'print("[Runner Test] Executing Python calculation...")\n'
        'data = {"result": 42 * 2, "status": "calculated"}\n'
        'os.makedirs("output", exist_ok=True)\n'
        'with open("output/result.json", "w") as fp:\n'
        '    json.dump(data, fp)\n'
        'print("[Runner Test] File written: output/result.json")\n'
    )

    res = runner.execute(
        vfs=vfs,
        entrypoint="/src/compute.py",
        runtime="python",
        code_override=py_script,
    )

    assert res["exit_code"] == 0
    assert "[Runner Test]" in res["stdout"]
    assert "/output/result.json" in res["synced_files"]

    # Verify output file was automatically persisted into SQLite VFS
    out_rec = vfs.read_file("/output/result.json", as_text=True)
    parsed = json.loads(out_rec["content"])
    assert parsed["result"] == 84
    assert parsed["status"] == "calculated"

    # Verify execution was recorded in exec_runs table
    runs = vfs.list_exec_runs(limit=10)
    assert len(runs) >= 1
    assert runs[0]["entrypoint"] == "/src/compute.py"
    assert runs[0]["exit_code"] == 0


def test_playground_runner_artcraft_wasm_bridge(temp_spaces_dir):
    vfs = SingleFileSpaceVFS(scope="user", owner_id="cad_user", base_dir=temp_spaces_dir)
    runner = WasmAndCodePlaygroundRunner()

    # The starter drawing.dxf has already been seeded
    run_res = runner.execute(vfs=vfs, entrypoint="/artcraft/drawing.dxf", runtime="artcraft-wasm")
    assert run_res["exit_code"] == 0
    assert run_res["wasm_host_bridge"] is not None

    bridge = run_res["wasm_host_bridge"]
    assert bridge["app"] == "cadcraft"
    assert bridge["wasm_url"] == "/wasm/cadcraft/index.html?host=parent"
    assert bridge["open_message"]["type"] == "cadcraft:open"
    assert bridge["open_message"]["name"] == "drawing.dxf"
    assert bridge["open_message"]["bytes_b64"] is not None
    assert bridge["save_message_type"] == "cadcraft:save"
    assert bridge["ready_message_type"] == "cadcraft:ready"
    assert bridge["dirty_message_type"] == "cadcraft:dirty"
    assert bridge["coordinate_system"]["direction"] == "y-up"


def test_agent_space_harness_3d_rodin_and_artcraft(temp_spaces_dir):
    vfs = SingleFileSpaceVFS(scope="user", owner_id="creator_agent", base_dir=temp_spaces_dir)
    harness = AgentSpaceHarness(vfs=vfs)

    prompt = (
        "Generate a 3D robot mesh and stage a cadcraft dxf floorplan layout, "
        "then simulate a python physics calculation."
    )

    result = harness.run_agent(prompt=prompt, author="agent_test")
    assert result["turn_id"].startswith("turn_")
    assert len(result["rodin_assets"]) >= 1
    assert len(result["wasm_bridges"]) >= 1
    assert len(result["exec_results"]) >= 1

    # Check 3D mesh
    rodin_path = result["rodin_assets"][0]["path"]
    assert rodin_path.startswith("/models3d/")
    assert rodin_path.endswith(".glb")

    glb_rec = vfs.read_file(rodin_path, as_text=False)
    raw_glb = vfs.export_space_bytes()  # Just ensure space is consistent
    # Inspect raw GLB bytes
    import base64
    glb_bytes = base64.b64decode(glb_rec["content_b64"])
    assert glb_bytes[:4] == b"glTF"
    version = struct.unpack("<I", glb_bytes[4:8])[0]
    assert version == 2

    # Check agent turns logged
    turns = vfs.list_agent_turns()
    assert len(turns) >= 1
    assert turns[0]["prompt"] == prompt


def test_fork_file_and_fork_space(temp_spaces_dir):
    manager = AgentSpaceManager(base_dir=temp_spaces_dir)

    # 1. Fork file from topic to user
    topic_vfs = manager.get_space(scope="topic", owner_id="topic_alpha")
    topic_vfs.write_file("/shared/notes.txt", "Topic knowledge base entry")

    fork_file_res = manager.fork_file(
        from_scope="topic",
        from_id="topic_alpha",
        to_scope="user",
        to_id="user_charlie",
        path="/shared/notes.txt",
    )
    assert fork_file_res["forked"] is True

    user_vfs = manager.get_space(scope="user", owner_id="user_charlie")
    user_rec = user_vfs.read_file("/shared/notes.txt", as_text=True)
    assert user_rec["content"] == "Topic knowledge base entry"

    # 2. Fork whole space
    fork_space_res = manager.fork_space(
        from_scope="topic",
        from_id="topic_alpha",
        to_scope="user",
        to_id="user_charlie_full",
    )
    assert fork_space_res["scope"] == "user"
    assert fork_space_res["owner_id"] == "user_charlie_full"

    full_user_vfs = manager.get_space(scope="user", owner_id="user_charlie_full")
    assert full_user_vfs.read_file("/shared/notes.txt")["content"] == "Topic knowledge base entry"


def test_wasm_manifest_and_apps(temp_spaces_dir):
    manager = AgentSpaceManager(base_dir=temp_spaces_dir)
    manifest = manager.get_wasm_manifest()

    assert manifest["total_artcraft_apps"] == 15
    assert len(manifest["artcraft_apps"]) == 15

    for app_id, app_info in manifest["artcraft_apps"].items():
        assert app_info["app"] == app_id
        assert "extensions" in app_info
        assert "coordinate_system" in app_info
        assert app_info["bundle_url"] == f"/wasm/{app_id}/index.html?host=parent"
        assert app_info["ready_event"] == f"{app_id}:ready"
        assert app_info["open_event"] == f"{app_id}:open"
        assert app_info["save_event"] == f"{app_id}:save"
        assert app_info["dirty_event"] == f"{app_id}:dirty"

    runtimes = manifest["wasm_runtimes"]
    assert "pyodide-wasm" in runtimes
    assert "wasi-wasm" in runtimes
    assert "quickjs-wasm" in runtimes
    assert "three-glb-viewer" in runtimes


def test_generate_minimal_glb_bytes():
    glb = generate_minimal_glb_bytes("test_mesh")
    assert len(glb) > 100
    assert glb[:4] == b"glTF"
    version = struct.unpack("<I", glb[4:8])[0]
    length = struct.unpack("<I", glb[8:12])[0]
    assert version == 2
    assert length == len(glb)


def test_normalize_path_and_summary(temp_spaces_dir):
    vfs = SingleFileSpaceVFS(scope="user", owner_id="path_user", base_dir=temp_spaces_dir)
    assert vfs.normalize_path("foo/bar") == "/foo/bar"
    assert vfs.normalize_path("/foo/../bar") == "/bar"
    assert vfs.normalize_path("///a//b///c") == "/a/b/c"
    assert vfs.normalize_path("../../etc/passwd") == "/etc/passwd"

    summary = vfs.get_summary()
    assert summary["scope"] == "user"
    assert summary["owner_id"] == "path_user"
    assert summary["file_count"] >= 5
    assert len(summary["merkle_root"]) == 64
    assert isinstance(summary["recent_runs"], list)
    assert isinstance(summary["recent_turns"], list)


def test_manager_list_and_export_b64(temp_spaces_dir):
    manager = AgentSpaceManager(base_dir=temp_spaces_dir)
    s1 = manager.get_space(scope="user", owner_id="u1")
    s2 = manager.get_space(scope="topic", owner_id="t1")

    spaces = manager.list_spaces()
    assert len(spaces) >= 2
    scopes = {s["scope"] for s in spaces}
    assert "user" in scopes
    assert "topic" in scopes

    user_spaces = manager.list_spaces(scope="user")
    assert all(s["scope"] == "user" for s in user_spaces)

    # Export b64 and import b64
    b64_str = manager.export_space_b64("user", "u1")
    assert isinstance(b64_str, str)
    assert len(b64_str) > 0

    imp_res = manager.import_space("user", "u_clone", b64_str)
    assert imp_res["imported"] is True
    clone_space = manager.get_space("user", "u_clone")
    assert clone_space.compute_merkle_root() == s1.compute_merkle_root()


def test_playground_runner_timeout_and_wasm(temp_spaces_dir):
    vfs = SingleFileSpaceVFS(scope="user", owner_id="runner_edge", base_dir=temp_spaces_dir)
    runner = WasmAndCodePlaygroundRunner()

    # 1. Timeout handling
    loop_code = "import time\ntime.sleep(2.0)\nprint('done')\n"
    res_timeout = runner.execute(
        vfs=vfs,
        entrypoint="/src/loop.py",
        runtime="python",
        code_override=loop_code,
        timeout_sec=0.2,
    )
    assert res_timeout["exit_code"] == 124
    assert "timed out" in res_timeout["stderr"]

    # 2. Wasm validation
    wasm_magic = b"\x00asm\x01\x00\x00\x00"
    vfs.write_file("/bin/sample.wasm", wasm_magic)
    res_wasm = runner.execute(vfs=vfs, entrypoint="/bin/sample.wasm", runtime="wasm")
    assert res_wasm["exit_code"] == 0
    assert "[Wasm Module Validated]" in res_wasm["stdout"]

    # 3. Invalid Wasm
    vfs.write_file("/bin/corrupt.wasm", b"notwasmheader")
    res_corrupt = runner.execute(vfs=vfs, entrypoint="/bin/corrupt.wasm", runtime="wasm")
    assert res_corrupt["exit_code"] == 1
    assert "Invalid WebAssembly" in res_corrupt["stderr"]


def test_agent_space_harness_with_code_block_and_ai_router(temp_spaces_dir):
    vfs = SingleFileSpaceVFS(scope="user", owner_id="harness_code", base_dir=temp_spaces_dir)

    class MockAIRouter:
        def __init__(self):
            self.calls = []

        def dispatch_completion(self, alias, messages):
            self.calls.append({"alias": alias, "messages": messages})
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "Execution verified: computation ran successfully in isolated space VFS.",
                    }
                }]
            }

    mock_router = MockAIRouter()
    harness = AgentSpaceHarness(vfs=vfs, ai_router=mock_router)

    prompt = (
        "Here is the Python module to execute:\n"
        "```python\n"
        "x = 10 * 10\n"
        "print(f'COMPUTATION_RESULT={x}')\n"
        "```\n"
    )

    result = harness.run_agent(prompt=prompt, model_alias="gemini-brain")
    assert result["turn_id"].startswith("turn_")
    assert "/src/agent_code.py" in result["files_mutated"]
    assert len(result["exec_results"]) == 1
    assert "COMPUTATION_RESULT=100" in result["exec_results"][0]["stdout"]
    assert "Execution verified" in result["reply"]
    assert len(mock_router.calls) == 1

