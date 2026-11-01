# N4 R10 + local light/color: one hypothesis batch.
# Hypothesis: material identity (wood grain vs stripe, metal sheen, kerb grass
# density, far-bank contrast) is the main remaining gap; no camera/exposure
# change in this batch.
import bpy, json, os, time, random
from mathutils import Euler

t0 = time.time()
random.seed(251104)
sc = bpy.context.scene
LOG = {}

# 1) wood crate: flatten the wave-stripe ramp + break evenness with noise
m = bpy.data.materials.get("Old stained wood")
if m and m.use_nodes:
    nt = m.node_tree
    for nd in nt.nodes:
        if nd.type == 'VALTORGB' and len(nd.color_ramp.elements) >= 2:
            els = nd.color_ramp.elements
            c0 = list(els[0].color); c1 = list(els[-1].color)
            mid = [(a + b) / 2 for a, b in zip(c0[:3], c1[:3])] + [1.0]
            for e, c in ((els[0], c0), (els[-1], c1)):
                e.color = [mid[i] * 0.55 + c[i] * 0.45 for i in range(3)] + [1.0]
            LOG["wood_ramp_flattened"] = True
    # multiply a soft noise into base color to break even striping
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf and bsdf.inputs["Base Color"].is_linked:
        lk = bsdf.inputs["Base Color"].links[0]
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 7.0
        noise.inputs["Detail"].default_value = 6.0
        mixn = nt.nodes.new("ShaderNodeMix")
        mixn.data_type = 'RGBA'
        mixn.blend_type = 'MULTIPLY'
        mixn.name = "P1 force trim woodnoise"
        mixn.inputs[0].default_value = 0.35
        mixn.inputs[6].default_value = (1.15, 1.0, 0.9, 1.0)
        nt.links.new(lk.from_socket, mixn.inputs[7])
        nt.links.new(noise.outputs["Fac"], mixn.inputs[0])
        nt.links.new(mixn.outputs[2], bsdf.inputs["Base Color"])
        LOG["wood_noise_added"] = True

# 2) metals: lower sheen
for mn in ("Muted rust service metal",):
    mm = bpy.data.materials.get(mn)
    if mm and mm.use_nodes:
        for nd in mm.node_tree.nodes:
            if nd.type == 'BSDF_PRINCIPLED' and "Specular IOR Level" in nd.inputs:
                nd.inputs["Specular IOR Level"].default_value = 0.28
                LOG["metal_spec"] = 0.28

# 3) kerb grass beds: duplicate for density (offset avoids z-fight)
stone_src = ["P1 yard | kerb A | dry grass bed", "P1 yard | kerb B | dry grass bed"]
for i, nm in enumerate(stone_src):
    ob = bpy.data.objects.get(nm)
    if ob:
        d = ob.copy()   # linked duplicate
        sc.collection.objects.link(d)
        d.name = nm + " fill"
        d.location = d.location + __import__("mathutils").Vector((0.045, 0.03, 0.01))
        d.scale = (d.scale[0] * 1.05, d.scale[1] * 1.05, d.scale[2] * 0.95)
        d.rotation_euler = Euler((0, 0, 0.06 if i else -0.05))
        LOG["kerb_grass_doubled"] = LOG.get("kerb_grass_doubled", 0) + 1

# 4) far bank: lift base toward muted warm gray to cut harsh contrast
fb = bpy.data.materials.get("P1 tier | far bank")
if fb and fb.use_nodes:
    for nd in fb.node_tree.nodes:
        if nd.type == 'BSDF_PRINCIPLED':
            nd.inputs["Base Color"].default_value = (0.085, 0.078, 0.062, 1.0)
            LOG["farbank_base"] = [0.085, 0.078, 0.062]

# 5) low-ground planes: slightly desaturated toward cool to help depth
lg = bpy.data.materials.get("P1 tier | low ground")
if lg and lg.use_nodes:
    for nd in lg.node_tree.nodes:
        if nd.type == 'BSDF_PRINCIPLED' and not nd.inputs["Base Color"].is_linked:
            c = nd.inputs["Base Color"].default_value
            nd.inputs["Base Color"].default_value = (c[0] * 0.92, c[1] * 0.94, min(1.0, c[2] * 1.06), 1.0)
            LOG["lowground_shift"] = True

bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()
LOG["elapsed_s"] = round(time.time() - t0, 1)
with open(os.path.join(os.path.dirname(__file__), "N4_MAT_LOG.json"), "w", encoding="utf-8") as f:
    json.dump(LOG, f, ensure_ascii=False, indent=1)
print("N4_DONE", LOG)
