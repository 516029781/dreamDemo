#!/usr/bin/env python3
"""P02: migrate the old producer catalog into vNext three-axis asset status records.

Reads (never modifies):
  art/full/art_complete_catalog.json          old catalog (status=engine_verified, blockers notes)
  art/full/reviews/<ASSET_ID>.json            producer technical self-checks
  art_review/reports/independent_20261024/defects.json   independent open defects

Writes a single new file under art_review/vnext/ (enforced). Old frozen paths are
never written. Invariants enforced (exit 2 if violated):
  - migration never emits visual_state=pass or release_state=released
  - any record with an open blocking/major issue must be release_state=blocked
  - behavior_state=not_required requires a reason and is limited to
    no-interaction-surface kinds
  - a technical review promotes technical_state only when its decision is in
    SUCCESS_DECISIONS, it names the same asset, and its evidence resolves to
    real files; failed/empty reviews demote, never promote (F04)
  - the generated document must pass the real Draft-07 schema (F03)
Historical blocker notes are preserved verbatim as historical_notes and do not
affect release decisions (non-empty history is not an automatic failure).
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "vnext.asset_status/1.0.1"
OUT_PREFIX = "art_review/vnext/"
ASSET_ID_RE = re.compile(r"\b[A-Z]{3,4}\d{3}(?![a-z0-9])")
SUCCESS_DECISIONS = {"pass", "approved", "engine_verified"}

# Defect routing overrides. Regex hits are used when no override applies.
# Values: (asset_ids, affected_scope). Empty asset list routes to the CATALOG
# package record. R08's regex hit on ENV006 is dropped: it is a process defect.
DEFECT_ROUTES = {
    "R01": (["MAP001"], "scene_character_integration"),
    "R02": (["MAP001"], "scene_camera"),
    "R05": (["MAP001"], "input_lock_behavior"),
    "R07": (["FX003"], "board_transition"),
    "R08": ([], "catalog_process"),
    "R09": ([], "ui_family"),
    "R10": ([], "catalog_docs"),
}
SCOPE_OVERRIDES = {"R06": "tri_stats_reporting"}
# Defects that are visual findings: attached items get visual_state=rework.
VISUAL_DEFECT_IDS = {"R01", "R02", "R03", "R04"}
# Independently verified behavior/integration failures -> behavior_state=fail.
BEHAVIOR_FAIL_DEFECT_IDS = {"R01", "R05"}
# Kinds with no runtime interaction surface may carry behavior_state=not_required.
BEHAVIOR_NOT_REQUIRED_KINDS = {"material", "scene_profile", "delivery"}
BEHAVIOR_NOT_REQUIRED_REASON = (
    "无运行时交互面；行为检查(Q04/Q05)适用于场景/角色/UI条目，见NEXT_ITERATION_PLAN.md §4"
)

TECH_TO_STATE = {
    "missing": "missing",
    "candidate": "source_ready",
    "historical_candidate": "source_ready",
    "source_ready": "source_ready",
    "engine_verified": "import_verified",
    "approved": "import_verified",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def defect_asset_ids(defect: dict) -> list:
    if defect["id"] in DEFECT_ROUTES:
        return list(DEFECT_ROUTES[defect["id"]][0])
    blob = " ".join(
        defect.get("evidence", [])
        + [defect.get("observed", ""), defect.get("recheck", "")]
        + defect.get("supplemental_diagnostics", [])
    )
    return sorted(set(ASSET_ID_RE.findall(blob)))


def defect_scope(defect: dict) -> str:
    if defect["id"] in SCOPE_OVERRIDES:
        return SCOPE_OVERRIDES[defect["id"]]
    return DEFECT_ROUTES.get(defect["id"], ("", "asset_visual"))[1]


def make_issue(defect: dict, source_review: str) -> dict:
    return {
        "issue_id": defect["id"],
        "severity": defect["severity"],
        "status": "open" if defect.get("status", "open") == "open" else defect["status"],
        "title": defect["title"],
        "affected_scope": defect_scope(defect),
        "evidence": list(defect.get("evidence", [])),
        "source_review": source_review,
    }


def review_check(repo: Path, asset_id: str, rev: dict):
    """F04: only a successful, asset-bound review with real evidence may promote."""
    if not isinstance(rev, dict):
        return False, "review JSON is not an object"
    if rev.get("asset_id") not in (None, asset_id):
        return False, f"review asset_id {rev.get('asset_id')!r} does not match {asset_id}"
    decision = rev.get("decision")
    if decision not in SUCCESS_DECISIONS:
        return False, f"decision {decision!r} is not in success whitelist"
    if not isinstance(rev.get("reviewer"), str) or not rev["reviewer"].strip():
        return False, "missing reviewer"
    evidence = rev.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        return False, "empty evidence"
    resolved = [
        item for item in evidence
        if isinstance(item, str) and item.strip() and (repo / item).is_file()
    ]
    if not resolved:
        return False, "no evidence path resolves to a file"
    return True, None


def validate_schema(doc: dict, schema_path: Path) -> int:
    try:
        import jsonschema
    except ImportError:
        print("ERROR: a real Draft-07 validator is required (pip install jsonschema)", file=sys.stderr)
        return 3
    validator = jsonschema.Draft7Validator(load_json(schema_path))
    errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
    for err in errors:
        print("SCHEMA VIOLATION: " + "/".join(map(str, err.path)) + ": " + err.message, file=sys.stderr)
    return 2 if errors else 0


def record(asset_id, group, kind, technical_state, tech_review, visual_state,
           behavior_state, behavior_reason, release_state, release_reason,
           issues, historical_notes, mapping, technical_state_reason=None):
    rec = {
        "asset_id": asset_id,
        "record_kind": "package" if asset_id == "CATALOG" else "asset",
        "technical_state": technical_state,
        "visual_state": visual_state,
        "behavior_state": behavior_state,
        "release_state": release_state,
        "release_state_reason": release_reason,
        "issues": sorted(issues, key=lambda i: i["issue_id"]),
        "historical_notes": historical_notes,
        "mapping": mapping,
    }
    if technical_state_reason:
        rec["technical_state_reason"] = technical_state_reason
    if group:
        rec["group"] = group
    if kind:
        rec["kind"] = kind
    if tech_review:
        rec["technical_evidence"] = tech_review
    if behavior_state == "not_required":
        rec["behavior_not_required_reason"] = behavior_reason
    return rec


def check_invariants(doc: dict) -> list:
    errs = []
    records = [doc["package"]] + doc["items"]
    for rec in records:
        rid = rec["asset_id"]
        if rec["visual_state"] == "pass":
            errs.append(f"{rid}: migration emitted visual_state=pass (forbidden)")
        if rec["release_state"] == "released":
            errs.append(f"{rid}: migration emitted release_state=released (forbidden)")
        open_blocking = [
            i for i in rec["issues"]
            if i["status"] == "open" and i["severity"] in ("blocking", "major")
        ]
        if open_blocking and rec["release_state"] != "blocked":
            errs.append(
                f"{rid}: open blocking/major issues {[i['issue_id'] for i in open_blocking]} "
                f"but release_state={rec['release_state']}"
            )
        if rec["behavior_state"] == "not_required" and not rec.get(
            "behavior_not_required_reason"
        ):
            errs.append(f"{rid}: behavior not_required without reason")
        if rec["release_state"] == "blocked" and not open_blocking:
            errs.append(f"{rid}: blocked without open blocking/major issue")
    return errs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    repo = Path(__file__).resolve().parents[2]
    ap.add_argument("--catalog", default="art/full/art_complete_catalog.json")
    ap.add_argument("--reviews-dir", default="art/full/reviews")
    ap.add_argument("--defects", default="art_review/reports/independent_20261024/defects.json")
    ap.add_argument("--source-review-dir", default="art_review/reports/independent_20261024")
    ap.add_argument("--out", default="art_review/vnext/asset_status_migrated.json")
    ap.add_argument("--schema", default="art_review/vnext/asset_status.schema.json")
    ap.add_argument("--contract-version", default="1.3.0")
    ap.add_argument("--as-of", default=None, help="ISO timestamp override for migrated_at")
    args = ap.parse_args(argv)

    catalog_p = (repo / args.catalog) if not Path(args.catalog).is_absolute() else Path(args.catalog)
    reviews_d = (repo / args.reviews_dir) if not Path(args.reviews_dir).is_absolute() else Path(args.reviews_dir)
    defects_p = (repo / args.defects) if not Path(args.defects).is_absolute() else Path(args.defects)

    out_p = Path(args.out) if Path(args.out).is_absolute() else (repo / args.out)
    try:
        out_rel = out_p.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        print(f"ERROR: output must live inside the repo: {out_p}", file=sys.stderr)
        return 3
    if not out_rel.startswith(OUT_PREFIX):
        print(
            f"ERROR: output must stay under {OUT_PREFIX} (old frozen paths are read-only); got {out_rel}",
            file=sys.stderr,
        )
        return 3

    try:
        catalog = load_json(catalog_p)
        defects_doc = load_json(defects_p)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read inputs: {exc}", file=sys.stderr)
        return 3

    migrated_from = [
        {"path": args.catalog, "sha256": sha256_file(catalog_p)},
        {"path": args.defects, "sha256": sha256_file(defects_p)},
    ]

    issues_by_asset = {}
    for defect in defects_doc.get("defects", []):
        issue = make_issue(defect, args.source_review_dir)
        ids = defect_asset_ids(defect)
        for aid in ids:
            issues_by_asset.setdefault(aid, []).append(issue)

    package_open_ids = [d["id"] for d in defects_doc.get("defects", []) if d.get("status", "open") == "open"]
    package_blocking = [
        d for d in defects_doc.get("defects", [])
        if d.get("status", "open") == "open" and d["severity"] in ("blocking", "major")
    ]

    items = []
    for item in catalog.get("items", []):
        aid = item["id"]
        old_status = item.get("status", "missing")
        technical_state = TECH_TO_STATE.get(old_status)
        if technical_state is None:
            print(f"ERROR: unknown old status {old_status!r} for {aid}", file=sys.stderr)
            return 3

        tech_review = None
        tech_reason = None
        review_file = reviews_d / f"{aid}.json"
        old_decision = old_reviewer = None
        if review_file.exists():
            try:
                rev = load_json(review_file)
            except (OSError, json.JSONDecodeError) as exc:
                print(f"ERROR: cannot read review {review_file}: {exc}", file=sys.stderr)
                return 3
            old_decision = rev.get("decision")
            old_reviewer = rev.get("reviewer")
            limitations = list(rev.get("limitations", []))
            ok, why = review_check(repo, aid, rev)
            if not ok:
                limitations.append("Review not accepted for technical_state: " + why)
                tech_reason = "技术自检未通过F04成功白名单/证据校验: " + why
                technical_state = "source_ready" if technical_state == "import_verified" else technical_state
            else:
                technical_state = "import_verified"
            tech_review = {
                "review_kind": "technical_self_check",
                "reviewer": old_reviewer,
                "decision": old_decision,
                "reviewed_at": rev.get("reviewed_at"),
                "evidence": list(rev.get("evidence", [])),
                "source_file": args.reviews_dir + "/" + review_file.name,
                "limitations": limitations,
            }
        else:
            tech_reason = "无技术自检review文件；旧目录状态不能单独支撑import_verified"
            technical_state = "source_ready" if technical_state == "import_verified" else technical_state

        issues = list(issues_by_asset.get(aid, []))
        has_open_blocking = any(
            i["status"] == "open" and i["severity"] in ("blocking", "major") for i in issues
        )
        has_visual_defect = any(
            i["issue_id"] in VISUAL_DEFECT_IDS and i["status"] == "open" for i in issues
        )
        visual_state = "rework" if has_visual_defect else "not_reviewed"
        behavior_fail = any(
            i["issue_id"] in BEHAVIOR_FAIL_DEFECT_IDS and i["status"] == "open" for i in issues
        )
        kind = item.get("kind", "")
        if kind in BEHAVIOR_NOT_REQUIRED_KINDS:
            behavior_state, behavior_reason = "not_required", BEHAVIOR_NOT_REQUIRED_REASON
        elif behavior_fail:
            behavior_state, behavior_reason = "fail", None
        else:
            behavior_state, behavior_reason = "not_tested", None

        if has_open_blocking:
            blocking_ids = [i["issue_id"] for i in issues
                            if i["status"] == "open" and i["severity"] in ("blocking", "major")]
            release_state = "blocked"
            release_reason = f"独立审核未解blocking/major问题: {','.join(blocking_ids)}（{args.source_review_dir}）"
        else:
            release_state = "reviewed_not_released"
            release_reason = (
                "包含于2026-10-24独立返修整体结论(review_gate blocked/H02)；无本条目未解blocking/major问题；"
                "released只能由外部控制器产生"
            )

        items.append(record(
            aid, item.get("group", ""), kind, technical_state, tech_review,
            visual_state, behavior_state, behavior_reason,
            release_state, release_reason, issues,
            [str(b) for b in item.get("blockers", [])],
            {"old_status": old_status, "old_decision": old_decision, "old_reviewer": old_reviewer},
            technical_state_reason=tech_reason,
        ))

    items.sort(key=lambda r: r["asset_id"])

    package_release = "blocked" if package_blocking else "reviewed_not_released"
    package_reason = (
        f"未解blocking/major问题{len(package_blocking)}项: {','.join(d['id'] for d in package_blocking)}"
        if package_blocking
        else "无未解blocking/major问题；released只能由外部控制器产生"
    )
    package_rec = record(
        "CATALOG", None, None,
        TECH_TO_STATE.get(catalog.get("status", "missing"), "missing"),
        {
            "review_kind": "technical_self_check",
            "reviewer": "producer technical engine check (not independent stage signoff)",
            "decision": catalog.get("status", "unknown"),
            "evidence": [args.catalog],
            "source_file": args.catalog,
            "limitations": [],
        },
        "not_reviewed", "not_tested", None,
        package_release, package_reason,
        [make_issue(d, args.source_review_dir) for d in defects_doc.get("defects", [])
         if not defect_asset_ids(d)],
        [f"catalog_status={catalog.get('status')}"],
        {"old_status": catalog.get("status"), "old_decision": None, "old_reviewer": None},
    )
    package_rec["open_issue_ids_all"] = package_open_ids
    package_rec["decision_source"] = defects_doc.get("decision")
    package_rec["accepted"] = defects_doc.get("accepted")

    doc = {
        "schema_version": SCHEMA_VERSION,
        "vnext_effective": False,
        "contract_version_in_effect": args.contract_version,
        "migrated_from": migrated_from,
        "migrated_at": args.as_of or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "package": package_rec,
        "items": items,
    }

    errs = check_invariants(doc)
    if errs:
        for e in errs:
            print(f"INVARIANT VIOLATION: {e}", file=sys.stderr)
        return 2

    schema_p = Path(args.schema) if Path(args.schema).is_absolute() else (repo / args.schema)
    schema_status = validate_schema(doc, schema_p)
    if schema_status:
        return schema_status

    out_p.parent.mkdir(parents=True, exist_ok=True)
    with out_p.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")

    n_rework = sum(1 for r in items if r["visual_state"] == "rework")
    n_blocked = sum(1 for r in items if r["release_state"] == "blocked")
    n_issues = sum(len(r["issues"]) for r in items) + len(package_rec["issues"])
    n_tech_demoted = sum(1 for r in items if r.get("technical_state_reason"))
    print(f"OK wrote {out_rel} (schema=draft-07 pass)")
    print(f"items={len(items)} rework={n_rework} blocked={n_blocked} "
          f"package={package_release} total_issue_attachments={n_issues} "
          f"technical_state_notes={n_tech_demoted}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
