"""Compare isolated reproduction with the shipping master.

Run:
  python tools/space_base_repro_compare.py --master <master.png> \
      --repro <repro_flipped.png> --out <reproduction.json> \
      --command "<render + flip command>" --exit-code 0 --elapsed-ms 0
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


def content_sha(p: Path) -> str:
    with Image.open(p) as im:
        return hashlib.sha256(im.convert("RGB").tobytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", required=True)
    ap.add_argument("--repro", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--command", default="")
    ap.add_argument("--exit-code", type=int, default=0)
    ap.add_argument("--elapsed-ms", type=int, default=0)
    a = ap.parse_args()
    m, r = Path(a.master), Path(a.repro)
    with Image.open(m) as im1, Image.open(r) as im2:
        size_ok = im1.size == im2.size
        rms = None
        if size_ok:
            diff = ImageChops.difference(im1.convert("RGB"), im2.convert("RGB"))
            rms = round(sum(ImageStat.Stat(diff).rms) / 3.0, 4)
    msha, rsha = content_sha(m), content_sha(r)
    ok = size_ok and (rms is not None and rms <= 2.0)
    payload = {
        "schema": "reproduction-v1", "status": "pass" if ok else "fail",
        "pass": ok, "master": str(m), "repro": str(r),
        "master_content_sha256": msha, "repro_content_sha256": rsha,
        "same_content_sha": msha == rsha,
        "rms": rms, "tolerance": "2.0/255", "size_ok": size_ok,
        "command": a.command, "exit_code": a.exit_code, "elapsed_ms": a.elapsed_ms,
        "note": "Cycles same-scene renders may not be bit-identical; pass by RMS tolerance."
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print("REPRO_COMPARE", payload["status"], "rms", rms, "same", msha == rsha)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
