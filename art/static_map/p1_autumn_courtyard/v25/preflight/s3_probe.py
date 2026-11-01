# -*- coding: utf-8 -*-
"""S3 前置探查：① 机位/灯光 ② v44-50 带命中 ③ 可用中景资产清单。"""
import json
import os

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene
cam = sc.camera

out = {}

# ---- 1. 相机与灯 ----
out["camera"] = {
    "loc": [round(c, 3) for c in cam.matrix_world.translation],
    "rot_x": round(cam.rotation_euler[0], 8),
    "lens": cam.data.lens,
}
out["render"] = {
    "res": [sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage],
    "samples": sc.cycles.samples,
    "view_transform": sc.view_settings.view_transform,
    "exposure": round(sc.view_settings.exposure, 3),
}
lights = []
for ob in bpy.data.objects:
    if ob.type != 'LIGHT':
        continue
    d = (ob.matrix_world.to_quaternion() @ Vector((0, 0, -1)))
    lights.append({
        "name": ob.name, "type": ob.data.type,
        "energy": round(ob.data.energy, 2),
        "dir": [round(c, 3) for c in d],
        "loc": [round(c, 3) for c in ob.matrix_world.translation],
        "shadow": ob.data.use_shadow,
    })
out["lights"] = lights

# ---- 2. 射线：u 网格 × v 44-52 ----
fr = cam.data.view_frame(scene=sc)
tr, br, bl, tl = fr
o = cam.matrix_world.translation
quat = cam.matrix_world.to_quaternion()


def direction(u, v):
    top = tl.lerp(tr, u)
    bot = bl.lerp(br, u)
    p = top.lerp(bot, v)
    return (quat @ p).normalized()


dg = bpy.context.evaluated_depsgraph_get()
rows = []
for ui in range(1, 20):
    u = ui / 20.0
    for vi in range(0, 61):
        v = vi / 100.0
        hit, loc, nor, idx, ob, mtx = sc.ray_cast(dg, o, direction(u, v))
        if hit:
            rows.append([round(u, 3), round(v, 3), ob.name,
                         round((loc - o).length, 1),
                         [round(c, 2) for c in loc]])
        else:
            rows.append([round(u, 3), round(v, 3), None, None, None])
out["rays"] = rows

# 每 2% 带的命中构成
comp = {}
for u, v, name, dist, loc in rows:
    b = int(v * 100) // 2 * 2
    key = "%02d-%02d" % (b, b + 2)
    comp.setdefault(key, {}).setdefault(name or "---", 0)
    comp[key][name or "---"] += 1
out["band_comp"] = {k: dict(sorted(v.items(), key=lambda x: -x[1])[:6]) for k, v in comp.items()}

# ---- 3. 中景可用资产 ----
cands = []
for ob in bpy.data.objects:
    if ob.type not in {'MESH', 'CURVE'}:
        continue
    if ob.hide_render or ob.hide_viewport:
        continue
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    xs = [p.x for p in bb]; ys = [p.y for p in bb]; zs = [p.z for p in bb]
    x0, x1 = min(xs), max(xs); y0, y1 = min(ys), max(ys); z0, z1 = min(zs), max(zs)
    if not (y1 > 0.3 and y0 < 6.0):
        continue
    if not (z1 > 0.6 and z0 < 3.2):
        continue
    if x1 < -14 or x0 > 14:
        continue
    cands.append({
        "name": ob.name, "type": ob.type,
        "bbox": [round(x0, 2), round(x1, 2), round(y0, 2), round(y1, 2), round(z0, 2), round(z1, 2)],
        "size": [round(x1 - x0, 2), round(y1 - y0, 2), round(z1 - z0, 2)],
        "polys": len(ob.data.polygons) if ob.type == 'MESH' else 0,
        "mats": [m.name for m in ob.data.materials if m][:3] if hasattr(ob.data, "materials") else [],
        "parent": ob.parent.name if ob.parent else None,
    })
cands.sort(key=lambda c: -c["size"][0] * c["size"][1])
out["midground_candidates"] = cands

with open(os.path.join(PRE, "S3_PROBE.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("=== CAM ===", out["camera"])
print("=== LIGHTS ===")
for l in lights:
    print("  %-34s %-6s E=%-8s dir=%s" % (l["name"], l["type"], l["energy"], l["dir"]))
print("=== BAND COMP v36-52 ===")
for k in sorted(comp):
    if 36 <= int(k[:2]) <= 52:
        print(" ", k, out["band_comp"][k])
print("=== MIDGROUND CANDIDATES ===", len(cands))
for c in cands[:40]:
    print("  %-46s %s p=%d %s" % (c["name"][:46], c["bbox"], c["polys"], c["mats"][:1]))
print("S3_PROBE_DONE")
