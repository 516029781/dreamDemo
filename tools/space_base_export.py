"""Image export helpers for space_base_minigame v01.

Usage (system Python with Pillow):
  python tools/space_base_export.py flip --in raw.png --out master.png
  python tools/space_base_export.py jpeg --master master.png --out ship.jpg
  python tools/space_base_export.py checks --image ship.jpg --out-dir renders/checks
  python tools/space_base_export.py grid --image graybox.png --out-dir renders/graybox_checks
  python tools/space_base_export.py stats --image ship.jpg --out stats.json
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from PIL import Image

W, H = 1920, 2560


def flip(a):
    im = Image.open(a.input).convert("RGB")
    out = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    out.save(a.out)
    print("FLIP_OK", a.out, out.size)


def jpeg(a):
    im = Image.open(a.master).convert("RGB")
    out = im.resize((W, H), Image.Resampling.LANCZOS)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    out.save(a.out, format="JPEG", quality=a.quality, optimize=True, progressive=False)
    print("JPEG_OK", a.out, out.size, os.path.getsize(a.out))


def _crop(im, box, out):
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    im.crop(box).save(out)
    print("CROP_OK", out)


def checks(a):
    im = Image.open(a.image).convert("RGB")
    if im.size != (W, H):
        im = im.resize((W, H), Image.Resampling.LANCZOS)
    d = Path(a.out_dir)
    _crop(im, (420, 940, 1500, 2560), d / "01_core.png")
    _crop(im, (620, 0, 1700, 1620), d / "02_workshop.png")
    _crop(im, (560, 719, 1360, 1519), d / "03_south_exit.png")
    _crop(im, (560, 1604, 1360, 2404), d / "04_ceo.png")


def grid(a):
    im = Image.open(a.image).convert("RGB")
    if im.size != (W, H):
        im = im.resize((W, H), Image.Resampling.LANCZOS)
    d = Path(a.out_dir)
    xs, ys, tw, th = [0, 600, 1200], [0, 1160], 720, 1400
    n = 0
    for y in ys:
        for x in xs:
            _crop(im, (x, y, x + tw, y + th), d / f"grid_{n:02d}.png")
            n += 1


def stats(a):
    im = Image.open(a.image).convert("RGB")
    hsv = im.convert("HSV")
    w, h = im.size
    n = w * h
    white = green = orange = 0
    hch, sch, vch = hsv.split()
    hs, ss, vs = hch.getdata(), sch.getdata(), vch.getdata()
    for hh, ss_, vv in zip(hs, ss, vs):
        if ss_ < 56 and vv > 128:
            white += 1
        if 45 <= hh <= 85 and ss_ > 46 and vv > 30:
            green += 1
        if 5 <= hh <= 22 and ss_ > 90 and vv > 64:
            orange += 1
    payload = {
        "image": a.image, "size": [w, h],
        "white_light_pct": round(white * 100.0 / n, 2),
        "green_pct": round(green * 100.0 / n, 2),
        "orange_pct": round(orange * 100.0 / n, 2),
        "note": "diagnostic_only; HSV thresholds are approximate and do not replace visual review",
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print("STATS_OK", payload)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("flip"); p.add_argument("--in", dest="input", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("jpeg"); p.add_argument("--master", required=True); p.add_argument("--out", required=True); p.add_argument("--quality", type=int, default=88)
    p = sub.add_parser("checks"); p.add_argument("--image", required=True); p.add_argument("--out-dir", required=True)
    p = sub.add_parser("grid"); p.add_argument("--image", required=True); p.add_argument("--out-dir", required=True)
    p = sub.add_parser("stats"); p.add_argument("--image", required=True); p.add_argument("--out", required=True)
    a = ap.parse_args()
    {"flip": flip, "jpeg": jpeg, "checks": checks, "grid": grid, "stats": stats}[a.cmd](a)


if __name__ == "__main__":
    main()
