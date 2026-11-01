"""打散远岸灌木带：现在 54 个灌木排成同一 y，读起来像一排石头。

做法：y 方向随机 ±2.2、x ±0.8、缩放 0.7-1.35，落地用射线找地面高度。
"""
import bpy
import random
from mathutils import Vector

random.seed(20261101)
sc = bpy.context.scene
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()

objs = [o for o in bpy.data.objects if o.name.startswith("P1 bank | shrub")]
print("SHRUBS", len(objs))
moved = 0
for o in objs:
    m = o.matrix_world.copy()
    c = m.translation.copy()
    dy = random.uniform(-2.4, 2.4)
    dx = random.uniform(-0.9, 0.9)
    s = random.uniform(0.70, 1.38)
    nx, ny = c.x + dx, c.y + dy
    hit, loc, nor, j, ob, mtx = sc.ray_cast(dg, Vector((nx, ny, 6.0)), Vector((0, 0, -1)))
    z = loc.z if hit else 0.0
    # 缩放（绕自身中心，保持底部贴地）
    for i in range(3):
        m[i][0] *= s
        m[i][1] *= s
        m[i][2] *= s
    m.translation = (nx, ny, z - 0.04)
    o.matrix_world = m
    moved += 1

# 左侧大树左移，让树冠压住左上角、影子移出广场中心
tn = 0
for o in bpy.data.objects:
    if "broadleaf" in o.name.lower() or o.name.startswith("Tree ") or "Tree primary" in o.name:
        m = o.matrix_world.copy()
        m.translation.x -= 3.2
        m.translation.y += 1.0
        o.matrix_world = m
        tn += 1
print("TREES_MOVED", tn)

bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()
print("S3D_DONE", moved)
