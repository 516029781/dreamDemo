# -*- coding: utf-8 -*-
"""B4 + B5：单主光、压暗部、开景深。

用法：
    blender -b scene.blend -P preflight/b45_light_dof.py -- --exposure -1.12 --fstop 1.8 --focus 22
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
ap.add_argument("--exposure", type=float, default=-1.12)
ap.add_argument("--fstop", type=float, default=1.8)
ap.add_argument("--focus", type=float, default=22.0)
ap.add_argument("--sun-dir", default="-0.55,-0.45,0.70")
ap.add_argument("--dry-run", action="store_true")
args = ap.parse_args(argv)

log = {"lights": [], "world": [], "dof": {}, "exposure": {}, "checks": {}}

# ---------- 1. 主光 ----------
SUN = "Warm directional afternoon sun"
KEY = "Warm late afternoon key"
BOUNCE = "v15 broad warm camera-side bounce"
FILL = "Cool sky fill"

d = Vector([float(x) for x in args.sun_dir.split(",")]).normalized()
quat = d.to_track_quat("Z", "Y")

for ob in sc.objects:
    if ob.type != "LIGHT":
        continue
    L = ob.data
    if ob.name == SUN:
        L.energy = 14.0
        if hasattr(L, "angle"):
            L.angle = math.radians(1.2)
        L.use_shadow = True
        ob.rotation_euler = quat.to_euler()
        log["lights"].append({"name": ob.name, "energy": 14.0,
                              "dir": [round(c, 3) for c in d],
                              "euler": [round(c, 4) for c in ob.rotation_euler]})
    elif ob.name == KEY:
        L.energy = 120.0
        L.use_shadow = False
        log["lights"].append({"name": ob.name, "energy": 120.0, "shadow": False})
    elif ob.name == BOUNCE:
        L.energy = 12.0
        log["lights"].append({"name": ob.name, "energy": 12.0})
    elif ob.name == FILL:
        L.energy = 4.0
        log["lights"].append({"name": ob.name, "energy": 4.0})

# ---------- 2. world ----------
w = sc.world
if w and w.node_tree:
    for n in w.node_tree.nodes:
        if n.type == "BACKGROUND":
            old = n.inputs["Strength"].default_value
            n.inputs["Strength"].default_value = min(old, 0.35)
            log["world"].append({"strength_before": round(old, 3),
                                 "after": round(n.inputs["Strength"].default_value, 3)})

# ---------- 3. 曝光 ----------
old_exp = sc.view_settings.exposure
sc.view_settings.exposure = args.exposure
log["exposure"] = {"before": round(old_exp, 3), "after": args.exposure}

# ---------- 4. 景深 ----------
old_f, old_focus = cam.data.dof.aperture_fstop, cam.data.dof.focus_distance
cam.data.dof.use_dof = True
cam.data.dof.aperture_fstop = args.fstop
cam.data.dof.focus_distance = args.focus

# CoC 验算：CoC = f^2 * |s-d| / (N * d * (s-f))
f = cam.data.lens
N = args.fstop
coc_c = 0.03
s = args.focus * 1000.0
f_mm = f
d_bg = 60000.0
coc_bg = (f_mm ** 2) * abs(s - d_bg) / (N * d_bg * (s - f_mm))
H_hyper = f_mm ** 2 / (N * coc_c) + f_mm
far_lim = H_hyper * s / max(1e-6, (H_hyper - s))
log["dof"] = {"fstop": [old_f, args.fstop], "focus": [old_focus, args.focus],
              "hyperfocal_m": round(H_hyper / 1000, 1),
              "far_limit_m": round(far_lim / 1000, 1),
              "coc_at_60m_mm": round(coc_bg, 3)}
log["checks"]["bg_blurred"] = coc_bg >= 2.0
log["checks"]["subject_sharp"] = far_lim / 1000 > 30

if not args.dry_run:
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))

with open(os.path.join(PRE, "B45_LIGHT_DOF.json"), "w", encoding="utf-8") as fp:
    json.dump(log, fp, ensure_ascii=False, indent=1)

print("LIGHTS", json.dumps(log["lights"], ensure_ascii=False))
print("WORLD ", json.dumps(log["world"], ensure_ascii=False))
print("DOF   ", json.dumps(log["dof"], ensure_ascii=False))
print("CHECKS", json.dumps(log["checks"], ensure_ascii=False))
