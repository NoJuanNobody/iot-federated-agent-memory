"""HTTP routes for arena brain context stores and context-aware duels.

Mounted by ``server.MeshGatewayHandler`` (``ARENA_CONTEXT_API.handle_get`` /
``handle_post``). Every route resolves the requesting account on the server
and only ever opens that account's stores, so one user can never name another
user's files: the account is not a request parameter.

Identity (see :meth:`ArenaContextAPI.identify`): the server-side sign-in
session (``MeshGatewayHandler._session_account``: HttpOnly ``tincan_session``
cookie or Bearer token). A client-sent peer_id is never trusted. The shared
``peer``/``anonymous`` buckets and auto-provisioned ``@mesh.local`` guest
ledgers are refused.

Duels are not a separate endpoint: ``/api/chat`` with ``arena=true`` (the
per-account billing flow: ``/api/mesh/arena/match`` then one call per side)
calls :meth:`ArenaContextAPI.inject_context` when the request names an
``agent_id``, so context-injected duels are billed exactly like every duel.

Routes::

    GET  /api/arena/context/status                     drive mirror + identity
    GET  /api/arena/context/agents                     this account's brains
    GET  /api/arena/context/files?agent_id=            list files
    GET  /api/arena/context/file?agent_id=&path=       read one file
    GET  /api/arena/context/search?agent_id=&q=&k=     ranked snippets
    POST /api/arena/context/ingest                     upload / paste (.space unpacked)
    POST /api/arena/context/import                     copy from the user's own Agent Space
    POST /api/arena/context/drive/link                 link drive-mirror files (local only)
    POST /api/arena/context/delete                     remove a file
"""

from __future__ import annotations

import base64
import binascii
import json
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs

from .arena_context import (
    ArenaContextRegistry,
    ContextStoreError,
    build_context_messages,
    validate_agent_id,
)

RESERVED_PEER_IDS = frozenset({"", "peer", "anonymous", "default_user", "relay", "system"})
MAX_JSON_BYTES = 12 * 1024 * 1024
MAX_PROMPT_CHARS = 8000


class ArenaContextAPI:
    def __init__(self, registry: ArenaContextRegistry, account_registry: Any,
                 banned_peers: Optional[Dict[str, Any]] = None,
                 space_manager_getter: Any = None):
        self.registry = registry
        # An object, or a zero-arg callable returning the live registry (server.py
        # passes a getter so a swapped-in registry is always the one used).
        self._accounts = account_registry
        self.banned = banned_peers if banned_peers is not None else {}
        self.space_manager_getter = space_manager_getter

    @property
    def accounts(self) -> Any:
        acc = self._accounts
        return acc() if callable(acc) and not hasattr(acc, "get_account_by_peer") else acc

    # ------------------------------------------------------------ plumbing
    @staticmethod
    def _send_error(handler, err: ContextStoreError) -> None:
        handler._send_json({"error": err.message, "code": err.code}, err.status)

    @staticmethod
    def _read_json(handler) -> Dict[str, Any]:
        try:
            length = int(handler.headers.get("Content-Length", 0) or 0)
        except ValueError:
            raise ContextStoreError("Bad Content-Length.", 400)
        if length > MAX_JSON_BYTES:
            # Refuse before reading an oversized body; drop the connection.
            handler.close_connection = True
            raise ContextStoreError("Request too large (12 MB max).", 413, "too_large")
        raw = handler.rfile.read(length) if length else b""
        try:
            data = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ContextStoreError("Body must be JSON.", 400)
        if not isinstance(data, dict):
            raise ContextStoreError("Body must be a JSON object.", 400)
        return data

    def identify(self, handler, data: Optional[Dict[str, Any]] = None,
                 query: Optional[Dict[str, List[str]]] = None) -> Tuple[Dict[str, Any], str]:
        """Resolve the signed-in account from the server session. Raises 401/403."""
        session_lookup = getattr(handler, "_session_account", None)
        account = session_lookup() if callable(session_lookup) else None
        if not account:
            raise ContextStoreError(
                "Sign in to use brain context. Arena files and duels belong to your own account.",
                401, "sign_in_required")
        acct_id = str(account.get("peer_id") or "")
        if acct_id in RESERVED_PEER_IDS or str(account.get("email") or "").endswith("@mesh.local"):
            raise ContextStoreError(
                "This is a shared or guest ledger, not your account. Create your TinCan account first.",
                403, "shared_bucket_refused")
        if acct_id in self.banned:
            raise ContextStoreError("This account is banned from the arena.", 403, "banned")
        return account, "session"

    # --------------------------------------------------------------- routes
    def handle_get(self, handler, parsed) -> bool:
        path = parsed.path
        if not path.startswith("/api/arena/context"):
            return False
        query = parse_qs(parsed.query)
        q = lambda k, d="": (query.get(k) or [d])[0]
        try:
            account, via = self.identify(handler, query=query)
            pid = account["peer_id"]
            if path == "/api/arena/context/status":
                handler._send_json({
                    "account": {"peer_id": pid, "username": account.get("username") or "",
                                "token_balance": account.get("token_balance", 0)},
                    "auth": via,
                    "drive_mirror": {
                        **self.registry.drive.status(),
                        "allowed_here": self._drive_allowed(handler),
                    },
                    "agents": self.registry.list_agents(pid),
                }, 200)
            elif path == "/api/arena/context/agents":
                handler._send_json({"agents": self.registry.list_agents(pid)}, 200)
            elif path == "/api/arena/context/files":
                store = self.registry.store(pid, q("agent_id"))
                files = store.list_files()
                handler._send_json({"agent_id": store.agent_id, "files": files, "count": len(files),
                                    **store.summary()}, 200)
            elif path == "/api/arena/context/file":
                store = self.registry.store(pid, q("agent_id"))
                handler._send_json(store.read_file(q("path")), 200)
            elif path == "/api/arena/context/search":
                store = self.registry.store(pid, q("agent_id"))
                try:
                    k = int(q("k", "6"))
                except ValueError:
                    k = 6
                handler._send_json({"agent_id": store.agent_id, **store.search(q("q"), top_k=k)}, 200)
            else:
                handler._send_json({"error": "Not found"}, 404)
        except ContextStoreError as err:
            self._send_error(handler, err)
        except Exception:
            handler._send_json({"error": "Context store error. Please try again.", "code": "server_error"}, 500)
        return True

    def handle_post(self, handler, parsed) -> bool:
        path = parsed.path
        if not path.startswith("/api/arena/context/"):
            return False
        try:
            data = self._read_json(handler)
            account, _via = self.identify(handler, data=data)
            pid = account["peer_id"]
            store = self.registry.store(pid, data.get("agent_id"))
            who = str(account.get("username") or pid)[:64]
            if path == "/api/arena/context/ingest":
                files = data.get("files")
                if files is None and ("content" in data or "content_b64" in data):
                    files = [data]
                if not isinstance(files, list) or not files:
                    raise ContextStoreError("Send files: [{name, content}] or [{name, content_b64}].", 400)
                if len(files) > 50:
                    raise ContextStoreError("Up to 50 files per request.", 400)
                added, errors = [], []
                for f in files:
                    if not isinstance(f, dict):
                        errors.append({"name": "", "error": "Each file must be an object."})
                        continue
                    name = f.get("path") or f.get("name")
                    source = str(f.get("source") or data.get("source") or "upload")
                    try:
                        if f.get("content_b64") is not None:
                            try:
                                raw = base64.b64decode(str(f["content_b64"]), validate=True)
                            except (binascii.Error, ValueError):
                                raise ContextStoreError("content_b64 is not valid base64.", 400)
                            added.extend(store.ingest_bytes(name, raw, source=source, added_by=who))
                        else:
                            added.append(store.ingest_text(name, f.get("content", ""), source=source, added_by=who))
                    except ContextStoreError as err:
                        errors.append({"name": str(name or ""), "error": err.message, "code": err.code})
                status = 200 if added else 400
                handler._send_json({"agent_id": store.agent_id, "added": added, "errors": errors,
                                    **store.summary()}, status)
            elif path == "/api/arena/context/import":
                sm = self.space_manager_getter() if self.space_manager_getter else None
                if sm is None:
                    raise ContextStoreError("Agent Space is not available on this server.", 503)
                # Only spaces this account owns: its primary peer_id and its linked devices.
                owners = {pid}
                if hasattr(self.accounts, "list_linked_peers"):
                    owners.update(self.accounts.list_linked_peers(pid))
                owner = str(data.get("space_owner") or pid).strip()
                if owner not in owners and self.accounts.resolve_account_peer_id(owner) != pid:
                    raise ContextStoreError("You can only import from your own Agent Space.", 403, "not_your_space")
                space = sm.get_or_create_space("user", owner)
                paths = data.get("paths") or None
                if paths is not None and not isinstance(paths, list):
                    raise ContextStoreError("paths must be a list.", 400)
                added = store.import_from_space(space, paths=paths, added_by=who)
                handler._send_json({"agent_id": store.agent_id, "added": added, **store.summary()}, 200)
            elif path == "/api/arena/context/drive/link":
                if not self._drive_allowed(handler):
                    raise ContextStoreError(
                        "Drive files can only be linked from the machine running TinCan, with the drive mirror on.",
                        403, "drive_mirror_unavailable")
                added = store.link_drive(str(data.get("drive_path") or ""), added_by=who)
                handler._send_json({"agent_id": store.agent_id, "added": added, **store.summary()}, 200)
            elif path == "/api/arena/context/delete":
                store.delete(data.get("path"))
                handler._send_json({"agent_id": store.agent_id, "deleted": data.get("path"), **store.summary()}, 200)
            else:
                handler._send_json({"error": "Not found"}, 404)
        except ContextStoreError as err:
            self._send_error(handler, err)
        except Exception:
            handler._send_json({"error": "Context store error. Please try again.", "code": "server_error"}, 500)
        return True

    def _drive_allowed(self, handler) -> bool:
        if not self.registry.drive.enabled():
            return False
        server_check = getattr(handler, "_drive_mirror_allowed", None)
        if callable(server_check):
            return bool(server_check())
        client_ip = handler.client_address[0] if getattr(handler, "client_address", None) else ""
        return self.registry.drive.request_allowed(
            client_ip, handler.headers.get("Host", ""), handler.headers.get("X-Forwarded-For", ""))

    # ------------------------------------------------- duel context injection
    def inject_context(self, account: Dict[str, Any], data: Dict[str, Any], model: str,
                       messages: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Prepend this brain's retrieved files to one arena side's messages.

        Called from ``/api/chat`` (arena=true) after the session account is
        resolved and before the side is authorized and billed, so the context
        tokens count toward the side's worst-case estimate and its bill.
        """
        agent_id = validate_agent_id(data.get("agent_id"))
        use = data.get("use_context", True)
        enabled = bool(use) and str(use).lower() not in ("0", "false", "off")
        query = str(data.get("prompt") or "").strip()
        if not query:
            users = [m for m in messages if isinstance(m, dict) and m.get("role") == "user"]
            query = str(users[-1].get("content", "")) if users else ""
        ctx: Dict[str, Any] = {"snippets": [], "files": [], "tokens": 0}
        if enabled and query:
            ctx = self.registry.store(account["peer_id"], agent_id).search(query[:MAX_PROMPT_CHARS])
        summary = {
            "agent_id": agent_id,
            "enabled": enabled,
            "files": ctx.get("files", []),
            "tokens": ctx.get("tokens", 0),
            "snippets": [
                {k: sn[k] for k in ("path", "chunk", "source", "score", "tokens", "span", "text")}
                for sn in ctx.get("snippets", [])
            ],
        }
        return build_context_messages(agent_id, model, ctx) + list(messages), summary
