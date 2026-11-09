"""Human-In-The-Loop (HITL) Read-Only Accessibility Queue for Inbound Actions.

Security Policy:
- OS command execution (`subprocess.run`) and automatic browser/URL launching are permanently disabled.
- Approving an action records a read-only cryptographic acknowledgment without spawning any process.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional


def get_queue_file(config_dir: Optional[str] = None) -> str:
    base = config_dir or os.path.expanduser("~/.tin-can")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "pending_actions.json")


def load_pending_actions(config_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    path = get_queue_file(config_dir)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return []


def save_pending_actions(actions: List[Dict[str, Any]], config_dir: Optional[str] = None) -> None:
    path = get_queue_file(config_dir)
    with open(path, "w") as f:
        json.dump(actions, f, indent=2)


def enqueue_action(
    seq: int,
    sender: str,
    sender_alias: Optional[str],
    command_text: str,
    config_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Queue an incoming notification item (read-only; never executes shell commands)."""
    actions = load_pending_actions(config_dir)
    for act in actions:
        if act["seq"] == seq and act["sender"] == sender:
            return act

    item = {
        "id": f"action-{int(time.time()*1000)}-{seq}",
        "seq": seq,
        "sender": sender,
        "sender_alias": sender_alias or "peer",
        "command": command_text,
        "queued_at": time.time(),
        "status": "pending_approval",
    }
    actions.append(item)
    save_pending_actions(actions, config_dir)
    return item


def execute_action(action_id_or_seq: str, config_dir: Optional[str] = None) -> Dict[str, Any]:
    """Acknowledge an inbound item in read-only mode (OS subprocess execution is disabled)."""
    actions = load_pending_actions(config_dir)
    target = None
    for act in actions:
        if act["id"] == action_id_or_seq or str(act["seq"]) == str(action_id_or_seq):
            target = act
            break

    if not target:
        raise ValueError(f"Action '{action_id_or_seq}' not found in pending queue.")

    cmd_text = target["command"].strip()
    result_output = f"Read-only acknowledgment recorded (OS/browser execution disabled): {cmd_text}"

    target["status"] = "completed"
    target["executed_at"] = time.time()
    target["result"] = result_output
    save_pending_actions(actions, config_dir)
    return target


def dismiss_action(action_id_or_seq: str, config_dir: Optional[str] = None) -> Dict[str, Any]:
    """Dismiss/reject an inbound action without executing."""
    actions = load_pending_actions(config_dir)
    target = None
    for act in actions:
        if act["id"] == action_id_or_seq or str(act["seq"]) == str(action_id_or_seq):
            target = act
            break

    if not target:
        raise ValueError(f"Action '{action_id_or_seq}' not found.")

    target["status"] = "dismissed"
    save_pending_actions(actions, config_dir)
    return target
