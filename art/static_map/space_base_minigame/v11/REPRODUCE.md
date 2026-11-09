# 复现 v11（design r11）

```bash
# 1) 建场景（约 3 min）
blender -b --factory-startup --python tools/blender_space_base/build_scene_v11.py -- \
  --out art/static_map/space_base_minigame/v11/scene.blend

# 2) 出图（master 3360x5880 / hero / route）
blender -b art/static_map/space_base_minigame/v11/scene.blend \
  --python tools/blender_space_base/render_v11_views.py -- \
  art/static_map/space_base_minigame/v11/renders

# 3) 场景证据 GA01-GA15 / G6 / S8-S10
blender -b art/static_map/space_base_minigame/v11/scene.blend \
  --python tools/blender_space_base/evidence_v11.py -- \
  knowledge/active/20261108-space-base-v11-fan/runs/20261108-1500/evidence

# 4) 后处理（S1/S2/S3/S12/S15/G1/GA09）
python tools/space_base_v11_post.py

# 5) 交付与门禁
python tools/make_v11_delivery.py
python tools/space_base_check_v7.py --request knowledge/active/20261108-space-base-v11-fan \
  --candidate art/static_map/space_base_minigame/v11 --run 20261108-1500
```
