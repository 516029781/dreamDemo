# -*- coding: utf-8 -*-
"""S1G · 从当前状态继续收敛水面（更强的亮度/色相修正）。"""
import json
import os

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
TMP = os.path.join(ROOT, "renders", "_s1g_tmp.png")
sc = bpy.context.scene
TARGET = (127, 145, 154)
LUMT = 0.299 * 127 + 0.587 * 145 + 0.114 * 154

mat = bpy.data.materials.get("P1 pool water")
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')


def l2s(v):
    v = max(0.0, min(1.0, v))
    return 255.0 * (v * 12.92 if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055)


sc.render.resolution_percentage = 20
sc.cycles.samples = 6

emis = nt.nodes.new('ShaderNodeEmission')
emis.inputs['Color'].default_value = (1.0, 0.0, 1.0, 1.0)
emis.inputs['Strength'].default_value = 3.0
old_link = out.inputs['Surface'].links[0].from_socket
nt.links.new(emis.outputs['Emission'], out.inputs['Surface'])
sc.render.filepath = os.path.join(ROOT, "renders", "_s1g_mask.png")
bpy.ops.render.render(write_still=True)
img = bpy.data.images.load(sc.render.filepath, check_existing=False)
W, H = img.size
px = list(img.pixels)
mask = [(x, y) for y in range(H) for x in range(W)
        if px[(y * W + x) * 4] > 0.25 and px[(y * W + x) * 4 + 2] > 0.25 and px[(y * W + x) * 4 + 1] < 0.25]
bpy.data.images.remove(img)
nt.links.new(old_link, out.inputs['Surface'])
nt.nodes.remove(emis)
print("MASK", len(mask))

sc.render.filepath = TMP
log = []
for it in range(1, 6):
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(TMP, check_existing=False)
    px = list(img.pixels)
    acc = [0.0, 0.0, 0.0]; n = 0
    for (x, y) in mask[::2]:
        i = (y * W + x) * 4
        for c in range(3):
            acc[c] += px[i + c]
        n += 1
    bpy.data.images.remove(img)
    cur = [l2s(a / n) for a in acc]
    lum = 0.299 * cur[0] + 0.587 * cur[1] + 0.114 * cur[2]
    log.append({"iter": it, "srgb": [round(v, 1) for v in cur], "B-R": round(cur[2] - cur[0], 1)})
    print(f"ITER {it} ({cur[0]:.0f},{cur[1]:.0f},{cur[2]:.0f}) B-R={cur[2]-cur[0]:.0f} lum={lum:.0f} tgt={LUMT:.0f}")
    if abs(lum - LUMT) < 8 and abs(cur[2] - cur[0] - 27) < 5:
        print("CONVERGED")
        break
    k = (LUMT / max(1.0, lum)) ** 1.25
    for sock in ('Base Color', 'Emission Color'):
        c = list(bsdf.inputs[sock].default_value[:3])
        c = [max(0.0, min(1.0, v * k)) for v in c]
        bsdf.inputs[sock].default_value = (c[0], c[1], c[2], 1.0)
    if cur[2] - cur[0] < 24:
        for sock in ('Base Color', 'Emission Color'):
            c = list(bsdf.inputs[sock].default_value[:3])
            c[0] *= 0.92
            c[2] = min(1.0, c[2] * 1.10)
            bsdf.inputs[sock].default_value = (c[0], c[1], c[2], 1.0)

sc.render.resolution_percentage = 50
sc.cycles.samples = 24
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
json.dump({"iterations": log,
           "base": [round(v, 4) for v in bsdf.inputs['Base Color'].default_value[:3]],
           "emission_strength": round(bsdf.inputs['Emission Strength'].default_value, 3),
           "emission_color": [round(v, 4) for v in bsdf.inputs['Emission Color'].default_value[:3]]},
          open(os.path.join(PRE, "S1G_WATER.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("S1G_DONE")
