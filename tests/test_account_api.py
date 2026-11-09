import json
import threading
import urllib.request
import uuid
import pytest
from server import HTTPServer, MeshGatewayHandler


@pytest.fixture(scope="module")
def live_server():
    test_port = 8992
    httpd = HTTPServer(("127.0.0.1", test_port), MeshGatewayHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{test_port}"
    httpd.shutdown()


def test_account_registration_billing_and_topup_api(live_server):
    peer_id = f"test-peer-{uuid.uuid4().hex[:8]}"
    email = f"{peer_id}@fau.edu"
    # 1. Register account
    payload = {
        "peer_id": peer_id,
        "full_name": "Billing Test User",
        "phone_number": "+15615559876",
        "email": email,
    }
    req = urllib.request.Request(
        f"{live_server}/api/account/register",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as response:
        assert response.status == 201
        data = json.loads(response.read().decode("utf-8"))
        assert data["account"]["token_balance"] == 50000

    # 2. Top-up tokens
    topup_payload = {
        "peer_id": peer_id,
        "tokens": 25000,
        "amount_usd": 2.50,
    }
    topup_req = urllib.request.Request(
        f"{live_server}/api/account/billing/topup",
        data=json.dumps(topup_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(topup_req) as response:
        assert response.status == 200
        data = json.loads(response.read().decode("utf-8"))
        assert data["account"]["token_balance"] == 75000

    # 3. Query billing summary
    with urllib.request.urlopen(f"{live_server}/api/account/billing?peer_id={peer_id}") as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["token_balance"] == 75000
        assert data["peer_id"] == peer_id
