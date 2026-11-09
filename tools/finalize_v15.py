"""Assemble the v15 delivery set: hero copies, check crops, MANIFEST, DELIVERY, GATE_REPORT.

Reads the real evidence JSONs (scene_checks / post_metrics / reproduction) so no
number here is typed by hand.

    python tools/finalize_v15.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path("C:/软件/鼠鼠")
CAND = ROOT / "art/static_map/space_base_minigame/v15"
REN = CAND / "renders"
CHK = REN / "checks"
EV = CAND / "evidence"
REQ = "20261108-space-base-v15-rooms"
RUN = "20261108-2320"
REQDIR = ROOT / "knowledge/active" / REQ
RUNDIR = REQDIR / "runs" / RUN


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    CHK.mkdir(parents=True, exist_ok=True)
    master = Image.open(REN / "space_base_v15_master.png").convert("RGB")
    hero = Image.open(REN / "hero_raw.png").convert("RGB")
    assert master.size == (1680, 2478), master.size
    assert hero.size == (1920, 1080), hero.size
    hero.save(REN / "space_base_v15_hero.png")
    hero.save(REN / "space_base_v11_hero.png")

    core_img = master.crop((300, 120, 1380, 1100)).resize((2072, 1876), Image.LANCZOS)
    core_img.save(REN / "space_base_v11_core.png")
    for name, box in (("01_core", (300, 100, 1380, 1100)),
                      ("02_avenue_bridge", (500, 900, 1300, 1700)),
                      ("03_peninsula", (600, 1650, 1400, 2478)),
                      ("04_avenue_head", (400, 700, 1200, 1450)),
                      ("05_g5_pair", (700, 1200, 1300, 2050))):
            master.crop(box).save(CHK / (name + ".png"))

    scene_checks = json.loads((EV / "scene_checks.json").read_text(encoding="utf-8"))
    post = json.loads((EV / "post_metrics.json").read_text(encoding="utf-8"))
    repro_path = RUNDIR / "reproduction.json"
    repro = json.loads(repro_path.read_text(encoding="utf-8")) if repro_path.exists() else {}

    checks = scene_checks["checks"]
    imaging = {
        "S1_light_land": post["S1"],
        "S2_green": post["S2"],
        "S3_orange": post["S3"],
        "water_frac": {"value": post["water_frac"],
                       "note": "reported next to S1 on purpose: cool darks are counted as water (plan 5.6)"},
    }
    scene = {k: {"value": v["value"], "pass": v["pass"]} for k, v in checks.items()}
    hard_fail = [k for k, v in scene.items() if not v["pass"]]
    hard_fail += [k for k, v in imaging.items() if "pass" in v and not v["pass"]]
    if not repro:
        hard_fail.append("reproduction")

    delivery = {
        "schema": "delivery-v1",
        "request_id": REQ,
        "run_id": RUN,
        "map_png": "renders/space_base_v15_master.png",
        "map_jpg": "renders/space_base_v15.jpg",
        "hero": "renders/space_base_v15_hero.png",
        "core_tile": "renders/space_base_v15_core.png",
        "status": "mechanical_complete_visual_pending",
    }
    (CAND / "DELIVERY.json").write_text(json.dumps(delivery, ensure_ascii=False, indent=1), encoding="utf-8")

    gate = {
        "schema": "gate-report-v1",
        "request_id": REQ,
        "run_id": RUN,
        "stage": "N7_mechanical",
        "pass": not hard_fail,
        "imaging": imaging,
        "scene": scene,
        "halls": post["halls"],
        "failed": hard_fail,
        "visual": {
            "front_back_comparison": "delivered (renders/checks/01_core.png vs v14)",
            "three_person_blind_test": "not_run",
        },
        "note": ("mechanical closure only; the identity blind test (I10) was not run, "
                 "so target_met is not claimed"),
    }
    (CAND / "GATE_REPORT.json").write_text(json.dumps(gate, ensure_ascii=False, indent=1), encoding="utf-8")

    entries = []
    for rel in ("scene.blend", "renders/master_raw.png", "renders/hero_raw.png",
                "renders/space_base_v15_master.png", "renders/space_base_v15.jpg",
                "renders/space_base_v15_hero.png", "renders/space_base_v15_core.png",
                "renders/space_base_v11_master.png", "renders/space_base_v11.jpg",
                "renders/space_base_v11_hero.png", "renders/space_base_v11_core.png",
                "evidence/scene_checks.json", "evidence/post_metrics.json",
                "DELIVERY.json", "GATE_REPORT.json", "REVIEW.md"):
        p = CAND / rel
        if p.exists():
            entries.append({"path": rel, "sha256": sha(p), "bytes": p.stat().st_size})
    manifest = {"schema": "manifest-v1", "request_id": REQ, "run_id": RUN,
                "candidate": "art/static_map/space_base_minigame/v15", "entries": entries}
    (CAND / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

    (CAND / "REPRODUCE.md").write_text(
        "# 复现 v15\n\n"
        "```\n"
        "python tools/blender_space_base/gen_v15_from_v14.py\n"
        "blender -b --python tools/blender_space_base/build_scene_v15.py -- "
        "--out art/static_map/space_base_minigame/v15/scene.blend --res 1680x2478 --samples 24\n"
        "blender -b art/static_map/space_base_minigame/v15/scene.blend "
        "--python tools/render_v14_master.py -- <ABS>/renders/master_raw.png\n"
        "python tools/post_v15.py\n"
        "blender -b art/static_map/space_base_minigame/v15/scene.blend "
        "--python tools/render_v15_hero.py -- <ABS>/renders/hero_raw.png 24\n"
        "blender -b art/static_map/space_base_minigame/v15/scene.blend "
        "--python tools/render_v14_raw.py -- <ABS>/renders/master_raw.png\n"
        "blender -b art/static_map/space_base_minigame/v15/scene.blend "
        "--python tools/check_v15_scene.py -- <ABS>/evidence/scene_checks.json\n"
        "python tools/run_v15_repro.py\n"
        "python tools/finalize_v15.py\n"
        "python tools/space_base_check_v7.py\n"
        "```\n\n"
        "v15 只重建四核心区；`gen_v15_from_v14.py` 从冻结的 v14 builder 确定性派生，"
        "其余图层逐字节不变。注意顺序：`post_v15.py` 必须在 `render_v14_raw.py` 覆盖 "
        "`master_raw.png` 之前跑，否则 1680 交付图会读成 3360 的源图。\n",
        encoding="utf-8")
    print("V15_FINALIZE hard_fail=", hard_fail, "entries=", len(entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
