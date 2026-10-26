"""Create the candidate_n5 source package and lock its SHA.

Freeze order (N5_EXECUTION_DESIGN_AND_GAP_AUDIT.md §5):
  editable sources + evidence frozen -> source ZIP -> its SHA -> manifest
The manifest references the source ZIP by hash; no ZIP may contain the
manifest that describes itself.

Execution logs (performance/) deliberately stay OUT of the source ZIP: they keep
changing while the run is in progress, which is what made the n4 archive drift.
They are archived separately, if at all, after the run ends.

Usage:
  python delivery/next_cycle/n5/make_n5_source_pack.py            # write v8
  python delivery/next_cycle/n5/make_n5_source_pack.py --check    # verify only
"""
import argparse
import json
import os
import zipfile
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "delivery/courtyard_scene_demo_sources_v9.zip"
STAMP = ROOT / "delivery/next_cycle/n5/source_package_v9.json"

INCLUDE_DIRS = [
    "art/candidates/candidate_n5/source",
    "art/candidates/candidate_n5/ui",
    "demo_n5/assets",
    "demo_n5/settings",
    "tools/blender_n5",
    "tools/ui_n5",
    "tools/textures_n5",
    "tools/art_gate",
    "art/iterations/cycle_04/reviews",
    "art/iterations/cycle_04/PROP001/versions",
]
INCLUDE_FILES = [
    "demo_n5/build-config-web-desktop.json",
    "demo_n5/package.json",
    "demo_n5/tsconfig.json",
    "tools/producer_review.py",
    "tools/art_harness.py",
    "tools/workflow.py",
    "tools/cocos/build_web_desktop.py",
    "tools/n5_log.py",
    "tools/n5_build.py",
    "tools/n5_baseline.py",
    "delivery/RUN_DEMO_v8.md",
    "art_review/harness_contract.json",
    "art_review/rubric.json",
    "planning/execution/producer_review_policy.json",
    "PRODUCER_SELF_REVIEW.md",
    "PHASE1_ART_ACCEPTANCE.md",
]
EVIDENCE_DIRS = ["T2", "T4", "T5", "T6"]
EXCLUDE_DIR_NAMES = {"build", "library", "temp", "profiles", "node_modules", "__pycache__", "performance"}
EXCLUDE_SUFFIXES = {".tmp", ".db", ".log", ".blend1", ".glb"}


def iter_dir(rel):
    base = ROOT / rel
    if not base.is_dir():
        return
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIR_NAMES]
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix in EXCLUDE_SUFFIXES:
                continue
            yield p.relative_to(ROOT).as_posix()


def collect():
    files = set()
    for rel in INCLUDE_DIRS:
        files.update(iter_dir(rel))
    for rel in INCLUDE_FILES:
        if (ROOT / rel).is_file():
            files.add(rel)
    n5 = ROOT / "delivery/next_cycle/n5"
    for p in sorted(n5.glob("*.js")) + sorted(n5.glob("*.py")):
        files.add(p.relative_to(ROOT).as_posix())
    # Review outputs reference the manifest, which references this ZIP. Shipping
    # them inside it would create a hash cycle, so they stay out of the archive.
    REVIEW_OUTPUTS = {"producer_self_review_n5.json", "producer_submission_check_n5.json"}
    for sub in EVIDENCE_DIRS:
        for p in sorted((n5 / sub).rglob("*.json")):
            if p.name in REVIEW_OUTPUTS:
                continue
            files.add(p.relative_to(ROOT).as_posix())
    return sorted(files)


def verify_zip():
    if not OUT.is_file():
        raise SystemExit("source package missing: %s" % OUT)
    stamp = json.loads(STAMP.read_text(encoding="utf-8-sig"))
    actual = sha256(OUT.read_bytes()).hexdigest()
    with zipfile.ZipFile(OUT) as z:
        bad = z.testzip()
        names = z.namelist()
        dupes = {n for n in names if names.count(n) > 1}
        inner = {n: sha256(z.read(n)).hexdigest() for n in names}
    problems = []
    if bad:
        problems.append("CRC failure at %s" % bad)
    if dupes:
        problems.append("duplicate entries: %s" % sorted(dupes))
    if actual != stamp.get("sha256"):
        problems.append("ZIP sha drift: disk %s != stamp %s" % (actual, stamp.get("sha256")))
    if len(names) != stamp.get("entries"):
        problems.append("entry count %d != stamp %d" % (len(names), stamp.get("entries")))
    missing_on_disk = [n for n in inner if not (ROOT / n).is_file()]
    if missing_on_disk:
        problems.append("ZIP entries missing on disk: %d" % len(missing_on_disk))
    mismatched = [n for n, h in inner.items()
                  if (ROOT / n).is_file() and sha256((ROOT / n).read_bytes()).hexdigest() != h]
    if mismatched:
        problems.append("ZIP/disk sha mismatch: %d (%s)" % (len(mismatched), mismatched[:3]))
    result = {
        "kind": "n5_source_package_verify",
        "zip": OUT.relative_to(ROOT).as_posix(),
        "sha256": actual,
        "entries": len(names),
        "problems": problems,
        "pass": not problems,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not problems else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.check:
        return verify_zip()

    files = collect()
    if OUT.exists():
        raise SystemExit("refusing to overwrite %s; content changed means a new candidate "
                         "version, not a silent rewrite" % OUT.name)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for rel in files:
            z.write(ROOT / rel, rel)
    stamp = {
        "kind": "candidate_n5_source_package",
        "candidate_id": "candidate_n5",
        "path": OUT.relative_to(ROOT).as_posix(),
        "bytes": OUT.stat().st_size,
        "sha256": sha256(OUT.read_bytes()).hexdigest(),
        "entries": len(files),
        "excludes": "performance logs, *.glb (regenerated), *.blend1, build/library/temp",
        "note": "manifest must reference this SHA; this ZIP must not contain the manifest",
        # Exported binaries are regenerable from the sources above, so they stay
        # out of the archive but their hashes are still pinned for provenance.
        "exports": {rel: sha256((ROOT / rel).read_bytes()).hexdigest()
                    for rel in ("art/candidates/candidate_n5/source/layout/MAP001_courtyard.glb",
                                "art/candidates/candidate_n5/source/environment/ENV006_autumn_tree.glb",
                                "demo_n5/assets/resources/models/MAP001_courtyard.glb")
                    if (ROOT / rel).is_file()},
    }
    STAMP.write_text(json.dumps(stamp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(stamp, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
