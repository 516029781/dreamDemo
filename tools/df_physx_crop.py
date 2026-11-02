"""TIMEPX01 -> 指定世界坐标范围的放大俯视图。

用途：把核心建筑群或某条通道单独放大，看清庭院、水池、连廊的位置关系。
只读碰撞面做投影，不生成可分发资产。

用法：
    python tools/df_physx_crop.py <bin> <x0> <y0> <x1> <y1> <out.png> [width] [title]
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from df_physx_parse import parse, quat_mat  # noqa: E402


def sample_points(tri):
    a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
    mid = np.stack([(a + b) * 0.5, (b + c) * 0.5, (c + a) * 0.5], axis=1)
    cen = ((a + b + c) / 3.0)[:, None, :]
    return np.concatenate([tri, mid, cen], axis=1)


def render(src, box, width=1400):
    x0, y0, x1, y1 = box
    d = parse(src)
    hulls, hull_of = d["hulls"], d["hull_of"]
    quat, pos, scl = d["quat"], d["pos"], d["scl"]
    pos_m = pos / 100.0

    W = width
    H = int(round(W * (y1 - y0) / (x1 - x0)))
    sx = (W - 1) / (x1 - x0)
    sy = (H - 1) / (y1 - y0)

    zbuf = np.full(H * W, -1e9, np.float32)
    cnt = np.zeros(H * W, np.float32)

    by_hull = {}
    for i, h in enumerate(hull_of):
        by_hull.setdefault(int(h), []).append(i)

    for hi_, inst_list in by_hull.items():
        verts, idx = hulls[hi_]
        if idx.size == 0:
            continue
        inst = np.asarray(inst_list)
        pts0 = sample_points((verts[idx] / 100.0).astype(np.float32))
        B = max(1, int(3_000_000 // max(1, pts0.shape[0])))
        for s in range(0, len(inst), B):
            blk = inst[s:s + B]
            R = np.stack([quat_mat(q) for q in quat[blk]])
            v = pts0[None] * scl[blk][:, None, None, :]
            w = np.matmul(v, np.transpose(R, (0, 2, 1))[:, None, :, :])
            w += pos_m[blk][:, None, None, :]
            x = w[..., 0].ravel()
            y = w[..., 1].ravel()
            z = w[..., 2].ravel()
            px = (x - x0) * sx
            py = (1.0 - (y - y0) / (y1 - y0)) * (H - 1)
            ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)
            if not ok.any():
                continue
            fi = (np.clip(py[ok], 0, H - 1).astype(np.int32) * W
                  + np.clip(px[ok], 0, W - 1).astype(np.int32))
            np.maximum.at(zbuf, fi, z[ok])
            np.add.at(cnt, fi, 1.0)

    return zbuf.reshape(H, W), cnt.reshape(H, W), (W, H)


def colorize(zbuf, cnt):
    mask = zbuf > -1e8
    z = np.where(mask, zbuf, np.nan)
    zs = z[mask]
    if zs.size == 0:
        return Image.new("RGB", (10, 10))
    p2, p98 = np.percentile(zs, [2, 98])

    dens = np.log1p(cnt)
    dmax = np.percentile(dens[dens > 0], 97)
    dn = np.clip(dens / max(1e-6, dmax), 0, 1)

    img_d = Image.fromarray((dn * 255).astype(np.uint8))
    img_d = img_d.filter(ImageFilter.MedianFilter(3))
    dn = np.asarray(img_d, np.float32) / 255.0

    t = np.clip((z - p2) / max(1e-6, p98 - p2), 0, 1)
    t = np.nan_to_num(t, nan=0.0)
    c0 = np.array([26, 46, 74], np.float32)
    c1 = np.array([60, 118, 154], np.float32)
    c2 = np.array([124, 178, 192], np.float32)
    c3 = np.array([255, 238, 200], np.float32)
    t3 = t[..., None]
    col = np.where(t3 < 0.35, c0 + (c1 - c0) * (t3 / 0.35),
          np.where(t3 < 0.72, c1 + (c2 - c1) * ((t3 - 0.35) / 0.37),
                              c2 + (c3 - c2) * ((t3 - 0.72) / 0.28)))

    lum = (0.16 + 0.84 * dn ** 0.62)[..., None]
    bg = np.array([10, 12, 18], np.float32)
    col = bg + (col - bg) * lum
    col = np.where(mask[..., None], col, bg)

    img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB")
    b = np.asarray(img.filter(ImageFilter.GaussianBlur(2.4)), np.float32)
    a = np.asarray(img, np.float32)
    return Image.fromarray(np.clip(a * 1.06 + b * 0.30, 0, 255).astype(np.uint8))


def decorate(img, box, out, title, subtitle, grid=50):
    W, H = img.size
    top = 84
    canvas = Image.new("RGB", (W, H + top + 46), (9, 11, 16))
    canvas.paste(img, (0, top))
    dr = ImageDraw.Draw(canvas)

    def font(sz, bold=False):
        for p in ("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
                  "C:/Windows/Fonts/simhei.ttf"):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                continue
        return ImageFont.load_default()

    dr.text((28, 16), title, fill=(232, 240, 244), font=font(28, True))
    dr.text((28, 54), subtitle, fill=(122, 146, 160), font=font(15))

    x0, y0, x1, y1 = box

    def px_of(wx):
        return (wx - x0) * (W - 1) / (x1 - x0)

    def py_of(wy):
        return (1.0 - (wy - y0) / (y1 - y0)) * (H - 1)

    step = grid
    for wx in range(int(x0 // step) * step, int(x1) + step, step):
        X = px_of(wx)
        if not (0 <= X < W):
            continue
        dr.line([(X, top), (X, top + H)], fill=(34, 44, 58), width=1)
        dr.text((X + 3, top + 4), f"{wx}", fill=(98, 118, 134), font=font(12))
    for wy in range(int(y0 // step) * step, int(y1) + step, step):
        Y = py_of(wy)
        if not (0 <= Y < H):
            continue
        dr.line([(0, top + Y), (W, top + Y)], fill=(34, 44, 58), width=1)
        dr.text((4, top + Y + 2), f"{wy}", fill=(98, 118, 134), font=font(12))

    bar_m = 50
    bar_px = bar_m * (W - 1) / (x1 - x0)
    bx, by = 28, H + top + 24
    dr.line([(bx, by), (bx + bar_px, by)], fill=(210, 226, 232), width=3)
    for xx in (bx, bx + bar_px):
        dr.line([(xx, by - 6), (xx, by + 6)], fill=(210, 226, 232), width=3)
    dr.text((bx + bar_px + 10, by - 9), f"{bar_m} m", fill=(190, 208, 216), font=font(14))
    dr.text((W - 300, by - 9), f"{x1-x0:.0f} × {y1-y0:.0f} m", fill=(120, 142, 156), font=font(14))
    canvas.save(out)
    print("saved", out, canvas.size)


if __name__ == "__main__":
    src = sys.argv[1]
    box = tuple(float(a) for a in sys.argv[2:6])
    out = sys.argv[6]
    width = int(sys.argv[7]) if len(sys.argv) > 7 else 1400
    title = sys.argv[8] if len(sys.argv) > 8 else "航天基地 · 局部放大"
    zb, cnt, meta = render(src, box, width)
    img = colorize(zb, cnt)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    decorate(img, box, out, title,
             "source: QH190311/delta-force-3d-map / Physx/hangtianjidi.bin ｜ PhysX 碰撞几何 ｜ 仅供内部参考")
