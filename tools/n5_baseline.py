"""Record the candidate_n5 baseline: inherited editable sources with SHAs."""
import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASES = [
    "art/candidates/candidate_n5/source",
    "art/candidates/candidate_n5/ui",
    "tools/blender_n5",
    "tools/textures_n5",
    "tools/ui_n5",
    "demo_n5/assets",
]
SKIP_DIRS = {"__pycache__", "node_modules", "library", "temp", "build"}
SKIP_SUFFIX = (".glb", ".blend1")
OUT = os.path.join(ROOT, "delivery/next_cycle/n5/performance/baseline_n5.json")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    files = {}
    for base in BASES:
        full = os.path.join(ROOT, base)
        if not os.path.isdir(full):
            continue
        for dirpath, dirnames, filenames in os.walk(full):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in filenames:
                if name.endswith(SKIP_SUFFIX):
                    continue
                p = os.path.join(dirpath, name)
                files[os.path.relpath(p, ROOT).replace("\\", "/")] = sha(p)
    payload = {
        "candidate_id": "candidate_n5",
        "inherited_from": "candidate_n4",
        "created_utc": "2026-10-26",
        "excluded": "*.glb (regenerated from editable sources), *.blend1 (Blender backups)",
        "read_only_originals": ["art/candidates/candidate_n2", "art/candidates/candidate_n4",
                                "demo_n4", "delivery/next_cycle/n4"],
        "file_count": len(files),
        "files": dict(sorted(files.items())),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(json.dumps({"file_count": len(files),
                      "blend": sum(1 for k in files if k.endswith(".blend")),
                      "svg": sum(1 for k in files if k.endswith(".svg")),
                      "out": os.path.relpath(OUT, ROOT).replace("\\", "/")},
                     ensure_ascii=False))


main()
