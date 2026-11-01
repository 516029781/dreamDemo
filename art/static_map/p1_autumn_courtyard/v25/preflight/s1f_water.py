# -*- coding: utf-8 -*-
"""S1F · 水面定色：基色 + 少量自发光，压住暖光高光，收敛到 (127,145,154)。"""
import json
import os

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
MASK = os.path.join(ROOT, "renders", "_s1f_mask.png")
TMP = os.path.join(ROOT, "renders", "_s1f_tmp.png")
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

lin = tuple(s2l(c) for c in TARGET)
bsdf.inputs['Base Color'].default_value = (*lin, 1.0)
for k, v in [('Roughness', 0.62), ('Metallic', 0.0), ('IOR', 1.20)]:
    if k in bsdf.inputs:
        bsdf.inputs[k].default_value = v
if 'Specular IOR Level' in bsdf.inputs:
    bsdf.inputs['Specular IOR Level'].default_value = 0.08
if 'Emission Color' in bsdf.inputs:
    bsdf.inputs['Emission Color'].default_value = (*lin, 1.0)
if 'Emission Strength' in bsdf.inputs:
    bsdf.inputs['Emission Strength'].default_value = 0.55

sc.render.resolution_percentage = 25
sc.cycles.samples = 8

# 遮罩
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
mask_idx = [(x, y) for y in range(H) for x in range(W)
            if px[(y * W + x) * 4] > 0.25 and px[(y * W + x) * 4 + 2] > 0.25
            and px[(y * W + x) * 4 + 1] < 0.25]
bpy.data.images.remove(img)
xs = [p[0] for p in mask_idx]; ys = [p[1] for p in mask_idx]
print("MASK %d px  u[%.3f,%.3f] v[%.3f,%.3f]" % (len(mask_idx), min(xs) / W, max(xs) / W,
                                                1 - max(ys) / H, 1 - min(ys) / H))
nt.links.new(old_link, out.inputs['Surface'])
nt.nodes.remove(emis)

sc.render.filepath = TMP
log = []
for it in range(1, 4):
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(TMP, check_existing=False)
    px = list(img.pixels)
    acc = [0.0, 0.0, 0.0]; n = 0
    for (x, y) in mask_idx[::2]:
        i = (y * W + x) * 4
        for c in range(3):
            acc[c] += px[i + c]
        n += 1
    bpy.data.images.remove(img)
    cur = [l2s(a / n) for a in acc]
    log.append({"iter": it, "srgb": [round(v, 1) for v in cur]})
    print(f"ITER {it} ({cur[0]:.0f},{cur[1]:.0f},{cur[2]:.0f}) B-R={cur[2]-cur[0]:.0f}")
    if abs(cur[2] - cur[0] - 27) < 6 and abs(cur[1] - TARGET[1]) < 8:
        print("CONVERGED")
        break
    # 调整自发光强度：偏暗就加，偏亮就减
    s = bsdf.inputs['Emission Strength'].default_value
    lum_cur = 0.299 * cur[0] + 0.587 * cur[1] + 0.114 * cur[2]
    lum_tgt = 0.299 * TARGET[0] + 0.587 * TARGET[1] + 0.114 * TARGET[2]
    s = max(0.0, min(1.5, s * (lum_tgt / max(1.0, lum_cur)) ** 0.7))
    bsdf.inputs['Emission Strength'].default_value = s
    # 冷味不足则把基色蓝度再拉高
    if cur[2] - cur[0] < 20:
        b = list(bsdf.inputs['Base Color'].default_value[:3])
        b[0] *= 0.90; b[2] = min(1.0, b[2] * 1.10)
        bsdf.inputs['Base Color'].default_value = (b[0], b[1], b[2], 1.0)
        ec = list(bsdf.inputs['Emission Color'].default_value[:3])
        ec[0] *= 0.90; ec[2] = min(1.0, ec[2] * 1.10)
        bsdf.inputs['Emission Color'].default_value = (ec[0], ec[1], ec[2], 1.0)

sc.render.resolution_percentage = 50
sc.cycles.samples = 24
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
json.dump({"target": TARGET, "mask_px": len(mask_idx), "iterations": log,
           "emission_strength": round(bsdf.inputs['Emission Strength'].default_value, 3)},
          open(os.path.join(PRE, "S1F_WATER.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("S1F_DONE")
