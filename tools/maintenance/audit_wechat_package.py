#!/usr/bin/env python3
"""Measure a Cocos WeChat Mini Game build without changing its contents."""

import argparse
import json
from pathlib import Path

MIB = 1024 * 1024


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build", type=Path, help="Directory containing game.json")
    parser.add_argument("--main-limit-mib", type=float, default=4.0)
    parser.add_argument("--output", type=Path, help="Write the same report as JSON")
    args = parser.parse_args()

    build = args.build.resolve()
    game = json.loads((build / "game.json").read_text(encoding="utf-8-sig"))
    packages = game.get("subpackages", game.get("subPackages", []))
    roots = {}
    for item in packages:
        root = str(item["root"]).replace("\\", "/").strip("/")
        if not root or root == ".." or root.startswith("../"):
            raise ValueError("Invalid subpackage root: " + repr(root))
        roots[root] = item.get("name", root)

    totals = {"main": 0, "remote": 0}
    counts = {"main": 0, "remote": 0}
    for name in roots.values():
        totals["subpackage:" + name] = 0
        counts["subpackage:" + name] = 0
    largest = []
    for path in build.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(build).as_posix()
        if rel == "remote" or rel.startswith("remote/"):
            bucket = "remote"
        else:
            bucket = "main"
            for root, name in roots.items():
                if rel == root or rel.startswith(root + "/"):
                    bucket = "subpackage:" + name
                    break
        size = path.stat().st_size
        totals[bucket] += size
        counts[bucket] += 1
        largest.append({"path": rel, "bytes": size, "bucket": bucket})

    largest.sort(key=lambda row: row["bytes"], reverse=True)
    report = {
        "build": str(build),
        "main_limit_bytes": int(args.main_limit_mib * MIB),
        "main_pass": totals["main"] <= int(args.main_limit_mib * MIB),
        "bytes_by_bucket": totals,
        "files_by_bucket": counts,
        "largest_files": largest[:15],
        "note": "Raw build directory bytes; final platform acceptance requires WeChat DevTools.",
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    print(rendered, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    return 0 if report["main_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
