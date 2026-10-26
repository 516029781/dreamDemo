"""Build and verify the candidate_n2 review pack; write checksum outside the ZIP."""
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACK_REL = "delivery/candidate_n2_review_pack_20261025.zip"
PACK = ROOT / PACK_REL
VERIFY_REL = "delivery/N08_pack_verification.json"
SHA_REL = "delivery/candidate_n2_review_pack_20261025.zip.sha256"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8-sig"))


def main():
    manifest_rel = "art_review/submissions/candidate_n2/manifest.json"
    manifest = load(manifest_rel)
    paths = []
    for row in manifest["artifacts"] + manifest.get("catalog_members", []):
        paths.append(row["path"])
    extras = [
        manifest_rel,
        "art_review/submissions/candidate_n2/spec.json",
        "delivery/next_cycle/T4/producer_self_review.json",
        "delivery/next_cycle/T4/producer_submission_check.json",
        "delivery/next_cycle/N_rework/REWORK_REPORT.md",
        "delivery/next_cycle/N_rework/FINAL_REVIEW_REQUEST.md",
        "delivery/next_cycle/N_rework/N08_pack_plan.json",
        "delivery/next_cycle/N_rework/q04_normal_move_n.json",
        "delivery/next_cycle/N_rework/q04_pause_n.json",
        "delivery/next_cycle/N_rework/q04_dialogue_n.json",
        "delivery/next_cycle/N_rework/q04_resume_n.json",
        "delivery/next_cycle/T2/sample_manifest.json",
        "delivery/next_cycle/T7/I07_manifest_verify.json",
        "delivery/next_cycle/T7/I07_complete_candidate_package.json",
        "delivery/REVIEW_HANDOFF.md",
        "delivery/COMPLETE_CANDIDATE_DELIVERY.md",
        "art_review/rubric.json",
        "art_review/harness_contract.json",
        "planning/execution/producer_review_policy.json",
        "PRODUCER_SELF_REVIEW.md",
        "PHASE1_ART_ACCEPTANCE.md",
        "tools/producer_review.py",
        "tools/art_harness.py",
        "tools/art_gate/check_quality.py",
        "tools/art_gate/check_bindings.py",
        "reference/_raw_screenshots/P1/t015s.jpg",
        "reference/_raw_screenshots/P1/t044s.jpg",
        "reference/_raw_screenshots/P1/t084s.jpg",
    ]
    for p in extras:
        paths.append(p)
    seen = []
    for p in paths:
        if p not in seen:
            seen.append(p)
    missing = [p for p in seen if not (ROOT / p).is_file()]
    if missing:
        raise SystemExit("missing files: " + repr(missing))

    stale_terms = ("final4", "candidate_full", "finalN_formal", "finalN_dialogue",
                   "T3/bindings/", "T6/character/char_", "behavior_results.json",
                   "lighting_profile_v2", "plant_finalN_", "mat_finalN_")
    stale = []
    for p in seen:
        for term in stale_terms:
            if term in p:
                stale.append((p, term))
                break
    if stale:
        raise SystemExit("stale path selected: " + repr(stale))

    tmp = PACK.with_suffix(".zip.tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in seen:
            z.writestr(p, (ROOT / p).read_bytes())
    tmp.replace(PACK)

    # Re-open the final ZIP and compare every entry to disk.
    mismatches = []
    missing_disk = []
    with zipfile.ZipFile(PACK) as z:
        names = z.namelist()
        for n in names:
            disk = ROOT / n
            if not disk.is_file():
                missing_disk.append(n)
                continue
            if hashlib.sha256(z.read(n)).hexdigest() != sha(disk):
                mismatches.append(n)
        crc_bad = z.testzip()

    verification = {
        "kind": "n08_final_pack_verification",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pack": PACK_REL,
        "pack_sha256": sha(PACK),
        "pack_bytes": PACK.stat().st_size,
        "entry_count": len(names),
        "verified_entries": len(names) - len(mismatches) - len(missing_disk),
        "mismatches": mismatches,
        "missing_on_disk": missing_disk,
        "crc_error": crc_bad,
        "stale_path_hits": [],
        "bindings": {
            "manifest": {"path": manifest_rel, "sha256": sha(ROOT / manifest_rel)},
            "self_review": {"path": "delivery/next_cycle/T4/producer_self_review.json",
                            "sha256": sha(ROOT / "delivery/next_cycle/T4/producer_self_review.json")},
            "producer_check": {"path": "delivery/next_cycle/T4/producer_submission_check.json",
                               "sha256": sha(ROOT / "delivery/next_cycle/T4/producer_submission_check.json")},
            "catalog": {"path": "art/iterations/cycle_03/full_art_catalog.json",
                        "sha256": sha(ROOT / "art/iterations/cycle_03/full_art_catalog.json")},
            "source_zip": {"path": "delivery/courtyard_scene_demo_sources_v5.zip",
                           "sha256": sha(ROOT / "delivery/courtyard_scene_demo_sources_v5.zip")},
            "run_instructions": {"path": "delivery/RUN_DEMO_v5.md",
                                 "sha256": sha(ROOT / "delivery/RUN_DEMO_v5.md")},
        },
        "checks": {
            "entry_count_matches_expected": len(names) == len(seen),
            "all_entries_match_disk": not mismatches and not missing_disk,
            "no_stale_paths": True,
            "crc_ok": crc_bad is None,
            "checksum_outside_zip": True,
        },
        "result": "pass" if (not mismatches and not missing_disk and crc_bad is None and len(names) == len(seen)) else "fail",
        "note": ("ZIP entries are project-relative and byte-identical to disk at verification time. "
                 "The .sha256 and this verification file are outside the ZIP."),
    }
    if verification["result"] != "pass":
        raise SystemExit("pack verification failed: " + json.dumps(verification, ensure_ascii=False))
    (ROOT / VERIFY_REL).write_text(json.dumps(verification, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / SHA_REL).write_text(f"{verification['pack_sha256']}  candidate_n2_review_pack_20261025.zip\n", encoding="ascii")
    print(json.dumps({"pack": PACK_REL, "sha256": verification["pack_sha256"], "bytes": verification["pack_bytes"],
                      "entries": len(names), "result": verification["result"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
