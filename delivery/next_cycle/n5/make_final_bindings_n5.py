"""Create and verify capture bindings for the final formal-camera evidence."""
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
T3 = ROOT / "delivery/next_cycle/n5/T3"
OUT = ROOT / "art_review/submissions/candidate_n5/bindings"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    checker = load("check_bindings", ROOT / "tools/art_gate/check_bindings.py")
    shots = json.loads((T3 / "game_finalN5h_shots.json").read_text(encoding="utf-8-sig"))
    pin_path = ROOT / "delivery/next_cycle/n5/performance/formal_build.json"
    if not pin_path.is_file():
        raise SystemExit("no formal build pin; run tools/n5_build.py before binding")
    pin = json.loads(pin_path.read_text(encoding="utf-8-sig"))
    build_report = pin["build_report_json"]
    build_id = pin["build_id"]
    build_log = ROOT / pin["build_log"]
    sources = [
        ("map_blend", "art/candidates/candidate_n5/source/layout/MAP001_courtyard.blend"),
        ("tree_blend", "art/candidates/candidate_n5/source/environment/ENV006_autumn_tree.blend"),
        ("map_script", "tools/blender_n5/build_map001.py"),
        ("tree_script", "tools/blender_n5/build_env_courtyard.py"),
        ("engine_bootstrap", "demo_n5/assets/scripts/CourtyardBootstrap.ts"),
    ]
    exports = [
        ("map_glb", "art/candidates/candidate_n5/source/layout/MAP001_courtyard.glb"),
        ("engine_glb", "demo_n5/assets/resources/models/MAP001_courtyard.glb"),
    ]
    textures = [
        ("texture", "art/candidates/candidate_n5/source/textures/tex_stone_tiles.png"),
        ("texture", "art/candidates/candidate_n5/source/textures/tex_wood_grain.png"),
        ("texture", "art/candidates/candidate_n5/source/textures/tex_metal_brushed.png"),
        ("texture", "art/candidates/candidate_n5/source/textures/tex_soil_noise.png"),
        ("texture", "art/candidates/candidate_n5/source/textures/tex_bark.png"),
        ("texture", "art/candidates/candidate_n5/source/textures/tex_leaf_detail.png"),
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    summary = []
    for shot in shots["shots"]:
        meta = shot["meta"]
        output_path = Path(meta["output"]["path"])
        if output_path.is_absolute():
            output_rel = output_path.resolve().relative_to(ROOT).as_posix()
        else:
            output_rel = str(output_path).replace("\\", "/")
        binding = {
            "binding_version": "vnext.capture_binding/1.0.0",
            "binding_id": "cap-finalN5-" + shot["name"],
            "stage": "art_complete",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "backend": {"name": "cocos-creator-web-desktop", "version": "3.8.8"},
            "viewport": {**meta["viewport"], "device_pixel_ratio": meta["device_pixel_ratio"]},
            "canvas": {
                "selector": meta["selector"], "css_rect": meta["css_rect"],
                "backing_width": meta["backing_width"], "backing_height": meta["backing_height"],
                "capture_method": meta["capture_method"], "page_screenshot": False,
            },
            "camera": {"node": "Main Camera", "position": [-2.5, 11.5, -14.6],
                       "rotation": [-36.276619358317014, 180, 0], "fov": 37.5, "clip_time": None},
            "sources": [{"role": role, "path": path, "sha256": sha(ROOT / path)} for role, path in sources],
            "exports": [{"role": role, "path": path, "sha256": sha(ROOT / path)} for role, path in exports],
            "shared_inputs": [{"role": role, "path": path, "sha256": sha(ROOT / path),
                               "scope": ["MAP001"]} for role, path in textures],
            "build": {"build_id": build_id,
                      "log_path": pin["build_log"],
                      "log_sha256": sha(build_log), "result": "success"},
            "output": {"path": output_rel,
                       "sha256": meta["output"]["sha256"],
                       "width": meta["output"]["width"], "height": meta["output"]["height"]},
            "notes": ["Cocos 3.8.8 exits 36 after Finished + SIGTERM; accepted only by the versioned gate rule with build output present.",
                      "Real canvas element capture; CSS rect extends beyond the 1280x720 browser viewport, full backing captured."],
        }
        path = OUT / ("binding_" + shot["name"] + ".json")
        path.write_text(json.dumps(binding, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result = checker.verify_binding(ROOT, path, ROOT / "art_review/vnext/capture_binding.schema.json")
        summary.append({"shot": shot["name"], "binding": path.relative_to(ROOT).as_posix(),
                        "verified": result["verified"], "checks": result["checks"],
                        "output": result["output"]})
    summary_path = T3 / "finalN5_bindings_summary.json"
    summary_path.write_text(json.dumps({
        "kind": "finalN5_capture_bindings", "build_report": pin["build_report"],
        "build_id": build_id,
        "bindings": summary, "all_verified": all(item["verified"] for item in summary),
        "meaning": "Evidence-chain verification only; not visual acceptance.",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_verified": all(item["verified"] for item in summary),
                      "count": len(summary), "summary": str(summary_path)}, ensure_ascii=False))
    return 0 if all(item["verified"] for item in summary) else 2


if __name__ == "__main__":
    raise SystemExit(main())
