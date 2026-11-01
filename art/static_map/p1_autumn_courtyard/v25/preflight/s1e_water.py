# -*- coding: utf-8 -*-
"""S1E · 用水面遮罩（自发光）定位水面像素，再做颜色迭代。"""
import json
import os

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
MASK = os.path.join(ROOT, "renders", "_s1e_mask.png")
TMP = os.path.join(ROOT, "renders", "_s1e_tmp.png")
sc = bpy.context.scene
TARGET = (127, 145, 154)


def s2l(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def l2s(v):
    v = max(0.0, min(1.0, v))
    return 255.0 * (v * 12.92 if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055)


mat = bpy.data.materials.get("P1 pool water")
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')

# 恢复一个合理的起点：目标色
bsdf.inputs['Base Color'].default_value = (s2l(TARGET[0]), s2l(TARGET[1]), s2l(TARGET[2]), 1.0)

sc.render.resolution_percentage = 25
sc.cycles.samples = 8

# ---- 1. 遮罩渲染 ----
emis = nt.nodes.new('ShaderNodeEmission')
emis.inputs['Color'].default_value = (1.0, 0.0, 1.0, 1.0)
emis.inputs['Strength'].default_value = 3.0
old_link = out.inputs['Surface'].links[0].from_socket
nt.links.new(emis.outputs['Emission'], out.inputs['Surface'])
sc.render.filepath = MASK
bpy.ops.render.render(write_still=True)
img = bpy.data.images.load(MASK, check_existing=False)
W, H = img.size
px = list(img.pixels)
mask_idx = []
for y in range(H):
    for x in range(W):
        i = (y * W + x) * 4
        r, g, b = px[i], px[i + 1], px[i + 2]
        if r > 0.25 and b > 0.25 and g < 0.25:
            mask_idx.append((x, y))
bpy.data.images.remove(img)
print("MASK_PIXELS", len(mask_idx), "of", W * H)
if mask_idx:
    xs = [p[0] for p in mask_idx]; ys = [p[1] for p in mask_idx]
    print("MASK_BBOX u[%.3f,%.3f] v[%.3f,%.3f]" % (min(xs) / W, max(xs) / W,
                                                   1 - max(ys) / H, 1 - min(ys) / H))

# 恢复水面 shader
nt.links.new(old_link, out.inputs['Surface'])
nt.nodes.remove(emis)

# ---- 2. 迭代 ----
sc.render.filepath = TMP
log = []
for it in range(1, 5):
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(TMP, check_existing=False)
    px = list(img.pixels)
    acc = [0.0, 0.0, 0.0]
    n = 0
    for (x, y) in mask_idx[::3]:
        i = (y * W + x) * 4
        for c in range(3):
            acc[c] += px[i + c]
        n += 1
    bpy.data.images.remove(img)
    cur = [l2s(a / n) for a in acc]
    log.append({"iter": it, "srgb": [round(v, 1) for v in cur]})
    print(f"ITER {it} ({cur[0]:.0f},{cur[1]:.0f},{cur[2]:.0f}) B-R={cur[2]-cur[0]:.0f}")
    if abs(cur[1] - TARGET[1]) < 7 and abs(cur[2] - cur[0] - 27) < 9:
        print("CONVERGED")
        break
    base = list(bsdf.inputs['Base Color'].default_value[:3])
    for c in range(3):
        ratio = TARGET[c] / max(1.0, cur[c])
        base[c] = max(0.0, min(1.0, base[c] * (ratio ** 0.8)))
    bsdf.inputs['Base Color'].default_value = (base[0], base[1], base[2], 1.0)

sc.render.resolution_percentage = 50
sc.cycles.samples = 24
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
json.dump({"target": TARGET, "mask_px": len(mask_idx), "iterations": log,
           "final_base": [round(v, 4) for v in bsdf.inputs['Base Color'].default_value[:3]]},
          open(os.path.join(PRE, "S1E_WATER.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("S1E_DONE")
