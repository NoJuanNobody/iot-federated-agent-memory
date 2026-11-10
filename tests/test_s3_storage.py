"""Unit tests for S3 storage module and persistent playlist hydration."""

import json
from unittest.mock import MagicMock, patch

from iot_federated_agent_memory.s3_storage import (
    _build_sigv4_headers,
    s3_delete_object,
    s3_get_json,
    s3_list_objects,
    s3_put_json,
)
from iot_federated_agent_memory.video_playlist import RelayVideoPlaylist


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
    with patch("iot_federated_agent_memory.video_playlist.s3_get_json", return_value=mock_s3_data), \
         patch("iot_federated_agent_memory.video_playlist.s3_list_objects", return_value=[]), \
         patch("iot_federated_agent_memory.video_playlist.s3_put_json", return_value=True):
        pl = RelayVideoPlaylist(sync_s3=True, local_file_path=tmp_local)
        playlist = pl.get_playlist()
        assert playlist["total"] == 1
        assert playlist["videos"][0]["video_id"] == "custom-99"
        assert playlist["videos"][0]["creator"] == "@custom_curator"
        assert playlist["videos"][0]["title"] == "Persistent S3 Track"
