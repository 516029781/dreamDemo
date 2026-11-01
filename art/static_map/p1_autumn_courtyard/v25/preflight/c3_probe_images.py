# -*- coding: utf-8 -*-
"""查出所有引用 M0x_*.png 的对象与材质，确认景片实际用的是哪张图。只读。"""
import bpy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene

img_users = {}
for img in bpy.data.images:
    if not img.filepath:
        continue
    users = []
    for m in bpy.data.materials:
        if not m.node_tree:
            continue
        for n in m.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image == img:
                users.append(m.name)
    img_users[os.path.basename(img.filepath)] = {
        "filepath": img.filepath,
        "size": list(img.size),
        "materials": sorted(set(users)),
    }

obj_map = []
for ob in sc.objects:
    if ob.type not in {"MESH", "CURVE"}:
        continue
    mats = []
    if hasattr(ob.data, "materials"):
        mats = [m.name for m in ob.data.materials if m]
    if any("M0" in m for m in mats) or ob.name.startswith(("M0", "V18 B", "V20")):
        obj_map.append({
            "name": ob.name,
            "hide_render": ob.hide_render,
            "materials": mats,
        })

out = {"images": img_users, "objects": obj_map}
with open(os.path.join(PRE, "C3_IMAGE_USERS.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("=== IMAGES ===")
for k, v in img_users.items():
    print(f'{k:22s} {v["size"]}  mats={v["materials"]}')
print("=== OBJECTS with M0 mats ===")
for o in obj_map:
    print(f'{"HIDE " if o["hide_render"] else "     "}{o["name"][:46]:48s} {o["materials"]}')
