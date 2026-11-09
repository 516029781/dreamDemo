"""Hero 1920x1080 for the v15 delivery set.

    blender -b <v15>/scene.blend --python tools/render_v15_hero.py -- <ABS_PNG> [samples]
"""
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
out = os.path.abspath(argv[0])
spp = int(argv[1]) if len(argv) > 1 else 24
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.get("is_char"):
        o.hide_render = True
    if o.get("v14_fog"):
        o.hide_render = False
sc.camera = bpy.data.objects["CameraHero"]
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.cycles.samples = spp
sc.cycles.seed = 0
os.makedirs(os.path.dirname(out), exist_ok=True)
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("V15_HERO_DONE", out)
