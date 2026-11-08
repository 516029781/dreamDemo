"""Render the three v07 views from scene.blend in one session.

Hero-only fog: objects flagged `is_fog` are hidden for master/core, shown for hero.
"""
import bpy
import os
import sys
import time

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out_dir = argv[0]
sc = bpy.context.scene
fog_objs = [o for o in bpy.data.objects if o.get("is_fog")]
views = [("Camera", 3360, 5880, 32, "master_raw.png"),
         ("CameraCore", 2072, 1876, 32, "core_raw.png"),
         ("CameraHero", 1920, 1080, 48, "hero_raw.png")]
for cam, w, h, samples, fn in views:
    for o in fog_objs:
        o.hide_render = (cam != "CameraHero")
    sc.camera = bpy.data.objects[cam]
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.cycles.samples = samples
    sc.render.filepath = os.path.join(out_dir, fn)
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    print("VIEW_DONE %s %.1fs" % (fn, time.time() - t0))
