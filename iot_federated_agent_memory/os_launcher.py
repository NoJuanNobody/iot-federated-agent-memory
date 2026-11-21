"""TinCan OS Local Node Manager & Multi-Window Launcher (AI-246).

Provides:
- Canonical `WINDOW_CATALOG` mapping every Mesh OS app slug to its stable route,
  window DOM id, title, default dimensions, and slash command.
- `LocalNodeManager`: spawns, checks, and stops a local offline-capable TinCan
  Mesh OS server bound to `127.0.0.1:<free_port>` with its own local data
  directory (`~/.tincan/node_data`) and local Ed25519 identity (passwordless).
- Browser app-window launcher: prefers Chrome / Chromium / Brave / Edge in
  `--app=<url>` chromeless window mode, falling back to the OS default browser.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Canonical Window Catalog (single source of truth for /windows, CLI, Desktop)
# ---------------------------------------------------------------------------

WINDOW_CATALOG: List[Dict[str, Any]] = [
    {
        "slug": "desktop",
        "aliases": ["zen", "os", "all"],
        "route": "/",
        "window_id": None,
        "title": "TinCan Mesh OS",
        "desc": "Full TinCan Mesh OS desktop with Zen shell & Cmd-K launcher",
        "slash": None,
        "width": 1280,
        "height": 820,
        "admin": False,
    },
    {
        "slug": "tv",
        "aliases": ["watch-party", "watchparty", "video"],
        "route": "/tv",
        "window_id": "win-tv",
        "title": "Watch Party",
        "desc": "The collection together, with reactions",
        "slash": "/tv",
        "width": 1120,
        "height": 760,
        "admin": False,
    },
    {
        "slug": "talk",
        "aliases": ["comms", "chat"],
        "route": "/comms",
        "window_id": "chat",
        "title": "Talk & Comms",
        "desc": "Room chat, channels, people & encrypted comms",
        "slash": "/talk",
        "width": 1040,
        "height": 740,
        "admin": False,
    },
    {
        "slug": "call",
        "aliases": ["webrtc", "voice"],
        "route": "/call",
        "window_id": "win-call",
        "title": "Video Call",
        "desc": "Sub-80ms WebRTC video, voice & 60fps desktop screenshare",
        "slash": "/call",
        "width": 1080,
        "height": 720,
        "admin": False,
    },
    {
        "slug": "board",
        "aliases": ["cyberspace", "forum"],
        "route": "/board",
        "window_id": "win-board",
        "title": "Board",
        "desc": "Omni-bar, AI suggestions, curated feed & activity threads",
        "slash": "/board",
        "width": 1180,
        "height": 780,
        "admin": False,
    },
    {
        "slug": "space",
        "aliases": ["workstation", "agentspace", "files", "finder"],
        "route": "/workstation",
        "window_id": "win-agentspace",
        "title": "Workstation",
        "desc": "User, Topic & Sandbox VFS workspace, code runs & Ranger explorer",
        "slash": "/workstation",
        "width": 1280,
        "height": 820,
        "admin": False,
    },
    {
        "slug": "copilot",
        "aliases": ["ai-copilot"],
        "route": "/copilot",
        "window_id": "win-copilot",
        "title": "AI Copilot",
        "desc": "Multi-gateway router, Context Palace & .space diffs",
        "slash": "/copilot",
        "width": 1060,
        "height": 760,
        "admin": False,
    },
    {
        "slug": "ai",
        "aliases": ["home", "ai-hub"],
        "route": "/ai",
        "window_id": "win-ai-home",
        "title": "AI Hub",
        "desc": "Unified tincan ask command bar, ad credits & workflow overview",
        "slash": "/ai",
        "width": 1080,
        "height": 740,
        "admin": False,
    },
    {
        "slug": "3dstudio",
        "aliases": ["rodin", "3d"],
        "route": "/3dstudio",
        "window_id": "win-workstation",
        "title": "3D Studio",
        "desc": "Hyper3D Rodin 3D meshes, TEE audits & Workstation bridge",
        "slash": "/3dstudio",
        "width": 1200,
        "height": 780,
        "admin": False,
    },
    {
        "slug": "node-studio",
        "aliases": ["nodes", "gemini-node-studio"],
        "route": "/nodes",
        "window_id": "win-nodes",
        "title": "Node Studio",
        "desc": "Nano Banana Gemini Node Studio · infinite canvas & Prompt Island",
        "slash": "/nodes",
        "width": 1320,
        "height": 840,
        "admin": False,
    },
    {
        "slug": "terminal",
        "aliases": ["term", "pty", "shell"],
        "route": "/terminal",
        "window_id": "win-terminal",
        "title": "Terminal",
        "desc": "Quickstart and coding agent harnesses (agy, claude, opencode, dsx)",
        "slash": "/terminal",
        "width": 1080,
        "height": 720,
        "admin": False,
    },
    {
        "slug": "arena",
        "aliases": ["duel", "brain-arena"],
        "route": "/arena",
        "window_id": "win-arena",
        "title": "Arena",
        "desc": "Run Arena, vote A/B & Context Palace universal inventory",
        "slash": "/arena",
        "width": 1180,
        "height": 780,
        "admin": False,
    },
    {
        "slug": "network",
        "aliases": ["peers", "mesh"],
        "route": "/network",
        "window_id": "win-network",
        "title": "Network",
        "desc": "Who's here, peers and the leaderboard",
        "slash": "/network",
        "width": 980,
        "height": 700,
        "admin": False,
    },
    {
        "slug": "quests",
        "aliases": ["rewards", "xp"],
        "route": "/quests",
        "window_id": "win-quests",
        "title": "Quests",
        "desc": "Quests, XP and rankings",
        "slash": "/quests",
        "width": 960,
        "height": 700,
        "admin": False,
    },
    {
        "slug": "tokens",
        "aliases": ["billing", "wallet", "ads"],
        "route": "/tokens",
        "window_id": "win-billing",
        "title": "Tokens & Ads",
        "desc": "Token wallet, sponsor ads & AI deliverable credits",
        "slash": "/tokens",
        "width": 1020,
        "height": 740,
        "admin": False,
    },
    {
        "slug": "browser",
        "aliases": ["web"],
        "route": "/browser",
        "window_id": "win-browser",
        "title": "Browser",
        "desc": "Built-in web browser pane",
        "slash": "/browser",
        "width": 1160,
        "height": 780,
        "admin": False,
    },
    {
        "slug": "localhost",
        "aliases": ["preview", "dev"],
        "route": "/localhost",
        "window_id": "win-localhost",
        "title": "Localhost",
        "desc": "Preview local dev servers inside Mesh OS",
        "slash": "/localhost",
        "width": 1120,
        "height": 760,
        "admin": False,
    },
    {
        "slug": "moderator",
        "aliases": ["moderate", "admin", "treasury"],
        "route": "/moderator",
        "window_id": "win-moderator",
        "title": "Moderate & Treasury",
        "desc": "Admin controls & treasury governance",
        "slash": "/moderate",
        "width": 1040,
        "height": 720,
        "admin": True,
    },
]


def resolve_window_entry(app: Optional[str], catalog: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    """Resolve an app name, alias, route, or window_id to a WINDOW_CATALOG entry."""
    entries = catalog if catalog is not None else WINDOW_CATALOG
    if not app or not str(app).strip():
        return entries[0] if entries else None
    needle = str(app).strip().lower().lstrip("/")
    for entry in entries:
        if entry.get("slug", "").lower() == needle:
            return entry
        if entry.get("route", "").lstrip("/").lower() == needle:
            return entry
        if entry.get("window_id") and str(entry["window_id"]).lower() == needle:
            return entry
        aliases = [a.lower() for a in entry.get("aliases", [])]
        if needle in aliases:
            return entry
    return None


def build_windows_payload(
    base_url: str,
    node_mode: str = "local",
    node_id: str = "local-node",
    tc_address: str = "",
) -> Dict[str, Any]:
    """Build the JSON payload served by `GET /windows`."""
    base = base_url.rstrip("/")
    windows = []
    for item in WINDOW_CATALOG:
        route = item["route"]
        windows.append({
            **item,
            "url": f"{base}{route}",
        })
    return {
        "node_mode": node_mode,
        "node_id": node_id,
        "tc_address": tc_address,
        "base_url": base,
        "count": len(windows),
        "windows": windows,
    }


# ---------------------------------------------------------------------------
# Local Identity Helper (passwordless local node identity)
# ---------------------------------------------------------------------------

def ensure_local_identity(config_dir: Optional[str] = None) -> Dict[str, Any]:
    """Ensure a local Ed25519 TinCan identity exists and return public metadata."""
    base_dir = Path(config_dir or os.environ.get("TINCAN_CONFIG_DIR") or (Path.home() / ".tincan"))
    base_dir.mkdir(parents=True, exist_ok=True)

    # Reuse TinCanMCPClient's identity store when PyNaCl is available
    try:
        from .tincan_mcp import TinCanMCPClient

        client = TinCanMCPClient(
            relay_url="http://127.0.0.1:0",
            config_dir=str(base_dir),
        )
        addr = getattr(client.identity, "address", "")
        alias = getattr(client, "alias", "") or os.environ.get("USER") or "local-peer"
        return {
            "tc_address": addr,
            "alias": alias,
            "node_id": f"local-{addr[3:11]}" if addr.startswith("tc:") else f"local-{alias}",
            "config_dir": str(base_dir),
            "ed25519": True,
        }
    except Exception:
        # Fallback if optional deps are missing in a minimal environment
        fallback_path = base_dir / "local_node_id.json"
        if fallback_path.exists():
            try:
                data = json.loads(fallback_path.read_text(encoding="utf-8"))
                if data.get("node_id"):
                    return data
            except Exception:
                pass
        alias = os.environ.get("USER") or "local-peer"
        data = {
            "tc_address": f"tc:local-{socket.gethostname().lower()}",
            "alias": alias,
            "node_id": f"local-{socket.gethostname().lower()}",
            "config_dir": str(base_dir),
            "ed25519": False,
        }
        fallback_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data


# ---------------------------------------------------------------------------
# Free Port & Process Lifecycle Helpers
# ---------------------------------------------------------------------------

def find_free_port(host: str = "127.0.0.1", preferred: int = 0) -> int:
    """Return an available TCP port on `host` (honoring `preferred` if free)."""
    if preferred and preferred > 0:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, preferred))
                return preferred
            except OSError:
                pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return int(s.getsockname()[1])


def is_pid_alive(pid: int) -> bool:
    """Return True if process `pid` currently exists."""
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


def _http_get_json(url: str, timeout: float = 1.5) -> Optional[Dict[str, Any]]:
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    return None


# ---------------------------------------------------------------------------
# Browser App-Window Detection & Launch
# ---------------------------------------------------------------------------

def find_chromium_browser() -> Optional[str]:
    """Return path to Chrome/Chromium/Brave/Edge supporting `--app=<url>`, or None."""
    system = platform.system()
    candidates: List[str] = []
    if system == "Darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Arc.app/Contents/MacOS/Arc",
        ]
    elif system == "Linux":
        for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "brave-browser", "microsoft-edge"):
            found = shutil.which(name)
            if found:
                candidates.append(found)
    elif system == "Windows":
        for env_key in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            base = os.environ.get(env_key)
            if not base:
                continue
            candidates.extend([
                os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"),
                os.path.join(base, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
                os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe"),
            ])

    for path in candidates:
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def launch_browser_window(
    url: str,
    width: int = 1280,
    height: int = 820,
    app_mode: bool = True,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Open `url` in a browser app window (`--app=`) or fall back to default browser."""
    browser_bin = find_chromium_browser() if app_mode else None
    if browser_bin:
        cmd = [
            browser_bin,
            f"--app={url}",
            f"--window-size={width},{height}",
        ]
        if dry_run:
            return {"launched": False, "dry_run": True, "mode": "chromium-app", "cmd": cmd, "url": url}
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return {"launched": True, "mode": "chromium-app", "cmd": cmd, "url": url}

    if dry_run:
        return {"launched": False, "dry_run": True, "mode": "default-browser", "cmd": None, "url": url}

    opened = webbrowser.open(url, new=2)
    return {"launched": bool(opened), "mode": "default-browser", "cmd": None, "url": url}


# ---------------------------------------------------------------------------
# Local Node State & Manager
# ---------------------------------------------------------------------------

@dataclass
class LocalNodeState:
    pid: int
    host: str
    port: int
    url: str
    data_dir: str
    log_path: str
    tc_address: str
    alias: str
    node_id: str
    started_at: float


class LocalNodeManager:
    """Manages the local TinCan Mesh OS server process for `tincan os` & `tincan open`."""

    def __init__(
        self,
        config_dir: Optional[str] = None,
        data_dir: Optional[str] = None,
        repo_root: Optional[str] = None,
    ) -> None:
        self.config_dir = Path(config_dir or os.environ.get("TINCAN_CONFIG_DIR") or (Path.home() / ".tincan"))
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir = Path(data_dir or os.environ.get("TINCAN_DATA_DIR") or (self.config_dir / "node_data"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.config_dir / "os_node.json"
        self.log_file = self.config_dir / "os_node.log"
        self.repo_root = Path(repo_root) if repo_root else Path(__file__).resolve().parent.parent

    def load_state(self) -> Optional[LocalNodeState]:
        if not self.state_file.exists():
            return None
        try:
            raw = json.loads(self.state_file.read_text(encoding="utf-8"))
            return LocalNodeState(**raw)
        except Exception:
            return None

    def save_state(self, state: LocalNodeState) -> None:
        self.state_file.write_text(json.dumps(asdict(state), indent=2), encoding="utf-8")

    def clear_state(self) -> None:
        try:
            self.state_file.unlink(missing_ok=True)
        except Exception:
            pass

    def status(self) -> Dict[str, Any]:
        """Return live status of the local TinCan OS node."""
        state = self.load_state()
        if not state:
            return {"running": False, "state_file": str(self.state_file)}

        alive = is_pid_alive(state.pid)
        windows_info = _http_get_json(f"{state.url}/windows", timeout=1.2) if alive else None
        if not alive or windows_info is None:
            if not alive:
                self.clear_state()
            return {
                "running": False,
                "stale_pid": state.pid,
                "url": state.url,
                "data_dir": state.data_dir,
            }

        return {
            "running": True,
            "pid": state.pid,
            "host": state.host,
            "port": state.port,
            "url": state.url,
            "data_dir": state.data_dir,
            "log_path": state.log_path,
            "tc_address": state.tc_address,
            "alias": state.alias,
            "node_id": state.node_id,
            "started_at": state.started_at,
            "windows_count": windows_info.get("count", len(WINDOW_CATALOG)),
        }

    def start(
        self,
        host: str = "127.0.0.1",
        port: int = 0,
        startup_timeout: float = 20.0,
    ) -> Tuple[LocalNodeState, bool]:
        """Ensure the local node is running. Returns `(state, started_new)`."""
        st = self.status()
        if st.get("running"):
            existing = self.load_state()
            if existing:
                return existing, False

        identity = ensure_local_identity(str(self.config_dir))
        chosen_port = find_free_port(host=host, preferred=port)
        server_py = self.repo_root / "server.py"
        if not server_py.is_file():
            raise FileNotFoundError(f"TinCan server entrypoint not found at {server_py}")

        env = os.environ.copy()
        env["TINCAN_HOST"] = host
        env["PORT"] = str(chosen_port)
        env["TINCAN_DATA_DIR"] = str(self.data_dir)
        env["AGENT_SPACES_DIR"] = str(self.data_dir / "spaces")
        env["TINCAN_CONFIG_DIR"] = str(self.config_dir)
        env["TINCAN_LOCAL_NODE"] = "1"
        env["TINCAN_LOCAL_TC_ADDRESS"] = identity["tc_address"]
        env["TINCAN_LOCAL_ALIAS"] = identity["alias"]
        env["TINCAN_LOCAL_NODE_ID"] = identity["node_id"]
        env["PYTHONUNBUFFERED"] = "1"
        existing_py = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{self.repo_root}{os.pathsep}{existing_py}" if existing_py else str(self.repo_root)

        log_fh = open(self.log_file, "ab")
        try:
            proc = subprocess.Popen(
                [sys.executable, str(server_py)],
                cwd=str(self.repo_root),
                env=env,
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        finally:
            log_fh.close()

        url = f"http://{host}:{chosen_port}"
        deadline = time.time() + startup_timeout
        ready = False
        while time.time() < deadline:
            if proc.poll() is not None:
                break
            info = _http_get_json(f"{url}/windows", timeout=0.8)
            if info is not None:
                ready = True
                break
            time.sleep(0.15)

        if not ready:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                pass
            tail = ""
            try:
                tail = self.log_file.read_text(encoding="utf-8", errors="replace")[-1200:]
            except Exception:
                pass
            raise RuntimeError(f"Local TinCan node failed to start on {url}.\nLog tail:\n{tail}")

        state = LocalNodeState(
            pid=proc.pid,
            host=host,
            port=chosen_port,
            url=url,
            data_dir=str(self.data_dir),
            log_path=str(self.log_file),
            tc_address=identity["tc_address"],
            alias=identity["alias"],
            node_id=identity["node_id"],
            started_at=time.time(),
        )
        self.save_state(state)
        return state, True

    def stop(self, timeout: float = 5.0) -> Dict[str, Any]:
        """Stop the local TinCan OS node if running."""
        state = self.load_state()
        if not state:
            return {"stopped": False, "reason": "not_running"}

        pid = state.pid
        if not is_pid_alive(pid):
            self.clear_state()
            return {"stopped": False, "reason": "stale_pid", "pid": pid}

        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            self.clear_state()
            return {"stopped": False, "reason": "already_exited", "pid": pid}

        deadline = time.time() + timeout
        while time.time() < deadline:
            if not is_pid_alive(pid):
                self.clear_state()
                return {"stopped": True, "pid": pid, "url": state.url}
            time.sleep(0.1)

        # Force kill if graceful shutdown timed out
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
        self.clear_state()
        return {"stopped": True, "forced": True, "pid": pid, "url": state.url}

    def fetch_windows(self, base_url: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query `/windows` from the running local node (falls back to static catalog)."""
        url = base_url
        if not url:
            st = self.status()
            if st.get("running"):
                url = st["url"]
        if url:
            data = _http_get_json(f"{url.rstrip('/')}/windows", timeout=1.5)
            if data and isinstance(data.get("windows"), list):
                return data["windows"]
        return WINDOW_CATALOG
