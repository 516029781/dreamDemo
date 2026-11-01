# P1 业务 Profile

- business_id：`p1_autumn_static`
- 版本：**r03**（2026-11-02，按 2026-11-01T23:19–23:23 的更新记录恢复“整图无植被”）
- 交付类型：固定机位静态环境地图 + 可编辑 Blender 源
- 平台/画幅：单张静帧，1920×1078，53mm 固定相机（参数见状态文件）
- lifecycle：`active`
- activation_basis：用户 2026-10-28 锁定 t084 为唯一整图参考；**2026-11-01T23:23 状态文件明确
  “整图完全没有植物”，以设备/箱体建立画面层次**（此前 21:00 的手绘植被为中间尝试，已被覆盖）

## 1. 范围

- 做：一张原创布局的秋日庭院静态图；可重开 Blender 源；同机位证据链。
- 不做：人物、UI、动画、玩法、Cocos/微信、完整游戏流程、可行走性承诺。
- 数据研究：`research_arknights_mapdata` 仅用于地图参数与 Harness 规则，不作视觉参考。

## 2. 当前状态指针

- 候选状态机：`planning/art/ACTIVE_STATIC_ART.json`（唯一事实源，2026-11-01T23:23）
- 当前工作图：`v25/renders/final_v27.png`（含树、草——**中间产物，不是当前目标**），
  质量 `unverified_current_image`，源—图同源 `unverified`
- 活动工作单：`planning/art/P1_WORKORDER_20261101_NEXT.md`（无植被设备化改编）
- 信息订正契约：`planning/art/STATIC_ART_INFORMATION_CORRECTION_20261101.md`（23:19 版）

## 3. 植被政策（r03，当前）

| 项 | 内容 |
|---|---|
| 当前政策 | **整图完全没有植物**：清除树、树叶、草、花、灌木、苔藓、藤蔓、杂草、盆栽、花池、裸土与植物贴图/纹样 |
| 左树区 | 改为 2–3 个不同宽高的高型维护柜/通风控制设备，连续底座、检修门、少量格栅/接口、明确地面投影 |
| 右草池 | 改为封闭式过滤/储液圆筒：浅灰连续筒壁、顶部有盖、底部支撑环、少量接口管路 |
| 依据 | `ACTIVE_STATIC_ART.json`（23:23）`user_art_direction`；`P1_WORKORDER_20261101_NEXT.md`（23:20） |
| 历史 | 2026-11-01 21:00 的“手绘树叶与草”方向为中间尝试，**已被覆盖**；相关计划降为 historical_only |
| 边界 | P1 专属决定；其他地图是否用植被由各自 brief 决定 |

## 4. 质量与门槛

- 评分：`scorecard.json`（六维权重 20/20/20/15/15/10，总分 ≥85、各维 ≥3）
- 组合检查四项：`floor`、`structures`、`lighting`、`background`
- 八项硬门槛含 `no_vegetation`、`left_area_functional_replacement`（均有效）
- 独立终审：**不要求**（用户 2026-11-01 决定）；制作侧自评 + 反证 + 机械 gate 字段校验

## 5. 交付

- 可编辑源、最终图、`REVIEW.md`、`DELIVERY.json`、`GATE_REPORT.json`、`reference_analysis/`、
  复现记录、SHA 清单；导出图不得替代源。图 SHA 变更 → 视觉证据失效，须重评。

## 6. 已知风险

1. 源—图同源未验证（V27 的复现证据未归档）。
2. I3 遮罩/ROI 未校准，全图色彩统计仅诊断。
3. V27 现含植被，须在新候选目录完成清除，不覆盖 `v25/` 既有文件。
