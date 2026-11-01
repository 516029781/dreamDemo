"""V27C: replace fine-wire grass instances with hand-painted tuft cards.
Instances = the 127 objects whose meshes were silhouette-restored in V26 (changed='mesh').
Density x2 via one offset clone per instance; depth-graded tint.
Usage: blender scene.blend -b --python v27_grass.py -- <V25_DIR>
"""
import bpy, json, sys, os, math, random
from mathutils import Vector

V25 = sys.argv[sys.argv.index("--") + 1]
TEX = os.path.join(V25, "assets", "handpainted", "grass_tuft.png")
V26LOG = os.path.join(V25, "preflight", "V26_REWORK_LOG.json")
LOG = os.path.join(V25, "preflight", "V27_GRASS_LOG.json")
log = {"instances": 0, "clones": 0, "tints": {"bright": 0, "mid": 0, "dark": 0}, "errors": []}

scene = bpy.context.scene
rnd = random.Random(727)

d = json.load(open(V26LOG, encoding="utf-8"))
names = [k for k, v in d.get("grass_overrides", {}).items() if v.get("changed") == "mesh"]
print("GRASS_INSTANCES", len(names))

# texture
img = bpy.data.images.get("grass_tuft.png") or bpy.data.images.load(TEX)
img.name = "grass_tuft.png"

def make_grass_mat(name, tint):
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
    emis.inputs["Strength"].default_value = 0.7
    diff = nt.nodes.new("ShaderNodeBsdfPrincipled")
    diff.inputs["Roughness"].default_value = 1.0
    add = nt.nodes.new("ShaderNodeAddShader")
    mixa = nt.nodes.new("ShaderNodeMixShader")
    mixa.inputs["Fac"].default_value = 0.6
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

mat_bright = make_grass_mat("HP grass bright", (1.06, 1.0, 0.88))
mat_mid = make_grass_mat("HP grass mid", (0.92, 0.85, 0.72))
mat_dark = make_grass_mat("HP grass dark", (0.76, 0.68, 0.56))

# card mesh: vertical quad in XZ, origin bottom-center, normal -Y (faces camera)
def make_card_mesh(name, mat):
    m = bpy.data.meshes.new(name)
    m.from_pydata([(-0.5, 0, 0), (0.5, 0, 0), (0.5, 0, 1), (-0.5, 0, 1)],
                  [], [(0, 1, 2, 3)])
    m.update()
    uv = m.uv_layers.new()
    uv.data[0].uv = (0, 0); uv.data[1].uv = (1, 0)
    uv.data[2].uv = (1, 1); uv.data[3].uv = (0, 1)
    m.materials.append(mat)
    return m

mesh_bright = make_card_mesh("HP grass card bright", mat_bright)
mesh_mid = make_card_mesh("HP grass card mid", mat_mid)
mesh_dark = make_card_mesh("HP grass card dark", mat_dark)

def pick_mesh(y):
    if y < 5: return mesh_bright
    if y < 14: return mesh_mid
    return mesh_dark

def spawn(name, mesh, loc, base_scale):
    ob = bpy.data.objects.new(name, mesh)
    ob.location = loc
    tilt = math.radians(rnd.uniform(4, 14) * (1 if rnd.random() < 0.5 else -1))
    yaw = rnd.uniform(-0.35, 0.35)
    ob.rotation_euler = (tilt, 0.0, yaw)
    s = base_scale * rnd.uniform(0.85, 1.15)
    ob.scale = (s, s, s)
    scene.collection.objects.link(ob)
    ob.hide_render = False
    ob.hide_viewport = False
    return ob

for n in names:
    ob = bpy.data.objects.get(n)
    if ob is None or ob.type != "MESH":
        log["errors"].append("missing: " + str(n))
        continue
    loc = tuple(ob.location)
    if ob.parent:
        # keep world-ish position: convert to parent space not needed; instances are top-level in practice
        pass
    y = loc[1]
    m = pick_mesh(y)
    ob.data = m
    ob.rotation_euler = (math.radians(rnd.uniform(4, 14) * (1 if rnd.random() < 0.5 else -1)), 0.0, rnd.uniform(-0.35, 0.35))
    s = rnd.uniform(0.9, 1.15)
    ob.scale = (s, s, s)
    ob.hide_render = False
    log["instances"] += 1
    log["tints"]["bright" if m is mesh_bright else "mid" if m is mesh_mid else "dark"] += 1
    # density clone
    off = (rnd.uniform(-0.28, 0.28), rnd.uniform(-0.2, 0.2), 0.0)
    clone = spawn(n + ".hp", m, (loc[0] + off[0], loc[1] + off[1], loc[2]), s * 0.95)
    if ob.parent:
        clone.parent = ob.parent
    log["clones"] += 1

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(V25, "scene.blend"))
with open(LOG, "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=1)
print("V27C_DONE instances=%d clones=%d errors=%d" % (log["instances"], log["clones"], len(log["errors"])))
