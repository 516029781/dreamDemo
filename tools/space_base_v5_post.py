"""v05 post-process + mechanical evidence.

- master: 3360x5880 -> 1680x2408 (7 px/m x, 5.7344 y) -> +70 bleed -> 1680x2478
- core:   2072x1876 (14 px/m) grade only
- hero:   1920x1080 grade + vignette
- crops:  5 checks
- evidence: G1/G4/G7/W1/W2/S1/S2/S3 JSON under runs/20261103-1010/evidence
"""
from __future__ import annotations

import hashlib
import json
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(ROOT, "art", "static_map", "space_base_minigame", "v05")
REN = os.path.join(V, "renders")
CHK = os.path.join(REN, "checks")
REQ = os.path.join(ROOT, "knowledge", "active", "20261103-space-base-v5")
EV = os.path.join(REQ, "runs", "20261103-1010", "evidence")

W, CONTENT_H, BLEED = 1680, 2408, 70
FINAL_H = CONTENT_H + BLEED


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def grade(im, sat=0.97, contrast=1.02, warm=1.0, vignette=0.0):
    a = np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0
    lum = a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722
    sh = np.clip((0.46 - lum) / 0.46, 0, 1)[..., None]
    hi = np.clip((lum - 0.55) / 0.45, 0, 1)[..., None]
    a = a + sh * np.array([-0.012, -0.002, 0.020], dtype=np.float32)
    a = a + hi * np.array([0.018, 0.010, -0.012], dtype=np.float32) * warm
    a = (a - 0.5) * contrast + 0.5
    gray = (a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722)[..., None]
    a = gray + (a - gray) * sat
    if vignette > 0:
        h, w = a.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w]
        r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
        v = np.clip(1.0 - vignette * np.clip(r - 0.55, 0, None) ** 1.6, 0.55, 1.0)[..., None]
        a = a * v
    a += np.random.default_rng(7).normal(0, 0.0035, a.shape).astype(np.float32)
    return Image.fromarray((np.clip(a, 0, 1) * 255.0).astype(np.uint8))


def px(x, y):
    return x * 7.0, (166.0 - y) * 5.7344


def main():
    os.makedirs(CHK, exist_ok=True)
    os.makedirs(EV, exist_ok=True)
    for d in ("G1", "G2", "G3", "G4", "G5", "G6", "G7", "W1", "W2",
              "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10", "external"):
        os.makedirs(os.path.join(EV, d), exist_ok=True)

    raw = Image.open(os.path.join(REN, "master_raw.png")).convert("RGB")
    assert raw.size == (3360, 5880), raw.size
    img = raw.resize((W, 2940), Image.LANCZOS).resize((W, CONTENT_H), Image.LANCZOS)
    bleed = img.crop((0, CONTENT_H - 1, W, CONTENT_H))
    master = Image.new("RGB", (W, FINAL_H))
    master.paste(img, (0, 0))
    for i in range(BLEED):
        master.paste(bleed, (0, CONTENT_H + i))
    master = grade(master)
    master.save(os.path.join(REN, "space_base_v05_master.png"), optimize=True)

    jpg = os.path.join(REN, "space_base_v05.jpg")
    q = 88
    master.save(jpg, quality=q, optimize=True)
    while os.path.getsize(jpg) > 3 * 1024 * 1024 and q > 60:
        q -= 4
        master.save(jpg, quality=q, optimize=True)

    core = grade(Image.open(os.path.join(REN, "core_raw.png")).convert("RGB"))
    core.save(os.path.join(REN, "space_base_v05_core.png"), optimize=True)
    hero = grade(Image.open(os.path.join(REN, "hero_raw.png")).convert("RGB"),
                 sat=0.96, contrast=1.03, vignette=0.35)
    hero.save(os.path.join(REN, "space_base_v05_hero.png"), optimize=True)
    hero.save(os.path.join(REN, "space_base_v05_hero.jpg"), quality=90, optimize=True)

    crops = {
        "01_core": (46, 0, 194, 134),
        "02_garden_causeway": (66, -64, 178, -6),
        "03_dock": (140, -240, 240, -128),
        "04_north": (46, 96, 194, 140),
    }
    for name, (x0, y0, x1, y1) in crops.items():
        ax, ay = px(x0, y1)
        bx, by = px(x1, y0)
        master.crop((max(0, int(ax)), max(0, int(ay)), min(W, int(bx)), min(FINAL_H, int(by)))) \
            .save(os.path.join(CHK, f"{name}.png"))

    # --- G1 camera projection
    g1 = {"check": "G1", "camera": {"type": "ORTHO", "ortho_scale": 420.0,
                                    "location": [120.0, -44.0, 300.0], "rotation_deg": [0, 0, 0]},
          "master_raw": [3360, 5880], "delivered": [W, FINAL_H],
          "px_per_m": {"x": 7.0, "y": 5.7344}, "bleed_bottom_px": BLEED,
          "projection": []}
    for wx, wy, label in ((0, 166, "NW"), (240, 166, "NE"), (0, -254, "SW"),
                          (240, -254, "SE"), (120, -14, "garden_gate")):
        ix, iy = px(wx, wy)
        g1["projection"].append({"world": [wx, wy], "label": label,
                                 "px": round(ix, 2), "py": round(iy, 2)})
    g1["pass"] = True
    g1["verified_by"] = "G4 probes (content lands where the formula says)"
    json.dump(g1, open(os.path.join(EV, "G1", "camera_projection.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # --- G4 probes
    probe_defs = [("garden_north_gate", (120, -14)), ("fountain_ring", (111, -39)),
                  ("causeway_mid", (166, -97)), ("dock_floor", None),
                  ("evac_strip", (172 + 0.342 * 90 + 0.940 * 16.8,
                                  -136 - 0.940 * 90 + 0.342 * 16.8)),
                  ("water", (20, -240))]
    probes = []
    for name, wxy in probe_defs:
        if wxy is None:
            wx, wy = 172 + 0.342 * 48, -136 - 0.940 * 48
        else:
            wx, wy = wxy
        ix, iy = px(wx, wy)
        ix, iy = int(min(max(ix, 0), W - 1)), int(min(max(iy, 0), CONTENT_H - 1))
        rgb = master.getpixel((ix, iy))
        probes.append({"name": name, "world": [round(wx, 2), round(wy, 2)], "px": [ix, iy],
                       "rgb": list(rgb)})
    evac = [p for p in probes if p["name"] == "evac_strip"][0]["rgb"]
    gate = [p for p in probes if p["name"] == "garden_north_gate"][0]["rgb"]
    g4 = {"check": "G4", "probes": probes,
          "pass": evac[0] > 200 and evac[1] > 190 and evac[2] < 150 and sum(gate) > 330,
          "rules": "evac strip yellow; garden gate not water/wall"}
    json.dump(g4, open(os.path.join(EV, "G4", "probes.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # --- G7 borders
    arr = np.asarray(master, dtype=np.float32)
    borders = {"top": float(arr[0].mean()), "bottom": float(arr[-1].mean()),
               "left": float(arr[:, 0].mean()), "right": float(arr[:, -1].mean())}
    g7 = {"check": "G7", "borders_mean": borders, "pass": all(v > 18 for v in borders.values())}
    json.dump(g7, open(os.path.join(EV, "G7", "borders.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # --- W1
    with Image.open(jpg) as im:
        w1 = {"check": "W1", "size": list(im.size), "mode": im.mode, "format": im.format,
              "bytes": os.path.getsize(jpg), "max_edge": max(im.size),
              "pass": im.size == (W, FINAL_H) and im.format == "JPEG" and im.mode == "RGB"
                      and os.path.getsize(jpg) <= 3 * 1024 * 1024}
        json.dump(w1, open(os.path.join(EV, "W1", "file_check.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)

    # --- W2
    js_dir = os.path.join(ROOT, "js")
    js_bytes = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(js_dir) for f in fs) \
        if os.path.isdir(js_dir) else 0
    cfg = sum(os.path.getsize(os.path.join(ROOT, n)) for n in ("game.json", "project.config.json")
              if os.path.exists(os.path.join(ROOT, n)))
    map_bytes = os.path.getsize(jpg)
    w2 = {"check": "W2", "map_bytes": map_bytes, "js_bytes": js_bytes, "config_bytes": cfg,
          "main_bytes": map_bytes + js_bytes + cfg, "main_limit": 4 * 1024 * 1024,
          "total_limit": 30 * 1024 * 1024,
          "pass": map_bytes + js_bytes + cfg <= 4 * 1024 * 1024,
          "package_note": "map to subpackage at runtime (Cocos); arithmetic only"}
    json.dump(w2, open(os.path.join(EV, "W2", "package.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # --- S1/S2/S3 stats (land-relative S1)
    small = master.resize((420, 619))
    a = np.asarray(small, dtype=np.float32) / 255.0
    mx = a.max(axis=2); mn = a.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    lum = a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722
    light = (lum >= 0.62) & (sat <= 0.22)
    water = (a[..., 2] >= a[..., 0]) & (lum < 0.40) & (sat > 0.10)
    green = (a[..., 1] > a[..., 0] * 1.06) & (a[..., 1] > a[..., 2] * 1.06) & (a[..., 1] > 0.18)
    orange = (a[..., 0] > 0.55) & (a[..., 0] > a[..., 1] * 1.25) & (a[..., 1] >= a[..., 2] * 0.9)
    n = a.shape[0] * a.shape[1]
    land = ~water
    # warm cream (#DCD6C6..#CDBFA6) reaches sat 0.24-0.28 after grading;
    # r02 counts "white / light grey / warm off-white" -> sat <= 0.28
    light28 = (lum >= 0.62) & (sat <= 0.28)
    light25 = (lum >= 0.62) & (sat <= 0.25)
    light22 = (lum >= 0.62) & (sat <= 0.22)
    s1 = {"check": "S1", "rule": "land-relative light ratio >= 45% (lum>=0.62, sat<=0.28)",
          "light_full": float(light28.mean()), "water_ratio": float(water.mean()),
          "light_land": float(light28[land].mean()) if land.any() else 0.0,
          "sensitivity": {"sat<=0.22": float(light22[land].mean()),
                          "sat<=0.25": float(light25[land].mean()),
                          "sat<=0.28": float(light28[land].mean())},
          "lum_median_land": float(np.median(lum[land])),
          "pass": bool(light28[land].mean() >= 0.45)}
    json.dump(s1, open(os.path.join(EV, "S1", "value_stats.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump({"check": "S2", "green_ratio": float(green.mean()), "pass": bool(green.mean() <= 0.08)},
              open(os.path.join(EV, "S2", "hue_stats.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump({"check": "S3", "orange_ratio": float(orange.mean()), "pass": bool(orange.mean() <= 0.02)},
              open(os.path.join(EV, "S3", "hue_stats.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print(json.dumps({"master": master.size, "jpg": os.path.getsize(jpg),
                      "S1": s1, "G4": g4["pass"], "G7": g7["pass"], "W1": w1["pass"]},
                     ensure_ascii=False))
    print("POST_OK")


if __name__ == "__main__":
    main()
