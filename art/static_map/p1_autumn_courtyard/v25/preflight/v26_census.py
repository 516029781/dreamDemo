"""V26 Step0: census of canopy/grass objects in a scene file.
Usage: blender <file.blend> -b --python n0_v26_census.py -- <out_json> <tag>
"""
import bpy, json, sys

argv = sys.argv[sys.argv.index("--") + 1:]
out_json, tag = argv[0], argv[1]

KEYS = ("canopy", "grass", "tuft", "clump", "leaf", "shrub", "mulch")

recs = []
for ob in bpy.data.objects:
    n = ob.name.lower()
    if any(k in n for k in KEYS):
        recs.append({
            "name": ob.name,
            "type": ob.type,
            "loc": [round(v, 4) for v in ob.location],
            "rot_euler": [round(v, 4) for v in ob.rotation_euler] if ob.rotation_mode == "XYZ" else None,
            "rot_mode": ob.rotation_mode,
            "scale": [round(v, 4) for v in ob.scale],
            "parent": ob.parent.name if ob.parent else None,
            "mats": [m.name if hasattr(m, "name") else str(m) for m in getattr(ob.data, "materials", [])] if ob.type == "MESH" else [],
            "mesh": ob.data.name if ob.type == "MESH" else None,
            "hide_render": ob.hide_render,
        })

# material-level census for grass/leaf mats in file
mat_recs = [m.name for m in bpy.data.materials if any(k in m.name.lower() for k in ("grass", "leaf", "foliage", "root"))]

out = {"tag": tag, "object_count_total": len(bpy.data.objects), "objects": recs, "veg_materials": mat_recs}
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("CENSUS_DONE", tag, len(recs))
