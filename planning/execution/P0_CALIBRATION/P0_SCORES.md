# P0 校准结果

两名评分者使用同一份 ANCHORS.md 与同一批帧，互不可见；制作侧分数取自冻结的 n5 自评。

## 逐卡

| 卡片 | 评分者 A | 评分者 B | 制作侧 | A−B | A−制作 | 判定 |
|---|---:|---:|---:|---:|---:|---|
| ENV | 75.00 | 75.00 | 77.50 | 0.00 | 2.50 | 一致 |
| CHAR | 81.25 | 83.75 | 93.75 | 2.50 | 12.50 | 一致 |
| UI | 75.00 | 77.50 | 87.50 | 2.50 | 12.50 | 一致 |
| MIX | 75.00 | 75.00 | 80.00 | 0.00 | 5.00 | 一致 |

## 逐维

| 卡片 | 维度 | 权重 | A | B | 制作侧 | |A−B| | |A−制作| |
|---|---|---:|---:|---:|---:|---:|---:|
| ENV | composition_scale | 20 | 3 | 3 | 3 | 0 | 0 |
| ENV | geometry_craft | 20 | 3 | 3 | 3 | 0 | 0 |
| ENV | material_separation | 20 | 3 | 3 | 3 | 0 | 0 |
| ENV | lighting_contact | 20 | 3 | 3 | 3 | 0 | 0 |
| ENV | vegetation_depth | 10 | 3 | 3 | 4 | 0 | 1 |
| ENV | play_readability | 10 | 3 | 3 | 3 | 0 | 0 |
| CHAR | silhouette_proportion | 20 | 3 | 3 | 4 | 0 | 1 |
| CHAR | line_quality | 15 | 3 | 3 | 4 | 0 | 1 |
| CHAR | cel_color_light | 15 | 3 | 3 | 4 | 0 | 1 |
| CHAR | identity_consistency | 25 | 4 | 4 | 4 | 0 | 0 |
| CHAR | motion_contact | 15 | 3 | 3 | 3 | 0 | 0 |
| CHAR | small_scale_clarity | 10 | 3 | 4 | 3 | 1 | 0 |
| UI | paper_shape | 20 | 3 | 3 | 4 | 0 | 1 |
| UI | doodle_icon_family | 20 | 3 | 3 | 3 | 0 | 0 |
| UI | typography | 20 | 3 | 3 | 3 | 0 | 0 |
| UI | layout_air | 15 | 3 | 3 | 4 | 0 | 1 |
| UI | state_feedback | 15 | 3 | 3 | 4 | 0 | 1 |
| UI | palette_restraint | 10 | 3 | 4 | 3 | 1 | 0 |
| MIX | visual_language | 25 | 3 | 3 | 3 | 0 | 0 |
| MIX | color_light_coherence | 25 | 3 | 3 | 3 | 0 | 0 |
| MIX | grounding_occlusion | 20 | 3 | 3 | 4 | 0 | 1 |
| MIX | focus_readability | 15 | 3 | 3 | 3 | 0 | 0 |
| MIX | world_style_coherence | 15 | 3 | 3 | 3 | 0 | 0 |

## 结论

- 两名评分者的最大逐卡差：**2.50 分**（阈值 3）→ PASS
- 逐维平均差：0.09 分；与制作侧逐维平均差：0.35 分
- 与制作侧的最大逐卡差：12.50 分
- 差异最大的维度：small_scale_clarity(-1), palette_restraint(-1), composition_scale(+0), geometry_craft(+0), material_separation(+0)
