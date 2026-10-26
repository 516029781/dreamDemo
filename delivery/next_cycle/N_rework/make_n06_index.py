"""Write the N06 per-dimension evidence index."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
P = "delivery/next_cycle/"

d = {
    "kind": "n06_self_review_evidence_index",
    "stage": "art_complete",
    "build": "finalN2 (Cocos 3.8.8 web-desktop, 1280x720)",
    "note": "Candidate-side evidence only; reference frames are separate and never composited into candidate pixels.",
    "cards": {
        "ENV": {
            "composition_scale": {
                "observation": "Central tree, main paving route, planter/bench/fence groups read at the formal camera; P1 t015 still has a denser foreground layer and more nested platform depth.",
                "evidence": [P+"T2/sample_no_ui.png", P+"T4/N01_tree_hedge_before_after.png", "reference/_raw_screenshots/P1/t015s.jpg"]},
            "geometry_craft": {
                "observation": "Branch depth 3 and card clusters are visible, but crown mass, planter rim and bench remain faceted/simple at formal scale.",
                "evidence": ["delivery/next_cycle/T6/assets/ENV006.png", P+"T3/mat_finalN2_ENV006.png", P+"T4/N01_tree_hedge_before_after.png", "reference/_raw_screenshots/P1/t015s.jpg"]},
            "material_separation": {
                "observation": "Stone, wood, metal and soil have distinct texture/roughness; metal still flattens at distance and wear is simpler than P1.",
                "evidence": [P+"T4/N02_material_closeups.png", P+"T3/mat_finalN2_ENV001.png", P+"T3/mat_finalN2_PROP001.png", P+"T3/mat_finalN2_PROP004.png", "reference/_raw_screenshots/P1/t015s.jpg"]},
            "lighting_contact": {
                "observation": "Soft dappled tree shadow and contact shadow replace blocky crown shadow; ambient bounce and long cast shadow remain limited.",
                "evidence": [P+"T4/N02_shadow_before_after.png", P+"T2/sample_no_ui.png", P+"T5/q03_front.png", P+"T5/q03_behind.png", "reference/_raw_screenshots/P1/t015s.jpg"]},
            "vegetation_depth": {
                "observation": "Six-lobe crown, outer break clusters, three hedge rows, side-hedge cards and extra groundcover increase front/mid/back separation; foreground is still thinner than P1.",
                "evidence": [P+"T4/N01_tree_hedge_before_after.png", P+"T4/plant_closeups_finalN2.png", "delivery/next_cycle/T6/assets/ENV009.png", "reference/_raw_screenshots/P1/t015s.jpg"]},
            "play_readability": {
                "observation": "Main route and interactables remain legible with HUD on; a few props blend into soil at the far edge.",
                "evidence": [P+"T2/sample_hud.png", P+"T2/sample_no_ui.png", P+"T5/q05_board_full.png", "reference/_raw_screenshots/P1/t084s.jpg"]},
        },
        "CHAR": {
            "silhouette_proportion": {
                "observation": "Locked 1015 Spine silhouette/proportion preserved; real visible bbox 130x130px, target 86-130; no asset scaling.",
                "evidence": [P+"T4/N04_actor_bbox.png", P+"T6/character_n/N07_animation_sheet.png", "delivery/next_cycle/T6/assets/CHAR002.png", "reference/_raw_screenshots/P1/t044s.jpg"]},
            "line_quality": {
                "observation": "Original outline/attachments remain stable at source and in engine; no redraw.",
                "evidence": ["art/phase1/character_playback_1015/idle_preview.png", "delivery/next_cycle/T6/assets/CHAR002.png", "reference/_raw_screenshots/P1/t044s.jpg"]},
            "cel_color_light": {
                "observation": "Source palette is stable; scene real-time light does not tint the character, so integration relies on contact shadow and value separation.",
                "evidence": [P+"T6/character_n/N07_animation_sheet.png", P+"T3/game_finalN2_dialogue.png", "reference/_raw_screenshots/P1/t044s.jpg"]},
            "identity_consistency": {
                "observation": "Same 1015 source, portrait and dialogue identity; no costume/accessory substitution.",
                "evidence": ["art/phase1/character_playback_1015/reference_comparison.png", P+"T6/character_n/N07_animation_sheet.png", P+"T3/game_finalN2_dialogue.png", "reference/_raw_screenshots/P1/t044s.jpg"]},
            "motion_contact": {
                "observation": "Real runtime captures at 500ms: idle 6 unique frames, move 6 unique frames; Spine trackTime advances and bones change. No Spine rebuild.",
                "evidence": [P+"T6/character_n/char_idle.gif", P+"T6/character_n/char_move.gif", P+"T6/character_n/N07_animation_sheet.png", P+"T6/character_n/N07_animation.json", "reference/_raw_screenshots/P1/t084s.jpg"]},
            "small_scale_clarity": {
                "observation": "At 130px the character remains identifiable but fine accessories compress; P1 t084 shows a similar scale without losing the main color blocks.",
                "evidence": [P+"T4/N04_actor_bbox.png", P+"T2/sample_no_ui.png", P+"T6/character_n/N07_animation_sheet.png", "reference/_raw_screenshots/P1/t084s.jpg"]},
        },
        "UI": {
            "paper_shape": {
                "observation": "Panels are translucent with dashed inner edge, fibers and softer outer edge; P1 sheets are thinner and more irregular.",
                "evidence": [P+"T4/N03_ui_before_after.png", P+"T3/game_finalN2_dialogue.png", "delivery/next_cycle/T6/ui_states/dialogue_gardener_p1.png", "reference/_raw_screenshots/P1/t044s.jpg"]},
            "doodle_icon_family": {
                "observation": "Doodle speech/leaf/sparkle marks added around title, dialogue and HUD; the icon family is still smaller than P1's set.",
                "evidence": [P+"T4/N03_ui_before_after.png", "delivery/next_cycle/T6/ui_states/spec_icons.png", "delivery/next_cycle/T6/ui_states/title_initial.png", "reference/_raw_screenshots/P1/t084s.jpg"]},
            "typography": {
                "observation": "Name/body/button hierarchy is consistent and Chinese text is readable at native size; P1 uses more variable hand-set spacing.",
                "evidence": [P+"T3/game_finalN2_dialogue.png", "delivery/next_cycle/T6/state_index.json", "reference/_raw_screenshots/P1/t044s.jpg"]},
            "layout_air": {
                "observation": "HUD stays at task-left/action-right with the play area open; dialogue occupies the lower third and still covers more height than P1.",
                "evidence": [P+"T2/sample_hud.png", P+"T2/sample_no_ui.png", "delivery/next_cycle/T6/ui_states/hud_1_3.png", "reference/_raw_screenshots/P1/t084s.jpg"]},
            "state_feedback": {
                "observation": "41 states captured including pressed, hidden, toast, loading failure/retry, pause and complete; most are look-state evidence, not transition timing.",
                "evidence": ["delivery/next_cycle/T6/state_index.json", "delivery/next_cycle/T6/ui_states/pause_default.png", "delivery/next_cycle/T6/ui_states/complete_default.png", "delivery/next_cycle/T6/ui_states/toast_pickup.png", "reference/_raw_screenshots/P1/t084s.jpg"]},
            "palette_restraint": {
                "observation": "Warm neutrals with mint interaction accent are restrained; P1 is closer to white/gray with small warm color accents.",
                "evidence": [P+"T4/N03_ui_before_after.png", P+"T2/sample_hud.png", "delivery/next_cycle/T6/ui_states/hud_2_3.png", "reference/_raw_screenshots/P1/t084s.jpg"]},
        },
        "MIX": {
            "visual_language": {
                "observation": "Low-poly autumn courtyard and paper UI share a warm, hand-drawn direction; P1 still has richer environment detail and thinner UI.",
                "evidence": [P+"T2/sample_no_ui.png", P+"T3/game_finalN2_dialogue.png", P+"T4/N03_ui_before_after.png", "reference/_raw_screenshots/P1/t044s.jpg"]},
            "color_light_coherence": {
                "observation": "Warm key light, cool fill, soft tree shadow and cream UI are coherent; flat material response reduces bounce light.",
                "evidence": [P+"T4/N02_shadow_before_after.png", P+"T3/game_finalN2_dialogue.png", P+"T2/sample_hud.png", "reference/_raw_screenshots/P1/t015s.jpg"]},
            "grounding_occlusion": {
                "observation": "Contact shadow plus tree occlusion (front/behind) ground the character; silhouette edge still reads as a cutout in some shots.",
                "evidence": [P+"T5/q03_front.png", P+"T5/q03_behind.png", P+"T4/N04_actor_bbox.png", P+"T4/N02_shadow_before_after.png", "reference/_raw_screenshots/P1/t084s.jpg"]},
            "focus_readability": {
                "observation": "Character, task and interact button remain readable; tall foliage occasionally competes at the top edge.",
                "evidence": [P+"T2/sample_hud.png", P+"T5/q05_board_full.png", P+"T2/sample_no_ui.png", "reference/_raw_screenshots/P1/t084s.jpg"]},
            "world_style_coherence": {
                "observation": "Scene, character and UI are consistently stylized; the gap to P1 is detail density and light response, not a style clash.",
                "evidence": [P+"T2/reference_comparison.png", P+"T4/N01_tree_hedge_before_after.png", P+"T4/N03_ui_before_after.png", "reference/_raw_screenshots/P1/t015s.jpg"]},
        },
    },
}

out = ROOT / P / "N_rework/N06_evidence_index.json"
out.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(out)
