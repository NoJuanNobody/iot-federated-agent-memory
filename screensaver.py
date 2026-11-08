#!/usr/bin/env python3
"""
AI Mesíah - Retro ASCII Matrix & Cyberspace Banner Screensaver
"""

import os
import random
import sys
import time

CYAN = "\033[36m"
BRIGHT_CYAN = "\033[96m"
MAGENTA = "\033[35m"
BRIGHT_MAGENTA = "\033[95m"
GREEN = "\033[32m"
BRIGHT_GREEN = "\033[92m"
GOLD = "\033[33m"
BOLD = "\033[1m"
RESET = "\033[0m"
CLEAR = "\033[2J\033[H"

LOGO_FRAMES = [
f"""{BRIGHT_CYAN}{BOLD}
          .                                                      .
        .n8888bo.               .d88888b.                     .d8888b.
       .888888888b             d88P" "Y88b                   d88P  Y88b
       88888888888             888     888                   888    888
       8888   8888             888     888   .d88b.   .d8888b 888d8888.
       8888   8888    {BRIGHT_MAGENTA}▄▄{BRIGHT_CYAN}       888     888  d8P  Y8b  88K      888   888
       8888   8888   {BRIGHT_MAGENTA}████{BRIGHT_CYAN}      888     888  88888888  "Y8888b. 888   888
       Y888888888P    {BRIGHT_MAGENTA}▀▀{BRIGHT_CYAN}       Y88b. .d88P  Y8b.           X88 888   888
        "Y88888P"               "Y88888P"    "Y8888P   88888P' 888   888
            `                                                    `
           {GOLD}⚡  A I   M E S Í A H   //   I o T   M E S H   C O R E  ⚡{RESET}
""",
f"""{BRIGHT_MAGENTA}{BOLD}
          .                                                      .
        .n8888bo.               .d88888b.                     .d8888b.
       .888888888b             d88P" "Y88b                   d88P  Y88b
       88888888888             888     888                   888    888
       8888   8888             888     888   .d88b.   .d8888b 888d8888.
       8888   8888    {BRIGHT_CYAN}✦✦{BRIGHT_MAGENTA}       888     888  d8P  Y8b  88K      888   888
       8888   8888   {BRIGHT_CYAN}✦✦✦✦{BRIGHT_MAGENTA}      888     888  88888888  "Y8888b. 888   888
       Y888888888P    {BRIGHT_CYAN}✦✦{BRIGHT_MAGENTA}       Y88b. .d88P  Y8b.           X88 888   888
        "Y88888P"               "Y88888P"    "Y8888P   88888P' 888   888
            `                                                    `
           {BRIGHT_CYAN}◈  A I   M E S Í A H   //   I o T   M E S H   C O R E  ◈{RESET}
"""
]

TELEMETRY_MSGS = [
    "WebRTC UDP Pipe ............. [ACTIVE: 60 FPS SUB-80MS]",
    "CRDT Gossip Vector Clock ..... [STATE MERGED // 0 CONFLICTS]",
    "MQTT Telemetry Broker ....... [INGESTING 12 METRICS/SEC]",
    "AI Gateway Provider ......... [CLAUDE 3.7 SONNET POOL OK]",
    "Vault GraphRAG Paywall ...... [HMAC SIGNATURE VERIFIED]",
    "Central Peer Relay .......... [ONLINE @ RAILWAY PRODUCTION]"
]

def render_screensaver(duration_seconds=3.0):
    start = time.time()
    idx = 0
    try:
        while time.time() - start < duration_seconds:
            frame = LOGO_FRAMES[idx % len(LOGO_FRAMES)]
            msg = TELEMETRY_MSGS[idx % len(TELEMETRY_MSGS)]
            
            # Simple matrix rain tail
            rain = "".join([random.choice("0123456789ABCDEF!@#$%^&*()_+{}[]") for _ in range(60)])
            
            sys.stdout.write(CLEAR)
            sys.stdout.write(frame)
            sys.stdout.write(f"\n   {BRIGHT_GREEN}{msg}{RESET}\n")
            sys.stdout.write(f"   {GREEN}STREAM: {rain}{RESET}\n")
            sys.stdout.flush()
            
            time.sleep(0.3)
            idx += 1
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(RESET)

if __name__ == "__main__":
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
    render_screensaver(dur)
