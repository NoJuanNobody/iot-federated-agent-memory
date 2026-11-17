"""Tests for free in-house glTF 2.0 auto-rigging & animation across glb_rigger, server, UI, and AgentSpace."""

import base64
import json
import math
import os
import struct
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

WORKTREE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKTREE_DIR not in sys.path:
    sys.path.insert(0, WORKTREE_DIR)

import pytest

from iot_federated_agent_memory.glb_rigger import pack_glb, parse_glb, rig_glb_bytes
from iot_federated_agent_memory.agent_space import (
    AgentSpaceHarness,
    SingleFileSpaceVFS,
    _TINCAN_GEN_SCRIPT,
    build_tincan_capability_manifest,
)
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI
from iot_federated_agent_memory.workstation_ui import render_workstation_window_html
import server


def _make_static_creature_glb(*, quadruped: bool = False, node_rotation=None) -> bytes:
    """Build a synthetic multi-part static GLB (torso, head, limbs, tail) with UVs + normals."""
    boxes = []
    if quadruped:
        # Elongated quadruped resting along Z axis (Y height smaller than Z depth)
        boxes.extend([
            ((0.0, 0.45, 0.0), (0.28, 0.22, 0.50)),    # torso
            ((0.0, 0.62, 0.60), (0.18, 0.18, 0.20)),   # head (+Z)
            ((-0.18, 0.18, 0.36), (0.07, 0.22, 0.07)), # front L leg
            ((0.18, 0.18, 0.36), (0.07, 0.22, 0.07)),  # front R leg
            ((-0.18, 0.18, -0.36), (0.07, 0.22, 0.07)),# rear L leg
            ((0.18, 0.18, -0.36), (0.07, 0.22, 0.07)), # rear R leg
            ((0.0, 0.55, -0.62), (0.05, 0.06, 0.18)),  # tail (-Z)
        ])
    else:
        # Upright creature (e.g. Pikachu-like proportions: ears, head, body, arms, legs, tail)
        boxes.extend([
            ((0.0, 0.55, 0.0), (0.26, 0.30, 0.22)),    # torso
            ((0.0, 1.05, 0.02), (0.22, 0.22, 0.20)),   # head
            ((-0.14, 1.38, 0.0), (0.05, 0.18, 0.04)),  # left ear
            ((0.14, 1.38, 0.0), (0.05, 0.18, 0.04)),   # right ear
            ((-0.34, 0.68, 0.04), (0.12, 0.08, 0.08)), # left arm
            ((0.34, 0.68, 0.04), (0.12, 0.08, 0.08)),  # right arm
            ((-0.14, 0.15, 0.0), (0.09, 0.16, 0.10)),  # left leg
            ((0.14, 0.15, 0.0), (0.09, 0.16, 0.10)),   # right leg
            ((0.0, 0.52, -0.34), (0.05, 0.20, 0.12)),  # tail (-Z)
        ])

    positions = []
    normals = []
    uvs = []
    indices = []

    face_defs = [
        ((0, 0, 1), [(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]),
        ((0, 0, -1), [(1, -1, -1), (-1, -1, -1), (-1, 1, -1), (1, 1, -1)]),
        ((1, 0, 0), [(1, -1, 1), (1, -1, -1), (1, 1, -1), (1, 1, 1)]),
        ((-1, 0, 0), [(-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1)]),
        ((0, 1, 0), [(-1, 1, 1), (1, 1, 1), (1, 1, -1), (-1, 1, -1)]),
        ((0, -1, 0), [(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)]),
    ]
    for (cx, cy, cz), (sx, sy, sz) in boxes:
        for nrm, quad in face_defs:
            base = len(positions)
            for qx, qy, qz in quad:
                positions.append((cx + qx * sx, cy + qy * sy, cz + qz * sz))
                normals.append(nrm)
            uvs.extend([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])
            indices.extend([base, base + 1, base + 2, base, base + 2, base + 3])

    pos_bytes = b"".join(struct.pack("<3f", *p) for p in positions)
    nrm_bytes = b"".join(struct.pack("<3f", *n) for n in normals)
    uv_bytes = b"".join(struct.pack("<2f", *u) for u in uvs)
    idx_bytes = b"".join(struct.pack("<H", i) for i in indices)

    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]
    zs = [p[2] for p in positions]

    blob = bytearray()
    def _push(raw: bytes) -> tuple:
        while len(blob) % 4 != 0:
            blob.append(0)
        off = len(blob)
        blob.extend(raw)
        return off, len(raw)

    p_off, p_len = _push(pos_bytes)
    n_off, n_len = _push(nrm_bytes)
    u_off, u_len = _push(uv_bytes)
    i_off, i_len = _push(idx_bytes)

    node = {"name": "StaticCreature", "mesh": 0}
    if node_rotation is not None:
        node["rotation"] = list(node_rotation)

    gltf = {
        "asset": {"version": "2.0", "generator": "test-static-mesh"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [node],
        "meshes": [
            {
                "name": "CreatureMesh",
                "primitives": [
                    {
                        "attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2},
                        "indices": 3,
                        "material": 0,
                    }
                ],
            }
        ],
        "materials": [{"pbrMetallicRoughness": {"baseColorFactor": [0.95, 0.82, 0.15, 1.0]}}],
        "buffers": [{"byteLength": len(blob)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": p_off, "byteLength": p_len, "target": 34962},
            {"buffer": 0, "byteOffset": n_off, "byteLength": n_len, "target": 34962},
            {"buffer": 0, "byteOffset": u_off, "byteLength": u_len, "target": 34962},
            {"buffer": 0, "byteOffset": i_off, "byteLength": i_len, "target": 34963},
        ],
        "accessors": [
            {
                "bufferView": 0, "componentType": 5126, "count": len(positions), "type": "VEC3",
                "min": [min(xs), min(ys), min(zs)], "max": [max(xs), max(ys), max(zs)],
            },
            {"bufferView": 1, "componentType": 5126, "count": len(normals), "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": len(uvs), "type": "VEC2"},
            {"bufferView": 3, "componentType": 5123, "count": len(indices), "type": "SCALAR"},
        ],
    }
    return pack_glb(gltf, bytes(blob))


def _read_accessor_floats(gltf, bin_blob, accessor_idx: int, comps: int):
    acc = gltf["accessors"][accessor_idx]
    bv = gltf["bufferViews"][acc["bufferView"]]
    base = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = bv.get("byteStride") or (4 * comps)
    out = []
    fmt = "<" + ("f" * comps)
    for i in range(acc["count"]):
        off = base + i * stride
        out.append(struct.unpack_from(fmt, bin_blob, off))
    return out


def _read_accessor_u16(gltf, bin_blob, accessor_idx: int, comps: int):
    acc = gltf["accessors"][accessor_idx]
    bv = gltf["bufferViews"][acc["bufferView"]]
    base = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = bv.get("byteStride") or (2 * comps)
    out = []
    fmt = "<" + ("H" * comps)
    for i in range(acc["count"]):
        off = base + i * stride
        out.append(struct.unpack_from(fmt, bin_blob, off))
    return out


@pytest.fixture(scope="module")
def live_server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.MeshGatewayHandler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_rig_biped_creature_valid_gltf_and_animations():
    raw_glb = _make_static_creature_glb(quadruped=False)
    out_bytes, meta = rig_glb_bytes(raw_glb, rig_type="auto", animation="all")

    assert meta["cost_usd"] == 0.0
    assert meta["rig_type"] in ("biped_creature", "humanoid")
    assert meta["bone_count"] >= 8
    assert meta["animations"] == ["TinCan_walk", "TinCan_run", "TinCan_idle", "TinCan_dance"]

    gltf, blob = parse_glb(out_bytes)
    assert len(gltf["skins"]) == 1
    skin = gltf["skins"][0]
    joints = skin["joints"]
    assert len(joints) == meta["bone_count"]

    ibm_vals = _read_accessor_floats(gltf, blob, skin["inverseBindMatrices"], 16)
    assert len(ibm_vals) == len(joints)

    prim = gltf["meshes"][0]["primitives"][0]
    attrs = prim["attributes"]
    assert "JOINTS_0" in attrs and "WEIGHTS_0" in attrs

    j_rows = _read_accessor_u16(gltf, blob, attrs["JOINTS_0"], 4)
    w_rows = _read_accessor_floats(gltf, blob, attrs["WEIGHTS_0"], 4)
    assert len(j_rows) == meta["vertex_count"]
    assert len(w_rows) == meta["vertex_count"]

    for js, ws in zip(j_rows, w_rows):
        for j in js:
            assert 0 <= j < len(joints)
        for w in ws:
            assert w >= -1e-6
        assert abs(sum(ws) - 1.0) < 1e-4

    anims = gltf.get("animations") or []
    assert [a["name"] for a in anims] == ["TinCan_walk", "TinCan_run", "TinCan_idle", "TinCan_dance"]
    for anim in anims:
        assert len(anim["channels"]) >= 4
        for ch in anim["channels"]:
            samp = anim["samplers"][ch["sampler"]]
            times = [t[0] for t in _read_accessor_floats(gltf, blob, samp["input"], 1)]
            assert times == sorted(times)
            assert times[0] == pytest.approx(0.0, abs=1e-5)
            assert times[-1] > 0.5
            path = ch["target"]["path"]
            if path == "rotation":
                quats = _read_accessor_floats(gltf, blob, samp["output"], 4)
                for q in quats:
                    norm = math.sqrt(sum(c * c for c in q))
                    assert norm == pytest.approx(1.0, abs=1e-3)


def test_rig_quadruped_with_rotated_root_node():
    # Rotate quadruped 90 deg around X before baking transform
    q_x90 = (math.sin(math.pi / 4), 0.0, 0.0, math.cos(math.pi / 4))
    raw_glb = _make_static_creature_glb(quadruped=True, node_rotation=q_x90)
    out_bytes, meta = rig_glb_bytes(raw_glb, rig_type="quadruped", animation="walk")

    assert meta["rig_type"] == "quadruped"
    assert meta["animations"] == ["TinCan_walk"]
    gltf, _ = parse_glb(out_bytes)
    assert len(gltf["skins"]) == 1
    assert any(n.get("skin") == 0 for n in gltf["nodes"])


def test_draco_compressed_glb_raises_clear_error():
    raw_glb = _make_static_creature_glb()
    gltf, blob = parse_glb(raw_glb)
    gltf["extensionsRequired"] = ["KHR_draco_mesh_compression"]
    draco_glb = pack_glb(gltf, blob)
    with pytest.raises(ValueError, match="Draco"):
        rig_glb_bytes(draco_glb)


def test_http_api_3d_rig_roundtrip_and_errors(live_server):
    import uuid

    raw_glb = _make_static_creature_glb(quadruped=False)
    owner = f"rig-test-{uuid.uuid4().hex[:8]}"
    src_path = "/models3d/pikachu_test.glb"

    # Seed .space file via /api/space/file
    write_payload = json.dumps({
        "scope": "user",
        "owner_id": owner,
        "path": src_path,
        "content": base64.b64encode(raw_glb).decode("ascii"),
        "is_base64": True,
        "mime_type": "model/gltf-binary",
        "action": "write",
        "updated_by": owner,
    }).encode("utf-8")
    req_w = urllib.request.Request(
        f"{live_server}/api/space/file",
        data=write_payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req_w, timeout=15) as resp_w:
        assert resp_w.status == 200

    # Rig directly from .space path
    rig_payload = json.dumps({
        "scope": "user",
        "owner_id": owner,
        "peer_id": owner,
        "path": src_path,
        "rig_type": "biped_creature",
        "animation": "walk",
    }).encode("utf-8")
    req_r = urllib.request.Request(
        f"{live_server}/api/3d/rig",
        data=rig_payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req_r, timeout=20) as resp_r:
        assert resp_r.status == 200
        res = json.loads(resp_r.read().decode("utf-8"))

    assert res["ok"] is True
    assert res["cost_usd"] == 0.0
    assert res["rig_type"] == "biped_creature"
    assert res["animations"] == ["TinCan_walk"]
    assert res["path"] == "/models3d/pikachu_test_rigged.glb"
    assert res["saved_to_space"]["path"] == "/models3d/pikachu_test_rigged.glb"

    out_glb = base64.b64decode(res["glb_bytes_b64"])
    gltf, _ = parse_glb(out_glb)
    assert len(gltf["skins"]) == 1 and len(gltf["animations"]) == 1

    # Verify missing path returns 404
    bad_req = urllib.request.Request(
        f"{live_server}/api/3d/rig",
        data=json.dumps({"scope": "user", "owner_id": owner, "path": "/models3d/does_not_exist.glb"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(bad_req, timeout=10)
    assert exc_info.value.code == 404


def test_agent_space_rig_action_and_ui_markers():
    with tempfile.TemporaryDirectory() as td:
        vfs = SingleFileSpaceVFS(os.path.join(td, "space.sqlite"))
        raw_glb = _make_static_creature_glb()
        vfs.write_file("/models3d/mouse.glb", raw_glb, mime_type="model/gltf-binary", updated_by="tester")
        harness = AgentSpaceHarness(vfs)

        files_mutated = []
        rodin_assets = []
        tool_calls = []
        cleaned = harness._execute_tincan_action_blocks(
            'Rigging mouse now.\n```tincan_action\n{"action":"rig_3d","path":"/models3d/mouse.glb","rig_type":"biped_creature","animation":"all"}\n```',
            author="tester",
            auto_exec=True,
            files_mutated=files_mutated,
            exec_results=[],
            image_assets=[],
            rodin_assets=rodin_assets,
            tool_calls=tool_calls,
        )
        assert "/models3d/mouse_rigged.glb" in files_mutated
        assert any(tc.get("tool") == "rig_3d" and tc.get("status") == "Done" for tc in tool_calls)
        assert "Auto-rigged 3D mesh" in cleaned

    manifest = build_tincan_capability_manifest()
    assert "tincan-gen rig" in manifest
    assert "/api/3d/rig" in manifest
    assert "def main(" in _TINCAN_GEN_SCRIPT and '"rig"' in _TINCAN_GEN_SCRIPT

    assert "finder3dRigBtn" in MESH_OS_HTML_UI
    assert "rigActiveSpaceGlb" in MESH_OS_HTML_UI
    assert "setAttribute('autoplay'" in MESH_OS_HTML_UI

    ws_html = render_workstation_window_html()
    assert "wsRigGlbBtn" in ws_html
    assert "rigCurrentGlb" in ws_html
