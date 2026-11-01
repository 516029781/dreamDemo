# -*- coding: utf-8 -*-
"""G0：对 P1 主参考人工重描 U/F/W/K/A/X 五类，输出类别图、叠图与面积表。

坐标一律归一化（左上原点）。类别：
  F 可见近中景实体（台阶/平台/树/草池/设备/近岸）
  W 可见远水
  K 对岸与远植被
  A 天空/空气/更远树影（含 world 兜底）
  X 参考里的 UI、角色、字幕及无法判断处
U = F ∪ W ∪ K ∪ A；B_ref = W ∪ K ∪ A。
"""
import hashlib
import json
import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _project_root(p):
    cur = os.path.abspath(p)
    for _ in range(8):
        if os.path.isdir(os.path.join(cur, "reference")) and os.path.isdir(os.path.join(cur, "tools")):
            return cur
        cur = os.path.dirname(cur)
    raise RuntimeError("project root not found")


PROJ = _project_root(ROOT)
REF = os.path.join(PROJ, "reference", "_raw_screenshots", "P1", "t084s.jpg")
OUT = os.path.join(ROOT, "reference_analysis", "background_masks")
W, H = 1920, 1078

os.makedirs(OUT, exist_ok=True)

# ---- X：UI / 角色 / 字幕 ----
X = [
    [(0.000, 0.000), (0.318, 0.000), (0.318, 0.050), (0.000, 0.050)],          # 顶部说明条
    [(0.000, 0.052), (0.140, 0.052), (0.140, 0.288), (0.000, 0.288)],          # 左侧任务卡
    [(0.022, 0.850), (0.078, 0.850), (0.078, 0.916), (0.022, 0.916)],          # 左下眼睛键
    [(0.832, 0.762), (0.942, 0.762), (0.942, 0.932), (0.832, 0.932)],          # 右下交互卡
    [(0.944, 0.852), (1.000, 0.852), (1.000, 0.948), (0.944, 0.948)],          # 右下 Shift/奔跑
    [(0.472, 0.375), (0.578, 0.375), (0.578, 0.562), (0.472, 0.562)],          # 角色与选中环
    [(0.518, 0.328), (0.572, 0.328), (0.572, 0.400), (0.518, 0.400)],          # 角色上方小图标
    [(0.098, 0.330), (0.132, 0.330), (0.132, 0.392), (0.098, 0.392)],          # 左侧感叹号
]

# ---- W：可见远水（横向缺口，两端被树/设备/草池挡住）----
W_POLY = [
    (0.258, 0.158), (0.292, 0.140), (0.340, 0.132), (0.392, 0.132),
    (0.446, 0.140), (0.492, 0.150), (0.516, 0.166), (0.520, 0.196),
    (0.494, 0.212), (0.446, 0.222), (0.386, 0.226), (0.330, 0.220),
    (0.284, 0.204), (0.262, 0.184),
]

# ---- K：对岸与远植被（水之上、天空之下的暖浅地形与树影）----
K_POLY = [
    (0.212, 0.058), (0.286, 0.046), (0.368, 0.044), (0.452, 0.046),
    (0.528, 0.052), (0.604, 0.062), (0.620, 0.104), (0.588, 0.128),
    (0.520, 0.146), (0.470, 0.142), (0.410, 0.132), (0.348, 0.132),
    (0.292, 0.142), (0.244, 0.156), (0.216, 0.120),
]

# ---- A：天空 / 空气 / 更远树影（上缘带；被树、草池、UI 切走的部分另算）----
A_POLYS = [
    [(0.000, 0.000), (1.000, 0.000), (1.000, 0.058), (0.000, 0.058)],
]

# ---- F：其余可观察区 = U 减去 W/K/A/X ----
# U 由人工界定：参考里除 UI/角色外全部是环境；四角被 UI 切掉的按 X 计。


def poly_mask(size, polys):
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    for p in polys:
        d.polygon([(x * size[0], y * size[1]) for x, y in p], fill=255)
    return m


ref = Image.open(REF).convert("RGB")
assert ref.size == (W, H), ref.size

x_m = poly_mask((W, H), X)
w_m = poly_mask((W, H), [W_POLY])
k_m = poly_mask((W, H), K_POLY and [K_POLY])
a_m = poly_mask((W, H), A_POLYS)

# U = 全画幅 - X；背景 = W∪K∪A，但要扣除 X（被 UI 挡住的部分不算可见背景）
bg = Image.new("L", (W, H), 0)
for m in (w_m, k_m, a_m):
    bg = Image.composite(m, bg, m)
inv_x = Image.eval(x_m, lambda v: 255 - v)
bg = Image.composite(bg, Image.new("L", (W, H), 0), inv_x)
u_m = inv_x
f_m = Image.new("L", (W, H), 0)
f_m.paste(u_m, (0, 0))
for m in (bg,):
    f_m = Image.composite(Image.new("L", (W, H), 0), f_m, m)

# 类别图：F 暖灰、W 蓝、K 黄绿、A 紫、X 洋红
color = Image.new("RGB", (W, H), (0, 0, 0))
color.paste(Image.new("RGB", (W, H), (150, 146, 138)), (0, 0), f_m)
color.paste(Image.new("RGB", (W, H), (46, 104, 178)), (0, 0), w_m)
color.paste(Image.new("RGB", (W, H), (176, 150, 62)), (0, 0), k_m)
color.paste(Image.new("RGB", (W, H), (120, 76, 150)), (0, 0), a_m)
color.paste(Image.new("RGB", (W, H), (214, 40, 120)), (0, 0), x_m)
color.save(os.path.join(OUT, "P1_FWKA_classmap.png"))

overlay = Image.blend(ref, color, 0.55)
overlay.save(os.path.join(OUT, "P1_FWKA_overlay.png"))

n = W * H


def frac(m):
    return sum(1 for v in m.getdata() if v > 127) / n


areas = {
    "frame_px": [W, H],
    "F": round(frac(f_m), 5),
    "W": round(frac(w_m), 5),
    "K": round(frac(k_m), 5),
    "A_full_band": round(frac(a_m), 5),
    "X": round(frac(x_m), 5),
}
areas["U"] = round(areas["F"] + areas["W"] + areas["K"] + frac(
    Image.composite(a_m, Image.new("L", (W, H), 0), inv_x)), 5)

# 实际可见 A（扣掉 X 与树/草池遮挡后）
a_vis = Image.composite(a_m, Image.new("L", (W, H), 0), inv_x)
a_vis = Image.composite(a_vis, Image.new("L", (W, H), 0), f_m.point(lambda v: 255 - v))
# 已被 W/K 覆盖的 A 不应重复计
a_only = Image.new("L", (W, H), 0)
a_only.paste(a_vis, (0, 0))
for m in (w_m, k_m):
    a_only = Image.composite(Image.new("L", (W, H), 0), a_only, m)
areas["A_visible"] = round(frac(a_only), 5)

areas["background"] = round(areas["W"] + areas["K"] + areas["A_visible"], 5)
areas["background_over_U"] = round(areas["background"] / areas["U"], 5) if areas["U"] else None
areas["note"] = ("A 先按 0–5.8% 全宽上缘带登记，再扣除被 X、树冠、草池遮住的部分；"
                 "W/K 为人工多边形近似，不是像素级分割真值。")

sha_ref = hashlib.sha256(open(REF, "rb").read()).hexdigest()
sha_map = hashlib.sha256(open(os.path.join(OUT, "P1_FWKA_classmap.png"), "rb").read()).hexdigest()
sha_ov = hashlib.sha256(open(os.path.join(OUT, "P1_FWKA_overlay.png"), "rb").read()).hexdigest()

record = {
    "schema": "p1-reference-fwka-mask/v1",
    "reference": {"path": "reference/_raw_screenshots/P1/t084s.jpg", "sha256": sha_ref,
                  "frame_px": [W, H]},
    "method": ("人工多边形重描，非自动分割；坐标归一化，标在 50% 图上先定大形，"
               "再按原尺寸检查水岸、树枝与 UI 邻接边。V20 旧遮罩只作起点，本轮独立重画。"),
    "classes": {"F": "可见近中景实体", "W": "可见远水", "K": "对岸/远植被",
                "A": "天空/空气/更远树影（含 world 兜底）", "X": "UI/角色/字幕/不可判断"},
    "areas_fraction_of_frame": areas,
    "polygons": {"X": X, "W": W_POLY, "K": K_POLY, "A": A_POLYS},
    "outputs": {
        "classmap": {"path": "reference_analysis/background_masks/P1_FWKA_classmap.png", "sha256": sha_map},
        "overlay": {"path": "reference_analysis/background_masks/P1_FWKA_overlay.png", "sha256": sha_ov},
    },
    "evaluation_mode": "manual_only",
    "caveat": "锚区为人工近似，不得当作自动判定容差；面积只作趋势与量级对照。",
}
json.dump(record, open(os.path.join(OUT, "P1_FWKA_MASK.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(json.dumps(areas, ensure_ascii=False, indent=1))
print("classmap", sha_map[:16], "overlay", sha_ov[:16])
