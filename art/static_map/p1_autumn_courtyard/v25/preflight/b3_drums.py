# -*- coding: utf-8 -*-
"""B1 圆筒改比例：32 个分件绕筒轴统一缩放，并做出画校验。

关键：分件各有独立原点，直接改 scale 会各自缩放导致散架。
必须绕筒轴 A 变换位置：p' = A + (p - A) * s，同时把 scale 乘上 s。

用法：
    blender -b scene.blend -P preflight/b1_drums.py -- --sxy 0.65 --sz 1.40
"""
import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene
cam = sc.camera

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--sxy", type=float, default=0.65)
ap.add_argument("--sz", type=float, default=1.40)
ap.add_argument("--z-anchor", type=float, default=0.22)
ap.add_argument("--dry-run", action="store_true")
args = ap.parse_args(argv)

parts = [o for o in sc.objects if o.name.lower().startswith("p1 cropped round tower")]
if not parts:
    parts = [o for o in sc.objects if "round tower" in o.name.lower() and o.type == "MESH"]
if not parts:
    raise SystemExit("no drum parts found")

# 筒轴：所有分件世界包围盒的 xy 中心
xs, ys = [], []
for ob in parts:
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    xs += [v.x for v in bb]
    ys += [v.y for v in bb]
A = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, args.z_anchor))

before = {"x": [round(min(xs), 2), round(max(xs), 2)],
          "y": [round(min(ys), 2), round(max(ys), 2)],
          "diameter": round(max(xs) - min(xs), 2)}

for ob in parts:
    b = ob.matrix_world.translation.copy()
    new_loc = Vector((A.x + (b.x - A.x) * args.sxy,
                      A.y + (b.y - A.y) * args.sxy,
                      A.z + (b.z - A.z) * args.sz))
    ob.location = new_loc
    ob.scale = (ob.scale.x * args.sxy, ob.scale.y * args.sxy, ob.scale.z * args.sz)

bpy.context.view_layer.update()

# 缩放后包围盒与投影
xs2, ys2, zs2 = [], [], []
for ob in parts:
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    xs2 += [v.x for v in bb]
    ys2 += [v.y for v in bb]
    zs2 += [v.z for v in bb]

tv = (18.0 / cam.data.lens) * (1078 / 1920)
th = tv * 1920 / 1078
pitch = 90 - math.degrees(cam.rotation_euler.x)
o = cam.matrix_world.translation


def proj_v(x, y, z):
    dy = y - o.y
    if dy <= 0.01:
        return None
    p = math.degrees(math.atan2(o.z - z, dy))
    return 0.5 - (math.tan(math.radians(pitch)) - math.tan(math.radians(p))) / (2 * tv)


vs = [proj_v(x, y, z) for x, y, z in [(min(xs2), min(ys2), max(zs2)),
                                      (max(xs2), max(ys2), max(zs2)),
                                      (min(xs2), min(ys2), min(zs2))]]
vs = [v for v in vs if v is not None]
v_top = min(vs) if vs else None

after = {"x": [round(min(xs2), 2), round(max(xs2), 2)],
         "y": [round(min(ys2), 2), round(max(ys2), 2)],
         "z": [round(min(zs2), 2), round(max(zs2), 2)],
         "diameter": round(max(xs2) - min(xs2), 2),
         "top_v": None if v_top is None else round(v_top, 4)}

checks = {
    "diameter_in_range": 2.7 <= after["diameter"] <= 3.0,
    "not_out_of_frame": v_top is not None and v_top >= 0.05,
}
rec = {"axis": [round(c, 3) for c in A], "sxy": args.sxy, "sz": args.sz,
       "parts": len(parts), "before": before, "after": after, "checks": checks}

if not args.dry_run:
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))

with open(os.path.join(PRE, "B1_DRUM_SCALE.json"), "w", encoding="utf-8") as f:
    json.dump(rec, f, ensure_ascii=False, indent=1)

print("BEFORE", json.dumps(before, ensure_ascii=False))
print("AFTER ", json.dumps(after, ensure_ascii=False))
print("CHECKS", json.dumps(checks, ensure_ascii=False))
if not checks["diameter_in_range"]:
    print("WARN: 直径不在 2.7-3.0，调 --sxy")
if not checks["not_out_of_frame"]:
    print("WARN: 顶部出画，调 --sz 或后移 y")
