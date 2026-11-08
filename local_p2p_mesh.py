#!/usr/bin/env python3
"""
Direct Local P2P Mesh Server (LAN / mDNS / Direct IP)
Runs entirely local on your machine without Railway or any third-party cloud.
"""

import argparse
import json
import os
import socket
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

DEFAULT_LOCAL_PORT = 8080

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to an arbitrary public IP to determine default egress interface
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

class LocalMeshHandler(BaseHTTPRequestHandler):
    peers = {}

    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/api/status":
            self._send_json({
                "status": "online_local_p2p",
                "mode": "LAN_DIRECT_CONNECT",
                "host_ip": get_local_ip(),
                "connected_peers": list(LocalMeshHandler.peers.values()),
            })
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/register":
            length = int(self.headers.get('content-length', 0))
            body = self.rfile.read(length)
            peer = json.loads(body.decode('utf-8'))
            LocalMeshHandler.peers[peer['peer_id']] = peer
            print(f"[+] Direct P2P Handshake from: {peer['display_name']} ({peer['peer_id']})")
            self._send_json({"status": "handshake_ok", "direct_p2p": True})
        else:
            self.send_response(404)
            self.end_headers()

def main():
    parser = argparse.ArgumentParser(description="Start Local P2P Mesh Server")
    parser.add_argument("--port", type=int, default=DEFAULT_LOCAL_PORT, help="Port to bind")
    args = parser.parse_args()

    local_ip = get_local_ip()
    server = HTTPServer(("0.0.0.0", args.port), LocalMeshHandler)
    print("=" * 60)
    print(f"[*] LOCAL P2P MESH SERVER ACTIVE (NO CLOUD REQUIRED)")
    print(f"[*] Your Local IP Address: http://{local_ip}:{args.port}")
    print(f"[*] Have your friend connect directly using:")
    print(f"    python3 connect_peer.py --relay http://{local_ip}:{args.port}")
    print("=" * 60)
    server.serve_forever()

if __name__ == "__main__":
    main()
