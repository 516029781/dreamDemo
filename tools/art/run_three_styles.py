"""Build the same courtyard in three look directions and shoot each one.

o = shipped procedural look (cards + tiling detail maps)
c = low-poly cartoon (solid blobs, flat colour, no maps)
r = realistic (alpha-cut leaf atlas on the cards, warmer grade)

Each variant is a full Blender rebuild + engine build + formal capture, so the
three images are comparable: same camera, same composition, same UI state.

Usage: python tools/art/run_three_styles.py [O C R]
"""

import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BENCH = os.path.join(ROOT, "planning", "art", "THREE_STYLES.json")
BLENDER = os.environ.get("P1_BLENDER_EXE") or os.path.join(
    os.path.expanduser("~"), ".cache", "blender", "5.2.3", "blender-5.2.3-windows-x64", "blender.exe"
)
MAP_SCRIPT = os.path.join("tools", "blender_n5", "build_map001.py")
SHOTS = os.path.join("delivery", "next_cycle", "n5", "_variant_shots.js")
ART_GLB = os.path.join(ROOT, "art", "candidates", "candidate_n5", "source", "layout",
                       "MAP001_courtyard.glb")

sys.path.insert(0, os.path.join(ROOT, "tools", "art"))
from run_art_variants import glb_stats, run  # noqa: E402


def log(msg):
    print("[styles] " + msg, flush=True)


def variant_env(cfg):
    env = dict(os.environ)
    palette = ";".join("%s=%s" % (k, v) for k, v in cfg["palette"].items())
    env.update({
        "N5_ART_VARIANT": "style-" + cfg["style"],
        "N5_STYLE": cfg["style"],
        "N5_LEAF_SHAPE": str(cfg["leaf_shape"]),
        "N5_LEAF_FOLD": str(cfg["leaf_fold"]),
        "N5_LEAF_SCALE": str(cfg["leaf_scale"]),
        "N5_LEAF_COUNT_SCALE": str(cfg["leaf_count_scale"]),
        "N5_GRASS_BLADE_KEEP": str(cfg["grass_keep"]),
        "N5_GRASS_RING_BLADE_KEEP": str(cfg["grass_ring_keep"]),
        "N5_GRASS_WIDTH_SCALE": str(cfg["grass_width"]),
        "N5_GRASS_HEIGHT_SCALE": str(cfg["grass_height"]),
        "N5_GRASS_COUNT_SCALE": str(cfg["grass_count_scale"]),
        "N5_PAVING_UNIFY": str(cfg["paving_unify"]),
        "N5_PAVING_JOINT_SCALE": str(cfg["paving_joint_scale"]),
        "N5_PAVING_CRACKS": str(cfg["paving_cracks"]),
        "N5_PALETTE": palette,
    })
    if "blob_keep" in cfg:
        env["N5_BLOB_KEEP"] = str(cfg["blob_keep"])
        env["N5_BLOB_RADIUS_SCALE"] = str(cfg["blob_radius_scale"])
        env["N5_BLOB_SUBDIV"] = str(cfg["blob_subdiv"])
    for noisy in ("PYTHONHOME",):
        env.pop(noisy, None)
    return env


def build(tag, cfg):
    env = variant_env(cfg)
    res = {"tag": tag, "label": cfg["label"], "url_style": cfg["url_style"], "steps": {}}
    before = os.path.getmtime(ART_GLB) if os.path.exists(ART_GLB) else 0

    code, out, dt = run([BLENDER, "--background", "--factory-startup", "--python", MAP_SCRIPT],
                        env, 2400, tag + " blender")
    res["steps"]["blender"] = {"exit": code, "seconds": round(dt, 1)}
    if code != 0 or not re.findall(r"GLB_WRITTEN=(\S+)", out):
        res["error"] = "blender failed"
        res["tail"] = "\n".join(out.strip().splitlines()[-12:])
        log("FAILED " + tag + "\n" + res["tail"])
        return res
    if os.path.getmtime(ART_GLB) <= before:
        res["error"] = "GLB not rewritten"
        return res
    res["glb"] = glb_stats(ART_GLB)
    res["skipped_planting"] = len(set(re.findall(r"PLANTING_SKIP (\S+)", out)))

    code, out, dt = run([sys.executable, os.path.join("tools", "sync_map_glb.py"), "--apply"],
                        env, 900, tag + " sync")
    res["steps"]["sync"] = {"exit": code, "seconds": round(dt, 1)}
    if code != 0:
        res["error"] = "sync failed"
        res["tail"] = "\n".join(out.strip().splitlines()[-8:])
        return res

    code, out, dt = run([sys.executable, os.path.join("tools", "n5_build.py"),
                         "--run-id", "style-" + tag.lower(),
                         "--reason", "style bench " + tag, "--force"],
                        env, 3000, tag + " engine")
    res["steps"]["engine"] = {"exit": code, "seconds": round(dt, 1),
                              "tail": out.strip().splitlines()[-2:]}
    # n5_build's exit code is polluted by a safe-delete confirmation prompt for
    # __pycache__; the pinned report is the real signal.
    if code != 0 and '"pinned"' not in out:
        res["error"] = "engine build failed"
        return res

    shot_env = dict(env)
    shot_env["N5_SHOT_OUT"] = os.path.join(ROOT, "delivery", "next_cycle", "n5", "T5",
                                           "styles", tag)
    code, out, dt = run(["node", os.path.join(SHOTS), tag, BENCH], shot_env, 900, tag + " shot")
    res["steps"]["shot"] = {"exit": code, "seconds": round(dt, 1),
                            "tail": out.strip().splitlines()[-1:]}
    if code != 0:
        res["error"] = "shot failed"
        res["tail"] = "\n".join(out.strip().splitlines()[-8:])
    return res


def main():
    tags = [t.upper() for t in sys.argv[1:]] or ["O", "C", "R"]
    bench = json.load(open(BENCH, encoding="utf-8"))["variants"]
    results, t0 = [], time.time()
    for tag in tags:
        if tag not in bench:
            log("skip unknown " + tag)
            continue
        log("=== %s: %s ===" % (tag, bench[tag]["label"]))
        results.append(build(tag, bench[tag]))

    stamp = time.strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(ROOT, "delivery", "performance", "three_styles_%s.json" % stamp)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "total_seconds": round(time.time() - t0, 1),
                   "variants": results}, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    log("report " + out_path)
    failed = [r["tag"] for r in results if r.get("error")]
    log("done: %d ok, %d failed" % (len(results) - len(failed), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
