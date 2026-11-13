"""Exec sandbox dev toolchain: PATH/env for brew, cargo, node; tool runtimes; no-sync dirs."""

import os
import shutil
import tempfile

import pytest

from iot_federated_agent_memory.agent_space import (
    TOOL_RUNTIMES,
    SingleFileSpaceVFS,
    WasmAndCodePlaygroundRunner,
    build_toolchain_env,
)


@pytest.fixture
def spaces_dir():
    with tempfile.TemporaryDirectory(prefix="test_tool_spaces_") as d:
        yield d


def test_toolchain_env_paths_and_homes(tmp_path):
    home = tmp_path / "home"
    (home / ".cargo" / "bin").mkdir(parents=True)
    (home / ".rustup").mkdir()
    env = build_toolchain_env(str(tmp_path / "run"), str(tmp_path / "cache"),
                              base_env={"PATH": "/usr/bin:/bin", "HOME": str(home), "HOMEBREW_NO_ANALYTICS": "1"})
    parts = env["PATH"].split(os.pathsep)
    assert parts[:2] == ["/usr/bin", "/bin"]  # server PATH stays first
    assert str(home / ".cargo" / "bin") in parts
    assert env["CARGO_HOME"] == str(home / ".cargo")
    assert env["RUSTUP_HOME"] == str(home / ".rustup")
    assert env["HOME"] == str(tmp_path / "run")
    assert env["npm_config_cache"].startswith(str(tmp_path / "cache"))
    assert env["HOMEBREW_NO_ANALYTICS"] == "1"


def test_toolchain_env_passes_explicit_homes(tmp_path):
    env = build_toolchain_env("/tmp/r", "/tmp/c", base_env={"PATH": "/bin", "CARGO_HOME": "/opt/cargo",
                                                            "RUSTUP_HOME": "/opt/rustup", "HOMEBREW_PREFIX": "/opt/brew"})
    assert env["CARGO_HOME"] == "/opt/cargo" and env["RUSTUP_HOME"] == "/opt/rustup" and env["HOMEBREW_PREFIX"] == "/opt/brew"


def test_tool_runtimes_known():
    assert set(TOOL_RUNTIMES) >= {"npm", "npx", "cargo", "brew"}


def test_missing_tool_reports_127(spaces_dir, monkeypatch):
    monkeypatch.setattr("iot_federated_agent_memory.agent_space._TOOLCHAIN_DIRS", ())
    monkeypatch.setenv("PATH", "/nonexistent")
    monkeypatch.setenv("HOME", "/nonexistent")
    vfs = SingleFileSpaceVFS(scope="topic", owner_id="tools_missing", base_dir=spaces_dir)
    res = WasmAndCodePlaygroundRunner().execute(vfs=vfs, runtime="brew", args=["--version"])
    assert res["exit_code"] == 127


@pytest.mark.skipif(shutil.which("npm") is None, reason="npm not installed")
def test_npm_runtime_runs_without_entrypoint(spaces_dir):
    vfs = SingleFileSpaceVFS(scope="topic", owner_id="tools_npm", base_dir=spaces_dir)
    res = WasmAndCodePlaygroundRunner().execute(vfs=vfs, runtime="npm", args=["-v"])
    assert res["exit_code"] == 0, res["stderr"]
    assert res["stdout"].strip()[0].isdigit()
    assert not any("/.npm/" in p for p in res["synced_files"])


@pytest.mark.skipif(shutil.which("rustc") is None and not os.path.exists(os.path.expanduser("~/.cargo/bin/rustc")),
                    reason="rustc not installed")
def test_rust_file_runtime(spaces_dir):
    vfs = SingleFileSpaceVFS(scope="topic", owner_id="tools_rust", base_dir=spaces_dir)
    res = WasmAndCodePlaygroundRunner().execute(
        vfs=vfs, entrypoint="/src/main.rs", runtime="auto", timeout_sec=120,
        code_override='fn main() { println!("hi from rust {}", std::env::args().nth(1).unwrap_or_default()); }',
        args=["arg1"],
    )
    assert res["runtime"] == "rust"
    assert res["exit_code"] == 0, res["stderr"]
    assert "hi from rust arg1" in res["stdout"]
    assert res["synced_files"] == []  # binary stays out of the VFS


def test_node_modules_not_synced(spaces_dir):
    vfs = SingleFileSpaceVFS(scope="topic", owner_id="tools_sync", base_dir=spaces_dir)
    script = (
        "import os\n"
        "os.makedirs('node_modules/x', exist_ok=True)\n"
        "open('node_modules/x/index.js','w').write('1')\n"
        "open('out.txt','w').write('ok')\n"
    )
    res = WasmAndCodePlaygroundRunner().execute(vfs=vfs, entrypoint="/src/w.py", runtime="python", code_override=script)
    assert res["exit_code"] == 0, res["stderr"]
    assert "/src/out.txt" in res["synced_files"] or "/out.txt" in res["synced_files"]
    assert not any("node_modules" in p for p in res["synced_files"])
