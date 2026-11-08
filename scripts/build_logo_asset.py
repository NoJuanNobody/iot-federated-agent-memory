#!/usr/bin/env python3
"""Regenerate the AI Messiah logo pixel asset used by the TUI.

Requires Pillow (only for this build step; the TUI itself has no dependencies).

    python3 scripts/build_logo_asset.py ~/Downloads/Gemini_Generated_Image.jpeg

The default crop box selects the middle panel (circuit-brain chimp) of the
three-panel "THE AI MESSIAH CONSULTING" comic sheet.
"""

import argparse
import os

from PIL import Image

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_DIR = os.path.join(REPO_ROOT, "iot_federated_agent_memory", "assets")
DEFAULT_CROP = (506, 110, 903, 541)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", help="Source artwork (jpeg/png)")
    parser.add_argument("--crop", type=int, nargs=4, default=DEFAULT_CROP, metavar=("L", "T", "R", "B"))
    parser.add_argument("--width", type=int, default=110, help="Stored asset width in pixels")
    args = parser.parse_args()

    os.makedirs(ASSET_DIR, exist_ok=True)
    panel = Image.open(os.path.expanduser(args.source)).convert("RGB").crop(tuple(args.crop))
    panel.save(os.path.join(ASSET_DIR, "ai_messiah_logo.png"))

    height = round(args.width * panel.height / panel.width)
    small = panel.resize((args.width, height), Image.LANCZOS)

    hex_path = os.path.join(ASSET_DIR, "ai_messiah_logo.hex")
    with open(hex_path, "w") as f:
        f.write(f"{args.width} {height}\n")
        for y in range(height):
            f.write("".join("%02x%02x%02x" % small.getpixel((x, y)) for x in range(args.width)) + "\n")
    print(f"wrote {hex_path} ({args.width}x{height}) and ai_messiah_logo.png")


if __name__ == "__main__":
    main()
