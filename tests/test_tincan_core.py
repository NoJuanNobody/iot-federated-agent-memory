"""Unit tests for TinCan 2 cryptographic core and addressing library."""

import json
import os
import time
import pytest
import nacl.public
import nacl.signing

from iot_federated_agent_memory.tincan_core import (
    ContactBook,
    DecryptionError,
    InvalidAddressError,
    KeyConflictError,
    TinCanIdentity,
    address_to_curve25519_pubkey,
    address_to_verify_key,
    canonical_envelope_bytes,
    decode_address,
    encode_address,
    generate_identity,
    open_payload,
    pubkey_to_address,
    seal_payload,
    sign_envelope,
    validate_address,
    verify_envelope,
)


class TestIdentityAndAddressing:
    """Tests for TinCanIdentity, key derivation, and tc: address formatting."""

    def test_identity_generation_and_properties(self):
        id1 = generate_identity()
        assert isinstance(id1, TinCanIdentity)
        assert isinstance(id1.signing_key, nacl.signing.SigningKey)
        assert isinstance(id1.verify_key, nacl.signing.VerifyKey)
        assert isinstance(id1.encryption_private_key, nacl.public.PrivateKey)
        assert isinstance(id1.encryption_public_key, nacl.public.PublicKey)
        assert id1.address.startswith("tc:")
        assert len(id1.address) == 55  # 'tc:' (3) + 52 base32 chars
        assert id1.current_seq == 0
        assert id1.next_seq() == 1
        assert id1.next_seq() == 2

    def test_deterministic_identity_from_seed(self):
        seed = b"32_byte_seed_deterministic_test!"
        id1 = TinCanIdentity.from_seed(seed)
        id2 = TinCanIdentity.from_seed(seed)
        assert id1.address == id2.address
        assert bytes(id1.verify_key) == bytes(id2.verify_key)
        assert bytes(id1.encryption_public_key) == bytes(id2.encryption_public_key)

    def test_identity_from_private_bytes(self):
        id1 = generate_identity()
        priv_bytes = bytes(id1.signing_key)
        id2 = TinCanIdentity.from_private_bytes(priv_bytes)
        assert id1.address == id2.address
        assert bytes(id1.verify_key) == bytes(id2.verify_key)

    def test_address_encode_and_decode_roundtrip(self):
        for _ in range(25):
            raw_key = os.urandom(32)
            addr = encode_address(raw_key)
            assert addr.startswith("tc:")
            assert len(addr) == 55
            assert addr.islower()
            decoded = decode_address(addr)
            assert decoded == raw_key
            assert validate_address(addr) is True

    def test_address_validation_negative(self):
        # Missing prefix
        assert validate_address("abcdef" * 8) is False
        # Too short / too long
        assert validate_address("tc:abc") is False
        assert validate_address("tc:" + "a" * 51) is False
        assert validate_address("tc:" + "a" * 53) is False
        # Invalid base32 chars (1, 8, 9, 0 are not in RFC 4648 base32)
        assert validate_address("tc:" + "8" * 52) is False
        assert validate_address("tc:" + "9" * 52) is False
        # Non-string types
        assert validate_address(None) is False
        assert validate_address(12345) is False
        assert validate_address(b"tc:" + b"a" * 52) is False

    def test_decode_address_exceptions(self):
        with pytest.raises(InvalidAddressError, match="prefix"):
            decode_address("wrong:abcdef")
        with pytest.raises(InvalidAddressError, match="length"):
            decode_address("tc:short")
        with pytest.raises(InvalidAddressError):
            decode_address("tc:" + "9" * 52)

    def test_pubkey_to_address_conversions(self):
        ident = generate_identity()
        assert pubkey_to_address(ident.verify_key) == ident.address
        assert pubkey_to_address(bytes(ident.verify_key)) == ident.address
        assert pubkey_to_address(ident) == ident.address
        assert pubkey_to_address(ident.address) == ident.address

    def test_address_to_curve25519_pubkey(self):
        ident = generate_identity()
        curve_pk = address_to_curve25519_pubkey(ident.address)
        assert isinstance(curve_pk, nacl.public.PublicKey)
        assert bytes(curve_pk) == bytes(ident.encryption_public_key)


class TestSealedDelivery:
    """Tests for X25519 SealedBox encryption and open_payload decryption."""

    def test_alice_bob_seal_and_open_roundtrip(self):
        alice = generate_identity()
        bob = generate_identity()

        secret_message = "Confidential telemetry report: temperature=22.4C, status=NOMINAL."

        # Alice seals for Bob using Bob's address
        ciphertext_b64 = seal_payload(bob.address, secret_message)
        assert isinstance(ciphertext_b64, str)
        assert ciphertext_b64 != secret_message

        # Bob opens using his encryption private key
        decrypted = open_payload(bob.encryption_private_key, ciphertext_b64)
        assert decrypted == secret_message

        # Bob opens using his TinCanIdentity directly
        decrypted_ident = open_payload(bob, ciphertext_b64)
        assert decrypted_ident == secret_message

        # Bob opens using his SigningKey (which auto-converts)
        decrypted_sk = open_payload(bob.signing_key, ciphertext_b64)
        assert decrypted_sk == secret_message

        # Identity method bob.open_sealed
        assert bob.open_sealed(ciphertext_b64) == secret_message

    def test_seal_with_various_recipient_representations(self):
        bob = generate_identity()
        msg = "Multi-target seal test"

        # Seal using PublicKey
        ct1 = seal_payload(bob.encryption_public_key, msg)
        assert bob.open_sealed(ct1) == msg

        # Seal using VerifyKey
        ct2 = seal_payload(bob.verify_key, msg)
        assert bob.open_sealed(ct2) == msg

        # Seal using TinCanIdentity
        ct3 = seal_payload(bob, msg)
        assert bob.open_sealed(ct3) == msg

        # Seal using identity helper alice.seal_for
        alice = generate_identity()
        ct4 = alice.seal_for(bob.address, msg)
        assert bob.open_sealed(ct4) == msg

    def test_seal_payload_types(self):
        bob = generate_identity()

        # Unicode with emojis
        unicode_str = "🚀 IoT Edge Mesh Telemetry 📡: 42°C & OK!"
        ct_unicode = seal_payload(bob.address, unicode_str)
        assert bob.open_sealed(ct_unicode) == unicode_str

        # Raw bytes
        raw_bytes = b"binary-data-buffer-\x00\x01\x02\xff"
        ct_bytes = seal_payload(bob.address, raw_bytes)
        assert bob.open_sealed_bytes(ct_bytes) == raw_bytes
        assert bob.open_sealed(ct_bytes).encode("latin-1") == raw_bytes

        # JSON object / dict
        obj = {"sensor": "gyro", "coords": [10.5, 20.2, -5.1]}
        ct_json = seal_payload(bob.address, obj)
        assert json.loads(bob.open_sealed(ct_json)) == obj

    def test_wrong_recipient_cannot_decrypt(self):
        bob = generate_identity()
        eve = generate_identity()

        ciphertext = seal_payload(bob.address, "Top Secret Data")

        with pytest.raises(DecryptionError, match="SealedBox decryption failed"):
            open_payload(eve.encryption_private_key, ciphertext)

        with pytest.raises(DecryptionError):
            eve.open_sealed(ciphertext)

    def test_corrupted_ciphertext_fails(self):
        bob = generate_identity()
        ciphertext = seal_payload(bob.address, "Sensitive Information")

        # Corrupt the base64 string deterministically
        flip_char = "B" if ciphertext[0] == "A" else "A"
        corrupted = flip_char + ciphertext[1:]
        with pytest.raises(DecryptionError):
            bob.open_sealed(corrupted)

        # Invalid base64 characters
        with pytest.raises(DecryptionError):
            bob.open_sealed("!!!not-valid-base64???")


class TestEnvelopeSigningAndVerification:
    """Tests for envelope structure, canonical serialization, signing, and tamper rejection."""

    def test_sign_and_verify_valid_envelope(self):
        alice = generate_identity()
        bob = generate_identity()

        envelope = {
            "sender": alice.address,
            "recipient": bob.address,
            "timestamp": time.time(),
            "seq": 1,
            "payload": {"status": "heartbeat", "battery": 98},
        }

        signed = sign_envelope(alice.signing_key, envelope)
        assert "signature" in signed
        assert isinstance(signed["signature"], str)

        # Verify using envelope's self-contained sender address
        assert verify_envelope(signed) is True

        # Verify specifying Alice's VerifyKey explicitly
        assert verify_envelope(signed, verify_key=alice.verify_key) is True

        # Verify specifying Alice's address explicitly
        assert verify_envelope(signed, verify_key=alice.address) is True

    def test_identity_create_envelope_helper(self):
        alice = generate_identity()
        bob = generate_identity()

        signed = alice.create_envelope(recipient=bob.address, payload="Ping from Alice")
        assert signed["sender"] == alice.address
        assert signed["recipient"] == bob.address
        assert signed["seq"] == 1
        assert "signature" in signed
        assert verify_envelope(signed) is True

    def test_tamper_rejection_payload(self):
        alice = generate_identity()
        bob = generate_identity()

        signed = alice.create_envelope(bob.address, {"command": "read_sensor"})
        assert verify_envelope(signed) is True

        # Tamper payload
        signed["payload"] = {"command": "format_disk"}
        assert verify_envelope(signed) is False

    def test_tamper_rejection_seq(self):
        alice = generate_identity()
        bob = generate_identity()

        signed = alice.create_envelope(bob.address, "msg")
        assert verify_envelope(signed) is True

        # Replay attack with modified sequence number
        signed["seq"] = 9999
        assert verify_envelope(signed) is False

    def test_tamper_rejection_timestamp(self):
        alice = generate_identity()
        bob = generate_identity()

        signed = alice.create_envelope(bob.address, "msg")
        assert verify_envelope(signed) is True

        signed["timestamp"] += 10.0
        assert verify_envelope(signed) is False

    def test_tamper_rejection_recipient(self):
        alice = generate_identity()
        bob = generate_identity()
        eve = generate_identity()

        signed = alice.create_envelope(bob.address, "msg")
        assert verify_envelope(signed) is True

        # Divert message to Eve
        signed["recipient"] = eve.address
        assert verify_envelope(signed) is False

    def test_tamper_rejection_sender(self):
        alice = generate_identity()
        bob = generate_identity()
        mallory = generate_identity()

        signed = alice.create_envelope(bob.address, "msg")
        assert verify_envelope(signed) is True

        # Mallory claims to be sender
        signed["sender"] = mallory.address
        assert verify_envelope(signed) is False

    def test_tamper_rejection_signature(self):
        alice = generate_identity()
        bob = generate_identity()

        signed = alice.create_envelope(bob.address, "msg")
        assert verify_envelope(signed) is True

        # Corrupt signature string
        sig_chars = list(signed["signature"])
        sig_chars[5] = "A" if sig_chars[5] != "A" else "B"
        signed["signature"] = "".join(sig_chars)
        assert verify_envelope(signed) is False

    def test_verify_envelope_malformed_inputs(self):
        alice = generate_identity()
        signed = alice.create_envelope("tc:fake", "payload")

        # Missing required fields
        for field in ("sender", "recipient", "timestamp", "seq", "payload", "signature"):
            bad_env = dict(signed)
            del bad_env[field]
            assert verify_envelope(bad_env) is False

        # Non-dict inputs
        assert verify_envelope(None) is False
        assert verify_envelope("string") is False
        assert verify_envelope([]) is False

        # Invalid sender address
        bad_sender = dict(signed)
        bad_sender["sender"] = "invalid_address"
        assert verify_envelope(bad_sender) is False


class TestContactBookTOFU:
    """Tests for ContactBook and Trust-On-First-Use key pinning."""

    def test_pin_alias_on_first_use(self):
        book = ContactBook()
        alice = generate_identity()

        assert "alice" not in book
        assert book.pin("alice", alice.address) is True
        assert "alice" in book
        assert book.get_address("alice") == alice.address
        assert len(book) == 1

    def test_idempotent_repin_same_address(self):
        book = ContactBook()
        alice = generate_identity()

        assert book.pin("alice", alice.address, metadata={"role": "sensor"}) is True
        # Re-pinning same address succeeds
        assert book.pin("alice", alice.address, metadata={"version": "2.0"}) is True
        assert book.get_address("alice") == alice.address
        contact = book.get_contact("alice")
        assert contact["metadata"]["role"] == "sensor"
        assert contact["metadata"]["version"] == "2.0"

    def test_key_conflict_detected_and_raises(self):
        book = ContactBook(raise_on_conflict=True)
        alice_real = generate_identity()
        alice_imposter = generate_identity()

        # TOFU pins real Alice
        book.pin("alice", alice_real.address)

        # Imposter tries to bind to the alias "alice"
        with pytest.raises(KeyConflictError, match="TOFU conflict for alias 'alice'"):
            book.pin("alice", alice_imposter.address)

        # Address remains pinned to real Alice
        assert book.get_address("alice") == alice_real.address

    def test_key_conflict_without_raising(self):
        book = ContactBook(raise_on_conflict=False)
        alice_real = generate_identity()
        alice_imposter = generate_identity()

        book.pin("alice", alice_real.address)
        # Should return False without raising
        success = book.pin("alice", alice_imposter.address)
        assert success is False
        assert book.get_address("alice") == alice_real.address

    def test_pin_invalid_address_raises(self):
        book = ContactBook()
        with pytest.raises(InvalidAddressError):
            book.pin("charlie", "tc:bad_address")

    def test_verify_and_verify_or_pin(self):
        book = ContactBook()
        bob = generate_identity()
        mallory = generate_identity()

        # Unknown contact verify returns False
        assert book.verify("bob", bob.address) is False

        # verify_or_pin pins on first use
        assert book.verify_or_pin("bob", bob.address) is True

        # Now verify succeeds
        assert book.verify("bob", bob.address) is True

        # Mismatched address triggers conflict
        with pytest.raises(KeyConflictError, match="TOFU key mismatch"):
            book.verify("bob", mallory.address)

    def test_dictionary_style_access(self):
        book = ContactBook()
        node1 = generate_identity()

        book["node1"] = node1.address
        assert book["node1"] == node1.address

        with pytest.raises(KeyError):
            _ = book["unknown_node"]

    def test_remove_and_clear(self):
        book = ContactBook()
        a = generate_identity()
        b = generate_identity()

        book.pin("a", a.address)
        book.pin("b", b.address)
        assert len(book) == 2

        assert book.remove("a") is True
        assert "a" not in book
        assert len(book) == 1

        book.clear()
        assert len(book) == 0

    def test_list_contacts_and_reverse_lookup(self):
        book = ContactBook()
        id1 = generate_identity()

        book.pin("primary_hub", id1.address)
        book.pin("backup_hub", id1.address)

        contacts = book.list_contacts()
        assert "primary_hub" in contacts
        assert "backup_hub" in contacts

        aliases = book.get_aliases_for_address(id1.address)
        assert aliases == ["backup_hub", "primary_hub"]


class TestEndToEndAliceBobWorkflow:
    """Full integration test: Alice and Bob establish TOFU pinning, exchange sealed & signed envelopes."""

    def test_full_roundtrip_exchange(self):
        alice = generate_identity()
        bob = generate_identity()

        alice_book = ContactBook()
        bob_book = ContactBook()

        # 1. Initial discovery / TOFU pinning
        alice_book.pin("bob", bob.address)
        bob_book.pin("alice", alice.address)

        # 2. Alice prepares confidential message for Bob
        secret_order = {"action": "dispatch_rescue_swarm", "target_hex": "882681a339fffff", "priority": 1}
        sealed_payload = alice.seal_for(alice_book["bob"], secret_order)

        # 3. Alice wraps in signed envelope
        envelope = alice.create_envelope(recipient=bob.address, payload=sealed_payload)

        # 4. Bob receives envelope: verifies outer signature
        assert verify_envelope(envelope) is True

        # 5. Bob verifies sender identity against his TOFU ContactBook
        assert bob_book.verify("alice", envelope["sender"]) is True

        # 6. Bob decrypts sealed payload
        decrypted_raw = bob.open_sealed(envelope["payload"])
        decrypted_order = json.loads(decrypted_raw)
        assert decrypted_order == secret_order

        # 7. Bob prepares signed acknowledgment sealed for Alice
        ack_msg = {"status": "acknowledged", "task_id": "TSK-9402", "eta_seconds": 120}
        bob_sealed_ack = bob.seal_for(bob_book["alice"], ack_msg)
        bob_envelope = bob.create_envelope(recipient=alice.address, payload=bob_sealed_ack)

        # 8. Alice receives Bob's envelope
        assert verify_envelope(bob_envelope) is True
        assert alice_book.verify("bob", bob_envelope["sender"]) is True
        decrypted_ack = json.loads(alice.open_sealed(bob_envelope["payload"]))
        assert decrypted_ack["status"] == "acknowledged"
        assert decrypted_ack["task_id"] == "TSK-9402"
