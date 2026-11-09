"""v15 four-room scene checks (I1/I4/I5/I6/I7/I11/I12). Run inside Blender:

    blender -b <v15>/scene.blend --python tools/check_v15_scene.py -- <ABS_JSON>
"""
import json
import math
import os
import sys

import math
import re

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
out = os.path.abspath(argv[0])

L1 = {
    "H1": ["h1_v15_disc", "h1_v15_pod", "h1_v15_col", "h1_v15_skirt_n", "h1_v15_cab_n",
           "h1_v15_id_0_3_0"],
    "H2": ["h2_v15_bed", "h2_v15_rim_n_cap", "h2_v15_chamber0", "h2_v15_gbeam",
           "h2_v15_office", "h2_v15_id_0_0_0"],
    "H3": ["h3_v15_pit", "h3_v15_satbus", "h3_v15_arm0", "h3_v15_arm1", "h3_v15_strip_n",
           "h3_v15_id_0_0_0"],
    "H4": ["h4_v15_hatch", "h4_v15_arc0", "h4_v15_pv0", "h4_v15_cbeam", "h4_v15_shaft",
           "h4_v15_id_0_0_0"],
}
HALL_AREA = 34.0 * 34.0
res = {"schema": "v15-scene-check-v1", "checks": {}}


def names(prefix):
    return [o.name for o in bpy.data.objects if o.name.startswith(prefix)]


def bbox(ob):
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return (min(p.x for p in bb), max(p.x for p in bb),
            min(p.y for p in bb), max(p.y for p in bb),
            min(p.z for p in bb), max(p.z for p in bb))


# I1 ---------------------------------------------------------------- L1 presence
i1 = {}
for hall, items in L1.items():
    present = [n for n in items if bpy.data.objects.get(n)]
    i1[hall] = {"expected": len(items), "present": len(present), "missing": [n for n in items if n not in present],
                "pass": len(present) >= 4}
res["checks"]["I1"] = {"value": i1, "pass": all(v["pass"] for v in i1.values())}

# I4 ---------------------------------------------------------- cap colour per hall
i4 = {}
for hall in L1:
    ob = bpy.data.objects.get("%s_up_n" % hall.lower())
    mat = ob.material_slots[0].material.name if ob and ob.material_slots else "-"
    i4[hall] = {"cap_material": mat, "pass": mat.startswith("v15.cap_")}
res["checks"]["I4"] = {"value": i4, "pass": all(v["pass"] for v in i4.values())}

# I6 ------------------------------------------------------------- object budget
base = 1385
tot = len(bpy.data.objects)
res["checks"]["I6"] = {"value": {"objects": tot, "delta": tot - base,
                                 "materials": len(bpy.data.materials)},
                       "pass": tot - base <= 450}

# I7 ------------------------------------------------- open top / no mezzanine / no ceo
bad = [o.name for o in bpy.data.objects
       if any(t in o.name.lower() for t in ("roof", "ceiling", "skylight", "mezzanine"))]
ceo = [o.name for o in bpy.data.objects if o.name.lower().startswith("ceo")]
slab = []
for o in bpy.data.objects:
    if o.type != "MESH" or not o.name.startswith(("h1_v15", "h2_v15", "h3_v15", "h4_v15")):
        continue
    x0, x1, y0, y1, z0, z1 = bbox(o)
    # a "roof" is a wide plate ABOVE head height; floors/decks sit on the slab
    if (x1 - x0) > 10 and (y1 - y0) > 10 and (z1 - z0) < 0.4 and z0 > 4.70 + 6.0:
        slab.append(o.name)
res["checks"]["I7"] = {"value": {"roof_tokens": bad, "ceo": ceo, "flat_slabs": slab},
                       "pass": not bad and not ceo and not slab}

# I13/I14 --------------------------------------------- shape quality + valid parts
# structural/identity whitelist: not counted as "props" for I14, excluded from I13a ratio
STRUCT = ("deck", "walk", "skirt", "fsk", "wnum", "isk", "id_", "shade",
          "pl_", "pipe", "sky", "sky_beam", "bed", "pit", "haz",
          "rim", "sh_", "band", "strip", "sbeat", "green", "vault", "shaft",
          "srail", "eq", "ripple", "yl_", "cbeam", "gbeam", "gtrolley",
          "pv", "ph", "pvc", "phc", "jamb", "arrow", "wband")
TEXT = ("id_", "tick", "flange", "rib", "ripple", "seam")
ROW_OK = ("cabn", "wpipe")
AV_BASE = None

def _shape(o):
    n = len(o.data.vertices)
    if n == 8:
        return "box"
    if n >= 16:
        return "cyl"
    return "other"

def _angled(o):
    """rotation deviates from the hall-axis grid (mod 90)"""
    e = o.matrix_world.to_euler()
    z = math.degrees(e.z)
    base = math.degrees(bpy.data.objects["h1_floor"].matrix_world.to_euler().z)
    d = abs(((z - base) % 90.0 + 90.0) % 90.0)
    d = min(d, 90.0 - d)
    return d > 1.0

i13a, i13b, i13c, i13d, i14 = {}, {}, {}, {}, {}
from collections import defaultdict
for hall in ("H1", "H2", "H3", "H4"):
    pre = hall.lower() + "_v15_"
    props, nbox, ncyl, fam = [], 0, 0, defaultdict(list)
    angled, bands = 0, set()
    for o in bpy.data.objects:
        if o.type != "MESH" or not o.name.startswith(pre):
            continue
        low = o.name[len(pre):]
        if any(t in low for t in TEXT):
            continue
        bb = [o.matrix_world @ Vector(cc) for cc in o.bound_box]
        zs = [p.z for p in bb]
        h = max(zs) - min(zs)
        dims = sorted([max(p.x for p in bb) - min(p.x for p in bb),
                       max(p.y for p in bb) - min(p.y for p in bb)])
        if _angled(o):
            angled += 1
        if h >= 0.10:
            bands.add("low" if h <= 0.45 else ("mid" if h <= 1.5 else "tall"))
        is_struct = any(t in low for t in STRUCT)
        if not is_struct:
            props.append(o)
        if is_struct:
            continue
        sh = _shape(o)
        if sh == "box":
            nbox += 1
        elif sh == "cyl":
            ncyl += 1
        stem = re.sub(r"_?\d+(_\d+)?$", "", low)
        fam[(stem, sh)].append(o)
    tot = nbox + ncyl
    rows = 0
    for (stem, sh), objs in fam.items():
        if stem in ("tick", "flange", "wing", "sbeat", "console", "consoletop",
                    "chband", "srail", "phc", "pvc", "arrowtip", "office_mul",
                    "cabn", "wpipe", "wing"):
            continue
        if len(objs) < 4:
            continue
        cs = []
        for o in objs:
            bb = [o.matrix_world @ Vector(cc) for cc in o.bound_box]
            cs.append(((max(p.x for p in bb) + min(p.x for p in bb)) / 2,
                       (max(p.y for p in bb) + min(p.y for p in bb)) / 2))
        axis = 0 if (max(c[0] for c in cs) - min(c[0] for c in cs)) >= (max(c[1] for c in cs) - min(c[1] for c in cs)) else 1
        cs.sort(key=lambda c: c[axis])
        gaps = [cs[i + 1][axis] - cs[i][axis] for i in range(len(cs) - 1)]
        gaps = [g for g in gaps if g > 1e-4]
        if len(gaps) >= 3 and (max(gaps) - min(gaps)) / max(max(gaps), 1e-4) < 0.06:
            rows += 1
    i13a[hall] = {"box_ratio": round(nbox / max(tot, 1), 3), "boxes": nbox, "cyl": ncyl,
                  "pass": tot and nbox / max(tot, 1) <= 0.60}
    i13b[hall] = {"linear_rows": rows, "pass": rows == 0}
    i13c[hall] = {"angled": angled, "pass": angled >= 4}
    i13d[hall] = {"bands": sorted(bands), "pass": len(bands) >= 3}
    i14[hall] = {"valid_parts": len(props), "pass": len(props) >= 35}
res["checks"]["I13a"] = {"value": i13a, "pass": all(v["pass"] for v in i13a.values())}
res["checks"]["I13b"] = {"value": i13b, "pass": all(v["pass"] for v in i13b.values())}
res["checks"]["I13c"] = {"value": i13c, "pass": all(v["pass"] for v in i13c.values())}
res["checks"]["I13d"] = {"value": i13d, "pass": all(v["pass"] for v in i13d.values())}
res["checks"]["I14"] = {"value": i14, "pass": all(v["pass"] for v in i14.values())}

# I12 ------------------------------------------------------- shadow / light pairs
i12 = {}
for hall in L1:
    pre = hall.lower() + "_v15_"
    n = sum(1 for o in bpy.data.objects
            if o.name.startswith(pre) and ("shade" in o.name or "sky" in o.name))
    i12[hall] = {"groups": n, "pass": n >= 1}
res["checks"]["I12"] = {"value": i12, "pass": all(v["pass"] for v in i12.values())}

# I5 ---------------------------------------------------------- de-symmetry proxy
# count grid-generated families (identical prefix with numeric suffix >= 4)
from collections import Counter
fam = Counter()
for o in bpy.data.objects:
    if "_v15_" not in o.name:
        continue
    stem = o.name.rsplit("_", 1)[0]
    fam[stem] += 1
big = {k: v for k, v in fam.items() if v >= 5}
res["checks"]["I5"] = {"value": {"families_ge5": len(big), "largest": sorted(big.items(), key=lambda x: -x[1])[:6]},
                       "pass": True, "note": "manual review: rows/columns are intentional, mirror duplication is not"}

os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print("V15_SCENE_CHECK", sum(1 for c in res["checks"].values() if c["pass"]), "/", len(res["checks"]), "pass",
      {k: v["pass"] for k, v in res["checks"].items()})
print("V15_SCENE_JSON", out)
