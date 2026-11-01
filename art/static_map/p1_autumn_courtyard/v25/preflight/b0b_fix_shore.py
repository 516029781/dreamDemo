"""B0b · 修正 B0 遗留的三处几何缺陷（不重做，只定点修）

缺陷（均由包围盒实测确认，非推测）：
  1. `P1 far shore edge` 顶点是世界坐标，却又 parent 到相机 -> 被二次变换，
     实际落在 z 26.3 / y -13.5（相机上方偏后），E3 永远打不中。
  2. `T01 | far retaining coping` / `far retaining wall` 是 z=0.30 的**扁平片**，
     横跨 x ±22，悬在水面（z -0.18）上方 0.48 m，把水面切成上下两段。
  3. `T01 | east shore cap` z 顶 0.13，比压顶低，形成第二道台阶。

做法：
  1 重建岸线（世界坐标、无父级）；
  2 压顶降到 z=0.02（水面 +0.20），从"横切水面的悬浮板"变成"水近端的薄压边"；
  3 东岸 cap 同步降到 0.02，与压顶同一高度，避免第二道台阶。
"""
import bpy
import json
import os
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene
log = {"steps": []}


def bbox(ob):
    cs = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return {
        "x": [round(min(c.x for c in cs), 2), round(max(c.x for c in cs), 2)],
        "y": [round(min(c.y for c in cs), 2), round(max(c.y for c in cs), 2)],
        "z": [round(min(c.z for c in cs), 2), round(max(c.z for c in cs), 2)],
    }


# ---------- 1. 重建岸线：世界坐标，不 parent ----------
EDGE = "P1 far shore edge"
water = bpy.data.objects.get("M01W | horizontal water plane")
y_far = max(v.co.y for v in water.data.vertices) if water else 19.5

old = bpy.data.objects.get(EDGE)
if old:
    log["steps"].append({"op": "remove", "obj": EDGE, "before": bbox(old)})
    bpy.data.objects.remove(old, do_unlink=True)

y0, y1 = y_far, y_far + 0.5
x0, x1 = -20.0, 20.0
ztop, zbot = 0.35, -0.30
verts = [
    (x0, y0, zbot), (x1, y0, zbot), (x1, y0, ztop), (x0, y0, ztop),
    (x0, y1, ztop), (x1, y1, ztop),
]
faces = [(0, 1, 2, 3), (3, 2, 5, 4), (0, 3, 4), (1, 5, 2)]
me = bpy.data.meshes.new(EDGE)
me.from_pydata(verts, [], faces)
me.update()
ob = bpy.data.objects.new(EDGE, me)
sc.collection.objects.link(ob)
# 关键：顶点的世界坐标 == 对象世界坐标，不能再 parent 到相机
ob.parent = None
ob.matrix_world.identity()

mat = bpy.data.materials.get("P1 far shore edge mat")
if not mat:
    mat = bpy.data.materials.new("P1 far shore edge mat")
    mat.use_nodes = True
    b = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if b:
        b.inputs["Base Color"].default_value = (0.30, 0.26, 0.20, 1)
        if "Roughness" in b.inputs:
            b.inputs["Roughness"].default_value = 0.92
ob.data.materials.append(mat)
ob.visible_shadow = False
log["steps"].append({"op": "rebuild_shore_edge", "obj": EDGE,
                     "y": [round(y0, 2), round(y1, 2)], "z_top": ztop,
                     "after": bbox(ob)})

# ---------- 2. 压顶 / 东岸 cap 降到水面上 0.20 ----------
for name, znew in [
    ("T01 | far retaining coping", 0.02),
    ("T01 | far retaining wall", 0.02),
    ("T01 | east shore cap", 0.02),
]:
    target = bpy.data.objects.get(name)
    if not target:
        log["steps"].append({"op": "missing", "obj": name})
        continue
    before = bbox(target)
    dz = znew - before["z"][1]
    target.location.z += dz
    bpy.context.view_layer.update()
    log["steps"].append({"op": "lower", "obj": name, "dz": round(dz, 3),
                         "before": before, "after": bbox(target)})

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))

with open(os.path.join(PRE, "B0B_FIX.json"), "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=1)

print("=== B0b ===")
for s in log["steps"]:
    print(" ", json.dumps(s, ensure_ascii=False))
