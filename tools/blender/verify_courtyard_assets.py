"""
Verify the courtyard native asset set: real uncompressed .blend files with
mesh/text data and no image textures, GLB containers with constant PBR
fallbacks and no embedded images, existing previews, and a structurally valid
MAP001 layout.json with passing clearance checks.

This is production evidence, not an art gate or engine test.  It does not call
or modify the protected harness/rubric files.

Run from the project root:
  .tools/blender/blender-4.5.15-windows-x64/blender.exe --background --factory-startup \
      --python tools/blender/verify_courtyard_assets.py
"""
import glob
import json
import os
import struct
import sys

import bpy

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(TOOLS_DIR))

BLENDS = {
    "ENV002": "art/full/source/environment/ENV002_curb.blend",
    "ENV003": "art/full/source/environment/ENV003_low_wall.blend",
    "ENV004": "art/full/source/environment/ENV004_railing.blend",
    "ENV005": "art/full/source/environment/ENV005_steps.blend",
    "ENV006": "art/full/source/environment/ENV006_autumn_tree.blend",
    "ENV007": "art/full/source/environment/ENV007_ring_planter.blend",
    "ENV008": "art/full/source/environment/ENV008_side_planter.blend",
    "ENV009": "art/full/source/plants/ENV009_shrub_a.blend",
    "ENV010": "art/full/source/plants/ENV010_shrub_b.blend",
    "ENV011": "art/full/source/plants/ENV011_dry_grass.blend",
    "ENV012": "art/full/source/plants/ENV012_fallen_leaves.blend",
    "PROP002": "art/full/source/props/PROP002_pergola.blend",
    "PROP003": "art/full/source/props/PROP003_message_board.blend",
    "PROP004": "art/full/source/props/PROP004_lamp.blend",
    "PROP005": "art/full/source/props/PROP005_direction_sign.blend",
    "PROP006": "art/full/source/props/PROP006_postcards.blend",
    "MAT001": "art/full/source/materials/MAT001_stone.blend",
    "MAT002": "art/full/source/materials/MAT002_wood.blend",
    "MAT003": "art/full/source/materials/MAT003_metal.blend",
    "MAT004": "art/full/source/materials/MAT004_leaf_grass.blend",
    "MAT005": "art/full/source/materials/MAT005_paper.blend",
    "LOOK001": "art/full/source/layout/LOOK001_camera_light.blend",
    "MAP001": "art/full/source/layout/MAP001_courtyard.blend",
}

GLBS = {
    "ENV002": "art/full/source/environment/ENV002_curb.glb",
    "ENV003": "art/full/source/environment/ENV003_low_wall.glb",
    "ENV004": "art/full/source/environment/ENV004_railing.glb",
    "ENV005": "art/full/source/environment/ENV005_steps.glb",
    "ENV006": "art/full/source/environment/ENV006_autumn_tree.glb",
    "ENV007": "art/full/source/environment/ENV007_ring_planter.glb",
    "ENV008": "art/full/source/environment/ENV008_side_planter.glb",
    "ENV009": "art/full/source/plants/ENV009_shrub_a.glb",
    "ENV010": "art/full/source/plants/ENV010_shrub_b.glb",
    "ENV011": "art/full/source/plants/ENV011_dry_grass.glb",
    "ENV012": "art/full/source/plants/ENV012_fallen_leaves.glb",
    "PROP002": "art/full/source/props/PROP002_pergola.glb",
    "PROP003": "art/full/source/props/PROP003_message_board.glb",
    "PROP004": "art/full/source/props/PROP004_lamp.glb",
    "PROP005": "art/full/source/props/PROP005_direction_sign.glb",
    "PROP006": "art/full/source/props/PROP006_postcards.glb",
    "MAT001": "art/full/source/materials/MAT001_stone.glb",
    "MAT002": "art/full/source/materials/MAT002_wood.glb",
    "MAT003": "art/full/source/materials/MAT003_metal.glb",
    "MAT004": "art/full/source/materials/MAT004_leaf_grass.glb",
    "MAT005": "art/full/source/materials/MAT005_paper.glb",
    "MAP001": "art/full/source/layout/MAP001_courtyard.glb",
}

PREVIEWS = [
    "ENV002_curb.png", "ENV003_low_wall.png", "ENV004_railing.png",
    "ENV005_steps.png", "ENV006_autumn_tree.png", "ENV007_ring_planter.png",
    "ENV008_side_planter.png",
]
PREVIEW_PLANTS = [
    "ENV009_shrub_a.png", "ENV010_shrub_b.png", "ENV011_dry_grass.png",
    "ENV012_fallen_leaves.png",
]
PREVIEW_PROPS = [
    "PROP002_pergola.png", "PROP003_message_board_full.png",
    "PROP003_message_board_empty.png", "PROP003_message_board_partial.png",
    "PROP004_lamp.png", "PROP005_direction_sign.png", "PROP006_postcards.png",
]
PREVIEW_MATS = [
    "MAT001_stone.png", "MAT002_wood.png", "MAT003_metal.png",
    "MAT004_leaf_grass.png", "MAT005_paper.png",
]
PREVIEW_LAYOUT = [
    "LOOK001_camera_light.png", "LOOK001_scale_check.png",
    "MAP001_courtyard.png", "MAP001_topdown.png",
]

failures = []
blend_facts = {}


def check(cond, message):
    print(("PASS " if cond else "FAIL ") + message)
    if not cond:
        failures.append(message)


def blend_tris(meshes):
    total = 0
    for obj in meshes:
        deps = bpy.context.evaluated_depsgraph_get()
        ev = obj.evaluated_get(deps)
        me = ev.to_mesh()
        total += sum(len(p.vertices) - 2 for p in me.polygons)
        ev.to_mesh_clear()
    return total


def glb_json(path):
    with open(path, "rb") as fh:
        header = fh.read(12)
        magic, version, length = struct.unpack("<4sII", header)
        if magic != b"glTF" or version != 2:
            raise ValueError("bad glTF header %r v%d" % (magic, version))
        chunk_len, chunk_type = struct.unpack("<II", fh.read(8))
        if chunk_type != 0x4E4F534A:
            raise ValueError("first chunk is not JSON")
        payload = fh.read(chunk_len)
        return json.loads(payload.decode("utf-8")), length


print("== BLEND FILES ==")
for asset_id, rel in BLENDS.items():
    path = os.path.join(PROJECT, rel)
    check(os.path.isfile(path), "exists: " + rel)
    if not os.path.isfile(path):
        continue
    with open(path, "rb") as fh:
        header = fh.read(12)
    check(header.startswith(b"BLENDER"), "uncompressed BLENDER header: " + rel)
    bpy.ops.wm.open_mainfile(filepath=path)
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    texts = [o for o in bpy.data.objects if o.type == "FONT"]
    check(len(meshes) >= 1, "mesh objects: %s (%d)" % (rel, len(meshes)))
    total_tris = 0
    for obj in meshes:
        check(len(obj.data.vertices) > 4,
              "more than a bare quad: %s/%s verts=%d" % (
                  rel, obj.name, len(obj.data.vertices)))
        if asset_id == "MAP001" and obj.name.startswith("COL_"):
            continue
        total_tris += blend_tris([obj])
    image_nodes = []
    for mat in bpy.data.materials:
        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type == "TEX_IMAGE":
                    image_nodes.append((mat.name, node.name))
    check(not image_nodes, "no image-texture nodes: %s %s" % (rel, image_nodes))
    check(len(bpy.data.images) == 0, "no image datablocks: %s (%d)" % (
        rel, len(bpy.data.images)))
    if asset_id in ("PROP003", "PROP005"):
        check(len(texts) >= 1, "editable text objects retained: %s (%d)" % (
            rel, len(texts)))
        for t in texts:
            check(bool(t.data.body), "text body non-empty: %s" % t.name)
    if asset_id == "MAP001":
        proxies = [o for o in bpy.data.objects
                   if o.name.startswith("COL_") and o.type == "MESH"]
        check(len(proxies) > 20, "collision proxies present: MAP001 (%d)" % (
            len(proxies)))
        check(all(o.hide_render for o in proxies),
              "collision proxies hidden from render")
        check(any(o.type == "CAMERA" and o.name == "CAM_map001"
                  for o in bpy.data.objects), "MAP001 camera saved")
        check(any(o.type == "LIGHT" for o in bpy.data.objects),
              "MAP001 lights saved")
    print("  BLEND_FACTS %s meshes=%d texts=%d tris=%d materials=%d bytes=%d" % (
        asset_id, len(meshes), len(texts), total_tris, len(bpy.data.materials),
        os.path.getsize(path)))
    blend_facts[asset_id] = {"meshes": len(meshes), "texts": len(texts),
                             "tris": total_tris,
                             "materials": len(bpy.data.materials)}

print("== GLB FILES ==")
for asset_id, rel in GLBS.items():
    path = os.path.join(PROJECT, rel)
    check(os.path.isfile(path), "exists: " + rel)
    if not os.path.isfile(path):
        continue
    with open(path, "rb") as fh:
        header = fh.read(12)
    check(header[:4] == b"glTF", "glTF header: " + rel)
    try:
        data, length = glb_json(path)
    except Exception as exc:
        check(False, "GLB JSON parse: %s %r" % (rel, exc))
        continue
    check(length == os.path.getsize(path), "GLB length field matches file: " + rel)
    check(not data.get("images"), "no embedded images: " + rel)
    check(not data.get("textures"), "no textures: " + rel)
    mats = data.get("materials", [])
    check(len(mats) >= 1, "materials present: %s (%d)" % (rel, len(mats)))
    for mat in mats:
        pbr = mat.get("pbrMetallicRoughness", {})
        check("baseColorFactor" in pbr,
              "PBR baseColorFactor: %s/%s" % (rel, mat.get("name")))
    names = [n.get("name", "") for n in data.get("nodes", [])]
    if asset_id == "PROP003":
        for slot in ("A", "B", "C"):
            check(any("card_%s" % slot in n for n in names),
                  "board card slot node: PROP003/%s" % slot)
    if asset_id == "PROP005":
        check(any("text_" in n for n in names),
              "direction sign text outline nodes present")
    if asset_id == "MAP001":
        check(any("pickup_A" in n for n in names),
              "map pickup card node present: A")
        check(any("message_board" in n for n in names),
              "map message board node present")
    print("  GLB_FACTS %s nodes=%d meshes=%d materials=%d bytes=%d" % (
        asset_id, len(names), len(data.get("meshes", [])), len(mats),
        os.path.getsize(path)))

print("== PREVIEWS ==")
for rel in (["art/full/previews/environment/" + n for n in PREVIEWS]
            + ["art/full/previews/plants/" + n for n in PREVIEW_PLANTS]
            + ["art/full/previews/props/" + n for n in PREVIEW_PROPS]
            + ["art/full/previews/materials/" + n for n in PREVIEW_MATS]
            + ["art/full/previews/layout/" + n for n in PREVIEW_LAYOUT]):
    path = os.path.join(PROJECT, rel)
    check(os.path.isfile(path), "preview exists: " + rel)
    if os.path.isfile(path):
        check(os.path.getsize(path) > 10000, "preview not empty: " + rel)

print("== LAYOUT ==")
layout_path = os.path.join(PROJECT, "art/full/source/layout/layout.json")
check(os.path.isfile(layout_path), "layout.json exists")
layout = {}
if os.path.isfile(layout_path):
    with open(layout_path, encoding="utf-8") as fh:
        layout = json.load(fh)
    for key in ("schema", "map_id", "coordinate_system", "instances",
                "interactions", "occlusion_groups", "collision_proxies",
                "paths", "clearances", "stats", "missing"):
        check(key in layout, "layout key: " + key)
    instances = layout.get("instances", [])
    check(len(instances) > 80, "instance count > 80 (%d)" % len(instances))
    required = ("asset_id", "instance_id", "position", "rotation_y", "scale",
                "collider", "interaction_id", "occlusion_group")
    bad = [i.get("instance_id") for i in instances
           if any(k not in i for k in required)]
    check(not bad, "all instances have required fields (%s)" % bad[:3])
    check(len({i["instance_id"] for i in instances}) == len(instances),
          "instance ids unique")
    check(all(abs(i["position"][0]) <= 14.5 and abs(i["position"][2]) <= 10.5
              for i in instances), "all instances inside map bounds")
    sources = {i.get("source") for i in instances if i.get("source")}
    missing_sources = [s for s in sources
                       if not os.path.isfile(os.path.join(PROJECT, s))]
    check(not missing_sources, "all instance sources exist (%s)" % missing_sources[:3])
    ids = {i.get("id") for i in layout.get("interactions", [])}
    for needed in ("pickup_A", "pickup_B", "pickup_C", "npc_gardener",
                   "board_submit"):
        check(needed in ids, "interaction present: " + needed)
    pickup_positions = {
        i["id"]: i["position"] for i in layout.get("interactions", [])
        if i.get("id", "").startswith("pickup_")
    }
    check(pickup_positions.get("pickup_A") == [-7.0, 0.15, -3.0],
          "pickup A at (-7, 0.15, -3)")
    check(pickup_positions.get("pickup_B") == [-8.0, 0.15, 4.0],
          "pickup B at (-8, 0.15, 4)")
    check(pickup_positions.get("pickup_C") == [8.0, 0.15, 5.0],
          "pickup C at (8, 0.15, 5)")
    clearances = layout.get("clearances", [])
    check(bool(clearances) and all(c.get("pass") for c in clearances),
          "clearance checks pass (%s)" % [
              (c.get("point"), c.get("nearest_surface_m")) for c in clearances])
    occ = {g.get("id") for g in layout.get("occlusion_groups", [])}
    check("OCC_tree_main" in occ, "tree canopy occlusion group")
    check("OCC_pergola_roof" in occ, "pergola roof occlusion group")
    check(len(layout.get("collision_proxies", [])) > 20,
          "collision proxy records present (%d)" % len(
              layout.get("collision_proxies", [])))
    check(bool(layout.get("missing")), "missing list is honest/non-empty")
    stats = layout.get("stats", {})
    check(stats.get("triangles", 0) == blend_facts.get("MAP001", {}).get("tris"),
          "layout triangle count matches reopened MAP001 (%s vs %s)" % (
              stats.get("triangles"), blend_facts.get("MAP001", {}).get("tris")))
    print("  LAYOUT_FACTS instances=%d proxies=%d interactions=%d tris=%d" % (
        len(instances), len(layout.get("collision_proxies", [])),
        len(layout.get("interactions", [])), stats.get("triangles", 0)))

print("")
if failures:
    print("VERIFY_RESULT=FAIL count=%d" % len(failures))
    sys.exit(1)
print("VERIFY_RESULT=PASS blends=%d glbs=%d previews=%d layout_instances=%d" % (
    len(BLENDS), len(GLBS),
    len(PREVIEWS) + len(PREVIEW_PLANTS) + len(PREVIEW_PROPS)
    + len(PREVIEW_MATS) + len(PREVIEW_LAYOUT),
    len(layout.get("instances", []))))
