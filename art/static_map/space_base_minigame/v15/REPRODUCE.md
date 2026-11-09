# 复现 v15

```
python tools/blender_space_base/gen_v15_from_v14.py
blender -b --python tools/blender_space_base/build_scene_v15.py -- --out art/static_map/space_base_minigame/v15/scene.blend --res 1680x2478 --samples 24
blender -b art/static_map/space_base_minigame/v15/scene.blend --python tools/render_v14_master.py -- <ABS>/renders/master_raw.png
python tools/post_v15.py
blender -b art/static_map/space_base_minigame/v15/scene.blend --python tools/render_v15_hero.py -- <ABS>/renders/hero_raw.png 24
blender -b art/static_map/space_base_minigame/v15/scene.blend --python tools/render_v14_raw.py -- <ABS>/renders/master_raw.png
blender -b art/static_map/space_base_minigame/v15/scene.blend --python tools/check_v15_scene.py -- <ABS>/evidence/scene_checks.json
python tools/run_v15_repro.py
python tools/finalize_v15.py
python tools/space_base_check_v7.py
```

v15 只重建四核心区；`gen_v15_from_v14.py` 从冻结的 v14 builder 确定性派生，其余图层逐字节不变。注意顺序：`post_v15.py` 必须在 `render_v14_raw.py` 覆盖 `master_raw.png` 之前跑，否则 1680 交付图会读成 3360 的源图。
