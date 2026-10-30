"""Procedural leaf-card atlas: 4 shapes x 2 tones, alpha + tip-to-base gradient.

Native raster source, no generative imagery: each cell is drawn from analytic
shapes (cluster of overlapping leaf ellipses) with per-pixel shading, then the
whole sheet is written as RGBA PNG. Cells are 128x128 in a 512x256 sheet.
"""
import math
import os
import random

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(ROOT, "demo_n5/assets/resources/textures/tex_leaf_atlas")
OUT = os.path.join(OUT_DIR, "texture.png")

CELL = 128
COLS, ROWS = 4, 2
TONE_TOP = [(196, 130, 74), (176, 112, 62), (168, 120, 70), (188, 126, 72)]
TONE_BASE = [(92, 52, 30), (84, 48, 28), (78, 50, 30), (88, 52, 30)]


def leaf_shape(draw, cx, cy, rx, ry, angle, fill):
    pts = []
    for i in range(24):
        t = i / 24.0 * math.tau
        # pointed ellipse: narrow at the two ends
        k = 1.0 - 0.65 * abs(math.sin(t))
        x = rx * math.cos(t) * k
        y = ry * math.sin(t)
        xr = x * math.cos(angle) - y * math.sin(angle)
        yr = x * math.sin(angle) + y * math.cos(angle)
        pts.append((cx + xr, cy + yr))
    draw.polygon(pts, fill=fill)


def make_cell(seed, tone_top, tone_base):
    rng = random.Random(seed)
    cell = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    d = ImageDraw.Draw(cell)
    # 5-7 overlapping leaves fanning upward from the base
    for i in range(rng.randint(5, 7)):
        cx = CELL * 0.5 + rng.uniform(-26, 26)
        cy = CELL * 0.55 + rng.uniform(-18, 18)
        rx = rng.uniform(20, 30)
        ry = rng.uniform(34, 50)
        ang = math.radians(rng.uniform(-38, 38))
        leaf_shape(d, cx, cy, rx, ry, ang, (120, 74, 44, 255))
    # shade: vertical gradient multiplied into the alpha shape
    px = cell.load()
    for y in range(CELL):
        t = y / (CELL - 1.0)
        col = [int(tone_top[k] * (1 - t) + tone_base[k] * t) for k in range(3)]
        for x in range(CELL):
            r, g, b, a = px[x, y]
            if a:
                # slight lateral variation so the card is not a flat band
                lat = 0.92 + 0.16 * abs(x / (CELL - 1.0) - 0.5)
                px[x, y] = (min(255, int(col[0] * lat)), min(255, int(col[1] * lat)),
                            min(255, int(col[2] * lat)), a)
    return cell


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    sheet = Image.new("RGBA", (CELL * COLS, CELL * ROWS), (0, 0, 0, 0))
    for row in range(ROWS):
        for col in range(COLS):
            cell = make_cell(20261027 + row * 17 + col * 5,
                             TONE_TOP[col], TONE_BASE[col])
            sheet.paste(cell, (col * CELL, row * CELL))
    sheet.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
