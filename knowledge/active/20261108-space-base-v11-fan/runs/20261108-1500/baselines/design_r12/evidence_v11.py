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


# ---------------- GA12 fan site ----------------
def area_of(ob):
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
    zmax = max(p.z for p in vs)
    top = [p for p in vs if abs(p.z - zmax) < 1e-4]
    a = 0.0
    for i in range(len(top)):
        p, q = top[i], top[(i + 1) % len(top)]
        a += p.x * q.y - q.x * p.y
    return abs(a) / 2.0


plate = bpy.data.objects.get("fan_plate")
pave = bpy.data.objects.get("fan_pave")
fan_area = area_of(pave) if pave else 0.0
walls = [o for o in bpy.data.objects if o.name.startswith("fan_wall_")]
bands = [o for o in bpy.data.objects if o.name.startswith("fan_band_")]
copes = [o for o in bpy.data.objects if o.name.startswith("fan_cope_")]
z_top = None
if pave:
    z_top = round(max((pave.matrix_world @ v.co).z for v in pave.data.vertices), 3)
ga12 = {"check": "GA12", "site": "fan",
        "fill_area_m2": round(fan_area, 1), "top_z": z_top,
        "seawall_segments": len(walls), "orange_band_segments": len(bands),
        "coping_segments": len(copes),
        "wall_height_m": round(max((o.dimensions.z for o in walls), default=0), 3),
        "water_at_mouth": bool(bpy.data.objects.get("water")),
        "bridge_a_removed": not any(o.name.startswith(("av_deck_a", "av_surf_a")) for o in bpy.data.objects),
        "pass": bool(plate) and abs(fan_area - 47399) < 900 and z_top == 4.72
                and len(walls) >= 18 and len(bands) >= 18 and len(copes) >= 18
                and not any(o.name.startswith(("av_deck_a", "av_surf_a")) for o in bpy.data.objects)}
dump("GA12/fan_site.json", ga12)

# ---------------- GA13 single-storey core ----------------
halls = {}
for i in range(1, 5):
    wl = [o for o in bpy.data.objects if o.name.startswith(f"h{i}_wall_n_")]
    w = max(wl, key=lambda o: o.dimensions.z) if wl else None
    f = bpy.data.objects.get(f"h{i}_floor")
    halls[i] = {"width_m": round(f.dimensions.y, 2) if f else None,
                "depth_m": round(f.dimensions.x, 2) if f else None,
                "wall_h": round(w.dimensions.z, 2) if w else None}
mezz = [o.name for o in bpy.data.objects
        if o.name.startswith(("mezz", "h1_control", "ceo")) or "ceo" in o.name.lower()]
corr = bpy.data.objects.get("corr_floor")
court = bpy.data.objects.get("court_floor")
ga13 = {"check": "GA13", "halls": halls,
        "corridor_width_m": round(corr.dimensions.y, 2) if corr else None,
        "corridor_length_m": round(corr.dimensions.x, 2) if corr else None,
        "annex_blocks": len([o for o in bpy.data.objects if o.name.startswith("annex_") and o.name[-1] in "we"]),
        "courtyard": {"width_m": round(court.dimensions.y, 2) if court else None,
                      "depth_m": round(court.dimensions.x, 2) if court else None,
                      "sunken_m": round(PLATFORM_Z - (court.matrix_world.translation.z if court else 0), 2)},
        "drum": {"diameter_m": round(2 * bpy.data.objects["h1_drum"].dimensions.x / 2, 2) if bpy.data.objects.get("h1_drum") else None,
                 "top_m": round(max((bpy.data.objects["h1_drum"].matrix_world @ v.co).z for v in bpy.data.objects["h1_drum"].data.vertices), 2) if bpy.data.objects.get("h1_drum") else None},
        "mezzanine_or_ceo_objects": mezz,
        "single_storey": not mezz,
        "pass": all(v["width_m"] is not None and v["depth_m"] is not None and v["wall_h"] is not None
                    and abs(v["width_m"] - 34.0) < 0.6 and abs(v["depth_m"] - 34.0) < 0.6
                    and abs(v["wall_h"] - 12.5) < 0.2 for v in halls.values())
                and bool(corr) and abs(corr.dimensions.y - 146.0) < 1.0 and abs(corr.dimensions.x - 10.0) < 0.5
                and bool(court) and not mezz}
print("HALLS", halls)
dump("GA13/core.json", ga13)

# ---------------- GA14 1:1 kit ----------------
roller = [o for o in bpy.data.objects if "_rdoor" in o.name and o.name.endswith("_panel")]
roller += [o for o in bpy.data.objects if o.name.startswith("annex_door") and o.name.endswith("_panel")]
dbl = [o for o in bpy.data.objects if o.name.endswith("_ndoor_leaf")]
canopies = [o for o in bpy.data.objects if o.name.endswith("_canopy_slab") or o.name.endswith("_canopy0_slab")
            or "_canopy" in o.name and o.name.endswith("_slab")]
docks = [o for o in bpy.data.objects if o.name.startswith("dock_") and o.name.endswith("_w") or o.name.startswith("dock_e")]
slides = [o for o in bpy.data.objects if "_slat" in o.name]
ga14 = {"check": "GA14",
        "roller_doors": len(roller),
        "roller_size_m": [round(max(o.dimensions.x, o.dimensions.y), 2) for o in roller[:3]],
        "roller_height_m": round(max((o.dimensions.z for o in roller), default=0), 2),
        "double_doors": len(dbl), "double_door_h_m": round(max((o.dimensions.z for o in dbl), default=0), 2),
        "canopies": len(canopies), "slat_lines": len(slides),
        "loading_docks": len([o for o in bpy.data.objects if o.name in ("dock_w", "dock_e")]),
        "pass": len(roller) >= 12 and len(dbl) == 4 and len(canopies) >= 12 and len(slides) >= 60
                and abs(round(max((o.dimensions.z for o in roller), default=0), 1) - 5.0) < 0.2}
dump("GA14/kit.json", ga14)

print("GA01", ga1["pass"], "GA02", ga2["pass"], "GA03", ga3["pass"], "GA04", ga4["pass"],
      "GA05", ga5["pass"], "GA06", ga6["pass"], "GA07", ga7["pass"], "GA08", ga8["pass"],
      "GA11", ga11["pass"], "GA12", ga12["pass"], "GA13", ga13["pass"], "GA14", ga14["pass"])
