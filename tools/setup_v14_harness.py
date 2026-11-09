"""Create the v14 harness request/run identity required by space_base_check_v7.py.

    python tools/setup_v14_harness.py

Does NOT fabricate evidence: reproduction.json is written later by the real
isolated-reopen check, and evidence dirs are created empty for the checker's
dangling-path test (contents come from the actual measurements).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path("C:/软件/鼠鼠")
REQ = "20261108-space-base-v14-art"
RUN = "20261108-2035"
BASE = ROOT / "knowledge/active" / REQ
RUNDIR = BASE / "runs" / RUN
EV = RUNDIR / "evidence"
for d in (BASE, RUNDIR, EV):
    d.mkdir(parents=True, exist_ok=True)


def sha(rel):
    p = ROOT / rel
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


LOADED = [
    "planning/art/SPACE_BASE_V14_ONESHOT_PLAN_20261108.md",
    "planning/art/SPACE_BASE_TECHNICAL_ART_PLAN_20261108.md",
    "planning/art/SPACE_BASE_EXTERIOR_ORGANIC_PLAN_20261108.md",
    "knowledge/common/dev_core/HARNESS_LIFECYCLE.md",
    "knowledge/business/space_base_minigame/HARNESS_SPEC.json",
    "knowledge/business/space_base_minigame/STYLE_PROFILE.md",
    "AGENTS.md",
    "tools/blender_space_base/build_scene_v14.py",
    "tools/blender_space_base/gen_v14_from_v13.py",
    "tools/check_v14_art.py",
    "tools/check_v14_scene.py",
    "tools/space_base_check_v7.py",
]
loaded = [{"path": p, "sha256": sha(p), "scope": "active", "lifecycle": "active",
           "maturity": "observed", "usage": "requirement"} for p in LOADED]
missing = [x["path"] for x in loaded if x["sha256"] is None]
if missing:
    raise SystemExit("MISSING_LOADED " + str(missing))

brief = """# 需求 Brief：航天基地 v14 · 一次性成像层改造

- request_id：`20261108-space-base-v14-art`
- run_id：`20261108-2035`
- business_id：`space_base_minigame` / deliverable_type `static_map`
- 唯一口径：`planning/art/SPACE_BASE_V14_ONESHOT_PLAN_20261108.md`
- 触发：用户 2026-11-08 20:34「给出完整的调整方案，我要一次性开发完成」
- 状态：单批次开发，v13 冻结只读

| REQ-ID | 要求 | 验收 |
|---|---|---|
| REQ-50 | compositor 分级栈（M03） | 场景 use_nodes=True + 节点链统计 |
| REQ-51 | L0-b 色调映射采用 D（exposure −0.15） | 场景 view_settings |
| REQ-52 | 光照与明度分工（M04/M05） | A1/A2/A3/A4/A5 |
| REQ-53 | 材质族与表面响应（M06） | A6/A7 场景统计 |
| REQ-54 | 纹理幅度与边缘（M07/M08） | A8 + 目视 |
| REQ-55 | 水面三段与雾分工（M09） | 目视 + 对象统计 |
| REQ-56 | S1 light_land ≥0.45，不改判据 | check_v14_art.py |
| REQ-57 | 交付包 + MANIFEST SHA + check_v7 + 复现 + 前后对照 | space_base_check_v7.py |

不可变：画幅 1680×2478 / 7 px/m / 四厅敞顶 / 桥 B / 试车间 S-构件。
不做：场地轮廓去直角、路面 F1–F5 填充、四厅立面套件（另案）。
"""
(BASE / "REQUIREMENTS_BRIEF.md").write_text(brief, encoding="utf-8")

cases = []
for i in range(1, 9):
    rid = "REQ-%02d" % (49 + i)
    tid = "TVV14-%02d" % i
    ep = "runs/%s/evidence/%s/" % (RUN, tid)
    (BASE / ep).mkdir(parents=True, exist_ok=True)
    cases.append({"test_id": tid, "covers": [rid], "stage": "final",
                  "check_type": "mechanical", "responsible": "automated",
                  "evidence_path": ep, "diagnostic_only": False,
                  "pass_criteria": "see REQUIREMENTS_BRIEF", "failure_rule": "return to N6"})
tc = {"schema": "test-cases-v1", "request_id": REQ, "business_id": "space_base_minigame",
      "version": "v14", "cases": cases}
(BASE / "test_cases.json").write_text(json.dumps(tc, ensure_ascii=False, indent=1), encoding="utf-8")
(RUNDIR / "test_cases.json").write_text(json.dumps(tc, ensure_ascii=False, indent=1), encoding="utf-8")

ctx = {"schema": "run-context-v1", "request_id": REQ, "run_id": RUN,
       "business_id": "space_base_minigame", "deliverable_type": "static_map",
       "task_mode": "production", "harness_stage": "N7",
       "candidate": "art/static_map/space_base_minigame/v14",
       "parent_candidate": "art/static_map/space_base_minigame/v13 (frozen, readonly)",
       "checks": {"harness_spec": "knowledge/business/space_base_minigame/HARNESS_SPEC.json",
                  "checker": "tools/space_base_check_v7.py",
                  "art": "tools/check_v14_art.py", "scene": "tools/check_v14_scene.py"}}
(BASE / "RUN_CONTEXT.json").write_text(json.dumps(ctx, ensure_ascii=False, indent=1), encoding="utf-8")
(RUNDIR / "RUN_CONTEXT.json").write_text(json.dumps(ctx, ensure_ascii=False, indent=1), encoding="utf-8")

res = {"schema": "resolved-knowledge-v1", "request_id": REQ, "run_id": RUN,
       "business_id": "space_base_minigame", "loaded": loaded,
       "decisions": [
           {"rule_id": "Q-T1", "decision": "A cool-grey base + warm accents"},
           {"rule_id": "Q-T2", "decision": "color management changed only in the v14 branch"},
           {"rule_id": "Q-T3", "decision": "S1 contract unchanged; P0 measured 0.614"},
           {"rule_id": "L0-b", "decision": "candidate D (Standard / None / -0.15)"},
       ]}
(BASE / "RESOLVED_KNOWLEDGE.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
(RUNDIR / "RESOLVED_KNOWLEDGE.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

print("HARNESS_SETUP_OK", REQ, RUN, "loaded=", len(loaded), "cases=", len(cases))
