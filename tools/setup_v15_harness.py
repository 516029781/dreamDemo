"""Create the v15 harness request/run identity required by space_base_check_v7.py.

    python tools/setup_v15_harness.py

Does NOT fabricate evidence: reproduction.json is written later by the real
isolated-reopen check, and evidence dirs are created empty for the checker's
dangling-path test (contents come from the actual measurements).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path("C:/软件/鼠鼠")
REQ = "20261108-space-base-v15-rooms"
RUN = "20261108-2320"
BASE = ROOT / "knowledge/active" / REQ
RUNDIR = BASE / "runs" / RUN
EV = RUNDIR / "evidence"
for d in (BASE, RUNDIR, EV):
    d.mkdir(parents=True, exist_ok=True)


def sha(rel):
    p = ROOT / rel
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


LOADED = [
    "planning/art/SPACE_BASE_CORE_ROOMS_ART_PLAN_20261108.md",
    "planning/art/SPACE_BASE_CORE_ROOMS_CHECK_20261108.md",
    "planning/art/SPACE_BASE_INTERIOR_DRESSING_20261102.md",
    "knowledge/common/dev_core/HARNESS_LIFECYCLE.md",
    "knowledge/business/space_base_minigame/HARNESS_SPEC.json",
    "knowledge/business/space_base_minigame/STYLE_PROFILE.md",
    "AGENTS.md",
    "tools/blender_space_base/build_scene_v15.py",
    "tools/blender_space_base/v15_rooms_src.py",
    "tools/blender_space_base/gen_v15_from_v14.py",
    "tools/check_v15_scene.py",
    "tools/post_v15.py",
    "tools/space_base_check_v7.py",
]
loaded = [{"path": p, "sha256": sha(p), "scope": "active", "lifecycle": "active",
           "maturity": "observed", "usage": "requirement"} for p in LOADED]
missing = [x["path"] for x in loaded if x["sha256"] is None]
if missing:
    raise SystemExit("MISSING_LOADED " + str(missing))

brief = """# 需求 Brief：航天基地 v15 · 四核心区内部重建

- request_id：`20261108-space-base-v15-rooms`
- run_id：`20261108-2320`
- business_id：`space_base_minigame` / deliverable_type `static_map`
- 唯一口径：`planning/art/SPACE_BASE_CORE_ROOMS_ART_PLAN_20261108.md`（v1.3）
- 复核：`planning/art/SPACE_BASE_CORE_ROOMS_CHECK_20261108.md`
- 触发：用户 2026-11-08 22:49「可以按你的推荐执行」（Q2/Q5/Q6/Q7 全部按建议裁决）
- 状态：单批次开发，v14 冻结只读

| REQ-ID | 要求 | 验收 |
|---|---|---|
| REQ-58 | 四厅按实机重建 L1 标志物（每厅 4–6 件） | check_v15_scene.py I1 |
| REQ-59 | 墙顶 0.55 m 压顶按厅上色（青/冷灰青/藏蓝/绿） | I4 |
| REQ-60 | 色带 ≤1.2 m、只做 1–2 面墙；取消 2 m 四圈与整圈黄栏杆 | I2 + 目视 |
| REQ-61 | 中间尺度成组构件 ≥0.045 件/m²（每厅 ≥52 件 1–3 m） | I11 |
| REQ-62 | 每厅 ≥1 组亮/暗成对贴地投影 | I12 |
| REQ-63 | 敞顶单层 / 无总裁室 / 无横跨铺板 | I7 |
| REQ-64 | S1 ≥0.45、S2 ≤0.12、S3 ≤0.02（不改判据），同报 water_frac | post_v15.py I8 |
| REQ-65 | 交付包 + MANIFEST SHA + check_v7 + 前后同机位对照 | space_base_check_v7.py I9 |

不可变：画幅 284.7×420 m / 5.902 px/m / 1680×2478 / 四厅 34×34 / 十字过道 10 / 场地 +4.70。
不做：总裁室与十字暖色地标（用户 22:19 裁决）、四厅立面套件（hero 另案）、场地轮廓去直角、路面 F1–F5 填充。
裁决记录：Q2 单梁按 TV13-03 先例豁免；Q5 H2 池口以截图为准（取消整圈黄栏杆）；
Q6 接受冷暗被 S1 判为水体、P3 同报 water_frac；Q7 52 件/厅在预算内。
"""
(BASE / "REQUIREMENTS_BRIEF.md").write_text(brief, encoding="utf-8")

cases = []
for i in range(1, 9):
    rid = "REQ-%02d" % (57 + i)
    tid = "TVV15-%02d" % i
    ep = "runs/%s/evidence/%s/" % (RUN, tid)
    (BASE / ep).mkdir(parents=True, exist_ok=True)
    cases.append({"test_id": tid, "covers": [rid], "stage": "final",
                  "check_type": "mechanical", "responsible": "automated",
                  "evidence_path": ep, "diagnostic_only": False,
                  "pass_criteria": "see REQUIREMENTS_BRIEF", "failure_rule": "return to N6"})
tc = {"schema": "test-cases-v1", "request_id": REQ, "business_id": "space_base_minigame",
      "version": "v15", "cases": cases}
(BASE / "test_cases.json").write_text(json.dumps(tc, ensure_ascii=False, indent=1), encoding="utf-8")
(RUNDIR / "test_cases.json").write_text(json.dumps(tc, ensure_ascii=False, indent=1), encoding="utf-8")

ctx = {"schema": "run-context-v1", "request_id": REQ, "run_id": RUN,
       "business_id": "space_base_minigame", "deliverable_type": "static_map",
       "task_mode": "production", "harness_stage": "N7",
       "candidate": "art/static_map/space_base_minigame/v15",
       "parent_candidate": "art/static_map/space_base_minigame/v13 (frozen, readonly)",
       "checks": {"harness_spec": "knowledge/business/space_base_minigame/HARNESS_SPEC.json",
                  "checker": "tools/space_base_check_v7.py",
                  "art": "tools/check_v15_art.py", "scene": "tools/check_v15_scene.py"}}
(BASE / "RUN_CONTEXT.json").write_text(json.dumps(ctx, ensure_ascii=False, indent=1), encoding="utf-8")
(RUNDIR / "RUN_CONTEXT.json").write_text(json.dumps(ctx, ensure_ascii=False, indent=1), encoding="utf-8")

res = {"schema": "resolved-knowledge-v1", "request_id": REQ, "run_id": RUN,
       "business_id": "space_base_minigame", "loaded": loaded,
       "decisions": [
           {"rule_id": "Q-T1", "decision": "keep the warm-sand land / cool-water split; hall identity by shape first, colour second"},
           {"rule_id": "Q-T2", "decision": "colour management unchanged from v14 (Standard, no LUT, gamma 1.10)"},
           {"rule_id": "Q-T3", "decision": "S1 >= 0.45 unchanged; the v1.2 25%% dark-area cap was retracted after measurement"},
           {"rule_id": "Q5", "decision": "H2 pool rim follows the screenshot: concrete upstand + 1.2 m teal cap + black guard runs, no full yellow ring"},
           {"rule_id": "Q6", "decision": "cool darks are read as water by the S1 mask; water_frac is reported next to S1"},
           {"rule_id": "Q7", "decision": "52 mid-scale parts per hall fits the 450-object budget"},
           {"rule_id": "Q1", "decision": "no exec suite: build_ceo and the CEO constant are removed from the v15 builder"},
       ]}
(BASE / "RESOLVED_KNOWLEDGE.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
(RUNDIR / "RESOLVED_KNOWLEDGE.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

print("HARNESS_SETUP_OK", REQ, RUN, "loaded=", len(loaded), "cases=", len(cases))
