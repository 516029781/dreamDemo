# V08 独立样板视觉复核请求

状态：**等待 P08 通过后执行**。制作侧未评分、未签认。审核者应实际看原尺寸图、重开代表源、复现遮挡/输入/重置。

## 输入

- 样板 manifest：`delivery/next_cycle/T2/sample_manifest.json` (sha256 `4e789c7b5485d56b50be22abe5d484862d16dda1ae92f855aada566ef6a7543f`)
- 完整候选 manifest：`art_review/submissions/candidate_full/manifest.json` (sha256 `2f8e63bf0e4c82d8a63a20286ff064ce89196a0d33cbfa0d5091aff9a3f58a3a`)
- 当前画面：`delivery/next_cycle/T3/game_final4_formal_no_ui.png`、`game_final4_formal_ui.png`、`game_final4_dialogue.png`
- 对比：`delivery/next_cycle/T4/*_final4.png`
- Q 证据：`delivery/next_cycle/T5/behavior_results.json`、`q03_occlusion.json`、`q04_behavior.json`、`q05_board.json`、`q09_viewports.json`
- 源包：`delivery/courtyard_scene_demo_sources_v4.zip`
- 合并包：`delivery/candidate_full_review_pack_20261025_final.zip`
- 角色锁定播放：`art/phase1/character_playback_1015/idle_preview.png`、`move_preview.gif`、`move_contact.png`

## 要求

1. 自己打开原尺寸图（不是只看 producer 报告/缩略图），对照 P1 t015/t044/t084。
2. 重开代表源（MAP001/ENV006/PROP001/UI），复现树前/树后遮挡、暂停/对白/恢复、留言板 empty→full→reset、横竖 viewport。
3. 按 rubric 四卡逐维填分；样板门槛：每卡 >=85，核心 >=3，任意维 >=2，开放 blocking/major = 0；不得照抄制作自评。
4. 输出到 `delivery/next_cycle/T3/independent_review.json` 和 `delivery/next_cycle/T3/defects.json`；可复制本目录模板。
5. 未通过：列出具体缺陷并回退关联 V/A 任务；通过：进入 V09。制作方不会代签。
