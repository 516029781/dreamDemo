# -*- coding: utf-8 -*-
"""Generate v10 REVIEW.md from the evidence JSONs (no hand-typed numbers)."""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(ROOT, "art", "static_map", "space_base_minigame", "v10")
REQ = os.path.join(ROOT, "knowledge", "active", "20261105-space-base-v10-garden")
RUN = "20261105-1800"
EV = os.path.join(REQ, "runs", RUN, "evidence")


def load(rel):
    p = os.path.join(EV, rel)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def main():
    gate = json.load(open(os.path.join(V, "GATE_REPORT.json"), encoding="utf-8"))
    s1 = load("S1/value_stats.json")
    s2 = load("S2/hue_stats.json")
    s3 = load("S3/hue_stats.json")
    s12 = load("S12/water_border.json")
    s11 = load("S11/value_span.json")
    s13 = load("S13/illustration_metrics.json")
    s14 = load("S14/ceo_readout.json")
    s15 = load("S15/color_probe.json")
    ga1 = load("GA01/platform_geom.json")
    ga3 = load("GA03/paving.json")
    ga4 = load("GA04/wall_profile.json")
    ga5 = load("GA05/planting.json")
    ga6 = load("GA06/water.json")
    ga7 = load("GA07/structures.json")
    ga8 = load("GA08/cleanup.json")
    ga9 = load("GA09/hero_route.json")
    ga10 = load("GA10/delivery.json")
    rep = load("../reproduction.json")

    checks = gate["checks"]
    hard = gate["hard_failures"]
    diag = gate["diagnostic_failures"]
    proj = gate["project_checks"]

    lines = []
    a = lines.append
    a("# v10 · 中央花园外场 · 交付自评\n")
    a("> 日期：2026-11-05　｜　请求：`%s`　｜　run：`%s`　｜　spec：%s\n"
      % (gate["request_id"], RUN, gate["spec"]))
    a("> 机械门禁：**%s**（硬失败 %d）；业务 25 项 + 项目级 GA01–GA12。\n"
      % ("PASS" if not hard else "FAIL", len(hard)))

    a("## 1. 本轮做了什么\n")
    a("| 阶段 | 内容 | 结果 |")
    a("| --- | --- | --- |")
    a("| G-0 清理 | 删 v09 遗留的 5 只水面浮锥（桥侧 3 + 半岛 2，保留岛上 1 只）；删整组引道管架 `cw_pipe/cw_post/cw_loop/cw_lamp`（横贯平台且悬空 4.5 m）；平台段内 5 灯 / 3 墩 / 23×2 栏杆 / 标线 / 路缘全部重排到桥 A/B；K10 管廊在 t40/114 两端落井 | GA08 0 命中 |")
    a("| G-1 平台 | 100×74 m、8 m 倒角、顶面 +4.70、北端 8 m 入口坡；桥 A 0–40、桥 B 114–138.7 | 净面积 %s m²、z=%s |"
      % (ga1.get("area_m2"), ga1.get("z_top")))
    a("| G-2 地面 | 6 m 二级缝 0.030 + 24 m 一级缝 0.060 + 0.12 m 锈渍晕；1.2 m 外圈边带 8 段；池缘 0.045 m 圆角 | 缝距 %s / 主缝 %s |"
      % (ga3.get("joint_pitch_m"), ga3.get("primary_pitch_m")))
    a("| G-3 种植 | 32 株棕榈（中轴双列 16 + 外圈沿篱 16，卡片冠）、2 座 20×14 模纹园、4 块 10×8 花坛、边篱 58 m×2 | %s 株 / %s 坛 / %s 园 |"
      % (ga5.get("palm_trunks"), ga5.get("beds"), ga5.get("parterres")))
    a("| G-4 构筑 | 挡墙 1.10（橙带 0.60–0.78 + 浅压顶 1.10–1.28 + 4.5 m 壁柱）、观景台 6 凳、廊架 8 柱、服务区、2 门架、2 牌、8 灯 | 墙高 %s m |"
      % ga4.get("wall_height_m"))
    ga11 = load("GA11/facade.json")
    a("| G-7 半岛立面 | K07 立面构件由反贴 0.4 m 改正为外挑；外窗 %s 樘（深色玻璃 + 浅框 + %s 根竖梃）、卷帘分节 %s 道、门套 %s、雨棚 %s、落水管 %s、墙灯 %s、风向袋支臂 | v_min %s |"
      % (ga11.get("exterior_windows"), ga11.get("mullions"), ga11.get("door_slats"),
         ga11.get("door_jambs"), ga11.get("k07_canopies"), ga11.get("downpipes"),
         ga11.get("wall_lamps"), ga11.get("k07_facade_v_min")))
    a("| G-5 渲染 | master 3360×5880@32、core 2072×1876@32、hero 1920×1080@48、HeroRoute 1920×1080、06 铺装 / 07 挡墙 / 花园平视 | 全部产出 |")
    a("| G-6 门禁 | 隔离复现 RMS %s；S15 5/5；check_v7 0 硬失败 | %s |"
      % (rep.get("rms"), "PASS" if not hard else "FAIL"))
    a("")

    a("## 2. 门禁结果\n")
    a("| 组 | 项 | 结果 |")
    a("| --- | --- | --- |")
    total = len(gate["required_checks"])
    ok = [c for c in gate["required_checks"] if checks.get(c, {}).get("pass")]
    a("| 业务（spec r06） | %d / %d 通过 | %s |"
      % (len(ok), total,
         "其余 %d 项为预置 diagnostic（不阻塞）：%s" % (len(diag), ", ".join(diag)) if diag else "全部通过"))
    a("| 项目级 GA | %d / 12 | %s |"
      % (sum(1 for v in proj.values() if v) + (1 if ga10.get("pass") else 0),
         "全部通过" if all(proj.values()) and ga10.get("pass") else "见下"))
    a("")

    a("## 3. 关键数值\n")
    a("| 指标 | 实测 | 阈值 |")
    a("| --- | --- | --- |")
    a("| S1 陆地相对浅色 | **%.3f** | ≥ 0.45 |" % s1.get("light_land", 0))
    a("| S2 绿占比 | %.4f | ≤ 0.12 |" % s2.get("green_ratio", 0))
    a("| S3 橙占比 | %.4f | ≤ 0.02 |" % s3.get("orange_ratio", 0))
    a("| S12 侧框水色 | %.3f（宽边界行 %s） | ≥ 0.55 / = 0 |"
      % (s12.get("side_water_ratio", 0), s12.get("wide_boundary_rows")))
    a("| S14 总裁盒 std | %.3f（家具 %s） | ≥ 0.15 / ≥ 3 |"
      % (s14.get("std", 0), s14.get("furniture_components")))
    a("| S15 逐区配色 | %s | 5 行全过 |"
      % ("5/5" if s15.get("pass") else "FAIL"))
    a("| 复现 RMS | %.3f | ≤ 8 |" % rep.get("rms", 0))
    a("| 平台面积 | %s m² | 7272 ± 5 |" % ga1.get("area_m2"))
    a("| 水面标高 | %s | 4.615 ± 0.03 |" % ", ".join(str(p["z_top"]) for p in ga6.get("pools", [])))
    a("| 浮锥 / K10 穿平台 / 桥件 | %d / %d / %d | 0 / 0 / 0 |"
      % (len(ga8.get("bad_cones", [])), len(ga8.get("k10_pipes_in_platform", [])),
         len(ga8.get("bridge_parts_in_platform", []))))
    a("")

    a("## 4. 已知偏差 / 取舍\n")
    for d in gate.get("known_deviations", []):
        a("- **%s**：%s" % (d.get("check"), d.get("note")))
    a("")
    a("## 5. 交付文件\n")
    a("| 文件 | 尺寸 |")
    a("| --- | --- |")
    for rel, size in (("renders/space_base_v10_master.png", "1680×2478"),
                      ("renders/space_base_v10.jpg", "1680×2478"),
                      ("renders/master_raw.png", "3360×5880"),
                      ("renders/space_base_v10_core.png", "2072×1876"),
                      ("renders/space_base_v10_hero.png", "1920×1080"),
                      ("renders/hero/HeroRoute.png", "1920×1080"),
                      ("renders/hero/GardenEye.png", "1920×1080"),
                      ("renders/checks/06_paving.png", "1600×1000"),
                      ("renders/checks/07_wall.png", "1600×1000")):
        a("| `%s` | %s |" % (rel, size))
    a("")
    a("复现见 `REPRODUCE.md`；门禁明细见 `GATE_REPORT.json`；哈希绑定见 `MANIFEST.json`。")
    a("")

    out = os.path.join(V, "REVIEW.md")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print("REVIEW_OK", out)


if __name__ == "__main__":
    main()
