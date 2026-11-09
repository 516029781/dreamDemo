# v14 开发记录（单批次）

- 生成器：`tools/blender_space_base/gen_v14_from_v13.py`（22 处替换 + 追加 `apply_v14_art`）
- 构建：`tools/blender_space_base/build_scene_v14.py` → `v14/scene.blend`
- 渲染：`render_v14_quick.py` / `render_v14_master.py` / `render_v14_views.py` / `render_v14_raw.py`
- 检查：`check_v14_art.py` / `check_v14_scene.py` / `check_v14_grounding.py`
- 交付：`make_v14_delivery.py` / `finalize_v14.py` / `space_base_check_v7.py`

## 返修单（HARNESS_LIFECYCLE §4）

| id | 现象 → 根因 → 源级修改 → 重跑 | 结果 |
|---|---|---|
| H1/r2 | S1 0.017；全局 HueSat 提饱和 + 整体减光使 `sat≤0.28` 与 `L≥0.62` 同时塌陷；提亮 Sun/World、温和分级、加亮度门控掩码 | S1 0.4483 |
| H2/r3 | 掩码未接上（CompositorNodeValToRGB 输出名不是 `Color`）；改用 `outputs[0]`；并按 §6 提 platform +4% | 见最终指标 |

## 关键实现取舍

- `--art=off` 未做：颜色/纹理/倒角已写进源脚本常量；A/B 以冻结的 v13 候选对照。
- compositor 在 `build_camera_light` 之后建，确保不被后续构建覆盖。
- 雾仅英雄图启用，俯视 master 保持隐藏（否则遮地图）。
- Glare 用 FOG_GLOW + 低 Strength；不用 LUT（Blender 4.5 无该节点）、不用暗角。
