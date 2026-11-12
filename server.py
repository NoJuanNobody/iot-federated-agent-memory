#!/usr/bin/env python3
import gzip
import hashlib
import hmac
import io
import json
import os
import secrets
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
from typing import Any, Dict, List, Optional
from http.server import ThreadingHTTPServer as HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from iot_federated_agent_memory.scale import IoTFederatedMemoryScale
from iot_federated_agent_memory.webrtc_relay import WebRTCSignalingRelay
from iot_federated_agent_memory.ai_gateway import DynamicAIGatewayRouter
from iot_federated_agent_memory.tincan_relay import TinCanBlindRelay
from iot_federated_agent_memory.video_playlist import RelayVideoPlaylist
from iot_federated_agent_memory.mesh_os_engine import TinCanMeshOSEngine
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI
from iot_federated_agent_memory.account_registry import (
    EMAIL_EXISTS_MESSAGE,
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
from iot_federated_agent_memory.cyberspace_board import CyberspaceBoardEngine
from iot_federated_agent_memory.crdt_mesh import CRDTMeshGossipSync, CRDTDeltaMessage
from iot_federated_agent_memory.edge_telemetry import (
    EdgeTelemetryIngestor,
    HMACVendingMachine,
    MQTTTelemetryClientAdapter,
    CreditExhaustionError,
)
from dataclasses import asdict

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
    tier_costs = {"Regular": 0.50, "Sketch": 0.25, "Detail": 1.00, "Smooth": 0.75}
    cost = tier_costs.get(tier, 0.50)
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
        "tier_pricing_usd": {
            "Regular": 0.50,
            "Sketch": 0.25,
            "Detail": 1.00,
            "Smooth": 0.75,
        },
    }


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

# Register seed peers for live dashboard (IP addresses redacted, peripherals OFF by default)
relay.register_peer("peer-primary-mac", "Mac Studio (M1 Chip)", "redacted", 50004, has_video=False, has_audio=False, has_screen=False)
relay.register_peer("peer-secondary-node", "Collaborator Node", "redacted", 50006, has_video=False, has_audio=False, has_screen=False)

# Moderator registry for space/mesh bans & reported digital artifacts
banned_peers: Dict[str, Dict[str, Any]] = {}
reported_artifacts: List[Dict[str, Any]] = []

HTML_UI = MESH_OS_HTML_UI


def _get_html_Entry(html_str: str):
    key = id(html_str)
    entry = _html_cache.get(key)
    if entry is None:
        raw = html_str.encode("utf-8")
        gz = gzip.compress(raw, compresslevel=6)
        etag = f'"{hashlib.sha256(raw).hexdigest()[:16]}"'
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

    def _send_empty(self, code: int = 204) -> None:
        self.send_response(code)
        self.send_header("Content-Length", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def _send_json(self, data, code=200):
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
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self._write_body(body)

    def do_HEAD(self):
        self.do_GET()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def _client_key(self) -> str:
        fwd = (self.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
        return fwd or (self.client_address[0] if self.client_address else "unknown")

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
                self._send_json({"status": "passkey_registered", "account": account}, 200)
            elif path == "/api/passkey/login/options":
                rp_id, origins = resolve_relying_party(host)
                out = passkey_auth.begin_authentication(peer_id, rp_id, origins, email=str(data.get("email") or ""))
                self._send_json(out, 200)
            elif path == "/api/passkey/login/verify":
                account = passkey_auth.finish_authentication(peer_id, str(data.get("challenge_id") or ""), data.get("credential"))
                self._send_json({"status": "signed_in", "account": account}, 200)
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

    def do_POST(self):
        parsed = urlparse(self.path)
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
                completion = router.dispatch_completion(
                    alias=model_alias,
                    messages=messages,
                    temperature=float(data.get("temperature", 0.7)),
                    max_tokens=int(data.get("max_tokens", 512)),
                )
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
                if not alias or not new_model:
                    self._send_json({"error": "Missing 'alias' or 'model'"}, 400)
                    return
                updated_config = router.set_model(alias, new_model, display_name)
                self._send_json({
                    "status": "updated",
                    "alias": alias,
                    "model": updated_config.model_alias,
                    "display_name": updated_config.display_name,
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
                award = mesh_os.award_xp(
                    peer_id=peer_id,
                    action_key=action_key,
                    display_name=data.get("display_name"),
                )
                flight = mesh_os.record_flight(
                    from_node=data.get("from_node") or peer_id,
                    to_node=data.get("to_node") or "relay",
                    kind=action_key,
                    label=action_key,
                )
                self._send_json({"status": "awarded", "award": award, "flight": flight}, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/mesh/arena/vote":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = data.get("peer_id") or "peer"
                winner_alias = data.get("winner_alias") or "gemini-brain"
                res = mesh_os.vote_arena(
                    peer_id=peer_id,
                    winner_alias=winner_alias,
                    prompt_preview=data.get("prompt_preview", ""),
                    display_name=data.get("display_name"),
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
                if is_new and not body["has_passkey"]:
                    # Brand-new account: allow this browser to attach its first passkey.
                    body["enroll_token"] = passkey_auth.issue_enrollment_grant(account["peer_id"], purpose="signup")
                self._send_json(body, 201)
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
            admin_key = self.headers.get("X-Admin-Key", "")
            if not TINCAN_ADMIN_KEY or not hmac.compare_digest(admin_key, TINCAN_ADMIN_KEY):
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
                sponsor_id = data.get("sponsor_id") or ""
                creative = next((s for s in sponsor_manager.sponsors if s.id == sponsor_id), None)
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
                    locked=data.get("locked"),
                    resolved=data.get("resolved"),
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

                res = _dispatch_rodin(
                    router,
                    prompt=prompt,
                    images=images,
                    tier=tier,
                    geometry_file_format=fmt,
                    mesh_mode=mesh_mode,
                )

                # If save_path or owner_id passed, write into .space VFS
                sm = _get_space_manager()
                if sm and (save_path or owner_id):
                    try:
                        sp_path = save_path or f"/models3d/{res.get('uuid', 'model')}.{fmt}"
                        sp = sm.get_or_create_space(scope, owner_id)
                        glb_b64 = res.get("glb_bytes_b64", "")
                        sp.write_file(sp_path, glb_b64, is_base64=True, mime_type="model/gltf-binary", updated_by=peer_id)
                        res["saved_to_space"] = {"scope": scope, "owner_id": owner_id, "path": sp_path}
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
                res = _check_rodin_status(router, sub_key)
                self._send_json(res, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/3d/download":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                task_uuid = data.get("task_uuid") or data.get("uuid") or ""
                res = _download_rodin_assets(router, task_uuid)
                self._send_json(res, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
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
                out = sm.run_agent(
                    scope=scope,
                    owner_id=owner_id,
                    prompt=prompt,
                    model_alias=model_alias,
                    author=author,
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

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/health", "/call", "/tv", "/os", "/mesh", "/board", "/cyberspace"):
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
            limit = int(query.get("limit", ["50"])[0])
            res = cyberspace_board.list_topics(
                category=category,
                tag=tag,
                mentioned_user=user,
                mentioned_agent=agent,
                sort_by=sort_by,
                verified_only=verified_only,
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
        elif parsed.path in ("/api/models/available", "/api/models/openrouter"):
            models = router.get_available_models() if hasattr(router, "get_available_models") else []
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
        elif parsed.path == "/api/space/ls":
            query = parse_qs(parsed.query)
            scope = query.get("scope", ["user"])[0]
            owner_id = query.get("owner_id", query.get("peer_id", query.get("topic_id", ["default_user"])))[0]
            sm = _get_space_manager()
            sp = sm.get_or_create_space(scope, owner_id)
            self._send_json(sp.get_summary(), 200)
        elif parsed.path == "/api/space/file":
            query = parse_qs(parsed.query)
            scope = query.get("scope", ["user"])[0]
            owner_id = query.get("owner_id", query.get("peer_id", query.get("topic_id", ["default_user"])))[0]
            path = query.get("path", ["/src/main.py"])[0]
            sm = _get_space_manager()
            sp = sm.get_or_create_space(scope, owner_id)
            try:
                rec = sp.read_file(path)
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
        elif parsed.path in ("/install.sh", "/install_peer.sh"):
            install_script_path = os.path.join(os.path.dirname(__file__), "install_peer.sh")
            if os.path.exists(install_script_path):
                with open(install_script_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
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
