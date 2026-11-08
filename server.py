#!/usr/bin/env python3
import io
import json
import os
import tarfile
from http.server import ThreadingHTTPServer as HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from iot_federated_agent_memory.scale import IoTFederatedMemoryScale
from iot_federated_agent_memory.webrtc_relay import WebRTCSignalingRelay
from iot_federated_agent_memory.ai_gateway import DynamicAIGatewayRouter
from iot_federated_agent_memory.tincan_relay import TinCanBlindRelay

PORT = int(os.environ.get("PORT", 8080))

relay = WebRTCSignalingRelay()
router = DynamicAIGatewayRouter()
scale = IoTFederatedMemoryScale()
tincan_relay = TinCanBlindRelay()

# Register seed peers for live dashboard
relay.register_peer("peer-primary-mac", "Mac Studio (M1 Max)", "192.168.1.100", 50004)
relay.register_peer("peer-secondary-node", "Collaborator MacBook", "192.168.1.105", 50006)

class MeshGatewayHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/tincan/send":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode("utf-8"))
                result = tincan_relay.send(payload)
                self._send_json(result, 200)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                model_alias = data.get("model", "gemini-brain")
                prompt = data.get("prompt")
                messages = data.get("messages")
                if not messages:
                    if not prompt:
                        prompt = "Hello from TinCan 2 / IoT Federated Mesh!"
                    messages = [{"role": "user", "content": prompt}]
                completion = router.dispatch_completion(
                    alias=model_alias,
                    messages=messages,
                    temperature=float(data.get("temperature", 0.7)),
                    max_tokens=int(data.get("max_tokens", 512)),
                )
                self._send_json(completion, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        else:
            self.send_response(404)
            self.end_headers()

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
                "tincan_relay": tincan_relay.get_stats(),
            })
        elif parsed.path == "/api/streams":
            self._send_json(relay.get_active_streams())
        elif parsed.path == "/api/providers":
            self._send_json({k: {"lab": v.lab_id, "credits": v.available_credits, "model": v.model_alias} for k, v in router.providers.items()})
        elif parsed.path == "/api/tincan/inbox":
            query = parse_qs(parsed.query)
            address = query.get("address", query.get("addr", [None]))[0]
            since_seq_str = query.get("since_seq", query.get("since", ["0"]))[0]
            timeout_str = query.get("timeout", ["0.0"])[0]
            try:
                since_seq = int(since_seq_str)
            except ValueError:
                since_seq = 0
            try:
                timeout = float(timeout_str)
            except ValueError:
                timeout = 0.0

            if not address:
                self._send_json({"error": "Missing 'address' or 'addr' query parameter"}, 400)
                return
            try:
                res = tincan_relay.inbox(address, since_seq=since_seq, timeout=timeout)
                self._send_json(res)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as exc:
                self._send_json({"error": str(exc)}, 500)
        elif parsed.path == "/api/tincan/whoami":
            query = parse_qs(parsed.query)
            address = query.get("address", query.get("addr", [None]))[0]
            res = tincan_relay.whoami(address)
            self._send_json(res)
        elif parsed.path == "/install.sh":
            install_script_path = os.path.join(os.path.dirname(__file__), "install_peer.sh")
            if os.path.exists(install_script_path):
                with open(install_script_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/x-shellscript; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_response(404)
                self.end_headers()
        elif parsed.path == "/download/bundle.tar.gz":
            base_dir = os.path.dirname(os.path.abspath(__file__))
            buf = io.BytesIO()
            with tarfile.open(fileobj=buf, mode="w:gz") as tar:
                def exclude_cruft(tarinfo):
                    name = tarinfo.name
                    if ".git" in name or "__pycache__" in name or ".pytest_cache" in name or ".worktrees" in name:
                        return None
                    return tarinfo
                tar.add(base_dir, arcname="iot-federated-agent-memory", filter=exclude_cruft)
            archive_data = buf.getvalue()
            self.send_response(200)
            self.send_header("Content-Type", "application/gzip")
            self.send_header("Content-Disposition", 'attachment; filename="iot-federated-agent-memory.tar.gz"')
            self.send_header("Content-Length", str(len(archive_data)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(archive_data)
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
          <h2 class="font-bold text-white text-base">One-Line Curl Commands</h2>
        </div>
        <span class="text-xs bg-indigo-950 text-indigo-300 border border-indigo-800 px-2.5 py-1 rounded-md font-mono">Instant Terminal Access</span>
      </div>
      <p class="text-xs text-slate-400 mb-2">1. Install and setup peer mesh &amp; TinCan tools (no account needed):</p>
      <div class="bg-black/80 border border-slate-800 rounded-lg p-3 flex items-center justify-between font-mono text-sm mb-3">
        <code id="installCmd" class="text-emerald-400 select-all overflow-x-auto">curl -sSL https://iot-federated-agent-memory-production.up.railway.app/install.sh | bash</code>
        <button onclick="navigator.clipboard.writeText(document.getElementById('installCmd').innerText); alert('Copied install command!')" class="ml-4 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-sans font-semibold transition active:scale-95 shrink-0">
          Copy Curl
        </button>
      </div>

      <p class="text-xs text-slate-400 mb-2">2. Live AI Model Prompt over OpenRouter Gateway (Gemini 2.5, Claude 3.7, Grok, GPT-4o):</p>
      <div class="bg-black/80 border border-slate-800 rounded-lg p-3 flex items-center justify-between font-mono text-sm">
        <code id="chatCmd" class="text-cyan-400 select-all overflow-x-auto">curl -s -X POST https://iot-federated-agent-memory-production.up.railway.app/api/chat -H "Content-Type: application/json" -d '{"prompt":"Hello world!"}'</code>
        <button onclick="navigator.clipboard.writeText(document.getElementById('chatCmd').innerText); alert('Copied chat curl command!')" class="ml-4 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-sans font-semibold transition active:scale-95 shrink-0">
          Copy Curl
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
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
      <div class="bg-slate-900 border border-slate-800 p-5 rounded-xl">
        <h2 class="text-sm font-semibold text-slate-400 uppercase tracking-wider">TinCan Blind Relay</h2>
        <div class="text-xl font-bold text-amber-400 mt-2">Sealed Delivery</div>
        <div class="text-xs text-slate-400 mt-1">X25519 Ciphertext Mailboxes</div>
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
