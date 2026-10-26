"""P02 self-check: real Draft-07 validation plus F03/F04 positive/negative cases.

Uses synthetic fixtures only; never touches production reviews or approvals.
"""
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MIGRATOR = ROOT / "tools/art_gate/migrate_catalog.py"
SCHEMA = ROOT / "art_review/vnext/asset_status.schema.json"
MIGRATED = ROOT / "art_review/vnext/asset_status_migrated.json"
TMP = ROOT / "delivery/next_cycle/T0/_p02_tmp"
OUT_DIR = ROOT / "art_review/vnext/_p02_tmp"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def load_migrator():
    spec = importlib.util.spec_from_file_location("migrate_catalog", MIGRATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fixture(case, status, decision, evidence, review_asset=None, reviewer="synthetic technical reviewer"):
    base = TMP / case
    evidence_rel = f"delivery/next_cycle/T0/_p02_tmp/evidence_{case}.png"
    (ROOT / evidence_rel).write_bytes(b"\x89PNG\r\n\x1a\nsynthetic")
    catalog = {"status": "engine_verified", "items": [
        {"id": "ASSET01", "status": status, "kind": "environment", "group": "env", "blockers": []}]}
    defects = {"decision": "rework", "accepted": False, "defects": []}
    write(base / "catalog.json", catalog)
    write(base / "defects.json", defects)
    write(base / "reviews/ASSET01.json", {
        "asset_id": review_asset or "ASSET01", "decision": decision,
        "reviewer": reviewer, "reviewed_at": "2026-10-25",
        "evidence": [evidence_rel if e == "<real>" else e for e in evidence]})
    return base, evidence_rel


def run_case(module, case, status, decision, evidence, review_asset=None):
    base, _ = fixture(case, status, decision, evidence, review_asset)
    out = OUT_DIR / case / "out.json"
    code = module.main([
        "--catalog", str(base / "catalog.json"), "--reviews-dir", str(base / "reviews"),
        "--defects", str(base / "defects.json"), "--out", str(out),
        "--schema", str(SCHEMA), "--as-of", "2026-10-25T00:00:00Z"])
    state = load(out)["items"][0]["technical_state"] if out.is_file() else None
    reason = load(out)["items"][0].get("technical_state_reason") if out.is_file() else None
    return code, state, reason, out


def main():
    if TMP.exists():
        shutil.rmtree(TMP)
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    TMP.mkdir(parents=True)
    OUT_DIR.mkdir(parents=True)

    import jsonschema
    schema = load(SCHEMA)
    real_doc = load(MIGRATED)
    jsonschema.Draft7Validator(schema).validate(real_doc)

    catalog_rec = real_doc["package"]
    results = {
        "kind": "p02_selfcheck_f03_f04",
        "schema_draft07_validator": f"jsonschema {jsonschema.__version__}",
        "schema_sha256": sha(SCHEMA),
        "migrator_sha256": sha(MIGRATOR),
        "migrated_output_sha256": sha(MIGRATED),
        "real_output_schema_valid": True,
        "real_output_invariants": {
            "visual_pass": sum(1 for r in [catalog_rec] + real_doc["items"] if r["visual_state"] == "pass"),
            "released": sum(1 for r in [catalog_rec] + real_doc["items"] if r["release_state"] == "released"),
            "catalog_old_decision": catalog_rec["mapping"]["old_decision"],
        },
        "cases": [],
    }

    module = load_migrator()
    cases = [
        ("fail_empty_evidence_missing", "missing", "fail", [], None, 0, "missing"),
        ("pass_empty_evidence_missing", "missing", "pass", [], None, 0, "missing"),
        ("pass_unresolvable_evidence_missing", "missing", "pass", ["nope/absent.png"], None, 0, "missing"),
        ("pass_wrong_asset_binding", "missing", "pass", ["<real>"], "OTHER9", 0, "missing"),
        ("pass_real_evidence_promotes", "missing", "pass", ["<real>"], None, 0, "import_verified"),
        ("fail_review_demotes_engine_verified", "engine_verified", "fail", [], None, 0, "source_ready"),
    ]
    ok_all = True
    for name, status, decision, evidence, review_asset, want_code, want_state in cases:
        code, state, reason, out = run_case(module, name, status, decision, evidence, review_asset)
        passed = code == want_code and state == want_state
        ok_all = ok_all and passed
        results["cases"].append({
            "case": name, "input_status": status, "review_decision": decision,
            "evidence": evidence, "review_asset": review_asset,
            "exit_code": code, "technical_state": state, "technical_state_reason": reason,
            "expected_state": want_state, "pass": passed,
        })

    # F03: null is explicitly allowed, but other types are still rejected.
    bad = json.loads(json.dumps(real_doc))
    bad["items"][0]["mapping"]["old_decision"] = 123
    null_allowed = not list(jsonschema.Draft7Validator(schema).iter_errors(real_doc))
    bad_rejected = bool(list(jsonschema.Draft7Validator(schema).iter_errors(bad)))
    results["f03_mapping_null_semantics"] = {
        "null_allowed_by_schema": null_allowed,
        "integer_rejected_by_schema": bad_rejected,
        "catalog_old_decision_is_null": catalog_rec["mapping"]["old_decision"] is None,
    }
    ok_all = ok_all and null_allowed and bad_rejected and catalog_rec["mapping"]["old_decision"] is None

    results["all_passed"] = ok_all
    if TMP.exists():
        shutil.rmtree(TMP)
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)

    output = ROOT / "delivery/next_cycle/T0/p02_selfcheck.json"
    write(output, results)
    print(json.dumps({"all_passed": ok_all, "cases": len(results["cases"]),
                      "output": str(output), "sha256": sha(output)}, ensure_ascii=False))
    return 0 if ok_all else 2


if __name__ == "__main__":
    sys.exit(main())
