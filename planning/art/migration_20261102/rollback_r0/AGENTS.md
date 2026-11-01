# 鼠鼠项目执行规则

## 当前项目范围

当前任务只制作 P1 秋日静态环境图与可重开的 Blender 场景，不做角色、UI、动画、玩法、Cocos/GLB、微信小游戏或真机验证。执行入口为 `START_HERE.md`；唯一整图参考为 `reference/_raw_screenshots/P1/t084s.jpg`，SHA256 为 `13706e7eab96726565156a9e6440727de5d5bac82ee9c09c293a5745dd7446de`。活动候选和工作单以 `planning/art/ACTIVE_STATIC_ART.json` 为准。

## 当前硬性美术约束

- **画面完全不出现植被**：不得制作或保留树、树叶、草、花、灌木、苔藓、藤蔓、杂草、盆栽、裸土/花池或植物图案/贴图。左侧原树区域用有功能、有底座、有检修面的高型维护柜/设备组替代；右侧原草池用封闭式圆筒过滤/储液设备替代。设备不得随机堆放或悬空。
- P1 原图仍提供构图、暖石地、明暗、工业物件和远景层次参考。原图植物仅是已观察的事实，不是新图目标；按要求移除植物不扣分，也不能声称已复刻植物细节。
- 质量目标为总分 `≥85/100`、六维各 `≥3/4`，且组合项/硬门槛全部通过。维度定义只读 `planning/art/P1_T084_ART_DIRECTION_STANDARD_20261028.md`。

## 制作、返修与验收

- 按 `planning/art/STATIC_MAP_WORKFLOW_20261028.md` 连续完成 G0–G3，不等待阶段审核或其他模型独立终审。制作模型负责看绑定图片、自评、找低分根因、修改 Blender 原生源、同机位重渲并循环至达标。
- 质量 gate 只检查文件、SHA、评分算术、清单和复现证据；不看图、不启动 Blender，也不能替代视觉自评。机械字段只读 `planning/art/CODEX_STATIC_MAP_QUALITY_HOOK_20261029.md`。
- Blender 场景须隔离重开并复现正式图。源、参考、最终图和报告绑定 SHA；不得覆盖冻结候选或清除唯一证据。
- 旧的密植/稀疏植被规则、树冠/草池返修工作单、独立终审流程和 gate v1/v2 均为历史内容，不能用于当前候选。
- 完整游戏工具 `tools/art_harness.py`、`tools/producer_review.py`、Q01–Q09、47 项检查、`workflow.py summary --write` 不属于当前静态地图任务，不要运行。
- 旧 `style.json`、`regions.json`、`target_layout_v04.json` 和未校准旧视觉脚本不能判通过或失败。CW-8/CW-9 只作地图数据/Harness 结构研究。

## 项目 Hook 与空间

`.codex/hooks.json` 的质量 hook 只作用于本项目内、当前会话明确启动 P1 静态图任务并已 armed 的情况；不改用户级 Codex 配置。Hook 未生效时手动运行项目 gate。失败时同一制作模型继续修源并重评；独立审稿不是阻塞条件。只有真实外部依赖阻断且具备完整替代尝试证据时才能如实标记 `blocked_external`。

本任务的 P1 Art Harness 是“任务规范 + 项目/会话 Hook + 制作模型/Blender 执行 + 制品哈希登记 + 检查器 + 失败反馈 + 经验沉淀”的闭环；当前只有 Hook 和机械 Gate 部分自动化，Blender 运行、视觉判断、根因修复、知识回写仍由制作模型负责。它不是 `tools/art_harness.py` 的完整游戏流程，详见 `planning/art/P1_ART_HARNESS_ARCHITECTURE_20261102.md`。

项目空间上限 15 GiB、12 GiB 预警；按工作流预检容量。清理只限维护工具 dry-run 明确许可的可重建缓存。

通用可迁移制作方法见 `knowledge/REUSABLE_MAP_ART_PIPELINE.md`。P1 的参考、相机、锚点、无植被改编和评分不可直接迁移到其他地图。
