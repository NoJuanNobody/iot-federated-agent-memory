#!/usr/bin/env python3
"""Re-vendor the stdlib-only core of context-palace into TinCan.

TinCan's Dockerfile runs ``python3 server.py`` from ``COPY . .`` with only
pynacl/cryptography/webauthn installed, so the arena context store vendors the
three context-palace modules it needs (models, lake, retrieval). They import
nothing outside the standard library. The full context-palace package is not a
dependency: its ``__init__`` eagerly imports the Rich/Textual TUI.

Usage:
    python scripts/vendor_context_palace.py /path/to/context-palace <commit>

The copy is byte-for-byte except that ``from context_palace.`` imports become
package-relative (``from .``). VENDORED.json records the commit and the
sha256 of every upstream file so drift is detectable in tests.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys

MODULES = ("models.py", "lake.py", "retrieval.py")
DEST = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "iot_federated_agent_memory", "vendor", "context_palace",
)
UPSTREAM = "https://github.com/NoJuanNobody/context-palace"


def main(repo: str, commit: str) -> int:
    full = subprocess.check_output(["git", "-C", repo, "rev-parse", commit], text=True).strip()
    os.makedirs(DEST, exist_ok=True)
    record = {"upstream": UPSTREAM, "commit": full, "files": {}}
    for name in MODULES:
        raw = subprocess.check_output(["git", "-C", repo, "show", f"{full}:context_palace/{name}"])
        record["files"][name] = {"upstream_sha256": hashlib.sha256(raw).hexdigest()}
        text = raw.decode("utf-8").replace("from context_palace.", "from .")
        with open(os.path.join(DEST, name), "w", encoding="utf-8") as fh:
            fh.write(text)
    with open(os.path.join(DEST, "VENDORED.json"), "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2)
        fh.write("\n")
    print(f"vendored {', '.join(MODULES)} @ {full[:7]} -> {DEST}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
