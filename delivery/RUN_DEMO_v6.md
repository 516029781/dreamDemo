# 秋庭来信 · candidate_n3 运行说明（v6 / N01–N09 返修后）

更新：2026-10-25。该包是**制作侧候选**，不是独立审核通过或正式放行版本。

## 1. 环境

- 工作目录：`C:/软件/鼠鼠`
- Cocos Creator：`tools/cocos/editors/3.8.8/CocosCreator.exe`
- Chrome：`C:/Program Files/Google/Chrome/Application/chrome.exe`
- Python：`C:/Users/tt/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`
- 静态服务：`http://127.0.0.1:8802/`，根目录 `demo_n3/build/web-desktop`
- candidate_n2 仍保留在 `demo/build/web-desktop`（8801），未覆盖。

## 2. 打开与运行

1. 保持 8802 静态服务运行；若未运行，用任意静态服务器指向 `demo_n3/build/web-desktop`。
2. Chrome 打开 `http://127.0.0.1:8802/`，等待 `[COURTYARD] READY`。
3. 键盘：WASD/方向键移动，E/空格交互；鼠标点击 UI。
4. 触控：左下摇杆移动，右下按钮交互。
5. 竖屏：显示“请横屏游玩”提示并锁定输入；转回横屏恢复角色/HUD/输入，保留移动后的玩家坐标与相机目标。
6. 暂停恢复：`__courtyard.setPause(true/false)`；恢复只清输入，不重置玩家位置；只有重新开始/restart 才回出生点。
7. 页面外壳按窗口自适应；canvas 使用实际视口尺寸，不做 CSS 假竖屏。

## 3. 重新构建（定向）

```powershell
# 原生源阶段（当前候选已构建；改源后使用）
powershell -NoProfile -File tools/blender_n3/run_courtyard_build.ps1 -Stage env_tree,env_ring_planter,env_side_planter
# 长椅源（独立脚本）
& .tools/blender/blender-4.5.15-windows-x64/blender.exe --background --factory-startup --python tools/blender_n3/prop001_bench.py -- build
# 地图
powershell -NoProfile -File tools/blender_n3/run_courtyard_build.ps1 -Stage map001
# 复制地图 GLB
Copy-Item art/candidates/candidate_n3/source/layout/MAP001_courtyard.glb demo_n3/assets/resources/models/MAP001_courtyard.glb
# 纹理
& $taskPython -X utf8 tools/textures_n3/make_procedural_textures.py
# UI 纸片导出
node tools/ui_n3/build_ui.js
Copy-Item art/candidates/candidate_n3/ui/exports/paper_panel_128.9slice.png demo_n3/assets/resources/ui/paper_panel_384.png
# Cocos web-desktop（exit 36 仅在 Finished + 有序 SIGTERM + 产物时接受）
& $taskPython -X utf8 tools/cocos/build_web_desktop.py --project demo_n3 --config demo_n3/build-config-web-desktop.json --log tools/cocos/logs/build_web_desktop_n3.log --expect-output demo_n3/build/web-desktop/index.html
```

## 4. 证据与检查

```powershell
node delivery/next_cycle/_v06_game_shots_n3.js finalN3
node delivery/next_cycle/n3/_t5_probe_n3.js
node delivery/next_cycle/n3/_n04_bbox_n3.js
node delivery/next_cycle/n3/_n05_orientation_n3.js
node delivery/next_cycle/n3/_n07_animation_n3.js
node delivery/next_cycle/n3/_n3_q04.js
node delivery/next_cycle/n3/_q04_dialogue_n3.js
node delivery/next_cycle/n3/_t6_all_states_n3.js
node delivery/next_cycle/n3/_v06_material_closeups_n3.js finalN3
node delivery/next_cycle/n3/_v06_plant_closeups_n3.js finalN3
node delivery/next_cycle/n3/_t6_demo_n3.js
& $taskPython -X utf8 delivery/next_cycle/n3/build_n3_evidence.py
& $taskPython -X utf8 delivery/next_cycle/n3/build_catalog_n3.py
```

## 5. N01–N09 对应内容

- N01：主树更细分枝与叶卡、平滑树冠核心；中心花坛改为连续石鼓+浅接缝；长椅增加扶手/横撑/螺栓与更细分板；绿篱增加第四排；前景增加长椅与叶堆。
- N02：1024 石材/木纹、512 金属/树皮/土壤纹理；运行时生成 stone/wood/metal/soil 的 normal+pbr map；提高接触遮蔽强度；保留 8192 soft shadow，新增暖色反弹补光。
- N03：对白面板 176px（24.4% 高）、外缘半透明+内层纸、手绘边角/纸胶带/纤维/叶枝、提高字色对比；任务卡也采用双层纸。
- N04：可见/隐藏 PlayerWorldQuad 差分 bbox 130×130；目标区间经 P1 原图复核，未缩放 Spine。
- N05：真实 fresh portrait + resize 监听；竖屏锁输入、横屏恢复；从移动位置返回不回跳。
- N07：500ms 间隔真实 canvas 帧；idle/move 各 6 个唯一帧，记录 Spine trackTime/bones。
- N09：`setPause(false)` 只恢复输入并保留玩家坐标/相机/任务/板状态；`resetView` 只用于显式重新开始；竖屏返回也走保留状态路径。Q04 从键盘 1.05m、触控 1.80m 处分别验证。

## 6. 已知限制

- 独立视觉/规则复核、控制器放行未完成；所有内容仍是 candidate，`accepted=false`。
- 无手机真机测试；Q09 只声明桌面浏览器横屏与竖屏提示，不声明真机通过。
- Q06 MAP001/LOOK001 draw calls 768、triangles 520946，高于 400/400k 预警线，记录为 warning，不是硬失败；真机性能仍待测。
- 场景为低多边形风格化复刻，与 P1 在树冠轮廓、材质细节、光照层次上仍有差距；自评未按 90 门槛通过。
- 角色使用锁定 1015 Spine 源；未重画、未缩放、未用 AI 图。
