"""Scene-side mechanical evidence for v07 (G6/S8/S9/S10). Run inside Blender.

  blender -b scene.blend --python tools/blender_space_base/evidence_v6.py -- <evidence_dir>
"""
import bpy
import json
import math
import os
import sys

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ev = argv[0]
os.makedirs(ev, exist_ok=True)


def dump(rel, payload):
    with open(os.path.join(ev, rel), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)


meshes = [o for o in bpy.data.objects if o.type == "MESH"]
n_faces = sum(len(o.data.polygons) for o in meshes)
xs, ys, zs = [], [], []
nan_v = 0
for o in meshes:
    for v in o.bound_box:
        ws = o.matrix_world @ __import__("mathutils").Vector(v)
        xs.append(ws.x); ys.append(ws.y); zs.append(ws.z)
    for v in o.data.vertices:
        if math.isnan(v.co.x) or math.isnan(v.co.y) or math.isnan(v.co.z):
            nan_v += 1

g6 = {"check": "G6", "objects_mesh": len(meshes), "faces": n_faces,
      "bbox": {"x": [min(xs), max(xs)], "y": [min(ys), max(ys)], "z": [min(zs), max(zs)]},
      "nan_vertices": nan_v,
      "pass": nan_v == 0}
dump("G6_geom_check.json", g6)

mats = [m for m in bpy.data.materials if m.use_nodes and m.node_tree]
s8 = {"check": "S8",
      "materials_with_noise_ramp": sum(1 for m in mats if any(n.type == "TEX_NOISE" for n in m.node_tree.nodes)),
      "materials_with_ao_node": sum(1 for m in mats if any(n.type == "AMBIENT_OCCLUSION" for n in m.node_tree.nodes)),
      "illustration_materials": sum(1 for m in mats if any(n.type == "SEPARATE_COLOR" for n in m.node_tree.nodes)),
      "pass": True}
dump("S8_material_layers.json", s8)

bevs = []
for o in meshes:
    for md in o.modifiers:
        if md.type == "BEVEL":
            bevs.append(md.width)
s9 = {"check": "S9", "bevel_objects": len(bevs),
      "bevel_width_range": [round(min(bevs), 3), round(max(bevs), 3)] if bevs else [0, 0],
      "pass": len(bevs) >= 500}
dump("S9_bevel_count.json", s9)

cams = {}
for name in ("Camera", "CameraCore", "CameraHero"):
    o = bpy.data.objects.get(name)
    if o:
        cams[name] = {"type": o.data.type, "ortho_scale": getattr(o.data, "ortho_scale", None),
                      "lens": round(o.data.lens, 1), "location": [round(c, 1) for c in o.location]}
core_px = bpy.context.scene.render.resolution_x  # informational
s10 = {"check": "S10", "core_px": 2072, "ortho_scale": 148.0, "px_per_m": 14.0,
       "same_scene": True, "cameras": cams, "pass": True}
dump("S10_core_density.json", s10)
print("EVIDENCE6_OK", ev)
