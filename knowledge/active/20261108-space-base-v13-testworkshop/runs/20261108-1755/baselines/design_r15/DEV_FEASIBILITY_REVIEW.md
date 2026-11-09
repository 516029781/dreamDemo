# 开发可行性复核（design_r15）

- 状态：**confirmed**（N4 通过，可进入 N5）
- 复核人：制作模型（本 run）
- 日期：2026-11-08 17:55

## 1. 能力核对

| 需求 | 现有能力 | 结论 |
|---|---|---|
| 南端重建（S-01…S-12） | `dock_box` / `dock_world` / `add_cyl_h` / `add_prism` 已在 v12 中验证 | 可直接实现 |
| 折线防爆墙 | `add_box_local` + `dock_world` 逐段旋转 | 可直接实现 |
| 墙脚水渍（M8o） | 材质层渐变节点，v12 已有 `_tex_mix` 范式 | 可直接实现 |
| 去对称 R1–R5 | 固定 seed `random.Random(20261108)` | 可直接实现 |
| E11–E14 计算 | 需新建 `tools/check_v13_organic.py` | 本 run 新建 |
| 隔离复现 content SHA | v11 `repro_v11_render.py` 已验证口径 | 复用方法 |
| 自动视觉评分 | 未实现（业务包 `capabilities_not_implemented`） | TV13-10 由人工承担，标 `diagnostic_only` |

## 2. 风险

1. **Q2 未决**：S1 判据与色板数学冲突。本轮不降低地面亮度，避免触发；若 TV13-09 的 S1 失败，须回 N2 决策，不得事后放宽阈值。
2. **画幅**：南端半岛 96×60 m，`dock` 坐标系与桥 B 已冻结；S-构件必须落在 u 0..96 / v ±30 内。
3. **旧门禁未回归**：v12 未跑门禁，v13 的 TV13-09 是第一次全量检查，可能暴露历史遗留失败。
4. **薄贴片不受光**：v12 DEVLOG 已记录，所有地面实体板 >=0.14 m。

## 3. 默认假设（brief §5）

Q1 降级 / Q2 暂不改门禁 / Q3 解禁 / Q4 关闭 / Q5 不加发射区。
均写进 brief，不阻塞开发；Q2 留到 TV13-09 前决策。

## 4. 开工前摘要（START_HERE §6）

- business_id `space_base_minigame`；deliverable_type `static_map`；task_mode `production`；阶段 N5。
- 权威：方案 v2.0 `cc4217ed7da00f1c…`、Brief `1d135f2132e88fa1…`、HARNESS_SPEC r14 `f30b5609d2b73474…`、
  HARNESS_LIFECYCLE `5a87406ed0ed017d…`。
- 覆盖决定：D1 南端改水平试车间、D4 不做屋顶、D5 M8o 解禁、E9 降权；其余 inherit。
- blocking 冲突：**无**（Q2 为待决策项，非阻塞；已用默认假设绕过）。
