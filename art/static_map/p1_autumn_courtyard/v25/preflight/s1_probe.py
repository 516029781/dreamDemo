# -*- coding: utf-8 -*-
"""S1 探针：列出水池落位区的铺装与地面对象，确认可开洞的构造。"""
import json
import os

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene

# 水池外框（含压顶余量）
CX, CY = -1.14, 12.0
RX, RY = 2.7, 2.5


def bbox(ob):
    cs = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return (min(c.x for c in cs), max(c.x for c in cs),
            min(c.y for c in cs), max(c.y for c in cs),
            min(c.z for c in cs), max(c.z for c in cs))


hits = []
allobj = []
for ob in sc.objects:
    if ob.type != 'MESH':
        continue
    b = bbox(ob)
    allobj.append({"name": ob.name, "bbox": [round(v, 2) for v in b],
                   "hide": int(ob.hide_render), "verts": len(ob.data.vertices)})
    # 包围盒与水池外框相交
    if b[1] < CX - RX or b[0] > CX + RX or b[3] < CY - RY or b[2] > CY + RY:
        continue
    hits.append({"name": ob.name, "bbox": [round(v, 2) for v in b],
                 "hide": int(ob.hide_render), "verts": len(ob.data.vertices),
                 "mats": [m.name for m in ob.data.materials if m][:3]})

# 地面类对象（覆盖水池区域的大件）
ground = []
for ob in sc.objects:
    if ob.type != 'MESH':
        continue
    b = bbox(ob)
    w = b[1] - b[0]
    h = b[3] - b[2]
    if w > 6 and h > 6 and b[4] < 1.0:
        ground.append({"name": ob.name, "bbox": [round(v, 2) for v in b],
                       "hide": int(ob.hide_render), "verts": len(ob.data.vertices)})

out = {"pool_frame": {"cx": CX, "cy": CY, "rx": RX, "ry": RY},
       "intersecting": sorted(hits, key=lambda x: x["name"]),
       "ground_like": sorted(ground, key=lambda x: -(x["bbox"][1] - x["bbox"][0])),
       "total_mesh": len(allobj)}
json.dump(out, open(os.path.join(PRE, "S1_PROBE.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("=== 水池区相交对象 %d ===" % len(hits))
for h in hits[:20]:
    b = h["bbox"]
    print(f"  {h['name'][:44]:46s} x[{b[0]:6.2f},{b[1]:6.2f}] y[{b[2]:6.2f},{b[3]:6.2f}] z[{b[4]:5.2f},{b[5]:5.2f}] v={h['verts']}")
print("=== 大地面件 %d ===" % len(ground))
for g in ground[:6]:
    b = g["bbox"]
    print(f"  {g['name'][:44]:46s} x[{b[0]:7.2f},{b[1]:7.2f}] y[{b[2]:6.2f},{b[3]:6.2f}] z[{b[4]:5.2f},{b[5]:5.2f}]")
