"""导出 TEST-02 证据：对象清单、世界坐标 zmin、相机、太阳旋转模式。"""
import json
import bpy
from mathutils import Vector

sc = bpy.context.scene
rows = []
for o in sc.collection.all_objects:
    if o.type != "MESH":
        continue
    zmin = min((o.matrix_world @ Vector(c)).z for c in o.bound_box)
    rows.append({
        "name": o.name,
        "zmin": round(zmin, 4),
        "dims": [round(v, 3) for v in o.dimensions],
        "mats": [m.name for m in o.data.materials],
    })

cam = sc.camera
sun = bpy.data.objects.get("sun")
payload = {
    "objects": rows,
    "object_count": len(rows),
    "camera": {"name": cam.name, "loc": [round(v, 3) for v in cam.location], "lens": cam.data.lens},
    "sun": {
        "rot_mode": sun.rotation_mode,
        "quat": [round(v, 4) for v in sun.rotation_quaternion],
        "energy": sun.data.energy,
    },
    "libraries": [lib.filepath for lib in bpy.data.libraries],
    "images": [(im.name, im.filepath) for im in bpy.data.images if im.source == "FILE"],
}
print("EVID_JSON_BEGIN")
print(json.dumps(payload, ensure_ascii=True))
print("EVID_JSON_END")
