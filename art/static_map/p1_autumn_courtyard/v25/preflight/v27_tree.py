"""V27B: rebuild left tree crown with 3 layers of hand-painted mass cards.
- Delete old cards + fine twiggy foliage overlay; keep trunk (LOD1) and canopy gobo
- New cards face the locked camera, painted-light materials (emission-led)
Usage: blender scene.blend -b --python v27_tree.py -- <V25_DIR>
"""
import bpy, json, sys, os, math, random
from mathutils import Vector, Quaternion

V25 = sys.argv[sys.argv.index("--") + 1]
TEX_DIR = os.path.join(V25, "assets", "handpainted")
LOG = os.path.join(V25, "preflight", "V27_TREE_LOG.json")
log = {"deleted": [], "created": [], "errors": []}

scene = bpy.context.scene
CAM_POS = Vector((0.25, -20.5, 8.2))
CROWN = Vector((-8.9, 7.0, 1.15))

# ---------- delete old crown ----------
DEL = ["P1 canopy inner A", "P1 canopy inner B", "P1 canopy inner C",
       "P1 canopy top layer", "P1 broadleaf foliage overlay | widened canopy"]
for n in DEL:
    ob = bpy.data.objects.get(n)
    if ob:
        log["deleted"].append(n)
        bpy.data.objects.remove(ob, do_unlink=True)
    else:
        log["errors"].append("not found: " + n)

# delete misplaced distant-grove lobes hanging in the left tree crown
import mathutils
for ob in list(bpy.context.scene.collection.all_objects):
    if ob.type == "MESH" and ob.name.startswith("Distant grove foliage lobe"):
        p = ob.matrix_world.translation
        if -13 < p.x < -6 and 4 < p.y < 11 and p.z < 5:
            log["deleted"].append(ob.name + " (grove lobe)")
            bpy.data.objects.remove(ob, do_unlink=True)

# strip the tree's own fine leaf-card faces (slot 1 'P1 autumn leaves'), warm the branches
lod = bpy.data.objects.get("P1 broadleaf | Poly Haven Tree Small 02 LOD1")
if lod and lod.type == "MESH":
    leaf_slot = None
    for i, m in enumerate(lod.data.materials):
        if m and "autumn leaves" in m.name:
            leaf_slot = i
    if leaf_slot is not None:
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(lod.data)
        removed = sum(1 for f in bm.faces if f.material_index == leaf_slot)
        for f in list(bm.faces):
            if f.material_index == leaf_slot:
                bm.faces.remove(f)
        bm.to_mesh(lod.data)
        bm.free()
        lod.data.update()
        log["deleted"].append(f"LOD1 leaf faces ({removed} faces, slot {leaf_slot})")
    bm_name = lod.data.materials[0].name if lod.data.materials else None
    if bm_name:
        src = bpy.data.materials[bm_name]
        users = [o for o in bpy.data.objects if o.type == "MESH"
                 and any(m and m.name == bm_name for m in o.data.materials)]
        target = src if len(users) == 1 else src.copy()
        if target is not src:
            target.name = "P1 tree branch warm"
            lod.material_slots[0].link = "OBJECT"
            lod.material_slots[0].material = target
        target.use_nodes = True
        nt = target.node_tree
        principled = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if principled:
            bc = principled.inputs["Base Color"]
            mul = nt.nodes.new("ShaderNodeMixRGB")
            mul.blend_type = "MULTIPLY"
            mul.inputs["Fac"].default_value = 1.0
            mul.inputs["Color2"].default_value = (0.52, 0.36, 0.22, 1.0)  # warm dark
            if bc.is_linked:
                src_sock = bc.links[0].from_socket
                nt.links.new(src_sock, mul.inputs["Color1"])
            else:
                mul.inputs["Color1"].default_value = bc.default_value
            nt.links.new(mul.outputs["Color"], bc)
        log["deleted"].append(f"branch material warmed ({bm_name}, users={len(users)})")

# ---------- textures & materials ----------
def load_tex(name):
    path = os.path.join(TEX_DIR, name)
    img = bpy.data.images.get(name)
    if img is None:
        img = bpy.data.images.load(path)
        img.name = name
    return img

tex_a = load_tex("leaf_cluster_a.png")
tex_b = load_tex("leaf_cluster_b.png")
tex_full = load_tex("canopy_full.png")

def make_leaf_mat(name, img, tint):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Cubic"
    mul = nt.nodes.new("ShaderNodeMixRGB")
    mul.blend_type = "MULTIPLY"
    mul.inputs["Fac"].default_value = 1.0
    mul.inputs["Color2"].default_value = (*tint, 1.0)
    emis = nt.nodes.new("ShaderNodeEmission")
    emis.inputs["Strength"].default_value = 0.55
    diff = nt.nodes.new("ShaderNodeBsdfPrincipled")
    diff.inputs["Roughness"].default_value = 1.0
    add = nt.nodes.new("ShaderNodeAddShader")
    mixa = nt.nodes.new("ShaderNodeMixShader")
    mixa.inputs["Fac"].default_value = 0.5  # half painted light, half scene light
    nt.links.new(tex.outputs["Color"], mul.inputs["Color1"])
    nt.links.new(mul.outputs["Color"], emis.inputs["Color"])
    nt.links.new(mul.outputs["Color"], diff.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], diff.inputs["Alpha"])
    nt.links.new(emis.outputs[0], add.inputs[0])
    nt.links.new(diff.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], mixa.inputs[1])
    nt.links.new(diff.outputs[0], mixa.inputs[2])
    nt.links.new(mixa.outputs[0], out.inputs["Surface"])
    mat.blend_method = "CLIP"
    return mat

mat_inner = make_leaf_mat("HP crown dark", tex_full, (0.42, 0.32, 0.24))
mat_mid_a = make_leaf_mat("HP crown main", tex_full, (1.0, 1.0, 1.0))
mat_mid_b = make_leaf_mat("HP crown warm", tex_full, (0.95, 0.85, 0.72))
mat_outer = make_leaf_mat("HP crown lit", tex_full, (1.22, 1.10, 0.88))

# ---------- card mesh (1x1 plane, +Z front) ----------
mesh = bpy.data.meshes.get("HP canopy card")
if mesh is None:
    mesh = bpy.data.meshes.new("HP canopy card")
    mesh.from_pydata([(-0.5, -0.5, 0), (0.5, -0.5, 0), (0.5, 0.5, 0), (-0.5, 0.5, 0)],
                     [], [(0, 1, 2, 3)])
    mesh.update()
    uv = mesh.uv_layers.new()
    uv.data[0].uv = (0, 0); uv.data[1].uv = (1, 0)
    uv.data[2].uv = (1, 1); uv.data[3].uv = (0, 1)

# ---------- card factory ----------
rnd = random.Random(271)

def add_card(name, pos, size, mat, roll=None):
    ob = bpy.data.objects.new(name, mesh)
    ob.location = pos
    away = pos - CAM_POS
    q = away.to_track_quat("-Z", "Y")  # -Z away => +Z faces camera
    if roll is None:
        roll = rnd.uniform(-0.35, 0.35)
    ob.rotation_quaternion = q @ Quaternion((0.0, 0.0, 1.0), roll)
    ob.scale = (size, size, 1.0)
    ob.data = mesh
    ob.data.materials.clear()
    scene.collection.objects.link(ob)  # MUST link (v26 lesson)
    ob.hide_render = False
    ob.hide_viewport = False
    # per-card material slot on object level via mesh copy is heavy; use object link
    ob.material_slots  # ensure slot exists
    if not ob.material_slots:
        ob.data = mesh  # shared mesh: assign per-object via slot override not possible
    log["created"].append({"name": name, "loc": [round(v, 3) for v in pos], "size": size})
    return ob

# shared mesh cannot carry per-object materials -> create per-card mesh copies (cheap, 12 cards)
def add_card2(name, pos, size, mat, roll=None):
    m = mesh.copy()
    ob = bpy.data.objects.new(name, m)
    ob.location = pos
    away = pos - CAM_POS
    q = away.to_track_quat("-Z", "Y")
    if roll is None:
        roll = rnd.uniform(-0.35, 0.35)
    ob.rotation_quaternion = q @ Quaternion((0.0, 0.0, 1.0), roll)
    ob.scale = (size, size, 1.0)
    m.materials.append(mat)
    scene.collection.objects.link(ob)
    ob.hide_render = False
    ob.hide_viewport = False
    log["created"].append({"name": name, "loc": [round(v, 3) for v in pos], "size": size})
    return ob

# main: one big cohesive canopy mass + supporting cards (hand-painted way)
add_card2("P1 HP canopy main", CROWN + Vector((-0.05, -0.1, 0.1)), 3.6, mat_mid_a, roll=rnd.uniform(-0.1, 0.1))
add_card2("P1 HP canopy dark back", CROWN + Vector((-0.75, 0.3, -0.4)), 2.8, mat_inner, roll=-0.3)
add_card2("P1 HP canopy dark low-left", CROWN + Vector((-1.05, 0.3, -0.55)), 2.0, mat_inner, roll=0.4)
add_card2("P1 HP canopy upper-left", CROWN + Vector((-0.6, 0.35, 0.55)), 2.2, mat_mid_b, roll=0.35)
add_card2("P1 HP canopy right", CROWN + Vector((0.85, -0.2, 0.0)), 1.9, mat_outer, roll=0.2)
add_card2("P1 HP canopy top", CROWN + Vector((0.15, 0.25, 0.72)), 1.8, mat_outer, roll=-0.15)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(V25, "scene.blend"))
with open(LOG, "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=1)
print("V27B_DONE deleted=%d created=%d errors=%d" % (len(log["deleted"]), len(log["created"]), len(log["errors"])))
