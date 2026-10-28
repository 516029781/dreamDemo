"""Score the look-dev variants against the reference with the same metrics.

Runs tools/art/image_metrics.js for every built variant plus the reference,
then applies the pass/fail thresholds from the plan (appendix C5).

Usage: python tools/art/check_variants.py [A B C]
"""

import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REF = "reference/_raw_screenshots/P1/t015s.jpg"
SHOTS = "delivery/next_cycle/n5/T5/variants"
METRICS = os.path.join(ROOT, "tools", "art", "image_metrics.js")
OUT_JSON = os.path.join(ROOT, "delivery", "performance", "art_variants_metrics.json")

# Same boxes as the baseline measurement: the variants share one camera.
BOXES = {
    "tree": (470, 80, 360, 250),
    "grass": (500, 340, 320, 200),
    "paving": (400, 480, 480, 200),
}
REF_BOXES = {
    "tree": (562, 40, 700, 340),
    "grass": (290, 150, 300, 120),
    "paving": (620, 450, 700, 180),
}

# (region, metric, comparison, threshold)
THRESHOLDS = [
    ("tree", "edgeDensity", "<=", 18),
    ("tree", "lumP50", ">=", 72),
    ("tree", "satMean", "<=", 42),
    ("grass", "edgeDensity", "<=", 22),
    ("grass", "satMean", ">=", 38),
    ("grass", "bandLight", "<=", 30),
    ("paving", "jointsPerRow", "<=", 24),
    ("paving", "jointContrast", "<=", 33),
]


def run(tags):
    args = [METRICS, OUT_JSON]
    jobs = []
    for region, box in REF_BOXES.items():
        jobs.append("参考-%s|%s|%s|%s" % (region, REF, region, ",".join(map(str, box))))
    for tag in tags:
        path = "%s/variant_%s_no_ui.png" % (SHOTS, tag)
        if not os.path.exists(os.path.join(ROOT, path)):
            continue
        for region, box in BOXES.items():
            jobs.append("%s-%s|%s|%s|%s" % (tag, region, path, region,
                                            ",".join(map(str, box))))
    subprocess.run(["node"] + args + jobs, cwd=ROOT, check=True,
                   stdout=subprocess.DEVNULL)
    with open(os.path.join(ROOT, OUT_JSON), encoding="utf-8") as fh:
        return json.load(fh)["runs"]


def joints_per_row(run_item, box):
    """jointSamples counts joints over sampled rows (every 2nd row)."""
    if not run_item.get("jointSamples"):
        return None
    rows = box[3] // 2
    return round(run_item["jointSamples"] / rows, 1)


def main():
    tags = sys.argv[1:] or ["A", "B", "C"]
    runs = run(tags)
    by_key = {}
    for r in runs:
        label = r["label"]
        by_key[label] = r

    ref = {}
    for region, box in REF_BOXES.items():
        ref[region] = by_key.get("参考-%s" % region)
        ref[region]["jointsPerRow"] = joints_per_row(ref[region], box)

    print("region  metric          reference   " + "   ".join(tags) + "     thresholds")
    failures = {}
    for region, metric, op, thr in THRESHOLDS:
        rv = ref[region].get(metric)
        cells = []
        for tag in tags:
            item = by_key.get("%s-%s" % (tag, region))
            if not item:
                cells.append("--")
                continue
            v = item.get(metric)
            if metric == "jointsPerRow":
                v = joints_per_row(item, BOXES[region])
            ok = (v <= thr) if op == "<=" else (v >= thr)
            cells.append("%s %s" % (round(v, 1) if v is not None else "--",
                                    "ok" if ok else "X"))
            if not ok:
                failures.setdefault(tag, []).append("%s.%s" % (region, metric))
        print("%-7s %-15s %-11s %s   %s %s" % (
            region, metric, round(rv, 1) if rv is not None else "--",
            "   ".join(cells), op, thr))

    print()
    for tag in tags:
        bad = failures.get(tag, [])
        print("%s: %s" % (tag, "PASS all 8" if not bad else "FAIL " + ", ".join(bad)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
