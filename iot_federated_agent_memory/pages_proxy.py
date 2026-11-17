"""GitHub-Pages-style `.space` static/build site hosting (`/pages/...`) and localhost port proxy (`/localhost/<port>/...`).

Allows builds/files written inside `.space` (e.g. `/index.html`, `/dist/index.html`, `/models3d/pikachu_walk.html`)
or local sandbox dev servers (`127.0.0.1:5173`, `:3000`, `:8080`) to be accessed cleanly on live relative URLs.
"""

from __future__ import annotations

import base64
import html as _html
import posixpath
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from .file_inspector import guess_mime_type

_EXPLICIT_SCOPES = frozenset({"user", "topic", "project", "peer"})
_HOP_BY_HOP_HEADERS = frozenset({
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "content-length", "x-frame-options",
})


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        return None


_NO_REDIRECT_OPENER = urllib.request.build_opener(_NoRedirectHandler())


def _safe_posix_subpath(parts: List[str]) -> str:
    joined = "/".join(urllib.parse.unquote(p) for p in parts if p)
    if not joined:
        return "/"
    norm = posixpath.normpath("/" + joined)
    if not norm.startswith("/"):
        norm = "/" + norm
    return norm


def resolve_pages_route(raw_path: str) -> Tuple[Optional[str], Optional[str], Optional[str], str, bool]:
    """Parse `/pages/...` or `/site/...` into `(redirect_to, scope, owner_id, subpath, trailing_slash)`."""
    prefix = "/pages" if raw_path.startswith("/pages") else ("/site" if raw_path.startswith("/site") else "")
    if not prefix:
        return None, None, None, "/", False
    rest = raw_path[len(prefix) :]
    trailing_slash = raw_path.endswith("/")
    parts = [p for p in rest.split("/") if p]
    if not parts:
        return None, None, None, "/", True

    if parts[0] in _EXPLICIT_SCOPES:
        if len(parts) < 2:
            return None, None, None, "/", True
        scope = parts[0]
        owner_id = urllib.parse.unquote(parts[1])
        rel_parts = parts[2:]
        if not rel_parts and not trailing_slash:
            return f"{prefix}/{scope}/{urllib.parse.quote(owner_id, safe='')}/", scope, owner_id, "/", True
    else:
        scope = "user"
        owner_id = urllib.parse.unquote(parts[0])
        rel_parts = parts[1:]
        if not rel_parts and not trailing_slash:
            return f"{prefix}/user/{urllib.parse.quote(owner_id, safe='')}/", scope, owner_id, "/", True

    return None, scope, owner_id, _safe_posix_subpath(rel_parts), trailing_slash


def list_space_page_entrypoints(sp: Any, scope: str, owner_id: str) -> Dict[str, Any]:
    """List navigable HTML pages and common build roots inside a `.space` VFS."""
    files = sp.list_files() or []
    paths = sorted(str(f.get("path") or "") for f in files if f.get("path"))
    priority = [
        "/index.html", "/index.htm", "/dist/index.html",
        "/build/index.html", "/public/index.html", "/docs/index.html",
    ]
    seen = set()
    entries: List[Dict[str, str]] = []
    base_url = f"/pages/{urllib.parse.quote(scope, safe='')}/{urllib.parse.quote(owner_id, safe='')}"

    for p in priority:
        if p in paths:
            seen.add(p)
            entries.append({"path": p, "label": f"{p} (build entry)", "url": base_url + p})
    for p in paths:
        if p not in seen and p.lower().endswith((".html", ".htm")):
            seen.add(p)
            entries.append({"path": p, "label": p, "url": base_url + p})
    entries.append({"path": "/", "label": "/ (directory / auto index)", "url": base_url + "/"})

    default_path = entries[0]["path"] if entries else "/"
    return {
        "ok": True,
        "scope": scope,
        "owner_id": owner_id,
        "base_url": base_url + "/",
        "default_path": default_path,
        "merkle_root": sp.compute_merkle_root() if hasattr(sp, "compute_merkle_root") else "",
        "entrypoints": entries,
    }


def _render_directory_html(scope: str, owner_id: str, dir_path: str, files: List[Dict[str, Any]]) -> bytes:
    prefix = "/" if dir_path == "/" else dir_path.rstrip("/") + "/"
    base_url = f"/pages/{urllib.parse.quote(scope, safe='')}/{urllib.parse.quote(owner_id, safe='')}"
    subdirs = set()
    direct_files: List[Dict[str, Any]] = []
    for f in files:
        p = str(f.get("path") or "")
        if not p.startswith(prefix):
            continue
        rem = p[len(prefix) :]
        if "/" in rem:
            subdirs.add(rem.split("/", 1)[0])
        elif rem:
            direct_files.append({"name": rem, "path": p, "size": int(f.get("size_bytes") or 0)})

    rows: List[str] = []
    if dir_path != "/":
        parent = posixpath.dirname(dir_path.rstrip("/")) or "/"
        parent_href = base_url + ("/" if parent == "/" else parent + "/")
        rows.append(f'<li><a href="{_html.escape(parent_href)}">.. (parent directory)</a></li>')
    for d in sorted(subdirs):
        href = base_url + prefix + urllib.parse.quote(d) + "/"
        rows.append(f'<li><span>DIR</span> <a href="{_html.escape(href)}">{_html.escape(d)}/</a></li>')
    for f in sorted(direct_files, key=lambda x: x["name"].lower()):
        href = base_url + f["path"]
        rows.append(
            f'<li><span>{f["size"]:,} B</span> <a href="{_html.escape(href)}">{_html.escape(f["name"])}</a></li>'
        )
    if not rows:
        rows.append("<li><em>Empty directory — write index.html or /dist/index.html into .space to publish here.</em></li>")

    doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Index of {_html.escape(dir_path)}</title>
<style>
  body{{font-family:-apple-system,BlinkMacSystemFont,"Inter",sans-serif;background:#FAFAFA;color:#111;max-width:760px;margin:36px auto;padding:0 20px}}
  h1{{font-size:16px;font-family:ui-monospace,Menlo,monospace;border-bottom:1px solid rgba(17,17,17,.14);padding-bottom:8px}}
  .meta{{font-size:12px;color:#5A5F66;margin-bottom:16px;font-family:ui-monospace,Menlo,monospace}}
  ul{{list-style:none;padding:0;margin:0;border:1px solid rgba(17,17,17,.14);border-radius:8px;background:#fff}}
  li{{display:flex;justify-content:space-between;gap:12px;padding:8px 12px;border-bottom:1px solid rgba(17,17,17,.08);font-family:ui-monospace,Menlo,monospace;font-size:12px}}
  li:last-child{{border-bottom:0}}
  a{{color:#047857;text-decoration:none;font-weight:600}} a:hover{{text-decoration:underline}}
  span{{color:#5A5F66;font-size:11px}}
</style></head><body>
<h1>Index of {_html.escape(dir_path)}</h1>
<div class="meta">TinCan .space Pages (gh-pages route) · scope={_html.escape(scope)} · owner={_html.escape(owner_id)}</div>
<ul>{"".join(rows)}</ul></body></html>"""
    return doc.encode("utf-8")


def _send_bytes(handler: Any, status: int, body: bytes, content_type: str, *, send_body: bool = True) -> None:
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    if send_body and body:
        handler.wfile.write(body)


def serve_space_pages(handler: Any, sm: Any, raw_path: str) -> None:
    """Serve `.space` VFS websites on `/pages/<scope>/<owner_id>/<subpath...>` like GitHub Pages."""
    redirect_to, scope, owner_id, subpath, trailing_slash = resolve_pages_route(raw_path)
    is_head = getattr(handler, "command", "GET") == "HEAD"
    if redirect_to:
        handler.send_response(302)
        handler.send_header("Location", redirect_to)
        handler.send_header("Content-Length", "0")
        handler.end_headers()
        return

    if not scope or not owner_id:
        landing = (
            "<!DOCTYPE html><html><body style='font-family:sans-serif;max-width:680px;margin:40px auto;padding:0 16px'>"
            "<h2>TinCan .space Pages</h2>"
            "<p>Open <code>/pages/user/&lt;owner_id&gt;/</code> (or <code>/pages/&lt;owner_id&gt;/</code>) to view published HTML/JS/CSS/3D builds straight from your .space.</p>"
            "<p><a href='/pages/user/default/'>Open default user Pages →</a></p></body></html>"
        ).encode("utf-8")
        _send_bytes(handler, 200, landing, "text/html; charset=utf-8", send_body=not is_head)
        return

    sp = sm.get_or_create_space(scope, owner_id)
    candidates: List[str] = []
    if subpath == "/":
        candidates = ["/index.html", "/index.htm", "/dist/index.html", "/build/index.html", "/public/index.html", "/docs/index.html"]
    elif trailing_slash:
        base = subpath.rstrip("/")
        candidates = [f"{base}/index.html", f"{base}/index.htm"]
    else:
        candidates = [subpath, f"{subpath}/index.html", f"{subpath}.html"]

    for cand in candidates:
        try:
            rec = sp.read_file(cand, as_text=False)
        except FileNotFoundError:
            continue
        # If `/sub` matched `/sub/index.html`, redirect once to `/sub/` so relative assets resolve cleanly
        if cand == f"{subpath}/index.html" and not trailing_slash and subpath != "/":
            handler.send_response(302)
            handler.send_header("Location", raw_path + "/")
            handler.send_header("Content-Length", "0")
            handler.end_headers()
            return
        raw_bytes = base64.b64decode(rec.get("content_b64") or "")
        ctype = guess_mime_type(cand, rec.get("mime_type") or "")
        _send_bytes(handler, 200, raw_bytes, ctype, send_body=not is_head)
        return

    files = sp.list_files() or []
    dir_prefix = "/" if subpath == "/" else subpath.rstrip("/") + "/"
    if subpath == "/" or any(str(f.get("path") or "").startswith(dir_prefix) for f in files):
        if subpath != "/" and not trailing_slash:
            handler.send_response(302)
            handler.send_header("Location", raw_path + "/")
            handler.send_header("Content-Length", "0")
            handler.end_headers()
            return
        listing = _render_directory_html(scope, owner_id, subpath, files)
        _send_bytes(handler, 200, listing, "text/html; charset=utf-8", send_body=not is_head)
        return

    not_found = (
        f"<!DOCTYPE html><html><body style='font-family:monospace;padding:32px'>"
        f"<h3>404 — Not found in .space Pages</h3><p>Missing path: <code>{_html.escape(subpath)}</code></p>"
        f"<p><a href='/pages/{_html.escape(scope)}/{_html.escape(urllib.parse.quote(owner_id))}/'>← Back to Pages root</a></p>"
        f"</body></html>"
    ).encode("utf-8")
    _send_bytes(handler, 404, not_found, "text/html; charset=utf-8", send_body=not is_head)


def _rewrite_proxy_location(loc: str, port: int) -> str:
    prefix = f"/localhost/{port}"
    parsed = urllib.parse.urlparse(loc)
    if parsed.scheme in ("http", "https") and parsed.hostname in ("127.0.0.1", "localhost") and (parsed.port in (port, None)):
        tail = parsed.path or "/"
        if parsed.query:
            tail += "?" + parsed.query
        return prefix + (tail if tail.startswith("/") else "/" + tail)
    if loc.startswith("/") and not loc.startswith("//") and not loc.startswith(prefix + "/"):
        return prefix + loc
    return loc


def proxy_localhost_port(handler: Any, method: str, raw_path: str, query_str: str) -> None:
    """Reverse-proxy `/localhost/<port>/<subpath>` to `http://127.0.0.1:<port>/<subpath>`."""
    rest = raw_path[len("/localhost") :].lstrip("/")
    if not rest:
        _send_bytes(handler, 400, b"Specify /localhost/<port>/ (1024-65535).", "text/plain; charset=utf-8")
        return

    parts = rest.split("/", 1)
    port_str = parts[0]
    if not port_str.isdigit():
        _send_bytes(handler, 400, b"Invalid localhost port.", "text/plain; charset=utf-8")
        return
    port = int(port_str)
    if port < 1024 or port > 65535:
        _send_bytes(handler, 403, b"Only non-privileged ports 1024..65535 can be proxied.", "text/plain; charset=utf-8")
        return

    own_port = getattr(getattr(handler, "server", None), "server_port", None)
    if own_port and port == int(own_port):
        _send_bytes(handler, 508, b"Loop detected: cannot proxy TinCan's own listening port.", "text/plain; charset=utf-8")
        return

    has_sub = len(parts) > 1 or raw_path.endswith("/")
    if not has_sub and method in ("GET", "HEAD"):
        loc = f"/localhost/{port}/" + (f"?{query_str}" if query_str else "")
        handler.send_response(302)
        handler.send_header("Location", loc)
        handler.send_header("Content-Length", "0")
        handler.end_headers()
        return

    sub = parts[1] if len(parts) > 1 else ""
    target = f"http://127.0.0.1:{port}/{sub}"
    if query_str:
        target += f"?{query_str}"

    body_bytes: Optional[bytes] = None
    if method in ("POST", "PUT", "PATCH"):
        try:
            clen = int(handler.headers.get("Content-Length", 0))
        except ValueError:
            clen = 0
        if clen > 0:
            body_bytes = handler.rfile.read(clen)

    fwd_headers: Dict[str, str] = {}
    for hdr in ("Accept", "Content-Type", "Cookie", "Authorization", "Range"):
        val = handler.headers.get(hdr)
        if val:
            fwd_headers[hdr] = val

    req = urllib.request.Request(target, data=body_bytes, headers=fwd_headers, method=method)
    try:
        resp = _NO_REDIRECT_OPENER.open(req, timeout=12.0)
        status = resp.status
        resp_headers = list(resp.headers.items())
        payload = b"" if method == "HEAD" else resp.read()
    except urllib.error.HTTPError as he:
        status = he.code
        resp_headers = list(he.headers.items()) if he.headers else []
        payload = b"" if method == "HEAD" else he.read()
    except Exception as exc:
        offline_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Localhost :{port} Offline</title>
<style>
  body{{font-family:-apple-system,BlinkMacSystemFont,"Inter",sans-serif;background:#FAFAFA;color:#111;max-width:600px;margin:48px auto;padding:20px}}
  .card{{background:#fff;border:1px solid rgba(17,17,17,.14);border-radius:10px;padding:18px}}
  code{{background:#f0f2f0;padding:2px 6px;border-radius:4px;font-size:12px}}
  a{{color:#047857;font-weight:600;text-decoration:none}}
</style></head><body><div class="card">
<h3>Localhost :{port} is not listening</h3>
<p>Could not reach <code>http://127.0.0.1:{port}/</code> ({_html.escape(str(exc))}).</p>
<p>Start any dev server on port <code>{port}</code> inside Terminal (e.g. <code>python3 -m http.server {port}</code> or <code>npm run dev -- --port {port}</code>), or switch to <strong>.space Pages (gh-pages)</strong> to serve files built into <code>.space</code>.</p>
<p><a href="/pages/user/default/">Open .space Pages →</a></p>
</div></body></html>""".encode("utf-8")
        _send_bytes(handler, 502, offline_html, "text/html; charset=utf-8", send_body=(method != "HEAD"))
        return

    handler.send_response(status)
    has_ctype = False
    for k, v in resp_headers:
        kl = k.lower()
        if kl in _HOP_BY_HOP_HEADERS:
            continue
        if kl == "location":
            v = _rewrite_proxy_location(v, port)
        elif kl == "content-type":
            has_ctype = True
        handler.send_header(k, v)
    if not has_ctype:
        handler.send_header("Content-Type", guess_mime_type(sub or "index.html"))
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    if method != "HEAD" and payload:
        handler.wfile.write(payload)
