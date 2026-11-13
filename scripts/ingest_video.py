#!/usr/bin/env python3
"""
Ingest TikTok / Social Videos into TinCan Self-Hosted MP4 Store & Railway S3 Bucket (`tincan-videos`).

Usage:
  python3 scripts/ingest_video.py --all-defaults
  python3 scripts/ingest_video.py "https://www.tiktok.com/@nojuannobody/video/7705677376465767711" --title "Walkthrough"
  railway run python3 scripts/ingest_video.py --repair   # re-ingest playlist items stored as TikTok/Instagram page links
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from iot_federated_agent_memory.s3_storage import s3_put_object
from iot_federated_agent_memory.video_playlist import (
    VIDEOS_DIR,
    RelayVideoPlaylist,
    download_tiktok_mp4,
    parse_video_input,
)


def ingest_single(url_or_id: str, title: str | None = None, creator: str = "@nojuannobody", category: str = "instruction") -> bool:
    item = parse_video_input(
        raw_input=url_or_id,
        title=title,
        creator=creator,
        category=category,
        auto_download=True,
    )
    local_path = item.local_mp4_path or os.path.join(VIDEOS_DIR, f"{item.video_id}.mp4")
    if not os.path.isfile(local_path):
        cite = f"https://www.tiktok.com/{item.creator}/video/{item.video_id}"
        local_path = download_tiktok_mp4(item.video_id, cite, sync_s3=True) or local_path

    if os.path.isfile(local_path):
        size_kb = os.path.getsize(local_path) / 1024.0
        print(f"[+] Downloaded native MP4 ({size_kb:.1f} KB): {local_path}")
        try:
            s3_res = s3_put_object(local_path, f"videos/{item.video_id}.mp4")
            if s3_res:
                print(f"[+] Uploaded to Railway S3 Bucket: {s3_res['s3_uri']} (HTTP {s3_res['status']})")
        except Exception as exc:
            print(f"[!] S3 upload warning: {exc}", file=sys.stderr)
        print(f"[+] Relay Stream Path: {item.embed_url}")
        return True
    else:
        print(f"[-] Failed to download MP4 for {url_or_id}", file=sys.stderr)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Download and ingest video(s) as native MP4 + S3 for TinCan Relay")
    parser.add_argument("url_or_id", nargs="?", default=None, help="TikTok URL, video ID, or blockquote snippet")
    parser.add_argument("--all-defaults", action="store_true", help="Ingest all default @nojuannobody collection videos")
    parser.add_argument("--title", default=None, help="Display title")
    parser.add_argument("--creator", default="@nojuannobody", help="Creator handle")
    parser.add_argument("--category", default="instruction", help="Category (instruction, ad, spotlight)")
    parser.add_argument("--repair", action="store_true", help="Re-ingest S3 playlist items whose embed_url is a page link, not an MP4")
    args = parser.parse_args()

    if args.repair:
        pl = RelayVideoPlaylist(sync_s3=True)
        if not pl._s3_hydrated:
            print("[-] Could not read playlist.json from S3; refusing to repair fallback state", file=sys.stderr)
            return 1
        report = pl.repair_unplayable()
        for vid in report["repaired"]:
            print(f"[+] Repaired: {vid} -> /videos/{vid}.mp4")
        for f in report["failed"]:
            print(f"[-] Still unplayable: {f['video_id']} ({f['source'][:60]}): {f['error']}", file=sys.stderr)
        return 0 if not report["failed"] else 1

    if args.all_defaults or not args.url_or_id:
        ok_all = True
        for entry in RelayVideoPlaylist.DEFAULT_COLLECTION:
            ok = ingest_single(entry["id"], title=entry["title"], creator=entry["creator"], category=entry["category"])
            ok_all = ok_all and ok
        return 0 if ok_all else 1

    return 0 if ingest_single(args.url_or_id, title=args.title, creator=args.creator, category=args.category) else 1


if __name__ == "__main__":
    sys.exit(main())
