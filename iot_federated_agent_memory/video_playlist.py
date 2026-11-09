"""Relay Video Channel & Native MP4 Playlist Manager (Backed by Railway S3 Bucket `tincan-videos`)."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
import time
import urllib.request
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

from .s3_storage import s3_get_object, s3_put_object

VIDEOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "videos")


@dataclass
class PlaylistItem:
    id: str
    video_id: str
    platform: str  # "mp4"
    creator: str
    title: str
    category: str  # "instruction", "ad", "spotlight"
    cite_url: str
    embed_url: str  # Direct /videos/<id>.mp4 stream
    duration_seconds: int = 35
    added_at: float = 0.0
    local_mp4_path: Optional[str] = None
    s3_uri: Optional[str] = None


def download_tiktok_mp4(
    video_id: str,
    cite_url: str,
    dest_dir: Optional[str] = None,
    sync_s3: bool = True,
) -> Optional[str]:
    """Resolve clean MP4 from local cache, Railway S3 bucket, yt-dlp, or TikWM API."""
    target_dir = dest_dir or VIDEOS_DIR
    os.makedirs(target_dir, exist_ok=True)
    out_path = os.path.join(target_dir, f"{video_id}.mp4")

    # 1. Local cache check
    if os.path.isfile(out_path) and os.path.getsize(out_path) > 1024:
        return out_path

    # 2. Check Railway S3 bucket ('tincan-videos')
    if sync_s3 and s3_get_object(f"videos/{video_id}.mp4", out_path):
        return out_path

    # 3. Try yt-dlp if available on system
    ytdlp_bin = os.path.expanduser("~/.local/bin/yt-dlp")
    if not (os.path.isfile(ytdlp_bin) and os.access(ytdlp_bin, os.X_OK)):
        ytdlp_bin = shutil.which("yt-dlp")

    if ytdlp_bin:
        try:
            subprocess.run(
                [ytdlp_bin, "-f", "mp4/best", "-o", out_path, cite_url],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=35,
            )
        except Exception:
            pass

    # 4. Fallback for cloud containers without yt-dlp: TikWM direct MP4 resolver
    if not (os.path.isfile(out_path) and os.path.getsize(out_path) > 1024):
        try:
            api_url = f"https://www.tikwm.com/api/?url={cite_url}"
            req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                meta = json.loads(resp.read().decode("utf-8"))
            mp4_url = (meta.get("data") or {}).get("play")
            if mp4_url:
                dl_req = urllib.request.Request(mp4_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(dl_req, timeout=20) as mp4_resp:
                    data = mp4_resp.read()
                if len(data) > 1024:
                    with open(out_path, "wb") as f:
                        f.write(data)
        except Exception:
            pass

    if os.path.isfile(out_path) and os.path.getsize(out_path) > 1024:
        if sync_s3:
            try:
                s3_put_object(out_path, f"videos/{video_id}.mp4")
            except Exception:
                pass
        return out_path

    return None


def parse_video_input(
    raw_input: str,
    title: Optional[str] = None,
    creator: Optional[str] = None,
    category: str = "spotlight",
    duration_seconds: int = 35,
    auto_download: bool = True,
) -> PlaylistItem:
    """Parse a TikTok URL/embed/ID or direct MP4 URL and resolve to a self-hosted native MP4 stream."""
    text = (raw_input or "").strip()
    if not text:
        raise ValueError("Video input cannot be empty")

    # 1. Check for TikTok video ID in data-video-id="..." or /video/<digits> or bare 19-digit ID
    tt_id_match = (
        re.search(r'data-video-id=["\'](\d{15,22})["\']', text)
        or re.search(r"/video/(\d{15,22})", text)
        or re.search(r"^(\d{15,22})$", text)
    )
    if tt_id_match:
        vid = tt_id_match.group(1)
        handle_match = re.search(r"tiktok\.com/(@[A-Za-z0-9_.-]+)", text)
        detected_creator = creator or (handle_match.group(1) if handle_match else "@nojuannobody")
        if not detected_creator.startswith("@"):
            detected_creator = f"@{detected_creator}"
        tiktok_source_url = f"https://www.tiktok.com/{detected_creator}/video/{vid}"
        local_mp4 = download_tiktok_mp4(vid, tiktok_source_url) if auto_download else None
        embed_url = f"/videos/{vid}.mp4"
        return PlaylistItem(
            id=f"video-{vid}",
            video_id=vid,
            platform="mp4",
            creator=detected_creator,
            title=title or f"TinCan Featured Video ({detected_creator})",
            category=category or "spotlight",
            cite_url=embed_url,
            embed_url=embed_url,
            duration_seconds=int(duration_seconds),
            added_at=time.time(),
            local_mp4_path=local_mp4,
        )

    # 2. Direct MP4/WebM path or URL
    if text.startswith("http://") or text.startswith("https://") or text.startswith("/videos/"):
        vid = os.path.splitext(os.path.basename(text.split("?")[0]))[0] or f"stream-{int(time.time() * 1000)}"
        return PlaylistItem(
            id=f"video-{vid}",
            video_id=vid,
            platform="mp4",
            creator=creator or "@tincan",
            title=title or f"TinCan Video ({vid})",
            category=category or "ad",
            cite_url=text,
            embed_url=text,
            duration_seconds=int(duration_seconds),
            added_at=time.time(),
        )

    raise ValueError(f"Unrecognized video URL, ID, or embed snippet: {text[:80]}")


class RelayVideoPlaylist:
    """Thread-safe native MP4 video collection manager for the TinCan Relay."""

    DEFAULT_COLLECTION = [
        {
            "id": "7705677376465767711",
            "title": "TinCan Mesh Walkthrough",
            "creator": "@nojuannobody",
            "category": "instruction",
        },
        {
            "id": "7705963225849892126",
            "title": "AI Messiah Non-Profit AI Lab",
            "creator": "@nojuannobody",
            "category": "ad",
        },
        {
            "id": "7704099297763003678",
            "title": "Deconstructing the Frame (HARP)",
            "creator": "@nojuannobody",
            "category": "spotlight",
        },
    ]

    def __init__(self, seed_default_only_first: bool = False) -> None:
        self._lock = threading.Lock()
        self.items: List[PlaylistItem] = []
        self.autoplay: bool = True
        self.loop_collection: bool = True
        os.makedirs(VIDEOS_DIR, exist_ok=True)
        seeds = self.DEFAULT_COLLECTION[:1] if seed_default_only_first else self.DEFAULT_COLLECTION
        for s in seeds:
            self.add_video(
                raw_input=s["id"],
                title=s["title"],
                creator=s["creator"],
                category=s["category"],
                duration_seconds=35,
                auto_download=False,
            )

    def add_video(
        self,
        raw_input: str,
        title: Optional[str] = None,
        creator: Optional[str] = None,
        category: str = "spotlight",
        duration_seconds: int = 35,
        auto_download: bool = True,
    ) -> Dict[str, Any]:
        item = parse_video_input(
            raw_input=raw_input,
            title=title,
            creator=creator,
            category=category,
            duration_seconds=duration_seconds,
            auto_download=auto_download,
        )
        with self._lock:
            for idx, existing in enumerate(self.items):
                if existing.video_id == item.video_id:
                    self.items[idx] = item
                    return asdict(item)
            self.items.append(item)
            return asdict(item)

    def remove_video(self, video_id_or_id: str) -> bool:
        with self._lock:
            before = len(self.items)
            self.items = [
                it for it in self.items if it.id != video_id_or_id and it.video_id != video_id_or_id
            ]
            return len(self.items) < before

    def get_playlist(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "autoplay": self.autoplay,
                "loop_collection": self.loop_collection,
                "total": len(self.items),
                "videos": [asdict(it) for it in self.items],
            }
