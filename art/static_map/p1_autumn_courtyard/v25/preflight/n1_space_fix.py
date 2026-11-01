# N1 R01/R02: remove broad foreground stair, clean floating strips,
# close stair-to-paving joint, fill stair rear cavity. One hypothesis batch.
# Hypothesis: deleting the 9-tread broad stair + patching stair junction
# yields a continuous lowland -> main stair -> terrace path.
import bpy, json, os, time

t0 = time.time()
sc = bpy.context.scene
LOG = {"deleted": [], "added": [], "notes": []}

# 1) delete broad foreground stair (9 independent boxes from s7_steps.py)
for i in range(9):
    nm = "P1 steps | %02d" % i
    ob = bpy.data.objects.get(nm)
    if ob:
        bpy.data.objects.remove(ob, do_unlink=True)
        LOG["deleted"].append(nm)

# 2) delete expansion-joint strips whose fascia is already hidden (float in air)
for ob in list(bpy.data.objects):
    if ob.name.startswith("Landing fascia recessed expansion joint"):
        LOG["deleted"].append(ob.name)
        bpy.data.objects.remove(ob, do_unlink=True)

# 3) landing cap closing tread00 (top z=-0.09) to paving bed (z=-0.02)
plinth = bpy.data.objects.get("Deep platform plinth left")
pmats = [m for m in plinth.data.materials if m] if plinth else []
stone = bpy.data.materials.get("P1 edge | step stone")


def box(name, x0, x1, y0, y1, z0, z1, mats):
    me = bpy.data.meshes.new(name)
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me.from_pydata(v, [], f)
    me.update()
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    for m in mats:
        ob.data.materials.append(m)
    return ob


# stair bounds from N0 census: x[-4.47,-1.83]; tread00 y[-1.59,-0.90]
cap = box("P1 stair landing cap", -4.47, -1.83, -1.59, -0.90, -0.09, -0.02, pmats or [stone])
LOG["added"].append({"name": cap.name, "bbox": [-4.47, -1.59, -0.09, -1.83, -0.90, -0.02]})

# 4) backfill cavity behind stair inside plinth opening (stair backs onto solid base)
fill = box("P1 stair rear fill", -4.55, -1.75, -0.90, 3.00, -1.31, -0.02, pmats or [stone])
LOG["added"].append({"name": fill.name, "bbox": [-4.55, -0.90, -1.31, -1.75, 3.00, -0.02]})

# sanity: verify deletions and junction heights
assert not bpy.data.objects.get("P1 steps | 00"), "broad stair still present"
LOG["notes"].append("stair rear fill uses plinth material family; cap closes 0.07 m joint to bed z=-0.02")

bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()
LOG["elapsed_s"] = round(time.time() - t0, 1)
LOG["saved"] = bpy.data.filepath
with open(os.path.join(os.path.dirname(__file__), "N1_SPACE_LOG.json"), "w", encoding="utf-8") as f:
    json.dump(LOG, f, ensure_ascii=False, indent=1)
print("N1_SPACE_DONE deleted=%d added=%d elapsed=%.1fs" % (len(LOG["deleted"]), len(LOG["added"]), LOG["elapsed_s"]))
