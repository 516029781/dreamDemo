"""F0 光色与后期。

方案 §三 F0：
  主光 左上偏后（画面 10-11 点），仰角 25-30°，影长/物高 2.0-2.4
  天光偏蓝，负责阴影里的冷；右侧低角度冷补光，只提亮不改色相
  后期：Glare 辉光 / 深度雾 / 暗角 -12% / 颗粒 / 亮部橙暗部青
"""
import bpy
import json
import math
import os
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOBS = os.path.join(ROOT, "preflight", "KNOBS.json")
K = json.load(open(KNOBS, encoding="utf-8"))
sc = bpy.context.scene

# ---------------- 1. 太阳：翻到左上偏后 ----------------
sun = bpy.data.objects.get("Warm directional afternoon sun")
if sun is None:
    for ob in bpy.data.objects:
        if ob.type == 'LIGHT' and ob.data.type == 'SUN':
            sun = ob
            break
if sun:
    d = Vector(K.get("sun_dir", [0.62, -0.62, -0.47])).normalized()
    sun.rotation_mode = 'QUATERNION'
    sun.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    sun.data.energy = float(K.get("sun_energy", 3.6))
    sun.data.angle = math.radians(float(K.get("sun_angle_deg", 2.4)))
    sun.data.color = tuple(K.get("sun_color", [1.0, 0.93, 0.84]))
    print("SUN dir=%s E=%.2f" % ([round(c, 3) for c in d], sun.data.energy))


# ---------------- 2. 面光 ----------------
def aim(ob, loc, target):
    ob.location = loc
    v = Vector(target) - Vector(loc)
    ob.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()


def setup_area(name, energy, loc, target, color, size=6.0, size_y=None, on=True):
    ob = bpy.data.objects.get(name)
    if ob is None:
        if not on:
            return
        ld = bpy.data.lights.new(name, 'AREA')
        ob = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(ob)
    ob.hide_render = not on
    if not on:
        return
    ob.data.energy = energy
    ob.data.color = color
    if size_y:
        ob.data.shape = 'RECTANGLE'
        ob.data.size = size
        ob.data.size_y = size_y
    else:
        ob.data.shape = 'SQUARE'
        ob.data.size = size
    aim(ob, Vector(loc), Vector(target))


# 暖主补：左后上方，压住"逆光后整个正面全黑"
setup_area("Warm late afternoon key",
           float(K.get("key_energy", 240.0)),
           tuple(K.get("key_loc", [-7.5, 6.0, 7.2])),
           tuple(K.get("key_target", [-0.5, 5.0, 0.4])),
           tuple(K.get("key_color", [1.0, 0.90, 0.78])),
           size=9.0, size_y=6.0)

# 暖反弹：右后方低位，只补背光面的边缘
setup_area("v15 broad warm bounce",
           float(K.get("bounce_energy", 34.0)),
           tuple(K.get("bounce_loc", [9.0, 4.0, 2.6])),
           tuple(K.get("bounce_target", [0.0, 4.0, 0.6])),
           tuple(K.get("bounce_color", [1.0, 0.86, 0.70])),
           size=8.0, size_y=5.0)

# 冷补：右侧低角度，负责把阴影推冷，不改色相
setup_area("Cool sky fill",
           float(K.get("fill_energy", 26.0)),
           tuple(K.get("fill_loc", [10.0, -5.0, 2.4])),
           tuple(K.get("fill_target", [0.0, 2.0, 1.0])),
           tuple(K.get("fill_color", [0.70, 0.82, 1.0])),
           size=7.0, size_y=6.0)

# ---------------- 3. 天光偏蓝 ----------------
w = sc.world
if w and w.use_nodes:
    for nd in w.node_tree.nodes:
        if nd.type == 'BACKGROUND':
            nm = nd.name
            if nm == "Background 0.2" or "Background" in nm:
                nd.inputs['Color'].default_value = tuple(K.get("sky_color", [0.42, 0.53, 0.72, 1.0]))
                nd.inputs['Strength'].default_value = float(K.get("sky_strength", 0.62))

# ---------------- 3.5 曝光与色彩管理 ----------------
try:
    sc.view_settings.view_transform = K.get("view_transform", "Standard")
    sc.view_settings.exposure = float(K.get("exposure", -0.10))
    sc.view_settings.look = K.get("look", "None")
    print("EXPOSURE", sc.view_settings.exposure, sc.view_settings.view_transform)
except Exception as e:
    print("EXPOSURE fail", e)

# ---------------- 4. 后期合成 ----------------
def build_comp():
    sc.use_nodes = True
    nt = sc.node_tree
    nt.nodes.clear()
    rl = nt.nodes.new('CompositorNodeRLayers')
    rl.location = (-900, 0)

    # 辉光：草尖、天井边、台阶亮面外溢
    glare = nt.nodes.new('CompositorNodeGlare')
    glare.location = (-650, 0)
    for gt in ('BLOOM', 'FOG_GLOW'):
        try:
            glare.glare_type = gt
            break
        except Exception:
            continue
    glare.quality = 'HIGH'
    glare.threshold = float(K.get("glow_threshold", 0.86))
    glare.size = int(K.get("glow_size", 7))
    try:
        glare.mix = float(K.get("glow_mix", -0.55))
    except Exception:
        pass
    nt.links.new(rl.outputs['Image'], glare.inputs['Image'])

    # 深度雾：远处压淡、偏冷
    fog_col = tuple(K.get("fog_color", [0.78, 0.79, 0.80]))
    try:
        mv = nt.nodes.new('CompositorNodeMapValue')
        mv.location = (-650, -260)
        mv.offset = (0.0,)
        mv.size = (float(K.get("fog_near", 0.0)),)
        mv.use_min = mv.use_max = True
        mv.min = 0.0
        mv.offset[0] = -float(K.get("fog_start", 0.04))
        mv.size[0] = 1.0 / max(float(K.get("fog_span", 0.30)), 1e-3)
        mix = nt.nodes.new('CompositorNodeMixRGB')
        mix.location = (-400, -160)
        mix.blend_type = 'MIX'
        mix.inputs[2].default_value = (*fog_col, 1.0)
        nt.links.new(rl.outputs['Depth'], mv.inputs['Value'])
        nt.links.new(mv.outputs['Value'], mix.inputs['Fac'])
        nt.links.new(glare.outputs['Image'], mix.inputs[1])
        last = mix
    except Exception as e:
        print("FOG skip:", e)
        last = glare

    # 分级：亮部偏橙、暗部偏青（RGB 曲线，两端各抬一点）
    try:
        cur = nt.nodes.new('CompositorNodeCurveRGB')
        cur.location = (-150, 0)
        m = cur.mapping
        m.initialize()
        c = m.curves[0]
        c.points[0].location = (0.0, 0.0)
        c.points[-1].location = (1.0, 1.0)
        c.points.new(0.28, 0.245)
        c.points.new(0.80, 0.828)
        c2 = m.curves[1]
        c2.points.new(0.28, 0.285)
        c2.points.new(0.80, 0.808)
        c3 = m.curves[2]
        c3.points.new(0.28, 0.325)
        c3.points.new(0.80, 0.775)
        nt.links.new(last.outputs[0], cur.inputs['Image'])
        last = cur
    except Exception as e:
        print("GRADE skip:", e)

    # 暗角 -12%
    try:
        em = nt.nodes.new('CompositorNodeEllipseMask')
        em.location = (-150, -320)
        em.width = float(K.get("vig_size", 1.05))
        em.height = float(K.get("vig_size", 1.05) * 0.62)
        bl = nt.nodes.new('CompositorNodeBlur')
        bl.location = (60, -320)
        bl.filter_type = 'GAUSS'
        bl.size_x = int(K.get("vig_blur", 260))
        bl.size_y = int(K.get("vig_blur", 260))
        nt.links.new(em.outputs['Mask'], bl.inputs['Image'])
        mv2 = nt.nodes.new('CompositorNodeMapValue')
        mv2.location = (240, -320)
        mv2.offset = (1.0,)
        mv2.size = (float(K.get("vig_strength", 0.12)),)
        nt.links.new(bl.outputs['Image'], mv2.inputs['Value'])
        mul = nt.nodes.new('CompositorNodeMixRGB')
        mul.location = (420, 0)
        mul.blend_type = 'MULTIPLY'
        mul.inputs[0].default_value = 1.0
        nt.links.new(mv2.outputs['Value'], mul.inputs[0])
        nt.links.new(last.outputs[0], mul.inputs[1])
        mul.inputs[2].default_value = (1, 1, 1, 1)
        last = mul
    except Exception as e:
        print("VIG skip:", e)

    # 颗粒 3%
    try:
        tex = bpy.data.textures.get("P1 grain")
        if not tex:
            tex = bpy.data.textures.new("P1 grain", type='CLOUDS')
            tex.noise_scale = 0.35
            tex.noise_depth = 2
            tex.intensity = 1.0
        tn = nt.nodes.new('CompositorNodeTexture')
        tn.location = (240, -520)
        tn.texture = tex
        tn.inputs['Scale'].default_value = 1.0
        gmul = nt.nodes.new('CompositorNodeMixRGB')
        gmul.location = (600, -200)
        gmul.blend_type = 'OVERLAY'
        gmul.inputs[0].default_value = float(K.get("grain", 0.030))
        nt.links.new(last.outputs[0], gmul.inputs[1])
        nt.links.new(tn.outputs['Value'], gmul.inputs[2])
        last = gmul
    except Exception as e:
        print("GRAIN skip:", e)

    comp = nt.nodes.new('CompositorNodeComposite')
    comp.location = (820, 0)
    nt.links.new(last.outputs[0], comp.inputs['Image'])
    print("COMP built")


try:
    build_comp()
except Exception as e:
    print("COMP FAILED:", e)

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()
json.dump(K, open(KNOBS, "w"), ensure_ascii=False, indent=1)
print("S0_DONE")
