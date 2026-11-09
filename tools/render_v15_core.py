"""Quick core-tile render for the v15 four-room iteration loop.

    blender -b <v15>/scene.blend --python tools/render_v15_core.py -- <ABS_PNG> [samples]
"""
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
out = os.path.abspath(argv[0])
spp = int(argv[1]) if len(argv) > 1 else 12
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.get("is_char") or o.get("v14_fog"):
        o.hide_render = True
sc.camera = bpy.data.objects["CameraCore"]
sc.render.resolution_x, sc.render.resolution_y = 1620, 1470
sc.cycles.samples = spp
sc.cycles.seed = 0
os.makedirs(os.path.dirname(out), exist_ok=True)
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("V15_CORE_DONE", out)
