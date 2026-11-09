"""Convergence-only render: one 1680x2478 / 24 spp master (about 77 s).

Used by the automatic convergence loop in SPACE_BASE_V14_ONESHOT_PLAN §6 so we
do not pay for the full 3-view render on every parameter trial.

    blender -b <v14>/scene.blend --python tools/render_v14_master.py -- <ABS_PNG>
"""
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
out = os.path.abspath(argv[0])
os.makedirs(os.path.dirname(out), exist_ok=True)
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.get("is_char") or o.get("v14_fog"):
        o.hide_render = True
sc.camera = bpy.data.objects["Camera"]
sc.render.resolution_x, sc.render.resolution_y = 1680, 2478
sc.cycles.samples = 24
sc.cycles.seed = 0
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("V14_MASTER_DONE", out)
