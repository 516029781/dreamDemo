# N0 需求 Brief：航天基地静态地图 v02 细节补齐（space_base_minigame）

- business_id：`space_base_minigame`
- request_id：`20261102-space-base-detail`
- task_mode：`production`
- deliverable_type：`static_map`
- 确认来源：用户 2026-11-02「继续补齐 L2/L3 细节和真机验证」；上游确认文件
  `planning/art/SPACE_BASE_EXECUTION_PLAN_20261102.md`
- 状态：`confirmed`（v02 追加，N4 见 `DEV_FEASIBILITY_REVIEW.md`）

## 1. 目标

做一张**可验收的 WeChat 小游戏竖屏静态地图**：1920×2560 随包 JPEG + 3840×5120 master PNG +
可独立重开的 Blender 源 + 完整证据。不是完整游戏，不做角色/UI/玩法/真机性能。

## 2. 范围

做：
- 世界 240×380 m：核心区 240×190、南花园 240×30、引道 24×30、试车间 170×130；
- 四角四室 + 四段环廊（转角实墙）+ 中央实心设备体 + 9 m 顶总裁盒；
- 南花园 40×8 池/双喷泉/15 m 南出口；南向通道 11 件；试车间 9 m 墙/绿色门洞/T-16/撤离点；
- 7 个识别点、12 色、55° 正交、8 px/m；
- 可编辑 `scene.blend`、4 张检查图、REVIEW/DELIVERY/GATE/MANIFEST/REPRODUCE。

不做：
- 角色、UI、动画、玩法、完整 Cocos/微信工程、真机性能；
- A1/W3/W4（运行时外置）；
- P1 候选、P1 参考、P1 评分、P1 gate；
- AI 直出整图；导出图不替代源；
- 不覆盖 `concept/` 与 `reference/` 旧图。

## 3. 固定输入

| 项 | 值 |
|---|---|
| 设计 | `planning/art/SPACE_BASE_MASTER_SPEC_20261102.md` v1.3 |
| 执行 | `planning/art/SPACE_BASE_EXECUTION_PLAN_20261102.md` |
| 交接 | `planning/art/HANDOFF_20261102.md` |
| 图 | `_routes_v13.html`、`_corridor_strip.html` |
| 相机 | 正交 55°，北侧朝南，上南下北，只平移 |
| 比例 | 8 px/m；纵向 6.5536 px/m |
| 整图 | 1920×2560（南侧 70 px 出血） |
| master | 3840×5120 PNG |
| 随包 | 1920×2560 JPEG q88–90，≤3 MB |
| 风格 | spec §6 的 12 色；HAAVK 绿大面积≤8%、橙≤2% |

## 4. 需求与验收

| REQ | 检查 | 要求 | 来源 | 本轮 |
|---|---|---|---|---|
| REQ-01 | G1 | 240 m = 1920 px；master 3840×5120 | §9.7.1 | 必过 |
| REQ-02 | G2 | 遮字仍辨出四室/总裁/花园/试车间 | §9.7.1 | 必过 |
| REQ-03 | G3 | 总裁两竖梯入口可读；落地层四边实墙 | §9.7.1 | 必过 |
| REQ-04 | G4 | 南出口 py≈1119、横向 47–53% | §9.7.1 | 必过 |
| REQ-05 | G5 | 北门看集装箱挡住撤离黄框 | §9.7.1 | 必过 |
| REQ-06 | G6 | 无悬浮/断墙/穿模；6 格扫视 | §9.7.1 | 必过 |
| REQ-07 | G7 | 四边跟随边界正确 | §9.7.1 | 必过 |
| REQ-08 | G8 | 花园/引道同屏、材质分缝连续 | §9.7.1 | 必过 |
| REQ-09 | W1 | JPEG≤3 MB、1920×2560、最大边≤4096、无 alpha | §9.7.2 | 必过 |
| REQ-10 | W2 | 主包算术≤4 MB、总包≤30 MB、地图可分包 | §9.7.2 | 必过（算术） |
| REQ-11 | S1 | 白+浅灰 ≥45% | §9.7.3 | 必过 |
| REQ-12 | S2 | 大面积绿≤8%，只在指定面 | §9.7.3 | 必过 |
| REQ-13 | S3 | 橙≤2%，只在指定点缀 | §9.7.3 | 必过 |
| REQ-14 | S4 | 五室各一个色相签名 | §9.7.3 | 必过 |
| REQ-15 | S5 | 无圆角（金属 R≤0.05） | §9.7.3 | 必过 |
| REQ-16 | S6 | 墙 1.2×2.4、地 3×3 分缝 | §9.7.3 | 必过 |
| REQ-17 | S7 | 阴影 0.6–0.8 硬边；总裁唯一暖区 | §9.7.3 | 必过 |
| REQ-18 | A1 | 角色阴影方向一致 | §9.7.4 | external |
| REQ-19 | W3 | 真机首帧≤1.5 s、内存≤150 MB | §9.7.2 | external |
| REQ-20 | W4 | 低端降级 1440×1920 / 1280×1707 | §9.7.2 | external |

`target_met` 覆盖 REQ-01..17；REQ-18..20 单独列 external，不写成 pass。

## 5. 交付

- `art/static_map/space_base_minigame/v01/scene.blend`
- `renders/space_base_v01_master.png`（3840×5120）
- `renders/space_base_v01.jpg`（1920×2560）
- `renders/checks/01_core.png`、`02_workshop.png`、`03_south_exit.png`、`04_ceo.png`
- `REVIEW.md`、`DELIVERY.json`、`GATE_REPORT.json`、`MANIFEST.json`、`REPRODUCE.md`
- active run：`RUN_CONTEXT.json`、`RESOLVED_KNOWLEDGE.json`、`runs/20261102-1314/` 证据

## 6. 约束

- 8 px/m/55°/1920×2560 冻结；变更即回 N2/N4。
- 不套 P1 参考/评分/8 条硬门槛；本业务用 `HARNESS_SPEC.json` + 人工自评 + `tools/space_base_check.py`。
- 图变即证据失效；终图必须由同一 `scene.blend` 重开渲染；隔离复现绑 content SHA。
- 不自签外部验收；`not_run`/`external`/`diagnostic_only` 不得写成 `pass`。
- 新业务只追加 manifest/START_HERE/AGENTS/active README，不覆盖现有 pilot/P1 改动。


## 8. v02 追加：L2/L3 细节与真机验证

- 目标：在 v01 布局/相机/验收不变的前提下，补齐可见的 L2/L3 细节（设备细节、栏杆/管线/法兰、货箱门/肋、门窗框、屏幕、灯、地面标线/导视、外墙编号板等），并建立最小微信运行时冒烟包。
- 不改变：8 px/m、55°、1920×2560、所有坐标/门位/路线/17 条必检。
- 追加检查（不计入 17 条 gate）：D1 细节不造成悬浮/穿插；D2 7 识别点仍清楚；D3 文件/包体预算仍过；D4 无外部贴图/AI 直出；D5 细节不压可走面。
- 真机：准备 `runtime_space_base/`（纯 Canvas 加载 + 触控平移 + 首帧/内存日志）；DevTools CLI 已安装但当前报“需要重新登录”，需扫码登录后生成预览 QR；W3/W4 仍以真机证据为准，未测不写 pass。
- 候选：`art/static_map/space_base_minigame/v02/`；v01 保留。

## 7. 完成定义

v01 源可重开；master/JPEG/4 检查图存在；REQ-01..17 全过；隔离复现通过；
REVIEW/DELIVERY/GATE/MANIFEST/REPRODUCE 完整；最终报告只写证据支持的状态。
