# -*- coding: utf-8 -*-
"""G1b/G2 分层源绘制（M02 对岸 / M03 空气与远树）。

画布 1920×1078、RGBA。屏幕坐标 = 贴图坐标（景片按相机视锥构建）。
带位置由 G1_SHORE_PROJECTION.json 反算：
  水面（真实网格 y15.3–22.5, z=-0.18）→ v 0.223–0.126
  对岸 M02 → v 0.040–0.136（下缘压进水面 0.010）
  空气 M03 → v 0.000–0.052（下缘压进对岸 0.012）
"""
import json
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "background_src")
W, H = 1920, 1078
os.makedirs(SRC, exist_ok=True)

P = {
    "air_top":    (86, 74, 78),
    "air_mid":    (112, 96, 92),
    "haze":       (168, 148, 124),
    "fartree":    (92, 76, 64),
    "fartree_hi": (116, 98, 78),
    "bank_top":   (176, 154, 112),
    "bank_mid":   (156, 134, 96),
    "bank_low":   (124, 104, 74),
    "bank_dark":  (96, 80, 58),
    "reed":       (188, 164, 108),
    "water_edge": (86, 100, 102),
}

V_BANK_TOP, V_BANK_BOT = 0.022, 0.066
V_AIR_BOT = 0.030
V_WATER_TOP = 0.058


def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def vgrad(d, y0, y1, c0, c1, alpha0=255, alpha1=255):
    y0, y1 = int(y0), int(y1)
    h = max(1, y1 - y0)
    for y in range(y0, y1):
        t = (y - y0) / h
        c = lerp(c0, c1, t)
        a = int(alpha0 + (alpha1 - alpha0) * t)
        d.line([(0, y), (W, y)], fill=(*c, a))


# ---------------------------------------------------------------- M03 空气
def paint_m03():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y_air_bot = int(V_AIR_BOT * H)
    vgrad(d, 0, int(H * 0.010), P["air_top"], P["air_mid"])
    vgrad(d, int(H * 0.010), y_air_bot, P["air_mid"], P["haze"])

    rng = random.Random(31)
    # 3 组不等大的远树大形，压在空气下缘
    masses = [
        (0.00, 0.26, 0.030, 0.020),
        (0.20, 0.46, 0.026, 0.026),
        (0.42, 0.62, 0.020, 0.016),
        (0.58, 0.86, 0.024, 0.022),
    ]
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for x0, x1, h, top in masses:
        pts = []
        n = 26
        for i in range(n + 1):
            u = x0 + (x1 - x0) * i / n
            yy = (V_AIR_BOT - top) * H + math.sin(i * 0.9 + x0 * 10) * h * H * 0.16
            pts.append((u * W, yy))
        pts += [(x1 * W, V_AIR_BOT * H), (x0 * W, V_AIR_BOT * H)]
        ld.polygon(pts, fill=(*P["fartree"], 210))
    layer = layer.filter(ImageFilter.GaussianBlur(7))
    im.alpha_composite(layer)

    # 低频明暗，避免平涂
    noise = Image.new("L", (48, 27))
    noise.putdata([128 + rng.randint(-10, 10) for _ in range(48 * 27)])
    noise = noise.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(18))
    tint = Image.new("RGBA", (W, H), (255, 240, 220, 0))
    tint.putalpha(noise.point(lambda v: max(0, (v - 128)) // 5))
    im.alpha_composite(tint)

    # 下缘渐隐，压进对岸
    fade = Image.new("L", (W, H), 255)
    fd = ImageDraw.Draw(fade)
    y0, y1 = int(H * 0.018), int(V_AIR_BOT * H)
    for y in range(y0, y1):
        fd.line([(0, y), (W, y)], fill=int(255 * (1 - (y - y0) / max(1, y1 - y0)) ** 1.1))
    im.putalpha(Image.composite(im.split()[3], Image.new("L", (W, H), 0), fade))
    return im


# ---------------------------------------------------------------- M02 对岸
def paint_m02():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rng = random.Random(77)

    # 主体：上缘起伏（不让成一条直线），下缘压进水面
    n = 140
    top = []
    for i in range(n + 1):
        u = i / n
        y = (V_BANK_TOP * H
             + math.sin(i * 0.24) * H * 0.0035
             + math.sin(i * 0.87 + 1.3) * H * 0.0022
             + rng.uniform(-1.6, 1.6))
        top.append((u * W, y))
    poly = top + [(W, V_BANK_BOT * H), (0, V_BANK_BOT * H)]
    d.polygon(poly, fill=(*P["bank_top"], 255))
    vgrad(d, int(V_BANK_TOP * H), int(V_BANK_BOT * H), P["bank_top"], P["bank_low"])

    # 遮罩：保持上缘形状
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon(poly, fill=255)

    # 大块：3–5 个宽窄不同的暗草影，先破条带
    mass = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(mass)
    blocks = [(0.00, 0.18, 0.026, 0.060), (0.15, 0.42, 0.030, 0.064),
              (0.40, 0.55, 0.024, 0.058), (0.55, 0.80, 0.028, 0.062),
              (0.78, 1.00, 0.022, 0.058)]
    for x0, x1, y0, y1 in blocks:
        col = lerp(P["bank_mid"], P["bank_dark"], rng.uniform(0.2, 0.7))
        md.polygon([(x0 * W + rng.uniform(-20, 20), y0 * H),
                    (x1 * W + rng.uniform(-20, 20), y0 * H + rng.uniform(-8, 8)),
                    (x1 * W + rng.uniform(-30, 30), y1 * H),
                    (x0 * W + rng.uniform(-30, 30), y1 * H)], fill=(*col, rng.randint(70, 120)))
    mass = mass.filter(ImageFilter.GaussianBlur(22))
    im.alpha_composite(Image.composite(mass, Image.new("RGBA", (W, H), (0, 0, 0, 0)), mask))

    # 草丛：不等大、成组，贴在上缘
    tufts = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(tufts)
    x = -30.0
    while x < W + 30:
        gw = rng.uniform(40, 130)
        gh = rng.uniform(4, 12)
        col = lerp(P["bank_dark"], P["reed"], rng.uniform(0.1, 0.6))
        td.ellipse([x, V_BANK_TOP * H - gh, x + gw, V_BANK_TOP * H + 10],
                   fill=(*col, rng.randint(90, 150)))
        x += gw * rng.uniform(0.4, 0.9) + rng.uniform(6, 46)
    tufts = tufts.filter(ImageFilter.GaussianBlur(6))
    im.alpha_composite(Image.composite(tufts, Image.new("RGBA", (W, H), (0, 0, 0, 0)), mask))

    # 细笔触：短竖草，密度向下递减
    strokes = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(strokes)
    for _ in range(5200):
        u = rng.uniform(0, 1)
        v = rng.uniform(V_BANK_TOP + 0.002, V_BANK_BOT - 0.002)
        x0, y0 = u * W, v * H
        hh = rng.uniform(2, 6)
        col = P["reed"] if rng.random() < 0.5 else P["bank_dark"]
        sd.line([(x0, y0), (x0 + rng.uniform(-1.4, 1.4), y0 - hh)],
                fill=(*col, rng.randint(30, 85)), width=1)
    im.alpha_composite(Image.composite(strokes, Image.new("RGBA", (W, H), (0, 0, 0, 0)), mask))

    # 与水接触：下缘压一条暗湿带
    edge = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(edge).rectangle([0, int((V_BANK_BOT - 0.008) * H), W, int(V_BANK_BOT * H)],
                                   fill=(*P["water_edge"], 190))
    im.alpha_composite(edge.filter(ImageFilter.GaussianBlur(6)))

    # 下缘渐隐，接水面
    fade = Image.new("L", (W, H), 255)
    fd = ImageDraw.Draw(fade)
    y0, y1 = int((V_BANK_BOT - 0.006) * H), int((V_BANK_BOT + 0.004) * H)
    for y in range(y0, min(H, y1)):
        fd.line([(0, y), (W, y)], fill=int(255 * (1 - (y - y0) / max(1, y1 - y0))))
    im.putalpha(Image.composite(im.split()[3], Image.new("L", (W, H), 0), fade))

    im.putalpha(im.split()[3].filter(ImageFilter.GaussianBlur(1.2)))
    return im


for name, fn in (("M03_air.png", paint_m03), ("M02_bank.png", paint_m02)):
    img = fn()
    img.save(os.path.join(SRC, name))
    print("saved", name, img.size)

json.dump({"bands": {"bank_top": V_BANK_TOP, "bank_bot": V_BANK_BOT,
                     "air_bot": V_AIR_BOT, "water_top": V_WATER_TOP},
           "canvas": [W, H],
           "palette": {k: list(v) for k, v in P.items()},
           "note": "带位置由 G1_SHORE_PROJECTION.json 反算；M02 下缘 0.136 与水面 0.126 重叠 0.010。"},
          open(os.path.join(SRC, "BANDS.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("paint done")
