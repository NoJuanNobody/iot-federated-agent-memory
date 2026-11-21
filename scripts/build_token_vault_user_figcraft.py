#!/usr/bin/env python3
"""Build the User-Perspective TinCan Mesh OS Token Vault FigCraft design.

Outputs:
  assets/designs/tincan_token_vault_user.figcraft

Design System: Aeonik Celadon & Ink
  - Stage:   #DFE6D7
  - Window:  #ECF1E6
  - Card:    #E1E9D8 / #F4F8F0
  - Paper:   #FFFFFF
  - Ink:     #111111
  - Muted:   #4A4A4A
  - Emerald: #107A47
"""

from __future__ import annotations

import json
import os
import zipfile
from typing import Any, Dict, List, Optional

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGNS_DIR = os.path.join(REPO_ROOT, "assets", "designs")
OUT_FIGCRAFT = os.path.join(DESIGNS_DIR, "tincan_token_vault_user.figcraft")


def hex_to_rgba(hex_str: str, alpha: float = 1.0) -> Dict[str, float]:
    h = hex_str.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    return {"r": round(r, 6), "g": round(g, 6), "b": round(b, 6), "a": alpha}


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


class TokenVaultFigCraftBuilder:
    def __init__(self) -> None:
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.next_id: int = 1
        self.page_id: int = self.alloc_id()
        self.nodes[str(self.page_id)] = {
            "id": self.page_id,
            "name": "TinCan Mesh OS · Token Vault (User Perspective)",
            "type": "page",
            "background": hex_to_rgba("#DFE6D7"),
            "flows": [],
            "prototype": {
                "device": "None",
                "background": hex_to_rgba("#DFE6D7"),
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

    def _attach(self, parent_id: int, nid: int) -> None:
        self.nodes[str(parent_id)].setdefault("children", []).append(nid)

    def add_frame(
        self,
        parent_id: int,
        name: str,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: Optional[str] = "#FFFFFF",
        stroke: Optional[str] = "#111111",
        stroke_weight: float = 1.0,
        radius: float = 0.0,
        clip: bool = True,
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
        self.nodes[str(nid)] = node
        self._attach(parent_id, nid)
        return nid

    def add_rect(
        self,
        parent_id: int,
        name: str,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: Optional[str] = "#111111",
        stroke: Optional[str] = None,
        stroke_weight: float = 1.0,
        radius: float = 0.0,
        opacity: float = 1.0,
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
            node["fills"] = solid_paint(fill, opacity=opacity)
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
        self.nodes[str(nid)] = node
        self._attach(parent_id, nid)
        return nid

    def add_ellipse(
        self,
        parent_id: int,
        name: str,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: str = "#BDBDBD",
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
            "fills": solid_paint(fill),
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
        color: str = "#111111",
        font_family: str = "Inter",
        font_style: str = "Regular",
        w: Optional[float] = None,
        h: Optional[float] = None,
    ) -> int:
        nid = self.alloc_id()
        est_w = float(w) if w is not None else max(16.0, round(len(text) * size * 0.62, 1))
        est_h = float(h) if h is not None else round(size * 1.35, 1)
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
        h: float = 28.0,
        bg: str = "#FFFFFF",
        border: Optional[str] = "#111111",
        fg: str = "#111111",
        font_family: str = "Inter",
        font_style: str = "SemiBold",
        font_size: float = 11.0,
    ) -> int:
        fid = self.add_frame(
            parent_id, name, x, y, w, h,
            fill=bg, stroke=border, stroke_weight=1.0, radius=999.0, clip=True,
        )
        est_tw = len(text) * font_size * 0.54
        tx = max(10.0, round((w - est_tw) / 2.0, 1))
        ty = round((h - font_size * 1.25) / 2.0, 1)
        self.add_text(
            fid, f"{name}_Label", text, tx, ty,
            size=font_size, color=fg, font_family=font_family, font_style=font_style,
            w=w - 8.0,
        )
        return fid

    def build(self) -> Dict[str, Any]:
        # Root Artboard (1440 x 900)
        stage = self.add_frame(
            self.page_id,
            "TokenVault_UserPerspective_1440x900",
            0.0,
            0.0,
            1440.0,
            900.0,
            fill="#DFE6D7",
            stroke=None,
            radius=0.0,
        )

        # Subtle window drop shadow
        self.add_rect(
            stage, "Window_Shadow", 136.0, 78.0, 1180.0, 760.0,
            fill="#111111", radius=16.0, opacity=0.08,
        )

        # Main Desktop Window (1180 x 760)
        win = self.add_frame(
            stage,
            "TokenVault_Window",
            130.0,
            70.0,
            1180.0,
            760.0,
            fill="#ECF1E6",
            stroke="#111111",
            stroke_weight=1.5,
            radius=16.0,
        )

        # Traffic lights
        self.add_ellipse(win, "Dot_Close", 22.0, 16.0, 10.0, 10.0, fill="#C4C9BF")
        self.add_ellipse(win, "Dot_Min", 38.0, 16.0, 10.0, 10.0, fill="#C4C9BF")
        self.add_ellipse(win, "Dot_Max", 54.0, 16.0, 10.0, 10.0, fill="#C4C9BF")

        # Title Row
        self.add_text(win, "Win_Title_Bold", "Token Vault", 24.0, 38.0, size=24.0, color="#111111", font_style="Bold", w=155.0)
        self.add_text(win, "Win_Title_Sub", "· Your Credits & Usage", 174.0, 41.0, size=21.0, color="#3A3A3A", font_style="Regular", w=260.0)
        self.add_pill(
            win, "Badge_PersonalWallet", "PERSONAL WALLET", 412.0, 42.0, 124.0, 24.0,
            bg="#ECF1E6", border="#8D9688", fg="#2B2B2B", font_family="JetBrains Mono", font_style="SemiBold", font_size=9.5,
        )
        self.add_pill(win, "Btn_ExportReceipts", "Export Receipts", 936.0, 38.0, 126.0, 32.0, bg="#FFFFFF", border="#111111", fg="#111111", font_size=11.5)
        self.add_pill(win, "Btn_Refresh", "Refresh", 1072.0, 38.0, 84.0, 32.0, bg="#FFFFFF", border="#111111", fg="#111111", font_size=11.5)

        # =====================================================================
        # 1. TOP HERO STRIP (3 cards)
        # =====================================================================
        hero_y = 88.0
        hero_h = 136.0

        # Card 1: Your Balance
        c1 = self.add_frame(win, "Card_YourBalance", 24.0, hero_y, 412.0, hero_h, fill="#FFFFFF", stroke="#111111", stroke_weight=1.0, radius=12.0)
        self.add_text(c1, "Lbl_YourBalance", "YOUR BALANCE", 18.0, 14.0, size=10.5, color="#4A4A4A", font_style="Bold", w=140.0)
        self.add_text(c1, "Val_Balance", "1,420", 18.0, 34.0, size=34.0, color="#111111", font_family="JetBrains Mono", font_style="Bold", w=110.0)
        self.add_text(c1, "Val_BalanceUnit", "CR", 120.0, 46.0, size=20.0, color="#111111", font_family="JetBrains Mono", font_style="Bold", w=40.0)
        self.add_text(c1, "Sub_BalanceEquiv", "~7,100 NanoGPT chats · ~140 OpenRouter frontier chats", 18.0, 78.0, size=11.0, color="#333333", font_style="Medium", w=380.0)
        self.add_pill(c1, "Badge_Ready", "Ready to use", 18.0, 100.0, 96.0, 24.0, bg="#107A47", border=None, fg="#FFFFFF", font_size=10.5)

        # Card 2: Saved with Local AI
        c2 = self.add_frame(win, "Card_LocalSaved", 452.0, hero_y, 320.0, hero_h, fill="#DCE5D4", stroke="#9CA696", stroke_weight=1.0, radius=12.0)
        self.add_text(c2, "Lbl_LocalSaved", "SAVED WITH LOCAL AI", 18.0, 14.0, size=10.5, color="#3D4639", font_style="Bold", w=180.0)
        self.add_text(c2, "Val_LocalSaved", "$14.20", 18.0, 34.0, size=34.0, color="#107A47", font_family="JetBrains Mono", font_style="Bold", w=180.0)
        self.add_text(c2, "Sub_LocalSaved", "48 local Ollama chats · Always 0 CR", 18.0, 80.0, size=11.5, color="#2D332B", font_style="Regular", w=280.0)

        # Card 3: Earn Free Credits
        c3 = self.add_frame(win, "Card_EarnFree", 788.0, hero_y, 368.0, hero_h, fill="#DCE5D4", stroke="#9CA696", stroke_weight=1.0, radius=12.0)
        self.add_text(c3, "Lbl_EarnFree", "EARN FREE CREDITS", 18.0, 14.0, size=10.5, color="#3D4639", font_style="Bold", w=180.0)
        # Progress bar
        p_track = self.add_frame(c3, "Bar_ClipTrack", 18.0, 36.0, 332.0, 20.0, fill="#F4F8F0", stroke="#9CA696", stroke_weight=1.0, radius=999.0)
        self.add_rect(p_track, "Bar_ClipFill", 0.0, 0.0, 133.0, 20.0, fill="#107A47", radius=999.0)
        self.add_text(p_track, "Bar_ClipPct", "40%", 88.0, 3.0, size=10.5, color="#FFFFFF", font_family="JetBrains Mono", font_style="Bold", w=34.0)
        self.add_text(c3, "Sub_ClipCount", "2 / 5 daily clips", 18.0, 64.0, size=12.0, color="#111111", font_style="Medium", w=140.0)
        self.add_pill(
            c3, "Btn_WatchClip", "▶ Watch 10s Clip (+25 CR)", 18.0, 92.0, 332.0, 32.0,
            bg="#111111", border=None, fg="#FFFFFF", font_size=11.5,
        )

        # =====================================================================
        # 2. MIDDLE 2-COLUMN SECTION: CREDIT PACKS | SIMPLE RATE CARD
        # =====================================================================
        mid_lbl_y = 244.0
        mid_card_y = 266.0
        mid_h = 224.0

        # Left Header
        self.add_text(win, "Hdr_TopUp", "TOP UP CREDITS · STRIPE CHECKOUT", 24.0, mid_lbl_y, size=10.5, color="#3A3A3A", font_style="Bold", w=290.0)

        packs = [
            {
                "id": "Pack_Starter",
                "x": 24.0,
                "badge": "CREDIT PACK",
                "badge_bg": "#E7EDE2",
                "name": "Starter",
                "price": "$1.00",
                "credits": "120 CR",
                "desc1": "Quick cloud bursts",
                "desc2": "& Arena duels",
                "cta": "Buy $1",
                "featured": False,
            },
            {
                "id": "Pack_Builder",
                "x": 214.0,
                "badge": "POPULAR · +8%",
                "badge_bg": "#E7EDE2",
                "name": "Builder",
                "price": "$5.00",
                "credits": "650 CR",
                "desc1": "Everyday NanoGPT +",
                "desc2": "OpenRouter chats",
                "cta": "Buy $5 →",
                "featured": True,
            },
            {
                "id": "Pack_Studio",
                "x": 404.0,
                "badge": "BEST VALUE · +17%",
                "badge_bg": "#E7EDE2",
                "name": "Studio",
                "price": "$20.00",
                "credits": "2,800 CR",
                "desc1": "Heavy frontier &",
                "desc2": "3D sessions",
                "cta": "Buy $20",
                "featured": False,
            },
        ]

        for p in packs:
            featured = p["featured"]
            if featured:
                self.add_rect(win, f"{p['id']}_Shadow", p["x"] + 3.0, mid_card_y + 4.0, 178.0, mid_h, fill="#111111", radius=12.0, opacity=0.12)
            card = self.add_frame(
                win,
                p["id"],
                p["x"],
                mid_card_y,
                178.0,
                mid_h,
                fill="#FFFFFF" if featured else "#F4F8F0",
                stroke="#111111" if featured else "#AEB7A8",
                stroke_weight=2.0 if featured else 1.0,
                radius=12.0,
            )
            self.add_pill(
                card, f"{p['id']}_Badge", p["badge"], 14.0, 14.0, 122.0, 20.0,
                bg=p["badge_bg"], border=None, fg="#333333", font_family="JetBrains Mono", font_style="Bold", font_size=8.5,
            )
            self.add_text(card, f"{p['id']}_Name", p["name"], 14.0, 42.0, size=15.0, color="#111111", font_style="Bold", w=120.0)
            self.add_text(card, f"{p['id']}_Price", p["price"], 14.0, 64.0, size=24.0, color="#111111", font_family="JetBrains Mono", font_style="Bold", w=140.0)
            self.add_text(card, f"{p['id']}_Credits", p["credits"], 14.0, 96.0, size=13.5, color="#107A47", font_family="JetBrains Mono", font_style="Bold", w=120.0)
            self.add_text(card, f"{p['id']}_Desc1", p["desc1"], 14.0, 122.0, size=11.0, color="#4A4A4A", w=150.0)
            self.add_text(card, f"{p['id']}_Desc2", p["desc2"], 14.0, 138.0, size=11.0, color="#4A4A4A", w=150.0)
            self.add_pill(
                card,
                f"{p['id']}_Btn",
                p["cta"],
                14.0,
                176.0,
                150.0,
                32.0,
                bg="#111111" if featured else "#FFFFFF",
                border=None if featured else "#111111",
                fg="#FFFFFF" if featured else "#111111",
                font_size=11.5,
            )

        # Right Header & Simple Rate Card Panel
        self.add_text(win, "Hdr_RateCard", "WHAT CREDITS COST · SIMPLE RATE CARD", 602.0, mid_lbl_y, size=10.5, color="#3A3A3A", font_style="Bold", w=340.0)
        rc = self.add_frame(win, "Panel_RateCard", 602.0, mid_card_y, 554.0, mid_h, fill="#FFFFFF", stroke="#111111", stroke_weight=1.0, radius=12.0)

        rate_rows = [
            {
                "name": "NanoGPT · Open-Weight & TEE",
                "sub": "Fast everyday chat & coding",
                "badge": "PRIMARY · LOW COST",
                "badge_bg": "#107A47",
                "badge_x": 228.0,
                "badge_w": 124.0,
                "rate": "0.2 CR / 1K tokens",
                "rate_color": "#111111",
            },
            {
                "name": "OpenRouter · Frontier Models",
                "sub": "Claude, GPT & Gemini reasoning",
                "badge": "PRIMARY · FRONTIER",
                "badge_bg": "#111111",
                "badge_x": 226.0,
                "badge_w": 124.0,
                "rate": "3–15 CR / 1K tokens",
                "rate_color": "#111111",
            },
            {
                "name": "Local Ollama / BYOK",
                "sub": "Private on-device inference",
                "badge": None,
                "badge_bg": None,
                "badge_x": 0.0,
                "badge_w": 0.0,
                "rate": "FREE (0 CR)",
                "rate_color": "#107A47",
            },
            {
                "name": "3D Studio (Rodin / Atlas)",
                "sub": "3D meshes & world splats",
                "badge": None,
                "badge_bg": None,
                "badge_x": 0.0,
                "badge_w": 0.0,
                "rate": "50–100 CR / scene",
                "rate_color": "#111111",
            },
        ]

        row_h = 56.0
        for idx, rr in enumerate(rate_rows):
            ry = idx * row_h
            if idx > 0:
                self.add_rect(rc, f"Rate_Div_{idx}", 16.0, ry, 522.0, 1.0, fill="#111111", opacity=0.14)
            self.add_text(rc, f"Rate_Title_{idx}", rr["name"], 18.0, ry + 11.0, size=13.0, color="#111111", font_style="SemiBold", w=210.0)
            self.add_text(rc, f"Rate_Sub_{idx}", rr["sub"], 18.0, ry + 31.0, size=11.0, color="#555555", w=240.0)
            if rr["badge"]:
                self.add_pill(
                    rc, f"Rate_Badge_{idx}", rr["badge"], rr["badge_x"], ry + 10.0, rr["badge_w"], 19.0,
                    bg=rr["badge_bg"], border=None, fg="#FFFFFF", font_family="JetBrains Mono", font_style="Bold", font_size=8.0,
                )
            rate_x = 412.0 if rr["rate"] != "FREE (0 CR)" else 452.0
            self.add_text(rc, f"Rate_Val_{idx}", rr["rate"], rate_x, ry + 19.0, size=12.0, color=rr["rate_color"], font_family="JetBrains Mono", font_style="Bold", w=132.0)

        # =====================================================================
        # 3. BOTTOM SECTION: RECENT ACTIVITY RECEIPT TABLE
        # =====================================================================
        act_lbl_y = 510.0
        act_card_y = 532.0
        self.add_text(win, "Hdr_Activity", "RECENT ACTIVITY", 24.0, act_lbl_y, size=10.5, color="#3A3A3A", font_style="Bold", w=180.0)

        tbl = self.add_frame(win, "Panel_RecentActivity", 24.0, act_card_y, 1132.0, 202.0, fill="#FFFFFF", stroke="#111111", stroke_weight=1.0, radius=12.0)

        # Table Header
        self.add_rect(tbl, "Tbl_HeaderBg", 0.0, 0.0, 1132.0, 36.0, fill="#F4F8F0")
        self.add_rect(tbl, "Tbl_HeaderDiv", 0.0, 36.0, 1132.0, 1.0, fill="#111111", opacity=0.18)
        self.add_text(tbl, "Col_Time", "Time", 18.0, 11.0, size=11.5, color="#4A4A4A", font_style="SemiBold", w=80.0)
        self.add_text(tbl, "Col_Activity", "Activity", 104.0, 11.0, size=11.5, color="#4A4A4A", font_style="SemiBold", w=200.0)
        self.add_text(tbl, "Col_Provider", "Provider", 610.0, 11.0, size=11.5, color="#4A4A4A", font_style="SemiBold", w=120.0)
        self.add_text(tbl, "Col_Credits", "Credits", 1054.0, 11.0, size=11.5, color="#4A4A4A", font_style="SemiBold", w=60.0)

        activities = [
            ("17:42", "Coding Chat · DeepSeek V4", "NanoGPT", "-4 CR", "#111111"),
            ("17:38", "Architecture Review · Claude Sonnet", "OpenRouter", "-38 CR", "#111111"),
            ("17:25", "Local Brainstorm · Llama 3", "Ollama", "FREE", "#107A47"),
            ("17:10", "Daily Sponsor Clip Reward", "Bonus", "+25 CR", "#107A47"),
        ]
        for idx, (t_str, act_str, prov_str, cr_str, cr_col) in enumerate(activities):
            ry = 37.0 + idx * 41.0
            if idx > 0:
                self.add_rect(tbl, f"Act_Div_{idx}", 16.0, ry, 1100.0, 1.0, fill="#111111", opacity=0.10)
            self.add_text(tbl, f"Act_Time_{idx}", t_str, 18.0, ry + 13.0, size=12.0, color="#4A4A4A", font_family="JetBrains Mono", w=64.0)
            self.add_text(tbl, f"Act_Name_{idx}", act_str, 104.0, ry + 13.0, size=12.5, color="#111111", font_style="Medium", w=420.0)
            self.add_text(tbl, f"Act_Prov_{idx}", prov_str, 610.0, ry + 13.0, size=12.0, color="#333333", w=140.0)
            self.add_text(tbl, f"Act_Cred_{idx}", cr_str, 1054.0, ry + 13.0, size=12.0, color=cr_col, font_family="JetBrains Mono", font_style="Bold", w=64.0)

        doc = {
            "format": "figcraft",
            "version": 1,
            "imageIndex": [],
            "name": "TinCan Mesh OS · Token Vault (User Perspective)",
            "pages": [self.page_id],
            "nodes": self.nodes,
            "next_id": self.next_id,
            "styles": [],
            "variables": {
                "collections": [
                    {
                        "id": "VariableCollectionId:1",
                        "name": "Aeonik Celadon & Ink",
                        "modes": [
                            {"id": "VariableCollectionId:1/mode_light", "name": "Celadon Light"},
                        ],
                    }
                ],
                "variables": [
                    {
                        "id": "VariableID:1",
                        "name": "tv/desk",
                        "collection": "VariableCollectionId:1",
                        "resolvedType": "color",
                        "values": {"VariableCollectionId:1/mode_light": {"type": "color", "value": hex_to_rgba("#DFE6D7")}},
                    },
                    {
                        "id": "VariableID:2",
                        "name": "tv/canvas",
                        "collection": "VariableCollectionId:1",
                        "resolvedType": "color",
                        "values": {"VariableCollectionId:1/mode_light": {"type": "color", "value": hex_to_rgba("#ECF1E6")}},
                    },
                    {
                        "id": "VariableID:3",
                        "name": "tv/paper",
                        "collection": "VariableCollectionId:1",
                        "resolvedType": "color",
                        "values": {"VariableCollectionId:1/mode_light": {"type": "color", "value": hex_to_rgba("#FFFFFF")}},
                    },
                    {
                        "id": "VariableID:4",
                        "name": "tv/ink",
                        "collection": "VariableCollectionId:1",
                        "resolvedType": "color",
                        "values": {"VariableCollectionId:1/mode_light": {"type": "color", "value": hex_to_rgba("#111111")}},
                    },
                    {
                        "id": "VariableID:5",
                        "name": "tv/emerald",
                        "collection": "VariableCollectionId:1",
                        "resolvedType": "color",
                        "values": {"VariableCollectionId:1/mode_light": {"type": "color", "value": hex_to_rgba("#107A47")}},
                    },
                ],
            },
            "current_page": self.page_id,
            "document_colors": [],
            "comments": [],
        }
        return doc


def main() -> None:
    builder = TokenVaultFigCraftBuilder()
    doc = builder.build()
    os.makedirs(DESIGNS_DIR, exist_ok=True)
    with zipfile.ZipFile(OUT_FIGCRAFT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("document.json", json.dumps(doc, indent=2))
    print(f"Wrote {OUT_FIGCRAFT} ({len(doc['nodes'])} nodes)")


if __name__ == "__main__":
    main()
