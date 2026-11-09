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
from iot_federated_agent_memory.video_playlist import RelayVideoPlaylist

PORT = int(os.environ.get("PORT", 8080))

relay = WebRTCSignalingRelay()
router = DynamicAIGatewayRouter()
scale = IoTFederatedMemoryScale()
tincan_relay = TinCanBlindRelay()
playlist = RelayVideoPlaylist()

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
        elif parsed.path == "/api/webrtc/register":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = data.get("peer_id")
                display_name = data.get("display_name") or peer_id or "Peer"
                if not peer_id:
                    self._send_json({"error": "Missing 'peer_id'"}, 400)
                    return
                session = relay.register_peer(
                    peer_id=peer_id,
                    display_name=display_name,
                    udp_address=data.get("udp_address", self.client_address[0] if self.client_address else "127.0.0.1"),
                    udp_port=int(data.get("udp_port", 50000)),
                    room=data.get("room", "main"),
                    has_video=bool(data.get("has_video", True)),
                    has_audio=bool(data.get("has_audio", True)),
                    has_screen=bool(data.get("has_screen", False)),
                )
                self._send_json({
                    "status": "registered",
                    "peer_id": session.peer_id,
                    "room": session.room,
                    "peers": relay.get_room_peers(session.room),
                }, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/webrtc/signal":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                sender_id = data.get("from") or data.get("sender_id")
                receiver_id = data.get("to") or data.get("receiver_id") or "*"
                signal_type = data.get("type") or data.get("signal_type")
                payload = data.get("payload") or {}
                room = data.get("room", "main")
                if not sender_id or not signal_type:
                    self._send_json({"error": "Missing 'from' or 'type'"}, 400)
                    return
                msg = relay.exchange_signal(
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    signal_type=signal_type,
                    sdp_or_candidate=payload,
                    room=room,
                )
                self._send_json({"status": "signaled", "signal": msg}, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/webrtc/leave":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = data.get("peer_id")
                room = data.get("room", "main")
                if not peer_id:
                    self._send_json({"error": "Missing 'peer_id'"}, 400)
                    return
                left = relay.leave_peer(peer_id)
                relay.exchange_signal(peer_id, "*", "hangup", {"peer_id": peer_id}, room=room)
                self._send_json({"status": "left", "peer_id": peer_id, "removed": left}, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/playlist/add":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                raw_input = data.get("url") or data.get("input") or data.get("video_id") or data.get("embed")
                if not raw_input:
                    self._send_json({"error": "Missing 'url', 'input', or 'video_id'"}, 400)
                    return
                added = playlist.add_video(
                    raw_input=raw_input,
                    title=data.get("title"),
                    creator=data.get("creator"),
                    category=data.get("category", "spotlight"),
                    duration_seconds=int(data.get("duration_seconds", 35)),
                )
                self._send_json({
                    "status": "added",
                    "item": added,
                    "playlist": playlist.get_playlist(),
                }, 200)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/playlist/remove":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                vid = data.get("id") or data.get("video_id")
                if not vid:
                    self._send_json({"error": "Missing 'id' or 'video_id'"}, 400)
                    return
                removed = playlist.remove_video(vid)
                self._send_json({
                    "status": "removed" if removed else "not_found",
                    "playlist": playlist.get_playlist(),
                }, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/health", "/call", "/tv"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_UI.encode("utf-8"))
        elif parsed.path == "/api/playlist":
            self._send_json(playlist.get_playlist(), 200)
        elif parsed.path.startswith("/videos/") and parsed.path.endswith(".mp4"):
            from iot_federated_agent_memory.video_playlist import VIDEOS_DIR, download_tiktok_mp4
            import re

            fname = os.path.basename(parsed.path)
            vid = os.path.splitext(fname)[0]
            file_path = os.path.join(VIDEOS_DIR, f"{vid}.mp4")
            if not os.path.isfile(file_path):
                download_tiktok_mp4(vid, f"https://www.tiktok.com/@nojuannobody/video/{vid}", VIDEOS_DIR)

            if not os.path.isfile(file_path):
                self.send_response(404)
                self.end_headers()
                return

            file_size = os.path.getsize(file_path)
            range_header = self.headers.get("Range")
            if range_header:
                m = re.match(r"bytes=(\d+)-(\d*)", range_header)
                if m:
                    start = int(m.group(1))
                    end = int(m.group(2)) if m.group(2) else file_size - 1
                    end = min(end, file_size - 1)
                    length = max(0, end - start + 1)
                    with open(file_path, "rb") as f:
                        f.seek(start)
                        chunk = f.read(length)
                    self.send_response(206)
                    self.send_header("Content-Type", "video/mp4")
                    self.send_header("Accept-Ranges", "bytes")
                    self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                    self.send_header("Content-Length", str(len(chunk)))
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(chunk)
                    return

            with open(file_path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(file_size))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)
        elif parsed.path == "/api/webrtc/signals":
            query = parse_qs(parsed.query)
            peer_id = query.get("peer_id", query.get("peer", [None]))[0]
            room = query.get("room", ["main"])[0]
            since_str = query.get("since_seq", query.get("since", ["0"]))[0]
            try:
                since_seq = int(since_str)
            except ValueError:
                since_seq = 0
            if not peer_id:
                self._send_json({"error": "Missing 'peer_id' query parameter"}, 400)
                return
            self._send_json(relay.poll_signals(receiver_id=peer_id, room=room, since_seq=since_seq), 200)
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
        elif parsed.path == "/api/version":
            commit_hash = "2f7faf2"
            try:
                import subprocess
                out = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=os.path.dirname(__file__)).decode().strip()
                if out:
                    commit_hash = out
            except Exception:
                pass
            self._send_json({
                "service": "tincan",
                "commit": commit_hash,
                "version": "2.1.0",
                "relay_url": "https://iot-federated-agent-memory-production.up.railway.app",
            })
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

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      <!-- Left: Quickstart & One-Line Curl Commands -->
      <div class="lg:col-span-7 bg-slate-900 border border-indigo-900/60 rounded-xl p-5 shadow-2xl space-y-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-xl">⚡</span>
            <h2 class="font-bold text-white text-base">Quickstart &amp; One-Line Curl Commands</h2>
          </div>
          <span class="text-xs bg-indigo-950 text-indigo-300 border border-indigo-800 px-2.5 py-1 rounded-md font-mono">Instant Terminal Access</span>
        </div>

        <div>
          <p class="text-xs text-slate-400 mb-2">1. Install &amp; setup peer mesh + TinCan CLI (no account needed):</p>
          <div class="bg-black/80 border border-slate-800 rounded-lg p-3 flex items-center justify-between font-mono text-sm">
            <code id="installCmd" class="text-emerald-400 select-all overflow-x-auto">curl -sSL https://iot-federated-agent-memory-production.up.railway.app/install.sh | bash</code>
            <button onclick="navigator.clipboard.writeText(document.getElementById('installCmd').innerText); alert('Copied install command!')" class="ml-4 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-sans font-semibold transition active:scale-95 shrink-0">
              Copy Curl
            </button>
          </div>
        </div>

        <div>
          <p class="text-xs text-slate-400 mb-2">2. Live AI Model Prompt over OpenRouter Gateway (Gemini 2.5, Claude, Grok, GPT-4o):</p>
          <div class="bg-black/80 border border-slate-800 rounded-lg p-3 flex items-center justify-between font-mono text-sm">
            <code id="chatCmd" class="text-cyan-400 select-all overflow-x-auto">curl -s -X POST https://iot-federated-agent-memory-production.up.railway.app/api/chat -H "Content-Type: application/json" -d '{"prompt":"Hello world!"}'</code>
            <button onclick="navigator.clipboard.writeText(document.getElementById('chatCmd').innerText); alert('Copied chat curl command!')" class="ml-4 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-sans font-semibold transition active:scale-95 shrink-0">
              Copy Curl
            </button>
          </div>
        </div>

        <div class="bg-slate-950/80 border border-slate-800 rounded-lg p-4 space-y-2">
          <div class="flex items-center justify-between">
            <h3 class="text-xs font-bold uppercase tracking-wider text-amber-400">TinCan Voice, Video &amp; Mesh Cheat Sheet</h3>
            <span class="text-[11px] font-mono text-slate-400">Watch the @nojuannobody walkthrough →</span>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 font-mono text-xs">
            <div class="p-2 bg-slate-900 rounded border border-slate-800">
              <div class="text-slate-400 text-[10px]">Speak + Send Remote TTS</div>
              <div class="text-emerald-300 mt-0.5">tincan say "Hey!" --to peer1</div>
            </div>
            <div class="p-2 bg-slate-900 rounded border border-slate-800">
              <div class="text-slate-400 text-[10px]">Live 2-Way Voice Call</div>
              <div class="text-cyan-300 mt-0.5">tincan call peer1 --voice-only</div>
            </div>
            <div class="p-2 bg-slate-900 rounded border border-slate-800">
              <div class="text-slate-400 text-[10px]">Live Video / Screenshare</div>
              <div class="text-indigo-300 mt-0.5">tincan call peer1 --screen</div>
            </div>
            <div class="p-2 bg-slate-900 rounded border border-slate-800">
              <div class="text-slate-400 text-[10px]">Approve Queued Peer Action</div>
              <div class="text-amber-300 mt-0.5">tincan trigger 1</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Relay Autoplaying Native MP4 Video Channel & Collection Player (Zero External Links) -->
      <div id="tv" class="lg:col-span-5 bg-slate-900 border border-pink-900/60 rounded-xl p-5 shadow-2xl flex flex-col space-y-3">
        <div class="w-full flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-lg">📺</span>
            <div>
              <h2 class="font-bold text-white text-sm">Relay Video Channel &amp; Collection</h2>
              <p id="nowPlayingTitle" class="text-[11px] text-slate-400">Self-hosted Native MP4 · <span class="text-pink-400 font-mono">@nojuannobody</span></p>
            </div>
          </div>
          <span id="playlistCounterBadge" class="text-[10px] bg-pink-950 text-pink-300 border border-pink-800 px-2.5 py-0.5 rounded-full font-mono uppercase">1 / 1 · Loop</span>
        </div>

        <!-- Self-Hosted Native HTML5 MP4 Player (Zero TikTok Links or Redirects) -->
        <div class="w-full flex flex-col items-center justify-center overflow-hidden rounded-lg bg-black border border-slate-800 relative h-[520px]">
          <video
            id="relayNativeVideo"
            src="/videos/7705677376465767711.mp4"
            autoplay
            loop
            muted
            playsinline
            controls
            class="w-full h-full object-contain bg-black"
          ></video>
        </div>

        <!-- Playlist Controls -->
        <div class="flex items-center justify-between gap-2 text-xs font-mono">
          <div class="flex items-center gap-1.5">
            <button onclick="prevPlaylistVideo()" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 transition">⏮ Prev</button>
            <button onclick="nextPlaylistVideo()" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 transition">Next ⏭</button>
            <button id="autoRotateBtn" onclick="toggleAutoRotate()" class="px-2.5 py-1 bg-emerald-950 text-emerald-300 rounded border border-emerald-800 transition">🔁 Auto-Loop: ON</button>
          </div>
          <button id="soundToggleBtn" onclick="toggleVideoSound()" class="px-2.5 py-1 bg-pink-950 hover:bg-pink-900 text-pink-300 rounded border border-pink-800 transition">
            🔊 Tap to Unmute
          </button>
        </div>

        <!-- Collection Queue List -->
        <div id="playlistQueue" class="space-y-1 max-h-28 overflow-y-auto pr-1 text-xs font-mono">
          <!-- Populated dynamically from /api/playlist -->
        </div>

        <!-- Add Video to Collection Form -->
        <div class="pt-2 border-t border-slate-800 flex gap-1.5 text-xs">
          <input id="newVideoInput" type="text" placeholder="Paste video URL or ID to ingest MP4 into relay collection..." class="flex-1 bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white font-mono placeholder:text-slate-600">
          <button onclick="addVideoToPlaylist()" class="px-3 py-1.5 bg-pink-600 hover:bg-pink-500 text-white font-semibold rounded transition shrink-0">
            + Ingest MP4
          </button>
        </div>
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

    <div id="call" class="bg-slate-900 border border-cyan-800/70 rounded-xl p-5 space-y-4 shadow-2xl">
      <div class="flex flex-wrap justify-between items-center gap-3">
        <div>
          <h2 class="text-lg font-bold text-white flex items-center gap-2">
            <span>📹</span> Live WebRTC Video, Voice &amp; Screenshare Studio
          </h2>
          <p class="text-xs text-slate-400">Peer-to-peer encrypted WebRTC camera, microphone voice calling, and H.264 desktop screenshare</p>
        </div>
        <div class="flex items-center gap-2 text-xs font-mono">
          <span class="text-slate-400">Room:</span>
          <input id="roomInput" type="text" value="main" class="bg-slate-950 border border-slate-700 rounded px-2.5 py-1 text-cyan-300 w-28">
          <button onclick="copyInviteLink()" class="px-3 py-1 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded text-slate-200 transition">
            Copy Invite Link
          </button>
          <span id="callStatusBadge" class="px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">Idle</span>
        </div>
      </div>

      <!-- Control Bar -->
      <div class="flex flex-wrap gap-2">
        <button onclick="startCall('video')" class="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg transition active:scale-95">
          🎥 Start Video + Voice
        </button>
        <button onclick="startCall('voice')" class="px-3.5 py-2 bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold rounded-lg transition active:scale-95">
          🎙️ Voice-Only Call
        </button>
        <button onclick="startScreenShare()" class="px-3.5 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold rounded-lg transition active:scale-95">
          🖥️ Share Screen
        </button>
        <button id="muteBtn" onclick="toggleMute()" class="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition">
          🔇 Mute Mic
        </button>
        <button id="camBtn" onclick="toggleCamera()" class="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition">
          📷 Toggle Cam
        </button>
        <button onclick="hangupCall()" class="px-3.5 py-2 bg-rose-700 hover:bg-rose-600 text-white text-xs font-semibold rounded-lg transition ml-auto">
          ⏹ End Call
        </button>
      </div>

      <!-- Video / Audio Viewports -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="relative bg-black rounded-lg border border-slate-800 overflow-hidden aspect-video flex items-center justify-center">
          <video id="localVideo" autoplay playsinline muted class="w-full h-full object-cover"></video>
          <div class="absolute bottom-2 left-2 px-2 py-0.5 bg-black/75 rounded text-xs font-mono text-emerald-300 border border-emerald-900">
            Local (<span id="localPeerLabel">you</span>)
          </div>
        </div>
        <div class="relative bg-black rounded-lg border border-slate-800 overflow-hidden aspect-video flex items-center justify-center">
          <video id="remoteVideo" autoplay playsinline class="w-full h-full object-cover"></video>
          <div class="absolute bottom-2 left-2 px-2 py-0.5 bg-black/75 rounded text-xs font-mono text-cyan-300 border border-cyan-900">
            Remote Peer (<span id="remotePeerLabel">waiting for peer...</span>)
          </div>
        </div>
      </div>

      <!-- Active Peers in Room -->
      <div class="pt-2 border-t border-slate-800/80">
        <div class="text-xs font-semibold text-slate-400 mb-2">Active Room &amp; UDP Streams</div>
        <div id="roomPeersGrid" class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
          <div class="p-3 bg-slate-800/60 rounded-lg border border-slate-700 flex justify-between items-center">
            <span class="text-white">Mac Studio (M1 Max)</span>
            <span class="bg-emerald-900 text-emerald-300 px-2 py-0.5 rounded">UDP: 50004</span>
          </div>
          <div class="p-3 bg-slate-800/60 rounded-lg border border-slate-700 flex justify-between items-center">
            <span class="text-white">Collaborator MacBook</span>
            <span class="bg-cyan-900 text-cyan-300 px-2 py-0.5 rounded">UDP: 50006</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    const urlParams = new URLSearchParams(window.location.search);
    const myPeerId = urlParams.get('peer') || ('peer-' + Math.random().toString(36).substring(2, 8));
    const initialRoom = urlParams.get('room') || 'main';
    document.getElementById('roomInput').value = initialRoom;
    document.getElementById('localPeerLabel').innerText = myPeerId;

    let pc = null;
    let localStream = null;
    let lastSignalSeq = 0;
    let pollTimer = null;
    let isMuted = false;
    let isCamOff = false;

    const rtcConfig = {
      iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
      ]
    };

    function setCallStatus(text, tone = 'slate') {
      const badge = document.getElementById('callStatusBadge');
      badge.innerText = text;
      badge.className = `px-2.5 py-1 rounded border text-xs font-mono bg-${tone}-950 text-${tone}-300 border-${tone}-800`;
    }

    function copyInviteLink() {
      const room = document.getElementById('roomInput').value.trim() || 'main';
      const inviteUrl = `${window.location.origin}/?room=${encodeURIComponent(room)}#call`;
      navigator.clipboard.writeText(inviteUrl);
      alert('Copied WebRTC room invite link: ' + inviteUrl);
    }

    async function sendSignal(type, payload, to = '*') {
      const room = document.getElementById('roomInput').value.trim() || 'main';
      await fetch('/api/webrtc/signal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from: myPeerId, to, room, type, payload })
      });
    }

    function ensurePeerConnection() {
      if (pc) return pc;
      pc = new RTCPeerConnection(rtcConfig);
      pc.onicecandidate = (ev) => {
        if (ev.candidate) {
          sendSignal('candidate', { candidate: ev.candidate });
        }
      };
      pc.ontrack = (ev) => {
        const remoteVideo = document.getElementById('remoteVideo');
        if (ev.streams && ev.streams[0]) {
          remoteVideo.srcObject = ev.streams[0];
          setCallStatus('Connected (Live Media)', 'emerald');
        }
      };
      if (localStream) {
        localStream.getTracks().forEach(track => pc.addTrack(track, localStream));
      }
      return pc;
    }

    async function startCall(mode = 'video') {
      try {
        const room = document.getElementById('roomInput').value.trim() || 'main';
        setCallStatus('Requesting mic/cam...', 'amber');
        localStream = await navigator.mediaDevices.getUserMedia({
          video: mode === 'video',
          audio: true
        });
        document.getElementById('localVideo').srcObject = localStream;

        await fetch('/api/webrtc/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            display_name: myPeerId,
            room,
            has_video: mode === 'video',
            has_audio: true,
            has_screen: false
          })
        });

        ensurePeerConnection();
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        await sendSignal('offer', { sdp: pc.localDescription });
        setCallStatus('Calling room ' + room + '...', 'cyan');
        if (!pollTimer) pollTimer = setInterval(pollSignals, 1200);
      } catch (err) {
        setCallStatus('Media error: ' + err.message, 'rose');
      }
    }

    async function startScreenShare() {
      try {
        const room = document.getElementById('roomInput').value.trim() || 'main';
        const screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
        localStream = screenStream;
        document.getElementById('localVideo').srcObject = screenStream;

        await fetch('/api/webrtc/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            display_name: myPeerId + ' (Screen)',
            room,
            has_video: true,
            has_audio: true,
            has_screen: true
          })
        });

        ensurePeerConnection();
        const videoTrack = screenStream.getVideoTracks()[0];
        const sender = pc.getSenders().find(s => s.track && s.track.kind === 'video');
        if (sender && videoTrack) {
          await sender.replaceTrack(videoTrack);
        } else {
          screenStream.getTracks().forEach(t => pc.addTrack(t, screenStream));
        }
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        await sendSignal('offer', { sdp: pc.localDescription });
        setCallStatus('Sharing Screen in ' + room, 'cyan');
        if (!pollTimer) pollTimer = setInterval(pollSignals, 1200);
      } catch (err) {
        setCallStatus('Screenshare error: ' + err.message, 'rose');
      }
    }

    function toggleMute() {
      if (!localStream) return;
      isMuted = !isMuted;
      localStream.getAudioTracks().forEach(t => { t.enabled = !isMuted; });
      document.getElementById('muteBtn').innerText = isMuted ? '🔊 Unmute Mic' : '🔇 Mute Mic';
    }

    function toggleCamera() {
      if (!localStream) return;
      isCamOff = !isCamOff;
      localStream.getVideoTracks().forEach(t => { t.enabled = !isCamOff; });
      document.getElementById('camBtn').innerText = isCamOff ? '📷 Cam On' : '📷 Toggle Cam';
    }

    async function hangupCall() {
      const room = document.getElementById('roomInput').value.trim() || 'main';
      if (localStream) {
        localStream.getTracks().forEach(t => t.stop());
        localStream = null;
      }
      if (pc) {
        pc.close();
        pc = null;
      }
      document.getElementById('localVideo').srcObject = null;
      document.getElementById('remoteVideo').srcObject = null;
      document.getElementById('remotePeerLabel').innerText = 'waiting for peer...';
      await fetch('/api/webrtc/leave', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ peer_id: myPeerId, room })
      });
      setCallStatus('Call Ended', 'slate');
    }

    async function pollSignals() {
      try {
        const room = document.getElementById('roomInput').value.trim() || 'main';
        const res = await fetch(`/api/webrtc/signals?peer_id=${encodeURIComponent(myPeerId)}&room=${encodeURIComponent(room)}&since_seq=${lastSignalSeq}`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.latest_seq && data.latest_seq > lastSignalSeq) {
          lastSignalSeq = data.latest_seq;
        }
        if (data.peers) {
          const grid = document.getElementById('roomPeersGrid');
          grid.innerHTML = data.peers.map(p => `
            <div class="p-3 bg-slate-800/60 rounded-lg border border-slate-700 flex justify-between items-center">
              <span class="text-white">${p.display_name}</span>
              <span class="bg-emerald-900 text-emerald-300 px-2 py-0.5 rounded">${p.has_screen ? 'SCREEN' : (p.has_video ? 'VIDEO+VOICE' : 'VOICE')} · UDP:${p.udp_port}</span>
            </div>
          `).join('');
        }
        for (const sig of (data.signals || [])) {
          document.getElementById('remotePeerLabel').innerText = sig.from;
          if (sig.type === 'offer' && sig.payload && sig.payload.sdp) {
            ensurePeerConnection();
            await pc.setRemoteDescription(new RTCSessionDescription(sig.payload.sdp));
            const answer = await pc.createAnswer();
            await pc.setLocalDescription(answer);
            await sendSignal('answer', { sdp: pc.localDescription }, sig.from);
            setCallStatus('Connected with ' + sig.from, 'emerald');
          } else if (sig.type === 'answer' && sig.payload && sig.payload.sdp && pc) {
            await pc.setRemoteDescription(new RTCSessionDescription(sig.payload.sdp));
            setCallStatus('Connected with ' + sig.from, 'emerald');
          } else if (sig.type === 'candidate' && sig.payload && sig.payload.candidate && pc) {
            try {
              await pc.addIceCandidate(new RTCIceCandidate(sig.payload.candidate));
            } catch (e) {}
          } else if (sig.type === 'hangup') {
            document.getElementById('remoteVideo').srcObject = null;
            document.getElementById('remotePeerLabel').innerText = 'peer hung up';
            setCallStatus('Peer disconnected', 'amber');
          }
        }
      } catch (e) {}
    }

    pollTimer = setInterval(pollSignals, 2000);
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

    // =========================================================================
    // Relay Video Channel & Auto-Rotating Playlist Engine
    // =========================================================================
    let playlistVideos = [];
    let currentVideoIdx = 0;
    let autoRotateEnabled = true;
    let rotateTimer = null;
    let useBlockquoteMode = false;

    async function loadPlaylist(preserveIndex = true) {
      try {
        const res = await fetch('/api/playlist');
        if (!res.ok) return;
        const data = await res.json();
        playlistVideos = data.videos || [];
        if (!preserveIndex || currentVideoIdx >= playlistVideos.length) {
          currentVideoIdx = 0;
        }
        renderPlaylistUI();
      } catch (e) {}
    }

    function renderPlaylistUI() {
      const total = playlistVideos.length;
      const badge = document.getElementById('playlistCounterBadge');
      const queue = document.getElementById('playlistQueue');
      if (!total) {
        badge.innerText = '0 / 0';
        queue.innerHTML = '<div class="text-slate-500">No videos in collection</div>';
        return;
      }

      const item = playlistVideos[currentVideoIdx];
      badge.innerText = `${currentVideoIdx + 1} / ${total} · ${autoRotateEnabled ? 'Loop' : 'Paused'}`;
      document.getElementById('nowPlayingTitle').innerHTML =
        `${item.title} · <span class="text-pink-400 font-mono">${item.creator}</span>`;

      const vidEl = document.getElementById('relayNativeVideo');
      const targetSrc = item.embed_url || `/videos/${item.video_id}.mp4`;
      if (vidEl) {
        vidEl.loop = (total === 1 && autoRotateEnabled);
        if (vidEl.getAttribute('data-vid') !== item.id) {
          vidEl.setAttribute('data-vid', item.id);
          vidEl.src = targetSrc;
          vidEl.play().catch(() => {});
        }
      }

      queue.innerHTML = playlistVideos.map((v, idx) => `
        <div onclick="selectPlaylistVideo(${idx})" class="cursor-pointer px-2.5 py-1.5 rounded border flex justify-between items-center transition ${idx === currentVideoIdx ? 'bg-pink-950/60 border-pink-700 text-white' : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'}">
          <span class="truncate">${idx + 1}. ${v.title} (${v.creator})</span>
          <span class="text-[10px] uppercase px-1.5 py-0.5 rounded bg-slate-900 text-slate-300 ml-2 shrink-0">${v.category}</span>
        </div>
      `).join('');
    }

    function scheduleAutoAdvance(seconds) {
      if (rotateTimer) clearTimeout(rotateTimer);
      if (!autoRotateEnabled || playlistVideos.length <= 1) return;
      rotateTimer = setTimeout(() => {
        nextPlaylistVideo();
      }, (seconds || 35) * 1000);
    }

    function selectPlaylistVideo(idx) {
      if (idx < 0 || idx >= playlistVideos.length) return;
      currentVideoIdx = idx;
      renderPlaylistUI();
    }

    function nextPlaylistVideo() {
      if (!playlistVideos.length) return;
      currentVideoIdx = (currentVideoIdx + 1) % playlistVideos.length;
      renderPlaylistUI();
    }

    function prevPlaylistVideo() {
      if (!playlistVideos.length) return;
      currentVideoIdx = (currentVideoIdx - 1 + playlistVideos.length) % playlistVideos.length;
      renderPlaylistUI();
    }

    function toggleAutoRotate() {
      autoRotateEnabled = !autoRotateEnabled;
      const btn = document.getElementById('autoRotateBtn');
      btn.innerText = autoRotateEnabled ? '🔁 Auto-Loop: ON' : '⏸ Auto-Loop: OFF';
      btn.className = autoRotateEnabled
        ? 'px-2.5 py-1 bg-emerald-950 text-emerald-300 rounded border border-emerald-800 transition'
        : 'px-2.5 py-1 bg-slate-800 text-slate-400 rounded border border-slate-700 transition';
      renderPlaylistUI();
    }

    function toggleVideoSound() {
      const vidEl = document.getElementById('relayNativeVideo');
      const btn = document.getElementById('soundToggleBtn');
      if (!vidEl) return;
      vidEl.muted = !vidEl.muted;
      btn.innerText = vidEl.muted ? '🔊 Tap to Unmute' : '🔇 Mute Audio';
      vidEl.play().catch(() => {});
    }

    document.getElementById('relayNativeVideo').addEventListener('ended', () => {
      if (autoRotateEnabled && playlistVideos.length > 1) {
        nextPlaylistVideo();
      } else if (autoRotateEnabled && playlistVideos.length === 1) {
        const vidEl = document.getElementById('relayNativeVideo');
        vidEl.currentTime = 0;
        vidEl.play().catch(() => {});
      }
    });

    async function addVideoToPlaylist() {
      const inp = document.getElementById('newVideoInput');
      const raw = inp.value.trim();
      if (!raw) return;
      try {
        const res = await fetch('/api/playlist/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ input: raw, category: 'spotlight' })
        });
        const data = await res.json();
        if (res.ok) {
          inp.value = '';
          playlistVideos = data.playlist.videos || [];
          currentVideoIdx = playlistVideos.length - 1;
          renderPlaylistUI();
        } else {
          alert('Could not add video: ' + (data.error || 'Unknown error'));
        }
      } catch (err) {
        alert('Failed to add video: ' + err.message);
      }
    }

    // Listen for TikTok Player v1 postMessage events (e.g. video ended -> advance to next in collection)
    window.addEventListener('message', (event) => {
      try {
        const msg = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
        if (msg && msg['x-tiktok-player'] && msg.type === 'onStateChange' && msg.value === 0) {
          if (autoRotateEnabled && playlistVideos.length > 1) {
            nextPlaylistVideo();
          }
        }
      } catch (e) {}
    });

    loadPlaylist(false);
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
