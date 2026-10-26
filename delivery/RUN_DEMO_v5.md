# 秋庭来信 · 完整美术候选运行说明（v5 / N01–N08 返修后）

更新：2026-10-25。该包是**制作侧候选**，不是独立审核通过或正式放行版本。

## 1. 环境

- 工作目录：`C:/软件/鼠鼠`
- Cocos Creator：`tools/cocos/editors/3.8.8/CocosCreator.exe`
- Chrome：`C:/Program Files/Google/Chrome/Application/chrome.exe`
- Python：`C:/Users/tt/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`
- 静态服务：`http://127.0.0.1:8801/`，根目录 `demo/build/web-desktop`

## 2. 打开与运行

1. 保持 8801 静态服务运行；若未运行，用任意静态服务器指向 `demo/build/web-desktop`。
2. Chrome 打开 `http://127.0.0.1:8801/`，等待 `[COURTYARD] READY`。
3. 键盘：WASD/方向键移动，E/空格交互；鼠标点击 UI。
4. 触控：左下摇杆移动，右下按钮交互。
5. 竖屏：显示“请横屏游玩”提示并锁定输入；转回横屏恢复角色/HUD/输入。
6. 页面外壳按窗口自适应；canvas 使用实际视口尺寸，不做 CSS 假竖屏。

## 3. 重新构建（定向）

```powershell
# 只重建受影响阶段（当前候选已构建；改源后使用）
powershell -NoProfile -File tools/blender/run_courtyard_build.ps1 -Stage env_tree,map001
# 复制地图 GLB
Copy-Item art/full/source/layout/MAP001_courtyard.glb demo/assets/resources/models/MAP001_courtyard.glb
# Cocos web-desktop（exit 36 是 3.8.8 已知异常，仅在有 Finished + 有序 SIGTERM + 产物时接受）
& $taskPython -X utf8 tools/cocos/build_web_desktop.py
```

## 4. 证据与检查

```powershell
# 当前构建全状态/资产预览（41 UI states / 34 assets）
node delivery/next_cycle/_t6_all_states.js
# 最终样张、材质/植物近景、demo GIF
node delivery/next_cycle/_v06_game_shots.js finalN2
node delivery/next_cycle/_v06_material_closeups.js finalN2
node delivery/next_cycle/_v06_plant_closeups.js finalN2
node delivery/next_cycle/_t6_demo.js
# Q 行为探针（50 输出）
node delivery/next_cycle/_t5_probe.js
# N04/N05/N07 专项
node delivery/next_cycle/_n04_bbox.js
node delivery/next_cycle/_n05_orientation.js
node delivery/next_cycle/_n07_animation.js
# 重建绑定与 Q 结果（finalN2）
& $taskPython -X utf8 delivery/next_cycle/N_rework/build_n_evidence.py
# 制作侧提交筛选（不产生独立批准）
& $taskPython -X utf8 tools/producer_review.py check --review delivery/next_cycle/T4/producer_self_review.json --out delivery/next_cycle/T4/producer_submission_check.json
```

## 5. N01–N08 对应内容

- N01：树冠改为 6 叶簇 + 外层破形簇；绿篱 3 排 + 侧篱叶卡；增加近景地被。原生 Blender 网格/叶片卡。
- N02：8192 阴影图、bias 0.0002、normal bias 0.20、PCF SOFT_4X；树冠实体关闭投影，新增软接触影与叶卡斑驳。
- N03：半透明纸面、虚线内缘、纤维、手绘涂鸦图标；降低遮挡场景的实心色块。
- N04：可见/隐藏 PlayerWorldQuad 差分实测 bbox 130×130；目标区间经 P1 原图复核，未缩放 Spine。
- N05：真实 fresh portrait + resize 监听；竖屏提示仅锁输入，不注入假状态。
- N06：自评逐维/逐项使用当前构建证据，不沿用旧分数。
- N07：500ms 间隔真实 canvas 帧；idle/move 各 6 个唯一帧，记录 Spine trackTime/bones。
- N08：审阅包逐文件磁盘/ZIP 对照，外部 checksum 单独存放。

## 6. 已知限制

- 独立视觉/规则复核、控制器放行未完成；所有内容仍是 candidate，`accepted=false`。
- 无手机真机测试；Q09 只声明桌面浏览器横屏与竖屏提示，不声明真机通过。
- Q06 的 MAP001/LOOK001 draw calls 715，高于 400 预警线，记录为 warning，不是硬失败；真机性能仍待测。
- 场景为低多边形风格化复刻，与 P1 参考在树冠轮廓、材质细节、光照层次上仍有差距；自评未按 90 门槛通过。
- 角色使用锁定 1015 Spine 源；未重画、未缩放、未用 AI 图。
