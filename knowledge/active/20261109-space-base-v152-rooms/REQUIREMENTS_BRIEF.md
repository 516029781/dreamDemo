# 需求 Brief：航天基地 v15 · 四核心区内部重建

- request_id：`20261108-space-base-v15-rooms`
- run_id：`20261108-2320`
- business_id：`space_base_minigame` / deliverable_type `static_map`
- 唯一口径：`planning/art/SPACE_BASE_CORE_ROOMS_ART_PLAN_20261108.md`（v1.3）
- 复核：`planning/art/SPACE_BASE_CORE_ROOMS_CHECK_20261108.md`
- 触发：用户 2026-11-08 22:49「可以按你的推荐执行」（Q2/Q5/Q6/Q7 全部按建议裁决）
- 状态：单批次开发，v14 冻结只读

| REQ-ID | 要求 | 验收 |
|---|---|---|
| REQ-58 | 四厅按实机重建 L1 标志物（每厅 4–6 件） | check_v15_scene.py I1 |
| REQ-59 | 墙顶 0.55 m 压顶按厅上色（青/冷灰青/藏蓝/绿） | I4 |
| REQ-60 | 色带 ≤1.2 m、只做 1–2 面墙；取消 2 m 四圈与整圈黄栏杆 | I2 + 目视 |
| REQ-61 | 中间尺度成组构件 ≥0.045 件/m²（每厅 ≥52 件 1–3 m） | I11 |
| REQ-62 | 每厅 ≥1 组亮/暗成对贴地投影 | I12 |
| REQ-63 | 敞顶单层 / 无总裁室 / 无横跨铺板 | I7 |
| REQ-64 | S1 ≥0.45、S2 ≤0.12、S3 ≤0.02（不改判据），同报 water_frac | post_v15.py I8 |
| REQ-65 | 交付包 + MANIFEST SHA + check_v7 + 前后同机位对照 | space_base_check_v7.py I9 |

不可变：画幅 284.7×420 m / 5.902 px/m / 1680×2478 / 四厅 34×34 / 十字过道 10 / 场地 +4.70。
不做：总裁室与十字暖色地标（用户 22:19 裁决）、四厅立面套件（hero 另案）、场地轮廓去直角、路面 F1–F5 填充。
裁决记录：Q2 单梁按 TV13-03 先例豁免；Q5 H2 池口以截图为准（取消整圈黄栏杆）；
Q6 接受冷暗被 S1 判为水体、P3 同报 water_frac；Q7 52 件/厅在预算内。
