"""Render the 3360x5880 high-resolution master required by HARNESS_SPEC r14.

Same scene / same Camera as render_v13_views.py, only resolution and sample
count differ. Pre-declared difference (HARNESS_LIFECYCLE §3): portrait aspect
3360/5880 = 0.571 vs the 1680/2478 = 0.678 delivery frame, so the ortho camera
shows a narrower horizontal span. This is the same relationship v11 had
between its master_raw.png and its delivery master.
"""
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
out = argv[0]
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.get("is_char"):
        o.hide_render = True
sc.camera = bpy.data.objects["Camera"]
sc.render.resolution_x, sc.render.resolution_y = 3360, 5880
sc.cycles.samples = 12
sc.render.filepath = os.path.abspath(out)
bpy.ops.render.render(write_still=True)
print("HIGHRES_RAW_DONE", out)
