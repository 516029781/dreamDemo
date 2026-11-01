"""V27B2: build one full-canopy hand-painted texture (cloud silhouette + clusters + shadow pockets)."""
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import math, random, os

random.seed(404)
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "handpainted")
GOLD = (217, 164, 65); AMBER = (176, 114, 46); OCHRE = (122, 74, 34); BROWN = (74, 46, 24)

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def ramp(u):
    u = max(0.0, min(1.0, u))
    if u < 0.33: return lerp(BROWN, OCHRE, u / 0.33)
    if u < 0.7: return lerp(OCHRE, AMBER, (u - 0.33) / 0.37)
    return lerp(AMBER, GOLD, (u - 0.7) / 0.3)

S = 1024
# --- cloud silhouette mask: big blobs forming rounded canopy ---
mask = Image.new("L", (S, S), 0)
md = ImageDraw.Draw(mask)
rnd = random.Random(11)
# overall canopy outline (slightly wider than tall, flat-ish bottom)
for _ in range(16):
    cx = rnd.randint(int(S*0.28), int(S*0.72))
    cy = rnd.randint(int(S*0.25), int(S*0.62))
    r = rnd.randint(150, 240)
    md.ellipse([cx-r, cy-r*0.8, cx+r, cy+r*0.8], fill=255)
# flatten bottom
md.rectangle([int(S*0.12), int(S*0.66), int(S*0.88), S], fill=0)
mask = mask.filter(ImageFilter.GaussianBlur(18))

# --- internal cluster dabs ---
clus_a = Image.new("L", (S, S), 0)
clus_rgb = Image.new("RGB", (S, S), (0, 0, 0))
ca = ImageDraw.Draw(clus_a)
cc = ImageDraw.Draw(clus_rgb)
for _ in range(430):
    x = rnd.randint(int(S*0.1), int(S*0.9))
    y = rnd.randint(int(S*0.12), int(S*0.78))
    if mask.getpixel((x, y)) < 100:
        continue
    dab = rnd.randint(30, 85)
    u = (x + (S - y)) / (2 * S) + rnd.uniform(-0.22, 0.22)
    pocket = rnd.random() < 0.26 and y > S * 0.42
    col = lerp(BROWN, OCHRE, rnd.uniform(0, 0.5)) if pocket else ramp(u)
    a = rnd.randint(120, 255)
    tmp = Image.new("L", (S, S), 0)
    td = ImageDraw.Draw(tmp)
    td.ellipse([x-dab, y-dab*0.42, x+dab, y+dab*0.42], fill=a)
    tmp = tmp.rotate(rnd.uniform(-30, 30), center=(x, y))
    clus_a = Image.composite(Image.new("L", (S, S), 255), clus_a, tmp)
    solid = Image.new("RGB", (S, S), col)
    clus_rgb.paste(solid, (0, 0), tmp)
clus_a = clus_a.filter(ImageFilter.GaussianBlur(1.6))

# --- compose ---
base_dim = mask.point(lambda p: int(p * 0.9))
alpha = ImageChops.screen(base_dim, clus_a)
alpha = alpha.filter(ImageFilter.GaussianBlur(1.0))
alpha = alpha.point(lambda p: 0 if p < 60 else p)  # hard-ish clip floor

# gradient fill
grad = Image.new("RGB", (S, S))
gd = ImageDraw.Draw(grad)
shade = Image.new("L", (S, S))
sd = ImageDraw.Draw(shade)
for yy in range(S):
    v_frac = yy / S
    xx = 0
    while xx < S:
        u = (xx + (S - yy)) / (2 * S)
        gd.rectangle([xx, yy, xx+8, yy+1], fill=ramp(u))
        xx += 8
    sd.line([(0, yy), (S, yy)], fill=int(255 * (0.5 + 0.5 * (1 - v_frac))))
grad = grad.filter(ImageFilter.GaussianBlur(32))
grad = ImageChops.multiply(grad, Image.merge("RGB", (shade, shade, shade)))

clus_soft = clus_a.filter(ImageFilter.GaussianBlur(3.5))
out_rgb = Image.composite(clus_rgb, grad, clus_soft.point(lambda p: min(255, int(p * 2.2))))
noise = Image.effect_noise((S, S), 12).convert("L")
out_rgb = ImageChops.add(out_rgb, Image.merge("RGB", (noise, noise, noise)), scale=1, offset=-6)
out = out_rgb.convert("RGBA")
out.putalpha(alpha)
out.save(os.path.join(OUT, "canopy_full.png"))

# preview
pv = Image.new("RGB", (S, S), (90, 90, 95))
pv.paste(out, (0, 0), out)
pv.save(os.path.join(OUT, "canopy_full_preview.png"))
print("CANOPY_FULL_DONE")
