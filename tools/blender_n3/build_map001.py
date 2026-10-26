"""
Build MAP001, the full 28 x 20 courtyard layout, from the native module set.

Coordinate contract (also written into layout.json):
  * engine: Y up, ground XZ, map centre (0,0,0), X in [-14,14], Z in [-10,10]
  * Blender scene: X = engine X, Y = -engine Z, Z = engine Y
  * module local front is -Y in Blender, which is +Z in engine space; layout
    rotation_y is the engine yaw applied to that local front.
  * paving modules are sunk so their top surface is engine Y = 0 (ENV001's own
    source keeps its 0.14 module-space top; the layout position compensates).
  * 1 Blender unit = 1 world unit.

The map is assembled from the same builder functions that produce the
standalone module sources (plus the existing PROP001 bench appended from its
source file).  No background image is used.  Cycles renders are previews.

Run from the project root:
  .tools/blender/blender-4.5.15-windows-x64/blender.exe --background --factory-startup \
      --python tools/blender/build_map001.py
"""
import json
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import courtyard_lib as cl  # noqa: E402
import courtyard_postcard as pc  # noqa: E402
import env001_layout  # noqa: E402
import build_env_courtyard as env  # noqa: E402
import build_props_courtyard as props  # noqa: E402

BLEND = os.path.join(cl.SRC_LAYOUT, "MAP001_courtyard.blend")
GLB = os.path.join(cl.SRC_LAYOUT, "MAP001_courtyard.glb")
LAYOUT = os.path.join(cl.SRC_LAYOUT, "layout.json")
PNG = os.path.join(cl.PREVIEW_LAYOUT, "MAP001_courtyard.png")
PNG_TOP = os.path.join(cl.PREVIEW_LAYOUT, "MAP001_topdown.png")

MAP_SIZE = (28.0, 20.0)
SOIL_TOP = -0.02

STATE = {
    "instances": [],
    "interactions": [],
    "proxies": [],
    "occlusion": [],
}


def record(asset_id, inst_id, x, z, rot=0.0, y=0.0, scale=1.0,
           collider=None, interaction_id=None, occlusion_group=None,
           source=None, note=None, objects=None, merged_object=None,
           lod=None):
    entry = {
        "asset_id": asset_id,
        "instance_id": inst_id,
        "position": [round(x, 3), round(y, 3), round(z, 3)],
        "rotation_y": round(rot, 2),
        "scale": [scale, scale, scale],
        "collider": collider or {"type": "none"},
        "interaction_id": interaction_id,
        "occlusion_group": occlusion_group,
        "source": source,
        "note": note,
    }
    if objects:
        entry["objects"] = [o.name for o in objects]
    if merged_object:
        entry["merged_object"] = merged_object
    if lod:
        entry["lod"] = lod
    STATE["instances"].append(entry)
    return entry


def box_collider(x, z, w, d, rot=0.0, height=1.0):
    return {"type": "box", "center": [round(x, 3), round(z, 3)],
            "size": [round(w, 3), round(d, 3)],
            "rotation_y": round(rot, 2), "height": round(height, 3)}


def circle_collider(x, z, radius, height=1.0):
    return {"type": "circle", "center": [round(x, 3), round(z, 3)],
            "radius": round(radius, 3), "height": round(height, 3)}


def join_meshes(objects, name, collection):
    meshes = [o for o in objects if o.type == "MESH"]
    if len(meshes) == 1:
        meshes[0].name = name
        meshes[0]["merged_from"] = 1
        return meshes[0]
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    active = meshes[0]
    bpy.context.view_layer.objects.active = active
    bpy.ops.object.join()
    active.name = name
    active["merged_from"] = len(meshes)
    return active


def add_ground(collection):
    bm = bmesh.new()
    cl.add_box(bm, (0, 0, SOIL_TOP - 0.01), (28.0, 20.0, 0.02), mat_index=0)
    ground = cl.finish_mesh("MAP001_ground", bm, [cl.mat_ground_soil()],
                            collection)

    skirt_bm = bmesh.new()
    cl.add_box(skirt_bm, (0, 0, -0.21), (40.0, 32.0, 0.16), mat_index=0)
    skirt = cl.finish_mesh("MAP001_ground_skirt", skirt_bm,
                           [cl.mat_ground_skirt()], collection)
    return [ground, skirt]


def add_background_scenery(collection):
    """Non-playable depth layer: hedge line and distant autumn trees behind the
    north/east/west fences.  Native meshes only; no colliders and no instance
    records, so they cannot be mistaken for catalog assets."""
    rng = random.Random(20261025)
    hedge_bm = bmesh.new()
    hedge_leaf_bm = bmesh.new()
    hedge_mats = [cl.mat_leaf_deep(), cl.mat_leaf_olive(), cl.mat_leaf_amber()]
    for row, (yy, base_z, rr, spacing, count) in enumerate((
            (-11.9, 0.55, 0.66, 1.02, 29),
            (-12.5, 0.42, 0.58, 1.16, 26),
            (-13.1, 0.30, 0.52, 1.30, 23),
            (-13.7, 0.22, 0.47, 1.48, 20))):
        for i in range(count):
            x = -14.0 + i * spacing + (row * 0.18)
            r = rr + rng.uniform(-0.04, 0.10)
            cl.add_mass_lobe(hedge_bm, (x, yy, base_z), r * 0.46, rng,
                             flatten=0.55, subdiv=2, displace=0.16,
                             mat_index=(i + row) % 2)
            cl.add_leaf_cluster(hedge_leaf_bm, (x, yy, base_z + r * 0.30),
                                r * 1.38, 88, rng, [1, 2, 3, 0],
                                leaf_size=rng.uniform(0.10, 0.16),
                                shell_inner=0.70, z_min=-0.30)
    hedge = cl.finish_mesh("MAP001_bg_hedge", hedge_bm, hedge_mats, collection)
    bpy.ops.object.select_all(action="DESELECT")
    hedge.select_set(True)
    bpy.context.view_layer.objects.active = hedge
    bpy.ops.object.shade_smooth()
    hedge.select_set(False)
    hedge_cards = cl.finish_mesh("MAP001_bg_hedge_cards", hedge_leaf_bm,
                                 [cl.mat_leaf_deep(), cl.mat_leaf_olive(),
                                  cl.mat_leaf_amber()], collection)
    for obj in (hedge, hedge_cards):
        obj["asset_id"] = "SCENERY"
        obj["role"] = "background hedge outside the playable area"
    for side, sx in (("east", 16.0), ("west", -16.0)):
        side_bm = bmesh.new()
        side_leaf_bm = bmesh.new()
        for i in range(8):
            y = -8.0 + i * 2.6
            r = 0.58 + rng.uniform(-0.04, 0.08)
            cl.add_mass_lobe(side_bm, (sx, y, 0.50), r * 0.48, rng,
                             flatten=0.55, subdiv=2, displace=0.16,
                             mat_index=i % 2)
            cl.add_leaf_cluster(side_leaf_bm, (sx, y, 0.68), r * 1.35, 40, rng,
                                [1, 2, 3, 0], leaf_size=0.32,
                                shell_inner=0.55, z_min=-0.30)
        side_hedge = cl.finish_mesh("MAP001_bg_hedge_" + side, side_bm,
                                    [cl.mat_leaf_deep(), cl.mat_leaf_olive()],
                                    collection)
        side_cards = cl.finish_mesh("MAP001_bg_hedge_" + side + "_cards",
                                    side_leaf_bm,
                                    [cl.mat_leaf_deep(), cl.mat_leaf_olive(),
                                     cl.mat_leaf_amber()], collection)
        for obj in (side_hedge, side_cards):
            obj["asset_id"] = "SCENERY"

    leaf_mats = [cl.mat_leaf_ochre(), cl.mat_leaf_amber(),
                 cl.mat_leaf_olive(), cl.mat_leaf_deep()]
    # Distant crown band instead of bare trunks: the formal camera crops tall
    # trees at the top, so a low foliage line reads as depth without poles.
    distant = ((-12.0, -14.4, 1.35, 0.72), (-6.5, -14.8, 1.45, 0.80),
               (-1.0, -14.6, 1.40, 0.76), (4.5, -14.7, 1.45, 0.80),
               (9.5, -14.2, 1.30, 0.72), (13.5, -14.0, 1.20, 0.68))
    band_bm = bmesh.new()
    band_cards = bmesh.new()
    for i, (x, y, r, z) in enumerate(distant):
        cl.add_mass_lobe(band_bm, (x, y, z), r * 0.55, rng, flatten=0.62,
                         subdiv=2, displace=0.15, mat_index=i % 2)
        cl.add_leaf_cluster(band_cards, (x, y, z), r * 1.28, 92, rng,
                            [2, 2, 3, 1], leaf_size=0.17,
                            shell_inner=0.70, z_min=-0.30)
    band = cl.finish_mesh("MAP001_bg_crown_band", band_bm,
                          [cl.mat_leaf_olive(), cl.mat_leaf_deep()], collection)
    band_leaf = cl.finish_mesh("MAP001_bg_crown_band_cards", band_cards,
                               leaf_mats, collection)
    for obj in (band, band_leaf):
        obj["asset_id"] = "SCENERY"
        obj["role"] = "distant crown band outside the playable area"

    # Three background trees break the flat hedge band and add layered depth.
    tree_bm = bmesh.new()
    tree_leaf_bm = bmesh.new()
    for ti, (tx, ty, th, tr) in enumerate(((-10.8, -15.2, 4.8, 1.05),
                                           (-2.2, -15.8, 4.4, 0.92),
                                           (7.6, -15.4, 4.6, 0.98))):
        cl.add_cylinder(tree_bm, (tx, ty, 0.0), (tx + 0.10, ty + 0.05, th * 0.72),
                        tr * 0.11, tr * 0.06, 8, 0)
        for li, (dx, dy, dz, rr) in enumerate(((0.0, 0.0, 0.86, 0.62),
                                               (-0.42, 0.12, 0.80, 0.50),
                                               (0.40, -0.10, 0.82, 0.52),
                                               (0.08, 0.36, 0.72, 0.44),
                                               (-0.10, -0.34, 0.74, 0.42))):
            center = (tx + dx * tr, ty + dy * tr, th * dz)
            cl.add_mass_lobe(tree_leaf_bm, center, tr * rr, rng, flatten=0.72,
                             subdiv=2, displace=0.18, mat_index=li % 2)
            cl.add_leaf_cluster(tree_leaf_bm, center, tr * rr * 1.45, 64, rng,
                                [2, 2, 3, 1], leaf_size=0.16,
                                shell_inner=0.70, z_min=-0.34)
    tree_trunks = cl.finish_mesh("MAP001_bg_tree_trunks", tree_bm,
                                 [cl.mat_wood_dark()], collection)
    tree_crowns = cl.finish_mesh("MAP001_bg_tree_crowns", tree_leaf_bm,
                                 leaf_mats, collection)
    for obj in (tree_trunks, tree_crowns):
        obj["asset_id"] = "SCENERY"
        obj["role"] = "background trees behind hedge"
    STATE.setdefault("scenery", []).append({
        "kind": "background_depth_layer",
        "hedge": ["MAP001_bg_hedge", "MAP001_bg_hedge_cards", "MAP001_bg_hedge_east", "MAP001_bg_hedge_west"],
        "distant_crowns": ["MAP001_bg_crown_band", "MAP001_bg_crown_band_cards"],
        "note": "no colliders, no catalog instances; depth only",
    })


def add_proxy_box(collection, name, x, z, w, d, rot, height):
    bm = bmesh.new()
    cl.add_box(bm, (0, 0, height / 2.0), (w, d, height), mat_index=0)
    obj = cl.finish_mesh(name, bm, [], collection)
    obj.location = (x, -z, 0.0)
    obj.rotation_euler = (0, 0, math.radians(rot))
    obj.display_type = "WIRE"
    obj.hide_render = True
    obj["collision_proxy"] = True
    obj["shape"] = "box"
    STATE["proxies"].append({"name": name, "shape": "box",
                             "center": [x, 0, z], "size": [w, height, d],
                             "rotation_y": rot})
    return obj


def add_proxy_circle(collection, name, x, z, radius, height):
    bm = bmesh.new()
    cl.add_cylinder(bm, (0, 0, 0), (0, 0, height), radius, radius, 16, 0)
    obj = cl.finish_mesh(name, bm, [], collection)
    obj.location = (x, -z, 0.0)
    obj.display_type = "WIRE"
    obj.hide_render = True
    obj["collision_proxy"] = True
    obj["shape"] = "circle"
    STATE["proxies"].append({"name": name, "shape": "circle",
                             "center": [x, 0, z], "radius": radius,
                             "height": height})
    return obj


def add_foreground_details(collection):
    """Low native planting beds and leaf drifts that break the empty paving
    without changing the playable route or the camera."""
    rng = random.Random(20261025 + 3)
    stone, light, dark = cl.mat_stone_base(), cl.mat_stone_light(), cl.mat_stone_dark()
    soil_mat = cl.mat_soil()
    leaf_mats = [cl.mat_leaf_ochre(), cl.mat_leaf_amber(), cl.mat_leaf_olive(),
                 cl.mat_leaf_deep()]
    beds = ((-6.8, -7.2, 3.0, 1.5), (6.8, -7.2, 3.0, 1.5))
    for bi, (bx, bz, bw, bd) in enumerate(beds):
        border = bmesh.new()
        cl.add_box(border, (0, 0, 0.05), (bw, bd, 0.10), mat_index=2)
        cl.add_box(border, (0, 0, 0.14), (bw - 0.18, bd - 0.18, 0.10), mat_index=0)
        for sx in (-1, 1):
            cl.add_box(border, (sx * (bw / 2 - 0.08), 0, 0.20),
                       (0.16, bd, 0.14), mat_index=1 if sx < 0 else 0)
        for sz in (-1, 1):
            cl.add_box(border, (0, sz * (bd / 2 - 0.08), 0.20),
                       (bw, 0.16, 0.14), mat_index=1 if sz > 0 else 0)
        border_obj = cl.finish_mesh("MAP001_fg_bed_%d_stone" % bi, border,
                                    [stone, light, dark], collection)
        cl.add_bevel(border_obj, width=0.008, segments=2)
        border_obj.location = (bx, -bz, 0)
        border_obj["asset_id"] = "SCENERY"
        soil = bmesh.new()
        cl.add_box(soil, (0, 0, 0.12), (bw - 0.30, bd - 0.30, 0.10), mat_index=0)
        soil_obj = cl.finish_mesh("MAP001_fg_bed_%d_soil" % bi, soil, [soil_mat],
                                  collection)
        soil_obj.location = (bx, -bz, 0)
        soil_obj["asset_id"] = "SCENERY"
        leaves = bmesh.new()
        for cx, cz, cr in ((-0.55, 0.0, 0.42), (0.50, 0.05, 0.38),
                           (0.0, -0.25, 0.34)):
            cl.add_leaf_cluster(leaves, (cx, cz, 0.34), cr, 54, rng,
                                [1, 1, 2, 3, 0], leaf_size=0.28,
                                shell_inner=0.55, z_min=-0.30)
        leaf_obj = cl.finish_mesh("MAP001_fg_bed_%d_leaves" % bi, leaves,
                                  leaf_mats, collection)
        leaf_obj.location = (bx, -bz, 0)
        leaf_obj["asset_id"] = "SCENERY"

    # Leaf drifts along the south path edge, one merged draw.
    drift = bmesh.new()
    for (dx, dz, count, radius) in ((-5.8, -7.4, 90, 0.7), (5.8, -7.4, 90, 0.7),
                                     (-2.8, -8.2, 58, 0.45), (2.8, -8.2, 58, 0.45),
                                     (-11.5, -6.2, 38, 0.4), (11.5, -6.2, 38, 0.4)):
        cl.add_leaf_cluster(drift, (dx, dz, 0.045), radius, count, rng,
                            [0, 0, 1, 2, 3], leaf_size=0.16, flatten=0.10,
                            shell_inner=0.05, z_min=-0.40)
    drift_obj = cl.finish_mesh("MAP001_fg_leaf_drift", drift, leaf_mats, collection)
    drift_obj["asset_id"] = "SCENERY"
    drift_obj["role"] = "foreground leaf drift on paving edge"


def append_bench(collection, x, z, rot):
    path = os.path.join(cl.SRC_PROP, "PROP001_bench.blend")
    names = ["PROP001_bench", "PROP001_bench_wood", "PROP001_bench_metal"]
    with bpy.data.libraries.load(path, link=False) as (data_from, data_to):
        data_to.objects = [n for n in names if n in data_from.objects]
    root = None
    meshes = []
    for obj in data_to.objects:
        if obj is None:
            continue
        collection.objects.link(obj)
        if obj.name == "PROP001_bench":
            root = obj
        elif obj.type == "MESH":
            meshes.append(obj)
    if root is None or not meshes:
        raise RuntimeError("PROP001 bench append failed")
    root.location = (x, -z, 0.0)
    root.rotation_euler = (0, 0, math.radians(rot))
    bpy.context.view_layer.update()
    for obj in meshes:
        mw = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = mw
        obj["asset_id"] = "PROP001"
        obj["appended_from"] = "art/candidates/candidate_n3/source/props/PROP001_bench.blend"
        for slot in obj.material_slots:
            if slot.material:
                base = slot.material.name.split(".")[0]
                canon = bpy.data.materials.get(base)
                if canon is not None:
                    slot.material = canon
    root["asset_id"] = "PROP001"
    bpy.data.objects.remove(root, do_unlink=True)
    for name, (hex_color, roughness, metallic) in {
            "MAT_bench_wood": ("#887158", 0.55, 0.0),
            "MAT_bench_metal": ("#494744", 0.36, 0.85)}.items():
        mat = bpy.data.materials.get(name)
        if mat is not None:
            mat["engine_base_color"] = list(cl.hex_to_linear_rgba(hex_color))
            mat["engine_roughness"] = roughness
            mat["engine_metallic"] = metallic
            mat["source_hex"] = hex_color
    return meshes


# ---------------------------------------------------------------------------
# Clearance validation
# ---------------------------------------------------------------------------

def _dist_point_box(px, pz, collider):
    cx, cz = collider["center"]
    ang = math.radians(-collider.get("rotation_y", 0.0))
    dx, dz = px - cx, pz - cz
    lx = dx * math.cos(ang) - dz * math.sin(ang)
    lz = dx * math.sin(ang) + dz * math.cos(ang)
    hw, hd = collider["size"][0] / 2.0, collider["size"][1] / 2.0
    qx = max(abs(lx) - hw, 0.0)
    qz = max(abs(lz) - hd, 0.0)
    return math.hypot(qx, qz)


def _dist_point_collider(px, pz, collider):
    if collider["type"] == "circle":
        cx, cz = collider["center"]
        return max(0.0, math.hypot(px - cx, pz - cz) - collider["radius"])
    if collider["type"] == "box":
        return _dist_point_box(px, pz, collider)
    return 1e9


def clearance_report(points):
    colliders = []
    for i in STATE["instances"]:
        c = i["collider"]
        if c["type"] in ("box", "circle"):
            colliders.append(c)
        elif c["type"] == "compound":
            colliders.extend(c.get("shapes", []))
    results = []
    for name, px, pz, required in points:
        best = min((_dist_point_collider(px, pz, c) for c in colliders),
                   default=1e9)
        inside = any(
            c["type"] == "circle"
            and math.hypot(px - c["center"][0], pz - c["center"][1])
            < c["radius"]
            for c in colliders
        ) or any(
            c["type"] == "box"
            and _dist_point_box(px, pz, c) <= 0.0
            for c in colliders
        )
        results.append({
            "point": name, "nearest_surface_m": round(best, 3),
            "required_m": required, "pass": (best >= required and not inside),
            "inside_collider": inside,
        })
        print("CLEARANCE %s nearest=%.3f required=%.2f inside=%s %s" % (
            name, best, required, inside, "PASS" if best >= required and not inside
            else "FAIL"))
    return results


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build():
    cl.reset_scene()
    scene = bpy.context.scene
    c_ground = cl.new_collection("MAP_ground")
    c_pave = cl.new_collection("MAP_paving")
    c_env = cl.new_collection("MAP_environment")
    c_props = cl.new_collection("MAP_props")
    c_plants = cl.new_collection("MAP_plants")
    c_edge = cl.new_collection("MAP_edge_closure")
    c_col = cl.new_collection("MAP_collision_proxies")
    c_light = cl.new_collection("MAP_lighting")

    # Ground / skirt.
    add_ground(c_ground)
    STATE["ground"] = {
        "courtyard": {"size": [28.0, 20.0], "top_y": SOIL_TOP,
                      "material": "MAT_ground_soil"},
        "skirt": {"size": [40.0, 32.0], "top_y": -0.13,
                  "note": "visual edge skirt outside the playable 28x20 area"},
    }
    add_background_scenery(c_env)
    add_foreground_details(c_env)

    # Paving modules (same 4x4 layout as ENV001, map LOD bevel).
    paving_centers = [
        (-4, -4), (0, -4), (4, -4),
        (-4, 0), (0, 0), (4, 0),
        (-4, 4), (0, 4), (4, 4),
        (-8, -4), (-8, 0), (-8, 4),
        (8, 4), (12, 6), (0, -8), (0, 8),
    ]
    paving_objs = env001_layout.create_paving(
        c_pave, [(x, -z) for (x, z) in paving_centers], z_top=0.0,
        prefix="MAP001_paving", bevel_segments=0, lod=True)
    paving_obj = paving_objs[0]
    for i, (x, z) in enumerate(paving_centers):
        record("ENV001", "paving_%02d" % i, x, z, 0.0, 0.0,
               collider={"type": "none"},
               source="art/full/source/environment/ENV001_stone_paving.blend",
               note="map LOD: same module/joint layout, no bevel; top at y=0",
               merged_object=paving_obj.name,
               lod="bevel_segments=0")

    # Curbs (2.0 m modules; low kerbs are non-blocking).
    curb_placements = []
    for z in (-9, -7):
        curb_placements += [(-2, z, 90), (2, z, 90)]
    for z in (7, 9):
        curb_placements += [(-2, z, 90), (2, z, 90)]
    for x in (-5, -3, 3, 5):
        curb_placements += [(x, -6, 0), (x, 6, 0)]
    for z in (-5, -3, -1, 1):
        curb_placements.append((6, z, 90))
    for z in (-5, -3, -1, 1, 3, 5):
        curb_placements.append((-10, z, 90))
    for x in (-9, -7):
        curb_placements.append((x, -6, 0))
    curb_placements += [(10, 3, 90)]
    for x in (7, 9):
        curb_placements += [(x, 2, 0), (x, 6, 0)]
    curb_placements += [(10, 7, 90)]
    for x in (11, 13):
        curb_placements += [(x, 4, 0), (x, 8, 0)]

    curb_objs = []
    for i, (x, z, rot) in enumerate(curb_placements):
        objs = env.create_curb(c_edge, (x, -z, 0.0), rot, "MAP001_curb_%02d" % i,
                               lod=True)
        curb_objs += objs
        record("ENV002", "curb_%02d" % i, x, z, rot, collider={"type": "none"},
               source="art/full/source/environment/ENV002_curb.blend",
               note="map LOD; 0.18 m kerb, non-blocking", lod="1-seg bevel")
    curb_merged = join_meshes(curb_objs, "MAP001_curbs", c_edge)
    for inst in STATE["instances"]:
        if inst["asset_id"] == "ENV002":
            inst["merged_object"] = curb_merged.name

    # Edge closure: low wall north, railing east/west/south.
    wall_objs = []
    for i, x in enumerate((-12, -8, -4, 0, 4, 8, 12)):
        objs = env.create_low_wall(c_edge, (x, -9.7, 0), 0.0,
                                   "MAP001_low_wall_%02d" % i, lod=True)
        wall_objs += objs
        record("ENV003", "low_wall_%02d" % i, x, 9.7, 0.0,
               collider=box_collider(x, 9.7, 4.0, 0.5, 0.0, 0.79),
               source="art/full/source/environment/ENV003_low_wall.blend",
               note="north edge closure; map LOD", lod="1-seg bevel")
    wall_merged = join_meshes(wall_objs, "MAP001_north_wall", c_edge)
    for inst in STATE["instances"]:
        if inst["asset_id"] == "ENV003":
            inst["merged_object"] = wall_merged.name

    rail_objs = []
    rail_index = 0
    rail_specs = []
    for x in range(-13, 14, 2):
        rail_specs.append((x, -9.9, 0.0))
    for z in range(-9, 10, 2):
        rail_specs.append((13.9, z, 90.0))
        rail_specs.append((-13.9, z, 90.0))
    for (x, z, rot) in rail_specs:
        objs = env.create_railing(c_edge, (x, -z, 0), rot,
                                  "MAP001_railing_%02d" % rail_index, lod=True)
        rail_objs += objs
        record("ENV004", "railing_%02d" % rail_index, x, z, rot,
               collider=box_collider(x, z, 2.0, 0.10, rot, 1.12),
               source="art/full/source/environment/ENV004_railing.blend",
               note="map LOD: 5 balusters, 1-seg bevel", lod="5 balusters")
        rail_index += 1
    rail_merged = join_meshes(rail_objs, "MAP001_railings", c_edge)
    for inst in STATE["instances"]:
        if inst["asset_id"] == "ENV004":
            inst["merged_object"] = rail_merged.name

    # Decorative edge steps (landscape only, blocked).
    step_objs = env.create_steps(c_edge, (-4.6, 9.05, 0), 180.0,
                                 "MAP001_steps", lod=True)
    record("ENV005", "edge_steps", -4.6, -9.05, 180.0,
           collider=box_collider(-4.6, -9.05, 2.7, 1.4, 180.0, 0.49),
           source="art/full/source/environment/ENV005_steps.blend",
           note="landscape only at the south edge; no climbing", objects=step_objs)

    # Central ring planter + hero tree.
    planter_objs = env.create_ring_planter(c_env, (0, 0, 0), 0.0,
                                           "MAP001_ring_planter")
    record("ENV007", "ring_planter", 0, 0, 0.0,
           collider=circle_collider(0, 0, 2.08, 0.63),
           source="art/full/source/environment/ENV007_ring_planter.blend",
           objects=planter_objs, note="walkway outside r=2.08")
    add_proxy_circle(c_col, "COL_ring_planter", 0, 0, 2.08, 0.63)

    tree_objs = env.create_tree(c_env, (0, 0, 0.55), 0.0, "MAP001_tree")
    canopy = [o for o in tree_objs if o.name.endswith("_canopy")][0]
    occ_objs = [o.name for o in tree_objs
                if o.name.endswith("_canopy") or o.name.endswith("_crown_mass")]
    record("ENV006", "hero_tree", 0, 0, 0.0, y=0.55,
           collider=circle_collider(0, 0, 0.36, 1.4),
           occlusion_group="OCC_tree_main",
           source="art/full/source/environment/ENV006_autumn_tree.blend",
           objects=tree_objs,
           note="tree base sits just below planter soil top y=0.615; y=0.55; "
                "canopy object " + canopy.name + " + solid crown mass")
    STATE["occlusion"].append({
        "id": "OCC_tree_main",
        "objects": occ_objs,
        "rule": "hide canopy + crown mass when the player silhouette is behind it "
                "relative to the fixed camera; restore on exit",
        "note": "runtime occlusion is not implemented or engine-tested yet",
    })

    # Side planters + shrubs inside them.
    sp_objs = env.create_side_planter(c_env, (-11.8, -4.6, 0), 0.0,
                                      "MAP001_west_planter")
    record("ENV008", "west_planter", -11.8, 4.6, 0.0,
           collider=box_collider(-11.8, 4.6, 3.28, 1.48, 0.0, 0.48),
           source="art/full/source/environment/ENV008_side_planter.blend",
           objects=sp_objs)
    add_proxy_box(c_col, "COL_west_planter", -11.8, 4.6, 3.28, 1.48, 0.0, 0.48)

    sp2_objs = env.create_side_planter(c_env, (11.8, 4.8, 0), 90.0,
                                       "MAP001_east_planter")
    record("ENV008", "east_planter", 11.8, -4.8, 90.0,
           collider=box_collider(11.8, -4.8, 3.28, 1.48, 90.0, 0.48),
           source="art/full/source/environment/ENV008_side_planter.blend",
           objects=sp2_objs)
    add_proxy_box(c_col, "COL_east_planter", 11.8, -4.8, 3.28, 1.48, 90.0, 0.48)

    # Existing bench source, appended and placed.
    bench_objs = append_bench(c_props, -9.3, -4.4, 90.0)
    record("PROP001", "bench_A", -9.3, -4.4, 90.0,
           collider=box_collider(-9.3, -4.4, 1.7, 0.70, 90.0, 0.88),
           source="art/full/source/props/PROP001_bench.blend",
           objects=bench_objs, note="appended from existing PROP001 source")
    add_proxy_box(c_col, "COL_bench_A", -9.3, -4.4, 1.7, 0.70, 90.0, 0.88)
    bench_b = append_bench(c_props, -6.4, -5.0, 0.0)
    record("PROP001", "bench_B", -6.4, -5.0, 0.0,
           collider=box_collider(-6.4, -5.0, 1.7, 0.70, 0.0, 0.88),
           source="art/candidates/candidate_n3/source/props/PROP001_bench.blend",
           objects=bench_b, note="foreground bench, N01 depth")
    add_proxy_box(c_col, "COL_bench_B", -6.4, -5.0, 1.7, 0.70, 0.0, 0.88)
    bench_c = append_bench(c_props, 6.4, -5.0, 180.0)
    record("PROP001", "bench_C", 6.4, -5.0, 180.0,
           collider=box_collider(6.4, -5.0, 1.7, 0.70, 180.0, 0.88),
           source="art/candidates/candidate_n3/source/props/PROP001_bench.blend",
           objects=bench_c, note="foreground bench, N01 depth")
    add_proxy_box(c_col, "COL_bench_C", 6.4, -5.0, 1.7, 0.70, 180.0, 0.88)

    # Message board (engine z=+6.9 -> Blender y=-6.9).
    board_objs = props.create_message_board(c_props, (0, -6.9, 0), 180.0,
                                            "MAP001_message_board")
    board_meshes = [o for o in board_objs if o.type == "MESH"]
    record("PROP003", "message_board", 0, 6.9, 180.0,
           collider=box_collider(0, 6.9, 2.50, 0.32, 180.0, 1.98),
           interaction_id="board_submit",
           source="art/full/source/props/PROP003_message_board.blend",
           objects=board_objs)
    add_proxy_box(c_col, "COL_message_board", 0, 6.9, 2.50, 0.32, 180.0, 1.98)
    STATE["interactions"].append({
        "id": "board_submit", "type": "message_board",
        "position": [0, 0.95, 6.74], "interaction_position": [0, 0, 5.9],
        "radius": 1.6, "asset_id": "PROP003",
        "states": "cards A/B/C independently visible; empty and full supported",
    })

    # Pergola (engine z=+6.4 -> Blender y=-6.4).
    pergola_objs = props.create_pergola(c_props, (11.6, -6.4, 0), 0.0,
                                        "MAP001_pergola")
    post_shapes = []
    for (dx, dz) in ((1.45, 1.15), (1.45, -1.15),
                     (-1.45, 1.15), (-1.45, -1.15)):
        px, pz = 11.6 + dx, 6.4 + dz
        post_shapes.append(box_collider(px, pz, 0.22, 0.22, 0.0, 2.6))
    record("PROP002", "pergola", 11.6, 6.4, 0.0,
           collider={"type": "compound", "shapes": post_shapes},
           occlusion_group="OCC_pergola_roof",
           source="art/full/source/props/PROP002_pergola.blend",
           objects=pergola_objs,
           note="roof spans x 9.9-13.3 / z 5.3-7.9; card C at (8,5) is clear; "
                "collision is compound (4 posts)")
    for i, (dx, dz) in enumerate(((1.45, 1.15), (1.45, -1.15),
                                  (-1.45, 1.15), (-1.45, -1.15))):
        px, pz = 11.6 + dx, 6.4 + dz
        add_proxy_box(c_col, "COL_pergola_post_%d" % i, px, pz, 0.22, 0.22,
                      0.0, 2.6)
    roof = [o for o in pergola_objs if o.name.endswith("_roof")][0]
    state_occ = {
        "id": "OCC_pergola_roof",
        "objects": [roof.name],
        "rule": "optional roof hide when the player is behind the beam grid; "
                "not required for card C",
        "note": "runtime occlusion is not implemented or engine-tested yet",
    }
    STATE["occlusion"].append(state_occ)

    # Lamps.
    lamps = [(-6.8, -6.8), (6.8, -6.8), (-6.8, 6.8), (6.8, 6.8)]
    for i, (x, z) in enumerate(lamps):
        objs = props.create_lamp(c_props, (x, -z, 0), 0.0,
                                 "MAP001_lamp_%d" % i)
        record("PROP004", "lamp_%d" % i, x, z, 0.0,
               collider=circle_collider(x, z, 0.30, 2.67),
               source="art/full/source/props/PROP004_lamp.blend", objects=objs)
        add_proxy_circle(c_col, "COL_lamp_%d" % i, x, z, 0.30, 2.67)

    # Direction sign (engine z=-7.5 -> Blender y=+7.5).
    sign_objs = props.create_direction_sign(c_props, (-3.4, 7.5, 0), 180.0,
                                            "MAP001_direction_sign")
    record("PROP005", "direction_sign", -3.4, -7.5, 180.0,
           collider=circle_collider(-3.4, -7.5, 0.28, 2.1),
           source="art/full/source/props/PROP005_direction_sign.blend",
           objects=sign_objs)
    add_proxy_circle(c_col, "COL_direction_sign", -3.4, -7.5, 0.28, 2.1)

    # Pickup postcards at A/B/C, 0.15 above the paving.
    pickups = [("A", -7.0, -3.0), ("B", -8.0, 4.0), ("C", 8.0, 5.0)]
    for (design, x, z) in pickups:
        card = pc.create_postcard(c_props, design, "MAP001_pickup_%s" % design,
                                  scale=1.75, pins=False)
        card.location = (x, -z, 0.15)
        card.rotation_euler = (0, 0, math.radians(180.0))
        record("PROP006", "pickup_%s" % design, x, z, 180.0, y=0.15,
               collider={"type": "none"}, interaction_id="pickup_" + design,
               source="art/full/source/props/PROP006_postcards.blend",
               objects=[card], note="card front faces south; floats at y=0.15")
        STATE["interactions"].append({
            "id": "pickup_" + design, "type": "pickup", "card_design": design,
            "position": [x, 0.15, z], "radius": 1.6, "asset_id": "PROP006",
            "collected_state": "hidden after pickup; shown by board card node",
        })

    STATE["interactions"].append({
        "id": "npc_gardener", "type": "npc", "position": [3.0, 0.0, -5.0],
        "radius": 1.6, "asset_id": None,
        "status": "character asset pending; no stand-in character placed",
    })

    # Shrubs / dry grass / fallen leaves (planting and edge softening).
    shrub_specs = [
        ("ENV009", -12.4, -6.2, 15.0, 0.85), ("ENV010", -12.3, 1.0, -20.0, 1.10),
        ("ENV009", -12.5, 8.4, 40.0, 0.95), ("ENV010", 12.4, 0.2, 160.0, 1.15),
        ("ENV009", 6.4, 9.0, 80.0, 1.00), ("ENV010", -5.8, 9.0, -60.0, 0.90),
        ("ENV009", 12.6, -7.3, 200.0, 1.05), ("ENV010", 4.2, 9.2, 115.0, 0.85),
    ]
    for i, (asset, x, z, rot, scale) in enumerate(shrub_specs):
        builder = env.create_shrub_a if asset == "ENV009" else env.create_shrub_b
        objs = builder(c_plants, (x, -z, 0.0), rot, "MAP001_%s_%02d" % (
            asset.lower(), i))
        if scale != 1.0:
            for o in objs:
                o.scale = (scale, scale, scale)
        radius = (0.46 if asset == "ENV009" else 0.60) * scale
        record(asset, "shrub_%02d" % i, x, z, rot, scale=scale,
               collider=circle_collider(x, z, radius, 1.1 * scale),
               occlusion_group="OCC_shrub_%02d" % i,
               source="art/full/source/plants/%s.blend" % (
                   "ENV009_shrub_a" if asset == "ENV009" else "ENV010_shrub_b"),
               objects=objs)
        add_proxy_circle(c_col, "COL_shrub_%02d" % i, x, z, radius, 1.1 * scale)
        leaves = [o for o in objs if o.name.endswith("_leaves")]
        STATE["occlusion"].append({
            "id": "OCC_shrub_%02d" % i,
            "objects": [o.name for o in leaves],
            "rule": "optional per-shrub hide if it covers the player; not runtime-tested",
        })

    # Layered planter planting: two shrubs + grass tufts + leaf litter per
    # side planter, so the soil bed reads full instead of bare.
    planter_plantings = [
        # west planter (long axis along x): soil x -13.0..-10.6, z 4.07..5.13
        [("ENV009", -12.50, 4.75, 15.0, 0.90), ("ENV010", -11.15, 4.40, -20.0, 0.85),
         ("ENV011", -11.85, 5.00, 30.0, 1.00), ("ENV011", -12.35, 4.20, 80.0, 1.00),
         ("ENV012", -11.80, 4.55, 10.0, 1.00)],
        # east planter (rot 90, long axis along z): soil x 11.21..12.39, z -6.0..-3.6
        [("ENV010", 11.75, -5.50, 100.0, 0.90), ("ENV009", 11.90, -4.10, 65.0, 0.85),
         ("ENV011", 11.45, -4.85, 140.0, 1.00), ("ENV011", 12.15, -5.90, 200.0, 1.00),
         ("ENV012", 11.80, -4.80, 70.0, 1.00)],
    ]
    for pi, planting in enumerate(planter_plantings):
        for si, (asset, x, z, rot, scale) in enumerate(planting):
            y = 0.40
            if asset == "ENV009":
                objs = env.create_shrub_a(c_plants, (x, -z, y), rot,
                                          "MAP001_planter_%02d_shrub_a" % pi)
            elif asset == "ENV010":
                objs = env.create_shrub_b(c_plants, (x, -z, y), rot,
                                          "MAP001_planter_%02d_shrub_b" % pi)
            elif asset == "ENV011":
                objs = env.create_dry_grass(c_plants, (x, -z, y), rot,
                                            "MAP001_planter_%02d_grass_%d" % (pi, si))
            else:
                y = 0.42
                objs = env.create_fallen_leaves(c_plants, (x, -z, y), rot,
                                                "MAP001_planter_%02d_litter_%d" % (pi, si))
            if scale != 1.0:
                for o in objs:
                    o.scale = (scale, scale, scale)
            record(asset, "planter_plant_%02d_%02d" % (pi, si), x, z, rot, y=y,
                   scale=scale, collider={"type": "none"},
                   source="art/full/source/plants/ENV011_dry_grass.blend"
                   if asset == "ENV011" else
                   "art/full/source/plants/ENV012_fallen_leaves.blend"
                   if asset == "ENV012" else
                   "art/full/source/plants/%s.blend" % (
                       "ENV009_shrub_a" if asset == "ENV009" else "ENV010_shrub_b"),
                   objects=objs,
                   note="inside side planter; planter collider covers it")

    # Dry grass and fallen leaf clusters: soil margins, fence lines and the
    # central ring, with varied scales so the beds stop reading as bare ground.
    grass_specs = [(-13.2, -7.6, 20.0, 1.20), (-13.3, -2.4, 80.0, 1.10),
                   (-13.1, 2.8, 140.0, 1.30), (-13.2, 7.2, 15.0, 1.15),
                   (13.2, -7.4, -30.0, 1.25), (13.3, -2.0, 60.0, 1.10),
                   (13.1, 3.2, 200.0, 1.20), (13.2, 7.4, 100.0, 1.15),
                   (-8.6, 9.1, 10.0, 1.10), (0.4, 9.2, 120.0, 1.25),
                   (8.6, 9.1, -70.0, 1.15), (-8.4, -9.0, 40.0, 1.10),
                   (0.6, -9.0, 160.0, 1.20), (8.4, -9.0, -15.0, 1.10),
                   (-11.9, 2.0, 30.0, 1.00), (11.0, 8.4, 120.0, 1.00),
                   (-3.7, 9.0, -20.0, 1.00), (6.0, -9.0, 75.0, 1.00),
                   (-10.6, -8.6, 10.0, 1.00), (10.8, 6.9, 200.0, 1.00)]
    for i, (x, z, rot, scale) in enumerate(grass_specs):
        objs = env.create_dry_grass(c_plants, (x, -z, 0.0), rot,
                                    "MAP001_dry_grass_%02d" % i)
        if scale != 1.0:
            for o in objs:
                o.scale = (scale, scale, scale)
        record("ENV011", "dry_grass_%02d" % i, x, z, rot, scale=scale,
               collider={"type": "none"},
               source="art/full/source/plants/ENV011_dry_grass.blend",
               objects=objs)
    leaf_specs = [(0.4, 2.3, 10.0, 1.20), (2.4, 0.2, 70.0, 1.00),
                  (-2.2, -1.0, 140.0, 1.10), (-8.3, -3.2, -30.0, 1.20),
                  (-13.0, 0.5, 20.0, 1.30), (12.9, 3.0, 80.0, 1.20),
                  (-6.5, 8.7, 10.0, 1.10), (6.5, 8.7, 60.0, 1.15),
                  (-11.8, 4.6, 30.0, 1.10), (11.8, -5.0, 90.0, 1.10)]
    for i, (x, z, rot, scale) in enumerate(leaf_specs):
        objs = env.create_fallen_leaves(c_plants, (x, -z, 0.0), rot,
                                        "MAP001_fallen_leaves_%02d" % i)
        if scale != 1.0:
            for o in objs:
                o.scale = (scale, scale, scale)
        record("ENV012", "fallen_leaves_%02d" % i, x, z, rot, scale=scale,
               collider={"type": "none"},
               source="art/full/source/plants/ENV012_fallen_leaves.blend",
               objects=objs)
    ring_cover = [("ENV012", 0.90, 0.60, 10.0, 0.80),
                  ("ENV012", -0.80, 0.80, 70.0, 0.70),
                  ("ENV012", 0.20, -1.10, 130.0, 0.75),
                  ("ENV011", -0.55, -0.90, 40.0, 0.70)]
    for i, (asset, x, z, rot, scale) in enumerate(ring_cover):
        builder = env.create_dry_grass if asset == "ENV011" else env.create_fallen_leaves
        objs = builder(c_plants, (x, -z, 0.63), rot,
                       "MAP001_ring_cover_%02d" % i)
        for o in objs:
            o.scale = (scale, scale, scale)
        record(asset, "ring_cover_%02d" % i, x, z, rot, y=0.63, scale=scale,
               collider={"type": "none"},
               source="art/full/source/plants/ENV011_dry_grass.blend"
               if asset == "ENV011" else
               "art/full/source/plants/ENV012_fallen_leaves.blend",
               objects=objs,
               note="inside central ring planter; planter collider covers it")

    # Edge beds visible in the formal camera: break up the remaining bare soil.
    extra_cover = [("ENV011", -6.8, 5.8, 20.0, 1.10),
                   ("ENV011", -8.5, 4.5, 70.0, 1.20),
                   ("ENV011", -10.5, 6.5, 140.0, 1.00),
                   ("ENV012", -7.3, 6.9, 10.0, 1.20),
                   ("ENV011", 6.8, 5.8, 40.0, 1.15),
                   ("ENV012", 9.5, 3.5, 90.0, 1.10),
                   ("ENV011", -9.5, -1.5, 160.0, 1.20),
                   ("ENV012", 9.5, -2.5, 30.0, 1.15),
                   ("ENV011", -11.0, -8.8, 20.0, 1.35),
                   ("ENV011", -4.0, -8.8, 90.0, 1.25),
                   ("ENV011", 4.0, -8.8, 150.0, 1.30),
                   ("ENV011", 11.0, -8.8, 210.0, 1.30),
                   ("ENV012", -7.0, -8.8, 40.0, 1.15),
                   ("ENV012", 7.0, -8.8, 120.0, 1.20),
                   ("ENV011", -12.8, 3.8, 75.0, 1.20),
                   ("ENV011", 12.8, -1.2, 175.0, 1.20),
                   ("ENV012", -6.0, 9.3, 10.0, 1.10),
                   ("ENV012", 6.0, 9.3, 80.0, 1.10)]
    for i, (asset, x, z, rot, scale) in enumerate(extra_cover):
        builder = env.create_dry_grass if asset == "ENV011" else env.create_fallen_leaves
        objs = builder(c_plants, (x, -z, 0.0), rot,
                       "MAP001_edge_cover_%02d" % i)
        for o in objs:
            o.scale = (scale, scale, scale)
        record(asset, "edge_cover_%02d" % i, x, z, rot, scale=scale,
               collider={"type": "none"},
               source="art/full/source/plants/ENV011_dry_grass.blend"
               if asset == "ENV011" else
               "art/full/source/plants/ENV012_fallen_leaves.blend",
               objects=objs)

    # Path / clearance metadata.
    STATE["paths"] = [
        {"id": "central_plaza", "rect_x": [-6, 6], "rect_z": [-6, 6],
         "width_min": 4.0, "note": "ring around planter leaves 4.0 m clear"},
        {"id": "south_approach", "rect_x": [-2, 2], "rect_z": [-10, -6],
         "width_min": 4.0},
        {"id": "north_approach", "rect_x": [-2, 2], "rect_z": [6, 10],
         "width_min": 4.0},
        {"id": "west_approach", "rect_x": [-10, -6], "rect_z": [-6, 6],
         "width_min": 4.0},
        {"id": "east_approach", "rect_x": [6, 10], "rect_z": [2, 6],
         "width_min": 4.0},
        {"id": "pergola_pad", "rect_x": [10, 14], "rect_z": [4, 8],
         "width_min": 3.0},
    ]

    # Clearance checks required by the brief.
    checks = clearance_report([
        ("spawn_south", 0.0, -8.0, 1.0),
        ("pickup_A", -7.0, -3.0, 1.5),
        ("pickup_B", -8.0, 4.0, 1.5),
        ("pickup_C", 8.0, 5.0, 1.5),
        ("npc_gardener", 3.0, -5.0, 0.8),
        ("board_stand", 0.0, 5.9, 0.8),
        ("pergola_card_gap", 8.0, 5.0, 1.5),
    ])
    STATE["validation"] = checks

    # Fixed demo camera and light rig (saved with the layout for inspection).
    cam = cl.setup_demo_camera(target=(0, 0, 0.80), distance=33.0, fov_deg=35.0,
                               resolution=(1500, 950), samples=72)
    cam.name = "CAM_map001"
    cam["map_id"] = "MAP001"
    cam["elevation_deg"] = 45.0
    cam["vertical_fov_deg"] = 35.0
    cam["view_from"] = "engine south (+Z), facing north"
    scene.view_settings.exposure = -0.30
    for obj in scene.objects:
        if obj.type == "LIGHT":
            obj["map_id"] = "MAP001"

    # Triangle / object facts before save.
    export_meshes = [o for o in scene.objects
                     if o.type == "MESH" and not o.name.startswith("COL_")]
    text_objects = [o for o in scene.objects if o.type == "FONT"]
    total_tris = sum(cl.object_triangles(o) for o in export_meshes)
    total_verts = sum(len(o.data.vertices) for o in export_meshes)
    print("MAP001 objects=%d meshes=%d text=%d tris=%d verts=%d" % (
        len(scene.objects), len(export_meshes), len(text_objects), total_tris,
        total_verts))

    # World-space box UVs so engine material textures keep uniform texel
    # density (V02); wood objects project grain along their long axis.
    wood_names = {"MAT_wood_old", "MAT_wood_dark", "MAT_wood_pale",
                  "MAT_bench_wood"}
    for o in export_meshes:
        names = {m.name for m in o.data.materials if m}
        cl.bake_box_uvs(o, density=1.0, grain=bool(names & wood_names))
    print("MAP001 UVs baked: %d meshes" % len(export_meshes))

    cl.save_blend(BLEND)
    cl.export_glb([o for o in scene.objects if o.type in ("MESH", "FONT")
                   and not o.name.startswith("COL_")], GLB)
    cl.render_to(PNG)

    # Top-down diagnostic view (preview only; not saved as a map camera).
    top_cam_data = bpy.data.cameras.new("MAP001_top_camera")
    top_cam_data.type = "ORTHO"
    top_cam_data.ortho_scale = 30.0
    top_cam = bpy.data.objects.new("MAP001_top_camera", top_cam_data)
    c_light.objects.link(top_cam)
    top_cam.location = (0, 0, 30.0)
    top_cam.rotation_euler = (0, 0, math.pi)
    scene.camera = top_cam
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 860
    scene.cycles.samples = 32
    cl.render_to(PNG_TOP)

    # Restore main camera for the saved file?  The .blend was already saved with
    # the demo camera; this in-memory change is not saved.
    scene.camera = cam

    # Layout JSON.
    payload = {
        "schema": "courtyard_layout/1",
        "map_id": "MAP001",
        "name": "秋庭完整布局",
        "generated_by": "tools/blender/build_map001.py",
        "units": "1 Blender unit = 1 world unit",
        "coordinate_system": {
            "engine": "Y up, ground XZ, centre (0,0,0)",
            "bounds_x": [-14, 14], "bounds_z": [-10, 10],
            "blender_to_engine": "engine = (x, z, -y); engine yaw = Blender Z rotation",
            "module_front": "-Y Blender / +Z engine before layout rotation",
            "ground_top_y": 0.0,
            "soil_top_y": SOIL_TOP,
            "paving_note": "ENV001 modules sunk by 0.14 so their top is y=0",
        },
        "look": {
            "profile": "art/full/source/layout/LOOK001_look_profile.json",
            "camera": "45 deg elevation, vertical FOV 35, from south",
            "renderer": "Cycles CPU preview; not Cocos/WeChat evidence",
        },
        "ground": STATE["ground"],
        "instances": STATE["instances"],
        "interactions": STATE["interactions"],
        "occlusion_groups": STATE["occlusion"],
        "collision_proxies": STATE["proxies"],
        "paths": STATE["paths"],
        "clearances": STATE["validation"],
        "stats": {
            "instances": len(STATE["instances"]),
            "mesh_objects": len(export_meshes),
            "text_objects": len(text_objects),
            "triangles": total_tris,
            "vertices": total_verts,
            "materials": sorted({m.name for o in export_meshes
                                 for m in o.data.materials if m}),
        },
        "missing": [
            "NPC gardener character (no stand-in placed; character work pending)",
            "engine-ready baked textures/UVs for all procedural materials",
            "Cocos/WeChat import, Y-up axis check and engine screenshots",
            "runtime occlusion/collision logic (layout data only)",
            "background buildings beyond the wall/railing edge closure",
        ],
    }
    cl.write_json(LAYOUT, payload)
    print("LAYOUT_INSTANCES=%d PROXIES=%d" % (
        len(STATE["instances"]), len(STATE["proxies"])))


if __name__ == "__main__":
    build()
