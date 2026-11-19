"""Comprehensive unit tests for iot_federated_agent_memory.node_studio_engine."""

from __future__ import annotations

import base64
import json

import pytest

from iot_federated_agent_memory.node_studio_engine import (
    ALL_ASPECT_RATIOS,
    FILTER_PRESETS,
    MAX_REFERENCES,
    MODALITY_SPECS,
    MODEL_SPECS,
    NANOGPT_CHAT_URL,
    NANOGPT_IMAGES_URL,
    NANOGPT_VIDEO_URL,
    apply_node_filters,
    build_contents,
    build_text_context_prompt,
    build_timeline_sequence,
    derive_generation_mode,
    get_default_studio_state,
    get_model_spec,
    get_node_studio_health,
    handle_node_studio_filter,
    handle_node_studio_generate,
)


def test_model_and_modality_registry_completeness():
    assert list(MODALITY_SPECS.keys()) == ["image", "text", "video"]

    # Image models & bidirectional NanoGPT aliases
    img_default = get_model_spec("nano-banana-2.1")
    assert img_default["id"] == "gemini-nano-banana-2.1"
    assert img_default["nanogptModel"] == "nano-banana-2.1"
    assert img_default["creditCost"] == pytest.approx(0.20)
    assert img_default["maxReferences"] == 14
    assert img_default["thinkingLevels"] == ["minimal", "medium", "high"]
    assert img_default["webGrounding"] is True
    assert img_default["imageSearchGrounding"] is True
    for ratio in ("1:4", "4:1", "1:8", "8:1", "21:9"):
        assert ratio in img_default["aspects"]
        assert ratio in ALL_ASPECT_RATIOS

    assert get_model_spec("nano-banana-pro")["id"] == "gemini-3-pro-image"
    assert MODEL_SPECS["gemini-3-pro-image"]["creditCost"] == pytest.approx(0.50)
    assert get_model_spec("nano-banana-2")["id"] == "gemini-3.1-flash-image"
    assert MODEL_SPECS["gemini-3.1-flash-image"]["resolutions"] == ["512", "1K", "2K", "4K"]
    assert MODEL_SPECS["gemini-3.1-flash-image"]["creditCost"] == pytest.approx(0.15)
    assert get_model_spec("nano-banana-2-lite")["id"] == "gemini-3.1-flash-lite-image"
    assert MODEL_SPECS["gemini-3.1-flash-lite-image"]["resolutions"] == ["1K"]
    assert MODEL_SPECS["gemini-3.1-flash-lite-image"]["creditCost"] == pytest.approx(0.08)

    # Text models
    txt_default = get_model_spec(None, modality="text")
    assert txt_default["id"] == "nanogpt/TEE/deepseek-v4.1-flash"
    assert txt_default["contextWindow"] == 128000
    assert txt_default["teeAttested"] is True
    assert txt_default["creditCost"] == pytest.approx(0.08)
    assert MODEL_SPECS["gemini-3.1-pro"]["creditCost"] == pytest.approx(0.15)
    assert MODEL_SPECS["nanogpt/Gemma-4-31B-Gembrain-uncensored-heretic"]["creditCost"] == pytest.approx(0.10)

    # Video models
    vid_default = get_model_spec(None, modality="video")
    assert vid_default["id"] == "ltx-video"
    assert vid_default["fpsOptions"] == [24, 60]
    assert vid_default["audioSync"] is True
    assert vid_default["creditCost"] == pytest.approx(0.40)
    assert MODEL_SPECS["kling-1.6"]["creditCost"] == pytest.approx(0.60)
    assert MODEL_SPECS["nanogpt-video"]["creditCost"] == pytest.approx(0.35)


def test_derive_generation_mode():
    assert derive_generation_mode(None) == "GENERATE"
    assert derive_generation_mode([]) == "GENERATE"
    assert derive_generation_mode(["", None]) == "GENERATE"
    assert derive_generation_mode(["01"]) == "EDIT"
    assert derive_generation_mode(["01", "01"]) == "EDIT"
    assert derive_generation_mode(["01", "02"]) == "MERGE"
    assert derive_generation_mode(["01", "02", "03"]) == "MERGE"


def test_edit_branch_inherits_history_signature_and_filters():
    parent = {
        "id": "01",
        "type": "morphingNode",
        "data": {
            "type": "GENERATED",
            "modality": "image",
            "label": "[01 · GENERATED]",
            "filters": {
                "kodak_2383": {"id": "kodak_2383", "enabled": True, "value": 92, "unit": "%", "type": "range"},
                "halation": {"id": "halation", "enabled": True, "value": 45, "unit": "%", "type": "range"},
            },
            "content": {"text": "Root shot", "base64": "AAAA", "mimeType": "image/png"},
            "metadata": {
                "thoughtSignature": "sig_parent_xyz",
                "conversationHistory": ["User: Root prompt", "AssistantThought: sig_parent_xyz"],
            },
        },
    }

    resp = handle_node_studio_generate(
        {
            "prompt": "Add warm sodium backlight",
            "modality": "image",
            "selectedNodeIds": ["01"],
            "parentNodes": [parent],
            "shortId": "a1b2",
        },
        headers={},
        env={},
    )
    assert resp["ok"] is True
    assert resp["mode"] == "EDIT"
    child = resp["node"]
    assert child["id"] == "01.a1b2"
    assert child["data"]["type"] == "EDITED"
    assert child["data"]["filters"]["kodak_2383"]["value"] == 92
    assert child["data"]["filters"]["halation"]["value"] == 45
    meta = child["data"]["metadata"]
    assert meta["conversationHistory"][:2] == ["User: Root prompt", "AssistantThought: sig_parent_xyz"]
    assert "User: Add warm sodium backlight" in meta["conversationHistory"]
    assert meta["thoughtSignature"].startswith("sig_offline_")
    assert resp["edges"] == [{"id": "e-01-01.a1b2", "source": "01", "target": "01.a1b2", "kind": "edit"}]


def test_merge_mode_edges_and_drag_ordered_references_capped_at_14():
    refs = [{"id": f"drag-{i}", "name": f"ref_{i}.png", "type": "image"} for i in range(18)]
    resp = handle_node_studio_generate(
        {
            "prompt": "Composite scene from nodes 01, 02, 03",
            "modality": "image",
            "selectedNodeIds": ["01", "02", "03"],
            "references": refs,
            "shortId": "m99",
        },
        headers={},
        env={},
    )
    assert resp["ok"] is True
    assert resp["mode"] == "MERGE"
    node = resp["node"]
    assert node["id"] == "merge-m99"
    assert node["data"]["type"] == "MERGED"
    assert len(resp["edges"]) == 3
    assert [(e["source"], e["target"], e["kind"]) for e in resp["edges"]] == [
        ("01", "merge-m99", "merge"),
        ("02", "merge-m99", "merge"),
        ("03", "merge-m99", "merge"),
    ]
    saved_refs = node["data"]["metadata"]["references"]
    assert len(saved_refs) == MAX_REFERENCES
    assert [r["id"] for r in saved_refs] == [f"drag-{i}" for i in range(14)]


def test_non_destructive_filters_across_all_modalities():
    assert set(FILTER_PRESETS["image"].keys()) == {
        "kodak_2383",
        "halation",
        "film_grain_16mm",
        "anamorphic_streak",
        "soop_dirty_ink",
    }
    assert set(FILTER_PRESETS["text"].keys()) == {"wga_tighten", "fact_lock", "eli12_strip"}
    assert set(FILTER_PRESETS["video"].keys()) == {
        "optical_flow_60fps",
        "temporal_deflicker",
        "j_cut_dialogue_duck",
    }

    # Image clamping & non-mutation
    raw_img_node = {
        "id": "03",
        "data": {"modality": "image", "content": {"text": "raw frame", "base64": "XYZ"}},
    }
    filtered_img = apply_node_filters(
        raw_img_node,
        {"kodak_2383": 140, "halation": -10, "anamorphic_streak": True, "soop_dirty_ink": True},
        modality="image",
    )
    assert "filters" not in raw_img_node["data"]
    assert filtered_img["data"]["filters"]["kodak_2383"]["value"] == 100
    assert filtered_img["data"]["filters"]["halation"]["value"] == 0
    assert filtered_img["data"]["filterSummary"]["anamorphicStreak"] is True
    assert filtered_img["data"]["filterSummary"]["soopDirtyInk"] is True
    assert filtered_img["data"]["content"]["base64"] == "XYZ"

    # Bypass leaves configured values intact while clearing active output
    bypassed = apply_node_filters(filtered_img, bypass=True)
    assert bypassed["data"]["filtersBypassed"] is True
    assert bypassed["data"]["filters"]["kodak_2383"]["value"] == 100
    assert bypassed["data"]["filterSummary"]["cssFilter"] == "none"

    # Text prose filters preserve raw text while clamping WGA preview to <=4 lines/beat
    six_lines = "\n".join(f"Line {i}: cryptographic orchestration deterministic" for i in range(1, 7))
    raw_txt_node = {"id": "t1", "data": {"modality": "text", "content": {"text": six_lines}}}
    filtered_txt = apply_node_filters(
        raw_txt_node,
        {"wga_tighten": {"enabled": True, "value": 9}, "fact_lock": True, "eli12_strip": True},
        modality="text",
    )
    assert filtered_txt["data"]["content"]["text"] == six_lines
    assert filtered_txt["data"]["filters"]["wga_tighten"]["value"] == 4
    preview_lines = filtered_txt["data"]["filterSummary"]["filteredPreview"].splitlines()
    assert len(preview_lines) == 4
    assert "lock-box" in preview_lines[0]

    # Video temporal filters
    vid_res = handle_node_studio_filter(
        {"nodeId": "04", "modality": "video", "filters": {"optical_flow_60fps": 60, "j_cut_dialogue_duck": -14.0}}
    )
    assert vid_res["ok"] is True
    assert vid_res["filterSummary"]["outputFps"] == 60
    assert vid_res["filterSummary"]["dialogueDuckLufs"] == pytest.approx(-14.0)


def test_build_timeline_sequence_on_default_5_node_dag():
    state = get_default_studio_state("image")
    timeline = build_timeline_sequence(state["nodes"], state["edges"])
    assert timeline["timecodes"] == ["00:00", "00:03", "00:06", "00:09"]
    assert [stage["nodeId"] for stage in timeline["stages"]] == ["01", "03", "04", "05"]
    assert timeline["stages"][2]["mergedParentIds"] == ["02"]
    assert len(timeline["stages"][0]["sparkline"]) == 8
    assert len(timeline["stages"][0]["activeFilters"]) >= 1
    assert "00:00 [#01] -> 00:03 [#03] -> 00:06 [#04] -> 00:09 [#05]" == timeline["summary"]


def test_default_studio_states_for_all_three_modalities():
    for modality in ("image", "text", "video"):
        state = get_default_studio_state(modality)
        assert state["ok"] is True
        assert state["modality"] == modality
        assert len(state["nodes"]) == 5
        assert len(state["edges"]) == 4
        assert len(state["telemetry"]) == 4
        assert state["timeline"]["timecodes"] == ["00:00", "00:03", "00:06", "00:09"]
        assert state["spaceTree"]["root"] == f"~/space/nodes/{modality}"
        assert len(state["spaceTree"]["lines"]) > 5


def test_health_and_validation_errors():
    health_none = get_node_studio_health(headers={}, env={})
    assert health_none["ok"] is True
    assert health_none["hasServerKey"] is False
    assert health_none["hasGeminiKey"] is False
    assert health_none["hasNanogptKey"] is False
    assert health_none["modalities"] == ["text", "image", "video"]
    assert "gemini-nano-banana-2.1" in health_none["models"]

    health_hdr = get_node_studio_health(
        headers={"X-NanoGPT-Api-Key": "ngpt-secret", "X-Gemini-Api-Key": "gem-secret"},
        env={},
    )
    assert health_hdr["hasServerKey"] is True
    assert health_hdr["hasGeminiKey"] is True
    assert health_hdr["hasNanogptKey"] is True
    assert "ngpt-secret" not in json.dumps(health_hdr)

    bad = handle_node_studio_generate({"prompt": "   "}, headers={}, env={})
    assert bad["ok"] is False
    assert bad["statusCode"] == 400


def test_all_three_modalities_synthetic_morphing_generation():
    for modality in ("text", "image", "video"):
        resp = handle_node_studio_generate(
            {"prompt": f"Test {modality} generation", "modality": modality},
            headers={},
            env={},
        )
        assert resp["ok"] is True
        assert resp["modality"] == modality
        assert resp["mode"] == "GENERATE"
        node = resp["node"]
        assert node["data"]["morphingTransitions"] == ["generating", "message", modality]
        assert node["data"]["morphingStatus"] == modality
        assert resp["result"]["offline"] is True


def test_live_nanogpt_routing_with_mocked_http():
    calls = []

    def fake_post(url, headers, payload):
        calls.append((url, headers, payload))
        if url == NANOGPT_IMAGES_URL:
            raw_b64 = base64.b64encode(b"\x89PNG\r\n\x1a\nfake").decode("ascii")
            return 200, {"data": [{"b64_json": raw_b64}]}
        if url == NANOGPT_CHAT_URL:
            return 200, {"choices": [{"message": {"content": "TEE verified response"}}]}
        if url == NANOGPT_VIDEO_URL:
            return 200, {"videoUrl": "https://cdn.nanogpt.test/clip.mp4"}
        raise AssertionError(f"Unexpected URL: {url}")

    # Image via NanoGPT
    img_res = handle_node_studio_generate(
        {
            "prompt": "Panoramic dusk studio",
            "modality": "image",
            "config": {
                "provider": "nanogpt",
                "model": "gemini-nano-banana-2.1",
                "aspectRatio": "21:9",
                "resolution": "4K",
                "thinkingLevel": "high",
                "groundingMode": "Web+Img",
            },
            "references": [{"id": "r1", "base64": "AAAA", "mimeType": "image/png"}],
        },
        headers={"X-NanoGPT-Api-Key": "ngpt-key"},
        env={},
        http_post=fake_post,
    )
    assert img_res["ok"] is True
    assert img_res["result"]["providerUsed"] == "nanogpt"
    assert img_res["result"]["modelUsed"] == "nano-banana-2.1"
    sent_url, sent_hdrs, sent_body = calls[0]
    assert sent_url == NANOGPT_IMAGES_URL
    assert sent_hdrs["Authorization"] == "Bearer ngpt-key"
    assert sent_body["aspect_ratio"] == "21:9"
    assert sent_body["resolution"] == "2k"
    assert sent_body["thinking_level"] == "high"
    assert sent_body["enable_web_search"] is True
    assert sent_body["input_references"] == ["data:image/png;base64,AAAA"]

    # Non-image reference rejected cleanly on NanoGPT image endpoint
    bad_ref = handle_node_studio_generate(
        {
            "prompt": "Analyze PDF",
            "modality": "image",
            "config": {"provider": "nanogpt"},
            "references": [{"id": "pdf1", "base64": "JVBERi0", "mimeType": "application/pdf"}],
        },
        env={"NANOGPT_API_KEY": "ngpt-key"},
        http_post=fake_post,
    )
    assert bad_ref["ok"] is False
    assert bad_ref["statusCode"] == 400

    # Text via NanoGPT TEE
    txt_res = handle_node_studio_generate(
        {
            "prompt": "Tighten scene",
            "modality": "text",
            "config": {"provider": "nanogpt", "model": "nanogpt/TEE/deepseek-v4.1-flash"},
        },
        env={"NANOGPT_API_KEY": "ngpt-key"},
        http_post=fake_post,
    )
    assert txt_res["ok"] is True
    assert txt_res["result"]["text"] == "TEE verified response"

    # Video via NanoGPT LTX-Video
    vid_res = handle_node_studio_generate(
        {
            "prompt": "Animate dolly shot",
            "modality": "video",
            "config": {"provider": "nanogpt", "model": "ltx-video", "fps": 60, "audioSync": True},
        },
        env={"NANOGPT_API_KEY": "ngpt-key"},
        http_post=fake_post,
    )
    assert vid_res["ok"] is True
    assert vid_res["node"]["data"]["content"]["videoUrl"] == "https://cdn.nanogpt.test/clip.mp4"


def test_auto_mode_gemini_429_fallback_to_nanogpt():
    visited_urls = []

    def fake_post(url, headers, payload):
        visited_urls.append(url)
        if "generativelanguage.googleapis.com" in url:
            return 429, {"error": {"message": "RESOURCE_EXHAUSTED quota exceeded"}}
        if url == NANOGPT_IMAGES_URL:
            raw_b64 = base64.b64encode(b"\x89PNG\r\n\x1a\nfallback").decode("ascii")
            return 200, {"data": [{"b64_json": raw_b64}]}
        raise AssertionError(f"Unexpected URL: {url}")

    resp = handle_node_studio_generate(
        {
            "prompt": "Fallback test",
            "modality": "image",
            "config": {"provider": "auto", "model": "gemini-nano-banana-2.1"},
        },
        env={"GEMINI_API_KEY": "gem-key", "NANOGPT_API_KEY": "ngpt-key"},
        http_post=fake_post,
    )
    assert resp["ok"] is True
    assert len(visited_urls) == 2
    assert resp["result"]["providerUsed"] == "nanogpt"
    assert resp["result"]["fallbackFrom"] == "gemini"
    assert resp["node"]["data"]["metadata"]["fallbackFrom"] == "gemini"


def test_conversation_history_builders_preserve_thought_signatures():
    signed_contents = build_contents(
        ["User: first", "AssistantImage: sig_abc|||caption"],
        requires_thought_signature=True,
        current_parts=[{"text": "next edit"}],
    )
    assert signed_contents[1]["parts"] == [{"thoughtSignature": "sig_abc"}]
    assert signed_contents[-1] == {"role": "user", "parts": [{"text": "next edit"}]}

    unsigned_contents = build_contents(
        ["User: first", "Assistant: legacy unsigned"],
        requires_thought_signature=True,
        current_parts=[{"text": "next edit"}],
    )
    assert len(unsigned_contents) == 2
    assert unsigned_contents[0]["role"] == "user"
    assert "legacy unsigned" in unsigned_contents[0]["parts"][0]["text"]

    briefing = build_text_context_prompt(
        "new prompt",
        ["User: u1", "Assistant: a1", "User: u2", "Assistant: a2"],
    )
    assert "Context from previous turns:" in briefing
    assert "Current instruction: new prompt" in briefing


def test_merge_two_data_url_images_with_nano_banana_2_extracts_both_refs():
    captured = {}

    def fake_post(url, headers, payload):
        captured["url"] = url
        captured["payload"] = payload
        return 200, {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Dog floating in space"},
                            {"inlineData": {"data": "TUVSR0VE", "mimeType": "image/png"}},
                        ]
                    }
                }
            ]
        }

    resp = handle_node_studio_generate(
        {
            "prompt": "Put this dog in space",
            "modality": "image",
            "selectedNodeIds": ["img-dog", "img-space"],
            "references": [
                {"id": "img-dog", "name": "dog.png", "type": "image", "url": "data:image/png;base64,RE9H"},
                {"id": "img-space", "name": "space.jpg", "type": "image", "url": "data:image/jpeg;base64,U1BBQ0U="},
            ],
            "config": {"model": "gemini-3.1-flash-image", "provider": "gemini"},
        },
        env={"GEMINI_API_KEY": "gem-key"},
        http_post=fake_post,
    )
    assert resp["ok"] is True
    assert resp["mode"] == "MERGE"
    assert resp["modality"] == "image"
    assert "gemini-3.1-flash-image:generateContent" in captured["url"]
    parts = captured["payload"]["contents"][-1]["parts"]
    inline_parts = [p["inlineData"] for p in parts if "inlineData" in p]
    assert len(inline_parts) == 2
    assert inline_parts[0]["data"] == "RE9H"
    assert inline_parts[1]["data"] == "U1BBQ0U="
    assert inline_parts[1]["mimeType"] == "image/jpeg"
    assert resp["node"]["data"]["content"]["imageUrl"] == "data:image/png;base64,TUVSR0VE"


def test_text_modality_with_text_and_image_references_nanogpt():
    captured = {}

    def fake_post(url, headers, payload):
        captured["url"] = url
        captured["payload"] = payload
        return 200, {"choices": [{"message": {"content": "Refined scene prompt with dog astronaut."}}]}

    resp = handle_node_studio_generate(
        {
            "prompt": "Combine these into a movie logline",
            "modality": "text",
            "selectedNodeIds": ["txt-1", "img-1"],
            "references": [
                {"id": "txt-1", "name": "Notes", "type": "text", "text": "A brave golden retriever."},
                {"id": "img-1", "name": "Nebula", "type": "image", "url": "data:image/png;base64,TkVCVUxB"},
            ],
            "config": {"model": "nanogpt/TEE/deepseek-v4.1-flash", "provider": "nanogpt"},
        },
        env={"NANOGPT_API_KEY": "ngpt-key"},
        http_post=fake_post,
    )
    assert resp["ok"] is True
    assert resp["modality"] == "text"
    assert captured["url"] == NANOGPT_CHAT_URL
    last_msg = captured["payload"]["messages"][-1]
    assert isinstance(last_msg["content"], list)
    assert "A brave golden retriever." in last_msg["content"][0]["text"]
    assert last_msg["content"][1]["image_url"]["url"] == "data:image/png;base64,TkVCVUxB"
