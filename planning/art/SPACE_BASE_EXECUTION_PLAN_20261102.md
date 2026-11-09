# 航天基地静态地图 · 一次性执行计划（N0–N7）

> 状态：**proposed**。确认本计划 = N4 `confirmed`；回复“开始”后连续执行 P0–P4，不再停在阶段间等审批。
> 唯一设计口径：`planning/art/SPACE_BASE_MASTER_SPEC_20261102.md`（v1.3，SHA `4e0e2222…`）。
> 执行契约：`knowledge/common/dev_core/HARNESS_LIFECYCLE.md`；连续制作模式参考
> `planning/art/STATIC_MAP_WORKFLOW_20261028.md` 的 G0–G3，但**不套用 P1 的参考、评分、硬门槛或 gate**。

## 0. 一次性能完成到什么程度

本轮的交付目标是**一张可验收的静态地图 + 可重开的 Blender 源 + 绑定证据**，不是完整游戏。

做：
- 1920×2560 随包 JPEG（q88–90，目标 ≤3 MB）；
- 3840×5120 PNG master（仅归档、2× 超采样）；
- 可独立重开的 `scene.blend`；
- 4 张检查图、`REVIEW.md`、`DELIVERY.json`、`GATE_REPORT.json`、`MANIFEST.json`、`REPRODUCE.md`；
- 本机微信加载 **W1/W2 预检**（文件尺寸/格式/包体算术）；有 DevTools 就做一次最小加载冒烟。

不做（本轮范围外）：
- 角色、UI、动画、玩法、完整 Cocos/微信游戏工程、真机性能；
- A1 角色阴影、W3 首帧/内存、W4 真机降级——这三项属于运行时验收，另开 run；本轮只记录为 `external`；
- 不覆盖 `art/static_map/space_base_minigame/` 现有概念图/参考图；新源写 `v01/`。
- 不用 AI 直出整图；所有几何/材质/贴图来自可编辑 Blender 源。

**冻结条件**：8 px/m、正交 55°、北侧朝南、`ortho_scale=240`、1920×2560（含南侧 70 px 出血）。
任何一项要改，整图/相机公式全变，必须回到本计划重批，不边做边改。

### 0.1 输入冻结

| 输入 | 当前 SHA256 | 用途 |
|---|---|---|
| `SPACE_BASE_MASTER_SPEC_20261102.md` | `4e0e2222…` | 唯一设计口径 |
| `_routes_v13.html` | `6b98e788…` | 总平面/动线 |
| `_corridor_strip.html` | `650dbdff…` | 南向通道条图 |
| `HANDOFF_20261102.md` | `3a4a27b4…` | 交接口径 |
| `reference/_df_screenshots/MANIFEST.json` | P0 重算 | 参考截图/SHA |

P0 重新计算并核对；任何一份与上表不一致，先停下查原因，不带着漂移输入开工。

## 1. 工作流映射

| 阶段 | 本计划 | 产物 | 关口 |
|---|---|---|---|
| N0 需求 | P0：写 `REQUIREMENTS_BRIEF.md` | 范围/交付/验收/冻结条件 | 用户确认本计划 |
| N1 路由 | P0：新建 `space_base_minigame` 业务包 + `RESOLVED_KNOWLEDGE.json` | 业务包、加载清单、排除 P1/Arknights | 路由无歧义 |
| N2 设计 | P0：`SOLUTION_DESIGN.md` 指向 spec v1.3 + 两张图 | 设计快照、SHA、相机/比例 | spec/图一致 |
| N3 用例 | P0：`test_cases.json`（G/W/S/A 共 20 条） | 用例、判据、证据路径 | 覆盖 20/20 |
| N4 确认 | 本计划末尾的确认 | `design_baseline.status=confirmed` | **只确认一次** |
| N5 原型 | P1：G1 灰盒 | 灰盒图、G1–G8 证据 | 灰盒不过不做 L2 |
| N6 生产 | P2：G2 代表组合；P3：G3 终图 | 材质/灯光/终图/证据 | S1–S7、W1/W2 |
| N7 验证 | P3：机械 gate + 隔离复现 + 自评 | `GATE_REPORT`、`DELIVERY`、`REPRODUCE` | 必检全过 |
| N8 复盘 | P4：交接/日志/冻结 | 最终报告、handoff 更新 | 无未解决项 |

**一次性契约**：
- P0–P4 连续执行；每关不过就在同一 run 内修源、重渲、重跑，不请求阶段审批。
- 同一问题同一方法两次无改善 → 换方法；两种方法各两次无改善 → `design_recheck_required`，带证据停下。
- 只有真实外部阻塞（Blender/参考/DevTools 缺失、用户叫停）才停；`not_run`/`external` 不得写成 `pass`。
- 单写者：`v01/scene.blend` 只允许本 run 写；并行只做只读审计/独立预览，不并行写主场景。

## 2. 业务包与运行目录

### 2.1 新建业务包

`knowledge/business/space_base_minigame/`

| 文件 | 内容 |
|---|---|
| `START_HERE.md` | 业务入口：先读 spec v1.3、本计划、HANDOFF |
| `BUSINESS_PROFILE.md` | business_id、deliverable_type=static_map、范围/边界、8 px/m、P1 隔离 |
| `HARNESS_SPEC.json` | 本业务检查集：G1–G8、W1/W2、S1–S7；A1/W3/W4 标 external |
| `test_cases.json` | 20 条用例，绑定 Brief/SHA/证据路径 |
| `scorecard.json` | 可读性检查表（无总分门槛，不做美术评分） |

注意：`knowledge/business/manifest.json` 和 `knowledge/active/README.md` 当前有 pilot 相关未提交改动；
P0 **只追加** space base 条目，不覆盖其他业务。

### 2.2 新建 active run

`knowledge/active/20261102-space-base-map/`

| 文件 | 内容 |
|---|---|
| `REQUIREMENTS_BRIEF.md` | N0：本计划 §0 的范围/交付/验收/冻结条件 |
| `SOLUTION_DESIGN.md` | N2：spec v1.3 的相机、坐标、分区、L0–L5、20 检查 |
| `DEV_FEASIBILITY_REVIEW.md` | Blender 路径/版本、引擎、渲染时间、磁盘、风险 |
| `OPEN_QUESTIONS.md` | 仅列真实未决项；默认全按本计划 |
| `RUN_CONTEXT.json` | business_id/request_id/run_id、candidate=`v01`、design_baseline=`confirmed` |
| `RESOLVED_KNOWLEDGE.json` | 加载 spec/handoff/两张图/lifecycle/static workflow；排除 P1/Arknights |
| `runs/<run_id>/` | `MANIFEST.json`、`reproduction.json`、`evidence/G1..G3`、`repro/` |

### 2.3 候选目录

`art/static_map/space_base_minigame/v01/`

```text
scene.blend
renders/
  space_base_v01_master.png      # 3840×5120，归档
  space_base_v01.jpg             # 1920×2560，随包
  checks/
    01_core.png
    02_workshop.png
    03_south_exit.png
    04_ceo.png
reference_analysis/
  SPACE_BASE_REFERENCE_PROFILE.json
REVIEW.md
DELIVERY.json
GATE_REPORT.json
MANIFEST.json
REPRODUCE.md
```

### 2.4 工具

| 文件 | 用途 |
|---|---|
| `tools/blender_space_base/spec_dims.py` | 把 spec 的关键坐标/尺寸集中成常量，禁止场景脚本手写散落坐标 |
| `tools/blender_space_base/build_scene.py` | 程序化搭 L0–L5；分区 collection、命名、材质、实例 |
| `tools/blender_space_base/render_only.py` | 隔离复现：只开相机/灯光/渲染，不重建场景 |
| `tools/space_base_check.py` | 机械检查：文件/SHA/尺寸/JPEG 大小/用例覆盖/证据路径/包体算术 |
| `tools/blender_space_base/geom_check.py` | Blender 内检查包围盒 z-min、悬空/穿插、门位/边界（G1/G3/G6 的机械部分） |

## 3. 分阶段执行

### P0 / G0 — 锁输入与 N0–N4（45–60 分钟）

1. 重算并记录 spec、handoff、两张示意图、参考清单的 SHA；确认 `v01` 未占用。
2. 建 §2.1–§2.4 的业务包、active 目录、候选骨架、工具骨架；在
   `knowledge/business/manifest.json` 追加 `space_base_minigame`，在 `START_HERE.md` /
   `AGENTS.md` 的业务清单追加一行，在 `knowledge/active/README.md` 登记本请求
   （只追加，保留现有 pilot 改动）。
3. 写 Brief/Design/Feasibility/Open Questions；`RUN_CONTEXT.design_baseline.status=confirmed`，
   `confirmed_basis` 写用户确认本计划的时间/消息。
4. 按 `START_HERE.md` §6 输出 3–5 行开工摘要：business_id、deliverable_type、
   权威文件路径与 SHA、覆盖决定、是否存在 blocking；与 `RESOLVED_KNOWLEDGE.json` 对齐。
5. 把 §9.7 的 20 条转成 `test_cases.json`：
   - G1–G8：灰盒/终图，机械+人工；
   - W1/W2：本机文件/包体预检；
   - S1–S7：终图人工视觉，绑定 SHA；
   - A1/W3/W4：`external`，不参与本轮 target。
6. 建 `HARNESS_SPEC.json` + `scorecard.json`；写 `tools/space_base_check.py` 的最小可运行版。
7. 磁盘预检；记录 Blender 版本/路径、渲染引擎选择。
8. **N4 记录**：用户确认本计划即 `confirmed`，不另开审批。

P0 完成证据：输入清单、SHA、业务包/active 文件、20 条用例覆盖表、工具 `--help` 输出。

### P1 / G1 — 灰盒 L0–L1（2–3 小时）

只建：地面、四室墙、四段环廊、中央设备体、花园带、引道、试车间防爆墙、门洞、南出口、北门、T-16 基础体块。
不建 L2 以下的任何细节。

相机锁：正交 55°、北侧朝南、`ortho_scale=240`、分辨率先 1920×2560（灰盒预览）。
渲染整图灰盒，检查 G1–G8：
- G1 240 m = 1920 px；
- G2 四室可辨（遮字仍能认出）；
- G3 总裁两条竖梯入口/落地层四边实墙；
- G4 南出口不被 UI 压（py 1119、横向 47–53%）；
- G5 北门看终点被集装箱挡住（灰盒先放体块）；
- G6 无悬浮/断墙/穿模（Blender geom_check + 6 格扫视）；
- G7 四边跟随边界（视口模拟图）；
- G8 花园带/引道衔接无缝。

不过就修布局/接地/门位，重渲；**G1–G8 全过才进 P2**。

P1 证据：灰盒整图、6 格裁切、geom_check JSON、G1–G8 表、相机参数、源 SHA。

### P2 / G2 — 代表组合 L2–L4（2–3 小时）

按“7 个识别点优先”建，不求 §5 全表逐件：
- H1：Ø38 低墙 + 12 柱 + 观察窗带 + 中央立柱 + 14 m 吊舱；
- H2：45×28 池 + 3 压力舱 + 龙门吊 + 办公舱；
- H3：24×22 坑 + 双机械臂 + 卫星 + 9 条蓝光带 + 二层窄环廊；
- H4：整面绿墙 + 筒拱 + Ø12 舱门 + 机械臂/卫星 + 行车 + 3 道矮隔墙；
- 总裁：40×30 玻璃盒 + 透明顶 + 屏风 + 保险柜 + 浑天仪 + 沙发 + 竹槽 + 盒南栏杆；
- 花园：40×8 池 + 双喷泉 + 树池 + 长椅 + 灯柱；
- 四段环廊 + 引道 11 件 + 试车间关键件（防撞管/T-16、导流坑、集装箱掩体、撤离点/终端）。

材质：12 色、程序化、无外部贴图；L3 标线/分缝/水渍/标识画贴图或贴片；不堆无用途小件。
灯光：天空/主光/环境光/室内补光/总裁暖光；阴影 0.6–0.8 倍、硬边。
渲 1920×2560 代表组合图；检查 S1–S7 + G5/G6；低分就改源重渲。
允许把非识别小件合并/贴图化，但必须在 `REVIEW.md` 记“省略/合并”清单。

P2 证据：组合图、局部裁切（H1/H2/H3/H4/总裁/花园/走廊/试车间）、色相/明度统计（diagnostic_only）、S1–S7 自评。

### P3 / G3 — 终图、导出、验证（1.5–2 小时）

1. L5 最终灯光；3840×5120 PNG master 渲染（Eevee/Cycles 按 P0 实测选择；一次渲完整图，禁止分块）。
2. 降采样 1920×2560；导出 JPEG q88–90；检查 ≤3 MB、最大边 ≤4096。
3. 4 张检查图：核心区视口 135×247、试车间、南出口衔接、总裁特写。
4. W1/W2 本机预检：
   - W1：格式/尺寸/大小/无 alpha/最大边；
   - W2：地图 JPEG + `js/` + config 的包体算术 ≤4 MB，总包 ≤30 MB；
   - 有 DevTools CLI 就做最小加载冒烟并截图/console；没有就记 `not_run`。
5. 机械 gate：`tools/space_base_check.py`；检查源/图 SHA、尺寸、JPEG 大小、用例覆盖、证据路径、包体算术。
6. 隔离复现：复制 `scene.blend` 到 `runs/<run_id>/repro/`，用 `render_only.py` 重开重渲；
   比较 content SHA / RMS（容差事前声明 ≤2/255）；记录命令、退出码、耗时。
7. 制作侧自评 + 反证：
   - 逐条 G/S/W1/W2 写可见证据；
   - 逐条写“最可能扣分的反例”，确认/下调；
   - 不过的项进 `repair_queue`，改源重渲，直到全过或真实外部阻塞；
   - A1/W3/W4 标 `external`，不写成 pass。
8. 写 `REVIEW.md`、`DELIVERY.json`、`GATE_REPORT.json`、`MANIFEST.json`、`REPRODUCE.md`。

### P4 / N8 — 复盘与冻结（15 分钟）

- 最终报告：`target_met`（静态图部分）或证据完整的 `blocked_external`；
- 更新 handoff/工作日志；记录未验证项（A1/W3/W4）；
- 不覆盖旧候选；不推送，除非用户单独要求。

## 4. 20 条验收的归属

| 组 | 本轮要求 | 方式 |
|---|---|---|
| G1–G8 | **必过** | 灰盒 + 终图；机械尺寸/geom_check + 人工看图 |
| W1 | **必过** | 本机文件/尺寸/大小检查 |
| W2 | **必过（算术预检）** | 地图+项目文件大小；不声称真机 |
| S1–S7 | **必过** | 终图人工自评 + 反证，绑定图 SHA |
| A1 | external | 无角色层；运行时另测 |
| W3/W4 | external | 真机首帧/内存/降级；本机无设备就 blocked_external |

`target_met` 只覆盖 G1–G8 + W1/W2 + S1–S7；A1/W3/W4 在最终报告中单独列外部项，不混写。

## 5. 返修与停止

- 每批一个主假设；记录 `hypothesis_id`、前后同机位图、源/图 SHA、命令/退出码/耗时、`improved/unchanged/worse`。
- 修复顺序：布局/接地 → 主体轮廓 → 材质统一 → 光色纵深 → 局部细节。
- 同一方法两次无改善 → 换方法；两种方法各两次无改善 → `design_recheck_required`，带证据停。
- 外部阻塞只认：Blender 缺失/崩溃、参考缺失、DevTools/设备缺失（仅 W3/W4）、用户叫停。
- 不得通过改 spec/阈值/参考、重算旧 SHA、堆无用途物件来“过”。

## 6. 时间、资源、风险

预计一次连续运行 **6.5–9 小时 agent 工作 + 渲染/返修时间**（不含真机）；在同一个 run 内完成，不按阶段等审批。

| 风险 | 对策 |
|---|---|
| 8 px/m 被改 | 本计划冻结 8；要改先重批，整图/相机重算 |
| 62 类 L1/180 L2 做不完 | 只保证 7 识别点 + 20 检查；非识别件合并/贴图化，REVIEW 列省略清单 |
| Blender/渲染慢 | P0 实测 Eevee/Cycles 与分辨率；灰盒先 1920，终图 3840；一次渲完整图 |
| 相机/遮挡 | G1 灰盒先过 G1–G8；不过不往上做 |
| 源—图不同源 | 终图必须由 `scene.blend` 重开渲染；隔离复现绑 content SHA |
| 微信真机不可用 | W1/W2 本机；W3/W4 记 external，不冒充 pass |
| P1 hook 不适用 | 新建业务包；人工自评 + 本业务机械 checker；不套 P1 评分 |
| manifest/active 有 pilot 未提交改动 | 只追加本业务条目，不覆盖其他改动 |
| 磁盘 | 新候选 + master PNG + 证据先预检；≤15 GiB，12 GiB 预警 |
| 自评虚高 | 逐条反证自检；图 SHA 变则自评失效；无独立终审不等于可自签 |
| 时间盒 | P1 ≤4 h、P2 ≤4 h、P3 ≤3 h；超出先削可选 L2/L3，不削 7 个识别点/20 条检查；终图最多 3 轮整图重渲 |

## 7. 完成定义（DoD）

- `v01/scene.blend` 可独立重开；源/图/参考 SHA 全绑定。
- `space_base_v01_master.png` 3840×5120；`space_base_v01.jpg` 1920×2560、≤3 MB。
- G1–G8、S1–S7、W1/W2 全过；A1/W3/W4 明确 external/not_run。
- 4 张检查图、`REVIEW.md`（含反证/返修/省略清单）、`DELIVERY.json`、`GATE_REPORT.json`、`MANIFEST.json`、`REPRODUCE.md`。
- 隔离复现通过（content SHA 相同或 RMS ≤2/255，容差事前声明）。
- 最终报告只写证据支持的状态；不把 `not_run`/`external`/`diagnostic_only` 写成 pass。

## 8. 确认

**确认本计划 = N4 confirmed。** 默认按：
- 8 px/m 冻结；
- 本轮只做静态图 + 可编辑源 + W1/W2 预检；
- A1/W3/W4 运行时另开。

回复“**开始**”即进入 P0→P4 连续执行；中途只在真实外部阻塞或你叫停时停。
若要改 8 px/m、把运行时/真机纳入本轮，或要求 full 62 类 L1，请在确认时直接写出来——这会改变工期和“一次完成”的定义。
