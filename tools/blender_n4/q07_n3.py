"""Q07: edit a copy of the n3 bench source, save/reopen/export."""
import hashlib, json, os
import bpy
ROOT = r"C:\软件\鼠鼠"
BLEND = os.path.join(ROOT, "art", "iterations", "cycle_04", "PROP001", "versions", "q07_edited_bench.blend")
GLB = os.path.join(ROOT, "art", "iterations", "cycle_04", "PROP001", "versions", "q07_edited_bench.glb")
OUT = os.path.join(ROOT, "delivery", "next_cycle", "n3", "T5", "q07_archive_report.json")

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

def dims(o):
    return [round(v, 4) for v in o.dimensions]

bpy.ops.wm.open_mainfile(filepath=BLEND)
wood = bpy.data.objects["PROP001_bench_wood"]
metal = bpy.data.objects["PROP001_bench_metal"]
before = dims(wood)
metal_before = dims(metal)
wood.scale.x *= 1.20
bpy.context.view_layer.update()
bpy.context.view_layer.objects.active = wood
wood.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bpy.context.view_layer.update()
after = dims(wood)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
saved = sha(BLEND)
bpy.ops.wm.open_mainfile(filepath=BLEND)
reopened = dims(bpy.data.objects["PROP001_bench_wood"])
metal_after = dims(bpy.data.objects["PROP001_bench_metal"])
objs = [bpy.data.objects["PROP001_bench_wood"], bpy.data.objects["PROP001_bench_metal"]]
bpy.ops.object.select_all(action="DESELECT")
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", use_selection=True,
                          export_apply=True, export_yup=True, export_tangents=True)
report = {
    "kind": "q07_native_source_edit_n3",
    "source": "art/iterations/cycle_04/PROP001/versions/q07_edited_bench.blend",
    "object": "PROP001_bench_wood",
    "edit": "scale X by 1.20 and apply transform; save, reopen, export",
    "dimensions_before": before,
    "dimensions_after": after,
    "dimensions_reopened": reopened,
    "metal_before": metal_before,
    "metal_after": metal_after,
    "dimensions_changed": before != after,
    "reopened_matches": after == reopened,
    "unrelated_metal_unchanged": metal_before == metal_after,
    "saved_sha256": saved,
    "glb": {"path": "art/iterations/cycle_04/PROP001/versions/q07_edited_bench.glb",
            "sha256": sha(GLB), "bytes": os.path.getsize(GLB)},
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(report, ensure_ascii=False))
