"""Create the single formal n5 build and pin its identity.

n4 failed P0-2 because bindings and Q results were matched to "the newest
build report on disk". This wrapper builds once, then writes an explicit pin
(delivery/next_cycle/n5/performance/formal_build.json) recording the build
report path, build_id, log path and the SHAs of every input that shaped the
build. Capture, Q and binding steps must read the pin, never a glob.

Refuses to overwrite an existing pin unless --force, so a rebuild is always a
deliberate, logged act.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIN = os.path.join(ROOT, "delivery/next_cycle/n5/performance/formal_build.json")
LOGS = os.path.join(ROOT, "delivery/next_cycle/n5/performance/logs")
BUILD_SCRIPT = os.path.join(ROOT, "tools/cocos/build_web_desktop.py")
PROJECT = os.path.join(ROOT, "demo_n5")
CONFIG = os.path.join(ROOT, "demo_n5/build-config-web-desktop.json")
EXPECT = os.path.join(ROOT, "demo_n5/build/web-desktop/index.html")
PYTHON = r"C:/Users/tt/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe"

# Inputs whose content decides what the build looks like.
INPUT_FILES = [
    "demo_n5/assets/scripts/CourtyardBootstrap.ts",
    "demo_n5/assets/resources/models/MAP001_courtyard.glb",
    "demo_n5/assets/resources/ui/paper_panel_wash.png",
    "demo_n5/assets/resources/textures/tex_tree_shadow.png",
    "demo_n5/build-config-web-desktop.json",
]
INPUT_TEXTURES = "demo_n5/assets/resources/textures"


def sha(path):
    full = path if os.path.isabs(path) else os.path.join(ROOT, path)
    if not os.path.isfile(full):
        return None
    h = hashlib.sha256()
    with open(full, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_sha(base_rel):
    """Hash a directory's file list + contents so texture swaps are visible."""
    base = os.path.join(ROOT, base_rel)
    if not os.path.isdir(base):
        return None
    h = hashlib.sha256()
    for name in sorted(os.listdir(base)):
        p = os.path.join(base, name)
        if os.path.isfile(p):
            h.update(name.encode("utf-8"))
            h.update((sha(p) or "").encode("ascii"))
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--reason", default="")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if os.path.isfile(PIN) and not args.force:
        raise SystemExit("formal build already pinned at %s; pass --force to rebuild "
                         "(this invalidates every capture and Q result)" % PIN)
    if not os.path.isfile(os.path.join(ROOT, "demo_n5/assets/resources/models/MAP001_courtyard.glb")):
        raise SystemExit("demo_n5 map GLB missing; build MAP001 first")

    os.makedirs(LOGS, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = os.path.join(LOGS, "cocos.%s.%s.log" % (args.run_id, stamp))
    cmd = [PYTHON, "-X", "utf8", BUILD_SCRIPT,
           "--project", PROJECT, "--config", CONFIG,
           "--log", log_path, "--expect-output", EXPECT]
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    print((proc.stdout or "").strip()[-600:])
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or "")
        raise SystemExit("cocos build wrapper failed with %d" % proc.returncode)

    # The wrapper prints a JSON line with the report path.
    report_path = None
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if line.startswith("{") and "output" in line:
            try:
                report_path = json.loads(line)["output"]
            except Exception:
                pass
    if not report_path or not os.path.isfile(report_path):
        raise SystemExit("could not resolve build report from wrapper output")

    report = json.loads(open(report_path, encoding="utf-8-sig").read())
    build_id = "cocos-web-desktop-" + os.path.splitext(os.path.basename(report_path))[0]
    pin = {
        "candidate_id": "candidate_n5",
        "run_id": args.run_id,
        "reason": args.reason,
        "pinned_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "started_at_utc": started,
        "build_id": build_id,
        # Bindings reject absolute/drive paths, so every recorded path is
        # repo-relative. relpath is used because stripping dirname(ROOT) leaves
        # the repo folder name on the path.
        "build_report": os.path.relpath(report_path, ROOT).replace("\\", "/"),
        "build_report_json": report,
        "build_log": os.path.relpath(log_path, ROOT).replace("\\", "/"),
        "build_log_sha256": sha(log_path),
        "output_index_sha256": sha(EXPECT),
        "inputs": {p: sha(p) for p in INPUT_FILES},
        "texture_dir_sha256": tree_sha(INPUT_TEXTURES),
    }
    os.makedirs(os.path.dirname(PIN), exist_ok=True)
    with open(PIN, "w", encoding="utf-8") as fh:
        json.dump(pin, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(json.dumps({"pinned": pin["build_id"], "report": pin["build_report"]},
                     ensure_ascii=False))
    # Every build leaves Blender .blend1 autosaves and a fresh layer of
    # git-lfs scratch behind. Sweeping them here keeps the disk from filling
    # silently between work packages; it only touches regenerable files.
    try:
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import clean_workspace
        freed, removed = clean_workspace.apply_clean(keep_builds=True)
        print(json.dumps({"cleanup": {"removed": removed, "freed_mb": round(freed / 1048576, 1)}},
                         ensure_ascii=False))
    except Exception as exc:  # noqa: BLE001 - housekeeping must never fail a build
        print("cleanup skipped: %s" % exc)


if __name__ == "__main__":
    main()
