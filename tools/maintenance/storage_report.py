"""Read-only, one-pass storage report for this workspace."""

from __future__ import annotations

import argparse
import heapq
import json
import os
from collections import Counter
from pathlib import Path


def scan(root: Path, largest_count: int = 40) -> dict:
    root = root.resolve()
    sizes: Counter[str] = Counter()
    counts: Counter[str] = Counter()
    largest: list[tuple[int, str]] = []
    errors: list[str] = []
    total = 0
    file_count = 0
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(Path(entry.path))
                        elif entry.is_file(follow_symlinks=False):
                            size = entry.stat(follow_symlinks=False).st_size
                            relative = Path(entry.path).relative_to(root)
                            parts = relative.parts
                            total += size
                            file_count += 1
                            for depth in (1, 2, 3):
                                if len(parts) >= depth:
                                    key = "/".join(parts[:depth])
                                    sizes[key] += size
                                    counts[key] += 1
                            item = (size, relative.as_posix())
                            if len(largest) < largest_count:
                                heapq.heappush(largest, item)
                            elif size > largest[0][0]:
                                heapq.heapreplace(largest, item)
                    except OSError as exc:
                        errors.append(f"{entry.path}: {exc}")
        except OSError as exc:
            errors.append(f"{directory}: {exc}")
    return {
        "root": str(root),
        "total_bytes": total,
        "total_gib": round(total / 1024**3, 3),
        "file_count": file_count,
        "groups": [
            {"path": key, "bytes": size, "gib": round(size / 1024**3, 3), "files": counts[key]}
            for key, size in sizes.most_common()
        ],
        "largest_files": [
            {"path": path, "bytes": size, "mib": round(size / 1024**2, 1)}
            for size, path in sorted(largest, reverse=True)
        ],
        "errors": errors[:20],
        "error_count": len(errors),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--depth", type=int, choices=(1, 2, 3), default=2)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = scan(args.root)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    print(f"TOTAL {report['total_gib']:.3f} GiB, {report['file_count']} files; errors={report['error_count']}")
    for row in (r for r in report["groups"] if len(Path(r["path"]).parts) == args.depth):
        if args.limit <= 0:
            break
        print(f"{row['gib']:8.3f} GiB {row['files']:7} {row['path']}")
        args.limit -= 1
    print("LARGEST FILES")
    for row in report["largest_files"][:20]:
        print(f"{row['mib']:8.1f} MiB {row['path']}")


if __name__ == "__main__":
    main()
