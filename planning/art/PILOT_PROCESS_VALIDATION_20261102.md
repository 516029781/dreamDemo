# 流程验证报告（pilot_simple_map）

- 日期：2026-11-02 07:00–07:25
- 指令：用户 06:58「你做一个简单的图 验证一下流程吧」
- 性质：**机制验证**，不是美术交付；不评价画面好坏，只回答"流程能不能跑、卡在哪"
- 结论：N0–N8 全部有产物可查，6 条用例 5 pass + 1 pass_visual；**发现 7 处模板/契约缺陷，其中 4 处已在本轮修好**

## 1. 实际跑出来的路径

| 阶段 | 做了什么 | 产物 |
|---|---|---|
| N0 需求 | 写 Brief（6 条 REQ）+ 待确认 4 条 | `knowledge/active/20261102-pilot-simple-map/REQUIREMENTS_BRIEF.md` |
| N1 路由 | 判定 `new_business_bootstrap`，排除 P1 与数据研究包 | `RESOLVED_KNOWLEDGE.json` |
| N2 设计 | 机位/10 物件坐标/材质/渲染参数 + 5 版灰模迭代 | `runs/…/baselines/design_r01/DESIGN_PREVIEW_PACK/blockout.png` |
| N3 用例 | 6 条用例，容差事前声明 | `knowledge/business/pilot_simple_map/test_cases.json` |
| N4 确认 | status=confirmed（依据用户原话） | `DEV_FEASIBILITY_REVIEW.md` |
| N5 原型 | 960×540 / 64 spp / 20 s | `art/static_map/pilot_simple_map/v01/renders/final.png` |
| N6 返修 | 未触发（预算 2 轮未用） | — |
| N7 验证 | 6 条用例 + 隔离重开重渲 | `runs/20261102-0710/evidence/*`、`reproduction.json` |
| N8 复盘 | 本文件 | — |

时间分布：文档 ~8 min，场景与 5 版预览 ~7 min，终图 20 s，复现 19 s，检查与证据 ~5 min。

## 2. 发现（按严重度）

### F1 模板里的 `command` 是占位符，不填就跑不了 —— 已修
`HARNESS_SPEC.template.json` 写着 `<gate script>` / `<isolated reopen script>`。
落到业务包时必须替换成真实命令，否则 harness 只是一份读起来像契约的文本。
- 本轮：`knowledge/business/pilot_simple_map/HARNESS_SPEC.json` 已改为实际脚本路径。
- 建议：模板加行内提示"落包前必须替换尖括号占位"，并加一条机械检查（出现 `<...>` 即 fail）。

### F2 没有"实验/pilot"这一类业务 —— 部分绕过
`manifest.routing_rules` 只有 selected / no_match / multi_business。本次靠 `no_match` 兜底，
但 pilot 与"真实新业务"是两种东西（前者允许低完成度、允许一次性的验证目标）。
- 建议：`routing_rules` 增 `pilot` 类别，或在 business 条目里用 `lifecycle: pilot` 显式标记
  （本轮已用后者，route 校验仍 10/10 通过）。

### F3 设计基线该放哪里，文档自相矛盾 —— 已修
`active/README.md` 说 `baselines/design_rNN/`，我第一版把预览放进了 `evidence/DESIGN_SNAPSHOT/`，
`RUN_CONTEXT.design_baseline` 也跟着错。改回 `runs/<run_id>/baselines/design_r01/` 并生成
`BASELINE_MANIFEST.json`（status=frozen）。
- 建议：`RUN_CONTEXT.template.json` 的 `design_baseline.path` 直接写成完整示例路径，
  别再让执行者猜。

### F4 PNG 文件 SHA 不可复现（本轮最重要的发现）—— 契约已更新
同一场景两次渲染：**像素完全一致（max channel diff 0、RMS 0.0、pixel SHA 相同），
但 PNG 文件 SHA 不同**。差异来自 Blender 写进 PNG 的 `File / Date / RenderTime / cycles.*` 文本块。
如果证据契约要求"文件 SHA 一致"，复现检查会永远失败。
- 本轮处理：契约改为以 `pixel_sha256`（对 raw RGB 做 SHA）为判定，file SHA 仅作参考；
  记录在 `reproduction.json` 与 `MANIFEST.json` 的 note 里。
- 备选（已实测可行但不采用）：`tools/normalize_render.py` 去掉元数据后两份文件同为
  `7c1f3b31…`，但会丢 sRGB/gamma 色块，不适合交付图。
- 已落地：`knowledge/common/dev_core/HARNESS_LIFECYCLE.md` §3 已把"绑定 SHA"拆成
  **content SHA（像素）** 与 **container SHA（文件）**，并写入本轮实测数据。

### F5 新业务没有可用的机械 gate —— 已补一个业务专属检查器
`tools/static_map_quality_gate.py` 的参考 SHA、六维权重、8 条硬门槛全部写死为 P1，
对新业务零语义。本轮新建 `tools/pilot_simple_map_check.py`（尺寸 / 明度 / 文档闭环三项）。
- 局限：它是业务专属的，不是通用检查器。
- 建议：抽一个 `tools/check_common.py`（尺寸、SHA 绑定、证据路径存在、诊断项不得计入 PASS），
  业务专属检查只补充业务语义。

### F6 `manifest.json` 的 P1 `optional_docs` 有重复项 —— 已修
同一路径 `STATIC_ART_INFORMATION_CORRECTION_20261101.md` 出现两次，已去重。

### F7 N4 的 "confirmed" 没有记录"谁确认" —— 已修（模板已加字段）
本轮在 `DEV_FEASIBILITY_REVIEW.md` 写明"依据用户 06:58 原话"，但模板没有
`confirmed_by` / `confirmed_basis` 字段，容易被后来者误读成"模型自作主张批准"。
- 已落地：`DEV_FEASIBILITY_REVIEW.template.md` 增 `confirmed_by` / `confirmed_basis` 两字段；
  本轮 N4 文档已按新字段填写（user + 用户原话）。

## 3. 顺带验证成立的既有经验

- **sun 必须用四元数**（`rotation_quaternion = dir.to_track_quat('-Z','Y')`）：重开后实测
  `rot_mode=QUATERNION`，三处投影同向，无第二方向硬影。
- **高机位俯视小场景，背景不要堆远景体块**：3 种做法（方块带 / 扁球山 / 山脊）全部读作悬浮暗块，
  最终用"地面按相机距离雾化"才成立。已写入 `STYLE_PROFILE.md`。
- **无外部依赖的打包是可行的**：重开日志 `external libraries []`、`images []`，
  自建几何 + 节点材质的场景确实能自包含。

## 4. 没有验证到的（不要当成已验证）

- Hook 自动化、跨业务路由自动化、自动视觉评分：本轮全程人工触发。
- 复杂场景（植被、贴图、多光源、夜景）下的同源复现：只测了 13 个基础体的单帧。
- 真实用户验收：仅一次用户口头指令，无第二轮确认。
- `maturity` 最高只能给 `observed`。

## 5. 交付物索引

| 类型 | 路径 |
|---|---|
| 业务包 | `knowledge/business/pilot_simple_map/`（PROFILE / STYLE / HARNESS_SPEC / test_cases / scorecard / START_HERE） |
| 运行记录 | `knowledge/active/20261102-pilot-simple-map/`（Brief / Design / DevReview / RUN_CONTEXT / RESOLVED / TRACEABILITY / runs） |
| 候选 | `art/static_map/pilot_simple_map/v01/`（scene.blend / final.png / MANIFEST / DELIVERY / REVIEW / 三个脚本） |
| 新工具 | `tools/pilot_simple_map_check.py`、`tools/normalize_render.py` |
| 关键证据 | `runs/20261102-0710/reproduction.json`（pixel SHA 一致、file SHA 不一致的实测记录） |

## 6. 建议的下一步（按性价比）

1. ~~F4 SHA 拆分入契约~~ 已完成。
2. ~~F7 confirmed_by 字段~~ 已完成。
3. 抽 `tools/check_common.py`（F5）——目前检查器仍是业务专属。
4. `routing_rules` 增 pilot 类别（F2）——现在靠 `lifecycle: pilot` 兜底，能跑但语义不清。
5. 之后再谈 Hook 自动化：机械检查集还没抽通用，接 Hook 只会把人工判断固化成脚本 bug。
