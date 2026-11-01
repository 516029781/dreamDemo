# 鼠鼠项目知识库

更新：2026-11-02（迁移 P0-1..P0-5）。本文件是知识路由入口，不复制任何业务阈值。

## 1. 两层结构

| 层 | 位置 | 加载规则 |
|---|---|---|
| 通用开发核心 | `common/dev_core/` | 所有开发任务必读：生命周期、证据、身份隔离、通用规范索引 |
| 通用方法模块 | `common/methods/<type>/` | 按 `deliverable_type` 选读；地图方法不强迫 UI/角色任务加载 |
| 通用美术基线 | `common/art_base/ART_STYLE_BASE.md` | 仅美术任务；当前 `draft`，未批准前不得作门槛 |
| 业务知识包 | `business/<id>/` | 由需求显式选中后加载；未选中不读 |
| 当前运行上下文 | `active/<request_id>/runs/<run_id>/` | 每次任务新建；不是可继承的知识 |

## 2. 什么在生效

| 包 | 状态 | 入口 |
|---|---|---|
| `p1_autumn_static` | active（r02，植被政策按用户 2026-11-01 指令修订） | `business/p1_autumn_static/START_HERE.md` |
| `research_arknights_mapdata` | active（仅数据研究） | `knowledge/ARKNIGHTS_MAP_DATA_AND_HARNESS_AUDIT_20261029.md` |
| 案例库 | 暂无验收通过案例 | `cases/README.md` |
| 项目美术基线 | `draft` | `common/art_base/ART_STYLE_BASE.md` |

## 3. 状态契约

每条知识用三个独立字段，不得合成单一 `status`：

- `scope`：`common/dev_core` / `common/methods/<type>` / `common/art_base` / `business/<id>` / `active`
- `lifecycle`：`draft` / `active` / `superseded` / `deprecated` / `historical`
- `maturity`：`not_applicable` / `proposed` / `observed` / `reproduced` / `reusable`

`needs_evidence` 是证据缺口标记，`unknown` 是未知事实，均不是生命周期。
未验证经验不得写成成功案例；单业务观察不得升级为 common 的 `reusable`。

## 4. 加载规则

1. 先读通用开发核心与本次类型的方法模块。
2. 按 `business_id` 只加载选中业务包的 `required_docs`；`optional_docs` 按范围决定。
3. 记录 `RESOLVED_KNOWLEDGE.json`（路径、SHA、状态、usage、覆盖决定）。
4. 没有匹配业务包 → `new_business_bootstrap`，用 `templates/` 新建，不借用其他业务答案。
5. 未校准的数值指标一律 `diagnostic_only`。

## 5. 维护

- 新增/变更知识先过增量审计，写入 `planning/art/KNOWLEDGE_AUDIT_20261102.json` 的同类条目。
- 每条活动规则只能有一个权威正文；其他文件保留摘要与指针。
- 归档与过期识别以 `planning/art/ART_DOCUMENTATION_ARCHIVE_INDEX_20261029.md` 为准。
- 历史与归档文件保留原文，可追溯但不得被当作当前指令。
