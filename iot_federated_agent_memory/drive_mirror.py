"""Read-only, login-time mirror of the user's real hard drive for the Ranger VFS.

Nothing in this module writes, moves or deletes anything on disk, and nothing
it gathers is persisted: every call to :func:`gather_mirror` walks the disk
fresh, so the Finder's "spaces" always reflect what is on the drive right now
instead of a saved folder list.

The mirror only makes sense when the TinCan server runs on the user's own
machine (``python server.py`` / tincan_cli on the Mac).  On Railway or any
other remote host the server cannot see the user's disk, so the mirror is
switched off there and the browser falls back to the File System Access API
(a folder the user picks, held in memory for the session only).
"""

from __future__ import annotations

import ipaddress
import mimetypes
import os
import stat
import time
from typing import Any, Dict, Iterable, List, Optional

# Directory names never descended into (noise, huge, or private app data).
SKIP_DIR_NAMES = frozenset({
    "node_modules", ".git", ".hg", ".svn", "__pycache__", ".venv", "venv", "env",
    ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".next", ".nuxt",
    "dist", "build", "target", ".gradle", ".idea", ".cache", "Pods", "DerivedData",
    "Library", "Applications", "Pictures Library", ".Trash", "System", "Volumes",
    "site-packages", ".terraform", "coverage",
})

# Candidate names for the user's dev folder, in priority order.
DEV_DIR_CANDIDATES = (
    "dev", "Dev", "Developer", "developer", "code", "Code", "src",
    "projects", "Projects", "workspace", "Workspace", "repos", "git", "GitHub",
)

DEFAULT_MAX_DEPTH = 3
DEFAULT_MAX_ENTRIES = 4000
DEFAULT_MAX_CHILDREN = 300
DEFAULT_MAX_TEXT_BYTES = 512 * 1024
DEFAULT_MAX_RAW_BYTES = 64 * 1024 * 1024

_RAILWAY_ENV_KEYS = ("RAILWAY_ENVIRONMENT", "RAILWAY_ENVIRONMENT_NAME", "RAILWAY_PROJECT_ID", "RAILWAY_SERVICE_ID")
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "[::1]"}


class MirrorAccessError(PermissionError):
    """Requested path is outside the mirrored root (or otherwise not allowed)."""


def _env_flag(name: str) -> Optional[bool]:
    raw = (os.environ.get(name) or "").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    return None


def running_on_railway() -> bool:
    return any(os.environ.get(k) for k in _RAILWAY_ENV_KEYS)


def mirror_root() -> str:
    """Root that the mirror is allowed to show: TINCAN_DRIVE_ROOT or the home dir."""
    root = os.environ.get("TINCAN_DRIVE_ROOT") or os.path.expanduser("~")
    return os.path.realpath(root)


def mirror_enabled() -> bool:
    """Server-side mirror is on for local runs, off on Railway unless forced."""
    flag = _env_flag("TINCAN_DRIVE_MIRROR")
    if flag is not None:
        return flag
    return not running_on_railway()


def request_allowed(client_ip: str, host_header: str = "", forwarded_for: str = "") -> bool:
    """Only serve the disk to the machine it lives on.

    Requires a loopback client, a localhost Host header (blocks DNS rebinding)
    and no proxy hop, unless TINCAN_DRIVE_MIRROR=1 explicitly opts in to remote
    access (e.g. a trusted LAN/Tailscale setup).
    """
    if not mirror_enabled():
        return False
    if _env_flag("TINCAN_DRIVE_MIRROR") is True:
        return True
    if forwarded_for:
        return False
    try:
        if not ipaddress.ip_address((client_ip or "").split("%")[0]).is_loopback:
            return False
    except ValueError:
        return False
    host = (host_header or "").strip().lower()
    if host.startswith("["):
        host = host.split("]")[0] + "]"
    else:
        host = host.rsplit(":", 1)[0] if host.count(":") == 1 else host
    return host in _LOCAL_HOSTS


def find_dev_folder(root: Optional[str] = None) -> Optional[str]:
    """TINCAN_DEV_DIR wins; otherwise the first existing ~/dev-style folder."""
    root = root or mirror_root()
    override = os.environ.get("TINCAN_DEV_DIR")
    if override:
        p = os.path.realpath(os.path.expanduser(override))
        if os.path.isdir(p):
            return p
    try:
        present = set(os.listdir(root))
    except OSError:
        return None
    for name in DEV_DIR_CANDIDATES:
        if name in present:
            p = os.path.join(root, name)
            if os.path.isdir(p) and not os.path.islink(p):
                return os.path.realpath(p)
    return None


def _skip(name: str, show_hidden: bool) -> bool:
    if name in SKIP_DIR_NAMES:
        return True
    return name.startswith(".") and not show_hidden


def resolve_inside(root: str, rel_path: str) -> str:
    """Resolve ``rel_path`` under ``root`` and refuse anything that escapes it."""
    root = os.path.realpath(root)
    rel = (rel_path or "").replace("\\", "/").lstrip("/")
    target = os.path.realpath(os.path.join(root, rel))
    if target != root and not target.startswith(root + os.sep):
        raise MirrorAccessError("Path is outside the mirrored drive")
    return target


def _rel(root: str, abs_path: str) -> str:
    rel = os.path.relpath(abs_path, root)
    return "/" if rel == "." else "/" + rel.replace(os.sep, "/")


def list_dir(root: str, rel_path: str = "/", *, show_hidden: bool = False,
             max_children: int = DEFAULT_MAX_CHILDREN) -> Dict[str, Any]:
    """One directory level (folders first, then files), read-only, capped."""
    abs_dir = resolve_inside(root, rel_path)
    if not os.path.isdir(abs_dir):
        raise NotADirectoryError(rel_path)
    dirs: List[Dict[str, Any]] = []
    files: List[Dict[str, Any]] = []
    total = 0
    try:
        with os.scandir(abs_dir) as it:
            entries = sorted(it, key=lambda e: e.name.lower())
    except OSError as exc:
        return {"path": _rel(root, abs_dir), "dirs": [], "files": [], "error": str(exc), "truncated": False}
    for e in entries:
        if _skip(e.name, show_hidden):
            continue
        total += 1
        if len(dirs) + len(files) >= max_children:
            continue
        try:
            is_dir = e.is_dir(follow_symlinks=False)
            st = e.stat(follow_symlinks=False)
        except OSError:
            continue
        if is_dir:
            dirs.append({"name": e.name, "path": _rel(root, e.path), "type": "dir"})
        elif stat.S_ISREG(st.st_mode):
            files.append({
                "name": e.name, "path": _rel(root, e.path), "type": "file",
                "size_bytes": st.st_size, "mtime": int(st.st_mtime),
                "mime_type": mimetypes.guess_type(e.name)[0] or "application/octet-stream",
            })
    return {
        "path": _rel(root, abs_dir),
        "dirs": dirs,
        "files": files,
        "truncated": total > len(dirs) + len(files),
    }


def _walk_tree(root: str, abs_dir: str, depth: int, max_depth: int, budget: List[int],
               show_hidden: bool, max_children: int) -> Dict[str, Any]:
    node: Dict[str, Any] = {"name": os.path.basename(abs_dir) or abs_dir, "path": _rel(root, abs_dir), "children": []}
    if depth >= max_depth or budget[0] <= 0:
        node["more"] = True
        return node
    try:
        with os.scandir(abs_dir) as it:
            subdirs = sorted(
                (e for e in it if not _skip(e.name, show_hidden) and e.is_dir(follow_symlinks=False)),
                key=lambda e: e.name.lower(),
            )
    except OSError:
        node["error"] = "unreadable"
        return node
    if len(subdirs) > max_children:
        node["truncated"] = True
        subdirs = subdirs[:max_children]
    for e in subdirs:
        if budget[0] <= 0:
            node["truncated"] = True
            break
        budget[0] -= 1
        node["children"].append(_walk_tree(root, e.path, depth + 1, max_depth, budget, show_hidden, max_children))
    return node


def gather_mirror(root: Optional[str] = None, *, max_depth: int = DEFAULT_MAX_DEPTH,
                  max_entries: int = DEFAULT_MAX_ENTRIES, max_children: int = DEFAULT_MAX_CHILDREN,
                  show_hidden: bool = False) -> Dict[str, Any]:
    """Fresh, in-memory folder tree of the drive. Never cached or persisted.

    Folders only (files are listed lazily per directory with :func:`list_dir`),
    hidden/vendor folders skipped, symlinks not followed, depth and total
    folder count capped so a huge home directory stays fast.
    """
    started = time.time()
    root = os.path.realpath(root or mirror_root())
    dev_abs = find_dev_folder(root)
    budget = [max(1, int(max_entries))]
    places: List[Dict[str, Any]] = []

    if dev_abs and (dev_abs == root or dev_abs.startswith(root + os.sep)):
        dev_tree = _walk_tree(root, dev_abs, 0, max_depth, budget, show_hidden, max_children)
        dev_tree.update({"pinned": True, "kind": "dev"})
        places.append(dev_tree)

    try:
        with os.scandir(root) as it:
            top = sorted(
                (e for e in it if not _skip(e.name, show_hidden) and e.is_dir(follow_symlinks=False)),
                key=lambda e: e.name.lower(),
            )
    except OSError:
        top = []
    for e in top[:max_children]:
        if dev_abs and os.path.realpath(e.path) == dev_abs:
            continue
        if budget[0] <= 0:
            break
        budget[0] -= 1
        # Top-level home folders get a shallower walk than the pinned dev folder.
        places.append(_walk_tree(root, e.path, 0, max(1, max_depth - 1), budget, show_hidden, max_children))

    return {
        "source": "server",
        "root": root,
        "root_label": os.path.basename(root) or root,
        "dev_folder": _rel(root, dev_abs) if dev_abs else None,
        "dev_folder_abs": dev_abs,
        "places": places,
        "limits": {"max_depth": max_depth, "max_entries": max_entries, "max_children": max_children},
        "truncated": budget[0] <= 0,
        "gathered_at": int(started),
        "elapsed_ms": int((time.time() - started) * 1000),
        "persisted": False,
    }


def _looks_binary(sample: bytes) -> bool:
    if b"\x00" in sample:
        return True
    try:
        sample.decode("utf-8")
        return False
    except UnicodeDecodeError as exc:
        # A multi-byte char cut at the sample boundary is still text.
        return exc.start < len(sample) - 4


def read_text_preview(root: str, rel_path: str, *, max_bytes: int = DEFAULT_MAX_TEXT_BYTES) -> Dict[str, Any]:
    """Read-only preview: text up to ``max_bytes``; binaries return metadata only."""
    abs_path = resolve_inside(root, rel_path)
    if not os.path.isfile(abs_path):
        raise FileNotFoundError(rel_path)
    st = os.stat(abs_path)
    mime = mimetypes.guess_type(abs_path)[0] or "application/octet-stream"
    with open(abs_path, "rb") as fh:
        head = fh.read(max_bytes + 1)
    truncated = len(head) > max_bytes
    head = head[:max_bytes]
    binary = _looks_binary(head[:8192])
    out: Dict[str, Any] = {
        "path": _rel(root, abs_path),
        "abs_path": abs_path,
        "name": os.path.basename(abs_path),
        "size_bytes": st.st_size,
        "mtime": int(st.st_mtime),
        "mime_type": mime,
        "is_binary": binary,
        "truncated": truncated and not binary,
        "content": None,
        "source": "drive",
        "read_only": True,
    }
    if not binary:
        out["content"] = head.decode("utf-8", errors="replace")
    return out


def open_raw(root: str, rel_path: str, *, max_bytes: int = DEFAULT_MAX_RAW_BYTES):
    """Return (abs_path, size, mime) for streaming a file read-only."""
    abs_path = resolve_inside(root, rel_path)
    if not os.path.isfile(abs_path):
        raise FileNotFoundError(rel_path)
    size = os.path.getsize(abs_path)
    if size > max_bytes:
        raise MirrorAccessError(f"File is larger than the {max_bytes // (1024 * 1024)} MB preview limit")
    mime = mimetypes.guess_type(abs_path)[0] or "application/octet-stream"
    return abs_path, size, mime


def iter_file_chunks(abs_path: str, chunk: int = 256 * 1024) -> Iterable[bytes]:
    with open(abs_path, "rb") as fh:
        while True:
            buf = fh.read(chunk)
            if not buf:
                return
            yield buf
