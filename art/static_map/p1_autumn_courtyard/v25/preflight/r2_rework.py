# -*- coding: utf-8 -*-
"""R2 返修：光照重做 + 地面旧化 + 圆筒深木 + 草色压深 + 树冠放大。

依据 v21 诊断：
  - 主光 Warm late afternoon key 的 use_shadow=False，导致全图无方向性投影；
  - 三层补光 420/260/60 + world 1.189 让暗部消失；
  - 地面 V18 unified midtone limestone paving 无污渍与色差；
  - 圆筒 Weathered dark timber garden ribs 实际偏浅，彩旗抢色；
  - Dry grass 系列偏白。
只改参数与节点，不改几何拓扑（除树冠均匀放大）。
"""
import bpy
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene
log = {"lights": [], "materials": [], "objects": [], "warnings": []}

# ---------------- 1. 光照：恢复方向性，拉开光比 ----------------
TARGET = {
    "Warm late afternoon key": {"energy": 620.0, "use_shadow": True, "size": 3.2},
    "v15 broad warm camera-side bounce": {"energy": 95.0, "use_shadow": True},
    "Cool sky fill": {"energy": 26.0, "use_shadow": True},
    "Warm directional afternoon sun": {"energy": 14.0, "angle_deg": 1.6, "use_shadow": True},
}

for ob in sc.objects:
    if ob.type != "LIGHT":
        continue
    cfg = TARGET.get(ob.name)
    if not cfg:
        continue
    L = ob.data
    before = {"energy": L.energy, "use_shadow": L.use_shadow}
    if "energy" in cfg:
        L.energy = cfg["energy"]
    if "use_shadow" in cfg:
        L.use_shadow = cfg["use_shadow"]
    if "size" in cfg and hasattr(L, "size"):
        L.size = cfg["size"]
    if "angle_deg" in cfg and hasattr(L, "angle"):
        L.angle = math.radians(cfg["angle_deg"])
    log["lights"].append({"name": ob.name, "before": before,
                          "after": {"energy": L.energy, "use_shadow": L.use_shadow}})

# world 压暗，让环境光不再托底
w = sc.world
if w and w.node_tree:
    for n in w.node_tree.nodes:
        if n.type == "BACKGROUND":
            before = n.inputs["Strength"].default_value
            n.inputs["Strength"].default_value = 0.72
            log["warnings"].append(f"world strength {before:.3f} -> 0.720")

# 提升对比：曝光略回，gamma 不动
sc.view_settings.exposure = -0.55
log["warnings"].append("exposure -0.78 -> -0.55")

# ---------------- 2. 材质工具 ----------------
def principled(mat):
    if not mat.node_tree:
        return None
    for n in mat.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            return n
    return None


def darken_base(mat, factor, tint=None, tag=""):
    """把 Base Color 压暗并轻微偏色。贴图前插 Mix 乘法。"""
    bsdf = principled(mat)
    if not bsdf:
        log["warnings"].append(f"no principled: {mat.name}")
        return False
    nt = mat.node_tree
    inp = bsdf.inputs["Base Color"]
    if not inp.is_linked:
        c = list(inp.default_value)
        c[0] *= factor
        c[1] *= factor
        c[2] *= factor
        if tint:
            for i in range(3):
                c[i] *= tint[i]
        inp.default_value = (c[0], c[1], c[2], 1.0)
        log["materials"].append({"name": mat.name, "op": "base_mul", "f": factor, "tag": tag})
        return True
    # 有贴图：在贴图与 BSDF 之间插 MixRGB multiply
    src = inp.links[0].from_socket
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    toned = tint or (1.0, 1.0, 1.0)
    mix.inputs[7].default_value = (factor * toned[0], factor * toned[1], factor * toned[2], 1.0)
    nt.links.new(src, mix.inputs[6])
    nt.links.new(mix.outputs[2], inp)
    mix.name = f"__tone_{tag or 'd'}"
    log["materials"].append({"name": mat.name, "op": "mix_multiply", "f": factor, "tag": tag})
    return True


def add_grime(mat, scale=14.0, strength=0.42, dark=(0.30, 0.26, 0.21), tag="grime"):
    """在 Base Color 上叠一层低频噪声污渍。"""
    bsdf = principled(mat)
    if not bsdf:
        return False
    nt = mat.node_tree
    inp = bsdf.inputs["Base Color"]
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = scale
    tex.inputs["Detail"].default_value = 6.0
    tex.inputs["Roughness"].default_value = 0.72
    tex.location = (-900, -320)
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.42
    ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
    ramp.color_ramp.elements[1].position = 0.68
    ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
    ramp.location = (-700, -320)
    nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])

    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MIX"
    mix.location = (-500, -200)
    mix.inputs[7].default_value = (dark[0], dark[1], dark[2], 1.0)
    nt.links.new(ramp.outputs["Color"], mix.inputs["Factor"])
    if inp.is_linked:
        src = inp.links[0].from_socket
        nt.links.new(src, mix.inputs[6])
    else:
        mix.inputs[6].default_value = inp.default_value
    nt.links.new(mix.outputs[2], inp)
    mix.inputs["Factor"].default_value = 0.55 * strength
    mix.name = f"__{tag}"
    # 污渍处粗糙度略升
    rough = bsdf.inputs["Roughness"]
    if not rough.is_linked:
        rough.default_value = min(1.0, rough.default_value + 0.10)
    log["materials"].append({"name": mat.name, "op": "grime", "scale": scale, "strength": strength})
    return True


def add_cracks(mat, scale=42.0, width=0.035, dark=(0.16, 0.14, 0.12)):
    """Voronoi 边缘做细裂缝。"""
    bsdf = principled(mat)
    if not bsdf:
        return False
    nt = mat.node_tree
    inp = bsdf.inputs["Base Color"]
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = scale
    vor.location = (-900, -680)
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
    ramp.color_ramp.elements[1].position = width
    ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
    ramp.location = (-700, -680)
    nt.links.new(vor.outputs["Distance"], ramp.inputs["Fac"])

    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MIX"
    mix.location = (-480, -520)
    mix.inputs[7].default_value = (dark[0], dark[1], dark[2], 1.0)
    nt.links.new(ramp.outputs["Color"], mix.inputs["Factor"])
    if inp.is_linked:
        nt.links.new(inp.links[0].from_socket, mix.inputs[6])
    else:
        mix.inputs[6].default_value = inp.default_value
    nt.links.new(mix.outputs[2], inp)
    mix.name = "__cracks"
    log["materials"].append({"name": mat.name, "op": "cracks", "scale": scale})
    return True


# ---------------- 3. 地面：色差 + 污渍 + 裂缝 ----------------
GROUND = [
    "V18 | P1 unified midtone limestone paving",
    "Sunlit limestone slab",
    "Warm limestone ashlar light",
    "Stone worn edges",
    "Recessed warm joints",
]
for name in GROUND:
    m = bpy.data.materials.get(name)
    if not m:
        log["warnings"].append(f"missing material: {name}")
        continue
    if name == "Recessed warm joints":
        darken_base(m, 0.62, tag="joint_dark")
        continue
    darken_base(m, 0.88, tint=(1.0, 0.965, 0.915), tag="paving_warm")
    add_grime(m, scale=9.0, strength=0.55)
    add_cracks(m, scale=30.0, width=0.030)

# ---------------- 4. 圆筒改深木 ----------------
for name in ["Weathered dark timber garden ribs"]:
    m = bpy.data.materials.get(name)
    if m:
        darken_base(m, 0.58, tint=(1.0, 0.86, 0.70), tag="drum_deep")
        bsdf = principled(m)
        if bsdf and not bsdf.inputs["Roughness"].is_linked:
            bsdf.inputs["Roughness"].default_value = 0.86

# 彩色三角旗压暗，避免抢色
for m in bpy.data.materials:
    if "bunting" in m.name.lower() or "pennant" in m.name.lower() or "flag" in m.name.lower():
        darken_base(m, 0.72, tag="bunting_mute")

# ---------------- 5. 草：压深并偏金褐 ----------------
grass_hit = 0
for m in bpy.data.materials:
    n = m.name.lower()
    if n.startswith("dry grass") or n.startswith("grass") or "golden crown grass" in n:
        if darken_base(m, 0.74, tint=(1.06, 0.92, 0.66), tag="grass_deep"):
            grass_hit += 1
log["warnings"].append(f"grass materials toned: {grass_hit}")

# ---------------- 6. 左树冠放大 ----------------
TREE_SCALE = 1.26
tree_objs = [ob for ob in sc.objects
             if ob.type == "MESH" and ("broadleaf" in ob.name.lower()
                                       or ob.name.startswith("Tree joined autumn foliage"))]
PIVOT = (-5.3, 4.7, 0.23)
for ob in tree_objs:
    if ob.parent:
        continue
    before = list(ob.scale)
    ob.scale = (ob.scale.x * TREE_SCALE, ob.scale.y * TREE_SCALE, ob.scale.z * TREE_SCALE)
    ob.location = (PIVOT[0] + (ob.location.x - PIVOT[0]) * TREE_SCALE,
                   PIVOT[1] + (ob.location.y - PIVOT[1]) * TREE_SCALE,
                   ob.location.z)
    log["objects"].append({"name": ob.name, "before_scale": [round(v, 3) for v in before],
                           "after_scale": [round(v, 3) for v in ob.scale]})

# ---------------- 7. 保存 ----------------
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
with open(os.path.join(PRE, "R2_REWORK.json"), "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=1)

print("=== LIGHTS ===")
for d in log["lights"]:
    print(" ", d["name"], d["before"], "->", d["after"])
print("=== MATERIALS ===", len(log["materials"]))
print("=== OBJECTS ===", len(log["objects"]))
print("=== WARN ===")
for w_ in log["warnings"]:
    print("  !", w_)
