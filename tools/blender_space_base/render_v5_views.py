"""Render the three v05 views from scene.blend in one session."""
import bpy
import os
import sys
import time

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out_dir = argv[0]
sc = bpy.context.scene
views = [("Camera", 3360, 5880, 24, "master_raw.png"),
         ("CameraCore", 2072, 1876, 32, "core_raw.png"),
         ("CameraHero", 1920, 1080, 48, "hero_raw.png")]
for cam, w, h, samples, fn in views:
    sc.camera = bpy.data.objects[cam]
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.cycles.samples = samples
    sc.render.filepath = os.path.join(out_dir, fn)
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    print("VIEW_DONE %s %.1fs" % (fn, time.time() - t0))
