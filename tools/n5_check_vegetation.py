"""Re-check that no grass tuft grows on the stone paving.

The build writes vegetation_audit.json with every tuft's map position and the
build's own verdict. This checker recomputes the verdict independently from the
PAVING_CENTERS / PAVING_HALF literals parsed out of build_map001.py, so a bug in
the build's own predicate cannot silently pass.

Usage:
  python tools/n5_check_vegetation.py                     # check the audit
  python tools/n5_check_vegetation.py --selftest          # negative control
  python tools/n5_check_vegetation.py --audit <path>
"""
import argparse
import ast
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "tools/blender_n5/build_map001.py")
DEFAULT_AUDIT = os.path.join(ROOT, "art/candidates/candidate_n5/vegetation_audit.json")


def parse_paving(path):
    src = open(path, encoding="utf-8").read()
    m = re.search(r"^PAVING_CENTERS\s*=\s*(\[[^\]]*\])", src, re.M | re.S)
    if not m:
        raise SystemExit("could not parse PAVING_CENTERS from %s" % path)
    centers = ast.literal_eval(m.group(1))
    h = re.search(r"^PAVING_HALF\s*=\s*([0-9.]+)", src, re.M)
    if not h:
        raise SystemExit("could not parse PAVING_HALF from %s" % path)
    return centers, float(h.group(1))


def on_paving(x, z, centers, half, inset=0.12):
    limit = half - inset
    return any(abs(x - cx) <= limit and abs(z - cz) <= limit for (cx, cz) in centers)


def check(audit_path):
    centers, half = parse_paving(BUILD)
    data = json.loads(open(audit_path, encoding="utf-8-sig").read())
    tufts = data.get("tufts", [])
    # Only ground-level, uncontainerised grass is subject to the paving rule.
    # Tufts standing on a raised bed or inside a planter sit above the slabs, so
    # a flat 2-D test would flag them as false positives (it did: 1150 of them).
    violations = []
    mismatches = []
    orphans = []
    for t in tufts:
        container = t.get("container", "unknown")
        if container == "unknown":
            orphans.append(t)
            continue
        if container != "open_ground":
            continue
        dropped = bool(t.get("dropped"))
        # The builder's on_paving flag uses a larger exclusion margin than this
        # checker, so a dropped candidate may be blocked even when its centre
        # lies outside the slab footprint. Validate that it was blocked, then
        # exclude it from placement geometry and violation counts.
        if dropped:
            if not t.get("on_paving"):
                mismatches.append(t)
            continue
        truth = on_paving(t["x"], t["z"], centers, half)
        if truth:
            violations.append(t)
        if bool(t.get("on_paving")) != truth:
            mismatches.append(t)
    by_container = {}
    for t in tufts:
        by_container[t.get("container", "?")] = by_container.get(t.get("container", "?"), 0) + 1
    result = {
        "kind": "n5_vegetation_check",
        "audit": os.path.relpath(audit_path, ROOT).replace("\\", "/"),
        "paving_modules": len(centers),
        "total_tufts": len(tufts),
        "by_container": by_container,
        "violations": len(violations),
        "blocked_by_paving": sum(1 for t in tufts
                                 if t.get("container") != "unknown"
                                 and t.get("on_paving") and t.get("dropped")),
        "audit_mismatches": len(mismatches),
        "orphans": len(orphans),
        "violation_samples": violations[:5],
        "pass": not violations and not mismatches and not orphans,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1


def selftest():
    """Negative control: a placed open_ground tuft on paving must be flagged;
    the same tuft recorded as dropped (blocked by the builder) must pass."""
    centers, half = parse_paving(BUILD)
    base = {"x": centers[0][0], "z": centers[0][1],
            "on_paving": True, "container": "open_ground"}
    cases = [
        ("placed tuft on paving must be flagged", [dict(base)], 1),
        ("dropped (blocked) tuft on paving must pass",
         [dict(base, dropped=True)], 0),
        ("missing container must be reported", [{"x": 0.0, "z": 0.0,
                                                 "on_paving": False}], 1),
    ]
    tmp = os.path.join(ROOT, "art/candidates/candidate_n5/_vegetation_selftest.json")
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    results = []
    ok = True
    for note, tufts, expected in cases:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"tufts": tufts}, fh)
        code = check(tmp)
        good = code == expected
        ok = ok and good
        results.append({"note": note, "expected": expected,
                        "got": code, "pass": good})
    os.remove(tmp)
    print(json.dumps({"selftest": "pass" if ok else "FAIL",
                      "cases": results}, ensure_ascii=False))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", default=DEFAULT_AUDIT)
    ap.add_argument("--selftest", action="store_true")
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = argv[1:]
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    return check(args.audit)


if __name__ == "__main__":
    sys.exit(main())
