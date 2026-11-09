# TEST-03 投影方向（视觉）

- image：`art/static_map/pilot_simple_map/v01/renders/final.png`
- pixel_sha256：`135843d8cdeb2079…`（与 MANIFEST 一致）
- 证据图：`shadow_crops.png`（左矮墙 / 灯柱 / 木箱三处 ×2 放大）

## 判读

| 区域 | 投影落向 | 结论 |
|---|---|---|
| 左矮墙 | 画面右侧、向右下 | 与主光一致 |
| 灯柱 | 向右下偏长条，末端落在台面 | 与主光一致 |
| 木箱+金属桶 | 向右、向右下 | 与主光一致 |

三处同向，无第二方向硬影；环境光为 World 冷灰蓝，不产生独立投影。

**pass**（failure_rule 未触发；sun 的 `rotation_mode` 实测为 `QUATERNION`，符合 `r1_light.py` 记录的写法）。
