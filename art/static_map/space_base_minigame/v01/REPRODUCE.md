# REPRODUCE — space_base_minigame v01

1. Copy `scene.blend` to an isolated directory (no external textures/assets).
2. Render:
   `blender -b <copy>/scene.blend --python tools/blender_space_base/render_only.py -- --out <copy>/master_raw.png --res 3840x5120 --samples 32`
3. Mirror horizontally:
   `python tools/space_base_export.py flip --in <copy>/master_raw.png --out <copy>/master_repro_flipped.png`
4. Compare content SHA with `C:\软件\鼠鼠\art\static_map\space_base_minigame\v01\renders\space_base_v01_master.png`: `e40212cf8ec8d5e893839c83c167616ffb33dffa0a6be0105723425da0046702`.
   Allowed difference: RMS <= 2.0/255.
   Recorded: pass (RMS=0.0/255, tol=2.0)

The scene uses procedural materials only; no external textures. The mirror is required by C2 (`px=x*8`, west-left, south-up).
