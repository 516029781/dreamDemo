# 秋庭来信 · 完整美术候选运行说明（v4）

更新：2026-10-25。该包是完整美术候选，不是独立审核或正式放行版本。

## 1. 环境

- 工作目录：`C:/软件/鼠鼠`
- Cocos Creator：`tools/cocos/editors/3.8.8/CocosCreator.exe`
- Chrome：`C:/Program Files/Google/Chrome/Application/chrome.exe`
- Python：`C:/Users/tt/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`
- 服务：本机 `http://127.0.0.1:8801/` 已运行，根目录 `demo/build/web-desktop`。

## 2. 打开与运行

1. 保持 8801 静态服务运行；若未运行，用任意静态服务器指向 `demo/build/web-desktop`。
2. 浏览器打开 `http://127.0.0.1:8801/`，等待 `[COURTYARD] READY`。
3. 键盘：WASD/方向键移动，E/空格交互；鼠标点击 UI。
4. 触控：左下摇杆移动，右下按钮交互；竖屏显示“请横屏游玩”。

## 3. 重新构建（定向）

```powershell
# 只重建受影响阶段（当前候选已构建；改源后使用）
powershell -NoProfile -File tools/blender/run_courtyard_build.ps1 -Stage env_tree,map001
# 复制地图 GLB
Copy-Item art/full/source/layout/MAP001_courtyard.glb demo/assets/resources/models/MAP001_courtyard.glb
# Cocos web-desktop（exit 36 是 3.8.8 已知异常，仅在有 Finished + 有序 SIGTERM + 产物时接受）
python -X utf8 tools/cocos/build_web_desktop.py
```

## 4. 证据与检查

```powershell
# 当前构建全状态/资产预览
node delivery/next_cycle/_t6_all_states.js
# 采集绑定
python -X utf8 delivery/next_cycle/T3/make_final_bindings.py
# 质量检查
python -X utf8 tools/art_gate/check_quality.py --results delivery/next_cycle/T5/behavior_results.json --binding delivery/next_cycle/T3/bindings/binding_formal_no_ui.json
# 制作侧提交筛选（不产生独立批准）
python -X utf8 tools/producer_review.py check --review delivery/next_cycle/T4/producer_self_review.json --out delivery/next_cycle/T4/producer_submission_check.json
```

## 5. 已知限制

- 独立视觉/规则复核与控制器放行尚未完成；所有内容都是 candidate。
- 无手机真机测试；Q09 只声明浏览器横屏与竖屏提示。
- Q06 draw calls 高于 400 预警线，记录为 warning，不是硬失败。
- headless 下角色 Spine 帧未推进，角色运动证据使用锁定源的真实 idle/move 播放文件；场景 demo 用实际移动帧。
- 旧 T1/T2 页面截图仅历史，不作为当前构建证据。
