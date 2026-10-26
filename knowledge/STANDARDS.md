# 当前规范速查卡

更新：2026-10-26。本页帮助定位和执行规范，**不复制合同数值作为新权威**。运行前读 `planning/execution/CURRENT_INSTRUCTION_INDEX.md`、活动返修指针和当前工作包；若本页与生效合同、账本或新独立报告冲突，回到原文件核实并更新本页。

| 主题 | 执行要求 | 权威来源 / 核验 |
|---|---|---|
| 当前目标 | 以 `PROJECT_TASKS.json` 的 scope、活动返修指针的 `next_candidate/open_findings` 和生成工作包确定下一步；低分不是停工出口 | `START_HERE.md`、`EXECUTION_PROTOCOL.md`；运行 `tools/workflow.py summary --write` |
| 角色与权利 | 角色源只读有效合同的锁定来源；复用资源的技术可用性不等于微信商业发布权利 | `art_review/harness_contract.json`、`P1_ART_STYLE_GUIDE.md`；核原源、动作、来源记录及许可状态 |
| 可编辑美术 | 环境/道具保留 Blender 原生源，UI 保留 SVG/Krita 原生结构，角色保留原 Spine/兼容动作；PNG 是导出/预览，不是唯一源；当前生产禁 AI Image 直接出图 | `AGENTS.md`、`ART_WORKBENCH_SPEC.md`、`FULL_ART_DELIVERY.md`；重开源、改单个参数、重新导出并在 Cocos 看结果 |
| P1 风格 | 用指定 P1 原帧对照构图、材质/植物层次、角色/UI 关系；以目标引擎真实 canvas 原尺寸图判最终画面 | `P1_ART_STYLE_GUIDE.md`、`PHASE1_ART_ACCEPTANCE.md`、`reference/_raw_screenshots/P1/`；同机位前后图和逐维观察 |
| 质量检查 | 制作侧提交筛选与正式独立验收分开；四卡逐卡、核心维度和最低维度均按当前文件执行，不用平均分掩盖失败 | `planning/execution/producer_review_policy.json`、`art_review/rubric.json`、`PRODUCER_SELF_REVIEW.md`；保存真实自评分和独立复核 |
| 证据同源 | 源→导出→构建→真实 canvas/Q/绑定→自审→独立审核保持可追溯；改源/相机/全局 UI 后重新计算受影响范围 | `art_review/harness_contract.json`、`HARNESS.md`、当前返修报告；核 SHA、显式 build report 和实际输入结果 |
| 候选冻结 | 旧候选只读；源 ZIP 先锁定，再由 manifest 引用其 SHA；外层审阅 ZIP 的 SHA 放包外。哈希或 build_id 错配要重建证据，不能改字段伪装通过 | `art_review/reports/candidate_n4_provisional_20261026/REPORT.md`、`planning/performance/N5_EXECUTION_DESIGN_AND_GAP_AUDIT.md`；负例及最终完整校验 |
| 自我学习 | 每批先记可证伪假设，再改源、预览、找反例、复验和总结；一次成功只算经验提案 | `planning/execution/SELF_LEARNING_LOOP.md`、`planning/execution/LESSONS.md`；核 decisions/events 与前后图 |
| 性能与效率 | 局部预览减少无效构建，正式完整检查不减；试点运行次数和时间收益须按全轮日志实测 | n5 执行设计、`planning/performance/PERFORMANCE_TEST_PROTOCOL.md`；分别报告命令时长、整轮墙钟、unknown 和画质 |
| 微信与地图后续 | 浏览器 Q 和地图工具方案不代表微信真机或完整玩法已交付；宿舍区地图属于后续方案，启动范围以账本为准 | `PROJECT_TASKS.json`、`SPACE_CITY_DORMITORY_MVP_REFERENCE_AND_ART_PLAN.md`；未测明确写未测 |

更新任一规范时，先改权威文件及其版本/审批流程，再检查本页、`knowledge/RECIPES.md` 与工作包文字是否需同步。知识库不能自行提高或降低门槛。
