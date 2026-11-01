# Batch R7: consensus fixes after blind reviews R1/R2 (tree size + grass density)
import bpy, math, random, time
from mathutils import Vector, Euler

t0 = time.time()
random.seed(711)
sc = bpy.context.scene
LOG = {}
# 1) ENLARGE the left tree (both reviewers: crown must dominate upper-left like reference)
for nm in ['P1 broadleaf | Poly Haven Tree Small 02 LOD1', 'P1 broadleaf foliage overlay | widened canopy']:
    ob = bpy.data.objects.get(nm)
    if ob:
        r = 1.10 / ob.scale[0]
        ob.scale = (ob.scale[0] * r, ob.scale[1] * r, ob.scale[2] * r)
        ob.location.z = 0.05
        LOG.setdefault('tree_scaled', []).append(nm[:30])
for i in range(3):
    ob = bpy.data.objects.get('P1 canopy clump %02d' % i)
    if ob:
        ob.scale = (ob.scale[0] * 1.32, ob.scale[1] * 1.32, ob.scale[2] * 1.32)
main = bpy.data.objects.get('P1 broadleaf | Poly Haven Tree Small 02 LOD1')
ov = bpy.data.objects.get('P1 broadleaf foliage overlay | widened canopy')
if main: main.location.x -= 0.3
if ov: ov.location.x -= 0.35; ov.location.y += 0.15

# 2) GRASS DENSITY: scale up tower/planters grass, fill bare soil with extra tufts
scaled = 0
for ob in bpy.data.objects:
    if ob.type != 'MESH': continue
    if 'barrel grass' in ob.name or 'tower top grass' in ob.name or 'golden crown' in ob.name:
        ob.scale = (ob.scale[0] * 1.25, ob.scale[1] * 1.25, ob.scale[2] * 1.2)
        scaled += 1
LOG['grass_scaled'] = scaled
clones = 0
donors = [o for o in bpy.data.objects if o.type == 'MESH' and o.data and o.data.name.startswith('v16 grass tuft') and ('tower crown' in o.name or 'planter' in o.name)]
for i in range(36):
    src = random.choice(donors) if donors else None
    if src is None: break
    d = src.copy()
    sc.collection.objects.link(d)
    d.name = 'P1 densify tuft %02d' % i
    d.location = d.location + Vector((random.uniform(-0.35, 0.35), random.uniform(-0.35, 0.35), random.uniform(-0.05, 0.08)))
    s = random.uniform(0.85, 1.25)
    d.scale = (d.scale[0] * s, d.scale[1] * s, d.scale[2] * random.uniform(0.9, 1.3))
    d.rotation_euler = Euler((0, 0, random.uniform(0, 6.28)))
    clones += 1
LOG['densify_clones'] = clones

# 3) crumpled gold piles: shrink so they read as mulch under grass
cnt = 0
for ob in bpy.data.objects:
    if ob.type != 'MESH': continue
    n = ob.name.lower()
    if ('dry grass bed' in n or 'mulch' in n or 'straw' in n) and 'kerb' not in n:
        ob.scale = (ob.scale[0] * 0.82, ob.scale[1] * 0.82, ob.scale[2] * 0.75)
        cnt += 1
LOG['mulch_shrunk'] = cnt

bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()
LOG['elapsed_s'] = round(time.time() - t0, 1)
with open(bpy.path.abspath('//preflight/R7_DENSITY_LOG.json'), 'w', encoding='utf-8') as f:
    json.dump(LOG, f, ensure_ascii=False, indent=1)
print('R7_DONE', {k: (v if not isinstance(v, list) else len(v)) for k, v in LOG.items()})
