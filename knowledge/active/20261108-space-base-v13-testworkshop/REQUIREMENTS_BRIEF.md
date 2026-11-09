# 需求 Brief：航天基地 v13 · 水平试车间重建与去几何化

- request_id：`20261108-space-base-v13-testworkshop`
- run_id：`20261108-1755`
- business_id：`space_base_minigame`
- deliverable_type：`static_map`（静态图 + 可编辑 Blender 源）
- 平台 / 画幅：微信小游戏预渲染图；240×420 m；7 px/m；交付 1680×2478，高清 3360×5880
- 需求来源：用户 2026-11-08 17:45「最下方应该是航天基地的水平试车间，对比航天基地模型做出调整；
  整体路面比较空旷；有物品的地方过于对称和死板」；17:54「按我们的 harness 流程开始开发」
- 状态：`frozen`（N4 已确认）
- 唯一设计口径：`planning/art/SPACE_BASE_EXTERIOR_ORGANIC_PLAN_20261108.md` v2.0

## 1. 目标与不可变约束

- **目标**：最下方重建为实机「水平试车间」（露天防爆试验场）；路面按五层填充至可读密度；
  视觉摆件去掉等距矩阵与双侧镜像。
- **必须出现**：折线防爆墙（9 m，墙脚水渍）、蓝绿 ENTRANCE 门洞、Ø0.6×4 斜穿落地管道、
  3 堆错线集装箱、导流坑、局部黄线、黄框撤离点、墙上绿色小终端。
- **禁止出现**：屋面板 / 女儿墙回归 / 横跨桁架 / 采光板顶；直升机停机坪 H 圈；
  蓝色发光撤离圈；2×5 储罐矩阵；双侧镜像黄路缘；绿色战术烟雾。
- **明确不做**：发射区完整建模（Q5 默认不加）；玩法层规则；UI；室内陈设细化。
- **不可变**：画幅、7 px/m、四厅 34×34、十字过道 10、桥 B、花园 34×34、场地 +4.70、
  阶梯宽 94/74/62、`dock` 坐标系与半岛外形、`DOCK_ROTZ=20°`。

### 覆盖声明

| 条款 | 决定 | 依据 |
|---|---|---|
| `SPACE_BASE_FAN_MASTERPLAN_20261108.md` 的「南端 = 码头」 | **override** | 用户 17:45 明确 |
| `HARNESS_SPEC.json` r14 的业务检查集 | **inherit**（不回归） | 业务包 |
| `STYLE_PROFILE.md` M8「做旧只在一处」 | **override**（室外 M8o；试车间防爆墙必须做旧） | 实机 A 级观察卡 §8.4.6 |
| 旧规范 §5.11 的 170×130 尺寸 / 全局坐标 | **not_applicable**（只借构件类型） | 画幅已变（方案 D3） |
| v1.2 的 Q4「码头是否敞顶」 | **close**（整体重建后无码头） | 方案 D2 |
| `SPACE_BASE_MASTER_SPEC` §8.4.6 露天防爆场结论 | **inherit** | A 级证据 |

## 2. 参考（按角色区分）

| 角色 | 路径 | SHA256 | 用途 | 许可边界 |
|---|---|---|---|---|
| structural_reference | `reference/_df_screenshots/gamersky/01_航天基地.jpg` | `4b5ef636e55182a02c1fe62d59cc1cc7c8c43d2904a7e5d06bdaafe4cfa60dfe` | 水平试车间方位、Y 字分叉、陆地块形状 | 官方地图，仅观察，不入包 |
| visual_reference | `reference/_df_screenshots/gamersky/12_水平试车间.jpg` | `21076db950035a26a0c19369ee8251a35941042c21ffbb62fe4035afc13d880e` | 防爆墙/管道/箱堆/绿门/黄线/水渍 | 游民星空转载，仅观察 |
| visual_reference | `reference/_df_screenshots/gamersky/13_核心区.jpg` | `0ad05aea0a6ebd513f0c26f9eb46c02bc70fc6a36c324a647c4b8e9441fd7caf` | 雷达罩、立面、屋顶设备 | 同上 |
| tooling_reference | `SPACE_BASE_MASTER_SPEC_20261102.md` §5.11 / §8.4.6 | `5af3e12ac4d3130a1c571f19cd7cc89086d529690de4d8d44437f94b63efe757` | 构件类型与 A 级观察卡 | 项目自有 |
| tooling_reference | `SPACE_BASE_INTERIOR_DRESSING_20261102.md` §11 | `85d755bb83164b134f2213f56305679cd175b008dc981c09c86dea9e48c743d2` | 实机订正（露天，无桁架） | 项目自有 |
| tooling_reference | `SPACE_BASE_LAYOUT_ISSUES_20261103.md` A3/A4 | `c8f39dfc61b671deed34268c79c172d08e7bae788cba05a18a0757e2d3b6f9f3` | 东南 20° 斜置干船坞；摆件预算教训 | 项目自有 |

**参考图不进 Git、不入发布包、不二次分发**；结论只以文字与色值落到方案。

## 3. 验收要求

| REQ-ID | 要求 | 级别 | 验收方法 | TEST-ID |
|---|---|---|---|---|
| REQ-40 | 南端为露天水平试车间，S-01…S-12 识别组合齐全 | must | 对象名计数 + 同机位裁图 | TV13-01 |
| REQ-41 | §2.1.2 删除清单 0 残留（含 `test_hall_roof`） | must | 对象名黑名单扫描 | TV13-02 |
| REQ-42 | 全图屋顶对象数 = 0（屋面板/女儿墙回归/横跨桁架/采光板顶） | must | 对象名 + 几何扫描 | TV13-03 |
| REQ-43 | 路面可辨物件密度 ≥ 1 件 / 400 m² | must | 主路面 8,000 m² 内计数 | TV13-04 |
| REQ-44 | E11 CV≥0.28、E12 镜像≤0.35、E13 同朝向≤0.40、E14 共线≤0.35 | must | `check_v13_organic.py` | TV13-05 |
| REQ-45 | 大路面保持"一整块"：不分幅、不抬高、不新增路缘 | must | 地形对象检查 + 目视 | TV13-06 |
| REQ-46 | 前后同机位对照图（master / hero / 南端裁图） | must | 目视 | TV13-07 |
| REQ-47 | 隔离目录重开重渲，content SHA 一致 | must | 复现脚本 | TV13-08 |
| REQ-48 | 旧业务门禁 13 项不回归（G1/G2/G6/G8/W1/S1/S2/S3/S8/S9/S10/S12/S15） | must | `space_base_check_v7.py` | TV13-09 |
| REQ-49 | 3 人 5 秒盲测：≥2 人秒认出我们的图即不通过 | should | 人工 | TV13-10 |

## 4. 约束与预算

- 单轮构建 ≤60 s、全尺寸渲染 ≤6 min；候选目录 ≤200 MB。
- 源/候选/证据分离；不改 `v11/` `v12/` 已冻结候选。
- 结束状态只允许 `target_met` 或证据完整的 `blocked_external`；低分不算外部阻塞。

## 5. 待确认 5 条（本轮按默认假设先做，不阻塞开发）

| # | 事项 | 本轮默认假设 |
|---|---|---|
| Q1 | 橙带岸壁是否降级 | **降级**：橙带只留在构件，不绕海岸 |
| Q2 | S1 阈值（色板地面 luma 0.608 < 判据 0.62） | **暂不改门禁**；本轮不降低地面亮度，Q2 留到验收前决策 |
| Q3 | 室外做旧解禁（M8o） | **解禁**：试车间防爆墙脚 1.5 m 水渍为 A 级实机特征，必须做 |
| Q4 | 码头敞顶 | **关闭**（D2） |
| Q5 | 西南发射区剪影 | **不加**：画幅紧，南端只做试车间一个终点 |
