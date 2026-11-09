"""Axis-aligned render of the four-hall block (inspection only).

    blender -b <v15>/scene.blend --python tools/render_v15_block.py -- <ABS_PNG> [samples]
"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
out = os.path.abspath(argv[0])
spp = int(argv[1]) if len(argv) > 1 else 12
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.get("is_char") or o.get("v14_fog"):
        o.hide_render = True
xs, ys = [], []
for nm in ("h1_floor", "h2_floor", "h3_floor", "h4_floor"):
    ob = bpy.data.objects[nm]
    for c in ob.bound_box:
        p = ob.matrix_world @ Vector(c)
        xs.append(p.x); ys.append(p.y)
cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
cd = bpy.data.cameras.new("ProbeCam")
cd.type = "ORTHO"
cd.ortho_scale = 84.0
cd.clip_start, cd.clip_end = 1.0, 700.0
co = bpy.data.objects.new("ProbeCam", cd)
bpy.context.scene.collection.objects.link(co)
co.location = (cx, cy, 300.0)
co.rotation_euler = (0.0, 0.0, math.radians(-70))
sc.camera = co
sc.render.resolution_x, sc.render.resolution_y = 1000, 1000
sc.cycles.samples = spp
sc.cycles.seed = 0
os.makedirs(os.path.dirname(out), exist_ok=True)
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("V15_BLOCK_DONE", out)
