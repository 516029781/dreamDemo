# 美术风格系统迁移 · P0-1..P0-5 执行报告

日期：2026-11-02
依据：`planning/art/ART_STYLE_SYSTEM_AND_NEW_PRODUCT_ONBOARDING_PLAN_20261102.md`（r2）§7
范围：流程与知识库落地。**未制作地图、未渲染、未覆盖候选、未修改用户全局配置。**

## 1. P0-1 审计结果

- 审计文件：27 份（活动入口、通用规范、知识库、P1 依赖、skills、Hook/Gate、迁移方案）
- 规则条款：9 条（R-VEG、R-BLIND、R-85、R-P1-PARAM、R-EVID、R-DISK、R-HOOK、R-KNOW、R-ARTBASE）
- 审计清单：`planning/art/KNOWLEDGE_AUDIT_20261102.json`
  （每条含 path/sha256/scope/lifecycle/maturity/rule_ids/duplicate_of/conflicts_with/
  canonical_source/decision/replacement/evidence/references_updated）

### 关键裁决

| 规则 | 冲突 | 裁决 |
|---|---|---|
| R-VEG-01 植被政策 | 2026-11-01 21:00 手绘植被（V26/V27）vs 23:19–23:23 记录“整图无植物” | **以更晚记录为准：P1 当前为无植被设备化改编**；手绘方向标 `superseded`；V27 树草为中间产物 |
| R-BLIND-01 双独立盲评 | MODEL_EXECUTION_GUIDE 要求两份盲评 ≥85 vs 用户“不需要独立终审” | 盲评要求标 `superseded`；改为制作侧自评+反证+机械 gate |
| R-85-01 85 分门槛 | 被通用文件复述，存在范围泄漏 | 收归 P1 scorecard；通用层不写阈值 |
| R-P1-PARAM-01 P1 参数 | 参考 SHA/相机/锚点出现在根入口与通用层 | 移入 P1 references/STYLE_PROFILE，根入口只留路由 |
| R-HOOK-01 P1 Hook | 易被当作跨业务能力 | 明确为 P1 专属，通用层只写现状与边界 |
| R-ARTBASE-01 美术基线 | 未经批准 | 保持 `draft`，可研究不可作门槛 |

## 2. P0-2 入口修订（已切换，备份可回滚）

| 文件 | 变更 |
|---|---|
| `START_HERE.md` | 改为跨业务路由：必读顺序、按 business_id 选包、冲突优先级、过期识别、开工摘要 |
| `AGENTS.md` | 只留跨业务约束；P1 专属（无植被、85、hook、参考）移入业务包 |
| `MODEL_EXECUTION_GUIDE.md` | 明确为 P1 专属；G3 的“两份独立盲评”改为制作侧自评+机械 gate |
| `knowledge/README.md` | 两层结构与状态契约（scope/lifecycle/maturity）、按需加载、维护规则 |
| `knowledge/STANDARDS.md` | 改为重定向，通用速查移至 `common/dev_core/STANDARDS.md` |
| `knowledge/RECIPES.md` | 改为指针页，不保存步骤与阈值 |

回滚：`planning/art/migration_20261102/rollback_r0/`（6 份原文件 + `ROLLBACK_MANIFEST.json` 含 SHA），
按清单相对路径复制回根目录即可恢复。

## 3. P0-3 模板（13 份）

`knowledge/templates/`：REQUIREMENTS_BRIEF、OPEN_QUESTIONS、SOLUTION_DESIGN、TEST_PLAN、
TEST_CASES.json、DEV_FEASIBILITY_REVIEW、STYLE_PROFILE、ACTIVE_PRODUCT.json、HARNESS_SPEC.json、
ASSET_MANIFEST.json、RUN_CONTEXT.json、RESOLVED_KNOWLEDGE.json、BASELINE_MANIFEST.json

要点：N4 状态四值固定；design_rNN 快照不可原地改；每条 REQ 必须有用例；未校准指标 `diagnostic_only`。

## 4. P0-4 知识包落地

```text
knowledge/
├─ README.md                         # 路由入口
├─ common/dev_core/{HARNESS_LIFECYCLE.md, STANDARDS.md, lessons/README.md}
├─ common/methods/map_art/README.md  # 指向 REUSABLE_MAP_ART_PIPELINE（物理迁移延后）
├─ common/art_base/ART_STYLE_BASE.md # draft，未批准
├─ common/assets/ASSET_LIBRARY.md
├─ business/manifest.json            # p1_autumn_static r03 + research_arknights_mapdata r01
├─ business/p1_autumn_static/{START_HERE, BUSINESS_PROFILE, STYLE_PROFILE,
│                             DRAWING_PLAYBOOK, scorecard.json, test_cases.json,
│                             references.manifest.json}
├─ cases/README.md                   # 明确没有成功案例
├─ templates/                        # 13 份
└─ active/README.md + _validation/   # 三条路由样例
```

P1 包内容要点：

- 参考事实 / 本项目做法 / 未知事实 / 被取代方向 四者分开；不把计划勾选当成功案例
- `scorecard.json` r03：六维 20/20/20/15/15/10、≥85、各维 ≥3、八项硬门槛（含 `no_vegetation`）
  与机械 gate 一致；明确 gate 不读图、不证明评审独立性
- `test_cases.json` r02：文件/绑定/无植被/设备替代/明暗/评分 6 项 + 1 项仅诊断的色彩统计

## 5. P0-5 手动路由校验（10/10 通过）

证据：`planning/art/migration_20261102/P0_5_ROUTING_CHECK.json`；样例在
`knowledge/active/_validation/{p1_production,new_business,planning_only}/`。

| 检查 | 结果 |
|---|---|
| C1 所有加载路径存在且 SHA 相符 | pass |
| C2 P1 样例不加载研究数据包 | pass |
| C3 新业务样例不加载任何 P1 视觉文档 | pass |
| C4 美术基线保持 draft 且仅作信息 | pass |
| C5 纯讨论无候选、无生产门禁 | pass |
| C6 业务注册表 ID 唯一且含 P1 | pass |
| C7 评分卡权重合计 100、门槛 85/3 | pass |
| C8 13 份模板齐全 | pass |
| C9 入口草案引用均存在 | pass |
| C10 审计条目字段完整 | pass |

## 6. 执行中发现的二次冲突（已处理）

制作过程中发现 `ACTIVE_STATIC_ART.json`（23:23）与工作单（23:20）已把方向改回**整图无植被**，
与当日下午的手绘植被实现相反。处理：

1. 以更晚记录为权威，P1 业务包从 r02 改为 **r03 无植被**；
2. 评分卡恢复 `no_vegetation` 与 `left_area_functional_replacement` 硬门槛；
3. P1 标准勘误段改为“无植被条款继续有效”，并注明 21:00 手绘为中间尝试；
4. L-ART-06 恢复为当前用户偏好；
5. 审计 R-VEG-01 裁决改为 `keep_active_latest_wins`。

教训：并行会话可能在任务中途改写入口文件，**开工与交付前都必须重算 SHA 并复核口径**。

## 7. 未完成（明确保留）

| 项 | 状态 | 说明 |
|---|---|---|
| P0-6 项目美术基线批准 | 未开始 | `ART_STYLE_BASE.md` 保持 draft，需用户逐条确认 |
| P1-1 真实新业务试点 | 未开始 | 需选一个真实新需求手动跑 N0–N8 |
| P1-2 路由/Harness 适配 | 未开始 | Hook 隔离/并发样例仍为**待实测**，不得声称已验证 |
| I3 遮罩/ROI 校准 | 未完成 | 全图色彩统计继续 `diagnostic_only` |
| 源—图同源复现 | 未验证 | V27 无归档隔离复现证据 |
| 评分卡与 gate 同步 | 已对齐 r03 | 但 gate 尚未做跨业务适配与测试 |
| `REUSABLE_MAP_ART_PIPELINE.md` 物理迁移 | 延后 | 先做索引，避免断链与双正文 |

## 8. 交接

1. 任何新任务先读根 `START_HERE.md`，按 `deliverable_type` + `business_id` 进入业务包。
2. P1 下一步按 `P1_WORKORDER_20261101_NEXT.md` 的 P1-A/B/C 执行；新候选用未占用目录，不覆盖 `v25/`。
3. 需要回滚文档入口时，复制 `rollback_r0/` 内 6 个文件回原路径即可（不影响候选与证据）。
4. 知识变更须先在 `KNOWLEDGE_AUDIT_20261102.json` 增加/更新条目，再改正文。
