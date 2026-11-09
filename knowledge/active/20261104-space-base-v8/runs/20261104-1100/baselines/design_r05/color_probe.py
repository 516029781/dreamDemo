# -*- coding: utf-8 -*-
"""配色探针：量测渲染图里每个区域的实际中位色，与实机换算目标比较。

用法：
    python tools/color_probe.py [渲染图] [--camera core|master]

默认读 v05 的 core_raw.png（CameraCore，14 px/m，中心 (120,67)）。
输出：每区 当前 hex / H,S,L、目标 hex、ΔH、ΔS、ΔL、判定。
"""
import colorsys
import json
import sys

import numpy as np
from PIL import Image

# 实机色 → 地图色（L' = 0.34 + 0.55·L，S 保持），见方案 §5.11.2
TARGETS = {
    "H1": ("离心", "#547684"),
    "H2": ("浮力", "#477A8A"),
    "H3": ("蓝室", "#3A6DBF"),
    "H4": ("黑室", "#58837D"),
    "C5": ("总裁", "#95755B"),
}
# 每区采样框（世界坐标，避开墙与设备，取中部地面）
# H3 框 x0=141：避开 CEO 盒（x≤140.8，含檐口）与本室的 warm overlap——CEO 属 C5 区
BOXES = {
    "H1": (67, 10, 70.5, 50),
    "H2": (72, 66, 114, 108),
    "H3": (142, 102, 156, 110),
    "H4": (126, 12, 168, 54),
    "C5": (106, 50, 134, 70),
}


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def rgb2hex(c):
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(v * 255))) for v in c)


def hls(c):
    h, l, s = colorsys.rgb_to_hls(*c)
    return h * 360, s, l


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else \
        "art/static_map/space_base_minigame/v05/renders/core_raw.png"
    cam = "core"
    if "--camera" in sys.argv:
        cam = sys.argv[sys.argv.index("--camera") + 1]
    out = None
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    im = Image.open(path).convert("RGB")
    a = np.asarray(im, dtype=np.float32) / 255.0

    if cam == "core":            # 2072x1876, 14 px/m
        def w2p(x, y):
            return 1036 + (x - 120) * 14, 938 - (y - 67) * 14
    else:                        # master 1680x2478, 7 / 5.7344 px/m
        def w2p(x, y):
            return x * 7, (166 - y) * 5.7344

    rows = []
    for key, (name, tgt) in TARGETS.items():
        x0, y0, x1, y1 = BOXES[key]
        p0, p1 = w2p(x0, y1), w2p(x1, y0)
        sub = a[int(p0[1]):int(p1[1]), int(p0[0]):int(p1[0])].reshape(-1, 3)
        if sub.size == 0:
            continue
        med = np.median(sub, axis=0)
        ch, cs, cl = hls(tuple(float(v) for v in med))
        th, ts, tl = hls(hex2rgb(tgt))
        dh = (ch - th + 180) % 360 - 180
        rows.append({
            "room": key, "name": name, "current": rgb2hex(med), "target": tgt,
            "H": round(ch), "S": round(cs, 2), "L": round(cl, 2),
            "dH": round(dh), "dS": round(cs - ts, 2), "dL": round(cl - tl, 2),
            "pass": abs(dh) <= 12 and abs(cs - ts) <= 0.08 and abs(cl - tl) <= 0.06,
        })

    print("%-4s %-5s %-9s %-9s %5s %5s %5s %6s" %
          ("区", "名", "当前", "目标", "ΔH", "ΔS", "ΔL", "判定"))
    for r in rows:
        print("%-4s %-5s %-9s %-9s %+5d %+5.2f %+5.2f %6s" %
              (r["room"], r["name"], r["current"], r["target"],
               r["dH"], r["dS"], r["dL"], "OK" if r["pass"] else "FIX"))
    bad = [r["room"] for r in rows if not r["pass"]]
    print("\nCOLOR_PROBE %s  pass %d/%d  需要修: %s" %
          (path.split("/")[-1], len(rows) - len(bad), len(rows), ",".join(bad) or "无"))
    payload = {"rows": rows, "path": path,
               "pass_count": len(rows) - len(bad), "total": len(rows), "bad": bad}
    print(json.dumps(payload, ensure_ascii=False))
    if out:
        import os
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
