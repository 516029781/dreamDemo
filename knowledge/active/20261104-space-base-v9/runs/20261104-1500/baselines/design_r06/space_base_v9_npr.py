"""NPR finishing for the v09 near views (C-tier: cel bands + ink outline + haze).

Blender gives a denoised beauty pass plus a normalised depth pass (1 = near,
0 = far).  Everything below is 2D finishing, so the look is fully re-tunable
without re-rendering:

  1. aerial perspective  - distance haze so the far end of the street recedes
  2. cel banding         - quantise luminance, keep hue/chroma (never quantise RGB)
  3. ink outline         - depth discontinuity (structure) + luminance edges
  4. grade               - cool shadows / warm highlights, lifted blacks
  5. paper               - grain, vignette, 1.2 px jitter on the silhouette

Usage:
  python tools/space_base_v9_npr.py [src_dir] [dst_dir]
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

SRC = sys.argv[1] if len(sys.argv) > 1 else "art/static_map/space_base_minigame/v09/renders/near"
DST = sys.argv[2] if len(sys.argv) > 2 else "art/static_map/space_base_minigame/v09/renders/near_npr"

HAZE = np.array([0.72, 0.78, 0.79], dtype=np.float32)   # cool sea haze
DARK = np.array([0.16, 0.18, 0.21], dtype=np.float32)   # ink colour


def load(path, mode="RGB"):
    return np.asarray(Image.open(path).convert(mode), dtype=np.float32) / 255.0


def save(a, path):
    Image.fromarray(np.clip(a * 255.0, 0, 255).astype(np.uint8)).save(path)


def luma(a):
    return a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722


def box(a, r):
    """Cheap separable box blur via PIL (fast enough for 2.5k stills)."""
    img = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
    img = img.filter(ImageFilter.BoxBlur(r))
    return np.asarray(img, dtype=np.float32) / 255.0


def aerial(a, z, strength=0.34, falloff=120.0):
    """z: 1 near, 0 far."""
    t = np.clip(1.0 - z, 0.0, 1.0)
    f = (1.0 - np.exp(-t * (220.0 / falloff))) * strength
    f = f[..., None]
    return a * (1.0 - f) + HAZE[None, None, :] * f


def cel(a, levels=5, amount=0.72):
    l = luma(a)
    l = np.maximum(l, 1e-4)
    # smooth-step quantisation keeps the band edges soft (no aliasing shimmer)
    q = np.floor(l * levels) / levels
    frac = (l * levels) - np.floor(l * levels)
    q = q + np.clip((frac - 0.55) * 3.4, 0.0, 1.0) / levels
    q = np.maximum(q, 1e-4)
    scale = (q / l)[..., None]
    out = a * scale
    return a * (1.0 - amount) + out * amount


def ink(a, z, lw=1.0, dark=0.80):
    gz = np.zeros_like(z)
    gz[:, :-1] += np.abs(np.diff(z, axis=1))
    gz[:-1, :] += np.abs(np.diff(z, axis=0))
    # structural edges: any real depth step
    e = (box(gz, 1) > 0.012).astype(np.float32)
    # luminance edges give the small props a line as well
    l = luma(a)
    gl = np.zeros_like(l)
    gl[:, :-1] += np.abs(np.diff(l, axis=1))
    gl[:-1, :] += np.abs(np.diff(l, axis=0))
    e2 = (box(gl, 1) > 0.085).astype(np.float32)
    edge = np.maximum(e, e2 * 0.8)
    if lw > 1.0:
        edge = np.maximum(edge, box(edge, 1))
    edge = edge[..., None] * dark
    return a * (1.0 - edge) + DARK[None, None, :] * edge


def grade(a):
    l = luma(a)[..., None]
    shadow = np.clip(1.0 - l * 2.4, 0.0, 1.0)
    high = np.clip(l * 1.5 - 0.25, 0.0, 1.0)
    a = a + shadow * np.array([-0.020, 0.004, 0.030], dtype=np.float32)
    a = a + high * np.array([0.045, 0.020, -0.020], dtype=np.float32)
    a = (a - 0.5) * 1.10 + 0.5
    a = np.clip(a, 0.0, 1.0) ** 0.94
    return np.clip(a, 0.0, 1.0)


def paper(a, seed=7):
    rng = np.random.default_rng(seed)
    h, w = a.shape[:2]
    grain = rng.normal(0.0, 1.0, (h // 2, w // 2)).astype(np.float32)
    grain = np.asarray(Image.fromarray(((grain * 0.5 + 0.5) * 255).astype(np.uint8))
                       .resize((w, h), Image.BILINEAR), dtype=np.float32) / 255.0 - 0.5
    a = a * (1.0 + grain[..., None] * 0.055)
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    vig = np.clip(1.0 - 0.16 * np.clip(r - 0.55, 0, 2) ** 1.6, 0.0, 1.0)[..., None]
    return np.clip(a * vig, 0.0, 1.0)


def main():
    os.makedirs(DST, exist_ok=True)
    names = [f[:-4] for f in sorted(os.listdir(SRC))
             if f.endswith(".png") and not f.endswith("_z.png")]
    if not names:
        print("NO_INPUT")
        return
    for n in names:
        zpath = os.path.join(SRC, f"{n}_z.png")
        if not os.path.exists(zpath):
            print("NO_DEPTH", n)
            continue
        a = load(os.path.join(SRC, f"{n}.png"))
        z = load(zpath, "L")
        a = aerial(a, z)
        a = cel(a, levels=5, amount=0.72)
        a = ink(a, z)
        a = grade(a)
        a = paper(a)
        save(a, os.path.join(DST, f"{n}_npr.png"))
        print("NPR_OK", n, a.shape[:2])
    print("NPR_ALL_OK")


if __name__ == "__main__":
    main()
