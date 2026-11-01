"""
Build the remaining courtyard props as native Blender geometry.

PROP002 pergola, PROP003 message board (three independently switchable card
slots, empty/partial/full previews), PROP004 lamp, PROP005 direction sign with
editable text, PROP006 three native postcard pickups.

Run one stage per process from the project root:
  .tools/blender/blender-4.5.15-windows-x64/blender.exe --background --factory-startup \
      --python tools/blender/build_props_courtyard.py -- pergola

Stages: pergola, message_board, lamp, direction_sign, postcards
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Euler, Vector

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import courtyard_lib as cl  # noqa: E402
import courtyard_postcard as pc  # noqa: E402


# ---------------------------------------------------------------------------
# PROP002 pergola
# ---------------------------------------------------------------------------

def create_pergola(collection, origin=(0, 0, 0), rot=0.0, prefix="PROP002"):
    wood, dark = cl.mat_wood(), cl.mat_wood_dark()
    stone, iron, brass = (cl.mat_stone_base(), cl.mat_metal(),
                          cl.mat_metal_brass())
    frame_bm = bmesh.new()
    # Footings.
    for x in (-1.45, 1.45):
        for y in (-1.15, 1.15):
            cl.add_box(frame_bm, (x, y, 0.055), (0.30, 0.30, 0.11), mat_index=2)
    # Four posts.
    for x in (-1.45, 1.45):
        for y in (-1.15, 1.15):
            cl.add_box(frame_bm, (x, y, 1.30), (0.14, 0.14, 2.38), mat_index=0)
    # Corner braces (two per post, in the XZ plane under the main beams).
    for x in (-1.45, 1.45):
        for y in (-1.15, 1.15):
            sx = 1.0 if x > 0 else -1.0
            cl.add_box(frame_bm, (x - sx * 0.24, y, 2.30), (0.56, 0.075, 0.075),
                       rot_deg=(0, -45 * sx, 0), mat_index=1)
    frame = cl.finish_mesh(prefix + "_frame", frame_bm,
                           [wood, dark, stone], collection)
    cl.add_bevel(frame, width=0.007, segments=2)

    roof_bm = bmesh.new()
    # Main beams along X.
    for y in (-1.15, 1.15):
        cl.add_box(roof_bm, (0, y, 2.535), (3.36, 0.13, 0.15), mat_index=0)
    # Rafters along Y.
    for i in range(5):
        x = -1.30 + i * 0.65
        cl.add_box(roof_bm, (x, 0, 2.63), (0.085, 2.92, 0.10), mat_index=1)
    roof = cl.finish_mesh(prefix + "_roof", roof_bm, [wood, dark], collection)
    cl.add_bevel(roof, width=0.007, segments=2)
    roof["occlusion_group"] = "OCC_pergola_roof"

    metal_bm = bmesh.new()
    for x in (-1.45, 1.45):
        for y in (-1.15, 1.15):
            # Through-bolt at the post/beam connection.
            cl.add_cylinder(metal_bm, (x, y - 0.10, 2.23), (x, y + 0.10, 2.23),
                            0.018, 0.018, 8, 1)
    metal = cl.finish_mesh(prefix + "_metal", metal_bm, [iron, brass], collection)
    cl.add_bevel(metal, width=0.003, segments=1)

    objs = [frame, roof, metal]
    for o in objs:
        cl.set_instance(o, origin, rot)
        o["asset_id"] = "PROP002"
    frame["collision"] = "4 posts, 0.18 x 0.18 plan footprint; roof is not a collider"
    frame["roof_canopy_group"] = "OCC_pergola_roof"
    frame["clearance_note"] = "roof spans x 10.1-13.4 / z 5.3-7.9 in the map; card C at (8,5) is outside"
    return objs


# ---------------------------------------------------------------------------
# PROP003 message board
# ---------------------------------------------------------------------------

def create_message_board(collection, origin=(0, 0, 0), rot=0.0,
                         prefix="PROP003"):
    wood, dark = cl.mat_wood(), cl.mat_wood_dark()
    paper, brass, ink = cl.mat_paper_kraft(), cl.mat_metal_brass(), cl.mat_ink()
    stone = cl.mat_stone_base()

    bm = bmesh.new()
    for x in (-1.02, 1.02):
        cl.add_box(bm, (x, 0.03, 0.08), (0.24, 0.24, 0.16), mat_index=3)
        cl.add_box(bm, (x, 0.03, 0.98), (0.10, 0.10, 1.80), mat_index=1)
        cl.add_box(bm, (x, 0.03, 1.89), (0.14, 0.14, 0.05), mat_index=1)
        cl.add_cylinder(bm, (x, 0.03, 1.915), (x, 0.03, 1.975), 0.066, 0.008,
                        4, 0)
    # Board frame (outer) and cap.
    cl.add_box(bm, (0, -0.005, 0.84), (2.30, 0.12, 0.10), mat_index=0)
    cl.add_box(bm, (0, -0.005, 1.75), (2.30, 0.12, 0.10), mat_index=0)
    for x in (-1.10, 1.10):
        cl.add_box(bm, (x, -0.005, 1.295), (0.10, 0.12, 1.00), mat_index=0)
    cl.add_box(bm, (0, -0.01, 1.83), (2.48, 0.30, 0.07), mat_index=0)
    cl.add_box(bm, (0, -0.02, 0.775), (2.18, 0.20, 0.055), mat_index=1)
    panel = cl.finish_mesh(prefix + "_wood", bm, [wood, dark, paper, stone],
                           collection)
    cl.add_bevel(panel, width=0.006, segments=2)

    panel_bm = bmesh.new()
    cl.add_box(panel_bm, (0, -0.045, 1.295), (2.10, 0.02, 0.88), mat_index=0)
    cork = cl.finish_mesh(prefix + "_cork", panel_bm, [paper], collection)

    plate_bm = bmesh.new()
    cl.add_box(plate_bm, (0, -0.066, 0.845), (0.50, 0.004, 0.095), mat_index=0)
    plate = cl.finish_mesh(prefix + "_label_plate", plate_bm, [brass], collection)

    label = cl.add_text(prefix + "_label_text", "秋 日 来 信", size=0.14,
                        location=(0, -0.069, 0.846), rot_deg=(90, 0, 0),
                        extrude=0.0015, mat=ink, collection=collection)

    cards = []
    for idx, design in enumerate(("A", "B", "C")):
        card = pc.create_postcard(
            collection, design, "%s_card_%s" % (prefix, design), scale=1.75,
            pins=True)
        card.location = (-0.68 + 0.68 * idx, -0.059, 1.125)
        card["slot_index"] = idx
        card["board_state"] = "visible"
        cards.append(card)

    objs = [panel, cork, plate, label] + cards
    cl.place_instance(objs, origin, rot)
    for o in objs:
        o["asset_id"] = "PROP003"
    panel["collision"] = "box 2.48 x 0.32, height 1.98"
    panel["states"] = "card_A / card_B / card_C are independent visibility nodes"
    return objs


# ---------------------------------------------------------------------------
# PROP004 lamp
# ---------------------------------------------------------------------------

def create_lamp(collection, origin=(0, 0, 0), rot=0.0, prefix="PROP004"):
    iron, glass, brass, stone = (cl.mat_metal(), cl.mat_lamp_glass(),
                                 cl.mat_metal_brass(), cl.mat_stone_dark())
    bm = bmesh.new()
    cl.add_cylinder(bm, (0, 0, 0.0), (0, 0, 0.06), 0.26, 0.25, 8, 1)
    cl.add_cylinder(bm, (0, 0, 0.06), (0, 0, 0.14), 0.21, 0.18, 8, 1)
    cl.add_cylinder(bm, (0, 0, 0.14), (0, 0, 0.23), 0.16, 0.11, 8, 0)
    cl.add_cylinder(bm, (0, 0, 0.23), (0, 0, 1.98), 0.078, 0.052, 8, 0)
    cl.add_cylinder(bm, (0, 0, 1.98), (0, 0, 2.045), 0.105, 0.105, 8, 2)
    cl.add_cylinder(bm, (0, 0, 2.045), (0, 0, 2.075), 0.145, 0.145, 8, 0)
    # Lantern corner posts and plates.
    for x in (-0.105, 0.105):
        for y in (-0.105, 0.105):
            cl.add_box(bm, (x, y, 2.28), (0.020, 0.020, 0.40), mat_index=0)
    cl.add_box(bm, (0, 0, 2.475), (0.25, 0.25, 0.025), mat_index=0)
    cl.add_cylinder(bm, (0, 0, 2.4875), (0, 0, 2.60), 0.175, 0.018, 4, 0)
    cl.add_cylinder(bm, (0, 0, 2.60), (0, 0, 2.655), 0.022, 0.012, 6, 2)
    for s in (-1, 1):
        cl.add_box(bm, (0, s * 0.105, 2.28), (0.19, 0.012, 0.38), mat_index=2)
        cl.add_box(bm, (s * 0.105, 0, 2.28), (0.012, 0.19, 0.38), mat_index=2)
    obj = cl.finish_mesh(prefix + "_iron", bm, [iron, stone, brass], collection)
    cl.add_bevel(obj, width=0.004, segments=2)

    glass_bm = bmesh.new()
    for s in (-1, 1):
        cl.add_box(glass_bm, (0, s * 0.100, 2.28), (0.175, 0.006, 0.36),
                   mat_index=0)
        cl.add_box(glass_bm, (s * 0.100, 0, 2.28), (0.006, 0.175, 0.36),
                   mat_index=0)
    glass_obj = cl.finish_mesh(prefix + "_glass", glass_bm, [glass], collection)

    objs = [obj, glass_obj]
    for o in objs:
        cl.set_instance(o, origin, rot)
        o["asset_id"] = "PROP004"
    obj["collision"] = "circle radius 0.30"
    obj["light_note"] = "emissive glass only; no dynamic light required by the spec"
    return objs


# ---------------------------------------------------------------------------
# PROP005 direction sign (editable text)
# ---------------------------------------------------------------------------

def _add_arrow_board(bm, center, length, height, depth, direction, mat_index):
    cx, cz = center
    tip = length / 2.0
    hinge = length / 2.0 - height * 0.55
    pts = [(-tip, -height / 2), (hinge, -height / 2), (tip, 0.0),
           (hinge, height / 2), (-tip, height / 2)]
    if direction < 0:
        pts = [(-x, z) for (x, z) in pts]
    front_y, back_y = -depth / 2.0, depth / 2.0
    fv = [bm.verts.new((cx + x, front_y, cz + z)) for (x, z) in pts]
    bv = [bm.verts.new((cx + x, back_y, cz + z)) for (x, z) in pts]
    f = bm.faces.new(fv)
    f.material_index = mat_index
    b = bm.faces.new(list(reversed(bv)))
    b.material_index = mat_index
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        f2 = bm.faces.new((fv[i], bv[i], bv[j], fv[j]))
        f2.material_index = mat_index
    return pts


def create_direction_sign(collection, origin=(0, 0, 0), rot=0.0,
                          prefix="PROP005"):
    wood, dark, ink = cl.mat_wood(), cl.mat_wood_dark(), cl.mat_ink()
    iron, brass, leaf = (cl.mat_metal(), cl.mat_metal_brass(),
                         cl.mat_leaf_ochre())
    bm = bmesh.new()
    cl.add_box(bm, (0, 0, 0.045), (0.30, 0.30, 0.09), mat_index=3)
    cl.add_cylinder(bm, (0, 0, 0.09), (0, 0, 2.02), 0.055, 0.048, 8, 1)
    for z, length, direction in ((1.20, 0.92, 1), (1.53, 0.92, -1),
                                 (1.86, 0.92, 1)):
        _add_arrow_board(bm, (0, z), length, 0.205, 0.038, direction, 0)
    cl.add_cylinder(bm, (0, 0, 2.02), (0, 0, 2.10), 0.062, 0.030, 6, 4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = cl.finish_mesh(prefix + "_body", bm, [wood, dark, ink, iron, brass],
                         collection)
    cl.add_bevel(obj, width=0.0045, segments=2)

    text_objs = []
    labels = (("中央花坛", 1.20, 1), ("留言板", 1.53, -1),
              ("秋庭入口", 1.86, 1))
    for i, (body, z, direction) in enumerate(labels):
        text_objs.append(cl.add_text(
            "%s_text_%d" % (prefix, i + 1), body, size=0.24,
            location=(-0.20 * direction, -0.022, z), rot_deg=(90, 0, 0),
            extrude=0.0018, mat=ink, collection=collection))
    # Small leaf marker at the top, facing the viewer.
    leaf_bm = bmesh.new()
    cl.add_leaf(leaf_bm, (0, -0.045, 2.09), Vector((0, -1, 0.2)), 0.115,
                math.radians(15), 0)
    leaf_obj = cl.finish_mesh(prefix + "_leaf", leaf_bm, [leaf], collection)

    objs = [obj, leaf_obj] + text_objs
    cl.place_instance(objs, origin, rot)
    for o in objs:
        o["asset_id"] = "PROP005"
    obj["collision"] = "circle radius 0.28"
    obj["text_note"] = "text objects stay editable in .blend; GLB gets outline meshes"
    return objs


# ---------------------------------------------------------------------------
# PROP006 postcard pickups
# ---------------------------------------------------------------------------

def create_postcards(collection, origin=(0, 0, 0), rot=0.0, prefix="PROP006"):
    objs = []
    for idx, design in enumerate(("A", "B", "C")):
        card = pc.create_postcard(collection, design,
                                  "%s_card_%s" % (prefix, design), scale=1.75,
                                  pins=False)
        card["pickup_id"] = design
        card["interaction_id"] = "pickup_" + design
        objs.append(card)
        for o in objs:
            o["asset_id"] = "PROP006"
    return objs


# ---------------------------------------------------------------------------
# Delivery
# ---------------------------------------------------------------------------

PROP_STAGES = {
    "pergola": {
        "id": "PROP002", "name": "PROP002_pergola", "builder": create_pergola,
        "target": (0, 0, 1.30), "distance": 7.4, "elevation": 17.0,
        "resolution": (1100, 800), "samples": 56,
    },
    "message_board": {
        "id": "PROP003", "name": "PROP003_message_board",
        "builder": create_message_board, "target": (0, 0, 1.10),
        "distance": 5.6, "elevation": 13.0, "resolution": (1000, 850),
        "samples": 56,
    },
    "lamp": {
        "id": "PROP004", "name": "PROP004_lamp", "builder": create_lamp,
        "target": (0, 0, 1.35), "distance": 6.2, "elevation": 9.0,
        "resolution": (900, 900), "samples": 56,
    },
    "direction_sign": {
        "id": "PROP005", "name": "PROP005_direction_sign",
        "builder": create_direction_sign, "target": (0, 0, 1.18),
        "distance": 5.0, "elevation": 10.0, "resolution": (900, 850),
        "samples": 56,
    },
    "postcards": {
        "id": "PROP006", "name": "PROP006_postcards",
        "builder": create_postcards, "target": (0, 0, 0.12),
        "distance": 1.30, "elevation": 26.0, "resolution": (1000, 700),
        "samples": 64, "azimuth": 12.0,
    },
}


def _render_message_board_states(png_base):
    cards = [o for o in bpy.data.objects if o.type == "MESH"
             and o.name.startswith("PROP003_message_board_card_")]
    cards.sort(key=lambda o: o.name)
    if len(cards) != 3:
        raise RuntimeError("expected 3 board cards, found %d" % len(cards))
    for o in cards:
        o.hide_render = False
    bpy.context.view_layer.update()
    cl.render_to(png_base + "_full.png")
    for o in cards:
        o.hide_render = True
    bpy.context.view_layer.update()
    cl.render_to(png_base + "_empty.png")
    cards[0].hide_render = False
    bpy.context.view_layer.update()
    cl.render_to(png_base + "_partial.png")
    for o in cards:
        o.hide_render = False


def deliver(stage_key, cfg):
    cl.reset_scene()
    collection = bpy.context.scene.collection
    objects = cfg["builder"](collection, (0, 0, 0), 0.0, cfg["name"])
    facts = cl.print_module_facts(cfg["name"], objects)
    print("STAGE %s asset_id=%s" % (stage_key, cfg["id"]))

    blend = os.path.join(cl.SRC_PROP, cfg["name"] + ".blend")
    glb = os.path.join(cl.SRC_PROP, cfg["name"] + ".glb")
    png = os.path.join(cl.PREVIEW_PROP, cfg["name"] + ".png")

    cl.save_blend(blend)
    cl.export_glb(objects, glb)

    # Preview-only arrangement for PROP006: cards share a zeroed instance
    # origin in the source; separate them here without touching the saved file.
    if stage_key == "postcards":
        for i, o in enumerate(objects):
            o.location = (-0.24 + 0.24 * i, 0, 0)
        bpy.context.view_layer.update()

    cl.setup_studio(target=cfg["target"], distance=cfg["distance"],
                    elevation_deg=cfg["elevation"], fov_deg=35.0,
                    azimuth_deg=cfg.get("azimuth", 32.0),
                    resolution=cfg["resolution"], samples=cfg["samples"],
                    ground_color="#6F6658")
    if stage_key == "message_board":
        _render_message_board_states(png[:-4])
    else:
        cl.render_to(png)
    print("DELIVERED %s tris=%d" % (cfg["id"], facts["triangles"]))


def main():
    argv = sys.argv
    args = argv[argv.index("--") + 1:] if "--" in argv else []
    stage = args[0] if args else "pergola"
    if stage not in PROP_STAGES:
        raise SystemExit("unknown stage %r (choose from %s)" % (
            stage, ", ".join(PROP_STAGES)))
    deliver(stage, PROP_STAGES[stage])


if __name__ == "__main__":
    main()
