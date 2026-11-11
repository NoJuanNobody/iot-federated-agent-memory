"""Per-thread filesystem for TinCan Mesh OS.

Each chat thread gets a directory (like a ChatGPT Space) where an agent can
read and write persistent files. On Railway the files live on the attached
storage volume (see ``resolve_threads_root``). Locally they fall back to
``~/.tin-can/threads`` when no data-dir or volume env is set.

Layout::

    <root>/<peer_id>/<thread_id>/
        thread.json
        files/          # agent-visible workspace (sandboxed)

Conversation IDs are minted server-side (UUID-4 hex). A client-supplied
``thread_id`` is reused only when that thread already exists for the same
peer; otherwise a new id is minted.

Paths passed to read/write/list/delete are relative to ``files/``. Absolute
paths, ``..`` traversal, and symlink escapes outside the thread directory
(and the threads root) are rejected. Peer ids and thread ids are sanitized
to the same conservative character set.
"""

from __future__ import annotations

import json
import math
import os
import shutil
import re
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
THREAD_ID_RE = ID_RE  # backwards-compatible alias
FILES_DIRNAME = "files"
META_FILENAME = "thread.json"
ANONYMOUS_PEER_ID = "anonymous"
_MAX_REL_DEPTH = 32


class ThreadFsError(ValueError):
    """Invalid peer/thread id or unsandboxed path."""


class ThreadQuotaError(ThreadFsError):
    """Write exceeds the free per-thread tier or a hard size cap.

    ``code`` is one of ``tokens_required``, ``hard_limit``, or
    ``insufficient_tokens``.
    """

    def __init__(
        self,
        message: str,
        *,
        code: str = "tokens_required",
        overage_bytes: int = 0,
        tokens_required: int = 0,
        plan: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.overage_bytes = overage_bytes
        self.tokens_required = tokens_required
        self.plan = plan or {}


def _env_dir(name: str) -> Optional[str]:
    """Return a non-empty environment value, or None if unset/blank."""
    value = os.environ.get(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def resolve_threads_root(root: Optional[Union[str, Path]] = None) -> Path:
    """Return the threads root directory.

    Precedence (first match wins; blank env values are ignored):

    1. Explicit ``root`` argument
    2. ``TINCAN_THREADS_DIR`` — direct override of the threads folder
    3. ``$TINCAN_DATA_DIR/threads`` — same data dir as ``PeerAccountRegistry``
       and the cyberspace board (typically pointed at the Railway volume)
    4. ``$RAILWAY_VOLUME_MOUNT_PATH/threads`` — set automatically by Railway
       when a volume is attached to the service
    5. ``$TINCAN_DIR/threads`` — local CLI identity directory
    6. ``~/.tin-can/threads`` — local default when nothing else is set
    """
    if root is not None:
        return Path(root).expanduser().resolve()
    explicit = _env_dir("TINCAN_THREADS_DIR")
    if explicit:
        return Path(explicit).expanduser().resolve()
    data_dir = _env_dir("TINCAN_DATA_DIR")
    if data_dir:
        return (Path(data_dir).expanduser() / "threads").resolve()
    volume = _env_dir("RAILWAY_VOLUME_MOUNT_PATH")
    if volume:
        return (Path(volume).expanduser() / "threads").resolve()
    base = _env_dir("TINCAN_DIR") or os.path.expanduser("~/.tin-can")
    return (Path(base).expanduser() / "threads").resolve()


def _sanitize_id(value: str, *, label: str) -> str:
    if not isinstance(value, str):
        raise ThreadFsError(f"{label} must be a string")
    tid = value.strip()
    if tid in {".", ".."} or not ID_RE.fullmatch(tid):
        raise ThreadFsError(f"invalid {label}: {value!r}")
    return tid


def sanitize_thread_id(thread_id: str) -> str:
    return _sanitize_id(thread_id, label="thread_id")


def sanitize_peer_id(peer_id: str) -> str:
    return _sanitize_id(peer_id, label="peer_id")


def mint_thread_id() -> str:
    """Return a fresh server-minted thread id (UUID-4 hex, 32 chars)."""
    return uuid.uuid4().hex


def _under_root(path: Path, root: Path) -> Path:
    """Resolve ``path`` and reject symlink/lexical escapes outside ``root``."""
    resolved_root = root.resolve()
    try:
        resolved = path.resolve()
        resolved.relative_to(resolved_root)
    except (ValueError, OSError) as exc:
        raise ThreadFsError("path escapes the threads root") from exc
    # Reject a symlink in the existing ancestor chain that points outside.
    cursor = path
    chain: List[Path] = []
    while True:
        chain.append(cursor)
        if cursor == root or cursor.parent == cursor:
            break
        cursor = cursor.parent
    for item in chain:
        if item.exists() and item.is_symlink():
            try:
                item.resolve(strict=True).relative_to(resolved_root)
            except (ValueError, OSError) as exc:
                raise ThreadFsError("path escapes the threads root") from exc
    return resolved


def peer_dir(peer_id: str, *, root: Optional[Union[str, Path]] = None) -> Path:
    base = resolve_threads_root(root)
    return _under_root(base / sanitize_peer_id(peer_id), base)


def thread_dir(peer_id: str, thread_id: str, *, root: Optional[Union[str, Path]] = None) -> Path:
    base = resolve_threads_root(root)
    return _under_root(
        base / sanitize_peer_id(peer_id) / sanitize_thread_id(thread_id),
        base,
    )


def thread_exists(peer_id: str, thread_id: str, *, root: Optional[Union[str, Path]] = None) -> bool:
    """True when ``thread.json`` already exists for this peer+thread pair."""
    try:
        meta = thread_dir(peer_id, thread_id, root=root) / META_FILENAME
    except ThreadFsError:
        return False
    return meta.is_file()


def _utc_now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def ensure_thread_dir(
    peer_id: str,
    thread_id: str,
    *,
    root: Optional[Union[str, Path]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Path:
    """Create ``<root>/<peer_id>/<thread_id>/{thread.json,files/}`` if missing.

    Idempotent. Existing ``thread.json`` keys are preserved. ``updated_at`` is
    refreshed; ``peer_id`` and any ``metadata`` keys are filled in only when
    absent. This is a primitive that creates a *given* id; conversation start
    should go through ``start_or_continue_thread`` so ids stay server-minted.
    """
    pid = sanitize_peer_id(peer_id)
    tid = sanitize_thread_id(thread_id)
    tdir = thread_dir(pid, tid, root=root)
    files = tdir / FILES_DIRNAME
    files.mkdir(parents=True, exist_ok=True)
    # Re-check after mkdir in case a parent was a symlink.
    tdir = thread_dir(pid, tid, root=root)
    meta_path = tdir / META_FILENAME
    now = _utc_now_iso()
    meta: Dict[str, Any] = {}
    if meta_path.is_file():
        try:
            loaded = json.loads(meta_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                meta = loaded
        except (OSError, json.JSONDecodeError):
            meta = {}
    if "thread_id" not in meta:
        meta["thread_id"] = tid
    if "created_at" not in meta:
        meta["created_at"] = now
    if "peer_id" not in meta:
        meta["peer_id"] = pid
    if metadata:
        for key, value in metadata.items():
            if key not in meta:
                meta[key] = value
    meta["updated_at"] = now
    _atomic_write_bytes(meta_path, (json.dumps(meta, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    return tdir


def start_or_continue_thread(
    peer_id: str,
    thread_id: Optional[str] = None,
    *,
    root: Optional[Union[str, Path]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    template: Optional[str] = None,
    kind: Optional[str] = None,
) -> Path:
    """Open an existing thread for this peer, or mint a new id and create it.

    A client-supplied ``thread_id`` is accepted only when ``thread.json``
    already exists under that peer. Unknown, invalid, or cross-peer ids are
    ignored and a fresh UUID-4 hex id is minted instead.

    When a new thread is minted, ``template`` or ``kind`` (e.g. ``scam-case``)
    seeds ``files/`` from ``templates/threads/<name>/``. Existing threads are
    not re-seeded.
    """
    created = not (thread_id and thread_exists(peer_id, thread_id, root=root))
    if not created:
        tid = sanitize_thread_id(thread_id)  # type: ignore[arg-type]
    else:
        tid = mint_thread_id()
    template_name = normalize_template_name(template or kind)
    meta = dict(metadata or {})
    if created and template_name:
        meta.setdefault("template", template_name)
        meta.setdefault("kind", template_name)
    tdir = ensure_thread_dir(peer_id, tid, root=root, metadata=meta)
    if created and template_name:
        seed_thread_from_template(peer_id, tid, template_name, root=root)
    return tdir


def _safe_relpath(relpath: str) -> Path:
    if not isinstance(relpath, str) or not relpath.strip():
        raise ThreadFsError("path must be a non-empty relative path")
    raw = relpath.strip().replace("\\", "/")
    if raw.startswith("/") or raw.startswith("~"):
        raise ThreadFsError("absolute paths are not allowed")
    if len(raw) >= 2 and raw[1] == ":" and raw[0].isalpha():
        raise ThreadFsError("absolute paths are not allowed")
    candidate = Path(raw)
    if candidate.is_absolute():
        raise ThreadFsError("absolute paths are not allowed")
    parts = candidate.parts
    if not parts or len(parts) > _MAX_REL_DEPTH:
        raise ThreadFsError("path must be a non-empty relative path")
    for part in parts:
        if part in (".", "..") or not part or part.startswith("/"):
            raise ThreadFsError("path traversal is not allowed")
    return Path(*parts)


def _files_root(tdir: Path) -> Path:
    return (tdir / FILES_DIRNAME).resolve()


def resolve_in_thread(
    peer_id: str,
    thread_id: str,
    relpath: str,
    *,
    root: Optional[Union[str, Path]] = None,
    must_exist: bool = False,
) -> Path:
    """Resolve ``relpath`` inside the thread's ``files/`` directory, or raise."""
    tdir = thread_dir(peer_id, thread_id, root=root)
    files_root = _files_root(tdir)
    rel = _safe_relpath(relpath)
    candidate = files_root / rel
    try:
        resolved = candidate.resolve(strict=must_exist)
    except FileNotFoundError as exc:
        raise ThreadFsError(f"file not found: {relpath}") from exc
    except OSError as exc:
        raise ThreadFsError(f"invalid path: {exc}") from exc
    try:
        resolved.relative_to(files_root)
    except ValueError as exc:
        raise ThreadFsError("path escapes the thread files directory") from exc
    cursor = candidate
    chain: List[Path] = []
    while True:
        chain.append(cursor)
        if cursor == files_root or cursor.parent == cursor:
            break
        cursor = cursor.parent
    for item in chain:
        if item.exists() and item.is_symlink():
            try:
                item.resolve(strict=True).relative_to(files_root)
            except (ValueError, OSError) as exc:
                raise ThreadFsError("path escapes the thread files directory") from exc
    return resolved


def list_files(
    peer_id: str,
    thread_id: str,
    *,
    subpath: str = "",
    root: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
    """List files under ``files/`` (or a subdirectory). Does not follow symlinks."""
    tdir = ensure_thread_dir(peer_id, thread_id, root=root)
    files_root = _files_root(tdir)
    if subpath:
        start = resolve_in_thread(peer_id, thread_id, subpath, root=root, must_exist=True)
        if not start.is_dir():
            raise ThreadFsError(f"not a directory: {subpath}")
    else:
        start = files_root
        start.mkdir(parents=True, exist_ok=True)

    entries: List[Dict[str, Any]] = []
    for dirpath, dirnames, filenames in os.walk(start, followlinks=False):
        dirnames[:] = [d for d in dirnames if not Path(dirpath, d).is_symlink()]
        rel_dir = Path(dirpath).resolve()
        try:
            rel_dir.relative_to(files_root)
        except ValueError:
            continue
        names: Iterable[str] = list(dirnames) + list(filenames)
        for name in names:
            full = Path(dirpath) / name
            if full.is_symlink():
                continue
            try:
                resolved = full.resolve(strict=True)
                rel = resolved.relative_to(files_root).as_posix()
            except (ValueError, OSError):
                continue
            stat = full.stat()
            entries.append(
                {
                    "path": rel,
                    "is_dir": full.is_dir(),
                    "size": 0 if full.is_dir() else stat.st_size,
                }
            )
    entries.sort(key=lambda e: e["path"])
    return entries


def read_file(
    peer_id: str,
    thread_id: str,
    relpath: str,
    *,
    root: Optional[Union[str, Path]] = None,
    binary: bool = False,
) -> Union[str, bytes]:
    path = resolve_in_thread(peer_id, thread_id, relpath, root=root, must_exist=True)
    if not path.is_file() or path.is_symlink():
        raise ThreadFsError(f"not a regular file: {relpath}")
    data = path.read_bytes()
    if binary:
        return data
    return data.decode("utf-8")


def write_file(
    peer_id: str,
    thread_id: str,
    relpath: str,
    data: Union[str, bytes],
    *,
    root: Optional[Union[str, Path]] = None,
    billing: Optional[Any] = None,
) -> Path:
    """Atomically write ``data`` under the thread's ``files/`` directory.

    Writes within the free per-thread tier are unpaid. Larger writes require
    a ``billing`` callable ``billing(plan) -> receipt`` (typically
    ``charge_thread_quota`` against ``PeerAccountRegistry``). Without a
    billing hook, a ``ThreadQuotaError`` (code ``tokens_required``) is raised.
    Writes past the hard cap always raise ``ThreadQuotaError`` (code
    ``hard_limit``), even if tokens are available.
    """
    ensure_thread_dir(peer_id, thread_id, root=root)
    payload = data if isinstance(data, bytes) else data.encode("utf-8")
    plan = plan_write(peer_id, thread_id, relpath, len(payload), root=root)
    if plan["exceeds_hard_limit"]:
        raise ThreadQuotaError(
            f"write exceeds hard size limit ({plan['reason']})",
            code="hard_limit",
            overage_bytes=plan["overage_bytes"],
            tokens_required=0,
            plan=plan,
        )
    if not plan["within_free_tier"]:
        if billing is None:
            raise ThreadQuotaError(
                "write exceeds the free per-thread file tier; tokens are required",
                code="tokens_required",
                overage_bytes=plan["overage_bytes"],
                tokens_required=plan["tokens_required"],
                plan=plan,
            )
        try:
            plan["billing"] = billing(plan)
        except ThreadQuotaError:
            raise
        except Exception as exc:
            raise ThreadQuotaError(
                str(exc) or "insufficient tokens for over-tier write",
                code="insufficient_tokens",
                overage_bytes=plan["overage_bytes"],
                tokens_required=plan["tokens_required"],
                plan=plan,
            ) from exc
    path = resolve_in_thread(peer_id, thread_id, relpath, root=root, must_exist=False)
    _atomic_write_bytes(path, payload)
    return path


def delete_file(
    peer_id: str,
    thread_id: str,
    relpath: str,
    *,
    root: Optional[Union[str, Path]] = None,
) -> bool:
    """Delete a regular file under ``files/``. Returns False if it did not exist."""
    try:
        path = resolve_in_thread(peer_id, thread_id, relpath, root=root, must_exist=True)
    except ThreadFsError as exc:
        if "file not found" in str(exc):
            return False
        raise
    if path.is_dir():
        raise ThreadFsError(f"refusing to delete directory: {relpath}")
    if not path.is_file():
        raise ThreadFsError(f"not a regular file: {relpath}")
    path.unlink()
    return True

# ---------------------------------------------------------------------------
# Quotas (free per-thread tier; overage billed in tokens)
# ---------------------------------------------------------------------------

DEFAULT_MAX_FILE_BYTES = 256 * 1024  # 256 KiB
DEFAULT_MAX_TOTAL_BYTES = 1 * 1024 * 1024  # 1 MiB
DEFAULT_HARD_MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MiB
DEFAULT_HARD_MAX_TOTAL_BYTES = 32 * 1024 * 1024  # 32 MiB
DEFAULT_OVERAGE_TOKENS_PER_KIB = 1
QUOTA_LEDGER_MODEL = "thread-fs-quota"


def _env_int(name: str, default: int) -> int:
    raw = _env_dir(name)
    if raw is None:
        return default
    try:
        value = int(raw, 10)
    except ValueError:
        return default
    return value if value > 0 else default


def thread_quota_settings() -> Dict[str, int]:
    """Return the current free-tier and hard caps (env-configurable)."""
    return {
        "max_file_bytes": _env_int("TINCAN_THREAD_MAX_FILE_BYTES", DEFAULT_MAX_FILE_BYTES),
        "max_total_bytes": _env_int("TINCAN_THREAD_MAX_TOTAL_BYTES", DEFAULT_MAX_TOTAL_BYTES),
        "hard_max_file_bytes": _env_int(
            "TINCAN_THREAD_HARD_MAX_FILE_BYTES", DEFAULT_HARD_MAX_FILE_BYTES
        ),
        "hard_max_total_bytes": _env_int(
            "TINCAN_THREAD_HARD_MAX_TOTAL_BYTES", DEFAULT_HARD_MAX_TOTAL_BYTES
        ),
        "overage_tokens_per_kib": _env_int(
            "TINCAN_THREAD_OVERAGE_TOKENS_PER_KIB", DEFAULT_OVERAGE_TOKENS_PER_KIB
        ),
    }


def thread_usage_bytes(peer_id: str, thread_id: str, *, root: Optional[Union[str, Path]] = None) -> int:
    """Sum of regular file sizes under the thread's ``files/`` directory."""
    try:
        tdir = thread_dir(peer_id, thread_id, root=root)
    except ThreadFsError:
        return 0
    files_root = tdir / FILES_DIRNAME
    if not files_root.is_dir():
        return 0
    total = 0
    for dirpath, dirnames, filenames in os.walk(files_root, followlinks=False):
        dirnames[:] = [d for d in dirnames if not Path(dirpath, d).is_symlink()]
        for name in filenames:
            full = Path(dirpath) / name
            if full.is_symlink() or not full.is_file():
                continue
            try:
                total += full.stat().st_size
            except OSError:
                continue
    return total


def plan_write(
    peer_id: str,
    thread_id: str,
    relpath: str,
    new_size: int,
    *,
    root: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Describe whether ``new_size`` bytes at ``relpath`` fit the free or hard caps."""
    settings = thread_quota_settings()
    if new_size < 0:
        raise ThreadFsError("new_size must be non-negative")
    old_size = 0
    try:
        existing = resolve_in_thread(peer_id, thread_id, relpath, root=root, must_exist=True)
        if existing.is_file() and not existing.is_symlink():
            old_size = existing.stat().st_size
    except ThreadFsError:
        old_size = 0
    current_total = thread_usage_bytes(peer_id, thread_id, root=root)
    new_total = current_total - old_size + new_size
    file_over = max(0, new_size - settings["max_file_bytes"])
    total_over = max(0, new_total - settings["max_total_bytes"])
    overage_bytes = max(file_over, total_over)
    tokens_required = 0
    if overage_bytes > 0:
        tokens_required = max(
            1,
            int(math.ceil(overage_bytes / 1024.0) * settings["overage_tokens_per_kib"]),
        )
    exceeds_hard = (
        new_size > settings["hard_max_file_bytes"]
        or new_total > settings["hard_max_total_bytes"]
    )
    reason = "ok"
    if new_size > settings["hard_max_file_bytes"]:
        reason = "hard_max_file_bytes"
    elif new_total > settings["hard_max_total_bytes"]:
        reason = "hard_max_total_bytes"
    elif file_over and total_over:
        reason = "max_file_and_total_bytes"
    elif file_over:
        reason = "max_file_bytes"
    elif total_over:
        reason = "max_total_bytes"
    return {
        "new_size": new_size,
        "old_size": old_size,
        "current_total": current_total,
        "new_total": new_total,
        "overage_bytes": overage_bytes,
        "tokens_required": tokens_required,
        "within_free_tier": overage_bytes == 0,
        "exceeds_hard_limit": exceeds_hard,
        "reason": reason,
        "settings": settings,
    }


def charge_thread_quota(registry: Any, peer_id: str, plan: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Debit ``PeerAccountRegistry`` for an over-tier write.

    Uses the existing ``bill_tokens`` ledger (model name ``thread-fs-quota``)
    with ``allow_overage=False``. No-ops when the write is within the free
    tier. Raises ``ThreadQuotaError`` if the peer cannot cover the charge.
    """
    if plan.get("within_free_tier") or plan.get("tokens_required", 0) <= 0:
        return None
    if registry is None:
        raise ThreadQuotaError(
            "write exceeds the free per-thread file tier; tokens are required",
            code="tokens_required",
            overage_bytes=int(plan.get("overage_bytes") or 0),
            tokens_required=int(plan.get("tokens_required") or 0),
            plan=plan,
        )
    tokens = int(plan["tokens_required"])
    try:
        receipt = registry.bill_tokens(
            peer_id=peer_id,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=tokens,
            cost_usd=0.0,
            model=QUOTA_LEDGER_MODEL,
            allow_overage=False,
        )
    except Exception as exc:
        raise ThreadQuotaError(
            str(exc) or "insufficient tokens for over-tier write",
            code="insufficient_tokens",
            overage_bytes=int(plan.get("overage_bytes") or 0),
            tokens_required=tokens,
            plan=plan,
        ) from exc
    return receipt


# ---------------------------------------------------------------------------
# Templates / scam-case seed files
# ---------------------------------------------------------------------------

def default_templates_root() -> Path:
    """Directory containing per-kind thread templates (``<name>/...``)."""
    env = _env_dir("TINCAN_THREAD_TEMPLATES_DIR")
    if env:
        return Path(env).expanduser().resolve()
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / "templates" / "threads",
        here / "templates" / "threads",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
    return candidates[0].resolve()


def normalize_template_name(name: Optional[str]) -> Optional[str]:
    if not name or not str(name).strip():
        return None
    cleaned = str(name).strip().lower().replace("_", "-").replace(" ", "-")
    # allow a single path segment only
    return sanitize_thread_id(cleaned)


def list_templates(*, templates_root: Optional[Union[str, Path]] = None) -> List[str]:
    base = Path(templates_root) if templates_root else default_templates_root()
    if not base.is_dir():
        return []
    return sorted(p.name for p in base.iterdir() if p.is_dir() and not p.name.startswith("."))


def seed_thread_from_template(
    peer_id: str,
    thread_id: str,
    template: str,
    *,
    root: Optional[Union[str, Path]] = None,
    templates_root: Optional[Union[str, Path]] = None,
) -> List[str]:
    """Copy template files into ``files/``. Existing dest paths are left alone.

    Seed writes stay within the free tier (no billing hook). Returns the
    relative paths that were newly written.
    """
    name = normalize_template_name(template)
    if not name:
        raise ThreadFsError("template name is required")
    base = Path(templates_root) if templates_root else default_templates_root()
    src = (base / name).resolve()
    try:
        src.relative_to(base.resolve())
    except ValueError as exc:
        raise ThreadFsError("template path escapes the templates root") from exc
    if not src.is_dir():
        raise ThreadFsError(f"unknown thread template: {name}")
    written: List[str] = []
    for dirpath, dirnames, filenames in os.walk(src, followlinks=False):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and not Path(dirpath, d).is_symlink()]
        for filename in filenames:
            if filename.startswith("."):
                continue
            full = Path(dirpath) / filename
            if full.is_symlink() or not full.is_file():
                continue
            rel = full.resolve().relative_to(src).as_posix()
            try:
                resolve_in_thread(peer_id, thread_id, rel, root=root, must_exist=True)
                continue  # already present
            except ThreadFsError:
                pass
            data = full.read_bytes()
            write_file(peer_id, thread_id, rel, data, root=root)
            written.append(rel)
    return written
