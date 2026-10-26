__file__='C:\\软件\\鼠鼠\\delivery\\next_cycle\\T0\\p05_selfcheck.py'
__name__="__main__"
"""P05 self-check: Q01-Q09 evidence gating, pending/fail semantics, solution neutrality."""
import copy
import importlib.util
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CHECKER = ROOT / "tools/art_gate/check_quality.py"
CHECKS = ROOT / "art_review/vnext/quality_checks.json"
TEMPLATE = ROOT / "art_review/vnext/review_template.json"
TMP = ROOT / "art_review/reports/independent_20261025_candidate/fixtures_p05"

ROLES = {
    "Q01": ["no_ui_shot", "with_ui_shot", "dialogue_shot", "camera_json"],
    "Q02": ["reference_regions", "candidate_comparison"],
    "Q03": ["front_shot", "behind_shot", "world_position_log"],
    "Q04": ["normal_move_log", "pause_log", "dialogue_log", "resume_log"],
    "Q05": ["empty_shot", "full_shot", "reset_shot", "child_visibility_log"],
    "Q06": ["final_glb", "runtime_stats_log", "decode_stats"],
    "Q07": ["edited_source", "reexport", "same_camera_shot", "reopen_log"],
    "Q08": ["evidence_binding_manifest"],
    "Q09": ["state_index", "landscape_shot", "portrait_shot", "text_native_size_shot"],
}


def load_checker():
    spec = importlib.util.spec_from_file_location("check_quality", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def wj(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def build_evidence(base):
    evidence = {}
    for qid, roles in ROLES.items():
        evidence[qid] = []
        for role in roles:
            path = base / "evidence" / f"{qid}_{role}.txt"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"synthetic {qid} {role} evidence", encoding="utf-8")
            evidence[qid].append({"role": role, "path": path.relative_to(ROOT).as_posix()})
    return evidence


def measurements():
    return {
        "Q01": {"character_height_px": 97.8, "same_camera": True},
        "Q02": {"regions_compared": 4, "differences": [
            {"region": "tree canopy", "difference": "main lobes need larger continuous masses"},
            {"region": "planters", "difference": "ground cover is still only sparse seedlings"},
            {"region": "stone/wood/metal", "difference": "roughness separation is weak at formal camera"},
        ]},
        "Q03": {"cases": {"front": {"occluded": False}, "behind": {"occluded": True}},
                "foot_shadow_drift_m": 0.001},
        "Q04": {"runs": [
            {"input_mode": "keyboard", "normal_move_m": 0.9, "pause_displacement_m": 0.0,
             "dialogue_displacement_m": 0.0, "resumed_without_input_m": 0.0,
             "resumed_after_new_input_m": 0.45, "clip_after_pause": False},
            {"input_mode": "touch", "normal_move_m": 0.8, "pause_displacement_m": 0.0,
             "dialogue_displacement_m": 0.0, "resumed_without_input_m": 0.0,
             "resumed_after_new_input_m": 0.4, "clip_after_pause": False},
        ]},
        "Q05": {"states": {"empty": {"count": 0}, "full": {"count": 3}, "reset": {"count": 0}},
                "reset_residue": False},
        "Q06": {"final_glb_sha256": "a" * 64, "stats_source": "runtime_measured_from_final_build",
                "scopes": {"MAP001": {"draws": 337, "tris": 203566}}},
        "Q07": {"edit": {"parameter_or_component": "bench wood roughness (procedural material)",
                         "reopened": True, "reexported": True, "same_camera_result": True,
                         "unrelated_objects_unchanged": True}},
        "Q08": {"evidence_binding": {"source_sha256": "b" * 64, "export_sha256": "c" * 64,
                                     "contract_sha256": "d" * 64, "rubric_version": "1.2.0",
                                     "review_sha256": "e" * 64, "capture_id": "cap-1",
                                     "build_id": "build-1"}},
        "Q09": {"viewports": [
            {"name": "1280x720", "width": 1280, "height": 720, "canvas_backing": [1280, 720],
             "screenshot_dimensions": [1280, 720], "safe_area": {"top": 0, "bottom": 0},
             "text_native_size": True},
            {"name": "720x1280", "width": 720, "height": 1280, "canvas_backing": [720, 1280],
             "screenshot_dimensions": [720, 1280], "safe_area": {"top": 0, "bottom": 0},
             "text_native_size": True},
        ], "device_tested": False},
    }


def results_doc(evidence):
    return {
        "results_version": "vnext.behavior_results/1.0.0",
        "stage": "scene_demo",
        "build_id": "build-1",
        "generated_at": "2026-10-25T00:00:00Z",
        "results": [{"check_id": qid, "asset_id": "MAP001", "status": "pass",
                     "evidence": evidence[qid], "measurements": measurements()[qid],
                     "tested_by": "synthetic fixture", "tested_at": "2026-10-25T00:00:00Z"}
                    for qid in ROLES],
    }


def main():
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True)
    module = load_checker()
    checks = json.loads(CHECKS.read_text(encoding="utf-8"))
    binding = {"binding_id": "cap-1", "build_id": "build-1"}
    output = {"kind": "p05_selfcheck_quality_checks", "checker_sha256": module.sha256_file(CHECKER),
              "checks_sha256": module.sha256_file(CHECKS), "cases": []}
    ok = True

    def run_case(name, mutate=None, delete_role=None, use_binding=True, expect=None):
        nonlocal ok
        base = TMP / name
        evidence = build_evidence(base)
        doc = results_doc(evidence)
        if mutate:
            mutate(doc)
        if delete_role:
            qid, role = delete_role
            path = next(e["path"] for e in evidence[qid] if e["role"] == role)
            (ROOT / path).unlink()
        result = module.evaluate(ROOT, doc, checks, binding if use_binding else None)
        passed = result["status"] == expect[0]
        if len(expect) > 1:
            passed = passed and expect[1](result)
        output["cases"].append({"case": name, "expected": expect[0], "actual": result["status"],
                                "pass": passed, "failed": result["failed"], "pending": result["pending"],
                                "warnings": result["warnings"]})
        ok = ok and passed
        return result

    def set_measurement(qid, key, value):
        def mutate(doc):
            for record in doc["results"]:
                if record["check_id"] == qid:
                    record["measurements"][key] = value
        return mutate

    def drop_result(qid):
        def mutate(doc):
            doc["results"] = [r for r in doc["results"] if r["check_id"] != qid]
        return mutate

    run_case("all_pass", expect=("pass", lambda r: any("device_tested" in w for w in r["warnings"])))
    run_case("missing_q03", mutate=drop_result("Q03"), expect=("pending",))
    run_case("q04_no_touch", mutate=lambda d: d["results"][3]["measurements"]["runs"].pop(1),
             expect=("fail",))
    run_case("q04_pause_drift", mutate=set_measurement("Q04", "runs", [
        {"input_mode": "keyboard", "normal_move_m": 0.9, "pause_displacement_m": 0.01,
         "dialogue_displacement_m": 0.0, "resumed_without_input_m": 0.0,
         "resumed_after_new_input_m": 0.45, "clip_after_pause": False},
        {"input_mode": "touch", "normal_move_m": 0.8, "pause_displacement_m": 0.0,
         "dialogue_displacement_m": 0.0, "resumed_without_input_m": 0.0,
         "resumed_after_new_input_m": 0.4, "clip_after_pause": False},
    ]), expect=("fail",))
    run_case("q05_reset_residue", mutate=set_measurement("Q05", "reset_residue", True),
             expect=("fail",))
    run_case("q09_portrait_mock", mutate=set_measurement("Q09", "viewports", [
        {"name": "1280x720", "width": 1280, "height": 720, "canvas_backing": [1280, 720],
         "screenshot_dimensions": [1280, 720], "safe_area": {}, "text_native_size": True},
        {"name": "720x1280", "width": 720, "height": 1280, "canvas_backing": [720, 1280],
         "screenshot_dimensions": [1280, 720], "safe_area": {}, "text_native_size": True},
    ]), expect=("fail",))
    run_case("q06_copied_stats", mutate=set_measurement("Q06", "stats_source", "copied_old_values"),
             expect=("fail",))
    run_case("q06_high_draws_is_warning_only", mutate=set_measurement("Q06", "scopes", {
        "MAP001": {"draws": 450, "tris": 203566}}),
        expect=("pass", lambda r: any("draws" in w for w in r["warnings"])))
    run_case("q03_missing_behind", mutate=set_measurement("Q03", "cases", {
        "front": {"occluded": False}}), expect=("fail",))
    run_case("q05_missing_evidence_file", delete_role=("Q05", "empty_shot"), expect=("pending",))
    run_case("q01_too_small", mutate=set_measurement("Q01", "character_height_px", 60),
             expect=("fail",))
    run_case("no_capture_binding", use_binding=False, expect=("pending", lambda r: "capture_binding" in r["pending"]))

    template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    structure = {
        "template_only": template.get("report_kind") == "template_not_actual_review" and template.get("template_only") is True,
        "overall_pending": template.get("overall_decision") == "pending",
        "gates_unchecked": all(v["status"] == "not_checked" for v in template["gates"].values()),
        "quality_unchecked": all(v["status"] == "not_checked" for v in template["quality_checks"].values()),
        "behavior_unbound": template.get("behavior_results", {}).get("path") is None,
        "checks_count": len(checks["checks"]) == 9 and {c["id"] for c in checks["checks"]} == {f"Q0{i}" for i in range(1, 10)},
        "hard_fails_defined": all(c.get("hard_fails") for c in checks["checks"]),
        "solution_neutral": "not require" not in json.dumps(checks["solution_neutrality"]).lower()
                            and "不得要求" in checks["solution_neutrality"]["note"],
    }
    output["template_structure"] = structure
    ok = ok and all(structure.values())
    output["factual_note"] = ("All fixtures are synthetic. Passing Q06 with a procedural material (no texture atlas) "
                              "demonstrates solution neutrality, not production approval.")
    output["all_passed"] = bool(ok)
    if TMP.exists():
        shutil.rmtree(TMP)
    out_path = ROOT / "art_review/reports/independent_20261025_candidate/p05_replay.json"
    wj(out_path, output)
    print(json.dumps({"all_passed": output["all_passed"], "cases": len(output["cases"]),
                      "output": str(out_path), "sha256": module.sha256_file(out_path)}, ensure_ascii=False))
    return 0 if output["all_passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
