# Batch R3: rebuild grass clump prototypes (art repair plan, D)
import bpy, json, os, math, time, random
from mathutils import Vector

t0 = time.time()
random.seed(20261101)
sc = bpy.context.scene
LOG = {}

# 1) locate shared prototype mesh and its grass material
old_mesh = bpy.data.meshes.get('v16 | CC0 grass silhouette var')
if old_mesh is None:
    for m in bpy.data.meshes:
        if 'grass silhouette' in m.name:
            old_mesh = m
            break
assert old_mesh, 'prototype mesh not found'
grass_mat = None
for m in old_mesh.materials:
    if m and 'grass' in m.name.lower():
        grass_mat = m
        break
if grass_mat is None:
    grass_mat = old_mesh.materials[0]
LOG['grass_mat'] = grass_mat.name

# collect instances
insts = [ob for ob in bpy.data.objects if ob.type == 'MESH' and ob.data == old_mesh]
LOG['instances'] = len(insts)

def build_clump(name, n_blades, length_range, tilt_range, curl):
    """Build a tuft mesh: blades bend outward then droop at the tip."""
    verts, faces = [], []
    for b in range(n_blades):
        az = random.uniform(0, 2 * math.pi)               # blade azimuth
        L = random.uniform(*length_range)                  # blade length
        tilt = random.uniform(*tilt_range)                 # outward lean at tip (m)
        w0 = random.uniform(0.018, 0.03)                   # root width
        bend_az = az + random.uniform(-0.5, 0.5)           # bend direction
        off = len(verts)
        rings = []
        for t in (0.0, 0.38, 0.72, 1.0):
            # centerline: lean outward with t, droop with curl at tip
            r_h = tilt * (t ** 1.4)                        # horizontal reach
            z = L * t * (1.0 - curl * (t ** 2.2))          # height, droops near tip
            cx = math.cos(az) * r_h
            cy = math.sin(az) * r_h
            w = w0 * (1.0 - t) ** 0.7 + 0.001              # taper to tip
            px, py = -math.sin(az) * w, math.cos(az) * w   # perpendicular offset
            verts.append((cx - px, cy - py, z))
            verts.append((cx + px, cy + py, z))
            rings.append(off + len(rings) * 2)
        for k in range(3):
            a, b_, c, d_ = rings[k], rings[k]+1, rings[k+1]+1, rings[k+1]
            faces.append((a, b_, c, d_))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.materials.append(grass_mat)
    return me

variants = [
    build_clump('v16 grass tuft A | arching', 11, (0.45, 0.85), (0.10, 0.30), 0.45),
    build_clump('v16 grass tuft B | drooping', 9, (0.55, 0.95), (0.18, 0.42), 0.70),
    build_clump('v16 grass tuft C | windswept', 10, (0.40, 0.80), (0.14, 0.36), 0.55),
]
LOG['variants'] = [m.name for m in variants]

# 2) reassign instances: deterministic hash split, keep each instance's random transform
counts = [0, 0, 0]
for ob in insts:
    idx = (hash(ob.name) & 0xffff) % 3
    ob.data = variants[idx]
    counts[idx] += 1
LOG['assigned'] = counts

bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()
LOG['elapsed_s'] = round(time.time() - t0, 1)
with open(bpy.path.abspath('//preflight/R3_GRASS_LOG.json'), 'w', encoding='utf-8') as f:
    json.dump(LOG, f, ensure_ascii=False, indent=1)
print('R3_DONE', {k: (v if not isinstance(v, list) else len(v)) for k, v in LOG.items()}, counts)
