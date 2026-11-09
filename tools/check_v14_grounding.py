"""M08 grounding diagnostic for v14 (read-only, Blender-internal).

Reports objects whose world bounding-box bottom is far from their expected
support plane. Diagnostic_only: an orthographic pre-render has no single
global support plane, so this never gates delivery by itself.

    blender -b <v14>/scene.blend --python tools/check_v14_grounding.py -- <OUT_JSON>
"""
import json
import sys
from collections import Counter
from pathlib import Path

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
out = Path(argv[0]).resolve()
out.parent.mkdir(parents=True, exist_ok=True)

PLATFORM_Z = 4.70
suspects = []
bottoms = Counter()
for ob in bpy.data.objects:
    if ob.type != "MESH":
        continue
    zs = [(ob.matrix_world @ Vector(c)).z for c in ob.bound_box]
    zmin = min(zs)
    bottoms[round(zmin, 1)] += 1
    # Above the platform with nothing beneath within 0.02 m is not detectable
    # from a bounding box alone; flag only clearly airborne props.
    if 5.0 < zmin < 60.0 and not any(k in ob.name for k in
            ("_up_", "cope", "rail", "pipe", "rack", "card", "fog", "dome",
             "silo", "antenna", "mast", "crane", "truss", "beam", "lamp",
             "light", "palm", "crown", "branch", "ladder", "rung")):
        suspects.append({"name": ob.name, "zmin": round(zmin, 3)})

d = {
    "schema": "v14-grounding-v1",
    "scene": bpy.data.filepath.replace("\\", "/"),
    "meshes": sum(1 for o in bpy.data.objects if o.type == "MESH"),
    "bottom_z_histogram": dict(bottoms.most_common(16)),
    "airborne_suspects": suspects[:40],
    "airborne_suspect_count": len(suspects),
    "diagnostic_only": True,
    "note": "bounding-box proxy; visual sign-off is still required",
}
out.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
print("GROUNDING_OK suspects=", len(suspects))
