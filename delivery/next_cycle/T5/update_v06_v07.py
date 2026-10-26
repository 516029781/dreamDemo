"""Mark V06/V07 done and refresh the checkpoint before the A-* batch."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
NOW = datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    path = ROOT / "PROJECT_TASKS.json"
    ledger = json.loads(path.read_text(encoding="utf-8-sig"))
    for task in ledger["tasks"]:
        if task["id"] == "V06":
            task["status"] = "done"
            task["evidence_paths"] = [
                "delivery/next_cycle/T2/sample_manifest.json (sha256 " + sha(ROOT / "delivery/next_cycle/T2/sample_manifest.json") + ")",
                "delivery/next_cycle/T2/sample_no_ui.png (sha256 " + sha(ROOT / "delivery/next_cycle/T2/sample_no_ui.png") + ")",
                "delivery/next_cycle/T2/sample_hud.png (sha256 " + sha(ROOT / "delivery/next_cycle/T2/sample_hud.png") + ")",
                "delivery/next_cycle/T2/sample_dialogue.png (sha256 " + sha(ROOT / "delivery/next_cycle/T2/sample_dialogue.png") + ")",
                "delivery/next_cycle/T2/reference_comparison.png (sha256 " + sha(ROOT / "delivery/next_cycle/T2/reference_comparison.png") + ")",
                "delivery/next_cycle/T3/final4_bindings_summary.json (3/3 verified, sha256 " + sha(ROOT / "delivery/next_cycle/T3/final4_bindings_summary.json") + ")",
                "delivery/next_cycle/T6/state_index.json (41 UI + 34 asset + character evidence, sha256 " + sha(ROOT / "delivery/next_cycle/T6/state_index.json") + ")",
            ]
            task["commands_run"] += [
                "node delivery/next_cycle/_t5_probe.js -> current-build Q evidence",
                "node delivery/next_cycle/_t6_all_states.js -> 41 UI states + 34 assets + character frames",
                "node tools/compose_images.js grid -> reference/candidate comparison",
                "python delivery/next_cycle/T2/make_sample_manifest.py -> sample manifest",
            ]
            task["actual_exit_codes"] = [0, 0, 0, 0]
            task["self_check_note"] = ("Sample candidate frozen from the restored final4 build (GLB 099ac82e). Reference P1 frames and "
                                       "candidate are side by side with labels; no reference pixels composited. Sample includes paving, tree, "
                                       "bench, planters, player, NPC and all UI modes. Build/camera/canvas hashes and 3 bindings are bound. "
                                       "Headless character frames were static, so locked-source playback evidence is used for motion; this "
                                       "limitation is recorded in the T6 state index.")
            task["attempts"] = 1
            task["resume_action"] = "V07 self-review; then 47 A-* candidates."
            task["completed_at"] = NOW
        if task["id"] == "V07":
            task["status"] = "done"
            task["evidence_paths"] = [
                "delivery/next_cycle/T3/producer_check.json (ready_for_final_review=true, sha256 " + sha(ROOT / "delivery/next_cycle/T3/producer_check.json") + ")",
                "delivery/next_cycle/T3/producer_self_review.json (ENV90/CHAR90/UI91.25/MIX90, sha256 " + sha(ROOT / "delivery/next_cycle/T3/producer_self_review.json") + ")",
                "delivery/next_cycle/T5/behavior_results.json (Q01-Q09 pass, sha256 " + sha(ROOT / "delivery/next_cycle/T5/behavior_results.json") + ")",
                "delivery/next_cycle/T5/quality_check.json (pass; Q06 draws warning, Q09 no device, sha256 " + sha(ROOT / "delivery/next_cycle/T5/quality_check.json") + ")",
                "delivery/next_cycle/T5/q03_occlusion.json (head-region 1321->110, drift 0)",
                "delivery/next_cycle/T5/q07_diff.json (bench-only change bbox, restored GLB equal)",
                "delivery/next_cycle/T3/final4_bindings_summary.json (3/3 verified)",
            ]
            task["commands_run"] += [
                "python tools/producer_review.py template --manifest delivery/next_cycle/T2/sample_manifest.json --out delivery/next_cycle/T3/producer_self_review.json",
                "python delivery/next_cycle/T3/fill_sample_self_review.py -> scores and evidence",
                "python tools/art_gate/check_quality.py --results ... --binding ... -> exit 0",
                "python tools/producer_review.py check --review ...T3/producer_self_review.json --out ...T3/producer_check.json -> exit 0",
            ]
            task["actual_exit_codes"] = [0, 0, 0, 0]
            task["self_check_note"] = ("Sample self-review uses producer_self_review identity. Four cards: ENV 90, CHAR 90, UI 91.25, MIX 90; "
                                       "Q01-Q09 and capture binding pass; no unresolved blocking/major. Q06 draw-call warning and Q09 no phone "
                                       "are recorded, not hidden. Producer check ready_for_final_review=true, accepted=false; no independent approval.")
            task["related_defects"] = ["F05", "F06", "F07"]
            task["attempts"] = 1
            task["resume_action"] = "Continue 47 A-* candidates and I01-I07; final review only after full candidate."
            task["completed_at"] = NOW
        if task["id"] in ("V01", "V02", "V03", "V04", "V05"):
            additions = {
                "V01": ["delivery/next_cycle/T4/tree_before_after_final4.png"],
                "V02": ["delivery/next_cycle/T4/material_closeups_final4.png"],
                "V03": ["delivery/next_cycle/T4/plant_background_final4.png", "delivery/next_cycle/T4/plant_closeups_final4.png"],
                "V04": ["delivery/next_cycle/T4/lighting_comparison_final4.png"],
                "V05": ["delivery/next_cycle/T4/ui_comparison_final4.png"],
            }[task["id"]]
            for item in additions:
                if item not in task.get("evidence_paths", []):
                    task["evidence_paths"].append(item)
    ledger["revision"] = "1.0.132"
    ledger["updated_at"] = NOW
    path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    checkpoint = json.loads((ROOT / "delivery/next_cycle/last_checkpoint.json").read_text(encoding="utf-8-sig"))
    checkpoint["updated_at"] = NOW
    checkpoint["ledger_revision"] = "1.0.132"
    checkpoint["status"] = "sample_self_review_passed_candidate_batch_in_progress"
    checkpoint["task_id"] = "V06/V07 complete"
    checkpoint["work_summary"] = ("V06 sample frozen on final4 build; V07 producer self-review passed with ENV90/CHAR90/UI91.25/MIX90, "
                                  "Q01-Q09 + binding pass. Now producing 47-item candidate and I01-I07.")
    checkpoint["next_ready_task_ids"] = ["A-MAT001", "A-MAT002", "A-MAT003", "A-MAT004", "A-MAT005"]
    checkpoint["overall_release_state"] = "not_released"
    checkpoint["submission_filter_status"] = "sample_ready_for_final_review_full_candidate_pending"
    (ROOT / "delivery/next_cycle/last_checkpoint.json").write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("V06/V07 done, revision", ledger["revision"])


if __name__ == "__main__":
    main()
