# -*- coding: utf-8 -*-
"""列出遮挡水池窗口 v0.10-0.27 / u0.28-0.60 的非远景对象。"""
import json
import os

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene
cam = sc.camera
fr = cam.data.view_frame(scene=sc)
tr, br, bl, tl = fr
dg = bpy.context.evaluated_depsgraph_get()


def direction(u, v):
    top = tl.lerp(tr, u)
    bot = bl.lerp(br, u)
    p = top.lerp(bot, v)
    return (cam.matrix_world.to_quaternion() @ p).normalized()


origin = cam.matrix_world.translation
blockers = {}
for iu in range(28, 61, 4):
    for iv in range(10, 28, 2):
        u, v = iu / 100.0, iv / 100.0
        hit, loc, nor, idx, ob, mx = sc.ray_cast(dg, origin, direction(u, v))
        if not hit:
            continue
        d = (loc - origin).length
        if ob.name.startswith("P1 pool") or d > 40:
            continue
        key = ob.name
        rec = blockers.setdefault(key, {"name": key, "dist": round(d, 1),
                                        "v": [1, 0], "u": [1, 0], "n": 0})
        rec["n"] += 1
        rec["v"][0] = min(rec["v"][0], v)
        rec["v"][1] = max(rec["v"][1], v)
        rec["u"][0] = min(rec["u"][0], u)
        rec["u"][1] = max(rec["u"][1], u)

rows = sorted(blockers.values(), key=lambda r: -r["n"])
json.dump(rows, open(os.path.join(PRE, "S1B_BLOCKERS.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("=== 遮挡池面的对象 %d 个 ===" % len(rows))
for r in rows:
    print(f"  {r['name'][:44]:46s} n={r['n']:3d} d={r['dist']:6.1f} "
          f"v[{r['v'][0]*100:5.1f},{r['v'][1]*100:5.1f}] u[{r['u'][0]:.2f},{r['u'][1]:.2f}]")
