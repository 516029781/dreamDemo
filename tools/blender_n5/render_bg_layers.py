"""A2 layer isolation: toggle each distant layer in the built MAP001 blend.

Why this exists: the n4 review said the top of frame is "one dark band" but not
which layer causes it. Rebuilding MAP001 once per hypothesis costs ~6 minutes
each; opening the saved blend and hiding one object pair costs a render. This
script produces same-camera, same-light renders with exactly one layer removed
at a time so the culprit is attributable rather than guessed.

Usage (after MAP001 has been built for candidate_n5):
  blender --background --factory-startup --python tools/blender_n5/render_bg_layers.py
"""
import json
import os
import sys

import bpy

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import courtyard_lib as cl  # noqa: E402

BLEND = os.path.join(cl.SRC_LAYOUT, "MAP001_courtyard.blend")
OUT_DIR = os.path.join(cl.PREVIEW_LAYOUT, "a2_layers")
RES = (1280, 720)
SAMPLES = 40

LAYERS = {
    "treeline": ("MAP001_bg_treeline_mass", "MAP001_bg_treeline_cards"),
    "far_hedge_row": ("MAP001_bg_hedge_far", "MAP001_bg_hedge_far_cards"),
    "near_hedge": ("MAP001_bg_hedge", "MAP001_bg_hedge_cards"),
    "background_trees": ("MAP001_bg_tree_trunks", "MAP001_bg_tree_crowns"),
}


def render(out_path):
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = RES
    scene.cycles.samples = SAMPLES
    scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    return out_path


def main():
    if not os.path.isfile(BLEND):
        raise SystemExit("MAP001 blend missing: %s" % BLEND)
    os.makedirs(OUT_DIR, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"

    present = {o.name for o in bpy.data.objects}
    report = {"blend": BLEND, "camera": scene.camera.name if scene.camera else None,
              "variants": {}}

    for variant, names in LAYERS.items():
        missing = [n for n in names if n not in present]
        if missing:
            report["variants"][variant] = {"skipped": "missing objects", "missing": missing}
            continue
        for n in names:
            bpy.data.objects[n].hide_render = True
        path = render(os.path.join(OUT_DIR, "MAP001_no_%s.png" % variant))
        for n in names:
            bpy.data.objects[n].hide_render = False
        report["variants"][variant] = {"hidden": names, "render": path}
        print("LAYER_RENDER=%s" % path)

    report["variants"]["full"] = {"render": render(os.path.join(OUT_DIR, "MAP001_full.png"))}
    print("LAYER_RENDER=%s" % report["variants"]["full"]["render"])

    out_json = os.path.join(OUT_DIR, "a2_layers.json")
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print("A2_LAYERS_JSON=%s" % out_json)


main()
