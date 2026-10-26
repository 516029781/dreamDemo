"""V06: freeze the sample candidate manifest from the current build and captures."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
T2 = ROOT / "delivery/next_cycle/T2"
T3 = ROOT / "delivery/next_cycle/T3"
T5 = ROOT / "delivery/next_cycle/T5"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    now = datetime.now(timezone.utc).isoformat()
    mapping = {
        "sample_no_ui.png": T3 / "game_finalN2_formal_no_ui.png",
        "sample_hud.png": T3 / "game_finalN2_formal_ui.png",
        "sample_dialogue.png": T3 / "game_finalN2_dialogue.png",
    }
    for target, source in mapping.items():
        shutil.copy2(source, T2 / target)
    build_reports = sorted((ROOT / "delivery/performance").glob("cocos_build_*.json"))
    build_report = json.loads(build_reports[-1].read_text(encoding="utf-8-sig"))
    camera = json.loads((T5 / "q01_camera.json").read_text(encoding="utf-8-sig"))["camera"]
    references = ["reference/_raw_screenshots/P1/t015s.jpg",
                  "reference/_raw_screenshots/P1/t044s.jpg",
                  "reference/_raw_screenshots/P1/t084s.jpg"]
    manifest = {
        "sample_manifest_version": "1.1.0",
        "status": "candidate_not_independently_approved",
        "stage": "scene_demo",
        "created_at": now,
        "camera": camera,
        "build": {
            "engine": "Cocos Creator 3.8.8 web-desktop",
            "report": str(build_reports[-1].relative_to(ROOT)).replace("\\", "/"),
            "report_sha256": sha(build_reports[-1]),
            "cocos_exit_code": build_report.get("cocos_exit_code"),
            "known_exit_rule": "exit 36 accepted only with Finished + ordered SIGTERM + output present",
            "map_glb": {"path": "art/full/source/layout/MAP001_courtyard.glb",
                        "sha256": sha(ROOT / "art/full/source/layout/MAP001_courtyard.glb")},
            "engine_glb": {"path": "demo/assets/resources/models/MAP001_courtyard.glb",
                           "sha256": sha(ROOT / "demo/assets/resources/models/MAP001_courtyard.glb")},
            "bootstrap": {"path": "demo/assets/scripts/CourtyardBootstrap.ts",
                          "sha256": sha(ROOT / "demo/assets/scripts/CourtyardBootstrap.ts")},
        },
        "samples": {
            "no_ui": {"path": "delivery/next_cycle/T2/sample_no_ui.png", "sha256": sha(T2 / "sample_no_ui.png")},
            "hud": {"path": "delivery/next_cycle/T2/sample_hud.png", "sha256": sha(T2 / "sample_hud.png")},
            "dialogue": {"path": "delivery/next_cycle/T2/sample_dialogue.png", "sha256": sha(T2 / "sample_dialogue.png")},
        },
        "capture_bindings": {
            "paths": ["art_review/submissions/candidate_n2/bindings/binding_formal_no_ui.json",
                      "art_review/submissions/candidate_n2/bindings/binding_formal_ui.json",
                      "art_review/submissions/candidate_n2/bindings/binding_dialogue.json"],
            "summary": {"path": "art_review/submissions/candidate_n2/bindings/summary.json",
                        "sha256": sha(ROOT / "art_review/submissions/candidate_n2/bindings/summary.json")},
        },
        "reference": {
            "frames": [{"path": p, "sha256": sha(ROOT / p)} for p in references],
            "comparison": {"path": "delivery/next_cycle/T2/reference_comparison.png",
                           "sha256": sha(T2 / "reference_comparison.png")},
            "rule": "reference and candidate are displayed side by side; no reference pixels are composited into the candidate",
        },
        "q_evidence": {
            "camera": "delivery/next_cycle/T5/q01_camera.json",
            "occlusion": "delivery/next_cycle/T5/q03_occlusion.json",
            "behavior": "delivery/next_cycle/T5/q04_behavior.json",
            "board": "delivery/next_cycle/T5/q05_board.json",
            "stats": "delivery/next_cycle/T5/q06_stats.json",
            "viewports": "delivery/next_cycle/T5/q09_viewports.json",
        },
        "artifacts": [],
        "catalog_members": [],
        "limitations": [
            "Candidate only; producer self-review did not reach the full 90 threshold on ENV/UI/MIX.",
            "Independent visual review and controller release are not signed.",
            "Portrait shows the designed rotate notice; gameplay is landscape-only.",
            "Q06 draws are above the 400 warning line; recorded as warning, not a hard fail.",
            "No phone-device test; Q09 is browser-only.",
        ],
    }
    files = []
    for pattern in ("delivery/next_cycle/T2/sample_*.png",
                    "delivery/next_cycle/T2/reference_comparison.png",
                    "delivery/next_cycle/T4/N0*.png",
                    "delivery/next_cycle/T4/plant_closeups_finalN2.png",
                    "delivery/next_cycle/T5/q01_*.png",
                    "delivery/next_cycle/T5/q03_*.png",
                    "delivery/next_cycle/T5/q04_*.png",
                    "delivery/next_cycle/T5/q05_*.png",
                    "delivery/next_cycle/T5/q07_*.png",
                    "delivery/next_cycle/T5/q09_*.png",
                    "delivery/next_cycle/T5/q0*.json",
                    "delivery/next_cycle/T2/lighting_profile_v2.json",
                    "delivery/next_cycle/T6/state_index.json",
                    "delivery/next_cycle/T3/final4_bindings_summary.json",
                    "delivery/next_cycle/T6/ui_states/*.png",
                    "delivery/next_cycle/T6/assets/*.png",
                    "delivery/next_cycle/T6/character/*.png",
                    "delivery/next_cycle/T6/character/*.gif",
                    "delivery/next_cycle/T6/character_n/*.png",
                    "delivery/next_cycle/T6/character_n/*.gif",
                    "delivery/next_cycle/T6/character_n/*.json",
                    "art/phase1/character_playback_1015/*.png",
                    "art/phase1/character_playback_1015/*.gif",
                    "art/phase1/character_playback_1015/*.json",
                    "art/phase1/character_playback_1015/*.txt",
                    "delivery/next_cycle/T3/game_finalN2_formal_no_ui.png",
                    "delivery/next_cycle/T3/game_finalN2_formal_ui.png",
                    "delivery/next_cycle/T3/game_finalN2_dialogue.png",
                    "delivery/next_cycle/T3/mat_finalN2_*.png",
                    "delivery/next_cycle/T3/plant_finalN2_*.png",
                    "delivery/next_cycle/N_rework/N0*.json",
                    "delivery/next_cycle/N_rework/N04_*.png",
                    "delivery/next_cycle/N_rework/N05_*.png"):
        files.extend(sorted(ROOT.glob(pattern)))
    seen = set()
    for file in files:
        relative = file.relative_to(ROOT).as_posix()
        if relative in seen:
            continue
        seen.add(relative)
        manifest["artifacts"].append({"path": relative, "sha256": sha(file)})
    manifest["artifact_count"] = len(manifest["artifacts"])
    out = T2 / "sample_manifest.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(out), "sha256": sha(out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
