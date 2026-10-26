# -*- coding: utf-8 -*-
"""Deterministic procedural texture sources for V02 material separation.

Native generation only (NumPy + OpenCV PNG encode): no AI image, no diffusion.
Sources land in art/full/source/textures/; engine copies go to
demo/assets/resources/textures/. Every texture is designed so its mean
luminance stays near 0.92 - the Cocos tint carries the palette color while
the texture carries pattern only.
"""
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '.tools', 'pycv'))
import cv2

OUT_ART = os.path.join(os.path.dirname(__file__), '..', '..', 'art', 'full', 'source', 'textures')
OUT_DEMO = os.path.join(os.path.dirname(__file__), '..', '..', 'demo', 'assets', 'resources', 'textures')
rng = np.random.default_rng(20261024)


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


def wood_grain(size=512):
    u, v = np.meshgrid(np.linspace(0, 1, size), np.linspace(0, 1, size))
    streaks = np.zeros((size, size))
    for k in range(1, 9):
        amp = 0.5 / k
        ph = rng.uniform(0, 2 * np.pi)
        streaks += amp * np.sin(2 * np.pi * (v * k * rng.uniform(1.5, 3.0)
                                             + 0.35 * np.sin(2 * np.pi * u * rng.uniform(0.5, 1.2))
                                             + ph))
    grain_fine = rng.normal(0, 0.05, (size, size))
    # stretch fine noise along U (grain direction)
    kernel = np.ones((1, 31)) / 31.0
    grain = cv2.filter2D(grain_fine, -1, kernel)
    value = 0.92 + 0.080 * streaks + 0.060 * grain
    # two plank joints across V (every 0.5 m at 1 repeat = 1 m)
    for jv in (0.25, 0.75):
        d = np.abs(v - jv)
        value -= 0.14 * np.exp(-(d ** 2) / (2 * 0.004 ** 2))
    img = np.clip(norm01(value), 0, 1)
    save((np.dstack([img * 236, img * 224, img * 208])).astype(np.uint8), 'tex_wood_grain.png')


def stone_tiles(size=512, tiles=2):
    value = np.full((size, size), 0.92)
    cell = size // tiles
    for ty in range(tiles):
        for tx in range(tiles):
            b = rng.uniform(0.80, 1.00)
            value[ty * cell:(ty + 1) * cell, tx * cell:(tx + 1) * cell] *= b
    # tile edge darkening
    edge = np.zeros((size, size))
    for ty in range(tiles + 1):
        y = ty * cell
        for d in range(3):
            row = (y + d) % size
            edge[row, :] = np.maximum(edge[row, :], 0.14 - d * 0.04)
            edge[row - 1, :] = np.maximum(edge[row - 1, :], 0.14 - d * 0.04)
    for tx in range(tiles + 1):
        x = tx * cell
        for d in range(3):
            col = (x + d) % size
            edge[:, col] = np.maximum(edge[:, col], 0.14 - d * 0.04)
            edge[:, col - 1] = np.maximum(edge[:, col - 1], 0.14 - d * 0.04)
    value -= edge
    value += rng.normal(0, 0.030, (size, size))
    img = np.clip(value, 0, 1)
    save(np.dstack([img * 232, img * 226, img * 214]).astype(np.uint8), 'tex_stone_tiles.png')


def metal_brushed(size=256):
    fine = rng.normal(0, 1.0, (size, size))
    kernel = np.ones((9, 1)) / 9.0
    streaks = cv2.filter2D(fine, -1, kernel)  # vertical brush along V
    value = 0.92 + 0.09 * streaks
    img = np.clip(norm01(value) * 0.42 + 0.71, 0, 1)
    save(np.dstack([img * 225, img * 224, img * 222]).astype(np.uint8), 'tex_metal_brushed.png')


def bark(size=256):
    u, v = np.meshgrid(np.linspace(0, 1, size), np.linspace(0, 1, size))
    ridges = np.zeros((size, size))
    for k in range(1, 10):
        ph = rng.uniform(0, 2 * np.pi)
        warp = 0.25 * np.sin(2 * np.pi * (u * 2.0 + ph))
        ridges += (0.5 / k) * np.sin(2 * np.pi * (u * k * 2.2 + warp + ph))
    value = 0.92 + 0.07 * ridges + rng.normal(0, 0.03, (size, size))
    img = np.clip(norm01(value), 0, 1)
    save(np.dstack([img * 214, img * 202, img * 186]).astype(np.uint8), 'tex_bark.png')


def soil_noise(size=256):
    fine = rng.normal(0, 1.0, (size, size))
    blob = cv2.GaussianBlur(rng.normal(0, 1.0, (size, size)).astype(np.float32), (0, 0), 6)
    value = 0.92 + 0.07 * blob / (np.abs(blob).max() + 1e-6) + 0.06 * fine
    img = np.clip(value, 0, 1)
    save(np.dstack([img * 224, img * 212, img * 196]).astype(np.uint8), 'tex_soil_noise.png')


if __name__ == '__main__':
    wood_grain()
    stone_tiles()
    metal_brushed()
    bark()
    soil_noise()
    print('ALL_TEXTURES_DONE')
