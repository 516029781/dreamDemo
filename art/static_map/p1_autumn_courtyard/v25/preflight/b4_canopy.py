# -*- coding: utf-8 -*-
"""B2 树冠加密并下垂：复制叶簇、随机偏移、整体下移。

用法：
    blender -b scene.blend -P preflight/b2_canopy.py -- --copies 2.2 --drop 0.35
"""
import argparse
import json
import math
import os
import random
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene
cam = sc.camera

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--copies", type=float, default=2.2, help="叶簇复制倍数")
ap.add_argument("--drop", type=float, default=0.35, help="整体下移米数")
ap.add_argument("--radius", type=float, default=1.6)
ap.add_argument("--seed", type=int, default=20261031)
ap.add_argument("--dry-run", action="store_true")
args = ap.parse_args(argv)

random.seed(args.seed)

canopy = [o for o in sc.objects
          if o.type == "MESH" and ("foliage" in o.name.lower()
                                   or "Tree joined autumn foliage" in o.name)]
if not canopy:
    raise SystemExit("no canopy objects found")

base_faces = sum(len(o.data.polygons) for o in canopy)
target_extra = max(0, int(round(len(canopy) * (args.copies - 1.0))))

created = []
for src in canopy[:2]:
    for i in range(target_extra):
        dup = src.copy()
        dup.data = src.data.copy()
        dup.name = f"{src.name} | densify {i:02d}"
        sc.collection.objects.link(dup)
        # 在冠层包围盒内随机偏移
        bb = [src.matrix_world @ Vector(c) for c in src.bound_box]
        cx = sum(v.x for v in bb) / 8
        cy = sum(v.y for v in bb) / 8
        cz = sum(v.z for v in bb) / 8
        dup.location = (cx + random.uniform(-args.radius, args.radius),
                        cy + random.uniform(-args.radius, args.radius),
                        cz + random.uniform(-args.radius * 0.5, args.radius * 0.5))
        s = random.uniform(0.8, 1.2)
        dup.scale = (src.scale.x * s, src.scale.y * s, src.scale.z * s)
        dup.rotation_euler = (src.rotation_euler.x,
                              src.rotation_euler.y,
                              src.rotation_euler.z + random.uniform(0, math.tau))
        created.append(dup.name)

# 整体下移（含新副本）
for ob in canopy + [bpy.data.objects[n] for n in created]:
    ob.location.z -= args.drop

bpy.context.view_layer.update()

# 冠层下缘投影
tv = (18.0 / cam.data.lens) * (1078 / 1920)
pitch = 90 - math.degrees(cam.rotation_euler.x)
o = cam.matrix_world.translation
allz, ally = [], []
for ob in canopy + [bpy.data.objects[n] for n in created]:
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    allz += [v.z for v in bb]
    ally += [v.y for v in bb]
zmin, ymin = min(allz), min(ally)
p = math.degrees(math.atan2(o.z - zmin, ymin - o.y))
v_low = 0.5 - (math.tan(math.radians(pitch)) - math.tan(math.radians(p))) / (2 * tv)

new_faces = sum(len(bpy.data.objects[n].data.polygons) for n in created)
rec = {
    "canopy_sources": [o.name for o in canopy],
    "copies_created": len(created),
    "faces_before": base_faces,
    "faces_after": base_faces + new_faces,
    "face_ratio": round((base_faces + new_faces) / max(1, base_faces), 2),
    "canopy_bottom_v": round(v_low, 4),
    "checks": {
        "bottom_in_range": 0.23 <= v_low <= 0.26,
        "face_ratio_ok": (base_faces + new_faces) / max(1, base_faces) <= 2.3,
    },
}

if not args.dry_run:
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))

with open(os.path.join(PRE, "B2_CANOPY.json"), "w", encoding="utf-8") as f:
    json.dump(rec, f, ensure_ascii=False, indent=1)

print("COPIES", len(created), "FACES", rec["faces_before"], "->", rec["faces_after"],
      f'({rec["face_ratio"]}x)')
print("CANOPY BOTTOM v =", f'{v_low*100:.1f}%', "目标 23-26%")
print("CHECKS", json.dumps(rec["checks"], ensure_ascii=False))
