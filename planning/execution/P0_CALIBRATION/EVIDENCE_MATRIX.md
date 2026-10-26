# P0 证据矩阵

● 适用且已有证据　○ 适用但缺证据　◐ 有帧但目标被遮挡、不可用于判档　△ 该帧不构成独立视角　— 不适用

| 维度 | 权重 | F1<br>俯视全景 | F2<br>同机位 | F3<br>对白中景 | F4<br>树后低角 | F5<br>告示板近景 | F6<br>竖屏安全区 | M1<br>独立机位1 正面全景 | M2<br>独立机位2 侧向45° | M3<br>独立机位3 东南中位 |
|---|---|---|---|---|---|---|---|---|---|---|
| composition_scale | 20 | ● | ● | ● | ● | ● | △ | ● | ● | ● |
| geometry_craft | 20 | ● | ● | ● | ● | ● | △ | ● | ● | ● |
| material_separation | 20 | ● | ● | ● | ● | ● | △ | ● | ● | ● |
| lighting_contact | 20 | ● | ● | ● | ● | ● | △ | ● | ● | ● |
| vegetation_depth | 10 | ● | ● | ● | ● | ● | △ | ● | ● | ● |
| play_readability | 10 | ● | ● | ● | ● | ● | △ | ● | ● | ● |
| silhouette_proportion | 20 | ● | ● | ● | ◐ | — | △ | ● | ● | ● |
| line_quality | 15 | ● | ● | ● | ◐ | — | △ | ● | ● | ● |
| cel_color_light | 15 | ● | ● | ● | ◐ | — | △ | ● | ● | ● |
| identity_consistency | 25 | ● | ● | ● | ◐ | — | △ | ● | ● | ● |
| motion_contact | 15 | ● | ● | ● | ◐ | — | △ | ● | ● | ● |
| small_scale_clarity | 10 | ● | ● | ● | ◐ | — | △ | ● | ● | ● |
| paper_shape | 20 | — | ● | ● | — | — | ● | — | ● | — |
| doodle_icon_family | 20 | — | ● | ● | — | — | ● | — | ● | — |
| typography | 20 | — | ● | ● | — | — | ● | — | ● | — |
| layout_air | 15 | — | ● | ● | — | — | ● | — | ● | — |
| state_feedback | 15 | — | ● | ● | — | — | ● | — | ● | — |
| palette_restraint | 10 | — | ● | ● | — | — | ● | — | ● | — |
| visual_language | 25 | ● | ● | ● | ● | ● | △ | ● | ● | ● |
| color_light_coherence | 25 | ● | ● | ● | ● | ● | △ | ● | ● | ● |
| grounding_occlusion | 20 | ● | ● | ● | ● | ● | △ | ● | ● | ● |
| focus_readability | 15 | ● | ● | ● | ● | ● | △ | ● | ● | ● |
| world_style_coherence | 15 | ● | ● | ● | ● | ● | △ | ● | ● | ● |

统计：可用证据 148 格，缺证据 0 格，目标被遮挡 6 格，不构成独立视角 17 格。

## 机位清单

| 代号 | 文件 | 说明 |
|---|---|---|
| M1 | pose_m1_front_no_ui.png | 独立机位1，与正式机位同机位，基准 |
| M2 | pose_m2_side_no_ui.png | 独立机位2，侧向 45°，角色 161 px |
| M3 | pose_m3_southeast_no_ui.png | 独立机位3，东南中位，角色 188 px |
| F1 | q01_formal_no_ui.png | 俯视全景，Q01 构图机位（唯一判 composition_scale 的帧） |
| F3 | q01_dialogue.png | 对白中景，角色下半身被面板压住 |
| F4 | q03_behind.png | 树后低角，角色被树冠遮约八成，不可用于判档 |
| F5 | q05_board_full.png | 告示板近景，验证材质与构造 |

F2 与 F1 同机位仅差 UI 叠加（缩略图差异 6.14/255）；F6 是同一画面的竖屏裁切加提示层，两者都不构成独立视角。M1/M2/M3 是契约 v2.1 §3.1 要求的三个独立机位，由 `delivery/next_cycle/n5/_p0b_poses.js` 在同一构建上拍摄，未改资产、未重建。
