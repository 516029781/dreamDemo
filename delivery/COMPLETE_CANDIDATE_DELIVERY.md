# 秋庭来信 · candidate_n2 交付说明（N01–N08 返修后）

更新：2026-10-25 04:35（本地）。状态：**candidate_not_independently_approved / producer_filter_not_passed / not_released**。
本包是 N01–N08 返修后的完整美术候选。制作侧自审没有达到 90 门槛；仍按用户要求在最终集中审核提交，供独立角色判断。P08、V08、V09、I08、I09 未由制作方自签。

## 1. 可审包位置

| 内容 | 路径 |
|---|---|
| 完整候选 manifest | `art_review/submissions/candidate_n2/manifest.json`（sha256 `890dfe78…`） |
| 47 项 catalog | `art/iterations/cycle_03/full_art_catalog.json` |
| 47 项逐项 producer 自审 | `art/iterations/cycle_03/reviews/<ID>.json` |
| 完整四卡自审 | `delivery/next_cycle/T4/producer_self_review.json` |
| 制作侧筛选结果 | `delivery/next_cycle/T4/producer_submission_check.json`（producer_rework_required, accepted=false） |
| 最终审核请求 | `delivery/next_cycle/N_rework/FINAL_REVIEW_REQUEST.md` |
| 返修报告（N01–N08） | `delivery/next_cycle/N_rework/REWORK_REPORT.md` |
| 合并可审包 | `delivery/candidate_n2_review_pack_20261025.zip` + 外部 `.sha256` |
| 打包核验 | `delivery/N08_pack_verification.json` |
| 源包 | `delivery/courtyard_scene_demo_sources_v5.zip` |
| 运行说明 | `delivery/RUN_DEMO_v5.md` |
| Q01-Q09 结果 | `delivery/next_cycle/N_rework/behavior_results_n.json` |
| 质量检查 | `delivery/next_cycle/N_rework/quality_check_n.json`（all pass, warnings only） |
| 采集绑定 | `art_review/submissions/candidate_n2/bindings/summary.json`（3/3 verified） |
| I07 报告 | `delivery/next_cycle/T7/I07_manifest_verify.json`、`I07_complete_candidate_package.json` |
| 全状态索引 | `delivery/next_cycle/T6/state_index.json`（41 UI 状态、34 资产预览） |

最终画面：
- `delivery/next_cycle/T3/game_finalN2_formal_no_ui.png`
- `delivery/next_cycle/T3/game_finalN2_formal_ui.png`
- `delivery/next_cycle/T3/game_finalN2_dialogue.png`
- 对比：`delivery/next_cycle/T4/N01_…`、`N02_…`、`N03_…`、`N04_…`、`N05_…`

## 2. 运行方式

1. 保持 `http://127.0.0.1:8801/` 静态服务指向 `demo/build/web-desktop`。
2. 浏览器打开；等待 `[COURTYARD] READY`。
3. WASD/方向键移动，E/空格交互；触控摇杆/按钮；竖屏显示“请横屏游玩”并锁输入。
4. 重建：`tools/blender/run_courtyard_build.ps1 -Stage env_tree,map001` → 复制 GLB → `python tools/cocos/build_web_desktop.py`。
5. 复跑证据：`node delivery/next_cycle/_t6_all_states.js`、`_t5_probe.js`、`_n04_bbox.js`、`_n05_orientation.js`、`_n07_animation.js`、`python delivery/next_cycle/N_rework/build_n_evidence.py`、`python tools/producer_review.py check ...`。

## 3. 四卡制作自评（真实结果）

| 卡 | 分数 | 门槛 | 判断 |
|---|---:|---:|---|
| ENV | **70.00** | ≥90 | 未达；geometry_craft 2 分触发核心底线 |
| CHAR | **93.75** | ≥90 | 达；角色仍为锁定 1015 Spine |
| UI | **75.00** | ≥90 | 未达；纸面/涂鸦仍比 P1 规整 |
| MIX | **75.00** | ≥90 | 未达；细节密度/光响应不足 |

`producer_review.py check`：`status=producer_rework_required`，`ready_for_final_review=false`，`accepted=false`，`independent_approval=false`。
没有把制作侧 70/75 写成 90，也没有把机械检查通过当成视觉通过。

## 4. Q 检查与构建

- Q01 真实 bbox 130×130px（目标 86–130），可见/隐藏四边差分。
- Q02 P1 t015/t044/t084 对照；Q03 树前/树后遮挡（白像素 5188→867）；Q04 键盘+触控暂停/对白/恢复；Q05 空/满/重置；Q06 最终 GLB `809e2d2b…` + runtime stats；Q07 长椅源编辑→重开→导出；Q08 同源绑定；Q09 fresh portrait + resize 720×1280 + 横屏恢复。
- 采集绑定 3/3 通过；manifest mechanical checks pass；Cocos 3.8.8 exit 36 仅在 Finished+有序 SIGTERM+产物存在时接受。
- 警告（非硬失败）：Q06 MAP001/LOOK001 draws 715 高于 400 预警线；Q09 未测手机真机。

## 5. 缺陷对账

- F01–F08、R01–R10 全部为 **fixed_pending_independent_confirmation**；N01–N08 也逐条记录。
- N04/N05/N07 由真实 bbox、真实 orientation 事件、500ms 动画帧证明；N01/N02/N03 有一轮原生 Blender/引擎改动和前后对照。
- 未解决 blocking/major：制作侧证据无未解项；但 ENV/UI/MIX 分数与 ENV 核心底线未过，属于真实质量差距，不是证据问题。

## 6. 未测与限制

- 无手机真机；Q09 只声明浏览器横屏和竖屏提示。
- 未做完整任务玩法闭环、微信开发者工具、性能/包体验收。
- 桌面 Chrome SwiftShader 下的 FPS/draw calls 不是真机结论。
- 场景仍是低多边形风格化；N01 提高了植被密度，但未把树冠/材质/光照做到 P1 的细节层级。
- 独立视觉/规则复核、控制器证书和正式放行未完成。

## 7. 下一步

1. 最终审核者按 `FINAL_REVIEW_REQUEST.md` 看原尺寸图、复现 Q 行为并独立评分。
2. 若判继续返修：优先 ENV geometry_craft → material/light → UI paper/doodle → MIX coherence。
3. 若判通过：仍需控制器外部签认；制作模型不生成密钥、不修改 accepted、不签证书。
4. 任何源/构建/相机/UI 改动都会使当前 manifest、绑定、自审和包校验失效，必须重打包重审。
