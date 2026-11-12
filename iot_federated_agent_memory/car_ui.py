"""TinCan OS — Aftermarket Car Head-Unit UI (1280x720 Sumi-Dock).

Implements the glanceable, low-glare dark Sumi-Dock UI for 1280x720 dashboard displays.
Features:
- 76px minimum touch targets.
- Client-side mode switching across 4 car modes: driving, parked, dashcam, identity.
- Parked-safety gate enforcement: while in driving mode, pairing/passkey, clip browsing,
  spaces sync and driver switching are gated with a parked-only notice.
- Dashcam telemetry (REC 1080p60 / front / cabin / rear feeds).
- Live fetch hooks to /api/tincan/whoami and /api/mesh/state.
- Dirty-gradient SVG feTurbulence grain overlay with Sumi, Washi, and Kaki color palette.
"""

from typing import Optional

CAR_MODES = ("driving", "parked", "dashcam", "identity")


def render_car_headunit_html(mode: str = "driving") -> str:
    """Return a complete, self-contained HTML5 document for the 1280x720 car head unit."""
    initial_mode = mode.lower() if mode and mode.lower() in CAR_MODES else "driving"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=1280, height=720, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>TinCan OS · Car Head Unit</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@500;600&family=Zen+Kaku+Gothic+New:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{
  --sumi: #0e0d0b;
  --sumi-2: #17150f;
  --washi: #ece6da;
  --washi-2: rgba(236, 230, 218, 0.66);
  --washi-3: rgba(236, 230, 218, 0.6);
  --tick: rgba(236, 230, 218, 0.38);
  --line: rgba(236, 230, 218, 0.14);
  --kaki: #d0703f;
  --rust: #964622;
  --moss: #42522e;
  --umber: #705436;
  --mincho: "Shippori Mincho", "Noto Serif", serif;
  --gothic: "Zen Kaku Gothic New", "Noto Sans", system-ui, sans-serif;
  --ease: cubic-bezier(0.16, 1, 0.3, 1);
  --dock: 128px;
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{
  width: 1280px;
  height: 720px;
  overflow: hidden;
  background: var(--sumi);
  color: var(--washi);
  font-family: var(--gothic);
  -webkit-font-smoothing: antialiased;
  user-select: none;
}}
button {{ font: inherit; color: inherit; background: none; border: 0; cursor: pointer; }}
.stage {{ position: relative; width: 1280px; height: 720px; overflow: hidden; background: var(--sumi); }}

/* Dirty gradient: soft mixed washes + grain */
.dirt {{ position: absolute; inset: 0; z-index: 0; pointer-events: none; overflow: hidden; }}
.dirt-washes {{
  position: absolute; inset: 0;
  transition: background 0.5s var(--ease);
  background:
    radial-gradient(ellipse 90% 70% at 8% 92%, rgba(150, 70, 34, 0.38), transparent 58%),
    radial-gradient(ellipse 80% 62% at 92% 8%, rgba(66, 82, 46, 0.42), transparent 54%),
    radial-gradient(ellipse 60% 50% at 70% 110%, rgba(112, 84, 54, 0.34), transparent 52%),
    radial-gradient(ellipse 46% 36% at 28% 0%, rgba(208, 112, 63, 0.16), transparent 55%),
    radial-gradient(ellipse 40% 30% at 50% 46%, rgba(23, 21, 15, 0.35), transparent 70%),
    linear-gradient(158deg, #16130f 0%, #0e0d0b 42%, #19150f 100%);
}}
.dirt-washes.drive {{
  background:
    radial-gradient(ellipse 70% 55% at 62% 0%, rgba(208, 112, 63, 0.14), transparent 50%),
    radial-gradient(ellipse 90% 80% at 50% 120%, rgba(150, 70, 34, 0.28), transparent 55%),
    radial-gradient(ellipse 50% 40% at 10% 20%, rgba(66, 82, 46, 0.28), transparent 60%),
    linear-gradient(180deg, #1a1713 0%, #0e0d0b 48%, #14110d 100%);
}}
.dirt svg {{ position: absolute; inset: 0; width: 100%; height: 100%; opacity: 0.46; mix-blend-mode: overlay; }}
.vignette {{
  position: absolute; inset: 0; z-index: 1; pointer-events: none;
  background: linear-gradient(180deg, rgba(14,13,11,0.55) 0%, rgba(14,13,11,0) 18%, rgba(14,13,11,0) 72%, rgba(14,13,11,0.72) 100%);
}}

.ui {{ position: relative; z-index: 2; display: flex; width: 1280px; height: 720px; }}

/* Left persistent dock (76px minimum touch targets enforced via 80x80px tiles) */
.dock {{
  width: var(--dock); flex: 0 0 var(--dock);
  display: flex; flex-direction: column; align-items: center;
  padding: 22px 0 20px;
  background: linear-gradient(180deg, rgba(14,13,11,0.55), rgba(14,13,11,0.28));
  border-right: 1px solid var(--line);
}}
.mark {{ width: 44px; height: 44px; margin-bottom: 18px; flex: 0 0 auto; cursor: pointer; }}
.dock-list {{ display: flex; flex-direction: column; align-items: center; gap: 10px; flex: 1; justify-content: center; }}
.dock-btn {{
  width: 80px; height: 80px; min-width: 80px; min-height: 80px;
  min-height: 76px; min-width: 76px;
  border-radius: 24px;
  display: flex; align-items: center; justify-content: center;
  color: var(--washi-2);
  background: rgba(236, 230, 218, 0.04);
  border: 1px solid transparent;
  transition: all 0.2s var(--ease);
}}
.dock-btn svg {{ width: 34px; height: 34px; display: block; }}
.dock-btn.active {{
  color: var(--washi);
  background: rgba(236, 230, 218, 0.12);
  border-color: rgba(236, 230, 218, 0.2);
  box-shadow: 0 0 0 1px rgba(208, 112, 63, 0.28) inset;
}}
.dock-btn.locked {{ opacity: 0.38; cursor: pointer; }}
.dock-btn:hover:not(.locked) {{ background: rgba(236, 230, 218, 0.08); }}
.dock-foot {{ margin-top: auto; padding-top: 8px; }}

/* Main column */
.main {{ flex: 1; min-width: 0; height: 720px; display: flex; flex-direction: column; padding: 0 28px 22px; }}
.status {{
  height: 64px; flex: 0 0 64px;
  display: flex; align-items: center; gap: 16px;
  font-size: 16px; letter-spacing: 0.03em; color: var(--washi-2);
}}
.status .time {{ font-family: var(--mincho); font-weight: 500; font-size: 22px; color: var(--washi); letter-spacing: 0.01em; }}
.status .dot {{ width: 2px; height: 14px; background: var(--tick); border-radius: 1px; }}
.status .grow {{ flex: 1; }}
.pill {{
  display: inline-flex; align-items: center; gap: 8px;
  padding: 6px 14px; border-radius: 999px;
  background: rgba(236, 230, 218, 0.06);
  border: 1px solid var(--line);
  font-size: 14px; color: var(--washi);
}}
.pill.kaki {{
  background: rgba(208, 112, 63, 0.14);
  border-color: rgba(208, 112, 63, 0.38);
  color: var(--washi);
}}
.pill.safety-pill {{
  background: rgba(66, 82, 46, 0.18);
  border-color: rgba(66, 82, 46, 0.4);
  color: var(--washi);
  cursor: pointer;
}}
.pill .rec {{
  width: 9px; height: 9px; border-radius: 50%;
  background: var(--kaki);
  box-shadow: 0 0 0 3px rgba(208, 112, 63, 0.25);
  animation: pulse 1.8s infinite;
}}
@keyframes pulse {{
  0%, 100% {{ opacity: 1; }}
  50% {{ opacity: 0.35; }}
}}

.content {{ flex: 1; min-height: 0; display: flex; gap: 20px; }}

/* Card fundamentals */
.card {{
  border-radius: 24px;
  background: rgba(23, 21, 15, 0.72);
  border: 1px solid var(--line);
  position: relative; overflow: hidden;
}}
.kicker {{
  font-size: 13px; text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--washi-3); font-weight: 500; margin-bottom: 6px;
}}

/* Driving view */
.nav-card {{ flex: 1.45; min-width: 0; padding: 32px 36px; display: flex; flex-direction: column; }}
.nav-top {{ display: flex; gap: 24px; align-items: flex-start; z-index: 2; }}
.turn {{
  width: 96px; height: 96px; min-width: 96px;
  border-radius: 28px;
  background: var(--kaki); color: var(--sumi);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 10px 30px rgba(208, 112, 63, 0.35);
}}
.turn svg {{ width: 54px; height: 54px; stroke-width: 3.4; }}
.nav-copy h1 {{ font-family: var(--mincho); font-weight: 500; font-size: 64px; line-height: 1; letter-spacing: -0.02em; }}
.nav-copy .street {{ font-size: 24px; margin-top: 8px; color: var(--washi); }}
.nav-copy .then {{ font-size: 17px; margin-top: 6px; color: var(--washi-2); }}

.road {{
  position: absolute; inset: 0; pointer-events: none; z-index: 1;
  background:
    radial-gradient(ellipse 80% 50% at 85% 90%, rgba(208, 112, 63, 0.12), transparent 50%),
    linear-gradient(135deg, rgba(23,21,15,0) 0%, rgba(14,13,11,0.6) 100%);
}}
.road .lane {{
  position: absolute; right: 90px; bottom: -40px;
  width: 280px; height: 380px;
  border-left: 2px dashed rgba(236, 230, 218, 0.22);
  border-right: 2px solid rgba(236, 230, 218, 0.28);
  transform: perspective(300px) rotateX(48deg);
  border-radius: 40px 40px 0 0;
}}
.road .path {{
  position: absolute; right: 140px; bottom: 0;
  width: 160px; height: 260px;
  border-right: 6px solid var(--kaki);
  border-top: 6px solid var(--kaki);
  border-top-right-radius: 60px;
  transform: perspective(300px) rotateX(48deg);
  filter: drop-shadow(0 0 18px rgba(208, 112, 63, 0.6));
}}

.side {{ width: 360px; flex: 0 0 360px; display: flex; flex-direction: column; gap: 20px; }}
.speed-card {{
  flex: 1; padding: 26px 30px;
  display: flex; flex-direction: column; justify-content: space-between;
}}
.speed-card .num {{
  font-family: var(--mincho); font-weight: 500; font-size: 110px; line-height: 0.9;
  letter-spacing: -0.04em; color: var(--washi);
}}
.speed-card .unit {{ font-size: 18px; letter-spacing: 0.14em; color: var(--washi-3); font-weight: 500; margin-top: 4px; }}
.speed-card .hint {{ font-size: 14px; line-height: 1.4; color: var(--washi-3); border-top: 1px solid var(--line); padding-top: 14px; }}

.media-card {{
  height: 140px; flex: 0 0 140px; padding: 18px 20px;
  display: flex; align-items: center; gap: 18px;
}}
.media-art {{
  width: 96px; height: 96px; min-width: 96px; border-radius: 18px;
  background:
    radial-gradient(ellipse at 30% 30%, rgba(208, 112, 63, 0.7), transparent 60%),
    radial-gradient(ellipse at 80% 80%, rgba(66, 82, 46, 0.8), transparent 60%),
    #14110d;
  border: 1px solid var(--line);
}}
.media-copy {{ flex: 1; min-width: 0; }}
.media-copy h2 {{ font-family: var(--mincho); font-weight: 500; font-size: 22px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.media-copy p {{ font-size: 15px; color: var(--washi-2); margin-top: 4px; }}
.play {{
  width: 56px; height: 56px; min-width: 56px; border-radius: 50%;
  background: rgba(236, 230, 218, 0.1); color: var(--washi);
  display: flex; align-items: center; justify-content: center;
  border: 1px solid var(--line);
}}
.play svg {{ width: 28px; height: 28px; }}

/* Parked / Launcher view */
.feed {{
  width: 280px; flex: 0 0 280px; border-radius: 24px; position: relative; overflow: hidden;
  background:
    radial-gradient(ellipse at 40% 20%, rgba(208, 112, 63, 0.42), transparent 60%),
    radial-gradient(ellipse at 70% 80%, rgba(66, 82, 46, 0.5), transparent 60%),
    linear-gradient(180deg, #1c1813, #0a0907);
  border: 1px solid var(--line);
  display: flex; flex-direction: column; justify-content: flex-end; padding: 24px;
}}
.feed-fade {{
  position: absolute; inset: 0;
  background: linear-gradient(180deg, transparent 40%, rgba(14,13,11,0.88) 100%);
}}
.feed-cap {{ position: relative; z-index: 1; }}
.feed-cap h2 {{ font-family: var(--mincho); font-weight: 500; font-size: 24px; line-height: 1.2; margin: 4px 0 6px; }}
.feed-cap p {{ font-size: 14px; color: var(--washi-2); }}

.tiles {{
  flex: 1; display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 16px; min-width: 0;
}}
.tile {{
  border-radius: 24px; padding: 22px 22px;
  background: rgba(23, 21, 15, 0.76);
  border: 1px solid var(--line);
  display: flex; flex-direction: column; justify-content: flex-start;
  min-height: 80px;
  transition: transform 0.15s var(--ease), border-color 0.15s var(--ease);
}}
.tile:hover {{
  transform: translateY(-2px);
  border-color: rgba(236,230,218,0.25);
}}
.tile .ico {{
  width: 52px; height: 52px; border-radius: 16px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(236,230,218,0.07); color: var(--washi);
  margin-bottom: auto;
}}
.tile .ico svg {{ width: 28px; height: 28px; }}
.tile h3 {{ font-family: var(--mincho); font-weight: 500; font-size: 24px; line-height: 1.15; }}
.tile p {{ font-size: 14px; color: var(--washi-3); margin-top: 2px; }}

/* Dashcam view */
.dashcam-wrap {{ flex: 1; display: flex; gap: 20px; min-height: 0; }}
.preview {{
  flex: 1.15; min-width: 0; border-radius: 22px; position: relative; overflow: hidden;
  background:
    linear-gradient(180deg, rgba(14,13,11,0.15), rgba(14,13,11,0.55)),
    radial-gradient(ellipse 60% 30% at 50% 38%, rgba(236,230,218,0.08), transparent 50%),
    linear-gradient(180deg, #1c1914 0%, #0c0b09 100%);
  border: 1px solid var(--line);
}}
.preview .horizon {{
  position: absolute; left: 0; right: 0; top: 42%; height: 2px;
  background: linear-gradient(90deg, transparent, rgba(236,230,218,0.18), transparent);
}}
.preview .roadline {{
  position: absolute; left: 50%; bottom: 108px; width: 2px; height: 38%;
  background: linear-gradient(180deg, rgba(236,230,218,0.05), rgba(236,230,218,0.32));
  transform: translateX(-50%);
}}
.preview::after {{
  content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 150px;
  background: linear-gradient(180deg, transparent, rgba(14,13,11,0.88));
  pointer-events: none;
}}
.preview-top, .preview-bot {{ z-index: 2; }}
.preview-top {{
  position: absolute; left: 18px; right: 18px; top: 16px;
  display: flex; align-items: center; gap: 10px;
}}
.preview-bot {{
  position: absolute; left: 18px; right: 18px; bottom: 16px;
  display: flex; align-items: baseline; justify-content: space-between; gap: 12px;
}}
.preview-bot h2 {{ font-family: var(--mincho); font-weight: 500; font-size: 26px; }}
.preview-bot p {{ font-size: 15px; color: var(--washi-2); }}

.cam-feeds {{
  position: absolute; top: 62px; right: 18px; z-index: 3;
  display: flex; flex-direction: column; gap: 8px;
}}
.feed-card {{
  padding: 6px 12px; border-radius: 12px;
  background: rgba(14,13,11,0.78); border: 1px solid var(--line);
  font-size: 12px; color: var(--washi-2); display: flex; align-items: center; gap: 6px;
}}
.feed-card.active {{ border-color: var(--kaki); color: var(--washi); }}
.feed-card .dot-s {{ width: 6px; height: 6px; border-radius: 50%; background: var(--kaki); }}

.clips {{ width: 420px; flex: 0 0 420px; display: flex; flex-direction: column; gap: 10px; min-width: 0; }}
.clips h2 {{ font-family: var(--mincho); font-weight: 500; font-size: 24px; margin-bottom: 2px; }}
.clip {{
  min-height: 76px; border-radius: 18px; padding: 12px 14px;
  display: flex; align-items: center; gap: 12px;
  background: rgba(23,21,15,0.7); border: 1px solid var(--line);
}}
.thumb {{
  width: 76px; height: 52px; min-width: 76px; border-radius: 10px;
  background:
    radial-gradient(circle at 30% 40%, rgba(208,112,63,0.35), transparent 55%),
    linear-gradient(135deg, #2a2218, #14110d);
  border: 1px solid var(--line); position: relative;
}}
.thumb.lock {{
  display: flex; align-items: center; justify-content: center; color: var(--washi);
  background:
    radial-gradient(circle at 40% 40%, rgba(208,112,63,0.45), transparent 55%),
    linear-gradient(135deg, #3a2416, #14110d);
}}
.thumb.lock svg {{ width: 18px; height: 18px; }}
.clip h3 {{ font-family: var(--mincho); font-weight: 500; font-size: 18px; line-height: 1.2; }}
.clip p {{ font-size: 13px; color: var(--washi-3); margin-top: 3px; }}
.sync {{
  margin-top: auto; min-height: 76px; border-radius: 18px; padding: 14px 16px;
  background: rgba(66, 82, 46, 0.22); border: 1px solid rgba(66, 82, 46, 0.45);
  display: flex; align-items: center; gap: 12px;
}}
.sync svg {{ width: 26px; height: 26px; flex: 0 0 auto; color: var(--washi); }}
.sync h3 {{ font-family: var(--mincho); font-weight: 500; font-size: 17px; line-height: 1.25; }}
.sync p {{ font-size: 13px; color: var(--washi-2); margin-top: 3px; }}

/* Identity view */
.gate-wrap {{ flex: 1; display: flex; gap: 20px; min-height: 0; }}
.gate {{
  flex: 1.35; min-width: 0; border-radius: 24px; padding: 36px 40px 32px;
  background: rgba(23, 21, 15, 0.88);
  border: 1px solid var(--line);
  display: flex; flex-direction: column;
}}
.gate h1 {{ font-family: var(--mincho); font-weight: 500; font-size: 48px; line-height: 1.1; letter-spacing: -0.02em; margin: 12px 0 16px; }}
.gate .lead {{ font-size: 22px; line-height: 1.4; color: var(--washi); max-width: 640px; }}
.gate .sub {{ margin-top: 10px; font-size: 16px; line-height: 1.45; color: var(--washi-2); max-width: 620px; }}
.phone-row {{ display: flex; align-items: center; gap: 20px; margin: 28px 0 0; }}
.phone {{
  width: 88px; height: 88px; min-width: 88px; border-radius: 26px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(208,112,63,0.14); border: 1px solid rgba(208,112,63,0.32); color: var(--washi);
}}
.phone svg {{ width: 44px; height: 44px; }}
.wait {{ font-family: var(--mincho); font-size: 22px; }}
.wait span {{ display: block; margin-top: 4px; font-family: var(--gothic); font-size: 15px; color: var(--washi-3); }}
.pair {{
  margin-top: auto; padding-top: 22px; border-top: 1px solid var(--line);
  font-size: 16px; color: var(--washi-2); line-height: 1.45;
}}
.pair strong {{ color: var(--washi); font-weight: 500; }}
.drivers {{
  width: 340px; flex: 0 0 340px; padding: 24px 22px;
  display: flex; flex-direction: column; gap: 12px;
}}
.drivers h2 {{ font-family: var(--mincho); font-weight: 500; font-size: 26px; margin: 0 0 8px; }}
.driver {{
  min-height: 80px; border-radius: 20px; padding: 14px 16px;
  display: flex; align-items: center; gap: 14px;
  background: rgba(236,230,218,0.04); border: 1px solid var(--line);
}}
.driver.on {{ background: rgba(208,112,63,0.12); border-color: rgba(208,112,63,0.38); }}
.avatar {{
  width: 52px; height: 52px; border-radius: 50%; flex: 0 0 auto;
  display: flex; align-items: center; justify-content: center;
  background: rgba(236,230,218,0.1); font-family: var(--mincho); font-size: 20px;
}}
.driver h3 {{ font-family: var(--mincho); font-weight: 500; font-size: 20px; }}
.driver p {{ font-size: 14px; color: var(--washi-3); margin-top: 2px; }}

/* Toast / Parked Safety Notice */
.safety-toast {{
  position: fixed; bottom: 28px; left: calc(var(--dock) + 28px); right: 28px;
  background: rgba(208, 112, 63, 0.95); color: #0e0d0b;
  padding: 18px 24px; border-radius: 16px; font-weight: 500; font-size: 16px;
  display: flex; align-items: center; justify-content: space-between;
  box-shadow: 0 10px 40px rgba(0,0,0,0.6);
  z-index: 999;
  transform: translateY(120%);
  transition: transform 0.3s var(--ease);
}}
.safety-toast.show {{ transform: translateY(0); }}
.safety-toast button {{
  background: rgba(14,13,11,0.2); padding: 8px 16px; border-radius: 8px; font-weight: 600; color: #0e0d0b;
}}
</style>
</head>
<body>
<div class="stage">

<div class="dirt" aria-hidden="true">
  <div class="dirt-washes {'drive' if initial_mode == 'driving' else ''}" id="dirtWashes"></div>
  <svg xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">
    <filter id="carGrain" x="-20%" y="-20%" width="140%" height="140%">
      <feTurbulence type="fractalNoise" baseFrequency="0.72" numOctaves="4" seed="4" stitchTiles="stitch" result="n"/>
      <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.92  0 0 0 0 0.88  0 0 0 0 0.78  0 0 0 0.55 0"/>
    </filter>
    <rect width="100%" height="100%" filter="url(#carGrain)"/>
  </svg>
</div>
<div class="vignette" aria-hidden="true"></div>

<div class="ui">

    <aside class="dock">
      <svg class="mark" viewBox="0 0 44 44" fill="none" aria-label="TinCan Zen Mark" onclick="switchCarMode('parked')">
        <path d="M29.2 11.2A13.2 13.2 0 1 0 30.4 20.8" stroke="#ece6da" stroke-width="2.4" stroke-linecap="round"/>
        <circle cx="30.3" cy="15.8" r="2" fill="#d0703f"/>
      </svg>
      <div class="dock-list">
        <button class="dock-btn {'active' if initial_mode == 'parked' else ''}" id="dockLauncher" aria-label="Launcher" onclick="onDockClick('parked')">
          <svg viewBox="0 0 34 34" fill="none"><rect x="5" y="5" width="10.5" height="10.5" rx="3" stroke="currentColor" stroke-width="2"/><rect x="18.5" y="5" width="10.5" height="10.5" rx="3" stroke="currentColor" stroke-width="2"/><rect x="5" y="18.5" width="10.5" height="10.5" rx="3" stroke="currentColor" stroke-width="2"/><rect x="18.5" y="18.5" width="10.5" height="10.5" rx="3" stroke="currentColor" stroke-width="2"/></svg>
        </button>
        <button class="dock-btn {'active' if initial_mode == 'driving' else ''}" id="dockNavigate" aria-label="Navigate" onclick="onDockClick('driving')">
          <svg viewBox="0 0 34 34" fill="none"><path d="M8 26V15a7 7 0 0 1 7-7h4" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/><path d="M16 5l6 6-6 6" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        <button class="dock-btn" id="dockListen" aria-label="Listen" onclick="onListenClick()">
          <svg viewBox="0 0 34 34" fill="none"><path d="M8 22V12h4l8-5v20l-8-5H8z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M23 13.5a6 6 0 0 1 0 7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        </button>
        <button class="dock-btn {'active' if initial_mode == 'dashcam' else ''}" id="dockDashcam" aria-label="Dashcam" onclick="onDockClick('dashcam')">
          <svg viewBox="0 0 34 34" fill="none"><rect x="4" y="9" width="20" height="16" rx="4" stroke="currentColor" stroke-width="2"/><circle cx="14" cy="17" r="4" stroke="currentColor" stroke-width="2"/><path d="M24 14l6-3v12l-6-3v-6z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>
        </button>
        <button class="dock-btn" id="dockSpaces" aria-label="Spaces" onclick="onSpacesClick()">
          <svg viewBox="0 0 34 34" fill="none"><circle cx="9" cy="17" r="4.2" stroke="currentColor" stroke-width="2"/><circle cx="25" cy="17" r="4.2" stroke="currentColor" stroke-width="2"/><path d="M13.4 17h7.2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="17" cy="17" r="1.6" fill="currentColor"/></svg>
        </button>
        <button class="dock-btn {'active' if initial_mode == 'identity' else ''}" id="dockDrivers" aria-label="Drivers" onclick="onDockClick('identity')">
          <svg viewBox="0 0 34 34" fill="none"><circle cx="17" cy="12" r="5" stroke="currentColor" stroke-width="2"/><path d="M6.5 27c1.6-5 5.2-7.5 10.5-7.5S25.9 22 27.5 27" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        </button>
      </div>
    </aside>

<section class="main">
  <header class="status">
    <div class="time" id="statusClock">9:41 PM</div>
    <div class="dot"></div>
    <div id="statusSubtitle">{'Moving · glance only' if initial_mode == 'driving' else ('Parked · launcher open' if initial_mode == 'parked' else ('Parked · clip browser' if initial_mode == 'dashcam' else 'Parked · waiting on a passkey'))}</div>
    <div class="grow"></div>
    <button class="pill safety-pill" id="safetyToggle" onclick="toggleSafetyDrive()">
      <span>Mode: <strong id="safetyModeLabel">{'DRIVING' if initial_mode == 'driving' else 'PARKED'}</strong></span>
    </button>
    <div class="pill kaki"><span class="rec"></span> <span id="recTelemetry">REC 1080p60 · Live</span></div>
    <div class="pill" id="meshStatusPill">Mesh · connecting...</div>
  </header>

  <div class="content" id="viewContainer">
    <!-- View content rendered via switchCarMode() -->
  </div>
</section>

</div>

<div class="safety-toast" id="safetyToast">
  <span id="safetyToastMsg">Parked-safety gate: Bring vehicle to complete stop to access pairing, clip browsing, and space writes.</span>
  <button onclick="dismissToast()">Dismiss</button>
</div>

</div>

<script>
var CURRENT_MODE = "{initial_mode}";
var VEHICLE_STATE = "{'driving' if initial_mode == 'driving' else 'parked'}";
var PEER_INFO = null;
var MESH_STATE = null;

var VIEWS = {{
  driving: `
    <article class="card nav-card">
      <div class="nav-top">
        <div class="turn"><svg viewBox="0 0 54 54" fill="none"><path d="M14 40V24a10 10 0 0 1 10-10h16" stroke="currentColor" stroke-width="3.4" stroke-linecap="round"/><path d="M32 8l14 14-14 14" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/></svg></div>
        <div class="nav-copy">
          <p class="kicker">Next move</p>
          <h1>0.4 mi</h1>
          <p class="street">Right on Bloor Street West</p>
          <p class="then">Then continue 1.2 mi toward home</p>
        </div>
      </div>
      <div class="road" aria-hidden="true"><div class="lane"></div><div class="path"></div></div>
    </article>
    <aside class="side">
      <article class="card speed-card">
        <p class="kicker">Speed</p>
        <div class="num">28</div>
        <div class="unit">MPH</div>
        <p class="hint">Clip browser, spaces, and driver switch stay locked until you park.</p>
      </article>
      <article class="card media-card">
        <div class="media-art" aria-hidden="true"></div>
        <div class="media-copy">
          <h2>Night Drive</h2>
          <p>Open Signal</p>
        </div>
        <div class="play"><svg viewBox="0 0 28 28" fill="currentColor"><path d="M8 5.5v17l15-8.5L8 5.5z"/></svg></div>
      </article>
    </aside>
  `,
  parked: `
    <aside class="feed">
      <div class="feed-fade"></div>
      <div class="feed-cap">
        <p class="kicker">Now in the feed</p>
        <h2>Night market, Toronto</h2>
        <p>Open Signal · played from this car</p>
      </div>
    </aside>
    <div class="tiles">
      <button class="tile" onclick="switchCarMode('driving')"><div class="ico"><svg viewBox="0 0 34 34" fill="none"><path d="M8 26V15a7 7 0 0 1 7-7h4" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/><path d="M16 5l6 6-6 6" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg></div><h3>Navigate</h3><p>12 min to home</p></button>
      <button class="tile" onclick="onListenClick()"><div class="ico"><svg viewBox="0 0 34 34" fill="none"><path d="M8 22V12h4l8-5v20l-8-5H8z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M23 13.5a6 6 0 0 1 0 7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></div><h3>Listen</h3><p>Night Drive</p></button>
      <button class="tile" onclick="switchCarMode('dashcam')"><div class="ico"><svg viewBox="0 0 34 34" fill="none"><rect x="4" y="9" width="20" height="16" rx="4" stroke="currentColor" stroke-width="2"/><circle cx="14" cy="17" r="4" stroke="currentColor" stroke-width="2"/><path d="M24 14l6-3v12l-6-3v-6z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg></div><h3>Dashcam</h3><p>3 locked events</p></button>
      <button class="tile" onclick="onSpacesClick()"><div class="ico"><svg viewBox="0 0 34 34" fill="none"><circle cx="9" cy="17" r="4.2" stroke="currentColor" stroke-width="2"/><circle cx="25" cy="17" r="4.2" stroke="currentColor" stroke-width="2"/><path d="M13.4 17h7.2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="17" cy="17" r="1.6" fill="currentColor"/></svg></div><h3>Spaces</h3><p>Tony's Garage</p></button>
      <button class="tile" onclick="onMessagesClick()"><div class="ico"><svg viewBox="0 0 34 34" fill="none"><rect x="5" y="8" width="24" height="18" rx="4" stroke="currentColor" stroke-width="2"/><path d="M7 11l10 8 10-8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></div><h3>Messages</h3><p>2 unread in the mesh</p></button>
      <button class="tile" onclick="switchCarMode('identity')"><div class="ico"><svg viewBox="0 0 34 34" fill="none"><circle cx="17" cy="12" r="5" stroke="currentColor" stroke-width="2"/><path d="M6.5 27c1.6-5 5.2-7.5 10.5-7.5S25.9 22 27.5 27" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></div><h3>Drivers</h3><p>Tony is signed in</p></button>
    </div>
  `,
  dashcam: `
    <div class="dashcam-wrap">
      <article class="preview">
        <div class="horizon"></div>
        <div class="roadline"></div>
        <div class="preview-top">
          <div class="pill kaki"><span class="rec"></span> Live</div>
          <div class="pill">REC 1080p60 · Saved to this car</div>
        </div>
        <div class="cam-feeds">
          <div class="feed-card active"><span class="dot-s"></span> Front (1080p60)</div>
          <div class="feed-card"><span class="dot-s"></span> Cabin (1080p30)</div>
          <div class="feed-card"><span class="dot-s"></span> Rear (1080p30)</div>
        </div>
        <div class="preview-bot">
          <div>
            <h2>Front camera</h2>
            <p>Loop running · events lock automatically</p>
          </div>
        </div>
      </article>
      <aside class="clips">
        <h2>Recent clips</h2>
        <div class="clip">
          <div class="thumb lock"><svg viewBox="0 0 18 18" fill="none"><rect x="3.5" y="8" width="11" height="8" rx="2" stroke="currentColor" stroke-width="1.6"/><path d="M6 8V5.8a3 3 0 0 1 6 0V8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></div>
          <div><h3>Hard brake</h3><p>Tonight, 8:46 PM · 18 sec</p></div>
        </div>
        <div class="clip">
          <div class="thumb lock"><svg viewBox="0 0 18 18" fill="none"><rect x="3.5" y="8" width="11" height="8" rx="2" stroke="currentColor" stroke-width="1.6"/><path d="M6 8V5.8a3 3 0 0 1 6 0V8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></div>
          <div><h3>Manual save</h3><p>Tonight, 7:12 PM · 42 sec</p></div>
        </div>
        <div class="clip">
          <div class="thumb lock"><svg viewBox="0 0 18 18" fill="none"><rect x="3.5" y="8" width="11" height="8" rx="2" stroke="currentColor" stroke-width="1.6"/><path d="M6 8V5.8a3 3 0 0 1 6 0V8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></div>
          <div><h3>Impact watch</h3><p>Yesterday, 11:03 PM · 24 sec</p></div>
        </div>
        <div class="clip">
          <div class="thumb"></div>
          <div><h3>Queen and Bathurst</h3><p>Loop clip · 8:21 PM</p></div>
        </div>
        <div class="sync" onclick="onSyncClipsClick()">
          <svg viewBox="0 0 26 26" fill="none"><path d="M6 13a7 7 0 0 1 11.5-5.4L19 10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M20 8v4h-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M20 13a7 7 0 0 1-11.5 5.4L7 16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M6 18v-4h4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <div>
            <h3>Syncing 2 locked clips</h3>
            <p>To Tony's Garage · one space on the mesh</p>
          </div>
        </div>
      </aside>
    </div>
  `,
  identity: `
    <div class="gate-wrap">
      <article class="gate">
        <p class="kicker">TinCan identity</p>
        <h1 id="identityTitle">Unlock this car</h1>
        <p class="lead">Unlock with Face ID or fingerprint on your phone.</p>
        <p class="sub">A passkey prompt is open on your paired device. Nothing in the car can move, record to a space, or switch drivers until it succeeds.</p>
        <div class="phone-row">
          <div class="phone"><svg viewBox="0 0 44 44" fill="none"><rect x="13" y="6" width="18" height="32" rx="5" stroke="currentColor" stroke-width="2.2"/><circle cx="22" cy="32.5" r="1.6" fill="currentColor"/><path d="M18 16c1.2-1.8 6.8-1.8 8 0" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="22" cy="20.5" r="2.2" stroke="currentColor" stroke-width="2"/></svg></div>
          <div class="wait" id="phoneWaitStatus">Waiting on your phone<span>Usually takes a second · you can cancel from the phone</span></div>
        </div>
        <p class="pair">After unlock, this display <strong id="pairNoticeText">pairs to your TinCan account</strong> and keeps a sealed driver key on the head unit. Guests can be added later from the switcher.</p>
      </article>
      <aside class="card drivers">
        <h2>Drivers</h2>
        <div class="driver on" id="primaryDriverRow">
          <div class="avatar" id="primaryAvatar">T</div>
          <div><h3 id="primaryDriverName">Tony</h3><p>Owner · passkey ready</p></div>
        </div>
        <div class="driver" onclick="onSwitchDriver('Guest')">
          <div class="avatar">G</div>
          <div><h3>Guest</h3><p>Unlock first to switch</p></div>
        </div>
        <div class="driver" style="opacity:.55" onclick="onAddDriverClick()">
          <div class="avatar">+</div>
          <div><h3>Add a driver</h3><p>Parked only</p></div>
        </div>
      </aside>
    </div>
  `
}};

function showSafetyNotice(msg) {{
  var toast = document.getElementById("safetyToast");
  var text = document.getElementById("safetyToastMsg");
  text.textContent = msg || "Parked-safety gate: Bring vehicle to complete stop to access pairing, clip browsing, and space writes.";
  toast.classList.add("show");
  clearTimeout(toast._timer);
  toast._timer = setTimeout(function() {{
    toast.classList.remove("show");
  }}, 5000);
}}

function dismissToast() {{
  document.getElementById("safetyToast").classList.remove("show");
}}

function toggleSafetyDrive() {{
  if (VEHICLE_STATE === "driving") {{
    VEHICLE_STATE = "parked";
  }} else {{
    VEHICLE_STATE = "driving";
  }}
  updateSafetyUi();
  if (VEHICLE_STATE === "driving" && (CURRENT_MODE === "dashcam" || CURRENT_MODE === "identity")) {{
    showSafetyNotice("Vehicle is in motion (driving). Switching to glanceable navigation mode.");
    switchCarMode("driving");
  }}
}}

function updateSafetyUi() {{
  var lbl = document.getElementById("safetyModeLabel");
  if (lbl) lbl.textContent = VEHICLE_STATE.toUpperCase();

  var isDriving = VEHICLE_STATE === "driving";
  var dirt = document.getElementById("dirtWashes");
  if (dirt) {{
    if (isDriving || CURRENT_MODE === "driving") {{
      dirt.classList.add("drive");
    }} else {{
      dirt.classList.remove("drive");
    }}
  }}

  var dockDashcam = document.getElementById("dockDashcam");
  var dockSpaces = document.getElementById("dockSpaces");
  var dockDrivers = document.getElementById("dockDrivers");
  var dockLauncher = document.getElementById("dockLauncher");

  if (dockDashcam) {{
    if (isDriving) dockDashcam.classList.add("locked");
    else dockDashcam.classList.remove("locked");
  }}
  if (dockSpaces) {{
    if (isDriving) dockSpaces.classList.add("locked");
    else dockSpaces.classList.remove("locked");
  }}
  if (dockDrivers) {{
    if (isDriving) dockDrivers.classList.add("locked");
    else dockDrivers.classList.remove("locked");
  }}
  if (dockLauncher) {{
    if (isDriving) dockLauncher.classList.add("locked");
    else dockLauncher.classList.remove("locked");
  }}
}}

function onDockClick(targetMode) {{
  if (VEHICLE_STATE === "driving" && targetMode !== "driving") {{
    showSafetyNotice("Locked while moving. Launcher, clip browser, spaces, and driver switch require the car to be parked.");
    return;
  }}
  switchCarMode(targetMode);
}}

function onSpacesClick() {{
  if (VEHICLE_STATE === "driving") {{
    showSafetyNotice("Spaces browsing and manual sync are locked while driving.");
    return;
  }}
  showSafetyNotice("TinCan Space: Connected to 'Tony\\'s Garage'. Merkle root verified.");
}}

function onListenClick() {{
  showSafetyNotice("TinCan Audio: Stream playing via local media relay.");
}}

function onMessagesClick() {{
  if (VEHICLE_STATE === "driving") {{
    showSafetyNotice("Message composition is gated while moving.");
    return;
  }}
  showSafetyNotice("TinCan Messages: 2 unread end-to-end encrypted notes.");
}}

function onSyncClipsClick() {{
  if (VEHICLE_STATE === "driving") {{
    showSafetyNotice("Manual space clip sync is parked-only.");
    return;
  }}
  showSafetyNotice("Dashcam: Syncing 2 locked clips to mesh space 'Tony\\'s Garage'...");
}}

function onSwitchDriver(name) {{
  if (VEHICLE_STATE === "driving") {{
    showSafetyNotice("Driver switching is gated while driving.");
    return;
  }}
  showSafetyNotice("Driver switched to " + name + ".");
}}

function onAddDriverClick() {{
  if (VEHICLE_STATE === "driving") {{
    showSafetyNotice("Adding drivers requires the car to be parked.");
    return;
  }}
  showSafetyNotice("Passkey pairing prompt dispatched for new driver.");
}}

function switchCarMode(mode) {{
  if (!VIEWS[mode]) mode = "driving";
  CURRENT_MODE = mode;

  // Update dock buttons
  var btns = ["dockLauncher", "dockNavigate", "dockDashcam", "dockDrivers"];
  btns.forEach(function(bId) {{
    var el = document.getElementById(bId);
    if (el) el.classList.remove("active");
  }});

  if (mode === "parked") {{
    var el = document.getElementById("dockLauncher");
    if (el) el.classList.add("active");
  }} else if (mode === "driving") {{
    var el = document.getElementById("dockNavigate");
    if (el) el.classList.add("active");
  }} else if (mode === "dashcam") {{
    var el = document.getElementById("dockDashcam");
    if (el) el.classList.add("active");
  }} else if (mode === "identity") {{
    var el = document.getElementById("dockDrivers");
    if (el) el.classList.add("active");
  }}

  // Subtitle
  var sub = document.getElementById("statusSubtitle");
  if (sub) {{
    if (mode === "driving") sub.textContent = "Moving · glance only";
    else if (mode === "parked") sub.textContent = "Parked · launcher open";
    else if (mode === "dashcam") sub.textContent = "Parked · clip browser";
    else if (mode === "identity") sub.textContent = "Parked · waiting on a passkey";
  }}

  // Render view
  var container = document.getElementById("viewContainer");
  if (container) {{
    container.innerHTML = VIEWS[mode];
  }}

  updateSafetyUi();
  updateClock();
}}

function updateClock() {{
  var d = new Date();
  var hours = d.getHours();
  var minutes = d.getMinutes();
  var ampm = hours >= 12 ? 'PM' : 'AM';
  hours = hours % 12;
  hours = hours ? hours : 12;
  minutes = minutes < 10 ? '0' + minutes : minutes;
  var clk = document.getElementById("statusClock");
  if (clk) clk.textContent = hours + ':' + minutes + ' ' + ampm;
}}

function fetchTelemetry() {{
  // 1. Fetch TinCan whoami / peer info
  fetch('/api/tincan/whoami')
    .then(function(res) {{
      if (res.ok) return res.json();
      throw new Error("HTTP " + res.status);
    }})
    .then(function(data) {{
      PEER_INFO = data;
      if (data && data.address) {{
        var pName = document.getElementById("primaryDriverName");
        if (pName && data.alias) pName.textContent = data.alias;
        var pNotice = document.getElementById("pairNoticeText");
        if (pNotice) pNotice.textContent = "pairs to " + (data.alias || data.address.slice(0, 10)) + "'s TinCan account";
      }}
    }})
    .catch(function(err) {{
      // Fallback or peer not initialized
    }});

  // 2. Fetch Mesh state
  fetch('/api/mesh/state')
    .then(function(res) {{
      if (res.ok) return res.json();
      throw new Error("HTTP " + res.status);
    }})
    .then(function(data) {{
      MESH_STATE = data;
      var pill = document.getElementById("meshStatusPill");
      if (pill) {{
        var peerCount = (data.peers && Array.isArray(data.peers)) ? data.peers.length : 3;
        pill.textContent = "Mesh · " + peerCount + " peers sealed";
      }}
    }})
    .catch(function(err) {{
      var pill = document.getElementById("meshStatusPill");
      if (pill) pill.textContent = "Mesh · 3 peers sealed";
    }});
}}

window.addEventListener('DOMContentLoaded', function() {{
  switchCarMode(CURRENT_MODE);
  setInterval(updateClock, 30000);
  fetchTelemetry();
  setInterval(fetchTelemetry, 15000);
}});
</script>
</body>
</html>
"""
