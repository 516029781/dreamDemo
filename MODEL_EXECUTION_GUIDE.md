# 给执行模型：完整制作后集中评审

当前视觉锚点先读 `planning/art/P1_VISUAL_TARGET_LOCK_20261027.md`：整画面固定对照 P1 `t084s.jpg`。本轮仍需制作可编辑场景和真实运行证据；旧 t015/t044 多帧平均、T5 试验变体不能自动作为整画面验收结果。

## 当前指令：candidate_n2 退回后的返修

下一制作轮先读 `art_review/reports/candidate_n4_provisional_20261026/REPORT.md` 和 `planning/performance/N5_EXECUTION_DESIGN_AND_GAP_AUDIT.md`。前者记录 n4 的 90 分差距、证据链错误和关闭标准；后者给出 n5 各类变更该跑什么、何时升级到 Cocos/全量采集、工具缺口与时间目标的计算口径。按活动返修指针使用新候选号。下一候选必须保存 `events.jsonl`、原始命令/日志、返修决策和阶段汇总，缺日志的“已提速”不得作为结论。

视觉制作按 `knowledge/N5_VISUAL_PRODUCTION_PLAYBOOK.md`：它把树枝/叶锚点、背景暗带、铺地模块、Cocos 材质/光照、对白取景和接地影分成可编辑源、局部预览、引擎复核、失败替代方法。先修结构后修表面；不靠增加随机细节或改评分文字结束返修。该配方仍须用 n5 真实图验证。

每个 n5 变更批次另按 `planning/execution/SELF_LEARNING_LOOP.md` 执行“提取相关经验→写可证伪预期→局部修改/预览→主动找反例→修复/复验→批次总结”，经验索引见 `planning/execution/LESSONS.md`。不要把仅记录下一步、评分升高或命令 exit0 当成学到并解决了问题。

2026-10-25 独立报告退回 `candidate_n2`；最新制作尝试、已解决待独立确认项、开放缺陷与下个候选 ID **只读 `planning/execution/ACTIVE_REWORK_CYCLE.json`**，不要从本段推断仍应做 n3。先读该文件指向的报告和工作单，再运行 workflow summary。对每个开放缺陷执行“低分维度与原图→共享原因→改原生母版→同机位预览→记录变化”的循环；不达标继续修，不能只报告下一步。同机位预览未达标不要完整打包。冻结候选与已完成尝试的证据不动，既有 47 项任务不从头做；自审四卡各 ≥90、Q/绑定通过、严重问题清零后才再次提交集中独立审核。90仅为制作侧筛选线，独立验收仍按 `art_review/rubric.json`。

下文第 1–3 节记载首次完整制作的历史路径，不按其 V06/V07 工作顺序重新领取任务；第 7 节的直接续做文字以活动返修指针为准。完整规则责任见 `planning/execution/CURRENT_INSTRUCTION_INDEX.md`。完成新一轮独立审核后更新返修指针，不能只改旧候选的评分或报告。

更新：2026-10-25。用户明确改变工作方式：**不要停在中途独立审核上，先完整制作、自检、打包，再交用户安排集中评审。** 当前账本为1.0.130或更新版本，实时状态以PROJECT_TASKS为准。

## 1. 首次制作阶段的历史说明（当前返修不执行）

原P08→V06和V09→47项制作的硬前置已移除；审核任务没有假签或删除，改在完整候选后处理。首次制作时 P07 及 K/V 已完成，随后进入 V06；**这不是当前下一项**。当前以活动返修指针和工作包为准。

在项目根PowerShell运行：

```powershell
Set-Location -LiteralPath 'C:\软件\鼠鼠'
$taskPython = 'C:\Users\tt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $taskPython -X utf8 tools/workflow.py storage --enforce
& $taskPython -X utf8 tools/workflow.py summary --write
```

读取delivery/workflow/CURRENT_WORK_PACKAGE.md。首次再读AGENTS与EXECUTION_PROTOCOL；以后只补读变更和当前包。不要从旧聊天/历史文档重新添加“V09前不扩批”限制。

容量预检记录在 `delivery/workflow/STORAGE_STATUS.json`。10 GiB 起预警；超过 12 GiB 时，不再启动新的全量构建、批量导出或审阅包，仍继续原生源返修、局部验证和空间恢复。预计新增 ≥50 MiB 的命令前，用 `storage --planned-growth-mib <预计值> --enforce` 重测；用 `workflow.py run` 执行时也传 `--planned-growth-mib`。每轮结束重测并记录差值。分类与复用见 `planning/performance/ARTIFACT_REUSE_AND_STORAGE.md`。

## 2. 当前完整任务指什么

本期仍是完整美术候选：一张庭院、47组资产、锁定主角/动作、固定NPC与头像、全部UI状态/字体/图标、世界反馈、可编辑源、真实引擎构建、采集绑定与检查记录。制作目标I07；全部producer任务完成并达到PRODUCER_SELF_REVIEW提交门槛后，再请求集中评审。

制作候选不是获准发布。P08/V08/V09/I08/I09共5个外部角色记录可保留待审；制作侧完整后done数不必达到82或97，不能靠自签凑数。后续完整游戏玩法/微信及可选工具本轮不自动进入。

## 3. 首次完整制作路径（历史，当前不重跑）

1. **V06**：按实际修复后的代码/源构建，冻结同屏样板候选及camera/build/canvas/hash证据。可用明确版本的vNext草案自检，但不替换生效合同，不要求先P08批准。
2. **V07**：制作侧完成Q检查、参考对照与四卡自评/差异说明，每卡>=85；不足自行返修，无需外部审核。技术故障修复，未测/未独立确认保持真实状态。自检结果定义可复用候选基线，不伪称独立pass。
3. **B04—B10 / 47项A任务**：V07后直接继续全套候选。先资产差异表，分有效复用、局部修改、结构返修、缺失；按材质/环境道具/角色/UI/FX集中处理，地图集成再清单打包。现有具体制作依赖保留，不要重新给每个资产加V09阻塞。
4. **I01—I05**：同一候选做场景、UI/行为、预算、原生编辑/依赖及viewport检查。复用采集会话与同源证据，每项结果单列；不可拿截图存在替代行为验证。
5. **I06/I07**：逐条列旧R/新F问题的制作侧结果、未解/待独立确认项及完整覆盖；freeze/prepare完整候选，按PRODUCER_SELF_REVIEW做自审返修；每卡>=90、核心>=3、任维>=2、Q/绑定通过且无未解严重问题，才交启动方式、源、原图/动作、日志和问题表。独立验收采用单独 rubric。
6. **交用户集中评审**：P08规则→V08样板/角色证据→V09样板证书；I08全量审查→I09正式放行。可在一次评审周期形成多份记录，制作模型不在此前停工等待这些签认。

发布验证仍可要求完整证书链，候选prepare/构建不要求先有批准。如果harness verify返回needs_review/无密钥，保存该事实并继续制作，不把verify当进入下一制作任务的开关。不要调用attest/certify自造批准。

## 4. 真正的阻塞与持续自检

外部审核待回复不是中途阻塞。真实缺失资源/设备、不可运行构建、损坏源或无法完成的技术故障需要记录并修；其他独立工作继续。模型能修的错误不能包装成外部阻塞。

仍需运行对应检查并保存实际退出码；技术/行为失败不写pass。已知审美差距主动修，最多先3个有解释的原生候选，不无限微调；统一配置/母版防止47项风格漂移。未独立评审批量制作的内容统一标candidate_not_independently_approved。

允许正常评审交接：完整本期候选及全部制作任务已提交且制作侧筛选通过；低分应继续自行返修。真实停止例外：真实外部资源阻塞且没有可做工作；用户暂停；运行限制必须交接。不能因P08或V08/V09未批而停在半成品。

## 5. 既有缺陷与优化继续追踪

planning/execution/workflow_fixes.json记录F01—F08，原R01—R10保留。最新模型报告P00—P07和V01—V05已完成制作侧修复，本次不重新判定修复质量、不回滚新成果；独立确认留最终。

重点复用：前序证书实际依赖绑定、冻结历史恢复、schema/失败状态修复、真实canvas、日志失败优先、定向构建和Q检查。核实际新文件与报告，不因为旧文档说“待实现”就再做一次。

原生源版本化；不覆盖旧冻结包、不改后缀伪造源；禁止AI Image/扩散/局部生成修补。角色来源只读有效合同；不重选引擎、重装工具或重画已有角色，不先开发Forge/MCP平台。

当前包显示execution_optimization动作，按实际依赖定向构建、共享UI组件/材质和采集会话。最终全量覆盖不减。性能状态索引optimization_rollout.json需随实际实现更新，不直接把制作侧done当性能目标已通过。

## 6. 计时与交付汇报

可包装单个明确命令记录耗时：

```powershell
& $taskPython -X utf8 tools/workflow.py run --package B03 --label sample-audit --planned-growth-mib 0 -- $taskPython -X utf8 tools/art_harness.py audit
```

日志在delivery/performance/<run_id>/。audit本身可能返回未接受，需看日志并正确分类；退出0也不代表美术批准。单命令耗时不等于端到端，未知间隔、首次工具成本、返修和外部等待单列。性能A/B仍按PERFORMANCE_TEST_PROTOCOL执行，不声称未测的提速。

每项更新ledger/checkpoint后重新生成摘要继续。最终给用户完整候选包位置、运行步骤、实际覆盖、未测/已知问题、真实计时和所有待评审记录；不要只汇报完成几项或要求中途指定审核者。

## 7. 直接续做指令

> 先读 `planning/execution/ACTIVE_REWORK_CYCLE.json` 指向的独立报告和返修工作单，使用其中 `next_candidate` 与 `open_findings`，不要沿用旧候选 ID。先选择影响最大的开放视觉缺陷，实际修改可编辑母版、同机位看图并记录改善，再处理下一项；低于自审门槛就继续此循环，不以“已制定下一步”为完成。达到完整制作侧门槛后才集中交独立审核，不自签批准。既有 47 组无需从 V06 重来。


## 8. 自审先过滤低质量（最新要求）

先读PRODUCER_SELF_REVIEW.md。相同模型可以独立进行一轮批判性自审，但身份仍是producer_self_review，非独立批准。低分、缺证据、Q/绑定失败都继续自行修复，不找最终审核者等待。完整包每卡自评>=90并经producer_review.py check筛选后才请求集中评审。90仅为制作侧提交筛选线；检查器不判断真实审美，最终仍抽查，不能靠虚报高分过关。
