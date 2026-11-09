"""Zero-Dependency AWS Signature V4 S3 Client for Railway Object Storage Buckets (`tincan-videos`)."""

from __future__ import annotations

import datetime
import hashlib
import hmac
import json
import os
import subprocess
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

_CACHED_CREDS: Optional[Dict[str, str]] = None


def get_s3_credentials(bucket_alias: str = "tincan-videos") -> Optional[Dict[str, str]]:
    """Resolve S3 bucket credentials from environment variables or local Railway CLI."""
    global _CACHED_CREDS
    if _CACHED_CREDS is not None:
        return _CACHED_CREDS

    endpoint = os.environ.get("AWS_ENDPOINT_URL") or os.environ.get("S3_ENDPOINT_URL")
    bucket_name = os.environ.get("AWS_S3_BUCKET_NAME") or os.environ.get("S3_BUCKET_NAME")
    access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    region = os.environ.get("AWS_DEFAULT_REGION", "auto")

    if endpoint and bucket_name and access_key and secret_key:
        _CACHED_CREDS = {
            "endpoint": endpoint.rstrip("/"),
            "bucket": bucket_name,
            "access_key": access_key,
            "secret_key": secret_key,
            "region": region or "auto",
        }
        return _CACHED_CREDS

    # Fallback: query local `railway bucket credentials --bucket <alias> --json`
    try:
        repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        raw = subprocess.check_output(
            ["railway", "bucket", "credentials", "--bucket", bucket_alias, "--json"],
            cwd=repo_dir,
            stderr=subprocess.DEVNULL,
            timeout=10,
        ).decode("utf-8")
        data = json.loads(raw)
        if data.get("accessKeyId") and data.get("secretAccessKey") and data.get("bucketName"):
            _CACHED_CREDS = {
                "endpoint": (data.get("endpoint") or "https://t3.storageapi.dev").rstrip("/"),
                "bucket": data["bucketName"],
                "access_key": data["accessKeyId"],
                "secret_key": data["secretAccessKey"],
                "region": data.get("region") or "auto",
            }
            return _CACHED_CREDS
    except Exception:
        pass

    return None


def _sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _get_signature_key(secret_key: str, date_stamp: str, region_name: str, service_name: str = "s3") -> bytes:
    k_date = _sign(("AWS4" + secret_key).encode("utf-8"), date_stamp)
    k_region = _sign(k_date, region_name)
    k_service = _sign(k_region, service_name)
    k_signing = _sign(k_service, "aws4_request")
    return k_signing


def _build_sigv4_headers(
    method: str,
    host: str,
    canonical_uri: str,
    payload_bytes: bytes,
    creds: Dict[str, str],
    extra_headers: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    now = datetime.datetime.now(datetime.timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    region = creds.get("region") or "auto"
    service = "s3"

    payload_hash = hashlib.sha256(payload_bytes).hexdigest()
    headers_to_sign: Dict[str, str] = {
        "host": host,
        "x-amz-content-sha256": payload_hash,
        "x-amz-date": amz_date,
    }
    if extra_headers:
        for k, v in extra_headers.items():
            headers_to_sign[k.lower()] = v.strip()

    sorted_keys = sorted(headers_to_sign.keys())
    canonical_headers = "".join(f"{k}:{headers_to_sign[k]}\n" for k in sorted_keys)
    signed_headers = ";".join(sorted_keys)

    canonical_request = "\n".join([
        method.upper(),
        canonical_uri,
        "",  # query string
        canonical_headers,
        signed_headers,
        payload_hash,
    ])

    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = "\n".join([
        algorithm,
        amz_date,
        credential_scope,
        hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
    ])

    signing_key = _get_signature_key(creds["secret_key"], date_stamp, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization_header = (
        f"{algorithm} Credential={creds['access_key']}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    out_headers = {
        "Host": host,
        "x-amz-date": amz_date,
        "x-amz-content-sha256": payload_hash,
        "Authorization": authorization_header,
    }
    if extra_headers:
        out_headers.update(extra_headers)
    return out_headers


def s3_put_object(
    local_path: str,
    object_key: str,
    content_type: str = "video/mp4",
    creds: Optional[Dict[str, str]] = None,
) -> Optional[Dict[str, Any]]:
    """Upload a local file to the Railway S3 bucket using pure-Python SigV4 PUT."""
    resolved = creds or get_s3_credentials()
    if not resolved or not os.path.isfile(local_path):
        return None

    with open(local_path, "rb") as f:
        payload = f.read()

    parsed_ep = urllib.parse.urlparse(resolved["endpoint"])
    host = f"{resolved['bucket']}.{parsed_ep.netloc}"
    clean_key = object_key.lstrip("/")
    canonical_uri = "/" + urllib.parse.quote(clean_key, safe="/-_.~")
    url = f"{parsed_ep.scheme}://{host}{canonical_uri}"

    headers = _build_sigv4_headers(
        method="PUT",
        host=host,
        canonical_uri=canonical_uri,
        payload_bytes=payload,
        creds=resolved,
        extra_headers={
            "Content-Type": content_type,
            "Content-Length": str(len(payload)),
        },
    )

    req = urllib.request.Request(url, data=payload, headers=headers, method="PUT")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return {
            "status": resp.status,
            "bucket": resolved["bucket"],
            "key": clean_key,
            "size_bytes": len(payload),
            "s3_uri": f"s3://{resolved['bucket']}/{clean_key}",
        }


def s3_get_object(
    object_key: str,
    dest_path: str,
    creds: Optional[Dict[str, str]] = None,
) -> bool:
    """Download an object from the Railway S3 bucket to dest_path."""
    resolved = creds or get_s3_credentials()
    if not resolved:
        return False

    parsed_ep = urllib.parse.urlparse(resolved["endpoint"])
    host = f"{resolved['bucket']}.{parsed_ep.netloc}"
    clean_key = object_key.lstrip("/")
    canonical_uri = "/" + urllib.parse.quote(clean_key, safe="/-_.~")
    url = f"{parsed_ep.scheme}://{host}{canonical_uri}"

    headers = _build_sigv4_headers(
        method="GET",
        host=host,
        canonical_uri=canonical_uri,
        payload_bytes=b"",
        creds=resolved,
    )

    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        if len(data) > 1024:
            os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
            with open(dest_path, "wb") as f:
                f.write(data)
            return True
    except Exception:
        pass
    return False
