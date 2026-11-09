"""Tests for TinCan Admin Moderator & Mesh Roster Telemetry."""

import json
import tempfile
import pytest

from iot_federated_agent_memory.tincan_mcp import TinCanMCPClient
from iot_federated_agent_memory.tincan_cli import main as tincan_cli_main


def test_admin_role_persistence():
    """Verify operator can set, persist, and retrieve admin moderator role."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        client = TinCanMCPClient(config_dir=tmp_dir, alias="operator")
        assert client.get_my_role() == "peer"
        assert client.tincan_whoami()["is_admin"] is False

        # Set to admin
        client.set_my_role("admin")
        assert client.get_my_role() == "admin"
        assert client.tincan_whoami()["role"] == "admin"
        assert client.tincan_whoami()["is_admin"] is True

        # Reload client from same directory
        client2 = TinCanMCPClient(config_dir=tmp_dir, alias="operator")
        assert client2.get_my_role() == "admin"
        assert client2.tincan_whoami()["role"] == "admin"
        assert client2.tincan_whoami()["is_admin"] is True


def test_admin_contact_role():
    """Verify contacts can be pinned with admin or moderator role."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        client = TinCanMCPClient(config_dir=tmp_dir, alias="alice")
        res = client.tincan_add_contact("chief_mod", "tc:vsp2iduq4tmorbgjomy4dcf7n7gsmf7w5lsvqcwaftqkesstk5fq", role="moderator")
        assert res["role"] == "moderator"

        contacts = client.tincan_list_contacts()
        assert len(contacts) == 1
        assert contacts[0]["role"] == "moderator"

        # Update role to admin
        upd = client.set_contact_role("chief_mod", role="admin")
        assert upd["role"] == "admin"


def test_cli_admin_role_and_whoami(capsys):
    """Verify CLI admin role setting and whoami badge output."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Run admin role self admin
        ret = tincan_cli_main(["--dir", tmp_dir, "admin", "role", "self", "admin"])
        assert ret == 0
        captured = capsys.readouterr()
        assert "Successfully set local identity role to: ADMIN" in captured.out

        # Run whoami
        ret = tincan_cli_main(["--dir", tmp_dir, "whoami"])
        assert ret == 0
        captured = capsys.readouterr()
        assert "🛡️ ADMIN MODERATOR" in captured.out
