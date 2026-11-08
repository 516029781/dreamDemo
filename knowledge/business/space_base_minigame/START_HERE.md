# 业务入口：space_base_minigame

- business_id：`space_base_minigame`
- deliverable_type：`static_map`（静态图 + 可编辑 Blender 源）
- lifecycle：`active`（r01，2026-11-02 用户确认一次性执行计划后启用）
- 当前阶段：**N5 灰盒 → N6 生产 → N7 验证**，候选 `art/static_map/space_base_minigame/v01/`

## 读什么

| 顺序 | 文件 | 解决什么 |
|---|---|---|
| 1 | `BUSINESS_PROFILE.md` | 范围、边界、冻结条件、当前状态 |
| 2 | `HARNESS_SPEC.json` | 本业务检查集：必检 25 条 + 外置 3 条（r03） |
| 3 | `test_cases.json` | 28 条用例的判据、证据路径、责任方 |
| 4 | `planning/art/SPACE_BASE_MASTER_SPEC_20261102.md` | 唯一设计口径（v1.3） |
| 5 | `planning/art/SPACE_BASE_EXECUTION_PLAN_20261102.md` | 一次性执行计划 P0–P4 |
| 6 | `planning/art/HANDOFF_20261102.md` | 快速交接与当前状态 |
| 7 | `planning/art/_routes_v13.html` / `_corridor_strip.html` | 总图/走廊图 |
| 8 | `planning/art/STATIC_MAP_WORKFLOW_20261028.md` | 只作 G0–G3 连续制作/证据方法参考 |

## 不要读什么

- `knowledge/business/p1_autumn_static/`：P1 专属参考、评分、8 条硬门槛，不适用于本图。
- `knowledge/business/research_arknights_mapdata/`：只作数据研究，不是视觉参考。
- `knowledge/business/pilot_simple_map/`：流程样例，不是本业务风格来源。
- `planning/art/SPACE_BASE_RENDER_BRIEF_20261102.md`：v03 历史稿，正文数字全部过期；只作追溯。

## 开工前

1. 重算并核对 spec / handoff / 两张示意图 / 参考清单 SHA；不符先停。
2. 确认 `v01/` 未占用；不覆盖 `concept/`、`reference/` 旧图。
3. 读 `knowledge/active/20261102-space-base-map/RUN_CONTEXT.json` 与 `RESOLVED_KNOWLEDGE.json`。
4. 8 px/m、55° 正交、北侧朝南、`ortho_scale=240` 已冻结；要改先回 N2 重批。
5. A1/W3/W4 是运行时外置项；本轮只做静态图 + 源 + W1/W2。
