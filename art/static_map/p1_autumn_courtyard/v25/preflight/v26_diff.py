"""V26 Step0b: full object diff current vs pre_B/pre_D + tree transform capture.
Usage: blender scene.blend -b --python v26_diff.py -- preflight/
"""
import bpy, json, sys, os

out_dir = sys.argv[sys.argv.index("--") + 1]
V25 = os.path.dirname(out_dir.rstrip("/\\"))
PB = os.path.join(V25, "_backup", "scene_pre_B.blend")
PD = os.path.join(V25, "_backup", "scene_pre_D.blend")

cur = {}
for ob in bpy.data.objects:
    cur[ob.name] = {
        "loc": [round(v, 4) for v in ob.location],
        "scale": [round(v, 4) for v in ob.scale],
        "parent": ob.parent.name if ob.parent else None,
    }

def lib_names(path):
    with bpy.data.libraries.load(path, link=False) as (df, dt):
        return list(df.objects)

pb = set(lib_names(PB))
pd = set(lib_names(PD))
cn = set(cur)

# capture transforms of tree-related objects in pre_B by appending them
TREE_KEYS = ("lod", "trunk", "broadleaf", "r30", "canopy")
def tree_rec(names):
    return [n for n in names if any(k in n.lower() for k in TREE_KEYS)]

preB_tree_names = tree_rec(pb - cn) + [n for n in tree_rec(pb & cn)]
appended = []
with bpy.data.libraries.load(PB, link=False) as (df, dt):
    dt.objects = [n for n in preB_tree_names if n in df.objects]
recs = {}
for ob in bpy.data.objects:
    if ob.name in preB_tree_names and ob.name not in cur:
        recs[ob.name] = {"loc": [round(v,4) for v in ob.location],
                         "scale": [round(v,4) for v in ob.scale],
                         "rot_mode": ob.rotation_mode,
                         "parent": ob.parent.name if ob.parent else None}
        appended.append(ob)
for ob in appended:
    bpy.data.objects.remove(ob, do_unlink=True)

out = {
    "current_not_in_preB": sorted(cn - pb),
    "preB_not_in_current": sorted(pb - cn),
    "current_not_in_preD": sorted(cn - pd),
    "preD_not_in_current": sorted(pd - cn),
    "preB_tree_transforms": recs,
}
with open(os.path.join(out_dir, "V26_DIFF.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("DIFF_DONE", len(cn-pb), len(pb-cn), len(cn-pd), len(pd-cn), "tree_recs", len(recs))
