# -*- coding: utf-8 -*-
"""重载景片贴图并渲染（贴图改动后必须 reload，否则用缓存）。"""
import bpy
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REN = os.path.join(ROOT, "renders")
SRC = os.path.join(ROOT, "background_src")
sc = bpy.context.scene

for img in bpy.data.images:
    if img.filepath and os.path.basename(img.filepath).startswith(("M01", "M02", "M03")):
        want = os.path.join(SRC, os.path.basename(img.filepath))
        if os.path.exists(want):
            img.filepath = want
        img.reload()
        print("RELOAD", img.name, tuple(img.size))

sc.render.engine = "CYCLES"
sc.cycles.samples = int(os.environ.get("SAMPLES", "24"))
sc.cycles.seed = 0
sc.cycles.use_denoising = True
sc.render.resolution_x = 1920
sc.render.resolution_y = 1078
sc.render.resolution_percentage = int(os.environ.get("PCT", "50"))
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGB"
bpy.context.preferences.filepaths.save_version = 0

out = os.environ.get("OUT", "R2_preview.png")
sc.render.filepath = os.path.join(REN, out)
bpy.ops.render.render(write_still=True)
print("OUT", sc.render.filepath)
