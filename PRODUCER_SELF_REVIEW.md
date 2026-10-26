# 制作模型自审与低分返修

2026-10-25。用户要求低质量先由执行模型自己改，达标后再提交最终评审。自审不需要外部审核者；允许同一个制作模型切换到审查视角，但reviewer.mode必须是producer_self_review，不能冒充独立角色。

## 1. 提交门槛

| 条件 | 样板V07 | 完整候选I07提交 |
|---|---:|---:|
| ENV环境、CHAR角色、UI界面、MIX融合 | 每卡>=85 | 每卡>=90 |
| 核心维度（0—4） | >=3 | >=3 |
| 任意维度（0—4） | >=2 | >=2 |
| Q01—Q09及实际采集绑定 | 全部通过 | 全部通过 |
| 未解决blocking/major | 0 | 0 |
| 资产覆盖 | 样板要求 | 全部47组 |

四卡分别算，不能平均；使用现有rubric权重按sum(weight*score/4)计算，不先四舍五入。3分全部满足仅75，不许为凑90无证据改4。4分要求至少两个相关候选机位/状态的证据，实际表现也必须支持多情境一致。角色来源读有效合同，不照抄rubric内的历史候选说明。

90是制作侧提交筛选门槛，独立评分标准当前为 `art_review/rubric.json` 的85分，不表示真实质量客观达到90%，也不是视觉相似度百分比。代码验证不了审美或诚实程度，最终审查仍会抽查实际图/源/行为。

## 2. 每轮自己做什么

每批返修的自我发现步骤详见 `planning/execution/SELF_LEARNING_LOOP.md`。先写可证伪预期，预览后主动找非目标区域/状态的反例，核修复是否造成回归；将失败假设和下次最小检查写入 `performance/decisions.jsonl`，把可复用经验记入 `planning/execution/LESSONS.md`。经验不替代本节实际看图、Q/绑定和独立审核。

1. 完成一批制作后，切到审查视角，先打开当前原尺寸图、运行状态和P1对应画面，再读自己实现细节。不能只读日志、缩略图或自报pass。
2. 按ENV/CHAR/UI/MIX逐维填写观察、参考差异、分数、修复动作/可接受理由、参考和候选证据及hash。缺证据填null/未测，不填高分。
   若任何卡低于完整提交门槛，直接从检查结果的 `dimension_diagnostics` 按失分权重和共享原因挑下一处修改；写明“改哪个原生母版、改什么结构、看哪张固定机位图”。本轮至少执行这次修改和预览，不能把动作只留在报告的 `next_action`。
3. 核实际源→导出→构建→采集绑定；运行既有Q/绑定检查，正常移动对照、遮挡、暂停/触控、空满重置、viewport不可遗漏。
4. 先修严重问题，再修失分权重最大的共享原因：如树冠体块、相机/材质、UI组件。不要对每张图分别打补丁，也不要重画已有角色。
5. 只重建/采集受影响内容，更新冻结manifest及review绑定，重算分数。构建/相机/源变化后不能沿用旧分数或旧截图。
6. 连续三轮无改善，记录失败原因并换方法/缩小诊断，不自动停工找最终审核者。真实权限、设备或缺源问题如实上报；不能伪造达标或把能力不足写成已完成。

## 3. 报告与工具

策略：planning/execution/producer_review_policy.json。
样板报告：delivery/next_cycle/T3/producer_self_review.json。
完整报告：delivery/next_cycle/T4/producer_self_review.json。

先对实际候选prepare/freeze manifest，再生成一个新的空模板（以下manifest参数替换为实际项目相对路径，不要直接填占位文本）：

```powershell
& $taskPython -X utf8 tools/producer_review.py template --manifest <实际候选manifest路径> --out delivery/next_cycle/T4/producer_self_review.json
```

模板生成不等于审过。模板不覆盖已有报告；返修时保留旧报告到round_01等版本目录，再用实际观察填写新版本。报告应包括：

- reviewer真实身份/producer_self_review；manifest、有效rubric/合同、提交策略的hash。
- 每维score、observation、gap、action_or_acceptance_reason、reference_evidence、candidate_evidence。
- 证据格式为项目相对path与sha256；参考必须含真实P1原帧，候选来自该manifest快照。
- quality_results为真实Q结果输入JSON的path/hash；capture_binding为真实绑定输入JSON的path/hash，不是把一份pass摘要冒充原始输入。
- 完整候选asset_checks覆盖47项，逐项decision/reason/evidence；可以复用已有item_review内容和原图，不再重做素材。
- 完整报告issues必须逐条对账旧R/新F已知问题，不能删掉问题伪装无缺陷；已修待独立确认用fixed_pending_independent_confirmation并附实际resolution_evidence，不自行填写独立通过。

填写后执行：

```powershell
& $taskPython -X utf8 tools/producer_review.py check --review delivery/next_cycle/T4/producer_self_review.json --out delivery/next_cycle/T4/producer_submission_check.json
```

exit0=制作侧提交筛选通过，accepted仍false；exit3=**立即回到原生源修改与同机位预览**，不是本轮正常结束；exit2=输入/执行错误。输出给出失分维度、证据问题和制作模型自己填写的修复建议，不等于机器视觉判分。检查器重算分数/核hash，并调用既有Q和绑定验证器；依赖环境缺失必须修复或如实记录，不能用自评分代替。

## 4. 何时可以交给用户评审

完整包及全部producer任务完成，并且完整自审检查ready_for_final_review=true，才请求最终集中评审。V07内部自审无需用户参与，不恢复P08/V09中途外部阻塞。

没有ready账本任务但自审未达标时，继续修复相关制作任务、更新证据和分数；不能说“只剩外部审核所以停”。workflow摘要会显示producer_self_review_required或producer_rework_required并指向B11。

检查通过只允许提交，不能自动给P08/V08/V09/I08/I09写done、生成密钥或签证书。最终评审集中处理规则/样板/全量记录；用户收到的是完整且已自行筛过质量的候选包。

## 5. 转交执行模型

> 你可以自己审核和返修，不需要等外部审核者。按PRODUCER_SELF_REVIEW.md看实际P1和当前产物，样板四卡各>=85，完整候选四卡各>=90；核心>=3、任意项>=2，Q/绑定通过，无未解严重问题。低分自己改、重采证据再评，连续三轮无改善换方法，不自动交低质量包给用户。完整制作且producer_review检查可提交后，再请求用户最终集中评审。自审身份必须如实标注，不能自签独立批准。90仅为制作侧提交筛选线，独立验收仍按 art_review/rubric.json 执行。
