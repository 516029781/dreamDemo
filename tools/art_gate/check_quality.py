#!/usr/bin/env python3
"""P05: evaluate Q01-Q09 results against the vNext quality checks.

Missing evidence or untested items stay pending/failed; they never become pass.
Statistical thresholds produce warnings only where quality_checks.json says so.
Exit 0 = all applicable checks pass; 2 = pending/fail/invalid (cannot release).
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

RESULTS_VERSION = "vnext.behavior_results/1.0.0"


class QualityError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise QualityError(message)


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def schema_validate(document, schema_path):
    try:
        import jsonschema
    except ImportError:
        raise QualityError("a real Draft-07 validator is required (pip install jsonschema)")
    schema = load_json(schema_path)
    validator = jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda e: list(e.path))
    require(not errors, "Schema violations: " + "; ".join(
        "/".join(map(str, e.path)) + ": " + e.message for e in errors))


def evidence_gaps(root, record):
    gaps = []
    for entry in record["evidence"]:
        path = root / entry["path"]
        if not path.is_file():
            gaps.append(entry["role"] + " (missing file)")
        elif entry.get("sha256") and sha256_file(path) != entry["sha256"]:
            gaps.append(entry["role"] + " (hash mismatch)")
    return gaps


def need(mapping, key, label):
    value = mapping.get(key)
    require(value is not None and value != "", "missing measurement: " + label)
    return value


def q01(m, t):
    height = need(m, "character_height_px", "Q01 character_height_px")
    require(isinstance(height, (int, float)), "Q01 character_height_px must be numeric")
    lo, hi = t["q01_character_height_px"]["min"], t["q01_character_height_px"]["max"]
    require(lo <= height <= hi, "Q01 character height " + str(height) + "px outside " + str(lo) + "-" + str(hi))
    require(m.get("same_camera") is True, "Q01 the three formal shots must share one camera")
    return [], []


def q02(m, t):
    regions = need(m, "regions_compared", "Q02 regions_compared")
    differences = need(m, "differences", "Q02 differences")
    require(isinstance(regions, int) and regions >= 3, "Q02 needs at least 3 compared regions")
    require(isinstance(differences, list) and differences, "Q02 difference list is empty")
    for diff in differences:
        require(isinstance(diff, dict) and diff.get("region") and diff.get("difference"),
                "Q02 each difference needs region + concrete difference")
        require(len(str(diff["difference"]).strip()) >= 8, "Q02 difference is too generic")
    return [], []


def q03(m, t):
    cases = need(m, "cases", "Q03 cases")
    require(isinstance(cases, dict), "Q03 cases must be an object")
    for required_case in ("front", "behind"):
        require(required_case in cases, "Q03 missing " + required_case + " case")
    require(cases["behind"].get("occluded") is True, "Q03 behind case does not prove foreground occlusion")
    drift = need(m, "foot_shadow_drift_m", "Q03 foot_shadow_drift_m")
    limit = t["q03_foot_shadow_drift_m"]
    require(abs(float(drift)) <= limit, "Q03 foot/shadow drift " + str(drift) + "m exceeds " + str(limit))
    return [], []


def q04(m, t):
    runs = need(m, "runs", "Q04 runs")
    require(isinstance(runs, list) and runs, "Q04 needs input runs")
    modes = {run.get("input_mode") for run in runs if isinstance(run, dict)}
    require("keyboard" in modes, "Q04 missing keyboard run")
    require("touch" in modes, "Q04 missing touch run; keyboard alone cannot substitute")
    limit = t["q04_locked_displacement_m"]
    for run in runs:
        label = "Q04[" + str(run.get("input_mode")) + "]"
        require(float(need(run, "normal_move_m", label + " normal_move_m")) > 0, label + " normal move has no displacement")
        require(float(need(run, "pause_displacement_m", label + " pause_displacement_m")) <= limit,
                label + " pause displacement exceeds " + str(limit) + "m")
        require(float(need(run, "dialogue_displacement_m", label + " dialogue_displacement_m")) <= limit,
                label + " dialogue displacement exceeds " + str(limit) + "m")
        require(float(run.get("resumed_without_input_m", 0)) <= limit, label + " moved without new input after resume")
        require(float(need(run, "resumed_after_new_input_m", label + " resumed_after_new_input_m")) > 0,
                label + " did not respond to new input after resume")
        require(run.get("clip_after_pause") is False, label + " continues Move while paused/dialogue")
    return [], []


def q05(m, t):
    states = need(m, "states", "Q05 states")
    require(isinstance(states, dict), "Q05 states must be an object")
    for name in ("empty", "full", "reset"):
        require(name in states, "Q05 missing " + name + " state")
    require(states["empty"].get("count") == 0, "Q05 empty state has cards")
    require(states["full"].get("count") == 3, "Q05 full state does not show three cards")
    require(states["reset"].get("count") == 0, "Q05 reset does not clear cards")
    require(m.get("reset_residue") is False, "Q05 reset leaves residue")
    return [], []


def q06(m, t):
    glb = str(need(m, "final_glb_sha256", "Q06 final_glb_sha256"))
    require(len(glb) == 64 and all(c in "0123456789abcdef" for c in glb), "Q06 final GLB hash is not sha256")
    require(m.get("stats_source") == "runtime_measured_from_final_build",
            "Q06 stats must come from the final build's real runtime, not copied/old values")
    scopes = need(m, "scopes", "Q06 scopes")
    require(isinstance(scopes, dict) and scopes, "Q06 scope stats are empty")
    warnings = []
    for name, stats in scopes.items():
        require(isinstance(stats, dict) and isinstance(stats.get("draws"), int) and isinstance(stats.get("tris"), int),
                "Q06 scope " + name + " needs numeric draws/tris")
        if stats["draws"] > t["q06_warning"]["draw_calls"]:
            warnings.append("Q06 " + name + " draws " + str(stats["draws"]) + " above warning line")
        if stats["tris"] > t["q06_warning"]["triangles"]:
            warnings.append("Q06 " + name + " triangles " + str(stats["tris"]) + " above warning line")
    return [], warnings


def q07(m, t):
    edit = need(m, "edit", "Q07 edit")
    require(isinstance(edit, dict), "Q07 edit record must be an object")
    require(bool(edit.get("parameter_or_component")), "Q07 edit must name the changed parameter/component")
    for flag in ("reopened", "reexported", "same_camera_result", "unrelated_objects_unchanged"):
        require(edit.get(flag) is True, "Q07 edit record requires " + flag + "=true")
    return [], []


def q08(m, t):
    binding = need(m, "evidence_binding", "Q08 evidence_binding")
    require(isinstance(binding, dict), "Q08 evidence_binding must be an object")
    for key in ("source_sha256", "export_sha256", "contract_sha256", "rubric_version", "review_sha256"):
        require(binding.get(key), "Q08 evidence binding misses " + key)
    for key in ("source_sha256", "export_sha256", "contract_sha256", "review_sha256"):
        value = str(binding[key])
        require(len(value) == 64 and all(c in "0123456789abcdef" for c in value),
                "Q08 " + key + " is not sha256")
    require(binding.get("capture_id"), "Q08 evidence binding misses capture_id")
    require(binding.get("build_id"), "Q08 evidence binding misses build_id")
    return [], []


def q09(m, t):
    viewports = need(m, "viewports", "Q09 viewports")
    require(isinstance(viewports, list) and viewports, "Q09 needs real viewport records")
    landscape = [v for v in viewports if v.get("width", 0) > v.get("height", 0)]
    portrait = [v for v in viewports if v.get("height", 0) > v.get("width", 0)]
    require(landscape, "Q09 missing landscape viewport")
    require(portrait, "Q09 missing portrait viewport; a 1280x720 mock cannot substitute for 720x1280")
    for view in viewports:
        name = view.get("name", "?")
        expected = [view.get("width"), view.get("height")]
        require(view.get("canvas_backing") == expected, "Q09 " + str(name) + " canvas backing differs from viewport")
        require(view.get("screenshot_dimensions") == expected, "Q09 " + str(name) + " screenshot size differs from viewport")
        require(bool(view.get("safe_area")), "Q09 " + str(name) + " missing safe area")
        require(view.get("text_native_size") is True, "Q09 " + str(name) + " missing native-size text evidence")
    warnings = []
    if m.get("device_tested") is not True:
        warnings.append("Q09 device_tested=false: browser adaptation only; no real-device claim")
    return [], warnings


RULES = {"Q01": q01, "Q02": q02, "Q03": q03, "Q04": q04, "Q05": q05,
         "Q06": q06, "Q07": q07, "Q08": q08, "Q09": q09}


def evaluate(root, results_doc, checks_doc, binding_doc=None):
    thresholds = checks_doc["thresholds"]
    applicable = [c for c in checks_doc["checks"] if results_doc["stage"] in c["applies_to"]]
    by_id = {}
    for record in results_doc["results"]:
        require(record["check_id"] not in by_id, "duplicate check_id: " + record["check_id"])
        by_id[record["check_id"]] = record

    rows = {}
    warnings = []
    for check in applicable:
        qid = check["id"]
        record = by_id.get(qid)
        if record is None:
            rows[qid] = {"status": "pending", "reason": "缺少 " + qid + " 结果记录"}
            continue
        if record["status"] != "pass":
            rows[qid] = {"status": "fail" if record["status"] == "fail" else "pending",
                         "reason": record.get("reason") or record["status"]}
            continue
        gaps = evidence_gaps(root, record)
        missing_roles = [role for role in check["required_evidence"]
                         if role not in {e["role"] for e in record["evidence"]}]
        if gaps or missing_roles:
            rows[qid] = {"status": "pending",
                         "reason": "证据不完整: " + ", ".join(gaps + ["role:" + r for r in missing_roles])}
            continue
        try:
            fails, warns = RULES[qid](record["measurements"], thresholds)
        except (QualityError, KeyError, TypeError, ValueError) as exc:
            rows[qid] = {"status": "fail", "reason": str(exc)}
            continue
        if fails:
            rows[qid] = {"status": "fail", "reason": "; ".join(fails)}
        else:
            rows[qid] = {"status": "pass", "reason": None}
            warnings.extend(warns)

    if binding_doc is not None:
        binding = binding_doc
        require(binding.get("binding_id"), "capture binding lacks binding_id")
        rows["capture_binding"] = {"status": "pass", "reason": None,
                                   "binding_id": binding["binding_id"]}
        if binding.get("build_id") and binding["build_id"] != results_doc["build_id"]:
            rows["capture_binding"] = {"status": "fail",
                                       "reason": "capture binding build_id differs from results build_id"}
    else:
        rows["capture_binding"] = {"status": "pending",
                                   "reason": "未绑定真实 canvas 采集记录（F05）"}

    failed = [qid for qid, row in rows.items() if row["status"] == "fail"]
    pending = [qid for qid, row in rows.items() if row["status"] == "pending"]
    status = "fail" if failed else ("pending" if pending else "pass")
    return {"status": status, "checks": rows, "warnings": warnings,
            "failed": failed, "pending": pending}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--results", required=True)
    ap.add_argument("--checks", default="art_review/vnext/quality_checks.json")
    ap.add_argument("--schema", default="art_review/vnext/behavior_results.schema.json")
    ap.add_argument("--binding")
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args(argv)
    root = args.root.resolve()
    try:
        results_doc = load_json(root / args.results)
        schema_validate(results_doc, root / args.schema)
        require(results_doc.get("results_version") == RESULTS_VERSION, "Unknown results version")
        checks_doc = load_json(root / args.checks)
        binding = load_json(root / args.binding) if args.binding else None
        result = evaluate(root, results_doc, checks_doc, binding)
        if args.json_out:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "pass" else 2
    except (QualityError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "invalid", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
