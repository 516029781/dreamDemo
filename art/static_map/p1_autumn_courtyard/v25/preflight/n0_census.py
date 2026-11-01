# N0 census: objects, camera, bbox, external links. Run headless:
# blender.exe -b <blend> -P n0_census.py
import bpy, json, math, os
from mathutils import Vector

OUT = os.path.join(os.path.dirname(__file__), "N0_CENSUS.json")
sc = bpy.context.scene
cam = sc.camera

def wbbox(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
    return [round(min(xs), 3), round(min(ys), 3), round(min(zs), 3),
            round(max(xs), 3), round(max(ys), 3), round(max(zs), 3)]

objs = []
for ob in sc.objects:
    if ob.type not in {'MESH', 'CURVE', 'SURFACE'}:
        continue
    nv = len(ob.data.vertices) if hasattr(ob.data, 'vertices') else 0
    objs.append({
        "name": ob.name, "type": ob.type, "verts": nv,
        "visible_render": not ob.hide_render,
        "bbox": wbbox(ob),
        "mats": [m.name for m in ob.data.materials if m] if ob.type == 'MESH' else [],
    })

# camera info
cam_info = None
if cam:
    cd = cam.data
    r = cam.matrix_world.to_euler()
    cam_info = {
        "name": cam.name, "loc": [round(v, 4) for v in cam.matrix_world.translation],
        "rot_deg": [round(math.degrees(a), 3) for a in r],
        "type": cd.type, "lens": round(cd.lens, 3),
        "sensor": round(cd.sensor_width, 3), "clip": [cd.clip_start, cd.clip_end],
        "dof": cd.dof.use_dof, "focus_dist": round(cd.dof.focus_distance, 3) if cd.dof.use_dof else None,
    }

# render settings
render = {
    "res": [sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage],
    "engine": sc.render.engine,
    "film_transparent": sc.render.film_transparent,
    "view_transform": sc.view_settings.view_transform,
    "exposure": round(sc.view_settings.exposure, 4),
    "look": sc.view_settings.look,
}

# external image links
links = []
for img in bpy.data.images:
    if img.filepath and img.packed_file is None:
        p = bpy.path.abspath(img.filepath)
        links.append({"image": img.name, "path": p, "exists": os.path.exists(p)})

# unit / world
meta = {"unit_scale": sc.unit_settings.scale_length,
        "unit_system": sc.unit_settings.system,
        "world_nodes": sc.world is not None and sc.world.use_nodes,
        "object_count_total": len(sc.objects)}

out = {"camera": cam_info, "render": render, "meta": meta,
       "mesh_objects": sorted(objs, key=lambda o: o["bbox"][1]),
       "external_images": links}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("CENSUS_WRITTEN", OUT, "objects=", len(objs))
