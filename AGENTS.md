# 鼠鼠项目执行规则（通用）

本文件只保留**跨业务**执行约束。产品画风、参考图、评分与专属门槛在 `knowledge/business/<id>/`。

## 1. 任务范围与路由

- 项目承载多个业务：当前有 P1 秋日庭院静态地图（`p1_autumn_static`）、Arknights 地图参数研究数据包
  （`research_arknights_mapdata`）与航天基地静态地图（`space_base_minigame`，规划/制作中）。新需求按根 `START_HERE.md` 路由。
- 不得把某个业务的参考图、色板、相机、评分或禁用项当作其他业务的默认规则。
- 完整游戏阶段（角色/UI/玩法/Cocos/微信/发布审核）仍暂停；恢复需用户明确启动并重新读取当时有效入口。

## 2. 通用制作约束

- 新产品新建独立场景与输出目录；固定参考、相机与验收目标后再绘制细节。
- 交付可编辑源 + 产物；导出图不得替代源。最终图须由可编辑源重开渲染。
- 使用 AI 辅助草稿/贴图时保留原始结果、编辑文件与来源记录；AI 直出整图不得当作最终交付。
- 渲染/导出/工具运行须记录命令、退出码、耗时与 SHA；未记录的执行不得声称“已验证”。
- 不把密钥写入工程或日志。

## 3. 证据与验证（摘要）

完整契约见 `knowledge/common/dev_core/HARNESS_LIFECYCLE.md`：

- 源/候选/证据分离；完整 SHA；图变即视觉证据失效。
- 复现须在隔离目录重开重渲并留证；未留证标 `unverified`。
- `not_run`/`not_applicable`/`failed` 不得写成 `pass`；`diagnostic_only` 不计 PASS。
- 结束状态只有 `target_met` 或证据完整的真实 `blocked_external`。

## 4. 版本、磁盘与仓库

- Git 只提交代码、配置和小型规范；本地源、图片、模型和证据保留在磁盘并登记 manifest，不因未跟踪而删除。
- 项目目录（含 `.git` 与工具）≤15 GiB，12 GiB 预警；清理先 dry-run，保护当前源、正式证据与冻结候选。
- 旧文档、旧阈值、旧参考未经审计不得回到活动入口；归档以 `planning/art/ART_DOCUMENTATION_ARCHIVE_INDEX_20261029.md` 为准。

## 5. 门禁与自动化现状

- 目前只有 **P1 专属**的会话 Hook 与机械 gate（见 P1 业务包与
  `planning/art/CODEX_STATIC_MAP_QUALITY_HOOK_20261029.md`）；它不是跨业务路由器，也不读取图像。
- 跨业务知识路由、自动 Blender 执行、自动视觉判断尚未实现；缺匹配检查器时在任务内用手工检查，并报告能力缺口。
- 不改用户级全局配置；项目 Hook 只在当前仓库、用户明确启动对应制作任务时生效。

## 6. 冲突优先级

用户本轮明确要求 > 本次 Brief 覆盖决定 > 已启用业务包 > 已批准 `ART_STYLE_BASE` >
`reusable` 案例 > `observed/proposed` 经验。冲突须记录 `conflict → decision → source`。
