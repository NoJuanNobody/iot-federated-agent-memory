from iot_federated_agent_memory.scale import IoTFederatedMemoryScale


def test_iot_federated_memory_scale_evaluation(tmp_path):
    vault_dir = tmp_path / "vault_data"
    grok_dir = vault_dir / "grok_bridge"
    grok_dir.mkdir(parents=True)

    (vault_dir / "shared_hub_manifest.json").write_text("{}", encoding="utf-8")
    (vault_dir / "mcp_shared_hub_config.json").write_text("{}", encoding="utf-8")
    (grok_dir / "grok_workspace_bundle.md").write_text("# Bundle", encoding="utf-8")

    pool_json = tmp_path / "shared_gemini_pool.json"
    pool_json.write_text("{}", encoding="utf-8")

    scale = IoTFederatedMemoryScale(
        vault_dir=str(vault_dir),
        harvester_pool_path=str(pool_json),
    )
    report = scale.evaluate_current_and_future()

    assert report["completed_foundation_score"] == 100.0
    assert report["composite_iot_scale_score"] >= 90.0
    assert "L5:" in report["readiness_tier"]
    assert len(report["dimensions"]) == 6
    assert len(report["future_iot_roadmap"]) == 4
