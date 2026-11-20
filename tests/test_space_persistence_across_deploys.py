"""Tests verifying zero-reset .space persistence across deploys, WAL checkpoints, atomic S3 sync, and hydration."""

import importlib
import json
import os
import threading
import urllib.request
from http.server import ThreadingHTTPServer

from iot_federated_agent_memory.agent_space import AgentSpaceManager


def test_spaces_survive_manager_restart_and_wal_checkpoint(tmp_path):
    vol_dir = str(tmp_path / "persistent_data")

    mgr1 = AgentSpaceManager(base_dir=vol_dir, auto_hydrate_s3=False)
    sp_a = mgr1.get_or_create_space("user", "peer-jewkdo")
    sp_a.write_file("/nodes/test.nodes.json", json.dumps({"nodes": [{"id": "n1"}]}), mime_type="application/json")
    sp_a.write_file("/audio/track.mp3", b"ID3REALMP3DATA" * 20, mime_type="audio/mpeg")
    sp_b = mgr1.get_or_create_space("topic", "topic-57003ccbd7")
    sp_b.write_file("/notes/plan.md", "# Do not wipe on deploy\n", mime_type="text/markdown")

    merkle_a = sp_a.compute_merkle_root()
    merkle_b = sp_b.compute_merkle_root()

    # Simulate graceful SIGTERM flush before container swap
    flush_res = mgr1.flush_all_spaces(sync_s3=False)
    assert flush_res["flushed"] == 2

    # Simulate fresh container boot attached to the same persistent /data volume
    mgr2 = AgentSpaceManager(base_dir=vol_dir, auto_hydrate_s3=False)
    listed = mgr2.list_spaces()
    keys = {(s["scope"], s["owner_id"]) for s in listed}
    assert ("user", "peer-jewkdo") in keys
    assert ("topic", "topic-57003ccbd7") in keys

    sp_a2 = mgr2.get_or_create_space("user", "peer-jewkdo")
    sp_b2 = mgr2.get_or_create_space("topic", "topic-57003ccbd7")
    assert sp_a2.compute_merkle_root() == merkle_a
    assert sp_b2.compute_merkle_root() == merkle_b
    assert json.loads(sp_a2.read_file("/nodes/test.nodes.json", as_text=True)["content"])["nodes"][0]["id"] == "n1"
    assert sp_b2.read_file("/notes/plan.md", as_text=True)["content"] == "# Do not wipe on deploy\n"


def test_consistent_s3_backup_atomic_hydrate_and_never_clobbers_local(tmp_path, monkeypatch):
    s3_mod = importlib.import_module("iot_federated_agent_memory.s3_storage")
    fake_bucket = {}

    def fake_put(local_path, object_key, content_type="application/x-sqlite3", creds=None):
        assert s3_mod.validate_sqlite_file(local_path), "S3 upload snapshot must be a valid consistent SQLite file"
        with open(local_path, "rb") as f:
            raw = f.read()
        fake_bucket[object_key] = raw
        return {"status": 200, "bucket": "test-bucket", "key": object_key, "size_bytes": len(raw)}

    def fake_get(object_key, dest_path, creds=None, validate_sqlite=None):
        raw = fake_bucket.get(object_key)
        if not raw:
            return False
        tmp = dest_path + ".test.tmp"
        os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
        with open(tmp, "wb") as f:
            f.write(raw)
        if validate_sqlite and not s3_mod.validate_sqlite_file(tmp):
            os.unlink(tmp)
            return False
        os.replace(tmp, dest_path)
        return True

    def fake_list(prefix="", creds=None):
        return [{"key": k, "size": len(v)} for k, v in fake_bucket.items() if k.startswith(prefix)]

    monkeypatch.setattr(s3_mod, "s3_put_object", fake_put)
    monkeypatch.setattr(s3_mod, "s3_get_object", fake_get)
    monkeypatch.setattr(s3_mod, "s3_list_objects", fake_list)
    monkeypatch.setattr(s3_mod, "get_s3_credentials", lambda: {"bucket": "test-bucket", "endpoint": "https://s3.local", "access_key": "a", "secret_key": "b", "region": "auto"})

    # 1. Populate volume 1 and back up all spaces to S3
    vol1 = str(tmp_path / "vol1")
    mgr1 = AgentSpaceManager(base_dir=vol1, auto_hydrate_s3=False)
    sp1 = mgr1.get_or_create_space("user", "peer-test-alpha")
    sp1.write_file("/nodes/studio.nodes.json", json.dumps({"nodes": [{"id": "hero"}]}))
    sp2 = mgr1.get_or_create_space("user", "peer-test-beta")
    sp2.write_file("/notes/alice.txt", "Alice persistent notes")

    backup_res = mgr1.backup_all_spaces(only_dirty=False)
    assert backup_res["ok"] is True
    assert backup_res["backed_up_count"] == 2
    assert "spaces/users/peer-test-alpha.space" in fake_bucket
    assert "spaces/users/peer-test-beta.space" in fake_bucket

    # 2. Fresh empty volume 2 hydrates all spaces from S3 automatically
    vol2 = str(tmp_path / "vol2")
    mgr2 = AgentSpaceManager(base_dir=vol2, auto_hydrate_s3=False)
    hyd = mgr2.hydrate_from_s3(overwrite_existing=False)
    assert hyd["ok"] is True
    assert hyd["restored_count"] == 2

    sp1_restored = mgr2.get_or_create_space("user", "peer-test-alpha")
    assert json.loads(sp1_restored.read_file("/nodes/studio.nodes.json")["content"])["nodes"][0]["id"] == "hero"

    # 3. Local writes on volume 2 are NEVER overwritten by a subsequent hydrate_from_s3(overwrite_existing=False)
    sp1_restored.write_file("/nodes/studio.nodes.json", json.dumps({"nodes": [{"id": "newer-local"}]}))
    hyd2 = mgr2.hydrate_from_s3(overwrite_existing=False)
    assert hyd2["restored_count"] == 0
    assert hyd2["skipped_count"] == 2
    assert json.loads(sp1_restored.read_file("/nodes/studio.nodes.json")["content"])["nodes"][0]["id"] == "newer-local"

    # 4. Corrupt S3 payload is rejected without clobbering existing local space
    fake_bucket["spaces/users/peer-corrupt.space"] = b"NOT_A_SQLITE_FILE" * 100
    hyd3 = mgr2.hydrate_from_s3(overwrite_existing=False)
    assert "spaces/users/peer-corrupt.space" in hyd3["failed"]
    assert not os.path.exists(os.path.join(vol2, "spaces", "users", "peer-corrupt.space"))


def test_persistence_and_backup_http_endpoints(tmp_path, monkeypatch):
    s3_mod = importlib.import_module("iot_federated_agent_memory.s3_storage")
    srv_mod = importlib.import_module("server")

    vol_dir = str(tmp_path / "http_data")
    monkeypatch.setenv("TINCAN_DATA_DIR", vol_dir)
    temp_mgr = AgentSpaceManager(base_dir=vol_dir, ai_router=srv_mod.router, auto_hydrate_s3=False)
    sp = temp_mgr.get_or_create_space("user", "peer-ops")
    sp.write_file("/nodes/live.nodes.json", json.dumps({"nodes": [{"id": "n-live"}]}))
    monkeypatch.setattr(srv_mod, "_space_manager", temp_mgr)
    monkeypatch.setattr(srv_mod, "_get_space_manager", lambda: temp_mgr)

    uploaded = []
    monkeypatch.setattr(
        s3_mod,
        "s3_put_object",
        lambda local_path, object_key, content_type="application/x-sqlite3", creds=None: (
            uploaded.append(object_key) or {"status": 200, "bucket": "b", "key": object_key, "size_bytes": os.path.getsize(local_path)}
        ),
    )
    monkeypatch.setattr(
        s3_mod,
        "get_s3_credentials",
        lambda: {"bucket": "b", "endpoint": "https://s3.local", "access_key": "a", "secret_key": "s", "region": "auto"},
    )

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), srv_mod.MeshGatewayHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    base_url = f"http://127.0.0.1:{httpd.server_address[1]}"
    try:
        with urllib.request.urlopen(f"{base_url}/api/spaces/persistence", timeout=10) as resp:
            assert resp.status == 200
            st = json.loads(resp.read().decode("utf-8"))
        assert st["ok"] is True
        assert st["is_persistent_volume"] is True
        assert st["writable"] is True
        assert st["space_count"] == 1
        assert st["total_vfs_files"] >= 6
        assert st["s3_backup_enabled"] is True

        req = urllib.request.Request(
            f"{base_url}/api/spaces/backup",
            data=json.dumps({"only_dirty": False}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            assert resp.status == 200
            bk = json.loads(resp.read().decode("utf-8"))
        assert bk["ok"] is True
        assert bk["backed_up_count"] == 1
        assert "spaces/users/peer-ops.space" in uploaded
    finally:
        httpd.shutdown()
        httpd.server_close()
