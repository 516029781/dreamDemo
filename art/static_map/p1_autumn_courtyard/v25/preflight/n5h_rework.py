# Rework batch H (blind-review driven): fix the two failed hard gates + combo
# gaps. Methods chosen differ from previous attempts per the two-strike rule.
#  1) far shore: crown-card screen in front of M02 prism + cool the plates
#  2) grass: per-cluster vertex scatter (blades splay, root-dense) instead of
#     cluster-transform-only randomization
#  3) paving: roughness variation noise
#  4) green understory -> warm brown (reference has no green shrubs)
import bpy, json, os, math, random, time
from mathutils import Euler, Vector

t0 = time.time()
random.seed(251107)
sc = bpy.context.scene
LOG = {}

# ---- 1) far-shore crown screen (single-user copies, grounded) ----
proto = None
for ob in sc.objects:
    if ob.name.startswith('P1 crown | ') and ob.type == 'MESH':
        proto = ob
        break
made = 0
if proto:
    spots = []
    for i in range(8):
        x = random.uniform(-18.0, -6.0) if i % 2 == 0 else random.uniform(6.0, 18.0)
        y = random.uniform(19.8, 21.6)
        s = random.uniform(0.40, 0.66)
        spots.append((x, y, s, random.uniform(0, 6.28)))
    for i, (x, y, s, rz) in enumerate(spots):
        me = proto.data.copy()
        ob = bpy.data.objects.new('P1 shore screen %02d' % i, me)
        sc.collection.objects.link(ob)
        ob.location = (x, y, 0.25)
        ob.scale = (s, s, s * random.uniform(0.8, 1.05))
        ob.rotation_euler = Euler((0, 0, rz))
        made += 1
    LOG['shore_screen'] = made

# ---- 2) cool + lift the M02/M03 far plates ----
for mn, fac in [('M02 | far bank plate mat', (0.72, 0.80, 0.92)),
                ('M03 | distant air plate mat', (0.62, 0.72, 0.88))]:
    m = bpy.data.materials.get(mn)
    if m and m.use_nodes:
        nt = m.node_tree
        bsdf = next((n for n in nt.nodes if n.type in ('BSDF_PRINCIPLED', 'BSDF_DIFFUSE', 'EMISSION')), None)
        if bsdf:
            for inp in ('Base Color', 'Color'):
                if inp in bsdf.inputs and bsdf.inputs[inp].is_linked:
                    lk = bsdf.inputs[inp].links[0]
                    mixn = nt.nodes.new('ShaderNodeMix')
                    mixn.data_type = 'RGBA'
                    mixn.blend_type = 'MIX'
                    mixn.name = 'P1 force trim ' + mn[:8]
                    mixn.inputs[0].default_value = 0.55
                    mixn.inputs[6].default_value = (fac[0]*0.9, fac[1]*0.9, fac[2], 1.0)
                    nt.links.new(lk.from_socket, mixn.inputs[7])
                    nt.links.new(mixn.outputs[2], bsdf.inputs[inp])
                    LOG.setdefault('plate_cooled', []).append(mn)
                    break

# ---- 3) per-cluster vertex scatter on grass (blades splay) ----
disp_tex = bpy.data.textures.new('P1 grass scatter', 'CLOUDS')
disp_tex.noise_scale = 0.35
count = 0
for ob in sc.objects:
    if ob.type != 'MESH' or ob.hide_render:
        continue
    if ob.name.startswith(('v16 grass clump', 'P1 veg | barrel grass', 'P1 veg | low grass')):
        has = any(md.type == 'DISPLACE' for md in ob.modifiers)
        if not has:
            md = ob.modifiers.new('scatter', 'DISPLACE')
            md.texture = disp_tex
            md.texture_coords = 'GLOBAL'
            md.strength = 0.055
            md.mid_level = 0.5
            count += 1
LOG['grass_scatter'] = count

# ---- 4) tower-crown top density: second layer copies ----
barrel_proto = None
for ob in sc.objects:
    if ob.name.startswith('P1 veg | barrel grass') and ob.type == 'MESH':
        barrel_proto = ob
        break
made2 = 0
if barrel_proto:
    for i in range(8):
        a = 2 * math.pi * i / 8
        r = random.uniform(1.2, 1.9)
        x = 7.25 + r * math.cos(a)
        y = 3.70 + r * math.sin(a)
        me = barrel_proto.data.copy()
        ob = bpy.data.objects.new('P1 tower top grass %02d' % i, me)
        sc.collection.objects.link(ob)
        s = random.uniform(0.8, 1.15)
        ob.location = (x, y, 3.66)
        ob.scale = (s, s, s * random.uniform(0.85, 1.1))
        ob.rotation_euler = Euler((0, 0, random.uniform(0, 6.28)))
        made2 += 1
    LOG['tower_top_grass'] = made2

# ---- 5) paving roughness variation ----
pm = bpy.data.materials.get('V18 | P1 unified midtone limestone paving')
if pm and pm.use_nodes:
    nt = pm.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf:
        rgh = bsdf.inputs['Roughness']
        if not rgh.is_linked:
            noise = nt.nodes.new('ShaderNodeTexNoise')
            noise.inputs['Scale'].default_value = 9.0
            noise.inputs['Detail'].default_value = 8.0
            ramp = nt.nodes.new('ShaderNodeValToRGB')
            ramp.color_ramp.elements[0].position = 0.35
            ramp.color_ramp.elements[0].color = (0.72, 0.72, 0.72, 1.0)
            ramp.color_ramp.elements[1].position = 0.75
            ramp.color_ramp.elements[1].color = (0.97, 0.97, 0.97, 1.0)
            nt.links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
            nt.links.new(ramp.outputs['Color'], rgh)
            LOG['paving_rough'] = True

# ---- 6) green understory -> warm brown ----
for ob in sc.objects:
    if 'understory' in ob.name and ob.data and ob.data.materials:
        for m in ob.data.materials:
            if m and m.use_nodes:
                for nd in m.node_tree.nodes:
                    if nd.type == 'BSDF_PRINCIPLED' and not nd.inputs['Base Color'].is_linked:
                        c = nd.inputs['Base Color'].default_value
                        g = (c[0] + c[1] + c[2]) / 3
                        nd.inputs['Base Color'].default_value = (g * 1.5, g * 1.05, g * 0.62, 1.0)
                        LOG['understory_warm'] = True

bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()
LOG['elapsed_s'] = round(time.time() - t0, 1)
with open(os.path.join(os.path.dirname(__file__), 'N5H_REWORK_LOG.json'), 'w', encoding='utf-8') as f:
    json.dump(LOG, f, ensure_ascii=False, indent=1)
print('BATCH_H_DONE', {k: (v if not isinstance(v, list) else len(v)) for k, v in LOG.items()})
