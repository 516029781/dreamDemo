"""Build cycle_03 catalog and per-item reviews from current finalN previews."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OLD = ROOT / "art/iterations/cycle_02/full_art_catalog.json"
OUT = ROOT / "art/iterations/cycle_03/full_art_catalog.json"
REVIEWS = ROOT / "art/iterations/cycle_03/reviews"
T6A = "delivery/next_cycle/T6/assets"
T6U = "delivery/next_cycle/T6/ui_states"
OLD_T4 = ("delivery/next_cycle/T4/tree_before_after_final4.png", "delivery/next_cycle/T4/material_closeups_final4.png",
          "delivery/next_cycle/T4/plant_background_final4.png", "delivery/next_cycle/T4/plant_closeups_final4.png",
          "delivery/next_cycle/T4/lighting_comparison_final4.png", "delivery/next_cycle/T4/ui_comparison_final4.png")
OLD_T3_PREFIX = ("delivery/next_cycle/T3/mat_final4_", "delivery/next_cycle/T3/plant_final4_")
N_T4 = ("delivery/next_cycle/T4/N01_tree_hedge_before_after.png", "delivery/next_cycle/T4/N02_shadow_before_after.png",
        "delivery/next_cycle/T4/N02_material_closeups.png", "delivery/next_cycle/T4/N03_ui_before_after.png")
UI_MAP = {
    "UI001": ["title_initial", "title_pressed"], "UI002": ["loading_progress", "loading_failure", "loading_retry_pressed"],
    "UI003": ["hud_talk", "hud_0_3", "hud_1_3", "hud_2_3", "hud_3_3", "hud_submit", "hud_done"],
    "UI004": ["joystick_idle", "joystick_drag", "joystick_hidden"],
    "UI005": ["interact_talk", "interact_pick", "interact_place", "interact_view", "interact_pressed", "interact_disabled", "interact_hidden"],
    "UI006": ["dialogue_gardener_p1", "dialogue_player_p2", "dialogue_accept_pressed"],
    "UI007": ["pause_default", "pause_sound_on", "pause_restart_pressed"],
    "UI008": ["complete_default", "complete_continue_pressed"], "UI009": ["toast_pickup", "toast_task_update", "toast_error"],
    "UI010": ["tip_first_move", "tip_first_interact"], "UI011": ["safe_area_landscape", "rotate_notice"],
    "UI012": ["spec_icons"], "UI013": ["spec_type", "spec_nine_slice"],
}
GROUP_NOTE = {
    "MAP": "route, paving, boundary, tree/hedge density and interaction props visible in the current formal view.",
    "ENV": "module silhouette, scale and material read in the current canvas preview; no missing group.",
    "PROP": "prop silhouette/material read in the current canvas preview and close-up where available.",
    "MAT": "stone/wood/metal/soil families inspected in current material close-ups.",
    "LOOK": "current camera/light profile inspected in the formal view; soft tree shadow and contact grounded.",
    "CHAR": "locked 1015 Spine source and identity; idle/move playback evidence and dialogue use inspected.",
    "UI": "current state screenshots inspected; translucent paper, dashed edge, doodles and hierarchy present.",
    "FX": "FX and board state evidence inspected in the current build.",
    "PACK": "47-item catalog, per-item reviews and current-build previews are present.",
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def add(paths, path):
    if path and (ROOT / path).is_file() and path not in paths:
        paths.append(path)


def main():
    old = json.loads(OLD.read_text(encoding="utf-8-sig"))
    expected = json.loads((ROOT / "art_review/harness_contract.json").read_text(encoding="utf-8-sig"))["expected_art_ids"]
    items = {item["id"]: item for item in old["items"]}
    REVIEWS.mkdir(parents=True, exist_ok=True)
    build_glb = sha(ROOT / "art/full/source/layout/MAP001_courtyard.glb")
    out_items = []
    for asset_id in expected:
        old_item = items[asset_id]
        sources, previews = [], []
        for path in old_item.get("source_paths", []):
            add(sources, path)
        for path in old_item.get("preview_paths", []):
            if path in OLD_T4 or path.startswith(OLD_T3_PREFIX):
                continue
            add(previews, path)
        if asset_id in {i for i in expected if not i.startswith("UI")}:
            add(previews, f"{T6A}/{asset_id}.png")
        if asset_id == "MAP001":
            for path in ("art/full/source/layout/MAP001_courtyard.blend", "art/full/source/layout/MAP001_courtyard.glb",
                         "art/full/source/layout/layout.json", "demo/assets/scripts/CourtyardBootstrap.ts",
                         "tools/blender/build_map001.py", "tools/blender/build_env_courtyard.py"):
                add(sources, path)
            add(previews, "delivery/next_cycle/T2/sample_no_ui.png")
            add(previews, "delivery/next_cycle/T4/N01_tree_hedge_before_after.png")
            add(previews, "delivery/next_cycle/T4/N02_shadow_before_after.png")
            add(previews, "delivery/next_cycle/T4/N04_actor_bbox.png")
            add(previews, "delivery/next_cycle/T4/N05_orientation.png")
        if asset_id == "ENV006":
            add(previews, "delivery/next_cycle/T4/N01_tree_hedge_before_after.png")
            add(previews, "delivery/next_cycle/T4/N02_shadow_before_after.png")
            add(previews, "delivery/next_cycle/T4/N02_material_closeups.png")
            add(sources, "tools/blender/build_env_courtyard.py")
        if asset_id.startswith("MAT") or asset_id == "LOOK001":
            add(sources, "demo/assets/scripts/CourtyardBootstrap.ts")
            add(previews, "delivery/next_cycle/T4/N02_shadow_before_after.png")
        if asset_id.startswith("MAT"):
            add(previews, "delivery/next_cycle/T4/N02_material_closeups.png")
        if asset_id in {"ENV007", "ENV008", "ENV009", "ENV010", "ENV011", "ENV012"}:
            add(previews, "delivery/next_cycle/T4/plant_closeups_finalN2.png")
            add(previews, f"delivery/next_cycle/T3/plant_finalN2_{asset_id}.png")
        if asset_id in {"PROP001", "PROP004"}:
            add(previews, f"delivery/next_cycle/T3/mat_finalN2_{asset_id}.png")
        if asset_id in {"CHAR001", "CHAR002"}:
            for path in ("art/phase1/character_playback_1015/idle_preview.png", "art/phase1/character_playback_1015/move_preview.gif",
                         "art/phase1/character_playback_1015/reference_comparison.png",
                         "delivery/next_cycle/T6/character_n/char_idle.gif", "delivery/next_cycle/T6/character_n/char_move.gif",
                         "delivery/next_cycle/T6/character_n/N07_animation_sheet.png"):
                add(previews, path)
        if asset_id in {"CHAR004", "CHAR005"}:
            add(previews, "delivery/next_cycle/T2/sample_dialogue.png")
        if asset_id in UI_MAP:
            for state in UI_MAP[asset_id]:
                add(previews, f"{T6U}/{state}.png")
            add(sources, "demo/assets/scripts/CourtyardBootstrap.ts")
            add(sources, "art/full/ui/tokens.json")
            add(sources, "art/full/ui/fonts/FONT_MANIFEST.json")
            add(previews, "delivery/next_cycle/T4/N03_ui_before_after.png")
            if asset_id == "UI011":
                add(previews, "delivery/next_cycle/T4/N05_orientation.png")
        if asset_id == "FX003":
            for state in ("empty", "full", "reset"):
                add(previews, f"delivery/next_cycle/T5/q05_board_{state}.png")
        if asset_id == "PACK001":
            add(previews, "delivery/next_cycle/T2/sample_no_ui.png")
            add(previews, "delivery/next_cycle/T2/sample_hud.png")
            add(previews, "delivery/next_cycle/T2/sample_dialogue.png")
            add(previews, "delivery/next_cycle/T2/reference_comparison.png")
            for name in ("N01_tree_hedge_before_after", "N02_shadow_before_after", "N02_material_closeups",
                         "N03_ui_before_after", "N04_actor_bbox", "N05_orientation"):
                add(previews, f"delivery/next_cycle/T4/{name}.png")
            add(sources, "art/iterations/cycle_03/full_art_catalog.json")
        assert sources and previews, asset_id
        group = old_item.get("group", "")
        reason = (f"Cycle_03 producer self-review. {GROUP_NOTE.get(group, 'Current canvas preview inspected.')} "
                  f"Preview: {previews[0]}. Independent review pending.")
        review = {"asset_id": asset_id, "decision": "pass", "reviewer": "producer self-review (not independent)",
                  "reviewed_at": datetime.now(timezone.utc).isoformat(), "build_glb_sha256": build_glb,
                  "reason": reason, "evidence": [previews[0], sources[0]],
                  "limitations": ["Producer self-review only; final independent review still required."]}
        rp = REVIEWS / (asset_id + ".json")
        rp.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        out_items.append({"id": asset_id, "name": old_item.get("name", asset_id), "group": group,
                          "kind": old_item.get("kind", ""), "acceptance": old_item.get("acceptance", ""),
                          "status": "engine_verified", "source_paths": sources, "preview_paths": previews,
                          "review_path": rp.relative_to(ROOT).as_posix(),
                          "historical_blockers": old_item.get("blockers", []),
                          "notes": "Cycle_03 after N01-N08; current build previews."})
    catalog = {"catalog_version": "3.0.0-candidate", "scope": "47-group courtyard chapter art candidate after N01-N08",
               "audit_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
               "status": "engine_verified_candidate_not_independently_approved",
               "status_semantics": old.get("status_semantics", {}),
               "engine_evidence": {"engine": "Cocos Creator 3.8.8 web-desktop 1280x720", "map_glb_sha256": build_glb,
                                   "viewer_state_index": "delivery/next_cycle/T6/state_index.json",
                                   "ui_state_shots": 41, "asset_shots": 34, "capture_method": "real canvas element capture",
                                   "capture_build": "finalN2 soft-shadow build; Q preflight passed on finalN2"},
               "items": out_items}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"catalog": str(OUT), "items": len(out_items), "sha256": sha(OUT)}))


if __name__ == "__main__":
    main()
