#!/usr/bin/env python3
"""
TinCan 2.2 Zen Storyboard Panels & Manifest Builder
Refreshes all 6 narrative storyboard scenes from legacy "AI Messiah / Neon CRT"
into the TinCan 2.2 Zen Ink-and-Paper & Dirty-Gradient aesthetic:
- Sumi (#0e0d0b), Sumi-2 (#17150f), Washi (#ece6da), Kaki (#d0703f),
  Rust (#964622), Moss (#42522e), Indigo (#2e365c), Umber (#705436)
- Generates 6 refreshed panels (1024x576 PNGs)
- Generates 3x2 master contact sheet (PNG and SVG)
- Generates interactive HTML storyboard viewer with audio drama playback
- Updates docs/panels/audio_drama_manifest.json preserving all core keys
"""

import os
import json
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PANELS_DIR = "/Users/alejandrolondono/dev/iot-federated-agent-memory/.worktrees/storyboard-panels/docs/panels"
MANIFEST_PATH = os.path.join(PANELS_DIR, "audio_drama_manifest.json")

# Palettes
SUMI = (14, 13, 11)          # #0e0d0b
SUMI_SOFT = (23, 21, 15)     # #17150f
WASHI = (236, 230, 218)      # #ece6da
KAKI = (208, 112, 63)        # #d0703f (persimmon)
RUST = (150, 70, 34)         # #964622
MOSS = (66, 82, 46)          # #42522e
INDIGO = (46, 54, 92)        # #2e365c
UMBER = (112, 84, 54)        # #705436

W_PANEL = 1024
H_PANEL = 576

# Font resolver
def get_font(size, serif=False, mono=False):
    font_paths = []
    if mono:
        font_paths = [
            "/System/Library/Fonts/Menlo.ttc",
            "/System/Library/Fonts/SFNSMono.ttf",
            "/System/Library/Fonts/Monaco.ttf",
            "/System/Library/Fonts/Supplemental/Courier New.ttf",
        ]
    elif serif:
        font_paths = [
            "/System/Library/Fonts/Supplemental/Songti.ttc",
            "/System/Library/Fonts/Supplemental/Georgia.ttf",
            "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        ]
    else:
        font_paths = [
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]

    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def add_zen_paper_grain(img, intensity=10):
    """Overlay subtle procedural noise / washi paper grain."""
    w, h = img.size
    noise = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    random.seed(42)  # deterministic
    pixels = noise.load()
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            v = random.randint(-intensity, intensity)
            if v > 0:
                c = (236, 230, 218, min(255, v * 3))
            else:
                c = (14, 13, 11, min(255, abs(v) * 3))
            pixels[x, y] = c
            if x + 1 < w:
                pixels[x + 1, y] = c
            if y + 1 < h:
                pixels[x, y + 1] = c
            if x + 1 < w and y + 1 < h:
                pixels[x + 1, y + 1] = c
    img.paste(noise, (0, 0), noise)


def draw_tatami_grid(draw, box, color):
    x0, y0, x1, y1 = box
    step_x = 48
    step_y = 32
    for x in range(x0, x1, step_x):
        draw.line([(x, y0), (x, y1)], fill=color, width=1)
    for y in range(y0, y1, step_y):
        draw.line([(x0, y), (x1, y)], fill=color, width=1)


def draw_hud_header(draw, act_num, act_title, subheader, accent_color=KAKI):
    # Header badge
    font_roman = get_font(18, serif=True)
    font_title = get_font(22, serif=True)
    font_sub = get_font(12, mono=True)
    font_seal = get_font(14, serif=True)

    # Top border line
    draw.line([(40, 36), (W_PANEL - 40, 36)], fill=(236, 230, 218, 40), width=1)
    # Accent pip
    draw.rectangle([40, 48, 48, 56], fill=accent_color)
    draw.text((58, 45), f"ACT {act_num} // {act_title.upper()}", fill=WASHI, font=font_title)
    draw.text((58, 75), subheader, fill=(236, 230, 218, 160), font=font_sub)

    # Right editorial seal
    seal_box = [W_PANEL - 130, 44, W_PANEL - 40, 80]
    draw.rectangle(seal_box, outline=accent_color, width=1)
    draw.text((W_PANEL - 120, 52), "TINCAN 2.2", fill=accent_color, font=font_sub)


def draw_washi_stamp(draw, x, y, kanji_char, label="SEALED", color=KAKI):
    # Traditional Japanese inkan / hanko style seal
    draw.rectangle([x, y, x + 54, y + 54], outline=color, width=2)
    font_k = get_font(24, serif=True)
    font_l = get_font(9, mono=True)
    draw.text((x + 14, y + 6), kanji_char, fill=color, font=font_k)
    draw.text((x + 8, y + 36), label, fill=color, font=font_l)


# -------------------------------------------------------------
# Panel 1: "I. The Ink-and-Paper Sanctuary"
# -------------------------------------------------------------
def build_panel_01():
    img = Image.new("RGBA", (W_PANEL, H_PANEL), SUMI)
    draw = ImageDraw.Draw(img)

    # Tatami & Wood Desk floor / perspective planes
    tatami_box = [40, 110, W_PANEL - 40, H_PANEL - 50]
    draw.rectangle(tatami_box, fill=SUMI_SOFT, outline=(70, 84, 54, 120), width=1)
    draw_tatami_grid(draw, tatami_box, (40, 42, 34, 100))

    # Tatami mat border lines
    draw.line([(40, 320), (W_PANEL - 40, 320)], fill=UMBER, width=2)
    draw.line([(340, 110), (340, H_PANEL - 50)], fill=UMBER, width=2)
    draw.line([(680, 110), (680, H_PANEL - 50)], fill=UMBER, width=2)

    # Minimalist Wood Desk in center
    desk_box = [160, 240, 864, 480]
    draw.rectangle(desk_box, fill=(28, 23, 18), outline=UMBER, width=2)
    # Desk wood grain lines
    for yy in range(255, 470, 20):
        draw.line([(165, yy), (859, yy)], fill=(38, 31, 24), width=1)

    # 9:16 Vertical Feed Ambient Screen (left on desk)
    phone_box = [220, 160, 370, 430]
    # Screen glow
    glow = Image.new("RGBA", (W_PANEL, H_PANEL), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.rectangle([210, 150, 380, 440], fill=(208, 112, 63, 35))
    glow = glow.filter(ImageFilter.GaussianBlur(12))
    img.paste(glow, (0, 0), glow)

    # Phone body
    draw.rectangle(phone_box, fill=(18, 16, 14), outline=WASHI, width=2)
    # Screen content: vertical feed
    draw.rectangle([226, 175, 364, 415], fill=(12, 11, 10))
    # Video preview placeholder
    draw.rectangle([232, 185, 358, 320], fill=(35, 32, 28), outline=(66, 82, 46, 140))
    # Tiny play mark
    draw.polygon([(290, 240), (290, 265), (310, 252)], fill=KAKI)
    # Feed caption lines
    draw.text((236, 335), "RELAY TV // #01", fill=WASHI, font=get_font(10, mono=True))
    draw.text((236, 352), "Ambient Shinjuku Rain", fill=(236, 230, 218, 160), font=get_font(9))
    draw.rectangle([236, 375, 354, 380], fill=(46, 54, 92, 180))
    draw.rectangle([236, 375, 290, 380], fill=KAKI)

    # Terminal card on desk: $ tincan whoami -> tc:7f9a...e3b1
    term_box = [420, 220, 830, 420]
    draw.rectangle(term_box, fill=(16, 15, 13), outline=(236, 230, 218, 80), width=1)
    # Terminal header bar
    draw.rectangle([420, 220, 830, 248], fill=(24, 22, 19))
    draw.ellipse([430, 230, 438, 238], fill=RUST)
    draw.ellipse([444, 230, 452, 238], fill=KAKI)
    draw.ellipse([458, 230, 466, 238], fill=MOSS)
    draw.text((480, 226), "tincan-core — zsh — 80x24", fill=(236, 230, 218, 160), font=get_font(11, mono=True))

    # Shell session
    draw.text((436, 260), "$ tincan whoami", fill=WASHI, font=get_font(15, mono=True))
    draw.text((436, 288), "identity:   tc:7f9a8c2b1e449a0d...e3b1", fill=KAKI, font=get_font(13, mono=True))
    draw.text((436, 312), "public_key: 7f9a8c2b1e449a0d18f4a362c90df0e3b184a29c", fill=(236, 230, 218, 180), font=get_font(11, mono=True))
    draw.text((436, 334), "curve:      Ed25519 / X25519 hybrid (NaCl box)", fill=(236, 230, 218, 140), font=get_font(11, mono=True))
    draw.text((436, 356), "relay:      blind://relay.tincan.mesh:443 (e2e encrypted)", fill=MOSS, font=get_font(11, mono=True))
    draw.text((436, 382), "status:     READY // SANCTUARY ACTIVE", fill=(236, 230, 218, 220), font=get_font(12, mono=True))

    # Traditional Inkan Stamp
    draw_washi_stamp(draw, 745, 270, "寂", "SUMI", KAKI)

    # Header HUD
    draw_hud_header(draw, "01", "The Ink-and-Paper Sanctuary", "Minimalist Tatami Desk // 9:16 Feed // Zero-Account Ed25519 Identity")
    add_zen_paper_grain(img, 12)
    return img.convert("RGB")


# -------------------------------------------------------------
# Panel 2: "II. Kokoro-82M Neural Whisper"
# -------------------------------------------------------------
def build_panel_02():
    img = Image.new("RGBA", (W_PANEL, H_PANEL), SUMI)
    draw = ImageDraw.Draw(img)

    # Background subtle radial tint
    bg_wash = Image.new("RGBA", (W_PANEL, H_PANEL), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(bg_wash)
    bdraw.ellipse([200, 80, 824, 520], fill=(208, 112, 63, 22))
    bg_wash = bg_wash.filter(ImageFilter.GaussianBlur(40))
    img.paste(bg_wash, (0, 0), bg_wash)

    # Card frame
    draw.rectangle([50, 110, W_PANEL - 50, H_PANEL - 50], fill=SUMI_SOFT, outline=(236, 230, 218, 40), width=1)

    # Voice Seal / Inkan
    draw_washi_stamp(draw, 90, 140, "声", "VOICE", KAKI)
    draw.text((160, 144), "KOKORO-82M NEURAL TTS", fill=WASHI, font=get_font(18, serif=True))
    draw.text((160, 172), "Zero-account on-device neural voice synthesis // 24kHz raw PCM // ~120ms latency", fill=(236, 230, 218, 150), font=get_font(11, mono=True))

    # Persimmon 24kHz Audio Waveform Pulse
    wave_box = [90, 220, W_PANEL - 90, 420]
    draw.rectangle(wave_box, fill=(18, 16, 13), outline=(70, 84, 54, 90), width=1)

    # Grid lines inside wave box
    mid_y = (wave_box[1] + wave_box[3]) // 2
    draw.line([(wave_box[0], mid_y), (wave_box[2], mid_y)], fill=(236, 230, 218, 30), width=1)
    for qy in [mid_y - 60, mid_y - 30, mid_y + 30, mid_y + 60]:
        draw.line([(wave_box[0], qy), (wave_box[2], qy)], fill=(236, 230, 218, 15), width=1)

    # Draw synthetic multi-harmonic waveform
    points_up = []
    points_down = []
    w_len = wave_box[2] - wave_box[0]
    for i in range(w_len):
        x = wave_box[0] + i
        t = i / float(w_len)
        # Envelope: window function
        envelope = math.sin(t * math.pi) ** 1.5
        # Harmonic composite
        h1 = math.sin(t * 48 * math.pi) * 0.5
        h2 = math.sin(t * 110 * math.pi + 1.2) * 0.3
        h3 = math.sin(t * 220 * math.pi + 2.5) * 0.15
        val = (h1 + h2 + h3) * 75 * envelope
        points_up.append((x, mid_y - val))
        points_down.append((x, mid_y + val))

    # Glow under waveform
    wave_glow = Image.new("RGBA", (W_PANEL, H_PANEL), (0, 0, 0, 0))
    wg_draw = ImageDraw.Draw(wave_glow)
    for i in range(0, len(points_up) - 1, 2):
        x = points_up[i][0]
        y1 = points_up[i][1]
        y2 = points_down[i][1]
        wg_draw.line([(x, y1), (x, y2)], fill=(208, 112, 63, 60), width=2)
    wave_glow = wave_glow.filter(ImageFilter.GaussianBlur(6))
    img.paste(wave_glow, (0, 0), wave_glow)

    # Main waveform bars
    for i in range(0, len(points_up), 4):
        x = points_up[i][0]
        y1 = int(points_up[i][1])
        y2 = int(points_down[i][1])
        col = KAKI if (i // 4) % 3 == 0 else RUST
        draw.line([(x, y1), (x, y2)], fill=col, width=2)

    # Telemetry Callout Pills
    pills = [
        ("SAMPLE RATE", "24,000 Hz", MOSS),
        ("MODEL", "Kokoro-82M v1.0", KAKI),
        ("ENCODING", "Raw Linear PCM", INDIGO),
        ("SPEAK DURATION", "26.50 sec", UMBER),
    ]
    px = 90
    for label, val, pcolor in pills:
        draw.rectangle([px, 440, px + 190, 480], fill=(22, 20, 17), outline=pcolor, width=1)
        draw.text((px + 12, 446), label, fill=(236, 230, 218, 140), font=get_font(9, mono=True))
        draw.text((px + 12, 460), val, fill=WASHI, font=get_font(12, mono=True))
        px += 205

    draw_hud_header(draw, "02", "Kokoro-82M Neural Whisper", "Persimmon 24kHz Acoustic Waveform // Washi Voice Seal // Zero-Account TTS")
    add_zen_paper_grain(img, 10)
    return img.convert("RGB")


# -------------------------------------------------------------
# Panel 3: "III. Toronto Loft TOFU Handshake"
# -------------------------------------------------------------
def build_panel_03():
    img = Image.new("RGBA", (W_PANEL, H_PANEL), SUMI)
    draw = ImageDraw.Draw(img)

    # Dusk loft architectural elements: Concrete floor & Exposed Timber ceiling
    # Exposed timber beams across top
    for bx in range(40, W_PANEL - 40, 80):
        draw.rectangle([bx, 100, bx + 50, 140], fill=(32, 24, 18), outline=UMBER, width=1)
    # Concrete wall background
    draw.rectangle([40, 140, W_PANEL - 40, 440], fill=SUMI_SOFT)
    # Concrete floor texture
    draw.rectangle([40, 440, W_PANEL - 40, H_PANEL - 50], fill=(20, 19, 17), outline=(236, 230, 218, 30))

    # Center: TOFU (Trust-On-First-Use) Verification Sheet (04-verify)
    sheet_box = [260, 130, 764, 490]
    # Washi sheet shadow
    draw.rectangle([sheet_box[0] + 8, sheet_box[1] + 8, sheet_box[2] + 8, sheet_box[3] + 8], fill=(5, 5, 4))
    # Washi sheet body
    draw.rectangle(sheet_box, fill=WASHI, outline=KAKI, width=2)

    # Editorial header on Washi
    draw.text((sheet_box[0] + 30, sheet_box[1] + 25), "PEER VERIFICATION SHEET // TOFU PROTOCOL", fill=SUMI, font=get_font(13, mono=True))
    draw.text((sheet_box[0] + 30, sheet_box[1] + 46), "Toronto Loft Node // 04-verify", fill=(80, 70, 60), font=get_font(16, serif=True))
    draw.line([(sheet_box[0] + 30, sheet_box[1] + 75), (sheet_box[2] - 30, sheet_box[1] + 75)], fill=(180, 170, 155), width=1)

    # QR Code placeholder grid (procedural matrix)
    qr_x, qr_y = sheet_box[0] + 35, sheet_box[1] + 95
    qr_size = 140
    draw.rectangle([qr_x, qr_y, qr_x + qr_size, qr_y + qr_size], fill=(245, 242, 235), outline=SUMI, width=2)
    # Corner finder patterns
    for cx, cy in [(qr_x + 8, qr_y + 8), (qr_x + qr_size - 38, qr_y + 8), (qr_x + 8, qr_y + qr_size - 38)]:
        draw.rectangle([cx, cy, cx + 30, cy + 30], fill=SUMI)
        draw.rectangle([cx + 6, cy + 6, cx + 24, cy + 24], fill=(245, 242, 235))
        draw.rectangle([cx + 10, cy + 10, cx + 20, cy + 20], fill=SUMI)
    # Pseudo QR data modules
    random.seed(99)
    for row in range(qr_y + 44, qr_y + qr_size - 10, 10):
        for col in range(qr_x + 44, qr_x + qr_size - 10, 10):
            if random.random() > 0.45:
                draw.rectangle([col, row, col + 7, row + 7], fill=SUMI)

    # Right side: Cryptographic Fingerprints & Passkey status
    fx = sheet_box[0] + 195
    fy = sheet_box[1] + 95
    draw.text((fx, fy), "PEER ID: toronto-mac-studio.local", fill=SUMI, font=get_font(12, mono=True))
    draw.text((fx, fy + 22), "FINGERPRINT (SHA-256):", fill=RUST, font=get_font(10, mono=True))
    draw.text((fx, fy + 40), "3F8A : B192 : E7C4 : 90DA", fill=SUMI, font=get_font(13, mono=True))
    draw.text((fx, fy + 58), "44E1 : 7720 : AD8C : EF31", fill=SUMI, font=get_font(13, mono=True))

    draw.rectangle([fx, fy + 88, sheet_box[2] - 30, fy + 124], fill=(230, 222, 206), outline=MOSS, width=1)
    draw.text((fx + 10, fy + 95), "PASSKEY STATUS: ENROLLED (Apple Secure Enclave)", fill=MOSS, font=get_font(10, mono=True))
    draw.text((fx + 10, fy + 110), "BIOMETRIC: Touch ID Verified @ 2026-11-12", fill=(60, 55, 48), font=get_font(9, mono=True))

    # Bottom of sheet: Action buttons / Status stamp
    draw.line([(sheet_box[0] + 30, sheet_box[3] - 70), (sheet_box[2] - 30, sheet_box[3] - 70)], fill=(180, 170, 155), width=1)
    draw.rectangle([sheet_box[0] + 35, sheet_box[3] - 55, sheet_box[0] + 220, sheet_box[3] - 20], fill=KAKI)
    draw.text((sheet_box[0] + 55, sheet_box[3] - 44), "TRUST ON FIRST USE", fill=WASHI, font=get_font(11, mono=True))

    draw_washi_stamp(draw, sheet_box[2] - 90, sheet_box[3] - 62, "信", "TRUST", RUST)

    draw_hud_header(draw, "03", "Toronto Loft TOFU Handshake", "Dusk Timber Loft // iOS Passkey & Ed25519 QR Sheet // Trust-On-First-Use")
    add_zen_paper_grain(img, 12)
    return img.convert("RGB")


# -------------------------------------------------------------
# Panel 4: "IV. Sealed NaCl Cryptographic Flight"
# -------------------------------------------------------------
def build_panel_04():
    img = Image.new("RGBA", (W_PANEL, H_PANEL), SUMI)
    draw = ImageDraw.Draw(img)

    # Cosmic / Relay transit dark Indigo Wash background
    relay_box = [40, 110, W_PANEL - 40, H_PANEL - 50]
    draw.rectangle(relay_box, fill=SUMI_SOFT, outline=(236, 230, 218, 40), width=1)

    # Blind relay node indicators on left and right
    # Left node (Sender Peer)
    draw.rectangle([70, 220, 200, 360], fill=(20, 18, 16), outline=MOSS, width=2)
    draw.text((85, 235), "ORIGIN PEER", fill=MOSS, font=get_font(11, mono=True))
    draw.text((85, 260), "tc:7f9a...e3b1", fill=WASHI, font=get_font(12, mono=True))
    draw.text((85, 285), "NaCl box.open", fill=(236, 230, 218, 140), font=get_font(10, mono=True))
    draw.text((85, 310), "Ephem PubKey OK", fill=(236, 230, 218, 140), font=get_font(10, mono=True))

    # Right node (Blind Relay Server)
    draw.rectangle([W_PANEL - 200, 220, W_PANEL - 70, 360], fill=(20, 18, 16), outline=INDIGO, width=2)
    draw.text((W_PANEL - 185, 235), "BLIND RELAY", fill=INDIGO, font=get_font(11, mono=True))
    draw.text((W_PANEL - 185, 260), "Zero-Knowledge", fill=WASHI, font=get_font(12, mono=True))
    draw.text((W_PANEL - 185, 285), "No Plaintext Stored", fill=(236, 230, 218, 140), font=get_font(10, mono=True))
    draw.text((W_PANEL - 185, 310), "Payload: 4,096 B", fill=(236, 230, 218, 140), font=get_font(10, mono=True))

    # Particle stream carrying sealed capsule
    stream_glow = Image.new("RGBA", (W_PANEL, H_PANEL), (0, 0, 0, 0))
    sg_draw = ImageDraw.Draw(stream_glow)
    sg_draw.line([(200, 290), (W_PANEL - 200, 290)], fill=(208, 112, 63, 100), width=18)
    sg_draw.line([(200, 290), (W_PANEL - 200, 290)], fill=(150, 70, 34, 180), width=6)
    stream_glow = stream_glow.filter(ImageFilter.GaussianBlur(14))
    img.paste(stream_glow, (0, 0), stream_glow)

    # Particle dots
    random.seed(123)
    for _ in range(120):
        px = random.randint(210, W_PANEL - 210)
        py = int(290 + random.gauss(0, 25))
        prad = random.choice([1, 2, 3])
        pcol = random.choice([KAKI, RUST, INDIGO, WASHI])
        draw.ellipse([px - prad, py - prad, px + prad, py + prad], fill=pcol)

    # Center: The Sealed NaCl Cryptographic Capsule (Envelope)
    cap_x0, cap_y0 = (W_PANEL // 2) - 120, 210
    cap_x1, cap_y1 = (W_PANEL // 2) + 120, 370
    draw.rectangle([cap_x0, cap_y0, cap_x1, cap_y1], fill=(28, 25, 20), outline=KAKI, width=2)
    # Flap diagonal lines of envelope
    draw.line([(cap_x0, cap_y0), (W_PANEL // 2, cap_y0 + 75)], fill=KAKI, width=2)
    draw.line([(cap_x1, cap_y0), (W_PANEL // 2, cap_y0 + 75)], fill=KAKI, width=2)

    # Inscription on capsule
    draw.text((cap_x0 + 20, cap_y0 + 85), "SEALED NaCl BOX (X25519)", fill=WASHI, font=get_font(11, mono=True))
    draw.text((cap_x0 + 20, cap_y0 + 105), "Nonce: 9f03...84c2 (24B)", fill=(236, 230, 218, 160), font=get_font(10, mono=True))
    draw.text((cap_x0 + 20, cap_y0 + 125), "Poly1305 MAC: Valid", fill=MOSS, font=get_font(10, mono=True))

    # Washi Stamp on Envelope
    draw_washi_stamp(draw, cap_x1 - 65, cap_y0 + 85, "封", "SEAL", RUST)

    # Bottom caption
    draw.text((W_PANEL // 2 - 210, 430), "END-TO-END ZERO-KNOWLEDGE BLIND RELAY TRANSIT", fill=WASHI, font=get_font(13, mono=True))

    draw_hud_header(draw, "04", "Sealed NaCl Cryptographic Flight", "Dirty-Gradient Stream // X25519 Sealed Envelope // Blind Relay Flight")
    add_zen_paper_grain(img, 10)
    return img.convert("RGB")


# -------------------------------------------------------------
# Panel 5: "V. Editorial AI Brain Arena Duel"
# -------------------------------------------------------------
def build_panel_05():
    img = Image.new("RGBA", (W_PANEL, H_PANEL), SUMI)
    draw = ImageDraw.Draw(img)

    # Arena arena container
    draw.rectangle([50, 110, W_PANEL - 50, H_PANEL - 50], fill=SUMI_SOFT, outline=(236, 230, 218, 40), width=1)

    # Split Sumi Cards: Model Alpha (Left) vs Model Beta (Right)
    card_w = 410
    card_h = 320
    card_y = 140

    # Model Alpha Card (Claude 3.5 Sonnet / Local SLM)
    card_a = [80, card_y, 80 + card_w, card_y + card_h]
    draw.rectangle(card_a, fill=(20, 18, 15), outline=KAKI, width=2)
    # Header tag
    draw.rectangle([80, card_y, 80 + card_w, card_y + 36], fill=(30, 25, 20))
    draw.text((95, card_y + 10), "MODEL ALPHA // CLAUDE-3.5-SONNET", fill=KAKI, font=get_font(12, mono=True))

    draw.text((95, card_y + 55), "Prompt Synthesis Output:", fill=(236, 230, 218, 140), font=get_font(10, mono=True))
    sample_text_a = (
        "> Decentralized IoT mesh synchronized.\n"
        "> CRDT state delta applied: 14 peers.\n"
        "> Zero-knowledge proof verified.\n"
        "> Autonomous consensus achieved in 88ms."
    )
    draw.text((95, card_y + 80), sample_text_a, fill=WASHI, font=get_font(12, mono=True), spacing=6)

    # Alpha Telemetry Metrics
    draw.line([(80, card_y + 190), (80 + card_w, card_y + 190)], fill=(236, 230, 218, 40), width=1)
    draw.text((95, card_y + 205), "TTFT (Time-To-First-Token):", fill=(236, 230, 218, 150), font=get_font(10, mono=True))
    draw.text((310, card_y + 203), "142 ms", fill=WASHI, font=get_font(12, mono=True))
    draw.text((95, card_y + 230), "Generation Speed:", fill=(236, 230, 218, 150), font=get_font(10, mono=True))
    draw.text((310, card_y + 228), "98.4 tok/s", fill=KAKI, font=get_font(12, mono=True))
    draw.text((95, card_y + 255), "OpenRouter Spend:", fill=(236, 230, 218, 150), font=get_font(10, mono=True))
    draw.text((310, card_y + 253), "$0.0034", fill=MOSS, font=get_font(12, mono=True))

    # Vote Stamp on Alpha (Winner)
    draw_washi_stamp(draw, 80 + card_w - 70, card_y + card_h - 65, "勝", "WINNER", KAKI)

    # Model Beta Card (Grok / Mistral)
    card_b = [W_PANEL - 80 - card_w, card_y, W_PANEL - 80, card_y + card_h]
    draw.rectangle(card_b, fill=(20, 18, 15), outline=(236, 230, 218, 80), width=1)
    # Header tag
    draw.rectangle([card_b[0], card_y, card_b[2], card_y + 36], fill=(24, 22, 19))
    draw.text((card_b[0] + 15, card_y + 10), "MODEL BETA // GROK-2-MINI", fill=(236, 230, 218, 180), font=get_font(12, mono=True))

    draw.text((card_b[0] + 15, card_y + 55), "Prompt Synthesis Output:", fill=(236, 230, 218, 140), font=get_font(10, mono=True))
    sample_text_b = (
        "> Network topology online and mapped.\n"
        "> State gossiped across 14 channels.\n"
        "> Verification signature complete.\n"
        "> Consensus resolved in 115ms."
    )
    draw.text((card_b[0] + 15, card_y + 80), sample_text_b, fill=(236, 230, 218, 200), font=get_font(12, mono=True), spacing=6)

    # Beta Telemetry Metrics
    draw.line([(card_b[0], card_y + 190), (card_b[2], card_y + 190)], fill=(236, 230, 218, 40), width=1)
    draw.text((card_b[0] + 15, card_y + 205), "TTFT (Time-To-First-Token):", fill=(236, 230, 218, 150), font=get_font(10, mono=True))
    draw.text((card_b[0] + 240, card_y + 203), "215 ms", fill=WASHI, font=get_font(12, mono=True))
    draw.text((card_b[0] + 15, card_y + 230), "Generation Speed:", fill=(236, 230, 218, 150), font=get_font(10, mono=True))
    draw.text((card_b[0] + 240, card_y + 228), "72.1 tok/s", fill=(236, 230, 218, 180), font=get_font(12, mono=True))
    draw.text((card_b[0] + 15, card_y + 255), "OpenRouter Spend:", fill=(236, 230, 218, 150), font=get_font(10, mono=True))
    draw.text((card_b[0] + 240, card_y + 253), "$0.0018", fill=MOSS, font=get_font(12, mono=True))

    # Center VS Badge
    vs_x, vs_y = W_PANEL // 2, card_y + (card_h // 2)
    draw.ellipse([vs_x - 24, vs_y - 24, vs_x + 24, vs_y + 24], fill=SUMI, outline=KAKI, width=2)
    draw.text((vs_x - 12, vs_y - 9), "VS", fill=KAKI, font=get_font(14, mono=True))

    draw_hud_header(draw, "05", "Editorial AI Brain Arena Duel", "Split Sumi Comparison Cards // TTFT & tok/s Telemetry // Kaki Win Stamp")
    add_zen_paper_grain(img, 10)
    return img.convert("RGB")


# -------------------------------------------------------------
# Panel 6: "VI. Ascension to L5 Mesh Sovereign"
# -------------------------------------------------------------
def build_panel_06():
    img = Image.new("RGBA", (W_PANEL, H_PANEL), SUMI)
    draw = ImageDraw.Draw(img)

    # Topology constellation background
    topo_box = [50, 110, W_PANEL - 50, H_PANEL - 50]
    draw.rectangle(topo_box, fill=SUMI_SOFT, outline=(236, 230, 218, 40), width=1)

    # Cooperative L1 -> L5 Mesh Topology Hierarchy
    tiers = [
        ("L1", "LOCAL DISCOVERY", MOSS, 180),
        ("L2", "PEER-TO-PEER DATA SYNC", INDIGO, 240),
        ("L3", "CRYPTOGRAPHIC TOFU MESH", UMBER, 300),
        ("L4", "AUTONOMOUS BRAIN ARENA", RUST, 360),
        ("L5", "SOVEREIGN FEDERATED SWARM", KAKI, 420),
    ]

    # Progression ladder on left
    for code, desc, tcol, ty in tiers:
        draw.rectangle([80, ty - 18, 120, ty + 18], fill=tcol)
        draw.text((90, ty - 8), code, fill=WASHI, font=get_font(13, mono=True))
        draw.rectangle([130, ty - 18, 380, ty + 18], fill=(22, 20, 16), outline=tcol, width=1)
        draw.text((145, ty - 6), desc, fill=WASHI, font=get_font(10, mono=True))

    # Connective ladder line
    draw.line([(100, 180), (100, 420)], fill=(236, 230, 218, 60), width=2)

    # Center-Right: Tri-Node Constellation (Car / iOS / Mac Desktop)
    nodes = [
        ("DESKTOP MESH", 520, 220, "Mac Studio M1", INDIGO),
        ("MOBILE NODE", 760, 200, "iPhone iOS Passkey", KAKI),
        ("CABIN NODE", 640, 380, "Vehicle Dynamic Audio", MOSS),
    ]

    # Inter-node lines
    draw.line([(520, 220), (760, 200)], fill=KAKI, width=2)
    draw.line([(760, 200), (640, 380)], fill=MOSS, width=2)
    draw.line([(640, 380), (520, 220)], fill=INDIGO, width=2)

    # Node badges
    for name, nx, ny, sub, ncol in nodes:
        # Glow
        nglow = Image.new("RGBA", (W_PANEL, H_PANEL), (0, 0, 0, 0))
        ng_draw = ImageDraw.Draw(nglow)
        ng_draw.ellipse([nx - 45, ny - 45, nx + 45, ny + 45], fill=(*ncol, 40))
        nglow = nglow.filter(ImageFilter.GaussianBlur(10))
        img.paste(nglow, (0, 0), nglow)

        draw.ellipse([nx - 36, ny - 36, nx + 36, ny + 36], fill=(24, 21, 17), outline=ncol, width=2)
        draw.ellipse([nx - 8, ny - 8, nx + 8, ny + 8], fill=ncol)
        draw.text((nx - 45, ny + 44), name, fill=WASHI, font=get_font(10, mono=True))
        draw.text((nx - 55, ny + 60), sub, fill=(236, 230, 218, 150), font=get_font(9, mono=True))

    # Center of constellation: Sovereign Core
    core_x, core_y = (520 + 760 + 640) // 3, (220 + 200 + 380) // 3
    draw.ellipse([core_x - 14, core_y - 14, core_x + 14, core_y + 14], fill=KAKI)
    draw.text((core_x - 4, core_y - 7), "Ω", fill=WASHI, font=get_font(12, mono=True))

    # Master Washi stamp: 昇天 (Ascension)
    draw_washi_stamp(draw, W_PANEL - 130, 130, "昇", "ASCENT", KAKI)
    draw_washi_stamp(draw, W_PANEL - 130, 195, "天", "SOV", KAKI)

    draw_hud_header(draw, "06", "Ascension to L5 Mesh Sovereign", "Cooperative L1->L5 Topology // Unified Car/iOS/Desktop Nodes // 昇天 Seal")
    add_zen_paper_grain(img, 12)
    return img.convert("RGB")


# -------------------------------------------------------------
# Contact Sheet (3x2 Master Grid)
# -------------------------------------------------------------
def build_contact_sheet(panel_images):
    # 3 columns, 2 rows
    # Each panel scaled or rendered at 1024x576, or composed into master canvas
    margin = 40
    gap = 24
    cols, rows = 3, 2
    cell_w, cell_h = 640, 360
    total_w = (margin * 2) + (cols * cell_w) + ((cols - 1) * gap)
    total_h = (margin * 2) + 90 + (rows * cell_h) + ((rows - 1) * gap)

    master = Image.new("RGBA", (total_w, total_h), SUMI)
    draw = ImageDraw.Draw(master)

    # Master header
    draw.rectangle([margin, margin, total_w - margin, margin + 70], fill=SUMI_SOFT, outline=KAKI, width=1)
    draw.text((margin + 24, margin + 14), "TINCAN 2.2 // MASTER STORYBOARD CONTACT SHEET", fill=WASHI, font=get_font(22, serif=True))
    draw.text((margin + 24, margin + 44), "6-Scene Narrative Audio Drama // Zen Ink-and-Paper & Dirty-Gradient Aesthetic // 3×2 Grid", fill=(236, 230, 218, 160), font=get_font(12, mono=True))
    draw_washi_stamp(draw, total_w - margin - 80, margin + 8, "全", "ALL 6", KAKI)

    for idx, pimg in enumerate(panel_images):
        col = idx % cols
        row = idx // cols
        x = margin + col * (cell_w + gap)
        y = margin + 90 + row * (cell_h + gap)

        # Resize panel to cell
        thumb = pimg.resize((cell_w, cell_h), Image.Resampling.LANCZOS)
        master.paste(thumb, (x, y))
        draw.rectangle([x, y, x + cell_w, y + cell_h], outline=(236, 230, 218, 80), width=1)

        # Label tag
        act_titles = [
            "ACT I: The Ink-and-Paper Sanctuary",
            "ACT II: Kokoro-82M Neural Whisper",
            "ACT III: Toronto Loft TOFU Handshake",
            "ACT IV: Sealed NaCl Cryptographic Flight",
            "ACT V: Editorial AI Brain Arena Duel",
            "ACT VI: Ascension to L5 Mesh Sovereign",
        ]
        draw.rectangle([x, y + cell_h - 28, x + cell_w, y + cell_h], fill=(14, 13, 11, 210))
        draw.text((x + 10, y + cell_h - 22), act_titles[idx], fill=WASHI, font=get_font(11, mono=True))

    add_zen_paper_grain(master, 8)
    return master.convert("RGB")


def build_contact_sheet_svg():
    # Standalone high-fidelity SVG contact sheet
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="100%" height="100%">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@500;600&amp;family=Zen+Kaku+Gothic+New:wght@400;500&amp;display=swap');
      .title {{ font-family: 'Shippori Mincho', serif; font-size: 28px; font-weight: 600; fill: #ece6da; }}
      .sub {{ font-family: 'Zen Kaku Gothic New', monospace, sans-serif; font-size: 13px; fill: rgba(236, 230, 218, 0.7); }}
      .card-title {{ font-family: 'Shippori Mincho', serif; font-size: 16px; font-weight: 500; fill: #ece6da; }}
      .card-meta {{ font-family: 'Zen Kaku Gothic New', monospace, sans-serif; font-size: 11px; fill: #d0703f; }}
      .stamp-kanji {{ font-family: 'Shippori Mincho', serif; font-size: 22px; fill: #d0703f; font-weight: 600; }}
      .stamp-sub {{ font-family: 'Zen Kaku Gothic New', monospace; font-size: 8px; fill: #d0703f; letter-spacing: 1px; }}
    </style>
    <filter id="noise">
      <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="3" result="turb" />
      <feColorMatrix type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 0.06 0" />
      <feComposite in2="SourceGraphic" in="gl" operator="in" />
    </filter>
  </defs>

  <!-- Background Sumi -->
  <rect width="1920" height="1080" fill="#0e0d0b" />
  <rect width="1920" height="1080" fill="#17150f" opacity="0.6" filter="url(#noise)" />

  <!-- Master Header -->
  <rect x="50" y="40" width="1820" height="70" rx="8" fill="#17150f" stroke="#d0703f" stroke-width="1.5" />
  <text x="80" y="75" class="title">TINCAN 2.2 // MASTER STORYBOARD CONTACT SHEET</text>
  <text x="80" y="96" class="sub">6-Scene Narrative Audio Drama // Zen Ink-and-Paper &amp; Dirty-Gradient Aesthetic // 3×2 Matrix</text>

  <!-- Header Hanko Seal -->
  <rect x="1790" y="48" width="54" height="54" rx="4" fill="none" stroke="#d0703f" stroke-width="2" />
  <text x="1805" y="78" class="stamp-kanji">全</text>
  <text x="1800" y="94" class="stamp-sub">ALL 6</text>

  <!-- Grid Panels (3 cols x 2 rows) -->
  <!-- Col 1: 50 + 0 * 593 = 50 | Col 2: 50 + 613 = 663 | Col 3: 50 + 1226 = 1276 -->
  <!-- Row 1: y=140, h=420 | Row 2: y=590, h=420 -->

  <!-- Panel 1 -->
  <g transform="translate(50, 140)">
    <rect width="580" height="420" rx="10" fill="#17150f" stroke="#42522e" stroke-width="1.5" />
    <image href="panel_01_cyber_lab_crt.png" x="10" y="10" width="560" height="315" preserveAspectRatio="xMidYMid slice" rx="6" />
    <rect x="10" y="335" width="560" height="75" rx="6" fill="#0e0d0b" />
    <text x="24" y="360" class="card-title">ACT I: The Ink-and-Paper Sanctuary</text>
    <text x="24" y="382" class="card-meta">Tatami &amp; Wood Desk // $ tincan whoami // tc:7f9a...e3b1 // 29.79s</text>
    <rect x="500" y="345" width="50" height="50" rx="4" fill="none" stroke="#d0703f" stroke-width="1.5" />
    <text x="515" y="373" class="stamp-kanji">寂</text>
    <text x="510" y="388" class="stamp-sub">SUMI</text>
  </g>

  <!-- Panel 2 -->
  <g transform="translate(670, 140)">
    <rect width="580" height="420" rx="10" fill="#17150f" stroke="#d0703f" stroke-width="1.5" />
    <image href="panel_02_kokoro_voice_alert.png" x="10" y="10" width="560" height="315" preserveAspectRatio="xMidYMid slice" rx="6" />
    <rect x="10" y="335" width="560" height="75" rx="6" fill="#0e0d0b" />
    <text x="24" y="360" class="card-title">ACT II: Kokoro-82M Neural Whisper</text>
    <text x="24" y="382" class="card-meta">24kHz Acoustic Waveform // Persimmon Pulse // Zero-Account TTS // 26.50s</text>
    <rect x="500" y="345" width="50" height="50" rx="4" fill="none" stroke="#d0703f" stroke-width="1.5" />
    <text x="515" y="373" class="stamp-kanji">声</text>
    <text x="508" y="388" class="stamp-sub">VOICE</text>
  </g>

  <!-- Panel 3 -->
  <g transform="translate(1290, 140)">
    <rect width="580" height="420" rx="10" fill="#17150f" stroke="#964622" stroke-width="1.5" />
    <image href="panel_03_toronto_loft_tofu.png" x="10" y="10" width="560" height="315" preserveAspectRatio="xMidYMid slice" rx="6" />
    <rect x="10" y="335" width="560" height="75" rx="6" fill="#0e0d0b" />
    <text x="24" y="360" class="card-title">ACT III: Toronto Loft TOFU Handshake</text>
    <text x="24" y="382" class="card-meta">Dusk Loft // iOS Passkey &amp; Ed25519 QR Sheet // 04-verify // 24.62s</text>
    <rect x="500" y="345" width="50" height="50" rx="4" fill="none" stroke="#964622" stroke-width="1.5" />
    <text x="515" y="373" class="stamp-kanji" fill="#964622">信</text>
    <text x="508" y="388" class="stamp-sub" fill="#964622">TRUST</text>
  </g>

  <!-- Panel 4 -->
  <g transform="translate(50, 590)">
    <rect width="580" height="420" rx="10" fill="#17150f" stroke="#2e365c" stroke-width="1.5" />
    <image href="panel_04_webrtc_capsule_flight.png" x="10" y="10" width="560" height="315" preserveAspectRatio="xMidYMid slice" rx="6" />
    <rect x="10" y="335" width="560" height="75" rx="6" fill="#0e0d0b" />
    <text x="24" y="360" class="card-title">ACT IV: Sealed NaCl Cryptographic Flight</text>
    <text x="24" y="382" class="card-meta">Dirty-Gradient Stream // X25519 Sealed Envelope // Blind Relay // 30.83s</text>
    <rect x="500" y="345" width="50" height="50" rx="4" fill="none" stroke="#2e365c" stroke-width="1.5" />
    <text x="515" y="373" class="stamp-kanji" fill="#ece6da">封</text>
    <text x="510" y="388" class="stamp-sub" fill="#ece6da">SEAL</text>
  </g>

  <!-- Panel 5 -->
  <g transform="translate(670, 590)">
    <rect width="580" height="420" rx="10" fill="#17150f" stroke="#705436" stroke-width="1.5" />
    <image href="panel_05_ai_brain_arena.png" x="10" y="10" width="560" height="315" preserveAspectRatio="xMidYMid slice" rx="6" />
    <rect x="10" y="335" width="560" height="75" rx="6" fill="#0e0d0b" />
    <text x="24" y="360" class="card-title">ACT V: Editorial AI Brain Arena Duel</text>
    <text x="24" y="382" class="card-meta">Split Sumi Cards // TTFT &amp; tok/s Telemetry // Kaki Win Stamp // 29.21s</text>
    <rect x="500" y="345" width="50" height="50" rx="4" fill="none" stroke="#d0703f" stroke-width="1.5" />
    <text x="515" y="373" class="stamp-kanji">勝</text>
    <text x="508" y="388" class="stamp-sub">WIN</text>
  </g>

  <!-- Panel 6 -->
  <g transform="translate(1290, 590)">
    <rect width="580" height="420" rx="10" fill="#17150f" stroke="#d0703f" stroke-width="1.5" />
    <image href="panel_06_tier_l5_messiah_gold.png" x="10" y="10" width="560" height="315" preserveAspectRatio="xMidYMid slice" rx="6" />
    <rect x="10" y="335" width="560" height="75" rx="6" fill="#0e0d0b" />
    <text x="24" y="360" class="card-title">ACT VI: Ascension to L5 Mesh Sovereign</text>
    <text x="24" y="382" class="card-meta">L1→L5 Cooperative Mesh // Car/iOS/Desktop Constellation // 32.21s</text>
    <rect x="500" y="345" width="50" height="50" rx="4" fill="none" stroke="#d0703f" stroke-width="1.5" />
    <text x="515" y="373" class="stamp-kanji">昇</text>
    <text x="508" y="388" class="stamp-sub">SOV</text>
  </g>
</svg>
"""
    return svg


# -------------------------------------------------------------
# Interactive HTML Storyboard Viewer & Drama Player
# -------------------------------------------------------------
def build_storyboard_viewer_html(manifest_data):
    scenes_json = json.dumps(manifest_data["scenes"], indent=2)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TinCan 2.2 // Zen Storyboard &amp; Narrative Audio Drama</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@500;600&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --sumi: #0e0d0b;
      --sumi-soft: #17150f;
      --washi: #ece6da;
      --washi-dim: rgba(236, 230, 218, 0.65);
      --washi-hairline: rgba(236, 230, 218, 0.15);
      --kaki: #d0703f;
      --rust: #964622;
      --moss: #42522e;
      --indigo: #2e365c;
      --umber: #705436;
      --font-serif: "Shippori Mincho", "Hiragino Mincho ProN", serif;
      --font-sans: "Zen Kaku Gothic New", system-ui, sans-serif;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      background: var(--sumi);
      color: var(--washi);
      font-family: var(--font-sans);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow-x: hidden;
    }}
    header {{
      background: var(--sumi-soft);
      border-bottom: 1px solid var(--washi-hairline);
      padding: 1.25rem 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: sticky;
      top: 0;
      z-index: 100;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 1rem;
    }}
    .hanko {{
      border: 1.5px solid var(--kaki);
      color: var(--kaki);
      font-family: var(--font-serif);
      width: 38px;
      height: 38px;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.2rem;
      font-weight: 600;
    }}
    .title-group h1 {{
      font-family: var(--font-serif);
      font-size: 1.3rem;
      font-weight: 600;
      letter-spacing: 0.02em;
    }}
    .title-group p {{
      font-size: 0.78rem;
      color: var(--washi-dim);
      letter-spacing: 0.04em;
    }}
    .transport-bar {{
      display: flex;
      align-items: center;
      gap: 1.25rem;
    }}
    .btn {{
      background: transparent;
      border: 1px solid var(--washi-hairline);
      color: var(--washi);
      padding: 0.5rem 1.1rem;
      border-radius: 4px;
      font-family: var(--font-sans);
      font-size: 0.85rem;
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .btn:hover {{
      border-color: var(--kaki);
      color: var(--kaki);
    }}
    .btn-primary {{
      background: var(--kaki);
      border-color: var(--kaki);
      color: var(--sumi);
      font-weight: 700;
    }}
    .btn-primary:hover {{
      background: #e28150;
      color: var(--sumi);
    }}
    .timeline-container {{
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      min-width: 280px;
    }}
    .timeline-track {{
      background: rgba(236, 230, 218, 0.12);
      height: 6px;
      border-radius: 3px;
      position: relative;
      cursor: pointer;
    }}
    .timeline-progress {{
      background: var(--kaki);
      height: 100%;
      border-radius: 3px;
      width: 0%;
      transition: width 0.1s linear;
    }}
    .time-digits {{
      display: flex;
      justify-content: space-between;
      font-size: 0.72rem;
      font-family: monospace;
      color: var(--washi-dim);
    }}

    main {{
      max-width: 1400px;
      width: 100%;
      margin: 0 auto;
      padding: 2rem;
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 2rem;
    }}

    @media (max-width: 1024px) {{
      main {{
        grid-template-columns: 1fr;
      }}
    }}

    .stage-card {{
      background: var(--sumi-soft);
      border: 1px solid var(--washi-hairline);
      border-radius: 8px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }}
    .stage-viewport {{
      position: relative;
      aspect-ratio: 16 / 9;
      background: #000;
      width: 100%;
      overflow: hidden;
    }}
    .stage-viewport img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
      transition: opacity 0.3s ease;
    }}
    .stage-overlay {{
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      background: linear-gradient(transparent, rgba(14, 13, 11, 0.95));
      padding: 1.5rem;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
    }}
    .stage-title {{
      font-family: var(--font-serif);
      font-size: 1.5rem;
      font-weight: 600;
      margin-bottom: 0.25rem;
    }}
    .stage-cpl {{
      font-size: 0.85rem;
      color: var(--washi-dim);
      font-family: monospace;
      max-width: 600px;
      line-height: 1.4;
    }}

    .playlist-card {{
      background: var(--sumi-soft);
      border: 1px solid var(--washi-hairline);
      border-radius: 8px;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }}
    .playlist-card h2 {{
      font-family: var(--font-serif);
      font-size: 1.15rem;
      font-weight: 500;
      border-bottom: 1px solid var(--washi-hairline);
      padding-bottom: 0.5rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .scene-list {{
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }}
    .scene-item {{
      background: rgba(236, 230, 218, 0.03);
      border: 1px solid var(--washi-hairline);
      border-radius: 6px;
      padding: 0.75rem 1rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 1rem;
      transition: all 0.15s ease;
    }}
    .scene-item:hover {{
      background: rgba(236, 230, 218, 0.08);
      border-color: rgba(208, 112, 63, 0.5);
    }}
    .scene-item.active {{
      background: rgba(208, 112, 63, 0.12);
      border-color: var(--kaki);
    }}
    .scene-num {{
      font-family: monospace;
      color: var(--kaki);
      font-size: 0.8rem;
      font-weight: 700;
      min-width: 24px;
    }}
    .scene-info {{
      flex: 1;
    }}
    .scene-info h3 {{
      font-family: var(--font-serif);
      font-size: 0.95rem;
      font-weight: 500;
    }}
    .scene-info p {{
      font-size: 0.75rem;
      color: var(--washi-dim);
      font-family: monospace;
    }}
    .scene-timing {{
      font-family: monospace;
      font-size: 0.75rem;
      color: var(--washi-dim);
    }}

    .sheet-section {{
      max-width: 1400px;
      width: 100%;
      margin: 0 auto 3rem auto;
      padding: 0 2rem;
    }}
    .sheet-card {{
      background: var(--sumi-soft);
      border: 1px solid var(--washi-hairline);
      border-radius: 8px;
      padding: 1.5rem;
    }}
    .sheet-card h2 {{
      font-family: var(--font-serif);
      font-size: 1.15rem;
      margin-bottom: 1rem;
      color: var(--washi);
    }}
    .sheet-card img {{
      width: 100%;
      border-radius: 4px;
      border: 1px solid var(--washi-hairline);
    }}
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <div class="hanko">禅</div>
      <div class="title-group">
        <h1>TinCan 2.2 // Zen Storyboard &amp; Narrative Drama</h1>
        <p>Sumi / Washi / Kaki Aesthetic // 6-Act Decentralized Audio Drama</p>
      </div>
    </div>
    <div class="transport-bar">
      <button class="btn btn-primary" id="playBtn" onclick="togglePlay()">PLAY MASTER VO</button>
      <div class="timeline-container">
        <div class="timeline-track" id="timelineTrack" onclick="seek(event)">
          <div class="timeline-progress" id="timelineProgress"></div>
        </div>
        <div class="time-digits">
          <span id="currentTime">00:00</span>
          <span id="durationTime">02:53</span>
        </div>
      </div>
    </div>
  </header>

  <main>
    <div class="stage-card">
      <div class="stage-viewport">
        <img id="activeStageImg" src="panel_01_zen_sanctuary.png" alt="Active Scene">
        <div class="stage-overlay">
          <div>
            <div class="stage-title" id="stageTitle">I. The Ink-and-Paper Sanctuary</div>
            <div class="stage-cpl" id="stageCpl">CPL: Wide interior dusk. Minimalist tatami and cedar desk. 9:16 vertical video feed glow. Ed25519 identity seal.</div>
          </div>
          <div class="hanko" id="stageHanko">寂</div>
        </div>
      </div>
      <div style="padding: 1.25rem 1.5rem; border-top: 1px solid var(--washi-hairline); display: flex; justify-content: space-between; align-items: center;">
        <span style="font-size: 0.82rem; font-family: monospace; color: var(--washi-dim);">SCENE AUDIO: <strong id="sceneAudioLabel" style="color: var(--washi);">panel_01_cyber_lab_crt_drama.wav</strong></span>
        <button class="btn" onclick="playSceneSolo()">PLAY SCENE AUDIO</button>
      </div>
    </div>

    <div class="playlist-card">
      <h2>
        <span>Narrative Scenes</span>
        <span style="font-size: 0.8rem; font-family: monospace; color: var(--kaki);">6 ACTS</span>
      </h2>
      <ul class="scene-list" id="sceneList"></ul>
    </div>
  </main>

  <section class="sheet-section">
    <div class="sheet-card">
      <h2>3×2 Master Storyboard Contact Sheet</h2>
      <img src="zen_storyboard_contact_sheet.png" alt="Zen Storyboard Master Contact Sheet">
    </div>
  </section>

  <audio id="masterAudio" src="trailer_voiceover.wav" preload="auto"></audio>
  <audio id="sceneAudio" preload="auto"></audio>

  <script>
    const scenes = {scenes_json};
    let activeIndex = 0;
    const masterAudio = document.getElementById("masterAudio");
    const sceneAudio = document.getElementById("sceneAudio");
    const playBtn = document.getElementById("playBtn");
    const progress = document.getElementById("timelineProgress");
    const currentTimeEl = document.getElementById("currentTime");
    const durationTimeEl = document.getElementById("durationTime");

    function renderScenes() {{
      const list = document.getElementById("sceneList");
      list.innerHTML = "";
      scenes.forEach((s, idx) => {{
        const li = document.createElement("li");
        li.className = "scene-item" + (idx === activeIndex ? " active" : "");
        li.onclick = () => selectScene(idx);
        li.innerHTML = `
          <div class="scene-num">0${{idx + 1}}</div>
          <div class="scene-info">
            <h3>${{s.title}}</h3>
            <p>${{s.zen_id}}</p>
          </div>
          <div class="scene-timing">${{s.duration_sec.toFixed(1)}}s</div>
        `;
        list.appendChild(li);
      }});
    }}

    function selectScene(idx) {{
      activeIndex = idx;
      const s = scenes[idx];
      document.getElementById("activeStageImg").src = s.zen_panel_path.split("/").pop();
      document.getElementById("stageTitle").innerText = s.title;
      document.getElementById("stageCpl").innerText = "CPL: " + (s.cpl_prompt || "");
      document.getElementById("sceneAudioLabel").innerText = s.audio_path.split("/").pop();
      sceneAudio.src = s.audio_path.split("/").pop();

      const kanjis = ["寂", "声", "信", "封", "勝", "昇"];
      document.getElementById("stageHanko").innerText = kanjis[idx] || "禅";

      renderScenes();
    }}

    function togglePlay() {{
      if (masterAudio.paused) {{
        masterAudio.play();
        playBtn.innerText = "PAUSE MASTER VO";
      }} else {{
        masterAudio.pause();
        playBtn.innerText = "PLAY MASTER VO";
      }}
    }}

    function playSceneSolo() {{
      masterAudio.pause();
      playBtn.innerText = "PLAY MASTER VO";
      sceneAudio.currentTime = 0;
      sceneAudio.play();
    }}

    masterAudio.ontimeupdate = () => {{
      const t = masterAudio.currentTime;
      const d = masterAudio.duration || 173.167;
      progress.style.width = ((t / d) * 100) + "%";
      currentTimeEl.innerText = formatTime(t);
      durationTimeEl.innerText = formatTime(d);

      // Auto update active scene based on start_sec
      for (let i = scenes.length - 1; i >= 0; i--) {{
        if (t >= scenes[i].start_sec) {{
          if (activeIndex !== i) {{
            selectScene(i);
          }}
          break;
        }}
      }}
    }};

    function seek(e) {{
      const rect = e.currentTarget.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const ratio = clickX / rect.width;
      const d = masterAudio.duration || 173.167;
      masterAudio.currentTime = ratio * d;
    }}

    function formatTime(secs) {{
      const m = Math.floor(secs / 60);
      const s = Math.floor(secs % 60);
      return (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
    }}

    selectScene(0);
  </script>
</body>
</html>
"""
    return html


# -------------------------------------------------------------
# Main Orchestrator
# -------------------------------------------------------------
def main():
    print(">>> [1/5] Reading audio_drama_manifest.json...")
    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    # Zen scene definitions
    zen_scenes_meta = [
        {
            "zen_id": "panel_01_zen_sanctuary",
            "title": "I. The Ink-and-Paper Sanctuary",
            "legacy_id": "panel_01_cyber_lab_crt",
            "palette": ["#0e0d0b", "#17150f", "#ece6da", "#d0703f", "#42522e", "#705436"],
            "cpl_prompt": "Minimalist tatami and cedar wood desk; warm ambient glow of a 9:16 vertical video feed; terminal session displaying $ tincan whoami -> tc:7f9a...e3b1; washi paper texture; editorial Sumi framing.",
            "builder": build_panel_01,
            "filenames": ["panel_01_cyber_lab_crt.png", "panel_01_zen_sanctuary.png"]
        },
        {
            "zen_id": "panel_02_kokoro_whisper",
            "title": "II. Kokoro-82M Neural Whisper",
            "legacy_id": "panel_02_kokoro_voice_alert",
            "palette": ["#0e0d0b", "#17150f", "#ece6da", "#d0703f", "#964622", "#42522e"],
            "cpl_prompt": "Persimmon 24kHz acoustic waveform pulse across Sumi background; traditional Washi voice seal (声); zero-account local neural speech synthesis telemetry; raw PCM streams.",
            "builder": build_panel_02,
            "filenames": ["panel_02_kokoro_voice_alert.png", "panel_02_kokoro_whisper.png"]
        },
        {
            "zen_id": "panel_03_toronto_loft_tofu",
            "title": "III. Toronto Loft TOFU Handshake",
            "legacy_id": "panel_03_toronto_loft_tofu",
            "palette": ["#0e0d0b", "#17150f", "#ece6da", "#d0703f", "#964622", "#705436"],
            "cpl_prompt": "Dusk concrete and timber loft architecture; physical Washi verification sheet (04-verify); procedural Ed25519 QR matrix; Apple Secure Enclave Passkey enrollment; Trust-On-First-Use seal.",
            "builder": build_panel_03,
            "filenames": ["panel_03_toronto_loft_tofu.png"]
        },
        {
            "zen_id": "panel_04_webrtc_capsule_flight",
            "title": "IV. Sealed NaCl Cryptographic Flight",
            "legacy_id": "panel_04_webrtc_capsule_flight",
            "palette": ["#0e0d0b", "#17150f", "#ece6da", "#d0703f", "#964622", "#2e365c"],
            "cpl_prompt": "Dirty-gradient particle flight path over Indigo Wash; X25519 sealed envelope capsule crossing zero-knowledge blind relay; Poly1305 MAC tag and 24-byte nonce verification; sealed inkan stamp (封).",
            "builder": build_panel_04,
            "filenames": ["panel_04_webrtc_capsule_flight.png"]
        },
        {
            "zen_id": "panel_05_ai_brain_arena",
            "title": "V. Editorial AI Brain Arena Duel",
            "legacy_id": "panel_05_ai_brain_arena",
            "palette": ["#0e0d0b", "#17150f", "#ece6da", "#d0703f", "#42522e", "#705436"],
            "cpl_prompt": "Split Sumi comparison cards; Model Alpha vs Model Beta prompt outputs; live TTFT and tok/s telemetry; OpenRouter spend metering; Kaki winner inkan seal (勝).",
            "builder": build_panel_05,
            "filenames": ["panel_05_ai_brain_arena.png"]
        },
        {
            "zen_id": "panel_06_l5_mesh_sovereign",
            "title": "VI. Ascension to L5 Mesh Sovereign",
            "legacy_id": "panel_06_tier_l5_messiah_gold",
            "palette": ["#0e0d0b", "#17150f", "#ece6da", "#d0703f", "#2e365c", "#42522e"],
            "cpl_prompt": "Cooperative L1 through L5 mesh progression ladder; Car cabin audio, iOS mobile, and Mac desktop unified sovereign nodes; double Washi inkan stamp 昇天 (Ascension).",
            "builder": build_panel_06,
            "filenames": ["panel_06_tier_l5_messiah_gold.png", "panel_06_l5_mesh_sovereign.png"]
        },
    ]

    print(">>> [2/5] Rendering 6 Zen Storyboard panels...")
    rendered_panels = []
    for idx, zmeta in enumerate(zen_scenes_meta):
        print(f"  Rendering Scene {idx + 1}: {zmeta['title']}...")
        pimg = zmeta["builder"]()
        rendered_panels.append(pimg)
        for fname in zmeta["filenames"]:
            out_path = os.path.join(PANELS_DIR, fname)
            pimg.save(out_path, format="PNG")
            print(f"    Saved: {out_path} ({pimg.size})")

    print(">>> [3/5] Building 3x2 Master Contact Sheet (PNG & SVG)...")
    contact_sheet_img = build_contact_sheet(rendered_panels)
    contact_png_path = os.path.join(PANELS_DIR, "zen_storyboard_contact_sheet.png")
    contact_sheet_img.save(contact_png_path, format="PNG")
    print(f"  Saved Contact Sheet PNG: {contact_png_path} ({contact_sheet_img.size})")

    contact_svg_content = build_contact_sheet_svg()
    contact_svg_path = os.path.join(PANELS_DIR, "zen_storyboard_contact_sheet.svg")
    with open(contact_svg_path, "w", encoding="utf-8") as f:
        f.write(contact_svg_content)
    print(f"  Saved Contact Sheet SVG: {contact_svg_path}")

    print(">>> [4/5] Updating audio_drama_manifest.json with Zen metadata...")
    manifest["design_system"] = "TinCan 2.2 Zen (Sumi / Washi / Kaki)"
    manifest["contact_sheet"] = os.path.join(PANELS_DIR, "zen_storyboard_contact_sheet.png")
    manifest["contact_sheet_svg"] = os.path.join(PANELS_DIR, "zen_storyboard_contact_sheet.svg")
    manifest["viewer"] = os.path.join(PANELS_DIR, "storyboard_viewer.html")

    for i, s in enumerate(manifest["scenes"]):
        zmeta = zen_scenes_meta[i]
        s["zen_id"] = zmeta["zen_id"]
        s["title"] = zmeta["title"]
        s["zen_panel_path"] = os.path.join(PANELS_DIR, zmeta["filenames"][-1])
        s["palette"] = zmeta["palette"]
        s["cpl_prompt"] = zmeta["cpl_prompt"]

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("  Manifest updated successfully.")

    print(">>> [5/5] Building interactive HTML Storyboard Viewer...")
    viewer_html = build_storyboard_viewer_html(manifest)
    viewer_path = os.path.join(PANELS_DIR, "storyboard_viewer.html")
    with open(viewer_path, "w", encoding="utf-8") as f:
        f.write(viewer_html)
    print(f"  Saved Storyboard Viewer: {viewer_path}")
    print(">>> Done!")


if __name__ == "__main__":
    main()
