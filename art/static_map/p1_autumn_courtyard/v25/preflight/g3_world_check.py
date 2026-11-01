# -*- coding: utf-8 -*-
"""G3：world 暴露检查（景片保留 alpha，world 设为洋红，其余压成深灰）。
任何洋红像素即为 world 可见像素，必须计入 A 类背景。"""
import bpy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REN = os.path.join(ROOT, "renders")
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene

grey = bpy.data.materials.get("__worldchk") or bpy.data.materials.new("__worldchk")
grey.use_nodes = True
gb = grey.node_tree.nodes.get("Principled BSDF")
gb.inputs["Base Color"].default_value = (0.25, 0.25, 0.25, 1)

saved = {}
for ob in sc.objects:
    if ob.type in {"MESH", "CURVE"} and hasattr(ob.data, "materials"):
        if ob.name.startswith("M0"):
            ob.hide_render = False
            continue
        saved[ob.name] = [m.name for m in ob.data.materials]
        ob.data.materials.clear()
        ob.data.materials.append(grey)

w = sc.world
bg = w.node_tree.nodes["Background"]
bg.inputs[0].default_value = (1.0, 0.0, 1.0, 1.0)
bg.inputs[1].default_value = 1.0

sc.render.engine = "CYCLES"
sc.cycles.samples = 8
sc.cycles.use_denoising = False
sc.camera.data.dof.use_dof = False
sc.render.resolution_percentage = 50
sc.render.filepath = os.path.join(REN, "G3_world_exposure.png")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.render.render(write_still=True)

for name, mats in saved.items():
    ob = bpy.data.objects.get(name)
    if ob and hasattr(ob.data, "materials"):
        ob.data.materials.clear()
        for mn in mats:
            mt = bpy.data.materials.get(mn)
            if mt:
                ob.data.materials.append(mt)
bg.inputs[0].default_value = (0.54, 0.52, 0.49, 1.0)
bg.inputs[1].default_value = 0.2

json.dump({"world_color": [1, 0, 1], "resolution": "960x539", "samples": 8},
          open(os.path.join(PRE, "G3_WORLD_CHECK.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("WORLD CHECK DONE")
