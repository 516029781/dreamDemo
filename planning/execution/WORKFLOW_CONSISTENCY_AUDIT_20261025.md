# 工作流程过时与冲突审查

日期：2026-10-25。审查范围是活动入口、任务/返修指针、审核门槛、历史计划及工作包生成；没有修改 candidate_n2/n3 冻结证据或 n4 制作源。最新状态仍读 `ACTIVE_REWORK_CYCLE.json` 和 `PROJECT_TASKS.json`。

| 问题 | 证据 | 处理 |
|---|---|---|
| 早期索引自称“唯一活动规则”，却指向 2026-10-24 报告和旧中途审核顺序 | `delivery/next_cycle/T0/active_spec_index.json` | 保留其冻结证据原样；新建 `CURRENT_INSTRUCTION_INDEX.md` 作为当前责任索引，在入口指明替代关系。 |
| 旧 T0–T4 计划要求样板独立批准后扩图，和用户授权的完整候选后集中审核冲突 | `NEXT_ITERATION_PLAN.md` 第3/6节；根目录范围/画法文档曾引用其执行顺序 | 给旧计划加历史横幅；修改 `FULL_ART_DELIVERY.md`、`PHASE1_ART_ACCEPTANCE.md`、`P1_ART_STYLE_GUIDE.md`、`ART_WORKBENCH_SPEC.md` 的入口链接。Q01–Q09 初版内容可作背景，不作现行状态/顺序。 |
| 返修候选号写死 n3，实际已指向 n4 | `MODEL_EXECUTION_GUIDE.md`、旧续做段落；活动返修 JSON | 活动文本改为读取 `next_candidate` 与 `open_findings`，历史首次制作章节明确标记不重跑。 |
| I07 为 `rework` 时，工作包把 n3 低分显示为 `not_due_until_full_candidate`，并列旧输出路径 | `tools/workflow.py`、n3 真实检查结果 `producer_rework_required` | 工作包读取活动指针的最近尝试结果；I07 返修时只展示当前开放项和动态新候选输出，不把 n3 输出当目标。 |
| 自审失败后只写下一步，缺少本轮实际修改出口 | n3 检查 75/93.75/75/75 与 n4 工作记录 | 协议规定低分后同轮至少选择一个共享原因、修改原生源并同机位预览；检查点必须记录结果。 |
| 旧性能与“剩余80项”文件使用过期数量/状态 | `WORKFLOW_REVIEW.md`、`REMAINING_WORKFLOW_OPTIMIZATION.md`、`PERFORMANCE_OPTIMIZATION_PLAN.md` | 加历史快照横幅；当前优化方案以 `END_TO_END_DEVELOPMENT_CHAIN_PLAN.md` 为准。50%/70%仍是目标，非实测。 |

## 保留但不能作为现行指令的内容

- `PROJECT_TASKS.json` 中已完成任务的旧 `inputs`、路径、标题和 `resume_action` 是当时执行记录；不批量改写账本历史。任务状态/制作依赖仍以账本为准，当前候选和缺陷以活动返修指针为准。
- `TASK_CHECKLIST.md` 只作任务 ID/依赖索引；早期 P03 等命名保留历史含义，不恢复中途审核阻塞。
- `reference/planning_history/`、旧独立报告、候选 manifest、`delivery/workflow/activation.json` 和 T0 索引保持只读可追溯。

## 当前单一路径

`START_HERE.md` → `CURRENT_INSTRUCTION_INDEX.md` → 活动返修指针/报告/工作单 → `EXECUTION_PROTOCOL.md` 与 `PRODUCER_SELF_REVIEW.md` → 账本与生成工作包 → 制作新候选和自审 → 达标后集中独立审核。合同、rubric、角色来源另按当前索引读取；本次未改变它们的阈值与批准权。

## 仍需观察

工作包生成器展示最近一次制作侧检查结果，不能独立证实美术质量。n4 正在制作时，任何新预览都只是草稿；需由制作模型完成同机位视觉自审和正式候选绑定。微信真机/帧率/内存仍未在本次流程审查中验证。流程审查没有授权制作方自签批准。
