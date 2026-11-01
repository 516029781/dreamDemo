"""V26 Step1+2 (rev2): vegetation rollback.
- Tree: delete R2 clumps, append 4 old leaf cards from pre_B, restore tree transform(s)
- Grass: restore transforms/meshes of all grass-family objects from pre_D state
- Append back grass-family objects present in pre_D but missing in current
- Mesh compare uses base names (strip .NNN) to avoid duplicate-datablock churn
- Never touches: v15 planted tree-bed soil surface (orange culprit), shrub B16, fallen leaves
Usage: blender scene.blend -b --python v26_rework.py -- <V25_DIR>
"""
import bpy, json, sys, os, re

V25 = sys.argv[sys.argv.index("--") + 1]
PB = os.path.join(V25, "_backup", "scene_pre_B.blend")
PD = os.path.join(V25, "_backup", "scene_pre_D.blend")
LOG = os.path.join(V25, "preflight", "V26_REWORK_LOG.json")

CARDS = ["P1 canopy inner A", "P1 canopy inner B", "P1 canopy inner C", "P1 canopy top layer"]
TREE_KEYS = ("lod", "trunk", "broadleaf", "r30", "canopy gobo", "canopy inner", "canopy top")
GRASS_KEYS = ("grass", "tuft", "clump", "mulch", "barrel")
EXCLUDE = ("soil surface", "shrub b16", "fallen leaf", "densify tuft", "canopy clump", "canopy inner", "canopy top")
log = {"deleted": [], "appended_cards": [], "appended_missing": [], "tree_overrides": {}, "grass_overrides": {}, "errors": []}

cur = {ob.name: ob for ob in bpy.data.objects}

def base(n):
    return re.sub(r"\.\d{3}$", "", n)

def lib_names(path):
    with bpy.data.libraries.load(path, link=False) as (df, dt):
        return list(df.objects)

pb_names = set(lib_names(PB))
pd_names = set(lib_names(PD))

def snap(ob):
    return {
        "loc": [round(v, 4) for v in ob.location],
        "scale": [round(v, 4) for v in ob.scale],
        "rot": [round(v, 4) for v in (ob.rotation_euler if ob.rotation_mode == "XYZ" else ob.rotation_quaternion)],
        "mode": ob.rotation_mode,
        "mesh": ob.data.name if ob.type == "MESH" else None,
        "parent": ob.parent.name if ob.parent else None,
    }

def mesh_differs(c, s):
    if not s["mesh"] or c["mesh"] is None:
        return False
    return base(c["mesh"]) != base(s["mesh"])

def apply(dst, src_snap, src_lib):
    dst.location = src_snap["loc"]
    dst.scale = src_snap["scale"]
    if src_snap["mode"] == "XYZ":
        dst.rotation_mode = "XYZ"
        dst.rotation_euler = src_snap["rot"]
    else:
        dst.rotation_mode = src_snap["mode"]
        dst.rotation_quaternion = src_snap["rot"]
    if dst.type == "MESH" and mesh_differs(snap(dst), src_snap):
        want = base(src_snap["mesh"])
        target = bpy.data.meshes.get(want)
        if target is None:
            # append the mesh explicitly from source library by its original name
            with bpy.data.libraries.load(src_lib, link=False) as (df, dt):
                if want in df.meshes:
                    dt.meshes = [want]
            target = bpy.data.meshes.get(want)
        if target:
            dst.data = target
            return "mesh"
    if src_snap["parent"] and src_snap["parent"] in bpy.data.objects and (dst.parent and dst.parent.name) != src_snap["parent"]:
        dst.parent = bpy.data.objects[src_snap["parent"]]
        return "parent"
    return "xf"

def restore_phase(names, src_lib, tag):
    """Temp-append objects, snapshot their transforms, remove temps, apply diffs."""
    if not names:
        return
    orig_ids = set(id(o) for o in bpy.data.objects)
    with bpy.data.libraries.load(src_lib, link=False) as (df, dt):
        dt.objects = [n for n in names if n in df.objects]
    fresh = [o for o in bpy.data.objects if id(o) not in orig_ids]
    snaps = {}
    for o in fresh:
        key = o.name if o.name in names else o.name.rsplit(".", 1)[0]
        snaps[key] = snap(o)
    for o in fresh:
        bpy.data.objects.remove(o, do_unlink=True)
    for name, s in snaps.items():
        ob = bpy.data.objects.get(name)
        if not ob:
            log["errors"].append(tag + " missing in current: " + name)
            continue
        c = snap(ob)
        diff = (c["loc"] != s["loc"] or c["scale"] != s["scale"] or c["rot"] != s["rot"]
                or mesh_differs(c, s))
        if diff:
            try:
                what = apply(ob, s, src_lib)
                log[tag + "_overrides"][name] = {"changed": what, "from": c, "to": s}
            except Exception as e:
                log["errors"].append(f"{name}: {e}")

# ---------- Phase 1: tree ----------
for name in list(cur):
    if name.startswith("P1 canopy clump") or name.startswith("P1 densify tuft"):
        log["deleted"].append(name)
        bpy.data.objects.remove(cur[name], do_unlink=True)

with bpy.data.libraries.load(PB, link=False) as (df, dt):
    dt.objects = [n for n in CARDS if n in df.objects]
for name in CARDS:
    if name in bpy.data.objects and name not in cur:
        log["appended_cards"].append(name)
    elif name in cur:
        log["errors"].append("card collided: " + name)
cur = {ob.name: ob for ob in bpy.data.objects}

tree_names = [n for n in cur
              if any(k in n.lower() for k in TREE_KEYS)
              and n in pb_names
              and n not in CARDS]
restore_phase(tree_names, PB, "tree")

# ---------- Phase 2: grass ----------
cur = {ob.name: ob for ob in bpy.data.objects}
def is_grass(n):
    ln = n.lower()
    return any(k in ln for k in GRASS_KEYS) and not any(k in ln for k in EXCLUDE)

g_names = [n for n in cur if is_grass(n) and n in pd_names]
restore_phase(g_names, PD, "grass")

# Phase 2b: append back grass-family objects present in pre_D but missing in current
missing = [n for n in pd_names if is_grass(n) and n not in cur]
with bpy.data.libraries.load(PD, link=False) as (df, dt):
    dt.objects = [n for n in missing if n in df.objects]
log["appended_missing"] = [n for n in missing if n in bpy.data.objects]

# ---------- save ----------
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(V25, "scene.blend"))
try:
    bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(V25, "scene.blend"))
except Exception as e:
    log["errors"].append("purge: %s" % e)
with open(LOG, "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=1)
print("REWORK_DONE deleted=%d cards=%d tree=%d grass=%d missing_back=%d errors=%d" % (
    len(log["deleted"]), len(log["appended_cards"]),
    len(log["tree_overrides"]), len(log["grass_overrides"]),
    len(log["appended_missing"]), len(log["errors"])))
