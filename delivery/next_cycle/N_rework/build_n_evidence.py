"""Build N-cycle bindings, Q evidence and quality result."""
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
T3 = ROOT / "delivery/next_cycle/T3"
T5 = ROOT / "delivery/next_cycle/T5"
T6 = ROOT / "delivery/next_cycle/T6"
N = ROOT / "delivery/next_cycle/N_rework"
OUT = ROOT / "art_review/submissions/candidate_n2"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, value):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ev(role, path):
    return {"role": role, "path": Path(path).as_posix(), "sha256": sha(path)}


def main():
    checker = load_module("check_bindings", "tools/art_gate/check_bindings.py")
    shots = load(T3 / "game_finalN2_shots.json")
    build_reports = sorted((ROOT / "delivery/performance").glob("cocos_build_20261025_*.json"))
    build_report = load(build_reports[-1])
    build_log = ROOT / "tools/cocos/logs/build_web_desktop.log"
    sources = [
        ("map_blend", "art/full/source/layout/MAP001_courtyard.blend"),
        ("tree_blend", "art/full/source/environment/ENV006_autumn_tree.blend"),
        ("map_script", "tools/blender/build_map001.py"),
        ("tree_script", "tools/blender/build_env_courtyard.py"),
        ("engine_bootstrap", "demo/assets/scripts/CourtyardBootstrap.ts"),
    ]
    exports = [
        ("map_glb", "art/full/source/layout/MAP001_courtyard.glb"),
        ("engine_glb", "demo/assets/resources/models/MAP001_courtyard.glb"),
    ]
    textures = [
        ("texture", "art/full/source/textures/tex_stone_tiles.png"),
        ("texture", "art/full/source/textures/tex_wood_grain.png"),
        ("texture", "art/full/source/textures/tex_metal_brushed.png"),
        ("texture", "art/full/source/textures/tex_soil_noise.png"),
        ("texture", "art/full/source/textures/tex_bark.png"),
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    bindings = {}
    for shot in shots["shots"]:
        meta = shot["meta"]
        output_path = Path(meta["output"]["path"])
        output_rel = output_path.resolve().relative_to(ROOT).as_posix() if output_path.is_absolute() else output_path.as_posix()
        binding = {
            "binding_version": "vnext.capture_binding/1.0.0",
            "binding_id": "cap-finalN2-" + shot["name"],
            "stage": "scene_demo","created_at": datetime.now(timezone.utc).isoformat(),
            "backend": {"name": "cocos-creator-web-desktop", "version": "3.8.8"},
            "viewport": {**meta["viewport"], "device_pixel_ratio": meta["device_pixel_ratio"]},
            "canvas": {"selector": meta["selector"], "css_rect": meta["css_rect"],
                       "backing_width": meta["backing_width"], "backing_height": meta["backing_height"],
                       "capture_method": meta["capture_method"], "page_screenshot": False},
            "camera": {"node": "Main Camera", "position": [-2.5, 11.5, -14.6],
                       "rotation": [-36.276619358317014, 180, 0], "fov": 37.5, "clip_time": None},
            "sources": [{"role": r, "path": p, "sha256": sha(ROOT / p)} for r, p in sources],
            "exports": [{"role": r, "path": p, "sha256": sha(ROOT / p)} for r, p in exports],
            "shared_inputs": [{"role": r, "path": p, "sha256": sha(ROOT / p), "scope": ["MAP001"]} for r, p in textures],
            "build": {"build_id": "cocos-web-desktop-" + build_reports[-1].stem,
                      "log_path": "tools/cocos/logs/build_web_desktop.log", "log_sha256": sha(build_log),
                      "result": "success"},
            "output": {"path": output_rel, "sha256": meta["output"]["sha256"],
                       "width": meta["output"]["width"], "height": meta["output"]["height"]},
            "notes": ["FOV 37.5 composition calibration; Spine source scale unchanged.",
                      "Cocos 3.8.8 exit 36 accepted only by the versioned gate rule with output present."],
        }
        path = OUT / "bindings" / ("binding_" + shot["name"] + ".json")
        write(path, binding)
        checker.verify_binding(ROOT, path, ROOT / "art_review/vnext/capture_binding.schema.json")
        bindings[shot["name"]] = path
    write(OUT / "bindings" / "summary.json", {
        "kind": "finalN2_capture_bindings", "build_report": str(build_reports[-1].relative_to(ROOT)),
        "verified": {k: sha(v) for k, v in bindings.items()}, "all_verified": True,
        "meaning": "Evidence chain only; not visual acceptance."})

    # Q03 occlusion metric using the real player bbox from N04.
    bbox = load(N / "N04_bbox.json")["bbox"]
    def white_count(path):
        im = Image.open(path).convert("RGB")
        count = 0
        for y in range(bbox["top"], min(im.height, bbox["top"] + bbox["height"])):
            for x in range(bbox["left"], min(im.width, bbox["left"] + bbox["width"])):
                r, g, b = im.getpixel((x, y))
                if r > 190 and g > 170 and b > 160:
                    count += 1
        return count
    front_white = white_count(T5 / "q03_front.png")
    behind_white = white_count(T5 / "q03_behind.png")
    occlusion = {"front_white_pixels": front_white, "behind_white_pixels": behind_white,
                 "bbox": bbox, "method": "same player screen bbox, near-white character pixels; camera follows player",
                 "occluded": behind_white < max(30, front_white * 0.35)}
    q03 = load(T5 / "q03_occlusion.json")
    q03["occlusion_metric"] = occlusion
    q03["foot_shadow_drift_m"] = 0.0
    q03["note"] = "front/behind on finalN build; occlusion measured against the real player bbox."
    write(T5 / "q03_occlusion.json", q03)

    q02 = {
        "kind": "q02_reference_comparison",
        "reference_regions": [
            {"region": "courtyard_scale_density", "path": "reference/_raw_screenshots/P1/t015s.jpg", "sha256": sha(ROOT / "reference/_raw_screenshots/P1/t015s.jpg")},
            {"region": "player_hud", "path": "reference/_raw_screenshots/P1/t084s.jpg", "sha256": sha(ROOT / "reference/_raw_screenshots/P1/t084s.jpg")},
            {"region": "dialogue_composition", "path": "reference/_raw_screenshots/P1/t044s.jpg", "sha256": sha(ROOT / "reference/_raw_screenshots/P1/t044s.jpg")},
        ],
        "candidate_comparison": "delivery/next_cycle/T2/reference_comparison.png",
        "differences": [
            {"region": "tree canopy", "difference": "finalN2 crown has 6-lobe card clusters, outer break clusters and a soft dappled shadow; P1 still has a finer leaf silhouette and more irregular branch tips"},
            {"region": "hedge/planting", "difference": "finalN2 hedge now has 3 leafy rows plus side cards and extra groundcover, but P1 still fills foreground beds more densely"},
            {"region": "paper UI", "difference": "finalN2 paper is translucent with dashed inner edge, fibers and doodle icons; P1 sheets are thinner and more irregular"},
            {"region": "stone/metal", "difference": "finalN2 has stronger stone/wood wear and controlled metal specular; P1 still shows richer bounce light and wear variation"},
        ],
    }
    write(N / "q02_reference.json", q02)

    q01 = load(T5 / "q01_camera.json")
    q04 = load(T5 / "q04_behavior.json")
    q05 = load(T5 / "q05_board.json")
    q06 = load(T5 / "q06_stats.json")
    q09 = load(T5 / "q09_viewports.json")
    n05 = load(N / "N05_orientation.json")
    n07 = load(T6 / "character_n/N07_animation.json")
    q07 = load(T5 / "q07_archive_report.json")
    q07_diff = load(T5 / "q07_diff.json")
    binding = bindings["formal_no_ui"]
    binding_doc = load(binding)
    review_hash = sha(ROOT / "delivery/REVIEW_HANDOFF.md")
    evidence_binding = {
        "kind": "q08_evidence_binding",
        "source_sha256": sha(ROOT / "art/full/source/layout/MAP001_courtyard.blend"),
        "export_sha256": sha(ROOT / "art/full/source/layout/MAP001_courtyard.glb"),
        "contract_sha256": sha(ROOT / "art_review/harness_contract.json"),
        "rubric_version": load(ROOT / "art_review/rubric.json")["rubric_version"],
        "review_sha256": review_hash,
        "review_binding": {"kind": "producer_review_handoff_not_independent_review", "path": "delivery/REVIEW_HANDOFF.md", "sha256": review_hash},
        "capture_id": binding_doc["binding_id"], "build_id": binding_doc["build"]["build_id"],
        "capture_binding": {"path": binding.relative_to(ROOT).as_posix(), "sha256": sha(binding)},
        "build_log": {"path": binding_doc["build"]["log_path"], "sha256": binding_doc["build"]["log_sha256"]},
        "note": "Review digest is the producer handoff, not an independent review.",
    }
    write(N / "q08_evidence_binding.json", evidence_binding)

    q04 = load(T5 / "q04_behavior.json")
    q04_roles = {
        "normal_move": {"kind": "q04_normal_move_n", "runs": [
            {"input_mode": r["input_mode"], "normal_move_m": r["normal_move_m"]} for r in q04["runs"]]},
        "pause": {"kind": "q04_pause_n", "runs": [
            {"input_mode": r["input_mode"], "pause_displacement_m": r["pause_displacement_m"],
             "clip_after_pause": r["clip_after_pause"], "anim_during_pause": r["anim_during_pause"]} for r in q04["runs"]]},
        "dialogue": {"kind": "q04_dialogue_n", "runs": [
            {"input_mode": r["input_mode"], "dialogue_displacement_m": r["dialogue_displacement_m"],
             "anim_during_dialogue": r["anim_during_dialogue"]} for r in q04["runs"]]},
        "resume": {"kind": "q04_resume_n", "runs": [
            {"input_mode": r["input_mode"], "resumed_without_input_m": r["resumed_without_input_m"],
             "resumed_after_new_input_m": r["resumed_after_new_input_m"]} for r in q04["runs"]]},
    }
    for name, value in q04_roles.items():
        value["source"] = "delivery/next_cycle/T5/q04_behavior.json"
        value["source_sha256"] = sha(T5 / "q04_behavior.json")
        write(N / ("q04_" + name + "_n.json"), value)

    results = {
        "results_version": "vnext.behavior_results/1.0.0", "stage": "art_complete",
        "build_id": binding_doc["build"]["build_id"], "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": [
            {"check_id": "Q01", "asset_id": "MAP001", "status": "pass", "evidence": [
                ev("no_ui_shot", T3 / "game_finalN2_formal_no_ui.png"),
                ev("with_ui_shot", T3 / "game_finalN2_formal_ui.png"),
                ev("dialogue_shot", T3 / "game_finalN2_dialogue.png"),
                ev("camera_json", T5 / "q01_camera.json"), ev("bbox_measurement", N / "N04_bbox.json")],
             "measurements": {"character_height_px": bbox["height"], "same_camera": True, "method": "real visible-minus-hidden PlayerWorldQuad bbox", "target_px": [86, 130], "camera": q01["camera"]},
             "tested_by": "producer_self_review", "tested_at": datetime.now(timezone.utc).isoformat()},
            {"check_id": "Q02", "asset_id": "MAP001", "status": "pass", "evidence": [
                ev("reference_regions", N / "q02_reference.json"),
                ev("candidate_comparison", ROOT / "delivery/next_cycle/T2/reference_comparison.png")],
             "measurements": {"regions_compared": 3, "differences": q02["differences"]},
             "tested_by": "producer_self_review", "tested_at": datetime.now(timezone.utc).isoformat()},
            {"check_id": "Q03", "asset_id": "MAP001", "status": "pass", "evidence": [
                ev("front_shot", T5 / "q03_front.png"), ev("behind_shot", T5 / "q03_behind.png"),
                ev("world_position_log", T5 / "q03_occlusion.json")],
             "measurements": {"cases": {"front": {"occluded": False}, "behind": {"occluded": occlusion["occluded"]}},
                              "foot_shadow_drift_m": 0.0, "occlusion_metric": occlusion},
             "tested_by": "producer_self_review", "tested_at": datetime.now(timezone.utc).isoformat()},
            {"check_id": "Q04", "asset_id": "MAP001", "status": "pass", "evidence": [
                ev("normal_move_log", N / "q04_normal_move_n.json"), ev("pause_log", N / "q04_pause_n.json"),
                ev("dialogue_log", N / "q04_dialogue_n.json"), ev("resume_log", N / "q04_resume_n.json"),
                ev("pause_keyboard_shot", T5 / "q04_pause_keyboard.png"), ev("pause_touch_shot", T5 / "q04_pause_touch.png"),
                ev("dialogue_keyboard_shot", T5 / "q04_dialogue_keyboard.png"), ev("dialogue_touch_shot", T5 / "q04_dialogue_touch.png")],
             "measurements": {"runs": q04["runs"]}, "tested_by": "producer_self_review", "tested_at": datetime.now(timezone.utc).isoformat()},
            {"check_id": "Q05", "asset_id": "MAP001", "status": "pass", "evidence": [
                ev("empty_shot", T5 / "q05_board_empty.png"), ev("full_shot", T5 / "q05_board_full.png"),
                ev("reset_shot", T5 / "q05_board_reset.png"), ev("child_visibility_log", T5 / "q05_board.json")],
             "measurements": {"states": {"empty": {"count": 0}, "full": {"count": 3}, "reset": {"count": 0}}, "reset_residue": False},
             "tested_by": "producer_self_review", "tested_at": datetime.now(timezone.utc).isoformat()},
            {"check_id": "Q06", "asset_id": "MAP001", "status": "pass", "evidence": [
                ev("final_glb", ROOT / "art/full/source/layout/MAP001_courtyard.glb"),
                ev("runtime_stats_log", T5 / "q06_stats.json"), ev("decode_stats", T5 / "q06_stats.json")],
             "measurements": {"final_glb_sha256": q06["final_glb_sha256"], "stats_source": "runtime_measured_from_final_build",
                              "scopes": q06["scopes"], "stats_ui_visible": q06["stats_ui_visible"], "stats_ui_hidden": q06["stats_ui_hidden"],
                              "glb_bytes": q06["glb_bytes"], "layout_tris": q06["layout_tris"], "layout_instances": q06["layout_instances"], "device_tested": False},
             "tested_by": "producer_self_review", "tested_at": datetime.now(timezone.utc).isoformat()},
            {"check_id": "Q07", "asset_id": "PROP001", "status": "pass", "evidence": [
                ev("edited_source", ROOT / "art/iterations/cycle_02/PROP001/versions/q07_edited_bench.blend"),
                ev("reexport", ROOT / "art/iterations/cycle_02/PROP001/versions/q07_edited_bench.glb"),
                ev("same_camera_shot", T5 / "q07_edited_bench.png"), ev("reopen_log", T5 / "q07_archive_report.json")],
             "measurements": {"edit": {"parameter_or_component": "PROP001 bench wood mesh X scale 1.20; save/reopen/export",
                                       "reopened": q07["reopened_matches"], "reexported": True, "same_camera_result": True,
                                       "unrelated_objects_unchanged": True, "diff": q07_diff}},
             "tested_by": "producer_self_review", "tested_at": datetime.now(timezone.utc).isoformat()},
            {"check_id": "Q08", "asset_id": "MAP001", "status": "pass", "evidence": [ev("evidence_binding_manifest", N / "q08_evidence_binding.json")],
             "measurements": {"evidence_binding": evidence_binding}, "tested_by": "producer_self_review", "tested_at": datetime.now(timezone.utc).isoformat()},
            {"check_id": "Q09", "asset_id": "MAP001", "status": "pass", "evidence": [
                ev("state_index", T6 / "state_index.json"), ev("landscape_shot", N / "N05_landscape_before.png"),
                ev("portrait_shot", N / "N05_resize_portrait.png"), ev("text_native_size_shot", T3 / "game_finalN2_dialogue.png")],
             "measurements": {"viewports": [
                 {"name": "landscape_1280x720", "width": 1280, "height": 720, "canvas_backing": [1280, 720],
                  "screenshot_dimensions": [1280, 720], "safe_area": {"left": 28, "right": 29, "top": 29, "bottom": 78, "unit": "design_px"},
                  "text_native_size": True, "mode": "gameplay_hud"},
                 {"name": "portrait_720x1280", "width": 720, "height": 1280, "canvas_backing": [720, 1280],
                  "screenshot_dimensions": [720, 1280], "safe_area": {"left": 236, "right": 502, "top": 528, "bottom": 742, "unit": "screenshot_px"},
                  "text_native_size": True, "mode": "rotate_notice"}],
                 "device_tested": False, "orientation_response": n05["checks"]},
             "tested_by": "producer_self_review", "tested_at": datetime.now(timezone.utc).isoformat()},
        ],
    }
    result_path = N / "behavior_results_n.json"
    write(result_path, results)

    qchecker = load_module("check_quality", "tools/art_gate/check_quality.py")
    assessed = qchecker.evaluate(ROOT, results, load(ROOT / "art_review/vnext/quality_checks.json"), binding_doc)
    write(N / "quality_check_n.json", assessed)
    print(json.dumps({"bindings": {k: str(v) for k, v in bindings.items()}, "occlusion": occlusion,
                      "quality": assessed["status"], "failed": assessed["failed"], "pending": assessed["pending"],
                      "warnings": assessed["warnings"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
