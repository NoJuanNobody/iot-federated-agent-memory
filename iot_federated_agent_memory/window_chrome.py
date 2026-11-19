"""TinCan Mesh OS: shared Celadon window chrome.

One place for the Aeonik Celadon & Ink look of every Mesh OS window:

* ``render_titlebar`` is the shared titlebar component. Every window header in
  mesh_os_ui.py is a ``<!--TC_TITLEBAR {...}-->`` placeholder that expands to it,
  so all windows get the same Inter title, the same Pop Out / maximize / close
  controls and the same focus styling.
* ``CELADON_HEAD`` holds the design tokens (colours, radius scale, type), the
  self-hosted Inter + JetBrains Mono faces and the component styles.
* ``celadonize_classes`` compiles the legacy dark/neon Tailwind utilities
  (slate panels, cyan/emerald/indigo/amber text, gradient buttons, ...) into the
  Celadon tokens. It runs over the served HTML, so markup injected by other
  modules (for example the arena duel) is covered too, and it is idempotent.

Tokens come from c84394c (mesh_os_ui.py Terminal, designs_gallery.py):
background #ecf1e6, ink #111111, card #f4f8f0, 1px hairlines, Inter for text and
JetBrains Mono for monospace.
"""

from __future__ import annotations

import html as _html
import json
import re
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------
BG = "#ecf1e6"
INK = "#111111"
CARD = "#f4f8f0"
PAPER = "#ffffff"
MUTED = "#4a4a4a"      # 8.0:1 on BG, secondary text
FAINT = "#5c5c5c"      # 6.0:1 on BG, tertiary text / labels
DANGER = "#8a1c1c"     # errors only

RADIUS = {"xs": "4px", "sm": "8px", "md": "12px", "lg": "16px", "pill": "9999px"}

# Old palette words that must not survive in window bodies (see tests).
DARK_NEUTRALS = ("slate", "gray", "zinc", "neutral", "stone")
ACCENTS = (
    "red", "orange", "amber", "yellow", "lime", "green", "emerald", "teal", "cyan",
    "sky", "blue", "indigo", "violet", "purple", "fuchsia", "pink", "rose",
)

# ---------------------------------------------------------------------------
# Shared titlebar component
# ---------------------------------------------------------------------------
TITLEBAR_PLACEHOLDER_RE = re.compile(r"<!--TC_TITLEBAR (\{.*?\})-->")


def render_titlebar(win_id: str, title: str, icon: str = "", badge: str = "",
                    meta_html: str = "", extra_controls_html: str = "") -> str:
    """Markup for the one titlebar every Mesh OS window uses.

    ``title`` and ``badge`` are plain text (escaped here). ``meta_html`` and
    ``extra_controls_html`` are trusted markup from mesh_os_ui.py (for example
    the Terminal clock or the Fono link).
    """
    wid = _html.escape(win_id, quote=True)
    t = _html.escape(title)
    parts = [f'<div class="window-header tc-titlebar" data-tc-titlebar="{wid}">',
             '<div class="tc-titlebar__lead">']
    if icon:
        parts.append(f'<span class="tc-titlebar__icon" aria-hidden="true">{_html.escape(icon)}</span>')
    parts.append(f'<span class="window-title tc-titlebar__title" title="{_html.escape(title, quote=True)}">{t}</span>')
    if badge:
        parts.append(f'<span class="tc-titlebar__badge" title="{_html.escape(badge, quote=True)}">{_html.escape(badge)}</span>')
    if meta_html:
        parts.append(f'<span class="tc-titlebar__meta">{meta_html}</span>')
    parts.append('</div>')
    parts.append('<div class="window-controls tc-titlebar__controls">')
    if extra_controls_html:
        parts.append(extra_controls_html)
    parts.append(
        '<button type="button" class="tc-ctl tc-ctl--theme" data-tc-theme-toggle="1" '
        'onclick="if(window.TinCanTheme)window.TinCanTheme.toggle()" '
        'title="Toggle TinCan Dark / Light Mode" aria-label="Toggle Dark Mode">&#x263E; Dark</button>'
        f'<button type="button" class="tc-ctl tc-ctl--new" onclick="openWindowInstance(\'{wid}\')" '
        f'title="Open another independent {t} window" aria-label="New {t} window">&#x2B; New</button>'
        f'<button type="button" class="tc-ctl tc-ctl--pop" onclick="openPopoutWindow(\'{wid}\')" '
        f'title="Pop out into a separate window" aria-label="Pop out">&#x2197;&#xFE0E; Pop Out</button>'
        f'<button type="button" class="tc-ctl tc-ctl--max" onclick="maximizeWindow(\'{wid}\')" '
        f'title="Maximize" aria-label="Maximize">&#x25A1;</button>'
        f'<button type="button" class="tc-ctl tc-ctl--close" onclick="minimizeWindow(\'{wid}\')" '
        f'title="Close" aria-label="Close">&#x2715;</button>'
    )
    parts.append('</div></div>')
    return "".join(parts)


def expand_titlebars(html: str) -> str:
    def _sub(m: "re.Match[str]") -> str:
        spec = json.loads(m.group(1))
        return render_titlebar(
            spec["id"], spec["title"], spec.get("icon", ""), spec.get("badge", ""),
            spec.get("meta_html", ""), spec.get("extra_controls_html", ""),
        )
    return TITLEBAR_PLACEHOLDER_RE.sub(_sub, html)


# ---------------------------------------------------------------------------
# Legacy utility -> Celadon compiler
# ---------------------------------------------------------------------------
_COLOR_WORDS = DARK_NEUTRALS + ACCENTS + ("black", "white")
_UTIL_RE = re.compile(
    r"(?<![\w\-\[/#])"
    r"((?:[a-z0-9\-]+:)*)"                                   # variants: hover:, md:, group-hover:, placeholder:
    r"(bg|text|border(?:-[trblxy])?|from|via|to|ring|divide|shadow|accent|outline|ring-offset|caret|decoration|fill|stroke)"
    r"-(" + "|".join(_COLOR_WORDS) + r")"
    r"(?:-(\d{2,3}))?"
    r"(?:/(\d{1,3}))?"
    r"(?![\w\-/\]])"
)
_GRADIENT_RE = re.compile(r"(?<![\w\-])((?:[a-z0-9\-]+:)*)bg-gradient-to-(?:t|tr|r|br|b|bl|l|tl)(?![\w\-])")

INK_BG_TOKENS = (f"bg-[{INK}]", "bg-black")


def _is_ink_bg(prefix: str, util: str, color: str, shade: Optional[int], alpha: Optional[int]) -> bool:
    if prefix or util != "bg":
        return False
    if color == "black":
        return alpha is None
    if color in ACCENTS and shade is not None and 400 <= shade <= 800:
        return alpha is None or alpha >= 70
    return False


_INK_LITERAL_RE = re.compile(r"(?<![\w:\-])(?:bg-\[#111111\]|bg-black)(?![\w/\-])")


def _context_has_ink(tokens: List[Tuple[str, str, str, Optional[int], Optional[int]]], raw: str) -> bool:
    if _INK_LITERAL_RE.search(raw):
        return True
    for prefix, util, color, shade, alpha in tokens:
        if _is_ink_bg(prefix, util, color, shade, alpha):
            return True
    if _GRADIENT_RE.search(raw):
        m = re.search(r"(?<![\w\-:])from-(" + "|".join(ACCENTS) + r")-(\d{3})", raw)
        if m and 400 <= int(m.group(2)) <= 800:
            return True
    return False


def _map_token(prefix: str, util: str, color: str, shade: Optional[int], alpha: Optional[int],
               ink_ctx: bool, has_gradient: bool, gradient_ink: bool) -> str:
    """Return the Celadon replacement for one legacy utility ('' drops it)."""
    hover = "hover:" in prefix or "group-hover:" in prefix or "focus:" in prefix
    p = prefix
    neutral = color in DARK_NEUTRALS
    accent = color in ACCENTS
    s = shade or 0

    if "placeholder:" in prefix:
        return f"{p}{util}-[#737373]" if util == "text" else ""
    if util in ("from", "via", "to"):
        return ""  # gradients are flattened, see bg handling
    if util == "shadow":
        return ""  # coloured glows are off-system
    if util in ("ring", "outline", "ring-offset", "caret", "accent", "decoration", "fill", "stroke"):
        if color == "white" and util in ("fill", "stroke"):
            return f"{p}{util}-[{BG}]" if ink_ctx else f"{p}{util}-[{INK}]"
        return f"{p}{util}-[{INK}]"
    if util == "divide":
        return f"{p}divide-[{INK}]/10"

    if util == "bg":
        if color == "white":
            if alpha is not None and alpha <= 20:
                return f"{p}bg-black/5"
            return f"{p}bg-white"
        if color == "black":
            # Solid black is ink (buttons, video letterbox); translucent black panes become paper.
            return f"{p}bg-[{INK}]" if alpha is None else f"{p}bg-white"
        if hover:
            if (accent and 400 <= s <= 800 and (alpha is None or alpha >= 70)) or (ink_ctx and (alpha is None or alpha >= 70)):
                return f"{p}bg-[#333333]"
            return f"{p}bg-black/5"
        if neutral:
            if s >= 900:
                return f"{p}bg-[{CARD}]"
            if s >= 700:
                return f"{p}bg-white"
            if s >= 400:
                return f"{p}bg-black/10"
            return f"{p}bg-white"
        if accent:
            if alpha is not None and alpha <= 40:
                return f"{p}bg-transparent"
            if s >= 900:
                return f"{p}bg-[{CARD}]"
            if s >= 400:
                return f"{p}bg-[{INK}]"
            return f"{p}bg-white"

    if util == "text":
        if hover:
            return f"{p}text-[{BG}]" if ink_ctx else f"{p}text-black"
        if color == "black":
            return f"{p}text-[{INK}]"
        if color == "white" or (neutral and s <= 300) or (accent and s <= 500 and color not in ("red", "rose")):
            return f"{p}text-[{BG}]" if ink_ctx else f"{p}text-[{INK}]"
        if color in ("red", "rose"):
            return f"{p}text-[{BG}]" if ink_ctx else f"{p}text-[{DANGER}]"
        if neutral and s <= 500:
            return f"{p}text-[{BG}]/80" if ink_ctx else f"{p}text-[{MUTED}]"
        if neutral and s <= 600:
            return f"{p}text-[{BG}]/70" if ink_ctx else f"{p}text-[{FAINT}]"
        if neutral:
            return f"{p}text-[{INK}]"
        if accent:
            return f"{p}text-[{BG}]" if ink_ctx else f"{p}text-[{INK}]"

    if util.startswith("border"):
        if "placeholder:" in prefix:
            return ""
        if hover:
            return f"{p}{util}-[{INK}]"
        if color == "white":
            return f"{p}{util}-[{BG}]/40" if ink_ctx else f"{p}{util}-[{INK}]/15"
        if color == "black":
            return f"{p}{util}-[{INK}]"
        if neutral:
            return f"{p}{util}-[{INK}]/15" if s >= 700 or s == 0 else f"{p}{util}-[{INK}]/25"
        return f"{p}{util}-[{INK}]"

    return f"{p}{util}-[{INK}]"


def _compile_segment(seg: str) -> str:
    """Rewrite the utilities inside one class list / string literal."""
    found = []
    for m in _UTIL_RE.finditer(seg):
        prefix, util, color, shade, alpha = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
        found.append((prefix, util, color, int(shade) if shade else None, int(alpha) if alpha else None))
    has_gradient = bool(_GRADIENT_RE.search(seg))
    if not found and not has_gradient:
        return seg
    if has_gradient and "bg-clip-text" in seg:
        # Gradient-filled wordmarks become plain ink text.
        seg = _GRADIENT_RE.sub("", seg)
        seg = re.sub(r"(?<![\w\-:])(?:from|via|to)-[a-z]+(?:-\d{2,3})?(?:/\d{1,3})?(?![\w\-])", "", seg)
        seg = seg.replace("bg-clip-text", "").replace("text-transparent", f"text-[{INK}]")
        return re.sub(r"[ \t]{2,}", " ", seg)
    ink_ctx = _context_has_ink(found, seg)
    gradient_ink = False
    if has_gradient:
        m = re.search(r"(?<![\w\-:])from-(" + "|".join(_COLOR_WORDS) + r")(?:-(\d{3}))?", seg)
        if m:
            c, sh = m.group(1), int(m.group(2) or 0)
            gradient_ink = (c in ACCENTS and 400 <= sh <= 800) or c == "black"

    def _rep(m: "re.Match[str]") -> str:
        prefix, util, color = m.group(1), m.group(2), m.group(3)
        shade = int(m.group(4)) if m.group(4) else None
        alpha = int(m.group(5)) if m.group(5) else None
        return _map_token(prefix, util, color, shade, alpha, ink_ctx, has_gradient, gradient_ink)

    out = _UTIL_RE.sub(_rep, seg)
    if has_gradient:
        flat = f"bg-[{INK}]" if gradient_ink else f"bg-[{CARD}]"
        out = _GRADIENT_RE.sub(lambda m: m.group(1) + flat, out)
    out = re.sub(r"[ \t]{2,}", " ", out)
    return out


# Segments: class="..." values, then quoted JS strings. Templates are kept per line.
_SEGMENT_RE = re.compile(r'class="[^"\n]*"|className\s*=\s*\'[^\'\n]*\'|\'[^\'\n]*\'|"[^"\n]*"|`[^`\n]*`')


def _compile_line(line: str) -> str:
    if not _UTIL_RE.search(line) and not _GRADIENT_RE.search(line):
        return line
    pieces = []
    last = 0
    for m in _SEGMENT_RE.finditer(line):
        if m.start() < last:
            continue
        pieces.append(_compile_segment_outside(line[last:m.start()]))
        pieces.append(_compile_segment(m.group(0)))
        last = m.end()
    pieces.append(_compile_segment_outside(line[last:]))
    return "".join(pieces)


def _compile_segment_outside(text: str) -> str:
    # Utilities outside any quotes (rare, e.g. inside a ${cond ? a : b} split) map with no context.
    if not text or (not _UTIL_RE.search(text) and not _GRADIENT_RE.search(text)):
        return text
    return _compile_segment(text)


_STYLE_BLOCK_RE = re.compile(r"(<style\b[^>]*>.*?</style>)", re.S | re.I)


def celadonize_classes(html: str) -> str:
    """Compile legacy dark/neon utilities in markup and scripts (not <style>)."""
    parts = _STYLE_BLOCK_RE.split(html)
    out = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(part)
            continue
        out.append("\n".join(_compile_line(l) for l in part.split("\n")))
    return "".join(out)


LEGACY_PALETTE_RE = re.compile(
    r"(?<![\w\-\[/#])(?:[a-z\-]+:)*(?:bg|text|border|from|via|to|ring|divide)-(?:"
    + "|".join(DARK_NEUTRALS) + r")-(?:[6-9]00|950)(?:/\d+)?(?![\w\-])"
    r"|(?<![\w\-\[/#])(?:[a-z\-]+:)*(?:text|bg|border|from|to|via)-(?:cyan|emerald|indigo|purple|pink|amber|teal|violet|fuchsia|sky|lime|green|yellow|orange|blue)-\d{2,3}(?:/\d+)?(?![\w\-])"
    r"|(?<![\w\-])bg-gradient-to-[a-z]{1,2}(?![\w\-])"
)


def legacy_palette_classes(fragment: str) -> List[str]:
    """Old dark-palette utilities still present in ``fragment`` (used by tests)."""
    return [m.group(0) for m in LEGACY_PALETTE_RE.finditer(fragment)]


# ---------------------------------------------------------------------------
# Head: fonts, tokens, components
# ---------------------------------------------------------------------------
CELADON_HEAD = r"""
  <link rel="preload" href="/assets/fonts/inter-latin-wght.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="/assets/fonts/jetbrains-mono-latin-wght.woff2" as="font" type="font/woff2" crossorigin>
  <style id="tc-celadon">
    @font-face { font-family: "Inter"; font-style: normal; font-weight: 100 900; font-display: swap;
      src: url("/assets/fonts/inter-latin-wght.woff2") format("woff2"); }
    @font-face { font-family: "JetBrains Mono"; font-style: normal; font-weight: 100 800; font-display: swap;
      src: url("/assets/fonts/jetbrains-mono-latin-wght.woff2") format("woff2"); }

    :root {
      --tc-bg: #ecf1e6; --tc-ink: #111111; --tc-card: #f4f8f0; --tc-paper: #ffffff;
      --tc-muted: #4a4a4a; --tc-faint: #5c5c5c; --tc-danger: #8a1c1c;
      --tc-hair: 1px solid #111111; --tc-hair-soft: 1px solid rgba(17, 17, 17, 0.15); --tc-line: rgba(17, 17, 17, 0.22);
      --tc-font: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      --tc-mono: "JetBrains Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace;
      --tc-r-xs: 4px; --tc-r-sm: 8px; --tc-r-md: 12px; --tc-r-lg: 16px; --tc-r-pill: 9999px;
      --tc-shadow: 0 16px 40px rgba(0, 0, 0, 0.08);
      --tc-shadow-focus: 0 0 0 1px #111111, 0 0 0 4px rgba(17, 17, 17, 0.12), 0 24px 56px rgba(0, 0, 0, 0.16);
    }

    /* ---------- type ---------- */
    body, body .font-sans, .mesh-window, .mesh-window .window-body { font-family: var(--tc-font) !important; }
    .font-mono, code, pre, kbd, samp, .mesh-window input, .mesh-window textarea, .mesh-window select,
    .ranger-code, .ubar-wrap, .aeonik-notice { font-family: var(--tc-mono) !important; }
    .font-serif { font-family: var(--tc-font) !important; }

    /* ---------- window frame + body (radius scale: window lg, tiles md, controls sm, chips pill) ---------- */
    .mesh-window, .mesh-window[data-zen-window="true"], body.zen .mesh-window {
      background: var(--tc-bg) !important; color: var(--tc-ink) !important;
      border: var(--tc-hair) !important; border-radius: var(--tc-r-lg) !important;
      box-shadow: var(--tc-shadow) !important; backdrop-filter: none !important;
    }
    .mesh-window.window-focused { box-shadow: var(--tc-shadow-focus) !important; }
    .mesh-window:not(.window-focused) .tc-titlebar__title { color: var(--tc-faint) !important; }
    .mesh-window:not(.window-focused) .tc-titlebar { background: #e4eadd !important; }
    .mesh-window.popout-fullscreen { background: var(--tc-bg) !important; box-shadow: none !important; border-radius: var(--tc-r-lg) !important; }
    .mesh-window .window-body { background: var(--tc-bg) !important; color: var(--tc-ink) !important; }
    .mesh-window .window-resize-handle::after { border-color: rgba(17, 17, 17, 0.35) !important; }

    .mesh-window :is(.rounded, .rounded-sm, .rounded-md) { border-radius: var(--tc-r-sm) !important; }
    .mesh-window :is(.rounded-lg, .rounded-xl, .rounded-2xl, .rounded-3xl) { border-radius: var(--tc-r-md) !important; }
    .mesh-window .rounded-full { border-radius: var(--tc-r-pill) !important; }
    .mesh-window :is(.stat-card, .card, .panel-card, .stream-card, .quest-card) { border-radius: var(--tc-r-md) !important; }
    .mesh-window :is(input, textarea, select) { border-radius: var(--tc-r-sm) !important; }
    .mesh-window select { text-overflow: ellipsis; padding-right: 1.75rem !important; }

    /* ---------- shared titlebar ---------- */
    .mesh-window .tc-titlebar {
      display: flex; align-items: center; justify-content: space-between; gap: 0.75rem;
      padding: 10px 12px 10px 16px !important; min-height: 44px;
      background: var(--tc-bg) !important; border-bottom: var(--tc-hair) !important; color: var(--tc-ink) !important;
    }
    .tc-titlebar__lead { display: flex; align-items: center; gap: 0.5rem; min-width: 0; flex: 1 1 auto; }
    .tc-titlebar__icon { font-size: 15px; line-height: 1; flex-shrink: 0; }
    .mesh-window .tc-titlebar .tc-titlebar__title {
      font-family: var(--tc-font) !important; font-weight: 600 !important; font-size: 14px !important;
      letter-spacing: -0.01em !important; color: var(--tc-ink) !important;
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0;
    }
    .tc-titlebar__badge {
      flex-shrink: 1; min-width: 0; max-width: 16rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
      font-family: var(--tc-mono); font-size: 10px; font-weight: 500; letter-spacing: 0.04em; text-transform: uppercase;
      color: var(--tc-ink); border: var(--tc-hair); border-radius: var(--tc-r-pill); padding: 1px 8px; background: transparent;
    }
    .tc-titlebar__meta { display: inline-flex; align-items: baseline; gap: 0.5rem; font-family: var(--tc-mono); font-size: 11px; color: var(--tc-muted); white-space: nowrap; overflow: hidden; }
    .tc-titlebar__controls { display: flex; align-items: center; gap: 4px; flex-shrink: 0; }
    .mesh-window .tc-titlebar .tc-ctl, .mesh-window .tc-titlebar .window-controls .tc-ctl {
      display: inline-flex; align-items: center; justify-content: center; gap: 4px;
      height: 26px; min-width: 26px; padding: 0 8px !important; white-space: nowrap; flex-shrink: 0;
      font-family: var(--tc-font) !important; font-size: 12px !important; font-weight: 500 !important; line-height: 1;
      color: var(--tc-ink) !important; background: transparent !important; border: 1px solid transparent !important;
      border-radius: var(--tc-r-pill) !important; cursor: pointer; transition: background 120ms, color 120ms, border-color 120ms;
    }
    .mesh-window .tc-titlebar .tc-ctl--theme,
    .mesh-window .tc-titlebar .tc-ctl--new,
    .mesh-window .tc-titlebar .tc-ctl--pop { border-color: var(--tc-ink) !important; padding: 0 10px !important; }
    .mesh-window .tc-titlebar .tc-ctl:hover, .mesh-window .tc-titlebar .tc-ctl:focus-visible { background: var(--tc-ink) !important; color: var(--tc-bg) !important; outline: none; }
    .tc-titlebar__controls a { white-space: nowrap; }
    .tc-dragging-window iframe { pointer-events: none !important; }
    .mesh-window-instance .window-body { padding: 0 !important; flex: 1 1 auto !important; min-height: 0 !important; max-height: none !important; overflow: hidden !important; background: var(--tc-bg) !important; }
    .mesh-window-instance .tc-titlebar__badge { flex-shrink: 0 !important; }
    .mesh-window-instance .tc-titlebar__title { max-width: 14rem; }
    .tc-instance-count { display: inline-flex; align-items: center; justify-content: center; margin-left: 4px; padding: 0 5px; height: 15px; border-radius: 9999px; background: var(--tc-ink); color: var(--tc-bg); font-family: var(--tc-mono); font-size: 9px; font-weight: 700; line-height: 1; }

    /* ---------- body surfaces the compiler cannot express ---------- */
    .mesh-window .window-body [class*="bg-[#f4f8f0]"] { border-color: rgba(17, 17, 17, 0.15); }
    .mesh-window [class~="bg-[#111111]"], .mesh-window [class~="bg-[#111111]"] :is(span, b, strong, i, em, small) { color: var(--tc-bg); }
    .mesh-window .window-body button:focus-visible, .mesh-window .window-body a:focus-visible { outline: 2px solid var(--tc-ink); outline-offset: 2px; }
    .mesh-window ::placeholder { color: var(--tc-faint) !important; opacity: 1; }
    #rodinStatusNotice, #drivePlacesStatus { color: var(--tc-muted) !important; }
    .mesh-window ::-webkit-scrollbar-track { background: transparent; }
    .mesh-window ::-webkit-scrollbar-thumb { background: rgba(17, 17, 17, 0.25); border-radius: var(--tc-r-pill); }

    /* Empty-state panel used where a dashboard has no data yet */
    .tc-empty { border: 1px dashed rgba(17, 17, 17, 0.35); border-radius: var(--tc-r-md); background: var(--tc-card);
      padding: 0.75rem 0.9rem; font-size: 12px; color: var(--tc-muted); }
    .tc-empty strong { color: var(--tc-ink); font-weight: 600; }
    .tc-stat { display: grid; grid-template-rows: auto auto auto; align-content: start; gap: 2px; min-height: 76px; }
    .tc-stat__label { font-size: 10px; letter-spacing: 0.06em; text-transform: uppercase; color: var(--tc-faint); }
    .tc-stat__value { font-family: var(--tc-mono); font-size: 18px; font-weight: 600; color: var(--tc-ink); font-variant-numeric: tabular-nums; }
    .tc-stat__sub { font-size: 10px; color: var(--tc-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .tc-stat[data-empty="true"] .tc-stat__value { color: var(--tc-faint); font-weight: 500; font-size: 13px; }
    #orStatGrid > .tc-stat { background: var(--tc-card); border-color: var(--tc-line); }
    #orDashEmpty { display: block; padding: 12px 14px; font-size: 12px; line-height: 1.5; color: var(--tc-muted); }
    #orDashEmpty.hidden { display: none; }
    #orDashEmpty strong { display: block; margin-bottom: 2px; }
    .tc-provider-card { background: var(--tc-card); border-color: var(--tc-line); color: var(--tc-ink); }
    .tc-provider-card:hover { border-color: var(--tc-ink); }
    .tc-provider-card.is-selected { border-color: var(--tc-ink); box-shadow: inset 0 0 0 1px var(--tc-ink); }
    .tc-provider-stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px; margin: 0; padding-top: 6px; border-top: 1px solid rgba(17, 17, 17, 0.12); }
    .tc-provider-stats dt { font-size: 10px; letter-spacing: 0.06em; text-transform: uppercase; color: var(--tc-faint); }
    .tc-provider-stats dd { margin: 0; font-family: var(--tc-mono); font-size: 12px; font-weight: 600; font-variant-numeric: tabular-nums; color: var(--tc-ink); }
    .tc-swap-grid select, .tc-swap-grid input { min-width: 0; text-overflow: ellipsis; }
    .tc-chip { display: inline-flex; align-items: center; gap: 4px; padding: 2px 10px; border: var(--tc-hair); border-radius: var(--tc-r-pill);
      background: var(--tc-paper); color: var(--tc-ink); font-family: var(--tc-mono); font-size: 11px; line-height: 1.5; cursor: pointer; white-space: nowrap; }
    .tc-chip:hover, .tc-chip:focus-visible { background: var(--tc-ink); color: var(--tc-bg); outline: none; }
    .tc-btn { display: inline-flex; align-items: center; justify-content: center; gap: 6px; padding: 6px 14px; border-radius: var(--tc-r-pill);
      background: var(--tc-ink); color: var(--tc-bg); border: var(--tc-hair); font-weight: 600; font-size: 12px; white-space: nowrap; cursor: pointer; }
    .tc-btn:hover { background: #333333; }
    .tc-btn--ghost { background: transparent; color: var(--tc-ink); }
    .tc-btn--ghost:hover { background: var(--tc-ink); color: var(--tc-bg); }
    .tc-truncate { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

    /* Arena duel box (#arenaBattleBox today, .arena-duel once the context-store PR lands): styling only */
    :is(#arenaBattleBox, .arena-duel) { background: var(--tc-card) !important; border: var(--tc-hair) !important; border-radius: var(--tc-r-md) !important; }
    :is(#arenaBattleBox, .arena-duel) :is([id$="ResultA"], [id$="ResultB"]) { background: var(--tc-paper) !important; color: var(--tc-ink) !important; border: var(--tc-hair-soft); border-radius: var(--tc-r-sm) !important; }
    :is(#arenaBattleBox, .arena-duel) select { min-width: 12rem; width: 100%; }
    :is(#arenaBattleBox, .arena-duel) [id$="ModelsNote"] { color: var(--tc-muted) !important; }
    :is(#arenaBattleBox, .arena-duel) button[onclick*="Battle"], :is(#arenaBattleBox, .arena-duel) button[onclick*="runArena"], :is(#arenaBattleBox, .arena-duel) button[onclick*="arenaDuelRun"] {
      background: var(--tc-ink) !important; color: var(--tc-bg) !important; border-radius: var(--tc-r-pill) !important; }

    /* Ranger: no text selection while the splitter drags; names ellipsize with a tooltip */
    body.tc-dragging, body.tc-dragging * { user-select: none !important; -webkit-user-select: none !important; cursor: col-resize !important; }
    #rangerListPane .tc-truncate, #spaceFileList [data-path] span, #spaceFileList .truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-width: 0; }

    /* Identity gate in Celadon (shown over the feed and the classic desktop) */
    #accountSetupModal, body.zen #accountSetupModal { background: rgba(236, 241, 230, 0.82) !important; backdrop-filter: blur(8px) !important; }
    #accountSetupModal > div, body.zen #accountSetupModal > div, #accountSetupModal .modal-content, #accountSetupModal .bg-slate-900 {
      background: var(--tc-bg) !important; color: var(--tc-ink) !important; border: var(--tc-hair) !important;
      border-radius: var(--tc-r-lg) !important; box-shadow: var(--tc-shadow) !important; font-family: var(--tc-font) !important; }
    #accountSetupModal h2, #accountSetupModal h3 { font-family: var(--tc-font) !important; color: var(--tc-ink) !important; font-weight: 600 !important; }
    #accountSetupModal :is(input, select, textarea) { background: var(--tc-paper) !important; color: var(--tc-ink) !important; border: var(--tc-hair) !important; border-radius: var(--tc-r-sm) !important; }
    #zenGateBack { color: var(--tc-muted) !important; text-decoration-color: rgba(17, 17, 17, 0.3) !important; }

    /* Feed chrome belongs to the zen landing only, not to the classic desktop or single-window routes */
    body:not(.zen) #zenStage, body:not(.zen) .zen-chrome, body:not(.zen) #zenLauncher { display: none !important; }
    /* Single-window routes and pop-outs: the window is the page */
    body.tc-single #meshOsHud, body.tc-single #meshOsDock { display: none !important; }
    body.tc-single .mesh-window.popout-fullscreen { top: 8px !important; height: calc(100vh - 16px) !important; min-height: calc(100vh - 16px) !important; max-height: calc(100vh - 16px) !important; }
    body.tc-single .mesh-window.popout-fullscreen .window-body { height: calc(100vh - 62px) !important; max-height: calc(100vh - 62px) !important; }
    /* Embedded desktop instance iframe: parent frame already provides titlebar & drag/resize */
    body.tc-embed #accountSetupModal { display: none !important; }
    body.tc-embed #desktopWorkspace { padding: 0 !important; min-height: 100vh !important; }
    body.tc-embed .mesh-window.popout-fullscreen { top: 0 !important; left: 0 !important; right: 0 !important; bottom: 0 !important; width: 100vw !important; height: 100vh !important; min-height: 100vh !important; max-height: 100vh !important; border: 0 !important; border-radius: 0 !important; box-shadow: none !important; }
    body.tc-embed .mesh-window.popout-fullscreen .tc-titlebar, body.tc-embed .mesh-window.popout-fullscreen .window-resize-handle { display: none !important; }
    body.tc-embed .mesh-window.popout-fullscreen .window-body { height: 100vh !important; max-height: 100vh !important; }
    #meshOsHud { background: rgba(236, 241, 230, 0.94) !important; border-bottom: var(--tc-hair) !important; backdrop-filter: blur(8px); }

    /* =======================================================================
       Always-Dark Terminal Surfaces (#000000 Pitch-Black Monochrome Terminal)
       Guarantees the terminal is immediately recognizable as a dark terminal
       in both Light and Dark mode.
       ======================================================================= */
    .tcsh,
    #win-terminal .tc-term-body,
    #aiHomeHub .tc-ai-cmd-bar,
    #aiHomeHub .tc-ai-output,
    #zenOut {
      background: #000000 !important;
      color: #f5f5f5 !important;
      border-color: #ffffff !important;
    }
    #win-terminal .tc-term-top {
      background: #0c0c0c !important;
      border-bottom: 1px solid #2e2e2e !important;
      color: #a3a3a3 !important;
    }
    #win-terminal .tc-term-top span { color: #a3a3a3 !important; }
    #win-terminal .tc-term-top button {
      background: #171717 !important;
      color: #f5f5f5 !important;
      border-color: #333333 !important;
    }
    #win-terminal .tc-term-top button:first-of-type,
    #win-terminal .tc-term-top button:hover {
      background: #ffffff !important;
      color: #000000 !important;
      border-color: #ffffff !important;
    }
    #aiHomeHub .tc-ai-prompt-prefix { color: #ffffff !important; }
    #aiHomeHub .tc-ai-prompt-input { color: #f5f5f5 !important; caret-color: #ffffff !important; }
    #aiHomeHub .tc-ai-prompt-input::placeholder { color: #737373 !important; }
    #aiHomeHub .tc-ai-dispatch-btn { background: #ffffff !important; color: #000000 !important; border-color: #ffffff !important; }
    #aiHomeHub .tc-ai-output-body { color: #f5f5f5 !important; }
    #aiHomeHub .tc-ai-output-meta { color: #ffffff !important; }

    /* =======================================================================
       TinCan 2.2 · Monochrome Black & White Dark Mode (html[data-theme="dark"] / body.tc-dark)
       ======================================================================= */
    html[data-theme="dark"],
    body.tc-dark {
      --tc-bg: #0e0e0e;
      --tc-ink: #f5f5f5;
      --tc-card: #151515;
      --tc-paper: #1a1a1a;
      --tc-muted: #a3a3a3;
      --tc-faint: #737373;
      --tc-danger: #d4d4d4;
      --tc-hair: 1px solid #2e2e2e;
      --tc-hair-soft: 1px solid rgba(255, 255, 255, 0.14);
      --tc-line: rgba(255, 255, 255, 0.18);
      --tc-shadow: 0 24px 60px rgba(0, 0, 0, 0.65);
      --tc-shadow-focus: 0 0 0 1px #ffffff, 0 0 0 4px rgba(255, 255, 255, 0.16), 0 28px 68px rgba(0, 0, 0, 0.8);
      --zen-sumi: #050505;
      --zen-sumi-2: #0e0e0e;
      --zen-washi: #f5f5f5;
      --zen-washi-2: rgba(245, 245, 245, 0.72);
      --zen-washi-3: rgba(245, 245, 245, 0.52);
      --zen-tick: rgba(245, 245, 245, 0.35);
      --zen-line: #2e2e2e;
      --zen-kaki: #ffffff;
      background: #080808 !important;
      color: #f5f5f5 !important;
    }
    html[data-theme="dark"] body,
    body.tc-dark {
      background: #080808 !important;
      color: #f5f5f5 !important;
    }
    html[data-theme="dark"] #meshOsHud,
    body.tc-dark #meshOsHud,
    html[data-theme="dark"] #meshOsDock,
    body.tc-dark #meshOsDock {
      background: rgba(12, 12, 12, 0.94) !important;
      color: #f5f5f5 !important;
      border-color: #2e2e2e !important;
    }
    html[data-theme="dark"] .mesh-window:not(.window-focused) .tc-titlebar,
    body.tc-dark .mesh-window:not(.window-focused) .tc-titlebar {
      background: #0a0a0a !important;
    }
    html[data-theme="dark"] .mesh-window .tc-titlebar .tc-ctl--theme,
    body.tc-dark .mesh-window .tc-titlebar .tc-ctl--theme {
      background: #000000 !important;
      color: #ffffff !important;
      border-color: #ffffff !important;
    }
    html[data-theme="dark"] .mesh-window [class*="bg-[#ecf1e6]"],
    body.tc-dark .mesh-window [class*="bg-[#ecf1e6]"] {
      background-color: #0e0e0e !important;
      color: #f5f5f5 !important;
    }
    html[data-theme="dark"] .mesh-window [class*="bg-[#f4f8f0]"],
    body.tc-dark .mesh-window [class*="bg-[#f4f8f0]"] {
      background-color: #151515 !important;
      color: #f5f5f5 !important;
      border-color: #2e2e2e !important;
    }
    html[data-theme="dark"] .mesh-window :is(.bg-white, [class*="bg-[#ffffff]"]),
    body.tc-dark .mesh-window :is(.bg-white, [class*="bg-[#ffffff]"]) {
      background-color: #1a1a1a !important;
      color: #f5f5f5 !important;
      border-color: #2e2e2e !important;
    }
    html[data-theme="dark"] .mesh-window :is([class*="text-[#111111]"], .text-black),
    body.tc-dark .mesh-window :is([class*="text-[#111111]"], .text-black) {
      color: #f5f5f5 !important;
    }
    html[data-theme="dark"] .mesh-window :is([class*="text-[#4a4a4a]"], [class*="text-[#5c5c5c]"]),
    body.tc-dark .mesh-window :is([class*="text-[#4a4a4a]"], [class*="text-[#5c5c5c]"]) {
      color: #a3a3a3 !important;
    }
    html[data-theme="dark"] .mesh-window :is([class*="border-[#111111]"], .border-black),
    body.tc-dark .mesh-window :is([class*="border-[#111111]"], .border-black) {
      border-color: #2e2e2e !important;
    }
    html[data-theme="dark"] .mesh-window [class~="bg-[#111111]"],
    body.tc-dark .mesh-window [class~="bg-[#111111]"] {
      background-color: #ffffff !important;
      color: #000000 !important;
      border-color: #ffffff !important;
    }
    html[data-theme="dark"] .mesh-window [class~="bg-[#111111]"] :is(span, b, strong, i, em, small),
    body.tc-dark .mesh-window [class~="bg-[#111111]"] :is(span, b, strong, i, em, small) {
      color: #000000 !important;
    }
    html[data-theme="dark"] .mesh-window :is(input, textarea, select),
    body.tc-dark .mesh-window :is(input, textarea, select) {
      background-color: #0c0c0c !important;
      color: #f5f5f5 !important;
      border-color: #2e2e2e !important;
    }
    html[data-theme="dark"] :is(#aiHomeHub, #win-copilot, #win-workstation, #win-nodes, #win-billing),
    body.tc-dark :is(#aiHomeHub, #win-copilot, #win-workstation, #win-nodes, #win-billing) {
      --tc-desk: #080808 !important;
      --tc-bg: #0e0e0e !important;
      --tc-surface: #151515 !important;
      --tc-card: #1a1a1a !important;
      --tc-paper: #1a1a1a !important;
      --tc-ink: #f5f5f5 !important;
      --tc-muted: #a3a3a3 !important;
      --tc-faint: #737373 !important;
      --tc-green: #ffffff !important;
      --tc-crimson: #d4d4d4 !important;
      background: #0e0e0e !important;
      color: #f5f5f5 !important;
    }
    html[data-theme="dark"] #aiHomeSparkline rect,
    body.tc-dark #aiHomeSparkline rect {
      fill: #ffffff !important;
    }
    html[data-theme="dark"] :is(#accountSetupModal, body.zen #accountSetupModal),
    body.tc-dark :is(#accountSetupModal, body.zen #accountSetupModal) {
      background: rgba(5, 5, 5, 0.84) !important;
    }
  </style>
"""

CELADON_BODY_JS = r"""
  <script id="tc-celadon-js">
    (function () {
      // =====================================================================
      // TinCanTheme: Dark Mode (Monochrome Black & White) + Always-Dark Terminal
      // =====================================================================
      const THEME_STORAGE_KEY = 'tincan_theme';
      function resolveInitialTheme() {
        try {
          const q = new URLSearchParams(window.location.search || '');
          const qTheme = (q.get('theme') || '').toLowerCase();
          if (qTheme === 'dark' || qTheme === 'light') return qTheme;
          const saved = (localStorage.getItem(THEME_STORAGE_KEY) || '').toLowerCase();
          if (saved === 'dark' || saved === 'light') return saved;
        } catch (e) {}
        return 'dark';
      }
      function syncThemeButtons(mode) {
        const isDark = mode === 'dark';
        const nextPressed = isDark ? 'true' : 'false';
        const nextLabel = isDark ? '\u263E Dark' : '\u2600 Light';
        const nextTitle = isDark
          ? 'Dark Mode Active (click for Celadon Light; Terminal stays dark)'
          : 'Celadon Light Mode (click for Monochrome B&W Dark Mode)';
        document.querySelectorAll('[data-tc-theme-toggle]').forEach((btn) => {
          if (btn.getAttribute('aria-pressed') !== nextPressed) {
            btn.setAttribute('aria-pressed', nextPressed);
          }
          if (btn.textContent !== nextLabel) {
            btn.textContent = nextLabel;
          }
          if (btn.title !== nextTitle) {
            btn.title = nextTitle;
          }
        });
      }
      function applyTheme(mode, persist) {
        const clean = String(mode || '').toLowerCase() === 'light' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', clean);
        if (document.body) {
          document.body.classList.toggle('tc-dark', clean === 'dark');
          document.body.classList.toggle('tc-light', clean === 'light');
        }
        if (persist !== false) {
          try { localStorage.setItem(THEME_STORAGE_KEY, clean); } catch (e) {}
        }
        syncThemeButtons(clean);
        try {
          window.dispatchEvent(new CustomEvent('tincan:theme-changed', { detail: { theme: clean } }));
        } catch (e) {}
        return clean;
      }
      window.TinCanTheme = {
        get() {
          return document.documentElement.getAttribute('data-theme') || resolveInitialTheme();
        },
        set(mode) {
          return applyTheme(mode, true);
        },
        toggle() {
          const next = (this.get() === 'dark') ? 'light' : 'dark';
          return applyTheme(next, true);
        },
        syncButtons() {
          syncThemeButtons(this.get());
        },
      };
      applyTheme(resolveInitialTheme(), false);

      // Every window: the active one gets the focus ring, the rest step back.
      function focusFirstVisible() {
        if (document.querySelector('.mesh-window.window-focused')) return;
        const open = Array.from(document.querySelectorAll('.mesh-window')).filter(w => w.style.display !== 'none' && !w.classList.contains('hidden'));
        if (!open.length) return;
        open.sort((a, b) => (parseInt(b.style.zIndex || 0, 10) - parseInt(a.style.zIndex || 0, 10)));
        open[0].classList.add('window-focused');
      }
      window.addEventListener('load', () => {
        applyTheme(window.TinCanTheme.get(), false);
        setTimeout(focusFirstVisible, 400);
      });
      // Truncated names get their full text as a tooltip.
      function titleTruncated(root) {
        (root || document).querySelectorAll('.mesh-window .truncate, .mesh-window .tc-truncate').forEach(el => {
          if (!el.title && el.textContent && el.textContent.trim().length > 0) el.title = el.textContent.trim();
        });
      }
      const mo = new MutationObserver((muts) => {
        let sawThemeToggle = false;
        for (const m of muts) {
          for (let i = 0; i < m.addedNodes.length; i++) {
            const n = m.addedNodes[i];
            if (n && n.nodeType === 1) {
              titleTruncated(n);
              if (
                (n.hasAttribute && n.hasAttribute('data-tc-theme-toggle')) ||
                (n.querySelector && n.querySelector('[data-tc-theme-toggle]'))
              ) {
                sawThemeToggle = true;
              }
            }
          }
        }
        if (sawThemeToggle) {
          syncThemeButtons(window.TinCanTheme.get());
        }
      });
      window.addEventListener('load', () => { titleTruncated(document); mo.observe(document.body, { childList: true, subtree: true }); });
    })();
  </script>
"""


def apply_window_chrome(html: str) -> str:
    """Expand titlebars, compile legacy utilities and inject the Celadon head (idempotent)."""
    if 'id="tc-celadon"' in html:
        return html
    html = expand_titlebars(html)
    html = celadonize_classes(html)
    # Celadon styles go last in <head> so they win over the classic and zen styles.
    head_end = html.find("</head>")
    if head_end != -1:
        html = html[:head_end] + CELADON_HEAD + html[head_end:]
    body_end = html.rfind("</body>")
    if body_end != -1:
        html = html[:body_end] + CELADON_BODY_JS + html[body_end:]
    return html
