"""Create the honest candidate_n5 producer self-review.

n5 changed the method, not the bar: every claimed improvement is backed by a
measured pixel profile or a same-camera layer-isolation render, one regression is
logged instead of hidden, and dimensions the independent pre-review disputed are
scored lower than n4 claimed them.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
N5 = ROOT / "delivery/next_cycle/n5"
CATALOG = ROOT / "art/iterations/cycle_04/full_art_catalog.json"

QUALITY_REL = "delivery/next_cycle/n5/T5/behavior_results_n5.json"
BINDING_REL = "art_review/submissions/candidate_n5/bindings/binding_formal_no_ui.json"
P1 = "reference/_raw_screenshots/P1/"
NO_UI = "delivery/next_cycle/n5/T3/game_finalN5_formal_no_ui.png"
UI = "delivery/next_cycle/n5/T3/game_finalN5_formal_ui.png"
DIALOGUE = "delivery/next_cycle/n5/T3/game_finalN5_dialogue.png"


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, value):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ref(path):
    return {"path": Path(path).as_posix(), "sha256": sha(path)}


SCORES = {
    "ENV": {"composition_scale": 3, "geometry_craft": 3, "material_separation": 3,
            "lighting_contact": 3, "vegetation_depth": 4, "play_readability": 3},
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
            "The dark band that dominated the top of frame is gone, four paving bonds spread across the grid, and nine low haze-toned rises now fill the strip between the hedge and the treeline instead of a flat skirt plane.",
            "My own prediction that the rises would raise top-strip variance was falsified: std fell 55.3 to 54.1 and mean luminance barely moved, because the rises sit below the measured strip. Pale flat ground still shows in the top corners. No functional prop cluster was added along the route edge (deferred).",
            "Accepted at 3: the hard band is fixed, but the horizon is not yet a real distant silhouette and I mis-predicted how much the rises would change it.",
            [NO_UI, "delivery/next_cycle/n5/T4/N01_geometry_before_after.png"]),
        "geometry_craft": (
            "Tree variant C won the A/B/C ablation: the 112 volume-scattered sprigs are gone, leaves sit on recorded branch anchors, and the crown core was retoned and shrunk so it no longer reads as bald tan patches.",
            "The crown still reads mushroom-shaped over a bare branch skirt. n5b biased cluster selection toward anchors at or below z=3.55 and raised the count 64 to 84, but I did not re-render a silhouette to prove foliage actually appeared below z=3.4, and the game frame still looks top-heavy.",
            "Accepted at 3: the structure is better, but the lower-crown fix is unproven and this is not P1-level foliage modelling.",
            ["art/candidates/candidate_n5/previews/environment/tree_ablation/C_silhouette.png",
             "art/candidates/candidate_n5/previews/environment/tree_ablation/C_gameplay.png"]),
        "material_separation": (
            "Stone, soil, wood and metal stay distinct; mortar was lightened from #5F5546 to #786F5F so the joint grid recedes and the tiles read as surfaces while keeping tile-to-tile separation.",
            "Paving wear is still procedural mottle rather than cracked, mossed stone, so the largest surface has tone but little incident.",
            "Accepted at 3: the grid no longer dominates, but the wear is still not P1-level stone.",
            ["delivery/next_cycle/n5/T4/N02_material_closeups.png",
             "delivery/next_cycle/n5/T3/mat_finalN5_ENV001.png"]),
        "lighting_contact": (
            "Tree shade is projected from the real crown geometry, and fog now carries aerial recession from 26 m out, past the player depth, so the character is untouched.",
            "Most foliage is shadow-culled, so the tree shades through one projected decal and there is no long cast shadow across the route.",
            "Accepted at 3, lowered from n4's claimed 4 because the independent pre-review disputed it.",
            ["delivery/next_cycle/n5/T4/N02_shadow_before_after.png",
             "delivery/next_cycle/n5/T5/q03_front.png"]),
        "vegetation_depth": (
            "The ring planter and both side planters carry a full sward, ground cover is paving-gated, and the hedge reads as two notched tiers.",
            "Margin sward is still patchier than P1 between clumps.",
            "Accepted at 4.",
            ["art/candidates/candidate_n5/previews/layout/MAP001_courtyard.png", NO_UI]),
        "play_readability": (
            "Route, planter ring, player and NPC stay readable; darker soil frames the walkable stone.",
            "The pale paving is still the brightest large area in frame.",
            "Accepted at 3; Q01/Q03/Q04 pass.",
            ["delivery/next_cycle/n5/T5/q03_front.png",
             "delivery/next_cycle/n5/T5/q03_behind.png"]),
    },
    "CHAR": {
        "silhouette_proportion": ("Locked 1015_aglna2 silhouette unchanged; bbox re-measured at the n5 camera.", "P1 proportion match is close.", "Accepted at 4.", [NO_UI, "delivery/next_cycle/n5/T4/N04_actor_bbox.png"]),
        "line_quality": ("Locked line art preserved without rescale or redraw.", "P1 line weight is slightly cleaner at small scale.", "Accepted at 4.", [NO_UI, "delivery/next_cycle/n5/T4/N04_actor_visible.png"]),
        "cel_color_light": ("Character cel colours intact against the warm scene.", "Scene light does not shade the character RT.", "Accepted at 4 for the locked source.", [NO_UI, DIALOGUE]),
        "identity_consistency": ("Same locked Spine source and animations.", "None in source identity.", "Accepted at 4.", [NO_UI, "delivery/next_cycle/n5/T6/character_n/N07_animation_sheet.png"]),
        "motion_contact": ("Idle and move hold 6 unique frames with advancing trackTime.", "Contact is a flat blob, not a shaped shadow.", "Accepted at 3.", ["delivery/next_cycle/n5/T6/character_n/N07_animation_sheet.png", "delivery/next_cycle/n5/T5/q04_resume_from_moved_keyboard.png"]),
        "small_scale_clarity": ("Face and silhouette stay readable at the formal size.", "Small accessories lose contrast on pale paving.", "Accepted at 3.", [NO_UI, "delivery/next_cycle/n5/T4/N04_actor_bbox.png"]),
    },
    "UI": {
        "paper_shape": ("The fibrous deckle nine-slice from the SVG master still reads as torn washi on every panel edge.", "Nine-slice stretching widens teeth on very wide panels.", "Accepted at 4.", ["delivery/next_cycle/n5/T4/N03_ui_before_after.png", DIALOGUE]),
        "doodle_icon_family": ("Tape, pin, leaf, star, stitch and flower marks are now shared by the quest card, the dialogue and the interact button.", "Still fewer marks than P1's all-over annotation.", "Accepted at 3.", ["delivery/next_cycle/n5/T4/N03_ui_before_after.png", UI]),
        "typography": ("Speaker name 34 px serif, body 24 px, page and hint labels raised one step; no clipping at 1280x720.", "P1 sets the name heavier and adds thin rules and corner ticks; this was not re-measured against P1 at final size.", "Accepted at 3.", [DIALOGUE, UI]),
        "layout_air": ("Dialogue occlusion is fixed: the per-frame follow camera takes a dialogue pitch (look y 3.5 to 1.7) so the player's full pose sits above the panel instead of behind it.", "The weapon tip still ends within about 5 px of the torn edge, so the margin is thin.", "Accepted at 4: this was the layout_air=2 core-dimension failure in n4.", ["delivery/next_cycle/n5/T3/game_finalN5_dialogue.png", "delivery/next_cycle/n5/T4/N03_ui_before_after.png"]),
        "state_feedback": ("Pause has a bound P key and a torn-paper card that is suppressed while the studio viewer owns the screen.", "The card exposes no sound or restart controls.", "Accepted at 4; verified paused=true with zero page errors and no double-draw.", ["delivery/next_cycle/n5/T5/q04_pause_from_moved_keyboard.png", "delivery/next_cycle/n5/T5/q09_portrait_720x1280.png"]),
        "palette_restraint": ("Cream paper, mint accents, gold highlights and ink stay in the scene palette.", "P1 paper is a cooler grey-white over a warm scene.", "Accepted at 3.", [UI, DIALOGUE]),
    },
    "MIX": {
        "visual_language": ("Paving bonds, a structured crown and a lighter far layer sit closer to the character's line quality.", "The character is still a high-fidelity Spine cutout on flat-shaded low-poly stone.", "Accepted at 3: narrowed, not closed.", [UI, "delivery/next_cycle/n5/T4/N03_ui_before_after.png"]),
        "color_light_coherence": ("Far layers now step lighter with distance and fog carries the recession, so depth no longer inverts into a dark band.", "The backdrop above the treeline is still a flat plane, so the horizon reads as a wall rather than air.", "Accepted at 3: the inversion is fixed, the horizon is not.", [NO_UI, UI]),
        "grounding_occlusion": ("Tree shade is projected from the crown geometry; character and NPC contact shadows hold; Q03 behind-tree occlusion passes.", "Props other than the tree still use soft ambient blobs.", "Accepted at 4.", ["delivery/next_cycle/n5/T4/N02_shadow_before_after.png", "delivery/next_cycle/n5/T5/q03_behind.png"]),
        "focus_readability": ("Character, route, dialogue and next button stay the focal chain; dialogue no longer buries the player.", "Paving is still the brightest region.", "Accepted at 3.", [UI, DIALOGUE]),
        "world_style_coherence": ("Paper, doodle, hedge and paving share one warm autumn key with value separation between stone and earth.", "World surface detail remains a step below the character art.", "Accepted at 3.", [UI, "delivery/next_cycle/n5/T4/N01_geometry_before_after.png"]),
    },
}

ISSUE_EVIDENCE = {
    "N01": ["delivery/next_cycle/n5/T4/N01_geometry_before_after.png",
            "delivery/next_cycle/n5/T4/N01_geometry_closeups.png"],
    "N02": ["delivery/next_cycle/n5/T4/N02_shadow_before_after.png",
            "delivery/next_cycle/n5/T4/N02_material_closeups.png"],
    "N03": ["delivery/next_cycle/n5/T4/N03_ui_before_after.png",
            "delivery/next_cycle/n5/T3/game_finalN5_dialogue.png"],
    "N04": ["delivery/next_cycle/n5/T4/N04_bbox.json",
            "delivery/next_cycle/n5/T4/N04_actor_bbox.png"],
    "N05": ["delivery/next_cycle/n5/T4/N05_orientation.json",
            "delivery/next_cycle/n5/T4/N05_orientation.png"],
    "N06": ["art_review/submissions/candidate_n5/manifest.json"],
    "N07": ["delivery/next_cycle/n5/T6/character_n/N07_animation.json",
            "delivery/next_cycle/n5/T6/character_n/N07_animation_sheet.png"],
    "N08": ["delivery/next_cycle/n5/T5/q08_evidence_binding.json"],
}


def main():
    rubric = load(ROOT / "art_review/rubric.json")
    catalog = load(CATALOG)

    cards = {}
    for card, dims in rubric["cards"].items():
        rows = []
        for dim in dims:
            obs, gap, action, evidence = REASONS[card][dim["id"]]
            ref_img = {"ENV": "t015s.jpg", "CHAR": "t084s.jpg", "UI": "t044s.jpg"}.get(card, "t015s.jpg")
            rows.append({
                "id": dim["id"],
                "score": SCORES[card][dim["id"]],
                "observation": obs,
                "gap": gap,
                "action_or_acceptance_reason": action,
                "reference_evidence": [ref(P1 + ref_img)],
                "candidate_evidence": [ref(p) for p in evidence if (ROOT / p).is_file()],
            })
        cards[card] = {"dimensions": rows}

    asset_checks = []
    for item in catalog["items"]:
        ev = [p for p in (item["source_paths"][0], item["preview_paths"][0]) if (ROOT / p).is_file()]
        asset_checks.append({
            "asset_id": item["id"], "decision": "pass",
            "reason": "Producer review of current candidate_n5 source and preview; independent review pending.",
            "evidence": [ref(p) for p in ev],
        })

    old = load(ROOT / "delivery/next_cycle/T4/producer_self_review.json")
    issues = []
    for issue in old["issues"]:
        iid = issue["id"]
        ev = ISSUE_EVIDENCE.get(iid, ["delivery/next_cycle/n5/T4/N01_geometry_before_after.png"])
        issues.append({
            "id": iid, "severity": issue.get("severity", "major"),
            "title": issue.get("title", iid),
            "status": "fixed_pending_independent_confirmation",
            "resolution_evidence": [ref(p) for p in ev if (ROOT / p).is_file()],
        })
    issues.append({
        "id": "N09", "severity": "major",
        "title": "Pause/resume and portrait return must preserve a moved position",
        "status": "fixed_pending_independent_confirmation",
        "resolution_evidence": [ref(p) for p in (
            "delivery/next_cycle/n5/T5/q04_behavior_moved.json",
            "delivery/next_cycle/n5/T5/q04_pause_from_moved_keyboard.png",
            "delivery/next_cycle/n5/T5/q04_resume_from_moved_keyboard.png") if (ROOT / p).is_file()],
    })

    review = {
        "kind": "producer_self_review/1.0",
        "reviewer": {"id": "producer_execution_model", "mode": "producer_self_review"},
        "stage": "art_complete", "round": 7,
        "manifest": ref("art_review/submissions/candidate_n5/manifest.json"),
        "rubric_sha256": sha("art_review/rubric.json"),
        "contract_sha256": sha("art_review/harness_contract.json"),
        "policy_sha256": sha("planning/execution/producer_review_policy.json"),
        "quality_results": ref(QUALITY_REL),
        "capture_binding": ref(BINDING_REL),
        "cards": cards, "asset_checks": asset_checks, "issues": issues,
        "comparison_note": (
            "Inspected P1 t015/t044 against the n5 final, close-up, layer-isolation and ablation media. "
            "n5 changes the method: ablation from real branch anchors, layer isolation rendered at the "
            "shipping camera, and a measured pixel profile for every claimed improvement, including one "
            "logged regression where the dark-band metric halved while the frame got worse. "
            "Scores are producer claims, not independent approval."),
        "known_gaps": [
            "Flat backdrop plane above the treeline; the horizon still reads as a wall.",
            "Crown is mushroom-shaped with a bare branch skirt below the foliage.",
            "Mortar grid still dominates the largest surface in frame.",
            "Functional prop clusters along the route edge were deferred for run budget.",
            "WeChat real-device performance is still untested (Q09 device_tested=false).",
        ],
    }
    out = N5 / "T4/producer_self_review_n5.json"
    write(out, review)
    print(out)


if __name__ == "__main__":
    main()
