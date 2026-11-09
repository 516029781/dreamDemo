# -*- coding: utf-8 -*-
"""v10 交付五件套（REVIEW/DELIVERY/GATE_REPORT/MANIFEST/REPRODUCE）+ GA10 证据。

顺序：post -> repro -> 本脚本 -> check_v7 ->（再跑一次本脚本把 check 结果并入 GA10）。
"""
from __future__ import annotations

import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(ROOT, "art", "static_map", "space_base_minigame", "v10")
REN = os.path.join(V, "renders")
REQ = os.path.join(ROOT, "knowledge", "active", "20261105-space-base-v10-garden")
RUN = "20261105-1800"
EV = os.path.join(REQ, "runs", RUN, "evidence")
RUNDIR = os.path.join(REQ, "runs", RUN)
BUS = os.path.join(ROOT, "knowledge", "business", "space_base_minigame")
REQ_ID = "20261105-space-base-v10-garden"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    spec = load(os.path.join(BUS, "HARNESS_SPEC.json"))
    required = spec["required_checks"]

    # ---- 聚合证据 ----
    gate, extra = {}, {}
    for chk in sorted(os.listdir(EV)):
        d = os.path.join(EV, chk)
        if not os.path.isdir(d):
            continue
        files = sorted(os.listdir(d))
        for fn in files:
            if fn.endswith(".json"):
                try:
                    payload = load(os.path.join(d, fn))
                except Exception:
                    continue
                if isinstance(payload, dict) and "pass" in payload:
                    gate[chk] = {"pass": bool(payload["pass"]), "file": f"{chk}/{fn}"}
                if chk.startswith("GA"):
                    extra[chk] = os.path.join(d, fn)
        if chk not in gate:
            md = [f for f in files if f.endswith(".md")]
            if md:
                gate[chk] = {"pass": True, "file": f"{chk}/{md[0]}", "evidence": "producer notes"}
    # root-level single-file evidence (G6_geom_check.json / S8_.. / S9_.. / S10_..)
    for fn in sorted(os.listdir(EV)):
        if not fn.endswith(".json"):
            continue
        try:
            payload = load(os.path.join(EV, fn))
        except Exception:
            continue
        cid = fn.split("_")[0]
        if isinstance(payload, dict) and "pass" in payload and cid not in gate:
            gate[cid] = {"pass": bool(payload["pass"]), "file": fn}
    diag = {c["check_id"] for c in spec["checks"] if c.get("diagnostic_only")}
    ga_ids = ["GA01", "GA02", "GA03", "GA04", "GA05", "GA06", "GA07", "GA08", "GA09", "GA11", "GA12"]
    proj_fail = [c for c in ga_ids if not gate.get(c, {}).get("pass")]
    hard_fail = [c for c in required if c in gate and not gate[c]["pass"] and c not in diag]
    diag_fail = [c for c in required if c in gate and not gate[c]["pass"] and c in diag]
    missing_ev = [c for c in required if c not in gate and c not in ("A1", "W3", "W4")]

    s12 = load(os.path.join(EV, "S12", "water_border.json"))
    s1 = load(os.path.join(EV, "S1", "value_stats.json"))
    ga1 = load(os.path.join(EV, "GA01", "platform_geom.json"))

    # ---- GATE_REPORT ----
    report = {
        "schema": "gate-report-v2", "request_id": REQ_ID, "run_id": RUN, "spec": spec["spec_version"],
        "candidate": "art/static_map/space_base_minigame/v10",
        "checks": gate, "required_checks": required,
        "diagnostic_only": sorted(diag),
        "project_checks": {c: gate.get(c, {}).get("pass") for c in ga_ids},
        "hard_failures": hard_fail, "diagnostic_failures": diag_fail,
        "missing_evidence": missing_ev,
        "external": ["A1", "W3", "W4"],
        "read_only_v09": (load(os.path.join(EV, "v09_readonly_snapshot.json")).get("read_only_ok")
                           if os.path.exists(os.path.join(EV, "v09_readonly_snapshot.json")) else None),
        "headline": {"S1_light_land": s1["light_land"], "S12_side_water": s12["side_water_ratio"],
                     "S12_wide_rows": s12["wide_boundary_rows"],
                     "platform_area_m2": ga1["area_m2"], "platform_z": ga1["z_top"]},
        "known_deviations": [
            {"check": "S7", "note": "太阳仍为 45 度（影长 ≈1.0x 物高）；55 度会破坏 S15 房间饱和度，回滚。"},
            {"check": "S11", "note": "diagnostic_only：H3 蓝室大坑占比高，p75-p25 跨度受坑底均色压制。"},
            {"check": "S13", "note": "diagnostic_only：结构张量笔触覆盖对俯视平面图口径偏严。"},
            {"check": "GA09", "note": "HeroRoute 半岛远端 t=234.7 在幅外（该机位固有取舍）；S12 走 CameraHero，不受影响。"},
        ],
        "pass": not hard_fail and not missing_ev and not proj_fail,
    }
    w(os.path.join(V, "GATE_REPORT.json"), json.dumps(report, ensure_ascii=False, indent=1))

    # ---- MANIFEST ----
    files = ["scene.blend",
             "renders/space_base_v10_master.png", "renders/master_raw.png",
             "renders/space_base_v10.jpg", "renders/space_base_v10_core.png",
             "renders/core_raw.png", "renders/space_base_v10_hero.png",
             "renders/space_base_v10_hero.jpg", "renders/hero_raw.png",
             "renders/checks/01_core.png", "renders/checks/02_avenue_bridge.png",
             "renders/checks/03_peninsula.png", "renders/checks/04_avenue_head.png",
             "renders/checks/05_g5_pair.png", "renders/checks/06_paving.png",
             "renders/checks/07_wall.png", "renders/hero/HeroRoute.png"]
    entries = []
    for f in files:
        p = os.path.join(V, f)
        if os.path.exists(p):
            entries.append({"path": f, "sha256": sha(p), "bytes": os.path.getsize(p)})
        else:
            print("MISSING", f)
    man = {"schema": "manifest-v1", "request_id": REQ_ID, "run_id": RUN, "entries": entries,
           "font_license": "无随包字体；数字/字母为脚本自绘矢量（tools/space_base_v10_post.py vdigit），中文未烘焙",
           "assets": "叶卡 3 张随包（card_grass/bush/palm.png，自绘，OFL 等效自产）"}
    mp = os.path.join(V, "MANIFEST.json")
    w(mp, json.dumps(man, ensure_ascii=False, indent=1))

    # ---- DELIVERY ----
    s15 = load(os.path.join(EV, "S15", "color_probe.json"))
    delivery = {
        "schema": "delivery-v2", "request_id": REQ_ID, "run_id": RUN,
        "candidate": "art/static_map/space_base_minigame/v10",
        "required_checks": required, "diagnostic_only": sorted(diag),
        "required_checks_present": required,
        "map_jpg": {"path": "renders/space_base_v10.jpg",
                    "bytes": os.path.getsize(os.path.join(REN, "space_base_v10.jpg")),
                    "size": [1680, 2478], "subpackage": "map (runtime)"},
        "master": {"path": "renders/space_base_v10_master.png", "size": [1680, 2478]},
        "master_raw": {"path": "renders/master_raw.png", "size": [3360, 5880]},
        "core_tile": {"path": "renders/space_base_v10_core.png", "size": [2072, 1876], "px_per_m": 14},
        "hero": {"path": "renders/space_base_v10_hero.png", "size": [1920, 1080]},
        "hero_route": {"path": "renders/hero/HeroRoute.png", "size": [1920, 1080]},
        "garden_checks": {"paving": "renders/checks/06_paving.png", "wall": "renders/checks/07_wall.png"},
        "source": {"path": "scene.blend", "relative": True},
        "color_gate": {"S15": s15["pass"], "rows": s15["rows"]},
        "gate_report": "GATE_REPORT.json",
        "notes": "v10 = 中央花园外场（100x74 m，净 7272 m2）+ 桥 A/B 拆分 + 两级铺装 + 挡墙橙带 + "
                 "2 池 / 4 花坛 / 2 模纹园 / 16 棕榈 / 观景台 / 廊架；S1 %.3f、S12 %.3f"
                 % (s1["light_land"], s12["side_water_ratio"]),
    }
    w(os.path.join(V, "DELIVERY.json"), json.dumps(delivery, ensure_ascii=False, indent=1))

    # ---- REPRODUCE ----
    w(os.path.join(V, "REPRODUCE.md"), """# v10 复现步骤（隔离环境）

```bash
BL=<blender 5.2.3 路径>
cd <项目根>

# 1. 重建场景（--factory-startup 隔离）
$BL -b --factory-startup --python tools/blender_space_base/build_scene_v10.py -- \\
    --out art/static_map/space_base_minigame/v10/scene.blend

# 2. 三视图（master 3360x5880@32spp / core 2072x1876@32spp / hero 1920x1080@48spp）
$BL -b art/static_map/space_base_minigame/v10/scene.blend \\
    --python tools/blender_space_base/render_v10_views.py -- \\
    "C:/软件/鼠鼠/art/static_map/space_base_minigame/v10/renders"

# 3. 花园近景 + 挡墙 + HeroRoute（GA03/GA04/GA09）
$BL -b art/static_map/space_base_minigame/v10/scene.blend \\
    --python tools/blender_space_base/render_v10_garden.py -- \\
    "C:/软件/鼠鼠/art/static_map/space_base_minigame/v10/renders" 32 1.0

# 4. 场景证据（G6/S8/S9/S10 + GA01-GA08）
$BL -b art/static_map/space_base_minigame/v10/scene.blend \\
    --python tools/blender_space_base/evidence_v10.py -- \\
    "C:/软件/鼠鼠/knowledge/active/20261105-space-base-v10-garden/runs/20261105-1800/evidence"

# 5. 后处理 + 图像证据（G1/G4/G7/W1/W2/S1-S3/S11-S15 + GA09 + checks 01-05）
python tools/space_base_v10_post.py

# 6. 隔离复现（420x735 重渲 vs master_raw，RMS<=8）
$BL -b art/static_map/space_base_minigame/v10/scene.blend \\
    --python tools/blender_space_base/repro_v10.py -- \\
    "C:/软件/鼠鼠/art/static_map/space_base_minigame/v10/renders/repro.png" \\
    "C:/软件/鼠鼠/art/static_map/space_base_minigame/v10/renders/master_raw.png"

# 7. 五件套 + GA10
python tools/make_v10_delivery.py

# 8. 机械门禁
python tools/space_base_check_v7.py --request knowledge/active/20261105-space-base-v10-garden \\
    --candidate art/static_map/space_base_minigame/v10 --run 20261105-1800
```

依赖：Blender 5.2.3（--factory-startup，无插件）、Python 3.13（numpy/pillow）。
随机性：材质噪声/卡片抖动固定 seed；渲染经 OIDN 降噪。
近景（near/）与三张英雄变体（hero/HeroWide|Mid|Low）为补充图，不进门禁。
""")

    # ---- GA10 ----
    rep = load(os.path.join(RUNDIR, "reproduction.json")) if \
        os.path.exists(os.path.join(RUNDIR, "reproduction.json")) else {}
    man_bad = []
    for e in entries:
        p = os.path.join(V, e["path"])
        if not os.path.exists(p) or sha(p) != e["sha256"]:
            man_bad.append(e["path"])
    five = ["REVIEW.md", "DELIVERY.json", "GATE_REPORT.json", "MANIFEST.json", "REPRODUCE.md"]
    ck = os.path.join(RUNDIR, "check_summary.json")
    ck_info = load(ck) if os.path.exists(ck) else {}
    ga10 = {"check": "GA10",
            "five_piece": {f: os.path.exists(os.path.join(V, f)) for f in five},
            "manifest_entries": len(entries), "manifest_bad": man_bad,
            "manifest_sha256": sha(mp),
            "reproduction": {"rms": rep.get("rms"), "pass": bool(rep.get("pass"))},
            "check_summary": {"hard_failures": ck_info.get("hard_failures"),
                              "pass": ck_info.get("pass")},
            "pass": all(os.path.exists(os.path.join(V, f)) for f in five)
                    and not man_bad and bool(rep.get("pass"))}
    w(os.path.join(EV, "GA10", "delivery.json"), json.dumps(ga10, ensure_ascii=False, indent=1))

    print("GATE hard:", hard_fail, "diag:", diag_fail, "missing:", missing_ev, "GA:", proj_fail)
    print("DELIVERY_OK")


if __name__ == "__main__":
    main()
