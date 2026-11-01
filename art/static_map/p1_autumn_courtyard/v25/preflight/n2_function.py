# N2 R03-R07: functional grouping. One hypothesis batch.
# Hypothesis: removing objects with no attach point / no use, moving logistics
# (crates+barrel) beside the tug, moving cabinet/dumpster/kerbA out of the
# stair-exit corridor, and giving the pipe cluster a base yields readable
# maintenance / logistics / planting zones with a clear path from stair exit.
import bpy, json, os, time
from mathutils import Vector

t0 = time.time()
sc = bpy.context.scene
LOG = {"deleted": [], "moved": [], "added": [], "corridor_check": {}}


def bb_center(ob):
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return Vector((sum(p.x for p in pts) / 8, sum(p.y for p in pts) / 8, sum(p.z for p in pts) / 8))


# ---- 1) delete floating / useless ----
DELETE = []
DELETE += ["v15 grounded gantry ladder stile", "v15 grounded gantry ladder stile.001",
           "v15 ladder top bracket", "v15 ladder top bracket.001",
           "v15 ladder foot bracket", "v15 ladder foot bracket.001"]
DELETE += ["v15 short warm bulb 02", "v15 short warm bulb 03", "v15 short warm bulb 04",
           "v15 short warm bulb 05", "v15 short warm bulb 06"]
DELETE += ["Fence support", "Fence support.001", "Fence support.002", "Pump panel bolt"]
DELETE += ["v15 centered tree planter | east wall", "v15 centered tree planter | north wall",
           "v15 centered tree planter | south wall", "v15 centered tree planter | west wall",
           "v15 centered tree planter | soil body"]
DELETE += ["P1 foreground table | dark thin tabletop", "P1 foreground table | front apron",
           "P1 foreground table | rear apron", "P1 foreground table | left apron",
           "P1 foreground table | right apron"]
DELETE += ["v15 safety cone 1 rubber foot", "v15 safety cone 1 body"]
for nm in DELETE:
    ob = bpy.data.objects.get(nm)
    if ob:
        LOG["deleted"].append(nm)
        bpy.data.objects.remove(ob, do_unlink=True)

# ---- 2) move logistics group (3 crates + lid + barrel parts) beside tug ----
# group bbox center (4.55,-0.26) -> target (-5.60, 2.70); tug fork tip x=-5.04, fork y 1.29..1.65
MOVE = {
    "Foreground wooden crate": (-9.90, 2.99, 0), "Foreground wooden crate.001": (-9.90, 2.99, 0),
    "Foreground wooden crate.002": (-9.90, 2.99, 0), "Crate lid board": (-9.90, 2.99, 0),
    "Foreground barrel": (-9.90, 2.99, 0), "Barrel bottom hoop": (-9.90, 2.99, 0),
    "Barrel top hoop": (-9.90, 2.99, 0), "Barrel lid": (-9.90, 2.99, 0),
    # dumpster west, out of exit corridor
    "P1 yard | dumpster": (-1.13, -1.56, 0), "P1 yard | dumpster | band 0": (-1.13, -1.56, 0),
    "P1 yard | dumpster | band 1": (-1.13, -1.56, 0),
    # cabinet east into maintenance group
    "P1 yard | cabinet": (3.02, 0.57, 0), "P1 yard | cabinet | band 0": (3.02, 0.57, 0),
    "P1 yard | cabinet | band 1": (3.02, 0.57, 0),
    # coiled hose beside cabinet (outside corridor x>-1.75)
    "Coiled hose": (-1.80, 1.40, 0), "Coiled hose.001": (-1.80, 1.40, 0), "Coiled hose.002": (-1.80, 1.40, 0),
    # kerb A east to join kerb B, clear corridor
    "P1 yard | kerb A": (4.60, 0, 0), "P1 yard | kerb A | soil": (4.60, 0, 0),
    "P1 yard | kerb A | dry grass bed": (4.60, 0, 0),
}
for nm, d in MOVE.items():
    ob = bpy.data.objects.get(nm)
    if ob:
        c0 = bb_center(ob)
        ob.location = ob.location + Vector((d[0], d[1], d[2]))
        bpy.context.view_layer.update()
        c1 = bb_center(ob)
        LOG["moved"].append({"name": nm, "delta": [round(v, 2) for v in (c1 - c0)]})

# ---- 3) pipe cluster base (ground attachment) ----
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
    for m in (mats or [stone]):
        ob.data.materials.append(m)
    return ob


base = box("P1 pipe cluster base", 0.10, 1.00, 2.15, 2.55, 0.04, 0.75, None)
LOG["added"].append(base.name)

# ---- 4) corridor clearance check: x[-4.55,-1.75] y[-0.9,2.5] ----
intruders = []
for ob in sc.objects:
    if ob.type != 'MESH' or ob.hide_render:
        continue
    b = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    xs = [p.x for p in b]; ys = [p.y for p in b]; zs = [p.z for p in b]
    if max(xs) > -4.55 and min(xs) < -1.75 and max(ys) > -0.9 and min(ys) < 2.5 and max(zs) > 0.10:
        n = ob.name
        if any(k in n for k in ("limestone", "bed", "stair", "Continuous", "tier", "Ground", "crack")):
            continue
        intruders.append(n)
LOG["corridor_check"] = {"zone": "x[-4.55,-1.75] y[-0.9,2.5] z>0.10", "intruders": intruders}

bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()
LOG["elapsed_s"] = round(time.time() - t0, 1)
with open(os.path.join(os.path.dirname(__file__), "N2_FUNC_LOG.json"), "w", encoding="utf-8") as f:
    json.dump(LOG, f, ensure_ascii=False, indent=1)
print("N2_DONE deleted=%d moved=%d added=%d corridor_intruders=%s elapsed=%.1fs" % (
    len(LOG["deleted"]), len(LOG["moved"]), len(LOG["added"]), intruders, LOG["elapsed_s"]))
