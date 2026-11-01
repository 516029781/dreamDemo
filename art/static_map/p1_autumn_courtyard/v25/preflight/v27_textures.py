"""V27A: generate hand-painted foliage alpha textures with PIL.
Outputs (to v25/assets/handpainted/):
  leaf_cluster_a.png / leaf_cluster_b.png  1024x1024 RGBA canopy masses
  grass_tuft.png                            1024x1024 RGBA grass tuft card
  preview_hp.png                            side-by-side preview on grey bg
Palette anchors sampled from reference t084s:
  bright gold #D9A441 / amber #B0722E / ochre #7A4A22 / deep brown #4A2E18
"""
from PIL import Image, ImageDraw, ImageFilter
import math, random, os

random.seed(27)
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "handpainted")

GOLD = (217, 164, 65)
AMBER = (176, 114, 46)
OCHRE = (122, 74, 34)
BROWN = (74, 46, 24)

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def ramp_color(u, v=None):
    """u in [0,1] along gradient: 0=deep brown (shade) .. 1=bright gold (lit).
    v adds midtone variation."""
    if u < 0.33:
        return lerp(BROWN, OCHRE, u / 0.33)
    if u < 0.7:
        return lerp(OCHRE, AMBER, (u - 0.33) / 0.37)
    return lerp(AMBER, GOLD, (u - 0.7) / 0.3)

def build_leaf_cluster(seed, fname):
    rnd = random.Random(seed)
    S = 1024
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

    # --- base blob mask via soft ellipses ---
    base = Image.new("L", (S, S), 0)
    bd = ImageDraw.Draw(base)
    blobs = []
    n_blobs = rnd.randint(9, 12)
    for _ in range(n_blobs):
        cx = rnd.randint(int(S * 0.22), int(S * 0.78))
        cy = rnd.randint(int(S * 0.22), int(S * 0.78))
        r = rnd.randint(150, 260)
        blobs.append((cx, cy, r))
        bd.ellipse([cx - r, cy - r * 0.85, cx + r, cy + r * 0.85], fill=255)
    base = base.filter(ImageFilter.GaussianBlur(24))

    # --- cluster dabs layer (both color and alpha detail) ---
    clus_a = Image.new("L", (S, S), 0)
    clus_rgb = Image.new("RGB", (S, S), (0, 0, 0))
    cd_a = ImageDraw.Draw(clus_a)
    cd_c = ImageDraw.Draw(clus_rgb)
    # light from top-right: u = (x + (S - y)) / (2S)
    for cx, cy, r in blobs:
        n_dabs = rnd.randint(26, 34)
        for _ in range(n_dabs):
            ang = rnd.uniform(0, math.tau)
            rr = r * rnd.uniform(0.15, 1.02)
            x = cx + math.cos(ang) * rr
            y = cy + math.sin(ang) * rr * 0.8
            dab = rnd.randint(34, 74)
            rot = rnd.uniform(-0.5, 0.5)
            u = min(1.0, max(0.0, (x + (S - y)) / (2 * S) + rnd.uniform(-0.25, 0.25)))
            # shadow pockets: between-blob dabs go dark
            pocket = rnd.random() < 0.22 and rr > r * 0.35
            if pocket:
                col = lerp(BROWN, OCHRE, rnd.uniform(0, 0.5))
            else:
                col = ramp_color(u)
            # dab alpha: interior solid, edge dabs thinner
            edge = rr > r * 0.85
            a = rnd.randint(140, 255) if not edge else rnd.randint(90, 200)
            # leaf-shaped dab: 2 overlapping ellipses rotated
            tmp = Image.new("L", (S, S), 0)
            td = ImageDraw.Draw(tmp)
            td.ellipse([x - dab, y - dab * 0.42, x + dab, y + dab * 0.42], fill=a)
            tmp = tmp.rotate(math.degrees(rot), center=(x, y))
            clus_a = Image.composite(Image.new("L", (S, S), 255), clus_a, tmp)
            # paint color where dab
            solid = Image.new("RGB", (S, S), col)
            clus_rgb.paste(solid, (0, 0), tmp)
    clus_a = clus_a.filter(ImageFilter.GaussianBlur(2))

    # --- compose: alpha = base*0.75 + clus; color from clus with blob shading ---
    # --- compose without numpy ---
    from PIL import ImageChops
    # alpha = screen(base*0.82, clus)
    base_dim = base.point(lambda p: int(p * 0.82))
    alpha = ImageChops.screen(base_dim, clus_a)

    # fill gradient: bright top-right -> dark bottom-left, per-pixel ramp
    grad = Image.new("RGB", (S, S))
    gd = ImageDraw.Draw(grad)
    shade = Image.new("L", (S, S))
    sd = ImageDraw.Draw(shade)
    for yy in range(S):
        v_frac = yy / S
        for xx in range(0, S, 64):  # coarse horizontal bands (blurred later)
            u = (xx + (S - yy)) / (2 * S)
            col = ramp_color(min(1.0, max(0.0, u)))
            gd.rectangle([xx, yy, xx + 64, yy + 1], fill=col)
        sd.line([(0, yy), (S, yy)], fill=int(255 * (0.55 + 0.45 * (1 - v_frac))))
    grad = grad.filter(ImageFilter.GaussianBlur(48))
    grad = ImageChops.multiply(grad, Image.merge("RGB", (shade, shade, shade)))

    # where clus painted use clus color else gradient fill
    clus_soft = clus_a.filter(ImageFilter.GaussianBlur(6))
    out_rgb = Image.composite(clus_rgb, grad, clus_soft.point(lambda p: min(255, int(p * 2.2))))
    # slight painterly noise
    noise = Image.effect_noise((S, S), 14).convert("L")
    out_rgb = ImageChops.add(out_rgb, Image.merge("RGB", (noise, noise, noise)), scale=1, offset=-7)

    out = out_rgb.convert("RGBA")
    out.putalpha(alpha)
    out.save(os.path.join(OUT, fname))
    print("saved", fname)

def build_grass_tuft():
    S = 1024
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rnd = random.Random(7)
    cx = S // 2
    base_y = S - 40
    n_blades = 15
    for i in range(n_blades):
        lean = (i - n_blades // 2) * rnd.uniform(0.04, 0.075) + rnd.uniform(-0.03, 0.03)
        # blade as tapered curved strip along a quadratic bend
        length = rnd.uniform(S * 0.55, S * 0.92)
        w0 = rnd.uniform(44, 66)   # base width
        w1 = rnd.uniform(8, 18)    # tip width
        bend = rnd.uniform(0.15, 0.45) * (1 if lean >= 0 else -1)
        pts = []
        steps = 24
        for s in range(steps + 1):
            t = s / steps
            # position along curved spine
            x = cx + lean * length * t + bend * length * (t ** 2) * 0.9
            y = base_y - length * t
            pts.append((x, y, t))
        # build polygon strip
        left, right = [], []
        for x, y, t in pts:
            w = (w0 + (w1 - w0) * t) * 0.5
            left.append((x - w, y))
            right.append((x + w, y))
        poly = left + right[::-1]
        # color: root dark -> tip gold, with per-blade jitter
        u = rnd.uniform(0.45, 1.0)
        c_root = lerp(BROWN, OCHRE, rnd.uniform(0.2, 0.6))
        c_tip = ramp_color(u)
        blade = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        bd2 = ImageDraw.Draw(blade)
        bd2.polygon(poly, fill=(255, 255, 255, 235))
        # vertical gradient along blade
        grad = Image.new("L", (1, S), 0)
        for yy in range(S):
            t = 1 - yy / S  # 0 at bottom..1 at top? y grows downward
            grad.putpixel((0, yy), 0)
        # simpler: paint strips
        mask = blade.split()[3]
        solid = Image.new("RGB", (S, S), c_tip)
        # gradient overlay image
        g = Image.new("RGB", (S, S), c_root)
        gg = Image.new("L", (S, S), 0)
        gd = ImageDraw.Draw(gg)
        for yy in range(S):
            t = max(0.0, min(1.0, (base_y - yy) / length))
            gd.line([(0, yy), (S, yy)], fill=int(t * 255))
        solid = Image.composite(Image.new("RGB", (S, S), c_tip), g, gg)
        img.paste(solid, (0, 0), mask)
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    img.save(os.path.join(OUT, "grass_tuft.png"))
    print("saved grass_tuft.png")

build_leaf_cluster(27, "leaf_cluster_a.png")
build_leaf_cluster(91, "leaf_cluster_b.png")
build_grass_tuft()

# preview on grey
tiles = ["leaf_cluster_a.png", "leaf_cluster_b.png", "grass_tuft.png"]
prev = Image.new("RGB", (1024 * 3, 1024), (90, 90, 95))
for i, t in enumerate(tiles):
    im = Image.open(os.path.join(OUT, t)).convert("RGBA")
    prev.paste(im, (i * 1024, 0), im)
prev.save(os.path.join(OUT, "preview_hp.png"))
print("PREVIEW_DONE")
