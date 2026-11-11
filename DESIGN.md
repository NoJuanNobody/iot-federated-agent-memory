---
name: TinCan Mesh OS (startup shell)
description: A hushed ink-and-paper room around a vertical video feed, with every tool behind one mark.
colors:
  sumi: "#0e0d0b"
  sumi-soft: "#17150f"
  washi: "#ece6da"
  washi-quiet: "rgba(236, 230, 218, 0.66)"
  washi-dim: "rgba(236, 230, 218, 0.6)"
  washi-tick: "rgba(236, 230, 218, 0.38)"
  washi-hairline: "rgba(236, 230, 218, 0.14)"
  persimmon: "#d0703f"
  wash-rust: "#964622"
  wash-moss: "#42522e"
  wash-indigo: "#2e365c"
  wash-umber: "#705436"
typography:
  mark:
    fontFamily: "Shippori Mincho, Hiragino Mincho ProN, Yu Mincho, serif"
    fontSize: "1.05rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0.02em"
  caption-title:
    fontFamily: "Shippori Mincho, Hiragino Mincho ProN, Yu Mincho, serif"
    fontSize: "1.12rem"
    fontWeight: 500
    lineHeight: 1.35
    letterSpacing: "normal"
  launcher-name:
    fontFamily: "Shippori Mincho, Hiragino Mincho ProN, Yu Mincho, serif"
    fontSize: "clamp(1.6rem, 3.1vw, 2.3rem)"
    fontWeight: 500
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  caption-meta:
    fontFamily: "Zen Kaku Gothic New, Hiragino Sans, Yu Gothic, system-ui, sans-serif"
    fontSize: "0.78rem"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "0.03em"
  control:
    fontFamily: "Zen Kaku Gothic New, Hiragino Sans, Yu Gothic, system-ui, sans-serif"
    fontSize: "0.86rem"
    fontWeight: 400
    lineHeight: 1.2
    letterSpacing: "normal"
  field:
    fontFamily: "Zen Kaku Gothic New, Hiragino Sans, Yu Gothic, system-ui, sans-serif"
    fontSize: "0.95rem"
    fontWeight: 400
    lineHeight: 1.3
    letterSpacing: "0.02em"
  launcher-desc:
    fontFamily: "Zen Kaku Gothic New, Hiragino Sans, Yu Gothic, system-ui, sans-serif"
    fontSize: "0.82rem"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "normal"
  fine:
    fontFamily: "Zen Kaku Gothic New, Hiragino Sans, Yu Gothic, system-ui, sans-serif"
    fontSize: "0.72rem"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "0.03em"
rounded:
  key: "5px"
  focus: "6px"
  panel: "14px"
  gate: "16px"
  capsule: "999px"
spacing:
  caption-gap: "0.4rem"
  row-y: "0.5rem"
  mark-gap: "0.7rem"
  action-gap: "1.4rem"
  gutter: "1.5rem"
  gutter-phone: "1.1rem"
  launcher-column: "15rem"
  launcher-inset-x: "9vw"
  launcher-inset-y: "6vh"
components:
  mark:
    textColor: "{colors.washi}"
    typography: "{typography.mark}"
  caption-title:
    textColor: "{colors.washi}"
    typography: "{typography.caption-title}"
  caption-meta:
    textColor: "{colors.washi-quiet}"
    typography: "{typography.caption-meta}"
  sound-toggle:
    textColor: "{colors.washi-quiet}"
    typography: "{typography.control}"
  sound-toggle-hover:
    textColor: "{colors.washi}"
  join-button:
    textColor: "{colors.washi}"
    typography: "{typography.control}"
    rounded: "{rounded.capsule}"
    padding: "0.55rem 1.05rem"
  tick:
    backgroundColor: "{colors.washi-tick}"
    width: "2px"
    height: "18px"
  tick-current:
    backgroundColor: "{colors.persimmon}"
    width: "2px"
    height: "30px"
  launcher-row:
    textColor: "{colors.washi-quiet}"
    typography: "{typography.launcher-name}"
    padding: "0.5rem 0 0.5rem 1.5rem"
  launcher-row-selected:
    textColor: "{colors.washi}"
  launcher-search:
    textColor: "{colors.washi}"
    typography: "{typography.field}"
  key-cap:
    textColor: "{colors.washi-dim}"
    typography: "{typography.fine}"
    rounded: "{rounded.key}"
    padding: "0.1rem 0.4rem"
  clip-frame:
    backgroundColor: "#000000"
    rounded: "{rounded.panel}"
    height: "92dvh"
  window:
    backgroundColor: "{colors.sumi-soft}"
    rounded: "{rounded.panel}"
  gate-card:
    backgroundColor: "{colors.sumi-soft}"
    rounded: "{rounded.gate}"
---

# Design System: TinCan Mesh OS (startup shell)

## Overview

**Creative North Star: "The Ink Room"**

The shell is a dark room with one thing playing in it. A vertical clip sits in the middle, its own blurred image spreads behind it as a backdrop, and a slow, muddy wash of rust, moss, indigo and umber drifts over that backdrop under fine moving grain. Everything the interface adds is paper-white (washi) on ink (sumi): thin hairlines, small type, and a single persimmon accent. The interface is meant to be forgotten until the viewer reaches for it, and the clip is the thing the visitor came for.

Two voices carry the type. A soft Japanese-style serif (Shippori Mincho) names things: the mark, the clip title, the tools. A quiet humanist gothic (Zen Kaku Gothic New) does the small work: metadata, controls, hints, fields. Scale is used sparingly. The only large type in the whole shell is the tool list in the launcher, where a returning peer reads names the way a menu is read.

Depth comes from blur and darkness, not from raised objects. When a tool is called, the launcher deepens the wash and blurs the clip that is still playing behind it. When a window opens, the clip dims and softens and the window floats over it as a smoked, blurred pane with a hairline edge. The shell never fills the screen with chrome; when it has nothing to say, the chrome is invisible.

**Key Characteristics:**
- Ink ground, paper type, one persimmon accent; no second accent.
- Muddy, desaturated washes with film grain over a blurred copy of the playing clip.
- 1px washi hairlines as the only separator and border.
- Two typefaces with strict roles: serif names, gothic utilities.
- Chrome fades out when a window or the launcher is up, and returns when the feed returns.
- Motion is one long ease-out curve, vertical, and slow; reduced-motion stills the wash and grain and shortens every transition to 1ms.

## Colors

A near-black ink field, one warm paper white at three transparencies, one persimmon accent, and four muted earth washes that exist only as background atmosphere.

### Primary
- **Persimmon (kaki)** (#d0703f): The single accent. Used for the dot in the mark's ring, the current-clip tick, the selected-row dot in the launcher, the caret in the search field, and the text-selection tint (at 45% alpha). Nowhere else.

### Neutral
- **Sumi Ink** (#0e0d0b): The page and stage ground, the clip frame's surround, and the dark end of every wash gradient.
- **Sumi Soft** (#17150f): The surface for re-dressed windows (at 90% alpha) and the identity gate card (at 96% alpha).
- **Washi** (#ece6da): All primary text and the mark's ring. A warm off-white, never pure white.
- **Washi Quiet** (rgba 236, 230, 218 at 66%): Secondary text at rest: clip metadata, sound control, launcher names and descriptions when not selected.
- **Washi Dim** (rgba 236, 230, 218 at 60%): Tertiary text: placeholders, hint text, key caps, launcher footer. This is the legibility floor for text on the ink ground; do not go dimmer.
- **Washi Tick** (rgba 236, 230, 218 at 38%): Non-text marks only: inactive position ticks.
- **Washi Hairline** (rgba 236, 230, 218 at 14%): Every 1px border and divider: the clip frame ring, the search underline, window and gate edges, key cap outlines.

### Washes (atmosphere only, never UI fills)
- **Rust** (#964622), **Moss** (#42522e), **Indigo** (#2e365c), **Umber** (#705436): Radial blooms at 60-80% alpha, composed with `hard-light` blend over the backdrop and closed by a dark vignette. The launcher repeats rust and moss at about 30-34% alpha under a left-to-right ink gradient.

### Named Rules
**The One Ember Rule.** Persimmon marks position and selection and nothing else: where you are in the feed, which tool is selected, where the caret is. It never fills a button, a surface or a heading.

**The Three Paper Levels Rule.** Text is washi, washi-quiet or washi-dim. A new surface picks one of the three; it does not invent a fourth transparency or introduce a new hue for text.

**The Dirty Wash Rule.** Washes stay muddy and low in saturation, sit behind the clip, and are always closed by a vignette. A clean or saturated gradient is a different world.

## Typography

**Display / Name Font:** Shippori Mincho (with Hiragino Mincho ProN, Yu Mincho, serif)
**Body / UI Font:** Zen Kaku Gothic New (with Hiragino Sans, Yu Gothic, system-ui, sans-serif)

**Character:** A literary serif for names set against a clean, slightly warm gothic for utility. The serif is used in two weights only (500, 600); the gothic in one (400; a 500 is loaded but unused).

### Hierarchy
- **Launcher name** (500, clamp(1.6rem, 3.1vw, 2.3rem), 1.15, -0.01em tracking): The tool list. The only large type in the shell; single line, never wraps.
- **Mark** (600, 1.05rem, 0.02em): The "TinCan" wordmark next to the ring mark.
- **Clip title** (500, 1.12rem, 1.35, balanced wrap): Bottom-left caption, capped near 30ch.
- **Field** (400, 0.95rem, 0.02em): The launcher search input.
- **Control** (400, 0.86rem): Sound toggle and Join button labels.
- **Launcher description** (400, 0.82rem): One line beside each tool name.
- **Clip meta** (400, 0.78rem, 0.03em): Creator handle under the title.
- **Fine** (400, 0.72-0.74rem, 0.03-0.04em): Mark hint, key caps, launcher footer. This is the smallest size in the system and the floor.

### Named Rules
**The Two Voices Rule.** The serif names things (brand, clip, tool); the gothic does everything else. Do not set a control, field or paragraph in the serif, and do not set a name in the gothic.

**The Quiet Case Rule.** No uppercase, no wide tracking on labels. Hierarchy comes from face, size and the three paper levels.

## Layout

The stage is full-viewport and fixed. The 9:16 clip is centered at 92dvh tall (or narrower if the width would clip it, leaving 1rem each side), so on desktop it is a tall column between two fields of wash. Chrome is pinned to the viewport corners and edge: mark top-left, clip caption bottom-left, sound and Join bottom-right, position ticks centered on the right edge. All use a 1.5rem gutter with the bottom offset respecting the safe area.

The launcher is a left-weighted full-screen sheet: content in a column up to 42rem, inset about 9vw from the left and 6vh from the top and bottom, with the wash darkest on the left so the clip stays visible on the right. Each row is a two-column grid: a 15rem name column and a flexible description column, 1.25rem apart.

On phones (aspect narrower than 11:16, or width up to 560px) the clip becomes the screen: full-bleed, no radius, no shadow, with ink gradients at top (9rem) and bottom (15rem) so the chrome stays legible. The gutter tightens to 1.1rem, the caption moves above a full-width actions row (sound left, Join right), the launcher rows stack name over description, and open windows pin 0.75rem from each side at 4rem from the top.

Spacing is rem-based and unsystematic by design: small steps (0.4, 0.5, 0.7rem) inside a control, 1.4-1.5rem between groups. Do not retrofit a grid onto it.

## Elevation & Depth

Depth is tonal and optical, not structural. The clip frame has one soft, large, downward ambient shadow plus the hairline ring; everything else separates by blur, dimming and hairline. There are no raised buttons, no hard offset shadows and no glow.

State changes carry the depth. When a window opens (working state), the clip frame drops to 32% opacity with a 6px blur and the backdrop to 55%. When the launcher opens, the clip blurs 10px, dims to 72% brightness and scales to 97%, while the launcher's wash fades in over 520ms.

### Shadow and Blur Vocabulary
- **Clip frame** (`box-shadow: 0 40px 90px -30px rgba(0,0,0,0.85), 0 0 0 1px var(--zen-line)`): The one object that sits on the room.
- **Window** (`box-shadow: 0 30px 80px -24px rgba(0,0,0,0.8)`; `backdrop-filter: blur(22px) saturate(0.85)`): Smoked pane over the dimmed feed.
- **Gate card** (`box-shadow: 0 40px 100px -30px rgba(0,0,0,0.85)`) over a scrim of ink at 62% with `blur(18px) saturate(0.8)`.
- **Backdrop** (`filter: blur(34px) saturate(0.75) brightness(0.62)`): The blurred copy of the playing clip behind the frame.
- **Caption legibility** (`text-shadow: 0 1px 12px rgba(0,0,0,0.6-0.7)`): The only text shadow, on floating chrome over the clip.

### Named Rules
**The Recede Rule.** Feed chrome (caption, sound, Join, ticks) fades to zero and drops 6px while a window or the launcher is open. The mark never fades; it is the way back.

**The No Raised Surface Rule.** Nothing in the shell is lifted by an offset shadow. A new element earns separation with a hairline, a blur or a darker ground.

## Shapes

Soft, ordinary rounding on the big objects (the clip frame and windows at 14px, the gate card at 16px) and almost none on the small ones (key caps at 5px, focus outlines at 6px). Position ticks are 2px bars with a 1px radius. The selected launcher row gets a 7px round dot, not a highlight bar. On phones the clip loses its radius entirely and goes edge to edge. Hairlines are always 1px.

The single capsule in the shell is the Join control, and it is a hairline outline with a translucent ink fill, never a colored or filled pill.

## Components

### Mark
A 30px open ring (washi, 2.4px stroke) with a break at the upper right, closed by one small persimmon dot in the gap, beside the "TinCan" wordmark in the serif. On hover the ring rotates about -24deg over 900ms; on fine-pointer devices a "tools · ⌘K" hint slides in next to it. It is the single permanent control and sits above everything (z-index 70).

### Clip caption
Title in the serif over the creator handle in the gothic at washi-quiet, bottom-left. Updates through an `aria-live="polite"` region. On phones it sits above the actions row with a 5.5rem right margin.

### Sound toggle and Join (feed actions)
- **Sound toggle:** A 18px speaker line icon plus "Sound off / on" in the gothic. Washi-quiet at rest, washi on hover. No container.
- **Join the mesh:** The one container in the feed chrome. 1px washi border at 32% alpha, ink fill at 32% with a 10px backdrop blur, capsule radius, 0.55rem by 1.05rem padding. Hover lifts the fill to washi at 12% and the border to 55%, over 300ms.
- **Focus (all controls):** a 1px washi outline, 4px offset, 6px radius.

### Position ticks
A vertical list on the right edge: 2px by 18px bars at washi-tick; the current clip grows to 30px and turns persimmon. Each tick has an invisible 6px-by-10px hit-area expansion. They are buttons, not decoration.

### Launcher
A modal full-screen sheet over the still-playing clip. A search field with a washi-hairline underline (which brightens to 42% on focus, caret in persimmon) and an `esc` key cap, then the tool list. Each row is a serif name beside a gothic description; at rest washi-quiet, on hover or selection washi with a persimmon dot fading in at the left. Arrow keys move, enter opens, esc returns to the feed. A one-line footer teaches the keys. Admin-only tools are omitted unless the user is an admin.

### Re-dressed windows and the identity gate
The shell supplies the containers only: Sumi Soft surface at 90-96% alpha, washi hairline, 14px (windows) or 16px (gate) radius, the large soft shadow, header divider at washi 8%. Windows open centered over the dimmed feed. The gate adds one shell element, a quiet underlined text button, "Not now, back to the feed", that dismisses it. The interiors of both are the classic Mesh OS look and are not part of this system (see Known drift).

## Do's and Don'ts

### Do:
- **Do** let the clip be the brightest, most saturated thing on screen; the interface stays in ink and washi.
- **Do** use persimmon (#d0703f) only for position, selection and the caret.
- **Do** pick text color from washi (#ece6da), washi-quiet (66%) or washi-dim (60%).
- **Do** separate with a 1px washi-hairline (14%) or with blur and darkness.
- **Do** name things in Shippori Mincho and set utility text in Zen Kaku Gothic New.
- **Do** fade feed chrome out when anything modal is open, and return it when the feed returns.
- **Do** use the single easing curve `cubic-bezier(0.16, 1, 0.3, 1)`; durations of 260-620ms for state, 900ms for atmosphere, and 70s for the wash drift.
- **Do** honor reduced motion by stilling the wash and grain and cutting transitions to 1ms.
- **Do** keep every tool one gesture away: the mark or Cmd/Ctrl+K, with full keyboard operation.

### Don't:
- **Don't** add a second accent color or fill any surface with persimmon.
- **Don't** let the washes become clean, bright or saturated, or sit in front of the clip.
- **Don't** use a glow, a colored shadow or a hard offset shadow.
- **Don't** add a filled or colored pill, a button bar or a dock; the one capsule is the hairline Join.
- **Don't** open any window or form over the first clip; nothing opens until asked for.
- **Don't** set text below washi-dim or below 0.72rem.
- **Don't** use uppercase labels, wide tracking, or emoji in new shell UI.
- **Don't** copy the classic interior look (neon cyan, emerald and indigo fills, monospace, gradient call-to-action buttons) into new shell work.

## Known drift (recorded, not repaired, not part of the system)

- **Classic window interiors** (Board, Space, Arena, Network, Quests, Tokens, Terminal, Talk, Moderate) still carry the old slate-and-neon look: monospace type, cyan, emerald and indigo fills, gradient call-to-action buttons, emoji icons, and dense small controls. Only the window container and header are re-dressed.
- **The identity gate's interior** is likewise classic (monospace, emerald-to-cyan gradient button, emoji, red and amber banners); only its card, scrim and the "Not now" link belong to this world.
- **The Join control** is a capsule (999px radius) even though the world's intent was to avoid pills. It is recorded as built and limited to this single control; it is not a pattern to extend.
- **The launcher footer** uses arrow glyphs ("↑ ↓") as key hints and the mark hint uses the ⌘ glyph as text; these were not canonized as an icon style, and new hints should use key caps.
- **Washi-quiet (66%) and washi-dim (60%)** are close enough that the three paper levels read as two in practice.
- **Fonts** load from Google Fonts at runtime; on a failed load or a non-Apple system the fallbacks (generic serif, system-ui) will differ from the rendered evidence.
- **The clip itself** is content: the walkthrough video shows the old gold-and-mono app UI and is not governed by this system.
