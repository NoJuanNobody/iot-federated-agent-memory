"""
Unit and integration tests for TinCan Blind Relay, MCP Protocol Tools, and Server Endpoints.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
import time
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from iot_federated_agent_memory.tincan_core import (
    TinCanIdentity,
    verify_envelope,
)
from iot_federated_agent_memory.tincan_relay import TinCanBlindRelay
from iot_federated_agent_memory.tincan_mcp import (
    TinCanMCPClient,
    get_default_client,
    set_default_client,
    tincan_whoami,
    tincan_send,
    tincan_read,
    tincan_list_contacts,
    tincan_add_contact,
    handle_mcp_request,
)
from iot_federated_agent_memory.tincan_cli import main as tincan_cli_main
from server import MeshGatewayHandler, tincan_relay as server_tincan_relay


@pytest.fixture
def temp_relay():
    """Provides a fresh in-memory TinCanBlindRelay."""
    relay = TinCanBlindRelay(":memory:")
    yield relay
    relay.clear()


@pytest.fixture
def temp_dirs():
    """Provides two separate temporary directories for Alice and Bob config."""
    with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
        yield d1, d2


def test_relay_mailbox_storage_and_monotonic_seq(temp_relay):
    """Test that relay stores ciphertext mailboxes per recipient with monotonic seq."""
    alice = TinCanIdentity.generate()
    bob = TinCanIdentity.generate()
    charlie = TinCanIdentity.generate()

    # Alice sends 2 messages to Bob
    env1 = alice.create_envelope(recipient=bob.address, payload="ciphertext_bob_1", envelope_id="e1")
    env2 = alice.create_envelope(recipient=bob.address, payload="ciphertext_bob_2", envelope_id="e2")
    res1 = temp_relay.send(env1)
    res2 = temp_relay.send(env2)

    assert res1["status"] == "ok"
    assert res1["seq"] == 1
    assert res2["status"] == "ok"
    assert res2["seq"] == 2

    # Alice sends 1 message to Charlie (Charlie starts at seq 1)
    env3 = alice.create_envelope(recipient=charlie.address, payload="ciphertext_charlie_1", envelope_id="e3")
    res3 = temp_relay.send(env3)
    assert res3["status"] == "ok"
    assert res3["seq"] == 1

    # Verify Bob's mailbox
    bob_inbox = temp_relay.inbox(bob.address, since_seq=0)
    assert bob_inbox["count"] == 2
    assert bob_inbox["latest_seq"] == 2
    assert [m["seq"] for m in bob_inbox["messages"]] == [1, 2]
    assert [m["envelope_id"] for m in bob_inbox["messages"]] == ["e1", "e2"]

    # Verify since_seq filtering
    bob_inbox_since1 = temp_relay.inbox(bob.address, since_seq=1)
    assert bob_inbox_since1["count"] == 1
    assert bob_inbox_since1["latest_seq"] == 2
    assert bob_inbox_since1["messages"][0]["seq"] == 2

    # Verify relay never stores plaintext
    cur = temp_relay.conn.cursor()
    cur.execute("SELECT ciphertext FROM envelopes WHERE recipient = ?", (bob.address,))
    rows = cur.fetchall()
    assert rows[0][0] == "ciphertext_bob_1"
    assert rows[1][0] == "ciphertext_bob_2"


def test_relay_signature_verification_and_tamper_rejection(temp_relay):
    """Test relay rejects tampered envelopes and invalid addresses."""
    alice = TinCanIdentity.generate()
    bob = TinCanIdentity.generate()

    valid_env = alice.create_envelope(recipient=bob.address, payload="sealed_secret")
    # Tamper with signature
    tampered_sig = dict(valid_env)
    tampered_sig["signature"] = "A" * 88
    with pytest.raises(ValueError, match="Invalid envelope signature"):
        temp_relay.send(tampered_sig)

    # Tamper with payload after signing
    tampered_payload = dict(valid_env)
    tampered_payload["payload"] = "modified_payload"
    with pytest.raises(ValueError, match="Invalid envelope signature"):
        temp_relay.send(tampered_payload)

    # Invalid recipient address format
    bad_recipient = dict(valid_env)
    bad_recipient["recipient"] = "invalid_address"
    with pytest.raises(ValueError, match="Invalid recipient"):
        temp_relay.send(bad_recipient)


def test_relay_long_polling(temp_relay):
    """Test long polling waits and wakes up upon new message arrival."""
    alice = TinCanIdentity.generate()
    bob = TinCanIdentity.generate()

    results = []

    def poller():
        res = temp_relay.inbox(bob.address, since_seq=0, timeout=2.0)
        results.append(res)

    t = threading.Thread(target=poller)
    t.start()

    time.sleep(0.1)
    assert len(results) == 0  # Still waiting

    # Alice sends message to Bob
    env = alice.create_envelope(recipient=bob.address, payload="delayed_msg")
    temp_relay.send(env)

    t.join(timeout=3.0)
    assert len(results) == 1
    assert results[0]["count"] == 1
    assert results[0]["messages"][0]["payload"] == "delayed_msg"


def test_relay_whoami_and_stats(temp_relay):
    """Test relay status and mailbox metadata queries."""
    alice = TinCanIdentity.generate()
    bob = TinCanIdentity.generate()

    env = alice.create_envelope(recipient=bob.address, payload="msg1")
    temp_relay.send(env)

    # General whoami
    info = temp_relay.whoami()
    assert info["status"] == "online"
    assert info["service"] == "tincan-blind-relay"
    assert info["total_mailboxes"] == 1
    assert info["total_envelopes"] == 1

    # Address-specific whoami
    bob_info = temp_relay.whoami(address=bob.address)
    assert bob_info["mailbox_stats"]["address"] == bob.address
    assert bob_info["mailbox_stats"]["count"] == 1
    assert bob_info["mailbox_stats"]["latest_seq"] == 1

    # Stats
    stats = temp_relay.get_stats()
    assert stats["status"] == "online"
    assert stats["total_envelopes"] == 1


def test_mcp_client_whoami_and_contacts(temp_relay, temp_dirs):
    """Test TinCanMCPClient identity initialization, whoami, and TOFU contacts."""
    d1, d2 = temp_dirs
    alice = TinCanMCPClient(config_dir=d1, alias="alice", relay=temp_relay)
    bob = TinCanMCPClient(config_dir=d2, alias="bob", relay=temp_relay)

    who = alice.tincan_whoami()
    assert who["alias"] == "alice"
    assert who["address"].startswith("tc:")
    assert len(who["public_key"]) == 64  # 32 bytes hex
    assert who["contacts_count"] == 0

    # Pin contact
    pin = alice.tincan_add_contact(alias="bob", address=bob.address)
    assert pin["status"] == "pinned"
    assert pin["alias"] == "bob"
    assert pin["address"] == bob.address

    # List contacts
    contacts = alice.tincan_list_contacts()
    assert len(contacts) == 1
    assert contacts[0]["alias"] == "bob"
    assert contacts[0]["address"] == bob.address


def test_mcp_end_to_end_send_and_read(temp_relay, temp_dirs):
    """Test encrypted send and verified read through MCP client."""
    d1, d2 = temp_dirs
    alice = TinCanMCPClient(config_dir=d1, alias="alice", relay=temp_relay)
    bob = TinCanMCPClient(config_dir=d2, alias="bob", relay=temp_relay)

    alice.tincan_add_contact("bob", bob.address)
    bob.tincan_add_contact("alice", alice.address)

    # Alice sends to 'bob' via alias
    send_res = alice.tincan_send(recipient_address="bob", message="Hello Agent Bob!", speak=True)
    assert send_res["status"] == "sent"
    assert send_res["seq"] == 1
    assert send_res["speak"] is True
    assert send_res["alias"] == "bob"

    # Bob reads inbox
    msgs = bob.tincan_read(since_seq=0)
    assert len(msgs) == 1
    m = msgs[0]
    assert m["seq"] == 1
    assert m["message"] == "Hello Agent Bob!"
    assert m["speak"] is True
    assert m["verified"] is True
    assert m["sender"] == alice.address
    assert m["sender_alias"] == "alice"

    # Reading again with since_seq=1 returns empty
    empty_msgs = bob.tincan_read(since_seq=1)
    assert len(empty_msgs) == 0


def test_module_level_mcp_tools(temp_relay, temp_dirs):
    """Test module-level MCP functions with configured default client."""
    d1, d2 = temp_dirs
    client1 = TinCanMCPClient(config_dir=d1, alias="agent1", relay=temp_relay)
    client2 = TinCanMCPClient(config_dir=d2, alias="agent2", relay=temp_relay)

    set_default_client(client1)

    who = tincan_whoami()
    assert who["alias"] == "agent1"

    tincan_add_contact("agent2", client2.address)
    contacts = tincan_list_contacts()
    assert len(contacts) == 1
    assert contacts[0]["alias"] == "agent2"

    send_res = tincan_send("agent2", "Top secret data", speak=False)
    assert send_res["status"] == "sent"

    # Switch default to agent2 and read
    set_default_client(client2)
    inbox = tincan_read(since_seq=0)
    assert len(inbox) == 1
    assert inbox[0]["message"] == "Top secret data"
    assert inbox[0]["verified"] is True


def test_mcp_jsonrpc_protocol(temp_relay, temp_dirs):
    """Test JSON-RPC 2.0 MCP interface for tools/list and tools/call."""
    d1, _ = temp_dirs
    client = TinCanMCPClient(config_dir=d1, alias="tester", relay=temp_relay)

    # 1. initialize
    init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
    init_resp = handle_mcp_request(init_req, client=client)
    assert init_resp["result"]["serverInfo"]["name"] == "tincan-mcp"

    # 2. tools/list
    list_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
    list_resp = handle_mcp_request(list_req, client=client)
    tools = list_resp["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "tincan_whoami" in tool_names
    assert "tincan_send" in tool_names
    assert "tincan_read" in tool_names
    assert "tincan_list_contacts" in tool_names
    assert "tincan_add_contact" in tool_names

    # 3. tools/call: tincan_whoami
    call_req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "tincan_whoami", "arguments": {}},
    }
    call_resp = handle_mcp_request(call_req, client=client)
    content_text = call_resp["result"]["content"][0]["text"]
    parsed = json.loads(content_text)
    assert parsed["alias"] == "tester"
    assert parsed["address"].startswith("tc:")

    # 4. Unknown tool
    unknown_req = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {"name": "non_existent_tool", "arguments": {}},
    }
    err_resp = handle_mcp_request(unknown_req, client=client)
    assert "error" in err_resp
    assert err_resp["error"]["code"] == -32601


def test_server_http_endpoints():
    """Test HTTP endpoints /api/tincan/send, /api/tincan/inbox, /api/tincan/whoami, and /api/status."""
    server_tincan_relay.clear()

    # Start test HTTP server on ephemeral port (port 0)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), MeshGatewayHandler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True
    thread.start()

    base_url = f"http://127.0.0.1:{port}"

    try:
        # Create 2 identities
        alice = TinCanIdentity.generate()
        bob = TinCanIdentity.generate()

        # Check /api/status includes tincan_relay
        status_req = urllib.request.Request(f"{base_url}/api/status")
        with urllib.request.urlopen(status_req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "online"
            assert "tincan_relay" in data
            assert data["tincan_relay"]["status"] == "online"

        # Check /api/tincan/whoami
        who_req = urllib.request.Request(f"{base_url}/api/tincan/whoami")
        with urllib.request.urlopen(who_req) as resp:
            who = json.loads(resp.read().decode("utf-8"))
            assert who["service"] == "tincan-blind-relay"

        # Alice sends sealed message to Bob via HTTP POST /api/tincan/send
        ct = alice.seal_for(bob.address, "Hello over HTTP!")
        env = alice.create_envelope(recipient=bob.address, payload=ct, envelope_id="http-1", speak=True)

        post_req = urllib.request.Request(
            f"{base_url}/api/tincan/send",
            data=json.dumps(env).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(post_req) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            assert res["status"] == "ok"
            assert res["seq"] == 1
            assert res["recipient"] == bob.address

        # Bob fetches inbox via HTTP GET /api/tincan/inbox
        inbox_url = f"{base_url}/api/tincan/inbox?address={urllib.parse.quote(bob.address)}&since_seq=0"
        inbox_req = urllib.request.Request(inbox_url)
        with urllib.request.urlopen(inbox_req) as resp:
            inbox_res = json.loads(resp.read().decode("utf-8"))
            assert inbox_res["status"] == "ok"
            assert inbox_res["count"] == 1
            recvd_envelope = inbox_res["messages"][0]
            assert recvd_envelope["seq"] == 1
            raw_dict = json.loads(recvd_envelope["raw_envelope"])
            assert verify_envelope(raw_dict) is True

            # Bob decrypts payload
            plain = bob.open_sealed(recvd_envelope["payload"])
            assert plain == "Hello over HTTP!"

        # Also test Bob using TinCanMCPClient pointing to the HTTP server
        with tempfile.TemporaryDirectory() as bob_dir:
            bob_client = TinCanMCPClient(relay_url=base_url, config_dir=bob_dir, alias="bob_http")
            bob_client.identity = bob
            bob_client.address = bob.address
            bob_msgs = bob_client.tincan_read(since_seq=0)
            assert len(bob_msgs) == 1
            assert bob_msgs[0]["message"] == "Hello over HTTP!"
            assert bob_msgs[0]["verified"] is True

    finally:
        httpd.shutdown()
        server_tincan_relay.clear()


def test_tincan_cli_execution(temp_dirs):
    """Test CLI commands whoami, add-contact, contacts."""
    d1, _ = temp_dirs
    test_identity = TinCanIdentity.generate()

    # CLI whoami
    code = tincan_cli_main(["--dir", d1, "--as", "cli_user", "whoami", "--json"])
    assert code == 0

    # CLI add-contact
    code = tincan_cli_main(["--dir", d1, "--as", "cli_user", "add-contact", "peer1", test_identity.address, "--json"])
    assert code == 0

    # CLI contacts
    code = tincan_cli_main(["--dir", d1, "--as", "cli_user", "contacts", "--json"])
    assert code == 0
