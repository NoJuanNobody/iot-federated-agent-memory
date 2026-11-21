# TinCan Federated CRDT Mesh — Security & Threat Model (`AI-240`)

## 1. Security Goals

TinCan synchronizes agent knowledge-graph state across untrusted local networks (LAN, Wi-Fi Direct, ad-hoc wireless, or off-grid radio links) without relying on a central authority. Every CRDT delta must satisfy:

1. **Authenticity & Non-Repudiation:** Receivers can cryptographically verify which peer authored a delta using that peer's Ed25519 public key (`tc:<base32>` address).
2. **Integrity:** Any in-transit bit flip or malicious payload modification is detected before the delta can mutate local CRDT state.
3. **Authorization (Peer Trust):** Only deltas signed by keys present in the local `TrustStore` (pinned explicitly or via opt-in TOFU) are accepted into the CRDT state store.

---

## 2. Adversary Model

We assume a **Dolev-Yao network adversary** on the local transport medium (e.g., compromised Wi-Fi router, rogue LAN host, or radio interceptor) who can:
- Eavesdrop on cleartext UDP/radio frames.
- Modify, corrupt, or truncate framed CRDT deltas in transit.
- Forge new deltas claiming to originate from a legitimate `node_id`.
- Replay previously observed valid deltas.
- Inject deltas from an unknown / unauthorized Ed25519 keypair.

**Out of scope for `AI-240`:**
- Compromise of a trusted peer's local private key on disk (device physical compromise).
- Traffic-analysis resistance or RF jamming (layer-1 DoS).
- Payload confidentiality on broadcast links (orthogonal; can be layered via TinCan's X25519 `SealedBox` or QUIC/Reticulum link encryption).

---

## 3. Cryptographic Design

- **Identity Primitive:** Each mesh node holds an Ed25519 signing keypair (`TinCanIdentity`, `PyNaCl` / libsodium) whose canonical identifier is `tc:<base32(verify_key)>`.
- **Canonical Signed Payload:** Before signing, the delta dictionary (excluding `signature`) is serialized with deterministic canonical JSON (`sort_keys=True, separators=(",", ":")`) and prefixed with a domain separation tag (`b"TINCAN-CRDT-DELTA-V1\x00"`).
- **Signature Verification:** On receipt (`process_incoming_transport` and `merge_remote_delta`), when signature verification is enabled:
  1. Frame framing, CRC32, and SHA-256 are checked first (`FrameIntegrityError`).
  2. `sender_pubkey` and `signature` must be present; otherwise `DeltaAuthenticationError` is raised.
  3. `TrustStore.resolve_verify_key(node_id, sender_pubkey)` confirms the public key is trusted for `node_id` (preventing key substitution / spoofing).
  4. `VerifyKey.verify(canonical_bytes, sig_bytes)` verifies the Ed25519 signature; any mismatch raises `DeltaAuthenticationError` and the delta is rejected without updating clocks, `seen_delta_hashes`, or CRDT state.

---

## 4. Attack Matrix & Mitigations

| Attack Vector | Mechanism | Mitigation in TinCan |
|---|---|---|
| **In-transit tampering** | Attacker edits `value`, `key`, `vclock`, or `operation` and recomputes CRC32 + SHA-256 | Ed25519 signature covers all canonical delta fields; verification fails with `DeltaAuthenticationError`. |
| **Sender spoofing / forgery** | Attacker fabricates a delta with victim's `node_id` and signs with attacker's key | `TrustStore` binds `node_id -> trusted VerifyKey`; mismatched or untrusted key is rejected. |
| **Replay attack** | Attacker re-transmits an old valid signed delta | `seen_delta_hashes` deduplication + CRDT semilattice idempotence (replaying an already-applied delta is a no-op and cannot regress vector clocks or HLCs). |
| **Unauthorized peer injection** | Rogue node broadcasts validly self-signed deltas | Strict `TrustStore` mode (`trust_on_first_use=False`) rejects unknown keys until explicitly pinned. |
| **Clock manipulation by untrusted node** | Rogue node sends huge HLC/vector clock values | Rejected before `VectorClock.merge()` or `HLC.receive()` executes. |
