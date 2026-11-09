"""Procedural builder for space_base_minigame v13 (design r15).

run: knowledge/active/20261108-space-base-v13-testworkshop/runs/20261108-1755
Derived from build_scene_v12.py. N5 prototype: south end rebuilt as the
*horizontal test workshop* (open-air blast-wall yard), per real-game reference
12_水平试车间.jpg (A-grade observation card, MASTER_SPEC 8.4.6).

DO-NOT-ROOF: no roof slabs / parapet return / spanning trusses / skylight covers.

De-symmetry code contract (R1-R5, see EXTERIOR_ORGANIC_PLAN v2.0 §2.3):
  R1 break periodicity  - no bare range(a,b,step) generating visual props
  R2 break mirroring    - never `for side in (-1, 1)` for one prop family
  R3 break heading      - rotate peer props by a seeded jitter
  R4 break collinearity - prop centres must not sit on one t/u or v line
  R5 structural exception - buildings, road markings, joints, bridges, rails,
                            stall lines and rack posts stay straight.
Seed: random.Random(20261108). Ground slabs must be >= 0.14 m thick
(0.02 m decals do not receive light in this scene; see v12/DEVLOG.md).
"""
from __future__ import annotations

import argparse
import math
import os
import random
import re
import sys

import bpy
from mathutils import Vector

# ------------------------------------------------------------------ constants
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PLAN = os.path.join(ROOT, "planning", "art", "SPACE_BASE_NEW_PLAN_20261103.md")

# octagon platform (v3.10 §3.5), top +6
AV_HEAD0 = (125.0, -6.6)
AV_U0, AV_V0 = (0.342, -0.940), (0.940, 0.342)


def av_pt(t, off=0.0):
    return (AV_HEAD0[0] + AV_U0[0] * t + AV_V0[0] * off,
            AV_HEAD0[1] + AV_U0[1] * t + AV_V0[1] * off)


OCT = [(76.8, -6.6), (163.2, -6.6), (180, 13.2), (180, 106.8),
       (163.2, 120), (76.8, 120), (53.4, 106.8), (53.4, 13.2)]   # v08: x0.9 about (120,60)
# v07 landmark alignment (SPACE_BASE_LANDMARK_ALIGNMENT_PLAN_20261104.md §4):
# island + channel + two bridges + outer bands (Q1), garden removed (Q2)
CHAN_N = (44, 196, 120, 134)          # north channel strip cut from platform
CHAN_E = (180, 196, -16, 136)         # east channel strip cut from platform
PALMS = [av_pt(t, s) for t in (12.0, 27.0, 42.0, 57.0) for s in (-32.0, 32.0)]
CAUSE_A = (152.0, -8.0)               # v08: start on the shrunk island edge
CAUSE_B = (172.0, -136.0)             # peninsula NW neck
CAUSE_W = 18.0
DOCK_O = (172.0, -136.0)
DOCK_U = (math.sin(math.radians(20)), -math.cos(math.radians(20)))   # SE, len 96
DOCK_V = (math.cos(math.radians(20)), math.sin(math.radians(20)))    # NE, half 25
DOCK_LEN, DOCK_HALF = 96.0, 30.0      # v09: 60 m wide so the 24 m avenue fits with 18 m side bands
DOCK_WALL_H = 9.0

ROOMS = {
    "H1": (66, 120, 6, 60),
    "H2": (66, 120, 60, 114),
    "H3": (120, 174, 60, 114),
    "H4": (120, 174, 6, 60),
}
WALL_H = {"H1": 9.0, "H2": 9.0, "H3": 9.0, "H4": 13.0}
DOOR_W = 3.2
GATES = {"G1": (93.0, 60), "G2": (147.0, 60), "E1": (93.0, 6),
         "E2": (147.0, 6), "E3": (93.0, 114), "E4": (147.0, 114)}


PLATFORM_Z = 4.70          # v11: the whole fan sits level with the garden deck
WATER_TOP = 0.0

# v08: indoor contents keep their size but move toward the core centre (rooms 60->54)
SHRINK = 0.9
IND = {"on": False}
CORE_C = (120.0, 60.0)


def _tc(x, y):
    if not IND["on"]:
        return x, y
    return CORE_C[0] + (x - CORE_C[0]) * SHRINK, CORE_C[1] + (y - CORE_C[1]) * SHRINK


def _box_xy(x0, x1, y0, y1, z0, z1):
    """Flat decals scale with the room; solid props keep extents and shift centre."""
    if not IND["on"]:
        return x0, x1, y0, y1
    if z1 - z0 <= 0.25:
        (x0, y0), (x1, y1) = _tc(x0, y0), _tc(x1, y1)
        return x0, x1, y0, y1
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    hx, hy = (x1 - x0) / 2.0, (y1 - y0) / 2.0
    cx, cy = _tc(cx, cy)
    return cx - hx, cx + hx, cy - hy, cy + hy


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--render", default="")
    ap.add_argument("--res", default="3360x5880")
    ap.add_argument("--samples", type=int, default=24)
    return ap.parse_args(argv)


# ------------------------------------------------------------------ helpers
def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def coll(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgba(value, alpha=1.0):
    value = value.lstrip("#")
    return tuple(srgb_to_linear(int(value[i:i + 2], 16) / 255.0) for i in (0, 2, 4)) + (alpha,)


def make_mat(name, hex_color, rough=0.7, metal=0.0, alpha=1.0, emission=None, emis=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    r, g, bl, _ = hex_rgba(hex_color, alpha)
    b.inputs["Base Color"].default_value = (r, g, bl, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND"
    if emission:
        er, eg, eb, _ = hex_rgba(emission)
        key = "Emission Color" if "Emission Color" in b.inputs else "Emission"
        b.inputs[key].default_value = (er, eg, eb, 1.0)
        b.inputs["Emission Strength"].default_value = emis
    return m


def _mesh_obj(name, mesh, mat, collection):
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    if mat is not None:
        obj.data.materials.append(mat)
    return obj


def add_box(name, x0, x1, y0, y1, z0, z1, mat, c):
    x0, x1, y0, y1 = _box_xy(x0, x1, y0, y1, z0, z1)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
        [], [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    mesh.validate(); mesh.update()
    return _mesh_obj(name, mesh, mat, c)


def add_box_local(name, cx, cy, cz, dx, dy, dz, mat, c, rot_z=0.0):
    cx, cy = _tc(cx, cy)
    mesh = bpy.data.meshes.new(name)
    hx, hy, hz = dx / 2.0, dy / 2.0, dz / 2.0
    mesh.from_pydata([
        (-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
        (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)],
        [], [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    mesh.validate(); mesh.update()
    obj = _mesh_obj(name, mesh, mat, c)
    obj.location = (cx, cy, cz)
    obj.rotation_euler = (0.0, 0.0, rot_z)
    return obj


def add_prism(name, pts, z_bot, z_top, mat, c):
    """Footprint pts [(x,y)...], per-vertex bottom/top callables or consts."""
    if IND["on"]:
        pts = [_tc(px, py) for (px, py) in pts]
    zb = [z_bot(i, p) for i, p in enumerate(pts)] if callable(z_bot) else [z_bot] * len(pts)
    zt = [z_top(i, p) for i, p in enumerate(pts)] if callable(z_top) else [z_top] * len(pts)
    verts = [(p[0], p[1], zb[i]) for i, p in enumerate(pts)] + \
            [(p[0], p[1], zt[i]) for i, p in enumerate(pts)]
    n = len(pts)
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.validate(); mesh.update()
    return _mesh_obj(name, mesh, mat, c)


def add_cyl(name, x, y, z0, z1, r, mat, c, axis="Z", vertices=20):
    x, y = _tc(x, y)
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=r, depth=z1 - z0,
                                        location=(x, y, (z0 + z1) / 2.0))
    obj = bpy.context.object
    obj.name = name
    for cc in list(obj.users_collection):
        cc.objects.unlink(obj)
    c.objects.link(obj)
    obj.data.materials.append(mat)
    if axis == "X":
        obj.rotation_euler[1] = math.radians(90)
    elif axis == "Y":
        obj.rotation_euler[0] = math.radians(90)
    return obj


def add_cyl_h(name, x, y, zc, length, r, mat, c, axis="X", vertices=20, rot_z=0.0):
    """Horizontal cylinder whose axis sits at height zc, centred at (x, y)."""
    obj = add_cyl(name, x, y, zc - length / 2.0, zc + length / 2.0, r, mat, c,
                  axis=axis, vertices=vertices)
    if rot_z:
        obj.rotation_euler[2] = rot_z
    return obj


def add_tube(name, x, y, r_out, r_in, z0, z1, mat, c, segments=40, a0=0.0, a1=2 * math.pi):
    x, y = _tc(x, y)
    mesh = bpy.data.meshes.new(name)
    verts = []
    for z in (z0, z1):
        for r in (r_out, r_in):
            for i in range(segments + 1):
                a = a0 + (a1 - a0) * i / segments
                verts.append((x + r * math.cos(a), y + r * math.sin(a), z))
    faces, stride = [], segments + 1
    for i in range(segments):
        faces.append((i, i + 1, stride + i + 1, stride + i))
    base = 2 * stride
    for i in range(segments):
        faces.append((base + i, base + i + 1, base + stride + i + 1, base + stride + i))
        faces.append((i, base + i, base + i + 1, i + 1))
        faces.append((stride + i, stride + i + 1, base + stride + i + 1, base + stride + i))
    mesh.from_pydata(verts, [], faces)
    mesh.validate(); mesh.update()
    return _mesh_obj(name, mesh, mat, c)


def dock_world(u, v):
    return (DOCK_O[0] + DOCK_U[0] * u + DOCK_V[0] * v,
            DOCK_O[1] + DOCK_U[1] * u + DOCK_V[1] * v)


DOCK_ROTZ = math.atan2(DOCK_U[1], DOCK_U[0])   # -70 deg


def dock_box(name, u, v, du, dv, z0, z1, mat, c):
    x, y = dock_world(u, v)
    return add_box_local(name, x, y, (z0 + z1) / 2.0, du, dv, z1 - z0, mat, c, rot_z=DOCK_ROTZ)


def dock_win(name, u0, u1, z0, z1, v_face, sign, m, c, mullions=2):
    """Exterior window on a peninsula facade: light frame plate + dark glass + mullions.

    sign = +1 when the facade looks toward +v (K05/K07, road side), -1 otherwise.
    """
    uc = (u0 + u1) / 2.0
    dock_box(name + "_fr", uc, v_face + 0.03 * sign, (u1 - u0) + 0.36, 0.10,
             z0 - 0.18, z1 + 0.18, m["win_frame"], c)
    dock_box(name + "_gl", uc, v_face + 0.10 * sign, u1 - u0, 0.06, z0, z1,
             m["win_dark"], c)
    for k in range(mullions):
        uu = u0 + (u1 - u0) * (k + 1.0) / (mullions + 1.0)
        dock_box(f"{name}_mu{k}", uu, v_face + 0.14 * sign, 0.13, 0.06, z0, z1,
                 m["win_frame"], c)


def wall_h(name, y, x0, x1, h, openings, mat, c, t=0.6, z0=PLATFORM_Z):
    pos, idx = x0, 0
    for a, b in sorted(openings):
        if a > pos:
            add_box(f"{name}_{idx}", pos, a, y - t / 2, y + t / 2, z0, z0 + h, mat, c)
            idx += 1
        pos = max(pos, b)
    if pos < x1:
        add_box(f"{name}_{idx}", pos, x1, y - t / 2, y + t / 2, z0, z0 + h, mat, c)


def wall_v(name, x, y0, y1, h, openings, mat, c, t=0.6, z0=PLATFORM_Z):
    pos, idx = y0, 0
    for a, b in sorted(openings):
        if a > pos:
            add_box(f"{name}_{idx}", x - t / 2, x + t / 2, pos, a, z0, z0 + h, mat, c)
            idx += 1
        pos = max(pos, b)
    if pos < y1:
        add_box(f"{name}_{idx}", x - t / 2, x + t / 2, pos, y1, z0, z0 + h, mat, c)


# ------------------------------------------------------------------ materials
# M8.5 光照预补偿（迭代 r3）：实测规律——低饱和冷色被暖光拖色相（ΔH −40..−66）且
# S 被稀释 2-3 倍（基色 S 钳 1.0 仍只渲染 0.26）；高饱和色守住色相（C5 ΔH+4）。
# r3 策略：h1-h4 基色 = 目标色相 + S1.0/L0.30，再叠同色相 emission 0.30-0.40 护色；
# C5 r2 已 PASS 不动（基色 = r1 补偿值）。probe 目标值口径不变（统一方案 §4.1）。
import colorsys as _cs


def _hsl_hex(h, s, l):
    r, g, b = _cs.hls_to_rgb((h % 360) / 360.0, l, s)
    return "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))


def _hsl(hx):
    hx = hx.lstrip("#")
    r, g, b = (int(hx[i:i + 2], 16) / 255 for i in (0, 2, 4))
    h, l, s = _cs.rgb_to_hls(r, g, b)
    return h * 360, s, l


def _compensated(target_hex, measured_h, measured_s, measured_l):
    th, ts, tl = _hsl(target_hex)
    return _hsl_hex(2 * th - measured_h,
                    min(0.95, ts * ts / max(measured_s, 0.02)),
                    min(0.85, max(0.05, tl * tl / max(measured_l, 0.05))))


C_C5 = _hsl_hex(26.6, 0.20, 0.335)               # v09.1: 直接给 L（补偿式已到极限，实测仍 +0.07）


def build_materials():
    return {
        "water": make_mat("v6.water", "#17383F", 0.22, 0.0, 1.0, "#0F282E", 0.50),
        "platform": make_mat("v6.platform", "#BBB7A8", 0.9),       # v14 r3 +4% for S1
        "garden": make_mat("v6.garden", "#B8AC96", 0.9),           # 压暗后微调回
        "garden_wall": make_mat("v10.garden_wall", "#3A403C", 0.85),
        "garden_orange": make_mat("v10.garden_orange", "#874E2F", 0.55),
        "garden_coping": make_mat("v10.garden_coping", "#D8D2C6", 0.72),
        "garden_border": make_mat("v10.garden_border", "#A79C92", 0.9),
        "garden_pool": make_mat("v10.garden_pool", "#2E4A4A", 0.22),
        "garden_gravel": make_mat("v10.garden_gravel", "#A79D8E", 0.95),
        "garden_stone": make_mat("v10.garden_stone", "#C9C2B4", 0.88),
        "garden_hedge": make_mat("v10.garden_hedge", "#33402F", 0.85),
        "garden_grass": make_mat("v10.garden_grass", "#4E5C3E", 0.9),
        "garden_walk": make_mat("v10.garden_walk", "#BAB2A5", 0.9),
        "garden_rust": make_mat("v10.garden_rust", "#9C8C6E", 0.94),
        "win_dark": make_mat("v10.win_dark", "#4F6167", 0.28),
        "win_frame": make_mat("v10.win_frame", "#EDE7DA", 0.85),
        "garden_dark": make_mat("v10.garden_dark", "#2A2A26", 0.7),
        "dock": make_mat("v6.dock", "#8A8C84", 0.9),               # 中性灰绿（工业）
        "road": make_mat("v9.road", "#7C7F81", 0.90),              # v14 M05 压暗
        "apron": make_mat("v9.apron", "#B0AC9F", 0.9),             # 混凝土场坪
        "causeway": make_mat("v6.causeway", "#B6B5AB", 0.9),
        "island": make_mat("v6.island", "#7E8482", 0.95),
        "h1": make_mat("v6.h1", _hsl_hex(208, 1.0, 0.20), 0.9, 0.0, 1.0, "#547684", 0.62),
        "h2": make_mat("v6.h2", _hsl_hex(212, 1.0, 0.30), 0.9, 0.0, 1.0, "#477A8A", 0.32),
        "h3": make_mat("v6.h3", _hsl_hex(224, 1.0, 0.075), 0.9, 0.0, 1.0, "#3A6DBF", 0.86),
        "h4": make_mat("v6.h4", _hsl_hex(185, 0.44, 0.285), 0.9),
        "wall": make_mat("v6.wall", "#E2DDD0", 0.65),
        "wall_h4": make_mat("v6.wall_h4", "#4A7A5A", 0.65),        # 涂装板绿（仅 3-4 块）
        "rib_blue": make_mat("v6.rib_blue", "#3E5CA8", 0.6, 0.2),  # H3 肋板藏蓝（r6 增饱和）
        "h3_strip": make_mat("v6.h3_strip", "#4C86D8", 0.4, 0.0, 1.0, "#4C86D8", 1.9),
        "green_in": make_mat("v6.green_in", "#357F52", 0.7),
        "glass": make_mat("v6.glass", "#A9BEC6", 0.1, 0.0, 0.42),
        "frost": make_mat("v6.frost", "#D8E2E4", 0.5, 0.0, 0.55),
        "metal": make_mat("v6.metal", "#525F64", 0.42, 0.60),
        "steel": make_mat("v6.steel", "#8B9698", 0.42, 0.60),   # v09.1: 镀锌屋面更亮（S1）
        "dark": make_mat("v6.dark", "#1E2427", 0.8),
        "white": make_mat("v6.white", "#E8ECEC", 0.6),
        "yellow": make_mat("v6.yellow", "#F2C230", 0.55),
        "evac_blue": make_mat("v6.evac_blue", "#2E6FA8", 0.5),
        "evac_floor": make_mat("v6.evac_floor", "#2E5FC8", 0.85, 0.0, 1.0, "#2E5FC8", 0.20),
        "evac": make_mat("v6.evac", "#FFE010", 0.45, 0.0, 1.0, "#FFE010", 5.0),
        "green": make_mat("v6.green", "#3E9B63", 0.6),
        "pool": make_mat("v6.pool", "#123B47", 0.22),
        "pit": make_mat("v6.pit", "#151C20", 0.8),
        "pit_blue": make_mat("v6.pit_blue", "#0E1E33", 0.8, 0.0, 1.0, "#2A4C82", 1.10),
        "zone_blue": make_mat("v6.zone_blue", "#8AA6C8", 0.85),    # H3 蓝灰分区带
        "zone_blight": make_mat("v6.zone_blight", "#8FB0DC", 0.85),  # H3 蓝调亮条
        "brass": make_mat("v6.brass", "#8A6A45", 0.42, 0.7),
        "gold": make_mat("v6.gold", "#C9A227", 0.4, 0.7),
        "caramel": make_mat("v6.caramel", C_C5, 0.74, 0.0, 1.0, "#E8D6B4", 0.04),
        "rug": make_mat("v6.rug", "#C9B49A", 0.85),                # v6 leftover (unused)
        "zone_light": make_mat("v6.zone_light", "#A9C4B6", 0.85),  # H4 亮分区条（S11 对比）
        "wood": make_mat("v6.wood", "#6B4A33", 0.7),
        "container_blue": make_mat("v6.ctl_b", "#2F5C9C", 0.55, 0.3),
        "container_olive": make_mat("v6.ctl_o", "#5A6247", 0.6, 0.2),
        "container_gray": make_mat("v6.ctl_g", "#676D6E", 0.6, 0.2),
        "foliage": make_mat("v6.foliage", "#3E6B4A", 0.85),
        "teal": make_mat("v6.teal", "#2F6D78", 0.55),
        "emis": make_mat("v6.emis", "#F2F5F0", 0.4, 0.0, 1.0, "#F2F5F0", 2.0),
        "orange": make_mat("v6.orange", "#C87A30", 0.55),
        "bluebox": make_mat("v6.bluebox", "#2E6FA8", 0.5),
        "rock": make_mat("v6.rock", "#71766F", 0.95),
        "mesh": make_mat("v6.mesh", "#9AA4A2", 0.6, 0.3, 0.5),
        "char_dark": make_mat("v9.char_dark", "#232A33", 0.75),
        "truss_dark": make_mat("v9.truss", "#39424B", 0.7),
        "soffit": make_mat("v9.soffit", "#2A3138", 0.85),
        "char_mid": make_mat("v9.char_mid", "#4A5865", 0.6),
        "char_acc": make_mat("v9.char_acc", "#6E7C88", 0.5, 0.25),
        "char_visor": make_mat("v9.char_visor", "#8FB6CE", 0.25, 0.0, 1.0, "#9FC6DE", 0.9),
        # ---- v12: 去几何化——墙顶骨架 / 室内地坪 / 双线岸缘
        "cope": make_mat("v12.cope", "#3B4344", 0.72),            # 墙顶深色压顶（顶视骨架）
        "floor_ind": make_mat("v12.floor_ind", "#939A98", 0.88),  # 室内工业地坪（冷灰）
        "floorshadow": make_mat("v12.floorshadow", "#6E7674", 0.95),  # 墙脚暗带
        "joint": make_mat("v12.joint", "#7E8482", 0.95),          # 地坪分仓缝
        "terrace": make_mat("v12.terrace", "#82857C", 0.92),      # 下部台地（比场地暗一档）
        "sand": make_mat("v12.sand", "#C0B394", 0.95),            # 沙滩段
        "riprap": make_mat("v12.riprap", "#565B53", 0.96),        # 抛石
        "dome": make_mat("v12.dome", "#E6E8E4", 0.55),            # 雷达罩球壳
        "dome_base": make_mat("v12.dome_base", "#8E9492", 0.8),   # 雷达罩基座
        # ---- v15 四核心区（复核 D2/D5/D9：冷相深色 + 色温预补偿）
        "h1_floor": make_mat("v15.h1_floor", "#767C78", 0.90),
        "h1_disc": make_mat("v15.h1_disc", "#222B2D", 0.86),
        "h2_poolbed": make_mat("v15.h2_poolbed", "#232A2C", 0.92),
        "h3_pitbed": make_mat("v15.h3_pitbed", "#2E5490", 0.86),
        "cap_h1": make_mat("v15.cap_h1", "#1C7C88", 0.62),
        "cap_h2": make_mat("v15.cap_h2", "#3E6E73", 0.62),
        "cap_h3": make_mat("v15.cap_h3", "#2C4A78", 0.66),
        "cap_h4": make_mat("v15.cap_h4", "#3E9159", 0.62),
        # ---- v13 水平试车间（露天防爆试验场）
        "ws_concrete": make_mat("v13.ws_concrete", "#979C9C", 0.9),   # 清水混凝土防爆墙
        "ws_stain": make_mat("v13.ws_stain", "#6E7573", 0.95),        # 墙脚 1.5 m 水渍
        "ws_coping": make_mat("v13.ws_coping", "#5F6667", 0.85),      # 墙顶压顶
        "ws_green": make_mat("v13.ws_green", "#17707C", 0.7),         # ENTRANCE 门套
        "ws_yellow": make_mat("v13.ws_yellow", "#D6A62B", 0.7),       # 黄线/护栏
        "ws_refractory": make_mat("v13.ws_refractory", "#8A6A52", 0.95),  # 导流坑耐火砖
        "ws_wet": make_mat("v13.ws_wet", "#5F6B6B", 0.3),            # 积水
        "ws_terminal": make_mat("v13.ws_terminal", "#3E9B63", 0.6),   # 墙面绿色小终端
        "ws_glass": make_mat("v13.ws_glass", "#A9BEC6", 0.2, 0.0, 0.45),
    }


# ------------------------------------------------------------------ terrain
# ------------------------------------------------------------------ v11 fan site
FAN_T_N = -141.0          # north edge
FAN_HALF_N = 73.0         # half width at the north edge (146 total = core width)
FAN_T_S = 126.0           # south edge (where the arc meets the flanks)
FAN_HALF_S = 98.0         # half width at the south arc (196 total)
FAN_ARC = 20.0            # extra depth at the crown of the south arc
FAN_BAY_T = 114.0         # bridge bay: land stops here in the middle
FAN_BAY_HALF = 14.0


def fan_half(t):
    f = (t - FAN_T_N) / (FAN_T_S - FAN_T_N)
    return FAN_HALF_N + (FAN_HALF_S - FAN_HALF_N) * max(0.0, min(1.0, f))


def fan_poly():
    """kept as an alias so the shore band follows the r13 stepped outline."""
    return site_poly()


def add_poly(name, pts, z0, z1, mat, c):
    """Solid prism from an arbitrary (possibly concave) footprint."""
    import bmesh
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    c.objects.link(ob)
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, z1)) for x, y in pts]
    bm.faces.new(vs)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob.data.materials.append(mat)
    sol = ob.modifiers.new("sol", "SOLIDIFY")
    sol.thickness = z1 - z0
    sol.offset = -1.0
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=sol.name)
    return ob


def fan_perimeter_wall(pts, m, c, h=0.86):
    """Seawall parapet: dark face + orange band + pale coping, one run per edge."""
    n = len(pts)
    for i in range(n):
        p0, p1 = pts[i], pts[(i + 1) % n]
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy)
        if L < 0.4:
            continue
        ang = math.atan2(dy, dx)
        mx, my = (p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0
        add_box_local(f"fan_wall_{i}", mx, my, PLATFORM_Z + h / 2.0, L + 0.30, 0.46, h,
                      m["garden_wall"], c, rot_z=ang)
        add_box_local(f"fan_band_{i}", mx, my, PLATFORM_Z + h * 0.62, L + 0.32, 0.50, 0.17,
                      m["garden_orange"], c, rot_z=ang)
        add_box_local(f"fan_cope_{i}", mx, my, PLATFORM_Z + h + 0.07, L + 0.34, 0.62, 0.14,
                      m["garden_coping"], c, rot_z=ang)


# ------------------------------------------------------------------ v13 stepped site
SITE_TN = -99.0           # north edge (13 m front yard)
SITE_W1 = 47.0            # half width of the core band (94)
SITE_T1 = 5.0             # step 1: core/loading -> apron
SITE_W2 = 37.0            # 74
SITE_T2 = 70.0            # step 2: apron -> parking
SITE_W3 = 31.0            # 62
SITE_TS = 104.0           # south edge (bridge head)


def site_poly():
    return [av(SITE_TN, -SITE_W1), av(SITE_TN, SITE_W1),
            av(SITE_T1, SITE_W1), av(SITE_T1, SITE_W2),
            av(SITE_T2, SITE_W2), av(SITE_T2, SITE_W3),
            av(SITE_TS, SITE_W3), av(SITE_TS, -SITE_W3),
            av(SITE_T2, -SITE_W3), av(SITE_T2, -SITE_W2),
            av(SITE_T1, -SITE_W2), av(SITE_T1, -SITE_W1)]


def add_poly(name, pts, z0, z1, mat, c):
    import bmesh
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    c.objects.link(ob)
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, z1)) for x, y in pts]
    bm.faces.new(vs)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob.data.materials.append(mat)
    sol = ob.modifiers.new("sol", "SOLIDIFY")
    sol.thickness = z1 - z0
    sol.offset = -1.0
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=sol.name)
    return ob


def site_wall(pts, m, c, h=0.86):
    n = len(pts)

    def tv(p):
        return ((p[0] - AV_HEAD[0]) * AV_U[0] + (p[1] - AV_HEAD[1]) * AV_U[1],
                (p[0] - AV_HEAD[0]) * AV_V[0] + (p[1] - AV_HEAD[1]) * AV_V[1])

    for i in range(n):
        p0, p1 = pts[i], pts[(i + 1) % n]
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy)
        if L < 0.4:
            continue
        # r14: leave a 26 m gate bay in the middle of the north edge
        t0_, v0_ = tv(p0)
        t1_, v1_ = tv(p1)
        if abs(t0_ - SITE_TN) < 0.5 and abs(t1_ - SITE_TN) < 0.5:
            for k, (a0, a1) in enumerate(((min(v0_, v1_), -13.0), (13.0, max(v0_, v1_)))):
                if a1 - a0 < 1.0:
                    continue
                dv = (a0 + a1) / 2.0 - v0_      # absolute v -> offset from this corner
                bx, by = p0[0] + dv * AV_V[0], p0[1] + dv * AV_V[1]
                add_box_local(f"fan_wall_n{k}", bx, by, PLATFORM_Z + h / 2.0,
                              a1 - a0 + 0.3, 0.46, h, m["garden_wall"], c, rot_z=AV_ROT)
                add_box_local(f"fan_band_n{k}", bx, by, PLATFORM_Z + h * 0.62,
                              a1 - a0 + 0.32, 0.50, 0.17, m["garden_orange"], c,
                              rot_z=AV_ROT)
                add_box_local(f"fan_cope_n{k}", bx, by, PLATFORM_Z + h + 0.07,
                              a1 - a0 + 0.34, 0.62, 0.14, m["garden_coping"], c,
                              rot_z=AV_ROT)
            continue
        ang = math.atan2(dy, dx)
        mx, my = (p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0
        add_box_local(f"fan_wall_{i}", mx, my, PLATFORM_Z + h / 2.0, L + 0.30, 0.46, h,
                      m["garden_wall"], c, rot_z=ang)
        add_box_local(f"fan_band_{i}", mx, my, PLATFORM_Z + h * 0.62, L + 0.32, 0.50, 0.17,
                      m["garden_orange"], c, rot_z=ang)
        add_box_local(f"fan_cope_{i}", mx, my, PLATFORM_Z + h + 0.07, L + 0.34, 0.62, 0.14,
                      m["garden_coping"], c, rot_z=ang)


def build_terrain(m):
    g = coll("TERRAIN")
    add_box("water", -1000, 1000, -1000, 1000, WATER_TOP - 0.35, WATER_TOP - 0.12, m["water"], g)
    pts = site_poly()
    add_poly("fan_plate", pts, -1.1, PLATFORM_Z, m["platform"], g)
    add_poly("fan_pave", pts, PLATFORM_Z, PLATFORM_Z + 0.02, m["apron"], g)
    site_wall(pts, m, g)
    z = PLATFORM_Z + 0.02
    # 12 m paving joints, band by band
    for t0, t1, hw in ((SITE_TN, SITE_T1, SITE_W1), (SITE_T1, SITE_T2, SITE_W2),
                       (SITE_T2, SITE_TS, SITE_W3)):
        t = t0 + 12.0
        while t < t1 - 1.0:
            av_box(f"fc_joint_t{int(t)}", t, 0, 0.05, hw * 2 - 3.0, z, z + 0.014,
                   m["garden_border"], g)
            t += 12.0
        for v in range(int(-hw) + 8, int(hw) - 6, 12):
            av_box(f"fc_joint_v{int(t0)}_{v}", (t0 + t1) / 2.0, v, t1 - t0 - 2.0, 0.05,
                   z, z + 0.014, m["garden_border"], g)
    print("SITE_OK")


# ---------------------------------------------------------- v12 双线岸缘 / 抛石 / 落地罩
def _signed_area(pts):
    s = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        s += x0 * y1 - x1 * y0
    return s * 0.5


def _out_normals(pts):
    sgn = 1.0 if _signed_area(pts) > 0 else -1.0
    n = len(pts)
    out = []
    for i in range(n):
        p0, p1 = pts[i], pts[(i + 1) % n]
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy) or 1.0
        out.append((sgn * dy / L, -sgn * dx / L))
    return out


def offset_poly(pts, d):
    """Miter offset outward by d; sharp corners clamped so no spikes appear."""
    n = len(pts)
    nrm = _out_normals(pts)
    res = []
    for i in range(n):
        n1 = nrm[(i - 1) % n]
        n2 = nrm[i]
        mx, my = n1[0] + n2[0], n1[1] + n2[1]
        L = math.hypot(mx, my)
        if L < 1e-6:
            mx, my, L = n2[0], n2[1], 1.0
        mx, my = mx / L, my / L
        cosh = max(mx * n2[0] + my * n2[1], 0.45)
        res.append((pts[i][0] + mx * d / cosh, pts[i][1] + my * d / cosh))
    return res


def build_lower_terrace(m):
    """v12: 分段下部台地——抛石 / 沙滩 / 直壁三种岸线交替，俯视形成第二条线。"""
    g = coll("TERRACE")
    pts = site_poly()
    qs = offset_poly(pts, 5.5)
    n = len(pts)
    # 逐段选材：台地 / 沙滩 / 台地 / 抛石坡 交替，避免整圈一个做法
    kinds = ["terrace", "sand", "terrace", "gravel", "terrace", "sand",
             "terrace", "gravel", "terrace", "sand", "terrace", "gravel"]
    for i in range(n):
        mat = m.get(kinds[i % len(kinds)], m["terrace"])
        add_poly("low_terrace_%d" % i, [pts[i], pts[(i + 1) % n], qs[(i + 1) % n], qs[i]],
                 -0.8, 1.25, mat, g)
    rnd = random.Random(20261108)
    nrm = _out_normals(pts)
    for i in range(n):
        p0, p1 = pts[i], pts[(i + 1) % n]
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy)
        if L < 1.5:
            continue
        ux, uy = dx / L, dy / L
        nx, ny = nrm[i]
        # 抛石只铺在 terrace / gravel 段，沙滩段留空
        if kinds[i % len(kinds)] == "sand":
            continue
        k = max(2, int(L / 2.4))
        for j in range(k):
            f = (j + rnd.uniform(0.08, 0.92)) / k
            off = 4.6 + rnd.uniform(0.0, 1.5)
            px = p0[0] + ux * L * f + nx * off
            py = p0[1] + uy * L * f + ny * off
            r = rnd.uniform(0.55, 1.15)
            h = rnd.uniform(0.45, 1.05)
            add_cyl("riprap_%d_%d" % (i, j), px, py, 0.25, 0.25 + h, r,
                    m["riprap"], g, vertices=7)
    print("TERRACE_OK")


def build_domes(m):
    """v12: 落地雷达罩。不要屋顶之后，这是航天符号唯一的载体。"""
    g = coll("DOMES")
    for i, (t, v, r) in enumerate(((-91.5, -35.0, 2.9), (-91.5, 35.0, 2.9))):
        x, y = av(t, v)
        add_cyl("dome_base_%d" % i, x, y, PLATFORM_Z, PLATFORM_Z + 1.10, r + 0.40,
                m["dome_base"], g, vertices=24)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=28, ring_count=14, radius=r,
                                             location=(x, y, PLATFORM_Z + 1.02))
        ob = bpy.context.active_object
        ob.name = "dome_%d" % i
        for col in list(ob.users_collection):
            col.objects.unlink(ob)
        g.objects.link(ob)
        ob.data.materials.append(m["dome"])
        ob.scale = (1.0, 1.0, 0.94)
    print("DOMES_OK")


def build_site_dressing(m):
    """v12: 中部空场地补功能带——侧向场坪 / 碎石堆场 / 泊位 / 草缘 / 管廊 / 箱堆。"""
    g = coll("SITE_DRESS")
    zb = PLATFORM_Z + 0.02          # 铺装顶面
    T = 0.14                        # 功能带做实体厚度（薄片在这里不受光）

    def pad(name, t0, t1, v0, v1, mat):
        avr(name, t0, t1, v0, v1, zb, zb + T, mat, g)

    def line(name, t0, t1, v0, v1, mat):
        avr(name, t0, t1, v0, v1, zb + T, zb + T + 0.012, mat, g)

    # 侧向场坪：不切断 48 m 大路面，只在两侧加深一档
    pad("sd_apron_w", -4.4, 4.5, -36.0, -24.5, m["road"])
    pad("sd_apron_e", -4.4, 4.5, 24.5, 36.0, m["road"])
    # 东侧碎石堆场
    pad("sd_yard_e", 8.0, 21.0, 19.0, 33.0, m["garden_gravel"])
    # 西侧泊车带 + 车位线
    pad("sd_park_w", 8.0, 21.0, -33.0, -19.0, m["apron"])
    for k in range(6):
        vv = -32.0 + k * 2.36
        line("sd_stall_%d" % k, 8.6, 13.4, vv - 0.07, vv + 0.07, m["yellow"])
    # 草缘（打断米色场地的连续性）
    pad("sd_verge_e", 6.0, 68.0, 33.6, 36.6, m["garden_grass"])
    pad("sd_verge_w", 6.0, 68.0, -36.6, -33.6, m["garden_grass"])
    # 管廊（东侧，跨在碎石场外沿）
    for k, tt in enumerate(range(10, 55, 6)):
        avr("sd_rack_post_%d" % k, tt - 0.14, tt + 0.14, 29.6, 32.2, zb + T, zb + T + 2.75,
            m["metal"], g)
    avr("sd_rack_beam", 10.0, 54.0, 29.6, 32.2, zb + T + 2.55, zb + T + 2.82, m["steel"], g)
    for i, vv in enumerate((30.2, 30.8, 31.4)):
        avr("sd_rack_pipe_%d" % i, 10.0, 54.0, vv - 0.16, vv + 0.16,
            zb + T + 2.82, zb + T + 3.02, m["metal"], g)
    # 集装箱堆（2–3 层，叠层在俯视才读得出体积）
    _r = random.Random(20261108)
    for i, (tt, vv, mk, nz) in enumerate((
            (11.5, 21.0, "container_blue", 2), (13.0, 23.6, "container_olive", 1),
            (16.0, 21.0, "container_gray", 2), (17.5, 23.6, "container_blue", 1),
            (19.5, 26.0, "container_olive", 2))):
        for lv in range(nz):
            jt, jv = _r.uniform(-1.4, 1.4), _r.uniform(-1.1, 1.1)
            av_box("sd_cont_%d_%d" % (i, lv), tt + jt, vv + jv, 6.0, 2.4,
                   zb + T + lv * 2.62, zb + T + lv * 2.62 + 2.58, m[mk], g).rotation_euler[2] = (
                       AV_ROT + _r.uniform(-0.5, 0.5))
    print("DRESS_OK")


AV_HEAD = (125.0, -6.6)
AV_U = (0.342, -0.940)
AV_V = (0.940, 0.342)
AV_ROT = math.atan2(AV_U[1], AV_U[0])
AV_L1 = 138.7
AV_EDGE = 12.0
AV_OFF = 138.7


GARDEN_T0 = 22.0       # r13: garden north edge
GARDEN_T1 = 56.0       # r13: garden south edge
GARDEN_HALF = 17.0
GARDEN_Z = 4.70
GARDEN_CHAMFER = 8.0
GARDEN_ENTRY = 8.0


def av(t, off=0.0):
    return (AV_HEAD[0] + AV_U[0] * t + AV_V[0] * off,
            AV_HEAD[1] + AV_U[1] * t + AV_V[1] * off)


def av_z(t):
    """v11: one level deck at 4.70 across the fan; bridge B drops to the dock."""
    if t <= GARDEN_T1:
        return GARDEN_Z
    if t <= AV_L1:
        return GARDEN_Z - (GARDEN_Z - 3.0) * (t - GARDEN_T1) / (AV_L1 - GARDEN_T1)
    if t <= AV_L1 + 24.0:
        return 3.0 - 3.0 * (t - AV_L1) / 24.0
    return 0.0


def av_box(name, t, off, lt, lv, z0, z1, mat, c):
    x, y = av(t, off)
    return add_box_local(name, x, y, (z0 + z1) / 2.0, lt, lv, z1 - z0, mat, c, rot_z=AV_ROT)


def av_bldg(name, u0, u1, v0, v1, z0, z1, mat, c):
    """Axis-aligned box given in peninsula (u,v) coordinates."""
    return dock_box(name, (u0 + u1) / 2.0, (v0 + v1) / 2.0, u1 - u0, v1 - v0, z0, z1, mat, c)


def build_avenue(m):
    """v09 中轴大道：S1 桥段 + S2 引道 + S3 中轴路 + K01-K12 特征件。

    The avenue is the only way in and out of the island (v09 scope: outer bands
    removed), so it carries the whole landmark budget of the map."""
    c = coll("AVENUE")
    z = PLATFORM_Z

    # ---------- S1 bridge B only; t 0-40 is now land (build_forecourt, r10) ----------
    # (bridge A deck/surf removed: the island-to-garden stretch is filled ground)
    pts_b = [av(GARDEN_T1, -AV_EDGE), av(AV_L1, -AV_EDGE), av(AV_L1, AV_EDGE), av(GARDEN_T1, AV_EDGE)]
    add_prism("av_deck_b", pts_b,
              lambda i, p: (av_z(GARDEN_T1) if i in (0, 3) else 3.0) - 0.9,
              lambda i, p: av_z(GARDEN_T1) if i in (0, 3) else 3.0, m["causeway"], c)
    surf_b = [av(GARDEN_T1, -11.0), av(AV_L1, -11.0), av(AV_L1, 11.0), av(GARDEN_T1, 11.0)]
    add_prism("av_surf_b", surf_b,
              lambda i, p: av_z(GARDEN_T1) + 0.01 if i in (0, 3) else 3.01,
              lambda i, p: av_z(GARDEN_T1) + 0.045 if i in (0, 3) else 3.045, m["apron"], c)

    # ---------- S2 ramp down to the peninsula deck ----------
    ramp = [av(AV_L1, -13), av(AV_L1 + 24, -13), av(AV_L1 + 24, 13), av(AV_L1, 13)]
    add_prism("av_ramp", ramp, -0.4,
              lambda i, p: 3.0 if i in (0, 3) else 0.0, m["causeway"], c)

    # ---------- K02 bridge railing + posts, two segments only ----------
    def rail_run(t0, t1, tag):
        n = max(1, int(round((t1 - t0) / 6.0)))
        dt = (t1 - t0) / n
        for si, side in enumerate((-1, 1)):
            for k in range(n):
                tc = t0 + (k + 0.5) * dt
                base = av_z(tc)
                for bi, (dz0, dz1) in enumerate(((0.5, 0.62), (0.95, 1.07))):
                    av_box(f"k02_rail_{tag}_{si}_{k}_{bi}", tc, side * 11.55, dt - 0.2, 0.14,
                           base + dz0, base + dz1, m["white"], c)
                av_box(f"k02_post_{tag}_{si}_{k}", t0 + k * dt, side * 11.55, 0.20, 0.20,
                       base - 0.1, base + 1.1, m["metal"], c)
    rail_run(GARDEN_T1, AV_L1, "b")
    # ---------- K03 piers ----------
    for k, t in enumerate((120.0,)):
        for side in (-1, 1):
            av_box(f"k03_pier_{k}_{side}", t, side * 8.0, 1.8, 1.8, -0.4,
                   av_z(t) - 0.96, m["steel"], c)
    # ---------- bridge lamps every 15 m, alternating sides ----------
    for k, t in enumerate((128.0,)):
        side = -1 if k % 2 else 1
        base = av_z(t)
        av_box(f"av_lamp_{k}_pole", t, side * 10.7, 0.26, 0.26, base, base + 6.2, m["metal"], c)
        av_box(f"av_lamp_{k}_head", t, side * 10.7, 0.95, 0.5, base + 6.0, base + 6.3, m["emis"], c)
        av_box(f"av_lamp_{k}_arm", t, side * 10.2, 0.16, 1.3, base + 6.02, base + 6.16, m["metal"], c)

    # ---------- K10 pipe rack: two runs, vaults at the garden portals ----------
    for k, t in enumerate((12.0, 24.0, 36.0, 120.0, 132.0)):
        av_box(f"k10_post_{k}", t, -13.7, 0.42, 0.42, av_z(t) - 0.9, av_z(t) + 2.3, m["metal"], c)
    for tag, (t0, t1) in (("a", (12.0, 39.0)), ("b", (115.0, 132.0))):
        tm = (t0 + t1) / 2.0
        x, y = av(tm, -13.7)
        for i, dz in enumerate((1.25, 1.95)):
            add_cyl_h(f"k10_pipe_{tag}_{i}", x, y, av_z(tm) + dz, t1 - t0, 0.28,
                      m["metal"], c, vertices=10, rot_z=AV_ROT)
    for tag, t in (("a", 40.0), ("b", 114.0)):
        x, y = av(t, -13.7)
        add_box_local(f"k10_vault_{tag}", x, y, GARDEN_Z + 1.0, 2.2, 2.2, 2.0,
                      m["garden_stone"], c, rot_z=AV_ROT)
        av_box(f"k10_vault_hatch_{tag}", t, -13.7, 0.9, 0.9, GARDEN_Z + 2.0, GARDEN_Z + 2.08,
               m["garden_dark"], c)

    # ---------- bridge markings: two segments only ----------
    def bridge_marks(t0, t1, tag, n):
        L = t1 - t0
        for sg in range(n):
            tc = t0 + (sg + 0.5) * L / n
            zz = av_z(tc) + 0.006
            for off in (-0.34, 0.34):
                av_box(f"br_cl_{tag}_{sg}_{off}", tc, off, L / n - 0.4, 0.16, zz, zz + 0.03,
                       m["yellow"], c)
            for off in (-10.4, 10.4):
                av_box(f"br_edge_{tag}_{sg}_{off}", tc, off, L / n - 0.4, 0.20, zz, zz + 0.03,
                       m["white"], c)
        for jn in range(1, n):
            tj = t0 + jn * L / n
            zz = av_z(tj) + 0.004
            av_box(f"br_joint_{tag}_{jn}", tj, 0.0, 0.34, 21.4, zz, zz + 0.028, m["dark"], c)
    bridge_marks(GARDEN_T1, AV_L1, "b", 2)
    # deck kerbs + lamp bases (two segments)
    for off in (-11.7, 11.7):
        for tag, (t0, t1) in (("b", (GARDEN_T1, AV_L1)),):
            n = max(1, int(round((t1 - t0) / 13.87)))
            L = (t1 - t0) / n
            for sg in range(n):
                tc = t0 + (sg + 0.5) * L
                zz = av_z(tc)
                av_box(f"br_kerb_{tag}_{sg}_{off}", tc, off, L - 0.3, 0.55,
                       zz - 0.02, zz + 0.16, m["white"], c)
    for k, t_l in enumerate((128.0,)):
        side = -1 if k % 2 else 1
        av_box(f"br_lampbase_{k}", t_l, side * 10.7, 0.7, 0.7, av_z(t_l), av_z(t_l) + 0.42,
               m["platform"], c)

    # ---------- K01 gate portal at the island mouth ----------
    base = av_z(5.0)
    for off in (-12.2, 12.2):
        av_box(f"k01_post_{off}", 5.0, off, 0.7, 0.7, base, base + 7.6, m["white"], c)
        av_box(f"k01_cap_{off}", 5.0, off, 1.0, 1.0, base + 7.6, base + 8.0, m["metal"], c)
    av_box("k01_beam", 5.0, 0, 0.9, 25.3, base + 6.6, base + 7.5, m["white"], c)
    av_box("k01_sign", 5.6, 0, 0.24, 13.0, base + 4.9, base + 6.4, m["evac_blue"], c)
    for i, off in enumerate((-9.0, 9.0)):
        av_box(f"k01_lamp_{i}", 5.0, off, 0.5, 0.4, base + 6.6, base + 6.85, m["emis"], c)

    # ---------- S3 asphalt + sidewalks on the peninsula (u 24..86) ----------
    for tag, v0, v1, mat, z1 in (("road", -11.0, 11.0, m["road"], 0.022),
                                 ("walk_w", -14.0, -11.0, m["apron"], 0.14),
                                 ("walk_e", 11.0, 14.0, m["apron"], 0.14)):
        av_bldg(f"av_{tag}", 24, 86, v0, v1, 0.0, z1, mat, c)
    # plaza apron at the tip
    av_bldg("av_plaza", 86, 112, -29, 29, 0.0, 0.02, m["apron"], c)
    # ---------- road paint ----------
    u_mid, L3 = 55.0, 62.0
    for off in (-0.36, 0.36):
        av_box(f"av_cl_{off}", AV_OFF + u_mid, off, L3, 0.16, 0.02, 0.05, m["yellow"], c)
    for off in (-9.6, 9.6):
        av_box(f"av_edge_{off}", AV_OFF + u_mid, off, L3, 0.22, 0.02, 0.05, m["white"], c)
    for off in (-11.3, 11.3):
        av_box(f"av_curb_{off}", AV_OFF + u_mid, off, L3, 0.6, 0.0, 0.42, m["white"], c)
    # zebra at the checkpoint: bars run across the roadway
    for i in range(12):
        av_box(f"av_zebra_{i}", AV_OFF + 33.0, -9.4 + i * 1.7, 4.0, 0.55, 0.02, 0.055,
               m["white"], c)

    # ---------- K04 checkpoint (gatehouse + boom barrier) ----------
    av_box("k04_hut", AV_OFF + 33.0, 14.6, 3.6, 3.6, 0.0, 3.1, m["white"], c)
    av_box("k04_hut_roof", AV_OFF + 33.0, 14.6, 4.2, 4.2, 3.1, 3.45, m["dark"], c)
    av_box("k04_hut_win", AV_OFF + 33.0, 12.75, 2.6, 0.2, 1.3, 2.5, m["glass"], c)
    av_box("k04_pivot", AV_OFF + 33.0, 11.0, 0.55, 0.55, 0.0, 1.35, m["metal"], c)
    av_box("k04_base", AV_OFF + 33.0, 5.6, 0.42, 10.6, 0.98, 1.18, m["yellow"], c)
    for i in range(6):
        av_box(f"k04_stripe_{i}", AV_OFF + 33.0, 1.1 + i * 1.7, 0.44, 0.85, 0.99, 1.17,
               m["dark"], c)

    # ---------- K05 warehouse, west of the road (roll doors face the avenue) ----------
    av_bldg("k05_body", 32, 70, -30, -14, 0.0, 9.0, m["dock"], c)
    av_bldg("k05_roof", 31.4, 70.6, -30.6, -13.4, 9.0, 9.45, m["steel"], c)
    for i, u in enumerate((36, 45, 54, 63)):
        av_bldg(f"k05_door_{i}", u, u + 6.6, -14.3, -13.9, 0.0, 4.6, m["metal"], c)
        av_bldg(f"k05_canopy_{i}", u - 0.6, u + 7.2, -13.9, -12.0, 4.6, 4.85, m["evac_blue"], c)
        dock_win(f"k05_win_{i}", u + 1.0, u + 5.6, 6.0, 7.4, -14.0, 1, m, c, mullions=2)
        av_bldg(f"k05_sill_{i}", u + 0.6, u + 6.0, -13.88, -13.66, 5.78, 5.96, m["white"], c)
        for k, uu in enumerate((u - 0.22, u + 6.6)):
            av_bldg(f"k05_jamb_{i}_{k}", uu, uu + 0.22, -14.04, -13.62, 0.0, 4.62,
                    m["white"], c)
        av_bldg(f"k05_head_{i}", u - 0.22, u + 6.82, -14.04, -13.62, 4.62, 4.84,
                m["white"], c)
        for j, zz in enumerate((0.95, 1.75, 2.55, 3.35, 4.15)):
            av_bldg(f"k05_slat_{i}_{j}", u + 0.05, u + 6.55, -13.90, -13.84, zz, zz + 0.07,
                    m["dark"], c)
    for i, u in enumerate((34, 48, 62)):
        av_bldg(f"k05_vent_{i}", u, u + 2.2, -26, -23, 9.45, 10.4, m["steel"], c)
    # fascia + pilasters so the long wall reads as a building, not a slab
    av_bldg("k05_fascia", 32, 70, -14.3, -13.8, 4.9, 6.0, m["white"], c)
    av_bldg("k05_plinth", 32, 70, -14.32, -13.82, 0.0, 0.55, m["dark"], c)
    for i, u in enumerate((32, 44.5, 57, 69.5)):
        av_bldg(f"k05_pilaster_{i}", u, u + 1.0, -14.4, -13.4, 0.0, 9.0, m["white"], c)
    av_bldg("k05_parapet", 32, 70, -14.5, -13.6, 9.0, 10.0, m["white"], c)

    # ---------- K06 tank farm: v13 R1/R4, 2x5 grid -> 3+2 staggered cluster ----------
    _r06 = random.Random(20261108)
    for k, (u, v) in enumerate(((58.0, 19.5), (64.4, 20.6), (71.2, 19.1),
                                (60.8, 26.4), (68.6, 25.8))):
        x, y = dock_world(u + _r06.uniform(-0.6, 0.6), v)
        add_cyl(f"k06_tank_{k}", x, y, 0.0, 8.4, 2.6, m["white"], c, vertices=18)
        add_cyl(f"k06_cap_{k}", x, y, 8.4, 8.85, 2.75, m["steel"], c, vertices=18)
        add_cyl(f"k06_band_{k}", x, y, 5.2, 5.6, 2.68, m["evac_blue"], c, vertices=18)
    x, y = dock_world(74, 26)
    add_cyl_h("k06_manifold", x, y, 1.2, 22.0, 0.34, m["steel"], c,
              vertices=12, rot_z=DOCK_ROTZ)

    # ---------- K07 sawtooth workshop, west side past the warehouse ----------
    av_bldg("k07_body", 74, 108, -30, -14, 0.0, 10.0, m["dock"], c)
    av_bldg("k07_roofslab", 73.6, 108.4, -30.4, -13.6, 11.8, 12.15, m["steel"], c)
    av_bldg("k07_parapet_n", 73.6, 108.4, -14.1, -13.5, 12.15, 12.7, m["white"], c)
    av_bldg("k07_plinth", 74, 108, -14.02, -13.62, 0.0, 0.55, m["dark"], c)
    for i in range(5):
        u = 74 + i * 6.9
        av_bldg(f"k07_tooth_{i}", u, u + 6.6, -30, -14.5, 10.0, 11.8, m["steel"], c)
        dock_win(f"k07_glass_{i}", u + 0.4, u + 6.2, 6.6, 9.4, -14.0, 1, m, c, mullions=3)
        av_bldg(f"k07_door_{i}", u + 1.4, u + 5.2, -14.0, -13.62, 0.0, 4.4, m["dark"], c)
        for k, uu in enumerate((u + 1.18, u + 5.2)):
            av_bldg(f"k07_jamb_{i}_{k}", uu, uu + 0.22, -14.02, -13.58, 0.0, 4.42,
                    m["white"], c)
        av_bldg(f"k07_head_{i}", u + 1.18, u + 5.42, -14.02, -13.58, 4.42, 4.62,
                m["white"], c)
        av_bldg(f"k07_canopy_{i}", u + 0.9, u + 5.7, -13.6, -12.15, 4.62, 4.86,
                m["steel"], c)
        for j, zz in enumerate((0.9, 1.6, 2.3, 3.0, 3.7)):
            av_bldg(f"k07_slat_{i}_{j}", u + 1.45, u + 5.15, -13.62, -13.57, zz, zz + 0.06,
                    m["metal"], c)
        for k, uu in enumerate((u + 0.95, u + 5.45)):
            av_bldg(f"k07_wlamp_{i}_{k}", uu, uu + 0.24, -13.64, -13.52, 3.48, 3.72,
                    m["emis"], c)
        av_bldg(f"k07_strip_{i}", u + 0.4, u + 6.2, -14.0, -13.62, 10.6, 11.2, m["white"], c)
    for k, u in enumerate((74.7, 88.0, 101.3, 107.4)):
        x, y = dock_world(u, -13.5)
        add_cyl(f"k07_pipe_{k}", x, y, 0.0, 11.6, 0.09, m["metal"], c, vertices=8)

    # ---------- K14 admin block, east kerb (street wall on the other side) ----------
    av_bldg("k14_body", 40, 58, 14, 30, 0.0, 13.0, m["wall"], c)
    av_bldg("k14_parapet", 39.6, 58.4, 13.6, 30.4, 13.0, 13.9, m["white"], c)
    av_bldg("k14_plinth", 40, 58, 13.85, 14.2, 0.0, 1.1, m["dark"], c)
    for f in range(3):
        zz = 3.4 + f * 3.4
        for k in range(5):
            dock_win(f"k14_win_{f}_{k}", 42 + k * 3.2, 44.4 + k * 3.2, zz, zz + 1.9,
                     14.0, -1, m, c, mullions=1)
        av_bldg(f"k14_band_{f}", 40, 58, 13.85, 14.25, zz - 0.45, zz - 0.15, m["white"], c)
    av_bldg("k14_entry", 46.6, 51.4, 13.8, 14.4, 0.0, 3.0, m["glass"], c)
    av_bldg("k14_canopy", 46.0, 52.0, 13.2, 14.6, 3.0, 3.35, m["evac_blue"], c)
    av_bldg("k14_roofbox", 44, 50, 18, 26, 13.9, 15.3, m["steel"], c)
    for i, u in enumerate((41.5, 53.0)):
        av_bldg(f"k14_door_{i}", u, u + 2.4, 13.75, 14.3, 0.0, 2.9, m["metal"], c)
        av_bldg(f"k14_doorframe_{i}", u - 0.25, u + 2.65, 13.7, 14.35, 2.9, 3.1,
                m["white"], c)
    av_bldg("k14_shop", 44.0, 46.0, 13.8, 14.25, 0.4, 2.9, m["glass"], c)
    av_bldg("k14_shop2", 55.0, 57.0, 13.8, 14.25, 0.4, 2.9, m["glass"], c)

    # ---------- K13 workshop block, east side before the container wall ----------
    av_bldg("k13_body", 22, 38, 14, 28, 0.0, 6.4, m["dock"], c)
    av_bldg("k13_roof", 21.6, 38.4, 13.7, 28.4, 6.4, 6.8, m["steel"], c)
    for i, u in enumerate((23, 28.5, 34)):
        av_bldg(f"k13_door_{i}", u, u + 4.4, 13.7, 14.1, 0.0, 3.8, m["metal"], c)
        dock_win(f"k13_win_{i}", u + 0.4, u + 4.0, 4.6, 5.8, 14.0, -1, m, c, mullions=2)
    av_bldg("k13_parapet", 22, 38, 13.6, 14.3, 6.4, 7.2, m["white"], c)
    av_bldg("k13_gable", 21.7, 22.2, 14, 28, 0.0, 6.4, m["white"], c)
    for i in range(2):
        av_bldg(f"k13_gband_{i}", 21.6, 21.8, 14.6, 27.4, 2.2 + i * 2.4, 2.5 + i * 2.4,
                m["dark"], c)

    # ---------- K08 container yard, east past the tank farm ----------
    cmats = [m["container_blue"], m["container_olive"], m["container_gray"]]
    for i in range(6):
        row, col = i // 3, i % 3
        av_bldg(f"k08_c_{i}", 88 + col * 6.2, 88 + col * 6.2 + 5.9,
                19.0 + row * 2.9, 19.0 + row * 2.9 + 2.5, 0.0, 2.6, cmats[i % 3], c)

    # ---------- K09 lamp columns along the peninsula road ----------
    for k, u in enumerate(range(28, 84, 14)):
        side = -1 if k % 2 else 1
        x, y = av(AV_OFF + u, side * 11.9)
        add_cyl(f"k09_pole_{k}", x, y, 0.0, 7.2, 0.16, m["metal"], c, vertices=10)
        av_box(f"k09_arm_{k}", AV_OFF + u, side * 10.9, 0.16, 2.2, 7.05, 7.2, m["metal"], c)
        av_box(f"k09_head_{k}", AV_OFF + u, side * 9.9, 0.95, 0.55, 6.95, 7.2, m["emis"], c)

    # ---------- K11 evacuation plaza at the tip ----------
    # deck edge paint (yellow) around u 86..112
    for v in (-29.0, 29.0):
        av_bldg(f"k11_border_v{v}", 86, 112, v - 0.2, v + 0.2, 0.02, 0.055, m["yellow"], c)
    for u in (86.0, 112.0):
        for (v0, v1) in ((-29.0, -11.5), (11.5, 29.0)):
            av_bldg(f"k11_border_u{u}_{v0}", u - 0.2, u + 0.2, v0, v1, 0.02, 0.055,
                    m["yellow"], c)
    # floodlight masts
    for i, (u, v) in enumerate(((88, -26), (88, 26), (104, -24), (104, 24))):
        x, y = dock_world(u, v)
        add_cyl(f"k11_mast_{i}", x, y, 0.0, 9.0, 0.24, m["metal"], c, vertices=10)
        av_box(f"k11_head_{i}", AV_OFF + u, v, 1.3, 0.9, 8.85, 9.25, m["emis"], c)
    # windsock at the tip
    x, y = dock_world(108, -12)
    add_cyl("k11_sock_pole", x, y, 0.0, 6.2, 0.16, m["metal"], c, vertices=8)
    x, y = dock_world(108, -14.4)
    px, py = dock_world(108, -12)
    ax_, ay_ = dock_world(108, -13.2)
    arm = add_cyl("k11_sock_arm", (px + ax_) / 2.0, (py + ay_) / 2.0, 5.72, 5.88, 0.07,
                  m["metal"], c, axis="X", vertices=8)
    arm.rotation_euler[2] = DOCK_ROTZ
    sock = add_cyl("k11_sock", x, y, 5.5, 6.0, 0.62, m["orange"], c, axis="X", vertices=10)
    sock.rotation_euler[2] = DOCK_ROTZ
    # v13 REQ-41: helipad H-ring removed (real test workshop has no helipad).
    # Replaced by a one-sided equipment cluster (R2/R4: no mirroring, no grid).
    _r13 = random.Random(20261108)
    for i, (uu, vv, rr) in enumerate(((101.0, -3.0, 2.6), (106.5, 1.8, 2.2),
                                      (96.0, 4.6, 2.4))):
        tx, ty = dock_world(uu, vv)
        add_cyl("k11_silo_%d" % i, tx, ty, 0.0, 8.4 + _r13.uniform(-0.8, 0.8),
                rr, m["white"], c, vertices=18)
        add_cyl("k11_silo_cap_%d" % i, tx, ty, 8.4, 8.85, rr + 0.15,
                m["steel"], c, vertices=18)

    # ---------- K12 vehicles ----------
    av_box("k12_forklift_body", AV_OFF + 44, 12.6, 2.8, 1.5, 0.0, 1.7, m["yellow"], c)
    av_box("k12_forklift_cab", AV_OFF + 44, 12.6, 1.2, 1.5, 1.7, 2.5, m["dark"], c)
    av_box("k12_forklift_mast", AV_OFF + 42.4, 12.6, 0.22, 1.3, 0.0, 2.9, m["metal"], c)
    av_box("k12_pickup_body", AV_OFF + 58, -12.7, 5.0, 2.0, 0.0, 1.25, m["container_olive"], c)
    av_box("k12_pickup_cab", AV_OFF + 56.9, -12.7, 2.0, 1.9, 1.25, 1.9, m["container_olive"], c)
    av_box("k12_pickup_bed", AV_OFF + 61.0, -12.7, 2.0, 1.9, 1.25, 1.5, m["dark"], c)

    # ---------- quay aprons that carry the roadside buildings ----------
    # quays taper: the map window ends at x=240 / y=-254, so both aprons stop short
    av_bldg("quay_w", 16, 104, -48, -30, -0.5, 0.0, m["platform"], c)
    av_bldg("quay_w_edge", 16, 104, -48.4, -47.6, 0.0, 0.3, m["white"], c)
    av_bldg("quay_e", 16, 88, 30, 36, -0.5, 0.0, m["platform"], c)
    av_bldg("quay_e_edge", 16, 88, 35.6, 36.4, 0.0, 0.3, m["white"], c)


# ------------------------------------------------------------------ v10 garden
# ------------------------------------------------------------------ r10 forecourt
FILL_POLY = [(74.0, -13.4), (166.0, -13.4), (178.2, -29.8), (99.2, -58.6)]


def build_forecourt(m):
    """One wide apron (garden centred) + parking / yard band down to the bridge."""
    c = coll("FORECOURT")
    z = PLATFORM_Z
    # apron t 4..74, v +-65
    avr("fc_apron", 5.0, 70.0, -37.0, 37.0, z + 0.02, z + 0.05, m["garden_walk"], c)
    for sgn in (-1, 1):
        avr(f"fc_apron_edge{sgn}", 5.0, 70.0, sgn * 37.0, sgn * 37.6, z + 0.02, z + 0.09,
            m["garden_border"], c)
    for k in range(6):
        av_box(f"fc_ap_j{k}", 10.0 + k * 11.0, 0, 0.05, 72.0, z + 0.05, z + 0.062,
               m["garden_border"], c)

    # parking band t 74..114: 2 rows x 9 on the west, yard on the east
    avr("fc_park_apron", 70.0, 104.0, -29.0, -4.0, z + 0.015, z + 0.035, m["road"], c)
    for row, vv in enumerate((-24.0, -12.0)):
        for k in range(9):
            tt = 74.0 + k * 3.2
            av_box(f"fc_bay_{row}_{k}", tt, vv, 3.0, 5.2, z + 0.02, z + 0.05,
                   m["garden_border"], c)
        av_box(f"fc_row{row}", 88.8, vv, 28.8, 0.16, z + 0.05, z + 0.08, m["white"], c)
    avr("fc_yard", 70.0, 104.0, 5.0, 29.0, z + 0.015, z + 0.035, m["garden_walk"], c)
    for k in range(3):
        av_box(f"fc_ctn{k}", 80.0 + k * 7.0, 22.0, 6.1, 2.44, z, z + 2.6, m["container_blue"], c)
        av_box(f"fc_ctn2_{k}", 80.0 + k * 7.0, 18.6, 6.1, 2.44, z, z + 2.6,
               m["container_olive"], c)
    for k in range(4):
        av_box(f"fc_crate_{k}", 76.0 + (k % 2) * 3.2, 8.0 + (k // 2) * 3.4, 2.8, 2.8,
               z, z + 1.1 + 0.2 * (k % 3), m["wood"], c)
    # palms along the apron edges + lamps
    for i, (x, y) in enumerate(PALMS):
        add_cyl(f"palm_trunk_{i}", x, y, z, z + 7.0, 0.30, m["wood"], c, vertices=8)
    for k, tt in enumerate((12.0, 32.0, 52.0, 66.0)):
        for sgn in (-1, 1):
            x, y = av(tt, sgn * 34.0)
            add_cyl(f"fc_lamp_{k}_{sgn}", x, y, z, z + 5.6, 0.11, m["garden_dark"], c, vertices=8)
            add_box_local(f"fc_lamp_h_{k}_{sgn}", x, y, z + 5.6, 0.7, 0.4, 0.2, m["emis"], c,
                          rot_z=AV_ROT)
    print("FORECOURT_OK")


GARDEN_PALMS = [(28.0, -9.0), (28.0, 9.0), (33.0, -9.0), (33.0, 9.0),
                (47.0, -9.0), (47.0, 9.0), (52.0, -9.0), (52.0, 9.0)]


def build_garden(m):
    """v12: the garden shrinks to one core module (34 x 34) -- a walled parterre."""
    c = coll("GARDEN")
    z = GARDEN_Z
    T0, T1, H = GARDEN_T0, GARDEN_T1, 17.0
    tc = (T0 + T1) / 2.0

    av_box("garden_platform", tc, 0, T1 - T0, 2 * H, z, z + 0.05, m["garden_stone"], c)
    av_box("garden_deck", tc, 0, T1 - T0 - 1.2, 2 * H - 1.2, z + 0.05, z + 0.06,
           m["garden_walk"], c)

    for tag, (t0, t1, v0, v1) in {
            "w": (T0, T1, -H, -H + 0.4), "e": (T0, T1, H - 0.4, H),
            "s": (T1 - 0.4, T1, -H, H)}.items():
        av_box(f"gw_{tag}_wall", (t0 + t1) / 2.0, (v0 + v1) / 2.0, t1 - t0, v1 - v0,
               z, z + 0.92, m["garden_wall"], c)
        av_box(f"gw_{tag}_band", (t0 + t1) / 2.0, (v0 + v1) / 2.0, t1 - t0 + 0.04,
               v1 - v0 + 0.04, z + 0.52, z + 0.70, m["garden_orange"], c)
        av_box(f"gw_{tag}_cope", (t0 + t1) / 2.0, (v0 + v1) / 2.0, t1 - t0 + 0.16,
               v1 - v0 + 0.16, z + 0.92, z + 1.04, m["garden_coping"], c)

    for side in (-1, 1):
        av_box(f"ggate_post_{side}", T0, side * 6.6, 0.7, 0.7, z, z + 4.6, m["white"], c)
        av_box(f"ggate_cap_{side}", T0, side * 6.6, 1.0, 1.0, z + 4.6, z + 4.85, m["metal"], c)
    av_box("ggate_beam", T0, 0, 0.9, 14.6, z + 3.9, z + 4.6, m["white"], c)
    for k, vv in enumerate((-3.2, 3.2)):
        av_box(f"gsign_{k}", T0 - 0.5, vv, 0.24, 3.4, z + 2.9, z + 3.7, m["evac_blue"], c)

    av_box("gpool_basin", tc, 0, 12.0, 12.0, z - 0.42, z - 0.10, m["garden_pool"], c)
    av_box("gpool_water", tc, 0, 11.6, 11.6, z - 0.10, z - 0.085, m["pool"], c)
    for tag, (dt, dv) in {"n": (-6.3, 0), "s": (6.3, 0), "w": (0, -6.3), "e": (0, 6.3)}.items():
        lt = 0.6 if dv == 0 else 13.2
        lv = 13.2 if dv == 0 else 0.6
        av_box(f"gpool_cope_{tag}", tc + dt, dv, lt, lv, z - 0.02, z + 0.10,
               m["garden_coping"], c)
    cx_, cy_ = av(tc, 0)
    add_cyl("gpool_jet", cx_, cy_, z - 0.08, z + 0.55, 0.35, m["teal"], c, vertices=12)

    for i, (t0, v0) in enumerate(((64.5, -15.0), (64.5, 9.0), (87.5, -15.0), (87.5, 9.0))):
        av_box(f"gbed_curb_{i}", t0 + 3.0, v0 + 3.0, 6.0, 6.0, z + 0.06, z + 0.30,
               m["garden_border"], c)
        av_box(f"gbed_soil_{i}", t0 + 3.0, v0 + 3.0, 5.2, 5.2, z + 0.30, z + 0.36,
               m["garden_grass"], c)
        av_box(f"gedge_{i}", t0 + 3.0, v0 + 3.0, 5.6, 5.6, z + 0.36, z + 0.78,
               m["garden_hedge"], c)
    for k, v0 in enumerate((-15.0, 9.0)):
        av_box(f"gpar_base_{k}", tc, v0 + 3.0, 9.0, 6.0, z + 0.06, z + 0.16,
               m["garden_gravel"], c)
        for j, tt in enumerate((tc - 3.0, tc, tc + 3.0)):
            av_box(f"gpar_h_{k}_{j}", tt, v0 + 3.0, 0.5, 5.0, z + 0.16, z + 0.55,
                   m["garden_hedge"], c)

    av_box("goverlook_paving", 90.0, 0, 6.0, 10.0, z + 0.06, z + 0.10, m["garden_gravel"], c)
    for k in range(6):
        av_box(f"gperg_slat_{k}", 93.5, 0, 0.35, 10.0, z + 2.6 + k * 0.06,
               z + 2.72 + k * 0.06, m["wood"], c)
    for side in (-1, 1):
        av_box(f"gperg_post_{side}", 93.5, side * 4.8, 0.28, 0.28, z, z + 2.6, m["wood"], c)

    for k, (tt, vv) in enumerate(((64.0, -15.6), (64.0, 15.6), (78.0, -15.6), (78.0, 15.6),
                                  (86.0, -15.6), (86.0, 15.6), (95.0, -6.0), (95.0, 6.0))):
        x, y = av(tt, vv)
        add_cyl(f"glamp_p_{k}", x, y, z, z + 3.2, 0.10, m["garden_dark"], c, vertices=8)
        add_box_local(f"glamp_h_{k}", x, y, z + 3.2, 0.5, 0.3, 0.18, m["emis"], c, rot_z=AV_ROT)
    for k, vv in enumerate((-13.0, -10.6)):
        av_box(f"gsvc_ct_{k}", 94.2, vv, 1.4, 1.2, z + 0.06, z + 1.1, m["container_gray"], c)

    for i, (tt, vv) in enumerate(GARDEN_PALMS):
        x, y = av(tt, vv)
        add_cyl(f"gpalm_t_{i}", x, y, z, z + 6.2, 0.26, m["wood"], c, vertices=8)

    for k in range(1, 6):
        av_box(f"gj_{k}", T0 + k * 5.6, 0, 0.04, 2 * H - 1.2, z + 0.06, z + 0.068,
               m["garden_border"], c)
    print("GARDEN_COMPACT_OK")


def build_street_kit(m):
    """A-tier dress-up: the small human-scale props that make the avenue read as
    a street rather than a slab (F6 wall-footage kit + roadside furniture)."""
    c = coll("STREET")
    z = 0.0

    def at(u, v, height=0.0):
        return dock_world(u, v)

    # 1. bollards along both kerbs
    for side in (-1, 1):
        for k, u in enumerate(range(26, 84, 8)):
            x, y = at(u, side * 12.2)
            add_cyl(f"st_boll_{side}_{k}", x, y, z, z + 0.85, 0.14, m["dark"], c, vertices=8)
            add_cyl(f"st_bollc_{side}_{k}", x, y, z + 0.85, z + 0.92, 0.16, m["yellow"], c,
                    vertices=8)
    # 2. guardrail bays in front of the warehouse apron
    for k, u in enumerate((36, 42, 48)):
        for side in (-1,):
            x, y = at(u, side * 12.4)
            add_box_local(f"st_gr_{k}", x, y, z + 0.55, 5.6, 0.12, 0.26, m["white"], c,
                          rot_z=DOCK_ROTZ)
            add_box_local(f"st_gr_b_{k}", x, y, z + 0.32, 5.6, 0.1, 0.1, m["white"], c,
                          rot_z=DOCK_ROTZ)
    # 3. planters + foliage in front of the workshop block
    for k, (u, v) in enumerate(((24, 12.6), (29, 12.6), (34, 12.6), (66, 12.6), (72, 12.6))):
        x, y = at(u, v)
        add_box_local(f"st_planter_{k}", x, y, z + 0.35, 2.2, 1.1, 0.7, m["white"], c,
                      rot_z=DOCK_ROTZ)
        add_box_local(f"st_pl_soil_{k}", x, y, z + 0.72, 1.9, 0.85, 0.06, m["dark"], c,
                      rot_z=DOCK_ROTZ)
        for j in range(2):
            add_box_local(f"st_pl_bush_{k}_{j}", x, y, z + 1.15, 1.7, 0.8, 0.85,
                          m["foliage"], c, rot_z=DOCK_ROTZ + j * 1.1)
    # 4. cable reels by the warehouse doors
    for k, (u, v, rr) in enumerate(((37, -15.6, 1.1), (39, -15.6, 0.9), (55, -15.4, 1.0))):
        x, y = at(u, v)
        add_cyl(f"st_reel_{k}", x, y, z, z + rr * 1.1, rr, m["wood"], c, axis="Y",
                vertices=16)
    # 5. drums + jerry cans
    for k, (u, v) in enumerate(((46, 13.0), (46.8, 13.7), (47.6, 13.0), (67, -15.2),
                                (68.2, -15.2))):
        x, y = at(u, v)
        add_cyl(f"st_drum_{k}", x, y, z, z + 0.9, 0.32, m["orange"] if k % 2 else m["bluebox"],
                c, vertices=10)
    # 6. pallets + crate stacks at the loading bays
    for k, (u, v, h) in enumerate(((44, -13.0, 1.2), (45.4, -13.0, 0.9), (60, -13.2, 1.5),
                                   (61.4, -13.2, 1.1))):
        x, y = at(u, v)
        add_box_local(f"st_pal_{k}", x, y, z + 0.07, 1.4, 1.1, 0.14, m["wood"], c,
                      rot_z=DOCK_ROTZ)
        add_box_local(f"st_crate_{k}", x, y, z + h / 2 + 0.14, 1.25, 0.95, h, m["caramel"], c,
                      rot_z=DOCK_ROTZ)
    # 7. utility poles + catenary cable along the east kerb
    for k, u in enumerate(range(30, 82, 26)):
        x, y = at(u, 13.4)
        add_cyl(f"st_pole_{k}", x, y, z, z + 8.2, 0.16, m["metal"], c, vertices=8)
        add_box_local(f"st_pole_arm_{k}", x, y, z + 7.9, 0.12, 2.2, 0.12, m["metal"], c,
                      rot_z=DOCK_ROTZ)
    for k in range(2):
        x, y = at(30 + k * 26 + 13, 13.4)
        add_box_local(f"st_wire_{k}", x, y, z + 7.75, 26.0, 0.035, 0.035, m["char_dark"], c,
                      rot_z=DOCK_ROTZ)
    # 8. signage boards on posts
    for k, (u, v, ang) in enumerate(((31, -13.0, 0.0), (56, 13.0, 3.14), (80, -13.0, 0.0))):
        x, y = at(u, v)
        add_cyl(f"st_sign_post_{k}", x, y, z, z + 2.4, 0.09, m["metal"], c, vertices=6)
        add_box_local(f"st_sign_{k}", x, y, z + 2.15, 1.5, 0.08, 0.95, m["white"], c,
                      rot_z=DOCK_ROTZ + ang)
        add_box_local(f"st_sign_txt_{k}", x, y, z + 2.15, 1.15, 0.1, 0.2, m["yellow"], c,
                      rot_z=DOCK_ROTZ + ang)
    # 9. fire hydrants / standpipes
    for k, u in enumerate((40, 64)):
        x, y = at(u, 12.0)
        add_cyl(f"st_hyd_{k}", x, y, z, z + 0.75, 0.13, m["orange"], c, vertices=8)
    # 10. west quay working yard: pipe stacks, pallet stacks, containers
    for k, (u, v) in enumerate(((22, -34), (30, -34), (22, -38), (30, -38))):
        x, y = at(u, v)
        add_cyl_h(f"st_qpipe_{k}", x, y, 0.55 + (k % 2) * 0.62, 7.0, 0.32, m["steel"], c,
                  vertices=10, rot_z=DOCK_ROTZ)
    for k, (u, v) in enumerate(((40, -33), (44, -33), (40, -37), (44, -37), (48, -33))):
        x, y = at(u, v)
        add_box_local(f"st_qpal_{k}", x, y, 0.07, 2.6, 2.2, 0.14, m["wood"], c, rot_z=DOCK_ROTZ)
        add_box_local(f"st_qbox_{k}", x, y, 0.75, 2.4, 2.0, 1.2, m["caramel"], c, rot_z=DOCK_ROTZ)
    for k, (u, v, mat) in enumerate(((62, -35, m["container_blue"]), (62, -39, m["container_olive"]),
                                     (70, -35, m["container_gray"]))):
        x, y = at(u, v)
        add_box_local(f"st_qcont_{k}", x, y, 1.3, 6.0, 2.4, 2.6, mat, c, rot_z=DOCK_ROTZ)
    for k, u in enumerate((24, 56, 88)):
        x, y = at(u, -45.5)
        add_cyl(f"st_qpole_{k}", x, y, 0.0, 8.0, 0.16, m["metal"], c, vertices=8)
        add_box_local(f"st_qhead_{k}", x, y, 7.85, 1.0, 0.5, 0.3, m["emis"], c,
                      rot_z=DOCK_ROTZ)
    # 11. kerbside cones (kept from the old dock kit)
    for k, (u, v) in enumerate(((50, -11.6), (51.4, -11.6), (73, 11.6), (74.4, 11.6))):
        x, y = at(u, v)
        add_cyl(f"st_cone_{k}", x, y, z, z + 0.62, 0.24, m["orange"], c, vertices=8)
        add_cyl(f"st_cone_b_{k}", x, y, z, z + 0.16, 0.30, m["dark"], c, vertices=8)


def build_horizon(m):
    """Distant silhouettes so eye-level shots do not end in a flat sea line."""
    c = coll("HORIZON")
    cols = ("#AEBFC2", "#C2D0D2", "#D3DDDC")
    for i, (dist, hgt, wid) in enumerate(((860.0, 11.0, 1100.0), (1120.0, 17.0, 1400.0),
                                          (1450.0, 26.0, 1700.0))):
        mat = make_mat(f"v9.horizon{i}", cols[i], 0.97)
        cx, cy = av(AV_OFF + 120.0 + dist, 0.0)
        pts = []
        n = 14
        for k in range(n + 1):
            t2 = -wid / 2 + wid * k / n
            h = hgt * (0.45 + 0.55 * abs(math.sin(k * 1.3 + i * 1.7)))
            x, y = av(AV_OFF + 120.0 + dist, t2)
            pts.append((x, y, h))
        pxv, pyv = AV_V
        verts = [(p[0], p[1], -2) for p in pts] + [(p[0], p[1], p[2]) for p in pts]
        faces = [(k, k + 1, n + 1 + k + 1, n + 1 + k) for k in range(n)]
        mesh = bpy.data.meshes.new(f"horizon_{i}")
        mesh.from_pydata(verts, [], faces)
        mesh.validate()
        mesh.update()
        _mesh_obj(f"horizon_{i}", mesh, mat, c)
        # a few cranes / stacks on the nearest ridge
        if i == 0:
            for k in range(6):
                x, y = av(AV_OFF + 120.0 + dist - 6, -wid / 2 + 40 + k * 82)
                add_box_local(f"hz_crane_{k}", x, y, hgt * 0.65, 4.0, 4.0, hgt * 1.3,
                              mat, c, rot_z=AV_ROT)


def purge_workshop_intruders():
    """v13 N6 / hypothesis H1.

    Phenomenon: v13 quick master showed the south yard cut in half by a wide
    pale band, a roofed warehouse on the west and a parapet block on the east.
    Root cause: build_avenue + build_forecourt + build_street_kit + K01-K14
    were authored for the v07 "approach road + dock" and place 489 meshes in
    the very same dock rectangle (u 0..96 / v -30..+30) as the new workshop.
    Source-level change: the south peninsula belongs exclusively to the
    workshop; remove every non-ws mesh whose world bounding-box centre falls
    inside it. The bridge B (u < 0) and the main site (u < -34) stay intact.
    Expected: enclosed folded-wall yard becomes readable, no roof objects.
    Rerun: TV13-01/02/03/07.
    """
    from mathutils import Vector
    U, Vv, O = DOCK_U, DOCK_V, DOCK_O
    keep = ("ws_", "water", "HeroFog", "low_terrace", "riprap_", "scale_")
    removed = []
    for ob in list(bpy.data.objects):
        if ob.type != "MESH" or ob.name.startswith(keep):
            continue
        c = ob.matrix_world @ (sum((Vector(v) for v in ob.bound_box), Vector()) / 8.0)
        dx, dy = c.x - O[0], c.y - O[1]
        u = dx * U[0] + dy * U[1]
        v = dx * Vv[0] + dy * Vv[1]
        # H2: v07 quay_w / st_q* sat at v -34..-48, outside the first pass.
        if -0.5 <= u <= 125.0 and -50.0 <= v <= 50.0:
            removed.append(ob.name)
            bpy.data.objects.remove(ob, do_unlink=True)
    print("PURGE_INTRUDERS", len(removed))


def build_test_workshop(m):
    """v13 (design r15): open-air horizontal test workshop / blast-wall yard.

    Real-game identity combination (MASTER_SPEC 8.4.6, A grade):
      9 m concrete blast walls (folded, stained) + scattered containers +
      ground-level pipe group + teal ENTRANCE gateway + yellow lane lines +
      diversion pit + yellow evac frame + wall-mounted green terminal.
    No roof, no truss, no gantry crane. dock u 0..96 / v -30..+30.
    """
    c = coll("TEST_WORKSHOP")
    rnd = random.Random(20261108)
    WH, WT = 9.0, 1.2

    # ---- S-01 folded blast walls (different offsets on each side: R2) ----
    west = [(2, 18, -28.6), (18, 34, -28.6), (34, 50, -27.4),
            (50, 66, -27.4), (66, 80, -29.0), (80, 94, -29.0)]
    east = [(2, 20, 28.2), (20, 38, 28.2), (38, 52, 29.4),
            (52, 72, 29.4), (72, 94, 27.8)]
    def wseg(tag, u0, u1, v, idx):
        dock_box("ws_wall_%s_%d" % (tag, idx), (u0 + u1) / 2.0, v, u1 - u0, WT,
                 0.0, WH, m["ws_concrete"], c)
        dock_box("ws_coping_%s_%d" % (tag, idx), (u0 + u1) / 2.0, v, u1 - u0 + 0.2,
                 WT + 0.3, WH, WH + 0.25, m["ws_coping"], c)
        # 6 m vertical panel joints
        k = 0
        uu = u0 + 6.0
        while uu < u1 - 1.0:
            dock_box("ws_joint_%s_%d_%d" % (tag, idx, k), uu, v, 0.10, WT + 0.06,
                     0.0, WH, m["dark"], c)
            uu += 6.0
            k += 1
        # wall-foot staining, 1.5 m (A-grade real-game feature, M8o override)
        inner = 0.55 if v < 0 else -0.55
        dock_box("ws_stain_%s_%d" % (tag, idx), (u0 + u1) / 2.0, v + inner,
                 u1 - u0, 0.22, 0.0, 1.5, m["ws_stain"], c)
    for i, (u0, u1, v) in enumerate(west):
        wseg("w", u0, u1, v, i)
    for i, (u0, u1, v) in enumerate(east):
        wseg("e", u0, u1, v, i)
    # south wall, split into 3 with slight offsets
    for i, (v0, v1, uu) in enumerate(((-29.0, -8.0, 94.0), (-8.0, 9.0, 93.4),
                                     (9.0, 27.8, 94.0))):
        dock_box("ws_wall_s_%d" % i, uu, (v0 + v1) / 2.0, WT, v1 - v0,
                 0.0, WH, m["ws_concrete"], c)
        dock_box("ws_coping_s_%d" % i, uu, (v0 + v1) / 2.0, WT + 0.3, v1 - v0,
                 WH, WH + 0.25, m["ws_coping"], c)
        dock_box("ws_stain_s_%d" % i, uu - 0.55, (v0 + v1) / 2.0, 0.22, v1 - v0,
                 0.0, 1.5, m["ws_stain"], c)
    # north wall with a 12 m entrance gap (v -6..+6)
    for i, (v0, v1) in enumerate(((-28.6, -6.0), (6.0, 28.2))):
        dock_box("ws_wall_n_%d" % i, 2.0, (v0 + v1) / 2.0, WT, v1 - v0,
                 0.0, WH, m["ws_concrete"], c)
        dock_box("ws_coping_n_%d" % i, 2.0, (v0 + v1) / 2.0, WT + 0.3, v1 - v0,
                 WH, WH + 0.25, m["ws_coping"], c)

    # ---- S-02 ENTRANCE gateway (teal door surround + letter band) ----
    for i, vv in enumerate((-6.4, 6.4)):
        dock_box("ws_entrance_jamb_%d" % i, 1.6, vv, 1.8, 0.9, 0.0, 8.0,
                 m["ws_green"], c)
    dock_box("ws_entrance", 1.05, 0.0, 0.36, 12.6, 7.0, 8.0, m["ws_green"], c)
    for i in range(7):
        dock_box("ws_entrance_letter_%d" % i, 0.84, -4.5 + i * 1.5, 0.06, 0.7,
                 7.3, 7.62, m["white"], c)
    dock_box("ws_entrance_dark", 3.4, 0.0, 2.6, 11.0, 0.0, 0.14, m["dark"], c)

    # ---- S-03 ground pipe group, 4 x dia 0.6, crossing the yard at 15 deg ----
    p0u, p0v, p1u, p1v = 10.0, -18.0, 72.0, -1.4
    ax, ay = dock_world(p0u, p0v)
    bx, by = dock_world(p1u, p1v)
    pang = math.atan2(by - ay, bx - ax)
    plen = math.hypot(bx - ax, by - ay)
    for i in range(4):
        ox, oy = dock_world(p0u, p0v + i * 1.05)
        qx, qy = dock_world(p1u, p1v + i * 1.05)
        mx, my = (ox + qx) / 2.0, (oy + qy) / 2.0
        add_cyl_h("ws_pipe_%d" % i, mx, my, 0.62, plen, 0.30, m["metal"], c,
                  axis="X", vertices=12, rot_z=pang)
        for k in range(7):
            f = (k + 0.5) / 7.0
            fx, fy = ox + (qx - ox) * f, oy + (qy - oy) * f
            add_cyl_h("ws_flange_%d_%d" % (i, k), fx, fy, 0.62, 0.22, 0.42,
                      m["steel"], c, axis="X", vertices=12, rot_z=pang)
            add_box_local("ws_pipestand_%d_%d" % (i, k), fx, fy, 0.22,
                          0.5, 1.5, 0.44, m["dark"], c, rot_z=pang)

    # ---- S-04 diversion pit 30 x 18, depth 2, yellow guard rail ----
    pu, pv = 68.0, 12.0
    dock_box("ws_pit_floor", pu, pv, 30.0, 18.0, -2.0, -1.86, m["dark"], c)
    for i, (du_, dv_, uu_, vv_) in enumerate(((30.0, 0.6, pu, pv - 9.0),
                                              (30.0, 0.6, pu, pv + 9.0),
                                              (0.6, 18.0, pu - 15.0, pv),
                                              (0.6, 18.0, pu + 15.0, pv))):
        dock_box("ws_pit_wall_%d" % i, uu_, vv_, du_, dv_, -2.0, 0.0,
                 m["ws_refractory"], c)
    px, py = dock_world(pu, pv)
    add_cyl("ws_pit_cone", px, py, -1.86, -0.35, 2.4, m["steel"], c, vertices=10)
    for i, (du_, dv_, uu_, vv_) in enumerate(((30.4, 0.14, pu, pv - 9.5),
                                              (21.0, 0.14, pu - 4.0, pv + 9.5),
                                              (0.14, 18.4, pu - 15.4, pv),
                                              (0.14, 18.4, pu + 15.4, pv))):
        dock_box("ws_pitrail_%d" % i, uu_, vv_, du_, dv_, 0.0, 1.1,
                 m["ws_yellow"], c)

    # ---- S-05 containers: 3 unequal piles, seeded jitter (R1/R3/R4) ----
    cmats = (m["container_blue"], m["container_gray"], m["container_olive"])
    for pi, (bu, bv, n) in enumerate(((16.0, -22.0, 3), (44.0, 21.0, 3),
                                      (80.0, -19.0, 4))):
        for k in range(n):
            du_ = rnd.uniform(-3.2, 3.2)
            dv_ = rnd.uniform(-1.8, 1.8)
            cx, cy = dock_world(bu + du_, bv + dv_ + k * 2.95)
            lv = 1 if (k == n - 1 and rnd.random() < 0.6) else 0
            add_box_local("ws_cont_%d_%d" % (pi, k), cx, cy,
                          0.14 + lv * 2.62 + 1.29, 6.0, 2.4, 2.58,
                          cmats[(pi + k) % 3], c,
                          rot_z=DOCK_ROTZ + rnd.uniform(-0.62, 0.62))

    # ---- S-06 ground: slab joints / partial yellow lines / trench covers / puddles ----
    for i, uu_ in enumerate((12.0, 28.0, 46.0, 64.0, 82.0)):
        dock_box("ws_slabjoint_%d" % i, uu_, 0.0, 0.16, 52.0, 0.0, 0.14,
                 m["joint"], c)
    for i, (uu_, vv_, ln) in enumerate(((20.0, -13.0, 22.0), (52.0, 6.0, 17.0),
                                        (84.0, 3.0, 14.0))):
        dock_box("ws_yellow_%d" % i, uu_, vv_, ln, 0.30, 0.0, 0.14,
                 m["ws_yellow"], c)
    for i, (uu_, vv_) in enumerate(((30.0, 14.0), (58.0, -16.0))):
        dock_box("ws_trench_%d" % i, uu_, vv_, 22.0, 0.9, 0.0, 0.14,
                 m["metal"], c)
    for i, (uu_, vv_, du_, dv_) in enumerate(((24.0, 5.0, 7.0, 4.0),
                                              (60.0, -6.0, 6.0, 3.5),
                                              (88.0, 10.0, 5.0, 3.0))):
        dock_box("ws_puddle_%d" % i, uu_, vv_, du_, dv_, 0.0, 0.14,
                 m["ws_wet"], c)

    # ---- S-07 control room: OPEN TOP, waist-high glass only ----
    for i, (du_, dv_, uu_, vv_) in enumerate(((8.0, 0.18, 12.0, 19.0),
                                              (8.0, 0.18, 12.0, 25.0),
                                              (0.18, 6.0, 8.0, 22.0),
                                              (0.18, 6.0, 16.0, 22.0))):
        dock_box("ws_ctrl_glass_%d" % i, uu_, vv_, du_, dv_, 0.0, 1.35,
                 m["ws_glass"], c)
    dock_box("ws_ctrl_bench", 12.0, 22.0, 3.0, 1.2, 0.0, 0.95, m["metal"], c)

    # ---- S-08 entrance bollards (8 m occupied, 4 m gap on east side) ----
    for i, vv_ in enumerate((-4.0, -1.0, 2.0)):
        dock_box("ws_bollard_%d" % i, 6.0, vv_, 0.34, 0.34, 0.0, 1.2,
                 m["ws_yellow"], c)
    dock_box("ws_bollard_bar", 6.0, -1.0, 0.20, 6.4, 1.0, 1.2, m["dark"], c)

    # ---- S-09 evac frame + arrow (no blue glow) ----
    eu, ev = 90.0, 19.0
    for i, (du_, dv_, uu_, vv_) in enumerate(((4.4, 0.24, eu, ev - 2.1),
                                              (4.4, 0.24, eu, ev + 2.1),
                                              (0.24, 4.4, eu - 2.1, ev),
                                              (0.24, 4.4, eu + 2.1, ev))):
        dock_box("ws_evac_%d" % i, uu_, vv_, du_, dv_, 0.0, 0.14,
                 m["ws_yellow"], c)
    dock_box("ws_evac_arrow_v", eu, ev, 0.36, 2.4, 0.0, 0.14, m["ws_yellow"], c)
    dock_box("ws_evac_arrow_h", eu - 0.7, ev + 1.2, 1.5, 0.30, 0.0, 0.14,
             m["ws_yellow"], c)

    # ---- S-10 wall-mounted green terminal (not a glowing pillar) ----
    dock_box("ws_terminal", 90.0, 27.4, 0.62, 0.22, 1.4, 2.2,
             m["ws_terminal"], c)
    dock_box("ws_terminal_led", 90.0, 27.2, 0.20, 0.06, 2.0, 2.12,
             m["emis"], c)

    # ---- S-11 cabinets / pallets / drums, clustered to one side ----
    for i in range(6):
        uu_ = 30.0 + i * 6.4 + rnd.uniform(-2.6, 2.6)
        vv_ = -25.0 + rnd.uniform(-3.2, 3.2)
        cx, cy = dock_world(uu_, vv_)
        add_box_local("ws_cab_%d" % i, cx, cy, 1.0, 1.5, 0.8, 2.0,
                      m["dark"], c, rot_z=DOCK_ROTZ + rnd.uniform(-0.5, 0.5))
    for i, (uu_, vv_) in enumerate(((22.0, 9.0), (27.0, 10.5), (33.0, 8.0),
                                    (86.0, -8.0))):
        dock_box("ws_pallet_%d" % i, uu_, vv_, 2.2, 2.0, 0.0, 0.24,
                 m["wood"], c)
        bx, by = dock_world(uu_, vv_)
        add_box_local("ws_palletbox_%d" % i, bx, by, 0.87, 1.8, 1.6, 1.26,
                      m["container_gray"], c,
                      rot_z=DOCK_ROTZ + rnd.uniform(-0.55, 0.55))
    for i in range(5):
        uu_ = 74.0 + (i % 3) * 1.6 + rnd.uniform(-0.6, 0.6)
        vv_ = 6.0 + (i // 3) * 2.1 + rnd.uniform(-0.9, 0.9)
        dx, dy = dock_world(uu_, vv_)
        add_box_local("ws_drum_%d" % i, dx, dy, 0.45 + rnd.uniform(0, 0.25),
                      0.9, 0.9, 0.9 + rnd.uniform(0, 0.4),
                      m["container_blue"] if i % 2 else m["orange"], c,
                      rot_z=DOCK_ROTZ + rnd.uniform(-0.8, 0.8))

    # ---- S-12 ladders ----
    for i, (uu_, vv_) in enumerate(((46.0, 20.6), (82.0, -17.0))):
        for j, vof in enumerate((-0.5, 0.5)):
            dock_box("ws_ladder_rail_%d_%d" % (i, j), uu_, vv_ + vof, 0.10, 0.10,
                     0.0, 5.4, m["metal"], c)
        for j in range(7):
            dock_box("ws_ladder_rung_%d_%d" % (i, j), uu_, vv_, 0.10, 1.1,
                     0.6 + j * 0.7, 0.72 + j * 0.7, m["steel"], c)

    # ---- deck + pointed tip (dock outline preserved, bridge B unchanged) ----
    dock_box("ws_floor", DOCK_LEN / 2, 0, DOCK_LEN + 1.2, DOCK_HALF * 2 + 1.2,
             -0.5, 0.0, m["apron"], c)
    tip = [dock_world(96, -DOCK_HALF), dock_world(96, DOCK_HALF), dock_world(114, 0)]
    add_prism("ws_tip", tip, -0.5, 0.0, m["apron"], c)
    print("WORKSHOP_OK")


def build_west_gate(m):
    c = coll("WEST_GATE")
    add_box("gate_island", 16, 32, 36, 84, -0.4, PLATFORM_Z, m["island"], c)
    add_box("gate_bridge", 32, 46, 52, 68, -0.4, PLATFORM_Z, m["platform"], c)
    for i, y in enumerate((51.5, 68.5)):
        add_cyl(f"gate_post_{i}", 40, y, PLATFORM_Z, PLATFORM_Z + 6, 0.8, m["white"], c, vertices=12)
    add_box("gate_door", 39.6, 40.0, 52, 60, PLATFORM_Z, PLATFORM_Z + 3.2, m["metal"], c)
    add_box("gate_hut", 22, 26, 72, 76, PLATFORM_Z, PLATFORM_Z + 3.2, m["white"], c)
    add_box("gate_hut_roof", 21.6, 26.4, 71.6, 76.4, PLATFORM_Z + 3.2, PLATFORM_Z + 3.5,
            m["dark"], c)
    add_box("courtyard", 4, 16, 36, 84, -0.4, 0.0, m["rock"], c)
    for (px0, py0, px1, py1) in ((4, 36, 16, 36), (4, 84, 16, 84), (4, 36, 4, 84), (16, 36, 16, 84)):
        mx, my = (px0 + px1) / 2, (py0 + py1) / 2
        ang = math.atan2(py1 - py0, px1 - px0)
        L2 = math.hypot(px1 - px0, py1 - py0)
        add_box_local("yard_fence_%d_%d" % (px0, py0), mx, my, 1.1, L2, 0.15, 2.2,
                      m["mesh"], c, rot_z=ang)
    # elevator tower island + 104 m silhouette
    add_box("tower_island", 2, 20, 100, 128, -0.4, PLATFORM_Z - 1.0, m["rock"], c)
    add_box("tower_base", 8, 14, 111, 117, PLATFORM_Z - 1.0, PLATFORM_Z + 4, m["white"], c)
    add_box("tower_shaft", 9.5, 12.5, 112.5, 115.5, PLATFORM_Z + 4, PLATFORM_Z + 100,
            m["white"], c)
    add_box("tower_head", 3, 19, 113.2, 114.8, PLATFORM_Z + 100, PLATFORM_Z + 102, m["white"], c)


def build_north_band(m):
    """v07 north outer band: dormitory + control tower + staff tunnel (silhouette grade, Q1)."""
    c = coll("NORTH_BAND")
    z = PLATFORM_Z
    add_prism("north_plate", [(24, 134), (238, 134), (238, 184), (24, 184)],
              -0.4, PLATFORM_Z, m["platform"], c)
    # 中控楼: tallest landmark, block + crown + canopy + window strips + antenna truss
    add_box("ctrl_main", 92, 148, 150, 184, z, z + 22, m["white"], c)
    add_box("ctrl_crown", 96, 144, 154, 180, z + 22, z + 25, m["dock"], c)
    add_box("ctrl_canopy", 100, 140, 147.5, 150, z + 4.5, z + 5.6, m["evac_blue"], c)
    for i in range(4):
        add_box(f"ctrl_win_{i}", 96 + i * 13, 104 + i * 13, 149.6, 149.9,
                z + 8, z + 19, m["emis"], c)
    for k in range(3):
        add_box(f"ctrl_ant_{k}", 117 + k, 117.6 + k, 165, 167, z + 25, z + 25 + (9 - k * 2.5),
                m["metal"], c)
    add_box("ctrl_dish", 133, 141, 168, 170, z + 26, z + 27, m["steel"], c)
    # 宿舍区: 3 blocks + link
    add_box("dorm_a", 28, 50, 142, 164, z, z + 12, m["white"], c)
    add_box("dorm_b", 56, 80, 142, 166, z, z + 10, m["dock"], c)
    add_box("dorm_c", 28, 50, 170, 178, z, z + 8, m["dock"], c)
    add_box("dorm_link", 50, 56, 148, 158, z, z + 3.5, m["steel"], c)
    for i in range(3):
        add_box(f"dorm_win_{i}", 30 + i * 7, 34 + i * 7, 141.6, 141.9, z + 3, z + 9, m["emis"], c)
    # 一号员工通道: elevated corridor dorm_b -> ctrl bridge head
    dx0, dy0, dx1, dy1 = 80.0, 156.0, 112.0, 136.0
    L = math.hypot(dx1 - dx0, dy1 - dy0)
    ang = math.atan2(dy1 - dy0, dx1 - dx0)
    add_box_local("tunnel_body", (dx0 + dx1) / 2, (dy0 + dy1) / 2, z + 7.5,
                  L + 4, 4.0, 3.0, m["steel"], c, rot_z=ang)
    for t in (0.2, 0.5, 0.8):
        cx_ = dx0 + (dx1 - dx0) * t
        cy_ = dy0 + (dy1 - dy0) * t
        add_box(f"tunnel_pier_{t}", cx_ - 0.7, cx_ + 0.7, cy_ - 0.7, cy_ + 0.7,
                z, z + 6.0, m["metal"], c)
    # 中控桥 over the north channel (island y120 -> band y134)
    add_box("ctrl_bridge_deck", 100, 124, 118, 136, z, z + 0.3, m["causeway"], c)
    for xx in (101, 123):
        for yy in (119, 135):
            add_cyl(f"ctrl_bridge_post_{xx}_{yy}", xx, yy, z + 0.3, z + 2.6, 0.22,
                    m["metal"], c, vertices=8)
    for yy in (118.6, 135.4):
        add_box(f"ctrl_bridge_rail_{yy}", 100, 124, yy - 0.12, yy + 0.12,
                z + 0.3, z + 1.1, m["metal"], c)
    for xx in (104, 120):
        add_cyl(f"ctrl_bridge_lamp_{xx}", xx, 127, z + 0.3, z + 4.2, 0.14,
                m["metal"], c, vertices=8)


def build_industrial(m):
    """v07 east outer band: print/hoist/assembly blocks + tank farm (silhouette grade, Q1)."""
    c = coll("EAST_BAND")
    z = PLATFORM_Z
    add_prism("east_plate", [(194, -14), (240, -14), (240, 134), (194, 134)],
              -0.4, PLATFORM_Z, m["platform"], c)
    add_box("ind_print", 198, 224, 88, 116, z, z + 9, m["dock"], c)
    add_box("ind_print_roof", 197, 225, 87, 117, z + 9, z + 9.6, m["steel"], c)
    add_box("ind_hoist", 198, 218, 36, 62, z, z + 11, m["white"], c)
    add_box("ind_assembly", 222, 238, 36, 62, z, z + 9, m["dock"], c)
    add_box("ind_hoist_door", 219.6, 220.4, 44, 54, z, z + 7, m["evac_blue"], c)
    for i in range(3):
        add_box(f"ind_win_{i}", 200 + i * 8, 206 + i * 8, 87.6, 87.9, z + 4, z + 8, m["emis"], c)
    # 罐装区: 6 vertical tanks
    for i, (tx, ty) in enumerate(((204, 6), (216, 6), (228, 6), (204, 20), (216, 20), (228, 20))):
        add_cyl(f"tank_{i}", tx, ty, z, z + 10, 4.5, m["white"], c, vertices=20)
        add_cyl(f"tank_cap_{i}", tx, ty, z + 10, z + 10.5, 4.7, m["steel"], c, vertices=20)
    add_cyl_h("tank_pipe", 216, 13, z + 3.5, 30.0, 0.5, m["metal"], c, vertices=10)
    # containers moved from the old SE margin (Q1 backdrop)
    for i, (x, y, ang) in enumerate(((200, -6, 0), (200, 2, 0), (206, -6, 0))):
        add_box_local(f"oc_{i}", x, y, z + 1.3, 6, 2.4, 2.6,
                      [m["container_blue"], m["container_olive"], m["container_gray"]][i],
                      c, rot_z=math.radians(ang))
    # 东区吊桥 over the east channel (island x180 -> band x194), slight 10 deg skew
    add_box_local("east_bridge_deck", 187, 60, z + 0.15, 20, 15, 0.3, m["causeway"], c,
                  rot_z=math.radians(10))
    for yy in (53, 67):
        add_box_local(f"east_bridge_truss_{yy}", 187, yy, z + 1.4, 20, 0.35, 2.0,
                      m["mesh"], c, rot_z=math.radians(10))
    for xx in (181, 193):
        add_box_local(f"east_bridge_pier_{xx}", xx, 60, z - 1.0, 1.4, 2.0, 7.0,
                      m["metal"], c, rot_z=math.radians(10))


def build_launch(m):
    """v07 SW diagonal launch strip into the sea (silhouette grade, Q1).

    Strip azimuth 30 deg west of south from the island SW shore; the tail runs
    out of the 240 m window (documented deviation, plan §4)."""
    c = coll("LAUNCH")
    z = PLATFORM_Z
    ang = math.radians(30)
    ux, uy = -math.sin(ang), -math.cos(ang)
    px_, py_ = -uy, ux
    sx, sy = 72.0, -4.0
    L = 160.0
    hw = 9.0
    pts = [(sx + px_ * hw, sy + py_ * hw), (sx + ux * L + px_ * hw, sy + uy * L + py_ * hw),
           (sx + ux * L - px_ * hw, sy + uy * L - py_ * hw), (sx - px_ * hw, sy - py_ * hw)]
    add_prism("launch_strip", pts, -0.4,
              lambda i, p: PLATFORM_Z if i in (0, 3) else PLATFORM_Z - 2.0, m["causeway"], c)
    pax, pay = sx + ux * 95, sy + uy * 95
    add_cyl("launch_pad", pax, pay, z - 2.0, z - 1.6, 13.0, m["dock"], c, vertices=28)
    add_cyl("launch_pad_ring", pax, pay, z - 1.6, z - 1.45, 9.5, m["yellow"], c, vertices=28)
    gx, gy = sx + ux * 108, sy + uy * 108
    add_box("launch_gantry", gx - 4, gx + 4, gy - 4, gy + 4, z - 2.0, z + 24, m["steel"], c)
    for k in range(4):
        add_box(f"launch_gantry_top_{k}", gx - 3 + k * 1.6, gx - 1.6 + k * 1.6,
                gy - 1, gy + 1, z + 24 + k * 1.2, z + 25 + k * 1.2, m["orange"], c)
    add_cyl("launch_rocket", pax, pay, z - 1.6, z + 20, 2.2, m["white"], c, vertices=16)
    add_cyl("launch_rocket_tip", pax, pay, z + 20, z + 24, 1.0, m["orange"], c, vertices=16)
    for i in range(3):
        tx = sx + ux * (28 + i * 22) + px_ * 5.5
        ty = sy + uy * (28 + i * 22) + py_ * 5.5
        add_cyl(f"launch_tank_{i}", tx, ty, z - 1.5, z + 4.5, 2.2, m["white"], c, vertices=12)


def build_north_gate(m):
    """North gate: gatehouse, canopy, checkpoint and a flag mast on the site's own yard."""
    c = coll("NORTH_GATE")
    z = PLATFORM_Z
    GT = -93.0                      # gate line, 6 m inside the perimeter wall
    for off in (-12.6, 12.6):
        av_box(f"ng_post_{off}", GT, off, 0.9, 0.9, z, z + 7.2, m["white"], c)
        av_box(f"ng_postcap_{off}", GT, off, 1.3, 1.3, z + 7.2, z + 7.5, m["metal"], c)
    av_box("ng_beam", GT, 0, 1.1, 26.4, z + 6.2, z + 7.2, m["white"], c)
    av_box("ng_sign", GT + 0.8, 0, 0.26, 12.0, z + 4.6, z + 6.0, m["evac_blue"], c)
    for off, tag in ((17.5, "w"), (-17.5, "e")):
        av_box(f"ng_booth_{tag}", GT - 3.0, off, 6.0, 5.0, z, z + 3.2,
               m["container_gray"], c)
        av_box(f"ng_booth_roof_{tag}", GT - 3.0, off, 6.6, 5.6, z + 3.2, z + 3.45,
               m["steel"], c)
        av_box(f"ng_booth_win_{tag}", GT - 0.05, off, 0.12, 3.4, z + 1.4, z + 2.6,
               m["glass"], c)
    av_box("ng_guard", GT - 3.0, -30.0, 10.0, 6.0, z, z + 3.4, m["white"], c)
    av_box("ng_guard_roof", GT - 3.0, -30.0, 10.8, 6.8, z + 3.4, z + 3.66, m["steel"], c)
    # inbound / outbound lanes painted on the yard
    for sgn in (-1, 1):
        av_box(f"ng_lane_{sgn}", GT + 4.0, sgn * 5.0, 9.0, 0.18, z + 0.03, z + 0.05,
               m["white"], c)
        for k in range(3):
            av_box(f"ng_arrow_{sgn}_{k}", GT + 2.0 + k * 4.0, sgn * 5.0, 0.9, 1.4,
                   z + 0.03, z + 0.05, m["white"], c)
    x, y = av(GT + 5.0, 22.0)
    add_cyl("ng_mast", x, y, z, z + 12.0, 0.16, m["metal"], c, vertices=10)
    add_box("ng_flag", x, x + 0.06, y, y + 3.2, z + 9.4, z + 11.2, m["evac_blue"], c)
    print("NGATE_OK")


def room_gates(rx0, rx1, ry0, ry1):
    """Door openings on each wall of a room, from global GATES."""
    out = {"n": [], "s": [], "e": [], "w": []}
    for gx, gy in GATES.values():
        if gy == ry1 and rx0 < gx < rx1:
            out["n"].append((gx - DOOR_W / 2, gx + DOOR_W / 2))
        if gy == ry0 and rx0 < gx < rx1:
            out["s"].append((gx - DOOR_W / 2, gx + DOOR_W / 2))
        if gx == rx1 and ry0 < gy < ry1:
            out["e"].append((gy - DOOR_W / 2, gy + DOOR_W / 2))
        if gx == rx0 and ry0 < gy < ry1:
            out["w"].append((gy - DOOR_W / 2, gy + DOOR_W / 2))
    return out


# ------------------------------------------------------------------ v11 core (single storey, 1:1)
# v13 core: 2 x 2 halls + cross corridor
CORE_TN = -86.0
CORE_TS = -8.0
CORE_HALF = 39.0
HALL = 34.0
CROSS = 10.0
HALL_H = 12.5
HALLS = [("H1", -86.0, -52.0, -39.0, -5.0), ("H2", -86.0, -52.0, 5.0, 39.0),
         ("H3", -42.0, -8.0, -39.0, -5.0), ("H4", -42.0, -8.0, 5.0, 39.0)]


def lane_world(name, p0, p1, w, z0, z1, mat, c):
    import math as _m
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = _m.hypot(dx, dy)
    return add_box_local(name, (p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0,
                         (z0 + z1) / 2.0, L, w, z1 - z0, mat, c, rot_z=_m.atan2(dy, dx))


def door_single(name, t, vc, z0, m, c, face=1.0):
    av_box(f"{name}_leaf", t + 0.03 * face, vc, 0.08, 1.20, z0, z0 + 2.20, m["steel"], c)
    av_box(f"{name}_jamb_l", t + 0.05 * face, vc - 0.66, 0.14, 0.12, z0, z0 + 2.32, m["white"], c)
    av_box(f"{name}_jamb_r", t + 0.05 * face, vc + 0.66, 0.14, 0.12, z0, z0 + 2.32, m["white"], c)
    av_box(f"{name}_head", t + 0.05 * face, vc, 0.14, 1.44, z0 + 2.20, z0 + 2.32, m["white"], c)


def avr(name, t0, t1, v0, v1, z0, z1, mat, c):
    return av_box(name, (t0 + t1) / 2.0, (v0 + v1) / 2.0, t1 - t0, v1 - v0, z0, z1, mat, c)


def wall_v_run(name, t, v0, v1, z0, h, th, ops, mat, c):
    cur = v0
    for i, (vc, w, dh) in enumerate(sorted(ops)):
        a, b = vc - w / 2.0, vc + w / 2.0
        if a > cur + 0.01:
            av_box(f"{name}_s{i}", t, (cur + a) / 2.0, th, a - cur, z0, z0 + h, mat, c)
        av_box(f"{name}_l{i}", t, vc, th, w, z0 + dh, z0 + h, mat, c)
        cur = max(cur, b)
    if cur < v1 - 0.01:
        av_box(f"{name}_s9", t, (cur + v1) / 2.0, th, v1 - cur, z0, z0 + h, mat, c)


def wall_t_run(name, v, t0, t1, z0, h, th, ops, mat, c):
    cur = t0
    for i, (tc, w, dh) in enumerate(sorted(ops)):
        a, b = tc - w / 2.0, tc + w / 2.0
        if a > cur + 0.01:
            av_box(f"{name}_s{i}", (cur + a) / 2.0, v, a - cur, th, z0, z0 + h, mat, c)
        av_box(f"{name}_l{i}", tc, v, w, th, z0 + dh, z0 + h, mat, c)
        cur = max(cur, b)
    if cur < t1 - 0.01:
        av_box(f"{name}_s9", (cur + t1) / 2.0, v, t1 - cur, th, z0, z0 + h, mat, c)


def roller_door(name, t, vc, w, h, z0, m, c, face=1.0):
    av_box(f"{name}_panel", t + 0.02 * face, vc, 0.10, w, z0, z0 + h, m["dark"], c)
    for i in range(int(h / 0.6)):
        zz = z0 + 0.6 * (i + 1)
        av_box(f"{name}_slat{i}", t + 0.10 * face, vc, 0.06, w - 0.10, zz - 0.05, zz, m["metal"], c)
    av_box(f"{name}_head", t + 0.04 * face, vc, 0.26, w + 0.44, z0 + h, z0 + h + 0.20, m["white"], c)


def double_door(name, t, vc, z0, m, c, face=1.0):
    av_box(f"{name}_leaf", t + 0.03 * face, vc, 0.08, 2.40, z0, z0 + 2.40, m["steel"], c)
    av_box(f"{name}_seam", t + 0.08 * face, vc, 0.05, 0.05, z0, z0 + 2.40, m["dark"], c)
    for sgn in (-1, 1):
        av_box(f"{name}_jamb{sgn}", t + 0.05 * face, vc + sgn * 1.26, 0.14, 0.12, z0, z0 + 2.52,
               m["white"], c)
    av_box(f"{name}_head", t + 0.05 * face, vc, 0.14, 2.64, z0 + 2.40, z0 + 2.52, m["white"], c)


def canopy(name, t, vc, z0, m, c, face=1.0, w=6.4, d=2.4):
    av_box(f"{name}_slab", t + face * d / 2.0, vc, d, w, z0, z0 + 0.24, m["steel"], c)
    for sgn in (-1, 1):
        av_box(f"{name}_rod{sgn}", t + face * d * 0.82, vc + sgn * (w / 2.0 - 0.3), 0.08, 0.08,
               z0 + 0.24, z0 + 1.30, m["metal"], c)


def panel_joints_t(name, t, v0, v1, z0, h, face, m, c):
    v = v0 + 6.0
    i = 0
    while v < v1 - 0.5:
        av_box(f"{name}_{i}", t + 0.03 * face, v, 0.05, 0.05, z0, z0 + h, m["dark"], c)
        v += 6.0
        i += 1
    for k in (1.5, 3.0, 4.5, 6.0, 7.5, 9.0, 10.5):
        if k < h - 0.4:
            av_box(f"{name}_h{k}", t + 0.03 * face, (v0 + v1) / 2.0, 0.05, v1 - v0,
                   z0 + k - 0.02, z0 + k + 0.02, m["dark"], c)


# =====================================================================
# v15 · four core rooms
# Spec: planning/art/SPACE_BASE_CORE_ROOMS_ART_PLAN_20261108.md (v1.3)
# Local hall frame: u = t - t0, v = off - v0, both 0..34, inner clear 0.45..33.55
# All lateral positions go through av()/avr() so AV_ROT is applied once.
# =====================================================================

_V15_FONT = {
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00110", "01010", "10010", "11111", "00010", "00010", "00010"),
}


def _v15_cyl(name, t, off, z0, z1, r, mat, c, verts=48):
    x, y = av(t, off)
    return add_cyl(name, x, y, z0, z1, r, mat, c, vertices=verts)


def _v15_ring(name, t, off, r, w, z0, z1, mat, c, seg=64, a0=0.0, a1=2 * math.pi):
    x, y = av(t, off)
    return add_tube(name, x, y, r + w * 0.5, max(0.02, r - w * 0.5), z0, z1, mat, c, seg, a0, a1)


def _v15_hcyl(name, t, off, zc, length, r, mat, c, deg=0.0, verts=24):
    x, y = av(t, off)
    return add_cyl_h(name, x, y, zc, length, r, mat, c, vertices=verts,
                     rot_z=AV_ROT + math.radians(deg))


def _v15_rot(name, t, off, du, dv, z0, z1, mat, c, deg=0.0):
    x, y = av(t, off)
    return add_box_local(name, x, y, (z0 + z1) * 0.5, du, dv, z1 - z0, mat, c,
                         rot_z=AV_ROT + math.radians(deg))


def _v15_text(name, t0, v0, cu, cv, z0, z1, txt, m, c, cell=0.5, gap=0.6, mat=None):
    """Ground stencil. Horizontal runs are merged into single tiles (object budget)."""
    mat = mat or m["white"]
    n = len(txt)
    width = n * 5 * cell + (n - 1) * gap * cell
    uu = cu - width * 0.5
    for ci, ch in enumerate(txt):
        rows = _V15_FONT.get(ch)
        if not rows:
            continue
        for ry, row in enumerate(rows):
            cx = 0
            while cx < len(row):
                if row[cx] != "1":
                    cx += 1
                    continue
                run = 1
                while cx + run < len(row) and row[cx + run] == "1":
                    run += 1
                a = uu + cx * cell
                b = cv + (3.5 - ry - 1) * cell
                avr("%s_%d_%d_%d" % (name, ci, ry, cx), t0 + a, t0 + a + run * cell,
                    v0 + b, v0 + b + cell, z0, z1, mat, c)
                cx += run
        uu += 5 * cell + gap * cell


def fit_out(name, t0, t1, v0, v1, z, m, c):
    """v15: per-hall rebuild. Four halls only -- no CEO room by user ruling (22:19)."""
    tag = name.lower()
    if name == "H1":
        _v15_h1(tag, t0, v0, z, m, c)
    elif name == "H2":
        _v15_h2(tag, t0, v0, z, m, c)
    elif name == "H3":
        _v15_h3(tag, t0, v0, z, m, c)
    elif name == "H4":
        _v15_h4(tag, t0, v0, z, m, c)


# ---------------------------------------------------------------- H1 centrifuge
def _v15_h1(tag, t0, v0, z, m, c):
    def R(nm, u0, u1, w0, w1, z0, z1, mat):
        avr("%s_v15_%s" % (tag, nm), t0 + u0, t0 + u1, v0 + w0, v0 + w1, z0, z1, mat, c)

    IN0, IN1 = 0.45, 33.55
    ZF = z + 0.06
    Z1 = ZF + 0.14          # whole-hall dark deck (0.14 m solid, not a decal)
    R("deck", IN0, IN1, IN0, IN1, ZF, Z1, m["h1_floor"])
    # wall skirt 1.2 m painted on the north + west walls only (D4: no four-side frame)
    R("skirt_n", IN0, IN1, IN0, IN0 + 1.2, Z1, Z1 + 0.10, m["cap_h1"])
    R("skirt_w", IN0, IN0 + 1.2, IN0 + 1.2, IN1, Z1, Z1 + 0.10, m["cap_h1"])
    # bright perimeter walk 1.35 m -- the "dark floor + light ring" figure/ground (D5)
    R("walk_n", IN0, IN1, IN0 + 1.2, IN0 + 2.55, Z1, Z1 + 0.10, m["platform"])
    R("walk_w", IN0 + 1.2, IN0 + 2.55, IN0 + 2.55, IN1, Z1, Z1 + 0.10, m["platform"])
    R("walk_s", IN0, IN1, IN1 - 1.5, IN1, Z1, Z1 + 0.10, m["platform"])
    R("walk_e", IN1 - 1.5, IN1, IN0, IN1 - 1.5, Z1, Z1 + 0.10, m["platform"])
    Z2 = Z1 + 0.10
    # main circular floor
    _v15_cyl("%s_v15_disc" % tag, t0 + 17.0, v0 + 17.0, Z2 - 0.02, Z2 + 0.12,
             14.0, m["h1_disc"], c, 72)
    Z3 = Z2 + 0.12
    for i, rr in enumerate((3.0, 5.5, 8.0, 11.0)):
        _v15_ring("%s_v15_ring%d" % (tag, i), t0 + 17.0, v0 + 17.0, rr, 0.30,
                  Z3, Z3 + 0.10, m["white"], c, 72)
    for i in range(12):
        a = i * 30.0 + 6.0
        cu = 17.0 + 9.4 * math.cos(math.radians(a))
        cv = 17.0 + 9.4 * math.sin(math.radians(a))
        _v15_rot("%s_v15_tick%d" % (tag, i), t0 + cu, v0 + cv, 1.6, 0.30,
                 Z3, Z3 + 0.08, m["orange"], c, deg=a)
    # centre column: silver segmented shaft, black flanges, rust foot ring
    _v15_ring("%s_v15_colfoot" % tag, t0 + 17.0, v0 + 17.0, 1.05, 0.55, Z3, Z3 + 0.26,
              m["ws_refractory"], c, 32)
    _v15_cyl("%s_v15_col" % tag, t0 + 17.0, v0 + 17.0, Z3, Z3 + 8.6, 0.70, m["metal"], c, 24)
    for i in range(8):
        hh = Z3 + 1.4 + i * 0.95
        _v15_rot("%s_v15_flange%d" % (tag, i), t0 + 17.0, v0 + 17.0, 1.55, 1.55,
                 hh, hh + 0.20, m["dark"], c)
    # the pod: the only diagonal in the hall
    zc = Z3 + 2.30
    _v15_hcyl("%s_v15_pod" % tag, t0 + 20.0, v0 + 15.0, zc, 8.4, 1.25, m["char_dark"], c, -18, 28)
    aa = math.radians(-18)
    for i, s in enumerate((-1.9, 1.9)):
        cu = 20.0 + s * math.cos(aa)
        cv = 15.0 + s * math.sin(aa)
        _v15_hcyl("%s_v15_podband%d" % (tag, i), t0 + cu, v0 + cv, zc, 0.55, 1.31,
                  m["steel"], c, -18, 28)
    for i, s in enumerate((-4.0, 4.0)):
        cu = 20.0 + s * math.cos(aa)
        cv = 15.0 + s * math.sin(aa)
        _v15_hcyl("%s_v15_podcap%d" % (tag, i), t0 + cu, v0 + cv, zc, 0.34, 1.27,
                  m["dark"], c, -18, 28)
    for i, s in enumerate((-3.0, 3.0)):
        cu = 20.0 + s * math.cos(aa)
        cv = 15.0 + s * math.sin(aa)
        _v15_rot("%s_v15_podskid%d" % (tag, i), t0 + cu, v0 + cv, 1.4, 2.2,
                 Z3, zc - 1.10, m["dark"], c, -18)
    # observation window band -> cabinet row on the north wall, second run on east
    R("cab_n", 2.0, 16.0, IN0, IN0 + 2.2, Z2, Z2 + 2.2, m["white"])
    for i in range(6):
        uu = 2.0 + 2.33 * (i + 1)
        R("cabn_seam%d" % i, uu - 0.06, uu + 0.06, IN0, IN0 + 2.2, Z2 + 0.10,
          Z2 + 2.26, m["dark"])
    R("cab_e", 30.4, 32.6, 2.0, 8.0, Z2, Z2 + 2.2, m["white"])
    for i in range(3):
        ww = 2.0 + 2.0 * (i + 1)
        R("cabe_seam%d" % i, 30.4, 32.6, ww - 0.06, ww + 0.06, Z2 + 0.10, Z2 + 2.26,
          m["dark"])
    # six ring consoles (seeded jitter, not a perfect 6-way split)
    jit = (3.0, -4.5, 6.0, -2.0, 4.0, -5.5)
    for i in range(6):
        a = math.radians(i * 60 + jit[i])
        cu = 17.0 + 15.2 * math.cos(a)
        cv = 17.0 + 15.2 * math.sin(a)
        _v15_rot("%s_v15_console%d" % (tag, i), t0 + cu, v0 + cv, 3.0, 1.1,
                 Z2, Z2 + 1.10, m["steel"], c, deg=math.degrees(a) + 90)
        _v15_rot("%s_v15_consoletop%d" % (tag, i), t0 + cu, v0 + cv, 2.6, 0.9,
                 Z2 + 1.10, Z2 + 1.18, m["orange"], c, deg=math.degrees(a) + 90)
    # two corner equipment rooms (not four -- break the mirror)
    for i, (u0, w0) in enumerate(((IN1 - 4.7, IN0 + 1.2), (IN1 - 4.7, IN1 - 4.7))):
        R("eq%d_glass" % i, u0, u0 + 4.2, w0, w0 + 4.2, Z2, Z2 + 2.6, m["glass"])
        for j, (a0, a1, b0, b1) in enumerate(((u0, u0 + 4.2, w0, w0 + 0.18),
                                              (u0, u0 + 4.2, w0 + 4.02, w0 + 4.2),
                                              (u0, u0 + 0.18, w0, w0 + 4.2),
                                              (u0 + 4.02, u0 + 4.2, w0, w0 + 4.2))):
            R("eq%d_fr%d" % (i, j), a0, a1, b0, b1, Z2 + 2.6, Z2 + 2.75, m["steel"])
    # mid-scale groups (structured runs, driver of perceived density)
    for i in range(5):
        R("pallet%d" % i, 23.0 + i * 1.9, 23.9 + i * 1.9, 28.0, 31.0, Z2, Z2 + 1.3,
          m["container_gray"])
    R("tray_a", 4.5, 4.5 + 9.0, 6.2, 7.0, Z2, Z2 + 0.32, m["metal"])
    R("tray_b", 4.5, 4.5 + 9.0, 7.6, 8.4, Z2, Z2 + 0.32, m["metal"])
    for i in range(4):
        R("cabinet%d" % i, 30.4, 31.6, 22.0 + i * 2.1, 23.6 + i * 2.1, Z2, Z2 + 2.1,
          m["steel"])
    for i in range(6):
        R("plate%d" % i, 26.5 + (i % 3) * 2.2, 27.6 + (i % 3) * 2.2,
          21.0 + (i // 3) * 2.2, 22.1 + (i // 3) * 2.2, Z3, Z3 + 0.10, m["floorshadow"])
    # one structure-shadow pair across the disc (skylight / truss projection)
    _v15_rot("%s_v15_shade%d" % (tag, 0), t0 + 13.0, v0 + 12.0, 22.0, 1.4,
             Z3, Z3 + 0.18, m["floorshadow"], c, deg=28)
    _v15_rot("%s_v15_shade%d" % (tag, 1), t0 + 12.0, v0 + 11.4, 16.0, 0.8,
             Z3, Z3 + 0.19, m["garden_coping"], c, deg=28)
    for i in range(6):
        R("scrate%d" % i, 2.4 + i * 1.5, 3.6 + i * 1.5, 30.4, 31.6, Z3, Z3 + 1.1,
          m["container_gray"])
    for i in range(6):
        R("splate%d" % i, 26.6 + (i % 3) * 2.2, 27.7 + (i % 3) * 2.2,
          16.0 + (i // 3) * 2.2, 17.1 + (i // 3) * 2.2, Z3, Z3 + 0.2, m["metal"])
    _v15_text("%s_v15_id" % tag, t0, v0, 22.5, 24.6, Z3, Z3 + 0.06, "H1", m, c)


# ----------------------------------------------------------------- H2 buoyancy
def _v15_h2(tag, t0, v0, z, m, c):
    def R(nm, u0, u1, w0, w1, z0, z1, mat):
        avr("%s_v15_%s" % (tag, nm), t0 + u0, t0 + u1, v0 + w0, v0 + w1, z0, z1, mat, c)

    IN0, IN1 = 0.45, 33.55
    ZF = z + 0.06
    ZD = ZF + 0.36          # deck top
    PX0, PX1, PY0, PY1 = 6.0, 28.0, 10.0, 24.0
    RC = 1.2                # coping width
    # deck built as four strips so the pool is a real void, not paint
    R("deck_n", IN0, IN1, IN0, PY0 - RC, ZF, ZD, m["dock"])
    R("deck_s", IN0, IN1, PY1 + RC, IN1, ZF, ZD, m["dock"])
    R("deck_w", IN0, PX0 - RC, PY0 - RC, PY1 + RC, ZF, ZD, m["dock"])
    R("deck_e", PX1 + RC, IN1, PY0 - RC, PY1 + RC, ZF, ZD, m["dock"])
    # pool bed + inner shadow ledge
    R("bed", PX0, PX1, PY0, PY1, ZF, ZF + 0.14, m["h2_poolbed"])
    for nm, (a0, a1, b0, b1) in {
            "sh_n": (PX0, PX1, PY0, PY0 + 1.6),
            "sh_s": (PX0, PX1, PY1 - 1.6, PY1),
            "sh_w": (PX0, PX0 + 1.6, PY0 + 1.6, PY1 - 1.6),
            "sh_e": (PX1 - 1.6, PX1, PY0 + 1.6, PY1 - 1.6)}.items():
        R(nm, a0, a1, b0, b1, ZF + 0.14, ZF + 0.24, m["cope"])
    # coping: concrete upstand + teal cap (the single strongest colour cue of H2)
    for nm, (a0, a1, b0, b1) in {
            "rim_n": (PX0 - RC, PX1 + RC, PY0 - RC, PY0),
            "rim_s": (PX0 - RC, PX1 + RC, PY1, PY1 + RC),
            "rim_w": (PX0 - RC, PX0, PY0, PY1),
            "rim_e": (PX1, PX1 + RC, PY0, PY1)}.items():
        R(nm, a0, a1, b0, b1, ZF, ZF + 1.50, m["dock"])
        R(nm + "_cap", a0, a1, b0, b1, ZF + 1.50, ZF + 1.66, m["cap_h2"])
    # thin yellow paint line inside the pool (real: 0.1 m; readable: 0.3 m)
    for nm, (a0, a1, b0, b1) in {
            "yl_n": (PX0 + 0.1, PX1 - 0.1, PY0 + 1.15, PY0 + 1.45),
            "yl_w": (PX0 + 1.15, PX0 + 1.45, PY0 + 1.45, PY1 - 1.15)}.items():
        R(nm, a0, a1, b0, b1, ZF + 0.14, ZF + 0.22, m["ws_yellow"])
    # three pressure chambers, three different headings, two in the pool
    for i, (cu, cv, ang, inpool) in enumerate(((11.5, 15.0, 25, True),
                                               (20.5, 20.5, 0, True),
                                               (25.2, 6.6, -12, False))):
        zc = (ZF + 0.24 + 1.1) if inpool else (ZD + 1.1)
        _v15_hcyl("%s_v15_chamber%d" % (tag, i), t0 + cu, v0 + cv, zc, 7.0, 1.10,
                  m["steel"], c, ang, 24)
        aa = math.radians(ang)
        for j, s in enumerate((-2.0, 0.0, 2.0)):
            uu = cu + s * math.cos(aa)
            vv = cv + s * math.sin(aa)
            _v15_hcyl("%s_v15_chband%d_%d" % (tag, i, j), t0 + uu, v0 + vv, zc, 0.42,
                      1.15, m["dark"], c, ang, 24)
        uu = cu + 3.6 * math.cos(aa)
        vv = cv + 3.6 * math.sin(aa)
        _v15_hcyl("%s_v15_chend%d" % (tag, i), t0 + uu, v0 + vv, zc, 0.30, 1.12,
                  m["ws_yellow"], c, ang, 24)
    # gantry: one beam, no deck plate
    for i, uu in enumerate((3.6, 30.4)):
        _v15_cyl("%s_v15_gleg%d" % (tag, i), t0 + uu, v0 + 17.0, ZD, z + 8.4, 0.55,
                 m["steel"], c, 12)
    R("gbeam", 3.6, 30.4, 16.4, 17.6, z + 7.6, z + 8.4, m["metal"])
    R("gtrolley", 9.2, 11.4, 16.1, 17.9, z + 8.4, z + 8.9, m["steel"])
    R("bbasket", 13.0, 15.6, 16.0, 18.2, z + 2.6, z + 4.9, m["metal"])
    for i, (cu, cv) in enumerate(((13.6, 16.4), (15.0, 17.8))):
        _v15_cyl("%s_v15_bcab%d" % (tag, i), t0 + cu, v0 + cv, z + 4.9, z + 8.4, 0.06,
                 m["dark"], c, 4)
    # office cabin on the deck, window band as top seam
    R("office", 1.4, 9.4, 26.2, 30.2, ZD, ZD + 3.1, m["white"])
    R("office_seam", 1.4, 9.4, 26.2, 26.45, ZD + 1.5, ZD + 2.9, m["dark"])
    for i in range(4):
        R("office_mul%d" % i, 2.6 + i * 1.7, 2.72 + i * 1.7, 26.2, 26.45,
          ZD + 1.5, ZD + 2.9, m["steel"])
    R("office_rim", 1.4, 9.4, 26.2, 26.45, ZD + 3.1, ZD + 3.3, m["steel"])
    for i in range(3):
        R("office_ahu%d" % i, 2.2 + i * 2.3, 3.6 + i * 2.3, 27.4, 29.2, ZD + 3.1, ZD + 3.9,
          m["metal"])
    # black steel guard runs on the coping (not a full yellow ring -- D3)
    for i, (a0, a1) in enumerate(((7.0, 12.0), (15.0, 20.0), (22.0, 27.0))):
        R("guard%d" % i, a0, a1, PY0 - RC - 0.05, PY0 - RC + 0.35, ZF + 1.66,
          ZF + 2.75, m["dark"])
    for i, (b0, b1) in enumerate(((11.0, 16.0), (18.0, 23.0))):
        R("guarde%d" % i, PX1 + RC - 0.35, PX1 + RC + 0.05, b0, b1, ZF + 1.66,
          ZF + 2.75, m["dark"])
    # hazard steps down to the pool (two, offset)
    for i, (a0, b0) in enumerate(((5.2, 25.4), (28.6, 14.0))):
        R("step%d" % i, a0, a0 + 2.2, b0, b0 + 1.4, ZD, ZD + 1.2, m["ws_yellow"])
    # mid-scale runs
    for i in range(6):
        R("crate%d" % i, 2.0 + i * 1.7, 3.0 + i * 1.7, 31.2, 32.4, ZD, ZD + 1.0,
          m["container_gray"])
    for i in range(4):
        R("pipe%d" % i, 31.4, 31.9, 9.5 + i * 0.9, 20.0 + i * 0.9, ZD, ZD + 0.42,
          m["metal"])
    for i in range(5):
        R("lplate%d" % i, 12.0 + i * 2.6, 13.2 + i * 2.6, 26.4, 27.6, ZD, ZD + 0.05,
          m["floorshadow"])
    # skylight: three bright bands and one dark beam shadow on the pool bed
    for i in range(2):
        R("sky%d" % i, PX0 + 3.4 + i * 9.0, PX0 + 5.2 + i * 9.0, PY0 + 2.4, PY1 - 2.4,
          ZF + 0.24, ZF + 0.275, m["platform"])
    R("sky_beam", PX0, PX1, 16.4, 17.6, ZF + 0.24, ZF + 0.30, m["floorshadow"])
    # mid-scale density run B (west/east decks, south wall)
    for i in range(4):
        for j in range(2):
            R("deckplate%d_%d" % (i, j), 1.2 + j * 2.1, 2.5 + j * 2.1,
              11.0 + i * 2.8, 12.4 + i * 2.8, ZD, ZD + 0.22, m["metal"])
    for i in range(6):
        R("scab%d" % i, 12.0 + i * 1.8, 13.3 + i * 1.8, 31.9, 33.3, ZD, ZD + 1.6,
          m["steel"])
    for i in range(6):
        R("ncrate%d" % i, 12.4 + i * 1.5, 13.5 + i * 1.5, 1.1, 2.3, ZD, ZD + 0.9,
          m["container_gray"])
    for i in range(6):
        R("psupp%d" % i, 30.3, 31.1, 10.0 + i * 1.9, 10.8 + i * 1.9, ZD, ZD + 0.7,
          m["dark"])
    _v15_text("%s_v15_id" % tag, t0, v0, 19.0, 3.0, ZD, ZD + 0.06, "H2", m, c)


# -------------------------------------------------------------------- H3 blue
def _v15_h3(tag, t0, v0, z, m, c):
    def R(nm, u0, u1, w0, w1, z0, z1, mat):
        avr("%s_v15_%s" % (tag, nm), t0 + u0, t0 + u1, v0 + w0, v0 + w1, z0, z1, mat, c)

    IN0, IN1 = 0.45, 33.55
    ZF = z + 0.06
    ZD = ZF + 1.20          # deck top, 1.2 m above the pit bed (reads as depth)
    PX0, PX1, PY0, PY1 = 11.0, 23.0, 11.0, 22.0
    R("deck_n", IN0, IN1, IN0, PY0, ZF, ZD, m["floor_ind"])
    R("deck_s", IN0, IN1, PY1, IN1, ZF, ZD, m["floor_ind"])
    R("deck_w", IN0, PX0, PY0, PY1, ZF, ZD, m["floor_ind"])
    R("deck_e", PX1, IN1, PY0, PY1, ZF, ZD, m["floor_ind"])
    R("pit", PX0, PX1, PY0, PY1, ZF, ZF + 0.14, m["h3_pitbed"])
    for nm, (a0, a1, b0, b1) in {
            "pit_sh_n": (PX0, PX1, PY0, PY0 + 1.2),
            "pit_sh_s": (PX0, PX1, PY1 - 1.2, PY1),
            "pit_sh_w": (PX0, PX0 + 1.2, PY0 + 1.2, PY1 - 1.2),
            "pit_sh_e": (PX1 - 1.2, PX1, PY0 + 1.2, PY1 - 1.2)}.items():
        R(nm, a0, a1, b0, b1, ZF + 0.14, ZF + 0.24, m["cap_h3"])
    # hazard edge on the deck, 3 gaps
    for i, (a0, a1, b0, b1) in enumerate(((PX0 - 0.7, PX1 + 0.7, PY0 - 0.7, PY0),
                                          (PX0 - 0.7, PX1 + 0.7, PY1, PY1 + 0.7))):
        R("haz%d" % i, a0, a1, b0, b1, ZD, ZD + 0.10, m["ws_yellow"])
    for i, (b0, b1) in enumerate(((PY0, PY0 + 4.0), (PY0 + 5.0, PY0 + 7.0),
                                  (PY0 + 8.0, PY1))):
        R("hazw%d" % i, PX0 - 0.7, PX0, b0, b1, ZD, ZD + 0.10, m["ws_yellow"])
        R("haze%d" % i, PX1, PX1 + 0.7, b0, b1, ZD, ZD + 0.10, m["ws_yellow"])
    # satellite: pedestal + dark bus + four copper-gold wings + dishes
    _v15_cyl("%s_v15_satped" % tag, t0 + 17.0, v0 + 16.5, ZF + 0.14, ZF + 2.30, 0.9,
             m["dark"], c, 16)
    R("satbus", 15.5, 18.5, 15.0, 18.0, ZF + 2.30, ZF + 3.70, m["metal"])
    R("satbus2", 16.2, 17.8, 15.7, 17.3, ZF + 3.70, ZF + 4.00, m["dark"])
    for i, (ang, off) in enumerate(((16, 2.3), (-16, 2.3), (16, -2.3), (-16, -2.3))):
        cu = 17.0 + off * math.cos(math.radians(ang + 90))
        cv = 16.5 + off * math.sin(math.radians(ang + 90))
        _v15_rot("%s_v15_wing%d" % (tag, i), t0 + cu, v0 + cv, 3.4, 1.35,
                 ZF + 3.72, ZF + 3.86, m["gold"], c, deg=ang)
    _v15_cyl("%s_v15_dish0" % tag, t0 + 19.6, v0 + 18.8, ZF + 3.8, ZF + 3.92, 0.65,
             m["dark"], c, 12)
    _v15_cyl("%s_v15_dish1" % tag, t0 + 15.0, v0 + 14.4, ZF + 3.8, ZF + 3.92, 0.50,
             m["dark"], c, 12)
    # two white arms, different poses, yellow joint rings
    for i, (cu, cv, deg, ln) in enumerate(((13.4, 16.2, 62, 3.6), (20.6, 17.0, -48, 3.4))):
        _v15_cyl("%s_v15_armbase%d" % (tag, i), t0 + cu, v0 + cv, ZF + 0.14, ZF + 2.0,
                 0.62, m["dark"], c, 12)
        _v15_rot("%s_v15_arm%d" % (tag, i), t0 + cu, v0 + cv, ln, 0.55, ZF + 2.0,
                 ZF + 2.45, m["white"], c, deg=deg)
        _v15_cyl("%s_v15_joint%d" % (tag, i), t0 + cu, v0 + cv, ZF + 2.0, ZF + 2.52,
                 0.45, m["ws_yellow"], c, 12)
        dd = math.radians(deg)
        uu = cu + ln * 0.5 * math.cos(dd)
        vv = cv + ln * 0.5 * math.sin(dd)
        _v15_rot("%s_v15_arm2_%d" % (tag, i), t0 + uu, v0 + vv, ln * 0.75, 0.45,
                 ZF + 2.45, ZF + 2.85, m["white"], c, deg=deg + 34)
    # gallery -> wall service band 1.5 m, blue steel
    R("band_n", IN0, IN1, IN0, IN0 + 1.5, ZD, ZD + 0.12, m["cap_h3"])
    R("band_w", IN0, IN0 + 1.5, IN0 + 1.5, IN1, ZD, ZD + 0.12, m["cap_h3"])
    R("band_e", IN1 - 1.5, IN1, IN0 + 1.5, IN1, ZD, ZD + 0.12, m["cap_h3"])
    # three continuous light strips (D6) + six short beats
    R("strip_n", 3.2, 27.8, IN0 + 0.5, IN0 + 1.0, ZD + 0.12, ZD + 0.26, m["h3_strip"])
    R("strip_w", IN0 + 0.5, IN0 + 1.0, 3.2, 27.8, ZD + 0.12, ZD + 0.26, m["h3_strip"])
    R("strip_e", IN1 - 1.0, IN1 - 0.5, 8.0, 27.8, ZD + 0.12, ZD + 0.26, m["h3_strip"])
    for i, (a0, b0) in enumerate(((6.0, 2.6), (12.0, 2.6), (18.0, 2.6),
                                  (6.0, 31.4), (12.0, 31.4), (24.0, 31.4))):
        R("sbeat%d" % i, a0, a0 + 1.8, b0, b0 + 0.5, ZD + 0.12, ZD + 0.26, m["h3_strip"])
    # racks and safes
    for i in range(4):
        R("rack%d" % i, 29.6, 31.9, 13.6 + i * 2.2, 14.8 + i * 2.2, ZD, ZD + 2.4,
          m["metal"])
    for i in range(3):
        R("safe%d" % i, 4.6, 5.8, 13.0 + i * 1.9, 14.2 + i * 1.9, ZD, ZD + 1.5,
          m["dark"])
    for i in range(4):
        R("crate%d" % i, 6.0 + i * 1.6, 7.2 + i * 1.6, 27.4, 28.6, ZD, ZD + 1.0,
          m["container_gray"])
    # one shadow band along the pit west edge (gallery projection)
    R("shade", PX0 + 1.2, PX0 + 2.2, PY0 + 1.2, PY1 - 1.2, ZF + 0.24, ZF + 0.27,
      m["floorshadow"])
    # mid-scale density run B
    for i in range(4):
        for j in range(2):
            R("crateb%d_%d" % (i, j), 12.6 + i * 2.6, 13.8 + i * 2.6,
              24.6 + j * 2.2, 25.8 + j * 2.2, ZD, ZD + 1.0, m["container_gray"])
    for i in range(4):
        for j in range(2):
            R("plateb%d_%d" % (i, j), 25.4 + i * 1.9, 26.6 + i * 1.9,
              26.0 + j * 2.4, 27.2 + j * 2.4, ZD, ZD + 0.22, m["metal"])
    for i in range(6):
        R("wcab%d" % i, 2.2, 3.6, 12.4 + i * 1.9, 13.8 + i * 1.9, ZD, ZD + 1.9,
          m["steel"])
    for i in range(6):
        R("ndrum%d" % i, 12.4 + i * 1.3, 13.3 + i * 1.3, 3.0, 4.2, ZD, ZD + 0.9,
          m["container_olive"] if i % 2 else m["metal"])
    for i in range(4):
        R("etray%d" % i, 24.4, 31.2, 15.2 + i * 2.0, 15.9 + i * 2.0, ZD, ZD + 0.3,
          m["dark"])
    for i in range(6):
        R("scrate%d" % i, 4.0 + i * 1.6, 5.2 + i * 1.6, 25.4, 26.6, ZD, ZD + 1.0,
          m["container_gray"])
    _v15_text("%s_v15_id" % tag, t0, v0, 6.5, 30.0, ZD, ZD + 0.06, "H3", m, c)


# ------------------------------------------------------------------- H4 black
def _v15_h4(tag, t0, v0, z, m, c):
    def R(nm, u0, u1, w0, w1, z0, z1, mat):
        avr("%s_v15_%s" % (tag, nm), t0 + u0, t0 + u1, v0 + w0, v0 + w1, z0, z1, mat, c)

    IN0, IN1 = 0.45, 33.55
    ZF = z + 0.06
    ZD = ZF + 0.24
    R("deck", IN0, IN1, IN0, IN1, ZF, ZD, m["terrace"])
    # green band on the two walls that are green in the real room
    R("green_n", IN0, IN1, IN0, IN0 + 1.2, ZD, ZD + 0.10, m["cap_h4"])
    R("green_e", IN1 - 1.2, IN1, IN0 + 1.2, IN1, ZD, ZD + 0.10, m["cap_h4"])
    # circular hatch: Ø6 ring + 12 radial ribs + hub + inner ring, east side
    _v15_cyl("%s_v15_hatch" % tag, t0 + 28.0, v0 + 17.0, ZD, ZD + 0.14, 3.75,
             m["char_dark"], c, 40)
    _v15_ring("%s_v15_hatch_ring" % tag, t0 + 28.0, v0 + 17.0, 3.62, 0.45, ZD + 0.14,
              ZD + 0.30, m["cope"], c, 40)
    _v15_ring("%s_v15_hatch_ring2" % tag, t0 + 28.0, v0 + 17.0, 2.30, 0.38, ZD + 0.14,
              ZD + 0.28, m["cope"], c, 32)
    for i in range(12):
        a = i * 30.0 + 15.0
        cu = 28.0 + 2.95 * math.cos(math.radians(a))
        cv = 17.0 + 2.95 * math.sin(math.radians(a))
        _v15_rot("%s_v15_rib%d" % (tag, i), t0 + cu, v0 + cv, 1.70, 0.34,
                 ZD + 0.14, ZD + 0.30, m["steel"], c, deg=a)
    _v15_cyl("%s_v15_hub" % tag, t0 + 28.0, v0 + 17.0, ZD + 0.14, ZD + 0.38, 0.85,
             m["ws_yellow"], c, 16)
    # barrel-vault mouth: dark recess pad + two concentric rib arcs + jamb columns
    R("vault", 1.2, 7.2, 2.4, 9.6, ZD, ZD + 0.14, m["char_dark"])
    for i, rr in enumerate((2.0, 3.3, 4.6)):
        _v15_ring("%s_v15_arc%d" % (tag, i), t0 + 6.5, v0 + 6.0, rr, 0.60, ZD + 0.14,
                  ZD + 0.34, m["rib_blue"], c, 40,
                  AV_ROT + math.radians(-90), AV_ROT + math.radians(90))
    for i, ww in enumerate((3.4, 8.6)):
        _v15_cyl("%s_v15_jamb%d" % (tag, i), t0 + 6.5, v0 + ww, ZD, z + 2.8, 0.32,
                 m["white"], c, 12)
    # "日" partition: 2 verticals + 3 horizontals, 1.5 m high with dark cap
    for i, uu in enumerate((12.0, 18.0)):
        R("pv%d" % i, uu, uu + 0.4, 6.0, 14.0, ZD, ZD + 1.2, m["white"])
        R("pvc%d" % i, uu - 0.1, uu + 0.5, 6.0, 14.0, ZD + 1.2, ZD + 1.42, m["cope"])
    # yellow channel arrows so the partitions read as walls, not shelving
    for i, (au, av_, deg) in enumerate(((13.0, 8.6, 0), (16.6, 11.4, 90), (13.0, 12.6, 180))):
        _v15_rot("%s_v15_arrow%d" % (tag, i), t0 + au, v0 + av_, 1.6, 0.45,
                 ZD + 0.14, ZD + 0.24, m["ws_yellow"], c, deg=deg)
        _v15_rot("%s_v15_arrowtip%d" % (tag, i), t0 + au + 0.9, v0 + av_, 0.9, 0.45,
                 ZD + 0.14, ZD + 0.24, m["ws_yellow"], c, deg=deg + 30)
    for i, vv in enumerate((6.0, 10.0, 14.0)):
        R("ph%d" % i, 12.0, 18.0, vv, vv + 0.4, ZD, ZD + 1.2, m["white"])
        R("phc%d" % i, 12.0, 18.0, vv - 0.1, vv + 0.5, ZD + 1.2, ZD + 1.42, m["cope"])
    # overhead crane, single beam
    R("cbeam", 3.0, 31.0, 26.4, 27.6, z + 7.6, z + 8.4, m["steel"])
    _v15_cyl("%s_v15_ctrolley" % tag, t0 + 20.0, v0 + 27.0, z + 8.4, z + 8.9, 0.9,
             m["metal"], c, 12)
    _v15_hcyl("%s_v15_cpod" % tag, t0 + 20.0, v0 + 27.0, z + 6.0, 3.0, 0.75, m["dark"],
              c, 90, 16)
    for i, cu in enumerate((19.6, 20.4)):
        _v15_cyl("%s_v15_ccab%d" % (tag, i), t0 + cu, v0 + 27.0, z + 6.6, z + 8.4, 0.05,
                 m["dark"], c, 4)
    # 4x4 black lift shaft with a 3 m gap in the railing
    R("shaft", 29.0, 33.0, 3.0, 7.0, ZD, ZD + 0.5, m["pit"])
    for i, (a0, a1, b0, b1) in enumerate(((29.0, 33.0, 3.0, 3.25),
                                          (29.0, 29.25, 3.25, 5.0),
                                          (32.75, 33.0, 3.25, 7.0))):
        R("srail%d" % i, a0, a1, b0, b1, ZD + 0.5, ZD + 1.1, m["ws_yellow"])
    # military crates, 4x2 grid
    for i in range(4):
        for j in range(2):
            R("mil%d_%d" % (i, j), 4.0 + i * 2.0, 5.4 + i * 2.0, 28.6 + j * 1.1,
              29.4 + j * 1.1, ZD, ZD + 0.9, m["container_olive"] if (i + j) % 2
              else m["sand"])
    for i in range(4):
        R("blackbox%d" % i, 8.0 + i * 1.4, 9.1 + i * 1.4, 31.6, 32.6, ZD, ZD + 0.8,
          m["dark"])
    # arms + satellite, one arm raised (same kit as H3, different pose)
    _v15_cyl("%s_v15_armbase" % tag, t0 + 21.2, v0 + 22.4, ZD, ZD + 1.0, 0.6,
             m["dark"], c, 12)
    _v15_rot("%s_v15_arm" % tag, t0 + 21.2, v0 + 22.4, 3.4, 0.5, ZD + 1.0, ZD + 1.4,
             m["white"], c, deg=112)
    _v15_cyl("%s_v15_joint" % tag, t0 + 21.2, v0 + 22.4, ZD + 1.0, ZD + 1.45, 0.42,
             m["ws_yellow"], c, 12)
    R("sat", 19.4, 21.2, 20.2, 22.0, ZD + 1.4, ZD + 2.4, m["metal"])
    for i, ang in enumerate((30, -30, 150, -150)):
        _v15_rot("%s_v15_wing%d" % (tag, i), t0 + 20.3, v0 + 21.1, 1.9, 0.8,
                 ZD + 1.8, ZD + 1.92, m["steel"], c, deg=ang)
    for i in range(4):
        R("ecab%d" % i, 24.2, 25.6, 6.0 + i * 2.4, 7.6 + i * 2.4, ZD, ZD + 2.0, m["steel"])
    for i in range(6):
        R("eplate%d" % i, 20.6 + (i % 3) * 2.4, 21.8 + (i % 3) * 2.4,
          24.6 + (i // 3) * 2.4, 25.8 + (i // 3) * 2.4, ZD, ZD + 0.05, m["floorshadow"])
    R("ehose", 22.0, 26.0, 21.0, 21.6, ZD, ZD + 0.8, m["orange"])
    # red/blue pipe runs on the floor to the north then east
    R("pipe_r", IN0, 26.0, 1.75, 2.1, ZD + 0.10, ZD + 0.34, m["orange"])
    R("pipe_b", 25.6, 26.0, 1.75, 20.0, ZD + 0.10, ZD + 0.34, m["evac_blue"])
    # mid-scale density run B
    for i in range(4):
        for j in range(2):
            R("palletb%d_%d" % (i, j), 8.0 + i * 1.9, 9.2 + i * 1.9,
              21.6 + j * 1.6, 22.6 + j * 1.6, ZD, ZD + 0.8, m["container_olive"])
    for i in range(6):
        R("wdrum%d" % i, 4.0 + i * 1.3, 4.9 + i * 1.3, 19.2, 20.4, ZD, ZD + 0.9,
          m["metal"] if i % 2 else m["sand"])
    for i in range(6):
        R("ntray%d" % i, 20.0 + i * 2.0, 21.4 + i * 2.0, 2.4, 3.2, ZD, ZD + 0.3,
          m["dark"])
    for i in range(4):
        R("seplate%d" % i, 26.4 + (i % 2) * 2.4, 27.6 + (i % 2) * 2.4,
          10.0 + (i // 2) * 2.4, 11.2 + (i // 2) * 2.4, ZD, ZD + 0.2, m["metal"])
    # one shadow pair: crane-beam band + arch-mouth light
    R("shade_beam", 3.0, 31.0, 26.9, 28.1, ZD + 0.24, ZD + 0.42, m["floorshadow"])
    R("shade_arch", 6.6, 9.4, 4.6, 7.4, ZD + 0.06, ZD + 0.10, m["garden_coping"])
    for i in range(5):
        R("spallet%d" % i, 24.0, 25.2, 14.0 + i * 1.6, 15.0 + i * 1.6, ZD, ZD + 0.9,
          m["container_olive"] if i % 2 else m["sand"])
    _v15_text("%s_v15_id" % tag, t0, v0, 17.0, 31.0, ZD, ZD + 0.06, "H4", m, c)
def build_core_v11(m):
    c = coll("CORE")
    z = PLATFORM_Z
    for name, t0, t1, v0, v1 in HALLS:
        tc = (t0 + t1) / 2.0
        vc = (v0 + v1) / 2.0
        avr(f"{name.lower()}_floor", t0, t1, v0, v1, z, z + 0.06, m["floor_ind"], c)
        # v12: 墙脚暗带 + 6 m 地坪分仓缝（敞顶后室内地坪是俯视最大可见面，必须出结构）
        for tag, (a0, a1, b0, b1) in {
                "n": (t0 + 0.45, t0 + 1.55, v0 + 0.4, v1 - 0.4),
                "s": (t1 - 1.55, t1 - 0.45, v0 + 0.4, v1 - 0.4),
                "w": (t0 + 0.4, t1 - 0.4, v0 + 0.45, v0 + 1.55),
                "e": (t0 + 0.4, t1 - 0.4, v1 - 1.55, v1 - 0.45)}.items():
            avr(f"{name.lower()}_fshadow_{tag}", a0, a1, b0, b1, z + 0.060, z + 0.066,
                m["floorshadow"], c)
        k = 0
        tt = t0 + 6.0
        while tt < t1 - 3.0:
            avr(f"{name.lower()}_joint_t{k}", tt - 0.08, tt + 0.08, v0 + 0.5, v1 - 0.5,
                z + 0.060, z + 0.067, m["joint"], c)
            tt += 6.0
            k += 1
        k = 0
        vv = v0 + 6.0
        while vv < v1 - 3.0:
            avr(f"{name.lower()}_joint_v{k}", t0 + 0.5, t1 - 0.5, vv - 0.08, vv + 0.08,
                z + 0.060, z + 0.067, m["joint"], c)
            vv += 6.0
            k += 1
        # outer walls
        avr(f"{name.lower()}_wall_n", t0, t0 + 0.45, v0, v1, z, z + HALL_H, m["wall"], c)
        avr(f"{name.lower()}_wall_s", t1 - 0.45, t1, v0, v1, z, z + HALL_H, m["wall"], c)
        # corridor-facing wall gets a 6 m roller door
        side = v1 if v0 > 0 else v0
        avr(f"{name.lower()}_wall_c", t0, t1, side - 0.22, side + 0.22, z, z + HALL_H,
            m["wall"], c)
        roller_door(f"{name.lower()}_rdoor", t0 + 6.0 if name in ("H1", "H3") else t1 - 6.0,
                    side, 6.0, 5.0, z, m, c, face=1.0)
        # r14: no roof slab and no parapet -- the halls stay open so the map reads inside
        # v12: 墙顶改成 0.55 m 深色压顶（顶视 3.9 px 深线），替代原来的 0.3 m 浅钢带
        for tag, (a0, a1, b0, b1) in {
                "n": (t0 - 0.05, t0 + 0.50, v0 - 0.05, v1 + 0.05),
                "s": (t1 - 0.50, t1 + 0.05, v0 - 0.05, v1 + 0.05),
                "w": (t0 - 0.05, t1 + 0.05, v0 - 0.05, v0 + 0.50),
                "e": (t0 - 0.05, t1 + 0.05, v1 - 0.50, v1 + 0.05)}.items():
            avr(f"{name.lower()}_up_{tag}", a0, a1, b0, b1, z + HALL_H, z + HALL_H + 0.18,
                m.get("cap_%s" % name.lower(), m["cope"]), c)
        fit_out(name, t0, t1, v0, v1, z, m, c)
        # facade kit
        double_door(f"{name.lower()}_ndoor", t0, vc, z, m, c, face=-1.0)
        panel_joints_t(f"{name.lower()}_pj_n", t0, v0, v1, z, HALL_H, -1.0, m, c)
        av_box(f"{name.lower()}_band_n", t0 - 0.34, vc, 0.06, v1 - v0 - 0.6, z + 9.6, z + 10.2,
               m["evac_blue"] if name in ("H1", "H4") else m["dark"], c)
        # (r14: rooftop AHUs removed together with the roof)

    # cross corridor: N-S (v -5..5) and E-W (t -52..-42), glass roof at 7.5
    avr("corr_ns", CORE_TN, CORE_TS, -5.0, 5.0, z, z + 0.058, m["garden_walk"], c)
    avr("corr_ew", -52.0, -42.0, -CORE_HALF, CORE_HALF, z + 0.001, z + 0.050,
        m["garden_walk"], c)
    # (r14: the corridor glazing is gone -- only the open truss frame remains)
    for k, tt in enumerate((-82.0, -74.0, -66.0, -58.0, -46.0, -38.0, -30.0, -22.0, -14.0)):
        avr(f"corr_truss{k}", tt - 0.22, tt + 0.22, -5.0, 5.0, z + 7.5, z + 8.7, m["steel"], c)
    for k, vv in enumerate((-34.0, -22.0, -10.0, 10.0, 22.0, 34.0)):
        avr(f"corr_beam{k}", -52.0, -42.0, vv - 0.22, vv + 0.22, z + 7.5, z + 8.7, m["steel"], c)
    avr("corr_kerb_ns", CORE_TN, CORE_TS, -5.4, -5.0, z, z + 0.06, m["yellow"], c)
    avr("corr_kerb_ns2", CORE_TN, CORE_TS, 5.0, 5.4, z, z + 0.06, m["yellow"], c)


    # 12 m loading strip along the south wall (4 roller doors)
    avr("load_deck", CORE_TS, CORE_TS + 3.6, -CORE_HALF, CORE_HALF, z, z + 1.10,
        m["container_gray"], c)
    avr("load_deck_top", CORE_TS, CORE_TS + 3.62, -CORE_HALF, CORE_HALF, z + 1.10, z + 1.16,
        m["dark"], c)
    avr("load_ramp", CORE_TS + 3.6, CORE_TS + 4.8, -CORE_HALF, CORE_HALF, z, z + 0.55,
        m["container_gray"], c)
    for k, vv in enumerate((-28.0, -13.0, 13.0, 28.0)):
        roller_door(f"load_door{k}", CORE_TS, vv, 6.0, 4.6, z + 1.10, m, c, face=1.0)
        canopy(f"load_canopy{k}", CORE_TS, vv, z + 5.9, m, c, face=1.0, w=6.4, d=2.4)
    print("CORE_OK")


def strip_h_open(name, y, x0, x1, z0, z1, openings, mat, c, w=0.7):
    pos, idx = x0, 0
    for a, b in sorted(openings):
        if a > pos:
            add_box(f"{name}_{idx}", pos, a, y - w / 2, y + w / 2, z0, z1, mat, c)
            idx += 1
        pos = max(pos, b)
    if pos < x1:
        add_box(f"{name}_{idx}", pos, x1, y - w / 2, y + w / 2, z0, z1, mat, c)


def strip_v_open(name, x, y0, y1, z0, z1, openings, mat, c, w=0.7):
    pos, idx = y0, 0
    for a, b in sorted(openings):
        if a > pos:
            add_box(f"{name}_{idx}", x - w / 2, x + w / 2, pos, a, z0, z1, mat, c)
            idx += 1
        pos = max(pos, b)
    if pos < y1:
        add_box(f"{name}_{idx}", x - w / 2, x + w / 2, pos, y1, z0, z1, mat, c)


def build_wall_layers(m):
    """Coping strips on wall tops (readable from above) + floor skirt bands."""
    c = coll("WALL_LAYERS")
    z = PLATFORM_Z
    cop = {k: make_mat(f"v4.coping.{k}", v, 0.55) for k, v in COPING.items()}
    skirt = make_mat("v4.skirt", "#4A5254", 0.85)
    G1 = (88.4, 91.6)
    G2 = (148.4, 151.6)
    E1 = (88.4, 91.6)
    E2 = (148.4, 151.6)
    E3 = (88.4, 91.6)
    E4 = (148.4, 151.6)
    plan = [
        ("H1", 8.4, [("h", 0, 60, 120, [E1]), ("h", 60, 60, 120, [G1]),
                     ("v", 60, 0, 60, []), ("v", 120, 0, 60, [])]),
        ("H2", 8.4, [("h", 120, 60, 120, [E3]), ("v", 60, 60, 120, []), ("v", 120, 60, 120, [])]),
        ("H3", 8.4, [("h", 120, 120, 180, [E4]), ("v", 180, 60, 120, []), ("v", 120, 60, 120, [])]),
        ("H4", 12.4, [("h", 0, 120, 180, [E2]), ("h", 60, 120, 180, [G2]),
                      ("v", 180, 0, 60, [])]),
    ]
    for room, hh, walls in plan:
        mat = cop[room]
        for kind, fixed, a0, a1, ops in walls:
            if kind == "h":
                strip_h_open(f"cop_{room}_{fixed}", fixed, a0, a1, z + hh, z + hh + 0.12, ops, mat, c)
            else:
                strip_v_open(f"cop_{room}_{fixed}", fixed, a0, a1, z + hh, z + hh + 0.12, ops, mat, c)
    # floor skirt bands along all inner faces
    skirts = [
        ("h", 0.9, 60.6, 119.4, [E1]), ("h", 59.1, 60.6, 119.4, [G1]), ("v", 60.9, 0.6, 59.4, []),
        ("v", 119.1, 0.6, 59.4, []),
        ("h", 60.9, 60.6, 119.4, [G1]), ("h", 119.1, 60.6, 119.4, [E3]), ("v", 60.9, 60.6, 119.4, []),
        ("v", 119.1, 60.6, 119.4, []),
        ("h", 60.9, 120.6, 179.4, [G2]), ("h", 119.1, 120.6, 179.4, [E4]), ("v", 120.9, 60.6, 119.4, []),
        ("v", 179.1, 60.6, 119.4, []),
        ("h", 0.9, 120.6, 179.4, [E2]), ("h", 59.1, 120.6, 179.4, [G2]), ("v", 120.9, 0.6, 59.4, []),
        ("v", 179.1, 0.6, 59.4, []),
    ]
    for i, (kind, fx, a0, a1, ops) in enumerate(skirts):
        if kind == "h":
            strip_h_open(f"skirt_{i}", fx, a0, a1, z + 0.055, z + 0.07, ops, skirt, c, w=0.9)
        else:
            strip_v_open(f"skirt_{i}", fx, a0, a1, z + 0.055, z + 0.07, ops, skirt, c, w=0.9)


def add_floor_grid(name, x0, x1, y0, y1, step, z, width, mat, c):
    verts, faces = [], []
    def quad(ax, ay, bx, by):
        i = len(verts)
        verts.extend([(ax, ay, z), (bx, ay, z), (bx, by, z), (ax, by, z)])
        faces.append((i, i + 1, i + 2, i + 3))
    x = x0 + step
    while x < x1 - 0.01:
        quad(x - width / 2, y0, x + width / 2, y1)
        x += step
    y = y0 + step
    while y < y1 - 0.01:
        quad(x0, y - width / 2, x1, y + width / 2)
        y += step
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.validate(); mesh.update()
    _mesh_obj(name, mesh, mat, c)


def build_floor_joints(m):
    c = coll("JOINTS")
    mat = make_mat("v5.joint", "#6E6A60", 0.9)
    for key, (x0, x1, y0, y1) in ROOMS.items():
        add_floor_grid(f"joint_{key}", x0 + 0.3, x1 - 0.3, y0 + 0.3, y1 - 0.3, 6.0,
                       PLATFORM_Z + 0.055, 0.028, mat, c)


def build_floor_marks(m):
    c = coll("FLOOR_MARKS")
    z = PLATFORM_Z
    pale = m["h3"] if "h3" in m else m["platform"]
    zone = make_mat("v4.zone", "#9BA4A4", 0.9)
    liney = make_mat("v4.line_y", "#E0B23A", 0.6)
    linew = make_mat("v4.line_w", "#E6EAEA", 0.7)
    # H1 annular floor ring + 4 radial lines
    add_tube("m_h1_ring", 90, 30, 19.0, 10.0, z + 0.05, z + 0.065, zone, c, 48)
    for i in range(4):
        a = math.radians(45 + i * 90)
        add_box_local(f"m_h1_rad_{i}", 90 + 14.5 * math.cos(a), 30 + 14.5 * math.sin(a),
                      z + 0.066, 9.0, 0.25, 0.012, liney, c, rot_z=a)
    # H2 pool safety ring (4 strips) + zone
    for i, (a0, a1, b0, b1) in enumerate(((62, 118, 78, 79), (62, 118, 101, 102),
                                          (62, 68, 79, 101), (104, 118, 79, 101))):
        add_box(f"m_h2_zone_{i}", a0, a1, b0, b1, z + 0.05, z + 0.062, zone, c)
    for (a0, a1, b0, b1) in ((66.8, 105.2, 77.8, 78.1), (66.8, 105.2, 101.9, 102.2),
                             (66.8, 67.1, 78, 102), (104.9, 105.2, 78, 102)):
        add_box("m_h2_line_%d" % a0, a0, a1, b0, b1, z + 0.063, z + 0.075, liney, c)
    # H3 zone (blue-gray) + hazard at ramp
    for i, (a0, a1, b0, b1) in enumerate(((130, 172, 74, 79), (130, 172, 101, 106),
                                          (130, 136, 79, 101), (160, 172, 79, 101))):
        add_box(f"m_h3_zone_{i}", a0, a1, b0, b1, z + 0.05, z + 0.062, m["zone_blue"], c)
    for i in range(3):
        add_box(f"m_h3_haz_{i}", 160, 166, 86.5 + i * 2, 87.5 + i * 2, z + 0.063, z + 0.075, liney, c)
    # H4 assembly zone + hazard at hatch
    for i, (a0, a1, b0, b1) in enumerate(((140, 162, 28, 46),)):
        add_box(f"m_h4_zone_{i}", a0, a1, b0, b1, z + 0.05, z + 0.062, zone, c)
    for i in range(3):
        add_box(f"m_h4_haz_{i}", 171 + i * 1.6, 172.2 + i * 1.6, 20, 25, z + 0.063, z + 0.075, liney, c)
    # zebra at six doors (3 strips each)
    doors = [(90, 0.9, "h"), (150, 0.9, "h"), (90, 59.1, "h"), (150, 59.1, "h"),
             (90, 119.1, "h"), (150, 119.1, "h")]
    for d_i, (dx, dy, _) in enumerate(doors):
        for k in range(3):
            off = (k - 1) * 1.1
            add_box(f"zebra_{d_i}_{k}", dx - 2.2, dx - 1.6, dy + off - 0.3, dy + off + 0.3,
                    z + 0.063, z + 0.075, linew, c)
    # (v07: garden path ring removed with the garden, Q2)
    for k in range(3):
        add_box(f"zebra_g_{k}", 112, 128, -15.3 + k * 1.1, -14.7 + k * 1.1,
                z + 0.05, z + 0.062, linew, c)


def build_room_extras(m):
    c = coll("ROOM_EXTRAS")
    z = PLATFORM_Z
    IND["on"] = True
    # H1 sign + circular wall coping ring
    add_box("x_h1_sign", 119.4, 119.65, 26, 34, z + 3.4, z + 4.4, m["evac_blue"], c)
    add_tube("x_h1_coping", 90, 30, 22.15, 21.9, z + 9.0, z + 9.12,
             make_mat("v6.h1_cop", "#7195A4", 0.55), c, 40)
    # H2 pipe group + valves + external stair
    for i in range(4):
        add_cyl_h(f"x_h2_pipe_{i}", 84, 75.6 + i * 0.55, z + 0.5, 34.0, 0.2, m["metal"], c,
                  vertices=10)
    for i, x in enumerate((104, 107, 110)):
        add_box(f"x_h2_valve_{i}", x - 0.6, x + 0.6, 75.2, 78.2, z + 0.0, z + 2.0, m["orange"], c)
    add_box("x_h2_stair", 74, 76, 106, 113, z + 0.2, z + 2.6, m["steel"], c)
    # H3 hoist + cable trays
    add_cyl("x_h3_hoist", 148, 96, z + 4.0, z + 10.0, 0.15, m["metal"], c, vertices=8)
    add_box("x_h3_hook", 147.5, 148.5, 95.5, 96.5, z + 3.6, z + 4.2, m["dark"], c)
    add_box("x_h3_tray_w", 120.55, 120.95, 62, 118, z + 2.0, z + 2.06, m["metal"], c)
    add_box("x_h3_tray_n", 122, 178, 119.05, 119.45, z + 2.0, z + 2.06, m["metal"], c)
    # H4 ceiling pipes + hanging signs + vault light strips
    for i, (yy, zz) in enumerate(((12, 6.3), (20, 6.6))):
        add_cyl_h(f"x_h4_pipe_{i}", 150, yy, z + zz, 58.0, 0.15, m["metal"], c, vertices=8)
    for i, yy in enumerate((49.5, 58.5)):
        add_box(f"x_h4_psign_{i}", 147, 153, yy - 0.1, yy + 0.1, z + 4.0, z + 4.7, m["yellow"], c)
    for i, xx in enumerate((146.2, 153.6)):
        add_box(f"x_h4_vlight_{i}", xx, xx + 0.3, 49, 59, z + 7.5, z + 7.62, m["emis"], c)
    IND["on"] = False
    # dock: gratings, sump, lane lines, gate zebra
    dc = coll("DOCK_EXTRA")
    dock_box("x_grate_u76", 76, 0, 1.2, 10, 0.0, 0.04, m["dark"], dc)
    dock_box("x_grate_u88", 88, 0, 1.2, 10, 0.0, 0.04, m["dark"], dc)
    dock_box("x_sump", 6, -22, 2, 2, 0.0, 0.05, m["dark"], dc)
    dock_box("x_lane_w", 48, -8, 78, 0.2, 0.0, 0.04, m["yellow"], dc)
    dock_box("x_lane_e", 48, 8, 78, 0.2, 0.0, 0.04, m["yellow"], dc)
    for k in range(4):
        dock_box(f"x_zebra_{k}", 2.5, -6 + k * 4, 1.0, 2.2, 0.0, 0.04, m["white"], dc)


def build_outdoor_props(m):
    c = coll("OUTDOOR")
    z = PLATFORM_Z
    pole = m["metal"]
    # ring-road lamps x14 (east/north rows moved onto the outer bands, Q1)
    lamps = [(82, -5.2), (108, -5.2), (134, -5.2), (158, -5.2),
             (178.6, 20), (178.6, 60), (178.6, 100),
             (82, 118.6), (108, 118.6), (134, 118.6), (158, 118.6),
             (54.8, 100), (54.8, 60), (54.8, 20)]
    for i, (x, y) in enumerate(lamps):
        add_cyl(f"rd_lamp_{i}", x, y, z, z + 6.0, 0.15, pole, c, vertices=8)
        add_cyl(f"rd_lamp_head_{i}", x, y, z + 5.9, z + 6.25, 0.45, m["emis"], c, vertices=10)
    # bollards x14 (east/north rows moved onto the outer bands)
    bolls = [(84, -5.8), (108, -5.8), (132, -5.8), (156, -5.8),
             (178.4, 24), (178.4, 48), (178.4, 72), (178.4, 96),
             (156, 118.4), (132, 118.4), (108, 118.4), (84, 118.4),
             (54.6, 96), (54.6, 72), (54.6, 48), (54.6, 24)]
    for i, (x, y) in enumerate(bolls):
        add_cyl(f"boll_{i}", x, y, z, z + 0.5, 0.28, m["dark"], c, vertices=8)
    # life rings x8 (east/north pairs moved onto the outer bands)
    rings = [(74, -5.8), (160, -5.8), (178.4, 8), (178.4, 112),
             (74, 118.4), (160, 118.4), (54.6, 112), (54.6, 8)]
    for i, (x, y) in enumerate(rings):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.45, minor_radius=0.12,
                                         location=(x, y, z + 0.5))
        o = bpy.context.object
        o.name = f"ring_{i}"
        for cc in list(o.users_collection):
            cc.objects.unlink(o)
        c.objects.link(o)
        o.data.materials.append(m["orange"])
    # benches x8 on ring road inner side
    benches = [((100, -4), 0), ((140, -4), 0), ((177, 20), 90), ((177, 100), 90),
               ((100, 117.5), 0), ((140, 117.5), 0), ((63, 20), 90), ((63, 100), 90)]
    for i, ((x, y), ang) in enumerate(benches):
        add_box_local(f"bench_rd_{i}", x, y, z + 0.25, 1.8, 0.6, 0.5, m["wood"], c,
                      rot_z=math.radians(ang))
    # barriers x4 at the two west viewing platforms (east pair removed with margin)
    for i, (x, y) in enumerate(((56, 10), (62, 20), (56, 100), (62, 110))):
        add_box_local(f"barrier_{i}", x, y, z + 0.55, 1.6, 0.5, 1.1, m["orange"], c,
                      rot_z=math.radians(0))
    # container clusters x3 (west near gate; the SE trio moved to the east band)
    for i, (x, y, ang) in enumerate(((20, 44, 90), (20, 52, 90), (26, 44, 90))):
        add_box_local(f"oc_{i}", x, y, z + 1.3, 6, 2.4, 2.6,
                      [m["container_blue"], m["container_olive"], m["container_gray"]][i % 3],
                      c, rot_z=math.radians(ang))
    # direction signs x2
    for i, (x, y, ang) in enumerate(((126, -5.2, 0), (164, -60, 32))):
        add_box_local(f"dsign_{i}", x, y, z + 2.2, 2.6, 0.1, 0.9, m["evac_blue"], c,
                      rot_z=math.radians(ang))
        add_cyl(f"dsign_pole_{i}", x, y, z, z + 2.2, 0.08, pole, c, vertices=6)
    # (v07: garden benches/bins removed with the garden, Q2)
    # (v10: the legacy causeway pipe rack + its 3 lamps were removed -- they ran
    #  straight through the garden at v=-6.4 and floated 4.5 m over the new deck.
    #  K10 is now the single pipe rack, on the west edge with piles and vaults.)
    # viewing platform lamps x4 (east pair moved onto the island)
    for i, (x, y) in enumerate(((177, 18), (177, 102), (59.5, 102), (59.5, 18))):
        add_cyl(f"vp_lamp_{i}", x, y, z, z + 4.5, 0.12, pole, c, vertices=6)
        add_cyl(f"vp_lamp_head_{i}", x, y, z + 4.4, z + 4.65, 0.35, m["emis"], c, vertices=8)



# ------------------------------------------------------------------ v5 upgrade helpers
ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                      "art", "static_map", "space_base_minigame", "v06", "assets")


def mottle(m, scale=0.05, amp=0.08, rough_lo=None, rough_hi=None):
    """Procedural base-colour + roughness variation (no external textures)."""
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    if b is None:
        return
    base = tuple(b.inputs["Base Color"].default_value)[:3]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 3.0
    nz.inputs["Roughness"].default_value = 0.55
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.32
    ramp.color_ramp.elements[0].color = (*[c * (1 - amp) for c in base], 1.0)
    ramp.color_ramp.elements[1].position = 0.68
    ramp.color_ramp.elements[1].color = (*[min(1.0, c * (1 + amp)) for c in base], 1.0)
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    if rough_lo is not None:
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.25
        mr.inputs["From Max"].default_value = 0.75
        mr.inputs["To Min"].default_value = rough_lo
        mr.inputs["To Max"].default_value = rough_hi
        nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])


def water_bump(m, scale=0.45, strength=0.18):
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 4.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = 0.4
    nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])


def card_material(name, filename):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    tex = m.node_tree.nodes.new("ShaderNodeTexImage")
    img = bpy.data.images.load(os.path.join(ASSETS, filename), check_existing=True)
    tex.image = img
    m.node_tree.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    m.node_tree.links.new(tex.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.82
    return m


def add_card(name, cx, cy, z0, w, h, mat, c, rot_z=0.0, vertical=True):
    mesh = bpy.data.meshes.new(name)
    if vertical:
        verts = [(-w / 2, 0, 0), (w / 2, 0, 0), (w / 2, 0, h), (-w / 2, 0, h)]
    else:
        verts = [(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)]
    mesh.from_pydata(verts, [], [(0, 1, 2, 3)])
    mesh.validate(); mesh.update()
    uv = mesh.uv_layers.new()
    for i, co in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[i].uv = co
    obj = _mesh_obj(name, mesh, mat, c)
    obj.location = (cx, cy, z0)
    obj.rotation_euler = (0.0, 0.0, rot_z)
    return obj


def build_cards(m):
    """Grass clumps, bushes and palm crowns from hand-drawn alpha cards."""
    c = coll("VEG_CARDS")
    gm, bm, pm = card_material("v5.grass", "card_grass.png"), \
        card_material("v5.bush", "card_bush.png"), card_material("v5.palm", "card_palm.png")
    # palms: crown card + 2 crossed side cards, on the island margins (Q2)
    for i, (x, y) in enumerate(PALMS):
        old = bpy.data.objects.get(f"palm_crown_{i}")
        if old:
            bpy.data.objects.remove(old, do_unlink=True)
        add_card(f"palm_crown_card_{i}", x, y, PLATFORM_Z + 7.0, 9.0, 9.0, pm, c,
                 rot_z=math.radians(i * 37), vertical=False)
        for k in range(2):
            add_card(f"palm_side_{i}_{k}", x, y, PLATFORM_Z + 4.6, 7.0, 4.2, pm, c,
                     rot_z=math.radians(k * 90 + i * 23), vertical=True)
    # v12 garden palms: 8, crown card + one side card each
    for i, (tt, vv) in enumerate(GARDEN_PALMS):
        x, y = av(tt, vv)
        add_card(f"gpalm_card_{i}", x, y, GARDEN_Z + 6.2, 5.6, 5.6, pm, c,
                 rot_z=math.radians(i * 47), vertical=False)
        add_card(f"gpalm_side_{i}_0", x, y, GARDEN_Z + 4.2, 4.2, 2.9, pm, c,
                 rot_z=math.radians(i * 31), vertical=True)
    # r10 forecourt palms
    for i, tt in enumerate((14.0, 22.0, 30.0, 38.0)):
        for side in (-1, 1):
            x, y = av(tt, side * 13.6)
            add_card(f"fc_palm_card_{i}_{side}", x, y, GARDEN_Z + 7.0, 6.6, 6.6, pm, c,
                     rot_z=math.radians(i * 29 + (0 if side > 0 else 61)), vertical=False)
            add_card(f"fc_palm_side_{i}_{side}_0", x, y, GARDEN_Z + 4.6, 5.0, 3.4, pm, c,
                     rot_z=math.radians(i * 19 + (0 if side > 0 else 37)), vertical=True)
    print("CARDS palms=%d garden=%d forecourt=%d" % (len(PALMS), 32, 8))


def build_shore(m):
    """Shallow-water band + wet edge around platform, garden and dock."""
    c = coll("SHORE")
    shallow = make_mat("v5.shallow", "#2E5A5F", 0.25, 0.0, 1.0, "#1C3C40", 0.35)
    z0, z1 = -0.34, -0.07
    pts = fan_poly()
    cx = sum(q[0] for q in pts) / len(pts)
    cy = sum(q[1] for q in pts) / len(pts)
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        a2 = (cx + (a[0] - cx) * 1.045, cy + (a[1] - cy) * 1.045)
        b2 = (cx + (b[0] - cx) * 1.045, cy + (b[1] - cy) * 1.045)
        add_prism(f"shore_fan_{i}", [a, b, b2, a2], z0, z1, shallow, c)
    # (v11: dock shore bands kept only around the peninsula proper)
    for i, quad in enumerate([[(104, -33), (104, 33), (109, 33), (109, -33)]]):
        add_prism(f"shore_dock_{i}", [dock_world(*q) for q in quad], z0, z1, shallow, c)


def build_ridges(m):
    """Three distant ridges for the promo views (M3).

    Hero looks from (-42,-236,168) toward (122,6) at pitch ~30 deg: the frame top
    sits ~20 deg below the horizon, so ANY ridge beyond the target is above the
    frame and cannot appear in the official hero — this is geometric, not a bug.
    The ridges ARE visible from the 17 deg / 8 deg promo cameras (hero_wide/low).
    Ribbons perpendicular to the view direction at 340/400/450 m."""
    c = coll("RIDGE")
    cols = ["#8494A0", "#6E808C", "#586A76"]
    dx, dy = 0.561, 0.827          # view direction (normalized)
    px_, py_ = dy, -dx             # perpendicular
    tx, ty = 122.0, 6.0            # hero target
    # hero framing: pitch -29 deg, half-FOV 9.9 deg -> an object at distance D
    # enters the frame only if height H <= 168 - 0.346*D (else it is above frame top)
    for i, (dist, hmax) in enumerate(((340.0, 50.0), (400.0, 29.0), (450.0, 12.0))):
        mat = make_mat(f"v6.ridge{i}", cols[i], 0.95)
        cx, cy = tx + dx * dist, ty + dy * dist
        n = 24
        half = 900.0
        pts = []
        for k in range(n + 1):
            t = -half + 2 * half * k / n
            h = hmax * (0.55 + 0.45 * math.sin(k * 1.7 + i * 2.1) ** 2)
            pts.append((cx + px_ * t, cy + py_ * t, h))
        verts = [(p[0], p[1], -2) for p in pts] + [(p[0], p[1], p[2]) for p in pts]
        faces = []
        for k in range(n):
            faces.append((k, k + 1, n + 1 + k + 1, n + 1 + k))
        mesh = bpy.data.meshes.new(f"ridge_{i}")
        mesh.from_pydata(verts, [], faces)
        mesh.validate(); mesh.update()
        _mesh_obj(f"ridge_{i}", mesh, mat, c)


def build_hero_fog():
    """Volume scatter cube, rendered only for the hero view (M3)."""
    c = coll("FOG")
    m = bpy.data.materials.new("v6.fog")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    sc = nt.nodes.new("ShaderNodeVolumeScatter")
    sc.inputs["Color"].default_value = (*hex_rgba("#42566A")[:3], 1.0)
    sc.inputs["Density"].default_value = 0.0008
    nt.links.new(sc.outputs["Volume"], out.inputs["Volume"])
    add_box("HeroFog", -450, 750, -800, 600, -60, 420, m, c)
    bpy.data.objects["HeroFog"]["is_fog"] = True


def build_equipment(m):
    """Four readable functional groups (one per room)."""
    c = coll("EQUIP")
    z = PLATFORM_Z
    # H1: two chairs + cable reel beside the console
    for i, (x, y) in enumerate(((104, 40), (106, 43))):
        add_box(f"eq_h1_seat_{i}", x - 0.45, x + 0.45, y - 0.45, y + 0.45, z + 0.45, z + 0.5,
                m["dark"], c)
        add_box(f"eq_h1_back_{i}", x - 0.45, x + 0.45, y + 0.35, y + 0.45, z + 0.5, z + 1.05,
                m["dark"], c)
        for dx, dy in ((-0.35, -0.35), (0.35, -0.35), (-0.35, 0.35), (0.35, 0.35)):
            add_box(f"eq_h1_leg_{i}_{dx}_{dy}", x + dx - 0.04, x + dx + 0.04, y + dy - 0.04,
                    y + dy + 0.04, z, z + 0.45, m["steel"], c)
    add_cyl("eq_h1_reel", 100, 44, z + 0.2, z + 1.4, 0.7, m["orange"], c, axis="Y", vertices=14)
    add_box("eq_h1_strip", 96, 112, 24, 25.2, z + 0.052, z + 0.062, m["zone_light"], c)
    add_box("eq_h1_crate_a", 70, 73, 44, 47, z, z + 1.2, m["dark"], c)
    add_box("eq_h1_crate_b", 106, 109, 12, 15, z, z + 1.0, m["dark"], c)
    # H2: two pump bodies on the deck near the pipe group
    for i, x in enumerate((78, 82)):
        add_cyl(f"eq_h2_pump_{i}", x, 74.8, z, z + 1.5, 0.75, m["steel"], c, vertices=16)
        add_box(f"eq_h2_motor_{i}", x - 0.6, x + 0.6, 73.2, 74.2, z + 0.2, z + 1.2,
                m["container_olive"], c)
        add_cyl(f"eq_h2_riser_{i}", x, 74.8, z + 1.5, z + 2.6, 0.18, m["metal"], c, vertices=10)
    # H3: three electrical cabinets with door seams along the west wall
    for i, y in enumerate((70, 74, 78)):
        add_box(f"eq_h3_cab_{i}", 121.2, 121.8, y - 1.6, y + 1.6, z, z + 2.2, m["white"], c)
        add_box(f"eq_h3_seam_{i}", 121.78, 121.84, y - 0.02, y + 0.02, z + 0.2, z + 2.0,
                m["dark"], c)
        add_box(f"eq_h3_vent_{i}", 121.75, 121.82, y - 1.2, y + 1.2, z + 1.7, z + 1.95,
                m["metal"], c)
    # H4: tool rack + tool chest
    add_box("eq_h4_rack_upright_a", 166.6, 167.0, 6.4, 6.8, z, z + 2.2, m["steel"], c)
    add_box("eq_h4_rack_upright_b", 166.6, 167.0, 10.2, 10.6, z, z + 2.2, m["steel"], c)
    for k, zz in enumerate((0.7, 1.3, 1.9)):
        add_box(f"eq_h4_shelf_{k}", 166.4, 167.2, 6.4, 10.6, z + zz, z + zz + 0.06,
                m["wood"], c)
    add_box("eq_h3_crate_a", 165, 173, 67, 71, z, z + 1.2, m["rib_blue"], c)
    add_box("eq_h3_strip_l", 142, 162, 103, 106.5, z + 0.052, z + 0.062, m["zone_blight"], c)
    add_box("eq_h3_crate_b", 165, 173, 107, 111, z, z + 1.0, m["rib_blue"], c)
    add_box("eq_h4_chest", 172, 174, 8.4, 9.6, z, z + 0.9, m["container_olive"], c)
    for k in range(3):
        add_box(f"eq_h4_chest_lid_{k}", 172.05, 173.95, 8.45 + k * 0.38, 8.48 + k * 0.38,
                z + 0.9, z + 0.94, m["dark"], c)


def build_extra_props(m):
    """25 readable small props + pool/pit work lights."""
    c = coll("PROPS5")
    z = PLATFORM_Z
    # traffic cones
    cones = [(166, -58), (160, -64), (156, -66), (166, -149), (170, -151), (112, -4.5)]
    for i, (x, y) in enumerate(cones):
        if i != 5:      # v10: five cones floated over water (bridge + dock); keep the island one
            continue
        bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.28, radius2=0.05, depth=0.75,
                                        location=(x, y, z + 0.38))
        o = bpy.context.object
        o.name = f"prop_cone_{i}"
        for cc in list(o.users_collection):
            cc.objects.unlink(o)
        c.objects.link(o)
        o.data.materials.append(m["orange"])
        add_box(f"prop_cone_base_{i}", x - 0.3, x + 0.3, y - 0.3, y + 0.3, z, z + 0.05,
                m["dark"], c)
    # drums
    for i, (x, y) in enumerate(((78.6, 70.8), (81.3, 70.8), (163.2, 16.8), (165.0, 16.8))):
        add_cyl(f"prop_drum_{i}", x, y, z, z + 0.9, 0.3, m["orange"] if i < 2 else m["container_olive"],
                c, vertices=12)
        add_cyl(f"prop_drum_ring_{i}", x, y, z + 0.25, z + 0.3, 0.32, m["dark"], c, vertices=12)
    # cable coils
    for i, (x, y) in enumerate(((98.4, 52.8), (127.2, 106.8), (147.0, 13.2))):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.55, minor_radius=0.18,
                                         location=(x, y, z + 0.2))
        o = bpy.context.object
        o.name = f"prop_coil_{i}"
        for cc in list(o.users_collection):
            cc.objects.unlink(o)
        c.objects.link(o)
        o.data.materials.append(m["dark"])
    # pallet stacks (dock)
    for i, (u, v) in enumerate(((66, -14), (70, -14))):
        x, y = dock_world(u, v)
        add_box_local(f"prop_stack_{i}", x, y, 0.7, 2.0, 2.0, 1.4, m["wood"], c, rot_z=DOCK_ROTZ)
        add_box_local(f"prop_stack_band_{i}", x, y, 0.35, 2.05, 2.05, 0.06, m["dark"], c,
                      rot_z=DOCK_ROTZ)
    # wall pipe runs (H1 west, H3 north, H4 west)
    for i, (x0, x1, y, zz) in enumerate(((61.0, 61.2, 8, 46), (121.4, 178, 0, 0), (0, 0, 0, 0))):
        if x1 > x0:
            add_cyl_h(f"prop_run_{i}", (x0 + x1) / 2, y, z + zz * 0 + z + 1.2, abs(x1 - x0), 0.09,
                      m["metal"], c, vertices=8) if False else None
    for i, (y0, y1, x) in enumerate(((13, 47, 66.4), (61, 112, 121.3))):
        length = abs(y1 - y0)
        add_cyl_h(f"prop_run_v_{i}", x, (y0 + y1) / 2, z + 1.2, length, 0.09, m["metal"], c,
                  vertices=8, rot_z=math.radians(90))
    # hanging lamps (emissive discs under the roof line)
    for i, (x, y, zz) in enumerate(((93, 33, 13.5), (80.4, 24, 12.5), (93, 87, 12.0),
                                     (147, 87, 12.0), (147, 33, 15.0), (172, -150, 8.2))):
        add_cyl(f"prop_lamp_{i}", x, y, z + zz - 0.12, z + zz, 0.55, m["emis"], c, vertices=12)
        add_cyl(f"prop_lamp_cord_{i}", x, y, z + zz, z + zz + 0.6, 0.04, m["dark"], c, vertices=6)
    # pit work lamp + pool underwater lights (pit lamp cool blue: H3 是蓝室，暖灯会洗色)
    ld = bpy.data.lights.new("PitLight", "AREA")
    ld.shape = "SQUARE"; ld.size = 8; ld.energy = 2500
    ld.color = hex_rgba("#B9CEE0")[:3]
    lo = bpy.data.objects.new("PitLight", ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = (145.2, 87, z + 3.0)
    for i, (x, y) in enumerate(((82.2, 81.6), (98.4, 92.4))):
        add_cyl(f"prop_pool_light_{i}", x, y, z - 1.6, z - 1.5, 0.5, m["emis"], c, vertices=12)
    # signboards
    for i, (x, y, ang) in enumerate(((122, 4, 0), (166, -70, 20))):
        add_box_local(f"prop_sign_{i}", x, y, z + 1.4, 0.08, 1.6, 0.9, m["evac_blue"], c,
                      rot_z=math.radians(ang))
        add_box_local(f"prop_sign_post_{i}", x, y, z + 0.7, 0.08, 0.08, 1.4, m["metal"], c,
                      rot_z=math.radians(ang))


def build_roof_structure(m):
    """M4: trusses 6/room (top = wall top - 0.4), crane beams, 4 lamp sets/room."""
    c = coll("ROOF_STRUCT")
    z = PLATFORM_Z
    for key, (x0, x1, y0, y1) in ROOMS.items():
        wt = WALL_H[key]
        zt = z + wt - 0.8                      # truss occupies wall_top-0.8 .. wall_top-0.4
        for k in range(6):
            yy = y0 + 15 + k * 6.0
            add_box(f"truss_{key}_{k}", x0 + 0.4, x1 - 0.4, yy - 0.14, yy + 0.14,
                    zt, zt + 0.34, m["truss_dark"], c)
            for ci, cx in enumerate((x0 + (x1 - x0) * 0.32, x0 + (x1 - x0) * 0.68)):
                add_box(f"truss_tie_{key}_{k}_{ci}", cx - 0.16, cx + 0.16, yy - 0.3,
                        yy + 0.3, zt + 0.34, zt + 0.46, m["truss_dark"], c)
        for k, (lx, ly) in enumerate(((x0 + 18, y0 + 18), (x1 - 18, y0 + 18),
                                      (x0 + 18, y1 - 18), (x1 - 18, y1 - 18))):
            add_cyl(f"rlamp_{key}_{k}", lx, ly, z + 6.3, z + 6.55, 0.5, m["emis"], c,
                    vertices=10)
            add_cyl(f"rlamp_cord_{key}_{k}", lx, ly, z + 6.55, z + wt - 0.45, 0.03,
                    m["dark"], c, vertices=4)
    # crane beams: H4 x2, H3 x1 (1.2 x 0.6, floor +8 m)
    for k, yy in enumerate((20.0, 40.0)):
        add_box(f"crb_H4_{k}", 121, 173, yy - 0.3, yy + 0.3, z + 8.0, z + 8.6,
                m["yellow"], c)
    add_box("crb_H3_0", 121, 173, 95.7, 96.3, z + 8.0, z + 8.6, m["yellow"], c)


def build_scale_anchor(m):
    """M4: 10 m shuttle bus inside the dock as the readable scale anchor."""
    c = coll("DOCK_EXTRA")
    dock_box("scale_bus", 30, -35.0, 10.0, 3.0, 0.0, 3.0, m["container_blue"], c)
    dock_box("scale_bus_roof", 30, -35.0, 9.6, 2.6, 3.0, 3.15, m["white"], c)
    dock_box("scale_bus_glass", 30, -36.48, 8.6, 0.06, 1.2, 2.2, m["glass"], c)


def apply_bevels():
    n = 0
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        bb = [Vector(c) for c in ob.bound_box]
        ext = [max(c[i] for c in bb) - min(c[i] for c in bb) for i in range(3)]
        mind = min(ext)
        if mind < 0.12:
            continue
        w = min(0.22, mind * 0.30)
        if w < 0.012:
            continue
        md = ob.modifiers.new("bev", "BEVEL")
        md.width = w
        md.segments = 2
        md.limit_method = "ANGLE"
        md.angle_limit = math.radians(30)
        md.use_clamp_overlap = True
        n += 1
    print("BEVELED", n)


def round_pool_edges():
    """Bullnose on the pool coping + platform wall coping (reference reads a rounded lip)."""
    n = 0
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        if not (ob.name.startswith("gpool_c") or ob.name.startswith("gw") and "_cope" in ob.name
                or ob.name.startswith("gpilcap_")):
            continue
        md = ob.modifiers.get("bev")
        if md is None:
            md = ob.modifiers.new("bev", "BEVEL")
            md.limit_method = "ANGLE"
            md.angle_limit = math.radians(30)
            md.use_clamp_overlap = True
        md.width = 0.045
        md.segments = 3
        n += 1
    print("POOL_EDGE_ROUNDED", n)


# ------------------------------------------------------------------ furniture from plan
DIM_RE = re.compile(r"(\d+(?:\.\d+)?)\s*[×x]\s*(\d+(?:\.\d+)?)(?:\s*[×x]\s*(\d+(?:\.\d+)?))?")
COORD_RE = re.compile(r"\((\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\)")
CUSTOM_KEYS = {"H1-01", "H1-02", "H1-03", "H1-04", "H1-06", "H1-17",
               "H2-01", "H2-02", "H2-03", "H2-04", "H2-05", "H2-07", "H2-08", "H2-09",
               "H3-01", "H3-02", "H3-03", "H3-04", "H3-05", "H3-06", "H3-16",
               "H4-01", "H4-02", "H4-03", "H4-04", "H4-05",
               "C5-01", "C5-02", "C5-03", "C5-04", "C5-05"}
ROOM_Z0 = {"H1": PLATFORM_Z + 0.05, "H2": PLATFORM_Z + 0.05,
           "H3": PLATFORM_Z + 0.05, "H4": PLATFORM_Z + 0.05, "C5": 12.2}
ROOM_MATS = {"H1": ["metal", "dark", "wood"], "H2": ["steel", "container_olive", "metal"],
             "H3": ["white", "metal", "dark"], "H4": ["container_olive", "dark", "wood"],
             "C5": ["caramel", "wood", "dark"]}


def parse_furniture_rows():
    rows = []
    with open(PLAN, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            mt = re.match(r"^\| ((?:H[1-4]|C5)-\d+) \| (.+?) \| (.+?) \| (.+?) \| (\d+) \| ", line)
            if not mt:
                continue
            key, name, dims, coords, count = mt.groups()
            if key in CUSTOM_KEYS or "L1" in line:
                continue
            rows.append((key, name, dims, coords, int(count)))
    return rows


def place_component(name, x, y, w, d, h, mat, c, z0):
    """3-4 part furniture item: body + top/lid + feet/legs + handle or seam."""
    x0, x1 = x - w / 2, x + w / 2
    y0, y1 = y - d / 2, y + d / 2
    if h >= 1.2:                                    # cabinet / locker
        add_box(f"{name}_body", x0, x1, y0, y1, z0 + 0.08, z0 + h * 0.94, mat, c)
        add_box(f"{name}_top", x0 - 0.02, x1 + 0.02, y0 - 0.02, y1 + 0.02,
                z0 + h * 0.94, z0 + h, mat, c)
        add_box(f"{name}_plinth", x0 + 0.06, x1 - 0.06, y0 + 0.06, y1 - 0.06, z0, z0 + 0.08,
                mat, c)
        add_box(f"{name}_seam", x0 + w * 0.48, x0 + w * 0.52, y0 - 0.01, y1 + 0.01,
                z0 + 0.1, z0 + h * 0.92, mat, c)
        add_box(f"{name}_handle", x + w * 0.30, x + w * 0.34, y0 - 0.05, y0 - 0.02,
                z0 + h * 0.55, z0 + h * 0.62, mat, c)
    elif w >= 1.4 and h <= 1.1:                     # table / bench
        add_box(f"{name}_top", x0, x1, y0, y1, z0 + h - 0.08, z0 + h, mat, c)
        for k, (dx, dy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
            lx = x + dx * (w / 2 - 0.08)
            ly = y + dy * (d / 2 - 0.08)
            add_box(f"{name}_leg{k}", lx - 0.04, lx + 0.04, ly - 0.04, ly + 0.04,
                    z0, max(z0 + 0.1, z0 + h - 0.08), mat, c)
    else:                                           # crate / box
        add_box(f"{name}_body", x0, x1, y0, y1, z0, z0 + h * 0.86, mat, c)
        add_box(f"{name}_lid", x0 - 0.02, x1 + 0.02, y0 - 0.02, y1 + 0.02,
                z0 + h * 0.86, z0 + h, mat, c)
        add_box(f"{name}_band", x0 - 0.01, x1 + 0.01, y + d * 0.22, y + d * 0.28,
                z0 + 0.02, z0 + h * 0.86, mat, c)


def build_furniture(m):
    c = coll("FURNITURE")
    placed = 0
    for key, name, dims, coords, count in parse_furniture_rows():
        room = key.split("-")[0]
        z0 = ROOM_Z0[room]
        dm = DIM_RE.search(dims)
        cm = COORD_RE.findall(coords)
        if not dm or not cm:
            continue
        w, d = float(dm.group(1)), float(dm.group(2))
        h = float(dm.group(3)) if dm.group(3) else 1.0
        w, d = min(w, 12.0), min(d, 12.0)
        h = min(h, 9.0)
        mat_name = ROOM_MATS[room][count % 3]
        mat = m[mat_name]
        for i, (csx, csy) in enumerate(cm[:8]):
            sx, sy = float(csx), float(csy)
            place_component(f"fur_{key}_{i}", sx, sy, w, d, h, mat, c, z0)
            placed += 1
        # extra instances for rows like "x5 benches" with a single coordinate
        if count > len(cm) and len(cm) >= 1 and count <= 12:
            sx0, sy0 = float(cm[0][0]), float(cm[0][1])
            for k in range(len(cm), min(count, 8)):
                sx = min(sx0 + 2.5 * k, ROOMS.get(room, (0, 240, 0, 0))[1] - 1 if room in ROOMS else 239)
                add_box(f"fur_{key}_{k}", sx - w / 2, sx + w / 2, sy0 - d / 2, sy0 + d / 2,
                        z0, z0 + h, mat, c)
                placed += 1
    print("FURNITURE_PLACED", placed)
    return placed


# ------------------------------------------------------------------ camera / render
# ------------------------------------------------------------------ v09 near-view rig
# Third-person close-ups are the primary deliverable (user 14:47), so the scene
# needs an eye-level camera set plus one placeholder character (G4, 14:49).

CHAR_YAW = {}


def char_part(c, name, x, y, z, dx, dy, dz, mat):
    """Box in character-local space (x = right, y = forward), rotated by the yaw."""
    ca, sa = math.cos(CHAR_YAW["a"]), math.sin(CHAR_YAW["a"])
    wx = x * ca - y * sa
    wy = x * sa + y * ca
    o = add_box_local(name, wx, wy, z, dx, dy, dz, mat, c, rot_z=CHAR_YAW["a"])
    o["is_char"] = True
    return o


def build_character(m, base=(0.0, 0.0, 0.0), yaw_deg=0.0):
    """G4 placeholder character: 1.75 m low-poly silhouette with gear, no face."""
    c = coll("CHARACTER")
    CHAR_YAW["a"] = math.radians(yaw_deg)
    dark = m["char_dark"]
    mid = m["char_mid"]
    acc = m["char_acc"]
    z = base[2]
    CHAR_YAW["ox"], CHAR_YAW["oy"] = base[0], base[1]

    def part(name, x, y, z0, z1, sx, sy, mat):
        o = char_part(c, name, x, y, (z0 + z1) / 2.0, sx, sy, z1 - z0, mat)
        o.location.x += base[0]
        o.location.y += base[1]
        return o

    # legs (slight stance), boots
    for i, sx in enumerate((-0.11, 0.11)):
        part(f"ch_leg_{i}", sx, 0.0, 0.10, 0.86, 0.17, 0.20, dark)
        part(f"ch_boot_{i}", sx, 0.04, 0.0, 0.12, 0.19, 0.30, mid)
        part(f"ch_knee_{i}", sx, 0.02, 0.42, 0.56, 0.19, 0.23, acc)
    # hips + belt
    part("ch_hips", 0.0, 0.0, 0.86, 1.06, 0.38, 0.24, dark)
    part("ch_belt", 0.0, 0.0, 1.02, 1.10, 0.40, 0.26, acc)
    # torso (chest wider at the top)
    part("ch_torso", 0.0, 0.0, 1.10, 1.46, 0.42, 0.26, mid)
    part("ch_chest", 0.0, 0.01, 1.38, 1.52, 0.46, 0.28, mid)
    part("ch_rig", 0.13, 0.10, 1.14, 1.34, 0.13, 0.10, acc)
    # shoulder pads
    for i, sx in enumerate((-0.26, 0.26)):
        part(f"ch_pad_{i}", sx, 0.0, 1.42, 1.55, 0.16, 0.26, acc)
    # arms, one bent forward (holding a strap)
    part("ch_arm_l", -0.28, 0.02, 1.06, 1.44, 0.14, 0.16, dark)
    part("ch_arm_r", 0.28, -0.06, 1.04, 1.44, 0.14, 0.16, dark)
    part("ch_forearm_r", 0.28, 0.05, 0.92, 1.12, 0.14, 0.16, dark)
    # neck + head + helmet
    part("ch_neck", 0.0, 0.0, 1.52, 1.60, 0.12, 0.12, dark)
    part("ch_head", 0.0, 0.01, 1.60, 1.80, 0.21, 0.23, mid)
    part("ch_helmet", 0.0, 0.0, 1.76, 1.86, 0.23, 0.25, dark)
    part("ch_visor", 0.0, 0.12, 1.66, 1.74, 0.17, 0.03, m["char_visor"])
    # backpack + antenna + slung rod
    part("ch_pack", 0.0, -0.19, 1.10, 1.52, 0.34, 0.24, acc)
    part("ch_pack_top", 0.0, -0.19, 1.52, 1.60, 0.28, 0.20, dark)
    o = part("ch_ant", 0.14, -0.22, 1.60, 2.05, 0.03, 0.03, dark)
    o.rotation_euler[1] = math.radians(6)
    o = part("ch_rod", 0.0, -0.30, 0.86, 1.62, 0.05, 0.05, mid)
    o.rotation_euler[1] = math.radians(24)


NEAR = (
    # name, lens, eye, target, fstop, character(u, v, yaw)
    ("CameraP1", 32.0, (26.0, -12.4), (56.0, 9.0), 4.5, (33.0, -7.0, 118.0)),
    ("CameraP2", 40.0, (74.0, 9.4), (30.0, -5.0), 5.6, None),
    ("CameraP3", 32.0, (26.0, -9.0), (37.0, 6.0), 4.5, None),
    ("CameraP4", 32.0, (56.0, -2.0), (44.0, -15.0), 4.2, (48.0, -8.4, 145.0)),
    ("CameraP5", 40.0, (54.0, -6.0), (70.0, 24.0), 5.6, None),
    ("CameraP6", 30.0, (80.0, 9.0), (94.0, -16.0), 4.5, None),
    ("CameraP7", 32.0, (80.0, -7.0), (92.0, 17.0), 4.5, (86.0, 4.0, 200.0)),
    ("CameraP8", 35.0, (118.0, 34.0), (122.0, 62.0), 4.0, None),
)


def cull_floaters():
    """Delete loose props that ended up over open water after the bands were removed.

    Keeps anything whose footprint centre sits inside the island octagon, the
    avenue corridor or the peninsula deck."""
    def inside(x, y):
        if 50.0 <= x <= 186.0 and -12.0 <= y <= 122.0:
            return True
        # avenue corridor (including kerbs and the quay aprons)
        dx, dy = x - AV_HEAD[0], y - AV_HEAD[1]
        tt = dx * AV_U[0] + dy * AV_U[1]
        oo = dx * AV_V[0] + dy * AV_V[1]
        if -6.0 <= tt <= AV_L1 + 30.0 and abs(oo) <= 16.0:
            return True
        if AV_L1 <= tt <= AV_L1 + 260.0 and abs(oo) <= 58.0:
            return True
        return False

    doomed = []
    for coll_name in ("OUTDOOR", "PROPS5", "VEG_CARDS"):
        c = bpy.data.collections.get(coll_name)
        if not c:
            continue
        for o in c.objects:
            if o.type != "MESH":
                continue
            if not inside(o.location.x, o.location.y):
                doomed.append(o)
    for o in doomed:
        bpy.data.objects.remove(o, do_unlink=True)
    print("CULL removed=%d" % len(doomed))


def build_near_rig(m):
    """Eye-level cameras (P1-P7 on the avenue/peninsula, P8 over the CEO deck)."""
    for name, lens, eye_uv, tgt_uv, fstop, ch in NEAR:
        cd = bpy.data.cameras.new(name)
        cam = bpy.data.objects.new(name, cd)
        bpy.context.scene.collection.objects.link(cam)
        if name == "CameraP8":
            cam.location = (118.0, 40.0, 30.0)
            tgt = Vector((122.0, 62.0, 13.0))
        else:
            t = AV_OFF + eye_uv[0]
            x, y = av(t, eye_uv[1])
            cam.location = (x, y, av_z(t) + 1.66)
            x2, y2 = av(AV_OFF + tgt_uv[0], tgt_uv[1])
            tgt = Vector((x2, y2, av_z(AV_OFF + tgt_uv[0]) + 2.1))
        d = tgt - Vector(cam.location)
        cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        cd.lens = lens
        cd.clip_start = 0.1
        cd.clip_end = 900.0
        cd.dof.use_dof = True
        cd.dof.focus_distance = d.length
        cd.dof.aperture_fstop = fstop
        cam["is_near"] = True
        if ch:
            wx, wy = dock_world(ch[0], ch[1])
            build_character(m, (wx, wy, 0.0), ch[2])


def build_camera_light(samples):
    # --- master ortho camera (map texture)
    cam_data = bpy.data.cameras.new("Camera")
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (151.00, -78.04, 300.0)
    cam.rotation_euler = (0.0, 0.0, math.radians(20))
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 420.0
    cam_data.clip_start = 1.0
    cam_data.clip_end = 700.0
    bpy.context.scene.camera = cam

    # --- core detail camera (14 px/m tile)
    core_data = bpy.data.cameras.new("CameraCore")
    core = bpy.data.objects.new("CameraCore", core_data)
    bpy.context.scene.collection.objects.link(core)
    core.location = (120.0, 67.0, 300.0)
    core.rotation_euler = (0.0, 0.0, 0.0)
    core_data.type = "ORTHO"
    core_data.ortho_scale = 148.0
    core_data.clip_start = 1.0
    core_data.clip_end = 700.0

    # --- hero camera (3/4 perspective for the promo shot)
    hero_data = bpy.data.cameras.new("CameraHero")
    hero = bpy.data.objects.new("CameraHero", hero_data)
    bpy.context.scene.collection.objects.link(hero)
    hero.location = (-42.0, -236.0, 168.0)
    target = Vector((122.0, 6.0, 0.0))
    d = target - hero.location
    hero.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    hero_data.lens = 58.0
    hero_data.clip_start = 1.0
    hero_data.clip_end = 1200.0
    hero_data.dof.use_dof = True
    hero_data.dof.focus_distance = d.length
    hero_data.dof.aperture_fstop = 4.0

    # --- sun: softer, warmer
    sun_data = bpy.data.lights.new("Sun", "SUN")
    sun = bpy.data.objects.new("Sun", sun_data)
    bpy.context.scene.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(57), 0, math.radians(-70))
    sun_data.energy = 4.2
    sun_data.angle = math.radians(5.0)
    sun_data.color = hex_rgba("#FFE7C4")[:3]

    # --- gradient sky
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 0.55
    # cool gradient sky: deep cool horizon -> pale sage zenith (M3)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*hex_rgba("#DCE5E2")[:3], 1.0)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (*hex_rgba("#7E97A2")[:3], 1.0)
    nt.links.new(tc.outputs["Normal"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

    # --- two shaping fills (warm top, cool side)
    for i, (loc, size, energy, col) in enumerate((((120, 60, 88), 180, 22000, "#FFE6C4"),
                                                  ((30, 190, 70), 150, 10000, "#CFE0EA"))):
        ld = bpy.data.lights.new(f"Shape_{i}", "AREA")
        ld.shape = "SQUARE"
        ld.size = size
        ld.energy = energy
        ld.color = hex_rgba(col)[:3]
        lo = bpy.data.objects.new(f"Shape_{i}", ld)
        bpy.context.scene.collection.objects.link(lo)
        lo.location = loc

    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    sc.cycles.max_bounces = 6
    sc.cycles.diffuse_bounces = 4
    sc.cycles.glossy_bounces = 4
    sc.cycles.transmission_bounces = 8
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.exposure = 0.0
    try:
        sc.view_settings.look = "None"
    except Exception:
        pass
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"


def ao_ground(m, distance=2.6, strength=0.55):
    """Cheap contact darkening for horizontal surfaces (no compositor pass in 5.2)."""
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    if b is None:
        return
    src = b.inputs["Base Color"].links[0].from_socket if b.inputs["Base Color"].links else None
    ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = distance
    try:
        ao.only_local = False
    except Exception:
        pass
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = strength
    if src:
        nt.links.new(src, mix.inputs["Color1"])
    else:
        mix.inputs["Color1"].default_value = tuple(b.inputs["Base Color"].default_value)
    nt.links.new(ao.outputs["AO"], mix.inputs["Color2"])
    nt.links.new(mix.outputs["Color"], b.inputs["Base Color"])


def apply_material_upgrade(m):
    ground = ("platform", "garden", "dock", "causeway", "island", "rock")
    for k in ground:
        mottle(m[k], scale=0.018, amp=0.13, rough_lo=0.78, rough_hi=1.0)
    for k in ("h1", "h2", "h3", "h4"):
        mottle(m[k], scale=0.045, amp=0.09, rough_lo=0.85, rough_hi=1.0)
    for k in ("wall", "wall_h4", "white", "green_in"):
        mottle(m[k], scale=0.07, amp=0.05)
    for k in ("metal", "steel"):
        mottle(m[k], scale=0.13, amp=0.12, rough_lo=0.3, rough_hi=0.55)
    for k in ("container_blue", "container_olive", "container_gray", "bluebox"):
        mottle(m[k], scale=0.09, amp=0.14, rough_lo=0.5, rough_hi=0.8)
    for k in ("wood", "caramel"):
        mottle(m[k], scale=0.2, amp=0.16, rough_lo=0.55, rough_hi=0.85)
    for k in ("teal", "orange", "yellow", "evac_blue", "dark"):
        mottle(m[k], scale=0.11, amp=0.1)
    mottle(m["pool"], scale=0.3, amp=0.07)
    water_bump(m["pool"], scale=0.5, strength=0.2)
    water_bump(m["water"], scale=0.35, strength=0.12)
    for k in ("h1", "h2", "h3", "h4", "causeway"):
        ao_ground(m[k], distance=0.9, strength=0.38)


IL_MATS = ("platform", "garden", "dock", "wall", "wall_h4", "metal", "wood",
           "island", "rock")
# 每材质 V 三档（§5.4 明度分工）：环路/堤道/坞底/岛 0.74，墙顶 0.88，其余默认
IL_BANDS = {"dock": (0.42, 0.74, 0.86), "island": (0.42, 0.74, 0.86),
            "rock": (0.42, 0.74, 0.86), "wall": (0.42, 0.66, 0.88)}


# ------------------------------------------------------------------ v09 B-tier textures
def _tex_mix(mat, mode="grain", scale=6.0, lo=0.80, hi=1.06, mortar=0.55):
    """Multiply a procedural mask into Base Color without touching the hue.

    mode: grain  - fine noise (asphalt, steel)
          panel  - brick grid, mortar lines only (concrete slabs / wall panels)
    """
    nt = mat.node_tree
    b = nt.nodes.get("Principled BSDF")
    if b is None:
        return
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    if mode == "panel":
        mp.inputs["Scale"].default_value = (scale, scale, scale)
    else:
        mp.inputs["Scale"].default_value = (scale, scale, scale)
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.20
    ramp.color_ramp.elements[0].color = (lo, lo, lo, 1.0)
    ramp.color_ramp.elements[1].position = 0.80
    ramp.color_ramp.elements[1].color = (hi, hi, hi, 1.0)
    if mode == "panel":
        tex = nt.nodes.new("ShaderNodeTexBrick")
        tex.inputs["Color1"].default_value = (1.0, 1.0, 1.0, 1.0)
        tex.inputs["Color2"].default_value = (1.0, 1.0, 1.0, 1.0)
        tex.inputs["Mortar"].default_value = (mortar, mortar, mortar, 1.0)
        tex.inputs["Scale"].default_value = 1.0
        tex.inputs["Mortar Size"].default_value = 0.012
        tex.inputs["Brick Width"].default_value = 0.5
        tex.inputs["Row Height"].default_value = 0.5
        nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
        out_sock = tex.outputs["Color"]
        nt.links.new(out_sock, ramp.inputs["Fac"])
    else:
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Detail"].default_value = 7.0
        tex.inputs["Roughness"].default_value = 0.62
        nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
        nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])

    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = 1.0
    src = b.inputs["Base Color"].links[0].from_socket if b.inputs["Base Color"].links else None
    if src is not None:
        nt.links.new(src, mix.inputs[1])
    else:
        mix.inputs[1].default_value = b.inputs["Base Color"].default_value[:]
    nt.links.new(ramp.outputs["Color"], mix.inputs[2])
    nt.links.new(mix.outputs["Color"], b.inputs["Base Color"])
    # v14 M07: roughness variation from the same mask (not a constant)
    try:
        if not b.inputs["Roughness"].is_linked:
            _base = float(b.inputs["Roughness"].default_value)
            _mr = nt.nodes.new("ShaderNodeMapRange")
            _mr.inputs["From Min"].default_value = 0.0
            _mr.inputs["From Max"].default_value = 1.0
            _mr.inputs["To Min"].default_value = max(0.02, _base * 0.85)
            _mr.inputs["To Max"].default_value = min(1.0, _base * 1.15)
            nt.links.new(ramp.outputs["Color"], _mr.inputs["Value"])
            nt.links.new(_mr.outputs["Result"], b.inputs["Roughness"])
    except Exception as _exc:
        print("V14_ROUGH_MASK_SKIP", str(_exc)[:60])


def apply_surface_textures(m):
    """B1-B4: four families of surface treatment, box-projected (no UV, no bake)."""
    _tex_mix(m["road"], "grain", 2.2, 0.62, 1.12)         # B1 asphalt aggregate
    _tex_mix(m["apron"], "panel", 1.6, 0.66, 1.10, 0.58)   # B2 concrete slabs
    _tex_mix(m["platform"], "panel", 0.9, 0.68, 1.10, 0.58)
    _tex_mix(m["dock"], "panel", 0.7, 0.66, 1.10, 0.58)    # B3 painted wall panels
    _tex_mix(m["wall"], "panel", 0.7, 0.66, 1.10, 0.58)
    _tex_mix(m["steel"], "grain", 3.0, 0.70, 1.12)         # B4 corrugated metal
    _tex_mix(m["white"], "grain", 1.4, 0.74, 1.08)
    _tex_mix(m["water"], "grain", 0.03, 0.78, 1.10)       # slow current variation
    print("SURFACE_TEX on 8 materials")


def apply_illustration_shader(m):
    """M5 illustration pass on 7 base materials.

    Chain: mottle -> HSV V-quantize (3 bands 0.42/0.66/0.86 @0.34/0.62)
           -> SoftLight 0.40 back-fill -> shadow tint #5A6470 by (1-AO)*0.55
           -> reveal white #E6E0D2 0.25 by AO -> directional strokes 0.12.
    AO node samples fixed to 32 (sand-eye guard).
    """
    shadow_tint = hex_rgba("#5A6470")[:3]
    reveal_col = hex_rgba("#E6E0D2")[:3]
    for key in IL_MATS:
        m_ = m[key]
        nt = m_.node_tree
        b = nt.nodes.get("Principled BSDF")
        if b is None:
            continue
        v1, v2, v3 = IL_BANDS.get(key, (0.42, 0.66, 0.86))
        src = b.inputs["Base Color"].links[0].from_socket if b.inputs["Base Color"].links else None

        sep = nt.nodes.new("ShaderNodeSeparateColor")
        sep.mode = "HSV"
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.interpolation = "CONSTANT"
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[0].color = (v1, v1, v1, 1.0)
        e1 = ramp.color_ramp.elements.new(0.34)
        e1.color = (v2, v2, v2, 1.0)
        e2 = ramp.color_ramp.elements.new(0.62)
        e2.color = (v3, v3, v3, 1.0)
        com = nt.nodes.new("ShaderNodeCombineColor")
        com.mode = "HSV"
        if src:
            nt.links.new(src, sep.inputs["Color"])
        else:
            sep.inputs["Color"].default_value = tuple(b.inputs["Base Color"].default_value) + (1.0,)
        nt.links.new(sep.outputs["Red"], com.inputs["Red"])     # H unchanged
        nt.links.new(sep.outputs["Green"], com.inputs["Green"])  # S unchanged
        nt.links.new(sep.outputs["Blue"], ramp.inputs["Fac"])    # V quantized
        nt.links.new(ramp.outputs["Color"], com.inputs["Blue"])

        soft = nt.nodes.new("ShaderNodeMixRGB")
        soft.blend_type = "SOFT_LIGHT"
        soft.inputs["Fac"].default_value = 0.40
        if src:
            nt.links.new(src, soft.inputs["Color2"])
        else:
            soft.inputs["Color2"].default_value = tuple(b.inputs["Base Color"].default_value) + (1.0,)
        nt.links.new(com.outputs["Color"], soft.inputs["Color1"])

        ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
        ao.samples = 32
        ao.inputs["Distance"].default_value = 1.4
        try:
            ao.only_local = False
        except Exception:
            pass
        inv = nt.nodes.new("ShaderNodeInvert")

        mul = nt.nodes.new("ShaderNodeMixRGB")
        mul.blend_type = "MULTIPLY"
        mul.inputs["Fac"].default_value = 1.0
        mul.inputs["Color2"].default_value = (*shadow_tint, 1.0)
        nt.links.new(soft.outputs["Color"], mul.inputs["Color1"])

        fmul = nt.nodes.new("ShaderNodeMath")
        fmul.operation = "MULTIPLY"
        fmul.inputs[1].default_value = 0.45
        nt.links.new(inv.outputs["Color"], fmul.inputs[0])
        mix2 = nt.nodes.new("ShaderNodeMixRGB")
        mix2.blend_type = "MIX"
        nt.links.new(soft.outputs["Color"], mix2.inputs["Color1"])
        nt.links.new(mul.outputs["Color"], mix2.inputs["Color2"])
        nt.links.new(fmul.outputs["Value"], mix2.inputs["Fac"])

        frev = nt.nodes.new("ShaderNodeMath")
        frev.operation = "MULTIPLY"
        frev.inputs[1].default_value = 0.25
        nt.links.new(inv.outputs["Color"], frev.inputs[0])
        rev = nt.nodes.new("ShaderNodeMixRGB")
        rev.blend_type = "MIX"
        rev.inputs["Color2"].default_value = (*reveal_col, 1.0)
        nt.links.new(mix2.outputs["Color"], rev.inputs["Color1"])
        nt.links.new(frev.outputs["Value"], rev.inputs["Fac"])

        # directional strokes: noise anisotropic, rotated 45 deg, soft-light 0.12
        tcs = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Rotation"].default_value[2] = math.radians(45)
        mp.inputs["Scale"].default_value = (7.0, 1.2, 1.0)
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 1.0
        nz.inputs["Detail"].default_value = 2.0
        stroke = nt.nodes.new("ShaderNodeMixRGB")
        stroke.blend_type = "SOFT_LIGHT"
        stroke.inputs["Fac"].default_value = 0.28
        nt.links.new(tcs.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
        nt.links.new(nz.outputs["Fac"], stroke.inputs["Color2"])
        nt.links.new(rev.outputs["Color"], stroke.inputs["Color1"])

        nt.links.new(inv.inputs["Color"], ao.outputs["AO"])
        nt.links.new(stroke.outputs["Color"], b.inputs["Base Color"])
    print("IL_SHADER on", len(IL_MATS), "materials")



# =====================================================================
# v14 single-batch art overhaul (M03 / M04 / M06 / M09)
# See planning/art/SPACE_BASE_V14_ONESHOT_PLAN_20261108.md
# =====================================================================

def _v14_area(name, loc, size, energy, color, target):
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = "SQUARE"
    ld.size = size
    ld.energy = energy
    ld.color = hex_rgba(color)[:3]
    o = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    d = Vector(target) - o.location
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return o


def build_v14_compositor(sat=1.0):
    """M03: P1-style grading stack. No vignette, no .cube (Blender 4.5 has no LUT node).

    r2 convergence: saturation boost is gated by a luminance mask so it only
    affects dark/mid tones. Bright low-sat concrete must stay low-sat, otherwise
    S1 (light = L>=0.62 AND sat<=0.28) collapses -- r1 measured 0.017.
    """
    sc = bpy.context.scene
    sc.use_nodes = True
    sc.render.use_compositing = True
    nt = sc.node_tree
    nt.nodes.clear()
    rl = nt.nodes.new("CompositorNodeRLayers")
    glare = nt.nodes.new("CompositorNodeGlare")
    try:
        glare.glare_type = "FOG_GLOW"
        glare.threshold = 0.90
        glare.size = 6
        glare.inputs["Strength"].default_value = 0.08
    except Exception as exc:
        print("V14_GLARE_SKIP", str(exc)[:80])
        nt.nodes.remove(glare)
        glare = None
    cb = nt.nodes.new("CompositorNodeColorBalance")
    cb.lift = (0.992, 0.997, 1.004)    # r2: much milder cool shadows
    cb.gain = (1.018, 1.006, 0.994)    # r2: much milder warm highlights
    cb.gamma = (1.10, 1.10, 1.10)   # r5: lift midtones across L=0.62 without pushing highlights
    hs = nt.nodes.new("CompositorNodeHueSat")
    hs.inputs["Saturation"].default_value = sat
    bc = nt.nodes.new("CompositorNodeBrightContrast")
    try:
        bc.inputs["Contrast"].default_value = 0.02
        bc.inputs["Bright"].default_value = 0.0
    except Exception:
        pass
    out = nt.nodes.new("CompositorNodeComposite")
    chain = [n for n in (rl, glare, cb, hs, bc, out) if n is not None]
    for a_, b_ in zip(chain, chain[1:]):
        nt.links.new(a_.outputs["Image"], b_.inputs["Image"])

    # luminance-gated saturation: dark -> boost, bright -> leave alone
    try:
        bw = nt.nodes.new("CompositorNodeRGBToBW")
        nt.links.new(rl.outputs["Image"], bw.inputs["Image"])
        ramp = nt.nodes.new("CompositorNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.32
        ramp.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
        ramp.color_ramp.elements[1].position = 0.68
        ramp.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)
        nt.links.new(bw.outputs[0], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs[0], hs.inputs["Fac"])
        print("V14_SAT_MASK_OK")
    except Exception as exc:
        print("V14_SAT_MASK_SKIP", str(exc)[:90])
        hs.inputs["Fac"].default_value = 0.0
    print("V14_COMPOSITOR_OK", " -> ".join(n.bl_idname for n in chain))


def _v14_family(name):
    n = name.lower()
    if any(k in n for k in ("platform", "apron", "concrete", "walk", "causeway",
                            "terrace", "garden_wall", "coping", "floor_ind", "cope")):
        return "concrete"
    if any(k in n for k in ("road", "asphalt", "joint")):
        return "asphalt"
    if any(k in n for k in ("metal", "steel", "truss", "brass", "mesh", "rib",
                            "dome", "silo", "pipe", "rack")):
        return "metal"
    if any(k in n for k in ("glass", "win_", "frost")):
        return "glass"
    if any(k in n for k in ("grass", "hedge", "foliage", "palm", "bush", "card")):
        return "vegetation"
    if any(k in n for k in ("yellow", "orange", "evac", "emis", "blue", "green",
                            "zone", "strip", "visor")):
        return "accent"
    return "other"


def apply_v14_art(m, a):
    """Single-batch post-build pass. Runs AFTER build_camera_light."""
    import os
    sc = bpy.context.scene

    # ---- M04: two shaping fills (P1 uses 6 Area lights; v13 had only 2) ----
    _v14_area("V14_CoolSkyFill", (60.0, -180.0, 120.0), 200.0, 4500.0,
              "#8FA3B0", (120.0, 0.0, 0.0))
    _v14_area("V14_WarmBounce", (240.0, 60.0, 70.0), 160.0, 3500.0,
              "#FFE0B8", (120.0, 0.0, 0.0))

    # ---- M03: compositor grading (toggle with V14_NO_COMP=1 for A/B) ----
    if not os.environ.get("V14_NO_COMP"):
        build_v14_compositor(sat=float(os.environ.get("V14_SAT", "1.0")))
    else:
        print("V14_COMPOSITOR_OFF")

    # ---- M06: family tags + surface-response redistribution ----
    for mat in bpy.data.materials:
        mat["material_family"] = _v14_family(mat.name)

    def set_resp(key, rough, metal):
        mat = m.get(key)
        if mat is None or not mat.use_nodes:
            return
        b = mat.node_tree.nodes.get("Principled BSDF")
        if not b:
            return
        try:
            if not b.inputs["Roughness"].is_linked:
                b.inputs["Roughness"].default_value = rough
            if not b.inputs["Metallic"].is_linked:
                b.inputs["Metallic"].default_value = metal
        except Exception:
            pass

    for k in ("metal", "steel", "dome", "dome_base", "truss_dark", "rib_blue"):
        set_resp(k, 0.42, 0.60)
    for k in ("container_blue", "container_olive", "container_gray"):
        set_resp(k, 0.48, 0.55)
    for k in ("platform", "apron", "garden_walk", "causeway"):
        set_resp(k, 0.86, 0.0)
    set_resp("road", 0.90, 0.0)
    set_resp("glass", 0.08, 0.0)
    set_resp("frost", 0.12, 0.0)

    # ---- M06: alias-merge near-identical concretes, then drop unused materials ----
    def remap(old_key, new_key):
        old, new = m.get(old_key), m.get(new_key)
        if old is None or new is None or old == new:
            return 0
        n = 0
        for ob in bpy.data.objects:
            if ob.type != "MESH":
                continue
            for slot in ob.material_slots:
                if slot.material == old:
                    slot.material = new
                    n += 1
        m[old_key] = new
        return n

    merged = (remap("garden_walk", "platform") +
              remap("causeway", "apron") +
              remap("garden_stone", "apron"))
    before = len(bpy.data.materials)
    for mat in list(bpy.data.materials):
        if mat.users == 0:
            bpy.data.materials.remove(mat)
    print("V14_MATERIALS", "merged_slots=%d" % merged,
          "materials=%d->%d" % (before, len(bpy.data.materials)))

    # ---- M09: three-step shallow-water band around the site ----
    shallow_mats = [
        make_mat("v14.shallow_far", "#245055", 0.25, 0.0, 1.0, "#183B40", 0.30),
        make_mat("v14.shallow_mid", "#2E5A5F", 0.25, 0.0, 1.0, "#1C3C40", 0.35),
        make_mat("v14.shallow_near", "#3E6360", 0.25, 0.0, 1.0, "#264A48", 0.35),
    ]
    band = 0
    for ob in bpy.data.objects:
        if ob.type == "MESH" and ob.name.startswith("shore_fan_"):
            try:
                idx = int(ob.name.rsplit("_", 1)[1])
            except ValueError:
                continue
            if ob.material_slots:
                ob.material_slots[0].material = shallow_mats[idx % 3]
                band += 1
    print("V14_SHORE_BANDS", band)

    # ---- fog: master keeps it hidden (top-down legibility), hero enables it ----
    for ob in bpy.data.objects:
        if ob.get("is_fog"):
            ob["v14_fog"] = True
            ob.hide_render = True

    print("V14_ART_OK", "lights=%d" % sum(1 for o in bpy.data.objects if o.type == "LIGHT"),
          "compositor=%s" % sc.use_nodes)



def main():
    a = parse_args()
    clear_scene()
    m = build_materials()
    build_terrain(m)
    build_lower_terrace(m)
    build_north_gate(m)
    build_core_v11(m)
    build_domes(m)
    build_site_dressing(m)
    build_avenue(m)
    build_forecourt(m)
    build_garden(m)
    build_street_kit(m)
    build_horizon(m)
    build_test_workshop(m)
    build_cards(m)
    build_shore(m)
    build_ridges(m)
    build_hero_fog()
    build_scale_anchor(m)
    purge_workshop_intruders()
    # H3 / TV13-03: four small roof caps (gate booths, guard hut, scale bus).
    # "Do not roof" applies globally; remove caps, keep the props as open-topped.
    _roof_caps = [o for o in bpy.data.objects
                  if any(t in o.name.lower() for t in ("roof", "ceiling", "skylight"))
                  and not any(e in o.name for e in ("corr_truss", "corr_beam"))]
    for _o in _roof_caps:
        bpy.data.objects.remove(_o, do_unlink=True)
    print("STRIP_ROOF_CAPS", len(_roof_caps))
    IND["on"] = True
    n_fur = 0
    IND["on"] = False
    apply_material_upgrade(m)
    apply_surface_textures(m)
    apply_illustration_shader(m)
    apply_bevels()
    round_pool_edges()
    for o in bpy.data.objects:
        if o.get("is_fog"):
            o.hide_render = True
    build_near_rig(m)
    build_camera_light(a.samples)
    apply_v14_art(m, a)

    res = a.res.lower().split("x")
    bpy.context.scene.render.resolution_x = int(res[0])
    bpy.context.scene.render.resolution_y = int(res[1])
    bpy.context.scene.render.resolution_percentage = 100

    n_objs = len(bpy.data.objects)
    n_tris = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == "MESH")
    print("SCENE_STATS objects=%d meshes=%d furniture=%d" % (n_objs, n_tris, n_fur))

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.out))
    if a.render:
        os.makedirs(os.path.dirname(os.path.abspath(a.render)), exist_ok=True)
        bpy.context.scene.render.filepath = os.path.abspath(a.render)
        bpy.ops.render.render(write_still=True)
    print("BUILD_OK v10", a.out, a.render)


if __name__ == "__main__":
    main()
