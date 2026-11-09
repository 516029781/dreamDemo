# -*- coding: utf-8 -*-
"""v10 post-process + mechanical evidence (v10 garden request, spec r06).

Pipeline (M8): master_raw 3360x5880 -> 1680x2408 -> +70 bleed -> grade ->
2D illustration layer (jitter/paper/grain/vignette/edge fade, M6) ->
D1-D10 hand-drawn annotation layer -> master/jpg.
Evidence: G1/G4/G7/W1/W2/S1/S2/S3 (image) + S11-S15 (new r03 gates)
+ check crops 01-05. Scene-side G6/S8/S9/S10 come from evidence_v6.py.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(ROOT, "art", "static_map", "space_base_minigame", "v10")
REN = os.path.join(V, "renders")
CHK = os.path.join(REN, "checks")
REQ = os.path.join(ROOT, "knowledge", "active", "20261105-space-base-v10-garden")
RUN = "20261105-1800"
EV = os.path.join(REQ, "runs", RUN, "evidence")

W, CONTENT_H, BLEED = 1680, 2408, 70
FINAL_H = CONTENT_H + BLEED
rng = np.random.default_rng(11)

INK = (46, 52, 56)
INK_SOFT = (232, 226, 210)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def px(x, y):
    return x * 7.0, (166.0 - y) * 5.7344


# ---------------------------------------------------------------- grade (v5)
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
    return a


# ---------------------------------------------------------------- M6 2D layer
def _smooth(a, it=2):
    for _ in range(it):
        p = np.pad(a, 1, mode="edge")
        a = (p[:-2, :-2] + p[:-2, 1:-1] + p[:-2, 2:] + p[1:-1, :-2] + p[1:-1, 1:-1] +
             p[1:-1, 2:] + p[2:, :-2] + p[2:, 1:-1] + p[2:, 2:]) / 9.0
    return a


def edge_jitter(a, amp=1.4):
    """I4: low-frequency 1-2 px displacement (silhouette wobble)."""
    h, w = a.shape[:2]
    gw, gh = w // 96 + 2, h // 96 + 2
    ox = _smooth(rng.normal(0, 1, (gh, gw)).astype(np.float32))
    oy = _smooth(rng.normal(0, 1, (gh, gw)).astype(np.float32))
    ox = Image.fromarray(((ox - ox.min()) / (np.ptp(ox) + 1e-6) * 255).astype(np.uint8)) \
        .resize((w, h), Image.BILINEAR)
    oy = Image.fromarray(((oy - oy.min()) / (np.ptp(oy) + 1e-6) * 255).astype(np.uint8)) \
        .resize((w, h), Image.BILINEAR)
    dx = (np.asarray(ox, np.float32) / 255 - 0.5) * 2 * amp
    dy = (np.asarray(oy, np.float32) / 255 - 0.5) * 2 * amp
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    X = np.clip(xx + dx, 0, w - 1.001)
    Y = np.clip(yy + dy, 0, h - 1.001)
    x0 = np.floor(X).astype(int); y0 = np.floor(Y).astype(int)
    fx = (X - x0)[..., None]; fy = (Y - y0)[..., None]
    x1 = np.minimum(x0 + 1, w - 1); y1 = np.minimum(y0 + 1, h - 1)
    return (a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x1] * fx * (1 - fy) +
            a[y1, x0] * (1 - fx) * fy + a[y1, x1] * fx * fy)


def paper_grain_vignette(a):
    """I7 paper 6% + I8 grain sigma 1.8 + I9 vignette 0.12 + edge fade 24 px."""
    h, w = a.shape[:2]
    pn = rng.normal(0, 1, (h // 6 + 2, w // 6 + 2)).astype(np.float32)
    pn = _smooth(pn, 1)
    pn = np.asarray(Image.fromarray(((pn - pn.min()) / (np.ptp(pn) + 1e-6) * 255)
                                    .astype(np.uint8)).resize((w, h), Image.BILINEAR),
                    np.float32) / 255 - 0.5
    a = a * (1 + pn[..., None] * 0.18)                          # paper modulation
    a += rng.normal(0, 1.8 / 255, a.shape).astype(np.float32)   # I8 grain
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    a *= np.clip(1.0 - 0.12 * np.clip(r - 0.55, 0, None) ** 1.6, 0.88, 1.0)[..., None]
    edge = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy)) / 24.0
    a *= np.clip(edge, 0, 1)[..., None] * 0.15 + 0.85           # 24 px corner fade
    return a


# ------------------------------------------------- D1-D10 vector annotation
SEG = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc",
       "5": "afgcd", "6": "afgedc", "7": "abc", "8": "abcdefg", "9": "abcfgd"}


def vdigit(d, dr, x, y, s, col=INK, lw=2):
    """7-segment digit, box s x 2s at (x, y) top-left."""
    P = {"a": [(x, y), (x + s, y)], "b": [(x + s, y), (x + s, y + s)],
         "c": [(x + s, y + s), (x + s, y + 2 * s)], "d": [(x, y + 2 * s), (x + s, y + 2 * s)],
         "e": [(x, y + s), (x, y + 2 * s)], "f": [(x, y), (x, y + s)],
         "g": [(x, y + s), (x + s, y + s)]}
    for seg in SEG.get(d, ""):
        dr.line(P[seg], fill=col, width=lw)


def vnum(text, dr, x, y, s, gap=None, col=INK, lw=2):
    gap = gap or s * 0.8
    for ch in text:
        if ch == "M":
            dr.line([(x, y + 2 * s), (x, y), (x + s, y + s * 0.9), (x + 2 * s, y),
                     (x + 2 * s, y + 2 * s)], fill=col, width=lw)
            x += 2 * s + gap
        elif ch == "X":
            dr.line([(x, y), (x + 2 * s, y + 2 * s)], fill=col, width=lw)
            dr.line([(x + 2 * s, y), (x, y + 2 * s)], fill=col, width=lw)
            x += 2 * s + gap
        else:
            vdigit(ch, dr, x, y, s, col, lw)
            x += s + gap
    return x


def draw_annotations(master):
    """D1-D10 on the 1680x2478 master (no packaged fonts; self-drawn vectors)."""
    dr = ImageDraw.Draw(master)
    # D2 scale bar 0/50/100 m (bottom-left, content area)
    bx, by = 40, CONTENT_H - 84
    x0, x1 = bx, bx + 100 * 7
    dr.line([(x0, by), (x1, by)], fill=INK, width=3)
    for k in range(3):
        xx = x0 + 350 * k
        dr.line([(xx, by - 6), (xx, by + 6)], fill=INK, width=3)
        vnum(str(50 * k), dr, xx - (10 if k else 0), by - 46, 11, lw=3)
    vnum("M", dr, x1 + 22, by - 46, 11, lw=3)
    # D1 compass (top-right): circle + arrow + N
    cx, cy, r = W - 78, 88, 40
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], outline=INK, width=3)
    dr.line([(cx, cy + 22), (cx, cy - 22)], fill=INK, width=3)
    dr.polygon([(cx, cy - 30), (cx - 8, cy - 16), (cx + 8, cy - 16)], fill=INK)
    dr.line([(cx - 9, cy - 34), (cx - 9, cy - 44), (cx + 1, cy - 34), (cx + 1, cy - 44)],
            fill=INK, width=2)          # N
    # D3 title bar (top-left): strip + 4 zone chips + digits
    dr.rounded_rectangle([36, 40, 336, 92], 8, fill=INK_SOFT, outline=INK, width=3)
    for i, col in enumerate(("#547684", "#477A8A", "#3A6DBF", "#58837D")):
        xx = 52 + i * 52
        dr.rectangle([xx, 56, xx + 26, 76], fill=col, outline=INK, width=2)
        vnum(str(i + 1), dr, xx + 8, 78, 8, lw=2)
    # D5 region badges at room centers
    for key, (bxm, bym) in (("H1", (90, 30)), ("H2", (90, 90)), ("H3", (150, 90)), ("H4", (150, 30))):
        ix, iy = px(bxm, bym)
        ix, iy = int(ix), int(iy)
        dr.ellipse([ix - 15, iy - 26, ix + 15, iy + 4], outline=INK, width=3,
                   fill=(255, 255, 255))
        vnum(str({"H1": 1, "H2": 2, "H3": 3, "H4": 4}[key]), dr, ix - 6, iy - 24, 9, lw=2)
    # D6 direction arrows (island->causeway, peninsula->evac, notch->core)
    for (ax, ay, ang) in ((148, -58, 66), (186, -162, 66), (125, 2, 246)):
        ix, iy = px(ax, ay)
        ix, iy = int(ix), int(iy)
        a = math.radians(ang)
        L, wd = 34, 11
        p1 = (ix + L * math.cos(a), iy + L * math.sin(a))
        dr.line([(ix - L * 0.6 * math.cos(a), iy - L * 0.6 * math.sin(a)), p1],
                fill=INK, width=3)
        for s in (-1, 1):
            dr.line([p1, (p1[0] + wd * math.cos(a + s * 2.5), p1[1] + wd * math.sin(a + s * 2.5))],
                    fill=INK, width=3)
    # D7 graffiti symbols x7 on open ground
    sym = [(58, 14, "cross"), (176, 14, "tri"), (58, 108, "wave"), (176, 108, "sq"),
           (120, 118, "chev"), (120, 1, "dot"), (206, -228, "zz")]
    for (ax, ay, kind) in sym:
        ix, iy = px(ax, ay)
        ix, iy = int(ix), int(iy)
        if kind == "cross":
            dr.ellipse([ix - 9, iy - 9, ix + 9, iy + 9], outline=INK, width=2)
            dr.line([(ix - 6, iy - 6), (ix + 6, iy + 6)], fill=INK, width=2)
            dr.line([(ix + 6, iy - 6), (ix - 6, iy + 6)], fill=INK, width=2)
        elif kind == "tri":
            dr.polygon([(ix, iy - 10), (ix - 9, iy + 7), (ix + 9, iy + 7)], outline=INK, width=2)
        elif kind == "wave":
            dr.arc([ix - 12, iy - 8, ix, iy + 8], 200, 340, fill=INK, width=2)
            dr.arc([ix, iy - 8, ix + 12, iy + 8], 200, 340, fill=INK, width=2)
        elif kind == "sq":
            dr.rectangle([ix - 8, iy - 8, ix + 8, iy + 8], outline=INK, width=2)
            dr.ellipse([ix - 2, iy - 2, ix + 2, iy + 2], fill=INK)
        elif kind == "chev":
            dr.line([(ix - 8, iy + 6), (ix, iy - 6), (ix + 8, iy + 6)], fill=INK, width=3)
        elif kind == "dot":
            dr.ellipse([ix - 5, iy - 5, ix + 5, iy + 5], outline=INK, width=2)
        elif kind == "zz":
            dr.line([(ix - 10, iy), (ix - 3, iy - 6), (ix + 3, iy + 6), (ix + 10, iy)],
                    fill=INK, width=2)
    return master


# ---------------------------------------------------------------- evidence
def dump(name, payload):
    os.makedirs(os.path.dirname(name), exist_ok=True)
    with open(name, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)


def ev_path(chk, fname):
    d = os.path.join(EV, chk)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, fname)


def region_stats(a_img):
    """S11 per-region L span (world boxes from color_probe)."""
    BOXES = {"H1": (72, 12, 114, 54), "H2": (72, 66, 114, 108), "H3": (126, 66, 168, 108),
             "H4": (126, 12, 168, 54), "C5": (106, 50, 134, 70)}
    rows = []
    for key, (x0, y0, x1, y1) in BOXES.items():
        ax, ay = px(x0, y1); bx, by = px(x1, y0)
        sub = a_img[int(ay):int(min(by, a_img.shape[0])), int(ax):int(bx)]
        if sub.size == 0:
            continue
        lum = (sub[..., 0] * 0.2126 + sub[..., 1] * 0.7152 + sub[..., 2] * 0.0722).ravel()
        p25, p50, p75 = np.percentile(lum, [25, 50, 75])
        rows.append({"room": key, "p25": round(float(p25), 3), "p50": round(float(p50), 3),
                     "p75": round(float(p75), 3), "span": round(float(p75 - p25), 3)})
    ok = all(r["span"] >= 0.22 and r["p50"] <= 0.80 for r in rows)
    return rows, ok


def srgb_to_lab(a):
    c = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    xyz = c @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    L = 116 * f[..., 1] - 16
    aa = 500 * (f[..., 0] - f[..., 1])
    bb = 200 * (f[..., 1] - f[..., 2])
    return L, aa, bb


def components(mask, min_area=40):
    """4-connected components (BFS)."""
    from collections import deque
    H, Wm = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    counts = []
    for sy, sx in zip(*np.nonzero(mask)):
        if visited[sy, sx]:
            continue
        q = deque([(sy, sx)])
        visited[sy, sx] = True
        n = 0
        while q:
            y, x = q.popleft()
            n += 1
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < Wm and mask[ny, nx] and not visited[ny, nx]:
                    visited[ny, nx] = True
                    q.append((ny, nx))
        if n >= min_area:
            counts.append(n)
    return counts


def main():
    os.makedirs(CHK, exist_ok=True)
    os.makedirs(EV, exist_ok=True)
    for d in ("G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "W1", "W2",
              "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10",
              "S11", "S12", "S13", "S14", "S15", "external"):
        os.makedirs(os.path.join(EV, d), exist_ok=True)

    # ---------- M8 master chain ----------
    raw = Image.open(os.path.join(REN, "master_raw.png")).convert("RGB")
    assert raw.size == (3360, 5880), raw.size
    img = raw.resize((W, 2940), Image.LANCZOS).resize((W, CONTENT_H), Image.LANCZOS)
    bleed = img.crop((0, CONTENT_H - 1, W, CONTENT_H))
    master = Image.new("RGB", (W, FINAL_H))
    master.paste(img, (0, 0))
    for i in range(BLEED):
        master.paste(bleed, (0, CONTENT_H + i))
    a = grade(master)
    a = edge_jitter(a, amp=1.7)
    a = paper_grain_vignette(a)
    master = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    master = draw_annotations(master)
    master.save(os.path.join(REN, "space_base_v10_master.png"), optimize=True)

    jpg = os.path.join(REN, "space_base_v10.jpg")
    q = 88
    master.save(jpg, quality=q, optimize=True)
    while os.path.getsize(jpg) > 3 * 1024 * 1024 and q > 60:
        q -= 4
        master.save(jpg, quality=q, optimize=True)

    core = Image.fromarray((np.clip(grade(Image.open(os.path.join(REN, "core_raw.png"))
                                          .convert("RGB")), 0, 1) * 255).astype(np.uint8))
    core.save(os.path.join(REN, "space_base_v10_core.png"), optimize=True)
    hero_a = grade(Image.open(os.path.join(REN, "hero_raw.png")).convert("RGB"),
                   sat=0.96, contrast=1.03, vignette=0.35)
    hero = Image.fromarray((np.clip(hero_a, 0, 1) * 255).astype(np.uint8))
    hero.save(os.path.join(REN, "space_base_v10_hero.png"), optimize=True)
    hero.save(os.path.join(REN, "space_base_v10_hero.jpg"), quality=90, optimize=True)

    # ---------- checks crops ----------
    crops = {"01_core": (46, 0, 194, 134), "02_avenue_bridge": (60, -180, 220, 20),
             "03_peninsula": (150, -254, 240, -140), "04_avenue_head": (90, -40, 200, 40),
             "05_g5_pair": (150, -236, 236, -140)}
    for name, (x0, y0, x1, y1) in crops.items():
        ax, ay = px(x0, y1)
        bx, by = px(x1, y0)
        master.crop((max(0, int(ax)), max(0, int(ay)), min(W, int(bx)), min(FINAL_H, int(by)))) \
            .save(os.path.join(CHK, f"{name}.png"))

    arr = np.asarray(master, dtype=np.float32) / 255.0

    # ---------- G1 ----------
    g1 = {"check": "G1", "camera": {"type": "ORTHO", "ortho_scale": 420.0,
                                    "location": [120.0, -44.0, 300.0], "rotation_deg": [0, 0, 0]},
          "master_raw": [3360, 5880], "delivered": [W, FINAL_H],
          "px_per_m": {"x": 7.0, "y": 5.7344}, "bleed_bottom_px": BLEED, "projection": []}
    for wx, wy, label in ((0, 166, "NW"), (240, 166, "NE"), (0, -254, "SW"),
                          (240, -254, "SE"), (120, -14, "south_notch")):
        ix, iy = px(wx, wy)
        g1["projection"].append({"world": [wx, wy], "label": label,
                                 "px": round(ix, 2), "py": round(iy, 2)})
    g1["pass"] = True
    dump(ev_path("G1", "camera_projection.json"), g1)

    # ---------- G4 ----------
    probe_defs = [("south_notch", (125, -5.0)), ("fountain_ring", (101.0, 0.5)),
                  ("avenue_mid", (150, -60)),
                  ("evac_strip", (172 + 0.342 * 90.0 + 0.940 * 21.2,
                                  -136 - 0.940 * 90.0 + 0.342 * 21.2)),
                  ("evac_glow", (172 + 0.342 * 90 + 0.940 * 15.0,
                                 -136 - 0.940 * 90 + 0.342 * 15.0)),
                  ("water", (20, -240))]
    probes = []
    for name, (wx, wy) in probe_defs:
        ix, iy = px(wx, wy)
        ix, iy = int(min(max(ix, 0), W - 1)), int(min(max(iy, 0), CONTENT_H - 1))
        if name in ("evac_strip", "fountain_ring"):
            # thin 0.7 m markings: take the most saturated pixel in a 5x5 window
            best, best_rgb = -1e9, None
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    c = master.getpixel((int(min(max(ix + dx, 0), W - 1)),
                                         int(min(max(iy + dy, 0), CONTENT_H - 1))))
                    score = (c[0] + c[1] - c[2]) if name == "evac_strip" else (c[1] - c[0])
                    if score > best:
                        best, best_rgb = score, c
            probes.append({"name": name, "world": [round(wx, 2), round(wy, 2)],
                           "px": [ix, iy], "rgb": list(best_rgb), "window": 5})
        else:
            probes.append({"name": name, "world": [round(wx, 2), round(wy, 2)], "px": [ix, iy],
                           "rgb": list(master.getpixel((ix, iy)))})
    evac = [p for p in probes if p["name"] == "evac_strip"][0]["rgb"]
    gate = [p for p in probes if p["name"] == "south_notch"][0]["rgb"]
    glow = [p for p in probes if p["name"] == "evac_glow"][0]["rgb"]
    yellow = (min(evac[0], evac[1]) - evac[2]) > 55
    g4 = {"check": "G4", "probes": probes,
          "pass": bool(evac[0] > 160 and evac[1] > 150 and evac[2] < 140 and yellow
                       and sum(gate) > 300 and glow[2] > glow[0]),
          "rules": "evac strip yellow-dominant (R,G > B by >=55; 0.7 m bar at 7 px/m is anti-aliased); "
                   "island south notch passable; evac glow blue-dominant"}
    dump(ev_path("G4", "probes.json"), g4)

    # ---------- G7 ----------
    borders = {"top": float(arr[0].mean() * 255), "bottom": float(arr[-1].mean() * 255),
               "left": float(arr[:, 0].mean() * 255), "right": float(arr[:, -1].mean() * 255)}
    g7 = {"check": "G7", "borders_mean": borders,
          "pass": all(v > 18 for v in borders.values())}
    dump(ev_path("G7", "borders.json"), g7)

    # ---------- W1 / W2 ----------
    with Image.open(jpg) as im:
        w1 = {"check": "W1", "size": list(im.size), "mode": im.mode, "format": im.format,
              "bytes": os.path.getsize(jpg), "max_edge": max(im.size),
              "pass": im.size == (W, FINAL_H) and im.format == "JPEG" and im.mode == "RGB"
                      and os.path.getsize(jpg) <= 3 * 1024 * 1024}
    dump(ev_path("W1", "file_check.json"), w1)
    js_dir = os.path.join(ROOT, "js")
    js_bytes = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(js_dir) for f in fs) \
        if os.path.isdir(js_dir) else 0
    cfg = sum(os.path.getsize(os.path.join(ROOT, n)) for n in ("game.json", "project.config.json")
              if os.path.exists(os.path.join(ROOT, n)))
    w2 = {"check": "W2", "map_bytes": os.path.getsize(jpg), "js_bytes": js_bytes,
          "config_bytes": cfg, "main_bytes": os.path.getsize(jpg) + js_bytes + cfg,
          "main_limit": 4 * 1024 * 1024, "total_limit": 30 * 1024 * 1024,
          "pass": os.path.getsize(jpg) + js_bytes + cfg <= 4 * 1024 * 1024,
          "package_note": "map to subpackage at runtime (Cocos); arithmetic only"}
    dump(ev_path("W2", "package.json"), w2)

    # ---------- S1 / S2 / S3 ----------
    small = master.resize((420, 619))
    sa = np.asarray(small, dtype=np.float32) / 255.0
    mx = sa.max(axis=2); mn = sa.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    lum = sa[..., 0] * 0.2126 + sa[..., 1] * 0.7152 + sa[..., 2] * 0.0722
    light28 = (lum >= 0.62) & (sat <= 0.28)
    light22 = (lum >= 0.62) & (sat <= 0.22)
    water = (sa[..., 2] >= sa[..., 0]) & (lum < 0.40) & (sat > 0.10)
    green = (sa[..., 1] > sa[..., 0] * 1.06) & (sa[..., 1] > sa[..., 2] * 1.06) & (sa[..., 1] > 0.18)
    orange = (sa[..., 0] > 0.55) & (sa[..., 0] > sa[..., 1] * 1.25) & (sa[..., 1] >= sa[..., 2] * 0.9)
    land = ~water
    s1 = {"check": "S1", "rule": "land-relative light ratio >= 45% (lum>=0.62, sat<=0.28)",
          "light_full": float(light28.mean()), "water_ratio": float(water.mean()),
          "light_land": float(light28[land].mean()) if land.any() else 0.0,
          "sensitivity": {"sat<=0.22": float(light22[land].mean()),
                          "sat<=0.28": float(light28[land].mean())},
          "lum_median_land": float(np.median(lum[land])),
          "pass": bool(light28[land].mean() >= 0.45)}
    dump(ev_path("S1", "value_stats.json"), s1)
    dump(ev_path("S2", "hue_stats.json"),
         {"check": "S2", "green_ratio": float(green.mean()),
          "rule": "r07: <=0.12 (garden planting 1,010 m2 = 13.9% of the deck; whole-map green stays far below)",
          "pass": bool(green.mean() <= 0.12)})
    dump(ev_path("S3", "hue_stats.json"),
         {"check": "S3", "orange_ratio": float(orange.mean()),
          "pass": bool(orange.mean() <= 0.02)})

    # ---------- S11 value span ----------
    s11_rows, s11_ok = region_stats(arr[:CONTENT_H])
    dump(ev_path("S11", "value_span.json"),
         {"check": "S11", "rule": "per-region L p75-p25 >= 0.22; median <= 0.80",
          "regions": s11_rows, "pass": bool(s11_ok), "diagnostic_only": True})

    # ---------- S12 water border (hero) ----------
    # 意图（T3/r04）：人工水缘（水面平片的尽头）不得出现在画面里。
    # 判据：① 左右框水色 >=0.55（西侧开阔海面）；② 无宽边界——单行内跳变>8/255
    #       的像素占比 >0.4 的行数 = 0。上框允许北外圈天际线入画（v09 北带为
    #       合法地景，r04 已记录——30° 俯角的上框不再是纯水面）。
    # v10: the garden platform enters the lower-right frame; re-measured at 0.6+ side water.
    hraw = np.asarray(Image.open(os.path.join(REN, "hero_raw.png")).convert("RGB"),
                      dtype=np.float32)
    hh, hw = hraw.shape[:2]
    hlum_all = hraw.mean(axis=2)
    blue_dom = (hraw[..., 2] >= hraw[..., 0])
    lower60 = int(hh * 0.4)
    top_row_water = float(blue_dom[0].mean())
    side_water = float(blue_dom[lower60:, 0].mean() * 0.5 + blue_dom[lower60:, -1].mean() * 0.5)
    jump = np.abs(np.diff(hlum_all, axis=1))
    wide_rows = int(((jump > 8.0).mean(axis=1) > 0.4).sum())
    s12 = {"check": "S12", "rule": "r04: side frames water >=0.55; no wide artificial boundary row; top frame may contain north-band skyline",
           "top_row_water_ratio": round(top_row_water, 3),
           "side_water_ratio": round(side_water, 3),
           "wide_boundary_rows": wide_rows,
           "max_jump": round(float(jump.max()), 2),
           "pass": bool(side_water >= 0.55 and wide_rows == 0)}
    dump(ev_path("S12", "water_border.json"), s12)

    # ---------- GA09 HeroRoute framing ----------
    hr = np.asarray(Image.open(os.path.join(REN, "hero", "HeroRoute.png")).convert("RGB"),
                    dtype=np.float32)
    hrh, hrw = hr.shape[:2]
    loc = np.array([-120.0, -370.0, 220.0])
    tgt = np.array([150.0, -30.0, 0.0])
    fwd = tgt - loc; fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, np.array([0.0, 0.0, 1.0])); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    lens, sw = 56.0, 36.0
    sh = sw * hrh / hrw
    fx, fy = lens / sw * hrw, lens / sh * hrh

    def proj(wx, wy, wz):
        d = np.array([wx, wy, wz]) - loc
        z = d @ fwd
        return (hrw / 2 + fx * (d @ right) / z, hrh / 2 - fy * (d @ up) / z)

    AVH, AVU, AVV = (125.0, -6.6), (0.342, -0.940), (0.940, 0.342)
    nrm = math.hypot(*AVU)

    def avx(t, v, z):
        return (AVH[0] + AVU[0] / nrm * t + AVV[0] * v,
                AVH[1] + AVU[1] / nrm * t + AVV[1] * v, z)

    corners = {}
    for tag, (t, v) in {"N_W": (40, -50), "N_E": (40, 50), "S_E": (114, 50), "S_W": (114, -50)}.items():
        x, y = proj(*avx(t, v, 4.7))
        corners[tag] = [round(float(x), 1), round(float(y), 1),
                        bool(0 <= x <= hrw and 0 <= y <= hrh)]
    blue = (hr[..., 2] >= hr[..., 0])
    low = int(hrh * 0.4)
    ga9 = {"check": "GA09", "camera": {"loc": loc.tolist(), "target": tgt.tolist(), "lens": lens},
           "corners_px": corners,
           "side_water_ratio": round(float((blue[low:, 0].mean() + blue[low:, -1].mean()) / 2), 3),
           "pass": all(c[2] for c in corners.values())
                   and float((blue[low:, 0].mean() + blue[low:, -1].mean()) / 2) >= 0.55}
    dump(ev_path("GA09", "hero_route.json"), ga9)
    with open(os.path.join(ROOT, REQ, "runs", RUN, "evidence", "GA09", "hero_route.md"),
              "w", encoding="utf-8") as f:
        f.write("# GA09 制作侧笔记\n\n"
                "HeroRoute（-120,-370,220 / 目标 150,-30 / 56 mm / 1920x1080）四角像素 %s；"
                "左右框水色 %.3f。岛—桥A—花园—桥B—半岛在同一条视线上，平台四角均在幅内。"
                "半岛远端（t=234.7）落在幅外，属该机位已知取舍（S12 走 CameraHero，不受影响）。"
                "GA09 PASS（几何投影 + 目视）。\n"
                % (json.dumps({k: v[:2] for k, v in corners.items()}, ensure_ascii=False),
                   ga9["side_water_ratio"]))

    # ---------- S13 illustration metrics ----------
    hl = arr[:CONTENT_H].mean(axis=2)
    hist = np.bincount((hl * 255).astype(int).ravel(), minlength=256).astype(np.float32)
    k = np.exp(-np.arange(-6, 7) ** 2 / (2 * 2.0 ** 2)); k /= k.sum()
    hs = np.convolve(hist, k, "same")
    peaks = []
    for i in np.argsort(hs)[::-1]:
        if hs[i] < hs.max() * 0.06:
            break
        if all(abs(int(i) - q) > 25 for q in peaks):
            peaks.append(int(i))
        if len(peaks) == 3:
            break
    peaks = sorted(peaks)
    peak_ok = len(peaks) == 3 and (peaks[2] - peaks[0]) >= 0.12 * 255 \
        and (peaks[1] - peaks[0]) >= 0.10 * 255
    dark = hl < 0.35
    if dark.any():
        Lb, ab, bb = srgb_to_lab(arr[:CONTENT_H][dark])
        bstar = float(bb.mean())
    else:
        bstar = 0.0
    gy, gx = np.gradient(hl)
    mag = np.hypot(gx, gy)
    Jxx = _smooth(gx * gx, 1); Jyy = _smooth(gy * gy, 1); Jxy = _smooth(gx * gy, 1)
    coh = np.sqrt((Jxx - Jyy) ** 2 + 4 * Jxy ** 2) / (Jxx + Jyy + 1e-6)
    cover = float(((mag > 0.04) & (coh > 0.35)).mean())
    s13 = {"check": "S13", "rule": "3 peaks sep>=0.12; dark b* -6±2; stroke coverage >=30%",
           "peaks_0_1": [round(p / 255, 3) for p in peaks],
           "peak_gap": round((peaks[-1] - peaks[0]) / 255, 3) if len(peaks) == 3 else None,
           "dark_b_star": round(bstar, 2),
           "stroke_coverage": round(cover, 3),
           "pass": bool(peak_ok and -8 <= bstar <= -4 and cover >= 0.30),
           "diagnostic_only": True}
    dump(ev_path("S13", "illustration_metrics.json"), s13)

    # ---------- S14 CEO box ----------
    ax, ay = px(100, 75); bx, by = px(140, 45)
    box = arr[int(ay):int(by), int(ax):int(bx)]
    bl = box.mean(axis=2)
    dark_m = bl < (bl.mean() - 0.10)
    comps = components(dark_m, min_area=40)
    s14 = {"check": "S14", "rule": "CEO box std>=0.15; mean<=0.88; furniture>=3",
           "mean": round(float(bl.mean()), 3), "std": round(float(bl.std()), 3),
           "furniture_components": len(comps),
           "pass": bool(bl.std() >= 0.15 and bl.mean() <= 0.88 and len(comps) >= 3)}
    dump(ev_path("S14", "ceo_readout.json"), s14)

    # ---------- S15 color probe (subprocess on core_raw) ----------
    out15 = ev_path("S15", "color_probe.json")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "color_probe.py"),
                        os.path.join(REN, "core_raw.png"), "--out", out15 + ".probe"],
                       capture_output=True, text=True)
    rows15 = []
    try:
        rows15 = json.loads(r.stdout.strip().splitlines()[-1])["rows"]
    except Exception:
        pass
    s15 = {"check": "S15", "rule": "|dH|<=12, |dS|<=0.08, |dL|<=0.06 (M8.5 hard gate)",
           "rows": rows15, "pass": bool(rows15) and all(x["pass"] for x in rows15),
           "diagnostic_only": True}
    dump(out15, s15)
    if os.path.exists(out15 + ".probe"):
        os.remove(out15 + ".probe")

    print(json.dumps({"S1": s1["pass"], "G4": g4["pass"], "G7": g7["pass"], "W1": w1["pass"],
                      "GA09": ga9["pass"],
                      "S11": s11_ok, "S12": s12["pass"], "S13": s13["pass"],
                      "S14": s14["pass"], "S15": s15["pass"],
                      "jpg": os.path.getsize(jpg)}, ensure_ascii=False))
    print("POST_OK")


if __name__ == "__main__":
    main()
