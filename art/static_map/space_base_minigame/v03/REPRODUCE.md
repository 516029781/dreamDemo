# REPRODUCE — space_base_minigame v03 (layout v3.10)

1. Rebuild scene from the plan (deterministic, procedural only, no external textures):
   `blender -b --factory-startup --python tools/blender_space_base/build_scene_v3.py -- --out <dir>/scene_v3.blend`
2. Render 2x supersample:
   `blender -b <dir>/scene_v3.blend --python-expr "import bpy;sc=bpy.context.scene;sc.render.resolution_x=3360;sc.render.resolution_y=5880;sc.cycles.samples=24;sc.render.filepath='<dir>/master_raw.png';bpy.ops.render.render(write_still=True)"`
3. Post-process + gate:
   `python tools/space_base_v3_post.py`
   (master_raw 3360x5880 -> 1680x2940 -> squash 1680x2408 -> 70 px bottom bleed = 1680x2478; writes master/jpg/checks/GATE_REPORT.json)
4. Compare `GATE_REPORT.json`: G1 dims pass, W1 pass, probes:
   - garden_north_gate_120_-14 = light (gate open, 20 m gap)
   - evac_strip_u90_v16.8 = yellow
   - water_sw_20_-240 = deep teal

Orientation: north-up, no mirror step (v02 required a flip; v3.10 does not).
Source of truth: `planning/art/SPACE_BASE_NEW_PLAN_20261103.md` (v3.10), section 8 pixel formula.
