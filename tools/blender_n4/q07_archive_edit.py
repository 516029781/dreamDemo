"""Q07 evidence: archive an edited copy of the bench source and its GLB export."""
import hashlib
import json
import os

import bpy

SOURCE = r"C:\软件\鼠鼠\art\iterations\cycle_02\PROP001\versions\q07_before\PROP001_bench.blend"
OUT_DIR = r"C:\软件\鼠鼠\art\iterations\cycle_02\PROP001\versions"
EDITED = os.path.join(OUT_DIR, "q07_edited_bench.blend")
EXPORT = os.path.join(OUT_DIR, "q07_edited_bench.glb")
REPORT = r"C:\软件\鼠鼠\delivery\next_cycle\T5\q07_archive_report.json"


def sha(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def dims(obj):
    return [round(v, 4) for v in obj.dimensions]


bpy.ops.wm.open_mainfile(filepath=SOURCE)
wood = bpy.data.objects["PROP001_bench_wood"]
before = dims(wood)
wood.scale.x *= 1.20
bpy.context.view_layer.update()
bpy.context.view_layer.objects.active = wood
wood.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bpy.context.view_layer.update()
after = dims(wood)
bpy.ops.wm.save_as_mainfile(filepath=EDITED)
bpy.ops.wm.open_mainfile(filepath=EDITED)
reopened = dims(bpy.data.objects["PROP001_bench_wood"])
bpy.ops.export_scene.gltf(filepath=EXPORT, export_format="GLB", use_selection=False)
report = {
    "kind": "q07_archived_native_edit",
    "source_original": SOURCE,
    "edited_blend": EDITED,
    "edited_glb": EXPORT,
    "object": "PROP001_bench_wood",
    "edit": "scale X by 1.20 and apply transform",
    "dimensions_before": before,
    "dimensions_after": after,
    "dimensions_reopened": reopened,
    "reopened_matches": after == reopened,
    "edited_blend_sha256": sha(EDITED),
    "edited_glb_sha256": sha(EXPORT),
    "note": "Final candidate build uses the restored original source; this archive proves the editable-source edit and re-export only.",
}
with open(REPORT, "w", encoding="utf-8") as handle:
    json.dump(report, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
print(json.dumps(report, ensure_ascii=False))
