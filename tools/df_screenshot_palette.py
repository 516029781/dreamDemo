#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extract an area-weighted colour palette from Delta Force screenshots.

Usage:
    python tools/df_screenshot_palette.py reference/_df_screenshots/gamersky/*.jpg

Notes:
- The guide screenshots carry a neon-green caption box in a corner. Pixels in
  that hue band (high-saturation cyan-green) are dropped so the palette
  reflects the game art, not the annotation overlay.
- Output is JSON on stdout; no files are written.
"""
import sys
import json
import colorsys

import numpy as np
from PIL import Image


def drop_overlay(rgb: np.ndarray) -> np.ndarray:
    """Remove the guide's neon-green caption overlay."""
    f = rgb.astype(np.float32) / 255.0
    mx = f.max(axis=1)
    mn = f.min(axis=1)
    v = mx
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
    # hue in degrees
    r, g, b = f[:, 0], f[:, 1], f[:, 2]
    d = np.maximum(mx - mn, 1e-6)
    h = np.zeros_like(mx)
    m = mx == r
    h[m] = (60 * ((g[m] - b[m]) / d[m])) % 360
    m = mx == g
    h[m] = 60 * ((b[m] - r[m]) / d[m]) + 120
    m = mx == b
    h[m] = 60 * ((r[m] - g[m]) / d[m]) + 240
    overlay = (h > 125) & (h < 170) & (s > 0.55) & (v > 0.55)
    return rgb[~overlay]


def kmeans(data: np.ndarray, k: int, iters: int = 24) -> tuple[np.ndarray, np.ndarray]:
    """Tiny k-means; deterministic seeding by luminance quantiles."""
    if len(data) > 120000:
        idx = np.random.default_rng(7).choice(len(data), 120000, replace=False)
        sample = data[idx]
    else:
        sample = data
    lum = sample @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    order = np.argsort(lum)
    centers = sample[order[np.linspace(0, len(order) - 1, k).astype(int)]].copy()
    for _ in range(iters):
        d = ((sample[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        lab = d.argmin(axis=1)
        for j in range(k):
            sel = sample[lab == j]
            if len(sel):
                centers[j] = sel.mean(axis=0)
    d = ((sample[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
    lab = d.argmin(axis=1)
    share = np.bincount(lab, minlength=k) / len(sample)
    return centers, share


def accent_mask(rgb: np.ndarray, sat_min: float = 0.35) -> np.ndarray:
    mx = rgb.max(axis=1) / 255.0
    mn = rgb.min(axis=1) / 255.0
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
    return (s > sat_min) & (mx > 0.2)


def analyse(path: str, k: int = 7) -> dict:
    im = Image.open(path).convert("RGB")
    arr = np.asarray(im).reshape(-1, 3).astype(np.float32)
    arr = drop_overlay(arr)
    centers, share = kmeans(arr, k)
    accents_src = arr[accent_mask(arr)]
    accents = []
    if len(accents_src) > 2000:
        ac, ash = kmeans(accents_src, 5)
        for j in np.argsort(-ash):
            c = ac[j].round().astype(int)
            accents.append({
                "hex": "#%02X%02X%02X" % tuple(int(x) for x in c),
                "share_of_accent": round(float(ash[j]), 3),
                "share_of_frame": round(float(len(accents_src) / len(arr)), 3),
            })
    order = np.argsort(-share)
    palette = []
    for j in order:
        c = centers[j].round().astype(int)
        r, g, b = (int(x) for x in c)
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        palette.append({
            "hex": "#%02X%02X%02X" % (r, g, b),
            "share": round(float(share[j]), 3),
            "hue": round(h * 360),
            "sat": round(s, 3),
            "lum": round(l, 3),
        })
    return {"file": path.split("/")[-1], "palette": palette, "accents": accents}


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    out = [analyse(p) for p in argv]
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
