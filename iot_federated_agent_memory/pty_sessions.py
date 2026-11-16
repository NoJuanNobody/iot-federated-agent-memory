"""Interactive PTY session manager for launching full-screen coding harness TUIs inside .space."""

from __future__ import annotations

import fcntl
import hashlib
import os
import pty
import shutil
import signal
import struct
import subprocess
import tempfile
import termios
import threading
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from .agent_space import (
    HARNESS_NO_SYNC_DIRS,
    WasmAndCodePlaygroundRunner,
    build_space_context_summary,
    prepare_harness_sandbox_env,
)
from .tincan_brew import (
    _can_execute_harness_locally,
    _harness_extra_env,
    codex_openrouter_flags,
    harness_base_argv,
    resolve_harness,
)


def prepare_tui_command(
    app_id: str,
    *,
    space_context_text: str = "",
) -> Tuple[List[str], Dict[str, str], str]:
    """Resolve interactive TUI argv, extra env, and canonical app id for a harness or shell."""
    clean = (app_id or "bash").strip().lower()
    if clean in ("bash", "sh", "shell", "zsh"):
        shell_bin = shutil.which("bash") or shutil.which("zsh") or shutil.which("sh") or "/bin/sh"
        flag = "-i" if os.path.basename(shell_bin) in ("bash", "zsh") else "-i"
        return [shell_bin, flag], {}, os.path.basename(shell_bin)

    target = resolve_harness(clean)
    if not target:
        raise ValueError(f"Unknown TUI harness '{app_id}'.")
    if not _can_execute_harness_locally(target):
        raise RuntimeError(
            f"{target['name']} (`{target['cli']}`) is not installed on this host. Install: {target['install_cmd']}"
        )
    if target["id"] == "gemini-cli" and not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
        raise RuntimeError(
            "Gemini CLI requires GEMINI_API_KEY (not configured on this server). Use claude, opencode, dsx, codex, or goose."
        )

    base = harness_base_argv(target)
    extra = _harness_extra_env(target)
    or_key = os.environ.get("OPENROUTER_API_KEY")

    if target["id"] == "claude-code":
        argv = [*base, "--permission-mode", "acceptEdits"]
        if or_key and not os.environ.get("ANTHROPIC_API_KEY"):
            argv.extend(["--model", os.environ.get("CLAUDE_MODEL") or "anthropic/claude-sonnet-5.5"])
        if space_context_text:
            argv.extend(["--append-system-prompt", space_context_text[:6000]])
    elif target["id"] == "opencode":
        argv = [*base]
        if or_key:
            argv.extend(["--model", os.environ.get("OPENCODE_MODEL") or "openrouter/openai/gpt-4o-mini"])
    elif target["id"] == "dsx":
        argv = [*base]
    elif target["id"] == "codex":
        argv = [*base, "--dangerously-bypass-approvals-and-sandbox"]
        if or_key and not os.environ.get("OPENAI_API_KEY"):
            argv.extend(codex_openrouter_flags())
    elif target["id"] == "goose":
        argv = [*base, "session"]
    elif target["id"] == "gemini-cli":
        argv = [*base, "--skip-trust", "--approval-mode", "yolo"]
    elif target["id"] == "aider":
        argv = [*base, "--yes-always", "--no-auto-commits", "--no-git"]
    elif target["id"] == "antigravity":
        argv = [*base, "--mode", "accept-edits"]
    else:
        argv = [*base]

    return argv, extra, target["id"]


def _set_winsize(fd: int, cols: int, rows: int) -> None:
    safe_cols = max(20, min(int(cols), 400))
    safe_rows = max(5, min(int(rows), 200))
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", safe_rows, safe_cols, 0, 0))


class PTYSession:
    """Single interactive PTY session attached to a materialized .space workspace."""

    MAX_BUFFER_BYTES = 512 * 1024

    def __init__(
        self,
        *,
        session_id: str,
        app_id: str,
        scope: str,
        owner_id: str,
        vfs: Any,
        argv: List[str],
        extra_env: Optional[Dict[str, str]] = None,
        space_context_text: str = "",
        active_file: Optional[str] = None,
        cols: int = 100,
        rows: int = 30,
    ) -> None:
        self.session_id = session_id
        self.app_id = app_id
        self.scope = scope
        self.owner_id = owner_id
        self.vfs = vfs
        self.argv = list(argv)
        self.cols = max(20, min(int(cols), 400))
        self.rows = max(5, min(int(rows), 200))
        self.created_at = time.time()
        self.last_active = self.created_at
        self.exit_code: Optional[int] = None
        self.closed = False

        self.tmpdir = tempfile.mkdtemp(prefix="tincan_pty_space_")
        self.cache_dir = tempfile.mkdtemp(prefix="tincan_pty_cache_")
        self._sync_lock = threading.Lock()
        self._io_lock = threading.Condition()
        self._buf = bytearray()
        self._base_offset = 0
        self._total_bytes = 0
        self._cleaned_up = False

        self.initial_hashes = WasmAndCodePlaygroundRunner._materialize_space(vfs, self.tmpdir)

        env = prepare_harness_sandbox_env(self.tmpdir, self.cache_dir, extra_env=extra_env)
        # Write ephemeral space & Context Palace briefing into sandbox HOME & agent instruction files without polluting .space.
        tincan_meta_dir = os.path.join(self.tmpdir, ".tincan")
        os.makedirs(tincan_meta_dir, exist_ok=True)
        ctx_file = os.path.join(tincan_meta_dir, "SPACE_CONTEXT.md")
        if space_context_text:
            with open(ctx_file, "w", encoding="utf-8") as cf:
                cf.write(space_context_text + "\n")
            dsx_home_dir = os.path.join(env["HOME"], ".dsx")
            os.makedirs(dsx_home_dir, exist_ok=True)
            with open(os.path.join(dsx_home_dir, "DSX.md"), "w", encoding="utf-8") as df:
                df.write(space_context_text + "\n")
            ctx_bytes = (space_context_text + "\n").encode("utf-8")
            for ctx_name in ("AGENTS.md", "CLAUDE.md", "GEMINI.md"):
                if ctx_name not in self.initial_hashes:
                    ctx_path = os.path.join(self.tmpdir, ctx_name)
                    with open(ctx_path, "wb") as af:
                        af.write(ctx_bytes)
                    self.initial_hashes[ctx_name] = hashlib.sha256(ctx_bytes).hexdigest()
        env["TERM"] = "xterm-256color"
        env["COLORTERM"] = "truecolor"
        env["COLUMNS"] = str(self.cols)
        env["LINES"] = str(self.rows)
        env["TINCAN_SPACE_SCOPE"] = scope
        env["TINCAN_SPACE_OWNER"] = owner_id
        if active_file:
            env["TINCAN_ACTIVE_FILE"] = active_file
        if space_context_text:
            env["TINCAN_SPACE_CONTEXT_FILE"] = ctx_file

        master_fd, slave_fd = pty.openpty()
        self.master_fd: Optional[int] = master_fd
        _set_winsize(slave_fd, self.cols, self.rows)

        def _attach_ctty() -> None:
            os.setsid()
            try:
                fcntl.ioctl(0, termios.TIOCSCTTY, 0)
            except OSError:
                pass

        try:
            self.proc = subprocess.Popen(
                self.argv,
                cwd=self.tmpdir,
                env=env,
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                close_fds=True,
                preexec_fn=_attach_ctty,
            )
        except Exception:
            os.close(slave_fd)
            os.close(master_fd)
            self.master_fd = None
            self._cleanup_dirs()
            raise
        finally:
            try:
                os.close(slave_fd)
            except OSError:
                pass

        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    def _append_output(self, chunk: bytes) -> None:
        if not chunk:
            return
        with self._io_lock:
            self._buf.extend(chunk)
            self._total_bytes += len(chunk)
            overflow = len(self._buf) - self.MAX_BUFFER_BYTES
            if overflow > 0:
                del self._buf[:overflow]
                self._base_offset += overflow
            self.last_active = time.time()
            self._io_lock.notify_all()

    def _read_loop(self) -> None:
        while True:
            fd = self.master_fd
            if fd is None:
                break
            try:
                data = os.read(fd, 8192)
            except OSError:
                break
            if not data:
                break
            self._append_output(data)

        rc = self.proc.poll()
        if rc is None:
            try:
                rc = self.proc.wait(timeout=1.0)
            except Exception:
                rc = -1
        self.exit_code = rc
        try:
            self.sync_to_space()
        except Exception:
            pass
        self._append_output(f"\r\n\x1b[90m[TinCan TUI exited ({rc}) — space synced]\x1b[0m\r\n".encode("utf-8"))
        with self._io_lock:
            self.closed = True
            self._io_lock.notify_all()

    def write(self, data: bytes) -> None:
        fd = self.master_fd
        if fd is None or self.closed or not data:
            return
        self.last_active = time.time()
        view = memoryview(data)
        sent = 0
        while sent < len(view):
            try:
                n = os.write(fd, view[sent:])
                if n <= 0:
                    break
                sent += n
            except OSError:
                break

    def resize(self, cols: int, rows: int) -> None:
        fd = self.master_fd
        if fd is None or self.closed:
            return
        self.cols = max(20, min(int(cols), 400))
        self.rows = max(5, min(int(rows), 200))
        try:
            _set_winsize(fd, self.cols, self.rows)
        except OSError:
            pass

    def read_since(self, offset: int, timeout: float = 0.25) -> Tuple[bytes, int, bool]:
        with self._io_lock:
            if offset >= self._total_bytes and not self.closed:
                self._io_lock.wait(timeout=timeout)
            eff_offset = max(offset, self._base_offset)
            rel = eff_offset - self._base_offset
            chunk = bytes(self._buf[rel:]) if rel < len(self._buf) else b""
            return chunk, self._total_bytes, self.closed

    def sync_to_space(self) -> List[str]:
        if self._cleaned_up or not os.path.isdir(self.tmpdir):
            return []
        with self._sync_lock:
            changed = WasmAndCodePlaygroundRunner._sync_space_changes(
                self.vfs,
                self.tmpdir,
                self.initial_hashes,
                no_sync_dirs=HARNESS_NO_SYNC_DIRS,
                updated_by=f"tui:{self.app_id}",
            )
            for vfs_path in changed:
                rel = vfs_path.lstrip("/")
                disk_path = os.path.join(self.tmpdir, rel)
                if os.path.isfile(disk_path):
                    with open(disk_path, "rb") as fp:
                        self.initial_hashes[rel] = hashlib.sha256(fp.read()).hexdigest()
            return changed

    def _cleanup_dirs(self) -> None:
        if self._cleaned_up:
            return
        self._cleaned_up = True
        for path in (self.tmpdir, self.cache_dir):
            shutil.rmtree(path, ignore_errors=True)

    def close(self) -> List[str]:
        synced: List[str] = []
        try:
            if self.proc.poll() is None:
                try:
                    os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
                except OSError:
                    self.proc.terminate()
                try:
                    self.proc.wait(timeout=1.5)
                except Exception:
                    try:
                        os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
                    except OSError:
                        self.proc.kill()
        except Exception:
            pass

        fd = self.master_fd
        self.master_fd = None
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass

        try:
            synced = self.sync_to_space()
        except Exception:
            pass
        with self._io_lock:
            self.closed = True
            self._io_lock.notify_all()
        self._cleanup_dirs()
        return synced

    def summary(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "app_id": self.app_id,
            "scope": self.scope,
            "owner_id": self.owner_id,
            "cols": self.cols,
            "rows": self.rows,
            "closed": self.closed,
            "exit_code": self.exit_code,
            "created_at": self.created_at,
        }


class PTYSessionManager:
    """Thread-safe registry for active browser-attached PTY TUI sessions."""

    def __init__(self, max_sessions: int = 12, idle_ttl_sec: float = 1800.0) -> None:
        self._sessions: Dict[str, PTYSession] = {}
        self._lock = threading.RLock()
        self.max_sessions = max_sessions
        self.idle_ttl_sec = idle_ttl_sec

    def _prune_stale(self) -> None:
        now = time.time()
        stale_ids = [
            sid
            for sid, sess in self._sessions.items()
            if (sess.closed and (now - sess.last_active) > 300.0)
            or ((now - sess.last_active) > self.idle_ttl_sec)
        ]
        for sid in stale_ids:
            sess = self._sessions.pop(sid, None)
            if sess is not None:
                sess.close()

    def start_session(
        self,
        app_id: str,
        *,
        scope: str,
        owner_id: str,
        vfs: Any,
        palace_snippets: Optional[List[Dict[str, Any]]] = None,
        active_file: Optional[str] = None,
        cols: int = 100,
        rows: int = 30,
        extra_env: Optional[Dict[str, str]] = None,
        ai_router: Optional[Any] = None,
    ) -> PTYSession:
        ctx = build_space_context_summary(
            vfs,
            active_file=active_file,
            palace_snippets=palace_snippets,
            ai_router=ai_router,
            include_capabilities=True,
        )
        tui_tool_guide = (
            "\n\n[Sandbox Generative Tools — Already Authenticated via TinCan Server]\n"
            "Do NOT claim you lack an API key or Rodin/image tool inside this session.\n"
            "Run these pre-installed CLI commands directly in your shell (on PATH):\n"
            "- Generate a 2D image (.png/.jpg saved into ./images/ & .space VFS):\n"
            '  tincan-gen image "a cartoon picture of spongebob"\n'
            "- Generate a 3D mesh (.glb via Hyper3D Rodin v2 saved into ./models3d/ & .space VFS):\n"
            '  tincan-gen 3d "a 3D stylized goose" --tier Regular\n'
            "- Inspect live models & Rodin billing:\n"
            "  tincan-gen models\n"
        )
        full_ctx_text = (ctx.get("text") or "") + tui_tool_guide
        argv, cmd_env, canonical_app = prepare_tui_command(
            app_id,
            space_context_text=full_ctx_text,
        )
        merged_env = dict(cmd_env)
        if extra_env:
            merged_env.update({k: v for k, v in extra_env.items() if v is not None})
        with self._lock:
            self._prune_stale()
            if len(self._sessions) >= self.max_sessions:
                oldest_sid = min(self._sessions, key=lambda k: self._sessions[k].last_active)
                oldest = self._sessions.pop(oldest_sid, None)
                if oldest is not None:
                    oldest.close()
            sid = f"pty_{uuid.uuid4().hex[:12]}"
            sess = PTYSession(
                session_id=sid,
                app_id=canonical_app,
                scope=scope,
                owner_id=owner_id,
                vfs=vfs,
                argv=argv,
                extra_env=merged_env,
                space_context_text=full_ctx_text,
                active_file=active_file,
                cols=cols,
                rows=rows,
            )
            self._sessions[sid] = sess
            return sess

    def get(self, session_id: str) -> Optional[PTYSession]:
        with self._lock:
            return self._sessions.get(session_id)

    def sync(self, session_id: str) -> List[str]:
        sess = self.get(session_id)
        if sess is None:
            raise KeyError(f"PTY session '{session_id}' not found")
        return sess.sync_to_space()

    def close(self, session_id: str) -> List[str]:
        with self._lock:
            sess = self._sessions.pop(session_id, None)
        if sess is None:
            return []
        return sess.close()

    def list_sessions(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [s.summary() for s in self._sessions.values()]
