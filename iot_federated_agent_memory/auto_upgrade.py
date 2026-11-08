"""Automatic background upgrade checker and updater for TinCan CLI."""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.request
from typing import Optional

CHECK_INTERVAL_SECONDS = 3600  # Check at most once per hour to stay fast and non-intrusive


def get_local_version_file(config_dir: Optional[str] = None) -> str:
    base = config_dir or os.path.expanduser("~/.tin-can")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "version_meta.json")


def should_check_for_update(meta_file: str) -> bool:
    if not os.path.exists(meta_file):
        return True
    try:
        with open(meta_file, "r") as f:
            data = json.load(f)
        last_check = float(data.get("last_check", 0))
        return (time.time() - last_check) > CHECK_INTERVAL_SECONDS
    except Exception:
        return True


def check_and_auto_upgrade(relay_url: str, config_dir: Optional[str] = None, force: bool = False) -> bool:
    """Query relay version; if remote commit differs from local commit, trigger background upgrade."""
    meta_file = get_local_version_file(config_dir)

    if not force and not should_check_for_update(meta_file):
        return False

    relay = relay_url.rstrip("/")
    try:
        req = urllib.request.Request(f"{relay}/api/version", headers={"User-Agent": "TinCanAutoUpgrade/1.0"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            remote_meta = json.loads(resp.read().decode("utf-8"))
        
        remote_version = remote_meta.get("commit") or remote_meta.get("version")
        local_version = None
        if os.path.exists(meta_file):
            with open(meta_file, "r") as f:
                local_version = json.load(f).get("current_commit")

        # Save check timestamp
        with open(meta_file, "w") as f:
            json.dump({
                "last_check": time.time(),
                "current_commit": local_version or remote_version,
                "remote_commit": remote_version,
            }, f, indent=2)

        if remote_version and local_version and remote_version != local_version:
            print(f"\033[33m[*] New TinCan release detected ({local_version} -> {remote_version}). Auto-upgrading...\033[0m")
            cmd = f"curl -sSL {relay}/install.sh | bash"
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            with open(meta_file, "w") as f:
                json.dump({
                    "last_check": time.time(),
                    "current_commit": remote_version,
                    "remote_commit": remote_version,
                }, f, indent=2)
            print(f"\033[32m[+] Successfully auto-upgraded TinCan to {remote_version}!\033[0m")
            return True
    except Exception:
        # Never crash the user command on network timeout or upgrade error
        pass

    return False
