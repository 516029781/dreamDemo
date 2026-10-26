# 最终集中审核请求（I08 / 候选 candidate_n2）

日期：2026-10-25。提出方：制作模型。性质：请求独立审核；**不是通过、不是证书、不是控制器放行**。

## 冻结输入

- manifest：`art_review/submissions/candidate_n2/manifest.json`
  - sha256：`890dfe78372c63f6945b5807368f5c577b365223d8d5053a2766d2a4c14db946`
  - 机械检查：`tools/art_harness.py verify` → `status=needs_review`，`mechanical_checks=pass`
- 自审：`delivery/next_cycle/T4/producer_self_review.json`
  - sha256：`724b2c08c9419156c9e5cd920a5ee46bb97837d003af526ec389d7edd7c49f4a`
  - 结果：`producer_submission_check.json` → `producer_rework_required`（ENV 70 / CHAR 93.75 / UI 75 / MIX 75）
- 审阅包：`delivery/candidate_n2_review_pack_20261025.zip`
  - 外层校验和：`delivery/candidate_n2_review_pack_20261025.zip.sha256`
  - 打包核验：`delivery/N08_pack_verification.json`
- 返修报告：`delivery/next_cycle/N_rework/REWORK_REPORT.md`
- 运行说明：`delivery/RUN_DEMO_v5.md`
- 源包：`delivery/courtyard_scene_demo_sources_v5.zip`
- Q 结果：`delivery/next_cycle/N_rework/behavior_results_n.json` + `quality_check_n.json`
- 采集绑定：`art_review/submissions/candidate_n2/bindings/`

## 请独立审核者做什么

1. 实际打开原尺寸图与 P1 t015/t044/t084，对照：
   - `T4/N01_tree_hedge_before_after.png`
   - `T4/N02_shadow_before_after.png`、`T4/N02_material_closeups.png`
   - `T4/N03_ui_before_after.png`
   - `T4/N04_actor_bbox.png`、`T4/N05_orientation.png`
   - `T6/character_n/N07_animation_sheet.png` 及两个 GIF
2. 按 rubric 1.2.0 四卡逐维独立填分；不要照抄制作自评，也不要用制作侧 70/75 直接当审核分。
3. 复核真实行为：Q01 角色 bbox、Q03 树前/树后、Q04 键盘/触控暂停/对白/恢复、Q05 空/满/重置、Q09 fresh portrait + resize。
4. 重开代表源：`MAP001_courtyard.blend`、`ENV006_autumn_tree.blend`、`PROP001`/`PROP004`、`paper_panel.svg`。
5. 逐项核对 `delivery/next_cycle/N_rework/N08_pack_plan.json` 与 `delivery/N08_pack_verification.json`：ZIP 内每个条目是否与磁盘一致，旧 final4/stale JSON 是否已排除。

## 已知未解决与不要误判的点

- **制作侧未达 90 门槛**：ENV 70、UI 75、MIX 75；ENV geometry_craft 自评 2，低于核心底线。直接后果是本次不是“制作侧筛选通过”的提交；请按独立标准判断是否需要继续返修。
- ENV 仍是低多边形风格化场景；N01 提高了树冠/绿篱密度，但树冠体块、枝条渐细、花坛/长椅倒角仍明显粗简。
- UI 纸面/虚线/涂鸦已改，但仍比 P1 规整；对白面板偏高。
- Q06：MAP001/LOOK001 draw calls 715，高于 400 预警线；记录为 warning，不是硬失败。
- Q09：只用桌面 Chrome 做横竖屏与 resize；无手机真机，不能声明微信/手机通过。
- 未做完整任务玩法、微信开发者工具、性能/包体。
- 角色仍是锁定 1015 Spine；未重画、未缩放、未用 AI Image。

## 输出建议

- 独立审核：`art_review/reports/independent_20261025_candidate_n2/`（新目录，不覆盖旧报告）。
- 如判不通过：按 N01–N08 + 新缺陷给出具体返修项，制作侧继续修。
- 如判通过：仍需控制器在外部签认；制作模型不生成密钥、不修改 `accepted`、不签证书。
