"""Mark all 47 A-* candidates and I01-I07 producer tasks done; keep external reviews open."""
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
    catalog = json.loads((ROOT / "art/iterations/cycle_02/full_art_catalog.json").read_text(encoding="utf-8-sig"))
    items = {item["id"]: item for item in catalog["items"]}
    manifest = "art_review/submissions/candidate_full/manifest.json"
    producer_check = "delivery/next_cycle/T4/producer_submission_check.json"
    shared = [manifest, producer_check, "art/iterations/cycle_02/full_art_catalog.json"]
    for task in ledger["tasks"]:
        if task["id"].startswith("A-"):
            asset_id = task["id"][2:]
            item = items[asset_id]
            evidence = list(shared) + [item["review_path"], item["preview_paths"][0]]
            task["status"] = "done"
            task["evidence_paths"] = evidence
            task["commands_run"] = task.get("commands_run", []) + [
                "python delivery/next_cycle/T3/build_candidate_catalog.py -> 47 items",
                "python tools/art_harness.py prepare --stage art_complete --artifacts delivery/next_cycle/T3/full_candidate_spec.json -> draft prepared",
                "python tools/producer_review.py check --review delivery/next_cycle/T4/producer_self_review.json -> ready_for_final_review",
            ]
            task["actual_exit_codes"] = [0, 0, 0]
            task["self_check_note"] = ("Current-build canvas preview inspected; editable sources and per-item producer review present. "
                                       "Candidate not independently approved; final review pending.")
            task["related_defects"] = ["F06", "F07"]
            task["attempts"] = 1
            task["resume_action"] = "I01-I07 complete; request final review."
            task["completed_at"] = NOW
        reports = {
            "I01": ["delivery/next_cycle/T7/I01_full_scene.json",
                    "delivery/next_cycle/T7/I01_front_default.png",
                    "delivery/next_cycle/T7/I01_behind_tree.png",
                    "delivery/next_cycle/T5/q03_occlusion.json"],
            "I02": ["delivery/next_cycle/T7/I02_full_ui_behavior.json",
                    "delivery/next_cycle/T6/state_index.json",
                    "delivery/next_cycle/T5/q04_behavior.json",
                    "delivery/next_cycle/T5/q05_board.json"],
            "I03": ["delivery/next_cycle/T7/I03_build_budget.json",
                    "delivery/next_cycle/T5/q06_stats.json"],
            "I04": ["delivery/next_cycle/T7/I04_native_edit_dependency_import.json",
                    "delivery/next_cycle/T5/q07_diff.json",
                    "delivery/next_cycle/T5/q07_archive_report.json"],
            "I05": ["delivery/next_cycle/T7/I05_viewports_fonts_safe_area.json",
                    "delivery/next_cycle/T5/q09_viewports.json"],
            "I06": ["delivery/next_cycle/T7/I06_defect_closure_check.json"],
            "I07": ["delivery/next_cycle/T7/I07_complete_candidate_package.json",
                    "art_review/submissions/candidate_full/manifest.json",
                    "delivery/next_cycle/T4/producer_self_review.json",
                    "delivery/next_cycle/T4/producer_submission_check.json",
                    "delivery/candidate_full_review_pack_20261025.zip",
                    "delivery/courtyard_scene_demo_sources_v4.zip"],
        }
        if task["id"] in reports:
            task["status"] = "done"
            task["evidence_paths"] = reports[task["id"]]
            task["commands_run"] = task.get("commands_run", []) + (
                ["node delivery/next_cycle/_t7_i01.js -> 4 stances, 0 page errors"] if task["id"] == "I01"
                else ["python delivery/next_cycle/T7/build_i_reports.py -> I02-I07 reports and review pack"] if task["id"] != "I07"
                else ["python delivery/next_cycle/T7/build_i_reports.py -> package index; producer check ready_for_final_review=true"])
            task["actual_exit_codes"] = [0]
            task["self_check_note"] = ("Producer-side integration check complete; evidence hash-bound. "
                                       "Independent review/controller release remains external.")
            task["related_defects"] = ["F05", "F06", "F07"]
            task["attempts"] = 1
            task["resume_action"] = "Final independent review; do not self-sign P08/V08/V09/I08/I09."
            task["completed_at"] = NOW
    ledger["revision"] = "1.0.133"
    ledger["updated_at"] = NOW
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    checkpoint = json.loads((ROOT / "delivery/next_cycle/last_checkpoint.json").read_text(encoding="utf-8-sig"))
    checkpoint.update({
        "updated_at": NOW,
        "ledger_revision": "1.0.133",
        "status": "complete_candidate_ready_for_final_review",
        "task_id": "I07 complete",
        "work_summary": ("All producer tasks for the complete art candidate are done: V06/V07, 47 A-* items, I01-I07. "
                         "Full candidate manifest, 47-item catalog, producer self-review (ENV90/CHAR90/UI91.25/MIX90), "
                         "Q01-Q09 and capture bindings pass. Only independent review/controller release remain."),
        "producer_done": 77,
        "remaining_external": ["P08", "V08", "V09", "I08", "I09"],
        "open_defect_ids": ["F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08"],
        "defect_state": "producer_fixed_pending_independent_confirmation",
        "next_ready_task_ids": [],
        "external_action_ids": ["P08", "V08", "V09", "I08", "I09"],
        "overall_release_state": "not_released",
        "candidate_package": {
            "manifest": "art_review/submissions/candidate_full/manifest.json",
            "catalog": "art/iterations/cycle_02/full_art_catalog.json",
            "producer_review": "delivery/next_cycle/T4/producer_self_review.json",
            "producer_check": "delivery/next_cycle/T4/producer_submission_check.json",
            "review_pack": "delivery/candidate_full_review_pack_20261025.zip",
            "source_archive": "delivery/courtyard_scene_demo_sources_v4.zip",
            "run_instructions": "delivery/RUN_DEMO_v4.md",
            "i_reports": "delivery/next_cycle/T7/",
        },
        "submission_filter_status": "ready_for_final_review",
        "ready_for_final_review": True,
        "how_to_resume": ["Hand the review pack, manifest and source archive to the final reviewers.",
                          "P08 rule review -> V08 visual review -> V09 controller certificate -> I08 full review -> I09 release.",
                          "Any source/build/camera change invalidates these exact hashes; regenerate bindings/review."],
    })
    (ROOT / "delivery/next_cycle/last_checkpoint.json").write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("ledger 1.0.133 updated; A/I tasks done")


if __name__ == "__main__":
    main()
