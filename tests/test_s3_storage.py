"""Unit tests for S3 storage module and persistent playlist hydration."""

import io
import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from iot_federated_agent_memory.s3_storage import (
    S3ReadError,
    _build_sigv4_headers,
    s3_delete_object,
    s3_get_json,
    s3_list_objects,
    s3_put_json,
)
from iot_federated_agent_memory.video_playlist import RelayVideoPlaylist, parse_video_input

VP = "iot_federated_agent_memory.video_playlist"
FAKE_CREDS = {
    "endpoint": "https://t3.storageapi.dev",
    "bucket": "test-bucket",
    "access_key": "test-access",
    "secret_key": "test-secret",
    "region": "auto",
}


def test_build_sigv4_headers_with_querystring():
    creds = {
        "endpoint": "https://t3.storageapi.dev",
        "bucket": "test-bucket",
        "access_key": "test-access",
        "secret_key": "test-secret",
        "region": "auto",
    }
    headers = _build_sigv4_headers(
        method="GET",
        host="test-bucket.storageapi.dev",
        canonical_uri="/",
        payload_bytes=b"",
        creds=creds,
        canonical_querystring="list-type=2&prefix=videos%2F",
    )
    assert "Authorization" in headers
    assert "Credential=test-access" in headers["Authorization"]
    assert "x-amz-date" in headers
    assert headers["Host"] == "test-bucket.storageapi.dev"


def test_s3_list_objects_mocked():
    sample_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
    <ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
        <Name>test-bucket</Name>
        <Contents>
            <Key>videos/test_vid_1.mp4</Key>
            <Size>12345</Size>
            <ETag>"abc123etag"</ETag>
            <LastModified>2026-11-09T00:00:00Z</LastModified>
        </Contents>
        <Contents>
            <Key>playlist.json</Key>
            <Size>512</Size>
            <ETag>"def456etag"</ETag>
            <LastModified>2026-11-09T01:00:00Z</LastModified>
        </Contents>
    </ListBucketResult>
    """
    mock_resp = MagicMock()
    mock_resp.read.return_value = sample_xml
    mock_resp.__enter__.return_value = mock_resp

    creds = {
        "endpoint": "https://t3.storageapi.dev",
        "bucket": "test-bucket",
        "access_key": "test-access",
        "secret_key": "test-secret",
        "region": "auto",
    }

    with patch("urllib.request.urlopen", return_value=mock_resp):
        objs = s3_list_objects(prefix="", creds=creds)
        assert len(objs) == 2
        assert objs[0]["key"] == "videos/test_vid_1.mp4"
        assert objs[0]["size"] == 12345
        assert objs[0]["etag"] == "abc123etag"
        assert objs[1]["key"] == "playlist.json"


def test_s3_json_roundtrip_mocked():
    creds = {
        "endpoint": "https://t3.storageapi.dev",
        "bucket": "test-bucket",
        "access_key": "test-access",
        "secret_key": "test-secret",
        "region": "auto",
    }

    # Test put json
    mock_put_resp = MagicMock()
    mock_put_resp.status = 200
    mock_put_resp.__enter__.return_value = mock_put_resp

    with patch("urllib.request.urlopen", return_value=mock_put_resp):
        ok = s3_put_json({"test": "data"}, "playlist.json", creds=creds)
        assert ok is True

    # Test get json
    mock_get_resp = MagicMock()
    mock_get_resp.read.return_value = json.dumps({"test": "data"}).encode("utf-8")
    mock_get_resp.__enter__.return_value = mock_get_resp

    with patch("urllib.request.urlopen", return_value=mock_get_resp):
        fetched = s3_get_json("playlist.json", creds=creds)
        assert fetched == {"test": "data"}

    # Test delete json
    mock_del_resp = MagicMock()
    mock_del_resp.status = 204
    mock_del_resp.__enter__.return_value = mock_del_resp

    with patch("urllib.request.urlopen", return_value=mock_del_resp):
        del_ok = s3_delete_object("playlist.json", creds=creds)
        assert del_ok is True


def test_playlist_hydrates_from_s3_json(tmp_path):
    mock_s3_data = {
        "autoplay": True,
        "loop_collection": True,
        "videos": [
            {
                "id": "video-custom-99",
                "video_id": "custom-99",
                "platform": "mp4",
                "creator": "@custom_curator",
                "title": "Persistent S3 Track",
                "category": "spotlight",
                "cite_url": "/videos/custom-99.mp4",
                "embed_url": "/videos/custom-99.mp4",
                "duration_seconds": 45,
            }
        ],
    }

    tmp_local = str(tmp_path / "playlist.json")
    with patch(f"{VP}.get_s3_credentials", return_value=FAKE_CREDS), \
         patch("iot_federated_agent_memory.video_playlist.s3_get_json", return_value=mock_s3_data), \
         patch("iot_federated_agent_memory.video_playlist.s3_list_objects", return_value=[]), \
         patch("iot_federated_agent_memory.video_playlist.s3_put_json", return_value=True):
        pl = RelayVideoPlaylist(sync_s3=True, local_file_path=tmp_local)
        playlist = pl.get_playlist()
        assert playlist["total"] == 1
        assert playlist["videos"][0]["video_id"] == "custom-99"
        assert playlist["videos"][0]["creator"] == "@custom_curator"
        assert playlist["videos"][0]["title"] == "Persistent S3 Track"


def _remote_playlist(*video_ids):
    return {
        "autoplay": True,
        "loop_collection": True,
        "videos": [
            {"id": f"video-{v}", "video_id": v, "title": f"Remote {v}",
             "embed_url": f"/videos/{v}.mp4", "cite_url": f"/videos/{v}.mp4"}
            for v in video_ids
        ],
    }


def test_s3_get_json_strict_distinguishes_missing_from_unreachable():
    def http_error(code):
        return urllib.error.HTTPError("https://x", code, "err", {}, io.BytesIO(b""))

    with patch("urllib.request.urlopen", side_effect=http_error(404)):
        assert s3_get_json("playlist.json", creds=FAKE_CREDS, strict=True) is None
    with patch("urllib.request.urlopen", side_effect=http_error(503)):
        with pytest.raises(S3ReadError):
            s3_get_json("playlist.json", creds=FAKE_CREDS, strict=True)
    with patch("urllib.request.urlopen", side_effect=TimeoutError()):
        with pytest.raises(S3ReadError):
            s3_get_json("playlist.json", creds=FAKE_CREDS, strict=True)
        assert s3_get_json("playlist.json", creds=FAKE_CREDS) is None


def test_failed_boot_read_never_overwrites_s3_playlist(tmp_path):
    """Redeploy regression: a transient S3 error at boot used to push seeds/baked playlist over the real one."""
    put = MagicMock(return_value=True)
    with patch(f"{VP}.get_s3_credentials", return_value=FAKE_CREDS), \
         patch(f"{VP}.s3_get_json", side_effect=S3ReadError("boom")), \
         patch(f"{VP}.s3_list_objects", return_value=[]), \
         patch(f"{VP}.s3_put_json", put), \
         patch(f"{VP}.time.sleep"):
        pl = RelayVideoPlaylist(sync_s3=True, local_file_path=str(tmp_path / "playlist.json"))
        assert pl.get_playlist()["total"] == len(RelayVideoPlaylist.DEFAULT_COLLECTION)
        pl.remove_video("7705677376465767711")
    put.assert_not_called()


def test_save_after_failed_boot_merges_onto_remote_state(tmp_path):
    reads = [S3ReadError("down"), S3ReadError("down"), S3ReadError("down"), _remote_playlist("keep-1", "keep-2")]
    put = MagicMock(return_value=True)
    with patch(f"{VP}.get_s3_credentials", return_value=FAKE_CREDS), \
         patch(f"{VP}.s3_get_json", side_effect=reads), \
         patch(f"{VP}.s3_list_objects", return_value=[]), \
         patch(f"{VP}.s3_put_json", put), \
         patch(f"{VP}.time.sleep"):
        pl = RelayVideoPlaylist(sync_s3=True, local_file_path=str(tmp_path / "playlist.json"))
        pl.add_video("new-clip", title="Fresh", auto_download=False)

    pushed = put.call_args[0][0]
    ids = [v["video_id"] for v in pushed["videos"]]
    assert ids == ["keep-1", "keep-2", "new-clip"]  # remote preserved, seeds not pushed, new item kept


def test_removed_video_is_not_resurrected_by_s3_discovery(tmp_path):
    local = str(tmp_path / "playlist.json")
    store = {"playlist": _remote_playlist("a1", "b2")}
    objects = [{"key": "videos/a1.mp4"}, {"key": "videos/b2.mp4"}]

    def put_json(data, key, **_):
        store["playlist"] = json.loads(json.dumps(data))
        return True

    def get_json(key, **_):
        return store["playlist"]

    with patch(f"{VP}.get_s3_credentials", return_value=FAKE_CREDS), \
         patch(f"{VP}.s3_get_json", side_effect=get_json), \
         patch(f"{VP}.s3_list_objects", return_value=objects), \
         patch(f"{VP}.s3_put_json", side_effect=put_json):
        pl = RelayVideoPlaylist(sync_s3=True, local_file_path=local)
        assert pl.remove_video("b2") is True
        restarted = RelayVideoPlaylist(sync_s3=True, local_file_path=local)

    assert [v["video_id"] for v in restarted.get_playlist()["videos"]] == ["a1"]


def test_page_links_are_never_stored_as_video_sources():
    with pytest.raises(ValueError):
        parse_video_input("https://www.instagram.com/reel/Dd9Fa6dteth/?exln=x", auto_download=False)

    item = parse_video_input("https://cdn.example.com/clip.mp4?sig=1", auto_download=False)
    assert item.embed_url == "https://cdn.example.com/clip.mp4?sig=1"


def test_tiktok_short_link_resolves_to_native_stream():
    canonical = "https://www.tiktok.com/@murphmaxxing/video/7706642712296000781?_r=1"
    with patch(f"{VP}.resolve_short_link", return_value=canonical) as resolve:
        item = parse_video_input("https://www.tiktok.com/t/ZPLtBeCR8/", auto_download=False)
    resolve.assert_called_once()
    assert item.video_id == "7706642712296000781"
    assert item.embed_url == "/videos/7706642712296000781.mp4"
    assert item.creator == "@murphmaxxing"
