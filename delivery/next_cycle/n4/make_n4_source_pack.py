"""Create candidate_n4 source package v7."""
import json
import os
import zipfile
from pathlib import Path
from hashlib import sha256

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "delivery/courtyard_scene_demo_sources_v7.zip"

INCLUDE_DIRS = [
    "art/candidates/candidate_n4/source",
    "art/candidates/candidate_n4/ui",
    "demo_n4/assets",
    "demo_n4/settings",
    "tools/blender_n4",
    "tools/ui_n4",
    "tools/textures_n4",
    "tools/art_gate",
    "art/iterations/cycle_04/reviews",
    "art/iterations/cycle_04/PROP001/versions",
]
INCLUDE_FILES = [
    "demo_n4/build-config-web-desktop.json",
    "demo_n4/package.json",
    "demo_n4/tsconfig.json",
    "tools/producer_review.py",
    "tools/art_harness.py",
    "tools/workflow.py",
    "tools/cocos/build_web_desktop.py",
    "delivery/RUN_DEMO_v7.md",
    "art_review/harness_contract.json",
    "art_review/rubric.json",
    "planning/execution/producer_review_policy.json",
    "PRODUCER_SELF_REVIEW.md",
    "PHASE1_ART_ACCEPTANCE.md",
]
EXCLUDE_DIR_NAMES = {"build", "library", "temp", "profiles", "node_modules", "__pycache__"}
EXCLUDE_SUFFIXES = {".tmp", ".db"}


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


def main():
    files = set()
    for rel in INCLUDE_DIRS:
        files.update(iter_dir(rel))
    for rel in INCLUDE_FILES:
        if (ROOT / rel).is_file():
            files.add(rel)
    # Current-build evidence scripts and logs (not screenshots). The JSON
    # results carry provenance such as the projected tree-shadow bake params.
    n4 = ROOT / "delivery/next_cycle/n4"
    for p in sorted(n4.glob("*.js")) + sorted(n4.glob("*.py")) + sorted(n4.glob("*.log")):
        files.add(p.relative_to(ROOT).as_posix())
    for sub in ("T2", "T4", "T5", "T6"):
        for p in sorted((n4 / sub).rglob("*.json")):
            files.add(p.relative_to(ROOT).as_posix())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for rel in sorted(files):
            z.write(ROOT / rel, rel)
    manifest = {
        "kind": "candidate_n4_source_package",
        "path": OUT.relative_to(ROOT).as_posix(),
        "bytes": OUT.stat().st_size,
        "sha256": sha256(OUT.read_bytes()).hexdigest(),
        "entries": len(files),
    }
    (ROOT / "delivery/next_cycle/n4/source_package_v7.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
