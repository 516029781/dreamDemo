# REPRODUCE — space_base_minigame v04 (layout v3.10, full detail)

1. Rebuild scene (deterministic, procedural only, no external textures):
   `blender -b --factory-startup --python tools/blender_space_base/build_scene_v3.py -- --out <dir>/scene_v4.blend`
   (includes the boolean holes for the buoyancy pool and the blue-room pit)
2. Render 2x supersample:
   `blender -b <dir>/scene_v4.blend --python-expr "import bpy;sc=bpy.context.scene;sc.render.resolution_x=3360;sc.render.resolution_y=5880;sc.cycles.samples=24;sc.render.filepath='<dir>/master_raw.png';bpy.ops.render.render(write_still=True)"`
3. Post-process + gate:
   `python tools/space_base_v3_post.py v04`
   (master_raw 3360x5880 -> 1680x2940 -> squash 1680x2408 -> 70 px bottom bleed = 1680x2478)
4. Probe expectations (GATE_REPORT.json):
   - `garden_north_gate_120_-14` = near-white (zebra)
   - `fountain_ring_120_-39` = teal (~87,113,124)
   - `evac_strip_u90_v16.8` = yellow (255,255,99)
   - `water_sw_20_-240` = deep teal (~63,87,92)

Orientation: north-up, no mirror. Source of truth: plan v3.10 §8 pixel formula.
