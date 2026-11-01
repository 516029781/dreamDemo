# -*- coding: utf-8 -*-
"""S2d · 重绘远景景片（B0/B1/B2/B3）

问题：M03/M02 现在只是画布顶部的一条**纯色平带**（1920x1078 里只用了 0-15%），
渲染出来是"一堵灰墙 + 一条亮线"，没有天空、没有树线、没有远近关系。

本脚本按屏幕 v 坐标反算贴图行，画出：
  M03（v0-10）  暖灰天空：顶部暗、向下渐亮、低对比云团、地平线一带雾化
  M02（v8.2-21.5）远岸：亮雾地平线 → 金色土坡 + 远树线剪影 → 近处暖沙

坐标关系（实测）：景片距机约 61 m，贴图 1078 行覆盖画面 v ≈ -0.03~1.0，
即 1 贴图行 ≈ 0.096% v；横向 1920 px ≈ 1.02 画面宽。
"""
import json
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = os.path.join(ROOT, "background_src")
W, H = 1920, 1078
random.seed(20261101)

ROW = 1078.0          # 贴图行数对应 v 0..1 的一段（约）


def v2row(v):
    return int(v * ROW)


def lerp(a, b, t):
    return a + (b - a) * t


def ramp(stops, t):
    for i in range(len(stops) - 1):
        a, ca = stops[i]
        b, cb = stops[i + 1]
        if a <= t <= b:
            k = (t - a) / max(1e-6, b - a)
            return tuple(int(ca[j] + (cb[j] - ca[j]) * k) for j in range(3))
    return stops[-1][1] if t > stops[-1][0] else stops[0][1]


# ============================================================
# M03 · 天空（v0–10）
# ============================================================
p = os.path.join(BG, "M03_air.png")
im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(im)

V_END = 0.108        # 天空到 v10.8 结束
for y in range(0, v2row(V_END)):
    t = y / v2row(V_END)
    # 顶部暗，向下渐亮；地平线一带雾化成暖白
    # 参考 v0-8 均值 87.6：整体压暗，到交界前快速抬亮与 M02 相接
    base = ramp([(0.00, (72, 62, 55)), (0.30, (78, 67, 58)),
                 (0.56, (90, 78, 66)), (0.78, (110, 96, 80)),
                 (0.91, (126, 112, 94)), (1.00, (136, 122, 102))], t)
    a = 255
    if t > 0.90:      # 与 M02 交叉淡出
        a = int(255 * max(0.0, 1 - (t - 0.90) / 0.10) ** 1.2)
    d.line([(0, y), (W, y)], fill=(*base, a))

# 云团：低对比明暗块，横向拉长（上部压暗、下部提亮，制造"天光"方向）
cloud = Image.new("RGBA", (W, v2row(V_END)), (0, 0, 0, 0))
cd = ImageDraw.Draw(cloud)
for i in range(180):
    cx = random.uniform(-W * 0.1, W * 1.1)
    cy = random.uniform(0, v2row(V_END) * 0.95)
    rw = random.uniform(W * 0.05, W * 0.26)
    rh = random.uniform(3, 13)
    upper = cy < v2row(V_END) * 0.42
    tone = random.choice([(74, 63, 54), (92, 80, 68)] if upper
                         else [(126, 112, 96), (116, 102, 86), (134, 120, 102)])
    cd.ellipse([cx - rw, cy - rh, cx + rw, cy + rh],
               fill=(*tone, random.randint(22, 54)))
cloud = cloud.filter(ImageFilter.GaussianBlur(13))
im.alpha_composite(cloud)

# 远树线：v8.2-9.9 一条不规则的暗剪影，这是"地平线"的读点
tree = Image.new("RGBA", (W, H), (0, 0, 0, 0))
td = ImageDraw.Draw(tree)
base_y = v2row(0.0975)
x = -20
while x < W + 20:
    cw = random.uniform(W * 0.010, W * 0.038)
    ch = random.uniform(v2row(0.008), v2row(0.022))
    tone = random.choice([(70, 58, 46), (82, 68, 54), (62, 52, 42)])
    td.ellipse([x, base_y - ch, x + cw, base_y + ch * 0.45],
               fill=(*tone, random.randint(150, 225)))
    if random.random() < 0.12:   # 偶尔留个缺口，露出后面的亮雾
        td.rectangle([x + cw * 0.3, base_y - ch, x + cw * 0.7, base_y],
                     fill=(0, 0, 0, 0))
    x += cw * random.uniform(0.45, 0.9)
tree = tree.filter(ImageFilter.GaussianBlur(2.2))
im.alpha_composite(tree)

# 树线以上的暖雾：让树线"沉"进远景
haze = Image.new("RGBA", (W, H), (0, 0, 0, 0))
hd = ImageDraw.Draw(haze)
for y in range(v2row(0.070), v2row(0.100)):
    t = (y - v2row(0.070)) / max(1, v2row(0.100) - v2row(0.070))
    hd.line([(0, y), (W, y)], fill=(150, 136, 116, int(70 * t ** 1.4)))
im.alpha_composite(haze.filter(ImageFilter.GaussianBlur(4)))
im.save(p)
print("M03", im.size, "v2%", im.getpixel((W // 2, v2row(0.02)))[:3],
      "v6%", im.getpixel((W // 2, v2row(0.06)))[:3],
      "v9%", im.getpixel((W // 2, v2row(0.09)))[:3])

# ============================================================
# M02 · 远岸（v8.2–21.5）
# ============================================================
p = os.path.join(BG, "M02_bank.png")
im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(im)

V0, V1 = 0.078, 0.220
r0, r1 = v2row(V0), v2row(V1)

# 1) 底色：地平线亮雾 → 金色土坡 → 近处暖沙
for y in range(r0, r1):
    t = (y - r0) / (r1 - r0)
    # 顶部先压暗（远树线之下的背光带 v8-9.5），再在 v9.5-11 抬成地平线雾
    # 参考 v10-22 均值 127.4：顶部不能再压暗，否则接缝处差 40 灰阶
    c = ramp([(0.00, (140, 126, 106)), (0.06, (136, 122, 102)),
              (0.14, (142, 128, 108)), (0.22, (152, 136, 112)),
              (0.32, (150, 128, 98)), (0.46, (154, 128, 94)),
              (0.62, (146, 120, 86)), (0.80, (134, 110, 80)),
              (1.00, (122, 100, 74))], t)
    a = 255
    if t < 0.055:
        a = int(255 * t / 0.055)
    elif t > 0.90:
        a = int(255 * max(0.0, 1 - (t - 0.90) / 0.10) ** 1.3)
    d.line([(0, y), (W, y)], fill=(*c, a))

# 2) 远山轮廓：地平线下 3-8%，一条低起伏暗带（比底色暗 20）
ridge = Image.new("RGBA", (W, H), (0, 0, 0, 0))
rd = ImageDraw.Draw(ridge)
base_y = r0 + (r1 - r0) * 0.10
for x in range(W):
    t = x / W
    hh = (r1 - r0) * (0.020 + 0.016 * math.sin(t * 7.0 + 0.8)
                      + 0.009 * math.sin(t * 17.0 + 2.1)
                      + 0.005 * math.sin(t * 41.0))
    rd.line([(x, base_y + hh), (x, base_y - hh * 0.6)],
            fill=(126, 110, 88, 170), width=2)
ridge = ridge.filter(ImageFilter.GaussianBlur(2.4))
im.alpha_composite(ridge)

# 3) 远树线：地平线上方一排低矮树冠剪影（成簇，不是等距）
trees = Image.new("RGBA", (W, H), (0, 0, 0, 0))
td = ImageDraw.Draw(trees)
x = 0
while x < W:
    cw = random.uniform(W * 0.006, W * 0.030)
    ch = random.uniform(6, 15)
    cy = r0 + (r1 - r0) * 0.085
    td.ellipse([x, cy - ch, x + cw, cy + ch * 0.7],
               fill=(118, 102, 82, random.randint(70, 120)))
    x += cw * random.uniform(0.55, 1.05)
trees = trees.filter(ImageFilter.GaussianBlur(3.0))
im.alpha_composite(trees)

# 4) 土坡斑块：明暗草簇/田块，打散平带
blobs = Image.new("RGBA", (W, H), (0, 0, 0, 0))
bd = ImageDraw.Draw(blobs)
for i in range(320):
    cx = random.uniform(0, W)
    cy = random.uniform(r0 + (r1 - r0) * 0.16, r1)
    rw = random.uniform(W * 0.01, W * 0.06)
    rh = random.uniform(2, 9)
    tone = random.choice([(158, 130, 94), (128, 104, 76), (166, 140, 102),
                          (112, 92, 68), (150, 118, 82)])
    bd.ellipse([cx - rw, cy - rh, cx + rw, cy + rh],
               fill=(*tone, random.randint(24, 70)))
blobs = blobs.filter(ImageFilter.GaussianBlur(6))
im.alpha_composite(blobs)

# 5) 近处压暗：v18 以下远景应该被地面挡住，留一点暗过渡避免硬边
shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(shade)
for y in range(r0 + int((r1 - r0) * 0.55), r1):
    t = (y - r0 - (r1 - r0) * 0.55) / max(1, (r1 - r0) * 0.45)
    sd.line([(0, y), (W, y)], fill=(104, 88, 68, int(30 * t)))
im.alpha_composite(shade.filter(ImageFilter.GaussianBlur(5)))
im.save(p)
print("M02", im.size, "v9%", im.getpixel((W // 2, v2row(0.09)))[:3],
      "v12%", im.getpixel((W // 2, v2row(0.12)))[:3],
      "v16%", im.getpixel((W // 2, v2row(0.16)))[:3])

json.dump({"M03": {"v_end": V_END}, "M02": {"v0": V0, "v1": V1}},
          open(os.path.join(ROOT, "preflight", "S2D_PLATES.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("S2D_DONE")
