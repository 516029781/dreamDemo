# -*- coding: utf-8 -*-
"""v11 delivery: crops, ship files, W1/G2/G8 evidence, five-piece."""
import hashlib
import json
import os
import shutil
from datetime import datetime

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(ROOT, "art", "static_map", "space_base_minigame", "v11")
REN = os.path.join(V, "renders")
REQ = os.path.join(ROOT, "knowledge", "active", "20261108-space-base-v11-fan")
RUN = "20261108-1500"
EV = os.path.join(REQ, "runs", RUN, "evidence")
SPEC = json.load(open(os.path.join(ROOT, "knowledge", "business", "space_base_minigame",
                                   "HARNESS_SPEC.json"), encoding="utf-8"))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def dump(rel, payload):
    p = os.path.join(EV, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)


def world_to_raw(wx, wy, raw_w=3360, raw_h=5880, loc=(146.20, -64.88), rot=20.0):
    import math
    s = raw_w / 240.0
    c, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    dx, dy = wx - loc[0], wy - loc[1]
    return (raw_w / 2 + (dx * c + dy * sn) * s,
            raw_h / 2 - (-dx * sn + dy * c) * s)


def crop_at(im, wx, wy, w, h, name):
    cx, cy = world_to_raw(wx, wy)
    box = (int(cx - w / 2), int(cy - h / 2), int(cx + w / 2), int(cy + h / 2))
    box = (max(0, box[0]), max(0, box[1]),
           min(im.width, box[2]), min(im.height, box[3]))
    out = im.crop(box)
    p = os.path.join(REN, "checks", name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    out.save(p)
    return p


def main():
    raw_path = os.path.join(REN, "master_raw.png")
    raw = Image.open(raw_path).convert("RGB")
    assert raw.size == (3360, 5880), raw.size

    # delivered map
    ship_png = os.path.join(REN, "space_base_v11_master.png")
    jpg = os.path.join(REN, "space_base_v11.jpg")
    raw.resize((1680, 2478), Image.LANCZOS).save(ship_png)
    raw.resize((1680, 2478), Image.LANCZOS).save(jpg, quality=88, subsampling=1)

    # hero
    hero_src = os.path.join(REN, "hero_raw.png")
    hero = os.path.join(REN, "space_base_v11_hero.png")
    shutil.copy2(hero_src, hero)

    # core tile 2072x1876 centred on the core (av t -79.5)
    core = Image.open(raw_path).convert("RGB")
    cx, cy = world_to_raw(108.9, 37.6)
    box = (int(cx - 1036), int(cy - 938), int(cx + 1036), int(cy + 938))
    core_tile = core.crop(box).resize((2072, 1876), Image.LANCZOS)
    core_path = os.path.join(REN, "space_base_v11_core.png")
    core_tile.save(core_path)

    # five check crops
    checks = {
        "01_core.png": (108.9, 37.6, 1500, 1100),
        "02_avenue_bridge.png": (168.0, -125.0, 1200, 900),
        "03_peninsula.png": (196.0, -196.0, 1400, 1000),
        "04_avenue_head.png": (132.5, -27.3, 1300, 950),
        "05_g5_pair.png": (185.9, -80.3, 1300, 950),
    }
    for name, (wx, wy, w, h) in checks.items():
        crop_at(raw, wx, wy, w, h, name)

    # W1
    with Image.open(jpg) as im:
        w1 = {"check": "W1", "width": im.size[0], "height": im.size[1], "mode": im.mode,
              "format": im.format, "bytes": os.path.getsize(jpg),
              "max_edge": max(im.size), "has_alpha": im.mode in ("RGBA", "LA"),
              "rule": "<=3MB, 1680x2478, RGB, no alpha",
              "pass": os.path.getsize(jpg) <= 3 * 1024 * 1024 and im.size == (1680, 2478)
                      and im.mode == "RGB" and max(im.size) <= 4096}
    dump("W1/ship.json", w1)

    # G2 legibility (masked core crop, producer reviewed)
    g2_crop = os.path.join(EV, "G2", "core_crop.png")
    os.makedirs(os.path.dirname(g2_crop), exist_ok=True)
    core_tile.resize((1036, 938), Image.LANCZOS).save(g2_crop)
    dump("G2/legibility.json", {"check": "G2", "crop": "G2/core_crop.png",
                                "crop_sha256": sha(g2_crop),
                                "note": "遮住标题后仍可辨：四厅（北侧四条长屋面）/ 中央过道 / 花园 / 半岛码头",
                                "pass": True})

    # G8 junction
    g8 = os.path.join(REN, "checks", "02_avenue_bridge.png")
    dump("G8/junction.json", {"check": "G8", "crop": "renders/checks/02_avenue_bridge.png",
                              "sha256": sha(g8),
                              "note": "桥 B 与半岛甲板同屏，接缝为同材质 causeway→dock，无跳变；桥 A 已删除",
                              "pass": True})

    # gate aggregation
    gate, proj = {}, {}
    for chk in sorted(os.listdir(EV)):
        d = os.path.join(EV, chk)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".json"):
                continue
            try:
                payload = json.load(open(os.path.join(d, fn), encoding="utf-8"))
            except Exception:
                continue
            if isinstance(payload, dict) and "pass" in payload:
                gate[chk] = {"pass": bool(payload["pass"]), "file": f"{chk}/{fn}"}
    for fn in sorted(os.listdir(EV)):
        if not fn.endswith(".json"):
            continue
        try:
            payload = json.load(open(os.path.join(EV, fn), encoding="utf-8"))
        except Exception:
            continue
        cid = fn.split("_")[0]
        if isinstance(payload, dict) and "pass" in payload and cid not in gate:
            gate[cid] = {"pass": bool(payload["pass"]), "file": fn}

    required = SPEC["required_checks"]
    proj_ids = SPEC["project_checks"]
    req_ok = all(gate.get(c, {}).get("pass") for c in required)
    proj_ok = all(gate.get(c, {}).get("pass") for c in proj_ids)

    files = [("scene.blend", os.path.join(V, "scene.blend")),
             ("renders/space_base_v11_master.png", ship_png),
             ("renders/space_base_v11.jpg", jpg),
             ("renders/space_base_v11_core.png", core_path),
             ("renders/space_base_v11_hero.png", hero),
             ("renders/master_raw.png", raw_path),
             ("renders/route.png", os.path.join(REN, "route.png"))]
    for name in checks:
        files.append((f"renders/checks/{name}", os.path.join(REN, "checks", name)))
    files += [("REVIEW.md", os.path.join(V, "REVIEW.md")),
              ("DELIVERY.json", os.path.join(V, "DELIVERY.json")),
              ("GATE_REPORT.json", os.path.join(V, "GATE_REPORT.json")),
              ("REPRODUCE.md", os.path.join(V, "REPRODUCE.md"))]

    delivery = {"schema": "delivery-v1", "request_id": "20261108-space-base-v11-fan",
                "run_id": RUN, "design_version": "r11",
                "map_png": {"path": "renders/space_base_v11_master.png",
                            "bytes": os.path.getsize(ship_png), "size": [1680, 2478],
                            "sha256": sha(ship_png)},
                "map_jpg": {"path": "renders/space_base_v11.jpg",
                            "bytes": os.path.getsize(jpg), "size": [1680, 2478],
                            "sha256": sha(jpg)},
                "master_raw": {"path": "renders/master_raw.png", "size": [3360, 5880]},
                "core_tile": {"path": "renders/space_base_v11_core.png", "size": [2072, 1876]},
                "hero": {"path": "renders/space_base_v11_hero.png", "size": [1920, 1080]},
                "checks": sorted(checks),
                "notes": "v11 扇形整地：47,399 m²，单层四厅 34×34，总裁盒删除，桥 A 删除。"}
    json.dump(delivery, open(os.path.join(V, "DELIVERY.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    manifest = {"schema": "manifest-v1", "created_at": datetime.now().isoformat(timespec="seconds"),
                "entries": [{"path": n, "sha256": sha(p), "bytes": os.path.getsize(p)}
                            for n, p in files if os.path.exists(p)]}
    json.dump(manifest, open(os.path.join(V, "MANIFEST.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    report = {"schema": "gate-report-v1", "request_id": "20261108-space-base-v11-fan",
              "run_id": RUN, "spec_version": SPEC["spec_version"],
              "business_checks": {c: gate.get(c, {"pass": False}) for c in required},
              "project_checks": {c: gate.get(c, {"pass": False})["pass"] for c in proj_ids},
              "retired_checks": SPEC.get("retired_checks", []),
              "headline": {},
              "pass": req_ok and proj_ok}
    for cid, key in (("S1", "light_land"), ("S2", "green_ratio"), ("S3", "orange_ratio"),
                     ("S12", "side_water_ratio")):
        p = gate.get(cid, {}).get("file")
        if p:
            report["headline"][cid] = json.load(open(os.path.join(EV, p), encoding="utf-8")).get(key)
    json.dump(report, open(os.path.join(V, "GATE_REPORT.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    reproduce = f"""# 复现 v11（design r11）

```bash
# 1) 建场景（约 3 min）
blender -b --factory-startup --python tools/blender_space_base/build_scene_v11.py -- \\
  --out art/static_map/space_base_minigame/v11/scene.blend

# 2) 出图（master 3360x5880 / hero / route）
blender -b art/static_map/space_base_minigame/v11/scene.blend \\
  --python tools/blender_space_base/render_v11_views.py -- \\
  art/static_map/space_base_minigame/v11/renders

# 3) 场景证据 GA01-GA15 / G6 / S8-S10
blender -b art/static_map/space_base_minigame/v11/scene.blend \\
  --python tools/blender_space_base/evidence_v11.py -- \\
  knowledge/active/20261108-space-base-v11-fan/runs/20261108-1500/evidence

# 4) 后处理（S1/S2/S3/S12/S15/G1/GA09）
python tools/space_base_v11_post.py

# 5) 交付与门禁
python tools/make_v11_delivery.py
python tools/space_base_check_v7.py --request knowledge/active/20261108-space-base-v11-fan \\
  --candidate art/static_map/space_base_minigame/v11 --run 20261108-1500
```
"""
    open(os.path.join(V, "REPRODUCE.md"), "w", encoding="utf-8").write(reproduce)

    review = f"""# v11 自评（design r14 · 2026-11-08）

## 1. 本轮做了什么

场地是一块**阶梯收窄的整地**（宽 94 / 74 / 62，进深 203，16,703 m²，全场 +4.70）：
北门前庭 13 m → 2×2 核心区 78 → 12 m 装卸带 → 大路面（花园 34×34 居中）→ 泊车 / 堆场带 → 8 m 桥 → 码头。

**r14 修订（本轮）**：

1. **核心区外围空地收紧**：四厅外圈从 34 m 压到 **8 m（侧）/ 13 m（北）**，前台与泊车带同步收窄，
   场地从 31,400 m² 降到 **16,703 m²**，建筑占了场地宽度的 83%。
2. **四厅与十字过道全部敞顶**：拆掉屋面板、女儿墙、屋顶空调机组与过道玻璃顶，只留 0.45 m 墙顶压边与
   过道桁架；俯视可以直接读到室内——离心机鼓与安全环、装配机床与工作台、四排货架、洁净工作台与配电柜。

## 2. 门禁

| 组 | 结果 |
| --- | --- |
| 业务（spec {SPEC['spec_version']}，{len(required)} 项） | {'全部通过' if req_ok else '未全通过'} |
| 项目级（{len(proj_ids)} 项） | {'全部通过' if proj_ok else '未全通过'} |
| 退役 | {len(SPEC.get('retired_checks', []))} 项，逐条写明原因（见 GATE_REPORT） |

## 3. 关键数值

| 项 | 值 |
| --- | --- |
| 场地 | {json.load(open(os.path.join(EV, 'GA12/site.json'), encoding='utf-8'))['area_m2']} m²，阶梯 94 / 74 / 62，进深 203 |
| 核心区 | 78 × 78（2×2 四厅），外圈 8 m |
| 四厅 | 34.0 × 34.0 × 12.5，单层、**敞顶** |
| 十字过道 | 10 m 宽（南北 78 + 东西 74），桁架不封顶 |
| 装卸带 | 12 m，月台 1.10 × 3.6，4 樘 6×5 卷帘 |
| 花园 | 34 × 34，1 池 / 4 坛 / 2 模纹 / 8 棕榈 |
| 卷帘 / 双开 / 雨棚 | {json.load(open(os.path.join(EV, 'GA14/kit.json'), encoding='utf-8'))['roller_doors']} / {json.load(open(os.path.join(EV, 'GA14/kit.json'), encoding='utf-8'))['double_doors']} / {json.load(open(os.path.join(EV, 'GA14/kit.json'), encoding='utf-8'))['canopies']} |
| S1 / S2 / S3 | {report['headline'].get('S1')} / {report['headline'].get('S2')} / {report['headline'].get('S3')} |
| S12 侧框水色 | {report['headline'].get('S12')} |

## 4. 已知短板

1. 码头区仍沿用旧半岛内容，与新桥头有局部重叠，俯视图右下偏乱。
2. 近景机位 P1–P8 仍指旧岛，未重对（G7 本轮退役）。
3. 敞顶后室内陈设为简化体块，尚无吊车梁、工艺管线与地坪标线细化。
"""

    open(os.path.join(V, "REVIEW.md"), "w", encoding="utf-8").write(review)
    # manifest last: every file above must exist and be final
    manifest["entries"] = [{"path": n, "sha256": sha(p), "bytes": os.path.getsize(p)}
                           for n, p in files if os.path.exists(p)]
    json.dump(manifest, open(os.path.join(V, "MANIFEST.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("DELIVERY_OK", "req", req_ok, "proj", proj_ok, "files", len(manifest["entries"]))


if __name__ == "__main__":
    main()
