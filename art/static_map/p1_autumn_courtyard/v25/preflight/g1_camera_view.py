# -*- coding: utf-8 -*-
"""G1a-2：C0/C1/C2 带材质的取景图（960×539，无 DOF，同曝光），
用于判断"远景带面积"与主锚点是否仍完整。纯色图只用于看 world 暴露。"""
import bpy
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REN = os.path.join(ROOT, "renders")
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene
cam = sc.camera

BASE = cam.rotation_euler.x
VARIANTS = {"C0": 0.0, "C1": -math.radians(1.5), "C2": -math.radians(3.0)}

sc.render.engine = "CYCLES"
sc.cycles.samples = 10
sc.cycles.seed = 0
sc.cycles.use_denoising = True
cam.data.dof.use_dof = False
sc.render.resolution_x = 1920
sc.render.resolution_y = 1078
sc.render.resolution_percentage = 50
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGB"
sc.view_settings.view_transform = "Standard"
bpy.context.preferences.filepaths.save_version = 0

log = {}
for tag, d in VARIANTS.items():
    cam.rotation_euler.x = BASE + d
    sc.render.filepath = os.path.join(REN, "G1_view_%s.png" % tag)
    bpy.ops.render.render(write_still=True)
    log[tag] = {"rot_x": round(cam.rotation_euler.x, 6),
                "pitch_deg": round(90 - math.degrees(cam.rotation_euler.x), 3)}
    print("VIEW", tag, log[tag])

cam.rotation_euler.x = BASE
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
json.dump({"base_rot_x": BASE, "lens": cam.data.lens, "exposure": sc.view_settings.exposure,
           "variants": log}, open(os.path.join(PRE, "G1_VIEW_PROBE.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("VIEW PROBE DONE")
