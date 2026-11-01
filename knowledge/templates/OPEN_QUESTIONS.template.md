# 待确认问题：<产品/地图名称>

只维护问题与决定指针；决定正文写入同目录 `DECISION_LOG.md`，避免两处保存不同答案。

| Q-ID | 问题 | 为什么影响结果 | 可选答案 | 推荐默认 | 选错的返工影响 | 负责人 | blocking | 状态 |
|---|---|---|---|---|---|---|---|---|
| Q-01 |  |  | A / B | A |  | 用户 / 开发者 | 是/否 | open |

## 状态取值

`open` → `answered`（转 DECISION_LOG）或 `deferred`（记录默认假设与适用范围）。

## 冻结规则

- 任一 `blocking` 未 answered：Brief 不得标 `frozen`，N4 不得 `confirmed`。
- `non_blocking` 可用标注过的默认假设推进，但须在 Brief 覆盖声明中记录。
- 已 answered 的问题保留 Q-ID，不删除；决定正文只在 DECISION_LOG。
