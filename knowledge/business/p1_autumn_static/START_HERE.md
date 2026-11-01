# P1 秋日庭院静态地图 · 业务入口

- business_id：`p1_autumn_static`（manifest r03）
- 交付类型：`static_map`
- 当前阶段：**待制作新一轮候选**（V27 为含植被的中间工作图，非当前目标）

## 读什么

| 顺序 | 文件 | 解决什么 |
|---|---|---|
| 1 | `BUSINESS_PROFILE.md` | 范围、当前状态、**无植被政策 r03** |
| 2 | `STYLE_PROFILE.md` | 参考可见事实、锚点、色彩角色、适配决定 |
| 3 | `scorecard.json` | 六维权重、门槛、八项硬门槛（与 gate 一致） |
| 4 | `planning/art/P1_WORKORDER_20261101_NEXT.md` | 当前工作单：无植被设备化改编（P1-A/B/C） |
| 5 | `planning/art/STATIC_MAP_WORKFLOW_20261028.md` | G0–G3 关口 |
| 6 | `planning/art/P1_T084_ART_DIRECTION_STANDARD_20261028.md` | 视觉标准正文（含 2026-11-02 勘误） |
| 7 | `planning/art/ACTIVE_STATIC_ART.json` | 当前候选、SHA、未验证事项（唯一事实源） |
| 8 | `DRAWING_PLAYBOOK.md`（按需） | 本项目做法、成熟度、证据；含被取代的中间方向 |

## 不要读什么

- 旧分层背景方案、历史执行表、V20/V24 计划 → 只作追溯（见 `ART_DOCUMENTATION_ARCHIVE_INDEX_20261029.md`）。
- `research_arknights_mapdata` 数据包：只做数据研究，不是视觉参考。

## 当前事实（2026-11-02）

- 当前工作图：`art/static_map/p1_autumn_courtyard/v25/renders/final_v27.png`
  （SHA `2d698729…`），源 `v25/scene.blend`（`3ea1b0e9…`）。
- **图中含树与草，属 2026-11-01 21:00 中间方向；23:19–23:23 的更新记录已改为整图无植被。**
- 源—图同源：`unverified`；质量：`unverified_current_image`；旧 DELIVERY/GATE 不适用。
- 机械 gate 与 r03 评分卡一致（含 `no_vegetation`），但 gate 不读图，不能证明评审独立性。

## 开工前

1. 重算三份实物 SHA 并核对 `ACTIVE_STATIC_ART.json`。
2. 建立本次 `RUN_CONTEXT.json` + `RESOLVED_KNOWLEDGE.json`。
3. 按工作单 P1-A（保全与锁候选）→ P1-B（清除植物与设备替代）→ P1-C（明暗与背景）推进；
   不覆盖 `v25/` 既有文件。
