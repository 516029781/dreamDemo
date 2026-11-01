# Batch R4: paving age via large-block tonal rhythm (art repair plan, C)
import bpy, json, os, math, time
from mathutils import Vector

t0 = time.time()
sc = bpy.context.scene
LOG = {'zones': {}, 'patched': [], 'facade': []}

src_mat = bpy.data.materials.get('V18 | P1 unified midtone limestone paving')
assert src_mat, 'paving material missing'

def zone_variant(name, warm_rgb):
    m = src_mat.copy()
    m.name = name
    for nd in m.node_tree.nodes:
        if nd.type == 'MIX' and 'warmup' in nd.name:
            nd.inputs[6].default_value = (warm_rgb[0], warm_rgb[1], warm_rgb[2], 1.0)
            return m
    # fallback: add multiply
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    bc = bsdf.inputs['Base Color']
    lk = bc.links[0]
    mixn = nt.nodes.new('ShaderNodeMix'); mixn.data_type = 'RGBA'; mixn.blend_type = 'MULTIPLY'
    mixn.name = 'P1 force trim warmup'
    mixn.inputs[0].default_value = 1.0
    mixn.inputs[6].default_value = (warm_rgb[0], warm_rgb[1], warm_rgb[2], 1.0)
    nt.links.new(lk.from_socket, mixn.inputs[7])
    nt.links.new(mixn.outputs[2], bc)
    return m

ZONE_MATS = {
    'worn_bright':  zone_variant('V18 zone worn bright',  (1.40, 1.30, 1.16)),   # trafficked, bleached
    'mid':          zone_variant('V18 zone mid',          (1.22, 1.10, 0.92)),   # original tone
    'aged_a':       zone_variant('V18 zone aged A',       (1.02, 0.99, 0.93)),
    'aged_b':       zone_variant('V18 zone aged B',       (0.88, 0.87, 0.86)),   # coolest/darkest
    'warm_dark':    zone_variant('V18 zone warm dark',    (1.04, 0.97, 0.86)),
}

STAIR_MOUTH = Vector((-2.6, -0.9, 0))
EQUIP = Vector((2.0, 2.6, 0))

slabs = [ob for ob in bpy.data.objects if ob.type == 'MESH' and 'limestone slab' in ob.name.lower()]
counts = {k: 0 for k in ZONE_MATS}
patch_candidates = []
for ob in slabs:
    c = sum(((ob.matrix_world @ Vector(cc)) for cc in ob.bound_box), Vector()) / 8
    d_stair = (Vector((c.x, c.y, 0)) - STAIR_MOUTH).length
    d_equip = (Vector((c.x, c.y, 0)) - EQUIP).length
    if d_stair < 3.2:
        mat, key = ZONE_MATS['worn_bright'], 'worn_bright'
    elif d_equip < 2.6:
        mat, key = ZONE_MATS['mid'], 'mid'
    elif c.x < -4:
        mat, key = ZONE_MATS['aged_b'], 'aged_b'
        patch_candidates.append((c.x, ob))
    elif c.x < 2:
        mat, key = ZONE_MATS['aged_a'], 'aged_a'
    else:
        mat, key = ZONE_MATS['warm_dark'], 'warm_dark'
    ob.data.materials[0] = mat
    counts[key] += 1
LOG['zones'] = counts

# 2) 3 darker "repaired new slabs" spread across aged zones (narrative of repair)
patch_candidates.sort(key=lambda t: t[0])
for i, (_, ob) in enumerate([patch_candidates[0], patch_candidates[len(patch_candidates)//2], patch_candidates[-1]]):
    pm = bpy.data.materials.get('P1 paving repair slab %d' % i) or bpy.data.materials.new('P1 paving repair slab %d' % i)
    pm.use_nodes = True
    bsdf = pm.node_tree.nodes.get('Principled BSDF') or next(n for n in pm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = (0.30, 0.275, 0.245, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.92
    bsdf.inputs['Specular IOR Level'].default_value = 0.25
    for lk in list(bsdf.inputs['Base Color'].links):
        pm.node_tree.links.remove(lk)
    ob.data.materials[0] = pm
    LOG['patched'].append(ob.name)

# 3) facades: give stair cheeks / fascias / plinths a slightly deeper, less plastic copy
for mn in ['Recessed warm joints', 'Stone worn edges']:
    src = bpy.data.materials.get(mn)
    if not (src and src.use_nodes): continue
    cp = src.copy(); cp.name = mn + ' facade aged'
    nt = cp.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf and bsdf.inputs['Base Color'].is_linked:
        lk = bsdf.inputs['Base Color'].links[0]
        mixn = nt.nodes.new('ShaderNodeMix'); mixn.data_type = 'RGBA'; mixn.blend_type = 'MULTIPLY'
        mixn.name = 'P1 force trim facadeage'
        mixn.inputs[0].default_value = 1.0
        mixn.inputs[6].default_value = (0.90, 0.875, 0.845, 1.0)
        nt.links.new(lk.from_socket, mixn.inputs[7])
        nt.links.new(mixn.outputs[2], bsdf.inputs['Base Color'])
    used = 0
    for ob in bpy.data.objects:
        if ob.type == 'MESH' and any(k in ob.name.lower() for k in ['fascia', 'plinth', 'cheek', 'deep platform']):
            for si, m in enumerate(ob.data.materials):
                if m and m.name == mn:
                    ob.data.materials[si] = cp
                    used += 1
    LOG['facade'].append('%s -> %d objs' % (mn, used))

bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()
LOG['elapsed_s'] = round(time.time() - t0, 1)
with open(bpy.path.abspath('//preflight/R4_PAVING_LOG.json'), 'w', encoding='utf-8') as f:
    json.dump(LOG, f, ensure_ascii=False, indent=1)
print('R4_DONE', {k: (v if not isinstance(v, list) else len(v)) for k, v in LOG.items()})
