# P02 规则与状态迁移说明（rule_migration.md）

生成：2026-10-24｜任务：PROJECT_TASKS.json P02｜关联缺陷：R08（技术自检覆盖文件却未完成风格放行）、R10（目录/规则旧信息与状态歧义）。

## 1. 版本现状与生效边界

- 当前生效合同：`art_review/harness_contract.json` **1.3.0**；rubric **1.2.0**。二者在本次迁移中**只读未改**。
- vNext（建议 1.4.0）**尚未生效**。本迁移产出为草案记录（`vnext_effective=false`），只有 P03+ 安装 vNext 合同/门禁代码并经独立审核确认后才作为门禁执行；在此之前不覆盖生产流程。
- 新证据按新合同重新冻结；**不自动继承任何旧批准**。

## 2. 产出与只读边界

| 文件 | 性质 |
|---|---|
| `art_review/vnext/asset_status.schema.json` | 新建：三轴+放行状态 schema（draft-07） |
| `art_review/vnext/asset_status_migrated.json` | 工具输出：旧目录迁移结果（草案） |
| `tools/art_gate/migrate_catalog.py` | 新建：确定性迁移工具（stdlib；生成后用 `jsonschema` Draft-07 验证） |

迁移工具强制输出只能落在 `art_review/vnext/` 下（否则退出码 3）；`art/full/`、`art_review/submissions/`、旧报告/旧合同/旧manifest 一律只读。运行前后 sha256 校验确认输入未被改动（`art/full/art_complete_catalog.json`、`art/full/reviews/MAP001.json`、`art/full/reviews/ENV006.json` 均校验 OK）。

## 3. 字段迁移映射

旧目录单一 `status` 拆为四轴（NEXT_ITERATION_PLAN.md §4），不再用一个词同时表达技术与批准：

| 旧字段/值 | 新字段/值 | 理由 |
|---|---|---|
| `status: engine_verified` | `technical_state: import_verified` | 旧语义只证明“实际引擎验证通过”（技术），不携带视觉/放行含义 |
| 每项 `art/full/reviews/<ID>.json`（reviewer=producer technical engine check, decision=pass） | `technical_evidence.review_kind=technical_self_check` | 制作方技术自检显式标注，**不得产生 visual_state=pass** |
| （无独立逐项视觉判定） | `visual_state: not_reviewed`；被视觉缺陷点名条目 → `rework` | 独立审核整体返修（H02），未对每项单独判pass；视觉缺陷=R01/R02/R03/R04 |
| （无行为验证记录） | `behavior_state: not_tested`；独立实测失败处 → `fail`（R01 世界遮挡、R05 暂停输入锁 → MAP001）；`not_required` 仅限 kind ∈ {material, scene_profile, delivery} 且必须附理由 | 行为项不得以视觉截图替代；N/A 需条款+理由 |
| 目录整体 `engine_verified_pending_independent_review` + review_gate blocked/H02 | `release_state: blocked`（有未解 blocking/major）/ `reviewed_not_released`（无）/ `released`（迁移永不产生） | released 只由外部控制器 controller_release 记录产生 |

旧 `blockers[]`（47 项全部非空）逐条原文保留为 `historical_notes`，**不参与放行判定**——“非空历史数组不自动失败”；阻断只来自独立审核当前未解问题（`issues[].status=open`）。历史已解决与当前未解通过 `issue.status` 分开。

## 4. 哪些旧批准/口径失效

1. **producer 技术 engine_verified ≠ 视觉 pass**：旧逐项 `decision=pass` 降级为 technical_self_check 证据，不迁移任何视觉批准。
2. **目录整体状态 `engine_verified_pending_independent_review` 失效**：迁移后 package=CATALOG，`release_state=blocked`，decision_source=rework（独立审核 accepted=false）。
3. **review_gate blocked/H02 继续有效**：迁移不改变门禁结论，只把结论拆到轴上。
4. **旧 `approved` 状态值不再可用**：迁移表中 `approved` 只映射 `technical_state=import_verified`，不产生任何 released。

## 5. 缺陷路由（确定性，记录于工具 DEFECT_ROUTES）

| 缺陷 | 严重度 | 挂载 | 影响面 |
|---|---|---|---|
| R01 | blocking | MAP001 | scene_character_integration |
| R02 | major | MAP001 | scene_camera |
| R03 | major | ENV006/ENV008/ENV009（证据路径正则提取） | asset_visual |
| R04 | major | ENV006/MAT001/MAT002（同上） | asset_visual |
| R05 | major | MAP001 | input_lock_behavior |
| R06 | major | MAP001 | tri_stats_reporting |
| R07 | major | FX003 | board_transition |
| R08 | major | CATALOG（流程缺陷，正则 ENV006 命中被显式丢弃） | catalog_process |
| R09 | minor | CATALOG | ui_family |
| R10 | minor | CATALOG | catalog_docs |

## 6. 迁移结果与自检（2026-10-24 实测）

- 命令：`python tools/art_gate/migrate_catalog.py`（退出码 0）。
- 结果：items=47；visual rework=6（ENV006/008/009、MAT001/002、MAP001）；blocked=7（上述6项+FX003）；package=blocked；issue挂载14条。
- 不变量自检通过：`visual_state=pass` 0 条；`release_state=released` 0 条；所有 blocked 记录均有未解 blocking/major issue；全部 `not_required` 附理由。
- 防护实测：`--out art/full/vnext_should_fail.json` → 拒绝并退出 3；合成违例（visual pass + blocked 无issue）被 `check_invariants` 捕获。
- 局限：本迁移是草案数据整理，不新增任何分数/批准；`schema_version=vnext.asset_status/1.0.0` 的门禁效力待 P03+ 独立审核确认。Q01–Q09 检查逻辑属 P03+ 门禁代码任务，本任务不实现。

## 7. 迁移操作程序（供 P03+ 与后续复核）

1. 重跑 `python tools/art_gate/migrate_catalog.py`（幂等，输出同路径覆盖草案）。
2. 若独立缺陷集更新（新 defects.json），重跑即重算 issues/release_state；旧输出按 hash 留档不覆盖历史证据。
3. vNext 合同生效前，生产判定仍以 1.3.0 合同 + `art_review/reports/independent_20261024/` 为准。

## 8. P02 返修（F03/F04，2026-10-25）

独立审核 progress_audit_20261024_2330 发现两项可复现缺陷，本次返修：

- **F03 迁移输出违反自身 schema**：CATALOG 的 `mapping.old_decision/old_reviewer` 为 `null`，而 1.0.0 schema 声明 string。修复：schema 升级 **1.0.1**，显式允许 `["string","null"]` 并把 null 语义定为“旧记录无对应值”（不等于空串或失败）；`technical_state_reason` 增补为可选字段。旧 schema 归档于 `art_review/vnext/versions/asset_status_v1.0.0.schema.json`，旧输出归档于 `art_review/vnext/versions/asset_status_migrated_v1.0.0_20261025.json`。
- **F04 失败技术检查可被提升为 import_verified**：旧逻辑只要 review 文件存在就把 missing 提升为 import_verified，不核 decision/证据/资产绑定。修复：`SUCCESS_DECISIONS={pass,approved,engine_verified}` 白名单 + `asset_id` 绑定 + reviewer 非空 + evidence 非空且至少一条路径可解析为真实文件；未通过时**降级**（engine_verified→source_ready，missing 保持 missing）并写 `technical_state_reason`。旧脚本归档于 `tools/art_gate/legacy/migrate_catalog_pre_f04.py`。

本次实测（2026-10-25）：

- `python -X utf8 tools/art_gate/migrate_catalog.py --as-of 2026-10-25T00:00:00Z` → exit 0；schema=draft-07 pass；items=47 rework=6 blocked=7 package=blocked；technical_state_notes=0（47 项 review 均通过 F04 校验）。
- `python -X utf8 delivery/next_cycle/T0/p02_selfcheck.py` → exit 0；6 个合成正反例全部符合预期：fail+空证据保持 missing、pass+空证据保持 missing、pass+不可解析证据保持 missing、asset 绑定不符保持 missing、pass+真实证据可提升 import_verified、engine_verified+fail 降为 source_ready；F03 的 null 允许而 integer 被拒绝。
- 证据：`delivery/next_cycle/T0/p02_selfcheck.json`（含 schema/migrator/迁移输出 sha256 与逐例结果）。
- 局限：制作侧返修完成，F03/F04 待独立确认；仍未产生任何视觉 pass、released 或新分数。
