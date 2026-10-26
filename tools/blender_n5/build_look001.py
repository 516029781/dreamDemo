"""
LOOK001 fixed camera / lighting look-dev scene (native Blender assembly).

A small courtyard corner built from the same native builders used by the map
module set: 2x2 paving modules, ring planter + autumn tree, bench, message
board, lamp, curb, shrubs, grass and fallen leaves.  One fixed demo camera
(45 degrees elevation, vertical FOV 35, from the south) plus a warm sun key, a
cool-gray area fill and real ground contact shadows.

Cycles CPU renders are previews, not engine evidence.  The stored .blend keeps
the camera, lights, geometry and a hidden 1.4 m scale pole for inspection.

Run from the project root:
  .tools/blender/blender-4.5.15-windows-x64/blender.exe --background --factory-startup \
      --python tools/blender/build_look001.py
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import courtyard_lib as cl  # noqa: E402
import build_env_courtyard as env  # noqa: E402
import build_props_courtyard as props  # noqa: E402

BLEND = os.path.join(cl.SRC_LAYOUT, "LOOK001_camera_light.blend")
PNG = os.path.join(cl.PREVIEW_LAYOUT, "LOOK001_camera_light.png")
PNG_SCALE = os.path.join(cl.PREVIEW_LAYOUT, "LOOK001_scale_check.png")
PROFILE = os.path.join(cl.SRC_LAYOUT, "LOOK001_look_profile.json")


def add_paving(collection):
    slabs_bm = bmesh.new()
    mortar_bm = bmesh.new()
    for (x, y) in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
        # Same 4x4 module layout as ENV001, top surface at z=0.
        from env001_layout import add_paving_module  # noqa: E402
        add_paving_module(slabs_bm, mortar_bm, (x, y), z_top=0.0, seed=20261024)
    slabs = cl.finish_mesh("LOOK001_paving", slabs_bm, [cl.mat_stone_base()],
                           collection)
    cl.add_bevel(slabs, width=0.006, segments=2)
    mortar = cl.finish_mesh("LOOK001_mortar", mortar_bm, [cl.mat_mortar()],
                            collection)
    return [slabs, mortar]


def add_scale_pole(collection):
    bm = bmesh.new()
    cl.add_cylinder(bm, (0, 0, 0), (0, 0, 1.4), 0.018, 0.014, 8, 0)
    for z in (0.5, 1.0, 1.4):
        cl.add_box(bm, (0, 0, z), (0.11, 0.02, 0.025), mat_index=1)
    obj = cl.finish_mesh("PREVIEW_scale_pole_1m4", bm,
                         [cl.mat_metal(), cl.mat_gold()], collection)
    obj["preview_only"] = True
    obj["height_m"] = 1.4
    obj.hide_render = True
    return obj


def build():
    cl.reset_scene()
    scene = bpy.context.scene
    collection = scene.collection

    # Ground and paving.
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=17, y_subdivisions=17, size=34.0, location=(0, 0, -0.005))
    ground = bpy.context.object
    ground.name = "LOOK001_ground"
    ground.data.materials.append(cl.mat_ground_soil())

    paving = add_paving(collection)

    curb = env.create_curb(collection, (-1.0, -4.05, 0), 0.0,
                           "LOOK001_curb_1", lod=False)
    curb += env.create_curb(collection, (1.0, -4.05, 0), 0.0,
                            "LOOK001_curb_2", lod=False)
    for o in curb:
        o["asset_id"] = "ENV002"

    planter = env.create_ring_planter(collection, (0, 0, 0), 0.0,
                                      "LOOK001_ring_planter")
    tree = env.create_tree(collection, (0, 0, 0.55), 0.0,
                           "LOOK001_tree")
    bench = _append_bench(collection, (-2.75, 3.0, 0), 200.0, "LOOK001_bench")
    board = props.create_message_board(collection, (3.35, -4.65, 0), 180.0,
                                       "LOOK001_message_board")
    lamp = props.create_lamp(collection, (3.35, 2.25, 0), 0.0, "LOOK001_lamp")
    sign = props.create_direction_sign(collection, (-4.25, -1.9, 0), 180.0,
                                       "LOOK001_sign")
    shrubs = []
    shrubs += env.create_shrub_a(collection, (-4.55, -1.55, 0), 20.0,
                                 "LOOK001_shrub_a")
    shrubs += env.create_shrub_b(collection, (4.35, -2.65, 0), -25.0,
                                 "LOOK001_shrub_b")
    shrubs += env.create_shrub_a(collection, (-3.9, 4.55, 0), 120.0,
                                 "LOOK001_shrub_c")
    grass = env.create_dry_grass(collection, (-4.6, 1.75, 0), 10.0,
                                 "LOOK001_grass")
    leaves = env.create_fallen_leaves(collection, (1.35, 0.55, 0), 0.0,
                                      "LOOK001_leaves")
    leaves2 = env.create_fallen_leaves(collection, (-1.9, -2.9, 0), 40.0,
                                       "LOOK001_leaves_b")

    scale_pole = add_scale_pole(collection)

    all_objs = (paving + curb + planter + tree + bench + board + lamp + sign
                + shrubs + grass + leaves + leaves2 + [scale_pole])
    facts = cl.print_module_facts("LOOK001", [o for o in all_objs
                                              if o is not None and o != scale_pole
                                              and getattr(o, "data", None) is not None
                                              and hasattr(o.data, "materials")])

    # Fixed demo camera and warm/cool light rig.
    cam = cl.setup_demo_camera(target=(0, 0, 2.2), distance=22.0, fov_deg=35.0,
                               resolution=(1280, 720), samples=72)
    scene.view_settings.exposure = -0.25
    cam["look_id"] = "LOOK001"
    cam["elevation_deg"] = 45.0
    cam["vertical_fov_deg"] = 35.0
    cam["azimuth"] = "from engine south (+Z in Blender scene), facing north"
    for obj in scene.objects:
        if obj.type == "LIGHT":
            obj["look_id"] = "LOOK001"

    cl.save_blend(BLEND)
    cl.render_to(PNG)

    # Scale check: 1.4 m pole visible only in this diagnostic frame.
    scale_pole.hide_render = False
    bpy.context.view_layer.update()
    cl.render_to(PNG_SCALE)
    scale_pole.hide_render = True

    cl.write_json(PROFILE, {
        "schema": "courtyard_look/1",
        "id": "LOOK001",
        "camera": {
            "name": cam.name,
            "projection": "perspective",
            "elevation_deg": 45.0,
            "vertical_fov_deg": 35.0,
            "lens_mm_equiv_vertical_fit": round(
                10.125 / math.tan(math.radians(35.0 / 2.0)), 2),
            "target_engine": [0.0, 2.2, 0.0],
            "target_blender": [0.0, 0.0, 2.2],
            "view_from": "south (+Z engine)",
        },
        "lights": {
            "key": {"type": "SUN", "energy": 3.6, "color": [1.0, 0.92, 0.80],
                    "angle_deg": 2.5, "direction": "screen-left / above"},
            "fill": {"type": "AREA", "energy": 900.0, "size": 14.0,
                     "color": [0.68, 0.76, 0.90]},
            "world": {"color": [0.37, 0.41, 0.46], "strength": 0.55},
        },
        "contact_shadow": "real ground plane + Cycles path-traced shadows",
        "units": "1 Blender unit = 1 world unit",
        "scale_check_pole": "1.4 m; hidden in main render, shown in _scale_check",
        "preview": os.path.relpath(PNG, cl.PROJECT).replace("\\", "/"),
        "preview_scale_check": os.path.relpath(PNG_SCALE, cl.PROJECT).replace("\\", "/"),
        "triangles": facts["triangles"],
        "limitations": [
            "Cycles CPU preview, not a Cocos/WeChat render",
            "procedural materials not baked for engine",
            "no character/NPC in this look scene",
        ],
    })


def _append_bench(collection, origin, rot_deg, prefix):
    """Append the existing PROP001 bench source and place it."""
    path = os.path.join(cl.SRC_PROP, "PROP001_bench.blend")
    names = ["PROP001_bench", "PROP001_bench_wood", "PROP001_bench_metal"]
    with bpy.data.libraries.load(path, link=False) as (data_from, data_to):
        data_to.objects = [n for n in names if n in data_from.objects]
    root = None
    appended = []
    for obj in data_to.objects:
        if obj is None:
            continue
        collection.objects.link(obj)
        appended.append(obj)
        if obj.name == "PROP001_bench":
            root = obj
    if root is None:
        raise RuntimeError("PROP001 bench root not found")
    root.name = prefix
    root.location = Vector(origin)
    root.rotation_euler = (0, 0, math.radians(rot_deg))
    _patch_bench_engine_materials()
    print("APPENDED_PROP001 root=%s objects=%s" % (
        root.name, [o.name for o in appended]))
    return appended


def _patch_bench_engine_materials():
    patches = {
        "MAT_bench_wood": ("#887158", 0.55, 0.0),
        "MAT_bench_metal": ("#494744", 0.36, 0.85),
    }
    for name, (hex_color, roughness, metallic) in patches.items():
        mat = bpy.data.materials.get(name)
        if mat is not None:
            mat["engine_base_color"] = list(cl.hex_to_linear_rgba(hex_color))
            mat["engine_roughness"] = roughness
            mat["engine_metallic"] = metallic
            mat["source_hex"] = hex_color


if __name__ == "__main__":
    build()
