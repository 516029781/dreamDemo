# 鼠鼠：P1 静态地图任务入口

当前只制作 P1 秋日静态环境图与可重开的 Blender 场景。画面完全无植被；不做角色、UI、动画、玩法、Cocos 或微信测试。无需其他模型独立终审，制作模型持续自评、修复并通过项目 gate 后交付。

## 开工前按序读取

1. `AGENTS.md`：当前约束、范围和执行边界。
2. `planning/art/ACTIVE_STATIC_ART.json`：当前源/图 SHA、状态和活动工作单。
3. 状态文件指向的活动工作单：本轮具体修复目标。
4. `planning/art/STATIC_MAP_WORKFLOW_20261028.md`：G0–G3、返修、交付和版本规则。
5. `planning/art/P1_T084_ART_DIRECTION_STANDARD_20261028.md`：固定参考、无植被改编、评分和硬门槛。
6. `planning/art/CODEX_STATIC_MAP_QUALITY_HOOK_20261029.md`：v3 报告字段和项目 gate 规则。

不要按文件修改时间猜最新候选，不从历史方案章节号领取任务。项目 skill 仅在需要 Blender 指引时读取；地图参数 Harness 调研不属于每轮必读。

要理解为什么 Hook/Gate 不等于完整 Harness、哪些环节已自动化或仍由模型手动完成，读 `planning/art/P1_ART_HARNESS_ARCHITECTURE_20261102.md`。它是架构说明，不增加每轮制作步骤。

## 固定目标

唯一整图参考是 `reference/_raw_screenshots/P1/t084s.jpg`。保留它的构图、暖浅石地、设施明暗、近中远层次等可见指导；不复刻树叶/草坪。左侧原树占位改为有功能的维护柜/设备组，右侧圆筒草池改为封闭圆筒设备。禁止任何植物模型、贴图、花池或裸土。评分是对无植被改编画面的完成质量，不把被移除的植被作为扣分项，也不声称植物相似度达标。

## 执行方式

一次连续完成 G0–G3：锁输入 → 灰模空间 → 代表组合 → 正式静帧 → 制作侧六维自评与自我返修 → 隔离重开复现 → 运行 v3 gate。低分就修 Blender 原生源并重新渲染/评分；不等待阶段审批或其他模型终审。绑定图片 SHA 变化后重新自评和绑定。gate 不看图片、不运行 Blender；它只验证结构化证据、数值与 SHA。

不要使用旧视觉脚本、完整游戏账本或完整游戏 Harness 验收静态图；不要运行 `tools/workflow.py summary --write`。开发链路时序图见 `planning/art/STATIC_MAP_CHAIN_AUDIT_AND_SEQUENCE_20261101.md`。
