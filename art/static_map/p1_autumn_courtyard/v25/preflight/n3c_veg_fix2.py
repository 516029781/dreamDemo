# N3c (third method): undo shared-mesh material pollution, restore tree,
# dark inner canopy via single-user mesh copies with fixed multiply wiring,
# remove misplaced far crown dups. Far-shore contrast softening moves to N4.
import bpy, json, os, math, random, time
from mathutils import Euler

t0 = time.time()
random.seed(251103)
sc = bpy.context.scene
LOG = {"deleted": [], "restored": [], "added": []}

# 1) restore the foliage overlay mesh material (it was polluted by n3b)
ov = bpy.data.objects.get("P1 broadleaf foliage overlay | widened canopy")
leaves = bpy.data.materials.get("P1 autumn leaves | texture-preserving warm shift")
if ov and leaves:
    ov.data.materials.clear()
    ov.data.materials.append(leaves)
    LOG["restored"].append("overlay mesh materials -> autumn leaves")

# 2) remove n3b inner cards and far crown dups (polluted / misplaced)
for ob in list(sc.objects):
    if ob.name.startswith(("P1 canopy inner", "P1 far crown dup")):
        LOG["deleted"].append(ob.name)
        bpy.data.objects.remove(ob, do_unlink=True)

# 3) fixed dark-leaf material: multiply toward deep amber via correct B input
src = bpy.data.materials.get("P1 autumn leaves | texture-preserving warm shift")
dark_leaf = None
if src:
    dark_leaf = src.copy()
    dark_leaf.name = "P1 canopy inner dark v2"
    nt = dark_leaf.node_tree
    done = False
    for nd in nt.nodes:
        if nd.type == 'BSDF_PRINCIPLED' and "Base Color" in nd.inputs:
            bc = nd.inputs["Base Color"]
            if bc.is_linked:
                lk = bc.links[0]
                mix = nt.nodes.new("ShaderNodeMix")
                mix.data_type = 'RGBA'
                mix.blend_type = 'MULTIPLY'
                mix.name = "P1 force trim canopydark2"
                mix.inputs[0].default_value = 1.0          # factor
                nt.links.new(lk.from_socket, mix.inputs[7])  # A = texture
                mix.inputs[6].default_value = (0.30, 0.22, 0.20, 1.0)  # B = deep amber multiplier
                nt.links.new(mix.outputs[2], bc)
                done = True
            else:
                bc.default_value = (0.05, 0.028, 0.015, 1.0)
                done = True
            break
    LOG["restored"].append("dark_leaf multiply wired=%s" % done)

# 4) inner canopy cards: single-user mesh copies, unlinked from tree mesh
if ov and dark_leaf:
    spots = [("P1 canopy inner A", (-9.3, 5.0, 3.4), 0.42, (0.0, 0.35, 2.2)),
             ("P1 canopy inner B", (-7.9, 6.0, 2.7), 0.34, (0.25, -0.2, 4.1)),
             ("P1 canopy inner C", (-8.8, 4.3, 4.6), 0.38, (-0.3, 0.15, 1.1))]
    for nm, loc, s, rot in spots:
        me = ov.data.copy()   # single user copy
        ob = bpy.data.objects.new(nm, me)
        sc.collection.objects.link(ob)
        me.materials.clear()
        me.materials.append(dark_leaf)
        ob.location = loc
        ob.scale = (s, s * random.uniform(0.8, 1.0), s * random.uniform(0.75, 0.95))
        ob.rotation_euler = Euler(rot)
        LOG["added"].append(nm)

bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()
LOG["elapsed_s"] = round(time.time() - t0, 1)
with open(os.path.join(os.path.dirname(__file__), "N3C_VEG_LOG.json"), "w", encoding="utf-8") as f:
    json.dump(LOG, f, ensure_ascii=False, indent=1)
print("N3C_DONE deleted=%d restored=%s added=%s elapsed=%.1fs" % (
    len(LOG["deleted"]), LOG["restored"], LOG["added"], LOG["elapsed_s"]))
