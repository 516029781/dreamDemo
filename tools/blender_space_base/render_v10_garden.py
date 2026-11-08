"""Garden close-ups (GA03 paving / GA04 wall) + HeroRoute wide shot for v10.

Creates the cameras at render time so the delivered scene stays free of
throw-away rigs; every camera is deterministic from the constants below.

Usage:
  blender -b scene.blend --python tools/blender_space_base/render_v10_garden.py -- \
      <out_dir> [samples] [scale]
"""
import math
import os
import sys
import time

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out_dir = argv[0] if argv else "art/static_map/space_base_minigame/v10/renders"
samples = int(argv[1]) if len(argv) > 1 else 32
scale = float(argv[2]) if len(argv) > 2 else 1.0

AV_HEAD, AV_U, AV_V = (125.0, -6.6), (0.342, -0.940), (0.940, 0.342)


def av(t, v, z=0.0):
    n = math.hypot(*AV_U)
    return Vector((AV_HEAD[0] + AV_U[0] / n * t + AV_V[0] * v,
                   AV_HEAD[1] + AV_U[1] / n * t + AV_V[1] * v, z))


sc = bpy.context.scene
for o in bpy.data.objects:
    if o.get("is_char"):
        o.hide_render = True


def shoot(name, loc, tgt, lens, w, h, fstop=None, dof=False):
    cd = bpy.data.cameras.new(name)
    cam = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(cam)
    cam.location = loc
    d = Vector(tgt) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cd.lens = lens
    cd.clip_start = 1.0
    cd.clip_end = 3000.0
    if dof:
        cd.dof.use_dof = True
        cd.dof.focus_distance = d.length
        cd.dof.aperture_fstop = fstop or 6.3
    sc.camera = cam
    sc.render.resolution_x = int(w * scale)
    sc.render.resolution_y = int(h * scale)
    sc.cycles.samples = samples
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = os.path.join(out_dir, f"{name}.png")
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    print("SHOT_DONE %s %.1fs" % (name, time.time() - t0))


os.makedirs(os.path.join(out_dir, "checks"), exist_ok=True)
os.makedirs(os.path.join(out_dir, "hero"), exist_ok=True)

# GA03: three-quarter look down the central walk, joints + 1.2 m band + pool lip
shoot("checks/06_paving", av(47.0, -31.0, 17.0), av(71.0, -6.0, 4.7), 55.0, 1600, 1000, 8.0, True)
# GA04: eye-level at the south-west wall, orange band + coping + pilasters
shoot("checks/07_wall", av(70.0, -60.0, 7.2), av(84.0, -49.0, 5.6), 62.0, 1600, 1000, 5.6, True)
# GA09: the whole route in one frame (island -> bridge A -> garden -> bridge B -> peninsula)
shoot("hero/HeroRoute", (-120.0, -370.0, 220.0), (150.0, -30.0, 0.0), 56.0, 1920, 1080, 8.0, True)

# supplementary eye-level look down the central walk (third-person framing check)
shoot("hero/GardenEye", av(46.0, 0.0, 6.36), av(92.0, 1.0, 6.1), 35.0, 1920, 1080, 4.0, True)

print("GARDEN_ALL_OK")
