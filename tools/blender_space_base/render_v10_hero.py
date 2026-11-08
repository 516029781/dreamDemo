"""Render hero-camera variants for the v10 scene (promo framing, fog on).

Usage:
  blender -b scene.blend --python tools/blender_space_base/render_v9_hero.py -- <out_dir> [samples]
"""
import os
import sys
import time

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out_dir = argv[0] if argv else "art/static_map/space_base_minigame/v10/renders/hero"
samples = int(argv[1]) if len(argv) > 1 else 48

os.makedirs(out_dir, exist_ok=True)
sc = bpy.context.scene

for o in bpy.data.objects:
    if o.get("is_char"):
        o.hide_render = True

# fog adds the aerial depth the promo shots need
for o in bpy.data.objects:
    if o.get("is_fog"):
        o.hide_render = False

VARIANTS = (
    # name, location, target, lens, fstop
    ("HeroWide", (-140.0, -470.0, 330.0), (150.0, -70.0, 0.0), 50.0, 8.0),
    ("HeroMid", (10.0, -430.0, 215.0), (160.0, -90.0, 0.0), 55.0, 6.3),
    ("HeroLow", (60.0, -330.0, 78.0), (200.0, -150.0, 8.0), 45.0, 5.6),
)

for name, loc, tgt, lens, fstop in VARIANTS:
    cd = bpy.data.cameras.new(name)
    cam = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(cam)
    cam.location = loc
    d = Vector(tgt) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cd.lens = lens
    cd.clip_start = 1.0
    cd.clip_end = 3000.0
    cd.dof.use_dof = True
    cd.dof.focus_distance = d.length
    cd.dof.aperture_fstop = fstop

    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.cycles.samples = samples
    sc.render.filepath = os.path.join(out_dir, f"{name}.png")
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    print("HERO_DONE %s %.1fs" % (name, time.time() - t0))

print("HERO_ALL_OK")
