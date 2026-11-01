# -*- coding: utf-8 -*-
"""R2e：最终收敛一轮——重载水纹、地面反照率下压、环境光再降。"""
import bpy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
SRC = os.path.join(ROOT, "background_src")
sc = bpy.context.scene
log = {"reload": [], "mats": [], "lights": [], "exposure": None}

# 1) 水纹重载
for img in bpy.data.images:
    if "M01" not in (img.filepath or "") and "M01" not in img.name:
        continue
    if img.packed_file:
        img.unpack(method="USE_ORIGINAL")
    want = os.path.join(SRC, os.path.basename(img.filepath)) if img.filepath else ""
    if want and os.path.exists(want):
        img.filepath = want
    img.reload()
    log["reload"].append({"name": img.name, "fp": img.filepath})

# 2) 地面材质压反照率
GROUND = ["V18 | P1 unified midtone limestone paving", "Sunlit limestone slab",
          "Warm limestone ashlar light", "Stone worn edges",
          "V18 | pale worn service limestone", "Warm limestone ashlar shade"]
for name in GROUND:
    mat = bpy.data.materials.get(name)
    if not mat or not mat.node_tree:
        continue
    bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if not bsdf:
        continue
    inp = bsdf.inputs["Base Color"]
    if inp.is_linked:
        nt = mat.node_tree
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        mix.inputs[7].default_value = (0.80, 0.79, 0.76, 1.0)
        nt.links.new(inp.links[0].from_socket, mix.inputs[6])
        nt.links.new(mix.outputs[2], inp)
        mix.name = "__alb"
        log["mats"].append({"name": name, "op": "texture_mul_0.80"})
    else:
        c = list(inp.default_value)
        inp.default_value = (c[0] * 0.80, c[1] * 0.79, c[2] * 0.76, 1.0)
        log["mats"].append({"name": name, "op": "base_mul_0.80"})

# 3) 环境光再降
for ob in sc.objects:
    if ob.type != "LIGHT":
        continue
    if ob.name == "v15 broad warm camera-side bounce":
        ob.data.energy = 34.0
    elif ob.name == "Cool sky fill":
        ob.data.energy = 8.0
    elif ob.name == "Warm late afternoon key":
        ob.data.energy = 300.0
    elif ob.name == "Warm directional afternoon sun":
        ob.data.energy = 9.0
    log["lights"].append({"name": ob.name, "energy": ob.data.energy})

sc.view_settings.exposure = -1.28
log["exposure"] = -1.28

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
with open(os.path.join(PRE, "R2E_TUNE.json"), "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=1)
print(json.dumps(log, ensure_ascii=False, indent=1)[:1200])
