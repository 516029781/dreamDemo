"""Imaging metrics for SPACE_BASE_TECHNICAL_ART_PLAN_20261108 v1.1 §5.

Pure-Python (PIL + numpy). Measures A1-A5, A10 proxy, A13, and the S1
light-land ratio in the exact same wording as tools/space_base_v11_post.py --
but WITHOUT writing into the frozen v11 candidate (that script hardcodes v11
paths and overwrites v11 deliverables).

Usage:
  python tools/check_v14_art.py --image <PNG> --out <JSON> [--label NAME]

Masks (declared before measurement, do not change between A/B runs):
  land_mask (for A1-A5/A13) : NOT ((B > G*0.95) & (G > R*1.15) & (L < 0.40))
  water_mask (for S1)       : (B >= R) & (L < 0.40) & (sat > 0.10)
  light (for S1)            : (L >= 0.62) & (sat <= 0.28)
  L = Rec.709 luma on sRGB-encoded 8-bit pixels / 255 (same as v11_post).

A10 is a PROXY for an orthographic top-down image: local gradient energy in
three horizontal bands. It is diagnostic_only, not a pass/fail gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


def measure(path: Path) -> dict:
    a = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    L = 0.2126 * r + 0.7152 * g + 0.0722 * b
    mx, mn = a.max(2), a.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)

    land = ~((b > g * 0.95) & (g > r * 1.15) & (L < 0.40))
    ll = L[land]
    p10, p50, p90 = (float(np.percentile(ll, q)) for q in (10, 50, 90))

    # S1: same rule as space_base_v11_post.py, evaluated at full resolution
    water = (b >= r) & (L < 0.40) & (sat > 0.10)
    light = (L >= 0.62) & (sat <= 0.28)
    s1 = float(light[~water].mean())

    # S1 historical-comparable variant: 420x735 downsample (v11_post wording)
    small = np.asarray(Image.open(path).convert("RGB").resize((420, 735), Image.LANCZOS),
                       dtype=np.float32) / 255.0
    sr, sg, sb = small[..., 0], small[..., 1], small[..., 2]
    sL = 0.2126 * sr + 0.7152 * sg + 0.0722 * sb
    smx, smn = small.max(2), small.min(2)
    sS = np.where(smx > 0, (smx - smn) / np.maximum(smx, 1e-6), 0)
    swater = (sb >= sr) & (sL < 0.40) & (sS > 0.10)
    slight = (sL >= 0.62) & (sS <= 0.28)
    s1_small = float(slight[~swater].mean())

    # A10 proxy: mean |gradient| per horizontal band (top / middle / bottom)
    bands = []
    H = L.shape[0]
    for i in range(3):
        band = L[i * H // 3:(i + 1) * H // 3]
        grad = float(np.abs(np.diff(band, axis=1)).mean() + np.abs(np.diff(band, axis=0)).mean())
        bands.append(round(grad, 5))

    return {
        "image": str(path).replace("\\", "/"),
        "image_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size": [int(a.shape[1]), int(a.shape[0])],
        "land_ratio": round(float(land.mean()), 4),
        "A1_land_L_p50": round(p50, 4),
        "A2_bright_gt080_pct": round(float((ll > 0.80).mean() * 100), 2),
        "A3_dark_lt030_pct": round(float((ll < 0.30).mean() * 100), 2),
        "A4_span_p90_p10": round(p90 - p10, 4),
        "A5_clip_gt097_pct": round(float((ll > 0.97).mean() * 100), 3),
        "A10_band_gradient_proxy": bands,
        "A13_mean_saturation": round(float(sat[land].mean()), 4),
        "S1_light_land": round(s1, 4),
        "S1_light_land_420x735": round(s1_small, 4),
        "S1_pass": bool(s1 >= 0.45),
        "extra": {
            "land_L_p10": round(p10, 4), "land_L_p90": round(p90, 4),
            "land_L_mean": round(float(ll.mean()), 4),
            "land_L_std": round(float(ll.std()), 4),
            "sat_full_frame": round(float(sat.mean()), 4),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    a = ap.parse_args()
    p = Path(a.image).resolve()
    out = Path(a.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    d = measure(p)
    d["label"] = a.label
    d["schema"] = "v14-art-metrics-v1"
    out.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print("ART_METRICS", a.label or p.name,
          "A1=%.3f A2=%.1f%% A3=%.1f%% A4=%.3f A5=%.2f%% A13=%.3f S1=%.3f(%s)" % (
              d["A1_land_L_p50"], d["A2_bright_gt080_pct"], d["A3_dark_lt030_pct"],
              d["A4_span_p90_p10"], d["A5_clip_gt097_pct"], d["A13_mean_saturation"],
              d["S1_light_land"], "PASS" if d["S1_pass"] else "FAIL"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
