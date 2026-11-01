# 需求 Brief：<产品/地图名称>

- request_id：`<YYYYMMDD-slug>`（对应 knowledge/active/<request_id>/）
- business_id：`<p1_autumn_static | <new_id> | none>`
- deliverable_type：`<静态地图 | 可行走地图 | UI | 角色/道具 | 其他>`
- 平台 / 画幅 / 展示条件：`<...>`
- 需求来源：用户原话摘要 + 日期
- 状态：`draft` / `frozen`

## 1. 目标与不可变约束

- 目标（一句话，可验收）：
- 必须出现：
- 禁止出现：
- 明确不做：
- 覆盖声明（对业务包/基线条款）：`inherit` / `override` / `not_applicable`，逐条列出

## 2. 参考（按角色区分）

| 角色 | 路径 | 来源 | SHA256 | 用途 | 许可边界 |
|---|---|---|---|---|---|
| visual_reference |  |  |  |  |  |
| structural_reference |  |  |  |  |  |
| tooling_reference |  |  |  |  |  |

无视觉参考时写“原创方向”，并说明为何不需要参考图；不得从相邻业务包借用画风。

## 3. 验收要求（每条分配 REQ-ID）

| REQ-ID | 要求 | 优先级 | 验收方法 | 预期 TEST-ID | 证据 |
|---|---|---|---|---|---|
| REQ-01 |  | must |  | TEST-01 |  |

## 4. 约束与预算

- 时间 / 性能 / 磁盘：
- 迭代上限或停止条件：

## 5. 冲突与决定

| 冲突 | 涉及规则 | 决定 | 依据（用户指令/业务包/基线） | 记录位置 |
|---|---|---|---|---|

## 6. 待确认

见 `OPEN_QUESTIONS.md`；blocking 项未解决时 Brief 不得冻结。

## 7. 追踪

`REQUIREMENTS_TRACEABILITY.json` 与本 Brief 同目录，TEST-ID 在 N3 生成后必须闭合。
