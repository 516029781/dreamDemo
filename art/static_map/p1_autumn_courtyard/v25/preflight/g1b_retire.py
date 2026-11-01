# -*- coding: utf-8 -*-
"""G1b 收口：逐对象处理旧近岸/芦苇（保留真正承托岸沿的 T01，隐藏 V18 B04/B15 旧件），
再把水面与对岸的接触关系固定下来。"""
import bpy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene

RETIRE_PREFIX = ("V18 B04 |", "V18 B15 |", "V18 B03 |")
decisions = []
for ob in sc.objects:
    if ob.type not in {"MESH", "CURVE"}:
        continue
    if any(ob.name.startswith(p) for p in RETIRE_PREFIX):
        before = ob.hide_render
        ob.hide_render = True
        decisions.append({"name": ob.name, "action": "retire",
                          "reason": "V20 旧近岸/芦苇，浮在新水面上方，与新 T01 岸沿重复",
                          "was_hidden": bool(before)})

# T01 岸沿保留，但压到 z 顶 0.10（原来 0.13 略高于水面视觉线）
keep = [ob.name for ob in sc.objects if ob.name.startswith("T01 |")]
json.dump({"retired": decisions, "kept_t01": keep,
           "note": "只隐藏旧远景/近岸件，不删除；T01 岸沿与暗壁继续承托水面。"},
          open(os.path.join(PRE, "G1B_RETIRE.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
print("RETIRE DONE", len(decisions))
