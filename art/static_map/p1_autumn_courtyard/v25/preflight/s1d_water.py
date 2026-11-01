# -*- coding: utf-8 -*-
"""S1D · 水面高度与颜色迭代：渲染值收敛到参考 (127,145,154)，B-R=27。"""
import json
import os

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
TMP = os.path.join(ROOT, "renders", "_s1d_tmp.png")
sc = bpy.context.scene
TARGET = (127, 145, 154)


def s2l(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def l2s(v):
    v = max(0.0, min(1.0, v))
    return 255.0 * (v * 12.92 if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055)


mat = bpy.data.materials.get("P1 pool water")
bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')

# 水面抬高，减少池壁自遮
water = bpy.data.objects.get("P1 pool | water surface")
if water:
    for v in water.data.vertices:
        v.co.z = -0.10
    water.data.update()

# 采样区：池心附近一小块（由射线确认的水面处）
SAMPLE = {"u": [0.435, 0.495], "v": [0.185, 0.215]}

sc.render.resolution_percentage = 25
sc.cycles.samples = 12
sc.render.filepath = TMP

log = []
for it in range(1, 4):
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(TMP, check_existing=False)
    W, H = img.size
    px = list(img.pixels)
    acc = [0.0, 0.0, 0.0]
    n = 0
    for y in range(int(H * SAMPLE["v"][0]), int(H * SAMPLE["v"][1])):
        for x in range(int(W * SAMPLE["u"][0]), int(W * SAMPLE["u"][1])):
            i = (y * W + x) * 4
            for c in range(3):
                acc[c] += px[i + c]
            n += 1
    cur = [l2s(a / n) for a in acc]
    bpy.data.images.remove(img)
    log.append({"iter": it, "srgb": [round(v, 1) for v in cur]})
    print(f"ITER {it}  ({cur[0]:.0f},{cur[1]:.0f},{cur[2]:.0f})  target {TARGET}")

    if abs(cur[1] - TARGET[1]) < 6 and abs(cur[2] - cur[0] - 27) < 8:
        break
    # 按通道比例修正基色（线性域）
    base = list(bsdf.inputs['Base Color'].default_value[:3])
    for c in range(3):
        ratio = TARGET[c] / max(1.0, cur[c])
        base[c] = max(0.0, min(1.0, base[c] * (ratio ** 0.85)))
    # 强制保持冷色关系：蓝最高、红最低
    lo = min(base)
    base[0] = lo * 0.92
    base[2] = min(1.0, lo * 1.35)
    bsdf.inputs['Base Color'].default_value = (base[0], base[1], base[2], 1.0)
    print("   base ->", [round(s2l(v) if False else l2s(v)) for v in base])

sc.render.resolution_percentage = 50
sc.cycles.samples = 24
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
json.dump({"target": TARGET, "iterations": log,
           "final_base": [round(v, 4) for v in bsdf.inputs['Base Color'].default_value[:3]]},
          open(os.path.join(PRE, "S1D_WATER.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("S1D_DONE")
