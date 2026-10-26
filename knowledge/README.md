# 鼠鼠项目知识库

更新：2026-10-26。本目录是**检索入口与可复用经验**，不是另一份合同、任务账本或审核结论。当前生产状态以 `planning/execution/ACTIVE_REWORK_CYCLE.json`、`PROJECT_TASKS.json` 和生成的 `delivery/workflow/CURRENT_WORK_PACKAGE.md` 为准；合同/评分以 `art_review/harness_contract.json`、`art_review/rubric.json`、`planning/execution/producer_review_policy.json` 为准。

## 按问题找资料

| 要解决的问题 | 先读 | 再看 |
|---|---|---|
| 现在该做什么、能否停工 | [当前指令索引](../planning/execution/CURRENT_INSTRUCTION_INDEX.md)、[当前工作包](../delivery/workflow/CURRENT_WORK_PACKAGE.md) | [执行协议](../EXECUTION_PROTOCOL.md)、活动返修指针中的报告 |
| P1 画面怎样画 | [P1 风格手册](../P1_ART_STYLE_GUIDE.md)、[验收标准](../PHASE1_ART_ACCEPTANCE.md) | [P1 原帧](../reference/_raw_screenshots/P1/)、[完整美术范围](../FULL_ART_DELIVERY.md) |
| 资产用什么工具制作 | [美术工坊分工](../ART_WORKBENCH_SPEC.md) | [可编辑工具调研](../EDITABLE_ART_RESEARCH.md)；使用前核当前工具与源 |
| 角色来源与动画 | **有效** [harness 合同](../art_review/harness_contract.json)的锁定来源 | [P1 手册](../P1_ART_STYLE_GUIDE.md)的方法、实际 Spine 源与播放证据 |
| Q、评分、审核如何执行 | [有效合同](../art_review/harness_contract.json)、[rubric](../art_review/rubric.json)、[制作自审](../PRODUCER_SELF_REVIEW.md) | [HARNESS 工具说明](../HARNESS.md)、实际检查脚本与报告；注意 vNext 草案尚未生效 |
| n5 怎么少做无效构建 | [n5 执行设计](../planning/performance/N5_EXECUTION_DESIGN_AND_GAP_AUDIT.md) | [n4 预审报告](../art_review/reports/candidate_n4_provisional_20261026/REPORT.md) |
| 首张成功后怎样复用到其他地图 | [地图链路沉淀方案](../planning/execution/POST_SUCCESS_MAP_REUSE_PLAN.md) | [地图工坊 M0 设计](../MAP_WORKBENCH_EXTENSION.md)、本库用例与案例；n5 运行中先留原始日志 |
| 航天基地宿舍区地图方案 | [宿舍区 MVP 方案](../SPACE_CITY_DORMITORY_MVP_REFERENCE_AND_ART_PLAN.md) | [地图转换方案](../SPACE_CITY_MAP_CONVERSION_PLAN.md)、[地图工坊扩展](../MAP_WORKBENCH_EXTENSION.md)；目前不是自动启用的 art_required 范围 |

当前要求的速查与来源见 [STANDARDS.md](STANDARDS.md)，具体美术制作与返修见 [n5 美术制作配方](N5_VISUAL_PRODUCTION_PLAYBOOK.md)，通用操作用例见 [RECIPES.md](RECIPES.md)，真实案例及证据边界见 [CASEBOOK.md](CASEBOOK.md)，文档和流程缺口见 [PROJECT_AUDIT.md](PROJECT_AUDIT.md)。短经验 ID 与状态仍集中在 `planning/execution/LESSONS.md`，本目录不要另起一份会漂移的经验账本。

目前**没有一份完整美术候选取得独立放行**，因此本库没有“完整游戏美术已通过”的最佳样例。用例 R01/R03 是待 n5 验证的推荐做法；R02 有 n3 局部行为证据；C04 仅是 n2 打包可追溯的局部成功。

## 如何使用和更新

1. 新任务先读当前指令索引和工作包；只打开与本次缺陷、资产、审核阶段匹配的知识条目。可用 `rg -n "N09|UI|build_id" knowledge planning/execution/LESSONS.md` 检索。
2. 知识条目必须标明 `适用范围`、`来源路径`、`经验状态`、`证据覆盖`、`做法`、`不适用情况`。经验状态沿用 `LESSONS.md` 的 `proposed|validated|retired`；证据覆盖另写制作侧复验或独立复核。独立复核某个局部，也不自动等于整个候选放行。
3. 每轮按 `planning/execution/SELF_LEARNING_LOOP.md` 记录假设、操作、反例与复验；有跨轮价值时更新 `LESSONS.md`，并在这里补一个简短用例或失败案例。原始图、日志、hash 只存候选证据目录，知识库只引用，不复制冻结文件。
4. 新独立审核出现相反证据时，优先更新当前指令和短经验状态，再修本目录对应条目。旧结论保留来源和时间，不把历史描述悄悄改为“已通过”。

## 权限与防误用

- 本目录不能改变 90 分制作侧筛选、独立 rubric、来源许可或任务范围；冲突时按 `planning/execution/CURRENT_INSTRUCTION_INDEX.md` 找权威文件。
- `n2/n3/n4` 冻结或既有候选证据只读。知识库引用它们供诊断，不能把旧截图或旧 build_id 用作 n5 的通过证据。
- 命令退出 0、单体预览通过、某张截图好看都不等于完整美术或微信真机通过；记录可观察范围和未测项。
