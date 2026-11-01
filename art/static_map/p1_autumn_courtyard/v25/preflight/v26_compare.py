"""V26 Step3: before/after comparison images.
Usage: python v26_compare.py
Produces:
  renders/v26_compare_full.png   (before | after, full frame)
  renders/v26_compare_tree.png   (tree region crop)
  renders/v26_compare_grass.png  (ground/pool region crop)
"""
from PIL import Image, ImageDraw
import os

R = os.path.dirname(os.path.abspath(__file__))
V25 = os.path.dirname(R)
RD = os.path.join(V25, "renders")
before_path = os.path.join(RD, "final.png")       # v25 艺术修复轮终图
after_path = os.path.join(RD, "final_v26.png")    # v26 植被回滚
assert os.path.exists(after_path), "final_v26.png not ready"

before = Image.open(before_path).convert("RGB")
after = Image.open(after_path).convert("RGB")
w, h = before.size
if after.size != before.size:
    after = after.resize(before.size)

def label(img, text):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 260, 40], fill=(0, 0, 0))
    d.text((10, 8), text, fill=(255, 255, 255))
    return img

def side(a, b, out):
    canvas = Image.new("RGB", (a.width * 2 + 8, a.height), (30, 30, 30))
    canvas.paste(a, (0, 0))
    canvas.paste(b, (a.width + 8, 0))
    canvas.save(out)
    print("saved", out, canvas.size)

# full
side(label(before.copy(), "BEFORE v25 (R1-R8)"), label(after.copy(), "AFTER v26 (veg rollback)"),
     os.path.join(RD, "v26_compare_full.png"))

# tree region: old tree at (-9.2, 7.3) screen left-center-upper
# from r2_tree_zoom history, tree occupies roughly x 8-40%, y 8-55%
tc = (int(w*0.06), int(h*0.05), int(w*0.46), int(h*0.60))
side(label(before.crop(tc), "BEFORE tree"), label(after.crop(tc), "AFTER tree"),
     os.path.join(RD, "v26_compare_tree.png"))

# ground/grass region: lower half center-left
gc = (int(w*0.10), int(h*0.52), int(w*0.75), int(h*0.98))
side(label(before.crop(gc), "BEFORE grass"), label(after.crop(gc), "AFTER grass"),
     os.path.join(RD, "v26_compare_grass.png"))

print("COMPARE_DONE")
