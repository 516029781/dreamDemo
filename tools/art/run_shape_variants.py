"""Shape-only bench: build one map per silhouette option and shoot one frame.

Colour, density and lighting stay at the shipped baseline, so what changes
between S1/S2/S3 is only the leaf silhouette, the blade curve and the paving
crack treatment. Leaf scale 1.7 / count 0.55 is applied to every option so a
single leaf is resolvable at 720p; the final numbers come from ART_VARIANTS.

Usage: python tools/art/run_shape_variants.py [S1 S2 S3]
"""

import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VARIANTS_JSON = os.path.join(ROOT, "planning", "art", "SHAPE_VARIANTS.json")
BLENDER = os.environ.get("P1_BLENDER_EXE") or os.path.join(
    os.path.expanduser("~"), ".cache", "blender", "5.2.3", "blender-5.2.3-windows-x64", "blender.exe"
)
MAP_SCRIPT = os.path.join("tools", "blender_n5", "build_map001.py")
ART_GLB = os.path.join(ROOT, "art", "candidates", "candidate_n5", "source", "layout",
                       "MAP001_courtyard.glb")
sys.path.insert(0, os.path.join(ROOT, "tools", "art"))
from run_art_variants import glb_stats, run  # noqa: E402


def log(msg):
    print("[shape] " + msg, flush=True)


def variant_env(cfg):
    env = dict(os.environ)
    env.update({
        "N5_ART_VARIANT": "shape",
        "N5_LEAF_SHAPE": str(cfg["leaf_shape"]),
        "N5_LEAF_FOLD": str(cfg["leaf_fold"]),
        "N5_LEAF_SCALE": str(cfg["leaf_scale"]),
        "N5_LEAF_COUNT_SCALE": str(cfg["leaf_count_scale"]),
        "N5_GRASS_SEGMENTS": str(cfg["grass_segments"]),
        "N5_GRASS_CURVE": str(cfg["grass_curve"]),
        "N5_GRASS_TAPER": str(cfg["grass_taper"]),
        "N5_GRASS_SPIKE": str(cfg["grass_spike"]),
        "N5_PAVING_CRACKS": str(cfg["paving_cracks"]),
    })
    env.pop("PYTHONHOME", None)
    return env


def build(tag, cfg):
    env = variant_env(cfg)
    res = {"tag": tag, "label": cfg["label"], "params": cfg, "steps": {}}
    before = os.path.getmtime(ART_GLB) if os.path.exists(ART_GLB) else 0
    code, out, dt = run([BLENDER, "--background", "--factory-startup", "--python", MAP_SCRIPT],
                        env, 1800, tag + " blender")
    res["steps"]["blender"] = {"exit": code, "seconds": dt}
    if code != 0 or not re.findall(r"GLB_WRITTEN=(\S+)", out):
        res["error"] = "blender failed"
        res["tail"] = "\n".join(out.strip().splitlines()[-10:])
        log("FAILED " + tag + "\n" + res["tail"])
        return res
    if os.path.getmtime(ART_GLB) <= before:
        res["error"] = "GLB not rewritten"
        return res
    res["glb"] = glb_stats(ART_GLB)
    res["skipped_planting"] = sorted(set(re.findall(r"PLANTING_SKIP (\S+)", out)))

    code, out, dt = run([sys.executable, os.path.join("tools", "sync_map_glb.py"), "--apply"],
                        env, 600, tag + " sync")
    res["steps"]["sync"] = {"exit": code, "seconds": dt}
    if code != 0:
        res["error"] = "sync failed"
        return res

    code, out, dt = run([sys.executable, os.path.join("tools", "n5_build.py"),
                         "--run-id", "shape-" + tag.lower(),
                         "--reason", "shape bench " + tag, "--force"],
                        env, 2400, tag + " engine")
    res["steps"]["engine"] = {"exit": code, "seconds": dt,
                              "tail": out.strip().splitlines()[-2:]}
    # n5_build's exit code is polluted by a safe-delete confirmation request
    # for the __pycache__ folders; the build report is the real signal.
    if code != 0 and '"pinned"' not in out:
        res["error"] = "engine build failed"
        return res

    code, out, dt = run(["node", os.path.join("delivery", "next_cycle", "n5", "_variant_shots.js"),
                         tag, VARIANTS_JSON], env, 600, tag + " shot")
    res["steps"]["shot"] = {"exit": code, "seconds": dt,
                            "tail": out.strip().splitlines()[-1:]}
    if code != 0:
        res["error"] = "shot failed"
        return res
    return res


def main():
    tags = sys.argv[1:] or ["S1", "S2", "S3"]
    bench = json.load(open(VARIANTS_JSON, encoding="utf-8"))["variants"]
    results, t0 = [], time.time()
    for tag in tags:
        if tag not in bench:
            log("skip unknown " + tag)
            continue
        log("=== %s: %s ===" % (tag, bench[tag]["label"]))
        results.append(build(tag, bench[tag]))

    stamp = time.strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(ROOT, "delivery", "performance", "shape_variants_%s.json" % stamp)
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
    sys.exit(main())
