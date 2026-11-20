"""Comprehensive unit tests for World Labs Atlas Developer API v2 Gateway, VFS downloads, Omni-Audio, and Telemetry."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import urllib.error
import urllib.request
from unittest.mock import MagicMock, patch

import pytest

from iot_federated_agent_memory.agent_space import SingleFileSpaceVFS
from iot_federated_agent_memory.ai_gateway import (
    DynamicAIGatewayRouter,
    LabProviderConfig,
    _resolve_worldlabs_key_fallback,
    generate_minimal_wav_bytes,
)
from iot_federated_agent_memory.ai_gateway_telemetry import (
    classify_gateway,
    estimate_preflight,
)


def _mock_http_response(payload: dict | bytes, status: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status = status
    if isinstance(payload, bytes):
        resp.read.return_value = payload
    else:
        resp.read.return_value = json.dumps(payload).encode("utf-8")
    resp.__enter__.return_value = resp
    return resp


def _make_http_error(url: str, code: int, body: dict | str) -> urllib.error.HTTPError:
    raw = (json.dumps(body) if isinstance(body, dict) else str(body)).encode("utf-8")
    return urllib.error.HTTPError(
        url=url,
        code=code,
        msg=f"HTTP {code}",
        hdrs=None,  # type: ignore[arg-type]
        fp=io.BytesIO(raw),
    )


def test_resolve_worldlabs_key_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify _resolve_worldlabs_key_fallback checks WLT_API_KEY then WORLDLABS_API_KEY."""
    monkeypatch.delenv("WLT_API_KEY", raising=False)
    monkeypatch.delenv("WORLDLABS_API_KEY", raising=False)
    assert _resolve_worldlabs_key_fallback() is None

    monkeypatch.setenv("WORLDLABS_API_KEY", "wlt-legacy-env-key")
    assert _resolve_worldlabs_key_fallback() == "wlt-legacy-env-key"

    monkeypatch.setenv("WLT_API_KEY", "wlt-primary-key")
    assert _resolve_worldlabs_key_fallback() == "wlt-primary-key"


def test_router_atlas_constants_and_init(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify DynamicAIGatewayRouter exposes ATLAS_BASE_URL, ATLAS_TASKS, ATLAS_CREDIT_USD_RATE, and state dicts."""
    monkeypatch.setenv("WLT_API_KEY", "wlt-init-key")
    router = DynamicAIGatewayRouter()
    assert router.ATLAS_BASE_URL.startswith("https://api.atlas.worldlabs.ai/api/v2")
    assert router.ATLAS_TASKS == (
        "atlasTextToImage",
        "images2PosedRGBD",
        "atlasGenerate",
        "atlasChisel",
        "posedImages2Splats",
        "splats2Mesh",
    )
    assert router.ATLAS_CREDIT_USD_RATE == 0.001
    assert router.worldlabs_key == "wlt-init-key"
    assert isinstance(router.atlas_operations, dict)
    assert router.atlas_operations == {}


def test_check_atlas_health_live_and_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify check_atlas_health reports key_configured and handles both live HTTP 200 and offline fallback."""
    monkeypatch.delenv("WLT_API_KEY", raising=False)
    monkeypatch.delenv("WORLDLABS_API_KEY", raising=False)

    router_no_key = DynamicAIGatewayRouter(worldlabs_key=None)
    with patch("urllib.request.urlopen", side_effect=OSError("Network unreachable")):
        health_offline = router_no_key.check_atlas_health()
    assert health_offline["ok"] is True
    assert health_offline["key_configured"] is False
    assert health_offline["simulated"] is True

    router_with_key = DynamicAIGatewayRouter(worldlabs_key="wlt-live-health-key")
    with patch("urllib.request.urlopen", return_value=_mock_http_response({"status": "ok"})) as mock_open:
        health_live = router_with_key.check_atlas_health()
    assert health_live["ok"] is True
    assert health_live["key_configured"] is True
    assert health_live["connected"] is True
    assert health_live["simulated"] is False
    assert health_live["status"] == "ok"
    req_sent = mock_open.call_args[0][0]
    assert req_sent.full_url.endswith("/health")
    assert req_sent.headers.get("Wlt-api-key") == "wlt-live-health-key"


def test_upload_atlas_asset_three_step_and_deterministic_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify 3-step Atlas Asset upload handshake and deterministic asset_<sha256[:16]> fallback."""
    monkeypatch.delenv("WLT_API_KEY", raising=False)
    monkeypatch.delenv("WORLDLABS_API_KEY", raising=False)
    sample_bytes = b"\xff\xd8\xff\xe0test-jpeg-payload\xff\xd9"
    expected_sha = hashlib.sha256(sample_bytes).hexdigest()
    expected_fallback_id = f"asset_{expected_sha[:16]}"

    # 1. Offline / no key fallback
    router_offline = DynamicAIGatewayRouter(worldlabs_key=None)
    res_fallback = router_offline.upload_atlas_asset(sample_bytes, mime_type="image/jpeg", filename="torii.jpg")
    assert res_fallback["ok"] is True
    assert res_fallback["id"] == expected_fallback_id
    assert res_fallback["assetId"] == expected_fallback_id
    assert res_fallback["simulated"] is True
    assert res_fallback["size_bytes"] == len(sample_bytes)

    # 2. Live 3-step upload (createUploadUrl -> PUT bytes -> completeUpload)
    router_live = DynamicAIGatewayRouter(worldlabs_key="wlt-upload-key")
    calls: list[tuple[str, str, dict]] = []

    def fake_urlopen(req: urllib.request.Request, timeout: float = 15.0):
        calls.append((req.get_method(), req.full_url, dict(req.headers)))
        if req.full_url.endswith("/assets:createUploadUrl"):
            return _mock_http_response(
                {
                    "assetId": "asset_live_998877",
                    "uploadUrl": "https://storage.worldlabs.ai/upload/signed-998877",
                    "headers": {"Content-Type": "image/jpeg", "x-goog-meta-asset": "998877"},
                }
            )
        if "storage.worldlabs.ai/upload/signed-998877" in req.full_url:
            assert req.data == sample_bytes
            return _mock_http_response(b"")
        if req.full_url.endswith("/assets/asset_live_998877:completeUpload"):
            return _mock_http_response({"id": "asset_live_998877", "status": "READY"})
        raise AssertionError(f"Unexpected URL: {req.full_url}")

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        res_live = router_live.upload_atlas_asset(sample_bytes, mime_type="image/jpeg", filename="torii.jpg")

    assert res_live["ok"] is True
    assert res_live["id"] == "asset_live_998877"
    assert res_live["assetId"] == "asset_live_998877"
    assert res_live["simulated"] is False
    assert len(calls) == 3
    assert calls[0][0] == "POST" and calls[0][1].endswith("/assets:createUploadUrl")
    assert calls[1][0] == "PUT" and "storage.worldlabs.ai/upload/signed-998877" in calls[1][1]
    assert calls[2][0] == "POST" and calls[2][1].endswith("/assets/asset_live_998877:completeUpload")


def test_create_atlas_read_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify POST /assets/{asset_id}:createReadUrl live and offline."""
    monkeypatch.delenv("WLT_API_KEY", raising=False)
    router_offline = DynamicAIGatewayRouter(worldlabs_key=None)
    offline_res = router_offline.create_atlas_read_url("asset_abc123")
    assert offline_res["ok"] is True
    assert offline_res["assetId"] == "asset_abc123"
    assert "asset_abc123" in offline_res["url"]
    assert offline_res["simulated"] is True

    router_live = DynamicAIGatewayRouter(worldlabs_key="wlt-read-key")
    with patch(
        "urllib.request.urlopen",
        return_value=_mock_http_response({"readUrl": "https://cdn.worldlabs.ai/read/asset_abc123?sig=1"}),
    ) as mock_open:
        live_res = router_live.create_atlas_read_url("asset_abc123")
    assert live_res["ok"] is True
    assert live_res["url"] == "https://cdn.worldlabs.ai/read/asset_abc123?sig=1"
    assert live_res["simulated"] is False
    req_sent = mock_open.call_args[0][0]
    assert req_sent.full_url.endswith("/assets/asset_abc123:createReadUrl")
    assert req_sent.get_method() == "POST"


@pytest.mark.parametrize(
    "task_name",
    [
        "atlasTextToImage",
        "images2PosedRGBD",
        "atlasGenerate",
        "atlasChisel",
        "posedImages2Splats",
        "splats2Mesh",
    ],
)
def test_submit_atlas_task_simulated_all_six_tasks(
    monkeypatch: pytest.MonkeyPatch,
    task_name: str,
) -> None:
    """Verify all 6 ATLAS_TASKS run deterministically in offline/simulated mode and store in atlas_operations."""
    monkeypatch.delenv("WLT_API_KEY", raising=False)
    monkeypatch.delenv("WORLDLABS_API_KEY", raising=False)
    router = DynamicAIGatewayRouter(worldlabs_key=None)

    op = router.submit_atlas_task(
        task_name,
        {"prompt": f"Test {task_name} scene"},
        idempotency_key="idem-fixed-1234",
    )
    assert op["ok"] is True
    assert op["task"] == task_name
    assert op["idempotency_key"] == "idem-fixed-1234"
    assert op["id"] == op["operation_id"]
    assert op["done"] is True
    assert isinstance(op["response"], dict)
    assert isinstance(op["metadata"], dict)
    assert op["id"] in router.atlas_operations

    # Idempotent repeat produces identical operation_id
    op_repeat = router.submit_atlas_task(
        task_name,
        {"prompt": f"Test {task_name} scene"},
        idempotency_key="idem-fixed-1234",
    )
    assert op_repeat["operation_id"] == op["operation_id"]


def test_submit_atlas_task_invalid_name_raises() -> None:
    """Verify submit_atlas_task rejects unknown task names."""
    router = DynamicAIGatewayRouter(worldlabs_key=None)
    with pytest.raises(ValueError, match="Unsupported World Labs Atlas task"):
        router.submit_atlas_task("notARealAtlasTask", {})


def test_submit_atlas_task_live_and_error_codes() -> None:
    """Verify live POST /tasks:{task} headers and HTTP 402/422 handling."""
    router = DynamicAIGatewayRouter(worldlabs_key="wlt-task-key")

    with patch(
        "urllib.request.urlopen",
        return_value=_mock_http_response(
            {
                "id": "operations/op_live_rgbd_001",
                "done": False,
                "metadata": {"task": "images2PosedRGBD"},
            }
        ),
    ) as mock_open:
        res = router.submit_atlas_task(
            "images2PosedRGBD",
            {"images": [{"assetId": "asset_1"}]},
        )
    assert res["ok"] is True
    assert res["operation_id"] == "op_live_rgbd_001"
    assert res["done"] is False
    assert res["idempotency_key"]
    req_sent = mock_open.call_args[0][0]
    assert req_sent.full_url.endswith("/tasks:images2PosedRGBD")
    assert req_sent.headers.get("Wlt-api-key") == "wlt-task-key"
    assert req_sent.headers.get("Idempotency-key") == res["idempotency_key"]

    # HTTP 402 CREDITS_UNAVAILABLE
    err_402 = _make_http_error(
        f"{router.ATLAS_BASE_URL}/tasks:posedImages2Splats",
        402,
        {"error": {"status": "CREDITS_UNAVAILABLE", "message": "Out of credits"}},
    )
    with patch("urllib.request.urlopen", side_effect=err_402):
        res_402 = router.submit_atlas_task("posedImages2Splats", {})
    assert res_402["ok"] is False
    assert res_402["status_code"] == 402
    assert res_402["error_code"] == "CREDITS_UNAVAILABLE"

    # HTTP 422 VALIDATION_ERROR
    err_422 = _make_http_error(
        f"{router.ATLAS_BASE_URL}/tasks:atlasGenerate",
        422,
        {"error": {"status": "INVALID_ARGUMENT", "message": "Missing camera intrinsics"}},
    )
    with patch("urllib.request.urlopen", side_effect=err_422):
        res_422 = router.submit_atlas_task("atlasGenerate", {})
    assert res_422["ok"] is False
    assert res_422["status_code"] == 422
    assert res_422["error_code"] == "VALIDATION_ERROR"


def test_get_atlas_operation_status_and_http_errors() -> None:
    """Verify get_atlas_operation handles 200 done, 404 retry-later, 402 credits, 422 validation, and THROTTLED."""
    router = DynamicAIGatewayRouter(worldlabs_key="wlt-poll-key")

    # 1. HTTP 404 right after submission -> retry_later
    err_404 = _make_http_error(f"{router.ATLAS_BASE_URL}/operations/op_pending_1", 404, "Not found yet")
    with patch("urllib.request.urlopen", side_effect=err_404):
        st_404 = router.get_atlas_operation("op_pending_1")
    assert st_404["ok"] is True
    assert st_404["done"] is False
    assert st_404["retry_later"] is True
    assert st_404["status_code"] == 404

    # 2. HTTP 402 CREDITS_UNAVAILABLE
    err_402 = _make_http_error(f"{router.ATLAS_BASE_URL}/operations/op_402", 402, "Credits exhausted")
    with patch("urllib.request.urlopen", side_effect=err_402):
        st_402 = router.get_atlas_operation("op_402")
    assert st_402["ok"] is False
    assert st_402["status_code"] == 402
    assert st_402["error_code"] == "CREDITS_UNAVAILABLE"

    # 3. HTTP 422 VALIDATION_ERROR
    err_422 = _make_http_error(f"{router.ATLAS_BASE_URL}/operations/op_422", 422, "Invalid body")
    with patch("urllib.request.urlopen", side_effect=err_422):
        st_422 = router.get_atlas_operation("op_422")
    assert st_422["ok"] is False
    assert st_422["status_code"] == 422
    assert st_422["error_code"] == "VALIDATION_ERROR"

    # 4. Operation finished with THROTTLED error payload
    with patch(
        "urllib.request.urlopen",
        return_value=_mock_http_response(
            {
                "id": "op_throttled",
                "done": True,
                "error": {"status": "THROTTLED", "message": "Capacity limit reached"},
            }
        ),
    ):
        st_throttled = router.get_atlas_operation("op_throttled")
    assert st_throttled["ok"] is False
    assert st_throttled["done"] is True
    assert st_throttled["error_code"] == "THROTTLED"


def test_download_atlas_operation_to_vfs_rgbd_splats_and_mesh(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """Verify download_atlas_operation_to_vfs writes operation.json, frames_0_*, refinedSplats_2000000.spz, and .glb."""
    monkeypatch.delenv("WLT_API_KEY", raising=False)
    monkeypatch.delenv("WORLDLABS_API_KEY", raising=False)
    router = DynamicAIGatewayRouter(worldlabs_key=None)
    vfs = SingleFileSpaceVFS(
        scope="user",
        owner_id="atlas_tester",
        space_path=str(tmp_path / "atlas_test.space"),
        enable_s3_sync=False,
    )

    # 1. images2PosedRGBD -> operation.json, frames_0_image.jpg, frames_0_depth.exr, frames_0_confidence.png
    op_rgbd = router.submit_atlas_task("images2PosedRGBD", {"images": [{"assetId": "asset_1"}]})
    dl_rgbd = router.download_atlas_operation_to_vfs(op_rgbd["operation_id"], vfs)
    assert dl_rgbd["ok"] is True
    assert dl_rgbd["operation_id"] == op_rgbd["operation_id"]
    saved_rgbd = dl_rgbd["saved_files"]
    assert any(p.endswith("/operation.json") for p in saved_rgbd)
    assert any(p.endswith("/frames_0_image.jpg") for p in saved_rgbd)
    assert any(p.endswith("/frames_0_depth.exr") for p in saved_rgbd)
    assert any(p.endswith("/frames_0_confidence.png") for p in saved_rgbd)
    for path in saved_rgbd:
        rec = vfs.read_file(path, as_text=False)
        assert rec["size_bytes"] > 0

    # 2. posedImages2Splats -> refinedSplats_2000000.spz
    op_splat = router.submit_atlas_task("posedImages2Splats", {"frames": []})
    dl_splat = router.download_atlas_operation_to_vfs(op_splat["operation_id"], vfs)
    assert dl_splat["ok"] is True
    assert any(p.endswith("/refinedSplats_2000000.spz") for p in dl_splat["saved_files"])

    # 3. splats2Mesh -> /models3d/atlas_<short_id>.glb
    op_mesh = router.submit_atlas_task("splats2Mesh", {"splatAssetId": "asset_splat_1"})
    dl_mesh = router.download_atlas_operation_to_vfs(op_mesh["operation_id"], vfs)
    assert dl_mesh["ok"] is True
    glb_paths = [p for p in dl_mesh["saved_files"] if p.startswith("/models3d/atlas_") and p.endswith(".glb")]
    assert len(glb_paths) == 1
    glb_rec = vfs.read_file(glb_paths[0], as_text=False)
    glb_raw = base64.b64decode(glb_rec["content_b64"])
    assert glb_raw.startswith(b"glTF")


@pytest.mark.parametrize(
    ("kind", "model"),
    [
        ("music", "google/lyria-3.5"),
        ("tts", "elevenlabs/eleven-v4"),
        ("sfx", "elevenlabs/sound-effects/v3"),
        ("tts", "qwen-audio-3.1-tts-flash"),
        ("tts", "kokoro-82m"),
    ],
)
def test_generate_omni_audio_models_and_wav_payload(kind: str, model: str) -> None:
    """Verify generate_omni_audio supports all 5 audio models and returns valid WAV + Aeonik sparkline."""
    router = DynamicAIGatewayRouter(worldlabs_key=None)
    res = router.generate_omni_audio(
        "Synthesize brutalist monolith atmospheric drone",
        kind=kind,
        model=model,
        voice="af_heart",
    )
    assert res["ok"] is True
    assert res["kind"] == kind
    assert res["model"] == model
    assert res["prompt"] == "Synthesize brutalist monolith atmospheric drone"
    assert res["mime_type"] == "audio/wav"
    assert res["sparkline"] == "│┃│┃┃│┃┃"
    assert res["lufs"] == -14.0

    wav_bytes = base64.b64decode(res["audio_bytes_b64"])
    assert wav_bytes.startswith(b"RIFF")
    assert b"WAVEfmt " in wav_bytes[:24]


def test_ai_gateway_telemetry_worldlabs_classification() -> None:
    """Verify classify_gateway and estimate_preflight classify WLT_API_KEY, worldlabs, and atlas under 'worldlabs'."""
    router = DynamicAIGatewayRouter(worldlabs_key="wlt-telem-key")
    assert classify_gateway({"api_key_env": "WLT_API_KEY"}) == "worldlabs"
    assert classify_gateway({"gateway": "worldlabs"}) == "worldlabs"
    assert classify_gateway({"gateway": "atlas"}) == "worldlabs"
    assert classify_gateway({"lab_id": "worldlabs"}) == "worldlabs"
    assert classify_gateway({"lab_id": "atlas"}) == "worldlabs"
    assert classify_gateway("worldlabs/posedImages2Splats") == "worldlabs"
    assert classify_gateway("images2PosedRGBD") == "worldlabs"

    cfg = LabProviderConfig(
        lab_id="atlas",
        display_name="World Labs Atlas v2",
        model_alias="worldlabs/posedImages2Splats",
        endpoint="https://api.atlas.worldlabs.ai/api/v2",
        api_key_env="WLT_API_KEY",
        available_credits=1000.0,
        is_active=True,
    )
    assert classify_gateway(cfg, router=router) == "worldlabs"

    est = estimate_preflight("worldlabs/posedImages2Splats", prompt_chars=120, router=router)
    assert est["gateway"] == "worldlabs"
    assert est["is_zero_burn"] is False
    assert est["estimated_credits"] == 500
    assert est["estimated_usd"] == 0.50
    assert "worldlabs atlas v2" in est["recommended_route"]


def test_generate_omni_audio_live_nanogpt_binary_async_polling_and_error(monkeypatch):
    import io
    import json
    import urllib.error
    import urllib.request

    class _FakeResp:
        def __init__(self, body: bytes, status: int = 200, content_type: str = "application/json"):
            self._body = body
            self.status = status
            self.headers = {"Content-Type": content_type}

        def read(self):
            return self._body

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    fake_mp3 = b"ID3\x03\x00\x00\x00\x00\x00\x00" + b"\xff\xfb\x90\x00" + b"MP3AUDIOBYTES" * 10
    seen_reqs = []

    def _fake_urlopen(req, timeout=None):
        url = req.full_url
        method = req.get_method()
        raw_data = req.data.decode("utf-8") if req.data else ""
        body = json.loads(raw_data) if raw_data else {}
        seen_reqs.append((method, url, body, dict(req.header_items())))

        if url == DynamicAIGatewayRouter.NANOGPT_TTS_URL:
            txt = body.get("text", "")
            if "trigger_error" in txt:
                raise urllib.error.HTTPError(
                    url,
                    500,
                    "Internal Server Error",
                    {},
                    io.BytesIO(b'{"error":"Upstream audio synth crashed"}'),
                )
            if "async_music" in txt:
                payload = {
                    "status": "pending",
                    "runId": "tts_run_42",
                    "model": "google/lyria-3.5",
                    "cost": 0.11,
                    "paymentSource": "USD",
                }
                return _FakeResp(json.dumps(payload).encode("utf-8"), status=202, content_type="application/json")
            # Direct binary MP3 response
            return _FakeResp(fake_mp3, status=200, content_type="audio/mpeg")

        if url.startswith(DynamicAIGatewayRouter.NANOGPT_TTS_STATUS_URL):
            if "runId=tts_run_pending" in url:
                return _FakeResp(json.dumps({"status": "pending", "runId": "tts_run_pending"}).encode("utf-8"))
            if "runId=tts_run_failed" in url:
                return _FakeResp(json.dumps({"status": "error", "error": "Voice model overloaded"}).encode("utf-8"))
            return _FakeResp(
                json.dumps({"status": "completed", "audioUrl": "https://cdn.example.com/tracks/lyria_42.mp3"}).encode("utf-8")
            )

        if url == "https://cdn.example.com/tracks/lyria_42.mp3":
            return _FakeResp(fake_mp3, status=200, content_type="audio/mpeg")

        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)
    router = DynamicAIGatewayRouter(nanogpt_key="ng-uuid-test-key", worldlabs_key=None)

    # 1. Direct binary MP3 TTS generation (ElevenLabs v4 gets valid default voice "Aria")
    tts = router.generate_omni_audio("Hello from TinCan", kind="tts", model="elevenlabs/eleven-v4")
    assert tts["ok"] is True
    assert tts["simulated"] is False
    assert tts["done"] is True
    assert tts["mime_type"] == "audio/mpeg"
    assert tts["ext"] == ".mp3"
    assert tts["voice"] == "Aria"
    assert base64.b64decode(tts["audio_bytes_b64"]) == fake_mp3

    # 2. Async HTTP 202 music generation returns pending runId + cost metadata
    mus = router.generate_omni_audio("async_music koto score", kind="music", model="google/lyria-3.5")
    assert mus["ok"] is True
    assert mus["async"] is True
    assert mus["done"] is False
    assert mus["status"] == "RUNNING"
    assert mus["job_id"] == "tts_run_42"
    assert mus["cost"] == 0.11
    assert mus["payment_source"] == "USD"

    # 3. Polling: pending -> completed (downloads CDN MP3 without leaking auth header) -> failed
    st_pending = router.poll_nanogpt_audio_status("tts_run_pending", model="google/lyria-3.5")
    assert st_pending["ok"] is True
    assert st_pending["done"] is False
    assert st_pending["status"] == "RUNNING"

    st_done = router.poll_nanogpt_audio_status("tts_run_42", model="google/lyria-3.5", cost=0.11, payment_source="USD")
    assert st_done["ok"] is True
    assert st_done["done"] is True
    assert st_done["status"] == "SUCCEEDED"
    assert st_done["mime_type"] == "audio/mpeg"
    assert st_done["ext"] == ".mp3"
    assert base64.b64decode(st_done["audio_bytes_b64"]) == fake_mp3
    cdn_req = [r for r in seen_reqs if r[1] == "https://cdn.example.com/tracks/lyria_42.mp3"][0]
    assert "Authorization" not in cdn_req[3]

    st_fail = router.poll_nanogpt_audio_status("tts_run_failed", model="google/lyria-3.5")
    assert st_fail["ok"] is False
    assert st_fail["done"] is True
    assert st_fail["status"] == "FAILED"
    assert "overloaded" in st_fail["error"]

    # 4. Live upstream HTTP 500 error never fakes a 120ms beep
    err = router.generate_omni_audio("trigger_error boom", kind="sfx", model="elevenlabs/sound-effects/v3")
    assert err["ok"] is False
    assert err["status_code"] == 500
    assert "crashed" in err["error"]
