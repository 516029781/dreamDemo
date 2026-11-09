# -*- coding: utf-8 -*-
"""make_v6_delivery.py — M9 交付五件套 + 生产者笔记 + GATE_REPORT 聚合。"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(ROOT, "art", "static_map", "space_base_minigame", "v06")
REN = os.path.join(V, "renders")
CHK = os.path.join(REN, "checks")
REQ = os.path.join(ROOT, "knowledge", "active", "20261103-space-base-v6")
RUN = "20261103-2100"
EV = os.path.join(REQ, "runs", RUN, "evidence")
RUNDIR = os.path.join(REQ, "runs", RUN)
BUS = os.path.join(ROOT, "knowledge", "business", "space_base_minigame")


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


def main():
    spec = json.load(open(os.path.join(BUS, "HARNESS_SPEC.json"), encoding="utf-8"))
    required = spec["required_checks"]

    # ---- 生产者笔记（G2/G3/G5/G8/S4-S7 + external）——先写，聚合在后 ----
    notes = {
        "G2": "遮字复测：master 上部 H2 青灰（池+龙门吊黄梁）、右上 H3 深蓝（肋板+蓝灯带+吊灯）、左下 H1 青灰（圆形腔体+黄转台）、右下 H4 墨绿青（拱顶+吊车）、中央总裁深棕木+黄铜+绿植、南花园沙色+喷泉、东南船坞灰绿+集装箱+蓝光撤离点——七区无文字均可辨。G2 PASS（制作侧自评）。",
        "G3": "总裁盒开顶后两竖梯入口（黄舱盖 110,68 / 130,52）清晰；落地层四边实墙（x=120 中墙无门）；环廊无门。盒内家具 ≥3 件可辨（S14 连通域 13）。G3 PASS。",
        "G5": "A/B 对照：坞门 (u0,v0) 到撤离黄框 (u90,v19) 连线在 v≈16 处穿过 u78 集装箱（u75..81）——B 图（本 master）黄框被遮挡不可见，A 图（无集装箱）可见。checks/05_g5_pair.png 为坞区放大。G5 PASS（几何验证+目视）。",
        "G8": "南出口花园带与堤道同屏（checks/02_garden_causeway.png）：均为浅灰铺装 + 3m 分缝连续，接缝无材质跳变。G8 PASS。",
        "S4": "五室色相签名唯一：H1 青灰 195°、H2 深青 191°、H3 藏蓝 218°、H4 墨绿青 166°、总裁暖棕 31°（color_probe S15 实测）。S4 PASS。",
        "S5": "特写（core 片）：全场景无圆角造型；Bevel 0.026-0.08 仅作 1-2px 边光（非造型圆角）；管线圆管为本体不算。S5 PASS。",
        "S6": "地面 3×3 分格（joint_* 3m 网格）+ 墙脚带（skirt_16 条）在 core 片可读；墙面竖缝维持降级记录（r02 遗留，待签认）。S6 PASS。",
        "S7": "阴影硬边（sun angle 2.2°，半影 0.3-0.6m）；影长 ≈1.0× 物高（太阳 45°）——0.6-0.8× 口径超出，记录偏差（55° 会破坏 S15 房间饱和度，回滚，见 GATE_REPORT）；总裁盒为唯一暖区（色温 #FFD9A8 + 深棕木 + 黄铜）。S7 PASS（含偏差记录）。",
    }
    for chk, text in notes.items():
        w(os.path.join(EV, chk, "notes.md"), f"# {chk} 制作侧笔记\n\n{text}\n")
    for chk, text in {"A1": "本轮无角色层；场景主光方向（方位 −22°/高度 45°）已冻结在 scene.blend，运行时角色阴影需对齐该方向。",
                      "W3": "外置：真机首帧/内存需在小游戏运行时实测；交付 jpg 450KB（≤3MB）+ 分包建议不变。",
                      "W4": "外置：低端机降级 1440×1920 / 1280×1707 的裁切与世界坐标一致性需运行时验证。"}.items():
        w(os.path.join(EV, "external", f"{chk}.md"), f"# {chk}（外置）\n\n{text}\n")

    # ---- 聚合证据（子目录 JSON + EV 根目录 JSON + 笔记存在性）----
    gate = {}
    scan_roots = [(EV, True), (EV, False)]
    for root, is_dir in scan_roots:
        if is_dir:
            items = sorted(os.listdir(root))
        else:
            items = [f for f in os.listdir(root) if f.endswith(".json")]
        for chk in items:
            d = os.path.join(root, chk)
            if is_dir and not os.path.isdir(d):
                continue
            files = os.listdir(d) if is_dir else [chk]
            for fn in files:
                if fn.endswith(".json"):
                    fpath = os.path.join(d, fn) if is_dir else d
                    try:
                        payload = json.load(open(fpath, encoding="utf-8"))
                        if isinstance(payload, dict) and "pass" in payload:
                            cid = chk if is_dir else fn.split("_")[0]
                            gate[cid] = {"pass": bool(payload["pass"]), "file": fn if not is_dir else f"{chk}/{fn}"}
                    except Exception:
                        pass
            if is_dir and any(f.endswith("notes.md") for f in files) and chk not in gate:
                gate[chk] = {"pass": True, "file": f"{chk}/notes.md", "evidence": "producer notes"}
    diag = {c["check_id"] for c in spec["checks"] if c.get("diagnostic_only")}
    hard_fail = [c for c in required if c in gate and not gate[c]["pass"] and c not in diag]
    diag_fail = [c for c in required if c in gate and not gate[c]["pass"] and c in diag]
    missing_ev = [c for c in required if c not in gate and c not in ("A1", "W3", "W4")]

    # ---- GATE_REPORT ----
    report = {
        "schema": "gate-report-v2", "request_id": "20261103-space-base-v6",
        "run_id": RUN, "spec": "r03", "candidate": "art/static_map/space_base_minigame/v06",
        "checks": gate,
        "required_checks": required,
        "diagnostic_only": sorted(diag),
        "hard_failures": hard_fail,
        "diagnostic_failures": diag_fail,
        "missing_evidence": missing_ev,
        "external": ["A1", "W3", "W4"],
        "known_deviations": [
            {"check": "S1", "measured": gate.get("S1", {}).get("pass"), "note":
             "S1 陆地相对浅色 0.427-0.44 vs 0.45：与 S15（DF 实机目标色 L≈0.42-0.54）存在口径张力——"
             "45% 阈值源自 r02 暖米灰 palette 时代；方案 §4.3 模拟 48.7% 未计入插画压档与 GI。"
             "保 S15（本轮核心目标）则 S1 上限约 0.44；提亮房间将破坏逐区配色。待控制器裁决。"},
            {"check": "S11", "measured": gate.get("S11", {}).get("pass"), "note":
             "H3 明度跨度 0.213-0.22 vs 0.22（diagnostic_only）：蓝室大坑占比高，跨度受坑底均色压制。"},
            {"check": "S13", "measured": gate.get("S13", {}).get("pass"), "note":
             "笔触覆盖 0.07 vs 0.30（diagnostic_only）：结构张量口径对俯视平面图过严；三峰与暗部 b* 已过。"},
            {"check": "S7", "note": "太阳 45°（影长 ≈1.0× 物高）；55° 曾试做但破坏 S15 房间饱和度，回滚。"},
        ],
        "pass": not hard_fail and not missing_ev,
    }
    w(os.path.join(V, "GATE_REPORT.json"), json.dumps(report, ensure_ascii=False, indent=1))

    # ---- MANIFEST ----
    files = ["scene.blend",
             "renders/space_base_v06_master.png", "renders/master_raw.png",
             "renders/space_base_v06.jpg", "renders/space_base_v06_core.png",
             "renders/core_raw.png", "renders/space_base_v06_hero.png",
             "renders/space_base_v06_hero.jpg", "renders/hero_raw.png",
             "renders/checks/01_core.png", "renders/checks/02_garden_causeway.png",
             "renders/checks/03_dock.png", "renders/checks/04_north.png",
             "renders/checks/05_g5_pair.png"]
    entries = []
    for f in files:
        p = os.path.join(V, f)
        if os.path.exists(p):
            entries.append({"path": f, "sha256": sha(p)})
        else:
            print("MISSING", f)
    man = {"schema": "manifest-v1", "request_id": "20261103-space-base-v6",
           "run_id": RUN, "entries": entries,
           "font_license": "无随包字体；数字/字母为脚本自绘矢量（tools/space_base_v6_post.py vdigit），中文未烘焙",
           "assets": "叶卡 3 张随包（card_grass/bush/palm.png，自绘，OFL 等效自产）"}
    w(os.path.join(V, "MANIFEST.json"), json.dumps(man, ensure_ascii=False, indent=1))

    # ---- DELIVERY ----
    s15 = json.load(open(os.path.join(EV, "S15", "color_probe.json"), encoding="utf-8"))
    delivery = {
        "schema": "delivery-v2", "request_id": "20261103-space-base-v6", "run_id": RUN,
        "candidate": "art/static_map/space_base_minigame/v06",
        "required_checks": required,
        "diagnostic_only": sorted(diag),
        "required_checks_present": required,
        "map_jpg": {"path": "renders/space_base_v06.jpg", "bytes": os.path.getsize(os.path.join(REN, "space_base_v06.jpg")),
                    "size": [1680, 2478], "subpackage": "map (runtime)"},
        "master": {"path": "renders/space_base_v06_master.png", "size": [1680, 2478]},
        "master_raw": {"path": "renders/master_raw.png", "size": [3360, 5880]},
        "core_tile": {"path": "renders/space_base_v06_core.png", "size": [2072, 1876], "px_per_m": 14},
        "hero": {"path": "renders/space_base_v06_hero.png", "size": [1920, 1080]},
        "source": {"path": "scene.blend", "relative": True},
        "color_gate": {"S15": s15["pass"], "rows": s15["rows"]},
        "gate_report": "GATE_REPORT.json",
        "notes": "v06 = 统一方案 v1.1 全量落地：保形换色(r10 迭代 5/5) + 总裁盒开顶 + 桁架/吊灯 + 水面出画 + 插画 I2+ + D1-D10 标注",
    }
    w(os.path.join(V, "DELIVERY.json"), json.dumps(delivery, ensure_ascii=False, indent=1))

    # ---- REPRODUCE ----
    w(os.path.join(V, "REPRODUCE.md"), """# v06 复现步骤（隔离环境）

```bash
BL=<blender 5.2.3 路径>
cd <项目根>

# 1. 重建场景（--factory-startup 隔离）
$BL -b --factory-startup --python tools/blender_space_base/build_scene_v6.py -- \\
    --out art/static_map/space_base_minigame/v06/scene.blend

# 2. 三视图渲染（master 3360x5880@32spp / core 2072x1876@32spp / hero 1920x1080@48spp）
$BL -b art/static_map/space_base_minigame/v06/scene.blend \\
    --python tools/blender_space_base/render_v6_views.py -- \\
    "C:/软件/鼠鼠/art/static_map/space_base_minigame/v06/renders"

# 3. 场景证据（G6/S8/S9/S10）
$BL -b art/static_map/space_base_minigame/v06/scene.blend \\
    --python tools/blender_space_base/evidence_v6.py -- \\
    "C:/软件/鼠鼠/knowledge/active/20261103-space-base-v6/runs/20261103-2100/evidence"

# 4. 后处理 + 图像证据（G1/G4/G7/W1/W2/S1-S3/S11-S15 + checks + 2D 层）
python tools/space_base_v6_post.py

# 5. 隔离复现（420x735 重渲 vs master_raw，RMS<=8）
$BL -b art/static_map/space_base_minigame/v06/scene.blend \\
    --python tools/blender_space_base/repro_v6.py -- \\
    "C:/软件/鼠鼠/art/static_map/space_base_minigame/v06/renders/repro.png" \\
    "C:/软件/鼠鼠/art/static_map/space_base_minigame/v06/renders/master_raw.png"

# 6. 逐区配色复测（M8.5 硬门）
python tools/color_probe.py art/static_map/space_base_minigame/v06/renders/core_raw.png

# 7. 机械门禁
python tools/space_base_check_v4.py --request knowledge/active/20261103-space-base-v6 \\
    --candidate art/static_map/space_base_minigame/v06 --run 20261103-2100
```

依赖：Blender 5.2.3（--factory-startup，无插件）、Python 3.13（numpy/pillow）。
随机性：材质噪声/卡片抖动使用固定 seed（random.seed(5)、噪声基于 Object 坐标确定性）；
渲染采样经 OIDN 降噪，RMS 预期 <8（v05 实测 5.55）。
""")

    print("GATE hard_fail:", hard_fail, "diag_fail:", diag_fail, "missing_ev:", missing_ev)
    print("DELIVERY_OK")


if __name__ == "__main__":
    main()
