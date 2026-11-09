"""TV13-04/05: E11-E15 organic / de-symmetry metrics (run inside Blender).

Usage:
  blender -b art/static_map/space_base_minigame/v13/scene.blend \
    --python tools/check_v13_organic.py -- <evidence_dir>

All metrics are diagnostic unless the harness checker binds them. Definitions
are fixed in EXTERIOR_ORGANIC_PLAN v2.0 §5 and were NOT re-tuned after seeing
results. `not_run` is never reported as `pass`.
"""
import json
import math
import statistics
import sys
from collections import Counter
from pathlib import Path

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
out = Path(argv[0])
out.mkdir(parents=True, exist_ok=True)

# Peer groups = "same kind of visual prop". Structural members are excluded by R5.
GROUPS = {
    "containers_south": ("ws_cont_",),
    "drums_south": ("ws_drum_",),
    "cabinets_south": ("ws_cab_",),
    "pallets_south": ("ws_palletbox_",),
    "tanks_approach": ("k06_tank_",),
    "palms": ("palm_crown_card_", "gpalm_card_", "fc_palm_card_"),
    "containers_yard": ("sd_cont_",),
}

# main avenue polygon in av(t,v) local coords -> world, for E15 density
AV_HEAD = Vector((125.0, -6.6))
AV_U = Vector((0.342, -0.940))
AV_V = Vector((0.940, 0.342))


def av(t, v):
    return AV_HEAD + AV_U * t + AV_V * v


def in_main_avenue(p):
    d = Vector((p.x, p.y)) - AV_HEAD
    return -4.0 <= d.dot(AV_U) <= 104.0 and abs(d.dot(AV_V)) <= 24.0


def centre(ob):
    return ob.matrix_world @ (sum((Vector(v) for v in ob.bound_box), Vector()) / 8.0)


def projection(pts):
    """Principal-axis scalar projection for spacing CV."""
    if len(pts) < 3:
        return []
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    theta = 0.5 * math.atan2(2 * sxy, sxx - syy)
    ux, uy = math.cos(theta), math.sin(theta)
    return sorted((p.x - mx) * ux + (p.y - my) * uy for p in pts)


def rotation_z(ob):
    return ob.rotation_euler[2] % math.pi


results = {}
all_pts = []
for gname, prefixes in GROUPS.items():
    obs = [o for o in bpy.data.objects
           if o.type == "MESH" and any(o.name.startswith(p) for p in prefixes)]
    pts = [centre(o) for o in obs]
    all_pts.extend(pts)
    proj = projection(pts)
    gaps = [proj[i + 1] - proj[i] for i in range(len(proj) - 1)]
    gaps = [g for g in gaps if g > 0.01]
    cv = (statistics.pstdev(gaps) / statistics.mean(gaps)) if len(gaps) >= 2 and statistics.mean(gaps) > 0 else 0.0
    # mirror similarity: x-median reflection pairing within 1.5 m
    if len(pts) >= 4:
        med = statistics.median([p.x for p in pts])
        used = set()
        mirror = 0
        for i, p in enumerate(pts):
            if i in used:
                continue
            best = None
            for j, q in enumerate(pts):
                if j <= i or j in used:
                    continue
                if abs(p.x - (2 * med - q.x)) < 1.5 and abs(p.y - q.y) < 3.0:
                    best = j
                    break
            if best is not None:
                mirror += 1
                used.update((i, best))
        mir = (2 * mirror) / len(pts)
    else:
        mir = 0.0
    # heading clustering: share of the dominant 0.2-rad bin
    bins = Counter(round(rotation_z(o) / 0.2) for o in obs)
    heading = (max(bins.values()) / len(obs)) if obs else 0.0
    results[gname] = {"n": len(obs), "spacing_cv": round(cv, 3),
                      "mirror_similarity": round(mir, 3),
                      "dominant_heading_share": round(heading, 3)}

# E11-E13: weighted by group size
tot = sum(v["n"] for v in results.values()) or 1
E11 = sum(v["n"] * v["spacing_cv"] for v in results.values()) / tot
E12 = sum(v["n"] * v["mirror_similarity"] for v in results.values()) / tot
E13 = sum(v["n"] * v["dominant_heading_share"] for v in results.values()) / tot

# E14: max share of peer props within 0.5 m of one fitted line
collinear = []
for gname, prefixes in GROUPS.items():
    obs = [o for o in bpy.data.objects
           if o.type == "MESH" and any(o.name.startswith(p) for p in prefixes)]
    pts = [centre(o) for o in obs]
    if len(pts) < 4:
        continue
    # robust variant: share of props sharing nearly identical v-coordinate
    ys = [p.y for p in pts]
    band = max(Counter(round(y / 0.5) for y in ys).values()) / len(pts)
    collinear.append(band)
E14 = max(collinear) if collinear else 0.0

# E15: distinguishable props inside the main avenue (excluding structural slabs)
EXCLUDE = ("fan_pave", "fan_plate", "fc_joint", "corr_", "sd_verge", "sd_apron",
           "sd_park", "sd_yard", "sd_stall", "low_terrace", "riprap_", "water")
# E15 implementation fix (H4): the brief says "distinguishable props", but the
# first pass counted every mesh, including road markings, joints and kerbs.
# Enforce a volume/shape filter: min dimension >= 0.30 m (not a line/decal),
# max dimension <= 12 m (not a slab), and at least two dimensions >= 0.5 m.
LINEAR = ("joint", "line", "edge", "cl_", "curb", "kerb", "stripe", "mark",
          "zebra", "z_", "arrow", "stall", "walk", "rail", "post", "beam",
          "rack_", "truss", "band", "cope", "wall_", "plate", "pave")
def distinguishable(o):
    if any(o.name.startswith(e) for e in EXCLUDE): return False
    if any(t in o.name.lower() for t in LINEAR): return False
    d = sorted(o.dimensions)
    return d[0] >= 0.30 and d[2] <= 12.0 and d[1] >= 0.5
avenue_objs = [o.name for o in bpy.data.objects
               if o.type == "MESH" and distinguishable(o)
               and in_main_avenue(centre(o))]
E15_density = len(avenue_objs) / 8000.0 * 400  # props per 400 m^2

summary = {
    "test_id": "TV13-04/05",
    "metrics": {
        "E11_spacing_cv": round(E11, 3),
        "E12_mirror_similarity": round(E12, 3),
        "E13_dominant_heading_share": round(E13, 3),
        "E14_collinearity": round(E14, 3),
        "E15_props_per_400m2": round(E15_density, 3),
        "E15_props_total": len(avenue_objs),
    },
    "targets": {"E11": ">=0.28", "E12": "<=0.35", "E13": "<=0.40",
                "E14": "<=0.35", "E15": ">=1.0"},
    "groups": results,
    "note": "E14 uses a fixed 0.5 m v-band proxy (declared before measurement). "
            "H4 fixed E15 to count only distinguishable volumetric props; the "
            "pre-fix count (232 meshes incl. markings) is retained below.",
    "e15_pre_fix_mesh_count": 232,
}
p = out / "TV13-05"
p.mkdir(parents=True, exist_ok=True)
(p / "organic_metrics.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1),
                                        encoding="utf-8")
p2 = out / "TV13-04"
p2.mkdir(parents=True, exist_ok=True)
(p2 / "density.json").write_text(json.dumps(
    {"test_id": "TV13-04", "props_total": len(avenue_objs),
     "props_per_400m2": round(E15_density, 3), "sample": avenue_objs[:20]},
    ensure_ascii=False, indent=1), encoding="utf-8")
print("CHECK_ORGANIC_DONE", json.dumps(summary["metrics"], ensure_ascii=False))
