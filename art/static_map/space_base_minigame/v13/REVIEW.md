# v13 制作侧自评（design r15 · N7 进行中）

> 状态：**in_progress**，不是交付。本文件不宣称 PASS / target_met。

## 本轮做了什么

按 harness N0–N4 建运行身份与冻结基线，N5 建原型，N6 四轮返修，N7 跑机械检查与隔离复现。

- **南端重建**：`build_peninsula`（v07 直升机撤离码头）→ `build_test_workshop`
  （实机露天防爆试验场 S-01…S-12）。保留 `dock` 坐标系与桥 B，只换内容。
- **关键发现 H1**：`build_avenue` / `build_forecourt` / `build_street_kit` / K01–K14
  是 v07「引道+码头」遗留，共 **480 个 mesh** 铺在同一块半岛上，其中 `av_road`
  贯穿院落、`k05_roof` 带屋顶盖住西侧。源级修法：南端归试车间独占，
  按 dock 局部坐标清理所有非 `ws_` 对象。
- **H2/H3**：扩大清理范围到 v ±50；删除 4 个岗亭/巴士顶盖（全图不做屋顶）。
- **H4**：`sd_cont_` / `ws_cab_` / `ws_drum_` / `ws_palletbox_` 破朝向与破共线；
  同时修正 E15 统计实现（原本把路面标线也算成"可辨物件"）。

## 机械检查（N7 部分）

| TEST-ID | 状态 | 实测 |
|---|---|---|
| TV13-01 S-构件齐全 | pass | 12/12 组存在 |
| TV13-02 删除清单 | pass | 命中 0 |
| TV13-03 屋顶对象 | pass | 命中 0 |
| TV13-04 E15 密度 | pass | 1.45 件/400 m² |
| TV13-05 E11–E14 | pass | E11 0.704 / E12 0.175 / E13 0.281 / E14 0.25 |
| TV13-06/07 目视 | diagnostic_only | `_cmp_master.png` / `_cmp_south.png` |
| TV13-08 隔离复现 | pass | content SHA 一致，RMS 0.0 |
| TV13-09 业务门禁 | **pass** | `space_base_check_v7` PASS，hard_failures=0 |
| TV13-10 盲测 | **not_run** | 需 3 人参与 |

`diagnostic_only` 与 `not_run` 均**不计 PASS**（HARNESS_LIFECYCLE §3）。

## 已知短板

1. `master_raw.png` 已补渲 3360×5880（12 samples）；与 1680×2478 交付图同相机，比例差导致横向视野更窄（v11 既有口径，已预先声明）。
2. 防爆墙在俯视下只是一条线，高度感要靠英雄图；英雄图已渲染但尚未逐区复核。
3. Q2（S1 阈值与色板冲突）未决，本轮不动门禁、不降地面亮度。
4. 主路面仍偏空（F1–F5 只做了 v12 已有的功能带，未做本轮新增填充）。
5. 场地轮廓 94/74/62 直角阶梯未动（方案 L0，下一轮）。

## 下一轮

TV13-09 已闭合。剩余：TV13-10 三人盲测 + TV13-06/07 目视签收 → 才能判结束状态。
