#!/usr/bin/env python3
"""
Scrape TikTok Favorites links from the active logged-in Google Chrome session
and paste/ingest each new video URL into TinCan Watch Party (`+ Ingest MP4`).

Requirements:
  - macOS Google Chrome with View -> Developer -> Allow JavaScript from Apple Events enabled
  - An open TikTok tab on your Favorites (or Collection) page
  - An open TinCan Mesh OS Watch Party tab (`#newVideoInput` / `+ Ingest MP4`)

Examples:
  python3 scripts/ingest_tiktok_favorites.py --dry-run
  python3 scripts/ingest_tiktok_favorites.py --limit 10
  python3 scripts/ingest_tiktok_favorites.py --mode modal --limit 5
  python3 scripts/ingest_tiktok_favorites.py --from-file favorites.txt
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

VIDEO_URL_RE = re.compile(r"(https?://(?:www\.)?tiktok\.com/@[^/?#]+/video/(\d{15,22}))")
PHOTO_URL_RE = re.compile(r"(https?://(?:www\.)?tiktok\.com/@[^/?#]+/photo/(\d{15,22}))")


@dataclass(frozen=True)
class ChromeTab:
    """Represents a Google Chrome window/tab pair."""

    window_index: int
    tab_index: int
    url: str
    title: str

    @property
    def label(self) -> str:
        return f"{self.window_index}:{self.tab_index}"


def run_osascript(script: str, args: Optional[List[str]] = None) -> str:
    """Run an AppleScript snippet with argv and return stripped stdout."""
    cmd = ["osascript", "-e", script]
    if args:
        cmd.extend(args)
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout).strip()
        raise RuntimeError(f"AppleScript error: {err}")
    return proc.stdout.strip()


def list_chrome_tabs() -> List[ChromeTab]:
    """Return all open Google Chrome tabs across windows."""
    script = """
    set sep to character id 9
    tell application "Google Chrome"
      set out to ""
      repeat with w from 1 to count of windows
        repeat with t from 1 to count of tabs of window w
          set out to out & w & sep & t & sep & (URL of tab t of window w) & sep & (title of tab t of window w) & linefeed
        end repeat
      end repeat
      return out
    end tell
    """
    raw = run_osascript(script)
    tabs: List[ChromeTab] = []
    for line in raw.splitlines():
        parts = line.split("\t", 3)
        if len(parts) < 3:
            continue
        tabs.append(
            ChromeTab(
                window_index=int(parts[0]),
                tab_index=int(parts[1]),
                url=parts[2],
                title=parts[3] if len(parts) > 3 else "",
            )
        )
    return tabs


def eval_tab_js(tab: ChromeTab, js_expr: str) -> Any:
    """Execute a JavaScript expression inside a specific Chrome tab and parse JSON output."""
    wrapped = f"(() => {{ try {{ return JSON.stringify({js_expr}); }} catch (err) {{ return JSON.stringify({{__js_error: String(err)}}); }} }})()"
    script = """
    on run argv
      set winIdx to (item 1 of argv) as integer
      set tabIdx to (item 2 of argv) as integer
      set jsCode to item 3 of argv
      tell application "Google Chrome"
        execute tab tabIdx of window winIdx javascript jsCode
      end tell
    end run
    """
    raw = run_osascript(script, [str(tab.window_index), str(tab.tab_index), wrapped])
    if not raw or raw == "missing value":
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if isinstance(parsed, dict) and "__js_error" in parsed:
        raise RuntimeError(f"Browser JS error on tab {tab.label}: {parsed['__js_error']}")
    return parsed


def parse_tab_override(spec: Optional[str], tabs: List[ChromeTab]) -> Optional[ChromeTab]:
    """Resolve an explicit `W:T` tab override if provided."""
    if not spec:
        return None
    m = re.match(r"^(\d+):(\d+)$", spec.strip())
    if not m:
        raise ValueError(f"Invalid tab format '{spec}'. Expected W:T (e.g. 3:1).")
    w_idx, t_idx = int(m.group(1)), int(m.group(2))
    for tab in tabs:
        if tab.window_index == w_idx and tab.tab_index == t_idx:
            return tab
    raise RuntimeError(f"Chrome tab {spec} not found.")


def find_target_tabs(
    tiktok_override: Optional[str] = None,
    watchparty_override: Optional[str] = None,
) -> Tuple[Optional[ChromeTab], ChromeTab]:
    """Locate the TikTok Favorites tab (if needed) and the Watch Party tab."""
    tabs = list_chrome_tabs()
    tt_tab = parse_tab_override(tiktok_override, tabs)
    wp_tab = parse_tab_override(watchparty_override, tabs)

    if wp_tab is None:
        for tab in tabs:
            try:
                has_wp = eval_tab_js(
                    tab,
                    "Boolean(document.getElementById('newVideoInput') && document.querySelector('button[onclick*=\"addVideoToPlaylist\"]'))",
                )
            except Exception:
                has_wp = False
            if has_wp:
                wp_tab = tab
                break

    if wp_tab is None:
        raise RuntimeError(
            "Could not find an open Watch Party tab containing #newVideoInput in Google Chrome."
        )

    if tt_tab is None:
        tiktok_candidates = [t for t in tabs if "tiktok.com" in t.url.lower()]
        for tab in tiktok_candidates:
            try:
                has_favs = eval_tab_js(
                    tab,
                    "Boolean(document.querySelector('[data-e2e=\"favorites-item-list\"], [data-e2e=\"favorites-tab\"]'))",
                )
            except Exception:
                has_favs = False
            if has_favs:
                tt_tab = tab
                break
        if tt_tab is None and tiktok_candidates:
            tt_tab = tiktok_candidates[0]

    return tt_tab, wp_tab


def normalize_tiktok_url(raw_url: str) -> Tuple[Optional[str], Optional[str], str]:
    """Return (clean_video_url, video_id, kind) for a TikTok link."""
    cleaned = raw_url.strip().split("?")[0].split("#")[0]
    m_vid = VIDEO_URL_RE.match(cleaned)
    if m_vid:
        return m_vid.group(1), m_vid.group(2), "video"
    m_photo = PHOTO_URL_RE.match(cleaned)
    if m_photo:
        return m_photo.group(1), m_photo.group(2), "photo"
    return None, None, "other"


def extract_visible_grid_links(tt_tab: ChromeTab) -> Dict[str, Any]:
    """Extract currently mounted favorite/collection links from the TikTok page DOM."""
    js = """
    (() => {
      const container =
        document.querySelector('[data-e2e="favorites-item-list"]') ||
        document.querySelector('[data-e2e="collection-item-list"]') ||
        document.querySelector('[data-e2e="user-post-item-list"]') ||
        document.querySelector('main');
      if (!container) return { urls: [], itemCount: 0, scrollY: window.scrollY, scrollHeight: document.documentElement.scrollHeight, innerHeight: window.innerHeight };

      const cards = container.querySelectorAll('[data-e2e="favorites-item"], [data-e2e="user-post-item"]');
      const anchors = cards.length
        ? Array.from(cards).flatMap(c => Array.from(c.querySelectorAll('a[href]')))
        : Array.from(container.querySelectorAll('a[href*="/video/"], a[href*="/photo/"]'));

      const seen = new Set();
      const urls = [];
      for (const a of anchors) {
        if (a.closest('[data-e2e="inbox-notifications"], [data-e2e="inbox-list"], nav, header')) continue;
        const href = a.href || '';
        if (!href.includes('/video/') && !href.includes('/photo/')) continue;
        if (!seen.has(href)) {
          seen.add(href);
          urls.push(href);
        }
      }
      return {
        urls,
        itemCount: cards.length || urls.length,
        scrollY: window.scrollY,
        scrollHeight: document.documentElement.scrollHeight,
        innerHeight: window.innerHeight
      };
    })()
    """
    return eval_tab_js(tt_tab, js) or {}


def collect_favorites_grid(
    tt_tab: ChromeTab,
    existing_ids: Optional[Set[str]] = None,
    new_limit: Optional[int] = None,
    max_scrolls: int = 200,
    scroll_pause: float = 1.2,
    stagnant_limit: int = 6,
) -> Tuple[List[str], int]:
    """Close any open modal if needed and scroll through TikTok Favorites collecting video URLs."""
    prep_js = """
    (() => {
      const closeBtn = document.querySelector('[data-e2e="browse-close"]');
      let closedModal = false;
      if (closeBtn) {
        closeBtn.click();
        closedModal = true;
      }
      const hasItems = Boolean(document.querySelector('[data-e2e="favorites-item"]'));
      const favTab = document.querySelector('[data-e2e="favorites-tab"]');
      let clickedFavTab = false;
      if (!hasItems && favTab && favTab.getAttribute('aria-selected') !== 'true' && !location.pathname.includes('/collection/')) {
        favTab.click();
        clickedFavTab = true;
      }
      return { closedModal, clickedFavTab };
    })()
    """
    prep = eval_tab_js(tt_tab, prep_js) or {}
    if prep.get("closedModal") or prep.get("clickedFavTab"):
        time.sleep(0.9)

    ordered_urls: List[str] = []
    seen_ids: Set[str] = set()
    skipped_photos: Set[str] = set()
    known_ids = existing_ids or set()
    new_found = 0
    stagnant_rounds = 0

    for _ in range(max_scrolls):
        snapshot = extract_visible_grid_links(tt_tab)
        new_in_step = 0
        for raw in snapshot.get("urls", []):
            clean_url, item_id, kind = normalize_tiktok_url(raw)
            if not clean_url or not item_id:
                continue
            if kind == "photo":
                skipped_photos.add(item_id)
                continue
            if item_id not in seen_ids:
                seen_ids.add(item_id)
                ordered_urls.append(clean_url)
                new_in_step += 1
                if item_id not in known_ids:
                    new_found += 1
                    if new_limit is not None and new_found >= new_limit:
                        return ordered_urls, len(skipped_photos)

        if new_in_step > 0:
            stagnant_rounds = 0
        else:
            stagnant_rounds += 1

        scroll_y = float(snapshot.get("scrollY") or 0)
        inner_h = float(snapshot.get("innerHeight") or 900)
        scroll_h = float(snapshot.get("scrollHeight") or 0)
        at_bottom = (scroll_y + inner_h) >= (scroll_h - 40)

        if stagnant_rounds >= stagnant_limit and at_bottom:
            break
        if stagnant_rounds >= stagnant_limit + 4:
            break

        eval_tab_js(
            tt_tab,
            """
            (() => {
              const items = document.querySelectorAll('[data-e2e="favorites-item"], [data-e2e="user-post-item"]');
              if (items.length) {
                items[items.length - 1].scrollIntoView({ behavior: 'instant', block: 'center' });
              }
              window.scrollBy(0, Math.max(600, window.innerHeight * 0.85));
              return true;
            })()
            """,
        )
        time.sleep(scroll_pause)

    return ordered_urls, len(skipped_photos)


def collect_favorites_modal(
    tt_tab: ChromeTab,
    existing_ids: Optional[Set[str]] = None,
    new_limit: Optional[int] = None,
    step_pause: float = 0.9,
) -> Tuple[List[str], int]:
    """Step through an open TikTok browse modal using the next-video button."""
    ordered_urls: List[str] = []
    seen_ids: Set[str] = set()
    skipped_photos: Set[str] = set()
    known_ids = existing_ids or set()
    new_found = 0
    max_steps = 500
    stagnant = 0

    for _ in range(max_steps):
        state = eval_tab_js(
            tt_tab,
            """
            (() => {
              const linkEl = document.querySelector('[data-e2e="browse-video-link"]');
              const raw = (linkEl && linkEl.innerText) ? linkEl.innerText.trim() : location.href;
              const nextBtn = document.querySelector('[data-e2e="arrow-right"]');
              const hasNext = Boolean(nextBtn && !nextBtn.disabled && nextBtn.getAttribute('aria-disabled') !== 'true');
              return { raw, hasNext };
            })()
            """,
        ) or {}
        raw = state.get("raw") or ""
        clean_url, item_id, kind = normalize_tiktok_url(raw)
        if clean_url and item_id:
            if kind == "photo":
                skipped_photos.add(item_id)
            elif item_id not in seen_ids:
                seen_ids.add(item_id)
                ordered_urls.append(clean_url)
                stagnant = 0
                if item_id not in known_ids:
                    new_found += 1
            else:
                stagnant += 1
        else:
            stagnant += 1

        if new_limit is not None and new_found >= new_limit:
            break
        if not state.get("hasNext") or stagnant >= 3:
            break

        eval_tab_js(
            tt_tab,
            "(() => { const b = document.querySelector('[data-e2e=\"arrow-right\"]'); if (b) b.click(); return Boolean(b); })()",
        )
        time.sleep(step_pause)

    return ordered_urls, len(skipped_photos)


def fetch_existing_watchparty_ids(wp_tab: ChromeTab) -> Set[str]:
    """Fetch existing video IDs directly from Watch Party `/api/playlist` in the tab."""
    sync_js = """
    (() => {
      try {
        const xhr = new XMLHttpRequest();
        xhr.open('GET', '/api/playlist', false);
        xhr.send(null);
        if (xhr.status >= 200 && xhr.status < 300) {
          const data = JSON.parse(xhr.responseText);
          return (data.videos || []).map(v => String(v.video_id || ''));
        }
      } catch (e) {}
      return [];
    })()
    """
    ids = eval_tab_js(wp_tab, sync_js)
    return {str(v) for v in (ids or []) if v}


def ensure_watchparty_window_visible(wp_tab: ChromeTab) -> None:
    """Open Watch Party (`#win-tv`) in the UI without triggering pop-out confirm dialogs."""
    js = """
    (() => {
      const win = document.getElementById('win-tv');
      if (!win) return false;
      const isHidden = win.style.display === 'none' || win.classList.contains('hidden') || win.classList.contains('minimized');
      if (isHidden) {
        win.style.display = 'flex';
        win.classList.remove('hidden', 'minimized');
        win.style.zIndex = '999';
      }
      const inp = document.getElementById('newVideoInput');
      if (inp) inp.scrollIntoView({ behavior: 'instant', block: 'center' });
      return true;
    })()
    """
    eval_tab_js(wp_tab, js)


def _run_page_script(wp_tab: ChromeTab, page_js: str) -> None:
    """Inject a short script tag into the page's main JS context and remove it immediately."""
    wrapped = f"""
    (() => {{
      const s = document.createElement('script');
      s.textContent = {json.dumps(page_js)};
      (document.head || document.documentElement).appendChild(s);
      s.remove();
      return true;
    }})()
    """
    eval_tab_js(wp_tab, wrapped)


def ingest_url_via_watchparty_ui(wp_tab: ChromeTab, url: str, timeout_s: float = 60.0) -> Tuple[bool, str]:
    """Paste a URL into `#newVideoInput`, click `+ Ingest MP4`, and wait for completion."""
    _run_page_script(
        wp_tab,
        """
        if (!window.__tcOrigAlert) { window.__tcOrigAlert = window.alert; }
        delete document.documentElement.dataset.tcLastAlert;
        window.alert = function(msg) {
          document.documentElement.dataset.tcLastAlert = String(msg || 'Unknown error');
        };
        """,
    )

    trigger_js = f"""
    (() => {{
      const inp = document.getElementById('newVideoInput');
      const btn = document.querySelector('button[onclick*="addVideoToPlaylist"]');
      if (!inp || !btn) return {{ started: false, error: 'Missing Watch Party input or + Ingest MP4 button' }};
      delete document.documentElement.dataset.tcLastAlert;
      inp.focus();
      inp.value = {json.dumps(url)};
      inp.dispatchEvent(new Event('input', {{ bubbles: true }}));
      inp.dispatchEvent(new Event('change', {{ bubbles: true }}));
      btn.click();
      return {{ started: true }};
    }})()
    """
    start_res = eval_tab_js(wp_tab, trigger_js) or {}
    if not start_res.get("started"):
        _run_page_script(wp_tab, "if (window.__tcOrigAlert) { window.alert = window.__tcOrigAlert; }")
        return False, str(start_res.get("error") or "Failed to trigger Watch Party UI")

    deadline = time.time() + timeout_s

    while time.time() < deadline:
        time.sleep(0.4)
        poll_js = """
        (() => {
          const inp = document.getElementById('newVideoInput');
          const alertMsg = document.documentElement.dataset.tcLastAlert || null;
          const val = inp ? inp.value.trim() : '';
          const badge = document.getElementById('playlistCounterBadge');
          const badgeText = badge ? badge.innerText.trim() : null;
          if (alertMsg) {
            return { done: true, ok: false, error: alertMsg, badge: badgeText };
          }
          if (val === '') {
            return { done: true, ok: true, badge: badgeText };
          }
          return { done: false };
        })()
        """
        status = eval_tab_js(wp_tab, poll_js) or {}
        if status.get("done"):
            _run_page_script(wp_tab, "if (window.__tcOrigAlert) { window.alert = window.__tcOrigAlert; }")
            if status.get("ok"):
                return True, f"badge={status.get('badge')}"
            return False, str(status.get("error") or "Ingest failed")

    _run_page_script(wp_tab, "if (window.__tcOrigAlert) { window.alert = window.__tcOrigAlert; }")
    return False, f"Timed out after {timeout_s:.0f}s waiting for + Ingest MP4"


def load_urls_from_file(path: Path) -> List[str]:
    """Load TikTok video URLs from a newline-delimited text file or JSON array."""
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []
    if raw.startswith("["):
        items = json.loads(raw)
        urls = [str(u).strip() for u in items if str(u).strip()]
    else:
        urls = [line.strip() for line in raw.splitlines() if line.strip() and not line.strip().startswith("#")]

    deduped: List[str] = []
    seen: Set[str] = set()
    for u in urls:
        clean_url, vid, kind = normalize_tiktok_url(u)
        if clean_url and vid and kind == "video" and vid not in seen:
            seen.add(vid)
            deduped.append(clean_url)
    return deduped


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy TikTok Favorites links from Chrome and ingest them into TinCan Watch Party."
    )
    parser.add_argument(
        "--mode",
        choices=("grid", "modal"),
        default="grid",
        help="Scrape Favorites grid by scrolling (grid) or step through open video modal (modal).",
    )
    parser.add_argument("--dry-run", action="store_true", help="List collected links without clicking + Ingest MP4.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of new videos to process.")
    parser.add_argument("--max-scrolls", type=int, default=200, help="Maximum scroll steps in grid mode.")
    parser.add_argument("--scroll-pause", type=float, default=1.2, help="Seconds to wait between grid scrolls.")
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds to wait between Watch Party ingests.")
    parser.add_argument("--timeout", type=float, default=60.0, help="Per-video timeout (seconds) for + Ingest MP4.")
    parser.add_argument("--include-existing", action="store_true", help="Also re-ingest videos already in Watch Party.")
    parser.add_argument("--tiktok-tab", default=None, help="Override Chrome TikTok tab as W:T (e.g. 3:1).")
    parser.add_argument("--watchparty-tab", default=None, help="Override Chrome Watch Party tab as W:T (e.g. 1:1).")
    parser.add_argument("--save-urls", type=Path, default=None, help="Write collected TikTok URLs to a file.")
    parser.add_argument("--from-file", type=Path, default=None, help="Ingest URLs from a file instead of scraping TikTok.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        tt_tab, wp_tab = find_target_tabs(args.tiktok_tab, args.watchparty_tab)
    except Exception as exc:
        print(f"[-] Chrome tab lookup failed: {exc}", file=sys.stderr)
        return 1

    print(f"[+] Watch Party tab: {wp_tab.label} ({wp_tab.url})")
    existing_ids = set() if args.include_existing else fetch_existing_watchparty_ids(wp_tab)

    if args.from_file:
        if not args.from_file.is_file():
            print(f"[-] File not found: {args.from_file}", file=sys.stderr)
            return 1
        urls = load_urls_from_file(args.from_file)
        skipped_photos = 0
        print(f"[+] Loaded {len(urls)} video URL(s) from {args.from_file}")
    else:
        if tt_tab is None:
            print("[-] No open TikTok tab found in Google Chrome.", file=sys.stderr)
            return 1
        print(f"[+] TikTok tab:      {tt_tab.label} ({tt_tab.url})")
        if args.mode == "modal":
            urls, skipped_photos = collect_favorites_modal(
                tt_tab,
                existing_ids=existing_ids,
                new_limit=args.limit,
            )
        else:
            urls, skipped_photos = collect_favorites_grid(
                tt_tab,
                existing_ids=existing_ids,
                new_limit=args.limit,
                max_scrolls=args.max_scrolls,
                scroll_pause=args.scroll_pause,
            )
        print(f"[+] Found {len(urls)} TikTok video link(s)" + (f" (skipped {skipped_photos} photo post(s))" if skipped_photos else ""))

    if args.save_urls:
        args.save_urls.parent.mkdir(parents=True, exist_ok=True)
        args.save_urls.write_text("\n".join(urls) + ("\n" if urls else ""), encoding="utf-8")
        print(f"[+] Saved URL list to {args.save_urls}")

    to_ingest: List[str] = []
    already_present = 0
    for url in urls:
        _, vid, _ = normalize_tiktok_url(url)
        if vid and vid in existing_ids:
            already_present += 1
            continue
        to_ingest.append(url)
        if args.limit is not None and len(to_ingest) >= args.limit:
            break

    print(f"[+] Already in Watch Party: {already_present} | Queued to ingest: {len(to_ingest)}")

    if args.dry_run:
        for idx, url in enumerate(to_ingest, 1):
            print(f"  [dry-run {idx}/{len(to_ingest)}] {url}")
        return 0

    if not to_ingest:
        print("[+] Nothing new to ingest.")
        return 0

    ensure_watchparty_window_visible(wp_tab)

    ok_count = 0
    fail_count = 0
    for idx, url in enumerate(to_ingest, 1):
        ok, detail = ingest_url_via_watchparty_ui(wp_tab, url, timeout_s=args.timeout)
        if ok:
            ok_count += 1
            print(f"[+{idx}/{len(to_ingest)}] Ingested {url} ({detail})")
        else:
            fail_count += 1
            print(f"[-{idx}/{len(to_ingest)}] Failed {url}: {detail}", file=sys.stderr)
        if idx < len(to_ingest) and args.delay > 0:
            time.sleep(args.delay)

    print(f"[+] Done: {ok_count} ingested, {fail_count} failed, {already_present} skipped (already present).")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
