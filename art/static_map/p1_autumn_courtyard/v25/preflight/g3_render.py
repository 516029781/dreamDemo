# -*- coding: utf-8 -*-
"""G3 交付渲染：final 1920×1078/48spp、blockout 50%、color_key 50%、no_dof 50%。"""
import bpy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REN = os.path.join(ROOT, "renders")
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene
cam = sc.camera

sc.render.engine = "CYCLES"
sc.cycles.seed = 0
sc.cycles.use_denoising = True
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGB"
bpy.context.preferences.filepaths.save_version = 0

# 1) 无 DOF 诊断
cam.data.dof.use_dof = False
sc.cycles.samples = 24
sc.render.resolution_x = 1920
sc.render.resolution_y = 1078
sc.render.resolution_percentage = 50
sc.render.filepath = os.path.join(REN, "no_dof_diagnostic.png")
bpy.ops.render.render(write_still=True)

# 2) 正式图
cam.data.dof.use_dof = True
sc.cycles.samples = 48
sc.render.resolution_percentage = 100
sc.render.filepath = os.path.join(REN, "final.png")
bpy.ops.render.render(write_still=True)

# 3) 色块图（保留材质但压成 5 个色角色 + 无贴图细节）
key = bpy.data.materials.get("__color_key") or bpy.data.materials.new("__color_key")
key.use_nodes = True
kb = key.node_tree.nodes.get("Principled BSDF")
kb.inputs["Base Color"].default_value = (0.62, 0.55, 0.45, 1)
kb.inputs["Roughness"].default_value = 0.9
saved = {}
for ob in sc.objects:
    if ob.type in {"MESH", "CURVE"} and hasattr(ob.data, "materials"):
        saved[ob.name] = [m.name for m in ob.data.materials]
        if ob.name.startswith("M0"):
            continue
        ob.data.materials.clear()
        ob.data.materials.append(key)
sc.render.resolution_percentage = 50
sc.cycles.samples = 16
sc.render.filepath = os.path.join(REN, "color_key.png")
bpy.ops.render.render(write_still=True)

# 还原
for name, mats in saved.items():
    ob = bpy.data.objects.get(name)
    if ob and hasattr(ob.data, "materials"):
        ob.data.materials.clear()
        for mn in mats:
            mt = bpy.data.materials.get(mn)
            if mt:
                ob.data.materials.append(mt)

# 4) 灰模
clay = bpy.data.materials.get("__blockout_clay") or bpy.data.materials.new("__blockout_clay")
clay.use_nodes = True
cb = clay.node_tree.nodes.get("Principled BSDF")
cb.inputs["Base Color"].default_value = (0.62, 0.61, 0.60, 1)
cb.inputs["Roughness"].default_value = 0.92
saved2 = {}
for ob in sc.objects:
    if ob.type in {"MESH", "CURVE"} and hasattr(ob.data, "materials"):
        if ob.name.startswith("M0"):
            ob.hide_render = True
            continue
        saved2[ob.name] = [m.name for m in ob.data.materials]
        ob.data.materials.clear()
        ob.data.materials.append(clay)
sc.render.resolution_percentage = 50
sc.render.filepath = os.path.join(REN, "blockout.png")
bpy.ops.render.render(write_still=True)

for name, mats in saved2.items():
    ob = bpy.data.objects.get(name)
    if ob and hasattr(ob.data, "materials"):
        ob.data.materials.clear()
        for mn in mats:
            mt = bpy.data.materials.get(mn)
            if mt:
                ob.data.materials.append(mt)
for ob in sc.objects:
    if ob.name.startswith("M0"):
        ob.hide_render = False

json.dump({"final": {"px": [1920, 1078], "samples": 48, "dof": True,
                     "f_stop": cam.data.dof.aperture_fstop,
                     "focus_m": round(cam.data.dof.focus_distance, 2)},
           "no_dof": {"px": [960, 539], "samples": 24, "dof": False},
           "blockout": {"px": [960, 539], "clay": 0.62, "plates_hidden": True},
           "color_key": {"px": [960, 539], "material": "single warm key + plates"},
           "seed": 0},
          open(os.path.join(PRE, "G3_RENDER.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
print("G3 RENDERS DONE")
