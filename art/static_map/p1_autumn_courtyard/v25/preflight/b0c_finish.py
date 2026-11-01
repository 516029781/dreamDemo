"""B0c · 收尾三处精度问题

1. 景片过覆盖：M02/M03 按视锥精确做满，v=0 正好在边界上，
   射线会漏（数值假象），但景深模糊会真的把边界外拉进画面 -> 各放大 8%。
2. 岸线太厚（占 4pp）：进深 0.5 -> 0.25，顶面 0.35 -> 0.22。
3. 记录最终锁定值到 B0_LOCK.json（合并而非覆盖）。
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


# ---------- 1. 景片过覆盖 ----------
for name in ("M02 | far bank plate", "M03 | distant air plate"):
    ob = bpy.data.objects.get(name)
    if not ob:
        log["steps"].append({"op": "missing", "obj": name})
        continue
    before = bbox(ob)
    ob.scale.x *= 1.08
    ob.scale.y *= 1.08
    bpy.context.view_layer.update()
    log["steps"].append({"op": "overfill", "obj": name, "factor": 1.08,
                         "before": before, "after": bbox(ob)})

# ---------- 2. 岸线做薄 ----------
EDGE = "P1 far shore edge"
old = bpy.data.objects.get(EDGE)
if old:
    before = bbox(old)
    y0 = before["y"][0]
    x0, x1 = -20.0, 20.0
    y1 = y0 + 0.25
    ztop, zbot = 0.22, -0.30
    bpy.data.objects.remove(old, do_unlink=True)
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
    ob.parent = None
    ob.matrix_world.identity()
    mat = bpy.data.materials.get("P1 far shore edge mat")
    if mat:
        ob.data.materials.append(mat)
    ob.visible_shadow = False
    log["steps"].append({"op": "thin_shore_edge", "before": before,
                         "y": [round(y0, 2), round(y1, 2)], "z_top": ztop,
                         "after": bbox(ob)})

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))

with open(os.path.join(PRE, "B0C_FIX.json"), "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=1)

print("=== B0c ===")
for s in log["steps"]:
    print(" ", json.dumps(s, ensure_ascii=False))
