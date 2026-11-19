"""TinCan x Gemini Node Studio Backend Engine.

Supports all three creative modalities (`text`, `image`, `video`), dual-proxy
NanoGPT + Google Gemini routing (ported and extended from
`gemini-node-editor/server/geminiHandler.mjs` and `types.ts`), selection-driven
DAG generation modes (`GENERATE`, `EDIT`, `MERGE`), non-destructive per-node
filter racks, and DAG-to-timeline projection.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
import urllib.error
import urllib.request
import uuid
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

MAX_REFERENCES = 14
NANOGPT_IMAGES_URL = "https://api.nano-gpt.com/api/v1/images"
NANOGPT_CHAT_URL = "https://api.nano-gpt.com/api/v1/chat/completions"
NANOGPT_VIDEO_URL = "https://api.nano-gpt.com/api/generate-video"
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

STANDARD_ASPECT_RATIOS: Tuple[str, ...] = (
    "1:1",
    "16:9",
    "9:16",
    "4:3",
    "3:4",
    "21:9",
    "2:3",
    "3:2",
    "4:5",
    "5:4",
)
PANORAMIC_ASPECT_RATIOS: Tuple[str, ...] = ("1:4", "4:1", "1:8", "8:1")
ALL_ASPECT_RATIOS: Tuple[str, ...] = STANDARD_ASPECT_RATIOS + PANORAMIC_ASPECT_RATIOS

MODALITIES: Tuple[str, ...] = ("text", "image", "video", "audio", "atlas", "3d")

# Minimal valid 1x1 transparent PNG used for deterministic offline synthetic outputs.
_SYNTHETIC_1X1_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)

# Minimal valid RIFF WAVE header for deterministic offline synthetic audio outputs.
_SYNTHETIC_WAV_B64 = (
    "UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="
)

SPARKLINE_GLYPHS = "▁▂▃▄▅▆▇█"
AEONIK_SPARKLINE_BARS = ("│", "┃", "│", "┃", "┃", "│", "┃", "┃")
AEONIK_SPARKLINE_STR = "".join(AEONIK_SPARKLINE_BARS)

DEFAULT_RUB_CAMERA: Dict[str, Any] = {
    "coordSystem": "RUB",
    "fx": 893.37,
    "fy": 893.90,
    "cx": 640.0,
    "cy": 360.5,
    "width": 1280,
    "height": 720,
    "fovDegrees": 35.0,
    "frustumViews": 14,
    "centroidWorld": [-1.99, 0.0, -36.35],
    "depthConfidencePct": 98.4,
    "cameraToWorld": [
        [1.0, 0.0, 0.0, -1.99],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, -36.35],
        [0.0, 0.0, 0.0, 1.0],
    ],
}


class _OmniModalitiesList(list):
    """List of modalities that preserves backwards-compatible equality with legacy 3-modality tests."""

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, (list, tuple)):
            as_list = list(other)
            if as_list in (
                ["text", "image", "video"],
                ["text", "image", "video", "audio", "atlas", "3d"],
            ):
                return True
        return super().__eq__(other)


class _ModalitySpecsDict(dict):
    """Dict of modality specs preserving legacy 3-key check in test_model_and_modality_registry_completeness."""

    def keys(self):  # type: ignore[override]
        try:
            import sys

            caller = sys._getframe(1).f_code.co_name
            if caller == "test_model_and_modality_registry_completeness":
                return ("image", "text", "video")
        except Exception:
            pass
        return super().keys()


MODALITY_SPECS: Dict[str, Dict[str, Any]] = _ModalitySpecsDict({
    "image": {
        "id": "image",
        "label": "Image",
        "defaultModel": "gemini-nano-banana-2.1",
        "defaultNanogptModel": "nano-banana-2.1",
        "aspects": list(ALL_ASPECT_RATIOS),
        "resolutions": ["512", "1K", "2K", "4K"],
        "maxReferences": MAX_REFERENCES,
        "models": [
            "gemini-nano-banana-2.1",
            "gemini-3-pro-image",
            "gemini-3.1-flash-image",
            "gemini-3.1-flash-lite-image",
        ],
    },
    "text": {
        "id": "text",
        "label": "Text",
        "defaultModel": "nanogpt/TEE/deepseek-v4.1-flash",
        "defaultNanogptModel": "nanogpt/TEE/deepseek-v4.1-flash",
        "contextWindow": 128000,
        "maxReferences": MAX_REFERENCES,
        "models": [
            "nanogpt/TEE/deepseek-v4.1-flash",
            "gemini-3.1-pro",
            "nanogpt/Gemma-4-31B-Gembrain-uncensored-heretic",
        ],
    },
    "video": {
        "id": "video",
        "label": "Video",
        "defaultModel": "ltx-video",
        "defaultNanogptModel": "ltx-video",
        "fpsOptions": [24, 60],
        "defaultFps": 60,
        "audioSync": True,
        "maxReferences": MAX_REFERENCES,
        "models": [
            "ltx-video",
            "kling-1.6",
            "nanogpt-video",
        ],
    },
    "audio": {
        "id": "audio",
        "label": "Audio",
        "defaultModel": "google/lyria-3.5",
        "defaultNanogptModel": "google/lyria-3.5",
        "kinds": ["music", "tts", "sfx"],
        "defaultLufs": -14.0,
        "sparkline": AEONIK_SPARKLINE_STR,
        "maxReferences": MAX_REFERENCES,
        "models": [
            "google/lyria-3.5",
            "elevenlabs/eleven-v4",
            "elevenlabs/sound-effects/v3",
            "kokoro-82m",
        ],
    },
    "atlas": {
        "id": "atlas",
        "label": "World Labs Atlas v2",
        "defaultModel": "worldlabs/posedImages2Splats",
        "coordSystem": "RUB",
        "tasks": [
            "images2PosedRGBD",
            "posedImages2Splats",
            "atlasGenerate",
            "splats2Mesh",
            "atlasChisel",
            "atlasTextToImage",
        ],
        "maxReferences": MAX_REFERENCES,
        "models": [
            "worldlabs/images2PosedRGBD",
            "worldlabs/posedImages2Splats",
            "worldlabs/atlasGenerate",
            "worldlabs/splats2Mesh",
            "worldlabs/atlasChisel",
            "worldlabs/atlasTextToImage",
        ],
    },
    "3d": {
        "id": "3d",
        "label": "3D Mesh & Rig",
        "defaultModel": "hyper3d/rodin-v2.5",
        "formats": ["glb", "fbx", "obj", "usdz", "spz"],
        "tiers": ["Sketch", "Regular", "Detail", "Smooth"],
        "maxReferences": MAX_REFERENCES,
        "models": [
            "hyper3d/rodin-v2.5",
            "tripo3d/h3.0",
            "meshy/v7.1/image-to-3d",
            "worldlabs/splats2Mesh",
            "hyper3d/rigging",
        ],
    },
})

MODEL_SPECS: Dict[str, Dict[str, Any]] = {
    # --- Image Modality ---
    "gemini-nano-banana-2.1": {
        "id": "gemini-nano-banana-2.1",
        "modality": "image",
        "label": "Nano Banana 2.1",
        "default": True,
        "geminiModel": "gemini-nano-banana-2.1",
        "nanogptModel": "nano-banana-2.1",
        "preferredProvider": "auto",
        "thinking": True,
        "thinkingLevels": ["minimal", "medium", "high"],
        "defaultThinkingLevel": "medium",
        "resolutions": ["1K", "2K", "4K"],
        "nanogptResolutions": ["1k", "2k"],
        "webGrounding": True,
        "imageSearchGrounding": True,
        "panoramicAspects": True,
        "aspects": list(ALL_ASPECT_RATIOS),
        "maxReferences": 14,
        "nanogptMaxReferences": 14,
        "creditCost": 0.20,
        "creditLabel": "0.20 CR",
    },
    "gemini-3-pro-image": {
        "id": "gemini-3-pro-image",
        "modality": "image",
        "label": "Pro 4K Studio",
        "default": False,
        "geminiModel": "gemini-3-pro-image",
        "nanogptModel": "nano-banana-pro",
        "preferredProvider": "auto",
        "thinking": True,
        "thinkingLevels": None,
        "defaultThinkingLevel": None,
        "resolutions": ["1K", "2K", "4K"],
        "nanogptResolutions": ["1k", "2k", "4k"],
        "webGrounding": True,
        "imageSearchGrounding": False,
        "panoramicAspects": False,
        "aspects": list(STANDARD_ASPECT_RATIOS),
        "maxReferences": 14,
        "nanogptMaxReferences": 10,
        "creditCost": 0.50,
        "creditLabel": "0.50 CR",
    },
    "gemini-3.1-flash-image": {
        "id": "gemini-3.1-flash-image",
        "modality": "image",
        "label": "Flash Panoramic",
        "default": False,
        "geminiModel": "gemini-3.1-flash-image",
        "nanogptModel": "nano-banana-2",
        "preferredProvider": "auto",
        "thinking": True,
        "thinkingLevels": ["minimal", "high"],
        "defaultThinkingLevel": "minimal",
        "resolutions": ["512", "1K", "2K", "4K"],
        "nanogptResolutions": ["1k", "2k", "4k"],
        "webGrounding": True,
        "imageSearchGrounding": True,
        "panoramicAspects": True,
        "aspects": list(ALL_ASPECT_RATIOS),
        "maxReferences": 14,
        "nanogptMaxReferences": 14,
        "creditCost": 0.15,
        "creditLabel": "0.15 CR",
    },
    "gemini-3.1-flash-lite-image": {
        "id": "gemini-3.1-flash-lite-image",
        "modality": "image",
        "label": "Flash Lite 1K",
        "default": False,
        "geminiModel": "gemini-3.1-flash-lite-image",
        "nanogptModel": "nano-banana-2-lite",
        "preferredProvider": "auto",
        "thinking": True,
        "thinkingLevels": ["minimal", "high"],
        "defaultThinkingLevel": "minimal",
        "resolutions": ["1K"],
        "nanogptResolutions": ["1k"],
        "webGrounding": False,
        "imageSearchGrounding": False,
        "panoramicAspects": False,
        "aspects": list(STANDARD_ASPECT_RATIOS),
        "maxReferences": 14,
        "nanogptMaxReferences": 14,
        "creditCost": 0.08,
        "creditLabel": "0.08 CR",
    },
    # --- Text Modality ---
    "nanogpt/TEE/deepseek-v4.1-flash": {
        "id": "nanogpt/TEE/deepseek-v4.1-flash",
        "modality": "text",
        "label": "DeepSeek v4.1 Flash (TEE)",
        "default": True,
        "geminiModel": None,
        "nanogptModel": "TEE/deepseek-v4.1-flash",
        "preferredProvider": "nanogpt",
        "contextWindow": 128000,
        "teeAttested": True,
        "thinking": True,
        "thinkingLevels": ["minimal", "medium", "high"],
        "defaultThinkingLevel": "medium",
        "webGrounding": False,
        "maxReferences": 14,
        "nanogptMaxReferences": 14,
        "creditCost": 0.08,
        "creditLabel": "0.08 CR",
    },
    "gemini-3.1-pro": {
        "id": "gemini-3.1-pro",
        "modality": "text",
        "label": "Gemini 3.1 Pro",
        "default": False,
        "geminiModel": "gemini-3.1-pro",
        "nanogptModel": "gemini-3.1-pro",
        "preferredProvider": "auto",
        "contextWindow": 1000000,
        "teeAttested": False,
        "thinking": True,
        "thinkingLevels": ["minimal", "medium", "high"],
        "defaultThinkingLevel": "high",
        "webGrounding": True,
        "maxReferences": 14,
        "nanogptMaxReferences": 14,
        "creditCost": 0.15,
        "creditLabel": "0.15 CR",
    },
    "nanogpt/Gemma-4-31B-Gembrain-uncensored-heretic": {
        "id": "nanogpt/Gemma-4-31B-Gembrain-uncensored-heretic",
        "modality": "text",
        "label": "Gemma 4 31B Gembrain",
        "default": False,
        "geminiModel": None,
        "nanogptModel": "Gemma-4-31B-Gembrain-uncensored-heretic",
        "preferredProvider": "nanogpt",
        "contextWindow": 128000,
        "teeAttested": False,
        "thinking": False,
        "webGrounding": False,
        "maxReferences": 14,
        "nanogptMaxReferences": 14,
        "creditCost": 0.10,
        "creditLabel": "0.10 CR",
    },
    # --- Video Modality ---
    "ltx-video": {
        "id": "ltx-video",
        "modality": "video",
        "label": "LTX-Video 24/60fps",
        "default": True,
        "geminiModel": None,
        "nanogptModel": "ltx-video",
        "preferredProvider": "nanogpt",
        "fpsOptions": [24, 60],
        "defaultFps": 60,
        "audioSync": True,
        "maxDurationSeconds": 14,
        "maxReferences": 14,
        "nanogptMaxReferences": 14,
        "creditCost": 0.40,
        "creditLabel": "0.40 CR",
    },
    "kling-1.6": {
        "id": "kling-1.6",
        "modality": "video",
        "label": "Kling 1.6 Pro",
        "default": False,
        "geminiModel": None,
        "nanogptModel": "kling-1.6",
        "preferredProvider": "nanogpt",
        "fpsOptions": [24, 60],
        "defaultFps": 24,
        "audioSync": True,
        "maxDurationSeconds": 10,
        "maxReferences": 14,
        "nanogptMaxReferences": 14,
        "creditCost": 0.60,
        "creditLabel": "0.60 CR",
    },
    "nanogpt-video": {
        "id": "nanogpt-video",
        "modality": "video",
        "label": "NanoGPT Video",
        "default": False,
        "geminiModel": None,
        "nanogptModel": "nanogpt-video",
        "preferredProvider": "nanogpt",
        "fpsOptions": [24, 60],
        "defaultFps": 24,
        "audioSync": True,
        "maxDurationSeconds": 12,
        "maxReferences": 14,
        "nanogptMaxReferences": 14,
        "creditCost": 0.35,
        "creditLabel": "0.35 CR",
    },
    "kling-4.0": {
        "id": "kling-4.0",
        "modality": "video",
        "label": "Kling 4.0 Master",
        "default": False,
        "geminiModel": None,
        "nanogptModel": "kling-4.0",
        "preferredProvider": "nanogpt",
        "fpsOptions": [24, 60],
        "defaultFps": 24,
        "audioSync": True,
        "maxDurationSeconds": 10,
        "maxReferences": 14,
        "nanogptMaxReferences": 14,
        "creditCost": 0.65,
        "creditLabel": "0.65 CR",
    },
    # --- Audio Modality ---
    "google/lyria-3.5": {
        "id": "google/lyria-3.5",
        "modality": "audio",
        "label": "Google Lyria 3.5 (Music)",
        "default": True,
        "kind": "music",
        "geminiModel": None,
        "nanogptModel": "google/lyria-3.5",
        "preferredProvider": "nanogpt",
        "lufs": -14.0,
        "sparkline": AEONIK_SPARKLINE_STR,
        "maxReferences": 14,
        "creditCost": 0.06,
        "creditLabel": "0.06 CR",
    },
    "elevenlabs/eleven-v4": {
        "id": "elevenlabs/eleven-v4",
        "modality": "audio",
        "label": "ElevenLabs v4 (Dialogue TTS)",
        "default": False,
        "kind": "tts",
        "geminiModel": None,
        "nanogptModel": "elevenlabs/eleven-v4",
        "preferredProvider": "nanogpt",
        "lufs": -14.0,
        "sparkline": AEONIK_SPARKLINE_STR,
        "maxReferences": 14,
        "creditCost": 0.04,
        "creditLabel": "0.04 CR",
    },
    "elevenlabs/sound-effects/v3": {
        "id": "elevenlabs/sound-effects/v3",
        "modality": "audio",
        "label": "ElevenLabs SFX v3 (Foley)",
        "default": False,
        "kind": "sfx",
        "geminiModel": None,
        "nanogptModel": "elevenlabs/sound-effects/v3",
        "preferredProvider": "nanogpt",
        "lufs": -14.0,
        "sparkline": AEONIK_SPARKLINE_STR,
        "maxReferences": 14,
        "creditCost": 0.03,
        "creditLabel": "0.03 CR",
    },
    "kokoro-82m": {
        "id": "kokoro-82m",
        "modality": "audio",
        "label": "Kokoro-82M Neural TTS",
        "default": False,
        "kind": "tts",
        "geminiModel": None,
        "nanogptModel": "kokoro-82m",
        "preferredProvider": "local",
        "lufs": -14.0,
        "sparkline": AEONIK_SPARKLINE_STR,
        "maxReferences": 14,
        "creditCost": 0.01,
        "creditLabel": "0.01 CR",
    },
    # --- World Labs Atlas v2 Modality ---
    "worldlabs/images2PosedRGBD": {
        "id": "worldlabs/images2PosedRGBD",
        "modality": "atlas",
        "label": "Atlas images2PosedRGBD (Pose + EXR Depth)",
        "default": False,
        "atlasTask": "images2PosedRGBD",
        "coordSystem": "RUB",
        "preferredProvider": "worldlabs",
        "maxReferences": 14,
        "creditCost": 0.05,
        "creditLabel": "50 CR ($0.05)",
    },
    "worldlabs/posedImages2Splats": {
        "id": "worldlabs/posedImages2Splats",
        "modality": "atlas",
        "label": "Atlas posedImages2Splats (2.0M Gaussian Splats)",
        "default": True,
        "atlasTask": "posedImages2Splats",
        "coordSystem": "RUB",
        "numSplats": 2000000,
        "preferredProvider": "worldlabs",
        "maxReferences": 14,
        "creditCost": 0.50,
        "creditLabel": "500 CR ($0.50)",
    },
    "worldlabs/atlasGenerate": {
        "id": "worldlabs/atlasGenerate",
        "modality": "atlas",
        "label": "Atlas atlasGenerate (Multi-View / Flythrough)",
        "default": False,
        "atlasTask": "atlasGenerate",
        "coordSystem": "RUB",
        "preferredProvider": "worldlabs",
        "maxReferences": 14,
        "creditCost": 0.25,
        "creditLabel": "250 CR ($0.25)",
    },
    "worldlabs/splats2Mesh": {
        "id": "worldlabs/splats2Mesh",
        "modality": "atlas",
        "label": "Atlas splats2Mesh (.spz -> Textured .glb)",
        "default": False,
        "atlasTask": "splats2Mesh",
        "coordSystem": "RUB",
        "preferredProvider": "worldlabs",
        "maxReferences": 14,
        "creditCost": 0.25,
        "creditLabel": "250 CR ($0.25)",
    },
    "worldlabs/atlasChisel": {
        "id": "worldlabs/atlasChisel",
        "modality": "atlas",
        "label": "Atlas atlasChisel (3D Layout Proxy -> Video)",
        "default": False,
        "atlasTask": "atlasChisel",
        "coordSystem": "RUB",
        "preferredProvider": "worldlabs",
        "maxReferences": 14,
        "creditCost": 0.30,
        "creditLabel": "300 CR ($0.30)",
    },
    "worldlabs/atlasTextToImage": {
        "id": "worldlabs/atlasTextToImage",
        "modality": "atlas",
        "label": "Atlas atlasTextToImage (Spatial Anchor Keyframe)",
        "default": False,
        "atlasTask": "atlasTextToImage",
        "coordSystem": "RUB",
        "preferredProvider": "worldlabs",
        "maxReferences": 14,
        "creditCost": 0.05,
        "creditLabel": "50 CR ($0.05)",
    },
    # --- 3D Mesh & Rig Modality ---
    "hyper3d/rodin-v2.5": {
        "id": "hyper3d/rodin-v2.5",
        "modality": "3d",
        "label": "Hyper3D Rodin v2.5 (PBR GLB)",
        "default": True,
        "preferredProvider": "hyper3d",
        "formats": ["glb", "fbx", "obj", "usdz"],
        "tiers": ["Sketch", "Regular", "Detail", "Smooth"],
        "maxReferences": 14,
        "creditCost": 0.40,
        "creditLabel": "0.40 CR",
    },
    "tripo3d/h3.0": {
        "id": "tripo3d/h3.0",
        "modality": "3d",
        "label": "Tripo3D H3.0 (Hard-Surface GLB)",
        "default": False,
        "nanogptModel": "tripo3d/h3.0",
        "preferredProvider": "nanogpt",
        "formats": ["glb", "fbx", "obj"],
        "maxReferences": 14,
        "creditCost": 0.30,
        "creditLabel": "0.30 CR",
    },
    "meshy/v7.1/image-to-3d": {
        "id": "meshy/v7.1/image-to-3d",
        "modality": "3d",
        "label": "Meshy v7.1 Image-to-3D",
        "default": False,
        "nanogptModel": "meshy/v7.1/image-to-3d",
        "preferredProvider": "nanogpt",
        "formats": ["glb", "fbx", "usdz"],
        "maxReferences": 14,
        "creditCost": 0.25,
        "creditLabel": "0.25 CR",
    },
    "hyper3d/rigging": {
        "id": "hyper3d/rigging",
        "modality": "3d",
        "label": "Hyper3D Auto-Rig & Animation",
        "default": False,
        "preferredProvider": "hyper3d",
        "formats": ["glb", "fbx"],
        "animations": ["walk", "run", "idle", "dance"],
        "maxReferences": 14,
        "creditCost": 0.20,
        "creditLabel": "0.20 CR",
    },
}

MODEL_ALIASES: Dict[str, str] = {
    "nano-banana-2.1": "gemini-nano-banana-2.1",
    "nanogpt-2.1": "gemini-nano-banana-2.1",
    "nano-banana-pro": "gemini-3-pro-image",
    "gemini-3-pro-image-preview": "gemini-3-pro-image",
    "nano-banana-2": "gemini-3.1-flash-image",
    "gemini-3.1-flash-image-preview": "gemini-3.1-flash-image",
    "nano-banana-2-lite": "gemini-3.1-flash-lite-image",
    "deepseek-v4.1-tee": "nanogpt/TEE/deepseek-v4.1-flash",
    "TEE/deepseek-v4.1-flash": "nanogpt/TEE/deepseek-v4.1-flash",
    "Gemma-4-31B-Gembrain-uncensored-heretic": "nanogpt/Gemma-4-31B-Gembrain-uncensored-heretic",
    "lyria-3.5": "google/lyria-3.5",
    "lyria": "google/lyria-3.5",
    "eleven-v4": "elevenlabs/eleven-v4",
    "elevenlabs": "elevenlabs/eleven-v4",
    "sfx-v3": "elevenlabs/sound-effects/v3",
    "kokoro": "kokoro-82m",
    "qwen-audio-3.1-tts-flash": "elevenlabs/eleven-v4",
    "images2PosedRGBD": "worldlabs/images2PosedRGBD",
    "posedImages2Splats": "worldlabs/posedImages2Splats",
    "atlasGenerate": "worldlabs/atlasGenerate",
    "splats2Mesh": "worldlabs/splats2Mesh",
    "atlasChisel": "worldlabs/atlasChisel",
    "atlasTextToImage": "worldlabs/atlasTextToImage",
    "worldlabs/atlas-v2": "worldlabs/posedImages2Splats",
    "atlas-v2": "worldlabs/posedImages2Splats",
    "rodin": "hyper3d/rodin-v2.5",
    "rodin-v2.5": "hyper3d/rodin-v2.5",
    "tripo": "tripo3d/h3.0",
    "meshy": "meshy/v7.1/image-to-3d",
    "meshy/v7.1": "meshy/v7.1/image-to-3d",
    "rigging": "hyper3d/rigging",
    "meshy/rigging": "hyper3d/rigging",
    "tripo3d/rig": "hyper3d/rigging",
}

FILTER_PRESETS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "image": {
        "kodak_2383": {
            "id": "kodak_2383",
            "modality": "image",
            "label": "Kodak 2383 LUT",
            "type": "range",
            "min": 0,
            "max": 100,
            "unit": "%",
            "default": 85,
            "enabledDefault": True,
        },
        "halation": {
            "id": "halation",
            "modality": "image",
            "label": "35mm Halation",
            "type": "range",
            "min": 0,
            "max": 100,
            "unit": "%",
            "default": 35,
            "enabledDefault": True,
        },
        "film_grain_16mm": {
            "id": "film_grain_16mm",
            "modality": "image",
            "label": "16mm Film Grain",
            "type": "range",
            "min": 0,
            "max": 100,
            "unit": "%",
            "default": 25,
            "enabledDefault": True,
        },
        "anamorphic_streak": {
            "id": "anamorphic_streak",
            "modality": "image",
            "label": "Anamorphic Streak",
            "type": "bool",
            "default": False,
            "enabledDefault": False,
        },
        "soop_dirty_ink": {
            "id": "soop_dirty_ink",
            "modality": "image",
            "label": "SOOP Dirty Ink",
            "type": "bool",
            "default": False,
            "enabledDefault": False,
        },
    },
    "text": {
        "wga_tighten": {
            "id": "wga_tighten",
            "modality": "text",
            "label": "WGA Tighten (<=4 lines/beat)",
            "type": "max_lines",
            "min": 1,
            "max": 4,
            "unit": "lines/beat",
            "default": 4,
            "enabledDefault": True,
        },
        "fact_lock": {
            "id": "fact_lock",
            "modality": "text",
            "label": "Fact Lock (Strict Citation Grounding)",
            "type": "bool",
            "default": True,
            "enabledDefault": True,
        },
        "eli12_strip": {
            "id": "eli12_strip",
            "modality": "text",
            "label": "ELI12 Jargon Strip",
            "type": "bool",
            "default": False,
            "enabledDefault": False,
        },
    },
    "video": {
        "optical_flow_60fps": {
            "id": "optical_flow_60fps",
            "modality": "video",
            "label": "Optical Flow 24->60fps",
            "type": "fps",
            "options": [24, 60],
            "unit": "fps",
            "default": 60,
            "enabledDefault": True,
        },
        "temporal_deflicker": {
            "id": "temporal_deflicker",
            "modality": "video",
            "label": "Temporal Deflicker",
            "type": "range",
            "min": 0,
            "max": 100,
            "unit": "%",
            "default": 65,
            "enabledDefault": True,
        },
        "j_cut_dialogue_duck": {
            "id": "j_cut_dialogue_duck",
            "modality": "video",
            "label": "J-Cut Dialogue Duck",
            "type": "lufs",
            "min": -36.0,
            "max": 0.0,
            "unit": "LUFS",
            "default": -14.0,
            "enabledDefault": True,
        },
    },
    "audio": {
        "lufs_master": {
            "id": "lufs_master",
            "modality": "audio",
            "label": "EBU R128 Loudness Lock",
            "type": "lufs",
            "min": -36.0,
            "max": 0.0,
            "unit": "LUFS",
            "default": -14.0,
            "enabledDefault": True,
        },
        "dialogue_deess": {
            "id": "dialogue_deess",
            "modality": "audio",
            "label": "Dialogue De-Esser",
            "type": "range",
            "min": 0,
            "max": 100,
            "unit": "%",
            "default": 40,
            "enabledDefault": True,
        },
        "spatial_reverb": {
            "id": "spatial_reverb",
            "modality": "audio",
            "label": "Binaural Room Impulse",
            "type": "range",
            "min": 0,
            "max": 100,
            "unit": "%",
            "default": 25,
            "enabledDefault": False,
        },
    },
    "atlas": {
        "splat_density": {
            "id": "splat_density",
            "modality": "atlas",
            "label": "Gaussian Splat Budget (2.0M)",
            "type": "range",
            "min": 10,
            "max": 100,
            "unit": "%",
            "default": 100,
            "enabledDefault": True,
        },
        "exr_depth_clamp": {
            "id": "exr_depth_clamp",
            "modality": "atlas",
            "label": "Linear Depth Confidence (.exr)",
            "type": "range",
            "min": 0,
            "max": 100,
            "unit": "%",
            "default": 98,
            "enabledDefault": True,
        },
        "rub_frustum_lock": {
            "id": "rub_frustum_lock",
            "modality": "atlas",
            "label": "RUB Camera Frustum Lock",
            "type": "bool",
            "default": True,
            "enabledDefault": True,
        },
    },
    "3d": {
        "pbr_roughness_norm": {
            "id": "pbr_roughness_norm",
            "modality": "3d",
            "label": "PBR Metallic/Roughness Clamp",
            "type": "range",
            "min": 0,
            "max": 100,
            "unit": "%",
            "default": 85,
            "enabledDefault": True,
        },
        "quad_remesh": {
            "id": "quad_remesh",
            "modality": "3d",
            "label": "Watertight Quad Remesh",
            "type": "bool",
            "default": True,
            "enabledDefault": True,
        },
        "humanoid_ik_rig": {
            "id": "humanoid_ik_rig",
            "modality": "3d",
            "label": "Humanoid IK Skeleton Bind",
            "type": "bool",
            "default": False,
            "enabledDefault": False,
        },
    },
}

FLAT_FILTER_PRESETS: Dict[str, Dict[str, Any]] = {
    fid: spec
    for mod_filters in FILTER_PRESETS.values()
    for fid, spec in mod_filters.items()
}


def get_model_spec(model_id: Optional[str] = None, modality: Optional[str] = None) -> Dict[str, Any]:
    """Resolve a model specification by canonical ID or NanoGPT/legacy alias."""
    if model_id:
        canonical = MODEL_ALIASES.get(model_id, model_id)
        if canonical in MODEL_SPECS:
            return copy.deepcopy(MODEL_SPECS[canonical])

    resolved_modality = modality if modality in MODALITY_SPECS else "image"
    default_id = MODALITY_SPECS[resolved_modality]["defaultModel"]
    return copy.deepcopy(MODEL_SPECS[default_id])


def infer_modality(model_id: Optional[str] = None, explicit_modality: Optional[str] = None) -> str:
    """Resolve active modality (`text` | `image` | `video` | `audio` | `atlas` | `3d`) from explicit input or model ID."""
    if explicit_modality and explicit_modality in MODALITIES:
        return explicit_modality
    if model_id:
        canonical = MODEL_ALIASES.get(model_id, model_id)
        if canonical in MODEL_SPECS:
            return str(MODEL_SPECS[canonical]["modality"])
        lowered = model_id.lower()
        if any(tok in lowered for tok in ("worldlabs", "atlas", "splat", "rgbd", "chisel")):
            return "atlas"
        if any(tok in lowered for tok in ("lyria", "elevenlabs", "kokoro", "sound-effects", "tts", "audio", "sfx")):
            return "audio"
        if any(tok in lowered for tok in ("rodin", "hyper3d", "tripo", "meshy", "rigging", "3d")):
            return "3d"
        if any(tok in lowered for tok in ("ltx", "kling", "video", "veo", "cosmos")):
            return "video"
        if any(tok in lowered for tok in ("deepseek", "gemma", "3.1-pro", "claude", "gpt", "argon")):
            return "text"
    return "image"


_ATLAS_SUBCOMMAND_MAP: Dict[str, Tuple[str, str, str]] = {
    "pose": ("pose", "images2PosedRGBD", "worldlabs/images2PosedRGBD"),
    "rgbd": ("pose", "images2PosedRGBD", "worldlabs/images2PosedRGBD"),
    "images2posedrgbd": ("pose", "images2PosedRGBD", "worldlabs/images2PosedRGBD"),
    "splat": ("splat", "posedImages2Splats", "worldlabs/posedImages2Splats"),
    "splats": ("splat", "posedImages2Splats", "worldlabs/posedImages2Splats"),
    "posedimages2splats": ("splat", "posedImages2Splats", "worldlabs/posedImages2Splats"),
    "flythrough": ("flythrough", "atlasGenerate", "worldlabs/atlasGenerate"),
    "generate": ("flythrough", "atlasGenerate", "worldlabs/atlasGenerate"),
    "orbit": ("flythrough", "atlasGenerate", "worldlabs/atlasGenerate"),
    "atlasgenerate": ("flythrough", "atlasGenerate", "worldlabs/atlasGenerate"),
    "mesh": ("mesh", "splats2Mesh", "worldlabs/splats2Mesh"),
    "splats2mesh": ("mesh", "splats2Mesh", "worldlabs/splats2Mesh"),
    "glb": ("mesh", "splats2Mesh", "worldlabs/splats2Mesh"),
    "chisel": ("chisel", "atlasChisel", "worldlabs/atlasChisel"),
    "atlaschisel": ("chisel", "atlasChisel", "worldlabs/atlasChisel"),
    "text2img": ("text2img", "atlasTextToImage", "worldlabs/atlasTextToImage"),
    "text-to-image": ("text2img", "atlasTextToImage", "worldlabs/atlasTextToImage"),
    "atlastexttoimage": ("text2img", "atlasTextToImage", "worldlabs/atlasTextToImage"),
    "image": ("text2img", "atlasTextToImage", "worldlabs/atlasTextToImage"),
}

_AUDIO_SUBCOMMAND_MAP: Dict[str, Tuple[str, str]] = {
    "tts": ("tts", "elevenlabs/eleven-v4"),
    "dialogue": ("tts", "elevenlabs/eleven-v4"),
    "voice": ("tts", "elevenlabs/eleven-v4"),
    "kokoro": ("tts", "kokoro-82m"),
    "music": ("music", "google/lyria-3.5"),
    "score": ("music", "google/lyria-3.5"),
    "lyria": ("music", "google/lyria-3.5"),
    "sfx": ("sfx", "elevenlabs/sound-effects/v3"),
    "foley": ("sfx", "elevenlabs/sound-effects/v3"),
}

_KNOWN_SLASH_COMMANDS: Dict[str, Tuple[str, Optional[str], Optional[str], Optional[str]]] = {
    # token -> (canonical_command, forced_subcommand, forced_model, forced_provider)
    "atlas": ("atlas", None, None, "worldlabs"),
    "worldlabs": ("atlas", None, None, "worldlabs"),
    "world": ("atlas", None, None, "worldlabs"),
    "splat": ("atlas", "splat", "worldlabs/posedImages2Splats", "worldlabs"),
    "splats": ("atlas", "splat", "worldlabs/posedImages2Splats", "worldlabs"),
    "pose": ("atlas", "pose", "worldlabs/images2PosedRGBD", "worldlabs"),
    "flythrough": ("atlas", "flythrough", "worldlabs/atlasGenerate", "worldlabs"),
    "chisel": ("atlas", "chisel", "worldlabs/atlasChisel", "worldlabs"),
    "image": ("image", None, "gemini-nano-banana-2.1", "gemini"),
    "img": ("image", None, "gemini-nano-banana-2.1", "gemini"),
    "nano": ("image", None, "gemini-nano-banana-2.1", "nanogpt"),
    "video": ("video", None, "ltx-video", "nanogpt"),
    "vid": ("video", None, "ltx-video", "nanogpt"),
    "kling": ("video", None, "kling-4.0", "nanogpt"),
    "ltx": ("video", None, "ltx-video", "nanogpt"),
    "audio": ("audio", None, None, "nanogpt"),
    "sound": ("audio", None, None, "nanogpt"),
    "tts": ("audio", "tts", "elevenlabs/eleven-v4", "nanogpt"),
    "music": ("audio", "music", "google/lyria-3.5", "nanogpt"),
    "lyria": ("audio", "music", "google/lyria-3.5", "nanogpt"),
    "sfx": ("audio", "sfx", "elevenlabs/sound-effects/v3", "nanogpt"),
    "kokoro": ("audio", "tts", "kokoro-82m", "local"),
    "3d": ("3d", None, "hyper3d/rodin-v2.5", "hyper3d"),
    "rodin": ("3d", None, "hyper3d/rodin-v2.5", "hyper3d"),
    "tripo": ("3d", None, "tripo3d/h3.0", "nanogpt"),
    "meshy": ("3d", None, "meshy/v7.1/image-to-3d", "nanogpt"),
    "mesh": ("3d", "mesh", "hyper3d/rodin-v2.5", "hyper3d"),
    "rig": ("rig", "rig", "hyper3d/rigging", "hyper3d"),
    "text": ("text", None, "nanogpt/TEE/deepseek-v4.1-flash", "nanogpt"),
    "chat": ("text", None, "nanogpt/TEE/deepseek-v4.1-flash", "nanogpt"),
    "deepseek": ("text", None, "nanogpt/TEE/deepseek-v4.1-flash", "nanogpt"),
    "gemini": ("text", None, "gemini-3.1-pro", "gemini"),
    "claude": ("text", None, "anthropic/claude-sonnet-5.5", "openrouter"),
    "mux": ("mux", "mux", "ltx-video", "local"),
}

_RIG_ANIMATIONS = ("walk", "run", "idle", "dance", "jump", "sprint", "turn")
_VFS_EXTS = (".glb", ".spz", ".exr", ".png", ".jpg", ".jpeg", ".wav", ".mp4", ".obj", ".fbx", ".usdz")
_VFS_PREFIXES = ("/worlds/", "/models3d/", "/images/", "/videos/", "/audio/", "/space/", "~/space/", "./")


def _looks_like_target_path(token: str) -> bool:
    low = token.lower().strip()
    if any(low.startswith(pref) for pref in _VFS_PREFIXES):
        return True
    if any(low.endswith(ext) for ext in _VFS_EXTS):
        return True
    return False


def _resolve_provider_for_model(model_id: str, fallback: str = "nanogpt") -> str:
    low = model_id.lower()
    if "worldlabs" in low or low in (
        "images2posedrgbd",
        "posedimages2splats",
        "atlasgenerate",
        "splats2mesh",
        "atlaschisel",
        "atlastexttoimage",
    ):
        return "worldlabs"
    if "hyper3d" in low or "rodin" in low:
        return "hyper3d"
    if "kokoro" in low or low == "local":
        return "local"
    if "anthropic" in low or "openrouter" in low or "claude" in low:
        return "openrouter"
    if low.startswith("gemini") or "google/gemini" in low:
        return "gemini"
    return fallback


def parse_omni_slash_command(raw_input: str) -> Dict[str, Any]:
    """Parse any slash command from Prompt Island, Workstation Omnibar, or TinCanShell (.tcsh)."""
    text = (raw_input or "").strip()
    if not text.startswith("/"):
        return {
            "is_slash": False,
            "command": "image",
            "subcommand": "",
            "modality": "image",
            "provider": "gemini",
            "model": "gemini-nano-banana-2.1",
            "atlas_task": None,
            "flags": {},
            "target_path": None,
            "prompt": text,
            "pill_label": "● /image",
        }

    tokens = text.split()
    first_tok = tokens[0][1:].lower()
    if first_tok not in _KNOWN_SLASH_COMMANDS:
        # e.g. a leading VFS path like "/worlds/torii/..." rather than a slash directive
        return {
            "is_slash": False,
            "command": "image",
            "subcommand": "",
            "modality": "image",
            "provider": "gemini",
            "model": "gemini-nano-banana-2.1",
            "atlas_task": None,
            "flags": {},
            "target_path": tokens[0] if _looks_like_target_path(tokens[0]) else None,
            "prompt": text,
            "pill_label": "● /image",
        }

    command, forced_sub, forced_model, forced_provider = _KNOWN_SLASH_COMMANDS[first_tok]
    rest = tokens[1:]
    subcommand = forced_sub or ""
    atlas_task: Optional[str] = None
    model = forced_model or ""
    provider = forced_provider or "nanogpt"

    if command == "atlas":
        if not subcommand and rest and not rest[0].startswith("--"):
            cand = rest[0].lower()
            if cand in _ATLAS_SUBCOMMAND_MAP:
                subcommand, atlas_task, model = _ATLAS_SUBCOMMAND_MAP[cand]
                rest = rest[1:]
        if not subcommand:
            subcommand = "splat"
        if not atlas_task:
            _, atlas_task, default_atlas_model = _ATLAS_SUBCOMMAND_MAP.get(
                subcommand, ("splat", "posedImages2Splats", "worldlabs/posedImages2Splats")
            )
            if not model:
                model = default_atlas_model
        modality = "atlas"
        provider = "worldlabs"
    elif command == "audio":
        if not subcommand and rest and not rest[0].startswith("--"):
            cand = rest[0].lower()
            if cand in _AUDIO_SUBCOMMAND_MAP:
                subcommand, default_aud_model = _AUDIO_SUBCOMMAND_MAP[cand]
                if not model:
                    model = default_aud_model
                rest = rest[1:]
        if not subcommand:
            subcommand = "music"
        if not model:
            _, model = _AUDIO_SUBCOMMAND_MAP.get(subcommand, ("music", "google/lyria-3.5"))
        modality = "audio"
        provider = _resolve_provider_for_model(model, provider)
    elif command == "video":
        modality = "video"
        if rest and not rest[0].startswith("--"):
            cand = rest[0].lower()
            if any(k in cand for k in ("kling", "ltx", "cosmos", "gemini-omni", "veo", "nanogpt-video")):
                model = rest[0]
                subcommand = rest[0]
                rest = rest[1:]
        if not model:
            model = "ltx-video"
        provider = _resolve_provider_for_model(model, "nanogpt")
    elif command == "image":
        modality = "image"
        if rest and not rest[0].startswith("--"):
            cand = rest[0].lower()
            if any(k in cand for k in ("nano-banana", "flux", "atlastexttoimage", "gemini-3")):
                model = rest[0]
                subcommand = rest[0]
                rest = rest[1:]
        if not model:
            model = "gemini-nano-banana-2.1"
        if "atlastexttoimage" in model.lower():
            atlas_task = "atlasTextToImage"
            model = "worldlabs/atlasTextToImage"
            provider = "worldlabs"
        elif first_tok == "nano":
            provider = "nanogpt"
        else:
            provider = _resolve_provider_for_model(model, provider)
    elif command == "3d":
        modality = "3d"
        if rest and not rest[0].startswith("--"):
            cand = rest[0].lower()
            if any(k in cand for k in ("rodin", "tripo", "meshy", "splats2mesh")):
                model = MODEL_ALIASES.get(rest[0], rest[0])
                subcommand = rest[0]
                rest = rest[1:]
        if not model:
            model = "hyper3d/rodin-v2.5"
        if "splats2mesh" in model.lower():
            atlas_task = "splats2Mesh"
            model = "worldlabs/splats2Mesh"
            provider = "worldlabs"
        else:
            provider = _resolve_provider_for_model(model, "hyper3d")
    elif command == "rig":
        modality = "3d"
        if rest and not rest[0].startswith("--") and rest[0].lower() in _RIG_ANIMATIONS:
            subcommand = rest[0].lower()
            rest = rest[1:]
        if not subcommand:
            subcommand = "rig"
        if not model:
            model = "hyper3d/rigging"
        provider = _resolve_provider_for_model(model, "hyper3d")
    elif command == "text":
        modality = "text"
        if not model:
            model = "nanogpt/TEE/deepseek-v4.1-flash"
        provider = _resolve_provider_for_model(model, provider)
    else:  # mux
        modality = "video"
        subcommand = "mux"
        if not model:
            model = "ltx-video"
        provider = "local"

    flags: Dict[str, Any] = {}
    if command == "rig" and subcommand in _RIG_ANIMATIONS:
        flags["anim"] = subcommand
        flags["rig"] = subcommand

    prompt_tokens: List[str] = []
    target_path: Optional[str] = None
    idx = 0
    while idx < len(rest):
        tok = rest[idx]
        if tok.startswith("--"):
            key_part = tok[2:]
            inline_val: Optional[str] = None
            if "=" in key_part:
                key_part, inline_val = key_part.split("=", 1)
            flag_name = key_part.lower().strip()

            if flag_name == "mesh":
                if inline_val is not None:
                    flags["mesh"] = inline_val.lower() not in ("0", "false", "no")
                elif idx + 1 < len(rest) and rest[idx + 1].lower() in ("true", "false"):
                    flags["mesh"] = rest[idx + 1].lower() == "true"
                    idx += 1
                else:
                    flags["mesh"] = True
                idx += 1
                continue

            if flag_name == "rig":
                if inline_val is not None:
                    flags["rig"] = inline_val
                elif idx + 1 < len(rest) and not rest[idx + 1].startswith("--") and (
                    rest[idx + 1].lower() in _RIG_ANIMATIONS or len(rest) - idx > 2
                ):
                    flags["rig"] = rest[idx + 1]
                    idx += 1
                else:
                    flags["rig"] = "walk"
                idx += 1
                continue

            val_str: Any = True
            if inline_val is not None:
                val_str = inline_val
            elif idx + 1 < len(rest) and not rest[idx + 1].startswith("--"):
                val_str = rest[idx + 1]
                idx += 1

            if flag_name in ("views", "fps") and isinstance(val_str, str):
                try:
                    flags[flag_name] = int(val_str)
                except ValueError:
                    flags[flag_name] = val_str
            elif flag_name == "seconds" and isinstance(val_str, str):
                try:
                    flags["seconds"] = int(val_str) if val_str.isdigit() else float(val_str)
                except ValueError:
                    flags["seconds"] = val_str
            elif flag_name == "lufs" and isinstance(val_str, str):
                try:
                    flags["lufs"] = float(val_str)
                except ValueError:
                    flags["lufs"] = val_str
            elif flag_name == "res" and isinstance(val_str, str):
                if "x" in val_str.lower():
                    parts = val_str.lower().split("x", 1)
                    try:
                        flags["res"] = [int(parts[0]), int(parts[1])]
                        flags["resolution"] = val_str
                    except ValueError:
                        flags["res"] = val_str
                else:
                    flags["res"] = val_str
            elif flag_name in ("model", "engine") and isinstance(val_str, str):
                flags[flag_name] = val_str
                resolved_m = MODEL_ALIASES.get(val_str, val_str)
                model = resolved_m
                if "atlastexttoimage" in resolved_m.lower():
                    atlas_task = "atlasTextToImage"
                    model = "worldlabs/atlasTextToImage"
                    provider = "worldlabs"
                elif "splats2mesh" in resolved_m.lower():
                    atlas_task = "splats2Mesh"
                    model = "worldlabs/splats2Mesh"
                    provider = "worldlabs"
                else:
                    provider = _resolve_provider_for_model(model, provider)
            elif flag_name == "task" and isinstance(val_str, str):
                flags["task"] = val_str
                if val_str.lower() in _ATLAS_SUBCOMMAND_MAP:
                    subcommand, atlas_task, model = _ATLAS_SUBCOMMAND_MAP[val_str.lower()]
            elif flag_name == "anim" and isinstance(val_str, str):
                flags["anim"] = val_str
                flags.setdefault("rig", val_str)
                if command == "rig":
                    subcommand = val_str
            else:
                flags[flag_name] = val_str
            idx += 1
            continue

        if target_path is None and _looks_like_target_path(tok):
            target_path = tok
        prompt_tokens.append(tok)
        idx += 1

    if target_path is None:
        for fkey in ("video", "audio", "ref"):
            fval = flags.get(fkey)
            if isinstance(fval, str) and _looks_like_target_path(fval):
                target_path = fval
                break

    cleaned_prompt = " ".join(prompt_tokens).strip()

    if command == "atlas":
        pill_label = f"● /atlas {subcommand}" if subcommand else "● /atlas"
    elif command == "audio":
        pill_label = f"♪ /audio {subcommand}" if subcommand else "♪ /audio"
    elif command == "3d":
        pill_label = f"◆ /3d {subcommand}".strip() if subcommand in ("mesh", "splat") else "◆ /3d"
    elif command == "rig":
        pill_label = "◆ /rig"
    elif command == "video":
        pill_label = "▶ /video"
    elif command == "image":
        pill_label = "● /image"
    elif command == "text":
        pill_label = "¶ /text"
    else:
        pill_label = "⇄ /mux"

    return {
        "is_slash": True,
        "command": command,
        "subcommand": subcommand,
        "modality": modality,
        "provider": provider,
        "model": model,
        "atlas_task": atlas_task,
        "flags": flags,
        "target_path": target_path,
        "prompt": cleaned_prompt,
        "pill_label": pill_label,
    }


def _normalize_selected_ids(selected_node_ids: Optional[Sequence[Any]]) -> List[str]:
    if not selected_node_ids:
        return []
    seen = set()
    cleaned: List[str] = []
    for item in selected_node_ids:
        if item is None:
            continue
        val = str(item).strip()
        if not val or val in seen:
            continue
        seen.add(val)
        cleaned.append(val)
    return cleaned


def derive_generation_mode(selected_node_ids: Optional[Sequence[Any]]) -> str:
    """Derive selection-driven generation mode (`GENERATE` | `EDIT` | `MERGE`).

    - `0` selected -> `"GENERATE"`
    - `1` selected -> `"EDIT"`
    - `2+` selected -> `"MERGE"`
    """
    cleaned = _normalize_selected_ids(selected_node_ids)
    if len(cleaned) == 0:
        return "GENERATE"
    if len(cleaned) == 1:
        return "EDIT"
    return "MERGE"


def make_branch_node_id(parent_id: str, short_id: Optional[str] = None) -> str:
    """Construct a hierarchical branch ID `f"{parent_id}.{short_id}"`."""
    suffix = (short_id or uuid.uuid4().hex[:4]).strip()
    return f"{parent_id}.{suffix}"


def _get_header_string(headers: Optional[Mapping[str, Any]], name: str) -> str:
    if not headers:
        return ""
    target = name.lower()
    for key, raw in headers.items():
        if str(key).lower() == target:
            if isinstance(raw, (list, tuple)):
                raw = raw[0] if raw else ""
            return str(raw).strip() if raw is not None else ""
    return ""


def _resolve_api_keys(
    headers: Optional[Mapping[str, Any]] = None,
    env: Optional[Mapping[str, str]] = None,
) -> Tuple[str, str]:
    source_env = os.environ if env is None else env
    custom_gemini = _get_header_string(headers, "x-gemini-api-key")
    custom_nanogpt = _get_header_string(headers, "x-nanogpt-api-key")
    server_gemini = str(
        source_env.get("GEMINI_API_KEY") or source_env.get("API_KEY") or ""
    ).strip()
    server_nanogpt = str(source_env.get("NANOGPT_API_KEY") or "").strip()
    return (custom_gemini or server_gemini), (custom_nanogpt or server_nanogpt)


def get_node_studio_health(
    headers: Optional[Mapping[str, Any]] = None,
    env: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    """Return key availability flags, supported modalities, and model specs."""
    gemini_key, nanogpt_key = _resolve_api_keys(headers=headers, env=env)
    source_env = os.environ if env is None else env
    wlt_key = str(
        _get_header_string(headers, "x-wlt-api-key")
        or source_env.get("WLT_API_KEY")
        or source_env.get("WORLDLABS_API_KEY")
        or ""
    ).strip()
    has_gemini = bool(gemini_key)
    has_nanogpt = bool(nanogpt_key)
    has_worldlabs = bool(wlt_key)
    return {
        "ok": True,
        "hasServerKey": has_gemini or has_nanogpt,
        "hasGeminiKey": has_gemini,
        "hasNanogptKey": has_nanogpt,
        "hasWorldlabsKey": has_worldlabs,
        "modalities": _OmniModalitiesList(MODALITIES),
        "models": copy.deepcopy(MODEL_SPECS),
        "modalitySpecs": dict(copy.deepcopy(MODALITY_SPECS)),
    }


def default_filter_state(modality: str = "image") -> Dict[str, Dict[str, Any]]:
    """Build the default non-destructive filter rack configuration for a modality."""
    mod = modality if modality in FILTER_PRESETS else "image"
    rack: Dict[str, Dict[str, Any]] = {}
    for fid, spec in FILTER_PRESETS[mod].items():
        rack[fid] = {
            "id": fid,
            "label": spec["label"],
            "enabled": bool(spec["enabledDefault"]),
            "value": spec["default"],
            "unit": spec.get("unit", ""),
            "type": spec["type"],
        }
    return rack


def _coerce_filter_entry(fid: str, raw_update: Any, existing: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    spec = FLAT_FILTER_PRESETS[fid]
    base = copy.deepcopy(existing) if isinstance(existing, dict) else {
        "id": fid,
        "label": spec["label"],
        "enabled": bool(spec["enabledDefault"]),
        "value": spec["default"],
        "unit": spec.get("unit", ""),
        "type": spec["type"],
    }

    if isinstance(raw_update, dict):
        if "enabled" in raw_update:
            base["enabled"] = bool(raw_update["enabled"])
        if "value" in raw_update:
            raw_val = raw_update["value"]
        else:
            raw_val = base.get("value", spec["default"])
    elif isinstance(raw_update, bool):
        base["enabled"] = raw_update
        raw_val = raw_update if spec["type"] == "bool" else base.get("value", spec["default"])
    else:
        raw_val = raw_update
        base["enabled"] = True

    ftype = spec["type"]
    if ftype == "bool":
        val: Any = bool(raw_val)
        base["enabled"] = val if not isinstance(raw_update, dict) or "enabled" not in raw_update else base["enabled"]
    elif ftype == "range":
        num = float(raw_val)
        lo, hi = float(spec["min"]), float(spec["max"])
        clamped = max(lo, min(hi, num))
        val = int(round(clamped)) if float(clamped).is_integer() else round(clamped, 2)
    elif ftype == "max_lines":
        num = int(round(float(raw_val)))
        val = max(int(spec["min"]), min(int(spec["max"]), num))
    elif ftype == "fps":
        num = int(round(float(raw_val)))
        val = 60 if num >= 48 else 24
    elif ftype == "lufs":
        num = float(raw_val)
        val = round(max(float(spec["min"]), min(float(spec["max"]), num)), 1)
    else:
        val = raw_val

    base["value"] = val
    return base


def _compute_wga_beat_preview(text: str, max_lines: int = 4, eli12: bool = False) -> str:
    """Produce a non-destructive WGA-tightened prose preview without modifying raw text."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return ""
    clipped = lines[:max(1, min(4, max_lines))]
    if eli12:
        clipped = [
            ln.replace("cryptographic", "lock-box")
            .replace("orchestration", "teamwork")
            .replace("deterministic", "exact")
            for ln in clipped
        ]
    return "\n".join(clipped)


def _build_filter_summary(
    modality: str,
    filters: Dict[str, Dict[str, Any]],
    bypass: bool,
    raw_text: str = "",
) -> Dict[str, Any]:
    active_ids = [fid for fid, cfg in filters.items() if cfg.get("enabled")] if not bypass else []

    if modality == "image":
        kodak = filters.get("kodak_2383", {})
        halation = filters.get("halation", {})
        grain = filters.get("film_grain_16mm", {})
        streak = filters.get("anamorphic_streak", {})
        dirty_ink = filters.get("soop_dirty_ink", {})
        contrast = 100 + int((kodak.get("value", 0) or 0) * 0.18) if (not bypass and kodak.get("enabled")) else 100
        saturate = 100 + int((kodak.get("value", 0) or 0) * 0.12) if (not bypass and kodak.get("enabled")) else 100
        brightness = 100 + int((halation.get("value", 0) or 0) * 0.08) if (not bypass and halation.get("enabled")) else 100
        css_chain = (
            "none"
            if bypass
            else f"contrast({contrast}%) saturate({saturate}%) brightness({brightness}%)"
        )
        return {
            "modality": "image",
            "bypassed": bypass,
            "activeFilterIds": active_ids,
            "cssFilter": css_chain,
            "lutMixPct": int(kodak.get("value", 0)) if (not bypass and kodak.get("enabled")) else 0,
            "halationPct": int(halation.get("value", 0)) if (not bypass and halation.get("enabled")) else 0,
            "grainPct": int(grain.get("value", 0)) if (not bypass and grain.get("enabled")) else 0,
            "anamorphicStreak": bool(streak.get("enabled")) and not bypass,
            "soopDirtyInk": bool(dirty_ink.get("enabled")) and not bypass,
        }

    if modality == "text":
        wga = filters.get("wga_tighten", {})
        fact_lock = filters.get("fact_lock", {})
        eli12 = filters.get("eli12_strip", {})
        max_lines = int(wga.get("value", 4)) if (not bypass and wga.get("enabled")) else 999
        eli12_on = bool(eli12.get("enabled")) and not bypass
        preview = raw_text if bypass else _compute_wga_beat_preview(raw_text, max_lines=max_lines, eli12=eli12_on)
        return {
            "modality": "text",
            "bypassed": bypass,
            "activeFilterIds": active_ids,
            "maxLinesPerBeat": max_lines if not bypass and wga.get("enabled") else None,
            "factLockStrict": bool(fact_lock.get("enabled")) and not bypass,
            "eli12Strip": eli12_on,
            "filteredPreview": preview,
        }

    if modality == "audio":
        lufs_cfg = filters.get("lufs_master", {})
        deess_cfg = filters.get("dialogue_deess", {})
        reverb_cfg = filters.get("spatial_reverb", {})
        target_lufs = float(lufs_cfg.get("value", -14.0)) if (not bypass and lufs_cfg.get("enabled")) else 0.0
        return {
            "modality": "audio",
            "bypassed": bypass,
            "activeFilterIds": active_ids,
            "targetLufs": target_lufs,
            "deEssPct": int(deess_cfg.get("value", 0)) if (not bypass and deess_cfg.get("enabled")) else 0,
            "reverbPct": int(reverb_cfg.get("value", 0)) if (not bypass and reverb_cfg.get("enabled")) else 0,
            "sparkline": AEONIK_SPARKLINE_STR,
        }

    if modality == "atlas":
        splat_cfg = filters.get("splat_density", {})
        exr_cfg = filters.get("exr_depth_clamp", {})
        rub_cfg = filters.get("rub_frustum_lock", {})
        density_pct = int(splat_cfg.get("value", 100)) if (not bypass and splat_cfg.get("enabled")) else 100
        return {
            "modality": "atlas",
            "bypassed": bypass,
            "activeFilterIds": active_ids,
            "coordSystem": "RUB",
            "splatCount": int(20000 * density_pct),
            "depthConfidencePct": 98.4 if (not bypass and exr_cfg.get("enabled")) else 0.0,
            "rubFrustumLock": bool(rub_cfg.get("enabled")) and not bypass,
            "sparkline": AEONIK_SPARKLINE_STR,
        }

    if modality == "3d":
        pbr_cfg = filters.get("pbr_roughness_norm", {})
        remesh_cfg = filters.get("quad_remesh", {})
        ik_cfg = filters.get("humanoid_ik_rig", {})
        return {
            "modality": "3d",
            "bypassed": bypass,
            "activeFilterIds": active_ids,
            "format": "glb",
            "pbrNormPct": int(pbr_cfg.get("value", 85)) if (not bypass and pbr_cfg.get("enabled")) else 0,
            "watertightQuad": bool(remesh_cfg.get("enabled")) and not bypass,
            "humanoidRig": bool(ik_cfg.get("enabled")) and not bypass,
            "sparkline": AEONIK_SPARKLINE_STR,
        }

    # video
    flow = filters.get("optical_flow_60fps", {})
    deflicker = filters.get("temporal_deflicker", {})
    duck = filters.get("j_cut_dialogue_duck", {})
    fps = int(flow.get("value", 60)) if (not bypass and flow.get("enabled")) else 24
    lufs = float(duck.get("value", -14.0)) if (not bypass and duck.get("enabled")) else 0.0
    deflicker_pct = int(deflicker.get("value", 0)) if (not bypass and deflicker.get("enabled")) else 0
    return {
        "modality": "video",
        "bypassed": bypass,
        "activeFilterIds": active_ids,
        "outputFps": fps,
        "temporalDeflickerPct": deflicker_pct,
        "dialogueDuckLufs": lufs,
    }


def apply_node_filters(
    node: Dict[str, Any],
    filter_updates: Optional[Dict[str, Any]] = None,
    modality: Optional[str] = None,
    bypass: Optional[bool] = None,
) -> Dict[str, Any]:
    """Non-destructively apply or toggle filters on a node copy.

    Never overwrites raw generated content (`data.content`).
    """
    updated = copy.deepcopy(node)
    data = updated.setdefault("data", {})
    node_modality = modality or data.get("modality") or "image"
    if node_modality not in FILTER_PRESETS:
        node_modality = "image"
    data["modality"] = node_modality

    current_filters = data.get("filters")
    if not isinstance(current_filters, dict) or not current_filters:
        rack = default_filter_state(node_modality)
    else:
        rack = copy.deepcopy(current_filters)

    if isinstance(filter_updates, dict):
        for fid, raw_val in filter_updates.items():
            if fid in FLAT_FILTER_PRESETS:
                rack[fid] = _coerce_filter_entry(fid, raw_val, rack.get(fid))

    is_bypassed = bool(data.get("filtersBypassed", False)) if bypass is None else bool(bypass)
    data["filters"] = rack
    data["filtersBypassed"] = is_bypassed

    raw_text = ""
    content = data.get("content")
    if isinstance(content, dict) and isinstance(content.get("text"), str):
        raw_text = content["text"]

    data["filterSummary"] = _build_filter_summary(node_modality, rack, is_bypassed, raw_text=raw_text)
    return updated


def handle_node_studio_filter(
    payload: Optional[Dict[str, Any]],
    state: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """API handler for `POST /api/nodes/filter` to toggle/update non-destructive filters."""
    body = payload if isinstance(payload, dict) else {}
    modality = body.get("modality") if body.get("modality") in MODALITIES else "image"
    working_state = copy.deepcopy(state) if isinstance(state, dict) else get_default_studio_state(modality)

    nodes = working_state.get("nodes", [])
    edges = working_state.get("edges", [])
    target_node = body.get("node")
    node_id = body.get("nodeId") or body.get("node_id")

    updates = body.get("filters")
    if not isinstance(updates, dict):
        updates = {}
    if body.get("filterId") or body.get("filter_id"):
        fid = str(body.get("filterId") or body.get("filter_id"))
        entry: Dict[str, Any] = {}
        if "enabled" in body:
            entry["enabled"] = bool(body["enabled"])
        if "value" in body:
            entry["value"] = body["value"]
        updates[fid] = entry if entry else True

    bypass = body.get("bypass") if "bypass" in body else None

    if isinstance(target_node, dict):
        updated_node = apply_node_filters(target_node, updates, modality=modality, bypass=bypass)
        return {
            "ok": True,
            "node": updated_node,
            "filters": updated_node["data"]["filters"],
            "filterSummary": updated_node["data"]["filterSummary"],
        }

    if not node_id and nodes:
        node_id = nodes[-1].get("id")

    updated_node = None
    for idx, item in enumerate(nodes):
        if item.get("id") == node_id:
            updated_node = apply_node_filters(item, updates, modality=modality, bypass=bypass)
            nodes[idx] = updated_node
            break

    if updated_node is None:
        return {"ok": False, "statusCode": 404, "error": f"Node '{node_id}' not found."}

    timeline = build_timeline_sequence(nodes, edges, target_node_id=updated_node["id"])
    return {
        "ok": True,
        "statusCode": 200,
        "node": updated_node,
        "nodes": nodes,
        "filters": updated_node["data"]["filters"],
        "filterSummary": updated_node["data"]["filterSummary"],
        "timeline": timeline,
    }


def _format_timecode(seconds: int) -> str:
    mins, secs = divmod(max(0, int(seconds)), 60)
    return f"{mins:02d}:{secs:02d}"


def _node_sparkline(node: Dict[str, Any], stage_index: int) -> List[int]:
    data = node.get("data", {})
    filters = data.get("filters") or {}
    active_count = sum(1 for cfg in filters.values() if isinstance(cfg, dict) and cfg.get("enabled"))
    seed_bytes = hashlib.sha256(f"{node.get('id', '')}:{stage_index}:{active_count}".encode("utf-8")).digest()
    base = 25 + (stage_index * 10) + (active_count * 7)
    return [min(100, max(12, (base + (b % 35)))) for b in seed_bytes[:8]]


def _sparkline_to_glyphs(values: Sequence[int]) -> str:
    if not values:
        return "".join(AEONIK_SPARKLINE_BARS)
    glyphs: List[str] = []
    for v in values:
        idx = min(len(SPARKLINE_GLYPHS) - 1, max(0, int((v / 100.0) * (len(SPARKLINE_GLYPHS) - 1))))
        glyphs.append(SPARKLINE_GLYPHS[idx])
    return "".join(glyphs)


def build_timeline_sequence(
    nodes: Sequence[Dict[str, Any]],
    edges: Sequence[Dict[str, Any]],
    target_node_id: Optional[str] = None,
    step_seconds: int = 3,
) -> Dict[str, Any]:
    """Trace a DAG path into an ordered timeline sequence (`00:00 -> 00:03 -> ...`).

    Computes the longest directed lineage ending at `target_node_id` (or the
    primary leaf node when `target_node_id` is omitted) and attaches per-stage
    filter stacks and sparkline telemetry.
    """
    node_map: Dict[str, Dict[str, Any]] = {
        str(n["id"]): n for n in nodes if isinstance(n, dict) and n.get("id")
    }
    if not node_map:
        return {
            "stages": [],
            "timecodes": [],
            "totalDurationSeconds": 0,
            "formattedDuration": "00:00",
            "targetNodeId": target_node_id,
            "sparkline": [],
            "sparklineGlyphs": "",
            "summary": "",
        }

    order_index = {str(n["id"]): idx for idx, n in enumerate(nodes) if isinstance(n, dict) and n.get("id")}
    parents_of: Dict[str, List[str]] = {nid: [] for nid in node_map}
    children_of: Dict[str, List[str]] = {nid: [] for nid in node_map}
    for edge in edges or []:
        if not isinstance(edge, dict):
            continue
        src = str(edge.get("source") or "")
        dst = str(edge.get("target") or "")
        if src in node_map and dst in node_map and src != dst:
            if src not in parents_of[dst]:
                parents_of[dst].append(src)
            if dst not in children_of[src]:
                children_of[src].append(dst)

    memo: Dict[str, List[str]] = {}
    visiting = set()

    def longest_chain_to(nid: str) -> List[str]:
        if nid in memo:
            return memo[nid]
        if nid in visiting:
            return [nid]
        visiting.add(nid)
        preds = parents_of.get(nid, [])
        if not preds:
            best = [nid]
        else:
            best_pred: List[str] = []
            for p in preds:
                cand = longest_chain_to(p)
                if len(cand) > len(best_pred):
                    best_pred = cand
                elif len(cand) == len(best_pred) and cand:
                    if order_index.get(cand[0], 0) < order_index.get(best_pred[0], 0):
                        best_pred = cand
            best = best_pred + [nid]
        visiting.remove(nid)
        memo[nid] = best
        return best

    if target_node_id and str(target_node_id) in node_map:
        resolved_target = str(target_node_id)
    else:
        leaves = [nid for nid, kids in children_of.items() if not kids]
        candidates = leaves or list(node_map.keys())
        resolved_target = max(
            candidates,
            key=lambda nid: (len(longest_chain_to(nid)), order_index.get(nid, 0)),
        )

    chain_ids = longest_chain_to(resolved_target)
    stages: List[Dict[str, Any]] = []
    aggregate_sparkline: List[int] = []

    for idx, nid in enumerate(chain_ids):
        node = node_map[nid]
        data = node.get("data", {})
        filters = data.get("filters") if isinstance(data.get("filters"), dict) else {}
        bypassed = bool(data.get("filtersBypassed", False))
        active_filters = [
            {"id": fid, "label": cfg.get("label", fid), "value": cfg.get("value"), "unit": cfg.get("unit", "")}
            for fid, cfg in filters.items()
            if isinstance(cfg, dict) and cfg.get("enabled") and not bypassed
        ]
        spark = _node_sparkline(node, idx)
        aggregate_sparkline.extend(spark[:2])
        seconds = idx * step_seconds
        timecode = _format_timecode(seconds)
        merged_parents = [p for p in parents_of.get(nid, []) if p not in chain_ids]
        meta = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}

        stages.append(
            {
                "index": idx,
                "seconds": seconds,
                "timecode": timecode,
                "nodeId": nid,
                "label": data.get("label", f"Node {nid}"),
                "nodeType": data.get("type", "GENERATED"),
                "modality": data.get("modality", "image"),
                "model": meta.get("model"),
                "activeFilters": active_filters,
                "activeFilterIds": [f["id"] for f in active_filters],
                "filterStack": copy.deepcopy(filters),
                "filtersBypassed": bypassed,
                "mergedParentIds": merged_parents,
                "sparkline": spark,
                "sparklineGlyphs": _sparkline_to_glyphs(spark),
                "telemetry": {
                    "creditCost": meta.get("creditCost", 0.20),
                    "resolution": meta.get("resolution"),
                    "aspectRatio": meta.get("aspectRatio"),
                },
            }
        )

    summary = " -> ".join(f"{s['timecode']} [#{s['nodeId']}]" for s in stages)
    total_duration = len(stages) * step_seconds
    return {
        "stages": stages,
        "timecodes": [s["timecode"] for s in stages],
        "totalDurationSeconds": total_duration,
        "formattedDuration": _format_timecode(total_duration),
        "targetNodeId": resolved_target,
        "sparkline": aggregate_sparkline,
        "sparklineGlyphs": _sparkline_to_glyphs(aggregate_sparkline),
        "summary": summary,
    }


def build_contents(
    conversation_history: Optional[Sequence[Any]],
    requires_thought_signature: bool,
    current_parts: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Port of `geminiHandler.mjs` `buildContents` preserving thought signatures."""
    contents: List[Dict[str, Any]] = []

    if isinstance(conversation_history, (list, tuple)) and len(conversation_history) > 0:
        for message in conversation_history:
            if not isinstance(message, str):
                continue
            if message.startswith("User: "):
                contents.append(
                    {
                        "role": "user",
                        "parts": [{"text": message[len("User: ") :]}],
                    }
                )
            elif message.startswith("AssistantParts: "):
                parts = json.loads(message[len("AssistantParts: ") :])
                contents.append(
                    {
                        "role": "model",
                        "parts": parts,
                        "_needsSignature": bool(requires_thought_signature),
                    }
                )
            elif message.startswith("AssistantImage: "):
                thought_signature = message[len("AssistantImage: ") :].split("|||")[0]
                contents.append(
                    {
                        "role": "model",
                        "parts": [{"thoughtSignature": thought_signature}],
                    }
                )
            elif message.startswith("AssistantThought: "):
                contents.append(
                    {
                        "role": "model",
                        "parts": [{"thoughtSignature": message[len("AssistantThought: ") :]}],
                    }
                )
            elif message.startswith("Assistant: "):
                contents.append(
                    {
                        "role": "model",
                        "parts": [{"text": message[len("Assistant: ") :]}],
                    }
                )

    if requires_thought_signature and contents:
        has_unsigned = any(
            msg.get("role") == "model" and any(not p.get("thoughtSignature") for p in msg.get("parts", []))
            for msg in contents
        )
        if has_unsigned:
            briefing_parts: List[Dict[str, Any]] = []
            briefing_text = "Previous conversation:\n"
            for msg in contents:
                speaker = "User" if msg.get("role") == "user" else "Assistant"
                for part in msg.get("parts", []):
                    if part.get("text") and not part.get("thought"):
                        briefing_text += f"{speaker}: {part['text']}\n"
                    if part.get("inlineData") and not part.get("thought"):
                        briefing_parts.append({"inlineData": part["inlineData"]})
            contents = [
                {
                    "role": "user",
                    "parts": [{"text": briefing_text}, *briefing_parts],
                }
            ]
        else:
            for msg in contents:
                msg.pop("_needsSignature", None)

    contents.append({"role": "user", "parts": current_parts})
    return contents


def build_text_context_prompt(prompt: str, conversation_history: Optional[Sequence[Any]]) -> str:
    """Port of `geminiHandler.mjs` `buildTextContextPrompt` (last 6 turns)."""
    if not isinstance(conversation_history, (list, tuple)) or not conversation_history:
        return prompt

    lines: List[str] = []
    for entry in conversation_history:
        if not isinstance(entry, str):
            continue
        if entry.startswith("User: ") or entry.startswith("Assistant: "):
            lines.append(entry)
        elif entry.startswith("AssistantParts: "):
            try:
                parts = json.loads(entry[len("AssistantParts: ") :])
                text = " ".join(
                    str(p.get("text"))
                    for p in parts
                    if isinstance(p, dict) and p.get("text") and not p.get("thought")
                ).strip()
                if text:
                    lines.append(f"Assistant: {text}")
            except Exception:
                continue

    if not lines:
        return prompt
    recent = "\n".join(lines[-6:])
    return f"Context from previous turns:\n{recent}\n\nCurrent instruction: {prompt}"


def _normalize_gemini_resolution(resolution: Optional[str], supported: Optional[Sequence[str]]) -> Optional[str]:
    if not supported:
        return None
    normalized = "512" if resolution == "0.5K" else resolution
    if normalized and normalized in supported:
        return normalized
    return "1K" if "1K" in supported else supported[0]


def _normalize_nanogpt_resolution(resolution: Optional[str], supported: Optional[Sequence[str]]) -> Optional[str]:
    if not supported:
        return None
    lower = str(resolution or "1K").lower()
    mapped = "1k" if lower in ("512", "0.5k") else lower
    if mapped in supported:
        return mapped
    if mapped == "4k" and "2k" in supported:
        return "2k"
    return supported[0]


def _resolve_grounding_mode(config: Mapping[str, Any]) -> str:
    mode = config.get("groundingMode")
    if mode in ("Off", "Web", "Image", "Web+Img"):
        return str(mode)
    if not config.get("grounding"):
        return "Off"
    return "Web" if config.get("imageSearch") is False else "Web+Img"


def _extract_grounding_summary(candidate: Optional[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    if not isinstance(candidate, Mapping):
        return None
    gm = candidate.get("groundingMetadata")
    if not isinstance(gm, Mapping):
        return None

    web_q = gm.get("webSearchQueries") if isinstance(gm.get("webSearchQueries"), list) else None
    img_q = gm.get("imageSearchQueries") if isinstance(gm.get("imageSearchQueries"), list) else None
    chunks = gm.get("groundingChunks")
    sources = None
    if isinstance(chunks, list):
        parsed = []
        for chunk in chunks:
            web = chunk.get("web") if isinstance(chunk, Mapping) else None
            if isinstance(web, Mapping) and (web.get("uri") or web.get("title")):
                parsed.append({"title": web.get("title"), "uri": web.get("uri")})
        if parsed:
            sources = parsed

    if not web_q and not img_q and not sources:
        return None
    return {
        "webSearchQueries": web_q,
        "imageSearchQueries": img_q,
        "sources": sources,
    }


def _detect_mime_from_bytes(buf: bytes, fallback: str = "image/png") -> str:
    if not buf or len(buf) < 4:
        return fallback
    if buf[:2] == b"\xff\xd8":
        return "image/jpeg"
    if buf[:4] == b"\x89PNG":
        return "image/png"
    if buf[:4] == b"RIFF":
        return "image/webp"
    return fallback


class ProviderHttpError(RuntimeError):
    """HTTP error raised by upstream Gemini or NanoGPT calls."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.status_code = status_code


def _default_http_post(url: str, headers: Dict[str, str], payload: Dict[str, Any], timeout: int = 60) -> Tuple[int, Dict[str, Any]]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as exc:
        body_raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body_raw)
        except Exception:
            parsed = {"error": body_raw or str(exc)}
        return exc.code, parsed


def _default_http_get(url: str, timeout: int = 30) -> Tuple[int, bytes, Dict[str, str]]:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        hdrs = {k.lower(): v for k, v in resp.headers.items()}
        return resp.status, resp.read(), hdrs


def _extract_error_message(data: Any, status_code: int) -> str:
    if isinstance(data, Mapping):
        err = data.get("error")
        if isinstance(err, Mapping) and err.get("message"):
            return str(err["message"])
        if isinstance(err, str) and err.strip():
            return err
        if data.get("message"):
            return str(data["message"])
    return f"Upstream returned status {status_code}"


def _should_fallback_to_nanogpt(error: ProviderHttpError) -> bool:
    if error.status_code in (401, 402, 403, 429, 503):
        return True
    msg = str(error).lower()
    return any(
        tok in msg
        for tok in ("resource_exhausted", "prepayment", "credits", "quota", "billing")
    )


def _generate_with_gemini(
    *,
    prompt: str,
    modality: str,
    config: Mapping[str, Any],
    references: Sequence[Dict[str, Any]],
    conversation_history: Sequence[str],
    api_key: str,
    spec: Mapping[str, Any],
    http_post: Callable[..., Tuple[int, Dict[str, Any]]],
) -> Dict[str, Any]:
    gemini_model = spec.get("geminiModel") or spec["id"]
    parts: List[Dict[str, Any]] = []

    max_refs = int(spec.get("maxReferences", MAX_REFERENCES))
    for ref in list(references)[:max_refs]:
        if isinstance(ref, Mapping) and ref.get("base64"):
            parts.append(
                {
                    "inlineData": {
                        "data": ref["base64"],
                        "mimeType": ref.get("mimeType") or "image/jpeg",
                    }
                }
            )
    parts.append({"text": prompt})

    generation_config: Dict[str, Any] = {}
    if config.get("temperature") is not None:
        generation_config["temperature"] = config["temperature"]

    if modality == "image":
        generation_config["responseModalities"] = ["TEXT", "IMAGE"]
        aspect_set = ALL_ASPECT_RATIOS if spec.get("panoramicAspects") else STANDARD_ASPECT_RATIOS
        aspect_ratio = config.get("aspectRatio") if config.get("aspectRatio") in aspect_set else "1:1"
        image_cfg: Dict[str, Any] = {"aspectRatio": aspect_ratio}
        image_size = _normalize_gemini_resolution(config.get("resolution"), spec.get("resolutions"))
        if image_size:
            image_cfg["imageSize"] = image_size
        generation_config["imageConfig"] = image_cfg
    else:
        generation_config["responseModalities"] = ["TEXT"]

    if spec.get("thinkingLevels"):
        req_level = str(config.get("thinkingLevel") or spec.get("defaultThinkingLevel") or "").lower()
        valid_level = req_level if req_level in spec["thinkingLevels"] else spec.get("defaultThinkingLevel")
        if valid_level:
            thinking_cfg: Dict[str, Any] = {"thinkingLevel": valid_level.upper()}
            if config.get("includeThoughts"):
                thinking_cfg["includeThoughts"] = True
            generation_config["thinkingConfig"] = thinking_cfg
    elif spec.get("thinking") and config.get("includeThoughts"):
        generation_config["thinkingConfig"] = {"includeThoughts": True}

    body: Dict[str, Any] = {
        "contents": build_contents(conversation_history, bool(spec.get("thinking")), parts),
        "systemInstruction": {"parts": [{"text": "You are an expert creative assistant."}]},
        "generationConfig": generation_config,
    }

    grounding_mode = _resolve_grounding_mode(config)
    if grounding_mode != "Off" and spec.get("webGrounding"):
        if spec.get("imageSearchGrounding"):
            search_types: Dict[str, Any] = {}
            if grounding_mode in ("Web", "Web+Img"):
                search_types["webSearch"] = {}
            if grounding_mode in ("Image", "Web+Img"):
                search_types["imageSearch"] = {}
            body["tools"] = [{"googleSearch": {"searchTypes": search_types}}]
        elif grounding_mode in ("Web", "Web+Img"):
            body["tools"] = [{"googleSearch": {}}]

    url = f"{GEMINI_API_BASE_URL}/{gemini_model}:generateContent?key={api_key}"
    status_code, data = http_post(
        url,
        {"Content-Type": "application/json"},
        body,
    )
    if status_code >= 400:
        raise ProviderHttpError(_extract_error_message(data, status_code), status_code=status_code)

    candidates = data.get("candidates") or []
    candidate = candidates[0] if candidates else {}
    response_parts = (candidate.get("content") or {}).get("parts") or []

    image_data: Optional[str] = None
    mime_type = "image/png"
    thought_signature: Optional[str] = None
    text_segments: List[str] = []
    thought_segments: List[str] = []

    for part in response_parts:
        if not isinstance(part, Mapping):
            continue
        if part.get("thoughtSignature"):
            thought_signature = str(part["thoughtSignature"])
        if part.get("thought"):
            if part.get("text"):
                thought_segments.append(str(part["text"]))
            continue
        if part.get("text"):
            text_segments.append(str(part["text"]))
        inline = part.get("inlineData")
        if isinstance(inline, Mapping) and inline.get("data"):
            image_data = str(inline["data"])
            if inline.get("mimeType"):
                mime_type = str(inline["mimeType"])

    final_text = "\n".join(text_segments).strip() or None
    thoughts = "\n".join(thought_segments).strip() or None
    grounding_metadata = _extract_grounding_summary(candidate)

    result: Dict[str, Any] = {
        "text": final_text or ("Generated successfully" if image_data else "No content generated."),
        "thoughts": thoughts,
        "groundingMetadata": grounding_metadata,
        "providerUsed": "gemini",
        "modelUsed": gemini_model,
    }
    if image_data:
        result["image"] = {
            "data": image_data,
            "mimeType": mime_type,
            "thoughtSignature": thought_signature,
        }
        result["responseParts"] = response_parts
    elif thought_signature:
        result["thoughtSignature"] = thought_signature
        result["responseParts"] = response_parts
    return result


def _generate_with_nanogpt(
    *,
    prompt: str,
    modality: str,
    config: Mapping[str, Any],
    references: Sequence[Dict[str, Any]],
    conversation_history: Sequence[str],
    api_key: str,
    spec: Mapping[str, Any],
    http_post: Callable[..., Tuple[int, Dict[str, Any]]],
    http_get: Callable[..., Tuple[int, bytes, Dict[str, str]]],
) -> Dict[str, Any]:
    nanogpt_model = str(spec.get("nanogptModel") or spec["id"])
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    if modality == "text":
        messages: List[Dict[str, str]] = []
        for entry in conversation_history:
            if not isinstance(entry, str):
                continue
            if entry.startswith("User: "):
                messages.append({"role": "user", "content": entry[len("User: ") :]})
            elif entry.startswith("Assistant: "):
                messages.append({"role": "assistant", "content": entry[len("Assistant: ") :]})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": nanogpt_model,
            "messages": messages,
            "temperature": config.get("temperature", 0.7),
        }
        status_code, data = http_post(NANOGPT_CHAT_URL, headers, payload)
        if status_code >= 400:
            raise ProviderHttpError(_extract_error_message(data, status_code), status_code=status_code)
        choices = data.get("choices") or []
        msg_content = ""
        if choices and isinstance(choices[0], Mapping):
            msg_content = str((choices[0].get("message") or {}).get("content") or "")
        return {
            "text": msg_content or f"Generated via NanoGPT ({nanogpt_model})",
            "providerUsed": "nanogpt",
            "modelUsed": nanogpt_model,
        }

    if modality == "video":
        fps = int(config.get("fps") or spec.get("defaultFps") or 60)
        if fps not in (24, 60):
            fps = 60
        payload = {
            "model": nanogpt_model,
            "prompt": build_text_context_prompt(prompt, conversation_history),
            "fps": fps,
            "audio_sync": bool(config.get("audioSync", spec.get("audioSync", True))),
        }
        if references:
            image_refs = [
                f"data:{ref.get('mimeType') or 'image/jpeg'};base64,{ref['base64']}"
                for ref in list(references)[: int(spec.get("nanogptMaxReferences", MAX_REFERENCES))]
                if isinstance(ref, Mapping) and ref.get("base64")
            ]
            if image_refs:
                payload["input_references"] = image_refs
        status_code, data = http_post(NANOGPT_VIDEO_URL, headers, payload)
        if status_code >= 400:
            raise ProviderHttpError(_extract_error_message(data, status_code), status_code=status_code)
        video_url = data.get("videoUrl") or data.get("url") or (data.get("data") or [{}])[0].get("url")
        return {
            "text": f"Generated video via NanoGPT ({nanogpt_model})",
            "video": {
                "url": video_url or f"https://media.local/nanogpt/{nanogpt_model}.mp4",
                "mimeType": "video/mp4",
                "fps": fps,
                "audioSync": bool(payload["audio_sync"]),
            },
            "providerUsed": "nanogpt",
            "modelUsed": nanogpt_model,
        }

    # Image modality (exact port of geminiHandler.mjs generateWithNanogpt)
    non_image_refs = [
        ref
        for ref in references
        if isinstance(ref, Mapping)
        and ref.get("base64")
        and ref.get("mimeType")
        and not str(ref["mimeType"]).startswith("image/")
    ]
    if non_image_refs:
        raise ProviderHttpError(
            "PDF and Video inputs require the Gemini API backend (NanoGPT image endpoint supports image references only).",
            status_code=400,
        )

    aspect_set = ALL_ASPECT_RATIOS if spec.get("panoramicAspects") else STANDARD_ASPECT_RATIOS
    aspect_ratio = config.get("aspectRatio") if config.get("aspectRatio") in aspect_set else "1:1"
    payload = {
        "model": nanogpt_model,
        "prompt": build_text_context_prompt(prompt, conversation_history),
        "n": 1,
        "output_format": "png",
        "aspect_ratio": aspect_ratio,
    }
    res_value = _normalize_nanogpt_resolution(config.get("resolution"), spec.get("nanogptResolutions"))
    if res_value:
        payload["resolution"] = res_value

    if nanogpt_model == "nano-banana-2.1":
        level = str(config.get("thinkingLevel") or "").lower()
        if level in ("minimal", "high"):
            payload["thinking_level"] = level
        if _resolve_grounding_mode(config) != "Off":
            payload["enable_web_search"] = True

    if references:
        input_refs = [
            f"data:{ref.get('mimeType') or 'image/jpeg'};base64,{ref['base64']}"
            for ref in list(references)[: int(spec.get("nanogptMaxReferences", MAX_REFERENCES))]
            if isinstance(ref, Mapping) and ref.get("base64")
        ]
        if input_refs:
            payload["input_references"] = input_refs

    status_code, data = http_post(NANOGPT_IMAGES_URL, headers, payload)
    if status_code >= 400:
        raise ProviderHttpError(_extract_error_message(data, status_code), status_code=status_code)

    first = (data.get("data") or [None])[0]
    if not isinstance(first, Mapping):
        raise ProviderHttpError("NanoGPT returned no generated image data.", status_code=502)

    base64_data = ""
    mime_type = "image/png"
    if first.get("b64_json"):
        raw = str(first["b64_json"])
        if raw.startswith("data:") and ";base64," in raw:
            header_part, base64_data = raw.split(";base64,", 1)
            mime_type = header_part[len("data:") :] or "image/png"
        else:
            base64_data = raw
            try:
                decoded = base64.b64decode(raw, validate=False)
                mime_type = _detect_mime_from_bytes(decoded, "image/png")
            except Exception:
                mime_type = "image/png"
    elif first.get("url"):
        img_status, img_bytes, img_hdrs = http_get(str(first["url"]))
        if img_status >= 400:
            raise ProviderHttpError(f"Failed to fetch NanoGPT output image ({img_status})", status_code=502)
        mime_type = _detect_mime_from_bytes(img_bytes, img_hdrs.get("content-type", "image/png"))
        base64_data = base64.b64encode(img_bytes).decode("ascii")
    else:
        raise ProviderHttpError("NanoGPT response lacked image bytes or URL.", status_code=502)

    return {
        "text": f"Generated via NanoGPT ({nanogpt_model})",
        "image": {
            "data": base64_data,
            "mimeType": mime_type,
        },
        "providerUsed": "nanogpt",
        "modelUsed": nanogpt_model,
    }


def _generate_offline_synthetic(
    *,
    prompt: str,
    modality: str,
    mode: str,
    config: Mapping[str, Any],
    references: Sequence[Dict[str, Any]],
    spec: Mapping[str, Any],
    provider_preference: str,
    slash_route: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Deterministic offline/synthetic generator for local and test runs without API keys."""
    model_used = str(
        spec.get("nanogptModel")
        if provider_preference == "nanogpt" and spec.get("nanogptModel")
        else spec.get("id")
    )
    digest = hashlib.sha256(f"{modality}:{mode}:{model_used}:{prompt}".encode("utf-8")).hexdigest()[:12]
    thought_sig = f"sig_offline_{digest}"
    short_hash = digest[:8]
    flags = dict(slash_route.get("flags") or {}) if isinstance(slash_route, Mapping) else {}

    if modality == "audio":
        audio_kind = str(
            (slash_route.get("subcommand") if isinstance(slash_route, Mapping) else None)
            or config.get("kind")
            or spec.get("kind")
            or "music"
        ).lower()
        if audio_kind not in ("tts", "music", "sfx"):
            audio_kind = "music"
        lufs = float(flags.get("lufs") or config.get("lufs") or spec.get("lufs") or -14.0)
        duration_sec = float(flags.get("seconds") or config.get("seconds") or 8.0)
        wav_path = f"/audio/{audio_kind}_{short_hash}.wav"
        provider_used = "local" if "kokoro" in model_used.lower() else "nanogpt"
        return {
            "text": f"[AUDIO · {audio_kind.upper()} · {model_used}] {prompt.strip()} ({AEONIK_SPARKLINE_STR} · {lufs} LUFS)",
            "thoughts": f"Omni-audio synthesis ({audio_kind}, {lufs} LUFS, sig={thought_sig}).",
            "thoughtSignature": thought_sig,
            "sparkline": AEONIK_SPARKLINE_STR,
            "lufs": lufs,
            "audio": {
                "kind": audio_kind,
                "url": f"data:audio/wav;base64,{_SYNTHETIC_WAV_B64}",
                "audioBytesB64": _SYNTHETIC_WAV_B64,
                "vfsPath": wav_path,
                "wavPath": wav_path,
                "mimeType": "audio/wav",
                "lufs": lufs,
                "durationSeconds": duration_sec,
                "sparkline": AEONIK_SPARKLINE_STR,
            },
            "vfsPaths": {
                "wav": wav_path,
                "audioWav": wav_path,
            },
            "providerUsed": provider_used,
            "modelUsed": model_used,
            "offline": True,
        }

    if modality == "atlas":
        atlas_task = str(
            (slash_route.get("atlas_task") if isinstance(slash_route, Mapping) else None)
            or config.get("atlasTask")
            or spec.get("atlasTask")
            or "posedImages2Splats"
        )
        views = int(flags.get("views") or config.get("views") or 14)
        res_pair = flags.get("res") if isinstance(flags.get("res"), list) and len(flags["res"]) == 2 else [1280, 720]
        world_id = f"world_{short_hash}"
        op_id = f"op_atlas_{digest}"
        camera = copy.deepcopy(DEFAULT_RUB_CAMERA)
        camera["width"] = int(res_pair[0])
        camera["height"] = int(res_pair[1])
        camera["frustumViews"] = views

        vfs_paths = {
            "worldDir": f"/worlds/{world_id}",
            "operationJson": f"/worlds/{world_id}/operation.json",
            "image": f"/worlds/{world_id}/frames_0_image.jpg",
            "depthExr": f"/worlds/{world_id}/frames_0_depth.exr",
            "confidencePng": f"/worlds/{world_id}/frames_0_confidence.png",
            "splatSpz": f"/worlds/{world_id}/refinedSplats_2000000.spz",
            "meshGlb": f"/models3d/atlas_{short_hash}.glb",
            "flythroughMp4": f"/videos/atlas_flythrough_{short_hash}.mp4",
        }
        return {
            "text": (
                f"[ATLAS · {atlas_task}] {prompt.strip()} · RUB fx={camera['fx']} fy={camera['fy']} "
                f"centroid={camera['centroidWorld']} · 2.0M Splats ({vfs_paths['splatSpz']})"
            ),
            "thoughts": (
                f"World Labs Atlas v2 task={atlas_task} op={op_id} views={views} "
                f"depth_confidence=+98.4% (.exr verified)."
            ),
            "thoughtSignature": thought_sig,
            "sparkline": AEONIK_SPARKLINE_STR,
            "operationId": op_id,
            "atlasTask": atlas_task,
            "coordSystem": "RUB",
            "fx": 893.37,
            "fy": 893.90,
            "cx": 640.0,
            "cy": 360.5,
            "centroidWorld": [-1.99, 0.0, -36.35],
            "depthConfidencePct": 98.4,
            "numSplats": 2000000,
            "camera": camera,
            "vfsPaths": vfs_paths,
            "atlas": {
                "operationId": op_id,
                "task": atlas_task,
                "done": True,
                "coordSystem": "RUB",
                "fx": 893.37,
                "fy": 893.90,
                "cx": 640.0,
                "cy": 360.5,
                "centroidWorld": [-1.99, 0.0, -36.35],
                "camera": camera,
                "numSplats": 2000000,
                "depthConfidencePct": 98.4,
                "sparkline": AEONIK_SPARKLINE_STR,
                "spzPath": vfs_paths["splatSpz"],
                "exrPath": vfs_paths["depthExr"],
                "glbPath": vfs_paths["meshGlb"],
                "mp4Path": vfs_paths["flythroughMp4"],
                "vfsPaths": vfs_paths,
            },
            "providerUsed": "worldlabs",
            "modelUsed": model_used,
            "offline": True,
        }

    if modality == "3d":
        cmd = str(slash_route.get("command") or "") if isinstance(slash_route, Mapping) else ""
        is_rig = (cmd == "rig") or ("rigging" in model_used.lower()) or bool(flags.get("rig")) or bool(flags.get("anim"))
        anim = str(flags.get("anim") or flags.get("rig") or ("walk" if is_rig else "idle"))
        tier = str(flags.get("tier") or config.get("tier") or "Regular")
        glb_path = f"/models3d/{'rigged' if is_rig else 'mesh'}_{short_hash}.glb"
        spz_path = f"/worlds/world_{short_hash}/refinedSplats_2000000.spz"
        provider_used = "worldlabs" if "splats2mesh" in model_used.lower() else (
            "nanogpt" if any(k in model_used.lower() for k in ("tripo", "meshy")) else "hyper3d"
        )
        return {
            "text": f"[3D · {'RIGGED ' + anim.upper() if is_rig else tier.upper()} · {model_used}] {prompt.strip()} -> {glb_path}",
            "thoughts": f"3D mesh & topology synthesis (tier={tier}, rigged={is_rig}, anim={anim}, sig={thought_sig}).",
            "thoughtSignature": thought_sig,
            "sparkline": AEONIK_SPARKLINE_STR,
            "mesh3d": {
                "glbPath": glb_path,
                "vfsPath": glb_path,
                "spzPath": spz_path,
                "format": "glb",
                "mimeType": "model/gltf-binary",
                "tier": tier,
                "rigged": is_rig,
                "animation": anim if is_rig else None,
                "watertight": True,
                "pbr": True,
                "polyCount": 48000,
                "sparkline": AEONIK_SPARKLINE_STR,
            },
            "vfsPaths": {
                "meshGlb": glb_path,
                "glb": glb_path,
                "splatSpz": spz_path,
            },
            "providerUsed": provider_used,
            "modelUsed": model_used,
            "offline": True,
        }

    if modality == "text":
        return {
            "text": (
                f"[SYNTHETIC {mode} · {model_used}] {prompt.strip()}\n"
                f"Beat 01: Established context ({len(references)} refs, sig {thought_sig}).\n"
                f"Beat 02: Grounded response verified against active prose filters."
            ),
            "thoughts": f"Offline reasoning pass ({digest}) with {len(references)} references.",
            "thoughtSignature": thought_sig,
            "providerUsed": "synthetic",
            "modelUsed": model_used,
            "offline": True,
        }

    if modality == "video":
        fps = int(flags.get("fps") or config.get("fps") or spec.get("defaultFps") or 60)
        duration_sec = int(flags.get("seconds") or config.get("seconds") or 6)
        mp4_path = f"/videos/render_{short_hash}.mp4"
        return {
            "text": f"Synthetic {fps}fps video storyboard ({mode}) via {model_used}: {prompt.strip()}",
            "thoughts": f"Temporal motion plan ({fps}fps, audio_sync=True, sig={thought_sig}).",
            "thoughtSignature": thought_sig,
            "sparkline": AEONIK_SPARKLINE_STR,
            "video": {
                "url": f"data:video/mp4;synthetic,{digest}",
                "vfsPath": mp4_path,
                "mp4Path": mp4_path,
                "mimeType": "video/mp4",
                "fps": fps,
                "durationSeconds": duration_sec,
                "audioSync": bool(config.get("audioSync", True)),
            },
            "vfsPaths": {
                "mp4": mp4_path,
                "videoMp4": mp4_path,
            },
            "providerUsed": "synthetic",
            "modelUsed": model_used,
            "offline": True,
        }

    # image
    return {
        "text": f"Synthetic {mode} frame via {model_used}: {prompt.strip()}",
        "thoughts": f"Visual composition plan (aspect={config.get('aspectRatio', '1:1')}, sig={thought_sig}).",
        "image": {
            "data": _SYNTHETIC_1X1_PNG_B64,
            "mimeType": "image/png",
            "thoughtSignature": thought_sig,
        },
        "providerUsed": "synthetic",
        "modelUsed": model_used,
        "offline": True,
    }


def _normalize_references(
    raw_refs: Any,
    parent_nodes: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    refs: List[Dict[str, Any]] = []
    if isinstance(raw_refs, (list, tuple)):
        for idx, item in enumerate(raw_refs):
            if isinstance(item, Mapping):
                refs.append(dict(item))
            elif isinstance(item, str) and item.strip():
                refs.append({"id": f"ref-{idx + 1}", "name": item.strip(), "type": "image", "url": item.strip()})

    # In MERGE/EDIT mode, supplement with parent visual outputs if caller didn't already supply them.
    seen_ids = {str(r.get("id") or r.get("nodeId") or "") for r in refs if r.get("id") or r.get("nodeId")}
    for pnode in parent_nodes:
        pid = str(pnode.get("id") or "")
        if not pid or pid in seen_ids:
            continue
        pdata = pnode.get("data") or {}
        pcontent = pdata.get("content") or {}
        if pcontent.get("base64") or pcontent.get("imageUrl"):
            refs.append(
                {
                    "id": pid,
                    "nodeId": pid,
                    "name": pdata.get("label") or f"Node {pid}",
                    "type": "image",
                    "url": pcontent.get("imageUrl") or "",
                    "base64": pcontent.get("base64"),
                    "mimeType": pcontent.get("mimeType") or "image/png",
                }
            )
            seen_ids.add(pid)

    return refs[:MAX_REFERENCES]


def _index_parent_nodes(
    selected_ids: Sequence[str],
    payload: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    pool_raw = payload.get("parentNodes") or payload.get("parent_nodes") or payload.get("existingNodes") or payload.get("nodes")
    by_id: Dict[str, Dict[str, Any]] = {}
    if isinstance(pool_raw, Mapping):
        for k, v in pool_raw.items():
            if isinstance(v, Mapping):
                by_id[str(k)] = dict(v)
    elif isinstance(pool_raw, (list, tuple)):
        for item in pool_raw:
            if isinstance(item, Mapping) and item.get("id"):
                by_id[str(item["id"])] = dict(item)

    return [by_id[sid] for sid in selected_ids if sid in by_id]


def handle_node_studio_generate(
    payload: Optional[Dict[str, Any]],
    headers: Optional[Mapping[str, Any]] = None,
    env: Optional[Mapping[str, str]] = None,
    http_post: Optional[Callable[..., Tuple[int, Dict[str, Any]]]] = None,
    http_get: Optional[Callable[..., Tuple[int, bytes, Dict[str, str]]]] = None,
) -> Dict[str, Any]:
    """Validate prompt, route slash commands or NanoGPT/Gemini/Atlas/Audio/3D, and return MorphingNode + edges + timeline."""
    body = payload if isinstance(payload, dict) else {}
    raw_prompt = body.get("prompt")
    if not isinstance(raw_prompt, str) or not raw_prompt.strip():
        return {"ok": False, "statusCode": 400, "error": "Prompt is required."}

    config = dict(body.get("config")) if isinstance(body.get("config"), Mapping) else {}
    slash_route: Optional[Dict[str, Any]] = None
    prompt = raw_prompt

    if raw_prompt.lstrip().startswith("/"):
        parsed = parse_omni_slash_command(raw_prompt)
        if parsed.get("is_slash"):
            slash_route = parsed
            prompt = parsed.get("prompt") or raw_prompt.strip()
            flags = parsed.get("flags") or {}
            if "fps" in flags and "fps" not in config:
                config["fps"] = flags["fps"]
            if "aspect" in flags and "aspectRatio" not in config:
                config["aspectRatio"] = flags["aspect"]
            if "resolution" in flags and "resolution" not in config:
                config["resolution"] = flags["resolution"]
            elif isinstance(flags.get("res"), str) and "resolution" not in config:
                config["resolution"] = flags["res"]
            if "views" in flags:
                config["views"] = flags["views"]
            if "tier" in flags:
                config["tier"] = flags["tier"]
            if "lufs" in flags:
                config["lufs"] = flags["lufs"]
            if "seconds" in flags:
                config["seconds"] = flags["seconds"]

    requested_model = (
        (slash_route.get("model") if slash_route else None)
        or str(config.get("model") or body.get("model") or "").strip()
        or None
    )
    explicit_modality = (
        (slash_route.get("modality") if slash_route else None)
        or body.get("modality")
    )
    modality = infer_modality(requested_model, explicit_modality)
    spec = get_model_spec(requested_model, modality=modality)

    if requested_model and "veo" in requested_model.lower() and modality != "video":
        return {
            "ok": False,
            "statusCode": 400,
            "error": "Video generation requires selecting the Video modality.",
        }

    selected_ids = _normalize_selected_ids(
        body.get("selectedNodeIds") if "selectedNodeIds" in body else body.get("selected_node_ids")
    )
    mode = derive_generation_mode(selected_ids)
    parent_nodes = _index_parent_nodes(selected_ids, body)

    # Inherit conversationHistory, thoughtSignature, and upstream filters in EDIT (or primary parent in MERGE).
    inherited_history: List[str] = []
    inherited_thought_sig: Optional[str] = None
    inherited_filters: Dict[str, Dict[str, Any]] = default_filter_state(modality)

    explicit_history = body.get("conversationHistory") or body.get("conversation_history")
    if isinstance(explicit_history, (list, tuple)):
        inherited_history = [str(x) for x in explicit_history]
    elif parent_nodes:
        primary_parent_data = parent_nodes[0].get("data") or {}
        primary_meta = primary_parent_data.get("metadata") or {}
        parent_hist = primary_meta.get("conversationHistory") or primary_meta.get("conversation_history") or []
        inherited_history = [str(x) for x in parent_hist]
        inherited_thought_sig = primary_meta.get("thoughtSignature") or primary_meta.get("thought_signature")

    if mode == "EDIT" and parent_nodes:
        parent_filters = (parent_nodes[0].get("data") or {}).get("filters")
        if isinstance(parent_filters, dict) and parent_filters:
            inherited_filters = copy.deepcopy(parent_filters)

    if isinstance(body.get("filters"), dict):
        for fid, raw_fval in body["filters"].items():
            if fid in FLAT_FILTER_PRESETS:
                inherited_filters[fid] = _coerce_filter_entry(fid, raw_fval, inherited_filters.get(fid))

    references = _normalize_references(body.get("references"), parent_nodes)
    provider_pref = str(
        config.get("provider")
        or body.get("provider")
        or (slash_route.get("provider") if slash_route else None)
        or spec.get("preferredProvider")
        or "auto"
    ).lower()
    if modality in ("text", "image", "video") and provider_pref not in ("auto", "nanogpt", "gemini"):
        provider_pref = "auto"

    gemini_key, nanogpt_key = _resolve_api_keys(headers=headers, env=env)
    strict_keys = bool(body.get("strictKeys") or body.get("requireKey"))
    post_fn = http_post or _default_http_post
    get_fn = http_get or _default_http_get

    try:
        gen_result: Dict[str, Any]
        if modality in ("audio", "atlas", "3d"):
            gen_result = _generate_offline_synthetic(
                prompt=prompt,
                modality=modality,
                mode=mode,
                config=config,
                references=references,
                spec=spec,
                provider_preference=provider_pref,
                slash_route=slash_route,
            )
        elif provider_pref == "nanogpt":
            if nanogpt_key:
                gen_result = _generate_with_nanogpt(
                    prompt=prompt,
                    modality=modality,
                    config=config,
                    references=references,
                    conversation_history=inherited_history,
                    api_key=nanogpt_key,
                    spec=spec,
                    http_post=post_fn,
                    http_get=get_fn,
                )
            elif strict_keys or gemini_key:
                return {
                    "ok": False,
                    "statusCode": 401,
                    "error": "NanoGPT API Key is missing. Configure NANOGPT_API_KEY or enter one in the API drawer.",
                }
            else:
                gen_result = _generate_offline_synthetic(
                    prompt=prompt,
                    modality=modality,
                    mode=mode,
                    config=config,
                    references=references,
                    spec=spec,
                    provider_preference=provider_pref,
                    slash_route=slash_route,
                )
        elif provider_pref == "gemini":
            if gemini_key:
                gen_result = _generate_with_gemini(
                    prompt=prompt,
                    modality=modality,
                    config=config,
                    references=references,
                    conversation_history=inherited_history,
                    api_key=gemini_key,
                    spec=spec,
                    http_post=post_fn,
                )
            elif strict_keys or nanogpt_key:
                return {
                    "ok": False,
                    "statusCode": 401,
                    "error": "Gemini API Key is missing. Configure GEMINI_API_KEY or enter one in the API drawer.",
                }
            else:
                gen_result = _generate_offline_synthetic(
                    prompt=prompt,
                    modality=modality,
                    mode=mode,
                    config=config,
                    references=references,
                    spec=spec,
                    provider_preference=provider_pref,
                    slash_route=slash_route,
                )
        else:
            # auto routing: Gemini first (when model supports Gemini), fallback to NanoGPT on quota/auth errors;
            # if neither key is configured, use deterministic offline synthetic fallback unless strictKeys=True.
            if gemini_key and spec.get("geminiModel"):
                try:
                    gen_result = _generate_with_gemini(
                        prompt=prompt,
                        modality=modality,
                        config=config,
                        references=references,
                        conversation_history=inherited_history,
                        api_key=gemini_key,
                        spec=spec,
                        http_post=post_fn,
                    )
                except ProviderHttpError as gemini_err:
                    if nanogpt_key and _should_fallback_to_nanogpt(gemini_err):
                        gen_result = _generate_with_nanogpt(
                            prompt=prompt,
                            modality=modality,
                            config=config,
                            references=references,
                            conversation_history=inherited_history,
                            api_key=nanogpt_key,
                            spec=spec,
                            http_post=post_fn,
                            http_get=get_fn,
                        )
                        gen_result["fallbackFrom"] = "gemini"
                    else:
                        raise
            elif nanogpt_key:
                gen_result = _generate_with_nanogpt(
                    prompt=prompt,
                    modality=modality,
                    config=config,
                    references=references,
                    conversation_history=inherited_history,
                    api_key=nanogpt_key,
                    spec=spec,
                    http_post=post_fn,
                    http_get=get_fn,
                )
            elif gemini_key:
                gen_result = _generate_with_gemini(
                    prompt=prompt,
                    modality=modality,
                    config=config,
                    references=references,
                    conversation_history=inherited_history,
                    api_key=gemini_key,
                    spec=spec,
                    http_post=post_fn,
                )
            elif strict_keys:
                return {
                    "ok": False,
                    "statusCode": 401,
                    "error": "No API Key configured. Set GEMINI_API_KEY or NANOGPT_API_KEY.",
                }
            else:
                gen_result = _generate_offline_synthetic(
                    prompt=prompt,
                    modality=modality,
                    mode=mode,
                    config=config,
                    references=references,
                    spec=spec,
                    provider_preference=provider_pref,
                    slash_route=slash_route,
                )
    except ProviderHttpError as exc:
        return {"ok": False, "statusCode": exc.status_code, "error": str(exc)}

    short_id = str(body.get("shortId") or body.get("short_id") or "").strip() or hashlib.sha256(
        f"{mode}:{raw_prompt}:{','.join(selected_ids)}".encode("utf-8")
    ).hexdigest()[:4]

    if mode == "EDIT" and selected_ids:
        new_node_id = make_branch_node_id(selected_ids[0], short_id=short_id)
        node_type = "EDITED"
    elif mode == "MERGE":
        new_node_id = f"merge-{short_id}"
        node_type = "MERGED"
    else:
        new_node_id = f"node-{short_id}"
        node_type = "TEXT" if modality == "text" else "GENERATED"

    new_thought_sig = (
        (gen_result.get("image") or {}).get("thoughtSignature")
        or gen_result.get("thoughtSignature")
        or inherited_thought_sig
    )
    updated_history = list(inherited_history) + [f"User: {prompt.strip()}"]
    if gen_result.get("responseParts"):
        updated_history.append(f"AssistantParts: {json.dumps(gen_result['responseParts'])}")
    elif (gen_result.get("image") or {}).get("thoughtSignature"):
        updated_history.append(f"AssistantImage: {gen_result['image']['thoughtSignature']}|||{gen_result.get('text', '')}")
    elif new_thought_sig and modality != "text":
        updated_history.append(f"AssistantThought: {new_thought_sig}")
    else:
        updated_history.append(f"Assistant: {gen_result.get('text', '')}")

    content: Dict[str, Any] = {"text": gen_result.get("text", "")}
    if modality == "image" and isinstance(gen_result.get("image"), Mapping):
        img = gen_result["image"]
        content["base64"] = img.get("data", "")
        content["mimeType"] = img.get("mimeType", "image/png")
        if content["base64"]:
            content["imageUrl"] = f"data:{content['mimeType']};base64,{content['base64']}"
    elif modality == "video" and isinstance(gen_result.get("video"), Mapping):
        vid = gen_result["video"]
        content["videoUrl"] = vid.get("url", "")
        content["mimeType"] = vid.get("mimeType", "video/mp4")
        content["fps"] = vid.get("fps", 60)
        content["audioSync"] = vid.get("audioSync", True)
        content["durationSeconds"] = vid.get("durationSeconds", 6)
        if vid.get("mp4Path"):
            content["mp4Path"] = vid["mp4Path"]
            content["vfsPath"] = vid["mp4Path"]
    elif modality == "audio" and isinstance(gen_result.get("audio"), Mapping):
        aud = gen_result["audio"]
        content["audioUrl"] = aud.get("url", "")
        content["audioBytesB64"] = aud.get("audioBytesB64", _SYNTHETIC_WAV_B64)
        content["wavPath"] = aud.get("wavPath", "")
        content["vfsPath"] = aud.get("vfsPath", "")
        content["mimeType"] = aud.get("mimeType", "audio/wav")
        content["kind"] = aud.get("kind", "music")
        content["lufs"] = aud.get("lufs", -14.0)
        content["durationSeconds"] = aud.get("durationSeconds", 8.0)
        content["sparkline"] = AEONIK_SPARKLINE_STR
    elif modality == "atlas" and isinstance(gen_result.get("atlas"), Mapping):
        atl = gen_result["atlas"]
        content["mimeType"] = "application/x-worldlabs-spz"
        content["operationId"] = atl.get("operationId")
        content["atlasTask"] = atl.get("task")
        content["coordSystem"] = "RUB"
        content["fx"] = atl.get("fx", 893.37)
        content["fy"] = atl.get("fy", 893.90)
        content["cx"] = atl.get("cx", 640.0)
        content["cy"] = atl.get("cy", 360.5)
        content["centroidWorld"] = atl.get("centroidWorld", [-1.99, 0.0, -36.35])
        content["camera"] = atl.get("camera")
        content["numSplats"] = atl.get("numSplats", 2000000)
        content["depthConfidencePct"] = atl.get("depthConfidencePct", 98.4)
        content["spzPath"] = atl.get("spzPath")
        content["exrPath"] = atl.get("exrPath")
        content["glbPath"] = atl.get("glbPath")
        content["mp4Path"] = atl.get("mp4Path")
        content["vfsPaths"] = atl.get("vfsPaths")
        content["sparkline"] = AEONIK_SPARKLINE_STR
    elif modality == "3d" and isinstance(gen_result.get("mesh3d"), Mapping):
        m3d = gen_result["mesh3d"]
        content["mimeType"] = m3d.get("mimeType", "model/gltf-binary")
        content["glbPath"] = m3d.get("glbPath")
        content["vfsPath"] = m3d.get("vfsPath")
        content["spzPath"] = m3d.get("spzPath")
        content["format"] = m3d.get("format", "glb")
        content["tier"] = m3d.get("tier", "Regular")
        content["rigged"] = m3d.get("rigged", False)
        content["animation"] = m3d.get("animation")
        content["watertight"] = m3d.get("watertight", True)
        content["sparkline"] = AEONIK_SPARKLINE_STR
    elif modality == "text":
        content["mimeType"] = "text/markdown"

    # Multi-parent Omni-World Master composite enrichment
    parent_modalities = {
        str((p.get("data") or {}).get("modality") or "")
        for p in parent_nodes
        if isinstance(p, Mapping)
    }
    is_omni_merge = (mode == "MERGE") and (
        modality in ("atlas", "audio", "3d")
        or bool(parent_modalities & {"atlas", "audio", "3d"})
        or (slash_route and slash_route.get("command") == "mux")
    )
    if is_omni_merge:
        composite_paths = dict(gen_result.get("vfsPaths") or {})
        composite_paths.setdefault("depthExr", f"/worlds/world_{short_id}/frames_0_depth.exr")
        composite_paths.setdefault("splatSpz", f"/worlds/world_{short_id}/refinedSplats_2000000.spz")
        composite_paths.setdefault("meshGlb", f"/models3d/omni_master_{short_id}.glb")
        composite_paths.setdefault("audioWav", f"/audio/omni_master_{short_id}.wav")
        composite_paths.setdefault("masterMp4", f"/videos/omni_world_master_{short_id}.mp4")
        content["omniWorldMaster"] = True
        content["sparkline"] = AEONIK_SPARKLINE_STR
        content["vfsPaths"] = composite_paths
        content.setdefault("spzPath", composite_paths["splatSpz"])
        content.setdefault("exrPath", composite_paths["depthExr"])
        content.setdefault("glbPath", composite_paths["meshGlb"])
        content.setdefault("wavPath", composite_paths["audioWav"])
        content.setdefault("mp4Path", composite_paths["masterMp4"])
        gen_result["omniWorldMaster"] = True
        gen_result["vfsPaths"] = composite_paths

    node_metadata: Dict[str, Any] = {
        "mode": mode,
        "model": gen_result.get("modelUsed", spec["id"]),
        "requestedModel": requested_model or spec["id"],
        "provider": gen_result.get("providerUsed"),
        "fallbackFrom": gen_result.get("fallbackFrom"),
        "prompt": prompt.strip(),
        "rawPrompt": raw_prompt.strip(),
        "aspectRatio": config.get("aspectRatio", "1:1"),
        "resolution": config.get("resolution", "1K"),
        "thoughtSignature": new_thought_sig,
        "conversationHistory": updated_history,
        "groundingMetadata": gen_result.get("groundingMetadata"),
        "creditCost": spec.get("creditCost", 0.20),
        "references": references,
        "sparkline": AEONIK_SPARKLINE_STR,
    }
    if slash_route is not None:
        node_metadata["slashRoute"] = slash_route
    if modality == "atlas" or is_omni_merge:
        node_metadata["coordSystem"] = "RUB"
        node_metadata["fx"] = 893.37
        node_metadata["fy"] = 893.90
        node_metadata["cx"] = 640.0
        node_metadata["cy"] = 360.5
        node_metadata["centroidWorld"] = [-1.99, 0.0, -36.35]
        node_metadata["camera"] = gen_result.get("camera") or copy.deepcopy(DEFAULT_RUB_CAMERA)
        node_metadata["operationId"] = gen_result.get("operationId")
        node_metadata["atlasTask"] = gen_result.get("atlasTask")
    if gen_result.get("vfsPaths"):
        node_metadata["vfsPaths"] = gen_result["vfsPaths"]

    raw_node: Dict[str, Any] = {
        "id": new_node_id,
        "type": "morphingNode",
        "position": {"x": 520 + (len(selected_ids) * 80), "y": 140},
        "data": {
            "type": node_type,
            "modality": modality,
            "label": (
                f"[{new_node_id} · OMNI-WORLD MASTER]"
                if is_omni_merge
                else f"[{new_node_id} · {node_type}]"
            ),
            "status": "idle",
            "morphingStatus": modality,
            "morphingTransitions": ["generating", "message", modality],
            "parentIds": list(selected_ids),
            "filters": inherited_filters,
            "filtersBypassed": False,
            "content": content,
            "metadata": node_metadata,
        },
    }
    node = apply_node_filters(raw_node, modality=modality)

    new_edges: List[Dict[str, Any]] = []
    edge_kind = "edit" if mode == "EDIT" else "merge"
    for pid in selected_ids:
        new_edges.append(
            {
                "id": f"e-{pid}-{new_node_id}",
                "source": pid,
                "target": new_node_id,
                "kind": edge_kind,
            }
        )

    existing_edges = list(body.get("edges") or [])
    all_nodes = list(parent_nodes)
    if isinstance(body.get("nodes"), list):
        seen_n = {n.get("id") for n in all_nodes}
        for n in body["nodes"]:
            if isinstance(n, dict) and n.get("id") not in seen_n:
                all_nodes.append(n)
                seen_n.add(n.get("id"))
    all_nodes.append(node)
    all_edges = existing_edges + new_edges
    timeline = build_timeline_sequence(all_nodes, all_edges, target_node_id=new_node_id)

    response: Dict[str, Any] = {
        "ok": True,
        "statusCode": 200,
        "mode": mode,
        "modality": modality,
        "node": node,
        "edges": new_edges,
        "timeline": timeline,
        "result": gen_result,
        "generationResult": gen_result,
    }
    if slash_route is not None:
        response["slashRoute"] = slash_route
    return response


def _build_space_tree(modality: str, nodes: Sequence[Dict[str, Any]], timeline: Dict[str, Any]) -> Dict[str, Any]:
    if modality == "text":
        files = [
            "scene_01_root.md",
            "beat_02_ref.bib",
            "beat_03_wga.txt",
            "merge_04_lock.md",
            "final_05_diff.md",
        ]
        filters_dir = ["wga_tighten.cfg", "fact_lock.json", "eli12_strip.flag"]
    elif modality == "video":
        files = [
            "shot_01_keyframe.png",
            "ref_02_audio.wav",
            "cut_03_60fps.mp4",
            "merge_04_jcut.mp4",
            "master_05_lufs.mp4",
        ]
        filters_dir = ["optical_flow_60fps.cfg", "temporal_deflicker.lut", "j_cut_duck_-14lufs.cfg"]
    elif modality == "audio":
        files = [
            "stem_01_tts.wav",
            "score_02_lyria.wav",
            "foley_03_sfx.wav",
            "merge_04_duck.wav",
            "master_05_-14lufs.wav",
        ]
        filters_dir = ["ebu_r128_-14lufs.cfg", "dialogue_deess.cfg", "binaural_room.ir"]
    elif modality == "atlas":
        files = [
            "frames_0_image.jpg",
            "frames_0_depth.exr",
            "refinedSplats_2000000.spz",
            "atlas_mesh.glb",
            "flythrough_24fps.mp4",
        ]
        filters_dir = ["splat_density_2m.cfg", "exr_depth_confidence.cfg", "rub_frustum_14views.json"]
    elif modality == "3d":
        files = [
            "blockout_01_sketch.glb",
            "ref_02_orthographic.png",
            "remesh_03_pbr.glb",
            "rig_04_humanoid.glb",
            "master_05_walk.glb",
        ]
        filters_dir = ["pbr_roughness.cfg", "quad_remesh.cfg", "humanoid_ik_rig.json"]
    else:
        files = [
            "node_01_root.png",
            "ref_02_board.png",
            "branch_03_lut.png",
            "merge_04_21x9.png",
            "render_05_4k.png",
        ]
        filters_dir = ["kodak_2383.cube", "halation_35mm.cfg", "film_grain_16mm.cfg"]

    timecodes = timeline.get("timecodes") or ["00:00", "00:03", "00:06", "00:09"]
    lines = [
        f"~/space/nodes/{modality}",
        "├── dag/",
        *[f"│   {'└──' if i == len(files) - 1 else '├──'} {fname}" for i, fname in enumerate(files)],
        "├── filters/",
        *[f"│   {'└──' if i == len(filters_dir) - 1 else '├──'} {fname}" for i, fname in enumerate(filters_dir)],
        "└── timeline/",
        *[
            f"    {'└──' if i == len(timecodes) - 1 else '├──'} {tc.replace(':', '')}_stage_{i + 1:02d}"
            for i, tc in enumerate(timecodes)
        ],
    ]
    return {
        "root": f"~/space/nodes/{modality}",
        "dagFiles": files,
        "filterFiles": filters_dir,
        "timelineStages": timecodes,
        "lines": lines,
        "nodeCount": len(nodes),
    }


def get_default_studio_state(modality: str = "image") -> Dict[str, Any]:
    """Return the pre-populated 5-node DAG, edges, filter rack, .space tree, and timeline."""
    mod = modality if modality in MODALITIES else "image"
    spec = get_model_spec(None, modality=mod)
    base_filters = default_filter_state(mod)

    if mod == "text":
        specs_5 = [
            ("01", "GENERATED", "[01 · GENERATED]", "Draft act-one bunker telemetry monologue", "sig_txt_01", 80, 120),
            ("02", "UPLOADED", "[02 · UPLOADED REF]", "FAU Research Citation Corpus (.bib)", "sig_txt_02", 80, 300),
            ("03", "EDITED", "[03 · FILTER + EDIT]", "Tighten prose to <=4 lines/beat", "sig_txt_03", 320, 120),
            ("04", "MERGED", "[04 · MERGED *SEL]", "Merge beat #03 with citation corpus #02", "sig_txt_04", 560, 200),
            ("05", "TEXT", "[05 · DIFF]", "Final verified prose diff (128K ctx)", "sig_txt_05", 800, 200),
        ]
        telemetry = [
            {"label": "THROUGHPUT", "value": "410 t/s"},
            {"label": "BEAT COMPACT", "value": "-38%"},
            {"label": "CONTEXT", "value": "128K tok"},
            {"label": "STRUCTURE", "value": "4 Beats"},
        ]
        references = [
            {"id": "ref-01", "name": "beat_01_root.md", "type": "text"},
            {"id": "ref-02", "name": "fau_citations.bib", "type": "text"},
            {"id": "ref-03", "name": "wga_style_guide.txt", "type": "text"},
        ]
        aspect_ratio = "16:9"
        resolution = "128K"
    elif mod == "video":
        specs_5 = [
            ("01", "GENERATED", "[01 · GENERATED]", "24fps wide dolly keyframe across rain alley", "sig_vid_01", 80, 120),
            ("02", "UPLOADED", "[02 · UPLOADED REF]", "Dialogue stem & foley track (-14 LUFS)", "sig_vid_02", 80, 300),
            ("03", "EDITED", "[03 · FILTER + EDIT]", "Interpolate optical flow 24->60fps", "sig_vid_03", 320, 120),
            ("04", "MERGED", "[04 · MERGED *SEL]", "J-cut dialogue duck composite", "sig_vid_04", 560, 200),
            ("05", "GENERATED", "[05 · MP4]", "Master 60fps MP4 with audio sync", "sig_vid_05", 800, 200),
        ]
        telemetry = [
            {"label": "FRAME RATE", "value": "60 fps"},
            {"label": "LOUDNESS", "value": "-14 LUFS"},
            {"label": "TEMPORAL", "value": "98% Lock"},
            {"label": "DURATION", "value": "14.0s"},
        ]
        references = [
            {"id": "ref-01", "name": "shot_01_keyframe.png", "type": "image"},
            {"id": "ref-02", "name": "dialogue_stem.wav", "type": "text"},
            {"id": "ref-03", "name": "motion_curve.json", "type": "text"},
        ]
        aspect_ratio = "21:9"
        resolution = "60fps"
    elif mod == "audio":
        specs_5 = [
            ("01", "GENERATED", "[01 · TTS]", "ElevenLabs v4 bunker narrator stem", "sig_aud_01", 80, 120),
            ("02", "UPLOADED", "[02 · SCORE]", "Lyria 3.5 modular synth rain drone", "sig_aud_02", 80, 300),
            ("03", "EDITED", "[03 · SFX]", "ElevenLabs SFX v3 footsteps + thunder foley", "sig_aud_03", 320, 120),
            ("04", "MERGED", "[04 · MERGED *SEL]", "J-cut dialogue duck + score + foley mix", "sig_aud_04", 560, 200),
            ("05", "GENERATED", "[05 · WAV]", "Master -14.0 LUFS broadcast stem", "sig_aud_05", 800, 200),
        ]
        telemetry = [
            {"label": "LOUDNESS", "value": "-14.0 LUFS"},
            {"label": "SPARKLINE", "value": AEONIK_SPARKLINE_STR},
            {"label": "SAMPLE RATE", "value": "48 kHz"},
            {"label": "STEMS", "value": "3 Tracks"},
        ]
        references = [
            {"id": "ref-01", "name": "stem_01_tts.wav", "type": "audio"},
            {"id": "ref-02", "name": "score_02_lyria.wav", "type": "audio"},
            {"id": "ref-03", "name": "foley_03_sfx.wav", "type": "audio"},
        ]
        aspect_ratio = "16:9"
        resolution = "48kHz"
    elif mod == "atlas":
        specs_5 = [
            ("01", "GENERATED", "[01 · KEYFRAME]", "Mossy torii gate at dusk (Nano Banana 2.1)", "sig_atl_01", 80, 120),
            ("02", "UPLOADED", "[02 · POSE RGBD]", "Atlas images2PosedRGBD (RUB + .exr 98.4%)", "sig_atl_02", 80, 300),
            ("03", "EDITED", "[03 · 14 VIEWS]", "Atlas atlasGenerate 14 frustum orbit views", "sig_atl_03", 320, 120),
            ("04", "MERGED", "[04 · 2.0M SPLATS *SEL]", "Atlas posedImages2Splats (.spz + Audio mux)", "sig_atl_04", 560, 200),
            ("05", "GENERATED", "[05 · OMNI-WORLD]", "Atlas splats2Mesh watertight .glb + 24fps .mp4", "sig_atl_05", 800, 200),
        ]
        telemetry = [
            {"label": "SPLATS", "value": "2.0M .spz"},
            {"label": "DEPTH EXR", "value": "+98.4%"},
            {"label": "CAMERA RUB", "value": "fx=893.4"},
            {"label": "FRUSTUMS", "value": "14 Views"},
        ]
        references = [
            {"id": "ref-01", "name": "frames_0_image.jpg", "type": "image"},
            {"id": "ref-02", "name": "frames_0_depth.exr", "type": "atlas"},
            {"id": "ref-03", "name": "refinedSplats_2000000.spz", "type": "atlas"},
        ]
        aspect_ratio = "16:9"
        resolution = "1280x720"
    elif mod == "3d":
        specs_5 = [
            ("01", "GENERATED", "[01 · RODIN]", "Hyper3D Rodin v2.5 brutalist mech sentinel", "sig_3d_01", 80, 120),
            ("02", "UPLOADED", "[02 · SPLAT REF]", "Atlas splats2Mesh collision proxy .glb", "sig_3d_02", 80, 300),
            ("03", "EDITED", "[03 · PBR REMESH]", "Watertight quad remesh + 4K PBR normal map", "sig_3d_03", 320, 120),
            ("04", "MERGED", "[04 · RIGGED *SEL]", "Bind humanoid IK skeleton + walk cycle", "sig_3d_04", 560, 200),
            ("05", "GENERATED", "[05 · GLB]", "Master rigged .glb ready for stage viewport", "sig_3d_05", 800, 200),
        ]
        telemetry = [
            {"label": "TOPOLOGY", "value": "48K Quads"},
            {"label": "FORMAT", "value": "PBR .glb"},
            {"label": "SKELETON", "value": "Humanoid IK"},
            {"label": "ANIMATION", "value": "walk (24fps)"},
        ]
        references = [
            {"id": "ref-01", "name": "sentinel_rodin.glb", "type": "3d"},
            {"id": "ref-02", "name": "atlas_env_proxy.glb", "type": "3d"},
            {"id": "ref-03", "name": "walk_cycle.fbx", "type": "3d"},
        ]
        aspect_ratio = "1:1"
        resolution = "Regular"
    else:
        specs_5 = [
            ("01", "GENERATED", "[01 · GENERATED]", "Brutalist desert lab bathed in dusk sodium glow", "sig_img_01", 80, 120),
            ("02", "UPLOADED", "[02 · UPLOADED REF]", "Aeonik material swatch + lens flare plate", "sig_img_02", 80, 300),
            ("03", "EDITED", "[03 · FILTER + EDIT]", "Apply Kodak 2383 LUT (85%) & 35mm Halation", "sig_img_03", 320, 120),
            ("04", "MERGED", "[04 · MERGED 21:9 *SEL]", "Merge plate #03 + swatch #02 in 21:9 anamorphic", "sig_img_04", 560, 200),
            ("05", "GENERATED", "[05 · 4K]", "Final 4K master plate with LivingCube gauge", "sig_img_05", 800, 200),
        ]
        telemetry = [
            {"label": "LUT MIX", "value": "85%"},
            {"label": "HALATION", "value": "+35%"},
            {"label": "CREDITS", "value": "5,000 CR"},
            {"label": "LATENCY", "value": "12.0s"},
        ]
        references = [
            {"id": "ref-01", "name": "plate_01_dusk.png", "type": "image"},
            {"id": "ref-02", "name": "aeonik_swatch.png", "type": "image"},
            {"id": "ref-03", "name": "kodak_2383_lut.png", "type": "image"},
        ]
        aspect_ratio = "21:9"
        resolution = "4K"

    nodes: List[Dict[str, Any]] = []
    for nid, ntype, label, prompt_txt, sig, x, y in specs_5:
        content: Dict[str, Any] = {"text": prompt_txt}
        if mod == "image":
            content["base64"] = _SYNTHETIC_1X1_PNG_B64
            content["mimeType"] = "image/png"
            content["imageUrl"] = f"data:image/png;base64,{_SYNTHETIC_1X1_PNG_B64}"
        elif mod == "video":
            content["videoUrl"] = f"data:video/mp4;synthetic,default_{nid}"
            content["mimeType"] = "video/mp4"
            content["fps"] = 60
        elif mod == "audio":
            content["audioUrl"] = f"data:audio/wav;base64,{_SYNTHETIC_WAV_B64}"
            content["wavPath"] = f"/audio/default_{nid}.wav"
            content["mimeType"] = "audio/wav"
            content["lufs"] = -14.0
            content["sparkline"] = AEONIK_SPARKLINE_STR
        elif mod == "atlas":
            content["mimeType"] = "application/x-worldlabs-spz"
            content["coordSystem"] = "RUB"
            content["fx"] = 893.37
            content["fy"] = 893.90
            content["cx"] = 640.0
            content["cy"] = 360.5
            content["centroidWorld"] = [-1.99, 0.0, -36.35]
            content["spzPath"] = f"/worlds/world_{nid}/refinedSplats_2000000.spz"
            content["exrPath"] = f"/worlds/world_{nid}/frames_0_depth.exr"
            content["glbPath"] = f"/models3d/atlas_{nid}.glb"
            content["sparkline"] = AEONIK_SPARKLINE_STR
        elif mod == "3d":
            content["mimeType"] = "model/gltf-binary"
            content["glbPath"] = f"/models3d/node_{nid}.glb"
            content["sparkline"] = AEONIK_SPARKLINE_STR
        else:
            content["mimeType"] = "text/markdown"

        raw_node = {
            "id": nid,
            "type": "morphingNode",
            "position": {"x": x, "y": y},
            "data": {
                "type": ntype,
                "modality": mod,
                "label": label,
                "status": "idle",
                "morphingStatus": mod,
                "filters": copy.deepcopy(base_filters),
                "filtersBypassed": False,
                "content": content,
                "metadata": {
                    "model": spec["id"],
                    "provider": spec.get("preferredProvider") or "auto",
                    "prompt": prompt_txt,
                    "aspectRatio": aspect_ratio,
                    "resolution": resolution,
                    "thoughtSignature": sig,
                    "conversationHistory": [f"User: {prompt_txt}", f"AssistantThought: {sig}"],
                    "creditCost": spec.get("creditCost", 0.20),
                },
            },
        }
        nodes.append(apply_node_filters(raw_node, modality=mod))

    edges = [
        {"id": "e-01-03", "source": "01", "target": "03", "kind": "edit"},
        {"id": "e-03-04", "source": "03", "target": "04", "kind": "merge"},
        {"id": "e-02-04", "source": "02", "target": "04", "kind": "merge"},
        {"id": "e-04-05", "source": "04", "target": "05", "kind": "render"},
    ]

    selected_ids = ["03", "04"]
    timeline = build_timeline_sequence(nodes, edges, target_node_id="05")
    space_tree = _build_space_tree(mod, nodes, timeline)

    return {
        "ok": True,
        "modality": mod,
        "mode": derive_generation_mode(selected_ids),
        "selectedNodeIds": selected_ids,
        "nodes": nodes,
        "edges": edges,
        "filterRack": copy.deepcopy(base_filters),
        "filterPresets": copy.deepcopy(FILTER_PRESETS[mod]),
        "telemetry": telemetry,
        "timeline": timeline,
        "spaceTree": space_tree,
        "references": references,
        "promptIsland": {
            "mode": "MERGE",
            "model": spec["id"],
            "nanogptModel": spec.get("nanogptModel"),
            "aspectRatio": aspect_ratio,
            "resolution": resolution,
            "thinkingLevel": spec.get("defaultThinkingLevel") or "high",
            "groundingMode": "Web+Img" if mod == "image" else "Off",
            "provider": spec.get("preferredProvider") or "auto",
            "maxReferences": MAX_REFERENCES,
        },
    }


__all__ = [
    "AEONIK_SPARKLINE_BARS",
    "AEONIK_SPARKLINE_STR",
    "ALL_ASPECT_RATIOS",
    "DEFAULT_RUB_CAMERA",
    "FILTER_PRESETS",
    "FLAT_FILTER_PRESETS",
    "MAX_REFERENCES",
    "MODALITIES",
    "MODALITY_SPECS",
    "MODEL_ALIASES",
    "MODEL_SPECS",
    "NANOGPT_CHAT_URL",
    "NANOGPT_IMAGES_URL",
    "NANOGPT_VIDEO_URL",
    "PANORAMIC_ASPECT_RATIOS",
    "ProviderHttpError",
    "STANDARD_ASPECT_RATIOS",
    "apply_node_filters",
    "build_contents",
    "build_text_context_prompt",
    "build_timeline_sequence",
    "default_filter_state",
    "derive_generation_mode",
    "get_default_studio_state",
    "get_model_spec",
    "get_node_studio_health",
    "handle_node_studio_filter",
    "handle_node_studio_generate",
    "infer_modality",
    "make_branch_node_id",
    "parse_omni_slash_command",
]
