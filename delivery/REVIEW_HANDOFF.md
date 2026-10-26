# 集中评审交接单（candidate_n2 / N01–N08 返修后）

更新：2026-10-25。账本 **1.0.136**。制作侧 **76 done / 2 waiting_review / 1 rework / 18 todo**（art_required: 76/2/1/3）。I07 因制作侧筛选未过为 rework；I08 已登记 waiting_review。
本文件是交接说明，不是审核结论；制作方未填写独立分数、未签发证书、未生成生产密钥。

## 当前候选

- manifest：`art_review/submissions/candidate_n2/manifest.json`
  - sha256 `890dfe78372c63f6945b5807368f5c577b365223d8d5053a2766d2a4c14db946`
  - `tools/art_harness.py verify`：`mechanical_checks=pass`，`status=needs_review`，`accepted=false`
- I07 状态：`rework`（制作侧 90 门槛未过，不冒充候选完成）
- 最终审核请求：`delivery/next_cycle/N_rework/FINAL_REVIEW_REQUEST.md`
- 返修报告：`delivery/next_cycle/N_rework/REWORK_REPORT.md`
- 审阅包：`delivery/candidate_n2_review_pack_20261025.zip` + 外部 `.sha256`
- 打包核验：`delivery/N08_pack_verification.json`
- 运行说明：`delivery/RUN_DEMO_v5.md`
- 源包：`delivery/courtyard_scene_demo_sources_v5.zip`

## 制作侧自审（不是独立评分）

- `delivery/next_cycle/T4/producer_self_review.json`
  - sha256 `724b2c08c9419156c9e5cd920a5ee46bb97837d003af526ec389d7edd7c49f4a`
- `delivery/next_cycle/T4/producer_submission_check.json`：
  - `producer_rework_required`，**未通过 90 门槛**
  - ENV 70.00 / CHAR 93.75 / UI 75.00 / MIX 75.00
  - findings：ENV geometry_craft 低于核心底线；ENV/UI/MIX 分数低于完整候选门槛
- Q01–Q09：`quality_check_n.json` 全部 pass；Q06 draw warning、Q09 无真机是记录项。

## 返修结论

- N04/Q01、N05/Q09、N07 动画证据已用真实测量/浏览器事件/500ms 帧采集修复。
- N01/N02/N03 已完成一轮原生 Blender/引擎视觉迭代，残余差距见 `REWORK_REPORT.md`。
- N06 已重做逐维/逐项自评，**没有**把 70/75 写成 90。
- N08 已按当前 manifest 重新打包并逐项对照磁盘；旧包 199 项中 106 项已过期，未沿用。

## 审核链

- P08 独立规则评审：仍 `waiting_review`；请求 `delivery/next_cycle/T0/P08_review_request/`。
- I08 独立全量美术复审：`waiting_review`；使用 `FINAL_REVIEW_REQUEST.md` 与 candidate_n2 包。
- V08/V09 为样板链外部任务，本轮不自动推进、不代签。
- I09 控制器放行：未开始；需要外部密钥/证书，制作模型不得生成或修改 `accepted`。

## 角色与范围边界

- 角色唯一来源仍是锁定 1015 Spine；未重画/缩放/替换。
- 未做完整任务玩法、微信真机、性能/包体；桌面 Chrome 截图不等于手机通过。
- 任何源/构建/相机/UI 改动都会使当前 manifest、绑定、自评和包校验失效，必须重打包重审。
