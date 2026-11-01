# Batch R5: equipment silhouette enrichment (E) + color noise cleanup (G)
import bpy, json, os, math, time, random
from mathutils import Vector, Euler

t0 = time.time()
sc = bpy.context.scene
LOG = {}

# ---------- materials ----------
def flat_mat(name, rgb, rough, metal=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    for lk in list(b.inputs['Base Color'].links):
        m.node_tree.links.remove(lk)
    b.inputs['Base Color'].default_value = (*rgb, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Specular IOR Level'].default_value = 0.3
    return m

dark_metal = flat_mat('P1 equip dark metal', (0.10, 0.10, 0.11), 0.55, 0.6)
rust_red   = flat_mat('P1 barrel rust red',  (0.30, 0.14, 0.10), 0.85)
leaf_a     = flat_mat('P1 fallen leaf A',    (0.55, 0.28, 0.12), 0.9)
leaf_b     = flat_mat('P1 fallen leaf B',    (0.44, 0.21, 0.10), 0.9)

# ---------- E1: tank hoops + top flange (tank column at ~(0.9,1.8), body z 0.65-2.1) ----------
made = []
for (z, r) in [(1.15, 0.38), (1.72, 0.37)]:
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.022,
                                     location=(0.9, 1.8, z), rotation=(0, 0, 0))
    t = bpy.context.object
    t.name = 'P1 tank hoop %d' % len(made)
    t.data.materials.append(dark_metal)
    made.append(t.name)
bpy.ops.mesh.primitive_cylinder_add(radius=0.30, depth=0.06, location=(0.9, 1.8, 2.16))
f1 = bpy.context.object; f1.name = 'P1 tank flange plate'; f1.data.materials.append(dark_metal)
bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.14, location=(0.9, 1.8, 2.26))
f2 = bpy.context.object; f2.name = 'P1 tank flange stub'; f2.data.materials.append(dark_metal)
made += [f1.name, f2.name]
LOG['tank_dress'] = made

# ---------- E2: crossover pipe tank -> power box top ----------
p0 = Vector((0.72, 1.80, 1.98))   # tank side
p1 = Vector((-1.05, 1.62, 1.12))  # power box top
mid = (p0 + p1) / 2
d = (p1 - p0)
L = d.length
q = d.normalized().to_track_quat('Z', 'Y')
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=L, location=mid, rotation=q.to_euler())
pipe = bpy.context.object; pipe.name = 'P1 crossover pipe'; pipe.data.materials.append(dark_metal)
for pnt, nm in [(p0, 'A'), (p1, 'B')]:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.085, location=pnt)
    s = bpy.context.object; s.name = 'P1 crossover elbow ' + nm; s.data.materials.append(dark_metal)
    made.append(s.name)
LOG['crossover'] = pipe.name

# ---------- E3: barrel in front of cabinet (adds foreground layer) ----------
bpy.ops.mesh.primitive_cylinder_add(radius=0.28, depth=0.55, location=(0.5, 0.12, 0.32))
bar = bpy.context.object; bar.name = 'P1 cabinet front barrel'; bar.data.materials.append(rust_red)
bpy.ops.mesh.primitive_torus_add(major_radius=0.28, minor_radius=0.02, location=(0.5, 0.12, 0.58))
ring = bpy.context.object; ring.name = 'P1 cabinet barrel rim'; ring.data.materials.append(dark_metal)
LOG['front_barrel'] = [bar.name, ring.name]

# ---------- G1: desaturate the 3 pennant fabrics ----------
for mn in ['Faded ochre fabric', 'Faded teal fabric', 'Dusty cream fabric']:
    m = bpy.data.materials.get(mn)
    if not (m and m.use_nodes): continue
    b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not b or b.inputs['Base Color'].is_linked: continue
    c = b.inputs['Base Color'].default_value
    g = (c[0] + c[1] + c[2]) / 3
    f = 0.5   # 55% toward gray
    b.inputs['Base Color'].default_value = (c[0]+(g-c[0])*f, c[1]+(g-c[1])*f, c[2]+(g-c[2])*f, 1.0)
    LOG.setdefault('fabric_desat', []).append(mn)

# ---------- G2: calm the over-orange sunlit slabs ----------
sm = bpy.data.materials.get('Sunlit limestone slab')
if sm and sm.use_nodes:
    b = next(n for n in sm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bc = b.inputs['Base Color']
    if bc.is_linked:
        lk = bc.links[0]
        mixn = sm.node_tree.nodes.new('ShaderNodeMix'); mixn.data_type = 'RGBA'; mixn.blend_type = 'MULTIPLY'
        mixn.name = 'P1 force trim sunlitcalm'
        mixn.inputs[0].default_value = 1.0
        mixn.inputs[6].default_value = (0.74, 0.68, 0.60, 1.0)
        sm.node_tree.links.new(lk.from_socket, mixn.inputs[7])
        sm.node_tree.links.new(mixn.outputs[2], bc)
        LOG['sunlit_calm'] = True

# ---------- G3: fallen-leaf scatter on the front lowland ----------
random.seed(511)
n_leaf = 0
for i in range(18):
    x = random.uniform(-8.5, 1.5)
    if -5.2 < x < -1.2: continue           # keep stair mouth clear
    y = random.uniform(-4.9, -3.9)
    r = random.uniform(0.05, 0.10)
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=0.008,
                                        location=(x, y, -1.26 + 0.02 * i / 18),
                                        rotation=(random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15), random.uniform(0, 3.14)))
    lf = bpy.context.object
    lf.name = 'P1 fallen leaf %02d' % i
    lf.data.materials.append(leaf_a if i % 2 else leaf_b)
    lf.scale = (1.0, random.uniform(0.6, 0.9), 1.0)
    n_leaf += 1
LOG['fallen_leaves'] = n_leaf

bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()
LOG['elapsed_s'] = round(time.time() - t0, 1)
with open(bpy.path.abspath('//preflight/R5_EQUIP_LOG.json'), 'w', encoding='utf-8') as f:
    json.dump(LOG, f, ensure_ascii=False, indent=1)
print('R5_DONE', {k: (v if not isinstance(v, list) else len(v)) for k, v in LOG.items()})
