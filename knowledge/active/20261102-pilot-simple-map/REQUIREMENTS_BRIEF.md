# 需求 Brief：流程验证用小场景（pilot_simple_map）

- request_id：`20261102-pilot-simple-map`
- business_id：`pilot_simple_map`（新建，走 new_business_bootstrap；非 P1）
- deliverable_type：`静态地图`（单帧 16:9 展示图，非可玩关卡）
- 平台 / 画幅 / 展示条件：PC 查看器，1920×1080 内展示；出图 960×540，sRGB 显示
- 需求来源：用户 2026-11-02 06:58「你做一个简单的图 验证一下流程吧」
- 状态：`frozen`

> 本单不是美术交付，是**机制验证**：用最小可完成场景把 N0→N8 与证据契约实跑一遍，
> 找出模板、路由、gate 在真实执行里卡住的环节。因此"简单"是硬约束，不是偷懒。

## 1. 目标与不可变约束

- 目标（一句话，可验收）：产出一张 960×540 的静态场景图，并留下**可复现**的 SHA 证据链，
  使 N0–N8 每个阶段都有对应文件可查。
- 必须出现：石台、正面三级台阶、左侧矮墙、右侧两只木箱+一个金属桶、一根灯柱、后景剪影带。
- 禁止出现：任何植物（树/草/花/灌木/裸土）；P1 参考图及其色板；写入 P1 候选目录。
- 明确不做：角色、动画、UI、手绘贴图、多机位、可玩性。
- 覆盖声明（对业务包/基线条款）：
  - `p1_autumn_static` 业务包：`not_applicable`（本单是新业务，不继承其评分卡与硬门槛）
  - `common/art_base/ART_STYLE_BASE.md`：`inherit`（仅 draft 基线，不构成批准）
  - `common/dev_core/HARNESS_LIFECYCLE.md`：`inherit`（生命周期与证据契约不可改写）

## 2. 参考

| 角色 | 路径 | 来源 | SHA256 | 用途 | 许可边界 |
|---|---|---|---|---|---|
| visual_reference | — | — | — | — | 无 |
| structural_reference | — | — | — | — | 无 |
| tooling_reference | `art/static_map/p1_autumn_courtyard/v25/preflight/r1_light.py` | 本项目 | 见仓库 | 仅取 sun 四元数赋值写法 | 代码参考，不取画面 |

**原创方向声明**：本单不需要视觉参考图。理由：验证目标是流程与证据，不是风格复刻；
若引入参考图，会顺带把"参考→色板→评分"的未校准环节混进来，反而干扰判断。

## 3. 验收要求

| REQ-ID | 要求 | 优先级 | 验收方法 | 预期 TEST-ID | 证据 |
|---|---|---|---|---|---|
| REQ-01 | 单帧 16:9 图，960×540，可正常打开 | must | 读图尺寸 | TEST-01 | runs/<run>/evidence/TEST-01 |
| REQ-02 | ≥6 个可识别功能体块，全部接地，无悬空/穿插 | must | 列对象清单 + 目视裁切 | TEST-02 | 同上 |
| REQ-03 | 单一主光源，画面内投影方向一致 | must | 目视影子朝向 | TEST-03 | 同上 |
| REQ-04 | 材质分石/木/金属/地四族，无纯黑纯白 | must | 采样 HSV 值域 | TEST-04 | 同上 |
| REQ-05 | scene.blend 与 final.png 完整 SHA256 + 隔离重开重渲记录（容差先声明） | must | 重渲对比 RMS | TEST-05 | 同上 |
| REQ-06 | 文档链闭合：brief→design→tests→run_context→resolved 相互引用，REQ/TEST 全闭合 | must | 脚本检查 | TEST-06 | 同上 |

## 4. 约束与预算

- 时间：单次运行 ≤ 30 分钟；渲染 ≤ 3 分钟/张。
- 磁盘：试点目录 ≤ 150 MB（scene.blend 目标 < 60 MB）。
- 迭代上限：N5 之后最多 2 轮返修；同一问题同方法连续 2 次无改善即换方法（HARNESS §4）。

## 5. 冲突与决定

| 冲突 | 涉及规则 | 决定 | 依据 | 记录位置 |
|---|---|---|---|---|
| P1 零植被条款是否约束本单 | R-VEG-01（P1 业务包） | 不约束，但本单仍不画植物 | 本单 business_id 非 P1；避免借道验证 P1 政策 | 本文件 §1 |
| 是否套用 P1 的 85 分与硬门槛 | R-85-01 | 不套用 | 业务包按 business_id 隔离 | `knowledge/business/pilot_simple_map/scorecard.json` |
| N4 开发确认由谁给 | HARNESS §1 | 用户 06:58 指令视为 confirmed | 用户原话即授权做这张图 | `DEV_FEASIBILITY_REVIEW.md` |

## 6. 待确认

见 `OPEN_QUESTIONS.md`。当前无 blocking 项（Q-02 属可运行假设，已记录）。

## 7. 追踪

`REQUIREMENTS_TRACEABILITY.json` 与本 Brief 同目录；TEST-ID 已在 N3 生成后闭合。
