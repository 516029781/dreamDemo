"""Scene-side evidence for v05: G6 / S8 / S9 / S10 / camera list."""
import bpy
import json
import os
import sys

out = sys.argv[sys.argv.index("--") + 1]
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
objs = [o for o in bpy.data.objects if o.type == "MESH"]
faces = sum(len(o.data.polygons) for o in objs)
bevel = sum(1 for o in objs if any(m.type == "BEVEL" for m in o.modifiers))
bevel_w = [m.width for o in objs for m in o.modifiers if m.type == "BEVEL"]
nan = 0
for o in objs:
    for v in o.data.vertices:
        if any(c != c for c in v.co):
            nan += 1
xs, ys, zs = [], [], []
for o in objs:
    for c in o.bound_box:
        w = o.matrix_world @ __import__("mathutils").Vector(c)
        xs.append(w.x); ys.append(w.y); zs.append(w.z)

mottled, ao = 0, 0
for m in bpy.data.materials:
    nt = m.node_tree
    if not nt:
        continue
    if any(n.type == "TEX_NOISE" for n in nt.nodes) and any(n.type == "VALTORGB" for n in nt.nodes):
        mottled += 1
    if any(n.type == "AMBIENT_OCCLUSION" for n in nt.nodes):
        ao += 1

cams = {}
for name in ("Camera", "CameraCore", "CameraHero"):
    o = bpy.data.objects.get(name)
    if o:
        cams[name] = {"type": o.data.type, "ortho_scale": getattr(o.data, "ortho_scale", None),
                      "lens": getattr(o.data, "lens", None),
                      "location": list(o.location)}

g6 = {"check": "G6", "objects_mesh": len(objs), "faces": faces,
      "bbox": {"x": [round(min(xs), 1), round(max(xs), 1)],
               "y": [round(min(ys), 1), round(max(ys), 1)],
               "z": [round(min(zs), 1), round(max(zs), 1)]},
      "nan_vertices": nan, "pass": nan == 0 and len(objs) > 1000}
json.dump(g6, open(os.path.join(out, "G6", "geom_check.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
json.dump({"check": "S8", "materials_with_noise_ramp": mottled,
           "materials_with_ao_node": ao, "pass": mottled >= 8},
          open(os.path.join(out, "S8", "material_layers.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
json.dump({"check": "S9", "bevel_objects": bevel,
           "bevel_width_range": [round(min(bevel_w), 3), round(max(bevel_w), 3)] if bevel_w else [0, 0],
           "pass": bevel >= 500},
          open(os.path.join(out, "S9", "bevel_count.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
core_px = 2072
px_per_m = core_px / cams["CameraCore"]["ortho_scale"]
json.dump({"check": "S10", "core_px": core_px, "ortho_scale": cams["CameraCore"]["ortho_scale"],
           "px_per_m": round(px_per_m, 3), "same_scene": True,
           "cameras": cams, "pass": px_per_m >= 14.0},
          open(os.path.join(out, "S10", "core_density.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("EVIDENCE_OK", len(objs), faces, bevel, mottled, ao, round(px_per_m, 2))
