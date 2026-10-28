"""Measure the fixed P1 whole-scene anchor (t084) for the next candidate.

Outputs, per frame:
  - dominant palette (median-cut quantisation) with shares
  - hue histogram weighted by saturation
  - value histogram and percentile points
  - shadow tint (darkest 10%) and highlight tint (brightest 5%)
  - warm/cool split
The historical five-frame aggregate remains untouched. Current measurements
must describe the stable whole-scene anchor, not an average of changing shots.

Usage: python tools/p1_style_probe.py
"""
import colorsys
import argparse
import hashlib
import json
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P1 = os.path.join(ROOT, "reference/_raw_screenshots/P1")
MAIN_REFERENCE = "t084s.jpg"
OUT = os.path.join(ROOT, "delivery/next_cycle/n5/T2/p1_style_probe_t084.json")


def hex_of(rgb):
    return "#%02X%02X%02X" % tuple(int(round(v)) for v in rgb)


def hsv_of(rgb):
    r, g, b = [v / 255.0 for v in rgb]
    return colorsys.rgb_to_hsv(r, g, b)


def analyse(path):
    im = Image.open(path).convert("RGB")
    im.thumbnail((640, 640), Image.LANCZOS)
    a = np.asarray(im, dtype=np.float32)

    # Dominant palette by median cut.
    q = im.quantize(colors=10, method=Image.MEDIANCUT)
    pal = np.array(q.getpalette()[: 30]).reshape(10, 3)
    counts = np.bincount(np.asarray(q).ravel(), minlength=10)
    order = np.argsort(-counts)
    palette = [{"hex": hex_of(pal[i]),
                "hue": round(hsv_of(pal[i])[0] * 360, 1),
                "sat": round(hsv_of(pal[i])[1], 3),
                "val": round(hsv_of(pal[i])[2], 3),
                "share": round(float(counts[i]) / counts.sum(), 3)}
               for i in order if counts[i] > 0]

    mx = a.max(2) / 255.0
    mn = a.min(2) / 255.0
    v = mx
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)

    # Hue histogram weighted by saturation, so grey pixels do not dominate.
    hue = np.zeros_like(v)
    d = mx - mn
    m = d > 1e-6
    r, g, b = a[..., 0] / 255.0, a[..., 1] / 255.0, a[..., 2] / 255.0
    idx = (mx == r) & m
    hue[idx] = ((g[idx] - b[idx]) / d[idx]) % 6
    idx = (mx == g) & m
    hue[idx] = ((b[idx] - r[idx]) / d[idx]) + 2
    idx = (mx == b) & m
    hue[idx] = ((r[idx] - g[idx]) / d[idx]) + 4
    hue *= 60
    w = s
    bins = np.arange(0, 361, 30)
    hist = np.histogram(hue, bins=bins, weights=w)[0]
    hist = hist / max(hist.sum(), 1e-6)

    # Shadow and highlight tints.
    flat = a.reshape(-1, 3)
    vf = v.ravel()
    lo = flat[vf <= np.percentile(vf, 10)]
    hi = flat[vf >= np.percentile(vf, 95)]
    shadow = hex_of(lo.mean(0)) if len(lo) else None
    highlight = hex_of(hi.mean(0)) if len(hi) else None

    # Warm vs cool, split at hue 60/240 on saturated pixels.
    sel = s > 0.15
    hh = hue[sel]
    warm = float(((hh < 90) | (hh > 330)).mean()) if len(hh) else 0.0
    cool = float(((hh >= 150) & (hh <= 280)).mean()) if len(hh) else 0.0

    return {
        "frame": os.path.basename(path),
        "size": list(Image.open(path).size),
        "palette": palette,
        "hue_hist_30deg": {f"{bins[i]}-{bins[i+1]}": round(float(hist[i]), 3)
                           for i in range(12)},
        "value": {
            "mean": round(float(v.mean()), 3),
            "std": round(float(v.std()), 3),
            "p5": round(float(np.percentile(v, 5)), 3),
            "p50": round(float(np.percentile(v, 50)), 3),
            "p95": round(float(np.percentile(v, 95)), 3),
        },
        "saturation": {"mean": round(float(s.mean()), 3),
                       "p90": round(float(np.percentile(s, 90)), 3)},
        "shadow_tint": shadow,
        "highlight_tint": highlight,
        "warm_ratio": round(warm, 3),
        "cool_ratio": round(cool, 3),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", help="Optional candidate screenshot to measure with the same whole-frame metrics")
    args = parser.parse_args()
    path = os.path.join(P1, MAIN_REFERENCE)
    if not os.path.isfile(path):
        raise SystemExit("missing fixed P1 reference: %s" % path)
    with open(path, "rb") as fh:
        reference_sha = hashlib.sha256(fh.read()).hexdigest()
    rows = [analyse(path)]
    candidate = None
    if args.candidate:
        candidate_path = os.path.abspath(args.candidate)
        with open(candidate_path, "rb") as fh:
            candidate = {
                "path": os.path.relpath(candidate_path, ROOT).replace("\\", "/"),
                "sha256": hashlib.sha256(fh.read()).hexdigest(),
                "profile": analyse(candidate_path),
            }
    agg = {
        "kind": "p1_style_probe/2",
        "primary_reference": {
            "path": "reference/_raw_screenshots/P1/" + MAIN_REFERENCE,
            "sha256": reference_sha,
            "role": "fixed_whole_scene_anchor",
        },
        "candidate_comparison": candidate,
        "frames": rows,
        "aggregate": {
            "value_p95_mean": round(float(np.mean([r["value"]["p95"] for r in rows])), 3),
            "value_std_mean": round(float(np.mean([r["value"]["std"] for r in rows])), 3),
            "value_p5_mean": round(float(np.mean([r["value"]["p5"] for r in rows])), 3),
            "sat_mean": round(float(np.mean([r["saturation"]["mean"] for r in rows])), 3),
            "sat_p90_mean": round(float(np.mean([r["saturation"]["p90"] for r in rows])), 3),
            "warm_ratio_mean": round(float(np.mean([r["warm_ratio"] for r in rows])), 3),
            "cool_ratio_mean": round(float(np.mean([r["cool_ratio"] for r in rows])), 3),
            "hue_0_30_mean": round(float(np.mean([r["hue_hist_30deg"]["0-30"] for r in rows])), 3),
            "hue_30_60_mean": round(float(np.mean([r["hue_hist_30deg"]["30-60"] for r in rows])), 3),
        },
    }
    if candidate:
        ref_profile = rows[0]
        cand_profile = candidate["profile"]
        delta_fields = {
            "value.p5": (cand_profile["value"]["p5"], ref_profile["value"]["p5"]),
            "value.p50": (cand_profile["value"]["p50"], ref_profile["value"]["p50"]),
            "value.p95": (cand_profile["value"]["p95"], ref_profile["value"]["p95"]),
            "saturation.mean": (cand_profile["saturation"]["mean"], ref_profile["saturation"]["mean"]),
            "hue.0-30": (cand_profile["hue_hist_30deg"]["0-30"], ref_profile["hue_hist_30deg"]["0-30"]),
            "hue.30-60": (cand_profile["hue_hist_30deg"]["30-60"], ref_profile["hue_hist_30deg"]["30-60"]),
        }
        agg["candidate_comparison"]["delta_candidate_minus_reference"] = {
            key: round(a - b, 3) for key, (a, b) in delta_fields.items()
        }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(agg, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    print(json.dumps(agg["aggregate"], ensure_ascii=False))
    for r in rows:
        print("\n" + r["frame"],
              "| shadow", r["shadow_tint"], "| highlight", r["highlight_tint"],
              "| warm", r["warm_ratio"], "cool", r["cool_ratio"])
        for p in r["palette"][:6]:
            print("   %s  hue %5.1f  sat %.2f  val %.2f  share %.2f"
                  % (p["hex"], p["hue"], p["sat"], p["val"], p["share"]))


if __name__ == "__main__":
    main()
