"""Identify which objects occupy the top band of the game frame (no render)."""
import math
import os
import sys

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools", "blender_n5")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import courtyard_lib as cl  # noqa: E402
import render_game_layers as rgl  # noqa: E402

BLEND = os.path.join(cl.SRC_LAYOUT, "MAP001_courtyard.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene

cam_data = bpy.data.cameras.new("DIAG_CAM")
cam_data.sensor_fit = "VERTICAL"
cam_data.angle_y = math.radians(rgl.FOV_Y)
cam = bpy.data.objects.new("DIAG_CAM", cam_data)
scene.collection.objects.link(cam)
cam.location = Vector(rgl.CAM_POS)
cam.rotation_euler = (Vector(rgl.CAM_LOOK) - Vector(rgl.CAM_POS)).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam
bpy.context.view_layer.update()

rows = []
for obj in scene.objects:
    if obj.type != "MESH":
        continue
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    ndc = [world_to_camera_view(scene, cam, p) for p in pts]
    if not ndc:
        continue
    xs = [p.x for p in ndc]
    ys = [p.y for p in ndc]
    if max(ys) < 0.62 or min(xs) > 1.0 or max(xs) < 0.0:
        continue
    mats = [s.material.name if s.material else "?" for s in obj.material_slots]
    rows.append({
        "name": obj.name,
        "x": [round(min(xs), 2), round(max(xs), 2)],
        "y": [round(min(ys), 2), round(max(ys), 2)],
        "mats": mats[:4],
        "zmax": round(max(p.z for p in pts), 2),
    })
rows.sort(key=lambda r: r["y"][1], reverse=True)
for r in rows:
    print("TOPBAND", r["name"], r["x"], r["y"], r["mats"], "zmax", r["zmax"])
print("TOPBAND_COUNT", len(rows))
