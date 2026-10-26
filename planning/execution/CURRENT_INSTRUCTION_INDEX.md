# 当前执行规则索引

更新：2026-10-25。此索引用于区分当前指令、候选证据和历史方案；任务状态仍以 `PROJECT_TASKS.json` 为准，审核结论以对应冻结候选的独立报告为准。索引本身不改变合同或评分。

## 读取顺序

1. `START_HERE.md`、`AGENTS.md`：当前范围、不可改的候选、工具与角色边界。
2. `planning/execution/ACTIVE_REWORK_CYCLE.json`：若 `status=open`，读取其中的 `next_candidate`、`open_findings`、`independent_report`、`execution_spec` 与存在时的 `review_report`；这些字段优先于文档里写死的旧候选号。最近候选的测评、关闭标准和耗时日志要求以 `review_report` 为准，但它不替代正式独立结论。
3. `EXECUTION_PROTOCOL.md`、`PRODUCER_SELF_REVIEW.md`：连续制作、自审失败后的实际返修及停止条件。
   每批自我总结、主动找反例、经验入库/失效按 `planning/execution/SELF_LEARNING_LOOP.md`；短经验索引为 `planning/execution/LESSONS.md`，仅作参考，不覆盖合同与证据。
4. `PROJECT_TASKS.json`、运行 `tools/workflow.py storage --enforce` 与 `tools/workflow.py summary --write` 后生成的 `delivery/workflow/STORAGE_STATUS.json` 和 `CURRENT_WORK_PACKAGE.md`：容量预检、制作任务状态和当下动作；生成摘要不能批准候选。容量分类与复用见 `planning/performance/ARTIFACT_REUSE_AND_STORAGE.md`，细则见 `tools/maintenance/STORAGE_POLICY.md`。
5. `art_review/harness_contract.json`、`art_review/rubric.json`、`planning/execution/producer_review_policy.json`：当前合同、评分与制作侧提交筛选。角色来源只读有效合同。
6. `FULL_ART_DELIVERY.md`、`PHASE1_ART_ACCEPTANCE.md`、`P1_ART_STYLE_GUIDE.md`：资产范围、画面特征与制作方法。发生执行顺序冲突时按本索引第1–4项。
7. `planning/performance/END_TO_END_DEVELOPMENT_CHAIN_PLAN.md` 与 `planning/performance/N5_EXECUTION_DESIGN_AND_GAP_AUDIT.md`：当前优化方案及 n5 可执行细化；它们不能覆盖账本状态、合同和独立审核结论。

按问题查已有规范、操作示例和证据案例时用 `knowledge/README.md`；知识库只做导航与经验沉淀。短经验状态仍以 `planning/execution/LESSONS.md` 为准，任何摘要与生效合同或当前工作包不一致时，以本索引对应的权威源为准。

当前 n5 美术返修的源文件级制作方法见 `knowledge/N5_VISUAL_PRODUCTION_PLAYBOOK.md`；它是待实图验证的制作配方，不能取代有效合同、rubric、n4 缺陷关闭标准或 n5 工具实施设计。

## 历史与待启动资料

- `NEXT_ITERATION_PLAN.md`：2026-10-24 的缺陷分析与 Q01–Q09 设计背景。其 T0–T4、“先独立批准样板再扩图”、当时的分数和未实施状态均已过时，不能按它领取任务。Q 的当前执行以有效合同、实际质量检查代码及本轮返修工作单为准。
- `PROJECT_TASKS.json` 中早期已完成任务的 `inputs`、`outputs`、`resume_action`、标题可以保留当时的计划/证据路径；**仅 status/depends_on/owner_role 和当前 I07 返修状态用于排程**，开放缺陷与候选号以活动返修指针为准。不要从历史 `inputs` 重新执行 T0–T4。
- `delivery/next_cycle/T0/active_spec_index.json`：P01 当时交付的冻结证据。虽然文件自称“唯一活动规则”，它记录的是当时快照，已被本索引取代，不修改原证据。
- `planning/performance/WORKFLOW_REVIEW.md`、`REMAINING_WORKFLOW_OPTIMIZATION.md`、根目录 `PERFORMANCE_OPTIMIZATION_PLAN.md`：历史排程、任务数量和提速假设。只用于追溯；当前性能试点要求可参考 `planning/performance/PERFORMANCE_TEST_PROTOCOL.md`，不得把计划值写成实测。
- `reference/planning_history/`、旧候选 manifest/截图/报告：只读历史，不作为当前生产或批准输入。
- 游戏玩法、微信真机与可选地图工具仍属账本中的后续范围；本期 art_required 不自动扩展。

## 冲突处理

先确定文件是当前指令还是历史证据，再核候选 ID、账本 revision、合同/rubric 版本和源→构建→采集哈希。相同主题有冲突时，停止沿用旧句子，按上面的责任归属核实；不要修改旧冻结文件消除冲突。发现新的活动冲突时更新本索引及实际入口，保留旧文件原貌与原因记录。
