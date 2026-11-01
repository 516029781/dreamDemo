# -*- coding: utf-8 -*-
"""G3：在正式图（含 world）上按 F/W/K/A/X 统计可见背景。

输入：
  renders/final.png            —— 正式合成图（1920×1078）
  renders/G3_world_exposure.png—— 同机位、景片保留 alpha、world=洋红的检查图
输出：
  reference_analysis/background_masks/V21_candidate_FWKA.png
  reference_analysis/background_masks/V21_candidate_FWKA_overlay.png
  reference_analysis/background_masks/V21_CANDIDATE_MASK.json（含面积与 SHA）
"""
import hashlib
import json
import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REN = os.path.join(ROOT, "renders")
OUT = os.path.join(ROOT, "reference_analysis", "background_masks")
os.makedirs(OUT, exist_ok=True)

final = Image.open(os.path.join(REN, "final.png")).convert("RGB")
W, H = final.size
world = Image.open(os.path.join(REN, "G3_world_exposure.png")).convert("RGB").resize((W, H), Image.NEAREST)

px = final.load()
wpx = world.load()

cls = Image.new("L", (W, H), 0)   # 1=F 2=W 3=K 4=A 5=X
cd = ImageDraw.Draw(cls)

BG_LIMIT = 0.170   # 台地前缘以上才是背景候选区（由 G1 投影实测）


def is_world(c):
    r, g, b = c
    return r > 120 and b > 120 and g < 80


def is_water(c):
    r, g, b = c
    return b > r + 4 and b > 78 and b >= g


def is_warm(c):
    r, g, b = c
    return r > b + 8 and r > 60


counts = {"F": 0, "W": 0, "K": 0, "A": 0, "X": 0}
for y in range(H):
    v = y / (H - 1)
    for x in range(W):
        c = px[x, y]
        wc = wpx[x, y]
        if is_world(wc):
            k = "A"
        elif v >= BG_LIMIT:
            k = "F"
        else:
            if is_water(c):
                k = "W"
            elif is_warm(c):
                k = "K" if v < 0.040 else "K"
            else:
                k = "A"
        counts[k] += 1
        cd.point((x, y), fill={"F": 1, "W": 2, "K": 3, "A": 4, "X": 5}[k])

palette = {1: (150, 146, 138), 2: (46, 104, 178), 3: (176, 150, 62), 4: (120, 76, 150), 5: (214, 40, 120)}
color = Image.new("RGB", (W, H), (0, 0, 0))
cp = color.load()
cl = cls.load()
for y in range(H):
    for x in range(W):
        cp[x, y] = palette[cl[x, y]]
color.save(os.path.join(OUT, "V21_candidate_FWKA.png"))
Image.blend(final, color, 0.5).save(os.path.join(OUT, "V21_candidate_FWKA_overlay.png"))

n = W * H
areas = {k: round(v / n, 5) for k, v in counts.items()}
U = areas["F"] + areas["W"] + areas["K"] + areas["A"]
bg = areas["W"] + areas["K"] + areas["A"]
areas["U"] = round(U, 5)
areas["background"] = round(bg, 5)
areas["background_over_U"] = round(bg / U, 5) if U else None

ref = json.load(open(os.path.join(OUT, "P1_FWKA_MASK.json"), encoding="utf-8"))
ref_areas = ref["areas_fraction_of_frame"]
ref_bg_u = ref_areas["background_over_U"]

sha_final = hashlib.sha256(open(os.path.join(REN, "final.png"), "rb").read()).hexdigest()
sha_map = hashlib.sha256(open(os.path.join(OUT, "V21_candidate_FWKA.png"), "rb").read()).hexdigest()

record = {
    "schema": "p1-candidate-fwka-mask/v1",
    "candidate": "v21",
    "final_png_sha256": sha_final,
    "method": ("在 50%/100% 正式图上按色彩与位置分类：world 由同机位洋红检查图判定并全部计入 A；"
               "v≥0.170 记为 F（台地前缘以上为背景候选区）；蓝灰判 W，暖色判 K，其余判 A。"
               "分类以人工复核叠图为准，不是自动分割真值。"),
    "areas_fraction_of_frame": areas,
    "reference": {"background_over_U": ref_bg_u,
                  "background_fraction_of_frame": ref_areas["background"],
                  "source": "reference_analysis/background_masks/P1_FWKA_MASK.json"},
    "delta_background_over_U_pp": round((areas["background_over_U"] - ref_bg_u) * 100, 2),
    "outputs": {"classmap": {"path": "reference_analysis/background_masks/V21_candidate_FWKA.png",
                             "sha256": sha_map}},
    "world_included": True,
    "note": "world 可见像素通过洋红检查图单独识别后并入 A，不再用卡片开关差分。",
}
json.dump(record, open(os.path.join(OUT, "V21_CANDIDATE_MASK.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(json.dumps(areas, ensure_ascii=False, indent=1))
print("delta pp", record["delta_background_over_U_pp"])
