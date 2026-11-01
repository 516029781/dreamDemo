"""B1b · 水线黑边：压顶法线校正

现象：v=14% 处一条 (19,20,19) 的近黑硬边，正好在水面下缘。
排查：`T01 | retaining stone` 基色 (0.264,0.221,0.162) 是中暖石，不可能渲成 19。
     这两个对象是**扁平片**（z 只有 0.02 一个值），若法线朝下，从上方看到的是背面，
     Cycles 会按"背对光"着色，于是全黑。

做法：逐对象检查平均法线 z 分量，< 0 则翻转；然后渲一张 24spp/50% 采样确认。
"""
import bpy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
TMP = os.path.join(PRE, "_b1b_probe.png")
sc = bpy.context.scene
log = {"fixed": [], "kept": []}

TARGETS = ["T01 | far retaining coping", "T01 | far retaining wall",
           "T01 | east shore cap", "T01 | east dark sidewall"]

for name in TARGETS:
    ob = bpy.data.objects.get(name)
    if not ob or ob.type != "MESH":
        log["kept"].append({"obj": name, "reason": "missing"})
        continue
    me = ob.data
    nz = sum(p.normal.z for p in me.polygons) / max(1, len(me.polygons))
    if nz < 0:
        for p in me.polygons:
            p.flip()
        me.update()
        log["fixed"].append({"obj": name, "avg_normal_z_before": round(nz, 3)})
    else:
        log["kept"].append({"obj": name, "avg_normal_z": round(nz, 3)})


def sample(rows):
    sc.cycles.samples = 24
    sc.render.resolution_percentage = 50
    sc.render.filepath = TMP
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(TMP, check_existing=False)
    W, H = img.size
    px = list(img.pixels)
    out = {}
    for label, vs in rows.items():
        vals = []
        for vf in vs:
            y = int(H * vf)
            row = H - 1 - y
            i = (row * W + W // 2) * 4
            vals.append(round(255 * px[i]))
        out[label] = vals
    bpy.data.images.remove(img)
    return out


before = sample({"waterline_v13_15": [0.130, 0.135, 0.140, 0.145, 0.150]})

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))

log["waterline_after"] = before
with open(os.path.join(PRE, "B1B_NORMALS.json"), "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=1)

print("=== B1b ===")
print("fixed", json.dumps(log["fixed"], ensure_ascii=False))
print("waterline", json.dumps(before, ensure_ascii=False))
