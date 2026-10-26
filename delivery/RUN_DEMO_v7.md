# 秋庭来信 · candidate_n4 运行说明（v7 / 风格级返修）

更新：2026-10-25。该包是**制作侧候选**，不是独立审核通过或正式放行版本。

## 1. 环境

- 工作目录：`C:/软件/鼠鼠`
- Cocos Creator：`tools/cocos/editors/3.8.8/CocosCreator.exe`
- Chrome：`C:/Program Files/Google/Chrome/Application/chrome.exe`
- Python：`C:/Users/tt/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`
  - 需要 `PYTHONPATH=.tools/pyrembg;.tools/pycv` 才能导入 PIL / OpenCV / jsonschema。
- 静态服务：`http://127.0.0.1:8803/`，根目录 `demo_n4/build/web-desktop`。
- candidate_n2/n3 的冻结包与证据未被覆盖。

## 2. 打开与运行

1. 启动静态服务（若未运行）：
   ```powershell
   & $taskPython -m http.server 8803 --bind 127.0.0.1 --directory demo_n4/build/web-desktop
   ```
2. Chrome 打开 `http://127.0.0.1:8803/`，等待 `[COURTYARD] READY`。
3. 键盘：WASD/方向键移动，E/空格交互，H 切 HUD，P 暂停/继续，Esc 关对白。
4. 触控：左下摇杆移动，右下按钮交互。
5. 竖屏：显示“请横屏游玩”并锁输入；返回横屏保留玩家坐标、任务、相机与留言板状态。
6. 暂停恢复：`__courtyard.setPause(true/false)`；恢复只解锁输入，不回出生点；只有显式 restart 才重置。

## 3. 重新构建（定向）

```powershell
# 主树
& .tools/blender/blender-4.5.15-windows-x64/blender.exe --background --factory-startup --python tools/blender_n4/build_env_courtyard.py -- tree
# 地图
& .tools/blender/blender-4.5.15-windows-x64/blender.exe --background --factory-startup --python tools/blender_n4/build_map001.py
# 复制地图 GLB
Copy-Item art/candidates/candidate_n4/source/layout/MAP001_courtyard.glb demo_n4/assets/resources/models/MAP001_courtyard.glb
# 程序化纹理
& $taskPython -X utf8 tools/textures_n4/make_procedural_textures.py
# 撕纸 UI 母版（SVG -> PNG）
node -e "const {createRequire}=require('module');const req=createRequire('C:/软件/鼠鼠/.tooling/package.json');const sharp=req('sharp');sharp('art/candidates/candidate_n4/ui/components/paper_panel_wash.svg').png().toFile('demo_n4/assets/resources/ui/paper_panel_wash.png').then(()=>sharp('art/candidates/candidate_n4/ui/components/paper_panel_wash.svg').png().toFile('art/candidates/candidate_n4/ui/exports/paper_panel_wash.png'))"
# Cocos web-desktop（exit 36 仅在 Finished + 有序 SIGTERM + 产物时接受）
& $taskPython -X utf8 tools/cocos/build_web_desktop.py --project demo_n4 --config demo_n4/build-config-web-desktop.json --log tools/cocos/logs/build_web_desktop_n4.log --expect-output demo_n4/build/web-desktop/index.html
```

## 4. 证据与检查

```powershell
node delivery/next_cycle/n4/_v06_game_shots_n4.js finalN4
node delivery/next_cycle/n4/_v06_material_closeups_n4.js finalN4
node delivery/next_cycle/n4/_v06_plant_closeups_n4.js
node delivery/next_cycle/n4/_t5_probe_n4.js
node delivery/next_cycle/n4/_n04_bbox_n4.js
node delivery/next_cycle/n4/_n05_orientation_n4.js
node delivery/next_cycle/n4/_n07_animation_n4.js
node delivery/next_cycle/n4/_n4_q04.js
node delivery/next_cycle/n4/_q04_dialogue_n4.js
node delivery/next_cycle/n4/_t6_all_states_n4.js
node delivery/next_cycle/n4/_t6_demo_n4.js
& $taskPython -X utf8 delivery/next_cycle/n4/make_n4_comparisons.py
& $taskPython -X utf8 delivery/next_cycle/n4/make_n4_sheets.py
& $taskPython -X utf8 delivery/next_cycle/n4/make_final_bindings_n4.py
& $taskPython -X utf8 delivery/next_cycle/n4/build_catalog_n4.py
& $taskPython -X utf8 delivery/next_cycle/n4/build_n4_evidence.py
```

Q07 原生源往返：

```powershell
& .tools/blender/blender-4.5.15-windows-x64/blender.exe --background --factory-startup --python tools/blender_n4/q07_n4.py
& .tools/blender/blender-4.5.15-windows-x64/blender.exe --background --factory-startup --python tools/blender_n4/q07_render_n4.py
```

## 5. candidate_n4 相对 n3 的实际变化

- **树**：主枝/侧枝改为连续管状拓扑，删除球形叶团；叶簇改为枝挂双层叶卡，橄榄/金黄/琥珀混合，冠层更密但枝干仍可辨。
- **绿篱/背景**：由离散球体改为连续位移篱墙 + 扁平叶皮；增加第二排、侧篱、墙前低篱与爬墙叶；背景树冠降低到画框内，远处树线替换灰色屋顶块。
- **地面**：新增石边花圃、草簇、三叶/苔藓地被、碎石、中央卵石带、花坛常春藤与落叶堆积；清理铺地纹理的深色碎片与法线墨渍。
- **光照**：降低环境光、提高暖色主光，新增暖色正面补光与背面轮廓；阴影饱和度降低，叶卡/背景不再投影，树冠使用柔和斑驳接触影，避免黑色叶影。
- **UI**：对白/任务卡改为真正半透明撕纸（512×256 九宫格、44px 撕裂边），删除实心内衬；增加纸胶带、纤维、折痕、墨点与统一笔触涂鸦；修复 Label 首帧字体图集造成的文字重影。
- **角色融合**：保留 1015_aglna2 锁定源，仅施加轻微暖色；增加玩家/园丁接触影，场景阴影不再覆盖角色。

## 6. 已知限制

- 无手机/微信真机测试；Q09 只声明桌面浏览器适配。
- Q06：当前构建约 551 draw calls / 1.18M triangles，高于 400 预警线，仍为 warning。
- 完整任务玩法、微信开发者工具、包体/内存/帧率验收不在本候选范围。
- 制作侧自审不是独立审核；`accepted=false`，未签发证书。
