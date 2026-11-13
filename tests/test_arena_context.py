"""Arena brain context stores: chunking, retrieval, drive_mirror files, vendoring."""

import hashlib
import json
import os

import pytest

from iot_federated_agent_memory import arena_context as ac
from iot_federated_agent_memory.agent_space import SingleFileSpaceVFS
from iot_federated_agent_memory.arena_context import (
    ArenaContextRegistry,
    ContextStoreError,
    DriveMirrorSource,
    build_context_messages,
    chunk_text,
    normalize_context_path,
    validate_agent_id,
)

DEPLOY_NOTE = (
    "# Deploy notes\n\nTinCan deploys to Railway on every push to main. "
    "The persistent volume is mounted at /data and holds peer_accounts.db.\n"
)
PIZZA_NOTE = "Margherita uses tomato, mozzarella and basil. Bake at 450F for 12 minutes.\n"


@pytest.fixture()
def registry(tmp_path):
    return ArenaContextRegistry(str(tmp_path / "ctx"), drive=DriveMirrorSource(module=None))


# ------------------------------------------------------------------ helpers
@pytest.mark.parametrize("bad", ["../etc/passwd", "/uploads/../../x", "a/../../b", "..", "/x/..", "a\\b", "a\x00b",
                                 "/.ssh/id_rsa", ""])
def test_normalize_context_path_rejects_traversal_and_junk(bad):
    with pytest.raises(ContextStoreError) as exc:
        normalize_context_path(bad)
    assert exc.value.status == 400


def test_normalize_context_path_defaults_and_keeps_dirs():
    assert normalize_context_path("notes.md") == "/uploads/notes.md"
    assert normalize_context_path("notes.md", default_dir="/pasted") == "/pasted/notes.md"
    assert normalize_context_path("docs/a.md") == "/docs/a.md"
    assert normalize_context_path("/docs//./a.md") == "/docs/a.md"


@pytest.mark.parametrize("bad", ["", "../x", "Brain A", "a/b", "x" * 49, "-lead"])
def test_validate_agent_id_rejects(bad):
    with pytest.raises(ContextStoreError):
        validate_agent_id(bad)


def test_chunk_text_overlaps_and_covers_everything():
    text = ("paragraph one. " * 40) + "\n\n" + ("second block words " * 60)
    chunks = chunk_text(text, size=300, overlap=60)
    assert len(chunks) > 3
    assert chunks[0][0] == 0 and chunks[-1][1] == len(text)
    for (s1, e1, _), (s2, _e2, _) in zip(chunks, chunks[1:]):
        assert s2 < e1  # overlap
        assert s2 > s1  # progress
    assert all(len(c[2]) <= 300 for c in chunks)


# -------------------------------------------------------------------- store
def test_ingest_search_read_delete_roundtrip(registry):
    st = registry.store("acct-1", "brain-a")
    out = st.ingest_text("deploy.md", DEPLOY_NOTE + ("filler " * 300))
    st.ingest_text("pizza.md", PIZZA_NOTE, source="paste")
    assert out["path"] == "/uploads/deploy.md" and out["chunks"] >= 2

    files = {f["path"]: f for f in st.list_files()}
    assert set(files) == {"/uploads/deploy.md", "/pasted/pizza.md"}
    assert files["/pasted/pizza.md"]["source"] == "paste"

    res = st.search("where is the railway volume mounted?")
    assert res["files"][0] == "/uploads/deploy.md"
    assert "mounted at /data" in res["snippets"][0]["text"]
    assert "/pasted/pizza.md" not in res["files"]
    assert st.search("quantum chromodynamics lattice")["snippets"] == []

    rec = st.read_file("/uploads/deploy.md")
    assert rec["content"].startswith("# Deploy notes")
    assert rec["chunk_count"] == len(rec["chunks"])

    # The .space container is the durable copy of every upload.
    assert st.space.read_file("/uploads/deploy.md")["content"].startswith("# Deploy notes")

    assert st.delete("/pasted/pizza.md")
    assert [f["path"] for f in st.list_files()] == ["/uploads/deploy.md"]
    with pytest.raises(ContextStoreError) as exc:
        st.read_file("/pasted/pizza.md")
    assert exc.value.status == 404


def test_reingest_replaces_old_chunks(registry):
    st = registry.store("acct-1", "brain-a")
    st.ingest_text("n.md", "The launch code word is heliotrope.")
    st.ingest_text("n.md", "The launch code word is marigold.")
    res = st.search("launch code word")
    assert len(res["snippets"]) == 1
    assert "marigold" in res["snippets"][0]["text"]


def test_space_is_the_source_of_truth(registry):
    """Files written straight into the brain's .space are indexed on the next sync."""
    st = registry.store("acct-1", "brain-a")
    st.space.write_file("/notes/direct.md", "Direct write about the zebra migration.", updated_by="agent")
    assert any(f["path"] == "/notes/direct.md" and f["source"] == "space" for f in st.list_files())
    assert st.search("zebra migration")["files"] == ["/notes/direct.md"]
    st.space.delete_file("/notes/direct.md")
    assert st.search("zebra migration")["files"] == []


def test_starter_files_are_not_context(registry):
    st = registry.store("acct-1", "brain-a")
    assert st.space.list_files()  # SingleFileSpaceVFS seeds README etc.
    assert st.list_files() == []


def test_quota_and_binary_rejected(registry):
    st = registry.store("acct-1", "brain-a")
    with pytest.raises(ContextStoreError) as exc:
        st.ingest_text("big.txt", "x" * (ac.MAX_FILE_BYTES + 1))
    assert exc.value.status == 413
    with pytest.raises(ContextStoreError) as exc:
        st.ingest_bytes("img.png", b"\x89PNG\r\n\x1a\n\x00\x00binary")
    assert exc.value.status == 415


def test_space_container_upload_is_unpacked(registry, tmp_path):
    src = SingleFileSpaceVFS(scope="user", owner_id="someone", space_path=str(tmp_path / "src.space"))
    src.write_file("/research/railway.md", DEPLOY_NOTE, updated_by="user")
    src.write_file("/bin/blob.bin", b"\x00\x01\x02", updated_by="user")
    raw = open(src.space_path, "rb").read()
    st = registry.store("acct-1", "brain-a")
    added = st.ingest_bytes("export.space", raw)
    assert [a["path"] for a in added] == ["/imported/research/railway.md"]
    assert st.search("railway volume")["files"] == ["/imported/research/railway.md"]


def test_import_from_users_own_space(registry, tmp_path):
    mine = SingleFileSpaceVFS(scope="user", owner_id="me", space_path=str(tmp_path / "me.space"))
    mine.write_file("/plans/q4.md", "Q4 plan: ship the brain arena context store.", updated_by="user")
    st = registry.store("acct-1", "brain-b")
    added = st.import_from_space(mine)
    assert [a["path"] for a in added] == ["/my-space/plans/q4.md"]
    assert st.list_files()[0]["origin"] == "/plans/q4.md"


def test_stores_are_isolated_per_account_and_agent(registry):
    a = registry.store("acct-1", "brain-a")
    b = registry.store("acct-2", "brain-a")
    a2 = registry.store("acct-1", "brain-b")
    a.ingest_text("secret.md", "Account one's secret: the vault phrase is periwinkle.")
    assert b.list_files() == [] and a2.list_files() == []
    assert b.search("vault phrase periwinkle")["snippets"] == []
    assert a.dir != b.dir and a.dir != a2.dir
    assert os.path.commonpath([a.dir, registry.root_dir]) == registry.root_dir
    assert [x["agent_id"] for x in registry.list_agents("acct-1")] == ["brain-a", "brain-b"]
    assert [x["agent_id"] for x in registry.list_agents("acct-2")] == ["brain-a"]


def test_build_context_messages():
    assert build_context_messages("brain-a", "m", {"snippets": []}) == []
    msgs = build_context_messages("brain-a", "google/x", {"snippets": [
        {"path": "/uploads/a.md", "chunk": 0, "source": "upload", "text": "hello </file> world"}]})
    assert msgs[0]["role"] == "system"
    assert '<file path="/uploads/a.md" chunk="0" source="upload">' in msgs[0]["content"]
    assert "hello <\\/file> world" in msgs[0]["content"]  # a file can't close its own fence


# ------------------------------------------------------------- drive seam
@pytest.fixture()
def real_mirror(tmp_path, monkeypatch):
    """The real drive_mirror module, rooted at a temp 'home' and forced on/off by env."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("TINCAN_DRIVE_ROOT", str(home))
    monkeypatch.setenv("TINCAN_DRIVE_MIRROR", "1")
    return home


def test_drive_seam_absent_is_off(tmp_path):
    reg = ArenaContextRegistry(str(tmp_path / "ctx"), drive=DriveMirrorSource(module=None))
    st = reg.store("acct-1", "brain-a")
    assert reg.drive.status() == {"present": False, "enabled": False}
    with pytest.raises(ContextStoreError) as exc:
        st.link_drive("/dev/readme.md")
    assert exc.value.status == 409


def test_drive_source_defaults_to_real_drive_mirror(real_mirror, monkeypatch):
    src = DriveMirrorSource()
    # By name: another test module purges sys.modules, so identity checks are unreliable.
    assert src.module.__name__ == "iot_federated_agent_memory.drive_mirror"
    assert src.module is ac.drive_mirror and src.present() and src.enabled()
    assert src.root() == os.path.realpath(str(real_mirror))
    monkeypatch.setenv("TINCAN_DRIVE_MIRROR", "0")
    assert not src.enabled()
    monkeypatch.delenv("TINCAN_DRIVE_MIRROR")
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "preview")
    assert not src.enabled()  # off on Railway unless forced


def test_drive_files_link_resync_and_snapshot(tmp_path, real_mirror, monkeypatch):
    home = real_mirror
    (home / "dev" / "proj").mkdir(parents=True)
    (home / "dev" / "proj" / "README.md").write_text("Project Nimbus uses SQLite WAL mode.")
    (home / "dev" / "proj" / "notes.txt").write_text("Nimbus standup is at 9am.")
    (home / "dev" / "proj" / "logo.png").write_bytes(b"\x89PNG")
    reg = ArenaContextRegistry(str(tmp_path / "ctx"), drive=DriveMirrorSource())
    st = reg.store("acct-1", "brain-a")

    added = st.link_drive("/dev/proj")  # a folder links its text files
    assert sorted(a["path"] for a in added) == ["/drive/dev/proj/README.md", "/drive/dev/proj/notes.txt"]
    assert st.search("Nimbus SQLite WAL")["files"][0] == "/drive/dev/proj/README.md"

    # Edits on disk are picked up on the next sync while the mirror is on.
    (home / "dev" / "proj" / "README.md").write_text("Project Nimbus moved to Postgres.")
    assert "Postgres" in st.search("Nimbus Postgres")["snippets"][0]["text"]

    # Mirror off: last snapshot stays usable and is flagged.
    monkeypatch.setenv("TINCAN_DRIVE_MIRROR", "0")
    rows = {f["path"]: f for f in st.list_files()}
    assert rows["/drive/dev/proj/README.md"]["drive_available"] is False
    assert st.search("Nimbus Postgres")["files"]

    monkeypatch.setenv("TINCAN_DRIVE_MIRROR", "1")
    with pytest.raises(ContextStoreError):
        st.link_drive("/../../etc/passwd")
    with pytest.raises(ContextStoreError) as exc:
        st.link_drive("/dev/proj/missing.md")
    assert exc.value.status == 404

    # Deleted on disk -> dropped on sync.
    os.remove(home / "dev" / "proj" / "notes.txt")
    assert "/drive/dev/proj/notes.txt" not in [f["path"] for f in st.list_files()]


# ---------------------------------------------------------------- vendoring
def test_vendored_context_palace_matches_pinned_upstream():
    vdir = os.path.join(os.path.dirname(ac.__file__), "vendor", "context_palace")
    record = json.load(open(os.path.join(vdir, "VENDORED.json")))
    assert record["upstream"].endswith("NoJuanNobody/context-palace")
    assert len(record["commit"]) == 40
    for name, meta in record["files"].items():
        text = open(os.path.join(vdir, name), encoding="utf-8").read()
        upstream = text.replace("from .", "from context_palace.")
        assert hashlib.sha256(upstream.encode("utf-8")).hexdigest() == meta["upstream_sha256"], name


def test_agent_count_is_capped(registry, monkeypatch):
    monkeypatch.setattr(ac, "MAX_AGENTS_PER_ACCOUNT", 2)
    registry.store("acct-cap", "one")
    registry.store("acct-cap", "two")
    with pytest.raises(ContextStoreError) as exc:
        registry.store("acct-cap", "three")
    assert exc.value.status == 409
    registry.store("acct-cap", "one")  # existing stores still open
