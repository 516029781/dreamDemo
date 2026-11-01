# -*- coding: utf-8 -*-
"""R4：缩短水面网格到 y18.5，把画面顶部让给对岸景片。

参考构图中水面只占窄带，顶部是对岸/远山。v22 水面铺到 y22.5，
投影占 v11–22%，且远端在阴影里发黑，形成横贯黑带。
"""
import bpy
import bmesh
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene
log = {"water": {}, "warnings": []}

Y_NEW_FAR = 18.5
for ob in sc.objects:
    if not ob.name.startswith("M01W"):
        continue
    before = [[round(min(v[i] for v in ob.bound_box), 2),
               round(max(v[i] for v in ob.bound_box), 2)] for i in range(3)]
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    moved = 0
    for v in bm.verts:
        world_y = (ob.matrix_world @ v.co).y
        if world_y > Y_NEW_FAR:
            # 转到本地坐标后回写
            local = ob.matrix_world.inverted() @ __import__("mathutils").Vector(
                ((ob.matrix_world @ v.co).x, Y_NEW_FAR, (ob.matrix_world @ v.co).z))
            v.co = local
            moved += 1
    bm.to_mesh(me)
    bm.free()
    me.update()
    after = [[round(min(v[i] for v in ob.bound_box), 2),
              round(max(v[i] for v in ob.bound_box), 2)] for i in range(3)]
    log["water"] = {"name": ob.name, "before": before, "after": after, "verts_moved": moved}
    print("WATER", ob.name, "moved", moved, "bbox", after)

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
with open(os.path.join(PRE, "R4_WATER_CROP.json"), "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=1)
