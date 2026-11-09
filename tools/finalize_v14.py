"""Write the v14 delivery docs and rebind MANIFEST SHA (run LAST).

    python tools/finalize_v14.py <final_master_metrics.json> <final_scene_metrics.json>

Reads measured values only; never fabricates a pass. diagnostic_only and
not_run are recorded as such (HARNESS_LIFECYCLE §3).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path("C:/软件/鼠鼠")
CAND = ROOT / "art/static_map/space_base_minigame/v14"
EV = CAND / "evidence"
REQ = "20261108-space-base-v14-art"
RUN = "20261108-2035"
RUNDIR = ROOT / "knowledge/active" / REQ / "runs" / RUN

img = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
scn = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))

TARGETS = {
    "A1_land_L_p50": (0.62, 0.70), "A2_bright_gt080_pct": (None, 10.0),
    "A3_dark_lt030_pct": (8.0, None), "A4_span_p90_p10": (0.50, None),
    "A5_clip_gt097_pct": (None, 0.8), "A13_mean_saturation": (0.24, None),
    "S1_light_land": (0.45, None),
}
rows, fails = [], []
for k, (lo, hi) in TARGETS.items():
    v = img[k]
    ok = (lo is None or v >= lo) and (hi is None or v <= hi)
    if not ok:
        fails.append(k)
    rows.append("| %s | %s | %s | %s |" % (k, v,
                ("%s–%s" % (lo, hi)) if lo is not None and hi is not None else
                ("≥%s" % lo if lo is not None else "≤%s" % hi),
                "PASS" if ok else "**FAIL**"))

scene_rows = [
    ("在用材质 A6", scn["A6_materials_used"], "≤40", "FAIL" if scn["A6_materials_used"] > 40 else "PASS"),
    ("material_family 族数", scn["A6_family_count_excl_untagged"], "3 主族", "diagnostic_only"),
    ("低粗糙度占比 A7", scn["A7_low_roughness_ratio"], "≥0.25",
     "PASS" if scn["A7_low_roughness_ratio"] >= 0.25 else "FAIL"),
    ("metallic>0.5 材质数 A7", scn["A7_metallic_gt050_count"], "≥4",
     "PASS" if scn["A7_metallic_gt050_count"] >= 4 else "FAIL"),
    ("结构块倒角 A8 (px)", scn["A8_structural_blocks_mind_ge_0_73"]["max_width_px"], "≥1.3",
     "PASS" if scn["A8_structural_blocks_mind_ge_0_73"]["max_width_px"] >= 1.3 else "FAIL"),
]

(CAND / "REVIEW.md").write_text("""# v14 制作侧自评（一次性成像层改造）

> 状态：**机械交付完成；视觉签收与部分指标未达标如实列出**。不宣称 target_met。

## 做了什么

按 `planning/art/SPACE_BASE_V14_ONESHOT_PLAN_20261108.md` 单批次完成 M01–M12：
compositor 分级栈（含亮度门控饱和度）、D 候选曝光、多灯分工与 AO、明度分工、
材质族标签与表面响应、纹理幅度与粗糙度 mask、倒角分档、水面三段与雾分工。

v13 冻结只读；v14 由 `gen_v14_from_v13.py` 从 v13 源脚本确定性派生。

## 成像指标（交付尺寸 1680×2478 / 24 spp）

| 指标 | 实测 | 目标 | 判定 |
|---|---:|---|---|
%s

未达标项：%s（不写成 pass，不事后放宽阈值）。

## 场景指标

| 项 | 实测 | 目标 | 判定 |
|---|---:|---|---|
%s

## 收敛记录（方案 §6 允许 2 轮，实际因 S1 硬约束做了 5 轮，如实记录）

| 轮 | 改动 | A1 | A2 | A3 | A4 | A13 | S1 |
|---|---|---:|---:|---:|---:|---:|---:|
| r1 | 初版（exposure −0.15 / Sun 3.6 / World .45 / HueSat 1.16 全局） | .568 | 0.8 | 9.6 | .428 | .266 | **0.017** |
| r2 | 提亮（exp 0 / Sun 4.2 / World .55）+ 温和分级 + 亮度门控掩码（未接上） | .644 | 16.9 | 7.1 | .489 | .213 | 0.448 |
| r3 | 修掩码 `outputs[0]` + platform +4%% | .621 | 16.6 | 7.1 | .494 | **.276** | **0.163** |
| r4 | 关掉饱和度提升（sat 1.0），保留 platform +4%% | .644 | 17.1 | 7.0 | .492 | .213 | 0.448 |
| **r5** | **ColorBalance gamma 1.10 抬中间调（不推高光）** | **.670** | 18.7 | 4.8 | .471 | .195 | **0.507 ✅** |

**关键诊断**：S1 的瓶颈不是饱和度，是 `L≥0.62` 的陆地像素从 v13 的 67.8%% 掉到 52.5%%；
`sat≤0.28` 仅从 89.8%% 掉到 87.7%%。提亮单个材质无效（已达标区域），
必须抬中间调 → gamma 是比 exposure 更精准的杠杆（高光端影响小）。
r3 证明 **A13（提饱和）与 S1（低饱和浅色占比）直接互斥**，本批次优先保 S1 契约。

## 结构性结论（重要）

**S1 判据与"降低亮端堆积"存在面积竞争**：S1 要求 ≥45%% 陆地像素同时满足
`L≥0.62` 与 `sat≤0.28`，而本方案要压低 L>0.80 占比、提高暗部与饱和度。
v13 能满足 S1 正是因为 42.3%% 亮端堆积。本批次未改契约，靠"亮度门控饱和度 +
platform 提亮 4%%"把两者勉强同时保住；若要进一步提高暗部/跨度，
需按 HARNESS_LIFECYCLE 走 N2 重新裁决 S1 口径。

## 已知短板

1. A2/A3/A4/A13 等未达标项见上表，均为真实测量。
2. 场地轮廓 94/74/62 直角阶梯、主路面 F1–F5 填充、四厅立面套件属 v2.0 内容方案，未纳入。
3. 视觉盲测（3 人 5 秒）未做，需人工。
""" % ("\n".join(rows), ", ".join(fails) or "无",
       "\n".join("| %s | %s | %s | %s |" % r for r in scene_rows)), encoding="utf-8")

(CAND / "DEVLOG.md").write_text("""# v14 开发记录（单批次）

- 生成器：`tools/blender_space_base/gen_v14_from_v13.py`（22 处替换 + 追加 `apply_v14_art`）
- 构建：`tools/blender_space_base/build_scene_v14.py` → `v14/scene.blend`
- 渲染：`render_v14_quick.py` / `render_v14_master.py` / `render_v14_views.py` / `render_v14_raw.py`
- 检查：`check_v14_art.py` / `check_v14_scene.py` / `check_v14_grounding.py`
- 交付：`make_v14_delivery.py` / `finalize_v14.py` / `space_base_check_v7.py`

## 返修单（HARNESS_LIFECYCLE §4）

| id | 现象 → 根因 → 源级修改 → 重跑 | 结果 |
|---|---|---|
| H1/r2 | S1 0.017；全局 HueSat 提饱和 + 整体减光使 `sat≤0.28` 与 `L≥0.62` 同时塌陷；提亮 Sun/World、温和分级、加亮度门控掩码 | S1 0.4483 |
| H2/r3 | 掩码未接上（CompositorNodeValToRGB 输出名不是 `Color`）；改用 `outputs[0]`；并按 §6 提 platform +4% | 见最终指标 |

## 关键实现取舍

- `--art=off` 未做：颜色/纹理/倒角已写进源脚本常量；A/B 以冻结的 v13 候选对照。
- compositor 在 `build_camera_light` 之后建，确保不被后续构建覆盖。
- 雾仅英雄图启用，俯视 master 保持隐藏（否则遮地图）。
- Glare 用 FOG_GLOW + 低 Strength；不用 LUT（Blender 4.5 无该节点）、不用暗角。
""", encoding="utf-8")

gate = {
    "schema": "gate-report-v1", "request_id": REQ, "run_id": RUN,
    "stage": "N7_mechanical", "pass": False,
    "imaging": {k: {"value": img[k], "pass": (lo is None or img[k] >= lo) and
                    (hi is None or img[k] <= hi)} for k, (lo, hi) in TARGETS.items()},
    "scene": {r[0]: {"value": r[1], "verdict": r[3]} for r in scene_rows},
    "failed_metrics": fails,
    "visual": {"front_back_comparison": "diagnostic_only",
               "three_person_blind_test": "not_run"},
    "note": "not_run / diagnostic_only are NOT counted as pass. Business gate is mechanical only.",
}
(CAND / "GATE_REPORT.json").write_text(json.dumps(gate, ensure_ascii=False, indent=1), encoding="utf-8")
(CAND / "DELIVERY.json").write_text(json.dumps({
    "schema": "delivery-v1", "request_id": REQ, "run_id": RUN,
    "map_png": "renders/space_base_v14_master.png", "map_jpg": "renders/space_base_v14.jpg",
    "hero": "renders/space_base_v14_hero.png", "core_tile": "renders/space_base_v14_core.png",
    "status": "mechanical_complete_visual_pending"}, ensure_ascii=False, indent=1), encoding="utf-8")
(CAND / "REPRODUCE.md").write_text("""# 复现 v14

```bash
python tools/blender_space_base/gen_v14_from_v13.py
blender -b --factory-startup --python tools/blender_space_base/build_scene_v14.py -- \\
  --out <ABS>/art/static_map/space_base_minigame/v14/scene.blend
blender -b <v14>/scene.blend --python tools/blender_space_base/render_v14_views.py -- <ABS>/v14/renders
python tools/make_v14_delivery.py
blender -b <v14>/scene.blend --python tools/render_v14_raw.py -- <ABS>/v14/renders/master_raw.png
blender -b <v14>/scene.blend --python tools/check_v14_scene.py -- <OUT>.json
python tools/check_v14_art.py --image <PNG> --out <OUT>.json
python tools/space_base_check_v7.py --request knowledge/active/%s \\
  --candidate art/static_map/space_base_minigame/v14 --run %s
```

`V14_NO_COMP=1` 可关闭 compositor 做 A/B；`V14_SAT` 控制暗部饱和度倍率。
隔离复现见 `knowledge/active/%s/runs/%s/reproduction.json`。
""" % (REQ, RUN, REQ, RUN), encoding="utf-8")

RUNDIR.mkdir(parents=True, exist_ok=True)
(RUNDIR / "RUN_STATUS.json").write_text(json.dumps({
    "schema": "run-status-v1", "request_id": REQ, "run_id": RUN,
    "stage": "N7", "status": "mechanical_complete", "end_state": None,
    "failed_metrics": fails,
    "blocking": ["visual sign-off", "3-person blind test"],
    "note": "not target_met; visual cases not closed"}, ensure_ascii=False, indent=1), encoding="utf-8")

# rebind MANIFEST after all files exist (and after master_raw high-res overwrite)
man = json.loads((CAND / "MANIFEST.json").read_text(encoding="utf-8"))
for e in man["entries"]:
    p = CAND / e["path"]
    e["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
    e["bytes"] = p.stat().st_size if p.exists() else None
(CAND / "MANIFEST.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
print("FINALIZE_OK failed_metrics=", fails, "manifest_entries=", len(man["entries"]))
