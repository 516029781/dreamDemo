# 中央花园 v10 · Harness 开发计划

> 日期：2026-11-05　｜　状态：**待开工**
> request_id `20261105-space-base-v10-garden`｜run_id `20261105-1800`｜design **r07**
> 依据：`SPACE_BASE_GARDEN_OUTFIELD_PLAN_20261105.md` **v1.3（已定版）**、`REQUIREMENTS_BRIEF.md`（38 条 REQ）、`test_cases.json`（38 用例）
> 原则：v09 只读留档，v10 独立 candidate / run / builder；所有改动都落在 v10，不碰 v09。

## 1. 运行身份

| 项 | 值 |
| --- | --- |
| request_id | `20261105-space-base-v10-garden` |
| run_id | `20261105-1800` |
| candidate | `art/static_map/space_base_minigame/v10` |
| design baseline | `runs/20261105-1800/baselines/design_r07/` |
| 业务 spec | `knowledge/business/space_base_minigame/HARNESS_SPEC.json`（r06，不改） |
| 项目级检查 | GA01–GA10（花园几何 / 布局 / 地面 / 挡墙 / 种植 / 水景 / 构筑 / 清理 / HeroRoute / 交付） |
| 机械检查器 | `tools/space_base_check_v7.py`（v6 的 v10 文件名版） |
| 交付尺寸 | master 3360×5880 → 1680×2478；core 2072×1876；hero 1920×1080；JPEG ≤3 MB |

目录：

```
knowledge/active/20261105-space-base-v10-garden/
├── REQUIREMENTS_BRIEF.md        38 条 REQ（28 承继 + 10 新增）
├── test_cases.json              38 用例，证据路径已指向 runs/20261105-1800
├── RUN_CONTEXT.json             candidate=v10，baseline=design_r07
├── RESOLVED_KNOWLEDGE.json      Q1–Q5 定版 + 8 份知识绑定
└── runs/20261105-1800/
    ├── baselines/design_r07/    方案 v1.3 / spec / build_scene_v9 / check_v7
    └── evidence/                G1–S15 + GA01–GA10
```

## 2. 阶段计划

| 阶段 | 目标 | 主要动作 | 产物 | 退出条件 | 预估 |
| --- | --- | --- | --- | --- | --- |
| G-0 隔离与清理 | 建立 v10 写入边界，先拆雷 | 复制 v9 工具链为 v10；删 5 只浮锥（桥 3 + 半岛 2）；删遗留引道管架 cw_pipe/cw_post/cw_loop/cw_lamp（横贯平台且悬空）；清平台段内 5 灯 / 3 墩 / 23×2 栏杆 / 标线 / 路缘；K10 在 t40 / 114 两端落井 | `build_scene_v10.py` 骨架、清理清单 | GA08 扫描 0 命中；v09 文件 mtime 不变 | 0.25 天 |
| G-1 平台几何 | 桥 → 平台 → 桥 | 平台 100×74、8 m 倒角、z=4.70、8 m 入口坡；桥 A/B 重做；桥墩留 24 / 120；K10 竖井 | `scene.blend` 几何 | GA01 通过；G1/G8 通过 | 0.5 天 |
| G-2 地面与水景 | 铺装分级 + 圆角池缘 | 6 m 二级缝 / 24 m 一级缝 / 1.2 m 边带 / 0.08 m 锈渍；2 座 22×8 池；0.45 m 圆角压顶；花坛石缘 | 地面、水池、`checks/06_paving.png` | GA03 / GA06 通过；S1 0.55–0.58 | 0.5 天 |
| G-3 种植 | 棕榈列 + 绿篱 + 模纹 | 16 株列植（1.8 m 方池）、条槽绿篱、2 座 20×14 模纹园、4 块 10×8 花坛、连续边篱 | `checks/08_garden_plan.png` | GA05 通过；S2 0.030 | 0.5 天 |
| G-4 构筑物 | 挡墙 + 观景台 + 廊架 + 外场 | 深墙 / 浅压顶 / 橙带 / 4.5 m 壁柱；观景台 16×12（6 凳）；廊架 14×12（8 柱）；服务区 10×14；门架 ×2；牌 ×2；灯 ×8 | `checks/07_wall.png` | GA04 / GA07 通过；G6 通过 | 0.5 天 |
| G-5 渲染与证据 | 全链出图 | master / core / hero / 06–08 / HeroWide-Mid-Low / HeroRoute / 近景 P1–P8 + NPR | `renders/`、`evidence/` | W1 / W2 / G7 / S12 通过 | 0.5 天 |
| G-6 门禁与交付 | 0 硬失败 | 复现 RMS、S15、check_v7、五件套、MANIFEST | `GATE_REPORT` / `DELIVERY` / `MANIFEST` / `REPRODUCE` / `REVIEW` | check 0 硬失败；GA10 通过 | 0.25 天 |

> 合计约 **3.0 天**；比方案 §7 的 2.75 天多 0.25 天（G-6 门禁与交付绑定）。

## 3. 文件与工具

| 新文件 | 来源 | 关键改动 |
| --- | --- | --- |
| `tools/blender_space_base/build_scene_v10.py` | v9 复制 | 新增 `build_garden_platform` / `ground` / `planting` / `structures`；桥 A/B 拆分；K10 落井；删浮锥 |
| `tools/blender_space_base/render_v10_views.py` | v9 复制 | master / core / hero_raw，输出 v10 文件名 |
| `tools/blender_space_base/render_v10_garden.py` | 新建 | 3 个机位：`06_paving` / `07_wall` / `08_garden_plan` |
| `tools/blender_space_base/render_v10_hero.py` | v9 复制 | VARIANTS 增加 `HeroRoute`（−120,−370,220 / 150,−30 / 58） |
| `tools/blender_space_base/render_v10_near.py` | v9 复制 | P1–P8 机位不变；花园入画的两张重取构图 |
| `tools/blender_space_base/evidence_v10.py` | v9 复制 | 增加 GA01 / GA02 / GA05 / GA06 / GA07 / GA08 的对象级证据 |
| `tools/blender_space_base/repro_v10.py` | repro_v8 复制 | 840×1470@64 → LANCZOS 420×735，对比 master_raw |
| `tools/space_base_v10_npr.py` | v9 复制 | 空气透视 / 5 段色阶 / 深度描边 / 纸纹，参数不变 |
| `tools/space_base_v10_post.py` | v9 复制 | 合成 + S1/S2/S3/S12 + checks 01–05 + 复制 06–08；新增 GA09 水色统计 |
| `tools/make_v10_delivery.py` | v9 复制 | v10 路径 + GA01–GA10 汇总 + 五件套 |
| `tools/space_base_check_v7.py` | v6 复制 | **已建**：v10 文件名；其余 25 门禁逻辑不变 |

## 4. 证据矩阵

| REQ | 检查 | 证据 | 生产 |
| --- | --- | --- | --- |
| REQ-01..08 | G1–G8 | `evidence/G1..G8/*`（G5 pair_note、G6 geom_check、G8 notes） | post + evidence_v10 |
| REQ-09..10 | W1 / W2 | `evidence/W1/file_check.json`、`W2/package.json` | post |
| REQ-11..20 | S1–S10 | `evidence/S1..S10/*` | post + evidence_v10 |
| REQ-21..23 | A1 / W3 / W4 | `evidence/external/*.md` | 外置，随交付说明 |
| REQ-24..28 | S11–S15 | `evidence/S11..S15/*` | post + color_probe |
| REQ-29 | GA01 | `evidence/GA01/platform_geom.json` | evidence_v10 |
| REQ-30 | GA02 | `evidence/GA02/layout.json` | evidence_v10 |
| REQ-31 | GA03 | `evidence/GA03/paving.json` + `checks/06_paving.png` | render_v10_garden + post |
| REQ-32 | GA04 | `evidence/GA04/wall_profile.json` + `checks/07_wall.png` | render_v10_garden + post |
| REQ-33 | GA05 | `evidence/GA05/planting.json` + `checks/08_garden_plan.png` | evidence_v10 |
| REQ-34 | GA06 | `evidence/GA06/water.json` | evidence_v10 |
| REQ-35 | GA07 | `evidence/GA07/structures.json` | evidence_v10 |
| REQ-36 | GA08 | `evidence/GA08/cleanup.json` | evidence_v10（按名字/坐标扫描） |
| REQ-37 | GA09 | `evidence/GA09/hero_route.md` + `renders/hero/HeroRoute.png` | render_v10_hero + post |
| REQ-38 | GA10 | `evidence/GA10/delivery.json` | make_v10_delivery |

## 5. 门禁阈值

| 门禁 | 阈值 | 预计 | 失败动作 |
| --- | --- | --- | --- |
| G1 | 240 m = 1680 px，误差 ≤2 px | 通过 | 重算相机 |
| G2 | 七区 + 花园可辨 | 通过（花园从无到有） | 重渲 + 人工复核 |
| G4 | 黄框黄、南豁口通、蓝光蓝 | 通过 | 调探针/材质 |
| G6 | 无悬浮 / 断墙 / 穿模 | 通过（先删 5 浮锥） | 回 G-0 |
| G8 | 接缝无材质跳变 | 通过（同 apron + 0.3 m 压边） | 调接缝 |
| S1 | ≥0.45 | **0.55–0.58** | 提亮边带 / 铺装 |
| S2 | ≤0.12 | **0.030** | 降绿量或压暗绿植 |
| S3 | ≤0.02 | **0.002** | 缩橙带 |
| S12 | 左右框水 ≥0.55，无宽边界行 | **0.662**（余量 0.11） | 抬高 / 后移 CameraHero 重测 |
| S15 | 五区 \|ΔH\|≤12、\|ΔS\|≤0.08、\|ΔL\|≤0.06 | 5/5 | 回 color_probe |
| S11 / S13 | 诊断项 | 记录 | 不阻断 |
| GA01 | 7,272±5 m²；bbox x94–208 / y−128..−30；z4.70 | 通过 | 回 G-1 |
| GA02 | 12 区边界误差 ≤1 m；横轴 u38–42 | 通过 | 回 G-1/G-4 |
| GA03 | 两级缝可辨；边带 1.2±0.1；池缘无直角 | 通过 | 回 G-2 |
| GA04 | 橙带连续；壁柱 4.5±0.3 m；桥口断开 | 通过 | 回 G-4 |
| GA05 | 棕榈 16、花坛 4、模纹 2、边篱连续；绿化 1,010±30 | 通过 | 回 G-3 |
| GA06 | 2 座 22×8；水面 4.615（deck 4.70 下 0.085）；池底 `#2E4A4A` | 通过 | 回 G-2 |
| GA07 | 6 凳 / 8 柱 / 2 门架 / 2 牌 / 8 灯 | 通过 | 回 G-4 |
| GA08 | 浮锥 0；K10 段无管；桥件全清 | 通过 | 回 G-0 |
| GA09 | 平台四角在幅内；左右框水 ≥0.55 | 通过（0.65） | 重取机位 |
| GA10 | 五件套齐；sha 全匹配；RMS ≤8；0 硬失败 | 通过 | 回交付 |

## 6. 风险与回退

| 风险 | 触发 | 回退 |
| --- | --- | --- |
| S12 余量不足 | 实测 <0.55（体量替身 0.662） | CameraHero 抬高 15 m / 后移 25 m 重测；不改平台宽度；仍失败则用 HeroRoute 作 S12 机位并在 spec 记偏差 |
| G6 浮锥 / 穿模 | 5 只浮锥未删；平台切桥件 | G-0 先删；geom_check 扫名字；平台段内桥件白名单清零 |
| K10 冲突 | 管廊仍穿 t40–114 | 两端落井 + GA08 扫描；不做架空绕行 |
| 接缝跳变 | 平台与桥材质/标高铰接 | 同 apron 材质 + 0.3 m 深色压边；G8 复核 |
| S1 下滑 | 绿化 13.9% 压暗铺装 | 提亮边带 / 铺装 +0.03 L；不动绿量 |
| 近景穿帮 | 花园进 P 系列画面 | 只重取构图，不改机位编号；不达标就裁切避让 |
| 工期滑 | G-1/G-2 超时 | 先保 GA01–GA08 与 25 门禁；HeroRoute / 近景可后补，不砍平台与种植 |

## 7. 命令清单

```bash
BL="/c/Users/tt/.cache/blender/5.2.3/blender-5.2.3-windows-x64/blender.exe"
V10="art/static_map/space_base_minigame/v10"
RUN="knowledge/active/20261105-space-base-v10-garden/runs/20261105-1800"

# 1 构建（隔离）
$BL -b --factory-startup --python tools/blender_space_base/build_scene_v10.py -- --out "$V10/scene.blend"
# 2 三视图 + 花园特写
$BL -b "$V10/scene.blend" --python tools/blender_space_base/render_v10_views.py -- "C:/软件/鼠鼠/$V10/renders"
$BL -b "$V10/scene.blend" --python tools/blender_space_base/render_v10_garden.py -- "C:/软件/鼠鼠/$V10/renders"
# 3 场景证据（G6 / S8 / S9 / S10 + GA01/02/05/06/07/08）
$BL -b "$V10/scene.blend" --python tools/blender_space_base/evidence_v10.py -- "C:/软件/鼠鼠/$RUN/evidence"
# 4 后处理 + 图像证据（G1/G4/G7/W1/W2/S1-S3/S11-S15 + checks + GA03/GA04/GA09）
python tools/space_base_v10_post.py
# 5 英雄图 + HeroRoute
$BL -b "$V10/scene.blend" --python tools/blender_space_base/render_v10_hero.py -- "C:/软件/鼠鼠/$V10/renders/hero"
# 6 隔离复现
$BL -b "$V10/scene.blend" --python tools/blender_space_base/repro_v10.py -- \
    "C:/软件/鼠鼠/$V10/renders/repro.png" "C:/软件/鼠鼠/$V10/renders/master_raw.png"
# 7 逐区配色（M8.5）
python tools/color_probe.py "$V10/renders/core_raw.png"
# 8 机械门禁
python tools/space_base_check_v7.py --request knowledge/active/20261105-space-base-v10-garden \
    --candidate "$V10" --run 20261105-1800
# 9 五件套
python tools/make_v10_delivery.py
# 10 计划文档自检
python tools/plan_doc_check.py planning/art/SPACE_BASE_GARDEN_HARNESS_DEV_PLAN_20261105.md
```

## 8. 完成定义（DoD）

- [ ] `v10/scene.blend` 可由 `build_scene_v10.py` 在 `--factory-startup` 下重建；
- [ ] `master_raw 3360×5880`、`master 1680×2478`、`core 2072×1876`、`hero 1920×1080`、`jpg ≤3 MB`；
- [ ] `checks/01–05` + `06_paving` + `07_wall` + `08_garden_plan`；
- [ ] `hero/HeroWide|HeroMid|HeroLow|HeroRoute.png`；
- [ ] 近景 P1–P8 + NPR（若保留）与 v09 同规格；
- [ ] `GATE_REPORT.json`：25 项门禁全过（S11/S13 diagnostic，S15 硬门 5/5）+ GA01–GA10 全过；
- [ ] `MANIFEST.json` sha 全匹配；`DELIVERY.json`；`REPRODUCE.md`；`REVIEW.md`；
- [ ] `reproduction.json` RMS ≤8（v09 实测 3.557）；
- [ ] `check_v7` 0 硬失败；`check_summary.json` 落盘；
- [ ] v09 只读：文件 mtime / sha 不变；
- [ ] 请求包四件（brief / test_cases / run_context / resolved）与 run 证据完整。

## 9. 时间表

| 日 | 内容 |
| --- | --- |
| D1 上午 | G-0 隔离与清理 + G-1 平台几何 |
| D1 下午 | G-2 地面与水景；第一张 master 粗看 |
| D2 上午 | G-3 种植 + G-4 构筑物 |
| D2 下午 | G-5 全链渲染（master / core / hero / HeroRoute / 06–08） |
| D3 上午 | G-6 复现、S15、check_v7、五件套；S12 优先复测 |

## 10. 变更控制

- 任何布局 / 尺寸变更 → 先改方案并升 `design_r08`，同步 `test_cases.bound_design_sha256`，重跑受影响阶段；不接受"边做边改"；
- 门禁阈值只允许在 `GATE_REPORT` 里记录偏差并说明理由，不静默放宽；
- v09 目录只读；所有写入落在 v10 与 `runs/20261105-1800/`。
