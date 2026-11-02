"""TIMEPX01 -> 俯视地图（密度 × 高程双通道着色）。

碰撞几何是薄壁 + 大面积平台板：
- 纯实心填充会被平台整块涂死，看不到内部
- 纯高度雾化又太暗
所以用两条通道：命中密度决定亮度与可见度，高程决定色相。
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


def accumulate(src, width=1600):
    d = parse(src)
    hulls, hull_of = d["hulls"], d["hull_of"]
    quat, pos, scl = d["quat"], d["pos"], d["scl"]
    pos_m = pos / 100.0

    # bbox（米）
    lo = np.array([1e18, 1e18])
    hi = np.array([-1e18, -1e18])
    by_hull = {}
    for i, h in enumerate(hull_of):
        by_hull.setdefault(int(h), []).append(i)
    for hi_, inst in by_hull.items():
        v = hulls[hi_][0] / 100.0
        ext = np.abs(v)[:, :2].max(0) * np.abs(scl[inst])[:, :2].max(0)
        lo = np.minimum(lo, pos_m[inst][:, :2].min(0) - ext)
        hi = np.maximum(hi, pos_m[inst][:, :2].max(0) + ext)
    lo -= 4
    hi += 4
    span = hi - lo
    W = width
    H = int(round(W * span[1] / span[0]))
    print(f"画布 {W}x{H}, 覆盖 {span[0]:.0f}x{span[1]:.0f} m")

    zbuf = np.full(H * W, -1e9, np.float32)
    cnt = np.zeros(H * W, np.float32)
    sx = (W - 1) / span[0]
    sy = (H - 1) / span[1]

    total = 0
    for hi_, inst_list in by_hull.items():
        verts, idx = hulls[hi_]
        if idx.size == 0:
            continue
        inst = np.asarray(inst_list)
        pts0 = sample_points((verts[idx] / 100.0).astype(np.float32))
        T = pts0.shape[0]
        total += T * len(inst)
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
            px = (x - lo[0]) * sx
            py = (1.0 - (y - lo[1]) / span[1]) * (H - 1)
            ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)
            if not ok.any():
                continue
            fi = (np.clip(py[ok], 0, H - 1).astype(np.int32) * W
                  + np.clip(px[ok], 0, W - 1).astype(np.int32))
            np.maximum.at(zbuf, fi, z[ok])
            np.add.at(cnt, fi, 1.0)
    print(f"三角面 {total:,}")
    return zbuf.reshape(H, W), cnt.reshape(H, W), (lo, hi, W, H)


def colorize(zbuf, cnt, meta):
    lo, hi, W, H = meta
    mask = zbuf > -1e8
    z = np.where(mask, zbuf, np.nan)

    zs = z[mask]
    p1, p99 = np.percentile(zs, [1, 99])
    print(f"高程 {zs.min():.1f}..{zs.max():.1f} m, 1-99% = {p1:.1f}..{p99:.1f}")

    # 密度 -> 亮度（对数压缩，抑制超大平台，突出小构件）
    dens = np.log1p(cnt)
    dmax = np.percentile(dens[dens > 0], 97)
    dn = np.clip(dens / max(1e-6, dmax), 0, 1)

    # 中值滤波压掉孤立噪点（高处零星碰撞体）
    img_d = Image.fromarray((dn * 255).astype(np.uint8))
    img_d = img_d.filter(ImageFilter.MedianFilter(3))
    dn = np.asarray(img_d, np.float32) / 255.0

    # 高程 -> 色相：低=深蓝，中=青，高=暖白
    t = np.clip((z - p1) / max(1e-6, p99 - p1), 0, 1)
    t = np.nan_to_num(t, nan=0.0)
    c0 = np.array([28, 48, 78], np.float32)     # 低：深蓝
    c1 = np.array([58, 116, 152], np.float32)   # 中低：靛青
    c2 = np.array([122, 176, 190], np.float32)  # 中高：青白
    c3 = np.array([255, 236, 196], np.float32)  # 高：暖白
    t3 = t[..., None]
    col = np.where(t3 < 0.35, c0 + (c1 - c0) * (t3 / 0.35),
          np.where(t3 < 0.72, c1 + (c2 - c1) * ((t3 - 0.35) / 0.37),
                              c2 + (c3 - c2) * ((t3 - 0.72) / 0.28)))

    # 密度做亮度：无几何处纯黑，密集处满色
    lum = (0.18 + 0.82 * dn ** 0.62)[..., None]
    bg = np.array([9, 11, 16], np.float32)
    col = bg + (col - bg) * lum
    col = np.where(mask[..., None], col, bg)

    arr = np.clip(col, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr, "RGB")

    # 晕光：让密集处发光，接近卫星/夜视质感
    b = np.asarray(img.filter(ImageFilter.GaussianBlur(3.0)), np.float32)
    a = np.asarray(img, np.float32)
    img = Image.fromarray(np.clip(a * 1.06 + b * 0.32, 0, 255).astype(np.uint8))
    return img


def decorate(img, meta, out, title, subtitle, note=""):
    lo, hi, W, H = meta
    top = 96
    canvas = Image.new("RGB", (W, H + top + 56), (9, 11, 16))
    canvas.paste(img, (0, top))
    dr = ImageDraw.Draw(canvas)

    def font(sz, bold=False):
        for p in ("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
                  "C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/arial.ttf"):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                continue
        return ImageFont.load_default()

    dr.text((30, 18), title, fill=(232, 240, 244), font=font(31, True))
    dr.text((30, 60), subtitle, fill=(122, 146, 160), font=font(16))

    # 网格：100 m 细线 + 200 m 主线带坐标标注
    def px_of(wx):
        return (wx - lo[0]) * (W - 1) / (hi[0] - lo[0])

    def py_of(wy):
        return (1.0 - (wy - lo[1]) / (hi[1] - lo[1])) * (H - 1)

    fx = 14
    for wx in range(int(lo[0] // 100) * 100, int(hi[0]) + 101, 100):
        X = px_of(wx)
        if not (0 <= X < W):
            continue
        major = (wx % 200 == 0)
        dr.line([(X, top), (X, top + H)],
                fill=(40, 52, 68) if major else (22, 28, 38), width=1)
        if major:
            dr.text((X + 3, top + H - 18), f"{wx}", fill=(96, 116, 132), font=font(fx))

    for wy in range(int(lo[1] // 100) * 100, int(hi[1]) + 101, 100):
        Y = py_of(wy)
        if not (0 <= Y < H):
            continue
        major = (wy % 200 == 0)
        dr.line([(0, top + Y), (W, top + Y)],
                fill=(40, 52, 68) if major else (22, 28, 38), width=1)
        if major:
            dr.text((4, top + Y - 16), f"{wy}", fill=(96, 116, 132), font=font(fx))

    # 比例尺
    bar_m = 200
    bar_px = bar_m * (W - 1) / (hi[0] - lo[0])
    x0, y0 = 30, H + top + 30
    dr.line([(x0, y0), (x0 + bar_px, y0)], fill=(210, 226, 232), width=3)
    for xx in (x0, x0 + bar_px):
        dr.line([(xx, y0 - 7), (xx, y0 + 7)], fill=(210, 226, 232), width=3)
    dr.text((x0 + bar_px / 2 - 28, y0 + 9), f"{bar_m} m", fill=(190, 208, 216), font=font(15))

    # 指北针：放在图内右上角，避让底部信息行
    cx, cy = W - 62, top + 56
    dr.ellipse([cx - 26, cy - 34, cx + 26, cy + 30], fill=(12, 16, 24))
    dr.polygon([(cx, cy - 26), (cx - 10, cy + 8), (cx, cy + 1), (cx + 10, cy + 8)],
               fill=(232, 240, 244))
    dr.text((cx - 5, cy + 10), "N", fill=(210, 226, 232), font=font(14, True))

    info = f"{hi[0]-lo[0]:.0f} × {hi[1]-lo[1]:.0f} m   |   {note}"
    tw = dr.textlength(info, font=font(15))
    dr.text((W - tw - 30, H + top + 30), info, fill=(116, 138, 152), font=font(15))
    canvas.save(out)
    print("saved", out, canvas.size)


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "Physx/hangtianjidi.bin"
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/dfmap/out/hangtian_map.png"
    zb, cnt, meta = accumulate(src, width=1600)
    img = colorize(zb, cnt, meta)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    decorate(img, meta, out,
             "三角洲行动 · 航天基地 — 俯视结构图",
             "source: QH190311/delta-force-3d-map / Physx/hangtianjidi.bin ｜ PhysX 碰撞几何，非美术模型 ｜ 仅供学习交流",
             note="碰撞面 2.87 M ｜ 网格 100 m ｜ 坐标单位 m")
