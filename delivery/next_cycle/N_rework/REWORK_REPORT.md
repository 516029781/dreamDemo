# N01–N08 集中返修报告（制作侧）

日期：2026-10-25。对象：`art_review/reports/independent_20261025_candidate/REPORT.md`。
性质：制作侧返修与自审，**不是独立审核、不是控制器放行**。`accepted=false`。

## 结论摘要

- Q01、Q09、N07 证据链已按真实引擎行为重做；Q01–Q09 在 finalN2 构建上全部机械通过。
- N01/N02/N03 用原生 Blender/引擎改动完成一轮视觉迭代；N04/N05/N07 由真实测量/事件/画面证明。
- **制作侧完整候选 90 分门槛未达到**：ENV 70.00 / CHAR 93.75 / UI 75.00 / MIX 75.00。
  按 `PRODUCER_SELF_REVIEW.md`，`producer_review.py check` 返回 `producer_rework_required`。
- 该结果如实提交给最终审核，不把 70/75 的卡片包装成 90，也不把制作侧自检说成独立通过。

## 当前可审产物

- 冻结 manifest：`art_review/submissions/candidate_n2/manifest.json`
  （sha256 `890dfe78372c63f6945b5807368f5c577b365223d8d5053a2766d2a4c14db946`）
- 自审报告：`delivery/next_cycle/T4/producer_self_review.json`
- 自审筛选结果：`delivery/next_cycle/T4/producer_submission_check.json`
- 运行说明：`delivery/RUN_DEMO_v5.md`
- 源包：`delivery/courtyard_scene_demo_sources_v5.zip`
- 最终审阅包与外部校验和：`delivery/candidate_n2_review_pack_20261025.zip` 及 `.sha256`
- 打包核验：`delivery/N08_pack_verification.json`

## 逐项返修

| ID | 原问题 | 实际修改 | 当前证据 | 制作侧结论 |
|---|---|---|---|---|
| N01 | 树冠/绿篱重复体块、裸土多、层次弱 | 主树 6 叶簇+外层破形簇，分枝深度 3；绿篱 3 排+侧篱叶卡；新增近景地被。原生网格/叶卡，非位图生成 | `T4/N01_tree_hedge_before_after.png`、`T3/game_finalN2_formal_no_ui.png`、`T6/assets/ENV006.png` | 已改，残余：树冠仍偏低模，几何工艺自评 2 |
| N02 | 树影阶梯块、材质近景弱 | 8192 阴影图、bias 0.0002、normal bias 0.20、PCF SOFT_4X；冠部实体关闭投影；新增 7.2×6.4 软接触影与叶卡斑驳；石/木/金属纹理增强 | `T4/N02_shadow_before_after.png`、`T4/N02_material_closeups.png`、`T3/mat_finalN2_*.png`、`T2/lighting_settings_finalN2.json` | 已改，残余：环境反弹光仍少 |
| N03 | 不透明奶油面板、双框、规整图标 | 半透明纸面、虚线内缘、纤维、手绘涂鸦（标题/对白/HUD）；降低遮挡场景的实心色块 | `T4/N03_ui_before_after.png`、`T3/game_finalN2_formal_ui.png`、`T6/state_index.json` | 已改，残余：纸片仍比 P1 规整 |
| N04 | Q01 用投影代理，非真实角色 bbox | 可见/隐藏 `PlayerWorldQuad` 同帧差分；实测 130×130px；P1 t084 复核 720p 约 107.5px；未缩放 Spine，FOV 37.5 校准 | `T4/N04_actor_bbox.png`、`N_rework/N04_bbox.json`、`N04_actor_visible.png`/`hidden.png` | 已修，Q01 pass |
| N05 | Q09 注入 `rotate_notice`，自然竖屏仍 1280×720 | data 场景监听 resize/orientationchange；fresh portrait 与 resize 均 720×1280、`rotate_notice`、输入锁；转回横屏清 viewer/恢复输入 | `T4/N05_orientation.png`、`N_rework/N05_orientation.json`、`T5/q09_viewports.json` | 已修，Q09 pass |
| N06 | 自评复用样张分数、逐项理由空泛 | 新自评逐维绑定 N06 证据索引与真实画面，四卡分别 70/93.75/75/75；47 项逐项使用 cycle_03 项目审查与当前预览 | `N_rework/N06_evidence_index.json`、`T4/producer_self_review.json` | 已重做，但未达 90，不冒充通过 |
| N07 | idle/move GIF 相同且静态 | 500ms 间隔真实 canvas 采集；idle 6 唯一帧、move 6 唯一帧；记录 Spine `trackTime`/bones；未重建 Spine | `T6/character_n/N07_animation_sheet.png`、`N07_animation.json`、`char_idle.gif`、`char_move.gif` | 已修 |
| N08 | 旧审阅 ZIP 有过期 JSON/旧 SHA，缺磁盘对照 | 旧包 199 项中 106 项与当前磁盘不同；新包只从 candidate_n2 冻结 manifest 打包，逐项比对磁盘/ZIP，外层 `.sha256` 放 ZIP 外 | `N_rework/N08_pack_plan.json`、`delivery/N08_pack_verification.json` | 已重打包并核验 |

## Q01–Q09（finalN2）

`delivery/next_cycle/N_rework/quality_check_n.json`：全部 `pass`。

- Q01：真实 bbox 130×130px（目标 86–130）。
- Q03：前景白像素 5188，树后 867，判定遮挡成立；脚影漂移 0.0m。
- Q04：键盘/触控两轮；正常位移 >0，暂停/对白位移 0，恢复需新输入。
- Q05：empty 0 / full 3 / reset 0，无残留。
- Q06：GLB 17,800,760 bytes；runtime draws 715、tris 397,590（MAP001/LOOK001）；**warning**，非硬失败。
- Q07：源局部改、重开、重导出、同机位一致。
- Q08：源/导出/构建/采集/合同/rubric/审阅摘要同源绑定。
- Q09：1280×720 与 720×1280 真实 canvas；无真机，`device_tested=false`。

运行错误：`_t5_probe.js` 0 page errors；`_t6_all_states.js` 41 UI / 34 assets / 0 errors；N04/N05/N07 均 exit 0。

## 自审四卡（制作侧，非独立）

| 卡片 | 分数 | 判断 |
|---|---:|---|
| ENV | 70.00 | 未达 90；几何工艺 2 分触发核心底线 |
| CHAR | 93.75 | 达 90；角色仍为锁定 1015 Spine |
| UI | 75.00 | 未达 90；纸面/涂鸦仍比 P1 规整 |
| MIX | 75.00 | 未达 90；整体统一但细节密度/光响应不足 |

`producer_submission_check.json`：`status=producer_rework_required`，4 条 finding（ENV geometry 核心底线、ENV/UI/MIX 分数低于 90）。没有未解决的 blocking/major 证据问题；分数问题是真实视觉差距。

## 下一轮最有价值的修复（按权重）

1. ENV/geometry_craft：树冠体块细分/法线/枝条渐细、花坛与长椅倒角；目标把 2 提到 3 以上。
2. ENV/material+lighting：加环境反弹光/顶光层次、长方向影、金属粗糙度分区。
3. UI/paper+doodle：更薄更不规则的纸边、扩展手绘图标族、压缩对白高度。
4. MIX：用上述 ENV/UI 改动同时提升视觉语言与色彩光 coherence，避免分别打补丁。

## 未验证 / 限制

- 未做手机真机、微信开发者工具、性能和包体验收。
- 未做完整任务玩法闭环。
- 桌面 Chrome SwiftShader 下的 FPS/draw calls 不是真机结论。
- 独立审核、控制器证书/密钥均未生成、未自签。
