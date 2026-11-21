#!/usr/bin/env python3
"""Build the Admin-Only Token Control Panel FigCraft design.

Outputs:
  assets/designs/tincan_token_vault_admin.figcraft

Design System: Aeonik Celadon & Ink with high-contrast #111111 Operator Header
to visually distinguish Admin Controls from the end-user Personal Wallet.
"""

from __future__ import annotations

import json
import os
import zipfile
from typing import Any, Dict, List, Optional

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGNS_DIR = os.path.join(REPO_ROOT, "assets", "designs")
OUT_FIGCRAFT = os.path.join(DESIGNS_DIR, "tincan_token_vault_admin.figcraft")


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


class AdminTokenFigCraftBuilder:
    def __init__(self) -> None:
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.next_id: int = 1
        self.page_id: int = self.alloc_id()
        self.nodes[str(self.page_id)] = {
            "id": self.page_id,
            "name": "TinCan Mesh OS · Admin Token Control Panel",
            "type": "page",
            "background": hex_to_rgba("#D6DFCE"),
            "flows": [],
            "prototype": {
                "device": "None",
                "background": hex_to_rgba("#D6DFCE"),
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
        fill: str = "#111111",
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
            "fills": solid_paint(fill),
        }
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
        h: float = 26.0,
        bg: str = "#FFFFFF",
        border: Optional[str] = "#111111",
        fg: str = "#111111",
        font_family: str = "JetBrains Mono",
        font_style: str = "SemiBold",
        font_size: float = 10.0,
    ) -> int:
        fid = self.add_frame(
            parent_id, name, x, y, w, h,
            fill=bg, stroke=border, stroke_weight=1.0, radius=999.0, clip=True,
        )
        est_tw = len(text) * font_size * 0.56
        tx = max(8.0, round((w - est_tw) / 2.0, 1))
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
            "TokenVault_AdminControl_1440x900",
            0.0, 0.0, 1440.0, 900.0,
            fill="#D6DFCE", stroke=None, radius=0.0,
        )

        self.add_rect(stage, "AdminWindow_Shadow", 126.0, 62.0, 1200.0, 788.0, fill="#111111", radius=16.0, opacity=0.10)

        # Main Admin Window (1200 x 788)
        win = self.add_frame(
            stage, "TokenVault_AdminWindow", 120.0, 56.0, 1200.0, 788.0,
            fill="#ECF1E6", stroke="#111111", stroke_weight=1.5, radius=16.0,
        )

        # High-contrast Ink Admin Top Bar
        hdr = self.add_frame(win, "Admin_HeaderBar", 0.0, 0.0, 1200.0, 62.0, fill="#111111", stroke=None, radius=0.0)
        self.add_ellipse(hdr, "Dot_1", 20.0, 26.0, 10.0, 10.0, fill="#4A4A4A")
        self.add_ellipse(hdr, "Dot_2", 36.0, 26.0, 10.0, 10.0, fill="#4A4A4A")
        self.add_ellipse(hdr, "Dot_3", 52.0, 26.0, 10.0, 10.0, fill="#4A4A4A")
        self.add_text(hdr, "Hdr_Title", "Token Treasury & Economy Control", 78.0, 18.0, size=19.0, color="#ECF1E6", font_style="Bold", w=340.0)
        self.add_pill(
            hdr, "Badge_AdminOnly", "ADMIN ONLY · X-ADMIN-KEY", 412.0, 19.0, 176.0, 24.0,
            bg="#107A47", border=None, fg="#FFFFFF", font_size=9.0,
        )
        self.add_pill(
            hdr, "Btn_KillSwitch", "⏸ Pause Cloud Routing", 846.0, 17.0, 166.0, 28.0,
            bg="#8A1C1C", border="#D66B6B", fg="#FFFFFF", font_family="Inter", font_size=11.0,
        )
        self.add_pill(
            hdr, "Btn_ExportAudit", "Export Audit CSV", 1024.0, 17.0, 152.0, 28.0,
            bg="#262626", border="#555555", fg="#ECF1E6", font_family="Inter", font_size=11.0,
        )

        # =====================================================================
        # 1. UPSTREAM PROVIDER TREASURY (4 LIVE POOL CARDS)
        # =====================================================================
        self.add_text(win, "Sec_Treasury", "UPSTREAM PROVIDER TREASURY (LIVE API POOLS)", 24.0, 78.0, size=10.5, color="#3A3A3A", font_style="Bold", w=360.0)
        pools = [
            ("Pool_NanoGPT", 24.0, "NANOGPT POOL", "$42.80", "18.4 NANO · 1,240 calls today", "HEALTHY · PRIMARY", "#107A47"),
            ("Pool_OpenRouter", 316.0, "OPENROUTER POOL", "$128.40", "$6.12 spent today · 312 calls", "HEALTHY · PRIMARY", "#107A47"),
            ("Pool_Rodin", 608.0, "HYPER3D RODIN", "$50.00", "100.0 Rodin CR · 4 meshes", "POOLED · ACTIVE", "#107A47"),
            ("Pool_StripeNet", 900.0, "NET MARGIN (30D)", "$314.60", "30.1% gross · after Stripe fees", "STRIPE VERIFIED", "#111111"),
        ]
        for pid, px, lbl, val, sub, badge, bcol in pools:
            card = self.add_frame(win, pid, px, 98.0, 276.0, 108.0, fill="#FFFFFF", stroke="#111111", stroke_weight=1.0, radius=12.0)
            self.add_text(card, f"{pid}_Lbl", lbl, 14.0, 12.0, size=9.5, color="#555555", font_style="Bold", w=160.0)
            self.add_text(card, f"{pid}_Val", val, 14.0, 30.0, size=26.0, color="#111111", font_family="JetBrains Mono", font_style="Bold", w=160.0)
            self.add_text(card, f"{pid}_Sub", sub, 14.0, 64.0, size=10.5, color="#4A4A4A", w=248.0)
            self.add_pill(card, f"{pid}_Badge", badge, 14.0, 82.0, 134.0, 18.0, bg=bcol, border=None, fg="#FFFFFF", font_size=8.0)

        # =====================================================================
        # 2. MIDDLE 2-COLUMN: LIVE ECONOMY DIALS | MINT QUEUE & USER TIERS
        # =====================================================================
        mid_y = 224.0

        # Left Column: Live Economy Dials (w=588)
        self.add_text(win, "Sec_Dials", "LIVE ECONOMY DIALS (REAL-TIME BILLING CONTROLS)", 24.0, mid_y, size=10.5, color="#3A3A3A", font_style="Bold", w=380.0)
        dials_panel = self.add_frame(win, "Panel_EconomyDials", 24.0, mid_y + 20.0, 588.0, 286.0, fill="#F4F8F0", stroke="#111111", stroke_weight=1.0, radius=12.0)

        # Dial 1: Credit Margin Dial
        self.add_text(dials_panel, "Dial1_Title", "Credit Markup & Gross Margin Dial", 16.0, 14.0, size=12.5, color="#111111", font_style="Bold", w=260.0)
        self.add_pill(dials_panel, "Dial1_Val", "1.43x · 30.1% GROSS MARGIN", 380.0, 12.0, 192.0, 22.0, bg="#107A47", border=None, fg="#FFFFFF", font_size=9.0)
        # Slider track + thumb
        self.add_rect(dials_panel, "Dial1_Track", 16.0, 48.0, 556.0, 8.0, fill="#FFFFFF", stroke="#111111", stroke_weight=1.0, radius=999.0)
        self.add_rect(dials_panel, "Dial1_Fill", 16.0, 48.0, 240.0, 8.0, fill="#111111", radius=999.0)
        self.add_ellipse(dials_panel, "Dial1_Thumb", 248.0, 43.0, 18.0, 18.0, fill="#111111", stroke="#FFFFFF", stroke_weight=2.0)
        # Preset pills
        self.add_pill(dials_panel, "Preset_100", "1.00x (0%)", 16.0, 68.0, 92.0, 24.0, bg="#FFFFFF", border="#111111", fg="#111111", font_size=9.5)
        self.add_pill(dials_panel, "Preset_125", "1.25x (20%)", 116.0, 68.0, 98.0, 24.0, bg="#FFFFFF", border="#111111", fg="#111111", font_size=9.5)
        self.add_pill(dials_panel, "Preset_130", "1.30x (23%)", 222.0, 68.0, 98.0, 24.0, bg="#FFFFFF", border="#111111", fg="#111111", font_size=9.5)
        self.add_pill(dials_panel, "Preset_143", "1.43x (30%)", 328.0, 68.0, 98.0, 24.0, bg="#111111", border=None, fg="#FFFFFF", font_size=9.5)
        self.add_pill(dials_panel, "Btn_ApplyDial", "Apply Live", 476.0, 68.0, 96.0, 24.0, bg="#111111", border=None, fg="#FFFFFF", font_family="Inter", font_size=10.5)

        self.add_rect(dials_panel, "Dial_Div1", 16.0, 106.0, 556.0, 1.0, fill="#111111", opacity=0.14)

        # Dial 2: Daily Sponsor Ad Reward Dial
        self.add_text(dials_panel, "Dial2_Title", "Sponsor Video Reward Dial", 16.0, 118.0, size=12.5, color="#111111", font_style="Bold", w=220.0)
        self.add_pill(dials_panel, "Dial2_Val", "25 CR / clip × 5/day = 125 CR", 364.0, 116.0, 208.0, 22.0, bg="#FFFFFF", border="#111111", fg="#111111", font_size=9.0)
        self.add_rect(dials_panel, "Dial2_Track", 16.0, 152.0, 556.0, 8.0, fill="#FFFFFF", stroke="#111111", stroke_weight=1.0, radius=999.0)
        self.add_rect(dials_panel, "Dial2_Fill", 16.0, 152.0, 160.0, 8.0, fill="#107A47", radius=999.0)
        self.add_ellipse(dials_panel, "Dial2_Thumb", 168.0, 147.0, 18.0, 18.0, fill="#107A47", stroke="#FFFFFF", stroke_weight=2.0)
        self.add_text(dials_panel, "Dial2_Sub", "Aligned with Pack CR scale · Max daily subsidy: $0.25 USD/user · 96% ad arbitrage margin", 16.0, 172.0, size=10.5, color="#4A4A4A", w=540.0)

        self.add_rect(dials_panel, "Dial_Div2", 16.0, 198.0, 556.0, 1.0, fill="#111111", opacity=0.14)

        # Dial 3: Signup Grant & Role Defaults
        self.add_text(dials_panel, "Dial3_Title", "Default Role Quotas & Free Trial Grant", 16.0, 210.0, size=12.5, color="#111111", font_style="Bold", w=300.0)
        self.add_pill(dials_panel, "Role_Free", "Free: 50 CR", 16.0, 240.0, 126.0, 28.0, bg="#FFFFFF", border="#111111", fg="#111111", font_size=10.0)
        self.add_pill(dials_panel, "Role_Student", "Student (FAU): BYOK", 150.0, 240.0, 156.0, 28.0, bg="#FFFFFF", border="#111111", fg="#107A47", font_size=10.0)
        self.add_pill(dials_panel, "Role_Builder", "Builder: Paid Packs", 314.0, 240.0, 150.0, 28.0, bg="#FFFFFF", border="#111111", fg="#111111", font_size=10.0)
        self.add_pill(dials_panel, "Role_Admin", "Admin: ∞", 472.0, 240.0, 100.0, 28.0, bg="#111111", border=None, fg="#FFFFFF", font_size=10.0)

        # Right Column: Mint Requests & Manual Grant Queue (x=628, w=548)
        self.add_text(win, "Sec_MintQueue", "MINT REQUESTS & MANUAL CREDIT GRANTS", 628.0, mid_y, size=10.5, color="#3A3A3A", font_style="Bold", w=340.0)
        mq = self.add_frame(win, "Panel_MintQueue", 628.0, mid_y + 20.0, 548.0, 286.0, fill="#FFFFFF", stroke="#111111", stroke_weight=1.0, radius=12.0)

        # Quick manual grant bar
        self.add_frame(mq, "Input_Peer", 14.0, 14.0, 224.0, 32.0, fill="#F4F8F0", stroke="#111111", stroke_weight=1.0, radius=8.0)
        self.add_text(mq, "Input_PeerTxt", "peer_id (e.g. tc:maria91)", 24.0, 22.0, size=11.0, color="#666666", font_family="JetBrains Mono", w=200.0)
        self.add_frame(mq, "Input_Amount", 246.0, 14.0, 118.0, 32.0, fill="#F4F8F0", stroke="#111111", stroke_weight=1.0, radius=8.0)
        self.add_text(mq, "Input_AmtTxt", "+500 CR", 258.0, 22.0, size=11.5, color="#111111", font_family="JetBrains Mono", font_style="Bold", w=90.0)
        self.add_pill(mq, "Btn_MintNow", "Mint Credits", 374.0, 14.0, 160.0, 32.0, bg="#111111", border=None, fg="#FFFFFF", font_family="Inter", font_size=11.0)

        self.add_rect(mq, "MQ_Div0", 14.0, 58.0, 520.0, 1.0, fill="#111111", opacity=0.14)
        self.add_text(mq, "MQ_SubHdr", "PENDING PEER REQUESTS (2)", 16.0, 68.0, size=9.5, color="#555555", font_style="Bold", w=200.0)

        reqs = [
            ("tc:alex-fau", "FAU Student · Capstone RAG", "+300 CR", 92.0),
            ("tc:dev-node4", "Builder · NanoGPT Swarm Test", "+650 CR", 156.0),
        ]
        for idx, (peer, reason, amt, ry) in enumerate(reqs):
            box = self.add_frame(mq, f"MintReq_{idx}", 14.0, ry, 520.0, 54.0, fill="#F4F8F0", stroke="#B6BFB0", stroke_weight=1.0, radius=10.0)
            self.add_text(box, f"MR_Peer_{idx}", peer, 12.0, 9.0, size=12.0, color="#111111", font_family="JetBrains Mono", font_style="Bold", w=140.0)
            self.add_text(box, f"MR_Reason_{idx}", reason, 12.0, 29.0, size=10.5, color="#4A4A4A", w=220.0)
            self.add_text(box, f"MR_Amt_{idx}", amt, 268.0, 18.0, size=13.0, color="#107A47", font_family="JetBrains Mono", font_style="Bold", w=80.0)
            self.add_pill(box, f"MR_Approve_{idx}", "Approve", 360.0, 14.0, 74.0, 26.0, bg="#107A47", border=None, fg="#FFFFFF", font_family="Inter", font_size=10.5)
            self.add_pill(box, f"MR_Reject_{idx}", "Reject", 442.0, 14.0, 66.0, 26.0, bg="#FFFFFF", border="#8A1C1C", fg="#8A1C1C", font_family="Inter", font_size=10.5)

        # Stripe webhook status strip at bottom of Mint Queue
        wh = self.add_frame(mq, "Stripe_Health", 14.0, 224.0, 520.0, 48.0, fill="#DCE5D4", stroke="#9CA696", stroke_weight=1.0, radius=10.0)
        self.add_text(wh, "WH_Title", "Stripe Webhook · HMAC Verified", 14.0, 8.0, size=11.5, color="#111111", font_style="Bold", w=240.0)
        self.add_text(wh, "WH_Sub", "Last checkout: 12m ago · pack_500 ($5.00 → 650 CR) · 0 failed deliveries", 14.0, 26.0, size=10.0, color="#3A3A3A", w=480.0)

        # =====================================================================
        # 3. BOTTOM SECTION: GLOBAL MARGIN & ARBITRAGE AUDIT LEDGER
        # =====================================================================
        aud_y = 544.0
        self.add_text(win, "Sec_Audit", "GLOBAL MARGIN & UPSTREAM AUDIT LEDGER (ALL PEERS)", 24.0, aud_y, size=10.5, color="#3A3A3A", font_style="Bold", w=420.0)
        tbl = self.add_frame(win, "Panel_AuditLedger", 24.0, aud_y + 20.0, 1152.0, 200.0, fill="#FFFFFF", stroke="#111111", stroke_weight=1.0, radius=12.0)

        self.add_rect(tbl, "Aud_HdrBg", 0.0, 0.0, 1152.0, 34.0, fill="#F4F8F0")
        self.add_rect(tbl, "Aud_HdrDiv", 0.0, 34.0, 1152.0, 1.0, fill="#111111", opacity=0.18)
        cols = [
            ("Time", 16.0),
            ("Peer / Role", 96.0),
            ("Gateway / Model", 290.0),
            ("Tokens", 600.0),
            ("Upstream $", 716.0),
            ("Billed $ (1.43x)", 848.0),
            ("Net Margin", 1016.0),
        ]
        for cname, cx in cols:
            self.add_text(tbl, f"Aud_Col_{cname}", cname, cx, 10.0, size=10.5, color="#4A4A4A", font_style="SemiBold", w=120.0)

        rows = [
            ("17:42:11", "tc:maria91 · Builder", "nanogpt / deepseek-v4-tee", "18,400", "$0.0037", "$0.0053", "+$0.0016 (+30%)", "#107A47"),
            ("17:38:04", "tc:dev-02 · Studio", "openrouter / claude-sonnet-4", "12,100", "$0.1180", "$0.1687", "+$0.0507 (+30%)", "#107A47"),
            ("17:25:19", "tc:alex-fau · Student", "ollama / qwen3-coder:30b", "6,200", "$0.0000", "$0.0000", "LOCAL FREE", "#107A47"),
            ("17:10:02", "tc:guest88 · Free", "sponsor-ad / vercel-clip-10s", "+25 CR", "$0.0020", "$0.0500 rev", "+$0.0480 (96%)", "#107A47"),
        ]
        for idx, (t, peer, gw, tok, up, bill, marg, mcol) in enumerate(rows):
            ry = 35.0 + idx * 41.0
            if idx > 0:
                self.add_rect(tbl, f"Aud_Div_{idx}", 14.0, ry, 1124.0, 1.0, fill="#111111", opacity=0.10)
            self.add_text(tbl, f"AR_T_{idx}", t, 16.0, ry + 13.0, size=11.0, color="#4A4A4A", font_family="JetBrains Mono", w=72.0)
            self.add_text(tbl, f"AR_P_{idx}", peer, 96.0, ry + 13.0, size=11.5, color="#111111", font_style="Medium", w=184.0)
            self.add_text(tbl, f"AR_G_{idx}", gw, 290.0, ry + 13.0, size=11.5, color="#333333", font_family="JetBrains Mono", w=290.0)
            self.add_text(tbl, f"AR_K_{idx}", tok, 600.0, ry + 13.0, size=11.5, color="#111111", font_family="JetBrains Mono", w=90.0)
            self.add_text(tbl, f"AR_U_{idx}", up, 716.0, ry + 13.0, size=11.5, color="#4A4A4A", font_family="JetBrains Mono", w=96.0)
            self.add_text(tbl, f"AR_B_{idx}", bill, 848.0, ry + 13.0, size=11.5, color="#111111", font_family="JetBrains Mono", font_style="SemiBold", w=120.0)
            self.add_text(tbl, f"AR_M_{idx}", marg, 1016.0, ry + 13.0, size=11.5, color=mcol, font_family="JetBrains Mono", font_style="Bold", w=124.0)

        return {
            "format": "figcraft",
            "version": 1,
            "imageIndex": [],
            "name": "TinCan Mesh OS · Admin Token Control Panel",
            "pages": [self.page_id],
            "nodes": self.nodes,
            "next_id": self.next_id,
            "styles": [],
            "variables": {
                "collections": [
                    {
                        "id": "VariableCollectionId:1",
                        "name": "Admin Celadon & Ink",
                        "modes": [{"id": "VariableCollectionId:1/mode_admin", "name": "Operator Mode"}],
                    }
                ],
                "variables": [
                    {
                        "id": "VariableID:1",
                        "name": "admin/header",
                        "collection": "VariableCollectionId:1",
                        "resolvedType": "color",
                        "values": {"VariableCollectionId:1/mode_admin": {"type": "color", "value": hex_to_rgba("#111111")}},
                    },
                    {
                        "id": "VariableID:2",
                        "name": "admin/canvas",
                        "collection": "VariableCollectionId:1",
                        "resolvedType": "color",
                        "values": {"VariableCollectionId:1/mode_admin": {"type": "color", "value": hex_to_rgba("#ECF1E6")}},
                    },
                    {
                        "id": "VariableID:3",
                        "name": "admin/emerald",
                        "collection": "VariableCollectionId:1",
                        "resolvedType": "color",
                        "values": {"VariableCollectionId:1/mode_admin": {"type": "color", "value": hex_to_rgba("#107A47")}},
                    },
                    {
                        "id": "VariableID:4",
                        "name": "admin/danger",
                        "collection": "VariableCollectionId:1",
                        "resolvedType": "color",
                        "values": {"VariableCollectionId:1/mode_admin": {"type": "color", "value": hex_to_rgba("#8A1C1C")}},
                    },
                ],
            },
            "current_page": self.page_id,
            "document_colors": [],
            "comments": [],
        }


def main() -> None:
    builder = AdminTokenFigCraftBuilder()
    doc = builder.build()
    os.makedirs(DESIGNS_DIR, exist_ok=True)
    with zipfile.ZipFile(OUT_FIGCRAFT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("document.json", json.dumps(doc, indent=2))
    print(f"Wrote {OUT_FIGCRAFT} ({len(doc['nodes'])} nodes)")


if __name__ == "__main__":
    main()
