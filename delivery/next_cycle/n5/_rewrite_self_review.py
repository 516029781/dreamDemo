import pathlib

p = pathlib.Path('delivery/next_cycle/n5/make_n5_self_review.py')
s = p.read_text(encoding='utf-8')
start = s.index('SCORES = {')
end = s.index('ISSUE_EVIDENCE = {')

new = '''SCORES = {
    "ENV": {"composition_scale": 3, "geometry_craft": 3, "material_separation": 3,
            "lighting_contact": 3, "vegetation_depth": 4, "play_readability": 4},
    "CHAR": {"silhouette_proportion": 4, "line_quality": 4, "cel_color_light": 4,
             "identity_consistency": 4, "motion_contact": 3, "small_scale_clarity": 3},
    "UI": {"paper_shape": 4, "doodle_icon_family": 3, "typography": 3,
           "layout_air": 4, "state_feedback": 4, "palette_restraint": 3},
    "MIX": {"visual_language": 3, "color_light_coherence": 3, "grounding_occlusion": 4,
            "focus_readability": 3, "world_style_coherence": 3},
}

REASONS = {
    "ENV": {
        "composition_scale": (
            "Grouped paving repairs (2-4 adjacent dark slabs per module), bunting lines and two glazed jars break the single-bond grid; the near rail was moved to z=-8.8 but still projects below the frame.",
            "No foreground object enters the bottom of frame, so the paving still runs to the edge; the reference uses stairs and rails as a foreground band.",
            "Accepted at 3: colours and repairs improved, but the composition gap the user called out (P9) is only half closed.",
            [NO_UI, "delivery/next_cycle/n5/T4/N01_geometry_before_after.png"]),
        "geometry_craft": (
            "The smooth crown core is deleted (mesh count confirms MAP001_tree_crown_mass is gone); the interior is now 34 inner leaf clusters on recorded anchors.",
            "From the game camera the crown still reads top-heavy; the lower crown was not re-checked with a silhouette render this round.",
            "Accepted at 3.",
            ["art/candidates/candidate_n5/previews/environment/tree_ablation/C_gameplay.png", NO_UI]),
        "material_separation": (
            "Stone albedo darkened (base #A79B88, dark #6F6455, mortar #7E7364), soil darkened to #4C3A2B; the paved field now measures #A08B6C against the reference range #897161 to #D6C0A7.",
            "Cracks, moss and edge wear are still absent; the largest surface has tone and repair groups but little incident.",
            "Accepted at 3.",
            ["delivery/next_cycle/n5/T4/N02_material_closeups.png", NO_UI]),
        "lighting_contact": (
            "Vertex-colour AO ships in the GLB (all 473 primitives carry COLOR_0): roots darken by height, downward foliage faces darken, and ground within 0.45 m of solid props gets a contact ring (4,396 ground vertices, min factor 0.58).",
            "Highlights remain low: frame p95 is 0.741 against the 0.80 target, so the strongest 5% of the picture still looks flat.",
            "Accepted at 3: grounding is real, the contrast target is not met.",
            [NO_UI, "delivery/next_cycle/n5/T5/q03_front.png"]),
        "vegetation_depth": (
            "Paving gate is per-tuft and audited: vegetation_audit.json totals 4,024 tufts with 0 violations, 0 orphans, 0 audit mismatches.",
            "Margin sward is still patchier than P1 between clumps.",
            "Accepted at 4.",
            ["art/candidates/candidate_n5/vegetation_audit.json", NO_UI]),
        "play_readability": (
            "Route, planter ring, player and NPC stay readable; the character silhouette holds against mid-tone paving.",
            "Paving is still the largest bright area in frame.",
            "Accepted at 4; Q01/Q03/Q04 pass.",
            ["delivery/next_cycle/n5/T5/q03_front.png", "delivery/next_cycle/n5/T5/q03_behind.png"]),
    },
    "CHAR": {
        "silhouette_proportion": ("Locked 1015_aglna2 silhouette unchanged; bbox re-measured at the n5 camera.", "P1 proportion match is close.", "Accepted at 4.", [NO_UI, "delivery/next_cycle/n5/T4/N04_actor_bbox.png"]),
        "line_quality": ("Locked line art preserved without rescale or redraw.", "P1 line weight is slightly cleaner at small scale.", "Accepted at 4.", [NO_UI, "delivery/next_cycle/n5/T4/N04_actor_visible.png"]),
        "cel_color_light": ("Character cel colours intact; the world grade ships as palette plus light, so the character RT is not double-graded.", "Scene light does not shade the character RT.", "Accepted at 4 for the locked source.", [NO_UI, DIALOGUE]),
        "identity_consistency": ("Same locked Spine source and animations.", "None in source identity.", "Accepted at 4.", [NO_UI, "delivery/next_cycle/n5/T6/character_n/N07_animation_sheet.png"]),
        "motion_contact": ("Idle and move hold 6 unique frames with advancing trackTime.", "Contact is a flat blob, not a shaped shadow.", "Accepted at 3.", ["delivery/next_cycle/n5/T6/character_n/N07_animation_sheet.png", "delivery/next_cycle/n5/T5/q04_resume_from_moved_keyboard.png"]),
        "small_scale_clarity": ("Face and silhouette stay readable at the formal size.", "Small accessories lose contrast on pale paving.", "Accepted at 3.", [NO_UI, "delivery/next_cycle/n5/T4/N04_actor_bbox.png"]),
    },
    "UI": {
        "paper_shape": ("Pause card reads as the same torn washi family as the quest card and dialogue; deckle outline reduced to alpha 30.", "Nine-slice stretching widens teeth on very wide panels.", "Accepted at 4.", ["delivery/next_cycle/n5/T4/N03_ui_before_after.png", DIALOGUE]),
        "doodle_icon_family": ("Doodle count cut from four to two on the quest and pause cards, one tape each; the family is shared across panels.", "Still fewer marks than P1 all-over annotation.", "Accepted at 3.", ["delivery/next_cycle/n5/T4/N03_ui_before_after.png", UI]),
        "typography": ("Speaker 34 px serif, body 24 px; no clipping at 1280x720 or 720x1280 in the Q09 captures.", "P1 sets the name heavier with thin rules; not re-measured at final size.", "Accepted at 3.", [DIALOGUE, UI]),
        "layout_air": ("Dialogue pitch keeps the player full pose above the panel.", "Weapon tip ends within about 5 px of the torn edge.", "Accepted at 4.", [DIALOGUE, "delivery/next_cycle/n5/T4/N03_ui_before_after.png"]),
        "state_feedback": ("Pause card alpha lowered to 205 with one tape and two doodles; pause/resume and portrait return pass in Q04.", "The card exposes no sound or restart controls on the panel itself.", "Accepted at 4.", ["delivery/next_cycle/n5/T5/q04_pause_from_moved_keyboard.png", "delivery/next_cycle/n5/T5/q09_portrait_720x1280.png"]),
        "palette_restraint": ("Cream paper, mint accents, gold highlights and ink stay in the scene palette.", "P1 paper is a cooler grey-white over a warm scene.", "Accepted at 3.", [UI, DIALOGUE]),
    },
    "MIX": {
        "visual_language": ("Paving bonds, a leaf-built crown and grouped accents sit closer to the character line quality than n5b.", "The character is still a high-fidelity Spine cutout on flat-shaded low-poly stone.", "Accepted at 3.", [UI, "delivery/next_cycle/n5/T4/N03_ui_before_after.png"]),
        "color_light_coherence": ("Hue moved into the reference range: 0-30 deg share 0.349 (target at least 0.25, was 0.067); shadow tint sits at hue 20.", "Frame p95 0.741 (below 0.80) and saturation 0.421 (reference 0.275) still read flatter and more ochre than P1; the screen-space grade that would have closed this was blocked by the legacy pipeline (decisions n5d-s1).", "Accepted at 3: hue direction fixed, the reference brightness and contrast are not delivered.", [NO_UI, UI]),
        "grounding_occlusion": ("Vertex AO plus the projected crown decal ground props; Q03 behind-tree occlusion passes.", "Props other than the tree still use soft ambient blobs.", "Accepted at 4.", ["delivery/next_cycle/n5/T4/N02_shadow_before_after.png", "delivery/next_cycle/n5/T5/q03_behind.png"]),
        "focus_readability": ("Character, route, dialogue and next button stay the focal chain.", "Paving is still the brightest region.", "Accepted at 3.", [UI, DIALOGUE]),
        "world_style_coherence": ("Paper, hedge and paving share one warm autumn key with value separation between stone and earth.", "World surface detail remains a step below the character art.", "Accepted at 3.", [UI, "delivery/next_cycle/n5/T4/N01_geometry_before_after.png"]),
    },
}

'''

s = s[:start] + new + s[end:]
s = s.replace('"stage": "art_complete", "round": 7,', '"stage": "art_complete", "round": 8,')
old_gaps = '''        "known_gaps": [
            "Flat backdrop plane above the treeline; the horizon still reads as a wall.",
            "Crown is mushroom-shaped with a bare branch skirt below the foliage.",
            "Mortar grid still dominates the largest surface in frame.",
            "Functional prop clusters along the route edge were deferred for run budget.",
            "WeChat real-device performance is still untested (Q09 device_tested=false).",
        ],'''
new_gaps = '''        "known_gaps": [
            "Frame p95 0.741 below the 0.80 target and saturation 0.421 above the reference 0.275; the screen-space grade was blocked by the legacy pipeline.",
            "No foreground object enters the bottom of frame; the near rail sits below the view.",
            "Leaf-card atlas (S4) was not delivered; foliage still uses flat-colour folded cards.",
            "Cracks, moss and edge wear on stone remain procedural mottle only.",
            "Far treeline reads as dark rounded lumps above the hedge.",
            "WeChat real-device performance is still untested (Q09 device_tested=false).",
        ],'''
assert old_gaps in s
s = s.replace(old_gaps, new_gaps)
p.write_text(s, encoding='utf-8')
print('self review replaced')
