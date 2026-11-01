# Harness 生命周期（通用）

- scope：`common/dev_core`
- lifecycle：`active`
- maturity：`not_applicable`（这是执行契约，不是经验）
- 适用：所有开发任务；业务包不得改写本契约

## 1. 阶段

`N0 需求 → N1 知识路由 → N2 设计+预览 → N3 用例 → N4 开发确认 → N5 原型 → N6 生产返修 → N7 最终验证 → N8 复盘`

- N0–N4 是制作前确认阶段，允许灰模/小样，不得批量生产。
- N4 只有 `confirmed` 才进入 N5；其余状态（`changes_required` / `blocked_on_user_input` / `blocked_technical`）必须写明返修或阻塞项。
- 局部返修按影响裁剪，但不得跳过 N7；证据可复用仅当其输入与依赖 SHA 未变。

## 2. 身份与隔离

- 每次运行使用 `knowledge/active/<request_id>/runs/<run_id>/`，禁止 `latest` 等可覆盖名。
- `RUN_CONTEXT.json` 绑定 project_root、session、request、run、task_mode、business_id、知识版本与候选路径。
- 一个候选的写入只允许一个运行持有；并发注册必须原子占用。
- 转交会话须显式接管并记录原会话、未完阶段与候选，不复制 armed 状态。

## 3. 证据契约（R-EVID-01 唯一正文）

- 源、候选、证据分离；候选目录不得回写设计快照。
- 每个交付绑定完整 SHA256：源、最终图、报告、复现记录。
- 同一图 SHA 变更后，旧视觉评分失效，须重跑受影响用例；交付前跑全量。
- 复现验证必须在隔离目录重开源并重渲，记录命令、退出码、耗时与结果 SHA；未留证则标 `unverified`。
- 允许降采样/降噪差异须在报告中预先声明容差；不得事后放宽。
- `not_run` / `not_applicable` / `failed` 不得写成 `pass`；`diagnostic_only` 不计 PASS。
- 结束状态只有 `target_met` 或证据完整的真实 `blocked_external`；低分或实现困难不属于外部阻塞。

## 4. 失败与返修

- 失败必须指向 `TEST-ID/rule_id → 现象 → 区域/对象 → 根因假设 → 源级修改 → 预期变化 → 重跑用例`。
- 每批一个主假设；记录 `hypothesis_id`、方法、前后 SHA、固定条件、预期与实际（improved/unchanged/worse）。
- 同一问题同一方法连续两次无改善 → 换方法；两种实质不同方法各两次无改善 → `design_recheck_required`，返回 N2/N3 并在同任务内完成。
- 用户停止指令优先于质量门禁；不得用门禁覆盖停止请求。

## 5. 与业务包的关系

业务包提供 WHAT（目标、参考、评分、检查集），本文件提供 HOW（生命周期、证据、结束条件）。
业务包可指定检查集，但不得改写本文件的身份隔离与结束状态契约。
