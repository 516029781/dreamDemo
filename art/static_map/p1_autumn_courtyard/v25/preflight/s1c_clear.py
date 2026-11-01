# -*- coding: utf-8 -*-
"""S1C · 撤走横穿水池的错位中景结构（S3 会按 y1.0-2.5 / 高≤1.8m 重建）。"""
import json
import os

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")

HIDE_PREFIX = ("Gantry", "Bunting support cord", "v15 gantry", "Bridge arched iron handrail",
               "Bridge lower iron rail")

hidden = []
for ob in bpy.data.objects:
    if any(ob.name.startswith(k) for k in HIDE_PREFIX) and not ob.hide_render:
        ob.hide_render = True
        hidden.append(ob.name)

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
json.dump(hidden, open(os.path.join(PRE, "S1C_HIDDEN.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("HIDDEN", len(hidden))
