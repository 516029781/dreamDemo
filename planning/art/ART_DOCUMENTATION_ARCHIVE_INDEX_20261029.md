# 美术流程历史文件索引

更新：2026-10-29。此索引用于防止旧文档重新进入当前执行链。列为历史不表示删除原始候选或 Git 历史。

## 当前权威文件

- 执行流程：`STATIC_MAP_WORKFLOW_20261028.md`
- 目标与评分：`P1_T084_ART_DIRECTION_STANDARD_20261028.md`
- 地图参数/Harness 规则：`knowledge/MAP_PARAMETER_HARNESS_RULES_20261029.md`
- Arknights 数据来源与研究事实：`knowledge/ARKNIGHTS_MAP_DATA_AND_HARNESS_AUDIT_20261029.md`
- 入口：`AGENTS.md`、`START_HERE.md`
- 知识入口：`knowledge/README.md`

## 当前参考与旧测量工具边界

| 文件/资源 | 状态 | 处理要求 |
|---|---|---|
| `P1_T084_ART_DIRECTION_STANDARD_20261028.md` | 当前视觉标准 | 唯一秋日整图目标；参考 SHA、六锚点、色彩样本和 85 分口径以此为准 |
| `ARKNIGHTS_BASE_MAP_ART_STANDARD_20261029.md` | 已被用户澄清覆盖 | 不再是画面目标；仅保留研究背景，不得按其中的 `reference_lock_pending` 制作 |
| `P1_VISUAL_TARGET_LOCK_20261027.md`、`P1_MAP_ART_ONLY_REVIEW_20261028.md` | 历史流程/评审 | 可追溯 t084 与旧候选；旧差距、分数、角色/UI要求不直接迁移到 v06 |
| `target_layout_v04.json` | 旧机器配置，待逐字段核对 | 有 P1 六锚点，也残留 90 分、角色/UI展示层和旧阈值；不能直接作为当前门禁 |
| `style.json`、`regions.json`、`grade_lut.json` | 旧测量配置 | 色相/远景颜色和区域框存在与现行 P1 标准不一致或旧候选绑定；只用于历史复现，不作为当前阈值 |
| `ART_CONSISTENCY_MECHANISM.md`、`REGION_PLAYBOOK_20261028.md` | 历史方法记录 | 可借鉴“全图指标会被 LUT 刷过”的失败经验；具体数值、目标框、通过结论不迁移 |
| `tools/art/consistency_check.js`、`region_report.js`、`composition_check.js`、`tools/p1_style_probe.py`、`make_static_map_overlay.py` | 旧实现，当前未认证 | 仍会读取旧配置；不能为当前 v06 报 PASS/FAIL。建立新 `P1_REFERENCE_PROFILE.json` 并重校准后再决定复用或替换 |
| `.agents/skills/p1-art-director/SKILL.md`、`.agents/skills/p1-map-environment-art/SKILL.md` | 当前项目技能 | 前者负责 P1 视觉观察与差距描述，后者负责 Blender 制作与证据；技能名称明确 P1 目标，Arknights 数据仅属 Harness 研究 |

## 旧流程与调研：隔离，不作为命令

| 文件 | 状态 | 处理要求 |
|---|---|---|
| `MASTER_PLAN_20261028.md`、`HANDOFF_TO_NEXT_MODEL_20261028.md` | 历史方案/交接 | 仅追溯；不按其中的阶段、参考和分数执行 |
| `WORKFLOW_AUDIT_AND_V2_PROPOSAL_20261028.md`、`STATIC_MAP_PLAN_20261028.md`、`STATIC_MAP_V03_DRAWING_PLAN.md` | 历史方案 | 不放进当前必读入口；与新流程重复或目标已变 |
| `STATIC_MAP_V6_PROCESS_KNOWLEDGE_PROPOSAL_20261028.md` | 已审阅标注的历史提案，非执行入口 | 原 Arknights 视觉目标/撤销 P1 的结论已废止；文内逐项标记已落实、过时和部分实现，并链接当前权威文件。冲突时按工作流、P1 标准与 Harness 规则执行 |
| `ART_TECH_BENCHMARK_20261028.md` | 未核验技术调研 | 引擎、材质、光照、draw call 等主张先找原始证据；不得称官方已证实 |
| `ARKNIGHTS_MAP_DECOMPILED.md` | 隔离研究草稿 | 原始 JSON/commit/SHA/解析器证据缺失；tile prefab、固定高度、PBR/Lightmap、法律可用等推论未核验。只作追溯，按 `knowledge/ARKNIGHTS_MAP_DATA_AND_HARNESS_AUDIT_20261029.md` 复核后才能引用 |
| `STATIC_MAP_ART_SKILLS_AND_TOOLS_20261028.md` | 旧工具调研，非当前资料 | 不进开工链；新工具需求出现时重新查源并验证 |
| `planning/execution/_archive/MODEL_EXECUTION_GUIDE_FULL_GAME_HISTORY_20261029.md` | 旧完整游戏执行指南 | 根目录 `MODEL_EXECUTION_GUIDE.md` 已精简为当前静态图入口；此历史副本不对当前任务生效 |
| `planning/execution/_archive/CURRENT_INSTRUCTION_INDEX_FULL_GAME_HISTORY_20261029.md` | 旧完整游戏指令索引 | 当前 `CURRENT_INSTRUCTION_INDEX.md` 只保留静态地图入口；旧索引不作当前执行命令 |
| `delivery/workflow/CURRENT_WORK_PACKAGE.md` 与现存 `STORAGE_STATUS.json` | 暂停的完整游戏账本派生快照 | 可能保留旧任务状态或过期容量测量；不得作为静态地图指令。按当前 15 GiB/12 GiB 规则重新执行 storage preflight 后才引用容量状态 |
| `ART_PIPELINE_SIMPLIFICATION_AND_TARGET_CORRECTION_20261029.md` | 已被后续用户澄清覆盖 | 仅保留过程追溯；其中撤销 t084、等待 Arknights 参考包和禁止重用 P1 配置等结论均不再生效 |

## 清理规则

先从活动文档和 skill 中删除失效指令、重复阈值、旧链接和重复说明；历史文件可保留为短指针，或在反向链接/脚本依赖确认后移入 `planning/art/_archive/`。原始截图、候选源、唯一报告、可复现素材和哈希绑定不随文档瘦身删除。清理生成物遵循 `tools/maintenance/STORAGE_POLICY.md` 与当前工作流的 dry-run/保护规则。
