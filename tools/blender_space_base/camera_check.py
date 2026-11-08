"""Camera/pixel contract check for space_base_minigame v01.

Run:
  blender -b <scene.blend> --python tools/blender_space_base/camera_check.py -- \
    --out-dir knowledge/active/20261102-space-base-map/runs/20261102-1314/evidence

Implements C1/C2:
  physical camera = 55 deg elevation (Blender Euler X=35), north side looking south;
  final image = horizontal mirror of the physical render, so final_px = W - raw_px.
Expected final mapping: px=x*8; py=70+(y+190)*6.5536.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec_dims as S  # noqa: E402

W, H = 1920, 2560
POINTS = [
    ("x=0 wall", 0.0, 0.0, 0.02, 0.0, 1315.18),
    ("x=240 wall", 240.0, 0.0, 0.02, 1920.0, 1315.18),
    ("south wall y-190", 120.0, -190.0, 0.02, 960.0, 70.0),
    ("north wall y190", 120.0, 190.0, 0.02, 960.0, 2560.0),
    ("south exit", 120.0, -30.0, 0.02, 960.0, 1119.0),
    ("workshop north gate", 120.0, -60.0, 0.02, 960.0, 922.0),
    ("evac", 195.0, -180.0, 0.02, 1560.0, 136.0),
    ("exit west edge", 112.5, -30.0, 0.02, 900.0, 1119.0),
    ("exit east edge", 127.5, -30.0, 0.02, 1020.0, 1119.0),
]


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    return ap.parse_args(argv)


def main():
    a = parse()
    sc = bpy.context.scene
    cam = sc.camera
    rows = []
    max_err = 0.0
    for name, x, y, z, exp_px, exp_py in POINTS:
        co = world_to_camera_view(sc, cam, Vector((x, y, z)))
        raw_px = co.x * W
        py = (1.0 - co.y) * H
        final_px = W - raw_px
        err = max(abs(final_px - exp_px), abs(py - exp_py))
        max_err = max(max_err, err)
        rows.append({
            "point": name, "world": [x, y, z],
            "raw_px": round(raw_px, 3), "final_px": round(final_px, 3),
            "py": round(py, 3), "expected_px": exp_px, "expected_py": exp_py,
            "error_px": round(err, 3), "pass": err <= 1.5,
        })
    cam_info = {
        "location": [round(v, 3) for v in cam.location],
        "rotation_deg": [round(math.degrees(v), 3) for v in cam.rotation_euler],
        "ortho_scale": cam.data.ortho_scale,
        "sensor_fit": cam.data.sensor_fit,
        "resolution": [sc.render.resolution_x, sc.render.resolution_y],
        "image_contract": "final_px = W - raw_px; py = 70+(y+190)*6.5536; W=1920,H=2560",
    }
    g1 = {"test_id": "TEST-G1", "check": "G1", "camera": cam_info, "points": rows,
          "max_error_px": round(max_err, 3), "pass": max_err <= 1.5}

    # viewport clamp math for G7 (1080x1620; top = clamp(py-810,0,940); left = clamp(px-540,0,840))
    vp = []
    for name, x, y, z, exp_px, exp_py in POINTS:
        co = world_to_camera_view(sc, cam, Vector((x, y, z)))
        px = W - co.x * W
        py = (1.0 - co.y) * H
        left = min(max(px - 540.0, 0.0), W - 1080.0)
        top = min(max(py - 810.0, 0.0), H - 1620.0)
        vp.append({"point": name, "px": round(px, 2), "py": round(py, 2),
                   "viewport_left": round(left, 2), "viewport_top": round(top, 2),
                   "inside": -1e-6 <= left <= W - 1080.0 and -1e-6 <= top <= H - 1620.0})
    g7 = {"test_id": "TEST-G7", "check": "G7", "viewport": [1080, 1620],
          "clamp": {"left": [0, 840], "top": [0, 940]}, "points": vp,
          "pass": all(p["inside"] for p in vp)}

    ev = os.path.join(a.out_dir)
    os.makedirs(os.path.join(ev, "G1"), exist_ok=True)
    os.makedirs(os.path.join(ev, "G7"), exist_ok=True)
    with open(os.path.join(ev, "G1", "camera_projection.json"), "w", encoding="utf-8") as f:
        json.dump(g1, f, ensure_ascii=False, indent=1)
    with open(os.path.join(ev, "G7", "viewport_math.json"), "w", encoding="utf-8") as f:
        json.dump(g7, f, ensure_ascii=False, indent=1)
    print("CAMERA_CHECK", "PASS" if g1["pass"] and g7["pass"] else "FAIL", "max_err", max_err)
    return 0 if g1["pass"] and g7["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
