# -*- coding: utf-8 -*-
"""G3b：用系统 Python + PIL 生成细节板（Blender 自带 Python 无 PIL）。"""
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.dirname(HERE)
REN = os.path.join(CAND, "renders")

src = os.path.join(REN, "final.png")
im = Image.open(src)
W, H = im.size
crops = [
    ("d1_left_tree", (0.00, 0.00, 0.34, 0.42)),
    ("d2_center_rig", (0.30, 0.10, 0.66, 0.48)),
    ("d3_right_drum", (0.62, 0.05, 1.00, 0.46)),
    ("d4_stairs", (0.10, 0.42, 0.44, 0.86)),
    ("d5_paving", (0.34, 0.50, 0.78, 0.92)),
]
tiles = []
for name, (x0, y0, x1, y1) in crops:
    box = (int(W * x0), int(H * y0), int(W * x1), int(H * y1))
    c = im.crop(box)
    tw = int(W * 0.30)
    th = max(1, int(tw * c.height / c.width))
    tiles.append(c.resize((tw, th), Image.LANCZOS))

pad = 12
cw = max(t.width for t in tiles)
ch = max(t.height for t in tiles)
cols = 3
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (cols * cw + pad * (cols + 1), rows * ch + pad * (rows + 1)), (30, 28, 26))
for i, t in enumerate(tiles):
    r, c = divmod(i, cols)
    sheet.paste(t, (pad + c * (cw + pad), pad + r * (ch + pad)))
out = os.path.join(REN, "details.png")
sheet.save(out)
print("DETAILS", out, sheet.size)
