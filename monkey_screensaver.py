#!/usr/bin/env python3
"""AI MESSIAH logo screensaver (starts the TUI in screensaver mode).

    python3 monkey_screensaver.py         # until you press q / ESC
    python3 monkey_screensaver.py 10      # exit after 10 seconds
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from iot_federated_agent_memory.tui import main  # noqa: E402

if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0].replace(".", "", 1).isdigit():  # legacy positional duration
        args = ["--duration", args[0]] + args[1:]
    sys.exit(main(["--screensaver"] + args))
