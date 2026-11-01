# -*- coding: utf-8 -*-
"""B0 背景空间结构：挡墙抬高 + 水面延伸（自收敛）+ 岸线建立。

核心：射线不需要渲染，改几何后 view_layer.update() 即可 ray_cast，
因此 y 的收敛在**单个 blender 进程内**完成，秒级，不需要反复渲染。

用法：
    blender -b scene.blend -P preflight/b0_autumn.py -- \
        --target-v 0.10 --water-start 22.0 --wall-z 0.30

输出：preflight/B0_LOCK.json（含实测 v、锁定 y、收敛轮次）
"""
import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene
cam = sc.camera

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--target-v", type=float, default=0.10, help="水面上缘目标 v")
ap.add_argument("--water-start", type=float, default=22.0)
ap.add_argument("--wall-z", type=float, default=0.30)
ap.add_argument("--edge-z", type=float, default=0.35)
ap.add_argument("--edge-depth", type=float, default=0.5)
ap.add_argument("--tol", type=float, default=0.01)
ap.add_argument("--max-iter", type=int, default=6)
ap.add_argument("--dry-run", action="store_true")
args = ap.parse_args(argv)

tv = (cam.data.sensor_width / 2) / cam.data.lens * (sc.render.resolution_y / sc.render.resolution_x) * 2
tv = (18.0 / cam.data.lens) * (1078 / 1920)
fr = cam.data.view_frame(scene=sc)
tr, br, bl, tl = fr


def cam_dir(u, v):
    top = tl.lerp(tr, u)
    bot = bl.lerp(br, u)
    p = top.lerp(bot, v)
    return (cam.matrix_world.to_quaternion() @ p).normalized()


def ray_at(v, u=0.5):
    dg = bpy.context.evaluated_depsgraph_get()
    o = cam.matrix_world.translation
    hit, loc, nor, idx, ob, mtx = sc.ray_cast(dg, o, cam_dir(u, v))
    return (ob.name if hit else None), (loc.copy() if hit else None)


def water_top_v():
    """扫描水面上缘：从 v=0 向下，返回第一次命中水面的 v（即上缘）。"""
    WNAME = "M01W"
    for i in range(0, 401):
        v = i / 1000.0
        name, _ = ray_at(v)
        if name and name.startswith(WNAME):
            return v
    return None


def set_water_far(y, y_near=15.5):
    """把水面远端顶点拉到 y，近端拉到 y_near（近端必须在挡墙外侧，否则水会被墙切开）。

    注意：不能写 `if w.y > y` —— 原远端只有 18.5，比目标 22 小，条件永远不成立。
    正确做法：找出 y 最大的那批顶点当作远端。
    """
    for ob in sc.objects:
        if not ob.name.startswith("M01W"):
            continue
        me = ob.data
        inv = ob.matrix_world.inverted()
        ws = [ob.matrix_world @ v.co for v in me.vertices]
        if not ws:
            continue
        ymax = max(w.y for w in ws)
        ymin = min(w.y for w in ws)
        for vert, w in zip(me.vertices, ws):
            tgt = None
            if abs(w.y - ymax) < 1e-3:
                tgt = y
            elif abs(w.y - ymin) < 1e-3:
                tgt = y_near
            if tgt is not None:
                vert.co = inv @ Vector((w.x, tgt, w.z))
        me.update()


log = {"steps": [], "iterations": [], "lock": {}}

# ---------- 1. 挡墙抬高 ----------
for ob in sc.objects:
    if not ob.name.startswith("T01 | far retaining"):
        continue
    me = ob.data
    inv = ob.matrix_world.inverted()
    zs = [(ob.matrix_world @ v.co).z for v in me.vertices]
    if not zs:
        continue
    zmax = max(zs)
    if zmax >= args.wall_z - 1e-4:
        continue
    for vert in me.vertices:
        w = ob.matrix_world @ vert.co
        vert.co = inv @ Vector((w.x, w.y, args.wall_z))
    me.update()
    log["steps"].append({"op": "wall_raise", "obj": ob.name, "zmax_before": round(zmax, 3),
                         "zmax_after": args.wall_z})

bpy.context.view_layer.update()

# ---------- 2. 水面延伸：单进程内收敛 ----------
y = args.water_start
best = None
for it in range(1, args.max_iter + 1):
    set_water_far(y)
    bpy.context.view_layer.update()
    v = water_top_v()
    log["iterations"].append({"iter": it, "far_y": round(y, 2),
                              "water_top_v": None if v is None else round(v, 4)})
    if v is None:
        y -= 2.0
        continue
    err = v - args.target_v
    if abs(err) <= args.tol:
        best = (y, v)
        break
    # v 偏大（水面够高但没到目标）→ 继续延伸；v 偏小（过了）→ 回退
    y += 1.5 if err > 0 else -1.0
    best = (y, v)

if best is None:
    log["lock"] = {"status": "failed", "reason": "no convergence"}
else:
    log["lock"] = {"status": "ok", "water_far_y": round(best[0], 2),
                   "water_top_v": round(best[1], 4), "target_v": args.target_v}

# ---------- 3. 岸线 ----------
EDGE = "P1 far shore edge"
old = bpy.data.objects.get(EDGE)
if old:
    bpy.data.objects.remove(old, do_unlink=True)

if best and not args.dry_run:
    y_far = best[0]
    y0, y1 = y_far, y_far + args.edge_depth
    x0, x1 = -20.0, 20.0
    ztop, zbot = args.edge_z, -0.30
    verts = [
        (x0, y0, zbot), (x1, y0, zbot), (x1, y0, ztop), (x0, y0, ztop),
        (x0, y1, ztop), (x1, y1, ztop),
    ]
    faces = [(0, 1, 2, 3), (3, 2, 5, 4), (0, 3, 4), (1, 5, 2)]
    me = bpy.data.meshes.new(EDGE)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(EDGE, me)
    sc.collection.objects.link(ob)
    ob.parent = cam
    ob.matrix_parent_inverse.identity()

    mat = bpy.data.materials.get("P1 far shore edge mat") or bpy.data.materials.new("P1 far shore edge mat")
    mat.use_nodes = True
    bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.30, 0.26, 0.20, 1)
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = 0.92
    ob.data.materials.append(mat)
    ob.visible_shadow = False
    log["steps"].append({"op": "shore_edge", "obj": EDGE,
                         "y": [round(y0, 2), round(y1, 2)], "z_top": ztop})

# ---------- 4. 删残留 ----------
# v16 far garden 是 46.5 m 的旧地形片，正好挡住 v0-4%，必须清掉
for kw in ("V18 B13", "Soft blue distant ridge", "V18 B04",
           "v16 far garden", "v16 gap tree"):
    for ob in list(sc.objects):
        if ob.name.startswith(kw):
            log["steps"].append({"op": "remove", "obj": ob.name})
            bpy.data.objects.remove(ob, do_unlink=True)

if not args.dry_run:
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))

with open(os.path.join(PRE, "B0_LOCK.json"), "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=1)

print("=== B0 ===")
for it in log["iterations"]:
    print("  iter", it)
print("LOCK", json.dumps(log["lock"], ensure_ascii=False))
