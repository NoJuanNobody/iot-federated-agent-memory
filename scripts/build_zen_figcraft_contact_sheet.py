#!/usr/bin/env python3
"""
TinCan Mesh OS — Zen Interior Design System & Window Contact Sheet Builder.
Generates assets/designs/tincan_zen_windows.figcraft containing all 10 tool windows
and the citizen identity registration gate in the Zen aesthetic.
"""

import os
import json
import zipfile

OUT_DIR = "/Users/alejandrolondono/dev/iot-federated-agent-memory/assets/designs"
os.makedirs(OUT_DIR, exist_ok=True)
FIGCRAFT_PATH = os.path.join(OUT_DIR, "tincan_zen_windows.figcraft")

# Color palette: Sumi, Washi, Kaki, Washes
C_SUMI = {"r": 14/255, "g": 13/255, "b": 11/255, "a": 1.0}        # #0e0d0b
C_SUMI_SOFT = {"r": 23/255, "g": 21/255, "b": 15/255, "a": 1.0}   # #17150f
C_SUMI_CARD = {"r": 32/255, "g": 29/255, "b": 22/255, "a": 1.0}   # #201d16
C_SUMI_WELL = {"r": 10/255, "g": 9/255, "b": 7/255, "a": 1.0}     # #0a0907
C_WASHI = {"r": 236/255, "g": 230/255, "b": 218/255, "a": 1.0}    # #ece6da
C_WASHI_QUIET = {"r": 236/255, "g": 230/255, "b": 218/255, "a": 0.70}
C_WASHI_DIM = {"r": 236/255, "g": 230/255, "b": 218/255, "a": 0.40}
C_WASHI_LINE = {"r": 236/255, "g": 230/255, "b": 218/255, "a": 0.14}
C_KAKI = {"r": 208/255, "g": 112/255, "b": 63/255, "a": 1.0}      # #d0703f
C_KAKI_DIM = {"r": 208/255, "g": 112/255, "b": 63/255, "a": 0.20}
C_RUST = {"r": 150/255, "g": 70/255, "b": 34/255, "a": 1.0}       # #964622
C_MOSS = {"r": 66/255, "g": 82/255, "b": 46/255, "a": 1.0}        # #42522e
C_INDIGO = {"r": 46/255, "g": 54/255, "b": 92/255, "a": 1.0}      # #2e365c
C_GREEN = {"r": 52/255, "g": 168/255, "b": 83/255, "a": 1.0}

next_id = 1
nodes = {}

def alloc_id():
    global next_id
    nid = next_id
    next_id += 1
    return nid

def make_solid_fill(color, opacity=1.0):
    return [{
        "type": "solid",
        "color": color,
        "opacity": opacity,
        "visible": True,
        "blend": "normal"
    }]

def make_solid_stroke(color, opacity=1.0):
    return [{
        "type": "solid",
        "color": color,
        "opacity": opacity,
        "visible": True,
        "blend": "normal"
    }]

def add_rect(parent_id, name, x, y, w, h, fill=None, stroke=None, radius=0.0):
    nid = alloc_id()
    node = {
        "id": nid,
        "name": name,
        "type": "rectangle",
        "parent": parent_id,
        "blend": "normal",
        "transform": [1.0, 0.0, 0.0, 1.0, float(x), float(y)],
        "width": float(w),
        "height": float(h),
        "fills": make_solid_fill(fill) if fill else [],
    }
    if stroke:
        node["strokes"] = make_solid_stroke(stroke)
    if radius > 0:
        node["corners"] = {"radii": [float(radius)]*4, "smoothing": 0.0}
    nodes[str(nid)] = node
    if parent_id and str(parent_id) in nodes and "children" in nodes[str(parent_id)]:
        nodes[str(parent_id)]["children"].append(nid)
    return nid

def add_text(parent_id, name, text, x, y, w, h, font="Zen Kaku Gothic New", size=13.0, weight="Regular", color=C_WASHI):
    nid = alloc_id()
    node = {
        "id": nid,
        "name": name,
        "type": "text",
        "characters": text,
        "style": {
            "font_family": font,
            "font_style": weight,
            "font_size": float(size),
            "line_height": {"unit": "auto"},
            "letter_spacing": {"unit": "percent", "value": 0.0},
            "decoration": "none",
            "case": "original",
            "fills": None,
            "link": None
        },
        "parent": parent_id,
        "blend": "normal",
        "transform": [1.0, 0.0, 0.0, 1.0, float(x), float(y)],
        "width": float(w),
        "height": float(h),
        "fills": make_solid_fill(color),
        "child_layout": {
            "sizing_h": "hug",
            "sizing_v": "hug",
            "absolute": False,
            "min_w": None, "max_w": None, "min_h": None, "max_h": None,
            "grid_column": None, "grid_row": None, "grid_column_span": 0, "grid_row_span": 0
        }
    }
    nodes[str(nid)] = node
    if parent_id and str(parent_id) in nodes and "children" in nodes[str(parent_id)]:
        nodes[str(parent_id)]["children"].append(nid)
    return nid

def add_frame(parent_id, name, x, y, w, h, fill=None, stroke=None, radius=0.0):
    nid = alloc_id()
    node = {
        "id": nid,
        "name": name,
        "type": "frame",
        "parent": parent_id,
        "children": [],
        "width": float(w),
        "height": float(h),
        "clip": True,
        "transform": [1.0, 0.0, 0.0, 1.0, float(x), float(y)],
        "fills": make_solid_fill(fill) if fill else []
    }
    if stroke:
        node["strokes"] = make_solid_stroke(stroke)
    if radius > 0:
        node["corners"] = {"radii": [float(radius)]*4, "smoothing": 0.0}
    nodes[str(nid)] = node
    if parent_id and str(parent_id) in nodes and "children" in nodes[str(parent_id)]:
        nodes[str(parent_id)]["children"].append(nid)
    return nid

def build_window_shell(page_id, name, title_text, tool_tag, x, y, w=980, h=740):
    """Builds a standardized Zen window frame with top header bar."""
    win_id = add_frame(page_id, name, x, y, w, h, fill=C_SUMI_SOFT, stroke=C_WASHI_LINE, radius=14.0)

    # Window Header Bar (height 48)
    head_bg = add_rect(win_id, "Header Background", 0, 0, w, 48, fill=C_SUMI, stroke=C_WASHI_LINE)
    dot = add_rect(win_id, "Zen Dot", 20, 19, 10, 10, fill=C_KAKI, radius=5.0)
    title = add_text(win_id, "Window Title", title_text, 38, 14, 420, 22, font="Shippori Mincho", size=16.0, weight="Medium", color=C_WASHI)

    # Tool Badge
    badge_bg = add_rect(win_id, "Badge BG", w - 240, 12, 110, 24, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=999.0)
    badge_txt = add_text(win_id, "Badge Text", tool_tag, w - 232, 17, 95, 14, size=10.0, weight="Regular", color=C_WASHI_QUIET)

    # Window Controls [↗] [—] [□]
    ctrl_pop = add_text(win_id, "Ctrl Pop", "↗", w - 105, 14, 18, 18, size=13.0, color=C_WASHI_DIM)
    ctrl_min = add_text(win_id, "Ctrl Min", "—", w - 75, 14, 18, 18, size=13.0, color=C_WASHI_DIM)
    ctrl_max = add_text(win_id, "Ctrl Max", "□", w - 45, 14, 18, 18, size=13.0, color=C_WASHI_DIM)

    # Content Area Container (below header, y=48, h=692)
    body_id = add_frame(win_id, "Body Content", 0, 48, w, h - 48, fill=C_SUMI_SOFT)

    return win_id, body_id

# -------------------------------------------------------------
# Main Generation
# -------------------------------------------------------------
def main():
    print("[*] Building TinCan Mesh OS Zen Windows FigCraft document...")

    # Page Node (ID 1)
    page_id = 1
    global next_id
    next_id = 2

    # Canvas Frame: 4400 x 3600
    canvas_w = 4400.0
    canvas_h = 3600.0
    canvas_id = add_frame(page_id, "TinCan Mesh OS · Zen Windows Contact Sheet (4400x3600)", 0, 0, canvas_w, canvas_h, fill=C_SUMI)

    # Top Master Header
    top_header = add_rect(canvas_id, "Header Banner", 0, 0, canvas_w, 280, fill=C_SUMI_WELL, stroke=C_WASHI_LINE)
    logo_dot = add_rect(canvas_id, "Master Logo Dot", 100, 60, 24, 24, fill=C_KAKI, radius=12.0)
    add_text(canvas_id, "Master Title", "TINCAN MESH OS · ZEN INTERIOR DESIGN SYSTEM & CONTACT SHEET", 140, 52, 2800, 44, font="Shippori Mincho", size=36.0, weight="Medium", color=C_WASHI)
    add_text(canvas_id, "Master Subtitle", "Complete architectural redesign of all 10 tool window interiors + citizen identity verification gate · Ink & washi paper aesthetic (Sumi #0E0D0B · Washi #ECE6DA · Kaki #D0703F)", 140, 106, 2600, 26, font="Zen Kaku Gothic New", size=18.0, color=C_WASHI_QUIET)

    # Palette Legend in Header
    swatches = [
        ("Sumi (#0E0D0B)", C_SUMI),
        ("Sumi Soft (#17150F)", C_SUMI_SOFT),
        ("Washi (#ECE6DA)", C_WASHI),
        ("Kaki Persimmon (#D0703F)", C_KAKI),
        ("Wash Rust (#964622)", C_RUST),
        ("Wash Moss (#42522E)", C_MOSS),
        ("Wash Indigo (#2E365C)", C_INDIGO),
    ]
    sx = 140
    for label, col in swatches:
        add_rect(canvas_id, "Swatch Box", sx, 160, 24, 24, fill=col, stroke=C_WASHI_LINE, radius=4.0)
        add_text(canvas_id, "Swatch Label", label, sx + 32, 164, 180, 20, size=12.0, color=C_WASHI_QUIET)
        sx += 230

    # Grid coordinates
    cols = [100, 1140, 2180, 3220]
    rows = [320, 1120, 1920]

    # =========================================================
    # ROW 1, COL 1: Window 1 — Watch Party (`win-tv`)
    # =========================================================
    _, b1 = build_window_shell(canvas_id, "Win 01: Watch Party (win-tv)", "Watch Party · Relay TV", "win-tv", cols[0], rows[0])
    # Left: Vertical 9:16 Video Stage (w: 360, h: 630, x: 24, y: 24)
    v_stage = add_rect(b1, "9:16 Video Player Stage", 24, 24, 360, 630, fill=C_SUMI_WELL, stroke=C_WASHI_LINE, radius=12.0)
    add_rect(b1, "Dirty Wash Rim", 24, 24, 360, 630, fill=C_RUST, stroke=None, radius=12.0)
    add_rect(b1, "Video Core Glass", 32, 32, 344, 614, fill=C_SUMI, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b1, "Video Stamp", "AI MESSIAH · EPISODE 01", 50, 60, 300, 24, font="Shippori Mincho", size=18.0, color=C_WASHI)
    add_text(b1, "Video Sub", "@nojuannobody · 1080p 60fps · Ed25519 Sealed", 50, 90, 300, 18, size=12.0, color=C_WASHI_QUIET)
    # Scrubber
    add_rect(b1, "Scrub Track", 50, 560, 308, 4, fill=C_SUMI_CARD, radius=2.0)
    add_rect(b1, "Scrub Progress", 50, 560, 130, 4, fill=C_KAKI, radius=2.0)
    add_rect(b1, "Scrub Thumb", 178, 557, 10, 10, fill=C_WASHI, radius=5.0)
    add_text(b1, "Timecode", "0:14 / 0:34 · Ambient Loop", 50, 574, 200, 16, size=11.0, color=C_WASHI_DIM)
    add_rect(b1, "Sound Pill", 50, 600, 130, 28, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=999.0)
    add_text(b1, "Sound Text", "🔊 Tap for Sound", 66, 606, 110, 16, size=11.0, color=C_WASHI)

    # Right: Controls, Reactions & Queue (x: 410, y: 24, w: 540)
    add_text(b1, "Sync Title", "Synchronized Room Playback", 410, 30, 300, 24, font="Shippori Mincho", size=17.0, color=C_WASHI)
    add_rect(b1, "Sync Pill", 770, 30, 170, 24, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=999.0)
    add_text(b1, "Sync Text", "● In-Sync · 4 Observers", 780, 35, 150, 16, size=11.0, color=C_GREEN)
    add_text(b1, "Reaction Header", "Room Live Reactions", 410, 75, 200, 18, size=13.0, color=C_WASHI_QUIET)
    rx = 410
    for emoji, count in [("🥫", "14"), ("🔥", "52"), ("⚡", "31"), ("🧠", "88"), ("🎌", "24")]:
        add_rect(b1, "Reaction Box", rx, 100, 95, 38, fill=C_SUMI_CARD, stroke=C_KAKI_DIM, radius=8.0)
        add_text(b1, "Reaction Text", f"{emoji} {count}", rx + 24, 110, 50, 20, size=14.0, color=C_WASHI)
        rx += 110
    add_text(b1, "Queue Header", "Relay Video Queue (4 items)", 410, 165, 300, 20, font="Shippori Mincho", size=15.0, color=C_WASHI)
    qy = 195
    q_items = [
        ("01. Zero-Knowledge Relay Architecture", "0:34 · Now Playing", C_KAKI),
        ("02. AI Brain Arena Dual-Model Duel", "0:45 · Up Next", C_WASHI_QUIET),
        ("03. Toronto Loft TOFU Peer Handshake", "0:52 · Queued", C_WASHI_QUIET),
        ("04. L1-L5 Cryptographic Edge Memory", "1:15 · Queued", C_WASHI_QUIET),
    ]
    for qtitle, qmeta, qcol in q_items:
        add_rect(b1, "Q Item BG", 410, qy, 540, 52, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=8.0)
        add_text(b1, "Q Title", qtitle, 426, qy + 10, 360, 18, size=13.0, weight="Medium", color=qcol)
        add_text(b1, "Q Meta", qmeta, 426, qy + 28, 300, 16, size=11.0, color=C_WASHI_DIM)
        add_rect(b1, "Q Play Btn", 880, qy + 12, 54, 28, fill=C_SUMI, stroke=C_WASHI_LINE, radius=6.0)
        add_text(b1, "Q Play Text", "Play", 894, qy + 18, 30, 14, size=11.0, color=C_WASHI)
        qy += 62
    # Add video input
    add_rect(b1, "Add Input Box", 410, 465, 380, 40, fill=C_SUMI_WELL, stroke=C_WASHI_LINE, radius=8.0)
    add_text(b1, "Add Input Placeholder", "Paste TikTok or MP4 URL to collection...", 425, 477, 350, 16, size=12.0, color=C_WASHI_DIM)
    add_rect(b1, "Add Btn", 805, 465, 145, 40, fill=C_KAKI, radius=8.0)
    add_text(b1, "Add Btn Text", "+ Add Video", 840, 477, 90, 18, size=13.0, weight="Medium", color=C_WASHI)

    # =========================================================
    # ROW 1, COL 2: Window 2 — Talk / Comms (`win-comms`)
    # =========================================================
    _, b2 = build_window_shell(canvas_id, "Win 02: Talk & Media (win-comms)", "Talk · Room Comms & Video", "win-comms", cols[1], rows[0])
    # Top status
    add_rect(b2, "Room Select", 24, 20, 150, 32, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=6.0)
    add_text(b2, "Room Text", "Room: main ▾", 40, 28, 120, 16, size=12.0, color=C_WASHI)
    add_rect(b2, "WebRTC Status", 190, 20, 240, 32, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=999.0)
    add_text(b2, "Status Text", "● Connected · 2 Peers · 24ms RTT", 205, 28, 220, 16, size=11.0, color=C_GREEN)

    # Media slots
    add_rect(b2, "Remote Stream Card", 24, 68, 450, 240, fill=C_SUMI_WELL, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b2, "Remote Label", "Mac Studio (M1 Max) · Remote Peer Stream", 40, 84, 350, 18, font="Shippori Mincho", size=14.0, color=C_WASHI)
    add_text(b2, "Remote Spec", "1080p 60fps · WebRTC UDP · Audio Active", 40, 104, 300, 16, size=11.0, color=C_WASHI_DIM)
    add_rect(b2, "Wave Bar 1", 40, 270, 8, 24, fill=C_KAKI, radius=4.0)
    add_rect(b2, "Wave Bar 2", 52, 260, 8, 34, fill=C_KAKI, radius=4.0)
    add_rect(b2, "Wave Bar 3", 64, 250, 8, 44, fill=C_KAKI, radius=4.0)
    add_rect(b2, "Wave Bar 4", 76, 264, 8, 30, fill=C_WASHI_QUIET, radius=4.0)

    add_rect(b2, "Local Stream Card", 498, 68, 450, 240, fill=C_SUMI_WELL, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b2, "Local Label", "You (Local Workstation Preview)", 514, 84, 350, 18, font="Shippori Mincho", size=14.0, color=C_WASHI)
    add_text(b2, "Local Spec", "Microphone Active · Camera Off · Screen Ready", 514, 104, 300, 16, size=11.0, color=C_WASHI_DIM)

    # Action bar
    bx = 24
    for bname in ["[🎤 Mute]", "[📹 Camera]", "[📺 Screen Share]", "[⛔ Leave Room]"]:
        add_rect(b2, "Comms Btn", bx, 324, 215, 38, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=8.0)
        add_text(b2, "Comms Btn Text", bname, bx + 45, 335, 140, 18, size=13.0, color=C_WASHI)
        bx += 238

    # Chat thread
    add_rect(b2, "Chat Thread Frame", 24, 380, 930, 240, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b2, "Chat Header", "Encrypted P2P Room Messages (XSalsa20-Poly1305)", 40, 395, 400, 18, font="Shippori Mincho", size=13.0, color=C_WASHI)
    add_text(b2, "Msg 1", "@nojuannobody (10:14 PM): Sealed envelope #42 decrypted via X25519.", 40, 425, 700, 16, size=12.0, color=C_WASHI_QUIET)
    add_text(b2, "Msg 2", "@collaborator (10:15 PM): Audio ducking verified at -14 LUFS standard across WebRTC.", 40, 450, 700, 16, size=12.0, color=C_WASHI_QUIET)
    add_text(b2, "Msg 3", "@system (10:16 PM): Peer peer-secondary-node pinned public key via TOFU contact register.", 40, 475, 700, 16, size=12.0, color=C_KAKI)

    # Chat Input
    add_rect(b2, "Chat Input Box", 40, 560, 760, 42, fill=C_SUMI_WELL, stroke=C_WASHI_LINE, radius=8.0)
    add_text(b2, "Chat Input Placeholder", "Type message to room peers... (Enter to send)", 56, 573, 500, 16, size=12.0, color=C_WASHI_DIM)
    add_rect(b2, "Chat Send Btn", 815, 560, 120, 42, fill=C_KAKI, radius=8.0)
    add_text(b2, "Chat Send Text", "Send ↵", 850, 573, 60, 18, size=13.0, weight="Medium", color=C_WASHI)

    # =========================================================
    # ROW 1, COL 3: Window 3 — Cyberspace Board (`win-board`)
    # =========================================================
    _, b3 = build_window_shell(canvas_id, "Win 03: Cyberspace Board (win-board)", "Cyberspace · Discussion Board & Graph", "win-board", cols[2], rows[0])
    # Search bar
    add_rect(b3, "Board Search Box", 24, 20, 680, 40, fill=C_SUMI_WELL, stroke=C_WASHI_LINE, radius=8.0)
    add_text(b3, "Board Search Text", "🔍 Search topics, entities, and graph nodes...", 40, 32, 400, 16, size=12.0, color=C_WASHI_DIM)
    add_rect(b3, "Search Mode Select", 720, 20, 230, 40, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=8.0)
    add_text(b3, "Search Mode Text", "Hybrid: GraphRAG + BM25 ▾", 735, 32, 200, 16, size=12.0, color=C_KAKI)

    # Category pills
    cx = 24
    for cat in ["All Topics (42)", "#research (18)", "#creative (12)", "#governance (8)", "#mesh-protocol (4)"]:
        add_rect(b3, "Cat Pill", cx, 75, 165, 30, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=999.0)
        add_text(b3, "Cat Text", cat, cx + 18, 83, 140, 16, size=11.0, color=C_WASHI_QUIET)
        cx += 180

    # Topic feed
    ty = 120
    topics = [
        ("PPR GraphRAG Retrieval vs Dense Vector Embeddings in Edge Networks", "@nojuannobody · ✅ Verified · +48 votes · 16 replies", C_WASHI),
        ("Decentralized Blind Relay Economics & Bancor Bonding Curves", "@cryptoscribe · +34 votes · 8 replies · 1h ago", C_WASHI_QUIET),
        ("Kokoro TTS Voice Synthesis Integration for Local Agent Feedback", "@soundcraft · +21 votes · 5 replies · 3h ago", C_WASHI_QUIET),
        ("Multi-Account Gemini Harvester & Token Pool Architecture", "@ai_architect · +17 votes · 4 replies · 6h ago", C_WASHI_QUIET),
    ]
    for top_title, top_meta, top_col in topics:
        add_rect(b3, "Topic Card", 24, ty, 930, 76, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=10.0)
        add_text(b3, "Topic Title", top_title, 44, ty + 16, 750, 22, font="Shippori Mincho", size=15.0, weight="Medium", color=top_col)
        add_text(b3, "Topic Meta", top_meta, 44, ty + 42, 600, 16, size=12.0, color=C_WASHI_DIM)
        add_rect(b3, "Topic View Btn", 840, ty + 20, 95, 34, fill=C_SUMI, stroke=C_WASHI_LINE, radius=6.0)
        add_text(b3, "Topic View Text", "Read Thread", 852, ty + 28, 80, 16, size=11.0, color=C_KAKI)
        ty += 88

    # Graph preview card
    add_rect(b3, "Graph HUD Box", 24, 490, 930, 175, fill=C_SUMI_WELL, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b3, "Graph HUD Title", "Knowledge Graph Topology · 128 Entities / 312 Edges", 44, 508, 400, 20, font="Shippori Mincho", size=14.0, color=C_WASHI)
    # Simulated graph nodes
    add_rect(b3, "GNode 1", 100, 560, 16, 16, fill=C_KAKI, radius=8.0)
    add_rect(b3, "GNode 2", 240, 540, 16, 16, fill=C_RUST, radius=8.0)
    add_rect(b3, "GNode 3", 400, 580, 16, 16, fill=C_MOSS, radius=8.0)
    add_rect(b3, "GNode 4", 580, 550, 16, 16, fill=C_INDIGO, radius=8.0)
    add_rect(b3, "GNode 5", 750, 570, 16, 16, fill=C_WASHI_QUIET, radius=8.0)
    add_text(b3, "GLabel 1", "PPR Algorithm", 75, 582, 100, 14, size=10.0, color=C_WASHI_DIM)
    add_text(b3, "GLabel 2", "GraphRAG", 225, 562, 100, 14, size=10.0, color=C_WASHI_DIM)
    add_text(b3, "GLabel 3", "Ed25519", 390, 602, 100, 14, size=10.0, color=C_WASHI_DIM)
    add_text(b3, "GLabel 4", "WebRTC", 570, 572, 100, 14, size=10.0, color=C_WASHI_DIM)
    add_text(b3, "GLabel 5", "Kokoro TTS", 735, 592, 100, 14, size=10.0, color=C_WASHI_DIM)

    # =========================================================
    # ROW 1, COL 4: Window 4 — AgentSpace (`win-agentspace`)
    # =========================================================
    _, b4 = build_window_shell(canvas_id, "Win 04: AgentSpace (win-agentspace)", "AgentSpace · .space VFS & Wasm", "win-agentspace", cols[3], rows[0])
    # Sub-tabs
    ax = 24
    for tab in [".space VFS Tree", "Rodin 3D Model", "Wasm Studio", "Notes → Apply"]:
        add_rect(b4, "Agent Tab", ax, 18, 190, 32, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=6.0)
        add_text(b4, "Agent Tab Text", tab, ax + 25, 26, 150, 16, size=12.0, color=C_WASHI_QUIET)
        ax += 205

    # Left pane: VFS tree (x: 24, w: 320)
    add_rect(b4, "VFS Pane", 24, 65, 320, 590, fill=C_SUMI_WELL, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b4, "VFS Header", "📁 /data/.space/ (Persistent)", 40, 80, 280, 18, font="Shippori Mincho", size=13.0, color=C_WASHI)
    vfs_files = [
        ("📄 manifest.json", "VFS Metadata · S3 Synced"),
        ("🧊 rodin_mesh.obj", "3D Hyper-Mesh (1.4 MB)"),
        ("⚙️ kernel_runtime.wasm", "WebAssembly Binary (42 KB)"),
        ("📝 notes.md", "Active Neural Note Draft"),
        ("📊 memory_telemetry.log", "L1-L5 XP Stream Log"),
    ]
    vy = 115
    for fname, fdesc in vfs_files:
        add_rect(b4, "VFS Row", 36, vy, 296, 48, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=6.0)
        add_text(b4, "VFS FName", fname, 48, vy + 8, 260, 18, size=12.0, weight="Medium", color=C_WASHI)
        add_text(b4, "VFS FDesc", fdesc, 48, vy + 26, 260, 14, size=10.0, color=C_WASHI_DIM)
        vy += 56

    # Right pane: Notes → Apply AI Editor (x: 360, w: 590)
    add_rect(b4, "Editor Pane", 360, 65, 595, 590, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b4, "Editor Title", "notes.md · Neural Notes Editor", 380, 80, 300, 18, font="Shippori Mincho", size=14.0, color=C_WASHI)
    add_rect(b4, "Editor Code Box", 380, 110, 555, 460, fill=C_SUMI_WELL, stroke=C_WASHI_LINE, radius=8.0)
    code_lines = [
        "# AgentSpace Specification v2.2",
        "## Dual-Persistence Architecture",
        "- Local mount: /data/.space/ (Railway Persistent Volume)",
        "- Cloud mirror: AWS S3 tincan-videos bucket fallback",
        "",
        "## Active Subsystems",
        "1. Rodin Hyper3D wireframe parser with WebGL fallback",
        "2. Wasm sandboxed memory runtime for DFA guardrails",
        "3. Live 'Notes -> Apply' diffing engine for VFS mutations",
        "",
        "// Operator Note: Apply AI edits seamlessly synchronizes",
        "// local state across all active WebRTC peer nodes."
    ]
    cy = 125
    for cl in code_lines:
        add_text(b4, "Code Line", cl, 396, cy, 520, 16, font="monospace", size=11.0, color=C_WASHI_QUIET if not cl.startswith("//") else C_KAKI)
        cy += 22

    add_rect(b4, "Apply Btn", 380, 590, 260, 44, fill=C_KAKI, radius=8.0)
    add_text(b4, "Apply Btn Text", "✨ Apply AI Edits to .space VFS", 405, 603, 220, 18, size=13.0, weight="Medium", color=C_WASHI)
    add_rect(b4, "Sync S3 Btn", 660, 590, 275, 44, fill=C_SUMI, stroke=C_WASHI_LINE, radius=8.0)
    add_text(b4, "Sync S3 Text", "💾 Sync S3 Mirror Bucket", 710, 603, 190, 18, size=13.0, color=C_WASHI_QUIET)

    # =========================================================
    # ROW 2, COL 1: Window 5 — Terminal & Quickstart (`win-terminal`)
    # =========================================================
    _, b5 = build_window_shell(canvas_id, "Win 05: Terminal (win-terminal)", "Terminal · Operator Quickstart & CLI", "win-terminal", cols[0], rows[1])
    # Card 1: One-line install
    add_rect(b5, "Term Card 1", 24, 20, 930, 140, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b5, "TC1 Title", "1. One-Line Terminal Installer (Installs TinCan CLI & Skills):", 44, 35, 600, 18, font="Shippori Mincho", size=14.0, color=C_WASHI)
    add_rect(b5, "Cmd Box 1", 44, 65, 710, 40, fill=C_SUMI_WELL, stroke=C_WASHI_LINE, radius=6.0)
    add_text(b5, "Cmd Text 1", "curl -sSL https://iot-federated-agent-memory-production.up.railway.app/install.sh | bash", 58, 77, 680, 16, font="monospace", size=11.0, color=C_GREEN)
    add_rect(b5, "Copy Btn 1", 770, 65, 160, 40, fill=C_KAKI, radius=6.0)
    add_text(b5, "Copy Text 1", "Copy Installer", 805, 77, 100, 16, size=12.0, weight="Medium", color=C_WASHI)

    # Card 2: npx skills
    add_rect(b5, "Term Card 2", 24, 175, 930, 140, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b5, "TC2 Title", "2. Or Install TinCan Skills Directly via npx skills:", 44, 190, 600, 18, font="Shippori Mincho", size=14.0, color=C_WASHI)
    add_rect(b5, "Cmd Box 2", 44, 220, 710, 40, fill=C_SUMI_WELL, stroke=C_WASHI_LINE, radius=6.0)
    add_text(b5, "Cmd Text 2", "npx skills add NoJuanNobody/tincan-skills -g -y", 58, 232, 680, 16, font="monospace", size=11.0, color=C_KAKI)
    add_rect(b5, "Copy Btn 2", 770, 220, 160, 40, fill=C_SUMI, stroke=C_WASHI_LINE, radius=6.0)
    add_text(b5, "Copy Text 2", "Copy Command", 805, 232, 100, 16, size=12.0, color=C_WASHI)

    # Card 3: Live CLI output HUD
    add_rect(b5, "Term Card 3", 24, 330, 930, 335, fill=C_SUMI_WELL, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b5, "TC3 Title", "3. Local CLI Identity & Operational Status", 44, 345, 500, 18, font="Shippori Mincho", size=14.0, color=C_WASHI)
    cli_lines = [
        "$ tincan whoami --json",
        "{",
        '  "alias": "default",',
        '  "address": "tc:rbxcv5ryvnmibok52jp7lo6t2ysegojnfuuxbznzcij7zvdgbqka",',
        '  "role": "admin",',
        '  "is_admin": true,',
        '  "public_key": "886e2af638ab5880b95dd25ff5bbd3d62443392d2d2970e5b91213fcd4660c14",',
        '  "relay_url": "https://iot-federated-agent-memory-production.up.railway.app",',
        '  "contacts_count": 2',
        "}",
        "$ tincan ping peer-primary-mac",
        "✓ Peer Mac Studio (M1 Max) online · 24ms RTT · Sealed Mailbox Ready"
    ]
    ty = 375
    for cl in cli_lines:
        add_text(b5, "CLI Line", cl, 44, ty, 880, 16, font="monospace", size=11.0, color=C_WASHI_QUIET if not cl.startswith("✓") else C_GREEN)
        ty += 20

    # =========================================================
    # ROW 2, COL 2: Window 6 — AI Brain Arena (`win-arena`)
    # =========================================================
    _, b6 = build_window_shell(canvas_id, "Win 06: AI Brain Arena (win-arena)", "Arena · AI Model Duel & Routing", "win-arena", cols[1], rows[1])
    # Prompt header
    add_rect(b6, "Arena Prompt Box", 24, 20, 930, 75, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b6, "Arena Prompt Title", "Active Arena Prompt Duel #104 · Architecture Challenge", 44, 32, 500, 18, font="Shippori Mincho", size=14.0, color=C_WASHI)
    add_text(b6, "Arena Prompt Text", "\"Design a zero-knowledge WebRTC TURN fallback relay with XSalsa20 encryption and monotonic sequence numbering.\"", 44, 56, 880, 18, size=12.0, color=C_KAKI)

    # Duel panes (w: 450 each)
    add_rect(b6, "Model A Box", 24, 110, 450, 430, fill=C_SUMI_WELL, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b6, "Model A Title", "Model A: Google Gemini 2.5 Pro", 44, 126, 350, 18, font="Shippori Mincho", size=15.0, color=C_WASHI)
    add_text(b6, "Model A Telemetry", "44.2 tok/s · 175ms TTFT · $1.25/M tokens", 44, 148, 350, 16, size=11.0, color=C_WASHI_DIM)
    gem_lines = [
        "class ZeroKnowledgeTurnRelay:",
        "    def __init__(self, key: bytes):",
        "        self.box = nacl.secret.SecretBox(key)",
        "        self.seq = 0",
        "",
        "    def forward_sealed(self, ciphertext: bytes):",
        "        self.seq += 1",
        "        # Relay never inspects plaintext",
        "        return emit_datagram(self.seq, ciphertext)",
    ]
    gy = 180
    for gl in gem_lines:
        add_text(b6, "Gem Line", gl, 44, gy, 410, 16, font="monospace", size=11.0, color=C_WASHI_QUIET)
        gy += 20
    add_rect(b6, "Vote A Btn", 44, 480, 410, 44, fill=C_KAKI, radius=8.0)
    add_text(b6, "Vote A Text", "Vote Model A (+150 XP)", 160, 493, 200, 18, size=13.0, weight="Medium", color=C_WASHI)

    add_rect(b6, "Model B Box", 498, 110, 450, 430, fill=C_SUMI_WELL, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b6, "Model B Title", "Model B: Anthropic Claude 3.7 Sonnet", 518, 126, 350, 18, font="Shippori Mincho", size=15.0, color=C_WASHI)
    add_text(b6, "Model B Telemetry", "39.1 tok/s · 210ms TTFT · $3.00/M tokens", 518, 148, 350, 16, size=11.0, color=C_WASHI_DIM)
    claude_lines = [
        "struct BlindRelayEnvelope {",
        "    seq: u64,",
        "    sender: [u8; 32],",
        "    box_payload: Vec<u8>,",
        "}",
        "",
        "impl BlindRelayEnvelope {",
        "    pub fn relay(&mut self) -> Result<()> {",
        "        self.verify_signature()?;",
        "        transmit_udp(self.seq, &self.box_payload)",
        "    }",
        "}",
    ]
    cly = 180
    for cl in claude_lines:
        add_text(b6, "Claude Line", cl, 518, cly, 410, 16, font="monospace", size=11.0, color=C_WASHI_QUIET)
        cly += 20
    add_rect(b6, "Vote B Btn", 518, 480, 410, 44, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=8.0)
    add_text(b6, "Vote B Text", "Vote Model B (+150 XP)", 635, 493, 200, 18, size=13.0, color=C_WASHI)

    # Bottom Arena Bar
    add_rect(b6, "Arena Stats Box", 24, 560, 930, 90, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b6, "Arena Stats Title", "Cumulative Duel Telemetry · 148 Matches Completed", 44, 575, 400, 18, font="Shippori Mincho", size=13.0, color=C_WASHI)
    add_text(b6, "Arena Stats Body", "Google Gemini 2.5 Pro (52% Win Rate · 1.2M tokens routed)  |  Anthropic Claude 3.7 Sonnet (48% Win Rate · 980K tokens routed)", 44, 605, 880, 16, size=12.0, color=C_WASHI_QUIET)

    # =========================================================
    # ROW 2, COL 3: Window 7 — Network & Peers (`win-network`)
    # =========================================================
    _, b7 = build_window_shell(canvas_id, "Win 07: Network & Peers (win-network)", "Network · Active Nodes & Telemetry", "win-network", cols[2], rows[1])
    # Metrics top
    mx = 24
    for mlabel, mval in [("🖥️ Peers Online", "2 Active"), ("🖱️ Web Visitors", "4 Connected"), ("⚡ Mesh RTT", "24ms Avg"), ("📶 Bandwidth", "3.2 Mbps")]:
        add_rect(b7, "Net Metric Box", mx, 20, 218, 64, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=8.0)
        add_text(b7, "Net Metric Label", mlabel, mx + 16, 30, 180, 16, size=11.0, color=C_WASHI_DIM)
        add_text(b7, "Net Metric Val", mval, mx + 16, 50, 180, 22, font="Shippori Mincho", size=16.0, weight="Medium", color=C_WASHI)
        mx += 237

    # Active peers table
    add_rect(b7, "Peers Frame", 24, 100, 930, 260, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b7, "Peers Head", "Active Mesh Workstations & Edge Streams", 44, 115, 400, 18, font="Shippori Mincho", size=14.0, color=C_WASHI)
    add_rect(b7, "Peer Row 1", 40, 145, 898, 90, fill=C_SUMI_WELL, stroke=C_WASHI_LINE, radius=8.0)
    add_text(b7, "P1 Title", "🖥️ Mac Studio (M1 Max) — peer-primary-mac", 56, 160, 400, 18, font="Shippori Mincho", size=14.0, color=C_WASHI)
    add_text(b7, "P1 Spec", "UDP Port 50004 · 1080p Video + Audio · 24ms RTT · 3.2 Mbps", 56, 182, 450, 16, size=11.0, color=C_GREEN)
    add_rect(b7, "P1 Call Btn", 710, 160, 100, 36, fill=C_KAKI, radius=6.0)
    add_text(b7, "P1 Call Text", "📞 Call", 740, 170, 50, 16, size=12.0, color=C_WASHI)
    add_rect(b7, "P1 Screen Btn", 825, 160, 100, 36, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=6.0)
    add_text(b7, "P1 Screen Text", "📺 Screen", 845, 170, 70, 16, size=12.0, color=C_WASHI)

    add_rect(b7, "Peer Row 2", 40, 245, 898, 90, fill=C_SUMI_WELL, stroke=C_WASHI_LINE, radius=8.0)
    add_text(b7, "P2 Title", "💻 Collaborator Node — peer-secondary-node", 56, 260, 400, 18, font="Shippori Mincho", size=14.0, color=C_WASHI)
    add_text(b7, "P2 Spec", "UDP Port 50006 · Audio Stream Only · 31ms RTT · 1.1 Mbps", 56, 282, 450, 16, size=11.0, color=C_WASHI_QUIET)
    add_rect(b7, "P2 Call Btn", 710, 260, 100, 36, fill=C_KAKI, radius=6.0)
    add_text(b7, "P2 Call Text", "📞 Call", 740, 270, 50, 16, size=12.0, color=C_WASHI)
    add_rect(b7, "P2 Screen Btn", 825, 260, 100, 36, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=6.0)
    add_text(b7, "P2 Screen Text", "💬 Ping", 855, 270, 50, 16, size=12.0, color=C_WASHI)

    # Web visitors table
    add_rect(b7, "Visitors Frame", 24, 380, 930, 280, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b7, "Visitors Head", "Active Web Browser Sessions & Focused Windows", 44, 395, 400, 18, font="Shippori Mincho", size=14.0, color=C_WASHI)
    v_rows = [
        ("🖱️ User-7782 (Local macOS)", "Focused: win-board", "Active now (0s)", C_GREEN),
        ("🖱️ User-9104 (Chrome Win11)", "Focused: win-tv", "Active 8s ago", C_WASHI_QUIET),
        ("🤖 Agent-Grok (xAI Connector)", "Focused: win-agentspace", "Active 14s ago", C_WASHI_QUIET),
        ("🖱️ User-1049 (Safari iOS)", "Focused: win-terminal", "Active 32s ago", C_WASHI_DIM),
    ]
    vy = 430
    for vname, vfocus, vdiff, vcol in v_rows:
        add_rect(b7, "V Row", 40, vy, 898, 45, fill=C_SUMI_WELL, stroke=C_WASHI_LINE, radius=6.0)
        add_text(b7, "V Name", vname, 56, vy + 14, 300, 18, size=12.0, weight="Medium", color=C_WASHI)
        add_text(b7, "V Focus", vfocus, 420, vy + 14, 250, 18, font="monospace", size=11.0, color=C_KAKI)
        add_text(b7, "V Diff", vdiff, 760, vy + 14, 150, 18, size=11.0, color=vcol)
        vy += 53

    # =========================================================
    # ROW 2, COL 4: Window 8 — Quests & Tiers (`win-quests`)
    # =========================================================
    _, b8 = build_window_shell(canvas_id, "Win 08: Quests & Tiers (win-quests)", "Quests · Federated Readiness & XP", "win-quests", cols[3], rows[1])
    # Tier Progress Card
    add_rect(b8, "Tier Card", 24, 20, 930, 130, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b8, "Tier Title", "Tier L3: Cryptographic Multi-Account Bridge", 44, 35, 500, 22, font="Shippori Mincho", size=17.0, color=C_WASHI)
    add_text(b8, "Tier Sub", "550 / 1000 XP · 450 XP required to unlock Tier L4: CRDT Gossip Matrix", 44, 62, 500, 16, size=12.0, color=C_WASHI_QUIET)
    # Progress Bar
    add_rect(b8, "Tier Bar BG", 44, 90, 880, 8, fill=C_SUMI_WELL, radius=4.0)
    add_rect(b8, "Tier Bar Fill", 44, 90, 484, 8, fill=C_KAKI, radius=4.0)
    add_text(b8, "Themes Label", "Unlocked Themes: [Slate] [Amber CRT] [Crypto Emerald]", 44, 112, 500, 16, size=11.0, color=C_KAKI)

    # Quests Grid (6 cards, 2 cols x 3 rows)
    q_data = [
        ("First Handshake", "+50 XP · Completed by 2 nodes", "Connect a workstation or WebRTC peer to the mesh", True),
        ("Sealed Courier", "+100 XP · Completed by 1 node", "Send an Ed25519-signed ciphertext envelope", True),
        ("Zero-Knowledge Reader", "+75 XP · In Progress", "Poll and verify a sealed TinCan mailbox", False),
        ("Synapse Arbiter", "+150 XP · Available", "Run a dual-model AI Arena match and vote on winner", False),
        ("Broadcast DJ", "+125 XP · Available", "Ingest a video into the Relay Watch Party collection", False),
        ("HITL Commander", "+200 XP · Completed", "Approve and trigger a cooperative peer action", True),
    ]
    q_coords = [
        (24, 165), (498, 165),
        (24, 325), (498, 325),
        (24, 485), (498, 485),
    ]
    for idx, (qname, qbadge, qdesc, qdone) in enumerate(q_data):
        qx, qy = q_coords[idx]
        add_rect(b8, f"Q Card {idx}", qx, qy, 450, 140, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=10.0)
        add_text(b8, f"Q Title {idx}", ("🟢 " if qdone else "⚡ ") + qname, qx + 20, qy + 18, 300, 20, font="Shippori Mincho", size=14.0, weight="Medium", color=C_WASHI)
        add_rect(b8, f"Q Badge {idx}", qx + 320, qy + 14, 110, 24, fill=C_SUMI_WELL, stroke=C_KAKI_DIM if not qdone else None, radius=999.0)
        add_text(b8, f"Q Badge Txt {idx}", "+XP Reward", qx + 338, qy + 19, 90, 14, size=10.0, color=C_KAKI if not qdone else C_GREEN)
        add_text(b8, f"Q Desc {idx}", qdesc, qx + 20, qy + 48, 410, 36, size=12.0, color=C_WASHI_QUIET)
        status_txt = "✓ Completed & Attested" if qdone else "Pending Action Trigger"
        add_text(b8, f"Q Status {idx}", status_txt, qx + 20, qy + 98, 300, 16, size=11.0, color=C_GREEN if qdone else C_WASHI_DIM)

    # =========================================================
    # ROW 3, COL 1: Window 9 — Tokens & Sponsoring (`win-billing`)
    # =========================================================
    _, b9 = build_window_shell(canvas_id, "Win 09: Tokens & Billing (win-billing)", "Tokens · Balance & Sponsoring Studio", "win-billing", cols[0], rows[2])
    # Balance Banner
    add_rect(b9, "Balance Card", 24, 20, 930, 95, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b9, "Bal Title", "Current Token Balance", 44, 34, 300, 18, font="Shippori Mincho", size=14.0, color=C_WASHI_DIM)
    add_text(b9, "Bal Big", "14,500 Token Credits", 44, 56, 400, 36, font="Shippori Mincho", size=28.0, weight="Medium", color=C_WASHI)
    add_text(b9, "Bal Equiv", "≈ $14.50 USD Value · Zero Relaying Surcharge · S3 Mirror Ledger", 480, 62, 450, 18, size=12.0, color=C_KAKI)

    # Sponsoring Studio
    add_rect(b9, "Sponsor Box", 24, 130, 930, 240, fill=C_SUMI_WELL, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b9, "Sponsor Title", "Sponsored Ad Viewer Studio · Watch to Earn Tokens", 44, 145, 500, 20, font="Shippori Mincho", size=15.0, color=C_WASHI)
    add_rect(b9, "Sponsor Video Box", 44, 180, 420, 170, fill=C_SUMI, stroke=C_WASHI_LINE, radius=8.0)
    add_text(b9, "Sponsor Clip Label", "Sponsored: Antigravity AI Coding Agent", 60, 200, 380, 18, font="Shippori Mincho", size=13.0, color=C_WASHI)
    add_text(b9, "Sponsor Countdown", "0:15 / 0:30 · Reward Unlockable at Finish", 60, 230, 350, 16, size=11.0, color=C_WASHI_DIM)
    add_rect(b9, "Claim Reward Btn", 500, 240, 430, 48, fill=C_KAKI, radius=8.0)
    add_text(b9, "Claim Reward Text", "🎁 Watch 15s & Claim +50 Tokens", 600, 254, 250, 18, size=13.0, weight="Medium", color=C_WASHI)

    # Packages
    add_text(b9, "Pkg Title", "Token Refill Packages", 24, 385, 300, 18, font="Shippori Mincho", size=14.0, color=C_WASHI)
    px = 24
    pkgs = [
        ("Starter Pack", "5,000 Tokens", "$5.00 USD", "Basic AI model queries & relay messages"),
        ("Operator Pack", "25,000 Tokens", "$20.00 USD (20% Off)", "High-volume dual AI Arena duels & WebRTC calls"),
        ("Messiah Node", "100,000 Tokens", "$70.00 USD (30% Off)", "Full studio deployment & persistent memory hosting"),
    ]
    for pname, ptok, pcost, pdesc in pkgs:
        add_rect(b9, "Pkg Card", px, 415, 298, 240, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=10.0)
        add_text(b9, "P Name", pname, px + 20, 435, 250, 20, font="Shippori Mincho", size=16.0, color=C_WASHI)
        add_text(b9, "P Tok", ptok, px + 20, 465, 250, 24, font="Shippori Mincho", size=20.0, weight="Medium", color=C_KAKI)
        add_text(b9, "P Cost", pcost, px + 20, 498, 250, 16, size=12.0, color=C_WASHI_QUIET)
        add_text(b9, "P Desc", pdesc, px + 20, 526, 250, 36, size=11.0, color=C_WASHI_DIM)
        add_rect(b9, "P Buy Btn", px + 20, 595, 258, 40, fill=C_SUMI_WELL, stroke=C_WASHI_LINE, radius=6.0)
        add_text(b9, "P Buy Text", "Select Package", px + 95, 606, 120, 16, size=12.0, color=C_WASHI)
        px += 316

    # =========================================================
    # ROW 3, COL 2: Window 10 — Mesh Moderator (`win-moderator`)
    # =========================================================
    _, b10 = build_window_shell(canvas_id, "Win 10: Moderator (win-moderator)", "Moderator · Admin Governance Console", "win-moderator", cols[1], rows[2])
    # Admin security badge
    add_rect(b10, "Mod Banner", 24, 20, 930, 60, fill=C_SUMI_CARD, stroke=C_KAKI_DIM, radius=8.0)
    add_text(b10, "Mod Banner Text", "🔒 Administrator Console · Verified Operator Privilege (Role: Admin)", 44, 38, 600, 20, font="Shippori Mincho", size=14.0, color=C_KAKI)

    # Broadcast transmitter
    add_rect(b10, "Bcast Box", 24, 95, 930, 115, fill=C_SUMI_WELL, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b10, "Bcast Title", "Emergency Mesh Broadcast Transmitter", 44, 110, 400, 18, font="Shippori Mincho", size=13.0, color=C_WASHI)
    add_rect(b10, "Bcast Input", 44, 140, 660, 44, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=6.0)
    add_text(b10, "Bcast Placeholder", "Enter announcement text to broadcast to all connected peer nodes...", 58, 153, 600, 16, size=12.0, color=C_WASHI_DIM)
    add_rect(b10, "Bcast Btn", 720, 140, 210, 44, fill=C_KAKI, radius=6.0)
    add_text(b10, "Bcast Btn Text", "📢 Send Broadcast", 760, 153, 150, 18, size=13.0, weight="Medium", color=C_WASHI)

    # Active peer control table
    add_rect(b10, "Mod Table Frame", 24, 225, 930, 240, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b10, "Mod Table Title", "Live Peer Node Access & Enforcement", 44, 240, 400, 18, font="Shippori Mincho", size=13.0, color=C_WASHI)
    mod_rows = [
        ("peer-primary-mac", "Mac Studio (M1 Max)", "50004", "Connected 14m", "Host Node (Protected)"),
        ("peer-secondary-node", "Collaborator Node", "50006", "Connected 8m", "Active"),
        ("peer-visitor-3312", "WebRTC Visitor", "50012", "Connected 2m", "Active"),
    ]
    my = 275
    for pid, pname, pport, pconn, pstat in mod_rows:
        add_rect(b10, "Mod Row", 40, my, 898, 44, fill=C_SUMI_WELL, stroke=C_WASHI_LINE, radius=6.0)
        add_text(b10, "Mod PID", pid, 56, my + 13, 200, 16, font="monospace", size=11.0, color=C_WASHI)
        add_text(b10, "Mod PName", pname, 260, my + 13, 220, 16, size=12.0, color=C_WASHI_QUIET)
        add_text(b10, "Mod PPort", f"Port {pport}", 500, my + 13, 100, 16, font="monospace", size=11.0, color=C_WASHI_DIM)
        add_text(b10, "Mod PConn", pconn, 620, my + 13, 120, 16, size=11.0, color=C_GREEN)
        if "Host" in pstat:
            add_text(b10, "Mod Host", "● Host", 800, my + 13, 100, 16, size=11.0, color=C_WASHI_DIM)
        else:
            add_rect(b10, "Mod Kick", 770, my + 8, 65, 28, fill=C_RUST, radius=4.0)
            add_text(b10, "Mod Kick Text", "Kick", 788, my + 14, 40, 14, size=11.0, color=C_WASHI)
            add_rect(b10, "Mod Mute", 845, my + 8, 65, 28, fill=C_SUMI, stroke=C_WASHI_LINE, radius=4.0)
            add_text(b10, "Mod Mute Text", "Mute", 863, my + 14, 40, 14, size=11.0, color=C_WASHI_QUIET)
        my += 52

    # Sponsor and Video Management
    add_rect(b10, "Video Studio Box", 24, 480, 930, 180, fill=C_SUMI_WELL, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b10, "Studio Title", "Video Playlist & Sponsor Ad Moderation Studio", 44, 495, 450, 18, font="Shippori Mincho", size=13.0, color=C_WASHI)
    add_text(b10, "Studio Sub", "Ingest direct S3 MP4 uploads, configure programmatic ads, and update video duration metadata.", 44, 520, 700, 16, size=11.0, color=C_WASHI_DIM)
    add_rect(b10, "Studio Btn 1", 44, 560, 240, 44, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=6.0)
    add_text(b10, "Studio Btn 1 Text", "🎬 Ingest S3 Video", 95, 573, 160, 18, size=12.0, color=C_WASHI)
    add_rect(b10, "Studio Btn 2", 300, 560, 240, 44, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=6.0)
    add_text(b10, "Studio Btn 2 Text", "📊 Sponsor Analytics", 345, 573, 160, 18, size=12.0, color=C_WASHI)
    add_rect(b10, "Studio Btn 3", 560, 560, 240, 44, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=6.0)
    add_text(b10, "Studio Btn 3 Text", "🔄 Refresh Cloud State", 605, 573, 160, 18, size=12.0, color=C_KAKI)

    # =========================================================
    # ROW 3, COL 3: Window 11 — Citizen Registration Gate (`accountSetupModal`)
    # =========================================================
    _, b11 = build_window_shell(canvas_id, "Win 11: Registration Gate (accountSetupModal)", "Identity · Enter the Mesh Gate", "gate-modal", cols[2], rows[2])
    # Modal Core Card
    add_rect(b11, "Gate Modal Box", 60, 25, 860, 620, fill=C_SUMI_WELL, stroke=C_WASHI_LINE, radius=16.0)
    add_rect(b11, "Gate Stamp", 85, 50, 44, 44, fill=C_KAKI, radius=8.0)
    add_text(b11, "Stamp Emoji", "✍️", 96, 60, 24, 24, size=20.0, color=C_WASHI)
    add_text(b11, "Gate Heading", "Enter the Mesh & Claim Citizen Badge", 145, 50, 600, 28, font="Shippori Mincho", size=22.0, weight="Medium", color=C_WASHI)
    add_text(b11, "Gate Sub", "Zero-account cryptographic identity. Watching is free; tools require registered citizen attestation.", 145, 80, 700, 18, size=12.0, color=C_WASHI_QUIET)

    # Form Fields
    fields = [
        ("Full Legal Name", "Alejandro Londono"),
        ("Cyberspace Handle (@username)", "@nojuannobody"),
        ("Contact Email Address", "alondono11@gmail.com"),
        ("Academic Institution & ID", "Florida Atlantic University (FAU) · Z23961745"),
    ]
    fy = 125
    for flabel, fval in fields:
        add_text(b11, "Field Label", flabel, 85, fy, 400, 16, size=12.0, color=C_WASHI_QUIET)
        add_rect(b11, "Field Box", 85, fy + 22, 810, 42, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=6.0)
        add_text(b11, "Field Val", fval, 100, fy + 33, 600, 18, font="monospace" if "@" in fval or "Z23" in fval else "Zen Kaku Gothic New", size=13.0, color=C_WASHI)
        fy += 78

    # Consent Checkbox
    add_rect(b11, "Consent Checkbox", 85, 450, 20, 20, fill=C_KAKI, radius=4.0)
    add_text(b11, "Check Mark", "✓", 90, 451, 14, 16, size=12.0, color=C_WASHI)
    add_text(b11, "Consent Text", "I agree to publish public attestations and receive peer encrypted messages.", 115, 451, 700, 18, size=12.0, color=C_WASHI_QUIET)

    # Action Buttons
    add_rect(b11, "Submit Gate Btn", 85, 500, 810, 52, fill=C_KAKI, radius=8.0)
    add_text(b11, "Submit Gate Text", "✅ Enter the Mesh & Attest Identity", 360, 516, 300, 20, font="Shippori Mincho", size=16.0, weight="Medium", color=C_WASHI)

    add_rect(b11, "Dismiss Gate Btn", 85, 565, 810, 42, fill=C_SUMI_SOFT, stroke=C_WASHI_LINE, radius=8.0)
    add_text(b11, "Dismiss Gate Text", "Not now — Return to ambient video feed (Esc)", 335, 577, 350, 18, size=13.0, color=C_WASHI_DIM)

    # =========================================================
    # ROW 3, COL 4: Panel 12 — Zen Design System & Component Tokens Guide
    # =========================================================
    _, b12 = build_window_shell(canvas_id, "Win 12: Design Tokens (tokens-guide)", "Zen Tokens · Design System Specification", "spec-guide", cols[3], rows[2])
    add_text(b12, "Spec Title", "Architectural Tokens & Component Contracts", 24, 20, 600, 20, font="Shippori Mincho", size=16.0, color=C_WASHI)
    add_text(b12, "Spec Intro", "Enforces the calm ink-and-paper aesthetic across all window interiors.", 24, 45, 800, 16, size=12.0, color=C_WASHI_QUIET)

    # Token Matrices
    add_rect(b12, "Color Box", 24, 75, 450, 270, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b12, "Color Title", "1. Color Matrix", 44, 90, 200, 18, font="Shippori Mincho", size=14.0, color=C_WASHI)
    c_specs = [
        ("Sumi (#0E0D0B)", "Canvas & Viewport Well"),
        ("Sumi-Soft (#17150F)", "Window Body & Cards"),
        ("Washi (#ECE6DA)", "Primary Typography"),
        ("Kaki (#D0703F)", "Primary Action & Active"),
        ("Washes (Rust/Moss/Indigo)", "Atmospheric Rims"),
    ]
    csy = 120
    for cname, cdesc in c_specs:
        add_text(b12, "CS Name", cname, 44, csy, 220, 16, font="monospace", size=11.0, color=C_KAKI)
        add_text(b12, "CS Desc", cdesc, 250, csy, 200, 16, size=11.0, color=C_WASHI_QUIET)
        csy += 26

    add_rect(b12, "Typo Box", 498, 75, 450, 270, fill=C_SUMI_CARD, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b12, "Typo Title", "2. Typography Contracts", 518, 90, 250, 18, font="Shippori Mincho", size=14.0, color=C_WASHI)
    t_specs = [
        ("Shippori Mincho", "Window Titles, Headings, Marks"),
        ("Zen Kaku Gothic", "Body Text, Inputs, Buttons, Tabs"),
        ("Monospace (JetBrains)", "Hashes, Ports, Addresses, Code"),
        ("Letter Spacing: -0.01em", "High-contrast editorial serif"),
    ]
    tsy = 120
    for tname, tdesc in t_specs:
        add_text(b12, "TS Name", tname, 518, tsy, 200, 16, font="monospace", size=11.0, color=C_WASHI)
        add_text(b12, "TS Desc", tdesc, 710, tsy, 220, 16, size=11.0, color=C_WASHI_QUIET)
        tsy += 26

    add_rect(b12, "Arch Box", 24, 365, 924, 290, fill=C_SUMI_WELL, stroke=C_WASHI_LINE, radius=10.0)
    add_text(b12, "Arch Title", "3. Implementation Strategy · Modular Injection via zen_shell.py", 44, 380, 600, 18, font="Shippori Mincho", size=14.0, color=C_WASHI)
    arch_notes = [
        "- Zero Merge Conflicts: Overrides are injected via apply_zen_shell() at boot time.",
        "- CSS Scoping: Styles target .mesh-window and window interiors under body.zen.",
        "- Preserves Logic: JavaScript event handlers (e.g. WebRTC, arena voting, VFS) remain intact.",
        "- Accessibility: High-contrast text ratios exceeding WCAG AAA standards on dark backgrounds.",
        "- Single-Window Routes: Pop-outs (?window=) and standalone routes (/tv, /board) inherit Zen skin."
    ]
    any = 415
    for an in arch_notes:
        add_text(b12, "Arch Note", an, 44, any, 880, 16, size=12.0, color=C_WASHI_QUIET)
        any += 28

    # Assemble Document JSON
    doc = {
        "format": "figcraft",
        "version": 1,
        "imageIndex": [],
        "name": "TinCan Mesh OS — Zen Windows Contact Sheet",
        "pages": [page_id],
        "nodes": {
            str(page_id): {
                "id": page_id,
                "name": "Page 1",
                "type": "page",
                "background": {
                    "r": 0.0549,
                    "g": 0.0509,
                    "b": 0.0431,
                    "a": 1.0
                },
                "flows": [],
                "prototype": {
                    "device": "None",
                    "background": {
                        "r": 0.0549,
                        "g": 0.0509,
                        "b": 0.0431,
                        "a": 1.0
                    },
                    "rotation": "portrait"
                },
                "guides": [],
                "children": [canvas_id],
                "width": canvas_w,
                "height": canvas_h
            }
        },
        "next_id": next_id,
        "styles": [],
        "variables": {"collections": [], "variables": []},
        "current_page": page_id,
        "document_colors": [],
        "comments": []
    }
    doc["nodes"].update(nodes)

    print(f"[*] Generated {len(doc['nodes'])} FigCraft nodes across 11 windows + token guide.")

    # Write document.json to zip
    with zipfile.ZipFile(FIGCRAFT_PATH, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("document.json", json.dumps(doc, indent=2))
        # Add a placeholder thumbnail
        z.writestr("thumbnail.png", b"")

    print(f"[✓] Successfully wrote FigCraft design to: {FIGCRAFT_PATH}")


if __name__ == "__main__":
    main()
