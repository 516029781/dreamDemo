"""V26 fix: link appended objects into scene collection + restore 6 missing barrels.
Usage: blender scene.blend -b --python v26_link_fix.py -- <V25_DIR>
"""
import bpy, json, sys, os

V25 = sys.argv[sys.argv.index("--") + 1]
PB = os.path.join(V25, "_backup", "scene_pre_B.blend")
PD = os.path.join(V25, "_backup", "scene_pre_D.blend")
LOG = os.path.join(V25, "preflight", "V26_LINK_FIX_LOG.json")

CARDS = ["P1 canopy inner A", "P1 canopy inner B", "P1 canopy inner C", "P1 canopy top layer"]
MISSING = ["P1 edge | barrel -4.2", "P1 edge | barrel 2.8",
           "P1 edge | barrel rim -4", "P1 edge | barrel rim 2",
           "P1 veg | barrel grass -4.2", "P1 veg | barrel grass 2.8"]

log = {"linked": [], "reappended": [], "errors": []}
scene = bpy.context.scene

def link_existing(names, tag):
    for n in names:
        ob = bpy.data.objects.get(n)
        if ob is None:
            continue
        if ob.name not in scene.collection.objects:
            try:
                scene.collection.objects.link(ob)
                log["linked"].append(n)
            except Exception as e:
                log["errors"].append(f"link {n}: {e}")
        ob.hide_render = False
        ob.hide_viewport = False

def append_and_link(path, names):
    with bpy.data.libraries.load(path, link=False) as (df, dt):
        dt.objects = [n for n in names if n in df.objects]
    for n in names:
        ob = bpy.data.objects.get(n)
        if ob is None:
            log["errors"].append("append failed: " + n)
            continue
        if ob.name not in scene.collection.objects:
            scene.collection.objects.link(ob)
        ob.hide_render = False
        ob.hide_viewport = False
        log["reappended"].append(n)

# cards: link if present, else re-append from pre_B
present = [n for n in CARDS if n in bpy.data.objects]
absent = [n for n in CARDS if n not in bpy.data.objects]
link_existing(present, "card")
if absent:
    append_and_link(PB, absent)

# missing barrels: re-append from pre_D
append_and_link(PD, [n for n in MISSING if n not in bpy.data.objects])

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(V25, "scene.blend"))
with open(LOG, "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=1)
print("LINK_FIX_DONE linked=%d reappended=%d errors=%d" % (
    len(log["linked"]), len(log["reappended"]), len(log["errors"])))
