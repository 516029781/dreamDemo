#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Compare two blind scoring passes against the frozen producer self-review.

Usage (from the repository root):
    python planning/execution/P0_CALIBRATION/score_calc.py \
        --a scores_reviewer_a.json --b scores_reviewer_b.json \
        --producer delivery/next_cycle/n5/T4/producer_self_review_n5.json

Every score is an integer 0-4 on the anchors in ANCHORS.md. A missing dimension
is a hard error: the contract says a dimension without evidence must be null,
which makes the whole card pending, not something to be filled in later.
"""
import argparse
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
CARDS = ["ENV", "CHAR", "UI", "MIX"]


def load_anchors():
    with io.open(os.path.join(HERE, "ANCHORS.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    return data["anchors"]


def load_scores(path, label):
    with io.open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    scores = raw.get("scores") or raw
    if isinstance(scores, list):
        scores = {s["id"]: s["score"] for s in scores}
    return raw.get("scorer", label), scores


def load_producer(path):
    with io.open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    out = {}
    for card, body in d["cards"].items():
        for dim in body["dimensions"]:
            out[dim["id"]] = dim["score"]
    return out


def card_score(anchors, scores, card):
    dims = [a for a in anchors if a["card"] == card]
    total = sum(a["weight"] * scores[a["id"]] for a in dims)
    return total / 4.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--producer", required=True)
    ap.add_argument("--out", default=os.path.join(HERE, "P0_SCORES.md"))
    args = ap.parse_args()

    anchors = load_anchors()
    name_a, sa = load_scores(args.a, "A")
    name_b, sb = load_scores(args.b, "B")
    sp = load_producer(args.producer)

    missing = []
    for a in anchors:
        for src, s in (("A", sa), ("B", sb)):
            if a["id"] not in s:
                missing.append("%s:%s" % (src, a["id"]))
    if missing:
        raise SystemExit("missing dimensions: %s" % ", ".join(missing))

    rows = []
    for a in anchors:
        i = a["id"]
        va, vb, vp = sa[i], sb[i], sp.get(i)
        rows.append({"card": a["card"], "id": i, "w": a["weight"],
                     "A": va, "B": vb, "P": vp,
                     "ab": abs(va - vb), "ap": abs(va - vp) if vp is not None else None})

    cards = {}
    for c in CARDS:
        cards[c] = {
            "A": round(card_score(anchors, sa, c), 2),
            "B": round(card_score(anchors, sb, c), 2),
            "P": round(card_score(anchors, sp, c), 2) if all(
                a["id"] in sp for a in anchors if a["card"] == c) else None,
        }

    worst = max(abs(cards[c]["A"] - cards[c]["B"]) for c in CARDS)
    worst_p = max(abs(cards[c]["A"] - cards[c]["P"]) for c in CARDS
                  if cards[c]["P"] is not None)
    mean_dim_ab = sum(r["ab"] for r in rows) / len(rows)
    mean_dim_ap = sum(r["ap"] for r in rows if r["ap"] is not None) / max(
        1, sum(1 for r in rows if r["ap"] is not None))

    passed = worst <= 3
    verdict = "PASS" if passed else "FAIL"

    lines = ["# P0 校准结果", "",
             "两名评分者使用同一份 ANCHORS.md 与同一批帧，互不可见；制作侧分数取自冻结的 n5 自评。", "",
             "## 逐卡", "",
             "| 卡片 | 评分者 A | 评分者 B | 制作侧 | A−B | A−制作 | 判定 |",
             "|---|---:|---:|---:|---:|---:|---|"]
    for c in CARDS:
        d = cards[c]
        gap = abs(d["A"] - d["B"])
        gp = abs(d["A"] - d["P"]) if d["P"] is not None else None
        lines.append("| %s | %.2f | %.2f | %s | %.2f | %s | %s |" % (
            c, d["A"], d["B"], "%.2f" % d["P"] if d["P"] is not None else "—",
            gap, "%.2f" % gp if gp is not None else "—",
            "一致" if gap <= 3 else "超差"))
    lines += ["", "## 逐维", "",
              "| 卡片 | 维度 | 权重 | A | B | 制作侧 | |A−B| | |A−制作| |",
              "|---|---|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        lines.append("| %s | %s | %d | %d | %d | %s | %d | %s |" % (
            r["card"], r["id"], r["w"], r["A"], r["B"],
            r["P"] if r["P"] is not None else "—", r["ab"],
            r["ap"] if r["ap"] is not None else "—"))
    lines += ["", "## 结论", "",
              "- 两名评分者的最大逐卡差：**%.2f 分**（阈值 3）→ %s" % (worst, verdict),
              "- 逐维平均差：%.2f 分；与制作侧逐维平均差：%.2f 分" % (mean_dim_ab, mean_dim_ap),
              "- 与制作侧的最大逐卡差：%.2f 分" % worst_p,
              "- 差异最大的维度：%s" % ", ".join(
                  "%s(%+d)" % (r["id"], r["A"] - r["B"])
                  for r in sorted(rows, key=lambda x: -x["ab"])[:5]),
              ""]
    with io.open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))

    print("\n".join(lines[-8:]))
    print("\nwritten", args.out)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
