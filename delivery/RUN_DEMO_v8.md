# 秋庭来信 · candidate_n5 运行说明（v8 / 结构与证据链返修）

更新：2026-10-26。该包是**制作侧候选**，不是独立审核通过或正式放行版本。
n2 / n4 的冻结包、构建与证据一律只读，未被覆盖。

## 1. 环境

- 工作目录：`C:/软件/鼠鼠`
- Cocos Creator：`tools/cocos/editors/3.8.8/CocosCreator.exe`
- Chrome：`C:/Program Files/Google/Chrome/Application/chrome.exe`
- Blender：`.tools/blender/blender-4.5.15-windows-x64/blender.exe`
- Python：`C:/Users/tt/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`
  - 需 `PYTHONPATH=.tools/pyrembg;.tools/pycv` 才能导入 PIL / OpenCV / jsonschema。
- 静态服务：`http://127.0.0.1:8805/`，根目录 `demo_n5/build/web-desktop`。
  （n4 使用 8803，两者互不干扰。）

## 2. 打开与运行

1. 启动静态服务：
   ```bash
   python -m http.server 8805 --bind 127.0.0.1 --directory demo_n5/build/web-desktop
   ```
2. Chrome 打开 `http://127.0.0.1:8805/`，等待 `[COURTYARD] READY`。
3. 键盘：WASD/方向键移动，E/空格交互，H 切 HUD，P 暂停/继续，Esc 关对白。
4. 触控：左下摇杆移动，右下按钮交互。
5. 竖屏：显示"请横屏游玩"并锁输入；返回横屏保留玩家坐标、任务、相机与留言板状态。

## 3. n5 构建契约（与 n4 的关键差别）

n4 的失败点之一是「截图来自一个构建、Q 结果来自另一个」。n5 用**显式构建钉**取代
「取目录里最新的构建报告」：

- `tools/n5_build.py` 构建一次并写 `delivery/next_cycle/n5/performance/formal_build.json`，
  记录 `build_id`、构建报告路径、日志路径、以及所有影响画面的输入 SHA。
- 采集脚本在开跑前调用 `_n5_pin.js` 的 `assertPinnedBuild()`；服务中的
  `index.html` 与钉住的 SHA 不一致就直接失败。
- 绑定 / Q / catalog / spec 全部从钉读取 `build_id`，不再 `glob(...)[-1]`。
- 重建即令全部截图与 Q 失效；必须重新采集，不能混用旧 JSON。

## 4. 重新构建

```bash
# 主树（默认 variant=A，即基线；B/C 为消融）
& .tools/blender/blender-4.5.15-windows-x64/blender.exe --background --factory-startup \
    --python tools/blender_n5/build_env_courtyard.py -- tree

# 地图（N5_PAVING_VARIANTS=1 启用铺装变体；N5_NO_* 关闭远景层做 A2 隔离）
& .tools/blender/blender-4.5.15-windows-x64/blender.exe --background --factory-startup \
    --python tools/blender_n5/build_map001.py
cp art/candidates/candidate_n5/source/layout/MAP001_courtyard.glb \
   demo_n5/assets/resources/models/MAP001_courtyard.glb

# 程序化纹理与树影贴花
& $taskPython -X utf8 tools/textures_n5/make_procedural_textures.py
& .tools/blender/blender-4.5.15-windows-x64/blender.exe --background --factory-startup \
    --python tools/blender_n5/bake_tree_shadow.py
& $taskPython -X utf8 tools/textures_n5/make_tree_shadow_decal.py

# 唯一正式构建（写构建钉；已存在时拒绝覆盖）
& $taskPython -X utf8 tools/n5_build.py --run-id <run_id> --reason "<why>"
```

A2 逐层定位（一次构建、多次渲染，不用重建地图）：

```bash
& .tools/blender/blender-4.5.15-windows-x64/blender.exe --background --factory-startup \
    --python tools/blender_n5/render_bg_layers.py
```

## 5. 证据

```bash
node delivery/next_cycle/n5/_v06_game_shots_n5.js finalN5
node delivery/next_cycle/n5/_v06_material_closeups_n5.js finalN5
node delivery/next_cycle/n5/_v06_plant_closeups_n5.js
node delivery/next_cycle/n5/_t5_probe_n5.js
node delivery/next_cycle/n5/_n04_bbox_n5.js
node delivery/next_cycle/n5/_n05_orientation_n5.js
node delivery/next_cycle/n5/_n07_animation_n5.js
node delivery/next_cycle/n5/_n5_q04.js
node delivery/next_cycle/n5/_q04_dialogue_n5.js
node delivery/next_cycle/n5/_t6_all_states_n5.js
node delivery/next_cycle/n5/_t6_demo_n5.js
```

## 6. 日志

- `delivery/next_cycle/n5/performance/events.jsonl`：逐阶段起止、单调耗时、输入/输出 SHA。
- `performance/commands.txt`：实际命令、工作目录、退出码、日志路径。
- `performance/logs/`：每次运行的原始 stdout/stderr，文件名带 run_id 与 UTC 时间戳。
- `performance/decisions.jsonl`：每个返修批次的假设、改动、观察、反例、结论。
- `performance/baseline_n5.json`：n5 从 n4 继承的可编辑源清单与 SHA。

执行日志**不**打进源 ZIP（它们在本轮仍在变化），源 ZIP 只含可编辑源与冻结证据 JSON。
