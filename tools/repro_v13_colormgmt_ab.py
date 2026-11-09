"""Color-management A/B evidence for SPACE_BASE_TECHNICAL_ART_PLAN v1.1 §0.3.

Renders four variants from the SAME scene.blend, SAME camera, SAME samples and
seed, changing only scene.view_settings. Used to verify two claims:

  1. Does AgX really fix the v13 highlight pile-up (and what does it cost)?
  2. Does lowering the bright end break the S1 light-land ratio?

Usage:
  blender -b art/static_map/space_base_minigame/v13/scene.blend \
    --python tools/repro_v13_colormgmt_ab.py -- <ABS_OUTPUT_DIR>

Fixed conditions: Camera / 420x620 / Cycles 8 spp / seed 0 / is_char hidden.
These are low-resolution TREND comparisons only; absolute values are NOT
comparable with the 1680x2478 / 24 spp delivery image. Re-test at delivery
resolution before locking any parameter (P0 in the plan).
"""
from __future__ import annotations

import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
out_dir = argv[0]
os.makedirs(out_dir, exist_ok=True)

sc = bpy.context.scene
for o in bpy.data.objects:
    if o.get("is_char"):
        o.hide_render = True
sc.camera = bpy.data.objects["Camera"]
sc.render.resolution_x, sc.render.resolution_y = 420, 620
sc.cycles.samples = 8
sc.cycles.seed = 0

# (filename, view_transform, look, exposure)
CASES = (
    ("ab_standard.png", "Standard", "None", 0.22),                       # A current
    ("ab_agx_none.png", "AgX", "None", 0.22),                            # B
    ("ab_agx_mhc.png", "AgX", "AgX - Medium High Contrast", 0.22),      # C
    ("ab_standard_m1.png", "Standard", "None", -0.15),                   # D
)

for fn, transform, look, exposure in CASES:
    sc.view_settings.view_transform = transform
    sc.view_settings.look = look          # "Medium High Contrast" alone is INVALID in Blender 4.5
    sc.view_settings.exposure = exposure
    sc.render.filepath = os.path.join(out_dir, fn)
    bpy.ops.render.render(write_still=True)
    print("AB_DONE", fn, transform, look, exposure)
