#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Copy the built map GLB into the Cocos project, with a hash gate.

`run_courtyard_build.ps1 -Stage map001` writes the GLB to the candidate source
tree. The Cocos project reads a separate copy under `demo_n5/assets/resources/
models/`, and nothing in the repository moved one to the other — W3 could build
geometry but never see it in the engine.

The `.meta` file is deliberately left alone: it carries the asset uuid, and
replacing it would break every prefab reference to the model.

    python tools/sync_map_glb.py            # dry run, prints the plan
    python tools/sync_map_glb.py --apply    # copy, then verify both hashes
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "art/candidates/candidate_n5/source/layout/MAP001_courtyard.glb")
DST = os.path.join(ROOT, "demo_n5/assets/resources/models/MAP001_courtyard.glb")
REPORT = os.path.join(ROOT, "delivery/performance/sync_map_glb.json")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def triangles(path):
    """Read the triangle count out of the GLB header, no external deps."""
    import struct
    with open(path, "rb") as fh:
        magic, _ver, _length = struct.unpack("<III", fh.read(12))
        if magic != 0x46546C67:
            return None
        clen, _ctype = struct.unpack("<II", fh.read(8))
        doc = json.loads(fh.read(clen).decode("utf-8"))
    acc = doc.get("accessors", [])
    total = 0
    for mesh in doc.get("meshes", []):
        for prim in mesh.get("primitives", []):
            idx = prim.get("indices")
            if idx is not None:
                total += acc[idx]["count"] // 3
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="perform the copy")
    args = ap.parse_args()

    for path, label in ((SRC, "source"), (DST, "engine")):
        if not os.path.isfile(path):
            raise SystemExit("missing %s model: %s" % (label, path))

    src_sha = sha256(SRC)
    dst_sha = sha256(DST)
    src_mb = os.path.getsize(SRC) / 1048576.0
    dst_mb = os.path.getsize(DST) / 1048576.0

    plan = {
        "source": os.path.relpath(SRC, ROOT).replace("\\", "/"),
        "engine": os.path.relpath(DST, ROOT).replace("\\", "/"),
        "source_sha256": src_sha,
        "engine_sha256": dst_sha,
        "source_mb": round(src_mb, 1),
        "engine_mb": round(dst_mb, 1),
        "source_triangles": triangles(SRC),
        "engine_triangles": triangles(DST),
        "identical": src_sha == dst_sha,
        "meta_preserved": os.path.isfile(DST + ".meta"),
    }

    if not args.apply:
        print(json.dumps(dict(plan, action="dry-run"), ensure_ascii=False, indent=1))
        return

    if src_sha == dst_sha:
        print(json.dumps(dict(plan, action="no-op", reason="already identical"), ensure_ascii=False))
        return

    shutil.copyfile(SRC, DST)
    after = sha256(DST)
    ok = after == src_sha
    result = dict(plan, action="copied", after_sha256=after, verified=ok,
                  synced_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(json.dumps({k: result[k] for k in ("action", "source_mb", "engine_mb",
                                             "source_triangles", "verified")},
                     ensure_ascii=False))
    if not ok:
        raise SystemExit(1)
    if not result["meta_preserved"]:
        print("WARN: no .meta next to the engine model; Cocos will import it as a new asset",
              file=sys.stderr)


if __name__ == "__main__":
    main()
