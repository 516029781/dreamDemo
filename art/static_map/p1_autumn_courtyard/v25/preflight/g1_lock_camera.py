# -*- coding: utf-8 -*-
"""锁定 C1 机位并把关键水岸点投影到屏幕，供水面/岸沿/对岸定形。"""
import bpy
import json
import math
import os
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene
cam = sc.camera

BASE = 1.23617494
PITCH_DELTA = -math.radians(1.5)
cam.rotation_euler.x = BASE + PITCH_DELTA
cam.rotation_euler.y = 0.0
cam.rotation_euler.z = 0.01198983

fwd = (cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))).normalized()
right = (cam.matrix_world.to_quaternion() @ Vector((1, 0, 0))).normalized()
up = (cam.matrix_world.to_quaternion() @ Vector((0, 1, 0))).normalized()
o = cam.matrix_world.translation
th = 18.0 / cam.data.lens
tv = th * 1078 / 1920


def scr(P):
    d = Vector(P) - o
    z = d.dot(fwd)
    return (0.5 + 0.5 * (d.dot(right) / z) / th,
            0.5 - 0.5 * (d.dot(up) / z) / tv, z)


pts = {
    "shore_cap_front_y14.20_z0.13": (0, 14.20, 0.13),
    "shore_cap_back_y14.80_z0.13": (0, 14.80, 0.13),
    "terrace_edge_y15.20_z0.03": (0, 15.20, 0.03),
    "water_near_y15.40_z-0.18": (0, 15.40, -0.18),
    "water_y18_z-0.18": (0, 18.0, -0.18),
    "water_y21_z-0.18": (0, 21.0, -0.18),
    "water_far_y24_z-0.18": (0, 24.0, -0.18),
    "water_y28_z-0.18": (0, 28.0, -0.18),
    "bank_y26_z0.2": (0, 26.0, 0.2),
    "bank_y30_z0.6": (0, 30.0, 0.6),
    "ground_y40": (0, 40.0, 0.0),
    "ground_y55": (0, 55.0, 0.0),
}
out = {"camera": {"loc": [round(v, 4) for v in cam.location],
                  "rot_x": round(cam.rotation_euler.x, 8),
                  "pitch_deg": round(90 - math.degrees(cam.rotation_euler.x), 3),
                  "lens": cam.data.lens, "exposure": sc.view_settings.exposure},
       "horizon_v": round(0.5 - 0.5 * math.tan(math.radians(90 - math.degrees(cam.rotation_euler.x))) / tv, 4),
       "points": {}}
print("pitch", out["camera"]["pitch_deg"], "horizon", out["horizon_v"])
for k, P in pts.items():
    u, v, z = scr(P)
    out["points"][k] = {"u": round(u, 4), "v": round(v, 4), "depth": round(z, 2)}
    print(f"  {k:34s} u={u*100:6.2f}%  v={v*100:6.2f}%  d={z:6.2f}m")

json.dump(out, open(os.path.join(PRE, "G1_SHORE_PROJECTION.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
print("CAMERA LOCKED C1")
