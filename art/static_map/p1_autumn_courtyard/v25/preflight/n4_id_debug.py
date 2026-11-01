# One-off object-id debug render: flat random color per object.
import bpy, os, random, colorsys

sc = bpy.context.scene
HERE = os.path.dirname(__file__)
RD = os.path.join(os.path.dirname(HERE), "renders")
random.seed(7)
cam = sc.camera
dof0 = cam.data.dof.use_dof
cam.data.dof.use_dof = False
vl = bpy.context.view_layer
vl.material_override = None
ids = {}
mats = {}
for ob in sc.objects:
    if ob.type != 'MESH' or ob.hide_render:
        continue
    key = ob.name.split('.')[0][:28]
    if key not in mats:
        h = random.random()
        c = colorsys.hsv_to_rgb(h, 0.75, 0.95)
        m = bpy.data.materials.new("IDTMP " + key)
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs[0].default_value = (c[0], c[1], c[2], 1)
        em.inputs[1].default_value = 1.0
        outn = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(em.outputs[0], outn.inputs[0])
        mats[key] = m
        ids["%02x%02x%02x" % (int(c[0]*255), int(c[1]*255), int(c[2]*255))] = key
    ob.data.materials.clear()
    ob.data.materials.append(mats[key])
w0 = sc.world.node_tree.nodes.get("Background")
wcol = tuple(w0.inputs[0].default_value)
w0.inputs[0].default_value = (0, 0, 0, 1)
res0 = (sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage)
s0 = sc.cycles.samples
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 960, 539, 100
sc.cycles.samples = 8
sc.render.filepath = os.path.join(RD, "n4_id_map.png")
bpy.ops.render.render(write_still=True)
print("IDMAP_DONE")
with open(os.path.join(HERE, "N4_ID_COLORS.json"), "w") as f:
    import json
    json.dump(ids, f, indent=1)
