# -*- coding: utf-8 -*-
"""统一测量：把参考图和渲染图放到同一把尺子上（§3.7.6 方法）。

用法（系统 python）：
    python preflight/measure.py --render renders/check.png --json preflight/MEASURE.json
输出：控制台对照表 + JSON
"""
import argparse
import json
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = r"C:/软件/鼠鼠/reference/_raw_screenshots/P1/t084s.jpg"
U0, U1 = 0.20, 0.78          # 契约窗口，不可改
BAND = 2                     # 每 2% 一条带


def load(path, width=1920):
    im = Image.open(path).convert("RGB")
    h = round(im.height * width / im.width)
    return im.resize((width, h), Image.LANCZOS), h


def luma(r, g, b):
    return 0.299 * r + 0.587 * g + 0.114 * b


def band_means(im, h, u0=U0, u1=U1):
    """u 窗口内每 2% v 带的灰度均值。"""
    W = im.width
    x0, x1 = int(W * u0), int(W * u1)
    px = im.load()
    out = {}
    for band in range(0, 100, BAND):
        y0, y1 = int(h * band / 100), max(int(h * (band + BAND) / 100), int(h * band / 100) + 1)
        tot, n = 0.0, 0
        for y in range(y0, min(y1, h), 2):
            for x in range(x0, x1, 2):
                r, g, b = px[x, y]
                tot += luma(r, g, b)
                n += 1
        out[band] = round(tot / max(n, 1), 1)
    return out


def cold_stats(im, h, win=(0.30, 0.56, 0.14, 0.27)):
    """冷色占比按 §3.6 判据 8：只统计窗口内的冷色像素，分母是整幅。"""
    W = im.width
    px = im.load()
    ux0, ux1, vy0, vy1 = win
    x0, x1 = int(W * ux0), int(W * ux1)
    y0, y1 = int(h * vy0), int(h * vy1)
    n_cold = 0
    sr = sb = 0
    for y in range(y0, y1, 1):
        for x in range(x0, x1, 1):
            r, g, b = px[x, y]
            if b > r + 12:
                n_cold += 1
                sr += r
                sb += b
    total = W * h
    bbox = None
    if n_cold:
        bbox = [round(x0 / W, 3), round(x1 / W, 3), round(y0 / h, 3), round(y1 / h, 3)]
    return {
        "ratio_pct": round(100.0 * n_cold / max(total, 1), 3),
        "mean_b_minus_r": round((sb - sr) / max(n_cold, 1), 1),
        "mean_rgb": [round(sr / max(n_cold, 1)), round((sr + sb) / 2 / max(n_cold, 1)),
                     round(sb / max(n_cold, 1))],
        "bbox_u_v": bbox,
        "px": n_cold,
    }


def anchor_metrics(bm):
    top = sum(bm[b] for b in range(0, 8, 2)) / 4
    far = sum(bm[b] for b in range(10, 22, 2)) / 6
    stage = sum(bm[b] for b in range(56, 90, 2)) / 17
    valley = sum(bm[b] for b in range(44, 50, 2)) / 3
    local = min(range(30, 56, 2), key=lambda b: bm[b])
    return {
        "top_v0_8": round(top, 1),
        "far_v10_22": round(far, 1),
        "stage_v56_90": round(stage, 1),
        "valley_v44_50": round(valley, 1),
        "stage_minus_valley": round(stage - valley, 1),
        "local_min_v": local,
        "local_min_val": bm[local],
        "v22_to_44_max_rise": round(max(bm[b] - bm[22] for b in range(22, 45, 2)), 1),
        "v48_to_58_rise": round(bm[58] - bm[48], 1),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", required=True)
    ap.add_argument("--json", default=os.path.join(ROOT, "preflight", "MEASURE.json"))
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    ref_im, h = load(REF)
    now_im, h2 = load(args.render, width=1920)
    rb = band_means(ref_im, h)
    nb = band_means(now_im, h2)
    rl, nr = band_means(ref_im, h, 0.20, 0.50), band_means(now_im, h2, 0.20, 0.50)
    rr, nrr = band_means(ref_im, h, 0.50, 0.78), band_means(now_im, h2, 0.50, 0.78)
    rm, nm = anchor_metrics(rb), anchor_metrics(nb)
    rc, nc = cold_stats(ref_im, h), cold_stats(now_im, h2)

    out = {"render": args.render, "bands": {"ref": rb, "now": nb},
           "bands_left": {"ref": rl, "now": nr},
           "bands_right": {"ref": rr, "now": nrr},
           "anchors": {"ref": rm, "now": nm}, "cold": {"ref": rc, "now": nc}}
    with open(args.json, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    if args.quiet:
        print(json.dumps({"anchors": out["anchors"], "cold": out["cold"]},
                         ensure_ascii=False))
        return
    print("  v%    ref    now    Δ")
    for b in range(0, 100, 2):
        print("%3d   %6.1f %6.1f %+7.1f" % (b, rb[b], nb[b], nb[b] - rb[b]))
    print("\n指标                ref      now")
    for k in rm:
        print("%-18s %7s %7s" % (k, rm[k], nm[k]))
    print("\n冷色  ratio=%.3f%% (ref %.3f)  B-R=%s (ref %s)  bbox=%s (ref %s)"
          % (nc["ratio_pct"], rc["ratio_pct"], nc["mean_b_minus_r"],
             rc["mean_b_minus_r"], nc["bbox_u_v"], rc["bbox_u_v"]))


if __name__ == "__main__":
    main()
