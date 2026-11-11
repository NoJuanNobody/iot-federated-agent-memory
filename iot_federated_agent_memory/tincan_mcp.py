"""
TinCan MCP Protocol Server & Client Tools.

Exposes MCP tools for agent-to-agent encrypted communication over the TinCan Blind Relay:
- tincan_whoami(): returns current local address, alias, and public key.
- tincan_send(recipient_address, message, speak=False): encrypts, signs, and posts ciphertext to relay.
- tincan_read(since_seq=0): fetches inbox ciphertext from relay, decrypts using local private key, verifies sender signature, returns decrypted messages.
- tincan_list_contacts(): lists trusted aliases and addresses.
- tincan_add_contact(alias, address): pins contact key.

Can be used programmatically in Python, as an MCP stdio server for Claude Code/IDE harnesses,
or via CLI.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import sys
import time
import urllib.parse
import urllib.request
import uuid
from typing import Any, Dict, List, Optional

import nacl.signing

from .tincan_core import (
    ContactBook,
    DecryptionError,
    InvalidAddressError,
    KeyConflictError,
    TinCanIdentity,
    address_to_verify_key,
    decode_address,
    encode_address,
    open_payload,
    seal_payload,
    sign_envelope as core_sign_envelope,
    validate_address,
    verify_envelope as core_verify_envelope,
)
from .tincan_relay import TinCanBlindRelay

logger = logging.getLogger("tincan.mcp")

MCP_TOOLS_DEFINITIONS = [
    {
        "name": "tincan_whoami",
        "description": "Returns current local TinCan identity, address (tc:...), alias, and public key.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "tincan_send",
        "description": "Encrypts, signs, and posts sealed ciphertext to relay for a recipient address or contact alias.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "recipient_address": {
                    "type": "string",
                    "description": "Recipient TinCan address (tc:...) or trusted alias from contacts.",
                },
                "message": {
                    "type": "string",
                    "description": "Plaintext message content to seal and send.",
                },
                "speak": {
                    "type": "boolean",
                    "description": "Request recipient to vocalize message via TTS (kokoro-say).",
                    "default": False,
                },
            },
            "required": ["recipient_address", "message"],
        },
    },
    {
        "name": "tincan_read",
        "description": "Fetches inbox ciphertext from relay, decrypts using local private key, verifies sender signature, returns decrypted messages.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "since_seq": {
                    "type": "integer",
                    "description": "Sequence number offset (only return messages after since_seq).",
                    "default": 0,
                },
            },
            "required": [],
        },
    },
    {
        "name": "tincan_list_contacts",
        "description": "Lists trusted contacts, pinned public keys, and aliases.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "tincan_add_contact",
        "description": "Pins a contact's public key and associates it with an alias (TOFU).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "alias": {
                    "type": "string",
                    "description": "Human-readable name or alias for the contact.",
                },
                "address": {
                    "type": "string",
                    "description": "TinCan address (tc:<52 base32 chars>).",
                },
            },
            "required": ["alias", "address"],
        },
    },
    {
        "name": "tincan_rodin_generate",
        "description": "Dispatches generative 3D mesh creation via Hyper3D Rodin (Ronin), returns task UUID, status, and GLB mesh assets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Natural language prompt describing the 3D model to generate.",
                },
                "tier": {
                    "type": "string",
                    "description": "Generation tier: Regular ($0.50), Sketch ($0.25), Detail ($1.00), Smooth ($0.75).",
                    "enum": ["Regular", "Sketch", "Detail", "Smooth"],
                    "default": "Regular",
                },
                "format": {
                    "type": "string",
                    "description": "3D asset format (glb, fbx, obj, usdz).",
                    "enum": ["glb", "fbx", "obj", "usdz"],
                    "default": "glb",
                },
                "mesh_mode": {
                    "type": "string",
                    "description": "Mesh topology mode (Quad, Triangle).",
                    "default": "Quad",
                },
                "scope": {
                    "type": "string",
                    "description": "VFS target space scope ('user' or 'topic').",
                    "default": "user",
                },
                "owner_id": {
                    "type": "string",
                    "description": "Owner ID or Topic ID if saving into .space VFS.",
                },
                "save_path": {
                    "type": "string",
                    "description": "Optional VFS path inside .space (e.g. /models3d/model.glb).",
                },
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "tincan_space_ls",
        "description": "Lists all files, sizes, MIME types, and Merkle root in a single-file SQLite .space VFS.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "scope": {
                    "type": "string",
                    "description": "Target space scope ('user' or 'topic').",
                    "enum": ["user", "topic"],
                    "default": "user",
                },
                "owner_id": {
                    "type": "string",
                    "description": "Owner peer ID or Forum Topic ID (defaults to local identity).",
                },
            },
            "required": [],
        },
    },
    {
        "name": "tincan_space_write",
        "description": "Writes, patches, or deletes a file inside a single-file SQLite .space VFS.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Virtual file path (e.g. /src/main.py, /artcraft/design.dxf).",
                },
                "content": {
                    "type": "string",
                    "description": "File text content or base64 binary payload.",
                },
                "scope": {
                    "type": "string",
                    "description": "Target space scope ('user' or 'topic').",
                    "enum": ["user", "topic"],
                    "default": "user",
                },
                "owner_id": {
                    "type": "string",
                    "description": "Owner peer ID or Forum Topic ID.",
                },
                "action": {
                    "type": "string",
                    "description": "File action ('write', 'patch', or 'delete').",
                    "enum": ["write", "patch", "delete"],
                    "default": "write",
                },
                "target": {
                    "type": "string",
                    "description": "Target string to replace when action is 'patch'.",
                },
                "replacement": {
                    "type": "string",
                    "description": "Replacement string when action is 'patch'.",
                },
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "tincan_space_exec",
        "description": "Executes playground code or Wasm runtime inside a single-file SQLite .space VFS.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entrypoint": {
                    "type": "string",
                    "description": "Path to entrypoint script (e.g. /src/main.py).",
                    "default": "/src/main.py",
                },
                "runtime": {
                    "type": "string",
                    "description": "Runtime environment ('auto', 'python', 'js', 'wasm', 'artcraft-wasm').",
                    "default": "auto",
                },
                "scope": {
                    "type": "string",
                    "description": "Target space scope ('user' or 'topic').",
                    "default": "user",
                },
                "owner_id": {
                    "type": "string",
                    "description": "Owner peer ID or Forum Topic ID.",
                },
                "code_override": {
                    "type": "string",
                    "description": "Optional inline code string to execute instead of file.",
                },
                "args": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Optional CLI arguments to pass to the script.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "tincan_space_agent",
        "description": "Runs an autonomous coding agent turn inside a single-file SQLite .space VFS.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Coding instruction or task for the space agent.",
                },
                "model": {
                    "type": "string",
                    "description": "AI model alias (gemini-brain, claude-brain, grok-brain, openai-brain).",
                    "default": "gemini-brain",
                },
                "scope": {
                    "type": "string",
                    "description": "Target space scope ('user' or 'topic').",
                    "default": "user",
                },
                "owner_id": {
                    "type": "string",
                    "description": "Owner peer ID or Forum Topic ID.",
                },
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "tincan_space_note",
        "description": "Adds a note to a .space for the next Apply: an observation, code snippet, side-run result, or proposed edit. Notes change no files; tincan_space_apply compiles them into a new version.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "body": {"type": "string", "description": "Note text. Code and multi-line content are fine."},
                "kind": {
                    "type": "string",
                    "enum": ["observation", "question", "code", "result", "edit"],
                    "default": "observation",
                },
                "path": {"type": "string", "description": "File inside the space the note is about (optional)."},
                "scope": {"type": "string", "description": "Target space scope ('user' or 'topic').", "default": "user"},
                "owner_id": {"type": "string", "description": "Owner peer ID or Forum Topic ID."},
            },
            "required": ["body"],
        },
    },
    {
        "name": "tincan_space_notes",
        "description": "Lists notes in a .space (pending by default), each flagged `stale` if its file changed since it was written.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["pending", "applied", "dropped", "all"], "default": "pending"},
                "scope": {"type": "string", "description": "Target space scope ('user' or 'topic').", "default": "user"},
                "owner_id": {"type": "string", "description": "Owner peer ID or Forum Topic ID."},
            },
            "required": [],
        },
    },
    {
        "name": "tincan_space_apply",
        "description": "Compiles pending notes into a new version of the .space files. Without plan_id it only PROPOSES a plan (no files change) and returns its plan_id; call again with that plan_id to commit it as a new version.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "plan_id": {"type": "string", "description": "Commit this previously proposed plan."},
                "model": {"type": "string", "description": "AI model alias for proposing.", "default": "gemini-brain"},
                "note_ids": {"type": "array", "items": {"type": "string"}, "description": "Only apply these notes."},
                "instruction": {"type": "string", "description": "Extra instruction for the Apply step."},
                "scope": {"type": "string", "description": "Target space scope ('user' or 'topic').", "default": "user"},
                "owner_id": {"type": "string", "description": "Owner peer ID or Forum Topic ID."},
            },
            "required": [],
        },
    },
    {
        "name": "tincan_thread_list_files",
        "description": "List files in a TinCan thread workspace (files/), scoped by peer_id and thread_id. Uses the same token gate as /api/chat.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "peer_id": {"type": "string", "description": "Peer that owns the thread. Blank uses the anonymous bucket."},
                "thread_id": {"type": "string", "description": "Server-minted thread id."},
                "subpath": {"type": "string", "description": "Optional subdirectory under files/.", "default": ""},
            },
            "required": ["thread_id"],
        },
    },
    {
        "name": "tincan_thread_read_file",
        "description": "Read a file from a TinCan thread workspace, scoped by peer_id and thread_id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "peer_id": {"type": "string", "description": "Peer that owns the thread. Blank uses the anonymous bucket."},
                "thread_id": {"type": "string", "description": "Server-minted thread id."},
                "path": {"type": "string", "description": "Relative path under files/."},
            },
            "required": ["thread_id", "path"],
        },
    },
    {
        "name": "tincan_thread_write_file",
        "description": "Write a file in a TinCan thread workspace, scoped by peer_id and thread_id. Over-tier writes debit tokens via PeerAccountRegistry.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "peer_id": {"type": "string", "description": "Peer that owns the thread. Blank uses the anonymous bucket."},
                "thread_id": {"type": "string", "description": "Server-minted thread id."},
                "path": {"type": "string", "description": "Relative path under files/."},
                "content": {"type": "string", "description": "File contents to write."},
            },
            "required": ["thread_id", "path", "content"],
        },
    },
]


class TinCanMCPClient:
    """Client implementing the TinCan identity, encryption, contact pinning, and relay interface."""

    def __init__(
        self,
        relay_url: Optional[str] = None,
        config_dir: Optional[str] = None,
        alias: str = "default",
        relay: Optional[TinCanBlindRelay] = None,
    ):
        self.relay_url = (relay_url or os.environ.get("TINCAN_RELAY_URL", "http://localhost:8080")).rstrip("/")
        self.config_dir = config_dir or os.environ.get("TINCAN_DIR", os.path.expanduser("~/.tin-can"))
        self.alias = alias
        self.relay = relay

        self.identities_dir = os.path.join(self.config_dir, "identities")
        self.contacts_file = os.path.join(self.config_dir, "contacts.json")

        os.makedirs(self.identities_dir, exist_ok=True)
        self.identity = self._load_or_create_identity()
        self.address = self.identity.address
        self.public_key_hex = bytes(self.identity.verify_key).hex()

        self.contact_book = ContactBook(raise_on_conflict=True)
        self.role_file = os.path.join(self.config_dir, "role.json")
        self._load_contacts()

    def get_my_role(self) -> str:
        """Returns the current operator's role ('admin', 'moderator', 'mentor', 'mentee', 'peer')."""
        env_role = os.environ.get("TINCAN_ROLE", "").strip().lower()
        if env_role in ("admin", "moderator", "mentor", "mentee", "peer"):
            return env_role
        if os.path.exists(self.role_file):
            try:
                with open(self.role_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                r = data.get(self.alias) or data.get("default") or data.get("role")
                if r and str(r).lower() in ("admin", "moderator", "mentor", "mentee", "peer"):
                    return str(r).lower()
            except Exception:
                pass
        return "peer"

    def set_my_role(self, role: str) -> str:
        """Sets and persists the operator's role ('admin', 'moderator', 'mentor', 'mentee', 'peer')."""
        norm = role.strip().lower()
        if norm not in ("admin", "moderator", "mentor", "mentee", "peer"):
            raise ValueError(f"Invalid role '{role}'. Choose from: admin, moderator, mentor, mentee, peer")
        data = {}
        if os.path.exists(self.role_file):
            try:
                with open(self.role_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data[self.alias] = norm
        with open(self.role_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return norm

    def _load_or_create_identity(self) -> TinCanIdentity:
        key_path = os.path.join(self.identities_dir, f"{self.alias}.key")
        if os.path.exists(key_path):
            with open(key_path, "rb") as f:
                seed = f.read()
            if len(seed) >= 32:
                return TinCanIdentity.from_private_bytes(seed[:32])

        # Generate new key and save with 0600 mode
        identity = TinCanIdentity.generate()
        fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with open(fd, "wb") as f:
            f.write(identity.signing_key.encode())
        return identity

    def _load_contacts(self) -> None:
        if os.path.exists(self.contacts_file):
            try:
                with open(self.contacts_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for alias, info in data.items():
                    addr = info.get("address") if isinstance(info, dict) else info
                    meta = info.get("metadata", {}) if isinstance(info, dict) else {}
                    if addr and validate_address(addr):
                        self.contact_book.pin(alias, addr, metadata=meta, raise_on_conflict=False)
            except Exception as exc:
                logger.warning("Could not load contacts from %s: %s", self.contacts_file, exc)

    def _save_contacts(self) -> None:
        try:
            contacts_dict = self.contact_book.list_contacts()
            with open(self.contacts_file, "w", encoding="utf-8") as f:
                json.dump(contacts_dict, f, indent=2)
        except Exception as exc:
            logger.warning("Could not persist contacts to %s: %s", self.contacts_file, exc)

    def find_alias(self, address: str) -> Optional[str]:
        aliases = self.contact_book.get_aliases_for_address(address)
        return aliases[0] if aliases else None

    def _http_post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.relay_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "TinCanMCP/1.0"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _http_get(self, path: str) -> Dict[str, Any]:
        url = f"{self.relay_url}{path}"
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "TinCanMCP/1.0"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # -------------------------------------------------------------------------
    # Core MCP Tools
    # -------------------------------------------------------------------------

    def tincan_whoami(self, **kwargs) -> Dict[str, Any]:
        """Returns current local address, alias, role, and public key."""
        my_role = self.get_my_role()
        return {
            "alias": self.alias,
            "address": self.address,
            "role": my_role,
            "is_admin": my_role in ("admin", "moderator"),
            "public_key": self.public_key_hex,
            "public_key_b32": self.address[3:].split("@")[0],
            "relay_url": self.relay_url,
            "contacts_count": len(self.contact_book),
        }

    def tincan_send(
        self,
        recipient_address: str,
        message: str,
        speak: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Encrypts, signs, and posts ciphertext to relay."""
        if not recipient_address:
            raise ValueError("recipient_address is required")
        if not message:
            raise ValueError("message content is required")

        # Check if recipient_address is a known alias
        resolved_address = recipient_address
        resolved_alias = None
        if self.contact_book.has_alias(recipient_address):
            resolved_alias = recipient_address
            resolved_address = self.contact_book.get_address(recipient_address)
        else:
            resolved_alias = self.find_alias(recipient_address)

        clean_recipient = resolved_address.split("@")[0].strip()
        if not validate_address(clean_recipient):
            raise ValueError(f"Invalid recipient TinCan address: {resolved_address}")

        # Assemble inner plaintext message
        envelope_id = kwargs.get("id") or str(uuid.uuid4())
        inner_msg = {
            "id": envelope_id,
            "kind": kwargs.get("kind", "chat"),
            "text": str(message),
            "speak": bool(speak),
            "sender_role": kwargs.get("sender_role") or self.get_my_role(),
            "expects_reply": kwargs.get("expects_reply", False),
            "reply_to": kwargs.get("reply_to"),
            "hop": int(kwargs.get("hop", 0)),
            "as": self.alias,
            "created_at": time.time(),
        }

        # Encrypt inner message into SealedBox (X25519)
        ciphertext_b64 = self.identity.seal_for(clean_recipient, json.dumps(inner_msg))

        # Sign envelope using TinCanIdentity (Ed25519)
        nonce = base64.b64encode(os.urandom(16)).decode("ascii")
        timestamp = float(kwargs.get("timestamp", time.time()))
        seq = int(kwargs.get("seq", self.identity.next_seq()))

        envelope = self.identity.create_envelope(
            recipient=clean_recipient,
            payload=ciphertext_b64,
            seq=seq,
            timestamp=timestamp,
            envelope_id=envelope_id,
            speak=bool(speak),
            nonce=nonce,
        )

        if self.relay is not None:
            relay_resp = self.relay.send(envelope)
        else:
            relay_resp = self._http_post("/api/tincan/send", envelope)

        return {
            "status": "sent",
            "seq": relay_resp.get("seq"),
            "envelope_id": envelope_id,
            "recipient": clean_recipient,
            "alias": resolved_alias,
            "speak": bool(speak),
            "delivered_at": relay_resp.get("delivered_at"),
        }

    def tincan_read(self, since_seq: int = 0, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetches inbox ciphertext from relay, decrypts using local private key,
        verifies sender signature, returns decrypted messages.
        """
        since_seq = int(since_seq)
        timeout = float(kwargs.get("timeout", 0.0))

        if self.relay is not None:
            raw_inbox = self.relay.inbox(self.address, since_seq=since_seq, timeout=timeout)
        else:
            raw_inbox = self._http_get(
                f"/api/tincan/inbox?address={urllib.parse.quote(self.address)}&since_seq={since_seq}&timeout={timeout}"
            )

        decrypted_messages: List[Dict[str, Any]] = []
        for msg in raw_inbox.get("messages", []):
            sender = msg.get("from") or msg.get("sender")
            box = msg.get("box") or msg.get("ciphertext") or msg.get("payload")
            sig = msg.get("signature") or msg.get("sig")
            nonce = msg.get("nonce", "")
            ts = msg.get("timestamp") if msg.get("timestamp") is not None else msg.get("ts", 0)
            seq = msg.get("seq")
            envelope_id = msg.get("envelope_id")

            # Verify sender signature
            verified = False
            raw_env_str = msg.get("raw_envelope")
            if raw_env_str:
                try:
                    raw_dict = json.loads(raw_env_str)
                    if "signature" in raw_dict and core_verify_envelope(raw_dict):
                        verified = True
                except Exception:
                    pass

            if not verified:
                try:
                    # 1. Try dict format stripping extraneous helper keys
                    clean = {
                        k: v for k, v in msg.items()
                        if k not in ("to", "from", "box", "ciphertext", "sig", "ts", "delivered_at", "created_at", "raw_envelope")
                    }
                    if "signature" in clean and core_verify_envelope(clean):
                        verified = True
                except Exception:
                    verified = False

            if not verified:
                # 2. Try pipe format fallback
                try:
                    to_norm = self.address.split("@")[0].strip()
                    from_norm = sender.split("@")[0].strip()
                    vk = address_to_verify_key(from_norm)
                    sig_bytes = base64.b64decode(sig)
                    for can in [
                        f"1|{to_norm}|{from_norm}|{ts}|{nonce}|{box}",
                        f"1|{to_norm}|{from_norm}|{int(float(ts))}|{nonce}|{box}",
                    ]:
                        try:
                            vk.verify(can.encode("utf-8"), sig_bytes)
                            verified = True
                            break
                        except Exception:
                            continue
                except Exception:
                    verified = False

            # Decrypt SealedBox
            try:
                plain_str = self.identity.open_sealed(box)
                try:
                    inner = json.loads(plain_str)
                    if not isinstance(inner, dict):
                        inner = {"text": str(inner), "speak": msg.get("speak", False)}
                except (json.JSONDecodeError, ValueError):
                    inner = {"text": plain_str, "speak": msg.get("speak", False)}
            except Exception as exc:
                inner = {"error": f"Failed to decrypt: {exc}", "text": None}

            sender_alias = self.find_alias(sender)
            sender_meta: Dict[str, Any] = {}
            if sender_alias:
                c_info = self.contact_book.get_contact(sender_alias)
                if c_info:
                    sender_meta = c_info.get("metadata", {})

            decrypted_messages.append({
                "seq": seq,
                "envelope_id": envelope_id or inner.get("id"),
                "sender": sender,
                "sender_alias": sender_alias,
                "sender_role": sender_meta.get("role", "peer"),
                "sender_trust_mentor_tts": bool(sender_meta.get("trust_mentor_tts", False)),
                "recipient": self.address,
                "timestamp": ts,
                "verified": verified,
                "message": inner.get("text"),
                "speak": inner.get("speak", False),
                "inner": inner,
            })

        return decrypted_messages

    def tincan_list_contacts(self, **kwargs) -> List[Dict[str, Any]]:
        """Lists trusted aliases, addresses, and mentorship roles."""
        result = []
        for alias, info in sorted(self.contact_book.list_contacts().items()):
            addr = info.get("address", "")
            meta = info.get("metadata") or {}
            pub_hex = None
            if validate_address(addr):
                try:
                    pub_hex = decode_address(addr).hex()
                except Exception:
                    pass
            result.append({
                "alias": alias,
                "address": addr,
                "public_key": pub_hex,
                "pinned_at": info.get("pinned_at"),
                "role": meta.get("role", "peer"),
                "trust_mentor_tts": bool(meta.get("trust_mentor_tts", False)),
            })
        return result

    def tincan_add_contact(
        self,
        alias: str,
        address: str,
        role: str = "peer",
        trust_mentor_tts: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Pins contact key with optional role ('admin', 'moderator', 'mentor', 'mentee', 'peer')."""
        if not alias:
            raise ValueError("alias is required")
        if not address:
            raise ValueError("address is required")

        clean_addr = address.split("@")[0].strip()
        pub_bytes = decode_address(clean_addr)
        pk_hex = pub_bytes.hex()
        norm_role = role if role in ("admin", "moderator", "mentor", "mentee", "peer") else "peer"
        meta = {"role": norm_role, "trust_mentor_tts": bool(trust_mentor_tts)}

        self.contact_book.pin(alias, clean_addr, metadata=meta)
        self._save_contacts()

        contact_info = self.contact_book.get_contact(alias)
        pinned_at = contact_info["pinned_at"] if contact_info else time.time()

        return {
            "status": "pinned",
            "alias": alias,
            "address": clean_addr,
            "public_key": pk_hex,
            "pinned_at": pinned_at,
            "role": norm_role,
            "trust_mentor_tts": bool(trust_mentor_tts),
        }

    def set_contact_role(
        self,
        alias: str,
        role: Optional[str] = None,
        trust_mentor_tts: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update role ('admin', 'moderator', 'mentor', 'mentee', 'peer') and voice-gate policy for a pinned contact."""
        if not self.contact_book.has_alias(alias):
            raise ValueError(f"Unknown contact alias '{alias}'. Pin them first with 'tincan add-contact {alias} <tc:address>'.")
        c_info = self.contact_book.get_contact(alias) or {}
        addr = c_info["address"]
        meta = dict(c_info.get("metadata") or {})
        if role is not None:
            norm_r = str(role).strip().lower()
            if norm_r not in ("admin", "moderator", "mentor", "mentee", "peer"):
                raise ValueError(f"Invalid role '{role}'. Choose from: admin, moderator, mentor, mentee, peer")
            meta["role"] = norm_r
        if trust_mentor_tts is not None:
            meta["trust_mentor_tts"] = bool(trust_mentor_tts)
        self.contact_book.pin(alias, addr, metadata=meta)
        self._save_contacts()
        return {
            "status": "updated",
            "alias": alias,
            "address": addr,
            "role": meta.get("role", "peer"),
            "trust_mentor_tts": bool(meta.get("trust_mentor_tts", False)),
        }

    def tincan_rodin_generate(
        self,
        prompt: str,
        tier: str = "Regular",
        format: str = "glb",
        mesh_mode: str = "Quad",
        scope: str = "user",
        owner_id: Optional[str] = None,
        save_path: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Dispatch a 3D generative model request."""
        target_owner = owner_id or self.address
        payload = {
            "prompt": prompt,
            "tier": tier,
            "format": format,
            "mesh_mode": mesh_mode,
            "scope": scope,
            "owner_id": target_owner,
            "save_path": save_path,
            "peer_id": self.address,
        }
        try:
            return self._http_post("/api/3d/generate", payload)
        except Exception:
            # Fallback local generation if relay server is offline
            from .tincan_cli import _get_cli_space_manager
            from .ai_gateway import DynamicAIGatewayRouter
            router_inst = DynamicAIGatewayRouter()
            if hasattr(router_inst, "dispatch_rodin_generation"):
                res = router_inst.dispatch_rodin_generation(prompt=prompt, tier=tier, geometry_file_format=format)
            else:
                fake_glb = b"glTF\x02\x00\x00\x00\x14\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                res = {
                    "uuid": f"rodin-task-{uuid.uuid4().hex[:12]}",
                    "subscription_key": f"sub-{uuid.uuid4().hex[:12]}",
                    "prompt": prompt,
                    "tier": tier,
                    "format": format,
                    "status": "Done",
                    "cost_usd": 0.50,
                    "glb_bytes_b64": base64.b64encode(fake_glb).decode("ascii"),
                    "simulated": True,
                }
            if save_path or owner_id:
                try:
                    sm = _get_cli_space_manager()
                    sp = sm.get_or_create_space(scope, target_owner)
                    sp_p = save_path or f"/models3d/{res.get('uuid', 'model')}.{format}"
                    sp.write_file(sp_p, res.get("glb_bytes_b64", ""), is_base64=True, mime_type="model/gltf-binary", updated_by=self.address)
                    res["saved_to_space"] = {"scope": scope, "owner_id": target_owner, "path": sp_p}
                except Exception as e:
                    res["space_save_error"] = str(e)
            return res

    def tincan_space_ls(
        self,
        scope: str = "user",
        owner_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """List files in .space VFS."""
        target_owner = owner_id or self.address
        try:
            return self._http_get(f"/api/space/ls?scope={scope}&owner_id={urllib.parse.quote(target_owner)}")
        except Exception:
            from .tincan_cli import _get_cli_space_manager
            sm = _get_cli_space_manager()
            sp = sm.get_or_create_space(scope, target_owner)
            return sp.get_summary()

    def tincan_space_write(
        self,
        path: str,
        content: str,
        scope: str = "user",
        owner_id: Optional[str] = None,
        action: str = "write",
        target: Optional[str] = None,
        replacement: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Write, patch, or delete a file in .space VFS."""
        target_owner = owner_id or self.address
        payload = {
            "path": path,
            "content": content,
            "scope": scope,
            "owner_id": target_owner,
            "action": action,
            "target": target,
            "replacement": replacement,
            "updated_by": self.address,
        }
        try:
            return self._http_post("/api/space/file", payload)
        except Exception:
            from .tincan_cli import _get_cli_space_manager
            sm = _get_cli_space_manager()
            sp = sm.get_or_create_space(scope, target_owner)
            if action == "delete":
                return sp.delete_file(path)
            elif action == "patch":
                return sp.patch_file(path, target or "", replacement or "", updated_by=self.address)
            return sp.write_file(path, content, updated_by=self.address)

    def tincan_space_exec(
        self,
        entrypoint: str = "/src/main.py",
        runtime: str = "auto",
        scope: str = "user",
        owner_id: Optional[str] = None,
        code_override: Optional[str] = None,
        args: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Execute playground code or Wasm runtime in .space VFS."""
        target_owner = owner_id or self.address
        payload = {
            "entrypoint": entrypoint,
            "runtime": runtime,
            "scope": scope,
            "owner_id": target_owner,
            "code_override": code_override,
            "args": args or [],
        }
        try:
            return self._http_post("/api/space/exec", payload)
        except Exception:
            from .tincan_cli import _get_cli_space_manager
            sm = _get_cli_space_manager()
            return sm.run_playground(
                scope=scope,
                owner_id=target_owner,
                entrypoint=entrypoint,
                runtime=runtime,
                code_override=code_override,
                args=args,
            )

    def tincan_space_agent(
        self,
        prompt: str,
        model: str = "gemini-brain",
        scope: str = "user",
        owner_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Run an autonomous agent turn inside .space VFS."""
        target_owner = owner_id or self.address
        payload = {
            "prompt": prompt,
            "model_alias": model,
            "scope": scope,
            "owner_id": target_owner,
            "author": self.address,
        }
        try:
            return self._http_post("/api/space/agent", payload)
        except Exception:
            from .tincan_cli import _get_cli_space_manager
            sm = _get_cli_space_manager()
            return sm.run_agent(
                scope=scope,
                owner_id=target_owner,
                prompt=prompt,
                model_alias=model,
                author=self.address,
            )

    def _space_notes_editor(self, scope: str, owner_id: Optional[str]):
        from .space_notes import SpaceNotesEditor, pick_router
        from .tincan_cli import _get_cli_space_manager
        sm = _get_cli_space_manager()
        vfs = sm.get_or_create_space(scope, owner_id or self.address)
        router = pick_router(getattr(sm, "ai_router", None), self.relay_url, self.address)
        return SpaceNotesEditor(vfs, ai_router=router)

    def tincan_space_note(
        self,
        body: str,
        kind: str = "observation",
        path: Optional[str] = None,
        scope: str = "user",
        owner_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Add a note for the next Apply."""
        return self._space_notes_editor(scope, owner_id).add_note(body, kind=kind, path=path, author=self.address)

    def tincan_space_notes(
        self,
        status: str = "pending",
        scope: str = "user",
        owner_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """List notes in a .space."""
        notes = self._space_notes_editor(scope, owner_id).list_notes(status=None if status == "all" else status)
        return {"notes": notes, "count": len(notes)}

    def tincan_space_apply(
        self,
        plan_id: Optional[str] = None,
        model: str = "gemini-brain",
        note_ids: Optional[List[str]] = None,
        instruction: str = "",
        scope: str = "user",
        owner_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Propose an Apply plan, or commit one when plan_id is given."""
        editor = self._space_notes_editor(scope, owner_id)
        if plan_id:
            return editor.commit(plan_id, author=self.address)
        return editor.propose(model_alias=model, note_ids=note_ids, instruction=instruction)


# -----------------------------------------------------------------------------
# Module-level tool exports & Singleton Management
# -----------------------------------------------------------------------------

_default_client: Optional[TinCanMCPClient] = None


def get_default_client() -> TinCanMCPClient:
    global _default_client
    if _default_client is None:
        _default_client = TinCanMCPClient()
    return _default_client


def set_default_client(client: TinCanMCPClient) -> None:
    global _default_client
    _default_client = client


def tincan_whoami(**kwargs) -> Dict[str, Any]:
    """Returns current local address, alias, and public key."""
    return get_default_client().tincan_whoami(**kwargs)


def tincan_send(
    recipient_address: str,
    message: str,
    speak: bool = False,
    **kwargs,
) -> Dict[str, Any]:
    """Encrypts, signs, and posts ciphertext to relay."""
    return get_default_client().tincan_send(
        recipient_address=recipient_address,
        message=message,
        speak=speak,
        **kwargs,
    )


def tincan_read(since_seq: int = 0, **kwargs) -> List[Dict[str, Any]]:
    """Fetches inbox ciphertext from relay, decrypts using local private key, verifies sender signature, returns decrypted messages."""
    return get_default_client().tincan_read(since_seq=since_seq, **kwargs)


def tincan_list_contacts(**kwargs) -> List[Dict[str, Any]]:
    """Lists trusted aliases and addresses."""
    return get_default_client().tincan_list_contacts(**kwargs)


def tincan_add_contact(alias: str, address: str, **kwargs) -> Dict[str, Any]:
    """Pins contact key."""
    return get_default_client().tincan_add_contact(alias=alias, address=address, **kwargs)


def tincan_rodin_generate(prompt: str, **kwargs) -> Dict[str, Any]:
    """Dispatches generative 3D mesh creation."""
    return get_default_client().tincan_rodin_generate(prompt=prompt, **kwargs)


def tincan_space_ls(**kwargs) -> Dict[str, Any]:
    """Lists files in .space VFS."""
    return get_default_client().tincan_space_ls(**kwargs)


def tincan_space_write(path: str, content: str, **kwargs) -> Dict[str, Any]:
    """Writes, patches, or deletes file in .space VFS."""
    return get_default_client().tincan_space_write(path=path, content=content, **kwargs)


def tincan_space_exec(entrypoint: str = "/src/main.py", **kwargs) -> Dict[str, Any]:
    """Executes playground code or Wasm runtime in .space VFS."""
    return get_default_client().tincan_space_exec(entrypoint=entrypoint, **kwargs)


def tincan_space_agent(prompt: str, **kwargs) -> Dict[str, Any]:
    """Runs autonomous agent turn in .space VFS."""
    return get_default_client().tincan_space_agent(prompt=prompt, **kwargs)


def tincan_thread_list_files(
    thread_id: str,
    peer_id: Optional[str] = None,
    subpath: str = "",
    **kwargs,
) -> Dict[str, Any]:
    from .thread_api import api_list_files

    _code, body = api_list_files(peer_id, thread_id, subpath=subpath or "")
    return body


def tincan_thread_read_file(
    thread_id: str,
    path: str,
    peer_id: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    from .thread_api import api_read_file

    _code, body = api_read_file(peer_id, thread_id, path)
    return body


def tincan_thread_write_file(
    thread_id: str,
    path: str,
    content: str,
    peer_id: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    from .thread_api import api_write_file

    _code, body = api_write_file(peer_id, thread_id, path, content)
    return body



# -----------------------------------------------------------------------------
# MCP JSON-RPC 2.0 Protocol Handler
# -----------------------------------------------------------------------------

def handle_mcp_request(
    request: Dict[str, Any],
    client: Optional[TinCanMCPClient] = None,
) -> Optional[Dict[str, Any]]:
    """Handle standard Model Context Protocol (MCP) JSON-RPC requests."""
    cl = client or get_default_client()
    req_id = request.get("id")
    method = request.get("method", "")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                },
                "serverInfo": {
                    "name": "tincan-mcp",
                    "version": "1.0.0",
                },
            },
        }

    if method == "notifications/initialized" or method == "initialized":
        return None

    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": MCP_TOOLS_DEFINITIONS,
            },
        }

    if method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        try:
            if tool_name == "tincan_whoami":
                result = cl.tincan_whoami(**arguments)
            elif tool_name == "tincan_send":
                result = cl.tincan_send(**arguments)
            elif tool_name == "tincan_read":
                result = cl.tincan_read(**arguments)
            elif tool_name == "tincan_list_contacts":
                result = cl.tincan_list_contacts(**arguments)
            elif tool_name == "tincan_add_contact":
                result = cl.tincan_add_contact(**arguments)
            elif tool_name == "tincan_rodin_generate":
                result = cl.tincan_rodin_generate(**arguments)
            elif tool_name == "tincan_space_ls":
                result = cl.tincan_space_ls(**arguments)
            elif tool_name == "tincan_space_write":
                result = cl.tincan_space_write(**arguments)
            elif tool_name == "tincan_space_exec":
                result = cl.tincan_space_exec(**arguments)
            elif tool_name == "tincan_space_agent":
                result = cl.tincan_space_agent(**arguments)
            elif tool_name == "tincan_space_note":
                result = cl.tincan_space_note(**arguments)
            elif tool_name == "tincan_space_notes":
                result = cl.tincan_space_notes(**arguments)
            elif tool_name == "tincan_space_apply":
                result = cl.tincan_space_apply(**arguments)
            elif tool_name == "tincan_thread_list_files":
                result = tincan_thread_list_files(**arguments)
            elif tool_name == "tincan_thread_read_file":
                result = tincan_thread_read_file(**arguments)
            elif tool_name == "tincan_thread_write_file":
                result = tincan_thread_write_file(**arguments)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {tool_name}",
                    },
                }

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                },
            }
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "isError": True,
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error executing {tool_name}: {exc}",
                        }
                    ],
                },
            }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": -32601,
            "message": f"Unknown MCP method: {method}",
        },
    }


def run_stdio_server(client: Optional[TinCanMCPClient] = None) -> None:
    """Run interactive MCP JSON-RPC server over stdio."""
    cl = client or get_default_client()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = handle_mcp_request(req, client=cl)
            if resp is not None:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
        except Exception as exc:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {exc}"},
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    run_stdio_server()
