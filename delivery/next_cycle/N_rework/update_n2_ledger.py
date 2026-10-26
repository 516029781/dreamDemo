"""Update ledger and checkpoint for the candidate_n2 rework."""
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
NOW = datetime.now(timezone.utc).isoformat()


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8-sig"))


def write(rel, value):
    (ROOT / rel).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    led = load("PROJECT_TASKS.json")
    for t in led["tasks"]:
        if t["id"] == "I07":
            t["status"] = "rework"
            t["outputs"] = [
                "art_review/submissions/candidate_n2/manifest.json",
                "delivery/next_cycle/T7/I07_manifest_verify.json",
                "delivery/next_cycle/T4/producer_self_review.json",
                "delivery/next_cycle/T4/producer_submission_check.json",
                "delivery/next_cycle/N_rework/REWORK_REPORT.md",
            ]
            t["acceptance"] = [
                "47项候选覆盖，源/导出/构建/截图同源；保留旧包与新版本索引。",
                "N01-N08 返修后重跑 Q01-Q09、绑定、全状态图和自审；制作侧 90 门槛未通过，如实记录 70/93.75/75/75。",
                "提交最终独立审核请求；不得把制作侧自评写成独立通过，不得修改 accepted。",
            ]
            t["evidence_paths"] = [
                "art_review/submissions/candidate_n2/manifest.json",
                "delivery/next_cycle/T7/I07_manifest_verify.json",
                "delivery/next_cycle/T7/I07_complete_candidate_package.json",
                "delivery/next_cycle/T4/producer_self_review.json",
                "delivery/next_cycle/T4/producer_submission_check.json",
                "delivery/next_cycle/N_rework/REWORK_REPORT.md",
                "delivery/next_cycle/N_rework/FINAL_REVIEW_REQUEST.md",
                "delivery/candidate_n2_review_pack_20261025.zip",
                "delivery/candidate_n2_review_pack_20261025.zip.sha256",
                "delivery/next_cycle/N_rework/N08_pack_plan.json",
                "delivery/N08_pack_verification.json",
                "delivery/courtyard_scene_demo_sources_v5.zip",
                "delivery/RUN_DEMO_v5.md",
                "delivery/COMPLETE_CANDIDATE_DELIVERY.md",
                "art/iterations/cycle_03/full_art_catalog.json",
            ]
            t["commands_run"] = [
                "build_n_evidence.py -> Q01-Q09 pass on finalN2; 3 bindings verified",
                "producer_review.py check -> producer_rework_required; ENV70/CHAR93.75/UI75/MIX75",
                "art_harness.py verify candidate_n2 -> mechanical_checks=pass, needs_review",
            ]
            t["actual_exit_codes"] = [0, 3, 3]
            t["related_defects"] = ["F05", "F06", "F07", "N01", "N02", "N03", "N04", "N05", "N06", "N07", "N08"]
            t["blocker"] = ("Producer self-review did not meet the 90 threshold on ENV/UI/MIX "
                            "(and ENV geometry_craft core floor); independent final review requested.")
            t["resume_action"] = ("Independent reviewer: use FINAL_REVIEW_REQUEST.md and candidate_n2 pack; "
                                  "if fail, continue ENV/UI/MIX repair. Producer must not self-sign.")
        if t["id"] == "I08":
            t["status"] = "waiting_review"
            t["evidence_paths"] = [
                "delivery/next_cycle/N_rework/FINAL_REVIEW_REQUEST.md",
                "art_review/submissions/candidate_n2/manifest.json",
                "delivery/candidate_n2_review_pack_20261025.zip",
                "delivery/candidate_n2_review_pack_20261025.zip.sha256",
                "delivery/next_cycle/N_rework/REWORK_REPORT.md",
                "delivery/next_cycle/T4/producer_self_review.json",
                "delivery/next_cycle/T4/producer_submission_check.json",
                "delivery/N08_pack_verification.json",
            ]
            t["blocker"] = ("Independent full art review pending; producer self-review is below the 90 threshold "
                            "and is not a pass.")
            t["resume_action"] = ("Independent reviewer scores rubric 1.2.0 on actual media and behavior; output new report; "
                                  "producer must not sign.")
        if t["id"] == "P08":
            t["resume_action"] = ("Independent rule reviewer runs P08 commands. Candidate_n2 exists for the separate full art review; "
                                  "P08 remains a rule-review gate and is not signed by the producer.")
        if t["id"] == "V08":
            t["resume_action"] = ("Sample review chain remains external and unstarted; "
                                  "do not substitute for the candidate_n2 full review.")
        if t["id"] == "I09":
            t["resume_action"] = ("Controller release only after I08; external key/certificate required; "
                                  "producer must not generate or alter accepted.")
    led["revision"] = "1.0.136"
    led["updated_at"] = NOW
    led["workflow_review_note"] = ("N01-N08 rework candidate frozen as candidate_n2; producer self-review honestly failed the 90 gate; "
                                   "final independent review requested per user instruction.")
    write("PROJECT_TASKS.json", led)

    counts = {}
    for t in led["tasks"]:
        counts[t["status"]] = counts.get(t["status"], 0) + 1
    print("counts", counts, "tasks", len(led["tasks"]))

    cp = {
        "updated_at": NOW,
        "ledger_revision": "1.0.136",
        "status": "waiting_external_candidate_review",
        "task_id": "N01-N08 rework candidate (candidate_n2)",
        "work_summary": ("N01-N08 fixes completed: Q01 real bbox 130x130, Q09 natural portrait/resize, "
                         "N07 real 6-frame idle/move GIFs, N01/N02/N03 native visual iteration, N06 honest self-review, "
                         "N08 repack. Producer self-review ENV70/CHAR93.75/UI75/MIX75 -> producer_rework_required; "
                         "final review requested anyway, no self-approval."),
        "ledger_done": counts.get("done", 0),
        "ledger_todo": counts.get("todo", 0),
        "status_counts": counts,
        "open_defect_ids": ["F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08",
                            "R01", "R02", "R03", "R04", "R05", "R06", "R07", "R08", "R09", "R10",
                            "N01", "N02", "N03", "N04", "N05", "N06", "N07", "N08"],
        "defect_state": "producer_fixed_pending_independent_confirmation; scores below producer 90 gate",
        "next_ready_task_ids": [],
        "external_action_ids": ["I08"],
        "overall_release_state": "not_released",
        "artifacts": {
            "manifest": "art_review/submissions/candidate_n2/manifest.json",
            "scene_no_ui": "delivery/next_cycle/T3/game_finalN2_formal_no_ui.png",
            "scene_hud": "delivery/next_cycle/T3/game_finalN2_formal_ui.png",
            "scene_dialogue": "delivery/next_cycle/T3/game_finalN2_dialogue.png",
            "comparisons": ["delivery/next_cycle/T4/N01_tree_hedge_before_after.png",
                            "delivery/next_cycle/T4/N02_shadow_before_after.png",
                            "delivery/next_cycle/T4/N02_material_closeups.png",
                            "delivery/next_cycle/T4/N03_ui_before_after.png",
                            "delivery/next_cycle/T4/N04_actor_bbox.png",
                            "delivery/next_cycle/T4/N05_orientation.png",
                            "delivery/next_cycle/T6/character_n/N07_animation_sheet.png"],
            "bindings_summary": "art_review/submissions/candidate_n2/bindings/summary.json",
            "quality_results": "delivery/next_cycle/N_rework/behavior_results_n.json",
            "quality_check": "delivery/next_cycle/N_rework/quality_check_n.json",
            "self_review": "delivery/next_cycle/T4/producer_self_review.json",
            "producer_check": "delivery/next_cycle/T4/producer_submission_check.json",
            "pack": "delivery/candidate_n2_review_pack_20261025.zip",
            "pack_sha256": "delivery/candidate_n2_review_pack_20261025.zip.sha256",
            "pack_verification": "delivery/N08_pack_verification.json",
            "source_zip": "delivery/courtyard_scene_demo_sources_v5.zip",
            "run_instructions": "delivery/RUN_DEMO_v5.md",
            "catalog": "art/iterations/cycle_03/full_art_catalog.json",
            "rework_report": "delivery/next_cycle/N_rework/REWORK_REPORT.md",
            "final_review_request": "delivery/next_cycle/N_rework/FINAL_REVIEW_REQUEST.md",
        },
        "commands_and_results": [
            {"command": "_t5_probe.js", "exit_code": 0, "observed": "50 outputs, 0 page errors; Q01-Q09 evidence on finalN2"},
            {"command": "_t6_all_states.js", "exit_code": 0, "observed": "41 UI states, 34 asset previews, 24 frames, 0 errors"},
            {"command": "_v06_game_shots.js finalN2; _v06_material_closeups.js finalN2; _v06_plant_closeups.js finalN2",
             "exit_code": 0, "observed": "3 formal + 4 material + 4 plant real-canvas shots"},
            {"command": "_t6_demo.js", "exit_code": 0, "observed": "16-frame demo GIF"},
            {"command": "_n04_bbox.js", "exit_code": 0, "observed": "real visible-hidden bbox 130x130, pass"},
            {"command": "_n05_orientation.js", "exit_code": 0,
             "observed": "fresh portrait 720x1280 rotate_notice + inputLock; resize and restore pass"},
            {"command": "_n07_animation.js", "exit_code": 0,
             "observed": "idle 6 unique frames, move 6 unique frames, trackTime advances"},
            {"command": "build_n_evidence.py", "exit_code": 0,
             "observed": "3 bindings verified; Q01-Q09 pass; warnings Q06 draws 715, Q09 no device"},
            {"command": "build_catalog_v3.py", "exit_code": 0, "observed": "47-item cycle_03 catalog + 47 reviews"},
            {"command": "art_harness.py prepare/verify candidate_n2", "exit_code": 0,
             "observed": "mechanical_checks=pass, status=needs_review, accepted=false"},
            {"command": "producer_review.py check", "exit_code": 3,
             "observed": "producer_rework_required; ENV70/CHAR93.75/UI75/MIX75; ENV geometry_craft below core floor"},
            {"command": "source zip v5 rebuild + N08 pack verification", "exit_code": 0,
             "observed": "source v5 241 entries; final pack verified against disk; outer checksum written"},
        ],
        "timing": {
            "final_cocos_build_seconds": 171.5,
            "measured_note": "Blender stage timing from earlier cycles; this N round is dominated by real capture and review, not a single build duration.",
        },
        "limitations": [
            "No phone/WeChat device test; Q09 browser-only.",
            "No full gameplay loop or performance/package acceptance.",
            "ENV/UI/MIX visual gap remains; producer filter failed.",
            "Independent review/controller release not signed.",
        ],
        "how_to_resume": [
            "Independent reviewer uses delivery/next_cycle/N_rework/FINAL_REVIEW_REQUEST.md.",
            "If rework: fix ENV geometry/material/light, then UI paper/doodle, then MIX; recapture affected evidence and rescore.",
            "I09 controller release only after I08; external key/certificate; producer never alters accepted.",
        ],
    }
    write("delivery/next_cycle/last_checkpoint.json", cp)
    print("checkpoint written")


if __name__ == "__main__":
    main()
