# -*- coding: utf-8 -*-
"""诊断：隐藏水面后渲一张，确认 M02/M03 景片是否正常显示、位置是否对。"""
import bpy
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REN = os.path.join(ROOT, "renders")
sc = bpy.context.scene

for ob in sc.objects:
    if ob.name.startswith("M01W"):
        ob.hide_render = True
        print("HIDDEN", ob.name)

sc.render.engine = "CYCLES"
sc.cycles.samples = 16
sc.cycles.seed = 0
sc.cycles.use_denoising = True
sc.render.resolution_x = 1920
sc.render.resolution_y = 1078
sc.render.resolution_percentage = 50
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGB"
bpy.context.preferences.filepaths.save_version = 0
sc.render.filepath = os.path.join(REN, "DIAG_nowater.png")
bpy.ops.render.render(write_still=True)

for ob in sc.objects:
    if ob.name.startswith("M01W"):
        ob.hide_render = False
print("DONE", sc.render.filepath)
