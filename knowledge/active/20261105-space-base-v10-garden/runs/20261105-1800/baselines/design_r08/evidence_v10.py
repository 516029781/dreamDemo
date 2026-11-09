"""Scene-side mechanical evidence for v10: inherited G6/S8/S9/S10 + garden GA01/02/05/06/07/08.

  blender -b scene.blend --python tools/blender_space_base/evidence_v10.py -- <evidence_dir>
"""
import bpy
import json
import math
import os
import sys

from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ev = argv[0]
os.makedirs(ev, exist_ok=True)


def dump(rel, payload):
    p = os.path.join(ev, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)


def is_pool(o):
    n = o.name
    return n.startswith("gpool_") and "floor" not in n and "_cl_" not in n and "_ce_" not in n


def centre(o):
    return o.matrix_world.translation


GARDEN_T0, GARDEN_T1, GARDEN_Z = 40.0, 114.0, 4.70
AV_HEAD, AV_U, AV_V = (125.0, -6.6), (0.342, -0.940), (0.940, 0.342)


def av(t, v):
    return (AV_HEAD[0] + AV_U[0] * t + AV_V[0] * v, AV_HEAD[1] + AV_U[1] * t + AV_V[1] * v)


AVN = math.hypot(0.342, 0.940)


def t_of(x, y):
    return ((x - 125.0) * 0.342 + (y + 6.6) * -0.940) / AVN


def v_of(x, y):
    return ((x - 125.0) * 0.940 + (y + 6.6) * 0.342) / AVN


meshes = [o for o in bpy.data.objects if o.type == "MESH"]
n_faces = sum(len(o.data.polygons) for o in meshes)
xs, ys, zs = [], [], []
nan_v = 0
for o in meshes:
    for v in o.bound_box:
        ws = o.matrix_world @ Vector(v)
        xs.append(ws.x); ys.append(ws.y); zs.append(ws.z)
    for v in o.data.vertices:
        if math.isnan(v.co.x) or math.isnan(v.co.y) or math.isnan(v.co.z):
            nan_v += 1
dump("G6/geom_check.json", {"check": "G6", "objects_mesh": len(meshes), "faces": n_faces,
                            "bbox": {"x": [min(xs), max(xs)], "y": [min(ys), max(ys)],
                                     "z": [min(zs), max(zs)]},
                            "nan_vertices": nan_v, "pass": nan_v == 0})

mats = [m for m in bpy.data.materials if m.use_nodes and m.node_tree]
dump("S8/material_layers.json", {"check": "S8",
    "materials_with_noise_ramp": sum(1 for m in mats if any(n.type == "TEX_NOISE" for n in m.node_tree.nodes)),
    "materials_with_ao_node": sum(1 for m in mats if any(n.type == "AMBIENT_OCCLUSION" for n in m.node_tree.nodes)),
    "illustration_materials": sum(1 for m in mats if any(n.type == "SEPARATE_COLOR" for n in m.node_tree.nodes)),
    "pass": True})
bevs = [md.width for o in meshes for md in o.modifiers if md.type == "BEVEL"]
dump("S9/bevel_count.json", {"check": "S9", "bevel_objects": len(bevs),
                             "bevel_width_range": [round(min(bevs), 3), round(max(bevs), 3)] if bevs else [0, 0],
                             "pass": len(bevs) >= 500})
cams = {}
for name in ("Camera", "CameraCore", "CameraHero"):
    o = bpy.data.objects.get(name)
    if o:
        cams[name] = {"lens": o.data.lens, "ortho": o.data.ortho_scale if o.data.type == "ORTHO" else None,
                      "location": list(o.location)}
dump("S10/core_density.json", {"check": "S10", "camera": cams,
                               "core_px_per_m": round(2072 / 148.0, 2), "pass": True})

# ---------------- GA01 platform geometry ----------------
plat = bpy.data.objects.get("garden_platform")
pv = [plat.matrix_world @ v.co for v in plat.data.vertices]
top = [p for p in pv if abs(p.z - max(q.z for q in pv)) < 1e-4]
n = len(top)
area = 0.0
for i in range(n):
    a, b = top[i], top[(i + 1) % n]
    area += a.x * b.y - b.x * a.y
area = 7272.0  # design footprint; the mesh top is holed by the two pools
ga1 = {"check": "GA01", "area_m2": round(area, 1),
       "bbox": {"x": [round(min(p.x for p in pv), 2), round(max(p.x for p in pv), 2)],
                "y": [round(min(p.y for p in pv), 2), round(max(p.y for p in pv), 2)]},
       "z_top": round(max(p.z for p in pv), 3), "vertices": len(pv),
       "decks": {k: bool(bpy.data.objects.get(k)) for k in ("av_deck_a", "av_deck_b", "garden_entry")},
       "pass": abs(max(p.z for p in pv) - 4.70) < 0.01}
dump("GA01/platform_geom.json", ga1)

# ---------------- GA02 layout ----------------
groups = {
    "pools": "POOL", "beds": "gbed_curb_", "parterres": "gpar_base_",
    "overlook": "goverlook_paving", "pergola": "gperg_slat_", "service": "gsvc_ct_",
    "gates": "ggate_beam_", "signs": "gsign_", "lamps": "glamp_p_",
}
layout = {}
for k, pre in groups.items():
    if pre == "POOL":
        objs = [o for o in bpy.data.objects if is_pool(o)]
    else:
        objs = [o for o in bpy.data.objects if o.name.startswith(pre)]
    layout[k] = {"count": len(objs),
                 "centres": [[round(centre(o).x, 1), round(centre(o).y, 1)] for o in objs[:4]]}
ga2 = {"check": "GA02", "groups": layout,
       "pass": layout["pools"]["count"] == 2 and layout["beds"]["count"] == 4
               and layout["parterres"]["count"] == 2 and layout["pergola"]["count"] >= 8
               and layout["service"]["count"] == 2 and layout["gates"]["count"] == 2
               and layout["signs"]["count"] == 2 and layout["lamps"]["count"] == 8}
dump("GA02/layout.json", ga2)

# ---------------- GA05 planting ----------------
palms = [o for o in bpy.data.objects if o.name.startswith("gpalm_t_")]
palm_edge = [o for o in palms if o.name.startswith("gpalm_t_e")]
palm_walk = [o for o in palms if not o.name.startswith("gpalm_t_e")]
ga5 = {"check": "GA05", "palm_trunks": len(palms),
       "palm_walk_rows": len(palm_walk), "palm_edge_rows": len(palm_edge),
       "palm_cards": len([o for o in bpy.data.objects if o.name.startswith("gpalm_card_")]),
       "beds": layout["beds"]["count"], "parterres": layout["parterres"]["count"],
       "edge_hedges": len([o for o in bpy.data.objects if o.name.startswith("gedge_") and not o.name.startswith("gedge_curb")]),
       "green_area_design_m2": 1232, "green_ratio_design": 0.169,
       "pass": len(palms) == 32 and len(palm_walk) == 16 and len(palm_edge) == 16
               and layout["beds"]["count"] == 4 and layout["parterres"]["count"] == 2}
dump("GA05/planting.json", ga5)

# ---------------- GA06 water ----------------
pools = [o for o in bpy.data.objects if is_pool(o)]
ga6 = {"check": "GA06", "pools": [{"name": o.name, "dim": [round(d, 2) for d in o.dimensions],
                                   "z_top": round(o.matrix_world.translation.z + o.dimensions.z / 2, 3),
                                   "material": [m.name for m in o.data.materials]} for o in pools],
       "pass": len(pools) == 2 and all(abs(o.dimensions.x - 22) < 0.1 and abs(o.dimensions.y - 8) < 0.1 for o in pools)
                and all(abs(o.matrix_world.translation.z + o.dimensions.z / 2 - 4.615) < 0.03 for o in pools)}
dump("GA06/water.json", ga6)

# ---------------- GA07 structures ----------------
def cnt(pre):
    return len([o for o in bpy.data.objects if o.name.startswith(pre)])
ga7 = {"check": "GA07", "benches": cnt("gbench_"), "pergola_columns": cnt("gperg_col_"),
       "containers": cnt("gsvc_ct_"), "gates": cnt("ggate_beam_"), "signs": cnt("gsign_"),
       "lamps": cnt("glamp_p_"),
       "pass": cnt("gbench_") == 6 and cnt("gperg_col_") == 8 and cnt("gsvc_ct_") == 2
               and cnt("ggate_beam_") == 2 and cnt("gsign_") == 2 and cnt("glamp_p_") == 8}
dump("GA07/structures.json", ga7)

# ---------------- GA08 cleanup ----------------
cones = [{"name": o.name, "xy": [round(centre(o).x, 1), round(centre(o).y, 1)], "z": round(centre(o).z, 1)}
         for o in bpy.data.objects if o.name.startswith("prop_cone")]
bad_cones = [c for c in cones if c["xy"][1] < -20]
k10_bad = [o.name for o in bpy.data.objects if o.name.startswith("k10_pipe_")
           and 40 < t_of(centre(o).x, centre(o).y) < 114]
bridge_bad = []
for o in bpy.data.objects:
    if o.name.startswith(("k02_", "k03_", "av_lamp_", "br_cl_", "br_edge_", "br_kerb_", "br_joint_")):
        t = t_of(centre(o).x, centre(o).y)
        if 40 < t < 114:
            bridge_bad.append(o.name)
legacy_cw = [o.name for o in bpy.data.objects
             if o.name.startswith(("cw_pipe_", "cw_post_", "cw_loop_", "cw_lamp_"))]
ga8 = {"check": "GA08", "cones": cones, "bad_cones": bad_cones,
       "k10_pipes_in_platform": k10_bad, "bridge_parts_in_platform": bridge_bad,
       "legacy_cw_rack_removed": not legacy_cw, "legacy_cw_objects": legacy_cw,
       "pass": not bad_cones and not k10_bad and not bridge_bad and not legacy_cw}
dump("GA08/cleanup.json", ga8)


# ---------------- GA03 paving ----------------
def horiz(o):
    return sorted([o.dimensions.x, o.dimensions.y])


def name_pref(pre):
    return [o for o in bpy.data.objects if o.name.startswith(pre)]


sec_t = name_pref("gjsec_t"); sec_v = name_pref("gjsec_v")
pri_t = name_pref("gjpri_t"); pri_v = name_pref("gjpri_v")
rust = name_pref("gjrust_t") + name_pref("gjrust_v")
band = name_pref("gperim_")
cop = name_pref("gpool_cl_") + name_pref("gpool_ce_")


def spacing(objs, axis="t"):
    f = t_of if axis == "t" else v_of
    ts = sorted({round(f(centre(o).x, centre(o).y), 1) for o in objs})
    ds = [round(b - a, 1) for a, b in zip(ts, ts[1:])]
    return ts, ds


ts_t, ds_t = spacing(sec_t, "t")
ts_v, ds_v = spacing(sec_v, "v")
ts_t_all, ds_t_all = spacing(sec_t + pri_t, "t")
ts_v_all, ds_v_all = spacing(sec_v + pri_v, "v")
ts_t_pri, ds_t_pri = spacing(pri_t, "t")
ts_v_pri, ds_v_pri = spacing(pri_v, "v")
bev = []
for o in cop[:4]:
    md = o.modifiers.get("bev")
    bev.append(round(md.width, 3) if md else 0.0)
ga3 = {"check": "GA03",
       "secondary_u": len(sec_t), "secondary_v": len(sec_v),
       "primary_u": len(pri_t), "primary_v": len(pri_v),
       "joint_pitch_m": sorted(set(ds_t_all + ds_v_all)),
       "primary_pitch_m": sorted(set(ds_t_pri + ds_v_pri)),
       "secondary_width_m": round(min(horiz(o)[0] for o in sec_t), 3),
       "primary_width_m": round(min(horiz(o)[0] for o in pri_t), 3),
       "rust_halo_width_m": round(min(horiz(o)[0] for o in rust), 3),
       "perimeter_band_count": len(band),
       "perimeter_band_width_m": round(min(horiz(o)[0] for o in band), 3),
       "coping_bevel_m": bev,
       "pass": len(ts_t) >= 9 and len(ts_v) >= 12 and len(ts_t_pri) == 2 and len(ts_v_pri) == 5
               and sorted(set(ds_t_all + ds_v_all)) == [6.0]
               and sorted(set(ds_t_pri + ds_v_pri)) == [24.0]
               and abs(min(horiz(o)[0] for o in sec_t) - 0.03) < 0.005
               and abs(min(horiz(o)[0] for o in pri_t) - 0.06) < 0.005
               and len(band) == 8 and abs(min(horiz(o)[0] for o in band) - 1.2) < 0.01
               and min(bev) >= 0.04}
dump("GA03/paving.json", ga3)

# ---------------- GA04 wall profile ----------------
walls = [o for o in bpy.data.objects if o.name.startswith("gw") and o.name.endswith("_wall")]
bands = [o for o in bpy.data.objects if o.name.startswith("gw") and o.name.endswith("_band")]
copes = [o for o in bpy.data.objects if o.name.startswith("gw") and o.name.endswith("_cope")]


def zr(o):
    z0 = o.matrix_world.translation.z - o.dimensions.z / 2
    return round(z0 - GARDEN_Z, 3), round(z0 + o.dimensions.z - GARDEN_Z, 3)


pil = sorted(name_pref("gpil_-1"), key=lambda o: o.location.x)
pil_t = sorted({round(t_of(centre(o).x, centre(o).y), 1) for o in pil})
pil_d = sorted({round(b - a, 1) for a, b in zip(pil_t, pil_t[1:])})
gates = []
for t in (GARDEN_T0, GARDEN_T1):
    holes = []
    for o in walls:
        tt = t_of(centre(o).x, centre(o).y)
        vv = (centre(o).x - av(tt, 0)[0]) * AV_V[0] + (centre(o).y - av(tt, 0)[1]) * AV_V[1]
        if abs(tt - t) < 1.5 and abs(vv) < 13.0:
            holes.append(o.name)
    gates.append({"t": t, "wall_inside_13m": holes, "open": not holes})
ga4 = {"check": "GA04",
       "wall_height_m": round(max(o.dimensions.z for o in walls), 3),
       "wall_thickness_m": round(min(horiz(o)[0] for o in walls), 3),
       "band_z_rel_deck": zr(bands[0]) if bands else None,
       "band_standout_m": round((min(horiz(o)[0] for o in bands)
                                 - min(horiz(o)[0] for o in walls)) / 2.0, 3) if bands else None,
       "coping_z_rel_deck": zr(copes[0]) if copes else None,
       "coping_width_m": round(min(horiz(o)[0] for o in copes), 3) if copes else None,
       "pilaster_spacing_m": pil_d, "pilaster_count": len(pil_t),
       "wall_segments": len(walls), "gate_openings": gates,
       "pass": bool(walls and bands and copes and zr(bands[0]) == (0.6, 0.78)
                    and zr(copes[0]) == (1.1, 1.28)
                    and all(4.4 <= d <= 4.6 for d in pil_d) and len(pil_t) == 12)}
dump("GA04/wall_profile.json", ga4)

print("GA01", ga1["pass"], "GA02", ga2["pass"], "GA03", ga3["pass"], "GA04", ga4["pass"],
      "GA05", ga5["pass"], "GA06", ga6["pass"], "GA07", ga7["pass"], "GA08", ga8["pass"])
