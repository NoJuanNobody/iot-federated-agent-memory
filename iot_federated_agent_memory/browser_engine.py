"""Thread-safe Playwright Chromium + HTTP Reader browser engine for TinCan Mesh OS & Agents.

Provides:
- ``TinCanBrowserManager``: manages per-session headless Chromium contexts via a
  dedicated worker thread (required by Playwright Sync API) with automatic
  HTTP/HTML reader fallback when Chromium binaries are absent.
- URL validation & SSRF protection (blocks loopback/private/metadata IPs by default).
- Interactive actions: navigate, click coordinates, selector click, fill, type,
  key press, scroll, history back/forward, reload, DOM/element extraction,
  screenshots, and saving extracted Markdown / PNG directly to ``.space`` VFS.
"""

from __future__ import annotations

import base64
import concurrent.futures
from html.parser import HTMLParser
import ipaddress
import os
import queue
import re
import socket
import struct
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zlib
from typing import Any, Callable, Dict, List, Optional, Tuple


DEFAULT_VIEWPORT_W = 1280
DEFAULT_VIEWPORT_H = 800
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def _encode_solid_png(width: int = 320, height: int = 180, rgb: Tuple[int, int, int] = (236, 241, 230)) -> bytes:
    """Create a valid minimal PNG image in pure Python stdlib for non-Chromium reader previews."""
    r, g, b = rgb
    raw_row = b"\x00" + bytes([r, g, b]) * width
    raw = raw_row * height
    compressed = zlib.compress(raw, level=6)

    def _chunk(tag: bytes, payload: bytes) -> bytes:
        crc = zlib.crc32(tag + payload) & 0xFFFFFFFF
        return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", compressed) + _chunk(b"IEND", b"")


def _slug_from_url(url: str, fallback: str = "webpage") -> str:
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").replace("www.", "")
    path = parsed.path.strip("/").replace("/", "_")
    raw = f"{host}_{path}" if path else host or fallback
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", raw).strip("_").lower()
    return cleaned[:42] or fallback


class _SimpleReaderHTMLParser(HTMLParser):
    """Extract title, clean readable text, links, and interactive elements from HTML."""

    _SKIP_TAGS = {"script", "style", "noscript", "svg", "template"}

    def __init__(self, base_url: str = "") -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self._skip_depth = 0
        self._in_title = False
        self.title_parts: List[str] = []
        self.text_parts: List[str] = []
        self.links: List[Dict[str, str]] = []
        self.elements: List[Dict[str, Any]] = []
        self._current_link_href: Optional[str] = None
        self._current_link_text: List[str] = []
        self._elem_idx = 0

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        t = tag.lower()
        if t in self._SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth > 0:
            return
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        if t == "title":
            self._in_title = True
        elif t in ("h1", "h2", "h3", "h4", "p", "li", "br", "tr", "div", "section", "article"):
            self.text_parts.append("\n")
        if t == "a" and attr_map.get("href"):
            href = urllib.parse.urljoin(self.base_url, attr_map["href"])
            self._current_link_href = href
            self._current_link_text = []
        elif t in ("input", "button", "textarea", "select"):
            self._elem_idx += 1
            el_type = attr_map.get("type", t)
            label = attr_map.get("aria-label") or attr_map.get("placeholder") or attr_map.get("name") or attr_map.get("value") or t
            el_id = attr_map.get("id")
            name = attr_map.get("name")
            sel = f"#{el_id}" if el_id else (f'{t}[name="{name}"]' if name else t)
            self.elements.append({
                "ref": f"@e{self._elem_idx}",
                "tag": t,
                "type": el_type,
                "label": label[:80],
                "selector": sel,
            })

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in self._SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth > 0:
            return
        if t == "title":
            self._in_title = False
        elif t == "a" and self._current_link_href is not None:
            txt = re.sub(r"\s+", " ", "".join(self._current_link_text)).strip()
            href = self._current_link_href
            self._current_link_href = None
            self._current_link_text = []
            if href.startswith(("http://", "https://")) and len(self.links) < 60:
                self.links.append({"text": (txt or href)[:90], "href": href})
                self._elem_idx += 1
                if len(self.elements) < 60:
                    self.elements.append({
                        "ref": f"@e{self._elem_idx}",
                        "tag": "a",
                        "type": "link",
                        "label": (txt or href)[:80],
                        "href": href,
                        "selector": f'a[href="{attr_escape(href)}"]',
                    })

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        if self._in_title:
            self.title_parts.append(data)
        if self._current_link_href is not None:
            self._current_link_text.append(data)
        stripped = data.strip()
        if stripped:
            self.text_parts.append(stripped + " ")

    def result(self) -> Dict[str, Any]:
        title = re.sub(r"\s+", " ", "".join(self.title_parts)).strip()
        raw_text = "".join(self.text_parts)
        lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in raw_text.splitlines()]
        clean_text = "\n".join(ln for ln in lines if ln)
        return {
            "title": title,
            "text": clean_text[:20000],
            "links": self.links,
            "elements": self.elements[:50],
        }


def attr_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _is_private_or_local_ip(ip_str: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        return (
            ip_obj.is_private
            or ip_obj.is_loopback
            or ip_obj.is_link_local
            or ip_obj.is_multicast
            or ip_obj.is_reserved
            or ip_obj.is_unspecified
        )
    except ValueError:
        return True


def normalize_and_validate_url(raw_url: str, *, allow_private: bool = False) -> str:
    """Normalize a URL or bare domain and validate against SSRF / non-HTTP schemes."""
    candidate = (raw_url or "").strip()
    if not candidate:
        raise ValueError("URL cannot be empty.")
    lower = candidate.lower()
    if lower.startswith(("javascript:", "data:", "vbscript:", "file:", "blob:", "about:")):
        raise ValueError(f"Unsupported URL scheme: {candidate.split(':', 1)[0]!r}.")
    if "://" not in candidate:
        candidate = f"https://{candidate}"
    parsed = urllib.parse.urlparse(candidate)
    if parsed.scheme.lower() not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme!r}. Only http/https are allowed.")
    host = (parsed.hostname or "").strip().lower()
    if not host:
        raise ValueError("URL is missing a hostname.")

    if not allow_private:
        if host in ("localhost", "ip6-localhost") or host.endswith((".local", ".internal", ".localhost")):
            raise ValueError(f"Blocked internal hostname: {host}")
        try:
            ipaddress.ip_address(host)
            if _is_private_or_local_ip(host):
                raise ValueError(f"Blocked private/loopback IP: {host}")
        except ValueError as err:
            if str(err).startswith("Blocked"):
                raise
            # Hostname resolution check (fail closed only if it resolves strictly to private/metadata IPs)
            try:
                infos = socket.getaddrinfo(host, None)
                resolved_ips = {info[4][0].split("%")[0] for info in infos if info[4]}
                if resolved_ips and all(_is_private_or_local_ip(ip) for ip in resolved_ips):
                    raise ValueError(f"Blocked private network host: {host}")
            except socket.gaierror:
                # Let the actual HTTP fetch/Playwright report DNS failures naturally.
                pass

    return parsed.geturl()


class _PlaywrightWorker:
    """Single-thread actor running Playwright's synchronous Chromium API safely."""

    def __init__(self) -> None:
        self._queue: queue.Queue[Optional[Tuple[Callable[[Any], Any], concurrent.futures.Future]]] = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._available: Optional[bool] = None
        self._init_error: Optional[str] = None

    def is_available(self) -> Tuple[bool, Optional[str]]:
        if self._available is not None:
            return self._available, self._init_error
        try:
            import playwright.sync_api  # noqa: F401
            self._available = True
            self._init_error = None
        except Exception as err:
            self._available = False
            self._init_error = str(err)
        return self._available, self._init_error

    def _ensure_started(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._thread = threading.Thread(target=self._loop, name="tincan-playwright-worker", daemon=True)
            self._thread.start()

    def _loop(self) -> None:
        pw = None
        browser = None
        try:
            from playwright.sync_api import sync_playwright

            pw = sync_playwright().start()
            browser = pw.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            )
        except Exception as err:
            self._available = False
            self._init_error = str(err)
            while True:
                item = self._queue.get()
                if item is None:
                    break
                _, fut = item
                if not fut.done():
                    fut.set_exception(RuntimeError(f"Playwright Chromium unavailable: {err}"))
            return

        try:
            while True:
                item = self._queue.get()
                if item is None:
                    break
                fn, fut = item
                try:
                    res = fn(browser)
                    if not fut.done():
                        fut.set_result(res)
                except Exception as exc:
                    if not fut.done():
                        fut.set_exception(exc)
        finally:
            try:
                if browser:
                    browser.close()
            except Exception:
                pass
            try:
                if pw:
                    pw.stop()
            except Exception:
                pass

    def run(self, fn: Callable[[Any], Any], timeout: float = 45.0) -> Any:
        ok, err = self.is_available()
        if not ok:
            raise RuntimeError(err or "Playwright unavailable")
        self._ensure_started()
        fut: concurrent.futures.Future = concurrent.futures.Future()
        self._queue.put((fn, fut))
        return fut.result(timeout=timeout)


class TinCanBrowserManager:
    """Manages interactive browser sessions (Chromium + Reader fallback) for Desktop & Agents."""

    def __init__(self, *, allow_private: bool = False, prefer_playwright: bool = True) -> None:
        self.allow_private = allow_private
        self.prefer_playwright = prefer_playwright
        self._worker = _PlaywrightWorker()
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def status(self) -> Dict[str, Any]:
        ok, err = self._worker.is_available() if self.prefer_playwright else (False, "reader-only mode")
        return {
            "playwright_available": ok,
            "engine_default": "playwright" if ok else "reader",
            "active_sessions": len(self._sessions),
            "error": err,
        }

    def _get_or_create_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        sid = (session_id or "").strip() or f"br-{uuid.uuid4().hex[:10]}"
        with self._lock:
            sess = self._sessions.get(sid)
            if not sess:
                sess = {
                    "session_id": sid,
                    "url": "about:blank",
                    "title": "New Tab",
                    "status": 200,
                    "engine": "idle",
                    "text": "",
                    "links": [],
                    "elements": [],
                    "history": [],
                    "history_idx": -1,
                    "console_logs": [],
                    "screenshot_b64": "",
                    "updated_at": time.time(),
                    "_pw_page": None,
                    "_pw_context": None,
                }
                self._sessions[sid] = sess
            return sess

    def _public_snapshot(self, sess: Dict[str, Any], *, include_screenshot: bool = True) -> Dict[str, Any]:
        out = {
            "ok": True,
            "session_id": sess["session_id"],
            "url": sess.get("url", "about:blank"),
            "title": sess.get("title", ""),
            "status": sess.get("status", 200),
            "engine": sess.get("engine", "reader"),
            "text": sess.get("text", ""),
            "links": list(sess.get("links") or []),
            "elements": list(sess.get("elements") or []),
            "can_back": sess.get("history_idx", -1) > 0,
            "can_forward": 0 <= sess.get("history_idx", -1) < len(sess.get("history") or []) - 1,
            "history_count": len(sess.get("history") or []),
            "console_logs": list(sess.get("console_logs") or [])[-20:],
            "updated_at": sess.get("updated_at"),
        }
        if include_screenshot:
            out["screenshot_b64"] = sess.get("screenshot_b64", "")
        return out

    def _ensure_pw_page(self, browser: Any, sess: Dict[str, Any]) -> Any:
        page = sess.get("_pw_page")
        if page and not page.is_closed():
            return page
        ctx = browser.new_context(
            viewport={"width": DEFAULT_VIEWPORT_W, "height": DEFAULT_VIEWPORT_H},
            user_agent=DEFAULT_USER_AGENT,
        )
        page = ctx.new_page()
        page.set_default_timeout(20000)

        def _on_console(msg: Any) -> None:
            try:
                logs = sess.setdefault("console_logs", [])
                logs.append(f"[{msg.type}] {msg.text}"[:240])
                if len(logs) > 40:
                    del logs[:-40]
            except Exception:
                pass

        page.on("console", _on_console)
        sess["_pw_context"] = ctx
        sess["_pw_page"] = page
        return page

    def _extract_pw_state(self, page: Any, sess: Dict[str, Any], *, http_status: Optional[int] = None) -> None:
        url = page.url or sess.get("url", "about:blank")
        try:
            title = page.title() or url
        except Exception:
            title = url
        extracted: Dict[str, Any] = {}
        try:
            extracted = page.evaluate(
                """() => {
                  const text = (document.body && (document.body.innerText || document.body.textContent)) || '';
                  const links = Array.from(document.querySelectorAll('a[href]'))
                    .map(a => ({
                      text: (a.innerText || a.getAttribute('aria-label') || a.href || '').trim().slice(0, 90),
                      href: a.href
                    }))
                    .filter(l => /^https?:\\/\\//i.test(l.href))
                    .slice(0, 60);
                  const interactive = Array.from(document.querySelectorAll('a[href], button, input, textarea, select'))
                    .filter(el => {
                      const r = el.getBoundingClientRect();
                      return r.width > 0 && r.height > 0;
                    })
                    .slice(0, 50)
                    .map((el, idx) => {
                      const tag = el.tagName.toLowerCase();
                      const r = el.getBoundingClientRect();
                      const idSel = el.id ? '#' + CSS.escape(el.id) : '';
                      const nameSel = (!idSel && el.getAttribute('name')) ? `${tag}[name="${el.getAttribute('name')}"]` : '';
                      const lbl = (el.innerText || el.getAttribute('aria-label') || el.getAttribute('placeholder') || el.value || el.href || tag).trim().slice(0, 80);
                      return {
                        ref: `@e${idx + 1}`,
                        tag,
                        type: el.getAttribute('type') || (tag === 'a' ? 'link' : tag),
                        label: lbl,
                        selector: idSel || nameSel || tag,
                        x: Math.round(r.left + r.width / 2),
                        y: Math.round(r.top + r.height / 2),
                        href: tag === 'a' ? el.href : undefined
                      };
                    });
                  return { text: text.slice(0, 20000), links, elements: interactive };
                }"""
            ) or {}
        except Exception:
            extracted = {}

        try:
            png = page.screenshot(type="png", full_page=False)
            b64 = base64.b64encode(png).decode("ascii")
        except Exception:
            b64 = ""

        sess["url"] = url
        sess["title"] = title
        if http_status is not None:
            sess["status"] = http_status
        sess["engine"] = "playwright"
        sess["text"] = str(extracted.get("text") or "").strip()
        sess["links"] = extracted.get("links") or []
        sess["elements"] = extracted.get("elements") or []
        sess["screenshot_b64"] = b64
        sess["updated_at"] = time.time()

    def _record_history(self, sess: Dict[str, Any], url: str) -> None:
        hist = sess.setdefault("history", [])
        idx = sess.get("history_idx", -1)
        if idx >= 0 and idx < len(hist) and hist[idx] == url:
            return
        if idx < len(hist) - 1:
            hist = hist[: idx + 1]
        hist.append(url)
        sess["history"] = hist[-50:]
        sess["history_idx"] = len(sess["history"]) - 1

    def _reader_fetch(self, url: str) -> Dict[str, Any]:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": DEFAULT_USER_AGENT, "Accept": "text/html,application/xhtml+xml,*/*;q=0.9"},
            method="GET",
        )
        status_code = 200
        ctype = ""
        final_url = url
        with urllib.request.urlopen(req, timeout=20.0) as resp:
            status_code = int(getattr(resp, "status", 200) or 200)
            final_url = resp.geturl() or url
            ctype = str(resp.headers.get("Content-Type") or "").lower()
            raw = resp.read(1_500_000)

        decoded = raw.decode("utf-8", errors="replace")
        if "html" in ctype or "<html" in decoded[:512].lower() or "<!doctype" in decoded[:512].lower():
            parser = _SimpleReaderHTMLParser(base_url=final_url)
            parser.feed(decoded)
            parser.close()
            parsed = parser.result()
        else:
            parsed = {
                "title": final_url,
                "text": decoded[:20000],
                "links": [],
                "elements": [],
            }
        parsed["status"] = status_code
        parsed["url"] = final_url
        parsed["raw_html"] = decoded if "html" in ctype else ""
        return parsed

    def navigate(
        self,
        url: str,
        *,
        session_id: Optional[str] = None,
        reader_only: bool = False,
        wait_until: str = "domcontentloaded",
    ) -> Dict[str, Any]:
        clean_url = normalize_and_validate_url(url, allow_private=self.allow_private)
        sess = self._get_or_create_session(session_id)

        pw_ok, _ = self._worker.is_available() if (self.prefer_playwright and not reader_only) else (False, "disabled")
        if pw_ok:
            def _do_nav(browser: Any) -> int:
                page = self._ensure_pw_page(browser, sess)
                resp = page.goto(clean_url, wait_until=wait_until, timeout=25000)
                try:
                    page.wait_for_timeout(350)
                except Exception:
                    pass
                status_val = int(resp.status) if resp and resp.status else 200
                self._extract_pw_state(page, sess, http_status=status_val)
                return status_val

            try:
                self._worker.run(_do_nav, timeout=35.0)
                self._record_history(sess, sess["url"])
                return self._public_snapshot(sess)
            except Exception as pw_err:
                sess.setdefault("console_logs", []).append(f"[playwright-fallback] {pw_err}"[:200])

        # Fallback: direct HTTP Reader fetch
        fetched = self._reader_fetch(clean_url)
        sess["url"] = fetched["url"]
        sess["title"] = fetched["title"] or fetched["url"]
        sess["status"] = fetched["status"]
        sess["engine"] = "reader"
        sess["text"] = fetched["text"]
        sess["links"] = fetched["links"]
        sess["elements"] = fetched["elements"]
        sess["screenshot_b64"] = base64.b64encode(_encode_solid_png()).decode("ascii")
        sess["updated_at"] = time.time()
        self._record_history(sess, sess["url"])
        return self._public_snapshot(sess)

    def action(
        self,
        session_id: str,
        act: str,
        *,
        selector: Optional[str] = None,
        x: Optional[float] = None,
        y: Optional[float] = None,
        text: Optional[str] = None,
        key: Optional[str] = None,
        delta_y: float = 480.0,
        script: Optional[str] = None,
        full_page: bool = False,
    ) -> Dict[str, Any]:
        sess = self._get_or_create_session(session_id)
        act_name = (act or "").strip().lower()

        if act_name == "back":
            idx = sess.get("history_idx", -1)
            hist = sess.get("history") or []
            if idx > 0:
                sess["history_idx"] = idx - 1
                return self.navigate(hist[idx - 1], session_id=session_id, reader_only=(sess.get("engine") == "reader"))
            return self._public_snapshot(sess)

        if act_name == "forward":
            idx = sess.get("history_idx", -1)
            hist = sess.get("history") or []
            if 0 <= idx < len(hist) - 1:
                sess["history_idx"] = idx + 1
                return self.navigate(hist[idx + 1], session_id=session_id, reader_only=(sess.get("engine") == "reader"))
            return self._public_snapshot(sess)

        if act_name == "reload":
            target = sess.get("url") or "about:blank"
            if target != "about:blank":
                return self.navigate(target, session_id=session_id, reader_only=(sess.get("engine") == "reader"))
            return self._public_snapshot(sess)

        pw_ok, _ = self._worker.is_available() if self.prefer_playwright else (False, "disabled")
        if not pw_ok or sess.get("_pw_page") is None:
            # In reader fallback mode, clicking a link element navigates cleanly
            if act_name in ("click", "click_xy") and selector:
                for el in sess.get("elements") or []:
                    if el.get("ref") == selector or el.get("selector") == selector:
                        if el.get("href"):
                            return self.navigate(el["href"], session_id=session_id, reader_only=True)
            return {**self._public_snapshot(sess), "note": f"Action '{act_name}' requires Chromium engine; active mode is {sess.get('engine')}."}

        # Resolve @eN reference to selector/coordinates if given
        resolved_sel = selector
        resolved_x, resolved_y = x, y
        if selector and selector.startswith("@e"):
            for el in sess.get("elements") or []:
                if el.get("ref") == selector:
                    resolved_sel = el.get("selector") or selector
                    if resolved_x is None:
                        resolved_x = el.get("x")
                    if resolved_y is None:
                        resolved_y = el.get("y")
                    break

        def _do_act(browser: Any) -> Dict[str, Any]:
            page = self._ensure_pw_page(browser, sess)
            eval_result: Any = None
            if act_name == "click_xy" and resolved_x is not None and resolved_y is not None:
                page.mouse.click(float(resolved_x), float(resolved_y))
            elif act_name == "click":
                if resolved_x is not None and resolved_y is not None and (selector or "").startswith("@e"):
                    page.mouse.click(float(resolved_x), float(resolved_y))
                elif resolved_sel:
                    page.locator(resolved_sel).first.click(timeout=10000)
                elif resolved_x is not None and resolved_y is not None:
                    page.mouse.click(float(resolved_x), float(resolved_y))
            elif act_name in ("fill", "type") and text is not None:
                if resolved_sel and act_name == "fill":
                    page.locator(resolved_sel).first.fill(str(text), timeout=10000)
                elif resolved_sel:
                    page.locator(resolved_sel).first.click(timeout=10000)
                    page.keyboard.type(str(text))
                else:
                    page.keyboard.type(str(text))
            elif act_name == "press" and key:
                page.keyboard.press(str(key))
            elif act_name == "scroll":
                page.mouse.wheel(0, float(delta_y))
            elif act_name == "eval" and script:
                eval_result = page.evaluate(str(script))
            elif act_name == "screenshot":
                png = page.screenshot(type="png", full_page=bool(full_page))
                sess["screenshot_b64"] = base64.b64encode(png).decode("ascii")
            try:
                page.wait_for_timeout(300)
            except Exception:
                pass
            self._extract_pw_state(page, sess)
            if act_name == "screenshot" and full_page:
                png = page.screenshot(type="png", full_page=True)
                sess["screenshot_b64"] = base64.b64encode(png).decode("ascii")
            self._record_history(sess, sess["url"])
            return {"eval_result": eval_result}

        extra = self._worker.run(_do_act, timeout=35.0)
        snap = self._public_snapshot(sess)
        if extra.get("eval_result") is not None:
            snap["eval_result"] = extra["eval_result"]
        return snap

    def get_state(self, session_id: str, *, include_screenshot: bool = True) -> Dict[str, Any]:
        sess = self._get_or_create_session(session_id)
        return self._public_snapshot(sess, include_screenshot=include_screenshot)

    def save_to_space(
        self,
        session_id: str,
        space_manager: Any,
        *,
        scope: str = "user",
        owner_id: str = "default",
        peer_id: str = "browser",
        kind: str = "markdown",
        save_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        sess = self._get_or_create_session(session_id)
        sp = space_manager.get_or_create_space(scope, owner_id)
        slug = _slug_from_url(sess.get("url") or "page")

        if kind == "screenshot":
            b64 = sess.get("screenshot_b64") or ""
            raw = base64.b64decode(b64) if b64 else _encode_solid_png()
            target = save_path or f"/images/web_{slug}.png"
            sp.write_file(target, raw, mime_type="image/png", updated_by=peer_id)
            return {"ok": True, "path": target, "mime_type": "image/png", "size_bytes": len(raw)}

        # Markdown / clean reader dump
        target = save_path or f"/notes/web_{slug}.md"
        links_md = "\n".join(f"- [{l.get('text') or l.get('href')}]({l.get('href')})" for l in (sess.get("links") or [])[:25])
        md = (
            f"# {sess.get('title') or 'Web Capture'}\n\n"
            f"- **URL:** {sess.get('url')}\n"
            f"- **Engine:** {sess.get('engine')}\n"
            f"- **Status:** {sess.get('status')}\n\n"
            f"## Extracted Content\n\n{sess.get('text') or '(empty)'}\n\n"
            + (f"## Links\n\n{links_md}\n" if links_md else "")
        )
        sp.write_file(target, md, mime_type="text/markdown", updated_by=peer_id)
        return {"ok": True, "path": target, "mime_type": "text/markdown", "size_bytes": len(md.encode("utf-8"))}

    def fetch_reader_proxy(self, url: str) -> Dict[str, Any]:
        clean = normalize_and_validate_url(url, allow_private=self.allow_private)
        fetched = self._reader_fetch(clean)
        return {
            "ok": True,
            "url": fetched["url"],
            "title": fetched["title"],
            "status": fetched["status"],
            "text": fetched["text"],
            "links": fetched["links"],
            "elements": fetched["elements"],
        }

    def close_session(self, session_id: str) -> bool:
        with self._lock:
            sess = self._sessions.pop(session_id, None)
        if not sess:
            return False
        ctx = sess.get("_pw_context")
        if ctx is not None:
            try:
                self._worker.run(lambda _b: ctx.close(), timeout=10.0)
            except Exception:
                pass
        return True
