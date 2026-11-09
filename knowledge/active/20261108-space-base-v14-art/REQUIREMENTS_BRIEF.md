# 需求 Brief：航天基地 v14 · 一次性成像层改造

- request_id：`20261108-space-base-v14-art`
- run_id：`20261108-2035`
- business_id：`space_base_minigame` / deliverable_type `static_map`
- 唯一口径：`planning/art/SPACE_BASE_V14_ONESHOT_PLAN_20261108.md`
- 触发：用户 2026-11-08 20:34「给出完整的调整方案，我要一次性开发完成」
- 状态：单批次开发，v13 冻结只读

| REQ-ID | 要求 | 验收 |
|---|---|---|
| REQ-50 | compositor 分级栈（M03） | 场景 use_nodes=True + 节点链统计 |
| REQ-51 | L0-b 色调映射采用 D（exposure −0.15） | 场景 view_settings |
| REQ-52 | 光照与明度分工（M04/M05） | A1/A2/A3/A4/A5 |
| REQ-53 | 材质族与表面响应（M06） | A6/A7 场景统计 |
| REQ-54 | 纹理幅度与边缘（M07/M08） | A8 + 目视 |
| REQ-55 | 水面三段与雾分工（M09） | 目视 + 对象统计 |
| REQ-56 | S1 light_land ≥0.45，不改判据 | check_v14_art.py |
| REQ-57 | 交付包 + MANIFEST SHA + check_v7 + 复现 + 前后对照 | space_base_check_v7.py |

不可变：画幅 1680×2478 / 7 px/m / 四厅敞顶 / 桥 B / 试车间 S-构件。
不做：场地轮廓去直角、路面 F1–F5 填充、四厅立面套件（另案）。
