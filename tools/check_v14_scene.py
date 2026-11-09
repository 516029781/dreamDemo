"""Scene-side metrics A6/A7/A8 for SPACE_BASE_TECHNICAL_ART_PLAN v1.1 §5.

Runs INSIDE Blender:
  blender -b <scene.blend> --python tools/check_v14_scene.py -- <OUT_JSON>

Read-only. Reports material count / family coverage / roughness tiers and
bevel widths split by structural blocks (mind >= 0.73 m) vs thin slabs, since
v1.1 C9 showed that `min(0.22, mind*0.30)` cannot reach 1.3 px on 0.14 m slabs.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import bpy
from mathutils import Vector

PX_PER_M = 7.0
STRUCT_MIND = 0.73  # minimum dimension needed for w=0.22 under w=min(0.22, mind*0.30)

argv = sys.argv[sys.argv.index("--") + 1:]
out = Path(argv[0]).resolve()
out.parent.mkdir(parents=True, exist_ok=True)

mats = [m for m in bpy.data.materials if m.users > 0]
rough_tiers = Counter()
families = Counter()
rough_values = []
metallic_high = 0
for m in mats:
    families[str(m.get("material_family", "untagged"))] += 1
    if not m.use_nodes:
        continue
    b = m.node_tree.nodes.get("Principled BSDF")
    if not b:
        continue
    inp = b.inputs.get("Roughness")
    if inp and not inp.is_linked:
        rv = float(inp.default_value)
        rough_values.append(rv)
        rough_tiers[round(rv, 2)] += 1
    elif inp:
        rough_tiers["linked"] += 1
    mi = b.inputs.get("Metallic")
    if mi and not mi.is_linked and float(mi.default_value) > 0.5:
        metallic_high += 1

# P0 finding: v1.1's A7 ("roughness concentrated in 3 tiers, need >=6") is
# already satisfied by raw distinct-value counting (22 tiers) and therefore has
# no discriminating power. Report the distribution shape instead.
n_const = len(rough_values)
low = sum(1 for v in rough_values if v < 0.5)
high = sum(1 for v in rough_values if v >= 0.8)

bevels = []
thin_slab_bevels = []
struct_bevels = []
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    bb = [Vector(c) for c in o.bound_box]
    ext = [max(c[i] for c in bb) - min(c[i] for c in bb) for i in range(3)]
    mind = min(ext)
    for md in o.modifiers:
        if md.type == "BEVEL":
            w = float(md.width)
            bevels.append(round(w, 4))
            (struct_bevels if mind >= STRUCT_MIND else thin_slab_bevels).append(round(w, 4))

d = {
    "schema": "v14-scene-metrics-v1",
    "scene": bpy.data.filepath.replace("\\", "/"),
    "objects": len(bpy.data.objects),
    "meshes": sum(1 for o in bpy.data.objects if o.type == "MESH"),
    "A6_materials_used": len(mats),
    "A6_family_tags": dict(families),
    "A6_family_count_excl_untagged": len([k for k in families if k != "untagged"]),
    "A7_roughness_tiers": dict(rough_tiers.most_common()),
    "A7_roughness_tier_count": len([k for k in rough_tiers if isinstance(k, float)]),
    "A7_roughness_const_materials": n_const,
    "A7_low_roughness_lt050_count": low,
    "A7_low_roughness_ratio": round(low / n_const, 4) if n_const else 0,
    "A7_high_roughness_ge080_count": high,
    "A7_metallic_gt050_count": metallic_high,
    "A7_note": "raw distinct-tier count already >=6 at v13; use low-roughness share / metallic count / family spread instead",
    "A8_bevel_count": len(bevels),
    "A8_bevel_width_histogram": dict(Counter(bevels).most_common(12)),
    "A8_structural_blocks_mind_ge_0_73": {
        "count": len(struct_bevels),
        "max_width_m": max(struct_bevels) if struct_bevels else 0,
        "max_width_px": round(max(struct_bevels) * PX_PER_M, 3) if struct_bevels else 0,
    },
    "A8_thin_slabs": {
        "count": len(thin_slab_bevels),
        "max_width_m": max(thin_slab_bevels) if thin_slab_bevels else 0,
        "max_width_px": round(max(thin_slab_bevels) * PX_PER_M, 3) if thin_slab_bevels else 0,
    },
    "note": "A8 target >=1.3 px applies ONLY to structural blocks; thin slabs must use material-layer edge lines.",
}
out.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
print("SCENE_METRICS", d["A6_materials_used"], "materials,",
      d["A7_roughness_tier_count"], "roughness tiers,",
      d["A8_bevel_count"], "bevels, struct max",
      d["A8_structural_blocks_mind_ge_0_73"]["max_width_px"], "px")
