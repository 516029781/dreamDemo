"""Mechanical checker for space_base_minigame r03 (v06 candidate).

Reads dims + required checks from HARNESS_SPEC.json (r03 draft), validates the
delivery set, evidence existence, coverage, id consistency, manifest binding and
isolated reproduction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

from PIL import Image

REQ_RE = re.compile(r"^\|\s*(REQ-\d+)\s*\|", re.M)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--run", required=True)
    ap.add_argument("--spec", default="knowledge/business/space_base_minigame/HARNESS_SPEC.json")
    a = ap.parse_args()

    request = Path(a.request).resolve()
    cand = Path(a.candidate).resolve()
    run_dir = request / "runs" / a.run
    ev = run_dir / "evidence"
    ev.mkdir(parents=True, exist_ok=True)
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    hard, notes = [], []

    W = spec["deliverable"]["width"]
    H = spec["deliverable"]["height"]
    MW, MH = spec["deliverable"]["master"]
    CW, CH = spec["deliverable"]["core_tile"]
    HW, HH = spec["deliverable"]["hero"]

    scene = cand / "scene.blend"
    master = cand / "renders" / "space_base_v06_master.png"
    raw = cand / "renders" / "master_raw.png"
    ship = cand / "renders" / "space_base_v06.jpg"
    core = cand / "renders" / "space_base_v06_core.png"
    hero = cand / "renders" / "space_base_v06_hero.png"
    checks = [cand / "renders" / "checks" / n for n in
              ("01_core.png", "02_garden_causeway.png", "03_dock.png",
               "04_north.png", "05_g5_pair.png")]
    required = [scene, master, raw, ship, core, hero, *checks,
                cand / "REVIEW.md", cand / "DELIVERY.json", cand / "GATE_REPORT.json",
                cand / "MANIFEST.json", cand / "REPRODUCE.md"]
    for p in required:
        if not p.exists():
            hard.append(f"missing {p.relative_to(cand)}")

    info = {}
    for key, path, size in (("master", master, (W, H)), ("raw", raw, (MW, MH)),
                            ("core", core, (CW, CH)), ("hero", hero, (HW, HH))):
        if path.exists():
            with Image.open(path) as im:
                info[key] = {"size": list(im.size), "mode": im.mode, "bytes": path.stat().st_size}
                if im.size != size:
                    hard.append(f"{key} size {im.size} != {size}")
    if ship.exists():
        with Image.open(ship) as im:
            info["ship"] = {"size": list(im.size), "mode": im.mode, "format": im.format,
                            "bytes": ship.stat().st_size}
            if im.size != (W, H):
                hard.append(f"JPEG size {im.size} != {(W, H)}")
            if im.mode != "RGB":
                hard.append(f"JPEG mode {im.mode}")
            if im.format != "JPEG":
                hard.append(f"ship format {im.format}")
            if ship.stat().st_size > 3 * 1024 * 1024:
                hard.append(f"JPEG {ship.stat().st_size} > 3 MB")

    # coverage
    brief = (request / "REQUIREMENTS_BRIEF.md").read_text(encoding="utf-8")
    reqs = sorted(set(REQ_RE.findall(brief)))
    cases = json.loads((request / "test_cases.json").read_text(encoding="utf-8"))
    covered = sorted({r for c in cases["cases"] for r in c.get("covers", [])})
    missing = [r for r in reqs if r not in covered]
    extra = [r for r in covered if r not in reqs]
    dangling = [c.get("evidence_path") for c in cases["cases"]
                if c.get("check_type") != "external"
                and not (request / c.get("evidence_path", "")).exists()]
    run_ctx = json.loads((request / "RUN_CONTEXT.json").read_text(encoding="utf-8"))
    resolved = json.loads((request / "RESOLVED_KNOWLEDGE.json").read_text(encoding="utf-8"))
    bad_loaded = []
    for item in resolved.get("loaded", []):
        q = Path(item.get("path", ""))
        if not q.exists():
            bad_loaded.append({"path": str(q), "reason": "missing"})
        elif sha(q) != item.get("sha256"):
            bad_loaded.append({"path": str(q), "reason": "sha mismatch"})
    if bad_loaded:
        hard.append(f"resolved knowledge binding failures {len(bad_loaded)}")
    ids = {"test_cases": cases.get("request_id"), "run_context": run_ctx.get("request_id"),
           "resolved": resolved.get("request_id")}
    ids_ok = len(set(ids.values())) == 1
    if missing or extra or dangling or not ids_ok:
        hard.append(f"coverage/ids missing={missing} extra={extra} dangling={dangling} ids={ids}")

    # required checks coverage in spec
    need = set(spec["required_checks"])
    have = {c["check_id"] for c in spec["checks"]}
    if not need <= have:
        hard.append(f"spec required checks missing definitions {sorted(need - have)}")

    # reproduction
    rep = run_dir / "reproduction.json"
    rep_info = {}
    if rep.exists():
        rep_info = json.loads(rep.read_text(encoding="utf-8"))
        if not rep_info.get("pass"):
            hard.append(f"reproduction not pass: {rep_info.get('rms')}")
    else:
        hard.append("missing reproduction.json")

    # manifest binding
    man_info = {}
    if (cand / "MANIFEST.json").exists():
        man = json.loads((cand / "MANIFEST.json").read_text(encoding="utf-8"))
        entries = man.get("entries") or man.get("files") or []
        bad = []
        for item in entries:
            p = cand / item["path"]
            if not p.exists():
                bad.append({"path": item["path"], "reason": "missing"})
            elif sha(p) != item.get("sha256"):
                bad.append({"path": item["path"], "reason": "sha mismatch"})
        man_info = {"files": len(entries), "bad": bad}
        if bad:
            hard.append(f"manifest binding failures {len(bad)}")

    out = {"schema": "check-summary-v2", "stage": "final", "spec": spec["spec_version"],
           "request": str(request), "candidate": str(cand), "run": a.run,
           "images": info, "coverage": {"requirements": reqs, "covered": covered,
                                        "missing": missing, "extra": extra,
                                        "dangling": dangling, "ids": ids,
                                        "ids_consistent": ids_ok,
                                        "resolved_failures": bad_loaded},
           "manifest": man_info, "reproduction": rep_info,
           "hard_failures": hard, "pass": not hard, "notes": notes}
    (run_dir / "check_summary.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                                encoding="utf-8")
    print("CHECK", "PASS" if not hard else "FAIL", "hard_failures", len(hard))
    for h in hard:
        print(" -", h)
    return 0 if not hard else 1


if __name__ == "__main__":
    sys.exit(main())
