# -*- coding: utf-8 -*-
"""风格探针：在 v05 的 H1 单间（14 px/m）上预演三档画风，输出对照图。

用途：回答"参数化上色能到哪一步"，为 SPACE_BASE_ONESHOT_PLAN 的 I2/I3 定档提供依据。
输入：art/static_map/space_base_minigame/v05/renders/core_raw.png（CameraCore，14 px/m）
输出：planning/art/SPACE_BASE_CAPABILITY_20261103.png
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "art/static_map/space_base_minigame/v05/renders/core_raw.png")
OUT = os.path.join(ROOT, "planning/art/SPACE_BASE_CAPABILITY_20261103.png")
PANEL_DIR = os.path.join(ROOT, "planning/art")

# CameraCore: 2072x1876, ortho 148 m → 14 px/m, centre (120, 67)
def w2p(x, y):
    return 1036 + (x - 120) * 14, 938 - (y - 67) * 14


src = Image.open(SRC).convert("RGB")
x0, y0 = w2p(60, 60)
x1, y1 = w2p(120, 0)
A = src.crop((int(x0), int(y0), int(x1), int(y1)))
base = np.asarray(A, dtype=np.float32) / 255.0
H, W = base.shape[:2]


def lum(a):
    return a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722


def lowfreq(seed, cell=18):
    rng = np.random.default_rng(seed)
    g = rng.random((H // cell + 2, W // cell + 2)).astype(np.float32)
    return np.asarray(
        Image.fromarray((g * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC),
        dtype=np.float32) / 255


def s_curve(a, k=0.10):
    return np.clip(a + k * np.sin((a - 0.5) * math.pi) * 0.5, 0, 1)


def paint(a, amp, cell, seed=5):
    n = lowfreq(seed, cell) - 0.5
    fine = np.asarray(
        Image.fromarray((lowfreq(seed + 1, 3) * 255).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(0.8)), dtype=np.float32) / 255 - 0.5
    return np.clip(a * (1 + amp * 2 * n + amp * 0.4 * fine)[..., None], 0, 1)


def shadow_cool(a, s):
    m = np.clip((0.55 - lum(a)) / 0.55, 0, 1) * s
    tint = np.array([0.95, 0.985, 1.06], dtype=np.float32)
    return np.clip(a * (1 - m[..., None]) + a * tint * m[..., None], 0, 1)


def quant(a, lv):
    q = np.floor(a * lv + 0.5) / lv
    return np.clip(a * 0.84 + q * 0.16, 0, 1)


def ink_edge(a, thr, amt, ink=(0.22, 0.21, 0.19)):
    L = lum(a)
    g = np.asarray(Image.fromarray((L * 255).astype(np.uint8)).filter(ImageFilter.FIND_EDGES),
                   dtype=np.float32)
    g = np.asarray(Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(0.6)), dtype=np.float32)
    m = (g > thr).astype(np.float32)
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(
        ImageFilter.MaxFilter(3)), dtype=np.float32) / 255
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(0.8)), dtype=np.float32) / 255
    return np.clip(a * (1 - m[..., None] * amt)
                   + np.array(ink, dtype=np.float32) * m[..., None] * amt, 0, 1)


def paper(a, amt, seed=3):
    n = lowfreq(seed, 40)[..., None]
    r = np.where(n < 0.5, 2 * a * n, 1 - 2 * (1 - a) * (1 - n))
    return np.clip(a * (1 - amt) + r * amt, 0, 1)


def grain(a, s, seed=7):
    rng = np.random.default_rng(seed)
    return np.clip(a + rng.normal(0, s, a.shape).astype(np.float32), 0, 1)


def vignette(a, k):
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    return np.clip(a * np.clip(1 - k * np.clip(r - 0.55, 0, None) ** 1.5, 0.55, 1)[..., None], 0, 1)


def build(mild=True):
    a = s_curve(base, 0.10 if mild else 0.13)
    a = paint(a, 0.085 if mild else 0.115, 20 if mild else 14)
    a = shadow_cool(a, 0.55 if mild else 0.68)
    a = quant(a, 6 if mild else 5)
    a = ink_edge(a, 28 if mild else 25, 0.32 if mild else 0.42)
    a = paper(a, 0.05 if mild else 0.06)
    a = grain(a, (1.5 if mild else 1.8) / 255)
    return vignette(a, 0.10 if mild else 0.13)


def to_img(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


B = to_img(build(True))
C = to_img(build(False))
B.save(os.path.join(PANEL_DIR, "_preview2_p1.png"))
C.save(os.path.join(PANEL_DIR, "_preview2_p2.png"))

PAD, TOP, BOT = 30, 186, 104
Wc, Hc = PAD * 4 + A.width * 3, TOP + A.height + BOT
canvas = Image.new("RGB", (Wc, Hc), (16, 20, 24))
dr = ImageDraw.Draw(canvas)
fT = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 32)
fL = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 21)
fS = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 16)
dr.text((PAD, 24), "同一块区域（离心 H1，60×60 m，14 px/m）：画风能到哪一步", font=fT, fill=(238, 242, 236))
dr.text((PAD, 70), "2D 预演，只演示\"上色 / 边线 / 纸纹\"这一层；正式版还会叠加 3D 改动（总裁盒开顶、屋顶桁架投影、水面出画、手绘标注层）",
        font=fS, fill=(150, 168, 170))
labels = [("A · 现状（v05）", "纯渲染：明暗连续、阴影发灰、没有笔触", (152, 162, 166)),
          ("B · 温和上色（可达 · 1–2 天）", "6 级色阶 + 阴影偏冷 + 手绘边线 + 纸纹颗粒", (190, 214, 204)),
          ("C · 强化上色（上限 · 4–6 天含贴图）", "5 级色阶 + 更粗笔触 + 更硬边线 + 更强纸感", (228, 202, 152))]
for i, (img, (lab, sub, col)) in enumerate(zip([A, B, C], labels)):
    x = PAD + i * (A.width + PAD)
    canvas.paste(img, (x, TOP))
    dr.rectangle([x - 1, TOP - 1, x + A.width, TOP + A.height], outline=(58, 66, 70))
    dr.text((x, TOP - 58), lab, font=fL, fill=col)
    dr.text((x, TOP - 30), sub, font=fS, fill=(138, 156, 158))
dr.text((PAD, Hc - 70),
        "A→B：靠参数化上色，能拿到\"有手绘感的俯视渲染\"，1–2 天、包体几乎不涨。B→C：要真正像手绘插画，必须加手绘贴图与更粗笔触，4–6 天、+9–14 MB。",
        font=fS, fill=(216, 222, 214))
dr.text((PAD, Hc - 40),
        "关键：这些差异在 14 px/m 清楚可见；缩到主图 7 px/m 后 B 只剩一半，C 靠边线与色块还能保住 —— 所以主图先做\"边线+色块\"，细节留给核心区高清片。",
        font=fS, fill=(150, 168, 170))
canvas.save(OUT)
print("STYLE_PROBE_OK", canvas.size)
