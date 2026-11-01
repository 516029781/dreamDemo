# -*- coding: utf-8 -*-
"""G1：图层 ID 图（水=蓝、M02=绿、M03=红、其余=灰、world=洋红），
用于确认水/岸/对岸的实际屏幕位置，并作为对象与 world 分类证据。"""
import bpy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REN = os.path.join(ROOT, "renders")
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene

COLORS = {
    "water": (0.05, 0.25, 1.0),
    "M02": (0.10, 0.85, 0.20),
    "M03": (1.0, 0.12, 0.08),
    "other": (0.55, 0.55, 0.55),
}


def flat(name, rgb):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = (*rgb, 1)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


mats = {k: flat("__id_" + k, v) for k, v in COLORS.items()}
saved = {}
for ob in sc.objects:
    if ob.type in {"MESH", "CURVE"} and hasattr(ob.data, "materials"):
        saved[ob.name] = [m.name for m in ob.data.materials]
        key = "other"
        if ob.name.startswith("M01W"):
            key = "water"
        elif ob.name.startswith("M02"):
            key = "M02"
        elif ob.name.startswith("M03"):
            key = "M03"
        ob.data.materials.clear()
        ob.data.materials.append(mats[key])

w = sc.world
w.use_nodes = True
bg = w.node_tree.nodes["Background"]
old_col = tuple(bg.inputs[0].default_value)
old_str = bg.inputs[1].default_value
bg.inputs[0].default_value = (1.0, 0.0, 1.0, 1.0)
bg.inputs[1].default_value = 1.0

sc.render.engine = "CYCLES"
sc.cycles.samples = 4
sc.cycles.use_denoising = False
sc.camera.data.dof.use_dof = False
sc.render.resolution_x = 1920
sc.render.resolution_y = 1078
sc.render.resolution_percentage = 50
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGB"
sc.render.filepath = os.path.join(REN, "G1_layer_id.png")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.render.render(write_still=True)

for name, mats_list in saved.items():
    ob = bpy.data.objects.get(name)
    if ob and hasattr(ob.data, "materials"):
        ob.data.materials.clear()
        for mn in mats_list:
            mt = bpy.data.materials.get(mn)
            if mt:
                ob.data.materials.append(mt)
bg.inputs[0].default_value = old_col
bg.inputs[1].default_value = old_str

json.dump({"colors": {k: list(v) for k, v in COLORS.items()},
           "world": "magenta (1,0,1)",
           "resolution": "960x539"},
          open(os.path.join(PRE, "G1_LAYER_ID.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("LAYER ID DONE")
