"""TinCan Mesh OS Interactive Terminal Shell (TUI) for iot-federated-agent-memory.

Brings the Mesh OS web app's functionality directly into the terminal in the
DESIGN.md Ink & Paper palette (sumi, washi, persimmon):

* [1] Overview    - local/relay status, Ed25519 identity, readiness, peers & AI credits
* [2] Apps (18)   - every Cmd-K launcher window from /windows; Enter/o opens it locally
* [3] Board       - live Cyberspace Discussion Board topics (/api/board/topics)
* [4] Workstation - live .space & local node workspace files (/api/workstation/status)
* [5] Quests      - live mesh XP tier & leaderboard (/api/mesh/leaderboard)
* [6] Screensaver - animated AI Messiah logo + live mesh status

Press `/` or `Ctrl+K` at any time for the interactive Universal Command Bar
(fuzzy search over all 18 apps + slash commands). Pure standard library
(termios/select), macOS + Linux, zero mocks.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import select
import shutil
import signal
import sys
import threading
import time
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from .ansi import RGB, Canvas, detect_color_mode
from .logo import LogoImage, draw_title, title_width
from .os_launcher import (
    LocalNodeManager,
    WINDOW_CATALOG,
    launch_browser_window,
    resolve_window_entry,
)

DEFAULT_RELAY = os.environ.get("IOT_MESH_RELAY", "https://iot-federated-agent-memory-production.up.railway.app")

# DESIGN.md Ink & Paper palette (Sumi / Washi / Persimmon)
SUMI: RGB = (14, 13, 11)
SUMI_SOFT: RGB = (23, 21, 15)
WASHI: RGB = (236, 230, 218)
WASHI_QUIET: RGB = (165, 160, 150)
WASHI_DIM: RGB = (128, 123, 115)
WASHI_LINE: RGB = (58, 54, 48)
PERSIMMON: RGB = (208, 112, 63)

# Legacy palette aliases kept for Screensaver artwork harmony
BG_DEEP: RGB = SUMI
PURPLE: RGB = (150, 70, 200)
PURPLE_DIM: RGB = (70, 30, 100)
GOLD: RGB = PERSIMMON
GOLD_DIM: RGB = (150, 82, 46)
GREEN: RGB = (110, 210, 130)
RED: RGB = (230, 95, 85)
WHITE: RGB = WASHI
GREY: RGB = WASHI_QUIET
HEADER_BG: RGB = SUMI_SOFT

TABS: List[Tuple[str, str]] = [
    ("overview", "1 Overview"),
    ("apps", "2 Apps"),
    ("board", "3 Board"),
    ("workstation", "4 Workstation"),
    ("quests", "5 Quests"),
    ("screensaver", "6 Screensaver"),
]


def _resolve_initial_base_url(relay_arg: str) -> Tuple[str, bool]:
    """Prefer a running local TinCan OS node on 127.0.0.1; fall back to relay."""
    try:
        mgr = LocalNodeManager()
        st = mgr.status()
        if st.get("running") and st.get("url"):
            return str(st["url"]).rstrip("/"), True
    except Exception:
        pass
    return relay_arg.rstrip("/"), False


def _fetch_json(url: str, timeout: float = 4.0) -> Optional[Any]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "tincan-tui/2.2", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    return None


# --------------------------------------------------------------------------- status poller

class StatusPoller(threading.Thread):
    """Polls <base>/api/status, /windows, /api/board/topics, /api/workstation/status,
    /api/mesh/leaderboard, and /api/local/identity in the background."""

    def __init__(self, relay: str, interval: float = 10.0) -> None:
        super().__init__(daemon=True)
        self.relay = relay.rstrip("/")
        self.interval = interval
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self._state: Dict[str, Any] = {
            "data": None,
            "windows": list(WINDOW_CATALOG),
            "topics": [],
            "workstation": None,
            "leaderboard": [],
            "tier": None,
            "local_identity": None,
            "error": None,
            "updated_at": None,
            "fetching": True,
        }

    def run(self) -> None:
        while True:
            self._fetch()
            self._wake.wait(self.interval)
            self._wake.clear()

    def refresh(self) -> None:
        self._wake.set()

    def _fetch(self) -> None:
        with self._lock:
            self._state["fetching"] = True
        try:
            req = urllib.request.Request(self.relay + "/api/status", headers={"User-Agent": "tincan-tui/2.2"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            win_resp = _fetch_json(self.relay + "/windows", timeout=2.5)
            board_resp = _fetch_json(self.relay + "/api/board/topics?limit=25", timeout=2.5)
            ws_resp = _fetch_json(self.relay + "/api/workstation/status", timeout=2.5)
            lb_resp = _fetch_json(self.relay + "/api/mesh/leaderboard", timeout=2.5)
            id_resp = _fetch_json(self.relay + "/api/local/identity", timeout=2.0)

            topics: List[Dict[str, Any]] = []
            if isinstance(board_resp, dict):
                topics = list(board_resp.get("topics") or board_resp.get("items") or [])
            elif isinstance(board_resp, list):
                topics = list(board_resp)

            windows = list(win_resp.get("windows") or WINDOW_CATALOG) if isinstance(win_resp, dict) else list(WINDOW_CATALOG)
            leaderboard = list(lb_resp.get("leaderboard") or []) if isinstance(lb_resp, dict) else []
            tier = lb_resp.get("tier") if isinstance(lb_resp, dict) else None

            with self._lock:
                self._state.update(
                    data=data,
                    windows=windows,
                    topics=topics,
                    workstation=ws_resp if isinstance(ws_resp, dict) else None,
                    leaderboard=leaderboard,
                    tier=tier,
                    local_identity=id_resp if isinstance(id_resp, dict) else None,
                    error=None,
                    updated_at=time.time(),
                    fetching=False,
                )
        except Exception as exc:
            with self._lock:
                self._state.update(error=str(exc)[:160], updated_at=time.time(), fetching=False)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._state)


def status_summary(snap: Dict[str, Any], is_local: bool = False) -> Tuple[str, RGB]:
    prefix = "local node" if is_local else "relay"
    if snap.get("data") and not snap.get("error"):
        d = snap["data"]
        peers = len(d.get("active_webrtc_streams") or d.get("connected_peers") or [])
        provs = len(d.get("ai_providers") or {})
        return "%s online \u00b7 %d peers \u00b7 %d providers" % (prefix, peers, provs), GREEN
    if snap.get("error"):
        return f"{prefix} offline", RED
    return f"connecting to {prefix}\u2026", PERSIMMON


# --------------------------------------------------------------------------- screensaver

RAIN_CHARS = "01\u2502\u2524\u251c\u2500\u253c\u00b7"


class Screensaver:
    def __init__(self) -> None:
        self.size: Tuple[int, int] = (0, 0)
        self.logo: Optional[LogoImage] = None
        self.drops: List[float] = []
        self.speeds: List[float] = []
        self.twinkles: List[List[float]] = []

    def _layout(self, cols: int, rows: int) -> None:
        self.size = (cols, rows)
        self.logo = LogoImage.fit(cols - 4, rows - 8) if cols >= 24 and rows >= 14 else None
        self.drops = [random.uniform(-rows, rows) for _ in range(cols)]
        self.speeds = [random.uniform(0.25, 0.9) if random.random() < 0.45 else 0.0 for _ in range(cols)]
        self.twinkles = []

    def draw(self, canvas: Canvas, t: float, snap: Dict[str, Any], hint: str, animate: bool = True) -> None:
        cols, rows = canvas.cols, canvas.rows
        if (cols, rows) != self.size:
            self._layout(cols, rows)

        for x in range(cols):
            speed = self.speeds[x]
            if speed == 0.0:
                continue
            head = self.drops[x]
            for tail in range(10):
                y = int(head) - tail
                if 0 <= y < rows:
                    fade = 1.0 - tail / 10.0
                    color = PERSIMMON if tail == 0 else tuple(
                        int(WASHI_LINE[i] + (WASHI_QUIET[i] - WASHI_LINE[i]) * fade) for i in range(3)
                    )
                    canvas.put(
                        x, y,
                        random.choice(RAIN_CHARS) if tail < 2 else RAIN_CHARS[(x + y) % len(RAIN_CHARS)],
                        color, BG_DEEP,
                    )
            if animate:
                self.drops[x] += speed
                if head - 10 > rows:
                    self.drops[x] = random.uniform(-rows * 0.5, 0)

        if animate and random.random() < 0.25:
            self.twinkles.append([random.randrange(cols), random.randrange(rows), t])
        self.twinkles = [tw for tw in self.twinkles if t - tw[2] < 1.2]
        for x, y, born in self.twinkles:
            age = (t - born) / 1.2
            canvas.put(int(x), int(y), "+" if 0.25 < age < 0.75 else "\u00b7", PERSIMMON if age < 0.6 else WASHI_DIM, BG_DEEP)

        title = "TINCAN MESH OS"
        block_h = (self.logo.cell_rows if self.logo else 0) + 5
        top = max(1, (rows - block_h) // 2)
        if self.logo:
            lx = (cols - self.logo.width) // 2
            canvas.fill(lx - 1, top - 1, lx + self.logo.width + 1, top + self.logo.cell_rows + 1, BG_DEEP)
            self.logo.draw(canvas, lx, top, t if animate else None)
            top += self.logo.cell_rows + 1
        tw = title_width(title)
        canvas.fill(0, top, cols, top + 4, BG_DEEP)
        if tw <= cols - 2:
            draw_title(canvas, (cols - tw) // 2, top, title)
            sub_y = top + 3
        else:
            plain = "T I N C A N   M E S H   O S"
            canvas.text(max(0, (cols - len(plain)) // 2), top, plain, WASHI, BG_DEEP)
            sub_y = top + 1
        sub = "I N K   &   P A P E R   T E R M I N A L"
        canvas.text(max(0, (cols - len(sub)) // 2), sub_y, sub, WASHI_QUIET, BG_DEEP)

        canvas.fill(0, 0, cols, 1, BG_DEEP)
        canvas.text(1, 0, "TINCAN \u00b7 FEDERATED MESH OS", WASHI_QUIET, BG_DEEP)
        label, color = status_summary(snap)
        canvas.text(max(0, cols - len(label) - 3), 0, "\u25cf " + label, color, BG_DEEP)
        canvas.fill(0, rows - 1, cols, rows, BG_DEEP)
        canvas.text(max(0, (cols - len(hint)) // 2), rows - 1, hint, WASHI_QUIET, BG_DEEP)


# --------------------------------------------------------------------------- dashboard / tabs

def _bar(value: float, maximum: float, width: int) -> str:
    if maximum <= 0 or width <= 0:
        return ""
    frac = max(0.0, min(1.0, value / maximum))
    full = int(frac * width)
    partial = " \u258f\u258e\u258d\u258c\u258b\u258a\u2589"[int((frac * width - full) * 8)]
    return ("\u2588" * full + (partial if full < width else "")).ljust(width)


class Dashboard:
    """Multi-tab TinCan Mesh OS terminal UI."""

    def __init__(self) -> None:
        self.size: Tuple[int, int] = (0, 0)
        self.logo: Optional[LogoImage] = None

    def _draw_header(
        self,
        canvas: Canvas,
        snap: Dict[str, Any],
        relay: str,
        is_local: bool,
        active_tab: str,
    ) -> None:
        cols = canvas.cols
        canvas.fill(0, 0, cols, 1, HEADER_BG)
        canvas.text(1, 0, "\u25cb", PERSIMMON, HEADER_BG)
        canvas.text(3, 0, "TinCan Mesh OS", WASHI, HEADER_BG)
        mode_tag = "LOCAL NODE" if is_local else "RELAY"
        canvas.text(19, 0, f"[{mode_tag}]", PERSIMMON if is_local else WASHI_QUIET, HEADER_BG)
        label, color = status_summary(snap, is_local=is_local)
        canvas.text(max(0, cols - len(label) - 3), 0, "\u25cf " + label, color, HEADER_BG)

        # Tab bar on row 1
        canvas.fill(0, 1, cols, 2, SUMI)
        tx = 1
        for key, title in TABS:
            is_cur = key == active_tab
            fg = WASHI if is_cur else WASHI_DIM
            bg = SUMI_SOFT if is_cur else SUMI
            marker = "\u2022 " if is_cur else "  "
            pill = f"{marker}{title} "
            if tx + len(pill) < cols - 1:
                canvas.text(tx, 1, pill, fg, bg)
                if is_cur:
                    canvas.text(tx, 1, "\u2022", PERSIMMON, bg)
            tx += len(pill) + 1
        # Endpoint hint on right of row 1
        ep = relay[: max(0, cols - tx - 2)]
        if ep and tx + len(ep) + 1 < cols:
            canvas.text(cols - len(ep) - 1, 1, ep, WASHI_DIM, SUMI)
        # Hairline divider on row 2
        canvas.text(0, 2, "\u2500" * cols, WASHI_LINE, SUMI)

    def _draw_footer(self, canvas: Canvas, status_msg: str, idle_left: Optional[float]) -> None:
        cols, rows = canvas.cols, canvas.rows
        canvas.fill(0, rows - 1, cols, rows, HEADER_BG)
        if status_msg:
            canvas.text(1, rows - 1, status_msg[: max(0, cols - 2)], PERSIMMON, HEADER_BG)
            return
        footer = " [1-6] tabs   [/] cmd bar   [j/k] move   [Enter/o] open window   [r] refresh   [q] quit"
        if idle_left is not None:
            footer += "   \u00b7 saver %ds" % max(0, int(idle_left))
        canvas.text(0, rows - 1, footer[:cols], WASHI_QUIET, HEADER_BG)

    def _section(self, canvas: Canvas, x0: int, y: int, width: int, title: str) -> int:
        if y >= canvas.rows - 2:
            return y
        canvas.text(x0, y, title, WASHI)
        line_len = max(0, width - len(title) - 1)
        if line_len > 0:
            canvas.text(x0 + len(title) + 1, y, "\u2500" * line_len, WASHI_LINE)
        return y + 1

    def draw(
        self,
        canvas: Canvas,
        t: float,
        snap: Dict[str, Any],
        relay: str,
        idle_left: Optional[float],
        active_tab: str = "overview",
        selected_idx: int = 0,
        is_local: bool = False,
        status_msg: str = "",
        cmd_open: bool = False,
        cmd_query: str = "",
        cmd_items: Optional[List[Dict[str, Any]]] = None,
        cmd_sel: int = 0,
    ) -> None:
        cols, rows = canvas.cols, canvas.rows
        if (cols, rows) != self.size:
            self.size = (cols, rows)
            lw = min(30, cols // 3)
            self.logo = LogoImage.fit(lw, rows - 7) if cols >= 84 and rows >= 18 else None

        self._draw_header(canvas, snap, relay, is_local, active_tab)

        if active_tab == "overview":
            self._draw_overview(canvas, t, snap)
        elif active_tab == "apps":
            self._draw_apps(canvas, snap, selected_idx)
        elif active_tab == "board":
            self._draw_board(canvas, snap, selected_idx)
        elif active_tab == "workstation":
            self._draw_workstation(canvas, snap, selected_idx)
        elif active_tab == "quests":
            self._draw_quests(canvas, snap)

        if cmd_open:
            self._draw_cmd_bar(canvas, cmd_query, cmd_items or [], cmd_sel)

        self._draw_footer(canvas, status_msg, idle_left)

    def _draw_overview(self, canvas: Canvas, t: float, snap: Dict[str, Any]) -> None:
        cols, rows = canvas.cols, canvas.rows
        x0 = 2
        if self.logo:
            self.logo.draw(canvas, 2, 4, t)
            x0 = self.logo.width + 5
        width = max(10, cols - x0 - 2)
        y = 4
        data = snap.get("data") or {}
        local_id = snap.get("local_identity") or {}

        y = self._section(canvas, x0, y, width, "NODE IDENTITY & READINESS")
        if local_id.get("local_node"):
            addr = local_id.get("tc_address") or local_id.get("node_id") or "local"
            canvas.text(x0, y, f"Local Ed25519: {addr}"[:width], WASHI)
            y += 1
        if data:
            score = float(data.get("composite_score") or 0.0)
            canvas.text(x0, y, str(data.get("readiness_tier", "mesh-ready"))[:width], WASHI_QUIET)
            y += 1
            bw = max(10, min(36, width - 12))
            canvas.text(x0, y, _bar(score, 100.0, bw), PERSIMMON)
            canvas.text(x0 + bw + 1, y, "%5.1f/100" % score, WASHI)
            y += 1
        else:
            canvas.text(x0, y, "waiting for node\u2026" if not snap.get("error") else "offline / unreachable", WASHI_DIM)
            y += 1
        y += 1

        y = self._section(canvas, x0, y, width, "CONNECTED PEERS")
        peers = data.get("active_webrtc_streams") or data.get("connected_peers") or []
        if not peers:
            canvas.text(x0, y, "no remote peers connected (local node ready offline)", WASHI_DIM)
            y += 1
        for p in peers[: max(1, (rows - y - 7) // 2)]:
            if y >= rows - 4:
                break
            since = time.strftime("%H:%M", time.localtime(p["connected_at"])) if p.get("connected_at") else "--:--"
            line = "%-22s %-18s %s:%s  %s" % (
                str(p.get("display_name", "?"))[:22],
                str(p.get("peer_id", "?"))[:18],
                p.get("udp_address", "?"),
                p.get("udp_port", "?"),
                since,
            )
            canvas.text(x0, y, "\u25cf", GREEN if p.get("active_stream", True) else WASHI_DIM)
            canvas.text(x0 + 2, y, line[: max(0, width - 2)], WASHI)
            y += 1
        y += 1

        y = self._section(canvas, x0, y, width, "AI PROVIDER CREDITS")
        providers = data.get("ai_providers") or {}
        if not providers:
            canvas.text(x0, y, "none configured on this node", WASHI_DIM)
            y += 1
        else:
            top = max(providers.values()) if providers else 0
            for name, credits in providers.items():
                if y >= rows - 3:
                    break
                bw = max(8, min(30, width - 24))
                canvas.text(x0, y, "%-14s" % name[:14], WASHI)
                canvas.text(x0 + 15, y, _bar(float(credits), float(top), bw), PERSIMMON)
                canvas.text(x0 + 16 + bw, y, "$%.2f" % float(credits), WASHI)
                y += 1

        if y < rows - 2:
            if snap.get("error"):
                canvas.text(x0, rows - 2, ("last error: " + snap["error"])[:width], RED)
            elif snap.get("updated_at"):
                ts = time.strftime("%H:%M:%S", time.localtime(snap["updated_at"]))
                canvas.text(x0, rows - 2, f"updated {ts} \u00b7 press [2] for all 18 Mesh OS apps or [/] for Command Bar"[:width], WASHI_DIM)

    def _draw_apps(self, canvas: Canvas, snap: Dict[str, Any], selected_idx: int) -> None:
        cols, rows = canvas.cols, canvas.rows
        x0, width = 2, max(10, cols - 4)
        windows = snap.get("windows") or WINDOW_CATALOG
        y = self._section(canvas, x0, 4, width, f"MESH OS APPS ({len(windows)})  \u00b7  Enter/o launches window")
        max_rows = max(1, rows - y - 2)
        sel = max(0, min(selected_idx, max(0, len(windows) - 1)))
        start = max(0, sel - max_rows + 1)
        for idx, item in enumerate(windows[start : start + max_rows], start=start):
            is_sel = idx == sel
            bg = SUMI_SOFT if is_sel else SUMI
            if is_sel:
                canvas.fill(x0, y, cols - 2, y + 1, bg)
                canvas.text(x0, y, "\u25cf", PERSIMMON, bg)
            slug = str(item.get("slug", ""))[:13]
            title = str(item.get("title", ""))[:20]
            route = str(item.get("route", ""))[:14]
            desc = str(item.get("desc", ""))
            line = f"{slug:13s}  {title:20s}  {route:14s}  {desc}"
            canvas.text(x0 + 2, y, line[: max(0, width - 2)], WASHI if is_sel else WASHI_QUIET, bg)
            y += 1

    def _draw_board(self, canvas: Canvas, snap: Dict[str, Any], selected_idx: int) -> None:
        cols, rows = canvas.cols, canvas.rows
        x0, width = 2, max(10, cols - 4)
        topics = snap.get("topics") or []
        y = self._section(canvas, x0, 4, width, f"CYBERSPACE BOARD ({len(topics)} topics)  \u00b7  press [o] to open Board")
        if not topics:
            canvas.text(x0, y + 1, "No topics returned yet. Press [r] to refresh or [o] to open Board.", WASHI_DIM)
            return
        max_rows = max(1, rows - y - 2)
        sel = max(0, min(selected_idx, len(topics) - 1))
        start = max(0, sel - max_rows + 1)
        for idx, topic in enumerate(topics[start : start + max_rows], start=start):
            is_sel = idx == sel
            bg = SUMI_SOFT if is_sel else SUMI
            if is_sel:
                canvas.fill(x0, y, cols - 2, y + 1, bg)
                canvas.text(x0, y, "\u25cf", PERSIMMON, bg)
            title = str(topic.get("title") or topic.get("name") or "(untitled)")
            author = str(topic.get("author") or topic.get("creator") or "peer")
            replies = topic.get("reply_count", topic.get("replies", 0))
            if isinstance(replies, list):
                replies = len(replies)
            votes = topic.get("votes", topic.get("score", 0))
            line = f"[{votes:>2}v {replies:>2}r] {title}  (@{author})"
            canvas.text(x0 + 2, y, line[: max(0, width - 2)], WASHI if is_sel else WASHI_QUIET, bg)
            y += 1

    def _draw_workstation(self, canvas: Canvas, snap: Dict[str, Any], selected_idx: int) -> None:
        cols, rows = canvas.cols, canvas.rows
        x0, width = 2, max(10, cols - 4)
        ws = snap.get("workstation") or {}
        y = self._section(canvas, x0, 4, width, "WORKSTATION & LOCAL .SPACE FILES  \u00b7  press [o] to open Workstation")
        if ws:
            summary = f"Status: {ws.get('status', 'ready')}  \u00b7  Spaces dir: {ws.get('spaces_dir') or ws.get('root') or 'local'}"
            canvas.text(x0, y, summary[:width], WASHI_QUIET)
            y += 2
        # Show real files in local ~/.tincan/node_data
        mgr = LocalNodeManager()
        entries: List[str] = []
        try:
            for p in sorted(mgr.data_dir.iterdir()):
                kind = "DIR " if p.is_dir() else "FILE"
                size_b = p.stat().st_size if p.is_file() else 0
                entries.append(f"{kind}  {p.name:36s}  {size_b:>8d} B")
        except Exception:
            pass
        if not entries:
            canvas.text(x0, y, f"Local node data dir ({mgr.data_dir}) is ready (empty).", WASHI_DIM)
            return
        max_rows = max(1, rows - y - 2)
        sel = max(0, min(selected_idx, len(entries) - 1))
        start = max(0, sel - max_rows + 1)
        for idx, line in enumerate(entries[start : start + max_rows], start=start):
            is_sel = idx == sel
            bg = SUMI_SOFT if is_sel else SUMI
            if is_sel:
                canvas.fill(x0, y, cols - 2, y + 1, bg)
                canvas.text(x0, y, "\u25cf", PERSIMMON, bg)
            canvas.text(x0 + 2, y, line[: max(0, width - 2)], WASHI if is_sel else WASHI_QUIET, bg)
            y += 1

    def _draw_quests(self, canvas: Canvas, snap: Dict[str, Any]) -> None:
        cols, rows = canvas.cols, canvas.rows
        x0, width = 2, max(10, cols - 4)
        lb = snap.get("leaderboard") or []
        tier = snap.get("tier") or {}
        y = self._section(canvas, x0, 4, width, "QUESTS, XP & MESH LEADERBOARD  \u00b7  press [o] to open Quests")
        if tier:
            tline = f"Current Tier: {tier.get('name') or tier.get('tier') or 'L1'}  \u00b7  XP: {tier.get('xp', 0)}"
            canvas.text(x0, y, tline[:width], WASHI)
            y += 2
        if not lb:
            canvas.text(x0, y, "No leaderboard entries yet. Press [r] to refresh or [o] to open Quests.", WASHI_DIM)
            return
        for rank, row in enumerate(lb[: max(1, rows - y - 2)], start=1):
            name = str(row.get("username") or row.get("peer_id") or row.get("name") or "peer")
            xp = row.get("xp", row.get("score", 0))
            line = f"#{rank:<2d}  {name:26s}  {xp} XP"
            canvas.text(x0, y, line[:width], WASHI if rank <= 3 else WASHI_QUIET)
            y += 1

    def _draw_cmd_bar(
        self,
        canvas: Canvas,
        query: str,
        items: List[Dict[str, Any]],
        sel: int,
    ) -> None:
        cols, rows = canvas.cols, canvas.rows
        box_w = min(76, max(36, cols - 8))
        box_h = min(14, max(6, rows - 6))
        x0 = max(2, (cols - box_w) // 2)
        y0 = max(3, (rows - box_h) // 2)
        canvas.fill(x0, y0, x0 + box_w, y0 + box_h, SUMI_SOFT)
        canvas.text(x0, y0, "\u250c" + "\u2500" * (box_w - 2) + "\u2510", PERSIMMON, SUMI_SOFT)
        for ry in range(y0 + 1, y0 + box_h - 1):
            canvas.text(x0, ry, "\u2502", WASHI_LINE, SUMI_SOFT)
            canvas.text(x0 + box_w - 1, ry, "\u2502", WASHI_LINE, SUMI_SOFT)
        canvas.text(x0, y0 + box_h - 1, "\u2514" + "\u2500" * (box_w - 2) + "\u2518", WASHI_LINE, SUMI_SOFT)

        prompt = f" / {query}\u2588"
        canvas.text(x0 + 2, y0 + 1, prompt[: box_w - 4], WASHI, SUMI_SOFT)
        canvas.text(x0 + 1, y0 + 2, "\u2500" * (box_w - 2), WASHI_LINE, SUMI_SOFT)

        max_items = box_h - 4
        if not items:
            canvas.text(x0 + 2, y0 + 3, "No matching app or command. Try /board, /workstation, /open arena", WASHI_DIM, SUMI_SOFT)
            return
        clamped = max(0, min(sel, len(items) - 1))
        start = max(0, clamped - max_items + 1)
        for i, item in enumerate(items[start : start + max_items], start=start):
            ry = y0 + 3 + (i - start)
            is_cur = i == clamped
            marker = "\u25cf " if is_cur else "  "
            label = f"{marker}{item['label']:18s}  {item['desc']}"
            canvas.text(x0 + 2, ry, label[: box_w - 4], WASHI if is_cur else WASHI_QUIET, SUMI_SOFT)
            if is_cur:
                canvas.text(x0 + 2, ry, "\u25cf", PERSIMMON, SUMI_SOFT)


# --------------------------------------------------------------------------- app / terminal

class App:
    def __init__(
        self,
        relay: str,
        start: str,
        idle: float,
        duration: Optional[float],
        color_mode: str,
        animate: bool,
        is_local: bool = False,
    ) -> None:
        self.relay = relay
        self.is_local = is_local
        self.view = start  # "overview" | "apps" | "board" | "workstation" | "quests" | "screensaver"
        if self.view == "dashboard":
            self.view = "overview"
        self.idle = idle
        self.duration = duration
        self.color_mode = color_mode
        self.animate = animate
        self.poller = StatusPoller(relay)
        self.saver = Screensaver()
        self.dash = Dashboard()
        self.selected_idx = 0
        self.status_msg = ""
        self.status_until = 0.0
        self.cmd_open = False
        self.cmd_query = ""
        self.cmd_sel = 0

    def _set_status(self, msg: str, ttl: float = 3.5) -> None:
        self.status_msg = msg
        self.status_until = time.time() + ttl

    def _build_cmd_items(self) -> List[Dict[str, Any]]:
        q = self.cmd_query.strip().lower()
        items: List[Dict[str, Any]] = [
            {"label": "/overview", "desc": "Switch to Overview & Mesh status tab", "kind": "tab", "target": "overview"},
            {"label": "/apps", "desc": "Browse all 18 Mesh OS apps", "kind": "tab", "target": "apps"},
            {"label": "/board", "desc": "Browse live Cyberspace Board topics", "kind": "tab", "target": "board"},
            {"label": "/workstation", "desc": "Inspect Workstation & local .space files", "kind": "tab", "target": "workstation"},
            {"label": "/quests", "desc": "View Quests, XP & leaderboard", "kind": "tab", "target": "quests"},
            {"label": "/screensaver", "desc": "Enter animated screensaver", "kind": "tab", "target": "screensaver"},
            {"label": "/os", "desc": "Start local node & open full Mesh OS window", "kind": "open", "target": "desktop"},
            {"label": "/refresh", "desc": "Refresh live node data now", "kind": "action", "target": "refresh"},
            {"label": "/quit", "desc": "Exit TinCan Terminal", "kind": "action", "target": "quit"},
        ]
        snap = self.poller.snapshot()
        for w in snap.get("windows") or WINDOW_CATALOG:
            items.append({
                "label": f"open {w['slug']}",
                "desc": f"{w['title']} ({w['route']})",
                "kind": "open",
                "target": w["slug"],
            })
        if not q:
            return items
        clean = q.lstrip("/")
        return [it for it in items if clean in it["label"].lower() or clean in it["desc"].lower()]

    def _open_app_window(self, slug: Optional[str]) -> None:
        try:
            mgr = LocalNodeManager()
            st = mgr.status()
            if st.get("running") and st.get("url"):
                base = st["url"]
            else:
                state, _ = mgr.start(host="127.0.0.1")
                base = state.url
                self.relay = base
                self.is_local = True
                self.poller.relay = base
                self.poller.refresh()
            entry = resolve_window_entry(slug)
            if not entry:
                self._set_status(f"Unknown app: {slug}")
                return
            url = f"{base.rstrip('/')}{entry['route']}"
            launch_browser_window(url, width=int(entry.get("width", 1180)), height=int(entry.get("height", 780)), app_mode=True)
            self._set_status(f"Opened {entry['title']} -> {url}")
        except Exception as exc:
            self._set_status(f"Launch error: {str(exc)[:80]}")

    def _run_cmd_selection(self) -> bool:
        """Execute selected command-bar item. Returns True if app should quit."""
        items = self._build_cmd_items()
        if not items:
            self.cmd_open = False
            self.cmd_query = ""
            return False
        chosen = items[max(0, min(self.cmd_sel, len(items) - 1))]
        self.cmd_open = False
        self.cmd_query = ""
        self.cmd_sel = 0
        if chosen["kind"] == "tab":
            self.view = chosen["target"]
            self.selected_idx = 0
            return False
        if chosen["kind"] == "open":
            self._open_app_window(chosen["target"])
            return False
        if chosen["target"] == "refresh":
            self.poller.refresh()
            self._set_status("Refreshing live node data…")
            return False
        if chosen["target"] == "quit":
            return True
        return False

    def frame(self, cols: int, rows: int, t: float, idle_left: Optional[float]) -> Canvas:
        snap = self.poller.snapshot()
        if cols < 30 or rows < 10:
            c = Canvas(cols, rows, bg=SUMI)
            c.text(0, 0, "terminal too small"[:cols], PERSIMMON, SUMI)
            return c
        if self.view == "screensaver":
            c = Canvas(cols, rows, bg=BG_DEEP)
            hint = "press any key to continue" if self.duration else "[any key] Mesh OS terminal   [q] quit"
            self.saver.draw(c, t, snap, hint, animate=self.animate)
        else:
            c = Canvas(cols, rows, bg=SUMI)
            msg = self.status_msg if time.time() < self.status_until else ""
            cmd_items = self._build_cmd_items() if self.cmd_open else []
            self.dash.draw(
                c,
                t,
                snap,
                self.relay,
                idle_left,
                active_tab=self.view,
                selected_idx=self.selected_idx,
                is_local=self.is_local,
                status_msg=msg,
                cmd_open=self.cmd_open,
                cmd_query=self.cmd_query,
                cmd_items=cmd_items,
                cmd_sel=self.cmd_sel,
            )
        return c

    def run(self) -> None:
        import termios
        import tty

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        out = sys.stdout
        signal.signal(signal.SIGTERM, _exit_on_signal)
        self.poller.start()
        start = last_input = time.time()
        try:
            tty.setcbreak(fd)
            out.write("\x1b[?1049h\x1b[?25l\x1b[2J")
            out.flush()
            while True:
                now = time.time()
                if self.duration and now - start >= self.duration:
                    return
                if self.view != "screensaver" and not self.cmd_open and self.idle > 0 and now - last_input >= self.idle:
                    self.view = "screensaver"
                size = shutil.get_terminal_size((100, 32))
                idle_left = (self.idle - (now - last_input)) if (self.view != "screensaver" and self.idle > 0) else None
                out.write(self.frame(size.columns, size.lines, now - start, idle_left).render(self.color_mode))
                out.flush()

                fps = 15.0 if self.view == "screensaver" else 6.0
                for key in _read_keys(fd, max(0.0, 1.0 / fps - (time.time() - now))):
                    last_input = time.time()
                    if self.duration:
                        return
                    if self.cmd_open:
                        if key == "esc":
                            self.cmd_open = False
                            self.cmd_query = ""
                            self.cmd_sel = 0
                        elif key == "enter":
                            if self._run_cmd_selection():
                                return
                        elif key in ("up",):
                            self.cmd_sel = max(0, self.cmd_sel - 1)
                        elif key in ("down",):
                            self.cmd_sel += 1
                        elif key == "backspace":
                            self.cmd_query = self.cmd_query[:-1]
                            self.cmd_sel = 0
                        elif len(key) == 1 and key.isprintable():
                            self.cmd_query += key
                            self.cmd_sel = 0
                        continue

                    if key in ("q", "esc"):
                        return
                    if self.view == "screensaver":
                        self.view = "overview"
                        continue
                    if key in ("/", "ctrl+k"):
                        self.cmd_open = True
                        self.cmd_query = ""
                        self.cmd_sel = 0
                    elif key == "1":
                        self.view, self.selected_idx = "overview", 0
                    elif key == "2":
                        self.view, self.selected_idx = "apps", 0
                    elif key == "3":
                        self.view, self.selected_idx = "board", 0
                    elif key == "4":
                        self.view, self.selected_idx = "workstation", 0
                    elif key == "5":
                        self.view, self.selected_idx = "quests", 0
                    elif key in ("6", "s"):
                        self.view = "screensaver"
                    elif key == "tab":
                        names = [t_id for t_id, _ in TABS]
                        idx = (names.index(self.view) + 1) % len(names) if self.view in names else 0
                        self.view, self.selected_idx = names[idx], 0
                    elif key in ("j", "down"):
                        self.selected_idx += 1
                    elif key in ("k", "up"):
                        self.selected_idx = max(0, self.selected_idx - 1)
                    elif key in ("enter", "o"):
                        if self.view == "apps":
                            windows = self.poller.snapshot().get("windows") or WINDOW_CATALOG
                            if windows:
                                chosen = windows[max(0, min(self.selected_idx, len(windows) - 1))]
                                self._open_app_window(chosen["slug"])
                        elif self.view == "board":
                            self._open_app_window("board")
                        elif self.view == "workstation":
                            self._open_app_window("space")
                        elif self.view == "quests":
                            self._open_app_window("quests")
                        else:
                            self._open_app_window("desktop")
                    elif key == "r":
                        self.poller.refresh()
                        self._set_status("Refreshing live node data…")
        except KeyboardInterrupt:
            pass
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
            out.write("\x1b[0m\x1b[?25h\x1b[?1049l")
            out.flush()


def _exit_on_signal(signum: int, frame: Any) -> None:
    raise SystemExit(0)


def _read_keys(fd: int, timeout: float) -> List[str]:
    ready, _, _ = select.select([fd], [], [], timeout)
    if not ready:
        return []
    data = os.read(fd, 64)
    keys, i = [], 0
    while i < len(data):
        c = data[i]
        if c == 0x1B:
            if i + 2 < len(data) and data[i + 1] in (ord("["), ord("O")):
                code = chr(data[i + 2])
                if code == "A":
                    keys.append("up")
                    i += 3
                    continue
                if code == "B":
                    keys.append("down")
                    i += 3
                    continue
                if code == "C":
                    keys.append("right")
                    i += 3
                    continue
                if code == "D":
                    keys.append("left")
                    i += 3
                    continue
                j = i + 2
                while j < len(data) and not 0x40 <= data[j] <= 0x7E:
                    j += 1
                keys.append("seq")
                i = j + 1
                continue
            keys.append("esc")
        elif c in (0x0D, 0x0A):
            keys.append("enter")
        elif c in (0x7F, 0x08):
            keys.append("backspace")
        elif c == 0x09:
            keys.append("tab")
        elif c == 0x0B:
            keys.append("ctrl+k")
        else:
            keys.append(chr(c) if 32 <= c < 127 else "?")
        i += 1
    return keys


def splash(seconds: float = 2.5, relay: str = DEFAULT_RELAY) -> None:
    """Show the animated logo for a few seconds (used by connect_peer.py). No-op without a TTY."""
    if sys.stdin.isatty() and sys.stdout.isatty():
        App(relay, "screensaver", 0, seconds, detect_color_mode(), True).run()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="tincan-tui", description="TinCan Mesh OS interactive terminal shell")
    parser.add_argument("--relay", default=None, help="Mesh node/relay base URL (auto-detects local node first)")
    parser.add_argument("--screensaver", action="store_true", help="Start in the screensaver view")
    parser.add_argument(
        "--view",
        default="overview",
        choices=["overview", "apps", "board", "workstation", "quests", "screensaver"],
        help="Initial terminal tab (default: overview)",
    )
    parser.add_argument("--idle", type=float, default=60.0, help="Seconds of inactivity before the screensaver (0 = never)")
    parser.add_argument("--duration", type=float, default=None, help="Exit automatically after N seconds")
    parser.add_argument("--colors", choices=["auto", "truecolor", "256"], default="auto")
    parser.add_argument("--static", action="store_true", help="Disable animation")
    parser.add_argument("--once", action="store_true", help="Print a single frame to stdout and exit (no TTY needed)")
    parser.add_argument("--size", default=None, help="COLSxROWS for --once (default: terminal size)")
    args = parser.parse_args(argv)

    if args.relay:
        base_url = args.relay.rstrip("/")
        is_local = "127.0.0.1" in base_url or "localhost" in base_url
    else:
        base_url, is_local = _resolve_initial_base_url(DEFAULT_RELAY)

    start_view = "screensaver" if args.screensaver else args.view
    mode = detect_color_mode() if args.colors == "auto" else args.colors
    app = App(base_url, start_view, args.idle, args.duration, mode, not args.static, is_local=is_local)

    if args.once or not (sys.stdin.isatty() and sys.stdout.isatty()):
        if args.size:
            cols, rows = (int(v) for v in args.size.lower().split("x"))
        else:
            size = shutil.get_terminal_size((100, 40))
            cols, rows = size.columns, size.lines
        app.poller._fetch()
        sys.stdout.write(app.frame(cols, rows, 0.0, None).render(mode) + "\x1b[0m\n")
        return 0

    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
