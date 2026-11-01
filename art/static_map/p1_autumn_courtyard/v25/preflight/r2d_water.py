# -*- coding: utf-8 -*-
"""R2d：水面退后、曝光回归、地面压暗。

定位：成图顶部 0–22% 的蓝带是 M01W 真实水面（相机 20.67°，水面 y15.3–22.5
投影到 v 2.1%–22.3%），不是 M03 景片。参考图水面仅占左上角小块。
不缩网格（会露地面缺口），改为压暗去饱和 + 提高粗糙度，让水退成背景暗带。
"""
import bpy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene
log = {"water": [], "materials": [], "warnings": []}

m = bpy.data.materials.get("M01W water")
if m and m.node_tree:
    bsdf = None
    for n in m.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            bsdf = n
            break
    if bsdf:
        bc = bsdf.inputs["Base Color"]
        before = list(bc.default_value) if not bc.is_linked else "linked"
        # 向暖灰靠，压暗
        target = (0.108, 0.118, 0.122)
        if bc.is_linked:
            mix = m.node_tree.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0
            mix.inputs[7].default_value = (0.52, 0.55, 0.55, 1.0)
            m.node_tree.links.new(bc.links[0].from_socket, mix.inputs[6])
            m.node_tree.links.new(mix.outputs[2], bc)
            mix.name = "__water_dim"
        else:
            bc.default_value = (*target, 1.0)
        log["water"].append({"mat": m.name, "before": before,
                             "after": list(bc.default_value) if not bc.is_linked else "dimmed"})
        for key, val in [("Roughness", 0.62), ("IOR", 1.18)]:
            if key in bsdf.inputs and not bsdf.inputs[key].is_linked:
                old = bsdf.inputs[key].default_value
                bsdf.inputs[key].default_value = val
                log["water"].append({"param": key, "before": round(old, 3), "after": val})
        # 降高光
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = 0.28
        elif "Specular" in bsdf.inputs:
            bsdf.inputs["Specular"].default_value = 0.28

# 地面再压一档（只动非贴图基色材质）
for name in ["V18 | P1 unified midtone limestone paving", "Sunlit limestone slab",
             "Warm limestone ashlar light"]:
    mat = bpy.data.materials.get(name)
    if not mat or not mat.node_tree:
        continue
    bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if not bsdf:
        continue
    inp = bsdf.inputs["Base Color"]
    if not inp.is_linked:
        c = list(inp.default_value)
        inp.default_value = (c[0] * 0.90, c[1] * 0.90, c[2] * 0.88, 1.0)
        log["materials"].append({"name": name, "op": "base_mul_0.90"})

sc.view_settings.exposure = -1.15
log["warnings"].append("exposure -> -1.15")

# 水面远端的挡土墙提亮一点，形成岸线分界
for ob in sc.objects:
    if ob.name.startswith("T01 | far retaining"):
        for slot in ob.material_slots:
            mat = slot.material
            if not mat or not mat.node_tree:
                continue
            bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
            if bsdf and not bsdf.inputs["Base Color"].is_linked:
                c = list(bsdf.inputs["Base Color"].default_value)
                bsdf.inputs["Base Color"].default_value = (
                    min(1, c[0] * 1.06), min(1, c[1] * 1.02), min(1, c[2] * 0.96), 1.0)

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
with open(os.path.join(PRE, "R2D_WATER.json"), "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=1)

print("WATER:", log["water"])
print("MATS:", log["materials"])
