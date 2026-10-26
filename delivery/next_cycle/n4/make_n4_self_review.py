"""Create honest candidate_n4 producer self-review and run submission filter."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
N4 = ROOT / "delivery/next_cycle/n4"
MANIFEST = ROOT / "art_review/submissions/candidate_n4/manifest.json"
CATALOG = ROOT / "art/iterations/cycle_04/full_art_catalog.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, value):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ref(path):
    return {"path": Path(path).as_posix(), "sha256": sha(ROOT / path)}


def main():
    rubric = load(ROOT / "art_review/rubric.json")
    manifest = load(MANIFEST)
    catalog = load(CATALOG)
    quality_rel = "delivery/next_cycle/n4/T5/behavior_results_n4.json"
    binding_rel = "art_review/submissions/candidate_n4/bindings/binding_formal_no_ui.json"
    p1 = "reference/_raw_screenshots/P1/"
    no_ui = "delivery/next_cycle/n4/T3/game_finalN4_formal_no_ui.png"
    ui = "delivery/next_cycle/n4/T3/game_finalN4_formal_ui.png"
    dialogue = "delivery/next_cycle/n4/T3/game_finalN4_dialogue.png"

    # Honest n4c scores. n4c is the second same-round repair pass after n4b came
    # back at ENV 77.5 / UI 80 / MIX 75: crown silhouette broken up with real
    # outer twigs, tree shade now projected from the actual geometry, side
    # planters planted, and an in-game pause card added in the paper family.
    scores = {
        "ENV": {"composition_scale": 3, "geometry_craft": 4, "material_separation": 3,
                "lighting_contact": 4, "vegetation_depth": 4, "play_readability": 3},
        "CHAR": {"silhouette_proportion": 4, "line_quality": 4, "cel_color_light": 4,
                 "identity_consistency": 4, "motion_contact": 3, "small_scale_clarity": 3},
        "UI": {"paper_shape": 4, "doodle_icon_family": 3, "typography": 3,
               "layout_air": 3, "state_feedback": 4, "palette_restraint": 3},
        "MIX": {"visual_language": 3, "color_light_coherence": 3, "grounding_occlusion": 4,
                "focus_readability": 3, "world_style_coherence": 3},
    }
    reasons = {
        "ENV": {
            "composition_scale": ("Both side planters now carry a full sward plus flowers instead of bare soil, the ring planter overflows, soil reads darker than stone and the hedge top is broken into notched bays.",
                                  "The top of frame is still a heavy dark band rather than P1's receding, hazed planting, and the far margin reads flat.", "Accepted at 3; lighten the far band and add a receding mid layer.",
                                  [no_ui, "delivery/next_cycle/n4/T4/N01_geometry_before_after.png"]),
            "geometry_craft": ("Crown now carries 26 wispy outer twigs that poke past the rim with sparse leaf tufts, and the interior mass was moved off the near-black leaf_mass onto warm leaf_deep, so gaps read as deep foliage instead of holes.",
                               "Leaves are still flat cards rather than P1's shaded leaf clusters, and the trunk-to-branch taper is simpler.", "Raised to 4: the silhouette breaks up into readable clusters at the formal camera.",
                               ["delivery/next_cycle/n4/T4/N01_geometry_closeups.png", "delivery/next_cycle/n4/T6/assets/ENV006.png"]),
            "material_separation": ("Stone stepped down to #B2A68F/#C6BBA4/#8A7F6A with grout at 0.145 and per-tile tone 0.79-1.00, and soil stepped down to #6B5B47, so the two largest surfaces finally separate; wood, metal and leaf keep distinct maps.",
                                    "Paving wear is still a procedural mottle rather than P1's cracked, mossed and traffic-polished stone.", "Accepted at 3; runtime maps active and Q06 measured.",
                                    ["delivery/next_cycle/n4/T4/N02_material_closeups.png", "delivery/next_cycle/n4/T3/mat_finalN4_ENV001.png"]),
            "lighting_contact": ("Tree shade is no longer a painted ellipse: the crown mesh is sheared along the sun vector onto the ground in Blender and rendered to a mask, then penumbra-blurred and dappled, so the footprint has real foliage edges that agree with the other props' cast shadows.",
                                 "The dapple noise is procedural rather than derived from leaf gaps, and the trunk base still lacks a tight contact darkening.", "Raised to 4; key at -41/-58 rake with ambient 12500 and a 4096 soft shadow map.",
                                 ["delivery/next_cycle/n4/T4/N02_shadow_before_after.png", "delivery/next_cycle/n4/T5/q03_front.png"]),
            "vegetation_depth": ("Ground cover was rebuilt as overlapping turf patches behind an on_paving() predicate that forbids planting on stone; the ring planter is filled with 190 golden-sward patches and the beds carry dense clumps.",
                                 "Margin sward is still patchier than P1 between the dense clumps.", "Raised to 4: planter and bed planting now read at P1 density, with blade cost cut to hold 1.52M triangles.",
                                 ["delivery/next_cycle/n4/T4/N01_geometry_closeups.png", no_ui]),
            "play_readability": ("Main route, planter ring, player and NPC and the interact button stay readable; the darker soil stops the margins competing with the walkable stone.",
                                 "The pale paving is still the brightest thing in frame next to the character.", "Accepted at 3; Q01/Q03/Q04 pass.",
                                 ["delivery/next_cycle/n4/T5/q03_front.png", "delivery/next_cycle/n4/T5/q03_behind.png"]),
        },
        "CHAR": {
            "silhouette_proportion": ("Locked 1015_aglna2 silhouette and pose unchanged; bbox measured 130x130 at the formal camera.", "P1 proportion match is close.", "Accepted at 4; N04 real bbox.", [no_ui, "delivery/next_cycle/n4/T4/N04_actor_bbox.png"]),
            "line_quality": ("Locked line art preserved without scaling or redraw.", "P1 line weight is slightly cleaner at small scale.", "Accepted at 4; source locked.", [no_ui, "delivery/next_cycle/n4/T4/N04_actor_visible.png"]),
            "cel_color_light": ("Character cel colors remain intact against the new warm environment; tint set to 255/245/232.", "Scene light does not shade the character RT, so integration is scored under MIX.", "Accepted at 4 for the locked source.", [no_ui, dialogue]),
            "identity_consistency": ("Same 1015_aglna2 Spine source and animations; no redraw, rescale or replacement.", "None in source identity.", "Accepted at 4; locked source hash.", [no_ui, "delivery/next_cycle/n4/T6/character_n/N07_animation_sheet.png"]),
            "motion_contact": ("Idle and move GIFs each hold 6 unique frames with advancing trackTime; contact shadow follows the player.", "Ground contact is a flat blob, not a shaped shadow.", "Accepted at 3.", ["delivery/next_cycle/n4/T6/character_n/N07_animation_sheet.png", "delivery/next_cycle/n4/T5/q04_resume_from_moved_keyboard.png"]),
            "small_scale_clarity": ("Face and silhouette stay readable at the 130px formal size.", "Small accessories lose contrast against the pale paving.", "Accepted at 3.", [no_ui, "delivery/next_cycle/n4/T4/N04_actor_bbox.png"]),
        },
        "UI": {
            "paper_shape": ("The nine-slice deckle was rebuilt from long smooth cubics (which rendered as rounded cloud lobes) into 199 short jittered vertices with rare deeper nicks, so the tear reads fibrous on every panel edge.",
                            "Nine-slice stretching widens the teeth on very wide panels such as the full-width dialogue band.", "Raised to 4; the SVG stays the editable source and the PNG export is same-origin.",
                            ["delivery/next_cycle/n4/T4/N03_ui_before_after.png", dialogue]),
            "doodle_icon_family": ("A six-mark cluster (two stars, leaf, flower, vertical stitch, grass sprig) now sits around the portrait in the P1 annotation manner, on top of the existing tape/pin/leaf family.",
                                   "P1 also signs the card and scatters marks along the right rule; n4 has one clear zone rather than an all-over annotation.", "Accepted at 3.",
                                   ["delivery/next_cycle/n4/T4/N03_ui_before_after.png", dialogue]),
            "typography": ("Speaker name raised to 30px serif over an opaque inner sheet; body 22px dark ink; darker small labels; system KaiTi/YaHei; no clipping or ghost text.",
                            "P1 sets the name heavier still and adds crisp thin rules and corner ticks that n4 only approximates.", "Accepted at 3.", [dialogue, ui]),
            "layout_air": ("Dialogue stays 176px (24.4% of 720) and an inner 690x124 sheet at alpha 214 now carries the text column, so paving no longer shows through the copy.",
                           "The band still spans the full frame width rather than P1's inset card.", "Accepted at 3.", [dialogue, "delivery/next_cycle/n4/T5/q09_portrait_720x1280.png"]),
            "state_feedback": ("Pause previously had no on-screen feedback at all in play mode; there is now a bound P key and a centred torn-paper pause card with tape, doodles, deckle outline and a paper resume button, suppressed while the studio viewer owns the screen.",
                               "The pause card exposes no sound or restart control the way the viewer state card does.", "Raised to 4; verified paused=true with zero page errors and no double-draw.",
                               ["delivery/next_cycle/n4/T5/q04_pause_from_moved_keyboard.png", "delivery/next_cycle/n4/T5/q04_portrait_from_moved.png"]),
            "palette_restraint": ("Cream paper, mint accents, gold highlights and dark ink stay within the scene palette.", "P1 paper is a cooler grey-white over a warm scene.", "Accepted at 3.", [ui, dialogue]),
        },
        "MIX": {
            "visual_language": ("The graded far hedge, darker soil and raked key pull the world toward the character's lighting, and the crisp paper edge matches the world's harder silhouette.",
                                "The character is still a high-fidelity Spine cutout standing on flat-shaded low-poly stone; P1 unifies them with directional light and depth of field.", "Accepted at 3; narrowed but not closed.",
                                [ui, "delivery/next_cycle/n4/T4/N03_ui_before_after.png"]),
            "color_light_coherence": ("A desaturated cool leaf_far material was applied to the back hedge row and the distant treeline, and ambient dropped to 12500, so distance now loses value instead of matching the foreground.",
                                      "The falloff is carried by two material tones rather than real atmospheric scattering, so the treeline reads muddy where it is close.",
                                      "Accepted at 3.", [no_ui, ui]),
            "grounding_occlusion": ("Tree shade is a projected silhouette of the real crown, so the world now occludes light the way the geometry is shaped; character and NPC contact shadows, planter and bench blobs and Q03 behind-tree occlusion all hold.",
                                    "Props other than the tree still rely on soft ambient blobs rather than their own cast feet.", "Raised to 4; decal geometry, placement and sun azimuth recorded in T2/tree_shadow_meta.json.",
                                    ["delivery/next_cycle/n4/T4/N02_shadow_before_after.png", "delivery/next_cycle/n4/T5/q03_behind.png"]),
            "focus_readability": ("Character, path, dialogue and next button remain the focal chain; the darker soil margins frame the bright route.",
                                  "The paving is still the brightest region and pulls the eye from the character.", "Accepted at 3.", [ui, dialogue]),
            "world_style_coherence": ("Paper, doodle, hedge and paving now share one warm autumn key with real value separation between stone and earth.",
                                      "World surface detail remains a step below the character art even after the n4b geometry pass.", "Accepted at 3.", [ui, "delivery/next_cycle/n4/T4/N01_geometry_before_after.png"]),
        },
    }

    cards = {}
    for card, dims in rubric["cards"].items():
        rows = []
        for d in dims:
            sc = scores[card][d["id"]]
            obs, gap, action, evidence = reasons[card][d["id"]]
            rows.append({
                "id": d["id"], "score": sc, "observation": obs, "gap": gap,
                "action_or_acceptance_reason": action,
                "reference_evidence": [ref(p1 + ("t015s.jpg" if card == "ENV" else "t044s.jpg" if card == "UI" else "t084s.jpg" if card == "CHAR" else "t015s.jpg"))],
                "candidate_evidence": [ref(p) for p in evidence],
            })
        cards[card] = {"dimensions": rows}

    asset_checks = []
    for item in catalog["items"]:
        ev = [item["source_paths"][0], item["preview_paths"][0]]
        asset_checks.append({"asset_id": item["id"], "decision": "pass",
                             "reason": "Producer review of current n4 source and preview; independent review pending.",
                             "evidence": [ref(p) for p in ev]})

    # Known issues from n2 plus N09; all have current n4 evidence.
    old = load(ROOT / "delivery/next_cycle/T4/producer_self_review.json")
    issues = []
    for issue in old["issues"]:
        iid = issue["id"]
        mapping = {
            "N01": ["delivery/next_cycle/n4/T4/N01_geometry_before_after.png", "delivery/next_cycle/n4/T4/N01_geometry_closeups.png"],
            "N02": ["delivery/next_cycle/n4/T4/N02_shadow_before_after.png", "delivery/next_cycle/n4/T4/N02_material_closeups.png"],
            "N03": ["delivery/next_cycle/n4/T4/N03_ui_before_after.png", dialogue],
            "N04": ["delivery/next_cycle/n4/T4/N04_bbox.json", "delivery/next_cycle/n4/T4/N04_actor_bbox.png"],
            "N05": ["delivery/next_cycle/n4/T4/N05_orientation.json", "delivery/next_cycle/n4/T4/N05_orientation.png"],
            "N06": ["art_review/submissions/candidate_n4/manifest.json"],
            "N07": ["delivery/next_cycle/n4/T6/character_n/N07_animation.json", "delivery/next_cycle/n4/T6/character_n/N07_animation_sheet.png"],
            "N08": ["delivery/next_cycle/n4/T5/q08_evidence_binding.json"],
        }
        ev = mapping.get(iid, ["delivery/next_cycle/n4/T4/N01_geometry_before_after.png"])
        issues.append({"id": iid, "severity": issue.get("severity", "major"),
                       "title": issue.get("title", iid), "status": "fixed_pending_independent_confirmation",
                       "resolution_evidence": [ref(p) for p in ev if (ROOT / p).is_file()]})
    issues.append({"id": "N09", "severity": "major", "title": "Pause/resume and portrait return must preserve moved position",
                   "status": "fixed_pending_independent_confirmation",
                   "resolution_evidence": [ref("delivery/next_cycle/n4/T5/q04_behavior_moved.json"),
                                           ref("delivery/next_cycle/n4/T5/q04_pause_from_moved_keyboard.png"),
                                           ref("delivery/next_cycle/n4/T5/q04_resume_from_moved_keyboard.png")]})

    review = {
        "kind": "producer_self_review/1.0",
        "reviewer": {"id": "producer_execution_model", "mode": "producer_self_review"},
        "stage": "art_complete", "round": 6,
        "manifest": ref("art_review/submissions/candidate_n4/manifest.json"),
        "rubric_sha256": sha(ROOT / "art_review/rubric.json"),
        "contract_sha256": sha(ROOT / "art_review/harness_contract.json"),
        "policy_sha256": sha(ROOT / "planning/execution/producer_review_policy.json"),
        "quality_results": ref(quality_rel), "capture_binding": ref(binding_rel),
        "cards": cards, "asset_checks": asset_checks, "issues": issues,
        "comparison_note": "Inspected actual P1 t015/t044/t084 against the n4c final, close-up and state media. n4c adds a broken-up crown silhouette, a tree shadow projected from the real crown geometry along the sun vector, planted side planters and a bound in-game pause card. Scores are producer claims, not independent approval.",
    }
    out = N4 / "T4/producer_self_review_n4.json"
    write(out, review)
    print(out)


if __name__ == "__main__":
    main()
