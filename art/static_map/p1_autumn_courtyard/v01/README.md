# P1 静态地图美术候选 v01

状态：`quality_below_target`。这是一次完整可重开的 Blender 静帧交付，但没有达到 P1 目标；真实评分为 **35/100**，组合画面四项均为 `rework`。

## 交付物

- `scene.blend`：Blender 5.2.3 原生可编辑场景，Cycles 1920×1078。
- `renders/03_final.png`：正式全尺寸渲染。
- `renders/01_blockout.png`、`01b_color_key.png`、`02_material.png`：固定相机的阶段证据。
- `renders/details/detail_*.png`：物件局部；`renders/comparison_p1_vs_final.png`：主参考并排。
- `reference_analysis/`：固定参考图 SHA、锚点与截图标注。
- `METHOD_PROOF.md`、`REVIEW.md`、`render_log.json`、`COMMANDS.md`：制作尝试、失败点、评分和可复核命令。
- `camera_and_render.json`：锁定相机、灯光、色彩管理与各阶段渲染设置。

## 重开与渲染

从本目录打开 `scene.blend`。需要重新生成完整图时，在项目本机运行：

```powershell
& 'C:\Users\tt\.cache\blender\5.2.3\blender-5.2.3-windows-x64\blender.exe' -b --python render_final.py
```

整个场景由 Blender 原生网格、曲线、材质节点和灯光构成；没有使用 AI Image，也没有外链贴图。

