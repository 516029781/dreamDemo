"""Render the 3360x5880 high-res master required by HARNESS_SPEC r14.

Same scene / same Camera / same compositor as render_v14_views.py, only
resolution and samples differ. Overwrites renders/master_raw.png, so run it
AFTER make_v14_delivery.py has derived the 1680x2478 products.
"""
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
out = argv[0]
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.get("is_char"):
        o.hide_render = True
    if o.get("v14_fog"):
        o.hide_render = True
sc.camera = bpy.data.objects["Camera"]
sc.render.resolution_x, sc.render.resolution_y = 3360, 5880
sc.cycles.samples = 12
sc.cycles.seed = 0
sc.render.filepath = os.path.abspath(out)
bpy.ops.render.render(write_still=True)
print("HIGHRES_RAW_DONE", out)
