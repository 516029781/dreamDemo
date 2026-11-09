# 复现 v14

```bash
python tools/blender_space_base/gen_v14_from_v13.py
blender -b --factory-startup --python tools/blender_space_base/build_scene_v14.py -- \
  --out <ABS>/art/static_map/space_base_minigame/v14/scene.blend
blender -b <v14>/scene.blend --python tools/blender_space_base/render_v14_views.py -- <ABS>/v14/renders
python tools/make_v14_delivery.py
blender -b <v14>/scene.blend --python tools/render_v14_raw.py -- <ABS>/v14/renders/master_raw.png
blender -b <v14>/scene.blend --python tools/check_v14_scene.py -- <OUT>.json
python tools/check_v14_art.py --image <PNG> --out <OUT>.json
python tools/space_base_check_v7.py --request knowledge/active/20261108-space-base-v14-art \
  --candidate art/static_map/space_base_minigame/v14 --run 20261108-2035
```

`V14_NO_COMP=1` 可关闭 compositor 做 A/B；`V14_SAT` 控制暗部饱和度倍率。
隔离复现见 `knowledge/active/20261108-space-base-v14-art/runs/20261108-2035/reproduction.json`。
