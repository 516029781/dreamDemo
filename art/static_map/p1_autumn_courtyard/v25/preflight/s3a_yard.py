# -*- coding: utf-8 -*-
"""S3a · 中景服务院（造谷的载体，§3.7.8 ③）

上一版失败原因：6 段等高平面盒体 = 一排挡板。
本版改用**真实设备组合**：集装箱 / 罐体 / 格栅屏 / 管排 / 料箱 / 杂项，
按 y 1.0–2.5 错落摆放，高度 1.25–1.95（顶边落 v30–38，底边接 v50），
横向 x −8.3…4.6 连续覆盖 u 0.00–0.80，靠"轮廓高低 + 进深差 + 明暗节奏"成暗带。

用法: blender -b scene.blend -P preflight/s3a_yard.py
"""
import json
import math
import os
import random

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene
K = json.load(open(os.path.join(PRE, "KNOBS.json"), encoding="utf-8"))
GAIN = float(K.get("yard_gain", 1.0))
HS = float(K.get("yard_h", 1.0))
random.seed(771)

# ---------------- 0. 清掉上一版 ----------------
for ob in list(bpy.data.objects):
    if ob.name.startswith("P1 yard"):
        bpy.data.objects.remove(ob, do_unlink=True)
for m in list(bpy.data.materials):
    if m.name.startswith("P1 yard |"):
        bpy.data.materials.remove(m)


def s2l(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def mk_mat(name, srgb, rough=0.72, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = tuple(s2l(c) * GAIN for c in srgb) + (1.0,)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    return m


MAT = {
    "rust": mk_mat("P1 yard | rust", (118, 76, 50), 0.86),
    "iron": mk_mat("P1 yard | iron", (94, 90, 84), 0.62, 0.40),
    "wood": mk_mat("P1 yard | crate wood", (104, 78, 54), 0.90),
    "steel": mk_mat("P1 yard | steel mid", (126, 122, 114), 0.68, 0.28),
    "tank": mk_mat("P1 yard | tank pale", (152, 148, 138), 0.58, 0.18),
    "stone": mk_mat("P1 yard | planter stone", (142, 134, 122), 0.84),
    "grass": mk_mat("P1 yard | dry grass", (144, 116, 76), 0.94),
}


def mesh_obj(name, verts, faces, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    if mat:
        ob.data.materials.append(mat)
    return ob


def box(name, x0, x1, y0, y1, z0, z1, mat):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
         (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return mesh_obj(name, v, f, mat)


def box_r(name, cx, cy, w, d, z0, z1, ang, mat):
    """绕 z 轴旋转的箱体：避免所有东西都正对镜头（那正是"挡板感"的来源）。"""
    ca, sa = math.cos(ang), math.sin(ang)
    pts = []
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        px, py = sx * w / 2, sy * d / 2
        pts.append((cx + px * ca - py * sa, cy + px * sa + py * ca))
    v = [(p[0], p[1], z0) for p in pts] + [(p[0], p[1], z1) for p in pts]
    f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
         (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return mesh_obj(name, v, f, mat)


def cyl(name, cx, cy, z0, h, r, mat, seg=20, axis='Z'):
    verts, faces = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        ca, sa = math.cos(a), math.sin(a)
        if axis == 'Z':
            verts.append((cx + r * ca, cy + r * sa, z0))
            verts.append((cx + r * ca, cy + r * sa, z0 + h))
        else:
            verts.append((z0, cx + r * ca, cy + r * sa))
            verts.append((z0 + h, cx + r * ca, cy + r * sa))
    for i in range(seg):
        j = (i + 1) % seg
        faces.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
    faces.append(tuple(2 * i for i in range(seg)))
    faces.append(tuple(2 * i + 1 for i in range(seg - 1, -1, -1)))
    return mesh_obj(name, verts, faces, mat)


made = []


def reg(ob):
    made.append(ob.name)
    return ob


# ---------------- 1. 箱类 ----------------
def crate(name, cx, cy, w, d, h, mat, ang=0.0, ribs=2):
    z1 = h * HS
    if ang:
        reg(box_r(name, cx, cy, w, d, -0.02, z1, ang, mat))
    else:
        reg(box(name, cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, -0.02, z1, mat))
    # 两道加强肋：只做深色细条，不做"栅栏"
    for i in range(ribs):
        zz = z1 * (0.30 + 0.42 * i)
        reg(box("%s | band %d" % (name, i), cx - w / 2 - 0.02, cx + w / 2 + 0.02,
                cy - d / 2 - 0.02, cy - d / 2 + 0.03, zz, zz + 0.055, MAT["iron"]))


# 左组（在叉车后方，y 2.2+）
crate("P1 yard | crate L1", -7.55, 2.72, 1.05, 0.80, 1.30, MAT["wood"], 0.16)
crate("P1 yard | crate L2", -6.45, 2.66, 0.80, 0.70, 1.12, MAT["rust"], -0.22)
# 中左组（叉车右侧，y 1.2-2.1）
crate("P1 yard | dumpster", -4.72, 1.55, 1.05, 0.82, 1.22, MAT["iron"], 0.06)
crate("P1 yard | cabinet", -2.92, 1.48, 0.62, 0.70, 1.52, MAT["steel"], -0.10)
# 右组（花池前，y 1.2-2.3）
crate("P1 yard | crate R1", 1.72, 1.66, 1.00, 0.78, 1.14, MAT["wood"], 0.12)
crate("P1 yard | crate R2", 2.92, 1.78, 0.82, 0.72, 1.05, MAT["rust"], -0.18)
crate("P1 yard | crate R3", 4.02, 1.86, 1.00, 0.80, 1.26, MAT["iron"], 0.05)

# ---------------- 2. 罐体 / 桶 ----------------
def tank(name, cx, cy, r, h, mat="tank", bands=True):
    h *= HS
    reg(cyl(name, cx, cy, -0.02, h, r, MAT[mat], 20))
    reg(cyl(name + " | cap", cx, cy, h - 0.04, 0.08, r * 0.74, MAT["iron"], 14))
    if bands:
        for k in (0.42,):
            reg(cyl("%s | band %d" % (name, int(k * 100)), cx, cy,
                    h * k, 0.06, r * 1.05, MAT["iron"], 20))


tank("P1 yard | tank R", 3.45, 1.52, 0.42, 1.34)
tank("P1 yard | drum a", -5.62, 1.42, 0.27, 0.86, "rust", bands=False)
tank("P1 yard | drum b", -5.30, 1.86, 0.27, 0.86, "iron", bands=False)
tank("P1 yard | drum c", -5.66, 1.92, 0.27, 0.86, "wood", bands=False)
tank("P1 yard | drum d", 1.06, 1.24, 0.25, 0.80, "steel", bands=False)

# ---------------- 3. 管盘 / 管排 ----------------
# axis='X' 时 cyl 的参数是 (y_center, z_center, x_start, x_len, r)
reg(cyl("P1 yard | pipe spool", 1.60, 0.47, -4.16, 0.92, 0.46, MAT["steel"], 18, axis='X'))
for i, xx in enumerate((-4.18, -3.83, -3.48)):
    reg(cyl("P1 yard | pipe coil %d" % i, 1.60, 0.47, xx, 0.07, 0.40, MAT["iron"], 16, axis='X'))


def pipe(name, x0, x1, y, z, r=0.085, mat="steel"):
    reg(cyl(name, y, z * HS, x0, x1 - x0, r, MAT[mat], 10, axis='X'))


pipe("P1 yard | pipe run A", -8.00, -0.20, 2.86, 1.18, 0.075)
pipe("P1 yard | pipe run B", -8.00, -0.20, 2.86, 0.98, 0.055, "iron")
pipe("P1 yard | pipe run C", 1.10, 4.40, 2.62, 1.08, 0.070, "iron")

# ---------------- 4. 前缘种植槽（压住 v47-50，接住广场线） ----------------
def grass_bed(name, x0, x1, y0, y1, z_top, amp=0.10):
    """连续的干草带：用带噪声起伏的网格代替一排"花盆"，
    既是暗带的一部分，也让广场边缘读作种植带而不是长凳。"""
    nx, ny = 12, 4
    verts, faces = [], []
    for iy in range(ny + 1):
        for ix in range(nx + 1):
            fx, fy = ix / nx, iy / ny
            edge = min(fx, 1 - fx, fy, 1 - fy) * 2.0
            h = z_top - 0.04 + amp * (0.45 + 0.55 * edge) * (
                0.60 + 0.40 * math.sin(fx * 9.0 + fy * 5.0)
                + 0.22 * math.sin(fx * 19.0 + 2.1))
            verts.append((x0 + (x1 - x0) * fx, y0 + (y1 - y0) * fy,
                          h + random.uniform(-0.035, 0.035)))
    for iy in range(ny):
        for ix in range(nx):
            a = iy * (nx + 1) + ix
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    return mesh_obj(name, verts, faces, MAT["grass"])


def kerb(name, x0, x1, y0, y1, h):
    # 种植槽高度不跟 yard_h 联动：它负责压住 v47-50，位置必须稳定
    h = h * 1.0
    reg(box(name, x0, x1, y0, y1, -0.02, h, MAT["rust"]))
    reg(box(name + " | soil", x0 + 0.10, x1 - 0.10, y0 + 0.08, y1 - 0.08,
            h - 0.16, h - 0.04, MAT["wood"]))
    reg(grass_bed(name + " | dry grass bed", x0 + 0.06, x1 - 0.06,
                  y0 + 0.04, y1 - 0.04, h + 0.12, 0.10))


kerb("P1 yard | kerb A", -2.55, -0.45, 0.99, 1.42, 0.84)
kerb("P1 yard | kerb B", -0.35, 1.90, 0.99, 1.42, 0.78)

# ---------------- 5. 杂项 ----------------
reg(box("P1 yard | pallet A", 3.10, 3.72, 1.02, 1.30, 0.0, 0.12, MAT["wood"]))
reg(box("P1 yard | pallet B", 3.14, 3.68, 1.06, 1.34, 0.12, 0.24, MAT["wood"]))
for i in range(5):
    reg(box("P1 yard | ladder rung %d" % i, 4.34, 4.60, 2.42, 2.48,
            0.20 + i * 0.26, 0.24 + i * 0.26, MAT["iron"]))


# 整体前移：把中景暗带在画面上整体下移，让"谷"落在 v42-50 而不是 v38-44。
# 地面在 y0.6-3.4 是一整块平台（实测 z=0.035），前移不会悬空。
DY = float(K.get("yard_dy", -0.30))
if abs(DY) > 1e-6:
    for ob in bpy.data.objects:
        if ob.name.startswith("P1 yard"):
            ob.location.y += DY

bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))

json.dump({"gain": GAIN, "h": HS, "dy": DY, "objects": len(made), "names": made[:80]},
          open(os.path.join(PRE, "S3A_YARD.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("S3A_DONE gain=%.3f h=%.2f objects=%d" % (GAIN, HS, len(made)))
