# ERRATA — v02 active request (baseline 勘误)

`runs/20261102-1907/baselines/design_r02/` 已冻结，不在原地改写。以下为继承 v01 文本时留下的过期路径/数值，均不影响 v02 的布局、相机或验收口径。

| ID | 位置 | 过期内容 | 实际口径 |
|---|---|---|---|
| E1 | `REQUIREMENTS_BRIEF.md` §5 交付 | 指向 `v01/...` 与 `runs/20261102-1314/` | v02 候选 `art/static_map/space_base_minigame/v02/`；run `20261102-1907`，见 `RUN_CONTEXT.json` |
| E2 | `SOLUTION_DESIGN.md` §1 相机 | Euler `(55°,0,180°)`、location `(120,813.86,573.6)` | 由 `CONFLICTS_AND_DECISIONS.md` C1 取代：Euler `(35°,0,180°)`、location `(120,568.23,819.2)`；camera_check 实测 max 0.432 px |
| E3 | `SOLUTION_DESIGN.md` §2 候选 | 写 `.../v01/` | v02 候选 `.../v02/`；v01 只读作为上游 |
| E4 | `test_cases.json` G/S 用例 `input.files` | 指向 v01 图/源 | 作为 v01 布局回归对照保留；v02 证据写入 `runs/20261102-1907/evidence/`，D1–D5 见 `evidence/D*` |

处理：以本 ERRATA + `RUN_CONTEXT.json` 为准；不重开 baseline，不改验收数值。
