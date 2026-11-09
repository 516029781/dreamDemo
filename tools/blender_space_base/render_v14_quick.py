"""v14 quick look: master ortho (840x1239) + hero (960x540), low samples."""
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
out = argv[0]
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.get("is_char"):
        o.hide_render = True

sc.camera = bpy.data.objects["Camera"]
sc.render.resolution_x, sc.render.resolution_y = 840, 1239
sc.cycles.samples = 12
sc.cycles.seed = 0
sc.render.filepath = os.path.join(out, "q_master.png")
bpy.ops.render.render(write_still=True)
print("QUICK_DONE master")

sc.camera = bpy.data.objects["CameraHero"]
sc.render.resolution_x, sc.render.resolution_y = 960, 540
sc.cycles.samples = 20
for o in bpy.data.objects:
    if o.get("v14_fog"):
        o.hide_render = False
sc.render.filepath = os.path.join(out, "q_hero.png")
bpy.ops.render.render(write_still=True)
for o in bpy.data.objects:
    if o.get("v14_fog"):
        o.hide_render = True
print("QUICK_DONE")
