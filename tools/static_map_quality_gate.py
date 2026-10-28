"""Mechanical P1 static-map completion gate used by the project-local Codex Stop hook.

This validates evidence, hashes, scoring arithmetic, thresholds, and hard-gate records.
It does not independently perceive image quality; visual ratings must come from review passes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = "reference/_raw_screenshots/P1/t084s.jpg"
REFERENCE_SHA256 = "13706e7eab96726565156a9e6440727de5d5bac82ee9c09c293a5745dd7446de"
SCHEMA = "p1-static-map-quality-gate/v1"
WEIGHTS = {
    "composition_and_space": 20,
    "object_structure": 20,
    "surface_materials": 20,
    "vegetation": 15,
    "lighting_depth": 15,
    "style_cohesion": 10,
}
COMBO_CHECKS = ("floor", "tree", "grass", "lighting")
HARD_GATES = (
    "foreground_steps_railings",
    "right_grass_cylinder",
    "cohesive_non_checkerboard_ground",
    "tree_branching_negative_space",
    "dense_wavy_grass_canopy",
    "functional_midground_structure",
    "cool_soft_background",
    "materials_resolve",
)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _relative(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def _score_review(review: Any, label: str, failures: list[str], enforce_threshold: bool = True) -> tuple[float | None, dict[str, float]]:
    if not isinstance(review, dict):
        failures.append(f"{label}: review object missing")
        return None, {}
    if not str(review.get("reviewer_id", "")).strip():
        failures.append(f"{label}: reviewer_id missing")
    dimensions = review.get("dimensions")
    if not isinstance(dimensions, dict):
        failures.append(f"{label}: dimensions missing")
        return None, {}
    values: dict[str, float] = {}
    for name in WEIGHTS:
        item = dimensions.get(name)
        if not isinstance(item, dict):
            failures.append(f"{label}: dimension {name} missing")
            continue
        score = item.get("score")
        evidence = item.get("evidence")
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 4:
            failures.append(f"{label}: {name} score must be numeric from 0 to 4")
            continue
        values[name] = float(score)
        if len(str(evidence or "").strip()) < 20:
            failures.append(f"{label}: {name} needs at least 20 characters of visible evidence")
        if enforce_threshold and score < 3:
            failures.append(f"{label}: {name}={score:g}, below the per-dimension minimum 3")
    if len(values) != len(WEIGHTS):
        return None, values
    calculated = sum(WEIGHTS[key] * values[key] / 4 for key in WEIGHTS)
    declared = review.get("total_score")
    if isinstance(declared, bool) or not isinstance(declared, (int, float)):
        failures.append(f"{label}: total_score missing or not numeric")
    elif abs(float(declared) - calculated) > 0.01:
        failures.append(f"{label}: declared total {declared} differs from computed {calculated:.2f}")
    if enforce_threshold and calculated < 85:
        failures.append(f"{label}: computed total {calculated:.2f}, below 85")
    return calculated, values



def _check_checklist(collection: Any, required: tuple[str, ...], label: str, failures: list[str]) -> None:
    if not isinstance(collection, dict):
        failures.append(f"{label} must be an object")
        return
    for item_id in required:
        item = collection.get(item_id)
        if not isinstance(item, dict):
            failures.append(f"{label}.{item_id} missing")
            continue
        if item.get("status") != "pass":
            failures.append(f"{label}.{item_id} is not pass")
        if len(str(item.get("evidence", "")).strip()) < 20:
            failures.append(f"{label}.{item_id} needs visible evidence (20+ characters)")


def _checklist_passes(collection: Any, required: tuple[str, ...]) -> bool:
    if not isinstance(collection, dict):
        return False
    for item_id in required:
        item = collection.get(item_id)
        if not isinstance(item, dict):
            return False
        if item.get("status") != "pass" or len(str(item.get("evidence", "")).strip()) < 20:
            return False
    return True


def evaluate(candidate: str | Path) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    repairs: list[dict[str, Any]] = []
    candidate_path = Path(candidate)
    if not candidate_path.is_absolute():
        candidate_path = ROOT / candidate_path
    try:
        candidate_path = candidate_path.resolve(strict=True)
        candidate_rel = candidate_path.relative_to(ROOT.resolve()).as_posix()
    except (OSError, ValueError):
        return {"state": "repair_required", "stop_allowed": False,
                "failures": ["Candidate directory is missing or outside the project root."], "repairs": []}
    if not re.fullmatch(r"art/static_map/p1_autumn_courtyard/v\d+", candidate_rel):
        failures.append("Candidate must be an isolated vNN folder under art/static_map/p1_autumn_courtyard/.")
    candidate_id = candidate_path.name
    report_path = candidate_path / "GATE_REPORT.json"
    if not report_path.is_file():
        return {"state": "repair_required", "stop_allowed": False,
                "candidate_id": candidate_id, "failures": [
                    f"Missing {candidate_rel}/GATE_REPORT.json; create it using {SCHEMA} in planning/art/CODEX_STATIC_MAP_QUALITY_HOOK_20261029.md, then continue until it passes."
                ], "repairs": []}
    try:
        report = _load_json(report_path)
    except Exception as exc:
        return {"state": "repair_required", "stop_allowed": False,
                "candidate_id": candidate_id, "failures": [f"GATE_REPORT.json is invalid JSON: {exc}"], "repairs": []}
    if not isinstance(report, dict):
        return {"state": "repair_required", "stop_allowed": False,
                "candidate_id": candidate_id, "failures": ["GATE_REPORT.json must contain a JSON object."], "repairs": []}
    if report.get("schema") != SCHEMA:
        failures.append(f"schema must equal {SCHEMA}")
    if report.get("candidate_id") != candidate_id:
        failures.append(f"candidate_id must equal {candidate_id}")
    status = report.get("status")
    bindings = report.get("bindings")
    if not isinstance(bindings, dict):
        bindings = {}
        failures.append("bindings object is missing")

    expected_paths = {
        "reference": REFERENCE,
        "scene": f"{candidate_rel}/scene.blend",
        "render": f"{candidate_rel}/renders/final.png",
        "review": f"{candidate_rel}/REVIEW.md",
        "delivery": f"{candidate_rel}/DELIVERY.json",
        "profile": f"{candidate_rel}/reference_analysis/P1_REFERENCE_PROFILE.json",
    }
    actual_hashes: dict[str, str] = {}
    for key, expected_path in expected_paths.items():
        if status == "blocked_external" and key != "reference":
            continue
        entry = bindings.get(key)
        if not isinstance(entry, dict):
            failures.append(f"binding {key} is missing")
            continue
        rel = _relative(str(entry.get("path", "")))
        if rel != expected_path:
            failures.append(f"binding {key} path must be {expected_path}")
            continue
        full = (ROOT / rel).resolve()
        try:
            full.relative_to(ROOT.resolve())
            if key != "reference":
                full.relative_to(candidate_path)
        except ValueError:
            failures.append(f"binding {key} resolves outside its allowed directory")
            continue
        if not full.is_file():
            failures.append(f"bound file is missing: {rel}")
            continue
        actual = _sha(full)
        declared = str(entry.get("sha256", "")).lower()
        if declared != actual:
            failures.append(f"stale or incorrect SHA256 for {rel}")
        actual_hashes[key] = actual
    if actual_hashes.get("reference") != REFERENCE_SHA256:
        failures.append("P1 reference SHA256 differs from the locked target")

    if status == "blocked_external":
        blocker = report.get("external_blocker")
        if not isinstance(blocker, dict):
            failures.append("blocked_external requires an external_blocker record")
        else:
            if len(str(blocker.get("summary", "")).strip()) < 30:
                failures.append("external blocker summary must explain the specific outside dependency")
            attempts = blocker.get("attempts")
            if not isinstance(attempts, list) or len(attempts) < 2:
                failures.append("external blocker needs at least two documented alternative attempts")
            elif any(not isinstance(x, dict) or len(str(x.get("action", "")).strip()) < 8 or
                     len(str(x.get("result", "")).strip()) < 8 for x in attempts):
                failures.append("each external alternative needs a concrete action and result")
            if len(str(blocker.get("recovery_condition", "")).strip()) < 12:
                failures.append("external blocker needs a concrete recovery condition")
            evidence = blocker.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                failures.append("external blocker needs local evidence paths and SHA256 values")
            else:
                for item in evidence:
                    if not isinstance(item, dict):
                        failures.append("external blocker evidence entries must be objects")
                        continue
                    rel = _relative(str(item.get("path", "")))
                    full = (ROOT / rel).resolve()
                    try:
                        full.relative_to(candidate_path)
                    except ValueError:
                        failures.append(f"external blocker evidence must stay inside candidate: {rel}")
                        continue
                    if not full.is_file() or _sha(full) != str(item.get("sha256", "")).lower():
                        failures.append(f"external blocker evidence missing or SHA mismatch: {rel}")
        if not failures:
            return {"state": "blocked_external", "stop_allowed": True, "target_met": False,
                    "candidate_id": candidate_id, "failures": [], "repairs": [],
                    "summary": "Validated exception record; this is incomplete, not a quality pass."}

    elif status in ("target_met", "rework_required"):
        # Cross-check the candidate manifest and reference profile against the same bound files.
        try:
            delivery = _load_json(candidate_path / "DELIVERY.json")
            d_bindings = delivery.get("bindings", {}) if isinstance(delivery, dict) else {}
            if not isinstance(delivery, dict) or delivery.get("candidate_id") != candidate_id:
                failures.append("DELIVERY.json candidate_id does not match")
            expected_delivery_hashes = {
                "reference_sha256": "reference",
                "scene_sha256": "scene",
                "final_render_sha256": "render",
                "reference_profile_sha256": "profile",
            }
            for field, key in expected_delivery_hashes.items():
                if str(d_bindings.get(field, "")).lower() != actual_hashes.get(key):
                    failures.append(f"DELIVERY.json bindings.{field} does not match the actual file")
            profile = _load_json(candidate_path / "reference_analysis" / "P1_REFERENCE_PROFILE.json")
            if not isinstance(profile, dict) or str(profile.get("reference_sha256", "")).lower() != REFERENCE_SHA256:
                failures.append("P1_REFERENCE_PROFILE.json must bind the fixed P1 reference SHA256")
        except Exception as exc:
            failures.append(f"Cannot validate DELIVERY.json or P1 reference profile: {exc}")

        producer = report.get("producer_review")
        producer_total, producer_values = _score_review(producer, "producer_review", failures, enforce_threshold=False)
        producer_id = producer.get("reviewer_id", "") if isinstance(producer, dict) else ""
        if isinstance(producer, dict):
            if str(producer.get("render_sha256", "")).lower() != actual_hashes.get("render"):
                failures.append("producer_review is not bound to the current final render SHA256")
            if str(producer.get("reference_sha256", "")).lower() != REFERENCE_SHA256:
                failures.append("producer_review is not bound to the locked P1 reference SHA256")
        producer_preflight_passed = (
            producer_total is not None
            and producer_total >= 85
            and len(producer_values) == len(WEIGHTS)
            and all(producer_values[name] >= 3 for name in WEIGHTS)
            and _checklist_passes(report.get("combo_checks"), COMBO_CHECKS)
            and _checklist_passes(report.get("hard_gates"), HARD_GATES)
        )
        _check_checklist(report.get("combo_checks"), COMBO_CHECKS, "combo_checks", failures)
        _check_checklist(report.get("hard_gates"), HARD_GATES, "hard_gates", failures)

        # Do not spend blind-review cycles on a visibly failing producer draft.
        # Once producer preflight is clear, the final gate still requires two
        # separated reviews bound to the exact final render hash.
        collect_blind_reviews = status != "rework_required" or producer_preflight_passed
        if collect_blind_reviews:
            reviews = report.get("blind_reviews")
            if not isinstance(reviews, list) or len(reviews) != 2:
                failures.append("exactly two blind_reviews are required after producer preflight passes")
                reviews = []
            reviewer_ids: set[str] = set()
            for index, review in enumerate(reviews, start=1):
                label = f"blind_reviews[{index}]"
                if not isinstance(review, dict):
                    failures.append(f"{label}: review object missing")
                    continue
                reviewer_id = str(review.get("reviewer_id", "")).strip()
                if not reviewer_id or reviewer_id in reviewer_ids or reviewer_id == str(producer_id):
                    failures.append(f"{label}: reviewer_id must be unique and differ from producer")
                reviewer_ids.add(reviewer_id)
                if review.get("blind") is not True:
                    failures.append(f"{label}: blind must be true (reviewer saw neither producer scores nor the other review)")
                if str(review.get("render_sha256", "")).lower() != actual_hashes.get("render"):
                    failures.append(f"{label}: review is not bound to the current final render SHA256")
                if str(review.get("reference_sha256", "")).lower() != REFERENCE_SHA256:
                    failures.append(f"{label}: review is not bound to the locked P1 reference SHA256")
                _score_review(review, label, failures)
                _check_checklist(review.get("combo_checks"), COMBO_CHECKS, f"{label}.combo_checks", failures)
                _check_checklist(review.get("hard_gates"), HARD_GATES, f"{label}.hard_gates", failures)
        elif status == "rework_required":
            failures.append(
                "producer preflight is below target or a top-level checklist is incomplete; "
                "repair the producer draft before requesting blind reviews"
            )

        repro = report.get("reproducibility")
        if not isinstance(repro, dict) or repro.get("scene_reopened") is not True or repro.get("exit_code") != 0:
            failures.append("reproducibility must show scene reopened and exit_code 0")
        elif str(repro.get("render_sha256", "")).lower() != actual_hashes.get("render"):
            failures.append("reproducibility render SHA256 differs from the bound final render")

        if status == "rework_required":
            failures.append("report status is rework_required; complete the listed repairs and reassess before ending")
        if status == "target_met" and not failures:
            return {"state": "target_met", "stop_allowed": True, "target_met": True,
                    "candidate_id": candidate_id, "failures": [], "repairs": [],
                    "score_threshold": 85, "summary": "All score, evidence, and binding checks passed."}
    else:
        failures.append("status must be target_met, rework_required, or a fully evidenced blocked_external exception")

    raw_repairs = report.get("repair_queue", [])
    if failures:
        if not isinstance(raw_repairs, list) or not raw_repairs:
            failures.append("repair_queue is required for a failed report; include defect, cause, action, expected_effect, and verification for each failed dimension or gate")
        else:
            for index, item in enumerate(raw_repairs, start=1):
                if not isinstance(item, dict):
                    failures.append(f"repair_queue[{index}] must be an object")
                    continue
                if not (item.get("dimension") or item.get("gate_id")):
                    failures.append(f"repair_queue[{index}] must identify dimension or gate_id")
                for field in ("defect", "cause", "action", "expected_effect", "verification"):
                    if len(str(item.get(field, "")).strip()) < 12:
                        failures.append(f"repair_queue[{index}].{field} needs a concrete explanation")
                repairs.append({key: item.get(key) for key in
                                ("dimension", "gate_id", "defect", "cause", "action", "expected_effect", "verification")
                                if item.get(key) is not None})
    if not repairs and failures:
        repairs.append({"action": "Read the failed checks above, inspect the fixed P1 target beside the candidate, repair Blender-native source, rerender at the same camera, and refresh all hashes and review evidence."})
    return {"state": "repair_required", "stop_allowed": False, "target_met": False,
            "candidate_id": candidate_id, "failures": failures[:30], "repairs": repairs,
            "score_threshold": 85}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate P1 static-map completion evidence and quality thresholds.")
    parser.add_argument("--candidate", required=True, help="Project-relative or absolute vNN candidate directory")
    args = parser.parse_args()
    result = evaluate(args.candidate)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result.get("state") == "repair_required" else 0


if __name__ == "__main__":
    raise SystemExit(main())
