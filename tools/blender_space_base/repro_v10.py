"""Isolated reopen reproduction: render at 420x735 and compare RMS with master_raw downscale."""
import bpy
import os
import sys

argv = sys.argv[sys.argv.index("--") + 1:]
out_png, rms_json = argv[0], argv[1]
sc = bpy.context.scene
sc.camera = bpy.data.objects["Camera"]
sc.render.resolution_x = 420
sc.render.resolution_y = 735
sc.cycles.samples = 12
sc.render.filepath = out_png
bpy.ops.render.render(write_still=True)

from PIL import Image
import numpy as np
a = Image.open(out_png).convert("RGB").resize((420, 735))
b = Image.open(rms_json).convert("RGB").resize((420, 735))
ra = np.asarray(a, dtype=np.float32)
rb = np.asarray(b, dtype=np.float32)
# compare only the content area (735 px = whole, bleed included in master)
rms = float(np.sqrt(((ra - rb) ** 2).mean()))
print("REPRO_RMS %.3f" % rms)
