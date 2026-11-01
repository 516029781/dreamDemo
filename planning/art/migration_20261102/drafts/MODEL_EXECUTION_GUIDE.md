# 给执行模型：P1 秋日庭院静态地图（业务专属指南）

> 2026-11-02 修订：本文件只适用于 `business_id = p1_autumn_static`，不是跨业务通用必读。
> 通用规则见 `knowledge/common/dev_core/`；业务包入口见 `knowledge/business/p1_autumn_static/START_HERE.md`。

## 当前任务

制作一张原创布局的秋日庭院静态环境地图和可重开的 Blender 场景。唯一整图视觉目标为
`reference/_raw_screenshots/P1/t084s.jpg`（SHA256 `13706e7e…7446de`）。当前候选为 `v25`（V27 工作图），
状态见 `planning/art/ACTIVE_STATIC_ART.json`。角色、UI、动画、玩法、Cocos、微信与完整游戏验收均暂停。

## 必读入口

1. `AGENTS.md`、`START_HERE.md`（通用）
2. `knowledge/business/p1_autumn_static/START_HERE.md`（业务路由）
3. `BUSINESS_PROFILE.md`、`STYLE_PROFILE.md`、`scorecard.json`
4. `planning/art/STATIC_MAP_WORKFLOW_20261028.md`
5. `planning/art/P1_T084_ART_DIRECTION_STANDARD_20261028.md`
6. `knowledge/MAP_PARAMETER_HARNESS_RULES_20261029.md`
7. 需要时：`.agents/skills/p1-art-director/SKILL.md`、`p1-map-environment-art/SKILL.md`

## 当前状态与下一步

视觉目标已锁定。先核验参考、场景、成图三份 SHA；当前源—图同源为 `unverified`。
CW-8/CW-9 的网格、tileKey、路线数只作解析器 fixture，不得套用为 P1 尺寸或视觉验收标准。

质量核验器 `tools/static_map_quality_gate.py` 与项目级 Codex hook 已配置；gate 读取候选
`GATE_REPORT.json`，重算评分并核验绑定与门槛，但不启动 Blender、不读图，也不能证明评审独立性。
**注意：机械 gate 仍含旧版 `no_vegetation` 硬门槛，与 2026-11-02 起的植被政策不兼容；
在同步前不得用其结论声称通过。**

按 G0 在候选中建立 `reference_analysis/P1_REFERENCE_PROFILE.json`；未校准的屏幕位置/面积容差标 `manual_only`。
参考图 UI/角色区域只标为不可观察遮挡 mask。旧 `style.json`、`regions.json`、`target_layout_v04.json`
及读取它们的旧脚本不得用于当前 PASS/FAIL。文档规则未由实际命令执行时，不得写成“自动 Harness 通过”。

## G3 自检与评分（2026-11-02 修订）

G3 先做制作侧逐维自评与人工机械资料核对：按六维 `0–4` 打分，逐维写“参考可见什么、当前少了什么、
最强反例、保分/扣分理由”，绑定当前最终图 SHA；算术与门槛由 gate 复核。

**独立盲评不再作为交付前置条件**（用户 2026-11-01 决定，P1 Harness 架构文档同口径）。
如另行组织评审，只能作为诊断参考，不得阻塞或在报告中伪称为“独立认证”。

低于 85、任一维低于 3、组合项或硬门槛失败时，先修原生源并同机位重渲，再重评；
新图 SHA 改变后旧评分失效。连续两轮无改善换方法，不设普通轮数上限，也不在中途等待阶段批准。
只有真实外部阻塞才报告未完成。

## 每批记录

固定机位前后图、参数、命令与退出码、耗时、源/图 SHA、失败反例与决定；一次只验证一个主假设。
