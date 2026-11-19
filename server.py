#!/usr/bin/env python3
import difflib
import gzip
import hashlib
import hmac
import html as _html_mod
import importlib
import inspect
import io
import json
import math
import re
from http.cookies import SimpleCookie
import os
import secrets
import struct
import subprocess
import tarfile
import threading
import base64
import uuid
import time
import sqlite3
import sys
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple
from http.server import ThreadingHTTPServer as HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from iot_federated_agent_memory.scale import IoTFederatedMemoryScale
from iot_federated_agent_memory.webrtc_relay import WebRTCSignalingRelay
from iot_federated_agent_memory.ai_gateway import DynamicAIGatewayRouter, filter_gateway_models
from iot_federated_agent_memory.ai_gateway_telemetry import collect_gateway_telemetry, estimate_preflight
from iot_federated_agent_memory.token_ledger import build_token_summary
from iot_federated_agent_memory.space_notes import EditPlanError, SpaceNotesEditor
from iot_federated_agent_memory.tincan_relay import TinCanBlindRelay
from iot_federated_agent_memory.video_playlist import RelayVideoPlaylist
from iot_federated_agent_memory.mesh_os_engine import TinCanMeshOSEngine
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI
from iot_federated_agent_memory.account_registry import (
    EMAIL_EXISTS_MESSAGE,
    ArenaBillingError,
    EmailAlreadyRegisteredError,
    PeerAccountRegistry,
)
from iot_federated_agent_memory.passkey_auth import (
    PasskeyAuthService,
    PasskeyError,
    resolve_relying_party,
)
from iot_federated_agent_memory.thread_fs import (
    ANONYMOUS_PEER_ID,
    ThreadFsError,
    sanitize_peer_id,
    start_or_continue_thread,
)
from iot_federated_agent_memory.thread_api import (
    api_list_files,
    api_read_file,
    api_write_file,
    set_account_registry as set_thread_account_registry,
)
from iot_federated_agent_memory.sponsor_ads import SponsorAdManager
from iot_federated_agent_memory.arena_context import ArenaContextRegistry, ContextStoreError
from iot_federated_agent_memory.arena_context_api import ArenaContextAPI
from iot_federated_agent_memory import drive_mirror
from iot_federated_agent_memory.file_inspector import guess_mime_type, inspect_binary_file
from iot_federated_agent_memory.pages_proxy import (
    list_space_page_entrypoints,
    proxy_localhost_port,
    serve_space_pages,
)
from iot_federated_agent_memory.cyberspace_board import CyberspaceBoardEngine
from iot_federated_agent_memory.crdt_mesh import CRDTMeshGossipSync, CRDTDeltaMessage
from iot_federated_agent_memory.edge_telemetry import (
    EdgeTelemetryIngestor,
    HMACVendingMachine,
    MQTTTelemetryClientAdapter,
    CreditExhaustionError,
)
from dataclasses import asdict

# Car Head Unit UI & iOS Preview Integration
try:
    from iot_federated_agent_memory.car_ui import render_car_headunit_html, CAR_MODES
except Exception:
    render_car_headunit_html = None
    CAR_MODES = ()

try:
    from iot_federated_agent_memory import ios_preview
except Exception:
    ios_preview = None

try:
    from iot_federated_agent_memory.designs_gallery import render_designs_gallery_html
except Exception:
    render_designs_gallery_html = None

try:
    from iot_federated_agent_memory import node_studio_ui as _node_studio_ui
except Exception:
    _node_studio_ui = None

try:
    from iot_federated_agent_memory import node_studio_engine as _node_studio_engine
except Exception:
    _node_studio_engine = None

_VALID_NODE_MODALITIES = ("image", "text", "video", "audio", "atlas", "3d")
_VALID_NODE_VIEWS = ("editor", "timeline", "gateway")


def _get_node_studio_ui():
    if _node_studio_ui is not None:
        return _node_studio_ui
    try:
        return importlib.import_module("iot_federated_agent_memory.node_studio_ui")
    except Exception:
        return None


def _get_node_studio_engine():
    if _node_studio_engine is not None:
        return _node_studio_engine
    try:
        return importlib.import_module("iot_federated_agent_memory.node_studio_engine")
    except Exception:
        return None


def _normalize_node_modality(raw: Optional[str]) -> str:
    val = (raw or "image").strip().lower()
    return val if val in _VALID_NODE_MODALITIES else "image"


def _normalize_node_view(raw: Optional[str]) -> str:
    val = (raw or "editor").strip().lower()
    return val if val in _VALID_NODE_VIEWS else "editor"


def _render_node_studio_page(modality: str = "image", view: str = "editor") -> str:
    active_modality = _normalize_node_modality(modality)
    active_view = _normalize_node_view(view)
    ui_mod = _get_node_studio_ui()
    if ui_mod is not None and hasattr(ui_mod, "render_node_studio_html"):
        fn = ui_mod.render_node_studio_html
        try:
            params = inspect.signature(fn).parameters
        except (TypeError, ValueError):
            params = {}
        kwargs: Dict[str, Any] = {}
        if "active_modality" in params:
            kwargs["active_modality"] = active_modality
        elif "modality" in params:
            kwargs["modality"] = active_modality
        if "active_view" in params:
            kwargs["active_view"] = active_view
        elif "view" in params:
            kwargs["view"] = active_view
        if kwargs:
            return fn(**kwargs)
        if not params:
            return fn()
        return fn(active_modality)

    mod_title = _html_mod.escape(active_modality.title())
    view_title = _html_mod.escape(active_view.title())
    return (
        "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<title>Nano Banana Gemini Node Studio · {mod_title}</title>"
        "<style>body{background:#ecf1e6 radial-gradient(#11111126 1px,transparent 1px);background-size:24px 24px;"
        "color:#111111;font-family:Inter,-apple-system,sans-serif;margin:0;padding:24px;}"
        ".card{background:#f4f8f0;border:1px solid #111111;border-radius:16px;padding:16px;max-width:920px;margin:0 auto;}</style></head>"
        f"<body data-modality=\"{active_modality}\" data-view=\"{active_view}\">"
        f"<div class=\"card\"><h1>Node Studio · {mod_title} (Nano Banana 2.1)</h1>"
        f"<p>View: {view_title} · Lumina Library · Gateway: NANOGPT + GEMINI</p>"
        "<p>Mode: GENERATE / EDIT / MERGE · API: /api/nodes/generate · /api/generate</p></div></body></html>"
    )


def _node_studio_health(headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    eng = _get_node_studio_engine()
    if eng is not None and hasattr(eng, "get_node_studio_health"):
        return dict(eng.get_node_studio_health(headers=headers, env=os.environ))
    hdrs = {k.lower(): v for k, v in (headers or {}).items()}
    has_gemini = bool(os.environ.get("GEMINI_API_KEY") or hdrs.get("x-gemini-api-key"))
    has_nanogpt = bool(os.environ.get("NANOGPT_API_KEY") or hdrs.get("x-nanogpt-api-key"))
    return {
        "ok": True,
        "hasServerKey": has_gemini or has_nanogpt,
        "hasGeminiKey": has_gemini,
        "hasNanogptKey": has_nanogpt,
        "modalities": ["text", "image", "video"],
        "models": {},
        "fallback": True,
    }


def _node_studio_state(modality: str = "image") -> Dict[str, Any]:
    active_modality = _normalize_node_modality(modality)
    eng = _get_node_studio_engine()
    if eng is not None and hasattr(eng, "get_default_studio_state"):
        state = dict(eng.get_default_studio_state(modality=active_modality))
        state.setdefault("ok", True)
        state.setdefault("modality", active_modality)
        return state
    return {
        "ok": True,
        "modality": active_modality,
        "nodes": [],
        "edges": [],
        "filters": {},
        "timeline": [],
        "tree": [],
        "fallback": True,
    }


def _node_studio_generate(
    payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None
) -> Tuple[int, Dict[str, Any]]:
    if not isinstance(payload, dict):
        return 400, {"ok": False, "error": "Payload must be a JSON object"}
    eng = _get_node_studio_engine()
    if eng is not None and hasattr(eng, "handle_node_studio_generate"):
        try:
            res = eng.handle_node_studio_generate(payload, headers=headers, env=os.environ)
            out = dict(res) if isinstance(res, dict) else {"result": res}
            out.setdefault("ok", True)
            raw_code = out.get("statusCode")
            status_code = raw_code if isinstance(raw_code, int) else (400 if out.get("ok") is False else 200)
            return status_code, out
        except ValueError as ve:
            return 400, {"ok": False, "error": str(ve)}

    prompt = (payload.get("prompt") or "").strip()
    if not prompt:
        return 400, {"ok": False, "error": "Prompt is required"}
    modality = _normalize_node_modality(payload.get("modality"))
    selected = payload.get("selected_node_ids") or []
    if len(selected) >= 2:
        mode = "MERGE"
    elif len(selected) == 1:
        mode = "EDIT"
    else:
        mode = "GENERATE"
    node_id = f"node-{uuid.uuid4().hex[:6]}"
    return 200, {
        "ok": True,
        "mode": mode,
        "modality": modality,
        "node": {
            "id": node_id,
            "modality": modality,
            "prompt": prompt,
            "mode": mode,
            "parents": list(selected),
            "filters": dict(payload.get("filters") or {}),
        },
        "edges": [{"from": p, "to": node_id} for p in selected],
        "timeline": [{"timecode": "00:00", "node_id": node_id, "modality": modality}],
        "fallback": True,
    }


def _node_studio_filter(payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    if not isinstance(payload, dict):
        return 400, {"ok": False, "error": "Payload must be a JSON object"}
    eng = _get_node_studio_engine()
    if eng is not None and hasattr(eng, "handle_node_studio_filter"):
        try:
            res = eng.handle_node_studio_filter(payload)
            out = dict(res) if isinstance(res, dict) else {"result": res}
            out.setdefault("ok", True)
            raw_code = out.get("statusCode")
            status_code = raw_code if isinstance(raw_code, int) else (400 if out.get("ok") is False else 200)
            return status_code, out
        except ValueError as ve:
            return 400, {"ok": False, "error": str(ve)}

    node_id = (payload.get("node_id") or "").strip()
    filters = payload.get("filters") if isinstance(payload.get("filters"), dict) else {}
    modality = _normalize_node_modality(payload.get("modality"))
    if eng is not None and hasattr(eng, "apply_node_filters"):
        try:
            state = _node_studio_state(modality)
            nodes = payload.get("nodes") if isinstance(payload.get("nodes"), list) else state.get("nodes", [])
            edges = payload.get("edges") if isinstance(payload.get("edges"), list) else state.get("edges", [])
            fn = eng.apply_node_filters
            try:
                params = list(inspect.signature(fn).parameters.keys())
            except (TypeError, ValueError):
                params = []
            if "nodes" in params and "node_id" in params:
                updated = fn(nodes=nodes, node_id=node_id, filters=filters)
            elif len(params) >= 2 and params[0] == "node":
                target = next((n for n in nodes if isinstance(n, dict) and n.get("id") == node_id), {"id": node_id, "filters": {}})
                updated = fn(target, filters)
            else:
                updated = fn(node_id or "01", filters)
            timeline = state.get("timeline", [])
            if hasattr(eng, "build_timeline_sequence"):
                try:
                    timeline = eng.build_timeline_sequence(nodes, edges, target_node_id=node_id or None)
                except Exception:
                    pass
            return 200, {
                "ok": True,
                "node_id": node_id,
                "modality": modality,
                "filters": filters,
                "updated": updated,
                "timeline": timeline,
            }
        except ValueError as ve:
            return 400, {"ok": False, "error": str(ve)}

    return 200, {
        "ok": True,
        "node_id": node_id,
        "modality": modality,
        "filters": filters,
        "timeline": [],
        "fallback": True,
    }


# ---------------------------------------------------------------------------
# World Labs Atlas v2, Omni-Audio & Unified Slash-Command Router Helpers
# ---------------------------------------------------------------------------

_ATLAS_CANONICAL_TASKS: Tuple[str, ...] = (
    "atlasTextToImage",
    "images2PosedRGBD",
    "atlasGenerate",
    "atlasChisel",
    "posedImages2Splats",
    "splats2Mesh",
)

_ATLAS_SUBCMD_TO_TASK: Dict[str, str] = {
    "pose": "images2PosedRGBD",
    "rgbd": "images2PosedRGBD",
    "generate": "atlasGenerate",
    "flythrough": "atlasGenerate",
    "splats": "posedImages2Splats",
    "splat": "posedImages2Splats",
    "mesh": "splats2Mesh",
    "chisel": "atlasChisel",
    "text2img": "atlasTextToImage",
    "text-to-image": "atlasTextToImage",
}


def _build_minimal_wav_bytes(duration_ms: int = 120) -> bytes:
    """Build a valid minimal 16-bit mono PCM WAV payload for deterministic offline audio fallback."""
    sample_rate = 16000
    num_samples = max(160, int(sample_rate * (duration_ms / 1000.0)))
    pcm_bytes = b"\x00\x00" * num_samples
    data_size = len(pcm_bytes)
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        1,
        sample_rate,
        sample_rate * 2,
        2,
        16,
        b"data",
        data_size,
    )
    return header + pcm_bytes


def _atlas_health(ai_router: Any = None) -> Dict[str, Any]:
    rtr = ai_router or globals().get("router")
    if rtr is not None and hasattr(rtr, "check_atlas_health"):
        res = dict(rtr.check_atlas_health())
        res.setdefault("ok", True)
        return res
    wlt_key = (
        getattr(rtr, "worldlabs_key", None)
        or os.environ.get("WLT_API_KEY")
        or os.environ.get("WORLDLABS_API_KEY")
        or ""
    )
    base_url = getattr(rtr, "ATLAS_BASE_URL", None) or os.environ.get(
        "WLT_API_BASE_URL", "https://api.atlas.worldlabs.ai/api/v2"
    )
    tasks = list(getattr(rtr, "ATLAS_TASKS", _ATLAS_CANONICAL_TASKS))
    return {
        "ok": True,
        "status": "ok",
        "service": "worldlabs-atlas-v2",
        "base_url": base_url,
        "key_configured": bool(wlt_key),
        "tasks": tasks,
        "credit_usd_rate": 0.001,
    }


def _atlas_upload_asset(data: Dict[str, Any], ai_router: Any = None) -> Tuple[int, Dict[str, Any]]:
    if not isinstance(data, dict):
        return 400, {"ok": False, "error": "Payload must be a JSON object"}
    rtr = ai_router or globals().get("router")
    vfs_path = (data.get("vfs_path") or data.get("path") or "").strip()
    data_b64 = (data.get("data_b64") or data.get("bytes_b64") or data.get("content_b64") or "").strip()
    scope = (data.get("scope") or "user").strip()
    owner_id = (data.get("owner_id") or data.get("peer_id") or "default").strip()

    file_bytes: Optional[bytes] = None
    mime_type = (data.get("mime_type") or "").strip()
    filename = (data.get("filename") or "").strip()

    if data_b64:
        try:
            file_bytes = base64.b64decode(data_b64)
        except Exception as err:
            return 400, {"ok": False, "error": f"Invalid base64 payload: {err}"}
        if not filename:
            filename = os.path.basename(vfs_path) if vfs_path else "input.jpg"
    elif vfs_path:
        sm = _get_space_manager()
        sp = sm.get_or_create_space(scope, owner_id)
        try:
            rec = sp.read_file(vfs_path, as_text=False)
        except FileNotFoundError as err:
            return 404, {"ok": False, "error": str(err)}
        file_bytes = base64.b64decode(rec.get("content_b64") or "")
        if not mime_type:
            mime_type = str(rec.get("mime_type") or "")
        if not filename:
            filename = os.path.basename(vfs_path) or "input.jpg"
    else:
        return 400, {"ok": False, "error": "Provide 'vfs_path' or 'data_b64'"}

    if not mime_type:
        mime_type = guess_mime_type(filename or "input.jpg") or "image/jpeg"

    if rtr is not None and hasattr(rtr, "upload_atlas_asset"):
        res = dict(rtr.upload_atlas_asset(file_bytes, mime_type=mime_type, filename=filename))
    else:
        sha = hashlib.sha256(file_bytes).hexdigest()[:16]
        res = {
            "ok": True,
            "asset_id": f"asset_{sha}",
            "id": f"asset_{sha}",
            "filename": filename,
            "mime_type": mime_type,
            "size_bytes": len(file_bytes),
            "simulated": True,
        }
    res.setdefault("ok", True)
    res.setdefault("filename", filename)
    res.setdefault("mime_type", mime_type)
    res.setdefault("size_bytes", len(file_bytes))
    if vfs_path:
        res["vfs_path"] = vfs_path
    return (200 if res.get("ok") else 400), res


def _atlas_run_task(
    data: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
    ai_router: Any = None,
) -> Tuple[int, Dict[str, Any]]:
    if not isinstance(data, dict):
        return 400, {"ok": False, "error": "Payload must be a JSON object"}
    rtr = ai_router or globals().get("router")
    raw_task = (data.get("task") or data.get("task_name") or "").strip()
    if not raw_task:
        return 400, {"ok": False, "error": "Missing 'task'"}

    canonical_task = _ATLAS_SUBCMD_TO_TASK.get(raw_task.lower(), raw_task)
    allowed_tasks = tuple(getattr(rtr, "ATLAS_TASKS", _ATLAS_CANONICAL_TASKS))
    if canonical_task not in allowed_tasks:
        return 400, {
            "ok": False,
            "error": f"Unsupported Atlas v2 task '{raw_task}'. Must be one of {list(allowed_tasks)}",
        }

    req_body = data.get("request_body")
    if not isinstance(req_body, dict):
        req_body = data.get("request") if isinstance(data.get("request"), dict) else {}
        req_body = dict(req_body)
        for k in ("prompt", "asset_id", "images", "frames", "splat_asset_id", "views", "resolution", "fps"):
            if k in data and k not in req_body:
                req_body[k] = data[k]

    hdrs = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
    idem_key = (
        data.get("idempotency_key")
        or hdrs.get("idempotency-key")
        or str(uuid.uuid4())
    )

    if rtr is not None and hasattr(rtr, "submit_atlas_task"):
        try:
            res = dict(rtr.submit_atlas_task(canonical_task, req_body, idempotency_key=idem_key))
        except ValueError as ve:
            return 400, {"ok": False, "error": str(ve)}
    else:
        digest = hashlib.sha256(f"{canonical_task}:{idem_key}:{json.dumps(req_body, sort_keys=True)}".encode("utf-8")).hexdigest()[:12]
        op_id = f"op_atlas_{digest}"
        res = {
            "ok": True,
            "id": op_id,
            "operation_id": op_id,
            "task": canonical_task,
            "idempotency_key": idem_key,
            "done": True,
            "simulated": True,
            "response": {
                "task": canonical_task,
                "frames": [
                    {
                        "index": 0,
                        "imageAssetId": f"asset_img_{digest[:8]}",
                        "depthAssetId": f"asset_depth_{digest[:8]}",
                        "confidenceAssetId": f"asset_conf_{digest[:8]}",
                        "intrinsics": {"fx": 886.81, "fy": 886.81, "cx": 640.0, "cy": 360.0},
                        "extrinsics": {"coordinateSystem": "RUB", "centroidWorld": [0.0, 1.15, -2.4]},
                    }
                ],
                "splatAsset": {"id": f"asset_spz_{digest[:8]}", "numSplats": 2000000, "format": "spz"},
                "meshAsset": (
                    {"id": f"asset_glb_{digest[:8]}", "format": "glb"}
                    if canonical_task == "splats2Mesh"
                    else None
                ),
            },
            "metadata": {
                "task": canonical_task,
                "credits_used": 500,
                "cost_usd": 0.50,
            },
        }
        if rtr is not None:
            ops = getattr(rtr, "atlas_operations", None)
            if isinstance(ops, dict):
                ops[op_id] = res
            else:
                setattr(rtr, "atlas_operations", {op_id: res})

    status_code = int(res.get("status_code") or (200 if res.get("ok", True) else 400))
    return status_code, res


def _atlas_operation_status(operation_id: str, ai_router: Any = None) -> Tuple[int, Dict[str, Any]]:
    op_id = (operation_id or "").strip()
    if not op_id:
        return 400, {"ok": False, "error": "Missing 'operation_id'"}
    rtr = ai_router or globals().get("router")
    if rtr is not None and hasattr(rtr, "get_atlas_operation"):
        res = dict(rtr.get_atlas_operation(op_id))
    else:
        ops = getattr(rtr, "atlas_operations", {}) if rtr is not None else {}
        if isinstance(ops, dict) and op_id in ops:
            res = dict(ops[op_id])
        else:
            res = {
                "ok": True,
                "id": op_id,
                "operation_id": op_id,
                "done": True,
                "simulated": True,
                "response": {
                    "frames": [{"index": 0, "intrinsics": {"fx": 886.81, "fy": 886.81, "cx": 640.0, "cy": 360.0}}],
                    "splatAsset": {"id": f"asset_{op_id[-8:]}", "numSplats": 2000000, "format": "spz"},
                },
            }
    status_code = int(res.get("status_code") or (200 if res.get("ok", True) else 400))
    return status_code, res


def _atlas_download_operation(data: Dict[str, Any], ai_router: Any = None) -> Tuple[int, Dict[str, Any]]:
    if not isinstance(data, dict):
        return 400, {"ok": False, "error": "Payload must be a JSON object"}
    op_id = (data.get("operation_id") or data.get("id") or data.get("op_id") or "").strip()
    if not op_id:
        return 400, {"ok": False, "error": "Missing 'operation_id'"}
    scope = (data.get("scope") or "user").strip()
    owner_id = (data.get("owner_id") or data.get("peer_id") or "default").strip()
    target_dir = (data.get("target_dir") or "/worlds").strip() or "/worlds"
    author = (data.get("author") or data.get("peer_id") or owner_id or "atlas").strip()

    sm = _get_space_manager()
    target_vfs = sm.get_or_create_space(scope, owner_id)
    rtr = ai_router or globals().get("router")

    if rtr is not None and hasattr(rtr, "download_atlas_operation_to_vfs"):
        dl_res = dict(
            rtr.download_atlas_operation_to_vfs(
                op_id,
                target_vfs,
                target_dir=target_dir,
                author=author,
            )
        )
    else:
        from iot_federated_agent_memory.agent_space import generate_minimal_glb_bytes

        _, op_data = _atlas_operation_status(op_id, ai_router=rtr)
        short_id = re.sub(r"[^a-zA-Z0-9_-]", "", op_id.replace("op_atlas_", ""))[:12] or "world"
        world_dir = "/" + target_dir.strip("/") + f"/{short_id}"
        saved_files: List[str] = []

        op_json_path = f"{world_dir}/operation.json"
        target_vfs.write_file(op_json_path, json.dumps(op_data, indent=2), mime_type="application/json", updated_by=author)
        saved_files.append(op_json_path)

        resp_obj = op_data.get("response") if isinstance(op_data.get("response"), dict) else {}
        task_name = str(op_data.get("task") or resp_obj.get("task") or "")

        img_path = f"{world_dir}/frames_0_image.jpg"
        target_vfs.write_file(img_path, b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9", mime_type="image/jpeg", updated_by=author)
        saved_files.append(img_path)

        depth_path = f"{world_dir}/frames_0_depth.exr"
        target_vfs.write_file(depth_path, b"v/2\x01\x02\x00\x00\x00EXR_LINEAR_DEPTH", mime_type="image/x-exr", updated_by=author)
        saved_files.append(depth_path)

        conf_path = f"{world_dir}/frames_0_confidence.png"
        target_vfs.write_file(
            conf_path,
            base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="),
            mime_type="image/png",
            updated_by=author,
        )
        saved_files.append(conf_path)

        splat_path = f"{world_dir}/refinedSplats_2000000.spz"
        target_vfs.write_file(splat_path, b"SPZ\x02WORLDLABS_GAUSSIAN_SPLATS_2M", mime_type="application/octet-stream", updated_by=author)
        saved_files.append(splat_path)

        if resp_obj.get("meshAsset") or task_name == "splats2Mesh" or data.get("include_mesh"):
            glb_path = f"/models3d/atlas_{short_id}.glb"
            target_vfs.write_file(glb_path, generate_minimal_glb_bytes(f"atlas_{short_id}"), mime_type="model/gltf-binary", updated_by=author)
            saved_files.append(glb_path)

        dl_res = {
            "ok": True,
            "operation_id": op_id,
            "saved_files": saved_files,
        }

    files_b64: Dict[str, str] = {}
    for fpath in dl_res.get("saved_files") or []:
        try:
            frec = target_vfs.read_file(fpath, as_text=False)
            sz = int(frec.get("size_bytes") or 0)
            if frec.get("content_b64") and sz <= 2 * 1024 * 1024:
                files_b64[fpath] = frec["content_b64"]
        except Exception:
            pass

    dl_res.setdefault("ok", True)
    dl_res["operation_id"] = op_id
    dl_res["scope"] = scope
    dl_res["owner_id"] = owner_id
    if dl_res.get("spz_path"):
        dl_res["spz_raw_url"] = (
            f"/api/space/file?raw=1&scope={urllib.parse.quote(scope)}"
            f"&owner_id={urllib.parse.quote(owner_id)}"
            f"&path={urllib.parse.quote(str(dl_res['spz_path']))}"
        )
    dl_res["files_b64"] = files_b64
    return (200 if dl_res.get("ok") else 400), dl_res


def _audio_generate_and_save(data: Dict[str, Any], ai_router: Any = None) -> Tuple[int, Dict[str, Any]]:
    if not isinstance(data, dict):
        return 400, {"ok": False, "error": "Payload must be a JSON object"}
    from iot_federated_agent_memory.agent_space import _slug_from_prompt, _unique_space_path

    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return 400, {"ok": False, "error": "Missing 'prompt'"}
    kind = (data.get("kind") or "music").strip().lower()
    if kind not in ("tts", "music", "sfx"):
        kind = "music"
    model = data.get("model")
    voice = data.get("voice")
    scope = (data.get("scope") or "user").strip()
    owner_id = (data.get("owner_id") or data.get("peer_id") or "default").strip()
    peer_id = (data.get("peer_id") or owner_id or "peer").strip()
    save_path = (data.get("save_path") or "").strip()

    rtr = ai_router or globals().get("router")
    if rtr is not None and hasattr(rtr, "generate_omni_audio"):
        res = dict(rtr.generate_omni_audio(prompt, kind=kind, model=model, voice=voice))
    else:
        default_models = {
            "tts": "elevenlabs/eleven-v4",
            "music": "google/lyria-3.5",
            "sfx": "elevenlabs/sound-effects/v3",
        }
        resolved_model = model or default_models.get(kind, "google/lyria-3.5")
        wav_bytes = _build_minimal_wav_bytes()
        res = {
            "ok": True,
            "kind": kind,
            "model": resolved_model,
            "prompt": prompt,
            "audio_bytes_b64": base64.b64encode(wav_bytes).decode("ascii"),
            "mime_type": "audio/wav",
            "sparkline": "│┃│┃┃│┃┃",
            "lufs": -14.0,
        }

    wav_b64 = res.get("audio_bytes_b64") or ""
    if not wav_b64:
        wav_bytes = _build_minimal_wav_bytes()
        wav_b64 = base64.b64encode(wav_bytes).decode("ascii")
        res["audio_bytes_b64"] = wav_b64
    else:
        wav_bytes = base64.b64decode(wav_b64)

    sm = _get_space_manager()
    sp = sm.get_or_create_space(scope, owner_id)
    slug = _slug_from_prompt(prompt, default=f"{kind}_track")
    sp_path = save_path or _unique_space_path(sp, "/audio", f"{kind}_{slug}", ".wav")
    sp.write_file(sp_path, wav_bytes, mime_type=res.get("mime_type") or "audio/wav", updated_by=peer_id)

    res["ok"] = True
    res["path"] = sp_path
    res["size_bytes"] = len(wav_bytes)
    res["saved_to_space"] = {"scope": scope, "owner_id": owner_id, "path": sp_path}
    return 200, res


def _fallback_parse_omni_slash_command(raw_input: str) -> Dict[str, Any]:
    """Defensive fallback parser matching node_studio_engine.parse_omni_slash_command contract."""
    text = (raw_input or "").strip()
    is_slash = text.startswith("/")
    tokens = text.split()
    cmd = "image"
    subcmd = ""
    idx = 0
    if is_slash and tokens:
        head = tokens[0].lstrip("/").lower()
        idx = 1
        if head in ("atlas", "image", "video", "audio", "3d", "rodin", "rig", "text", "mux"):
            cmd = "3d" if head == "rodin" else head
        else:
            cmd = "text"

    if cmd == "atlas" and idx < len(tokens) and not tokens[idx].startswith("-"):
        cand = tokens[idx].lower()
        if cand in _ATLAS_SUBCMD_TO_TASK or cand in _ATLAS_CANONICAL_TASKS:
            subcmd = cand
            idx += 1
    elif cmd == "audio" and idx < len(tokens) and not tokens[idx].startswith("-"):
        cand = tokens[idx].lower()
        if cand in ("tts", "music", "sfx"):
            subcmd = cand
            idx += 1

    flags: Dict[str, Any] = {}
    prompt_parts: List[str] = []
    target_path: Optional[str] = None
    while idx < len(tokens):
        tok = tokens[idx]
        if tok.startswith("--"):
            key = tok[2:].lower()
            if key == "mesh":
                flags["mesh"] = True
                idx += 1
            elif idx + 1 < len(tokens) and not tokens[idx + 1].startswith("--"):
                val = tokens[idx + 1]
                if key in ("views", "fps", "seconds"):
                    try:
                        flags[key] = int(val)
                    except ValueError:
                        flags[key] = val
                elif key == "lufs":
                    try:
                        flags[key] = float(val)
                    except ValueError:
                        flags[key] = val
                elif key == "res" and "x" in val.lower():
                    parts = val.lower().split("x", 1)
                    try:
                        flags["res"] = [int(parts[0]), int(parts[1])]
                    except ValueError:
                        flags["res"] = val
                else:
                    flags[key] = val
                idx += 2
            else:
                flags[key] = True
                idx += 1
        else:
            if (tok.startswith("/") or tok.endswith((".glb", ".spz", ".exr", ".png", ".jpg", ".wav", ".mp4"))) and target_path is None:
                target_path = tok
            prompt_parts.append(tok)
            idx += 1

    clean_prompt = " ".join(prompt_parts).strip() or text

    if cmd == "atlas":
        subcmd = subcmd or "splat"
        atlas_task = _ATLAS_SUBCMD_TO_TASK.get(subcmd.lower(), subcmd if subcmd in _ATLAS_CANONICAL_TASKS else "posedImages2Splats")
        modality = "atlas"
        provider = "worldlabs"
        model = str(flags.get("model") or f"worldlabs/{atlas_task}")
        pill_label = f"● /atlas {subcmd}"
    elif cmd == "audio":
        subcmd = subcmd or "music"
        atlas_task = None
        modality = "audio"
        provider = "nanogpt"
        default_aud_models = {
            "tts": "elevenlabs/eleven-v4",
            "music": "google/lyria-3.5",
            "sfx": "elevenlabs/sound-effects/v3",
        }
        model = str(flags.get("model") or default_aud_models.get(subcmd, "google/lyria-3.5"))
        pill_label = f"♪ /audio {subcmd}"
    elif cmd == "3d":
        subcmd = subcmd or "generate"
        atlas_task = "splats2Mesh" if flags.get("model") == "splats2Mesh" else None
        modality = "3d"
        provider = "hyper3d"
        model = str(flags.get("model") or "hyper3d/rodin-v2.5")
        pill_label = "◆ /3d mesh"
    elif cmd == "rig":
        subcmd = subcmd or str(flags.get("anim") or "walk")
        atlas_task = None
        modality = "3d"
        provider = "local" if flags.get("engine") == "local" else "nanogpt"
        model = str(flags.get("engine") or flags.get("model") or "hyper3d/rigging")
        pill_label = f"◆ /rig {subcmd}"
    elif cmd == "video":
        subcmd = subcmd or "generate"
        atlas_task = None
        modality = "video"
        provider = "nanogpt"
        model = str(flags.get("model") or "kling-4.0")
        pill_label = "▶ /video"
    elif cmd == "text":
        subcmd = subcmd or "chat"
        atlas_task = None
        modality = "text"
        provider = "nanogpt"
        model = str(flags.get("model") or "nanogpt/TEE/deepseek-v4.1-flash")
        pill_label = "¶ /text"
    elif cmd == "mux":
        subcmd = subcmd or "master"
        atlas_task = None
        modality = "video"
        provider = "local"
        model = "omni-mux"
        pill_label = "⊕ /mux"
    else:
        subcmd = subcmd or "generate"
        atlas_task = "atlasTextToImage" if flags.get("model") == "atlasTextToImage" else None
        modality = "image"
        provider = "worldlabs" if atlas_task else "gemini"
        model = str(flags.get("model") or "gemini-nano-banana-2.1")
        pill_label = "◼ /image"

    return {
        "is_slash": is_slash,
        "command": cmd,
        "subcommand": subcmd,
        "modality": modality,
        "provider": provider,
        "model": model,
        "atlas_task": atlas_task,
        "flags": flags,
        "target_path": target_path,
        "prompt": clean_prompt,
        "pill_label": pill_label,
    }


def _parse_omni_slash_command(raw_input: str) -> Dict[str, Any]:
    eng = _get_node_studio_engine()
    if eng is not None and hasattr(eng, "parse_omni_slash_command"):
        try:
            parsed = dict(eng.parse_omni_slash_command(raw_input))
            if parsed.get("command") == "rodin":
                parsed["command"] = "3d"
                parsed["modality"] = "3d"
            return parsed
        except Exception:
            pass
    return _fallback_parse_omni_slash_command(raw_input)


def _normalize_posed_frames_for_splats(raw_frames: Any) -> List[Dict[str, Any]]:
    """Normalize images2PosedRGBD / atlasGenerate frames into exact World Labs Atlas v2 posedFrames schema."""
    if not isinstance(raw_frames, list):
        return []
    out: List[Dict[str, Any]] = []
    for f in raw_frames:
        if not isinstance(f, dict):
            continue
        img = f.get("imageAsset") or f.get("image")
        depth = f.get("depth")
        cam = f.get("camera")
        img_asset: Optional[Dict[str, Any]] = None
        if isinstance(img, dict):
            if img.get("assetId"):
                img_asset = {"assetId": str(img["assetId"])}
            elif img.get("url"):
                img_asset = {"url": str(img["url"])}
        depth_asset: Optional[Dict[str, Any]] = None
        if isinstance(depth, dict):
            da = depth.get("depthAsset") if isinstance(depth.get("depthAsset"), dict) else depth
            if isinstance(da, dict):
                if da.get("assetId"):
                    depth_asset = {"assetId": str(da["assetId"])}
                elif da.get("url"):
                    depth_asset = {"url": str(da["url"])}
        if img_asset and depth_asset and isinstance(cam, dict):
            out.append({
                "imageAsset": img_asset,
                "depth": {"depthAsset": depth_asset},
                "camera": cam,
            })
    return out


def _build_orbital_target_cameras(anchor_frame: Dict[str, Any], num_views: int = 6) -> List[Dict[str, Any]]:
    """Compute RUB target cameras orbiting centroidWorld around an anchor posed frame for atlasGenerate."""
    cam = anchor_frame.get("camera") if isinstance(anchor_frame.get("camera"), dict) else {}
    intr = cam.get("intrinsics") if isinstance(cam.get("intrinsics"), dict) else {
        "width": 1280, "height": 720, "fx": 762.31, "fy": 762.31, "cx": 640, "cy": 360,
    }
    extr = cam.get("extrinsics") if isinstance(cam.get("extrinsics"), dict) else {}
    pos0 = extr.get("position") if isinstance(extr.get("position"), list) and len(extr.get("position")) == 3 else [0.0, 1.0, 0.0]
    centroid = anchor_frame.get("centroidWorld") if isinstance(anchor_frame.get("centroidWorld"), list) and len(anchor_frame.get("centroidWorld")) == 3 else [0.0, pos0[1], pos0[2] - 3.0]

    dx = float(pos0[0]) - float(centroid[0])
    dz = float(pos0[2]) - float(centroid[2])
    radius = max(1.2, math.hypot(dx, dz))
    base_angle = math.atan2(dx, dz)
    cam_y = float(pos0[1])

    # Spread orbital angles around the anchor view (-55°..+55° plus elevated angles for solid depth overlap)
    angle_offsets_deg = [-45.0, -22.5, 22.5, 45.0, -30.0, 30.0][:max(2, min(num_views, 8))]
    y_offsets = [0.0, 0.0, 0.0, 0.0, 0.35, 0.35]

    targets: List[Dict[str, Any]] = []
    for idx, deg in enumerate(angle_offsets_deg):
        ang = base_angle + math.radians(deg)
        px = float(centroid[0]) + math.sin(ang) * radius
        pz = float(centroid[2]) + math.cos(ang) * radius
        py = cam_y + (y_offsets[idx] if idx < len(y_offsets) else 0.0)
        # Camera looks from (px, py, pz) toward centroid; in RUB (+X right, +Y up, +Z back),
        # yaw rotates around +Y by `ang`, pitch tilts slightly downward if elevated
        yaw = ang
        pitch = -math.atan2(py - float(centroid[1]), radius) * 0.6
        cy, sy = math.cos(yaw * 0.5), math.sin(yaw * 0.5)
        cp, sp = math.cos(pitch * 0.5), math.sin(pitch * 0.5)
        # q = q_yaw * q_pitch -> (qx, qy, qz, qw)
        qx = cy * sp
        qy = sy * cp
        qz = -sy * sp
        qw = cy * cp
        targets.append({
            "extrinsics": {
                "position": [round(px, 4), round(py, 4), round(pz, 4)],
                "quaternion": [round(qx, 5), round(qy, 5), round(qz, 5), round(qw, 5)],
                "coordinateSystem": "rub",
            },
            "intrinsics": intr,
        })
    return targets


def _poll_atlas_operation_briefly(op_id: str, ai_router: Any = None, max_wait_s: float = 24.0, step_s: float = 1.5) -> Dict[str, Any]:
    """Poll a fast Atlas operation (e.g. images2PosedRGBD) up to max_wait_s."""
    deadline = time.time() + max_wait_s
    last_res: Dict[str, Any] = {"ok": True, "operation_id": op_id, "done": False, "status": "RUNNING"}
    while time.time() < deadline:
        time.sleep(step_s)
        _, polled = _atlas_operation_status(op_id, ai_router=ai_router)
        if isinstance(polled, dict):
            last_res = polled
            if polled.get("done") or polled.get("ok") is False:
                break
    return last_res


def _omni_route(
    data: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
    ai_router: Any = None,
) -> Tuple[int, Dict[str, Any]]:
    if not isinstance(data, dict):
        return 400, {"ok": False, "error": "Payload must be a JSON object"}

    raw_cmd = (data.get("command") or "").strip()
    raw_prompt = (data.get("prompt") or "").strip()
    if raw_cmd and raw_prompt and raw_prompt not in raw_cmd:
        combined_input = f"{raw_cmd} {raw_prompt}".strip()
    else:
        combined_input = raw_cmd or raw_prompt

    if not combined_input:
        return 400, {"ok": False, "error": "Missing 'command' or 'prompt'"}

    parsed_route = _parse_omni_slash_command(combined_input)
    if raw_cmd.lower().startswith("/rodin"):
        parsed_route["command"] = "3d"
        parsed_route["modality"] = "3d"

    cmd = str(parsed_route.get("command") or "image").lower()
    scope = (data.get("scope") or "user").strip()
    owner_id = (data.get("owner_id") or data.get("peer_id") or "default").strip()
    peer_id = (data.get("peer_id") or owner_id or "peer").strip()
    rtr = ai_router or globals().get("router")

    if cmd == "atlas" or parsed_route.get("modality") == "atlas":
        atlas_task = parsed_route.get("atlas_task") or _ATLAS_SUBCMD_TO_TASK.get(
            str(parsed_route.get("subcommand") or "splat").lower(),
            "posedImages2Splats",
        )
        flags = parsed_route.get("flags") or {}
        res_flag = flags.get("res")
        target_res = res_flag if (isinstance(res_flag, list) and len(res_flag) == 2) else [1280, 720]
        # Default to Draft mode (~30s, $0.50) unless explicitly requesting refined (15-21m, $5.00)
        refine_mode = bool(data.get("refine") is True or flags.get("refined") or flags.get("refine") is True)
        has_live_wlt_key = bool(rtr is not None and getattr(rtr, "worldlabs_key", None))

        # Accept pre-posed frames from an earlier images2PosedRGBD / atlasGenerate node
        incoming_posed_frames = _normalize_posed_frames_for_splats(data.get("posed_frames") or data.get("posedFrames"))
        raw_incoming_posed = data.get("posed_frames") or data.get("posedFrames") or []

        # Ingest ALL multi-view image references (up to 14 uploaded photos)
        raw_refs = data.get("references") or data.get("images") or []
        atlas_frames: List[Dict[str, Any]] = []
        uploaded_assets: List[Dict[str, Any]] = []
        if isinstance(raw_refs, list):
            for idx, ref in enumerate(raw_refs[:14]):
                if not isinstance(ref, dict):
                    continue
                ref_type = str(ref.get("type") or "image").lower()
                if ref_type not in ("image", ""):
                    continue
                b64_val = str(ref.get("base64") or ref.get("data_b64") or "").strip()
                url_val = str(ref.get("url") or "").strip()
                mime_val = str(ref.get("mimeType") or ref.get("mime_type") or "image/jpeg").strip()
                fname_val = str(ref.get("name") or ref.get("filename") or f"view_{idx}.jpg").strip()
                if not b64_val and url_val.startswith("data:") and ";base64," in url_val:
                    b64_val = url_val.split(";base64,", 1)[1]
                if b64_val:
                    up_status, up_res = _atlas_upload_asset(
                        {
                            "data_b64": b64_val,
                            "mime_type": mime_val,
                            "filename": fname_val,
                            "scope": scope,
                            "owner_id": owner_id,
                        },
                        ai_router=rtr,
                    )
                    asset_id = up_res.get("asset_id") or up_res.get("id")
                    if up_status == 200 and asset_id:
                        uploaded_assets.append({
                            "filename": fname_val,
                            "asset_id": asset_id,
                            "mime_type": mime_val,
                            "simulated": bool(up_res.get("simulated")),
                        })
                        atlas_frames.append({"imageAsset": {"assetId": asset_id}})
                elif url_val.startswith(("http://", "https://")):
                    uploaded_assets.append({"filename": fname_val, "url": url_val, "mime_type": mime_val, "simulated": False})
                    atlas_frames.append({"imageAsset": {"url": url_val}})

        req_body: Dict[str, Any] = {
            "prompt": parsed_route.get("prompt") or combined_input,
            "subcommand": parsed_route.get("subcommand") or "splat",
            "flags": flags,
        }
        if parsed_route.get("target_path"):
            req_body["target_path"] = parsed_route["target_path"]

        stage1_pose_res: Optional[Dict[str, Any]] = None
        posed_frames_for_next: List[Dict[str, Any]] = list(incoming_posed_frames)
        raw_posed_frames_out: List[Dict[str, Any]] = list(raw_incoming_posed) if isinstance(raw_incoming_posed, list) else []
        strict_live_input = bool(has_live_wlt_key and (atlas_frames or incoming_posed_frames or data.get("splat_asset_id")))

        if atlas_task == "images2PosedRGBD" and atlas_frames:
            req_body = {"frames": atlas_frames, "targetResolution": target_res}
        elif atlas_task == "atlasGenerate" and (incoming_posed_frames or atlas_frames):
            # If user hasn't posed yet, pose uploaded photos first
            if not incoming_posed_frames and atlas_frames:
                _, stage1_pose_res = _atlas_run_task(
                    {"task": "images2PosedRGBD", "request_body": {"frames": atlas_frames, "targetResolution": target_res}},
                    headers=headers,
                    ai_router=rtr,
                )
                s1_op_id = (stage1_pose_res or {}).get("operation_id") or (stage1_pose_res or {}).get("id")
                if stage1_pose_res and stage1_pose_res.get("ok") and not stage1_pose_res.get("done") and s1_op_id:
                    stage1_pose_res = _poll_atlas_operation_briefly(s1_op_id, ai_router=rtr, max_wait_s=28.0)
                if strict_live_input and stage1_pose_res and not stage1_pose_res.get("ok"):
                    return int(stage1_pose_res.get("status_code") or 422), {
                        "ok": False,
                        "stage": "images2PosedRGBD",
                        "route": parsed_route,
                        "error": (stage1_pose_res.get("error") or {}).get("message") or "World Labs images2PosedRGBD failed",
                        "result": stage1_pose_res,
                    }
                s1_frames = ((stage1_pose_res or {}).get("response") or {}).get("frames") or []
                raw_posed_frames_out = s1_frames if isinstance(s1_frames, list) else []
                posed_frames_for_next = _normalize_posed_frames_for_splats(raw_posed_frames_out)
            anchor = raw_posed_frames_out[0] if raw_posed_frames_out else (posed_frames_for_next[0] if posed_frames_for_next else {})
            n_views = int(flags.get("views") or data.get("views") or 6)
            target_cams = _build_orbital_target_cameras(anchor, num_views=max(2, min(n_views, 8)))
            req_body = {
                "contextFrames": posed_frames_for_next,
                "targetCameras": target_cams,
                "returnDepth": True,
            }
            clean_p = (parsed_route.get("prompt") or "").strip()
            if clean_p and not clean_p.startswith("/"):
                req_body["prompt"] = clean_p
        elif atlas_task == "posedImages2Splats" and (incoming_posed_frames or atlas_frames):
            if not incoming_posed_frames and atlas_frames:
                # Stage 1: Pose all uploaded photos via images2PosedRGBD
                _, stage1_pose_res = _atlas_run_task(
                    {"task": "images2PosedRGBD", "request_body": {"frames": atlas_frames, "targetResolution": target_res}},
                    headers=headers,
                    ai_router=rtr,
                )
                s1_op_id = (stage1_pose_res or {}).get("operation_id") or (stage1_pose_res or {}).get("id")
                if stage1_pose_res and stage1_pose_res.get("ok") and not stage1_pose_res.get("done") and s1_op_id:
                    stage1_pose_res = _poll_atlas_operation_briefly(s1_op_id, ai_router=rtr, max_wait_s=28.0)
                if strict_live_input and stage1_pose_res and not stage1_pose_res.get("ok"):
                    return int(stage1_pose_res.get("status_code") or 422), {
                        "ok": False,
                        "stage": "images2PosedRGBD",
                        "route": parsed_route,
                        "error": (stage1_pose_res.get("error") or {}).get("message") or "World Labs images2PosedRGBD failed",
                        "result": stage1_pose_res,
                    }
                s1_resp = (stage1_pose_res or {}).get("response") or {}
                raw_posed_frames_out = s1_resp.get("frames") or s1_resp.get("posedFrames") or []
                posed_frames_for_next = _normalize_posed_frames_for_splats(raw_posed_frames_out)
            if strict_live_input and len(posed_frames_for_next) < 2:
                return 422, {
                    "ok": False,
                    "stage": "posedImages2Splats",
                    "route": parsed_route,
                    "error": (
                        f"World Labs posedImages2Splats requires at least 2 posed views (got {len(posed_frames_for_next)}). "
                        "Upload 2–14 overlapping photos of the same static scene, or run 'Generate Views' (atlasGenerate) from 1 posed anchor photo first."
                    ),
                    "result": {
                        "ok": False,
                        "simulated": False,
                        "input_frame_count": len(atlas_frames),
                        "posed_frame_count": len(posed_frames_for_next),
                        "posed_frames": raw_posed_frames_out,
                    },
                }
            # Exact World Labs Atlas v2 posedImages2Splats schema
            req_body = {
                "posedFrames": posed_frames_for_next if posed_frames_for_next else atlas_frames,
                "refine": refine_mode,
            }
            clean_p = (parsed_route.get("prompt") or "").strip()
            if clean_p and not clean_p.startswith("/") and clean_p.lower() not in ("multi-view 3d gaussian splat", "recreate the scene"):
                req_body["prompt"] = clean_p
        elif atlas_task == "splats2Mesh" and data.get("splat_asset_id"):
            req_body = {"splatAsset": {"assetId": str(data["splat_asset_id"])}}
        elif atlas_task == "atlasTextToImage":
            req_body = {"prompt": parsed_route.get("prompt") or combined_input}

        _, run_res = _atlas_run_task(
            {
                "task": atlas_task,
                "request_body": req_body,
                "idempotency_key": data.get("idempotency_key"),
            },
            headers=headers,
            ai_router=rtr,
        )
        op_id = run_res.get("operation_id") or run_res.get("id") or "op_atlas_sim"

        # If images2PosedRGBD is live and fast (~5s), poll briefly so we return completed posedFrames immediately
        if atlas_task == "images2PosedRGBD" and run_res.get("ok") and not run_res.get("done") and has_live_wlt_key:
            run_res = _poll_atlas_operation_briefly(op_id, ai_router=rtr, max_wait_s=26.0)
            if run_res.get("done") and isinstance(run_res.get("response"), dict):
                raw_posed_frames_out = run_res["response"].get("frames") or []
                posed_frames_for_next = _normalize_posed_frames_for_splats(raw_posed_frames_out)

        # NEVER silently fake a simulated .spz when live World Labs rejected real uploaded photos!
        if not run_res.get("ok"):
            if strict_live_input:
                err_obj = run_res.get("error") if isinstance(run_res.get("error"), dict) else {}
                err_msg = err_obj.get("message") or run_res.get("error") or f"World Labs {atlas_task} returned HTTP {run_res.get('status_code', 422)}"
                return int(run_res.get("status_code") or 422), {
                    "ok": False,
                    "stage": atlas_task,
                    "route": parsed_route,
                    "error": str(err_msg),
                    "result": {
                        **run_res,
                        "simulated": False,
                        "input_frame_count": len(atlas_frames) or len(posed_frames_for_next),
                        "posed_frames": raw_posed_frames_out,
                    },
                }
            # Offline / shorthand prompt without uploaded photos: deterministic local fallback
            if rtr is not None and hasattr(rtr, "_build_simulated_atlas_response"):
                short_hash = re.sub(r"[^a-zA-Z0-9]", "", op_id)[-12:] or "3e78434c27d2"
                sim_resp = rtr._build_simulated_atlas_response(atlas_task, req_body, short_hash)
                sim_op = {
                    "ok": True,
                    "id": op_id,
                    "operation_id": op_id,
                    "task": atlas_task,
                    "status": "SUCCEEDED",
                    "done": True,
                    "simulated": True,
                    "response": sim_resp,
                    "credits_consumed": 150,
                }
                if hasattr(rtr, "atlas_operations") and isinstance(rtr.atlas_operations, dict):
                    rtr.atlas_operations[op_id] = sim_op
                run_res = sim_op

        # Non-blocking async return for long-running live World Labs jobs (posedImages2Splats, atlasGenerate, splats2Mesh)
        if not run_res.get("done") and has_live_wlt_key:
            est_sec = 35 if (atlas_task == "posedImages2Splats" and not refine_mode) else (1080 if atlas_task == "posedImages2Splats" else 35)
            return 200, {
                "ok": True,
                "async": True,
                "done": False,
                "status": run_res.get("status") or "RUNNING",
                "operation_id": op_id,
                "task": atlas_task,
                "refine": refine_mode,
                "estimated_seconds": est_sec,
                "route": parsed_route,
                "result": {
                    **run_res,
                    "simulated": False,
                    "refine": refine_mode,
                    "estimated_seconds": est_sec,
                    "input_frame_count": len(atlas_frames) or len(posed_frames_for_next),
                    "uploaded_assets": uploaded_assets,
                    "posed_frames": raw_posed_frames_out,
                    "stage1_pose_operation_id": (stage1_pose_res or {}).get("operation_id") or (stage1_pose_res or {}).get("id"),
                },
                "saved_to_space": None,
                "files_b64": {},
            }

        _, dl_res = _atlas_download_operation(
            {
                "operation_id": op_id,
                "scope": scope,
                "owner_id": owner_id,
                "peer_id": peer_id,
                "target_dir": data.get("target_dir") or "/worlds",
                "include_mesh": bool(flags.get("mesh") or atlas_task == "splats2Mesh"),
            },
            ai_router=rtr,
        )
        saved_files = dl_res.get("saved_files") or []
        saved_to_space = {
            "scope": scope,
            "owner_id": owner_id,
            "files": saved_files,
            "path": dl_res.get("spz_path") or (saved_files[0] if saved_files else None),
        }
        result_payload: Dict[str, Any] = {
            **run_res,
            "refine": refine_mode,
            "input_frame_count": len(atlas_frames) or len(posed_frames_for_next),
            "uploaded_assets": uploaded_assets,
            "posed_frames": raw_posed_frames_out,
            "spz_path": dl_res.get("spz_path"),
            "spz_size_bytes": dl_res.get("spz_size_bytes", 0),
            "spz_asset_id": dl_res.get("spz_asset_id"),
            "is_real_spz": bool(dl_res.get("is_real_spz")),
            "download": {k: v for k, v in dl_res.items() if k != "files_b64"},
        }
        if stage1_pose_res is not None:
            result_payload["stage1_pose_operation_id"] = stage1_pose_res.get("operation_id") or stage1_pose_res.get("id")
        return 200, {
            "ok": True,
            "done": True,
            "operation_id": op_id,
            "task": atlas_task,
            "route": parsed_route,
            "result": result_payload,
            "saved_to_space": saved_to_space,
            "files_b64": dl_res.get("files_b64") or {},
        }

    if cmd == "audio" or parsed_route.get("modality") == "audio":
        kind = str(parsed_route.get("subcommand") or "music").lower()
        if kind not in ("tts", "music", "sfx"):
            kind = "music"
        flags = parsed_route.get("flags") or {}
        _, aud_res = _audio_generate_and_save(
            {
                "prompt": parsed_route.get("prompt") or combined_input,
                "kind": kind,
                "model": flags.get("model") or parsed_route.get("model"),
                "voice": flags.get("voice") or data.get("voice"),
                "scope": scope,
                "owner_id": owner_id,
                "peer_id": peer_id,
                "save_path": data.get("save_path"),
            },
            ai_router=rtr,
        )
        sp_path = aud_res.get("path")
        files_b64 = {sp_path: aud_res["audio_bytes_b64"]} if (sp_path and aud_res.get("audio_bytes_b64")) else {}
        return 200, {
            "ok": True,
            "route": parsed_route,
            "result": aud_res,
            "saved_to_space": aud_res.get("saved_to_space"),
            "files_b64": files_b64,
        }

    if cmd in ("3d", "rodin"):
        from iot_federated_agent_memory.agent_space import (
            _slug_from_prompt,
            _unique_space_path,
            generate_minimal_glb_bytes,
        )

        flags = parsed_route.get("flags") or {}
        tier = str(flags.get("tier") or data.get("tier") or "Regular")
        prompt_3d = parsed_route.get("prompt") or combined_input
        res_3d = _dispatch_rodin(
            rtr,
            prompt=prompt_3d,
            tier=tier,
            geometry_file_format="glb",
        )
        glb_b64 = res_3d.get("glb_bytes_b64") or ""
        if not glb_b64:
            glb_b64 = base64.b64encode(generate_minimal_glb_bytes(_slug_from_prompt(prompt_3d, default="mesh"))).decode("ascii")
            res_3d["glb_bytes_b64"] = glb_b64
        sm = _get_space_manager()
        sp = sm.get_or_create_space(scope, owner_id)
        slug = _slug_from_prompt(prompt_3d, default="rodin_mesh")
        sp_path = data.get("save_path") or _unique_space_path(sp, "/models3d", slug, ".glb")
        sp.write_file(sp_path, glb_b64, is_base64=True, mime_type="model/gltf-binary", updated_by=peer_id)
        saved_to_space = {"scope": scope, "owner_id": owner_id, "path": sp_path}
        res_3d["saved_to_space"] = saved_to_space
        return 200, {
            "ok": True,
            "route": parsed_route,
            "result": res_3d,
            "saved_to_space": saved_to_space,
            "files_b64": {sp_path: glb_b64},
        }

    if cmd == "rig":
        import posixpath
        from iot_federated_agent_memory.agent_space import (
            _unique_space_path,
            generate_minimal_glb_bytes,
        )
        from iot_federated_agent_memory.glb_rigger import rig_glb_bytes

        flags = parsed_route.get("flags") or {}
        src_path = (
            parsed_route.get("target_path")
            or data.get("path")
            or "/models3d/mesh.glb"
        )
        if not src_path.startswith("/"):
            src_path = "/" + src_path
        anim = str(flags.get("anim") or data.get("animation") or parsed_route.get("subcommand") or "walk")
        rig_type = str(flags.get("rig") or data.get("rig_type") or "auto")
        sm = _get_space_manager()
        sp = sm.get_or_create_space(scope, owner_id)
        try:
            rec = sp.read_file(src_path, as_text=False)
            src_bytes = base64.b64decode(rec.get("content_b64") or "")
        except FileNotFoundError:
            src_bytes = generate_minimal_glb_bytes("rig_source")
            sp.write_file(src_path, src_bytes, mime_type="model/gltf-binary", updated_by=peer_id)

        out_bytes, meta = rig_glb_bytes(src_bytes, rig_type=rig_type, animation=anim)
        out_b64 = base64.b64encode(out_bytes).decode("ascii")
        dname = posixpath.dirname(src_path) or "/models3d"
        stem = posixpath.splitext(posixpath.basename(src_path))[0] or "mesh"
        if stem.endswith("_rigged"):
            stem = stem[:-7] or "mesh"
        out_path = data.get("save_path") or _unique_space_path(sp, dname, f"{stem}_rigged", ".glb")
        sp.write_file(out_path, out_b64, is_base64=True, mime_type="model/gltf-binary", updated_by=peer_id)
        saved_to_space = {"scope": scope, "owner_id": owner_id, "path": out_path}
        rig_res = {
            "ok": True,
            "provider": "tincan-auto-rigger",
            "source_path": src_path,
            "path": out_path,
            "rig_type": meta["rig_type"],
            "bones": meta["bones"],
            "bone_count": meta["bone_count"],
            "animations": meta["animations"],
            "size_bytes": meta["size_bytes"],
            "saved_to_space": saved_to_space,
        }
        return 200, {
            "ok": True,
            "route": parsed_route,
            "result": rig_res,
            "saved_to_space": saved_to_space,
            "files_b64": {out_path: out_b64},
        }

    # Default: /text, /image, /video, /mux -> route to handle_node_studio_generate
    ns_payload = {
        **data,
        "prompt": combined_input,
        "modality": parsed_route.get("modality") or cmd,
        "model": parsed_route.get("model") or data.get("model"),
    }
    code, ns_res = _node_studio_generate(ns_payload, headers=headers)
    saved_to_space = ns_res.get("saved_to_space")
    if not saved_to_space:
        sm = _get_space_manager()
        sp = sm.get_or_create_space(scope, owner_id)
        node_obj = ns_res.get("node") if isinstance(ns_res.get("node"), dict) else {}
        node_id = str(node_obj.get("id") or f"node_{uuid.uuid4().hex[:6]}")
        meta_path = f"/nodes/{cmd}_{node_id}.json"
        sp.write_file(meta_path, json.dumps({"route": parsed_route, "node": node_obj}, indent=2), mime_type="application/json", updated_by=peer_id)
        saved_to_space = {"scope": scope, "owner_id": owner_id, "path": meta_path}
    return code, {
        "ok": ns_res.get("ok", True),
        "route": parsed_route,
        "result": ns_res,
        "saved_to_space": saved_to_space,
    }


def _normalize_node_graph_path(raw_path: Optional[str] = None, raw_name: Optional[str] = None) -> Tuple[str, str]:
    """Normalize a Node Studio graph name/path to `/nodes/<slug>.nodes.json` inside `.space` VFS."""
    candidate = (raw_path or raw_name or "workspace").strip()
    if candidate.startswith("/nodes/"):
        candidate = candidate[len("/nodes/"):]
    candidate = candidate.strip("/")
    for suffix in (".nodes.json", ".nodegraph.json", ".json"):
        if candidate.lower().endswith(suffix):
            candidate = candidate[: -len(suffix)]
            break
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", candidate).strip("_-") or "workspace"
    slug = slug[:64]
    return f"/nodes/{slug}.nodes.json", slug


def _node_graph_list(scope: str = "user", owner_id: str = "default") -> Tuple[int, Dict[str, Any]]:
    sm = _get_space_manager()
    sp = sm.get_or_create_space((scope or "user").strip(), (owner_id or "default").strip())
    summary = sp.get_summary()
    raw_files = summary.get("files") if isinstance(summary, dict) else []
    graphs: List[Dict[str, Any]] = []
    for f in (raw_files or []):
        if not isinstance(f, dict):
            continue
        fpath = str(f.get("path") or "")
        if fpath.startswith("/nodes/") and fpath.endswith(".nodes.json"):
            _, name = _normalize_node_graph_path(fpath)
            graphs.append({
                "path": fpath,
                "name": name,
                "size_bytes": f.get("size_bytes", 0),
                "updated_at": f.get("updated_at"),
                "sha256": f.get("sha256"),
            })
    graphs.sort(key=lambda g: str(g.get("updated_at") or ""), reverse=True)
    return 200, {
        "ok": True,
        "scope": scope,
        "owner_id": owner_id,
        "graphs": graphs,
        "count": len(graphs),
    }


def _node_graph_load(
    scope: str = "user",
    owner_id: str = "default",
    path: Optional[str] = None,
    name: Optional[str] = None,
) -> Tuple[int, Dict[str, Any]]:
    norm_path, norm_name = _normalize_node_graph_path(path, name)
    sm = _get_space_manager()
    sp = sm.get_or_create_space((scope or "user").strip(), (owner_id or "default").strip())
    try:
        rec = sp.read_file(norm_path, as_text=True)
    except FileNotFoundError:
        return 404, {
            "ok": False,
            "error": f"Node graph not found: {norm_path}",
            "path": norm_path,
            "name": norm_name,
        }
    raw_text = rec.get("content") or "{}"
    try:
        graph_obj = json.loads(raw_text) if isinstance(raw_text, str) else {}
    except Exception:
        graph_obj = {}
    return 200, {
        "ok": True,
        "scope": scope,
        "owner_id": owner_id,
        "path": norm_path,
        "name": norm_name,
        "updated_at": rec.get("updated_at"),
        "sha256": rec.get("sha256"),
        "graph": graph_obj,
    }


def _node_graph_save(data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    if not isinstance(data, dict):
        return 400, {"ok": False, "error": "Payload must be a JSON object"}
    scope = (data.get("scope") or "user").strip()
    owner_id = (data.get("owner_id") or data.get("peer_id") or "default").strip()
    updated_by = (data.get("updated_by") or data.get("peer_id") or owner_id or "user").strip()
    norm_path, norm_name = _normalize_node_graph_path(data.get("path"), data.get("name"))

    graph_in = data.get("graph") if isinstance(data.get("graph"), dict) else data
    nodes = graph_in.get("nodes") if isinstance(graph_in.get("nodes"), list) else []
    edges = graph_in.get("edges") if isinstance(graph_in.get("edges"), list) else []
    references = graph_in.get("references") if isinstance(graph_in.get("references"), list) else []
    viewport = graph_in.get("viewport") if isinstance(graph_in.get("viewport"), dict) else {"panX": 0, "panY": 0, "zoom": 1}
    config = graph_in.get("config") if isinstance(graph_in.get("config"), dict) else {}
    selected_ids = graph_in.get("selectedIds") if isinstance(graph_in.get("selectedIds"), list) else []
    saved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    payload = {
        "schema": "tincan.node_studio.graph.v1",
        "name": norm_name,
        "path": norm_path,
        "savedAt": saved_at,
        "viewport": viewport,
        "config": config,
        "nodeSeq": int(graph_in.get("nodeSeq") or len(nodes)),
        "selectedIds": selected_ids,
        "nodes": nodes,
        "edges": edges,
        "references": references,
    }

    sm = _get_space_manager()
    sp = sm.get_or_create_space(scope, owner_id)
    out = sp.write_file(
        norm_path,
        json.dumps(payload, indent=2),
        mime_type="application/json",
        updated_by=updated_by,
    )
    return 200, {
        "ok": True,
        "scope": scope,
        "owner_id": owner_id,
        "path": norm_path,
        "name": norm_name,
        "saved_at": saved_at,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "reference_count": len(references),
        "merkle_root": out.get("merkle_root") if isinstance(out, dict) else sp.compute_merkle_root(),
    }


PORT = int(os.environ.get("PORT", 8080))


def _resolve_commit_hash() -> str:
    env_sha = (
        os.environ.get("RAILWAY_GIT_COMMIT_SHA")
        or os.environ.get("GIT_COMMIT_SHA")
        or ""
    ).strip()
    if env_sha:
        return env_sha[:7]
    try:
        out = (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                stderr=subprocess.DEVNULL,
                timeout=2.0,
            )
            .decode("utf-8")
            .strip()
        )
        if out:
            return out
    except Exception:
        pass
    return "2f7faf2"


COMMIT_HASH = _resolve_commit_hash()
_downloading_videos = set()
_downloading_lock = threading.Lock()
_html_cache = {}

relay = WebRTCSignalingRelay()
router = DynamicAIGatewayRouter()
_DEFAULT_ROUTER = router
scale = IoTFederatedMemoryScale()
tincan_relay = TinCanBlindRelay()
playlist = RelayVideoPlaylist()
sponsor_manager = SponsorAdManager()
sponsor_manager.sync_from_playlist([asdict(it) for it in playlist.items])
mesh_os = TinCanMeshOSEngine(seed=False)
account_registry = PeerAccountRegistry()
set_thread_account_registry(account_registry)
passkey_auth = PasskeyAuthService(account_registry)

# --- Token minting lockdown -------------------------------------------------
# Credits are only ever added by the server: after a Stripe-signed payment
# webhook, after a server-timed ad view, or by an operator holding the admin key.
# Prices live here, never in the request, so a client can't name its own amount.
TOKEN_PACKS = {  # pack id -> (price in US cents, tokens). Matches the Mesh OS UI buttons.
    "pack_100": (100, 120),     # $1  (Stripe's USD minimum is $0.50, so no sub-$1 packs)
    "pack_500": (500, 650),     # $5
    "pack_2000": (2000, 2800),  # $20
}
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
TINCAN_ADMIN_KEY = os.environ.get("TINCAN_ADMIN_KEY", "")
AD_DAILY_REWARD_CAP = int(os.environ.get("TINCAN_AD_DAILY_CAP", "5"))
AD_MIN_WATCH_FRACTION = 0.9
_ad_views = {}  # view_token -> {peer_id, sponsor_id, started, duration, reward_tokens, reward_usd}
_ad_views_lock = threading.Lock()
SIGNON_QUEST_KEYS = ("sealed_courier", "brain_arena_match", "arena_vote", "coop_action", "sandboxed_run")
_mint_requests: List[Dict[str, Any]] = []
_mint_requests_lock = threading.Lock()


def verify_stripe_signature(payload: bytes, sig_header: str, secret: str, tolerance: int = 300) -> bool:
    """Verify a Stripe-Signature header (t=...,v1=...) per Stripe's webhook signing scheme."""
    if not secret or not sig_header:
        return False
    try:
        parts = dict(p.split("=", 1) for p in sig_header.split(",") if "=" in p)
        ts = int(parts.get("t", "0"))
    except ValueError:
        return False
    if abs(time.time() - ts) > tolerance:
        return False
    expected = hmac.new(secret.encode(), f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
    candidates = [v for k, v in (p.split("=", 1) for p in sig_header.split(",") if "=" in p) if k == "v1"]
    return any(hmac.compare_digest(expected, c) for c in candidates)


def create_stripe_checkout(peer_id: str, pack_id: str, base_url: str) -> str:
    cents, tokens = TOKEN_PACKS[pack_id]
    form = urllib.parse.urlencode({
        "mode": "payment",
        "client_reference_id": peer_id,
        "metadata[peer_id]": peer_id,
        "metadata[pack]": pack_id,
        "line_items[0][quantity]": "1",
        "line_items[0][price_data][currency]": "usd",
        "line_items[0][price_data][unit_amount]": str(cents),
        "line_items[0][price_data][product_data][name]": f"TinCan {tokens:,} tokens",
        "success_url": f"{base_url}/?checkout=success",
        "cancel_url": f"{base_url}/?checkout=cancel",
    }).encode()
    req = urllib.request.Request(
        "https://api.stripe.com/v1/checkout/sessions", data=form, method="POST",
        headers={"Authorization": f"Bearer {STRIPE_SECRET_KEY}"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())["url"]

cyberspace_board = CyberspaceBoardEngine(
    account_registry=account_registry,
    ai_router=router,
    tincan_relay=tincan_relay,
    webrtc_relay=relay,
    seed=False,
)
crdt_node = CRDTMeshGossipSync(local_node_id="relay-primary")
vending_machine = HMACVendingMachine()
mqtt_adapter = MQTTTelemetryClientAdapter(
    vending_machine=vending_machine,
    wallet_id="mesh-default",
    batch_size=5,
)
mqtt_adapter.subscribe("devices/#")
mqtt_adapter.subscribe("matter/#")
mqtt_adapter.subscribe("coap/#")

ARTCRAFT_WASM_APPS = [
    {
        "id": "cadcraft",
        "name": "CadCraft Web",
        "app": "cadcraft-web",
        "description": "3D CAD modeling, STEP/STL geometry, parametric sketches",
        "extensions": [".cad", ".step", ".stl", ".dxf"],
        "icon": "📐",
    },
    {
        "id": "vectorcraft",
        "name": "VectorCraft Web",
        "app": "vectorcraft-web",
        "description": "Vector graphics, SVG illustration & path typography",
        "extensions": [".svg", ".vec"],
        "icon": "✒️",
    },
    {
        "id": "deckcraft",
        "name": "DeckCraft Web",
        "app": "deckcraft-web",
        "description": "Pitch decks, slide presentations & interactive reports",
        "extensions": [".deck", ".slide", ".pptx"],
        "icon": "📊",
    },
    {
        "id": "designcraft",
        "name": "DesignCraft Web",
        "app": "designcraft-web",
        "description": "Page layout, typography & publication design",
        "extensions": [".indd", ".layout"],
        "icon": "📰",
    },
    {
        "id": "effectcraft",
        "name": "EffectCraft Web",
        "app": "effectcraft-web",
        "description": "Visual effects, motion graphics & particle rendering",
        "extensions": [".fx", ".comp"],
        "icon": "✨",
    },
    {
        "id": "figcraft",
        "name": "FigCraft Web",
        "app": "figcraft-web",
        "description": "UI/UX component systems, wireframing & mockups",
        "extensions": [".fig", ".ui"],
        "icon": "🎨",
    },
    {
        "id": "filmcraft",
        "name": "FilmCraft Web",
        "app": "filmcraft-web",
        "description": "Multi-track video editing, timeline & sequence clips",
        "extensions": [".film", ".timeline"],
        "icon": "🎬",
    },
    {
        "id": "gridcraft",
        "name": "GridCraft Web",
        "app": "gridcraft-web",
        "description": "Grid computation, spreadsheet analysis & tabular data",
        "extensions": [".grid", ".csv", ".xlsx"],
        "icon": "📈",
    },
    {
        "id": "lightcraft",
        "name": "LightCraft Web",
        "app": "lightcraft-web",
        "description": "Color grading, RAW image develop & LUT tone mapping",
        "extensions": [".raw", ".cube", ".grade"],
        "icon": "💡",
    },
    {
        "id": "pdfcraft",
        "name": "PdfCraft Web",
        "app": "pdfcraft-web",
        "description": "PDF document compilation, form filling & digital signing",
        "extensions": [".pdf"],
        "icon": "📄",
    },
    {
        "id": "photocraft",
        "name": "PhotoCraft Web",
        "app": "photocraft-web",
        "description": "Raster image manipulation, layering & retouching",
        "extensions": [".photo", ".psd", ".png", ".jpg"],
        "icon": "🖼️",
    },
    {
        "id": "scriptcraft",
        "name": "ScriptCraft Web",
        "app": "scriptcraft-web",
        "description": "Screenplay writing, fountain syntax & script beats",
        "extensions": [".fountain", ".script"],
        "icon": "📜",
    },
    {
        "id": "soundcraft",
        "name": "SoundCraft Web",
        "app": "soundcraft-web",
        "description": "Digital audio workstation, stem mixing & synthesizer",
        "extensions": [".sound", ".wav", ".mp3", ".ogg"],
        "icon": "🎵",
    },
    {
        "id": "wordcraft",
        "name": "WordCraft Web",
        "app": "wordcraft-web",
        "description": "Prose editor, distraction-free markdown & publication",
        "extensions": [".word", ".md", ".txt"],
        "icon": "📝",
    },
    {
        "id": "artcraft",
        "name": "ArtCraft Meta-Studio Web",
        "app": "artcraft-web",
        "description": "Omni-creative project launcher & pipeline graph loop",
        "extensions": [".craft", ".loop", ".json"],
        "icon": "🛸",
    },
]

WASM_RUNTIMES = [
    {
        "id": "pyodide-wasm",
        "name": "Pyodide Python 3.12 Wasm",
        "languages": ["python", "py"],
        "description": "In-browser CPython runtime with NumPy, Matplotlib & micropip",
    },
    {
        "id": "quickjs-wasm",
        "name": "QuickJS JavaScript Wasm",
        "languages": ["javascript", "js"],
        "description": "Embedded lightweight ES2020 JavaScript engine in WebAssembly",
    },
    {
        "id": "wasi-wasm",
        "name": "WASI Universal Bytecode",
        "languages": ["wasm", "wat", "c", "rust"],
        "description": "Sandboxed WebAssembly System Interface runtime container",
    },
    {
        "id": "three-glb-viewer",
        "name": "Three.js 3D glTF / GLB Spatial Viewer",
        "languages": ["glb", "gltf", "3d"],
        "description": "Interactive WebGL 3D viewer for Hyper3D Rodin & CadCraft meshes",
    },
]

WASM_POSTMESSAGE_CONTRACT = {
    "protocol": "artcraft-wasm-bridge-v1",
    "host_query": "?host=parent",
    "parent_events": {
        "<app>:ready": "Sent by child iframe when Wasm app is loaded and ready for state",
        "<app>:open": "Sent by parent to child: { name: str, bytes: str(b64) or content: str, path: str, format: str }",
        "<app>:save": "Sent by child to parent: { name: str, bytes: str(b64) or content: str, path: str, dirty: false }",
        "<app>:dirty": "Sent by child to parent when user modifies unsaved state: { dirty: bool }",
    },
}


RODIN_TIER_PRICING_USD = {
    "Sketch": 0.25,
    "Regular": 0.50,
    "Smooth": 0.75,
    "Detail": 1.00,
}


def _estimate_rodin_tier_cost(tier: str) -> float:
    """Resolve estimated USD cost for a Hyper3D Rodin generation tier."""
    if tier in RODIN_TIER_PRICING_USD:
        return float(RODIN_TIER_PRICING_USD[tier])
    low = str(tier or "").strip().lower()
    for key, price in RODIN_TIER_PRICING_USD.items():
        if key.lower() == low:
            return float(price)
    return 0.50


def _compute_plan_diff_preview(sp, edits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compute unified diff snippets comparing current VFS content vs proposed edits."""
    simulated: Dict[str, Optional[str]] = {}
    previews: List[Dict[str, Any]] = []
    for edit in edits:
        path = edit["path"]
        op = edit.get("op", "write")
        if path not in simulated:
            try:
                rec = sp.read_file(path, as_text=True)
                content = rec.get("content")
                simulated[path] = content if content is not None else "[binary content]"
            except FileNotFoundError:
                simulated[path] = None
        old_text = simulated[path]
        if op == "write":
            new_text: Optional[str] = edit.get("content", "")
        elif op == "delete":
            new_text = None
        elif op == "patch":
            target = edit.get("target", "")
            replacement = edit.get("replacement", "")
            if old_text is not None and target and target in old_text:
                new_text = old_text.replace(target, replacement, 1)
            else:
                new_text = old_text
        else:
            new_text = old_text
        simulated[path] = new_text

        old_lines = old_text.splitlines() if old_text is not None else []
        new_lines = new_text.splitlines() if new_text is not None else []
        fromfile = "/dev/null" if old_text is None else f"a{path}"
        tofile = "/dev/null" if new_text is None else f"b{path}"
        diff_lines = list(
            difflib.unified_diff(old_lines, new_lines, fromfile=fromfile, tofile=tofile, lineterm="")
        )
        previews.append({
            "path": path,
            "op": op,
            "diff": "\n".join(diff_lines),
            "lines": diff_lines,
            "added": sum(1 for ln in diff_lines if ln.startswith("+") and not ln.startswith("+++")),
            "removed": sum(1 for ln in diff_lines if ln.startswith("-") and not ln.startswith("---")),
        })
    return previews


def _dispatch_rodin(ai_router, prompt, images=None, tier="Regular", geometry_file_format="glb", material="PBR", quality="medium", mesh_mode="Quad"):
    if hasattr(ai_router, "dispatch_rodin_generation"):
        return ai_router.dispatch_rodin_generation(
            prompt=prompt,
            images=images,
            tier=tier,
            geometry_file_format=geometry_file_format,
            material=material,
            quality=quality,
            mesh_mode=mesh_mode,
        )
    cost = _estimate_rodin_tier_cost(tier)
    task_id = f"rodin-task-{uuid.uuid4().hex[:12]}"
    sub_key = f"sub-{uuid.uuid4().hex[:12]}"
    glb_raw = b"glTF\x02\x00\x00\x00\x14\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    glb_b64 = base64.b64encode(glb_raw).decode("ascii")
    return {
        "uuid": task_id,
        "subscription_key": sub_key,
        "prompt": prompt,
        "tier": tier,
        "format": geometry_file_format,
        "material": material,
        "quality": quality,
        "mesh_mode": mesh_mode,
        "status": "Done",
        "cost_usd": cost,
        "created_at": time.time(),
        "glb_bytes_b64": glb_b64,
        "simulated": True,
    }


def _check_rodin_status(ai_router, subscription_key):
    if hasattr(ai_router, "check_rodin_status"):
        return ai_router.check_rodin_status(subscription_key)
    return {
        "subscription_key": subscription_key,
        "status": "Done",
        "jobs": [{"uuid": f"rodin-{subscription_key[:8]}", "status": "Done"}],
    }


def _download_rodin_assets(ai_router, task_uuid):
    if hasattr(ai_router, "download_rodin_assets"):
        return ai_router.download_rodin_assets(task_uuid)
    glb_raw = b"glTF\x02\x00\x00\x00\x14\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    glb_b64 = base64.b64encode(glb_raw).decode("ascii")
    return {
        "task_uuid": task_uuid,
        "format": "glb",
        "files": [{"name": f"{task_uuid}.glb", "format": "glb", "bytes_b64": glb_b64}],
        "glb_bytes_b64": glb_b64,
    }


def _get_hyper3d_billing(ai_router):
    if hasattr(ai_router, "get_hyper3d_billing"):
        return ai_router.get_hyper3d_billing()
    analytics = ai_router.get_analytics() if hasattr(ai_router, "get_analytics") else {}
    if "hyper3d" in analytics:
        return analytics["hyper3d"]
    return {
        "connected": False,
        "provider": "Hyper3D Rodin (Ronin) v2",
        "endpoint": "https://api.hyper3d.com/api/v2/rodin",
        "account_remaining_credits": 0.0,
        "account_remaining_balance_usd": 0.0,
        "session_total_tasks": 0,
        "session_total_spend_usd": 0.0,
        "key_label": "not_configured",
        "tier_pricing_usd": dict(RODIN_TIER_PRICING_USD),
    }


_browser_manager_singleton = None


def _get_browser_manager():
    global _browser_manager_singleton
    if _browser_manager_singleton is None:
        from iot_federated_agent_memory.browser_engine import TinCanBrowserManager
        _browser_manager_singleton = TinCanBrowserManager()
    return _browser_manager_singleton


class FallbackSingleFileSpaceVFS:
    def __init__(self, db_path: str, scope: str = "user", owner_id: str = "default_user"):
        self.db_path = db_path
        self.scope = scope
        self.owner_id = owner_id
        os.makedirs(os.path.dirname(os.path.abspath(db_path)) or ".", exist_ok=True)
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS files (
                    path TEXT PRIMARY KEY,
                    content BLOB,
                    mime_type TEXT,
                    size_bytes INTEGER,
                    sha256 TEXT,
                    updated_at REAL,
                    updated_by TEXT,
                    is_base64 INTEGER DEFAULT 0
                )
                """
            )

    def _normalize_path(self, path: str) -> str:
        p = path.strip()
        if not p.startswith("/"):
            p = "/" + p
        return p

    def write_file(self, path: str, content: Any, mime_type: Optional[str] = None, updated_by: str = "user", is_base64: bool = False) -> Dict[str, Any]:
        p = self._normalize_path(path)
        if isinstance(content, bytes):
            raw = content
            is_b64 = 0
        elif is_base64:
            raw = base64.b64decode(content) if isinstance(content, str) else bytes(content)
            is_b64 = 1
        elif isinstance(content, str):
            raw = content.encode("utf-8")
            is_b64 = 0
        else:
            raw = str(content).encode("utf-8")
            is_b64 = 0

        size = len(raw)
        sha = hashlib.sha256(raw).hexdigest()
        now = time.time()
        m_type = mime_type or ("model/gltf-binary" if p.endswith(".glb") else ("application/json" if p.endswith(".json") else "text/plain"))

        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO files (path, content, mime_type, size_bytes, sha256, updated_at, updated_by, is_base64)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    content=excluded.content,
                    mime_type=excluded.mime_type,
                    size_bytes=excluded.size_bytes,
                    sha256=excluded.sha256,
                    updated_at=excluded.updated_at,
                    updated_by=excluded.updated_by,
                    is_base64=excluded.is_base64
                """,
                (p, raw, m_type, size, sha, now, updated_by, is_b64),
            )
        return {
            "path": p,
            "size_bytes": size,
            "sha256": sha,
            "mime_type": m_type,
            "updated_at": now,
            "updated_by": updated_by,
        }

    def read_file(self, path: str, as_text: bool = True) -> Dict[str, Any]:
        p = self._normalize_path(path)
        with self._get_conn() as conn:
            cur = conn.execute("SELECT path, content, mime_type, size_bytes, sha256, updated_at, updated_by, is_base64 FROM files WHERE path=?", (p,))
            row = cur.fetchone()
        if not row:
            raise FileNotFoundError(f"File not found in space: {p}")
        p_val, blob, m_type, size, sha, updated_at, updated_by, is_b64 = row
        text_content = None
        if as_text and blob is not None:
            try:
                text_content = blob.decode("utf-8")
            except Exception:
                text_content = None
        b64_content = base64.b64encode(blob).decode("ascii") if blob else ""
        return {
            "path": p_val,
            "mime_type": m_type,
            "size_bytes": size,
            "sha256": sha,
            "updated_at": updated_at,
            "updated_by": updated_by,
            "content": text_content,
            "content_b64": b64_content,
        }

    def patch_file(self, path: str, target: str, replacement: str, updated_by: str = "agent") -> Dict[str, Any]:
        rec = self.read_file(path, as_text=True)
        txt = rec.get("content")
        if txt is None:
            raise ValueError(f"Cannot patch binary file: {path}")
        if target not in txt:
            raise ValueError(f"Target string not found in {path}")
        patched = txt.replace(target, replacement)
        return self.write_file(path, patched, mime_type=rec.get("mime_type"), updated_by=updated_by)

    def delete_file(self, path: str) -> Dict[str, Any]:
        p = self._normalize_path(path)
        with self._get_conn() as conn:
            conn.execute("DELETE FROM files WHERE path=?", (p,))
        return {"deleted": True, "path": p}

    def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.execute("SELECT path, mime_type, size_bytes, sha256, updated_at, updated_by FROM files ORDER BY path ASC")
            rows = cur.fetchall()
        files = []
        for r in rows:
            if not prefix or r[0].startswith(prefix):
                files.append({
                    "path": r[0],
                    "mime_type": r[1],
                    "size_bytes": r[2],
                    "sha256": r[3],
                    "updated_at": r[4],
                    "updated_by": r[5],
                })
        return files

    def compute_merkle_root(self) -> str:
        files = self.list_files()
        if not files:
            return hashlib.sha256(b"empty").hexdigest()
        concatenated = "".join(f["path"] + ":" + f["sha256"] for f in sorted(files, key=lambda x: x["path"]))
        return hashlib.sha256(concatenated.encode("utf-8")).hexdigest()

    def get_summary(self) -> Dict[str, Any]:
        files = self.list_files()
        sz = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
        return {
            "scope": self.scope,
            "owner_id": self.owner_id,
            "space_file": self.db_path,
            "space_size_bytes": sz,
            "file_count": len(files),
            "merkle_root": self.compute_merkle_root(),
            "files": files,
            "recent_runs": [],
            "recent_turns": [],
        }

    def export_space_bytes(self) -> bytes:
        if os.path.exists(self.db_path):
            with open(self.db_path, "rb") as f:
                return f.read()
        return b""

    def import_space_bytes(self, raw_bytes: bytes) -> Dict[str, Any]:
        with open(self.db_path, "wb") as f:
            f.write(raw_bytes)
        return self.get_summary()


class FallbackAgentSpaceManager:
    def __init__(self, base_dir: Optional[str] = None, ai_router: Optional[Any] = None):
        self.base_dir = base_dir or os.path.join(os.environ.get("AGENT_SPACES_DIR") or os.environ.get("TINCAN_DATA_DIR") or os.environ.get("RAILWAY_VOLUME_MOUNT_PATH") or os.path.dirname(os.path.abspath(__file__)), "spaces")
        self.ai_router = ai_router
        self._spaces: Dict[str, FallbackSingleFileSpaceVFS] = {}
        os.makedirs(self.base_dir, exist_ok=True)

    def _space_key(self, scope: str, owner_id: str) -> str:
        return f"{scope}:{owner_id}"

    def get_space(self, scope: str = "user", owner_id: str = "default_user", **kwargs) -> FallbackSingleFileSpaceVFS:
        scope = re.sub(r"[^a-z0-9_\-]", "_", str(scope or "").lower().strip()) or "user"
        owner_id = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", str(owner_id or "").strip()).lstrip(".") or "default_user"
        key = self._space_key(scope, owner_id)
        if key not in self._spaces:
            folder = os.path.join(self.base_dir, f"{scope}s")
            os.makedirs(folder, exist_ok=True)
            db_path = os.path.join(folder, f"{owner_id}.space")
            self._spaces[key] = FallbackSingleFileSpaceVFS(db_path, scope=scope, owner_id=owner_id)
        return self._spaces[key]

    def get_or_create_space(self, scope: str = "user", owner_id: str = "default_user", **kwargs) -> FallbackSingleFileSpaceVFS:
        return self.get_space(scope, owner_id, **kwargs)

    def list_spaces(self, scope: Optional[str] = None) -> List[Dict[str, Any]]:
        res = []
        for key, sp in self._spaces.items():
            if scope is None or sp.scope == scope:
                res.append(sp.get_summary())
        return res

    def run_playground(self, scope: str, owner_id: str, entrypoint: str = "/src/main.py", runtime: str = "auto", code_override: Optional[str] = None, args: Optional[List[str]] = None) -> Dict[str, Any]:
        sp = self.get_space(scope, owner_id)
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        code = code_override
        if not code:
            try:
                file_rec = sp.read_file(entrypoint, as_text=True)
                code = file_rec.get("content") or ""
            except Exception:
                code = "print('Hello from AgentSpace Wasm Playground!')"

        stdout = ""
        stderr = ""
        exit_code = 0
        try:
            res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=10.0)
            stdout = res.stdout
            stderr = res.stderr
            exit_code = res.returncode
        except Exception as exc:
            stderr = str(exc)
            exit_code = 1

        return {
            "run_id": run_id,
            "scope": scope,
            "owner_id": owner_id,
            "entrypoint": entrypoint,
            "runtime": runtime,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
            "synced_files": [f["path"] for f in sp.list_files()],
            "wasm_bridge": True,
        }

    def run_agent(self, scope: str, owner_id: str, prompt: str, model_alias: str = "gemini-brain", author: str = "agent") -> Dict[str, Any]:
        sp = self.get_space(scope, owner_id)
        turn_id = f"turn-{uuid.uuid4().hex[:8]}"
        reply = ""
        if self.ai_router and hasattr(self.ai_router, "dispatch_completion"):
            try:
                comp = self.ai_router.dispatch_completion(
                    alias=model_alias,
                    messages=[
                        {"role": "system", "content": f"You are an AI engineer working inside the .space VFS ({scope}:{owner_id})."},
                        {"role": "user", "content": prompt},
                    ],
                )
                reply = comp.get("choices", [{}])[0].get("message", {}).get("content", "")
            except Exception as e:
                reply = f"[Agent dispatch simulated fallback: {e}]"
        if not reply:
            reply = f"Simulated Agent Turn for prompt: '{prompt}'. Space currently has {len(sp.list_files())} files."

        return {
            "turn_id": turn_id,
            "scope": scope,
            "owner_id": owner_id,
            "prompt": prompt,
            "model_alias": model_alias,
            "model": model_alias,
            "reply": reply,
            "author": author,
            "created_at": time.time(),
        }

    def fork_file(self, from_scope: str, from_id: str, to_scope: str, to_id: str, path: str, dest_path: Optional[str] = None, updated_by: str = "fork") -> Dict[str, Any]:
        src = self.get_space(from_scope, from_id)
        dst = self.get_space(to_scope, to_id)
        rec = src.read_file(path, as_text=False)
        d_path = dest_path or path
        return dst.write_file(d_path, base64.b64decode(rec["content_b64"]), mime_type=rec.get("mime_type"), updated_by=updated_by)

    def fork_space(self, from_scope: str, from_id: str, to_scope: str, to_id: str) -> Dict[str, Any]:
        src = self.get_space(from_scope, from_id)
        dst = self.get_space(to_scope, to_id)
        forked = []
        for f in src.list_files():
            rec = src.read_file(f["path"], as_text=False)
            dst.write_file(f["path"], base64.b64decode(rec["content_b64"]), mime_type=rec.get("mime_type"), updated_by="fork")
            forked.append(f["path"])
        return {
            "from_scope": from_scope,
            "from_id": from_id,
            "to_scope": to_scope,
            "to_id": to_id,
            "files_forked": forked,
            "count": len(forked),
        }

    def export_space(self, scope: str, owner_id: str) -> bytes:
        sp = self.get_space(scope, owner_id)
        return sp.export_space_bytes()

    def export_space_b64(self, scope: str, owner_id: str) -> str:
        b = self.export_space(scope, owner_id)
        return base64.b64encode(b).decode("ascii")

    def import_space(self, scope: str, owner_id: str, space_bytes_or_b64: Any) -> Dict[str, Any]:
        if isinstance(space_bytes_or_b64, str):
            raw = base64.b64decode(space_bytes_or_b64)
        else:
            raw = bytes(space_bytes_or_b64)
        sp = self.get_space(scope, owner_id)
        return sp.import_space_bytes(raw)

    def get_wasm_manifest(self) -> Dict[str, Any]:
        return {
            "artcraft_apps": ARTCRAFT_WASM_APPS,
            "wasm_runtimes": WASM_RUNTIMES,
            "contract": WASM_POSTMESSAGE_CONTRACT,
        }


_space_manager = None


def _get_space_manager():
    global _space_manager
    if _space_manager is not None:
        return _space_manager
    try:
        from iot_federated_agent_memory.agent_space import AgentSpaceManager
        _space_manager = AgentSpaceManager(ai_router=router)
    except Exception:
        _space_manager = FallbackAgentSpaceManager(ai_router=router)
    return _space_manager


space_manager = _get_space_manager()

# Brain Arena: one context store per (account, brain), see arena_context.py.
arena_context = ArenaContextRegistry()

# Moderator registry for space/mesh bans & reported digital artifacts
banned_peers: Dict[str, Dict[str, Any]] = {}
reported_artifacts: List[Dict[str, Any]] = []

ARENA_CONTEXT_API = ArenaContextAPI(
    arena_context, lambda: account_registry, banned_peers=banned_peers, space_manager_getter=_get_space_manager,
)

_pty_manager = None


def _get_pty_manager():
    global _pty_manager
    if _pty_manager is None:
        from iot_federated_agent_memory.pty_sessions import PTYSessionManager
        _pty_manager = PTYSessionManager()
    return _pty_manager


def _get_palace_snippets(limit: int = 8) -> List[Dict[str, Any]]:
    try:
        res = arena_context.list_palace_concepts(limit=limit)
        return list(res.get("concepts") or [])
    except Exception:
        return []


def _ws_recv_exact(sock: Any, count: int) -> Optional[bytes]:
    buf = bytearray()
    while len(buf) < count:
        try:
            chunk = sock.recv(count - len(buf))
        except OSError:
            return None
        if not chunk:
            return None
        buf.extend(chunk)
    return bytes(buf)


def _ws_send_frame(sock: Any, opcode: int, payload: bytes, lock: threading.Lock) -> bool:
    length = len(payload)
    if length < 126:
        header = bytes([0x80 | opcode, length])
    elif length <= 0xFFFF:
        header = struct.pack("!BBH", 0x80 | opcode, 126, length)
    else:
        header = struct.pack("!BBQ", 0x80 | opcode, 127, length)
    try:
        with lock:
            sock.sendall(header + payload)
        return True
    except OSError:
        return False


def _ws_recv_frame(sock: Any) -> Optional[Tuple[int, bytes]]:
    chunks: List[bytes] = []
    first_opcode: Optional[int] = None
    while True:
        hdr = _ws_recv_exact(sock, 2)
        if not hdr:
            return None
        fin = (hdr[0] & 0x80) != 0
        opcode = hdr[0] & 0x0F
        if first_opcode is None:
            first_opcode = opcode
        masked = (hdr[1] & 0x80) != 0
        length = hdr[1] & 0x7F
        if length == 126:
            ext = _ws_recv_exact(sock, 2)
            if not ext:
                return None
            length = struct.unpack("!H", ext)[0]
        elif length == 127:
            ext = _ws_recv_exact(sock, 8)
            if not ext:
                return None
            length = struct.unpack("!Q", ext)[0]
        if length > 2 * 1024 * 1024:
            return None
        mask = _ws_recv_exact(sock, 4) if masked else None
        if masked and not mask:
            return None
        raw = _ws_recv_exact(sock, length) if length else b""
        if raw is None:
            return None
        if masked and mask:
            raw = bytes(b ^ mask[i % 4] for i, b in enumerate(raw))
        chunks.append(raw)
        if fin:
            return (first_opcode if first_opcode is not None else opcode, b"".join(chunks))

HTML_UI = MESH_OS_HTML_UI

# Paths that open the shell straight into one window (mesh_os_ui.py maps each to its window id;
# zen_shell.py keeps the classic desktop for them). Keep the three lists in sync.
SINGLE_WINDOW_ROUTES = frozenset({
    "/tv", "/call", "/comms", "/chat", "/copilot", "/ai", "/home", "/arena", "/terminal", "/billing", "/tokens",
    "/board", "/cyberspace", "/space", "/files", "/finder", "/agentspace",
    "/quests", "/rewards", "/network", "/workstation", "/3dstudio", "/browser", "/localhost",
})


def _get_html_Entry(html_str: str):
    key = hashlib.sha256(html_str.encode("utf-8")).hexdigest()[:16]
    entry = _html_cache.get(key)
    if entry is None:
        raw = html_str.encode("utf-8")
        gz = gzip.compress(raw, compresslevel=6)
        etag = f'"{key}"'
        entry = (raw, gz, etag)
        _html_cache[key] = entry
    return entry


class MeshGatewayHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _accepts_gzip(self) -> bool:
        enc = self.headers.get("Accept-Encoding", "")
        return "gzip" in enc.lower()

    def _write_body(self, payload: bytes) -> None:
        if getattr(self, "command", "GET") != "HEAD" and payload:
            self.wfile.write(payload)

    def _send_html(self, html_str: str, code: int = 200) -> None:
        raw, gz, etag = _get_html_Entry(html_str)
        if self.headers.get("If-None-Match") == etag:
            self.send_response(304)
            self.send_header("ETag", etag)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        use_gzip = self._accepts_gzip()
        body = gz if use_gzip else raw
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("ETag", etag)
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Vary", "Accept-Encoding")
        if use_gzip:
            self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self._write_body(body)

    def _send_empty(self, code: int = 204) -> None:
        self.send_response(code)
        self.send_header("Content-Length", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def _send_file(self, file_path: str) -> None:
        import mimetypes
        ctype, _ = mimetypes.guess_type(file_path)
        if not ctype:
            if file_path.endswith(".woff2"):
                ctype = "font/woff2"
            elif file_path.endswith(".svg"):
                ctype = "image/svg+xml"
            elif file_path.endswith(".png"):
                ctype = "image/png"
            elif file_path.endswith(".wav"):
                ctype = "audio/wav"
            elif file_path.endswith(".css"):
                ctype = "text/css"
            elif file_path.endswith(".js"):
                ctype = "application/javascript"
            elif file_path.endswith(".json"):
                ctype = "application/json"
            else:
                ctype = "application/octet-stream"
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self._write_body(content)
        except Exception:
            self._send_empty(404)

    def _send_json(self, data, code=200, headers=None):
        raw = json.dumps(data, separators=(",", ":")).encode("utf-8")
        use_gzip = self._accepts_gzip() and len(raw) >= 512
        body = gzip.compress(raw, compresslevel=5) if use_gzip else raw
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        if use_gzip:
            self.send_header("Content-Encoding", "gzip")
        self.send_header("Vary", "Accept-Encoding")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-NanoGPT-Api-Key, X-Gemini-Api-Key")
        for hk, hv in (headers or []):
            self.send_header(hk, hv)
        self.end_headers()
        self._write_body(body)

    def _send_private_json(self, data, code=200):
        """JSON for local-only endpoints: no CORS header and never cached."""
        raw = json.dumps(data, separators=(",", ":")).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self._write_body(raw)

    def _drive_mirror_allowed(self) -> bool:
        return drive_mirror.request_allowed(
            self.client_address[0] if self.client_address else "",
            self.headers.get("Host") or "",
            self.headers.get("X-Forwarded-For") or "",
        )

    def _drive_status_payload(self, include_root: bool = False) -> Dict[str, Any]:
        """Build local drive-mirror status dictionary shared by /api/drive/status and /api/workstation/status."""
        allowed = self._drive_mirror_allowed()
        payload: Dict[str, Any] = {
            "available": allowed,
            "on_railway": drive_mirror.running_on_railway(),
            "fallback": None if allowed else "browser-folder-picker",
        }
        if include_root:
            root_path = drive_mirror.mirror_root() if allowed else None
            payload["connected"] = allowed
            payload["root_name"] = (os.path.basename(root_path) or root_path) if root_path else None
        return payload

    def _read_json_body(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b""
        if not post_data:
            return {}
        data = json.loads(post_data.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    def _resolve_space_identity(self, data: Dict[str, Any]) -> Tuple[str, str, str]:
        scope = data.get("scope") or "user"
        owner_id = data.get("owner_id") or data.get("peer_id") or data.get("topic_id") or "default_user"
        author = data.get("author") or data.get("updated_by") or "user"
        return str(scope), str(owner_id), str(author)

    def _resolve_space_query(self, query: Dict[str, List[str]]) -> Tuple[str, str]:
        scope = query.get("scope", ["user"])[0]
        owner_id = query.get("owner_id", query.get("peer_id", query.get("topic_id", ["default_user"])))[0]
        return scope, owner_id

    def _reject_if_banned(self, *peer_ids: str) -> bool:
        for pid in peer_ids:
            if pid and pid in banned_peers:
                self._send_json(
                    {"error": f"Banned: {banned_peers[pid].get('reason', 'Policy violation')}", "banned": True},
                    403,
                )
                return True
        return False

    def _get_notes_editor(self, scope: str, owner_id: str) -> Tuple[Any, SpaceNotesEditor]:
        sm = _get_space_manager()
        sp = sm.get_or_create_space(scope, owner_id)
        sm_router = getattr(sm, "ai_router", None)
        ai_r = router
        if sm_router is not None and sm_router is not _DEFAULT_ROUTER and router is _DEFAULT_ROUTER:
            ai_r = sm_router
        return sp, SpaceNotesEditor(sp, ai_router=ai_r)

    def _handle_space_notes_post(self, path: str) -> None:
        """Dispatch POST /api/space/notes* endpoints backed by SpaceNotesEditor."""
        if path not in (
            "/api/space/notes",
            "/api/space/notes/propose",
            "/api/space/notes/commit",
            "/api/space/notes/revert",
        ):
            self._send_empty(404)
            return
        try:
            data = self._read_json_body()
            scope, owner_id, author = self._resolve_space_identity(data)
            if self._reject_if_banned(owner_id, author):
                return
            sp, editor = self._get_notes_editor(scope, owner_id)

            if path == "/api/space/notes":
                action = str(data.get("action") or "add").strip().lower()
                if action == "add":
                    raw_kind = str(data.get("kind") or "observation").strip().lower()
                    note_kind = "edit" if raw_kind == "change" else raw_kind
                    note = editor.add_note(
                        body=data.get("body", ""),
                        kind=note_kind,
                        path=data.get("path"),
                        author=author,
                    )
                    self._send_json({"note": note}, 200)
                elif action == "drop":
                    note_id = data.get("note_id")
                    if not note_id:
                        self._send_json({"error": "Missing 'note_id'"}, 400)
                        return
                    self._send_json(editor.drop_note(str(note_id)), 200)
                else:
                    self._send_json({"error": f"Unknown notes action '{action}'"}, 400)
                return

            if path == "/api/space/notes/propose":
                model_alias = data.get("model") or data.get("model_alias") or "nanogpt/TEE/deepseek-v4.1-flash"
                note_ids = data.get("note_ids")
                instruction = data.get("instruction") or ""
                note_body = data.get("note_body")
                inline_note = None
                if note_body is not None:
                    if not str(note_body).strip():
                        self._send_json({"error": "Note body cannot be empty"}, 400)
                        return
                    raw_kind = str(data.get("kind") or "edit").strip().lower()
                    inline_kind = "edit" if raw_kind == "change" else raw_kind
                    inline_note = editor.add_note(
                        body=str(note_body),
                        kind=inline_kind,
                        path=data.get("path"),
                        author=author,
                    )
                    if isinstance(note_ids, list) and inline_note["note_id"] not in note_ids:
                        note_ids = list(note_ids) + [inline_note["note_id"]]
                plan = editor.propose(
                    model_alias=model_alias,
                    note_ids=note_ids,
                    instruction=instruction,
                )
                diff_preview = _compute_plan_diff_preview(sp, plan.get("edits", []))
                resp: Dict[str, Any] = {**plan, "diff_preview": diff_preview}
                if inline_note is not None:
                    resp["note"] = inline_note
                self._send_json(resp, 200)
                return

            if path == "/api/space/notes/commit":
                plan_id = data.get("plan_id")
                if not plan_id:
                    self._send_json({"error": "Missing 'plan_id'"}, 400)
                    return
                commit_author = data.get("author") or "notes-editor"
                self._send_json(editor.commit(str(plan_id), author=commit_author), 200)
                return

            version_id = data.get("version_id")
            if not version_id:
                self._send_json({"error": "Missing 'version_id'"}, 400)
                return
            revert_author = data.get("author") or "notes-editor"
            self._send_json(editor.revert(str(version_id), author=revert_author), 200)
        except (KeyError, FileNotFoundError) as exc:
            msg = exc.args[0] if isinstance(exc, KeyError) and exc.args else str(exc)
            self._send_json({"error": msg}, 404)
        except EditPlanError as exc:
            msg = str(exc)
            lower = msg.lower()
            code = (
                409
                if (path.endswith("/commit") or path.endswith("/revert"))
                and ("changed" in lower or "already" in lower)
                else 400
            )
            self._send_json({"error": msg}, code)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, 400)
        except Exception as exc:
            self._send_json({"error": str(exc)}, 500)

    def _handle_drive_get(self, parsed) -> None:
        """Read-only hard-drive mirror for the Ranger VFS (local server only)."""
        if parsed.path == "/api/drive/status":
            self._send_private_json(self._drive_status_payload(), 200)
            return
        if not self._drive_mirror_allowed():
            self._send_private_json({
                "error": "Drive mirror is only available when TinCan runs on this computer.",
                "available": False,
                "fallback": "browser-folder-picker",
            }, 403)
            return
        query = parse_qs(parsed.query)
        root = drive_mirror.mirror_root()
        rel = query.get("path", ["/"])[0]
        try:
            if parsed.path == "/api/drive/mirror":
                depth = max(1, min(int(query.get("depth", [drive_mirror.DEFAULT_MAX_DEPTH])[0]), 5))
                self._send_private_json(drive_mirror.gather_mirror(root, max_depth=depth), 200)
            elif parsed.path == "/api/drive/ls":
                self._send_private_json(drive_mirror.list_dir(root, rel), 200)
            elif parsed.path == "/api/drive/file":
                self._send_private_json(drive_mirror.read_text_preview(root, rel), 200)
            elif parsed.path == "/api/drive/raw":
                abs_path, size, mime = drive_mirror.open_raw(root, rel)
                mime = guess_mime_type(abs_path, mime)
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(size))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                if query.get("download", ["0"])[0] == "1":
                    fname = os.path.basename(abs_path).replace('"', "")
                    self.send_header("Content-Disposition", f'attachment; filename="{fname}"')
                self.end_headers()
                if self.command != "HEAD":
                    for chunk in drive_mirror.iter_file_chunks(abs_path):
                        self.wfile.write(chunk)
            else:
                self._send_private_json({"error": "Not found"}, 404)
        except drive_mirror.MirrorAccessError as exc:
            self._send_private_json({"error": str(exc)}, 403)
        except (FileNotFoundError, NotADirectoryError):
            self._send_private_json({"error": f"Not found: {rel}"}, 404)
        except Exception as exc:  # pragma: no cover - defensive
            self._send_private_json({"error": str(exc)}, 500)

    def do_HEAD(self):
        self.do_GET()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-NanoGPT-Api-Key, X-Gemini-Api-Key")
        self.end_headers()

    def _client_key(self) -> str:
        fwd = (self.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
        return fwd or (self.client_address[0] if self.client_address else "unknown")

    # ------------------------------------------------------------------
    # Server-side sign-in session (HttpOnly cookie, or Bearer for the CLI)
    # ------------------------------------------------------------------
    SESSION_COOKIE = "tincan_session"

    def _session_token(self) -> str:
        auth = self.headers.get("Authorization") or ""
        if auth.lower().startswith("bearer "):
            return auth[7:].strip()
        cookie_header = self.headers.get("Cookie") or ""
        if cookie_header:
            try:
                jar = SimpleCookie()
                jar.load(cookie_header)
                if self.SESSION_COOKIE in jar:
                    return jar[self.SESSION_COOKIE].value
            except Exception:
                return ""
        return ""

    def _session_account(self):
        """The signed-in account for this request, resolved on the server.

        Never derived from a client-sent peer_id.
        """
        token = self._session_token()
        return account_registry.resolve_session(token) if token else None

    def _is_admin_request(self) -> bool:
        """Verify X-Admin-Key header using constant-time digest comparison."""
        admin_key = self.headers.get("X-Admin-Key", "")
        return bool(TINCAN_ADMIN_KEY and admin_key and hmac.compare_digest(admin_key, TINCAN_ADMIN_KEY))

    def _session_cookie_headers(self, account_peer_id: str):
        token = account_registry.create_session(account_peer_id)
        proto = (self.headers.get("X-Forwarded-Proto") or "").split(",")[0].strip().lower()
        secure = "; Secure" if proto == "https" else ""
        max_age = int(account_registry.SESSION_TTL_SECONDS)
        return [("Set-Cookie", f"{self.SESSION_COOKIE}={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age={max_age}{secure}")]

    ARENA_MAX_TOKENS = 1024

    def _arena_error(self, err: "ArenaBillingError") -> None:
        self._send_json({"error": err.message, "code": err.code, **err.extra}, err.status)

    def _arena_account_or_401(self):
        account = self._session_account()
        if not account:
            self._send_json({
                "error": "Sign in to duel. Brain Arena duels are billed to your own account.",
                "code": "sign_in_required",
            }, 401)
            return None
        if account["peer_id"] in banned_peers:
            self._send_json({"error": f"Banned: {banned_peers[account['peer_id']].get('reason', 'Policy violation')}", "banned": True}, 403)
            return None
        return account

    def _handle_arena_match(self, data) -> None:
        account = self._arena_account_or_401()
        if not account:
            return
        model_a, model_b = data.get("model_a"), data.get("model_b")
        for m in (model_a, model_b):
            if not router.is_arena_model_allowed(m):
                self._send_json({"error": f"Model not allowed in the Brain Arena: {m}"}, 400)
                return
        try:
            match = account_registry.create_arena_match(
                account["peer_id"], model_a, model_b, prompt_preview=str(data.get("prompt") or "")[:80])
        except ArenaBillingError as ae:
            self._arena_error(ae)
            return
        self._send_json({"status": "match_created", "match": match,
                         "token_balance": account["token_balance"]}, 201)

    def _handle_arena_chat(self, data, model_alias) -> None:
        account = self._arena_account_or_401()
        if not account:
            return
        prompt = data.get("prompt") or ""
        messages = data.get("messages") or [{"role": "user", "content": prompt or "Hello from the Brain Arena"}]
        arena_ctx = None
        if data.get("agent_id"):
            # This brain's own files (its .space + linked drive files) go in
            # before the side is authorized, so they count toward its cost.
            try:
                messages, arena_ctx = ARENA_CONTEXT_API.inject_context(account, data, model_alias, messages)
            except ContextStoreError as ce:
                self._send_json({"error": ce.message, "code": ce.code}, ce.status)
                return
        prompt_text = " ".join(str(m.get("content", "")) for m in messages if isinstance(m, dict))
        max_tokens = max(1, min(int(data.get("max_tokens", 512)), self.ARENA_MAX_TOKENS))
        side = str(data.get("arena_side") or data.get("side") or "").upper()
        match_id = str(data.get("match_id") or "")
        required = account_registry.estimate_side_tokens(prompt_text, max_tokens)
        try:
            account_registry.authorize_arena_side(account["peer_id"], match_id, side, model_alias, required)
        except ArenaBillingError as ae:
            self._arena_error(ae)
            return
        completion = router.dispatch_completion(
            alias=model_alias,
            messages=messages,
            temperature=float(data.get("temperature", 0.7)),
            max_tokens=max_tokens,
        )
        mesh_os.record_flight(account["peer_id"], model_alias, kind="ai_prompt", label=model_alias)
        usage = completion.get("usage", {}) or {}
        p_toks = int(usage.get("prompt_tokens", 0))
        c_toks = int(usage.get("completion_tokens", 0))
        t_toks = int(usage.get("total_tokens", p_toks + c_toks))
        cost = float(completion.get("cost_usd") or usage.get("cost") or 0.0)
        try:
            completion["billing"] = account_registry.bill_tokens(
                peer_id=account["peer_id"], prompt_tokens=p_toks, completion_tokens=c_toks,
                total_tokens=t_toks, cost_usd=cost, model=model_alias,
                arena_match_id=match_id, arena_side=side,
            )
        except ArenaBillingError as ae:
            self._arena_error(ae)
            return
        completion["arena"] = {"match_id": match_id, "side": side}
        if arena_ctx is not None:
            completion["arena_context"] = arena_ctx
        self._send_json(completion, 200)

    def _handle_passkey_post(self, path: str) -> None:
        content_length = int(self.headers.get("Content-Length", 0) or 0)
        if content_length > 64 * 1024:
            self._send_json({"error": "Request too large"}, 413)
            return
        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data.decode("utf-8")) if post_data else {}
            if not isinstance(data, dict):
                raise PasskeyError("bad_request", "Invalid request.")
            peer_id = str(data.get("peer_id") or "").strip()
            host = self.headers.get("X-Forwarded-Host") or self.headers.get("Host", "")
            if path == "/api/passkey/register/options":
                rp_id, origins = resolve_relying_party(host)
                out = passkey_auth.begin_registration(peer_id, str(data.get("enroll_token") or ""), rp_id, origins)
                self._send_json(out, 200)
            elif path == "/api/passkey/register/verify":
                account = passkey_auth.finish_registration(peer_id, str(data.get("challenge_id") or ""), data.get("credential"))
                self._send_json({"status": "passkey_registered", "account": account, "signed_in": True}, 200,
                                headers=self._session_cookie_headers(account["peer_id"]))
            elif path == "/api/passkey/login/options":
                rp_id, origins = resolve_relying_party(host)
                out = passkey_auth.begin_authentication(peer_id, rp_id, origins, email=str(data.get("email") or ""))
                self._send_json(out, 200)
            elif path == "/api/passkey/login/verify":
                account = passkey_auth.finish_authentication(peer_id, str(data.get("challenge_id") or ""), data.get("credential"))
                self._send_json({"status": "signed_in", "account": account}, 200,
                                headers=self._session_cookie_headers(account["peer_id"]))
            elif path == "/api/account/recovery/request":
                out = passkey_auth.request_recovery_code(str(data.get("email") or ""), client_key=self._client_key())
                self._send_json(out, 200)
            elif path == "/api/account/recovery/verify":
                token = passkey_auth.verify_recovery_code(str(data.get("email") or ""), str(data.get("code") or ""))
                self._send_json({"status": "code_verified", "enroll_token": token}, 200)
        except PasskeyError as pe:
            self._send_json({"error": pe.message, "code": pe.code}, pe.status)
        except Exception:
            self._send_json({"error": "Something went wrong with passkey sign-in. Please try again.", "code": "server_error"}, 500)

    def do_PUT(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/localhost/"):
            return proxy_localhost_port(self, "PUT", parsed.path, parsed.query)
        self._send_json({"error": "Method not allowed"}, 405)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/localhost/"):
            return proxy_localhost_port(self, "DELETE", parsed.path, parsed.query)
        self._send_json({"error": "Method not allowed"}, 405)

    def do_PATCH(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/localhost/"):
            return proxy_localhost_port(self, "PATCH", parsed.path, parsed.query)
        self._send_json({"error": "Method not allowed"}, 405)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/localhost/"):
            return proxy_localhost_port(self, "POST", parsed.path, parsed.query)
        if ARENA_CONTEXT_API.handle_post(self, parsed):
            return
        if parsed.path == "/api/tincan/send":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode("utf-8"))
                result = tincan_relay.send(payload)
                sender_id = payload.get("from") or payload.get("sender") or "peer"
                recipient_id = payload.get("to") or payload.get("recipient") or "relay"
                mesh_os.award_xp(sender_id, "sealed_courier")
                mesh_os.record_flight(sender_id, recipient_id, kind="envelope", label="X25519 Sealed")
                self._send_json(result, 200)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = data.get("peer_id") or "peer"
                if peer_id in banned_peers:
                    self._send_json({"error": f"Banned: {banned_peers[peer_id].get('reason', 'Policy violation')}", "banned": True}, 403)
                    return
                model_alias = data.get("model", "gemini-brain")
                if data.get("arena") and not router.is_arena_model_allowed(model_alias):
                    self._send_json({"error": f"Model not allowed in the Brain Arena: {model_alias}"}, 400)
                    return
                if data.get("arena"):
                    # Duel sides are billed to the signed-in account only. Never the shared bucket.
                    self._handle_arena_chat(data, model_alias)
                    return
                prompt = data.get("prompt")
                messages = data.get("messages")
                if not messages:
                    if not prompt:
                        prompt = "Hello from TinCan 2 / IoT Federated Mesh!"
                    messages = [{"role": "user", "content": prompt}]
                acct = account_registry.get_account_by_peer(peer_id)
                if acct and acct.get("token_balance", 0) <= 0:
                    self._send_json({"error": "Insufficient tokens: balance is 0. Top up to continue."}, 402)
                    return
                # Per-thread workspace: mint a UUID-4 hex id on first turn, or
                # continue only if the client thread_id already exists for this
                # peer. A missing/blank peer_id uses the "anonymous" bucket.
                # An unsanitary peer_id skips FS setup without aborting chat.
                raw_peer_id = data.get("peer_id")
                thread_error = None
                thread_id = None
                if raw_peer_id is None or (isinstance(raw_peer_id, str) and not raw_peer_id.strip()):
                    fs_peer_id = ANONYMOUS_PEER_ID
                else:
                    fs_peer_id = raw_peer_id
                try:
                    sanitize_peer_id(fs_peer_id)
                    tdir = start_or_continue_thread(
                        fs_peer_id,
                        data.get("thread_id"),
                        template=data.get("template") or data.get("kind"),
                    )
                    thread_id = tdir.name
                except ThreadFsError as te:
                    thread_error = str(te)
                space_ctx_meta = None
                if data.get("use_space_context") or data.get("scope") or data.get("owner_id"):
                    try:
                        from iot_federated_agent_memory.agent_space import build_space_context_summary

                        sp_scope = (data.get("scope") or "user").strip()
                        sp_owner = (data.get("owner_id") or data.get("peer_id") or "default").strip()
                        sp_vfs = _get_space_manager().get_space(scope=sp_scope, owner_id=sp_owner)
                        ctx_summary = build_space_context_summary(
                            sp_vfs,
                            active_file=data.get("active_file"),
                            palace_snippets=_get_palace_snippets(limit=8),
                            ai_router=router,
                            include_capabilities=True,
                        )
                        if ctx_summary.get("text"):
                            messages = [
                                {
                                    "role": "system",
                                    "content": (
                                        "Use this live TinCan platform capability manifest, .space VFS, and Context Palace "
                                        "context when answering about TinCan's models, tools, files, code, or project.\n\n"
                                        + ctx_summary["text"]
                                    ),
                                },
                                *messages,
                            ]
                            space_ctx_meta = {
                                "scope": ctx_summary["scope"],
                                "owner_id": ctx_summary["owner_id"],
                                "active_file": ctx_summary["active_file"],
                                "files_count": ctx_summary["files_count"],
                                "merkle_root": ctx_summary["merkle_root"],
                            }
                    except Exception:
                        space_ctx_meta = None
                elif not data.get("arena"):
                    try:
                        from iot_federated_agent_memory.agent_space import build_tincan_capability_manifest

                        cap_manifest = build_tincan_capability_manifest(ai_router=router, include_tool_protocol=False)
                        if cap_manifest and not any(m.get("role") == "system" for m in messages):
                            messages = [{"role": "system", "content": cap_manifest}, *messages]
                    except Exception:
                        pass
                completion = router.dispatch_completion(
                    alias=model_alias,
                    messages=messages,
                    temperature=float(data.get("temperature", 0.7)),
                    max_tokens=int(data.get("max_tokens", 512)),
                )
                if space_ctx_meta is not None:
                    completion["space_context"] = space_ctx_meta
                peer_id = data.get("peer_id") or "peer"
                mesh_os.record_flight(peer_id, model_alias, kind="ai_prompt", label=model_alias)
                usage = completion.get("usage", {})
                p_toks = int(usage.get("prompt_tokens", 0))
                c_toks = int(usage.get("completion_tokens", 0))
                t_toks = int(usage.get("total_tokens", p_toks + c_toks))
                cost = float(completion.get("cost_usd") or usage.get("cost") or 0.0)
                try:
                    billing_receipt = account_registry.bill_tokens(
                        peer_id=peer_id,
                        prompt_tokens=p_toks,
                        completion_tokens=c_toks,
                        total_tokens=t_toks,
                        cost_usd=cost,
                        model=model_alias,
                        # Charge the balance down to zero for the final request; the
                        # pre-dispatch check above refuses the next one at 402.
                        allow_overage=True,
                    )
                    completion["billing"] = billing_receipt
                except Exception as b_err:
                    completion["billing_error"] = str(b_err)
                if not thread_error:
                    completion["thread_id"] = thread_id
                else:
                    completion["thread_error"] = thread_error
                self._send_json(completion, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/models/set":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                alias = data.get("alias")
                new_model = data.get("model")
                display_name = data.get("display_name")
                gateway = data.get("gateway")
                if not alias or not new_model:
                    self._send_json({"error": "Missing 'alias' or 'model'"}, 400)
                    return
                try:
                    updated_config = router.set_model(alias, new_model, display_name, gateway=gateway)
                except TypeError:
                    updated_config = router.set_model(alias, new_model, display_name)
                gateway_name = (
                    router._provider_gateway(updated_config)
                    if hasattr(router, "_provider_gateway")
                    else ("nanogpt" if updated_config.api_key_env == "NANOGPT_API_KEY" else "openrouter")
                )
                self._send_json({
                    "status": "updated",
                    "alias": alias,
                    "model": updated_config.model_alias,
                    "display_name": updated_config.display_name,
                    "endpoint": updated_config.endpoint,
                    "gateway": gateway_name,
                }, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/webrtc/register":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = (data.get("peer_id") or "").strip()
                display_name = (data.get("display_name") or "").strip()
                if not peer_id:
                    self._send_json({"error": "Missing 'peer_id'"}, 400)
                    return
                acc = account_registry.get_account_by_peer(peer_id)
                if acc:
                    fn = (acc.get("full_name") or "").strip()
                    un = (acc.get("username") or "").strip()
                    if fn and un:
                        display_name = f"{fn} (@{un})"
                    elif fn:
                        display_name = fn

                # Server-Side Mandatory Identity Gate: Reject unidentified anonymous room entries
                is_unidentified_default = peer_id.startswith("default-") and (
                    not display_name or display_name.startswith("default (") or display_name == peer_id
                )
                is_unidentified_browser = (
                    peer_id.startswith("peer-")
                    and not peer_id.startswith(("peer-primary-", "peer-secondary-", "peer-workstation-", "peer-test-"))
                    and not acc
                    and (not display_name or display_name == peer_id or display_name.startswith("peer-"))
                )
                if is_unidentified_default or is_unidentified_browser:
                    self._send_json(
                        {
                            "error": "Mandatory Identity Gate: You must identify yourself (Full Name, Username, Email & Phone) before entering the room.",
                            "require_identity": True,
                        },
                        403,
                    )
                    return

                if not display_name:
                    display_name = peer_id
                session = relay.register_peer(
                    peer_id=peer_id,
                    display_name=display_name,
                    udp_address="redacted",
                    udp_port=int(data.get("udp_port", 50000)),
                    room=data.get("room", "main"),
                    has_video=bool(data.get("has_video", False)),
                    has_audio=bool(data.get("has_audio", False)),
                    has_screen=bool(data.get("has_screen", False)),
                )
                mesh_os.award_xp(peer_id, "workstation_handshake", display_name=display_name)
                mesh_os.record_flight(peer_id, "relay", kind="webrtc", label="UDP Handshake")
                self._send_json({
                    "status": "registered",
                    "peer_id": session.peer_id,
                    "display_name": session.display_name,
                    "room": session.room,
                    "peers": relay.get_room_peers(session.room),
                }, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/webrtc/signal":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                sender_id = data.get("from") or data.get("sender_id")
                receiver_id = data.get("to") or data.get("receiver_id") or "*"
                signal_type = data.get("type") or data.get("signal_type")
                payload = data.get("payload") or {}
                room = data.get("room", "main")
                if not sender_id or not signal_type:
                    self._send_json({"error": "Missing 'from' or 'type'"}, 400)
                    return
                msg = relay.exchange_signal(
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    signal_type=signal_type,
                    sdp_or_candidate=payload,
                    room=room,
                )
                self._send_json({"status": "signaled", "signal": msg}, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path in ("/api/webrtc/leave", "/api/mesh/kick"):
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = data.get("peer_id")
                room = data.get("room", "main")
                if not peer_id:
                    self._send_json({"error": "Missing 'peer_id'"}, 400)
                    return
                left = relay.leave_peer(peer_id)
                relay.exchange_signal(peer_id, "*", "hangup", {"peer_id": peer_id}, room=room)
                with mesh_os._lock:
                    if peer_id in mesh_os.cursors:
                        del mesh_os.cursors[peer_id]
                self._send_json({"status": "left", "peer_id": peer_id, "removed": left}, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/playlist/add":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                raw_input = data.get("url") or data.get("input") or data.get("video_id") or data.get("embed")
                if not raw_input:
                    self._send_json({"error": "Missing 'url', 'input', or 'video_id'"}, 400)
                    return
                added = playlist.add_video(
                    raw_input=raw_input,
                    title=data.get("title"),
                    creator=data.get("creator"),
                    category=data.get("category", "spotlight"),
                    duration_seconds=int(data.get("duration_seconds", 35)),
                )
                peer_id = data.get("peer_id") or "curator-peer"
                mesh_os.award_xp(peer_id, "curator_drop")
                self._send_json({
                    "status": "added",
                    "item": added,
                    "playlist": playlist.get_playlist(),
                }, 200)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/playlist/remove":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                vid = data.get("id") or data.get("video_id")
                if not vid:
                    self._send_json({"error": "Missing 'id' or 'video_id'"}, 400)
                    return
                removed = playlist.remove_video(vid)
                self._send_json({
                    "status": "removed" if removed else "not_found",
                    "playlist": playlist.get_playlist(),
                }, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/playlist/update":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                vid = data.get("id") or data.get("video_id")
                if not vid:
                    self._send_json({"error": "Missing 'id' or 'video_id'"}, 400)
                    return
                updated = playlist.update_video(
                    video_id_or_id=vid,
                    title=data.get("title"),
                    creator=data.get("creator"),
                    category=data.get("category"),
                    duration_seconds=data.get("duration_seconds"),
                    cite_url=data.get("cite_url"),
                    embed_url=data.get("embed_url"),
                )
                if updated:
                    sponsor_manager.sync_from_playlist([asdict(it) for it in playlist.items])
                    self._send_json({
                        "status": "updated",
                        "item": updated,
                        "playlist": playlist.get_playlist(),
                    }, 200)
                else:
                    self._send_json({"error": "Video not found", "video_id": vid}, 404)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/sponsors/add":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                if not data.get("name"):
                    self._send_json({"error": "Missing sponsor 'name'"}, 400)
                    return
                added = sponsor_manager.add_sponsor(data)
                self._send_json({
                    "status": "added",
                    "sponsor": added,
                    "state": sponsor_manager.get_state(),
                }, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/sponsors/update":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                s_id = data.get("id")
                if not s_id:
                    self._send_json({"error": "Missing sponsor 'id'"}, 400)
                    return
                updated = sponsor_manager.update_sponsor(s_id, data)
                if updated:
                    self._send_json({
                        "status": "updated",
                        "sponsor": updated,
                        "state": sponsor_manager.get_state(),
                    }, 200)
                else:
                    self._send_json({"error": "Sponsor not found", "id": s_id}, 404)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/sponsors/remove":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                s_id = data.get("id")
                if not s_id:
                    self._send_json({"error": "Missing sponsor 'id'"}, 400)
                    return
                removed = sponsor_manager.remove_sponsor(s_id)
                self._send_json({
                    "status": "removed" if removed else "not_found",
                    "id": s_id,
                    "state": sponsor_manager.get_state(),
                }, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/mesh/cursor":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = (data.get("peer_id") or "peer").strip()
                display_name = (data.get("display_name") or "").strip()
                acc = account_registry.get_account_by_peer(peer_id)
                if acc:
                    fn = (acc.get("full_name") or "").strip()
                    un = (acc.get("username") or "").strip()
                    if fn and un:
                        display_name = f"{fn} (@{un})"
                    elif fn:
                        display_name = fn

                # Server-Side Mandatory Identity Gate: Reject unidentified browser cursors
                is_unidentified_cursor = (
                    peer_id.startswith("peer-")
                    and not peer_id.startswith(("peer-primary-", "peer-secondary-", "peer-workstation-", "peer-test-"))
                    and not acc
                    and (not display_name or display_name == peer_id or display_name.startswith("peer-"))
                )
                if is_unidentified_cursor:
                    with mesh_os._lock:
                        mesh_os.cursors.pop(peer_id, None)
                    self._send_json(
                        {
                            "error": "Mandatory Identity Gate: Please complete identity registration before entering the room.",
                            "require_identity": True,
                        },
                        403,
                    )
                    return

                cursor = mesh_os.update_cursor(
                    peer_id=peer_id,
                    x=float(data.get("x", 0.0)),
                    y=float(data.get("y", 0.0)),
                    window_id=data.get("window_id", "desktop"),
                    display_name=display_name or peer_id,
                    room=data.get("room", "main"),
                )
                self._send_json({"status": "ok", "cursor": cursor}, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/mesh/watchparty":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                wp = mesh_os.sync_watch_party(
                    peer_id=data.get("peer_id") or "peer",
                    video_idx=int(data.get("video_idx", 0)),
                    is_playing=bool(data.get("is_playing", True)),
                    current_time=float(data.get("current_time", 0.0)),
                )
                self._send_json({"status": "synced", "watch_party": wp}, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/mesh/react":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = data.get("peer_id") or "peer"
                emoji = data.get("emoji") or "🔥"
                rx = mesh_os.add_reaction(peer_id=peer_id, emoji=emoji, display_name=data.get("display_name"))
                self._send_json({"status": "reacted", "reaction": rx, "total_xp": mesh_os.total_xp}, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/mesh/quest":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = data.get("peer_id") or "peer"
                action_key = data.get("action_key") or "sealed_courier"
                is_signon = action_key in SIGNON_QUEST_KEYS
                award = mesh_os.award_xp(
                    peer_id=peer_id,
                    action_key=action_key,
                    display_name=data.get("display_name"),
                    once_per_peer=is_signon,
                )
                flight = None
                if not award.get("already_completed"):
                    flight = mesh_os.record_flight(
                        from_node=data.get("from_node") or peer_id,
                        to_node=data.get("to_node") or "relay",
                        kind=action_key,
                        label=action_key,
                    )
                self._send_json({
                    "status": "already_completed" if award.get("already_completed") else "awarded",
                    "signon_only": is_signon,
                    "award": award,
                    "flight": flight,
                }, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/mesh/arena/match":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                self._handle_arena_match(data if isinstance(data, dict) else {})
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/account/logout":
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length:
                self.rfile.read(content_length)
            token = self._session_token()
            revoked = account_registry.revoke_session(token) if token else False
            self._send_json({"status": "signed_out", "revoked": revoked}, 200, headers=[
                ("Set-Cookie", f"{self.SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"),
            ])
        elif parsed.path == "/api/mesh/arena/vote":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                feedback = str(data.get("feedback") or data.get("reason") or "").strip()[:500]
                if data.get("match_id"):
                    # A billed duel: the match record (not the client) says who played and what it cost.
                    account = self._arena_account_or_401()
                    if not account:
                        return
                    try:
                        match = account_registry.record_arena_vote(
                            account["peer_id"], str(data.get("match_id")), str(data.get("winner_side") or ""),
                            feedback=feedback)
                    except ArenaBillingError as ae:
                        self._arena_error(ae)
                        return
                    res = mesh_os.vote_arena(
                        peer_id=account["peer_id"],
                        winner_alias=match["winner_alias"],
                        prompt_preview=match["prompt_preview"][:40],
                        display_name=account.get("username") or account.get("full_name"),
                        model_a=match["model_a"],
                        model_b=match["model_b"],
                        winner_side=match["winner_side"],
                        match_id=match["match_id"],
                        cost_usd=match["total_cost_usd"],
                        tokens=match["total_tokens"],
                        feedback=feedback,
                    )
                    self._send_json({"status": "voted", **res, "match": match}, 200)
                    return
                peer_id = data.get("peer_id") or "peer"
                winner_alias = data.get("winner_alias") or "gemini-brain"
                model_a = data.get("model_a")
                model_b = data.get("model_b")
                winner_side = (data.get("winner_side") or "").upper() or None
                if model_a or model_b:
                    for m in (model_a, model_b):
                        if not router.is_arena_model_allowed(m):
                            self._send_json({"error": f"Model not allowed in the Brain Arena: {m}"}, 400)
                            return
                    if winner_side not in ("A", "B"):
                        self._send_json({"error": "winner_side must be 'A' or 'B'"}, 400)
                        return
                    winner_alias = model_a if winner_side == "A" else model_b
                res = mesh_os.vote_arena(
                    peer_id=peer_id,
                    winner_alias=winner_alias,
                    prompt_preview=data.get("prompt_preview", ""),
                    display_name=data.get("display_name"),
                    model_a=model_a,
                    model_b=model_b,
                    winner_side=winner_side,
                    feedback=feedback,
                )
                self._send_json({"status": "voted", **res}, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/moderator/ban":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = (data.get("peer_id") or "").strip()
                action = data.get("action", "ban").lower()
                reason = data.get("reason", "Moderator action: Policy violation")
                space_id = data.get("space_id", "")
                admin_id = data.get("admin_id", "moderator")

                if not peer_id:
                    self._send_json({"error": "Missing 'peer_id'"}, 400)
                    return

                if action == "unban":
                    banned_peers.pop(peer_id, None)
                    self._send_json({"status": "unbanned", "peer_id": peer_id}, 200)
                else:
                    banned_record = {
                        "peer_id": peer_id,
                        "reason": reason,
                        "space_id": space_id,
                        "banned_by": admin_id,
                        "banned_at": time.time(),
                    }
                    banned_peers[peer_id] = banned_record
                    self._send_json({"status": "banned", **banned_record}, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/moderator/report":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                reporter_id = data.get("reporter_id") or "anonymous_peer"
                reported_peer = data.get("reported_peer") or ""
                space_id = data.get("space_id") or "default_user"
                artifact_path = data.get("artifact_path") or ""
                reason = data.get("reason") or "Suspicious digital artifact"
                report_id = f"rep_{uuid.uuid4().hex[:8]}"

                content_preview = ""
                if artifact_path:
                    try:
                        sm = _get_space_manager()
                        sp = sm.get_or_create_space(scope="user", owner_id=space_id)
                        frec = sp.read_file(artifact_path, as_text=True)
                        content_preview = frec.get("content", "")[:500]
                    except Exception:
                        pass

                rep_record = {
                    "report_id": report_id,
                    "reporter_id": reporter_id,
                    "reported_peer": reported_peer,
                    "space_id": space_id,
                    "artifact_path": artifact_path,
                    "reason": reason,
                    "content_preview": content_preview,
                    "created_at": time.time(),
                    "status": "pending_review",
                }
                reported_artifacts.append(rep_record)
                self._send_json({"status": "reported", "report": rep_record}, 201)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/account/register":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = data.get("peer_id")
                name = data.get("name") or data.get("full_name")
                phone = data.get("phone") or data.get("phone_number")
                email = data.get("email")
                username = data.get("username") or name
                role = data.get("role", "Researcher / Student")
                consent_pii = bool(data.get("consent_pii", True))
                existing = account_registry.get_account_by_peer(peer_id) if (peer_id or "").strip() else None
                # New signup, or upgrading an auto-created guest placeholder (@mesh.local).
                is_new = bool((peer_id or "").strip()) and (
                    existing is None or str(existing.get("email", "")).endswith("@mesh.local")
                )
                account = account_registry.register_account(
                    peer_id=peer_id,
                    full_name=name,
                    phone_number=phone,
                    email=email,
                    username=username,
                    role=role,
                    consent_pii=consent_pii,
                )
                try:
                    mesh_os.award_xp(peer_id, "account_created")
                except Exception:
                    pass
                body = {
                    "status": "success",
                    "account": account,
                    "has_passkey": passkey_auth.has_passkey(account["peer_id"]),
                }
                extra_headers = None
                if is_new and not body["has_passkey"]:
                    # Brand-new account: allow this browser to attach its first passkey,
                    # and sign this browser in to the account it just created.
                    body["enroll_token"] = passkey_auth.issue_enrollment_grant(account["peer_id"], purpose="signup")
                    extra_headers = self._session_cookie_headers(account["peer_id"])
                    body["signed_in"] = True
                self._send_json(body, 201, headers=extra_headers)
            except EmailAlreadyRegisteredError:
                self._send_json({"error": EMAIL_EXISTS_MESSAGE, "code": "email_exists"}, 409)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception:
                self._send_json({"error": "Could not register this account right now. Please try again."}, 500)
        elif parsed.path in (
            "/api/passkey/register/options",
            "/api/passkey/register/verify",
            "/api/passkey/login/options",
            "/api/passkey/login/verify",
            "/api/account/recovery/request",
            "/api/account/recovery/verify",
        ):
            self._handle_passkey_post(parsed.path)
        elif parsed.path == "/api/ads/click":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                sponsor_id = data.get("sponsor_id", "")
                success = sponsor_manager.record_click(sponsor_id)
                self._send_json({"status": "ok", "recorded": success, "sponsor_id": sponsor_id}, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/ads/intel":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = (data.get("peer_id") or "admin-peer").strip()
                video_id = (data.get("video_id") or "ad").strip()
                title = (data.get("title") or "").strip()
                category = (data.get("category") or "ad").strip()
                metadata = data.get("metadata") or {}
                record = sponsor_manager.record_admin_intel(
                    peer_id=peer_id,
                    video_id=video_id,
                    title=title,
                    category=category,
                    metadata=metadata,
                )
                self._send_json({"status": "recorded", "intel": record}, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/account/billing/topup":
            # Operator-only manual grant. Clients can no longer credit themselves here.
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            if not self._is_admin_request():
                self._send_json({"error": "Forbidden: top-ups go through /api/billing/checkout"}, 403)
                return
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = data.get("peer_id") or ""
                result = account_registry.credit_once(
                    ref=f"admin:{secrets.token_hex(8)}", peer_id=peer_id, kind="admin_grant",
                    tokens=int(data.get("tokens", 0)), amount_usd=float(data.get("amount_usd", 0.0)),
                )
                self._send_json({"status": "topup_success", "account": result["account"]}, 200)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/tokens/mint-request":
            # Regular users submit a $TINCAN mint / credit-grant request for admin approval (or Add Money via Stripe).
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                session_acc = self._session_account()
                peer_id = (data.get("peer_id") or (session_acc.get("peer_id") if session_acc else "")).strip()
                acc = account_registry.get_account_by_peer(peer_id) if peer_id else None
                if not acc:
                    self._send_json({"error": "Register an account before requesting $TINCAN mint"}, 400)
                    return
                target_peer_id = (data.get("target_peer_id") or peer_id).strip()
                if not account_registry.get_account_by_peer(target_peer_id):
                    target_peer_id = peer_id
                try:
                    req_tokens = int(data.get("tokens", 10))
                except (TypeError, ValueError):
                    req_tokens = 10
                req_tokens = max(1, min(100000, req_tokens))
                reason = (data.get("reason") or "Onboarding / mesh operator credit request").strip()[:240]
                rec = {
                    "id": f"mreq-{secrets.token_hex(6)}",
                    "peer_id": peer_id,
                    "username": acc.get("username") or acc.get("full_name") or peer_id,
                    "full_name": acc.get("full_name") or peer_id,
                    "target_peer_id": target_peer_id,
                    "tokens": req_tokens,
                    "reason": reason,
                    "status": "pending",
                    "created_at": time.time(),
                    "resolved_at": None,
                    "resolved_by": None,
                }
                with _mint_requests_lock:
                    _mint_requests.append(rec)
                    if len(_mint_requests) > 200:
                        del _mint_requests[:-200]
                self._send_json({"status": "pending_admin_approval", "request": rec}, 201)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/tokens/mint-requests/resolve":
            # Operator-only resolution: approves a queued mint request and credits target customer peer.
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            if not self._is_admin_request():
                self._send_json({"error": "Forbidden: admin key required to mint or route $TINCAN"}, 403)
                return
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                req_id = (data.get("request_id") or "").strip()
                decision = (data.get("decision") or "approve").strip().lower()
                if decision not in ("approve", "reject"):
                    self._send_json({"error": "Decision must be 'approve' or 'reject'"}, 400)
                    return
                with _mint_requests_lock:
                    rec = next((r for r in _mint_requests if r["id"] == req_id), None)
                    if not rec:
                        self._send_json({"error": "Mint request not found"}, 404)
                        return
                    if rec["status"] != "pending":
                        self._send_json({"status": rec["status"], "request": rec}, 200)
                        return
                    target_peer = (data.get("target_peer_id") or rec["target_peer_id"] or rec["peer_id"]).strip()
                    grant_tokens = int(data.get("tokens", rec["tokens"]))
                    grant_usd = float(data.get("amount_usd", 0.0))
                if decision == "approve":
                    result = account_registry.credit_once(
                        ref=f"mintreq:{req_id}",
                        peer_id=target_peer,
                        kind="admin_grant",
                        tokens=grant_tokens,
                        amount_usd=grant_usd,
                    )
                    with _mint_requests_lock:
                        rec["status"] = "approved"
                        rec["target_peer_id"] = target_peer
                        rec["tokens"] = grant_tokens
                        rec["resolved_at"] = time.time()
                        rec["resolved_by"] = "admin"
                    self._send_json({"status": "approved", "request": rec, "account": result["account"]}, 200)
                else:
                    with _mint_requests_lock:
                        rec["status"] = "rejected"
                        rec["resolved_at"] = time.time()
                        rec["resolved_by"] = "admin"
                    self._send_json({"status": "rejected", "request": rec}, 200)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/billing/checkout":
            # Client may *request* a purchase; it only gets a Stripe-hosted payment link back.
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = (data.get("peer_id") or "").strip()
                pack_id = data.get("pack")
                if pack_id not in TOKEN_PACKS:
                    self._send_json({"error": f"Unknown pack. Choose one of {sorted(TOKEN_PACKS)}"}, 400)
                    return
                if not peer_id or not account_registry.get_account_by_peer(peer_id):
                    self._send_json({"error": "Register an account before buying tokens"}, 400)
                    return
                if not STRIPE_SECRET_KEY:
                    self._send_json({"error": "Payments are not configured on this relay"}, 503)
                    return
                base_url = os.environ.get("TINCAN_PUBLIC_URL") or f"http://{self.headers.get('Host', 'localhost')}"
                self._send_json({"checkout_url": create_stripe_checkout(peer_id, pack_id, base_url)}, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/billing/webhook":
            # The ONLY path that credits purchased tokens: a Stripe-signed, paid checkout session.
            content_length = int(self.headers.get("Content-Length", 0))
            payload = self.rfile.read(content_length)
            if not verify_stripe_signature(payload, self.headers.get("Stripe-Signature", ""), STRIPE_WEBHOOK_SECRET):
                self._send_json({"error": "Invalid signature"}, 400)
                return
            try:
                event = json.loads(payload.decode("utf-8"))
                if event.get("type") != "checkout.session.completed":
                    self._send_json({"status": "ignored"}, 200)
                    return
                session = event["data"]["object"]
                meta = session.get("metadata") or {}
                pack = TOKEN_PACKS.get(meta.get("pack"))
                if session.get("payment_status") != "paid" or not pack:
                    self._send_json({"status": "ignored"}, 200)
                    return
                cents, tokens = pack
                if session.get("amount_total") != cents or (session.get("currency") or "").lower() != "usd":
                    self._send_json({"error": "Amount does not match pack"}, 400)
                    return
                result = account_registry.credit_once(
                    ref=f"stripe:{session['id']}", peer_id=meta.get("peer_id", ""), kind="purchase",
                    tokens=tokens, amount_usd=cents / 100.0,
                )
                self._send_json({"status": "credited" if result["applied"] else "duplicate"}, 200)
            except Exception as e:
                # 500 makes Stripe retry; credit_once keeps retries from double-crediting.
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/ads/view/start":
            # Server issues a one-time view token and starts the clock.
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = (data.get("peer_id") or "").strip()
                sponsor_id = (data.get("sponsor_id") or "").strip()
                def _match_sponsor(sid: str):
                    if not sid:
                        return None
                    return next(
                        (
                            s
                            for s in sponsor_manager.sponsors
                            if s.id == sid or s.video_id == sid or s.id == f"video-{sid}"
                        ),
                        None,
                    )
                creative = _match_sponsor(sponsor_id)
                if not creative:
                    sponsor_manager.sync_from_playlist([asdict(it) for it in playlist.items])
                    creative = _match_sponsor(sponsor_id)
                if not creative:
                    self._send_json({"error": "Unknown sponsor"}, 400)
                    return
                if not peer_id or not account_registry.get_account_by_peer(peer_id):
                    self._send_json({"error": "Register an account to earn ad rewards"}, 400)
                    return
                if account_registry.count_credit_events(peer_id, "ad_reward", time.time() - 86400) >= AD_DAILY_REWARD_CAP:
                    self._send_json({"error": "Daily ad reward limit reached"}, 429)
                    return
                token = secrets.token_urlsafe(24)
                now = time.time()
                with _ad_views_lock:
                    for t in [t for t, v in _ad_views.items() if now - v["started"] > v["duration"] + 600]:
                        _ad_views.pop(t, None)
                    _ad_views[token] = {
                        "peer_id": peer_id, "sponsor_id": sponsor_id, "started": now,
                        "duration": max(1, int(creative.duration_seconds)),
                        "reward_tokens": creative.reward_tokens, "reward_usd": creative.reward_usd,
                    }
                self._send_json({"view_token": token, "min_seconds": creative.duration_seconds}, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/ads/view/complete":
            # Credits only if the server-side clock confirms the ad ran its length. Token is single-use.
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                token = data.get("view_token") or ""
                with _ad_views_lock:
                    view = _ad_views.get(token)
                    if not view or view["peer_id"] != (data.get("peer_id") or "").strip():
                        view = None
                    else:
                        elapsed = time.time() - view["started"]
                        if elapsed < view["duration"] * AD_MIN_WATCH_FRACTION:
                            self._send_json({"error": "View not complete yet"}, 400)
                            return
                        if elapsed > view["duration"] + 600:
                            _ad_views.pop(token, None)
                            view = None
                        else:
                            _ad_views.pop(token, None)
                if not view:
                    self._send_json({"error": "Invalid or expired view token"}, 400)
                    return
                result = account_registry.credit_once(
                    ref=f"ad:{token}", peer_id=view["peer_id"], kind="ad_reward",
                    tokens=view["reward_tokens"], amount_usd=view["reward_usd"],
                )
                sponsor_manager.record_completion(view["sponsor_id"])
                self._send_json({"status": "credited", "reward_tokens": view["reward_tokens"], "account": result["account"]}, 200)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/board/topics":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = data.get("peer_id") or "anonymous-peer"
                title = data.get("title") or ""
                body = data.get("body") or ""
                category = data.get("category") or "cyberspace"
                tags = data.get("tags") or []
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.split(",") if t.strip()]
                author_username = data.get("username") or data.get("author_username")
                require_verification = bool(data.get("require_verification", False))
                auto_agent_reply = bool(data.get("auto_agent_reply", True))

                result = cyberspace_board.create_topic(
                    peer_id=peer_id,
                    title=title,
                    body=body,
                    category=category,
                    tags=tags,
                    author_username=author_username,
                    require_verification=require_verification,
                    auto_agent_reply=auto_agent_reply,
                )
                if result.get("require_verification"):
                    self._send_json(result, 403)
                    return

                mesh_os.award_xp(peer_id, "cyberspace_post", display_name=result.get("author_username"))
                mesh_os.record_flight(peer_id, "relay", kind="cyberspace_topic", label=f"#{category}")
                self._send_json({"status": "created", "topic": result}, 201)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/board/topic/update":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                topic_id = data.get("topic_id") or data.get("id") or ""
                peer_id = data.get("peer_id") or "anonymous-peer"
                tags = data.get("tags")
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.split(",") if t.strip()]
                result = cyberspace_board.update_topic(
                    topic_id=topic_id,
                    peer_id=peer_id,
                    title=data.get("title"),
                    body=data.get("body"),
                    category=data.get("category"),
                    tags=tags,
                    pinned=data.get("pinned"),
                    curated=data.get("curated"),
                    locked=data.get("locked"),
                    resolved=data.get("resolved"),
                    is_admin=bool(data.get("is_admin")),
                )
                self._send_json(result, 200)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/board/curate":
            try:
                data = self._read_json_body()
                curated_val = data.get("curated")
                if curated_val is not None:
                    curated_val = bool(curated_val)
                result = cyberspace_board.curate_topic(
                    topic_id=str(data.get("topic_id") or "").strip(),
                    peer_id=str(data.get("peer_id") or data.get("curator_id") or "local-peer").strip(),
                    curated=curated_val,
                )
                self._send_json(result, 200)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/board/ai-suggest":
            try:
                data = self._read_json_body()
                result = cyberspace_board.ai_suggest(
                    query=str(data.get("query") or ""),
                    limit=int(data.get("limit") or 6),
                )
                self._send_json(result, 200)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/board/topic/delete":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                topic_id = data.get("topic_id") or data.get("id") or ""
                peer_id = data.get("peer_id") or "anonymous-peer"
                result = cyberspace_board.delete_topic(topic_id=topic_id, peer_id=peer_id)
                self._send_json(result, 200)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/board/reply":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                topic_id = data.get("topic_id") or ""
                peer_id = data.get("peer_id") or "anonymous-peer"
                body = data.get("body") or ""
                author_username = data.get("username") or data.get("author_username")
                parent_post_id = data.get("parent_post_id") or ""
                require_verification = bool(data.get("require_verification", False))
                auto_agent_reply = bool(data.get("auto_agent_reply", True))

                result = cyberspace_board.create_post(
                    topic_id=topic_id,
                    peer_id=peer_id,
                    body=body,
                    author_username=author_username,
                    parent_post_id=parent_post_id,
                    require_verification=require_verification,
                    auto_agent_reply=auto_agent_reply,
                )
                if result.get("require_verification"):
                    self._send_json(result, 403)
                    return

                mesh_os.award_xp(peer_id, "cyberspace_post", display_name=result.get("author_username"))
                mesh_os.record_flight(peer_id, "relay", kind="cyberspace_reply", label="Board Reply")
                self._send_json(result, 201)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/board/post/delete":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                post_id = data.get("post_id") or data.get("id") or ""
                peer_id = data.get("peer_id") or "anonymous-peer"
                result = cyberspace_board.delete_post(post_id=post_id, peer_id=peer_id)
                self._send_json(result, 200)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/board/vote":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                target_type = data.get("target_type") or "topic"
                target_id = data.get("target_id") or data.get("id") or ""
                peer_id = data.get("peer_id") or "anonymous-peer"
                direction = data.get("direction") or "up"
                result = cyberspace_board.vote_item(
                    target_type=target_type,
                    target_id=target_id,
                    peer_id=peer_id,
                    direction=direction,
                )
                mesh_os.award_xp(peer_id, "cyberspace_vote")
                self._send_json(result, 200)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/board/solution":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                topic_id = data.get("topic_id") or ""
                post_id = data.get("post_id") or ""
                peer_id = data.get("peer_id") or "anonymous-peer"
                result = cyberspace_board.accept_solution(topic_id=topic_id, post_id=post_id, peer_id=peer_id)
                self._send_json(result, 200)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/board/search":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                query_str = data.get("query") or data.get("q") or ""
                mode = data.get("mode") or "hybrid"
                top_k = int(data.get("top_k", 10))
                max_hops = int(data.get("max_hops", 2))
                res = cyberspace_board.search(query=query_str, mode=mode, top_k=top_k, max_hops=max_hops)
                self._send_json(res, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/verify/send":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = data.get("peer_id") or "anonymous-peer"
                username = data.get("username") or data.get("target_username") or ""
                reason = data.get("reason") or "Mandatory Cyberspace Identity Verification"
                res = cyberspace_board.dispatch_verification_form(
                    peer_id=peer_id,
                    target_username=username,
                    reason=reason,
                )
                mesh_os.record_flight("@verifier-agent", peer_id, kind="verification_form", label="🛡️ Verify Form")
                self._send_json(res, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/verify/submit":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = data.get("peer_id") or ""
                full_name = data.get("full_name") or data.get("name") or ""
                username = data.get("username") or ""
                email = data.get("email") or ""
                phone_number = data.get("phone_number") or data.get("phone") or ""
                role = data.get("role") or "Researcher / Student"
                bio = data.get("bio") or ""
                consent_pii = bool(data.get("consent_pii", True))
                request_id = data.get("request_id")
                challenge_code = data.get("challenge_code")

                res = cyberspace_board.submit_verification_form(
                    peer_id=peer_id,
                    full_name=full_name,
                    username=username,
                    email=email,
                    phone_number=phone_number,
                    role=role,
                    bio=bio,
                    consent_pii=consent_pii,
                    request_id=request_id,
                    challenge_code=challenge_code,
                )
                try:
                    mesh_os.award_xp(peer_id, "cyberspace_verified", display_name=f"{full_name} (@{username.lstrip('@')})")
                    mesh_os.record_flight(peer_id, "@verifier-agent", kind="verified", label="✅ Attested")
                except Exception:
                    pass
                self._send_json(res, 200)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path in ("/api/3d/generate", "/api/rodin/generate"):
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                prompt = data.get("prompt") or "futuristic generative 3d mesh"
                images = data.get("images")
                tier = data.get("tier", "Regular")
                fmt = data.get("format", "glb")
                mesh_mode = data.get("mesh_mode", "Quad")
                peer_id = data.get("peer_id") or "peer"
                scope = data.get("scope") or ("topic" if "topic" in data or "topic_id" in data else "user")
                owner_id = data.get("owner_id") or data.get("topic_id") or data.get("peer_id") or peer_id
                save_path = data.get("save_path")

                if data.get("max_cost_usd") is not None:
                    try:
                        max_cost_usd = float(data["max_cost_usd"])
                    except (TypeError, ValueError):
                        self._send_json({"error": "Invalid 'max_cost_usd' value"}, 400)
                        return
                    estimated_cost_usd = _estimate_rodin_tier_cost(tier)
                    if estimated_cost_usd > max_cost_usd:
                        self._send_json({
                            "error": (
                                f"Rodin tier '{tier}' estimated cost ${estimated_cost_usd:.2f} "
                                f"exceeds max_cost_usd ${max_cost_usd:.2f}"
                            ),
                            "estimated_cost_usd": estimated_cost_usd,
                            "max_cost_usd": max_cost_usd,
                            "budget_exceeded": True,
                        }, 400)
                        return

                res = _dispatch_rodin(
                    router,
                    prompt=prompt,
                    images=images,
                    tier=tier,
                    geometry_file_format=fmt,
                    mesh_mode=mesh_mode,
                )
                if data.get("wait") and not res.get("simulated") and hasattr(router, "wait_for_rodin_glb"):
                    res = router.wait_for_rodin_glb(res, max_wait_sec=float(data.get("wait_sec") or 120.0))

                # If save_path or owner_id passed and mesh is ready, write into .space VFS
                sm = _get_space_manager()
                if sm and (save_path or owner_id):
                    try:
                        if save_path:
                            sp_path = save_path
                        else:
                            from iot_federated_agent_memory.agent_space import _slug_from_prompt, _unique_space_path
                            sp_pre = sm.get_or_create_space(scope, owner_id)
                            slug = _slug_from_prompt(prompt, default=str(res.get("uuid", "rodin_mesh")))
                            sp_path = _unique_space_path(sp_pre, "/models3d", slug, f".{fmt}")
                        glb_b64 = res.get("glb_bytes_b64", "")
                        is_ready_to_save = bool(glb_b64) and bool(
                            res.get("downloaded") or res.get("simulated") or res.get("status") == "Done"
                        )
                        if is_ready_to_save:
                            sp = sm.get_or_create_space(scope, owner_id)
                            sp.write_file(sp_path, glb_b64, is_base64=True, mime_type="model/gltf-binary", updated_by=peer_id)
                            res["saved_to_space"] = {"scope": scope, "owner_id": owner_id, "path": sp_path}
                        else:
                            res["pending_save_path"] = sp_path
                    except Exception as err:
                        res["space_save_error"] = str(err)

                mesh_os.record_flight(peer_id, "rodin-3d", kind="3d_gen", label="Hyper3D Rodin")
                try:
                    mesh_os.award_xp(peer_id, "rodin_3d_generation")
                except Exception:
                    pass
                self._send_json(res, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/3d/status":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                sub_key = data.get("subscription_key") or data.get("key") or ""
                if data.get("auto_fallback") is False and hasattr(router, "check_rodin_status"):
                    res = router.check_rodin_status(sub_key, allow_fallback=False)
                else:
                    res = _check_rodin_status(router, sub_key)
                self._send_json(res, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/3d/download":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                import posixpath
                from iot_federated_agent_memory.agent_space import _slug_from_prompt, _unique_space_path
                from iot_federated_agent_memory.glb_rigger import (
                    animate_existing_rig_glb_bytes,
                    inspect_glb_rig_summary,
                )

                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                task_uuid = data.get("task_uuid") or data.get("uuid") or ""
                res = _download_rodin_assets(router, task_uuid)
                sm = _get_space_manager()
                scope = data.get("scope", "user")
                peer_id = data.get("peer_id") or "user"
                owner_id = data.get("owner_id") or peer_id
                save_path = data.get("save_path") or (res.get("save_path") if isinstance(res, dict) else "") or ""
                glb_b64 = res.get("glb_bytes_b64", "") if isinstance(res, dict) else ""
                is_rig_job = isinstance(res, dict) and res.get("task_kind") == "rig"

                # If neural rigger returned a skinned .glb with zero embedded animations, bake walk/idle keyframes
                if is_rig_job and glb_b64 and data.get("animate_if_empty", True):
                    try:
                        raw_dl = base64.b64decode(glb_b64)
                        summary = inspect_glb_rig_summary(raw_dl)
                        if summary.get("skin_count", 0) > 0 and not summary.get("animations"):
                            req_anim = str(data.get("animation") or res.get("requested_animation") or "walk")
                            anim_bytes, anim_meta = animate_existing_rig_glb_bytes(raw_dl, animation=req_anim)
                            glb_b64 = base64.b64encode(anim_bytes).decode("ascii")
                            res["glb_bytes_b64"] = glb_b64
                            res["bones"] = anim_meta["bones"]
                            res["bone_count"] = anim_meta["bone_count"]
                            res["animations"] = anim_meta["animations"]
                            res["animated_with_tincan_walk"] = True
                        else:
                            res["bones"] = summary.get("bones", [])
                            res["bone_count"] = summary.get("bone_count", 0)
                            res["animations"] = summary.get("animations", [])
                    except Exception as rig_post_err:
                        res["rig_post_note"] = str(rig_post_err)

                can_save = bool(glb_b64) and bool(
                    res.get("downloaded") or not res.get("simulated") or data.get("force_save")
                )
                if sm and can_save and (save_path or data.get("owner_id") or data.get("peer_id")):
                    try:
                        sp = sm.get_or_create_space(scope, owner_id)
                        if save_path:
                            sp_path = save_path
                        elif is_rig_job and res.get("source_path"):
                            ref_p = str(res["source_path"])
                            dname = posixpath.dirname(ref_p) or "/models3d"
                            base_n = posixpath.splitext(posixpath.basename(ref_p))[0] or "mesh"
                            if base_n.endswith("_rigged"):
                                base_n = base_n[:-7] or "mesh"
                            sp_path = _unique_space_path(sp, dname, f"{base_n}_rigged", ".glb")
                        else:
                            slug = _slug_from_prompt(data.get("prompt") or task_uuid, default="rodin_mesh")
                            sp_path = _unique_space_path(sp, "/models3d", slug, f".{res.get('format', 'glb')}")
                        sp.write_file(sp_path, glb_b64, is_base64=True, mime_type="model/gltf-binary", updated_by=peer_id)
                        res["path"] = sp_path
                        res["saved_to_space"] = {"scope": scope, "owner_id": owner_id, "path": sp_path}
                    except Exception as err:
                        res["space_save_error"] = str(err)
                self._send_json(res, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/3d/rig":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                import posixpath
                import urllib.parse
                from iot_federated_agent_memory.agent_space import _unique_space_path
                from iot_federated_agent_memory.glb_rigger import (
                    animate_existing_rig_glb_bytes,
                    inspect_glb_rig_summary,
                    rig_glb_bytes,
                )

                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                scope = data.get("scope", "user")
                peer_id = data.get("peer_id") or "user"
                owner_id = data.get("owner_id") or peer_id
                src_path = (data.get("path") or "").strip()
                raw_b64 = (data.get("glb_bytes_b64") or "").strip()
                rig_type = (data.get("rig_type") or "auto").strip()
                animation = (data.get("animation") or "walk").strip()
                engine = (data.get("engine") or data.get("model") or "local").strip().lower()
                save_path = (data.get("save_path") or "").strip()
                save_to_space = data.get("save_to_space", True)

                sm = _get_space_manager()
                if raw_b64:
                    try:
                        src_bytes = base64.b64decode(raw_b64, validate=True)
                    except ValueError as err:
                        return self._send_json({"error": f"Invalid glb_bytes_b64: {err}"}, 400)
                elif src_path:
                    if not sm:
                        return self._send_json({"error": "Space manager unavailable"}, 503)
                    sp = sm.get_or_create_space(scope, owner_id)
                    try:
                        rec = sp.read_file(src_path, as_text=False)
                    except FileNotFoundError as err:
                        return self._send_json({"error": str(err)}, 404)
                    src_b64 = rec.get("content_b64") or ""
                    if not src_b64:
                        return self._send_json({"error": f"Empty file in space: {src_path}"}, 400)
                    src_bytes = base64.b64decode(src_b64)
                else:
                    return self._send_json({"error": "Provide 'path' (a .glb in .space) or 'glb_bytes_b64'."}, 400)

                use_nanogpt = engine in ("nanogpt", "neural", "cloud") or engine in getattr(router, "NANOGPT_RIG_PRICING_USD", {})
                if use_nanogpt:
                    if not sm:
                        return self._send_json({"error": "Space manager required to stage model_url for NanoGPT rigging"}, 503)
                    sp = sm.get_or_create_space(scope, owner_id)
                    # Ensure source .glb exists in .space so /pages/<scope>/<owner>/<path> is publicly reachable
                    staged_src_path = src_path or _unique_space_path(sp, "/models3d", "source_mesh", ".glb")
                    if raw_b64 or not src_path:
                        sp.write_file(
                            staged_src_path,
                            base64.b64encode(src_bytes).decode("ascii"),
                            is_base64=True,
                            mime_type="model/gltf-binary",
                            updated_by=peer_id,
                        )
                    pub_base = (os.environ.get("TINCAN_PUBLIC_BASE_URL") or "").strip().rstrip("/")
                    if not pub_base:
                        fwd_host = (self.headers.get("X-Forwarded-Host") or self.headers.get("Host") or "").split(",")[0].strip()
                        fwd_proto = (self.headers.get("X-Forwarded-Proto") or ("https" if ".railway.app" in fwd_host else "http")).split(",")[0].strip()
                        if fwd_host:
                            pub_base = f"{fwd_proto}://{fwd_host}"
                    norm_src = staged_src_path if staged_src_path.startswith("/") else "/" + staged_src_path
                    model_url = (data.get("model_url") or "").strip() or (
                        f"{pub_base}/pages/{urllib.parse.quote(scope, safe='')}/{urllib.parse.quote(owner_id, safe='')}{norm_src}"
                        if pub_base else ""
                    )
                    data_uri = (
                        "data:model/gltf-binary;base64," + base64.b64encode(src_bytes).decode("ascii")
                        if len(src_bytes) <= 20 * 1024 * 1024
                        else None
                    )
                    pref_model = None if engine in ("nanogpt", "neural", "cloud") else engine
                    disp = router.dispatch_nanogpt_rig(
                        model_url=model_url,
                        model=pref_model,
                        rig_type=rig_type,
                        animation=animation,
                        skinning_method=str(data.get("skinning_method") or "shell"),
                        height_meters=float(data.get("height_meters") or 1.7),
                        skeleton_description=data.get("skeleton_description"),
                        image_url=data.get("image_url"),
                        data_uri_fallback=data_uri,
                        source_path=staged_src_path,
                        save_path=save_path or None,
                    )
                    if not disp.get("ok"):
                        return self._send_json({"ok": False, "error": disp.get("error") or "NanoGPT rigging dispatch failed"}, 400)

                    # Compute destination _rigged.glb path for pending UI display
                    dname = posixpath.dirname(norm_src) or "/models3d"
                    bname = posixpath.splitext(posixpath.basename(norm_src))[0] or "mesh"
                    if bname.endswith("_rigged"):
                        bname = bname[:-7] or "mesh"
                    pending_out = save_path or _unique_space_path(sp, dname, f"{bname}_rigged", ".glb")

                    try:
                        mesh_os.record_flight(peer_id, "nanogpt-rig", kind="3d_rig", label=disp.get("model", "NanoGPT Rig"))
                    except Exception:
                        pass

                    if not data.get("wait"):
                        return self._send_json({
                            "ok": True,
                            "provider": "nanogpt",
                            "gateway": "nanogpt",
                            "model": disp.get("model"),
                            "uuid": disp["uuid"],
                            "subscription_key": disp["subscription_key"],
                            "status": disp.get("status", "pending"),
                            "cost_usd": disp.get("cost_usd", 0.20),
                            "model_url": model_url,
                            "source_path": staged_src_path,
                            "pending_save_path": pending_out,
                        }, 200)

                    # Wait synchronously (CLI / explicit wait=True)
                    deadline = time.time() + float(data.get("wait_sec") or 110.0)
                    active_id = disp["uuid"]
                    last_st: Dict[str, Any] = {}
                    while time.time() < deadline:
                        last_st = _check_rodin_status(router, active_id)
                        active_id = str(last_st.get("uuid") or active_id)
                        if last_st.get("status") in ("Done", "Failed"):
                            break
                        time.sleep(2.5)
                    if last_st.get("status") != "Done":
                        return self._send_json({
                            "ok": last_st.get("status") != "Failed",
                            "provider": "nanogpt",
                            "gateway": "nanogpt",
                            "model": last_st.get("model") or disp.get("model"),
                            "uuid": active_id,
                            "subscription_key": active_id,
                            "status": last_st.get("status") or "Processing",
                            "error": last_st.get("error"),
                            "pending_save_path": pending_out,
                        }, 200 if last_st.get("status") != "Failed" else 502)

                    dl_res = _download_rodin_assets(router, active_id)
                    out_b64 = dl_res.get("glb_bytes_b64") or ""
                    if not out_b64:
                        return self._send_json({"ok": False, "error": dl_res.get("download_error") or "Downloaded empty rig asset"}, 502)
                    raw_out = base64.b64decode(out_b64)
                    summary = inspect_glb_rig_summary(raw_out)
                    if summary.get("skin_count", 0) > 0 and not summary.get("animations"):
                        anim_b, anim_meta = animate_existing_rig_glb_bytes(raw_out, animation=animation)
                        raw_out = anim_b
                        out_b64 = base64.b64encode(raw_out).decode("ascii")
                        summary["bones"] = anim_meta["bones"]
                        summary["bone_count"] = anim_meta["bone_count"]
                        summary["animations"] = anim_meta["animations"]
                    if save_to_space:
                        sp.write_file(pending_out, out_b64, is_base64=True, mime_type="model/gltf-binary", updated_by=peer_id)
                    return self._send_json({
                        "ok": True,
                        "provider": "nanogpt",
                        "gateway": "nanogpt",
                        "model": dl_res.get("model") or disp.get("model"),
                        "status": "Done",
                        "cost_usd": float(disp.get("cost_usd") or 0.20),
                        "source_path": staged_src_path,
                        "path": pending_out,
                        "rig_type": summary.get("rig_type") or rig_type,
                        "bones": summary.get("bones", []),
                        "bone_count": summary.get("bone_count", 0),
                        "animations": summary.get("animations", []),
                        "size_bytes": len(raw_out),
                        "glb_bytes_b64": out_b64,
                        "saved_to_space": {"scope": scope, "owner_id": owner_id, "path": pending_out} if save_to_space else None,
                    }, 200)

                try:
                    out_bytes, meta = rig_glb_bytes(src_bytes, rig_type=rig_type, animation=animation)
                except ValueError as err:
                    return self._send_json({"error": str(err)}, 400)

                out_b64 = base64.b64encode(out_bytes).decode("ascii")
                out_path = save_path
                saved_meta = None
                space_save_error = None
                if sm and save_to_space:
                    try:
                        sp = sm.get_or_create_space(scope, owner_id)
                        if not out_path:
                            ref_path = src_path or "/models3d/mesh.glb"
                            dname = posixpath.dirname(ref_path) or "/models3d"
                            base_name = posixpath.splitext(posixpath.basename(ref_path))[0] or "mesh"
                            if base_name.endswith("_rigged"):
                                base_name = base_name[:-7] or "mesh"
                            out_path = _unique_space_path(sp, dname, f"{base_name}_rigged", ".glb")
                        sp.write_file(out_path, out_b64, is_base64=True, mime_type="model/gltf-binary", updated_by=peer_id)
                        saved_meta = {"scope": scope, "owner_id": owner_id, "path": out_path}
                    except Exception as err:
                        space_save_error = str(err)

                try:
                    mesh_os.record_flight(peer_id, "tincan-auto-rigger", kind="3d_rig", label="Free Auto-Rig GLB")
                except Exception:
                    pass

                res: Dict[str, Any] = {
                    "ok": True,
                    "provider": "tincan-auto-rigger",
                    "cost_usd": 0.0,
                    "source_path": src_path or None,
                    "path": out_path or None,
                    "rig_type": meta["rig_type"],
                    "bones": meta["bones"],
                    "bone_count": meta["bone_count"],
                    "animations": meta["animations"],
                    "vertex_count": meta["vertex_count"],
                    "size_bytes": meta["size_bytes"],
                    "glb_bytes_b64": out_b64,
                }
                if saved_meta:
                    res["saved_to_space"] = saved_meta
                if space_save_error:
                    res["space_save_error"] = space_save_error
                self._send_json(res, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path in ("/api/image/generate", "/api/2d/generate"):
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                from iot_federated_agent_memory.agent_space import _slug_from_prompt, _unique_space_path

                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                prompt = (data.get("prompt") or "").strip()
                if not prompt:
                    self._send_json({"ok": False, "error": "Missing 'prompt'"}, 400)
                    return
                model = data.get("model")
                aspect_ratio = data.get("aspect_ratio")
                gateway = data.get("gateway")
                scope = (data.get("scope") or "user").strip()
                owner_id = (data.get("owner_id") or data.get("peer_id") or "default").strip()
                peer_id = (data.get("peer_id") or owner_id or "peer").strip()
                save_path = data.get("save_path")

                img_res = router.dispatch_image_generation(
                    prompt=prompt,
                    model=model,
                    aspect_ratio=aspect_ratio,
                    gateway=gateway,
                )
                if not img_res.get("ok") or not img_res.get("image_bytes"):
                    self._send_json({k: v for k, v in img_res.items() if k != "image_bytes"}, 502 if not img_res.get("simulated") else 400)
                    return

                sm = _get_space_manager()
                sp = sm.get_or_create_space(scope, owner_id)
                ext = str(img_res.get("ext") or ".png")
                sp_path = save_path or _unique_space_path(sp, "/images", _slug_from_prompt(prompt, default="image"), ext)
                sp.write_file(
                    sp_path,
                    img_res["image_bytes"],
                    mime_type=img_res.get("mime_type") or "image/png",
                    updated_by=peer_id,
                )
                out = {k: v for k, v in img_res.items() if k != "image_bytes"}
                if not out.get("image_b64"):
                    out["image_b64"] = base64.b64encode(img_res["image_bytes"]).decode("ascii")
                out["path"] = sp_path
                out["saved_to_space"] = {"scope": scope, "owner_id": owner_id, "path": sp_path}
                self._send_json(out, 200)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif parsed.path == "/api/file/inspect":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                fpath = str(data.get("path") or "/file.bin").strip()
                source = str(data.get("source") or "space").strip().lower()
                raw_b64 = str(data.get("bytes_b64") or "").strip()
                if raw_b64:
                    raw_bytes = base64.b64decode(raw_b64)
                elif source == "drive":
                    if not self._drive_mirror_allowed():
                        return self._send_json({"ok": False, "error": "Drive mirror forbidden from remote host"}, 403)
                    abs_path, _sz, _mime = drive_mirror.open_raw(drive_mirror.mirror_root(), fpath)
                    with open(abs_path, "rb") as fh:
                        raw_bytes = fh.read()
                else:
                    scope = str(data.get("scope") or "user")
                    owner_id = str(data.get("owner_id") or data.get("peer_id") or "default")
                    sm = _get_space_manager()
                    sp = sm.get_or_create_space(scope, owner_id)
                    rec = sp.read_file(fpath, as_text=False)
                    raw_bytes = base64.b64decode(rec.get("content_b64") or "")
                self._send_json(inspect_binary_file(raw_bytes, fpath), 200)
            except FileNotFoundError as fe:
                self._send_json({"ok": False, "error": str(fe)}, 404)
            except drive_mirror.MirrorAccessError as me:
                self._send_json({"ok": False, "error": str(me)}, 403)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif parsed.path == "/api/browser/navigate":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                url = str(data.get("url") or "").strip()
                if not url:
                    self._send_json({"ok": False, "error": "Missing 'url'"}, 400)
                    return
                bm = _get_browser_manager()
                res = bm.navigate(
                    url,
                    session_id=data.get("session_id"),
                    reader_only=bool(data.get("reader_only", False)),
                )
                self._send_json(res, 200)
            except ValueError as ve:
                self._send_json({"ok": False, "error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 502)
        elif parsed.path == "/api/browser/action":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                sid = str(data.get("session_id") or "").strip()
                act = str(data.get("action") or "").strip()
                if not sid or not act:
                    self._send_json({"ok": False, "error": "Missing 'session_id' or 'action'"}, 400)
                    return
                bm = _get_browser_manager()
                res = bm.action(
                    sid,
                    act,
                    selector=data.get("selector"),
                    x=data.get("x"),
                    y=data.get("y"),
                    text=data.get("text"),
                    key=data.get("key"),
                    delta_y=float(data.get("delta_y") if data.get("delta_y") is not None else 480.0),
                    script=data.get("script"),
                    full_page=bool(data.get("full_page", False)),
                )
                self._send_json(res, 200)
            except ValueError as ve:
                self._send_json({"ok": False, "error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif parsed.path == "/api/browser/save":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                sid = str(data.get("session_id") or "").strip()
                if not sid:
                    self._send_json({"ok": False, "error": "Missing 'session_id'"}, 400)
                    return
                bm = _get_browser_manager()
                sm = _get_space_manager()
                res = bm.save_to_space(
                    sid,
                    sm,
                    scope=(data.get("scope") or "user").strip(),
                    owner_id=(data.get("owner_id") or data.get("peer_id") or "default").strip(),
                    peer_id=(data.get("peer_id") or "browser").strip(),
                    kind=(data.get("kind") or "markdown").strip(),
                    save_path=data.get("save_path"),
                )
                self._send_json(res, 200)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif parsed.path == "/api/space/file":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                scope = data.get("scope", "user")
                owner_id = data.get("owner_id") or data.get("peer_id") or data.get("topic_id") or "default_user"
                updated_by = data.get("updated_by", "user")
                if owner_id in banned_peers or updated_by in banned_peers:
                    b_id = owner_id if owner_id in banned_peers else updated_by
                    self._send_json({"error": f"Banned: {banned_peers[b_id].get('reason', 'Policy violation')}", "banned": True}, 403)
                    return
                path = data.get("path")
                if not path:
                    self._send_json({"error": "Missing 'path'"}, 400)
                    return
                action = data.get("action", "write")
                content = data.get("content", "")
                target = data.get("target")
                replacement = data.get("replacement")
                is_b64 = bool(data.get("is_base64", False))

                sm = _get_space_manager()
                sp = sm.get_or_create_space(scope, owner_id)
                if action == "delete":
                    out = sp.delete_file(path)
                elif action == "patch":
                    out = sp.patch_file(path, target or "", replacement or "", updated_by=updated_by)
                else:
                    out = sp.write_file(path, content, updated_by=updated_by, is_base64=is_b64)
                self._send_json(out, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path.startswith("/api/space/notes"):
            self._handle_space_notes_post(parsed.path)
        elif parsed.path == "/api/space/exec":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                scope = data.get("scope", "user")
                owner_id = data.get("owner_id") or data.get("peer_id") or data.get("topic_id") or "default_user"
                entrypoint = data.get("entrypoint", "/src/main.py")
                runtime = data.get("runtime", "auto")
                code_override = data.get("code_override") or data.get("code")
                args = data.get("args") or []

                sm = _get_space_manager()
                out = sm.run_playground(
                    scope=scope,
                    owner_id=owner_id,
                    entrypoint=entrypoint,
                    runtime=runtime,
                    code_override=code_override,
                    args=args,
                )
                self._send_json(out, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/terminal/brew":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                from iot_federated_agent_memory.tincan_brew import handle_brew_command

                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                cmd = (data.get("command") or data.get("cmd") or "brew help").strip()
                peer_id = (data.get("peer_id") or data.get("owner_id") or "aeonik").strip()
                out = handle_brew_command(cmd, peer_id=peer_id, queue_hitl=True, execute_native=False)
                self._send_json(out, 200)
            except Exception as e:
                self._send_json({"status": "error", "error": str(e), "output": f"Error: {e}", "lines": [f"Error: {e}"]}, 500)
        elif parsed.path == "/api/terminal/harness":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                from iot_federated_agent_memory.tincan_brew import handle_harness_command

                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                cmd = (data.get("command") or data.get("cmd") or "harnesses").strip()
                peer_id = (data.get("peer_id") or data.get("owner_id") or "aeonik").strip()
                scope = (data.get("scope") or "user").strip()
                owner_id = (data.get("owner_id") or data.get("peer_id") or "default").strip()
                sm = _get_space_manager()
                space_vfs = sm.get_or_create_space(scope=scope, owner_id=owner_id)
                if getattr(self, "server", None) and getattr(self.server, "server_port", None):
                    os.environ["TINCAN_PORT"] = str(self.server.server_port)
                out = handle_harness_command(
                    cmd,
                    peer_id=peer_id,
                    queue_hitl=True,
                    execute=True,
                    space_vfs=space_vfs,
                    space_runner=getattr(sm, "runner", None),
                )
                self._send_json(out, 200 if out.get("status") != "error" else 400)
            except Exception as e:
                self._send_json({"status": "error", "error": str(e), "output": f"Error: {e}", "lines": [f"Error: {e}"]}, 500)
        elif parsed.path == "/api/terminal/actions":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                from iot_federated_agent_memory.tincan_actions import handle_actions_command

                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                cmd = (data.get("command") or data.get("cmd") or "actions").strip()
                out = handle_actions_command(cmd)
                self._send_json(out, 200 if out.get("status") != "error" else 400)
            except Exception as e:
                self._send_json({"status": "error", "error": str(e), "output": f"Error: {e}", "lines": [f"Error: {e}"]}, 500)
        elif parsed.path == "/api/terminal/pty/start":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                app_id = (data.get("harness") or data.get("command") or data.get("app") or "bash").strip()
                scope = (data.get("scope") or "user").strip()
                owner_id = (data.get("owner_id") or data.get("peer_id") or "default").strip()
                active_file = data.get("active_file")
                cols = int(data.get("cols") or 100)
                rows = int(data.get("rows") or 30)
                sp_vfs = _get_space_manager().get_or_create_space(scope=scope, owner_id=owner_id)
                srv_port = getattr(getattr(self, "server", None), "server_port", None) or PORT
                os.environ["TINCAN_PORT"] = str(srv_port)
                sess = _get_pty_manager().start_session(
                    app_id,
                    scope=scope,
                    owner_id=owner_id,
                    vfs=sp_vfs,
                    palace_snippets=_get_palace_snippets(limit=8),
                    active_file=active_file,
                    cols=cols,
                    rows=rows,
                    extra_env={"TINCAN_LOCAL_URL": f"http://127.0.0.1:{srv_port}"},
                    ai_router=router,
                )
                self._send_json({"status": "ok", **sess.summary(), "files_count": len(sp_vfs.list_files())}, 200)
            except Exception as e:
                self._send_json({"status": "error", "error": str(e)}, 400)
        elif parsed.path == "/api/terminal/pty/input":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                sid = (data.get("session_id") or "").strip()
                sess = _get_pty_manager().get(sid)
                if not sess:
                    self._send_json({"status": "error", "error": f"Unknown PTY session '{sid}'"}, 404)
                    return
                if data.get("data_b64"):
                    raw = base64.b64decode(data["data_b64"])
                else:
                    raw = str(data.get("data") or "").encode("utf-8")
                sess.write(raw)
                self._send_json({"status": "ok"}, 200)
            except Exception as e:
                self._send_json({"status": "error", "error": str(e)}, 400)
        elif parsed.path == "/api/terminal/pty/resize":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                sid = (data.get("session_id") or "").strip()
                sess = _get_pty_manager().get(sid)
                if not sess:
                    self._send_json({"status": "error", "error": f"Unknown PTY session '{sid}'"}, 404)
                    return
                sess.resize(int(data.get("cols") or 100), int(data.get("rows") or 30))
                self._send_json({"status": "ok", "cols": sess.cols, "rows": sess.rows}, 200)
            except Exception as e:
                self._send_json({"status": "error", "error": str(e)}, 400)
        elif parsed.path == "/api/terminal/pty/sync":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                sid = (data.get("session_id") or "").strip()
                synced = _get_pty_manager().sync(sid)
                self._send_json({"status": "ok", "synced_files": synced}, 200)
            except KeyError as e:
                self._send_json({"status": "error", "error": str(e)}, 404)
            except Exception as e:
                self._send_json({"status": "error", "error": str(e)}, 500)
        elif parsed.path == "/api/terminal/pty/stop":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                sid = (data.get("session_id") or "").strip()
                synced = _get_pty_manager().close(sid)
                self._send_json({"status": "ok", "synced_files": synced}, 200)
            except Exception as e:
                self._send_json({"status": "error", "error": str(e)}, 500)
        elif parsed.path == "/api/space/agent":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                scope = data.get("scope", "user")
                owner_id = data.get("owner_id") or data.get("peer_id") or data.get("topic_id") or "default_user"
                prompt = data.get("prompt")
                if not prompt:
                    self._send_json({"error": "Missing 'prompt'"}, 400)
                    return
                model_alias = data.get("model_alias") or data.get("model", "gemini-brain")
                author = data.get("author", "agent")

                sm = _get_space_manager()
                if getattr(sm, "ai_router", None) is None:
                    sm.ai_router = router
                out = sm.run_agent(
                    scope=scope,
                    owner_id=owner_id,
                    prompt=prompt,
                    model_alias=model_alias,
                    author=author,
                    palace_snippets=_get_palace_snippets(limit=8),
                    active_file=data.get("active_file"),
                )
                self._send_json(out, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/space/create":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                scope = data.get("scope", "dynamic")
                owner_id = data.get("owner_id") or data.get("space_id")
                title = data.get("title")
                description = data.get("description")
                template = data.get("template", "python")

                sm = _get_space_manager()
                if hasattr(sm, "create_space"):
                    sp = sm.create_space(scope=scope, owner_id=owner_id, title=title, description=description, template=template)
                else:
                    sp = sm.get_or_create_space(scope=scope, owner_id=owner_id, title=title, description=description)
                self._send_json({"status": "created", **sp.get_summary()}, 201)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path in ("/api/space/run", "/api/space/runner/execute"):
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                scope = data.get("scope", "dynamic")
                owner_id = data.get("owner_id") or data.get("space_id") or "default_user"
                prompt = data.get("prompt")
                code = data.get("code") or data.get("code_override")
                entrypoint = data.get("entrypoint", "/src/main.py")
                runtime = data.get("runtime", "auto")
                model_alias = data.get("model") or data.get("model_alias", "google/gemini-2.5-flash")
                author = data.get("author", "agent_runner")
                args = data.get("args") or []

                sm = _get_space_manager()
                sp = sm.get_or_create_space(scope=scope, owner_id=owner_id)

                agent_result = None
                exec_result = None

                # 1. If prompt is given, run autonomous agent in dynamic space
                if prompt:
                    agent_result = sm.run_agent(
                        scope=scope,
                        owner_id=owner_id,
                        prompt=prompt,
                        model_alias=model_alias,
                        author=author,
                    )
                # 2. If code is given or no prompt, run code playground in sandbox
                if code or not prompt:
                    if code:
                        sp.write_file(entrypoint, code, updated_by=author)
                    exec_result = sm.run_playground(
                        scope=scope,
                        owner_id=owner_id,
                        entrypoint=entrypoint,
                        runtime=runtime,
                        code_override=code,
                        args=args,
                    )

                self._send_json({
                    "status": "success",
                    "scope": scope,
                    "owner_id": owner_id,
                    "agent_result": agent_result,
                    "exec_result": exec_result,
                    "vfs": sp.get_summary(),
                }, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/space/fork":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                from_scope = data.get("from_scope", "topic")
                from_id = data.get("from_id") or data.get("from_owner") or data.get("from_topic", "")
                to_scope = data.get("to_scope", "user")
                to_id = data.get("to_id") or data.get("to_owner") or data.get("to_user", "")
                path = data.get("path")
                dest_path = data.get("dest_path")
                updated_by = data.get("updated_by", "fork")

                sm = _get_space_manager()
                if path:
                    out = sm.fork_file(from_scope, from_id, to_scope, to_id, path, dest_path=dest_path, updated_by=updated_by)
                else:
                    out = sm.fork_space(from_scope, from_id, to_scope, to_id)
                self._send_json(out, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/space/import":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                scope = data.get("scope", "user")
                owner_id = data.get("owner_id") or data.get("peer_id") or "default_user"
                space_b64 = data.get("data") or data.get("space_b64") or ""

                sm = _get_space_manager()
                out = sm.import_space(scope, owner_id, space_b64)
                self._send_json(out, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/artcraft/open":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                app_id = data.get("app_id") or data.get("app")
                scope = data.get("scope", "user")
                owner_id = data.get("owner_id") or data.get("peer_id") or "default_user"
                path = data.get("path")
                sync_back = bool(data.get("sync", False))
                launch_proc = bool(data.get("launch_process", True))
                sm = _get_space_manager()
                if sync_back and path and hasattr(sm, "sync_from_artcraft_pc"):
                    out = sm.sync_from_artcraft_pc(scope=scope, owner_id=owner_id, path=path)
                elif hasattr(sm, "open_in_artcraft_pc"):
                    out = sm.open_in_artcraft_pc(
                        app_id=app_id,
                        scope=scope,
                        owner_id=owner_id,
                        path=path,
                        launch_process=launch_proc,
                    )
                else:
                    out = {"status": "wasm-fallback", "app_id": app_id, "getartcraft_url": "https://getartcraft.com"}
                self._send_json(out, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/crdt/gossip":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                if "delta" in data and isinstance(data["delta"], dict):
                    delta = CRDTDeltaMessage.from_dict(data["delta"])
                    applied = crdt_node.merge_remote_delta(delta)
                else:
                    key = data.get("key")
                    if not key:
                        self._send_json({"error": "Missing 'key' or 'delta'"}, 400)
                        return
                    value = data.get("value") if isinstance(data.get("value"), dict) else {"value": data.get("value")}
                    operation = data.get("operation", "upsert")
                    delta = crdt_node.apply_local_update(key=str(key), value=value, operation=str(operation))
                    applied = True
                self._send_json({
                    "status": "ok",
                    "applied": applied,
                    "delta": delta.to_dict(),
                    "merkle_root": crdt_node.compute_merkle_root(),
                    "vector_clock": crdt_node.vector_clock,
                    "state_count": len(crdt_node.state_store),
                }, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/telemetry/ingest":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                topic = data.get("topic") or f"devices/{data.get('device_id', 'sensor-01')}/telemetry"
                flush_now = bool(data.get("flush", False))
                wallet_id = data.get("wallet_id")
                # mint_usd is ignored: telemetry clients can no longer fund their own wallet.
                if wallet_id:
                    mqtt_adapter.wallet_id = wallet_id
                pkt = mqtt_adapter.receive_message(topic, data)
                flushed_nodes = mqtt_adapter.flush_batch() if flush_now else []
                latest_receipt = mqtt_adapter.receipts[-1].to_dict() if mqtt_adapter.receipts else None
                self._send_json({
                    "status": "ingested",
                    "topic": topic,
                    "packet": pkt.to_dict() if pkt else None,
                    "vault_node": pkt.to_vault_node() if pkt else None,
                    "flushed_count": len(flushed_nodes),
                    "pending_batch_size": len(mqtt_adapter.pending_batch),
                    "wallet_balance_usd": vending_machine.get_balance(mqtt_adapter.wallet_id or "mesh-default"),
                    "latest_receipt": latest_receipt,
                }, 200)
            except CreditExhaustionError as ce:
                self._send_json({"error": str(ce), "code": "CREDIT_EXHAUSTED"}, 402)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path in ("/api/nodes/generate", "/api/generate"):
            try:
                data = self._read_json_body()
                code, res = _node_studio_generate(data, dict(self.headers))
                self._send_json(res, code)
            except ValueError as ve:
                self._send_json({"ok": False, "error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif parsed.path == "/api/nodes/filter":
            try:
                data = self._read_json_body()
                code, res = _node_studio_filter(data)
                self._send_json(res, code)
            except ValueError as ve:
                self._send_json({"ok": False, "error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif parsed.path == "/api/nodes/graph":
            try:
                data = self._read_json_body()
                code, res = _node_graph_save(data)
                self._send_json(res, code)
            except ValueError as ve:
                self._send_json({"ok": False, "error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif parsed.path == "/api/atlas/assets/upload":
            try:
                data = self._read_json_body()
                code, res = _atlas_upload_asset(data, ai_router=router)
                self._send_json(res, code)
            except ValueError as ve:
                self._send_json({"ok": False, "error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif parsed.path == "/api/atlas/tasks/run":
            try:
                data = self._read_json_body()
                code, res = _atlas_run_task(data, headers=dict(self.headers), ai_router=router)
                self._send_json(res, code)
            except ValueError as ve:
                self._send_json({"ok": False, "error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif parsed.path == "/api/atlas/operations/status":
            try:
                data = self._read_json_body()
                op_id = (data.get("operation_id") or data.get("id") or data.get("op_id") or "").strip()
                code, res = _atlas_operation_status(op_id, ai_router=router)
                self._send_json(res, code)
            except ValueError as ve:
                self._send_json({"ok": False, "error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif parsed.path == "/api/atlas/operations/download":
            try:
                data = self._read_json_body()
                code, res = _atlas_download_operation(data, ai_router=router)
                self._send_json(res, code)
            except ValueError as ve:
                self._send_json({"ok": False, "error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif parsed.path == "/api/audio/generate":
            try:
                data = self._read_json_body()
                code, res = _audio_generate_and_save(data, ai_router=router)
                self._send_json(res, code)
            except ValueError as ve:
                self._send_json({"ok": False, "error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif parsed.path == "/api/omni/route":
            try:
                data = self._read_json_body()
                code, res = _omni_route(data, headers=dict(self.headers), ai_router=router)
                self._send_json(res, code)
            except ValueError as ve:
                self._send_json({"ok": False, "error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 500)
        elif parsed.path == "/api/thread/file":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                code, body = api_write_file(
                    data.get("peer_id"),
                    data.get("thread_id"),
                    data.get("path") or data.get("relpath"),
                    data.get("content"),
                    registry=account_registry,
                )
                self._send_json(body, code)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        else:
            self._send_empty(404)

    def _send_shell_html(self) -> None:
        """Serve the Mesh OS shell (ETag + gzip), same as GET /."""
        raw, gz, etag = _get_html_Entry(HTML_UI)
        if self.headers.get("If-None-Match") == etag:
            self.send_response(304)
            self.send_header("ETag", etag)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        use_gzip = self._accepts_gzip()
        body = gz if use_gzip else raw
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("ETag", etag)
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Vary", "Accept-Encoding")
        if use_gzip:
            self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self._write_body(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if ARENA_CONTEXT_API.handle_get(self, parsed):
            return
        clean_path = parsed.path.rstrip("/") if parsed.path != "/" else "/"
        if clean_path in SINGLE_WINDOW_ROUTES:
            # Single-window routes: the shell reads location.pathname and opens that window.
            self._send_shell_html()
            return
        if parsed.path in ("/pages", "/site") or parsed.path.startswith(("/pages/", "/site/")):
            serve_space_pages(self, _get_space_manager(), parsed.path)
            return
        if parsed.path.startswith("/localhost/"):
            proxy_localhost_port(self, getattr(self, "command", "GET"), parsed.path, parsed.query)
            return
        if clean_path in ("/nodes", "/nodes/timeline", "/nodes/gateway", "/gemini-node-studio"):
            query = parse_qs(parsed.query)
            modality = _normalize_node_modality(query.get("modality", ["image"])[0])
            if clean_path == "/nodes/timeline":
                view = "timeline"
            elif clean_path == "/nodes/gateway":
                view = "gateway"
            else:
                view = _normalize_node_view(query.get("view", ["editor"])[0])
            self._send_html(_render_node_studio_page(modality=modality, view=view), 200)
            return
        if clean_path in ("/designs", "/mockups") or clean_path.startswith("/designs/") or clean_path.startswith("/mockups/"):
            if render_designs_gallery_html is not None:
                self._send_html(render_designs_gallery_html(), 200)
            else:
                self._send_html("<h1>Design Mockups Showcase</h1>", 200)
            return
        elif clean_path in ("/fono", "/aeonik", "/fono/", "/aeonik/"):
            fono_path = os.path.join(os.path.dirname(__file__), "docs", "designs", "ios-app", "html", "00-fono.html")
            if os.path.isfile(fono_path):
                with open(fono_path, "r", encoding="utf-8") as f:
                    self._send_html(f.read(), 200)
            else:
                self._send_html("<h1>Aeonik Fono Mobile UI</h1>", 200)
            return
        elif clean_path.startswith("/docs/") or clean_path.startswith("/assets/"):
            safe_rel = clean_path.lstrip("/").replace("..", "")
            fpath = os.path.join(os.path.dirname(__file__), safe_rel)
            if os.path.isfile(fpath):
                self._send_file(fpath)
            else:
                self._send_empty(404)
            return
        elif clean_path in ("/car",) or clean_path.startswith("/car/"):
            parts = [p for p in clean_path.split("/") if p]
            mode = parts[1] if len(parts) > 1 else "driving"
            if render_car_headunit_html is not None:
                self._send_html(render_car_headunit_html(mode), 200)
            else:
                self._send_empty(404)
            return
        elif clean_path in ("/ios",) or clean_path.startswith("/ios/"):
            parts = [p for p in clean_path.split("/") if p]
            screen = parts[1] if len(parts) > 1 else "01-onboarding"
            if ios_preview is not None and hasattr(ios_preview, "render_ios_simulator_html"):
                self._send_html(ios_preview.render_ios_simulator_html(screen), 200)
            else:
                # Standalone fallback: render from docs/designs/ios-app/html if present
                ios_doc_path = os.path.join(os.path.dirname(__file__), "docs", "designs", "ios-app", "html", f"{screen}.html" if not screen.endswith(".html") else screen)
                if os.path.isfile(ios_doc_path):
                    with open(ios_doc_path, "r", encoding="utf-8") as f:
                        self._send_html(f.read(), 200)
                else:
                    self._send_html(f"<!DOCTYPE html><html><body><h1>TinCan iOS Simulator</h1><p>Screen: {screen}</p></body></html>", 200)
            return
        elif parsed.path in ("/", "/health", "/call", "/tv", "/os", "/mesh", "/board", "/cyberspace", "/terminal",
                             "/arena", "/quests", "/rewards"):
            raw, gz, etag = _get_html_Entry(HTML_UI)
            if self.headers.get("If-None-Match") == etag:
                self.send_response(304)
                self.send_header("ETag", etag)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            use_gzip = self._accepts_gzip()
            body = gz if use_gzip else raw
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("ETag", etag)
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Vary", "Accept-Encoding")
            if use_gzip:
                self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self._write_body(body)
        elif parsed.path == "/api/mesh/state":
            query = parse_qs(parsed.query)
            room = query.get("room", ["main"])[0]
            state = mesh_os.get_state(room=room)
            state["active_webrtc_streams"] = relay.get_active_streams()
            self._send_json(state, 200)
        elif parsed.path == "/api/mesh/sync":
            query = parse_qs(parsed.query)
            room = query.get("room", ["main"])[0]
            peer_id = query.get("peer_id", query.get("peer", [None]))[0]
            since_str = query.get("since_seq", query.get("since", ["0"]))[0]
            inc_analytics = query.get("include_analytics", ["0"])[0] in ("1", "true", "yes")
            try:
                since_seq = int(since_str)
            except ValueError:
                since_seq = 0
            state = mesh_os.get_state(room=room)
            state["active_webrtc_streams"] = relay.get_active_streams()
            signals_payload = (
                relay.poll_signals(receiver_id=peer_id, room=room, since_seq=since_seq)
                if peer_id
                else {"signals": [], "latest_seq": since_seq, "peers": []}
            )
            payload = {
                "state": state,
                "signals": signals_payload,
            }
            if inc_analytics:
                payload["analytics"] = router.get_analytics()
            self._send_json(payload, 200)
        elif parsed.path == "/api/mesh/leaderboard":
            self._send_json({
                "leaderboard": mesh_os.get_leaderboard(),
                "tier": mesh_os.get_tier_info(),
            }, 200)
        elif parsed.path == "/api/playlist":
            self._send_json(playlist.get_playlist(), 200)
        elif parsed.path == "/api/ads/sponsor":
            query = parse_qs(parsed.query)
            sponsor_id = query.get("id", [None])[0]
            sponsor = sponsor_manager.get_sponsor(sponsor_id)
            state = sponsor_manager.get_state()
            self._send_json({
                "sponsor": sponsor,
                "networks": state["networks"],
                "total_sponsors": len(state["all_sponsors"]),
            }, 200)
        elif parsed.path in ("/api/ads/state", "/api/sponsors", "/api/sponsor/list"):
            self._send_json(sponsor_manager.get_state(), 200)
        elif parsed.path == "/api/ads/intel":
            self._send_json({
                "status": "ok",
                "intel_records": sponsor_manager.get_admin_intel_logs(),
                "total": len(sponsor_manager.admin_intel_logs),
            }, 200)
        elif parsed.path.startswith("/videos/") and parsed.path.endswith(".mp4"):
            from iot_federated_agent_memory.video_playlist import VIDEOS_DIR, download_tiktok_mp4
            from iot_federated_agent_memory.s3_storage import s3_get_object
            import re

            fname = os.path.basename(parsed.path)
            vid = os.path.splitext(fname)[0]
            file_path = os.path.join(VIDEOS_DIR, f"{vid}.mp4")
            if not os.path.isfile(file_path) or os.path.getsize(file_path) < 1024:
                # 1. Attempt immediate synchronous pull from persistent Railway S3 bucket
                try:
                    s3_get_object(f"videos/{vid}.mp4", file_path)
                except Exception:
                    pass

            if not os.path.isfile(file_path) or os.path.getsize(file_path) < 1024:
                with _downloading_lock:
                    already_downloading = vid in _downloading_videos
                    if not already_downloading:
                        _downloading_videos.add(vid)

                if not already_downloading:
                    def _bg_download(v_id: str, dest_dir: str):
                        try:
                            download_tiktok_mp4(v_id, f"https://www.tiktok.com/@nojuannobody/video/{v_id}", dest_dir)
                        finally:
                            with _downloading_lock:
                                _downloading_videos.discard(v_id)

                    threading.Thread(target=_bg_download, args=(vid, VIDEOS_DIR), daemon=True).start()

            if not os.path.isfile(file_path) or os.path.getsize(file_path) < 1024:
                self._send_empty(404)
                return

            stat = os.stat(file_path)
            file_size = stat.st_size
            etag = f'"{file_size}-{int(stat.st_mtime)}"'
            if self.headers.get("If-None-Match") == etag:
                self.send_response(304)
                self.send_header("ETag", etag)
                self.send_header("Cache-Control", "public, max-age=86400, immutable")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            range_header = self.headers.get("Range")
            chunk_size = 65536
            if range_header:
                m = re.match(r"bytes=(\d+)-(\d*)", range_header)
                if m:
                    start = int(m.group(1))
                    end = int(m.group(2)) if m.group(2) else file_size - 1
                    end = min(end, file_size - 1)
                    length = max(0, end - start + 1)
                    self.send_response(206)
                    self.send_header("Content-Type", "video/mp4")
                    self.send_header("Accept-Ranges", "bytes")
                    self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                    self.send_header("Content-Length", str(length))
                    self.send_header("ETag", etag)
                    self.send_header("Cache-Control", "public, max-age=86400, immutable")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    if getattr(self, "command", "GET") != "HEAD" and length > 0:
                        with open(file_path, "rb") as f:
                            f.seek(start)
                            remaining = length
                            while remaining > 0:
                                buf = f.read(min(chunk_size, remaining))
                                if not buf:
                                    break
                                self.wfile.write(buf)
                                remaining -= len(buf)
                    return

            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(file_size))
            self.send_header("ETag", etag)
            self.send_header("Cache-Control", "public, max-age=86400, immutable")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            if getattr(self, "command", "GET") != "HEAD" and file_size > 0:
                with open(file_path, "rb") as f:
                    while True:
                        buf = f.read(chunk_size)
                        if not buf:
                            break
                        self.wfile.write(buf)
        elif parsed.path == "/api/webrtc/signals":
            query = parse_qs(parsed.query)
            peer_id = query.get("peer_id", query.get("peer", [None]))[0]
            room = query.get("room", ["main"])[0]
            since_str = query.get("since_seq", query.get("since", ["0"]))[0]
            try:
                since_seq = int(since_str)
            except ValueError:
                since_seq = 0
            if not peer_id:
                self._send_json({"error": "Missing 'peer_id' query parameter"}, 400)
                return
            self._send_json(relay.poll_signals(receiver_id=peer_id, room=room, since_seq=since_seq), 200)
        elif parsed.path == "/api/thread/files":
            query = parse_qs(parsed.query)
            code, body = api_list_files(
                query.get("peer_id", [None])[0],
                query.get("thread_id", [None])[0],
                subpath=query.get("subpath", [""])[0] or "",
                registry=account_registry,
            )
            self._send_json(body, code)
        elif parsed.path == "/api/thread/file":
            query = parse_qs(parsed.query)
            code, body = api_read_file(
                query.get("peer_id", [None])[0],
                query.get("thread_id", [None])[0],
                query.get("path", [None])[0] or query.get("relpath", [None])[0],
                registry=account_registry,
            )
            self._send_json(body, code)
        elif parsed.path == "/api/account/get":
            query = parse_qs(parsed.query)
            peer_id = query.get("peer_id", [None])[0]
            if not peer_id:
                self._send_json({"error": "Missing 'peer_id' query parameter"}, 400)
                return
            acc = account_registry.get_account_by_peer(peer_id)
            if acc:
                self._send_json({"status": "found", "account": acc}, 200)
            else:
                self._send_json({"error": "Account not found", "peer_id": peer_id}, 404)
        elif parsed.path == "/api/account/list":
            accounts = account_registry.list_accounts()
            self._send_json({"count": len(accounts), "accounts": accounts}, 200)
        elif parsed.path == "/api/account/billing":
            query = parse_qs(parsed.query)
            peer_id = query.get("peer_id", [None])[0]
            if not peer_id:
                self._send_json({"error": "Missing 'peer_id' query parameter"}, 400)
                return
            summary = account_registry.get_billing_summary(peer_id)
            status_code = 200 if "error" not in summary else 404
            self._send_json(summary, status_code)
        elif parsed.path == "/api/board/topics":
            query = parse_qs(parsed.query)
            category = query.get("category", [None])[0]
            tag = query.get("tag", [None])[0]
            user = query.get("user", query.get("username", [None]))[0]
            agent = query.get("agent", [None])[0]
            sort_by = query.get("sort_by", query.get("sort", ["hot"]))[0]
            verified_only = query.get("verified_only", ["0"])[0] in ("1", "true", "yes")
            curated_only = query.get("curated_only", ["0"])[0] in ("1", "true", "yes")
            limit = int(query.get("limit", ["50"])[0])
            res = cyberspace_board.list_topics(
                category=category,
                tag=tag,
                mentioned_user=user,
                mentioned_agent=agent,
                sort_by=sort_by,
                verified_only=verified_only,
                curated_only=curated_only,
                limit=limit,
            )
            self._send_json(res, 200)
        elif parsed.path == "/api/board/topic":
            query = parse_qs(parsed.query)
            topic_id = query.get("id", query.get("topic_id", [None]))[0]
            if not topic_id:
                self._send_json({"error": "Missing 'id' or 'topic_id' query parameter"}, 400)
                return
            inc_views = query.get("increment_views", ["1"])[0] not in ("0", "false", "no")
            topic = cyberspace_board.get_topic(topic_id, increment_views=inc_views)
            if not topic:
                self._send_json({"error": f"Topic '{topic_id}' not found"}, 404)
                return
            self._send_json({"status": "ok", "topic": topic}, 200)
        elif parsed.path == "/api/board/search":
            query = parse_qs(parsed.query)
            q_str = query.get("q", query.get("query", [""]))[0]
            mode = query.get("mode", ["hybrid"])[0]
            top_k = int(query.get("top_k", ["10"])[0])
            max_hops = int(query.get("max_hops", ["2"])[0])
            res = cyberspace_board.search(query=q_str, mode=mode, top_k=top_k, max_hops=max_hops)
            self._send_json(res, 200)
        elif parsed.path == "/api/board/query":
            # Single search bar: #topics, @people/@agents, is:verified, /search, /topic.
            query = parse_qs(parsed.query)
            q_str = query.get("q", [""])[0]
            try:
                top_k = max(1, min(int(query.get("top_k", ["15"])[0]), 50))
            except ValueError:
                top_k = 15
            sort_by = query.get("sort_by", ["hot"])[0]
            self._send_json(cyberspace_board.unified_search(q_str, top_k=top_k, sort_by=sort_by), 200)
        elif parsed.path == "/api/board/suggest":
            query = parse_qs(parsed.query)
            try:
                limit = int(query.get("limit", ["6"])[0])
            except ValueError:
                limit = 6
            self._send_json(cyberspace_board.suggest(query.get("q", [""])[0], limit=limit), 200)
        elif parsed.path == "/api/board/ai-suggest":
            query = parse_qs(parsed.query)
            try:
                limit = int(query.get("limit", ["8"])[0])
            except ValueError:
                limit = 8
            self._send_json(cyberspace_board.ai_suggest(query.get("q", [""])[0], limit=limit), 200)
        elif parsed.path == "/api/board/trending":
            query = parse_qs(parsed.query)
            try:
                days = float(query.get("days", ["7"])[0])
                limit = int(query.get("limit", ["6"])[0])
            except ValueError:
                days, limit = 7.0, 6
            self._send_json(cyberspace_board.trending(window_days=days, limit=limit), 200)
        elif parsed.path == "/api/board/graph":
            self._send_json(cyberspace_board.graphrag.get_full_graph_snapshot(), 200)
        elif parsed.path == "/api/board/graph/path":
            query = parse_qs(parsed.query)
            src = query.get("from", query.get("source", [""]))[0]
            dst = query.get("to", query.get("target", [""]))[0]
            max_hops = int(query.get("max_hops", ["5"])[0])
            self._send_json(cyberspace_board.graphrag.find_entity_path(src, dst, max_hops=max_hops), 200)
        elif parsed.path == "/api/board/roster":
            self._send_json(cyberspace_board.get_roster_and_profiles(), 200)
        elif parsed.path == "/api/board/profile":
            query = parse_qs(parsed.query)
            user_or_peer = query.get("user", query.get("username", query.get("peer_id", [""])))[0]
            if not user_or_peer:
                self._send_json({"error": "Missing 'user' or 'peer_id' query parameter"}, 400)
                return
            self._send_json(cyberspace_board.get_user_profile(user_or_peer), 200)
        elif parsed.path == "/api/verify/status":
            query = parse_qs(parsed.query)
            peer_id = query.get("peer_id", query.get("peer", [None]))[0]
            username = query.get("username", query.get("user", [None]))[0]
            if not peer_id and not username:
                self._send_json({"error": "Missing 'peer_id' or 'username' query parameter"}, 400)
                return
            self._send_json(cyberspace_board.get_verification_status(peer_id=peer_id or "", username=username), 200)
        elif parsed.path == "/api/verify/list":
            self._send_json(cyberspace_board.list_verifications(), 200)
        elif parsed.path == "/api/moderator/banned":
            self._send_json({"banned_peers": list(banned_peers.values()), "count": len(banned_peers)}, 200)
        elif parsed.path == "/api/moderator/artifacts":
            self._send_json({"reported_artifacts": reported_artifacts, "count": len(reported_artifacts)}, 200)
        elif parsed.path == "/api/status":
            audit = scale.evaluate_current_and_future()
            self._send_json({
                "status": "online",
                "service": "iot-federated-agent-memory",
                "readiness_tier": audit["readiness_tier"],
                "composite_score": audit["composite_iot_scale_score"],
                "active_webrtc_streams": relay.get_active_streams(),
                "ai_providers": {k: v.available_credits for k, v in router.providers.items()},
                "tincan_relay": tincan_relay.get_stats(),
                "mesh_os": {
                    "xp": mesh_os.total_xp,
                    "tier": mesh_os.get_tier_info(),
                },
            })
        elif parsed.path == "/api/streams":
            self._send_json(relay.get_active_streams())
        elif parsed.path == "/api/providers":
            self._send_json(router.get_analytics()["providers"])
        elif parsed.path == "/api/models/analytics":
            self._send_json(router.get_analytics())
        elif parsed.path == "/api/gateway/telemetry":
            query = parse_qs(parsed.query)
            scope, owner_id = self._resolve_space_query(query)
            sm = _get_space_manager()
            try:
                sp = sm.get_or_create_space(scope, owner_id)
            except Exception:
                sp = None
            telemetry = collect_gateway_telemetry(router, space_owner=owner_id, vfs=sp)
            model_q = (query.get("model", [""])[0] or "").strip()
            if model_q:
                try:
                    prompt_chars = int(query.get("prompt_chars", ["0"])[0] or "0")
                except ValueError:
                    prompt_chars = 0
                telemetry["preflight"] = estimate_preflight(model_q, prompt_chars=prompt_chars, router=router)
            self._send_json(telemetry, 200)
        elif parsed.path == "/api/tokens/summary":
            query = parse_qs(parsed.query)
            session_acc = self._session_account()
            req_peer = (query.get("peer_id", [None])[0] or "").strip()
            acct_summary = None
            if req_peer:
                candidate = account_registry.get_billing_summary(req_peer)
                if isinstance(candidate, dict) and "error" not in candidate:
                    acct_summary = candidate
            if acct_summary is None and session_acc:
                sid = session_acc.get("peer_id")
                candidate = account_registry.get_billing_summary(sid) if sid else None
                acct_summary = candidate if (isinstance(candidate, dict) and "error" not in candidate) else session_acc
            analytics_data = router.get_analytics(include_live_billing=False) if hasattr(router, "get_analytics") else {}
            sponsor_state = sponsor_manager.get_state() if hasattr(sponsor_manager, "get_state") else {}
            payload = build_token_summary(
                account=acct_summary,
                analytics=analytics_data,
                sponsor_state=sponsor_state,
                daily_ad_cap=AD_DAILY_REWARD_CAP,
            )
            payload["rodin"] = _get_hyper3d_billing(router)
            self._send_json(payload, 200)
        elif parsed.path == "/api/tokens/mint-requests":
            query = parse_qs(parsed.query)
            peer_filter = (query.get("peer_id", [None])[0] or "").strip()
            status_filter = (query.get("status", [None])[0] or "").strip().lower()
            is_admin = self._is_admin_request()
            session_acc = self._session_account()
            with _mint_requests_lock:
                items = list(reversed(_mint_requests))
            if peer_filter:
                items = [r for r in items if r["peer_id"] == peer_filter or r["target_peer_id"] == peer_filter]
            elif not is_admin:
                if session_acc:
                    sid = session_acc.get("peer_id")
                    items = [r for r in items if r["peer_id"] == sid or r["target_peer_id"] == sid]
                else:
                    items = []
            if status_filter:
                items = [r for r in items if r["status"].lower() == status_filter]
            pending_count = sum(1 for r in items if r["status"] == "pending")
            self._send_json({
                "requests": items,
                "pending_count": pending_count,
                "admin_authenticated": is_admin,
            }, 200)
        elif parsed.path == "/api/tincan/inbox":
            query = parse_qs(parsed.query)
            address = query.get("address", query.get("addr", [None]))[0]
            since_seq_str = query.get("since_seq", query.get("since", ["0"]))[0]
            timeout_str = query.get("timeout", ["0.0"])[0]
            try:
                since_seq = int(since_seq_str)
            except ValueError:
                since_seq = 0
            try:
                timeout = float(timeout_str)
            except ValueError:
                timeout = 0.0

            if not address:
                self._send_json({"error": "Missing 'address' or 'addr' query parameter"}, 400)
                return
            try:
                res = tincan_relay.inbox(address, since_seq=since_seq, timeout=timeout)
                mesh_os.award_xp(address.split("@")[0], "inbox_decryption")
                self._send_json(res)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as exc:
                self._send_json({"error": str(exc)}, 500)
        elif parsed.path == "/api/tincan/whoami":
            query = parse_qs(parsed.query)
            address = query.get("address", query.get("addr", [None]))[0]
            res = tincan_relay.whoami(address)
            self._send_json(res)
        elif parsed.path == "/api/version":
            self._send_json({
                "service": "tincan",
                "commit": COMMIT_HASH,
                "version": "2.2.0",
                "relay_url": "https://iot-federated-agent-memory-production.up.railway.app",
            })
        elif parsed.path == "/api/account/session":
            account = self._session_account()
            if not account:
                self._send_json({"signed_in": False}, 200)
            else:
                self._send_json({"signed_in": True, "peer_id": account["peer_id"],
                                 "username": account.get("username"),
                                 "token_balance": account.get("token_balance"),
                                 "credit_balance_usd": account.get("credit_balance_usd")}, 200)
        elif parsed.path == "/api/mesh/arena/models":
            models = router.get_arena_models()
            self._send_json({"models": models, "count": len(models), "default": router.arena_default_pair()}, 200)
        elif parsed.path == "/api/models/nanogpt":
            query = parse_qs(parsed.query)
            live = query.get("live", ["1"])[0].lower() not in ("0", "false", "no")
            force = query.get("refresh", ["0"])[0].lower() in ("1", "true", "yes")
            models = (
                router.get_nanogpt_models(force_refresh=force, include_live_public=live)
                if hasattr(router, "get_nanogpt_models")
                else []
            )
            models = filter_gateway_models(
                models,
                category=query.get("category", [""])[0],
                exact_category=True,
                uncensored=query.get("uncensored", ["0"])[0].lower() in ("1", "true", "yes"),
                tee=query.get("tee", ["0"])[0].lower() in ("1", "true", "yes"),
                subscription=query.get("subscription", ["0"])[0].lower() in ("1", "true", "yes"),
                search=query.get("q", [""])[0],
            )
            self._send_json({"models": models, "count": len(models), "gateway": "nanogpt"}, 200)
        elif parsed.path in ("/api/models/available", "/api/models/openrouter"):
            query = parse_qs(parsed.query)
            gateway = (query.get("gateway", ["all"])[0] or "all").strip().lower()
            search_q = query.get("q", [""])[0]
            if gateway == "nanogpt" and hasattr(router, "get_nanogpt_models"):
                models = router.get_nanogpt_models(include_live_public=True)
            elif gateway == "ollama" and hasattr(router, "get_ollama_models"):
                models = router.get_ollama_models()
            else:
                models = router.get_available_models() if hasattr(router, "get_available_models") else []
                if gateway in ("openrouter", "ronin"):
                    models = [m for m in models if str(m.get("gateway", "openrouter")).lower() == gateway]
            models = filter_gateway_models(models, search=search_q)
            self._send_json({"models": models, "count": len(models)}, 200)
        elif parsed.path == "/api/spaces":
            query = parse_qs(parsed.query)
            scope = query.get("scope", [None])[0]
            sm = _get_space_manager()
            spaces = sm.list_spaces(scope=scope) if hasattr(sm, "list_spaces") else []
            self._send_json({"spaces": spaces, "count": len(spaces)}, 200)
        elif parsed.path == "/api/3d/balance":
            billing = _get_hyper3d_billing(router)
            self._send_json(billing, 200)
        elif parsed.path == "/api/browser/state":
            query = parse_qs(parsed.query)
            sid = query.get("session_id", [""])[0].strip()
            bm = _get_browser_manager()
            if sid:
                inc = query.get("screenshot", ["1"])[0].lower() not in ("0", "false", "no")
                self._send_json(bm.get_state(sid, include_screenshot=inc), 200)
            else:
                self._send_json(bm.status(), 200)
        elif parsed.path == "/api/browser/screenshot":
            query = parse_qs(parsed.query)
            sid = query.get("session_id", [""])[0].strip()
            if not sid:
                self._send_json({"ok": False, "error": "Missing 'session_id'"}, 400)
                return
            bm = _get_browser_manager()
            st = bm.get_state(sid, include_screenshot=True)
            b64 = st.get("screenshot_b64") or ""
            raw = base64.b64decode(b64) if b64 else b""
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if raw:
                self.wfile.write(raw)
        elif parsed.path == "/api/browser/proxy":
            query = parse_qs(parsed.query)
            target_url = query.get("url", [""])[0].strip()
            if not target_url:
                self._send_json({"ok": False, "error": "Missing 'url' query parameter"}, 400)
                return
            try:
                bm = _get_browser_manager()
                self._send_json(bm.fetch_reader_proxy(target_url), 200)
            except ValueError as ve:
                self._send_json({"ok": False, "error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 502)
        elif parsed.path in ("/api/nodes/health", "/api/health"):
            self._send_json(_node_studio_health(dict(self.headers)), 200)
        elif parsed.path == "/api/atlas/health":
            self._send_json(_atlas_health(ai_router=router), 200)
        elif parsed.path == "/api/atlas/operations/status":
            query = parse_qs(parsed.query)
            op_id = (
                query.get("operation_id", [""])[0]
                or query.get("id", [""])[0]
                or query.get("op_id", [""])[0]
            ).strip()
            code, res = _atlas_operation_status(op_id, ai_router=router)
            self._send_json(res, code)
        elif parsed.path == "/api/nodes/state":
            query = parse_qs(parsed.query)
            modality = _normalize_node_modality(query.get("modality", ["image"])[0])
            self._send_json(_node_studio_state(modality), 200)
        elif parsed.path == "/api/nodes/graphs":
            query = parse_qs(parsed.query)
            scope = query.get("scope", ["user"])[0]
            owner_id = query.get("owner_id", query.get("peer_id", ["default"]))[0]
            code, res = _node_graph_list(scope=scope, owner_id=owner_id)
            self._send_json(res, code)
        elif parsed.path == "/api/nodes/graph":
            query = parse_qs(parsed.query)
            scope = query.get("scope", ["user"])[0]
            owner_id = query.get("owner_id", query.get("peer_id", ["default"]))[0]
            path = query.get("path", [""])[0] or None
            name = query.get("name", [""])[0] or None
            code, res = _node_graph_load(scope=scope, owner_id=owner_id, path=path, name=name)
            self._send_json(res, code)
        elif parsed.path == "/api/workstation/status":
            query = parse_qs(parsed.query)
            scope, owner_id = self._resolve_space_query(query)
            sm = _get_space_manager()
            sp = sm.get_or_create_space(scope, owner_id)
            sp_summary = sp.get_summary()

            ng_key = getattr(router, "nanogpt_key", None)
            nanogpt_configured = bool(ng_key if ng_key is not None else os.environ.get("NANOGPT_API_KEY"))
            nanogpt_models = (
                router.get_nanogpt_models(include_live_public=False)
                if hasattr(router, "get_nanogpt_models")
                else []
            )
            self._send_json({
                "rodin": _get_hyper3d_billing(router),
                "rodin_tiers": dict(RODIN_TIER_PRICING_USD),
                "nanogpt": {
                    "configured": nanogpt_configured,
                    "total_count": len(nanogpt_models),
                    "tee_count": len(filter_gateway_models(nanogpt_models, tee=True)),
                    "heretic_count": len(filter_gateway_models(nanogpt_models, uncensored=True)),
                },
                "space": {
                    "scope": sp_summary.get("scope", scope),
                    "owner_id": sp_summary.get("owner_id", owner_id),
                    "merkle_root": sp_summary.get("merkle_root", ""),
                    "file_count": sp_summary.get("file_count", 0),
                },
                "drive_mirror": self._drive_status_payload(include_root=True),
            }, 200)
        elif parsed.path.startswith("/api/drive/"):
            self._handle_drive_get(parsed)
        elif parsed.path == "/api/space/notes":
            query = parse_qs(parsed.query)
            scope, owner_id = self._resolve_space_query(query)
            raw_status = query.get("status", ["pending"])[0]
            note_status = None if raw_status == "all" else raw_status
            try:
                sp, editor = self._get_notes_editor(scope, owner_id)
                self._send_json({
                    "notes": editor.list_notes(status=note_status),
                    "versions": editor.list_versions(),
                    "merkle_root": sp.compute_merkle_root(),
                }, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/space/ls":
            query = parse_qs(parsed.query)
            scope = query.get("scope", ["user"])[0]
            owner_id = query.get("owner_id", query.get("peer_id", query.get("topic_id", ["default_user"])))[0]
            sm = _get_space_manager()
            sp = sm.get_or_create_space(scope, owner_id)
            self._send_json(sp.get_summary(), 200)
        elif parsed.path == "/api/pages/list":
            query = parse_qs(parsed.query)
            scope, owner_id = self._resolve_space_query(query)
            sm = _get_space_manager()
            sp = sm.get_or_create_space(scope, owner_id)
            self._send_json(list_space_page_entrypoints(sp, scope, owner_id), 200)
        elif parsed.path == "/api/space/file":
            query = parse_qs(parsed.query)
            scope = query.get("scope", ["user"])[0]
            owner_id = query.get("owner_id", query.get("peer_id", query.get("topic_id", ["default_user"])))[0]
            path = query.get("path", ["/src/main.py"])[0]
            raw_flag = query.get("raw", ["0"])[0].strip().lower() in ("1", "true", "yes")
            sm = _get_space_manager()
            sp = sm.get_or_create_space(scope, owner_id)
            try:
                rec = sp.read_file(path, as_text=not raw_flag)
                if raw_flag:
                    raw_bytes = base64.b64decode(rec.get("content_b64") or "")
                    ctype = guess_mime_type(path, rec.get("mime_type") or "")
                    self.send_response(200)
                    self.send_header("Content-Type", ctype)
                    self.send_header("Content-Length", str(len(raw_bytes)))
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    if getattr(self, "command", "GET") != "HEAD":
                        self.wfile.write(raw_bytes)
                    return
                self._send_json(rec, 200)
            except FileNotFoundError as fe:
                self._send_json({"error": str(fe)}, 404)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/space/export":
            query = parse_qs(parsed.query)
            scope = query.get("scope", ["user"])[0]
            owner_id = query.get("owner_id", query.get("peer_id", query.get("topic_id", ["default_user"])))[0]
            sm = _get_space_manager()
            sp = sm.get_or_create_space(scope, owner_id)
            summary = sp.get_summary()
            b64_data = sm.export_space_b64(scope, owner_id) if hasattr(sm, "export_space_b64") else base64.b64encode(sp.export_space_bytes()).decode("ascii")
            self._send_json({
                "filename": f"{owner_id}.space",
                "scope": scope,
                "owner_id": owner_id,
                "size_bytes": len(base64.b64decode(b64_data)),
                "merkle_root": summary.get("merkle_root", ""),
                "space_b64": b64_data,
            }, 200)
        elif parsed.path == "/api/wasm/manifest":
            sm = _get_space_manager()
            manifest = sm.get_wasm_manifest() if hasattr(sm, "get_wasm_manifest") else {
                "artcraft_apps": ARTCRAFT_WASM_APPS,
                "wasm_runtimes": WASM_RUNTIMES,
                "contract": WASM_POSTMESSAGE_CONTRACT,
            }
            self._send_json(manifest, 200)
        elif parsed.path == "/api/artcraft/launcher":
            sm = _get_space_manager()
            status = sm.get_artcraft_launcher_status() if hasattr(sm, "get_artcraft_launcher_status") else {
                "getartcraft_url": "https://getartcraft.com",
                "craft_launcher_releases_url": "https://github.com/storytold/craft-launcher/releases/latest",
            }
            self._send_json(status, 200)
        elif parsed.path == "/api/crdt/state":
            self._send_json({
                "node_id": crdt_node.local_node_id,
                "vector_clock": crdt_node.vector_clock,
                "merkle_root": crdt_node.compute_merkle_root(),
                "state_store": crdt_node.state_store,
                "delta_count": len(crdt_node.delta_log),
            }, 200)
        elif parsed.path == "/api/telemetry/state":
            wallet_id = mqtt_adapter.wallet_id or "mesh-default"
            self._send_json({
                "wallet_id": wallet_id,
                "wallet_balance_usd": vending_machine.get_balance(wallet_id),
                "cost_per_batch_usd": vending_machine.cost_per_batch,
                "pending_batch_count": len(mqtt_adapter.pending_batch),
                "ingested_nodes_count": len(mqtt_adapter.ingestor.buffer),
                "ingested_nodes": mqtt_adapter.ingestor.buffer[-25:],
                "receipts": [r.to_dict() for r in mqtt_adapter.receipts[-10:]],
            }, 200)
        elif parsed.path == "/api/terminal/brew":
            from iot_federated_agent_memory.tincan_brew import BREW_CATALOG, load_cellar_state

            state = load_cellar_state()
            self._send_json(
                {
                    "status": "ok",
                    "taps": state.get("taps", []),
                    "installed": state.get("installed", {}),
                    "catalog": BREW_CATALOG,
                },
                200,
            )
        elif parsed.path == "/api/terminal/harnesses":
            from iot_federated_agent_memory.tincan_brew import discover_harnesses

            self._send_json(discover_harnesses(), 200)
        elif parsed.path == "/api/terminal/pty/ws":
            qs = parse_qs(parsed.query)
            sid = (qs.get("session_id") or [""])[0].strip()
            sess = _get_pty_manager().get(sid)
            if not sess:
                self._send_json({"status": "error", "error": f"Unknown PTY session '{sid}'"}, 404)
                return
            ws_key = self.headers.get("Sec-WebSocket-Key")
            if self.headers.get("Upgrade", "").lower() != "websocket" or not ws_key:
                self._send_json({"status": "error", "error": "WebSocket upgrade required"}, 426)
                return
            accept = base64.b64encode(
                hashlib.sha1((ws_key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest()
            ).decode("ascii")
            self.close_connection = True
            handshake = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
            ).encode("ascii")
            self.connection.sendall(handshake)

            write_lock = threading.Lock()
            stop_ev = threading.Event()

            def _pump_out() -> None:
                offset = 0
                while not stop_ev.is_set():
                    chunk, offset, closed = sess.read_since(offset, timeout=0.25)
                    if chunk:
                        if not _ws_send_frame(self.connection, 0x2, chunk, write_lock):
                            break
                    if closed and offset >= sess._total_bytes:
                        _ws_send_frame(self.connection, 0x8, b"", write_lock)
                        break

            pump_thread = threading.Thread(target=_pump_out, daemon=True)
            pump_thread.start()
            try:
                while not stop_ev.is_set():
                    frame = _ws_recv_frame(self.connection)
                    if frame is None:
                        break
                    opcode, payload = frame
                    if opcode == 0x8:
                        _ws_send_frame(self.connection, 0x8, b"", write_lock)
                        break
                    if opcode == 0x9:
                        _ws_send_frame(self.connection, 0xA, payload, write_lock)
                    elif opcode in (0x1, 0x2):
                        if payload.startswith(b"\x01{"):
                            try:
                                ctrl = json.loads(payload[1:].decode("utf-8"))
                                if ctrl.get("type") == "resize":
                                    sess.resize(int(ctrl.get("cols") or 100), int(ctrl.get("rows") or 30))
                            except Exception:
                                pass
                        else:
                            sess.write(payload)
            finally:
                stop_ev.set()
                pump_thread.join(timeout=1.0)
            return
        elif parsed.path == "/api/terminal/pty/stream":
            qs = parse_qs(parsed.query)
            sid = (qs.get("session_id") or [""])[0].strip()
            sess = _get_pty_manager().get(sid)
            if not sess:
                self._send_json({"status": "error", "error": f"Unknown PTY session '{sid}'"}, 404)
                return
            self.close_connection = True
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Accel-Buffering", "no")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            offset = 0
            try:
                while True:
                    chunk, offset, closed = sess.read_since(offset, timeout=0.4)
                    if chunk:
                        msg = f"data: {json.dumps({'b64': base64.b64encode(chunk).decode('ascii')})}\n\n".encode("utf-8")
                        self.wfile.write(msg)
                        self.wfile.flush()
                    else:
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()
                    if closed and offset >= sess._total_bytes:
                        self.wfile.write(f"event: close\ndata: {json.dumps({'exit_code': sess.exit_code})}\n\n".encode("utf-8"))
                        self.wfile.flush()
                        break
            except (OSError, BrokenPipeError):
                pass
            return
        elif parsed.path in ("/Formula/tincan.rb", "/Formula/context-palace.rb", "/tincan.rb"):
            from iot_federated_agent_memory.tincan_brew import generate_homebrew_formula

            fname = "context-palace" if "context-palace" in parsed.path else "tincan"
            rb_code = generate_homebrew_formula(fname).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/x-ruby; charset=utf-8")
            self.send_header("Content-Length", str(len(rb_code)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self._write_body(rb_code)
        elif parsed.path in ("/install.sh", "/install_peer.sh", "/install.command"):
            install_script_path = os.path.join(os.path.dirname(__file__), "install_peer.sh")
            if os.path.exists(install_script_path):
                with open(install_script_path, "rb") as f:
                    content = f.read()
                if parsed.path == "/install.command":
                    # Add explicit interactive pause at end of macOS .command so Terminal stays open with status
                    pause_suffix = b'\necho ""\nread -r -p "Press [Enter] to launch tincan or Ctrl+C to close..." _ || true\n"$HOME/.local/bin/tincan" --help || true\n'
                    content = content + pause_suffix
                self.send_response(200)
                if parsed.path == "/install.command":
                    self.send_header("Content-Type", "application/octet-stream")
                    self.send_header("Content-Disposition", 'attachment; filename="Install-TinCan.command"')
                else:
                    self.send_header("Content-Type", "text/x-shellscript; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self._write_body(content)
            else:
                self._send_empty(404)
        elif parsed.path == "/download/bundle.tar.gz":
            # Privacy Guard: Workspace tarball download is disabled to prevent leaking local files or PII.
            self._send_json({"error": "Bundle download disabled for privacy and security protection."}, 403)
        else:
            self._send_empty(404)


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), MeshGatewayHandler)
    print(f"[*] IoT Federated Agent Mesh listening on port {PORT}")
    server.serve_forever()


# ---------------------------------------------------------------------------
# FastAPI & TestClient Compatibility Layer
# ---------------------------------------------------------------------------
try:
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    _HAS_FASTAPI = True
except ImportError:
    _HAS_FASTAPI = False
    class HTMLResponse:
        def __init__(self, content: str = "", status_code: int = 200, media_type: str = "text/html; charset=utf-8"):
            self.content = content
            self.text = content if isinstance(content, str) else content.decode("utf-8") if isinstance(content, bytes) else str(content)
            self.status_code = status_code
            self.media_type = media_type

class _FastAPIRouteHandler:
    def __init__(self):
        self.routes = {}
        self.post_routes = {}

    def get(self, path: str):
        def decorator(fn):
            self.routes[path] = fn
            return fn
        return decorator

    def post(self, path: str):
        def decorator(fn):
            self.post_routes[path] = fn
            return fn
        return decorator

    def handle(self, method: str, path: str):
        clean_path = path.split("?")[0].rstrip("/") if path.split("?")[0] != "/" else "/"
        if method.upper() == "POST" and clean_path in self.post_routes:
            res = self.post_routes[clean_path]()
            return res if hasattr(res, "status_code") else HTMLResponse(json.dumps(res), 200)
        if clean_path in self.routes:
            res = self.routes[clean_path]()
            return res if hasattr(res, "status_code") else HTMLResponse(str(res), 200)
        if clean_path.startswith("/car/"):
            mode = clean_path[len("/car/"):]
            if "/car/{mode}" in self.routes:
                res = self.routes["/car/{mode}"](mode)
                return res if hasattr(res, "status_code") else HTMLResponse(str(res), 200)
        if clean_path.startswith("/ios/"):
            screen = clean_path[len("/ios/"):]
            if "/ios/{screen}" in self.routes:
                res = self.routes["/ios/{screen}"](screen)
                return res if hasattr(res, "status_code") else HTMLResponse(str(res), 200)
        return HTMLResponse("Not Found", 404)

if _HAS_FASTAPI:
    app = FastAPI(title="TinCan Car & Mesh OS")
else:
    app = _FastAPIRouteHandler()

@app.get("/car")
def _car_root():
    mode = "driving"
    return HTMLResponse(render_car_headunit_html(mode) if render_car_headunit_html else "<h1>Car Head Unit</h1>")

@app.get("/car/{mode}")
def _car_mode(mode: str):
    return HTMLResponse(render_car_headunit_html(mode) if render_car_headunit_html else f"<h1>Car Head Unit: {mode}</h1>")

@app.get("/ios")
def _ios_root():
    if ios_preview is not None and hasattr(ios_preview, "render_ios_simulator_html"):
        return HTMLResponse(ios_preview.render_ios_simulator_html("01-onboarding"))
    return HTMLResponse("<!DOCTYPE html><html><body><h1>TinCan iOS Simulator</h1></body></html>")

@app.get("/ios/{screen}")
def _ios_screen(screen: str):
    if ios_preview is not None and hasattr(ios_preview, "render_ios_simulator_html"):
        return HTMLResponse(ios_preview.render_ios_simulator_html(screen))
    return HTMLResponse(f"<!DOCTYPE html><html><body><h1>TinCan iOS Simulator: {screen}</h1></body></html>")

@app.get("/designs")
def _designs_root():
    return HTMLResponse(render_designs_gallery_html() if render_designs_gallery_html else "<h1>Design Mockups</h1>")

@app.get("/mockups")
def _mockups_root():
    return HTMLResponse(render_designs_gallery_html() if render_designs_gallery_html else "<h1>Design Mockups</h1>")

@app.get("/fono")
def _fono_root():
    fp = os.path.join(os.path.dirname(__file__), "docs", "designs", "ios-app", "html", "00-fono.html")
    if os.path.isfile(fp):
        with open(fp, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>Aeonik Fono Mobile UI</h1>")

@app.get("/aeonik")
def _aeonik_root():
    return _fono_root()

@app.get("/nodes")
def _nodes_root(modality: str = "image", view: str = "editor"):
    return HTMLResponse(_render_node_studio_page(modality=modality, view=view))

@app.get("/gemini-node-studio")
def _gemini_node_studio_root(modality: str = "image", view: str = "editor"):
    return HTMLResponse(_render_node_studio_page(modality=modality, view=view))

@app.get("/nodes/timeline")
def _nodes_timeline(modality: str = "image"):
    return HTMLResponse(_render_node_studio_page(modality=modality, view="timeline"))

@app.get("/nodes/gateway")
def _nodes_gateway(modality: str = "image"):
    return HTMLResponse(_render_node_studio_page(modality=modality, view="gateway"))

@app.get("/api/nodes/health")
def _nodes_health():
    return _node_studio_health()

@app.get("/api/health")
def _api_health():
    return _node_studio_health()

@app.get("/api/nodes/state")
def _nodes_state(modality: str = "image"):
    return _node_studio_state(modality=modality)

@app.get("/api/nodes/graphs")
def _nodes_graphs_list(scope: str = "user", owner_id: str = "default"):
    _, res = _node_graph_list(scope=scope, owner_id=owner_id)
    return res

@app.get("/api/nodes/graph")
def _nodes_graph_get(scope: str = "user", owner_id: str = "default", path: Optional[str] = None, name: Optional[str] = None):
    _, res = _node_graph_load(scope=scope, owner_id=owner_id, path=path, name=name)
    return res

@app.post("/api/nodes/graph")
def _nodes_graph_post(payload: Optional[Dict[str, Any]] = None):
    _, res = _node_graph_save(payload or {})
    return res

@app.post("/api/nodes/generate")
def _nodes_generate(payload: Optional[Dict[str, Any]] = None):
    _, res = _node_studio_generate(payload or {})
    return res

@app.post("/api/generate")
def _api_generate(payload: Optional[Dict[str, Any]] = None):
    _, res = _node_studio_generate(payload or {})
    return res

@app.post("/api/nodes/filter")
def _nodes_filter(payload: Optional[Dict[str, Any]] = None):
    _, res = _node_studio_filter(payload or {})
    return res

@app.get("/api/atlas/health")
def _api_atlas_health():
    return _atlas_health(ai_router=router)

@app.post("/api/atlas/assets/upload")
def _api_atlas_assets_upload(payload: Optional[Dict[str, Any]] = None):
    _, res = _atlas_upload_asset(payload or {}, ai_router=router)
    return res

@app.post("/api/atlas/tasks/run")
def _api_atlas_tasks_run(payload: Optional[Dict[str, Any]] = None):
    _, res = _atlas_run_task(payload or {}, ai_router=router)
    return res

@app.get("/api/atlas/operations/status")
def _api_atlas_operations_status_get(operation_id: str = ""):
    _, res = _atlas_operation_status(operation_id, ai_router=router)
    return res

@app.post("/api/atlas/operations/status")
def _api_atlas_operations_status_post(payload: Optional[Dict[str, Any]] = None):
    data = payload or {}
    op_id = (data.get("operation_id") or data.get("id") or data.get("op_id") or "").strip()
    _, res = _atlas_operation_status(op_id, ai_router=router)
    return res

@app.post("/api/atlas/operations/download")
def _api_atlas_operations_download(payload: Optional[Dict[str, Any]] = None):
    _, res = _atlas_download_operation(payload or {}, ai_router=router)
    return res

@app.post("/api/audio/generate")
def _api_audio_generate(payload: Optional[Dict[str, Any]] = None):
    _, res = _audio_generate_and_save(payload or {}, ai_router=router)
    return res

@app.post("/api/omni/route")
def _api_omni_route(payload: Optional[Dict[str, Any]] = None):
    _, res = _omni_route(payload or {}, ai_router=router)
    return res
