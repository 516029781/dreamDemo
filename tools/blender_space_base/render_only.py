"""Render-only reproduction for space_base_minigame v01.

Run:
  blender -b <copy.scene.blend> --python tools/blender_space_base/render_only.py -- \
    --out <repro.png> --res 1920x2560 --samples 16
"""
from __future__ import annotations

import argparse
import os
import sys

import bpy


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--res", default="1920x2560")
    ap.add_argument("--samples", type=int, default=16)
    return ap.parse_args(argv)


def main():
    a = parse()
    sc = bpy.context.scene
    w, h = [int(v) for v in a.res.lower().split("x")]
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = a.samples
    sc.cycles.use_denoising = True
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.filepath = os.path.abspath(a.out)
    bpy.ops.render.render(write_still=True)
    print("RENDER_ONLY_OK", a.out, w, h, a.samples)


if __name__ == "__main__":
    main()
