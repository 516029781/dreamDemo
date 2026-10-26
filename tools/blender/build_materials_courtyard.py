"""
Build the five shared courtyard material master families (MAT001-MAT005).

Each family gets a native .blend with real beveled swatch solids and procedural
Principled materials, a GLB of the swatches using constant PBR fallbacks, and a
Cycles CPU preview.  No image textures, no baked maps (baking is still pending,
recorded in the manifest and report).

Run from the project root:
  .tools/blender/blender-4.5.15-windows-x64/blender.exe --background --factory-startup \
      --python tools/blender/build_materials_courtyard.py -- all
Stages: all, stone, wood, metal, leaf_grass, paper
"""
import math
import os
import sys

import bmesh
import bpy

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import courtyard_lib as cl  # noqa: E402

FAMILIES = {
    "stone": {
        "id": "MAT001", "name": "MAT001_stone", "label": "石材材质族",
        "materials": [cl.mat_stone_base, cl.mat_stone_light, cl.mat_stone_dark,
                      cl.mat_mortar, cl.mat_soil],
    },
    "wood": {
        "id": "MAT002", "name": "MAT002_wood", "label": "木材材质族",
        "materials": [cl.mat_wood, cl.mat_wood_dark, cl.mat_wood_pale],
    },
    "metal": {
        "id": "MAT003", "name": "MAT003_metal", "label": "金属材质族",
        "materials": [cl.mat_metal, cl.mat_metal_rust, cl.mat_metal_brass,
                      cl.mat_lamp_glass],
    },
    "leaf_grass": {
        "id": "MAT004", "name": "MAT004_leaf_grass", "label": "树叶草材质族",
        "materials": [cl.mat_leaf_ochre, cl.mat_leaf_amber, cl.mat_leaf_olive,
                      cl.mat_leaf_deep, cl.mat_grass_dry, cl.mat_grass_pale],
    },
    "paper": {
        "id": "MAT005", "name": "MAT005_paper", "label": "纸片材质族",
        "materials": [cl.mat_paper_cream, cl.mat_paper_kraft, cl.mat_ink,
                      cl.mat_gold],
    },
}


def build_family(family):
    cl.reset_scene()
    mats = [factory() for factory in family["materials"]]
    bm = bmesh.new()
    spacing = 0.36
    for i in range(len(mats)):
        x = (i - (len(mats) - 1) / 2.0) * spacing
        cl.add_box(bm, (x, 0, 0.075), (0.27, 0.27, 0.15), mat_index=i)
    swatches = cl.finish_mesh(family["name"] + "_swatches", bm, mats,
                              bpy.context.scene.collection)
    cl.add_bevel(swatches, width=0.012, segments=3)
    swatches["asset_id"] = family["id"]
    swatches["usage"] = family["label"]
    facts = cl.print_module_facts(family["name"], [swatches])

    blend = os.path.join(cl.SRC_MAT, family["name"] + ".blend")
    glb = os.path.join(cl.SRC_MAT, family["name"] + ".glb")
    png = os.path.join(cl.PREVIEW_MAT, family["name"] + ".png")
    cl.save_blend(blend)
    cl.export_glb([swatches], glb)
    cl.setup_studio(target=(0, 0, 0.10), distance=2.65,
                    elevation_deg=16.0, fov_deg=35.0,
                    resolution=(1100, 460), samples=64,
                    ground_color="#A79C8A")
    cl.render_to(png)
    print("MATERIAL_FAMILY %s label=%s materials=%s tris=%d" % (
        family["id"], family["label"], [m.name for m in mats],
        facts["triangles"]))
    return {
        "id": family["id"],
        "label": family["label"],
        "blend": os.path.relpath(blend, cl.PROJECT).replace("\\", "/"),
        "glb": os.path.relpath(glb, cl.PROJECT).replace("\\", "/"),
        "preview": os.path.relpath(png, cl.PROJECT).replace("\\", "/"),
        "triangles": facts["triangles"],
        "baking": "not_done",
        "engine_note": "GLB uses constant PBR fallbacks; procedural detail is preview-only",
        "materials": [
            {
                "name": m.name,
                "source_hex": m.get("source_hex"),
                "roughness": m.get("engine_roughness"),
                "metallic": m.get("engine_metallic"),
                "emission_strength": m.get("engine_emission_strength"),
                "double_sided": not m.use_backface_culling,
            }
            for m in mats
        ],
    }


def main():
    argv = sys.argv
    args = argv[argv.index("--") + 1:] if "--" in argv else []
    stage = args[0] if args else "all"
    keys = list(FAMILIES) if stage == "all" else [stage]
    for key in keys:
        if key not in FAMILIES:
            raise SystemExit("unknown material family %r" % key)
    records = [build_family(FAMILIES[key]) for key in keys]
    if stage == "all":
        cl.write_json(os.path.join(cl.SRC_MAT, "MAT_families.json"), {
            "schema": "courtyard_materials/1",
            "units": "1 Blender unit = 1 world unit",
            "renderer": "Cycles CPU previews only; no engine verification",
            "families": records,
        })


if __name__ == "__main__":
    main()
