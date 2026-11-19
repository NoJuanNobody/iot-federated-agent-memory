"""Unit tests for Omni-Modal Node Studio Engine (text, image, video, audio, atlas, 3d) and Unified Slash-Command Router."""

from __future__ import annotations

import pytest

from iot_federated_agent_memory.node_studio_engine import (
    AEONIK_SPARKLINE_BARS,
    MODALITIES,
    MODALITY_SPECS,
    MODEL_SPECS,
    apply_node_filters,
    get_default_studio_state,
    get_model_spec,
    get_node_studio_health,
    handle_node_studio_filter,
    handle_node_studio_generate,
    infer_modality,
    parse_omni_slash_command,
)


def test_omnimodal_registry_and_specs():
    assert MODALITIES == ("text", "image", "video", "audio", "atlas", "3d")
    for mod in MODALITIES:
        assert mod in MODALITY_SPECS

    # Audio modality spec & models
    audio_spec = MODALITY_SPECS["audio"]
    assert audio_spec["defaultModel"] == "google/lyria-3.5"
    assert audio_spec["models"] == [
        "google/lyria-3.5",
        "elevenlabs/eleven-v4",
        "elevenlabs/sound-effects/v3",
        "kokoro-82m",
    ]
    for mid in audio_spec["models"]:
        assert mid in MODEL_SPECS
        assert MODEL_SPECS[mid]["modality"] == "audio"
        assert infer_modality(mid) == "audio"

    # Atlas modality spec & models
    atlas_spec = MODALITY_SPECS["atlas"]
    assert atlas_spec["defaultModel"] == "worldlabs/posedImages2Splats"
    assert atlas_spec["models"] == [
        "worldlabs/images2PosedRGBD",
        "worldlabs/posedImages2Splats",
        "worldlabs/atlasGenerate",
        "worldlabs/splats2Mesh",
        "worldlabs/atlasChisel",
        "worldlabs/atlasTextToImage",
    ]
    for mid in atlas_spec["models"]:
        assert mid in MODEL_SPECS
        assert MODEL_SPECS[mid]["modality"] == "atlas"
        assert infer_modality(mid) == "atlas"

    # 3D modality spec & models
    m3d_spec = MODALITY_SPECS["3d"]
    assert m3d_spec["defaultModel"] == "hyper3d/rodin-v2.5"
    assert m3d_spec["models"] == [
        "hyper3d/rodin-v2.5",
        "tripo3d/h3.0",
        "meshy/v7.1/image-to-3d",
        "worldlabs/splats2Mesh",
        "hyper3d/rigging",
    ]
    for mid in ("hyper3d/rodin-v2.5", "tripo3d/h3.0", "meshy/v7.1/image-to-3d", "hyper3d/rigging"):
        assert mid in MODEL_SPECS
        assert MODEL_SPECS[mid]["modality"] == "3d"
        assert infer_modality(mid) == "3d"

    assert get_model_spec(None, modality="audio")["id"] == "google/lyria-3.5"
    assert get_model_spec(None, modality="atlas")["id"] == "worldlabs/posedImages2Splats"
    assert get_model_spec(None, modality="3d")["id"] == "hyper3d/rodin-v2.5"

    health = get_node_studio_health(headers={}, env={"WLT_API_KEY": "wlt-secret"})
    assert health["ok"] is True
    assert health["hasWorldlabsKey"] is True
    for mod in ("text", "image", "video", "audio", "atlas", "3d"):
        assert mod in health["modalities"]
        assert mod in health["modalitySpecs"]


def test_parse_omni_slash_command_atlas_subcommands_and_flags():
    splat = parse_omni_slash_command(
        "/atlas splat --views 14 --res 1280x720 --mesh --rig walk --fps 24 --mux #N3 Mossy torii gate at dusk"
    )
    assert splat["is_slash"] is True
    assert splat["command"] == "atlas"
    assert splat["subcommand"] == "splat"
    assert splat["modality"] == "atlas"
    assert splat["provider"] == "worldlabs"
    assert splat["model"] == "worldlabs/posedImages2Splats"
    assert splat["atlas_task"] == "posedImages2Splats"
    assert splat["flags"]["views"] == 14
    assert splat["flags"]["res"] == [1280, 720]
    assert splat["flags"]["mesh"] is True
    assert splat["flags"]["rig"] == "walk"
    assert splat["flags"]["fps"] == 24
    assert splat["flags"]["mux"] == "#N3"
    assert splat["prompt"] == "Mossy torii gate at dusk"
    assert splat["pill_label"] == "● /atlas splat"

    pose = parse_omni_slash_command("/atlas pose --ref /images/torii_01.jpg /images/torii_01.jpg")
    assert pose["command"] == "atlas"
    assert pose["subcommand"] == "pose"
    assert pose["atlas_task"] == "images2PosedRGBD"
    assert pose["model"] == "worldlabs/images2PosedRGBD"
    assert pose["target_path"] == "/images/torii_01.jpg"
    assert pose["flags"]["ref"] == "/images/torii_01.jpg"
    assert pose["pill_label"] == "● /atlas pose"

    fly = parse_omni_slash_command("/flythrough --fps 24 --seconds 6 Push through bamboo archway")
    assert fly["command"] == "atlas"
    assert fly["subcommand"] == "flythrough"
    assert fly["atlas_task"] == "atlasGenerate"
    assert fly["model"] == "worldlabs/atlasGenerate"
    assert fly["flags"]["fps"] == 24
    assert fly["flags"]["seconds"] == 6
    assert fly["prompt"] == "Push through bamboo archway"

    mesh = parse_omni_slash_command("/atlas mesh /worlds/torii_3e78434c/refinedSplats_2000000.spz")
    assert mesh["subcommand"] == "mesh"
    assert mesh["atlas_task"] == "splats2Mesh"
    assert mesh["model"] == "worldlabs/splats2Mesh"
    assert mesh["target_path"] == "/worlds/torii_3e78434c/refinedSplats_2000000.spz"

    chisel = parse_omni_slash_command("/atlas chisel Brutalist courtyard blockout")
    assert chisel["subcommand"] == "chisel"
    assert chisel["atlas_task"] == "atlasChisel"
    assert chisel["model"] == "worldlabs/atlasChisel"

    t2i = parse_omni_slash_command("/atlas text2img Wide desert observatory")
    assert t2i["subcommand"] == "text2img"
    assert t2i["atlas_task"] == "atlasTextToImage"
    assert t2i["model"] == "worldlabs/atlasTextToImage"


def test_parse_omni_slash_command_audio_3d_rig_video_image_text_mux():
    aud_music = parse_omni_slash_command("/audio music --model google/lyria-3.5 Modular synth rain score")
    assert aud_music["is_slash"] is True
    assert aud_music["command"] == "audio"
    assert aud_music["subcommand"] == "music"
    assert aud_music["modality"] == "audio"
    assert aud_music["provider"] == "nanogpt"
    assert aud_music["model"] == "google/lyria-3.5"
    assert aud_music["prompt"] == "Modular synth rain score"
    assert aud_music["pill_label"] == "♪ /audio music"

    aud_tts = parse_omni_slash_command("/audio tts --tts eleven-v4 Welcome to the bunker")
    assert aud_tts["subcommand"] == "tts"
    assert aud_tts["model"] == "elevenlabs/eleven-v4"
    assert aud_tts["flags"]["tts"] == "eleven-v4"
    assert aud_tts["pill_label"] == "♪ /audio tts"

    aud_sfx = parse_omni_slash_command("/audio sfx Thunder and gravel footsteps")
    assert aud_sfx["subcommand"] == "sfx"
    assert aud_sfx["model"] == "elevenlabs/sound-effects/v3"

    rodin = parse_omni_slash_command("/rodin --tier Detail --rig walk Brutalist mech sentinel")
    assert rodin["command"] == "3d"
    assert rodin["modality"] == "3d"
    assert rodin["provider"] == "hyper3d"
    assert rodin["model"] == "hyper3d/rodin-v2.5"
    assert rodin["flags"]["tier"] == "Detail"
    assert rodin["flags"]["rig"] == "walk"
    assert rodin["prompt"] == "Brutalist mech sentinel"

    rig = parse_omni_slash_command("/rig --engine hyper3d/rigging --anim walk /models3d/sentinel.glb")
    assert rig["command"] == "rig"
    assert rig["modality"] == "3d"
    assert rig["provider"] == "hyper3d"
    assert rig["model"] == "hyper3d/rigging"
    assert rig["flags"]["anim"] == "walk"
    assert rig["target_path"] == "/models3d/sentinel.glb"
    assert rig["pill_label"] == "◆ /rig"

    vid = parse_omni_slash_command("/video kling-4.0 --fps 24 --seconds 5 Neon rain dolly shot")
    assert vid["command"] == "video"
    assert vid["modality"] == "video"
    assert vid["model"] == "kling-4.0"
    assert vid["flags"]["fps"] == 24
    assert vid["flags"]["seconds"] == 5
    assert vid["prompt"] == "Neon rain dolly shot"

    img = parse_omni_slash_command("/nano --res 4K --aspect 21:9 Celadon ceramic monolith")
    assert img["command"] == "image"
    assert img["modality"] == "image"
    assert img["provider"] == "nanogpt"
    assert img["model"] == "gemini-nano-banana-2.1"
    assert img["flags"]["res"] == "4K"
    assert img["flags"]["aspect"] == "21:9"

    txt = parse_omni_slash_command("/gemini Summarize the RUB camera frustum alignment")
    assert txt["command"] == "text"
    assert txt["modality"] == "text"
    assert txt["provider"] == "gemini"
    assert txt["model"] == "gemini-3.1-pro"

    mux = parse_omni_slash_command("/mux --video /videos/orbit.mp4 --audio /audio/score.wav --lufs -14.0")
    assert mux["command"] == "mux"
    assert mux["modality"] == "video"
    assert mux["flags"]["lufs"] == pytest.approx(-14.0)
    assert mux["target_path"] == "/videos/orbit.mp4"

    plain = parse_omni_slash_command("Plain natural language prompt without slash")
    assert plain["is_slash"] is False
    assert plain["prompt"] == "Plain natural language prompt without slash"


def test_handle_node_studio_generate_slash_routing_and_omnimodal_outputs():
    sparkline_str = "".join(AEONIK_SPARKLINE_BARS)
    assert sparkline_str == "│┃│┃┃│┃┃"

    # 1. /atlas splat route
    atlas_resp = handle_node_studio_generate(
        {
            "prompt": "/atlas splat --views 14 --res 1280x720 --mesh Mossy torii gate at dusk",
            "shortId": "atl1",
        },
        headers={},
        env={},
    )
    assert atlas_resp["ok"] is True
    assert atlas_resp["modality"] == "atlas"
    assert atlas_resp["slashRoute"]["command"] == "atlas"
    assert atlas_resp["slashRoute"]["atlas_task"] == "posedImages2Splats"
    atl_node = atlas_resp["node"]
    atl_content = atl_node["data"]["content"]
    atl_meta = atl_node["data"]["metadata"]
    assert atl_content["sparkline"] == "│┃│┃┃│┃┃"
    assert atl_content["coordSystem"] == "RUB"
    assert atl_content["fx"] == pytest.approx(893.37)
    assert atl_content["fy"] == pytest.approx(893.90)
    assert atl_content["cx"] == pytest.approx(640.0)
    assert atl_content["cy"] == pytest.approx(360.5)
    assert atl_content["centroidWorld"] == [-1.99, 0.0, -36.35]
    assert atl_content["spzPath"].endswith(".spz")
    assert atl_content["exrPath"].endswith(".exr")
    assert atl_content["glbPath"].endswith(".glb")
    assert atl_content["mp4Path"].endswith(".mp4")
    assert atl_meta["operationId"].startswith("op_atlas_")
    assert atl_meta["slashRoute"]["pill_label"] == "● /atlas splat"

    # 2. /audio music route
    audio_resp = handle_node_studio_generate(
        {
            "prompt": "/audio music --model google/lyria-3.5 Modular synth rain score",
            "shortId": "aud1",
        },
        headers={},
        env={},
    )
    assert audio_resp["ok"] is True
    assert audio_resp["modality"] == "audio"
    assert audio_resp["slashRoute"]["command"] == "audio"
    assert audio_resp["slashRoute"]["subcommand"] == "music"
    aud_content = audio_resp["node"]["data"]["content"]
    assert aud_content["sparkline"] == "│┃│┃┃│┃┃"
    assert aud_content["wavPath"].endswith(".wav")
    assert aud_content["mimeType"] == "audio/wav"
    assert aud_content["lufs"] == pytest.approx(-14.0)

    # 3. /3d & /rig route
    rig_resp = handle_node_studio_generate(
        {
            "prompt": "/rig --engine hyper3d/rigging --anim walk /models3d/sentinel.glb",
            "shortId": "rig1",
        },
        headers={},
        env={},
    )
    assert rig_resp["ok"] is True
    assert rig_resp["modality"] == "3d"
    assert rig_resp["slashRoute"]["command"] == "rig"
    rig_content = rig_resp["node"]["data"]["content"]
    assert rig_content["glbPath"].endswith(".glb")
    assert rig_content["rigged"] is True
    assert rig_content["animation"] == "walk"
    assert rig_content["sparkline"] == "│┃│┃┃│┃┃"

    # 4. Multi-parent Omni-World Master merge (#2 Atlas RGBD + #3 Audio -> #4 Omni-World Master)
    merge_resp = handle_node_studio_generate(
        {
            "prompt": "/atlas splat --mesh --mux #aud1 Composite Omni-World Master",
            "selectedNodeIds": [atl_node["id"], audio_resp["node"]["id"]],
            "parentNodes": [atl_node, audio_resp["node"]],
            "shortId": "mstr",
        },
        headers={},
        env={},
    )
    assert merge_resp["ok"] is True
    assert merge_resp["mode"] == "MERGE"
    m_node = merge_resp["node"]
    assert "OMNI-WORLD MASTER" in m_node["data"]["label"]
    m_content = m_node["data"]["content"]
    assert m_content["omniWorldMaster"] is True
    assert m_content["spzPath"].endswith(".spz")
    assert m_content["exrPath"].endswith(".exr")
    assert m_content["glbPath"].endswith(".glb")
    assert m_content["wavPath"].endswith(".wav")
    assert m_content["mp4Path"].endswith(".mp4")
    assert len(merge_resp["edges"]) == 2


def test_default_studio_states_and_filters_for_audio_atlas_3d():
    for modality in ("audio", "atlas", "3d"):
        state = get_default_studio_state(modality)
        assert state["ok"] is True
        assert state["modality"] == modality
        assert len(state["nodes"]) == 5
        assert len(state["edges"]) == 4
        assert state["spaceTree"]["root"] == f"~/space/nodes/{modality}"

    aud_filter = handle_node_studio_filter(
        {"nodeId": "05", "modality": "audio", "filters": {"lufs_master": -14.0, "dialogue_deess": 55}}
    )
    assert aud_filter["ok"] is True
    assert aud_filter["filterSummary"]["targetLufs"] == pytest.approx(-14.0)
    assert aud_filter["filterSummary"]["sparkline"] == "│┃│┃┃│┃┃"

    atl_node = {"id": "a1", "data": {"modality": "atlas", "content": {"text": "torii splat"}}}
    filtered_atl = apply_node_filters(atl_node, {"splat_density": 100, "rub_frustum_lock": True}, modality="atlas")
    assert filtered_atl["data"]["filterSummary"]["coordSystem"] == "RUB"
    assert filtered_atl["data"]["filterSummary"]["splatCount"] == 2000000
    assert filtered_atl["data"]["filterSummary"]["depthConfidencePct"] == pytest.approx(98.4)
