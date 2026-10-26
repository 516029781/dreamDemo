"""Mark V06 done with sample manifest evidence."""
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
                "delivery/next_cycle/T3/final3_bindings_summary.json (3/3 verified)",
                "delivery/next_cycle/T5/q01_camera.json",
            ]
            task["commands_run"] += [
                "node delivery/next_cycle/_t5_probe.js -> real-canvas Q evidence",
                "node tools/compose_images.js grid -> reference/candidate comparison",
                "python delivery/next_cycle/T2/make_sample_manifest.py -> sample manifest",
            ]
            task["actual_exit_codes"] = [0, 0, 0]
            task["self_check_note"] = ("Sample candidate frozen from the final3 build; reference P1 frames and candidate are "
                                       "side-by-side with labels, no reference pixels composited. Sample includes stone paving, tree, "
                                       "bench, planters, player, NPC and UI. Build ID/camera/canvas hashes are bound. "
                                       "Status remains candidate_not_independently_approved.")
            task["related_defects"] = []
            task["attempts"] = 1
            task["resume_action"] = "V07 producer preflight/self-review; then 47 A-* candidates."
            task["completed_at"] = NOW
    ledger["revision"] = "1.0.131"
    ledger["updated_at"] = NOW
    path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("V06 done; revision", ledger["revision"])


if __name__ == "__main__":
    main()
