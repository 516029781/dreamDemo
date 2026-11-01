# -*- coding: utf-8 -*-
"""对画面指定屏幕坐标发射射线，返回首个命中对象与材质，定位黑带来源。"""
import bpy
import json
import os
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene
cam = sc.camera
dg = bpy.context.evaluated_depsgraph_get()

fr = cam.data.view_frame(scene=sc)
# view_frame: 右上, 右下, 左下, 左上；构造屏幕 uv -> 相机空间
tr, br, bl, tl = fr
W, H = 1920, 1078


def cam_point(u, v):
    """u,v ∈ [0,1]，v=0 顶部。"""
    top = tl.lerp(tr, u)
    bot = bl.lerp(br, u)
    return top.lerp(bot, v)


samples = {
    "black_band_v0.065": (0.5, 0.065),
    "above_v0.02": (0.5, 0.02),
    "below_v0.12": (0.5, 0.12),
    "left_black_v0.065": (0.15, 0.065),
    "right_black_v0.065": (0.85, 0.065),
    "water_v0.16": (0.5, 0.16),
}

out = {"hits": {}}
origin = cam.matrix_world.translation
for key, (u, v) in samples.items():
    p = cam_point(u, v)
    direction = (cam.matrix_world.to_quaternion() @ p).normalized()
    hit, loc, nor, idx, ob, mtx = sc.ray_cast(dg, origin, direction)
    if hit:
        mats = []
        if hasattr(ob.data, "materials"):
            mats = [m.name for m in ob.data.materials if m]
        mat_name = None
        if mats and idx is not None:
            try:
                mat_name = ob.material_slots[ob.data.polygons[idx].material_index].material.name
            except Exception:
                mat_name = mats[0]
        out["hits"][key] = {
            "object": ob.name,
            "material": mat_name,
            "material_slot": mats,
            "distance": round((loc - origin).length, 2),
            "loc": [round(x, 2) for x in loc],
        }
    else:
        out["hits"][key] = {"object": None, "note": "no hit (world)"}

with open(os.path.join(PRE, "R3C_RAYHIT.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

for k, d in out["hits"].items():
    print(f'{k:26s} {d.get("object")}  mat={d.get("material")}  d={d.get("distance")}')
