"""Tests for unified Text/Image/Video/World model preferences & harness/terminal env injection."""

from __future__ import annotations

from iot_federated_agent_memory.account_registry import PeerAccountRegistry
from iot_federated_agent_memory.model_prefs import (
    load_model_prefs,
    resolve_harness_env,
    resolve_harness_model_flag,
    save_model_prefs,
)
from iot_federated_agent_memory.pty_sessions import prepare_tui_command


def test_model_prefs_save_and_load_file_and_sqlite(tmp_path):
    prefs_file = str(tmp_path / "model_prefs.json")
    reg = PeerAccountRegistry(db_path=str(tmp_path / "prefs.db"))

    saved = save_model_prefs(
        {
            "text": {"provider": "openrouter", "model": "anthropic/claude-sonnet-4"},
            "image": {"provider": "nanogpt", "model": "nanogpt/flux-pro"},
            "video": {"provider": "nanogpt", "model": "nanogpt/kling-v2.1"},
            "world": {"provider": "worldlabs", "model": "worldlabs/marble-v2"},
            "harness_overrides": {
                "codex": {"provider": "nanogpt", "model": "nanogpt/TEE/deepseek-v4.1-flash"},
            },
        },
        path=prefs_file,
        registry=reg,
    )
    assert saved["modalities"]["text"]["provider"] == "openrouter"
    assert saved["modalities"]["image"]["model"] == "nanogpt/flux-pro"
    assert saved["modalities"]["video"]["model"] == "nanogpt/kling-v2.1"
    assert saved["modalities"]["world"]["model"] == "worldlabs/marble-v2"

    loaded_file = load_model_prefs(path=prefs_file)
    assert loaded_file["modalities"]["text"]["model"] == "anthropic/claude-sonnet-4"

    loaded_db = load_model_prefs(registry=reg)
    assert loaded_db["harness_overrides"]["codex"]["provider"] == "nanogpt"


def test_resolve_harness_env_plugs_nanogpt_and_openrouter_into_all_harnesses(tmp_path):
    prefs = save_model_prefs(
        {
            "text": {"provider": "nanogpt", "model": "nanogpt/TEE/deepseek-v4.1-flash"},
            "image": {"provider": "nanogpt", "model": "nanogpt/flux-pro"},
            "video": {"provider": "nanogpt", "model": "nanogpt/kling-v2.1"},
            "world": {"provider": "worldlabs", "model": "worldlabs/marble-v2"},
            "harness_overrides": {
                "claude-code": {"provider": "openrouter", "model": "anthropic/claude-sonnet-4"},
            },
        },
        path=str(tmp_path / "prefs.json"),
    )
    fake_env = {"NANOGPT_API_KEY": "ng-test-key", "OPENROUTER_API_KEY": "or-test-key"}

    bash_env = resolve_harness_env("bash", prefs=prefs, base_env=fake_env)
    assert bash_env["OPENAI_BASE_URL"] == "https://nano-gpt.com/api/v1"
    assert bash_env["OPENAI_API_KEY"] == "ng-test-key"
    assert bash_env["TINCAN_TEXT_MODEL"] == "nanogpt/TEE/deepseek-v4.1-flash"
    assert bash_env["TINCAN_IMAGE_MODEL"] == "nanogpt/flux-pro"
    assert bash_env["TINCAN_VIDEO_MODEL"] == "nanogpt/kling-v2.1"
    assert bash_env["TINCAN_WORLD_MODEL"] == "worldlabs/marble-v2"

    claude_env = resolve_harness_env("claude-code", prefs=prefs, base_env=fake_env)
    assert claude_env["ANTHROPIC_BASE_URL"] == "https://openrouter.ai/api"
    assert claude_env["ANTHROPIC_AUTH_TOKEN"] == "or-test-key"
    assert claude_env["CLAUDE_MODEL"] == "anthropic/claude-sonnet-4"

    aider_env = resolve_harness_env("aider", prefs=prefs, base_env=fake_env)
    assert aider_env["AIDER_MODEL"] == "openai/TEE/deepseek-v4.1-flash"

    goose_env = resolve_harness_env("goose", prefs=prefs, base_env=fake_env)
    assert goose_env["GOOSE_PROVIDER"] == "openai"
    assert goose_env["OPENAI_HOST"] == "https://nano-gpt.com/api/v1"

    assert resolve_harness_model_flag("opencode", prefs=prefs, base_env=fake_env) == "nanogpt/TEE/deepseek-v4.1-flash"


def test_prepare_tui_command_shell_injects_modality_env(monkeypatch, tmp_path):
    prefs_file = str(tmp_path / "model_prefs.json")
    save_model_prefs({"text": {"provider": "nanogpt", "model": "nanogpt/TEE/deepseek-v4.1-flash"}}, path=prefs_file)
    monkeypatch.setenv("TINCAN_MODEL_PREFS_PATH", prefs_file)
    monkeypatch.setenv("NANOGPT_API_KEY", "ng-shell-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    argv, extra, app_id = prepare_tui_command("bash")
    assert argv
    assert extra["OPENAI_BASE_URL"] == "https://nano-gpt.com/api/v1"
    assert extra["TINCAN_TEXT_MODEL"] == "nanogpt/TEE/deepseek-v4.1-flash"
    assert extra["TINCAN_WORLD_MODEL"] == "worldlabs/marble-v2"
