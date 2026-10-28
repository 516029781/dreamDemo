import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
NOW = datetime.now(timezone.utc).isoformat()


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8-sig"))


def write(rel, value):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def main():
    check = load("delivery/next_cycle/n5/T4/producer_submission_check_n5.json")
    scores = check["computed_scores"]
    ready = bool(check.get("ready_for_final_review"))
    stats = load("delivery/next_cycle/n5/T5/q06_stats.json")
    map_stats = stats["scopes"]["MAP001"]
    led = load("PROJECT_TASKS.json")
    for t in led["tasks"]:
        if t["id"] == "I07":
            t["status"] = "rework"
            t["outputs"] = [
                "art_review/submissions/candidate_n5/manifest.json",
                "delivery/next_cycle/n5/T4/producer_self_review_n5.json",
                "delivery/next_cycle/n5/T4/producer_submission_check_n5.json",
                "delivery/next_cycle/n5/T5/quality_check_n5.json",
            ]
            t["evidence_paths"] = [
                "art_review/submissions/candidate_n5/manifest.json",
                "delivery/next_cycle/n5/T4/producer_self_review_n5.json",
                "delivery/next_cycle/n5/T4/producer_submission_check_n5.json",
                "delivery/next_cycle/n5/T5/quality_check_n5.json",
                "delivery/next_cycle/n5/T5/behavior_results_n5.json",
                "delivery/next_cycle/n5/T4/N01_geometry_before_after.png",
                "delivery/next_cycle/n5/T4/N02_material_closeups.png",
                "delivery/next_cycle/n5/T4/N03_ui_before_after.png",
                "delivery/next_cycle/n5/T5/q04_behavior_moved.json",
                "delivery/next_cycle/n5/T3/game_finalN5h_formal_no_ui.png",
                "delivery/next_cycle/n5/T3/game_finalN5h_formal_ui.png",
                "delivery/next_cycle/n5/T3/game_finalN5h_dialogue.png",
            ]
            t["commands_run"] = [
                "candidate_n5 directed Blender build (tree/planter/bench/map)",
                "Cocos web-desktop n4 build -> pass",
                "Q01-Q09 -> pass; Q06 MAP001 draws %s / tris %s; Q09 no device" % (
                    map_stats["draws"], map_stats["tris"]),
                "N09 moved-position Q04 -> keyboard 1.05m / touch 1.80m; resume 0; portrait return 0",
                "producer_review check -> %s; ENV %s / CHAR %s / UI %s / MIX %s" % (
                    check["status"], scores["ENV"], scores["CHAR"], scores["UI"], scores["MIX"]),
            ]
            t["actual_exit_codes"] = [0, 0, 0, 0, 0 if ready else 3]
            t["blocker"] = ("candidate_n5 self-review is %s/%s/%s/%s (gate 90); N09 fixed, ENV/UI/MIX visual gap to P1 remains."
                            % (scores["ENV"], scores["CHAR"], scores["UI"], scores["MIX"])) if not ready else None
            t["resume_action"] = ("Continue producer repair on ENV geometry/crown, lighting depth and MIX; do not submit candidate_n5 as a final candidate until self-review reaches 90."
                                  if not ready else "Self-review passes the 90 gate; request independent review.")
        if t["id"] == "I08":
            t["status"] = "waiting_review"
            t["blocker"] = ("candidate_n5 is not submitted for independent review because producer self-review is below the 90 gate."
                            if not ready else "candidate_n5 self-review passed; independent review requested.")
            t["resume_action"] = "Do not start independent review yet; continue producer rework. I08 remains independent after a passing self-review."
    led["revision"] = "1.0.138"
    led["updated_at"] = NOW
    led["workflow_review_note"] = ("candidate_n5 (n4b repair pass) produced and Q-validated; N09 fixed; producer self-review %s/%s/%s/%s %s the 90 gate. %s"
                                   % (scores["ENV"], scores["CHAR"], scores["UI"], scores["MIX"],
                                      "meets" if ready else "does not meet",
                                      "Candidate submitted for final review." if ready
                                      else "Candidate not submitted for final review."))
    write("PROJECT_TASKS.json", led)

    counts = {}
    for t in led["tasks"]:
        counts[t["status"]] = counts.get(t["status"], 0) + 1

    cycle = {
        "status": "open",
        "source_candidate": "candidate_n2",
        "attempted_candidate": "candidate_n5",
        "next_candidate": "candidate_n5",
        "independent_report": "art_review/reports/independent_20261025_candidate_n2/REPORT.md",
        "execution_spec": "art_review/reports/independent_20261025_candidate_n2/REWORK_EXECUTION_SPEC.md",
        "open_findings": ["N01", "N02", "N03", "MIX"],
        "resolved_pending_independent": ["N09", "N04", "N05", "N07"],
        "last_attempt": {
            "candidate": "candidate_n5",
            "manifest": "art_review/submissions/candidate_n5/manifest.json",
            "manifest_sha256": sha("art_review/submissions/candidate_n5/manifest.json"),
            "self_review": "delivery/next_cycle/n5/T4/producer_self_review_n5.json",
            "self_review_sha256": sha("delivery/next_cycle/n5/T4/producer_self_review_n5.json"),
            "scores": scores,
            "quality": "pass (Q06/Q09 warnings)",
            "producer_filter": check["status"],
            "not_submitted_reason": ("Producer self-review below 90; no final review request issued."
                                      if not ready else "n/a; self-review passed."),
        },
        "resume_action": "Keep candidate_n5 evidence; continue visual repair in candidate_n5. N09 and behavior are closed pending independent confirmation. Next focus: ENV tree-crown topology, foliage-shaped shade, east bed planting, MIX world/character surface detail.",
    }
    write("planning/execution/ACTIVE_REWORK_CYCLE.json", cycle)

    cp = {
        "updated_at": NOW,
        "ledger_revision": "1.0.138",
        "status": "producer_self_rework_required" if not ready else "ready_for_final_review",
        "task_id": "candidate_n5 rework cycle",
        "work_summary": "candidate_n5 n4b same-round repair pass on native sources: turf rebuilt as paving-gated dense patches with the ring planter fully swarded, stone and soil palettes stepped down for real value separation, hedge mass and leaf skin share one notched silhouette with a desaturated leaf_far grade, key light re-raked with lower ambient, NPC contact blob softened, and the nine-slice deckle edge regenerated from smooth cubics to 199 jittered fibrous vertices. Q01-Q09 pass; N09 moved tests pass. Self-review %s/%s/%s/%s -> %s." % (
            scores["ENV"], scores["CHAR"], scores["UI"], scores["MIX"], check["status"]),
        "ledger_done": counts.get("done", 0),
        "ledger_todo": counts.get("todo", 0),
        "status_counts": counts,
        "candidate": "candidate_n5",
        "manifest": "art_review/submissions/candidate_n5/manifest.json",
        "manifest_sha256": sha("art_review/submissions/candidate_n5/manifest.json"),
        "self_review": "delivery/next_cycle/n5/T4/producer_self_review_n5.json",
        "producer_check": "delivery/next_cycle/n5/T4/producer_submission_check_n5.json",
        "quality_results": "delivery/next_cycle/n5/T5/behavior_results_n5.json",
        "quality_check": "delivery/next_cycle/n5/T5/quality_check_n5.json",
        "scores": scores,
        "quality_status": "pass",
        "quality_warnings": ["Q06 MAP001/LOOK001 draws %s, tris %s" % (
            map_stats["draws"], map_stats["tris"]), "Q09 no device test"],
        "behavior": {
            "Q04_keyboard_move_before_pause_m": 1.05,
            "Q04_touch_move_before_pause_m": 1.7998,
            "Q04_resume_displacement_m": 0,
            "Q04_portrait_return_displacement_m": 0,
            "Q03_occluded": True,
            "Q01_bbox_px": 130,
        },
        "next_ready_task_ids": ["I07"],
        "overall_release_state": "not_released",
        "next_actions": ([
            "Do not submit candidate_n5 for independent review; self-review is below 90.",
            "Next visual cycle: ENV tree-crown topology and foliage-shaped shade, east bed planting, UI pause-card family, MIX world surface detail.",
            "Recapture affected Q01-Q09 only after visual changes; rebuild candidate_n5 manifest/pack.",
        ] if not ready else [
            "Request independent review of candidate_n5.",
        ]),
        "artifacts": {
            "reference_comparison": "delivery/next_cycle/n5/T2/reference_comparison.png",
            "formal_no_ui": "delivery/next_cycle/n5/T3/game_finalN5h_formal_no_ui.png",
            "formal_ui": "delivery/next_cycle/n5/T3/game_finalN5h_formal_ui.png",
            "dialogue": "delivery/next_cycle/n5/T3/game_finalN5h_dialogue.png",
            "n01": "delivery/next_cycle/n5/T4/N01_geometry_before_after.png",
            "n02": "delivery/next_cycle/n5/T4/N02_material_closeups.png",
            "n03": "delivery/next_cycle/n5/T4/N03_ui_before_after.png",
            "n04": "delivery/next_cycle/n5/T4/N04_actor_bbox.png",
            "n05": "delivery/next_cycle/n5/T4/N05_orientation.png",
            "n07": "delivery/next_cycle/n5/T6/character_n/N07_animation_sheet.png",
            "n09": "delivery/next_cycle/n5/T5/q04_behavior_moved.json",
        },
        "commands_and_results": [
            {"command": "directed Blender n4 build", "exit_code": 0, "observed": "tree/planter/bench/map written"},
            {"command": "Cocos web-desktop n4", "exit_code": 0, "observed": "gate pass, output present"},
            {"command": "Q01-Q09 n4", "exit_code": 0, "observed": "pass; Q06/Q09 warnings"},
            {"command": "N09 moved Q04", "exit_code": 0, "observed": "resume 0m; portrait return 0m; player preserved"},
            {"command": "producer_review check", "exit_code": 3, "observed": "producer_rework_required; 75/93.75/75/75"},
        ],
        "limitations": [
            "No phone/WeChat device test.",
            "No full gameplay loop/performance acceptance.",
            "Visual style gap to P1 remains; self-review below 90.",
            "Independent review/controller release not signed.",
        ],
    }
    write("delivery/next_cycle/last_checkpoint.json", cp)
    print(json.dumps({"counts": counts, "scores": cp["scores"], "status": cp["status"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
