"""TinCan 2.2 · Aeonik Celadon & Ink 4-Quadrant Industrial Terminal Node Studio UI.

Implements the multimodal Node Studio (Image, Text, Video) matching the Aeonik
Celadon & Ink design system (``#ecf1e6``, ``#f4f8f0``, ``#ffffff``, ``#111111``,
``#4a4a4a``, ``#5c5c5c``, ``#107a47``, ``#8a1c1c``) and FigCraft artboards 01-06.

Exports:
* ``AEONIK_PALETTE``: strict Celadon & Ink color token dictionary.
* ``MODALITY_SPECS``: preset 4-quadrant state for ``image``, ``text``, and ``video``.
* ``MODEL_OPTIONS``: NanoGPT + Gemini model selector registry.
* ``FILTER_RACK_SPECS``: non-destructive filter rack definitions across modalities.
* ``render_node_studio_html(active_modality="image", active_view="editor") -> str``:
  standalone full-page Aeonik 4-Quadrant Industrial Terminal HTML5 document.
* ``render_node_studio_window_html() -> str``:
  embeddable ``#win-nodes`` Mesh OS window with ``<!--TC_TITLEBAR ...-->``.
"""

from __future__ import annotations

import html as _html
import json
from typing import Any, Dict, List, Tuple

AEONIK_PALETTE: Dict[str, str] = {
    "bg": "#ecf1e6",
    "card": "#f4f8f0",
    "paper": "#ffffff",
    "ink": "#111111",
    "muted": "#4a4a4a",
    "faint": "#5c5c5c",
    "green": "#107a47",
    "danger": "#8a1c1c",
}

VALID_MODALITIES: Tuple[str, ...] = ("image", "text", "video")
VALID_VIEWS: Tuple[str, ...] = ("editor", "timeline", "library")

MODEL_OPTIONS: Tuple[Dict[str, str], ...] = (
    {
        "id": "nano-banana-2.1",
        "label": "nano-banana-2.1 (gemini-nano-banana-2.1 · 0.2 CR)",
        "alias": "gemini-nano-banana-2.1",
        "modality": "image",
        "tier": "DEFAULT · 1K-4K · 14 REFS",
        "cost": "0.20 CR",
    },
    {
        "id": "nano-banana-pro",
        "label": "nano-banana-pro (gemini-3-pro-image · 0.5 CR)",
        "alias": "gemini-3-pro-image",
        "modality": "image",
        "tier": "PRO · 4K STUDIO · 14 REFS",
        "cost": "0.50 CR",
    },
    {
        "id": "nano-banana-2",
        "label": "nano-banana-2 (gemini-3.1-flash-image · 0.15 CR)",
        "alias": "gemini-3.1-flash-image",
        "modality": "image",
        "tier": "FLASH · 512-4K · 14 REFS",
        "cost": "0.15 CR",
    },
    {
        "id": "nano-banana-2-lite",
        "label": "nano-banana-2-lite (gemini-3.1-flash-lite-image · 0.08 CR)",
        "alias": "gemini-3.1-flash-lite-image",
        "modality": "image",
        "tier": "LITE · 1K FAST · 14 REFS",
        "cost": "0.08 CR",
    },
    {
        "id": "deepseek-v4.1-tee",
        "label": "deepseek-v4.1-tee (nanogpt/TEE/deepseek-v4.1-flash · 0.08 CR)",
        "alias": "nanogpt/TEE/deepseek-v4.1-flash",
        "modality": "text",
        "tier": "TEE ENCLAVE · 128K CTX",
        "cost": "0.08 CR",
    },
    {
        "id": "gemini-3.1-pro",
        "label": "gemini-3.1-pro (reasoning + citation lock · 0.15 CR)",
        "alias": "gemini-3.1-pro",
        "modality": "text",
        "tier": "PRO TEXT · 2M CTX",
        "cost": "0.15 CR",
    },
    {
        "id": "ltx-video",
        "label": "ltx-video (24/60fps keyframe + audio · 0.40 CR)",
        "alias": "ltx-video",
        "modality": "video",
        "tier": "24/60FPS + AUDIO SYNC",
        "cost": "0.40 CR",
    },
    {
        "id": "kling-1.6",
        "label": "kling-1.6 (cinematic motion · 0.60 CR)",
        "alias": "kling-1.6",
        "modality": "video",
        "tier": "CINEMATIC MOTION",
        "cost": "0.60 CR",
    },
)

FILTER_RACK_SPECS: Tuple[Dict[str, Any], ...] = (
    {
        "id": "kodak_2383",
        "modality": "image",
        "label": "kodak_2383",
        "title": "Kodak 2383 Print LUT",
        "value": "85%",
        "file": "kodak_2383.cube",
        "desc": "Non-destructive 3D print curve LUT with warm shadow roll-off.",
        "enabled": True,
    },
    {
        "id": "halation",
        "modality": "image",
        "label": "halation",
        "title": "Film Halation & Bloom",
        "value": "+35%",
        "file": "halation_16mm.fx",
        "desc": "Specular edge scatter keyed to high-luminance highlights.",
        "enabled": True,
    },
    {
        "id": "film_grain_16mm",
        "modality": "image",
        "label": "film_grain_16mm",
        "title": "16mm Film Grain",
        "value": "20% ISO",
        "file": "film_grain_16mm.fx",
        "desc": "Temporal-locked silver halide grain and optional SOOP ink contours.",
        "enabled": True,
    },
    {
        "id": "wga_tighten",
        "modality": "text",
        "label": "wga_tighten",
        "title": "WGA Courier Tighten",
        "value": "<=4 ln/beat",
        "file": "wga_courier_tighten.rule",
        "desc": "Compresses dialogue and scene beats to <=4 lines per beat.",
        "enabled": True,
    },
    {
        "id": "fact_lock",
        "modality": "text",
        "label": "fact_lock",
        "title": "Fact-Lock Citations",
        "value": "Strict",
        "file": "fact_lock_citations.fx",
        "desc": "Enforces Context Capsule citation grounding across merged drafts.",
        "enabled": True,
    },
    {
        "id": "optical_flow_60fps",
        "modality": "video",
        "label": "optical_flow_60fps",
        "title": "Optical Flow 60fps",
        "value": "24->60fps",
        "file": "optical_flow_60fps.fx",
        "desc": "180-degree shutter motion interpolation from 24fps to 60fps.",
        "enabled": True,
    },
    {
        "id": "temporal_deflicker",
        "modality": "video",
        "label": "temporal_deflicker",
        "title": "Temporal Deflicker",
        "value": "98% Lock",
        "file": "temporal_deflicker.fx",
        "desc": "Cross-frame luminance stabilization across multi-shot clips.",
        "enabled": True,
    },
    {
        "id": "j_cut_dialogue_duck",
        "modality": "video",
        "label": "j_cut_dialogue_duck",
        "title": "J-Cut Dialogue Duck",
        "value": "-14.0 LUFS",
        "file": "j_cut_dialogue_duck.fx",
        "desc": "12-frame J-cut audio pre-lap ducked under Kokoro narration.",
        "enabled": True,
    },
)

SPARKLINE_BARS: Dict[str, Tuple[int, ...]] = {
    "image": (10, 14, 18, 12, 22, 16, 26, 20, 14, 28, 19, 15, 30, 24, 17, 32, 22, 16, 27, 21, 15, 29, 25, 18),
    "text": (16, 24, 20, 28, 18, 30, 22, 26, 15, 32, 24, 19, 27, 21, 29, 23, 17, 25, 31, 22, 18, 26, 20, 24),
    "video": (14, 18, 26, 22, 30, 28, 19, 24, 32, 27, 21, 29, 25, 31, 20, 26, 28, 23, 30, 24, 19, 27, 29, 26),
}

MODALITY_SPECS: Dict[str, Dict[str, Any]] = {
    "image": {
        "key": "image",
        "hero_title": "Node Studio · Image",
        "path": "~/space/nodes",
        "tree_header": "TREE ~/space/nodes/timeline",
        "q1_title": "NODE GRAPH · DAG & SERIAL FILTER CHAIN",
        "q1_shortcuts": ("[A] Auto-Layout", "[F] Fit View", "[Cmd+D] Bypass Filter"),
        "q2_title": "NANOGPT & FILTER RACK",
        "q2_endpoint": "POST /api/v1/images",
        "default_model": "nano-banana-2.1",
        "status_model": "nanogpt-2.1",
        "api_label": "API: NanoGPT + Gemini Ready",
        "cta_label": "▶ Generate [Enter] →",
        "aspect": "21:9",
        "resolution": "4K",
        "thinking": "high",
        "search": "web+img",
        "via": "auto",
        "metrics": [
            {"label": "LUT MIX", "value": "85%"},
            {"label": "HALATION", "value": "+35%"},
            {"label": "NANOGPT POOL", "value": "5,000 CR"},
            {"label": "TIMELINE", "value": "12.0s"},
        ],
        "nodes": [
            {
                "id": "01",
                "tag": "[01 · GENERATED]",
                "badge": "1K",
                "box": "Corridor 35mm · 1024px",
                "file": "kf01_alley_base.png",
                "meta": "nano-banana-2.1 · Sig ✓",
                "col": "1",
                "row": "1",
                "selected": False,
                "mode": "GENERATE",
                "filter_model": "nano-banana-2.1 (1K)",
                "cost": "0.2 CR",
                "state": "DONE",
            },
            {
                "id": "02",
                "tag": "[02 · UPLOADED REF]",
                "badge": "REF",
                "box": "Char Rig Sheet · Ref #02",
                "file": "char_rig_sheet.png",
                "meta": "Slot #02 · 1536×1024",
                "col": "1",
                "row": "2",
                "selected": False,
                "mode": "UPLOADED",
                "filter_model": "char_rig_sheet.png",
                "cost": "0.0 CR",
                "state": "REF #2",
            },
            {
                "id": "03",
                "tag": "[03 · FILTER + EDIT]",
                "badge": "LUT",
                "box": "LUT: Kodak 2383 [85%]\nHalation: Warm [+35%]\nGrain: 16mm ISO [20%]",
                "file": "kf02_kodak2383.png",
                "meta": "Branch #01.a4 · ON ●",
                "col": "2",
                "row": "1",
                "selected": True,
                "mode": "EDIT+LUT",
                "filter_model": "kodak_2383 + halation",
                "cost": "0.0 CR",
                "state": "ON ●",
            },
            {
                "id": "04",
                "tag": "[04 · MERGED 21:9 *SEL]",
                "badge": "21:9",
                "box": "21:9 Anamorphic Composite",
                "file": "kf03_composite_21x9.png",
                "meta": "Parents: [#03 + #02] · Via: NanoGPT 2.1 (0.2 CR)",
                "col": "3",
                "row": "1",
                "selected": True,
                "mode": "MERGE 21:9",
                "filter_model": "nano-banana-2.1 (2K)",
                "cost": "0.2 CR",
                "state": "SELECTED",
            },
            {
                "id": "05",
                "tag": "[05 · 4K]",
                "badge": "68%",
                "box": "LivingCube",
                "file": "kf04_4k_ltx.mp4",
                "meta": "LivingCube → LTX 3.5s",
                "col": "4",
                "row": "1",
                "selected": False,
                "pct": 68,
                "mode": "4K MASTER",
                "filter_model": "nano-banana-pro + LTX",
                "cost": "0.5 CR",
                "state": "68% ●",
            },
        ],
        "timeline": [
            {"time": "00:00", "node": "#01", "label": "00:00 [#01]"},
            {"time": "00:03", "node": "#03", "label": "00:03 [#03 LUT]"},
            {"time": "00:06", "node": "#04", "label": "00:06 [#04 21:9]"},
            {"time": "00:09", "node": "#05", "label": "00:09 [#05 4K]"},
        ],
        "timeline_prefix": "TIMELINE:",
        "tree": [
            ("nodes/", "dir", 0, ""),
            ("main.dag", "file", 1, "DAG root graph"),
            ("timeline_seq01/", "dir", 1, ""),
            ("00_00_kf01_base.png", "file", 2, "00:00 · 1K Root"),
            ("00_03_kf02_kodak2383.png", "file", 2, "00:03 · LUT 85%"),
            ("00_06_kf03_merge_21x9.png", "file", 2, "00:06 · 21:9 Merge"),
            ("00_09_kf04_4k_ltx.mp4", "file", 2, "00:09 · 4K + LTX"),
            ("filters/", "dir", 1, ""),
            ("kodak_2383.cube", "file", 2, "(ON · 85%)"),
            ("halation_16mm.fx", "file", 2, "(ON · +35%)"),
            ("soop_dirty_ink.fx", "file", 2, "(OFF)"),
            ("refs/", "dir", 1, ""),
            ("char_rig_sheet.png", "file", 2, "[Ref #02]"),
            ("walk_cycle.mp4", "file", 2, "[Ref #03]"),
        ],
        "tree_footer": "4 directories, 10 files · merkle 7a4c9f",
        "refs": [
            {"slot": "REF #01 · IMAGE", "name": "kf02_kodak2383.png (1K)"},
            {"slot": "REF #02 · IMAGE", "name": "char_rig_sheet.png"},
            {"slot": "REF #03 · VIDEO", "name": "walk_cycle.mp4 (3.5s)"},
        ],
        "prompt": (
            "Composite rigged protagonist [02] into graded corridor [01], "
            "apply Kodak 2383 LUT + 21:9 anamorphic streak filter, render 4K keyframe to .space/nodes/kf04.png"
        ),
        "status_mode": "MERGE",
    },
    "text": {
        "key": "text",
        "hero_title": "Node Studio · Text",
        "path": "~/space/notes",
        "tree_header": "TREE ~/space/notes/text-nodes",
        "q1_title": "TEXT NODE GRAPH · BRANCHING DRAFTS & PROSE FILTER CHAIN",
        "q1_shortcuts": ("[A] Auto-Layout", "[F] Fit View", "[Cmd+D] Bypass Filter"),
        "q2_title": "NANOGPT TEE & TEXT FILTER RACK",
        "q2_endpoint": "/api/v1/chat",
        "default_model": "deepseek-v4.1-tee",
        "status_model": "deepseek-v4.1-tee",
        "api_label": "API: NanoGPT TEE + Gemini Ready",
        "cta_label": "▶ Synthesize [Enter] →",
        "aspect": "FOUNTAIN/MD",
        "resolution": "2K TOK",
        "thinking": "high",
        "search": "web",
        "via": "nanogpt-tee",
        "metrics": [
            {"label": "THROUGHPUT", "value": "410 t/s"},
            {"label": "COMPRESSION", "value": "-38%"},
            {"label": "CONTEXT LAKE", "value": "128K tok"},
            {"label": "BEAT COUNT", "value": "4 Beats"},
        ],
        "nodes": [
            {
                "id": "01",
                "tag": "[01 · GENERATED]",
                "badge": "1.4Kt",
                "box": '"Scene 01: Outage Hook"',
                "file": "act1_draft_v1.md",
                "meta": "deepseek-v4.1 · Sig ✓",
                "col": "1",
                "row": "1",
                "selected": False,
                "mode": "GENERATE",
                "filter_model": "nanogpt/TEE/deepseek-v4",
                "cost": "1,420t",
                "state": "DONE",
            },
            {
                "id": "02",
                "tag": "[02 · UPLOADED DOC]",
                "badge": "PDF",
                "box": "PDF + Context Capsule 21",
                "file": "FAILOVER.pdf (Postmortem)",
                "meta": "Slot #02 · 4,810 tokens",
                "col": "1",
                "row": "2",
                "selected": False,
                "mode": "UPLOADED",
                "filter_model": "FAILOVER.pdf (grounding)",
                "cost": "4,810t",
                "state": "REF #2",
            },
            {
                "id": "03",
                "tag": "[03 · PROSE FILTER]",
                "badge": "WGA",
                "box": "Tone: WGA Noir [90%]\nTrim: <=4 ln/beat [ON]\nFact-Lock: Strict [ON]",
                "file": "act1_tightened_v2.md",
                "meta": "Branch #01.b2 · ON ●",
                "col": "2",
                "row": "1",
                "selected": True,
                "mode": "EDIT+FILTER",
                "filter_model": "wga_noir + tighten_4ln",
                "cost": "1,150t",
                "state": "ON ●",
            },
            {
                "id": "04",
                "tag": "[04 · MERGED SCRIPT *SEL]",
                "badge": "VO",
                "box": "Dialogue + Outage VO Narration",
                "file": "act1_master_vo.fountain",
                "meta": "Parents: [#03 + #02] · Via: NanoGPT TEE (0.08 CR)",
                "col": "3",
                "row": "1",
                "selected": True,
                "mode": "MERGE DOCS",
                "filter_model": "gemini-3.1-pro + heretic",
                "cost": "2,180t",
                "state": "SELECTED",
            },
            {
                "id": "05",
                "tag": "[05 · DIFF]",
                "badge": "84%",
                "box": "LivingCube",
                "file": "capsule_21_diff.patch",
                "meta": "LivingStream → .space/md",
                "col": "4",
                "row": "1",
                "selected": False,
                "pct": 84,
                "mode": "DIFF PATCH",
                "filter_model": "context_palace_capsule",
                "cost": "1,940t",
                "state": "84% ●",
            },
        ],
        "timeline": [
            {"time": "00:00", "node": "#01", "label": "Beat 01 [#01 Hook]"},
            {"time": "00:03", "node": "#03", "label": "Beat 02 [#03 WGA Filter]"},
            {"time": "00:06", "node": "#04", "label": "Beat 03 [#04 VO Merge]"},
            {"time": "00:09", "node": "#05", "label": "[#05]"},
        ],
        "timeline_prefix": "BEAT TIMELINE:",
        "tree": [
            ("text-nodes/", "dir", 0, ""),
            ("script_graph.dag", "file", 1, "Branching drafts"),
            ("beat_timeline/", "dir", 1, ""),
            ("01_opening_hook.md", "file", 2, "Beat 01"),
            ("02_filtered_dialogue.md", "file", 2, "Beat 02"),
            ("03_merged_narration.fountain", "file", 2, "Beat 03"),
            ("04_final_locked_spec.md", "file", 2, "Locked spec"),
            ("prose-filters/", "dir", 1, ""),
            ("wga_courier_tighten.rule", "file", 2, "(ON · 90%)"),
            ("fact_lock_citations.fx", "file", 2, "(ON · Strict)"),
            ("eli12_jargon_strip.fx", "file", 2, "(OFF)"),
            ("refs/", "dir", 1, ""),
            ("FAILOVER.pdf", "file", 2, "[Ref #02]"),
            ("palace_capsule_21.json", "file", 2, "[Ref #03]"),
        ],
        "tree_footer": "4 directories, 10 files · merkle 9b2e4c",
        "refs": [
            {"slot": "REF #01 · MARKDOWN", "name": "02_filtered_dialogue.md"},
            {"slot": "REF #02 · PDF DOC", "name": "FAILOVER.pdf (4,810t)"},
            {"slot": "REF #03 · PALACE", "name": "capsule_21_facts.json"},
        ],
        "prompt": (
            "Weave the Microsoft cloud outage root-cause from FAILOVER.pdf [02] directly into the "
            "tightened dialogue in [01] as an ominous voiceover narration, <=4 lines per beat..."
        ),
        "status_mode": "TEXT MERGE",
    },
    "video": {
        "key": "video",
        "hero_title": "Node Studio · Video",
        "path": "~/space/video",
        "tree_header": "TREE ~/space/video/timeline-cuts",
        "q1_title": "VIDEO NODE GRAPH · MULTI-SHOT & TEMPORAL CHAIN",
        "q1_shortcuts": ("[A] Auto-Layout", "[F] Fit View", "[Cmd+D] Bypass Filter"),
        "q2_title": "NANOGPT VIDEO & TEMPORAL RACK",
        "q2_endpoint": "LTX + KLING + VEO",
        "default_model": "ltx-video",
        "status_model": "ltx-video + nanogpt",
        "api_label": "API: NanoGPT + LTX Ready",
        "cta_label": "▶ Render Cut [Enter] →",
        "aspect": "21:9",
        "resolution": "1080P 60FPS",
        "thinking": "high",
        "search": "web+img",
        "via": "nanogpt+ltx",
        "metrics": [
            {"label": "FRAME RATE", "value": "60 fps"},
            {"label": "AUDIO LOUDNESS", "value": "-14 LUFS"},
            {"label": "DEFLICKER", "value": "98% Lock"},
            {"label": "TOTAL CUT", "value": "14.0s"},
        ],
        "nodes": [
            {
                "id": "01",
                "tag": "[01 · GENERATED]",
                "badge": "3.5s",
                "box": "▶ Clip 01: Server Dolly",
                "file": "shot01_dolly_raw.mp4",
                "meta": "ltx-video · 1080p 24fps",
                "col": "1",
                "row": "1",
                "selected": False,
                "mode": "GENERATE",
                "filter_model": "ltx-video / kling-1.6",
                "cost": "03.5s",
                "state": "DONE",
            },
            {
                "id": "02",
                "tag": "[02 · UPLOADED A/V]",
                "badge": "WAV",
                "box": "♫ VO + Camera Ref MP4",
                "file": "vo_kokoro_narration.wav",
                "meta": "Slot #02 · -14.0 LUFS",
                "col": "1",
                "row": "2",
                "selected": False,
                "mode": "UPLOADED",
                "filter_model": "vo_kokoro_narration.wav",
                "cost": "03.5s",
                "state": "REF #2",
            },
            {
                "id": "03",
                "tag": "[03 · TEMPORAL FX]",
                "badge": "60P",
                "box": "OptFlow: 24→60fps [ON]\nDeflicker: Lock [98%]\nShutter: 180° Blur [ON]",
                "file": "shot01_smooth_60p.mp4",
                "meta": "Branch #01.v2 · ON ●",
                "col": "2",
                "row": "1",
                "selected": True,
                "mode": "TEMPORAL FX",
                "filter_model": "opt_flow_60p + deflicker",
                "cost": "03.5s",
                "state": "ON ●",
            },
            {
                "id": "04",
                "tag": "[04 · MERGED A/V CUT *SEL]",
                "badge": "J-CUT",
                "box": "21:9 Cut + 12f J-Cut Audio",
                "file": "seq01_av_master_cut.mp4",
                "meta": "Parents: [#03 + #02] · Via: NanoGPT Vid + LTX",
                "col": "3",
                "row": "1",
                "selected": True,
                "mode": "MERGE A/V",
                "filter_model": "j_cut_12f + kodak_2383",
                "cost": "07.0s",
                "state": "SELECTED",
            },
            {
                "id": "05",
                "tag": "[05 · MP4]",
                "badge": "92%",
                "box": "LivingCube",
                "file": "watchparty_master.mp4",
                "meta": "Encoding 60p → WatchParty",
                "col": "4",
                "row": "1",
                "selected": False,
                "pct": 92,
                "mode": "BOUNCE MP4",
                "filter_model": "watchparty_s3_playlist",
                "cost": "14.0s",
                "state": "92% ●",
            },
        ],
        "timeline": [
            {"time": "00:00", "node": "#01", "label": "00:00 [#01 3.5s]"},
            {"time": "00:03.5", "node": "#03", "label": "00:03.5 [#03 60p]"},
            {"time": "00:07", "node": "#04", "label": "00:07 [#04 J-Cut]"},
            {"time": "00:14", "node": "#05", "label": "00:14 [#05]"},
        ],
        "timeline_prefix": "CUT TIMELINE:",
        "tree": [
            ("video-nodes/", "dir", 0, ""),
            ("sequence_01.dag", "file", 1, "Multi-shot DAG"),
            ("cuts_timeline/", "dir", 1, ""),
            ("00_00_shot01_dolly.mp4", "file", 2, "00:00 · 3.5s"),
            ("00_03_shot01_deflicker.mp4", "file", 2, "00:03.5 · 60p"),
            ("00_07_shot02_av_merged.mp4", "file", 2, "00:07 · J-Cut"),
            ("00_14_watchparty_master.mp4", "file", 2, "00:14 · Master"),
            ("temporal-filters/", "dir", 1, ""),
            ("optical_flow_60fps.fx", "file", 2, "(ON · 180° Shutter)"),
            ("temporal_deflicker.fx", "file", 2, "(ON · 98% Lock)"),
            ("j_cut_dialogue_duck.fx", "file", 2, "(ON · -14.0 LUFS)"),
            ("refs/", "dir", 1, ""),
            ("vo_kokoro_narration.wav", "file", 2, "[Ref #02]"),
            ("camera_track_blockout.mp4", "file", 2, "[Ref #03]"),
        ],
        "tree_footer": "4 directories, 10 files · merkle 4d8a1e",
        "refs": [
            {"slot": "REF #01 · VIDEO", "name": "shot01_smooth_60p.mp4"},
            {"slot": "REF #02 · AUDIO", "name": "vo_kokoro_3.5s.wav"},
            {"slot": "REF #03 · KEYFRAME", "name": "kf03_composite_21x9.png"},
        ],
        "prompt": (
            "Extend stabilized corridor dolly [01] into a 4-second tracking shot, lip-sync and duck "
            "ambient rain under Kokoro voiceover [02] with a 12-frame J-cut, push MP4 to WatchParty..."
        ),
        "status_mode": "VIDEO MERGE",
    },
}


def _safe_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=True).replace("</", "<\\/")


def _normalize_modality(modality: str | None) -> str:
    m = (modality or "image").strip().lower()
    return m if m in VALID_MODALITIES else "image"


def _normalize_view(view: str | None) -> str:
    v = (view or "editor").strip().lower()
    if v == "gateway":
        return "library"
    return v if v in VALID_VIEWS else "editor"


def _derive_mode_label(selected_count: int) -> Tuple[str, str]:
    if selected_count <= 0:
        return "GENERATE MODE", "MODE: GENERATE (0 SELECTED)"
    if selected_count == 1:
        return "EDIT + FILTER MODE", "MODE: EDIT + FILTER (1 SELECTED)"
    return "MERGE MODE", f"MODE: MERGE ({selected_count} SELECTED)"


def _render_sparkline_svg(modality: str) -> str:
    bars = SPARKLINE_BARS.get(modality, SPARKLINE_BARS["image"])
    rects: List[str] = []
    for idx, h in enumerate(bars):
        x = idx * 14 + 2
        y = 36 - h
        rects.append(
            f'<rect x="{x}" y="{y}" width="2" height="{h}" rx="1" fill="#111111" '
            f'opacity="{"0.92" if idx % 3 == 0 else "0.62"}"/>'
        )
    w = len(bars) * 14 + 4
    return (
        f'<svg class="ns-sparkline" viewBox="0 0 {w} 36" preserveAspectRatio="none" '
        'role="img" aria-label="Node Studio filter and throughput sparkline">'
        + "".join(rects)
        + "</svg>"
    )


def _render_dag_nodes_html(spec: Dict[str, Any]) -> str:
    cards: List[str] = []
    for node in spec["nodes"]:
        nid = _html.escape(node["id"], quote=True)
        selected = bool(node.get("selected"))
        sel_cls = " is-selected" if selected else ""
        pressed = "true" if selected else "false"
        col = _html.escape(node["col"], quote=True)
        row = _html.escape(node["row"], quote=True)

        if nid == "05":
            pct = int(node.get("pct", 68))
            circ = 125.66
            offset = round(circ * (1.0 - pct / 100.0), 2)
            body_html = (
                '<div class="ns-gauge-wrap">'
                '<svg class="ns-gauge-svg" viewBox="0 0 52 52" aria-hidden="true">'
                '<circle cx="26" cy="26" r="20" fill="none" stroke="rgba(17,17,17,0.18)" stroke-width="3"/>'
                f'<circle id="nsLivingGaugeArc" cx="26" cy="26" r="20" fill="none" stroke="#111111" '
                f'stroke-width="3" stroke-dasharray="{circ}" stroke-dashoffset="{offset}" '
                'transform="rotate(-90 26 26)"/>'
                "</svg>"
                f'<span id="nsLivingGaugePct" class="ns-gauge-pct">{pct}%</span>'
                "</div>"
                f'<div class="ns-node-file">{_html.escape(node["box"])}</div>'
                f'<div class="ns-node-meta">{_html.escape(node["meta"])}</div>'
            )
        else:
            box_lines = "<br>".join(_html.escape(line) for line in node["box"].split("\n"))
            body_html = (
                f'<div class="ns-node-preview">{box_lines}</div>'
                f'<div class="ns-node-file">{_html.escape(node["file"])}</div>'
                f'<div class="ns-node-meta">{_html.escape(node["meta"])}</div>'
            )

        quick_bar = (
            '<div class="ns-node-actions" onclick="event.stopPropagation()">'
            f'<button type="button" class="ns-act-btn" onclick="window.TinCanNodeStudio.nodeAction(\'{nid}\', \'ref\')">+ Ref</button>'
            '<span class="ns-act-sep">|</span>'
            f'<button type="button" class="ns-act-btn" onclick="window.TinCanNodeStudio.nodeAction(\'{nid}\', \'edit\')">Edit</button>'
            f'<button type="button" class="ns-act-btn" onclick="window.TinCanNodeStudio.nodeAction(\'{nid}\', \'filter\')">Filter</button>'
            f'<button type="button" class="ns-act-btn" onclick="window.TinCanNodeStudio.nodeAction(\'{nid}\', \'copy\')">Copy</button>'
            f'<button type="button" class="ns-act-btn" onclick="window.TinCanNodeStudio.nodeAction(\'{nid}\', \'save\')">Save</button>'
            '<span class="ns-act-sep">|</span>'
            f'<button type="button" class="ns-act-btn ns-act-del" onclick="window.TinCanNodeStudio.nodeAction(\'{nid}\', \'delete\')" aria-label="Delete node {nid}">×</button>'
            "</div>"
        )

        cards.append(
            f'<article id="nsNode-{nid}" class="ns-node-card{sel_cls}" '
            f'data-node-id="{nid}" data-col="{col}" data-row="{row}" '
            f'role="button" tabindex="0" aria-pressed="{pressed}" '
            f'onclick="window.TinCanNodeStudio.toggleNode(\'{nid}\', event)" '
            f'onkeydown="if(event.key===\'Enter\'||event.key===\' \'){{event.preventDefault();window.TinCanNodeStudio.toggleNode(\'{nid}\', event);}}">'
            f"{quick_bar}"
            '<div class="ns-node-head">'
            f'<span class="ns-node-tag">{_html.escape(node["tag"])}</span>'
            f'<span class="ns-node-badge">{_html.escape(node["badge"])}</span>'
            "</div>"
            f"{body_html}"
            "</article>"
        )
    return "".join(cards)


def _render_filter_rack_html(active_modality: str) -> str:
    rows: List[str] = []
    # Put active modality filters first, keep all 8 filter toggles interactive in the rack
    ordered = sorted(
        FILTER_RACK_SPECS,
        key=lambda f: (0 if f["modality"] == active_modality else 1),
    )
    for f in ordered:
        fid = _html.escape(f["id"], quote=True)
        fmod = _html.escape(f["modality"], quote=True)
        is_active_mod = f["modality"] == active_modality
        enabled = bool(f["enabled"])
        pill_txt = "ON ●" if enabled else "○ OFF"
        pill_cls = "ns-filter-toggle is-on" if enabled else "ns-filter-toggle"
        row_cls = "ns-filter-row" if is_active_mod else "ns-filter-row is-cross-modality"
        rows.append(
            f'<div id="nsFilterRow-{fid}" class="{row_cls}" data-filter-id="{fid}" data-filter-modality="{fmod}">'
            '<div class="ns-filter-info">'
            f'<span class="ns-filter-key">{_html.escape(f["label"])}</span>'
            f'<span class="ns-filter-val">{_html.escape(f["value"])}</span>'
            f'<span class="ns-filter-mod">{_html.escape(f["modality"].upper())}</span>'
            "</div>"
            f'<button id="nsFilterBtn-{fid}" type="button" class="{pill_cls}" '
            f'aria-pressed="{"true" if enabled else "false"}" '
            f'onclick="window.TinCanNodeStudio.toggleFilter(\'{fid}\')">{pill_txt}</button>'
            "</div>"
        )
    return "".join(rows)


def _render_node_table_html(spec: Dict[str, Any]) -> str:
    rows: List[str] = []
    for n in spec["nodes"]:
        nid = _html.escape(n["id"])
        sel_cls = " is-selected" if n.get("selected") else ""
        rows.append(
            f'<tr class="ns-table-row{sel_cls}" data-node-row="{nid}" '
            f'onclick="window.TinCanNodeStudio.toggleNode(\'{nid}\', event)">'
            f"<td>#{nid}</td>"
            f"<td>{_html.escape(n['mode'])}</td>"
            f'<td class="ns-td-wide">{_html.escape(n["filter_model"])}</td>'
            f"<td>{_html.escape(n['cost'])}</td>"
            f"<td>{_html.escape(n['state'])}</td>"
            "</tr>"
        )
    return "".join(rows)


def _render_tree_html(spec: Dict[str, Any]) -> str:
    lines: List[str] = []
    entries = spec["tree"]
    for idx, (name, kind, depth, note) in enumerate(entries):
        if depth == 0:
            prefix = ""
        elif depth == 1:
            is_last_1 = all(d != 1 for _, _, d, _ in entries[idx + 1 :])
            prefix = "└── " if is_last_1 else "├── "
        else:
            parent_is_last = True
            for _, _, d, _ in entries[idx + 1 :]:
                if d == 1:
                    parent_is_last = False
                    break
            is_last_2 = True
            for _, _, d, _ in entries[idx + 1 :]:
                if d < 2:
                    break
                if d == 2:
                    is_last_2 = False
                    break
            lead = "    " if parent_is_last else "│   "
            branch = "└── " if is_last_2 else "├── "
            prefix = lead + branch

        safe_name = _html.escape(name)
        safe_note = f' <span class="ns-tree-note">{_html.escape(note)}</span>' if note else ""
        cls = "ns-tree-line is-dir" if kind == "dir" else "ns-tree-line is-file"
        lines.append(
            f'<button type="button" class="{cls}" data-tree-path="{safe_name}" '
            f'onclick="window.TinCanNodeStudio.selectTreeFile(\'{safe_name}\')">'
            f'<span class="ns-tree-glyph">{_html.escape(prefix)}</span>'
            f'<span class="ns-tree-name">{safe_name}</span>{safe_note}</button>'
        )
    return "".join(lines)


def _render_refs_html(spec: Dict[str, Any]) -> str:
    chips: List[str] = []
    for idx, ref in enumerate(spec["refs"]):
        chips.append(
            f'<div class="ns-ref-chip" draggable="true" data-ref-index="{idx}">'
            '<div class="ns-ref-chip-top">'
            f'<span class="ns-ref-slot">[REF #{idx + 1:02d}]</span>'
            f'<button type="button" class="ns-ref-remove" aria-label="Remove ref {idx + 1}" '
            f'onclick="window.TinCanNodeStudio.removeRef({idx})">×</button>'
            "</div>"
            f'<div class="ns-ref-name">{_html.escape(ref["name"])}</div>'
            f'<div class="ns-ref-kind">{_html.escape(ref["slot"])}</div>'
            "</div>"
        )
    count = len(spec["refs"])
    chips.append(
        '<button id="nsAttachRefBtn" type="button" class="ns-ref-add" '
        'onclick="window.TinCanNodeStudio.attachQuickRef()">'
        f'<span class="ns-ref-add-title">+ Attach .space / Drop Ref</span>'
        f'<span id="nsRefCountHint" class="ns-ref-add-sub">({count}/14)</span>'
        "</button>"
    )
    return "".join(chips)


def _render_model_options_html(selected_model: str) -> str:
    opts: List[str] = []
    for m in MODEL_OPTIONS:
        mid = _html.escape(m["id"], quote=True)
        sel = " selected" if m["id"] == selected_model else ""
        opts.append(
            f'<option value="{mid}" data-modality="{_html.escape(m["modality"], quote=True)}"{sel}>'
            f'{_html.escape(m["label"])}</option>'
        )
    return "".join(opts)


def _render_timeline_strip_html(spec: Dict[str, Any]) -> str:
    parts: List[str] = []
    for idx, step in enumerate(spec["timeline"]):
        if idx > 0:
            parts.append('<span class="ns-tl-arrow" aria-hidden="true">→</span>')
        active_cls = " is-active" if idx == 2 else ""
        parts.append(
            f'<button type="button" class="ns-tl-stop{active_cls}" '
            f'data-tl-index="{idx}" data-tl-node="{_html.escape(step["node"], quote=True)}" '
            f'onclick="window.TinCanNodeStudio.scrubTimeline({idx})">'
            f'{_html.escape(step["label"])}</button>'
        )
    return "".join(parts)


def _render_timeline_view_html(spec: Dict[str, Any]) -> str:
    cards: List[str] = []
    for idx, step in enumerate(spec["timeline"]):
        node = spec["nodes"][idx] if idx < len(spec["nodes"]) else spec["nodes"][-1]
        cards.append(
            '<div class="ns-tl-card">'
            '<div class="ns-tl-card-head">'
            f'<span class="ns-tl-badge">{_html.escape(step["time"])} · NODE {_html.escape(node["id"])}</span>'
            f'<span class="ns-node-badge">{_html.escape(node["state"])}</span>'
            "</div>"
            f'<div class="ns-tl-card-box">{_html.escape(node["box"].splitlines()[0])}</div>'
            f'<div class="ns-tl-card-meta">File: {_html.escape(node["file"])} · {_html.escape(node["filter_model"])}</div>'
            "</div>"
        )
    filter_cards: List[str] = []
    for idx, f in enumerate(FILTER_RACK_SPECS[:4]):
        pill = "ON ●" if f["enabled"] else "○ OFF"
        filter_cards.append(
            '<div class="ns-lib-card">'
            '<div class="ns-tl-card-head">'
            f'<span class="ns-tl-badge">{idx + 1:02d} · {_html.escape(f["modality"].upper())}</span>'
            f'<button type="button" class="ns-filter-toggle is-on" onclick="window.TinCanNodeStudio.toggleFilter(\'{_html.escape(f["id"], quote=True)}\')">{pill}</button>'
            "</div>"
            f'<div class="ns-lib-title">{_html.escape(f["title"])}</div>'
            f'<div class="ns-lib-desc">{_html.escape(f["desc"])}</div>'
            f'<div class="ns-lib-foot">VALUE: {_html.escape(f["value"])} · {_html.escape(f["file"])}</div>'
            "</div>"
        )
    return (
        '<div class="ns-subview-head">'
        '<span class="ns-sec-title">NODE TIMELINE SEQUENCE · NON-DESTRUCTIVE FILTER RACK</span>'
        '<span class="ns-green-status">● NON-DESTRUCTIVE FILTER CHAIN ACTIVE · 0ms PREVIEW</span>'
        "</div>"
        f'<div id="nsTimelineViewCards" class="ns-tl-grid">{"".join(cards)}</div>'
        '<div class="ns-subview-head" style="margin-top:12px;">'
        '<span class="ns-sec-title">PLAYHEAD &amp; ACTIVE PASSES</span>'
        '<button type="button" class="ns-pill is-solid" onclick="window.TinCanNodeStudio.switchView(\'editor\')">Back to 4-Quadrant Editor →</button>'
        "</div>"
        f'<div class="ns-lib-grid">{"".join(filter_cards)}</div>'
    )


def _render_library_view_html() -> str:
    mode_cards = (
        '<div class="ns-lib-card">'
        '<div class="ns-tl-card-head"><span class="ns-tl-badge">01 · GENERATE MODE (0 SELECTED)</span></div>'
        '<div class="ns-lib-title">Root Node Spawn</div>'
        '<div class="ns-lib-desc">Clicking empty DAG canvas clears selection and resets conversation context to spawn a new root node in .space/nodes/.</div>'
        "</div>"
        '<div class="ns-lib-card">'
        '<div class="ns-tl-card-head"><span class="ns-tl-badge">02 · EDIT + FILTER (1 SELECTED)</span></div>'
        '<div class="ns-lib-title">Branch &amp; ThoughtSignature</div>'
        '<div class="ns-lib-desc">Creates hierarchical child branch (parent.child), inherits conversationHistory + thoughtSignature, and wires serial Filter Stack.</div>'
        "</div>"
        '<div class="ns-lib-card">'
        '<div class="ns-tl-card-head"><span class="ns-tl-badge">03 · MERGE MODE (2–14 SELECTED)</span></div>'
        '<div class="ns-lib-title">Drag-Ordered Composite</div>'
        '<div class="ns-lib-desc">Connects edges from all selected parent nodes into a single Composite Node with up to 14 drag-reordered references.</div>'
        "</div>"
    )
    model_rows: List[str] = []
    for m in MODEL_OPTIONS:
        model_rows.append(
            '<div class="ns-model-spec-row">'
            f'<div><strong>{_html.escape(m["id"])}</strong> <span class="ns-muted">({_html.escape(m["alias"])})</span>'
            f'<div class="ns-muted-xs">{_html.escape(m["tier"])}</div></div>'
            f'<button type="button" class="ns-pill" onclick="window.TinCanNodeStudio.selectModel(\'{_html.escape(m["id"], quote=True)}\');window.TinCanNodeStudio.switchView(\'editor\')">'
            f'Use ({_html.escape(m["cost"])})</button>'
            "</div>"
        )
    return (
        '<div class="ns-subview-head">'
        '<span class="ns-sec-title">MODEL_SPECS · CAPABILITY-AWARE SWITCHING &amp; PROMPT ISLAND MODES</span>'
        '<button type="button" class="ns-pill is-solid" onclick="window.TinCanNodeStudio.switchView(\'editor\')">Back to Editor →</button>'
        "</div>"
        f'<div class="ns-lib-grid">{mode_cards}</div>'
        '<div class="ns-model-spec-list">'
        f'{"".join(model_rows)}'
        "</div>"
    )


def _node_studio_css() -> str:
    return """<style id="nsStyles">
  :root {
    --ns-bg: #ecf1e6;
    --ns-card: #f4f8f0;
    --ns-paper: #ffffff;
    --ns-ink: #111111;
    --ns-muted: #4a4a4a;
    --ns-faint: #5c5c5c;
    --ns-green: #107a47;
    --ns-danger: #8a1c1c;
    --ns-font: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    --ns-mono: "JetBrains Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  }

  .ns-shell, .ns-shell * { box-sizing: border-box; }
  .ns-shell {
    background: var(--ns-bg);
    color: var(--ns-ink);
    font-family: var(--ns-font);
    display: flex;
    flex-direction: column;
    min-height: 100%;
    width: 100%;
  }

  .ns-page-wrap {
    min-height: 100vh;
    padding: 16px;
    background: var(--ns-bg);
    display: flex;
    align-items: stretch;
    justify-content: center;
  }

  .ns-terminal-frame {
    width: 100%;
    max-width: 1460px;
    background: var(--ns-bg);
    border: 1px solid var(--ns-ink);
    border-radius: 16px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .ns-window-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 20px 4px;
    font-family: var(--ns-mono);
    font-size: 13px;
    color: var(--ns-ink);
  }
  .ns-clock { font-variant-numeric: tabular-nums; font-weight: 500; }
  .ns-win-controls { display: inline-flex; align-items: center; gap: 14px; }
  .ns-win-btn {
    border: 0; background: transparent; color: var(--ns-ink);
    font-family: var(--ns-mono); font-size: 14px; cursor: pointer;
    padding: 2px 6px; border-radius: 4px;
  }
  .ns-win-btn:hover { background: rgba(17, 17, 17, 0.08); }

  .ns-hero-bar {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    padding: 2px 20px 14px;
  }
  .ns-hero-title {
    margin: 0;
    font-size: clamp(28px, 3vw, 40px);
    font-weight: 400;
    letter-spacing: -0.025em;
    line-height: 1.08;
    color: var(--ns-ink);
  }
  .ns-hero-meta {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
    font-family: var(--ns-mono);
    font-size: 13px;
    color: var(--ns-muted);
    border-left: 1px solid rgba(17, 17, 17, 0.35);
    padding-left: 14px;
  }
  .ns-cwd { color: var(--ns-muted); }
  .ns-seg-group { display: inline-flex; align-items: center; gap: 4px; flex-wrap: wrap; }

  .ns-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 10px;
    border-radius: 9999px;
    border: 1px solid rgba(17, 17, 17, 0.25);
    background: transparent;
    color: var(--ns-ink);
    font-family: var(--ns-mono);
    font-size: 11px;
    font-weight: 500;
    cursor: pointer;
    line-height: 1.35;
    white-space: nowrap;
  }
  .ns-pill:hover { border-color: var(--ns-ink); background: var(--ns-card); }
  .ns-pill.is-active, .ns-pill.is-solid {
    background: var(--ns-ink);
    color: var(--ns-bg);
    border-color: var(--ns-ink);
  }

  .ns-grid-wrap {
    margin: 0 20px;
    border: 1px solid var(--ns-ink);
    background: var(--ns-bg);
    flex: 1 1 auto;
    display: flex;
    flex-direction: column;
  }

  .ns-quad-grid {
    display: grid;
    grid-template-columns: minmax(0, 1.32fr) minmax(0, 1fr);
    grid-template-rows: minmax(340px, 1fr) minmax(260px, auto);
    flex: 1 1 auto;
  }
  .ns-quad {
    display: flex;
    flex-direction: column;
    min-width: 0;
    padding: 12px 14px;
    background: var(--ns-bg);
  }
  .ns-quad--1 { border-right: 1px solid var(--ns-ink); border-bottom: 1px solid var(--ns-ink); }
  .ns-quad--2 { border-bottom: 1px solid var(--ns-ink); }
  .ns-quad--3 { border-right: 1px solid var(--ns-ink); }
  .ns-quad--4 { background: var(--ns-bg); }

  .ns-quad-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(17, 17, 17, 0.55);
    margin-bottom: 10px;
  }
  .ns-sec-title {
    font-family: var(--ns-mono);
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--ns-ink);
  }
  .ns-head-tools {
    display: inline-flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    font-family: var(--ns-mono);
    font-size: 11px;
    color: var(--ns-faint);
  }
  .ns-kbd-btn {
    border: 0;
    background: transparent;
    color: var(--ns-faint);
    font-family: var(--ns-mono);
    font-size: 11px;
    cursor: pointer;
    padding: 1px 4px;
    border-radius: 4px;
  }
  .ns-kbd-btn:hover { background: rgba(17, 17, 17, 0.08); color: var(--ns-ink); }

  /* Quadrant 1: DAG Canvas */
  .ns-dag-canvas {
    position: relative;
    flex: 1 1 auto;
    min-height: 245px;
    padding: 8px 4px;
    overflow-x: auto;
  }
  .ns-dag-wires {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 0;
  }
  .ns-dag-nodes {
    position: relative;
    z-index: 1;
    display: grid;
    grid-template-columns: repeat(4, minmax(150px, 1fr));
    grid-template-rows: auto auto;
    gap: 14px 18px;
    align-items: start;
  }
  .ns-node-card {
    position: relative;
    background: var(--ns-card);
    border: 1px solid var(--ns-ink);
    border-radius: 10px;
    padding: 10px;
    cursor: pointer;
    transition: background 120ms, box-shadow 120ms, transform 120ms;
    min-width: 0;
  }
  .ns-node-card[data-col="1"][data-row="1"] { grid-column: 1; grid-row: 1; }
  .ns-node-card[data-col="1"][data-row="2"] { grid-column: 1; grid-row: 2; }
  .ns-node-card[data-col="2"][data-row="1"] { grid-column: 2; grid-row: 1 / span 2; align-self: center; }
  .ns-node-card[data-col="3"][data-row="1"] { grid-column: 3; grid-row: 1 / span 2; align-self: center; }
  .ns-node-card[data-col="4"][data-row="1"] { grid-column: 4; grid-row: 1 / span 2; align-self: center; }

  .ns-node-card:hover { background: var(--ns-paper); }
  .ns-node-card.is-selected {
    background: var(--ns-paper);
    border-width: 2px;
    box-shadow: 0 0 0 2px rgba(17, 17, 17, 0.12);
  }
  .ns-node-card.is-bypassed { opacity: 0.6; border-style: dashed; }

  .ns-node-actions {
    display: none;
    position: absolute;
    top: -22px;
    left: 6px;
    background: var(--ns-paper);
    border: 1px solid var(--ns-ink);
    border-radius: 9999px;
    padding: 1px 7px;
    font-family: var(--ns-mono);
    font-size: 10px;
    align-items: center;
    gap: 4px;
    white-space: nowrap;
    z-index: 5;
  }
  .ns-node-card:hover .ns-node-actions,
  .ns-node-card.is-selected .ns-node-actions { display: inline-flex; }
  .ns-act-btn {
    border: 0; background: transparent; color: var(--ns-ink);
    font-family: var(--ns-mono); font-size: 10px; cursor: pointer; padding: 0 2px;
  }
  .ns-act-btn:hover { text-decoration: underline; }
  .ns-act-del { color: var(--ns-danger); font-weight: 700; }
  .ns-act-sep { color: var(--ns-faint); }

  .ns-node-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
    margin-bottom: 6px;
  }
  .ns-node-tag {
    font-family: var(--ns-mono);
    font-size: 10px;
    font-weight: 600;
    color: var(--ns-ink);
  }
  .ns-node-badge {
    font-family: var(--ns-mono);
    font-size: 10px;
    color: var(--ns-muted);
    border: 1px solid rgba(17, 17, 17, 0.25);
    border-radius: 9999px;
    padding: 0 6px;
  }
  .ns-node-preview {
    border: 1px solid rgba(17, 17, 17, 0.65);
    border-radius: 6px;
    background: var(--ns-paper);
    padding: 8px;
    font-family: var(--ns-mono);
    font-size: 11px;
    line-height: 1.4;
    color: var(--ns-ink);
    margin-bottom: 6px;
  }
  .ns-node-file {
    font-family: var(--ns-mono);
    font-size: 11px;
    font-weight: 600;
    color: var(--ns-ink);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .ns-node-meta {
    font-family: var(--ns-mono);
    font-size: 10px;
    color: var(--ns-faint);
    margin-top: 2px;
  }
  .ns-gauge-wrap {
    position: relative;
    width: 56px;
    height: 56px;
    margin: 4px auto 6px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .ns-gauge-svg { width: 56px; height: 56px; }
  .ns-gauge-pct {
    position: absolute;
    font-family: var(--ns-mono);
    font-size: 11px;
    font-weight: 700;
    color: var(--ns-ink);
  }

  .ns-timeline-strip {
    margin-top: 10px;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;
    padding: 6px 10px;
    border: 1px solid var(--ns-ink);
    border-radius: 8px;
    background: var(--ns-card);
    font-family: var(--ns-mono);
    font-size: 11px;
  }
  .ns-tl-prefix { font-weight: 600; color: var(--ns-ink); }
  .ns-tl-stop {
    border: 1px solid transparent;
    background: transparent;
    color: var(--ns-ink);
    font-family: var(--ns-mono);
    font-size: 11px;
    padding: 2px 6px;
    border-radius: 9999px;
    cursor: pointer;
  }
  .ns-tl-stop:hover { border-color: rgba(17, 17, 17, 0.35); }
  .ns-tl-stop.is-active { background: var(--ns-ink); color: var(--ns-bg); }
  .ns-tl-arrow { color: var(--ns-faint); }
  .ns-tl-play {
    margin-left: auto;
    border: 1px solid var(--ns-ink);
    background: var(--ns-ink);
    color: var(--ns-bg);
    font-family: var(--ns-mono);
    font-size: 11px;
    padding: 2px 9px;
    border-radius: 9999px;
    cursor: pointer;
  }

  /* Quadrant 2: Telemetry + Filter Rack */
  .ns-kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 8px;
    margin-bottom: 10px;
  }
  .ns-kpi-label {
    font-family: var(--ns-mono);
    font-size: 10px;
    color: var(--ns-faint);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .ns-kpi-val {
    font-size: 20px;
    font-weight: 500;
    letter-spacing: -0.02em;
    color: var(--ns-ink);
    font-variant-numeric: tabular-nums;
    margin-top: 2px;
  }
  .ns-spark-wrap {
    padding: 4px 0 8px;
    border-bottom: 1px solid rgba(17, 17, 17, 0.2);
    margin-bottom: 8px;
  }
  .ns-sparkline { width: 100%; height: 32px; display: block; }

  .ns-filter-rack {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 6px;
    margin-bottom: 10px;
  }
  .ns-filter-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
    padding: 4px 8px;
    border: 1px solid rgba(17, 17, 17, 0.25);
    border-radius: 8px;
    background: var(--ns-card);
    font-family: var(--ns-mono);
    font-size: 10px;
  }
  .ns-filter-row.is-cross-modality { opacity: 0.72; background: transparent; }
  .ns-filter-info { display: flex; align-items: center; gap: 5px; min-width: 0; overflow: hidden; }
  .ns-filter-key { font-weight: 600; color: var(--ns-ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .ns-filter-val { color: var(--ns-muted); white-space: nowrap; }
  .ns-filter-mod {
    font-size: 9px; color: var(--ns-faint);
    border: 1px solid rgba(17, 17, 17, 0.18); border-radius: 9999px; padding: 0 4px;
  }
  .ns-filter-toggle {
    border: 1px solid var(--ns-ink);
    border-radius: 9999px;
    padding: 1px 8px;
    font-family: var(--ns-mono);
    font-size: 10px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    background: var(--ns-paper);
    color: var(--ns-ink);
  }
  .ns-filter-toggle.is-on { background: var(--ns-ink); color: var(--ns-bg); }

  .ns-node-table {
    width: 100%;
    border-collapse: collapse;
    font-family: var(--ns-mono);
    font-size: 11px;
  }
  .ns-node-table th {
    text-align: left;
    font-size: 10px;
    font-weight: 600;
    color: var(--ns-faint);
    padding: 3px 4px;
    border-bottom: 1px solid rgba(17, 17, 17, 0.2);
  }
  .ns-node-table td { padding: 3px 4px; color: var(--ns-ink); white-space: nowrap; }
  .ns-node-table td.ns-td-wide { max-width: 170px; overflow: hidden; text-overflow: ellipsis; }
  .ns-table-row { cursor: pointer; }
  .ns-table-row:hover td { background: var(--ns-card); }
  .ns-table-row.is-selected td { font-weight: 600; background: var(--ns-paper); }

  /* Quadrant 3: Tree */
  .ns-tree-list {
    display: flex;
    flex-direction: column;
    gap: 1px;
    font-family: var(--ns-mono);
    font-size: 12px;
    line-height: 1.48;
  }
  .ns-tree-line {
    display: flex;
    align-items: baseline;
    text-align: left;
    border: 0;
    background: transparent;
    color: var(--ns-ink);
    font-family: var(--ns-mono);
    font-size: 12px;
    padding: 1px 4px;
    border-radius: 4px;
    cursor: pointer;
    white-space: pre;
  }
  .ns-tree-line:hover, .ns-tree-line.is-active { background: var(--ns-card); }
  .ns-tree-line.is-dir .ns-tree-name { font-weight: 600; }
  .ns-tree-glyph { color: var(--ns-faint); }
  .ns-tree-note { color: var(--ns-faint); margin-left: 8px; font-size: 11px; }
  .ns-tree-footer {
    margin-top: auto;
    padding-top: 10px;
    font-family: var(--ns-mono);
    font-size: 11px;
    color: var(--ns-faint);
  }

  /* Quadrant 4: Prompt Island */
  .ns-pi-head-pills { display: inline-flex; align-items: center; gap: 6px; flex-wrap: wrap; }
  .ns-mode-pill {
    display: inline-flex;
    align-items: center;
    padding: 2px 9px;
    border-radius: 9999px;
    background: var(--ns-ink);
    color: var(--ns-bg);
    font-family: var(--ns-mono);
    font-size: 10px;
    font-weight: 600;
  }
  .ns-conv-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 2px 9px;
    border-radius: 9999px;
    border: 1px solid rgba(17, 17, 17, 0.35);
    background: var(--ns-card);
    color: var(--ns-ink);
    font-family: var(--ns-mono);
    font-size: 10px;
    cursor: pointer;
  }
  .ns-model-select {
    font-family: var(--ns-mono);
    font-size: 11px;
    border: 1px solid rgba(17, 17, 17, 0.35);
    border-radius: 8px;
    background: var(--ns-paper);
    color: var(--ns-ink);
    padding: 2px 8px;
    max-width: 240px;
  }
  .ns-green-status {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-family: var(--ns-mono);
    font-size: 11px;
    font-weight: 600;
    color: var(--ns-green);
    background: transparent;
    border: 1px solid rgba(16, 122, 71, 0.35);
    border-radius: 9999px;
    padding: 2px 9px;
    cursor: pointer;
  }
  .ns-api-drawer {
    margin-bottom: 8px;
    padding: 8px 10px;
    border: 1px solid var(--ns-ink);
    border-radius: 8px;
    background: var(--ns-card);
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    font-family: var(--ns-mono);
    font-size: 11px;
  }
  .ns-api-drawer.hidden { display: none; }
  .ns-api-field { display: flex; flex-direction: column; gap: 3px; }
  .ns-api-field label { font-size: 10px; color: var(--ns-muted); font-weight: 600; }
  .ns-api-field input {
    border: 1px solid rgba(17, 17, 17, 0.35);
    border-radius: 6px;
    background: var(--ns-paper);
    color: var(--ns-ink);
    padding: 4px 8px;
    font-family: var(--ns-mono);
    font-size: 11px;
  }

  .ns-refs-row {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 8px;
    margin-bottom: 10px;
  }
  .ns-ref-chip {
    border: 1px solid var(--ns-ink);
    border-radius: 8px;
    background: var(--ns-card);
    padding: 6px 8px;
    font-family: var(--ns-mono);
    cursor: grab;
    min-width: 0;
  }
  .ns-ref-chip.is-dragging { opacity: 0.55; }
  .ns-ref-chip-top { display: flex; align-items: center; justify-content: space-between; font-size: 10px; font-weight: 600; }
  .ns-ref-remove { border: 0; background: transparent; color: var(--ns-muted); cursor: pointer; font-size: 12px; }
  .ns-ref-name { font-size: 11px; color: var(--ns-ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 2px; }
  .ns-ref-kind { font-size: 9px; color: var(--ns-faint); margin-top: 1px; }
  .ns-ref-add {
    border: 1px dashed rgba(17, 17, 17, 0.45);
    border-radius: 8px;
    background: transparent;
    color: var(--ns-muted);
    padding: 6px 8px;
    font-family: var(--ns-mono);
    text-align: left;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  .ns-ref-add:hover { border-color: var(--ns-ink); background: var(--ns-card); color: var(--ns-ink); }
  .ns-ref-add-title { font-size: 10px; font-weight: 600; }
  .ns-ref-add-sub { font-size: 10px; color: var(--ns-faint); }

  .ns-cli-preview {
    font-family: var(--ns-mono);
    font-size: 11px;
    line-height: 1.45;
    color: var(--ns-ink);
    margin-bottom: 6px;
    word-break: break-word;
  }
  .ns-prompt-box {
    width: 100%;
    min-height: 58px;
    resize: vertical;
    border: 1px solid rgba(17, 17, 17, 0.35);
    border-radius: 8px;
    background: var(--ns-paper);
    color: var(--ns-ink);
    padding: 8px 10px;
    font-family: var(--ns-mono);
    font-size: 12px;
    line-height: 1.45;
  }

  .ns-pi-controls {
    margin-top: 10px;
    padding-top: 8px;
    border-top: 1px solid rgba(17, 17, 17, 0.22);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
  }
  .ns-pi-selects { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; }
  .ns-ctrl-select {
    font-family: var(--ns-mono);
    font-size: 10px;
    font-weight: 600;
    border: 1px solid rgba(17, 17, 17, 0.28);
    border-radius: 9999px;
    background: var(--ns-card);
    color: var(--ns-ink);
    padding: 3px 8px;
  }
  .ns-gen-btn {
    border: 1px solid var(--ns-ink);
    border-radius: 9999px;
    background: var(--ns-ink);
    color: var(--ns-bg);
    font-family: var(--ns-mono);
    font-size: 11px;
    font-weight: 600;
    padding: 6px 16px;
    cursor: pointer;
    white-space: nowrap;
  }
  .ns-gen-btn:hover { opacity: 0.9; }
  .ns-gen-feedback {
    margin-top: 6px;
    font-family: var(--ns-mono);
    font-size: 10px;
    color: var(--ns-green);
    min-height: 14px;
  }

  /* Subviews (Timeline / Library) */
  .ns-subview { padding: 14px; }
  .ns-subview.hidden, .ns-quad-grid.hidden { display: none; }
  .ns-subview-head {
    display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;
    padding-bottom: 8px; border-bottom: 1px solid rgba(17, 17, 17, 0.35); margin-bottom: 10px;
  }
  .ns-tl-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
  .ns-tl-card, .ns-lib-card {
    border: 1px solid var(--ns-ink); border-radius: 10px; background: var(--ns-card); padding: 10px;
    font-family: var(--ns-mono);
  }
  .ns-tl-card-head { display: flex; align-items: center; justify-content: space-between; gap: 6px; margin-bottom: 6px; }
  .ns-tl-badge {
    background: var(--ns-ink); color: var(--ns-bg); border-radius: 9999px;
    padding: 2px 8px; font-size: 10px; font-weight: 600;
  }
  .ns-tl-card-box {
    border: 1px solid rgba(17, 17, 17, 0.4); border-radius: 6px; background: var(--ns-paper);
    padding: 8px; font-size: 11px; margin-bottom: 6px;
  }
  .ns-tl-card-meta, .ns-lib-desc, .ns-lib-foot { font-size: 10px; color: var(--ns-muted); line-height: 1.4; }
  .ns-lib-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; }
  .ns-lib-title { font-family: var(--ns-font); font-size: 14px; font-weight: 600; margin-bottom: 4px; }
  .ns-model-spec-list { margin-top: 12px; display: flex; flex-direction: column; gap: 6px; }
  .ns-model-spec-row {
    display: flex; align-items: center; justify-content: space-between; gap: 10px;
    padding: 8px 10px; border: 1px solid var(--ns-ink); border-radius: 8px; background: var(--ns-card);
    font-family: var(--ns-mono); font-size: 11px;
  }
  .ns-muted { color: var(--ns-muted); }
  .ns-muted-xs { color: var(--ns-faint); font-size: 10px; margin-top: 2px; }

  /* Bottom Status Bar */
  .ns-status-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
    padding: 10px 20px;
    font-family: var(--ns-mono);
    font-size: 12px;
    color: var(--ns-muted);
  }
  .ns-status-left, .ns-status-right { display: inline-flex; align-items: center; flex-wrap: wrap; gap: 10px; }
  .ns-status-sep { color: rgba(17, 17, 17, 0.35); }

  /* Mesh OS window overrides */
  .tc-ns-host .window-body { padding: 0 !important; background: var(--ns-bg) !important; }
  .tc-ns-host .ns-terminal-frame { border: 0; border-radius: 0; max-width: none; }
  .tc-ns-host .ns-window-bar { display: none; }

  @media (max-width: 980px) {
    .ns-quad-grid { grid-template-columns: 1fr; grid-template-rows: auto; }
    .ns-quad--1, .ns-quad--3 { border-right: 0; }
    .ns-quad--3 { border-bottom: 1px solid var(--ns-ink); }
    .ns-dag-nodes { grid-template-columns: 1fr; grid-template-rows: auto; }
    .ns-node-card[data-col] { grid-column: auto !important; grid-row: auto !important; }
    .ns-refs-row, .ns-tl-grid, .ns-kpi-grid, .ns-filter-rack, .ns-api-drawer { grid-template-columns: 1fr; }
  }
</style>"""


def _node_studio_js(initial_modality: str, initial_view: str) -> str:
    specs_json = _safe_json(MODALITY_SPECS)
    filters_json = _safe_json(list(FILTER_RACK_SPECS))
    models_json = _safe_json(list(MODEL_OPTIONS))
    sparklines_json = _safe_json({k: list(v) for k, v in SPARKLINE_BARS.items()})

    template = r"""<script id="nodeStudioUiScript">
(function () {
  const SPECS = __SPECS_JSON__;
  const FILTER_SPECS = __FILTERS_JSON__;
  const MODEL_SPECS = __MODELS_JSON__;
  const SPARKLINES = __SPARKLINES_JSON__;

  const state = {
    modality: __INIT_MODALITY__,
    view: __INIT_VIEW__,
    selectedIds: [],
    filters: {},
    bypassed: false,
    inConversation: true,
    refs: [],
    model: "nano-banana-2.1",
    aspect: "21:9",
    resolution: "4K",
    thinking: "high",
    search: "web+img",
    via: "auto",
    playTimer: null,
    playIndex: 0,
    dragRefIndex: null
  };

  FILTER_SPECS.forEach((f) => { state.filters[f.id] = !!f.enabled; });

  function $(id) { return document.getElementById(id); }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function currentSpec() {
    return SPECS[state.modality] || SPECS.image;
  }

  function updateClock() {
    const el = $("nsTopClock");
    if (!el) return;
    const now = new Date();
    const hh = String(now.getHours()).padStart(2, "0");
    const mm = String(now.getMinutes()).padStart(2, "0");
    if (!el.dataset.pinnedClock) el.textContent = hh + ":" + mm;
  }

  function deriveMode() {
    const count = state.selectedIds.length;
    if (count === 0) return { key: "generate", short: "GENERATE", pill: "MODE: GENERATE (0 SELECTED)" };
    if (count === 1) return { key: "edit", short: "EDIT + FILTER", pill: "MODE: EDIT + FILTER (1 SELECTED)" };
    return { key: "merge", short: "MERGE", pill: "MODE: MERGE (" + count + " SELECTED)" };
  }

  function activeFilterArg() {
    const active = FILTER_SPECS.filter((f) => state.filters[f.id] && f.modality === state.modality);
    if (state.bypassed || active.length === 0) return "bypassed";
    return active.map((f) => f.id + ":" + String(f.value).toLowerCase().replace(/[^a-z0-9.%+-]/g, "")).join(",");
  }

  function renderModeAndStatus() {
    const spec = currentSpec();
    const mode = deriveMode();
    const modePill = $("nsModePill");
    if (modePill) modePill.textContent = mode.pill;

    const cli = $("nsCliPreview");
    if (cli) {
      cli.textContent =
        "tincan@studio:" + spec.path + "$ prompt --mode " + mode.key +
        " --via " + state.via + " --model " + state.model +
        " --aspect " + state.aspect + " --res " + state.resolution +
        " --think " + state.thinking + " --search " + state.search +
        " --filters \"" + activeFilterArg() + "\"";
    }

    const statusBar = $("nsBottomStatusLeft");
    if (statusBar) {
      const modeText = state.modality === "image"
        ? mode.short
        : (state.modality.toUpperCase() + " " + mode.short);
      statusBar.innerHTML =
        '<span>main ↑1 ↓0</span><span class="ns-status-sep">|</span>' +
        '<span>' + escapeHtml(spec.path) + '</span><span class="ns-status-sep">|</span>' +
        '<span>' + escapeHtml(modeText) + ' (' + state.refs.length + '/14 refs)</span><span class="ns-status-sep">|</span>' +
        '<span>' + escapeHtml(state.model) + '</span>';
    }
  }

  function drawDagWires() {
    const canvas = $("nsDagCanvas");
    const svg = $("nsDagWires");
    if (!canvas || !svg) return;
    const cRect = canvas.getBoundingClientRect();
    if (!cRect.width || !cRect.height) return;

    function pt(id, side) {
      const el = $("nsNode-" + id);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      const x = (side === "right" ? r.right : r.left) - cRect.left;
      const y = (r.top + r.height / 2) - cRect.top;
      return { x: Math.round(x), y: Math.round(y) };
    }

    const pairs = [["01", "03"], ["03", "04"], ["02", "04"], ["04", "05"]];
    const paths = [];
    pairs.forEach(([aId, bId]) => {
      const a = pt(aId, "right");
      const b = pt(bId, "left");
      if (!a || !b) return;
      const midX = Math.round((a.x + b.x) / 2);
      paths.push(
        '<path d="M ' + a.x + " " + a.y + " L " + midX + " " + a.y + " L " + midX + " " + b.y + " L " + b.x + " " + b.y +
        '" fill="none" stroke="#111111" stroke-width="1.5"/>'
      );
    });
    svg.setAttribute("viewBox", "0 0 " + Math.round(cRect.width) + " " + Math.round(cRect.height));
    svg.innerHTML = paths.join("");
  }

  function renderRefs() {
    const row = $("nsRefsRow");
    if (!row) return;
    const items = state.refs.map((ref, idx) =>
      '<div class="ns-ref-chip" draggable="true" data-ref-index="' + idx + '">' +
      '<div class="ns-ref-chip-top">' +
      '<span class="ns-ref-slot">[REF #' + String(idx + 1).padStart(2, "0") + ']</span>' +
      '<button type="button" class="ns-ref-remove" aria-label="Remove ref ' + (idx + 1) + '" ' +
      'onclick="window.TinCanNodeStudio.removeRef(' + idx + ')">×</button>' +
      '</div>' +
      '<div class="ns-ref-name">' + escapeHtml(ref.name) + '</div>' +
      '<div class="ns-ref-kind">' + escapeHtml(ref.slot) + '</div>' +
      '</div>'
    );
    const attachBtnId = "nsAttachRefBtn";
    const refHintId = "nsRefCountHint";
    items.push(
      '<button id="' + attachBtnId + '" type="button" class="ns-ref-add" onclick="window.TinCanNodeStudio.attachQuickRef()">' +
      '<span class="ns-ref-add-title">+ Attach .space / Drop Ref</span>' +
      '<span id="' + refHintId + '" class="ns-ref-add-sub">(' + state.refs.length + '/14)</span>' +
      '</button>'
    );
    row.innerHTML = items.join("");
    bindRefDragEvents();
    renderModeAndStatus();
  }

  function bindRefDragEvents() {
    const row = $("nsRefsRow");
    if (!row) return;
    row.querySelectorAll(".ns-ref-chip").forEach((chip) => {
      chip.addEventListener("dragstart", (ev) => {
        state.dragRefIndex = parseInt(chip.dataset.refIndex, 10);
        chip.classList.add("is-dragging");
        if (ev.dataTransfer) ev.dataTransfer.effectAllowed = "move";
      });
      chip.addEventListener("dragend", () => {
        chip.classList.remove("is-dragging");
        state.dragRefIndex = null;
      });
      chip.addEventListener("dragover", (ev) => { ev.preventDefault(); });
      chip.addEventListener("drop", (ev) => {
        ev.preventDefault();
        const targetIdx = parseInt(chip.dataset.refIndex, 10);
        if (state.dragRefIndex === null || isNaN(targetIdx) || state.dragRefIndex === targetIdx) return;
        const moved = state.refs.splice(state.dragRefIndex, 1)[0];
        state.refs.splice(targetIdx, 0, moved);
        renderRefs();
      });
    });
  }

  function applyModality(modality, pushQuery) {
    if (!SPECS[modality]) modality = "image";
    state.modality = modality;
    const spec = currentSpec();
    state.selectedIds = spec.nodes.filter((n) => n.selected).map((n) => n.id);
    state.refs = spec.refs.map((r) => Object.assign({}, r));
    state.model = spec.default_model;
    state.aspect = spec.aspect;
    state.resolution = spec.resolution;
    state.thinking = spec.thinking;
    state.search = spec.search;
    state.via = spec.via;

    const hero = $("nsHeroTitle");
    if (hero) hero.textContent = spec.hero_title;
    const cwd = $("nsHeaderCwd");
    if (cwd) cwd.textContent = spec.path;
    const q1Title = $("nsQ1Title");
    if (q1Title) q1Title.textContent = spec.q1_title;
    const q2Title = $("nsQ2Title");
    if (q2Title) q2Title.textContent = spec.q2_title;
    const q2End = $("nsQ2Endpoint");
    if (q2End) q2End.textContent = spec.q2_endpoint;
    const q3Title = $("nsQ3Title");
    if (q3Title) q3Title.textContent = spec.tree_header;
    const apiBtn = $("nsApiStatusBtn");
    if (apiBtn) apiBtn.textContent = "● " + spec.api_label;
    const genBtn = $("nsGenerateBtn");
    if (genBtn) genBtn.textContent = spec.cta_label;
    const promptInput = $("nsPromptInput");
    if (promptInput) promptInput.value = spec.prompt;
    const modelSel = $("nsModelSelect");
    if (modelSel) modelSel.value = spec.default_model;

    document.querySelectorAll("[data-modality-btn]").forEach((btn) => {
      const m = btn.dataset.modalityBtn;
      const active = m === modality;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-pressed", active ? "true" : "false");
      const label = m.charAt(0).toUpperCase() + m.slice(1);
      btn.textContent = active ? ("● " + label) : label;
    });

    const kpiGrid = $("nsKpiGrid");
    if (kpiGrid) {
      kpiGrid.innerHTML = spec.metrics.map((m) =>
        '<div><div class="ns-kpi-label">' + escapeHtml(m.label) + '</div>' +
        '<div class="ns-kpi-val">' + escapeHtml(m.value) + '</div></div>'
      ).join("");
    }

    const sparkWrap = $("nsSparkWrap");
    if (sparkWrap) {
      const bars = SPARKLINES[modality] || SPARKLINES.image;
      const rects = bars.map((h, i) =>
        '<rect x="' + (i * 14 + 2) + '" y="' + (36 - h) + '" width="2" height="' + h +
        '" rx="1" fill="#111111" opacity="' + (i % 3 === 0 ? "0.92" : "0.62") + '"/>'
      ).join("");
      sparkWrap.innerHTML = '<svg class="ns-sparkline" viewBox="0 0 ' + (bars.length * 14 + 4) +
        ' 36" preserveAspectRatio="none" role="img" aria-label="Node Studio filter sparkline">' + rects + '</svg>';
    }

    const gaugeArcId = "nsLivingGaugeArc";
    const gaugePctId = "nsLivingGaugePct";
    const dagNodes = $("nsDagNodes");
    if (dagNodes) {
      dagNodes.innerHTML = spec.nodes.map((n) => {
        const isSel = state.selectedIds.indexOf(n.id) !== -1;
        const inner = n.id === "05"
          ? ('<div class="ns-gauge-wrap"><svg class="ns-gauge-svg" viewBox="0 0 52 52" aria-hidden="true">' +
             '<circle cx="26" cy="26" r="20" fill="none" stroke="rgba(17,17,17,0.18)" stroke-width="3"/>' +
             '<circle id="' + gaugeArcId + '" cx="26" cy="26" r="20" fill="none" stroke="#111111" stroke-width="3" ' +
             'stroke-dasharray="125.66" stroke-dashoffset="' + (125.66 * (1 - (n.pct || 68) / 100)).toFixed(2) +
             '" transform="rotate(-90 26 26)"/></svg>' +
             '<span id="' + gaugePctId + '" class="ns-gauge-pct">' + (n.pct || 68) + '%</span></div>' +
             '<div class="ns-node-file">' + escapeHtml(n.box) + '</div>' +
             '<div class="ns-node-meta">' + escapeHtml(n.meta) + '</div>')
          : ('<div class="ns-node-preview">' + escapeHtml(n.box).replace(/\n/g, "<br>") + '</div>' +
             '<div class="ns-node-file">' + escapeHtml(n.file) + '</div>' +
             '<div class="ns-node-meta">' + escapeHtml(n.meta) + '</div>');

        return '<article id="nsNode-' + n.id + '" class="ns-node-card' + (isSel ? " is-selected" : "") +
          '" data-node-id="' + n.id + '" data-col="' + n.col + '" data-row="' + n.row +
          '" role="button" tabindex="0" aria-pressed="' + (isSel ? "true" : "false") +
          '" onclick="window.TinCanNodeStudio.toggleNode(\'' + n.id + '\', event)">' +
          '<div class="ns-node-actions" onclick="event.stopPropagation()">' +
          '<button type="button" class="ns-act-btn" onclick="window.TinCanNodeStudio.nodeAction(\'' + n.id + '\', \'ref\')">+ Ref</button>' +
          '<span class="ns-act-sep">|</span>' +
          '<button type="button" class="ns-act-btn" onclick="window.TinCanNodeStudio.nodeAction(\'' + n.id + '\', \'edit\')">Edit</button>' +
          '<button type="button" class="ns-act-btn" onclick="window.TinCanNodeStudio.nodeAction(\'' + n.id + '\', \'filter\')">Filter</button>' +
          '<button type="button" class="ns-act-btn" onclick="window.TinCanNodeStudio.nodeAction(\'' + n.id + '\', \'copy\')">Copy</button>' +
          '<button type="button" class="ns-act-btn" onclick="window.TinCanNodeStudio.nodeAction(\'' + n.id + '\', \'save\')">Save</button>' +
          '<span class="ns-act-sep">|</span>' +
          '<button type="button" class="ns-act-btn ns-act-del" onclick="window.TinCanNodeStudio.nodeAction(\'' + n.id + '\', \'delete\')">×</button>' +
          '</div>' +
          '<div class="ns-node-head"><span class="ns-node-tag">' + escapeHtml(n.tag) + '</span>' +
          '<span class="ns-node-badge">' + escapeHtml(n.badge) + '</span></div>' + inner + '</article>';
      }).join("");
    }

    const tlPrefix = $("nsTlPrefix");
    if (tlPrefix) tlPrefix.textContent = spec.timeline_prefix;
    const tlStops = $("nsTlStops");
    if (tlStops) {
      tlStops.innerHTML = spec.timeline.map((s, idx) =>
        (idx > 0 ? '<span class="ns-tl-arrow" aria-hidden="true">→</span>' : "") +
        '<button type="button" class="ns-tl-stop' + (idx === 2 ? " is-active" : "") +
        '" data-tl-index="' + idx + '" data-tl-node="' + escapeHtml(s.node) +
        '" onclick="window.TinCanNodeStudio.scrubTimeline(' + idx + ')">' + escapeHtml(s.label) + '</button>'
      ).join("");
    }

    const tblBody = $("nsNodeTableBody");
    if (tblBody) {
      tblBody.innerHTML = spec.nodes.map((n) => {
        const isSel = state.selectedIds.indexOf(n.id) !== -1;
        return '<tr class="ns-table-row' + (isSel ? " is-selected" : "") + '" data-node-row="' + n.id +
          '" onclick="window.TinCanNodeStudio.toggleNode(\'' + n.id + '\', event)">' +
          '<td>#' + escapeHtml(n.id) + '</td><td>' + escapeHtml(n.mode) + '</td>' +
          '<td class="ns-td-wide">' + escapeHtml(n.filter_model) + '</td>' +
          '<td>' + escapeHtml(n.cost) + '</td><td>' + escapeHtml(n.state) + '</td></tr>';
      }).join("");
    }

    document.querySelectorAll("[data-filter-modality]").forEach((row) => {
      row.classList.toggle("is-cross-modality", row.dataset.filterModality !== modality);
    });

    const treeList = $("nsTreeList");
    if (treeList) {
      treeList.innerHTML = spec.tree.map((entry, idx) => {
        const name = entry[0], kind = entry[1], depth = entry[2], note = entry[3];
        let prefix = "";
        if (depth === 1) {
          const isLast1 = spec.tree.slice(idx + 1).every((e) => e[2] !== 1);
          prefix = isLast1 ? "└── " : "├── ";
        } else if (depth >= 2) {
          let parentLast = true;
          for (let i = idx + 1; i < spec.tree.length; i++) {
            if (spec.tree[i][2] === 1) { parentLast = false; break; }
          }
          let isLast2 = true;
          for (let j = idx + 1; j < spec.tree.length; j++) {
            if (spec.tree[j][2] < 2) break;
            if (spec.tree[j][2] === 2) { isLast2 = false; break; }
          }
          prefix = (parentLast ? "    " : "│   ") + (isLast2 ? "└── " : "├── ");
        }
        return '<button type="button" class="ns-tree-line ' + (kind === "dir" ? "is-dir" : "is-file") +
          '" data-tree-path="' + escapeHtml(name) + '" onclick="window.TinCanNodeStudio.selectTreeFile(\'' + escapeHtml(name) + '\')">' +
          '<span class="ns-tree-glyph">' + escapeHtml(prefix) + '</span>' +
          '<span class="ns-tree-name">' + escapeHtml(name) + '</span>' +
          (note ? ' <span class="ns-tree-note">' + escapeHtml(note) + '</span>' : '') + '</button>';
      }).join("");
    }
    const treeFoot = $("nsTreeFooter");
    if (treeFoot) treeFoot.textContent = spec.tree_footer;

    renderRefs();
    setTimeout(drawDagWires, 0);

    if (pushQuery && typeof window.history !== "undefined" && window.history.replaceState) {
      try {
        const u = new URL(window.location.href);
        u.searchParams.set("modality", modality);
        window.history.replaceState({}, "", u.toString());
      } catch (_err) {}
    }
  }

  function syncSelectionDom() {
    document.querySelectorAll(".ns-node-card").forEach((el) => {
      const nid = el.dataset.nodeId;
      const sel = state.selectedIds.indexOf(nid) !== -1;
      el.classList.toggle("is-selected", sel);
      el.setAttribute("aria-pressed", sel ? "true" : "false");
    });
    document.querySelectorAll("[data-node-row]").forEach((row) => {
      row.classList.toggle("is-selected", state.selectedIds.indexOf(row.dataset.nodeRow) !== -1);
    });
    renderModeAndStatus();
  }

  function toggleNode(nodeId, ev) {
    if (ev && ev.stopPropagation) ev.stopPropagation();
    const idx = state.selectedIds.indexOf(nodeId);
    if (idx === -1) {
      state.selectedIds.push(nodeId);
    } else {
      state.selectedIds.splice(idx, 1);
    }
    syncSelectionDom();
  }

  function clearSelection() {
    state.selectedIds = [];
    syncSelectionDom();
  }

  function toggleFilter(filterId) {
    state.filters[filterId] = !state.filters[filterId];
    const btn = $("nsFilterBtn-" + filterId);
    if (btn) {
      const on = !!state.filters[filterId];
      btn.classList.toggle("is-on", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
      btn.textContent = on ? "ON ●" : "○ OFF";
    }
    renderModeAndStatus();
    if (typeof fetch === "function") {
      fetch("/api/nodes/filter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filter_id: filterId, enabled: !!state.filters[filterId], modality: state.modality })
      }).catch(() => {});
    }
  }

  function bypassFilters() {
    state.bypassed = !state.bypassed;
    document.querySelectorAll(".ns-node-card").forEach((el) => {
      el.classList.toggle("is-bypassed", state.bypassed);
    });
    const fb = $("nsGenFeedback");
    if (fb) fb.textContent = state.bypassed ? "Filter chain bypassed [Cmd+D]" : "Filter chain active";
    renderModeAndStatus();
  }

  function switchView(view) {
    if (["editor", "timeline", "library"].indexOf(view) === -1) view = "editor";
    state.view = view;
    document.querySelectorAll("[data-view-btn]").forEach((btn) => {
      const active = btn.dataset.viewBtn === view;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-pressed", active ? "true" : "false");
    });
    const quad = $("nsQuadGrid");
    const tl = $("nsTimelineSubview");
    const lib = $("nsLibrarySubview");
    if (quad) quad.classList.toggle("hidden", view !== "editor");
    if (tl) tl.classList.toggle("hidden", view !== "timeline");
    if (lib) lib.classList.toggle("hidden", view !== "library");
    if (view === "editor") setTimeout(drawDagWires, 0);
  }

  function scrubTimeline(idx) {
    state.playIndex = idx;
    document.querySelectorAll(".ns-tl-stop").forEach((btn) => {
      btn.classList.toggle("is-active", parseInt(btn.dataset.tlIndex, 10) === idx);
    });
  }

  function togglePlayTimeline() {
    const btn = $("nsTimelinePlayBtn");
    if (state.playTimer) {
      clearInterval(state.playTimer);
      state.playTimer = null;
      if (btn) btn.textContent = "▶";
      return;
    }
    if (btn) btn.textContent = "❚❚";
    state.playTimer = setInterval(() => {
      const stops = document.querySelectorAll(".ns-tl-stop");
      if (!stops.length) return;
      state.playIndex = (state.playIndex + 1) % stops.length;
      scrubTimeline(state.playIndex);
    }, 900);
  }

  function removeRef(idx) {
    if (idx < 0 || idx >= state.refs.length) return;
    state.refs.splice(idx, 1);
    renderRefs();
  }

  function attachQuickRef(name, slot) {
    if (state.refs.length >= 14) return;
    const num = state.refs.length + 1;
    state.refs.push({
      slot: slot || ("REF #" + String(num).padStart(2, "0") + " · SPACE"),
      name: name || ("space_ref_0" + num + ".png")
    });
    renderRefs();
  }

  function selectTreeFile(name) {
    document.querySelectorAll(".ns-tree-line").forEach((el) => {
      el.classList.toggle("is-active", el.dataset.treePath === name);
    });
    if (!name.endsWith("/") && state.refs.length < 14) {
      attachQuickRef(name, "REF · TREE");
    }
  }

  function nodeAction(nodeId, action) {
    const spec = currentSpec();
    const node = spec.nodes.find((n) => n.id === nodeId);
    if (action === "ref" && node) {
      attachQuickRef(node.file, "REF · NODE #" + nodeId);
    } else if (action === "edit") {
      state.selectedIds = [nodeId];
      syncSelectionDom();
    } else if (action === "filter") {
      bypassFilters();
    } else if (action === "copy" && node) {
      const fb = $("nsGenFeedback");
      if (fb) fb.textContent = "Copied node #" + nodeId + " (" + node.file + ")";
    } else if (action === "save" && node) {
      const fb = $("nsGenFeedback");
      if (fb) fb.textContent = "Saved " + node.file + " to .space/nodes/";
    } else if (action === "delete") {
      const el = $("nsNode-" + nodeId);
      if (el) el.style.opacity = "0.45";
      state.selectedIds = state.selectedIds.filter((id) => id !== nodeId);
      syncSelectionDom();
    }
  }

  function toggleApiDrawer() {
    const d = $("nsApiDrawer");
    if (d) d.classList.toggle("hidden");
  }

  function selectModel(modelId) {
    state.model = modelId;
    const sel = $("nsModelSelect");
    if (sel) sel.value = modelId;
    renderModeAndStatus();
  }

  function updateControl(key, value) {
    state[key] = value;
    renderModeAndStatus();
  }

  async function generateNode() {
    const promptEl = $("nsPromptInput");
    const prompt = promptEl ? promptEl.value.trim() : "";
    const fb = $("nsGenFeedback");
    if (!prompt) {
      if (fb) fb.textContent = "Enter a prompt to generate.";
      return;
    }
    const mode = deriveMode();
    if (fb) fb.textContent = "Dispatching " + mode.short + " via " + state.model + "...";

    const headers = { "Content-Type": "application/json" };
    const nanoKey = $("nsNanogptKeyInput") ? $("nsNanogptKeyInput").value.trim() : "";
    const gemKey = $("nsGeminiKeyInput") ? $("nsGeminiKeyInput").value.trim() : "";
    if (nanoKey) headers["X-NanoGPT-Api-Key"] = nanoKey;
    if (gemKey) headers["X-Gemini-Api-Key"] = gemKey;

    const payload = {
      prompt: prompt,
      modality: state.modality,
      model: state.model,
      provider: state.via,
      selected_node_ids: state.selectedIds.slice(),
      references: state.refs.map((r) => r.name),
      aspect_ratio: state.aspect,
      resolution: state.resolution,
      thinking_level: state.thinking,
      enable_web_search: state.search !== "off",
      filters: Object.assign({}, state.filters)
    };

    try {
      const res = await fetch("/api/nodes/generate", {
        method: "POST",
        headers: headers,
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        const outId = (data && data.node && data.node.id) ? data.node.id : "06";
        if (fb) fb.textContent = "200 OK · Node #" + outId + " (" + mode.short + ") rendered via " + state.model;
        return data;
      }
    } catch (_err) {}

    if (fb) fb.textContent = "Local preview: staged " + mode.short + " node via " + state.model;
    return null;
  }

  function init() {
    const params = typeof window !== "undefined" && window.location && window.location.search
      ? new URLSearchParams(window.location.search)
      : null;
    const pathName = (typeof window !== "undefined" && window.location && window.location.pathname) ? window.location.pathname : "";
    const qMod = params ? params.get("modality") : null;
    const qView = params ? params.get("view") : null;
    if (qMod && SPECS[qMod.toLowerCase()]) state.modality = qMod.toLowerCase();
    if (qView) {
      const lv = qView.toLowerCase();
      if (lv === "gateway") state.view = "library";
      else if (["editor", "timeline", "library"].indexOf(lv) !== -1) state.view = lv;
    } else if (pathName.endsWith("/nodes/timeline")) {
      state.view = "timeline";
    } else if (pathName.endsWith("/nodes/gateway")) {
      state.view = "library";
    }

    applyModality(state.modality, false);
    switchView(state.view);
    bindRefDragEvents();
    updateClock();
    const clkTimer = setInterval(updateClock, 30000);
    if (clkTimer && typeof clkTimer.unref === "function") clkTimer.unref();

    const canvas = $("nsDagCanvas");
    if (canvas) {
      canvas.addEventListener("click", (ev) => {
        if (ev.target === canvas || ev.target.id === "nsDagNodes") clearSelection();
      });
    }

    const promptEl = $("nsPromptInput");
    if (promptEl) {
      promptEl.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter" && !ev.shiftKey) {
          ev.preventDefault();
          generateNode();
        }
      });
    }

    document.addEventListener("keydown", (ev) => {
      const tag = ev.target && ev.target.tagName ? ev.target.tagName.toLowerCase() : "";
      const editing = tag === "textarea" || tag === "input" || tag === "select";
      if ((ev.metaKey || ev.ctrlKey) && ev.key.toLowerCase() === "d") {
        ev.preventDefault();
        bypassFilters();
      } else if (!editing && ev.key.toLowerCase() === "a") {
        drawDagWires();
      } else if (!editing && ev.key.toLowerCase() === "f") {
        drawDagWires();
      }
    });

    if (typeof window !== "undefined") {
      window.addEventListener("resize", drawDagWires);
    }
  }

  window.TinCanNodeStudio = {
    applyModality: applyModality,
    switchView: switchView,
    toggleNode: toggleNode,
    clearSelection: clearSelection,
    toggleFilter: toggleFilter,
    bypassFilters: bypassFilters,
    scrubTimeline: scrubTimeline,
    togglePlayTimeline: togglePlayTimeline,
    removeRef: removeRef,
    attachQuickRef: attachQuickRef,
    selectTreeFile: selectTreeFile,
    nodeAction: nodeAction,
    toggleApiDrawer: toggleApiDrawer,
    selectModel: selectModel,
    updateControl: updateControl,
    generateNode: generateNode,
    autoLayout: drawDagWires,
    getState: function () { return state; }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
</script>"""

    return (
        template.replace("__SPECS_JSON__", specs_json)
        .replace("__FILTERS_JSON__", filters_json)
        .replace("__MODELS_JSON__", models_json)
        .replace("__SPARKLINES_JSON__", sparklines_json)
        .replace("__INIT_MODALITY__", _safe_json(initial_modality))
        .replace("__INIT_VIEW__", _safe_json(initial_view))
    )


def _render_workspace_markup(active_modality: str, active_view: str) -> str:
    spec = MODALITY_SPECS[active_modality]
    selected_count = sum(1 for n in spec["nodes"] if n.get("selected"))
    _short_mode, mode_pill = _derive_mode_label(selected_count)

    view_buttons = "".join(
        f'<button id="nsViewBtn-{v}" type="button" data-view-btn="{v}" '
        f'class="ns-pill{" is-active" if v == active_view else ""}" '
        f'aria-pressed="{"true" if v == active_view else "false"}" '
        f'onclick="window.TinCanNodeStudio.switchView(\'{v}\')">'
        f'{v.capitalize()}</button>'
        for v in VALID_VIEWS
    )
    modality_buttons = "".join(
        f'<button id="nsModalityBtn-{m}" type="button" data-modality-btn="{m}" '
        f'class="ns-pill{" is-active" if m == active_modality else ""}" '
        f'aria-pressed="{"true" if m == active_modality else "false"}" '
        f'onclick="window.TinCanNodeStudio.applyModality(\'{m}\', true)">'
        f'{"● " if m == active_modality else ""}{m.capitalize()}</button>'
        for m in VALID_MODALITIES
    )

    kpis_html = "".join(
        f'<div><div class="ns-kpi-label">{_html.escape(m["label"])}</div>'
        f'<div class="ns-kpi-val">{_html.escape(m["value"])}</div></div>'
        for m in spec["metrics"]
    )

    cli_preview = (
        f'tincan@studio:{spec["path"]}$ prompt --mode '
        f'{"merge" if selected_count >= 2 else ("edit" if selected_count == 1 else "generate")} '
        f'--via {spec["via"]} --model {spec["default_model"]} '
        f'--aspect {spec["aspect"]} --res {spec["resolution"]} --think {spec["thinking"]} '
        f'--search {spec["search"]}'
    )

    quad_cls = "ns-quad-grid" if active_view == "editor" else "ns-quad-grid hidden"
    tl_cls = "ns-subview" if active_view == "timeline" else "ns-subview hidden"
    lib_cls = "ns-subview" if active_view == "library" else "ns-subview hidden"

    return f"""<div class="ns-terminal-frame" data-ns-modality="{_html.escape(active_modality, quote=True)}">
  <div class="ns-window-bar">
    <span id="nsTopClock" class="ns-clock" data-pinned-clock="true">14:41</span>
    <div class="ns-win-controls" aria-label="Terminal window controls">
      <button type="button" class="ns-win-btn" title="Minimize" aria-label="Minimize" onclick="window.TinCanNodeStudio.clearSelection()">—</button>
      <button type="button" class="ns-win-btn" title="Fit View" aria-label="Maximize" onclick="window.TinCanNodeStudio.autoLayout()">□</button>
      <button type="button" class="ns-win-btn" title="Reset View" aria-label="Close" onclick="window.TinCanNodeStudio.switchView('editor')">×</button>
    </div>
  </div>

  <header class="ns-hero-bar">
    <h1 id="nsHeroTitle" class="ns-hero-title">{_html.escape(spec["hero_title"])}</h1>
    <div class="ns-hero-meta">
      <span id="nsHeaderCwd" class="ns-cwd">{_html.escape(spec["path"])}</span>
      <span aria-hidden="true">·</span>
      <div class="ns-seg-group" role="tablist" aria-label="Node Studio View Switcher">{view_buttons}</div>
      <span aria-hidden="true">·</span>
      <div class="ns-seg-group" role="tablist" aria-label="Node Studio Modality Switcher">{modality_buttons}</div>
    </div>
  </header>

  <main class="ns-grid-wrap">
    <div id="nsQuadGrid" class="{quad_cls}">
      <!-- QUADRANT 1: TOP-LEFT -->
      <section class="ns-quad ns-quad--1" data-quadrant="1" aria-label="Node Graph DAG">
        <div class="ns-quad-head">
          <span id="nsQ1Title" class="ns-sec-title">{_html.escape(spec["q1_title"])}</span>
          <div class="ns-head-tools">
            <button type="button" class="ns-kbd-btn" onclick="window.TinCanNodeStudio.autoLayout()">[A] Auto-Layout</button>
            <button type="button" class="ns-kbd-btn" onclick="window.TinCanNodeStudio.autoLayout()">[F] Fit View</button>
            <button type="button" class="ns-kbd-btn" onclick="window.TinCanNodeStudio.bypassFilters()">[Cmd+D] Bypass Filter</button>
          </div>
        </div>
        <div id="nsDagCanvas" class="ns-dag-canvas">
          <svg id="nsDagWires" class="ns-dag-wires" aria-hidden="true"></svg>
          <div id="nsDagNodes" class="ns-dag-nodes">
            {_render_dag_nodes_html(spec)}
          </div>
        </div>
        <div class="ns-timeline-strip" aria-label="Docked Timeline Strip">
          <span id="nsTlPrefix" class="ns-tl-prefix">{_html.escape(spec["timeline_prefix"])}</span>
          <div id="nsTlStops" class="ns-seg-group">{_render_timeline_strip_html(spec)}</div>
          <button id="nsTimelinePlayBtn" type="button" class="ns-tl-play" aria-label="Play Timeline" onclick="window.TinCanNodeStudio.togglePlayTimeline()">▶</button>
        </div>
      </section>

      <!-- QUADRANT 2: TOP-RIGHT -->
      <section class="ns-quad ns-quad--2" data-quadrant="2" aria-label="NanoGPT and Filter Rack">
        <div class="ns-quad-head">
          <span id="nsQ2Title" class="ns-sec-title">{_html.escape(spec["q2_title"])}</span>
          <span id="nsQ2Endpoint" class="ns-head-tools">{_html.escape(spec["q2_endpoint"])}</span>
        </div>
        <div id="nsKpiGrid" class="ns-kpi-grid">{kpis_html}</div>
        <div id="nsSparkWrap" class="ns-spark-wrap">{_render_sparkline_svg(active_modality)}</div>
        <div id="nsFilterRack" class="ns-filter-rack" aria-label="Filter Rack Toggles">
          {_render_filter_rack_html(active_modality)}
        </div>
        <table class="ns-node-table" aria-label="Node Telemetry Table">
          <thead>
            <tr><th>NODE</th><th>MODE</th><th>FILTER / MODEL</th><th>COST</th><th>STATE</th></tr>
          </thead>
          <tbody id="nsNodeTableBody">
            {_render_node_table_html(spec)}
          </tbody>
        </table>
      </section>

      <!-- QUADRANT 3: BOTTOM-LEFT -->
      <section class="ns-quad ns-quad--3" data-quadrant="3" aria-label="Space Nodes File Tree">
        <div class="ns-quad-head">
          <span id="nsQ3Title" class="ns-sec-title">{_html.escape(spec["tree_header"])}</span>
          <span class="ns-head-tools">.space VFS</span>
        </div>
        <div id="nsTreeList" class="ns-tree-list">
          {_render_tree_html(spec)}
        </div>
        <div id="nsTreeFooter" class="ns-tree-footer">{_html.escape(spec["tree_footer"])}</div>
      </section>

      <!-- QUADRANT 4: BOTTOM-RIGHT -->
      <section class="ns-quad ns-quad--4" data-quadrant="4" aria-label="Prompt Island">
        <div class="ns-quad-head">
          <div class="ns-pi-head-pills">
            <span class="ns-sec-title">PROMPT ISLAND</span>
            <span id="nsModePill" class="ns-mode-pill">{_html.escape(mode_pill)}</span>
            <button id="nsConvPill" type="button" class="ns-conv-pill" onclick="this.classList.toggle('is-active')">In Conversation ×</button>
          </div>
          <div class="ns-pi-head-pills">
            <select id="nsModelSelect" class="ns-model-select" aria-label="Model Selector" onchange="window.TinCanNodeStudio.selectModel(this.value)">
              {_render_model_options_html(spec["default_model"])}
            </select>
            <button id="nsApiStatusBtn" type="button" class="ns-green-status" onclick="window.TinCanNodeStudio.toggleApiDrawer()">● {_html.escape(spec["api_label"])}</button>
          </div>
        </div>

        <div id="nsApiDrawer" class="ns-api-drawer hidden" aria-label="API Key Configuration">
          <div class="ns-api-field">
            <label for="nsNanogptKeyInput">X-NanoGPT-Api-Key</label>
            <input id="nsNanogptKeyInput" type="password" placeholder="Synced w/ TinCan Token Vault (optional override)" autocomplete="off">
          </div>
          <div class="ns-api-field">
            <label for="nsGeminiKeyInput">X-Gemini-Api-Key</label>
            <input id="nsGeminiKeyInput" type="password" placeholder="Optional Gemini client override" autocomplete="off">
          </div>
        </div>

        <div id="nsRefsRow" class="ns-refs-row" aria-label="Drag-Ordered References">
          {_render_refs_html(spec)}
        </div>

        <div id="nsCliPreview" class="ns-cli-preview">{_html.escape(cli_preview)}</div>
        <textarea id="nsPromptInput" class="ns-prompt-box" aria-label="Prompt Island input">{_html.escape(spec["prompt"])}</textarea>

        <div class="ns-pi-controls">
          <div class="ns-pi-selects">
            <select id="nsAspectSelect" class="ns-ctrl-select" aria-label="Aspect Ratio" onchange="window.TinCanNodeStudio.updateControl('aspect', this.value)">
              <option value="21:9" selected>ASPECT 21:9</option>
              <option value="16:9">ASPECT 16:9</option>
              <option value="1:1">ASPECT 1:1</option>
              <option value="9:16">ASPECT 9:16</option>
              <option value="1:4">ASPECT 1:4</option>
              <option value="4:1">ASPECT 4:1</option>
              <option value="1:8">ASPECT 1:8</option>
              <option value="8:1">ASPECT 8:1</option>
            </select>
            <select id="nsResSelect" class="ns-ctrl-select" aria-label="Resolution" onchange="window.TinCanNodeStudio.updateControl('resolution', this.value)">
              <option value="4K" selected>RES 4K</option>
              <option value="2K">RES 2K</option>
              <option value="1K">RES 1K</option>
              <option value="512">RES 512</option>
            </select>
            <select id="nsThinkSelect" class="ns-ctrl-select" aria-label="Thinking Level" onchange="window.TinCanNodeStudio.updateControl('thinking', this.value)">
              <option value="high" selected>THINK HIGH</option>
              <option value="medium">THINK MEDIUM</option>
              <option value="minimal">THINK MINIMAL</option>
            </select>
            <select id="nsSearchSelect" class="ns-ctrl-select" aria-label="Search Grounding" onchange="window.TinCanNodeStudio.updateControl('search', this.value)">
              <option value="web+img" selected>SEARCH WEB+IMG</option>
              <option value="web">SEARCH WEB</option>
              <option value="off">SEARCH OFF</option>
            </select>
            <select id="nsViaSelect" class="ns-ctrl-select" aria-label="Provider Routing" onchange="window.TinCanNodeStudio.updateControl('via', this.value)">
              <option value="auto" selected>VIA AUTO (NANOGPT)</option>
              <option value="nanogpt">VIA NANOGPT</option>
              <option value="gemini">VIA GEMINI</option>
              <option value="local">VIA LOCAL</option>
            </select>
          </div>
          <button id="nsGenerateBtn" type="button" class="ns-gen-btn" onclick="window.TinCanNodeStudio.generateNode()">{_html.escape(spec["cta_label"])}</button>
        </div>
        <div id="nsGenFeedback" class="ns-gen-feedback" role="status" aria-live="polite"></div>
      </section>
    </div>

    <div id="nsTimelineSubview" class="{tl_cls}">
      {_render_timeline_view_html(spec)}
    </div>

    <div id="nsLibrarySubview" class="{lib_cls}">
      {_render_library_view_html()}
    </div>
  </main>

  <footer class="ns-status-bar">
    <div id="nsBottomStatusLeft" class="ns-status-left">
      <span>main ↑1 ↓0</span>
      <span class="ns-status-sep">|</span>
      <span>{_html.escape(spec["path"])}</span>
      <span class="ns-status-sep">|</span>
      <span>{_html.escape(spec["status_mode"])} ({len(spec["refs"])}/14 refs)</span>
      <span class="ns-status-sep">|</span>
      <span>{_html.escape(spec["status_model"])}</span>
    </div>
    <div class="ns-status-right">
      <span>zsh</span>
      <span class="ns-status-sep">|</span>
      <span>120×34</span>
      <span class="ns-status-sep">|</span>
      <span>UTF-8</span>
    </div>
  </footer>
</div>"""


def render_node_studio_html(active_modality: str = "image", active_view: str = "editor") -> str:
    """Render the standalone full-page Aeonik Celadon 4-Quadrant Node Studio HTML5 document."""
    modality = _normalize_modality(active_modality)
    view = _normalize_view(active_view)
    spec = MODALITY_SPECS[modality]
    workspace = _render_workspace_markup(modality, view)
    css_block = _node_studio_css()
    js_block = _node_studio_js(modality, view)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_html.escape(spec["hero_title"])} · TinCan Aeonik Terminal</title>
  <link rel="preload" href="/assets/fonts/inter-latin-wght.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="/assets/fonts/jetbrains-mono-latin-wght.woff2" as="font" type="font/woff2" crossorigin>
  <style id="nsFonts">
    @font-face {{ font-family: "Inter"; font-style: normal; font-weight: 100 900; font-display: swap;
      src: url("/assets/fonts/inter-latin-wght.woff2") format("woff2"); }}
    @font-face {{ font-family: "JetBrains Mono"; font-style: normal; font-weight: 100 800; font-display: swap;
      src: url("/assets/fonts/jetbrains-mono-latin-wght.woff2") format("woff2"); }}
    html, body {{ margin: 0; padding: 0; background: #ecf1e6; color: #111111; }}
  </style>
  {css_block}
</head>
<body class="ns-shell">
  <div class="ns-page-wrap">
    {workspace}
  </div>
  {js_block}
</body>
</html>"""


def render_node_studio_window_html() -> str:
    """Render the embeddable ``#win-nodes`` Mesh OS window for Node Studio."""
    workspace = _render_workspace_markup("image", "editor")
    css_block = _node_studio_css()
    js_block = _node_studio_js("image", "editor")
    return (
        '<div id="win-nodes" class="mesh-window w-[1180px] max-w-full hidden tc-ns-host" '
        'data-zen-window="true" data-window-id="win-nodes" style="top: 56px; left: 88px; z-index: 38;">\n'
        '      <!--TC_TITLEBAR {"id": "win-nodes", "title": "Node Studio · Prompt Island, Timeline & Filter Graph", "badge": "NANOGPT + GEMINI"}-->\n'
        f"{css_block}\n"
        '      <div class="window-body ns-body aeonik-scope" data-ns-root="true">\n'
        f"{workspace}\n"
        "      </div>\n"
        f"{js_block}\n"
        "    </div>"
    )


__all__ = [
    "AEONIK_PALETTE",
    "FILTER_RACK_SPECS",
    "MODALITY_SPECS",
    "MODEL_OPTIONS",
    "VALID_MODALITIES",
    "VALID_VIEWS",
    "render_node_studio_html",
    "render_node_studio_window_html",
]
