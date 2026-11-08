"""Geometry sanity check for space_base_minigame v01.

Run:
  blender -b <scene.blend> --python tools/blender_space_base/geom_check.py -- \
    --out-dir knowledge/active/.../runs/<run>/evidence
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import bpy
from mathutils import Vector


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    return ap.parse_args(argv)


def bbox(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    zs = [p.z for p in pts]
    return [min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)]


def main():
    a = parse()
    objects = [o for o in bpy.data.objects if o.type == "MESH"]
    rows = []
    below = []
    outside = []
    for o in objects:
        b = bbox(o)
        rows.append({"name": o.name, "bbox": [round(v, 3) for v in b],
                     "materials": [m.name if m else None for m in o.data.materials]})
        intentional_below = o.name in ("h2_cab_a", "h2_cab_c")
        if o.name != "field" and b[2] < -0.05 and not intentional_below:
            below.append({"name": o.name, "zmin": round(b[2], 3)})
        if o.name != "field" and (b[0] < -8.5 or b[3] > 248.5 or b[1] < -212.5 or b[4] > 198.5):
            outside.append({"name": o.name, "bbox": [round(v, 3) for v in b]})
    key = {}
    for name in ("central_body", "ceo_top", "h2_pool", "h3_pit", "ws_pit", "t16_bar",
                 "stair_H2", "stair_H4", "bridge_0", "bridge_1", "evac_frame_n", "evac_frame_s"):
        o = bpy.data.objects.get(name)
        if o:
            key[name] = [round(v, 3) for v in bbox(o)]
    payload = {
        "test_id": "TEST-G6", "check": "G6",
        "object_count": len(objects), "mesh_count": len(bpy.data.meshes),
        "below_ground_excluding_field": below,
        "intentional_below_ground": [] if not any(o.name in ("h2_cab_a", "h2_cab_c") for o in objects) else ["h2_cab_a", "h2_cab_c"],
        "outside_world_excluding_field": outside,
        "key_objects": key,
        "pass": not below and not outside,
    }
    out = os.path.join(a.out_dir, "G6")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "geom_check.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print("GEOM_CHECK", "PASS" if payload["pass"] else "FAIL",
          "objects", len(objects), "below", len(below), "outside", len(outside))
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
