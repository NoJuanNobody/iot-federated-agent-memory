#!/usr/bin/env python3
"""Launch the AI MESSIAH dashboard + screensaver (works from any directory).

    python3 ~/dev/iot-federated-agent-memory/tui.py [--screensaver] [--relay URL]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from iot_federated_agent_memory.tui import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
