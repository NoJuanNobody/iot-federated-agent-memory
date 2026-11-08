"""Tests for the TinCan Human-In-The-Loop Accessibility Action Gate."""
import os
import pytest
from pathlib import Path
from iot_federated_agent_memory.tincan_actions import (
    enqueue_action,
    load_pending_actions,
    execute_action,
    dismiss_action,
)

def test_enqueue_list_dismiss(tmp_path):
    config_dir = str(tmp_path)
    assert load_pending_actions(config_dir) == []

    action_entry = enqueue_action(
        seq=1,
        sender="tc:peer1testaddress",
        sender_alias="peer1",
        command_text="Open Gemini",
        config_dir=config_dir,
    )
    assert action_entry is not None
    assert action_entry["seq"] == 1
    assert action_entry["status"] == "pending_approval"

    actions = load_pending_actions(config_dir)
    assert len(actions) == 1
    assert actions[0]["command"] == "Open Gemini"

    # Dismiss action
    dismissed = dismiss_action("1", config_dir=config_dir)
    assert dismissed["status"] == "dismissed"
    actions_after = load_pending_actions(config_dir)
    assert actions_after[0]["status"] == "dismissed"

def test_execute_action_mock(tmp_path, monkeypatch):
    config_dir = str(tmp_path)
    enqueue_action(
        seq=2,
        sender="tc:peer1testaddress",
        sender_alias="peer1",
        command_text="Open Gemini",
        config_dir=config_dir,
    )

    called = []
    def mock_run(cmd, **kwargs):
        called.append(cmd)
        class DummyProcess:
            returncode = 0
        return DummyProcess()

    monkeypatch.setattr("subprocess.run", mock_run)

    res = execute_action("2", config_dir=config_dir)
    assert res["status"] == "completed"
    assert "https://gemini.google.com" in res["result"]
    assert len(called) == 1

def test_execute_missing_action(tmp_path):
    config_dir = str(tmp_path)
    with pytest.raises(ValueError):
        execute_action("999", config_dir=config_dir)
