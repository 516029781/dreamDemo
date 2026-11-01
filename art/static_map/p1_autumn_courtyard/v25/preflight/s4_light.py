# -*- coding: utf-8 -*-
"""S4 · 定光（§3.8 ④）

三件事：
  1. 主光翻向镜头（dir.y < 0）：物体朝向观众的一面进入阴影 → 中景自然成暗带，
     影长/物高按 §3.7.8 取 2.2；
  2. 曝光作为"舞台亮度"的主旋钮（KNOBS.exposure）；
  3. 逆光下干草要"透光"：给草类材质加一点自发光（KNOBS.grass_emis）。

用法: blender -b scene.blend -P preflight/s4_light.py
"""
import json
import os

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene
K = json.load(open(os.path.join(PRE, "KNOBS.json"), encoding="utf-8"))

# ---------------- 1. 太阳 ----------------
sun = bpy.data.objects.get("Warm directional afternoon sun")
d = Vector(K["sun_dir"]).normalized()
sun.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
sun.data.energy = float(K["sun_energy"])
sun.data.angle = 0.0209

# ---------------- 2. 其余灯 ----------------
for name, key in (("Warm late afternoon key", "key_energy"),
                  ("v15 broad warm camera-side bounce", "bounce_energy"),
                  ("Cool sky fill", "fill_energy")):
    ob = bpy.data.objects.get(name)
    if ob:
        ob.data.energy = float(K[key])

# 远景补光（左侧 30 m 处的廊桥/栈道在逆光下会成黑洞，用一盏大面光提起来）
far = bpy.data.objects.get("P1 far distance fill")
fe = float(K.get("far_fill_energy", 0.0))
if fe > 0:
    if not far:
        ld = bpy.data.lights.new("P1 far distance fill", 'AREA')
        far = bpy.data.objects.new("P1 far distance fill", ld)
        sc.collection.objects.link(far)
    far.data.shape = 'RECTANGLE'
    far.data.size = 16.0
    far.data.size_y = 7.0
    far.data.energy = fe
    far.location = (-5.0, -7.0, 7.6)
    tgt = Vector((-3.6, 8.5, 1.1)) - Vector(far.location)
    far.rotation_euler = tgt.to_track_quat('-Z', 'Y').to_euler()
    far.data.use_shadow = False
elif far:
    bpy.data.objects.remove(far, do_unlink=True)

# 背光（kicker）：从院子背后打，提起"前排设备在后排设备上投下的暗缝"，
# 同时给箱体/罐体勾一道亮边，让中景有体积而不是一块暗带。
kick = bpy.data.objects.get("P1 yard kicker")
ke = float(K.get("kicker_energy", 0.0))
if ke > 0:
    if not kick:
        ld = bpy.data.lights.new("P1 yard kicker", 'AREA')
        kick = bpy.data.objects.new("P1 yard kicker", ld)
        sc.collection.objects.link(kick)
    kick.data.shape = 'RECTANGLE'
    kick.data.size = 11.0
    kick.data.size_y = 4.0
    kick.data.energy = ke
    kick.location = (2.2, 7.4, 5.2)
    tgt = Vector((-0.6, 2.0, 1.5)) - Vector(kick.location)
    kick.rotation_euler = tgt.to_track_quat('-Z', 'Y').to_euler()
    kick.data.use_shadow = False
elif kick:
    bpy.data.objects.remove(kick, do_unlink=True)

# ---------------- 3. 曝光 ----------------
sc.view_settings.view_transform = 'Standard'
sc.view_settings.exposure = float(K["exposure"])

# ---------------- 4. 草透光 ----------------
ge = float(K.get("grass_emis", 0.0))
touched = 0
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    n = m.name.lower()
    if not any(k in n for k in ("grass", "干草", "dry grass")):
        continue
    b = next((x for x in m.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'), None)
    if not b or 'Emission Strength' not in b.inputs:
        continue
    if b.inputs['Base Color'].is_linked:
        base = (0.32, 0.22, 0.09, 1.0)
    else:
        base = tuple(b.inputs['Base Color'].default_value)
    if 'Emission Color' in b.inputs:
        b.inputs['Emission Color'].default_value = base
    b.inputs['Emission Strength'].default_value = ge
    touched += 1

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))

shadow_ratio = (d.xy.length / abs(d.z)) if abs(d.z) > 1e-6 else 99
info = {
    "sun_dir": [round(c, 4) for c in d],
    "shadow_ratio": round(shadow_ratio, 2),
    "exposure": sc.view_settings.exposure,
    "grass_materials": touched,
    "far_fill": fe,
}
json.dump(info, open(os.path.join(PRE, "S4_LIGHT.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("S4_DONE", info)
