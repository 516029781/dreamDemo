# 鼠鼠：当前执行入口

**当前静态美术状态：**先读 [唯一候选状态](planning/art/ACTIVE_STATIC_ART.json) 和 [信息订正与下一轮交接](planning/art/STATIC_ART_INFORMATION_CORRECTION_20261101.md)。开工时重新核对状态文件里的 SHA 和磁盘实物；旧候选的交付与评分不自动适用于当前图。

当前任务：制作以秋日 P1 画面为唯一整图视觉目标的静态环境地图与可编辑 Blender 场景。明日方舟 CW-8/CW-9 数据只用于地图参数与 Harness 结构规则研究，不是美术主参考。

按顺序阅读：
1. AGENTS.md
2. planning/art/STATIC_MAP_WORKFLOW_20261028.md
3. planning/art/P1_T084_ART_DIRECTION_STANDARD_20261028.md
4. knowledge/MAP_PARAMETER_HARNESS_RULES_20261029.md
5. .agents/skills/p1-art-director/SKILL.md
6. .agents/skills/p1-map-environment-art/SKILL.md

历史方法与失效参数见候选状态文件的 `historical_only` 列表。下一轮具体任务以当前状态和对现存图的有效评审确定；新候选使用未占用目录。方案讨论不启动渲染或生成任务。

只做地图环境静帧，不做人物/UI/玩法/Cocos/微信。唯一整图目标是 `reference/_raw_screenshots/P1/t084s.jpg`；固定它的 SHA、锚点和画面语言。一次连续完成四个制作关口；先由制作侧自评返修，候选预检达到目标后再做两份盲评；低分就按工作单继续返修，不等待阶段批准。最终交付按工作流清单，包括可编辑源、灰模/色块/组合/最终图、细节板、REVIEW.md、DELIVERY.json、GATE_REPORT.json 和真实状态。地图参数 Harness 规则按知识库文档执行，不能覆盖或稀释视觉标准。

已有冻结候选保持原样；本轮设计基线见整体方案 §1，新候选按实际目录递增，不覆盖旧绑定。最终评分低于 85、任一维低于 3 或硬门槛失败时，必须回到原生源返修、同机位重渲并复评；不得以 `quality_below_target` 结束正常任务。仅真实外部阻塞可结束为未完成，并说明阻塞和已尝试的替代办法。

2026-10-31 复核：当前 gate 只允许 `target_met` 或证据完整的真实 `blocked_external` 结束；低于门槛时必须继续返修。开始任务时复核当前项目 gate 与此规则一致，不以机械检查代替视觉评审。

Codex 项目级静态地图 Stop hook 已配置：首次在 Codex `/hooks` 中审阅并信任后，只有明确启动 P1 静态地图制作的当前会话才会被 85 分质量门禁约束；未启动任务的对话不受影响。契约见 `planning/art/CODEX_STATIC_MAP_QUALITY_HOOK_20261029.md`。

完整游戏、旧账本和发布审核目前暂停；`delivery/workflow/CURRENT_WORK_PACKAGE.md` 属于旧账本，不要运行 `tools/workflow.py summary --write` 领取静态地图任务。美术工具调研文档仅在需要选择工具时查阅，不是每轮必读。
