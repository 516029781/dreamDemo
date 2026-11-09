"""TV13-01/02/03 mechanical checks (run inside Blender).

Usage:
  blender -b art/static_map/space_base_minigame/v13/scene.blend \
    --python tools/check_v13_workshop.py -- <evidence_dir>

Writes evidence/TV13-01/workshop_components.json, TV13-02/blacklist.json,
TV13-03/roof_scan.json. No PASS is claimed here; the harness checker decides.
"""
import json
import sys
from pathlib import Path

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
out = Path(argv[0])
out.mkdir(parents=True, exist_ok=True)
names = [o.name for o in bpy.data.objects]

# ---- TV13-01: S-01..S-12 identity combination ----
GROUPS = {
    "S-01_blast_wall": ("ws_wall_", "ws_coping_", "ws_joint_", "ws_stain_"),
    "S-02_entrance": ("ws_entrance",),
    "S-03_ground_pipes": ("ws_pipe_", "ws_flange_", "ws_pipestand_"),
    "S-04_diversion_pit": ("ws_pit_", "ws_pitrail_"),
    "S-05_containers": ("ws_cont_",),
    "S-06_ground_marks": ("ws_slabjoint_", "ws_yellow_", "ws_trench_", "ws_puddle_"),
    "S-07_control_room": ("ws_ctrl_",),
    "S-08_bollards": ("ws_bollard_",),
    "S-09_evac_frame": ("ws_evac_",),
    "S-10_terminal": ("ws_terminal",),
    "S-11_clutter": ("ws_cab_", "ws_pallet_", "ws_drum_"),
    "S-12_ladders": ("ws_ladder_",),
}
components = {}
for key, prefixes in GROUPS.items():
    hit = [n for n in names if any(n.startswith(p) for p in prefixes)]
    components[key] = {"count": len(hit), "sample": hit[:6]}
p = out / "TV13-01"
p.mkdir(parents=True, exist_ok=True)
(p / "workshop_components.json").write_text(
    json.dumps({"test_id": "TV13-01", "components": components,
                "all_present": all(v["count"] > 0 for v in components.values())},
               ensure_ascii=False, indent=1), encoding="utf-8")

# ---- TV13-02: deletion blacklist ----
BLACK = ("test_hall", "evac_glow", "pen_curb_", "k11_pad_", "dock_floor",
         "pen_tip", "drum_", "pallet_", "container_")
black_hits = {b: [n for n in names if n.startswith(b)] for b in BLACK}
p = out / "TV13-02"
p.mkdir(parents=True, exist_ok=True)
(p / "blacklist.json").write_text(
    json.dumps({"test_id": "TV13-02",
                "blacklist_hits": {k: v for k, v in black_hits.items() if v},
                "total_hits": sum(len(v) for v in black_hits.values())},
               ensure_ascii=False, indent=1), encoding="utf-8")

# ---- TV13-03: roof scan (corr_truss is the frozen r14 open frame, excluded) ----
ROOF_TOKENS = ("roof", "ceiling", "skylight", "parapet", "_dach_")
EXEMPT = ("corr_truss", "corr_beam", "truss_dark", "k05_parapet")
roof_hits = [n for n in names
             if any(t in n.lower() for t in ROOF_TOKENS)
             and not any(e in n for e in EXEMPT)]
p = out / "TV13-03"
p.mkdir(parents=True, exist_ok=True)
(p / "roof_scan.json").write_text(
    json.dumps({"test_id": "TV13-03", "roof_hits": roof_hits,
                "count": len(roof_hits), "exempted": list(EXEMPT)},
               ensure_ascii=False, indent=1), encoding="utf-8")

print("CHECK_WORKSHOP_DONE",
      "all_present=", all(v["count"] > 0 for v in components.values()),
      "blacklist_hits=", sum(len(v) for v in black_hits.values()),
      "roof_hits=", len(roof_hits))
