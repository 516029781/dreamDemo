"""Final ledger/checkpoint/baseline update for the repair cycle."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
NOW = datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ledger_path = ROOT / "PROJECT_TASKS.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8-sig"))
    for task in ledger["tasks"]:
        if task["id"] == "P07":
            task["evidence_paths"] = [
                "tools/test_art_harness.py (52项回归, sha256 " + sha(ROOT / "tools/test_art_harness.py") + ")",
                "delivery/next_cycle/T0/gate_regression.json (52 tests + 5 selfchecks, sha256 " + sha(ROOT / "delivery/next_cycle/T0/gate_regression.json") + ")",
                "delivery/next_cycle/T0/run_gate_regression.py (可复跑生成器, sha256 " + sha(ROOT / "delivery/next_cycle/T0/run_gate_regression.py") + ")",
                "delivery/next_cycle/T0/final_audit.json (audit with 3 verified capture bindings)",
            ]
            task["commands_run"] += [
                "bundled python -X utf8 delivery/next_cycle/T0/run_gate_regression.py -> exit 0 (52 tests + 5 selfchecks)",
                "bundled python -X utf8 tools/art_harness.py audit --stage art_complete --bindings <3 final bindings> -> exit 3 (not accepted; bindings pass)",
            ]
            task["actual_exit_codes"] = [0, 0, 0, 3]
            task["self_check_note"] += " 追加UTF-16日志解码与known-exit 36精确规则反例；最终52项回归+5自检全绿。"
    ledger["revision"] = "1.0.128"
    ledger["updated_at"] = NOW
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    baseline_path = ROOT / "delivery/next_cycle/baseline.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8-sig"))
    baseline["baseline_version"] = "2.1.0"
    baseline["current_visual_revision"] = {
        "map_glb": {"path": "art/full/source/layout/MAP001_courtyard.glb",
                    "sha256": sha(ROOT / "art/full/source/layout/MAP001_courtyard.glb")},
        "engine_glb": {"path": "demo/assets/resources/models/MAP001_courtyard.glb",
                       "sha256": sha(ROOT / "demo/assets/resources/models/MAP001_courtyard.glb")},
        "env006_blend": {"path": "art/full/source/environment/ENV006_autumn_tree.blend",
                         "sha256": sha(ROOT / "art/full/source/environment/ENV006_autumn_tree.blend")},
        "bootstrap": {"path": "demo/assets/scripts/CourtyardBootstrap.ts",
                      "sha256": sha(ROOT / "demo/assets/scripts/CourtyardBootstrap.ts")},
        "captures": ["delivery/next_cycle/T3/game_final3_formal_no_ui.png",
                     "delivery/next_cycle/T3/game_final3_formal_ui.png",
                     "delivery/next_cycle/T3/game_final3_dialogue.png"],
        "bindings": "delivery/next_cycle/T3/final3_bindings_summary.json (3/3 verified)",
        "review_state": "self_check_only_not_reviewed",
        "limitations": "Independent visual review and P08 rule review remain external; V09 not released.",
    }
    baseline["updated_at"] = NOW
    baseline_path.write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    checkpoint = {
        "updated_at": NOW,
        "ledger_revision": "1.0.128",
        "status": "producer_rework_complete_waiting_external_independent_review",
        "task_id": "V05/P07 complete",
        "work_summary": ("规则返修 P00-P07 与视觉返修 V01-V05 全部完成制作侧工作：F01-F04/F08 门禁修复、"
                         "F02 冻结载荷恢复、Q01-Q09/绑定/构建门、真实canvas采集、树冠/花境/材质/光照/UI返修。"
                         "当前唯一可执行外部动作是 P08 独立规则审核；V06/V09 放行不可自签。"),
        "ledger_done": 21,
        "ledger_todo": 61,
        "open_defect_ids": ["F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08"],
        "defect_state": "producer_fixed_pending_independent_confirmation",
        "next_ready_task_ids": [],
        "external_action_ids": ["P08"],
        "overall_release_state": "not_released",
        "artifacts": {
            "final_formal": "delivery/next_cycle/T3/game_final3_formal_no_ui.png",
            "final_formal_ui": "delivery/next_cycle/T3/game_final3_formal_ui.png",
            "final_dialogue": "delivery/next_cycle/T3/game_final3_dialogue.png",
            "comparisons": ["delivery/next_cycle/T4/tree_before_after_v2.png",
                            "delivery/next_cycle/T4/material_closeups_v2.png",
                            "delivery/next_cycle/T4/plant_background_v2.png",
                            "delivery/next_cycle/T4/plant_closeups_v2.png",
                            "delivery/next_cycle/T4/lighting_comparison_v2.png",
                            "delivery/next_cycle/T4/ui_comparison_v2.png"],
            "bindings_summary": "delivery/next_cycle/T3/final3_bindings_summary.json",
            "lighting_measurement": "delivery/next_cycle/T2/lighting_profile_v2.json",
            "gate_regression": "delivery/next_cycle/T0/gate_regression.json",
            "final_audit": "delivery/next_cycle/T0/final_audit.json",
        },
        "commands_and_results": [
            {"command": "tools/blender/run_courtyard_build.ps1 -Stage env_tree,map001 (repeated during candidates)",
             "exit_code": 0, "observed": "14 measured stage runs, 656.9s total; gate pass; map GLB rebuilt",
             "limitation": "Stage timing only; failed candidate runs are included in the count/sum."},
            {"command": "tools/cocos/build_web_desktop.py (repeated)",
             "exit_code": 0, "observed": "9 builds, 190.0s total; gate pass with known-exit 36 rule",
             "limitation": "Cocos 3.8.8 exit 36 accepted only with Finished + ordered SIGTERM + output present."},
            {"command": "node delivery/next_cycle/_v06_game_shots.js final3; _v06_material_closeups.js final3; plant closeups",
             "exit_code": 0, "observed": "3 formal + 4 material + 4 plant real-canvas shots, 0 page errors",
             "limitation": "Capture wall time not separately instrumented."},
            {"command": "python delivery/next_cycle/T3/make_final_bindings.py",
             "exit_code": 0, "observed": "3/3 bindings verified against source/export/build log/output hashes",
             "limitation": "Evidence-chain proof only."},
            {"command": "python delivery/next_cycle/T0/run_gate_regression.py",
             "exit_code": 0, "observed": "52 unittest + p02-p06 selfchecks all pass",
             "limitation": "Tool runtime only; no model editing or review waiting."},
            {"command": "python tools/art_harness.py audit --stage art_complete --bindings <3>",
             "exit_code": 3, "observed": "blocked; 19 failed checks from the last independent review; bindings pass",
             "limitation": "Audit cannot override the independent visual verdict."},
        ],
        "timing": {
            "blender_measured_seconds": 656.9,
            "cocos_measured_seconds": 190.0,
            "regression_measured_seconds": 11.3,
            "captures": "not separately timed",
            "wall_clock_note": "Model reading/editing time is not instrumented; tool times above are actual measured wall times.",
        },
        "how_to_resume": [
            "P08: hand the repo state to an independent reviewer; do not self-sign. Review rules/fixtures/F01-F08 closures.",
            "After P08 passes, V06 freeze the scene_demo submission with the final GLB/captures/bindings; V07 producer preflight; V08 independent visual review; V09 controller release.",
            "Do not expand A-* or the 47-item batch before V09.",
            "V06 must bind the exact final3 artifacts; any new source/build/camera change invalidates the current bindings (use check_bindings impact).",
            "Old T1/T2 page screenshots remain historical; only the final3 canvas captures + verified bindings are current evidence.",
        ],
        "changed_files": [
            {"path": "PROJECT_TASKS.json", "sha256": sha(ROOT / "PROJECT_TASKS.json")},
            {"path": "delivery/next_cycle/baseline.json", "sha256": sha(ROOT / "delivery/next_cycle/baseline.json")},
            {"path": "delivery/next_cycle/T0/gate_regression.json", "sha256": sha(ROOT / "delivery/next_cycle/T0/gate_regression.json")},
            {"path": "delivery/next_cycle/T0/final_audit.json", "sha256": sha(ROOT / "delivery/next_cycle/T0/final_audit.json")},
            {"path": "delivery/next_cycle/T3/final3_bindings_summary.json", "sha256": sha(ROOT / "delivery/next_cycle/T3/final3_bindings_summary.json")},
        ],
    }
    checkpoint_path = ROOT / "delivery/next_cycle/last_checkpoint.json"
    checkpoint_path.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("ledger 1.0.128; checkpoint written")


if __name__ == "__main__":
    main()
