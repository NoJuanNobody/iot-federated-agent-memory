"""
Notes -> Apply AI editor for Single-File Space VFS (*.space).

Instead of asking the model to read everything and emit one edit, work is split in two:

  1. Notes:  observations, side questions (answered by the model), code snippets,
             side runs (executed in a throwaway copy of the space) and proposed edits
             accumulate in a `space_notes` table. Each note remembers the file SHA /
             Merkle root it was written against so it can be flagged stale later.
  2. Apply:  all pending notes are compiled into one edit plan (`propose`), previewed,
             then committed (`commit`) as a new version. Every version stores the prior
             file contents so it can be reverted, and links back to the notes it consumed.

Everything lives inside the same .space SQLite container as the files themselves.
"""

import base64
import json
import os
import re
import tempfile
import time
import uuid
from typing import Any, Dict, List, Optional

from .agent_space import SingleFileSpaceVFS, WasmAndCodePlaygroundRunner

NOTE_KINDS = ("observation", "question", "code", "result", "edit")
NOTE_STATUSES = ("pending", "applied", "dropped")

# Context budget for the apply prompt (bytes of file text sent to the model)
MAX_CONTEXT_BYTES = 60_000
MAX_FILE_BYTES = 20_000


class EditPlanError(ValueError):
    """Raised when the model's edit plan is missing, malformed, or cannot be committed."""


def _extract_json_object(text: str) -> Dict[str, Any]:
    """Pull the first JSON object out of a model reply (tolerates ```json fences and prose)."""
    if not text:
        raise EditPlanError("Model returned an empty reply")
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise EditPlanError(f"Model reply contains no JSON edit plan: {text[:200]!r}")
        candidate = text[start:end + 1]
    try:
        obj = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise EditPlanError(f"Model edit plan is not valid JSON: {exc}") from exc
    if not isinstance(obj, dict):
        raise EditPlanError("Model edit plan must be a JSON object")
    return obj


class RelayChatRouter:
    """Routes completions through a TinCan relay's pooled /api/chat gateway (same path as `tincan ask`)."""

    def __init__(self, relay_url: str, peer_id: str = "peer", timeout_sec: float = 120.0):
        self.relay_url = relay_url.rstrip("/")
        self.peer_id = peer_id
        self.timeout_sec = timeout_sec

    def dispatch_completion(
        self,
        alias: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> Dict[str, Any]:
        import urllib.request

        payload = {
            "model": alias,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "peer_id": self.peer_id,
        }
        req = urllib.request.Request(
            f"{self.relay_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("error"):
            raise EditPlanError(f"Relay gateway error: {data['error']}")
        return data


def pick_router(local_router: Optional[Any], relay_url: Optional[str], peer_id: str) -> Optional[Any]:
    """Use the local gateway when it has an OpenRouter or NanoGPT key, else the relay's pooled gateway."""
    if local_router is not None and (
        getattr(local_router, "openrouter_key", None) or getattr(local_router, "nanogpt_key", None)
    ):
        return local_router
    if os.environ.get("OPENROUTER_API_KEY") or os.environ.get("NANOGPT_API_KEY") or not relay_url:
        return local_router
    return RelayChatRouter(relay_url, peer_id=peer_id)


class SpaceNotesEditor:
    """Notes -> Apply editor bound to one .space VFS."""

    def __init__(
        self,
        vfs: SingleFileSpaceVFS,
        ai_router: Optional[Any] = None,
        runner: Optional[WasmAndCodePlaygroundRunner] = None,
    ):
        self.vfs = vfs
        self._ai_router = ai_router
        self.runner = runner or WasmAndCodePlaygroundRunner()
        self._init_tables()

    @property
    def ai_router(self) -> Any:
        if self._ai_router is None:
            from .ai_gateway import DynamicAIGatewayRouter
            self._ai_router = DynamicAIGatewayRouter()
        return self._ai_router

    def _init_tables(self) -> None:
        with self.vfs._lock, self.vfs._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS space_notes (
                    note_id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    body TEXT NOT NULL,
                    path TEXT,
                    author TEXT,
                    base_sha TEXT,
                    base_merkle TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    version_id TEXT,
                    created_at REAL
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS space_apply_plans (
                    plan_id TEXT PRIMARY KEY,
                    base_merkle TEXT NOT NULL,
                    note_ids_json TEXT NOT NULL,
                    plan_json TEXT NOT NULL,
                    model_alias TEXT,
                    status TEXT NOT NULL DEFAULT 'proposed',
                    created_at REAL
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS space_versions (
                    version_id TEXT PRIMARY KEY,
                    plan_id TEXT,
                    parent_merkle TEXT,
                    merkle_root TEXT,
                    summary TEXT,
                    note_ids_json TEXT,
                    files_changed_json TEXT,
                    before_json TEXT,
                    reverted INTEGER NOT NULL DEFAULT 0,
                    created_at REAL
                );
                """
            )

    # ------------------------------------------------------------------
    # Notes
    # ------------------------------------------------------------------

    def _file_sha(self, path: Optional[str]) -> Optional[str]:
        if not path:
            return None
        norm = self.vfs.normalize_path(path)
        for f in self.vfs.list_files():
            if f["path"] == norm:
                return f["sha256"]
        return None

    def add_note(
        self,
        body: str,
        kind: str = "observation",
        path: Optional[str] = None,
        author: str = "user",
    ) -> Dict[str, Any]:
        """Record a note against the current version of the space (and of `path`, if given)."""
        kind = (kind or "observation").lower().strip()
        if kind not in NOTE_KINDS:
            raise ValueError(f"Unknown note kind '{kind}'. Expected one of: {', '.join(NOTE_KINDS)}")
        if not body or not body.strip():
            raise ValueError("Note body cannot be empty")
        norm_path = self.vfs.normalize_path(path) if path else None
        note = {
            "note_id": f"note_{uuid.uuid4().hex[:10]}",
            "kind": kind,
            "body": body.strip(),
            "path": norm_path,
            "author": author,
            "base_sha": self._file_sha(norm_path),
            "base_merkle": self.vfs.compute_merkle_root(),
            "status": "pending",
            "version_id": None,
            "created_at": time.time(),
        }
        with self.vfs._lock, self.vfs._connect() as conn:
            conn.execute(
                """
                INSERT INTO space_notes (note_id, kind, body, path, author, base_sha, base_merkle, status, version_id, created_at)
                VALUES (:note_id, :kind, :body, :path, :author, :base_sha, :base_merkle, :status, :version_id, :created_at)
                """,
                note,
            )
        return note

    def list_notes(self, status: Optional[str] = "pending") -> List[Dict[str, Any]]:
        """List notes (oldest first), annotated with whether they are stale against the current files."""
        query = "SELECT * FROM space_notes"
        params: tuple = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY created_at ASC"
        with self.vfs._lock, self.vfs._connect() as conn:
            rows = [dict(r) for r in conn.execute(query, params).fetchall()]

        current_merkle = self.vfs.compute_merkle_root()
        shas = {f["path"]: f["sha256"] for f in self.vfs.list_files()}
        for note in rows:
            if note["status"] != "pending":
                note["stale"] = False
            elif note["path"]:
                note["stale"] = shas.get(note["path"]) != note["base_sha"]
            else:
                note["stale"] = note["base_merkle"] != current_merkle
        return rows

    def drop_note(self, note_id: str) -> Dict[str, Any]:
        """Discard a pending note so Apply ignores it."""
        with self.vfs._lock, self.vfs._connect() as conn:
            cur = conn.execute(
                "UPDATE space_notes SET status = 'dropped' WHERE note_id = ? AND status = 'pending'",
                (note_id,),
            )
            if cur.rowcount == 0:
                raise KeyError(f"No pending note with id {note_id}")
        return {"dropped": True, "note_id": note_id}

    # ------------------------------------------------------------------
    # Side work that produces notes
    # ------------------------------------------------------------------

    def _complete(self, messages: List[Dict[str, str]], model_alias: str, max_tokens: int) -> str:
        res = self.ai_router.dispatch_completion(
            alias=model_alias, messages=messages, temperature=0.2, max_tokens=max_tokens
        )
        choices = res.get("choices") or []
        return (choices[0].get("message", {}).get("content", "") if choices else "") or ""

    def ask(
        self,
        question: str,
        path: Optional[str] = None,
        model_alias: str = "gemini-brain",
        author: str = "user",
    ) -> Dict[str, Any]:
        """Ask a side question about the space. The answer is stored as a `question` note; no files change."""
        context = self._build_file_context(focus_paths=[path] if path else [])
        messages = [
            {
                "role": "system",
                "content": (
                    "You are answering a side question about a project. Answer concisely and concretely. "
                    "Do not propose a full rewrite; your answer becomes a note that a later edit step will use.\n\n"
                    f"{context}"
                ),
            },
            {"role": "user", "content": question},
        ]
        answer = self._complete(messages, model_alias, max_tokens=1024).strip()
        note = self.add_note(f"Q: {question.strip()}\nA: {answer}", kind="question", path=path, author=author)
        return {"answer": answer, "note": note}

    def side_run(
        self,
        entrypoint: Optional[str] = None,
        code: Optional[str] = None,
        runtime: str = "auto",
        author: str = "user",
    ) -> Dict[str, Any]:
        """Execute code against a throwaway copy of the space and record the output as a `result` note.

        Inline `code` without an explicit entrypoint runs from its own scratch file, so it can read
        the space's files without overwriting any of them.
        """
        if entrypoint is None:
            if code is None:
                entrypoint = "/src/main.py"
            else:
                ext = {"node": ".js", "sh": ".sh"}.get(runtime, ".py")
                entrypoint = f"/.side/run_{uuid.uuid4().hex[:8]}{ext}"
        with tempfile.TemporaryDirectory(prefix="space_side_run_") as tmpdir:
            scratch_path = os.path.join(tmpdir, "scratch.space")
            with open(scratch_path, "wb") as f:
                f.write(self.vfs.export_space_bytes())
            scratch = SingleFileSpaceVFS(scope=self.vfs.scope, owner_id=self.vfs.owner_id, space_path=scratch_path)
            run = self.runner.execute(scratch, entrypoint=entrypoint, runtime=runtime, code_override=code)

        lines = [f"Side run of {run['entrypoint']} ({run['runtime']}) exited {run['exit_code']}."]
        if code is not None:
            lines.append(f"Code:\n{code.strip()}")
        if run.get("stdout"):
            lines.append(f"stdout:\n{run['stdout'].strip()[:4000]}")
        if run.get("stderr"):
            lines.append(f"stderr:\n{run['stderr'].strip()[:4000]}")
        if code is not None and run["entrypoint"].startswith("/.side/"):
            lines[0] = f"Side run of inline {run['runtime']} code exited {run['exit_code']}."
        note = self.add_note("\n".join(lines), kind="result", path=run["entrypoint"] if code is None else None, author=author)
        return {"run": run, "note": note}

    # ------------------------------------------------------------------
    # Apply: propose -> commit -> (revert)
    # ------------------------------------------------------------------

    def _build_file_context(self, focus_paths: List[str]) -> str:
        """Render current file contents for the model, focus paths first, within a byte budget."""
        files = self.vfs.list_files()
        focus = {self.vfs.normalize_path(p) for p in focus_paths if p}
        ordered = sorted(files, key=lambda f: (f["path"] not in focus, f["path"]))
        parts = [f"Space {self.vfs.scope}:{self.vfs.owner_id} has {len(files)} files."]
        budget = MAX_CONTEXT_BYTES
        for f in ordered:
            rec = self.vfs.read_file(f["path"], as_text=True)
            text = rec.get("content") if f["size_bytes"] else ""
            if text is None or f["size_bytes"] > MAX_FILE_BYTES or len(text) > budget:
                parts.append(f"--- {f['path']} ({f['size_bytes']} bytes, {f['mime_type']}; contents omitted) ---")
                continue
            budget -= len(text)
            parts.append(f"--- {f['path']} ---\n{text}")
        return "\n\n".join(parts)

    def propose(
        self,
        model_alias: str = "gemini-brain",
        note_ids: Optional[List[str]] = None,
        instruction: str = "",
    ) -> Dict[str, Any]:
        """Compile pending notes into an edit plan. Nothing changes until `commit(plan_id)`."""
        notes = self.list_notes(status="pending")
        if note_ids:
            wanted = set(note_ids)
            notes = [n for n in notes if n["note_id"] in wanted]
        if not notes:
            raise EditPlanError("No pending notes to apply")

        note_lines = []
        for n in notes:
            header = f"[{n['note_id']}] kind={n['kind']}"
            if n["path"]:
                header += f" path={n['path']}"
            if n["stale"]:
                header += " STALE (written against an older version; re-validate before using)"
            note_lines.append(f"{header}\n{n['body']}")

        system = (
            "You are the Apply step of a notes-based editor. The user and side agents collected the notes below "
            "while exploring. Produce ONE coherent new version of the files that incorporates them.\n"
            "Rules:\n"
            "- Respond with a single JSON object and nothing else.\n"
            '- Shape: {"summary": str, "edits": [{"path": str, "op": "write"|"patch"|"delete", '
            '"content": str (write), "target": str, "replacement": str (patch)}], '
            '"skipped": [{"note_id": str, "reason": str}], "conflicts": [str]}\n'
            "- Prefer `patch` with an exact, unique `target` substring for small changes; `write` the full file otherwise.\n"
            "- If notes contradict each other, pick the most recent unless an earlier note is clearly more correct, "
            "and describe the conflict in `conflicts`.\n"
            "- Skip notes that are stale and no longer apply, or that are questions with no actionable change.\n\n"
            f"Current files:\n{self._build_file_context([n['path'] for n in notes if n['path']])}"
        )
        user = "Notes to apply:\n\n" + "\n\n".join(note_lines)
        if instruction.strip():
            user += f"\n\nAdditional instruction: {instruction.strip()}"

        reply = self._complete(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            model_alias,
            max_tokens=8192,
        )
        plan = self._validate_plan(_extract_json_object(reply))

        plan_id = f"plan_{uuid.uuid4().hex[:10]}"
        base_merkle = self.vfs.compute_merkle_root()
        used_ids = [n["note_id"] for n in notes]
        with self.vfs._lock, self.vfs._connect() as conn:
            conn.execute(
                """
                INSERT INTO space_apply_plans (plan_id, base_merkle, note_ids_json, plan_json, model_alias, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'proposed', ?)
                """,
                (plan_id, base_merkle, json.dumps(used_ids), json.dumps(plan), model_alias, time.time()),
            )
        return {"plan_id": plan_id, "base_merkle": base_merkle, "note_ids": used_ids, **plan}

    def _validate_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        edits = plan.get("edits")
        if not isinstance(edits, list):
            raise EditPlanError("Edit plan is missing an `edits` list")
        clean_edits = []
        for i, e in enumerate(edits):
            if not isinstance(e, dict) or not e.get("path"):
                raise EditPlanError(f"Edit #{i} has no path")
            op = e.get("op", "write")
            path = self.vfs.normalize_path(e["path"])
            if op == "write":
                if not isinstance(e.get("content"), str):
                    raise EditPlanError(f"Edit #{i} ({path}) is a write without string content")
                clean_edits.append({"path": path, "op": op, "content": e["content"]})
            elif op == "patch":
                if not isinstance(e.get("target"), str) or not isinstance(e.get("replacement"), str) or not e["target"]:
                    raise EditPlanError(f"Edit #{i} ({path}) is a patch without target/replacement")
                clean_edits.append({"path": path, "op": op, "target": e["target"], "replacement": e["replacement"]})
            elif op == "delete":
                clean_edits.append({"path": path, "op": op})
            else:
                raise EditPlanError(f"Edit #{i} ({path}) has unknown op '{op}'")
        return {
            "summary": str(plan.get("summary", "")).strip(),
            "edits": clean_edits,
            "skipped": plan.get("skipped") or [],
            "conflicts": plan.get("conflicts") or [],
        }

    def get_plan(self, plan_id: str) -> Dict[str, Any]:
        with self.vfs._lock, self.vfs._connect() as conn:
            row = conn.execute("SELECT * FROM space_apply_plans WHERE plan_id = ?", (plan_id,)).fetchone()
        if not row:
            raise KeyError(f"No plan with id {plan_id}")
        return {
            "plan_id": row["plan_id"],
            "base_merkle": row["base_merkle"],
            "note_ids": json.loads(row["note_ids_json"]),
            "model_alias": row["model_alias"],
            "status": row["status"],
            "created_at": row["created_at"],
            **json.loads(row["plan_json"]),
        }

    def commit(self, plan_id: str, author: str = "notes-editor") -> Dict[str, Any]:
        """Apply a proposed plan as a new version. Refuses if the files changed since the plan was made."""
        plan = self.get_plan(plan_id)
        if plan["status"] != "proposed":
            raise EditPlanError(f"Plan {plan_id} is already {plan['status']}")
        parent_merkle = self.vfs.compute_merkle_root()
        if parent_merkle != plan["base_merkle"]:
            raise EditPlanError(
                f"Space changed since {plan_id} was proposed; run apply again to re-plan against the current files"
            )

        # Pre-check every patch target before mutating anything, so a bad plan changes nothing.
        before: Dict[str, Optional[str]] = {}
        for e in plan["edits"]:
            if e["path"] in before:
                continue
            try:
                rec = self.vfs.read_file(e["path"], as_text=False)
                before[e["path"]] = rec["content_b64"]
            except FileNotFoundError:
                before[e["path"]] = None
        simulated: Dict[str, Optional[str]] = {}
        for p, b in before.items():
            if not any(e["path"] == p and e["op"] == "patch" for e in plan["edits"]):
                continue
            try:
                simulated[p] = base64.b64decode(b).decode("utf-8") if b is not None else None
            except UnicodeDecodeError as exc:
                raise EditPlanError(f"Cannot patch binary file: {p}") from exc
        for e in plan["edits"]:
            if e["op"] == "write":
                simulated[e["path"]] = e["content"]
            elif e["op"] == "delete":
                simulated[e["path"]] = None
            else:
                current = simulated.get(e["path"])
                if current is None:
                    raise EditPlanError(f"Patch target file does not exist: {e['path']}")
                if current.count(e["target"]) != 1:
                    raise EditPlanError(f"Patch target is missing or not unique in {e['path']}")
                simulated[e["path"]] = current.replace(e["target"], e["replacement"], 1)

        self.vfs.create_snapshot(label=f"pre-{plan_id}")
        files_changed = []
        for path in before:
            final = simulated.get(path)
            if final is None:
                if before[path] is not None:
                    self.vfs.delete_file(path)
                    files_changed.append({"path": path, "op": "delete"})
            elif before[path] is None or base64.b64decode(before[path]) != final.encode("utf-8"):
                self.vfs.write_file(path, final, updated_by=author)
                files_changed.append({"path": path, "op": "create" if before[path] is None else "update"})

        merkle_root = self.vfs.compute_merkle_root()
        version_id = f"ver_{uuid.uuid4().hex[:10]}"
        snapshot = self.vfs.create_snapshot(label=version_id)
        with self.vfs._lock, self.vfs._connect() as conn:
            conn.execute(
                """
                INSERT INTO space_versions (version_id, plan_id, parent_merkle, merkle_root, summary, note_ids_json,
                                            files_changed_json, before_json, reverted, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                """,
                (
                    version_id,
                    plan_id,
                    parent_merkle,
                    merkle_root,
                    plan["summary"],
                    json.dumps(plan["note_ids"]),
                    json.dumps(files_changed),
                    json.dumps(before),
                    time.time(),
                ),
            )
            conn.execute("UPDATE space_apply_plans SET status = 'committed' WHERE plan_id = ?", (plan_id,))
            skipped = {s.get("note_id") for s in plan["skipped"] if isinstance(s, dict)}
            for note_id in plan["note_ids"]:
                if note_id not in skipped:
                    conn.execute(
                        "UPDATE space_notes SET status = 'applied', version_id = ? WHERE note_id = ? AND status = 'pending'",
                        (version_id, note_id),
                    )
        return {
            "version_id": version_id,
            "plan_id": plan_id,
            "summary": plan["summary"],
            "files_changed": files_changed,
            "parent_merkle": parent_merkle,
            "merkle_root": merkle_root,
            "snapshot_id": snapshot["snapshot_id"],
            "notes_applied": [n for n in plan["note_ids"] if n not in skipped],
            "notes_left_pending": sorted(n for n in skipped if n),
        }

    def apply(self, model_alias: str = "gemini-brain", note_ids: Optional[List[str]] = None, instruction: str = "") -> Dict[str, Any]:
        """Propose and immediately commit (the one-click path)."""
        plan = self.propose(model_alias=model_alias, note_ids=note_ids, instruction=instruction)
        return {"plan": plan, **self.commit(plan["plan_id"])}

    def list_versions(self) -> List[Dict[str, Any]]:
        with self.vfs._lock, self.vfs._connect() as conn:
            rows = conn.execute(
                "SELECT version_id, plan_id, parent_merkle, merkle_root, summary, note_ids_json, files_changed_json, reverted, created_at "
                "FROM space_versions ORDER BY created_at DESC"
            ).fetchall()
        return [
            {
                "version_id": r["version_id"],
                "plan_id": r["plan_id"],
                "parent_merkle": r["parent_merkle"],
                "merkle_root": r["merkle_root"],
                "summary": r["summary"],
                "note_ids": json.loads(r["note_ids_json"] or "[]"),
                "files_changed": json.loads(r["files_changed_json"] or "[]"),
                "reverted": bool(r["reverted"]),
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    def revert(self, version_id: str, author: str = "notes-editor") -> Dict[str, Any]:
        """Undo a version, if it is still the current state of the space. Its notes go back to pending."""
        with self.vfs._lock, self.vfs._connect() as conn:
            row = conn.execute("SELECT * FROM space_versions WHERE version_id = ?", (version_id,)).fetchone()
        if not row:
            raise KeyError(f"No version with id {version_id}")
        if row["reverted"]:
            raise EditPlanError(f"Version {version_id} is already reverted")
        if self.vfs.compute_merkle_root() != row["merkle_root"]:
            raise EditPlanError(f"Space changed after {version_id}; only the current version can be reverted")

        before = json.loads(row["before_json"] or "{}")
        for path, content_b64 in before.items():
            if content_b64 is None:
                try:
                    self.vfs.delete_file(path)
                except FileNotFoundError:
                    pass
            else:
                self.vfs.write_file(path, base64.b64decode(content_b64), updated_by=author)

        with self.vfs._lock, self.vfs._connect() as conn:
            conn.execute("UPDATE space_versions SET reverted = 1 WHERE version_id = ?", (version_id,))
            conn.execute(
                "UPDATE space_notes SET status = 'pending', version_id = NULL WHERE version_id = ?",
                (version_id,),
            )
        return {"reverted": True, "version_id": version_id, "merkle_root": self.vfs.compute_merkle_root()}
