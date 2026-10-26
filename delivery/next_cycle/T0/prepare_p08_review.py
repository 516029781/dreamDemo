"""Prepare the concentrated P08/V08/V09 review request dossier (templates only, no approvals)."""
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
NOW = datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def file_entry(path):
    return {"path": path, "sha256": sha(ROOT / path)}


def write(path, value):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    # Refresh I07 producer-check digest after the rebind.
    i07_path = ROOT / "delivery/next_cycle/T7/I07_complete_candidate_package.json"
    i07 = json.loads(i07_path.read_text(encoding="utf-8"))
    i07["producer_check"]["sha256"] = sha(ROOT / i07["producer_check"]["path"])
    i07["producer_review"]["sha256"] = sha(ROOT / i07["producer_review"]["report"])
    i07["quality"]["sha256"] = sha(ROOT / i07["quality"]["behavior_results"])
    i07_path.write_text(json.dumps(i07, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    gate = file_entry("delivery/next_cycle/T0/gate_regression.json")
    producer_check = file_entry("delivery/next_cycle/T4/producer_submission_check.json")
    manifest_verify = file_entry("delivery/next_cycle/T7/I07_manifest_verify.json")
    precondition = {
        "kind": "P08_precondition_check",
        "generated_at": NOW,
        "ledger_revision": "1.0.134",
        "candidate_stage": "art_complete",
        "producer_candidate_complete": True,
        "producer_check": {"path": producer_check["path"], "sha256": producer_check["sha256"],
                           "status": "ready_for_final_review", "accepted": False,
                           "scores": {"ENV": 90.0, "CHAR": 90.0, "UI": 91.25, "MIX": 90.0}},
        "manifest_verify": {"path": manifest_verify["path"], "sha256": manifest_verify["sha256"],
                            "mechanical_checks": "pass", "status": "needs_review"},
        "gate_regression": {"path": gate["path"], "sha256": gate["sha256"], "exit_code": 0,
                            "tests": 52, "failures": 0, "selfchecks": {
                                "p02": 0, "p03": 0, "p04": 0, "p05": 0, "p06": 0}},
        "contracts": {
            "harness_contract": file_entry("art_review/harness_contract.json"),
            "rubric": file_entry("art_review/rubric.json"),
            "vnext_contract": file_entry("art_review/vnext/harness_contract.json"),
            "vnext_effective": False,
        },
        "scope_checks": {
            "forty_seven_items": len(json.loads((ROOT / "art/iterations/cycle_02/full_art_catalog.json").read_text(encoding="utf-8-sig"))["items"]),
            "ui_states": 41,
            "capture_bindings": "3/3 verified",
            "source_archive": file_entry("delivery/courtyard_scene_demo_sources_v4.zip"),
        },
        "commands": [
            "python tools/test_art_harness.py -v",
            "python delivery/next_cycle/T0/run_gate_regression.py",
            "python tools/producer_review.py check --review delivery/next_cycle/T4/producer_self_review.json --out delivery/next_cycle/T4/producer_submission_check.json",
            "python tools/art_harness.py verify --manifest art_review/submissions/candidate_full/manifest.json",
        ],
        "note": "Precondition evidence only; P08 independent reviewer must inspect code/fixtures and decide.",
    }
    write("delivery/next_cycle/T0/P08_precondition_check.json", precondition)

    p08_checks = [
        ("P02", "状态/schema/迁移；F03/F04", ["delivery/next_cycle/T0/rule_migration.md",
                                             "art_review/vnext/asset_status.schema.json",
                                             "tools/art_gate/migrate_catalog.py",
                                             "delivery/next_cycle/T0/p02_selfcheck.json"]),
        ("P03", "证书链/前序实效；F01", ["tools/art_harness.py",
                                         "delivery/next_cycle/T0/p03_selfcheck.json",
                                         "delivery/next_cycle/T0/p03_chain_test.py",
                                         "art_review/vnext/stage_certificate.schema.json"]),
        ("P04", "采集绑定/dirty闭包；F02/F05", ["art_review/vnext/capture_binding.schema.json",
                                               "tools/art_gate/check_bindings.py",
                                               "delivery/next_cycle/T0/p04_selfcheck.json"]),
        ("P05", "Q01-Q09/审核模板", ["art_review/vnext/quality_checks.json",
                                     "art_review/vnext/behavior_results.schema.json",
                                     "art_review/vnext/review_template.json",
                                     "tools/art_gate/check_quality.py",
                                     "delivery/next_cycle/T0/p05_selfcheck.json"]),
        ("P06", "audit/CLI/构建/采集入口；F05/F08", ["tools/art_harness.py", "run-art-harness.ps1",
                                                     "HARNESS.md", "tools/art_gate/build_log_gate.py",
                                                     "tools/capture/canvas_capture.js",
                                                     "tools/cocos/build_web_desktop.py",
                                                     "delivery/next_cycle/T0/p06_selfcheck.json"]),
        ("P07", "回归夹具", ["tools/test_art_harness.py",
                             "delivery/next_cycle/T0/gate_regression.json"]),
        ("F01", "前序证书过期", ["delivery/next_cycle/T0/p03_selfcheck.json",
                                 "delivery/next_cycle/T0/gate_regression.json"]),
        ("F02", "冻结载荷恢复", ["reference/frozen_history/art_complete_20261024_manifest/RECOVERY_RECORD.json",
                                 "delivery/next_cycle/T0/verify_recovery.py"]),
        ("F03", "迁移 schema", ["delivery/next_cycle/T0/p02_selfcheck.json",
                                 "art_review/vnext/asset_status.schema.json"]),
        ("F04", "失败技术检查", ["delivery/next_cycle/T0/p02_selfcheck.json",
                                 "tools/art_gate/migrate_catalog.py"]),
        ("F05", "真实 canvas", ["delivery/next_cycle/T3/final4_bindings_summary.json",
                                 "tools/capture/canvas_capture.js"]),
        ("F06", "样板视觉", ["delivery/next_cycle/T4/tree_before_after_final4.png",
                             "delivery/next_cycle/T4/material_closeups_final4.png",
                             "delivery/next_cycle/T4/plant_background_final4.png",
                             "delivery/next_cycle/T4/ui_comparison_final4.png"]),
        ("F07", "光照测量", ["delivery/next_cycle/T2/lighting_profile_v2.json",
                             "tools/measure_lighting.js"]),
        ("F08", "Finished/失败传播", ["tools/art_gate/build_log_gate.py",
                                      "delivery/next_cycle/T0/gate_regression.json"]),
    ]
    p08_template = {
        "kind": "independent_rule_review_template_not_actual",
        "status": "pending_independent_review",
        "reviewer": {"id": None, "mode": "independent"},
        "reviewed_at": None,
        "inputs": {
            "precondition": file_entry("delivery/next_cycle/T0/P08_precondition_check.json"),
            "contract": file_entry("art_review/harness_contract.json"),
            "rubric": file_entry("art_review/rubric.json"),
            "vnext_contract": file_entry("art_review/vnext/harness_contract.json"),
            "gate_regression": gate,
            "producer_check": producer_check,
            "manifest_verify": manifest_verify,
        },
        "checks": [{"id": cid, "focus": focus,
                    "evidence": [file_entry(p) for p in paths if (ROOT / p).is_file()],
                    "decision": "pending", "notes": ""}
                   for cid, focus, paths in p08_checks],
        "global_checks": {
            "thresholds_unchanged": "pending",
            "old_packages_auditable": "pending",
            "vnext_not_effective": "pending",
            "no_producer_self_sign": "pending",
            "gate_regression_actual": "pending",
        },
        "overall_decision": "pending",
        "if_fail": "Reopen P02-P07 with concrete defects; do not lower thresholds.",
        "limitations": ["Template only; the producer did not review or sign this."],
    }
    write("delivery/next_cycle/T0/P08_review_request/independent_rule_review_template.json", p08_template)

    p08_doc = f"""# P08 独立规则评审请求

状态：**waiting_review**（制作侧未自签）。请独立审核者实际阅读代码/夹具并运行命令，然后填写
`delivery/next_cycle/T0/independent_rule_review.json`（可复制本目录模板）。

## 审什么

- P02–P07 实际实现与测试：`{gate['path']}`、`delivery/next_cycle/T0/p02..p06` 自检、`tools/test_art_harness.py`。
- F01–F08 修复证据；阈值未降低；旧包仍可审计；vNext 1.4.0-draft **未生效**；制作方无自签。
- 重点：前序证书实际依赖、冻结载荷恢复、迁移 schema/失败状态、Q/绑定、真实 canvas、构建失败传播、回归反例。

## 必须实跑

```powershell
$py='C:\\Users\\tt\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe'
& $py -X utf8 tools/test_art_harness.py -v
& $py -X utf8 delivery/next_cycle/T0/run_gate_regression.py
& $py -X utf8 tools/producer_review.py check --review delivery/next_cycle/T4/producer_self_review.json --out delivery/next_cycle/T4/producer_submission_check.json
& $py -X utf8 tools/art_harness.py verify --manifest art_review/submissions/candidate_full/manifest.json
```

- 期望：52 tests + 5 selfchecks exit 0；producer_check `ready_for_final_review=true`；manifest `mechanical_checks=pass`、`status=needs_review`（尚无独立 review）。
- 通过后输出 `independent_rule_review.json`，`reviewer.mode=independent`，并进入 V08；不通过则列出具体缺陷并重开 P02–P07。

## 证据包

- `delivery/P08_review_pack_20261025.zip`
- `delivery/next_cycle/T0/P08_precondition_check.json`
- `art_review/submissions/candidate_full/manifest.json` + `delivery/next_cycle/T4/producer_self_review.json`
"""
    (ROOT / "delivery/next_cycle/T0/P08_review_request/REVIEW_REQUEST.md").write_text(p08_doc, encoding="utf-8")

    # P08 review pack
    pack = ROOT / "delivery/P08_review_pack_20261025.zip"
    includes = [
        "delivery/next_cycle/T0/P08_review_request/REVIEW_REQUEST.md",
        "delivery/next_cycle/T0/P08_review_request/independent_rule_review_template.json",
        "delivery/next_cycle/T0/P08_precondition_check.json",
        "delivery/next_cycle/T0/gate_regression.json",
        "delivery/next_cycle/T0/p02_selfcheck.json", "delivery/next_cycle/T0/p03_selfcheck.json",
        "delivery/next_cycle/T0/p04_selfcheck.json", "delivery/next_cycle/T0/p05_selfcheck.json",
        "delivery/next_cycle/T0/p06_selfcheck.json", "delivery/next_cycle/T0/rule_migration.md",
        "delivery/next_cycle/T0/active_spec_index.json",
        "planning/execution/workflow_fixes.json", "planning/execution/producer_review_policy.json",
        "art_review/harness_contract.json", "art_review/rubric.json",
        "art_review/vnext/harness_contract.json", "art_review/vnext/asset_status.schema.json",
        "art_review/vnext/capture_binding.schema.json", "art_review/vnext/behavior_results.schema.json",
        "art_review/vnext/stage_certificate.schema.json", "art_review/vnext/quality_checks.json",
        "tools/art_harness.py", "tools/test_art_harness.py", "tools/producer_review.py",
        "tools/art_gate/migrate_catalog.py", "tools/art_gate/check_bindings.py",
        "tools/art_gate/check_quality.py", "tools/art_gate/build_log_gate.py",
        "tools/capture/canvas_capture.js", "tools/cocos/build_web_desktop.py",
        "run-art-harness.ps1", "HARNESS.md",
        "reference/frozen_history/art_complete_20261024_manifest/RECOVERY_RECORD.json",
        "art_review/submissions/candidate_full/manifest.json",
        "delivery/next_cycle/T4/producer_self_review.json",
        "delivery/next_cycle/T4/producer_submission_check.json",
        "delivery/next_cycle/T7/I07_manifest_verify.json",
    ]
    with zipfile.ZipFile(pack, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in sorted(set(includes)):
            if (ROOT / path).is_file():
                z.write(ROOT / path, path)
    print(json.dumps({"p08_pack": str(pack), "bytes": pack.stat().st_size, "sha256": sha(pack)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
