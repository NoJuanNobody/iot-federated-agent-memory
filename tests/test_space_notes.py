"""Tests for the Notes -> Apply AI editor on Single-File Space VFS (*.space)."""

import json
import tempfile

import pytest

from iot_federated_agent_memory.agent_space import SingleFileSpaceVFS
from iot_federated_agent_memory.space_notes import EditPlanError, SpaceNotesEditor, _extract_json_object


class FakeRouter:
    """Returns queued replies and records the messages it was sent."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []

    def dispatch_completion(self, alias, messages, temperature=0.7, max_tokens=1024):
        self.calls.append({"alias": alias, "messages": messages})
        content = self.replies.pop(0) if self.replies else ""
        return {"choices": [{"message": {"role": "assistant", "content": content}}]}


@pytest.fixture
def vfs():
    with tempfile.TemporaryDirectory(prefix="test_notes_") as tmpdir:
        v = SingleFileSpaceVFS(scope="user", owner_id="alice", base_dir=tmpdir)
        v.write_file("/doc/story.md", "# Title\n\nThe cat sat.\n", updated_by="test")
        yield v


def _plan(**kwargs):
    base = {"summary": "s", "edits": [], "skipped": [], "conflicts": []}
    base.update(kwargs)
    return "```json\n" + json.dumps(base) + "\n```"


def test_notes_do_not_change_files_and_track_staleness(vfs):
    editor = SpaceNotesEditor(vfs, ai_router=FakeRouter())
    root = vfs.compute_merkle_root()

    n1 = editor.add_note("Cat should be a dog", kind="edit", path="/doc/story.md")
    n2 = editor.add_note("Tone is too flat")
    assert vfs.compute_merkle_root() == root
    assert [n["note_id"] for n in editor.list_notes()] == [n1["note_id"], n2["note_id"]]
    assert not any(n["stale"] for n in editor.list_notes())

    vfs.write_file("/doc/story.md", "# Title\n\nThe cat ran.\n", updated_by="test")
    stale = {n["note_id"]: n["stale"] for n in editor.list_notes()}
    assert stale == {n1["note_id"]: True, n2["note_id"]: True}

    with pytest.raises(ValueError):
        editor.add_note("x", kind="nonsense")


def test_drop_note(vfs):
    editor = SpaceNotesEditor(vfs, ai_router=FakeRouter())
    n = editor.add_note("drop me")
    editor.drop_note(n["note_id"])
    assert editor.list_notes() == []
    assert editor.list_notes(status="dropped")[0]["note_id"] == n["note_id"]
    with pytest.raises(KeyError):
        editor.drop_note(n["note_id"])


def test_ask_saves_answer_as_note_without_mutation(vfs):
    router = FakeRouter("It is a cat.")
    editor = SpaceNotesEditor(vfs, ai_router=router)
    root = vfs.compute_merkle_root()

    out = editor.ask("What animal is in the story?", path="/doc/story.md")
    assert out["answer"] == "It is a cat."
    assert out["note"]["kind"] == "question"
    assert "The cat sat." in router.calls[0]["messages"][0]["content"]
    assert vfs.compute_merkle_root() == root


def test_side_run_uses_throwaway_copy(vfs):
    editor = SpaceNotesEditor(vfs, ai_router=FakeRouter())
    root = vfs.compute_merkle_root()
    files_before = {f["path"] for f in vfs.list_files()}

    out = editor.side_run(
        entrypoint="/scratch/probe.py",
        code="open('side_effect.txt','w').write('x')\nprint(open('doc/story.md').read().count('cat'))",
        runtime="python",
    )
    assert out["run"]["exit_code"] == 0
    assert "1" in out["run"]["stdout"]
    assert out["note"]["kind"] == "result"
    assert vfs.compute_merkle_root() == root
    assert {f["path"] for f in vfs.list_files()} == files_before


def test_propose_then_commit_creates_version_and_marks_notes(vfs):
    router = FakeRouter(_plan(
        summary="Swap cat for dog and add an ending",
        edits=[
            {"path": "/doc/story.md", "op": "patch", "target": "The cat sat.", "replacement": "The dog sat."},
            {"path": "/doc/ending.md", "op": "write", "content": "The end.\n"},
        ],
    ))
    editor = SpaceNotesEditor(vfs, ai_router=router)
    n1 = editor.add_note("Cat should be a dog", kind="edit", path="/doc/story.md")
    n2 = editor.add_note("Needs an ending")
    root = vfs.compute_merkle_root()

    plan = editor.propose()
    assert vfs.compute_merkle_root() == root  # proposing changes nothing
    assert plan["note_ids"] == [n1["note_id"], n2["note_id"]]
    prompt = router.calls[0]["messages"][1]["content"]
    assert "Cat should be a dog" in prompt and "Needs an ending" in prompt

    ver = editor.commit(plan["plan_id"])
    assert vfs.read_file("/doc/story.md")["content"] == "# Title\n\nThe dog sat.\n"
    assert vfs.read_file("/doc/ending.md")["content"] == "The end.\n"
    assert {(c["path"], c["op"]) for c in ver["files_changed"]} == {("/doc/story.md", "update"), ("/doc/ending.md", "create")}
    assert editor.list_notes() == []
    applied = editor.list_notes(status="applied")
    assert {n["version_id"] for n in applied} == {ver["version_id"]}
    assert editor.list_versions()[0]["version_id"] == ver["version_id"]

    with pytest.raises(EditPlanError):
        editor.commit(plan["plan_id"])


def test_skipped_notes_stay_pending(vfs):
    editor = SpaceNotesEditor(vfs, ai_router=None)
    keep = editor.add_note("Irrelevant question")
    use = editor.add_note("Add a subtitle")
    editor._ai_router = FakeRouter(_plan(
        edits=[{"path": "/doc/story.md", "op": "patch", "target": "# Title\n", "replacement": "# Title\n## Sub\n"}],
        skipped=[{"note_id": keep["note_id"], "reason": "no change"}],
    ))
    out = editor.apply()
    assert out["notes_applied"] == [use["note_id"]]
    assert [n["note_id"] for n in editor.list_notes()] == [keep["note_id"]]


def test_commit_refuses_when_space_changed(vfs):
    editor = SpaceNotesEditor(vfs, ai_router=FakeRouter(_plan(
        edits=[{"path": "/doc/story.md", "op": "write", "content": "new"}],
    )))
    editor.add_note("rewrite")
    plan = editor.propose()
    vfs.write_file("/doc/story.md", "someone else edited this", updated_by="peer")
    with pytest.raises(EditPlanError, match="changed since"):
        editor.commit(plan["plan_id"])
    assert vfs.read_file("/doc/story.md")["content"] == "someone else edited this"


def test_bad_patch_changes_nothing(vfs):
    editor = SpaceNotesEditor(vfs, ai_router=FakeRouter(_plan(edits=[
        {"path": "/doc/new.md", "op": "write", "content": "should not land"},
        {"path": "/doc/story.md", "op": "patch", "target": "not there", "replacement": "x"},
    ])))
    editor.add_note("something")
    plan = editor.propose()
    root = vfs.compute_merkle_root()
    with pytest.raises(EditPlanError, match="not unique|missing"):
        editor.commit(plan["plan_id"])
    assert vfs.compute_merkle_root() == root
    assert len(editor.list_notes()) == 1


def test_revert_restores_files_and_reopens_notes(vfs):
    editor = SpaceNotesEditor(vfs, ai_router=FakeRouter(_plan(edits=[
        {"path": "/doc/story.md", "op": "delete"},
        {"path": "/doc/other.md", "op": "write", "content": "hi"},
    ])))
    n = editor.add_note("replace story")
    root = vfs.compute_merkle_root()
    ver = editor.apply()
    assert vfs.compute_merkle_root() != root

    editor.revert(ver["version_id"])
    assert vfs.compute_merkle_root() == root
    assert [x["note_id"] for x in editor.list_notes()] == [n["note_id"]]
    assert editor.list_versions()[0]["reverted"] is True
    with pytest.raises(EditPlanError):
        editor.revert(ver["version_id"])


def test_invalid_model_replies():
    with pytest.raises(EditPlanError):
        _extract_json_object("[Simulated Gemini via OpenRouter router: key pending]")
    with pytest.raises(EditPlanError):
        _extract_json_object("")
    assert _extract_json_object('Sure! {"edits": []} hope that helps')["edits"] == []


def test_propose_without_notes_or_with_malformed_plan(vfs):
    editor = SpaceNotesEditor(vfs, ai_router=FakeRouter('{"edits": [{"op": "write"}]}'))
    with pytest.raises(EditPlanError, match="No pending notes"):
        editor.propose()
    editor.add_note("x")
    with pytest.raises(EditPlanError, match="no path"):
        editor.propose()


def test_inline_side_run_does_not_overwrite_entrypoint(vfs):
    vfs.write_file("/src/main.py", "print('original')", updated_by="test")
    editor = SpaceNotesEditor(vfs, ai_router=FakeRouter())
    out = editor.side_run(code="print(open('src/main.py').read())", runtime="python")
    assert out["run"]["stdout"].strip() == "print('original')"
    assert out["run"]["entrypoint"].startswith("/.side/")
    assert vfs.read_file("/src/main.py")["content"] == "print('original')"


def test_pick_router_prefers_local_key_else_relay(monkeypatch):
    from iot_federated_agent_memory.space_notes import RelayChatRouter, pick_router

    class Local:
        openrouter_key = None

    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert isinstance(pick_router(Local(), "https://relay.example", "p"), RelayChatRouter)
    assert pick_router(None, None, "p") is None
    keyed = Local()
    keyed.openrouter_key = "k"
    assert pick_router(keyed, "https://relay.example", "p") is keyed
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    assert pick_router(None, "https://relay.example", "p") is None
