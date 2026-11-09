# 航天基地 v14 · 一次性完整调整方案（单批次执行版）

> 日期 2026-11-08　｜　状态：**执行方案（写完即执行，中途不再分轮确认）**
> 整合：`SPACE_BASE_TECHNICAL_ART_PLAN_20261108.md` v1.2（成像层 P1–P5）
> 　　　+ `v14/p0/P0_REPORT.md`（实测基线与选型）
> 　　　+ `SPACE_BASE_EXTERIOR_ORGANIC_PLAN_20261108.md` v2.0（内容层，本批次范围见 §2.2）
> 用户要求：「给出一个完整的调整方案，我要一次性开发完成」
> 基线：`art/static_map/space_base_minigame/v13/`（**冻结只读**）｜目标：`.../v14/`

---

## 0. 这份方案解决什么

v1.2 把成像改造拆成 P1→P5 五轮、每轮等人看对照图。用户不要这个节奏。
本方案把 **L0-a / L0-b / L1 / L2 / L3 / L4 / L5 / L6 合并成一次构建**，
所有参数一次写入 `build_scene_v14.py`，内部用**自动收敛规则**（§6）代替人工逐轮确认，
最后一次性交付完整 v14 包 + 前后对照 + 验收报告。

**一句话**：v13 的问题不是缺内容，是「Standard 直出 + 3 盏灯 + 零 compositor + 63 个平涂材质」。
v14 一次把这四件事全改掉。

---

## 1. 基线（P0 已实测，不再推测）

| 项 | 值 |
|---|---|
| v13 master 成像 | p50 0.766 / L>0.80 42.3% / L<0.30 3.4% / 跨度 0.444 / 裁切 2.01% / sat 0.208 |
| v13 S1 | **0.614**（master）、0.501（hero），PASS |
| v13 场景 | 1,383 对象 / 9,935 面 / 69 材质定义（63 在用）/ 761 bevel / 3 灯 / `use_nodes=False` |
| 色彩管理 | `Standard / None / +0.22` |
| P0 选型 | **D：Standard / None / exposure −0.15**（交付尺寸实测，目视最贴 P1） |
| 计时基线 | 构建 24.15 s；master 1680×2478/24spp 单张 77–80 s |
| P1 成品参照 | 同为 `Standard / None / +0.34`，但 **7 盏灯 + 14 节点 compositor 栈** |

---

## 2. 范围

### 2.1 本批次做（一次完成）

- **成像链路全部**：L0-a compositor 分级栈、L0-b 色调映射、L1 光照、L2 明度分工、
  L3 材质族、L4 纹理响应、L5 边缘接地、L6 纵深水面。
- **完整交付包**：`scene.blend`、master / hero / route、派生交付图、A/B 对照、
  MANIFEST + SHA 重绑、`check_v7` 门禁、A1–A13 + S1 验收报告、复现命令。

### 2.2 本批次**不做**（明列，避免一次改太多变量无法归因）

| 项 | 理由 |
|---|---|
| 场地轮廓 94/74/62 去直角 | 牵动 `site_poly` / 桥 B / 岸线 / G1 投影，属结构改造，应单独立项 |
| 主路面 F1–F5 填充、四厅立面套件 | 属 v2.0 内容方案；成像层改完后再评估是否还需要 |
| 试车间内容增删 | v13 已闭合 S-01…S-12，门禁 PASS，不动 |
| 画幅 / 7 px/m / 四厅尺寸 / 敞顶 / 桥 B | 冻结 |
| 第三方贴图 / HDRI / LUT 文件 | 项目约束；Blender 4.5 无 `CompositorNodeLUT`（已实测） |
| 改 S1 门禁判据 | 不改契约；用参数把 S1 稳在 0.45 以上 |

---

## 3. 冻结决策（不再询问）

| # | 决定 | 依据 |
|---|---|---|
| Q-T1 | **A 冷灰基地 + 暖光点缀** | v1.2 §7 推荐默认；D 组自带暖调，无需切全局暖 |
| Q-T2 | 只在 **v14 分支**改色彩管理，v13 冻结 | 图变即证据失效 |
| Q-T3 | **不改 S1 契约**，降为验收项 | P0 实测 v13 S1=0.614，三候选全 PASS |
| L0-b | **采用 D**：`exposure = −0.15`，`view_transform` 保持 `Standard` | P0 交付尺寸实测 + 目视，见 §1 |
| 分期 | P1–P5 合并为**单批次**，内部自动收敛 ≤2 轮 | 用户本轮要求 |

### 3.1 硬约束（任何一条破即本批次不算完成）

1. **S1 `light_land ≥ 0.45`**（`tools/space_base_v11_post.py` 口径，不改判据）。
   D 组余量只有 0.497 → **这是全局最紧的约束**，见 §5.1。
2. `check_v7` PASS / 0 硬失败；**改图后必须重绑 MANIFEST SHA**。
3. 画幅 1680×2478、7 px/m、四厅敞顶、桥 B、试车间 S-构件不回归。
4. `AGENTS.md §2`：命令 / 退出码 / 耗时 / SHA 全部留证。
5. 不把 `diagnostic_only` / `not_run` 写成 pass。

---

## 4. 单批次改造清单 M01–M12

所有改动集中在 `build_scene_v14.py` 的 `apply_v14_art(m)` 一个函数内，
由 v13 脚本派生，末尾一次调用；`--art=off` 可退回 v13 行为做 A/B。

| # | 模块 | 入口 | 参数（一次写入） |
|---|---|---|---|
| **M01** | 派生 v14 | `build_scene_v13.py` → `build_scene_v14.py` | 追加 `apply_v14_art()`；输出 `v14/scene.blend` |
| **M02** | L0-b | `scene.view_settings` | `Standard` / `None` / **exposure −0.15**（gamma 1.0） |
| **M03** | L0-a compositor | `scene.use_nodes=True` | 链：`RLayers → Glare(FOG_GLOW, 低强度) → ColorBalance(冷 lift / 暖 gain) → HueSat(Sat 1.18, 补 A13) → CurveRGB(轻 S) → Composite`。**不用暗角**（压外缘）、**不用 LUT**。各节点可 `--no-<mod>` 关闭做 A/B |
| **M04** | L1 光照 | `build_camera_light` 后覆写 | Sun `rot.x 46°→57°`（仰角 44°→33°，`z` 保持 −70° 使影向不改）、`angle 2.2°→5°`、`energy 4.4→3.6`；World `0.62→0.45`；**补 2 盏 Area**（冷天光 fill `#8FA3B0` 4500 W / 暖 bounce `#FFE0B8` 3500 W，尺寸 160–200）；AO `0.42/1.6→0.55/2.6`；墙内暗带 `1.1→1.8 m` |
| **M05** | L2 明度分工 | 材质 Base Color | `road #87898B→#6E7275`、`steel/压顶→#333B3D`、室内地坪 `#A0A5A2→#8E9594`；**`platform #B4B0A2` 与 `apron #B0AC9F` 保持不动**（保 S1 浅色基本盘，§5.1） |
| **M06** | L3 材质族 | `bpy.data.materials` | 给 63 个在用材质打 `material_family` 标签（concrete/asphalt/metal/glass/vegetation/accent/other）；**别名合并**同色重复（`garden_walk→platform`、`causeway→apron` 等）后清理 `users==0` 材质；大面积可见金属设 `roughness 0.35–0.5 / metallic 0.6`、玻璃 `0.08`、混凝土 `0.85`、沥青 `0.9`；同步 `IL_MATS` |
| **M07** | L4 纹理 | `apply_surface_textures` 的 `_tex_mix` 调用 | `lo 0.74~0.90→0.62~0.74`、`hi 1.02~1.05→1.08~1.14`；`mortar 0.72→0.55`；**同一 mask 驱动 Roughness**（`Map Range 0.72–0.95`），让修补板/路径有高光差 |
| **M08** | L5 边缘 | `apply_bevels` | `w=min(0.08, mind*0.22)` → `min(0.22, mind*0.30)`（结构块 mind≥0.73 m 得 1.54 px）；薄板靠 panel 分缝暗线（M07 已增强），**不拿 0.22 m 当全场景指标**；新增 `check_v14_grounding.py` 查包围盒落地差 ≤0.02 m |
| **M09** | L6 纵深 | `build_shore` / 雾 | 在已有 `#2E5A5F` shallow + `shore_fan` 基础上按离岸距离分**三段色阶**（`#17383F → #2E5A5F → #3E6360`）；`is_fog` 雾**仅英雄图启用**、俯视 master 保持隐藏（避免雾遮地图）；compositor 局部柔化远景 |
| **M10** | 渲染脚本 | `render_v14_views.py` | master 1680×2478/24spp、hero 1920×1080/40spp、route 1680×2478/32spp；支持 `--no-comp`；输出绝对路径 |
| **M11** | 验收 | `check_v14_art.py` / `check_v14_scene.py` | A1–A13 + S1 + 场景统计，全写进 `v14/evidence/` |
| **M12** | 交付 | `make_v14_delivery.py` | 派生 `space_base_v11_*.png/.jpg` 命名副本（check_v7 契约）、checks 裁图、MANIFEST SHA 重绑、`check_v7`、前后并排图、DEVLOG / REVIEW / GATE_REPORT / REPRODUCE |

---

## 5. 验收口径（**开工前**重标定，不是事后放水）

### 5.1 一条必须讲清的冲突：A3 与 S1 抢面积

S1 数的是「陆地里 `L≥0.62 且 sat≤0.28` 的像素占比」，D 组只有 **0.497**，余量 0.047。
而 A3 要求暗部（`L<0.30`）从 5.3% 涨到 10–15%——暗部只能从中间调/浅色里拿面积，
**必然压低 S1**。P0 已实测：L0-b 两候选把亮端压下去了，暗部却只到 5%。

因此本批次的处理是：
- **暗部主要来自阴影与深色金属/沥青，不压浅色混凝土**（M05 明确 `platform` 不动）；
- **A3/A4 按俯视正交口径重标定**，原值保留为 stretch goal；
- **S1 是硬约束**，收敛时优先保 S1；若 A3 与 S1 不可兼得，如实记录 A3 未达标，不改判据、不写 pass。

### 5.2 指标表

| # | v1.2 目标 | **本批次目标** | 依据 |
|---|---|---|---|
| A1 陆地 L p50 | 0.58–0.64 | **0.62–0.70**（stretch 0.60–0.64） | D 实测 0.683；俯视正交中位天然偏亮 |
| A2 L>0.80 | ≤22% | **≤10%（收紧）** | D 已 3.4%，留补灯余量 |
| A3 L<0.30 | 10–15% | **≥8%**（stretch 10%） | §5.1 面积竞争；P1 参考 32.4% 是斜视景深，俯视不可比 |
| A4 跨度 | ≥0.55 | **≥0.50**（stretch 0.55） | 同上；D 实测 0.399，需靠 L1+L2 拉回 |
| A5 裁切 | ≤0.8% | ≤0.8%（不变） | D 0.79% |
| A6 材质 | 3 族 / ≤28 | 3 族 / **≤40（在用）** | 63 个里含大量功能识别色，硬压到 28 会破坏辨识；如实报最终数 |
| A7 表面响应 | `<0.5`≥25% / metallic≥4 / 族间极差≥0.15 | 同左（不变） | P0 重定义 |
| A8 边缘 | 结构块 ≥1.3 px | 同左 + panel 分缝对比可见 | P0 实测 0.56 px |
| A9–A10 | 目视 / 分带梯度 | 目视签收 + `diagnostic_only` | 正交俯视无真正远景 |
| A11 耗时 | 构建 ≤60 s / 全量 ≤6 min | 同左，实测留证 | AGENTS §2 |
| A12 门禁 | check_v7 PASS | 同左 + SHA 重绑 | |
| A13 饱和 | ≥0.24 | ≥0.24（不变） | D 0.210，靠 M03 HueSat 补 |
| **S1** | ≥0.45 | **≥0.45（硬约束）** | 不改契约 |

### 5.3 诚实规则

- 未达标项在 `GATE_REPORT.json` 里标 `fail` 并写原因，**不得写成 pass**；
- `diagnostic_only` / 目视项不计 PASS；
- 自动收敛最多 2 轮，仍不达标就如实交付 + 列出剩余缺口，不无限调参。

---

## 6. 自动收敛规则（代替人工逐轮确认）

每轮只改**一组**参数，全尺寸 master 一张（≈77 s），跑 `check_v14_art.py` 后按表决策：

| 触发 | 动作 | 上限 |
|---|---|---|
| A2 >10% | `exposure` 再 −0.05，或 2 盏补灯能量 ×0.8 | 1 次 |
| A3 <8% | `road` / `steel` 再压暗 10%，或 AO strength +0.08 | 1 次 |
| A13 <0.24 | HueSat `Saturation` +0.06 | 2 次 |
| A4 <0.50 | 同 A3（拉深暗部），**不用全局对比硬拉** | 1 次 |
| **S1 <0.45** | **提 `platform` 明度 +4%**（保浅色基本盘），不改判据 | 优先执行 |
| A1 >0.70 | 整体 `exposure` −0.03（须同时复测 S1） | 1 次 |

最多 2 轮；每轮留 `evidence/converge_rN.json`（参数、命令、耗时、指标、SHA）。
**任何参数变更都从源文件重构建，不在 blend 里手改**（AGENTS §2 / 可复现）。

---

## 7. 交付包（`art/static_map/space_base_minigame/v14/`）

```
scene.blend                    可编辑源（v14 唯一写入者）
renders/master_raw.png         1680x2478 / 24 spp
renders/hero_raw.png           1920x1080 / 40 spp
renders/route.png              1680x2478 / 32 spp
renders/space_base_v11_*.png   门禁命名副本（master/jpg/core/hero）
renders/checks/01..05.png      近景裁图
renders/_cmp_master.png        v13 → v14 同机位前后对照
renders/_cmp_hero.png          英雄视角前后对照
MANIFEST.json                  全量 SHA256（重绑）
DELIVERY.json / GATE_REPORT.json / REVIEW.md / DEVLOG.md / REPRODUCE.md
evidence/*.json                A1–A13、S1、场景统计、收敛轮次、计时
```

工具新增：`tools/blender_space_base/build_scene_v14.py`、`render_v14_views.py`、
`check_v14_grounding.py`、`make_v14_delivery.py`；沿用
`check_v14_art.py` / `check_v14_scene.py` / `space_base_check_v7.py`。

---

## 8. 回滚与证据

- **v13 全程只读**；所有写入只在 `v14/` 与 `knowledge/active/.../runs/` 的新目录。
- `build_scene_v14.py` 的 `--art=off` 可退回 v13 行为，用于归因。
- 每个阶段记录命令、退出码、耗时、产物 SHA；未留证不声称已验证。
- 若 M03 compositor 节点 API 不兼容，跳过该模块并在报告标注，其余链照常交付（不静默降级）。
- 若 `check_v7` 因交付命名/SHA 失败，按 TEST-ID 返修，**不放宽门禁**。

---

## 9. 执行顺序（一次跑完）

| 步 | 动作 | 产物 |
|---|---|---|
| S1 | 派生脚本 + 写 M02–M09 | `build_scene_v14.py` |
| S2 | 语法检查 + 构建 + 快速预览（840 / 12 spp） | `scene.blend`、`q_master.png` |
| S3 | 目视排查穿模/黑块/悬空；有则源级修 | 修后预览 |
| S4 | 全尺寸三视图渲染 | master / hero / route |
| S5 | A1–A13 + S1 + 场景统计 | `evidence/*.json` |
| S6 | 按 §6 自动收敛（≤2 轮，必要时从 S2 重来） | 收敛证据 |
| S7 | 派生交付图 + MANIFEST SHA 重绑 + `check_v7` | 完整交付包 |
| S8 | 前后对照 + 报告 + 记忆 | `_cmp_*.png`、DEVLOG、REVIEW、GATE_REPORT |

> **S6 之后不再向用户确认**，直接出最终包；未达标项如实列出。

---

## 10. 执行结果（本方案已跑完，2026-11-08 21:0x）

### 10.1 交付状态

| 步 | 状态 |
|---|---|
| S1 派生 `build_scene_v14.py`（`gen_v14_from_v13.py`，23 处替换 + `apply_v14_art`） | ✅ |
| S2 构建 + 快速预览（无黑块/穿模/爆光） | ✅ |
| S3 目视排查 | ✅ |
| S4 全尺寸三视图 | ✅ |
| S5 A1–A13 + S1 + 场景统计 | ✅ |
| S6 自动收敛 | ✅ **5 轮**（超出方案上限 2 轮，因 S1 是契约硬约束，如实记录） |
| S7 交付派生 + highres + MANIFEST SHA + `check_v7` | ✅ |
| S8 前后对照 + DEVLOG/REVIEW/GATE_REPORT | ✅ |

### 10.2 收敛轨迹

| 轮 | 核心改动 | S1 | A1 | A2 | A3 | A4 | A13 |
|---|---|---:|---:|---:|---:|---:|---:|
| r1 | 初版：全局提饱和 + 大幅减光 | **0.017** | .568 | 0.8% | 9.6% | .428 | .266 |
| r2 | 提亮 + 温和分级 | 0.448 | .644 | 16.9% | 7.1% | .489 | .213 |
| r3 | 亮度门控掩码接上 + platform +4% | **0.163** | .621 | 16.6% | 7.1% | .494 | **.276** |
| r4 | 关掉饱和度提升 | 0.448 | .644 | 17.1% | 7.0% | .492 | .213 |
| **r5 定稿** | **ColorBalance gamma 1.10 抬中间调** | **0.507 ✅** | **.670 ✅** | 18.7% | 4.8% | .471 | .195 |

**根因诊断**：S1 瓶颈是 `L≥0.62` 的陆地像素（v13 67.8% → r2 52.5%），
不是饱和度（`sat≤0.28` 仅 89.8% → 87.7%）。改单个材质无效，必须抬中间调；
gamma 比 exposure 更精准（高光端影响小）。

### 10.3 最终指标与未达标项

| 指标 | v13 | **v14 r5** | 本批次目标 | 判定 |
|---|---:|---:|---:|---|
| A1 陆地 L p50 | 0.766 | 0.670 | 0.62–0.70 | ✅ |
| A2 L>0.80 | 42.3% | **18.7%** | ≤10% | ❌（但优于 v1.2 原目标 22%） |
| A3 L<0.30 | 3.4% | 4.8% | ≥8% | ❌ |
| A4 跨度 | 0.444 | 0.471 | ≥0.50 | ❌ |
| A5 裁切 | 2.01% | 0.10% | ≤0.8% | ✅ |
| A13 饱和 | 0.208 | 0.195 | ≥0.24 | ❌ |
| **S1** | 0.614 | **0.507** | ≥0.45 硬约束 | ✅ |
| A6 在用材质 | 63 | 62 | ≤40 | ❌（功能识别色不可硬合） |
| A7 低粗糙度 / metallic | 16.7% / 1 | 24.5% / 7 | ≥25% / ≥4 | 部分（metallic ✅） |
| A8 结构块倒角 | 0.56 px | **1.54 px** | ≥1.3 px | ✅ |

**未达标项一律在 `GATE_REPORT.json` 标 FAIL，不写成 pass、不事后放宽阈值。**

### 10.4 结构性结论（写给下一轮）

**S1 判据与"消除亮端堆积"结构性互斥**：S1 要求 ≥45% 陆地像素同时满足
`L≥0.62 且 sat≤0.28`；v13 能满足，恰恰是因为 42.3% 的亮端堆积。
本批次未改契约，靠 gamma 抬中间调 + 放弃提饱和勉强兼顾，代价是 A3/A4/A13 未能达标。
若要把暗部、跨度、饱和度一起做上去，**必须按 HARNESS_LIFECYCLE 走 N2 重新裁决 S1 口径**——
这是业务契约问题，不是调参问题。

### 10.5 与方案的偏差（如实）

1. `--art=off` 未实现：颜色/纹理/倒角改动写进了源脚本常量；A/B 以冻结的 v13 候选对照。
2. 收敛轮次 5 > 方案上限 2：因 S1 硬约束连续两轮只差 0.002，继续收敛到 0.507 才停。
3. 亮度门控饱和度在 r3 验证有效但会把 S1 压到 0.163，最终版本保留节点、`sat=1.0`（等效关闭）。
4. A6 目标 ≤40 未达成（62）：63 个在用材质含四厅色相签名、警示/撤离/角色等功能色，
   硬合并会破坏 REQ-04 与 S4/S15，故不强行凑数。
5. 视觉盲测未做（`not_run`），`RUN_STATUS.json` 不宣称 `target_met`。

### 10.6 最终验证结果

| 项 | 结果 |
|---|---|
| `space_base_check_v7` | **PASS / hard_failures 0**（`check_summary.json`） |
| 隔离复现 | **content SHA 一致，RMS 0.0**（`reproduction.json`） |
| master 与收敛稿一致性 | `master_raw.png` 与 `converge_r5.png` 解码 RGB 完全一致 |
| highres raw | 3360×5880 / 12 spp ✅ |
| 全尺寸三视图耗时 | **6 m 51 s**（超 A11 的 6 min 上限，如实记录） |
| highres 耗时 | 6 m 20 s（与复现并行，含 CPU 争用） |
| 场景最终统计 | 1,385 对象 / 9,935 面 / 62 在用材质 / 761 bevel / 5 灯 / `use_nodes=True` |
| 接地检查 | 196 个包围盒高位疑点，`diagnostic_only`，需目视签收 |

**返修记录**：门禁首轮报 2 个硬失败——① REQ 编号 `REQ-V14-01` 不匹配
`check_v7` 的 `^\|\s*(REQ-\d+)\s*\|` 正则，改为 `REQ-50…57`；
② `MANIFEST.json` 绑定自身 SHA 永远不一致，从条目中移除。均属契约层，修后 PASS。

**结束状态**：`N7 / mechanical_complete / end_state=null`。
机械交付闭合；视觉签收、3 人盲测、以及 §10.4 的 S1 契约裁决仍需人工，
因此**不宣称 `target_met`**。

