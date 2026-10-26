# P08 独立规则评审请求

状态：**waiting_review**（制作侧未自签）。请独立审核者实际阅读代码/夹具并运行命令，然后填写
`delivery/next_cycle/T0/independent_rule_review.json`（可复制本目录模板）。

## 审什么

- P02–P07 实际实现与测试：`delivery/next_cycle/T0/gate_regression.json`、`delivery/next_cycle/T0/p02..p06` 自检、`tools/test_art_harness.py`。
- F01–F08 修复证据；阈值未降低；旧包仍可审计；vNext 1.4.0-draft **未生效**；制作方无自签。
- 重点：前序证书实际依赖、冻结载荷恢复、迁移 schema/失败状态、Q/绑定、真实 canvas、构建失败传播、回归反例。

## 必须实跑

```powershell
$py='C:\Users\tt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py -X utf8 tools/test_art_harness.py -v
& $py -X utf8 delivery/next_cycle/T0/run_gate_regression.py
& $py -X utf8 tools/producer_review.py check --review delivery/next_cycle/T4/producer_self_review.json --out delivery/next_cycle/T4/producer_submission_check.json
& $py -X utf8 tools/art_harness.py verify --manifest art_review/submissions/candidate_full/manifest.json
```

- 期望：52 tests + 5 selfchecks exit 0；producer_check `ready_for_final_review=true`；manifest `mechanical_checks=pass`、`status=needs_review`（尚无独立 review）。
- 通过后输出 `independent_rule_review.json`，`reviewer.mode=independent`，并进入 V08；不通过则列出具体缺陷并重开 P02–P07。

## 证据包

- `delivery/P08_review_pack_20261025.zip`
- `delivery/next_cycle/T0/P08_precondition_check.json`
- `art_review/submissions/candidate_full/manifest.json` + `delivery/next_cycle/T4/producer_self_review.json`
