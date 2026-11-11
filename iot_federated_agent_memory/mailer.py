#!/usr/bin/env python3
"""Pluggable transactional email sender for TinCan auth codes.

* When ``RESEND_API_KEY`` is set, mail goes out through Resend's HTTP API
  (https://resend.com/docs/api-reference/emails/send-email). ``TINCAN_EMAIL_FROM``
  must be a sender on a domain verified in Resend, e.g. ``TinCan <auth@example.com>``.
* Otherwise nothing is delivered. The sender logs that a message was *issued*
  (never its contents) and reports ``delivered=False`` so callers can say so
  honestly instead of pretending the email went out.
* For local development only, ``TINCAN_EMAIL_DEV_LOG=1`` prints the message body
  to the server log. It is ignored when running in production.

Tests can swap the transport with :func:`set_email_sender`.
"""

import json
import logging
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Optional

log = logging.getLogger("tincan.mailer")

RESEND_ENDPOINT = "https://api.resend.com/emails"


@dataclass
class EmailMessage:
    to: str
    subject: str
    text: str


@dataclass
class SendResult:
    delivered: bool
    provider: str
    detail: str = ""


def mask_email(email: str) -> str:
    local, _, domain = (email or "").partition("@")
    if not domain:
        return "***"
    return f"{local[:1]}***@{domain}"


def is_production() -> bool:
    env = (
        os.environ.get("TINCAN_ENV")
        or os.environ.get("RAILWAY_ENVIRONMENT_NAME")
        or os.environ.get("RAILWAY_ENVIRONMENT")
        or ""
    ).strip().lower()
    return env in ("prod", "production")


def delivery_configured() -> bool:
    return _custom_sender is not None or bool(os.environ.get("RESEND_API_KEY", "").strip())


def _send_via_resend(msg: EmailMessage) -> SendResult:
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    sender = os.environ.get("TINCAN_EMAIL_FROM", "").strip()
    if not sender:
        log.error("RESEND_API_KEY is set but TINCAN_EMAIL_FROM is missing; email not sent")
        return SendResult(False, "resend", "missing_from")
    body = json.dumps({"from": sender, "to": [msg.to], "subject": msg.subject, "text": msg.text}).encode("utf-8")
    req = urllib.request.Request(
        RESEND_ENDPOINT,
        data=body,
        method="POST",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            ok = 200 <= resp.status < 300
    except urllib.error.HTTPError as exc:
        log.error("Resend rejected email to %s (HTTP %s)", mask_email(msg.to), exc.code)
        return SendResult(False, "resend", f"http_{exc.code}")
    except Exception as exc:  # network errors
        log.error("Resend request failed for %s: %s", mask_email(msg.to), type(exc).__name__)
        return SendResult(False, "resend", "network_error")
    return SendResult(ok, "resend", "" if ok else "unexpected_status")


def _log_only(msg: EmailMessage) -> SendResult:
    log.warning(
        "Email delivery is not configured (set RESEND_API_KEY); a message to %s was issued but NOT delivered",
        mask_email(msg.to),
    )
    if os.environ.get("TINCAN_EMAIL_DEV_LOG") == "1" and not is_production():
        log.warning("[dev only] undelivered email to %s: %s | %s", mask_email(msg.to), msg.subject, msg.text)
    return SendResult(False, "log", "not_configured")


_custom_sender: Optional[Callable[[EmailMessage], SendResult]] = None


def set_email_sender(sender: Optional[Callable[[EmailMessage], SendResult]]) -> None:
    """Override the transport (tests, or another provider). ``None`` restores the default."""
    global _custom_sender
    _custom_sender = sender


def send_email(to: str, subject: str, text: str) -> SendResult:
    msg = EmailMessage(to=to, subject=subject, text=text)
    if _custom_sender is not None:
        return _custom_sender(msg)
    if os.environ.get("RESEND_API_KEY", "").strip():
        return _send_via_resend(msg)
    return _log_only(msg)
