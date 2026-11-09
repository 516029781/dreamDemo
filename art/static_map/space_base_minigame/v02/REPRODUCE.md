# REPRODUCE — space_base_minigame v02

1. Copy `scene.blend` to an isolated directory (no external textures/assets).
2. Render:
   `blender -b <copy>/scene.blend --python tools/blender_space_base/render_only.py -- --out <copy>/master_raw.png --res 3840x5120 --samples 32`
3. Mirror horizontally:
   `python tools/space_base_export.py flip --in <copy>/master_raw.png --out <copy>/master_repro_flipped.png`
4. Compare content SHA with `C:\软件\鼠鼠\art\static_map\space_base_minigame\v02\renders\space_base_v02_master.png`: `35e0cd8251d14595c34a006d04d6a21fa530de6f7cb214a61faae296a654b9c8`.
   Allowed difference: RMS <= 2.0/255.
   Recorded: not_run

The scene uses procedural materials only; no external textures. The mirror is required by C2 (`px=x*8`, west-left, south-up).
