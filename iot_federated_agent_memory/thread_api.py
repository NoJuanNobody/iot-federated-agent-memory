"""HTTP and MCP helpers for per-thread file list/read/write.

Access is scoped by ``peer_id`` + ``thread_id`` and uses the same token
gate as ``POST /api/chat``: a registered peer with a zero token balance
is rejected (HTTP 402). Missing/blank peer ids use the ``anonymous``
filesystem bucket; unsanitary peer ids return ``thread_error`` and do
not touch the filesystem.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, Union

from .account_registry import PeerAccountRegistry
from .thread_fs import (
    ANONYMOUS_PEER_ID,
    ThreadFsError,
    ThreadQuotaError,
    charge_thread_quota,
    list_files,
    read_file,
    sanitize_peer_id,
    sanitize_thread_id,
    thread_exists,
    write_file,
)

JsonResponse = Tuple[int, Dict[str, Any]]

_registry: Optional[PeerAccountRegistry] = None


def set_account_registry(registry: Optional[PeerAccountRegistry]) -> None:
    global _registry
    _registry = registry


def get_account_registry() -> PeerAccountRegistry:
    global _registry
    if _registry is None:
        _registry = PeerAccountRegistry()
    return _registry


def resolve_request_identities(raw_peer_id: Optional[str]) -> Dict[str, Any]:
    """Map a request peer id to billing vs filesystem identities."""
    billing_peer = raw_peer_id or "peer"
    if raw_peer_id is None or (isinstance(raw_peer_id, str) and not raw_peer_id.strip()):
        return {
            "ok": True,
            "billing_peer_id": billing_peer,
            "fs_peer_id": ANONYMOUS_PEER_ID,
        }
    try:
        fs_peer = sanitize_peer_id(raw_peer_id)
    except ThreadFsError as exc:
        return {
            "ok": False,
            "billing_peer_id": billing_peer,
            "fs_peer_id": None,
            "thread_error": str(exc),
        }
    return {
        "ok": True,
        "billing_peer_id": billing_peer,
        "fs_peer_id": fs_peer,
    }


def _token_gate(registry: PeerAccountRegistry, billing_peer_id: str) -> Optional[JsonResponse]:
    acct = registry.get_account_by_peer(billing_peer_id)
    if acct and acct.get("token_balance", 0) <= 0:
        return (
            402,
            {"error": "Insufficient tokens: balance is 0. Top up to continue."},
        )
    return None


def _require_existing_thread(fs_peer_id: str, raw_thread_id: Optional[str], *, root=None) -> Union[JsonResponse, Tuple[None, str, str]]:
    if not raw_thread_id or not str(raw_thread_id).strip():
        return 400, {"error": "Missing 'thread_id'"}
    try:
        tid = sanitize_thread_id(raw_thread_id)
    except ThreadFsError as exc:
        return 400, {"error": str(exc), "thread_error": str(exc)}
    if not thread_exists(fs_peer_id, tid, root=root):
        return 404, {"error": "Thread not found", "peer_id": fs_peer_id, "thread_id": tid}
    return None, fs_peer_id, tid  # type: ignore[return-value]


def api_list_files(
    raw_peer_id: Optional[str],
    thread_id: Optional[str],
    *,
    subpath: str = "",
    registry: Optional[PeerAccountRegistry] = None,
    root=None,
) -> JsonResponse:
    registry = registry or get_account_registry()
    ident = resolve_request_identities(raw_peer_id)
    if not ident["ok"]:
        return 400, {"error": ident["thread_error"], "thread_error": ident["thread_error"]}
    gated = _token_gate(registry, ident["billing_peer_id"])
    if gated:
        return gated
    required = _require_existing_thread(ident["fs_peer_id"], thread_id, root=root)
    if required[0] is not None:
        return required  # type: ignore[return-value]
    _, fs_peer, tid = required
    try:
        entries = list_files(fs_peer, tid, subpath=subpath or "", root=root)
    except ThreadFsError as exc:
        return 400, {"error": str(exc), "thread_error": str(exc)}
    return 200, {
        "peer_id": fs_peer,
        "thread_id": tid,
        "files": entries,
    }


def api_read_file(
    raw_peer_id: Optional[str],
    thread_id: Optional[str],
    relpath: Optional[str],
    *,
    registry: Optional[PeerAccountRegistry] = None,
    root=None,
) -> JsonResponse:
    registry = registry or get_account_registry()
    ident = resolve_request_identities(raw_peer_id)
    if not ident["ok"]:
        return 400, {"error": ident["thread_error"], "thread_error": ident["thread_error"]}
    gated = _token_gate(registry, ident["billing_peer_id"])
    if gated:
        return gated
    if not relpath or not str(relpath).strip():
        return 400, {"error": "Missing 'path'"}
    required = _require_existing_thread(ident["fs_peer_id"], thread_id, root=root)
    if required[0] is not None:
        return required  # type: ignore[return-value]
    _, fs_peer, tid = required
    try:
        content = read_file(fs_peer, tid, relpath, root=root)
    except ThreadFsError as exc:
        msg = str(exc)
        code = 404 if "not found" in msg else 400
        return code, {"error": msg, "thread_error": msg}
    return 200, {
        "peer_id": fs_peer,
        "thread_id": tid,
        "path": relpath,
        "content": content,
    }


def api_write_file(
    raw_peer_id: Optional[str],
    thread_id: Optional[str],
    relpath: Optional[str],
    content: Any,
    *,
    registry: Optional[PeerAccountRegistry] = None,
    root=None,
) -> JsonResponse:
    registry = registry or get_account_registry()
    ident = resolve_request_identities(raw_peer_id)
    if not ident["ok"]:
        return 400, {"error": ident["thread_error"], "thread_error": ident["thread_error"]}
    gated = _token_gate(registry, ident["billing_peer_id"])
    if gated:
        return gated
    if not relpath or not str(relpath).strip():
        return 400, {"error": "Missing 'path'"}
    if content is None:
        return 400, {"error": "Missing 'content'"}
    required = _require_existing_thread(ident["fs_peer_id"], thread_id, root=root)
    if required[0] is not None:
        return required  # type: ignore[return-value]
    _, fs_peer, tid = required
    if not isinstance(content, (str, bytes)):
        content = str(content)
    billing_peer = ident["billing_peer_id"]

    def _bill(plan: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return charge_thread_quota(registry, billing_peer, plan)

    try:
        write_file(fs_peer, tid, relpath, content, root=root, billing=_bill)
    except ThreadQuotaError as exc:
        status = 413 if exc.code == "hard_limit" else 402
        return status, {
            "error": str(exc),
            "thread_error": str(exc),
            "quota": {
                "code": exc.code,
                "overage_bytes": exc.overage_bytes,
                "tokens_required": exc.tokens_required,
                "plan": {k: v for k, v in exc.plan.items() if k != "billing"},
            },
        }
    except ThreadFsError as exc:
        return 400, {"error": str(exc), "thread_error": str(exc)}
    return 200, {
        "peer_id": fs_peer,
        "thread_id": tid,
        "path": relpath,
        "status": "written",
    }
