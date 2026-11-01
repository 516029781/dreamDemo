# -*- coding: utf-8 -*-
"""B3 重绘 M03 景片：v0-8% 远山 + 树线，其余透明。用系统 Python + PIL。

用法：python preflight/b3_sky.py [--src 目录]
"""
import argparse
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.dirname(HERE)
SRC = os.path.join(CAND, "background_src")

ap = argparse.ArgumentParser()
ap.add_argument("--file", default="M03_air.png")
ap.add_argument("--seed", type=int, default=20261031)
args = ap.parse_args()
random.seed(args.seed)

W, H = 1920, 1078
V_SKY_TOP = 0.000
V_RIDGE = 0.040     # 远山底
V_TREE = 0.080      # 树线底
y_ridge = int(H * V_RIDGE)
y_tree = int(H * V_TREE)

im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
px = im.load()

# ---------- 1. 天光：v0-4% 暖灰到暖白 ----------
for y in range(0, y_ridge):
    t = y / max(1, y_ridge - 1)
    c = (int(150 + 40 * t), int(132 + 38 * t), int(110 + 34 * t))
    for x in range(W):
        px[x, y] = (c[0], c[1], c[2], 255)

# ---------- 2. 远山：两层剪影，v1-4% ----------
ridge = Image.new("RGBA", (W, y_ridge), (0, 0, 0, 0))
rd = ImageDraw.Draw(ridge)
for amp, base, alpha, col in [(9, y_ridge * 0.42, 130, (128, 108, 88)),
                              (6, y_ridge * 0.66, 185, (104, 86, 70))]:
    pts = [(0, y_ridge)]
    ph = random.uniform(0, 6.28)
    for x in range(0, W + 8, 6):
        t = x / W
        yy = base + amp * (0.55 * math.sin(t * 5.1 + ph)
                           + 0.30 * math.sin(t * 12.7 + ph * 1.7)
                           + 0.15 * math.sin(t * 24.3 + ph * 2.1))
        pts.append((x, yy))
    pts.append((W, y_ridge))
    rd.polygon(pts, fill=(col[0], col[1], col[2], alpha))
im.alpha_composite(ridge.filter(ImageFilter.GaussianBlur(1.2)))

# ---------- 3. 树线：v4-8%，连续轮廓带 ----------
trees = Image.new("RGBA", (W, y_tree), (0, 0, 0, 0))
td = ImageDraw.Draw(trees)

# 轮廓线：低频起伏 + 高频锯齿
crest = []
ph1, ph2 = random.uniform(0, 6.28), random.uniform(0, 6.28)
for x in range(0, W + 4, 3):
    t = x / W
    base = y_ridge + (y_tree - y_ridge) * 0.35
    y = base \
        + 7.0 * math.sin(t * 7.3 + ph1) \
        + 3.5 * math.sin(t * 19.1 + ph2) \
        + 2.0 * math.sin(t * 41.7 + ph1 * 2.3)
    crest.append((x, y))

# 树冠体：轮廓线到底部，两层色
for layer, (col, alpha, dy) in enumerate([((92, 74, 58), 235, 0),
                                          ((70, 56, 44), 215, 6)]):
    pts = [(x, y + dy) for x, y in crest] + [(W, y_tree), (0, y_tree)]
    td.polygon(pts, fill=(col[0], col[1], col[2], alpha))

# 树冠内部的暗块，打散"色带感"
for _ in range(220):
    cx = random.randint(0, W - 1)
    idx = min(len(crest) - 1, cx // 3)
    cy = crest[idx][1] + random.uniform(2, (y_tree - y_ridge) * 0.9)
    r = random.uniform(4, 16)
    shade = random.choice([(58, 46, 36), (84, 68, 52), (46, 36, 28)])
    td.ellipse([cx - r, cy - r * 0.6, cx + r, cy + r * 0.6],
               fill=(*shade, random.randint(60, 150)))

# 顶部个别尖梢
for _ in range(140):
    x = random.randint(0, W - 1)
    idx = min(len(crest) - 1, x // 3)
    y0 = crest[idx][1]
    h = random.uniform(6, 22)
    td.line([(x, y0), (x + random.uniform(-2, 2), y0 - h)],
            fill=(70, 56, 44, random.randint(140, 220)), width=random.choice([1, 2]))

im.alpha_composite(trees.filter(ImageFilter.GaussianBlur(0.7)))

# ---------- 4. 下缘渐隐 v8-9% ----------
fade_end = int(H * 0.092)
for y in range(y_tree, fade_end):
    t = (y - y_tree) / max(1, fade_end - y_tree)
    a_scale = (1 - t) ** 1.4
    for x in range(W):
        r, g, b, a = px[x, y]
        if a == 0:
            continue
        px[x, y] = (r, g, b, int(a * a_scale))

out = os.path.join(SRC, args.file)
im.save(out)
print("WROTE", out)
for v in [0.005, 0.02, 0.035, 0.05, 0.07, 0.085, 0.10]:
    y = min(H - 1, int(H * v))
    print(f"  v={v*100:5.1f}%  px={im.getpixel((W//2, y))}")
