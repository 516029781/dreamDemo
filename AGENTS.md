# 鼠鼠项目当前执行规则

## 当前范围：P1 秋日风格静态地图

当前只制作一张以 `reference/_raw_screenshots/P1/t084s.jpg` 为唯一整图视觉目标的秋日风格静态环境地图和可编辑 Blender 场景。唯一执行清单为 `planning/art/STATIC_MAP_WORKFLOW_20261028.md`；视觉目标与评分只以 `planning/art/P1_T084_ART_DIRECTION_STANDARD_20261028.md` 为准。明日方舟 CW-8/CW-9 的结构化数据只用于地图数据解析与 Harness 规则研究，不得替换秋日主参考或把其格子、路线数量当成本项目地图指标。项目美术 skill 提供制作建议，不创建额外审批门。

`reference/_raw_screenshots/P1/t084s.jpg` 是已锁定的秋日整图参考，SHA256 `13706e7eab96726565156a9e6440727de5d5bac82ee9c09c293a5745dd7446de`。地图数据/Harness 规则与视觉参考分离；不得因研究了明日方舟关卡数据而改动该参考身份。继续静态地图时使用未占用的 P1 秋日目标版本目录；不得覆盖旧 v05 和冻结候选/哈希证据。

本任务不含人物、UI、动画、游戏玩法、Cocos/GLB、微信真机、全游戏 Q、release 审核或完整游戏候选。`delivery/workflow/CURRENT_WORK_PACKAGE.md` 和完整游戏账本属于暂停流程；不要用它们领取静态地图任务，也不要运行 workflow summary。历史游戏规则不对当前任务生效。

静态地图任务不要运行 `tools/art_harness.py` 或 `tools/producer_review.py`：它们默认使用完整游戏 `art_review/harness_contract.json`、四卡 rubric 和 47 项目录，不是当前 P1 静态图的验收器。当前静态图按 P1 标准的 G0–G3 和 85 分规则自评、返修并结案；地图参数 Harness 按 `knowledge/MAP_PARAMETER_HARNESS_RULES_20261029.md`，不要将完整游戏 90 分过滤器或 Q01–Q09 套进来。

## 当前制作约束

- 新建独立 Blender 场景和输出目录；固定参考、相机与验收目标后再绘制细节。
- 最终地图由可编辑 Blender 源重开渲染。按用户 2026-10-30 的授权，必要时可用小云雀辅助风格草稿、叶草图集、局部绘制纹理和远景片层；按 `planning/art/P1_SCENE_ART_REDESIGN_PLAN_20261030.md` §7 与工作流 §5 执行，保留原始结果、编辑文件、映射及来源记录，经同场景验证后使用。生成整图不得替代最终 Blender 渲染；不得把密钥写入工程或日志。
- 按 P1 秋日标准执行；分数、逐维最低项与硬门槛只读目标标准。低于 85、任一维低于 3 或有硬门槛失败时，进入最终质量闭环，诊断并返修 Blender 原生源，直到复评达标；不得改阈值或伪造分数。仅在真实外部阻塞时报告未完成。CW-8/CW-9 原始参数仅作解析器黄金样例；抽象出的结构规则可以用于本项目 Harness，但必须按本项目地图语义配置，不复制源关卡数值。
- 旧 `style.json`、`regions.json`、`target_layout_v04.json` 和读取它们的视觉脚本未经当前 P1 profile 校准；不得用其结果给新候选报通过/失败。
- 每个返修批次记录一个假设、同机位前后图、参数、命令/退出码、耗时和 SHA；连续两次没有改善就换方法并继续闭环，不作为结束条件。只有达标或真实外部阻塞才结束。
- Git 只提交代码、配置和小型规范；不入 Git 的本地源、图片、模型和证据仍要保留并列入 manifest，不能因未跟踪而删除。
- 项目目录（含 `.git` 和项目内工具）控制在 15 GiB 内，12 GiB 预警。开始和结束统计空间；预计新增 ≥50 MiB 的完整输出前先做容量预检。清理先 dry-run，保护当前源、正式证据、冻结候选和依赖包。自动清理被拒绝时停止，不绕过。

## Codex 项目级静态地图质量钩子

项目内 `.codex/hooks.json` 接入 `UserPromptSubmit` 与 `Stop`；`tools/static_map_quality_gate.py` 核验固定参考、文件 SHA、评分算术、85 分/逐维门槛、四项组合检查、八项硬门槛，并检查报告中登记的 Blender 重开复现结果。gate 不会启动 Blender 来复现。钩子只在本仓库目录受信任时加载，并按 Codex `session_id` 单独启用；只有明确开始/继续 P1 静态地图制作的用户提示才会 armed。方案讨论、未 armed 的项目对话、其他项目和其他会话不会被质量门禁阻止。状态只写入已忽略的 `.codex/state/`，不修改用户级 Codex 配置。首次使用须在 Codex `/hooks` 审阅并信任项目钩子。

Stop 未通过时必须根据门禁输出在同一会话实际返修，不可只复述计划；只有 `target_met` 或具备两种替代尝试与哈希证据的真实 `blocked_external` 才可结束。门禁能校验评分报告和证据完整性，不能从 JSON 自证视觉判断或盲评独立性；需按固定 P1 图像标准查看最终图，不能把机械通过称作独立艺术验收。完整配置和 `GATE_REPORT.json` 契约见 `planning/art/CODEX_STATIC_MAP_QUALITY_HOOK_20261029.md`。

## 暂停的完整游戏流程

完整游戏、角色/UI、Cocos、微信、Q 检查、制作账本、独立审核与发布规则目前暂停。恢复时由用户明确启动，并重新读取当时有效的游戏执行入口和合同；不要把本节历史规则混入静态地图任务。
