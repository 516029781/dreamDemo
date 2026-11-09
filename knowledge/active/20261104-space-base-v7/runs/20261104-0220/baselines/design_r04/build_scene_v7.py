"""Procedural builder for space_base_minigame v07 — landmark alignment (r04).

v06 -> v07 changes (SPACE_BASE_LANDMARK_ALIGNMENT_PLAN_20261104.md, confirmed):
  L1  north + east channels cut from the platform -> core becomes an island
  L2  ctrl bridge (N) + east suspension bridge (E) cross the channels
  L3  north outer band: dormitory x3 + control tower h22 + elevated staff tunnel
  L4  east outer band: print/hoist/assembly blocks + tank farm + containers
  L5  SW diagonal launch strip into the sea (pad + gantry + rocket silhouette)
  L6  dry dock -> open test-workshop peninsula (walls removed, pointed tip,
      test hall added; deck/props/evac kept at dock coords so G4/G5 hold)
  Q2  garden removed; fountain (r7) + 4 palms moved onto the island margins
  Hero: ridges kept for the 17/8 deg promo views (30 deg hero cannot see them,
  geometric fact documented in build_ridges)

Run:
  blender -b --factory-startup --python tools/blender_space_base/build_scene_v7.py -- \
    --out art/static_map/space_base_minigame/v07/scene.blend \
    --render art/static_map/space_base_minigame/v07/renders/master_raw.png \
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
OCT = [(72, -14), (168, -14), (194, 8), (194, 112), (168, 134), (72, 134), (46, 112), (46, 8)]
# v07 landmark alignment (SPACE_BASE_LANDMARK_ALIGNMENT_PLAN_20261104.md §4):
# island + channel + two bridges + outer bands (Q1), garden removed (Q2)
CHAN_N = (44, 196, 120, 134)          # north channel strip cut from platform
CHAN_E = (180, 196, -16, 136)         # east channel strip cut from platform
PALMS = [(53, 8), (53, 112), (76, -7), (164, -7)]   # 4 palms moved from garden (Q2)
CAUSE_A = (160.0, -58.0)              # island SE exit
CAUSE_B = (172.0, -136.0)             # peninsula NW neck
CAUSE_W = 18.0
DOCK_O = (172.0, -136.0)
DOCK_U = (math.sin(math.radians(20)), -math.cos(math.radians(20)))   # SE, len 96
DOCK_V = (math.cos(math.radians(20)), math.sin(math.radians(20)))    # NE, half 25
DOCK_LEN, DOCK_HALF = 96.0, 25.0
DOCK_WALL_H = 9.0

ROOMS = {
    "H1": (60, 120, 0, 60),
    "H2": (60, 120, 60, 120),
    "H3": (120, 180, 60, 120),
    "H4": (120, 180, 0, 60),
}
WALL_H = {"H1": 9.0, "H2": 9.0, "H3": 9.0, "H4": 13.0}
DOOR_W = 3.2
GATES = {"G1": (90.0, 60), "G2": (150.0, 60), "E1": (90.0, 0),
         "E2": (150.0, 0), "E3": (90.0, 120), "E4": (150.0, 120)}

CEO = (100, 140, 45, 75, 12.0, 16.5)   # x0,x1,y0,y1,z0,z1

PLATFORM_Z = 6.0
WATER_TOP = 0.0


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
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
        [], [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    mesh.validate(); mesh.update()
    return _mesh_obj(name, mesh, mat, c)


def add_box_local(name, cx, cy, cz, dx, dy, dz, mat, c, rot_z=0.0):
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


C_C5 = _compensated("#95755B", 29, 0.44, 0.62)   # r1 补偿基色，r2 实测 PASS


def build_materials():
    return {
        "water": make_mat("v6.water", "#16333A", 0.25, 0.0, 1.0, "#0F282E", 0.55),
        "platform": make_mat("v6.platform", "#B4B0A2", 0.9),       # S1 提亮
        "garden": make_mat("v6.garden", "#B8AC96", 0.9),           # 压暗后微调回
        "dock": make_mat("v6.dock", "#788980", 0.9),               # 灰绿工业（试车间）
        "causeway": make_mat("v6.causeway", "#B6B5AB", 0.9),
        "island": make_mat("v6.island", "#7E8482", 0.95),
        "h1": make_mat("v6.h1", _hsl_hex(208, 1.0, 0.24), 0.9, 0.0, 1.0, "#547684", 0.60),
        "h2": make_mat("v6.h2", _hsl_hex(212, 1.0, 0.30), 0.9, 0.0, 1.0, "#477A8A", 0.32),
        "h3": make_mat("v6.h3", _hsl_hex(224, 1.0, 0.12), 0.9, 0.0, 1.0, "#3A6DBF", 0.88),
        "h4": make_mat("v6.h4", _hsl_hex(185, 0.44, 0.285), 0.9),
        "wall": make_mat("v6.wall", "#E2DDD0", 0.65),
        "wall_h4": make_mat("v6.wall_h4", "#4A7A5A", 0.65),        # 涂装板绿（仅 3-4 块）
        "rib_blue": make_mat("v6.rib_blue", "#3E5CA8", 0.6, 0.2),  # H3 肋板藏蓝（r6 增饱和）
        "h3_strip": make_mat("v6.h3_strip", "#4C86D8", 0.4, 0.0, 1.0, "#4C86D8", 1.9),
        "green_in": make_mat("v6.green_in", "#357F52", 0.7),
        "glass": make_mat("v6.glass", "#A9BEC6", 0.1, 0.0, 0.42),
        "frost": make_mat("v6.frost", "#D8E2E4", 0.5, 0.0, 0.55),
        "metal": make_mat("v6.metal", "#59676D", 0.5, 0.45),
        "steel": make_mat("v6.steel", "#7E8A8C", 0.45, 0.6),
        "dark": make_mat("v6.dark", "#1E2427", 0.8),
        "white": make_mat("v6.white", "#E8ECEC", 0.6),
        "yellow": make_mat("v6.yellow", "#F2C230", 0.55),
        "evac_blue": make_mat("v6.evac_blue", "#2E6FA8", 0.5),
        "evac_floor": make_mat("v6.evac_floor", "#2E5FC0", 0.8, 0.0, 1.0, "#2E5FC0", 0.9),
        "evac": make_mat("v6.evac", "#FFE010", 0.45, 0.0, 1.0, "#FFE010", 5.0),
        "green": make_mat("v6.green", "#3E9B63", 0.6),
        "pool": make_mat("v6.pool", "#123B47", 0.22),
        "pit": make_mat("v6.pit", "#151C20", 0.8),
        "pit_blue": make_mat("v6.pit_blue", "#0E1E33", 0.8, 0.0, 1.0, "#1E3A66", 0.85),
        "zone_blue": make_mat("v6.zone_blue", "#8AA6C8", 0.85),    # H3 蓝灰分区带
        "zone_blight": make_mat("v6.zone_blight", "#8FB0DC", 0.85),  # H3 蓝调亮条
        "brass": make_mat("v6.brass", "#AA8355", 0.35, 0.8),
        "gold": make_mat("v6.gold", "#C9A227", 0.4, 0.7),
        "caramel": make_mat("v6.caramel", C_C5, 0.72, 0.0, 1.0, "#E8D6B4", 0.07),
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
    }


# ------------------------------------------------------------------ terrain
def build_terrain(m):
    g = coll("TERRAIN")
    # water sheet 2000x2000 (M3: runs past every crop edge)
    add_box("water", -1000, 1000, -1000, 1000, WATER_TOP - 0.35, WATER_TOP - 0.12, m["water"], g)
    # octagon platform +6 with seawall skirt; boolean holes for pool (H2) and pit (H3)
    plat = add_prism("core_platform", OCT, -0.4, PLATFORM_Z, m["platform"], g)
    for nm, (hx0, hx1, hy0, hy1) in (("cut_pool", (68, 104, 79, 101)),
                                     ("cut_pit", (136, 160, 79, 101))):
        cut = add_box(nm, hx0, hx1, hy0, hy1, -1.2, 7.2, m["platform"], g)
        mod = plat.modifiers.new("bool_" + nm, "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = cut
        bpy.context.view_layer.objects.active = plat
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cut, do_unlink=True)
    # v07 channels: cut north + east strips -> core becomes an island (Q1)
    for nm, (cx0, cx1, cy0, cy1) in (("cut_chan_n", CHAN_N), ("cut_chan_e", CHAN_E)):
        cut = add_box(nm, cx0, cx1, cy0, cy1, -1.2, 7.2, m["platform"], g)
        mod = plat.modifiers.new("bool_" + nm, "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = cut
        bpy.context.view_layer.objects.active = plat
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cut, do_unlink=True)
    # quay copings along the four channel faces
    add_box("cope_n_isl", 46, 180, 119.5, 120.0, PLATFORM_Z, PLATFORM_Z + 0.15, m["white"], g)
    add_box("cope_n_band", 24, 196, 134.0, 134.5, PLATFORM_Z, PLATFORM_Z + 0.15, m["white"], g)
    add_box("cope_e_isl", 179.5, 180.0, -14, 120, PLATFORM_Z, PLATFORM_Z + 0.15, m["white"], g)
    add_box("cope_e_band", 194.0, 194.5, -14, 134, PLATFORM_Z, PLATFORM_Z + 0.15, m["white"], g)
    # causeway (sloped +6 -> +3)
    ax, ay = CAUSE_A
    bx, by = CAUSE_B
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    px, py = -uy, ux
    hw = CAUSE_W / 2
    pts = [(ax + px * hw, ay + py * hw), (bx + px * hw, by + py * hw),
           (bx - px * hw, by - py * hw), (ax - px * hw, ay - py * hw)]
    add_prism("causeway", pts, -0.4,
              lambda i, p: PLATFORM_Z if i in (0, 3) else PLATFORM_Z - 3.0, m["causeway"], g)
    # viewing platforms at the cut corners (east pair moved onto the island, Q2)
    for cx, cy in ((169, 11), (169, 109), (59, 109), (59, 11)):
        add_box(f"view_{cx}_{cy}", cx - 11, cx + 11, cy - 11, cy + 11,
                PLATFORM_Z, PLATFORM_Z + 0.04, m["garden"], g)
    # parapet 1.2 m along the 8 octagon edges
    for i in range(len(OCT)):
        ax_, ay_ = OCT[i]
        bx_, by_ = OCT[(i + 1) % len(OCT)]
        segs = [((ax_, ay_), (bx_, by_))]
        if i == 0:   # south edge: 20 m gap at x110..130 for the garden gate
            segs = [((ax_, ay_), (110, ay_)), ((130, ay_), (bx_, by_))]
        for k, ((sx, sy), (ex, ey)) in enumerate(segs):
            mx, my = (sx + ex) / 2, (sy + ey) / 2
            ang = math.atan2(ey - sy, ex - sx)
            L2 = math.hypot(ex - sx, ey - sy)
            add_box_local(f"parapet_{i}_{k}", mx, my, PLATFORM_Z + 0.6, L2, 0.35, 1.2,
                          m["white"], g, rot_z=ang)
    # (v07: garden parapet removed with the garden, Q2)


def build_peninsula(m):
    """v07: the old walled dry dock becomes an open test-workshop peninsula (Q1/Q3).

    Deck, props, evac frame/glow and the G5 container row are kept at their
    dock-world coordinates so G4 probes and the evac point (221,-214) stay put."""
    c = coll("PENINSULA")
    # floor
    dock_box("dock_floor", DOCK_LEN / 2, 0, DOCK_LEN + 1.2, DOCK_HALF * 2 + 1.2,
             -0.5, 0.0, m["dock"], c)
    # v07: walls removed -> pointed tip + low curbs + test hall east of the deck
    tip = [dock_world(96, -25), dock_world(96, 25), dock_world(114, 0)]
    add_prism("pen_tip", tip, -0.5, 0.0, m["dock"], c)
    dock_box("pen_curb_w", 50, -24.6, 92, 0.5, 0.0, 0.4, m["yellow"], c)
    dock_box("pen_curb_e", 50, 24.6, 92, 0.5, 0.0, 0.4, m["yellow"], c)
    dock_box("test_hall", 40, 38, 44, 20, 0.0, 9.0, m["dock"], c)
    dock_box("test_hall_roof", 40, 38, 45.5, 23, 9.0, 9.6, m["steel"], c)
    for i in range(3):
        dock_box(f"test_hall_win_{i}", 24 + i * 14, 27.9, 0.4, 6.0, 5.0, 7.5, m["emis"], c)
    # ramp along west wall: u6..66, v-20.5..-15.5, +3 -> 0
    ramp = [dock_world(u, v) for u, v in ((6, -20.5), (66, -20.5), (66, -15.5), (6, -15.5))]
    add_prism("dock_ramp", ramp,
              lambda i, p: -0.35,
              lambda i, p: 3.0 if i in (0, 3) else 0.0, m["causeway"], c)
    # ramp-bottom platform u66..78, v-22..-10
    dock_box("ramp_platform", 72, -16, 12, 12, 0.0, 0.25, m["dock"], c)
    # drain channel along walls (dark strips)
    dock_box("drain_w", DOCK_LEN / 2, -DOCK_HALF + 0.8, DOCK_LEN, 0.6, 0.0, 0.06, m["dark"], c)
    dock_box("drain_e", DOCK_LEN / 2, DOCK_HALF - 0.8, DOCK_LEN, 0.6, 0.0, 0.06, m["dark"], c)
    # ENTRANCE blue box u18..34 v+10..+24
    dock_box("entrance_box", 26, 17, 16, 14, 0.0, 7.0, m["bluebox"], c)
    dock_box("entrance_door", 18.5, 10.2, 0.4, 3.2, 0.0, 3.5, m["green"], c)
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
    # pipe Ø3 x12 at u40 v+4
    x, y = dock_world(40, 4)
    add_cyl_h("dock_pipe", x, y, 1.5, 12.0, 1.5, m["metal"], c, vertices=16, rot_z=DOCK_ROTZ)
    # evac frame 4x4 at (u90, v19)
    for du_, dv_, l1, l2 in ((90, 19 - 2.2, 4.4, 0.4), (90, 19 + 2.2, 4.4, 0.4),
                             (90 - 2.2, 19, 0.4, 4.4), (90 + 2.2, 19, 0.4, 4.4)):
        dock_box("evac_frame", du_, dv_, l1, l2, 0.0, 0.06, m["evac"], c)
    # evac glow floor: low-intensity blue light field around the evac frame (M2)
    dock_box("evac_glow", 90, 19, 22, 18, 0.0, 0.045, m["evac_floor"], c)
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
    sx, sy = 74.0, -12.0
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


def build_island_green(m):
    """v07 Q2: fountain + 4 palms moved from the deleted garden onto the island margins."""
    c = coll("ISLAND_GREEN")
    z = PLATFORM_Z
    add_tube("fountain_ring", 120, -7, 7.0, 3.0, z, z + 0.5, m["pool"], c, 40)
    add_cyl("fountain_isle", 120, -7, z, z + 0.8, 3.0, m["garden"], c, vertices=24)
    add_cyl("fountain_core", 120, -7, z + 0.8, z + 4.5, 0.9, m["teal"], c, vertices=12)
    add_cyl("fountain_core_top", 120, -7, z + 4.5, z + 4.9, 1.6, m["metal"], c, vertices=12)
    for i, (x, y) in enumerate(PALMS):
        add_cyl(f"palm_trunk_{i}", x, y, z, z + 6.5, 0.35, m["wood"], c, vertices=8)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=2.6, location=(x, y, z + 7.2))
        crown = bpy.context.object
        crown.name = f"palm_crown_{i}"
        for cc in list(crown.users_collection):
            cc.objects.unlink(crown)
        c.objects.link(crown)
        crown.scale = (1.0, 1.0, 0.5)
        crown.data.materials.append(m["foliage"])


# ------------------------------------------------------------------ core rooms
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


def build_rooms(m):
    c = coll("ROOMS")
    z = PLATFORM_Z
    floors = {"H1": m["h1"], "H2": m["h2"], "H3": m["h3"], "H4": m["h4"]}
    HOLES = {"H2": (68, 104, 79, 101), "H3": (136, 160, 79, 101)}
    for key, (x0, x1, y0, y1) in ROOMS.items():
        h = WALL_H[key]
        if key in HOLES:
            hx0, hx1, hy0, hy1 = HOLES[key]
            for i, (a0, a1, b0, b1) in enumerate(((x0, x1, y0, hy0), (x0, x1, hy1, y1),
                                                  (x0, hx0, hy0, hy1), (hx1, x1, hy0, hy1))):
                add_box(f"floor_{key}_{i}", a0, a1, b0, b1, z, z + 0.05, floors[key], c)
        else:
            add_box(f"floor_{key}", x0, x1, y0, y1, z, z + 0.05, floors[key], c)
        g = room_gates(x0, x1, y0, y1)
        mat = m["wall"]   # v06: H4 walls are base wall; green only as 3-4 panels
        wall_h(f"{key}_wall_n", y1, x0, x1, h, g["n"], mat, c)
        wall_h(f"{key}_wall_s", y0, x0, x1, h, g["s"], mat, c)
        wall_v(f"{key}_wall_e", x1, y0, y1, h, g["e"], mat, c)
        wall_v(f"{key}_wall_w", x0, y0, y1, h, g["w"], mat, c)
    # x=120 median wall: solid, no openings (built as the two rooms' e/w walls above)
    # roof rail: two bright beams over x=118.4..121.6 slot, y0..120, z above box top
    for x in (118.4, 121.2):
        add_box(f"roof_rail_{x}", x, x + 0.4, 0, 120, 16.6, 17.0, m["emis"], c)
    for y in (1.0, 119.0):
        add_box(f"rail_pylon_{y}", 118.2, 121.8, y - 1, y + 1, 9.0, 16.6, m["metal"], c)


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
    for (hx, hy) in ((110, 68), (130, 52)):
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
    for i, (x, y) in enumerate(((110, 60), (130, 60))):
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
    mat = make_mat("v5.joint", "#8C8578", 0.9)
    for key, (x0, x1, y0, y1) in ROOMS.items():
        add_floor_grid(f"joint_{key}", x0 + 0.3, x1 - 0.3, y0 + 0.3, y1 - 0.3, 3.0,
                       PLATFORM_Z + 0.055, 0.045, mat, c)


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
    lamps = [(80, -12.6), (110, -12.6), (140, -12.6), (160, -12.6),
             (198.6, 20), (198.6, 60), (198.6, 100),
             (80, 136.6), (110, 136.6), (140, 136.6), (160, 136.6),
             (47.4, 100), (47.4, 60), (47.4, 20)]
    for i, (x, y) in enumerate(lamps):
        add_cyl(f"rd_lamp_{i}", x, y, z, z + 6.0, 0.15, pole, c, vertices=8)
        add_cyl(f"rd_lamp_head_{i}", x, y, z + 5.9, z + 6.25, 0.45, m["emis"], c, vertices=10)
    # bollards x14 (east/north rows moved onto the outer bands)
    bolls = [(84, -13.4), (108, -13.4), (132, -13.4), (156, -13.4),
             (196.4, 24), (196.4, 48), (196.4, 72), (196.4, 96),
             (156, 135.4), (132, 135.4), (108, 135.4), (84, 135.4),
             (46.6, 96), (46.6, 72), (46.6, 48), (46.6, 24)]
    for i, (x, y) in enumerate(bolls):
        add_cyl(f"boll_{i}", x, y, z, z + 0.5, 0.28, m["dark"], c, vertices=8)
    # life rings x8 (east/north pairs moved onto the outer bands)
    rings = [(72, -13.4), (168, -13.4), (196.4, 8), (196.4, 112),
             (72, 135.4), (168, 135.4), (46.6, 112), (46.6, 8)]
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
    benches = [((100, -4), 0), ((140, -4), 0), ((176, 20), 90), ((176, 100), 90),
               ((100, 124), 0), ((140, 124), 0), ((64, 20), 90), ((64, 100), 90)]
    for i, ((x, y), ang) in enumerate(benches):
        add_box_local(f"bench_rd_{i}", x, y, z + 0.25, 1.8, 0.6, 0.5, m["wood"], c,
                      rot_z=math.radians(ang))
    # barriers x4 at the two west viewing platforms (east pair removed with margin)
    for i, (x, y) in enumerate(((56, 4), (62, 18), (56, 102), (62, 116))):
        add_box_local(f"barrier_{i}", x, y, z + 0.55, 1.6, 0.5, 1.1, m["orange"], c,
                      rot_z=math.radians(0))
    # container clusters x3 (west near gate; the SE trio moved to the east band)
    for i, (x, y, ang) in enumerate(((20, 44, 90), (20, 52, 90), (26, 44, 90))):
        add_box_local(f"oc_{i}", x, y, z + 1.3, 6, 2.4, 2.6,
                      [m["container_blue"], m["container_olive"], m["container_gray"]][i % 3],
                      c, rot_z=math.radians(ang))
    # direction signs x2
    for i, (x, y, ang) in enumerate(((126, -13.2, 0), (164, -60, 32))):
        add_box_local(f"dsign_{i}", x, y, z + 2.2, 2.6, 0.1, 0.9, m["evac_blue"], c,
                      rot_z=math.radians(ang))
        add_cyl(f"dsign_pole_{i}", x, y, z, z + 2.2, 0.08, pole, c, vertices=6)
    # (v07: garden benches/bins removed with the garden, Q2)
    # causeway pipe rack (west side, 2 pipes + posts + 3 loops)
    ax, ay = CAUSE_A
    bx, by = CAUSE_B
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    px, py = -uy, ux
    ang = math.atan2(dy, dx)
    off = 6.4
    for i, dz in enumerate((0.0, 0.8)):
        x0c, y0c = ax + px * -off + ux * L * 0.5, ay + py * -off + uy * L * 0.5
        o = add_cyl_h(f"cw_pipe_{i}", x0c, y0c, z + 2.2 + dz, L * 0.88, 0.3, m["metal"], c,
                      vertices=10)
        o.rotation_euler = (math.radians(90), 0, ang + math.pi / 2)
    for i in range(5):
        t = 0.1 + i * 0.2
        xc, yc = ax + px * -off + ux * L * t, ay + py * -off + uy * L * t
        add_box(f"cw_post_{i}", xc - 0.25, xc + 0.25, yc - 0.25, yc + 0.25, z, z + 2.2, pole, c)
    for i in range(3):
        t = 0.3 + i * 0.3
        xc, yc = ax + px * -off + ux * L * t, ay + py * -off + uy * L * t
        bpy.ops.mesh.primitive_torus_add(major_radius=0.9, minor_radius=0.28,
                                         location=(xc, yc, z + 2.5),
                                         rotation=(0, 0, ang))
        o = bpy.context.object
        o.name = f"cw_loop_{i}"
        for cc in list(o.users_collection):
            cc.objects.unlink(o)
        c.objects.link(o)
        o.data.materials.append(m["metal"])
    # causeway lamps x3 east side
    for i in range(3):
        t = 0.2 + i * 0.3
        xc, yc = ax + px * 6.4 + ux * L * t, ay + py * 6.4 + uy * L * t
        add_cyl(f"cw_lamp_{i}", xc, yc, z, z + 5.5, 0.14, pole, c, vertices=8)
        add_cyl(f"cw_lamp_head_{i}", xc, yc, z + 5.4, z + 5.7, 0.4, m["emis"], c, vertices=10)
    # viewing platform lamps x4 (east pair moved onto the island)
    for i, (x, y) in enumerate(((169, 11), (169, 109), (59, 109), (59, 11))):
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
    # (v07: garden grass grid + edge bushes removed with the garden, Q2)
    print("CARDS palms=%d" % len(PALMS))


def build_shore(m):
    """Shallow-water band + wet edge around platform, garden and dock."""
    c = coll("SHORE")
    shallow = make_mat("v5.shallow", "#2E5A5F", 0.25, 0.0, 1.0, "#1C3C40", 0.35)
    z0, z1 = -0.34, -0.07
    ccx, ccy = 120.0, 60.0
    for i in range(len(OCT)):
        a = OCT[i]
        b = OCT[(i + 1) % len(OCT)]
        a2 = (ccx + (a[0] - ccx) * 1.09, ccy + (a[1] - ccy) * 1.09)
        b2 = (ccx + (b[0] - ccx) * 1.09, ccy + (b[1] - ccy) * 1.09)
        add_prism(f"shore_oct_{i}", [a, b, b2, a2], z0, z1, shallow, c)
    # (v07: garden shores removed with the garden, Q2)
    bands = [
        [(-8, -33), (-8, 33), (-13, 33), (-13, -33)],     # north gate side
        [(104, -33), (104, 33), (109, 33), (109, -33)],   # south end
        [(-8, -33), (104, -33), (104, -38), (-8, -38)],   # west
        [(-8, 33), (104, 33), (104, 38), (-8, 38)],       # east
    ]
    for i, quad in enumerate(bands):
        add_prism(f"shore_dock_{i}", [dock_world(*p) for p in quad], z0, z1, shallow, c)
    # v07: outer band seaward shores
    add_prism("shore_band_n", [(24, 184), (238, 184), (238, 190), (24, 190)],
              z0, z1, shallow, c)
    add_prism("shore_band_e", [(240, -14), (240, 134), (246, 134), (246, -14)],
              z0, z1, shallow, c)


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
    add_box("eq_h3_crate_a", 165, 173, 67, 71, z, z + 1.2, m["dark"], c)
    add_box("eq_h3_strip_l", 142, 162, 103, 106.5, z + 0.052, z + 0.062, m["zone_blight"], c)
    add_box("eq_h3_crate_b", 165, 173, 107, 111, z, z + 1.0, m["dark"], c)
    add_box("eq_h4_chest", 172, 174, 8.4, 9.6, z, z + 0.9, m["container_olive"], c)
    for k in range(3):
        add_box(f"eq_h4_chest_lid_{k}", 172.05, 173.95, 8.45 + k * 0.38, 8.48 + k * 0.38,
                z + 0.9, z + 0.94, m["dark"], c)


def build_extra_props(m):
    """25 readable small props + pool/pit work lights."""
    c = coll("PROPS5")
    z = PLATFORM_Z
    # traffic cones
    cones = [(166, -58), (160, -64), (156, -66), (166, -149), (170, -151), (112, -12)]
    for i, (x, y) in enumerate(cones):
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
    for i, (x, y) in enumerate(((74, 72), (77, 72), (168, 12), (170, 12))):
        add_cyl(f"prop_drum_{i}", x, y, z, z + 0.9, 0.3, m["orange"] if i < 2 else m["container_olive"],
                c, vertices=12)
        add_cyl(f"prop_drum_ring_{i}", x, y, z + 0.25, z + 0.3, 0.32, m["dark"], c, vertices=12)
    # cable coils
    for i, (x, y) in enumerate(((96, 52), (128, 112), (150, 8))):
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
    for i, (y0, y1, x) in enumerate(((6, 46, 61.0), (61, 118, 121.3))):
        length = abs(y1 - y0)
        add_cyl_h(f"prop_run_v_{i}", x, (y0 + y1) / 2, z + 1.2, length, 0.09, m["metal"], c,
                  vertices=8, rot_z=math.radians(90))
    # hanging lamps (emissive discs under the roof line)
    for i, (x, y, zz) in enumerate(((90, 30, 13.5), (76, 20, 12.5), (90, 90, 12.0),
                                     (150, 90, 12.0), (150, 30, 15.0), (172, -150, 8.2))):
        add_cyl(f"prop_lamp_{i}", x, y, z + zz - 0.12, z + zz, 0.55, m["emis"], c, vertices=12)
        add_cyl(f"prop_lamp_cord_{i}", x, y, z + zz, z + zz + 0.6, 0.04, m["dark"], c, vertices=6)
    # pit work lamp + pool underwater lights (pit lamp cool blue: H3 是蓝室，暖灯会洗色)
    ld = bpy.data.lights.new("PitLight", "AREA")
    ld.shape = "SQUARE"; ld.size = 8; ld.energy = 2500
    ld.color = hex_rgba("#B9CEE0")[:3]
    lo = bpy.data.objects.new("PitLight", ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = (148, 90, z + 3.0)
    for i, (x, y) in enumerate(((78, 84), (96, 96))):
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
            add_box(f"truss_{key}_{k}", x0 + 0.4, x1 - 0.4, yy - 0.25, yy + 0.25,
                    zt, zt + 0.4, m["steel"], c)
        for k, (lx, ly) in enumerate(((x0 + 18, y0 + 18), (x1 - 18, y0 + 18),
                                      (x0 + 18, y1 - 18), (x1 - 18, y1 - 18))):
            add_cyl(f"rlamp_{key}_{k}", lx, ly, z + 6.3, z + 6.55, 0.5, m["emis"], c,
                    vertices=10)
            add_cyl(f"rlamp_cord_{key}_{k}", lx, ly, z + 6.55, z + wt - 0.45, 0.03,
                    m["dark"], c, vertices=4)
    # crane beams: H4 x2, H3 x1 (1.2 x 0.6, floor +8 m)
    for k, yy in enumerate((20.0, 40.0)):
        add_box(f"crb_H4_{k}", 121, 179, yy - 0.3, yy + 0.3, z + 8.0, z + 8.6,
                m["yellow"], c)
    add_box("crb_H3_0", 121, 179, 99.7, 100.3, z + 8.0, z + 8.6, m["yellow"], c)


def build_scale_anchor(m):
    """M4: 10 m shuttle bus inside the dock as the readable scale anchor."""
    c = coll("DOCK_EXTRA")
    dock_box("scale_bus", 25, -2.5, 10.0, 3.0, 0.0, 3.0, m["container_blue"], c)
    dock_box("scale_bus_roof", 25, -2.5, 9.6, 2.6, 3.0, 3.15, m["white"], c)
    dock_box("scale_bus_glass", 25, -1.02, 8.6, 0.06, 1.2, 2.2, m["glass"], c)


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
def build_camera_light(samples):
    # --- master ortho camera (map texture)
    cam_data = bpy.data.cameras.new("Camera")
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (120.0, -44.0, 300.0)
    cam.rotation_euler = (0.0, 0.0, 0.0)
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
    sun.rotation_euler = (math.radians(45), 0, math.radians(-22))
    sun_data.energy = 4.6
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
    bg.inputs["Strength"].default_value = 0.82
    # cool gradient sky: deep cool horizon -> pale sage zenith (M3)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*hex_rgba("#8FA6AE")[:3], 1.0)
    ramp.color_ramp.elements[1].position = 0.8
    ramp.color_ramp.elements[1].color = (*hex_rgba("#D8DDD4")[:3], 1.0)
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
    build_west_gate(m)
    build_north_band(m)
    build_industrial(m)
    build_launch(m)
    build_island_green(m)
    build_peninsula(m)
    build_rooms(m)
    build_h1(m)
    build_h2(m)
    build_h3(m)
    build_h4(m)
    build_ceo(m)
    build_wall_layers(m)
    build_floor_marks(m)
    build_floor_joints(m)
    build_room_extras(m)
    build_outdoor_props(m)
    build_equipment(m)
    build_cards(m)
    build_shore(m)
    build_ridges(m)
    build_hero_fog()
    build_extra_props(m)
    build_roof_structure(m)
    build_scale_anchor(m)
    n_fur = build_furniture(m)
    apply_material_upgrade(m)
    apply_illustration_shader(m)
    apply_bevels()
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
    print("BUILD_OK v07", a.out, a.render)


if __name__ == "__main__":
    main()
