"""Zero-cost pure-Python glTF 2.0 Auto-Rigger & Procedural Animator (`glb_rigger.py`).

Takes any static `.glb` mesh (e.g. from Hyper3D Rodin, Tripo3D, or Hunyuan3D) and:
1. Parses the binary glTF 2.0 container (preserving materials, textures, normals, UVs, indices).
2. Normalizes node transforms into canonical Y-up world space so bones align reliably.
3. Fits an anatomical skeleton (`biped_creature`, `quadruped`, `humanoid`, or `auto`)
   using mesh bounding box + local vertex cluster centroids.
4. Computes smooth segment heat-kernel skin weights (`JOINTS_0`, `WEIGHTS_0`) and exact
   column-major `inverseBindMatrices` (`skins`).
5. Synthesizes seamless keyframe animation clips (`walk`, `run`, `idle`, `dance`, or `all`).
6. Outputs a standards-compliant rigged `.glb` playable natively in Three.js
   `AnimationMixer`, `<model-viewer autoplay>`, Blender, Godot, and Unity.
"""

from __future__ import annotations

import json
import math
import struct
from typing import Any, Dict, List, Optional, Sequence, Tuple

GLB_MAGIC = b"glTF"
GLB_VERSION = 2
CHUNK_JSON = 0x4E4F534A
CHUNK_BIN = 0x004E4942

_COMP_SIZE = {
    5120: 1,  # BYTE
    5121: 1,  # UNSIGNED_BYTE
    5122: 2,  # SHORT
    5123: 2,  # UNSIGNED_SHORT
    5125: 4,  # UNSIGNED_INT
    5126: 4,  # FLOAT
}
_TYPE_COUNT = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT2": 4,
    "MAT3": 9,
    "MAT4": 16,
}

Vec3 = Tuple[float, float, float]
Quat = Tuple[float, float, float, float]  # (x, y, z, w)
Mat4 = List[float]  # 16 floats column-major


def _mat4_identity() -> Mat4:
    return [
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]


def _mat4_mul(a: Sequence[float], b: Sequence[float]) -> Mat4:
    """Multiply two column-major 4x4 matrices: A * B."""
    out = [0.0] * 16
    for col in range(4):
        for row in range(4):
            out[col * 4 + row] = sum(a[k * 4 + row] * b[col * 4 + k] for k in range(4))
    return out


def _mat4_from_trs(t: Sequence[float], q: Sequence[float], s: Sequence[float]) -> Mat4:
    tx, ty, tz = float(t[0]), float(t[1]), float(t[2])
    qx, qy, qz, qw = float(q[0]), float(q[1]), float(q[2]), float(q[3])
    sx, sy, sz = float(s[0]), float(s[1]), float(s[2])
    xx, yy, zz = qx * qx, qy * qy, qz * qz
    xy, xz, yz = qx * qy, qx * qz, qy * qz
    wx, wy, wz = qw * qx, qw * qy, qw * qz
    return [
        (1.0 - 2.0 * (yy + zz)) * sx, (2.0 * (xy + wz)) * sx, (2.0 * (xz - wy)) * sx, 0.0,
        (2.0 * (xy - wz)) * sy, (1.0 - 2.0 * (xx + zz)) * sy, (2.0 * (yz + wx)) * sy, 0.0,
        (2.0 * (xz + wy)) * sz, (2.0 * (yz - wx)) * sz, (1.0 - 2.0 * (xx + yy)) * sz, 0.0,
        tx, ty, tz, 1.0,
    ]


def _mat4_transform_point(m: Sequence[float], p: Vec3) -> Vec3:
    x, y, z = p
    return (
        m[0] * x + m[4] * y + m[8] * z + m[12],
        m[1] * x + m[5] * y + m[9] * z + m[13],
        m[2] * x + m[6] * y + m[10] * z + m[14],
    )


def _mat4_transform_dir(m: Sequence[float], n: Vec3) -> Vec3:
    x, y, z = n
    nx = m[0] * x + m[4] * y + m[8] * z
    ny = m[1] * x + m[5] * y + m[9] * z
    nz = m[2] * x + m[6] * y + m[10] * z
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    if length < 1e-12:
        return (0.0, 1.0, 0.0)
    return (nx / length, ny / length, nz / length)


def _euler_xyz_to_quat(rx: float, ry: float, rz: float) -> Quat:
    """Convert Euler angles (radians, XYZ order) into unit glTF quaternion (x, y, z, w)."""
    cx, sx = math.cos(rx * 0.5), math.sin(rx * 0.5)
    cy, sy = math.cos(ry * 0.5), math.sin(ry * 0.5)
    cz, sz = math.cos(rz * 0.5), math.sin(rz * 0.5)
    x = sx * cy * cz + cx * sy * sz
    y = cx * sy * cz - sx * cy * sz
    z = cx * cy * sz + sx * sy * cz
    w = cx * cy * cz - sx * sy * sz
    norm = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    return (x / norm, y / norm, z / norm, w / norm)


def parse_glb(glb_bytes: bytes) -> Tuple[Dict[str, Any], bytearray]:
    """Parse binary glTF 2.0 bytes into (json_dict, mutable_bin_bytearray)."""
    if len(glb_bytes) < 20 or glb_bytes[:4] != GLB_MAGIC:
        raise ValueError("Invalid GLB file: missing 'glTF' binary header.")
    version, total_len = struct.unpack_from("<II", glb_bytes, 4)
    if version != GLB_VERSION:
        raise ValueError(f"Unsupported glTF version {version}; expected 2.")

    offset = 12
    gltf_json: Optional[Dict[str, Any]] = None
    bin_chunk = bytearray()
    limit = min(len(glb_bytes), total_len)

    while offset + 8 <= limit:
        chunk_len, chunk_type = struct.unpack_from("<II", glb_bytes, offset)
        offset += 8
        chunk_data = glb_bytes[offset : offset + chunk_len]
        offset += chunk_len
        if chunk_type == CHUNK_JSON:
            gltf_json = json.loads(chunk_data.decode("utf-8").rstrip("\x00 "))
        elif chunk_type == CHUNK_BIN:
            bin_chunk = bytearray(chunk_data)

    if gltf_json is None:
        raise ValueError("Invalid GLB file: missing JSON chunk.")
    return gltf_json, bin_chunk


def pack_glb(gltf_json: Dict[str, Any], bin_chunk: bytes) -> bytes:
    """Serialize glTF JSON + BIN chunk into an aligned 4-byte-padded binary .glb."""
    while len(bin_chunk) % 4 != 0:
        bin_chunk = bytes(bin_chunk) + b"\x00"

    if gltf_json.get("buffers"):
        gltf_json["buffers"][0]["byteLength"] = len(bin_chunk)
        gltf_json["buffers"][0].pop("uri", None)
    else:
        gltf_json["buffers"] = [{"byteLength": len(bin_chunk)}]

    json_bytes = json.dumps(gltf_json, separators=(",", ":")).encode("utf-8")
    while len(json_bytes) % 4 != 0:
        json_bytes += b" "

    total_len = 12 + 8 + len(json_bytes) + (8 + len(bin_chunk) if bin_chunk else 0)
    header = GLB_MAGIC + struct.pack("<II", GLB_VERSION, total_len)
    j_chunk = struct.pack("<II", len(json_bytes), CHUNK_JSON) + json_bytes
    if bin_chunk:
        b_chunk = struct.pack("<II", len(bin_chunk), CHUNK_BIN) + bin_chunk
        return header + j_chunk + b_chunk
    return header + j_chunk


def _read_vec3_f32(gltf: Dict[str, Any], bin_data: bytearray, acc_idx: int) -> List[Vec3]:
    acc = gltf["accessors"][acc_idx]
    bv = gltf["bufferViews"][acc["bufferView"]]
    comp_type = int(acc["componentType"])
    if comp_type != 5126 or acc.get("type") != "VEC3":
        raise ValueError(f"Expected VEC3 float32 accessor, got {acc.get('type')} / {comp_type}.")
    count = int(acc["count"])
    stride = int(bv.get("byteStride") or 12)
    base = int(bv.get("byteOffset", 0)) + int(acc.get("byteOffset", 0))
    pts: List[Vec3] = []
    for i in range(count):
        pts.append(struct.unpack_from("<fff", bin_data, base + i * stride))
    return pts


def _write_vec3_f32(gltf: Dict[str, Any], bin_data: bytearray, acc_idx: int, pts: List[Vec3]) -> None:
    acc = gltf["accessors"][acc_idx]
    bv = gltf["bufferViews"][acc["bufferView"]]
    stride = int(bv.get("byteStride") or 12)
    base = int(bv.get("byteOffset", 0)) + int(acc.get("byteOffset", 0))
    min_v = [float("inf"), float("inf"), float("inf")]
    max_v = [float("-inf"), float("-inf"), float("-inf")]
    for i, (x, y, z) in enumerate(pts):
        struct.pack_into("<fff", bin_data, base + i * stride, x, y, z)
        if x < min_v[0]: min_v[0] = x
        if y < min_v[1]: min_v[1] = y
        if z < min_v[2]: min_v[2] = z
        if x > max_v[0]: max_v[0] = x
        if y > max_v[1]: max_v[1] = y
        if z > max_v[2]: max_v[2] = z
    if pts:
        acc["min"] = [round(v, 6) for v in min_v]
        acc["max"] = [round(v, 6) for v in max_v]


def _append_buffer_view(gltf: Dict[str, Any], bin_data: bytearray, raw: bytes, target: Optional[int] = None) -> int:
    while len(bin_data) % 4 != 0:
        bin_data.append(0)
    offset = len(bin_data)
    bin_data.extend(raw)
    while len(bin_data) % 4 != 0:
        bin_data.append(0)
    bv: Dict[str, Any] = {"buffer": 0, "byteOffset": offset, "byteLength": len(raw)}
    if target is not None:
        bv["target"] = target
    views = gltf.setdefault("bufferViews", [])
    views.append(bv)
    return len(views) - 1


def _append_accessor(
    gltf: Dict[str, Any],
    bv_idx: int,
    component_type: int,
    acc_type: str,
    count: int,
    *,
    min_vals: Optional[List[float]] = None,
    max_vals: Optional[List[float]] = None,
) -> int:
    acc: Dict[str, Any] = {
        "bufferView": bv_idx,
        "componentType": component_type,
        "count": count,
        "type": acc_type,
    }
    if min_vals is not None:
        acc["min"] = min_vals
    if max_vals is not None:
        acc["max"] = max_vals
    accessors = gltf.setdefault("accessors", [])
    accessors.append(acc)
    return len(accessors) - 1


def _node_local_matrix(node: Dict[str, Any]) -> Mat4:
    if "matrix" in node:
        return [float(v) for v in node["matrix"]]
    t = node.get("translation", [0.0, 0.0, 0.0])
    r = node.get("rotation", [0.0, 0.0, 0.0, 1.0])
    s = node.get("scale", [1.0, 1.0, 1.0])
    return _mat4_from_trs(t, r, s)


def _compute_world_matrices(gltf: Dict[str, Any]) -> Dict[int, Mat4]:
    nodes = gltf.get("nodes") or []
    scenes = gltf.get("scenes") or []
    scene_idx = int(gltf.get("scene", 0)) if scenes else -1
    roots = list(scenes[scene_idx].get("nodes") or []) if 0 <= scene_idx < len(scenes) else []
    if not roots and nodes:
        children_set = {c for n in nodes for c in (n.get("children") or [])}
        roots = [i for i in range(len(nodes)) if i not in children_set]

    world: Dict[int, Mat4] = {}

    def _walk(idx: int, parent_m: Mat4) -> None:
        if idx < 0 or idx >= len(nodes):
            return
        local_m = _node_local_matrix(nodes[idx])
        m = _mat4_mul(parent_m, local_m)
        world[idx] = m
        for ch in nodes[idx].get("children") or []:
            _walk(int(ch), m)

    ident = _mat4_identity()
    for r in roots:
        _walk(int(r), ident)
    return world


def _dist_point_to_segment(p: Vec3, a: Vec3, b: Vec3) -> float:
    px, py, pz = p
    ax, ay, az = a
    bx, by, bz = b
    abx, aby, abz = bx - ax, by - ay, bz - az
    ab_len2 = abx * abx + aby * aby + abz * abz
    if ab_len2 < 1e-12:
        dx, dy, dz = px - ax, py - ay, pz - az
        return math.sqrt(dx * dx + dy * dy + dz * dz)
    t = ((px - ax) * abx + (py - ay) * aby + (pz - az) * abz) / ab_len2
    if t < 0.0:
        t = 0.0
    elif t > 1.0:
        t = 1.0
    cx, cy, cz = ax + t * abx, ay + t * aby, az + t * abz
    dx, dy, dz = px - cx, py - cy, pz - cz
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def _detect_rig_type(pts: List[Vec3]) -> str:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    zs = [p[2] for p in pts]
    w = max(xs) - min(xs)
    h = max(ys) - min(ys)
    d = max(zs) - min(zs)
    if d > w * 1.18 and h < d * 1.18:
        return "quadruped"
    if h >= max(w, d) * 1.32:
        return "humanoid"
    return "biped_creature"


def _region_centroid(
    pts: List[Vec3],
    bounds: Tuple[Vec3, Vec3],
    rx: Tuple[float, float],
    ry: Tuple[float, float],
    rz: Tuple[float, float],
    fallback: Tuple[float, float, float],
) -> Vec3:
    bmin, bmax = bounds
    w = max(bmax[0] - bmin[0], 1e-4)
    h = max(bmax[1] - bmin[1], 1e-4)
    d = max(bmax[2] - bmin[2], 1e-4)

    sx = sy = sz = 0.0
    cnt = 0
    step = max(1, len(pts) // 8000)
    for p in pts[::step]:
        nx = (p[0] - bmin[0]) / w
        ny = (p[1] - bmin[1]) / h
        nz = (p[2] - bmin[2]) / d
        if rx[0] <= nx <= rx[1] and ry[0] <= ny <= ry[1] and rz[0] <= nz <= rz[1]:
            sx += p[0]
            sy += p[1]
            sz += p[2]
            cnt += 1

    if cnt >= 3:
        return (sx / cnt, sy / cnt, sz / cnt)
    return (
        bmin[0] + fallback[0] * w,
        bmin[1] + fallback[1] * h,
        bmin[2] + fallback[2] * d,
    )


def _build_skeleton_spec(rig_type: str, pts: List[Vec3]) -> List[Dict[str, Any]]:
    """Build bone list: {name, parent_idx, pos, tip, sigma, side} in Y-up world coords."""
    bmin = (min(p[0] for p in pts), min(p[1] for p in pts), min(p[2] for p in pts))
    bmax = (max(p[0] for p in pts), max(p[1] for p in pts), max(p[2] for p in pts))
    bounds = (bmin, bmax)
    diag = math.sqrt(sum((bmax[i] - bmin[i]) ** 2 for i in range(3))) or 1.0

    def c(rx: Tuple[float, float], ry: Tuple[float, float], rz: Tuple[float, float], fb: Tuple[float, float, float]) -> Vec3:
        return _region_centroid(pts, bounds, rx, ry, rz, fb)

    def pt_frac(fx: float, fy: float, fz: float) -> Vec3:
        return (
            bmin[0] + fx * max(bmax[0] - bmin[0], 1e-4),
            bmin[1] + fy * max(bmax[1] - bmin[1], 1e-4),
            bmin[2] + fz * max(bmax[2] - bmin[2], 1e-4),
        )

    if rig_type == "quadruped":
        pelvis = c((0.35, 0.65), (0.35, 0.70), (0.12, 0.42), (0.50, 0.50, 0.28))
        spine = c((0.35, 0.65), (0.40, 0.75), (0.38, 0.62), (0.50, 0.54, 0.50))
        chest = c((0.35, 0.65), (0.42, 0.78), (0.58, 0.80), (0.50, 0.56, 0.70))
        neck = c((0.38, 0.62), (0.55, 0.82), (0.68, 0.88), (0.50, 0.68, 0.78))
        head = c((0.35, 0.65), (0.62, 0.96), (0.72, 1.00), (0.50, 0.78, 0.88))
        head_tip = pt_frac(0.50, 0.86, 0.96)
        tail_base = c((0.38, 0.62), (0.38, 0.72), (0.00, 0.24), (0.50, 0.52, 0.16))
        tail_tip = pt_frac(0.50, 0.60, 0.02)

        fl_hip = c((0.55, 0.90), (0.28, 0.55), (0.55, 0.82), (0.66, 0.42, 0.68))
        fl_foot = c((0.55, 0.95), (0.00, 0.22), (0.52, 0.85), (0.66, 0.04, 0.70))
        fr_hip = c((0.10, 0.45), (0.28, 0.55), (0.55, 0.82), (0.34, 0.42, 0.68))
        fr_foot = c((0.05, 0.45), (0.00, 0.22), (0.52, 0.85), (0.34, 0.04, 0.70))
        bl_hip = c((0.55, 0.90), (0.28, 0.55), (0.16, 0.44), (0.66, 0.42, 0.30))
        bl_foot = c((0.55, 0.95), (0.00, 0.22), (0.12, 0.46), (0.66, 0.04, 0.28))
        br_hip = c((0.10, 0.45), (0.28, 0.55), (0.16, 0.44), (0.34, 0.42, 0.30))
        br_foot = c((0.05, 0.45), (0.00, 0.22), (0.12, 0.46), (0.34, 0.04, 0.28))

        s_leg = diag * 0.14
        s_body = diag * 0.20
        return [
            {"name": "Pelvis", "parent": None, "pos": pelvis, "tip": spine, "sigma": s_body, "side": 0},
            {"name": "Spine", "parent": 0, "pos": spine, "tip": chest, "sigma": s_body, "side": 0},
            {"name": "Chest", "parent": 1, "pos": chest, "tip": neck, "sigma": s_body, "side": 0},
            {"name": "Neck", "parent": 2, "pos": neck, "tip": head, "sigma": s_body * 0.75, "side": 0},
            {"name": "Head", "parent": 3, "pos": head, "tip": head_tip, "sigma": s_body * 0.85, "side": 0},
            {"name": "Tail", "parent": 0, "pos": tail_base, "tip": tail_tip, "sigma": diag * 0.11, "side": 0},
            {"name": "FrontLeftLeg", "parent": 2, "pos": fl_hip, "tip": fl_foot, "sigma": s_leg, "side": 1},
            {"name": "FrontRightLeg", "parent": 2, "pos": fr_hip, "tip": fr_foot, "sigma": s_leg, "side": -1},
            {"name": "BackLeftLeg", "parent": 0, "pos": bl_hip, "tip": bl_foot, "sigma": s_leg, "side": 1},
            {"name": "BackRightLeg", "parent": 0, "pos": br_hip, "tip": br_foot, "sigma": s_leg, "side": -1},
        ]

    if rig_type == "humanoid":
        pelvis = pt_frac(0.50, 0.48, 0.50)
        spine = pt_frac(0.50, 0.58, 0.50)
        chest = pt_frac(0.50, 0.70, 0.50)
        neck = pt_frac(0.50, 0.80, 0.50)
        head = pt_frac(0.50, 0.88, 0.50)
        head_tip = pt_frac(0.50, 0.98, 0.50)

        l_sh = c((0.58, 0.78), (0.66, 0.80), (0.35, 0.65), (0.64, 0.74, 0.50))
        l_el = c((0.68, 0.88), (0.50, 0.72), (0.30, 0.70), (0.76, 0.62, 0.50))
        l_ha = c((0.76, 1.00), (0.35, 0.65), (0.25, 0.75), (0.88, 0.50, 0.50))

        r_sh = c((0.22, 0.42), (0.66, 0.80), (0.35, 0.65), (0.36, 0.74, 0.50))
        r_el = c((0.12, 0.32), (0.50, 0.72), (0.30, 0.70), (0.24, 0.62, 0.50))
        r_ha = c((0.00, 0.24), (0.35, 0.65), (0.25, 0.75), (0.12, 0.50, 0.50))

        l_hip = c((0.52, 0.70), (0.40, 0.52), (0.35, 0.65), (0.58, 0.45, 0.50))
        l_kn = c((0.52, 0.72), (0.20, 0.34), (0.35, 0.65), (0.58, 0.25, 0.52))
        l_fo = c((0.52, 0.74), (0.00, 0.12), (0.35, 0.75), (0.58, 0.04, 0.56))

        r_hip = c((0.30, 0.48), (0.40, 0.52), (0.35, 0.65), (0.42, 0.45, 0.50))
        r_kn = c((0.28, 0.48), (0.20, 0.34), (0.35, 0.65), (0.42, 0.25, 0.52))
        r_fo = c((0.26, 0.48), (0.00, 0.12), (0.35, 0.75), (0.42, 0.04, 0.56))

        s_limb = diag * 0.11
        s_core = diag * 0.16
        return [
            {"name": "Pelvis", "parent": None, "pos": pelvis, "tip": spine, "sigma": s_core, "side": 0},
            {"name": "Spine", "parent": 0, "pos": spine, "tip": chest, "sigma": s_core, "side": 0},
            {"name": "Chest", "parent": 1, "pos": chest, "tip": neck, "sigma": s_core, "side": 0},
            {"name": "Neck", "parent": 2, "pos": neck, "tip": head, "sigma": s_core * 0.65, "side": 0},
            {"name": "Head", "parent": 3, "pos": head, "tip": head_tip, "sigma": s_core * 0.85, "side": 0},
            {"name": "LeftUpperArm", "parent": 2, "pos": l_sh, "tip": l_el, "sigma": s_limb, "side": 1},
            {"name": "LeftForearm", "parent": 5, "pos": l_el, "tip": l_ha, "sigma": s_limb, "side": 1},
            {"name": "RightUpperArm", "parent": 2, "pos": r_sh, "tip": r_el, "sigma": s_limb, "side": -1},
            {"name": "RightForearm", "parent": 7, "pos": r_el, "tip": r_ha, "sigma": s_limb, "side": -1},
            {"name": "LeftThigh", "parent": 0, "pos": l_hip, "tip": l_kn, "sigma": s_limb * 1.15, "side": 1},
            {"name": "LeftShin", "parent": 9, "pos": l_kn, "tip": l_fo, "sigma": s_limb, "side": 1},
            {"name": "RightThigh", "parent": 0, "pos": r_hip, "tip": r_kn, "sigma": s_limb * 1.15, "side": -1},
            {"name": "RightShin", "parent": 11, "pos": r_kn, "tip": r_fo, "sigma": s_limb, "side": -1},
        ]

    # Default: "biped_creature" (Pikachu / duck / mascot / stylized creature)
    pelvis = pt_frac(0.50, 0.34, 0.50)
    spine = pt_frac(0.50, 0.48, 0.50)
    chest = pt_frac(0.50, 0.60, 0.50)
    head = c((0.35, 0.65), (0.64, 0.86), (0.35, 0.72), (0.50, 0.74, 0.50))
    head_tip = pt_frac(0.50, 0.90, 0.52)

    l_ear = c((0.55, 0.92), (0.80, 1.00), (0.30, 0.65), (0.66, 0.88, 0.48))
    l_ear_tip = pt_frac(0.76, 0.98, 0.44)
    r_ear = c((0.08, 0.45), (0.80, 1.00), (0.30, 0.65), (0.34, 0.88, 0.48))
    r_ear_tip = pt_frac(0.24, 0.98, 0.44)

    l_arm = c((0.58, 0.85), (0.42, 0.66), (0.38, 0.72), (0.66, 0.54, 0.54))
    l_arm_tip = c((0.72, 1.00), (0.32, 0.62), (0.40, 0.80), (0.82, 0.44, 0.58))
    r_arm = c((0.15, 0.42), (0.42, 0.66), (0.38, 0.72), (0.34, 0.54, 0.54))
    r_arm_tip = c((0.00, 0.28), (0.32, 0.62), (0.40, 0.80), (0.18, 0.44, 0.58))

    l_leg = c((0.54, 0.80), (0.20, 0.36), (0.32, 0.68), (0.62, 0.28, 0.50))
    l_foot = c((0.54, 0.86), (0.00, 0.14), (0.34, 0.78), (0.62, 0.04, 0.56))
    r_leg = c((0.20, 0.46), (0.20, 0.36), (0.32, 0.68), (0.38, 0.28, 0.50))
    r_foot = c((0.14, 0.46), (0.00, 0.14), (0.34, 0.78), (0.38, 0.04, 0.56))

    tail = c((0.38, 0.65), (0.20, 0.52), (0.02, 0.28), (0.50, 0.34, 0.20))
    tail_tip = pt_frac(0.50, 0.56, 0.02)

    s_core = diag * 0.18
    s_limb = diag * 0.12
    return [
        {"name": "Pelvis", "parent": None, "pos": pelvis, "tip": spine, "sigma": s_core, "side": 0},
        {"name": "Spine", "parent": 0, "pos": spine, "tip": chest, "sigma": s_core, "side": 0},
        {"name": "Chest", "parent": 1, "pos": chest, "tip": head, "sigma": s_core, "side": 0},
        {"name": "Head", "parent": 2, "pos": head, "tip": head_tip, "sigma": s_core * 0.90, "side": 0},
        {"name": "LeftEar", "parent": 3, "pos": l_ear, "tip": l_ear_tip, "sigma": s_limb * 0.85, "side": 1},
        {"name": "RightEar", "parent": 3, "pos": r_ear, "tip": r_ear_tip, "sigma": s_limb * 0.85, "side": -1},
        {"name": "LeftArm", "parent": 2, "pos": l_arm, "tip": l_arm_tip, "sigma": s_limb, "side": 1},
        {"name": "RightArm", "parent": 2, "pos": r_arm, "tip": r_arm_tip, "sigma": s_limb, "side": -1},
        {"name": "LeftLeg", "parent": 0, "pos": l_leg, "tip": l_foot, "sigma": s_limb * 1.1, "side": 1},
        {"name": "RightLeg", "parent": 0, "pos": r_leg, "tip": r_foot, "sigma": s_limb * 1.1, "side": -1},
        {"name": "Tail", "parent": 0, "pos": tail, "tip": tail_tip, "sigma": s_limb * 1.05, "side": 0},
    ]


def _skin_vertices(pts: List[Vec3], bones: List[Dict[str, Any]], mid_x: float) -> Tuple[bytes, bytes]:
    """Compute top-4 bone weights per vertex with lateral side separation."""
    j_buf = bytearray(len(pts) * 8)
    w_buf = bytearray(len(pts) * 16)
    num_bones = len(bones)

    for vi, p in enumerate(pts):
        px = p[0]
        scored: List[Tuple[float, int]] = []
        for bi, b in enumerate(bones):
            d = _dist_point_to_segment(p, b["pos"], b["tip"])
            sigma = max(b["sigma"], 1e-4)
            # Soft lateral guard so Left limbs don't steal Right limb vertices
            side = b["side"]
            penalty = 1.0
            if side == 1 and px < mid_x - sigma * 0.15:
                penalty = 0.08
            elif side == -1 and px > mid_x + sigma * 0.15:
                penalty = 0.08
            score = math.exp(-(d * d) / (2.0 * sigma * sigma)) * penalty
            scored.append((score, bi))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        top4 = scored[:4]
        while len(top4) < 4:
            top4.append((0.0, min(0, num_bones - 1)))

        w_sum = sum(s for s, _ in top4)
        if w_sum <= 1e-12:
            weights = [1.0, 0.0, 0.0, 0.0]
            joints = [0, 0, 0, 0]
        else:
            weights = [s / w_sum for s, _ in top4]
            joints = [bi for _, bi in top4]

        struct.pack_into("<4H", j_buf, vi * 8, *joints)
        struct.pack_into("<4f", w_buf, vi * 16, *weights)

    return bytes(j_buf), bytes(w_buf)


def _anim_pose_for_bone(clip_name: str, bone_name: str, phase: float, pelvis_pos: Vec3, scale_h: float) -> Tuple[Optional[Quat], Optional[Vec3]]:
    """Return procedural (rotation_quat, translation_vec3) for bone at normalized loop phase in [0, 2*pi]."""
    s1 = math.sin(phase)
    c1 = math.cos(phase)
    s2 = math.sin(2.0 * phase)
    c2 = math.cos(2.0 * phase)
    bn = bone_name.lower()

    if clip_name == "idle":
        if bn == "pelvis":
            return (
                _euler_xyz_to_quat(0.0, 0.02 * s1, 0.015 * c1),
                (pelvis_pos[0], pelvis_pos[1] + 0.010 * scale_h * s1, pelvis_pos[2]),
            )
        if bn in ("spine", "chest"):
            return (_euler_xyz_to_quat(0.03 * s1, 0.02 * c1, 0.0), None)
        if bn == "head":
            return (_euler_xyz_to_quat(0.04 * s1, 0.08 * math.sin(phase * 0.5), 0.02 * c1), None)
        if "ear" in bn:
            sign = 1.0 if "left" in bn else -1.0
            return (_euler_xyz_to_quat(0.05 * s1, 0.0, sign * 0.08 * s2), None)
        if "arm" in bn or "forearm" in bn:
            sign = 1.0 if "left" in bn else -1.0
            return (_euler_xyz_to_quat(0.04 * s1, 0.0, sign * 0.04 * c1), None)
        if bn == "tail":
            return (_euler_xyz_to_quat(0.08 * c1, 0.24 * s1, 0.0), None)
        return (None, None)

    if clip_name == "dance":
        if bn == "pelvis":
            return (
                _euler_xyz_to_quat(0.04 * s2, 0.22 * s1, 0.08 * s1),
                (pelvis_pos[0], pelvis_pos[1] + 0.045 * scale_h * abs(s2), pelvis_pos[2]),
            )
        if bn == "chest":
            return (_euler_xyz_to_quat(0.06 * c2, -0.18 * s1, -0.06 * s1), None)
        if bn == "head":
            return (_euler_xyz_to_quat(-0.08 * s2, 0.14 * s1, 0.10 * c1), None)
        if "ear" in bn:
            sign = 1.0 if "left" in bn else -1.0
            return (_euler_xyz_to_quat(0.18 * s2, 0.0, sign * 0.22 * c2), None)
        if "arm" in bn:
            sign = 1.0 if "left" in bn else -1.0
            return (_euler_xyz_to_quat(-0.35 * sign * s1, 0.0, sign * (0.45 + 0.35 * s1)), None)
        if "leg" in bn or "thigh" in bn or "shin" in bn:
            sign = 1.0 if "left" in bn else -1.0
            return (_euler_xyz_to_quat(0.22 * sign * s1, 0.0, 0.0), None)
        if bn == "tail":
            return (_euler_xyz_to_quat(0.18 * s2, 0.45 * s1, 0.0), None)
        return (None, None)

    # Walk & Run gaits
    amp = 1.45 if clip_name == "run" else 1.0
    bob = (0.042 if clip_name == "run" else 0.025) * scale_h
    lean = 0.16 if clip_name == "run" else 0.05

    if bn == "pelvis":
        return (
            _euler_xyz_to_quat(lean * 0.4, 0.09 * amp * s1, 0.05 * amp * c1),
            (pelvis_pos[0], pelvis_pos[1] + bob * (0.5 - 0.5 * c2), pelvis_pos[2]),
        )
    if bn == "spine":
        return (_euler_xyz_to_quat(lean * 0.35, -0.06 * amp * s1, -0.03 * amp * c1), None)
    if bn == "chest":
        return (_euler_xyz_to_quat(lean * 0.25, -0.08 * amp * s1, 0.0), None)
    if bn == "head":
        return (_euler_xyz_to_quat(-lean * 0.5 + 0.05 * amp * s2, 0.05 * s1, -0.03 * c1), None)
    if "ear" in bn:
        sign = 1.0 if "left" in bn else -1.0
        return (_euler_xyz_to_quat(0.14 * amp * s2, 0.0, sign * 0.10 * s2), None)
    if bn == "tail":
        return (_euler_xyz_to_quat(0.12 * s2, 0.34 * amp * s1, 0.0), None)

    # Quadruped diagonal trot vs Biped alternating stride
    if "frontleft" in bn or "backright" in bn:
        return (_euler_xyz_to_quat(0.42 * amp * s1, 0.0, 0.0), None)
    if "frontright" in bn or "backleft" in bn:
        return (_euler_xyz_to_quat(-0.42 * amp * s1, 0.0, 0.0), None)

    if "leftthigh" in bn or bn == "leftleg":
        return (_euler_xyz_to_quat(0.46 * amp * s1, 0.0, 0.0), None)
    if "rightthigh" in bn or bn == "rightleg":
        return (_euler_xyz_to_quat(-0.46 * amp * s1, 0.0, 0.0), None)
    if "leftshin" in bn:
        return (_euler_xyz_to_quat(0.42 * amp * max(0.0, -c1), 0.0, 0.0), None)
    if "rightshin" in bn:
        return (_euler_xyz_to_quat(0.42 * amp * max(0.0, c1), 0.0, 0.0), None)

    if "leftupperarm" in bn or bn == "leftarm":
        return (_euler_xyz_to_quat(-0.36 * amp * s1, 0.0, 0.08), None)
    if "rightupperarm" in bn or bn == "rightarm":
        return (_euler_xyz_to_quat(0.36 * amp * s1, 0.0, -0.08), None)
    if "leftforearm" in bn:
        return (_euler_xyz_to_quat(-0.22 * amp * (0.5 + 0.5 * s1), 0.0, 0.0), None)
    if "rightforearm" in bn:
        return (_euler_xyz_to_quat(-0.22 * amp * (0.5 - 0.5 * s1), 0.0, 0.0), None)

    return (None, None)


def rig_glb_bytes(
    glb_bytes: bytes,
    *,
    rig_type: str = "auto",
    animation: str = "walk",
) -> Tuple[bytes, Dict[str, Any]]:
    """Auto-rig any static binary `.glb` and embed procedural glTF 2.0 skeleton + animation clips.

    Returns ``(rigged_glb_bytes, metadata_dict)``.
    """
    gltf, bin_data = parse_glb(glb_bytes)
    meshes = gltf.get("meshes") or []
    if not meshes:
        raise ValueError("GLB contains no meshes to rig.")

    # Resolve world matrices per node and gather all mesh primitives referenced in scenes
    world_mats = _compute_world_matrices(gltf)
    nodes = gltf.get("nodes") or []

    primitive_records: List[Tuple[int, Dict[str, Any], Mat4]] = []
    seen_mesh_accessors: Dict[int, Mat4] = {}

    for node_idx, node in enumerate(nodes):
        if "mesh" not in node:
            continue
        mesh_idx = int(node["mesh"])
        m_world = world_mats.get(node_idx, _mat4_identity())
        for prim in meshes[mesh_idx].get("primitives") or []:
            ext = (prim.get("extensions") or {})
            if "KHR_draco_mesh_compression" in ext or "KHR_draco_mesh_compression" in (gltf.get("extensionsRequired") or []):
                raise ValueError("Draco-compressed GLB primitives must be decoded before auto-rigging.")
            attrs = prim.get("attributes") or {}
            if "POSITION" not in attrs:
                continue
            pos_idx = int(attrs["POSITION"])
            primitive_records.append((mesh_idx, prim, m_world))
            if pos_idx not in seen_mesh_accessors:
                seen_mesh_accessors[pos_idx] = m_world

        # Reset node transform to Identity since we bake M_world directly into vertex positions
        for tr_key in ("translation", "rotation", "scale", "matrix"):
            node.pop(tr_key, None)

    if not primitive_records:
        raise ValueError("GLB has no vertex POSITION attributes to rig.")

    # Bake node world transforms into POSITION / NORMAL so M_mesh == Identity cleanly
    all_points: List[Vec3] = []
    prim_pts_cache: Dict[int, List[Vec3]] = {}
    transformed_norm_acc = set()

    for _, prim, m_world in primitive_records:
        attrs = prim["attributes"]
        pos_idx = int(attrs["POSITION"])
        if pos_idx not in prim_pts_cache:
            raw_pts = _read_vec3_f32(gltf, bin_data, pos_idx)
            w_pts = [_mat4_transform_point(m_world, p) for p in raw_pts]
            _write_vec3_f32(gltf, bin_data, pos_idx, w_pts)
            prim_pts_cache[pos_idx] = w_pts
            all_points.extend(w_pts)

        if "NORMAL" in attrs:
            n_idx = int(attrs["NORMAL"])
            if n_idx not in transformed_norm_acc:
                transformed_norm_acc.add(n_idx)
                n_acc = gltf["accessors"][n_idx]
                if int(n_acc["componentType"]) == 5126 and n_acc.get("type") == "VEC3":
                    raw_n = _read_vec3_f32(gltf, bin_data, n_idx)
                    w_n = [_mat4_transform_dir(m_world, n) for n in raw_n]
                    _write_vec3_f32(gltf, bin_data, n_idx, w_n)

    if not all_points:
        raise ValueError("GLB contains zero vertices.")

    # Detect / build skeleton
    req_rig = (rig_type or "auto").strip().lower()
    chosen_rig = _detect_rig_type(all_points) if req_rig in ("auto", "") else req_rig
    if chosen_rig not in ("biped_creature", "quadruped", "humanoid"):
        chosen_rig = _detect_rig_type(all_points)

    bones = _build_skeleton_spec(chosen_rig, all_points)
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    mid_x = 0.5 * (min(xs) + max(xs))
    scale_h = max(max(ys) - min(ys), 1e-4)

    # Append JOINTS_0 & WEIGHTS_0 for each unique POSITION accessor / primitive
    skin_cache: Dict[int, Tuple[int, int]] = {}
    for _, prim, _ in primitive_records:
        pos_idx = int(prim["attributes"]["POSITION"])
        if pos_idx not in skin_cache:
            pts = prim_pts_cache[pos_idx]
            j_bytes, w_bytes = _skin_vertices(pts, bones, mid_x=mid_x)
            j_bv = _append_buffer_view(gltf, bin_data, j_bytes, target=34962)
            w_bv = _append_buffer_view(gltf, bin_data, w_bytes, target=34962)
            j_acc = _append_accessor(gltf, j_bv, 5123, "VEC4", len(pts))
            w_acc = _append_accessor(gltf, w_bv, 5126, "VEC4", len(pts))
            skin_cache[pos_idx] = (j_acc, w_acc)
        j_acc, w_acc = skin_cache[pos_idx]
        prim["attributes"]["JOINTS_0"] = j_acc
        prim["attributes"]["WEIGHTS_0"] = w_acc

    # Append skeleton joint nodes into gltf["nodes"] + active scene
    joint_node_indices: List[int] = []
    base_node_idx = len(nodes)
    for bi in range(len(bones)):
        joint_node_indices.append(base_node_idx + bi)

    for bi, b in enumerate(bones):
        jx, jy, jz = b["pos"]
        p_idx = b["parent"]
        if p_idx is None:
            rel_pos = [jx, jy, jz]
        else:
            px, py, pz = bones[p_idx]["pos"]
            rel_pos = [jx - px, jy - py, jz - pz]
        j_node: Dict[str, Any] = {
            "name": f"TinCan_{b['name']}",
            "translation": [round(float(v), 6) for v in rel_pos],
            "rotation": [0.0, 0.0, 0.0, 1.0],
            "scale": [1.0, 1.0, 1.0],
        }
        children = [base_node_idx + ci for ci, cb in enumerate(bones) if cb["parent"] == bi]
        if children:
            j_node["children"] = children
        nodes.append(j_node)

    # Inverse bind matrices (MAT4 column-major translate(-joint_world_pos))
    ibm_raw = bytearray()
    for b in bones:
        jx, jy, jz = b["pos"]
        ibm_raw.extend(struct.pack(
            "<16f",
            1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            -jx, -jy, -jz, 1.0,
        ))
    ibm_bv = _append_buffer_view(gltf, bin_data, bytes(ibm_raw))
    ibm_acc = _append_accessor(gltf, ibm_bv, 5126, "MAT4", len(bones))

    skin_idx = len(gltf.setdefault("skins", []))
    gltf["skins"].append({
        "name": f"TinCan_{chosen_rig}_Skin",
        "inverseBindMatrices": ibm_acc,
        "joints": joint_node_indices,
        "skeleton": joint_node_indices[0],
    })

    # Attach skin + root skeleton joint to scene
    for node in nodes[:base_node_idx]:
        if "mesh" in node:
            node["skin"] = skin_idx

    scenes = gltf.setdefault("scenes", [{"nodes": []}])
    s_idx = int(gltf.get("scene", 0))
    scene_nodes = scenes[s_idx].setdefault("nodes", [])
    if joint_node_indices[0] not in scene_nodes:
        scene_nodes.append(joint_node_indices[0])

    # Build procedural keyframe animations
    req_anim = (animation or "walk").strip().lower()
    if req_anim == "all":
        clip_specs = [("walk", 1.2), ("run", 0.72), ("idle", 2.4), ("dance", 1.6)]
    elif req_anim in ("walk", "run", "idle", "dance"):
        dur_map = {"walk": 1.2, "run": 0.72, "idle": 2.4, "dance": 1.6}
        clip_specs = [(req_anim, dur_map[req_anim])]
    else:
        clip_specs = [("walk", 1.2)]

    num_frames = 25
    animations_out = gltf.setdefault("animations", [])
    clip_names: List[str] = []

    for clip_name, duration in clip_specs:
        times = [duration * (i / float(num_frames - 1)) for i in range(num_frames)]
        t_raw = struct.pack(f"<{num_frames}f", *times)
        t_bv = _append_buffer_view(gltf, bin_data, t_raw)
        t_acc = _append_accessor(gltf, t_bv, 5126, "SCALAR", num_frames, min_vals=[0.0], max_vals=[float(duration)])

        samplers: List[Dict[str, Any]] = []
        channels: List[Dict[str, Any]] = []
        pelvis_pos = bones[0]["pos"]

        for bi, b in enumerate(bones):
            rot_frames: List[Quat] = []
            tr_frames: List[Vec3] = []
            has_rot = False
            has_tr = False

            for fi in range(num_frames):
                phase = 2.0 * math.pi * (fi / float(num_frames - 1))
                rq, tv = _anim_pose_for_bone(clip_name, b["name"], phase, pelvis_pos, scale_h)
                if rq is not None:
                    has_rot = True
                    rot_frames.append(rq)
                else:
                    rot_frames.append((0.0, 0.0, 0.0, 1.0))
                if tv is not None:
                    has_tr = True
                    tr_frames.append(tv)
                else:
                    tr_frames.append(pelvis_pos)

            j_node_idx = joint_node_indices[bi]
            if has_rot:
                r_raw = bytearray()
                for q in rot_frames:
                    r_raw.extend(struct.pack("<4f", *q))
                r_bv = _append_buffer_view(gltf, bin_data, bytes(r_raw))
                r_acc = _append_accessor(gltf, r_bv, 5126, "VEC4", num_frames)
                s_id = len(samplers)
                samplers.append({"input": t_acc, "interpolation": "LINEAR", "output": r_acc})
                channels.append({"sampler": s_id, "target": {"node": j_node_idx, "path": "rotation"}})

            if has_tr:
                tr_raw = bytearray()
                for tv in tr_frames:
                    tr_raw.extend(struct.pack("<3f", *tv))
                tr_bv = _append_buffer_view(gltf, bin_data, bytes(tr_raw))
                tr_acc = _append_accessor(gltf, tr_bv, 5126, "VEC3", num_frames)
                s_id = len(samplers)
                samplers.append({"input": t_acc, "interpolation": "LINEAR", "output": tr_acc})
                channels.append({"sampler": s_id, "target": {"node": j_node_idx, "path": "translation"}})

        animations_out.append({
            "name": f"TinCan_{clip_name}",
            "samplers": samplers,
            "channels": channels,
        })
        clip_names.append(f"TinCan_{clip_name}")

    out_bytes = pack_glb(gltf, bin_data)
    meta = {
        "rig_type": chosen_rig,
        "bones": [b["name"] for b in bones],
        "bone_count": len(bones),
        "animations": clip_names,
        "vertex_count": len(all_points),
        "size_bytes": len(out_bytes),
        "cost_usd": 0.0,
    }
    return out_bytes, meta
