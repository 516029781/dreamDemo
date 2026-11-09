"""Derive the v14 delivery set from the 1680x2478 master_raw.png.

Run BEFORE render_v14_raw.py overwrites master_raw.png with the 3360x5880
high-res version (space_base_check_v7.py expects both).

    python tools/make_v14_delivery.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path("C:/软件/鼠鼠")
CAND = ROOT / "art/static_map/space_base_minigame/v14"
REN = CAND / "renders"
CHECKS = REN / "checks"
CHECKS.mkdir(parents=True, exist_ok=True)

master = Image.open(REN / "master_raw.png").convert("RGB")
hero = Image.open(REN / "hero_raw.png").convert("RGB")
assert master.size == (1680, 2478), master.size

# v14 own naming
master.save(REN / "space_base_v14_master.png")
master.save(REN / "space_base_v14.jpg", quality=88, optimize=True)
hero.save(REN / "space_base_v14_hero.png")

# HARNESS_SPEC r14 deliverable.files still uses v11 names -> produce both
for src, names in ((master, ("space_base_v11_master.png", "space_base_v11.jpg")),
                   (hero, ("space_base_v11_hero.png",))):
    for n in names:
        if n.endswith(".jpg"):
            src.save(REN / n, quality=88, subsampling=1)
        else:
            src.save(REN / n)

master.crop((300, 120, 1380, 1100)).resize((2072, 1876), Image.LANCZOS).save(
    REN / "space_base_v11_core.png")
master.crop((300, 120, 1380, 1100)).resize((2072, 1876), Image.LANCZOS).save(
    REN / "space_base_v14_core.png")

boxes = (
    ("01_core", (300, 100, 1380, 1100)),
    ("02_avenue_bridge", (500, 900, 1300, 1700)),
    ("03_peninsula", (600, 1650, 1400, 2478)),
    ("04_avenue_head", (400, 700, 1200, 1450)),
    ("05_g5_pair", (700, 1200, 1300, 2050)),
)
for name, box in boxes:
    master.crop(box).save(CHECKS / (name + ".png"))

# front/back same-camera comparisons
v13 = ROOT / "art/static_map/space_base_minigame/v13/renders/space_base_v13_master.png"
old = Image.open(v13).convert("RGB")
H = 1100
aw, bw = int(old.width * H / old.height), int(master.width * H / master.height)
cmp_ = Image.new("RGB", (aw + bw + 30, H + 44), (245, 243, 238))
cmp_.paste(old.resize((aw, H), Image.LANCZOS), (0, 44))
cmp_.paste(master.resize((bw, H), Image.LANCZOS), (aw + 30, 44))
cmp_.save(REN / "_cmp_master.png")

old_hero = Image.open(ROOT / "art/static_map/space_base_minigame/v13/renders/hero_raw.png").convert("RGB")
HH = 540
aw2, bw2 = int(old_hero.width * HH / old_hero.height), int(hero.width * HH / hero.height)
ch = Image.new("RGB", (aw2 + bw2 + 24, HH), (245, 243, 238))
ch.paste(old_hero.resize((aw2, HH), Image.LANCZOS), (0, 0))
ch.paste(hero.resize((bw2, HH), Image.LANCZOS), (aw2 + 24, 0))
ch.save(REN / "_cmp_hero.png")

files = [
    "scene.blend", "renders/master_raw.png", "renders/hero_raw.png", "renders/route.png",
    "renders/space_base_v14_master.png", "renders/space_base_v14.jpg",
    "renders/space_base_v14_hero.png", "renders/space_base_v14_core.png",
    "renders/space_base_v11_master.png", "renders/space_base_v11.jpg",
    "renders/space_base_v11_hero.png", "renders/space_base_v11_core.png",
    "renders/_cmp_master.png", "renders/_cmp_hero.png",
    *["renders/checks/%s.png" % n for n, _ in boxes],
    "REVIEW.md", "DEVLOG.md", "GATE_REPORT.json", "DELIVERY.json",
    "REPRODUCE.md",
]
entries = []
for f in files:
    p = CAND / f
    entries.append({"path": f,
                    "sha256": hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None,
                    "bytes": p.stat().st_size if p.exists() else None})
man = {"schema": "manifest-v1", "request_id": "20261108-space-base-v14-art",
       "run_id": "20261108-2035", "candidate": "art/static_map/space_base_minigame/v14",
       "entries": entries}
(CAND / "MANIFEST.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
print("DELIVERY_IMAGES_OK", master.size, hero.size, len(files), "manifest entries")
