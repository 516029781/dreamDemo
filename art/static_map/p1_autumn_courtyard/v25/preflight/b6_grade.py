# -*- coding: utf-8 -*-
"""B6 后期：暖调 + 颗粒 + 暗角。系统 Python + PIL。

用法：python preflight/b6_grade.py [--in renders/final.png] [--out renders/final_graded.png]
"""
import argparse
import os
import random

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.dirname(HERE)

ap = argparse.ArgumentParser()
ap.add_argument("--in", dest="src", default="renders/final.png")
ap.add_argument("--out", dest="dst", default="renders/final_graded.png")
ap.add_argument("--warm-r", type=float, default=1.06)
ap.add_argument("--warm-b", type=float, default=0.97)
ap.add_argument("--grain", type=float, default=4.0)
ap.add_argument("--vignette", type=float, default=0.12)
ap.add_argument("--seed", type=int, default=20261031)
args = ap.parse_args()
random.seed(args.seed)

p_in = os.path.join(CAND, args.src)
p_out = os.path.join(CAND, args.dst)
im = Image.open(p_in).convert("RGB")
W, H = im.size

# 1) 暖调（在 float 域做，避免 8bit 截断）
px = im.load()
for y in range(H):
    for x in range(W):
        r, g, b = px[x, y]
        px[x, y] = (min(255, int(r * args.warm_r)),
                    g,
                    max(0, int(b * args.warm_b)))

# 2) 暗角
vig = Image.new("L", (W, H), 0)
vd = ImageDraw.Draw(vig)
cx, cy = W / 2, H / 2
maxd = (cx ** 2 + cy ** 2) ** 0.5
for i in range(40):
    t = i / 39.0
    r = maxd * (0.55 + 0.45 * t)
    vd.ellipse([cx - r, cy - r * H / W, cx + r, cy + r * H / W],
               outline=int(255 * (1 - t)))
vig = vig.filter(ImageFilter.GaussianBlur(W * 0.06))
vpx = vig.load()
for y in range(H):
    for x in range(W):
        k = 1.0 - args.vignette * (vpx[x, y] / 255.0)
        r, g, b = px[x, y]
        px[x, y] = (int(r * k), int(g * k), int(b * k))

# 3) 颗粒（单色，基于亮度扰动）
grain = Image.effect_noise((W, H), args.grain * 6).convert("L")
gpx = grain.load()
for y in range(H):
    for x in range(W):
        d = int((gpx[x, y] - 128) * (args.grain / 40.0))
        r, g, b = px[x, y]
        px[x, y] = (max(0, min(255, r + d)),
                    max(0, min(255, g + d)),
                    max(0, min(255, b + d)))

im.save(p_out)
print("GRADED", p_out, f"grain={args.grain} vignette={args.vignette}")
