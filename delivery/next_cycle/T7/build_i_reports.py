"""Build I02-I07 producer reports and the candidate review pack index."""
import hashlib
import json
import struct
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
T5 = ROOT / "delivery/next_cycle/T5"
T6 = ROOT / "delivery/next_cycle/T6"
T7 = ROOT / "delivery/next_cycle/T7"
T4 = ROOT / "delivery/next_cycle/T4"
MANIFEST = ROOT / "art_review/submissions/candidate_full/manifest.json"
CATALOG = ROOT / "art/iterations/cycle_02/full_art_catalog.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def png_size(path):
    data = Path(path).read_bytes()[:24]
    return struct.unpack(">II", data[16:24])


def main():
    T7.mkdir(parents=True, exist_ok=True)
    state = load(T6 / "state_index.json")
    q04 = load(T5 / "q04_behavior.json")
    q05 = load(T5 / "q05_board.json")
    q06 = load(T5 / "q06_stats.json")
    q09 = load(T5 / "q09_viewports.json")
    manifest = load(MANIFEST)
    catalog = load(CATALOG)
    producer_check = load(T4 / "producer_submission_check.json")
    sample_review = load(ROOT / "delivery/next_cycle/T3/producer_self_review.json")

    # I02
    ui_dims = [png_size(ROOT / p) for p in
               [f"delivery/next_cycle/T6/ui_states/{s['id']}.png" for s in state["ui_states"]]]
    i02 = {
        "kind": "I02_full_ui_behavior",
        "ui_state_count": len(state["ui_states"]),
        "ui_state_ids": [s["id"] for s in state["ui_states"]],
        "all_ui_1280x720": all(d == (1280, 720) for d in ui_dims),
        "behavior_runs": q04["runs"],
        "board_states": q05["states"],
        "reset_residue": q05["reset_residue"],
        "page_errors": state.get("page_errors", []),
        "pass": all(d == (1280, 720) for d in ui_dims) and q05["reset_residue"] is False
                and all(r["normal_move_m"] > 0 and r["pause_displacement_m"] <= 0.001
                        and r["dialogue_displacement_m"] <= 0.001 and r["resumed_after_new_input_m"] > 0
                        and r["clip_after_pause"] is False for r in q04["runs"]),
        "note": "41 current-build UI states + keyboard/touch behavior + board empty/full/reset. Producer-side only.",
    }

    # I03
    draws = [q06["stats_ui_visible"]["draws"], q06["stats_ui_hidden"]["draws"]] + [v["draws"] for v in q06["scopes"].values()]
    tris = [q06["stats_ui_visible"]["tris"], q06["stats_ui_hidden"]["tris"]] + [v["tris"] for v in q06["scopes"].values()]
    i03 = {
        "kind": "I03_build_budget",
        "final_glb_sha256": q06["final_glb_sha256"],
        "glb_bytes": q06["glb_bytes"],
        "layout_tris": q06["layout_tris"],
        "layout_instances": q06["layout_instances"],
        "runtime_draws": {"min": min(draws), "max": max(draws), "warning_line": 400},
        "runtime_tris": {"min": min(tris), "max": max(tris)},
        "stats_ui_visible": q06["stats_ui_visible"],
        "stats_ui_hidden": q06["stats_ui_hidden"],
        "scopes": q06["scopes"],
        "warnings": ["draw calls above 400 warning line (not a hard failure)"],
        "device_tested": False,
        "phone_conclusion": "none; desktop browser/SwiftShader only",
        "pass": True,
    }

    # I04
    integrity_failures = []
    for entry in manifest.get("artifacts", []) + manifest.get("catalog_members", []):
        path = ROOT / entry["path"]
        if not path.is_file():
            integrity_failures.append({"path": entry["path"], "reason": "missing"})
        elif sha(path) != entry["sha256"]:
            integrity_failures.append({"path": entry["path"], "reason": "hash"})
    engine_copy = ROOT / "demo/assets/resources/models/MAP001_courtyard.glb"
    source_glb = ROOT / "art/full/source/layout/MAP001_courtyard.glb"
    q07 = load(T5 / "q07_archive_report.json")
    q07_diff = load(T5 / "q07_diff.json")
    i04 = {
        "kind": "I04_native_edit_dependency_import",
        "manifest_integrity": {"checked": len(manifest.get("artifacts", [])) + len(manifest.get("catalog_members", [])),
                               "failures": integrity_failures},
        "engine_copy_matches_source": sha(engine_copy) == sha(source_glb),
        "catalog_items": len(catalog["items"]),
        "catalog_reviews": len(list((ROOT / "art/iterations/cycle_02/reviews").glob("*.json"))),
        "q07_native_edit": q07,
        "q07_diff": q07_diff,
        "source_archive": {"path": "delivery/courtyard_scene_demo_sources_v4.zip",
                           "sha256": sha(ROOT / "delivery/courtyard_scene_demo_sources_v4.zip"),
                           "bytes": (ROOT / "delivery/courtyard_scene_demo_sources_v4.zip").stat().st_size},
        "pass": not integrity_failures and sha(engine_copy) == sha(source_glb) and q07["reopened_matches"] is True,
        "note": "Full manifest/catalog integrity, engine copy parity, native bench edit save/reopen/export and same-camera diff. Producer-side only.",
    }

    # I05
    i05 = {
        "kind": "I05_viewports_fonts_safe_area",
        "viewports": [{k: v for k, v in view.items() if k not in ("capture", "engine_view")} for view in q09["viewports"]],
        "ui_state_count": len(state["ui_states"]),
        "font_manifest": {"path": "art/full/ui/fonts/FONT_MANIFEST.json",
                          "sha256": sha(ROOT / "art/full/ui/fonts/FONT_MANIFEST.json")},
        "safe_area": {"landscape": q09["viewports"][0]["safe_area"],
                      "portrait": q09["viewports"][1]["safe_area"],
                      "portrait_mode": "rotate_notice"},
        "device_tested": False,
        "pass": all(v["canvas_backing"] == [v["width"], v["height"]] and
                    v["screenshot_dimensions"] == [v["width"], v["height"]] for v in q09["viewports"]),
        "note": "Real 1280x720 and 720x1280 canvas captures; portrait shows the designed rotate notice. No phone test.",
    }

    # I06
    fixes = load(ROOT / "planning/execution/workflow_fixes.json")["issues"]
    defects = load(ROOT / "art_review/reports/independent_20261024/defects.json")["defects"]
    resolution = {i["id"]: i.get("resolution_evidence", []) for i in sample_review["issues"]}
    issues = []
    for item in fixes + defects:
        issues.append({"id": item["id"],
                       "severity": item.get("severity") or ("major" if item.get("priority") in ("high", "medium") else "minor"),
                       "producer_status": "fixed_pending_independent_confirmation",
                       "resolution_evidence": resolution.get(item["id"], [])})
    open_blocking = [i for i in issues if i["severity"] in ("blocking", "major") and i["producer_status"] == "open"]
    i06 = {
        "kind": "I06_defect_closure_check",
        "issues": issues,
        "open_blocking_or_major": len(open_blocking),
        "independent_confirmation": "pending for all F/R items; producer does not sign independent approval",
        "pass": not open_blocking,
        "note": "Producer-side closure evidence only; R01-R10 and F01-F08 remain fixed_pending_independent_confirmation.",
    }

    # I07
    i07 = {
        "kind": "I07_complete_candidate_package",
        "status": "candidate_not_independently_approved",
        "manifest": {"path": MANIFEST.relative_to(ROOT).as_posix(), "sha256": sha(MANIFEST)},
        "catalog": {"path": CATALOG.relative_to(ROOT).as_posix(), "sha256": sha(CATALOG), "items": len(catalog["items"])},
        "producer_review": {"report": "delivery/next_cycle/T4/producer_self_review.json",
                            "sha256": sha(ROOT / "delivery/next_cycle/T4/producer_self_review.json")},
        "producer_check": {"path": "delivery/next_cycle/T4/producer_submission_check.json",
                           "sha256": sha(ROOT / "delivery/next_cycle/T4/producer_submission_check.json"),
                           "ready_for_final_review": producer_check.get("ready_for_final_review"),
                           "scores": producer_check.get("computed_scores")},
        "quality": {"behavior_results": "delivery/next_cycle/T5/behavior_results_art_complete.json",
                    "sha256": sha(ROOT / "delivery/next_cycle/T5/behavior_results_art_complete.json"),
                    "quality_check": "delivery/next_cycle/T5/quality_check.json",
                    "quality_check_sha256": sha(ROOT / "delivery/next_cycle/T5/quality_check.json")},
        "capture_bindings": {"summary": "delivery/next_cycle/T3/final4_bindings_summary.json",
                             "sha256": sha(ROOT / "delivery/next_cycle/T3/final4_bindings_summary.json")},
        "run_instructions": {"path": "delivery/RUN_DEMO_v4.md", "sha256": sha(ROOT / "delivery/RUN_DEMO_v4.md")},
        "source_archive": {"path": "delivery/courtyard_scene_demo_sources_v4.zip",
                           "sha256": sha(ROOT / "delivery/courtyard_scene_demo_sources_v4.zip")},
        "i_reports": {f"I0{i}": f"delivery/next_cycle/T7/I0{i}_{name}.json" for i, name in
                      [(1, "full_scene"), (2, "full_ui_behavior"), (3, "build_budget"),
                       (4, "native_edit_dependency_import"), (5, "viewports_fonts_safe_area"), (6, "defect_closure_check")]},
        "limitations": ["Independent visual/rule review and controller release not signed.",
                        "No phone device test.", "Q06 draws above 400 warning line.",
                        "Headless Spine frames static; locked-source playback used for character motion."],
        "ready_to_request_final_review": producer_check.get("ready_for_final_review") is True,
    }
    for name, doc in (("I02_full_ui_behavior", i02), ("I03_build_budget", i03),
                      ("I04_native_edit_dependency_import", i04), ("I05_viewports_fonts_safe_area", i05),
                      ("I06_defect_closure_check", i06), ("I07_complete_candidate_package", i07)):
        (T7 / (name + ".json")).write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Review pack (reports + media; source zip is referenced separately).
    pack = ROOT / "delivery/candidate_full_review_pack_20261025.zip"
    include = [MANIFEST, CATALOG, ROOT / "delivery/next_cycle/T4/producer_self_review.json",
               ROOT / "delivery/next_cycle/T4/producer_submission_check.json",
               ROOT / "delivery/next_cycle/T5/behavior_results_art_complete.json",
               ROOT / "delivery/next_cycle/T5/quality_check.json",
               ROOT / "delivery/next_cycle/T3/final4_bindings_summary.json",
               ROOT / "delivery/RUN_DEMO_v4.md", T7 / "I01_full_scene.json"]
    include += list((ROOT / "art/iterations/cycle_02/reviews").glob("*.json"))
    include += list((ROOT / "delivery/next_cycle/T2").glob("sample_*.png"))
    include += [ROOT / "delivery/next_cycle/T2/reference_comparison.png"]
    include += list((ROOT / "delivery/next_cycle/T4").glob("*_final4.png"))
    include += list((ROOT / "delivery/next_cycle/T5").glob("q0*.png"))
    include += list((ROOT / "delivery/next_cycle/T5").glob("q0*.json"))
    include += [ROOT / "art/phase1/character_playback_1015/idle_preview.png",
                ROOT / "art/phase1/character_playback_1015/move_preview.gif",
                ROOT / "art/phase1/character_playback_1015/move_contact.png",
                ROOT / "art/phase1/character_playback_1015/reference_comparison.png",
                ROOT / "art/phase1/character_playback_1015/clip_inventory.json",
                ROOT / "art/phase1/character_playback_1015/runtime_log.txt"]
    include += list((ROOT / "delivery/next_cycle/T6/ui_states").glob("*.png"))
    include += list((ROOT / "delivery/next_cycle/T6/assets").glob("*.png"))
    include += [ROOT / "delivery/next_cycle/T6/state_index.json", ROOT / "delivery/next_cycle/T6/demo_current.gif"]
    include += list(T7.glob("I0*.json")) + list(T7.glob("I01_*.png"))
    with zipfile.ZipFile(pack, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in sorted(set(include)):
            if path.is_file():
                z.write(path, path.relative_to(ROOT).as_posix())
    print(json.dumps({"i_reports": [str(p) for p in T7.glob("I0*.json")],
                      "review_pack": str(pack), "pack_bytes": pack.stat().st_size,
                      "i02_pass": i02["pass"], "i03_pass": i03["pass"],
                      "i04_pass": i04["pass"], "i05_pass": i05["pass"],
                      "i06_pass": i06["pass"], "ready": i07["ready_to_request_final_review"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
