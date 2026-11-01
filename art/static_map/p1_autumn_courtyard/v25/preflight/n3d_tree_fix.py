# N3d: root-cause fix for the left tree. Camera top edge at tree distance is
# z~3.4 m, but the tree is ~10 m tall: its crown renders off-frame, leaving a
# bare trunk. Reference shows a short-trunk, wide-crown tree. Rescale the tree
# to 0.5, seat it on the terrace, reposition dark inner cards inside the crown.
import bpy, json, os, time

t0 = time.time()
sc = bpy.context.scene
LOG = {}

S = 0.5
for nm in ["P1 broadleaf | Poly Haven Tree Small 02 LOD1",
           "P1 broadleaf foliage overlay | widened canopy"]:
    ob = bpy.data.objects.get(nm)
    if ob:
        ob.scale = (ob.scale[0] / 1.46 * S, ob.scale[1] / 1.46 * S, ob.scale[2] / 1.46 * S)
        ob.location.z = 0.06   # seat on terrace surface (mesh origin ~0.2 base offset)
        LOG[nm] = {"scale": S, "z": 0.06}

# reposition dark inner cards into the now-visible crown (z 1.2-3.4 band)
spots = {"P1 canopy inner A": (-9.2, 5.9, 2.2, 0.30),
         "P1 canopy inner B": (-8.1, 6.6, 1.7, 0.26),
         "P1 canopy inner C": (-8.7, 5.2, 2.7, 0.28)}
for nm, (x, y, z, s) in spots.items():
    ob = bpy.data.objects.get(nm)
    if ob:
        ob.location = (x, y, z)
        ob.scale = (s, s * 0.9, s * 0.85)
        LOG[nm] = {"loc": [x, y, z], "scale": s}

bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()
LOG["elapsed_s"] = round(time.time() - t0, 1)
with open(os.path.join(os.path.dirname(__file__), "N3D_TREE_LOG.json"), "w", encoding="utf-8") as f:
    json.dump(LOG, f, ensure_ascii=False, indent=1)
print("N3D_DONE", {k: v for k, v in LOG.items() if k != "elapsed_s"}, "elapsed=%.1fs" % LOG["elapsed_s"])
