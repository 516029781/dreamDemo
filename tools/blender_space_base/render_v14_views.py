"""v14 views: master ortho + hero + route (delivery sizes)."""
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
    if o.get("v14_fog"):
        o.hide_render = True   # master: keep the top-down map legible

sc.camera = bpy.data.objects["Camera"]
sc.render.resolution_x, sc.render.resolution_y = 1680, 2478
sc.cycles.samples = 24
sc.cycles.seed = 0
sc.render.filepath = os.path.join(out, "master_raw.png")
bpy.ops.render.render(write_still=True)
print("VIEW_DONE master")

for o in bpy.data.objects:
    if o.get("v14_fog"):
        o.hide_render = False  # hero: atmospheric depth
cdh = bpy.data.cameras.new("H11")
cdh.lens = 40.0
cdh.clip_start, cdh.clip_end = 1.0, 3000.0
hero = bpy.data.objects.new("Hero11", cdh)
sc.collection.objects.link(hero)
hero.location = (-10.0, -360.0, 205.0)
_d = Vector((150.0, -70.0, 0.0)) - hero.location
hero.rotation_euler = _d.to_track_quat("-Z", "Y").to_euler()
sc.camera = hero
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.cycles.samples = 40
sc.render.filepath = os.path.join(out, "hero_raw.png")
bpy.ops.render.render(write_still=True)
print("VIEW_DONE hero")

for o in bpy.data.objects:
    if o.get("v14_fog"):
        o.hide_render = True
cd = bpy.data.cameras.new("R")
cam = bpy.data.objects.new("R", cd)
sc.collection.objects.link(cam)
cam.location = (-120.0, -370.0, 220.0)
d = Vector((140.0, -55.0, 0.0)) - cam.location
cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
cd.lens = 42.0
cd.clip_start, cd.clip_end = 1.0, 3000.0
sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 1680, 2478
sc.cycles.samples = 32
sc.render.filepath = os.path.join(out, "route.png")
bpy.ops.render.render(write_still=True)
print("VIEW_DONE")
