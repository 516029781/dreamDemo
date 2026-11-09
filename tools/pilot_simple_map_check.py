"""pilot_simple_map 机械检查集（TEST-01 / TEST-04 / TEST-06）

用法：
  python tools/pilot_simple_map_check.py --request knowledge/active/20261102-pilot-simple-map \
      --candidate art/static_map/pilot_simple_map/v01

输出：把证据写到 <request>/runs/<run_id>/evidence/TEST-0X/*.json，并在 stdout 打印 PASS/FAIL。
退出码 0 = 全部非诊断项通过；1 = 有失败。

说明：TEST-04 的数值部分标记为 diagnostic_only，只记录不参与退出码。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from PIL import Image

REQ_RE = re.compile(r"^\|\s*(REQ-\d+)\s*\|", re.M)


def check_size(img: Path) -> dict:
    with Image.open(img) as im:
        w, h = im.size
        mode = im.mode
    ok = (w, h) == (960, 540) and mode in ("RGB", "RGBA")
    return {"test_id": "TEST-01", "image": str(img), "width": w, "height": h,
            "mode": mode, "expect": "960x540", "pass": ok}


def check_values(img: Path) -> dict:
    with Image.open(img) as im:
        rgb = im.convert("RGB")
    px = list(rgb.getdata())
    n = len(px)
    near_black = sum(1 for r, g, b in px if max(r, g, b) < 10)
    near_white = sum(1 for r, g, b in px if min(r, g, b) > 250)
    lum = [0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b in px]
    return {
        "test_id": "TEST-04",
        "image": str(img),
        "pixels": n,
        "near_black_pct": round(near_black * 100.0 / n, 3),
        "near_white_pct": round(near_white * 100.0 / n, 3),
        "luma_min": round(min(lum), 1),
        "luma_max": round(max(lum), 1),
        "luma_mean": round(sum(lum) / n, 1),
        "thresholds": "near_black<1% and near_white<1%",
        "diagnostic_only": True,
    }


def check_linkage(request: Path) -> dict:
    brief = (request / "REQUIREMENTS_BRIEF.md").read_text(encoding="utf-8")
    reqs = sorted(set(REQ_RE.findall(brief)))
    cases = json.loads((request.parents[1] / "business" / "pilot_simple_map" / "test_cases.json")
                       .read_text(encoding="utf-8"))
    covered = sorted({r for c in cases["cases"] for r in c.get("covers", [])})
    missing = [r for r in reqs if r not in covered]
    extra = [r for r in covered if r not in reqs]

    dangling = []
    for c in cases["cases"]:
        p = c.get("evidence_path", "")
        if p.startswith("runs/"):
            if not (request / p).parent.exists():
                dangling.append(p)

    run_ctx = json.loads((request / "RUN_CONTEXT.json").read_text(encoding="utf-8"))
    resolved = json.loads((request / "RESOLVED_KNOWLEDGE.json").read_text(encoding="utf-8"))
    ids = {
        "brief": "20261102-pilot-simple-map",
        "test_cases": cases["request_id"],
        "run_context": run_ctx["request_id"],
        "resolved": resolved["request_id"],
    }
    consistent = len(set(ids.values())) == 1
    ok = not missing and not extra and not dangling and consistent
    return {"test_id": "TEST-06", "requirements": reqs, "covered": covered,
            "missing": missing, "extra": extra, "dangling_evidence": dangling,
            "request_ids": ids, "ids_consistent": consistent, "pass": ok}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--run", default="20261102-0710")
    a = ap.parse_args()

    request = Path(a.request).resolve()
    candidate = Path(a.candidate).resolve()
    ev = request / "runs" / a.run / "evidence"
    img = candidate / "renders" / "final.png"

    results = []
    for sub, name, payload in [
        ("TEST-01", "size.json", check_size(img)),
        ("TEST-04", "value_stats.json", check_values(img)),
        ("TEST-06", "linkage.json", check_linkage(request)),
    ]:
        d = ev / sub
        d.mkdir(parents=True, exist_ok=True)
        (d / name).write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        results.append(payload)
        flag = "PASS" if payload.get("pass") else ("SKIP(diagnostic)" if payload.get("diagnostic_only") else "FAIL")
        print(f"{sub} {flag}")
        if sub == "TEST-06" and not payload["pass"]:
            print("  missing:", payload["missing"], "extra:", payload["extra"],
                  "dangling:", payload["dangling_evidence"], "ids_ok:", payload["ids_consistent"])

    hard_fail = [r["test_id"] for r in results if not r.get("pass") and not r.get("diagnostic_only")]
    print("CHECK_EXIT", "fail" if hard_fail else "ok", hard_fail)
    return 1 if hard_fail else 0


if __name__ == "__main__":
    sys.exit(main())
