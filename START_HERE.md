# 鼠鼠：当前执行入口

当前任务：制作以秋日 P1 画面为唯一整图视觉目标的静态环境地图与可编辑 Blender 场景。明日方舟 CW-8/CW-9 数据只用于地图参数与 Harness 结构规则研究，不是美术主参考。

按顺序阅读：
1. AGENTS.md
2. planning/art/STATIC_MAP_WORKFLOW_20261028.md
3. planning/art/P1_T084_ART_DIRECTION_STANDARD_20261028.md
4. knowledge/MAP_PARAMETER_HARNESS_RULES_20261029.md
5. .agents/skills/p1-art-director/SKILL.md
6. .agents/skills/p1-map-environment-art/SKILL.md

本轮整画面美术方案：[P1_SCENE_ART_REDESIGN_PLAN_20261030.md](planning/art/P1_SCENE_ART_REDESIGN_PLAN_20261030.md)。当前背景方案以 V16 场景为只读布局基线，V17 有实验文件；下一轮使用未占用的新版本目录。方案统筹场所用途、背景结构、光色和树草母版，包含用户授权的小云雀辅助绘图边界；补充现有 G0–G3 的制作方法，不替代视觉标准或降低门槛。方案讨论不启动渲染或生成任务。

只做地图环境静帧，不做人物/UI/玩法/Cocos/微信。唯一整图目标是 `reference/_raw_screenshots/P1/t084s.jpg`；固定它的 SHA、锚点和画面语言。一次连续完成四个制作关口；先由制作侧自评返修，候选预检达到目标后再做两份盲评；低分就按工作单继续返修，不等待阶段批准。最终交付按工作流清单，包括可编辑源、灰模/色块/组合/最终图、细节板、REVIEW.md、DELIVERY.json、GATE_REPORT.json 和真实状态。地图参数 Harness 规则按知识库文档执行，不能覆盖或稀释视觉标准。

已有冻结候选保持原样；本轮设计基线见整体方案 §1，新候选按实际目录递增，不覆盖旧绑定。最终评分低于 85、任一维低于 3 或硬门槛失败时，必须回到原生源返修、同机位重渲并复评；不得以 `quality_below_target` 结束正常任务。仅真实外部阻塞可结束为未完成，并说明阻塞和已尝试的替代办法。

2026-10-31 复核：当前 gate 只允许 `target_met` 或证据完整的真实 `blocked_external` 结束；低于门槛时必须继续返修。开始任务时复核当前项目 gate 与此规则一致，不以机械检查代替视觉评审。

Codex 项目级静态地图 Stop hook 已配置：首次在 Codex `/hooks` 中审阅并信任后，只有明确启动 P1 静态地图制作的当前会话才会被 85 分质量门禁约束；未启动任务的对话不受影响。契约见 `planning/art/CODEX_STATIC_MAP_QUALITY_HOOK_20261029.md`。

完整游戏、旧账本和发布审核目前暂停；`delivery/workflow/CURRENT_WORK_PACKAGE.md` 属于旧账本，不要运行 `tools/workflow.py summary --write` 领取静态地图任务。美术工具调研文档仅在需要选择工具时查阅，不是每轮必读。
