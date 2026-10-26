"""Fill the N2 producer self-review from the frozen manifest and real evidence."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REVIEW = ROOT / "delivery/next_cycle/T4/producer_self_review_round_02.json"
OUT = ROOT / "delivery/next_cycle/T4/producer_self_review.json"
MANIFEST_REL = "art_review/submissions/candidate_n2/manifest.json"
TEMPLATE = "delivery/next_cycle/T4/producer_self_review_round_02.json"
P1 = "reference/_raw_screenshots/P1/"


def sha(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def ref(rel):
    p = ROOT / rel
    assert p.is_file(), rel
    return {"path": rel, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8-sig"))


def write(rel, value):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


SCORES = {
    "ENV": {
        "composition_scale": 3,
        "geometry_craft": 2,
        "material_separation": 3,
        "lighting_contact": 3,
        "vegetation_depth": 3,
        "play_readability": 3,
    },
    "CHAR": {
        "silhouette_proportion": 4,
        "line_quality": 4,
        "cel_color_light": 3,
        "identity_consistency": 4,
        "motion_contact": 4,
        "small_scale_clarity": 3,
    },
    "UI": {
        "paper_shape": 3,
        "doodle_icon_family": 3,
        "typography": 3,
        "layout_air": 3,
        "state_feedback": 3,
        "palette_restraint": 3,
    },
    "MIX": {
        "visual_language": 3,
        "color_light_coherence": 3,
        "grounding_occlusion": 3,
        "focus_readability": 3,
        "world_style_coherence": 3,
    },
}

GAPS = {
    "composition_scale": ("P1 t015 fills the foreground and nests midground platforms; finalN2 still leaves more open paving at the edges.", "N01 raised hedge/groundcover density. Accepted at 3; a further pass should add foreground planting/edge props."),
    "geometry_craft": ("Crown mass, planter rim and bench still read as faceted low-poly at formal scale; branch taper and silhouette variation are simpler than P1.", "N01 added branch depth and card clusters but did not hide the faceting. Scored 2 (usable but visibly crude); this is a key remaining gap."),
    "material_separation": ("Metal flattens at distance and wear variation is simpler than P1, though stone/wood/metal/soil are distinct.", "N02 strengthened texture contrast and material settings; accepted at 3."),
    "lighting_contact": ("Ambient bounce and long directional shadow remain limited; shadow is soft but fairly uniform.", "N02 replaced blocky crown shadow with 8192 PCF SOFT_4X, contact shadow and card dapple; accepted at 3."),
    "vegetation_depth": ("Foreground layer is thinner than P1 and leaf silhouette is coarser.", "N01 added six-lobe crown, outer clusters, three hedge rows, side cards and groundcover; accepted at 3."),
    "play_readability": ("A few far-edge props blend into soil; some foliage competes at the top edge.", "HUD leaves the center open and the main route is legible; accepted at 3."),
    "silhouette_proportion": ("None at the asset level; scale is 130px at the top of the allowed 86-130 range.", "Locked 1015 Spine; N04 real bbox confirmed 130x130; FOV calibrated rather than scaling the asset."),
    "line_quality": ("No redraw; original line weight is preserved, but engine downscale can soften fine lines.", "Locked source and engine preview inspected; accepted at 4."),
    "cel_color_light": ("Scene light does not tint the character; integration relies on contact shadow and value separation.", "Source palette preserved; accepted at 3 rather than claiming full scene lighting integration."),
    "identity_consistency": ("None observed across portrait, dialogue and runtime frames.", "Same locked source and identity; accepted at 4."),
    "motion_contact": ("Foot contact is authored in the source; no new animation authored.", "N07 captured idle/move at 500ms with 6 unique frames each and advancing trackTime; two states support 4."),
    "small_scale_clarity": ("Fine accessories compress at 130px on a 1280x720 frame.", "Character remains identifiable; accepted at 3."),
    "paper_shape": ("P1 sheets are thinner and more irregular; finalN2 keeps a visible rounded rectangle and a slightly heavier edge.", "N03 added translucency, dashed inner edge and fibers; accepted at 3, not 4."),
    "doodle_icon_family": ("The doodle family is still smaller than P1 and appears mainly around title/dialogue/HUD.", "N03 added leaf/sparkle/speech doodles; accepted at 3."),
    "typography": ("Hierarchy is consistent, but hand-set spacing and irregularity are weaker than P1.", "Native-size Chinese text is readable; accepted at 3."),
    "layout_air": ("Dialogue panel still covers more vertical space than P1.", "HUD keeps center open; accepted at 3."),
    "state_feedback": ("Most states are look-state captures; transition timing and pressed duration are not measured.", "41 states captured including pressed/hidden/toast/loading failure/pause/complete; accepted at 3."),
    "palette_restraint": ("P1 is closer to white/gray; finalN2 cream is warmer and metal/wood share similar values.", "Mint accent remains restrained; accepted at 3."),
    "visual_language": ("Environment detail is sparser and UI is heavier than P1, so the shared language is established but not refined.", "N01-N03 moved scene and UI toward the same warm paper/hand-drawn direction; accepted at 3."),
    "color_light_coherence": ("Flat material response reduces bounce light and makes some surfaces feel cut out.", "Warm key/cool fill, cream UI and soft shadow are coherent; accepted at 3."),
    "grounding_occlusion": ("Silhouette edge can still read as a cutout in some shots.", "Contact shadow and Q03 front/behind occlusion support 3; not claimed as 4."),
    "focus_readability": ("Tall foliage occasionally competes at the top edge.", "Character, task and interact button remain readable; accepted at 3."),
    "world_style_coherence": ("Gap to P1 is detail density and light response, not an intentional style clash.", "Scene/character/UI are consistently stylized; accepted at 3."),
}


def main():
    template = load(TEMPLATE)
    n06 = load("delivery/next_cycle/N_rework/N06_evidence_index.json")
    manifest = load(MANIFEST_REL)
    candidates = {a["path"] for a in manifest["artifacts"] + manifest.get("catalog_members", [])}
    report = template
    report["reviewer"] = {"id": "producer_execution_model", "mode": "producer_self_review"}
    report["round"] = 2
    report["manifest"] = ref(MANIFEST_REL)
    report["rubric_sha256"] = sha("art_review/rubric.json")
    report["contract_sha256"] = sha("art_review/harness_contract.json")
    report["policy_sha256"] = sha("planning/execution/producer_review_policy.json")
    report["quality_results"] = ref("delivery/next_cycle/N_rework/behavior_results_n.json")
    report["capture_binding"] = ref("art_review/submissions/candidate_n2/bindings/binding_formal_no_ui.json")
    report["comparison_note"] = (
        "Producer self-review of the finalN2 build, rescored from actual captures and P1 frames. "
        "It intentionally does not copy the previous 90/90/91.25/90 scores; ENV, UI and MIX remain below the 90 submission threshold."
    )

    for card, dims in report["cards"].items():
        for row in dims["dimensions"]:
            dim = row["id"]
            evidence = n06["cards"][card][dim]["evidence"]
            refs = [p for p in evidence if p.startswith(P1)]
            cands = [p for p in evidence if not p.startswith(P1)]
            row["score"] = SCORES[card][dim]
            row["observation"] = n06["cards"][card][dim]["observation"]
            row["gap"], row["action_or_acceptance_reason"] = GAPS[dim]
            row["reference_evidence"] = [ref(refs[0])]
            row["candidate_evidence"] = [ref(p) for p in cands]
            for p in cands:
                assert p in candidates, "candidate evidence not in manifest: " + p

    catalog = load("art/iterations/cycle_03/full_art_catalog.json")
    checks = []
    for item in catalog["items"]:
        review = load(item["review_path"])
        evidence = [item["review_path"], item["preview_paths"][0], item["source_paths"][0]]
        for p in evidence:
            assert p in candidates, "asset evidence not in manifest: " + p
        checks.append({
            "asset_id": item["id"],
            "decision": "pass",
            "reason": (review["reason"] + " This decision is producer self-review of the current finalN2 build; "
                       "independent visual confirmation is still required."),
            "evidence": [ref(p) for p in evidence],
        })
    report["asset_checks"] = checks

    previous = load("delivery/next_cycle/T4/versions/producer_self_review_round_01.json")["issues"]
    issues = {i["id"]: dict(i) for i in previous}
    update = {
        "F05": ["art_review/submissions/candidate_n2/bindings/summary.json"],
        "F06": ["delivery/next_cycle/T4/N01_tree_hedge_before_after.png", "delivery/next_cycle/T4/N02_shadow_before_after.png",
                "delivery/next_cycle/T4/N02_material_closeups.png", "delivery/next_cycle/T4/N03_ui_before_after.png"],
        "F07": ["delivery/next_cycle/T2/lighting_settings_finalN2.json", "delivery/next_cycle/T4/N02_shadow_before_after.png"],
        "R01": ["delivery/next_cycle/T5/q03_occlusion.json", "delivery/next_cycle/T5/q03_behind.png"],
        "R02": ["delivery/next_cycle/T4/N04_actor_bbox.png", "delivery/next_cycle/N_rework/N04_bbox.json", "delivery/next_cycle/T5/q01_camera.json"],
        "R03": ["delivery/next_cycle/T4/N01_tree_hedge_before_after.png", "delivery/next_cycle/T4/plant_closeups_finalN2.png"],
        "R04": ["delivery/next_cycle/T4/N02_shadow_before_after.png", "delivery/next_cycle/T2/lighting_settings_finalN2.json"],
        "R05": ["delivery/next_cycle/T5/q04_behavior.json", "delivery/next_cycle/N_rework/q04_pause_n.json"],
        "R06": ["delivery/next_cycle/T5/q06_stats.json"],
        "R07": ["delivery/next_cycle/T5/q05_board.json"],
        "R09": ["delivery/next_cycle/T6/state_index.json", "delivery/next_cycle/T2/sample_dialogue.png"],
    }
    for iid, paths in update.items():
        issues[iid]["status"] = "fixed_pending_independent_confirmation"
        issues[iid]["resolution_evidence"] = [ref(p) for p in paths]

    n_issues = [
        ("N01", "major", "Vegetation/composition: repeated boulders, bare beds, weak depth.",
         ["delivery/next_cycle/T4/N01_tree_hedge_before_after.png", "delivery/next_cycle/T2/sample_no_ui.png",
          "delivery/next_cycle/T6/assets/ENV006.png"]),
        ("N02", "major", "Tree shadow/material: blocky crown shadow and weak material close-ups.",
         ["delivery/next_cycle/T4/N02_shadow_before_after.png", "delivery/next_cycle/T4/N02_material_closeups.png",
          "delivery/next_cycle/T2/lighting_settings_finalN2.json"]),
        ("N03", "major", "UI style: opaque cream panels, double frames, regular icons.",
         ["delivery/next_cycle/T4/N03_ui_before_after.png", "delivery/next_cycle/T3/game_finalN2_dialogue.png",
          "delivery/next_cycle/T6/state_index.json"]),
        ("N04", "blocking", "Q01 used a projection proxy instead of the real visible character bbox.",
         ["delivery/next_cycle/T4/N04_actor_bbox.png", "delivery/next_cycle/N_rework/N04_bbox.json",
          "delivery/next_cycle/T5/q01_camera.json"]),
        ("N05", "blocking", "Q09 injected rotate_notice; natural portrait stayed 1280x720 without response.",
         ["delivery/next_cycle/T4/N05_orientation.png", "delivery/next_cycle/N_rework/N05_orientation.json",
          "delivery/next_cycle/T5/q09_viewports.json"]),
        ("N06", "major", "Self-review reused sample scores and generic per-item reasons.",
         ["delivery/next_cycle/N_rework/N06_evidence_index.json",
          "delivery/next_cycle/T4/N01_tree_hedge_before_after.png",
          "delivery/next_cycle/T4/N02_shadow_before_after.png",
          "delivery/next_cycle/T4/N03_ui_before_after.png",
          "delivery/next_cycle/T6/state_index.json"]),
        ("N07", "major", "Animation GIFs were identical and static.",
         ["delivery/next_cycle/T6/character_n/N07_animation_sheet.png",
          "delivery/next_cycle/T6/character_n/N07_animation.json",
          "delivery/next_cycle/T6/character_n/char_idle.gif",
          "delivery/next_cycle/T6/character_n/char_move.gif"]),
        ("N08", "major", "Review ZIP contained stale JSON and old SHA fields; disk/ZIP comparison missing.",
         ["delivery/next_cycle/N_rework/N08_pack_plan.json",
          "art_review/submissions/candidate_n2/manifest.json"]),
    ]
    for iid, sev, title, paths in n_issues:
        entry = {"id": iid, "severity": sev, "status": "fixed_pending_independent_confirmation",
                 "title": title, "resolution_evidence": [ref(p) for p in paths]}
        if iid == "N08":
            entry["status"] = "fixed_pending_independent_confirmation"
            entry["note"] = ("Final ZIP is rebuilt only from the frozen manifest after this review snapshot; "
                             "disk-vs-ZIP verification and the outer checksum are written outside the ZIP as "
                             "delivery/N08_pack_verification.json.")
        issues[iid] = entry
    report["issues"] = list(issues.values())

    write("delivery/next_cycle/T4/producer_self_review_round_02.json", report)
    write("delivery/next_cycle/T4/producer_self_review.json", report)
    totals = {}
    rubric = load("art_review/rubric.json")
    for card, defs in rubric["cards"].items():
        total = 0.0
        for d in defs:
            score = next(x["score"] for x in report["cards"][card]["dimensions"] if x["id"] == d["id"])
            total += d["weight"] * score / 4
        totals[card] = total
    print(json.dumps({"manifest": report["manifest"], "totals": totals,
                      "assets": len(report["asset_checks"]), "issues": len(report["issues"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
