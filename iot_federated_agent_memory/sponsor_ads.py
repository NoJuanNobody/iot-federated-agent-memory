"""Sponsor and Rewarded Ad Management for TinCan Mesh OS.

Supports:
1. Native direct developer video sponsors (Railway, Vercel AI SDK, Supabase, Anthropic).
2. Category 'ad' native MP4 videos dynamically synced from RelayVideoPlaylist.
3. Privacy-first developer ad networks (EthicalAds, Carbon Ads).
4. Google AdSense / Rewarded Web Ads configuration hooks.
"""

from __future__ import annotations

import os
import random
import threading
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class SponsorCreative:
    id: str
    name: str
    tagline: str
    cta: str
    url: str
    icon: str
    badge: str
    video_url: str
    video_id: str
    duration_seconds: int = 10
    reward_tokens: int = 5000
    reward_usd: float = 0.05
    category: str = "direct_partner"


DEFAULT_SPONSORS: List[SponsorCreative] = [
    SponsorCreative(
        id="railway",
        name="Railway Infrastructure",
        tagline="Instant container & database deployments for autonomous agents with zero DevOps friction.",
        cta="Deploy on Railway ↗",
        url="https://railway.com?referralCode=tincan",
        icon="🚂",
        badge="Cloud Partner",
        video_url="/videos/7705963225849892126.mp4",
        video_id="7705963225849892126",
        duration_seconds=10,
        reward_tokens=5000,
        reward_usd=0.05,
    ),
    SponsorCreative(
        id="vercel-ai",
        name="Vercel AI SDK & MicroVMs",
        tagline="Deploy durable agent sandboxes, streaming tool calls, and high-speed edge AI gateways.",
        cta="Explore Vercel AI ↗",
        url="https://sdk.vercel.ai?utm_source=tincan-mesh",
        icon="▲",
        badge="Framework Partner",
        video_url="/videos/7705677376465767711.mp4",
        video_id="7705677376465767711",
        duration_seconds=10,
        reward_tokens=5000,
        reward_usd=0.05,
    ),
    SponsorCreative(
        id="supabase",
        name="Supabase Postgres & pgvector",
        tagline="Open source Firebase alternative with fast vector embeddings for agent memory.",
        cta="Build on Supabase ↗",
        url="https://supabase.com?utm_source=tincan-mesh",
        icon="⚡",
        badge="Database Partner",
        video_url="/videos/7704099297763003678.mp4",
        video_id="7704099297763003678",
        duration_seconds=10,
        reward_tokens=5000,
        reward_usd=0.05,
    ),
    SponsorCreative(
        id="openrouter",
        name="OpenRouter Multi-Model Gateway",
        tagline="Unified API gateway bridging Claude, Gemini, Llama, and DeepSeek with instant balance top-ups.",
        cta="Get OpenRouter API ↗",
        url="https://openrouter.ai?utm_source=tincan-mesh",
        icon="🌐",
        badge="AI Gateway",
        video_url="/videos/7705963225849892126.mp4",
        video_id="7705963225849892126",
        duration_seconds=10,
        reward_tokens=5000,
        reward_usd=0.05,
    ),
]


class SponsorAdManager:
    """Manages active sponsors, rotation, clickout tracking, and programmatic network flags."""

    def __init__(self, custom_sponsors: Optional[List[SponsorCreative]] = None) -> None:
        self._lock = threading.Lock()
        self.sponsors: List[SponsorCreative] = list(custom_sponsors or DEFAULT_SPONSORS)
        self.impressions: Dict[str, int] = {}
        self.clicks: Dict[str, int] = {}
        self.completions: Dict[str, int] = {}
        self._rotation_idx: int = 0

    def get_sponsor(self, sponsor_id: Optional[str] = None) -> Dict[str, Any]:
        """Return the requested or next round-robin sponsor creative."""
        with self._lock:
            if not self.sponsors:
                self.sponsors = list(DEFAULT_SPONSORS)

            selected: SponsorCreative
            if sponsor_id:
                matched = [s for s in self.sponsors if s.id == sponsor_id]
                if matched:
                    selected = matched[0]
                else:
                    selected = self.sponsors[self._rotation_idx % len(self.sponsors)]
            else:
                selected = self.sponsors[self._rotation_idx % len(self.sponsors)]
                self._rotation_idx = (self._rotation_idx + 1) % len(self.sponsors)

            self.impressions[selected.id] = self.impressions.get(selected.id, 0) + 1
            return asdict(selected)

    def record_click(self, sponsor_id: str) -> bool:
        with self._lock:
            if any(s.id == sponsor_id for s in self.sponsors):
                self.clicks[sponsor_id] = self.clicks.get(sponsor_id, 0) + 1
                return True
            return False

    def record_completion(self, sponsor_id: str) -> Dict[str, Any]:
        with self._lock:
            matched = [s for s in self.sponsors if s.id == sponsor_id]
            self.completions[sponsor_id] = self.completions.get(sponsor_id, 0) + 1
            if matched:
                return {
                    "status": "verified",
                    "sponsor_id": sponsor_id,
                    "reward_tokens": matched[0].reward_tokens,
                    "reward_usd": matched[0].reward_usd,
                }
            return {
                "status": "verified",
                "sponsor_id": sponsor_id,
                "reward_tokens": 5000,
                "reward_usd": 0.05,
            }

    def sync_from_playlist(self, playlist_items: List[Dict[str, Any]]) -> int:
        """Inject any category='ad' items from the video playlist as active video sponsors."""
        added = 0
        with self._lock:
            existing_ids = {s.id for s in self.sponsors}
            for it in playlist_items:
                if it.get("category") == "ad":
                    ad_id = f"video-{it.get('video_id', it.get('id', 'ad'))}"
                    if ad_id not in existing_ids:
                        creative = SponsorCreative(
                            id=ad_id,
                            name=it.get("title", "Community Video Sponsor"),
                            tagline=f"Sponsored video by {it.get('creator', '@tincan')}. Fund mesh AI compute.",
                            cta="Watch & Support ↗",
                            url=it.get("cite_url", "/"),
                            icon="🎬",
                            badge="Community Sponsor",
                            video_url=it.get("embed_url", f"/videos/{it.get('video_id')}.mp4"),
                            video_id=it.get("video_id", "ad"),
                            duration_seconds=int(it.get("duration_seconds", 10)),
                            reward_tokens=5000,
                            reward_usd=0.05,
                            category="community_video",
                        )
                        self.sponsors.append(creative)
                        existing_ids.add(ad_id)
                        added += 1
        return added

    def get_state(self) -> Dict[str, Any]:
        """Return state including programmatic network flags."""
        with self._lock:
            active = self.sponsors[self._rotation_idx % len(self.sponsors)] if self.sponsors else None
            return {
                "active_sponsor": asdict(active) if active else None,
                "all_sponsors": [asdict(s) for s in self.sponsors],
                "telemetry": {
                    "impressions": dict(self.impressions),
                    "clicks": dict(self.clicks),
                    "completions": dict(self.completions),
                },
                "networks": {
                    "ethical_ads": {
                        "enabled": bool(os.getenv("ETHICALADS_PUBLISHER_ID")),
                        "publisher_id": os.getenv("ETHICALADS_PUBLISHER_ID", ""),
                    },
                    "google_adsense": {
                        "enabled": bool(os.getenv("ADSENSE_CLIENT_ID")),
                        "client_id": os.getenv("ADSENSE_CLIENT_ID", ""),
                    },
                },
            }
