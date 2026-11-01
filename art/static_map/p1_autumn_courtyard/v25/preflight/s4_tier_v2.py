"""S1（v2 参数）：两层地块骨架。

方案：planning/art/P1_TWO_TIER_TERRAIN_PLAN_20261101.md §四

与 v1 的差别（v1 建出来看不到墙，已作废）：
  - 没有 1.5 m 挡墙，改成 0.4 m 压沿（顶 z+0.10，底 z-0.30）
  - 低地块 z -1.44 → -0.30
  - 低地块反照率 0.34（湿沙），不是 0.78（亮沙）
  - 新增远岸坡 y19.5→22 升到 z+0.80，负责封住 v0-10
  - 水池后移 3.2 m、下沉 0.42 m、y 方向压到 0.58
  - 设备群不动（原 y1.0-2.5 正好落在 v45-48，属于"谷"的目标区间）
"""
import math

import bpy
from mathutils import Matrix, Vector

CUT_Y = 8.0          # 平台边缘
LOW_Z = -0.30        # 低地块地面
CURB_TOP = 0.10      # 压沿顶
BANK_Y0, BANK_Y1 = 19.5, 22.0
BANK_Z0, BANK_Z1 = LOW_Z, 0.80
X0, X1 = -22.0, 22.0

sc = bpy.context.scene


def mk_mat(name, rgb, rough, spec=0.35):
    m = bpy.data.materials.get(name)
    if m:
        bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, 1.0)
    b.inputs["Roughness"].default_value = rough
    try:
        b.inputs["Specular IOR Level"].default_value = spec
    except Exception:
        pass
    return m


def mesh(name, verts, faces, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def box(name, x0, x1, y0, y1, z0, z1, mat):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return mesh(name, v, f, mat)


# ---------------- 0. 清掉上一版试建的 tier 对象 ----------------
for o in list(bpy.data.objects):
    if o.name.startswith("P1 tier |"):
        bpy.data.objects.remove(o, do_unlink=True)

# ---------------- 1. 旧台地：留材质，隐藏本体 ----------------
terrace = bpy.data.objects.get("Rear service terrace ground")
tmat = None
if terrace:
    if terrace.data.materials:
        tmat = terrace.data.materials[0]
    terrace.hide_render = True
    print("OLD_TERRACE_HIDDEN")

stone = tmat if tmat else mk_mat("P1 tier | stone", (166, 158, 144), 0.86)
curb_m = mk_mat("P1 tier | curb", (176, 168, 154), 0.82)
low_m = mk_mat("P1 tier | low ground", (128, 116, 96), 0.96)      # 反照率 ~0.30
bank_m = mk_mat("P1 tier | far bank", (104, 95, 80), 0.95)

# ---------------- 2. 高平台（y2.6-8.0） ----------------
box("P1 tier | upper terrace", X0, X1, 2.60, CUT_Y, -0.60, 0.06, stone)

# ---------------- 3. 压沿（0.4 m，只露顶边） ----------------
box("P1 tier | curb", X0, X1, 7.82, 8.18, LOW_Z, CURB_TOP, curb_m)
box("P1 tier | curb cap", X0, X1, 7.76, 8.22, CURB_TOP, CURB_TOP + 0.04, curb_m)

# ---------------- 4. 低地块 ----------------
# 低地块必须给水池留洞，否则整块平板会把水面盖住（实测 cold=0）
GX0, GX1, GY0, GY1 = -3.60, 1.40, 13.80, 16.50
box("P1 tier | low ground S", X0, X1, CUT_Y, GY0, -0.60, LOW_Z, low_m)
box("P1 tier | low ground N", X0, X1, GY1, BANK_Y0 + 0.4, -0.60, LOW_Z, low_m)
box("P1 tier | low ground W", X0, GX0, GY0, GY1, -0.60, LOW_Z, low_m)
box("P1 tier | low ground E", GX1, X1, GY0, GY1, -0.60, LOW_Z, low_m)

# ---------------- 5. 远岸坡（封 v0-10） ----------------
mesh("P1 tier | far bank",
     [(X0, BANK_Y0, -0.60), (X1, BANK_Y0, -0.60), (X1, BANK_Y1, -0.60), (X0, BANK_Y1, -0.60),
      (X0, BANK_Y0, BANK_Z0), (X1, BANK_Y0, BANK_Z0), (X1, BANK_Y1, BANK_Z1), (X0, BANK_Y1, BANK_Z1)],
     [(4, 5, 6, 7), (0, 1, 5, 4), (3, 7, 6, 2), (0, 4, 7, 3), (1, 2, 6, 5)],
     bank_m)

# ---------------- 6. 水池：后移 3.2 m、下沉 0.42 m、y 压 0.58 ----------------
PIVOT_Y = 12.0
SY = 0.58
DZ = -0.42
DY = 3.2
M = (Matrix.Translation(Vector((0.0, PIVOT_Y + DY, DZ)))
     @ Matrix.Diagonal(Vector((1.0, SY, 1.0, 1.0)))
     @ Matrix.Translation(Vector((0.0, -PIVOT_Y, 0.0))))
pool = [o for o in bpy.data.objects if o.name.startswith("P1 pool |")]
for o in pool:
    o.matrix_world = M @ o.matrix_world
print("POOL_MOVED", len(pool))

# ---------------- 7. 隐藏旧远区（保留景片与水池） ----------------
KEEP = ("P1 tier", "P1 pool", "M01", "M02", "M03")
for o in list(bpy.data.objects):
    if o.name.startswith("P1 bank |"):
        o.hide_render = True
hidden = []
for o in bpy.data.objects:
    if o.type != 'MESH' or o.hide_render:
        continue
    if o.name.startswith(KEEP):
        continue
    ys = [(o.matrix_world @ Vector(c)).y for c in o.bound_box]
    if min(ys) > CUT_Y + 0.5:
        o.hide_render = True
        hidden.append(o.name)
print("HIDDEN_FAR", len(hidden))

bpy.context.view_layer.update()
print("COUNTS", len([o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render]))
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()
print("S4_TIER_V2_DONE")
