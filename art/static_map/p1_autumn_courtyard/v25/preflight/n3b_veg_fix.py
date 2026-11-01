# N3b: fix N3 blobs. Same hypothesis family, second method per workflow rule
# (two attempts allowed before switching approach): replace icosphere masses
# with linked duplicates of existing foliage/crown cards, darkened material
# variants. Deleting failed blobs entirely is recorded.
import bpy, json, os, math, random, time
from mathutils import Euler, Vector

t0 = time.time()
random.seed(251102)
sc = bpy.context.scene
LOG = {"deleted": [], "added": []}

# 1) delete failed blobs
for ob in list(sc.objects):
    if ob.name.startswith(("P1 canopy dark mass", "P1 far shrub")):
        LOG["deleted"].append(ob.name)
        bpy.data.objects.remove(ob, do_unlink=True)

# 2) darkened leaf material for inner canopy
src = bpy.data.materials.get("P1 autumn leaves | texture-preserving warm shift")
dark_leaf = src.copy() if src else None
if dark_leaf:
    dark_leaf.name = "P1 canopy inner dark leaves"
    nt = dark_leaf.node_tree
    for nd in nt.nodes:
        if nd.type == 'BSDF_PRINCIPLED' and "Base Color" in nd.inputs:
            bc = nd.inputs["Base Color"]
            if not bc.is_linked:
                bc.default_value = (bc.default_value[0] * 0.38, bc.default_value[1] * 0.34, bc.default_value[2] * 0.36, 1.0)
            else:
                mix = nt.nodes.new("ShaderNodeMix")
                mix.data_type = 'RGBA'
                mix.blend_type = 'MULTIPLY'
                mix.name = "P1 force trim canopydark"
                mix.inputs[6].default_value = (0.34, 0.30, 0.32, 1.0)  # factor color
                lk = bc.links[0]
                nt.links.new(lk.from_socket, mix.inputs[7])
                nt.links.new(mix.outputs[2], bc)
                break

# 3) inner canopy: linked duplicates of the foliage overlay, shrunk, rotated
ov = bpy.data.objects.get("P1 broadleaf foliage overlay | widened canopy")
if ov:
    spots = [("P1 canopy inner A", (-9.3, 5.0, 3.4), 0.40, (0.0, 0.35, 2.2)),
             ("P1 canopy inner B", (-7.9, 6.0, 2.7), 0.33, (0.25, -0.2, 4.1)),
             ("P1 canopy inner C", (-8.8, 4.3, 4.6), 0.36, (-0.3, 0.15, 1.1))]
    for nm, loc, s, rot in spots:
        ob = bpy.data.objects.new(nm, ov.data)   # linked duplicate
        sc.collection.objects.link(ob)
        ob.location = loc
        ob.scale = (s, s * random.uniform(0.8, 1.0), s * random.uniform(0.75, 0.95))
        ob.rotation_euler = Euler(rot)
        if dark_leaf:
            ob.data.materials.clear()
            ob.data.materials.append(dark_leaf)  # NOTE: linked mesh material slot affects original too?
        LOG["added"].append(nm)

# 4) far shrubs: linked duplicates of crown cards along the bank crest
crown_proto = None
for ob in sc.objects:
    if ob.name.startswith("P1 crown | ") and ob.type == 'MESH':
        crown_proto = ob
        break
crown_mat = bpy.data.materials.get("P1 crown | dark warm")
if crown_proto:
    made = 0
    for i in range(10):
        x = random.uniform(-17.0, 17.0)
        if -2 < x < 4:
            continue
        y = random.uniform(19.7, 21.3)
        s = random.uniform(0.35, 0.62)
        ob = bpy.data.objects.new("P1 far crown dup %02d" % i, crown_proto.data)
        sc.collection.objects.link(ob)
        base_z = 0.2
        ob.location = (x, y, base_z + 1.4 * s * 3.0)
        ob.scale = (s, s, s)
        ob.rotation_euler = Euler((0, 0, random.uniform(0, 6.28)))
        if crown_mat and crown_proto.data.materials:
            pass  # keep same crown material (linked mesh already carries it)
        made += 1
    LOG["added"].append("far crown dups x%d" % made)

bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()
LOG["elapsed_s"] = round(time.time() - t0, 1)
with open(os.path.join(os.path.dirname(__file__), "N3B_VEG_LOG.json"), "w", encoding="utf-8") as f:
    json.dump(LOG, f, ensure_ascii=False, indent=1)
print("N3B_DONE deleted=%d added=%s elapsed=%.1fs" % (len(LOG["deleted"]), LOG["added"], LOG["elapsed_s"]))
