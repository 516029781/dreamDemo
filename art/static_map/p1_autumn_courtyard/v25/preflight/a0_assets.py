"""F4 / F5 资产：程序化生成草卡、石板、落叶贴图（纯 PIL，无 numpy）。

规格来自 P1_BACKGROUND_OPTIMIZE_v24_1_PLAN.md §三 F4/F5：
  草：根 70-120 / 中段 150-200 / 尖 210-250，alpha 从根实到尖细
  石板：逐块 5-15 灰阶色差、接缝、裂缝、污渍
"""
import os
import random
from PIL import Image, ImageDraw, ImageFilter, ImageChops

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
os.makedirs(OUT, exist_ok=True)
SS = 4


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def make_grass(name, clusters, per_cluster, hmin, hmax, wid, seed,
               root, mid, tip, bend_max=0.34, W=512, H=256, wind=0.0):
    """簇生草：每簇从一个基部点发散，二次贝塞尔弯曲，根粗尖细。"""
    import math
    rnd = random.Random(seed)
    w, h = W * SS, H * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    for _c in range(clusters):
        cx = rnd.uniform(0.0, 1.0) * w
        cy = h - rnd.uniform(0.0, 0.045) * h
        wind_dir = wind + rnd.uniform(-0.35, 0.35)
        for _b in range(per_cluster):
            bx = cx + rnd.gauss(0, 0.012 * w)
            hgt = rnd.uniform(hmin, hmax) * h * rnd.choice([1.0, 1.0, 0.72, 0.55])
            lean = (wind_dir + rnd.uniform(-0.30, 0.30)) * hgt * 0.55
            bend = rnd.uniform(-1, 1) * bend_max * hgt * 0.42
            # 20% 的叶子更宽，做出"叶片"而不是"针"
            w0 = wid * SS * rnd.uniform(0.55, 1.25) * rnd.choice([1.0, 1.0, 1.0, 1.0, 2.1])
            a0 = rnd.randint(196, 255)
            # 二次贝塞尔 P0(根) P1(中) P2(尖)
            p0 = (bx, cy)
            p2 = (bx + lean, cy - hgt)
            p1 = (bx + lean * 0.35 + bend * 0.5, cy - hgt * 0.58)
            N = 22
            pts = []
            for k in range(N + 1):
                t = k / N
                u = 1 - t
                x = u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0]
                y = u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]
                pts.append((x, y))
            for k in range(N):
                t = k / N
                wdt = max(1, w0 * (1 - t) ** 0.55)
                c = lerp(root, mid, t / 0.42) if t < 0.42 else lerp(mid, tip, (t - 0.42) / 0.58)
                a = int(a0 * (1.0 if t < 0.78 else (1 - (t - 0.78) / 0.22 * 0.55)))
                d.line([pts[k], pts[k + 1]], fill=(*c, a), width=int(round(wdt)))

    img = img.resize((W, H), Image.LANCZOS)
    # 底部 8% 渐隐，避免草根被"切平"出现横条
    px = img.load()
    fade = int(H * 0.08)
    for y in range(H - fade, H):
        k = (H - y) / fade
        for x in range(W):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, int(a * k * k))
    img.save(os.path.join(OUT, name))
    print("grass", name, img.size)


def make_stone(name, W=2048, H=2048, tiles=6, seed=7):
    rnd = random.Random(seed)
    base = Image.new("RGB", (W, H), (198, 188, 170))
    d = ImageDraw.Draw(base)

    tw, th = W // tiles, H // tiles
    for iy in range(tiles):
        for ix in range(tiles):
            dv = rnd.uniform(-9, 9)
            tint = rnd.uniform(-3.5, 3.5)
            c = (int(198 + dv + tint), int(188 + dv), int(170 + dv - tint))
            d.rectangle([ix * tw, iy * th, (ix + 1) * tw, (iy + 1) * th], fill=c)

    # 低频斑驳：24x24 噪声放大，映射到 ±13
    small = Image.new("L", (24, 24))
    sp = small.load()
    for y in range(24):
        for x in range(24):
            sp[x, y] = rnd.randint(0, 255)
    mottle = small.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(max(W // 24 // 3, 2)))
    mottle = mottle.point(lambda v: int(v * 0.102))
    m3 = Image.merge("RGB", (mottle, mottle, mottle))
    base = ImageChops.add(base, m3, scale=1.0, offset=-13)

    # 高频颗粒
    grain = Image.effect_noise((W, H), 4.2).convert("RGB")
    base = ImageChops.add(base, grain, scale=1.0, offset=-128)

    # 接缝
    seam = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(seam)
    for ix in range(tiles + 1):
        x = int(ix * tw + rnd.uniform(-2, 2))
        sd.rectangle([max(0, x - 4), 0, min(W - 1, x + 4), H], fill=140)
        sd.rectangle([max(0, x - 7), 0, max(0, x - 4), H], fill=52)
        sd.rectangle([min(W - 1, x + 4), 0, min(W - 1, x + 7), H], fill=52)
    for iy in range(tiles + 1):
        y = int(iy * th + rnd.uniform(-2, 2))
        sd.rectangle([0, max(0, y - 4), W, min(H - 1, y + 4)], fill=140)
        sd.rectangle([0, max(0, y - 7), W, max(0, y - 4)], fill=52)
        sd.rectangle([0, min(H - 1, y + 4), W, min(H - 1, y + 7)], fill=52)
    dark = Image.new("RGB", (W, H), (60, 52, 42))
    base = Image.composite(Image.blend(base, dark, 0.55), base, seam.point(lambda v: int(v * 0.7)))

    # 污渍
    stain = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    st = ImageDraw.Draw(stain)
    for _ in range(26):
        cx, cy = rnd.randint(0, W), rnd.randint(0, H)
        rx, ry = rnd.randint(W // 22, W // 9), rnd.randint(H // 26, H // 12)
        st.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(96, 84, 66, rnd.randint(8, 22)))
    stain = stain.filter(ImageFilter.GaussianBlur(26))
    base = Image.alpha_composite(base.convert("RGBA"), stain)

    # 裂缝
    cr = ImageDraw.Draw(base)
    for _ in range(11):
        x, y = rnd.randint(0, W), rnd.randint(0, H)
        pts = [(x, y)]
        ang = rnd.uniform(0, 6.28)
        for _ in range(rnd.randint(14, 34)):
            ang += rnd.uniform(-0.55, 0.55)
            step = rnd.uniform(9, 22)
            x += __import__("math").cos(ang) * step
            y += __import__("math").sin(ang) * step
            pts.append((x, y))
        cr.line(pts, fill=(74, 64, 50, 255), width=rnd.randint(1, 3))
        cr.line([(p[0] + 1, p[1] + 1) for p in pts], fill=(150, 140, 122, 190), width=1)

    base.convert("RGB").save(os.path.join(OUT, name))
    print("stone", name, base.size)


def make_leaf(name, n=5, W=128, H=128, seed=11):
    rnd = random.Random(seed)
    img = Image.new("RGBA", (W * 4, H * 4), (0, 0, 0, 0))
    for _ in range(n):
        cx, cy = rnd.uniform(24, W * 4 - 24), rnd.uniform(24, H * 4 - 24)
        rx, ry = rnd.uniform(18, 34), rnd.uniform(9, 17)
        ang = rnd.uniform(0, 180)
        col = rnd.choice([(200, 122, 48), (176, 96, 40), (214, 150, 62), (150, 92, 44)])
        leaf = Image.new("RGBA", (int(rx * 2 + 10), int(ry * 2 + 10)), (0, 0, 0, 0))
        ld = ImageDraw.Draw(leaf)
        ld.ellipse([5, 5, 5 + rx * 2, 5 + ry * 2], fill=(*col, 255))
        leaf = leaf.rotate(ang, expand=True, resample=Image.BICUBIC)
        img.alpha_composite(leaf, (int(cx - leaf.width / 2), int(cy - leaf.height / 2)))
    img = img.resize((W, H), Image.LANCZOS)
    img.save(os.path.join(OUT, name))
    print("leaf", name, img.size)


if __name__ == "__main__":
    # 高疏剪影草：簇少、每簇多、长度差异大，能被光穿透
    make_grass("grass_tall.png", clusters=14, per_cluster=16, hmin=0.42, hmax=1.0,
               wid=3.4, seed=3, root=(70, 56, 38), mid=(172, 140, 96),
               tip=(246, 232, 200), bend_max=0.40, wind=0.10)
    # 密实矮草：簇多、矮、宽叶
    make_grass("grass_dense.png", clusters=26, per_cluster=14, hmin=0.26, hmax=0.72,
               wid=4.6, seed=9, root=(84, 66, 44), mid=(180, 148, 102),
               tip=(238, 220, 182), bend_max=0.22, wind=0.04)
    # 垂草：从桶沿往下垂，弯曲大
    make_grass("grass_drape.png", clusters=18, per_cluster=12, hmin=0.55, hmax=1.0,
               wid=2.8, seed=17, root=(78, 62, 42), mid=(168, 138, 96),
               tip=(248, 236, 208), bend_max=0.62, wind=0.22)
    make_stone("stone_floor.png")
    make_leaf("leaf.png")
