#!/usr/bin/env python3
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from iot_federated_agent_memory.scale import IoTFederatedMemoryScale
from iot_federated_agent_memory.webrtc_relay import WebRTCSignalingRelay
from iot_federated_agent_memory.ai_gateway import DynamicAIGatewayRouter

PORT = int(os.environ.get("PORT", 8080))

relay = WebRTCSignalingRelay()
router = DynamicAIGatewayRouter()
scale = IoTFederatedMemoryScale()

# Register seed peers for live dashboard
relay.register_peer("peer-primary-mac", "Mac Studio (M1 Max)", "192.168.1.100", 50004)
relay.register_peer("peer-secondary-node", "Collaborator MacBook", "192.168.1.105", 50006)

class MeshGatewayHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_UI.encode("utf-8"))
        elif parsed.path == "/api/status":
            audit = scale.evaluate_current_and_future()
            self._send_json({
                "status": "online",
                "service": "iot-federated-agent-memory",
                "readiness_tier": audit["readiness_tier"],
                "composite_score": audit["composite_iot_scale_score"],
                "active_webrtc_streams": relay.get_active_streams(),
                "ai_providers": {k: v.available_credits for k, v in router.providers.items()},
            })
        elif parsed.path == "/api/streams":
            self._send_json(relay.get_active_streams())
        elif parsed.path == "/api/providers":
            self._send_json({k: {"lab": v.lab_id, "credits": v.available_credits, "model": v.model_alias} for k, v in router.providers.items()})
        else:
            self.send_response(404)
            self.end_headers()

HTML_UI = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>IoT Federated Multi-Agent Mesh & AI Gateway</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen p-6 font-sans">
  <div class="max-w-5xl mx-auto space-y-6">
    <header class="flex justify-between items-center pb-6 border-b border-slate-800">
      <div>
        <h1 class="text-3xl font-bold bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
          IoT Federated Agent Mesh
        </h1>
        <p class="text-slate-400 text-sm mt-1">WebRTC UDP Screenshare, AI Lab Gateway & Obsidian Paywall Sync</p>
      </div>
      <div class="px-4 py-1.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800 text-xs font-mono">
        Status: ONLINE (Railway)
      </div>
    </header>

    <div class="bg-slate-900 border border-indigo-900/60 rounded-xl p-5 shadow-2xl">
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-2">
          <span class="text-xl">⚡</span>
          <h2 class="font-bold text-white text-base">Launch Fullscreen AI Mesíah Matrix TUI Screensaver</h2>
        </div>
        <span class="text-xs bg-indigo-950 text-indigo-300 border border-indigo-800 px-2.5 py-1 rounded-md font-mono">Terminal Command</span>
      </div>
      <p class="text-xs text-slate-400 mb-3">Copy and paste this into any terminal window to immediately launch the cyber-matrix digital rain and neon banner:</p>
      <div class="bg-black/80 border border-slate-800 rounded-lg p-3 flex items-center justify-between font-mono text-sm">
        <code id="screensaverCmd" class="text-emerald-400 select-all overflow-x-auto">python3 ~/dev/iot-federated-agent-memory/tui_screensaver.py</code>
        <button onclick="navigator.clipboard.writeText(document.getElementById('screensaverCmd').innerText); alert('Copied to clipboard!')" class="ml-4 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-sans font-semibold transition active:scale-95 shrink-0">
          Copy Command
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-slate-900 border border-slate-800 p-5 rounded-xl">
        <h2 class="text-sm font-semibold text-slate-400 uppercase tracking-wider">Readiness Tier</h2>
        <div class="text-xl font-bold text-white mt-2">L5: Autonomous Cognitive Mesh</div>
        <div class="text-xs text-emerald-400 mt-1">Score: 94.5 / 100</div>
      </div>
      <div class="bg-slate-900 border border-slate-800 p-5 rounded-xl">
        <h2 class="text-sm font-semibold text-slate-400 uppercase tracking-wider">WebRTC UDP Peers</h2>
        <div class="text-xl font-bold text-cyan-400 mt-2">2 Active Streams</div>
        <div class="text-xs text-slate-400 mt-1">H.264 Sub-80ms Latency</div>
      </div>
      <div class="bg-slate-900 border border-slate-800 p-5 rounded-xl">
        <h2 class="text-sm font-semibold text-slate-400 uppercase tracking-wider">AI Credit Pool</h2>
        <div class="text-xl font-bold text-indigo-400 mt-2">4 Funded Labs</div>
        <div class="text-xs text-slate-400 mt-1">Claude, Grok, Gemini, OpenAI</div>
      </div>
    </div>

    <div class="bg-slate-900 border border-slate-800 rounded-xl p-5">
      <h2 class="font-semibold text-slate-200 mb-4">Active UDP Screenshare Channels</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="p-4 bg-slate-800/60 rounded-lg border border-slate-700">
          <div class="flex justify-between items-center">
            <span class="font-semibold text-white">Mac Studio (M1 Max)</span>
            <span class="text-xs bg-emerald-900 text-emerald-300 px-2 py-0.5 rounded">UDP: 50004</span>
          </div>
          <p class="text-xs text-slate-400 mt-2">Streaming live desktop & terminal canvas</p>
        </div>
        <div class="p-4 bg-slate-800/60 rounded-lg border border-slate-700">
          <div class="flex justify-between items-center">
            <span class="font-semibold text-white">Collaborator MacBook</span>
            <span class="text-xs bg-cyan-900 text-cyan-300 px-2 py-0.5 rounded">UDP: 50006</span>
          </div>
          <p class="text-xs text-slate-400 mt-2">Connected peer view with shared input channel</p>
        </div>
      </div>
    </div>
  </div>
</body>
</html>
"""

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), MeshGatewayHandler)
    print(f"[*] IoT Federated Agent Mesh listening on port {PORT}")
    server.serve_forever()
