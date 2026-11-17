"""Universal stdlib file inspector, MIME resolver, and lightweight 3D/CAD/office previewer.

Handles every file category inside TinCan's Workstation Viewer & Pages static server:
- Accurate MIME types (.glb, .gltf, .obj, .stl, .ply, .svg, .webp, .woff2, .wasm, .pdf, etc.)
- Archives: .zip, .whl, .jar, .epub, .3mf, .tar, .tar.gz, .tgz, .gz
- Office docs: .docx, .xlsx, .pptx
- Databases: .sqlite, .sqlite3, .db, .space
- 3D meshes -> binary .glb conversion: .obj, .stl (ASCII & binary), .ply (ASCII)
- CAD wireframe extraction: .dxf
- Universal Hex + ASCII dump + magic-byte signature detection for arbitrary binary files
"""

from __future__ import annotations

import base64
import gzip
import hashlib
import io
import json
import mimetypes
import os
import posixpath
import re
import sqlite3
import struct
import tarfile
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from typing import Any, Dict, List, Optional, Tuple

from .glb_rigger import pack_glb

_EXTRA_MIMES: Dict[str, str] = {
    ".html": "text/html; charset=utf-8",
    ".htm": "text/html; charset=utf-8",
    ".xhtml": "application/xhtml+xml; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".mjs": "application/javascript; charset=utf-8",
    ".cjs": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".ipynb": "application/json; charset=utf-8",
    ".map": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".avif": "image/avif",
    ".ico": "image/x-icon",
    ".bmp": "image/bmp",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".ttf": "font/ttf",
    ".otf": "font/otf",
    ".wasm": "application/wasm",
    ".pdf": "application/pdf",
    ".glb": "model/gltf-binary",
    ".gltf": "model/gltf+json",
    ".obj": "text/plain; charset=utf-8",
    ".stl": "model/stl",
    ".ply": "text/plain; charset=utf-8",
    ".usdz": "model/vnd.usdz+zip",
    ".mp4": "video/mp4",
    ".m4v": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
    ".ogv": "video/ogg",
    ".mkv": "video/x-matroska",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".m4a": "audio/mp4",
    ".flac": "audio/flac",
    ".aac": "audio/aac",
    ".opus": "audio/opus",
    ".md": "text/markdown; charset=utf-8",
    ".markdown": "text/markdown; charset=utf-8",
    ".csv": "text/csv; charset=utf-8",
    ".tsv": "text/tab-separated-values; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".log": "text/plain; charset=utf-8",
    ".xml": "application/xml; charset=utf-8",
    ".yaml": "text/yaml; charset=utf-8",
    ".yml": "text/yaml; charset=utf-8",
    ".toml": "text/plain; charset=utf-8",
    ".py": "text/x-python; charset=utf-8",
    ".dxf": "application/dxf",
    ".fountain": "text/plain; charset=utf-8",
    ".zip": "application/zip",
    ".tar": "application/x-tar",
    ".gz": "application/gzip",
    ".tgz": "application/gzip",
    ".sqlite": "application/vnd.sqlite3",
    ".db": "application/vnd.sqlite3",
    ".space": "application/vnd.sqlite3",
}

_SIGNATURES: List[Tuple[bytes, str]] = [
    (b"glTF", "glTF 2.0 Binary (.glb)"),
    (b"%PDF-", "PDF Document"),
    (b"\x89PNG\r\n\x1a\n", "PNG Image"),
    (b"\xff\xd8\xff", "JPEG Image"),
    (b"GIF8", "GIF Image"),
    (b"PK\x03\x04", "ZIP / Office OpenXML Archive"),
    (b"\x1f\x8b", "Gzip Compressed Stream"),
    (b"SQLite format 3\x00", "SQLite 3 Database"),
    (b"\x00asm", "WebAssembly Binary (.wasm)"),
    (b"\x7fELF", "ELF Executable / Shared Object"),
    (b"\xcf\xfa\xed\xfe", "Mach-O 64-bit Binary"),
    (b"MZ", "PE / DOS Executable"),
    (b"RIFF", "RIFF Media (WAV / WebP / AVI)"),
    (b"ID3", "MP3 Audio (ID3 Tag)"),
    (b"\x93NUMPY", "NumPy Array (.npy)"),
]


def guess_mime_type(path: str, stored_mime: str = "") -> str:
    """Resolve an accurate MIME type from extension before falling back to stored/stdlib."""
    ext = posixpath.splitext((path or "").strip().lower())[1]
    if ext in _EXTRA_MIMES:
        return _EXTRA_MIMES[ext]
    if stored_mime and stored_mime != "application/octet-stream":
        return stored_mime
    guessed = mimetypes.guess_type(path or "")[0]
    return guessed or "application/octet-stream"


def detect_magic_signature(raw: bytes) -> str:
    """Identify binary header signature if recognized."""
    for sig, label in _SIGNATURES:
        if raw.startswith(sig):
            return label
    if len(raw) > 265 and raw[257:262] == b"ustar":
        return "POSIX Tar Archive"
    return "Raw Binary Stream"


def format_hex_dump(raw: bytes, *, max_bytes: int = 4096) -> str:
    """Return classic offset + 16-byte hex + ASCII inspector text."""
    view = raw[:max_bytes]
    lines: List[str] = []
    for off in range(0, len(view), 16):
        chunk = view[off : off + 16]
        left = " ".join(f"{b:02x}" for b in chunk[:8])
        right = " ".join(f"{b:02x}" for b in chunk[8:])
        hex_col = f"{left:<23}  {right:<23}"
        ascii_col = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{off:08x}  {hex_col}  |{ascii_col}|")
    if len(raw) > max_bytes:
        lines.append(f"... ({len(raw) - max_bytes:,} more bytes; download file for full binary)")
    return "\n".join(lines)


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _col_letters_to_idx(ref: str) -> int:
    idx = 0
    for ch in ref:
        if "A" <= ch <= "Z":
            idx = idx * 26 + (ord(ch) - ord("A") + 1)
        elif ch.isdigit():
            break
    return max(0, idx - 1)


def _inspect_office_zip(zf: zipfile.ZipFile, ext: str) -> Optional[Dict[str, Any]]:
    names = set(zf.namelist())
    if ext == ".docx" or "word/document.xml" in names:
        xml_bytes = zf.read("word/document.xml")
        root = ET.fromstring(xml_bytes)
        paragraphs: List[str] = []
        for p in root.iter():
            if _strip_ns(p.tag) == "p":
                txt = "".join(el.text or "" for el in p.iter() if _strip_ns(el.tag) == "t").strip()
                if txt:
                    paragraphs.append(txt)
        return {"kind": "docx", "paragraphs": paragraphs[:400], "total_paragraphs": len(paragraphs)}

    if ext == ".xlsx" or "xl/workbook.xml" in names:
        shared: List[str] = []
        if "xl/sharedStrings.xml" in names:
            sroot = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in sroot:
                if _strip_ns(si.tag) == "si":
                    shared.append("".join(t.text or "" for t in si.iter() if _strip_ns(t.tag) == "t"))
        sheet_names: List[str] = []
        if "xl/workbook.xml" in names:
            wroot = ET.fromstring(zf.read("xl/workbook.xml"))
            for sh in wroot.iter():
                if _strip_ns(sh.tag) == "sheet" and sh.attrib.get("name"):
                    sheet_names.append(sh.attrib["name"])
        sheet_paths = sorted(n for n in names if re.match(r"^xl/worksheets/sheet\d+\.xml$", n))
        sheets: List[Dict[str, Any]] = []
        for idx, spath in enumerate(sheet_paths[:10]):
            sroot = ET.fromstring(zf.read(spath))
            rows: List[List[str]] = []
            for row_el in sroot.iter():
                if _strip_ns(row_el.tag) != "row":
                    continue
                row_vals: Dict[int, str] = {}
                max_col = -1
                for c in row_el:
                    if _strip_ns(c.tag) != "c":
                        continue
                    col_idx = _col_letters_to_idx(c.attrib.get("r", "A1"))
                    ctype = c.attrib.get("t", "")
                    val_txt = ""
                    v_el = next((ch for ch in c if _strip_ns(ch.tag) == "v"), None)
                    is_el = next((ch for ch in c if _strip_ns(ch.tag) == "is"), None)
                    if is_el is not None:
                        val_txt = "".join(t.text or "" for t in is_el.iter() if _strip_ns(t.tag) == "t")
                    elif v_el is not None and v_el.text is not None:
                        if ctype == "s":
                            try:
                                val_txt = shared[int(v_el.text)]
                            except Exception:
                                val_txt = v_el.text
                        elif ctype == "b":
                            val_txt = "TRUE" if v_el.text == "1" else "FALSE"
                        else:
                            val_txt = v_el.text
                    row_vals[col_idx] = val_txt
                    max_col = max(max_col, col_idx)
                if max_col >= 0:
                    rows.append([row_vals.get(ci, "") for ci in range(min(max_col + 1, 40))])
                if len(rows) >= 200:
                    break
            sname = sheet_names[idx] if idx < len(sheet_names) else os.path.basename(spath)
            sheets.append({"name": sname, "rows": rows})
        return {"kind": "xlsx", "sheets": sheets}

    if ext == ".pptx" or any(re.match(r"^ppt/slides/slide\d+\.xml$", n) for n in names):
        slide_paths = sorted(
            (n for n in names if re.match(r"^ppt/slides/slide\d+\.xml$", n)),
            key=lambda p: int(re.search(r"(\d+)\.xml$", p).group(1)),  # type: ignore[union-attr]
        )
        slides: List[Dict[str, Any]] = []
        for spath in slide_paths[:60]:
            m = re.search(r"(\d+)\.xml$", spath)
            snum = int(m.group(1)) if m else len(slides) + 1
            sroot = ET.fromstring(zf.read(spath))
            texts: List[str] = []
            for p in sroot.iter():
                if _strip_ns(p.tag) == "p":
                    line = "".join(t.text or "" for t in p.iter() if _strip_ns(t.tag) == "t").strip()
                    if line:
                        texts.append(line)
            slides.append({"slide": snum, "texts": texts})
        return {"kind": "pptx", "slides": slides}

    if ext == ".odt" or "content.xml" in names:
        root = ET.fromstring(zf.read("content.xml"))
        paras = [
            "".join(el.itertext()).strip()
            for el in root.iter()
            if _strip_ns(el.tag) in ("p", "h")
        ]
        paras = [p for p in paras if p]
        return {"kind": "docx", "paragraphs": paras[:400], "total_paragraphs": len(paras)}

    return None


def _inspect_sqlite(raw: bytes) -> Dict[str, Any]:
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tf:
        tf.write(raw)
        tmp_path = tf.name
    try:
        conn = sqlite3.connect(f"file:{tmp_path}?mode=ro", uri=True)
        cur = conn.execute(
            "SELECT name, type, sql FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        tables: List[Dict[str, Any]] = []
        for tname, ttype, tsql in cur.fetchall()[:40]:
            qname = '"' + tname.replace('"', '""') + '"'
            try:
                cnt = int(conn.execute(f"SELECT COUNT(*) FROM {qname}").fetchone()[0])
            except Exception:
                cnt = 0
            try:
                rows_cur = conn.execute(f"SELECT * FROM {qname} LIMIT 25")
                cols = [d[0] for d in (rows_cur.description or [])]
                sample = [
                    [
                        (f"<{len(v)} bytes>" if isinstance(v, (bytes, bytearray)) else v)
                        for v in row
                    ]
                    for row in rows_cur.fetchall()
                ]
            except Exception:
                cols, sample = [], []
            tables.append({
                "name": tname,
                "type": ttype,
                "row_count": cnt,
                "columns": cols,
                "rows": sample,
                "sql": tsql or "",
            })
        conn.close()
        return {"kind": "sqlite", "tables": tables}
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def mesh_bytes_to_glb(raw: bytes, ext: str) -> bytes:
    """Convert .obj, .stl (binary or ASCII), or ASCII .ply into a valid binary .glb for model-viewer."""
    norm_ext = ("." + ext.lstrip(".")).lower()
    positions: List[Tuple[float, float, float]] = []
    normals: List[Tuple[float, float, float]] = []
    indices: List[int] = []

    if norm_ext == ".obj":
        txt = raw.decode("utf-8", errors="replace")
        raw_verts: List[Tuple[float, float, float]] = []
        for line in txt.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if parts[0] == "v" and len(parts) >= 4:
                raw_verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
            elif parts[0] == "f" and len(parts) >= 4:
                f_idx: List[int] = []
                for tok in parts[1:]:
                    v_str = tok.split("/")[0]
                    vi = int(v_str)
                    vi = (len(raw_verts) + vi) if vi < 0 else (vi - 1)
                    if 0 <= vi < len(raw_verts):
                        f_idx.append(vi)
                for k in range(1, len(f_idx) - 1):
                    positions.extend([raw_verts[f_idx[0]], raw_verts[f_idx[k]], raw_verts[f_idx[k + 1]]])
        if not positions and raw_verts:
            positions = raw_verts

    elif norm_ext == ".stl":
        is_ascii = raw.lstrip().lower().startswith(b"solid") and b"facet" in raw[:4096].lower()
        if not is_ascii and len(raw) >= 84:
            tri_count = struct.unpack_from("<I", raw, 80)[0]
            if 84 + tri_count * 50 <= len(raw):
                off = 84
                for _ in range(min(tri_count, 250000)):
                    nx, ny, nz = struct.unpack_from("<3f", raw, off)
                    v1 = struct.unpack_from("<3f", raw, off + 12)
                    v2 = struct.unpack_from("<3f", raw, off + 24)
                    v3 = struct.unpack_from("<3f", raw, off + 36)
                    positions.extend([v1, v2, v3])
                    normals.extend([(nx, ny, nz)] * 3)
                    off += 50
            else:
                is_ascii = True
        if is_ascii:
            txt = raw.decode("utf-8", errors="replace")
            cur_n = (0.0, 1.0, 0.0)
            tri: List[Tuple[float, float, float]] = []
            for line in txt.splitlines():
                p = line.strip().split()
                if len(p) >= 5 and p[0].lower() == "facet" and p[1].lower() == "normal":
                    cur_n = (float(p[2]), float(p[3]), float(p[4]))
                elif len(p) >= 4 and p[0].lower() == "vertex":
                    tri.append((float(p[1]), float(p[2]), float(p[3])))
                    if len(tri) == 3:
                        positions.extend(tri)
                        normals.extend([cur_n] * 3)
                        tri = []

    elif norm_ext == ".ply":
        head_end = raw.find(b"end_header")
        if head_end < 0:
            raise ValueError("Invalid PLY header")
        header = raw[:head_end].decode("ascii", errors="replace")
        if "ascii" not in header.lower():
            raise ValueError("Only ASCII .ply conversion is supported inline; hex preview available.")
        nl = raw.find(b"\n", head_end)
        body_lines = raw[nl + 1 :].decode("utf-8", errors="replace").splitlines()
        n_verts = 0
        n_faces = 0
        for hline in header.splitlines():
            hp = hline.strip().split()
            if len(hp) >= 3 and hp[0] == "element":
                if hp[1] == "vertex":
                    n_verts = int(hp[2])
                elif hp[1] == "face":
                    n_faces = int(hp[2])
        raw_verts = []
        idx_cursor = 0
        for line in body_lines:
            if len(raw_verts) >= n_verts:
                break
            p = line.strip().split()
            if len(p) >= 3:
                raw_verts.append((float(p[0]), float(p[1]), float(p[2])))
            idx_cursor += 1
        for line in body_lines[idx_cursor : idx_cursor + n_faces]:
            p = line.strip().split()
            if not p:
                continue
            cnt = int(p[0])
            f_idx = [int(x) for x in p[1 : 1 + cnt] if 0 <= int(x) < len(raw_verts)]
            for k in range(1, len(f_idx) - 1):
                positions.extend([raw_verts[f_idx[0]], raw_verts[f_idx[k]], raw_verts[f_idx[k + 1]]])
    else:
        raise ValueError(f"Unsupported 3D conversion extension: {norm_ext}")

    if not positions:
        raise ValueError(f"No triangles or vertices found in {norm_ext} mesh.")

    if len(normals) != len(positions):
        normals = []
        for i in range(0, len(positions) - 2, 3):
            a, b, c = positions[i], positions[i + 1], positions[i + 2]
            ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
            vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
            nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            mag = (nx * nx + ny * ny + nz * nz) ** 0.5 or 1.0
            n = (nx / mag, ny / mag, nz / mag)
            normals.extend([n, n, n])
        while len(normals) < len(positions):
            normals.append((0.0, 1.0, 0.0))

    indices = list(range(len(positions)))
    pos_b = b"".join(struct.pack("<3f", *p) for p in positions)
    nrm_b = b"".join(struct.pack("<3f", *n) for n in normals)
    idx_b = b"".join(struct.pack("<I", i) for i in indices)

    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]
    zs = [p[2] for p in positions]
    blob = bytearray(pos_b)
    nrm_off = len(blob)
    blob.extend(nrm_b)
    idx_off = len(blob)
    blob.extend(idx_b)

    gltf: Dict[str, Any] = {
        "asset": {"version": "2.0", "generator": "tincan-mesh-converter"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": "ConvertedMesh", "mesh": 0}],
        "meshes": [
            {
                "primitives": [
                    {
                        "attributes": {"POSITION": 0, "NORMAL": 1},
                        "indices": 2,
                        "material": 0,
                    }
                ]
            }
        ],
        "materials": [
            {
                "pbrMetallicRoughness": {
                    "baseColorFactor": [0.85, 0.88, 0.90, 1.0],
                    "metallicFactor": 0.1,
                    "roughnessFactor": 0.55,
                }
            }
        ],
        "buffers": [{"byteLength": len(blob)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(pos_b), "target": 34962},
            {"buffer": 0, "byteOffset": nrm_off, "byteLength": len(nrm_b), "target": 34962},
            {"buffer": 0, "byteOffset": idx_off, "byteLength": len(idx_b), "target": 34963},
        ],
        "accessors": [
            {
                "bufferView": 0, "componentType": 5126, "count": len(positions), "type": "VEC3",
                "min": [min(xs), min(ys), min(zs)], "max": [max(xs), max(ys), max(zs)],
            },
            {"bufferView": 1, "componentType": 5126, "count": len(normals), "type": "VEC3"},
            {"bufferView": 2, "componentType": 5125, "count": len(indices), "type": "SCALAR"},
        ],
    }
    return pack_glb(gltf, bytes(blob))


def _inspect_dxf(raw: bytes) -> Dict[str, Any]:
    lines = raw.decode("utf-8", errors="replace").splitlines()
    pairs: List[Tuple[str, str]] = []
    for i in range(0, len(lines) - 1, 2):
        pairs.append((lines[i].strip(), lines[i + 1].strip()))
    segments: List[Tuple[float, float, float, float]] = []
    circles: List[Tuple[float, float, float]] = []

    i = 0
    while i < len(pairs):
        code, val = pairs[i]
        if code == "0" and val in ("LINE", "CIRCLE"):
            props: Dict[str, float] = {}
            j = i + 1
            while j < len(pairs) and pairs[j][0] != "0":
                c, v = pairs[j]
                if c in ("10", "20", "11", "21", "40"):
                    try:
                        props[c] = float(v)
                    except ValueError:
                        pass
                j += 1
            if val == "LINE" and all(k in props for k in ("10", "20", "11", "21")):
                segments.append((props["10"], props["20"], props["11"], props["21"]))
            elif val == "CIRCLE" and all(k in props for k in ("10", "20", "40")):
                circles.append((props["10"], props["20"], props["40"]))
            i = j
            continue
        i += 1

    xs = [x for s in segments for x in (s[0], s[2])] + [x for cx, _, r in circles for x in (cx - r, cx + r)]
    ys = [y for s in segments for y in (s[1], s[3])] + [y for _, cy, r in circles for y in (cy - r, cy + r)]
    bounds = [min(xs), min(ys), max(xs), max(ys)] if xs and ys else [0.0, 0.0, 100.0, 100.0]
    return {
        "kind": "dxf",
        "segments": segments[:1500],
        "circles": circles[:500],
        "bounds": bounds,
    }


def inspect_binary_file(raw: bytes, path: str) -> Dict[str, Any]:
    """Produce a safe, rich JSON-serializable inspection payload for any file type."""
    ext = posixpath.splitext((path or "").strip().lower())[1]
    base: Dict[str, Any] = {
        "ok": True,
        "path": path,
        "ext": ext,
        "size_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "mime_type": guess_mime_type(path),
        "signature": detect_magic_signature(raw),
    }

    if ext in (".obj", ".stl", ".ply"):
        try:
            glb = mesh_bytes_to_glb(raw, ext)
            return {**base, "kind": "model_glb", "glb_b64": base64.b64encode(glb).decode("ascii")}
        except Exception as exc:
            base["conversion_note"] = str(exc)

    if ext == ".dxf":
        try:
            return {**base, **_inspect_dxf(raw)}
        except Exception as exc:
            base["inspect_error"] = str(exc)

    if raw.startswith(b"SQLite format 3\x00") or ext in (".sqlite", ".sqlite3", ".db", ".space"):
        try:
            return {**base, **_inspect_sqlite(raw)}
        except Exception as exc:
            base["inspect_error"] = str(exc)

    if zipfile.is_zipfile(io.BytesIO(raw)):
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                office = _inspect_office_zip(zf, ext)
                if office is not None:
                    return {**base, **office}
                entries = [
                    {"name": info.filename, "size": info.file_size, "compressed": info.compress_size}
                    for info in zf.infolist()[:500]
                ]
                return {**base, "kind": "archive", "format": "zip", "entry_count": len(zf.infolist()), "entries": entries}
        except Exception as exc:
            base["inspect_error"] = str(exc)

    if ext in (".tar", ".tgz", ".tbz2") or path.lower().endswith((".tar.gz", ".tar.bz2", ".tar.xz")):
        try:
            with tarfile.open(fileobj=io.BytesIO(raw), mode="r:*") as tf:
                members = tf.getmembers()
                entries = [{"name": m.name, "size": m.size, "is_dir": m.isdir()} for m in members[:500]]
                return {**base, "kind": "archive", "format": "tar", "entry_count": len(members), "entries": entries}
        except Exception as exc:
            base["inspect_error"] = str(exc)

    if ext == ".gz" and raw.startswith(b"\x1f\x8b"):
        try:
            unpacked = gzip.decompress(raw)
            try:
                text_preview = unpacked[:32768].decode("utf-8")
                return {**base, "kind": "gzip_text", "uncompressed_bytes": len(unpacked), "text_preview": text_preview}
            except UnicodeDecodeError:
                return {**base, "kind": "hex", "hex_dump": format_hex_dump(unpacked), "uncompressed_bytes": len(unpacked)}
        except Exception as exc:
            base["inspect_error"] = str(exc)

    return {**base, "kind": "hex", "hex_dump": format_hex_dump(raw)}
