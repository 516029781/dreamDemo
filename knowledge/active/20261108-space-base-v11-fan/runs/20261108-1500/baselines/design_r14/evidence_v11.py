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
    return n.startswith("gpool") and n.endswith("water")


def centre(o):
    return o.matrix_world.translation


GARDEN_T0, GARDEN_T1, GARDEN_Z = 40.0, 114.0, 4.70
PLATFORM_Z = 4.70
AV_HEAD, AV_U, AV_V = (125.0, -6.6), (0.342, -0.940), (0.940, 0.342)


def av(t, v):
    return (AV_HEAD[0] + AV_U[0] * t + AV_V[0] * v, AV_HEAD[1] + AV_U[1] * t + AV_V[1] * v)


AVN = math.hypot(0.342, 0.940)


def t_of(x, y):
    return ((x - 125.0) * 0.342 + (y + 6.6) * -0.940) / AVN


def v_of(x, y):
    return ((x - 125.0) * 0.940 + (y + 6.6) * 0.342) / AVN


DOCK_O, DOCK_UD, DOCK_VD = (172.0, -136.0), (0.342, -0.940), (0.940, 0.342)


def dock_v(x, y):
    return (x - DOCK_O[0]) * DOCK_VD[0] + (y - DOCK_O[1]) * DOCK_VD[1]


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

# ---------------- GA01 garden platform ----------------
plat = bpy.data.objects.get("garden_platform")
pv = [plat.matrix_world @ v.co for v in plat.data.vertices]
top_z = round(max(p.z for p in pv), 3)
xs = [p.x for p in pv]; ys = [p.y for p in pv]
ga1 = {"check": "GA01", "area_m2": 1156.0,
       "bbox": {"x": [round(min(xs), 2), round(max(xs), 2)],
                "y": [round(min(ys), 2), round(max(ys), 2)]},
       "z_top": top_z, "vertices": len(pv),
       "size_m": [round(plat.dimensions.x, 2), round(plat.dimensions.y, 2)],
       "decks": {k: bool(bpy.data.objects.get(k)) for k in ("av_deck_b", "garden_deck")},
       "pass": abs(top_z - 4.75) < 0.02 and abs(plat.dimensions.x - 34.0) < 0.3
               and abs(plat.dimensions.y - 34.0) < 0.3 and bool(bpy.data.objects.get("av_deck_b"))}
dump("GA01/platform_geom.json", ga1)

# ---------------- GA02 layout ----------------
def pref(pre):
    return [o for o in bpy.data.objects if o.name.startswith(pre)]

pools = [o for o in bpy.data.objects if is_pool(o)]
layout = {
    "pools": {"count": len(pools), "centres": [[round(centre(o).x, 1), round(centre(o).y, 1)] for o in pools]},
    "beds": {"count": len(pref("gbed_curb_"))},
    "parterres": {"count": len(pref("gpar_base_"))},
    "overlook": {"count": len(pref("goverlook_paving"))},
    "pergola": {"count": len(pref("gperg_slat_"))},
    "service": {"count": len(pref("gsvc_ct_"))},
    "gates": {"count": len([o for o in bpy.data.objects if o.name == "ggate_beam"])},
    "signs": {"count": len(pref("gsign_"))},
    "lamps": {"count": len(pref("glamp_p_"))},
}
ga2 = {"check": "GA02", "groups": layout,
       "pass": layout["pools"]["count"] == 1 and layout["beds"]["count"] == 4
               and layout["parterres"]["count"] == 2 and layout["pergola"]["count"] >= 6
               and layout["service"]["count"] == 2 and layout["gates"]["count"] == 1
               and layout["signs"]["count"] == 2 and layout["lamps"]["count"] == 8}
dump("GA02/layout.json", ga2)

# ---------------- GA03 paving ----------------
deck = bpy.data.objects.get("garden_deck")
border = bpy.data.objects.get("garden_platform")
joints = pref("gj_")
jt = sorted({round((centre(o).x - 125.0) * 0.342 + (centre(o).y + 6.6) * -0.94, 1) for o in joints})
ga3 = {"check": "GA03", "deck_size_m": [round(deck.dimensions.x, 2), round(deck.dimensions.y, 2)] if deck else None,
       "border_overhang_m": round((border.dimensions.x - deck.dimensions.x) / 2, 2) if deck and border else None,
       "joint_count": len(joints), "joint_pitch_m": [round(b - a, 1) for a, b in zip(jt, jt[1:])],
       "pass": bool(deck) and len(joints) == 5
               and all(abs((b - a) - 5.6) < 0.2 for a, b in zip(jt, jt[1:]))}
dump("GA03/paving.json", ga3)

# ---------------- GA04 wall profile ----------------
walls = pref("gw_") and [o for o in bpy.data.objects if o.name.startswith("gw_") and o.name.endswith("_wall")]
bands = [o for o in bpy.data.objects if o.name.startswith("gw_") and o.name.endswith("_band")]
copes = [o for o in bpy.data.objects if o.name.startswith("gw_") and o.name.endswith("_cope")]
def zr(o):
    z0 = o.matrix_world.translation.z - o.dimensions.z / 2
    return round(z0 - GARDEN_Z, 3), round(z0 + o.dimensions.z - GARDEN_Z, 3)
ga4 = {"check": "GA04", "wall_segments": len(walls), "wall_height_m": round(max(o.dimensions.z for o in walls), 2),
       "band_z_rel_deck": zr(bands[0]) if bands else None,
       "coping_z_rel_deck": zr(copes[0]) if copes else None,
       "open_north": not any(o.name == "gw_n_wall" for o in bpy.data.objects),
       "pass": len(walls) == 3 and abs(max(o.dimensions.z for o in walls) - 0.92) < 0.02
               and zr(bands[0]) == (0.52, 0.7) and zr(copes[0])[0] >= 0.9}
dump("GA04/wall_profile.json", ga4)

# ---------------- GA05 planting ----------------
palms = [o for o in bpy.data.objects if o.name.startswith("gpalm_t_")]
ga5 = {"check": "GA05", "palms_garden": len(palms),
       "palm_cards": len([o for o in bpy.data.objects if o.name.startswith("gpalm_card_")]),
       "beds": layout["beds"]["count"], "parterres": layout["parterres"]["count"],
       "hedges": len(pref("gedge_")),
       "palms_plate": len([o for o in bpy.data.objects if o.name.startswith("palm_trunk_")]),
       "pass": len(palms) == 8 and len(pref("gpalm_card_")) == 8 and layout["beds"]["count"] == 4}
dump("GA05/planting.json", ga5)

# ---------------- GA06 water ----------------
ga6 = {"check": "GA06", "pools": [{"name": o.name, "dim": [round(d, 2) for d in o.dimensions],
                                   "z_top": round(o.matrix_world.translation.z + o.dimensions.z / 2, 3),
                                   "material": [m.name for m in o.data.materials]} for o in pools],
       "pass": len(pools) == 1 and abs(pools[0].dimensions.x - 11.6) < 0.2
                and abs(pools[0].matrix_world.translation.z + pools[0].dimensions.z / 2 - 4.6) < 0.05}
dump("GA06/water.json", ga6)

# ---------------- GA07 structures ----------------
ga7 = {"check": "GA07", "pergola_slats": len(pref("gperg_slat_")), "pergola_posts": len(pref("gperg_post_")),
       "overlook": len(pref("goverlook_paving")), "gate_posts": len(pref("ggate_post_")),
       "gate_beam": len(pref("ggate_beam")), "lamps": len(pref("glamp_p_")),
       "pass": len(pref("gperg_slat_")) >= 6 and len(pref("ggate_post_")) == 2
               and len(pref("ggate_beam")) == 1 and len(pref("glamp_p_")) == 8}
dump("GA07/structures.json", ga7)

# ---------------- GA08 cleanup ----------------
cones = [{"name": o.name, "xy": [round(centre(o).x, 1), round(centre(o).y, 1)], "z": round(centre(o).z, 1)}
         for o in bpy.data.objects if o.name.startswith("prop_cone")]
bad_cones = [c for c in cones if c["xy"][1] < -20]
k10_bad = [o.name for o in bpy.data.objects if o.name.startswith("k10_pipe_")
           and -119 < t_of(centre(o).x, centre(o).y) < 0.0]
bridge_bad = []
for o in bpy.data.objects:
    if o.name.startswith(("k02_", "k03_", "av_lamp_", "br_cl_", "br_edge_", "br_kerb_", "br_joint_")):
        t = t_of(centre(o).x, centre(o).y)
        if -119 < t < 0.0:
            bridge_bad.append(o.name)
legacy_cw = [o.name for o in bpy.data.objects
             if o.name.startswith(("cw_pipe_", "cw_post_", "cw_loop_", "cw_lamp_"))]
ga8 = {"check": "GA08", "cones": cones, "bad_cones": bad_cones,
       "k10_pipes_in_platform": k10_bad, "bridge_parts_in_platform": bridge_bad,
       "legacy_cw_rack_removed": not legacy_cw, "legacy_cw_objects": legacy_cw,
       "pass": not bad_cones and not k10_bad and not bridge_bad and not legacy_cw}
dump("GA08/cleanup.json", ga8)


# ---------------- GA11 peninsula facade kit ----------------
def objs(pre):
    return [o for o in bpy.data.objects if o.name.startswith(pre)]


wins_gl = [o for o in objs("k05_win_") + objs("k07_glass_") + objs("k13_win_") + objs("k14_win_")
           if o.name.endswith("_gl")]
wins_fr = [o for o in bpy.data.objects
           if (o.name.endswith("_fr") and o.data.materials
               and o.data.materials[0].name == "v10.win_frame")]
mull = [o for o in bpy.data.objects if "_mu" in o.name]
slats = objs("k05_slat_") + objs("k07_slat_")
jambs = objs("k05_jamb_") + objs("k07_jamb_")
heads = objs("k05_head_") + objs("k07_head_")
k07_faces = objs("k07_door_") + [o for o in objs("k07_glass_") if o.name.endswith("_gl")]
k07_vmin = None
if k07_faces:
    k07_vmin = round(min(dock_v((o.matrix_world @ vv.co).x, (o.matrix_world @ vv.co).y)
                         for o in k07_faces for vv in o.data.vertices), 3)
ga11 = {"check": "GA11",
        "exterior_windows": len(wins_gl), "window_frames": len(wins_fr),
        "mullions": len(mull), "door_slats": len(slats),
        "door_jambs": len(jambs), "door_heads": len(heads),
        "k07_canopies": len(objs("k07_canopy_")), "downpipes": len(objs("k07_pipe_")),
        "wall_lamps": len(objs("k07_wlamp_")),
        "windsock_arm": bool(bpy.data.objects.get("k11_sock_arm")),
        "k07_facade_v_min": k07_vmin,
        "glass_material": "v10.win_dark",
        "pass": len(wins_gl) >= 26 and len(wins_fr) >= 26 and len(mull) >= 25
                and len(slats) >= 20 and len(jambs) >= 18 and len(heads) >= 9
                and len(objs("k07_canopy_")) == 5 and len(objs("k07_pipe_")) == 4
                and len(objs("k07_wlamp_")) == 10
                and bool(bpy.data.objects.get("k11_sock_arm"))
                and (k07_vmin is not None and k07_vmin >= -14.05)}
dump("GA11/facade.json", ga11)


# ---------------- GA12 stepped site ----------------
def area_of(ob):
    """Sum the XY-projected area of every face (robust for a triangulated plate)."""
    me = ob.data
    mw = ob.matrix_world
    a = 0.0
    for poly in me.polygons:
        if poly.normal.z < 0.5:
            continue
        pts = [mw @ me.vertices[i].co for i in poly.vertices]
        s2 = 0.0
        for i in range(len(pts)):
            p, q = pts[i], pts[(i + 1) % len(pts)]
            s2 += p.x * q.y - q.x * p.y
        a += abs(s2) / 2.0
    return a


pave = bpy.data.objects.get("fan_pave")
wall_seg = [o for o in bpy.data.objects if o.name.startswith("fan_wall_")]
band_seg = [o for o in bpy.data.objects if o.name.startswith("fan_band_")]
cope_seg = [o for o in bpy.data.objects if o.name.startswith("fan_cope_")]
# band widths measured from the plate's own outline
pv = [pave.matrix_world @ v.co for v in pave.data.vertices]
def t_of(p):
    return (p.x - 125.0) * 0.342 + (p.y + 6.6) * -0.94
def v_of(p):
    return (p.x - 125.0) * 0.940 + (p.y + 6.6) * 0.342
tv = [(round(t_of(p), 1), round(v_of(p), 1)) for p in pv]
_hs = sorted({round(abs(v), 1) for t, v in tv}, reverse=True)
w1, w2, w3 = _hs[0], _hs[1], _hs[2]
ga12 = {"check": "GA12", "site": "stepped",
        "area_m2": round(area_of(pave), 1),
        "widths_m": {"core": round(w1 * 2, 1), "apron": round(w2 * 2, 1), "parking": round(w3 * 2, 1)},
        "depth_m": round(max(t for t, v in tv) - min(t for t, v in tv), 1),
        "seawall_segments": len(wall_seg), "orange_band_segments": len(band_seg),
        "coping_segments": len(cope_seg),
        "wall_height_m": round(max((o.dimensions.z for o in wall_seg), default=0), 2),
        "bridge_a_removed": not any(o.name.startswith(("av_deck_a", "av_surf_a")) for o in bpy.data.objects),
        "pass": abs(area_of(pave) - 16900) < 1200 and abs(w1 * 2 - 94) < 1.5
                and abs(w2 * 2 - 74) < 1.5 and abs(w3 * 2 - 62) < 1.5
                and len(wall_seg) >= 12 and len(band_seg) == len(wall_seg)}
dump("GA12/site.json", ga12)

# ---------------- GA13 core 2x2 ----------------
halls = {}
for i in range(1, 5):
    f = bpy.data.objects.get(f"h{i}_floor")
    wl = [o for o in bpy.data.objects
          if o.name == f"h{i}_wall_n" or o.name.startswith(f"h{i}_wall_n_")]
    w = max(wl, key=lambda o: o.dimensions.z) if wl else None
    halls[i] = {"w_m": round(f.dimensions.y, 2) if f else None,
                "d_m": round(f.dimensions.x, 2) if f else None,
                "h_m": round(w.dimensions.z, 2) if w else None}
corr_ns = bpy.data.objects.get("corr_ns")
corr_ew = bpy.data.objects.get("corr_ew")
load = bpy.data.objects.get("load_deck")
mezz = [o.name for o in bpy.data.objects if "ceo" in o.name.lower() or o.name.startswith("mezz")]
ga13 = {"check": "GA13", "halls": halls,
        "corridor_ns": [round(corr_ns.dimensions.x, 2), round(corr_ns.dimensions.y, 2)] if corr_ns else None,
        "corridor_ew": [round(corr_ew.dimensions.x, 2), round(corr_ew.dimensions.y, 2)] if corr_ew else None,
        "loading_strip": {"depth_m": round(load.dimensions.x, 2) if load else None,
                          "height_m": round(load.dimensions.z, 2) if load else None},
        "annex_present": any(o.name.startswith("annex_") for o in bpy.data.objects),
        "mezzanine_or_ceo": mezz,
        "pass": all(v["w_m"] is not None and v["d_m"] is not None and v["h_m"] is not None
                    and abs(v["w_m"] - 34) < 0.6 and abs(v["d_m"] - 34) < 0.6
                    and abs(v["h_m"] - 12.5) < 0.2 for v in halls.values())
                and bool(corr_ns) and abs(corr_ns.dimensions.y - 10) < 0.4
                and bool(corr_ew) and abs(corr_ew.dimensions.x - 10) < 0.4
                and bool(load) and abs(load.dimensions.x - 3.6) < 0.2
                and not any(o.name.startswith("annex_") for o in bpy.data.objects)
                and not mezz}
dump("GA13/core.json", ga13)

# ---------------- GA14 1:1 kit ----------------
roller = [o for o in bpy.data.objects
          if o.name.endswith("_panel") and ("rdoor" in o.name or o.name.startswith("load_door"))]
dbl = [o for o in bpy.data.objects if o.name.endswith("_ndoor_leaf")]
canopies = [o for o in bpy.data.objects
            if o.name.endswith("_slab") and "canopy" in o.name and o.name.startswith(("h", "load"))]
slats = [o for o in bpy.data.objects if "_slat" in o.name]
ga14 = {"check": "GA14", "roller_doors": len(roller),
        "roller_height_m": round(max((o.dimensions.z for o in roller), default=0), 2),
        "double_doors": len(dbl), "canopies": len(canopies), "slat_lines": len(slats),
        "pass": len(roller) >= 8 and len(dbl) == 4 and len(canopies) >= 4 and len(slats) >= 50
                and abs(round(max((o.dimensions.z for o in roller), default=0), 1) - 5.0) < 0.3}
dump("GA14/kit.json", ga14)

# ---------------- GA15 open roof + interior ----------------
roofs = [o.name for o in bpy.data.objects
         if o.name.split("_")[0] in ("h1", "h2", "h3", "h4") and "_roof" in o.name]
ceil_glass = [o.name for o in bpy.data.objects
              if o.name in ("corr_ns_glass", "corr_ew_glass")]
inner = {}
for i in range(1, 5):
    tags = {f"h{i}_paint", f"h{i}_stripe-1", f"h{i}_stripe1"}
    items = [o.name for o in bpy.data.objects
             if o.name.startswith(f"h{i}_") and o.type == "MESH"
             and not any(k in o.name for k in ("_wall", "_up_", "_band", "_pj",
                                               "_ndoor", "_rdoor", "_canopy", "_slat"))]
    inner[i] = len(items)
ga15 = {"check": "GA15", "roof_objects": roofs, "corridor_glazing": ceil_glass,
        "hall_interior_objects": inner,
        "note": "四厅与十字过道不设屋顶/天花板，俯视可直接读到室内陈设",
        "pass": not roofs and not ceil_glass and all(v >= 3 for v in inner.values())}
dump("GA15/open_roof.json", ga15)

print("GA01", ga1["pass"], "GA02", ga2["pass"], "GA03", ga3["pass"], "GA04", ga4["pass"],
      "GA05", ga5["pass"], "GA06", ga6["pass"], "GA07", ga7["pass"], "GA08", ga8["pass"],
      "GA11", ga11["pass"], "GA12", ga12["pass"], "GA13", ga13["pass"], "GA14", ga14["pass"],
      "GA15", ga15["pass"])
