# 开发可行性确认（N4）：航天基地静态地图（space_base_minigame）

- 确认人/模型：Qoder（制作侧）
- 确认来源 confirmed_by：`user`
- 确认依据 confirmed_basis：用户 2026-11-02 消息「开始吧」，接受
  `planning/art/SPACE_BASE_EXECUTION_PLAN_20261102.md` 的一次性范围与默认条件
- 时间：2026-11-02
- 状态：`confirmed`

> 本确认只覆盖静态图 + 可编辑源 + W1/W2 预检；A1/W3/W4 外置。

## 1. 绑定（版本 + SHA）

| 项 | 路径 | 版本 | SHA256 |
|---|---|---|---|
| 需求 Brief | `knowledge/active/20261102-space-base-map/REQUIREMENTS_BRIEF.md` | r01 | `7604194b…` |
| 已选知识 | `knowledge/active/20261102-space-base-map/RESOLVED_KNOWLEDGE.json` | r01 | 写入后重算 |
| 方案设计 | `knowledge/active/20261102-space-base-map/SOLUTION_DESIGN.md` | r01 | `0cc61d90…` |
| 设计快照 | `runs/20261102-1314/baselines/design_r01/` | design_r01 | 见 BASELINE_MANIFEST |
| 测试用例 | `knowledge/active/20261102-space-base-map/test_cases.json` | r01 | `b4854ecd…` |
| 检查集 | `knowledge/business/space_base_minigame/HARNESS_SPEC.json` | r01 | `c4f8ac30…` |
| 设计主口径 | `planning/art/SPACE_BASE_MASTER_SPEC_20261102.md` | v1.3 | `4e0e2222…` |

## 2. 逐项检查

| 检查项 | 结论 | 说明/证据 |
|---|---|---|
| 需求是否遗漏或矛盾 | pass | 20 条 REQ 覆盖 spec §9.7；A1/W3/W4 明确 external |
| 业务知识包是否选对 | pass | 新建 `space_base_minigame`；排除 P1/Arknights/pilot |
| 预览能否表达目标效果 | pass（有限） | 预览 = spec §6 色板 + `_routes_v13` / `_corridor_strip` 两张图；无新风格小样，终图以 spec 为准 |
| 工具/源文件/目录是否可用 | pass | Blender 4.5.15 LTS、Cycles CPU 实测；Python 3.12 + PIL 13；`v01/` 空闲；DevTools 未装 |
| 阶段是否能按计划执行 | pass | P0–P4 连续；时间盒 P1≤4/P2≤4/P3≤3 h |
| 每条验收要求是否有可操作测试 | pass | `test_cases.json` 20/20；G/W1/W2 机械+人工；S 人工；A1/W3/W4 external |
| 返修失败时是否知道改哪里 | pass | 布局/接地→轮廓→材质→光色；`REVIEW.md` 记录对象/参数 |

## 3. 执行者挑战检查

- 最可能失败的两个假设：
  1. Cycles CPU 在 3840×5120/32–64 spp 的实际时间超出时间盒；
  2. 只建 7 识别点 + 关键件时，G2/S4/S7 的读图仍不足。
- 反证方式：P1 先渲 1920×2560 灰盒记时间；P2 先渲 1920×2560 组合图，逐条对照
  S1–S7 与 7 识别点；若时间超，降 samples/分辨率或换 Eevee；若读图不足，只补识别点相关件。
- 若失败，最先改的对象/材质/灯光层：墙/门位与接地 → 识别点体块比例 → 材质色相/明度 → 太阳/补光。

## 4. 遗留风险与条件

- 遗留风险：
  1. W3/W4 无真机/DevTools，只能 external；
  2. A1 无角色层，只能 external；
  3. 62 类 L1/180 L2 不逐件建，非识别件可能被省略/贴图化；
  4. 8 px/m 已冻结，改则全图重算；
  5. P1 机械 gate 不适用，本业务靠人工自评 + 本业务 checker。
- 需要用户决定的事项：无（默认已确认）；若要改比例/运行时/全量 62 类，需重开 N2/N4。
- 技术阻塞与已尝试替代：无当前阻塞；DevTools 未装，W3/W4 记录 external。

## 5. 确认失效边界

N5/N6 的建模细化、采样提高、容差内材质调整不使本确认失效；
更换参考、改变布局/机位/比例/验收条件、把 A1/W3/W4 纳入本轮，须返回 N2/N3 并新建 design_rNN。
