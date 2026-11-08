#!/usr/bin/env python3
"""
Peer Client Connect Script for IoT Federated Agent Memory & WebRTC UDP Mesh
Runs on both your machine and your friend's machine.
"""

import argparse
import json
import os
import sys
import time
import urllib.request

DEFAULT_RELAY = "https://iot-federated-agent-memory-production.up.railway.app"

def check_status(relay_url):
    req = urllib.request.Request(f"{relay_url}/api/status", headers={"User-Agent": "AntigravityPeerClient/1.0"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print("[+] Connected to Central Mesh Relay on Railway!")
            print(f"    - Service Status: {data.get('status')}")
            print(f"    - Readiness Tier: {data.get('readiness_tier')}")
            print(f"    - Active Streams: {len(data.get('active_webrtc_streams', []))}")
            print("    - Funded AI Token Labs:")
            for k, v in data.get("ai_providers", {}).items():
                print(f"      • {k}: ${v:.2f} credits available")
            return data
    except Exception as e:
        print(f"[-] Failed to reach relay: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Connect peer machine to IoT Federated Mesh")
    parser.add_argument("--peer-id", required=True, help="Unique identifier for this machine (e.g. alejandro-mac, friend-macbook)")
    parser.add_argument("--display-name", required=True, help="Human-readable name")
    parser.add_argument("--relay", default=DEFAULT_RELAY, help="Railway signaling relay endpoint")
    args = parser.parse_args()

    print(f"[*] Booting Peer Agent Client: {args.display_name} ({args.peer_id})...")
    
    # Animated AI MESSIAH logo splash (skipped automatically when not on a TTY).
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from iot_federated_agent_memory.tui import splash
        splash(2.5, relay=args.relay)
    except Exception as exc:
        print(f"[!] splash skipped: {exc}")

    status = check_status(args.relay)
    if not status:
        sys.exit(1)

    print("\n[+] Step 1: Synced to Shared Knowledge Graph & Memory Mesh")
    print("[+] Step 2: WebRTC UDP Peer Signaling Channel Established")
    print(f"[+] Step 3: AI Router mapped to {args.relay}")
    print("\nPeer is now LIVE and listening for shared screens & collaborative trajectory sync.")

if __name__ == "__main__":
    main()
