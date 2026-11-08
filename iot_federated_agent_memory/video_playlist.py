"""Relay Video Channel & Playlist Manager for Autoplaying Video Collections."""

from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class PlaylistItem:
    id: str
    video_id: str
    platform: str  # "tiktok", "youtube", "mp4"
    creator: str
    title: str
    category: str  # "instruction", "ad", "spotlight"
    cite_url: str
    embed_url: str
    duration_seconds: int = 35
    added_at: float = 0.0


def parse_video_input(
    raw_input: str,
    title: Optional[str] = None,
    creator: Optional[str] = None,
    category: str = "spotlight",
    duration_seconds: int = 35,
) -> PlaylistItem:
    """Parse a TikTok embed blockquote, TikTok URL, TikTok video ID, YouTube URL, or MP4 URL."""
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
        cite_url = f"https://www.tiktok.com/{detected_creator}/video/{vid}"
        embed_url = f"https://www.tiktok.com/player/v1/{vid}?autoplay=1&music_info=1&description=1&rel=0"
        return PlaylistItem(
            id=f"tiktok-{vid}",
            video_id=vid,
            platform="tiktok",
            creator=detected_creator,
            title=title or f"TinCan Demo & Spotlight ({detected_creator})",
            category=category or "spotlight",
            cite_url=cite_url,
            embed_url=embed_url,
            duration_seconds=int(duration_seconds),
            added_at=time.time(),
        )

    # 2. Check for YouTube URL
    yt_match = re.search(r"(?:v=|youtu\.be/|embed/)([A-Za-z0-9_-]{11})", text)
    if yt_match:
        vid = yt_match.group(1)
        return PlaylistItem(
            id=f"youtube-{vid}",
            video_id=vid,
            platform="youtube",
            creator=creator or "@tincan",
            title=title or f"YouTube Video ({vid})",
            category=category or "instruction",
            cite_url=f"https://www.youtube.com/watch?v={vid}",
            embed_url=f"https://www.youtube.com/embed/{vid}?autoplay=1&mute=0&loop=1",
            duration_seconds=int(duration_seconds),
            added_at=time.time(),
        )

    # 3. Direct MP4/WebM URL
    if text.startswith("http://") or text.startswith("https://"):
        vid = f"stream-{int(time.time() * 1000)}"
        return PlaylistItem(
            id=vid,
            video_id=vid,
            platform="mp4",
            creator=creator or "@tincan",
            title=title or "Direct Video Stream",
            category=category or "ad",
            cite_url=text,
            embed_url=text,
            duration_seconds=int(duration_seconds),
            added_at=time.time(),
        )

    raise ValueError(f"Unrecognized video URL, ID, or embed snippet: {text[:80]}")


class RelayVideoPlaylist:
    """Thread-safe video collection manager for the TinCan Relay."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.items: List[PlaylistItem] = []
        self.autoplay: bool = True
        self.loop_collection: bool = True
        # Seed with @nojuannobody's featured TikTok video
        self.add_video(
            raw_input="https://www.tiktok.com/@nojuannobody/video/7705677376465767711",
            title="TinCan Mesh Walkthrough & Creator Spotlight",
            creator="@nojuannobody",
            category="instruction",
            duration_seconds=35,
        )

    def add_video(
        self,
        raw_input: str,
        title: Optional[str] = None,
        creator: Optional[str] = None,
        category: str = "spotlight",
        duration_seconds: int = 35,
    ) -> Dict[str, Any]:
        item = parse_video_input(
            raw_input=raw_input,
            title=title,
            creator=creator,
            category=category,
            duration_seconds=duration_seconds,
        )
        with self._lock:
            # Replace if same video_id already exists, otherwise append to collection
            for idx, existing in enumerate(self.items):
                if existing.video_id == item.video_id and existing.platform == item.platform:
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
