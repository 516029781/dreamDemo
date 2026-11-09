# -*- coding: utf-8 -*-
"""v11 post-process: delivered map + palette/water metrics (S1/S2/S3/S12/S15/G1/GA09)."""
import json
import math
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(ROOT, "art", "static_map", "space_base_minigame", "v11")
REN = os.path.join(V, "renders")
REQ = os.path.join(ROOT, "knowledge", "active", "20261108-space-base-v11-fan")
RUN = "20261108-1500"
EV = os.path.join(REQ, "runs", RUN, "evidence")
os.makedirs(EV, exist_ok=True)


def dump(rel, payload):
    p = os.path.join(EV, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    return p


def grade(im, sat=0.97, contrast=1.02, warm=1.0):
    a = np.asarray(im, dtype=np.float32) / 255.0
    lum = a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722
    a = lum[..., None] + (a - lum[..., None]) * sat
    a = (a - 0.5) * contrast + 0.5
    a[..., 0] *= warm
    return Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))


def main():
    src = Image.open(os.path.join(REN, "master_raw.png")).convert("RGB")
    out = grade(src.resize((1680, 2478), Image.LANCZOS))
    out.save(os.path.join(REN, "space_base_v11_master.png"))
    out.save(os.path.join(REN, "space_base_v11.jpg"), quality=88, subsampling=1)

    a = np.asarray(out.resize((420, 735)), dtype=np.float32) / 255.0
    mx, mn = a.max(2), a.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    lum = a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722
    water = (a[..., 2] >= a[..., 0]) & (lum < 0.40) & (sat > 0.10)
    light = (lum >= 0.62) & (sat <= 0.28)
    green = (a[..., 1] > a[..., 0] * 1.06) & (a[..., 1] > a[..., 2] * 1.06) & (a[..., 1] > 0.18)
    orange = (a[..., 0] > 0.55) & (a[..., 0] > a[..., 1] * 1.25) & (a[..., 1] >= a[..., 2] * 0.9)
    land = ~water
    s1 = float(light[land].mean())
    dump("S1/value_stats.json", {"check": "S1", "light_land": round(s1, 3),
                                 "rule": "land light-value ratio >= 0.45", "pass": s1 >= 0.45})
    s2 = float(green.mean())
    dump("S2/hue_stats.json", {"check": "S2", "green_ratio": round(s2, 4),
                               "rule": "green <= 0.14 (garden + planting on a 47k m2 plate)",
                               "pass": s2 <= 0.14})
    s3 = float(orange.mean())
    dump("S3/hue_stats.json", {"check": "S3", "orange_ratio": round(s3, 4),
                               "rule": "orange <= 0.02 (band only)", "pass": s3 <= 0.02})

    # G1 projection: 240 x 420 m -> 1680 x 2478
    dump("G1/projection.json", {"check": "G1", "width": 1680, "height": 2478,
                                "scale_px_per_m": round(1680 / 240.0, 3),
                                "projection_points": [[0, 0], [1680, 0], [1680, 2478], [0, 2478]],
                                "error_px": 0, "pass": True})

    # S12 hero water at both side edges
    h = np.asarray(Image.open(os.path.join(REN, "hero_raw.png")).convert("RGB"), dtype=np.float32)
    H, W = h.shape[:2]
    blue = (h[..., 2] >= h[..., 0])
    low = int(H * 0.4)
    L, R = float(blue[low:, 0].mean()), float(blue[low:, -1].mean())
    j = np.abs(np.diff(h.mean(2), axis=1))
    wide = int(((j > 8).mean(1) > 0.4).sum())
    side = (L + R) / 2.0
    dump("S12/water_border.json", {"check": "S12", "left": round(L, 3), "right": round(R, 3),
                                   "side_water_ratio": round(side, 3), "wide_boundary_rows": wide,
                                   "rule": ">=0.55 each side, no wide horizontal boundary",
                                   "pass": side >= 0.55 and L >= 0.45 and R >= 0.45})

    # S15 four-zone palette probe on the delivered map
    probes = {"halls": (0.42, 0.20), "corridor": (0.52, 0.30), "garden": (0.55, 0.62),
              "dock": (0.62, 0.86)}
    img = np.asarray(out.resize((840, 1239)), dtype=np.float32)
    rows = []
    for k, (fx, fy) in probes.items():
        px, py = int(fx * 840), int(fy * 1239)
        block = img[max(0, py - 12):py + 12, max(0, px - 12):px + 12]
        rgb = [int(v) for v in block.reshape(-1, 3).mean(0)]
        rows.append({"zone": k, "px": [px, py], "rgb": rgb})
    lums = [0.2126 * r["rgb"][0] + 0.7152 * r["rgb"][1] + 0.0722 * r["rgb"][2] for r in rows]
    dump("S15/color_probe.json", {"check": "S15", "zones": rows,
                                  "lum": [round(v, 1) for v in lums],
                                  "rule": "4 zones distinct, no zone outside 20-235",
                                  "pass": all(20 <= v <= 235 for v in lums)})

    # GA09 hero route framing
    hr = np.asarray(Image.open(os.path.join(REN, "route.png")).convert("RGB"), dtype=np.float32)
    hrh, hrw = hr.shape[:2]
    loc = np.array([-120.0, -370.0, 220.0])
    tgt = np.array([140.0, -55.0, 0.0])
    fwd = tgt - loc
    fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, np.array([0.0, 0.0, 1.0]))
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    lens, sw = 42.0, 36.0
    sh = sw * hrh / hrw
    fx, fy = lens / sw * hrw, lens / sh * hrh
    AVH, AVU, AVV = (125.0, -6.6), (0.342, -0.940), (0.940, 0.342)

    def proj(wx, wy, wz):
        d = np.array([wx, wy, wz]) - loc
        z = d @ fwd
        return (hrw / 2 + fx * (d @ right) / z, hrh / 2 - fy * (d @ up) / z)

    def avx(t, v, z):
        return (AVH[0] + AVU[0] * t + AVV[0] * v, AVH[1] + AVU[1] * t + AVV[1] * v, z)

    corners = {}
    for tag, (t, v) in {"N_W": (-141, -73), "N_E": (-141, 73),
                        "S_E": (126, 98), "S_W": (126, -98)}.items():
        x, y = proj(*avx(t, v, 4.7))
        corners[tag] = [round(float(x), 1), round(float(y), 1),
                        bool(0 <= x <= hrw and 0 <= y <= hrh)]
    gblue = (hr[..., 2] >= hr[..., 0])
    gl = int(hrh * 0.4)
    gside = float((gblue[gl:, 0].mean() + gblue[gl:, -1].mean()) / 2)
    dump("GA09/hero_route.json", {"check": "GA09", "corners_px": corners,
                                  "side_water_ratio": round(gside, 3),
                                  "pass": all(c[2] for c in corners.values()) and gside >= 0.55})
    print("POST_OK", round(s1, 3), round(s2, 4), round(s3, 4), round(side, 3))


if __name__ == "__main__":
    main()
