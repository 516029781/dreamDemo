"""F0 后期合成（适配 Blender 5.2 的 Compositor Node Group API）。

链路：RL.Image -> Glare -> 雾(Mist) -> 分级 -> 暗角 -> 颗粒 -> GroupOutput
"""
import bpy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOBS = os.path.join(ROOT, "preflight", "KNOBS.json")
K = json.load(open(KNOBS, encoding="utf-8"))
sc = bpy.context.scene

# ---- Mist pass ----
if sc.world:
    ms = sc.world.mist_settings
    ms.use_mist = True
    ms.start = float(K.get("mist_start", 16.0))
    ms.depth = float(K.get("mist_depth", 60.0))
    try:
        ms.falloff = 'QUADRATIC'
    except Exception:
        pass
sc.view_layers[0].use_pass_mist = True

old = bpy.data.node_groups.get("P1 post")
if old:
    bpy.data.node_groups.remove(old)
ng = bpy.data.node_groups.new("P1 post", "CompositorNodeTree")
sc.compositing_node_group = ng


def N(t, x=0, y=0):
    n = ng.nodes.new(t)
    n.location = (x, y)
    return n


def setin(node, name, val, idx=0):
    try:
        node.inputs[name].default_value = val
        return True
    except Exception:
        try:
            node.inputs[idx].default_value = val
            return True
        except Exception as e:
            print("  set fail", node.bl_idname, name, e)
            return False


rl = N('CompositorNodeRLayers', -1100, 0)

# ---- 1. 辉光 ----
glare = N('CompositorNodeGlare', -880, 0)
for attr, val in (("glare_type", "BLOOM"), ("quality", "HIGH")):
    try:
        setattr(glare, attr, val)
    except Exception:
        pass
setin(glare, "Threshold", float(K.get("glow_threshold", 0.88)))
setin(glare, "Strength", float(K.get("glow_strength", 0.55)))
setin(glare, "Size", float(K.get("glow_size", 7)))
setin(glare, "Saturation", 1.0)
ng.links.new(rl.outputs['Image'], glare.inputs['Image'])
last = glare.outputs['Image']
print("GLARE ok")

# ---- 2. 深度雾 ----
try:
    mr_fog = N('ShaderNodeMapRange', -880, -300)
    setin(mr_fog, "From Min", 0.0)
    setin(mr_fog, "From Max", float(K.get("mist_span", 0.55)))
    setin(mr_fog, "To Min", 0.0)
    setin(mr_fog, "To Max", float(K.get("fog_max", 0.30)))
    ng.links.new(rl.outputs['Mist'], mr_fog.inputs['Value'])
    fogm = N('ShaderNodeMix', -660, -160)
    fogm.data_type = 'RGBA'
    fogm.blend_type = 'MIX'
    ng.links.new(mr_fog.outputs['Result'], fogm.inputs[0])
    ng.links.new(last, fogm.inputs[6])
    c = tuple(K.get("fog_color", [0.74, 0.76, 0.79]))
    fogm.inputs[7].default_value = (c[0], c[1], c[2], 1.0)
    last = fogm.outputs[2]
    print("FOG ok")
except Exception as e:
    print("FOG fail", e)

# ---- 3. 分级：亮部偏橙、暗部偏青 ----
try:
    cb = N('CompositorNodeColorBalance', -440, 0)
    try:
        cb.correction_method = 'LIFT_GAMMA_GAIN'
    except Exception:
        pass
    ng.links.new(last, cb.inputs['Image'])
    # Lift(暗部) 偏青 / Gain(亮部) 偏橙；ColorBalance 的输入里同名有多组，按索引找
    ins = [i for i in cb.inputs]
    lift = [i for i in ins if i.name == 'Lift']
    gain = [i for i in ins if i.name == 'Gain']
    if lift and gain:
        lc = tuple(K.get("lift_color", [0.955, 0.985, 1.030]))
        gc = tuple(K.get("gain_color", [1.035, 1.000, 0.950]))
        for i in lift:
            if i.type == 'RGBA':
                i.default_value = (lc[0], lc[1], lc[2], 1.0)
        for i in gain:
            if i.type == 'RGBA':
                i.default_value = (gc[0], gc[1], gc[2], 1.0)
        last = cb.outputs['Image']
        print("GRADE ok", len(lift), len(gain))
    else:
        print("GRADE skipped: no lift/gain sockets")
except Exception as e:
    print("GRADE fail", e)

# ---- 4. 暗角 ----
try:
    em = N('CompositorNodeEllipseMask', -440, -420)
    setin(em, "Position", (0.5, 0.5))
    sz = K.get("vig_size", [1.10, 0.72])
    if isinstance(sz, (int, float)):
        sz = [float(sz), float(sz) * 0.66]
    setin(em, "Size", (sz[0], sz[1]))
    bl = N('CompositorNodeBlur', -260, -420)
    setin(bl, "Size", float(K.get("vig_blur", 220)))
    for attr in ("size_x", "size_y"):
        try:
            setattr(bl, attr, float(K.get("vig_blur", 220)))
        except Exception:
            pass
    ng.links.new(em.outputs['Mask'], bl.inputs['Image'])
    vmr = N('ShaderNodeMapRange', -60, -420)
    setin(vmr, "From Min", 0.0)
    setin(vmr, "From Max", 1.0)
    setin(vmr, "To Min", 1.0 - float(K.get("vig_strength", 0.14)))
    setin(vmr, "To Max", 1.0)
    ng.links.new(bl.outputs['Image'], vmr.inputs['Value'])
    vmix = N('ShaderNodeMix', 160, -160)
    vmix.data_type = 'RGBA'
    vmix.blend_type = 'MULTIPLY'
    ng.links.new(last, vmix.inputs[6])
    ng.links.new(vmr.outputs['Result'], vmix.inputs[0])
    vmix.inputs[7].default_value = (1, 1, 1, 1)
    last = vmix.outputs[2]
    print("VIG ok")
except Exception as e:
    print("VIG fail", e)

# ---- 5. 颗粒 ----
try:
    nz = N('ShaderNodeTexNoise', 160, -520)
    setin(nz, "Scale", float(K.get("grain_scale", 900.0)))
    setin(nz, "Detail", 2.0)
    cc = N('CompositorNodeCombineColor', 360, -520)
    for ch in ('Red', 'Green', 'Blue'):
        try:
            ng.links.new(nz.outputs['Factor'], cc.inputs[ch])
        except Exception:
            pass
    gmix = N('ShaderNodeMix', 560, -160)
    gmix.data_type = 'RGBA'
    gmix.blend_type = 'OVERLAY'
    gmix.inputs[0].default_value = float(K.get("grain", 0.035))
    ng.links.new(last, gmix.inputs[6])
    ng.links.new(cc.outputs['Image'], gmix.inputs[7])
    last = gmix.outputs[2]
    print("GRAIN ok")
except Exception as e:
    print("GRAIN fail", e)

# ---- 输出 ----
out = N('NodeGroupOutput', 820, 0)
try:
    ng.interface.new_socket(name="Image", in_out='OUTPUT', socket_type='NodeSocketColor')
except Exception as e:
    print("iface", e)
try:
    ng.links.new(last, out.inputs[0])
except Exception as e:
    print("LINK OUT fail", e)

print("NODES", len(ng.nodes), "LINKS", len(ng.links))
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()
print("S0POST_DONE")
