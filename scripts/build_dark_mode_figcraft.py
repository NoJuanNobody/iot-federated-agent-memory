#!/usr/bin/env python3
"""Build the complete TinCan 2.2 Dark Mode FigCraft Design System (tincan_dark_mode_system.figcraft).

Unites all 12 Dark Mode pages & components of TinCan 2.2 on a 4x3 canvas grid in
Aeonik Monochrome Black & White (#080808 stage, #0E0E0E window, #151515 cards, #2E2E2E hairlines,
#F5F5F5 crisp washi text, #FFFFFF emerald accents) with unmistakable Pitch-Black
Terminal viewports (#000000 background, #0C0C0C terminal chrome header, red/amber/emerald
traffic dots, #FFFFFF emerald borders, #FFFFFF prompt `you@tincan:~/space$`, and
glowing #FFFFFF cursor block).
"""

from __future__ import annotations

import copy
import json
import os
import zipfile
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGNS_DIR = os.path.join(REPO_ROOT, "assets", "designs")
OUT_FIGCRAFT = os.path.join(DESIGNS_DIR, "tincan_dark_mode_system.figcraft")


def hex_to_rgba(hex_str: str, alpha: float = 1.0) -> Dict[str, float]:
    h = hex_str.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    return {"r": round(r, 6), "g": round(g, 6), "b": round(b, 6), "a": alpha}


def rgba_to_hex(color: Any) -> str:
    if isinstance(color, str):
        return color.upper()
    if isinstance(color, dict):
        r = max(0, min(255, round(float(color.get("r", 0.0)) * 255)))
        g = max(0, min(255, round(float(color.get("g", 0.0)) * 255)))
        b = max(0, min(255, round(float(color.get("b", 0.0)) * 255)))
        return f"#{r:02X}{g:02X}{b:02X}"
    return "#000000"


def solid_paint(hex_color: str, opacity: float = 1.0) -> List[Dict[str, Any]]:
    return [
        {
            "type": "solid",
            "color": hex_to_rgba(hex_color),
            "opacity": opacity,
            "visible": True,
            "blend": "normal",
        }
    ]


class FigCraftBuilder:
    def __init__(self) -> None:
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.next_id: int = 1
        self.page_id: int = self.alloc_id()
        self.nodes[str(self.page_id)] = {
            "id": self.page_id,
            "name": "TinCan 2.2 · Dark Mode & Dark Terminal System (All 12 Pages & Components)",
            "type": "page",
            "background": hex_to_rgba("#050505"),
            "flows": [],
            "prototype": {
                "device": "None",
                "background": hex_to_rgba("#050505"),
                "rotation": "portrait",
            },
            "guides": [],
            "children": [],
            "width": 0.0,
            "height": 0.0,
        }

    def alloc_id(self) -> int:
        nid = self.next_id
        self.next_id += 1
        return nid

    def _attach(self, parent_id: int, nid: int, index: Optional[int] = None) -> None:
        parent = self.nodes[str(parent_id)]
        children = parent.setdefault("children", [])
        if index is None:
            children.append(nid)
        else:
            children.insert(index, nid)

    def add_frame(
        self,
        parent_id: int,
        name: str,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: Optional[str] = "#0E0E0E",
        stroke: Optional[str] = "#2E2E2E",
        stroke_weight: float = 1.0,
        radius: float = 0.0,
        clip: bool = True,
        index: Optional[int] = None,
    ) -> int:
        nid = self.alloc_id()
        node: Dict[str, Any] = {
            "id": nid,
            "name": name,
            "type": "frame",
            "parent": parent_id,
            "children": [],
            "transform": [1.0, 0.0, 0.0, 1.0, float(x), float(y)],
            "width": float(w),
            "height": float(h),
            "clip": clip,
        }
        if fill:
            node["fills"] = solid_paint(fill)
        if stroke:
            node["strokes"] = solid_paint(stroke)
            node["stroke"] = {
                "weight": float(stroke_weight),
                "align": "inside",
                "sides": None,
                "cap_start": "none",
                "cap_end": "none",
                "join": "miter",
                "miter_limit": 4.0,
                "dashes": [],
            }
        if radius > 0:
            r = float(radius)
            node["corners"] = {"radii": [r, r, r, r], "smoothing": 0.0}
        if str(parent_id) in self.nodes and self.nodes[str(parent_id)].get("layout"):
            node["child_layout"] = {
                "sizing_h": "fixed",
                "sizing_v": "fixed",
                "absolute": True,
                "min_w": None,
                "max_w": None,
                "min_h": None,
                "max_h": None,
                "grid_column": None,
                "grid_row": None,
                "grid_column_span": 0,
                "grid_row_span": 0,
            }
        self.nodes[str(nid)] = node
        self._attach(parent_id, nid, index=index)
        return nid

    def add_rect(
        self,
        parent_id: int,
        name: str,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: Optional[str] = "#151515",
        stroke: Optional[str] = None,
        stroke_weight: float = 1.0,
        radius: float = 0.0,
        index: Optional[int] = None,
    ) -> int:
        nid = self.alloc_id()
        node: Dict[str, Any] = {
            "id": nid,
            "name": name,
            "type": "rectangle",
            "parent": parent_id,
            "blend": "normal",
            "transform": [1.0, 0.0, 0.0, 1.0, float(x), float(y)],
            "width": float(w),
            "height": float(h),
        }
        if fill:
            node["fills"] = solid_paint(fill)
        if stroke:
            node["strokes"] = solid_paint(stroke)
            node["stroke"] = {
                "weight": float(stroke_weight),
                "align": "inside",
                "sides": None,
                "cap_start": "none",
                "cap_end": "none",
                "join": "miter",
                "miter_limit": 4.0,
                "dashes": [],
            }
        if radius > 0:
            r = float(radius)
            node["corners"] = {"radii": [r, r, r, r], "smoothing": 0.0}
        if str(parent_id) in self.nodes and self.nodes[str(parent_id)].get("layout"):
            node["child_layout"] = {
                "sizing_h": "fixed",
                "sizing_v": "fixed",
                "absolute": True,
                "min_w": None,
                "max_w": None,
                "min_h": None,
                "max_h": None,
                "grid_column": None,
                "grid_row": None,
                "grid_column_span": 0,
                "grid_row_span": 0,
            }
        self.nodes[str(nid)] = node
        self._attach(parent_id, nid, index=index)
        return nid

    def add_ellipse(
        self,
        parent_id: int,
        name: str,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: Optional[str] = "#FFFFFF",
        stroke: Optional[str] = None,
        stroke_weight: float = 1.5,
    ) -> int:
        nid = self.alloc_id()
        node: Dict[str, Any] = {
            "id": nid,
            "name": name,
            "type": "ellipse",
            "start": 0.0,
            "sweep": 6.283185307179586,
            "inner": 0.0,
            "parent": parent_id,
            "blend": "normal",
            "transform": [1.0, 0.0, 0.0, 1.0, float(x), float(y)],
            "width": float(w),
            "height": float(h),
        }
        if fill:
            node["fills"] = solid_paint(fill)
        if stroke:
            node["strokes"] = solid_paint(stroke)
            node["stroke"] = {
                "weight": float(stroke_weight),
                "align": "center",
                "sides": None,
                "cap_start": "none",
                "cap_end": "none",
                "join": "miter",
                "miter_limit": 4.0,
                "dashes": [],
            }
        self.nodes[str(nid)] = node
        self._attach(parent_id, nid)
        return nid

    def add_text(
        self,
        parent_id: int,
        name: str,
        text: str,
        x: float,
        y: float,
        size: float = 12.0,
        color: str = "#F5F5F5",
        font_family: str = "Inter",
        font_style: str = "Regular",
        w: Optional[float] = None,
        h: Optional[float] = None,
    ) -> int:
        nid = self.alloc_id()
        est_w = float(w) if w is not None else max(16.0, round(len(text) * size * 0.56, 1))
        est_h = float(h) if h is not None else round(size * 1.3, 1)
        node: Dict[str, Any] = {
            "id": nid,
            "name": name,
            "type": "text",
            "characters": text,
            "style": {
                "font_family": font_family,
                "font_style": font_style,
                "font_size": float(size),
                "line_height": {"unit": "auto"},
                "letter_spacing": {"unit": "percent", "value": 0.0},
                "decoration": "none",
                "case": "original",
                "fills": None,
                "link": None,
            },
            "parent": parent_id,
            "blend": "normal",
            "transform": [1.0, 0.0, 0.0, 1.0, float(x), float(y)],
            "width": est_w,
            "height": est_h,
            "fills": solid_paint(color),
        }
        self.nodes[str(nid)] = node
        self._attach(parent_id, nid)
        return nid

    def add_pill(
        self,
        parent_id: int,
        name: str,
        text: str,
        x: float,
        y: float,
        w: float,
        h: float = 26.0,
        bg: str = "#1A1A1A",
        border: Optional[str] = "#383838",
        fg: str = "#F5F5F5",
        font_family: str = "JetBrains Mono",
        font_style: str = "SemiBold",
        font_size: float = 10.5,
        dot_color: Optional[str] = None,
    ) -> int:
        f_id = self.add_frame(
            parent_id,
            name,
            x,
            y,
            w,
            h,
            fill=bg,
            stroke=border,
            stroke_weight=1.0,
            radius=999.0,
            clip=True,
        )
        tx = 12.0
        if dot_color:
            self.add_ellipse(f_id, f"{name}_Dot", 10.0, round((h - 7.0) / 2, 1), 7.0, 7.0, fill=dot_color)
            tx = 23.0
        self.add_text(
            f_id,
            f"{name}_Txt",
            text,
            tx,
            round((h - font_size * 1.2) / 2, 1),
            size=font_size,
            color=fg,
            font_family=font_family,
            font_style=font_style,
        )
        return f_id

    def add_dark_terminal_box(
        self,
        parent_id: int,
        name: str,
        x: float,
        y: float,
        w: float,
        h: float,
        title: str,
        status_pill: str,
        lines: List[Tuple[str, str]],
        show_tui_tabs: bool = True,
        prompt_line: Optional[str] = "you@tincan:~/space$ ",
    ) -> int:
        """Create an unmistakably dark Pitch-Black Terminal (#000000) with zero header overlap."""
        term_id = self.add_frame(
            parent_id,
            name,
            x,
            y,
            w,
            h,
            fill="#000000",
            stroke="#FFFFFF",
            stroke_weight=1.5,
            radius=12.0,
            clip=True,
        )
        hdr_h = 34.0
        self.add_rect(term_id, f"{name}_HdrBg", 0, 0, w, hdr_h, fill="#0C0C0C")
        self.add_rect(term_id, f"{name}_HdrLine", 0, hdr_h, w, 1.0, fill="#2E2E2E")
        # Traffic light dots
        self.add_ellipse(term_id, f"{name}_DotR", 14, 12, 9, 9, fill="#525252")
        self.add_ellipse(term_id, f"{name}_DotY", 28, 12, 9, 9, fill="#A3A3A3")
        self.add_ellipse(term_id, f"{name}_DotG", 42, 12, 9, 9, fill="#FFFFFF")

        status_x = max(140.0, w - len(status_pill) * 6.5 - 14.0)
        if show_tui_tabs and w >= 560:
            tabs = (
                [("Claude TUI", True), ("OpenCode TUI", False), ("DSX TUI", False), ("Bash", False)]
                if w >= 860
                else [("Claude TUI", True), ("OpenCode", False), ("Bash", False)]
            )
            total_tabs_w = sum(len(t[0]) * 6.4 + 22 for t in tabs)
            tabs_start_x = max(180.0, status_x - total_tabs_w - 14.0)
            max_title_chars = max(10, int((tabs_start_x - 66.0) / 6.5))
            clean_title = title if len(title) <= max_title_chars else title[: max_title_chars - 1] + "…"
            self.add_text(
                term_id,
                f"{name}_HdrTitle",
                clean_title,
                58,
                10,
                size=10.5,
                color="#A3A3A4",
                font_family="JetBrains Mono",
                font_style="Bold",
            )
            tx = tabs_start_x
            for t_lbl, is_act in tabs:
                tw = len(t_lbl) * 6.4 + 16
                self.add_pill(
                    term_id,
                    f"{name}_Tab_{t_lbl}",
                    t_lbl,
                    tx,
                    6,
                    tw,
                    22,
                    bg="#FFFFFF" if is_act else "#141414",
                    border="#FFFFFF" if is_act else "#333333",
                    fg="#000000" if is_act else "#A3A3A4",
                    font_size=9.5,
                )
                tx += tw + 6
        else:
            max_title_chars = max(8, int((status_x - 66.0) / 6.5))
            clean_title = title if len(title) <= max_title_chars else title[: max_title_chars - 1] + "…"
            self.add_text(
                term_id,
                f"{name}_HdrTitle",
                clean_title,
                58,
                10,
                size=10.5,
                color="#A3A3A4",
                font_family="JetBrains Mono",
                font_style="Bold",
            )

        self.add_text(
            term_id,
            f"{name}_Status",
            status_pill,
            status_x,
            10,
            size=10.0,
            color="#FFFFFF",
            font_family="JetBrains Mono",
            font_style="Bold",
        )

        cy = hdr_h + 12.0
        bottom_limit = h - (36.0 if prompt_line else 6.0)
        for idx, (line_txt, line_col) in enumerate(lines):
            if cy + 15 > bottom_limit:
                break
            self.add_text(
                term_id,
                f"{name}_L{idx+1}",
                line_txt,
                16,
                cy,
                size=11.0,
                color=line_col,
                font_family="JetBrains Mono",
                font_style="SemiBold" if line_txt.startswith("you@tincan") or line_txt.startswith("$ ") else "Regular",
            )
            cy += 20.5

        if prompt_line:
            row_y = h - 34.0
            self.add_rect(term_id, f"{name}_InputRowBg", 0, row_y, w, 34.0, fill="#0A0A0A")
            self.add_rect(term_id, f"{name}_InputRowLine", 0, row_y, w, 1.0, fill="#2E2E2E")
            self.add_text(
                term_id,
                f"{name}_PromptRowTxt",
                prompt_line,
                16,
                row_y + 9.0,
                size=11.0,
                color="#FFFFFF",
                font_family="JetBrains Mono",
                font_style="Bold",
            )
            cursor_x = 16 + len(prompt_line) * 6.7
            self.add_rect(term_id, f"{name}_Cursor", min(w - 86, cursor_x), row_y + 9.0, 8.0, 15.0, fill="#FFFFFF")
            self.add_pill(
                term_id,
                f"{name}_RunBtn",
                "RUN ↵",
                w - 68.0,
                row_y + 5.0,
                56.0,
                24.0,
                bg="#FFFFFF",
                border="#FFFFFF",
                fg="#000000",
                font_size=9.5,
            )
        return term_id

    def add_shell_topbar_and_window(
        self,
        artboard_name: str,
        grid_x: float,
        grid_y: float,
        active_route: str,
        win_title: str,
        win_badge: str,
        win_meta: str,
    ) -> Tuple[int, int]:
        root = self.add_frame(
            self.page_id,
            artboard_name,
            grid_x,
            grid_y,
            1440.0,
            900.0,
            fill="#080808",
            stroke="#2A2A2A",
            stroke_weight=1.0,
            radius=0.0,
            clip=True,
        )
        # Topbar
        tb = self.add_frame(root, "TopBar", 20, 14, 1400, 40, fill=None, stroke=None, clip=False)
        self.add_ellipse(tb, "BrandRing", 4, 7, 26, 26, fill=None, stroke="#F5F5F5", stroke_weight=2.4)
        self.add_ellipse(tb, "BrandDot", 25, 12, 4, 4, fill="#FFFFFF")
        self.add_text(tb, "BrandName", "TinCan", 38, 10, size=16.0, color="#F5F5F5", font_style="Bold")
        self.add_pill(tb, "CmdKPill", "tools · ⌘K", 104, 7, 94, 26, bg="#141414", border="#333333", fg="#A3A3A4")

        routes = ["/terminal", "/ai", "/copilot", "/workstation", "/3dstudio", "/nodes", "/arena", "/board", "/talk", "/tokens"]
        rx = 208.0
        for r in routes:
            is_act = r == active_route
            lbl = f"{r} ●" if is_act else r
            rw = len(lbl) * 6.8 + 20
            self.add_pill(
                tb,
                f"Nav_{r}",
                lbl,
                rx,
                7,
                rw,
                26,
                bg="#FFFFFF" if is_act else "#111111",
                border="#FFFFFF" if is_act else "#2E2E2E",
                fg="#000000" if is_act else "#A3A3A4",
                font_size=10.0,
            )
            rx += rw + 6.0

        # Theme toggle pill + status pills on top-right
        self.add_pill(
            tb,
            "ThemeTogglePill",
            "DARK · MONOCHROME B&W",
            1042,
            7,
            178,
            26,
            bg="#000000",
            border="#FFFFFF",
            fg="#FFFFFF",
            font_size=10.0,
            dot_color="#FFFFFF",
        )
        self.add_pill(
            tb,
            "VaultPill",
            "VAULT · 5,000 CR ($5.00)",
            1228,
            7,
            172,
            26,
            bg="#141414",
            border="#333333",
            fg="#F5F5F5",
            font_size=10.0,
            dot_color="#FFFFFF",
        )

        # Window frame
        win = self.add_frame(
            root,
            "WindowFrame",
            20,
            64,
            1400,
            792,
            fill="#0E0E0E",
            stroke="#333333",
            stroke_weight=1.0,
            radius=16.0,
            clip=True,
        )
        self.add_rect(win, "TitlebarBg", 0, 0, 1400, 44, fill="#131313")
        self.add_rect(win, "TitlebarLine", 0, 44, 1400, 1, fill="#2E2E2E")
        self.add_rect(win, "WinIcon", 16, 15, 14, 14, fill="#FFFFFF", radius=3.0)
        self.add_text(win, "WinTitle", win_title, 38, 13, size=14.0, color="#F5F5F5", font_style="Bold")
        bw = len(win_badge) * 6.8 + 18
        tx_badge = 46 + len(win_title) * 7.5
        self.add_pill(
            win,
            "WinBadge",
            win_badge,
            tx_badge,
            12,
            bw,
            20,
            bg="#FFFFFF",
            border="#FFFFFF",
            fg="#000000",
            font_size=9.5,
        )
        meta_x = tx_badge + bw + 12
        max_meta_chars = max(12, int((1100.0 - meta_x) / 6.6))
        clean_meta = win_meta if len(win_meta) <= max_meta_chars else win_meta[: max_meta_chars - 1] + "…"
        self.add_text(
            win,
            "WinMeta",
            clean_meta,
            meta_x,
            15,
            size=11.0,
            color="#A3A3A4",
            font_family="JetBrains Mono",
        )
        # Window controls
        self.add_pill(win, "CtlTheme", "● Dark", 1118, 10, 74, 24, bg="#000000", border="#FFFFFF", fg="#FFFFFF", font_size=10.0)
        self.add_pill(win, "CtlNew", "+ New", 1198, 10, 58, 24, bg="#171717", border="#383838", fg="#F5F5F5", font_size=10.0)
        self.add_pill(win, "CtlPop", "Pop Out ↗", 1262, 10, 74, 24, bg="#171717", border="#383838", fg="#F5F5F5", font_size=10.0)
        self.add_pill(win, "CtlMax", "□", 1342, 10, 24, 24, bg="#171717", border="#383838", fg="#F5F5F5", font_size=10.0)
        self.add_pill(win, "CtlClose", "×", 1370, 10, 24, 24, bg="#171717", border="#383838", fg="#F5F5F5", font_size=11.0)

        # Statusbar
        self.add_text(
            root,
            "StatusLeft",
            "tincan-cli 2.2 · theme: obsidian-dark (WCAG AAA 17.4:1) · merkle 7a4c9f · terminal: #000000 dark-default · Railway 200 OK",
            20,
            868,
            size=11.0,
            color="#A3A3A4",
            font_family="JetBrains Mono",
        )
        self.add_text(
            root,
            "StatusRight",
            "[k] theme toggle  [⌘K] launcher  [t] dark terminal  TinCan Mesh OS 2.2",
            1015,
            868,
            size=11.0,
            color="#FFFFFF",
            font_family="JetBrains Mono",
        )
        return root, win

    def import_and_darken_frame(
        self,
        zip_path: str,
        src_frame_id: int,
        new_name: str,
        grid_x: float,
        grid_y: float,
        badge_xy: Optional[Tuple[float, float]] = (576.0, 16.0),
    ) -> int:
        """Import an existing FigCraft artboard subtree and transform every node to Monochrome Black & White Dark Mode."""
        with zipfile.ZipFile(zip_path) as z:
            src_doc = json.loads(z.read("document.json"))
        src_nodes = src_doc["nodes"]

        id_map: Dict[int, int] = {}

        def clone_node(old_id: int, new_parent_id: int, is_root: bool = False) -> int:
            old = copy.deepcopy(src_nodes[str(old_id)])
            nid = self.alloc_id()
            id_map[old_id] = nid
            old["id"] = nid
            old["parent"] = new_parent_id
            old_children = old.get("children", [])
            old["children"] = []

            nm = (old.get("name") or "").lower()
            ntype = old.get("type")
            w = float(old.get("width") or 0.0)
            h = float(old.get("height") or 0.0)
            new_parent_node = self.nodes.get(str(new_parent_id)) or {}
            new_parent_fills = new_parent_node.get("fills") or []
            new_parent_hex = (
                rgba_to_hex(new_parent_fills[0]["color"])
                if new_parent_fills and isinstance(new_parent_fills[0], dict) and "color" in new_parent_fills[0]
                else ""
            )

            if is_root:
                old["name"] = new_name
                old["transform"] = [1.0, 0.0, 0.0, 1.0, float(grid_x), float(grid_y)]
                old["fills"] = solid_paint("#080808")
            else:
                fills = old.get("fills") or []
                if fills and isinstance(fills[0], dict) and "color" in fills[0]:
                    hx = rgba_to_hex(fills[0]["color"])
                    if ntype == "text":
                        txt_val = old.get("characters") or ""
                        # Any text inside a bright emerald #FFFFFF pill/button gets deep ink #000000
                        if new_parent_hex == "#FFFFFF" or (hx in ("#ECF1E6", "#FFFFFF", "#F4F8F0") and new_parent_hex != "#000000"):
                            old["fills"] = solid_paint("#000000")
                        elif txt_val.startswith("you@tincan") or txt_val.startswith("+ ") or "●" in txt_val or hx in ("#107A47", "#FFFFFF", "#FFFFFF"):
                            old["fills"] = solid_paint("#FFFFFF")
                        elif txt_val.startswith("- ") or hx == "#8A1C1C":
                            old["fills"] = solid_paint("#D4D4D4")
                        elif hx in ("#111111", "#F5F5F5"):
                            old["fills"] = solid_paint("#F5F5F5")
                        elif hx in ("#4A4A4A", "#374151", "#94ADA0"):
                            old["fills"] = solid_paint("#A3A3A4")
                        elif hx in ("#5C5C5C", "#6B7280"):
                            old["fills"] = solid_paint("#737373")
                        else:
                            old["fills"] = solid_paint("#F5F5F5")
                    else:
                        is_terminal_or_code = any(
                            k in nm
                            for k in (
                                "termdark",
                                "heroinput",
                                "diffbox",
                                "spacediffbox",
                                "rodincanvas",
                                "spaceshellbox",
                                "spaceeditorbox",
                                "wsviewportcanvas",
                                "codebox",
                                "composebox",
                                "patch",
                                "inspectorcode",
                                "rodinstage",
                                "viewport",
                                "meshstage",
                            )
                        )
                        if is_terminal_or_code or hx in ("#050505", "#000000"):
                            old["fills"] = solid_paint("#000000")
                            old["strokes"] = solid_paint("#FFFFFF")
                        elif hx == "#0B1410":
                            old["fills"] = solid_paint("#0C0C0C")
                        elif hx in ("#DFE6D7", "#DCE4D4", "#E5EFE0"):
                            old["fills"] = solid_paint("#080808")
                        elif hx == "#ECF1E6":
                            if "window" in nm or "drawer" in nm or "panel" in nm or "island" in nm or h > 400:
                                old["fills"] = solid_paint("#0E0E0E")
                            else:
                                old["fills"] = solid_paint("#141414")
                        elif hx in ("#F4F8F0", "#F8FBF5"):
                            old["fills"] = solid_paint("#151515")
                        elif hx in ("#E6F4EC", "#EAF5EE", "#8CE2B0"):
                            old["fills"] = solid_paint("#181818")
                        elif hx in ("#CFD9C5", "#D9D9D9"):
                            old["fills"] = solid_paint("#262626")
                        elif hx == "#FFFFFF":
                            if "patch" in nm or "code" in nm or "term" in nm or "stage" in nm:
                                old["fills"] = solid_paint("#000000")
                            else:
                                old["fills"] = solid_paint("#1A1A1A")
                        elif hx in ("#111111", "#107A47", "#FFFFFF"):
                            if w <= 3.0 or h <= 3.0:
                                if "spark" in nm or "edge" in nm:
                                    old["fills"] = solid_paint("#FFFFFF")
                                else:
                                    old["fills"] = solid_paint("#2E2E2E")
                            elif "track" in nm:
                                old["fills"] = solid_paint("#242424")
                            else:
                                old["fills"] = solid_paint("#FFFFFF")

                strokes = old.get("strokes") or []
                if strokes and isinstance(strokes[0], dict) and "color" in strokes[0]:
                    shx = rgba_to_hex(strokes[0]["color"])
                    if any(k in nm for k in ("heroinput", "diffbox", "codebox", "composebox", "patch", "term", "island")):
                        old["strokes"] = solid_paint("#FFFFFF")
                    elif shx in ("#107A47", "#FFFFFF"):
                        old["strokes"] = solid_paint("#FFFFFF")
                    elif "swirl" in nm or "mark" in nm:
                        old["strokes"] = solid_paint("#F5F5F5")
                    else:
                        old["strokes"] = solid_paint("#333333")

            self.nodes[str(nid)] = old
            self._attach(new_parent_id, nid)
            for cid in old_children:
                if str(cid) in src_nodes:
                    clone_node(cid, nid, is_root=False)

            # Second pass for rectangle-backed buttons where text was a sibling instead of a child
            return nid

        root_nid = clone_node(src_frame_id, self.page_id, is_root=True)
        if badge_xy is not None:
            self.add_pill(
                root_nid,
                f"DarkBadge_{root_nid}",
                "DARK MODE · TERMINAL #000000",
                badge_xy[0],
                badge_xy[1],
                228.0,
                24.0,
                bg="#000000",
                border="#FFFFFF",
                fg="#FFFFFF",
                font_size=9.5,
                dot_color="#FFFFFF",
            )
        return root_nid

    # -------------------------------------------------------------------------
    # Bespoke Artboard 01: Zen Startup Shell, Video Feed & Cmd+K Command Bar (/)
    # -------------------------------------------------------------------------
    def build_artboard_01_zen_shell(self, gx: float, gy: float) -> int:
        root = self.add_frame(
            self.page_id,
            "01 · Zen Startup Shell, Video Feed & Cmd+K Command Bar (/)",
            gx,
            gy,
            1440,
            900,
            fill="#050505",
            stroke="#2E2E2E",
            clip=True,
        )
        self.add_rect(root, "WashRust", 180, 90, 420, 720, fill="#0F0F0F", radius=40)
        self.add_rect(root, "WashMoss", 820, 110, 440, 700, fill="#0F0F0F", radius=40)

        self.add_ellipse(root, "ZenMarkRing", 32, 26, 30, 30, fill=None, stroke="#FFFFFF", stroke_weight=2.4)
        self.add_ellipse(root, "ZenMarkDot", 56, 32, 4.5, 4.5, fill="#FFFFFF")
        self.add_text(root, "ZenMarkTitle", "TinCan", 74, 30, size=18, color="#FFFFFF", font_style="Bold")
        self.add_pill(root, "ZenMarkHint", "tools · ⌘K", 150, 29, 92, 24, bg="#121212", border="#333333", fg="#A3A3A4")
        self.add_pill(
            root,
            "ZenThemeBtn",
            "DARK · MONOCHROME B&W",
            252,
            29,
            152,
            24,
            bg="#000000",
            border="#FFFFFF",
            fg="#FFFFFF",
            dot_color="#FFFFFF",
        )

        vf = self.add_frame(
            root,
            "ZenVideoFrame_9x16",
            860,
            56,
            430,
            764,
            fill="#0A0A0A",
            stroke="#383838",
            stroke_weight=1.5,
            radius=16,
            clip=True,
        )
        self.add_pill(
            vf,
            "ZenClipTag",
            "▶ Clip 1/4 · @nojuannobody",
            16,
            16,
            196,
            26,
            bg="#000000",
            border="#FFFFFF",
            fg="#F5F5F5",
            font_size=10,
        )
        self.add_rect(vf, "VideoPreviewCard", 24, 64, 382, 540, fill="#111111", stroke="#2C2C2C", radius=12)
        self.add_text(vf, "VidOverlayEye", "SPONSORED WALKTHROUGH · +5,000 CR AD POOL", 42, 86, size=10, color="#FFFFFF", font_family="JetBrains Mono", font_style="Bold")
        self.add_text(vf, "VidOverlayH1", "Zero-Account Mesh OS & Dark Terminal", 42, 110, size=15, color="#FFFFFF", font_style="Bold")
        self.add_dark_terminal_box(
            vf,
            "VideoEmbeddedDarkTerm",
            38,
            148,
            354,
            280,
            "tincan start · live mesh TUI",
            "● 60fps",
            [
                ("you@tincan:~/space$ tincan whoami", "#FFFFFF"),
                ("tc:p3r8nq47m9 @nojuannobody", "#F5F5F5"),
                ("you@tincan:~/space$ tincan call --screen", "#FFFFFF"),
                ("[webrtc] sub-80ms UDP room main live", "#FFFFFF"),
                ("[reward] +5,000 CR credited (zero subs)", "#D4D4D4"),
            ],
            show_tui_tabs=False,
            prompt_line="you@tincan:~$ ",
        )
        self.add_text(vf, "VidCaptionTitle", "Aleploi Voice & TinCan Dark Terminal Demo", 24, 636, size=15, color="#FFFFFF", font_style="Bold")
        self.add_text(vf, "VidCaptionMeta", "@nojuannobody · Sponsored · Auto-earning +5,000 CR", 24, 662, size=11.5, color="#A3A3A4")
        self.add_pill(vf, "VidSoundPill", "[AUDIO] Sound on", 24, 710, 132, 30, bg="#161616", border="#383838", fg="#FFFFFF")
        self.add_pill(vf, "VidJoinPill", "Join the mesh →", 268, 710, 138, 30, bg="#FFFFFF", border="#FFFFFF", fg="#000000")

        self.add_rect(root, "Tick1_Current", 1396, 390, 3, 32, fill="#FFFFFF", radius=1.5)
        self.add_rect(root, "Tick2", 1396, 432, 3, 18, fill="#404040", radius=1.5)
        self.add_rect(root, "Tick3", 1396, 460, 3, 18, fill="#404040", radius=1.5)
        self.add_rect(root, "Tick4", 1396, 488, 3, 18, fill="#404040", radius=1.5)

        zl = self.add_frame(
            root,
            "ZenLauncherSheet_CmdK",
            48,
            76,
            776,
            744,
            fill="#0D0D0D",
            stroke="#383838",
            stroke_weight=1.5,
            radius=16,
            clip=True,
        )
        self.add_text(zl, "ZLLabel", "COMMAND LAUNCHER (⌘K) · SEARCH TOOLS, @MESSAGE PEERS, OR > RUN IN DARK TERMINAL", 28, 22, size=10.5, color="#FFFFFF", font_family="JetBrains Mono", font_style="Bold")
        sbox = self.add_frame(zl, "ZLSearchBox", 28, 46, 720, 44, fill="#000000", stroke="#FFFFFF", stroke_weight=1.5, radius=10)
        self.add_text(sbox, "ZLSearchTxt", "> tincan status && pytest -q tests/test_dark_mode.py", 16, 13, size=13, color="#F5F5F5", font_family="JetBrains Mono")
        self.add_pill(sbox, "ZLEscKey", "esc", 662, 10, 44, 24, bg="#161616", border="#383838", fg="#A3A3A4", font_size=10)

        self.add_text(zl, "ZLHint", "Search tools · @ message someone · > run a command · /dark /light /terminal /copilot /workstation /3dstudio /nodes", 28, 100, size=11, color="#A3A3A4")

        tools = [
            ("Terminal", "Quickstart, dark TinCanShell & coding agent harnesses (agy, claude, opencode, dsx)", "/terminal", True),
            ("AI Copilot", "Multi-gateway router (Ollama local / FAU OwlChat / NanoGPT TEE) & .space diffs", "/copilot", False),
            ("Workstation", "VSCode-style .space VFS explorer, multi-tab code editor & docked dark terminal", "/workstation", False),
            ("3D Studio", "Hyper3D Rodin v2 GLB meshes, TEE hardware enclave audits & Space bridge", "/3dstudio", False),
            ("Node Studio", "Nano Banana Gemini Node Studio · dark dot-grid canvas, Prompt Island & Lumina Library", "/nodes", False),
            ("Arena", "2-Brain blind model duels, A/B voting (+150 XP) & Context Palace SQLite inventory", "/arena", False),
            ("Board", "Cyberspace omni-bar, free AI suggestions, curated feed & knowledge graph", "/board", False),
            ("Talk & Call", "Encrypted channels, DM roster, Kokoro TTS & sub-80ms WebRTC terminal screenshare", "/talk", False),
            ("Tokens & Ads", "Watch Home Screen sponsor ads to earn +5,000 CR deliverables (zero subscriptions)", "/tokens", False),
        ]
        ty = 128.0
        for t_name, t_desc, t_cmd, is_sel in tools:
            row = self.add_frame(
                zl,
                f"ZLRow_{t_name}",
                28,
                ty,
                720,
                36,
                fill="#1A1A1A" if is_sel else "#121212",
                stroke="#FFFFFF" if is_sel else "#262626",
                radius=8,
            )
            if is_sel:
                self.add_ellipse(row, f"ZLDot_{t_name}", 12, 14, 8, 8, fill="#FFFFFF")
            self.add_text(row, f"ZLName_{t_name}", t_name, 28, 8, size=14.5, color="#FFFFFF" if is_sel else "#D4D4D4", font_style="Bold")
            self.add_text(row, f"ZLDesc_{t_name}", t_desc, 168, 10, size=11, color="#A3A3A4")
            self.add_pill(
                row,
                f"ZLAct_{t_name}",
                t_cmd,
                634,
                6,
                74,
                24,
                bg="#FFFFFF" if is_sel else "#1A1A1A",
                border="#FFFFFF" if is_sel else "#333333",
                fg="#000000" if is_sel else "#A3A3A4",
                font_size=9.5,
            )
            ty += 40.0

        self.add_dark_terminal_box(
            zl,
            "ZenLauncherDarkTerminalOut",
            28,
            496,
            720,
            204,
            "#zenOut · INLINE DARK TERMINAL EXECUTION (.SPACE SANDBOX)",
            "● EXIT 0 · 18ms",
            [
                ("you@tincan:~/space$ tincan status", "#FFFFFF"),
                ("room main · 14 peers online · blind relay 200 OK · merkle 7a4c9f", "#F5F5F5"),
                ("you@tincan:~/space$ pytest -q tests/test_dark_mode.py", "#FFFFFF"),
                ("................ [100%] 16 passed in 0.29s (terminal dark contrast 17.4:1)", "#FFFFFF"),
            ],
            show_tui_tabs=False,
            prompt_line="you@tincan:~/space$ /dark --persist",
        )
        self.add_text(zl, "ZLFoot", "↑ ↓ to move · enter to run in dark terminal · /dark to toggle theme · esc to return to feed", 28, 712, size=11, color="#A3A3A4")

        qb_items = ["Terminal", "Copilot", "Workstation", "Arena", "3D Studio", "Node Studio", "Watch Ad +CR", "● Dark", "All tools ⌘K"]
        qx = 48.0
        for q_lbl in qb_items:
            qw = len(q_lbl) * 7.2 + 22
            is_dark_btn = "Dark" in q_lbl or "Terminal" in q_lbl
            self.add_pill(
                root,
                f"ZenQuick_{q_lbl}",
                q_lbl,
                qx,
                844,
                qw,
                30,
                bg="#000000" if is_dark_btn else "#131313",
                border="#FFFFFF" if is_dark_btn else "#333333",
                fg="#FFFFFF" if is_dark_btn else "#F5F5F5",
                font_size=10.5,
            )
            qx += qw + 8.0
        return root

    # -------------------------------------------------------------------------
    # Bespoke Artboard 02: Dedicated Dark Terminal, Harnesses & Live PTY TUI
    # -------------------------------------------------------------------------
    def build_artboard_02_dark_terminal(self, gx: float, gy: float) -> int:
        root, win = self.add_shell_topbar_and_window(
            "02 · Dedicated Dark Terminal, Coding Harnesses, Live PTY TUI & One-Click Install (#win-terminal)",
            gx,
            gy,
            active_route="/terminal",
            win_title="Terminal · Shell, Harnesses & Live PTY TUI",
            win_badge="DARK TERMINAL",
            win_meta="14:41 · ~/space · merkle 7a4c9f · xterm.js PTY",
        )
        hbar = self.add_frame(win, "TermHarnessBar", 0, 45, 1400, 44, fill="#121212", stroke=None)
        self.add_rect(hbar, "HBarLine", 0, 43, 1400, 1, fill="#2E2E2E")
        self.add_text(hbar, "HBarLbl", "HARNESSES:", 18, 15, size=10.5, color="#A3A3A4", font_family="JetBrains Mono", font_style="Bold")
        h_pills = [
            ("Auto Best", True),
            ("Antigravity (agy)", False),
            ("Claude Code", True),
            ("OpenCode", False),
            ("DSX (Fallback)", False),
            ("+ All (6)", False),
        ]
        hx = 108.0
        for hp_lbl, hp_act in h_pills:
            pw = len(hp_lbl) * 6.8 + 22
            self.add_pill(
                hbar,
                f"Harness_{hp_lbl}",
                hp_lbl,
                hx,
                9,
                pw,
                26,
                bg="#FFFFFF" if hp_act else "#181818",
                border="#FFFFFF" if hp_act else "#363636",
                fg="#000000" if hp_act else "#F5F5F5",
                font_size=10.0,
            )
            hx += pw + 8.0
        self.add_pill(hbar, "BtnWorkstationFiles", "Workstation Files ↗", 1070, 9, 154, 26, bg="#181818", border="#363636", fg="#F5F5F5", font_size=10.0)
        self.add_pill(hbar, "BtnOneClickInstall", "▶ One-Click Install", 1232, 9, 150, 26, bg="#000000", border="#FFFFFF", fg="#FFFFFF", font_size=10.0)

        self.add_dark_terminal_box(
            win,
            "PrimaryTinCanShellDark",
            18,
            104,
            674,
            630,
            "TinCanShell (.tcsh)",
            "● READY · ~/space",
            [
                ("Commands run against your .space: ls, cat, open, tree, run, py, brew, harnesses, tui, ask, theme", "#737373"),
                ("you@tincan:~/space$ harnesses", "#FFFFFF"),
                ("  [1] claude-code  v1.0.24   READY (OpenRouter ANTHROPIC_BASE_URL bridge)", "#F5F5F5"),
                ("  [2] antigravity  v2.0.0    READY (agy non-interactive + Context Palace)", "#F5F5F5"),
                ("  [3] opencode     v0.4.12   READY (opencode-ai --model gemini-2.5-flash)", "#F5F5F5"),
                ("  [4] dsx          v1.2.0    READY (NoJuanNobody/dsx headless fallback)", "#F5F5F5"),
                ("  [5] codex        v0.1.9    READY (CODEX_HOME isolated .space sandbox)", "#F5F5F5"),
                ("  [6] goose        v1.0.4    READY (GOOSE_PROVIDER=openrouter)", "#F5F5F5"),
                ("you@tincan:~/space$ brew install tincan context-palace", "#FFFFFF"),
                ("  ==> Tapping NoJuanNobody/tap from Railway Blind Relay...", "#A3A3A4"),
                ("  ==> Pouring tincan-2.2.0.arm64_sequoia.bottle.tar.gz", "#F5F5F5"),
                ("  [OK] /opt/homebrew/Cellar/tincan/2.2.0: 21 commands + 6 skills (+35 XP)", "#FFFFFF"),
                ("you@tincan:~/space$ tree", "#FFFFFF"),
                ("  ~/space · alejandro (merkle 7a4c9f)", "#F5F5F5"),
                ("  ├── src/window_chrome.py   (18.4K · Dark Mode + Celadon tokens)", "#F5F5F5"),
                ("  ├── src/shell_component.py (16.2K · Pitch-Black .tcsh default)", "#F5F5F5"),
                ("  ├── models3d/pod_v2.glb    (3.8M  · Hyper3D Rodin v2 Smooth)", "#F5F5F5"),
                ("  └── designs/tincan_dark_mode_system.figcraft (12 Dark Artboards)", "#FFFFFF"),
                ("you@tincan:~/space$ theme status", "#FFFFFF"),
                ("  [theme] Active: dark (Monochrome Black & White) · Terminal: #000000 Pitch-Black", "#FFFFFF"),
                ("you@tincan:~/space$ tincan actions", "#FFFFFF"),
                ("  [HITL Gate] 0 pending unapproved remote mutations · enclave locked", "#F5F5F5"),
            ],
            show_tui_tabs=True,
            prompt_line='you@tincan:~/space$ claude "Audit dark mode contrast across all 17 windows"',
        )

        self.add_dark_terminal_box(
            win,
            "LivePtyTuiSessionDark",
            708,
            104,
            674,
            408,
            "xterm.js PTY TUI (.tcsh-tui) · WebSocket /api/terminal/pty/ws",
            "● TUI: claude-code",
            [
                ("[*] Mounting user:alejandro.space and launching claude-code TUI…", "#FFFFFF"),
                ("[*] Injected .tincan/SPACE_CONTEXT.md + 21 Context Palace facts", "#FFFFFF"),
                ("╭─ Claude Code (Anthropic / OpenRouter Pool) ─────────────────────────╮", "#FFFFFF"),
                ("│ > Make sure people can immediately see the TinCan terminal is dark │", "#F5F5F5"),
                ("│                                                                     │", "#F5F5F5"),
                ("│ ● Updated shell_component.py: .tcsh background #050505 -> #000000   │", "#FFFFFF"),
                ("│ ● Added [ DARK ] / [ LIGHT ] toggle to window_chrome.py & HUD       │", "#FFFFFF"),
                ("│ ● Verified 12 FigCraft Dark Mode artboards + Master Contact Sheet   │", "#FFFFFF"),
                ("│ [Synced to .space: /src/shell_component.py, /src/window_chrome.py]  │", "#D4D4D4"),
                ("╰─────────────────────────────────────────────────────────────────────╯", "#FFFFFF"),
                ("claude> Run pytest suite in .space sandbox [y/n]: y", "#F5F5F5"),
                ("65 passed in 1.12s · 0 warnings · merkle root updated -> 7a4c9f", "#FFFFFF"),
            ],
            show_tui_tabs=False,
            prompt_line="claude@tincan:~/space> /sync --commit",
        )

        ic = self.add_frame(
            win,
            "OneClickTerminalInstallCard",
            708,
            526,
            674,
            208,
            fill="#141414",
            stroke="#FFFFFF",
            stroke_weight=1.5,
            radius=12,
            clip=True,
        )
        self.add_text(ic, "ICHdr", "ONE-CLICK TERMINAL INSTALLER (install_card.py · data-tc-install)", 18, 14, size=11, color="#FFFFFF", font_family="JetBrains Mono", font_style="Bold")
        self.add_pill(ic, "ICTabBrew", "● brew", 18, 38, 76, 24, bg="#FFFFFF", border="#FFFFFF", fg="#000000", font_size=10)
        self.add_pill(ic, "ICTabCurl", "curl | bash", 100, 38, 96, 24, bg="#1A1A1A", border="#333333", fg="#F5F5F5", font_size=10)
        self.add_pill(ic, "ICTabNpx", "npx skills", 202, 38, 92, 24, bg="#1A1A1A", border="#333333", fg="#F5F5F5", font_size=10)
        self.add_pill(ic, "ICTabChat", "tincan ask", 300, 38, 92, 24, bg="#1A1A1A", border="#333333", fg="#F5F5F5", font_size=10)

        cmd_box = self.add_frame(ic, "ICDarkCmdBox", 18, 74, 638, 72, fill="#000000", stroke="#FFFFFF", radius=10)
        self.add_text(
            cmd_box,
            "ICCmdLine1",
            "$ brew install https://iot-federated-agent-memory-production.up.railway.app/Formula/tincan.rb",
            14,
            14,
            size=10.5,
            color="#FFFFFF",
            font_family="JetBrains Mono",
        )
        self.add_text(
            cmd_box,
            "ICCmdLine2",
            "$ npx skills add NoJuanNobody/tincan-skills -g -y && tincan start",
            14,
            40,
            size=10.5,
            color="#F5F5F5",
            font_family="JetBrains Mono",
        )
        self.add_pill(ic, "ICBtnCopy", "Copy Install Command", 18, 160, 188, 32, bg="#FFFFFF", border="#FFFFFF", fg="#000000", font_size=10.5)
        self.add_pill(ic, "ICBtnRunHere", "▶ Run in Dark Terminal", 216, 160, 184, 32, bg="#000000", border="#FFFFFF", fg="#FFFFFF", font_size=10.5)
        self.add_pill(ic, "ICBtnMacCmd", "↓ Install-TinCan.command", 410, 160, 246, 32, bg="#1A1A1A", border="#383838", fg="#F5F5F5", font_size=10.5)

        self.add_rect(win, "TermFootBg", 0, 748, 1400, 44, fill="#0C0C0C")
        self.add_rect(win, "TermFootLine", 0, 748, 1400, 1, fill="#2E2E2E")
        self.add_text(win, "TermFootL", "merkle 7a4c9f  |  ~/space  |  PTY WebSocket: CONNECTED  |  Terminal Theme: #000000 Pitch-Black", 20, 764, size=11, color="#FFFFFF", font_family="JetBrains Mono")
        self.add_text(win, "TermFootR", "Harnesses: claude-code · antigravity · opencode · dsx · codex · goose", 930, 764, size=11, color="#A3A3A4", font_family="JetBrains Mono")
        return root

    # -------------------------------------------------------------------------
    # Bespoke Artboard 05: Workstation IDE (.space Explorer, Editor & Docked Dark Terminal)
    # -------------------------------------------------------------------------
    def build_artboard_05_workstation_ide(self, gx: float, gy: float) -> int:
        root, win = self.add_shell_topbar_and_window(
            "05 · Workstation IDE · .space VFS Explorer, Code Editor & Docked Dark Terminal (#win-agentspace)",
            gx,
            gy,
            active_route="/workstation",
            win_title="Workstation · .space VFS Explorer & Docked Dark Terminal",
            win_badge="VFS · 3D · IDE",
            win_meta="user:alejandro.space · merkle 7a4c9f · S3 + Drive Mirror",
        )
        tbar = self.add_frame(win, "IdeScopeToolbar", 0, 45, 1400, 42, fill="#121212", stroke=None)
        self.add_rect(tbar, "IdeTBarLine", 0, 41, 1400, 1, fill="#2E2E2E")
        self.add_pill(tbar, "ScopeUser", "● User Space (alejandro)", 16, 8, 184, 26, bg="#FFFFFF", border="#FFFFFF", fg="#000000", font_size=10)
        self.add_pill(tbar, "ScopeTopic", "Topic Space (#architecture)", 208, 8, 192, 26, bg="#181818", border="#363636", fg="#F5F5F5", font_size=10)
        self.add_pill(tbar, "ScopeDynamic", "Sandbox (ephemeral)", 408, 8, 156, 26, bg="#181818", border="#363636", fg="#F5F5F5", font_size=10)
        self.add_pill(tbar, "BtnNewFile", "+ New File", 820, 8, 92, 26, bg="#181818", border="#363636", fg="#F5F5F5", font_size=10)
        self.add_pill(tbar, "BtnFigCraftWasm", "[FIG] Open in FigCraft Wasm", 920, 8, 188, 26, bg="#181818", border="#FFFFFF", fg="#FFFFFF", font_size=10)
        self.add_pill(tbar, "Btn3DStudio", "● 3D Studio", 1114, 8, 102, 26, bg="#181818", border="#363636", fg="#F5F5F5", font_size=10)
        self.add_pill(tbar, "BtnToggleTerm", "Docked Terminal: ON ●", 1224, 8, 160, 26, bg="#000000", border="#FFFFFF", fg="#FFFFFF", font_size=10)

        exp = self.add_frame(win, "RangerExplorerPane", 0, 87, 310, 668, fill="#0F0F0F", stroke=None)
        self.add_rect(exp, "ExpRightLine", 309, 0, 1, 668, fill="#2E2E2E")
        self.add_text(exp, "ExpHdr1", "EXPLORER · ~/SPACE VFS (MERKLE 7A4C9F)", 16, 14, size=10, color="#FFFFFF", font_family="JetBrains Mono", font_style="Bold")
        files = [
            ("[PY] /src/window_chrome.py", "18.4 KB", True),
            ("[PY] /src/shell_component.py", "16.2 KB", False),
            ("[PY] /src/ai_home_shell.py", "33.7 KB", False),
            ("[PY] /src/node_studio_ui.py", "105 KB", False),
            ("[FIG] /designs/dark_mode.figcraft", "164 KB", False),
            ("[3D] /models3d/drone_pod_v2.glb", "3.8 MB", False),
            ("[MD] /notes/chassis_spec.md", "4.2 KB", False),
            ("[PY] /tests/test_dark_mode.py", "9.6 KB", False),
        ]
        fy = 40.0
        for f_name, f_sz, f_act in files:
            frow = self.add_frame(
                exp,
                f"FileRow_{f_name}",
                10,
                fy,
                290,
                30,
                fill="#1C1C1C" if f_act else "#141414",
                stroke="#FFFFFF" if f_act else "#262626",
                radius=6,
            )
            self.add_text(frow, f"FN_{f_name}", f_name, 10, 7, size=10.0, color="#F5F5F5" if f_act else "#D4D4D4", font_family="JetBrains Mono")
            self.add_text(frow, f"FS_{f_name}", f_sz, 236, 8, size=9.5, color="#FFFFFF" if f_act else "#737373", font_family="JetBrains Mono")
            fy += 35.0

        self.add_text(exp, "ExpHdr2", "LOCAL DRIVE MIRROR (READ-ONLY)", 16, 336, size=10, color="#A3A3A4", font_family="JetBrains Mono", font_style="Bold")
        drives = [
            "[DIR] ~/dev/iot-federated-agent-memory",
            "[WAL] ~/.context_palace/context_lake.db",
            "[DIR] ~/Desktop/screenshots",
        ]
        dy = 360.0
        for d_path in drives:
            drow = self.add_frame(exp, f"Drive_{d_path}", 10, dy, 290, 28, fill="#121212", stroke="#262626", radius=6)
            self.add_text(drow, f"DT_{d_path}", d_path, 10, 7, size=10, color="#A3A3A4", font_family="JetBrains Mono")
            dy += 33.0

        wcard = self.add_frame(exp, "WasmPreviewCard", 10, 474, 290, 180, fill="#050505", stroke="#2E2E2E", radius=10)
        self.add_text(wcard, "WCHdr", "ARTCRAFT & GLB QUICK PREVIEW", 12, 12, size=10, color="#FFFFFF", font_family="JetBrains Mono", font_style="Bold")
        self.add_text(wcard, "WCBody", "Active: tincan_dark_mode.figcraft\n12 Dark Mode Artboards synced\nGLB Rig: drone_pod_v2.glb (Manifold)", 12, 36, size=10.5, color="#F5F5F5", font_family="JetBrains Mono")
        self.add_pill(wcard, "WCBtn1", "▶ Run in Sandbox", 12, 136, 130, 30, bg="#FFFFFF", border="#FFFFFF", fg="#000000", font_size=10)
        self.add_pill(wcard, "WCBtn2", "Apply AI Patch", 150, 136, 126, 30, bg="#181818", border="#383838", fg="#F5F5F5", font_size=10)

        ed = self.add_frame(win, "IdeCodeEditorPane", 310, 87, 1090, 378, fill="#080808", stroke=None)
        self.add_rect(ed, "EdTabBarBg", 0, 0, 1090, 36, fill="#121212")
        self.add_rect(ed, "EdTabBarLine", 0, 36, 1090, 1, fill="#2E2E2E")
        self.add_pill(ed, "Tab1", "[PY] window_chrome.py ● ×", 12, 5, 190, 26, bg="#000000", border="#FFFFFF", fg="#FFFFFF", font_size=10)
        self.add_pill(ed, "Tab2", "[PY] shell_component.py ×", 210, 5, 186, 26, bg="#171717", border="#2E2E2E", fg="#A3A3A4", font_size=10)
        self.add_pill(ed, "Tab3", "[FIG] tincan_dark_mode.figcraft ×", 404, 5, 224, 26, bg="#171717", border="#2E2E2E", fg="#A3A3A4", font_size=10)
        self.add_pill(ed, "EdSaveBtn", "✓ Save to .space [⌘S]", 912, 5, 162, 26, bg="#FFFFFF", border="#FFFFFF", fg="#000000", font_size=10)

        code_lines = [
            ('01  /* TinCan 2.2 · Monochrome Black & White Dark Mode + Always-Dark Terminal (.tcsh) */', "#737373"),
            ('02  html[data-theme="dark"], body.tc-dark {', "#FFFFFF"),
            ('03    --tc-bg: #080808; --tc-ink: #f5f5f5; --tc-card: #141414; --tc-paper: #1a1a1a;', "#F5F5F5"),
            ('04    --tc-muted: #a3a3a3; --tc-faint: #737373; --tc-line: rgba(255, 255, 255, 0.18);', "#F5F5F5"),
            ('05    --tc-term-bg: #000000; --tc-term-fg: #f5f5f5; --tc-term-accent: #ffffff;', "#FFFFFF"),
            ('06  }', "#FFFFFF"),
            ('07  /* Every terminal in TinCan is pitch-dark (#000000) so users see it immediately */', "#737373"),
            ('08  .tcsh {', "#D4D4D4"),
            ('09    background: #000000 !important; color: #f5f5f5 !important;', "#FFFFFF"),
            ('10    border: 1.5px solid #ffffff !important; border-radius: 12px;', "#F5F5F5"),
            ('11  }', "#D4D4D4"),
            ('12  .tcsh-bar, .tcsh-row { background: #0c0c0c !important; color: #a3a3a3 !important; }', "#F5F5F5"),
            ('13  .tcsh-ps { color: #ffffff !important; font-weight: 700; }', "#FFFFFF"),
        ]
        cy = 50.0
        for c_txt, c_col in code_lines:
            self.add_text(ed, f"Code_{cy}", c_txt, 18, cy, size=11.5, color=c_col, font_family="JetBrains Mono")
            cy += 23.0

        self.add_dark_terminal_box(
            win,
            "IdeDockedDarkTerminal",
            318,
            470,
            1074,
            278,
            "DOCKED WORKSTATION TERMINAL (#ideTermMount)",
            "● TUI + SHELL READY",
            [
                ("you@tincan:~/space$ pytest -q tests/test_terminal_space_ide.py tests/test_mesh_os_ui.py", "#FFFFFF"),
                (".............. [100%] 14 passed in 0.34s · .tcsh pitch-black terminal verified", "#FFFFFF"),
                ("you@tincan:~/space$ open /src/shell_component.py", "#FFFFFF"),
                ("Opened /src/shell_component.py in Workstation Editor (merkle 7a4c9f).", "#F5F5F5"),
                ('you@tincan:~/space$ ask "Verify dark terminal visibility across all 12 FigCraft artboards"', "#FFFFFF"),
                ("[agent] All 12 FigCraft Dark Mode artboards render #000000 terminals with 17.4:1 contrast.", "#FFFFFF"),
            ],
            show_tui_tabs=True,
            prompt_line="you@tincan:~/space$ git status --short && tincan status",
        )

        self.add_rect(win, "IdeFootBg", 0, 755, 1400, 37, fill="#0C0C0C")
        self.add_rect(win, "IdeFootLine", 0, 755, 1400, 1, fill="#2E2E2E")
        self.add_text(win, "IdeFootL", "READY  |  user:alejandro  |  /src/window_chrome.py  |  UTF-8 · Python/CSS  |  merkle 7a4c9f", 18, 768, size=11, color="#FFFFFF", font_family="JetBrains Mono")
        self.add_text(win, "IdeFootR", "Docked Dark Terminal: #000000  |  Ln 9, Col 42", 1090, 768, size=11, color="#A3A3A4", font_family="JetBrains Mono")
        return root

    # -------------------------------------------------------------------------
    # Bespoke Artboard 10: Talk Comms, DM Roster & WebRTC Dark Terminal Screenshare
    # -------------------------------------------------------------------------
    def build_artboard_10_comms_webrtc(self, gx: float, gy: float) -> int:
        root, win = self.add_shell_topbar_and_window(
            "10 · Talk · Encrypted Channels, DM Roster & Sub-80ms WebRTC Dark Terminal Screenshare (#win-comms + #win-call)",
            gx,
            gy,
            active_route="/talk",
            win_title="Talk & WebRTC Room · Channels & Dark Terminal Share",
            win_badge="E2EE + WEBRTC",
            win_meta="room: main · 4 peers · XSalsa20-Poly1305 · Kokoro-82M",
        )
        side = self.add_frame(win, "CommsSidebar", 16, 60, 260, 714, fill="#131313", stroke="#2E2E2E", radius=12)
        self.add_text(side, "ChHdr", "TEXT CHANNELS", 14, 16, size=10, color="#FFFFFF", font_family="JetBrains Mono", font_style="Bold")
        channels = [("# main", "12", True), ("# architecture", "4", False), ("# cyberspace", "9", False), ("# arena", "3", False)]
        cy = 40.0
        for ch_name, ch_cnt, ch_act in channels:
            crow = self.add_frame(side, f"Ch_{ch_name}", 10, cy, 240, 30, fill="#FFFFFF" if ch_act else "#181818", stroke="#FFFFFF" if ch_act else "#2E2E2E", radius=6)
            self.add_text(crow, f"ChN_{ch_name}", ch_name, 10, 7, size=11, color="#000000" if ch_act else "#F5F5F5", font_family="JetBrains Mono", font_style="Bold")
            self.add_text(crow, f"ChC_{ch_name}", ch_cnt, 212, 8, size=10, color="#000000" if ch_act else "#A3A3A4", font_family="JetBrains Mono")
            cy += 36.0

        self.add_text(side, "DmHdr", "PEOPLE IN ROOM (DM ROSTER)", 14, 198, size=10, color="#FFFFFF", font_family="JetBrains Mono", font_style="Bold")
        peers = [
            ("● @alejandro (You · L5)", "Mac Studio", "#FFFFFF"),
            ("● @alice (Verified TOFU)", "18ms · Call", "#FFFFFF"),
            ("● @bob (Mentor · Voice ON)", "24ms · Call", "#FFFFFF"),
            ("[AI] @claude-brain", "0ms · Pool", "#D4D4D4"),
            ("[AI] @verifier-agent", "Attested", "#A3A3A4"),
        ]
        py = 224.0
        for p_name, p_sub, p_col in peers:
            prow = self.add_frame(side, f"Peer_{p_name}", 10, py, 240, 42, fill="#171717", stroke="#2E2E2E", radius=8)
            self.add_text(prow, f"PN_{p_name}", p_name, 10, 6, size=10.5, color=p_col, font_family="JetBrains Mono", font_style="Bold")
            self.add_text(prow, f"PS_{p_name}", p_sub, 10, 23, size=9.5, color="#A3A3A4", font_family="JetBrains Mono")
            py += 48.0

        self.add_dark_terminal_box(
            side,
            "CommsKokoroCliBox",
            10,
            474,
            240,
            228,
            "tincan say · TTS",
            "● -14 LUFS",
            [
                ("you@tincan:~$ tincan say", "#FFFFFF"),
                ('  "Dark terminal screen', "#F5F5F5"),
                ('   share is live" --to @alice', "#F5F5F5"),
                ("[kokoro] af_heart · 1.8s", "#FFFFFF"),
                ("[seal] NaCl box -> @alice", "#FFFFFF"),
            ],
            show_tui_tabs=False,
            prompt_line="tincan send @alice ",
        )

        chat = self.add_frame(win, "CommsChatPane", 290, 60, 480, 714, fill="#131313", stroke="#2E2E2E", radius=12)
        self.add_rect(chat, "ChatHdrBg", 0, 0, 480, 42, fill="#181818")
        self.add_text(chat, "ChatTargetBanner", "[E2EE] #main · NaCl Sealed Room Stream (Zero-Knowledge Relay)", 14, 13, size=10.5, color="#FFFFFF", font_family="JetBrains Mono", font_style="Bold")

        msgs = [
            ("@alice · 14:38 · TOFU Verified [ed25519:9a4f]", "Can everyone see the new Dark Mode terminal on the WebRTC screenshare?", "#F5F5F5"),
            ("@alejandro · 14:39 · Mac Studio M1 Max [L5 Sovereign]", "Yes! Switched .tcsh to #000000 pitch-black with #FFFFFF white borders.", "#FFFFFF"),
            ("[VOICE] Kokoro-82M Neural Voice Note (af_heart · 0:12 · -14.0 LUFS)", "▂▃▅▇█▆▄▂▅▇█▅▃▂▄▆█▇▄▂▃▅▇▅▃▂  [✓ Audited & Played]", "#D4D4D4"),
            ("[AI] @claude-brain · 14:40 · Context Palace Capsule Injected", "Synced all 12 FigCraft Dark Mode artboards to tincan_dark_mode_system.figcraft.", "#F5F5F5"),
        ]
        my = 56.0
        for m_hdr, m_body, m_col in msgs:
            mcard = self.add_frame(chat, f"Msg_{my}", 14, my, 452, 86, fill="#1A1A1A", stroke="#2E2E2E", radius=10)
            self.add_text(mcard, f"MH_{my}", m_hdr, 12, 10, size=10, color="#FFFFFF", font_family="JetBrains Mono", font_style="Bold")
            self.add_text(mcard, f"MB_{my}", m_body, 12, 34, size=10.5, color=m_col)
            my += 98.0

        self.add_dark_terminal_box(
            chat,
            "ChatTerminalSnippet",
            14,
            452,
            452,
            194,
            "SHARED TERMINAL SNAPSHOT · @alejandro",
            "● MERKLE 7A4C9F",
            [
                ("you@tincan:~/space$ tincan ping @alice", "#FFFFFF"),
                ("  PONG from @alice (tc:7x9k...2m) · 18ms WebRTC data channel", "#FFFFFF"),
                ("you@tincan:~/space$ tincan mentor status", "#FFFFFF"),
                ("  Mentor: @bob (voice-allowed) · 0 pending guidance steps", "#F5F5F5"),
            ],
            show_tui_tabs=False,
            prompt_line="you@tincan:~/space$ ",
        )
        cinput = self.add_frame(chat, "ChatInputBox", 14, 658, 452, 42, fill="#000000", stroke="#FFFFFF", radius=10)
        self.add_text(cinput, "ChatInputTxt", "Message #main or @peer (NaCl sealed)...", 14, 13, size=11.5, color="#A3A3A4")
        self.add_pill(cinput, "ChatSendBtn", "Send ↵", 374, 8, 68, 26, bg="#FFFFFF", border="#FFFFFF", fg="#000000", font_size=10)

        call = self.add_frame(win, "WebRtcCallPane", 784, 60, 600, 714, fill="#131313", stroke="#2E2E2E", radius=12)
        self.add_rect(call, "CallHdrBg", 0, 0, 600, 42, fill="#181818")
        self.add_text(call, "CallHdrTxt", "[WEBRTC] #win-call · Sub-80ms Room (60fps Dark Terminal Screenshare)", 16, 13, size=10.5, color="#FFFFFF", font_family="JetBrains Mono", font_style="Bold")

        cam1 = self.add_frame(call, "CamTile1", 16, 56, 276, 150, fill="#050505", stroke="#FFFFFF", radius=10)
        self.add_text(cam1, "Cam1Title", "● @alejandro · Mac Studio M1 Max", 12, 12, size=10.5, color="#FFFFFF", font_family="JetBrains Mono", font_style="Bold")
        self.add_text(cam1, "Cam1Sub", "1080p60 · Sharing Dark Terminal · -14 LUFS", 12, 122, size=9.5, color="#A3A3A4", font_family="JetBrains Mono")

        cam2 = self.add_frame(call, "CamTile2", 308, 56, 276, 150, fill="#050505", stroke="#2E2E2E", radius=10)
        self.add_text(cam2, "Cam2Title", "● @alice · MacBook Pro M5", 12, 12, size=10.5, color="#F5F5F5", font_family="JetBrains Mono", font_style="Bold")
        self.add_text(cam2, "Cam2Sub", "1080p60 · 18ms RTT · Opus Audio Active", 12, 122, size=9.5, color="#A3A3A4", font_family="JetBrains Mono")

        self.add_dark_terminal_box(
            call,
            "WebRtcLiveDarkTerminalScreenshare",
            16,
            220,
            568,
            428,
            "WEBRTC 60FPS DARK TERMINAL SHARE",
            "● 1080p60 · 18ms",
            [
                ("you@tincan:~/space$ tincan call --room main --screen", "#FFFFFF"),
                ("  [webrtc] Streaming 60fps desktop + dark terminal over P2P SRTP/DTLS", "#FFFFFF"),
                ("you@tincan:~/space$ pytest -q", "#FFFFFF"),
                ("  ................................................................. [100%]", "#FFFFFF"),
                ("  65 passed in 1.18s (Dark Mode + Dark Terminal + FigCraft verified)", "#F5F5F5"),
                ("you@tincan:~/space$ tincan credits --summary", "#FFFFFF"),
                ("  balance: 5,000 CR ($5.00 USD) · local Ollama saved: $14.80 · subs: $0", "#F5F5F5"),
                ("you@tincan:~/space$ tincan mentor guide @alice 'Inspect dark terminal CSS'", "#FFFFFF"),
                ("  [mentor] Sent approval-gated guidance step #4 to @alice (+50 XP)", "#FFFFFF"),
            ],
            show_tui_tabs=True,
            prompt_line="you@tincan:~/space$ tincan status --peers",
        )

        cbtns = [
            ("[MIC] Mute", False),
            ("[CAM] On", False),
            ("[SCREEN] Dark Terminal ●", True),
            ("[TTS] Kokoro", False),
            ("Raise Hand", False),
            ("Leave", False),
        ]
        bx = 16.0
        for b_lbl, b_act in cbtns:
            bw = len(b_lbl) * 6.5 + 18
            self.add_pill(
                call,
                f"CallBtn_{b_lbl}",
                b_lbl,
                bx,
                664,
                bw,
                32,
                bg="#FFFFFF" if b_act else "#1A1A1A",
                border="#FFFFFF" if b_act else "#383838",
                fg="#000000" if b_act else "#F5F5F5",
                font_size=10,
            )
            bx += bw + 8.0
        return root

    # -------------------------------------------------------------------------
    # Bespoke Artboard 12: System & Cross-Platform Dark Suite
    # -------------------------------------------------------------------------
    def build_artboard_12_system_cross_platform(self, gx: float, gy: float) -> int:
        root, win = self.add_shell_topbar_and_window(
            "12 · System & Cross-Platform Dark Suite · Network, Quests, Browser, Localhost, Moderator, Fono, iOS & Car UI",
            gx,
            gy,
            active_route="/terminal",
            win_title="System Windows & Cross-Platform Dark Mode Suite",
            win_badge="FULL COVERAGE",
            win_meta="#win-network · #win-quests · #win-browser · #win-localhost · /fono · /ios · /car",
        )
        p1 = self.add_frame(win, "Panel_Network", 16, 58, 444, 350, fill="#131313", stroke="#2E2E2E", radius=12)
        self.add_text(p1, "P1Hdr", "[NET] #win-network · ACTIVE MESH NODES & LEADERBOARD", 14, 14, size=10.5, color="#FFFFFF", font_family="JetBrains Mono", font_style="Bold")
        nodes_info = [
            ("1. @alejandro · Mac Studio M1 Max", "L5 Sovereign · 4,850 XP · 12ms", "#FFFFFF"),
            ("2. @alice · MacBook Pro M5", "L4 Gossip · 2,340 XP · 18ms", "#F5F5F5"),
            ("3. @bob · Linux Homelab Mini-PC", "L4 Gossip · 1,920 XP · 24ms", "#F5F5F5"),
            ("4. @claude-brain · OpenRouter Pool", "Agent Node · 0 CR Local Bridge", "#D4D4D4"),
        ]
        ny = 42.0
        for n_title, n_sub, n_col in nodes_info:
            nrow = self.add_frame(p1, f"NetNode_{ny}", 12, ny, 420, 44, fill="#181818", stroke="#2E2E2E", radius=8)
            self.add_text(nrow, f"NT_{ny}", n_title, 10, 6, size=10.5, color=n_col, font_family="JetBrains Mono", font_style="Bold")
            self.add_text(nrow, f"NS_{ny}", n_sub, 10, 24, size=9.5, color="#A3A3A4", font_family="JetBrains Mono")
            ny += 50.0
        self.add_dark_terminal_box(
            p1,
            "NetPingDarkTerm",
            12,
            244,
            420,
            94,
            "tincan ping --mesh",
            "● 4 PEERS OK",
            [
                ("you@tincan:~$ tincan status --json", "#FFFFFF"),
                ('{"peers":4,"rtt_ms":18,"crdt":"converged"}', "#F5F5F5"),
            ],
            show_tui_tabs=False,
            prompt_line=None,
        )

        p2 = self.add_frame(win, "Panel_Quests", 478, 58, 444, 350, fill="#131313", stroke="#2E2E2E", radius=12)
        self.add_text(p2, "P2Hdr", "[XP] #win-quests · L1->L5 FEDERATED EDGE READINESS", 14, 14, size=10.5, color="#FFFFFF", font_family="JetBrains Mono", font_style="Bold")
        self.add_rect(p2, "XPBarTrack", 14, 42, 416, 10, fill="#222222", radius=5)
        self.add_rect(p2, "XPBarFill", 14, 42, 360, 10, fill="#FFFFFF", radius=5)
        self.add_text(p2, "XPTxt", "Tier L5 Sovereign Mesh · 4,850 / 5,000 XP (97% Complete)", 14, 58, size=10.5, color="#F5F5F5", font_family="JetBrains Mono")
        quests = [
            ("✓ First TOFU Ed25519 Handshake", "+100 XP · Completed", "#FFFFFF"),
            ("✓ Blind Arena Local-vs-Cloud Vote", "+150 XP · Completed", "#FFFFFF"),
            ("✓ Dark Terminal Harnesses & PTY TUI", "+250 XP · Completed", "#FFFFFF"),
            ("● Publish Dark Mode FigCraft System", "+500 XP · Active Goal", "#D4D4D4"),
        ]
        qy = 84.0
        for q_t, q_s, q_c in quests:
            qrow = self.add_frame(p2, f"Quest_{qy}", 12, qy, 420, 38, fill="#181818", stroke="#2E2E2E", radius=8)
            self.add_text(qrow, f"QT_{qy}", q_t, 10, 11, size=10.5, color=q_c, font_family="JetBrains Mono", font_style="Bold")
            self.add_text(qrow, f"QS_{qy}", q_s, 272, 12, size=9.5, color="#A3A3A4", font_family="JetBrains Mono")
            qy += 43.0
        self.add_dark_terminal_box(
            p2,
            "QuestCliTerm",
            12,
            260,
            420,
            78,
            "tincan xp --award dark_terminal",
            "● +250 XP",
            [("you@tincan:~$ tincan brew install context-palace -> +35 XP", "#FFFFFF")],
            show_tui_tabs=False,
            prompt_line=None,
        )

        p3 = self.add_frame(win, "Panel_BrowserLocalhost", 940, 58, 444, 350, fill="#131313", stroke="#2E2E2E", radius=12)
        self.add_text(p3, "P3Hdr", "[WEB] #win-browser & #win-localhost · DEV SERVER PROXY", 14, 14, size=10.5, color="#FFFFFF", font_family="JetBrains Mono", font_style="Bold")
        url_bar = self.add_frame(p3, "BrowserUrlBar", 12, 38, 420, 28, fill="#000000", stroke="#FFFFFF", radius=6)
        self.add_text(url_bar, "UrlTxt", "[HTTPS] tincan.local/localhost/3000/mesh?theme=dark", 10, 7, size=10, color="#FFFFFF", font_family="JetBrains Mono")
        bview = self.add_frame(p3, "BrowserViewport", 12, 74, 420, 96, fill="#080808", stroke="#2E2E2E", radius=8)
        self.add_text(bview, "BVTitle", "Playwright Headless Chromium + Localhost Port Proxy (:3000 / :8080)", 12, 12, size=10.5, color="#F5F5F5", font_style="Bold")
        self.add_text(bview, "BVSub", "Live DOM snapshot & screenshot capture synced to .space/images/", 12, 36, size=10, color="#A3A3A4")
        self.add_pill(bview, "BVBtn1", "Capture to .space", 12, 60, 146, 24, bg="#FFFFFF", border="#FFFFFF", fg="#000000", font_size=9.5)
        self.add_pill(bview, "BVBtn2", "↗ Pop Out :3000", 166, 60, 126, 24, bg="#181818", border="#363636", fg="#F5F5F5", font_size=9.5)

        self.add_dark_terminal_box(
            p3,
            "LocalhostDarkServerTerm",
            12,
            180,
            420,
            158,
            "LOCALHOST DEV SERVER (/localhost/8080)",
            "● :8080 OK",
            [
                ("you@tincan:~/space$ tincan serve --port 8080 --db :memory:", "#FFFFFF"),
                ("[relay] Zero-knowledge Blind Relay listening on 127.0.0.1:8080", "#FFFFFF"),
                ("GET /mesh?theme=dark 200 OK (1.8ms · gzip · dark terminal active)", "#F5F5F5"),
            ],
            show_tui_tabs=False,
            prompt_line="you@tincan:~/space$ ",
        )

        p4 = self.add_frame(win, "Panel_ModAndIdentityGate", 16, 422, 444, 354, fill="#131313", stroke="#2E2E2E", radius=12)
        self.add_text(p4, "P4Hdr", "[ADMIN] #win-moderator & #accountSetupModal · IDENTITY GATE", 14, 14, size=10.5, color="#FFFFFF", font_family="JetBrains Mono", font_style="Bold")
        gate = self.add_frame(p4, "IdentityGateDarkCard", 12, 40, 420, 176, fill="#0F0F0F", stroke="#FFFFFF", radius=10)
        self.add_text(gate, "GateTitle", "[ID] Citizen Passkey & Ed25519 Identity Attestation", 12, 10, size=11.5, color="#F5F5F5", font_style="Bold")
        self.add_text(gate, "GateF1", "Operator: Alejandro Londono (@nojuannobody) · FAU Z23961745", 12, 34, size=10, color="#A3A3A4", font_family="JetBrains Mono")
        self.add_text(gate, "GateF2", "WebAuthn Passkey: Attested Secure Enclave · Role: Admin Moderator", 12, 54, size=10, color="#FFFFFF", font_family="JetBrains Mono")
        self.add_pill(gate, "GateBtn1", "✓ Enter the Mesh & Attest Identity", 12, 84, 240, 28, bg="#FFFFFF", border="#FFFFFF", fg="#000000", font_size=10)
        self.add_pill(gate, "GateBtn2", "Not now — back to feed", 260, 84, 148, 28, bg="#181818", border="#363636", fg="#A3A3A4", font_size=9.5)
        self.add_text(gate, "ModBroadcast", "Admin Broadcast: [Send Mesh Alert] · Active Peers: 4 · Intel Gate: ON", 12, 128, size=9.5, color="#D4D4D4", font_family="JetBrains Mono")

        self.add_dark_terminal_box(
            p4,
            "ModeratorAuditDarkTerm",
            12,
            226,
            420,
            116,
            "ADMIN GOVERNANCE & HITL GATE",
            "● VERIFIED",
            [
                ("you@tincan:~$ tincan whoami --json", "#FFFFFF"),
                ('{"alias":"alejandro","role":"admin","fau_id":"Z23961745"}', "#F5F5F5"),
            ],
            show_tui_tabs=False,
            prompt_line=None,
        )

        p5 = self.add_frame(win, "Panel_FonoAndIosDark", 478, 422, 444, 354, fill="#131313", stroke="#2E2E2E", radius=12)
        self.add_text(p5, "P5Hdr", "[IOS] AEONIK FONO DARK (/fono) & NATIVE iOS APP DARK (/ios)", 14, 14, size=10.5, color="#FFFFFF", font_family="JetBrains Mono", font_style="Bold")
        ph1 = self.add_frame(p5, "FonoPhoneDark", 14, 40, 200, 300, fill="#080808", stroke="#FFFFFF", radius=18)
        self.add_text(ph1, "Ph1Title", "Aeonik Fono · ● Dark", 14, 12, size=10.5, color="#F5F5F5", font_style="Bold")
        self.add_ellipse(ph1, "FonoGaugeRing", 58, 38, 84, 84, fill=None, stroke="#FFFFFF", stroke_weight=4.0)
        self.add_text(ph1, "FonoGaugeVal", "98%", 84, 70, size=15, color="#FFFFFF", font_family="JetBrains Mono", font_style="Bold")
        self.add_dark_terminal_box(
            ph1,
            "FonoMiniTerm",
            10,
            134,
            180,
            152,
            "Fono Shell",
            "● SSH",
            [
                ("$ tincan ping", "#FFFFFF"),
                ("18ms · relay OK", "#F5F5F5"),
                ("$ tincan credits", "#FFFFFF"),
                ("5,000 CR ($5.00)", "#FFFFFF"),
            ],
            show_tui_tabs=False,
            prompt_line=None,
        )
        ph2 = self.add_frame(p5, "IosPhoneDark", 230, 40, 200, 300, fill="#080808", stroke="#383838", radius=18)
        self.add_text(ph2, "Ph2Title", "iOS 18 · Sealed Inbox ●", 14, 12, size=10.5, color="#F5F5F5", font_style="Bold")
        self.add_frame(ph2, "IosCard1", 10, 38, 180, 42, fill="#161616", stroke="#2E2E2E", radius=8)
        self.add_text(ph2, "IosC1T", "[E2EE] @alice · Verified\nDark terminal looks crisp!", 16, 44, size=9.5, color="#F5F5F5")
        self.add_frame(ph2, "IosCard2", 10, 86, 180, 42, fill="#161616", stroke="#2E2E2E", radius=8)
        self.add_text(ph2, "IosC2T", "[ARENA] Brain Duel +150 XP\nLocal Ollama beat Cloud", 16, 92, size=9.5, color="#FFFFFF")
        self.add_dark_terminal_box(
            ph2,
            "IosMiniTerm",
            10,
            134,
            180,
            152,
            "iOS Shell",
            "● KEY",
            [
                ("$ tincan whoami", "#FFFFFF"),
                ("Secure Enclave Key", "#F5F5F5"),
                ("$ tincan read", "#FFFFFF"),
                ("2 sealed msgs OK", "#FFFFFF"),
            ],
            show_tui_tabs=False,
            prompt_line=None,
        )

        p6 = self.add_frame(win, "Panel_CarHeadUnitDark", 940, 422, 444, 354, fill="#131313", stroke="#2E2E2E", radius=12)
        self.add_text(p6, "P6Hdr", "[CAR] HEAD-UNIT UI · SUMI-DOCK NIGHT MODE (/car · 1280×720)", 14, 14, size=10.5, color="#FFFFFF", font_family="JetBrains Mono", font_style="Bold")
        car = self.add_frame(p6, "CarScreenDark", 12, 40, 420, 174, fill="#050505", stroke="#FFFFFF", radius=12)
        self.add_pill(car, "CarModeDriving", "● DRIVING (LOW-GLARE)", 12, 12, 152, 24, bg="#FFFFFF", border="#FFFFFF", fg="#000000", font_size=9.5)
        self.add_pill(car, "CarModeDashcam", "3-CAM DASHCAM", 172, 12, 118, 24, bg="#171717", border="#2E2E2E", fg="#F5F5F5", font_size=9.5)
        self.add_pill(car, "CarRecPill", "● REC 1080p60", 298, 12, 108, 24, bg="#1C1C1C", border="#A3A3A3", fg="#D4D4D4", font_size=9.5)
        self.add_text(car, "CarMainStat", "42 MPH · Peer Mesh Connected · Kokoro Voice Gate ON", 14, 52, size=12, color="#F5F5F5", font_style="Bold")
        self.add_text(car, "CarSubStat", "Front Cam: Clear  |  Cabin IR: Night-Vision  |  Rear Cam: Active", 14, 78, size=10, color="#FFFFFF", font_family="JetBrains Mono")
        self.add_pill(car, "CarTouch1", "▶ Speak Inbox", 14, 118, 126, 40, bg="#161616", border="#383838", fg="#F5F5F5", font_size=10.5)
        self.add_pill(car, "CarTouch2", "● Voice Ask AI", 148, 118, 126, 40, bg="#FFFFFF", border="#FFFFFF", fg="#000000", font_size=10.5)
        self.add_pill(car, "CarTouch3", "★ Bookmark Clip", 282, 118, 126, 40, bg="#161616", border="#383838", fg="#F5F5F5", font_size=10.5)

        self.add_dark_terminal_box(
            p6,
            "CarTelemetryDarkTerm",
            12,
            224,
            420,
            118,
            "CAR CAN-BUS & VOICE TERMINAL",
            "● NIGHT SUMI",
            [
                ('you@tincan-car:~$ tincan say "Read latest sealed message"', "#FFFFFF"),
                ("[kokoro] Spoke @alice message via cabin audio (-14 LUFS)", "#F5F5F5"),
            ],
            show_tui_tabs=False,
            prompt_line=None,
        )
        return root

    def build_all(self) -> Dict[str, Any]:
        cols = [80.0, 1760.0, 3440.0, 5120.0]
        rows = [80.0, 1160.0, 2240.0]

        term_ai_zip = os.path.join(DESIGNS_DIR, "tincan_terminal_ai_redesign.figcraft")
        ws_zip = os.path.join(DESIGNS_DIR, "tincan_workstation_designs.figcraft")
        node_zip = os.path.join(DESIGNS_DIR, "tincan_gemini_node_editor.figcraft")
        arena_zip = os.path.join(DESIGNS_DIR, "context_palace_router_arena.figcraft")
        board_zip = os.path.join(DESIGNS_DIR, "cyberspace_board_redesign.figcraft")

        artboard_ids: List[int] = []

        # Row 1
        artboard_ids.append(self.build_artboard_01_zen_shell(cols[0], rows[0]))
        artboard_ids.append(self.build_artboard_02_dark_terminal(cols[1], rows[0]))
        artboard_ids.append(
            self.import_and_darken_frame(
                term_ai_zip,
                2,
                "03 · AI Home Shell, Gateway Command Bar & Dark Live Shell Transcript (#win-ai-home)",
                cols[2],
                rows[0],
                badge_xy=(576.0, 16.0),
            )
        )
        artboard_ids.append(
            self.import_and_darken_frame(
                term_ai_zip,
                3,
                "04 · AI Copilot, Multi-Gateway Router & Dark Terminal .space Code Diffs (#win-copilot)",
                cols[3],
                rows[0],
                badge_xy=(576.0, 16.0),
            )
        )

        # Row 2
        artboard_ids.append(self.build_artboard_05_workstation_ide(cols[0], rows[1]))
        artboard_ids.append(
            self.import_and_darken_frame(
                ws_zip,
                2,
                "06 · 3D Studio · Hyper3D Rodin v2 Stage & Dark Terminal TEE Enclave Diff (#win-workstation)",
                cols[1],
                rows[1],
                badge_xy=(576.0, 18.0),
            )
        )
        ab7 = self.import_and_darken_frame(
            node_zip,
            955,
            "07 · Nano Banana Gemini Node Studio · Dark Dot-Grid Canvas, Prompt Island & Dark Node Terminal (#win-nodes)",
            cols[2],
            rows[1],
            badge_xy=(1120.0, 18.0),
        )
        self.add_dark_terminal_box(
            ab7,
            "NodeStudioDarkCliOverlay",
            916,
            88,
            660,
            190,
            "NODE STUDIO DARK TERMINAL · /api/nodes/generate",
            "● DAG SYNCED",
            [
                ('you@tincan:~/space$ tincan nodes generate --model gemini-nano-banana-2.1 --res 4K', "#FFFFFF"),
                ("[+] MorphingNode #3 -> Kodak 2383 LUT (85%) + SOOP Dirty Ink applied", "#F5F5F5"),
                ("[+] Saved /images/cyberpunk_street_4k.png (750 CR Ad-Earned · 0 subs)", "#FFFFFF"),
            ],
            show_tui_tabs=False,
            prompt_line="you@tincan:~/space$ ",
        )
        artboard_ids.append(ab7)

        ab8 = self.import_and_darken_frame(
            arena_zip,
            2,
            "08 · AI Brain Arena Duel & Context Palace Universal Inventory (#win-arena)",
            cols[3],
            rows[1],
            badge_xy=(560.0, 32.0),
        )
        self.add_dark_terminal_box(
            ab8,
            "ArenaBrainADarkTermCode",
            724,
            420,
            310,
            190,
            "BRAIN A · DARK TERMINAL",
            "● 0 CR LOCAL",
            [
                ("$ pytest test_crdt.py", "#FFFFFF"),
                ("12 passed in 0.14s", "#FFFFFF"),
                ("HLC causal merge OK", "#F5F5F5"),
            ],
            show_tui_tabs=False,
            prompt_line=None,
        )
        self.add_dark_terminal_box(
            ab8,
            "ArenaBrainBDarkTermCode",
            1056,
            420,
            306,
            190,
            "BRAIN B · DARK TERMINAL",
            "● 3 CR CLOUD",
            [
                ("$ pytest test_webrtc.py", "#FFFFFF"),
                ("12 passed in 0.28s", "#FFFFFF"),
                ("Zero PII delta OK", "#F5F5F5"),
            ],
            show_tui_tabs=False,
            prompt_line=None,
        )
        artboard_ids.append(ab8)

        # Row 3
        ab9 = self.import_and_darken_frame(
            board_zip,
            2,
            "09 · Cyberspace Discussion Board, Omni-Bar, AI Suggestions & Knowledge Graph (#win-board)",
            cols[0],
            rows[2],
            badge_xy=None,
        )
        self.add_dark_terminal_box(
            ab9,
            "BoardThreadDarkTerminalPreview",
            868,
            664,
            488,
            210,
            "THREAD #3 · TERMINAL HARNESSES VERIFICATION",
            "● SOLVED ✓",
            [
                ('you@tincan:~/space$ claude "Verify passkey Ed25519 origin binding"', "#FFFFFF"),
                ("[claude-code] Audited passkey_auth.py · 28 tests passed in .space", "#FFFFFF"),
                ("you@tincan:~/space$ dsx --yes -p 'Check fallback runner'", "#FFFFFF"),
            ],
            show_tui_tabs=False,
            prompt_line="you@tincan:~/space$ ",
        )
        artboard_ids.append(ab9)

        artboard_ids.append(self.build_artboard_10_comms_webrtc(cols[1], rows[2]))

        ab11 = self.import_and_darken_frame(
            term_ai_zip,
            5,
            "11 · Watch Party Relay TV & Token Vault / Sponsor Ad Arbitrage (#win-tv + #win-billing)",
            cols[2],
            rows[2],
            badge_xy=(576.0, 16.0),
        )
        self.add_dark_terminal_box(
            ab11,
            "TokenVaultDarkCliLedger",
            40,
            650,
            1360,
            190,
            "TOKEN VAULT & WATCH PARTY CLI LEDGER (tincan credits / tincan playlist)",
            "● ZERO SUBSCRIPTIONS",
            [
                ("you@tincan:~/space$ tincan credits --json && tincan playlist list", "#FFFFFF"),
                ('  {"balance_cr": 5000, "usd_equiv": 5.00, "home_ad_reward_cr": 5000, "local_ollama_saved_usd": 14.80}', "#FFFFFF"),
                ("  [playlist] 01. AI Messiah Ep 01 (@nojuannobody · 1080p60)  |  02. Dark Terminal & Node Studio Walkthrough (+5,000 CR)", "#F5F5F5"),
            ],
            show_tui_tabs=False,
            prompt_line="you@tincan:~/space$ tincan cost --model ollama/qwen2.5:3b",
        )
        artboard_ids.append(ab11)

        artboard_ids.append(self.build_artboard_12_system_cross_platform(cols[3], rows[2]))

        self.add_rect(
            self.page_id,
            "MasterContactSheetBackdrop",
            0.0,
            0.0,
            6800.0,
            3320.0,
            fill="#000000",
            stroke="#FFFFFF",
            stroke_weight=2.0,
            index=0,
        )

        doc = {
            "format": "figcraft",
            "version": 1,
            "imageIndex": [],
            "name": "TinCan 2.2 · Dark Mode & Dark Terminal Design System",
            "pages": [self.page_id],
            "nodes": self.nodes,
            "next_id": self.next_id,
            "styles": [],
            "variables": {
                "collections": [
                    {
                        "id": "VariableCollectionId:1",
                        "name": "TinCan 2.2 Theme Tokens",
                        "modes": [
                            {"id": "VariableCollectionId:1/mode_dark", "name": "Obsidian Dark (Default Terminal)"},
                            {"id": "VariableCollectionId:1/mode_light", "name": "Celadon Light (Dark Terminal)"},
                        ],
                    }
                ],
                "variables": [
                    {
                        "id": "VariableID:1",
                        "name": "tc/bg/stage",
                        "collection": "VariableCollectionId:1",
                        "resolvedType": "color",
                        "values": {
                            "VariableCollectionId:1/mode_dark": {"type": "color", "value": hex_to_rgba("#080808")},
                            "VariableCollectionId:1/mode_light": {"type": "color", "value": hex_to_rgba("#DFE6D7")},
                        },
                        "description": "Stage background",
                    },
                    {
                        "id": "VariableID:2",
                        "name": "tc/bg/window",
                        "collection": "VariableCollectionId:1",
                        "resolvedType": "color",
                        "values": {
                            "VariableCollectionId:1/mode_dark": {"type": "color", "value": hex_to_rgba("#0E0E0E")},
                            "VariableCollectionId:1/mode_light": {"type": "color", "value": hex_to_rgba("#ECF1E6")},
                        },
                        "description": "Window surface",
                    },
                    {
                        "id": "VariableID:3",
                        "name": "tc/bg/card",
                        "collection": "VariableCollectionId:1",
                        "resolvedType": "color",
                        "values": {
                            "VariableCollectionId:1/mode_dark": {"type": "color", "value": hex_to_rgba("#151515")},
                            "VariableCollectionId:1/mode_light": {"type": "color", "value": hex_to_rgba("#F4F8F0")},
                        },
                        "description": "Elevated card surface",
                    },
                    {
                        "id": "VariableID:4",
                        "name": "tc/bg/terminal",
                        "collection": "VariableCollectionId:1",
                        "resolvedType": "color",
                        "values": {
                            "VariableCollectionId:1/mode_dark": {"type": "color", "value": hex_to_rgba("#000000")},
                            "VariableCollectionId:1/mode_light": {"type": "color", "value": hex_to_rgba("#000000")},
                        },
                        "description": "Pitch-black terminal viewport (always dark)",
                    },
                    {
                        "id": "VariableID:5",
                        "name": "tc/ink/primary",
                        "collection": "VariableCollectionId:1",
                        "resolvedType": "color",
                        "values": {
                            "VariableCollectionId:1/mode_dark": {"type": "color", "value": hex_to_rgba("#F5F5F5")},
                            "VariableCollectionId:1/mode_light": {"type": "color", "value": hex_to_rgba("#111111")},
                        },
                        "description": "Primary text",
                    },
                    {
                        "id": "VariableID:6",
                        "name": "tc/ink/muted",
                        "collection": "VariableCollectionId:1",
                        "resolvedType": "color",
                        "values": {
                            "VariableCollectionId:1/mode_dark": {"type": "color", "value": hex_to_rgba("#A3A3A4")},
                            "VariableCollectionId:1/mode_light": {"type": "color", "value": hex_to_rgba("#4A4A4A")},
                        },
                        "description": "Secondary text",
                    },
                    {
                        "id": "VariableID:7",
                        "name": "tc/accent/emerald",
                        "collection": "VariableCollectionId:1",
                        "resolvedType": "color",
                        "values": {
                            "VariableCollectionId:1/mode_dark": {"type": "color", "value": hex_to_rgba("#FFFFFF")},
                            "VariableCollectionId:1/mode_light": {"type": "color", "value": hex_to_rgba("#107A47")},
                        },
                        "description": "Emerald terminal & status accent",
                    },
                ],
            },
            "current_page": self.page_id,
            "document_colors": [],
            "comments": [],
        }
        return {"doc": doc, "artboard_ids": artboard_ids}


def main() -> None:
    builder = FigCraftBuilder()
    res = builder.build_all()
    doc = res["doc"]
    artboard_ids = res["artboard_ids"]
    os.makedirs(DESIGNS_DIR, exist_ok=True)
    with zipfile.ZipFile(OUT_FIGCRAFT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("document.json", json.dumps(doc, indent=2))
    print(f"Wrote {OUT_FIGCRAFT} with {len(doc['nodes'])} nodes across {len(artboard_ids)} artboards: {artboard_ids}")


if __name__ == "__main__":
    main()
