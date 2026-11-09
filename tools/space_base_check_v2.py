"""Mechanical checker for space_base_minigame v02 (detail pass).

Run:
  python tools/space_base_check_v2.py --request knowledge/active/20261102-space-base-detail \
      --candidate art/static_map/space_base_minigame/v02 --run 20261102-1907 --stage final

Same contract as v01, plus D1-D5 evidence files. Visual checks stay producer-reviewed;
this script does not judge art and never turns external checks into pass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from PIL import Image

REQ_RE = re.compile(r"^\|\s*(REQ-\d+)\s*\|", re.M)
W, H = 1920, 2560
MASTER_NAME = "space_base_v02_master.png"
SHIP_NAME = "space_base_v02.jpg"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--run", default="20261102-1907")
    ap.add_argument("--stage", choices=["prototype", "final"], default="final")
    a = ap.parse_args()

    request = Path(a.request).resolve()
    candidate = Path(a.candidate).resolve()
    run_dir = request / "runs" / a.run
    ev = run_dir / "evidence"
    ev.mkdir(parents=True, exist_ok=True)
    hard = []
    out = {"stage": a.stage, "request": str(request), "candidate": str(candidate), "run": a.run}

    scene = candidate / "scene.blend"
    gray = candidate / "renders" / "graybox.png"
    if not scene.exists():
        hard.append("missing scene.blend")
    if a.stage == "prototype":
        if not gray.exists():
            hard.append("missing renders/graybox.png")
        for rel in ("G1/camera_projection.json", "G6/geom_check.json", "G7/viewport_math.json"):
            if not (ev / rel).exists():
                hard.append(f"missing evidence {rel}")
        out["hard_failures"] = hard
        out["pass"] = not hard
        (ev / "check_summary.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("CHECK", "PASS" if not hard else "FAIL", hard)
        return 0 if not hard else 1

    master = candidate / "renders" / MASTER_NAME
    ship = candidate / "renders" / SHIP_NAME
    checks = [candidate / "renders" / "checks" / n for n in
              ("01_core.png", "02_workshop.png", "03_south_exit.png", "04_ceo.png")]
    detail_evidence = [ev / "D1" / "D1.md", ev / "D2" / "D2.md", ev / "D3" / "D3.json",
                       ev / "D4" / "D4.md", ev / "D5" / "D5.md"]
    required = [scene, master, ship, *checks,
                candidate / "reference_analysis" / "SPACE_BASE_REFERENCE_PROFILE.json",
                candidate / "REVIEW.md", candidate / "DELIVERY.json", candidate / "GATE_REPORT.json",
                candidate / "MANIFEST.json", candidate / "REPRODUCE.md", *detail_evidence]
    for p in required:
        if not p.exists():
            hard.append(f"missing {p.relative_to(candidate) if candidate in p.parents else p}")

    img_info = {}
    if master.exists():
        with Image.open(master) as im:
            img_info["master"] = {"size": list(im.size), "mode": im.mode, "bytes": master.stat().st_size}
            if im.size != (3840, 5120):
                hard.append(f"master size {im.size} != 3840x5120")
    if ship.exists():
        with Image.open(ship) as im:
            img_info["ship"] = {"size": list(im.size), "mode": im.mode, "format": im.format, "bytes": ship.stat().st_size}
            if im.size != (W, H):
                hard.append(f"JPEG size {im.size} != {W}x{H}")
            if im.format != "JPEG":
                hard.append(f"ship format {im.format} != JPEG")
            if im.mode not in ("RGB", "L"):
                hard.append(f"ship mode {im.mode} has alpha")
            if ship.stat().st_size > 3 * 1024 * 1024:
                hard.append(f"JPEG bytes {ship.stat().st_size} > 3 MB")
        w1 = {"test_id": "TEST-W1", "check": "W1", **img_info["ship"],
              "max_edge": max(img_info["ship"]["size"]), "limit_bytes": 3 * 1024 * 1024,
              "pass": not any("JPEG" in x or "ship" in x for x in hard)}
        (ev / "W1").mkdir(parents=True, exist_ok=True)
        (ev / "W1" / "file_check.json").write_text(json.dumps(w1, ensure_ascii=False, indent=1), encoding="utf-8")

    map_bytes = ship.stat().st_size if ship.exists() else 0
    repo_root = Path("C:/软件/鼠鼠")
    js_dir = repo_root / "js"
    js_bytes = sum(p.stat().st_size for p in js_dir.glob("**/*") if p.is_file()) if js_dir.exists() else 0
    config_bytes = sum((repo_root / n).stat().st_size for n in ("game.json", "project.config.json") if (repo_root / n).exists())
    main_bytes = map_bytes + js_bytes + config_bytes
    w2 = {"test_id": "TEST-W2", "check": "W2", "map_bytes": map_bytes, "js_bytes": js_bytes,
          "config_bytes": config_bytes, "main_bytes": main_bytes, "main_limit_bytes": 4 * 1024 * 1024,
          "total_limit_bytes": 30 * 1024 * 1024, "package_note": "quickstart arithmetic; map may be moved to a subpackage",
          "pass": main_bytes <= 4 * 1024 * 1024}
    (ev / "W2").mkdir(parents=True, exist_ok=True)
    (ev / "W2" / "package.json").write_text(json.dumps(w2, ensure_ascii=False, indent=1), encoding="utf-8")
    if not w2["pass"]:
        hard.append(f"main package arithmetic {main_bytes} > 4 MB")

    brief = (request / "REQUIREMENTS_BRIEF.md").read_text(encoding="utf-8")
    reqs = sorted(set(REQ_RE.findall(brief)))
    cases = json.loads((request / "test_cases.json").read_text(encoding="utf-8"))
    covered = sorted({r for c in cases["cases"] for r in c.get("covers", [])})
    missing = [r for r in reqs if r not in covered]
    extra = [r for r in covered if r not in reqs]
    dangling = []
    for c in cases["cases"]:
        if c.get("check_type") == "external":
            continue
        p = c.get("evidence_path", "")
        if p and not (request / p).exists():
            dangling.append(p)
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
    ids = {"brief_request": request.name, "test_cases": cases.get("request_id"),
           "run_context": run_ctx.get("request_id"), "resolved": resolved.get("request_id")}
    ids_ok = len(set(ids.values())) == 1
    if missing or extra or dangling or not ids_ok:
        hard.append(f"coverage/ids/evidence missing={missing} extra={extra} dangling={dangling} ids={ids}")
    out["coverage"] = {"requirements": reqs, "covered": covered, "missing": missing,
                       "extra": extra, "dangling_evidence": dangling, "ids": ids, "ids_consistent": ids_ok,
                       "resolved_loaded_failures": bad_loaded}

    rep = run_dir / "reproduction.json"
    rep_info = {}
    if rep.exists():
        try:
            rep_info = json.loads(rep.read_text(encoding="utf-8"))
            if not rep_info.get("pass"):
                hard.append(f"reproduction not pass: {rep_info.get('status')}")
        except Exception as e:
            hard.append(f"reproduction.json invalid: {e}")
    else:
        hard.append("missing runs/<run>/reproduction.json")

    manifest_info = {}
    if (candidate / "MANIFEST.json").exists():
        try:
            man = json.loads((candidate / "MANIFEST.json").read_text(encoding="utf-8"))
            files = man.get("files", [])
            bad = []
            for item in files:
                p = candidate / item["path"]
                if not p.exists():
                    bad.append({"path": item["path"], "reason": "missing"})
                elif sha(p) != item.get("sha256"):
                    bad.append({"path": item["path"], "reason": "sha mismatch"})
            manifest_info = {"files": len(files), "bad": bad}
            if bad:
                hard.append(f"manifest binding failures {len(bad)}")
        except Exception as e:
            hard.append(f"MANIFEST.json invalid: {e}")

    out.update({"images": img_info, "w1": w1 if ship.exists() else None, "w2": w2,
                "manifest": manifest_info, "reproduction": rep_info, "hard_failures": hard, "pass": not hard})
    (run_dir / "check_summary.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("CHECK", "PASS" if not hard else "FAIL", "hard_failures", len(hard))
    for h in hard:
        print(" -", h)
    return 0 if not hard else 1


if __name__ == "__main__":
    sys.exit(main())
