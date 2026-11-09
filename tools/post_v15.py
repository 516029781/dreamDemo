"""v15 post-process: grade + deliverable + S1/S2/S3/water_frac + per-hall stats.

Same colour grade as v11/v14 (sat .97 / contrast 1.02 / warm 1.0) so colour
management does not regress. Writes evidence JSON next to the run.

    python tools/post_v15.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path("C:/软件/鼠鼠")
CAND = ROOT / "art/static_map/space_base_minigame/v15"
REN = CAND / "renders"
EV = CAND / "evidence"
EV.mkdir(parents=True, exist_ok=True)

HALL_PX = {"H1": (609.9, 282.9, 810.5, 483.5), "H2": (869.6, 282.9, 1070.2, 483.6),
           "H3": (609.9, 542.6, 810.5, 743.2), "H4": (869.6, 542.6, 1070.2, 743.2)}


def grade(im, sat=0.97, contrast=1.02, warm=1.0):
    a = np.asarray(im, dtype=np.float32) / 255.0
    lum = a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722
    a = lum[..., None] + (a - lum[..., None]) * sat
    a = (a - 0.5) * contrast + 0.5
    a[..., 0] *= warm
    return Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))


def metrics(im):
    a = np.asarray(im.resize((420, 735), Image.LANCZOS), dtype=np.float32) / 255.0
    mx, mn = a.max(2), a.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    lum = a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722
    water = (a[..., 2] >= a[..., 0]) & (lum < 0.40) & (sat > 0.10)
    light = (lum >= 0.62) & (sat <= 0.28)
    green = (a[..., 1] > a[..., 0] * 1.06) & (a[..., 1] > a[..., 2] * 1.06) & (a[..., 1] > 0.18)
    orange = (a[..., 0] > 0.55) & (a[..., 0] > a[..., 1] * 1.25) & (a[..., 1] >= a[..., 2] * 0.9)
    land = ~water
    return a, lum, water, light, green, orange, land


def main() -> int:
    raw = Image.open(REN / "master_raw.png").convert("RGB")
    assert raw.size == (1680, 2478), raw.size
    out = grade(raw)
    out.save(REN / "space_base_v15_master.png")
    out.save(REN / "space_base_v15.jpg", quality=88, subsampling=1, optimize=True)
    # the business gate still pins v11 file names
    out.save(REN / "space_base_v11_master.png")
    out.save(REN / "space_base_v11.jpg", quality=88, subsampling=1)
    core = out.crop((300, 120, 1380, 1100)).resize((2072, 1876), Image.LANCZOS)
    core.save(REN / "space_base_v15_core.png")
    core.save(REN / "space_base_v11_core.png")

    a, lum, water, light, green, orange, land = metrics(out)
    s1, s2, s3 = float(light[land].mean()), float(green.mean()), float(orange.mean())
    wf = float(water.mean())
    halls = {}
    for k, (x1, y1, x2, y2) in HALL_PX.items():
        X1, X2, Y1, Y2 = [int(round(v / 4)) for v in (x1, x2, y1, y2)]
        sub = slice(Y1, Y2), slice(X1, X2)
        halls[k] = {"light_pct": round(float(light[sub].mean()) * 100, 1),
                    "L_med": round(float(np.median(lum[sub])), 3),
                    "water_pct": round(float(water[sub].mean()) * 100, 1)}
    payload = {
        "schema": "v15-post-v1",
        "S1": {"light_land": round(s1, 4), "rule": ">=0.45", "pass": s1 >= 0.45},
        "S2": {"green_ratio": round(s2, 5), "rule": "<=0.12", "pass": s2 <= 0.12},
        "S3": {"orange_ratio": round(s3, 5), "rule": "<=0.02", "pass": s3 <= 0.02},
        "water_frac": round(wf, 4),
        "land_frac": round(1.0 - wf, 4),
        "halls": halls,
        "grade": {"sat": 0.97, "contrast": 1.02, "warm": 1.0},
    }
    with open(EV / "post_metrics.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print("V15_POST", json.dumps({k: payload[k] for k in ("S1", "S2", "S3", "water_frac")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
