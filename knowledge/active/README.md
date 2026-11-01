# 活动运行（active）

每次任务在此建立独立运行目录；禁止 `latest` 等可覆盖名。

```text
active/<request_id>/runs/<run_id>/
├─ RUN_CONTEXT.json        # 项目/会话/需求/运行/模式/业务/候选绑定
├─ RESOLVED_KNOWLEDGE.json # 本轮加载的知识与 SHA、覆盖决定
├─ evidence/               # 各 TEST-ID 的证据
└─ baselines/design_rNN/   # 不可变设计快照（含 BASELINE_MANIFEST.json）
```

## 规则

- 一个候选的写入只允许一个运行持有；并发需原子占用。
- 转交会话须显式接管，记录原会话、未完阶段与候选；不复制 armed 状态。
- 运行结束不删除；清理须按保留清单核对 SHA。
- 模板：`knowledge/templates/RUN_CONTEXT.template.json`、`RESOLVED_KNOWLEDGE.template.json`、
  `BASELINE_MANIFEST.template.json`。

## 校验样例

`active/_validation/` 下为 P0-5 的三条人工路由样例（P1 制作 / 新业务 / 纯讨论），
仅作契约校验，不是真实运行。
