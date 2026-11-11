"""Agent runner loop with the OpenRouter router mocked (no paid calls)."""

from __future__ import annotations

from pathlib import Path

import pytest

from iot_federated_agent_memory.agent_runner import AgentRunner, AgentTask
from iot_federated_agent_memory.thread_fs import read_file, start_or_continue_thread, write_file


class ScriptedRouter:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def dispatch_completion(self, alias, messages, temperature=0.0, max_tokens=1024):
        self.calls.append({"alias": alias, "messages": messages})
        content = self.replies.pop(0)
        return {"choices": [{"message": {"role": "assistant", "content": content}}]}


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return tmp_path / "threads"


def test_runner_lists_then_finishes(root: Path):
    tdir = start_or_continue_thread("peer-1", root=root, template="scam-case")
    write_file("peer-1", tdir.name, "notes.txt", "workspace ok", root=root)
    router = ScriptedRouter(
        [
            '{"tool":"list_files","args":{}}',
            '{"tool":"read_file","args":{"path":"notes.txt"}}',
            '{"tool":"finish","args":{"result":"read the notes"}}',
        ]
    )
    runner = AgentRunner(router=router, root=root)
    task = AgentTask.create("peer-1", tdir.name, "Summarize the workspace")
    result = runner.run(task)
    assert result.status == "completed"
    assert result.result == "read the notes"
    assert [s["tool"] for s in result.steps] == ["list_files", "read_file", "finish"]
    assert any(e["path"] == "notes.txt" for e in result.steps[0]["output"])
    assert result.steps[1]["output"]["content"] == "workspace ok"
    assert router.calls  # used the injected router, not OpenRouter


def test_runner_can_write_via_tool(root: Path):
    tdir = start_or_continue_thread("peer-1", root=root)
    router = ScriptedRouter(
        [
            '{"tool":"write_file","args":{"path":"out.txt","content":"done"}}',
            '{"tool":"finish","args":{"result":"wrote out.txt"}}',
        ]
    )
    result = AgentRunner(router=router, root=root).run(
        AgentTask.create("peer-1", tdir.name, "Write a file")
    )
    assert result.status == "completed"
    assert read_file("peer-1", tdir.name, "out.txt", root=root) == "done"


def test_runner_fails_for_unknown_thread(root: Path):
    router = ScriptedRouter([])
    result = AgentRunner(router=router, root=root).run(
        AgentTask.create("peer-1", "a" * 32, "Nope")
    )
    assert result.status == "failed"
    assert result.error == "Thread not found"
    assert router.calls == []


def test_runner_stops_at_max_steps(root: Path):
    tdir = start_or_continue_thread("peer-1", root=root)
    router = ScriptedRouter(
        [
            '{"tool":"list_files","args":{}}',
            '{"tool":"list_files","args":{}}',
        ]
    )
    task = AgentTask.create("peer-1", tdir.name, "Loop", max_steps=2)
    result = AgentRunner(router=router, root=root).run(task)
    assert result.status == "failed"
    assert "max_steps" in (result.error or "")
