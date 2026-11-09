# v08 复现步骤（隔离环境）

```bash
BL=<blender 5.2.3 路径>
cd <项目根>

# 1. 重建场景（--factory-startup 隔离）
$BL -b --factory-startup --python tools/blender_space_base/build_scene_v6.py -- \
    --out art/static_map/space_base_minigame/v08/scene.blend

# 2. 三视图渲染（master 3360x5880@32spp / core 2072x1876@32spp / hero 1920x1080@48spp）
$BL -b art/static_map/space_base_minigame/v08/scene.blend \
    --python tools/blender_space_base/render_v6_views.py -- \
    "C:/软件/鼠鼠/art/static_map/space_base_minigame/v08/renders"

# 3. 场景证据（G6/S8/S9/S10）
$BL -b art/static_map/space_base_minigame/v08/scene.blend \
    --python tools/blender_space_base/evidence_v6.py -- \
    "C:/软件/鼠鼠/knowledge/active/20261104-space-base-v8/runs/20261104-1100/evidence"

# 4. 后处理 + 图像证据（G1/G4/G7/W1/W2/S1-S3/S11-S15 + checks + 2D 层）
python tools/space_base_v6_post.py

# 5. 隔离复现（420x735 重渲 vs master_raw，RMS<=8）
$BL -b art/static_map/space_base_minigame/v08/scene.blend \
    --python tools/blender_space_base/repro_v6.py -- \
    "C:/软件/鼠鼠/art/static_map/space_base_minigame/v08/renders/repro.png" \
    "C:/软件/鼠鼠/art/static_map/space_base_minigame/v08/renders/master_raw.png"

# 6. 逐区配色复测（M8.5 硬门）
python tools/color_probe.py art/static_map/space_base_minigame/v08/renders/core_raw.png

# 7. 机械门禁
python tools/space_base_check_v4.py --request knowledge/active/20261104-space-base-v8 \
    --candidate art/static_map/space_base_minigame/v08 --run 20261104-1100
```

依赖：Blender 5.2.3（--factory-startup，无插件）、Python 3.13（numpy/pillow）。
随机性：材质噪声/卡片抖动使用固定 seed（random.seed(5)、噪声基于 Object 坐标确定性）；
渲染采样经 OIDN 降噪，RMS 预期 <8（v05 实测 5.55）。
