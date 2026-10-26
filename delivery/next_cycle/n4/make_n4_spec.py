import json
import hashlib
import pathlib

ROOT = pathlib.Path(".")
N4 = ROOT / "delivery/next_cycle/n4"


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


artifacts = [
    ("clip_inventory", "art/phase1/character_playback_1015/clip_inventory.json"),
    ("idle_preview", "art/phase1/character_playback_1015/idle_preview.png"),
    ("move_preview", "art/phase1/character_playback_1015/move_preview.gif"),
    ("reference_comparison", "art/phase1/character_playback_1015/reference_comparison.png"),
    ("runtime_log", "art/phase1/character_playback_1015/runtime_log.txt"),
    ("scene_screenshot", "delivery/next_cycle/n4/T3/game_finalN4_formal_no_ui.png"),
    ("dialogue_screenshot", "delivery/next_cycle/n4/T3/game_finalN4_dialogue.png"),
    ("demo_recording", "delivery/next_cycle/n4/T6/demo_current.gif"),
    ("engine_sources", "delivery/courtyard_scene_demo_sources_v7.zip"),
    ("run_instructions", "delivery/RUN_DEMO_v7.md"),
    ("map_editable_source", "art/candidates/candidate_n4/source/layout/MAP001_courtyard.blend"),
    ("ui_editable_source", "art/candidates/candidate_n4/ui/components/paper_panel.svg"),
    ("ui_torn_paper_source", "art/candidates/candidate_n4/ui/components/paper_panel_wash.svg"),
    ("ui_torn_paper_export", "art/candidates/candidate_n4/ui/exports/paper_panel_wash.png"),
    ("full_art_catalog", "art/iterations/cycle_04/full_art_catalog.json"),
    ("ui_state_index", "delivery/next_cycle/n4/T6/state_index.json"),
    ("capture_bindings", "art_review/submissions/candidate_n4/bindings/summary.json"),
    ("quality_results", "delivery/next_cycle/n4/T5/behavior_results_n4.json"),
    ("runtime_stats", "delivery/next_cycle/n4/T5/q06_stats.json"),
    ("occlusion_evidence", "delivery/next_cycle/n4/T5/q03_occlusion.json"),
    ("sample_no_ui", "delivery/next_cycle/n4/T3/game_finalN4_formal_no_ui.png"),
    ("sample_hud", "delivery/next_cycle/n4/T3/game_finalN4_formal_ui.png"),
    ("sample_dialogue", "delivery/next_cycle/n4/T3/game_finalN4_dialogue.png"),
    ("reference_comparison_scene", "delivery/next_cycle/n4/T2/reference_comparison.png"),
    ("n01_tree_hedge", "delivery/next_cycle/n4/T4/N01_geometry_before_after.png"),
    ("n01_geometry_closeups", "delivery/next_cycle/n4/T4/N01_geometry_closeups.png"),
    ("n02_shadow", "delivery/next_cycle/n4/T4/N02_shadow_before_after.png"),
    ("n02_material", "delivery/next_cycle/n4/T4/N02_material_closeups.png"),
    ("n03_ui", "delivery/next_cycle/n4/T4/N03_ui_before_after.png"),
    ("n04_bbox_sheet", "delivery/next_cycle/n4/T4/N04_actor_bbox.png"),
    ("n04_visible", "delivery/next_cycle/n4/T4/N04_actor_visible.png"),
    ("n04_hidden", "delivery/next_cycle/n4/T4/N04_actor_hidden.png"),
    ("n04_bbox_json", "delivery/next_cycle/n4/T4/N04_bbox.json"),
    ("n05_orientation", "delivery/next_cycle/n4/T4/N05_orientation.png"),
    ("n05_orientation_json", "delivery/next_cycle/n4/T4/N05_orientation.json"),
    ("n07_animation_sheet", "delivery/next_cycle/n4/T6/character_n/N07_animation_sheet.png"),
    ("n07_animation_json", "delivery/next_cycle/n4/T6/character_n/N07_animation.json"),
    ("n07_idle_gif", "delivery/next_cycle/n4/T6/character_n/char_idle.gif"),
    ("n07_move_gif", "delivery/next_cycle/n4/T6/character_n/char_move.gif"),
    ("n09_q04_moved", "delivery/next_cycle/n4/T5/q04_behavior_moved.json"),
    ("n09_pause_keyboard", "delivery/next_cycle/n4/T5/q04_pause_from_moved_keyboard.png"),
    ("n09_resume_keyboard", "delivery/next_cycle/n4/T5/q04_resume_from_moved_keyboard.png"),
    ("n09_pause_touch", "delivery/next_cycle/n4/T5/q04_pause_from_moved_touch.png"),
    ("n09_resume_touch", "delivery/next_cycle/n4/T5/q04_resume_from_moved_touch.png"),
    ("n09_portrait", "delivery/next_cycle/n4/T5/q04_portrait_from_moved.png"),
    ("n09_landscape_return", "delivery/next_cycle/n4/T5/q04_landscape_return_from_moved.png"),
    ("q01_camera", "delivery/next_cycle/n4/T5/q01_camera.json"),
    ("q02_reference", "delivery/next_cycle/n4/T5/q02_reference.json"),
    ("q03_front", "delivery/next_cycle/n4/T5/q03_front.png"),
    ("q03_behind", "delivery/next_cycle/n4/T5/q03_behind.png"),
    ("q04_behavior", "delivery/next_cycle/n4/T5/q04_behavior_moved.json"),
    ("q05_board_empty", "delivery/next_cycle/n4/T5/q05_board_empty.png"),
    ("q05_board_full", "delivery/next_cycle/n4/T5/q05_board_full.png"),
    ("q05_board_reset", "delivery/next_cycle/n4/T5/q05_board_reset.png"),
    ("q05_board_json", "delivery/next_cycle/n4/T5/q05_board.json"),
    ("q06_stats", "delivery/next_cycle/n4/T5/q06_stats.json"),
    ("q07_edit", "delivery/next_cycle/n4/T5/q07_archive_report.json"),
    ("q07_diff", "delivery/next_cycle/n4/T5/q07_diff.json"),
    ("q07_edited_bench", "delivery/next_cycle/n4/T5/q07_edited_bench.png"),
    ("q07_restored_bench", "delivery/next_cycle/n4/T5/q07_restored_bench.png"),
    ("q08_binding", "delivery/next_cycle/n4/T5/q08_evidence_binding.json"),
    ("q09_landscape", "delivery/next_cycle/n4/T5/q09_landscape_1280x720.png"),
    ("q09_portrait", "delivery/next_cycle/n4/T5/q09_portrait_720x1280.png"),
    ("q09_viewports", "delivery/next_cycle/n4/T5/q09_viewports.json"),
    ("quality_assessment", "delivery/next_cycle/n4/T5/quality_check_n4.json"),
    ("lighting_settings", "delivery/next_cycle/n4/T2/lighting_settings_finalN4.json"),
    ("finalN4_shots", "delivery/next_cycle/n4/T3/game_finalN4_shots.json"),
    ("capture_bindings_summary", "art_review/submissions/candidate_n4/bindings/summary.json"),
    ("finalN4_binding_formal_no_ui", "art_review/submissions/candidate_n4/bindings/binding_formal_no_ui.json"),
    ("finalN4_binding_formal_ui", "art_review/submissions/candidate_n4/bindings/binding_formal_ui.json"),
    ("finalN4_binding_dialogue", "art_review/submissions/candidate_n4/bindings/binding_dialogue.json"),
    ("build_report", sorted((ROOT / "delivery/performance").glob("cocos_build_20261025_*.json"))[-1].relative_to(ROOT).as_posix()),
    ("build_log", "tools/cocos/logs/build_web_desktop_n4.log"),
    ("catalog_review_sample", "art/iterations/cycle_04/reviews/ENV006.json"),
    ("n06_evidence_index", "delivery/next_cycle/n4/N06_evidence_index.json"),
    ("mat_finalN4_ENV001", "delivery/next_cycle/n4/T3/mat_finalN4_ENV001.png"),
    ("mat_finalN4_ENV006", "delivery/next_cycle/n4/T3/mat_finalN4_ENV006.png"),
]
idx0 = {
    "kind": "n06_n4_evidence_index",
    "candidate": "candidate_n4",
    "source_candidate": "candidate_n2",
    "review_focus": ["N01 geometry", "N02 material/light", "N03 UI", "N09 pause/resume", "MIX"],
    "artifacts": {r: sha(p) for r, p in artifacts if p != "delivery/next_cycle/n4/N06_evidence_index.json"},
    "note": "Producer evidence index; not independent approval.",
}
(ROOT / "delivery/next_cycle/n4/N06_evidence_index.json").write_text(
    json.dumps(idx0, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
missing = [p for _, p in artifacts if not (ROOT / p).is_file()]
print("missing", missing)
assert not missing
spec = {
    "stage": "art_complete",
    "character_mode": "reference_spine",
    "production_methods": ["reference_spine", "blender_editable", "cocos_scene_edit", "svg_editable", "existing_asset_import"],
    "artifacts": [{"role": r, "path": p} for r, p in artifacts],
}
out = ROOT / "art_review/submissions/candidate_n4/spec.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
idx = {
    "kind": "n06_n4_evidence_index",
    "candidate": "candidate_n4",
    "source_candidate": "candidate_n2",
    "build_report": spec["artifacts"][-3]["path"],
    "review_focus": ["N01 geometry", "N02 material/light", "N03 UI", "N09 pause/resume", "MIX"],
    "artifacts": {r: sha(p) for r, p in artifacts},
    "note": "Producer evidence index; not independent approval.",
}
(ROOT / "delivery/next_cycle/n4/N06_evidence_index.json").write_text(
    json.dumps(idx, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("spec", out)
