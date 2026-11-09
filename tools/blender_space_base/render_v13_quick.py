"""v13 quick look: master ortho (840) + hero (960x540), low samples."""
import os
import sys

import bpy

from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
out = argv[0]
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.get("is_char"):
        o.hide_render = True

sc.camera = bpy.data.objects["Camera"]
sc.render.resolution_x, sc.render.resolution_y = 840, 1239
sc.cycles.samples = 12
sc.render.filepath = os.path.join(out, "q_master.png")
bpy.ops.render.render(write_still=True)
print("QUICK_DONE master")

cdh = bpy.data.cameras.new("H12")
cdh.lens = 40.0
cdh.clip_start, cdh.clip_end = 1.0, 3000.0
hero = bpy.data.objects.new("Hero12", cdh)
sc.collection.objects.link(hero)
hero.location = (-10.0, -360.0, 205.0)
_d = Vector((150.0, -70.0, 0.0)) - Vector(hero.location)
hero.rotation_euler = _d.to_track_quat("-Z", "Y").to_euler()
sc.camera = hero
sc.render.resolution_x, sc.render.resolution_y = 960, 540
sc.cycles.samples = 20
sc.render.filepath = os.path.join(out, "q_hero.png")
bpy.ops.render.render(write_still=True)
print("QUICK_DONE hero")
