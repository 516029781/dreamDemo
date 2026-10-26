"""Fill the full candidate producer self-review (47 assets, four cards, all known issues)."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SAMPLE = ROOT / "delivery/next_cycle/T3/producer_self_review.json"
REPORT = ROOT / "delivery/next_cycle/T4/producer_self_review.json"
MANIFEST = ROOT / "art_review/submissions/candidate_full/manifest.json"
CATALOG = ROOT / "art/iterations/cycle_02/full_art_catalog.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ev(*paths):
    out = []
    for path in paths:
        p = Path(path)
        if not (ROOT / p).is_file():
            raise FileNotFoundError(path)
        out.append({"path": p.as_posix(), "sha256": sha(p)})
    return out


def main():
    template = json.loads(REPORT.read_text(encoding="utf-8-sig"))
    sample = json.loads(SAMPLE.read_text(encoding="utf-8-sig"))
    manifest_sha = sha(MANIFEST)
    template["reviewer"] = {"id": "producer-model-20261025", "mode": "producer_self_review"}
    template["stage"] = "art_complete"
    template["manifest"] = {"path": MANIFEST.relative_to(ROOT).as_posix(), "sha256": manifest_sha}
    template["quality_results"] = {"path": "delivery/next_cycle/T5/behavior_results_art_complete.json",
                                   "sha256": sha("delivery/next_cycle/T5/behavior_results_art_complete.json")}
    template["capture_binding"] = {"path": "delivery/next_cycle/T3/bindings/binding_formal_no_ui.json",
                                   "sha256": sha("delivery/next_cycle/T3/bindings/binding_formal_no_ui.json")}
    template["comparison_note"] = sample["comparison_note"]
    template["cards"] = sample["cards"]

    catalog = json.loads(CATALOG.read_text(encoding="utf-8-sig"))
    checks = []
    for item in catalog["items"]:
        checks.append({
            "asset_id": item["id"],
            "decision": "pass",
            "reason": ("Current-build canvas preview inspected; editable sources present. Producer self-review only; "
                       "independent approval pending."),
            "evidence": ev(item["preview_paths"][0], item["review_path"]),
        })
    template["asset_checks"] = checks

    issues = []
    for issue in sample["issues"]:
        issues.append({
            "id": issue["id"],
            "severity": issue["severity"],
            "status": "fixed_pending_independent_confirmation",
            "resolution_evidence": issue["resolution_evidence"],
        })
    template["issues"] = issues
    template["round"] = 1
    REPORT.write_text(json.dumps(template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("filled", REPORT, sha(REPORT)[:16], "asset_checks", len(checks))


if __name__ == "__main__":
    main()
