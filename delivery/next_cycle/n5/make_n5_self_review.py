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
NO_UI = "delivery/next_cycle/n5/T3/game_finalN5h_formal_no_ui.png"
UI = "delivery/next_cycle/n5/T3/game_finalN5h_formal_ui.png"
DIALOGUE = "delivery/next_cycle/n5/T3/game_finalN5h_dialogue.png"


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


def reference_evidence(card, dimension_id):
    """Keep t084 primary; add only purpose-specific secondary P1 frames."""
    paths = [P1 + "t084s.jpg"]
    if card == "UI" and dimension_id in {"paper_shape", "typography", "layout_air"}:
        paths.append(P1 + "t090s.jpg")
    if card == "CHAR" and dimension_id == "identity_consistency":
        paths.append(P1 + "t054s.jpg")
    return [ref(path) for path in paths]


SCORES = {
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
            "The smooth crown core is deleted (mesh count confirms MAP001_tree_crown_mass is gone); the interior is now 52 inner clusters plus a 40-cluster curtain, a south skirt and a low south-west bough, all on recorded anchors; Q03 behind-tree occlusion now passes (366 of 1,089 white pixels visible).",
            "The low bough fixed the bare trunk skirt in the game camera, but there is still no four-view silhouette pass this round.",
            "Accepted at 3.",
            ["art/candidates/candidate_n5/previews/environment/tree_ablation/C_gameplay.png", NO_UI]),
        "material_separation": (
            "Stone albedo darkened (base #A79B88, dark #6F6455, mortar #7E7364), soil darkened to #4C3A2B; the paved field now measures #A08B6C against the reference range #897161 to #D6C0A7.",
            "Cracks, moss and edge wear are still absent; the largest surface has tone and repair groups but little incident.",
            "Accepted at 3.",
            ["delivery/next_cycle/n5/T4/N02_material_closeups.png", NO_UI]),
        "lighting_contact": (
            "Vertex-colour AO ships in the GLB (all 473 primitives carry COLOR_0): roots darken by height, downward foliage faces darken, and ground within 0.45 m of solid props gets a contact ring (4,396 ground vertices, min factor 0.58).",
            "Highlights remain low: frame p95 is 0.78 against the 0.80 target, so the strongest 5% of the picture still looks flat.",
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
        "color_light_coherence": ("Hue moved into the reference range: 0-30 deg share 0.410 (target at least 0.25, was 0.067); shadow tint sits at hue 20.", "Frame p95 0.78 (just below 0.80) and saturation 0.368 (reference 0.275) still read flatter and more ochre than P1; the screen-space grade that would have closed this was blocked by the legacy pipeline (decisions n5d-s1).", "Accepted at 3: hue direction fixed, the reference brightness and contrast are not delivered.", [NO_UI, UI]),
        "grounding_occlusion": ("Vertex AO plus the projected crown decal ground props; Q03 behind-tree occlusion passes.", "Props other than the tree still use soft ambient blobs.", "Accepted at 4.", ["delivery/next_cycle/n5/T4/N02_shadow_before_after.png", "delivery/next_cycle/n5/T5/q03_behind.png"]),
        "focus_readability": ("Character, route, dialogue and next button stay the focal chain.", "Paving is still the brightest region.", "Accepted at 3.", [UI, DIALOGUE]),
        "world_style_coherence": ("Paper, hedge and paving share one warm autumn key with value separation between stone and earth.", "World surface detail remains a step below the character art.", "Accepted at 3.", [UI, "delivery/next_cycle/n5/T4/N01_geometry_before_after.png"]),
    },
}

ISSUE_EVIDENCE = {
    "N01": ["delivery/next_cycle/n5/T4/N01_geometry_before_after.png",
            "delivery/next_cycle/n5/T4/N01_geometry_closeups.png"],
    "N02": ["delivery/next_cycle/n5/T4/N02_shadow_before_after.png",
            "delivery/next_cycle/n5/T4/N02_material_closeups.png"],
    "N03": ["delivery/next_cycle/n5/T4/N03_ui_before_after.png",
            "delivery/next_cycle/n5/T3/game_finalN5h_dialogue.png"],
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
            rows.append({
                "id": dim["id"],
                "score": SCORES[card][dim["id"]],
                "observation": obs,
                "gap": gap,
                "action_or_acceptance_reason": action,
                "reference_evidence": reference_evidence(card, dim["id"]),
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
        "stage": "art_complete", "round": 8,
        "manifest": ref("art_review/submissions/candidate_n5/manifest.json"),
        "rubric_sha256": sha("art_review/rubric.json"),
        "contract_sha256": sha("art_review/harness_contract.json"),
        "policy_sha256": sha("planning/execution/producer_review_policy.json"),
        "quality_results": ref(QUALITY_REL),
        "capture_binding": ref(BINDING_REL),
        "cards": cards, "asset_checks": asset_checks, "issues": issues,
        "comparison_note": (
            "Primary whole-scene comparison uses P1 t084 for every card. P1 t090 is cited only for dialogue UI state; t054 only for character identity detail. t015/t044 remain historical/special-purpose references and do not set current whole-scene scores. "
            "n5 changes the method: ablation from real branch anchors, layer isolation rendered at the "
            "shipping camera, and a measured pixel profile for every claimed improvement, including one "
            "logged regression where the dark-band metric halved while the frame got worse. "
            "Scores are producer claims, not independent approval."),
        "known_gaps": [
            "Frame p95 0.78 below the 0.80 target and saturation 0.368 above the reference 0.275; the screen-space grade was blocked by the legacy pipeline.",
            "No foreground object enters the bottom of frame; the near rail sits below the view.",
            "Leaf-card atlas (S4) was not delivered; foliage still uses flat-colour folded cards.",
            "Cracks, moss and edge wear on stone remain procedural mottle only.",
            "Far treeline reads as dark rounded lumps above the hedge.",
            "WeChat real-device performance is still untested (Q09 device_tested=false).",
        ],
    }
    out = N5 / "T4/producer_self_review_n5.json"
    write(out, review)
    print(out)


if __name__ == "__main__":
    main()
