"""Tests for 2D image generation, .space agent action routing, raw file preview, and model capability grounding."""

import base64
import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from iot_federated_agent_memory.agent_space import (
    AgentSpaceHarness,
    AgentSpaceManager,
    SingleFileSpaceVFS,
    build_space_context_summary,
    build_tincan_capability_manifest,
)
from iot_federated_agent_memory.ai_gateway import DynamicAIGatewayRouter
from iot_federated_agent_memory.shell_component import SHELL_JS

# Minimal 1x1 valid PNG binary
_TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
_TINY_JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"


class _DummyHTTPResp:
    def __init__(self, payload: dict, status: int = 200):
        self._body = json.dumps(payload).encode("utf-8")
        self.status = status
        self.headers = {"Content-Type": "application/json"}

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_dispatch_image_generation_openrouter_images_and_fallback(monkeypatch):
    router = DynamicAIGatewayRouter(openrouter_key="or-test-key", nanogpt_key="")
    calls = []

    def fake_urlopen(req, timeout=60.0):
        payload = json.loads(req.data.decode("utf-8"))
        calls.append({"url": req.full_url, "payload": payload})
        if len(calls) == 1:
            # Verify primary OpenRouter images list extraction
            return _DummyHTTPResp(
                {
                    "id": "gen-img-1",
                    "model": "google/gemini-2.5-flash-image",
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": "Rendered a crisp illustration of Pikachu.",
                                "images": [
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": "data:image/png;base64,"
                                            + base64.b64encode(_TINY_PNG).decode("ascii")
                                        },
                                    }
                                ],
                            }
                        }
                    ],
                    "usage": {"prompt_tokens": 12, "completion_tokens": 100, "total_tokens": 112, "cost": 0.039},
                }
            )
        if len(calls) == 2:
            raise urllib.error.HTTPError(
                req.full_url,
                404,
                "Not Found",
                hdrs={},
                fp=None,
            )
        # Fallback model returns markdown data URL (JPEG)
        return _DummyHTTPResp(
            {
                "id": "gen-img-2",
                "model": router.FALLBACK_IMAGE_MODEL,
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Here is Pikachu:\n\n![pikachu](data:image/jpeg;base64,"
                            + base64.b64encode(_TINY_JPEG).decode("ascii")
                            + ")",
                        }
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 80, "total_tokens": 90, "cost": 0.04},
            }
        )

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    res1 = router.dispatch_image_generation("can you make a picture of pikachu?")
    assert res1["ok"] is True
    assert res1["gateway"] == "openrouter"
    assert res1["mime_type"] == "image/png"
    assert res1["ext"] == ".png"
    assert res1["image_bytes"] == _TINY_PNG
    assert calls[0]["payload"]["modalities"] == ["image", "text"]

    res2 = router.dispatch_image_generation("use the model to generate a picture of pikachu")
    assert res2["ok"] is True
    assert res2["model"] == router.FALLBACK_IMAGE_MODEL
    assert res2["mime_type"] == "image/jpeg"
    assert res2["ext"] == ".jpg"
    assert res2["image_bytes"] == _TINY_JPEG


def test_dispatch_image_generation_nanogpt_and_no_key(monkeypatch):
    router_none = DynamicAIGatewayRouter(openrouter_key="", nanogpt_key="", hyper3d_key="")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("NANOGPT_API_KEY", raising=False)
    err_res = router_none.dispatch_image_generation("picture of pikachu")
    assert err_res["ok"] is False
    assert "OPENROUTER_API_KEY" in err_res["error"]

    router_nano = DynamicAIGatewayRouter(openrouter_key="", nanogpt_key="ng-test-key", hyper3d_key="")
    seen = {}

    def fake_nano(req, timeout=60.0):
        seen["url"] = req.full_url
        seen["body"] = json.loads(req.data.decode("utf-8"))
        return _DummyHTTPResp(
            {
                "data": [
                    {
                        "b64_json": base64.b64encode(_TINY_PNG).decode("ascii"),
                        "revised_prompt": "Pikachu sprite",
                    }
                ],
                "cost": 0.04,
            }
        )

    monkeypatch.setattr(urllib.request, "urlopen", fake_nano)
    res = router_nano.dispatch_image_generation("picture of pikachu")
    assert res["ok"] is True
    assert res["gateway"] == "nanogpt"
    assert res["image_bytes"] == _TINY_PNG
    assert seen["url"] == router_nano.NANOGPT_IMAGE_ENDPOINT


def test_harness_replays_pikachu_trajectory_cleanly(tmp_path):
    vfs = SingleFileSpaceVFS(scope="user", owner_id="nojuan", base_dir=str(tmp_path))
    vfs.write_file(
        "/models3d/README.txt",
        "3D Models Directory for Hyper3D / Rodin generated .glb binary meshes.",
        mime_type="text/plain",
        updated_by="system",
    )

    class MockRouter:
        def __init__(self):
            self.providers = DynamicAIGatewayRouter(openrouter_key="", nanogpt_key="").providers
            self.image_calls = []
            self.chat_calls = []

        def get_available_models(self):
            return DynamicAIGatewayRouter(openrouter_key="", nanogpt_key="").get_available_models()

        def dispatch_image_generation(self, prompt, model=None):
            self.image_calls.append(prompt)
            return {
                "ok": True,
                "gateway": "openrouter",
                "model": "google/gemini-2.5-flash-image",
                "mime_type": "image/png",
                "ext": ".png",
                "size_bytes": len(_TINY_PNG),
                "image_bytes": _TINY_PNG,
                "caption": "Electric mouse mascot portrait.",
                "cost_usd": 0.039,
            }

        def dispatch_completion(self, alias, messages):
            self.chat_calls.append({"alias": alias, "messages": messages})
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "TinCan supports chat models (gemini-brain, claude-brain), 2D image models (google/gemini-2.5-flash-image), and Hyper3D Rodin 3D models.",
                        }
                    }
                ]
            }

    mock_router = MockRouter()
    harness = AgentSpaceHarness(vfs=vfs, ai_router=mock_router)

    # 1. "can you make a picture of pikachu?"
    r1 = harness.run_agent("can you make a picture of pikachu?", author="nojuan")
    assert "/images/pikachu.png" in r1["files_mutated"]
    assert r1["image_assets"][0]["ok"] is True
    assert "cannot create images" not in r1["reply"].lower()
    assert base64.b64decode(vfs.read_file("/images/pikachu.png", as_text=False)["content_b64"]) == _TINY_PNG

    # 2. "what models do?"
    r2 = harness.run_agent("what models do?", author="nojuan")
    assert r2["files_mutated"] == []
    assert len(mock_router.chat_calls) == 1
    sys_msg = mock_router.chat_calls[0]["messages"][0]["content"]
    assert "google/gemini-2.5-flash-image" in sys_msg
    assert "Hyper3D Rodin" in sys_msg
    assert "/models3d/README.txt" in sys_msg
    assert "limited to text" in sys_msg

    # 3. "use the model to generate a picture of pikachu"
    r3 = harness.run_agent("use the model to generate a picture of pikachu", author="nojuan")
    assert r3["rodin_assets"] == []
    assert "/images/pikachu_2.png" in r3["files_mutated"]
    assert len(mock_router.image_calls) == 2


def test_spongebob_rodin_and_followup_disambiguation(tmp_path):
    vfs = SingleFileSpaceVFS(scope="user", owner_id="spongebob_user", base_dir=str(tmp_path))

    class TrajectoryRouter:
        def __init__(self):
            self.providers = DynamicAIGatewayRouter(openrouter_key="", nanogpt_key="").providers
            self.image_calls = []
            self.rodin_calls = []
            self.chat_calls = []

        def get_available_models(self):
            return DynamicAIGatewayRouter(openrouter_key="", nanogpt_key="").get_available_models()

        def dispatch_image_generation(self, prompt, model=None):
            self.image_calls.append(prompt)
            return {
                "ok": True,
                "gateway": "openrouter",
                "model": "google/gemini-2.5-flash-image",
                "mime_type": "image/png",
                "ext": ".png",
                "size_bytes": len(_TINY_PNG),
                "image_bytes": _TINY_PNG,
                "caption": "",
                "cost_usd": 0.039,
            }

        def dispatch_rodin_generation(self, prompt, geometry_file_format="glb"):
            self.rodin_calls.append(prompt)
            return {"uuid": "rodin-test", "status": "Done"}

        def dispatch_completion(self, alias, messages):
            self.chat_calls.append(messages)
            return {
                "choices": [{"message": {"role": "assistant", "content": "Rodin generates 3D .glb meshes; 2D images use OpenRouter."}}]
            }

    rtr = TrajectoryRouter()
    h = AgentSpaceHarness(vfs=vfs, ai_router=rtr)

    # Typo "picutre" stripped cleanly from slug -> /images/spongebob.png
    t1 = h.run_agent("can you draw a picutre of spongebob?", author="nojuan")
    assert t1["files_mutated"] == ["/images/spongebob.png"]
    assert t1["rodin_assets"] == []

    # Follow-up "can you pass my prompt to an image model?" reuses prior subject cleanly
    t2 = h.run_agent("can you pass my prompt to an image model?", author="nojuan")
    assert t2["files_mutated"] == ["/images/spongebob_2.png"]
    assert t2["image_assets"][0]["ok"] is True

    # Bare "rodin" MUST NOT create a 3D asset or charge Rodin
    t3 = h.run_agent("rodin", author="nojuan")
    assert t3["rodin_assets"] == []
    assert t3["files_mutated"] == []
    assert len(rtr.rodin_calls) == 0
    assert len(rtr.chat_calls) == 1

    # "generate an image using rodin a picture of spongebob or pikachu" -> 2D image + strips "using rodin"
    t4 = h.run_agent("generate an image using rodin a picture of spongebob or pikachu", author="nojuan")
    assert t4["rodin_assets"] == []
    assert t4["files_mutated"] == ["/images/spongebob_or_pikachu.png"]
    assert "rodin" not in rtr.image_calls[-1].lower()
    assert "Hyper3D Rodin" in t4["reply"]

    # "a picture of a mouse" & "generate an image of a mouse using rodin" -> 2D images
    t5 = h.run_agent("a picture of a mouse", author="nojuan")
    assert t5["files_mutated"] == ["/images/mouse.png"]
    t6 = h.run_agent("generate an image of a mouse using rodin", author="nojuan")
    assert t6["rodin_assets"] == []
    assert t6["files_mutated"] == ["/images/mouse_2.png"]

    # Explicit 3D still triggers Rodin
    t7 = h.run_agent("generate a 3d model of pikachu with rodin", author="nojuan")
    assert len(t7["rodin_assets"]) == 1
    assert t7["rodin_assets"][0]["path"].startswith("/models3d/")


def test_harness_executes_tincan_action_blocks(tmp_path):
    vfs = SingleFileSpaceVFS(scope="user", owner_id="action_peer", base_dir=str(tmp_path))

    class ActionMockRouter:
        def dispatch_completion(self, alias, messages):
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": (
                                "Creating and running your script.\n"
                                "```tincan_action\n"
                                '[{"action":"write_file","path":"/src/hi.py","content":"print(\'HI_TINCAN_SPACE\')\\n"},'
                                '{"action":"exec_python","entrypoint":"/src/hi.py"}]\n'
                                "```"
                            ),
                        }
                    }
                ]
            }

    harness = AgentSpaceHarness(vfs=vfs, ai_router=ActionMockRouter())
    res = harness.run_agent("create a tiny python greeter and run it")
    assert "/src/hi.py" in res["files_mutated"]
    assert len(res["exec_results"]) == 1
    assert "HI_TINCAN_SPACE" in res["exec_results"][0]["stdout"]
    assert "```tincan_action" not in res["reply"]


def test_http_space_agent_chat_and_raw_file(tmp_path, monkeypatch):
    import tests.test_tincan_ux_updates as ux_mod

    srv = ux_mod.server
    temp_mgr = AgentSpaceManager(base_dir=str(tmp_path), ai_router=srv.router)
    monkeypatch.setattr(srv, "_space_manager", temp_mgr)
    monkeypatch.setattr(srv, "_get_space_manager", lambda: temp_mgr)
    monkeypatch.setattr(srv.account_registry, "get_account_by_peer", lambda p: None)

    captured_chat = {}

    def fake_dispatch(*, alias, messages, temperature=0.7, max_tokens=512):
        captured_chat["messages"] = messages
        return {
            "id": "sim-cap",
            "choices": [{"message": {"role": "assistant", "content": "TinCan model lineup response."}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

    def fake_image_gen(prompt, *, model=None, aspect_ratio=None, gateway=None, timeout=60.0):
        return {
            "ok": True,
            "gateway": "openrouter",
            "model": "google/gemini-2.5-flash-image",
            "mime_type": "image/png",
            "ext": ".png",
            "size_bytes": len(_TINY_PNG),
            "image_bytes": _TINY_PNG,
            "caption": "Electric Pikachu art",
            "cost_usd": 0.039,
        }

    monkeypatch.setattr(srv.router, "dispatch_completion", fake_dispatch)
    monkeypatch.setattr(srv.router, "dispatch_image_generation", fake_image_gen)

    with ux_mod._live_server() as (host, port):
        addr = f"http://{host}:{port}"
        # 1. /api/chat with use_space_context injects capability manifest inside the single system message
        req = urllib.request.Request(
            f"{addr}/api/chat",
            data=json.dumps(
                {
                    "model": "gemini-brain",
                    "prompt": "what models do?",
                    "scope": "user",
                    "owner_id": "nojuan",
                    "use_space_context": True,
                    "peer_id": "nojuan",
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            chat_data = json.loads(r.read().decode("utf-8"))
        assert chat_data["space_context"]["owner_id"] == "nojuan"
        assert len(captured_chat["messages"]) == 2
        assert "[TinCan AI Models, Media Generators, Tools & TUIs]" in captured_chat["messages"][0]["content"]

        # 2. /api/space/agent generates image & saves in .space
        req2 = urllib.request.Request(
            f"{addr}/api/space/agent",
            data=json.dumps(
                {
                    "scope": "user",
                    "owner_id": "nojuan",
                    "prompt": "can you make a picture of pikachu?",
                    "author": "nojuan",
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req2, timeout=15) as r2:
            agent_data = json.loads(r2.read().decode("utf-8"))
        assert "/images/pikachu.png" in agent_data["files_mutated"]
        assert agent_data["image_assets"][0]["ok"] is True

        # 3. GET /api/space/file?raw=1 serves raw binary image/png
        with urllib.request.urlopen(
            f"{addr}/api/space/file?scope=user&owner_id=nojuan&path=/images/pikachu.png&raw=1",
            timeout=15,
        ) as r3:
            raw_bytes = r3.read()
            ctype = r3.headers.get("Content-Type")
        assert ctype == "image/png"
        assert raw_bytes == _TINY_PNG


def test_terminal_js_routes_natural_language_and_renders_image():
    script = f"""
    const fetchCalls = [];
    const dispatched = [];
    const elems = {{}};
    function makeNode(tag) {{
      return {{
        tagName: tag.toUpperCase(),
        className: '',
        id: '',
        textContent: '',
        _innerHTML: '',
        style: {{}},
        children: [],
        classList: {{
          _s: new Set(),
          add(c) {{ this._s.add(c); }},
          remove(c) {{ this._s.delete(c); }},
          toggle(c, force) {{ if (force) this._s.add(c); else this._s.delete(c); }},
          contains(c) {{ return this._s.has(c); }},
        }},
        appendChild(ch) {{ this.children.push(ch); return ch; }},
        addEventListener() {{}},
        focus() {{}},
        scrollIntoView() {{}},
        querySelector(sel) {{
          const m = sel.match(/^\\.([\\w-]+)$/);
          if (!m) return null;
          const walk = (node) => {{
            for (const c of (node.children || [])) {{
              if (c.className && c.className.split(/\\s+/).includes(m[1])) return c;
              const hit = walk(c);
              if (hit) return hit;
            }}
            return null;
          }};
          return walk(this);
        }},
        set innerHTML(v) {{ this._innerHTML = String(v); this.children = []; }},
        get innerHTML() {{ return this._innerHTML; }},
      }};
    }}
    const root = makeNode('div');
    const document = {{
      getElementById: () => null,
      querySelectorAll: () => [],
      createElement: makeNode,
      addEventListener() {{}},
    }};
    const window = {{
      addEventListener() {{}},
      dispatchEvent(ev) {{ dispatched.push(ev); }},
    }};
    function CustomEvent(name, init) {{ return {{ type: name, detail: (init && init.detail) || {{}} }}; }}
    function setInterval() {{ return 0; }}
    function setTimeout() {{ return 0; }}
    const localStorage = {{ getItem: () => '', setItem() {{}} }};
    const myPeerId = 'nojuan';
    const currentSpaceScope = 'user';
    const currentSpaceOwner = 'nojuan';
    async function fetch(url, opts) {{
      const parsed = JSON.parse((opts && opts.body) || '{{}}');
      fetchCalls.push({{ url, body: parsed }});
      if (url === '/api/space/agent') {{
        return {{
          ok: true,
          status: 200,
          json: async () => ({{
            reply: 'Generated 2D image `/images/pikachu.png`',
            files_mutated: ['/images/pikachu.png'],
            image_assets: [{{ ok: true, path: '/images/pikachu.png', model: 'google/gemini-2.5-flash-image', size_bytes: 68 }}],
            rodin_assets: [],
          }}),
        }};
      }}
      if (url === '/api/chat') {{
        return {{
          ok: true,
          status: 200,
          json: async () => ({{ choices: [{{ message: {{ content: 'Model manifest reply' }} }}] }}),
        }};
      }}
      if (url === '/api/terminal/harness') {{
        return {{
          ok: true,
          status: 200,
          json: async () => ({{ status: 'ok', output: 'Goose saw /src/main.py', lines: ['Goose saw /src/main.py'], synced_files: [] }}),
        }};
      }}
      return {{ ok: true, status: 200, json: async () => ({{}}) }};
    }}
    {SHELL_JS}
    (async () => {{
      const r1 = await window.TinCanShell.run('can you make a picture of pikachu?');
      const r2 = await window.TinCanShell.run('ask what models do?');
      const r3 = await window.TinCanShell.run('ask make a picture of pikachu');
      const r4 = await window.TinCanShell.run('hey goose can you see my files');
      const r5 = await window.TinCanShell.run('hey goose draw spongebob');
      console.log(JSON.stringify({{ r1, r2, r3, r4, r5, fetchCalls, dispatched }}));
    }})();
    """
    proc = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)
    data = json.loads(proc.stdout.strip())
    assert data["fetchCalls"][0]["url"] == "/api/space/agent"
    assert "/images/pikachu.png" in data["r1"]["files_mutated"]
    assert "<img src=\"/api/space/file?scope=user&amp;owner_id=nojuan&amp;path=%2Fimages%2Fpikachu.png&amp;raw=1\"" in data["r1"]["html"]
    assert any(ev["type"] == "tincan:space-changed" for ev in data["dispatched"])
    assert data["fetchCalls"][1]["url"] == "/api/chat"
    assert data["fetchCalls"][1]["body"]["use_space_context"] is True
    assert data["fetchCalls"][2]["url"] == "/api/space/agent"
    assert data["fetchCalls"][3]["url"] == "/api/terminal/harness"
    assert data["fetchCalls"][3]["body"]["command"] == "goose can you see my files"
    assert data["fetchCalls"][4]["url"] == "/api/space/agent"


def test_rodin_fallback_host_and_glb_download(monkeypatch):
    router = DynamicAIGatewayRouter(hyper3d_key="test-h3d-key")
    seen_urls = []

    class _BinResp:
        def __init__(self, body: bytes):
            self._b = body

        def read(self):
            return self._b

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=30.0):
        seen_urls.append(req.full_url)
        if req.full_url == router.RODIN_GENERATE_URL and seen_urls.count(router.RODIN_GENERATE_URL) == 1:
            return _DummyHTTPResp({"error": "INVALID_REQUEST", "message": "unsupported field"})
        if req.full_url == router.RODIN_GENERATE_URL:
            raise urllib.error.HTTPError(req.full_url, 503, "Service Unavailable", hdrs={}, fp=None)
        if req.full_url == router.RODIN_FALLBACK_GENERATE_URL:
            return _DummyHTTPResp({"uuid": "real-uuid-9", "jobs": {"subscription_key": "live-sub-9"}, "status": "Waiting"})
        if req.full_url == router.RODIN_STATUS_URL:
            return _DummyHTTPResp({"status": "Done", "jobs": [{"uuid": "real-uuid-9", "status": "Done"}]})
        if req.full_url == router.RODIN_DOWNLOAD_URL:
            return _DummyHTTPResp({"list": [{"name": "goose.glb", "url": "https://cdn.example/goose.glb"}]})
        if req.full_url == "https://cdn.example/goose.glb":
            return _BinResp(b"glTFREAL_MESH_BYTES")
        raise AssertionError(f"Unexpected URL {req.full_url}")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    rec = router.dispatch_rodin_generation(prompt="3D goose")
    assert rec["simulated"] is False
    assert rec["uuid"] == "real-uuid-9"
    assert rec["subscription_key"] == "live-sub-9"
    hydrated = router.wait_for_rodin_glb(rec, max_wait_sec=5.0)
    assert hydrated.get("downloaded") is True
    assert base64.b64decode(hydrated["glb_bytes_b64"]) == b"glTFREAL_MESH_BYTES"
    assert router.RODIN_GENERATE_URL in seen_urls
    assert router.RODIN_FALLBACK_GENERATE_URL in seen_urls


def test_pty_tui_session_exposes_tincan_gen_and_capabilities(tmp_path, monkeypatch):
    import tests.test_tincan_ux_updates as ux_mod
    from iot_federated_agent_memory.pty_sessions import PTYSessionManager
    import time

    srv = ux_mod.server
    temp_mgr = AgentSpaceManager(base_dir=str(tmp_path), ai_router=srv.router)
    pty_mgr = PTYSessionManager()
    monkeypatch.setattr(srv, "_space_manager", temp_mgr)
    monkeypatch.setattr(srv, "_get_space_manager", lambda: temp_mgr)
    monkeypatch.setattr(srv, "_pty_manager", pty_mgr)
    monkeypatch.setattr(srv, "_get_pty_manager", lambda: pty_mgr)

    def fake_image_gen(prompt, *, model=None, aspect_ratio=None, gateway=None, timeout=60.0):
        return {
            "ok": True,
            "gateway": "openrouter",
            "model": "google/gemini-2.5-flash-image",
            "mime_type": "image/png",
            "ext": ".png",
            "size_bytes": len(_TINY_PNG),
            "image_bytes": _TINY_PNG,
            "caption": "Generated from TUI",
            "cost_usd": 0.039,
        }

    monkeypatch.setattr(srv.router, "dispatch_image_generation", fake_image_gen)
    monkeypatch.setattr(
        srv.router,
        "dispatch_rodin_generation",
        lambda prompt, **kw: {
            "uuid": "rodin-tui-mock",
            "subscription_key": "sub-tui-mock",
            "prompt": prompt,
            "tier": kw.get("tier", "Regular"),
            "format": "glb",
            "status": "Done",
            "simulated": True,
            "cost_usd": 0.5,
            "glb_bytes_b64": base64.b64encode(b"glTF\x02\x00\x00\x00\x0c\x00\x00\x00").decode("ascii"),
        },
    )
    monkeypatch.setenv("HYPER3D_API_KEY", "secret-should-not-leak-to-pty")

    with ux_mod._live_server() as (host, port):
        addr = f"http://{host}:{port}"
        req = urllib.request.Request(
            f"{addr}/api/terminal/pty/start",
            data=json.dumps({"harness": "bash", "scope": "user", "owner_id": "tui_tool_user"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            start_data = json.loads(r.read().decode("utf-8"))
        sid = start_data["session_id"]
        sess = pty_mgr.get(sid)
        assert sess is not None

        # Verify CLAUDE.md, AGENTS.md, GEMINI.md, and .tincan/SPACE_CONTEXT.md all exist & document tincan-gen
        for fn in ("AGENTS.md", "CLAUDE.md", "GEMINI.md", ".tincan/SPACE_CONTEXT.md"):
            content = Path(sess.tmpdir, fn).read_text(encoding="utf-8")
            assert "tincan-gen image" in content
            assert "tincan-gen 3d" in content

        # Execute tincan-gen image & tincan-gen 3d inside the live PTY bash session, confirming HYPER3D_API_KEY stays hidden
        cmd = (
            b"if printenv HYPER3D_API_KEY >/dev/null; then echo SECRET_WAS_FOUND; else echo SAFE_NO_KEY; fi; "
            b"tincan-gen image 'a cartoon sponge' && "
            b"tincan-gen 3d 'a 3d goose' --no-wait && "
            b"ls -la images/ models3d/ && printf 'TINCAN_GEN_%s\\n' 'DONE'\n"
        )
        sess.write(cmd)
        deadline = time.time() + 10.0
        collected = b""
        off = 0
        while time.time() < deadline:
            chunk, off, _ = sess.read_since(off, timeout=0.2)
            collected += chunk
            if b"TINCAN_GEN_DONE" in collected:
                break
        out_str = collected.decode("utf-8", errors="replace")
        assert "\nSAFE_NO_KEY" in out_str or "\r\nSAFE_NO_KEY" in out_str
        assert "\nSECRET_WAS_FOUND" not in out_str
        assert "TINCAN_GEN_DONE" in out_str
        assert Path(sess.tmpdir, "images", "cartoon_sponge.png").read_bytes() == _TINY_PNG
        assert Path(sess.tmpdir, "models3d", "goose.glb").read_bytes().startswith(b"glTF")

        sp = temp_mgr.get_space("user", "tui_tool_user")
        paths = {f["path"] for f in sp.list_files()}
        assert "/images/cartoon_sponge.png" in paths
        assert "/models3d/goose.glb" in paths
        pty_mgr.close(sid)


def test_nanogpt_rodin_v25_fallback_and_status_polling(monkeypatch):
    router = DynamicAIGatewayRouter(hyper3d_key="direct-no-sub-key", nanogpt_key="ng-live-key")
    calls = []

    class _BinResp:
        def __init__(self, body: bytes):
            self._b = body

        def read(self):
            return self._b

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=45.0):
        url = req.full_url
        calls.append({"url": url, "method": req.get_method(), "data": req.data})
        if url in (router.RODIN_GENERATE_URL, router.RODIN_FALLBACK_GENERATE_URL):
            return _DummyHTTPResp(
                {"error": "API_NO_ACTIVE_SUBSCRIPTION", "message": "Your account does not have API access."}
            )
        if url == router.NANOGPT_MEDIA_SUBMIT_URL:
            body = json.loads(req.data.decode("utf-8"))
            assert body == {"model": "hyper3d/rodin-v2.5", "prompt": "a stylized origami goose"}
            return _DummyHTTPResp(
                {"runId": "vid_rodin_nanogpt_123", "modelSlug": "hyper3d/rodin-v2.5", "status": "pending", "cost": 0.48}
            )
        if url.startswith(router.NANOGPT_MEDIA_STATUS_URL):
            return _DummyHTTPResp(
                {
                    "requestId": "vid_rodin_nanogpt_123",
                    "data": {
                        "status": "COMPLETED",
                        "output": {"model_url": "https://media.nano-gpt.cloud/assets/goose_rodin.glb"},
                    },
                }
            )
        if url == "https://media.nano-gpt.cloud/assets/goose_rodin.glb":
            return _BinResp(b"glTF_NANOGPT_RODIN_V25_REAL_MESH")
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    rec = router.dispatch_rodin_generation(prompt="a stylized origami goose", tier="Regular", mesh_mode="Quad")
    assert rec["simulated"] is False
    assert rec["gateway"] == "nanogpt"
    assert rec["model"] == "hyper3d/rodin-v2.5"
    assert rec["uuid"] == "vid_rodin_nanogpt_123"
    assert rec["glb_bytes_b64"] == ""
    assert "API_NO_ACTIVE_SUBSCRIPTION" in rec.get("hyper3d_direct_error", "")
    assert abs(rec["cost_usd"] - 0.48) < 1e-6

    hydrated = router.wait_for_rodin_glb(rec, max_wait_sec=10.0)
    assert hydrated.get("downloaded") is True
    assert hydrated["status"] == "Done"
    assert hydrated["url"] == "https://media.nano-gpt.cloud/assets/goose_rodin.glb"
    assert base64.b64decode(hydrated["glb_bytes_b64"]) == b"glTF_NANOGPT_RODIN_V25_REAL_MESH"


def test_nanogpt_3d_upstream_rejected_auto_fallback_to_tripo3d(monkeypatch):
    router = DynamicAIGatewayRouter(hyper3d_key="direct-no-sub-key", nanogpt_key="ng-live-key")
    submitted_models = []

    class _BinResp:
        def __init__(self, body: bytes):
            self._b = body

        def read(self):
            return self._b

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=45.0):
        url = req.full_url
        if url in (router.RODIN_GENERATE_URL, router.RODIN_FALLBACK_GENERATE_URL):
            return _DummyHTTPResp(
                {"error": "API_NO_ACTIVE_SUBSCRIPTION", "message": "Your account does not have API access."}
            )
        if url == router.NANOGPT_MEDIA_SUBMIT_URL:
            body = json.loads(req.data.decode("utf-8"))
            submitted_models.append(body["model"])
            if body["model"] == "hyper3d/rodin-v2.5":
                return _DummyHTTPResp(
                    {"runId": "vid_rodin_reject_1", "modelSlug": "hyper3d/rodin-v2.5", "status": "pending", "cost": 0.48}
                )
            if body["model"] == "tripo3d/h3.0":
                return _DummyHTTPResp(
                    {"runId": "vid_tripo_ok_2", "modelSlug": "tripo3d/h3.0", "status": "pending", "cost": 0.24}
                )
        if url.startswith(router.NANOGPT_MEDIA_STATUS_URL):
            if "vid_rodin_reject_1" in url:
                return _DummyHTTPResp(
                    {
                        "requestId": "vid_rodin_reject_1",
                        "data": {
                            "status": "FAILED",
                            "error": "Upstream service rejected the request. Please check your inputs and try again.",
                        },
                    }
                )
            if "vid_tripo_ok_2" in url:
                return _DummyHTTPResp(
                    {
                        "requestId": "vid_tripo_ok_2",
                        "data": {
                            "status": "COMPLETED",
                            "output": {"model_url": "https://media.nano-gpt.cloud/assets/mouse_tripo.glb"},
                        },
                    }
                )
        if url == "https://media.nano-gpt.cloud/assets/mouse_tripo.glb":
            return _BinResp(b"glTF_TRIPO3D_H3_REAL_MESH_BYTES")
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    rec = router.dispatch_rodin_generation(prompt="low poly stylized mouse", tier="Regular", mesh_mode="Quad")
    assert rec["uuid"] == "vid_rodin_reject_1"
    assert rec["model"] == "hyper3d/rodin-v2.5"

    hydrated = router.wait_for_rodin_glb(rec, max_wait_sec=12.0)
    assert submitted_models == ["hyper3d/rodin-v2.5", "tripo3d/h3.0"]
    assert hydrated["status"] == "Done"
    assert hydrated.get("downloaded") is True
    assert hydrated["model"] == "tripo3d/h3.0"
    assert hydrated["uuid"] == "vid_tripo_ok_2"
    assert hydrated.get("fallback_from") == "hyper3d/rodin-v2.5"
    assert abs(hydrated["cost_usd"] - 0.24) < 1e-6
    assert base64.b64decode(hydrated["glb_bytes_b64"]) == b"glTF_TRIPO3D_H3_REAL_MESH_BYTES"


def test_http_3d_async_does_not_save_triangle_placeholder_until_download(tmp_path, monkeypatch):
    import tests.test_tincan_ux_updates as ux_mod

    srv = ux_mod.server
    temp_mgr = AgentSpaceManager(base_dir=str(tmp_path), ai_router=srv.router)
    monkeypatch.setattr(srv, "_space_manager", temp_mgr)
    monkeypatch.setattr(srv, "_get_space_manager", lambda: temp_mgr)

    test_router = DynamicAIGatewayRouter(hyper3d_key=None, nanogpt_key="ng-http-key")
    monkeypatch.setattr(srv, "router", test_router)
    monkeypatch.setattr(ux_mod, "router", test_router, raising=False)

    orig_urlopen = urllib.request.urlopen

    class _BinResp:
        def __init__(self, body: bytes):
            self._b = body

        def read(self):
            return self._b

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=45.0):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if url.startswith("http://127.0.0.1") or url.startswith("http://localhost"):
            return orig_urlopen(req, timeout=timeout)
        if url == test_router.NANOGPT_MEDIA_SUBMIT_URL:
            body = json.loads(req.data.decode("utf-8"))
            if body["model"] == "hyper3d/rodin-v2.5":
                return _DummyHTTPResp({"runId": "vid_http_1", "modelSlug": "hyper3d/rodin-v2.5", "status": "pending", "cost": 0.48})
            if body["model"] == "tripo3d/h3.0":
                return _DummyHTTPResp({"runId": "vid_http_2", "modelSlug": "tripo3d/h3.0", "status": "pending", "cost": 0.24})
        if url.startswith(test_router.NANOGPT_MEDIA_STATUS_URL):
            if "vid_http_1" in url:
                return _DummyHTTPResp({"data": {"status": "FAILED", "error": "Upstream service rejected the request."}})
            if "vid_http_2" in url:
                return _DummyHTTPResp({"data": {"status": "COMPLETED", "output": {"model_url": "https://cdn.nano.test/mouse.glb"}}})
        if url == "https://cdn.nano.test/mouse.glb":
            return _BinResp(b"glTF_REAL_HTTP_MOUSE_MESH_DATA")
        return orig_urlopen(req, timeout=timeout)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    with ux_mod._live_server() as (host, port):
        addr = f"http://{host}:{port}"

        def _post(path, payload):
            req = urllib.request.Request(
                f"{addr}{path}",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with orig_urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode("utf-8"))

        gen = _post(
            "/api/3d/generate",
            {"prompt": "cartoon mouse", "tier": "Regular", "format": "glb", "scope": "user", "owner_id": "mouse_user", "save_path": "/models3d/mouse.glb"},
        )
        assert gen["simulated"] is False
        assert gen["glb_bytes_b64"] == ""
        assert "saved_to_space" not in gen
        assert gen["pending_save_path"] == "/models3d/mouse.glb"
        sp = temp_mgr.get_space("user", "mouse_user")
        assert "/models3d/mouse.glb" not in {f["path"] for f in sp.list_files()}

        # First /api/3d/status detects Rodin v2.5 upstream rejection -> falls back to tripo3d/h3.0
        st1 = _post("/api/3d/status", {"subscription_key": gen["subscription_key"]})
        assert st1["status"] == "Processing"
        assert st1["model"] == "tripo3d/h3.0"
        assert st1["uuid"] == "vid_http_2"
        assert st1["fallback_from"] == "hyper3d/rodin-v2.5"

        # Second poll sees tripo3d/h3.0 Done
        st2 = _post("/api/3d/status", {"subscription_key": st1["subscription_key"]})
        assert st2["status"] == "Done"

        # Download persists real GLB into .space VFS
        dl = _post(
            "/api/3d/download",
            {"task_uuid": st2["uuid"], "scope": "user", "owner_id": "mouse_user", "peer_id": "mouse_user", "save_path": "/models3d/mouse.glb"},
        )
        assert dl["downloaded"] is True
        assert dl["saved_to_space"]["path"] == "/models3d/mouse.glb"
        saved_rec = sp.read_file("/models3d/mouse.glb", as_text=False)
        assert base64.b64decode(saved_rec["content_b64"]) == b"glTF_REAL_HTTP_MOUSE_MESH_DATA"


def test_workstation_and_mesh_ui_poll_async_3d_before_mounting():
    from iot_federated_agent_memory.workstation_ui import render_workstation_window_html
    from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI

    ws_html = render_workstation_window_html()
    assert "apiJson('/api/3d/status'" in ws_html
    assert "apiJson('/api/3d/download'" in ws_html
    assert "pending_save_path" in ws_html
    assert 'id="wsSplitterLeft"' in ws_html
    assert 'id="wsSplitterRight"' in ws_html
    assert 'id="wsStageSplitter"' in ws_html
    assert 'id="wsToggleLeftBtn"' in ws_html
    assert 'id="wsToggleRightBtn"' in ws_html
    assert 'id="wsTogglePatchBtn"' in ws_html

    mesh_html = MESH_OS_HTML_UI
    assert "fetch('/api/3d/status'" in mesh_html
    assert "fetch('/api/3d/download'" in mesh_html
    assert "window-resize-e" in mesh_html
    assert "window-resize-s" in mesh_html
    assert '[data-resized="true"]' in mesh_html
