"""Render the look-dev bench: one full build + one formal frame per variant.

Three variants differ only through environment knobs that the modelling code
already reads, so each one is an honest build of the real map rather than a
re-shaded screenshot. Engine-side light values are applied at capture time
(delivery/next_cycle/n5/_variant_shots.js) because they live in the scene, not
in the GLB.

Usage:
    python tools/art/run_art_variants.py            # A B C
    python tools/art/run_art_variants.py A B        # subset
"""

import json
import os
import re
import struct
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VARIANTS_JSON = os.path.join(ROOT, "planning", "art", "ART_VARIANTS.json")
BLENDER = os.environ.get("P1_BLENDER_EXE") or os.path.join(
    os.path.expanduser("~"), ".cache", "blender", "5.2.3", "blender-5.2.3-windows-x64", "blender.exe"
)
MAP_SCRIPT = os.path.join("tools", "blender_n5", "build_map001.py")
ART_GLB = os.path.join(ROOT, "art", "candidates", "candidate_n5", "source", "layout",
                       "MAP001_courtyard.glb")


def log(msg):
    print("[art] " + msg, flush=True)


def glb_stats(path):
    with open(path, "rb") as fh:
        fh.read(12)
        clen, _ = struct.unpack("<II", fh.read(8))
        js = json.loads(fh.read(clen))
    tris = 0
    for mesh in js.get("meshes", []):
        for prim in mesh.get("primitives", []):
            idx = prim.get("indices")
            if idx is not None:
                tris += js["accessors"][idx]["count"] // 3
    return {
        "bytes": os.path.getsize(path),
        "mb": round(os.path.getsize(path) / 1048576.0, 2),
        "triangles": tris,
        "meshes": len(js.get("meshes", [])),
        "materials": len(js.get("materials", [])),
    }


def variant_env(cfg):
    env = dict(os.environ)
    palette = ";".join("%s=%s" % (k, v) for k, v in cfg["palette"].items())
    env.update({
        "N5_ART_VARIANT": cfg["_tag"],
        "N5_PALETTE": palette,
        "N5_LEAF_SCALE": str(cfg["leaf_scale"]),
        "N5_LEAF_COUNT_SCALE": str(cfg["leaf_count_scale"]),
        "N5_GRASS_BLADE_KEEP": str(cfg["grass_keep"]),
        "N5_GRASS_RING_BLADE_KEEP": str(cfg["grass_ring_keep"]),
        "N5_GRASS_WIDTH_SCALE": str(cfg["grass_width"]),
        "N5_GRASS_HEIGHT_SCALE": str(cfg["grass_height"]),
        "N5_GRASS_COUNT_SCALE": str(cfg.get("grass_count_scale", 1.0)),
        "N5_PAVING_JOINT_SCALE": str(cfg["paving_joint_scale"]),
        "N5_PAVING_UNIFY": str(cfg["paving_unify"]),
    })
    # A stale PYTHONPATH/heredoc env must not leak into the Blender process.
    for noisy in ("PYTHONHOME",):
        env.pop(noisy, None)
    return env


def run(cmd, env, timeout, label):
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True,
                          timeout=timeout, text=True, encoding="utf-8", errors="replace")
    dt = time.time() - t0
    out = (proc.stdout or "") + (proc.stderr or "")
    log("%-22s exit=%d %.1fs" % (label, proc.returncode, dt))
    return proc.returncode, out, round(dt, 1)


def build_variant(tag, cfg):
    cfg = dict(cfg)
    cfg["_tag"] = tag
    env = variant_env(cfg)
    result = {"tag": tag, "label": cfg["label"], "params": {k: v for k, v in cfg.items()
                                                            if not k.startswith("_")},
              "steps": {}}

    before = os.path.getmtime(ART_GLB) if os.path.exists(ART_GLB) else 0
    code, out, dt = run([BLENDER, "--background", "--factory-startup", "--python", MAP_SCRIPT],
                        env, 1800, tag + " blender")
    result["steps"]["blender"] = {"exit": code, "seconds": dt}
    written = re.findall(r"GLB_WRITTEN=(\S+)", out)
    if code != 0 or not written:
        tail = "\n".join(out.strip().splitlines()[-12:])
        result["error"] = "blender failed"
        result["tail"] = tail
        log("FAILED " + tag + "\n" + tail)
        return result
    if os.path.getmtime(ART_GLB) <= before:
        result["error"] = "GLB not rewritten"
        return result
    result["glb"] = glb_stats(ART_GLB)

    code, out, dt = run([sys.executable, os.path.join("tools", "sync_map_glb.py"), "--apply"],
                        env, 600, tag + " sync")
    result["steps"]["sync"] = {"exit": code, "seconds": dt, "tail": out.strip().splitlines()[-1:]}
    if code != 0:
        result["error"] = "sync failed"
        return result

    code, out, dt = run([sys.executable, os.path.join("tools", "n5_build.py"),
                         "--run-id", "art-" + tag.lower(),
                         "--reason", "look-dev variant " + tag, "--force"],
                        env, 2400, tag + " engine build")
    result["steps"]["engine"] = {"exit": code, "seconds": dt,
                                 "tail": out.strip().splitlines()[-2:]}
    # n5_build's exit code is polluted by a safe-delete confirmation request
    # for the __pycache__ folders; the build report is the real signal.
    if code != 0 and '"pinned"' not in out:
        result["error"] = "engine build failed"
        return result

    code, out, dt = run(["node", os.path.join("delivery", "next_cycle", "n5", "_variant_shots.js"),
                         tag, VARIANTS_JSON], env, 600, tag + " shot")
    result["steps"]["shot"] = {"exit": code, "seconds": dt,
                               "tail": out.strip().splitlines()[-1:]}
    if code != 0:
        result["error"] = "shot failed"
        return result
    return result


def main():
    tags = sys.argv[1:] or ["A", "B", "C"]
    bench = json.load(open(VARIANTS_JSON, encoding="utf-8"))["variants"]
    results = []
    t0 = time.time()
    for tag in tags:
        if tag not in bench:
            log("skip unknown variant " + tag)
            continue
        log("=== variant %s: %s ===" % (tag, bench[tag]["label"]))
        results.append(build_variant(tag, bench[tag]))

    stamp = time.strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(ROOT, "delivery", "performance", "art_variants_%s.json" % stamp)
    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_seconds": round(time.time() - t0, 1),
        "variants": results,
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    log("report " + out_path)
    failed = [r["tag"] for r in results if r.get("error")]
    log("done: %d ok, %d failed%s" % (len(results) - len(failed), len(failed),
                                      (" (" + ",".join(failed) + ")") if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
