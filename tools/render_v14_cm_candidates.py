"""v14 P0: delivery-resolution color-management candidates (L0-b).

Renders three variants from the FROZEN v13 scene.blend, changing only
scene.view_settings. Same camera / resolution / samples / seed as
render_v13_views.py's master branch, so results are directly comparable with
the v13 delivery image.

  blender -b art/static_map/space_base_minigame/v13/scene.blend \
    --python tools/render_v14_cm_candidates.py -- <ABS_OUT_DIR>

Writes <OUT_DIR>/timing.json with command, exit status, wall time and SHA of
each render (AGENTS.md §2 evidence requirement). Does NOT modify v13/scene.blend.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
out_dir = Path(argv[0]).resolve()
out_dir.mkdir(parents=True, exist_ok=True)

sc = bpy.context.scene
for o in bpy.data.objects:
    if o.get("is_char"):
        o.hide_render = True
sc.camera = bpy.data.objects["Camera"]
sc.render.resolution_x, sc.render.resolution_y = 1680, 2478
sc.cycles.samples = 24
sc.cycles.seed = 0

CASES = (
    ("cm_A_current.png", "Standard", "None", 0.22),
    ("cm_C_agx_mhc.png", "AgX", "AgX - Medium High Contrast", 0.22),
    ("cm_D_standard_m015.png", "Standard", "None", -0.15),
)

records = []
t_all = time.perf_counter()
for fn, transform, look, exposure in CASES:
    sc.view_settings.view_transform = transform
    sc.view_settings.look = look
    sc.view_settings.exposure = exposure
    sc.render.filepath = str(out_dir / fn)
    t0 = time.perf_counter()
    bpy.ops.render.render(write_still=True)
    dt = time.perf_counter() - t0
    p = out_dir / fn
    records.append({
        "file": fn,
        "view_transform": transform, "look": look, "exposure": exposure,
        "wall_seconds": round(dt, 2),
        "exit_ok": p.exists() and p.stat().st_size > 0,
        "bytes": p.stat().st_size if p.exists() else 0,
        "sha256": hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None,
    })
    print("CM_CANDIDATE_DONE", fn, round(dt, 2), "s")

report = {
    "schema": "v14-p0-render-timing-v1",
    "source_scene": bpy.data.filepath.replace("\\", "/"),
    "command": "blender -b <v13>/scene.blend --python tools/render_v14_cm_candidates.py -- <OUT>",
    "fixed_conditions": {"camera": "Camera", "resolution": [1680, 2478],
                         "samples": 24, "seed": 0, "is_char_hidden": True},
    "total_wall_seconds": round(time.perf_counter() - t_all, 2),
    "records": records,
}
(out_dir / "timing.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
print("CM_CANDIDATES_DONE", len(records), "renders,", report["total_wall_seconds"], "s")
