"""Q07: copy the n4 bench source, edit/reopen/export without mutating history."""
import hashlib, json, os
import bpy

ROOT = r"C:\软件\鼠鼠"
SOURCE = os.path.join(ROOT, "art", "candidates", "candidate_n4", "source", "props", "PROP001_bench.blend")
OUT_DIR = os.path.join(ROOT, "art", "iterations", "cycle_04", "PROP001", "versions")
EDITED = os.path.join(OUT_DIR, "q07_edited_bench_n4.blend")
GLB = os.path.join(OUT_DIR, "q07_edited_bench_n4.glb")
OUT = os.path.join(ROOT, "delivery", "next_cycle", "n4", "T5", "q07_archive_report.json")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def dims(o):
    return [round(v, 4) for v in o.dimensions]


os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=SOURCE)
wood = bpy.data.objects["PROP001_bench_wood"]
metal = bpy.data.objects["PROP001_bench_metal"]
before = dims(wood)
metal_before = dims(metal)
wood.scale.x *= 1.20
bpy.context.view_layer.update()
bpy.context.view_layer.objects.active = wood
bpy.ops.object.select_all(action="DESELECT")
wood.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bpy.context.view_layer.update()
after = dims(wood)
bpy.ops.wm.save_as_mainfile(filepath=EDITED)
saved = sha(EDITED)
bpy.ops.wm.open_mainfile(filepath=EDITED)
reopened = dims(bpy.data.objects["PROP001_bench_wood"])
metal_after = dims(bpy.data.objects["PROP001_bench_metal"])
objs = [bpy.data.objects["PROP001_bench_wood"], bpy.data.objects["PROP001_bench_metal"]]
bpy.ops.object.select_all(action="DESELECT")
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", use_selection=True,
                          export_apply=True, export_yup=True, export_tangents=True)
report = {
    "kind": "q07_native_source_edit_n4",
    "source": "art/candidates/candidate_n4/source/props/PROP001_bench.blend",
    "edited_source": "art/iterations/cycle_04/PROP001/versions/q07_edited_bench_n4.blend",
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
    "glb": {"path": "art/iterations/cycle_04/PROP001/versions/q07_edited_bench_n4.glb",
            "sha256": sha(GLB), "bytes": os.path.getsize(GLB)},
}
open(OUT, "w", encoding="utf-8").write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(report, ensure_ascii=False))
