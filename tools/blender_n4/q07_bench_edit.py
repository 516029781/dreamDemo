"""Q07 probe: edit the native bench source, save, reopen and report dimensions."""
import hashlib
import json
import os

import bpy

BLEND = r"C:\软件\鼠鼠\art\full\source\props\PROP001_bench.blend"
OUT = r"C:\软件\鼠鼠\delivery\next_cycle\T5\q07_edit_report.json"


def sha(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def dims(obj):
    return [round(v, 4) for v in obj.dimensions]


bpy.ops.wm.open_mainfile(filepath=BLEND)
wood = bpy.data.objects["PROP001_bench_wood"]
before = dims(wood)
wood.scale.x *= 1.20
bpy.context.view_layer.update()
bpy.context.view_layer.objects.active = wood
wood.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bpy.context.view_layer.update()
after = dims(wood)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
saved_hash = sha(BLEND)

# Reopen the saved file: this is the save/reopen proof, not just in-memory data.
bpy.ops.wm.open_mainfile(filepath=BLEND)
reopened = dims(bpy.data.objects["PROP001_bench_wood"])
report = {
    "kind": "q07_native_source_edit",
    "source": BLEND,
    "object": "PROP001_bench_wood",
    "edit": "scale X by 1.20 and apply transform",
    "dimensions_before": before,
    "dimensions_after": after,
    "dimensions_reopened": reopened,
    "dimensions_changed": before != after,
    "reopened_matches": after == reopened,
    "saved_sha256": saved_hash,
}
with open(OUT, "w", encoding="utf-8") as handle:
    json.dump(report, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
print(json.dumps(report, ensure_ascii=False))
