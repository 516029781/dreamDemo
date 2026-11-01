"""B1 · 水面明度迭代

问题（实测）：水面贴图均值 (81,83,89)，渲染出来是 (58,60,63)，比岸线 (131,116,96)
暗一半，读起来是黑缝而不是水。参考里水面是画面唯一的冷光区，比岸亮。

做法：断开贴图，Base Color 改常量，渲染-采样-调整，直到落到目标区间。
在这个画面高度上（4pp）贴图细节本来就看不见，只贡献了错误的明度。

目标：水面均值 140–170，且比岸线亮 >= 8。
"""
import bpy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
TMP = os.path.join(PRE, "_b1_probe.png")
MAT = "M01W water"

TARGET_LO, TARGET_HI = 140.0, 170.0
MIN_DELTA_VS_SHORE = 8.0
MAX_ITER = 3

sc = bpy.context.scene
log = {"mat": MAT, "target": [TARGET_LO, TARGET_HI], "iterations": []}


def srgb(l):
    return 12.92 * l if l <= 0.0031308 else 1.055 * (l ** (1 / 2.4)) - 0.055


def lin(s):
    s = s / 255.0
    return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4


mat = bpy.data.materials.get(MAT)
if not mat:
    raise SystemExit("material not found: " + MAT)
bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
if not bsdf:
    raise SystemExit("no principled bsdf")

# ---------- 1. 断开贴图，改常量 ----------
bc = bsdf.inputs["Base Color"]
if bc.is_linked:
    for lk in list(bc.links):
        mat.node_tree.links.remove(lk)
    log["steps"] = ["unlink base color texture"]

# 初值：由 81 -> 205 的线性外推（渲染值约等于反照率 x 0.74）
START = (176, 190, 198)  # 冷灰：水面要比陆地冷，否则读成沙地
bc.default_value = (lin(START[0]), lin(START[1]), lin(START[2]), 1.0)


def measure():
    sc.cycles.samples = 24
    sc.render.resolution_percentage = 50
    sc.render.filepath = TMP
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(TMP, check_existing=False)
    W, H = img.size
    px = list(img.pixels)

    def avg(v0, v1, us):
        acc = [0.0, 0.0, 0.0]
        n = 0
        for vf in [v0 + (v1 - v0) * i / 5 for i in range(6)]:
            y = int(H * vf)
            row = H - 1 - y  # blender 像素原点在左下
            for uf in us:
                x = int(W * uf)
                i = (row * W + x) * 4
                for c in range(3):
                    # image.pixels 取回的 PNG 已是 sRGB 编码，不能再套 srgb()
                    acc[c] += px[i + c]
                n += 1
        return [round(255 * a / n, 1) for a in acc]

    water = avg(0.105, 0.135, [0.30, 0.50])
    shore = avg(0.070, 0.090, [0.30, 0.50])
    bpy.data.images.remove(img)
    return water, shore


best = None
for it in range(1, MAX_ITER + 1):
    water, shore = measure()
    wm = sum(water) / 3
    sm = sum(shore) / 3
    delta = wm - sm
    rec = {"iter": it, "base_srgb": [round(255 * srgb(c), 1) for c in bc.default_value[:3]],
           "water": water, "shore": shore,
           "water_mean": round(wm, 1), "delta_vs_shore": round(delta, 1)}
    log["iterations"].append(rec)
    print("ITER", it, "water", water, "mean", round(wm, 1),
          "shore", shore, "delta", round(delta, 1))
    best = rec

    if TARGET_LO <= wm <= TARGET_HI and delta >= MIN_DELTA_VS_SHORE:
        rec["verdict"] = "ok"
        break
    if wm < TARGET_LO:
        f = 1.18
    elif wm > TARGET_HI:
        f = 0.88
    else:
        f = 1.10
    # default_value 本身就是线性 0-1，直接缩放，不要再转 sRGB
    cur = list(bc.default_value[:3])
    new = [max(0.0, min(1.0, c * f)) for c in cur]
    bc.default_value = (new[0], new[1], new[2], 1.0)
    rec["applied_factor"] = f

log["final"] = best
log["lock"] = {
    "status": best.get("verdict", "not_converged"),
    "water_mean": best["water_mean"],
    "delta_vs_shore": best["delta_vs_shore"],
}

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))

with open(os.path.join(PRE, "B1_LOCK.json"), "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=1)

print("=== B1 ===")
for r in log["iterations"]:
    print("  ", json.dumps(r, ensure_ascii=False))
print("LOCK", json.dumps(log["lock"], ensure_ascii=False))
