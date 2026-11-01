# -*- coding: utf-8 -*-
"""修复 clay/color_key 材质泄漏：按 v21 材质映射逐对象回填。

泄漏根因：blockout 用 ob.data.materials.clear() 改共享 mesh，
多对象共用同一 mesh 时逐个恢复会互相覆盖，最终部分对象仍挂 clay。
本脚本按材质名直接写 material_slots，并校验零泄漏。
"""
import bpy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene

with open(os.path.join(PRE, "MAT_MAP_V21.json"), encoding="utf-8") as f:
    MP = json.load(f)

CLAY = "__blockout_clay"
KEY = "__color_key"
fixed, missing, restored = [], [], 0

for ob in sc.objects:
    if ob.type not in {"MESH", "CURVE"} or not hasattr(ob.data, "materials"):
        continue
    names = MP.get(ob.name)
    if not names:
        continue
    cur = [m.name if m else None for m in ob.data.materials]
    if not any(n in {CLAY, KEY} for n in cur if n):
        continue
    mats = []
    for n in names:
        if not n:
            mats.append(None)
            continue
        m = bpy.data.materials.get(n)
        if not m:
            missing.append((ob.name, n))
            mats.append(None)
        else:
            mats.append(m)
    # 直接写 slots，避免 clear() 影响共享 mesh 的其他用户
    if len(ob.material_slots) == len(mats):
        for i, m in enumerate(mats):
            ob.material_slots[i].material = m
    else:
        ob.data.materials.clear()
        for m in mats:
            ob.data.materials.append(m)
    fixed.append(ob.name)
    restored += 1

# 校验
leak = []
for ob in sc.objects:
    if ob.type not in {"MESH", "CURVE"} or not hasattr(ob.data, "materials"):
        continue
    for m in ob.data.materials:
        if m and m.name in {CLAY, KEY}:
            leak.append(ob.name)

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))

rec = {"restored": restored, "fixed": fixed[:40], "missing_materials": missing[:20],
       "remaining_leak": leak[:20], "leak_count": len(leak)}
with open(os.path.join(PRE, "R5_MAT_FIX.json"), "w", encoding="utf-8") as f:
    json.dump(rec, f, ensure_ascii=False, indent=1)
print("RESTORED", restored, "LEAK", len(leak))
print("MISSING", missing[:6])
