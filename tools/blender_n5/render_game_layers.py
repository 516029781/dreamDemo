"""A2b: layer isolation at the ACTUAL game camera.

The first A2 pass rendered through the map's overview camera, which does not
match the gameplay framing, so its attribution did not transfer: in the real
canvas only the top ~30 px changed when the far layers were re-graded. This
script adds the game camera (same position/aim/fov as CourtyardBootstrap) to the
saved MAP001 blend and renders one layer hidden at a time, so attribution is
made on the frame that actually ships.

Usage:
  blender --background --factory-startup --python tools/blender_n5/render_game_layers.py
"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import courtyard_lib as cl  # noqa: E402

BLEND = os.path.join(cl.SRC_LAYOUT, "MAP001_courtyard.blend")
OUT_DIR = os.path.join(cl.PREVIEW_LAYOUT, "a2_game_layers")
RES = (1280, 720)
SAMPLES = 40

# CourtyardBootstrap.setupCamera / update(): player-relative follow at the
# rest position (0, PAVING_TOP, -5.2), expressed in ENGINE coordinates.
# Blender scene = (X = engine X, Y = -engine Z, Z = engine Y), so every engine
# point must be converted before it can be used as a Blender camera transform.
ENGINE_CAM_POS = (-2.5, 11.5, -14.6)
ENGINE_CAM_LOOK = (-2.5, 3.5, -3.7)
FOV_Y = 37.5


def to_blender(p):
    return Vector((p[0], -p[2], p[1]))


CAM_POS = to_blender(ENGINE_CAM_POS)
CAM_LOOK = to_blender(ENGINE_CAM_LOOK)

LAYERS = {
    "treeline": ("MAP001_bg_treeline_mass", "MAP001_bg_treeline_cards"),
    "far_hedge_row": ("MAP001_bg_hedge_far", "MAP001_bg_hedge_far_cards"),
    "near_hedge": ("MAP001_bg_hedge", "MAP001_bg_hedge_cards"),
    "background_trees": ("MAP001_bg_tree_trunks", "MAP001_bg_tree_crowns"),
}


def main():
    if not os.path.isfile(BLEND):
        raise SystemExit("MAP001 blend missing: %s" % BLEND)
    os.makedirs(OUT_DIR, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.render.resolution_x, scene.render.resolution_y = RES
    scene.cycles.samples = SAMPLES

    cam_data = bpy.data.cameras.new("GAME_CAM")
    cam_data.sensor_fit = "VERTICAL"
    cam_data.angle_y = math.radians(FOV_Y)
    cam = bpy.data.objects.new("GAME_CAM", cam_data)
    scene.collection.objects.link(cam)
    cam.location = Vector(CAM_POS)
    direction = Vector(CAM_LOOK) - Vector(CAM_POS)
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam

    present = {o.name for o in bpy.data.objects}
    report = {"blend": BLEND,
              "camera": {"engine_pos": list(ENGINE_CAM_POS),
                         "engine_look": list(ENGINE_CAM_LOOK),
                         "blender_pos": [round(v, 3) for v in CAM_POS],
                         "blender_look": [round(v, 3) for v in CAM_LOOK],
                         "fov_y": FOV_Y},
              "variants": {}}

    for variant, names in LAYERS.items():
        missing = [n for n in names if n not in present]
        if missing:
            report["variants"][variant] = {"skipped": missing}
            continue
        for n in names:
            bpy.data.objects[n].hide_render = True
        path = os.path.join(OUT_DIR, "GAME_no_%s.png" % variant)
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        for n in names:
            bpy.data.objects[n].hide_render = False
        report["variants"][variant] = {"hidden": names, "render": path}
        print("GAME_LAYER=%s" % path)

    scene.render.filepath = os.path.join(OUT_DIR, "GAME_full.png")
    bpy.ops.render.render(write_still=True)
    report["variants"]["full"] = {"render": scene.render.filepath}
    print("GAME_LAYER=%s" % scene.render.filepath)

    out = os.path.join(OUT_DIR, "a2_game_layers.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print("A2_GAME_JSON=%s" % out)


main()
