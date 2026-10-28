# 命令与执行记录

工作目录：`C:\软件\鼠鼠\art\static_map\p1_autumn_courtyard\v01`

| 任务 | 命令 | 退出码 | 耗时 / 证据 |
|---|---|---:|---|
| 场景生成与预览 | `blender.exe -b --python build_scene.py` | 0 | 最终构图迭代约 27.75 秒；预览 960×539。 |
| 阶段图 | `blender.exe -b --python make_stages.py` | 0 | 最终运行约 11.56 秒；输出灰模、色块、组合图。 |
| 正式图与保存 `.blend` | `blender.exe -b --python render_final.py` | 0 | 正式 Cycles 渲染 30.39 秒；1920×1078；32 samples。 |
| 重开检查 | `render_final.py` 内 `bpy.ops.wm.open_mainfile` 后重新渲染 | 0 | 能重新打开 `.blend` 并读出 4049 个场景对象。 |
| 局部裁切与并排图 | PowerShell `System.Drawing` 裁切/缩放 | 0 | 输出 `renders/details/detail_*.png` 与 `renders/comparison_p1_vs_final.png`。 |
| 磁盘预检 | `python tools/workflow.py storage --planned-growth-mib 0 --enforce` | 1 | 扫描结果 16,129,522,412 B，高于 15 GiB 项目上限 23,395,052 B；候选本身约 10.24 MiB。未继续启动其他大构建。 |

早期低分辨率试图多次复用 `03_final.png` 文件名，旧版本未逐个保留，故没有为它们编造 SHA 或精确运行时长。此证据缺口见 `METHOD_PROOF.md`，最终产物仍提供源与同机位阶段证据。

