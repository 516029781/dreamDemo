# -*- coding: utf-8 -*-
"""探测 v22 继承场景的相机、地面、台阶、水面、景片的真实包围盒。只读，不改场景。"""
import bpy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene

out = {"camera": {}, "objects": []}

cam = sc.camera
out["camera"] = {
    "name": cam.name,
    "loc": [round(v, 4) for v in cam.location],
    "rot_euler": [round(v, 6) for v in cam.rotation_euler],
    "lens": cam.data.lens,
    "sensor": cam.data.sensor_width,
    "dof": {
        "use": cam.data.dof.use_dof,
        "focus": round(cam.data.dof.focus_distance, 4),
        "fstop": cam.data.dof.aperture_fstop,
    },
    "parent": cam.parent.name if cam.parent else None,
}

for ob in sc.objects:
    if ob.type not in {"MESH", "CURVE"}:
        continue
    if not ob.visible_get():
        continue
    bb = [ob.matrix_world @ __import__("mathutils").Vector(c) for c in ob.bound_box]
    xs = [v.x for v in bb]
    ys = [v.y for v in bb]
    zs = [v.z for v in bb]
    out["objects"].append({
        "name": ob.name,
        "type": ob.type,
        "parent": ob.parent.name if ob.parent else None,
        "x": [round(min(xs), 3), round(max(xs), 3)],
        "y": [round(min(ys), 3), round(max(ys), 3)],
        "z": [round(min(zs), 3), round(max(zs), 3)],
        "hide_render": ob.hide_render,
    })

out["objects"].sort(key=lambda d: d["name"])
with open(os.path.join(PRE, "C3_SCENE_PROBE.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("CAMERA", json.dumps(out["camera"], ensure_ascii=False))
print("OBJECTS", len(out["objects"]))
for o in out["objects"]:
    if o["hide_render"]:
        continue
    print(f'{o["name"][:40]:42s} x[{o["x"][0]:7.2f},{o["x"][1]:7.2f}] '
          f'y[{o["y"][0]:7.2f},{o["y"][1]:7.2f}] z[{o["z"][0]:6.2f},{o["z"][1]:6.2f}]')
