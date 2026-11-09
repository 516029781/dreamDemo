"""Isolated reopen-and-rerender reproduction for v13 (TV13-08).

Per HARNESS_LIFECYCLE §3: compare CONTENT SHA (decoded raw RGB), never the
container SHA of the PNG file. Renders a fixed low-resolution master so the
check is cheap; the declared tolerance is "identical decoded RGB bytes" at
420x620 / 8 samples / same camera / same color management.
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
sc.render.resolution_x, sc.render.resolution_y = 420, 620
sc.cycles.samples = 8
sc.cycles.seed = 0
sc.render.filepath = os.path.abspath(out)
bpy.ops.render.render(write_still=True)
print("REPRO_RENDER_DONE", out)
