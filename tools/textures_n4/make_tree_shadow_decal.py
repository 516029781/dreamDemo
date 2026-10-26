"""Turn the projected tree-shadow render into an engine decal.

Adds a modest penumbra so the silhouette does not read as a hard cutout, and
writes the placement metadata the runtime needs to line the decal up with the
trunk. The shape itself comes from bake_tree_shadow.py, i.e. real geometry.
"""
import json
import os

import numpy as np
from PIL import Image, ImageFilter

ROOT = r"C:\软件\鼠鼠"
RAW = os.path.join(ROOT, "art/candidates/candidate_n4/source/layout",
                   "ENV006_tree_shadow_raw.png")
SRC_OUT = os.path.join(ROOT, "art/candidates/candidate_n4/source/layout",
                       "ENV006_tree_shadow.png")
ENG_OUT = os.path.join(ROOT, "demo_n4/assets/resources/textures",
                       "tex_tree_shadow.png")
META = os.path.join(ROOT, "delivery/next_cycle/n4/T2/tree_shadow_meta.json")

# Sun elevation implied by the bake shear; drives how far the penumbra spreads.
BLUR_PX = 14
ALPHA_SCALING = 255.0 / 200.0   # the render is dense where foliage overlaps
MAX_ALPHA = 104
# Foliage never blocks light uniformly; a low-frequency noise field opens the
# umbra so the shade reads as dappled rather than as a flat black cutout.
DAPPLE_FREQ = 9
DAPPLE_MIN = 0.46
ORTHO_HALF = 6.192
CENTRE = (2.954, 1.419)         # Blender map space


def dapple_field(size):
    coarse = np.random.default_rng(20261025).random(
        (size // DAPPLE_FREQ + 2, size // DAPPLE_FREQ + 2))
    img = Image.fromarray((coarse * 255).astype(np.uint8), "L").resize(
        (size, size), Image.BICUBIC)
    img = img.filter(ImageFilter.GaussianBlur(size / 42.0))
    a = np.asarray(img, dtype=np.float32) / 255.0
    return DAPPLE_MIN + (1.0 - DAPPLE_MIN) * a


def main():
    os.makedirs(os.path.dirname(SRC_OUT), exist_ok=True)
    os.makedirs(os.path.dirname(ENG_OUT), exist_ok=True)
    im = Image.open(RAW).convert("RGBA")
    a = im.split()[3].filter(ImageFilter.GaussianBlur(BLUR_PX))
    a = a.point(lambda v: min(MAX_ALPHA, int(round(v * ALPHA_SCALING))))
    arr = np.asarray(a, dtype=np.float32) / 255.0
    arr = arr * dapple_field(im.size[0])
    a = Image.fromarray((arr * 255.0).astype(np.uint8), "L")
    black = Image.new("RGB", im.size, (26, 22, 18))
    out = Image.merge("RGBA", (*black.split(), a))
    out.save(SRC_OUT)
    out.save(ENG_OUT)
    meta = {
        "kind": "env006_projected_tree_shadow",
        "source_render": "art/candidates/candidate_n4/source/layout/ENV006_tree_shadow_raw.png",
        "source_geometry": "art/candidates/candidate_n4/source/environment/ENV006_autumn_tree.blend",
        "export": "demo_n4/assets/resources/textures/tex_tree_shadow.png",
        "resolution": list(out.size),
        "penumbra_blur_px": BLUR_PX,
        "max_alpha": MAX_ALPHA,
        "projection": {
            "method": "shear along sun vector onto ground plane, orthographic top render",
            "shear": [0.86, 0.50],
            "sun_elevation_deg": 45.15,
        },
        "placement": {
            "plane_size_world": [round(ORTHO_HALF * 2, 3), round(ORTHO_HALF * 2, 3)],
            "blender_centre": [CENTRE[0], CENTRE[1]],
            "engine_centre_xz": [CENTRE[0], -CENTRE[1]],
            "note": "engine Z = -Blender Y; tree base sits at engine (0,0) inside this footprint",
        },
    }
    with open(META, "w", encoding="utf-8") as handle:
        json.dump(meta, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps(meta["placement"], ensure_ascii=False))


main()
