# -*- coding: utf-8 -*-
"""重绘 M03 空气层顶部为暖色远山 + 暖雾，替换掉旧的蓝灰带。

旧 M03_air.png 顶部像素 (86,74,78) 深灰，且 y>=60 全透明；
但成图顶部呈 (101,107,120) 蓝灰，说明 blend 内为 packed 旧缓存。
本脚本只改磁盘 PNG，reload 由 c3_reload_images.py 负责。
"""
import os
import random

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "background_src")
W, H = 1920, 1078
random.seed(20261031)

path = os.path.join(SRC, "M03_air.png")
im = Image.open(path).convert("RGBA")
px = im.load()

# 顶部 0–72 px 重绘暖色远山层（v 0–6.7%）
TOP = 72
SKY_TOP = (96, 78, 62)     # 上方深赭
SKY_MID = (150, 126, 100)  # 中段暖雾
RIDGE = (108, 88, 68)      # 山脊
HAZE = (186, 162, 130)     # 底部暖雾

# 1) 竖向渐变底
for y in range(TOP):
    t = y / max(1, TOP - 1)
    if t < 0.35:
        k = t / 0.35
        c = tuple(int(SKY_TOP[i] + (SKY_MID[i] - SKY_TOP[i]) * k) for i in range(3))
    else:
        k = (t - 0.35) / 0.65
        c = tuple(int(SKY_MID[i] + (HAZE[i] - SKY_MID[i]) * k) for i in range(3))
    for x in range(W):
        px[x, y] = (c[0], c[1], c[2], 255)

# 2) 远山剪影：两段起伏，压在 v 1.5–4.5%
ridge = Image.new("RGBA", (W, TOP), (0, 0, 0, 0))
rd = ImageDraw.Draw(ridge)
for layer, (amp, base, alpha) in enumerate([(9, 30, 150), (6, 44, 200)]):
    pts = [(0, TOP)]
    ph = random.uniform(0, 6.28)
    for x in range(0, W + 8, 8):
        t = x / W
        y = base + amp * (
            0.55 * __import__("math").sin(t * 6.1 + ph)
            + 0.30 * __import__("math").sin(t * 13.7 + ph * 1.7)
            + 0.15 * __import__("math").sin(t * 27.3 + ph * 2.3)
        )
        pts.append((x, y))
    pts.append((W, TOP))
    rd.polygon(pts, fill=(RIDGE[0], RIDGE[1], RIDGE[2], alpha))
ridge = ridge.filter(ImageFilter.GaussianBlur(1.1))
im.alpha_composite(ridge)

# 3) 顶部再压一层暖雾，避免与 M02 交界生硬
fog = Image.new("RGBA", (W, 26), (HAZE[0], HAZE[1], HAZE[2], 0))
fd = ImageDraw.Draw(fog)
for y in range(26):
    a = int(120 * (y / 25.0) ** 1.6)
    fd.line([(0, y), (W, y)], fill=(HAZE[0], HAZE[1], HAZE[2], a))
im.alpha_composite(fog, (0, TOP - 26))

im.save(path)
print("REWROTE", path)
print("  top px", im.getpixel((W // 2, 2)), im.getpixel((W // 2, 30)), im.getpixel((W // 2, 60)))
