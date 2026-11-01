# 鼠鼠：项目必读入口

本文件是**跨业务路由**，只回答“先读什么、这次读哪个业务包、哪些是历史”。不承载任何单一产品的画面参数。

## 1. 当前项目范围

项目同时承载：
- **P1 秋日庭院静态地图**（active 业务包 `p1_autumn_static`）
- **Arknights 地图参数与 Harness 研究数据包**（`research_arknights_mapdata`，只作数据研究，不作视觉参考）

其他产品/地图按需求新建业务包接入，不默认继承任何既有画面的答案。

## 2. 必读顺序

| 顺序 | 读什么 | 规则 |
|---|---|---|
| 1 | `AGENTS.md` + 本文件 | 每轮必读；只含跨业务规则 |
| 2 | 用户本轮需求（及已有 `REQUIREMENTS_BRIEF.md` / 活动任务指针） | 判定 deliverable_type 与 business_id；无 brief 先做 N0 |
| 3 | `knowledge/README.md` + `knowledge/common/dev_core/` | 通用开发核心；`common/methods/<type>` 按类型选读 |
| 4 | 选中业务包入口（`knowledge/business/<id>/START_HERE.md`）+ Profile + 评分 | 只加载显式选中的业务包 |
| 5 | 当前阶段已有产物 | 设计前读问题单；设计后读方案/预览/用例；未生成的阶段文件不必读 |

## 3. 路由规则

1. 从需求提取 `deliverable_type`、主题、平台、交付范围。
2. 命中业务包 → 读该包 `START_HERE.md` 与 manifest 中的 `required_docs`。
3. 未命中 → `new_business_bootstrap`：只用 common 层 + 本次 Brief，新建业务包与小样；
   不得借用其他业务的参考图、色板、相机或评分。
4. 多业务混合 → Brief 显式声明主/辅业务与共享/隔离验收项。
5. 纯方案讨论 → `task_mode=planning`；不分配候选、不触发制作门禁。

## 4. 当前运行与活动指针

- 每次运行在 `knowledge/active/<request_id>/runs/<run_id>/` 建 `RUN_CONTEXT.json` 与 `RESOLVED_KNOWLEDGE.json`。
- 当前活动业务状态：`knowledge/business/p1_autumn_static/START_HERE.md` →
  `planning/art/ACTIVE_STATIC_ART.json`（唯一事实源）。
- 新需求没有活动指针时，先建 Brief，不猜业务包。

## 5. 冲突与过期识别

优先级：用户本轮明确要求 > 本次 Brief 覆盖决定 > 已启用业务包 > 已批准 `ART_STYLE_BASE` >
`reusable` 案例 > `observed/proposed` 经验。

- `superseded` / `deprecated` / `historical` 不参与当前裁决；修改时间新不等于权威。
- 归档索引：`planning/art/ART_DOCUMENTATION_ARCHIVE_INDEX_20261029.md`。
- 规则冲突写入本次 Brief 的 `conflicts_and_decisions`；无法裁决时标 `blocking`，不两套同时加载。

## 6. 开工前输出

用 3–5 行写出：本轮的 business_id、deliverable_type、加载的权威文件路径与 SHA、
覆盖决定、以及是否存在 blocking 冲突。该摘要与 `RESOLVED_KNOWLEDGE.json` 对应。
