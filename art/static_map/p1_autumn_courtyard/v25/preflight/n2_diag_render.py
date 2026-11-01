# N1 diagnosis renders: gray no-DOF still from fixed camera, top-down zoning,
# side section through main stair. Temporary changes only, scene not saved after.
import bpy, os, math, time

t0 = time.time()
sc = bpy.context.scene
HERE = os.path.dirname(__file__)
RD = os.path.join(os.path.dirname(HERE), "renders")
os.makedirs(RD, exist_ok=True)
cam = sc.camera

# gray override
gray = bpy.data.materials.new("N2 gray override")
gray.use_nodes = True
nt = gray.node_tree
nt.nodes.clear()
em = nt.nodes.new("ShaderNodeBsdfDiffuse")
em.inputs["Color"].default_value = (0.62, 0.60, 0.57, 1)
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(em.outputs[0], out.inputs[0])
vl = bpy.context.view_layer
vl.material_override = gray

world = sc.world
wstate = world.use_nodes
wnodes = [n for n in world.node_tree.nodes] if world.use_nodes else []
wbg = world.node_tree.nodes.get("Background")
wcol = tuple(wbg.inputs[0].default_value) if wbg else None
wstr = wbg.inputs[1].default_value if wbg else None
if wbg:
    wbg.inputs[0].default_value = (0.45, 0.47, 0.50, 1)
    wbg.inputs[1].default_value = 0.9

dof_state = cam.data.dof.use_dof
cam.data.dof.use_dof = False

cfg = sc.render
res0 = (cfg.resolution_x, cfg.resolution_y, cfg.resolution_percentage)
samp0 = sc.cycles.samples
cfg.resolution_x, cfg.resolution_y, cfg.resolution_percentage = 960, 539, 100
sc.cycles.samples = 32
sc.cycles.use_denoising = True

def snap(name):
    cfg.filepath = os.path.join(RD, name)
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print("RENDER", name, "%.1fs" % (time.time() - t))

# 1) fixed camera gray
snap("n2_gray.png")

# 2) top-down ortho
top_data = bpy.data.cameras.new("N2 top")
top_data.type = 'ORTHO'
top_data.ortho_scale = 34.0
top_ob = bpy.data.objects.new("N2 top", top_data)
sc.collection.objects.link(top_ob)
top_ob.location = (0, 4, 40)
top_ob.rotation_euler = (0, 0, 0)
cam_state = sc.camera
sc.camera = top_ob
snap("n2_top.png")

# 3) side section through main stair (look from -x toward +x, ortho)
side_data = bpy.data.cameras.new("N2 side")
side_data.type = 'ORTHO'
side_data.ortho_scale = 16.0
side_ob = bpy.data.objects.new("N2 side", side_data)
sc.collection.objects.link(side_ob)
side_ob.location = (-30, -2.6, 1.2)   # cutting plane near stair center x=-3.15
side_ob.rotation_euler = (math.radians(90), 0, math.radians(-90))
sc.camera = side_ob
snap("n2_side.png")

# restore
sc.camera = cam_state
for ob in (top_ob, side_ob):
    bpy.data.objects.remove(ob, do_unlink=True)
bpy.data.cameras.remove(top_data)
bpy.data.cameras.remove(side_data)
vl.material_override = None
cam.data.dof.use_dof = dof_state
if wbg and wcol:
    wbg.inputs[0].default_value = wcol
    wbg.inputs[1].default_value = wstr
if not wstate:
    world.use_nodes = False
cfg.resolution_x, cfg.resolution_y, cfg.resolution_percentage = res0
sc.cycles.samples = samp0
bpy.data.materials.remove(gray)
print("N2_DIAG_DONE elapsed=%.1fs" % (time.time() - t0))
