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
        elif parsed.path == "/api/models/set":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                alias = data.get("alias")
                new_model = data.get("model")
                display_name = data.get("display_name")
                if not alias or not new_model:
                    self._send_json({"error": "Missing 'alias' or 'model'"}, 400)
                    return
                updated_config = router.set_model(alias, new_model, display_name)
                self._send_json({
                    "status": "updated",
                    "alias": alias,
                    "model": updated_config.model_alias,
                    "display_name": updated_config.display_name,
                }, 200)
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
            self._send_json(router.get_analytics()["providers"])
        elif parsed.path == "/api/models/analytics":
            self._send_json(router.get_analytics())
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

    <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
      <div class="flex justify-between items-center">
        <div>
          <h2 class="text-lg font-bold text-white">AI Model Gateway &amp; Usage Tracking</h2>
          <p class="text-xs text-slate-400">Live token metrics, spend per provider, and hot-swappable model configurations</p>
        </div>
        <div id="analyticsHeader" class="text-right text-xs font-mono text-emerald-400">
          Loading metrics...
        </div>
      </div>

      <!-- Live Provider Cards Grid -->
      <div id="providerCards" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Injected via JavaScript -->
      </div>

      <!-- Set / Change Model Form -->
      <div class="bg-slate-950/70 border border-slate-800 rounded-lg p-4">
        <h3 class="text-sm font-semibold text-slate-200 mb-2">Configure / Swap Model Target</h3>
        <div class="grid grid-cols-1 sm:grid-cols-4 gap-2 text-xs">
          <div>
            <label class="block text-slate-400 mb-1">Target Alias</label>
            <select id="aliasSelect" class="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-white font-mono">
              <option value="gemini-brain">gemini-brain</option>
              <option value="claude-brain">claude-brain</option>
              <option value="grok-brain">grok-brain</option>
              <option value="openai-brain">openai-brain</option>
            </select>
          </div>
          <div class="sm:col-span-2">
            <label class="block text-slate-400 mb-1">OpenRouter Model ID</label>
            <input type="text" id="modelInput" placeholder="e.g. meta-llama/llama-3.3-70b-instruct" class="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-white font-mono placeholder:text-slate-600">
          </div>
          <div class="flex items-end">
            <button onclick="updateModel()" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded px-3 py-1.5 transition active:scale-95">
              Update Model
            </button>
          </div>
        </div>
        <p id="updateFeedback" class="text-xs mt-2 font-mono hidden"></p>
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

  <script>
    async function loadAnalytics() {
      try {
        const res = await fetch('/api/models/analytics');
        const data = await res.json();
        document.getElementById('analyticsHeader').innerText = 
          `Total Calls: ${data.total_calls} | Tokens: ${data.total_tokens} | Spend: $${data.total_spend_usd.toFixed(4)}`;
        
        const container = document.getElementById('providerCards');
        container.innerHTML = '';
        for (const [alias, info] of Object.entries(data.providers)) {
          const card = document.createElement('div');
          card.className = 'p-3 bg-slate-800/60 rounded-lg border border-slate-700/80 space-y-1.5 font-mono text-xs';
          card.innerHTML = `
            <div class="flex justify-between items-center">
              <span class="font-bold text-white">${alias}</span>
              <span class="text-xs bg-indigo-950 text-indigo-300 px-2 py-0.5 rounded border border-indigo-800">${info.display_name}</span>
            </div>
            <div class="text-slate-300 truncate"><span class="text-slate-500">Model:</span> ${info.model}</div>
            <div class="grid grid-cols-3 gap-1 pt-1 text-slate-400 border-t border-slate-700/50">
              <div><span class="text-slate-500">Calls:</span> <span class="text-white">${info.total_calls}</span></div>
              <div><span class="text-slate-500">Tokens:</span> <span class="text-white">${info.total_tokens}</span></div>
              <div><span class="text-slate-500">Cost:</span> <span class="text-emerald-400">$${info.cost_usd.toFixed(4)}</span></div>
            </div>
          `;
          container.appendChild(card);
        }
      } catch (e) {
        console.error('Failed to load analytics', e);
      }
    }

    async function updateModel() {
      const alias = document.getElementById('aliasSelect').value;
      const model = document.getElementById('modelInput').value.trim();
      const fb = document.getElementById('updateFeedback');
      if (!model) {
        fb.innerText = 'Please enter a valid model identifier';
        fb.className = 'text-xs mt-2 font-mono text-red-400';
        return;
      }
      try {
        const res = await fetch('/api/models/set', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({alias, model})
        });
        const resp = await res.json();
        if (res.ok) {
          fb.innerText = `✓ Updated ${resp.alias} -> ${resp.model}`;
          fb.className = 'text-xs mt-2 font-mono text-emerald-400';
          document.getElementById('modelInput').value = '';
          loadAnalytics();
        } else {
          fb.innerText = `Error: ${resp.error}`;
          fb.className = 'text-xs mt-2 font-mono text-red-400';
        }
      } catch (err) {
        fb.innerText = `Request failed: ${err.message}`;
        fb.className = 'text-xs mt-2 font-mono text-red-400';
      }
    }

    loadAnalytics();
    setInterval(loadAnalytics, 5000);
  </script>
</body>
</html>
"""

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), MeshGatewayHandler)
    print(f"[*] IoT Federated Agent Mesh listening on port {PORT}")
    server.serve_forever()
