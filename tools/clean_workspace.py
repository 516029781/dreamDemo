#!/usr/bin/env python3
"""Reclaim disk space from regenerable build scratch, then report what is stale.

Why this exists: regenerable build outputs and autosaves can fill the workspace.
Git LFS temporary files are reported separately but never deleted here because
another Git process may still be writing them.

Two kinds of content, handled differently:

  clean   - regenerable scratch. Deleted with --apply, reported otherwise.
            Nothing here is evidence: caches, autosaves, extracted installers.
  stale   - superseded artefacts (old candidates, old source packs). These are
            the project's audit trail, so they are only *reported*, never
            deleted by this tool. Removing them is a human decision.

Usage:
  python tools/clean_workspace.py                 # dry run, prints a report
  python tools/clean_workspace.py --apply         # delete the clean category
  python tools/clean_workspace.py --apply --json  # machine-readable
  python tools/clean_workspace.py --keep-builds   # also protect demo*/build
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_PROJECT = "demo_n5"


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return "%.1f %s" % (n, unit) if unit != "B" else "%d B" % n
        n /= 1024.0


def dir_size(path):
    total = 0
    for base, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(base, name))
            except OSError:
                pass
    return total


def tracked_paths():
    """Repo-relative paths git already owns. This tool must never delete one.

    A tracked .blend1 is a mistake in the repository, not scratch, and removing
    it is a `git rm` decision for a human. Guarding here means an over-broad
    pattern can only ever take untracked files.
    """
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z"],
                             capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return set()
    return {p for p in out.decode("utf-8", "replace").split("\0") if p}


def is_tracked(path, tracked):
    """True when `path` is tracked, or is a directory containing tracked files."""
    relative = path.relative_to(ROOT).as_posix()
    if path.is_dir():
        prefix = relative + "/"
        return any(item.startswith(prefix) for item in tracked)
    return relative in tracked


def remove(path):
    """Delete a file or tree, returning the bytes that actually went away."""
    if not path.exists():
        return 0
    root = ROOT.resolve()
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"refusing path outside workspace: {path}") from exc
    if not relative.parts or relative.parts[0] == ".git" or path.is_symlink():
        raise ValueError(f"refusing protected or linked path: {path}")
    if path.is_dir():
        size = dir_size(path)
        shutil.rmtree(path)
        return size
    try:
        size = path.stat().st_size
        path.unlink()
        return size
    except OSError:
        return 0


# --------------------------------------------------------------------------
# clean: regenerable scratch
# --------------------------------------------------------------------------

def clean_targets(keep_builds=False, tracked=None):
    """Yield (group, path) for regenerable scratch only.

    Anything git tracks is skipped: a tracked `.blend1` is a repository
    mistake, and removing it is a `git rm` decision a human has to make.
    """
    if tracked is None:
        tracked = set()

    def safe(group, path):
        return None if is_tracked(path, tracked) else (group, path)

    for blend1 in ROOT.rglob("*.blend1"):
        if ".git" in blend1.parts:
            continue
        if "candidate_n5" in blend1.parts:
            continue  # keep the active candidate's emergency Blender backup
        item = safe("blender-backup", blend1)
        if item:
            yield item

    for downloads in (ROOT / "tools" / "cocos" / "downloads", ROOT / ".tools" / "blender"):
        if not downloads.is_dir():
            continue
        for archive in downloads.glob("*.zip"):
            item = safe("installer-archive", archive)
            if item:
                yield item

    for cache in list(ROOT.glob("demo*/library")) + list(ROOT.glob("demo*/temp")):
        if cache.parent.name == ACTIVE_PROJECT:
            continue  # re-importing the live project costs minutes; keep it
        item = safe("cocos-cache", cache)
        if item:
            yield item

    if not keep_builds:
        for build in ROOT.glob("demo*/build"):
            if build.parent.name == ACTIVE_PROJECT:
                continue
            item = safe("cocos-build", build)
            if item:
                yield item

    for pycache in ROOT.rglob("__pycache__"):
        if ".git" in pycache.parts:
            continue
        item = safe("pycache", pycache)
        if item:
            yield item


def collect_clean(keep_builds=False):
    groups = {}
    tracked = tracked_paths()
    for group, path in clean_targets(keep_builds, tracked):
        size = dir_size(path) if path.is_dir() else path.stat().st_size
        groups.setdefault(group, []).append({"path": str(path.relative_to(ROOT)), "bytes": size})
    return groups


def apply_clean(keep_builds=False):
    freed = 0
    removed = 0
    tracked = tracked_paths()
    for _group, path in list(clean_targets(keep_builds, tracked)):
        got = remove(path)
        if got:
            freed += got
            removed += 1
    return freed, removed


# --------------------------------------------------------------------------
# stale: superseded artefacts, reported only
# --------------------------------------------------------------------------

STALE_RULES = (
    ("superseded-candidate", "art/candidates/candidate_n3"),
    ("superseded-evidence", "delivery/next_cycle/n3"),
    ("superseded-demo", "demo_n3"),
)


def collect_stale():
    rows = []
    for group, relative in STALE_RULES:
        path = ROOT / relative
        if path.exists():
            rows.append({"group": group, "path": relative, "bytes": dir_size(path)})

    delivery = ROOT / "delivery"
    if delivery.is_dir():
        for archive in sorted(delivery.glob("*.zip")):
            rows.append({"group": "source-pack-archive",
                         "path": str(archive.relative_to(ROOT)),
                         "bytes": archive.stat().st_size})
    rows.sort(key=lambda r: -r["bytes"])
    return rows


# --------------------------------------------------------------------------

def report(keep_builds=False, as_json=False):
    clean = collect_clean(keep_builds)
    stale = collect_stale()
    clean_total = sum(item["bytes"] for rows in clean.values() for item in rows)
    stale_total = sum(row["bytes"] for row in stale)

    result = {
        "clean": {group: {"files": len(rows), "bytes": sum(r["bytes"] for r in rows),
                          "items": sorted(rows, key=lambda r: -r["bytes"])[:8]}
                  for group, rows in sorted(clean.items())},
        "clean_total_bytes": clean_total,
        "stale": stale,
        "stale_total_bytes": stale_total,
    }
    lfs_tmp = ROOT / ".git" / "lfs" / "tmp"
    if lfs_tmp.is_dir():
        result["git_lfs_tmp_report_only_bytes"] = dir_size(lfs_tmp)
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result

    print("可清理（可再生，--apply 删除）")
    if not clean:
        print("  无")
    for group, rows in sorted(clean.items(), key=lambda kv: -sum(r["bytes"] for r in kv[1])):
        total = sum(r["bytes"] for r in rows)
        print("  %-18s %5d 项  %10s" % (group, len(rows), human(total)))
        for row in sorted(rows, key=lambda r: -r["bytes"])[:3]:
            print("      %10s  %s" % (human(row["bytes"]), row["path"]))
    print("  合计 %s" % human(clean_total))

    if result.get("git_lfs_tmp_report_only_bytes"):
        print("  Git LFS tmp（只报告，绝不自动删除）: %s" %
              human(result["git_lfs_tmp_report_only_bytes"]))

    print("\n过时但仍保留（审计链，请人工决定）")
    if not stale:
        print("  无")
    for row in stale[:10]:
        print("  %-22s %10s  %s" % (row["group"], human(row["bytes"]), row["path"]))
    print("  合计 %s" % human(stale_total))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="delete the clean category")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--keep-builds", action="store_true",
                        help="keep demo*/build for superseded projects")
    parser.add_argument("--quiet", action="store_true", help="only print the summary line")
    args = parser.parse_args(argv)

    if args.apply:
        freed, removed = apply_clean(args.keep_builds)
        if args.json:
            print(json.dumps({"applied": True, "removed": removed, "freed_bytes": freed}))
        elif args.quiet:
            print("cleanup: removed %d, freed %s" % (removed, human(freed)))
        else:
            print("已删除 %d 项，释放 %s" % (removed, human(freed)))
            report(args.keep_builds)
        return 0

    report(args.keep_builds, args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
