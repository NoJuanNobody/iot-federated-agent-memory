"""Tests for the TinCan Human-In-The-Loop Approval-Gated Accessibility Action Gate."""
import pytest
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


def test_execute_action_after_approval(tmp_path, monkeypatch):
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

    # Nothing runs while queued in pending_approval
    assert len(called) == 0

    # Once explicitly triggered by the user (`tincan trigger 2`), the approved action executes
    res = execute_action("2", config_dir=config_dir)
    assert res["status"] == "completed"
    assert "https://gemini.google.com" in res["result"]
    assert len(called) == 1


def test_execute_tts_action_after_approval(tmp_path, monkeypatch):
    config_dir = str(tmp_path)
    enqueue_action(
        seq=3,
        sender="tc:peer1testaddress",
        sender_alias="maya",
        command_text="Render is complete!",
        config_dir=config_dir,
        action_type="tts",
    )

    spoken = []
    monkeypatch.setattr(
        "iot_federated_agent_memory.tincan_voice.speak_text",
        lambda text, voice=None, background=True: spoken.append(text) or {"status": "spoken", "engine": "kokoro-say"},
    )

    assert len(spoken) == 0
    res = execute_action("3", config_dir=config_dir)
    assert res["status"] == "completed"
    assert len(spoken) == 1
    assert "Render is complete!" in spoken[0]


def test_execute_missing_action(tmp_path):
    config_dir = str(tmp_path)
    with pytest.raises(ValueError):
        execute_action("999", config_dir=config_dir)


def test_mentor_mentee_cli_workflow(tmp_path, capsys):
    import json
    from iot_federated_agent_memory.tincan_core import TinCanIdentity
    from iot_federated_agent_memory.tincan_cli import main as cli_main

    mentor_id = TinCanIdentity.generate()
    mentee_id = TinCanIdentity.generate()

    # 1. Pin a Mentor contact (default approval-gated voice)
    rc1 = cli_main([
        "--dir", str(tmp_path),
        "add-contact", "prof-maya", mentor_id.address,
        "--role", "mentor",
        "--json",
    ])
    assert rc1 == 0
    out1 = json.loads(capsys.readouterr().out)
    assert out1["role"] == "mentor"
    assert out1["trust_mentor_tts"] is False

    # 2. Pin a Mentee contact
    rc2 = cli_main([
        "--dir", str(tmp_path),
        "add-contact", "alex", mentee_id.address,
        "--role", "mentee",
        "--json",
    ])
    assert rc2 == 0
    out2 = json.loads(capsys.readouterr().out)
    assert out2["role"] == "mentee"

    # 3. Check `tincan mentor status --json`
    rc3 = cli_main(["--dir", str(tmp_path), "mentor", "status", "--json"])
    assert rc3 == 0
    status_data = json.loads(capsys.readouterr().out)
    assert len(status_data["mentors"]) == 1
    assert status_data["mentors"][0]["alias"] == "prof-maya"
    assert len(status_data["mentees"]) == 1
    assert status_data["mentees"][0]["alias"] == "alex"

    # 4. Toggle live voice coaching ON and then back to approval-gated
    rc4 = cli_main(["--dir", str(tmp_path), "mentor", "set", "prof-maya", "--role", "mentor", "--allow-voice", "--json"])
    assert rc4 == 0
    upd_on = json.loads(capsys.readouterr().out)
    assert upd_on["trust_mentor_tts"] is True

    rc5 = cli_main(["--dir", str(tmp_path), "mentor", "set", "prof-maya", "--role", "mentor", "--gate-voice", "--json"])
    assert rc5 == 0
    upd_off = json.loads(capsys.readouterr().out)
    assert upd_off["trust_mentor_tts"] is False
