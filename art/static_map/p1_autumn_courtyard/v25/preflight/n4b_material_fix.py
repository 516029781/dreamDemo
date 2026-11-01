# N4b: fix wood ramp colors (deep walnut family, low contrast), lower kerb
# planters to bench height, desaturate their soil, add subtle noise to
# retaining wall and front lowland so big planes stop reading as flat cards.
import bpy, json, os, time
from mathutils import Vector

t0 = time.time()
sc = bpy.context.scene
LOG = {}


def bbmin_z(ob):
    return min((ob.matrix_world @ Vector(c)).z for c in ob.bound_box)


def bbmax_z(ob):
    return max((ob.matrix_world @ Vector(c)).z for c in ob.bound_box)


# 1) wood ramp -> walnut pair (low contrast, warm dark)
m = bpy.data.materials.get("Old stained wood")
if m and m.use_nodes:
    for nd in m.node_tree.nodes:
        if nd.type == 'VALTORGB' and len(nd.color_ramp.elements) >= 2:
            els = nd.color_ramp.elements
            els[0].color = (0.055, 0.030, 0.016, 1.0)
            els[-1].color = (0.235, 0.135, 0.072, 1.0)
            LOG["wood_ramp"] = "walnut pair"

# 2) kerb planters: lower to ~0.52 m top
TARGET_TOP = 0.52
for nm in ["P1 yard | kerb A", "P1 yard | kerb A | soil", "P1 yard | kerb A | dry grass bed",
           "P1 yard | kerb A | dry grass bed fill",
           "P1 yard | kerb B", "P1 yard | kerb B | soil", "P1 yard | kerb B | dry grass bed",
           "P1 yard | kerb B | dry grass bed fill"]:
    ob = bpy.data.objects.get(nm)
    if not ob:
        continue
    z0, z1 = bbmin_z(ob), bbmax_z(ob)
    if z1 - z0 < 0.05:
        continue
    s = (TARGET_TOP + 0.02 - z0) / (z1 - z0)
    if s < 1.0:
        ob.scale = (ob.scale[0], ob.scale[1], ob.scale[2] * s)
        bpy.context.view_layer.update()
        dz = (TARGET_TOP + 0.02 - bbmax_z(ob))
        ob.location.z += dz  # keep base seated, settle top to target
        LOG.setdefault("kerb_lowered", []).append(nm)

# 3) soil desaturation
for mn in ("P1 yard | kerb A | soil", "P1 yard | kerb B | soil"):
    mm = None
    ob = bpy.data.objects.get(mn)
    if ob and ob.data.materials:
        mm = ob.data.materials[0]
    if mm and mm.use_nodes:
        for nd in mm.node_tree.nodes:
            if nd.type == 'BSDF_PRINCIPLED':
                c = nd.inputs["Base Color"].default_value
                g = (c[0] + c[1] + c[2]) / 3
                nd.inputs["Base Color"].default_value = (g * 1.35, g * 1.22, g * 1.0, 1.0)
                LOG["soil_desat"] = True

# 4) retaining wall + lowland: subtle large-scale tone variation via noise
for mn in ("Recessed warm joints", "Autumn soil beyond platform"):
    mm = bpy.data.materials.get(mn)
    if not (mm and mm.use_nodes):
        continue
    nt = mm.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not bsdf or bsdf.inputs["Base Color"].is_linked:
        continue
    lk_base = bsdf.inputs["Base Color"].default_value
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.9
    noise.inputs["Detail"].default_value = 4.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (lk_base[0] * 0.78, lk_base[1] * 0.78, lk_base[2] * 0.78, 1.0)
    ramp.color_ramp.elements[1].color = (min(1, lk_base[0] * 1.18), min(1, lk_base[1] * 1.18), min(1, lk_base[2] * 1.18), 1.0)
    mixn = nt.nodes.new("ShaderNodeMix")
    mixn.data_type = 'RGBA'
    mixn.blend_type = 'MIX'
    mixn.name = "P1 force tone " + mn[:12]
    mixn.inputs[0].default_value = 0.85
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], mixn.inputs[6])
    mixn.inputs[7].default_value = lk_base
    nt.links.new(mixn.outputs[2], bsdf.inputs["Base Color"])
    LOG.setdefault("plane_noise", []).append(mn)

bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()
LOG["elapsed_s"] = round(time.time() - t0, 1)
with open(os.path.join(os.path.dirname(__file__), "N4B_MAT_LOG.json"), "w", encoding="utf-8") as f:
    json.dump(LOG, f, ensure_ascii=False, indent=1)
print("N4B_DONE", {k: (len(v) if isinstance(v, list) else v) for k, v in LOG.items()})
