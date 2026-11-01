# N3 R08/R09: vegetation and far shore. One hypothesis batch.
# Hypothesis: (a) per-cluster random rotation/scale/jitter breaks the visible
# even-spacing of grass; (b) 4 dark inner canopy masses restore the tree's
# layered dark crown; (c) irregular far shrubs along the far-bank crest break
# its hard folded outline. No card-count increase, no blur.
import bpy, json, os, math, random, time
from mathutils import Vector, Euler

t0 = time.time()
random.seed(251101)
sc = bpy.context.scene
LOG = {"grass_randomized": 0, "canopy_added": [], "far_shrub_added": 0}


def bbc(ob):
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return Vector((sum(p.x for p in pts) / 8, sum(p.y for p in pts) / 8, sum(p.z for p in pts) / 8))


# ---- 1) randomize existing grass clusters (no new cards) ----
pref = ("v16 grass clump", "P1 veg | low grass", "P1 veg | barrel grass",
        "Foreground left edge grass", "P1 left understory")
for ob in sc.objects:
    if ob.type != 'MESH' or ob.hide_render:
        continue
    if not ob.name.startswith(pref):
        continue
    ob.rotation_mode = 'XYZ'
    ob.rotation_euler.rotate(Euler((0, 0, math.radians(random.uniform(-28, 28)))))
    s = random.uniform(0.85, 1.22)
    ob.scale = (ob.scale[0] * s * random.uniform(0.92, 1.08),
                ob.scale[1] * s * random.uniform(0.92, 1.08),
                ob.scale[2] * s * random.uniform(0.88, 1.25))
    ob.location = ob.location + Vector((random.uniform(-0.14, 0.14),
                                        random.uniform(-0.14, 0.14), 0))
    LOG["grass_randomized"] += 1

# ---- 2) dark inner canopy masses for the left tree ----
leaf_mat = bpy.data.materials.get("P1 autumn leaves | texture-preserving warm shift")
dark = bpy.data.materials.new("P1 canopy inner dark")
dark.use_nodes = True
nt = dark.node_tree
bsdf = nt.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.135, 0.072, 0.038, 1.0)
bsdf.inputs["Roughness"].default_value = 0.92


def blob(name, cx, cy, cz, r, mat, seed):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=r,
                                          location=(cx, cy, cz))
    ob = bpy.context.active_object
    ob.name = name
    dis = ob.modifiers.new("disp", 'DISPLACE')
    tex = bpy.data.textures.new(name + "_tex", 'CLOUDS')
    tex.noise_scale = r * 0.75
    dis.texture = tex
    dis.strength = r * 0.42
    dis.texture_coords = 'GLOBAL'
    ob.data.materials.append(mat)
    ob.rotation_euler = Euler((random.uniform(0, 3), random.uniform(0, 3), random.uniform(0, 3)))
    return ob


tree_spots = [("P1 canopy dark mass A", -9.6, 4.9, 3.1, 1.55),
              ("P1 canopy dark mass B", -7.6, 6.1, 2.5, 1.30),
              ("P1 canopy dark mass C", -8.3, 4.5, 4.5, 1.45),
              ("P1 canopy dark mass D", -9.3, 6.5, 5.3, 1.20)]
for nm, x, y, z, r in tree_spots:
    ob = blob(nm, x, y, z, r, dark, 0)
    LOG["canopy_added"].append({"name": nm, "loc": [x, y, z], "r": r})

# ---- 3) far-bank shrubs to break the hard crest line ----
crown_mat = bpy.data.materials.get("P1 crown | dark warm")
warm = bpy.data.materials.get("P1 autumn leaves | texture-preserving warm shift")
spots = []
for i in range(9):
    x = random.uniform(-17.5, 17.0)
    y = random.uniform(19.6, 21.4)
    r = random.uniform(1.1, 2.2)
    z = 0.2 + r * 0.35
    spots.append((x, y, z, r))
# keep the middle distance view clear: drop shrubs near x in [-2, 4] low band
spots = [s for s in spots if not (-2 < s[0] < 4 and s[3] > 1.6)]
for i, (x, y, z, r) in enumerate(spots):
    ob = blob("P1 far shrub %02d" % i, x, y, z, r, crown_mat or warm, i)
    ob.scale = (1.0, random.uniform(0.55, 0.85), random.uniform(0.6, 0.95))
    LOG["far_shrub_added"] += 1

bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()
LOG["elapsed_s"] = round(time.time() - t0, 1)
with open(os.path.join(os.path.dirname(__file__), "N3_VEG_LOG.json"), "w", encoding="utf-8") as f:
    json.dump(LOG, f, ensure_ascii=False, indent=1)
print("N3_DONE grass=%d canopy=%d shrubs=%d elapsed=%.1fs" % (
    LOG["grass_randomized"], len(LOG["canopy_added"]), LOG["far_shrub_added"], LOG["elapsed_s"]))
