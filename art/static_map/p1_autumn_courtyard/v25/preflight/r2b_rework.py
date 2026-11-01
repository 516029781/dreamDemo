# -*- coding: utf-8 -*-
"""R2b：修正 world 透出（顶部蓝带）、减弱地面污渍、继续拉开光比、树再放大。

问题定位：
  - world 节点树含 3 个 BACKGROUND（原 strength 0.200 / 0.600 / 1.189），
    R2 把三者统一压到 0.72，破坏混合比例，顶部透出蓝灰底。
  - add_grime strength 0.55 / scale 9 产生低频大油污斑。
"""
import bpy
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene
log = {"world": [], "materials": [], "lights": [], "objects": [], "warnings": []}

# ---------- 1. world：恢复原 strength，颜色改暖 ----------
ORIG = [0.200, 0.600, 1.189]
WARM = (0.34, 0.285, 0.225, 1.0)
w = sc.world
bg_nodes = [n for n in w.node_tree.nodes if n.type == "BACKGROUND"]
for i, n in enumerate(bg_nodes):
    before = (round(n.inputs["Strength"].default_value, 3),
              [round(c, 3) for c in n.inputs["Color"].default_value])
    n.inputs["Strength"].default_value = ORIG[i] if i < len(ORIG) else 1.0
    c = n.inputs["Color"].default_value
    n.inputs["Color"].default_value = WARM
    log["world"].append({"idx": i, "before": before,
                         "after_strength": round(n.inputs["Strength"].default_value, 3)})
log["warnings"].append(f"world bg nodes: {len(bg_nodes)} -> warm {WARM[:3]}")

# ---------- 2. 地面：撤掉过重的 grime，换轻量高频 ----------
def principled(mat):
    for n in mat.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            return n
    return None

GROUND = ["V18 | P1 unified midtone limestone paving", "Sunlit limestone slab",
          "Warm limestone ashlar light", "Stone worn edges"]
for name in GROUND:
    m = bpy.data.materials.get(name)
    if not m or name not in bpy.data.materials:
        continue
    nt = m.node_tree
    old = nt.nodes.get("__grime")
    if old:
        # 找旧 grime 的下游连接，接回上游
        bsdf = principled(m)
        inp = bsdf.inputs["Base Color"]
        # 旧 mix 的 A 输入来源即原始纹理
        src = None
        if old.inputs[6].is_linked:
            src = old.inputs[6].links[0].from_socket
        nt.nodes.remove(old)
        if src:
            nt.links.new(src, inp)
        dark = (0.30, 0.26, 0.21)
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = 26.0
        tex.inputs["Detail"].default_value = 8.0
        tex.inputs["Roughness"].default_value = 0.62
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.46
        ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
        ramp.color_ramp.elements[1].position = 0.74
        ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
        nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MIX"
        nt.links.new(ramp.outputs["Color"], mix.inputs["Factor"])
        cur = inp.links[0].from_socket if inp.is_linked else None
        if cur:
            nt.links.new(cur, mix.inputs[6])
        else:
            mix.inputs[6].default_value = inp.default_value
        nt.links.new(mix.outputs[2], inp)
        mix.inputs["Factor"].default_value = 0.30
        mix.name = "__grime2"
        log["materials"].append({"name": name, "op": "grime_replace", "factor": 0.30})

# ---------- 3. 光照：再压一档 ----------
for ob in sc.objects:
    if ob.type != "LIGHT":
        continue
    L = ob.data
    if ob.name == "Warm late afternoon key":
        L.energy = 520.0
    elif ob.name == "Warm directional afternoon sun":
        L.energy = 18.0
        L.angle = math.radians(1.2)
    elif ob.name == "v15 broad warm camera-side bounce":
        L.energy = 70.0
    elif ob.name == "Cool sky fill":
        L.energy = 20.0
    log["lights"].append({"name": ob.name, "energy": round(L.energy, 2)})

sc.view_settings.exposure = -0.72

# ---------- 4. 树再放大一档 ----------
TREE_SCALE = 1.16
PIVOT = (-5.3, 4.7, 0.23)
for ob in sc.objects:
    if ob.type != "MESH" or ob.parent:
        continue
    n = ob.name.lower()
    if not ("broadleaf" in n or ob.name.startswith("Tree joined autumn foliage")):
        continue
    ob.scale = (ob.scale.x * TREE_SCALE, ob.scale.y * TREE_SCALE, ob.scale.z * TREE_SCALE)
    ob.location = (PIVOT[0] + (ob.location.x - PIVOT[0]) * TREE_SCALE,
                   PIVOT[1] + (ob.location.y - PIVOT[1]) * TREE_SCALE,
                   ob.location.z)
    log["objects"].append({"name": ob.name, "scale": [round(v, 3) for v in ob.scale]})

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
with open(os.path.join(PRE, "R2B_REWORK.json"), "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=1)

print("WORLD:")
for d in log["world"]:
    print(" ", d)
print("MATERIALS:", log["materials"])
print("LIGHTS:", log["lights"])
print("OBJECTS:", len(log["objects"]))
