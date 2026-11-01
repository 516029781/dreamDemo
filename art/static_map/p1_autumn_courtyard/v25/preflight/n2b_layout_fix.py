# N2b: layout fix v3. Pump platform (Service platform group) stays - it is a
# grounded, complete pump station. Rework positions so that:
#  - stair exit y[-0.9,1.23] keeps full 2.64 m width, then west lane x[-4.47,-2.30]
#    (2.17 m) leads to open north-west terrace; east lane x>3.09 leads to apron
#  - cabinet/pipes/hose form maintenance cluster east of pump, kerbs become a
#    planting band along the south edge, crate+barrel group clears corridor
import bpy, json, os, time
from mathutils import Vector

t0 = time.time()
sc = bpy.context.scene
LOG = {"deleted": [], "moved": [], "rebuilt_base": False}


def bbc(ob):
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return Vector((sum(p.x for p in pts) / 8, sum(p.y for p in pts) / 8, sum(p.z for p in pts) / 8))


# 1) last floating bulb
ob = bpy.data.objects.get("v15 short warm bulb 01")
if ob:
    LOG["deleted"].append(ob.name)
    bpy.data.objects.remove(ob, do_unlink=True)

# 2) crate+barrel group further west (group now spans x[-6.41,-4.29]; need <-4.55)
d = Vector((-0.50, 0, 0))
for nm in ["Foreground wooden crate", "Foreground wooden crate.001", "Foreground wooden crate.002",
           "Crate lid board", "Foreground barrel", "Barrel bottom hoop", "Barrel top hoop", "Barrel lid"]:
    ob = bpy.data.objects.get(nm)
    if ob:
        c0 = bbc(ob)
        ob.location = ob.location + d
        bpy.context.view_layer.update()
        LOG["moved"].append({"name": nm, "delta": [round(v, 2) for v in (bbc(ob) - c0)]})

# 3) cabinet: from current (inside pump platform!) to SE of pump
d = Vector((0.84, -1.07, 0))
for nm in ["P1 yard | cabinet", "P1 yard | cabinet | band 0", "P1 yard | cabinet | band 1"]:
    ob = bpy.data.objects.get(nm)
    if ob:
        c0 = bbc(ob)
        ob.location = ob.location + d
        bpy.context.view_layer.update()
        LOG["moved"].append({"name": nm, "delta": [round(v, 2) for v in (bbc(ob) - c0)]})

# 4) kerb B and A: south planting band, same delta keeps pairing
d = Vector((0.70, -1.04, 0))
for nm in ["P1 yard | kerb B", "P1 yard | kerb B | soil", "P1 yard | kerb B | dry grass bed",
           "P1 yard | kerb A", "P1 yard | kerb A | soil", "P1 yard | kerb A | dry grass bed"]:
    ob = bpy.data.objects.get(nm)
    if ob:
        c0 = bbc(ob)
        ob.location = ob.location + d
        bpy.context.view_layer.update()
        LOG["moved"].append({"name": nm, "delta": [round(v, 2) for v in (bbc(ob) - c0)]})

# 5) pipes east of pump with rebuilt base
d = Vector((0.40, -0.62, 0))
for nm in list(bpy.data.objects.keys()):
    if nm.startswith("CC0 industrial pipe"):
        ob = bpy.data.objects[nm]
        c0 = bbc(ob)
        ob.location = ob.location + d
        bpy.context.view_layer.update()
        LOG["moved"].append({"name": nm, "delta": [round(v, 2) for v in (bbc(ob) - c0)]})
old = bpy.data.objects.get("P1 pipe cluster base")
if old:
    bpy.data.objects.remove(old, do_unlink=True)
stone = bpy.data.materials.get("P1 edge | step stone")
me = bpy.data.meshes.new("P1 pipe cluster base")
v = [(0.55, 1.30, 0.04), (1.60, 1.30, 0.04), (1.60, 2.00, 0.04), (0.55, 2.00, 0.04),
     (0.55, 1.30, 0.75), (1.60, 1.30, 0.75), (1.60, 2.00, 0.75), (0.55, 2.00, 0.75)]
f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
me.from_pydata(v, [], f)
me.update()
b = bpy.data.objects.new("P1 pipe cluster base", me)
sc.collection.objects.link(b)
if stone:
    b.data.materials.append(stone)
LOG["rebuilt_base"] = True

# 6) hose beside cabinet
d = Vector((1.00, -1.10, 0))
for nm in ["Coiled hose", "Coiled hose.001", "Coiled hose.002"]:
    ob = bpy.data.objects.get(nm)
    if ob:
        c0 = bbc(ob)
        ob.location = ob.location + d
        bpy.context.view_layer.update()
        LOG["moved"].append({"name": nm, "delta": [round(v, 2) for v in (bbc(ob) - c0)]})

bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()
LOG["elapsed_s"] = round(time.time() - t0, 1)
with open(os.path.join(os.path.dirname(__file__), "N2B_FUNC_LOG.json"), "w", encoding="utf-8") as f:
    json.dump(LOG, f, ensure_ascii=False, indent=1)
print("N2B_DONE deleted=%d moved=%d elapsed=%.1fs" % (len(LOG["deleted"]), len(LOG["moved"]), LOG["elapsed_s"]))
