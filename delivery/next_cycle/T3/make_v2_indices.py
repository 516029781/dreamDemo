"""Write v2 source/export indices for V01/V02/V03/V05 with real hashes."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    now = datetime.now(timezone.utc).isoformat()
    for sub in ("ENV006", "materials", "plants", "ui"):
        d = ROOT / "art/iterations/cycle_02" / sub
        idx = d / "source_export_index.json"
        versions = d / "versions"
        versions.mkdir(parents=True, exist_ok=True)
        if idx.exists() and not (versions / "source_export_index_v1.json").exists():
            shutil.copy2(idx, versions / "source_export_index_v1.json")

    common = {
        "cycle": "cycle_02",
        "index_version": "2.0.0",
        "generated_at": now,
        "review_state": "self_check_only_not_reviewed",
        "note": "Producer-side evidence only. Independent visual review and V09 release are not signed.",
        "current_build": {
            "map_blend": {"path": "art/full/source/layout/MAP001_courtyard.blend",
                          "sha256": sha(ROOT / "art/full/source/layout/MAP001_courtyard.blend")},
            "map_glb": {"path": "art/full/source/layout/MAP001_courtyard.glb",
                        "sha256": sha(ROOT / "art/full/source/layout/MAP001_courtyard.glb")},
            "engine_glb": {"path": "demo/assets/resources/models/MAP001_courtyard.glb",
                           "sha256": sha(ROOT / "demo/assets/resources/models/MAP001_courtyard.glb")},
            "env006_blend": {"path": "art/full/source/environment/ENV006_autumn_tree.blend",
                             "sha256": sha(ROOT / "art/full/source/environment/ENV006_autumn_tree.blend")},
            "env006_glb": {"path": "art/full/source/environment/ENV006_autumn_tree.glb",
                           "sha256": sha(ROOT / "art/full/source/environment/ENV006_autumn_tree.glb")},
            "layout_json": {"path": "art/full/source/layout/layout.json",
                            "sha256": sha(ROOT / "art/full/source/layout/layout.json")},
            "bootstrap_ts": {"path": "demo/assets/scripts/CourtyardBootstrap.ts",
                             "sha256": sha(ROOT / "demo/assets/scripts/CourtyardBootstrap.ts")},
            "cocos_build_log": {"path": "tools/cocos/logs/build_web_desktop.log",
                                "sha256": sha(ROOT / "tools/cocos/logs/build_web_desktop.log")},
        },
        "captures": {
            "formal_no_ui": {"path": "delivery/next_cycle/T3/game_final3_formal_no_ui.png",
                             "sha256": sha(ROOT / "delivery/next_cycle/T3/game_final3_formal_no_ui.png")},
            "formal_ui": {"path": "delivery/next_cycle/T3/game_final3_formal_ui.png",
                          "sha256": sha(ROOT / "delivery/next_cycle/T3/game_final3_formal_ui.png")},
            "dialogue": {"path": "delivery/next_cycle/T3/game_final3_dialogue.png",
                         "sha256": sha(ROOT / "delivery/next_cycle/T3/game_final3_dialogue.png")},
            "bindings_summary": {"path": "delivery/next_cycle/T3/final3_bindings_summary.json",
                                 "sha256": sha(ROOT / "delivery/next_cycle/T3/final3_bindings_summary.json")},
        },
        "commands": [
            "powershell -File tools/blender/run_courtyard_build.ps1 -Stage env_tree,map001 (directed; exit 0; gate pass)",
            "python -X utf8 tools/cocos/build_web_desktop.py (exit 36 known anomaly; Finished + ordered SIGTERM + output present; gate pass)",
            "node delivery/next_cycle/_v06_game_shots.js final3 (real canvas capture, 3 shots, 0 page errors)",
            "python -X utf8 delivery/next_cycle/T3/make_final_bindings.py (3/3 bindings verified)",
        ],
        "limitations": [
            "No independent visual review yet.",
            "Old T1/T2 page screenshots remain historical and are not used as final evidence.",
            "Cocos 3.8.8 exit 36 is accepted only by the versioned gate rule with success marker, ordered SIGTERM and output present.",
        ],
    }
    indices = {
        "ENV006": {
            "task": "V01 tree crown and branch hierarchy (v2)",
            "source_edit": {
                "file": "tools/blender/build_env_courtyard.py",
                "functions": ["create_tree", "_grow_branch"],
                "changes": [
                    "solid displaced crown mass (core + 40 micro-clumps) behind leaf cards",
                    "leaf cards moved to the outer shell with larger accents; branch tips tucked in",
                    "warm palette (ochre/amber) replaces the green-dominant mix",
                    "trunk/fork radii increased and main branch length extended",
                ],
            },
            "evidence": ["delivery/next_cycle/T4/tree_before_after_v2.png",
                         "delivery/next_cycle/T3/game_final3_formal_no_ui.png",
                         "delivery/next_cycle/T3/mat_final3_ENV006.png"],
            "acceptance_self_check": ["large/medium/small clumps present",
                                      "walkway clearance kept (canopy bottom > 3 m)",
                                      "occlusion group OCC_tree_main includes canopy + crown mass"],
            "review_state": "self_check_only_not_reviewed",
        },
        "materials": {
            "task": "V02 material separation (v2)",
            "source_edit": {
                "file": "demo/assets/scripts/CourtyardBootstrap.ts",
                "table": "MAT_OVERRIDES",
                "changes": [
                    "stone warm-grey palette, roughness 0.86-0.94",
                    "wood grain color/roughness along slats (bench 0.62)",
                    "metal iron metallic 0.90 / roughness 0.36; brass 0.85/0.35",
                    "soil darkened to #3F362C",
                ],
            },
            "evidence": ["delivery/next_cycle/T4/material_closeups_v2.png",
                         "delivery/next_cycle/T3/mat_final3_ENV001.png",
                         "delivery/next_cycle/T3/mat_final3_PROP001.png",
                         "delivery/next_cycle/T3/mat_final3_PROP004.png"],
            "acceptance_self_check": ["stone/wood/metal/soil families use distinct color+roughness+metallic",
                                      "all close-ups are real engine canvas captures"],
            "review_state": "self_check_only_not_reviewed",
        },
        "plants": {
            "task": "V03 planter/plant density and background layers (v2)",
            "source_edit": {
                "file": "tools/blender/build_map001.py",
                "changes": [
                    "20 dry-grass and 10 leaf-litter instances along soil margins with varied scale",
                    "ring planter ground cover around the trunk",
                    "side planter stays layered; shrub instances varied 0.85-1.15",
                    "background hedge (two rows + cards) and distant olive crown band (no bare trunks)",
                ],
            },
            "evidence": ["delivery/next_cycle/T4/plant_background_v2.png",
                         "delivery/next_cycle/T4/plant_closeups_v2.png",
                         "delivery/next_cycle/T3/plant_final3_ENV007.png",
                         "delivery/next_cycle/T3/plant_final3_ENV008.png",
                         "delivery/next_cycle/T3/plant_final3_ENV009.png",
                         "delivery/next_cycle/T3/plant_final3_ENV011.png"],
            "acceptance_self_check": ["planters no longer read as bare soil",
                                      "path/plaza center kept clear",
                                      "background has near hedge / mid wall / far crown layers"],
            "review_state": "self_check_only_not_reviewed",
        },
        "ui": {
            "task": "V05 paper/UI local polish (v2)",
            "source_edit": {
                "file": "demo/assets/scripts/CourtyardBootstrap.ts",
                "changes": [
                    "dialogue/quest/menu panels more translucent (alpha 222/218/225)",
                    "mint page/hint accents and leaf icon",
                    "mint underline + hand-drawn gold underline under speaker",
                    "speaker 28 / body 24 / page 13 hierarchy",
                ],
            },
            "evidence": ["delivery/next_cycle/T4/ui_comparison_v2.png",
                         "delivery/next_cycle/T3/game_final3_dialogue.png",
                         "delivery/next_cycle/T3/game_final3_formal_ui.png"],
            "acceptance_self_check": ["panel translucency visible against scene",
                                      "mint accent applied to status/hint",
                                      "double-border feel reduced but paper texture retained"],
            "review_state": "self_check_only_not_reviewed",
        },
    }
    for sub, doc in indices.items():
        path = ROOT / "art/iterations/cycle_02" / sub / "source_export_index.json"
        path.write_text(json.dumps({**common, **doc}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(path.relative_to(ROOT), sha(path)[:16])


if __name__ == "__main__":
    main()
