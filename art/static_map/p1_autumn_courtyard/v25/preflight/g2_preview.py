# -*- coding: utf-8 -*-
"""G1b 预览：无 DOF 接缝诊断 + 带 DOF 观感图（960×539，20spp）。"""
import bpy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REN = os.path.join(ROOT, "renders")
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene
cam = sc.camera

sc.render.engine = "CYCLES"
sc.cycles.samples = 20
sc.cycles.seed = 0
sc.cycles.use_denoising = True
sc.render.resolution_x = 1920
sc.render.resolution_y = 1078
sc.render.resolution_percentage = 50
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGB"
bpy.context.preferences.filepaths.save_version = 0

cam.data.dof.use_dof = False
sc.render.filepath = os.path.join(REN, "G1b_nodof.png")
bpy.ops.render.render(write_still=True)

cam.data.dof.use_dof = True
sc.render.filepath = os.path.join(REN, "G1b_preview.png")
bpy.ops.render.render(write_still=True)

json.dump({"samples": 20, "resolution": "960x539", "dof": [False, True],
           "f_stop": cam.data.dof.aperture_fstop, "focus_m": round(cam.data.dof.focus_distance, 2)},
          open(os.path.join(PRE, "G1B_PREVIEW.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("G1B PREVIEW DONE")
