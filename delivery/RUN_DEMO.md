# 秋庭 art_complete 候选包（Cocos Creator 3.8.8）运行说明

状态：**47 组全部具备可编辑源、引擎预览与逐项 review；art_complete 机械包待外部独立审核/controller 签认。**不是微信发布包，`accepted=false`。

## 源与构建

- Cocos Creator：`C:\软件\鼠鼠\tools\cocos\editors\3.8.8\CocosCreator.exe`（3.8.8）
- 工程源：`C:\软件\鼠鼠\demo\`；源码包：`delivery/courtyard_scene_demo_sources_v3.zip`
- web-desktop 构建：`C:\软件\鼠鼠\demo\build\web-desktop`（1280×720）
- 场景：`demo/assets/scenes/main.scene`；脚本：`demo/assets/scripts/CourtyardBootstrap.ts`
- 构建配置：`demo/build-config-web-desktop.json`
- 角色：`demo/assets/resources/char/1015_aglna2.*`（Spine 3.8）
- NPC：`demo/assets/resources/char/npc_gardener_slice.png`，由已批准的 t054 裁切经前景分割 matte 清理（非生成式），静态显示并带轻微摆动
- 地图：`demo/assets/resources/models/MAP001_courtyard.glb`（源 `art/full/source/layout/MAP001_courtyard.blend`）
- UI 图标/FX：`art/full/ui/components/icons/*.svg`、`art/full/source/fx/*.svg` 的真实 PNG 导出

MAP001：129 个布局实例合并为 74 个 mesh/文字渲染对象，92,976 三角面，24 个材质。Cocos 中地面/铺装不投自身阴影，树/灯/廊架/长椅/花坛等投射阴影。

## 干净重建

```bash
cd "C:/软件/鼠鼠"
unset ELECTRON_RUN_AS_NODE
"C:/软件/鼠鼠/tools/cocos/editors/3.8.8/CocosCreator.exe" \
  --project "C:/软件/鼠鼠/demo" \
  --build "configPath=C:/软件/鼠鼠/demo/build-config-web-desktop.json"
```

日志：`tools/cocos/logs/build_viewer_final2.out.txt`。已知 CLI 退出码 36 是编辑器退出时 `build-script` 子进程收到 SIGTERM 的产物行为；日志末有 `Finished`，以新产物 + 引擎截图为构建证据。

## 启动与查看器

```bash
cd C:/软件/鼠鼠/demo/build/web-desktop
npx --yes http-server -p 8801 -c-1 .
# 另一终端
cd C:/软件/鼠鼠
node tools/engine_capture.js          # 主场景/对白/移动 GIF
node tools/engine_viewer_capture.js   # 41 UI 状态 + 34 资产镜头
```

页面 API：

```js
__courtyard.resetView();
__courtyard.setUiState('hud_1_3');
__courtyard.focusAsset('ENV006');
__courtyard.focusAsset('CHAR003');
__courtyard.openDialogue(1);
__courtyard.setUi(false);
```

## 证据

- 主场景：`art/full/previews/engine/scene_gameplay_1280x720.png`
- 无 UI：`art/full/previews/engine/scene_no_ui_1280x720.png`
- 对白：`art/full/previews/engine/dialogue_npc_1280x720.png`、`dialogue_player_1280x720.png`
- 移动：`art/full/previews/engine/demo_recording.gif`（24 帧，Move 动画）
- UI 41 状态：`art/full/previews/engine/ui_states/*.png`
- 资产 34 镜头：`art/full/previews/engine/assets/*.png`
- 运行日志/状态：`viewer_capture.log`、`viewer_state.json`、`engine_capture.log`、`engine_state.json`
- 完整目录：`art/full/art_complete_catalog.json`；逐项 review：`art/full/reviews/<ID>.json`

## 已实测

- 完整 MAP001、真实 3D 相机/灯光/阴影、Spine 1015 Relax/Move、NPC 静态切片、HUD/对白/摇杆/交互按钮、标题/加载/暂停/完成/提示/安全区、FX001 接触阴影、FX002 拾取星芒、FX003 留言板卡片状态。
- 41 个 UI 状态和 34 个资产镜头均由同一次 Cocos 构建生成；无 load error。
- 47 组 catalog 均为 `engine_verified`，每项 review 绑定引擎预览证据。

## 未验证 / 限制

- MAP001 的拾取、留言板提交、遮挡淡出、任务流程与完整碰撞属于 G1，不在本美术包内。
- `rotate_notice` 是 1280×720 引擎布局示意；真实 720×1280 设备旋转尚未验证。
- MAT 组为程序材质引擎近景，未声称烘焙贴图；字体未做微信子集。
- 无微信构建/真机/性能/安全区实测；桌面帧率不能冒充手机结论。
- 独立视觉审核与 controller attestation 未完成；H09/H05 与四卡评分仍由外部审核者执行，`accepted=false`。
