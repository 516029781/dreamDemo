# -*- coding: utf-8 -*-
"""S3 · 造谷：在 y1.0–2.5 立一排连续实体（§3.7.8）。

目标：v44–50 带均值从 126.6 压到 ≤95；实体本体覆盖 v34–50，不侵入背景窗口 v10–27。
做法：4 段不同高度的矮墙 + 压顶，材质用现有石材；段间留缝，避免一整块"挡板"感。
"""
import json
import os

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene

SEGMENTS = [
    # x0, x1, y0, y1, 高度, 顶面类型
    (-9.6, -6.2, 1.10, 2.30, 1.45, "cope"),
    (-6.0, -2.6, 1.05, 2.35, 1.60, "cope"),
    (-2.4, 1.0, 1.10, 2.30, 1.50, "cope"),
    (1.2, 4.6, 1.05, 2.35, 1.68, "cope"),
    (4.8, 8.2, 1.10, 2.30, 1.52, "cope"),
    (8.4, 11.6, 1.05, 2.35, 1.42, "cope"),
]


def box(name, x0, x1, y0, y1, z0, z1, mat):
    verts = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    if mat:
        ob.data.materials.append(mat)
    return ob


wall_mat = bpy.data.materials.get("T01 | retaining stone")
cope_mat = bpy.data.materials.get("Cut limestone") or wall_mat

made = []
for i, (x0, x1, y0, y1, h, _t) in enumerate(SEGMENTS):
    ob = box(f"P1 terrace edge {i}", x0, x1, y0, y1, -0.05, h, wall_mat)
    made.append(ob.name)
    # 压顶
    c = box(f"P1 terrace edge {i} | coping", x0 - 0.04, x1 + 0.04, y0 - 0.06, y1 + 0.06, h, h + 0.09, cope_mat)
    made.append(c.name)

bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
json.dump({"segments": SEGMENTS, "created": made},
          open(os.path.join(PRE, "S3_EDGE.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("S3_DONE", len(made))
