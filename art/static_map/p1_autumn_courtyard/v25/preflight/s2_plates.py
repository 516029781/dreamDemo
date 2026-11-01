# -*- coding: utf-8 -*-
"""S2 · 重绘背景景片：M03 顶部暗云带 + M02 金色土坡，按参考实测明度阶梯。

参考实测（u0.20-0.78 水平带均值）：
  v0-8  : 82-96   顶暗（云/阴影）
  v8-10 : 88
  v10-12: 103
  v12-14: 117
  v14-16: 128
  v16-18: 141
  v18-20: 142
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = os.path.join(ROOT, "background_src")
random.seed(20261101)


def ramp(stops, t):
    for i in range(len(stops) - 1):
        a, ca = stops[i]
        b, cb = stops[i + 1]
        if a <= t <= b:
            k = (t - a) / max(1e-6, b - a)
            return tuple(int(ca[j] + (cb[j] - ca[j]) * k) for j in range(3))
    return stops[-1][1]


# ---------------- M03：顶部暗云带 ----------------
p = os.path.join(BG, "M03_air.png")
im = Image.open(p).convert("RGBA")
W, H = im.size
px = im.load()
stops = [(0.000, (84, 71, 63)), (0.040, (90, 76, 67)), (0.080, (98, 83, 72)),
         (0.110, (104, 88, 75)), (0.140, (110, 93, 78))]
for y in range(H):
    t = y / H
    if t > 0.150:
        for x in range(W):
            r, g, b, _ = px[x, y]
            px[x, y] = (r, g, b, 0)
        continue
    c = ramp(stops, min(t, 0.140))
    a = 255
    if t > 0.130:
        a = int(255 * max(0.0, 1 - (t - 0.130) / 0.020) ** 1.3)
    for x in range(W):
        px[x, y] = (c[0], c[1], c[2], a)

# 云团：低对比的明暗块，打散"平带"感
cloud = Image.new("RGBA", (W, int(H * 0.16)), (0, 0, 0, 0))
d = ImageDraw.Draw(cloud)
for i in range(90):
    cx = random.uniform(0, W)
    cy = random.uniform(0, H * 0.140)
    rw = random.uniform(W * 0.05, W * 0.22)
    rh = random.uniform(H * 0.006, H * 0.022)
    tone = random.choice([(96, 82, 72), (78, 66, 58), (108, 92, 80)])
    d.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=(*tone, random.randint(28, 70)))
cloud = cloud.filter(ImageFilter.GaussianBlur(9))
im.alpha_composite(cloud)
im.save(p)
print("M03", im.size, "top", im.getpixel((W // 2, 3)), "v6%", im.getpixel((W // 2, int(H * 0.06))))

# ---------------- M02：金色土坡 ----------------
p = os.path.join(BG, "M02_bank.png")
im = Image.open(p).convert("RGBA")
W, H = im.size
px = im.load()
stops = [(0.085, (106, 90, 74)), (0.100, (112, 95, 76)), (0.120, (124, 105, 80)),
         (0.140, (140, 117, 88)), (0.160, (156, 129, 96)), (0.180, (170, 140, 104)),
         (0.196, (176, 146, 110))]
for y in range(H):
    t = y / H
    if t < 0.082 or t > 0.215:
        for x in range(W):
            r, g, b, _ = px[x, y]
            px[x, y] = (r, g, b, 0)
        continue
    c = ramp(stops, min(max(t, 0.085), 0.196))
    a = 255
    if t < 0.095:
        a = int(255 * (t - 0.082) / 0.013)
    elif t > 0.196:
        a = int(255 * max(0.0, 1 - (t - 0.196) / 0.019) ** 1.4)
    for x in range(W):
        px[x, y] = (c[0], c[1], c[2], a)

# 土坡细节：明暗斑块 + 低矮起伏
detail = Image.new("RGBA", (W, int(H * 0.20)), (0, 0, 0, 0))
d = ImageDraw.Draw(detail)
for i in range(160):
    cx = random.uniform(0, W)
    cy = random.uniform(H * 0.10, H * 0.20)
    rw = random.uniform(W * 0.02, W * 0.09)
    rh = random.uniform(H * 0.003, H * 0.012)
    tone = random.choice([(150, 122, 88), (120, 100, 74), (168, 138, 100), (108, 92, 70)])
    d.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=(*tone, random.randint(35, 90)))
detail = detail.filter(ImageFilter.GaussianBlur(5))
im.alpha_composite(detail)

# 远处树线剪影，压在上缘，避免"平带"
line = Image.new("RGBA", (W, int(H * 0.035)), (0, 0, 0, 0))
d = ImageDraw.Draw(line)
base = int(H * 0.025)
for x in range(0, W, 5):
    t = x / W
    hh = base + 6 * (0.6 * math.sin(t * 13.0) + 0.4 * math.sin(t * 29.0 + 1.3))
    d.line([(x, base + 10), (x, base + 10 - hh)], fill=(96, 82, 70, 150), width=5)
line = line.filter(ImageFilter.GaussianBlur(2.2))
im.alpha_composite(line, (0, int(H * 0.088)))
im.save(p)
print("M02", im.size, "v10%", im.getpixel((W // 2, int(H * 0.10))),
      "v15%", im.getpixel((W // 2, int(H * 0.15))), "v18%", im.getpixel((W // 2, int(H * 0.18))))
print("S2_TEX_DONE")
