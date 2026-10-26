# 当前工作包（由账本生成）

账本：1.0.141；范围：art_required；工作包：B11。

先读 MODEL_EXECUTION_GUIDE.md。当前为完整候选后集中评审模式；待审核不阻塞制作，不自签放行。
相关规范/最佳用例/失败案例检索：knowledge/README.md（导航资料，不替代合同与当前工作包）。

制作目标：I07

最终制作侧提交筛选：四卡各自评≥90、核心≥3/4、所有项≥2/4；Q/绑定通过且无未解严重问题。独立验收仍按 art_review/rubric.json。低分自行返修，不找外部审核者等指令。

最近尝试的提交筛选：producer_rework_required（candidate_n5）

Ready：I07

## 当前独立审核退回：先执行返修

冻结候选：candidate_n2；下个候选：candidate_n5。
审核报告：art_review/reports/independent_20261025_candidate_n2/REPORT.md
返修工作单：art_review/reports/independent_20261025_candidate_n2/REWORK_EXECUTION_SPEC.md
开放项：N01, N02, MIX
N03 is executed and waits on an external reviewer. N01 and N02 are partially executed: paving, hedge depth and duplicate faces are done, tree-crown topology and material micro-variation are not. Re-run the formal camera set and hand the frames to a reviewer outside this model before any further scoring work.
执行闭环：选一个开放缺陷→从低分维度和原图定位共享原因→改可编辑母版→同机位预览→记录是否改善；未改善立即换结构方法，改善后再构建/采集/评分。自审未达门槛时不得以“已记录下一步”结束制作轮。
既有制作任务 done 不代表本次独立退回已解决。当前不应交外部放行；先修复并重新冻结新候选。

提示：Workspace over 12 GiB: do not generate another large build/export/package; continue source repair and storage recovery.

提示：Checkpoint revision differs; ledger wins, preserve previous evidence.

提示：Some previously done tasks have reopened ancestors; downstream scheduling checks the whole chain.

## 本工作包的提速措施（不是已完成证明）

- OPT06 同候选共享检查与完整出口：pending；先绑定真实源/构建/配置；不沿用已失效批准。
- OPT08 真实计时与净收益验证：partial；已有单命令与分阶段计时；仍无端到端模型开发/审核等待A-B结果。

## I07 冻结完整美术候选包并完成制作侧检查（集中评审入口）

状态：rework；角色：producer；ready=True
未完成制作前序：无
最终评审/放行依赖（不阻塞候选制作）：P08, V08, V09, I08, I09

验收：
- 当前开放项：N01, N02, MIX
- 在 candidate_n5 下实际修复并同机位比较；按当前工作单逐项关闭。
- 47项覆盖、四卡各≥90、Q/绑定通过、严重问题0；同源冻结并请求集中独立审核。

本轮输出：新候选的可编辑源、正式画面、行为/Q结果、自审与检查结果、manifest和审阅包；实际路径更新到返修指针和账本。旧候选路径只作历史证据。

本任务的流程优化动作：
- 复用有效证据并完整冻结；计入首次优化成本及返修，不把draft证据当正式通过。

下一动作：N03 is executed and waits on an external reviewer. N01 and N02 are partially executed: paving, hedge depth and duplicate faces are done, tree-crown topology and material micro-variation are not. Re-run the formal camera set and hand the frames to a reviewer outside this model before any further scoring work.

本轮执行优先级：上方当前返修指针与工作单覆盖此任务中旧 N01–N08 叙述；只重做 open_findings，resolved_pending_independent 在相关依赖变化时复核。原有 47 项覆盖及最终门槛继续有效。

