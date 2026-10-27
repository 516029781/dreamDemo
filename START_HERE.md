# 鼠鼠：执行入口

当前规则的责任与历史文件分类见 `planning/execution/CURRENT_INSTRUCTION_INDEX.md`。先按该索引判断文件是否仍是活动指令。

当前 n5 整画面视觉目标见 `planning/art/P1_VISUAL_TARGET_LOCK_20261027.md`：唯一主参考固定为 P1 `t084s.jpg`；其他时间点只承担该文档列出的辅助用途。旧多帧平均和 t015 区域数值保留为历史研究，不能代替本轮主参考或直接成为新候选硬门槛。

按问题检索规范、可复用操作用例和真实失败案例，可读 `knowledge/README.md`；它是知识入口，不替代当前账本、合同或审核结论。

**当前恢复点（2026-10-25）：独立审核退回后的制作侧返修。**先读 `planning/execution/ACTIVE_REWORK_CYCLE.json`，以其中 `next_candidate` 和 `open_findings` 为当前值，再读它指向的审核报告与返修工作单。`source_candidate` 及已完成尝试的证据只读；从原生源继续新候选。旧的 V06/V07/47项首次制作路线已完成，不从头重做。`PROJECT_TASKS.json` 仍是唯一任务账本。低于自审门槛时，工作包的下一动作是**实际修改一个开放缺陷并重新看图**，不是只写下一轮计划。

**2026-10-25用户新要求：完整候选做完后集中评审，取消制作途中的P08/V09外部审核阻塞。** 当前制作范围art_required，目标I07全套美术候选；独立审核和正式放行仍保留。

1. 读MODEL_EXECUTION_GUIDE.md、AGENTS.md、EXECUTION_PROTOCOL.md。
2. 在项目根运行 `tools/workflow.py storage --enforce`，记录容量基线；再运行 `tools/workflow.py summary --write`，读取 `delivery/workflow/CURRENT_WORK_PACKAGE.md`。10 GiB 预警；超过 12 GiB 只暂停新的大构建/导出/审阅包，不暂停返修和容量恢复。预计新增 ≥50 MiB 时用 `storage --planned-growth-mib <预计值> --enforce` 再检查一次。
3. 若当前有开放的独立返修周期，优先按返修工作单完成新候选；否则按真实制作依赖连续完成当前范围。P07→V06→V07→47组候选→I01—I07 是历史首次制作路线，不重复执行。
4. 全套候选完成后先按PRODUCER_SELF_REVIEW自行评分/返修；四卡各>=90且机械检查通过后，再交证据和问题表，由用户安排集中评审。90是制作侧提交筛选线；独立验收仍按 `art_review/rubric.json` 的标准。候选不叫accepted/released，独立任务不自签。

PROJECT_TASKS是唯一状态源；depends_on为制作前序，review_dependencies/release_dependencies为最终批准。旧计划“V09前禁止A-*”已由用户本次要求撤销，历史版本仅归档参考。

范围/画法见FULL_ART_DELIVERY、PHASE1_ART_ACCEPTANCE、P1_ART_STYLE_GUIDE。Q01–Q09 的旧设计背景可查 NEXT_ITERATION_PLAN 第5节，但实际执行以有效合同、当前质量检查代码和本轮返修工作单为准。当前有效合同/rubric及角色源读art_review/harness_contract.json与rubric.json；vNext未审核不生效。

缺陷见planning/execution/workflow_fixes.json与实际新证据；性能状态见optimization_rollout.json。旧独立报告保留历史，不用旧结论自动覆盖新成果。禁止AI Image/扩散，复用原生源和锁定角色。

workflow.py只生成任务摘要/命令计时，不后台开发、不自动批准。评分与正式放行证书验证未取消。后续游戏/微信scope及可选工具本轮不自动开启。

制作侧自审提交过滤已接入workflow摘要。低分自行修改，不是外部审核阻塞；机器只能验算与核证据，不能替代实际看图。
