"""Procedural builder for space_base_minigame v10 — central garden platform (r07).

v07 -> v08 changes (user: rooms too empty, compress each core area):
  S1  four rooms 60x60 -> 54x54 (grid x66..174 / y6..114), gates recomputed
  S2  indoor contents keep their size but shift toward (120,60) by 0.9
      (flat decals scale with the room) -> same props in denser halls
  S3  island octagon shrinks 0.9 too (margins stay tight); channels/bridges/
      outer bands unchanged; causeway now starts on the new island edge
  S4  fountain r4.5 on the south margin; palms on the new margins
  S5  road furniture (lamps/bollards/rings/benches/barriers) re-laid to the
      new edges; CEO box stays unscaled as the boss landmark

Run:
  blender -b --factory-startup --python tools/blender_space_base/build_scene_v8.py -- \
    --out art/static_map/space_base_minigame/v08/scene.blend \
    --render art/static_map/space_base_minigame/v08/renders/master_raw.png \
    --res 3360x5880 --samples 32
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
PALMS = [av_pt(t, s) for t in (10.0, 26.0, 42.0, 58.0) for s in (-60.0, 60.0)]
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

CEO = (100, 140, 45, 75, 12.0, 16.5)   # x0,x1,y0,y1,z0,z1

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
        "platform": make_mat("v6.platform", "#B4B0A2", 0.9),       # S1 提亮
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
        "road": make_mat("v9.road", "#87898B", 0.88),              # 沥青路（偏浅，护 S1）
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
        "metal": make_mat("v6.metal", "#59676D", 0.5, 0.45),
        "steel": make_mat("v6.steel", "#98A1A3", 0.45, 0.55),   # v09.1: 镀锌屋面更亮（S1）
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
        "rug": make_mat("v6.rug", "#C9B49A", 0.85),                # CEO 亮地毯（S14 对比）
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
SITE_TN = -120.0          # north edge
SITE_W1 = 73.0            # half width of the core band (146)
SITE_T1 = 4.0             # step 1: core/loading -> apron
SITE_W2 = 65.0            # 130
SITE_T2 = 74.0            # step 2: apron -> parking
SITE_W3 = 52.0            # 104
SITE_TS = 114.0           # south edge (bridge head)


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

    # ---------- K06 tank farm, east side behind the container row ----------
    for row in range(2):
        for col in range(5):
            u = 58 + col * 5.6
            v = 19.5 + row * 6.2
            x, y = dock_world(u, v)
            add_cyl(f"k06_tank_{row}_{col}", x, y, 0.0, 8.4, 2.6, m["white"], c, vertices=18)
            add_cyl(f"k06_cap_{row}_{col}", x, y, 8.4, 8.85, 2.75, m["steel"], c, vertices=18)
            add_cyl(f"k06_band_{row}_{col}", x, y, 5.2, 5.6, 2.68, m["evac_blue"], c, vertices=18)
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
    # helipad marking (ring + H bars)
    x, y = dock_world(99, 0)
    add_tube("k11_pad_ring", x, y, 11.0, 9.6, 0.02, 0.05, m["white"], c, 40)
    for i, off in enumerate((-2.4, 2.4)):
        x, y = dock_world(99, off)
        add_box_local(f"k11_pad_bar_{i}", x, y, 0.035, 5.0, 0.8, 0.03, m["white"], c,
                      rot_z=DOCK_ROTZ)
    x, y = dock_world(99, 0)
    add_box_local("k11_pad_cross", x, y, 0.035, 0.8, 3.2, 0.03, m["white"], c, rot_z=DOCK_ROTZ)

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
    avr("fc_apron", 4.0, 74.0, -65.0, 65.0, z + 0.02, z + 0.05, m["garden_walk"], c)
    for sgn in (-1, 1):
        avr(f"fc_apron_edge{sgn}", 4.0, 74.0, sgn * 65.0, sgn * 65.6, z + 0.02, z + 0.09,
            m["garden_border"], c)
    for k in range(6):
        av_box(f"fc_ap_j{k}", 10.0 + k * 11.0, 0, 0.05, 128.0, z + 0.05, z + 0.062,
               m["garden_border"], c)

    # parking band t 74..114: 2 rows x 9 on the west, yard on the east
    avr("fc_park_apron", 74.0, 114.0, -52.0, -6.0, z + 0.015, z + 0.035, m["road"], c)
    for row, vv in enumerate((-42.0, -30.0)):
        for k in range(9):
            tt = 78.0 + k * 3.6
            av_box(f"fc_bay_{row}_{k}", tt, vv, 3.2, 5.2, z + 0.02, z + 0.05,
                   m["garden_border"], c)
        av_box(f"fc_row{row}", 94.0, vv, 32.0, 0.16, z + 0.05, z + 0.08, m["white"], c)
    avr("fc_yard", 74.0, 114.0, 10.0, 50.0, z + 0.015, z + 0.035, m["garden_walk"], c)
    for k in range(3):
        av_box(f"fc_ctn{k}", 84.0 + k * 7.0, 34.0, 6.1, 2.44, z, z + 2.6, m["container_blue"], c)
        av_box(f"fc_ctn2_{k}", 84.0 + k * 7.0, 30.0, 6.1, 2.44, z, z + 2.6, m["container_olive"], c)
    for k in range(4):
        av_box(f"fc_crate_{k}", 80.0 + (k % 2) * 3.2, 16.0 + (k // 2) * 3.4, 2.8, 2.8,
               z, z + 1.1 + 0.2 * (k % 3), m["wood"], c)
    # palms along the apron edges + lamps
    for i, (x, y) in enumerate(PALMS):
        add_cyl(f"palm_trunk_{i}", x, y, z, z + 7.0, 0.30, m["wood"], c, vertices=8)
    for k, tt in enumerate((12.0, 32.0, 52.0, 72.0)):
        for sgn in (-1, 1):
            x, y = av(tt, sgn * 60.0)
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


def build_peninsula(m):
    """v07: the old walled dry dock becomes an open test-workshop peninsula (Q1/Q3).

    Deck, props, evac frame/glow and the G5 container row are kept at their
    dock-world coordinates so G4 probes and the evac point (221,-214) stay put."""
    c = coll("PENINSULA")
    # floor
    dock_box("dock_floor", DOCK_LEN / 2, 0, DOCK_LEN + 1.2, DOCK_HALF * 2 + 1.2,
             -0.5, 0.0, m["apron"], c)
    # v07: walls removed -> pointed tip + low curbs + test hall east of the deck
    tip = [dock_world(96, -DOCK_HALF), dock_world(96, DOCK_HALF), dock_world(114, 0)]
    add_prism("pen_tip", tip, -0.5, 0.0, m["apron"], c)
    dock_box("pen_curb_w", 45, -29.6, 82, 0.5, 0.0, 0.4, m["yellow"], c)
    dock_box("pen_curb_e", 45, 29.6, 82, 0.5, 0.0, 0.4, m["yellow"], c)
    dock_box("test_hall", 40, 38, 44, 20, 0.0, 9.0, m["dock"], c)
    dock_box("test_hall_roof", 40, 38, 45.5, 23, 9.0, 9.6, m["steel"], c)
    for i in range(3):
        dock_box(f"test_hall_win_{i}", 24 + i * 14, 27.9, 0.4, 6.0, 5.0, 7.5, m["emis"], c)
    # (v09: the in-deck ramp is replaced by the avenue ramp at u0..24)
    # drain channel along walls (dark strips)
    dock_box("drain_w", DOCK_LEN / 2, -DOCK_HALF + 0.8, DOCK_LEN, 0.6, 0.0, 0.06, m["dark"], c)
    dock_box("drain_e", DOCK_LEN / 2, DOCK_HALF - 0.8, DOCK_LEN, 0.6, 0.0, 0.06, m["dark"], c)
    # ENTRANCE blue box u18..34 v+10..+24
    dock_box("entrance_box", 26, 22, 16, 13, 0.0, 7.0, m["bluebox"], c)
    dock_box("entrance_door", 18.5, 15.6, 0.4, 3.2, 0.0, 3.5, m["green"], c)
    # container row v=+16, u 40/50/60/70/78 (2 m gap at u=73..75 before last)
    for i, u in enumerate((40, 50, 60, 70, 78)):
        mat = [m["container_blue"], m["container_olive"], m["container_gray"],
               m["container_olive"], m["container_blue"]][i]
        dock_box(f"container_{i}", u, 16, 6, 2.4, 0.0, 2.6, mat, c)
    # pallets u72..86 v-23, x3
    for i, u in enumerate((74, 80, 86)):
        dock_box(f"pallet_{i}", u, -23, 2, 2, 0.0, 1.5, m["wood"], c)
    # oil drums u20 v-23.5
    for i in range(6):
        uu = 19 + (i % 3) * 1.2
        vv = -23.2 - (i // 3) * 1.2
        x, y = dock_world(uu, vv)
        add_cyl(f"drum_{i}", x, y, 0.0, 0.9, 0.3, m["orange"], c, vertices=10)
    # (v09: the Ø3x12 dock pipe is gone — it used to lie across the new avenue)
    # evac frame 4x4 at (u90, v19)
    for du_, dv_, l1, l2 in ((90, 19 - 2.2, 4.4, 0.7), (90, 19 + 2.2, 4.4, 0.7),
                             (90 - 2.2, 19, 0.7, 4.4), (90 + 2.2, 19, 0.7, 4.4)):
        dock_box("evac_frame", du_, dv_, l1, l2, 0.0, 0.06, m["evac"], c)
    # evac glow floor: low-intensity blue light field around the evac frame (M2)
    # v09.1: a round light pool instead of a solid blue slab (it read as a tarp)
    ex, ey = dock_world(90, 19)
    add_cyl("evac_glow", ex, ey, 0.0, 0.04, 6.0, m["evac_floor"], c, vertices=36)
    add_tube("evac_glow_ring", ex, ey, 7.1, 6.6, 0.0, 0.05, m["evac_floor"], c, 36)
    # (v07: dock walls, gate beam, wall rails and wall-mounted blue belt removed
    #  — the peninsula is open; curbs above replace the rails)


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
    """North gate: gatehouse, canopy, checkpoint and a flag mast on the fan head."""
    c = coll("NORTH_GATE")
    z = PLATFORM_Z
    av_box("ng_plaza", -129.0, 0, 24.0, 146.0, z + 0.02, z + 0.04, m["apron"], c)
    for off in (-12.6, 12.6):
        av_box(f"ng_post_{off}", -123.0, off, 0.9, 0.9, z, z + 7.2, m["white"], c)
        av_box(f"ng_postcap_{off}", -123.0, off, 1.3, 1.3, z + 7.2, z + 7.5, m["metal"], c)
    av_box("ng_beam", -123.0, 0, 1.1, 26.4, z + 6.2, z + 7.2, m["white"], c)
    av_box("ng_sign", -122.2, 0, 0.26, 12.0, z + 4.6, z + 6.0, m["evac_blue"], c)
    for off, tag in ((17.5, "w"), (-17.5, "e")):
        av_box(f"ng_booth_{tag}", -126.0, off, 6.0, 5.0, z, z + 3.2, m["container_gray"], c)
        av_box(f"ng_booth_roof_{tag}", -126.0, off, 6.6, 5.6, z + 3.2, z + 3.45, m["steel"], c)
        av_box(f"ng_booth_win_{tag}", -122.95, off, 0.12, 3.4, z + 1.4, z + 2.6, m["glass"], c)
    av_box("ng_guard", -135.0, -22.0, 10.0, 6.0, z, z + 3.4, m["white"], c)
    av_box("ng_guard_roof", -135.0, -22.0, 10.8, 6.8, z + 3.4, z + 3.66, m["steel"], c)
    x, y = av(-133.0, 22.0)
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


def build_core_v11(m):
    c = coll("CORE")
    z = PLATFORM_Z
    for name, t0, t1, v0, v1 in HALLS:
        tc = (t0 + t1) / 2.0
        vc = (v0 + v1) / 2.0
        avr(f"{name.lower()}_floor", t0, t1, v0, v1, z, z + 0.06, m["garden_walk"], c)
        # outer walls
        avr(f"{name.lower()}_wall_n", t0, t0 + 0.3, v0, v1, z, z + HALL_H, m["wall"], c)
        avr(f"{name.lower()}_wall_s", t1 - 0.3, t1, v0, v1, z, z + HALL_H, m["wall"], c)
        # corridor-facing wall gets a 6 m roller door
        side = v1 if v0 > 0 else v0
        avr(f"{name.lower()}_wall_c", t0, t1, side - 0.15, side + 0.15, z, z + HALL_H,
            m["wall"], c)
        roller_door(f"{name.lower()}_rdoor", t0 + 6.0 if name in ("H1", "H3") else t1 - 6.0,
                    side, 6.0, 5.0, z, m, c, face=1.0)
        # roof + parapet
        avr(f"{name.lower()}_roof", t0, t1, v0, v1, z + HALL_H, z + HALL_H + 0.22, m["apron"], c)
        for tag, (a0, a1, b0, b1) in {
                "n": (t0 - 0.3, t0, v0, v1), "s": (t1, t1 + 0.3, v0, v1),
                "w": (t0, t1, v0 - 0.3, v0), "e": (t0, t1, v1, v1 + 0.3)}.items():
            avr(f"{name.lower()}_par_{tag}", a0, a1, b0, b1, z + HALL_H, z + HALL_H + 0.9,
                m["steel"], c)
        # facade kit
        double_door(f"{name.lower()}_ndoor", t0, vc, z, m, c, face=-1.0)
        panel_joints_t(f"{name.lower()}_pj_n", t0, v0, v1, z, HALL_H, -1.0, m, c)
        av_box(f"{name.lower()}_band_n", t0 - 0.34, vc, 0.06, v1 - v0 - 0.6, z + 9.6, z + 10.2,
               m["evac_blue"] if name in ("H1", "H4") else m["dark"], c)
        for k in range(3):
            vv = v0 + 6.0 + k * 10.0
            avr(f"{name.lower()}_ahu{k}", t0 + 6.0, t0 + 12.0, vv, vv + 4.0,
                z + HALL_H + 0.22, z + HALL_H + 1.4, m["steel"], c)

    # cross corridor: N-S (v -5..5) and E-W (t -52..-42), glass roof at 7.5
    avr("corr_ns", CORE_TN, CORE_TS, -5.0, 5.0, z, z + 0.05, m["garden_walk"], c)
    avr("corr_ew", -52.0, -42.0, -CORE_HALF, CORE_HALF, z, z + 0.05, m["garden_walk"], c)
    avr("corr_ns_glass", CORE_TN, CORE_TS, -5.0, 5.0, z + 7.5, z + 7.6, m["glass"], c)
    avr("corr_ew_glass", -52.0, -42.0, -CORE_HALF, CORE_HALF, z + 7.5, z + 7.6, m["glass"], c)
    for k, tt in enumerate((-82.0, -74.0, -66.0, -58.0, -46.0, -38.0, -30.0, -22.0, -14.0)):
        avr(f"corr_truss{k}", tt - 0.22, tt + 0.22, -5.0, 5.0, z + 7.5, z + 8.7, m["steel"], c)
    for k, vv in enumerate((-34.0, -22.0, -10.0, 10.0, 22.0, 34.0)):
        avr(f"corr_beam{k}", -52.0, -42.0, vv - 0.22, vv + 0.22, z + 7.5, z + 8.7, m["steel"], c)
    avr("corr_kerb_ns", CORE_TN, CORE_TS, -5.4, -5.0, z, z + 0.06, m["yellow"], c)
    avr("corr_kerb_ns2", CORE_TN, CORE_TS, 5.0, 5.4, z, z + 0.06, m["yellow"], c)

    # centrifuge drum inside H1
    cx, cy = av(-69.0, -22.0)
    add_cyl("h1_drum", cx, cy, z, z + 19.7, 8.75, m["wall"], c, vertices=40)
    add_cyl("h1_drum_band", cx, cy, z + 3.62, z + 3.98, 8.95, m["evac_blue"], c, vertices=40)
    add_cyl("h1_drum_cap", cx, cy, z + 19.7, z + 20.1, 8.2, m["steel"], c, vertices=40)
    add_cyl("h1_drum_eye", cx, cy, z + 20.1, z + 20.3, 3.2, m["dark"], c, vertices=24)

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


def build_h1(m):
    c = coll("H1_ANCHOR")
    z = PLATFORM_Z
    cx, cy = 90.0, 30.0
    # circular wall Ø44 with two door gaps (north 90°, south 270°)
    for i, (a0, a1) in enumerate(((math.radians(99), math.radians(261)),
                                  (math.radians(279), math.radians(441)))):
        add_tube(f"h1_cwall_{i}", cx, cy, 22.0, 21.65, z, z + 9, m["wall"], c, 48, a0, a1)
        add_tube(f"h1_glass_{i}", cx, cy, 21.9, 21.65, z + 4.5, z + 6.0, m["glass"], c, 48, a0, a1)
    # center column + flanges
    add_cyl("h1_column", cx, cy, z, z + 9, 1.0, m["metal"], c, vertices=16)
    for i in range(8):
        a = math.radians(i * 45)
        add_box_local(f"h1_flange_{i}", cx + 1.0 * math.cos(a), cy + 1.0 * math.sin(a),
                      z + 1.0 + i, 0.3, 0.6, 0.25, m["dark"], c, rot_z=a)
    # pod 18 x Ø4, rot -15
    add_cyl_h("h1_pod", 99, 28, z + 3.5, 14.0, 2.0, m["dark"], c, vertices=20,
              rot_z=math.radians(-15))
    # turntable Ø18
    add_cyl("h1_turntable", 98, 27, z + 0.05, z + 0.35, 9.0, m["yellow"], c, vertices=32)
    for i in range(12):
        a = math.radians(i * 30)
        add_box(f"h1_tick_{i}", 98 + 8.2 * math.cos(a) - 0.1, 98 + 8.2 * math.cos(a) + 0.1,
                27 + 8.2 * math.sin(a) - 0.35, 27 + 8.2 * math.sin(a) + 0.35,
                z + 0.35, z + 0.42, m["dark"], c)
    # roof trusses y=18 / y=42
    for y in (18, 42):
        add_box(f"h1_truss_{y}", 66, 114, y - 0.3, y + 0.3, z + 8.2, z + 9.0, m["steel"], c)
    # control room 10x3.5x3 elevated 2.5 at (76,56)
    add_box("h1_control", 71, 81, 54.25, 57.75, z + 2.5, z + 5.5, m["glass"], c)
    for x in (71.3, 80.7):
        add_box(f"h1_control_leg_{x}", x - 0.25, x + 0.25, 54.5, 57.5, z, z + 2.5, m["steel"], c)


def build_h2(m):
    c = coll("H2_ANCHOR")
    z = PLATFORM_Z
    # pool 36x22 center (86,90), depth 6.5
    px0, px1, py0, py1 = 68, 104, 79, 101
    add_box("h2_pool_floor", px0, px1, py0, py1, z - 6.5, z - 6.4, m["pit"], c)
    for (a0, a1, b0, b1) in ((px0, px1, py0, py0 + 0.3), (px0, px1, py1 - 0.3, py1),
                             (px0, px0 + 0.3, py0, py1), (px1 - 0.3, px1, py0, py1)):
        add_box("h2_pool_wall_%d_%d" % (a0, b0), a0, a1, b0, b1, z - 6.5, z, m["dock"], c)
    add_box("h2_pool_water", px0 + 0.3, px1 - 0.3, py0 + 0.3, py1 - 0.3,
            z - 6.4, z - 0.6, m["pool"], c)
    # rim + rail h1.1
    for (a0, a1, b0, b1) in ((px0 - 0.4, px1 + 0.4, py0 - 0.4, py0), (px0 - 0.4, px1 + 0.4, py1, py1 + 0.4),
                             (px0 - 0.4, px0, py0, py1), (px1, px1 + 0.4, py0, py1)):
        add_box("h2_rim_%d_%d" % (a0, b0), a0, a1, b0, b1, z, z + 1.1, m["teal"], c)
    # pressure capsules Ø4 x14
    for i, (x, y, ang) in enumerate(((76, 88, 20), (104, 108, 0), (96, 95, -10))):
        over_pool = 68 - 2 < x < 104 + 2 and 79 - 2 < y < 101 + 2
        zc = z + 4.2 if over_pool else z + 3.6
        add_cyl_h(f"h2_capsule_{i}", x, y, zc, 14.0, 2.0, m["white"], c, vertices=20,
                  rot_z=math.radians(ang))
        if over_pool:   # suspended from the gantry: two thin cables
            for dx in (-4, 4):
                xx = x + dx * math.cos(math.radians(ang))
                yy = y + dx * math.sin(math.radians(ang))
                add_cyl(f"h2_cable_{i}_{dx}", xx, yy, zc + 2.0, z + 8.5, 0.06, m["dark"], c,
                        vertices=4)
        else:
            for dx in (-5, 5):
                xx = x + dx * math.cos(math.radians(ang))
                yy = y + dx * math.sin(math.radians(ang))
                add_box(f"h2_cradle_{i}_{dx}", xx - 0.4, xx + 0.4, yy - 1.2, yy + 1.2, z, z + 1.6,
                        m["dark"], c)
    # gantry crane span 44 at y=102
    for x in (64, 108):
        add_cyl(f"h2_gantry_leg_{x}", x, 102, z, z + 8.5, 0.7, m["steel"], c, vertices=12)
    add_box("h2_gantry_beam", 62, 110, 101.6, 102.4, z + 8.5, z + 9.5, m["yellow"], c)
    # office cabin elevated at (68,112)
    add_box("h2_office", 63, 73, 109.5, 114.5, z + 2.2, z + 5.4, m["glass"], c)
    for x in (63.4, 72.6):
        for y in (109.9, 114.1):
            add_box(f"h2_office_leg_{x}_{y}", x - 0.25, x + 0.25, y - 0.25, y + 0.25, z, z + 2.2,
                    m["steel"], c)
    # hanging basket 4x3 h7 at (86,96)
    add_box("h2_basket", 84, 88, 94.5, 97.5, z + 2.0, z + 9.0, m["metal"], c)
    add_box("h2_basket_hook", 85.8, 86.2, 95.9, 96.1, z + 9.0, z + 9.5, m["dark"], c)
    # pool ladder at (100,101)
    add_box("h2_ladder", 99.6, 100.4, 100.6, 101.4, z - 6.0, z + 0.6, m["yellow"], c)
    # pool-floor grate 10x6 at (96,86)
    add_box("h2_grate", 91, 101, 83, 89, z - 6.4, z - 6.32, m["teal"], c)


def build_h3(m):
    c = coll("H3_ANCHOR")
    z = PLATFORM_Z
    # pit 24x22 center (148,90), depth 4 — 蓝光坑底（实机 H3 蓝光氛围 + 探针 B 通道）
    px0, px1, py0, py1 = 136, 160, 79, 101
    add_box("h3_pit_floor", px0, px1, py0, py1, z - 4.0, z - 3.9, m["pit_blue"], c)
    for (a0, a1, b0, b1) in ((px0, px1, py0, py0 + 0.3), (px0, px1, py1 - 0.3, py1),
                             (px0, px0 + 0.3, py0, py1), (px1 - 0.3, px1, py0, py1)):
        add_box("h3_pit_wall_%d_%d" % (a0, b0), a0, a1, b0, b1, z - 4.0, z, m["pit_blue"], c)
    # pit rail + east ramp 6x6 at (163,89)
    for (a0, a1, b0, b1) in ((px0 - 0.2, px1 + 0.2, py0 - 0.2, py0), (px0 - 0.2, px1 + 0.2, py1, py1 + 0.2),
                             (px0 - 0.2, px0, py0, py1)):
        add_box("h3_prail_%d_%d" % (a0, b0), a0, a1, b0, b1, z, z + 1.1, m["yellow"], c)
    add_prism("h3_ramp", [(160, 86), (166, 86), (166, 92), (160, 92)],
              -0.3, lambda i, p: z if i in (0, 3) else z - 4.0, m["dock"], c)
    # twin arms at (141,90)/(155,90) on pit floor
    for i, x in enumerate((141, 155)):
        add_cyl(f"h3_arm_base_{i}", x, 90, z - 4.0, z - 2.8, 0.8, m["dark"], c, vertices=12)
        add_box(f"h3_arm_{i}", x - 0.3, x + 0.3, 89.7, 90.3, z - 2.8, z - 0.9, m["orange"], c)
    # satellite 3x3x3 on pedestal
    add_box("h3_sat_ped", 147, 149, 89, 91, z - 4.0, z - 2.8, m["dark"], c)
    add_box("h3_sat_body", 146.5, 149.5, 88.5, 91.5, z - 2.8, z + 0.2, m["gold"], c)
    add_box("h3_sat_panel_a", 142.5, 146.5, 89.6, 90.4, z - 1.6, z - 1.45, m["evac_blue"], c)
    add_box("h3_sat_panel_b", 149.5, 153.5, 89.6, 90.4, z - 1.6, z - 1.45, m["evac_blue"], c)
    # high gallery: north edge y101..102.2 (x134..178), west edge x133.8..135 (y62..101)
    add_box("h3_gal_n", 134, 178, 101, 102.2, z + 4.4, z + 4.65, m["steel"], c)
    add_box("h3_gal_w", 133.8, 135, 62, 101, z + 4.4, z + 4.65, m["steel"], c)
    add_box("h3_stair", 125, 129, 99, 104, z + 0.2, z + 4.4, m["yellow"], c)
    # rib walls (藏蓝) + 6 blue light strips
    for (a0, a1, b0, b1) in ((121, 179, 119.4, 119.7), (179.4, 179.7, 61, 119), (120.3, 120.6, 61, 119)):
        add_box("h3_rib_%d_%d" % (a0, b0), a0, a1, b0, b1, z, z + 4.2, m["rib_blue"], c)
    for i, (a0, a1, b0, b1) in enumerate((
            (136, 146, 119.55, 119.65), (148, 158, 119.55, 119.65), (160, 170, 119.55, 119.65),
            (179.55, 179.65, 80, 95), (179.55, 179.65, 100, 115), (120.35, 120.45, 70, 85))):
        add_box(f"h3_light_{i}", a0, a1, b0, b1, z + 1.45, z + 1.57, m["h3_strip"], c)
    add_box("h3_sign", 141, 147, 119.45, 119.7, z + 5.0, z + 6.0, m["evac_blue"], c)


def build_h4(m):
    c = coll("H4_ANCHOR")
    z = PLATFORM_Z
    h = WALL_H["H4"]
    # green paint panels: 3 on north wall + 1 on east wall (real green only ~10%)
    for i, (a0, a1) in enumerate(((126, 138), (146, 158), (166, 178))):
        add_box(f"h4_panel_n_{i}", a0, a1, 59.3, 59.6, z + 2.0, z + 8.0, m["wall_h4"], c)
    add_box("h4_panel_e", 179.4, 179.7, 8, 20, z + 2.0, z + 8.0, m["wall_h4"], c)
    # barrel vault over north passage: cylinder r5, axis Y, center (150, 54, z+8)
    add_cyl("h4_vault", 150, 54, z + 2.0, z + 14.0, 5.0, m["teal"], c, axis="Y", vertices=24)
    # sealed Ø10 hatch on east wall at (180,28), center z+5
    # sealed Ø10 hatch: 1 m recess disc inside the wall + D-shaped floor marker
    add_cyl("h4_hatch_recess", 180.0, 28, z + 4.5, z + 5.5, 4.5, m["dark"], c, axis="X", vertices=24)
    add_tube("h4_hatch_ring", 179.4, 28, 5.0, 4.75, z + 0.055, z + 0.075, m["dark"], c, 32,
             math.radians(90), math.radians(270))
    add_cyl("h4_hatch_hub", 176.6, 28, z + 0.055, z + 0.076, 0.8, m["dark"], c, vertices=12)
    # three low partitions h3
    add_box("h4_part_a", 126, 138, 9.8, 10.2, z, z + 3.0, m["wall"], c)
    add_box("h4_part_b", 140, 156, 21.8, 22.2, z, z + 3.0, m["wall"], c)
    add_box("h4_part_c", 132, 144, 31.8, 32.2, z, z + 3.0, m["wall"], c)
    # overhead crane: rails + bridge at y=44, hook pod Ø3x5 at (164,44)
    for y in (41.5, 46.5):
        add_box(f"h4_crane_rail_{y}", 122, 178, y - 0.2, y + 0.2, z + 9.2, z + 9.6, m["steel"], c)
    add_box("h4_crane_bridge", 124, 176, 43.6, 44.4, z + 9.6, z + 10.4, m["yellow"], c)
    pod = add_cyl("h4_pod", 164, 44, z + 4.0, z + 9.0, 1.5, m["dark"], c, axis="X", vertices=16)
    pod.rotation_euler[2] = math.radians(90)
    add_box("h4_crane_hook", 163.6, 164.4, 43.6, 44.4, z + 9.0, z + 9.6, m["dark"], c)
    # S11 亮分区条（提高盒内明度跨度）
    add_box("h4_zone_l", 126, 176, 14, 15.2, z + 0.052, z + 0.062, m["zone_light"], c)
    add_box("h4_zone_r", 126, 176, 44.8, 46.0, z + 0.052, z + 0.062, m["zone_light"], c)
    add_box("h4_zone_m", 126, 176, 28, 29.2, z + 0.052, z + 0.062, m["zone_light"], c)


def build_ceo(m):
    c = coll("CEO")
    x0, x1, y0, y1, z0, z1 = CEO
    add_box("ceo_floor", x0, x1, y0, y1, z0, z0 + 0.2, m["caramel"], c)
    add_box("ceo_rug", 108, 132, 55, 65, z0 + 0.2, z0 + 0.24, m["rug"], c)      # S14 亮毯
    add_box("ceo_inlay_n", 102, 138, 71.5, 72.5, z0 + 0.2, z0 + 0.23, m["rug"], c)
    add_box("ceo_inlay_s", 102, 138, 47.5, 48.5, z0 + 0.2, z0 + 0.23, m["rug"], c)
    t = 0.12
    wall_v("ceo_w", x0, y0, y1, z1 - z0, [(67.5, 72.5)], m["glass"], c, t, z0)
    wall_v("ceo_e", x1, y0, y1, z1 - z0, [(52.5, 57.5)], m["glass"], c, t, z0)
    wall_h("ceo_s", y0, x0, x1, z1 - z0, [], m["glass"], c, t, z0)
    wall_h("ceo_n", y1, x0, x1, z1 - z0, [], m["glass"], c, t, z0)
    for x in (x0, 120, x1):
        for y in (y0, y1):
            add_box(f"ceo_post_{x}_{y}", x - 0.16, x + 0.16, y - 0.16, y + 0.16, z0, z1,
                    m["brass"], c)
    for y in (y0, y1):
        add_box(f"ceo_beam_n_{y}", x0, x1, y - 0.08, y + 0.08, z1 - 0.15, z1, m["brass"], c)
    for x in (x0, x1):
        add_box(f"ceo_beam_e_{x}", x - 0.08, x + 0.08, y0, y1, z1 - 0.15, z1, m["brass"], c)
    # v09.1: inner soffit + corner columns so it does not read as a table top
    for (a0, a1, b0, b1) in ((x0 + 0.3, x1 - 0.3, y0 + 0.3, y0 + 1.5),
                             (x0 + 0.3, x1 - 0.3, y1 - 1.5, y1 - 0.3),
                             (x0 + 0.3, x0 + 1.5, y0 + 1.5, y1 - 1.5),
                             (x1 - 1.5, x1 - 0.3, y0 + 1.5, y1 - 1.5)):
        add_box(f"ceo_soffit_{a0}_{b0}", a0, a1, b0, b1, z0 + 0.2, z0 + 0.26, m["soffit"], c)
    for cx in (x0 + 2.0, 120.0, x1 - 2.0):
        for cy in (y0 + 2.0, y1 - 2.0):
            add_box(f"ceo_col_{cx}_{cy}", cx - 0.28, cx + 0.28, cy - 0.28, cy + 0.28,
                    z0 + 0.2, z1 - 0.1, m["white"], c)
    # M1 open top: parapet 0.6 + brass coping 0.2 (visible 1.4 px @7 px/m)
    for (a0, a1, b0, b1) in ((x0 - 0.2, x1 + 0.2, y0 - 0.2, y0 + 0.1),
                             (x0 - 0.2, x1 + 0.2, y1 - 0.1, y1 + 0.2),
                             (x0 - 0.2, x0 + 0.1, y0, y1), (x1 - 0.1, x1 + 0.2, y0, y1)):
        add_box(f"ceo_parapet_%d_%d" % (a0, b0), a0, a1, b0, b1, z1, z1 + 0.6, m["wall"], c)
        add_box(f"ceo_coping_%d_%d" % (a0, b0), a0 - 0.06, a1 + 0.06, b0 - 0.06, b1 + 0.06,
                z1 + 0.6, z1 + 0.8, m["brass"], c)
    # 0.8 m overhanging eave just below the top -> 0.3-0.5 m dark rim inside the box
    for (a0, a1, b0, b1) in ((x0 - 0.8, x1 + 0.8, y0 - 0.8, y0),
                             (x0 - 0.8, x1 + 0.8, y1, y1 + 0.8),
                             (x0 - 0.8, x0, y0, y1), (x1, x1 + 0.8, y0, y1)):
        add_box(f"ceo_eave_%d_%d" % (a0, b0), a0, a1, b0, b1, z1 - 0.35, z1 - 0.1, m["wood"], c)
    # frosted screen x=120 y53..67
    add_box("ceo_screen", 119.925, 120.075, 53, 67, z0 + 0.2, z0 + 3.7, m["frost"], c)
    # hatches + ladders below
    for (hx, hy) in ((111, 67.2), (129, 52.8)):
        add_box(f"ceo_hatch_{hx}_{hy}", hx - 1.5, hx + 1.5, hy - 1.5, hy + 1.5, z0, z0 + 0.06,
                m["yellow"], c)
        add_box(f"ceo_ladder_{hx}_{hy}", hx - 0.4, hx + 0.4, hy - 0.1, hy + 0.1, PLATFORM_Z, z0,
                m["metal"], c)
    # 6-8 wall plants (real model bushes along the three blind walls)
    for i, (px_, py_) in enumerate(((104, 47), (112, 47), (128, 47), (136, 47),
                                    (102, 73), (118, 73), (134, 73), (138, 62))):
        add_cyl(f"ceo_plantpot_{i}", px_, py_, z0 + 0.2, z0 + 0.55, 0.45, m["brass"], c,
                vertices=10)
        add_cyl(f"ceo_plant_{i}", px_, py_, z0 + 0.55, z0 + 1.75, 0.75, m["foliage"], c,
                vertices=10)
    # warm interior lights, dimmed (open top -> sun does the lighting)
    for i, (x, y) in enumerate(((111, 60), (129, 60))):
        ld = bpy.data.lights.new(f"CEO_warm_{i}", "AREA")
        ld.shape = "SQUARE"; ld.size = 8; ld.energy = 25
        ld.color = hex_rgba("#FFD9A8")[:3]
        lo = bpy.data.objects.new(f"CEO_warm_{i}", ld)
        bpy.context.scene.collection.objects.link(lo)
        lo.location = (x, y, z1 - 0.4)



# ------------------------------------------------------------------ detail pass (v04)
COPING = {"H1": "#7195A4", "H2": "#609BAE", "H3": "#4B83CC", "H4": "#75A29D"}


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
        w = min(0.08, mind * 0.22)
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
    cam.location = (147.60, -68.62, 300.0)
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
    sun.rotation_euler = (math.radians(46), 0, math.radians(-70))
    sun_data.energy = 4.4
    sun_data.angle = math.radians(2.2)
    sun_data.color = hex_rgba("#FFE7C4")[:3]

    # --- gradient sky
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 0.62
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
    sc.view_settings.exposure = 0.22
    try:
        sc.view_settings.look = "None"
    except Exception:
        pass
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"


def ao_ground(m, distance=1.6, strength=0.42):
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
def _tex_mix(mat, mode="grain", scale=6.0, lo=0.80, hi=1.06, mortar=0.72):
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


def apply_surface_textures(m):
    """B1-B4: four families of surface treatment, box-projected (no UV, no bake)."""
    _tex_mix(m["road"], "grain", 2.2, 0.74, 1.05)         # B1 asphalt aggregate
    _tex_mix(m["apron"], "panel", 1.6, 0.86, 1.02, 0.80)   # B2 concrete slabs
    _tex_mix(m["platform"], "panel", 0.9, 0.88, 1.02, 0.84)
    _tex_mix(m["dock"], "panel", 0.7, 0.84, 1.03, 0.78)    # B3 painted wall panels
    _tex_mix(m["wall"], "panel", 0.7, 0.88, 1.02, 0.82)
    _tex_mix(m["steel"], "grain", 3.0, 0.84, 1.05)         # B4 corrugated metal
    _tex_mix(m["white"], "grain", 1.4, 0.90, 1.02)
    _tex_mix(m["water"], "grain", 0.03, 0.86, 1.05)       # slow current variation
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


def main():
    a = parse_args()
    clear_scene()
    m = build_materials()
    build_terrain(m)
    build_north_gate(m)
    build_core_v11(m)
    build_avenue(m)
    build_forecourt(m)
    build_garden(m)
    build_street_kit(m)
    build_horizon(m)
    build_peninsula(m)
    build_cards(m)
    build_shore(m)
    build_ridges(m)
    build_hero_fog()
    build_scale_anchor(m)
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
