#!/usr/bin/env python3
"""
Ingest TikTok / Social Videos into TinCan Self-Hosted MP4 Store & Railway S3 Bucket (`tincan-videos`).

Usage:
  python3 scripts/ingest_video.py "https://www.tiktok.com/@nojuannobody/video/7705677376465767711" --title "Walkthrough"
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from iot_federated_agent_memory.video_playlist import (
    VIDEOS_DIR,
    download_tiktok_mp4,
    parse_video_input,
)


def upload_to_s3_bucket_if_configured(local_mp4_path: str, object_key: str) -> Optional[str]:
    """Upload MP4 to Railway S3-compatible bucket ('tincan-videos') when S3 credentials are configured."""
    endpoint = os.environ.get("AWS_ENDPOINT_URL") or os.environ.get("S3_ENDPOINT_URL")
    access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    bucket_name = os.environ.get("AWS_S3_BUCKET_NAME", "tincan-videos")

    if not (endpoint and access_key and secret_key):
        return None

    try:
        import boto3  # type: ignore

        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        s3.upload_file(
            local_mp4_path,
            bucket_name,
            object_key,
            ExtraArgs={"ContentType": "video/mp4"},
        )
        return f"s3://{bucket_name}/{object_key}"
    except Exception as exc:
        print(f"[!] S3 upload skipped: {exc}", file=sys.stderr)
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Download and ingest video as native MP4 for TinCan Relay")
    parser.add_argument("url_or_id", help="TikTok URL, video ID, or blockquote snippet")
    parser.add_argument("--title", default=None, help="Display title")
    parser.add_argument("--creator", default="@nojuannobody", help="Creator handle")
    parser.add_argument("--category", default="instruction", help="Category (instruction, ad, spotlight)")
    args = parser.parse_args()

    item = parse_video_input(
        raw_input=args.url_or_id,
        title=args.title,
        creator=args.creator,
        category=args.category,
        auto_download=True,
    )
    local_path = item.local_mp4_path or os.path.join(VIDEOS_DIR, f"{item.video_id}.mp4")
    if not os.path.isfile(local_path):
        cite = f"https://www.tiktok.com/{item.creator}/video/{item.video_id}"
        local_path = download_tiktok_mp4(item.video_id, cite) or local_path

    if os.path.isfile(local_path):
        size_kb = os.path.getsize(local_path) / 1024.0
        print(f"[+] Downloaded native MP4 ({size_kb:.1f} KB): {local_path}")
        s3_uri = upload_to_s3_bucket_if_configured(local_path, f"videos/{item.video_id}.mp4")
        if s3_uri:
            print(f"[+] Synced to Railway S3 Bucket: {s3_uri}")
        print(f"[+] Relay Stream Path: {item.embed_url}")
        return 0
    else:
        print("[-] Failed to download MP4 file.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
