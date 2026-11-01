# 给执行模型：P1 秋日风格静态地图

## 当前任务

只制作一张原创布局的静态环境地图和可重开的 Blender 场景。唯一整图视觉目标为 `reference/_raw_screenshots/P1/t084s.jpg`（秋日场景，SHA256 `13706e7eab96726565156a9e6440727de5d5bac82ee9c09c293a5745dd7446de`）。明日方舟 CW-8/CW-9 只提供结构化地图数据与 Harness 规则研究，不作为视觉参考。角色、UI、动画、玩法、Cocos、微信与完整游戏验收均暂停。

## 必读入口

1. `AGENTS.md`
2. `START_HERE.md`
3. `planning/art/STATIC_MAP_WORKFLOW_20261028.md`
4. `planning/art/P1_T084_ART_DIRECTION_STANDARD_20261028.md`
5. `knowledge/MAP_PARAMETER_HARNESS_RULES_20261029.md`
6. `.agents/skills/p1-art-director/SKILL.md`
7. `.agents/skills/p1-map-environment-art/SKILL.md`

## 当前状态与下一步

视觉目标已锁定为秋日 P1 主参考。先核验该图 SHA，再使用目标标准中记录的锚点、区域和画面特征；CW-8/CW-9 的 12×8 网格、tileKey 分布、路线数等只作为源数据解析器的黄金 fixture，不得套用为 P1 地图的尺寸或视觉验收标准。

质量核验器 `tools/static_map_quality_gate.py` 和项目级 Codex hook 已配置；gate 读取候选的 `GATE_REPORT.json`，重算评分并核验绑定与门槛，但不启动 Blender、不读图，也不能证明盲评者真实独立。hook 只有在项目配置受信任且当前会话明确启动本任务时才生效。自动 preflight、盲评调用/身份验证、渲染编排与候选冻结尚未实现。

按 G0 在本候选中建立 `reference_analysis/P1_REFERENCE_PROFILE.json`；当前 profile 尚未校准，无法复核的屏幕位置/面积容差标为 `manual_only`，不得伪装自动通过。参考图中 UI/角色区域只标为不可观察的遮挡 mask，不制作这些内容。现有 `style.json`、`regions.json`、`target_layout_v04.json` 及读取它们的旧视觉脚本不得用于当前 PASS/FAIL。文档规则未由实际命令执行时，不得写成“自动 Harness 通过”。

在未占用的 P1 秋日静态地图版本目录连续完成 G0–G3。G1 先用临时机位完成灰模和早期色块，确认构图后再锁相机；只预留未来空间关系，不宣称本静态图可行走。每个返修批次记录一条可证伪假设、Blender 源/参数、固定机位前后图、命令与退出码、耗时、SHA、失败反例和决定。

G3 先做制作侧逐维自评和人工机械资料核对。自查低于 85、任一维低于 3、组合检查或硬门槛失败时，先修原生源并重渲，不启动盲评；制作侧认为达到目标且资料齐备后，再让两个分开的盲评过程查看同一最终图。两份都须 ≥85、每维 ≥3，且各自的四项组合检查与八项硬门槛通过。盲评失败就按扣分证据修复；新图 SHA 改变后重做两份盲评。连续两轮无改善时换方法，不设普通轮数上限，也不在中途等待用户审核。只有真实外部阻塞才报告未完成。

## 保护与边界

- 旧 v05 及所有已绑定证据保持原样；新目标建立后另作评审，不迁移旧分数。
- 使用可编辑 Blender 原生源、手绘或可追溯的程序化资产；不使用 AI Image 直接生成最终地图/贴图或图生图修补。
- 当前工作包和账本属于暂停的完整游戏流程；不要运行 `tools/workflow.py summary --write` 或据此领取当前任务。
- 最终交付静帧、`.blend`、灰模/色块/组合/最终图、局部细节板、`REVIEW.md`、`DELIVERY.json` 和 `GATE_REPORT.json`。完成后运行 `python tools/static_map_quality_gate.py --candidate art/static_map/p1_autumn_courtyard/vNN`，将真实输出写入交付记录。评分、硬门槛和状态依据 P1 秋日美术标准；结构化地图数据校验依据 Harness 规则文档。机械 gate 通过不能单独证明画质或评审独立性。

完整游戏的历史指南已移至 `planning/execution/_archive/MODEL_EXECUTION_GUIDE_FULL_GAME_HISTORY_20261029.md`，不对当前静态地图任务生效。
