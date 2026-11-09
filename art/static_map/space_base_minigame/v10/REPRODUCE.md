# v10 复现步骤（隔离环境）

```bash
BL=<blender 5.2.3 路径>
cd <项目根>

# 1. 重建场景（--factory-startup 隔离）
$BL -b --factory-startup --python tools/blender_space_base/build_scene_v10.py -- \
    --out art/static_map/space_base_minigame/v10/scene.blend

# 2. 三视图（master 3360x5880@32spp / core 2072x1876@32spp / hero 1920x1080@48spp）
$BL -b art/static_map/space_base_minigame/v10/scene.blend \
    --python tools/blender_space_base/render_v10_views.py -- \
    "C:/软件/鼠鼠/art/static_map/space_base_minigame/v10/renders"

# 3. 花园近景 + 挡墙 + HeroRoute（GA03/GA04/GA09）
$BL -b art/static_map/space_base_minigame/v10/scene.blend \
    --python tools/blender_space_base/render_v10_garden.py -- \
    "C:/软件/鼠鼠/art/static_map/space_base_minigame/v10/renders" 32 1.0

# 4. 场景证据（G6/S8/S9/S10 + GA01-GA08）
$BL -b art/static_map/space_base_minigame/v10/scene.blend \
    --python tools/blender_space_base/evidence_v10.py -- \
    "C:/软件/鼠鼠/knowledge/active/20261105-space-base-v10-garden/runs/20261105-1800/evidence"

# 5. 后处理 + 图像证据（G1/G4/G7/W1/W2/S1-S3/S11-S15 + GA09 + checks 01-05）
python tools/space_base_v10_post.py

# 6. 隔离复现（420x735 重渲 vs master_raw，RMS<=8）
$BL -b art/static_map/space_base_minigame/v10/scene.blend \
    --python tools/blender_space_base/repro_v10.py -- \
    "C:/软件/鼠鼠/art/static_map/space_base_minigame/v10/renders/repro.png" \
    "C:/软件/鼠鼠/art/static_map/space_base_minigame/v10/renders/master_raw.png"

# 7. 五件套 + GA10
python tools/make_v10_delivery.py

# 8. 机械门禁
python tools/space_base_check_v7.py --request knowledge/active/20261105-space-base-v10-garden \
    --candidate art/static_map/space_base_minigame/v10 --run 20261105-1800
```

依赖：Blender 5.2.3（--factory-startup，无插件）、Python 3.13（numpy/pillow）。
随机性：材质噪声/卡片抖动固定 seed；渲染经 OIDN 降噪。
近景（near/）与三张英雄变体（hero/HeroWide|Mid|Low）为补充图，不进门禁。
