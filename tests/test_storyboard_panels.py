"""
Tests for TinCan 2.2 Zen Storyboard Panels & Manifest Refresh.
Verifies:
1. audio_drama_manifest.json structure, preserved timings, and Zen metadata.
2. Existence and valid PNG dimensions of all 6 refreshed panels and zen_storyboard_contact_sheet.png.
3. Existence and Zen token content of storyboard_viewer.html and zen_storyboard_contact_sheet.svg.
"""

import os
import json
import pytest
from PIL import Image

REPO_ROOT = "/Users/alejandrolondono/dev/iot-federated-agent-memory/.worktrees/storyboard-panels"
PANELS_DIR = os.path.join(REPO_ROOT, "docs/panels")
MANIFEST_PATH = os.path.join(PANELS_DIR, "audio_drama_manifest.json")
VIEWER_PATH = os.path.join(PANELS_DIR, "storyboard_viewer.html")
CONTACT_PNG_PATH = os.path.join(PANELS_DIR, "zen_storyboard_contact_sheet.png")
CONTACT_SVG_PATH = os.path.join(PANELS_DIR, "zen_storyboard_contact_sheet.svg")

EXPECTED_SCENE_IDS = [
    ("panel_01_cyber_lab_crt", "panel_01_zen_sanctuary", 715, 0.0, 29.792),
    ("panel_02_kokoro_voice_alert", "panel_02_kokoro_whisper", 636, 29.792, 26.5),
    ("panel_03_toronto_loft_tofu", "panel_03_toronto_loft_tofu", 591, 56.292, 24.625),
    ("panel_04_webrtc_capsule_flight", "panel_04_webrtc_capsule_flight", 740, 80.917, 30.833),
    ("panel_05_ai_brain_arena", "panel_05_ai_brain_arena", 701, 111.75, 29.208),
    ("panel_06_tier_l5_messiah_gold", "panel_06_l5_mesh_sovereign", 773, 140.958, 32.208),
]


def test_manifest_structure_and_timings():
    assert os.path.exists(MANIFEST_PATH), f"Manifest missing at {MANIFEST_PATH}"
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Core keys preserved
    assert manifest["total_frames"] == 4156
    assert manifest["total_seconds"] == pytest.approx(173.167, rel=1e-3)
    assert manifest["total_ticks"] == 43987104000000
    assert "master_audio" in manifest
    assert os.path.exists(manifest["master_audio"])

    # Zen metadata additions
    assert "design_system" in manifest
    assert "TinCan 2.2 Zen" in manifest["design_system"]
    assert "contact_sheet" in manifest and os.path.exists(manifest["contact_sheet"])
    assert "contact_sheet_svg" in manifest and os.path.exists(manifest["contact_sheet_svg"])
    assert "viewer" in manifest and os.path.exists(manifest["viewer"])

    scenes = manifest.get("scenes", [])
    assert len(scenes) == 6

    for idx, (exp_id, exp_zen_id, exp_frames, exp_start, exp_dur) in enumerate(EXPECTED_SCENE_IDS):
        sc = scenes[idx]
        assert sc["id"] == exp_id
        assert sc["zen_id"] == exp_zen_id
        assert sc["frames"] == exp_frames
        assert sc["start_sec"] == pytest.approx(exp_start, rel=1e-3)
        assert sc["duration_sec"] == pytest.approx(exp_dur, rel=1e-3)
        assert "audio_path" in sc and os.path.exists(sc["audio_path"])
        assert "title" in sc and len(sc["title"]) > 0
        assert "palette" in sc and len(sc["palette"]) >= 4
        assert "cpl_prompt" in sc and len(sc["cpl_prompt"]) > 10
        assert "zen_panel_path" in sc and os.path.exists(sc["zen_panel_path"])


def test_refreshed_panels_existence_and_dimensions():
    panel_files = [
        "panel_01_cyber_lab_crt.png",
        "panel_01_zen_sanctuary.png",
        "panel_02_kokoro_voice_alert.png",
        "panel_02_kokoro_whisper.png",
        "panel_03_toronto_loft_tofu.png",
        "panel_04_webrtc_capsule_flight.png",
        "panel_05_ai_brain_arena.png",
        "panel_06_tier_l5_messiah_gold.png",
        "panel_06_l5_mesh_sovereign.png",
    ]
    for pf in panel_files:
        p_path = os.path.join(PANELS_DIR, pf)
        assert os.path.exists(p_path), f"Panel missing: {pf}"
        with Image.open(p_path) as im:
            assert im.size == (1024, 576), f"Wrong size for {pf}: {im.size}"
            assert im.mode in ("RGB", "RGBA")


def test_contact_sheet_png_and_svg():
    assert os.path.exists(CONTACT_PNG_PATH), "Contact sheet PNG missing"
    with Image.open(CONTACT_PNG_PATH) as im:
        assert im.size[0] >= 1920
        assert im.size[1] >= 800
        assert im.mode in ("RGB", "RGBA")

    assert os.path.exists(CONTACT_SVG_PATH), "Contact sheet SVG missing"
    with open(CONTACT_SVG_PATH, "r", encoding="utf-8") as f:
        svg_content = f.read()
    assert "<svg" in svg_content
    assert "#0e0d0b" in svg_content  # Sumi
    assert "#ece6da" in svg_content  # Washi
    assert "#d0703f" in svg_content  # Kaki
    assert "TINCAN 2.2" in svg_content


def test_storyboard_viewer_html():
    assert os.path.exists(VIEWER_PATH), "Storyboard viewer HTML missing"
    with open(VIEWER_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    assert "<!DOCTYPE html>" in html
    assert "TinCan 2.2" in html
    assert "Shippori Mincho" in html
    assert "Zen Kaku Gothic New" in html
    assert "#0e0d0b" in html
    assert "#d0703f" in html
    assert "trailer_voiceover.wav" in html
    assert "panel_01_zen_sanctuary" in html
    assert "panel_06_l5_mesh_sovereign" in html
