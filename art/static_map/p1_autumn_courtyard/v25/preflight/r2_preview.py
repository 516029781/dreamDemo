# -*- coding: utf-8 -*-
"""R2 快速预览：960×539 / 24spp，用于判断光照与材质返修方向。"""
import bpy
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REN = os.path.join(ROOT, "renders")
os.makedirs(REN, exist_ok=True)
sc = bpy.context.scene

sc.render.engine = "CYCLES"
sc.cycles.samples = 24
sc.cycles.seed = 0
sc.cycles.use_denoising = True
sc.render.resolution_x = 1920
sc.render.resolution_y = 1078
sc.render.resolution_percentage = 50
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGB"
bpy.context.preferences.filepaths.save_version = 0

cam = sc.camera
cam.data.dof.use_dof = True
sc.render.filepath = os.path.join(REN, "R2_preview.png")
bpy.ops.render.render(write_still=True)
print("PREVIEW", os.path.join(REN, "R2_preview.png"))
