# -*- coding: utf-8 -*-
"""Deterministic procedural base-color textures for candidate_n5.

Native generation only (NumPy + OpenCV PNG encode): no AI image, no diffusion.
Sources land in candidate_n5/source/textures; engine copies go to
demo_n5/assets/resources/textures/. Textures are kept near mean luminance 0.92
so the engine tint carries palette color while the texture carries pattern.
"""
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '.tools', 'pycv'))
import cv2

ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
OUT_ART = os.path.join(ROOT, 'art', 'candidates', 'candidate_n5', 'source', 'textures')
OUT_DEMO = os.path.join(ROOT, 'demo_n5', 'assets', 'resources', 'textures')
rng = np.random.default_rng(20261025)


def save(img, name):
    for base in (OUT_ART, OUT_DEMO):
        os.makedirs(base, exist_ok=True)
        ok, buf = cv2.imencode('.png', img)
        assert ok
        with open(os.path.join(base, name), 'wb') as f:
            f.write(buf.tobytes())
    print('WROTE', name, img.shape[1], 'x', img.shape[0])


def norm01(a):
    lo, hi = a.min(), a.max()
    return (a - lo) / (hi - lo) if hi > lo else np.zeros_like(a)


def smooth_noise(size, scale, octaves=4):
    out = np.zeros((size, size), np.float32)
    amp = 1.0
    for o in range(octaves):
        n = rng.normal(0, 1, (size, size)).astype(np.float32)
        sigma = max(1.0, size / (scale * (2 ** o)))
        n = cv2.GaussianBlur(n, (0, 0), sigma)
        out += amp * n / (np.abs(n).max() + 1e-6)
        amp *= 0.55
    return norm01(out)


def leaf_detail(size=256):
    u, v = np.meshgrid(np.linspace(0, 1, size), np.linspace(0, 1, size))
    vein = np.abs(np.sin(2 * np.pi * (v * 4.0 + 0.15 * np.sin(u * 12.0))))
    vein = np.power(vein, 5.0)
    mottle = smooth_noise(size, 7, 3) - 0.5
    spots = smooth_noise(size, 22, 2) - 0.5
    value = 0.965 - 0.075 * vein + 0.05 * mottle + 0.025 * spots
    img = np.clip(norm01(value), 0, 1)
    save((np.dstack([img * 238, img * 226, img * 206])).astype(np.uint8), 'tex_leaf_detail.png')


def wood_grain(size=1024):
    u, v = np.meshgrid(np.linspace(0, 1, size), np.linspace(0, 1, size))
    streaks = np.zeros((size, size), np.float32)
    for k in range(1, 11):
        amp = 0.55 / k
        ph = rng.uniform(0, 2 * np.pi)
        warp = 0.35 * np.sin(2 * np.pi * (u * rng.uniform(0.4, 1.1) + ph))
        streaks += amp * np.sin(2 * np.pi * (v * k * rng.uniform(1.2, 2.8) + warp + ph))
    fine = rng.normal(0, 0.055, (size, size)).astype(np.float32)
    grain = cv2.filter2D(fine, -1, np.ones((1, 41), np.float32) / 41.0)
    value = 0.92 + 0.070 * streaks + 0.065 * grain
    # Knots: concentric distorted rings plus a dark center.
    for _ in range(5):
        kx, ky = rng.uniform(0.12, 0.88), rng.uniform(0.12, 0.88)
        rr = np.sqrt(((u - kx) * 1.0) ** 2 + ((v - ky) * 1.8) ** 2)
        knot = np.exp(-(rr / 0.045) ** 2) * 0.55
        rings = 0.10 * np.sin(rr * 180.0) * np.exp(-(rr / 0.11) ** 2)
        value -= knot - rings
    # Plank joints every half metre.
    for jv in (0.25, 0.75):
        d = np.abs(v - jv)
        value -= 0.16 * np.exp(-(d ** 2) / (2 * 0.0035 ** 2))
        value += 0.05 * np.exp(-((d - 0.006) ** 2) / (2 * 0.0015 ** 2))
    # Small cracks and worn edges.
    crack = smooth_noise(size, 40, 3)
    value -= 0.05 * np.clip(crack - 0.62, 0, 1) / 0.38
    img = np.clip(norm01(value), 0, 1)
    save((np.dstack([img * 238, img * 224, img * 204])).astype(np.uint8), 'tex_wood_grain.png')


def stone_tiles(size=1024, tiles=4):
    value = np.full((size, size), 0.92, np.float32)
    cell = size // tiles
    tone = np.zeros((size, size), np.float32)
    warm = np.zeros((size, size), np.float32)
    for ty in range(tiles):
        for tx in range(tiles):
            b = rng.uniform(0.79, 1.00)
            w = rng.uniform(-1, 1)
            tone[ty * cell:(ty + 1) * cell, tx * cell:(tx + 1) * cell] = b
            warm[ty * cell:(ty + 1) * cell, tx * cell:(tx + 1) * cell] = w
    value *= tone
    # Beveled tile edges: dark narrow grout, light bevel, chipped corners.
    edge = np.zeros((size, size), np.float32)
    hi = np.zeros((size, size), np.float32)
    for ty in range(tiles + 1):
        y = ty * cell
        for d in range(5):
            edge[(y + d) % size, :] = np.maximum(edge[(y + d) % size, :], 0.145 - d * 0.028)
        hi[(y - 1) % size, :] = np.maximum(hi[(y - 1) % size, :], 0.05)
    for tx in range(tiles + 1):
        x = tx * cell
        for d in range(5):
            edge[:, (x + d) % size] = np.maximum(edge[:, (x + d) % size], 0.145 - d * 0.028)
        hi[:, (x - 1) % size] = np.maximum(hi[:, (x - 1) % size], 0.05)
    value -= edge
    value += hi
    # Per-tile mottling and fine pores.
    mottle = smooth_noise(size, 9, 4) - 0.5
    pores = smooth_noise(size, 55, 2) - 0.5
    value += 0.075 * mottle + 0.030 * pores
    # Stains and moss near joints and in one corner of each tile.
    stain = smooth_noise(size, 4, 3)
    value -= 0.055 * np.clip(stain - 0.62, 0, 1) / 0.38
    # Chips: small dark crescents at random tile corners.
    for _ in range(14):
        cx, cy = rng.integers(0, size, 2)
        rr = rng.uniform(3, 10)
        y0, y1 = max(0, cy - int(rr)), min(size, cy + int(rr))
        x0, x1 = max(0, cx - int(rr)), min(size, cx + int(rr))
        yy, xx = np.mgrid[y0:y1, x0:x1]
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        value[y0:y1, x0:x1] -= 0.06 * np.exp(-(d / rr) ** 4)
    img = np.clip(norm01(value), 0, 1)
    # A little warm/cool stone variation, still multiplied by the engine tint.
    r = img * (236 + warm * 4)
    g = img * (229 + warm * 2)
    b = img * (216 - warm * 4)
    save(np.dstack([r, g, b]).astype(np.uint8), 'tex_stone_tiles.png')


def metal_brushed(size=512):
    fine = rng.normal(0, 1.0, (size, size)).astype(np.float32)
    streaks = cv2.filter2D(fine, -1, np.ones((11, 1), np.float32) / 11.0)
    long = cv2.filter2D(fine, -1, np.ones((1, 61), np.float32) / 61.0)
    value = 0.92 + 0.10 * streaks + 0.04 * long
    # Sparse scratches at varied angles.
    for _ in range(18):
        x0, y0 = rng.integers(0, size, 2)
        length = rng.uniform(40, 180)
        ang = rng.uniform(-0.25, 0.25)
        x1 = int(np.clip(x0 + np.cos(ang) * length, 0, size - 1))
        y1 = int(np.clip(y0 + np.sin(ang) * length, 0, size - 1))
        cv2.line(value, (int(x0), int(y0)), (x1, y1), float(rng.uniform(-0.05, 0.05)), 1)
    for _ in range(7):
        cx, cy = rng.integers(0, size, 2)
        cv2.circle(value, (int(cx), int(cy)), int(rng.uniform(1, 3)), float(rng.uniform(-0.08, 0.04)), -1)
    img = np.clip(norm01(value) * 0.42 + 0.71, 0, 1)
    save((np.dstack([img * 222, img * 221, img * 218])).astype(np.uint8), 'tex_metal_brushed.png')


def bark(size=512):
    u, v = np.meshgrid(np.linspace(0, 1, size), np.linspace(0, 1, size))
    ridges = np.zeros((size, size), np.float32)
    for k in range(1, 12):
        ph = rng.uniform(0, 2 * np.pi)
        warp = 0.28 * np.sin(2 * np.pi * (u * 2.0 + ph)) + 0.10 * np.sin(2 * np.pi * v * 3.0)
        ridges += (0.55 / k) * np.sin(2 * np.pi * (u * k * 2.0 + warp + ph))
    fine = rng.normal(0, 0.045, (size, size)).astype(np.float32)
    value = 0.92 + 0.065 * ridges + fine
    value -= 0.10 * np.clip(smooth_noise(size, 16, 3) - 0.65, 0, 1) / 0.35
    img = np.clip(norm01(value), 0, 1)
    save((np.dstack([img * 212, img * 198, img * 179])).astype(np.uint8), 'tex_bark.png')


def soil_noise(size=512):
    fine = rng.normal(0, 1.0, (size, size)).astype(np.float32)
    blob = smooth_noise(size, 7, 4) - 0.5
    value = 0.90 + 0.10 * blob + 0.055 * fine
    # Pebbles and damp patches.
    for _ in range(90):
        cx, cy = rng.integers(0, size, 2)
        rr = rng.uniform(1.5, 6)
        cv2.circle(value, (int(cx), int(cy)), int(rr), float(rng.uniform(-0.11, 0.08)), -1)
    damp = smooth_noise(size, 3, 3)
    value -= 0.07 * np.clip(damp - 0.60, 0, 1) / 0.40
    img = np.clip(norm01(value), 0, 1)
    save((np.dstack([img * 226, img * 211, img * 192])).astype(np.uint8), 'tex_soil_noise.png')


if __name__ == '__main__':
    wood_grain()
    stone_tiles()
    leaf_detail()
    metal_brushed()
    bark()
    soil_noise()
    print('ALL_TEXTURES_DONE')
