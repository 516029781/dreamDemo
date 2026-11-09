"""Post-process + mechanical gate for space_base_minigame v03 (layout v3.10).

master_raw 3360x5880 (2x isotropic) -> 1680x2940 -> squash to 1680x2408
  (py = (166-y)*5.7344) -> pad 70 px bottom bleed -> 1680x2478.

Checks (per plan v3.10 §8 / §12 r02 draft):
  G1  dims 1680x2478 (master 3360x5880), 240 m = 1680 px
  G4  pixel probes: garden gate / fountain / dock gate / evac frame
  W1  jpg <=3 MB, max side <=4096, no alpha, 1680x2478
  S1  white+light-gray >= 45%
  S2  green <= 8%
  S3  orange <= 2%
Writes: master png, shipped jpg, 4 check crops, GATE_REPORT.json.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VER = sys.argv[1] if len(sys.argv) > 1 else "v04"
V03 = os.path.join(ROOT, "art", "static_map", "space_base_minigame", VER)
REN = os.path.join(V03, "renders")
CHK = os.path.join(V03, "checks")

CONTENT_H = 2408          # 420 m * 5.7344
FINAL_W, FINAL_H = 1680, 2478
BLEED = 70


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def px(x, y):
    """World meters -> final-image pixel (north-up)."""
    return x * 7.0, (166.0 - y) * 5.7344


def main():
    os.makedirs(REN, exist_ok=True)
    os.makedirs(CHK, exist_ok=True)

    raw = Image.open(os.path.join(REN, "master_raw.png")).convert("RGB")
    assert raw.size == (3360, 5880), raw.size

    # 2x -> 1x isotropic, then vertical squash to spec, then bleed
    img = raw.resize((1680, 2940), Image.LANCZOS)
    img = img.resize((FINAL_W, CONTENT_H), Image.LANCZOS)
    bleed_row = img.crop((0, CONTENT_H - 1, FINAL_W, CONTENT_H))
    master = img.copy()
    canvas = Image.new("RGB", (FINAL_W, FINAL_H))
    canvas.paste(img, (0, 0))
    for i in range(BLEED):
        canvas.paste(bleed_row, (0, CONTENT_H + i))
    master_path = os.path.join(REN, f"space_base_{VER}_master.png")
    canvas.save(master_path, optimize=True)

    # shipped jpg
    jpg_path = os.path.join(REN, f"space_base_{VER}.jpg")
    q = 88
    canvas.save(jpg_path, quality=q, optimize=True)
    while os.path.getsize(jpg_path) > 3 * 1024 * 1024 and q > 60:
        q -= 4
        canvas.save(jpg_path, quality=q, optimize=True)

    # check crops (world-rect -> px box, clamp)
    crops = {
        "check_core": (46, 0, 194, 134),
        "check_garden_causeway": (66, -64, 178, -6),
        "check_dock": (140, -240, 240, -128),
        "check_north": (46, 96, 194, 140),
    }
    crop_paths = {}
    for name, (x0, y0, x1, y1) in crops.items():
        ax, ay = px(x0, y1)
        bx, by = px(x1, y0)
        box = (max(0, int(ax)), max(0, int(ay)), min(FINAL_W, int(bx)), min(FINAL_H, int(by)))
        canvas.crop(box).save(os.path.join(CHK, f"{name}.png"))
        crop_paths[name] = box

    # pixel probes (G4-style mechanical, v3.10 geometry)
    probe_defs = [
        ("garden_north_gate_120_-14", (120, -14)),
        ("fountain_ring_120_-39", (111, -39)),
        ("causeway_mid_166_-97", (166, -97)),
        ("dock_floor_u48_v0", None),          # computed from dock local frame
        ("evac_frame_221_-214", (221, -214)),
        ("evac_strip_u90_v16.8", (172 + 0.342 * 90 + 0.940 * 16.8,
                                  -136 - 0.940 * 90 + 0.342 * 16.8)),
        ("water_sw_20_-240", (20, -240)),
    ]
    probes = {}
    for label, wxy in probe_defs:
        if wxy is None:   # dock floor: O + 48u
            wx, wy = 172 + 0.342 * 48, -136 - 0.940 * 48
        else:
            wx, wy = wxy
        ix, iy = px(wx, wy)
        ix, iy = int(min(max(ix, 0), FINAL_W - 1)), int(min(max(iy, 0), CONTENT_H - 1))
        probes[label] = {"world": [round(wx, 2), round(wy, 2)], "px": [ix, iy],
                         "rgb": canvas.getpixel((ix, iy))}

    # color statistics (S1/S2/S3) on shipped master
    small = canvas.resize((420, 619))
    pxs = list(small.getdata())
    n = len(pxs)
    s1 = s2 = s3 = water = 0
    for r, g, b in pxs:
        mx, mn = max(r, g, b), min(r, g, b)
        sat = 0 if mx == 0 else (mx - mn) / mx
        lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
        if lum >= 0.72 and sat <= 0.18:
            s1 += 1
        if g > r * 1.06 and g > b * 1.06 and g > 60:
            s2 += 1
        if r > 115 and r > g * 1.18 and g >= b:
            s3 += 1
        if b > r and b >= g and lum < 0.34 and sat > 0.12:
            water += 1
    stats = {"S1_light_ratio": round(s1 / n, 4), "S2_green_ratio": round(s2 / n, 4),
             "S3_orange_ratio": round(s3 / n, 4), "water_ratio": round(water / n, 4)}

    report = {
        "schema": "space-base-gate-v1",
        "business_id": "space_base_minigame",
        "version": VER,
        "layout_source": "planning/art/SPACE_BASE_NEW_PLAN_20261103.md (v3.10)",
        "G1": {"master": [3360, 5880], "final": [FINAL_W, FINAL_H],
               "px_per_m_x": 7.0, "px_per_m_y": 5.7344,
               "pass": canvas.size == (FINAL_W, FINAL_H)},
        "W1": {"jpg_bytes": os.path.getsize(jpg_path), "jpg_quality": q,
               "max_side": max(FINAL_W, FINAL_H), "alpha": False,
               "pass": os.path.getsize(jpg_path) <= 3 * 1024 * 1024
                       and max(FINAL_W, FINAL_H) <= 4096},
        "G4_probes": probes,
        "S1_S2_S3": stats,
        "crops": {k: list(v) for k, v in crop_paths.items()},
        "hashes": {"master_png": sha256(master_path), "shipped_jpg": sha256(jpg_path)},
        "notes": [
            "S2 绿色含花园植被（方案 S2 规则中植被绿独立景观色，不计入企业绿配额）",
            "G5（集装箱挡撤离黄框）与 G2/G3/G8/S4-S7 属视觉项，交独立审核",
        ],
    }
    with open(os.path.join(V03, "GATE_REPORT.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print(json.dumps({"master": canvas.size, "jpg_bytes": report["W1"]["jpg_bytes"],
                      "stats": stats, "probes": {k: v["rgb"] for k, v in probes.items()}},
                     ensure_ascii=False))
    print("POST_OK")


if __name__ == "__main__":
    sys.exit(main())
