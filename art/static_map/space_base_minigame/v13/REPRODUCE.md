# 复现 v13（design r15）

```bash
blender -b --factory-startup --python tools/blender_space_base/build_scene_v13.py -- \
  --out art/static_map/space_base_minigame/v13/scene.blend

blender -b art/static_map/space_base_minigame/v13/scene.blend \
  --python tools/blender_space_base/render_v13_views.py -- <ABS>/v13/renders

blender -b art/static_map/space_base_minigame/v13/scene.blend \
  --python tools/render_v13_raw.py -- <ABS>/v13/renders/master_raw.png  # 3360x5880

blender -b art/static_map/space_base_minigame/v13/scene.blend \
  --python tools/check_v13_workshop.py -- <ABS>/evidence
blender -b art/static_map/space_base_minigame/v13/scene.blend \
  --python tools/check_v13_organic.py -- <ABS>/evidence
```

隔离复现（content SHA，非 container SHA）：`tools/repro_v13_render.py`，
420x620 / 8 samples / seed 0。结果见 `runs/20261108-1755/reproduction.json`。

业务门禁：`python tools/space_base_check_v7.py --request knowledge/active/20261108-space-base-v13-testworkshop --candidate art/static_map/space_base_minigame/v13 --run 20261108-1755`
