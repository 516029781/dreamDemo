# Batch R8: final convergence push (paving warmth + orange patch + front pool grass)
import bpy, json, random, time
from mathutils import Vector, Euler

t0 = time.time()
random.seed(811)
sc = bpy.context.scene
LOG = {}

# 1) paving: warm all zone variants toward reference amber (216,195,170), widen tonal steps
WARM = {
    'V18 zone worn bright': (1.52, 1.38, 1.10),
    'V18 zone mid':         (1.30, 1.12, 0.82),
    'V18 zone aged A':      (1.05, 0.97, 0.78),
    'V18 zone aged B':      (0.84, 0.82, 0.78),
    'V18 zone warm dark':   (1.10, 0.97, 0.74),
}
fixed = 0
for mn, rgb in WARM.items():
    m = bpy.data.materials.get(mn)
    if not (m and m.use_nodes): continue
    for nd in m.node_tree.nodes:
        if nd.type == 'MIX' and 'warmup' in nd.name:
            nd.inputs[6].default_value = (*rgb, 1.0)
            fixed += 1
LOG['paving_warmed'] = fixed

# 2) the twice-flagged orange patch: turn sunlit slabs into deep warm repair boards
sm = bpy.data.materials.get('Sunlit limestone slab')
if sm and sm.use_nodes:
    for nd in sm.node_tree.nodes:
        if nd.type == 'MIX' and 'sunlitcalm' in nd.name:
            nd.inputs[6].default_value = (0.50, 0.46, 0.40, 1.0)
            LOG['sunlit_to_repair'] = True

# 3) front small pool grass: densify (S2 hard-gate fail)
scaled = 0
for ob in bpy.data.objects:
    if ob.type != 'MESH': continue
    if 'front planter C' in ob.name and ob.data.name.startswith('v16 grass tuft'):
        ob.scale = (ob.scale[0]*1.3, ob.scale[1]*1.3, ob.scale[2]*1.25)
        scaled += 1
donors = [o for o in bpy.data.objects if o.type == 'MESH' and o.data and o.data.name.startswith('v16 grass tuft') and 'front planter C' in o.name]
clones = 0
if donors:
    for i in range(12):
        src = random.choice(donors)
        d = src.copy()
        sc.collection.objects.link(d)
        d.name = 'P1 frontpool densify %02d' % i
        d.location = d.location + Vector((random.uniform(-0.3, 0.3), random.uniform(-0.25, 0.25), random.uniform(-0.04, 0.06)))
        s = random.uniform(0.9, 1.3)
        d.scale = (d.scale[0]*s, d.scale[1]*s, d.scale[2]*random.uniform(1.0, 1.35))
        d.rotation_euler = Euler((0, 0, random.uniform(0, 6.28)))
        clones += 1
LOG['frontpool'] = {'scaled': scaled, 'clones': clones}

# 4) global warmth: nudge compositor ColorBalance (API-tolerant)
nt = sc.compositing_node_group
for nd in nt.nodes:
    if nd.type == 'COLORBALANCE':
        try:
            g = nd.gain
            nd.gain = (g[0]*1.06, g[1]*1.0, g[2]*0.90)
            LOG['cb_gain_warmed'] = True
        except AttributeError:
            try:
                g = nd.slope
                nd.slope = (g[0]*1.06, g[1]*1.0, g[2]*0.90)
                LOG['cb_slope_warmed'] = True
            except AttributeError:
                LOG['cb_skipped'] = nd.name
        break

bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()
LOG['elapsed_s'] = round(time.time() - t0, 1)
with open(bpy.path.abspath('//preflight/R8_CONVERGE_LOG.json'), 'w', encoding='utf-8') as f:
    json.dump(LOG, f, ensure_ascii=False, indent=1)
print('R8_DONE', {k: (v if not isinstance(v, dict) else len(v)) for k, v in LOG.items()})
