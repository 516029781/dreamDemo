# -*- coding: utf-8 -*-
"""射线验收：沿画面中线扫描，输出每层命中、深度单调性、接触边、空洞。

用法：
    blender -b scene.blend -P preflight/raycheck.py -- --step 0.005
输出：preflight/RAYCHECK.json + 控制台表格
"""
import argparse
import json
import os
import sys

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene
cam = sc.camera

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--step", type=float, default=0.005)
ap.add_argument("--u", type=float, default=0.5)
ap.add_argument("--vmax", type=float, default=0.35)
args = ap.parse_args(argv)

fr = cam.data.view_frame(scene=sc)
tr, br, bl, tl = fr


def direction(u, v):
    top = tl.lerp(tr, u)
    bot = bl.lerp(br, u)
    p = top.lerp(bot, v)
    return (cam.matrix_world.to_quaternion() @ p).normalized()


dg = bpy.context.evaluated_depsgraph_get()
o = cam.matrix_world.translation

rows = []
# 从画面内侧 0.2% 起采样：v=0 正好落在景片边界上，射线会因浮点精度漏掉，
# 那是采样假象，不是真空洞。真实渲染的边界风险已由景片 8% 过覆盖兜住。
v = 0.002
while v <= args.vmax + 1e-9:
    d = direction(args.u, v)
    hit, loc, nor, idx, ob, mtx = sc.ray_cast(dg, o, d)
    if hit:
        mats = [m.name for m in ob.data.materials if m] if hasattr(ob.data, "materials") else []
        rows.append({"v": round(v, 4), "object": ob.name,
                     "dist": round((loc - o).length, 2),
                     "world": [round(c, 2) for c in loc], "mats": mats[:3]})
    else:
        rows.append({"v": round(v, 4), "object": None, "dist": None})
    v += args.step

# 统计
holes = [r for r in rows if r["object"] is None]

# 深度单调性：只校验「背景层序列」，即距离 ≥ BG_MIN_DIST 的连续命中。
# 24 m 的龙门架、25 m 的草簇是前景遮挡，本来就会打断单调，把它们算进来
# 会把一个正确场景判成失败（v1 就踩过这个坑）。
BG_VMAX = 0.16  # 背景带只到 16%：再往下是广场地面板块，属前景结构
BG_MIN_DIST = 30.0
bg_dists = [(r["v"], r["dist"]) for r in rows
            if r["dist"] and r["v"] <= BG_VMAX and r["dist"] >= BG_MIN_DIST]
mono_viol = []
# 容差 1.5 m：相邻构件（岸 cap 35.77 / 侧墙 36.07）本就近共面，
# 差 0.3 m 不该判成"深度反了"。只有 >1.5 m 的逆向跳变才算真错。
for i in range(1, len(bg_dists)):
    if bg_dists[i][1] > bg_dists[i - 1][1] + 1.5:
        mono_viol.append(bg_dists[i][0])

groups = []
for r in rows:
    key = r["object"] or "---"
    if groups and groups[-1]["object"] == key:
        groups[-1]["v_hi"] = r["v"]
    else:
        groups.append({"object": key, "v_lo": r["v"], "v_hi": r["v"],
                       "dist": r["dist"]})

# 关键接触边
def find(prefix):
    for g in groups:
        if g["object"] and g["object"].startswith(prefix):
            return g
    return None

checks = {
    "no_holes": len(holes) == 0,
    "depth_monotonic": len(mono_viol) == 0,
    "E2_wall": find("T01 | far retaining") is not None,
    "E3_edge": find("P1 far shore edge") is not None,
    "water_present": find("M01W") is not None,
}
if find("M01W"):
    w = find("M01W")
    checks["water_thickness_pp"] = round((w["v_hi"] - w["v_lo"]) * 100, 1)

out = {"u": args.u, "step": args.step, "groups": groups,
       "holes": [round(h["v"], 3) for h in holes],
       "monotonic_violations": [round(x, 3) for x in mono_viol],
       "checks": checks}

with open(os.path.join(PRE, "RAYCHECK.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("=== 分层（v 从高到低）===")
for g in groups:
    print(f'  {g["v_hi"]*100:6.1f}% → {g["v_lo"]*100:6.1f}%  {g["object"][:46]:48s} d={g["dist"]}')
print("=== CHECKS ===")
for k, val in checks.items():
    print(f"  {k}: {val}")
if holes:
    print("  HOLES at v:", [round(h["v"], 3) for h in holes[:12]])
