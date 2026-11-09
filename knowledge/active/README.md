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

## 真实运行样例

`active/20261102-pilot-simple-map/` 是第一次按本契约跑完 N0–N8 的运行（pilot_simple_map 业务）。
它验证了 `baselines/design_rNN/` 的用法，也暴露了 container SHA 不可复现的问题；
复盘见 `planning/art/PILOT_PROCESS_VALIDATION_20261102.md`。

## 当前运行

- `active/20261102-space-base-map/` — 航天基地静态地图 v01 验收运行
  （business_id `space_base_minigame`，run `20261102-1314`，已交付，保留只读）。
- `active/20261102-space-base-detail/` — v02 L2/L3 细节追加与运行时冒烟
  （business_id `space_base_minigame`，run `20261102-1907`，候选 `art/static_map/space_base_minigame/v02/`）。
