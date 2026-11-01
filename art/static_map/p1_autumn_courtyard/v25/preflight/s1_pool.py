# -*- coding: utf-8 -*-
"""S1 · 背景水池

目标（P1_GOAL_CONFIRM §3.8 B4/B5/B6/B7）：
  - 删掉全宽假水面 M01W
  - 在 v16.5-24.1 处开一个下沉水池：池缘 y≈13.9、近缘 y≈10.0、池底 z≈-0.45
  - 石压顶（比水面亮）+ 弧形高台
  - （风机已存在，本脚本只做缩放校正）

用法: blender -b scene.blend -P preflight/s1_pool.py
输出: preflight/S1_POOL.json
"""
import json
import math
import os
import random

import bpy
import bmesh
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene
random.seed(20261101)

LOG = {"removed": [], "created": [], "warnings": [], "materials": {}}

# ---------------- 1. 删掉假的水平面 + 占位物 ----------------
KILL_PREFIX = ("M01W", "V18 B02", "V18 B03")
for ob in list(bpy.data.objects):
    if any(ob.name.startswith(k) for k in KILL_PREFIX):
        LOG["removed"].append(ob.name)
        bpy.data.objects.remove(ob, do_unlink=True)

# 旧 watercourse 收起（保留数据块做参考，不参与渲染）
for ob in bpy.data.objects:
    if ob.name.startswith("Curved blue green watercourse"):
        ob.hide_render = True
        LOG["removed"].append(ob.name + " (hide)")

# 池区里的草簇，避免穿出水面
for ob in list(bpy.data.objects):
    if ob.name.startswith("V18 B10 | right-bank grass"):
        ob.hide_render = True
        LOG["removed"].append(ob.name + " (hide)")


# ---------------- 2. 几何参数 ----------------
CX, CY = -1.14, 12.00          # 池心（世界 x, y）
RX, RY = 2.20, 1.95            # 半轴
RIM_W = 0.42                   # 压顶宽度
Z_TOP = 0.22                   # 压顶顶面
Z_GROUND = 0.04                # 广场地面
Z_WATER = -0.26                # 水面
Z_FLOOR = -0.70                # 池底
SEG = 64


def ellipse_r(theta, grow=0.0, jitter=0.0, phase=0.0):
    c, s = math.cos(theta), math.sin(theta)
    r = 1.0 / math.sqrt((c / (RX + grow)) ** 2 + (s / (RY + grow)) ** 2)
    if jitter:
        r *= 1.0 + jitter * (math.sin(3 * theta + phase) * 0.6 + math.sin(5 * theta + phase * 1.7) * 0.4)
    return r


def ring_pts(grow, jitter=0.0, phase=0.0, z=0.0):
    pts = []
    for i in range(SEG):
        t = 2 * math.pi * i / SEG
        r = ellipse_r(t, grow, jitter, phase)
        pts.append(Vector((CX + r * math.cos(t), CY + r * math.sin(t), z)))
    return pts


def new_mesh_obj(name, verts, faces, mat=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    if mat:
        ob.data.materials.append(mat)
    return ob


def get_mat(*names):
    for n in names:
        m = bpy.data.materials.get(n)
        if m:
            return m
    return None


# ---------------- 3. 在广场地面开洞 ----------------
cut_ok = False
ground = bpy.data.objects.get("Rear service terrace ground")
if ground:
    cutter_verts = []
    cutter_faces = []
    # 上环 + 下环
    top = ring_pts(0.0, 0.0, 0.0, Z_TOP + 0.10)
    bot = ring_pts(0.0, 0.0, 0.0, -1.60)
    cutter_verts = [tuple(v) for v in top] + [tuple(v) for v in bot]
    for i in range(SEG):
        j = (i + 1) % SEG
        cutter_faces.append((i, j, SEG + j, SEG + i))
    cutter_faces.append(tuple(range(SEG)))
    cutter_faces.append(tuple(range(SEG, 2 * SEG)))
    cutter = new_mesh_obj("__pool_cutter", cutter_verts, cutter_faces)

    mod = ground.modifiers.new("pool_cut", 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = cutter
    mod.solver = 'EXACT'
    bpy.context.view_layer.objects.active = ground
    try:
        bpy.ops.object.modifier_apply(modifier=mod.name)
        cut_ok = True
        LOG["created"].append("boolean cut on Rear service terrace ground")
    except Exception as e:
        LOG["warnings"].append(f"boolean failed: {e}")
    bpy.data.objects.remove(cutter, do_unlink=True)
else:
    LOG["warnings"].append("Rear service terrace ground not found")

# ---------------- 4. 池壁 + 池底 ----------------
inner_out = ring_pts(0.0, 0.0, 0.0, Z_GROUND)
inner_bot = ring_pts(0.0, 0.0, 0.0, Z_FLOOR)
verts = [tuple(v) for v in inner_out] + [tuple(v) for v in inner_bot]
faces = [(i, (i + 1) % SEG, SEG + (i + 1) % SEG, SEG + i) for i in range(SEG)]
wall = new_mesh_obj("P1 pool | inner wall", verts, faces)

# 池底（扇形）
floor_v = [tuple(v) for v in ring_pts(0.0, 0.0, 0.0, Z_FLOOR)] + [(CX, CY, Z_FLOOR)]
ff = [(i, (i + 1) % SEG, SEG) for i in range(SEG)]
floor = new_mesh_obj("P1 pool | basin floor", floor_v, ff)

stone_dark = get_mat("T01 | retaining stone", "Pale cast planter stone", "P1 dry stone")
for o in (wall, floor):
    if stone_dark:
        o.data.materials.append(stone_dark)

# ---------------- 5. 水面 ----------------
water_mat = bpy.data.materials.get("P1 pool water")
if not water_mat:
    water_mat = bpy.data.materials.new("P1 pool water")
    water_mat.use_nodes = True
    b = next(n for n in water_mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')


def s2l(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


bsdf = next(n for n in water_mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
bsdf.inputs['Base Color'].default_value = (s2l(127), s2l(145), s2l(154), 1.0)
for k, v in [('Roughness', 0.32), ('Metallic', 0.0), ('IOR', 1.33)]:
    if k in bsdf.inputs:
        bsdf.inputs[k].default_value = v
if 'Specular IOR Level' in bsdf.inputs:
    bsdf.inputs['Specular IOR Level'].default_value = 0.28
LOG["materials"]["P1 pool water"] = [127, 145, 154]

water = new_mesh_obj("P1 pool | water surface",
                     [tuple(v) for v in ring_pts(-0.04, 0.0, 0.0, Z_WATER)] + [(CX, CY, Z_WATER)],
                     [(i, (i + 1) % SEG, SEG) for i in range(SEG)], water_mat)

# ---------------- 6. 石压顶（环） ----------------
o_in = ring_pts(0.02, 0.012, 0.4, Z_TOP)     # 顶内
o_mid = ring_pts(RIM_W, 0.012, 0.4, Z_TOP)   # 顶外
o_out_d = ring_pts(RIM_W, 0.012, 0.4, Z_GROUND - 0.05)  # 外侧下沿
o_in_d = ring_pts(0.02, 0.012, 0.4, Z_TOP - 0.06)       # 内沿下（倒角）

# 顶面 + 外侧面 + 内倒角
verts = ([tuple(v) for v in o_in] + [tuple(v) for v in o_mid] +
         [tuple(v) for v in o_out_d] + [tuple(v) for v in o_in_d])
N = SEG
faces = []
for i in range(N):
    j = (i + 1) % N
    faces.append((i, j, N + j, N + i))                 # 顶面
    faces.append((N + i, N + j, 2 * N + j, 2 * N + i))  # 外侧面
    faces.append((3 * N + i, 3 * N + j, j, i))          # 内倒角
rim = new_mesh_obj("P1 pool | stone rim", verts, faces)

stone_light = get_mat("Cut limestone", "P1 limestone paving", "T01 | retaining stone")
if stone_light:
    rim.data.materials.append(stone_light)

# ---------------- 7. 风机缩放校正（F7: v1.7-12.8, u0.543-0.599） ----------------
vent = [o for o in bpy.data.objects if o.name.startswith(("Ventilator", "Distant ventilator"))]
if vent:
    zs = []
    for o in vent:
        zs += [(o.matrix_world @ Vector(c)).z for c in o.bound_box]
    pivot = Vector((1.60, 10.45, min(zs)))
    k = 0.62
    for o in vent:
        o.location = pivot + (o.location - pivot) * k
        o.scale = [s * k for s in o.scale]
    LOG["created"].append(f"ventilator scaled x{k}")

# ---------------- 8. 保存 ----------------
bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))

LOG["params"] = {"center": [CX, CY], "rx": RX, "ry": RY, "rim_w": RIM_W,
                 "z_water": Z_WATER, "z_floor": Z_FLOOR, "z_top": Z_TOP,
                 "bool_cut": cut_ok}
json.dump(LOG, open(os.path.join(PRE, "S1_POOL.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("S1_DONE cut=%s removed=%d" % (cut_ok, len(LOG["removed"])))
