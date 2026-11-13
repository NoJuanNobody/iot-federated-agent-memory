"""Single-File Space Virtual Filesystem (*.space), WebAssembly & ArtCraft Host Runner, and Agent Playground."""

from __future__ import annotations

import base64
import contextlib
import hashlib
import json
import mimetypes
import os
import platform as py_platform
import plistlib
import posixpath
import re
import shutil
import sqlite3
import struct
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple, Union


# ---------------------------------------------------------------------------
# 1. ArtCraft 15-Domain Wasm Registry & Protocol Specifications
# ---------------------------------------------------------------------------

ARTCRAFT_WASM_APPS: Dict[str, Dict[str, Any]] = {
    "artcraft": {
        "app": "artcraft",
        "display_name": "ArtCraft 2D/3D Multi-Layer Studio",
        "extensions": [".artcraft", ".splat", ".glb"],
        "primary_extension": ".artcraft",
        "mime_type": "application/json",
        "coordinate_system": {
            "type": "hybrid",
            "2d": "y-down",
            "3d": "y-up",
            "units": "meters",
        },
        "description": "Stage 3D camera + depth pass -> separate FG/MG/BG layers (62-Model Routing, Marble 1.1 Gaussian Splats, OpenPBR glTF 2.0)",
        "bundle_url": "/wasm/artcraft/index.html?host=parent",
        "ready_event": "artcraft:ready",
        "open_event": "artcraft:open",
        "save_event": "artcraft:save",
        "dirty_event": "artcraft:dirty",
    },
    "cadcraft": {
        "app": "cadcraft",
        "display_name": "CadCraft 3D CAD & Drafting",
        "extensions": [".dxf", ".dwg", ".cadcraft"],
        "primary_extension": ".dxf",
        "mime_type": "image/vnd.dxf",
        "coordinate_system": {
            "type": "cartesian",
            "direction": "y-up",
            "units": "drawing_units",
            "rotation": "ccw_degrees",
        },
        "description": "ASME Y14.5-2018 GD&T (3-2-1 Datum), ISO 128 lineweights, NURBS G2 continuity",
        "bundle_url": "/wasm/cadcraft/index.html?host=parent",
        "ready_event": "cadcraft:ready",
        "open_event": "cadcraft:open",
        "save_event": "cadcraft:save",
        "dirty_event": "cadcraft:dirty",
    },
    "deckcraft": {
        "app": "deckcraft",
        "display_name": "DeckCraft Presentation Engine",
        "extensions": [".deckcraft", ".pptx"],
        "primary_extension": ".deckcraft",
        "mime_type": "application/json",
        "coordinate_system": {
            "type": "slide_points",
            "direction": "y-down",
            "dimensions": "960x540",
            "units": "pt",
        },
        "description": "Michael Alley Assertion-Evidence, 48pt safe margins, 12-col grid",
        "bundle_url": "/wasm/deckcraft/index.html?host=parent",
        "ready_event": "deckcraft:ready",
        "open_event": "deckcraft:open",
        "save_event": "deckcraft:save",
        "dirty_event": "deckcraft:dirty",
    },
    "designcraft": {
        "app": "designcraft",
        "display_name": "DesignCraft Editorial Layout",
        "extensions": [".designcraft", ".indd"],
        "primary_extension": ".designcraft",
        "mime_type": "application/json",
        "coordinate_system": {
            "type": "spread_points",
            "direction": "y-down",
            "dimensions": "612x792",
            "units": "pt",
        },
        "description": "Müller-Brockmann Swiss Grid, 12pt baseline lock, PDF/X-4 bleed & TAC",
        "bundle_url": "/wasm/designcraft/index.html?host=parent",
        "ready_event": "designcraft:ready",
        "open_event": "designcraft:open",
        "save_event": "designcraft:save",
        "dirty_event": "designcraft:dirty",
    },
    "effectcraft": {
        "app": "effectcraft",
        "display_name": "EffectCraft Motion VFX & Compositing",
        "extensions": [".effectcraft", ".aep"],
        "primary_extension": ".effectcraft",
        "mime_type": "application/json",
        "coordinate_system": {
            "type": "comp_pixels",
            "dimensions": "1920x1080",
            "time_units": "seconds",
        },
        "description": "ACEScg 32-bit float linear light, Cubic Bézier velocity curves (0.16, 1, 0.3, 1)",
        "bundle_url": "/wasm/effectcraft/index.html?host=parent",
        "ready_event": "effectcraft:ready",
        "open_event": "effectcraft:open",
        "save_event": "effectcraft:save",
        "dirty_event": "effectcraft:dirty",
    },
    "figcraft": {
        "app": "figcraft",
        "display_name": "FigCraft UI/UX Design System",
        "extensions": [".figcraft", ".fig"],
        "primary_extension": ".figcraft",
        "mime_type": "application/json",
        "coordinate_system": {
            "type": "page_pixels",
            "direction": "y-down",
            "units": "px",
            "relative": "parent-relative",
        },
        "description": "W3C DTCG 3-tier tokens, Flexbox Auto-Layout (hug/fill), 8pt grid, WCAG 2.2 AA",
        "bundle_url": "/wasm/figcraft/index.html?host=parent",
        "ready_event": "figcraft:ready",
        "open_event": "figcraft:open",
        "save_event": "figcraft:save",
        "dirty_event": "figcraft:dirty",
    },
    "filmcraft": {
        "app": "filmcraft",
        "display_name": "FilmCraft Timeline NLE Video Editor",
        "extensions": [".filmcraft", ".xml", ".edl"],
        "primary_extension": ".filmcraft",
        "mime_type": "application/json",
        "coordinate_system": {
            "type": "subsample_ticks",
            "ticks_per_sec": 254016000000,
            "timecode": "SMPTE ST 12-1",
        },
        "description": "SMPTE ST 12-1, J/L-cut split audio, ACEScct 0-100 IRE, -14 LUFS dialogue ducking",
        "bundle_url": "/wasm/filmcraft/index.html?host=parent",
        "ready_event": "filmcraft:ready",
        "open_event": "filmcraft:open",
        "save_event": "filmcraft:save",
        "dirty_event": "filmcraft:dirty",
    },
    "gridcraft": {
        "app": "gridcraft",
        "display_name": "GridCraft Financial Modeling Spreadsheet",
        "extensions": [".xlsx", ".gridcraft", ".csv"],
        "primary_extension": ".xlsx",
        "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "coordinate_system": {
            "type": "a1_notation",
            "indexing": "0-based sheet index",
        },
        "description": "FAST 4-Sheet Standard, Wall Street Colors (Blue input, Black formula, Green link), SIMD DAG",
        "bundle_url": "/wasm/gridcraft/index.html?host=parent",
        "ready_event": "gridcraft:ready",
        "open_event": "gridcraft:open",
        "save_event": "gridcraft:save",
        "dirty_event": "gridcraft:dirty",
    },
    "lightcraft": {
        "app": "lightcraft",
        "display_name": "LightCraft RAW Photo Grading",
        "extensions": [".lightcraft", ".dng", ".raw"],
        "primary_extension": ".lightcraft",
        "mime_type": "application/json",
        "coordinate_system": {
            "type": "normalized_image_space",
            "range": "0.0..1.0",
            "origin": "top-left",
        },
        "description": "Scene-referred linear RAW, 4-zone parametric curve, 3-way wheels, AI range masks",
        "bundle_url": "/wasm/lightcraft/index.html?host=parent",
        "ready_event": "lightcraft:ready",
        "open_event": "lightcraft:open",
        "save_event": "lightcraft:save",
        "dirty_event": "lightcraft:dirty",
    },
    "pdfcraft": {
        "app": "pdfcraft",
        "display_name": "PdfCraft PDF/A Document Processor",
        "extensions": [".pdf", ".pdfcraft"],
        "primary_extension": ".pdf",
        "mime_type": "application/pdf",
        "coordinate_system": {
            "type": "pdf_user_space",
            "units": "1/72 in",
            "pages": "1-based",
        },
        "description": "ISO 32000-2, ISO 19005-2 PDF/A-2b, ISO 14289-1 PDF/UA-1, Two-Pass True Redaction",
        "bundle_url": "/wasm/pdfcraft/index.html?host=parent",
        "ready_event": "pdfcraft:ready",
        "open_event": "pdfcraft:open",
        "save_event": "pdfcraft:save",
        "dirty_event": "pdfcraft:dirty",
    },
    "photocraft": {
        "app": "photocraft",
        "display_name": "PhotoCraft Raster Graphics & Retouching",
        "extensions": [".psd", ".photocraft", ".png"],
        "primary_extension": ".psd",
        "mime_type": "image/vnd.adobe.photoshop",
        "coordinate_system": {
            "type": "canvas_pixels",
            "direction": "y-down",
            "depth": "16-bit",
        },
        "description": "16-Bit Spatial Frequency Separation, Zone Luminosity Masks, 4-Axis Composite Match",
        "bundle_url": "/wasm/photocraft/index.html?host=parent",
        "ready_event": "photocraft:ready",
        "open_event": "photocraft:open",
        "save_event": "photocraft:save",
        "dirty_event": "photocraft:dirty",
    },
    "scriptcraft": {
        "app": "scriptcraft",
        "display_name": "ScriptCraft Fountain Screenwriting",
        "extensions": [".fountain", ".scriptcraft"],
        "primary_extension": ".fountain",
        "mime_type": "text/plain",
        "coordinate_system": {
            "type": "screenplay_pages",
            "font": "12pt Courier Prime",
            "lines_per_page": 55,
        },
        "description": "WGA Spec / Final Draft 13, Fountain syntax, <= 4 lines/action beat, 1st AD Page-Eighths (1/8)",
        "bundle_url": "/wasm/scriptcraft/index.html?host=parent",
        "ready_event": "scriptcraft:ready",
        "open_event": "scriptcraft:open",
        "save_event": "scriptcraft:save",
        "dirty_event": "scriptcraft:dirty",
    },
    "soundcraft": {
        "app": "soundcraft",
        "display_name": "SoundCraft Multi-Track Digital Audio Workstation",
        "extensions": [".soundcraft", ".wav"],
        "primary_extension": ".soundcraft",
        "mime_type": "application/json",
        "coordinate_system": {
            "type": "samples_or_seconds",
            "loudness": "-14.0 LUFS",
            "true_peak": "-1.0 dBTP",
        },
        "description": "ITU-R BS.1770-4 -14.0 LUFS Integrated & -1.0 dBTP True Peak, Mid-Side EQ, Non-destructive DAW",
        "bundle_url": "/wasm/soundcraft/index.html?host=parent",
        "ready_event": "soundcraft:ready",
        "open_event": "soundcraft:open",
        "save_event": "soundcraft:save",
        "dirty_event": "soundcraft:dirty",
    },
    "vectorcraft": {
        "app": "vectorcraft",
        "display_name": "VectorCraft Scalable Vector Graphics",
        "extensions": [".vectorcraft", ".svg", ".ai"],
        "primary_extension": ".vectorcraft",
        "mime_type": "application/json",
        "coordinate_system": {
            "type": "artboard_points",
            "direction": "y-down",
            "dimensions": "612x792",
            "units": "pt",
        },
        "description": "Extrema Anchor Rule (0/90/180/270 handles), G2 continuity, Boolean Pathfinder",
        "bundle_url": "/wasm/vectorcraft/index.html?host=parent",
        "ready_event": "vectorcraft:ready",
        "open_event": "vectorcraft:open",
        "save_event": "vectorcraft:save",
        "dirty_event": "vectorcraft:dirty",
    },
    "wordcraft": {
        "app": "wordcraft",
        "display_name": "WordCraft OpenXML Document Processor",
        "extensions": [".docx", ".wordcraft"],
        "primary_extension": ".docx",
        "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "coordinate_system": {
            "type": "dom_position",
            "offset_type": "utf-8 byte offset",
        },
        "description": "ECMA-376 OpenXML Cascading Styles (Normal -> Heading 1..9), widowControl, keepNext",
        "bundle_url": "/wasm/wordcraft/index.html?host=parent",
        "ready_event": "wordcraft:ready",
        "open_event": "wordcraft:open",
        "save_event": "wordcraft:save",
        "dirty_event": "wordcraft:dirty",
    },
}

# Inverted mapping: Extension -> App Name
EXTENSION_TO_ARTCRAFT_APP: Dict[str, str] = {}
for app_id, meta in ARTCRAFT_WASM_APPS.items():
    for ext in meta["extensions"]:
        EXTENSION_TO_ARTCRAFT_APP[ext.lower()] = app_id

# Canonical Craft App Suite desktop bundle names & metadata from storytold/craft-launcher (getartcraft.com)
CRAFT_LAUNCHER_DESKTOP_CATALOG: Dict[str, Dict[str, Any]] = {
    "artcraft-launcher": {
        "id": "artcraft-launcher",
        "name": "ArtCraft Launcher",
        "bundle_id": "ai.storyteller.artcraft-launcher",
        "repo": "storytold/craft-launcher",
        "website": "https://getartcraft.com",
        "releases_url": "https://github.com/storytold/craft-launcher/releases/latest",
    },
    "artcraft": {
        "id": "artcraft",
        "name": "ArtCraft",
        "bundle_id": "ai.artcraft.app",
        "repo": "storytold/artcraft",
        "website": "https://getartcraft.com",
        "releases_url": "https://github.com/storytold/artcraft/releases/latest",
    },
    "photocraft": {
        "id": "photocraft",
        "name": "PhotoCraft",
        "bundle_id": "ai.storyteller.photocraft",
        "repo": "storytold/photocraft",
        "website": "https://getartcraft.com/apps/photocraft",
        "releases_url": "https://github.com/storytold/photocraft/releases/latest",
    },
    "vectorcraft": {
        "id": "vectorcraft",
        "name": "VectorCraft",
        "bundle_id": "ai.storyteller.vectorcraft",
        "repo": "storytold/vectorcraft",
        "website": "https://getartcraft.com/apps/vectorcraft",
        "releases_url": "https://github.com/storytold/vectorcraft/releases/latest",
    },
    "filmcraft": {
        "id": "filmcraft",
        "name": "FilmCraft",
        "bundle_id": "ai.storyteller.filmcraft",
        "repo": "storytold/filmcraft",
        "website": "https://getartcraft.com/apps/filmcraft",
        "releases_url": "https://github.com/storytold/filmcraft/releases/latest",
    },
    "lightcraft": {
        "id": "lightcraft",
        "name": "LightCraft",
        "bundle_id": "ai.storyteller.lightcraft",
        "repo": "storytold/lightcraft",
        "website": "https://getartcraft.com/apps/lightcraft",
        "releases_url": "https://github.com/storytold/lightcraft/releases/latest",
    },
    "pdfcraft": {
        "id": "pdfcraft",
        "name": "PdfCraft",
        "bundle_id": "ai.storyteller.pdfcraft",
        "repo": "storytold/pdfcraft",
        "website": "https://getartcraft.com/apps/pdfcraft",
        "releases_url": "https://github.com/storytold/pdfcraft/releases/latest",
    },
    "effectcraft": {
        "id": "effectcraft",
        "name": "EffectCraft",
        "bundle_id": "ai.storyteller.effectcraft",
        "repo": "storytold/effectcraft",
        "website": "https://getartcraft.com/apps/effectcraft",
        "releases_url": "https://github.com/storytold/effectcraft/releases/latest",
    },
    "designcraft": {
        "id": "designcraft",
        "name": "DesignCraft",
        "bundle_id": "ai.storyteller.designcraft",
        "repo": "storytold/designcraft",
        "website": "https://getartcraft.com/apps/designcraft",
        "releases_url": "https://github.com/storytold/designcraft/releases/latest",
    },
    "wordcraft": {
        "id": "wordcraft",
        "name": "WordCraft",
        "bundle_id": "ai.storyteller.wordcraft",
        "repo": "storytold/wordcraft",
        "website": "https://getartcraft.com/apps/wordcraft",
        "releases_url": "https://github.com/storytold/wordcraft/releases/latest",
    },
    "deckcraft": {
        "id": "deckcraft",
        "name": "DeckCraft",
        "bundle_id": "ai.storyteller.deckcraft",
        "repo": "storytold/deckcraft",
        "website": "https://getartcraft.com/apps/deckcraft",
        "releases_url": "https://github.com/storytold/deckcraft/releases/latest",
    },
    "gridcraft": {
        "id": "gridcraft",
        "name": "GridCraft",
        "bundle_id": "ai.storyteller.gridcraft",
        "repo": "storytold/gridcraft",
        "website": "https://getartcraft.com/apps/gridcraft",
        "releases_url": "https://github.com/storytold/gridcraft/releases/latest",
    },
    "cadcraft": {
        "id": "cadcraft",
        "name": "CADCraft",
        "bundle_id": "ai.storyteller.cadcraft",
        "repo": "storytold/cadcraft",
        "website": "https://getartcraft.com/apps/cadcraft",
        "releases_url": "https://github.com/storytold/cadcraft/releases/latest",
    },
    "soundcraft": {
        "id": "soundcraft",
        "name": "SoundCraft",
        "bundle_id": "ai.storyteller.soundcraft",
        "repo": "storytold/soundcraft",
        "website": "https://getartcraft.com/apps/soundcraft",
        "releases_url": "https://github.com/storytold/soundcraft/releases/latest",
    },
    "figcraft": {
        "id": "figcraft",
        "name": "FigCraft",
        "bundle_id": "ai.storyteller.figcraft",
        "repo": "storytold/figcraft",
        "website": "https://getartcraft.com/apps/figcraft",
        "releases_url": "https://github.com/storytold/figcraft/releases/latest",
    },
    "scriptcraft": {
        "id": "scriptcraft",
        "name": "ScriptCraft",
        "bundle_id": "ai.storyteller.scriptcraft",
        "repo": "storytold/scriptcraft",
        "website": "https://getartcraft.com/apps/scriptcraft",
        "releases_url": "https://github.com/storytold/scriptcraft/releases/latest",
    },
}


class ArtCraftLauncherBridge:
    """
    Detects, launches, and syncs native desktop Craft apps and ArtCraft Launcher (getartcraft.com)
    on the user's PC (macOS /Applications, Windows Program Files, Linux AppImage/.deb/.rpm),
    with automatic fallback to WebAssembly (?host=parent) when a native binary is unavailable.
    """

    @staticmethod
    def get_platform_installer_info(app_id: str = "artcraft-launcher") -> Dict[str, str]:
        meta = CRAFT_LAUNCHER_DESKTOP_CATALOG.get(app_id, CRAFT_LAUNCHER_DESKTOP_CATALOG["artcraft-launcher"])
        stem = meta["id"]
        sys_name = sys.platform.lower()
        machine = py_platform.machine().lower()
        if sys_name == "darwin":
            pkg = f"{stem}-macos-universal.dmg"
            install_hint = "Download the signed universal DMG from getartcraft.com and drag to /Applications."
        elif sys_name.startswith("win"):
            arch = "arm64" if "arm" in machine or "aarch64" in machine else "x64"
            pkg = f"{stem}-windows-{arch}.msi"
            install_hint = "Run the Windows Installer (.msi) or unzip the portable release."
        else:
            arch = "aarch64" if "arm" in machine or "aarch64" in machine else "x86_64"
            pkg = f"{stem}-linux-{arch}.AppImage"
            install_hint = "Download the AppImage into ~/Applications, chmod +x, or install the .deb/.rpm."
        return {
            "app_id": stem,
            "package_pattern": pkg,
            "releases_url": meta["releases_url"],
            "website": meta["website"],
            "launcher_releases_url": "https://github.com/storytold/craft-launcher/releases/latest",
            "install_hint": install_hint,
        }

    @classmethod
    def detect_app_on_pc(cls, app_id: str) -> Dict[str, Any]:
        """Detect whether a Craft app (or ArtCraft Launcher itself) is installed locally on this PC."""
        clean_id = app_id.lower().strip()
        meta = CRAFT_LAUNCHER_DESKTOP_CATALOG.get(clean_id, {
            "id": clean_id,
            "name": clean_id.capitalize(),
            "bundle_id": f"ai.storyteller.{clean_id}",
            "repo": f"storytold/{clean_id}",
            "website": f"https://getartcraft.com/apps/{clean_id}",
            "releases_url": f"https://github.com/storytold/{clean_id}/releases/latest",
        })
        app_name = meta["name"]
        bundle_id = meta["bundle_id"]

        installed_path: Optional[str] = None
        version_str: Optional[str] = None
        commit_str: Optional[str] = None
        source_kind: Optional[str] = None

        # 1. macOS: check /Applications/<Name>.app and ~/Applications/<Name>.app (mirrors craft-launcher detect.rs)
        mac_candidates = [
            os.path.join("/Applications", f"{app_name}.app"),
            os.path.expanduser(os.path.join("~/Applications", f"{app_name}.app")),
        ]
        for cand in mac_candidates:
            plist_path = os.path.join(cand, "Contents", "Info.plist")
            if os.path.isfile(plist_path):
                try:
                    with open(plist_path, "rb") as pf:
                        plist_data = plistlib.load(pf)
                    installed_path = cand
                    source_kind = "macos_app"
                    full_key = f"{app_name.replace(' ', '')}Version"
                    version_str = (
                        plist_data.get(full_key)
                        or plist_data.get("CFBundleShortVersionString")
                        or plist_data.get("CFBundleVersion")
                    )
                    commit_key = f"{app_name.replace(' ', '')}BuildCommit"
                    commit_str = plist_data.get(commit_key)
                    break
                except Exception:
                    installed_path = cand
                    source_kind = "macos_app"
                    break

        # 2. Windows: check Program Files and LocalAppData
        if not installed_path and sys.platform.startswith("win"):
            win_roots = [
                os.environ.get("ProgramW6432", ""),
                os.environ.get("ProgramFiles", ""),
                os.environ.get("ProgramFiles(x86)", ""),
                os.environ.get("LOCALAPPDATA", ""),
            ]
            for root in win_roots:
                if not root:
                    continue
                exe_cand = os.path.join(root, app_name, f"{clean_id}.exe")
                if os.path.isfile(exe_cand):
                    installed_path = exe_cand
                    source_kind = "windows_msi"
                    break

        # 3. Linux / FreeBSD / PATH binaries & AppImages
        if not installed_path:
            which_bin = shutil.which(clean_id)
            if which_bin:
                installed_path = which_bin
                source_kind = "system_bin"
            else:
                app_dirs = [
                    os.path.expanduser("~/Applications"),
                    os.path.expanduser("~/AppImages"),
                    os.path.expanduser("~/.local/bin"),
                ]
                for adir in app_dirs:
                    if not os.path.isdir(adir):
                        continue
                    for fname in os.listdir(adir):
                        low = fname.lower()
                        if low.startswith(clean_id) and (low.endswith(".appimage") or low == clean_id):
                            installed_path = os.path.join(adir, fname)
                            source_kind = "linux_appimage"
                            break
                    if installed_path:
                        break

        wasm_meta = ARTCRAFT_WASM_APPS.get(clean_id, {})
        return {
            "id": clean_id,
            "name": app_name,
            "bundle_id": bundle_id,
            "installed_on_pc": bool(installed_path),
            "pc_path": installed_path,
            "pc_version": version_str,
            "pc_commit": commit_str,
            "pc_source": source_kind,
            "preferred_mode": "native-pc" if installed_path else "wasm-web",
            "website": meta["website"],
            "releases_url": meta["releases_url"],
            "wasm_bundle_url": wasm_meta.get("bundle_url", f"/wasm/{clean_id}/index.html?host=parent"),
            "installer": cls.get_platform_installer_info(clean_id),
        }

    @classmethod
    def detect_all_on_pc(cls) -> Dict[str, Any]:
        """Scan this PC for ArtCraft Launcher and all 15 Craft App Suite applications."""
        launcher_info = cls.detect_app_on_pc("artcraft-launcher")
        apps_list: List[Dict[str, Any]] = []
        installed_count = 0
        for app_id in ARTCRAFT_WASM_APPS:
            info = cls.detect_app_on_pc(app_id)
            if info["installed_on_pc"]:
                installed_count += 1
            apps_list.append(info)

        return {
            "launcher": launcher_info,
            "apps": apps_list,
            "installed_count": installed_count,
            "total_apps": len(apps_list),
            "getartcraft_url": "https://getartcraft.com",
            "craft_launcher_releases_url": "https://github.com/storytold/craft-launcher/releases/latest",
        }

    @classmethod
    def materialize_space_file_to_pc(
        cls,
        vfs: "SingleFileSpaceVFS",
        vfs_path: str,
        workspace_root: Optional[str] = None,
    ) -> str:
        """Export a file from a .space SQLite VFS to a local PC workspace directory for native desktop editing."""
        if workspace_root is None:
            workspace_root = os.path.expanduser("~/.tincan/workspace")
        norm_path = vfs.normalize_path(vfs_path)
        rel_path = norm_path.lstrip("/")
        local_dir = os.path.join(workspace_root, vfs.scope, vfs.owner_id, os.path.dirname(rel_path))
        os.makedirs(local_dir, exist_ok=True)
        local_file = os.path.join(workspace_root, vfs.scope, vfs.owner_id, rel_path)

        try:
            rec = vfs.read_file(norm_path, as_text=False)
            raw_bytes = base64.b64decode(rec["content_b64"]) if rec.get("content_b64") else b""
        except FileNotFoundError:
            raw_bytes = b""
            vfs.write_file(norm_path, raw_bytes, updated_by="pc-workspace")

        with open(local_file, "wb") as f:
            f.write(raw_bytes)
        return local_file

    @classmethod
    def sync_pc_file_to_space(
        cls,
        vfs: "SingleFileSpaceVFS",
        vfs_path: str,
        local_file: Optional[str] = None,
        workspace_root: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Sync edits made by a native PC Craft app back into the user/topic .space SQLite VFS."""
        norm_path = vfs.normalize_path(vfs_path)
        if local_file is None:
            if workspace_root is None:
                workspace_root = os.path.expanduser("~/.tincan/workspace")
            local_file = os.path.join(workspace_root, vfs.scope, vfs.owner_id, norm_path.lstrip("/"))
        if not os.path.isfile(local_file):
            raise FileNotFoundError(f"Local workspace file not found on PC: {local_file}")
        with open(local_file, "rb") as f:
            raw_bytes = f.read()
        res = vfs.write_file(norm_path, raw_bytes, updated_by="artcraft-pc")
        return {
            "synced": True,
            "local_file": local_file,
            "space_file": res,
            "merkle_root": vfs.compute_merkle_root(),
        }

    @classmethod
    def open_on_pc(
        cls,
        app_id: Optional[str] = None,
        vfs: Optional["SingleFileSpaceVFS"] = None,
        vfs_path: Optional[str] = None,
        launch_process: bool = True,
    ) -> Dict[str, Any]:
        """
        Open a Craft app (or file from a .space VFS) natively on the user's PC when installed,
        or launch ArtCraft Launcher (getartcraft.com) to install it, with WebAssembly fallback.
        """
        if not app_id and vfs_path:
            app_id = resolve_artcraft_app(vfs_path) or "artcraft-launcher"
        clean_id = (app_id or "artcraft-launcher").lower().strip()

        local_file: Optional[str] = None
        if vfs is not None and vfs_path:
            local_file = cls.materialize_space_file_to_pc(vfs, vfs_path)

        app_info = cls.detect_app_on_pc(clean_id)
        launcher_info = cls.detect_app_on_pc("artcraft-launcher")

        launched = False
        launch_target = None
        mode = "wasm-fallback"

        if app_info["installed_on_pc"] and app_info["pc_path"]:
            mode = "native-pc-app"
            launch_target = app_info["pc_path"]
            if launch_process:
                try:
                    if sys.platform == "darwin":
                        cmd = ["open", "-a", launch_target]
                        if local_file:
                            cmd.append(local_file)
                        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    elif sys.platform.startswith("win"):
                        cmd = [launch_target] + ([local_file] if local_file else [])
                        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        cmd = [launch_target] + ([local_file] if local_file else [])
                        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    launched = True
                except Exception:
                    launched = False
        elif launcher_info["installed_on_pc"] and launcher_info["pc_path"]:
            mode = "artcraft-launcher-pc"
            launch_target = launcher_info["pc_path"]
            if launch_process:
                try:
                    if sys.platform == "darwin":
                        subprocess.Popen(["open", "-a", launch_target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        subprocess.Popen([launch_target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    launched = True
                except Exception:
                    launched = False

        return {
            "status": "ok",
            "app_id": clean_id,
            "mode": mode,
            "launched_process": launched,
            "launch_target": launch_target,
            "local_workspace_file": local_file,
            "vfs_path": vfs_path,
            "app": app_info,
            "launcher": launcher_info,
            "wasm_fallback_url": app_info["wasm_bundle_url"],
            "getartcraft_url": app_info["website"],
        }


def resolve_artcraft_app(path: str) -> Optional[str]:
    """Resolve an ArtCraft application identifier from a file path extension."""
    ext = os.path.splitext(path)[1].lower()
    return EXTENSION_TO_ARTCRAFT_APP.get(ext)


def guess_mime_type(path: str) -> str:
    """Determine MIME type with ArtCraft and 3D extensions fallback."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".dxf":
        return "image/vnd.dxf"
    if ext == ".glb":
        return "model/gltf-binary"
    if ext == ".gltf":
        return "model/gltf+json"
    if ext == ".space":
        return "application/x-sqlite3"
    if ext == ".fountain":
        return "text/plain"
    if ext in EXTENSION_TO_ARTCRAFT_APP:
        app = ARTCRAFT_WASM_APPS[EXTENSION_TO_ARTCRAFT_APP[ext]]
        return app["mime_type"]
    mtype, _ = mimetypes.guess_type(path)
    return mtype or "application/octet-stream"


# ---------------------------------------------------------------------------
# 2. Binary glTF 2.0 (.glb) Generator Helper
# ---------------------------------------------------------------------------

def generate_minimal_glb_bytes(name: str = "rodin_mesh") -> bytes:
    """Generate a 100% valid, minimal binary glTF 2.0 buffer with 1 triangle mesh."""
    # Buffer views:
    # 0: Vertex Positions (3x VEC3 float32 = 36 bytes, target 34962 ARRAY_BUFFER)
    # 1: Triangle Indices (3x SCALAR uint16 = 6 bytes, target 34963 ELEMENT_ARRAY_BUFFER)
    positions = struct.pack("<9f", 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0)
    indices = struct.pack("<3H", 0, 1, 2)
    bin_data = positions + indices
    bin_padding = (4 - (len(bin_data) % 4)) % 4
    bin_data += b"\x00" * bin_padding

    gltf_json = {
        "asset": {
            "version": "2.0",
            "generator": "Hyper3D Rodin glTF 2.0 Generator",
        },
        "scene": 0,
        "scenes": [{"name": "DefaultScene", "nodes": [0]}],
        "nodes": [{"name": name, "mesh": 0}],
        "meshes": [
            {
                "name": name,
                "primitives": [
                    {
                        "attributes": {"POSITION": 0},
                        "indices": 1,
                        "mode": 4,  # TRIANGLES
                    }
                ],
            }
        ],
        "accessors": [
            {
                "bufferView": 0,
                "byteOffset": 0,
                "componentType": 5126,  # FLOAT
                "count": 3,
                "type": "VEC3",
                "max": [1.0, 1.0, 0.0],
                "min": [0.0, 0.0, 0.0],
            },
            {
                "bufferView": 1,
                "byteOffset": 0,
                "componentType": 5123,  # UNSIGNED_SHORT
                "count": 3,
                "type": "SCALAR",
                "max": [2],
                "min": [0],
            },
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 36, "target": 34962},
            {"buffer": 0, "byteOffset": 36, "byteLength": 6, "target": 34963},
        ],
        "buffers": [{"byteLength": len(bin_data)}],
    }

    json_str = json.dumps(gltf_json, separators=(",", ":"))
    json_bytes = json_str.encode("utf-8")
    json_padding = (4 - (len(json_bytes) % 4)) % 4
    json_bytes += b" " * json_padding

    total_length = 12 + 8 + len(json_bytes) + 8 + len(bin_data)
    header = struct.pack("<4sII", b"glTF", 2, total_length)
    json_chunk_header = struct.pack("<I4s", len(json_bytes), b"JSON")
    bin_chunk_header = struct.pack("<I4s", len(bin_data), b"BIN\x00")

    return header + json_chunk_header + json_bytes + bin_chunk_header + bin_data


# ---------------------------------------------------------------------------
# 3. Single-File Space VFS (Single SQLite Container on Disk + S3 Replication)
# ---------------------------------------------------------------------------

def _resolve_default_spaces_base_dir() -> str:
    """Resolve persistent storage root: AGENT_SPACES_DIR -> TINCAN_DATA_DIR -> RAILWAY_VOLUME_MOUNT_PATH -> ./agent_spaces."""
    return (
        os.environ.get("AGENT_SPACES_DIR")
        or os.environ.get("TINCAN_DATA_DIR")
        or os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
        or "./agent_spaces"
    )


class SingleFileSpaceVFS:
    """Represents a single SQLite container file on disk (*.space) that is an isolated filesystem."""

    def __init__(
        self,
        scope: str = "user",
        owner_id: str = "default",
        base_dir: Optional[str] = None,
        space_path: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        enable_s3_sync: bool = True,
    ):
        # The scope becomes a directory name below spaces/, so it must never carry
        # path separators or '..' (that would let /api/space/* reach any file).
        self.scope = re.sub(r"[^a-z0-9_\-]", "_", str(scope or "").lower().strip()) or "user"
        self.owner_id = str(owner_id).strip() or "default"
        clean_id = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", self.owner_id)
        self.clean_id = clean_id

        if space_path is not None:
            self.space_path = os.path.abspath(space_path)
        else:
            if base_dir is None:
                base_dir = _resolve_default_spaces_base_dir()
            base_dir = os.path.abspath(base_dir)
            if self.scope == "user":
                self.space_path = os.path.join(base_dir, "spaces", "users", f"{clean_id}.space")
            elif self.scope == "topic":
                self.space_path = os.path.join(base_dir, "spaces", "topics", f"{clean_id}.space")
            else:
                self.space_path = os.path.join(base_dir, "spaces", self.scope, f"{clean_id}.space")

        os.makedirs(os.path.dirname(self.space_path), exist_ok=True)
        self._lock = threading.RLock()
        scope_plural = "users" if self.scope == "user" else ("topics" if self.scope == "topic" else self.scope)
        self.s3_object_key = f"spaces/{scope_plural}/{clean_id}.space"
        is_temp_test = (
            "/tmp" in self.space_path
            or "/var/folders" in self.space_path
            or "PYTEST_CURRENT_TEST" in os.environ
        )
        self.enable_s3_sync = bool(enable_s3_sync and not is_temp_test)

        if self.enable_s3_sync and not os.path.isfile(self.space_path):
            self._restore_from_s3_if_missing()

        self._init_db(title=title, description=description)

    def _restore_from_s3_if_missing(self) -> bool:
        """Attempt to restore this .space SQLite container from the Railway S3 bucket if missing locally."""
        try:
            from iot_federated_agent_memory.s3_storage import s3_get_object
            if s3_get_object(self.s3_object_key, self.space_path):
                return True
        except Exception:
            pass
        return False

    def sync_to_s3(self) -> Optional[Dict[str, Any]]:
        """Synchronously upload this .space SQLite file to the Railway S3 bucket."""
        try:
            from iot_federated_agent_memory.s3_storage import s3_put_object
            if os.path.isfile(self.space_path):
                return s3_put_object(
                    local_path=self.space_path,
                    object_key=self.s3_object_key,
                    content_type="application/x-sqlite3",
                )
        except Exception:
            pass
        return None

    def _sync_to_s3_async(self) -> None:
        """Asynchronously replicate this .space SQLite file to the Railway S3 bucket."""
        if not self.enable_s3_sync:
            return
        threading.Thread(target=self.sync_to_s3, daemon=True).start()

    @contextlib.contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.space_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self, title: Optional[str] = None, description: Optional[str] = None) -> None:
        """Create tables and seed initial defaults if empty."""
        with self._lock, self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS space_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS fs_files (
                    path TEXT PRIMARY KEY,
                    content BLOB,
                    mime_type TEXT,
                    size_bytes INTEGER,
                    sha256 TEXT,
                    updated_at REAL,
                    updated_by TEXT
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS fs_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    label TEXT,
                    merkle_root TEXT,
                    manifest_json TEXT,
                    created_at REAL
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS exec_runs (
                    run_id TEXT PRIMARY KEY,
                    runtime TEXT,
                    entrypoint TEXT,
                    stdout TEXT,
                    stderr TEXT,
                    exit_code INTEGER,
                    duration_ms REAL,
                    artifacts_json TEXT,
                    created_at REAL
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_turns (
                    turn_id TEXT PRIMARY KEY,
                    prompt TEXT,
                    reply TEXT,
                    tool_calls_json TEXT,
                    files_mutated_json TEXT,
                    created_at REAL
                );
                """
            )

            # Check metadata
            cur.execute("SELECT key FROM space_meta")
            existing_meta = {r["key"] for r in cur.fetchall()}
            if "scope" not in existing_meta:
                now_str = str(time.time())
                disp_title = title or f"{self.scope.capitalize()} Space: {self.owner_id}"
                disp_desc = description or "Single-File Agent Space Virtual Filesystem container"
                meta_rows = [
                    ("scope", self.scope),
                    ("owner_id", self.owner_id),
                    ("title", disp_title),
                    ("description", disp_desc),
                    ("created_at", now_str),
                    ("version", "2.0.0"),
                ]
                cur.executemany("INSERT OR REPLACE INTO space_meta (key, value) VALUES (?, ?)", meta_rows)

            # Auto-seed starter files if fs_files is empty
            cur.execute("SELECT COUNT(*) AS cnt FROM fs_files")
            file_count = cur.fetchone()["cnt"]

        if file_count == 0:
            self._seed_default_files(title=title, description=description)

    def _seed_default_files(self, title: Optional[str] = None, description: Optional[str] = None) -> None:
        """Seed starter project files."""
        readme_title = title or f"{self.scope.capitalize()} Space: {self.owner_id}"
        readme_desc = description or "Single-file isolated workspace container."
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        readme_content = (
            f"# {readme_title}\n\n"
            f"{readme_desc}\n\n"
            f"### Container Metadata\n"
            f"- **Scope:** `{self.scope}`\n"
            f"- **Owner ID:** `{self.owner_id}`\n"
            f"- **Container File:** `{os.path.basename(self.space_path)}`\n"
            f"- **Created:** `{now_iso}`\n"
            f"- **Wasm Runtimes:** Python (Pyodide), JavaScript (QuickJS/Node), ArtCraft (15 Native Wasm Apps)\n\n"
            f"Run scripts with `run_playground` or agent workflows with `run_agent`.\n"
        )

        py_content = (
            'import sys\n\n'
            'def main():\n'
            '    print("Hello from Single-File Agent Space VFS!")\n'
            '    print(f"Python interpreter: {sys.version.split()[0]}")\n\n'
            'if __name__ == "__main__":\n'
            '    main()\n'
        )

        js_content = (
            'console.log("Hello from JavaScript Agent Space!");\n'
            'console.log("Timestamp:", new Date().toISOString());\n'
        )

        dxf_content = (
            "0\nSECTION\n2\nENTITIES\n0\nLINE\n8\n0\n10\n0.0\n20\n0.0\n11\n100.0\n21\n100.0\n0\nENDSEC\n0\nEOF\n"
        )

        models3d_readme = (
            "3D Models Directory for Hyper3D / Rodin generated .glb binary meshes.\n"
            "Query or prompt the agent to generate 3D assets to populate this folder.\n"
        )

        self.write_file("/README.md", readme_content, mime_type="text/markdown", updated_by="system")
        self.write_file("/src/main.py", py_content, mime_type="text/x-python", updated_by="system")
        self.write_file("/src/app.js", js_content, mime_type="application/javascript", updated_by="system")
        self.write_file("/artcraft/drawing.dxf", dxf_content, mime_type="image/vnd.dxf", updated_by="system")
        self.write_file("/models3d/README.txt", models3d_readme, mime_type="text/plain", updated_by="system")

    @staticmethod
    def normalize_path(path: str) -> str:
        """Normalize a path so it always starts with '/' and strictly prevents '..' traversal."""
        cleaned = str(path).strip()
        if not cleaned.startswith("/"):
            cleaned = "/" + cleaned
        norm = posixpath.normpath(cleaned)
        # Ensure it stays within root
        if not norm.startswith("/"):
            norm = "/" + norm
        return norm

    def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List all files in the space, optionally filtered by path prefix."""
        with self._lock, self._connect() as conn:
            cur = conn.cursor()
            if prefix:
                norm_prefix = self.normalize_path(prefix)
                cur.execute(
                    "SELECT path, mime_type, size_bytes, sha256, updated_at, updated_by FROM fs_files WHERE path LIKE ? ORDER BY path ASC",
                    (f"{norm_prefix}%",),
                )
            else:
                cur.execute(
                    "SELECT path, mime_type, size_bytes, sha256, updated_at, updated_by FROM fs_files ORDER BY path ASC"
                )
            rows = cur.fetchall()
            return [
                {
                    "path": r["path"],
                    "mime_type": r["mime_type"],
                    "size_bytes": r["size_bytes"],
                    "sha256": r["sha256"],
                    "updated_at": r["updated_at"],
                    "updated_by": r["updated_by"],
                }
                for r in rows
            ]

    def read_file(self, path: str, as_text: bool = True) -> Dict[str, Any]:
        """Read a file record by normalized path."""
        norm_path = self.normalize_path(path)
        with self._lock, self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT path, content, mime_type, size_bytes, sha256, updated_at, updated_by FROM fs_files WHERE path = ?",
                (norm_path,),
            )
            row = cur.fetchone()
            if not row:
                raise FileNotFoundError(f"File not found in space: {norm_path}")

            blob = row["content"] or b""
            content_b64 = base64.b64encode(blob).decode("ascii") if blob else ""
            text_content = None
            if as_text and blob:
                try:
                    text_content = blob.decode("utf-8")
                except UnicodeDecodeError:
                    text_content = None

            return {
                "path": row["path"],
                "mime_type": row["mime_type"],
                "size_bytes": row["size_bytes"],
                "sha256": row["sha256"],
                "updated_at": row["updated_at"],
                "updated_by": row["updated_by"],
                "content": text_content,
                "content_b64": content_b64,
            }

    def write_file(
        self,
        path: str,
        content: Union[str, bytes],
        mime_type: Optional[str] = None,
        updated_by: str = "user",
        is_base64: bool = False,
    ) -> Dict[str, Any]:
        """Write or overwrite a file in the space container."""
        norm_path = self.normalize_path(path)
        if is_base64 and isinstance(content, str):
            raw_bytes = base64.b64decode(content)
        elif isinstance(content, str):
            raw_bytes = content.encode("utf-8")
        elif isinstance(content, bytes):
            raw_bytes = content
        else:
            raise TypeError(f"Content must be str or bytes, got {type(content)}")

        if not mime_type:
            mime_type = guess_mime_type(norm_path)

        size_bytes = len(raw_bytes)
        sha256 = hashlib.sha256(raw_bytes).hexdigest()
        updated_at = time.time()

        with self._lock, self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO fs_files (path, content, mime_type, size_bytes, sha256, updated_at, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    content = excluded.content,
                    mime_type = excluded.mime_type,
                    size_bytes = excluded.size_bytes,
                    sha256 = excluded.sha256,
                    updated_at = excluded.updated_at,
                    updated_by = excluded.updated_by
                """,
                (norm_path, raw_bytes, mime_type, size_bytes, sha256, updated_at, updated_by),
            )

        self._sync_to_s3_async()
        return {
            "path": norm_path,
            "mime_type": mime_type,
            "size_bytes": size_bytes,
            "sha256": sha256,
            "updated_at": updated_at,
            "updated_by": updated_by,
        }

    def patch_file(
        self,
        path: str,
        target: str,
        replacement: str,
        updated_by: str = "agent",
    ) -> Dict[str, Any]:
        """Replace exact target substring with replacement in a text file."""
        rec = self.read_file(path, as_text=True)
        if rec["content"] is None:
            raise ValueError(f"Cannot patch non-UTF-8 or binary file: {path}")
        if target not in rec["content"]:
            raise ValueError(f"Target string not found in {path}")
        patched = rec["content"].replace(target, replacement)
        return self.write_file(path, patched, mime_type=rec["mime_type"], updated_by=updated_by)

    def delete_file(self, path: str) -> Dict[str, Any]:
        """Delete a file from the space container."""
        norm_path = self.normalize_path(path)
        with self._lock, self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT path FROM fs_files WHERE path = ?", (norm_path,))
            if not cur.fetchone():
                raise FileNotFoundError(f"File not found in space: {norm_path}")
            cur.execute("DELETE FROM fs_files WHERE path = ?", (norm_path,))
        self._sync_to_s3_async()
        return {"deleted": True, "path": norm_path}

    def compute_merkle_root(self) -> str:
        """Compute deterministic SHA-256 Merkle root over sorted path:sha256 pairs."""
        with self._lock, self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT path, sha256 FROM fs_files ORDER BY path ASC")
            rows = cur.fetchall()
            hasher = hashlib.sha256()
            for r in rows:
                line = f"{r['path']}:{r['sha256']}\n"
                hasher.update(line.encode("utf-8"))
            return hasher.hexdigest()

    def create_snapshot(self, label: str = "snapshot") -> Dict[str, Any]:
        """Create a point-in-time snapshot with Merkle root and manifest."""
        snapshot_id = f"snap_{uuid.uuid4().hex[:12]}"
        merkle_root = self.compute_merkle_root()
        manifest = self.list_files()
        manifest_json = json.dumps(manifest)
        created_at = time.time()
        with self._lock, self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO fs_snapshots (snapshot_id, label, merkle_root, manifest_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (snapshot_id, label, merkle_root, manifest_json, created_at),
            )
        return {
            "snapshot_id": snapshot_id,
            "label": label,
            "merkle_root": merkle_root,
            "manifest": manifest,
            "created_at": created_at,
        }

    def list_snapshots(self) -> List[Dict[str, Any]]:
        """List all snapshots sorted chronologically."""
        with self._lock, self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT snapshot_id, label, merkle_root, manifest_json, created_at FROM fs_snapshots ORDER BY created_at DESC"
            )
            rows = cur.fetchall()
            return [
                {
                    "snapshot_id": r["snapshot_id"],
                    "label": r["label"],
                    "merkle_root": r["merkle_root"],
                    "manifest": json.loads(r["manifest_json"] or "[]"),
                    "created_at": r["created_at"],
                }
                for r in rows
            ]

    def list_exec_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent playground execution runs."""
        with self._lock, self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT run_id, runtime, entrypoint, stdout, stderr, exit_code, duration_ms, artifacts_json, created_at FROM exec_runs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
            return [
                {
                    "run_id": r["run_id"],
                    "runtime": r["runtime"],
                    "entrypoint": r["entrypoint"],
                    "stdout": r["stdout"],
                    "stderr": r["stderr"],
                    "exit_code": r["exit_code"],
                    "duration_ms": r["duration_ms"],
                    "artifacts": json.loads(r["artifacts_json"] or "{}"),
                    "created_at": r["created_at"],
                }
                for r in rows
            ]

    def list_agent_turns(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent agent prompt/action turns."""
        with self._lock, self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT turn_id, prompt, reply, tool_calls_json, files_mutated_json, created_at FROM agent_turns ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
            return [
                {
                    "turn_id": r["turn_id"],
                    "prompt": r["prompt"],
                    "reply": r["reply"],
                    "tool_calls": json.loads(r["tool_calls_json"] or "[]"),
                    "files_mutated": json.loads(r["files_mutated_json"] or "[]"),
                    "created_at": r["created_at"],
                }
                for r in rows
            ]

    def get_summary(self) -> Dict[str, Any]:
        """Get high-level summary of the space container."""
        files = self.list_files()
        file_size = os.path.getsize(self.space_path) if os.path.exists(self.space_path) else 0
        return {
            "scope": self.scope,
            "owner_id": self.owner_id,
            "space_file": self.space_path,
            "space_size_bytes": file_size,
            "file_count": len(files),
            "merkle_root": self.compute_merkle_root(),
            "files": files,
            "recent_runs": self.list_exec_runs(limit=5),
            "recent_turns": self.list_agent_turns(limit=5),
        }

    def export_space_bytes(self) -> bytes:
        """Export the raw .space SQLite file bytes."""
        with self._lock:
            with open(self.space_path, "rb") as f:
                return f.read()

    def import_space_bytes(self, raw_bytes: bytes) -> Dict[str, Any]:
        """Validate SQLite header and replace the .space container file."""
        if len(raw_bytes) < 16 or not raw_bytes.startswith(b"SQLite format 3\x00"):
            raise ValueError("Invalid SQLite space file header")
        with self._lock:
            with open(self.space_path, "wb") as f:
                f.write(raw_bytes)
            self._init_db()
        return {
            "imported": True,
            "size_bytes": len(raw_bytes),
            "merkle_root": self.compute_merkle_root(),
        }

    def close(self) -> None:
        """Close connection to SQLite container (no-op with context-managed connections)."""
        return None


# ---------------------------------------------------------------------------
# 4. Wasm and Code Playground Runner
# ---------------------------------------------------------------------------

class WasmAndCodePlaygroundRunner:
    """Executes code, Wasm binaries, and ArtCraft Wasm bridges inside ephemeral sandboxes."""

    def execute(
        self,
        vfs: SingleFileSpaceVFS,
        entrypoint: str = "/src/main.py",
        runtime: str = "auto",
        code_override: Optional[str] = None,
        args: Optional[List[str]] = None,
        stdin_text: str = "",
        timeout_sec: float = 8.0,
    ) -> Dict[str, Any]:
        """Execute a file or code override within the context of the space VFS."""
        entrypoint = vfs.normalize_path(entrypoint)
        if code_override is not None:
            vfs.write_file(entrypoint, code_override, updated_by="runner")

        # Runtime auto-detection
        if runtime == "auto":
            ext = os.path.splitext(entrypoint)[1].lower()
            if ext == ".py":
                runtime = "python"
            elif ext in (".js", ".mjs", ".cjs", ".ts"):
                runtime = "node"
            elif ext == ".wasm":
                runtime = "wasm"
            elif ext in (".sh", ".bash"):
                runtime = "sh"
            elif ext in EXTENSION_TO_ARTCRAFT_APP:
                runtime = "artcraft-wasm"
            else:
                runtime = "python"

        run_id = f"run_{uuid.uuid4().hex[:12]}"
        t_start = time.time()
        stdout = ""
        stderr = ""
        exit_code = 0
        synced_files: List[str] = []
        wasm_host_bridge: Optional[Dict[str, Any]] = None

        # Special handling for ArtCraft Wasm documents
        if runtime == "artcraft-wasm":
            app_id = resolve_artcraft_app(entrypoint) or "artcraft"
            app_meta = ARTCRAFT_WASM_APPS.get(app_id, ARTCRAFT_WASM_APPS["artcraft"])
            file_rec = vfs.read_file(entrypoint, as_text=False)

            # Build exact postMessage host bridge matching cadcraft-web/src/host.rs (?host=parent)
            wasm_host_bridge = {
                "app": app_id,
                "display_name": app_meta["display_name"],
                "wasm_url": app_meta["bundle_url"],
                "entrypoint": entrypoint,
                "open_message": {
                    "type": app_meta["open_event"],
                    "name": os.path.basename(entrypoint),
                    "bytes": file_rec["content_b64"],
                    "bytes_b64": file_rec["content_b64"],
                    "mime_type": app_meta["mime_type"],
                },
                "save_message_type": app_meta["save_event"],
                "ready_message_type": app_meta["ready_event"],
                "dirty_message_type": app_meta["dirty_event"],
                "coordinate_system": app_meta["coordinate_system"],
            }
            stdout = (
                f"[ArtCraft Wasm Bridge Ready]\n"
                f"App: {app_id} ({app_meta['display_name']})\n"
                f"Entrypoint: {entrypoint}\n"
                f"Bundle URL: {app_meta['bundle_url']}\n"
                f"Host Protocol: postMessage (?host=parent)\n"
                f"Events: ready='{app_meta['ready_event']}', open='{app_meta['open_event']}', save='{app_meta['save_event']}', dirty='{app_meta['dirty_event']}'\n"
            )
            exit_code = 0
            duration_ms = round((time.time() - t_start) * 1000.0, 2)

            self._record_run(
                vfs=vfs,
                run_id=run_id,
                runtime=runtime,
                entrypoint=entrypoint,
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                duration_ms=duration_ms,
                artifacts={"wasm_host_bridge": wasm_host_bridge},
            )
            return {
                "run_id": run_id,
                "runtime": runtime,
                "entrypoint": entrypoint,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code,
                "duration_ms": duration_ms,
                "synced_files": [],
                "wasm_host_bridge": wasm_host_bridge,
            }

        # Ephemeral directory sandbox execution for Python, Node, Shell, and Wasm
        with tempfile.TemporaryDirectory(prefix="agent_space_run_") as tmpdir:
            initial_hashes: Dict[str, str] = {}
            # Materialize all files from space into tmpdir
            for f in vfs.list_files():
                fpath = f["path"]
                rel_path = fpath.lstrip("/")
                disk_path = os.path.join(tmpdir, rel_path)
                os.makedirs(os.path.dirname(disk_path), exist_ok=True)
                raw_rec = vfs.read_file(fpath, as_text=False)
                blob = base64.b64decode(raw_rec["content_b64"])
                with open(disk_path, "wb") as fp:
                    fp.write(blob)
                initial_hashes[rel_path] = f["sha256"]

            rel_entry = entrypoint.lstrip("/")
            full_entry = os.path.join(tmpdir, rel_entry)

            if not os.path.exists(full_entry):
                exit_code = 127
                stderr = f"Entrypoint not found in space: {entrypoint}"
            elif runtime == "wasm":
                with open(full_entry, "rb") as wfp:
                    wbytes = wfp.read(8)
                if not wbytes.startswith(b"\x00asm"):
                    exit_code = 1
                    stderr = f"Invalid WebAssembly binary magic header: {wbytes!r}"
                else:
                    exit_code = 0
                    stdout = (
                        f"[Wasm Module Validated]\n"
                        f"Entrypoint: {entrypoint}\n"
                        f"Size: {os.path.getsize(full_entry)} bytes\n"
                        f"Magic: \\x00asm (Wasm v{int.from_bytes(wbytes[4:8], 'little')})\n"
                    )
            else:
                # Prepare execution command
                cmd: List[str]
                if runtime == "python":
                    cmd = [sys.executable, rel_entry]
                elif runtime == "node":
                    cmd = ["node", rel_entry]
                elif runtime == "sh":
                    cmd = ["sh", rel_entry]
                else:
                    cmd = [sys.executable, rel_entry]

                if args:
                    cmd.extend(args)

                sandbox_env = {
                    "PATH": os.environ.get("PATH", "/usr/bin:/bin:/usr/local/bin"),
                    "TMPDIR": tmpdir,
                    "HOME": tmpdir,
                    "PYTHONPATH": tmpdir,
                    "LANG": "en_US.UTF-8",
                    "SANDBOX": "1",
                }
                if "VIRTUAL_ENV" in os.environ:
                    sandbox_env["VIRTUAL_ENV"] = os.environ["VIRTUAL_ENV"]

                try:
                    proc = subprocess.run(
                        cmd,
                        cwd=tmpdir,
                        input=stdin_text.encode("utf-8") if stdin_text else None,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env=sandbox_env,
                        timeout=timeout_sec,
                    )
                    stdout = proc.stdout.decode("utf-8", errors="replace")
                    stderr = proc.stderr.decode("utf-8", errors="replace")
                    exit_code = proc.returncode
                except subprocess.TimeoutExpired:
                    exit_code = 124
                    stderr = f"Execution timed out after {timeout_sec} seconds."
                except FileNotFoundError as err:
                    exit_code = 127
                    stderr = f"Runtime command not found: {err}"
                except Exception as err:
                    exit_code = 1
                    stderr = f"Execution failed: {err}"

            # Post-execution directory scan: any newly created or modified files are synced back
            for root, _, filenames in os.walk(tmpdir):
                for fname in filenames:
                    disk_file = os.path.join(root, fname)
                    rel = os.path.relpath(disk_file, tmpdir)
                    vfs_path = "/" + rel.replace(os.path.sep, "/")
                    try:
                        with open(disk_file, "rb") as dfp:
                            data = dfp.read()
                        new_hash = hashlib.sha256(data).hexdigest()
                        if initial_hashes.get(rel) != new_hash:
                            vfs.write_file(vfs_path, data, updated_by="runner")
                            synced_files.append(vfs_path)
                    except Exception:
                        pass

        duration_ms = round((time.time() - t_start) * 1000.0, 2)
        self._record_run(
            vfs=vfs,
            run_id=run_id,
            runtime=runtime,
            entrypoint=entrypoint,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            duration_ms=duration_ms,
            artifacts={"synced_files": synced_files},
        )

        return {
            "run_id": run_id,
            "runtime": runtime,
            "entrypoint": entrypoint,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
            "duration_ms": duration_ms,
            "synced_files": synced_files,
            "wasm_host_bridge": None,
            "wasm_bridge": True,
        }

    def _record_run(
        self,
        vfs: SingleFileSpaceVFS,
        run_id: str,
        runtime: str,
        entrypoint: str,
        stdout: str,
        stderr: str,
        exit_code: int,
        duration_ms: float,
        artifacts: Dict[str, Any],
    ) -> None:
        """Insert execution run into the exec_runs SQLite table."""
        with vfs._lock, vfs._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO exec_runs (run_id, runtime, entrypoint, stdout, stderr, exit_code, duration_ms, artifacts_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    runtime,
                    entrypoint,
                    stdout,
                    stderr,
                    exit_code,
                    duration_ms,
                    json.dumps(artifacts),
                    time.time(),
                ),
            )


# ---------------------------------------------------------------------------
# 5. Agent Space Harness (Autonomous Actions, Rodin 3D & ArtCraft)
# ---------------------------------------------------------------------------

class AgentSpaceHarness:
    """Autonomous agent harness executing code, synthesizing 3D Rodin models, and generating ArtCraft bridges."""

    def __init__(
        self,
        vfs: SingleFileSpaceVFS,
        runner: Optional[WasmAndCodePlaygroundRunner] = None,
        ai_router: Optional[Any] = None,
    ):
        self.vfs = vfs
        self.runner = runner or WasmAndCodePlaygroundRunner()
        self.ai_router = ai_router

    def run_agent(
        self,
        prompt: str,
        model_alias: str = "gemini-brain",
        author: str = "agent",
        auto_exec: bool = True,
    ) -> Dict[str, Any]:
        """Execute autonomous agent reasoning, file mutations, 3D generation, and tool runs."""
        turn_id = f"turn_{uuid.uuid4().hex[:12]}"
        files_mutated: List[str] = []
        exec_results: List[Dict[str, Any]] = []
        rodin_assets: List[Dict[str, Any]] = []
        wasm_bridges: List[Dict[str, Any]] = []
        tool_calls: List[Dict[str, Any]] = []
        clean_prompt = prompt.strip()

        # 1. 3D / Hyper3D Rodin Asset Generation Action
        is_3d_request = bool(re.search(r"\b(3d|hyper3d|rodin|ronin|\.glb|mesh|gltf)\b", clean_prompt, re.IGNORECASE))
        if is_3d_request:
            slug_match = re.search(r"(\b[a-zA-Z0-9_\-]{3,24}\b)\s+(?:mesh|model|3d)", clean_prompt, re.IGNORECASE)
            slug = slug_match.group(1).lower() if slug_match else "rodin_mesh"
            slug = re.sub(r"[^a-zA-Z0-9_\-]", "_", slug)
            glb_path = f"/models3d/{slug}.glb"

            glb_bytes: Optional[bytes] = None
            rodin_res: Dict[str, Any] = {}

            if self.ai_router is not None and hasattr(self.ai_router, "dispatch_rodin_generation"):
                try:
                    rodin_res = self.ai_router.dispatch_rodin_generation(prompt=clean_prompt, geometry_file_format="glb")
                    b64_str = rodin_res.get("glb_bytes_b64")
                    if b64_str:
                        glb_bytes = base64.b64decode(b64_str)
                except Exception as err:
                    rodin_res = {"error": str(err)}

            if not glb_bytes:
                glb_bytes = generate_minimal_glb_bytes(name=slug)
                rodin_res = rodin_res or {
                    "prompt": clean_prompt,
                    "format": "glb",
                    "status": "Done",
                    "simulated": True,
                }

            self.vfs.write_file(glb_path, glb_bytes, mime_type="model/gltf-binary", updated_by=author)
            files_mutated.append(glb_path)
            rodin_assets.append({"path": glb_path, "size_bytes": len(glb_bytes), "meta": rodin_res})
            tool_calls.append({"tool": "generate_rodin_3d", "path": glb_path, "status": "Done"})

        # 2. ArtCraft Application Document Generation
        mentioned_artcraft: Optional[str] = None
        for app in ARTCRAFT_WASM_APPS:
            if re.search(r"\b" + re.escape(app) + r"\b", clean_prompt, re.IGNORECASE):
                mentioned_artcraft = app
                break

        if not mentioned_artcraft:
            if re.search(r"\b(dxf|dwg|cad)\b", clean_prompt, re.IGNORECASE):
                mentioned_artcraft = "cadcraft"
            elif re.search(r"\b(svg|vector)\b", clean_prompt, re.IGNORECASE):
                mentioned_artcraft = "vectorcraft"
            elif re.search(r"\b(fountain|screenplay|script)\b", clean_prompt, re.IGNORECASE):
                mentioned_artcraft = "scriptcraft"
            elif re.search(r"\b(deck|slides|presentation)\b", clean_prompt, re.IGNORECASE):
                mentioned_artcraft = "deckcraft"

        if mentioned_artcraft:
            meta = ARTCRAFT_WASM_APPS[mentioned_artcraft]
            art_ext = meta["primary_extension"]
            art_path = f"/artcraft/{mentioned_artcraft}_artifact{art_ext}"

            if mentioned_artcraft == "cadcraft":
                art_content = (
                    "0\nSECTION\n2\nENTITIES\n0\nLINE\n8\n0\n10\n0.0\n20\n0.0\n11\n250.0\n21\n150.0\n0\nENDSEC\n0\nEOF\n"
                )
            elif mentioned_artcraft == "scriptcraft":
                art_content = (
                    "Title: CYBERSPACE EXPEDITION\n"
                    "Author: Autonomous Agent\n\n"
                    "EXT. MESH NODE - NIGHT\n\n"
                    "Neon telemetry pulses across the frosted antenna.\n"
                )
            elif mentioned_artcraft == "vectorcraft":
                art_content = (
                    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500">\n'
                    '  <circle cx="250" cy="250" r="200" fill="#10b981" stroke="#047857" stroke-width="8"/>\n'
                    '</svg>\n'
                )
            else:
                art_content = json.dumps(
                    {
                        "app": mentioned_artcraft,
                        "title": f"Generated {meta['display_name']}",
                        "created_by": author,
                        "coordinate_system": meta["coordinate_system"],
                    },
                    indent=2,
                )

            self.vfs.write_file(art_path, art_content, mime_type=meta["mime_type"], updated_by=author)
            files_mutated.append(art_path)

            bridge_run = self.runner.execute(self.vfs, entrypoint=art_path, runtime="artcraft-wasm")
            if bridge_run.get("wasm_host_bridge"):
                wasm_bridges.append(bridge_run["wasm_host_bridge"])
            tool_calls.append({"tool": "artcraft_bridge", "app": mentioned_artcraft, "path": art_path})

        # 3. Python / Code Execution Action
        # Extract explicit code blocks if provided in prompt
        py_code_match = re.search(r"```python\s*(.*?)\s*```", clean_prompt, re.DOTALL)
        js_code_match = re.search(r"```(?:javascript|js)\s*(.*?)\s*```", clean_prompt, re.DOTALL)

        if py_code_match:
            code = py_code_match.group(1)
            target_path = "/src/agent_code.py"
            self.vfs.write_file(target_path, code, mime_type="text/x-python", updated_by=author)
            files_mutated.append(target_path)
            if auto_exec:
                run_res = self.runner.execute(self.vfs, entrypoint=target_path, runtime="python")
                exec_results.append(run_res)
                tool_calls.append({"tool": "execute_python", "entrypoint": target_path, "exit_code": run_res["exit_code"]})
        elif js_code_match:
            code = js_code_match.group(1)
            target_path = "/src/agent_code.js"
            self.vfs.write_file(target_path, code, mime_type="application/javascript", updated_by=author)
            files_mutated.append(target_path)
            if auto_exec:
                run_res = self.runner.execute(self.vfs, entrypoint=target_path, runtime="node")
                exec_results.append(run_res)
                tool_calls.append({"tool": "execute_node", "entrypoint": target_path, "exit_code": run_res["exit_code"]})
        elif re.search(r"\b(solve|simulate|monte carlo|fibonacci|prime|calculate|run code|execute)\b", clean_prompt, re.IGNORECASE):
            # Autonomous simulation generator
            target_path = "/src/solution.py"
            sim_code = (
                'import math, time\n\n'
                f'# Generated for prompt: {clean_prompt}\n'
                'print("[Autonomous Solution Running]")\n'
                'results = [math.sqrt(x) for x in range(1, 10)]\n'
                'print(f"Calculated square roots: {results[:5]}...")\n'
                'print("[Execution Complete: Success]")\n'
            )
            self.vfs.write_file(target_path, sim_code, mime_type="text/x-python", updated_by=author)
            files_mutated.append(target_path)
            if auto_exec:
                run_res = self.runner.execute(self.vfs, entrypoint=target_path, runtime="python")
                exec_results.append(run_res)
                tool_calls.append({"tool": "execute_python", "entrypoint": target_path, "exit_code": run_res["exit_code"]})

        # 4. Generate AI Completion Reply grounded in VFS
        reply = ""
        current_files = [f["path"] for f in self.vfs.list_files()]
        exec_stdout = "\n".join(r.get("stdout", "") for r in exec_results).strip()

        if self.ai_router is not None and hasattr(self.ai_router, "dispatch_completion"):
            try:
                system_context = (
                    f"You are an autonomous AI Agent in Single-File Space VFS '{self.vfs.scope}:{self.vfs.owner_id}'.\n"
                    f"Current space files: {current_files}\n"
                    f"Files mutated in this turn: {files_mutated}\n"
                    f"Execution stdout:\n{exec_stdout}\n"
                )
                messages = [
                    {"role": "system", "content": system_context},
                    {"role": "user", "content": clean_prompt},
                ]
                comp_res = self.ai_router.dispatch_completion(alias=model_alias, messages=messages)
                choices = comp_res.get("choices", [])
                if choices:
                    reply = choices[0].get("message", {}).get("content", "")
            except Exception:
                reply = ""

        if not reply:
            reply_lines = [
                f"Completed autonomous agent turn on space `{self.vfs.scope}:{self.vfs.owner_id}`.",
                f"- **Prompt:** {clean_prompt}",
                f"- **Files Mutated ({len(files_mutated)}):** {', '.join(files_mutated) if files_mutated else 'None'}",
            ]
            if rodin_assets:
                reply_lines.append(f"- **3D Rodin Assets ({len(rodin_assets)}):** {', '.join(a['path'] for a in rodin_assets)}")
            if wasm_bridges:
                reply_lines.append(f"- **ArtCraft Bridges ({len(wasm_bridges)}):** {', '.join(b['app'] for b in wasm_bridges)}")
            if exec_results:
                reply_lines.append(f"- **Execution Runs ({len(exec_results)}):** Output preview:\n```\n{exec_stdout[:300]}\n```")
            reply_lines.append(f"- **Merkle Root:** `{self.vfs.compute_merkle_root()[:16]}...`")
            reply = "\n".join(reply_lines)

        # 5. Log turn to SQLite agent_turns
        with self.vfs._lock, self.vfs._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO agent_turns (turn_id, prompt, reply, tool_calls_json, files_mutated_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    turn_id,
                    clean_prompt,
                    reply,
                    json.dumps(tool_calls),
                    json.dumps(files_mutated),
                    time.time(),
                ),
            )

        return {
            "turn_id": turn_id,
            "scope": self.vfs.scope,
            "owner_id": self.vfs.owner_id,
            "prompt": clean_prompt,
            "reply": reply,
            "tool_calls": tool_calls,
            "files_mutated": files_mutated,
            "exec_results": exec_results,
            "rodin_assets": rodin_assets,
            "wasm_bridges": wasm_bridges,
            "merkle_root": self.vfs.compute_merkle_root(),
        }


# ---------------------------------------------------------------------------
# 6. Agent Space Manager (Multi-Space Orchestrator)
# ---------------------------------------------------------------------------

class AgentSpaceManager:
    """Manages User & Cyberspace Topic Single-File Spaces (*.space), execution, and forking."""

    def __init__(self, base_dir: Optional[str] = None, ai_router: Optional[Any] = None):
        if base_dir is None:
            base_dir = _resolve_default_spaces_base_dir()
        self.base_dir = os.path.abspath(base_dir)
        self.ai_router = ai_router
        self.runner = WasmAndCodePlaygroundRunner()
        self.launcher_bridge = ArtCraftLauncherBridge()
        self._spaces: Dict[str, SingleFileSpaceVFS] = {}
        self._lock = threading.RLock()

    def get_space(
        self,
        scope: str = "user",
        owner_id: str = "default",
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> SingleFileSpaceVFS:
        """Get or initialize a single-file space container."""
        clean_scope = scope.lower().strip() or "user"
        clean_id = str(owner_id).strip() or "default"
        key = f"{clean_scope}:{clean_id}"

        with self._lock:
            if key in self._spaces:
                return self._spaces[key]

            vfs = SingleFileSpaceVFS(
                scope=clean_scope,
                owner_id=clean_id,
                base_dir=self.base_dir,
                title=title,
                description=description,
            )
            self._spaces[key] = vfs
            return vfs

    def get_or_create_space(
        self,
        scope: str = "user",
        owner_id: str = "default",
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> SingleFileSpaceVFS:
        """Alias for get_space for cross-agent compatibility."""
        return self.get_space(scope=scope, owner_id=owner_id, title=title, description=description)

    def list_spaces(self, scope: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all discovered .space containers on disk."""
        results: List[Dict[str, Any]] = []
        spaces_root = os.path.join(self.base_dir, "spaces")
        if not os.path.exists(spaces_root):
            return results

        scope_to_dir = {"user": "users", "topic": "topics", "dynamic": "dynamic"}
        dir_to_scope = {"users": "user", "topics": "topic", "dynamic": "dynamic"}

        if scope:
            norm_scope = scope.lower().strip()
            target_dirs = [scope_to_dir.get(norm_scope, norm_scope)]
        else:
            target_dirs = [d for d in os.listdir(spaces_root) if os.path.isdir(os.path.join(spaces_root, d))]

        for sc_dir_name in target_dirs:
            sc_dir = os.path.join(spaces_root, sc_dir_name)
            if not os.path.isdir(sc_dir):
                continue
            canonical_scope = dir_to_scope.get(sc_dir_name, sc_dir_name)
            for fname in os.listdir(sc_dir):
                if fname.endswith(".space"):
                    owner_id = os.path.splitext(fname)[0]
                    space = self.get_space(scope=canonical_scope, owner_id=owner_id)
                    results.append(space.get_summary())

        return sorted(results, key=lambda x: (x["scope"], x["owner_id"]))

    def create_space(
        self,
        scope: str = "dynamic",
        owner_id: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        template: str = "python",
    ) -> SingleFileSpaceVFS:
        """Create a new dynamic space container with initial template files."""
        if not owner_id:
            owner_id = f"space_{uuid.uuid4().hex[:8]}"
        clean_scope = scope.lower().strip() or "dynamic"
        space = self.get_or_create_space(
            scope=clean_scope,
            owner_id=owner_id,
            title=title or f"Dynamic Space {owner_id}",
            description=description or "Dynamic Agent Execution Space",
        )
        if template == "web":
            space.write_file(
                "/src/index.html",
                "<!DOCTYPE html>\n<html>\n<head><title>Dynamic Space</title></head>\n<body>\n  <h1>Dynamic Agent Space</h1>\n  <div id='app'></div>\n  <script src='app.js'></script>\n</body>\n</html>\n",
                mime_type="text/html",
                updated_by="template",
            )
            space.write_file(
                "/src/app.js",
                "console.log('Dynamic web space loaded');\ndocument.getElementById('app').innerHTML = '<p>Sandboxed Web Agent Mini-Environment Ready</p>';\n",
                mime_type="application/javascript",
                updated_by="template",
            )
        elif template == "3d":
            glb_bytes = generate_minimal_glb_bytes("dynamic_scene")
            space.write_file("/models3d/scene.glb", glb_bytes, mime_type="model/gltf-binary", updated_by="template")
            space.write_file(
                "/src/view_3d.py",
                "# 3D Scene loader\nprint('3D Scene loaded: /models3d/scene.glb')\n",
                mime_type="text/x-python",
                updated_by="template",
            )
        elif template == "artcraft":
            space.write_file(
                "/artcraft/spec.cadcraft",
                "0\nSECTION\n2\nENTITIES\n0\nLINE\n8\n0\n10\n0.0\n20\n0.0\n11\n100.0\n21\n100.0\n0\nENDSEC\n0\nEOF\n",
                mime_type="application/json",
                updated_by="template",
            )
        return space

    def run_playground(
        self,
        scope: str,
        owner_id: str,
        entrypoint: str = "/src/main.py",
        runtime: str = "auto",
        code_override: Optional[str] = None,
        args: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Execute playground run on target space."""
        space = self.get_space(scope=scope, owner_id=owner_id)
        return self.runner.execute(
            vfs=space,
            entrypoint=entrypoint,
            runtime=runtime,
            code_override=code_override,
            args=args,
        )

    def run_agent(
        self,
        scope: str,
        owner_id: str,
        prompt: str,
        model_alias: str = "gemini-brain",
        author: str = "agent",
    ) -> Dict[str, Any]:
        """Execute autonomous agent reasoning and actions on target space."""
        space = self.get_space(scope=scope, owner_id=owner_id)
        harness = AgentSpaceHarness(vfs=space, runner=self.runner, ai_router=self.ai_router)
        return harness.run_agent(prompt=prompt, model_alias=model_alias, author=author)

    def fork_file(
        self,
        from_scope: str,
        from_id: str,
        to_scope: str,
        to_id: str,
        path: str,
        dest_path: Optional[str] = None,
        updated_by: str = "fork",
    ) -> Dict[str, Any]:
        """Fork a single file from one space to another."""
        src_space = self.get_space(scope=from_scope, owner_id=from_id)
        dst_space = self.get_space(scope=to_scope, owner_id=to_id)

        file_rec = src_space.read_file(path, as_text=False)
        target_path = dest_path or path

        res = dst_space.write_file(
            path=target_path,
            content=file_rec["content_b64"],
            mime_type=file_rec["mime_type"],
            updated_by=updated_by,
            is_base64=True,
        )
        return {
            "forked": True,
            "source": f"{from_scope}:{from_id}:{path}",
            "destination": f"{to_scope}:{to_id}:{target_path}",
            "file": res,
        }

    def fork_space(
        self,
        from_scope: str,
        from_id: str,
        to_scope: str,
        to_id: str,
    ) -> Dict[str, Any]:
        """Fork an entire .space SQLite container to a new destination."""
        src_space = self.get_space(scope=from_scope, owner_id=from_id)
        raw_bytes = src_space.export_space_bytes()

        dst_space = self.get_space(scope=to_scope, owner_id=to_id)
        dst_space.import_space_bytes(raw_bytes)

        # Update metadata in destination
        with dst_space._lock, dst_space._connect() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE space_meta SET value = ? WHERE key = 'scope'", (to_scope,))
            cur.execute("UPDATE space_meta SET value = ? WHERE key = 'owner_id'", (to_id,))

        return dst_space.get_summary()

    def export_space(self, scope: str, owner_id: str) -> bytes:
        """Export raw .space container bytes."""
        space = self.get_space(scope=scope, owner_id=owner_id)
        return space.export_space_bytes()

    def export_space_b64(self, scope: str, owner_id: str) -> str:
        """Export base64-encoded .space container string."""
        return base64.b64encode(self.export_space(scope=scope, owner_id=owner_id)).decode("ascii")

    def import_space(self, scope: str, owner_id: str, space_bytes_or_b64: Union[bytes, str]) -> Dict[str, Any]:
        """Import space bytes or base64 into a space container."""
        if isinstance(space_bytes_or_b64, str):
            raw = base64.b64decode(space_bytes_or_b64)
        else:
            raw = space_bytes_or_b64
        space = self.get_space(scope=scope, owner_id=owner_id)
        return space.import_space_bytes(raw)

    def get_artcraft_launcher_status(self) -> Dict[str, Any]:
        """Inspect native PC ArtCraft Launcher & Craft App Suite installations alongside Wasm runtimes."""
        return ArtCraftLauncherBridge.detect_all_on_pc()

    def open_in_artcraft_pc(
        self,
        app_id: Optional[str] = None,
        scope: str = "user",
        owner_id: str = "default",
        path: Optional[str] = None,
        launch_process: bool = True,
    ) -> Dict[str, Any]:
        """Open a file from a user/topic .space VFS directly in the native PC Craft app or ArtCraft Launcher."""
        vfs = self.get_space(scope=scope, owner_id=owner_id) if path else None
        return ArtCraftLauncherBridge.open_on_pc(
            app_id=app_id,
            vfs=vfs,
            vfs_path=path,
            launch_process=launch_process,
        )

    def sync_from_artcraft_pc(
        self,
        scope: str,
        owner_id: str,
        path: str,
        local_file: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Sync edits saved by a native PC Craft app back into the user/topic .space SQLite VFS."""
        vfs = self.get_space(scope=scope, owner_id=owner_id)
        return ArtCraftLauncherBridge.sync_pc_file_to_space(vfs=vfs, vfs_path=path, local_file=local_file)

    def get_wasm_manifest(self) -> Dict[str, Any]:
        """Get the complete manifest of ArtCraft (PC + WebAssembly) and general Wasm runtimes."""
        pc_status = ArtCraftLauncherBridge.detect_all_on_pc()
        pc_by_id = {a["id"]: a for a in pc_status["apps"]}
        enriched_apps: Dict[str, Dict[str, Any]] = {}
        for app_id, meta in ARTCRAFT_WASM_APPS.items():
            pc_info = pc_by_id.get(app_id, {})
            enriched_apps[app_id] = {
                **meta,
                "installed_on_pc": pc_info.get("installed_on_pc", False),
                "pc_path": pc_info.get("pc_path"),
                "pc_version": pc_info.get("pc_version"),
                "preferred_mode": pc_info.get("preferred_mode", "wasm-web"),
                "website": pc_info.get("website", f"https://getartcraft.com/apps/{app_id}"),
                "releases_url": pc_info.get("releases_url", f"https://github.com/storytold/{app_id}/releases/latest"),
            }
        return {
            "version": "2.1.0",
            "total_artcraft_apps": len(enriched_apps),
            "artcraft_launcher": pc_status["launcher"],
            "installed_pc_apps_count": pc_status["installed_count"],
            "getartcraft_url": "https://getartcraft.com",
            "artcraft_apps": enriched_apps,
            "wasm_runtimes": {
                "pyodide-wasm": {
                    "runtime": "pyodide-wasm",
                    "display_name": "Python 3.12 Pyodide WebAssembly",
                    "bundle_url": "/wasm/pyodide/pyodide.js",
                    "description": "Browser-based Python interpreter with NumPy, SciPy & SymPy support",
                },
                "wasi-wasm": {
                    "runtime": "wasi-wasm",
                    "display_name": "WASI WebAssembly Runtime",
                    "bundle_url": "/wasm/wasi/wasi-runner.js",
                    "description": "Standard WebAssembly System Interface (WASI snapshot_preview1) runner",
                },
                "quickjs-wasm": {
                    "runtime": "quickjs-wasm",
                    "display_name": "QuickJS Embedded JavaScript Wasm",
                    "bundle_url": "/wasm/quickjs/quickjs.wasm",
                    "description": "Lightweight ES2020 JavaScript engine compiled to WebAssembly",
                },
                "three-glb-viewer": {
                    "runtime": "three-glb-viewer",
                    "display_name": "Three.js Hyper3D Rodin glTF Viewer",
                    "bundle_url": "/wasm/viewers/three-gltf-viewer.html",
                    "description": "Hardware-accelerated WebGL / WebGPU 3D viewport for .glb models",
                },
            },
            "contract": {
                "protocol": "artcraft-wasm-bridge-v1",
                "query_param": "host=parent",
                "events": ["<app>:ready", "<app>:open", "<app>:save", "<app>:dirty"],
            },
        }
