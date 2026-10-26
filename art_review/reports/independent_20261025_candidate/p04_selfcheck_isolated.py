__file__='C:\\软件\\鼠鼠\\delivery\\next_cycle\\T0\\p04_selfcheck.py'
__name__="__main__"
"""P04 self-check: capture-binding proof and content-hash dirty closure on synthetic fixtures."""
import hashlib
import importlib.util
import json
import os
import shutil
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CHECKER = ROOT / "tools/art_gate/check_bindings.py"
SCHEMA = ROOT / "art_review/vnext/capture_binding.schema.json"
TMP = ROOT / "art_review/reports/independent_20261025_candidate/fixtures_p04"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_bindings", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def wj(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def wb(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def png(width, height):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    raw = (b"\x00" + b"\x00\x00\x00\x00" * width) * height
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def rel(path):
    return path.relative_to(ROOT).as_posix()


def build_fixture(case):
    base = TMP / case
    files = {
        "shared_tex.png": png(8, 8),
        "map.blend": b"BLENDER-map-fixture",
        "map.glb": b"glTF-map-fixture",
        "tree.blend": b"BLENDER-tree-fixture",
        "tree.glb": b"glTF-tree-fixture",
        "composite.glb": b"glTF-composite-fixture",
        "build.log": b"[build] Build Task Finished\n[build] 0 errors\n",
        "out_a.png": png(1280, 720),
        "out_b.png": png(1280, 720),
        "out_c.png": png(1280, 720),
        "out_d.png": png(1280, 720),
        "ui.svg": b'<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0 L4 4"/></svg>',
        "ui.glb": b"glTF-ui-fixture",
        "unique.txt": b"unreferenced fixture",
    }
    for name, data in files.items():
        wb(base / name, data)

    def camera(clip):
        return {"node": "Main Camera", "position": [-2.5, 11.5, -14.6],
                "rotation": [-33, 0, 0], "fov": 35, "clip_time": clip}

    def binding(bid, stage, sources, exports, outputs, shared, clip):
        return {
            "binding_version": "vnext.capture_binding/1.0.0",
            "binding_id": bid, "stage": stage, "created_at": "2026-10-25T00:00:00Z",
            "backend": {"name": "cocos-creator-web-desktop", "version": "3.8.8"},
            "viewport": {"browser_width": 1280, "browser_height": 720, "device_pixel_ratio": 1},
            "canvas": {"selector": "#GameCanvas",
                       "css_rect": {"x": 5, "y": 84.875, "width": 1280, "height": 720},
                       "backing_width": 1280, "backing_height": 720,
                       "capture_method": "canvas_to_data_url", "page_screenshot": False},
            "camera": camera(clip),
            "sources": sources, "exports": exports, "shared_inputs": shared,
            "build": {"build_id": "build-001", "log_path": rel(base / "build.log"),
                      "log_sha256": sha(base / "build.log"), "result": "success"},
            "output": {"path": rel(base / outputs), "sha256": sha(base / outputs),
                       "width": 1280, "height": 720},
        }

    tex = {"role": "texture", "path": rel(base / "shared_tex.png"),
           "sha256": sha(base / "shared_tex.png"), "scope": ["MAP001", "ENV006"]}
    a = binding("cap-A", "scene_demo",
                [{"role": "map_source", "path": rel(base / "map.blend"), "sha256": sha(base / "map.blend")}],
                [{"role": "map_glb", "path": rel(base / "map.glb"), "sha256": sha(base / "map.glb")}],
                "out_a.png", [tex], 0.5)
    b = binding("cap-B", "art_complete",
                [{"role": "tree_source", "path": rel(base / "tree.blend"), "sha256": sha(base / "tree.blend")}],
                [{"role": "tree_glb", "path": rel(base / "tree.glb"), "sha256": sha(base / "tree.glb")}],
                "out_b.png", [tex], 0.5)
    c = binding("cap-C", "art_complete",
                [{"role": "scene_capture", "path": rel(base / "out_a.png"), "sha256": sha(base / "out_a.png")},
                 {"role": "tree_capture", "path": rel(base / "out_b.png"), "sha256": sha(base / "out_b.png")}],
                [{"role": "composite_glb", "path": rel(base / "composite.glb"), "sha256": sha(base / "composite.glb")}],
                "out_c.png", [], None)
    d = binding("cap-D", "scene_demo",
                [{"role": "ui_source", "path": rel(base / "ui.svg"), "sha256": sha(base / "ui.svg")}],
                [{"role": "ui_glb", "path": rel(base / "ui.glb"), "sha256": sha(base / "ui.glb")}],
                "out_d.png", [], None)
    paths = {}
    for name, value in (("A", a), ("B", b), ("C", c), ("D", d)):
        path = base / f"binding_{name}.json"
        wj(path, value)
        paths[name] = path
    return base, paths


def main():
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True)
    module = load_checker()
    results = {"kind": "p04_selfcheck_capture_binding", "checker_sha256": sha(CHECKER),
               "schema_sha256": sha(SCHEMA), "verify_cases": [], "impact_cases": []}

    def run_verify(name, mutate=None, delete=None, expect_error=None):
        base, paths = build_fixture(name)
        binding = json.loads(paths["A"].read_text(encoding="utf-8"))
        if mutate:
            mutate(binding)
            wj(paths["A"], binding)
        if delete:
            (base / delete).unlink()
        try:
            out = module.verify_binding(ROOT, paths["A"], SCHEMA)
            passed = expect_error is None
            error = None
        except module.BindingError as exc:
            passed = expect_error is not None and expect_error in str(exc)
            error = str(exc)
            out = None
        results["verify_cases"].append({"case": name, "pass": passed, "error": error,
                                        "checks": (out or {}).get("checks"),
                                        "expected_error_contains": expect_error})
        return passed

    def set_output_hash(b):
        b["output"]["sha256"] = "0" * 64

    def page_screenshot(b):
        b["canvas"]["page_screenshot"] = True

    def backing_mismatch(b):
        b["canvas"]["backing_width"] = 1279

    def build_failure(b):
        b["build"]["result"] = "failure"

    def frozen_output(b):
        b["output"]["path"] = "art_review/submissions/frozen_capture.png"

    ok = True
    ok &= run_verify("good_binding")
    ok &= run_verify("output_hash_tampered", set_output_hash, expect_error="output hash mismatch")
    ok &= run_verify("page_screenshot_rejected", page_screenshot, expect_error="page_screenshot")
    ok &= run_verify("backing_size_mismatch", backing_mismatch, expect_error="canvas backing size")
    ok &= run_verify("missing_build_log", delete="build.log", expect_error="Missing file")
    ok &= run_verify("build_failure_rejected", build_failure, expect_error="marked failure")
    ok &= run_verify("frozen_output_rejected", frozen_output, expect_error="frozen evidence")

    def run_impact(name, changed, mutate, expected_dirty):
        base, paths = build_fixture(name)
        mutate(base)
        out = module.impact(ROOT, [paths["A"], paths["B"], paths["C"], paths["D"]], changed(base))
        dirty = sorted(row["binding_id"] for row in out["dirty_bindings"])
        unrelated_clean = "cap-D" not in dirty and "cap-D" in out["unaffected_bindings"]
        passed = dirty == expected_dirty and unrelated_clean
        results["impact_cases"].append({"case": name, "pass": passed, "dirty": dirty,
                                        "expected_dirty": expected_dirty,
                                        "unrelated_cap_d_clean": unrelated_clean,
                                        "stages": out["stages_to_rereview"],
                                        "changed": out["changed"]})
        return passed

    ok &= run_impact("shared_texture_change", lambda b: rel(b / "shared_tex.png"),
                     lambda b: wb(b / "shared_tex.png", png(9, 9)), ["cap-A", "cap-B", "cap-C"])
    ok &= run_impact("single_tree_source_change", lambda b: rel(b / "tree.blend"),
                     lambda b: wb(b / "tree.blend", b"BLENDER-tree-v2"), ["cap-B", "cap-C"])
    ok &= run_impact("same_bytes_touch_only", lambda b: rel(b / "out_a.png"),
                     lambda b: os.utime(b / "out_a.png", (2000000000, 2000000000)), [])
    ok &= run_impact("upstream_capture_change", lambda b: rel(b / "out_a.png"),
                     lambda b: wb(b / "out_a.png", png(1280, 720) + b"edited"), ["cap-A", "cap-C"])
    ok &= run_impact("unreferenced_file", lambda b: rel(b / "unique.txt"),
                     lambda b: wb(b / "unique.txt", b"changed but unreferenced"), [])

    results["all_passed"] = bool(ok)
    if TMP.exists():
        shutil.rmtree(TMP)
    output = ROOT / "art_review/reports/independent_20261025_candidate/p04_replay.json"
    wj(output, results)
    print(json.dumps({"all_passed": results["all_passed"],
                      "verify_cases": len(results["verify_cases"]),
                      "impact_cases": len(results["impact_cases"]),
                      "output": str(output), "sha256": sha(output)}, ensure_ascii=False))
    return 0 if results["all_passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
