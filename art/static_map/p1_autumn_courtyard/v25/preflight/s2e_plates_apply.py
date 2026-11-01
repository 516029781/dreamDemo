# -*- coding: utf-8 -*-
"""S2e · 把 KNOBS 里的景片发光强度写进场景，并重载贴图。

用法: blender -b scene.blend -P preflight/s2e_plates_apply.py
"""
import json
import os

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
SRC = os.path.join(ROOT, "background_src")
K = json.load(open(os.path.join(PRE, "KNOBS.json"), encoding="utf-8"))

EM = {
    "M02 | far bank plate mat": K["m02_em"],
    "M03 | distant air plate mat": K["m03_em"],
}

out = {}
for name, val in EM.items():
    m = bpy.data.materials.get(name)
    if not m:
        out[name] = "missing"
        continue
    em = next((n for n in m.node_tree.nodes if n.type == 'EMISSION'), None)
    if em:
        em.inputs['Strength'].default_value = val
        out[name] = round(val, 3)

for img in bpy.data.images:
    if img.filepath and os.path.basename(img.filepath).startswith(("M01", "M02", "M03")):
        want = os.path.join(SRC, os.path.basename(img.filepath))
        if os.path.exists(want):
            img.filepath = want
        img.reload()

# 孤岛：M01W 删除后，y19.5 这块"远岸板"没有任何支撑，渲染成一条横贯画面的亮线
HIDE = K.get("hide_far_shore", True)
hidden = []
for ob in bpy.data.objects:
    if ob.name.startswith("P1 far shore edge") and HIDE:
        ob.hide_render = True
        hidden.append(ob.name)
    elif ob.name.startswith("P1 far shore edge"):
        ob.hide_render = False

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
print("S2E_DONE", out, "hidden", len(hidden))
json.dump({"emission": out, "hidden": hidden},
          open(os.path.join(PRE, "S2E_PLATES.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
